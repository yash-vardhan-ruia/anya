import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  ...(process.env.IS_DOCKER === "true" ? { output: "standalone" } : {}),
};

export default nextConfig;
