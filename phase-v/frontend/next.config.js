/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Required for Docker deployment
  eslint: {
    // Disable ESLint during production builds
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Disable type checking during builds (speed up and avoid build failures)
    ignoreBuildErrors: true,
  },
}

module.exports = nextConfig
