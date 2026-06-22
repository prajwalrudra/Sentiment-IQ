/**
 * SentimentIQ — API Client
 * 
 * Centralized HTTP client for communicating with the FastAPI backend.
 * Handles auth tokens, error formatting, and request/response processing.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE;
    this.token = null;
  }

  setToken(token) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('sentimentiq_token', token);
    }
  }

  getToken() {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('sentimentiq_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('sentimentiq_token');
      localStorage.removeItem('sentimentiq_user');
    }
  }

  async _request(method, path, body = null, isFormData = false) {
    const headers = {};
    const token = this.getToken();

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      method,
      headers,
    };

    if (body) {
      config.body = isFormData ? body : JSON.stringify(body);
    }

    try {
      const response = await fetch(`${this.baseUrl}${path}`, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Request failed (${response.status})`);
      }

      return data;
    } catch (error) {
      if (error.message === 'Failed to fetch') {
        throw new Error('Cannot connect to the API server. Is the backend running?');
      }
      throw error;
    }
  }

  // ── Health ──────────────────────────────────────────────
  async health() {
    return this._request('GET', '/health');
  }

  // ── Analysis ────────────────────────────────────────────
  async analyze(text, options = {}) {
    return this._request('POST', '/api/analyze', {
      text,
      include_emotions: options.includeEmotions ?? true,
      include_aspects: options.includeAspects ?? true,
    });
  }

  // ── Batch ───────────────────────────────────────────────
  async batchAnalyze(reviews) {
    return this._request('POST', '/api/batch', { reviews });
  }

  async uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this._request('POST', '/api/batch/upload', formData, true);
  }

  async getBatchStatus(jobId) {
    return this._request('GET', `/api/batch/${jobId}`);
  }

  // ── Scraping ────────────────────────────────────────────
  async getPresets() {
    return this._request('GET', '/api/scrape/presets');
  }

  async scrape(url, maxPages = 3, useMock = false) {
    return this._request('POST', '/api/scrape', {
      url,
      max_pages: maxPages,
      use_mock: useMock,
    });
  }

  // ── Stats ───────────────────────────────────────────────
  async getStats() {
    return this._request('GET', '/api/stats');
  }

  // ── History ─────────────────────────────────────────────
  async getHistory(page = 1, limit = 20, filters = {}) {
    const params = new URLSearchParams({ page, limit });
    if (filters.source) params.append('source', filters.source);
    if (filters.sentiment) params.append('sentiment', filters.sentiment);
    return this._request('GET', `/api/history?${params}`);
  }

  async getAnalysisDetail(id) {
    return this._request('GET', `/api/history/${id}`);
  }

  async deleteAnalysis(id) {
    return this._request('DELETE', `/api/history/${id}`);
  }

  // ── Auth ────────────────────────────────────────────────
  async signup(email, password) {
    const data = await this._request('POST', '/api/auth/signup', { email, password });
    if (data.access_token) {
      this.setToken(data.access_token);
      if (typeof window !== 'undefined') {
        localStorage.setItem('sentimentiq_user', JSON.stringify(data.user));
      }
    }
    return data;
  }

  async login(email, password) {
    const data = await this._request('POST', '/api/auth/login', { email, password });
    if (data.access_token) {
      this.setToken(data.access_token);
      if (typeof window !== 'undefined') {
        localStorage.setItem('sentimentiq_user', JSON.stringify(data.user));
      }
    }
    return data;
  }

  async getMe() {
    return this._request('GET', '/api/auth/me');
  }

  logout() {
    this.clearToken();
  }
}

const api = new ApiClient();
export default api;
