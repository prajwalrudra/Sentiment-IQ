'use client';

/**
 * SentimentIQ — Login / Signup Page
 *
 * Authentication form using Supabase Auth via the FastAPI backend.
 */

import { useState } from 'react';
import api from '@/lib/api';

export default function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('login'); // 'login' or 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      let data;
      if (mode === 'login') {
        data = await api.login(email, password);
      } else {
        data = await api.signup(email, password);
        if (!data.access_token) {
          setSuccess('Account created! Check your email to confirm, then sign in.');
          setMode('login');
          setLoading(false);
          return;
        }
      }

      if (data.user) {
        onLogin(data.user);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 'calc(100vh - 100px)',
    }}>
      <div className="glass-card" style={{ maxWidth: '420px', width: '100%' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
          <div style={{
            width: '60px',
            height: '60px',
            margin: '0 auto var(--space-md)',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--accent-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem',
            boxShadow: '0 4px 20px rgba(99, 102, 241, 0.3)',
          }}>
            🧠
          </div>
          <h2 className="text-gradient" style={{ marginBottom: '4px' }}>
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {mode === 'login'
              ? 'Sign in to save your analyses'
              : 'Join SentimentIQ to get started'}
          </p>
        </div>

        {/* Toggle */}
        <div style={{
          display: 'flex',
          marginBottom: 'var(--space-xl)',
          background: 'var(--bg-glass)',
          borderRadius: 'var(--radius-md)',
          padding: '4px',
          border: '1px solid var(--border-subtle)',
        }}>
          <button
            className={mode === 'login' ? 'btn btn-primary' : 'btn btn-ghost'}
            onClick={() => { setMode('login'); setError(''); }}
            style={{ flex: 1, borderRadius: 'var(--radius-sm)' }}
          >
            Sign In
          </button>
          <button
            className={mode === 'signup' ? 'btn btn-primary' : 'btn btn-ghost'}
            onClick={() => { setMode('signup'); setError(''); }}
            style={{ flex: 1, borderRadius: 'var(--radius-sm)' }}
          >
            Sign Up
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 'var(--space-md)' }}>
            <label className="label">Email</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div style={{ marginBottom: 'var(--space-xl)' }}>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {error && (
            <div style={{
              marginBottom: 'var(--space-md)',
              padding: '12px',
              background: 'var(--negative-bg)',
              border: '1px solid var(--negative-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--negative)',
              fontSize: '0.85rem',
            }}>
              ⚠️ {error}
            </div>
          )}

          {success && (
            <div style={{
              marginBottom: 'var(--space-md)',
              padding: '12px',
              background: 'var(--positive-bg)',
              border: '1px solid var(--positive-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--positive)',
              fontSize: '0.85rem',
            }}>
              ✅ {success}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            style={{ width: '100%' }}
            disabled={loading}
          >
            {loading ? (
              <><span className="spinner" /> {mode === 'login' ? 'Signing in...' : 'Creating account...'}</>
            ) : (
              mode === 'login' ? '🔐 Sign In' : '🚀 Create Account'
            )}
          </button>
        </form>

        <p style={{
          textAlign: 'center',
          marginTop: 'var(--space-lg)',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
        }}>
          {mode === 'login'
            ? "Don't have an account? Click Sign Up above."
            : 'Already have an account? Click Sign In above.'}
        </p>
      </div>
    </div>
  );
}
