// Shared ECharts option fragments so all charts read as one system
// (dataviz skill, "mark specs & spacers" / consistent typography).
export const CHART_TEXT_COLOR = "#252a27"; // --color-charcoal
export const CHART_MUTED_COLOR = "#66716d"; // --color-slate
export const CHART_GRID_COLOR = "#e7dec8"; // --color-sand

// `right` leaves room for the direct value/percentage labels drawn past
// the end of horizontal bars (e.g. "39 (68%)") so they never clip against
// the chart-card edge.
export const baseGrid = { left: 8, right: 64, top: 24, bottom: 8, containLabel: true as const };

export const baseTextStyle = {
  fontFamily: "Segoe UI, system-ui, sans-serif",
  color: CHART_TEXT_COLOR,
};
