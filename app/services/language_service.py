"""
Language detection and translation service.
Uses deep-translator for multi-language support (Hindi, Marathi, Telugu, etc.)
"""
from __future__ import annotations

from typing import Optional

from loguru import logger

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not installed — language detection disabled.")

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logger.warning("deep-translator not installed — translation disabled.")


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "bn": "Bengali",
    "or": "Odia",
}


class LanguageService:
    """Detect and translate text for multilingual farmer interactions."""

    def detect_language(self, text: str) -> str:
        """Detect the language of input text. Returns ISO 639-1 code."""
        if not LANGDETECT_AVAILABLE or len(text.strip()) < 5:
            return "en"
        try:
            lang = detect(text)
            return lang if lang in LANGUAGE_NAMES else "en"
        except Exception:
            return "en"

    def translate_to_english(self, text: str, source_lang: str = "auto") -> str:
        """Translate text from any language to English."""
        if source_lang == "en" or not TRANSLATOR_AVAILABLE:
            return text
        try:
            translator = GoogleTranslator(source=source_lang, target="en")
            result = translator.translate(text)
            return result or text
        except Exception as exc:
            logger.warning(f"Translation to English failed: {exc}")
            return text

    def translate_from_english(self, text: str, target_lang: str = "en") -> str:
        """Translate English text to the target language."""
        if target_lang == "en" or not TRANSLATOR_AVAILABLE:
            return text
        try:
            translator = GoogleTranslator(source="en", target=target_lang)
            # GoogleTranslator has a 5000 char limit; split if needed
            if len(text) > 4500:
                chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
                translated_chunks = [translator.translate(c) or c for c in chunks]
                return " ".join(translated_chunks)
            result = translator.translate(text)
            return result or text
        except Exception as exc:
            logger.warning(f"Translation from English to '{target_lang}' failed: {exc}")
            return text

    def get_language_name(self, lang_code: str) -> str:
        return LANGUAGE_NAMES.get(lang_code, "Unknown")
