"""
SentimentIQ — Scrape & Analyze Endpoint

POST /api/scrape — Scrape product reviews from a URL and run full NLP analysis.
GET  /api/scrape/presets — Get available preset products for demo.
"""

import time
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from app.ml.schemas import ScrapeRequest, ScrapeResult, SentimentLabel, EmotionDistribution
from app.ml.pipeline import NLPPipeline
from app.api.deps import get_nlp_pipeline, get_current_user
from app.core.supabase_client import get_supabase_admin
from app.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Scraping"])


# ── Preset products for demo ─────────────────────────────────
PRESET_PRODUCTS = [
    {
        "id": "headphones",
        "name": "ProSound X500 Noise-Cancelling Headphones",
        "url": "https://example.com/products/headphones",
        "category": "electronics",
    },
    {
        "id": "smartwatch",
        "name": "FitTrack Ultra Smartwatch",
        "url": "https://example.com/products/smartwatch",
        "category": "electronics",
    },
    {
        "id": "laptop",
        "name": "ThinBook Pro 14\" Laptop",
        "url": "https://example.com/products/laptop",
        "category": "electronics",
    },
    {
        "id": "skincare",
        "name": "GlowUp Vitamin C Serum",
        "url": "https://example.com/products/skincare",
        "category": "beauty",
    },
    {
        "id": "coffee",
        "name": "BeanMaster Premium Dark Roast Coffee",
        "url": "https://example.com/products/coffee",
        "category": "food",
    },
    {
        "id": "saas",
        "name": "TaskFlow Project Management Software",
        "url": "https://example.com/products/saas",
        "category": "software",
    },
]


@router.get("/scrape/presets")
async def get_presets():
    """Get available preset products for demo scraping."""
    return {"presets": PRESET_PRODUCTS}


@router.post("/scrape", response_model=ScrapeResult)
@limiter.limit("5/minute")
async def scrape_and_analyze(
    request: Request,
    body: ScrapeRequest,
    pipeline: NLPPipeline = Depends(get_nlp_pipeline),
    current_user: dict = Depends(get_current_user),
):
    """
    Scrape product reviews from a URL and analyze them.

    - Attempts real scraping via BeautifulSoup + httpx
    - Falls back to realistic mock data if scraping fails
    - Runs all reviews through the full NLP pipeline
    """
    start_time = time.time()
    logger.info(f"🔍 Scraping: {body.url}")

    # Import scraping modules
    from app.scraper.engine import scrape_reviews
    from app.scraper.mock import generate_mock_reviews

    # ── Step 1: Get reviews ──────────────────────────────────────
    reviews = []
    source = "scraped"
    product_name = "Unknown Product"

    if body.use_mock:
        # Force mock
        product_name, reviews = generate_mock_reviews(body.url)
        source = "mock"
    else:
        try:
            product_name, reviews = await scrape_reviews(
                url=body.url,
                max_pages=body.max_pages,
            )
            source = "scraped"
            logger.info(f"  ✅ Scraped {len(reviews)} reviews")
        except Exception as e:
            logger.warning(f"  ⚠️ Scraping failed ({e}), falling back to mock data")
            product_name, reviews = generate_mock_reviews(body.url)
            source = "mock"

    if not reviews:
        product_name, reviews = generate_mock_reviews(body.url)
        source = "mock"

    # ── Step 2: Analyze each review ──────────────────────────────
    analyzed_reviews = []
    all_sentiments = []
    all_aspects = {}
    emotion_totals = {}
    rating_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    for review in reviews:
        text = review.get("text", "")
        rating = review.get("rating")

        if rating:
            rating_distribution[str(int(rating))] = rating_distribution.get(str(int(rating)), 0) + 1

        analysis = pipeline.analyze(text)

        all_sentiments.append(analysis.overall_sentiment.value)

        # Aggregate aspects
        for aspect in analysis.aspect_sentiments:
            if aspect.aspect not in all_aspects:
                all_aspects[aspect.aspect] = {
                    "positive": 0, "negative": 0, "neutral": 0, "mentions": 0
                }
            all_aspects[aspect.aspect][aspect.sentiment.value] += 1
            all_aspects[aspect.aspect]["mentions"] += 1

        # Aggregate emotions
        for field, value in analysis.emotion_distribution.model_dump().items():
            emotion_totals[field] = emotion_totals.get(field, 0) + value

        analyzed_reviews.append({
            "text": text,
            "rating": rating,
            "reviewer_name": review.get("reviewer_name", "Anonymous"),
            "date": review.get("date", ""),
            "sentiment": analysis.overall_sentiment.value,
            "confidence": analysis.overall_confidence,
            "emotions": analysis.emotion_distribution.model_dump(),
            "aspects": [a.model_dump() for a in analysis.aspect_sentiments],
        })

    # ── Step 3: Compute aggregates ───────────────────────────────
    total = len(analyzed_reviews)
    sentiment_dist = {
        "positive": all_sentiments.count("positive") / max(total, 1),
        "negative": all_sentiments.count("negative") / max(total, 1),
        "neutral": all_sentiments.count("neutral") / max(total, 1),
        "mixed": all_sentiments.count("mixed") / max(total, 1),
    }

    # Overall sentiment
    most_common = max(sentiment_dist, key=sentiment_dist.get)
    overall_sentiment = SentimentLabel(most_common)

    # Average emotions
    avg_emotions = EmotionDistribution(
        **{k: round(v / max(total, 1), 4) for k, v in emotion_totals.items()}
    ) if emotion_totals else EmotionDistribution()

    # Top aspects
    from app.ml.schemas import AspectSentiment
    top_aspects = []
    for aspect_name, counts in sorted(all_aspects.items(), key=lambda x: x[1]["mentions"], reverse=True)[:15]:
        if counts["positive"] >= counts["negative"]:
            asp_sentiment = SentimentLabel.POSITIVE
        else:
            asp_sentiment = SentimentLabel.NEGATIVE

        top_aspects.append(AspectSentiment(
            aspect=aspect_name,
            sentiment=asp_sentiment,
            confidence=round(max(counts["positive"], counts["negative"]) / counts["mentions"], 4),
            mention_count=counts["mentions"],
        ))

    # Key strengths & weaknesses
    key_strengths = [a.aspect for a in top_aspects if a.sentiment == SentimentLabel.POSITIVE][:5]
    key_weaknesses = [a.aspect for a in top_aspects if a.sentiment == SentimentLabel.NEGATIVE][:5]

    # Average rating
    total_ratings = sum(rating_distribution.values())
    avg_rating = None
    if total_ratings > 0:
        avg_rating = round(
            sum(int(k) * v for k, v in rating_distribution.items()) / total_ratings,
            2
        )

    processing_time = (time.time() - start_time) * 1000

    result = ScrapeResult(
        product_name=product_name,
        product_url=body.url,
        source=source,
        total_reviews=total,
        average_rating=avg_rating,
        rating_distribution=rating_distribution,
        overall_sentiment=overall_sentiment,
        sentiment_distribution=sentiment_dist,
        emotion_distribution=avg_emotions,
        top_aspects=top_aspects,
        reviews=analyzed_reviews,
        key_strengths=key_strengths,
        key_weaknesses=key_weaknesses,
        processing_time_ms=round(processing_time, 2),
    )

    # Save to Supabase if authenticated
    if current_user:
        try:
            supabase = get_supabase_admin()
            supabase.table("scraped_products").insert({
                "user_id": current_user["id"],
                "url": body.url,
                "product_name": product_name,
                "total_reviews": total,
                "avg_rating": avg_rating,
                "sentiment_summary": {
                    "distribution": sentiment_dist,
                    "overall": overall_sentiment.value,
                },
                "reviews": analyzed_reviews[:50],  # Store max 50
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to save scrape result: {e}")

    logger.info(f"✅ Scrape complete: {total} reviews, {overall_sentiment.value}, {processing_time:.0f}ms")
    return result
