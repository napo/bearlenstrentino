// Shared by every map in the app: caps how far a user can zoom/pan out,
// so the view can't drift away to a scale where the data (all within
// Trentino) stops meaning anything. Bounds as given (SW/NE, lat, lon),
// converted to MapLibre's [west, south, east, north] lng/lat order.
const SW = { lat: 45.305757, lon: 8.327711 };
const NE = { lat: 47.269867, lon: 13.804396 };

export const STUDY_AREA_MAX_BOUNDS: [number, number, number, number] = [
  SW.lon,
  SW.lat,
  NE.lon,
  NE.lat,
];
