"""
Simple file-based user store for login/register.
No database required — stores users in data/users.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

USERS_FILE = Path("data/users.json")


def _load_users() -> dict:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(
    name: str,
    email: str,
    password: str,
    state: str,
    district: str,
) -> dict:
    users = _load_users()
    email = email.lower().strip()
    if email in users:
        return {"success": False, "message": "Email already registered."}
    user_id = str(uuid.uuid4())
    users[email] = {
        "id": user_id,
        "name": name.strip(),
        "email": email,
        "password": _hash_password(password),
        "state": state.strip(),
        "district": district.strip(),
        "created_at": datetime.now().isoformat(),
    }
    _save_users(users)
    user = users[email].copy()
    user.pop("password")
    return {"success": True, "message": "Registration successful!", "user": user}


def login_user(email: str, password: str) -> dict:
    users = _load_users()
    email = email.lower().strip()
    user = users.get(email)
    if not user:
        return {"success": False, "message": "Email not found."}
    if user["password"] != _hash_password(password):
        return {"success": False, "message": "Incorrect password."}
    profile = user.copy()
    profile.pop("password")
    return {"success": True, "message": "Login successful!", "user": profile}


def get_user(email: str) -> Optional[dict]:
    users = _load_users()
    user = users.get(email.lower().strip())
    if user:
        profile = user.copy()
        profile.pop("password", None)
        return profile
    return None
