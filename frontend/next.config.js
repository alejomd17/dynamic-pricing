/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Necesario para el Dockerfile multi-stage: genera un servidor Node.js standalone
  output: "standalone",
};

module.exports = nextConfig;
