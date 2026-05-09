/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',   // For Docker multi-stage build
  
  experimental: {
    // Optimize packages for App Router
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ];
  },

  // Transpile workspace packages
  transpilePackages: [
    '@cognarc/shared-types',
    '@cognarc/design-tokens',
    '@cognarc/auth-client',
    '@cognarc/logger',
  ],
};

module.exports = nextConfig;
