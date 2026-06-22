'use client';

/**
 * SentimentIQ — Analyzer Page
 * 
 * Full-featured real-time text analyzer with:
 * - Sentence-level sentiment highlighting
 * - Emotion distribution bars
 * - Aspect-based sentiment tags
 * - Named entity display
 */

import { useState } from 'react';
import styles from './analyzer.module.css';
import api from '@/lib/api';

const SENTIMENT_COLORS = {
  positive: 'var(--positive)',
  negative: 'var(--negative)',
  neutral: 'var(--neutral)',
  mixed: 'var(--mixed)',
};

const EMOTION_COLORS = {
  joy: '#fbbf24',
  anger: '#ef4444',
  sadness: '#6366f1',
  fear: '#8b5cf6',
  surprise: '#f97316',
  disgust: '#84cc16',
  love: '#ec4899',
  optimism: '#10b981',
  pessimism: '#94a3b8',
};

const SAMPLE_TEXTS = [
  {
    label: '🎧 Headphones',
    text: 'The noise cancellation on these headphones is incredible — I can\'t hear anything around me when it\'s on. Sound quality is rich and detailed with deep bass. However, the build quality is disappointing. The headband feels flimsy and the ear cushions started peeling after just 3 months. For the price, I expected much better durability. Battery life is great though, easily lasting 30+ hours.',
  },
  {
    label: '📱 Phone',
    text: 'I absolutely love the camera on this phone! The night mode is game-changing and portrait shots look professional. The display is stunning with vibrant colors. But the battery barely lasts a full day with heavy use, which is frustrating. Also, it gets uncomfortably hot during gaming sessions. The software experience is smooth and clean though.',
  },
  {
    label: '☕ Coffee',
    text: 'This is the best coffee I\'ve ever had! Rich, bold flavor with hints of dark chocolate and zero bitterness. The beans arrive fresh and the aroma is heavenly. Makes perfect espresso and works great in a French press too. Will definitely subscribe for monthly delivery.',
  },
  {
    label: '😡 Bad Service',
    text: 'Terrible customer service experience. I waited 45 minutes on hold just to be transferred to another department. The representative was rude and unhelpful. My issue still hasn\'t been resolved after 3 calls. The product itself broke within a week. I want a full refund and will never buy from this company again.',
  },
];

export default function AnalyzerPage() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!text.trim() || text.trim().length < 3) return;
    setLoading(true);
    setError('');

    try {
      const data = await api.analyze(text);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSample = (sampleText) => {
    setText(sampleText);
    setResult(null);
    setError('');
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>🧠 Real-time Analyzer</h1>
        <p>Paste any text — reviews, feedback, comments — for deep sentiment analysis</p>
      </div>

      <div className={styles.analyzerLayout}>
        {/* Left: Input */}
        <div className={styles.inputPanel}>
          <div className="glass-card">
            <label className="label">Input Text</label>
            <div className={styles.textareaWrapper}>
              <textarea
                className="input"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste a review, feedback, or any text to analyze its sentiment, emotions, and aspects..."
                style={{ minHeight: '240px' }}
              />
              <span className={styles.charCount}>
                {text.length.toLocaleString()} chars · ~{text.split(/\s+/).filter(Boolean).length} words
              </span>
            </div>

            <div className={styles.actionBar}>
              <button
                className="btn btn-primary btn-lg"
                onClick={handleAnalyze}
                disabled={loading || !text.trim()}
              >
                {loading ? (
                  <><span className="spinner" /> Analyzing...</>
                ) : (
                  '🔍 Analyze Sentiment'
                )}
              </button>
              <button
                className="btn btn-ghost"
                onClick={() => { setText(''); setResult(null); setError(''); }}
              >
                Clear
              </button>
            </div>

            {/* Sample texts */}
            <div>
              <label className="label" style={{ marginTop: 'var(--space-md)' }}>Try a sample</label>
              <div className={styles.sampleBtns}>
                {SAMPLE_TEXTS.map((sample) => (
                  <button
                    key={sample.label}
                    className={styles.sampleBtn}
                    onClick={() => handleSample(sample.text)}
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {error && (
            <div className="glass-card" style={{
              borderColor: 'var(--negative-border)',
              background: 'var(--negative-bg)',
            }}>
              <p style={{ color: 'var(--negative)', fontSize: '0.9rem' }}>⚠️ {error}</p>
            </div>
          )}

          {/* Aspects */}
          {result?.aspect_sentiments?.length > 0 && (
            <div className={`${styles.aspectsCard} animate-fade-in-up`}>
              <h4 style={{ marginBottom: 'var(--space-md)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                📊 Aspect Sentiments ({result.aspect_sentiments.length})
              </h4>
              <div className={styles.aspectTags}>
                {result.aspect_sentiments.map((asp, i) => (
                  <span
                    key={i}
                    className={styles.aspectTag}
                    style={{
                      background: asp.sentiment === 'positive'
                        ? 'var(--positive-bg)'
                        : asp.sentiment === 'negative'
                          ? 'var(--negative-bg)'
                          : 'var(--neutral-bg)',
                      border: `1px solid ${asp.sentiment === 'positive'
                        ? 'var(--positive-border)'
                        : asp.sentiment === 'negative'
                          ? 'var(--negative-border)'
                          : 'var(--neutral-border)'}`,
                      color: SENTIMENT_COLORS[asp.sentiment],
                    }}
                  >
                    {asp.sentiment === 'positive' ? '👍' : asp.sentiment === 'negative' ? '👎' : '➖'}
                    {asp.aspect}
                    {asp.mention_count > 1 && (
                      <span style={{ opacity: 0.6, fontSize: '0.7rem' }}>×{asp.mention_count}</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Entities */}
          {result?.entity_mentions?.length > 0 && (
            <div className={`${styles.entitiesCard} animate-fade-in-up`}>
              <h4 style={{ marginBottom: 'var(--space-md)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                🏷️ Named Entities
              </h4>
              <div>
                {result.entity_mentions.map((entity, i) => (
                  <span key={i} className={styles.entityTag}>{entity}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Results */}
        <div className={styles.resultsPanel}>
          {!result && !loading && (
            <div className="glass-card empty-state">
              <div style={{ fontSize: '3rem', marginBottom: 'var(--space-md)' }}>🧠</div>
              <h3>Ready to Analyze</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Enter text and click Analyze to see results
              </p>
            </div>
          )}

          {loading && (
            <div className="glass-card empty-state">
              <div className="spinner spinner-lg" />
              <h3 style={{ marginTop: 'var(--space-md)' }}>Processing...</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Running through DistilBERT + GoEmotions pipeline
              </p>
            </div>
          )}

          {result && (
            <>
              {/* Sentiment Overview */}
              <div className={`${styles.overviewCard} animate-scale-in`}>
                <div className={styles.overviewHeader}>
                  <div className={styles.sentimentDisplay}>
                    <div
                      className={styles.sentimentCircle}
                      style={{
                        backgroundColor: `${SENTIMENT_COLORS[result.overall_sentiment]}15`,
                        color: SENTIMENT_COLORS[result.overall_sentiment],
                        borderColor: SENTIMENT_COLORS[result.overall_sentiment],
                      }}
                    >
                      {result.overall_sentiment === 'positive' ? '😊' :
                       result.overall_sentiment === 'negative' ? '😞' :
                       result.overall_sentiment === 'mixed' ? '😐' : '😶'}
                    </div>
                    <div className={styles.sentimentInfo}>
                      <span
                        className={styles.sentimentLabelLg}
                        style={{ color: SENTIMENT_COLORS[result.overall_sentiment] }}
                      >
                        {result.overall_sentiment}
                      </span>
                      <span className={styles.sentimentMeta}>
                        {(result.overall_confidence * 100).toFixed(1)}% confidence · {result.processing_time_ms.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                </div>

                {/* Ratio bar */}
                <div className={styles.ratioBars}>
                  <div
                    className={styles.ratioSegment}
                    style={{
                      width: `${result.positive_ratio * 100}%`,
                      backgroundColor: 'var(--positive)',
                    }}
                  />
                  <div
                    className={styles.ratioSegment}
                    style={{
                      width: `${result.neutral_ratio * 100}%`,
                      backgroundColor: 'var(--neutral)',
                    }}
                  />
                  <div
                    className={styles.ratioSegment}
                    style={{
                      width: `${result.negative_ratio * 100}%`,
                      backgroundColor: 'var(--negative)',
                    }}
                  />
                </div>

                <div className={styles.ratioLegend}>
                  <div className={styles.ratioItem}>
                    <span className={styles.ratioDot} style={{ backgroundColor: 'var(--positive)' }} />
                    Positive {(result.positive_ratio * 100).toFixed(0)}%
                  </div>
                  <div className={styles.ratioItem}>
                    <span className={styles.ratioDot} style={{ backgroundColor: 'var(--neutral)' }} />
                    Neutral {(result.neutral_ratio * 100).toFixed(0)}%
                  </div>
                  <div className={styles.ratioItem}>
                    <span className={styles.ratioDot} style={{ backgroundColor: 'var(--negative)' }} />
                    Negative {(result.negative_ratio * 100).toFixed(0)}%
                  </div>
                </div>

                <div style={{
                  marginTop: 'var(--space-md)',
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                }}>
                  {result.word_count} words · {result.sentence_count} sentences
                </div>
              </div>

              {/* Emotions */}
              <div className={`${styles.emotionsCard} animate-fade-in-up delay-1`}>
                <h4 style={{ marginBottom: 'var(--space-md)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  💭 Emotion Distribution
                </h4>
                {Object.entries(result.emotion_distribution)
                  .sort((a, b) => b[1] - a[1])
                  .map(([emotion, score]) => (
                    <div key={emotion} className={styles.emotionRow}>
                      <span className={styles.emotionName}>{emotion}</span>
                      <div className={styles.emotionTrack}>
                        <div
                          className={styles.emotionFill}
                          style={{
                            width: `${Math.min(score * 100, 100)}%`,
                            backgroundColor: EMOTION_COLORS[emotion] || '#6366f1',
                          }}
                        />
                      </div>
                      <span className={styles.emotionPct}>
                        {(score * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
              </div>

              {/* Sentences */}
              <div className={`${styles.sentencesCard} animate-fade-in-up delay-2`}>
                <div className={styles.sentencesTitle}>
                  📝 Sentence-Level Breakdown ({result.sentences.length})
                </div>
                {result.sentences.map((sent, i) => (
                  <div
                    key={i}
                    className={styles.sentenceItem}
                    style={{ animationDelay: `${i * 0.05}s` }}
                  >
                    <div
                      className={styles.sentenceBar}
                      style={{ backgroundColor: SENTIMENT_COLORS[sent.sentiment] }}
                    />
                    <div className={styles.sentenceContent}>
                      <div className={styles.sentenceText}>{sent.text}</div>
                      <div className={styles.sentenceMeta}>
                        <span className={`badge badge-${sent.sentiment}`}>
                          {sent.sentiment}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {(sent.confidence * 100).toFixed(1)}%
                        </span>
                        {sent.aspects?.map((asp, j) => (
                          <span
                            key={j}
                            style={{
                              fontSize: '0.7rem',
                              padding: '1px 8px',
                              borderRadius: 'var(--radius-full)',
                              background: 'var(--bg-glass)',
                              border: '1px solid var(--border-subtle)',
                              color: 'var(--text-accent)',
                            }}
                          >
                            {asp.aspect}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
