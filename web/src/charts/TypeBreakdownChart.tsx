import type { ObservationFeature } from "../data/types";
import { CATEGORY_HEX, CATEGORY_STYLES, toDisplayCategory } from "../data/categories";
import { baseGrid, baseTextStyle, CHART_GRID_COLOR, CHART_MUTED_COLOR } from "./chartTheme";
import { ChartCard } from "./ChartCard";

// Horizontal bar, not a pie/donut: a ranked list of counts is easier to
// compare accurately than angle/area (dataviz skill, "choosing a form").
// Values are direct-labeled on every bar — required here because two of
// the five category colors fall below the 3:1 contrast-vs-surface
// guideline on a light background (see categories.ts / validator output),
// so color is never the only way to read a value.
export function TypeBreakdownChart({ features }: { features: ObservationFeature[] }) {
  const counts = new Map<string, number>();
  for (const f of features) {
    const cat = toDisplayCategory(f.properties.observation_type);
    counts.set(cat, (counts.get(cat) ?? 0) + 1);
  }

  const categories = Object.values(CATEGORY_STYLES);
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
      data: categories.map((c) => c.label),
      axisLine: { lineStyle: { color: CHART_GRID_COLOR } },
      axisLabel: { color: CHART_MUTED_COLOR },
      inverse: true,
    },
    tooltip: {
      trigger: "item" as const,
      formatter: (params: { dataIndex: number; value: number }) => {
        const pct = total ? Math.round((params.value / total) * 100) : 0;
        return `${categories[params.dataIndex].label}: ${params.value} (${pct}%)`;
      },
    },
    series: [
      {
        type: "bar" as const,
        data: categories.map((c) => counts.get(c.id) ?? 0),
        itemStyle: {
          color: (p: { dataIndex: number }) => CATEGORY_HEX[categories[p.dataIndex].id],
          borderRadius: [0, 4, 4, 0],
        },
        label: {
          show: true,
          position: "right" as const,
          color: "#252a27",
          formatter: (p: { value: number }) =>
            total ? `${p.value} (${Math.round((p.value / total) * 100)}%)` : `${p.value}`,
        },
        barMaxWidth: 28,
      },
    ],
  };

  return (
    <ChartCard option={option} height={220} filename="tipi-di-segnalazione" id="chart-type-breakdown">
      <p className="chart-links">
        Vedi anche: <a href="#bias-eterogeneita-evidenza">tipi di prova diversi tra loro</a>.
      </p>
    </ChartCard>
  );
}
