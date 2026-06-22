'use client';

/**
 * SentimentIQ — History Page
 *
 * Displays past analysis records from Supabase with filters.
 */

import { useState, useEffect } from 'react';
import api from '@/lib/api';

const SENTIMENT_COLORS = {
  positive: 'var(--positive)',
  negative: 'var(--negative)',
  neutral: 'var(--neutral)',
  mixed: 'var(--mixed)',
};

export default function HistoryPage({ user }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ source: '', sentiment: '' });

  useEffect(() => {
    if (user) fetchHistory();
  }, [user, filters]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getHistory(1, 50, filters);
      setHistory(data.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="animate-fade-in">
        <div className="page-header">
          <h1>📋 Analysis History</h1>
          <p>View your past analyses</p>
        </div>
        <div className="glass-card empty-state">
          <div style={{ fontSize: '3rem', marginBottom: 'var(--space-md)' }}>🔐</div>
          <h3>Sign In Required</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '400px' }}>
            Sign in to save and view your analysis history. Your results will be securely stored in Supabase.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>📋 Analysis History</h1>
        <p>Browse your past analyses</p>
      </div>

      {/* Filters */}
      <div className="glass-card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div style={{ display: 'flex', gap: 'var(--space-lg)', flexWrap: 'wrap' }}>
          <div>
            <label className="label">Source</label>
            <select
              className="input"
              value={filters.source}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              style={{ width: '160px' }}
            >
              <option value="">All Sources</option>
              <option value="manual">Manual</option>
              <option value="batch">Batch</option>
              <option value="scrape">Scraper</option>
            </select>
          </div>
          <div>
            <label className="label">Sentiment</label>
            <select
              className="input"
              value={filters.sentiment}
              onChange={(e) => setFilters({ ...filters, sentiment: e.target.value })}
              style={{ width: '160px' }}
            >
              <option value="">All</option>
              <option value="positive">Positive</option>
              <option value="negative">Negative</option>
              <option value="neutral">Neutral</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="glass-card empty-state">
          <div className="spinner spinner-lg" />
          <h3 style={{ marginTop: 'var(--space-md)' }}>Loading history...</h3>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-card" style={{
          borderColor: 'var(--negative-border)',
          background: 'var(--negative-bg)',
          marginBottom: 'var(--space-xl)',
        }}>
          <p style={{ color: 'var(--negative)' }}>⚠️ {error}</p>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && history.length === 0 && (
        <div className="glass-card empty-state">
          <div style={{ fontSize: '3rem', marginBottom: 'var(--space-md)' }}>📭</div>
          <h3>No analyses yet</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Start analyzing text to build your history
          </p>
        </div>
      )}

      {/* History List */}
      {history.map((item, i) => (
        <div
          key={item.id}
          className="glass-card animate-fade-in-up"
          style={{
            marginBottom: 'var(--space-md)',
            animationDelay: `${i * 0.05}s`,
            borderLeft: `3px solid ${SENTIMENT_COLORS[item.overall_sentiment]}`,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-sm)' }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: '0.9rem', lineHeight: 1.5 }}>{item.input_text}</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', flexShrink: 0, marginLeft: 'var(--space-md)' }}>
              <span className={`badge badge-${item.overall_sentiment}`}>
                {item.overall_sentiment}
              </span>
              <button
                className="btn btn-ghost btn-sm"
                onClick={async () => {
                  try {
                    await api.deleteAnalysis(item.id);
                    setHistory(history.filter(h => h.id !== item.id));
                  } catch (err) {
                    setError(err.message);
                  }
                }}
                title="Delete"
              >
                🗑️
              </button>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-md)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>{new Date(item.created_at).toLocaleString()}</span>
            <span style={{ textTransform: 'capitalize' }}>📁 {item.source}</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>
              {(item.overall_confidence * 100).toFixed(0)}% confidence
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
