import type { NextConfig } from "next";

/**
 * Next.js Configuration with API Proxy
 * 
 * Rewrites proxy all /api/* requests to the FastAPI backend.
 * This allows the frontend to call /api/chat instead of http://localhost:8000/chat
 * 
 * For PRODUCTION:
 * Set NEXT_PUBLIC_BACKEND_URL environment variable in Vercel to your deployed backend URL
 * Example: https://your-backend.onrender.com
 */

// Backend URL - defaults to localhost for development
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  reactCompiler: true,
  
  // Required for external backend connections
  async rewrites() {
    return [
      // Proxy all /api/* requests to FastAPI backend
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },

  // Allow images from backend if needed
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
};

export default nextConfig;
