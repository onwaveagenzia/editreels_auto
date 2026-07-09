/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
  },
  output: 'standalone',
  compress: true,
  images: {
    unoptimized: true,
  },
  rewrites: async () => {
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: process.env.NEXT_PUBLIC_API_URL + '/api/:path*',
        },
      ],
    };
  },
}

module.exports = nextConfig
