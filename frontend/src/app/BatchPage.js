'use client';

/**
 * SentimentIQ — Batch Analyzer Page
 *
 * Upload review files (CSV format) for asynchronous batch processing.
 * Displays a live progress bar, aggregate statistics, a CSS donut chart,
 * and a filterable table of results, with a download link to export the analysis.
 */

import { useState, useEffect, useRef } from 'react';
import styles from './batch.module.css';
import api from '@/lib/api';
import { useToast } from './ToastContext';

const SENTIMENT_COLORS = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
  mixed: '#3b82f6',
};

const EMOTION_ICONS = {
  joy: '😄', anger: '😠', sadness: '😢', fear: '😨', surprise: '😲',
  disgust: '🤢', love: '❤️', optimism: '🌟', pessimism: '94a3b8',
};

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
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
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

export default function BatchPage() {
  const { addToast } = useToast();
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Job polling states
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null); // 'pending', 'processing', 'completed', 'failed'
  const [totalReviews, setTotalReviews] = useState(0);
  const [processedReviews, setProcessedReviews] = useState(0);
  const [results, setResults] = useState(null); // list of AnalysisResult
  const [aggregate, setAggregate] = useState(null);
  
  // Table browser states
  const [searchQuery, setSearchQuery] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const fileInputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
      } else {
        addToast('Only CSV files are supported.', 'error');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
      } else {
        addToast('Only CSV files are supported.', 'error');
      }
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current.click();
  };

  const resetUpload = () => {
    setFile(null);
    setJobId(null);
    setStatus(null);
    setTotalReviews(0);
    setProcessedReviews(0);
    setResults(null);
    setAggregate(null);
    setLoading(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const startPolling = (id) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    
    pollIntervalRef.current = setInterval(async () => {
      try {
        const job = await api.getBatchStatus(id);
        setStatus(job.status);
        setProcessedReviews(job.processed_reviews);
        setTotalReviews(job.total_reviews);
        
        if (job.status === 'completed') {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setAggregate(job.aggregate || {});
          setResults(job.results || []);
          setLoading(false);
          addToast('Batch analysis completed successfully!', 'success');
        } else if (job.status === 'failed') {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setLoading(false);
          addToast('Batch analysis failed.', 'error');
        }
      } catch (err) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
        setLoading(false);
        addToast('Error polling job status: ' + err.message, 'error');
      }
    }, 2000);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    addToast('Uploading and scheduling CSV batch job...', 'info');

    try {
      const job = await api.uploadCSV(file);
      setJobId(job.job_id);
      setStatus(job.status || 'pending');
      setTotalReviews(job.total_reviews);
      setProcessedReviews(0);
      
      addToast('Upload successful. Processing batch...', 'success');
      startPolling(job.job_id);
    } catch (err) {
      setLoading(false);
      addToast(err.message || 'Failed to upload batch file', 'error');
    }
  };

  const handleExport = () => {
    if (!jobId) return;
    window.location.href = `${api.baseUrl}/api/batch/${jobId}/export`;
    addToast('Downloading CSV results...', 'success');
  };

  // Table computations
  const getTopEmotion = (emotions) => {
    if (!emotions) return 'neutral';
    const sorted = Object.entries(emotions).sort((a, b) => b[1] - a[1]);
    return sorted[0]?.[0] || 'neutral';
  };

  const filteredResults = (results || []).filter(item => {
    const textMatch = item.input_text.toLowerCase().includes(searchQuery.toLowerCase());
    const sentimentMatch = sentimentFilter === 'all' || item.overall_sentiment === sentimentFilter;
    return textMatch && sentimentMatch;
  });

  const totalPages = Math.ceil(filteredResults.length / itemsPerPage) || 1;
  const paginatedResults = filteredResults.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1>📦 Batch Analyzer</h1>
        <p>Analyze thousands of reviews at once by uploading a CSV file</p>
      </div>

      <div className={styles.batchLayout}>
        {/* Upload Zone */}
        {!jobId && (
          <div className="glass-card" style={{ padding: 'var(--space-xl)' }}>
            <div
              className={`${styles.dropzone} ${dragActive ? styles.dropzoneActive : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={triggerFileSelect}
            >
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: 'none' }}
                accept=".csv"
                onChange={handleFileChange}
              />
              <div className={styles.dropIcon}>📁</div>
              <h3>Drag and drop your CSV review file here</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                CSV must contain a column named <strong>'review'</strong>, <strong>'text'</strong>, <strong>'comment'</strong>, or <strong>'feedback'</strong>
              </p>
              <button className="btn btn-secondary btn-sm" type="button" onClick={(e) => { e.stopPropagation(); triggerFileSelect(); }}>
                Browse Files
              </button>
            </div>

            {file && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: 'var(--space-lg)' }}>
                <div className={styles.fileDetails}>
                  <div className={styles.fileName}>{file.name}</div>
                  <div className={styles.fileSize}>{(file.size / 1024).toFixed(1)} KB</div>
                </div>
                <div className={styles.actionBar}>
                  <button className="btn btn-primary btn-lg" onClick={handleUpload} disabled={loading}>
                    🚀 Start Batch Analysis
                  </button>
                  <button className="btn btn-ghost" onClick={() => setFile(null)} disabled={loading}>
                    Clear
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Polling / Processing UI */}
        {jobId && status !== 'completed' && status !== 'failed' && (
          <div className={styles.progressCard}>
            <div className="spinner spinner-lg" style={{ margin: '0 auto var(--space-md)' }} />
            <h3>Processing Batch Job...</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              SentimentIQ is analyzing your reviews asynchronously. You can wait here or check back later.
            </p>
            
            <div className={styles.progressHeader}>
              <span className={styles.progressLabel}>
                {status === 'pending' ? 'Queued' : `Analyzing: ${processedReviews} of ${totalReviews} reviews`}
              </span>
              <span className={styles.progressPercent}>
                {totalReviews > 0 ? `${Math.round((processedReviews / totalReviews) * 100)}%` : '0%'}
              </span>
            </div>
            
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${totalReviews > 0 ? (processedReviews / totalReviews) * 100 : 0}%` }}
              />
            </div>
            
            <div style={{ marginTop: 'var(--space-md)' }}>
              <button className="btn btn-ghost" onClick={resetUpload}>
                Cancel & Upload New
              </button>
            </div>
          </div>
        )}

        {/* Failed UI */}
        {jobId && status === 'failed' && (
          <div className="glass-card text-center" style={{ padding: 'var(--space-2xl)' }}>
            <div style={{ fontSize: '3rem', marginBottom: 'var(--space-md)' }}>⚠️</div>
            <h2>Batch Job Failed</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-lg)' }}>
              An error occurred while processing the reviews in your CSV file. Please make sure the format is valid.
            </p>
            <button className="btn btn-primary" onClick={resetUpload}>
              Try Another File
            </button>
          </div>
        )}

        {/* Completed Results UI */}
        {jobId && status === 'completed' && aggregate && (
          <div className="animate-fade-in-up" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
            
            {/* Header / Summary Card */}
            <div className="glass-card" style={{ padding: 'var(--space-xl)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
                <div>
                  <h2>Batch Analysis Completed</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '4px' }}>
                    Job ID: {jobId} · Processed {totalReviews} reviews from <strong>{file?.name || 'CSV Upload'}</strong>
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                  <button className="btn btn-primary" onClick={handleExport}>
                    📥 Download CSV Export
                  </button>
                  <button className="btn btn-secondary" onClick={resetUpload}>
                    Upload Another
                  </button>
                </div>
              </div>
            </div>

            {/* Metrics cards */}
            <div className={styles.resultsGrid}>
              <div className={styles.metricCard}>
                <div className={styles.metricValue}>{totalReviews}</div>
                <div className={styles.metricLabel}>Total Reviews</div>
              </div>
              <div className={styles.metricCard}>
                <div className={styles.metricValue} style={{ color: 'var(--positive)' }}>
                  {aggregate.positive ? `${Math.round((aggregate.positive / totalReviews) * 100)}%` : '0%'}
                </div>
                <div className={styles.metricLabel}>Positive Ratio</div>
              </div>
              <div className={styles.metricCard}>
                <div className={styles.metricValue} style={{ color: 'var(--negative)' }}>
                  {aggregate.negative ? `${Math.round((aggregate.negative / totalReviews) * 100)}%` : '0%'}
                </div>
                <div className={styles.metricLabel}>Negative Ratio</div>
              </div>
              <div className={styles.metricCard}>
                <div className={styles.metricValue} style={{ color: 'var(--neutral)' }}>
                  {aggregate.avg_confidence ? `${(aggregate.avg_confidence * 100).toFixed(1)}%` : '0%'}
                </div>
                <div className={styles.metricLabel}>Avg Confidence</div>
              </div>
            </div>

            {/* Charts Row */}
            <div className={styles.chartsRow}>
              <div className={styles.chartCard}>
                <div className={styles.chartTitle}>Overall Sentiment Distribution</div>
                <div className={styles.donutWrap}>
                  <DonutChart distribution={aggregate} />
                </div>
              </div>

              <div className={styles.chartCard}>
                <div className={styles.chartTitle}>Summary Insights</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', justifyContent: 'center', flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: '14px', background: 'var(--bg-glass)', borderRadius: '12px' }}>
                    <div style={{ fontSize: '1.8rem' }}>
                      {aggregate.positive >= aggregate.negative ? '📈' : '📉'}
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.9rem', marginBottom: '2px' }}>Overall Sentiment Health</h4>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        This batch is predominantly <strong>{aggregate.positive >= aggregate.negative ? 'Positive' : 'Negative'}</strong> with {Math.max(aggregate.positive, aggregate.negative)} out of {totalReviews} reviews.
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: '14px', background: 'var(--bg-glass)', borderRadius: '12px' }}>
                    <div style={{ fontSize: '1.8rem' }}>🎯</div>
                    <div>
                      <h4 style={{ fontSize: '0.9rem', marginBottom: '2px' }}>Model Classification Precision</h4>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        The ML pipeline analyzed this batch with an average confidence score of <strong>{(aggregate.avg_confidence * 100).toFixed(1)}%</strong>.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Review Browser Table */}
            {results && results.length > 0 && (
              <div className={styles.tableCard}>
                <div className={styles.tableHeaderRow}>
                  <div className={styles.tableTitle}>📝 Review Browser</div>
                  <div className={styles.tableActions}>
                    <input
                      type="text"
                      className={styles.searchInput}
                      placeholder="Search reviews..."
                      value={searchQuery}
                      onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                    />
                    <select
                      className="input"
                      style={{ padding: '8px 16px', fontSize: '0.85rem', width: 'auto', minWidth: '130px', cursor: 'pointer' }}
                      value={sentimentFilter}
                      onChange={(e) => { setSentimentFilter(e.target.value); setCurrentPage(1); }}
                    >
                      <option value="all">All Sentiments</option>
                      <option value="positive">👍 Positive</option>
                      <option value="negative">👎 Negative</option>
                      <option value="neutral">➖ Neutral</option>
                      <option value="mixed">😐 Mixed</option>
                    </select>
                  </div>
                </div>

                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Review Text</th>
                        <th>Sentiment</th>
                        <th>Confidence</th>
                        <th>Top Emotion</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedResults.map((item, idx) => {
                        const topEmo = getTopEmotion(item.emotion_distribution);
                        const emoIcon = EMOTION_ICONS[topEmo] || '😐';
                        const actualIdx = (currentPage - 1) * itemsPerPage + idx + 1;
                        
                        return (
                          <tr key={idx}>
                            <td>{actualIdx}</td>
                            <td className={styles.reviewTextCol} title={item.input_text}>
                              {item.input_text}
                            </td>
                            <td className={styles.sentimentCol} style={{ color: SENTIMENT_COLORS[item.overall_sentiment] }}>
                              {item.overall_sentiment}
                            </td>
                            <td className={styles.confidenceCol}>
                              {(item.overall_confidence * 100).toFixed(0)}%
                            </td>
                            <td className={styles.emotionCol}>
                              {emoIcon} {topEmo}
                            </td>
                          </tr>
                        );
                      })}
                      {paginatedResults.length === 0 && (
                        <tr>
                          <td colSpan="5" style={{ textAlign: 'center', padding: 'var(--space-xl)', color: 'var(--text-muted)' }}>
                            No reviews found matching the filters.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination footer */}
                {filteredResults.length > 0 && (
                  <div className={styles.pagination}>
                    <div className={styles.pageInfo}>
                      Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, filteredResults.length)} of {filteredResults.length} reviews
                    </div>
                    <div className={styles.pageControls}>
                      <button
                        className={styles.pageBtn}
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </button>
                      <button
                        className={styles.pageBtn}
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
