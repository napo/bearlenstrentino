// Copies the pipeline's public output into web/public/data so the
// frontend can fetch it as a static asset. The web app never reads from
// ../data directly and never recomputes anything the pipeline already
// produced (see AGENTS.md, "mantenere frontend e pipeline disaccoppiati").
import { copyFileSync, existsSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, "..", "..");
const targetDir = join(here, "..", "public", "data");
const mediaTargetDir = join(here, "..", "public", "media");

const files = [
  { dir: join(repoRoot, "data", "normalized"), name: "observations.geojson" },
];

mkdirSync(targetDir, { recursive: true });

for (const { dir, name } of files) {
  const src = join(dir, name);
  if (!existsSync(src)) {
    console.warn(`[sync-data] ${src} not found, skipping.`);
    continue;
  }
  copyFileSync(src, join(targetDir, name));
  console.log(`[sync-data] copied ${name}`);
}

// Locally cached photos (see pipeline/acquisition/media.py — the source
// URLs block cross-site embedding, so the popup displays this local
// copy instead).
const mediaSrcDir = join(repoRoot, "data", "media");
if (existsSync(mediaSrcDir)) {
  mkdirSync(mediaTargetDir, { recursive: true });
  const entries = readdirSync(mediaSrcDir);
  for (const entry of entries) {
    copyFileSync(join(mediaSrcDir, entry), join(mediaTargetDir, entry));
  }
  console.log(`[sync-data] copied ${entries.length} media file(s)`);
} else {
  console.warn(`[sync-data] ${mediaSrcDir} not found, skipping.`);
}
