"""
SentimentIQ — ML Response Schemas

Pydantic models for all NLP pipeline responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class SentimentLabel(str, Enum):
    """Possible sentiment labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class AspectSentiment(BaseModel):
    """Sentiment for a specific product/topic aspect."""
    aspect: str = Field(..., description="The aspect/feature mentioned (e.g., 'battery life', 'screen')")
    sentiment: SentimentLabel
    confidence: float = Field(..., ge=0, le=1)
    mention_count: int = 1


class SentenceResult(BaseModel):
    """Analysis result for a single sentence."""
    text: str
    sentiment: SentimentLabel
    confidence: float = Field(..., ge=0, le=1)
    emotions: Dict[str, float] = Field(default_factory=dict, description="Emotion name → score")
    aspects: List[AspectSentiment] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list, description="Named entities found")


class EmotionDistribution(BaseModel):
    """Emotion scores across the entire text."""
    joy: float = 0.0
    anger: float = 0.0
    sadness: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0
    love: float = 0.0
    optimism: float = 0.0
    pessimism: float = 0.0


class AnalysisResult(BaseModel):
    """Complete analysis result for a piece of text."""
    input_text: str
    overall_sentiment: SentimentLabel
    overall_confidence: float = Field(..., ge=0, le=1)
    sentences: List[SentenceResult]
    emotion_distribution: EmotionDistribution
    aspect_sentiments: List[AspectSentiment] = Field(default_factory=list)
    entity_mentions: List[str] = Field(default_factory=list)
    word_count: int
    sentence_count: int
    positive_ratio: float = Field(..., ge=0, le=1)
    negative_ratio: float = Field(..., ge=0, le=1)
    neutral_ratio: float = Field(..., ge=0, le=1)
    processing_time_ms: float = 0.0


class AnalyzeRequest(BaseModel):
    """Request body for the /api/analyze endpoint."""
    text: str = Field(..., min_length=3, max_length=50000, description="Text to analyze")
    include_emotions: bool = True
    include_aspects: bool = True


class BatchReview(BaseModel):
    """A single review in a batch upload."""
    text: str
    rating: Optional[float] = None
    source: Optional[str] = None


class BatchRequest(BaseModel):
    """Request for batch analysis."""
    reviews: List[BatchReview] = Field(..., min_length=1, max_length=1000)


class BatchJobStatus(BaseModel):
    """Status of a batch processing job."""
    job_id: str
    status: str = "pending"  # pending, processing, completed, failed
    total_reviews: int = 0
    processed_reviews: int = 0
    results: Optional[List[AnalysisResult]] = None
    aggregate: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ScrapedReview(BaseModel):
    """A single review scraped from an e-commerce site."""
    text: str
    rating: Optional[float] = None
    reviewer_name: Optional[str] = None
    date: Optional[str] = None
    verified_purchase: bool = False
    helpful_count: int = 0


class ScrapeRequest(BaseModel):
    """Request body for the /api/scrape endpoint."""
    url: str = Field(..., description="Product URL to scrape reviews from")
    max_pages: int = Field(default=3, ge=1, le=10)
    use_mock: bool = Field(default=False, description="Force mock data instead of real scraping")


class ScrapeResult(BaseModel):
    """Result from scraping and analyzing product reviews."""
    product_name: str
    product_url: str
    source: str  # amazon, flipkart, mock
    total_reviews: int
    average_rating: Optional[float] = None
    rating_distribution: Dict[str, int] = Field(default_factory=dict)
    overall_sentiment: SentimentLabel
    sentiment_distribution: Dict[str, float] = Field(default_factory=dict)
    emotion_distribution: EmotionDistribution = Field(default_factory=EmotionDistribution)
    top_aspects: List[AspectSentiment] = Field(default_factory=list)
    reviews: List[Dict] = Field(default_factory=list, description="Reviews with analysis")
    key_strengths: List[str] = Field(default_factory=list)
    key_weaknesses: List[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class HistoryItem(BaseModel):
    """A saved analysis from history."""
    id: str
    input_text: str
    overall_sentiment: SentimentLabel
    overall_confidence: float
    source: str = "manual"
    created_at: datetime
