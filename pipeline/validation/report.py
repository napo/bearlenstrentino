"""Per-run validation report and plausibility guard (see README.md,
"Validazione dei dati"). A run that would silently collapse the dataset
(e.g. 1000 records -> 10) must fail loudly instead of publishing that.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pipeline.history.reconcile import ChangeLogEntry
from pipeline.normalization.observations import NormalizedObservation

MIN_RETENTION_RATIO = 0.5

_DATE_OK_STATUSES = {"full", "year_month", "day_month_no_year", "year_only"}


class ImplausibleDatasetChangeError(Exception):
    """Raised when the record count drops more than plausible for a
    routine update, so the run can abort instead of publishing silently."""


@dataclass
class ValidationReport:
    fetched_at: str
    number_of_records: int
    records_added: int
    records_removed: int
    records_modified: int
    records_candidate_removed: int
    date_parse_success: int
    date_parse_failed: int
    classification_high: int
    classification_medium: int
    classification_low: int
    classification_unknown: int
    invalid_coordinates: int
    missing_descriptions: int


def build_report(
    observations: "list[NormalizedObservation]",
    changes: "list[ChangeLogEntry]",
    *,
    fetched_at_iso: str,
) -> ValidationReport:
    return ValidationReport(
        fetched_at=fetched_at_iso,
        number_of_records=len(observations),
        records_added=sum(1 for c in changes if c.kind == "added"),
        records_removed=sum(1 for c in changes if c.kind == "removed"),
        records_modified=sum(1 for c in changes if c.kind == "modified"),
        records_candidate_removed=sum(1 for c in changes if c.kind == "candidate_removed"),
        date_parse_success=sum(1 for o in observations if o.date_parse_status in _DATE_OK_STATUSES),
        date_parse_failed=sum(1 for o in observations if o.date_parse_status not in _DATE_OK_STATUSES),
        classification_high=sum(1 for o in observations if o.classification_confidence == "high"),
        classification_medium=sum(1 for o in observations if o.classification_confidence == "medium"),
        classification_low=sum(1 for o in observations if o.classification_confidence == "low"),
        classification_unknown=sum(1 for o in observations if o.classification_confidence == "unknown"),
        invalid_coordinates=sum(1 for o in observations if o.coordinate_error is not None),
        missing_descriptions=sum(1 for o in observations if not o.description_public),
    )


def check_plausibility(previous_count: int, current_count: int) -> None:
    if previous_count == 0:
        return
    if current_count < previous_count * MIN_RETENTION_RATIO:
        raise ImplausibleDatasetChangeError(
            f"Record count dropped from {previous_count} to {current_count} "
            f"(below {MIN_RETENTION_RATIO:.0%} retention) — refusing to publish silently."
        )


def write_report(report: ValidationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
