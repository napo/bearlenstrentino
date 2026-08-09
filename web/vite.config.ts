import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // Served from https://napo.github.io/bearlenstrentino/ (a project page,
  // not a napo.github.io root repo) — every asset path Vite generates
  // needs this prefix, or they'd 404 one level up from where Pages
  // actually serves them. Code that fetches its own data (useObservations,
  // PopupContent, Header's logo) already reads import.meta.env.BASE_URL
  // rather than hardcoding "/", so this is the only place it needs setting.
  base: "/bearlenstrentino/",
  plugins: [react()],
  optimizeDeps: {
    // maplibre-gl ships a separate worker chunk that Vite's dependency
    // pre-bundling mishandles (404s on maplibre-gl-worker.mjs); excluding
    // it here plus the explicit setWorkerUrl() in src/map/MapView.tsx is
    // the documented workaround.
    exclude: ["maplibre-gl"],
  },
});
