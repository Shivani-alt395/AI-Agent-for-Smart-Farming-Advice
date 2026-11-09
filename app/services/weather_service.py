"""
Weather service — fetches real-time weather data from Open-Meteo (free, no key).
Falls back to mock data when network is unavailable.
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import get_settings
from app.models.schemas import WeatherData


# WMO Weather code descriptions
WMO_CODES: Dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Slight showers", 81: "Moderate showers",
    82: "Violent showers", 85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


class WeatherService:
    """Fetch weather forecasts using Open-Meteo API (free, no API key required)."""

    def __init__(self):
        self._settings = get_settings()
        self._base_url = self._settings.weather_api_url

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "Your Farm",
        days: int = 7,
    ) -> WeatherData:
        """Fetch weather forecast for given coordinates."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "windspeed_10m_max",
                "weathercode",
                "relative_humidity_2m_max",
                "precipitation_probability_max",
            ],
            "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain"],
            "current_weather": True,
            "timezone": "Asia/Kolkata",
            "forecast_days": days,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self._base_url, params=params)
                response.raise_for_status()
                data = response.json()
                return self._parse_response(data, location_name)
        except Exception as exc:
            logger.warning(f"Weather API error: {exc}. Using mock data.")
            return self._mock_weather(location_name)

    def _parse_response(self, data: Dict[str, Any], location_name: str) -> WeatherData:
        daily = data.get("daily", {})
        current = data.get("current_weather", {})
        live = data.get("current", {}) or {}
        probs = daily.get("precipitation_probability_max", []) or []

        forecast_days: List[Dict[str, Any]] = []
        dates = daily.get("time", [])
        for i, d in enumerate(dates):
            code = daily.get("weathercode", [0] * len(dates))[i]
            forecast_days.append(
                {
                    "date": d,
                    "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else 30,
                    "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else 22,
                    "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
                    "wind_speed": daily.get("windspeed_10m_max", [])[i] if i < len(daily.get("windspeed_10m_max", [])) else 10,
                    "condition": WMO_CODES.get(code, "Unknown"),
                    "humidity": daily.get("relative_humidity_2m_max", [])[i] if i < len(daily.get("relative_humidity_2m_max", [])) else 60,
                    "rain_chance": probs[i] if i < len(probs) and probs[i] is not None else None,
                    "source": "live",
                }
            )

        temps_max = daily.get("temperature_2m_max", [30])
        temps_min = daily.get("temperature_2m_min", [22])
        precip = daily.get("precipitation_sum", [0])
        winds = daily.get("windspeed_10m_max", [10])
        code_today = daily.get("weathercode", [0])[0] if daily.get("weathercode") else 0

        return WeatherData(
            location=location_name,
            temperature_max=temps_max[0] if temps_max else 30.0,
            temperature_min=temps_min[0] if temps_min else 22.0,
            precipitation=max(
                (precip[0] if precip and precip[0] is not None else 0.0),
                (live.get("precipitation") or 0.0),
            ),
            wind_speed=winds[0] if winds else 10.0,
            humidity=live.get("relative_humidity_2m") or daily.get("relative_humidity_2m_max", [60])[0],
            condition=WMO_CODES.get(code_today, "Clear sky"),
            forecast_days=forecast_days,
        )

    def _mock_weather(self, location_name: str) -> WeatherData:
        today = date.today()
        forecast_days = []
        for i in range(7):
            d = today + timedelta(days=i)
            forecast_days.append(
                {
                    "date": str(d),
                    "temp_max": 30 - i % 3,
                    "temp_min": 22 - i % 2,
                    "precipitation": 5.0 if i % 3 == 0 else 0.0,
                    "wind_speed": 15.0,
                    "condition": "Partly cloudy" if i % 2 == 0 else "Clear sky",
                    "humidity": 65,
                    "rain_chance": None,
                    "source": "fallback",
                }
            )
        return WeatherData(
            location=location_name,
            temperature_max=30.0,
            temperature_min=22.0,
            precipitation=0.0,
            wind_speed=15.0,
            humidity=65.0,
            condition="Partly cloudy",
            forecast_days=forecast_days,
        )

    def get_farming_advice_from_weather(self, weather: WeatherData) -> str:
        """Generate irrigation/farming advice based on weather conditions."""
        advice = []

        if weather.precipitation > 20:
            advice.append(
                "Heavy rain expected — avoid field operations. Check drainage channels. "
                "Postpone pesticide spraying."
            )
        elif weather.precipitation > 5:
            advice.append(
                "Light to moderate rain expected. Good opportunity to apply water-soluble "
                "fertilizers. Avoid pre-emergence herbicide application."
            )
        else:
            advice.append(
                "Dry conditions — irrigate crops as per schedule. "
                "Check soil moisture before next irrigation."
            )

        if weather.temperature_max > 40:
            advice.append(
                "Heat stress alert! Irrigate crops in early morning or evening. "
                "Mulch soil to retain moisture."
            )
        elif weather.temperature_min < 10:
            advice.append(
                "Cold wave warning! Protect nurseries with polythene covers. "
                "Light irrigation can prevent frost damage."
            )

        if weather.wind_speed > 40:
            advice.append(
                "Strong winds — avoid spraying any agrochemicals today. "
                "Secure loose crop supports."
            )

        if not advice:
            advice.append(
                "Weather conditions are favourable for field operations. "
                "Good time for sowing, transplanting, or applying fertilizers."
            )

        return " ".join(advice)
