"""CLI entry point for Milestone 9: territorial baseline generation.

Fetches (or reuses a cached) study area polygon - the administrative
boundary of the Provincia Autonoma di Trento, see
pipeline/baseline/study_area.py - and samples N uniform random control
points within it, writing:

    data/derived/study_area.geojson
    data/derived/baseline_points.geojson
    data/derived/baseline_manifest.json

N defaults to 10,000 per the project brief. Note this is the sampling
step only: OSM-enriching all 10,000 points (Milestone 10) will need its
own, separately documented scope decision - Milestone 8 already found
that even 57 points require a carefully scoped Overpass fetch strategy,
and 10,000 points spread across the whole study area amounts to needing
a full regional OSM extract rather than per-point queries.

Usage:
    python scripts/generate_baseline.py [--n 10000] [--seed 42] [--refresh-study-area]

Requires the "enrichment" extra: pip install -e ".[enrichment]"
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.baseline.sampling import SamplingManifest, sample_points_in_polygon  # noqa: E402
from pipeline.baseline.study_area import fetch_study_area  # noqa: E402
from shapely.geometry import mapping, shape  # noqa: E402

DEFAULT_N = 10_000
DEFAULT_SEED = 42  # arbitrary, fixed for reproducibility - see README.md


def _load_or_fetch_study_area(derived_dir: Path, *, refresh: bool):
    path = derived_dir / "study_area.geojson"
    if path.exists() and not refresh:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return shape(payload["geometry"]), payload["properties"]

    print("Fetching study area boundary from Nominatim (Provincia Autonoma di Trento)...")
    geometry, metadata = fetch_study_area()
    derived_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "Feature",
        "geometry": mapping(geometry),
        "properties": {**metadata, "fetched_at": datetime.now(timezone.utc).isoformat()},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Study area saved to {path}")
    return geometry, payload["properties"]


def run(args: argparse.Namespace) -> int:
    derived_dir: Path = args.data_dir / "derived"

    polygon, study_area_metadata = _load_or_fetch_study_area(derived_dir, refresh=args.refresh_study_area)

    print(f"Sampling {args.n} points (seed={args.seed})...")
    points = sample_points_in_polygon(polygon, args.n, seed=args.seed)

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"id": f"baseline_{i:05d}"},
        }
        for i, (lon, lat) in enumerate(points, start=1)
    ]
    points_path = derived_dir / "baseline_points.geojson"
    points_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest = SamplingManifest(
        method="uniform_random_rejection_sampling",
        n_requested=args.n,
        n_sampled=len(points),
        seed=args.seed,
        crs="EPSG:4326",
        attempts=-1,  # not tracked at this level; see pipeline.baseline.sampling for the algorithm
        study_area=study_area_metadata,
    )
    manifest_dict = asdict(manifest)
    manifest_dict["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest_dict["known_limitations"] = [
        "Uniform random sampling, not environmentally or accessibility-stratified "
        "(see REFERENCES.md, Steen et al. 2024 / Whitford et al. 2024 for alternatives).",
        "Study area is OSM's administrative boundary via Nominatim, not the "
        "authoritative ISTAT statistical boundary (see pipeline/baseline/study_area.py).",
        "OSM enrichment of these points (Milestone 10) is expected to operate on a "
        "documented subset, not all 10,000, due to Overpass scaling limits found in Milestone 8.",
    ]
    (derived_dir / "baseline_manifest.json").write_text(
        json.dumps(manifest_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Sampled {len(points)} baseline point(s) -> {points_path}")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--refresh-study-area", action="store_true", help="Re-fetch the study area boundary even if cached"
    )
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
