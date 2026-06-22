"""
SentimentIQ — API Dependencies

Dependency injection functions for FastAPI route handlers.
Provides: current user auth, NLP pipeline, and Supabase client.
"""

from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.core.supabase_client import verify_supabase_token, get_supabase_client
from app.ml.pipeline import get_pipeline, NLPPipeline


async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Extract and verify the Supabase JWT from the Authorization header.
    Returns the user dict or None if no auth provided.
    """
    if not authorization:
        return None

    # Handle "Bearer <token>" format
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    user = await verify_supabase_token(token)
    return user


async def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """
    Require authentication — raises 401 if no valid token.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required")
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    user = await verify_supabase_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    return user


def get_nlp_pipeline() -> NLPPipeline:
    """Get the loaded NLP pipeline singleton."""
    pipeline = get_pipeline()
    if not pipeline.is_loaded:
        raise HTTPException(status_code=503, detail="NLP models are still loading. Please try again shortly.")
    return pipeline
