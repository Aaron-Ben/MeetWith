import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      // Proxy chat API requests to the backend server (port 6005)
      "/v1": {
        target: "http://127.0.0.1:6005",
        changeOrigin: true,
      },
      // Proxy admin API requests to the backend server (port 6005)
      "/admin_api": {
        target: "http://127.0.0.1:6005",
        changeOrigin: true,
      },
      // Proxy Agent static files to the backend server (port 6005)
      "/Agent": {
        target: "http://127.0.0.1:6005",
        changeOrigin: true,
      },
    },
  },
});