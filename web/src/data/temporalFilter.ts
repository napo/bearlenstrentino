import type { ObservationFeature } from "./types";

// Milestone 6: temporal exploration. A feature with no usable event_date
// (date_parse_status not "full"/"year_month"/"day_month_no_year"/
// "year_only") is excluded from every window except "all" — never
// guessed into a period it might not belong to (see AGENTS.md).
export type TemporalFilter =
  | { kind: "all" }
  | { kind: "last_days"; days: number }
  | { kind: "year"; year: number }
  | { kind: "custom"; start: string; end: string };

export const PRESETS: { filter: TemporalFilter; label: string }[] = [
  { filter: { kind: "all" }, label: "Intero storico" },
  { filter: { kind: "last_days", days: 30 }, label: "Ultimo mese" },
  { filter: { kind: "last_days", days: 90 }, label: "Ultimi 3 mesi" },
  { filter: { kind: "last_days", days: 365 }, label: "Ultimi 12 mesi" },
];

export function availableYears(features: ObservationFeature[]): number[] {
  const years = new Set<number>();
  for (const f of features) {
    if (f.properties.event_year != null) years.add(f.properties.event_year);
  }
  return [...years].sort((a, b) => b - a);
}

export function applyTemporalFilter(
  features: ObservationFeature[],
  filter: TemporalFilter
): ObservationFeature[] {
  if (filter.kind === "all") return features;

  return features.filter((f) => {
    const iso = f.properties.event_date;
    if (!iso) return false;
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return false;

    switch (filter.kind) {
      case "last_days": {
        const diffDays = (Date.now() - date.getTime()) / (1000 * 60 * 60 * 24);
        return diffDays >= 0 && diffDays <= filter.days;
      }
      case "year":
        return date.getUTCFullYear() === filter.year;
      case "custom": {
        if (!filter.start && !filter.end) return true;
        if (filter.start && date < new Date(filter.start)) return false;
        if (filter.end && date > new Date(filter.end)) return false;
        return true;
      }
      default:
        return true;
    }
  });
}

export function filterLabel(filter: TemporalFilter): string {
  switch (filter.kind) {
    case "all":
      return "intero storico";
    case "last_days":
      return PRESETS.find((p) => p.filter.kind === "last_days" && p.filter.days === filter.days)?.label
        ?? `ultimi ${filter.days} giorni`;
    case "year":
      return `anno ${filter.year}`;
    case "custom":
      if (filter.start && filter.end) return `dal ${filter.start} al ${filter.end}`;
      if (filter.start) return `dal ${filter.start}`;
      if (filter.end) return `fino al ${filter.end}`;
      return "intervallo personalizzato";
  }
}
