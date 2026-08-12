"""Supabase JWT verification (JWKS for asymmetric keys + optional legacy HS256)."""

from __future__ import annotations

import logging
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
    return PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True)


def decode_supabase_access_token(token: str) -> dict:
    """Validate a Supabase-issued access token and return its payload."""
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"

    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            audience="authenticated",
            issuer=issuer,
        )
    except jwt.PyJWTError as jwks_error:
        if not settings.supabase_jwt_secret:
            logger.warning("Supabase JWKS verification failed: %s", jwks_error)
            raise

        try:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=issuer,
            )
        except jwt.PyJWTError:
            logger.warning(
                "Supabase token verification failed (JWKS and legacy HS256): %s",
                jwks_error,
            )
            raise
