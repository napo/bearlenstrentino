// Renders the 5 display-category markers as small canvas icons and
// registers them with MapLibre via map.addImage(), so the map's symbol
// layer can pick an icon per feature with a data-driven expression.
//
// Shapes exist so categories are distinguishable even without color
// (colorblind-safety, print, small screens) — see src/data/categories.ts
// for why color alone isn't relied upon here.
import type { Map as MapLibreMap } from "maplibre-gl";
import { CATEGORY_HEX, CATEGORY_STYLES, type CategoryStyle } from "../data/categories";

const SIZE = 34;

function drawShape(ctx: CanvasRenderingContext2D, shape: CategoryStyle["shape"], color: string) {
  const c = SIZE / 2;
  const r = SIZE * 0.3;

  ctx.lineJoin = "round";

  const path = new Path2D();
  switch (shape) {
    case "circle":
    case "circle-outline":
      path.arc(c, c, r, 0, Math.PI * 2);
      break;
    case "diamond":
      path.moveTo(c, c - r);
      path.lineTo(c + r, c);
      path.lineTo(c, c + r);
      path.lineTo(c - r, c);
      path.closePath();
      break;
    case "square": {
      const s = r * 1.5;
      path.rect(c - s / 2, c - s / 2, s, s);
      break;
    }
    case "triangle":
      path.moveTo(c, c - r * 1.2);
      path.lineTo(c + r * 1.05, c + r * 0.7);
      path.lineTo(c - r * 1.05, c + r * 0.7);
      path.closePath();
      break;
  }

  // White halo behind every mark for legibility over hillshaded terrain.
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 4;
  ctx.stroke(path);

  if (shape === "circle-outline") {
    ctx.fillStyle = "#ffffff";
    ctx.fill(path);
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.stroke(path);
  } else {
    ctx.fillStyle = color;
    ctx.fill(path);
  }
}

export function registerCategoryIcons(map: MapLibreMap): void {
  for (const style of Object.values(CATEGORY_STYLES)) {
    const imageId = `marker-${style.id}`;
    if (map.hasImage(imageId)) continue;

    const canvas = document.createElement("canvas");
    canvas.width = SIZE;
    canvas.height = SIZE;
    const ctx = canvas.getContext("2d");
    if (!ctx) continue;

    drawShape(ctx, style.shape, CATEGORY_HEX[style.id]);
    const imageData = ctx.getImageData(0, 0, SIZE, SIZE);
    map.addImage(imageId, { width: SIZE, height: SIZE, data: imageData.data });
  }
}
