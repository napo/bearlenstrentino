import type { ObservationFeature } from "../data/types";
import { CLASSIFICATION_METHOD_LABELS } from "../data/categories";
import { baseGrid, baseTextStyle, CHART_GRID_COLOR, CHART_MUTED_COLOR } from "./chartTheme";
import { ChartCard } from "./ChartCard";

// Shows HOW each observation_type was decided — a methodology-transparency
// chart, not a data-content chart. Grey is reused deliberately for
// "unknown" to keep one consistent visual meaning across the whole site
// (see categories.ts): grey always means "we don't know", never a
// decorative choice.
const METHOD_COLOR: Record<string, string> = {
  source_layer: "#227a55",
  text_heuristic: "#1f6c9c",
  unknown: "#9aa39c",
};
const METHOD_ORDER = ["source_layer", "text_heuristic", "unknown"];

export function ClassificationTransparencyChart({ features }: { features: ObservationFeature[] }) {
  const counts = new Map<string, number>();
  for (const f of features) {
    const method = f.properties.classification_method;
    counts.set(method, (counts.get(method) ?? 0) + 1);
  }

  const methods = METHOD_ORDER.filter((m) => counts.has(m));
  const total = features.length;

  const option = {
    textStyle: baseTextStyle,
    grid: baseGrid,
    xAxis: {
      type: "value" as const,
      splitLine: { lineStyle: { color: CHART_GRID_COLOR } },
      axisLabel: { color: CHART_MUTED_COLOR },
    },
    yAxis: {
      type: "category" as const,
      data: methods.map((m) => CLASSIFICATION_METHOD_LABELS[m] ?? m),
      axisLine: { lineStyle: { color: CHART_GRID_COLOR } },
      axisLabel: { color: CHART_MUTED_COLOR },
      inverse: true,
    },
    tooltip: {
      trigger: "item" as const,
      formatter: (params: { dataIndex: number; value: number }) => {
        const pct = total ? Math.round((params.value / total) * 100) : 0;
        return `${CLASSIFICATION_METHOD_LABELS[methods[params.dataIndex]]}: ${params.value} (${pct}%)`;
      },
    },
    series: [
      {
        type: "bar" as const,
        data: methods.map((m) => counts.get(m) ?? 0),
        itemStyle: {
          color: (p: { dataIndex: number }) => METHOD_COLOR[methods[p.dataIndex]],
          borderRadius: [0, 4, 4, 0],
        },
        label: {
          show: true,
          position: "right" as const,
          color: "#252a27",
          formatter: (p: { value: number }) =>
            total ? `${p.value} (${Math.round((p.value / total) * 100)}%)` : `${p.value}`,
        },
        barMaxWidth: 22,
      },
    ],
  };

  return (
    <ChartCard option={option} height={180} filename="come-classifichiamo-le-segnalazioni" id="chart-classification-method">
      <p className="legend-note">
        "Indicato dalla fonte originale" = la cartella in cui era già organizzata la
        segnalazione lo diceva in modo inequivocabile. "Dedotto dal testo" = capito da
        parole chiave nella descrizione. "Non determinato" = non c'erano indizi
        sufficienti in nessuno dei due casi - non indoviniamo mai.
      </p>
      <p className="chart-links">
        Vedi anche: <a href="#bias-eterogeneita-fonte">segnalazioni raccolte in modi diversi</a>,{" "}
        <a href="#bias-eterogeneita-evidenza">tipi di prova diversi tra loro</a>.
      </p>
    </ChartCard>
  );
}
