import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import { Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./maplibreSetup";
import type { ObservationFeature } from "../data/types";
import { binPointsIntoHexagons } from "./hexbin";
import { STUDY_AREA_MAX_BOUNDS } from "./mapBounds";

const BASEMAP_STYLE = "https://styles.maptoolkit.org/summer.json";
const INITIAL_CENTER: [number, number] = [11.12, 46.07];
const TIME_WINDOW_DAYS = 30;
// Deliberately NOT 0.06 (~6 km di lato): quella è la dimensione della
// griglia esagonale ufficiale della Provincia di Trento (uso statistico
// territoriale), e riusarla qui rischiava di far credere che questa
// aggregazione illustrativa fosse in qualche modo legata a quella griglia.
const HEX_CELL_SIZE_DEGREES = 0.03;

// Neutral, undifferentiated styling on purpose for "raw" and "time"
// modes: the point of this comparison is the effect of filtering/
// aggregation itself, not a repeat of the categorical evidence-type
// encoding used in the main map (section 4). Keeping color constant
// between "raw" and "time" isolates that one variable.
const POINT_COLOR = "#252a27"; // --color-charcoal
const HEX_COLOR_LIGHT = "#d8e6de";
const HEX_COLOR_DARK = "#1f4a37";
// Fixed pixel radius used in "cluster-fixed" — deliberately constant
// regardless of count, to demonstrate the bias. "cluster-proportional"
// instead scales radius by sqrt(count) (radius ∝ sqrt(value), no
// additive offset) so the circle's *area* is proportional to the count,
// the standard proportional-symbol convention. The multiplier (8, see
// below) is tuned to this dataset's actual count range (mostly 1-6): it
// keeps a count of 1 visible on its own while still landing noticeably
// smaller than CLUSTER_FIXED_RADIUS, and a count of 6 noticeably larger.
const CLUSTER_FIXED_RADIUS = 16;
const CLUSTER_PROPORTIONAL_RADIUS_SCALE = 8;

type Mode = "raw" | "time" | "hex" | "cluster-fixed" | "cluster-proportional";

const MODES: { id: Mode; label: string }[] = [
  { id: "raw", label: "Punti grezzi" },
  { id: "time", label: "Punti filtrati nel tempo" },
  { id: "hex", label: "Esagoni aggregati spazialmente" },
  { id: "cluster-fixed", label: "Cluster a dimensione fissa" },
  { id: "cluster-proportional", label: "Simboli proporzionali al conteggio" },
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
      maxBounds: STUDY_AREA_MAX_BOUNDS,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(new maplibregl.FullscreenControl({ container: cardRef.current ?? undefined }), "top-right");

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

      map.addSource("perception-clusters", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "perception-clusters-fill",
        type: "circle",
        source: "perception-clusters",
        paint: {
          // Constant color in both cluster modes, unlike the hex layer's
          // count-based color scale: the only variable that should change
          // between "cluster-fixed" and "cluster-proportional" is the
          // radius, otherwise color would leak the magnitude that the
          // fixed-radius mode is meant to hide.
          "circle-color": HEX_COLOR_DARK,
          "circle-radius": CLUSTER_FIXED_RADIUS,
          "circle-opacity": 0.85,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#ffffff",
        },
      });
      map.addLayer({
        id: "perception-clusters-label",
        type: "symbol",
        source: "perception-clusters",
        layout: {
          "text-field": ["to-string", ["get", "count"]],
          "text-size": 12,
        },
        paint: {
          "text-color": "#ffffff",
          "text-halo-color": "#1f4a37",
          "text-halo-width": 1,
        },
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
    const clusterSource = map.getSource("perception-clusters") as maplibregl.GeoJSONSource;

    const visiblePoints =
      mode === "time"
        ? features.filter((f) => isWithinDays(f.properties.event_date, TIME_WINDOW_DAYS))
        : features;

    const isCluster = mode === "cluster-fixed" || mode === "cluster-proportional";

    map.setLayoutProperty(
      "perception-points-layer",
      "visibility",
      mode === "raw" || mode === "time" ? "visible" : "none"
    );
    map.setLayoutProperty("perception-hexagons-fill", "visibility", mode === "hex" ? "visible" : "none");
    map.setLayoutProperty("perception-hexagons-outline", "visibility", mode === "hex" ? "visible" : "none");
    map.setLayoutProperty("perception-hexagons-label", "visibility", mode === "hex" ? "visible" : "none");
    map.setLayoutProperty("perception-clusters-fill", "visibility", isCluster ? "visible" : "none");
    map.setLayoutProperty("perception-clusters-label", "visibility", isCluster ? "visible" : "none");

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
    } else if (isCluster) {
      const coords = features
        .filter((f) => f.geometry !== null)
        .map((f) => f.geometry!.coordinates);
      const bins = binPointsIntoHexagons(coords, HEX_CELL_SIZE_DEGREES, INITIAL_CENTER[1]);
      map.setPaintProperty(
        "perception-clusters-fill",
        "circle-radius",
        mode === "cluster-fixed"
          ? CLUSTER_FIXED_RADIUS
          : ["*", CLUSTER_PROPORTIONAL_RADIUS_SCALE, ["sqrt", ["get", "count"]]]
      );
      clusterSource?.setData({
        type: "FeatureCollection",
        features: bins.map((bin) => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: bin.centroid },
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
      </div>
      <div ref={containerRef} className="maplibre-map" />
      <p className="legend-note" style={{ padding: "0.75rem 1rem 1rem" }}>
        {mode === "raw" &&
          `Tutte le ${total} segnalazioni del dataset, sovrapposte senza alcun filtro temporale.`}
        {mode === "time" &&
          `Solo le segnalazioni con data evento negli ultimi ${TIME_WINDOW_DAYS} giorni rispetto a oggi: ${timeFiltered} su ${total}. Stesso dataset, filtro diverso, impressione visiva diversa.`}
        {mode === "hex" &&
          "Le stesse segnalazioni aggregate in celle esagonali di circa 3 km di lato (dimensione arbitraria, scelta solo per illustrare l'effetto — non è la griglia esagonale ufficiale della Provincia di Trento, che ha lato di 6 km). L'aggregazione spaziale può far apparire zone \"calde\" continue anche a partire da pochi punti sparsi: è un effetto della rappresentazione, non necessariamente una prova della realtà sul terreno."}
        {mode === "cluster-fixed" &&
          "Le stesse celle della modalità precedente, ma disegnate come cerchi tutti della stessa dimensione: la differenza fra una cella con poche segnalazioni e una con molte si vede solo leggendo il numero, non dalla dimensione del simbolo. È un errore cartografico comune (il conteggio reale è nel numero, ma l'occhio legge prima la dimensione) che fa sembrare uniforme ciò che non lo è."}
        {mode === "cluster-proportional" &&
          "Le stesse celle, questa volta con l'area del cerchio proporzionale al numero di segnalazioni (simboli proporzionali). Qui la dimensione comunica davvero la grandezza, senza dover leggere il numero — il confronto con la modalità precedente mostra quanto la sola scelta della dimensione del simbolo possa cambiare l'impressione."}
      </p>
    </div>
  );
}
