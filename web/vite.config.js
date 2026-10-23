import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base relativa: o bundle e servido pelo FastAPI (StaticFiles) no .exe.
// proxy no dev: o Vite (:5173) encaminha /api pro uvicorn (:8000).
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "dist",
  },
});
