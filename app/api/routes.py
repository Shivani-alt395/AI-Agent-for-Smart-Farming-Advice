"""
FastAPI router — farming agent + auth endpoints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, EmailStr
from loguru import logger

from app.models.schemas import (
    FarmingQuery, FarmingResponse, HealthResponse, MandiPrice, WeatherData, Language,
)
from app.services.farming_agent import get_farming_agent
from app.services.weather_service import WeatherService
from app.services.market_service import MarketService
from app.core.rag_pipeline import get_rag_pipeline
from app.core.granite_llm import GraniteLLM

router = APIRouter()


# ══════════════════════════════════════════════════════
# AUTH MODELS
# ══════════════════════════════════════════════════════

class SendOTPRequest(BaseModel):
    name: str
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    state: str
    district: str
    otp: str  # must be verified before registering

class LoginRequest(BaseModel):
    email: str
    password: str


# ══════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════

@router.post("/auth/send-otp", summary="Send OTP to email for verification")
async def send_otp(req: SendOTPRequest) -> Dict[str, Any]:
    """
    Generate a 6-digit OTP and email it to the user.
    If SMTP is not configured, returns the OTP in the response (dev/demo mode).
    """
    from app.services.email_service import generate_otp, send_otp_email
    otp = generate_otp(req.email)
    result = send_otp_email(req.email, req.name, otp)

    if result.get("mode") in ("console", "console_fallback"):
        # SMTP not configured — return OTP so user can still register in demo mode
        return {
            "success": True,
            "message": "SMTP not configured. Use the OTP shown below (demo mode).",
            "demo_otp": otp,
            "note": "Configure SMTP_USER and SMTP_PASSWORD in .env to send real emails.",
        }
    return {"success": True, "message": f"Verification code sent to {req.email}. Check your inbox."}


@router.post("/auth/verify-otp", summary="Verify the OTP code")
async def verify_otp_endpoint(req: VerifyOTPRequest) -> Dict[str, Any]:
    from app.services.email_service import verify_otp
    if verify_otp(req.email, req.otp):
        return {"success": True, "message": "Email verified successfully."}
    raise HTTPException(status_code=400, detail="Invalid or expired OTP. Please request a new code.")


@router.post("/auth/register", summary="Register a new farmer (requires verified OTP)")
async def register(req: RegisterRequest) -> Dict[str, Any]:
    from app.services.email_service import verify_otp
    from app.services.user_store import register_user
    # Re-verify OTP at registration time
    if not verify_otp(req.email, req.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP. Please verify your email first.")
    result = register_user(req.name, req.email, req.password, req.state, req.district)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/auth/login", summary="Login farmer")
async def login(req: LoginRequest) -> Dict[str, Any]:
    from app.services.user_store import login_user
    result = login_user(req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result


# ══════════════════════════════════════════════════════
# FARMING AGENT ROUTES
# ══════════════════════════════════════════════════════

@router.post("/ask", response_model=FarmingResponse, summary="Ask the Smart Farming Agent")
async def ask_farming_agent(query: FarmingQuery) -> FarmingResponse:
    """Send a farming question to the IBM Granite-powered RAG agent."""
    try:
        agent = get_farming_agent()
        response = await agent.process_query(query)
        return response
    except Exception as exc:
        logger.error(f"Agent error: {exc}")
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(exc)}")


@router.get("/weather", response_model=WeatherData, summary="Get weather forecast")
async def get_weather(
    latitude: float  = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    location: str    = Query(default="Your Farm"),
    days: int        = Query(default=7, ge=1, le=14),
) -> WeatherData:
    return await WeatherService().get_weather(latitude, longitude, location, days)


@router.get("/prices", response_model=List[MandiPrice], summary="Get mandi prices")
async def get_mandi_prices(
    commodity: Optional[str] = Query(default=None),
    state: Optional[str]     = Query(default=None),
    district: Optional[str]  = Query(default=None),
    limit: int               = Query(default=15, ge=1, le=50),
) -> List[MandiPrice]:
    return await MarketService().get_prices(commodity=commodity, state=state, district=district, limit=limit)


@router.post("/ingest", summary="Load knowledge base into vector store")
async def ingest_knowledge_base(background_tasks: BackgroundTasks) -> Dict[str, str]:
    def _ingest():
        from app.services.knowledge_base import load_knowledge_base
        count = load_knowledge_base()
        logger.info(f"Knowledge base ingestion complete: {count} chunks.")
    background_tasks.add_task(_ingest)
    return {"message": "Knowledge base ingestion started in background."}


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    rag = get_rag_pipeline()
    llm = GraniteLLM.from_settings()
    return HealthResponse(
        status="healthy", version="1.0.0",
        granite_available=llm._model is not None,
        vector_store_ready=rag.is_ready,
        message=(
            "IBM Granite connected ✓" if llm._model is not None
            else "Demo mode — add IBM_API_KEY to .env for full Granite access"
        ),
    )


@router.get("/languages", summary="Supported languages")
async def list_languages() -> Dict[str, str]:
    return {
        "en":"English","hi":"Hindi (हिंदी)","mr":"Marathi (मराठी)",
        "te":"Telugu (తెలుగు)","ta":"Tamil (தமிழ்)","kn":"Kannada (ಕನ್ನಡ)",
        "gu":"Gujarati (ગુજરાતી)","pa":"Punjabi (ਪੰਜਾਬੀ)","bn":"Bengali (বাংলা)","or":"Odia (ଓଡ଼ିଆ)",
    }


@router.get("/sample-questions", summary="Sample farming questions")
async def get_sample_questions() -> Dict[str, List[str]]:
    return {
        "crop":   ["What crop is best for Kharif season in Maharashtra?","Which vegetables can I grow in summer?"],
        "weather":["When should I irrigate my wheat crop?","Is it safe to spray pesticides tomorrow?"],
        "pest":   ["There are yellow spots on my rice leaves, what should I do?","How to control stem borer?"],
        "market": ["What is today's mandi rate for tomatoes?","What is the MSP for wheat this year?"],
        "soil":   ["How do I improve my sandy soil?","How much fertilizer should I apply for cotton?"],
    }
