"""CLI entry point for Milestone 8: OpenStreetMap enrichment.

Not run daily - a separate, manual/periodic refresh from the daily KML
acquisition (see README.md, "Strategia OSM"). Fetches roads, buildings,
settlements and tourism features from the public Overpass API within a
radius of every observation (see pipeline/enrichment/osm_source.py for
why a targeted per-point fetch is used instead of one large
bounding-box query - the latter was tested live and returned ~130k
building ways alone), caches the raw response per category under
data/osm/snapshot-<date>/, and writes enriched observations to
data/enriched/.

Usage:
    python scripts/enrich_osm.py [--data-dir data] [--refresh]

Requires the "enrichment" extra: pip install -e ".[enrichment]"
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.enrichment.enrich import build_indices, enrich_point  # noqa: E402
from pipeline.enrichment.osm_source import (  # noqa: E402
    DEFAULT_BUILDING_RADIUS_M,
    DEFAULT_ROAD_RADIUS_M,
    DEFAULT_SETTLEMENT_RADIUS_M,
    DEFAULT_TOURISM_RADIUS_M,
)
from pipeline.enrichment.snapshot import fetch_and_cache_snapshot, load_snapshot  # noqa: E402


def _load_observation_coords(data_dir: Path) -> "list[tuple[float, float]]":
    path = data_dir / "normalized" / "observations.geojson"
    data = json.loads(path.read_text(encoding="utf-8"))
    coords = []
    for feature in data["features"]:
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        lon, lat = geometry["coordinates"]
        coords.append((lon, lat))
    return coords


def _find_latest_snapshot(osm_dir: Path) -> "Path | None":
    if not osm_dir.exists():
        return None
    snapshots = sorted(p for p in osm_dir.iterdir() if p.is_dir() and p.name.startswith("snapshot-"))
    return snapshots[-1] if snapshots else None


def run(args: argparse.Namespace) -> int:
    data_dir: Path = args.data_dir
    osm_dir = data_dir / "osm"
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_dir = osm_dir / f"snapshot-{date_str}"

    coords = _load_observation_coords(data_dir)
    if not coords:
        print(
            "ERROR: no observations with valid coordinates found; run scripts/acquire.py first.",
            file=sys.stderr,
        )
        return 1

    # A manifest is only written after all four categories succeed, so
    # its presence (not just the folder's) is what "today's snapshot is
    # complete" means - otherwise a partially-fetched snapshot (e.g. one
    # category hit a timeout) would be silently treated as done.
    today_manifest = snapshot_dir / "manifest.json"
    if args.refresh or not today_manifest.exists():
        existing = _find_latest_snapshot(osm_dir)
        if not args.refresh and existing is not None and existing != snapshot_dir:
            print(f"No complete snapshot for today yet (latest complete: {existing.name}).")
        fetch_and_cache_snapshot(
            coords,
            snapshot_dir,
            road_radius_m=args.road_radius,
            building_radius_m=args.building_radius,
            settlement_radius_m=args.settlement_radius,
            tourism_radius_m=args.tourism_radius,
        )
    else:
        print(f"Reusing today's complete snapshot at {snapshot_dir}")

    roads, buildings, settlements, tourism, manifest = load_snapshot(snapshot_dir)
    indices = build_indices(roads, buildings, settlements, tourism)

    observations_path = data_dir / "normalized" / "observations.geojson"
    observations = json.loads(observations_path.read_text(encoding="utf-8"))

    enriched_features = []
    for feature in observations["features"]:
        geometry = feature.get("geometry")
        properties = dict(feature["properties"])
        if geometry is not None:
            lon, lat = geometry["coordinates"]
            fields = enrich_point(
                lon,
                lat,
                indices,
                road_search_radius_m=manifest["road_radius_m"],
                building_search_radius_m=manifest["building_radius_m"],
                settlement_search_radius_m=manifest["settlement_radius_m"],
            )
            properties.update(asdict(fields))
        enriched_features.append({"type": "Feature", "geometry": geometry, "properties": properties})

    enriched_dir = data_dir / "enriched"
    enriched_dir.mkdir(parents=True, exist_ok=True)

    geojson_path = enriched_dir / "observations_enriched.geojson"
    geojson_path.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": enriched_features}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )

    csv_path = enriched_dir / "observations_enriched.csv"
    if enriched_features:
        fieldnames = list(enriched_features[0]["properties"].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for feature in enriched_features:
                writer.writerow(feature["properties"])

    (enriched_dir / "enrichment_manifest.json").write_text(
        json.dumps({**manifest, "osm_snapshot": snapshot_dir.name}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Enriched {len(enriched_features)} observation(s) -> {geojson_path}")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    parser.add_argument(
        "--refresh", action="store_true", help="Force a fresh OSM fetch even if today's snapshot exists"
    )
    parser.add_argument("--road-radius", type=float, default=DEFAULT_ROAD_RADIUS_M)
    parser.add_argument("--building-radius", type=float, default=DEFAULT_BUILDING_RADIUS_M)
    parser.add_argument("--settlement-radius", type=float, default=DEFAULT_SETTLEMENT_RADIUS_M)
    parser.add_argument("--tourism-radius", type=float, default=DEFAULT_TOURISM_RADIUS_M)
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
