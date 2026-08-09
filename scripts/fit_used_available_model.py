"""CLI entry point for Milestone 10b: exploratory used-available
logistic regression.

ROADMAP / ADVANCED, NOT MVP — see pipeline/analysis/logistic.py and
REFERENCES.md (M10b). This script's output is written to
data/derived/used_available_model.json for transparency and future
review, but is deliberately NOT surfaced as a headline result on the
site: a regression coefficient does not resolve whether a covariate
association reflects observation bias or real bear habitat selection
any more than Milestone 10's descriptive comparison does, and this
model has not had independent methodological review.

Only `night_light_proxy` is used as a covariate here, not the OSM
distance metrics from Milestone 10: night light is the only covariate
computed identically (same raster, no search-radius cutoff) for
observations AND the full 10,000-point baseline, so it's free of the
search-radius mismatch documented in comparison.json. Extending this to
a multi-covariate model requires first resolving that mismatch (e.g. via
a proper offline OSM extract instead of per-point Overpass queries).

Usage:
    python scripts/fit_used_available_model.py

Requires the "analysis" extra: pip install -e ".[analysis]"
"""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.analysis.logistic import fit_used_available_logistic  # noqa: E402

FEATURE = "night_light_proxy"

INTERPRETIVE_CAVEATS = [
    "Questo modello e' esplorativo (Milestone 10b), non validato per pubblicazione: "
    "richiede revisione metodologica indipendente — vedi REFERENCES.md.",
    "Un'associazione tra night_light_proxy e 'essere una segnalazione' non distingue "
    "un bias di osservazione da una reale selezione dell'habitat da parte dell'orso "
    "(vedi Sikdokur et al. 2024, Wilson et al. 2005, McFadden-Hiller et al. 2016).",
    "night_light_proxy e' un proxy visivo NASA GIBS (0-255), non radianza VIIRS "
    "calibrata — vedi pipeline/enrichment/nightlight.py.",
    "Il coefficiente e' per deviazione standard del covariata standardizzato, non "
    "per unita' grezza.",
    "Un solo covariato: non e' un modello multivariato used-available completo "
    "(gli altri covariati OSM hanno raggi di ricerca disomogenei tra segnalazioni "
    "e baseline — vedi comparison.json — e non sono inclusi qui per questo motivo).",
]


def _load_metric_values(csv_path: Path, metric: str) -> "list[float | None]":
    values = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = row.get(metric, "")
            values.append(float(raw) if raw not in ("", None, "None") else None)
    return values


def run(args) -> int:
    data_dir: Path = args.data_dir
    obs_path = data_dir / "enriched" / "observations_enriched.csv"
    baseline_path = data_dir / "enriched" / "baseline_nightlight.csv"

    if not obs_path.exists():
        print("ERROR: run scripts/enrich_osm.py and scripts/enrich_nightlight.py first.", file=sys.stderr)
        return 1
    if not baseline_path.exists():
        print("ERROR: run scripts/enrich_nightlight.py first.", file=sys.stderr)
        return 1

    used = [[v] for v in _load_metric_values(obs_path, FEATURE)]
    available = [[v] for v in _load_metric_values(baseline_path, FEATURE)]

    result = fit_used_available_logistic(used, available, [FEATURE])

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "used_available_logistic_regression_univariate",
        "feature": FEATURE,
        **asdict(result),
        "interpretive_caveats": INTERPRETIVE_CAVEATS,
    }

    derived_dir = data_dir / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    output_path = derived_dir / "used_available_model.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"n_used={result.n_used} n_available={result.n_available} converged={result.converged}")
    print(f"Wrote {output_path}")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
