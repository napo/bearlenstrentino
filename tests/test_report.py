from __future__ import annotations

import pytest

from pipeline.history.reconcile import ChangeLogEntry
from pipeline.normalization.observations import NormalizedObservation
from pipeline.validation.report import (
    ImplausibleDatasetChangeError,
    build_report,
    check_plausibility,
)


def _obs(**overrides) -> NormalizedObservation:
    defaults = dict(
        id="obs_1",
        source_layer="Avvistamento a distanza",
        name_public="Bosco Alto",
        description_public="Un orso è stato avvistato.",
        longitude=11.0,
        latitude=46.0,
        coordinate_error=None,
        date_parse_status="full",
        classification_confidence="high",
    )
    defaults.update(overrides)
    return NormalizedObservation(**defaults)


def test_build_report_counts_fields_correctly():
    observations = [
        _obs(id="a", date_parse_status="full", classification_confidence="high"),
        _obs(id="b", date_parse_status="not_present", classification_confidence="unknown"),
        _obs(id="c", coordinate_error="missing coordinates element", description_public=""),
    ]
    changes = [
        ChangeLogEntry(kind="added", id="a"),
        ChangeLogEntry(kind="modified", id="b"),
        ChangeLogEntry(kind="candidate_removed", id="z"),
    ]

    report = build_report(observations, changes, fetched_at_iso="2026-08-01T00:00:00+00:00")

    assert report.number_of_records == 3
    assert report.records_added == 1
    assert report.records_modified == 1
    assert report.records_candidate_removed == 1
    assert report.records_removed == 0
    # "a" and "c" default to date_parse_status="full" (see _obs helper);
    # only "b" is explicitly set to "not_present".
    assert report.date_parse_success == 2
    assert report.date_parse_failed == 1
    # Same default-inheritance note as above: "c" defaults to "high".
    assert report.classification_high == 2
    assert report.classification_unknown == 1
    assert report.invalid_coordinates == 1
    assert report.missing_descriptions == 1


def test_check_plausibility_allows_growth_and_mild_shrinkage():
    check_plausibility(previous_count=100, current_count=150)
    check_plausibility(previous_count=100, current_count=60)


def test_check_plausibility_rejects_a_collapse():
    with pytest.raises(ImplausibleDatasetChangeError):
        check_plausibility(previous_count=1000, current_count=10)


def test_check_plausibility_skips_check_on_first_ever_run():
    check_plausibility(previous_count=0, current_count=1)
