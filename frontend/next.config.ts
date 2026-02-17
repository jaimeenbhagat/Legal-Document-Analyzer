import type { NextConfig } from "next";

/**
 * Next.js Configuration with API Proxy
 * 
 * Rewrites proxy all /api/* requests to the FastAPI backend.
 * This allows the frontend to call /api/chat instead of http://localhost:8000/chat
 * 
 * Benefits:
 * - Single entry point (port 3000 only)
 * - No CORS issues (same-origin requests)
 * - Cleaner API calls in frontend code
 * - Production-ready (just change BACKEND_URL env var)
 */

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  reactCompiler: true,
  
  async rewrites() {
    return [
      // Proxy all /api/* requests to FastAPI backend
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
