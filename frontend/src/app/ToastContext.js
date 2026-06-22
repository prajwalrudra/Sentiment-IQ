'use client';

import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      
      {/* Toast Container */}
      <div
        style={{
          position: 'fixed',
          top: '24px',
          right: '24px',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          pointerEvents: 'none',
        }}
      >
        {toasts.map((toast) => {
          let bgColor = 'rgba(255, 255, 255, 0.08)';
          let textColor = '#ffffff';
          let borderLeftColor = 'var(--border-subtle)';
          let icon = 'ℹ️';

          if (toast.type === 'success') {
            bgColor = 'rgba(16, 185, 129, 0.12)';
            textColor = '#10b981';
            borderLeftColor = '#10b981';
            icon = '✅';
          } else if (toast.type === 'error') {
            bgColor = 'rgba(239, 68, 68, 0.12)';
            textColor = '#f87171';
            borderLeftColor = '#ef4444';
            icon = '⚠️';
          } else if (toast.type === 'info') {
            bgColor = 'rgba(99, 102, 241, 0.12)';
            textColor = '#a5b4fc';
            borderLeftColor = '#6366f1';
            icon = '💡';
          }

          return (
            <div
              key={toast.id}
              onClick={() => removeToast(toast.id)}
              style={{
                pointerEvents: 'auto',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '320px',
                padding: '14px 18px',
                borderRadius: '12px',
                backgroundColor: bgColor,
                color: textColor,
                borderLeft: `4px solid ${borderLeftColor}`,
                borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                borderRight: '1px solid rgba(255, 255, 255, 0.05)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                animation: 'toast-slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
            >
              <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{icon}</span>
              <span style={{ flexGrow: 1, lineHeight: '1.4' }}>{toast.message}</span>
              <button
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'inherit',
                  opacity: 0.5,
                  cursor: 'pointer',
                  fontSize: '0.8rem',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  removeToast(toast.id);
                }}
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>

      <style jsx global>{`
        @keyframes toast-slide-in {
          from {
            transform: translateX(120%) scale(0.9);
            opacity: 0;
          }
          to {
            transform: translateX(0) scale(1);
            opacity: 1;
          }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
