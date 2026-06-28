import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Redirige les appels /api vers le backend FastAPI en dev.
      "/api": "http://localhost:8000",
    },
  },
});
