import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import { Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./maplibreSetup";
import type { ObservationFeature } from "../data/types";
import { binPointsIntoHexagons } from "./hexbin";
import { useFullscreenToggle } from "./useFullscreenToggle";

const BASEMAP_STYLE = "https://styles.maptoolkit.org/summer.json";
const INITIAL_CENTER: [number, number] = [11.12, 46.07];
const TIME_WINDOW_DAYS = 30;
const HEX_CELL_SIZE_DEGREES = 0.06;

// Neutral, undifferentiated styling on purpose for "raw" and "time"
// modes: the point of this comparison is the effect of filtering/
// aggregation itself, not a repeat of the categorical evidence-type
// encoding used in the main map (section 4). Keeping color constant
// between "raw" and "time" isolates that one variable.
const POINT_COLOR = "#252a27"; // --color-charcoal
const HEX_COLOR_LIGHT = "#d8e6de";
const HEX_COLOR_DARK = "#1f4a37";

type Mode = "raw" | "time" | "hex";

const MODES: { id: Mode; label: string }[] = [
  { id: "raw", label: "Punti grezzi" },
  { id: "time", label: "Punti filtrati nel tempo" },
  { id: "hex", label: "Esagoni aggregati spazialmente" },
];

function isWithinDays(eventDateIso: string | null, days: number): boolean {
  if (!eventDateIso) return false;
  const eventDate = new Date(eventDateIso);
  if (Number.isNaN(eventDate.getTime())) return false;
  const diffDays = (Date.now() - eventDate.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= days;
}

export function PerceptionMap({ features }: { features: ObservationFeature[] }) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mode, setMode] = useState<Mode>("raw");

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP_STYLE,
      center: INITIAL_CENTER,
      zoom: 8.6,
      pitch: 0,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      map.addSource("perception-points", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "perception-points-layer",
        type: "circle",
        source: "perception-points",
        paint: {
          "circle-radius": 5,
          "circle-color": POINT_COLOR,
          "circle-opacity": 0.75,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addSource("perception-hexagons", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "perception-hexagons-fill",
        type: "fill",
        source: "perception-hexagons",
        paint: {
          "fill-color": [
            "interpolate",
            ["linear"],
            ["get", "count"],
            1,
            HEX_COLOR_LIGHT,
            10,
            HEX_COLOR_DARK,
          ],
          "fill-opacity": 0.85,
        },
      });
      map.addLayer({
        id: "perception-hexagons-outline",
        type: "line",
        source: "perception-hexagons",
        paint: { "line-color": "#ffffff", "line-width": 1 },
      });
      map.addLayer({
        id: "perception-hexagons-label",
        type: "symbol",
        source: "perception-hexagons",
        layout: {
          "text-field": ["to-string", ["get", "count"]],
          "text-size": 12,
        },
        paint: { "text-color": "#252a27" },
      });

      setMapLoaded(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const pointsSource = map.getSource("perception-points") as maplibregl.GeoJSONSource;
    const hexSource = map.getSource("perception-hexagons") as maplibregl.GeoJSONSource;

    const visiblePoints =
      mode === "time"
        ? features.filter((f) => isWithinDays(f.properties.event_date, TIME_WINDOW_DAYS))
        : features;

    map.setLayoutProperty("perception-points-layer", "visibility", mode === "hex" ? "none" : "visible");
    map.setLayoutProperty("perception-hexagons-fill", "visibility", mode === "hex" ? "visible" : "none");
    map.setLayoutProperty("perception-hexagons-outline", "visibility", mode === "hex" ? "visible" : "none");
    map.setLayoutProperty("perception-hexagons-label", "visibility", mode === "hex" ? "visible" : "none");

    if (mode === "hex") {
      const coords = features
        .filter((f) => f.geometry !== null)
        .map((f) => f.geometry!.coordinates);
      const bins = binPointsIntoHexagons(coords, HEX_CELL_SIZE_DEGREES, INITIAL_CENTER[1]);
      hexSource?.setData({
        type: "FeatureCollection",
        features: bins.map((bin) => ({
          type: "Feature",
          geometry: { type: "Polygon", coordinates: [bin.polygon] },
          properties: { count: bin.count },
        })),
      });
    } else {
      pointsSource?.setData({
        type: "FeatureCollection",
        features: visiblePoints
          .filter((f) => f.geometry !== null)
          .map((f) => ({ type: "Feature", geometry: f.geometry!, properties: {} })),
      });
    }
  }, [features, mode, mapLoaded]);

  const total = features.length;
  const timeFiltered = features.filter((f) => isWithinDays(f.properties.event_date, TIME_WINDOW_DAYS)).length;

  const { isFullscreen, toggleFullscreen } = useFullscreenToggle(cardRef, () => {
    mapRef.current?.resize();
  });

  return (
    <div className="map-card" ref={cardRef}>
      <div className="map-controls">
        {MODES.map((m) => (
          <button
            key={m.id}
            type="button"
            aria-pressed={mode === m.id}
            onClick={() => setMode(m.id)}
          >
            {m.label}
          </button>
        ))}
        <button type="button" aria-pressed={isFullscreen} onClick={toggleFullscreen}>
          {isFullscreen ? "Esci da schermo intero" : "Schermo intero"}
        </button>
      </div>
      <div ref={containerRef} className="maplibre-map" />
      <p className="legend-note" style={{ padding: "0.75rem 1rem 1rem" }}>
        {mode === "raw" &&
          `Tutte le ${total} segnalazioni del dataset, sovrapposte senza alcun filtro temporale.`}
        {mode === "time" &&
          `Solo le segnalazioni con data evento negli ultimi ${TIME_WINDOW_DAYS} giorni rispetto a oggi: ${timeFiltered} su ${total}. Stesso dataset, filtro diverso, impressione visiva diversa.`}
        {mode === "hex" &&
          "Le stesse segnalazioni aggregate in celle esagonali di circa 6 km di lato (aggregazione approssimativa, solo a scopo illustrativo). L'aggregazione spaziale può far apparire zone \"calde\" continue anche a partire da pochi punti sparsi: è un effetto della rappresentazione, non necessariamente una prova della realtà sul terreno."}
      </p>
    </div>
  );
}
