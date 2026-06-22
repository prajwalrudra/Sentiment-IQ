"""
SentimentIQ — Stats Endpoint

GET /api/stats — Returns aggregated analytics for the authenticated user:
  - Total analyses, batch jobs, and scrape sessions
  - Sentiment breakdown (positive / negative / neutral / mixed counts)
  - Average confidence score
  - Top detected emotion across all analyses
  - Recent activity (last 7 days)
  - Sentiment trend (last 30 days, grouped by day)
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import require_auth
from app.core.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Stats"])


@router.get("/stats")
async def get_stats(current_user: dict = Depends(require_auth)):
    """
    Return aggregated dashboard statistics for the current user.
    Pulls from the analyses, batch_jobs, and scraped_products tables.
    """
    try:
        supabase = get_supabase_admin()
        user_id = current_user["id"]

        # ── 1. All analyses for this user ─────────────────────────
        analyses_result = (
            supabase.table("analyses")
            .select("overall_sentiment, overall_confidence, emotion_distribution, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
        analyses = analyses_result.data or []

        # ── 2. Batch jobs ──────────────────────────────────────────
        batch_result = (
            supabase.table("batch_jobs")
            .select("id, status, total_reviews")
            .eq("user_id", user_id)
            .execute()
        )
        batch_jobs = batch_result.data or []

        # ── 3. Scraped products ────────────────────────────────────
        scrape_result = (
            supabase.table("scraped_products")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        scrape_sessions = scrape_result.data or []

        # ── 4. Compute sentiment breakdown ─────────────────────────
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        total_confidence = 0.0
        emotion_totals: dict[str, float] = {}

        for row in analyses:
            s = row.get("overall_sentiment", "neutral")
            if s in sentiment_counts:
                sentiment_counts[s] += 1
            total_confidence += row.get("overall_confidence", 0.0)

            # Aggregate emotions
            emotions = row.get("emotion_distribution") or {}
            if isinstance(emotions, dict):
                for emotion, score in emotions.items():
                    if isinstance(score, (int, float)):
                        emotion_totals[emotion] = emotion_totals.get(emotion, 0.0) + score

        total_analyses = len(analyses)
        avg_confidence = round(total_confidence / total_analyses, 4) if total_analyses > 0 else 0.0

        # Top emotion overall
        top_emotion = (
            max(emotion_totals, key=emotion_totals.get)
            if emotion_totals
            else None
        )

        # ── 5. Recent activity (last 7 days) ──────────────────────
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent_analyses = [
            row for row in analyses
            if row.get("created_at", "") >= seven_days_ago
        ]

        # ── 6. Sentiment trend — last 30 days, grouped by date ────
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        trend_map: dict[str, dict] = {}

        for row in analyses:
            raw_date = row.get("created_at", "")
            if not raw_date:
                continue
            try:
                # Parse ISO timestamp and extract date part
                dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                if dt < thirty_days_ago:
                    continue
                day = dt.strftime("%Y-%m-%d")
            except Exception:
                continue

            if day not in trend_map:
                trend_map[day] = {"date": day, "positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "total": 0}

            s = row.get("overall_sentiment", "neutral")
            if s in trend_map[day]:
                trend_map[day][s] += 1
            trend_map[day]["total"] += 1

        # Sort trend by date
        trend = sorted(trend_map.values(), key=lambda x: x["date"])

        # ── 7. Total reviews processed across all batch jobs ───────
        total_batch_reviews = sum(j.get("total_reviews", 0) for j in batch_jobs)

        return {
            "total_analyses": total_analyses,
            "total_batch_jobs": len(batch_jobs),
            "total_batch_reviews": total_batch_reviews,
            "total_scrape_sessions": len(scrape_sessions),
            "sentiment_breakdown": sentiment_counts,
            "avg_confidence": avg_confidence,
            "top_emotion": top_emotion,
            "recent_7_days": len(recent_analyses),
            "trend": trend,
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")
