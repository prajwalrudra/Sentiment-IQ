"""
SentimentIQ — Batch Analysis Endpoint

POST /api/batch — Upload reviews (JSON body or CSV file) for batch processing.
GET  /api/batch/{job_id} — Check batch job status and results.
"""

import csv
import io
import uuid
import time
import logging
from typing import Dict
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from app.ml.schemas import (
    AnalyzeRequest,
    AnalysisResult,
    BatchRequest,
    BatchJobStatus,
    SentimentLabel,
    EmotionDistribution,
)
from app.ml.pipeline import NLPPipeline
from app.api.deps import get_nlp_pipeline, get_current_user
from app.core.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Batch"])

# ── In-memory job store (for BackgroundTasks) ────────────────
# In production, this would be in Redis or a database
_batch_jobs: Dict[str, BatchJobStatus] = {}


def _process_batch(job_id: str, texts: list, pipeline: NLPPipeline, user_id: str = None):
    """Background task to process a batch of reviews."""
    job = _batch_jobs[job_id]
    job.status = "processing"

    # Initialize in database if user is authenticated
    if user_id:
        try:
            supabase = get_supabase_admin()
            supabase.table("batch_jobs").insert({
                "id": job_id,
                "user_id": user_id,
                "total_reviews": len(texts),
                "processed_reviews": 0,
                "status": "processing",
                "results": {},
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to initialize batch job in DB: {e}")

    results = []
    try:
        for i, text in enumerate(texts):
            result = pipeline.analyze(text)
            results.append(result)
            job.processed_reviews = i + 1

            # Update progress in DB periodically (every 10 reviews)
            if user_id and (i + 1) % 10 == 0:
                try:
                    supabase = get_supabase_admin()
                    supabase.table("batch_jobs").update({
                        "processed_reviews": i + 1,
                    }).eq("id", job_id).execute()
                except Exception as e:
                    logger.warning(f"Failed to update progress in DB: {e}")

        # Compute aggregate stats
        sentiments = [r.overall_sentiment.value for r in results]
        job.aggregate = {
            "total": len(results),
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral"),
            "mixed": sentiments.count("mixed"),
            "avg_confidence": round(sum(r.overall_confidence for r in results) / len(results), 4),
        }
        job.results = results
        job.status = "completed"
        job.completed_at = datetime.utcnow()

        # Save complete results to Supabase
        if user_id:
            try:
                supabase = get_supabase_admin()
                supabase.table("batch_jobs").upsert({
                    "id": job_id,
                    "user_id": user_id,
                    "total_reviews": len(texts),
                    "processed_reviews": len(texts),
                    "status": "completed",
                    "results": {
                        "aggregate": job.aggregate,
                        "details": [r.model_dump() for r in results]
                    },
                    "completed_at": job.completed_at.isoformat()
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to save final batch job results: {e}")

        logger.info(f"✅ Batch job {job_id} completed: {len(results)} reviews")

    except Exception as e:
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        logger.error(f"❌ Batch job {job_id} failed: {e}")
        if user_id:
            try:
                supabase = get_supabase_admin()
                supabase.table("batch_jobs").upsert({
                    "id": job_id,
                    "user_id": user_id,
                    "status": "failed",
                    "completed_at": job.completed_at.isoformat()
                }).execute()
            except Exception as db_err:
                logger.warning(f"Failed to save failed batch job state: {db_err}")


@router.post("/batch", response_model=BatchJobStatus)
async def batch_analyze(
    request: BatchRequest,
    background_tasks: BackgroundTasks,
    pipeline: NLPPipeline = Depends(get_nlp_pipeline),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a batch of reviews for async analysis.
    Returns a job_id to poll for status.
    """
    job_id = str(uuid.uuid4())
    texts = [review.text for review in request.reviews]

    job = BatchJobStatus(
        job_id=job_id,
        status="pending",
        total_reviews=len(texts),
    )
    _batch_jobs[job_id] = job

    user_id = current_user["id"] if current_user else None
    background_tasks.add_task(_process_batch, job_id, texts, pipeline, user_id)

    logger.info(f"📦 Batch job {job_id} queued: {len(texts)} reviews")
    return job


@router.post("/batch/upload", response_model=BatchJobStatus)
async def batch_upload_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    pipeline: NLPPipeline = Depends(get_nlp_pipeline),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a CSV file with a 'review' or 'text' column for batch analysis.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    # Find the text column
    texts = []
    for row in reader:
        text = row.get("review") or row.get("text") or row.get("comment") or row.get("feedback")
        if text and text.strip():
            texts.append(text.strip())

    if not texts:
        raise HTTPException(
            status_code=400,
            detail="No text column found. CSV must have a 'review', 'text', 'comment', or 'feedback' column."
        )

    if len(texts) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 reviews per batch upload")

    job_id = str(uuid.uuid4())
    job = BatchJobStatus(
        job_id=job_id,
        status="pending",
        total_reviews=len(texts),
    )
    _batch_jobs[job_id] = job

    user_id = current_user["id"] if current_user else None
    background_tasks.add_task(_process_batch, job_id, texts, pipeline, user_id)

    logger.info(f"📦 CSV batch job {job_id} queued: {len(texts)} reviews from {file.filename}")
    return job


@router.get("/batch/{job_id}", response_model=BatchJobStatus)
async def get_batch_status(job_id: str):
    """Check the status of a batch processing job."""
    job = _batch_jobs.get(job_id)
    if not job:
        # Fallback to Supabase
        try:
            supabase = get_supabase_admin()
            response = supabase.table("batch_jobs").select("*").eq("id", job_id).execute()
            if response.data:
                db_job = response.data[0]
                db_results = db_job.get("results") or {}
                
                # Handle formats
                if isinstance(db_results, dict) and "aggregate" in db_results:
                    aggregate = db_results.get("aggregate")
                    details = db_results.get("details")
                else:
                    aggregate = db_results
                    details = None
                
                job = BatchJobStatus(
                    job_id=db_job["id"],
                    status=db_job["status"],
                    total_reviews=db_job["total_reviews"],
                    processed_reviews=db_job["processed_reviews"],
                    aggregate=aggregate,
                    results=details,
                    created_at=db_job.get("created_at") or datetime.utcnow(),
                    completed_at=db_job.get("completed_at"),
                )
            else:
                raise HTTPException(status_code=404, detail="Batch job not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching batch job {job_id} from database: {e}")
            raise HTTPException(status_code=404, detail="Batch job not found")
            
    return job


@router.get("/batch/{job_id}/export")
async def export_batch_csv(job_id: str):
    """
    Export the results of a batch job as a CSV file download.
    """
    job = _batch_jobs.get(job_id)
    details = None
    
    if job and job.status == "completed":
        details = job.results
    else:
        # Check database
        try:
            supabase = get_supabase_admin()
            response = supabase.table("batch_jobs").select("*").eq("id", job_id).execute()
            if response.data:
                db_job = response.data[0]
                db_results = db_job.get("results") or {}
                if isinstance(db_results, dict) and "details" in db_results:
                    details = db_results.get("details")
        except Exception as e:
            logger.error(f"Error fetching batch job {job_id} for export: {e}")
            
    if not details:
        raise HTTPException(
            status_code=404, 
            detail="Batch job results not found, or job is not yet completed"
        )
        
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Text",
        "Overall Sentiment",
        "Overall Confidence",
        "Top Emotion",
        "Top Emotion Score",
        "Word Count",
        "Sentence Count"
    ])
    
    for r in details:
        if hasattr(r, "model_dump"):
            r_dict = r.model_dump()
        elif hasattr(r, "dict"):
            r_dict = r.dict()
        else:
            r_dict = r
            
        # Extract top emotion
        emotions = r_dict.get("emotion_distribution") or {}
        top_emotion = "neutral"
        top_score = 0.0
        if emotions:
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
            if sorted_emotions:
                top_emotion, top_score = sorted_emotions[0]
                
        writer.writerow([
            r_dict.get("input_text"),
            r_dict.get("overall_sentiment"),
            round(r_dict.get("overall_confidence", 0.0), 4),
            top_emotion,
            round(top_score, 4),
            r_dict.get("word_count"),
            r_dict.get("sentence_count")
        ])
        
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    filename = f"sentimentiq_batch_{job_id[:8]}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

