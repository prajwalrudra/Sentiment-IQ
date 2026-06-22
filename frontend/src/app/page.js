'use client';

/**
 * SentimentIQ — Main Application Page
 * 
 * Client-side SPA router that renders the sidebar + active page.
 * Pages: dashboard, analyzer, scraper, history, login
 */

import { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import DashboardPage from './DashboardPage';
import AnalyzerPage from './AnalyzerPage';
import BatchPage from './BatchPage';
import ScraperPage from './ScraperPage';
import HistoryPage from './HistoryPage';
import LoginPage from './LoginPage';
import api from '@/lib/api';

export default function Home() {
  const [activePage, setActivePage] = useState('dashboard');
  const [user, setUser] = useState(null);

  // Restore user from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('sentimentiq_user');
      const savedToken = localStorage.getItem('sentimentiq_token');
      if (savedUser && savedToken) {
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          // Invalid data, clear it
          localStorage.removeItem('sentimentiq_user');
          localStorage.removeItem('sentimentiq_token');
        }
      }
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    if (typeof window !== 'undefined') {
      localStorage.setItem('sentimentiq_user', JSON.stringify(userData));
    }
    setActivePage('dashboard');
  };

  const handleLogout = () => {
    api.logout();
    setUser(null);
    setActivePage('dashboard');
  };

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <DashboardPage onNavigate={setActivePage} />;
      case 'analyzer':
        return <AnalyzerPage />;
      case 'batch':
        return <BatchPage />;
      case 'scraper':
        return <ScraperPage />;
      case 'history':
        return <HistoryPage user={user} />;
      case 'login':
        return <LoginPage onLogin={handleLogin} />;
      default:
        return <DashboardPage onNavigate={setActivePage} />;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        user={user}
        onLogout={handleLogout}
      />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}
