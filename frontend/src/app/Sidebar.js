'use client';

/**
 * SentimentIQ — Sidebar Navigation Component
 * 
 * Fixed sidebar with glassmorphism effect, navigation links,
 * and user authentication state display.
 */

import { useState } from 'react';
import styles from './sidebar.module.css';

const NAV_ITEMS = [
  {
    section: 'Analysis',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: '📊' },
      { id: 'analyzer', label: 'Analyzer', icon: '🧠' },
      { id: 'batch', label: 'Batch Analyze', icon: '📦' },
      { id: 'scraper', label: 'Scraper', icon: '🔍' },
    ],
  },
  {
    section: 'Data',
    items: [
      { id: 'history', label: 'History', icon: '📋' },
    ],
  },
];

export default function Sidebar({ activePage, onNavigate, user, onLogout }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNav = (pageId) => {
    onNavigate(pageId);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile toggle */}
      <button
        className={styles.mobileToggle}
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle navigation"
      >
        {mobileOpen ? '✕' : '☰'}
      </button>

      {/* Mobile overlay */}
      <div
        className={`${styles.mobileOverlay} ${mobileOpen ? styles.active : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${mobileOpen ? styles.sidebarOpen : ''}`}>
        {/* Logo */}
        <div className={styles.sidebarLogo}>
          <div className={styles.logoIcon}>🧠</div>
          <div className={styles.logoText}>
            <span className={styles.logoName}>SentimentIQ</span>
            <span className={styles.logoTag}>ML-Powered Analytics</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className={styles.sidebarNav}>
          {NAV_ITEMS.map((section) => (
            <div key={section.section} className={styles.navSection}>
              <div className={styles.navSectionTitle}>{section.section}</div>
              {section.items.map((item) => (
                <button
                  key={item.id}
                  className={`${styles.navItem} ${
                    activePage === item.id ? styles.navItemActive : ''
                  }`}
                  onClick={() => handleNav(item.id)}
                >
                  <span className={styles.navIcon}>{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className={styles.sidebarFooter}>
          {user ? (
            <div className={styles.userInfo}>
              <div className={styles.userAvatar}>
                {user.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className={styles.userDetails}>
                <div className={styles.userName}>{user.email?.split('@')[0]}</div>
                <div className={styles.userEmail}>{user.email}</div>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={onLogout}
                title="Logout"
              >
                🚪
              </button>
            </div>
          ) : (
            <button
              className="btn btn-secondary"
              onClick={() => handleNav('login')}
              style={{ width: '100%' }}
            >
              🔐 Sign In
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
