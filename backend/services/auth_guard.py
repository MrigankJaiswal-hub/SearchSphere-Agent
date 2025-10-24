# optional: bearer token or key auth
# backend/services/auth_guard.py
import os
from fastapi import Header, HTTPException

API_KEY_EXPECTED = os.getenv("API_KEY")  # optional

def require_api_key(x_api_key: str = Header(None)):
    if API_KEY_EXPECTED and x_api_key != API_KEY_EXPECTED:
        raise HTTPException(status_code=401, detail="Invalid API key")
