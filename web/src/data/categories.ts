// Display-category mapping for the map legend and charts.
//
// pipeline.normalization.classification produces a finer-grained
// `observation_type` (sighting_direct, tracks_or_signs, scat, camera_trap,
// vehicle_collision, predation_evidence, hair, other, unknown) than is
// useful to show as distinct colors on a legend. This module collapses
// that into 5 display categories, chosen to be tellable apart both by
// color AND by shape (never color alone — see AGENTS.md / dataviz skill).
// The full, un-collapsed `observation_type` is still shown in the point
// detail popup, nothing is hidden, only simplified for the legend/chart.
//
// Color values are NOT the literal brand hex codes (Forest/Moss/Slate):
// those three sit too close together in lightness and chroma to be told
// apart reliably as flat color fills, even for full-color vision (see
// `node scripts/validate_palette.js` from the dataviz skill — the brand
// hexes fail the normal-vision-floor check as a categorical set). These
// are a re-saturated variant of the same hue family that passes all
// checks; the original brand hexes remain unchanged everywhere else
// (headers, buttons, panels — see theme.css).
export type DisplayCategory =
  | "sighting"
  | "track"
  | "scat"
  | "other_signs"
  | "uncertain";

export interface CategoryStyle {
  id: DisplayCategory;
  label: string;
  color: string;
  shape: "circle" | "diamond" | "square" | "triangle" | "circle-outline";
}

export const CATEGORY_STYLES: Record<DisplayCategory, CategoryStyle> = {
  sighting: { id: "sighting", label: "Avvistamento diretto", color: "var(--data-sighting)", shape: "circle" },
  track: { id: "track", label: "Impronta / traccia", color: "var(--data-track)", shape: "diamond" },
  scat: { id: "scat", label: "Escrementi", color: "var(--data-scat)", shape: "square" },
  other_signs: { id: "other_signs", label: "Altri segni indiretti", color: "var(--data-other-signs)", shape: "triangle" },
  uncertain: { id: "uncertain", label: "Incerto / non classificato", color: "var(--data-uncertain)", shape: "circle-outline" },
};

export const ALL_DISPLAY_CATEGORIES: DisplayCategory[] = Object.keys(CATEGORY_STYLES) as DisplayCategory[];

// Resolved hex values (mirrors theme.css custom properties) for contexts
// that can't read CSS variables, e.g. MapLibre paint expressions and
// ECharts series, which both need literal color strings.
export const CATEGORY_HEX: Record<DisplayCategory, string> = {
  sighting: "#c08a2e",
  track: "#227a55",
  scat: "#7fa23f",
  other_signs: "#1f6c9c",
  uncertain: "#9aa39c",
};

const TYPE_TO_DISPLAY: Record<string, DisplayCategory> = {
  sighting_direct: "sighting",
  tracks_or_signs: "track",
  scat: "scat",
  hair: "other_signs",
  camera_trap: "other_signs",
  vehicle_collision: "other_signs",
  predation_evidence: "other_signs",
  other: "other_signs",
  unknown: "uncertain",
};

export function toDisplayCategory(observationType: string): DisplayCategory {
  return TYPE_TO_DISPLAY[observationType] ?? "uncertain";
}

// Human-readable Italian labels for the full (un-collapsed) observation
// type, shown in the point detail popup.
export const OBSERVATION_TYPE_LABELS: Record<string, string> = {
  sighting_direct: "Avvistamento diretto",
  tracks_or_signs: "Impronte / tracce",
  scat: "Escrementi",
  hair: "Pelo",
  camera_trap: "Fototrappola",
  vehicle_collision: "Incidente stradale",
  predation_evidence: "Predazione (danno a bestiame)",
  other: "Altro",
  unknown: "Non classificato",
};

export const CLASSIFICATION_METHOD_LABELS: Record<string, string> = {
  source_layer: "indicato dalla fonte originale",
  text_heuristic: "dedotto dal testo",
  unknown: "non determinato",
};

export const CLASSIFICATION_CONFIDENCE_LABELS: Record<string, string> = {
  high: "alta",
  medium: "media",
  low: "bassa",
  unknown: "sconosciuta",
};

export const DATE_STATUS_LABELS: Record<string, string> = {
  full: "data completa",
  range: "intervallo di date",
  ambiguous: "data ambigua (non usata)",
  year_month: "solo mese e anno",
  day_month_no_year: "solo giorno e mese",
  year_only: "solo anno",
  failed: "testo di data non interpretabile",
  not_present: "nessuna data nel testo",
};
