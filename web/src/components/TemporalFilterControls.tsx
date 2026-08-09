import { useState } from "react";
import type { ObservationFeature } from "../data/types";
import { availableYears, PRESETS, type TemporalFilter } from "../data/temporalFilter";

function isSameFilter(a: TemporalFilter, b: TemporalFilter): boolean {
  if (a.kind !== b.kind) return false;
  if (a.kind === "last_days" && b.kind === "last_days") return a.days === b.days;
  if (a.kind === "year" && b.kind === "year") return a.year === b.year;
  return a.kind === "all";
}

export function TemporalFilterControls({
  features,
  filter,
  onChange,
}: {
  features: ObservationFeature[];
  filter: TemporalFilter;
  onChange: (filter: TemporalFilter) => void;
}) {
  const years = availableYears(features);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  return (
    <div className="temporal-filter">
      <div className="map-controls" style={{ flexWrap: "wrap", borderRadius: "10px" }}>
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            aria-pressed={isSameFilter(filter, p.filter)}
            onClick={() => onChange(p.filter)}
          >
            {p.label}
          </button>
        ))}
        {years.map((year) => (
          <button
            key={year}
            type="button"
            aria-pressed={filter.kind === "year" && filter.year === year}
            onClick={() => onChange({ kind: "year", year })}
          >
            {year}
          </button>
        ))}
      </div>
      <div className="temporal-filter-custom">
        <label>
          Da
          <input
            type="date"
            value={customStart}
            onChange={(e) => {
              setCustomStart(e.target.value);
              onChange({ kind: "custom", start: e.target.value, end: customEnd });
            }}
          />
        </label>
        <label>
          A
          <input
            type="date"
            value={customEnd}
            onChange={(e) => {
              setCustomEnd(e.target.value);
              onChange({ kind: "custom", start: customStart, end: e.target.value });
            }}
          />
        </label>
        {filter.kind === "custom" && (
          <span className="legend-note">intervallo personalizzato attivo</span>
        )}
      </div>
    </div>
  );
}
