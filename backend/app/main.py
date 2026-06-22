"""
SentimentIQ — FastAPI Application Entry Point

The main application that ties everything together:
- Loads NLP models at startup via lifespan
- Configures CORS for the Next.js frontend
- Registers all API routers
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.ml.pipeline import get_pipeline

# ── Configure Logging ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-25s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sentimentiq")


# ── Lifespan: Load models on startup ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models when the app starts, clean up on shutdown."""
    logger.info("=" * 60)
    logger.info(f"🧠 {settings.app_name} v{settings.app_version}")
    logger.info("=" * 60)
    logger.info("🔄 Loading NLP models (this may take a minute on first run)...")

    start = time.time()
    pipeline = get_pipeline()

    try:
        pipeline.load_models(
            sentiment_model=settings.sentiment_model,
            emotion_model=settings.emotion_model,
        )
        elapsed = time.time() - start
        logger.info(f"🚀 All models loaded in {elapsed:.1f}s")
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        logger.error("The API will start but /api/analyze will return 503")

    logger.info("=" * 60)
    logger.info(f"📡 API ready at http://localhost:8000")
    logger.info(f"📖 Docs at http://localhost:8000/docs")
    logger.info("=" * 60)

    yield  # App is running

    # Shutdown
    logger.info("👋 Shutting down SentimentIQ...")


from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# ── Create FastAPI Application ────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-grade Sentiment Analysis API powered by DistilBERT and GoEmotions. "
        "Provides real-time text analysis, batch processing, and e-commerce review scraping "
        "with per-sentence sentiment, emotion detection, and aspect-based analysis."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register API Routers ─────────────────────────────────────
from app.api.analyze import router as analyze_router
from app.api.batch import router as batch_router
from app.api.scrape import router as scrape_router
from app.api.history import router as history_router
from app.api.auth import router as auth_router
from app.api.stats import router as stats_router

app.include_router(analyze_router)
app.include_router(batch_router)
app.include_router(scrape_router)
app.include_router(history_router)
app.include_router(auth_router)
app.include_router(stats_router)


# ── Health Check ──────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Check if the API and ML models are running."""
    pipeline = get_pipeline()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "models_loaded": pipeline.is_loaded,
        "device": settings.model_device,
    }


@app.get("/", tags=["System"])
async def root():
    """API root — basic info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Sentiment Analysis API",
        "docs": "/docs",
        "health": "/health",
    }
