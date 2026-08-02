import { routes, type VercelConfig } from '@vercel/config/v1';

// Resolved at build/deploy time from the per-environment Vercel env var.
// Local (vercel dev / .env.local): http://localhost:8000
// Production: https://xapi.lifestoryagent.uk
const apiUrl = process.env.API_URL ?? 'http://localhost:8000';

export const config: VercelConfig = {
  rewrites: [
    // Proxy API calls to the backend, preserving the /api prefix
    // (the FastAPI routers are mounted under /api).
    routes.rewrite('/api/:path*', `${apiUrl}/api/:path*`),
    // SPA fallback. `rewrites` checks the filesystem first, so real
    // static assets (e.g. /assets/index-*.js/css) are served normally and
    // only non-file paths fall through to index.html.
    routes.rewrite('/(.*)', '/index.html'),
  ],
};
