import { useState } from "react";
import type { ObservationFeature } from "../data/types";
import { ALL_DISPLAY_CATEGORIES, CATEGORY_HEX, CATEGORY_STYLES, toDisplayCategory, type DisplayCategory } from "../data/categories";
import { baseGrid, baseTextStyle, CHART_GRID_COLOR, CHART_MUTED_COLOR } from "./chartTheme";
import { ChartCard } from "./ChartCard";

const MONTH_LABELS_IT = [
  "gen", "feb", "mar", "apr", "mag", "giu",
  "lug", "ago", "set", "ott", "nov", "dic",
];

type Mode = "total" | "by-type";

export interface MonthlyCounts {
  key: string; // "YYYY-MM"
  year: number;
  month: number; // 1-12
  label: string;
  total: number;
  byCategory: Record<DisplayCategory, number>;
}

// Pure data transform, kept separate from the ECharts option so it can be
// unit tested on its own once a frontend test runner exists (there isn't
// one in this project yet — see AGENTS.md notes on scope).
// Uses `event_year`/`event_month` (populated whenever the date parser
// found at least a month — statuses: full, year_month) and
// `toDisplayCategory` — the same category collapse used everywhere else
// on the site (map legend, type breakdown chart) — never a new taxonomy.
export function buildMonthlyCounts(features: ObservationFeature[]): {
  rows: MonthlyCounts[];
  withoutMonth: number;
} {
  const byKey = new Map<string, MonthlyCounts>();
  let withoutMonth = 0;

  for (const f of features) {
    const { event_year: year, event_month: month } = f.properties;
    if (year == null || month == null) {
      withoutMonth += 1;
      continue;
    }
    const key = `${year}-${String(month).padStart(2, "0")}`;
    let row = byKey.get(key);
    if (!row) {
      row = {
        key,
        year,
        month,
        label: `${MONTH_LABELS_IT[month - 1]} ${year}`,
        total: 0,
        byCategory: Object.fromEntries(ALL_DISPLAY_CATEGORIES.map((c) => [c, 0])) as Record<
          DisplayCategory,
          number
        >,
      };
      byKey.set(key, row);
    }
    row.total += 1;
    row.byCategory[toDisplayCategory(f.properties.observation_type)] += 1;
  }

  const rows = [...byKey.values()].sort((a, b) => a.key.localeCompare(b.key));
  return { rows, withoutMonth };
}

// True when the most recent month with any data is the same calendar
// month as today — purely informational (no correction, no projection,
// no estimate of what the final count will be), so a reader doesn't read
// a short bar at the right edge as "signalations are dropping".
function isCurrentMonthIncomplete(rows: MonthlyCounts[]): boolean {
  if (rows.length === 0) return false;
  const last = rows[rows.length - 1];
  const now = new Date();
  return last.year === now.getFullYear() && last.month === now.getMonth() + 1;
}

interface TooltipParam {
  seriesName: string;
  value: number;
  marker: string;
  axisValueLabel: string;
}

export function TimelineChart({ features }: { features: ObservationFeature[] }) {
  const [mode, setMode] = useState<Mode>("total");
  const { rows, withoutMonth } = buildMonthlyCounts(features);
  const currentMonthIncomplete = isCurrentMonthIncomplete(rows);

  const labels = rows.map((r) => r.label);

  const totalSeries = {
    type: "bar" as const,
    name: "Segnalazioni",
    data: rows.map((r) => r.total),
    itemStyle: { color: "#227a55", borderRadius: [4, 4, 0, 0] as [number, number, number, number] },
    barMaxWidth: 36,
  };

  const byCategorySeries = ALL_DISPLAY_CATEGORIES.map((cat) => ({
    type: "bar" as const,
    name: CATEGORY_STYLES[cat].label,
    stack: "total",
    data: rows.map((r) => r.byCategory[cat]),
    itemStyle: { color: CATEGORY_HEX[cat] },
    barMaxWidth: 36,
  }));

  const option = {
    textStyle: baseTextStyle,
    grid: mode === "by-type" ? { ...baseGrid, top: 56 } : baseGrid,
    legend:
      mode === "by-type"
        ? {
            top: 0,
            left: 0,
            textStyle: { color: CHART_MUTED_COLOR, fontSize: 11 },
            data: ALL_DISPLAY_CATEGORIES.map((cat) => CATEGORY_STYLES[cat].label),
          }
        : undefined,
    xAxis: {
      type: "category" as const,
      data: labels,
      axisLine: { lineStyle: { color: CHART_GRID_COLOR } },
      axisLabel: { color: CHART_MUTED_COLOR },
    },
    yAxis: {
      type: "value" as const,
      minInterval: 1,
      splitLine: { lineStyle: { color: CHART_GRID_COLOR } },
      axisLabel: { color: CHART_MUTED_COLOR },
    },
    tooltip:
      mode === "total"
        ? {
            trigger: "item" as const,
            formatter: (params: { name: string; value: number }) =>
              `${params.name}: ${params.value} segnalazion${params.value === 1 ? "e" : "i"}`,
          }
        : {
            trigger: "axis" as const,
            axisPointer: { type: "shadow" as const },
            formatter: (params: TooltipParam[]) => {
              const period = params[0]?.axisValueLabel ?? "";
              const total = params.reduce((sum, p) => sum + (p.value || 0), 0);
              const rowsHtml = params
                .filter((p) => p.value > 0)
                .map((p) => `${p.marker} ${p.seriesName}: ${p.value}`)
                .join("<br/>");
              return `<strong>${period}</strong><br/>Totale: ${total}${rowsHtml ? `<br/>${rowsHtml}` : ""}`;
            },
          },
    series: mode === "total" ? [totalSeries] : byCategorySeries,
  };

  return (
    <>
      <div className="map-controls chart-mode-toggle" role="group" aria-label="Modalità del grafico nel tempo">
        <button type="button" aria-pressed={mode === "total"} onClick={() => setMode("total")}>
          Totale
        </button>
        <button type="button" aria-pressed={mode === "by-type"} onClick={() => setMode("by-type")}>
          Per tipo
        </button>
      </div>
      <ChartCard
        option={option}
        height={mode === "by-type" ? 300 : 260}
        filename={mode === "total" ? "segnalazioni-nel-tempo" : "segnalazioni-nel-tempo-per-tipo"}
        id="chart-timeline"
      >
        {withoutMonth > 0 && (
          <p className="legend-note">
            {withoutMonth} segnalazion{withoutMonth === 1 ? "e" : "i"} senza almeno mese
            e anno utilizzabili nel testo originale non {withoutMonth === 1 ? "è" : "sono"}{" "}
            incluse in questo grafico.
          </p>
        )}
        {currentMonthIncomplete && (
          <p className="legend-note">Mese in corso: il dato è ancora parziale.</p>
        )}
        {mode === "by-type" && (
          <p className="legend-note">
            Due mesi con lo stesso totale possono avere una composizione per tipo molto
            diversa: il totale da solo non lo mostra.
          </p>
        )}
        <p className="chart-links">
          Vedi anche: <a href="#bias-accumulo-temporale">effetto di accumulo nel tempo (bias)</a>.
        </p>
      </ChartCard>
    </>
  );
}
