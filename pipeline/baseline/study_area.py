"""Milestone 9: study area definition.

Uses the administrative boundary of the Provincia Autonoma di Trento as
published in OpenStreetMap (relation, fetched via the public Nominatim
API) rather than an arbitrary hand-drawn bounding box — a reproducible,
citable, third-party-maintained boundary (see REFERENCES.md, "area di
studio"). Not re-fetched automatically: this is a manual/periodic step,
cached under data/derived/study_area.geojson.

Limitation, disclosed: this is OSM's own administrative boundary, not
the authoritative ISTAT statistical boundary that would be the more
formally "official" choice. It was chosen because it's fetchable through
infrastructure this project already depends on (Nominatim/Overpass),
without adding a shapefile-parsing dependency for a one-time lookup. If
this ever needs to match ISTAT's boundary precisely (e.g. for official
reporting), replace this module's source, not the sampling logic in
sampling.py.
"""
from __future__ import annotations

import requests
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = (
    "BearLensTrentino/0.1 (territorial study area lookup, one-time/periodic; "
    "contact via repository issues)"
)
DEFAULT_QUERY = "Provincia Autonoma di Trento"


def fetch_study_area(
    *, query: str = DEFAULT_QUERY, session: "requests.Session | None" = None
) -> "tuple[BaseGeometry, dict]":
    http = session or requests.Session()
    response = http.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "polygon_geojson": 1, "limit": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        raise ValueError(f"No Nominatim result for query {query!r}")

    result = results[0]
    geometry = shape(result["geojson"])
    metadata = {
        "source": "Nominatim (OpenStreetMap)",
        "osm_type": result["osm_type"],
        "osm_id": result["osm_id"],
        "display_name": result["display_name"],
        "query": query,
    }
    return geometry, metadata
