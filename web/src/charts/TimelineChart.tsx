import type { ObservationFeature } from "../data/types";
import { baseGrid, baseTextStyle, CHART_GRID_COLOR, CHART_MUTED_COLOR } from "./chartTheme";
import { ChartCard } from "./ChartCard";

const MONTH_LABELS_IT = [
  "gen", "feb", "mar", "apr", "mag", "giu",
  "lug", "ago", "set", "ott", "nov", "dic",
];

// Counts observations per month using `event_year` + `event_month`, which
// are populated whenever the date parser found at least a month (statuses:
// full, year_month — see pipeline.normalization.dates). Grouping by month
// rather than by year: the real dataset so far spans a single year, where
// a per-year chart degenerates to one bar and hides the seasonal pattern
// (e.g. spring/summer peaks) that a monthly view can actually show. This
// also scales correctly once multiple years of history accumulate, since
// each bar is labeled with its year.
export function TimelineChart({ features }: { features: ObservationFeature[] }) {
  const counts = new Map<string, number>(); // key: "YYYY-MM"
  let withoutMonth = 0;

  for (const f of features) {
    const { event_year: year, event_month: month } = f.properties;
    if (year == null || month == null) {
      withoutMonth += 1;
      continue;
    }
    const key = `${year}-${String(month).padStart(2, "0")}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const keys = [...counts.keys()].sort();
  const labels = keys.map((key) => {
    const [year, month] = key.split("-");
    return `${MONTH_LABELS_IT[Number(month) - 1]} ${year}`;
  });

  const option = {
    textStyle: baseTextStyle,
    grid: baseGrid,
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
    tooltip: {
      trigger: "item" as const,
      formatter: (params: { name: string; value: number }) =>
        `${params.name}: ${params.value} segnalazion${params.value === 1 ? "e" : "i"}`,
    },
    series: [
      {
        type: "bar" as const,
        data: keys.map((k) => counts.get(k)),
        itemStyle: { color: "#227a55", borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 36,
      },
    ],
  };

  return (
    <ChartCard option={option} height={260} filename="segnalazioni-nel-tempo" id="chart-timeline">
      {withoutMonth > 0 && (
        <p className="legend-note">
          {withoutMonth} segnalazion{withoutMonth === 1 ? "e" : "i"} senza almeno mese
          e anno utilizzabili nel testo originale non {withoutMonth === 1 ? "è" : "sono"}{" "}
          incluse in questo grafico.
        </p>
      )}
      <p className="chart-links">
        Vedi anche: <a href="#bias-accumulo-temporale">effetto di accumulo nel tempo (bias)</a>.
      </p>
    </ChartCard>
  );
}
