"""
Configuration management using Pydantic Settings.
Loads all values from environment variables / .env file.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # IBM watsonx.ai
    ibm_api_key: str = Field(default="", env="IBM_API_KEY")
    ibm_watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com", env="IBM_WATSONX_URL"
    )
    ibm_watsonx_project_id: str = Field(default="", env="IBM_WATSONX_PROJECT_ID")

    # IBM Granite model
    granite_model_id: str = Field(
        default="ibm/granite-4-h-small", env="GRANITE_MODEL_ID"
    )
    granite_max_tokens: int = Field(default=1024, env="GRANITE_MAX_TOKENS")
    granite_temperature: float = Field(default=0.3, env="GRANITE_TEMPERATURE")
    granite_top_p: float = Field(default=0.9, env="GRANITE_TOP_P")
    granite_top_k: int = Field(default=50, env="GRANITE_TOP_K")

    # Watson Assistant (optional)
    watson_assistant_api_key: str = Field(default="", env="WATSON_ASSISTANT_API_KEY")
    watson_assistant_url: str = Field(default="", env="WATSON_ASSISTANT_URL")
    watson_assistant_id: str = Field(default="", env="WATSON_ASSISTANT_ID")

    # External APIs
    weather_api_url: str = Field(
        default="https://api.open-meteo.com/v1/forecast", env="WEATHER_API_URL"
    )
    openweather_api_key: str = Field(default="", env="OPENWEATHER_API_KEY")
    data_gov_api_key: str = Field(default="", env="DATA_GOV_API_KEY")
    data_gov_mandi_url: str = Field(
        default="https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
        env="DATA_GOV_MANDI_URL",
    )

    # App settings
    app_name: str = Field(default="Smart Farming AI Agent", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    app_debug: bool = Field(default=False, env="APP_DEBUG")
    secret_key: str = Field(default="changeme", env="SECRET_KEY")

    # ChromaDB
    chroma_persist_dir: str = Field(default="./data/chroma_db", env="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(
        default="smart_farming_knowledge", env="CHROMA_COLLECTION_NAME"
    )

    # Embedding
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL"
    )

    # Languages
    supported_languages: str = Field(
        default="en,hi,mr,te,ta,kn,gu,pa,bn,or", env="SUPPORTED_LANGUAGES"
    )

    # RAG
    rag_top_k: int = Field(default=5, env="RAG_TOP_K")
    rag_chunk_size: int = Field(default=512, env="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=64, env="RAG_CHUNK_OVERLAP")

    @property
    def supported_language_list(self) -> List[str]:
        return [lang.strip() for lang in self.supported_languages.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
