"""Fetches OpenStreetMap features from the public Overpass API, for the
Milestone 8 enrichment.

Not run daily: OSM enrichment is a separate, manual/periodic refresh
(README.md, "Strategia OSM"), independent of the daily KML acquisition.

Queries use a single `around:<radius>,lat1,lon1,lat2,lon2,...` filter
built from every observation's coordinates, i.e. the union of small
circles around each point — not one large bounding-box query. A full
bounding-box fetch over the observation extent was tested directly
against the live Overpass API and returned ~130k building ways alone
(Trento's urban core inflates any bbox query); the per-point union is
what keeps this to a fraction of that. Verified live against
overpass-api.de before choosing these radii — see REFERENCES.md /
git history for the numbers.

Radii are deliberately conservative and asymmetric between layers:
buildings and roads are dense enough in Trento's valley floor that even
a 600 m union around 57 points returned 30k+ building ways (~20 MB,
~47 s) — going to the full 1000 m envisioned in the original design
would multiply that further and risks overloading a shared public
service. Settlements and tourism POIs are sparse by comparison, so a
larger radius stays cheap. This is a documented, disclosed scope
reduction for this MVP snapshot, not a silent one (see AGENTS.md,
"documentare le assunzioni GIS") — distance_to_*_m fields are only as
good as the fetch radius: a point genuinely farther than the radius from
any matching feature gets `None`, never a guessed value.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = (
    "BearLensTrentino/0.1 (OSM enrichment, manual/periodic refresh; "
    "contact via repository issues)"
)

# highway=* values, kept as separate categories — never a single
# "highway" bucket (see README.md, "Non trattare genericamente
# highway=* come un'unica categoria").
ROAD_VALUES = [
    "motorway", "trunk", "primary", "secondary",
    "tertiary", "residential", "service", "unclassified",
    "track", "path", "footway",
]
SETTLEMENT_VALUES = ["city", "town", "village", "hamlet", "isolated_dwelling"]
TOURISM_VALUES = ["alpine_hut", "wilderness_hut", "camp_site", "picnic_site", "viewpoint"]

DEFAULT_ROAD_RADIUS_M = 600
DEFAULT_BUILDING_RADIUS_M = 500
DEFAULT_TOURISM_RADIUS_M = 1200
DEFAULT_SETTLEMENT_RADIUS_M = 8000


@dataclass
class OsmWay:
    tags: dict = field(default_factory=dict)
    coordinates: "list[tuple[float, float]]" = field(default_factory=list)  # (lon, lat)


@dataclass
class OsmPoint:
    tags: dict = field(default_factory=dict)
    lon: float = 0.0
    lat: float = 0.0


def _around_clause(coords: "list[tuple[float, float]]", radius_m: float) -> str:
    """coords: list of (lon, lat). Overpass `around` wants lat,lon pairs."""
    pairs = ",".join(f"{lat},{lon}" for lon, lat in coords)
    return f"(around:{radius_m},{pairs})"


def build_way_query(tag: str, values: "list[str]", coords: "list[tuple[float, float]]", radius_m: float) -> str:
    alternation = "|".join(values)
    around = _around_clause(coords, radius_m)
    return f'[out:json][timeout:90];way["{tag}"~"^({alternation})$"]{around};out geom;'


def build_node_query(tag: str, values: "list[str]", coords: "list[tuple[float, float]]", radius_m: float) -> str:
    alternation = "|".join(values)
    around = _around_clause(coords, radius_m)
    return f'[out:json][timeout:90];node["{tag}"~"^({alternation})$"]{around};out;'


def _bbox_clause(coords: "list[tuple[float, float]]", margin_deg: float) -> str:
    lons = [lon for lon, _ in coords]
    lats = [lat for _, lat in coords]
    return (
        f"({min(lats) - margin_deg},{min(lons) - margin_deg},"
        f"{max(lats) + margin_deg},{max(lons) + margin_deg})"
    )


def build_settlement_query(
    tag: str, values: "list[str]", coords: "list[tuple[float, float]]", margin_deg: float
) -> str:
    # Settlements (place=*) are sparse regardless of area, unlike roads
    # and buildings — a single bounding-box query (with a small margin)
    # over the whole observation extent is cheap and far simpler for the
    # server than unioning a large-radius circle around every point
    # (tested live: an 8 km per-point union across 57 points caused a 504
    # Gateway Timeout on the geometry union itself, not on result size).
    alternation = "|".join(values)
    bbox = _bbox_clause(coords, margin_deg)
    return f'[out:json][timeout:90];node["{tag}"~"^({alternation})$"]{bbox};out;'


def build_tourism_query(coords: "list[tuple[float, float]]", radius_m: float) -> str:
    alternation = "|".join(TOURISM_VALUES)
    around = _around_clause(coords, radius_m)
    return (
        f'[out:json][timeout:90];'
        f'(node["tourism"~"^({alternation})$"]{around};'
        f'way["tourism"~"^({alternation})$"]{around};'
        f");out center;"
    )


def parse_ways(elements: "list[dict]") -> "list[OsmWay]":
    ways = []
    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
        ways.append(OsmWay(tags=el.get("tags", {}), coordinates=coords))
    return ways


def parse_nodes(elements: "list[dict]") -> "list[OsmPoint]":
    points = []
    for el in elements:
        if el.get("type") != "node":
            continue
        points.append(OsmPoint(tags=el.get("tags", {}), lon=el["lon"], lat=el["lat"]))
    return points


def parse_tourism_elements(elements: "list[dict]") -> "list[OsmPoint]":
    points = []
    for el in elements:
        if el.get("type") == "node":
            points.append(OsmPoint(tags=el.get("tags", {}), lon=el["lon"], lat=el["lat"]))
        elif el.get("type") == "way" and "center" in el:
            points.append(
                OsmPoint(tags=el.get("tags", {}), lon=el["center"]["lon"], lat=el["center"]["lat"])
            )
    return points


def run_query(
    query: str,
    *,
    session: "requests.Session | None" = None,
    timeout: float = 120.0,
    max_retries: int = 3,
) -> dict:
    """POSTs to the public Overpass API, retrying with backoff on 503/504
    (the shared instance returns these under load rather than queuing
    indefinitely) and 429 (explicit rate limiting — both observed
    directly during this project's own testing). Does not retry on other
    HTTP errors (e.g. 400 for a malformed query), since retrying those
    would just fail the same way three times. A 429 backs off much
    longer than a 503/504: it means the server is deliberately asking
    for a cooldown, not just momentarily busy."""
    http = session or requests.Session()
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = http.post(
                OVERPASS_URL, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=timeout
            )
            if response.status_code == 429 and attempt < max_retries:
                time.sleep(60 * attempt)
                continue
            if response.status_code in (503, 504) and attempt < max_retries:
                time.sleep(10 * attempt)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ReadTimeout as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(10 * attempt)

    raise RuntimeError(
        f"Overpass query failed after {max_retries} attempt(s), last error: {last_error}"
    ) from last_error


def fetch_roads(
    coords: "list[tuple[float, float]]", *, radius_m: float = DEFAULT_ROAD_RADIUS_M, session=None
) -> "list[OsmWay]":
    query = build_way_query("highway", ROAD_VALUES, coords, radius_m)
    return parse_ways(run_query(query, session=session)["elements"])


def build_building_query(coords: "list[tuple[float, float]]", radius_m: float) -> str:
    # `building=*` accepts any truthy value, so this needs a bare
    # existence filter (["building"]), not a regex value alternation.
    around = _around_clause(coords, radius_m)
    return f'[out:json][timeout:90];way["building"]{around};out geom;'


def fetch_buildings(
    coords: "list[tuple[float, float]]", *, radius_m: float = DEFAULT_BUILDING_RADIUS_M, session=None
) -> "list[OsmWay]":
    query = build_building_query(coords, radius_m)
    return parse_ways(run_query(query, session=session)["elements"])


def fetch_settlements(
    coords: "list[tuple[float, float]]", *, radius_m: float = DEFAULT_SETTLEMENT_RADIUS_M, session=None
) -> "list[OsmPoint]":
    # `radius_m` here sizes the bounding-box margin around the whole
    # observation extent (see build_settlement_query), not a per-point
    # circle: every input point ends up with at least `radius_m` of
    # margin beyond it in every direction, which is what makes the later
    # nearest() max_distance_m=radius_m cutoff in enrich_point valid.
    margin_deg = radius_m / 111_320
    query = build_settlement_query("place", SETTLEMENT_VALUES, coords, margin_deg)
    return parse_nodes(run_query(query, session=session)["elements"])


def fetch_tourism(
    coords: "list[tuple[float, float]]", *, radius_m: float = DEFAULT_TOURISM_RADIUS_M, session=None
) -> "list[OsmPoint]":
    query = build_tourism_query(coords, radius_m)
    return parse_tourism_elements(run_query(query, session=session)["elements"])
