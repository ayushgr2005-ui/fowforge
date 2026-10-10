from fastapi import Header, HTTPException, status
from app.core.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)):
    if not settings.auth_enabled:
        return
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
