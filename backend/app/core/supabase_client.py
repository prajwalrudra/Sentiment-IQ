"""
SentimentIQ — Supabase Client

Singleton client for interacting with Supabase (Database, Auth, Storage).
"""

from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ── Singleton Supabase Clients ────────────────────────────────

_supabase_client: Client | None = None
_supabase_admin: Client | None = None


def get_supabase_client() -> Client:
    """
    Returns the Supabase client using the ANON key.
    Used for operations that respect Row Level Security (RLS).
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
        logger.info("✅ Supabase client (anon) initialized")
    return _supabase_client


def get_supabase_admin() -> Client:
    """
    Returns the Supabase client using the SERVICE ROLE key.
    Bypasses RLS — use only for server-side admin operations.
    """
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        logger.info("✅ Supabase admin client initialized")
    return _supabase_admin


async def verify_supabase_token(token: str) -> dict | None:
    """
    Verify a Supabase JWT token and return the user data.
    Returns None if the token is invalid.
    """
    try:
        client = get_supabase_client()
        user_response = client.auth.get_user(token)
        if user_response and user_response.user:
            return {
                "id": str(user_response.user.id),
                "email": user_response.user.email,
                "created_at": str(user_response.user.created_at),
            }
        return None
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None
