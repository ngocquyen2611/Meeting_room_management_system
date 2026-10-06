import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt

from room_service.core.config import settings

# In-memory cache cho JWKS
_jwks_cache: dict[str, Any] | None = None
_jwks_cache_expiry: float = 0
JWKS_CACHE_TTL = 3600  # 1 giờ


def get_jwks(force_refresh: bool = False) -> dict[str, Any]:
    """
    Lấy danh sách Public Keys (JWKS) từ Auth0 với in-memory caching.
    """
    global _jwks_cache, _jwks_cache_expiry
    now = time.time()

    if _jwks_cache and not force_refresh and now < _jwks_cache_expiry:
        return _jwks_cache

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(settings.auth0_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_expiry = now + JWKS_CACHE_TTL
            return _jwks_cache
    except Exception as e:  # noqa: BLE001 - keep stale JWKS usable
        # Nếu fetch lỗi nhưng có cache cũ thì fallback về cache cũ
        if _jwks_cache:
            return _jwks_cache
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to fetch JWKS from Auth0: {e!s}",
        )


def verify_jwt(token: str, mock_jwks: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Xác minh chữ ký mã hóa (RS256 Cryptographic Verification) của JWT từ Auth0.
    Kiểm tra đầy đủ: Signature, Audience, Issuer, Expiration.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    rsa_key: dict[str, Any] = {}
    jwks = mock_jwks if mock_jwks is not None else get_jwks()

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token header missing 'kid'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            rsa_key = {
                "kty": key.get("kty"),
                "kid": key.get("kid"),
                "use": key.get("use"),
                "n": key.get("n"),
                "e": key.get("e"),
            }
            break

    if not rsa_key:
        # Thử refresh cache nếu không tìm thấy key (phòng khi Auth0 vừa xoay key)
        if mock_jwks is None:
            jwks = get_jwks(force_refresh=True)
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = {
                        "kty": key.get("kty"),
                        "kid": key.get("kid"),
                        "use": key.get("use"),
                        "n": key.get("n"),
                        "e": key.get("e"),
                    }
                    break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching public key for token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.AUTH0_ALGORITHMS],
            audience=settings.AUTH0_AUDIENCE,
            issuer=settings.auth0_issuer,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid claims (audience/issuer mismatch): {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        )
