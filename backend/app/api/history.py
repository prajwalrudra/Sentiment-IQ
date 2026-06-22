"""
SentimentIQ — History Endpoint

GET    /api/history     — List past analyses (requires auth)
GET    /api/history/:id — Get a specific analysis
DELETE /api/history/:id — Delete an analysis
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import require_auth
from app.core.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["History"])


@router.get("/history")
async def list_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source: str = Query(None, description="Filter by source: manual, batch, scrape"),
    sentiment: str = Query(None, description="Filter by sentiment: positive, negative, neutral, mixed"),
    current_user: dict = Depends(require_auth),
):
    """
    List the authenticated user's past analyses with pagination and filters.
    """
    try:
        supabase = get_supabase_admin()
        query = (
            supabase.table("analyses")
            .select("id, input_text, overall_sentiment, overall_confidence, source, created_at")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .range((page - 1) * limit, page * limit - 1)
        )

        if source:
            query = query.eq("source", source)
        if sentiment:
            query = query.eq("overall_sentiment", sentiment)

        result = query.execute()

        # Truncate input text for listing
        items = []
        for row in result.data:
            row["input_text"] = row["input_text"][:200] + ("..." if len(row["input_text"]) > 200 else "")
            items.append(row)

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": len(items),
        }

    except Exception as e:
        logger.error(f"History list error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.get("/history/{analysis_id}")
async def get_analysis_detail(
    analysis_id: str,
    current_user: dict = Depends(require_auth),
):
    """Get full details of a specific past analysis."""
    try:
        supabase = get_supabase_admin()
        result = (
            supabase.table("analyses")
            .select("*")
            .eq("id", analysis_id)
            .eq("user_id", current_user["id"])
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis")


@router.delete("/history/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: dict = Depends(require_auth),
):
    """Delete a specific analysis from history."""
    try:
        supabase = get_supabase_admin()
        result = (
            supabase.table("analyses")
            .delete()
            .eq("id", analysis_id)
            .eq("user_id", current_user["id"])
            .execute()
        )

        return {"message": "Analysis deleted successfully", "id": analysis_id}

    except Exception as e:
        logger.error(f"History delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete analysis")
