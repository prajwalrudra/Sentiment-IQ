"""
SentimentIQ — Backend API Tests

Smoke tests for the main API routes using pytest + httpx AsyncClient.
Covers: health check, analyze endpoint, batch job flow, auth routes.

Run from the backend directory:
    pytest app/tests/test_api.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

# ── Import the app & dependencies ────────────────────────────────
from app.main import app
from app.api.deps import get_nlp_pipeline


# ── Fixtures ───────────────────────────────────────────────────
@pytest.fixture
def mock_pipeline():
    """Mock the NLP pipeline so tests don't require GPU/models."""
    from app.ml.schemas import (
        AnalysisResult, SentimentLabel, EmotionDistribution, SentenceResult
    )
    mock = MagicMock()
    mock.is_loaded = True
    mock.analyze.return_value = AnalysisResult(
        input_text="Great product!",
        overall_sentiment=SentimentLabel.POSITIVE,
        overall_confidence=0.92,
        sentences=[
            SentenceResult(
                text="Great product!",
                sentiment=SentimentLabel.POSITIVE,
                confidence=0.92,
                emotions={"joy": 0.8},
            )
        ],
        emotion_distribution=EmotionDistribution(joy=0.8, optimism=0.1),
        aspect_sentiments=[],
        entity_mentions=[],
        word_count=2,
        sentence_count=1,
        positive_ratio=1.0,
        negative_ratio=0.0,
        neutral_ratio=0.0,
        processing_time_ms=42.0,
    )
    return mock


@pytest.fixture
async def client(mock_pipeline):
    """Async test client with mocked pipeline."""
    app.dependency_overrides[get_nlp_pipeline] = lambda: mock_pipeline
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Health Check ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health_check(client):
    """GET /health should return 200 with status healthy."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# ── Root ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_root(client):
    """GET / should return API metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


# ── Analyze Endpoint ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_analyze_text(client):
    """POST /api/analyze should return a valid AnalysisResult."""
    response = await client.post(
        "/api/analyze",
        json={"text": "This product is absolutely amazing! I love it.", "include_emotions": True, "include_aspects": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert "overall_sentiment" in data
    assert "overall_confidence" in data
    assert data["overall_sentiment"] in ["positive", "negative", "neutral", "mixed"]
    assert 0.0 <= data["overall_confidence"] <= 1.0
    assert "sentences" in data
    assert "emotion_distribution" in data


@pytest.mark.asyncio
async def test_analyze_too_short(client):
    """POST /api/analyze with very short text should return 422."""
    response = await client.post(
        "/api/analyze",
        json={"text": "a"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_missing_text(client):
    """POST /api/analyze with no body should return 422."""
    response = await client.post("/api/analyze", json={})
    assert response.status_code == 422


# ── Batch Job Flow ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_batch_submit_and_poll(client):
    """POST /api/batch should create a job; GET /api/batch/{id} should return it."""
    # Submit batch
    response = await client.post(
        "/api/batch",
        json={
            "reviews": [
                {"text": "Great product, works perfectly!"},
                {"text": "Terrible experience, would not recommend."},
            ]
        }
    )
    assert response.status_code == 200
    job = response.json()
    assert "job_id" in job
    assert job["status"] in ["pending", "processing", "completed"]
    assert job["total_reviews"] == 2

    job_id = job["job_id"]

    # Poll job status
    poll_response = await client.get(f"/api/batch/{job_id}")
    assert poll_response.status_code == 200
    poll_data = poll_response.json()
    assert poll_data["job_id"] == job_id
    assert "status" in poll_data


@pytest.mark.asyncio
async def test_batch_job_not_found(client):
    """GET /api/batch/{non-existent-id} should return 404."""
    response = await client.get("/api/batch/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# ── Auth Routes ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_auth_signup_missing_body(client):
    """POST /api/auth/signup with no body should return 422."""
    response = await client.post("/api/auth/signup", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auth_login_bad_credentials(client):
    """POST /api/auth/login with fake credentials should return 400 or 401."""
    with patch("app.api.auth.get_supabase_client") as mock_sb:
        mock_sb.return_value.auth.sign_in_with_password.side_effect = Exception("Invalid login")
        response = await client.post(
            "/api/auth/login",
            json={"email": "fake@example.com", "password": "wrongpassword"}
        )
        assert response.status_code in [400, 401, 422]


@pytest.mark.asyncio
async def test_auth_me_unauthorized(client):
    """GET /api/auth/me without token should return 401 or 403."""
    response = await client.get("/api/auth/me")
    assert response.status_code in [401, 403]


# ── Scraper Presets ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_scrape_presets(client):
    """GET /api/scrape/presets should return a list of preset products."""
    response = await client.get("/api/scrape/presets")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert isinstance(data["presets"], list)
    assert len(data["presets"]) > 0


# ── Rate Limiting ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rate_limiting(client):
    """POST /api/analyze should return 429 when rate limit is exceeded."""
    # Send 25 rapid requests (limit is 20/minute)
    responses = []
    for _ in range(25):
        resp = await client.post(
            "/api/analyze",
            json={"text": "Test rate limit", "include_emotions": False, "include_aspects": False}
        )
        responses.append(resp.status_code)
    
    assert 429 in responses


# ── CSV Export ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_batch_export_csv(client):
    """GET /api/batch/{id}/export should return a CSV file."""
    # First create a job
    response = await client.post(
        "/api/batch",
        json={"reviews": [{"text": "Great product!"}]}
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Export it
    export_resp = await client.get(f"/api/batch/{job_id}/export")
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]
    assert "attachment; filename=" in export_resp.headers["content-disposition"]
