/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    remotePatterns: [
      // E-commerce sites
      {
        protocol: 'https',
        hostname: '**.zara.com',
      },
      {
        protocol: 'https',
        hostname: '**.hm.com',
      },
      {
        protocol: 'https',
        hostname: '**.h-and-m.com',
      },
      {
        protocol: 'https',
        hostname: '**.amazon.com',
      },
      {
        protocol: 'https',
        hostname: '**.amazon.co.uk',
      },
      {
        protocol: 'https',
        hostname: '**.target.com',
      },
      {
        protocol: 'https',
        hostname: '**.walmart.com',
      },
      {
        protocol: 'https',
        hostname: '**.uniqlo.com',
      },
      {
        protocol: 'https',
        hostname: '**.nike.com',
      },
      {
        protocol: 'https',
        hostname: '**.adidas.com',
      },
      {
        protocol: 'https',
        hostname: '**.gap.com',
      },
      {
        protocol: 'https',
        hostname: '**.oldnavy.com',
      },
      {
        protocol: 'https',
        hostname: '**.macys.com',
      },
      {
        protocol: 'https',
        hostname: '**.nordstrom.com',
      },
      {
        protocol: 'https',
        hostname: '**.forever21.com',
      },
      {
        protocol: 'https',
        hostname: '**.express.com',
      },
      {
        protocol: 'https',
        hostname: '**.asos.com',
      },
      {
        protocol: 'https',
        hostname: '**.boohoo.com',
      },
      {
        protocol: 'https',
        hostname: '**.prettylittlething.com',
      },
      // Shopify stores
      {
        protocol: 'https',
        hostname: '**.myshopify.com',
      },
      {
        protocol: 'https',
        hostname: '**.shopifycdn.com',
      },
      {
        protocol: 'https',
        hostname: 'cdn.shopify.com',
      },
      // CDN services
      {
        protocol: 'https',
        hostname: '**.cloudinary.com',
      },
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: '**.cloudfront.net',
      },
      {
        protocol: 'https',
        hostname: '**.imgix.net',
      },
      // Generic catch-all for other stores (be more specific in production)
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
    // Optimize images for better performance
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
}

module.exports = nextConfig 