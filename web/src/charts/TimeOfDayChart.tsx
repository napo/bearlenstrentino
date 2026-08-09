import type { ObservationFeature } from "../data/types";
import { TIME_OF_DAY_BUCKETS } from "../data/timeOfDay";
import { baseGrid, baseTextStyle, CHART_GRID_COLOR, CHART_MUTED_COLOR } from "./chartTheme";
import { ChartCard } from "./ChartCard";

const NOT_SPECIFIED = "Non specificato";

// Horizontal bar, same reasoning as TypeBreakdownChart: a ranked list of
// counts reads more accurately than a clock-face or pie would, and every
// bar is direct-labeled so color is never load-bearing.
export function TimeOfDayChart({ features }: { features: ObservationFeature[] }) {
  const counts = new Map<string, number>();
  for (const bucket of TIME_OF_DAY_BUCKETS) counts.set(bucket.id, 0);
  counts.set(NOT_SPECIFIED, 0);

  for (const f of features) {
    const { event_hour: hour, time_parse_status: status } = f.properties;
    if (status === "not_present" || hour == null) {
      counts.set(NOT_SPECIFIED, (counts.get(NOT_SPECIFIED) ?? 0) + 1);
      continue;
    }
    const bucket = TIME_OF_DAY_BUCKETS.find((b) => b.hours.includes(hour));
    const key = bucket?.id ?? NOT_SPECIFIED;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const rows = [...TIME_OF_DAY_BUCKETS.map((b) => ({ id: b.id, label: b.label })), { id: NOT_SPECIFIED, label: NOT_SPECIFIED }];
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
      data: rows.map((r) => r.label),
      axisLine: { lineStyle: { color: CHART_GRID_COLOR } },
      axisLabel: { color: CHART_MUTED_COLOR },
      inverse: true,
    },
    tooltip: {
      trigger: "item" as const,
      formatter: (params: { dataIndex: number; value: number }) => {
        const pct = total ? Math.round((params.value / total) * 100) : 0;
        return `${rows[params.dataIndex].label}: ${params.value} (${pct}%)`;
      },
    },
    series: [
      {
        type: "bar" as const,
        data: rows.map((r) => counts.get(r.id) ?? 0),
        itemStyle: {
          color: (p: { dataIndex: number }) => (rows[p.dataIndex].id === NOT_SPECIFIED ? "#9aa39c" : "#227a55"),
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
    <ChartCard option={option} height={260} filename="orario-delle-segnalazioni" id="chart-time-of-day">
      <p className="legend-note">
        L'orario è quello scritto nel testo della segnalazione, quando c'è: "Non
        specificato" raggruppa le segnalazioni che non lo indicano, e non è escluso dal
        grafico proprio per non nasconderlo.
      </p>
      <p className="chart-links">
        Vedi anche: <a href="#bias-osservazione">effetto di osservazione (bias)</a>,{" "}
        <a href="#ref-ditmer-2021">Ditmer et al. 2021</a>.
      </p>
    </ChartCard>
  );
}
