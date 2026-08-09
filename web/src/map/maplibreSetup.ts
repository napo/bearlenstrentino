// Side-effect-only module: Vite mishandles maplibre-gl's separate worker
// chunk during dependency pre-bundling (404 on maplibre-gl-worker.mjs)
// unless the worker is imported through the `?worker&url` pipeline and
// registered explicitly — see vite.config.ts for the matching
// optimizeDeps.exclude. Import this module (for side effects only)
// before creating any maplibre-gl Map instance.
import { setWorkerUrl } from "maplibre-gl";
import maplibreWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

setWorkerUrl(maplibreWorkerUrl);
