import type { NextConfig } from "next";

// Where the FastAPI backend runs. The browser only ever calls /api on this
// site's own domain, and Next.js forwards those requests here. Set BACKEND_URL
// in Vercel's project settings; locally it defaults to the uvicorn dev server.
const backendUrl = (process.env.BACKEND_URL ?? "http://localhost:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
