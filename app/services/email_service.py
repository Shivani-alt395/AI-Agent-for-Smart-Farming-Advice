"""
Email OTP verification service.
Uses Python's built-in smtplib — works with Gmail App Password (free).
Falls back to console-print mode when SMTP is not configured.
"""
from __future__ import annotations

import random
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Tuple

from loguru import logger

# In-memory OTP store: { email: (otp_code, expires_at) }
_otp_store: Dict[str, Tuple[str, float]] = {}
OTP_TTL_SECONDS = 600  # 10 minutes


def _get_smtp_config() -> dict:
    """Read SMTP settings from environment."""
    import os
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_name": os.getenv("SMTP_FROM_NAME", "Smart Farming AI Agent"),
    }


def generate_otp(email: str) -> str:
    """Generate a 6-digit OTP and store it (expires in 10 min)."""
    otp = str(random.randint(100000, 999999))
    _otp_store[email.lower().strip()] = (otp, time.time() + OTP_TTL_SECONDS)
    return otp


def verify_otp(email: str, otp: str) -> bool:
    """Return True if the OTP is valid and not expired."""
    key = email.lower().strip()
    record = _otp_store.get(key)
    if not record:
        return False
    stored_otp, expires_at = record
    if time.time() > expires_at:
        del _otp_store[key]
        return False
    if stored_otp != otp.strip():
        return False
    del _otp_store[key]  # single-use
    return True


def send_otp_email(email: str, name: str, otp: str) -> dict:
    """
    Send OTP to the given email via SMTP.
    Falls back to console log if SMTP not configured.
    """
    cfg = _get_smtp_config()

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;background:#f9f9f9;border-radius:10px;overflow:hidden">
      <div style="background:#1a7f3c;padding:24px;text-align:center">
        <h2 style="color:#fff;margin:0">🌾 Smart Farming AI Agent</h2>
        <p style="color:rgba(255,255,255,.8);margin:4px 0 0">Email Verification</p>
      </div>
      <div style="padding:28px 32px;background:#fff">
        <p style="color:#333;font-size:15px">Hello <strong>{name}</strong>,</p>
        <p style="color:#555;font-size:14px">Use the verification code below to complete your registration:</p>
        <div style="background:#f0fdf4;border:2px dashed #1a7f3c;border-radius:8px;padding:20px;text-align:center;margin:20px 0">
          <span style="font-size:36px;font-weight:800;letter-spacing:10px;color:#1a7f3c">{otp}</span>
        </div>
        <p style="color:#888;font-size:12px">This code expires in <strong>10 minutes</strong>. Do not share it with anyone.</p>
        <p style="color:#888;font-size:12px">If you didn't request this, please ignore this email.</p>
      </div>
      <div style="background:#f4f4f4;padding:12px;text-align:center;font-size:11px;color:#999">
        Powered by IBM Cloud Lite + IBM Granite · Smart Farming AI Agent
      </div>
    </div>
    """

    if not cfg["user"] or cfg["user"] == "your_gmail@gmail.com":
        # Dev/demo mode — print to console
        logger.warning(
            f"SMTP not configured. OTP for {email}: {otp} "
            "(Set SMTP_USER and SMTP_PASSWORD in .env to send real emails)"
        )
        return {"success": True, "mode": "console", "otp": otp}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp} — Your Smart Farming AI Verification Code"
        msg["From"]    = f"{cfg['from_name']} <{cfg['user']}>"
        msg["To"]      = email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["user"], email, msg.as_string())

        logger.info(f"OTP email sent to {email}")
        return {"success": True, "mode": "email"}
    except Exception as exc:
        logger.error(f"SMTP send failed: {exc}. Falling back to console mode.")
        logger.warning(f"FALLBACK OTP for {email}: {otp}")
        return {"success": True, "mode": "console_fallback", "otp": otp}
