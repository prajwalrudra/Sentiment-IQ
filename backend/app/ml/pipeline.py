"""
SentimentIQ — NLP Pipeline Engine

The core ML orchestrator that loads and manages all NLP models:
- DistilBERT for sentiment classification (ONNX optimized)
- GoEmotions RoBERTa for multi-label emotion detection
- spaCy for sentence segmentation, NER, and aspect extraction

All models run on CPU with ONNX Runtime for maximum performance on
resource-constrained hardware (i3 / 8GB RAM).
"""

import time
import logging
import re
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict

import numpy as np
import spacy
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline as hf_pipeline,
)

from app.ml.schemas import (
    SentimentLabel,
    SentenceResult,
    AspectSentiment,
    AnalysisResult,
    EmotionDistribution,
)

logger = logging.getLogger(__name__)


# ── Aspect keyword categories ────────────────────────────────
# Used for lightweight rule-based aspect extraction
ASPECT_KEYWORDS = {
    "battery": ["battery", "charge", "charging", "power", "mah"],
    "screen": ["screen", "display", "resolution", "brightness", "amoled", "lcd", "oled"],
    "camera": ["camera", "photo", "picture", "lens", "selfie", "zoom", "video recording"],
    "performance": ["speed", "fast", "slow", "lag", "performance", "processor", "ram", "smooth"],
    "design": ["design", "look", "build", "premium", "plastic", "metal", "weight", "thin", "sleek"],
    "price": ["price", "cost", "value", "expensive", "cheap", "affordable", "worth", "money"],
    "sound": ["sound", "audio", "speaker", "bass", "volume", "noise cancelling", "microphone"],
    "comfort": ["comfort", "comfortable", "fit", "ergonomic", "soft", "padding"],
    "durability": ["durability", "durable", "sturdy", "break", "broken", "fragile", "quality"],
    "software": ["software", "app", "update", "ui", "interface", "os", "feature", "bug"],
    "delivery": ["delivery", "shipping", "packaging", "arrived", "dispatch"],
    "customer service": ["support", "service", "warranty", "return", "refund", "customer care"],
    "size": ["size", "big", "small", "compact", "large", "portable", "heavy", "lightweight"],
    "connectivity": ["wifi", "bluetooth", "nfc", "usb", "connection", "signal", "network"],
    "taste": ["taste", "flavor", "delicious", "bland", "spicy", "fresh", "stale"],
    "material": ["material", "fabric", "leather", "cotton", "synthetic", "texture"],
}

# ── Key emotion groups for the GoEmotions model ──────────────
EMOTION_GROUP_MAP = {
    "joy": ["joy", "amusement", "excitement"],
    "love": ["love", "caring", "gratitude", "admiration"],
    "optimism": ["optimism", "desire", "approval", "pride"],
    "anger": ["anger", "annoyance", "disapproval"],
    "sadness": ["sadness", "grief", "remorse", "disappointment"],
    "fear": ["fear", "nervousness"],
    "surprise": ["surprise", "realization", "curiosity", "confusion"],
    "disgust": ["disgust"],
    "pessimism": ["embarrassment"],
}


class NLPPipeline:
    """
    Main NLP pipeline that orchestrates all models.

    Usage:
        pipeline = NLPPipeline()
        pipeline.load_models()
        result = pipeline.analyze("This product is amazing but overpriced.")
    """

    def __init__(self):
        self._sentiment_pipeline = None
        self._emotion_pipeline = None
        self._nlp = None  # spaCy
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_models(self, sentiment_model: str = None, emotion_model: str = None):
        """
        Load all NLP models into memory. Called once at application startup.

        Args:
            sentiment_model: HuggingFace model ID for sentiment classification
            emotion_model: HuggingFace model ID for emotion detection
        """
        from app.core.config import settings

        sentiment_model = sentiment_model or settings.sentiment_model
        emotion_model = emotion_model or settings.emotion_model

        logger.info("🔄 Loading NLP models...")
        start = time.time()

        # ── 1. Load spaCy for tokenization, NER, sentence splitting ──
        try:
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("  ✅ spaCy en_core_web_sm loaded")
        except OSError:
            logger.warning("  ⚠️ spaCy model not found. Downloading en_core_web_sm...")
            spacy.cli.download("en_core_web_sm")
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("  ✅ spaCy en_core_web_sm downloaded and loaded")

        # ── 2. Load Sentiment model ──────────────────────────────────
        try:
            # Try ONNX optimized first
            from optimum.onnxruntime import ORTModelForSequenceClassification

            ort_model = ORTModelForSequenceClassification.from_pretrained(
                sentiment_model, export=True
            )
            tokenizer = AutoTokenizer.from_pretrained(sentiment_model)
            self._sentiment_pipeline = hf_pipeline(
                "sentiment-analysis",
                model=ort_model,
                tokenizer=tokenizer,
                device=-1,  # CPU
            )
            logger.info(f"  ✅ Sentiment model loaded (ONNX): {sentiment_model}")
        except Exception as e:
            logger.warning(f"  ⚠️ ONNX failed ({e}), falling back to PyTorch")
            self._sentiment_pipeline = hf_pipeline(
                "sentiment-analysis",
                model=sentiment_model,
                device=-1,
            )
            logger.info(f"  ✅ Sentiment model loaded (PyTorch): {sentiment_model}")

        # ── 3. Load Emotion model ────────────────────────────────────
        try:
            from optimum.onnxruntime import ORTModelForSequenceClassification

            ort_model = ORTModelForSequenceClassification.from_pretrained(
                emotion_model, export=True
            )
            tokenizer = AutoTokenizer.from_pretrained(emotion_model)
            self._emotion_pipeline = hf_pipeline(
                "text-classification",
                model=ort_model,
                tokenizer=tokenizer,
                top_k=None,  # Return all emotion scores
                device=-1,
            )
            logger.info(f"  ✅ Emotion model loaded (ONNX): {emotion_model}")
        except Exception as e:
            logger.warning(f"  ⚠️ Emotion ONNX failed ({e}), falling back to PyTorch")
            self._emotion_pipeline = hf_pipeline(
                "text-classification",
                model=emotion_model,
                top_k=None,
                device=-1,
            )
            logger.info(f"  ✅ Emotion model loaded (PyTorch): {emotion_model}")

        elapsed = time.time() - start
        self._is_loaded = True
        logger.info(f"🚀 All NLP models loaded in {elapsed:.1f}s")

    def analyze(self, text: str, include_emotions: bool = True, include_aspects: bool = True) -> AnalysisResult:
        """
        Run full NLP analysis on the given text.

        Args:
            text: Raw text to analyze
            include_emotions: Whether to run emotion detection
            include_aspects: Whether to extract aspect-based sentiment

        Returns:
            AnalysisResult with per-sentence breakdown, emotions, and aspects
        """
        if not self._is_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")

        start_time = time.time()

        # ── Step 1: Sentence segmentation + NER via spaCy ────────────
        doc = self._nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        entities = list(set(ent.text for ent in doc.ents))

        if not sentences:
            sentences = [text]

        # ── Step 2: Per-sentence sentiment analysis ──────────────────
        sentence_results: List[SentenceResult] = []
        all_aspects: Dict[str, List[float]] = defaultdict(list)

        for sent_text in sentences:
            # Sentiment
            sent_sentiment = self._classify_sentiment(sent_text)

            # Emotions
            sent_emotions = {}
            if include_emotions:
                sent_emotions = self._detect_emotions(sent_text)

            # Aspects
            sent_aspects = []
            if include_aspects:
                sent_aspects = self._extract_aspects(sent_text, sent_sentiment)
                for asp in sent_aspects:
                    conf = asp.confidence if asp.sentiment == SentimentLabel.POSITIVE else -asp.confidence
                    all_aspects[asp.aspect].append(conf)

            # Named entities in this sentence
            sent_doc = self._nlp(sent_text)
            sent_entities = [ent.text for ent in sent_doc.ents]

            sentence_results.append(SentenceResult(
                text=sent_text,
                sentiment=sent_sentiment[0],
                confidence=sent_sentiment[1],
                emotions=sent_emotions,
                aspects=sent_aspects,
                entities=sent_entities,
            ))

        # ── Step 3: Aggregate results ────────────────────────────────
        positive_count = sum(1 for s in sentence_results if s.sentiment == SentimentLabel.POSITIVE)
        negative_count = sum(1 for s in sentence_results if s.sentiment == SentimentLabel.NEGATIVE)
        neutral_count = sum(1 for s in sentence_results if s.sentiment == SentimentLabel.NEUTRAL)
        total = len(sentence_results)

        positive_ratio = positive_count / total
        negative_ratio = negative_count / total
        neutral_ratio = neutral_count / total

        # Overall sentiment
        overall_sentiment, overall_confidence = self._compute_overall_sentiment(sentence_results)

        # Aggregate emotions
        emotion_dist = self._aggregate_emotions(sentence_results) if include_emotions else EmotionDistribution()

        # Aggregate aspects
        aggregated_aspects = self._aggregate_aspects(all_aspects) if include_aspects else []

        processing_time = (time.time() - start_time) * 1000  # ms

        return AnalysisResult(
            input_text=text,
            overall_sentiment=overall_sentiment,
            overall_confidence=overall_confidence,
            sentences=sentence_results,
            emotion_distribution=emotion_dist,
            aspect_sentiments=aggregated_aspects,
            entity_mentions=entities,
            word_count=len(text.split()),
            sentence_count=total,
            positive_ratio=positive_ratio,
            negative_ratio=negative_ratio,
            neutral_ratio=neutral_ratio,
            processing_time_ms=round(processing_time, 2),
        )

    def analyze_batch(self, texts: List[str]) -> List[AnalysisResult]:
        """Analyze multiple texts and return a list of results."""
        return [self.analyze(text) for text in texts]

    # ── Private Methods ──────────────────────────────────────────────

    def _classify_sentiment(self, text: str) -> Tuple[SentimentLabel, float]:
        """Classify sentiment of a single text using DistilBERT."""
        try:
            result = self._sentiment_pipeline(text, truncation=True, max_length=512)
            if result:
                label = result[0]["label"].lower()
                score = result[0]["score"]

                # DistilBERT SST-2 outputs POSITIVE/NEGATIVE
                if label == "positive":
                    if score < 0.6:
                        return SentimentLabel.NEUTRAL, score
                    return SentimentLabel.POSITIVE, score
                elif label == "negative":
                    if score < 0.6:
                        return SentimentLabel.NEUTRAL, score
                    return SentimentLabel.NEGATIVE, score

            return SentimentLabel.NEUTRAL, 0.5
        except Exception as e:
            logger.error(f"Sentiment classification error: {e}")
            return SentimentLabel.NEUTRAL, 0.5

    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect emotions using GoEmotions model."""
        try:
            results = self._emotion_pipeline(text, truncation=True, max_length=512)
            if results:
                # results is a list of dicts [{label, score}, ...]
                emotion_scores = {}
                for item in results[0] if isinstance(results[0], list) else results:
                    emotion_scores[item["label"]] = round(item["score"], 4)

                # Group into main emotion categories
                grouped = {}
                for group_name, labels in EMOTION_GROUP_MAP.items():
                    scores = [emotion_scores.get(label, 0.0) for label in labels]
                    grouped[group_name] = round(max(scores) if scores else 0.0, 4)

                return grouped
            return {}
        except Exception as e:
            logger.error(f"Emotion detection error: {e}")
            return {}

    def _extract_aspects(
        self, text: str, sentiment: Tuple[SentimentLabel, float]
    ) -> List[AspectSentiment]:
        """
        Extract product/topic aspects from text using keyword matching
        combined with spaCy noun chunk extraction.
        """
        aspects = []
        text_lower = text.lower()

        # ── Method 1: Keyword-based aspect matching ──────────────────
        for aspect_name, keywords in ASPECT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    aspects.append(AspectSentiment(
                        aspect=aspect_name,
                        sentiment=sentiment[0],
                        confidence=sentiment[1],
                    ))
                    break  # Only add each aspect once

        # ── Method 2: spaCy noun chunk extraction ────────────────────
        doc = self._nlp(text)
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower().strip()
            # Skip very short or very long chunks, and pronouns
            if len(chunk_text) < 3 or len(chunk_text) > 40:
                continue
            if chunk.root.pos_ in ("PRON", "DET"):
                continue

            # Check if this chunk overlaps with any keyword aspect
            already_captured = any(
                keyword in chunk_text
                for keywords in ASPECT_KEYWORDS.values()
                for keyword in keywords
            )
            if not already_captured:
                aspects.append(AspectSentiment(
                    aspect=chunk_text,
                    sentiment=sentiment[0],
                    confidence=sentiment[1],
                ))

        return aspects

    def _compute_overall_sentiment(
        self, sentences: List[SentenceResult]
    ) -> Tuple[SentimentLabel, float]:
        """Compute overall sentiment by weighted averaging sentence sentiments."""
        if not sentences:
            return SentimentLabel.NEUTRAL, 0.5

        positive_score = 0.0
        negative_score = 0.0
        total_weight = 0.0

        for sent in sentences:
            # Weight longer sentences more
            weight = max(len(sent.text.split()), 1)
            total_weight += weight

            if sent.sentiment == SentimentLabel.POSITIVE:
                positive_score += sent.confidence * weight
            elif sent.sentiment == SentimentLabel.NEGATIVE:
                negative_score += sent.confidence * weight

        if total_weight == 0:
            return SentimentLabel.NEUTRAL, 0.5

        pos_avg = positive_score / total_weight
        neg_avg = negative_score / total_weight

        if pos_avg > neg_avg:
            if neg_avg > 0.2:
                return SentimentLabel.MIXED, round(pos_avg, 4)
            return SentimentLabel.POSITIVE, round(pos_avg, 4)
        elif neg_avg > pos_avg:
            if pos_avg > 0.2:
                return SentimentLabel.MIXED, round(neg_avg, 4)
            return SentimentLabel.NEGATIVE, round(neg_avg, 4)
        else:
            return SentimentLabel.NEUTRAL, 0.5

    def _aggregate_emotions(self, sentences: List[SentenceResult]) -> EmotionDistribution:
        """Average emotions across all sentences."""
        if not sentences:
            return EmotionDistribution()

        emotion_sums = defaultdict(float)
        count = 0

        for sent in sentences:
            if sent.emotions:
                count += 1
                for emotion, score in sent.emotions.items():
                    emotion_sums[emotion] += score

        if count == 0:
            return EmotionDistribution()

        return EmotionDistribution(
            joy=round(emotion_sums.get("joy", 0) / count, 4),
            anger=round(emotion_sums.get("anger", 0) / count, 4),
            sadness=round(emotion_sums.get("sadness", 0) / count, 4),
            fear=round(emotion_sums.get("fear", 0) / count, 4),
            surprise=round(emotion_sums.get("surprise", 0) / count, 4),
            disgust=round(emotion_sums.get("disgust", 0) / count, 4),
            love=round(emotion_sums.get("love", 0) / count, 4),
            optimism=round(emotion_sums.get("optimism", 0) / count, 4),
            pessimism=round(emotion_sums.get("pessimism", 0) / count, 4),
        )

    def _aggregate_aspects(self, aspect_scores: Dict[str, List[float]]) -> List[AspectSentiment]:
        """Aggregate aspect sentiment scores across sentences."""
        aggregated = []
        for aspect, scores in aspect_scores.items():
            avg_score = np.mean(scores)
            if avg_score > 0.1:
                sentiment = SentimentLabel.POSITIVE
            elif avg_score < -0.1:
                sentiment = SentimentLabel.NEGATIVE
            else:
                sentiment = SentimentLabel.NEUTRAL

            aggregated.append(AspectSentiment(
                aspect=aspect,
                sentiment=sentiment,
                confidence=round(abs(float(avg_score)), 4),
                mention_count=len(scores),
            ))

        # Sort by mention count descending
        aggregated.sort(key=lambda x: x.mention_count, reverse=True)
        return aggregated[:15]  # Top 15 aspects


# ── Singleton ────────────────────────────────────────────────────

_pipeline_instance: Optional[NLPPipeline] = None


def get_pipeline() -> NLPPipeline:
    """Get the singleton NLP pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = NLPPipeline()
    return _pipeline_instance
