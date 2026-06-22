'use client';

/**
 * SentimentIQ — Dashboard Page
 *
 * Shows REAL user statistics pulled from the /api/stats endpoint:
 *  - Total analyses, batch jobs, scrape sessions
 *  - Sentiment breakdown donut chart
 *  - Average confidence score
 *  - Top detected emotion
 *  - Recent activity (last 7 days)
 *  - 30-day sentiment trend sparkline
 *  - Quick analyze widget
 */

import { useState, useEffect, useRef } from 'react';
import styles from './dashboard.module.css';
import api from '@/lib/api';

// ── Color maps ────────────────────────────────────────────────
const SENTIMENT_COLORS = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral:  '#f59e0b',
  mixed:    '#3b82f6',
};

const EMOTION_ICONS = {
  joy:        '😄',
  admiration: '🤩',
  love:       '❤️',
  optimism:   '🌟',
  excitement: '🎉',
  gratitude:  '🙏',
  approval:   '👍',
  anger:      '😠',
  sadness:    '😢',
  fear:       '😨',
  disgust:    '🤢',
  surprise:   '😲',
  neutral:    '😐',
  confusion:  '😕',
  curiosity:  '🤔',
  desire:     '😍',
};

// ── Skeleton block ────────────────────────────────────────────
function Skeleton({ width = '100%', height = '1rem', style = {} }) {
  return (
    <div
      className="skeleton"
      style={{ width, height, borderRadius: '6px', ...style }}
    />
  );
}

// ── SVG Donut Chart ───────────────────────────────────────────
function DonutChart({ data, size = 140, thickness = 28 }) {
  const r = (size - thickness) / 2;
  const circ = 2 * Math.PI * r;
  const cx = size / 2;
  const cy = size / 2;

  const total = Object.values(data).reduce((s, v) => s + v, 0);
  if (total === 0) {
    return (
      <svg width={size} height={size}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={thickness} />
        <text x={cx} y={cy + 5} textAnchor="middle" fill="var(--text-muted)" fontSize="12">No data</text>
      </svg>
    );
  }

  const order = ['positive', 'negative', 'neutral', 'mixed'];
  let offset = 0;
  const slices = order.map((key) => {
    const value = data[key] || 0;
    const pct = value / total;
    const dash = pct * circ;
    const gap = circ - dash;
    const slice = { key, value, pct, dash, gap, offset: offset * circ };
    offset += pct;
    return slice;
  });

  const dominant = order.reduce((a, b) => (data[a] || 0) >= (data[b] || 0) ? a : b);

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      {/* Track */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth={thickness} />
      {slices.map((s) =>
        s.value > 0 ? (
          <circle
            key={s.key}
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={SENTIMENT_COLORS[s.key]}
            strokeWidth={thickness}
            strokeDasharray={`${s.dash} ${s.gap}`}
            strokeDashoffset={-s.offset}
            strokeLinecap="butt"
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        ) : null
      )}
      {/* Center label — counter-rotate */}
      <g style={{ transform: `rotate(90deg) translate(0, 0)` }}>
        <text
          x={0}
          y={0}
          transform={`translate(${cx}, ${cy - 8}) rotate(90)`}
          textAnchor="middle"
          fill={SENTIMENT_COLORS[dominant]}
          fontSize="22"
          fontWeight="700"
          fontFamily="Inter, sans-serif"
        >
          {Math.round((data[dominant] || 0) / total * 100)}%
        </text>
        <text
          transform={`translate(${cx}, ${cy + 14}) rotate(90)`}
          textAnchor="middle"
          fill="var(--text-muted)"
          fontSize="11"
          fontFamily="Inter, sans-serif"
        >
          {dominant}
        </text>
      </g>
    </svg>
  );
}

// ── Trend Sparkline ───────────────────────────────────────────
function Sparkline({ data, color = '#10b981', height = 48, width = '100%' }) {
  const svgRef = useRef(null);
  const [svgWidth, setSvgWidth] = useState(200);

  useEffect(() => {
    if (svgRef.current) {
      setSvgWidth(svgRef.current.clientWidth || 200);
    }
  }, []);

  if (!data || data.length < 2) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
        Not enough data yet
      </div>
    );
  }

  const values = data.map((d) => d.total);
  const max = Math.max(...values, 1);
  const min = Math.min(...values);
  const pad = 4;
  const points = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * (svgWidth - pad * 2);
    const y = height - pad - ((v - min) / (max - min || 1)) * (height - pad * 2);
    return `${x},${y}`;
  });

  const polyline = points.join(' ');
  const firstPt = points[0];
  const lastPt = points[points.length - 1];
  const area = `${firstPt.split(',')[0]},${height} ${polyline} ${lastPt.split(',')[0]},${height}`;

  return (
    <svg ref={svgRef} width="100%" height={height} style={{ display: 'block', overflow: 'visible' }}>
      <defs>
        <linearGradient id="sparkGrad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill="url(#sparkGrad)" />
      <polyline points={polyline} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {/* Last point dot */}
      {points.length > 0 && (() => {
        const [lx, ly] = lastPt.split(',');
        return <circle cx={lx} cy={ly} r="3.5" fill={color} />;
      })()}
    </svg>
  );
}

// ── Main Dashboard ────────────────────────────────────────────
export default function DashboardPage({ onNavigate }) {
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState('');

  const [quickText, setQuickText] = useState('');
  const [quickResult, setQuickResult] = useState(null);
  const [quickLoading, setQuickLoading] = useState(false);
  const [quickError, setQuickError] = useState('');

  // ── Load stats on mount ──────────────────────────────────
  useEffect(() => {
    async function loadStats() {
      try {
        const data = await api.getStats();
        setStats(data);
      } catch (err) {
        setStatsError(err.message);
      } finally {
        setStatsLoading(false);
      }
    }
    loadStats();
  }, []);

  // ── Quick Analyze ─────────────────────────────────────────
  const handleQuickAnalyze = async () => {
    if (!quickText.trim() || quickText.trim().length < 3) return;
    setQuickLoading(true);
    setQuickError('');
    setQuickResult(null);
    try {
      const result = await api.analyze(quickText);
      setQuickResult(result);
      // Refresh stats silently after a new analysis
      api.getStats().then(setStats).catch(() => {});
    } catch (err) {
      setQuickError(err.message);
    } finally {
      setQuickLoading(false);
    }
  };

  // ── Stat Card Component ───────────────────────────────────
  const StatCard = ({ icon, value, label, sublabel, color, delay, loading }) => (
    <div className={`${styles.statCard} animate-fade-in-up delay-${delay}`}>
      <div className={styles.statCardInner}>
        <div className={styles.statIcon} style={{ color, background: `${color}18`, borderColor: `${color}30` }}>
          {icon}
        </div>
        <div className={styles.statContent}>
          {loading ? (
            <>
              <Skeleton width="60px" height="1.8rem" style={{ marginBottom: '6px' }} />
              <Skeleton width="80px" height="0.75rem" />
            </>
          ) : (
            <>
              <div className={styles.statValue} style={{ color }}>{value}</div>
              <div className={styles.statLabel}>{label}</div>
              {sublabel && <div className={styles.statSublabel}>{sublabel}</div>}
            </>
          )}
        </div>
      </div>
    </div>
  );

  const total = stats?.total_analyses ?? 0;
  const avgPct = stats ? Math.round(stats.avg_confidence * 100) : 0;
  const topEmotion = stats?.top_emotion ?? '—';
  const recent7 = stats?.recent_7_days ?? 0;
  const breakdown = stats?.sentiment_breakdown ?? { positive: 0, negative: 0, neutral: 0, mixed: 0 };

  return (
    <div className="animate-fade-in">

      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Your real-time sentiment analysis workspace</p>
      </div>

      {statsError && (
        <div className={styles.statsError}>
          ⚠️ Could not load stats: {statsError}
        </div>
      )}

      {/* ── Stat Cards ──────────────────────────────────────── */}
      <div className={styles.statsGrid}>
        <StatCard
          icon="🧠"
          value={total.toLocaleString()}
          label="Total Analyses"
          sublabel={`${recent7} in last 7 days`}
          color="#a78bfa"
          delay={1}
          loading={statsLoading}
        />
        <StatCard
          icon="📦"
          value={stats?.total_batch_jobs?.toLocaleString() ?? '0'}
          label="Batch Jobs"
          sublabel={`${stats?.total_batch_reviews?.toLocaleString() ?? 0} reviews processed`}
          color="#38bdf8"
          delay={2}
          loading={statsLoading}
        />
        <StatCard
          icon="🎯"
          value={total > 0 ? `${avgPct}%` : '—'}
          label="Avg Confidence"
          sublabel="across all analyses"
          color="#10b981"
          delay={3}
          loading={statsLoading}
        />
        <StatCard
          icon={EMOTION_ICONS[topEmotion] ?? '💡'}
          value={topEmotion === '—' ? '—' : topEmotion.charAt(0).toUpperCase() + topEmotion.slice(1)}
          label="Top Emotion"
          sublabel="most detected overall"
          color="#f97316"
          delay={4}
          loading={statsLoading}
        />
      </div>

      {/* ── Charts Row ──────────────────────────────────────── */}
      <div className={styles.chartsRow}>

        {/* Sentiment Breakdown Donut */}
        <div className={`${styles.chartCard} animate-fade-in-up delay-3`}>
          <div className={styles.chartHeader}>
            <h3>Sentiment Breakdown</h3>
            <span className={styles.chartTotal}>{total} total</span>
          </div>
          {statsLoading ? (
            <div className={styles.donutWrap}>
              <Skeleton width="140px" height="140px" style={{ borderRadius: '50%' }} />
            </div>
          ) : (
            <div className={styles.donutWrap}>
              <DonutChart data={breakdown} size={148} thickness={30} />
            </div>
          )}
          <div className={styles.donutLegend}>
            {Object.entries(breakdown).map(([key, val]) => (
              <div key={key} className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: SENTIMENT_COLORS[key] }} />
                <span className={styles.legendLabel}>{key}</span>
                <span className={styles.legendVal}>
                  {statsLoading ? <Skeleton width="24px" height="0.8rem" /> : val}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 30-day Trend Sparkline */}
        <div className={`${styles.chartCard} ${styles.chartCardWide} animate-fade-in-up delay-4`}>
          <div className={styles.chartHeader}>
            <h3>30-Day Activity</h3>
            <span className={styles.chartTotal}>analyses per day</span>
          </div>
          {statsLoading ? (
            <Skeleton width="100%" height="60px" style={{ marginTop: '16px' }} />
          ) : (
            <div className={styles.sparklineWrap}>
              <Sparkline data={stats?.trend ?? []} color="#6366f1" height={72} />
              {(stats?.trend?.length ?? 0) === 0 && (
                <div className={styles.noDataLabel}>Run your first analysis to see the trend!</div>
              )}
            </div>
          )}
          {/* Mini sentiment legend under sparkline */}
          {!statsLoading && (stats?.trend?.length ?? 0) > 0 && (
            <div className={styles.trendFooter}>
              {['positive', 'negative', 'neutral'].map((s) => (
                <div key={s} className={styles.trendFooterItem}>
                  <span style={{ background: SENTIMENT_COLORS[s] }} className={styles.trendDot} />
                  {breakdown[s]} {s}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Quick Analyze ────────────────────────────────────── */}
      <div className={`${styles.quickSection} animate-fade-in-up delay-4`}>
        <div className={styles.quickCard}>
          <div className={styles.quickHeader}>
            <div>
              <h3>⚡ Quick Analyze</h3>
              <p>Paste any text to instantly analyze its sentiment</p>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleQuickAnalyze}
              disabled={quickLoading || quickText.trim().length < 3}
            >
              {quickLoading ? <><span className="spinner" /> Analyzing…</> : 'Analyze'}
            </button>
          </div>

          <textarea
            className="input"
            placeholder="Paste a review, tweet, or any feedback here… (Ctrl+Enter to analyze)"
            value={quickText}
            onChange={(e) => setQuickText(e.target.value)}
            rows={4}
            onKeyDown={(e) => { if (e.key === 'Enter' && e.ctrlKey) handleQuickAnalyze(); }}
          />

          {quickError && (
            <div className={styles.inlineError}>⚠️ {quickError}</div>
          )}

          {quickResult && (
            <div className={styles.quickResult}>
              {/* Header row */}
              <div className={styles.quickResultHeader}>
                <span className={`badge badge-${quickResult.overall_sentiment}`}>
                  {quickResult.overall_sentiment}
                </span>
                <span className={styles.quickMeta}>
                  {(quickResult.overall_confidence * 100).toFixed(1)}% confidence
                  &nbsp;·&nbsp;
                  {quickResult.processing_time_ms?.toFixed(0)}ms
                </span>
              </div>

              {/* Sentence highlights */}
              <div className={styles.sentences}>
                {quickResult.sentences?.map((sent, i) => (
                  <span
                    key={i}
                    className={styles.sentenceChip}
                    style={{
                      borderLeftColor: SENTIMENT_COLORS[sent.sentiment],
                      background: `${SENTIMENT_COLORS[sent.sentiment]}12`,
                    }}
                  >
                    {sent.text}
                  </span>
                ))}
              </div>

              {/* Top emotions */}
              {quickResult.emotion_distribution && (
                <div className={styles.emotionBars}>
                  {Object.entries(quickResult.emotion_distribution)
                    .filter(([, v]) => v > 0.02)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([emotion, score]) => (
                      <div key={emotion} className={styles.emotionRow}>
                        <span className={styles.emotionName}>
                          {EMOTION_ICONS[emotion] ?? '•'} {emotion}
                        </span>
                        <div className={styles.emotionTrack}>
                          <div
                            className={styles.emotionFill}
                            style={{ width: `${score * 100}%` }}
                          />
                        </div>
                        <span className={styles.emotionPct}>{(score * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Feature Navigation ───────────────────────────────── */}
      <div className={styles.featuresGrid}>
        {[
          { key: 'analyzer', icon: '🧠', title: 'Real-time Analyzer', desc: 'Deep-dive analysis with sentence-level highlighting, emotion radar, and aspect breakdown.', cta: 'Open Analyzer →' },
          { key: 'scraper',  icon: '🔍', title: 'E-Commerce Scraper', desc: 'Scrape product reviews from Amazon, Flipkart and more. Instant analytics.', cta: 'Open Scraper →' },
          { key: 'history',  icon: '📋', title: 'Analysis History', desc: 'Browse, search, and filter your past analyses. Track sentiment over time.', cta: 'View History →' },
        ].map((f, i) => (
          <div
            key={f.key}
            className={`${styles.featureCard} animate-fade-in-up delay-${i + 3}`}
            onClick={() => onNavigate(f.key)}
          >
            <div className={styles.featureIcon}>{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
            <div className={styles.featureArrow}>{f.cta}</div>
          </div>
        ))}
      </div>

    </div>
  );
}
