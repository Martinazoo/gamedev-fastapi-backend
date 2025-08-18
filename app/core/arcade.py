# app/core/arcade_sessions.py
import uuid
from typing import Dict

arcade_sessions: Dict[str, dict] = {}

def create_session():
    session_id = str(uuid.uuid4())
    arcade_sessions[session_id] = {"confirmed": False, "token": None, "username": None}
    return session_id

def confirm_session(session_id: str, token: str, username: str):
    if session_id in arcade_sessions:
        arcade_sessions[session_id] = {"confirmed": True, "token": token, "username": username}

def check_session(session_id: str):
    return arcade_sessions.get(session_id)
