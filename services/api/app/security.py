from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import TOKEN_SECRET, TOKEN_TTL_SECONDS
from .db import get_db
from .models import Profile

bearer = HTTPBearer(auto_error=False)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def issue_token(user_id: str) -> str:
    payload = {"sub": user_id, "iat": int(time.time()), "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(TOKEN_SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def verify_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
        expected = _b64(hmac.new(TOKEN_SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if payload.get("exp", 0) < time.time():
            raise ValueError("expired token")
        return payload
    except (ValueError, json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(status_code=401, detail={"code": "invalid_token", "message": "Session is invalid or expired."}) from exc


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> Profile:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"code": "authentication_required", "message": "Use the local demo sign-in endpoint to start a session."})
    payload = verify_token(credentials.credentials)
    user = db.get(Profile, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail={"code": "unknown_user", "message": "Session user was not found."})
    return user


def require_role(*roles: str):
    def dependency(user: Profile = Depends(current_user)) -> Profile:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Your role cannot perform this action."})
        return user
    return dependency

