"""
Entry point — run with: python run.py
Or: uvicorn run:app --reload
"""
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(".env"))

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "run:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level="info",
    )
