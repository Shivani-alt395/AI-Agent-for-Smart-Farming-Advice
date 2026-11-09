"""
Smart Farming Agent — orchestrates RAG + Granite LLM + external services.
This is the core reasoning engine of the application.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from langchain_core.prompts import PromptTemplate
from loguru import logger

from app.core.granite_llm import GraniteLLM
from app.core.rag_pipeline import get_rag_pipeline
from app.models.schemas import (
    FarmingQuery,
    FarmingResponse,
    QueryCategory,
    SourceDocument,
    WeatherData,
)
from app.services.language_service import LanguageService
from app.services.market_service import MarketService
from app.services.weather_service import WeatherService


# ── Intent detection keyword maps ──────────────────────────────────────────
INTENT_KEYWORDS: Dict[QueryCategory, List[str]] = {
    QueryCategory.WEATHER: [
        "weather", "rain", "rainfall", "temperature", "forecast", "monsoon",
        "drought", "flood", "humidity", "wind", "irrigation", "water", "mausam",
        "barish", "tapman", "sinchai",
    ],
    QueryCategory.MARKET: [
        "price", "mandi", "market", "rate", "sell", "buy", "bazar", "bhav",
        "tomato", "onion", "potato", "wheat", "rice", "cotton", "soybean",
        "msp", "minimum support", "e-nam", "enam",
    ],
    QueryCategory.PEST: [
        "pest", "disease", "insect", "blight", "fungus", "virus", "worm",
        "spray", "pesticide", "fungicide", "herbicide", "weed", "kida",
        "bimari", "rog", "keeda",
    ],
    QueryCategory.SOIL: [
        "soil", "fertilizer", "manure", "compost", "ph", "nitrogen", "npk",
        "potassium", "phosphorus", "organic", "mitti", "khad", "urvara",
    ],
    QueryCategory.CROP: [
        "crop", "sow", "plant", "harvest", "seed", "variety", "season",
        "kharif", "rabi", "zaid", "yield", "fasal", "beej", "ugana",
        "cultivation", "farming",
    ],
}

# ── System prompt template for IBM Granite ─────────────────────────────────
FARMING_PROMPT = PromptTemplate(
    input_variables=["context", "question", "weather_context", "market_context"],
    template="""You are an expert agricultural advisor AI for Indian farmers.

STRICT RULES:
1. Answer ONLY what is asked. Do NOT add unrelated topics.
2. If asked about a specific crop or commodity (e.g. onion, tomato), answer ONLY about that crop/commodity.
3. Give 2-4 bullet points maximum. Be concise and direct.
4. For market/price questions: state ONLY the price of the asked commodity. Do NOT list other commodities.
5. For greetings (hello, hi, namaste): respond with only a short friendly greeting. Do NOT give farming advice unless asked.
6. Include specific quantities/timings only when directly relevant to the question.

Knowledge: {context}
Weather: {weather_context}
Market: {market_context}
Question: {question}

Answer (strictly about what was asked):""",
)


class FarmingAgent:
    """
    Main AI agent that combines:
    - IBM Granite LLM for reasoning
    - ChromaDB RAG for knowledge retrieval
    - Weather API for real-time weather
    - Mandi price API for market data
    - Multilingual support
    """

    def __init__(self):
        self._llm = GraniteLLM.from_settings()
        self._rag = get_rag_pipeline()
        self._weather_service = WeatherService()
        self._market_service = MarketService()
        self._language_service = LanguageService()
        logger.info("FarmingAgent initialized.")

    async def process_query(self, query: FarmingQuery) -> FarmingResponse:
        """
        Main entry point. Process a farmer's question through the full pipeline:
        1. Detect/translate language
        2. Classify intent
        3. Fetch relevant external data (weather/market)
        4. Retrieve RAG context
        5. Generate answer with IBM Granite
        6. Translate response back if needed
        """
        session_id = query.session_id or str(uuid.uuid4())
        original_question = query.question
        user_lang = query.language.value

        # Step 1: Detect language if auto, translate to English for processing
        detected_lang = self._language_service.detect_language(original_question)
        working_lang = detected_lang if detected_lang != "en" else user_lang

        english_question = original_question
        if working_lang != "en":
            english_question = self._language_service.translate_to_english(
                original_question, source_lang=working_lang
            )
            logger.info(f"Translated question [{working_lang}→en]: {english_question}")

        # Step 2: Classify intent
        category = self._detect_intent(english_question)
        logger.info(f"Query category: {category.value} | Question: {english_question[:80]}")

        # Step 3: Fetch contextual data + RAG in parallel
        weather_data: Optional[WeatherData] = None
        weather_context = "No weather data."
        market_context = "No market data."
        market_data: Optional[Dict[str, Any]] = None

        need_weather = category in (QueryCategory.WEATHER, QueryCategory.CROP) and query.latitude and query.longitude
        need_market  = category == QueryCategory.MARKET
        commodity    = self._extract_commodity(english_question) if need_market else None

        # Extract state from the question text first (e.g. "onion price in karnataka"),
        # fall back to the sidebar location only if no state is mentioned in the question
        market_state = self._extract_state(english_question) or query.location

        async def _fetch_weather():
            return await self._weather_service.get_weather(
                latitude=query.latitude, longitude=query.longitude,
                location_name=query.location or "Your Farm",
            )

        async def _fetch_market():
            return await self._market_service.get_prices(commodity=commodity, state=market_state, limit=8)

        tasks = []
        if need_weather: tasks.append(_fetch_weather())
        if need_market:  tasks.append(_fetch_market())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        idx = 0
        if need_weather:
            r = results[idx]; idx += 1
            if not isinstance(r, Exception):
                weather_data = r
                adv = self._weather_service.get_farming_advice_from_weather(weather_data)
                weather_context = (
                    f"Today at {weather_data.location}: {weather_data.condition}, "
                    f"{weather_data.temperature_max}°C max, Rain:{weather_data.precipitation}mm. {adv}"
                )
            else:
                logger.warning(f"Weather fetch failed: {r}")
        if need_market:
            r = results[idx]; idx += 1
            if not isinstance(r, Exception):
                prices = r
                # If a specific commodity was asked, filter STRICTLY to that commodity only
                if commodity:
                    c_key = commodity.lower().replace(" (rice)", "").replace("paddy ", "")
                    filtered = [p for p in prices if c_key in p.commodity.lower()]
                    if filtered:
                        # Only show the asked commodity in table + context
                        market_context = self._market_service.format_prices_as_text(filtered)
                        market_data = {"prices": [p.dict() for p in filtered]}
                    else:
                        # Commodity not in DB — tell LLM, show no table
                        market_context = f"No specific price data found for {commodity} in the database."
                        market_data = None
                else:
                    market_context = self._market_service.format_prices_as_text(prices)
                    market_data = {"prices": [p.dict() for p in prices]}
            else:
                logger.warning(f"Market fetch failed: {r}")

        # Step 4: RAG retrieval — skip for greetings/very short queries
        GREETING_WORDS = {"hello","hi","hey","namaste","namaskar","hola","howdy","sup","yo"}
        is_greeting = english_question.strip().lower() in GREETING_WORDS or len(english_question.strip()) <= 6
        if is_greeting:
            rag_context = ""
            rag_results = []
        else:
            rag_context = self._rag.retrieve_as_context(english_question, k=3)
            if not rag_context:
                rag_context = "No specific knowledge found."
            rag_results = self._rag.retrieve(english_question, k=3)
        sources = [
            SourceDocument(
                content=doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                source=doc.metadata.get("source", "Knowledge Base"),
                relevance_score=float(score),
                category=QueryCategory(doc.metadata.get("category", "general")),
            )
            for doc, score in rag_results
        ]

        # Step 5: Build prompt and generate answer
        prompt = FARMING_PROMPT.format(
            context=rag_context,
            question=english_question,
            weather_context=weather_context,
            market_context=market_context,
        )

        answer_english = self._llm._call(prompt)

        # Step 6: Translate back if needed
        final_answer = answer_english
        if working_lang != "en":
            final_answer = self._language_service.translate_from_english(
                answer_english, target_lang=working_lang
            )

        # Compute confidence score based on RAG relevance
        confidence = (
            sum(score for _, score in rag_results[:3]) / min(len(rag_results), 3)
            if rag_results else 0.5
        )
        confidence = max(0.0, min(1.0, float(confidence)))

        return FarmingResponse(
            answer=final_answer,
            category=category,
            sources=sources,
            weather_data=weather_data.dict() if weather_data else None,
            market_data=market_data,
            language=query.language,
            session_id=session_id,
            confidence=confidence,
        )

    def _detect_intent(self, question: str) -> QueryCategory:
        """Classify the query into one of the farming categories. Greetings stay GENERAL."""
        q_lower = question.strip().lower()
        # Short greetings — keep as general so no market/weather fetch is wasted
        GREETINGS = {"hello", "hi", "hey", "namaste", "namaskar", "hola", "howdy",
                     "good morning", "good evening", "good afternoon", "sup", "yo"}
        if q_lower in GREETINGS or len(q_lower) <= 6:
            return QueryCategory.GENERAL
        scores: Dict[QueryCategory, int] = {}
        for category, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in q_lower)
            if score > 0:
                scores[category] = score
        if not scores:
            return QueryCategory.GENERAL
        return max(scores, key=scores.get)

    def _extract_state(self, question: str) -> Optional[str]:
        """Extract a state name mentioned in the question text."""
        from app.services.market_service import STATE_ALIASES, _normalise_state
        q_lower = question.lower()
        # Full state names first (longest match wins)
        full_names = [
            "andhra pradesh", "uttar pradesh", "madhya pradesh", "tamil nadu",
            "west bengal", "himachal pradesh", "arunachal pradesh",
            "jammu and kashmir",
        ]
        for name in full_names:
            if name in q_lower:
                return _normalise_state(name)
        # Then single-word aliases
        for alias, canonical in STATE_ALIASES.items():
            if len(alias) > 2 and alias in q_lower:  # skip 2-char codes to avoid false matches
                return canonical
        return None

    def _extract_commodity(self, question: str) -> Optional[str]:
        """Extract a commodity name from a market question — return FIRST match (most specific)."""
        commodities = [
            # vegetables
            ("onion", "Onion"), ("tomato", "Tomato"), ("potato", "Potato"),
            ("garlic", "Garlic"), ("ginger", "Ginger"), ("capsicum", "Capsicum"),
            ("cabbage", "Cabbage"), ("cauliflower", "Cauliflower"), ("brinjal", "Brinjal"),
            # fruits
            ("banana", "Banana"), ("mango", "Mango"), ("grapes", "Grapes"),
            ("pomegranate", "Pomegranate"), ("coconut", "Coconut"),
            ("orange", "Orange"), ("papaya", "Papaya"), ("watermelon", "Watermelon"),
            # nuts
            ("cashew", "Cashew"), ("cashewnut", "Cashew"), ("walnut", "Walnut"),
            ("almond", "Almond"), ("areca", "Areca Nut"),
            # spices / oilseeds
            ("turmeric", "Turmeric"), ("chilli", "Chilli"), ("chili", "Chilli"),
            ("pepper", "Black Pepper"), ("cardamom", "Cardamom"),
            ("cumin", "Cumin"), ("coriander", "Coriander"), ("fenugreek", "Fenugreek"),
            ("groundnut", "Groundnut"), ("mustard", "Mustard"),
            ("sesame", "Sesame"), ("sunflower", "Sunflower"),
            ("coffee", "Coffee"), ("tea", "Tea"),
            # pulses / dal
            ("urad dal", "Urad Dal"), ("urad", "Urad Dal"),
            ("chana dal", "Gram"), ("chana", "Gram"),
            ("arhar", "Arhar (Tur Dal)"), ("tur dal", "Arhar (Tur Dal)"), ("tur", "Arhar (Tur Dal)"),
            ("moong dal", "Moong Dal"), ("moong", "Moong Dal"),
            ("masoor", "Masoor Dal"), ("lentil", "Masoor Dal"),
            ("gram", "Gram"),
            # cash crops
            ("sugarcane", "Sugarcane"), ("sugar", "Sugarcane"),
            ("cotton", "Cotton"), ("jute", "Jute"), ("castor", "Castor"),
            ("tobacco", "Tobacco"),
            # oilseeds / cereals
            ("soybean", "Soybean"), ("maize", "Maize"), ("corn", "Maize"),
            ("ragi", "Ragi"), ("jowar", "Jowar"), ("bajra", "Bajra"),
            # staples — check last (short words match too broadly)
            ("paddy", "Paddy (Rice)"), ("rice", "Paddy (Rice)"), ("wheat", "Wheat"),
        ]
        q_lower = question.lower()
        for keyword, canonical in commodities:
            if keyword in q_lower:
                return canonical
        return None


# Module-level singleton
_agent: Optional[FarmingAgent] = None


def get_farming_agent() -> FarmingAgent:
    global _agent
    if _agent is None:
        _agent = FarmingAgent()
    return _agent
