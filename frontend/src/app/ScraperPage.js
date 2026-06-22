'use client';

/**
 * SentimentIQ — Scraper Page
 *
 * E-commerce review scraper with:
 * - URL input or preset product selection
 * - Sentiment distribution donut chart (pure CSS/SVG)
 * - Rating distribution bar chart
 * - Key strengths & weaknesses
 * - Filterable review feed
 */

import { useState, useEffect } from 'react';
import styles from './scraper.module.css';
import api from '@/lib/api';

const PRESET_PRODUCTS = [
  { id: 'headphones', name: '🎧 Headphones', url: 'https://example.com/products/headphones' },
  { id: 'smartwatch', name: '⌚ Smartwatch', url: 'https://example.com/products/smartwatch' },
  { id: 'laptop', name: '💻 Laptop', url: 'https://example.com/products/laptop' },
  { id: 'skincare', name: '✨ Skincare', url: 'https://example.com/products/skincare' },
  { id: 'coffee', name: '☕ Coffee', url: 'https://example.com/products/coffee' },
  { id: 'saas', name: '📊 SaaS Tool', url: 'https://example.com/products/software' },
];

const SENTIMENT_COLORS = {
  positive: 'var(--positive)',
  negative: 'var(--negative)',
  neutral: 'var(--neutral)',
  mixed: 'var(--mixed)',
};

const RATING_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981'];

function DonutChart({ distribution }) {
  const total = Object.values(distribution).reduce((a, b) => a + b, 0) || 1;
  const segments = [
    { key: 'positive', color: '#10b981', value: distribution.positive || 0 },
    { key: 'negative', color: '#ef4444', value: distribution.negative || 0 },
    { key: 'neutral', color: '#f59e0b', value: distribution.neutral || 0 },
    { key: 'mixed', color: '#3b82f6', value: distribution.mixed || 0 },
  ].filter(s => s.value > 0);

  let cumulative = 0;
  const size = 140;
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className={styles.donutChart}>
      <svg className={styles.donutRing} width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {segments.map((seg) => {
          const pct = seg.value / total;
          const dashArray = `${pct * circumference} ${circumference}`;
          const dashOffset = -cumulative * circumference;
          cumulative += pct;

          return (
            <circle
              key={seg.key}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={seg.color}
              strokeWidth={strokeWidth}
              strokeDasharray={dashArray}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
              style={{ transition: 'stroke-dasharray 0.6s ease' }}
            />
          );
        })}
      </svg>

      <div className={styles.donutLegend}>
        {segments.map(seg => (
          <div key={seg.key} className={styles.legendItem}>
            <span className={styles.legendDot} style={{ backgroundColor: seg.color }} />
            <span style={{ textTransform: 'capitalize' }}>{seg.key}</span>
            <span className={styles.legendPct}>{(seg.value * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ScraperPage() {
  const [url, setUrl] = useState('');
  const [selectedPreset, setSelectedPreset] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');

  const handlePresetClick = (preset) => {
    setUrl(preset.url);
    setSelectedPreset(preset.id);
    setResult(null);
    setError('');
  };

  const handleScrape = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await api.scrape(url, 3, true); // use_mock=true for demo
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredReviews = result?.reviews?.filter(r => {
    if (filter === 'all') return true;
    return r.sentiment === filter;
  }) || [];

  const maxRating = result ? Math.max(...Object.values(result.rating_distribution || {}), 1) : 1;

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>🔍 E-Commerce Scraper</h1>
        <p>Scrape product reviews and get instant sentiment analytics</p>
      </div>

      {/* Input Section */}
      <div className={`glass-card ${styles.scraperInput}`}>
        <label className="label">Product URL</label>
        <div className={styles.urlRow}>
          <input
            type="url"
            className="input"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setSelectedPreset(''); }}
            placeholder="Paste an Amazon, Flipkart, or any product URL..."
          />
          <button
            className="btn btn-primary"
            onClick={handleScrape}
            disabled={loading || !url.trim()}
          >
            {loading ? (
              <><span className="spinner" /> Scraping...</>
            ) : (
              '🚀 Scrape & Analyze'
            )}
          </button>
        </div>

        <label className="label">Or select a preset product</label>
        <div className={styles.presets}>
          {PRESET_PRODUCTS.map(preset => (
            <button
              key={preset.id}
              className={`${styles.presetChip} ${selectedPreset === preset.id ? styles.presetChipActive : ''}`}
              onClick={() => handlePresetClick(preset)}
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className={styles.progressCard}>
          <div className="spinner spinner-lg" style={{ margin: '0 auto var(--space-md)' }} />
          <h3>Scraping & Analyzing Reviews...</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 'var(--space-md)' }}>
            Running each review through the NLP pipeline
          </p>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: '60%' }} />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-card" style={{
          borderColor: 'var(--negative-border)',
          background: 'var(--negative-bg)',
          marginBottom: 'var(--space-xl)',
        }}>
          <p style={{ color: 'var(--negative)', fontSize: '0.9rem' }}>⚠️ {error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="animate-fade-in-up">
          {/* Product Header */}
          <div className="glass-card" style={{ marginBottom: 'var(--space-xl)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>{result.product_name}</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
                  {result.source === 'mock' ? '🎭 Simulated data' : '🌐 Scraped'} · {result.total_reviews} reviews · {result.processing_time_ms.toFixed(0)}ms
                </p>
              </div>
              <span className={`badge badge-${result.overall_sentiment}`} style={{ fontSize: '0.85rem', padding: '6px 16px' }}>
                {result.overall_sentiment}
              </span>
            </div>
          </div>

          {/* Metric Cards */}
          <div className={styles.resultsGrid}>
            <div className={`${styles.metricCard} animate-fade-in-up delay-1`}>
              <div className={styles.metricValue}>{result.total_reviews}</div>
              <div className={styles.metricLabel}>Total Reviews</div>
            </div>
            <div className={`${styles.metricCard} animate-fade-in-up delay-2`}>
              <div className={styles.metricValue} style={{ color: 'var(--positive)' }}>
                {result.average_rating ? `${result.average_rating}★` : 'N/A'}
              </div>
              <div className={styles.metricLabel}>Avg Rating</div>
            </div>
            <div className={`${styles.metricCard} animate-fade-in-up delay-3`}>
              <div className={styles.metricValue} style={{ color: 'var(--positive)' }}>
                {((result.sentiment_distribution?.positive || 0) * 100).toFixed(0)}%
              </div>
              <div className={styles.metricLabel}>Positive</div>
            </div>
            <div className={`${styles.metricCard} animate-fade-in-up delay-4`}>
              <div className={styles.metricValue} style={{ color: 'var(--negative)' }}>
                {((result.sentiment_distribution?.negative || 0) * 100).toFixed(0)}%
              </div>
              <div className={styles.metricLabel}>Negative</div>
            </div>
          </div>

          {/* Charts */}
          <div className={styles.chartsRow}>
            {/* Sentiment Distribution */}
            <div className={`${styles.chartCard} animate-fade-in-up delay-2`}>
              <div className={styles.chartTitle}>Sentiment Distribution</div>
              <DonutChart distribution={result.sentiment_distribution || {}} />
            </div>

            {/* Rating Distribution */}
            <div className={`${styles.chartCard} animate-fade-in-up delay-3`}>
              <div className={styles.chartTitle}>Rating Distribution</div>
              <div className={styles.barChart}>
                {[5, 4, 3, 2, 1].map(star => {
                  const count = result.rating_distribution?.[String(star)] || 0;
                  const pct = (count / maxRating) * 100;
                  return (
                    <div key={star} className={styles.barRow}>
                      <span className={styles.barLabel}>{star}★</span>
                      <div className={styles.barTrack}>
                        <div
                          className={styles.barFill}
                          style={{
                            width: `${Math.max(pct, 4)}%`,
                            backgroundColor: RATING_COLORS[star - 1],
                          }}
                        />
                      </div>
                      <span className={styles.barCount}>{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Insights */}
          <div className={styles.insightsRow}>
            <div className={`${styles.insightCard} animate-fade-in-up delay-3`}>
              <div className={styles.chartTitle}>💪 Key Strengths</div>
              <ul className={styles.insightList}>
                {(result.key_strengths?.length > 0 ? result.key_strengths : ['No specific strengths identified']).map((s, i) => (
                  <li key={i}>
                    <span style={{ color: 'var(--positive)' }}>✓</span>
                    <span style={{ textTransform: 'capitalize' }}>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className={`${styles.insightCard} animate-fade-in-up delay-4`}>
              <div className={styles.chartTitle}>⚠️ Key Weaknesses</div>
              <ul className={styles.insightList}>
                {(result.key_weaknesses?.length > 0 ? result.key_weaknesses : ['No specific weaknesses identified']).map((s, i) => (
                  <li key={i}>
                    <span style={{ color: 'var(--negative)' }}>✗</span>
                    <span style={{ textTransform: 'capitalize' }}>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Top Aspects */}
          {result.top_aspects?.length > 0 && (
            <div className="glass-card animate-fade-in-up delay-4" style={{ marginBottom: 'var(--space-xl)' }}>
              <div className={styles.chartTitle}>📊 Top Aspects</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
                {result.top_aspects.map((asp, i) => (
                  <span
                    key={i}
                    className={`badge badge-${asp.sentiment}`}
                    style={{ fontSize: '0.8rem', padding: '4px 12px' }}
                  >
                    {asp.sentiment === 'positive' ? '👍' : '👎'} {asp.aspect}
                    {asp.mention_count > 1 && ` (${asp.mention_count})`}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Review Feed */}
          <div className={styles.reviewsFeed}>
            <h3 style={{ marginBottom: 'var(--space-md)' }}>📝 Reviews ({result.reviews?.length || 0})</h3>
            <div className={styles.feedFilters}>
              {['all', 'positive', 'negative', 'neutral', 'mixed'].map(f => (
                <button
                  key={f}
                  className={`${styles.filterBtn} ${filter === f ? styles.filterBtnActive : ''}`}
                  onClick={() => setFilter(f)}
                >
                  {f === 'all' ? `All (${result.reviews?.length || 0})` :
                    `${f} (${result.reviews?.filter(r => r.sentiment === f).length || 0})`}
                </button>
              ))}
            </div>

            {filteredReviews.map((review, i) => (
              <div key={i} className={`${styles.reviewItem} animate-fade-in-up`} style={{ animationDelay: `${i * 0.05}s` }}>
                <div className={styles.reviewHeader}>
                  <div className={styles.reviewerInfo}>
                    <span className={styles.reviewerName}>{review.reviewer_name}</span>
                    <span className={styles.reviewDate}>{review.date}</span>
                  </div>
                  <span className={styles.reviewStars}>
                    {review.rating ? '★'.repeat(Math.round(review.rating)) + '☆'.repeat(5 - Math.round(review.rating)) : ''}
                  </span>
                </div>
                <p className={styles.reviewText}>{review.text}</p>
                <div className={styles.reviewMeta}>
                  <span className={`badge badge-${review.sentiment}`}>{review.sentiment}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {(review.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
