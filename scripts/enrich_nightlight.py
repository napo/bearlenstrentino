"""CLI entry point for Milestone 8c: artificial night light proxy.

Unlike the OSM enrichment (Milestone 8/10), which needs one Overpass
query per point (and hit real scaling/rate-limit walls even at a few
hundred points — see scripts/compare_baseline.py), a single NASA GIBS
WMS request returns a raster covering the *entire* study extent. That
raster is then sampled locally for every point, so this script enriches
ALL observations AND ALL 10,000 baseline points from Milestone 9 in one
fetch — no subsetting needed for this particular covariate.

See pipeline/enrichment/nightlight.py for why this is a documented
approximation (NASA GIBS' rendered Black Marble imagery), not the
calibrated VIIRS radiance used in Ditmer et al. (2021).

Usage:
    python scripts/enrich_nightlight.py [--data-dir data] [--refresh]

Requires the "raster" extra: pip install -e ".[raster]"
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.enrichment.nightlight import (  # noqa: E402
    DEFAULT_LAYER,
    DEFAULT_TIME,
    fetch_night_light_raster,
    sample_brightness,
)

BBOX_MARGIN_DEG = 0.05


def _load_geojson_points(path: Path) -> "list[tuple[str, float, float]]":
    data = json.loads(path.read_text(encoding="utf-8"))
    points = []
    for feature in data["features"]:
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        lon, lat = geometry["coordinates"]
        point_id = feature["properties"].get("id", "")
        points.append((point_id, lon, lat))
    return points


def _compute_bbox(
    all_coords: "list[tuple[float, float]]", margin_deg: float
) -> "tuple[float, float, float, float]":
    lons = [lon for lon, _ in all_coords]
    lats = [lat for _, lat in all_coords]
    return (
        min(lons) - margin_deg,
        min(lats) - margin_deg,
        max(lons) + margin_deg,
        max(lats) + margin_deg,
    )


def run(args: argparse.Namespace) -> int:
    data_dir: Path = args.data_dir

    obs_path = data_dir / "enriched" / "observations_enriched.geojson"
    baseline_path = data_dir / "derived" / "baseline_points.geojson"
    if not obs_path.exists():
        print("ERROR: run scripts/enrich_osm.py first.", file=sys.stderr)
        return 1
    if not baseline_path.exists():
        print("ERROR: run scripts/generate_baseline.py first.", file=sys.stderr)
        return 1

    observations = _load_geojson_points(obs_path)
    baseline = _load_geojson_points(baseline_path)

    bbox = _compute_bbox(
        [(lon, lat) for _, lon, lat in observations] + [(lon, lat) for _, lon, lat in baseline],
        BBOX_MARGIN_DEG,
    )

    snapshot_dir = data_dir / "nightlight" / f"snapshot-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    manifest_path = snapshot_dir / "manifest.json"
    raster_path = snapshot_dir / "night_light.tif"

    if args.refresh or not manifest_path.exists():
        print(f"Fetching night light raster for bbox {bbox}...")
        raster = fetch_night_light_raster(bbox, width=args.width, height=args.height, time=args.time)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        raster.image.save(raster_path, format="TIFF")
        manifest = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "NASA GIBS WMS (gibs.earthdata.nasa.gov)",
            "layer": DEFAULT_LAYER,
            "time": args.time,
            "bbox": bbox,
            "width": args.width,
            "height": args.height,
            "caveat": (
                "Rendered visualization proxy (8-bit RGB), NOT calibrated VIIRS "
                "radiance — see pipeline/enrichment/nightlight.py docstring."
            ),
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Snapshot saved to {snapshot_dir}")
    else:
        print(f"Reusing today's night light snapshot at {snapshot_dir}")
        from PIL import Image

        from pipeline.enrichment.nightlight import NightLightRaster

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        raster = NightLightRaster(image=Image.open(raster_path).convert("RGB"), bbox=tuple(manifest["bbox"]))

    # --- observations: merge the new field into the existing enriched CSV/GeoJSON ---
    obs_brightness = {point_id: sample_brightness(raster, lon, lat) for point_id, lon, lat in observations}

    obs_geojson = json.loads(obs_path.read_text(encoding="utf-8"))
    for feature in obs_geojson["features"]:
        feature["properties"]["night_light_proxy"] = obs_brightness.get(feature["properties"].get("id"))
    obs_path.write_text(json.dumps(obs_geojson, ensure_ascii=False, indent=2), encoding="utf-8")

    obs_csv_path = data_dir / "enriched" / "observations_enriched.csv"
    rows = []
    with obs_csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = [*reader.fieldnames, "night_light_proxy"] if "night_light_proxy" not in (reader.fieldnames or []) else reader.fieldnames
        for row in reader:
            row["night_light_proxy"] = obs_brightness.get(row["id"], "")
            rows.append(row)
    with obs_csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # --- baseline: full 10,000-point sample, own file (not merged into
    # baseline_points.geojson, which is Milestone 9's untouched sampling output) ---
    baseline_dir = data_dir / "enriched"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_csv_path = baseline_dir / "baseline_nightlight.csv"
    with baseline_csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "longitude", "latitude", "night_light_proxy"])
        for point_id, lon, lat in baseline:
            writer.writerow([point_id, lon, lat, sample_brightness(raster, lon, lat)])

    print(
        f"Sampled night light for {len(observations)} observation(s) and "
        f"{len(baseline)} baseline point(s)."
    )
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--time", default=DEFAULT_TIME)
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
