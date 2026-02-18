import type { NextConfig } from "next";
import path from "path";

/**
 * Next.js Configuration
 *
 * For Docker deployment: Uses static export (output: 'export')
 * The built files are served by FastAPI from the same container.
 *
 * For Development: Uses rewrites to proxy /api/* to FastAPI backend
 */

// Check if we're building for static export (Docker)
const isStaticExport = process.env.STATIC_EXPORT === "true";

// Backend URL for development proxy
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.BACKEND_URL ||
  "http://localhost:8000";

const nextConfig: NextConfig = {
  // Explicitly set webpack alias so @/ always resolves to frontend root
  webpack(config) {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@": path.resolve(__dirname),
    };
    return config;
  },

  // Static export for Docker deployment
  ...(isStaticExport && {
    output: "export",
    trailingSlash: true,
    images: {
      unoptimized: true,
    },
  }),

  // Development mode: proxy API requests
  ...(!isStaticExport && {
    async rewrites() {
      return [
        {
          source: "/api/:path*",
          destination: `${BACKEND_URL}/:path*`,
        },
      ];
    },
    images: {
      remotePatterns: [
        {
          protocol: "https",
          hostname: "**",
        },
      ],
    },
  }),
};

export default nextConfig;
