"""
Entry point — run with: python run.py
Or: uvicorn run:app --host 0.0.0.0 --port $PORT
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (local dev only; Render injects env vars directly)
load_dotenv(Path(".env"))

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings

    settings = get_settings()
    # Render (and most PaaS) set $PORT — use it if present, else fall back to config
    port = int(os.environ.get("PORT", settings.app_port))
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=port,
        reload=settings.app_debug,
        log_level="info",
    )
