# 🧠 SentimentIQ — Backend API

A production-grade **FastAPI** backend powering the SentimentIQ sentiment analysis platform. Built with DistilBERT and GoEmotions models, it delivers real-time text analysis, batch processing, emotion detection, aspect-based sentiment analysis, and e-commerce review scraping — all served over a clean REST API.

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app entry point, lifespan, CORS, routers
│   ├── api/
│   │   ├── analyze.py     # Single text analysis endpoint
│   │   ├── batch.py       # Batch text analysis endpoint
│   │   ├── scrape.py      # E-commerce review scraper endpoint
│   │   ├── history.py     # Analysis history (Supabase-backed)
│   │   ├── auth.py        # JWT authentication routes
│   │   └── deps.py        # Shared FastAPI dependencies
│   ├── ml/
│   │   ├── pipeline.py    # NLP pipeline (DistilBERT + GoEmotions)
│   │   └── schemas.py     # Pydantic request/response models
│   ├── core/
│   │   ├── config.py      # App settings (pydantic-settings)
│   │   └── supabase_client.py  # Supabase client singleton
│   └── scraper/
│       └── __init__.py    # Web scraping utilities (BS4 + fake-useragent)
├── supabase/              # Supabase migrations / SQL schemas
├── Dockerfile             # Multi-stage Docker build (CPU-optimised)
├── docker-compose.yml     # Local Docker Compose config
├── requirements.txt       # Python dependencies
├── .env                   # Local secrets (git-ignored)
└── .env.example           # Template for required env vars
```

---

## ⚡ Tech Stack

| Layer | Library / Tool |
|---|---|
| Web framework | FastAPI 0.115 + Uvicorn |
| ML / NLP | Transformers, ONNX Runtime, Optimum, spaCy |
| Sentiment model | `distilbert-base-uncased-finetuned-sst-2-english` |
| Emotion model | `SamLowe/roberta-base-go_emotions` |
| Database | Supabase (PostgreSQL) |
| Scraping | BeautifulSoup4, fake-useragent, lxml |
| Auth | python-jose (JWT) |
| Validation | Pydantic v2 |
| Containerisation | Docker (multi-stage, Python 3.11-slim) |

---

## 🚀 Getting Started

### Prerequisites

- Python **3.11+**
- `pip` or a virtual environment manager (e.g. `venv`)
- A [Supabase](https://supabase.com) project (for auth & history features)

### 1. Clone and Set Up the Environment

```bash
# From the project root
cd backend

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Download the spaCy English model
python -m spacy download en_core_web_sm
```

### 2. Configure Environment Variables

```bash
# Copy the example env file
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Then open `.env` and fill in your values:

```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# ML Models
MODEL_DEVICE=cpu
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
EMOTION_MODEL=SamLowe/roberta-base-go_emotions

# App
APP_NAME=SentimentIQ
APP_VERSION=1.0.0
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
DEBUG=true

# Scraping
SCRAPE_DELAY_MIN=1.0
SCRAPE_DELAY_MAX=3.0
SCRAPE_MAX_PAGES=5
```

### 3. Run the Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

| URL | Description |
|---|---|
| `http://localhost:8000` | API root |
| `http://localhost:8000/docs` | Swagger UI (interactive docs) |
| `http://localhost:8000/redoc` | ReDoc documentation |
| `http://localhost:8000/health` | Health check endpoint |

> **Note:** On first startup, Hugging Face will download the ML models (~300 MB). This only happens once; subsequent starts will load from cache.

---

## 🐳 Docker

### Build & Run with Docker

```bash
# Build the image
docker build -t sentimentiq-backend .

# Run the container
docker run -p 8000:8000 --env-file .env sentimentiq-backend
```

### Docker Compose (Recommended)

```bash
docker-compose up --build
```

> The Dockerfile uses a **multi-stage build** to keep the final image lean. The first stage installs all build dependencies and downloads the spaCy model; the second stage copies only the built artefacts.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API root info |
| `GET` | `/health` | Health check + model status |
| `POST` | `/api/analyze` | Analyse a single piece of text |
| `POST` | `/api/batch` | Batch analyse multiple texts |
| `POST` | `/api/scrape` | Scrape & analyse product reviews |
| `GET` | `/api/history` | Retrieve analysis history |
| `POST` | `/api/auth/...` | Authentication routes (JWT) |

Full interactive docs are available at `/docs` when the server is running.

---

## 🤖 ML Pipeline

The NLP pipeline (`app/ml/pipeline.py`) loads two models at startup:

1. **Sentiment Model** (`distilbert-base-uncased-finetuned-sst-2-english`)  
   Classifies text as **Positive**, **Negative**, or **Neutral** with a confidence score.

2. **Emotion Model** (`SamLowe/roberta-base-go_emotions`)  
   Detects 27 fine-grained emotions (joy, anger, sadness, surprise, etc.) from the GoEmotions dataset.

The pipeline also uses **spaCy** (`en_core_web_sm`) for sentence splitting and aspect-based analysis.

---

## 🔑 Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `SUPABASE_URL` | — | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | — | Supabase anonymous (public) key |
| `SUPABASE_SERVICE_ROLE_KEY` | — | Supabase service role key (server-side only) |
| `MODEL_DEVICE` | `cpu` | Inference device (`cpu` or `cuda`) |
| `SENTIMENT_MODEL` | `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace model ID |
| `EMOTION_MODEL` | `SamLowe/roberta-base-go_emotions` | HuggingFace model ID |
| `APP_NAME` | `SentimentIQ` | Application display name |
| `APP_VERSION` | `1.0.0` | Application version string |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `DEBUG` | `true` | Enable debug mode |
| `SCRAPE_DELAY_MIN` | `1.0` | Min delay (seconds) between scrape requests |
| `SCRAPE_DELAY_MAX` | `3.0` | Max delay (seconds) between scrape requests |
| `SCRAPE_MAX_PAGES` | `5` | Maximum pages to scrape per request |

---

## 🛠️ Development Tips

- **Auto-reload**: Use `--reload` flag with uvicorn during development — it watches for file changes.
- **Interactive docs**: FastAPI auto-generates Swagger UI at `/docs`. Use it to test endpoints directly in the browser without any external tool.
- **Model caching**: Hugging Face models are cached in `~/.cache/huggingface/`. Delete this folder to force a fresh download.
- **CORS**: If your frontend runs on a port other than `3000`, add it to `CORS_ORIGINS` in `.env`.

---

## 📦 Dependencies Overview

```
fastapi / uvicorn       → Web server & framework
transformers / torch    → Hugging Face ML models
onnxruntime / optimum   → ONNX-accelerated inference
spacy                   → NLP sentence splitting & aspect analysis
supabase                → Database client
beautifulsoup4 / lxml   → Web scraping
python-jose             → JWT authentication
pydantic-settings       → Typed environment config
```
