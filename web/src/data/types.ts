// Mirrors the properties written by pipeline/normalization/export.py into
// data/normalized/observations.geojson. Keep in sync with that module —
// this is a read-only view of pipeline output, never recomputed here (see
// AGENTS.md, "mantenere frontend e pipeline disaccoppiati").
export interface ObservationProperties {
  id: string;
  source_layer: string | null;
  name_public: string | null;
  description_public: string | null;
  coordinate_error: string | null;
  media_links: string[];
  media_local: (string | null)[];
  redaction_applied: boolean;
  redaction_codes: string[];
  first_seen_at: string | null;
  last_seen_at: string | null;
  source_changed_at: string | null;
  event_date: string | null;
  event_year: number | null;
  event_month: number | null;
  event_day: number | null;
  date_text_raw: string | null;
  date_parse_status: string;
  event_hour: number | null;
  event_minute: number | null;
  time_text_raw: string | null;
  time_parse_status: string;
  observation_type: string;
  classification_method: string;
  classification_confidence: string;
}

export interface ObservationFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] } | null;
  properties: ObservationProperties;
}

export interface ObservationCollection {
  type: "FeatureCollection";
  features: ObservationFeature[];
}
