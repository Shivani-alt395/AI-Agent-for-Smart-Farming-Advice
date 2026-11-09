"""
Pydantic models for API requests and responses.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"
    TELUGU = "te"
    TAMIL = "ta"
    KANNADA = "kn"
    GUJARATI = "gu"
    PUNJABI = "pa"
    BENGALI = "bn"
    ODIA = "or"


class QueryCategory(str, Enum):
    WEATHER = "weather"
    CROP = "crop"
    PEST = "pest"
    SOIL = "soil"
    MARKET = "market"
    GENERAL = "general"


class FarmingQuery(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, description="Farmer's question")
    language: Language = Field(default=Language.ENGLISH, description="Language of the question")
    location: Optional[str] = Field(default=None, description="Farm location (city/district)")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    session_id: Optional[str] = Field(default=None, description="Session identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What crop is best for this season?",
                "language": "en",
                "location": "Nashik, Maharashtra",
                "latitude": 19.9975,
                "longitude": 73.7898,
            }
        }


class SourceDocument(BaseModel):
    content: str
    source: str
    relevance_score: float = 0.0
    category: QueryCategory = QueryCategory.GENERAL


class FarmingResponse(BaseModel):
    answer: str
    category: QueryCategory
    sources: List[SourceDocument] = []
    weather_data: Optional[Dict[str, Any]] = None
    market_data: Optional[Dict[str, Any]] = None
    language: Language = Language.ENGLISH
    session_id: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "For Kharif season in Nashik, consider growing Soybean or Cotton.",
                "category": "crop",
                "sources": [],
                "confidence": 0.85,
            }
        }


class WeatherData(BaseModel):
    location: str
    temperature_max: float
    temperature_min: float
    precipitation: float
    wind_speed: float
    humidity: Optional[float] = None
    condition: str = "Clear"
    forecast_days: List[Dict[str, Any]] = []


class MandiPrice(BaseModel):
    commodity: str
    market: str
    state: str
    min_price: float
    max_price: float
    modal_price: float
    date: str
    unit: str = "Quintal"


class HealthResponse(BaseModel):
    status: str
    version: str
    granite_available: bool
    vector_store_ready: bool
    message: str
