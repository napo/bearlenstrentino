import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // maplibre-gl ships a separate worker chunk that Vite's dependency
    // pre-bundling mishandles (404s on maplibre-gl-worker.mjs); excluding
    // it here plus the explicit setWorkerUrl() in src/map/MapView.tsx is
    // the documented workaround.
    exclude: ["maplibre-gl"],
  },
});
