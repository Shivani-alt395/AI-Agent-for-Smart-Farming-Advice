"""IBM Granite LLM wrapper via IBM watsonx.ai."""
from __future__ import annotations

import os
from typing import Any, Dict, Iterator, List, Optional

from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from loguru import logger

from app.core.config import get_settings


class GraniteLLM(LLM):
    """
    LangChain-compatible wrapper around IBM Granite via watsonx.ai.
    Falls back gracefully when credentials are missing (demo mode).
    """

    model_id: str = "ibm/granite-4-h-small"
    max_new_tokens: int = 1024
    temperature: float = 0.3
    top_p: float = 0.9
    top_k: int = 50
    _client: Optional[Any] = None
    _model: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_model()

    def _init_model(self) -> None:
        settings = get_settings()
        api_key = settings.ibm_api_key
        url = settings.ibm_watsonx_url
        project_id = settings.ibm_watsonx_project_id

        if not api_key or api_key == "your_ibm_cloud_api_key_here":
            logger.warning(
                "IBM API key not configured — running in DEMO mode. "
                "Responses will use template answers instead of Granite."
            )
            return

        try:
            credentials = Credentials(api_key=api_key, url=url)
            self._client = APIClient(credentials)
            params = {
                GenParams.MAX_NEW_TOKENS: self.max_new_tokens,
                GenParams.TEMPERATURE: self.temperature,
                GenParams.TOP_P: self.top_p,
                GenParams.TOP_K: self.top_k,
                GenParams.STOP_SEQUENCES: ["<|endoftext|>", "Human:", "User:"],
            }
            self._model = ModelInference(
                model_id=self.model_id,
                params=params,
                credentials=credentials,
                project_id=project_id,
            )
            logger.info(f"IBM Granite model '{self.model_id}' initialized successfully.")
        except Exception as exc:
            logger.error(f"Failed to initialize IBM Granite: {exc}")
            self._model = None

    @property
    def _llm_type(self) -> str:
        return "ibm_granite"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        if self._model is None:
            return self._demo_response(prompt)

        try:
            response = self._model.generate_text(prompt=prompt, guardrails=False)
            return response if isinstance(response, str) else str(response)
        except Exception as exc:
            logger.error(f"Granite inference error: {exc}")
            return self._demo_response(prompt)

    def _demo_response(self, prompt: str) -> str:
        """Return a structured demo response when Granite is unavailable."""
        prompt_lower = prompt.lower()
        if any(k in prompt_lower for k in ["weather", "rain", "temperature", "forecast"]):
            return (
                "Based on current weather patterns for your region, expect moderate temperatures "
                "between 22–30°C with a chance of light rain this week. Ideal conditions for "
                "irrigating crops in the early morning. Keep drainage channels clear to prevent "
                "waterlogging in low-lying fields."
            )
        if any(k in prompt_lower for k in ["price", "mandi", "market", "rate", "tomato", "onion"]):
            return (
                "Today's mandi rates (approximate):\n"
                "• Tomato: ₹1,200–₹1,800 per quintal\n"
                "• Onion: ₹800–₹1,200 per quintal\n"
                "• Potato: ₹600–₹900 per quintal\n"
                "• Wheat: ₹2,015–₹2,100 per quintal (MSP)\n"
                "Prices vary by APMC market. Check your nearest mandi before selling."
            )
        if any(k in prompt_lower for k in ["pest", "disease", "insect", "fungus", "blight"]):
            return (
                "For effective pest management:\n"
                "1. Identify the pest/disease correctly before applying any treatment.\n"
                "2. Use Integrated Pest Management (IPM) — prefer bio-pesticides first.\n"
                "3. For fungal blight: apply copper-based fungicide (Bordeaux mixture) early morning.\n"
                "4. For stem borers: use pheromone traps and neem-based sprays.\n"
                "Consult your local Krishi Vigyan Kendra (KVK) for field-specific advice."
            )
        if any(k in prompt_lower for k in ["crop", "sow", "plant", "season", "kharif", "rabi"]):
            return (
                "Crop recommendations for the current season:\n"
                "• Kharif (June–Oct): Rice, Maize, Soybean, Cotton, Groundnut\n"
                "• Rabi (Oct–Mar): Wheat, Mustard, Gram, Barley, Peas\n"
                "• Zaid (Mar–Jun): Watermelon, Cucumber, Moong Dal\n"
                "Select crops based on your soil type, water availability, and local market demand. "
                "Conduct soil testing before sowing for best yield."
            )
        if any(k in prompt_lower for k in ["soil", "fertilizer", "nutrient", "ph", "manure"]):
            return (
                "Soil health recommendations:\n"
                "• Conduct soil testing every 2–3 years through your state agriculture department.\n"
                "• Maintain soil pH between 6.0–7.5 for most crops.\n"
                "• Apply organic manure (FYM) at 10–15 tonnes/hectare before sowing.\n"
                "• Use balanced NPK fertilizers based on soil test results.\n"
                "• Practice crop rotation to restore soil nutrients naturally."
            )
        return (
            "I am your Smart Farming AI Assistant powered by IBM Granite. "
            "I can help you with:\n"
            "• 🌤️ Weather forecasts and irrigation advice\n"
            "• 🌾 Crop selection and seasonal recommendations\n"
            "• 🐛 Pest and disease management\n"
            "• 💰 Mandi prices and market information\n"
            "• 🌱 Soil health and fertilizer guidance\n\n"
            "Please ask me a specific farming question!"
        )

    @classmethod
    def from_settings(cls) -> "GraniteLLM":
        settings = get_settings()
        return cls(
            model_id=settings.granite_model_id,
            max_new_tokens=settings.granite_max_tokens,
            temperature=settings.granite_temperature,
            top_p=settings.granite_top_p,
            top_k=settings.granite_top_k,
        )
