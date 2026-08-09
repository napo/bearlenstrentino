"""CLI entry point for Milestone 10: observations vs. territorial
baseline, descriptive comparison only (see README.md, "Confronti
statistici" and "Attenzione al denominatore").

OSM-enriches a deterministic SUBSET of the 10,000 baseline points from
Milestone 9 — not all of them. Milestone 8 found that even 57
observation points need a carefully scoped per-point Overpass fetch to
avoid overloading the shared public API; 10,000 points spread across the
whole study area would need a full regional OSM extract instead. Using a
subset here is a disclosed scope reduction (see the manifest's
"known_limitations"), not a silent one.

Usage:
    python scripts/compare_baseline.py [--subset-n 300] [--subset-seed 7]

Requires the "enrichment" extra: pip install -e ".[enrichment]"
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.analysis.compare import compare_distributions  # noqa: E402
from pipeline.enrichment.enrich import build_indices, enrich_point  # noqa: E402
from pipeline.enrichment.osm_source import (  # noqa: E402
    DEFAULT_BUILDING_RADIUS_M,
    DEFAULT_ROAD_RADIUS_M,
    DEFAULT_SETTLEMENT_RADIUS_M,
    DEFAULT_TOURISM_RADIUS_M,
)
from pipeline.enrichment.snapshot import fetch_and_cache_snapshot, load_snapshot  # noqa: E402

METRICS = ["distance_to_any_road_m", "distance_to_building_m", "distance_to_settlement_m"]
# NASA GIBS Black Marble is an 8-bit rendered proxy (0-255), not
# calibrated radiance — see pipeline/enrichment/nightlight.py.
NIGHT_LIGHT_EDGES = (10, 50, 120, 200)

CAVEATS = [
    "Un divario tra segnalazioni e territorio circostante non dimostra che le persone "
    "vedano l'orso solo dove passano: puo' riflettere anche comportamento reale "
    "dell'orso (attrazione verso i margini abitati, specialmente in autunno, quando "
    "cerca di mangiare il piu' possibile prima del letargo) — è quanto suggeriscono "
    "più studi scientifici sul tema (Sikdokur et al. 2024, Wilson et al. 2005, "
    "McFadden-Hiller et al. 2016).",
    "Il confronto e' descrittivo (percentuali per fascia di distanza): non è un test "
    "statistico né un modello predittivo.",
    "Il campione di controllo arricchito qui e' un sottoinsieme di punti scelti a caso "
    "sul territorio, non l'intero campione — vedi 'subset_n' e 'subset_seed' sotto.",
]


def _load_geojson_coords(path: Path) -> "list[tuple[float, float]]":
    data = json.loads(path.read_text(encoding="utf-8"))
    coords = []
    for feature in data["features"]:
        geometry = feature.get("geometry")
        if geometry is not None:
            coords.append(tuple(geometry["coordinates"]))
    return coords


def _csv_header(csv_path: Path) -> "list[str]":
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh))


def _load_observation_metric_values(csv_path: Path, metric: str) -> "list[float | None]":
    values = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = row.get(metric, "")
            values.append(float(raw) if raw not in ("", None) else None)
    return values


def run(args: argparse.Namespace) -> int:
    data_dir: Path = args.data_dir
    derived_dir = data_dir / "derived"
    osm_dir = data_dir / "osm"
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_dir = osm_dir / f"baseline_snapshot-{date_str}"

    baseline_path = derived_dir / "baseline_points.geojson"
    if not baseline_path.exists():
        print("ERROR: no baseline points found; run scripts/generate_baseline.py first.", file=sys.stderr)
        return 1
    all_baseline_coords = _load_geojson_coords(baseline_path)

    rng = random.Random(args.subset_seed)
    subset_coords = rng.sample(all_baseline_coords, min(args.subset_n, len(all_baseline_coords)))

    # Published so the site can show, not just claim, where the "random"
    # comparison points actually fall — including places nobody would
    # expect a bear (see README.md / MethodologySection: a uniform random
    # background can land in implausible terrain, which is exactly the
    # objection a skeptical reader would raise looking at only the bar
    # charts; Phillips et al. 2009 and Steen et al. 2024 discuss this
    # limitation of uniform-random background points directly).
    subset_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {},
            }
            for lon, lat in subset_coords
        ],
    }
    derived_dir.mkdir(parents=True, exist_ok=True)
    (derived_dir / "baseline_subset.geojson").write_text(
        json.dumps(subset_geojson, ensure_ascii=False), encoding="utf-8"
    )

    manifest_path = snapshot_dir / "manifest.json"
    if args.refresh or not manifest_path.exists():
        fetch_and_cache_snapshot(
            subset_coords,
            snapshot_dir,
            road_radius_m=args.road_radius,
            building_radius_m=args.building_radius,
            settlement_radius_m=args.settlement_radius,
            tourism_radius_m=args.tourism_radius,
            extra_manifest_fields={
                "subset_n": len(subset_coords),
                "subset_seed": args.subset_seed,
                "baseline_total_n": len(all_baseline_coords),
            },
        )
    else:
        print(f"Reusing today's baseline OSM snapshot at {snapshot_dir}")

    roads, buildings, settlements, tourism, osm_manifest = load_snapshot(snapshot_dir)
    indices = build_indices(roads, buildings, settlements, tourism)

    baseline_enriched = [
        enrich_point(
            lon,
            lat,
            indices,
            road_search_radius_m=osm_manifest["road_radius_m"],
            building_search_radius_m=osm_manifest["building_radius_m"],
            settlement_search_radius_m=osm_manifest["settlement_radius_m"],
        )
        for lon, lat in subset_coords
    ]

    enriched_obs_path = data_dir / "enriched" / "observations_enriched.csv"
    if not enriched_obs_path.exists():
        print("ERROR: no enriched observations found; run scripts/enrich_osm.py first.", file=sys.stderr)
        return 1

    obs_manifest_path = data_dir / "enriched" / "enrichment_manifest.json"
    obs_manifest = json.loads(obs_manifest_path.read_text(encoding="utf-8")) if obs_manifest_path.exists() else {}

    comparisons = {}
    metrics_meta = {}
    for metric in METRICS:
        observation_values = _load_observation_metric_values(enriched_obs_path, metric)
        baseline_values = [getattr(fields, metric) for fields in baseline_enriched]
        buckets = compare_distributions(observation_values, baseline_values)
        comparisons[metric] = [asdict(b) for b in buckets]
        metrics_meta[metric] = {
            "observation_n": len(observation_values),
            "baseline_n": len(baseline_values),
        }

    # Night light (Milestone 8c) is fetched once as a raster covering the
    # whole extent, not per-point via Overpass, so — unlike the OSM
    # metrics above — it's available for the FULL 10,000-point baseline,
    # not just this run's subset. Optional: only included if
    # scripts/enrich_nightlight.py has already been run.
    baseline_nightlight_path = data_dir / "enriched" / "baseline_nightlight.csv"
    if baseline_nightlight_path.exists() and "night_light_proxy" in _csv_header(enriched_obs_path):
        obs_nightlight = _load_observation_metric_values(enriched_obs_path, "night_light_proxy")
        baseline_nightlight = _load_observation_metric_values(baseline_nightlight_path, "night_light_proxy")
        buckets = compare_distributions(
            obs_nightlight,
            baseline_nightlight,
            edges=NIGHT_LIGHT_EDGES,
            unit="",
            unknown_label="sconosciuto (fuori dal raster)",
        )
        comparisons["night_light_proxy"] = [asdict(b) for b in buckets]
        metrics_meta["night_light_proxy"] = {
            "observation_n": len(obs_nightlight),
            "baseline_n": len(baseline_nightlight),
        }

    caveats = list(CAVEATS)
    if "night_light_proxy" in comparisons:
        caveats.append(
            "La luminosità artificiale notturna è qui un proxy visivo (un'immagine "
            "satellitare NASA, su una scala arbitraria da 0 a 255) e non una misura "
            "fisica calibrata della luce come quella usata in alcuni studi scientifici "
            "(Ditmer et al. 2021). È però calcolata su tutti i punti di controllo, non "
            "solo sul sottoinsieme usato per le altre metriche qui sopra."
        )
    radius_mismatch = {
        key: (obs_manifest.get(key), osm_manifest.get(key))
        for key in ("road_radius_m", "building_radius_m", "settlement_radius_m")
        if obs_manifest.get(key) != osm_manifest.get(key)
    }
    if radius_mismatch:
        details = "; ".join(
            f"{key}: segnalazioni={obs_val}m vs campione di controllo={base_val}m"
            for key, (obs_val, base_val) in radius_mismatch.items()
        )
        caveats.append(
            "I raggi di ricerca usati per segnalazioni e campione di controllo sono "
            f"diversi ({details}), per limiti pratici del servizio pubblico condiviso "
            "usato per interrogare i dati territoriali. Questo significa che la fascia "
            "\"sconosciuto\" NON è direttamente comparabile tra i due gruppi: un "
            "punto di controllo può risultare 'sconosciuto' semplicemente perché "
            "cercato con un raggio più piccolo, non perché sia oggettivamente più "
            "lontano. Confronta con cautela soprattutto quella fascia; le fasce "
            "con distanza nota restano informative."
        )

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subset_n": len(subset_coords),
        "subset_seed": args.subset_seed,
        "baseline_total_n": len(all_baseline_coords),
        "observation_n": len(_load_observation_metric_values(enriched_obs_path, METRICS[0])),
        "osm_snapshot": snapshot_dir.name,
        "search_radii_m": {
            "observations": {
                k: obs_manifest.get(k)
                for k in ("road_radius_m", "building_radius_m", "settlement_radius_m")
            },
            "baseline": {
                k: osm_manifest.get(k)
                for k in ("road_radius_m", "building_radius_m", "settlement_radius_m")
            },
        },
        "metrics": comparisons,
        "metrics_meta": metrics_meta,
        "known_limitations": caveats,
    }

    derived_dir.mkdir(parents=True, exist_ok=True)
    output_path = derived_dir / "comparison.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote comparison for {len(comparisons)} metric(s) -> {output_path}")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    parser.add_argument("--subset-n", type=int, default=300)
    parser.add_argument("--subset-seed", type=int, default=7)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--road-radius", type=float, default=DEFAULT_ROAD_RADIUS_M)
    parser.add_argument("--building-radius", type=float, default=DEFAULT_BUILDING_RADIUS_M)
    parser.add_argument("--settlement-radius", type=float, default=DEFAULT_SETTLEMENT_RADIUS_M)
    parser.add_argument("--tourism-radius", type=float, default=DEFAULT_TOURISM_RADIUS_M)
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
