"""
Tests for the Smart Farming AI Agent.
Run with: pytest tests/ -v
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from app.models.schemas import FarmingQuery, QueryCategory, Language
from app.services.farming_agent import FarmingAgent
from app.services.language_service import LanguageService
from app.services.market_service import MarketService, STATIC_PRICES
from app.services.weather_service import WeatherService


# ── Language Service Tests ──────────────────────────────────
class TestLanguageService:
    def setup_method(self):
        self.svc = LanguageService()

    def test_detect_english(self):
        lang = self.svc.detect_language("What crop should I grow this season?")
        assert lang == "en"

    def test_language_name(self):
        assert self.svc.get_language_name("hi") == "Hindi"
        assert self.svc.get_language_name("en") == "English"
        assert self.svc.get_language_name("xx") == "Unknown"

    def test_translate_english_passthrough(self):
        text = "Hello farmer"
        result = self.svc.translate_to_english(text, source_lang="en")
        assert result == text


# ── Market Service Tests ────────────────────────────────────
class TestMarketService:
    def setup_method(self):
        self.svc = MarketService()

    @pytest.mark.asyncio
    async def test_static_prices_returned_without_api_key(self):
        prices = await self.svc.get_prices(limit=5)
        assert len(prices) <= 5
        assert all(p.modal_price > 0 for p in prices)

    @pytest.mark.asyncio
    async def test_filter_by_commodity(self):
        prices = await self.svc.get_prices(commodity="Wheat", limit=10)
        assert all("wheat" in p.commodity.lower() for p in prices)

    def test_format_prices_as_text(self):
        prices = self.svc._get_static_prices(None, None, 3)
        text = self.svc.format_prices_as_text(prices)
        assert "₹" in text
        assert "Quintal" in text.lower() or "per" in text.lower()


# ── Weather Service Tests ───────────────────────────────────
class TestWeatherService:
    def setup_method(self):
        self.svc = WeatherService()

    def test_mock_weather_structure(self):
        weather = self.svc._mock_weather("Test Farm")
        assert weather.location == "Test Farm"
        assert len(weather.forecast_days) == 7
        assert weather.temperature_max > weather.temperature_min

    def test_farming_advice_dry(self):
        weather = self.svc._mock_weather("Farm")
        weather.precipitation = 0
        weather.temperature_max = 35
        advice = self.svc.get_farming_advice_from_weather(weather)
        assert len(advice) > 0

    def test_farming_advice_heavy_rain(self):
        weather = self.svc._mock_weather("Farm")
        weather.precipitation = 30
        advice = self.svc.get_farming_advice_from_weather(weather)
        assert "rain" in advice.lower() or "avoid" in advice.lower()


# ── FarmingAgent Intent Detection ──────────────────────────
class TestFarmingAgentIntentDetection:
    def setup_method(self):
        # Mock the LLM initialization to avoid needing IBM credentials
        with patch("app.core.granite_llm.GraniteLLM._init_model"):
            self.agent = FarmingAgent.__new__(FarmingAgent)
            self.agent._language_service = LanguageService()

    def test_detect_market_intent(self):
        category = self.agent._detect_intent("What is the mandi price for tomatoes today?")
        assert category == QueryCategory.MARKET

    def test_detect_weather_intent(self):
        category = self.agent._detect_intent("Will it rain tomorrow? Should I irrigate?")
        assert category == QueryCategory.WEATHER

    def test_detect_pest_intent(self):
        category = self.agent._detect_intent("My rice crop has fungal disease, how to spray?")
        assert category == QueryCategory.PEST

    def test_detect_soil_intent(self):
        category = self.agent._detect_intent("How much fertilizer NPK should I apply?")
        assert category == QueryCategory.SOIL

    def test_detect_crop_intent(self):
        category = self.agent._detect_intent("Which crop to sow in Kharif season?")
        assert category == QueryCategory.CROP

    def test_extract_commodity_tomato(self):
        result = self.agent._extract_commodity("What is the rate of tomato in mandi?")
        assert result == "Tomato"

    def test_extract_commodity_none(self):
        result = self.agent._extract_commodity("How to do crop rotation?")
        assert result is None


# ── Schema Tests ────────────────────────────────────────────
class TestSchemas:
    def test_farming_query_valid(self):
        q = FarmingQuery(
            question="What should I grow?",
            language=Language.ENGLISH,
            location="Pune",
        )
        assert q.question == "What should I grow?"
        assert q.language == Language.ENGLISH

    def test_farming_query_too_short(self):
        with pytest.raises(Exception):
            FarmingQuery(question="Hi")  # min_length=3 is satisfied; min meaningful is enforced by API
