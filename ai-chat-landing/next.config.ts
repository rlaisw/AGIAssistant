import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Dev-server cross-origin allowlist: the host's LAN IP so the app can be
  // used from remote machines (e.g. http://10.161.92.34:3000). Next dev
  // blocks cross-origin HMR/chunk requests otherwise (page loads, nothing
  // interactive works).
  allowedDevOrigins: ["10.161.92.34", "http://10.161.92.34:3000"],
}

export default nextConfig
