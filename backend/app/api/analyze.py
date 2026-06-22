"""
SentimentIQ — Real-time Analysis Endpoint

POST /api/analyze — Analyze text in real-time with sentiment, emotions, and aspects.
"""

from fastapi import APIRouter, Depends, Request
from app.ml.schemas import AnalyzeRequest, AnalysisResult
from app.ml.pipeline import NLPPipeline
from app.api.deps import get_nlp_pipeline, get_current_user
from app.core.supabase_client import get_supabase_admin
from app.core.limiter import limiter
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analyze", response_model=AnalysisResult)
@limiter.limit("20/minute")
async def analyze_text(
    request: Request,
    body: AnalyzeRequest,
    pipeline: NLPPipeline = Depends(get_nlp_pipeline),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze text for sentiment, emotions, and aspect-based sentiment.

    - Splits text into sentences
    - Classifies each sentence as positive/negative/neutral
    - Detects emotions (joy, anger, sadness, fear, surprise, etc.)
    - Extracts product aspects and their sentiments
    """
    logger.info(f"📝 Analyzing text ({len(body.text)} chars)")

    # Run the NLP pipeline
    result = pipeline.analyze(
        text=body.text,
        include_emotions=body.include_emotions,
        include_aspects=body.include_aspects,
    )

    # Save to Supabase if user is authenticated
    if current_user:
        try:
            supabase = get_supabase_admin()
            supabase.table("analyses").insert({
                "user_id": current_user["id"],
                "input_text": result.input_text[:5000],  # Limit stored text
                "overall_sentiment": result.overall_sentiment.value,
                "overall_confidence": result.overall_confidence,
                "emotion_distribution": result.emotion_distribution.model_dump(),
                "aspect_sentiments": [a.model_dump() for a in result.aspect_sentiments],
                "sentences": [s.model_dump() for s in result.sentences],
                "source": "manual",
            }).execute()
            logger.info(f"  💾 Saved analysis for user {current_user['id']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Failed to save analysis: {e}")

    logger.info(
        f"  ✅ Result: {result.overall_sentiment.value} "
        f"({result.overall_confidence:.2f}) in {result.processing_time_ms:.0f}ms"
    )

    return result
