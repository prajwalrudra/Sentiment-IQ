-- ================================================================
-- SentimentIQ — Supabase Database Schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor)
-- ================================================================

-- ── 1. Analyses Table ───────────────────────────────────────────
-- Stores individual text analysis results
CREATE TABLE IF NOT EXISTS analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    input_text TEXT NOT NULL,
    overall_sentiment TEXT NOT NULL CHECK (overall_sentiment IN ('positive', 'negative', 'neutral', 'mixed')),
    overall_confidence FLOAT NOT NULL CHECK (overall_confidence >= 0 AND overall_confidence <= 1),
    emotion_distribution JSONB DEFAULT '{}',
    aspect_sentiments JSONB DEFAULT '[]',
    sentences JSONB DEFAULT '[]',
    source TEXT DEFAULT 'manual' CHECK (source IN ('manual', 'batch', 'scrape')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast user history queries
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_sentiment ON analyses(overall_sentiment);


-- ── 2. Batch Jobs Table ─────────────────────────────────────────
-- Tracks batch processing jobs
CREATE TABLE IF NOT EXISTS batch_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name TEXT,
    total_reviews INT NOT NULL DEFAULT 0,
    processed_reviews INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    results JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_batch_jobs_user_id ON batch_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status);


-- ── 3. Scraped Products Table ───────────────────────────────────
-- Stores scraping results with analyzed reviews
CREATE TABLE IF NOT EXISTS scraped_products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    product_name TEXT,
    total_reviews INT DEFAULT 0,
    avg_rating FLOAT,
    sentiment_summary JSONB DEFAULT '{}',
    reviews JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scraped_products_user_id ON scraped_products(user_id);


-- ── 4. Row Level Security (RLS) ─────────────────────────────────
-- Users can only access their own data

ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_products ENABLE ROW LEVEL SECURITY;

-- Analyses policies
CREATE POLICY "Users can view own analyses"
    ON analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analyses"
    ON analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own analyses"
    ON analyses FOR DELETE
    USING (auth.uid() = user_id);

-- Batch jobs policies
CREATE POLICY "Users can view own batch_jobs"
    ON batch_jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own batch_jobs"
    ON batch_jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Scraped products policies
CREATE POLICY "Users can view own scraped_products"
    ON scraped_products FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scraped_products"
    ON scraped_products FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own scraped_products"
    ON scraped_products FOR DELETE
    USING (auth.uid() = user_id);


-- ── 5. Service Role Bypass ──────────────────────────────────────
-- Allow the backend service role to bypass RLS for server-side operations

CREATE POLICY "Service role full access to analyses"
    ON analyses FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to batch_jobs"
    ON batch_jobs FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to scraped_products"
    ON scraped_products FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');


-- ── 6. Storage Bucket for CSV Uploads ───────────────────────────
-- Run this separately or via Supabase Dashboard → Storage
-- INSERT INTO storage.buckets (id, name, public) VALUES ('batch-uploads', 'batch-uploads', false);
