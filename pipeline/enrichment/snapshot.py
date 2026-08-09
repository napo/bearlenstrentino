"""Shared OSM snapshot fetch/cache logic, used by both the observation
enrichment (scripts/enrich_osm.py) and baseline enrichment
(scripts/compare_baseline.py) CLIs — see osm_source.py for why a
per-point radius fetch is used instead of a regional extract.

Caches each category to its own file so a run interrupted partway
(e.g. by a 504 from the shared public Overpass instance, which has
happened during real use of this pipeline) can resume without
re-fetching categories that already succeeded.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from pipeline.enrichment.osm_source import (
    OsmPoint,
    OsmWay,
    fetch_buildings,
    fetch_roads,
    fetch_settlements,
    fetch_tourism,
)

OSM_LICENSE_NOTE = "© OpenStreetMap contributors, ODbL: https://opendatacommons.org/licenses/odbl/"
# Pause between category fetches so a single run doesn't hammer the
# shared public Overpass instance back-to-back.
COURTESY_DELAY_S = 2.0


def fetch_and_cache_snapshot(
    coords: "list[tuple[float, float]]",
    snapshot_dir: Path,
    *,
    road_radius_m: float,
    building_radius_m: float,
    settlement_radius_m: float,
    tourism_radius_m: float,
    extra_manifest_fields: "dict | None" = None,
) -> dict:
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _cached_or_fetch(filename: str, label: str, fetch_fn):
        path = snapshot_dir / filename
        if path.exists():
            print(f"{label}: reusing already-fetched {path.name}.")
            return json.loads(path.read_text(encoding="utf-8"))
        print(label)
        items = fetch_fn()
        payload = [asdict(item) for item in items]
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        time.sleep(COURTESY_DELAY_S)
        return payload

    roads = _cached_or_fetch(
        "roads.json",
        f"Fetching roads (radius {road_radius_m:.0f} m, {len(coords)} points)...",
        lambda: fetch_roads(coords, radius_m=road_radius_m),
    )
    buildings = _cached_or_fetch(
        "buildings.json",
        f"Fetching buildings (radius {building_radius_m:.0f} m)...",
        lambda: fetch_buildings(coords, radius_m=building_radius_m),
    )
    settlements = _cached_or_fetch(
        "settlements.json",
        f"Fetching settlements (bbox margin {settlement_radius_m:.0f} m)...",
        lambda: fetch_settlements(coords, radius_m=settlement_radius_m),
    )
    tourism = _cached_or_fetch(
        "tourism.json",
        f"Fetching tourism features (radius {tourism_radius_m:.0f} m)...",
        lambda: fetch_tourism(coords, radius_m=tourism_radius_m),
    )

    manifest = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Overpass API (overpass-api.de)",
        "license": OSM_LICENSE_NOTE,
        "point_count": len(coords),
        "road_radius_m": road_radius_m,
        "building_radius_m": building_radius_m,
        "settlement_radius_m": settlement_radius_m,
        "tourism_radius_m": tourism_radius_m,
        "note": (
            "Per-point radius union fetch, not a regional bounding-box "
            "extract — see pipeline/enrichment/osm_source.py docstring."
        ),
        "counts": {
            "roads": len(roads),
            "buildings": len(buildings),
            "settlements": len(settlements),
            "tourism": len(tourism),
        },
        **(extra_manifest_fields or {}),
    }
    (snapshot_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Snapshot saved to {snapshot_dir}")
    return manifest


def load_snapshot(snapshot_dir: Path):
    def _load_ways(name: str) -> "list[OsmWay]":
        raw = json.loads((snapshot_dir / name).read_text(encoding="utf-8"))
        return [
            OsmWay(tags=item["tags"], coordinates=[tuple(c) for c in item["coordinates"]])
            for item in raw
        ]

    def _load_points(name: str) -> "list[OsmPoint]":
        raw = json.loads((snapshot_dir / name).read_text(encoding="utf-8"))
        return [OsmPoint(tags=item["tags"], lon=item["lon"], lat=item["lat"]) for item in raw]

    roads = _load_ways("roads.json")
    buildings = _load_ways("buildings.json")
    settlements = _load_points("settlements.json")
    tourism = _load_points("tourism.json")
    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    return roads, buildings, settlements, tourism, manifest
