'use client';

import { useState, useEffect, useCallback } from 'react';
import PremiumChatInterface from '../components/PremiumChatInterface';
import { checkHealth, type HealthResponse } from '../lib/api';

// ============================================
// MAIN PAGE COMPONENT - Clean, Compact UI
// ============================================

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  const checkBackendHealth = useCallback(async () => {
    try {
      setIsRetrying(true);
      const status = await checkHealth();
      setHealth(status);
      setHealthError(null);
    } catch {
      setHealthError("Backend not reachable.");
    } finally {
      setIsRetrying(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    
    const doCheck = async () => {
      if (mounted) {
        await checkBackendHealth();
      }
    };
    
    doCheck();
    const interval = setInterval(doCheck, 30000);
    
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [checkBackendHealth]);

  const backendStatus = healthError ? 'offline' : (health ? 'online' : 'checking');

  // Offline State - Minimal Error UI
  if (backendStatus === 'offline') {
    return (
      <div className="h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center max-w-sm w-full">
          <div className="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Backend Offline
          </h2>
          <p className="text-sm text-gray-500 mb-5">
            Start the FastAPI server on port 8000
          </p>
          <div className="bg-gray-900 rounded-lg p-3 mb-5 text-left">
            <code className="text-green-400 text-xs font-mono">$ npm run dev</code>
          </div>
          <button
            onClick={checkBackendHealth}
            disabled={isRetrying}
            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isRetrying ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Connecting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Retry
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  // Main Chat Interface - Full Height, No Header/Footer
  return (
    <div className="h-screen bg-white overflow-hidden">
      <PremiumChatInterface
        health={health}
        onHealthUpdate={setHealth}
        onRequestHealthCheck={checkBackendHealth}
      />
    </div>
  );
}
