import { useEffect, useRef, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import * as maplibregl from "maplibre-gl";
import { Map as MapLibreMap, Popup, type MapLayerMouseEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./maplibreSetup";
import type { ObservationFeature } from "../data/types";
import { ALL_DISPLAY_CATEGORIES, toDisplayCategory, type DisplayCategory } from "../data/categories";
import { daysSinceEvent } from "../data/useObservations";
import { registerCategoryIcons } from "./markerIcons";
import { PopupContent } from "./PopupContent";
import { Legend } from "../components/Legend";
import { useFullscreenToggle } from "./useFullscreenToggle";

const BASEMAP_STYLE = "https://styles.maptoolkit.org/summer.json";
// Mapterhorn: open global terrain-RGB (terrarium encoding) tiles, see
// https://mapterhorn.com — used for the hillshade + optional 3D relief
// ("vista orografica"), never for statistics. See README.md, "Mappa 3D".
const TERRAIN_TILEJSON_URL = "https://tiles.mapterhorn.com/tilejson.json";

// Study area is not yet formally defined (that's Milestone 9) — this is
// just a reasonable initial map center over Trentino, not a claim about
// the analysis area.
const INITIAL_CENTER: [number, number] = [11.12, 46.07];

const RECENT_OPACITY_FLOOR_DAYS = 3 * 365;

// Clustering config: points within ~50px of each other merge into a
// cluster up to zoom 17 — past that, MapLibre stops trying to split them
// further. If a cluster still exists at zoom 17 its points are for
// practical purposes at the same spot (e.g. the same building/hamlet),
// which is exactly when spiderfying instead of zooming makes sense.
const CLUSTER_MAX_ZOOM = 17;
const CLUSTER_RADIUS = 50;
const SPIDER_LEG_RADIUS_PX = 42;

type Properties = ObservationFeature["properties"];

function toFeatureCollection(features: ObservationFeature[]) {
  return {
    type: "FeatureCollection" as const,
    features: features
      .filter((f) => f.geometry !== null)
      .map((f) => {
        const daysSince = daysSinceEvent(f.properties.event_date);
        return {
          type: "Feature" as const,
          geometry: f.geometry!,
          properties: {
            ...f.properties,
            display_category: toDisplayCategory(f.properties.observation_type),
            // Omitted (not `null`) when unknown, so the MapLibre `has`
            // expression below can tell "no usable date" apart from "0
            // days ago" without relying on a null-literal comparison.
            ...(daysSince !== null ? { days_since_event: daysSince } : {}),
          },
        };
      }),
  };
}

// Arranges `count` points on a small circle around a center pixel,
// spacing the ring out further as more points need to fit on it.
function spiderOffsets(count: number): [number, number][] {
  const radius = count <= 6 ? SPIDER_LEG_RADIUS_PX : SPIDER_LEG_RADIUS_PX + count * 2;
  const offsets: [number, number][] = [];
  for (let i = 0; i < count; i++) {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    offsets.push([Math.cos(angle) * radius, Math.sin(angle) * radius]);
  }
  return offsets;
}

export function MapView({ features }: { features: ObservationFeature[] }) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const popupRootRef = useRef<Root | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [reliefEnabled, setReliefEnabled] = useState(false);
  const [skippedCount, setSkippedCount] = useState(0);
  const [visibleCategories, setVisibleCategories] = useState<Set<DisplayCategory>>(
    () => new Set(ALL_DISPLAY_CATEGORIES)
  );

  // Map lifecycle: created once, independent of `features` (which arrives
  // asynchronously after the initial fetch).
  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP_STYLE,
      center: INITIAL_CENTER,
      zoom: 9,
      pitch: 0,
      bearing: 0,
      maxPitch: 85,
    });
    mapRef.current = map;

    if (import.meta.env.DEV) {
      // Debug-only handle for local inspection/testing; never present in
      // a production build.
      (window as unknown as { __bearlensMap?: MapLibreMap }).__bearlensMap = map;
    }

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");

    function showPopupAt(coordinates: [number, number], properties: Properties, clientY: number) {
      popupRootRef.current?.unmount();
      const container = document.createElement("div");
      const root = createRoot(container);
      popupRootRef.current = root;
      root.render(<PopupContent properties={properties} />);

      // MapLibre's automatic anchor placement measures the popup's DOM
      // size right after setDOMContent, which can race React's commit
      // and pick the wrong side — we've seen it clip against the map
      // container's own `overflow: hidden`. Choosing the anchor
      // ourselves from the click position is deterministic: open
      // downward near the top of the map, upward near the bottom.
      const containerHeight = map.getContainer().clientHeight;
      const anchor = clientY < containerHeight / 2 ? "top" : "bottom";

      const popup = new Popup({ closeButton: true, maxWidth: "480px", anchor })
        .setLngLat(coordinates)
        .setDOMContent(container)
        .addTo(map);

      popup.on("close", () => {
        root.unmount();
        if (popupRootRef.current === root) popupRootRef.current = null;
      });
    }

    function clearSpiderfy() {
      const linesSource = map.getSource("spider-lines") as maplibregl.GeoJSONSource | undefined;
      const pointsSource = map.getSource("spider-points") as maplibregl.GeoJSONSource | undefined;
      linesSource?.setData({ type: "FeatureCollection", features: [] });
      pointsSource?.setData({ type: "FeatureCollection", features: [] });
    }

    async function spiderfyCluster(clusterId: number, center: [number, number]) {
      const source = map.getSource("observations") as maplibregl.GeoJSONSource;
      const leaves = await source.getClusterLeaves(clusterId, Infinity, 0);
      const centerPx = map.project(center);
      const offsets = spiderOffsets(leaves.length);

      const spiderPoints: GeoJSON.Feature[] = [];
      const spiderLines: GeoJSON.Feature[] = [];
      leaves.forEach((leaf, i) => {
        const [dx, dy] = offsets[i];
        const legLngLat = map.unproject([centerPx.x + dx, centerPx.y + dy]);
        spiderPoints.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: [legLngLat.lng, legLngLat.lat] },
          properties: leaf.properties,
        });
        spiderLines.push({
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates: [center, [legLngLat.lng, legLngLat.lat]],
          },
          properties: {},
        });
      });

      (map.getSource("spider-points") as maplibregl.GeoJSONSource)?.setData({
        type: "FeatureCollection",
        features: spiderPoints,
      });
      (map.getSource("spider-lines") as maplibregl.GeoJSONSource)?.setData({
        type: "FeatureCollection",
        features: spiderLines,
      });
    }

    map.on("load", () => {
      map.addSource("terrainSource", {
        type: "raster-dem",
        url: TERRAIN_TILEJSON_URL,
        attribution: '<a href="https://mapterhorn.com" target="_blank" rel="noreferrer">Mapterhorn</a>',
      });
      map.addLayer({
        id: "hillshade",
        type: "hillshade",
        source: "terrainSource",
        paint: { "hillshade-shadow-color": "#473b24" },
      });

      registerCategoryIcons(map);

      map.addSource("observations", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: true,
        clusterRadius: CLUSTER_RADIUS,
        clusterMaxZoom: CLUSTER_MAX_ZOOM,
      });

      map.addLayer({
        id: "clusters-circle",
        type: "circle",
        source: "observations",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": ["step", ["get", "point_count"], "#8fb09d", 10, "#4f8a6c", 50, "#244a3a"],
          "circle-radius": ["step", ["get", "point_count"], 16, 10, 20, 50, 26],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });
      map.addLayer({
        id: "clusters-count",
        type: "symbol",
        source: "observations",
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-font": ["literal", ["Noto Sans Bold"]],
          "text-size": 13,
        },
        paint: { "text-color": "#ffffff" },
      });

      map.addLayer({
        id: "observations-symbols",
        type: "symbol",
        source: "observations",
        filter: ["!", ["has", "point_count"]],
        layout: {
          "icon-image": ["concat", "marker-", ["get", "display_category"]],
          "icon-size": 0.8,
          "icon-allow-overlap": true,
        },
        paint: {
          "icon-opacity": [
            "case",
            ["!", ["has", "days_since_event"]],
            0.55,
            [
              "interpolate",
              ["linear"],
              ["get", "days_since_event"],
              0,
              1,
              RECENT_OPACITY_FLOOR_DAYS,
              0.35,
            ],
          ],
        },
      });

      // Spiderfy layers: same source of truth (the cluster's real leaves)
      // spread onto a small circle so overlapping points at ~the same
      // coordinate become individually clickable instead of hiding
      // behind one cluster forever.
      map.addSource("spider-lines", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "spider-lines",
        type: "line",
        source: "spider-lines",
        paint: { "line-color": "#66716d", "line-width": 1.5, "line-opacity": 0.8 },
      });
      map.addSource("spider-points", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "spider-symbols",
        type: "symbol",
        source: "spider-points",
        layout: {
          "icon-image": ["concat", "marker-", ["get", "display_category"]],
          "icon-size": 0.8,
          "icon-allow-overlap": true,
        },
      });

      for (const layerId of ["clusters-circle", "observations-symbols", "spider-symbols"]) {
        map.on("mouseenter", layerId, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", layerId, () => {
          map.getCanvas().style.cursor = "";
        });
      }

      map.on("click", "clusters-circle", async (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature || feature.geometry.type !== "Point") return;
        const clusterId = feature.properties?.cluster_id as number;
        const center = feature.geometry.coordinates.slice() as [number, number];
        const source = map.getSource("observations") as maplibregl.GeoJSONSource;

        clearSpiderfy();
        const expansionZoom = await source.getClusterExpansionZoom(clusterId);
        if (expansionZoom > map.getZoom() && expansionZoom <= CLUSTER_MAX_ZOOM) {
          map.easeTo({ center, zoom: expansionZoom, duration: 400 });
        } else {
          // Zooming further would not separate these points (they're
          // effectively at the same spot) — spread them out instead.
          spiderfyCluster(clusterId, center);
        }
      });

      map.on("click", "observations-symbols", (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature || feature.geometry.type !== "Point") return;
        clearSpiderfy();
        const coordinates = feature.geometry.coordinates.slice() as [number, number];
        const properties = feature.properties as unknown as Properties;
        showPopupAt(coordinates, properties, e.point.y);
      });

      map.on("click", "spider-symbols", (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature || feature.geometry.type !== "Point") return;
        const coordinates = feature.geometry.coordinates.slice() as [number, number];
        const properties = feature.properties as unknown as Properties;
        showPopupAt(coordinates, properties, e.point.y);
      });

      // A click that hits none of our interactive layers (empty map,
      // basemap features) collapses any open spiderfy — otherwise the
      // spread-out legs would linger forever once you look elsewhere.
      map.on("click", (e: maplibregl.MapMouseEvent) => {
        const hits = map.queryRenderedFeatures(e.point, {
          layers: ["clusters-circle", "observations-symbols", "spider-symbols"],
        });
        if (hits.length === 0) clearSpiderfy();
      });
      map.on("movestart", clearSpiderfy);

      setMapLoaded(true);
    });

    return () => {
      popupRootRef.current?.unmount();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Push observation data into the map once both the map and the fetch
  // are ready, and whenever `features` or the category filter changes.
  // Filtering happens on the *input* data (not via a layer `filter`)
  // because clustering is computed from the source's raw features: a
  // layer-level filter would hide individual points but leave hidden
  // categories still counted inside every cluster bubble.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const visible = features.filter((f) =>
      visibleCategories.has(toDisplayCategory(f.properties.observation_type))
    );
    const allWithCoords = toFeatureCollection(features).features.length;
    const collection = toFeatureCollection(visible);
    setSkippedCount(features.length - allWithCoords);

    const source = map.getSource("observations") as maplibregl.GeoJSONSource | undefined;
    source?.setData(collection);
  }, [features, visibleCategories, mapLoaded]);

  function toggleCategory(category: DisplayCategory) {
    setVisibleCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }

  const { isFullscreen, toggleFullscreen } = useFullscreenToggle(cardRef, () => {
    // The map's canvas is sized from its container at creation time;
    // entering/exiting fullscreen changes that size without firing a
    // window resize event, so MapLibre never notices on its own.
    mapRef.current?.resize();
  });

  function toggleRelief() {
    const map = mapRef.current;
    if (!map) return;
    const next = !reliefEnabled;
    setReliefEnabled(next);
    if (next) {
      map.setTerrain({ source: "terrainSource", exaggeration: 1.2 });
      map.easeTo({ pitch: 60, bearing: -12, duration: 600 });
    } else {
      map.setTerrain(null);
      map.easeTo({ pitch: 0, bearing: 0, duration: 600 });
    }
  }

  return (
    <div className="map-card" ref={cardRef}>
      <div className="map-controls">
        <button type="button" aria-pressed={reliefEnabled} onClick={toggleRelief}>
          {reliefEnabled ? "Vista orografica 3D attiva" : "Vista piatta 2D (clicca per il 3D)"}
        </button>
        <button type="button" aria-pressed={isFullscreen} onClick={toggleFullscreen}>
          {isFullscreen ? "Esci da schermo intero" : "Schermo intero"}
        </button>
      </div>
      <div ref={containerRef} className="maplibre-map" />
      <Legend visible={visibleCategories} onToggle={toggleCategory} />
      <p className="legend-note" style={{ padding: "0 1rem 0.75rem" }}>
        I numeri raggruppano segnalazioni vicine tra loro: clicca per avvicinarti, o per
        separarle se sono già alla massima vicinanza possibile.
        {skippedCount > 0 &&
          ` ${skippedCount} segnalazion${skippedCount === 1 ? "e" : "i"} non mostrat${
            skippedCount === 1 ? "a" : "e"
          } in mappa per coordinate mancanti o non valide (visibili comunque nei dati normalizzati).`}
      </p>
    </div>
  );
}
