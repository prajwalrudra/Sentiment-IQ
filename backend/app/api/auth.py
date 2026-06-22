"""
SentimentIQ — Auth Endpoint

Proxies Supabase Auth operations to the frontend.
POST /api/auth/signup  — Register a new user
POST /api/auth/login   — Login with email/password
POST /api/auth/logout  — Logout (invalidate session)
GET  /api/auth/me      — Get current user profile
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.supabase_client import get_supabase_client
from app.api.deps import require_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


@router.post("/signup", response_model=AuthResponse)
async def signup(request: AuthRequest):
    """Register a new user via Supabase Auth."""
    try:
        client = get_supabase_client()
        result = client.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })

        if result.user is None:
            raise HTTPException(status_code=400, detail="Signup failed. Please check your credentials.")

        return AuthResponse(
            access_token=result.session.access_token if result.session else "",
            refresh_token=result.session.refresh_token if result.session else "",
            user={
                "id": str(result.user.id),
                "email": result.user.email,
                "created_at": str(result.user.created_at),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(request: AuthRequest):
    """Login with email and password via Supabase Auth."""
    try:
        client = get_supabase_client()
        result = client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if result.user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return AuthResponse(
            access_token=result.session.access_token,
            refresh_token=result.session.refresh_token,
            user={
                "id": str(result.user.id),
                "email": result.user.email,
                "created_at": str(result.user.created_at),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/logout")
async def logout():
    """Logout is handled client-side by clearing the token."""
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(require_auth)):
    """Get the current authenticated user's profile."""
    return {"user": current_user}
