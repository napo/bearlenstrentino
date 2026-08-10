"""CLI entry point for Milestones 1-4 (minus the GitHub Actions scheduling
- see README.md): download, validate, redact and log a snapshot of the
source KML, normalize it into observations.csv/.geojson (best-effort
event dates, observation-type classification), reconcile identity against
the previous run's state, and write a validation report.

Usage:
    python scripts/acquire.py [--map-id ID | --url URL] [--data-dir data]

Writes (all under --data-dir, default "data"):
    _local_raw/<date>/source.kml     true raw, gitignored, never publish
    private/name_mapping.csv         PII code lookup, gitignored, never publish
    raw_redacted/<date>/source_redacted.kml   public
    raw_log.jsonl                    public, append-only, no personal data
    normalized/observations.csv      public
    normalized/observations.geojson  public
    media/<hash>.<ext>               public, local cache of source photos
    history/state.json               public, cross-run identity state
    history/changes-<date>.json      public, added/removed/modified log
    history/report-<date>.json       public, validation/plausibility report
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.acquisition.fetch import (  # noqa: E402
    DEFAULT_MAP_ID,
    fetch_raw,
    read_last_hash,
    save_local_raw,
    write_last_hash,
)
from pipeline.acquisition.fingerprint import semantic_fingerprint  # noqa: E402
from pipeline.acquisition.redact_kml import redact_kml_tree, serialize_kml  # noqa: E402
from pipeline.acquisition.validate import InvalidSourceDataError, validate_kml  # noqa: E402
from pipeline.history.reconcile import reconcile  # noqa: E402
from pipeline.history.state import load_state, save_state  # noqa: E402
from pipeline.normalization.export import write_csv, write_geojson  # noqa: E402
from pipeline.normalization.kml_parser import extract_placemarks  # noqa: E402
from pipeline.normalization.observations import normalize_placemarks  # noqa: E402
from pipeline.privacy.redactor import PiiRedactor  # noqa: E402
from pipeline.validation.report import (  # noqa: E402
    ImplausibleDatasetChangeError,
    build_report,
    check_plausibility,
    write_report,
)


def run(args: argparse.Namespace) -> int:
    data_dir: Path = args.data_dir
    local_raw_dir = data_dir / "_local_raw"
    private_dir = data_dir / "private"
    redacted_dir = data_dir / "raw_redacted"
    history_dir = data_dir / "history"
    log_path = data_dir / "raw_log.jsonl"
    # Stores the *semantic* fingerprint (content only), not the raw byte
    # hash - see pipeline.acquisition.fingerprint for why the raw hash
    # can't be used to decide whether anything worth republishing changed.
    state_file = local_raw_dir / "last_fingerprint.txt"
    history_state_path = history_dir / "state.json"

    target = args.url or args.map_id

    try:
        snapshot = fetch_raw(target)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        root = validate_kml(snapshot.content, min_placemarks=args.min_placemarks)
    except InvalidSourceDataError as exc:
        print(f"ERROR: source content failed validation: {exc}", file=sys.stderr)
        return 1

    placemarks = extract_placemarks(root)
    fingerprint = semantic_fingerprint(placemarks)
    changed = read_last_hash(state_file) != fingerprint

    redactor = PiiRedactor(private_dir / "name_mapping.csv")
    observations = normalize_placemarks(
        placemarks, redactor, as_of=snapshot.fetched_at, media_cache_dir=data_dir / "media"
    )

    previous_state = load_state(history_state_path)
    result = reconcile(previous_state, observations, as_of=snapshot.fetched_at)

    try:
        check_plausibility(len(previous_state), len(result.observations))
    except ImplausibleDatasetChangeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Nothing is written until the plausibility gate above has passed -
    # a run that would silently look like data loss aborts before
    # touching any output (see README.md, "Validazione dei dati").
    date_str = snapshot.fetched_at.strftime("%Y-%m-%d")

    save_local_raw(snapshot, local_raw_dir)

    log_entry = {
        "fetched_at": snapshot.fetched_at.isoformat(),
        "raw_sha256": snapshot.sha256,
        "semantic_fingerprint": fingerprint,
        "byte_size": snapshot.byte_size,
        "placemark_count": len(placemarks),
        "changed": changed,
    }

    if changed:
        redacted_root, codes = redact_kml_tree(root, redactor)
        day_dir = redacted_dir / snapshot.fetched_at.strftime("%Y/%m/%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        (day_dir / "source_redacted.kml").write_bytes(serialize_kml(redacted_root))
        log_entry["redaction_codes_introduced_or_reused"] = len(set(codes))
        write_last_hash(state_file, fingerprint)
    else:
        print("Source unchanged since last run; skipping redacted copy.")

    write_csv(result.observations, data_dir / "normalized" / "observations.csv")
    write_geojson(result.observations, data_dir / "normalized" / "observations.geojson")

    redactor.save()

    save_state(history_state_path, result.new_state)
    (history_dir / f"changes-{date_str}.json").write_text(
        json.dumps([asdict(c) for c in result.changes], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = build_report(result.observations, result.changes, fetched_at_iso=snapshot.fetched_at.isoformat())
    write_report(report, history_dir / f"report-{date_str}.json")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    added = sum(1 for c in result.changes if c.kind == "added")
    removed = sum(1 for c in result.changes if c.kind == "removed")
    modified = sum(1 for c in result.changes if c.kind == "modified")
    print(
        f"Fetched {len(placemarks)} placemark(s); changed={changed}; "
        f"added={added} removed={removed} modified={modified}"
    )
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-id", default=DEFAULT_MAP_ID, help="Google My Maps MAP_ID")
    parser.add_argument("--url", default=None, help="Full KML export URL, overrides --map-id")
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    parser.add_argument(
        "--min-placemarks",
        type=int,
        default=1,
        help="Fail validation if fewer Placemark elements are found (plausibility guard)",
    )
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
