from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

import jwt
from fastapi import HTTPException, status

from app.core.config import settings

INVALID_TOKEN_DETAIL = "Could not validate credentials"


def signing_secret() -> str:
    configured = (settings.jwt_secret or "").strip()
    if configured:
        return configured
    # Existing Render services do not pick up blueprint generateValue.
    # Derive a stable per-environment secret so login works without Dashboard clicks.
    material = f"{settings.database_url}\0{settings.jwt_algorithm}\0factoryhr-lite-jwt"
    return sha256(material.encode("utf-8")).hexdigest()


def create_access_token(*, username: str, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, signing_secret(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, signing_secret(), algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except jwt.InvalidTokenError as orig:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_DETAIL,
        ) from orig
    username = payload.get("sub")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_DETAIL,
        )
    return payload
