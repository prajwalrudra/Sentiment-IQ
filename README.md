# SentimentIQ

**Production-grade ML-powered sentiment analysis platform** built with FastAPI, Next.js, DistilBERT, and GoEmotions.

---

## ✨ Features

- **Real-time Sentiment Analysis** — Classify text as positive / negative / neutral / mixed with confidence scores
- **Emotion Detection** — 27 emotion categories via GoEmotions (joy, anger, sadness, fear, surprise, etc.)
- **Aspect-Based Analysis** — Identify product aspects and their individual sentiments
- **Sentence-Level Breakdown** — Per-sentence sentiment highlighting
- **E-Commerce Scraper** — Scrape and analyze product reviews from any URL with fallback to realistic mock data
- **Batch Processing** — Upload CSV files with thousands of reviews for async analysis; download results as CSV
- **Analysis History** — Browse, filter, and search your past analyses
- **Dashboard Stats** — Live sentiment breakdown donut chart, 30-day activity sparkline, and key metrics
- **Toast Notifications** — Real-time success/error/info alerts throughout the app
- **Rate Limiting** — API protected against abuse with per-IP rate limits
- **Auth** — User registration and JWT-based login (via Supabase)

---

## 🏗️ Architecture

```
SentimentIQ/
├── backend/                  # FastAPI + ML pipeline
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   │   ├── analyze.py    # POST /api/analyze
│   │   │   ├── batch.py      # POST /api/batch, GET /api/batch/{id}, GET /api/batch/{id}/export
│   │   │   ├── scrape.py     # POST /api/scrape, GET /api/scrape/presets
│   │   │   ├── history.py    # GET /api/history
│   │   │   ├── stats.py      # GET /api/stats
│   │   │   └── auth.py       # POST /api/auth/signup, /login, GET /api/auth/me
│   │   ├── core/
│   │   │   ├── config.py     # Settings from .env
│   │   │   ├── supabase_client.py
│   │   │   └── limiter.py    # slowapi rate limiter
│   │   ├── ml/
│   │   │   ├── pipeline.py   # DistilBERT + GoEmotions + spaCy
│   │   │   └── schemas.py    # Pydantic models
│   │   ├── scraper/
│   │   │   ├── engine.py     # BeautifulSoup + httpx scraper
│   │   │   └── mock.py       # Realistic mock review generator
│   │   └── main.py           # FastAPI app entry point
│   ├── supabase/migrations/  # Database schema (SQL)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example
│
└── frontend/                 # Next.js 16 (Turbopack)
    └── src/app/
        ├── DashboardPage.js  # Real-time stats, donut chart, sparkline, quick analyze
        ├── AnalyzerPage.js   # Single text analyzer with emotion bars
        ├── BatchPage.js      # CSV upload, live polling, result browser + export
        ├── ScraperPage.js    # URL scraper with donut and rating charts
        ├── HistoryPage.js    # Paginated analysis history with filters
        ├── LoginPage.js      # Signup / login
        ├── Sidebar.js        # Navigation
        ├── ToastContext.js   # Global toast notification system
        ├── globals.css       # Design system (dark theme, glassmorphism)
        └── page.js           # SPA router
```

---

## 🚀 Quickstart

### Prerequisites

- Python 3.12+, `uv` or `pip`
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)

---

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
uv venv
# or: python -m venv .venv

# Install dependencies
uv pip install -r requirements.txt
# or: .venv\Scripts\pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
```

Edit `backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SECRET_KEY=any-random-secret-string
```

Run the database migration in **Supabase SQL Editor**:

```sql
-- Paste contents of: backend/supabase/migrations/001_initial_schema.sql
```

Start the backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API docs available at: **http://localhost:8001/docs**

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set the backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Start the dev server
npm run dev
```

Open: **http://localhost:3000**

---

### 3. Docker (Optional)

```bash
cd backend
docker-compose up --build
```

---

## 📡 API Reference

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `GET` | `/health` | Health check + model status | — |
| `POST` | `/api/analyze` | Analyze a single text | 20/min |
| `POST` | `/api/batch` | Submit JSON reviews for async analysis | — |
| `POST` | `/api/batch/upload` | Upload a CSV file for batch analysis | — |
| `GET` | `/api/batch/{id}` | Poll batch job status | — |
| `GET` | `/api/batch/{id}/export` | Download batch results as CSV | — |
| `POST` | `/api/scrape` | Scrape and analyze a product URL | 5/min |
| `GET` | `/api/scrape/presets` | List demo preset products | — |
| `GET` | `/api/history` | Paginated analysis history | — |
| `GET` | `/api/stats` | Dashboard stats (auth required) | — |
| `POST` | `/api/auth/signup` | Register a new user | — |
| `POST` | `/api/auth/login` | Login and get JWT | — |
| `GET` | `/api/auth/me` | Current user info | — |

---

## 🧠 ML Models

| Model | Purpose |
|-------|---------|
| `distilbert-base-uncased-finetuned-sst-2-english` | Sentiment classification (positive / negative) |
| `SamLowe/roberta-base-go_emotions` | Emotion detection (27 categories) |
| `en_core_web_sm` (spaCy) | Sentence splitting + aspect/entity extraction |

Models are loaded once at startup and cached in memory. First boot may take 1–2 minutes to download models.

---

## 🔒 Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon (public) key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (bypasses RLS) |
| `SECRET_KEY` | JWT signing secret (any random string) |
| `CORS_ORIGINS` | Comma-separated frontend origins (default: `http://localhost:3000`) |
| `MODEL_DEVICE` | `cpu` or `cuda` (default: `cpu`) |

---

## 📊 Tech Stack

**Backend:** FastAPI · Uvicorn · Pydantic · Supabase · slowapi · Transformers · spaCy · ONNX Runtime · BeautifulSoup · httpx

**Frontend:** Next.js 16 · React · Vanilla CSS (glassmorphism design system) · Inter font

**ML:** DistilBERT · GoEmotions (RoBERTa) · spaCy `en_core_web_sm`

**Infrastructure:** Docker · Supabase (PostgreSQL + Auth + RLS)
