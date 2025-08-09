/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@seraaj/ui', '@seraaj/sdk-bff'],
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['@seraaj/ui']
  }
};

module.exports = nextConfig;