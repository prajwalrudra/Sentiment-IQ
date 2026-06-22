"""
SentimentIQ — Application Configuration

Loads all configuration from environment variables using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # ── Supabase ──────────────────────────────────────────────
    supabase_url: str = "https://your-project-id.supabase.co"
    supabase_anon_key: str = "your-anon-key-here"
    supabase_service_role_key: str = "your-service-role-key-here"

    # ── ML Models ─────────────────────────────────────────────
    model_device: str = "cpu"
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    emotion_model: str = "SamLowe/roberta-base-go_emotions"

    # ── Application ───────────────────────────────────────────
    app_name: str = "SentimentIQ"
    app_version: str = "1.0.0"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    debug: bool = True

    # ── Scraping ──────────────────────────────────────────────
    scrape_delay_min: float = 1.0
    scrape_delay_max: float = 3.0
    scrape_max_pages: int = 5

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings singleton
settings = Settings()
