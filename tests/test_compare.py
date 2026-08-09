from __future__ import annotations

import pytest

from pipeline.analysis.compare import bin_label, compare_distributions

EDGES = (100, 250, 500, 1000)


def test_bin_label_within_first_bucket():
    assert bin_label(50, EDGES) == "0-100m"


def test_bin_label_supports_custom_unit_for_non_distance_metrics():
    brightness_edges = (10, 50, 120, 200)
    assert bin_label(30, brightness_edges, unit="") == "10-50"
    assert bin_label(None, brightness_edges, unit="", unknown_label="fuori raster") == "fuori raster"


def test_bin_label_at_edge_goes_to_upper_bucket():
    assert bin_label(100, EDGES) == "100-250m"


def test_bin_label_beyond_last_edge():
    assert bin_label(1500, EDGES) == ">1000m"


def test_bin_label_none_is_unknown_not_zero():
    assert bin_label(None, EDGES) == "sconosciuto (oltre il raggio di ricerca)"


def test_compare_distributions_percentages_sum_to_100():
    observations = [50, 150, None, 2000]
    baseline = [50, 50, 50, 3000, None, None]

    result = compare_distributions(observations, baseline, edges=EDGES)

    # Percentages come from dividing by bucket counts (e.g. sixths for the
    # 6-item baseline here), which isn't exactly representable in binary
    # floating point — approx, not ==, is the correct check for a sum of
    # such values.
    assert sum(b.observation_pct for b in result) == pytest.approx(100.0)
    assert sum(b.baseline_pct for b in result) == pytest.approx(100.0)


def test_compare_distributions_counts_are_correct_per_bucket():
    observations = [50, 60, 150]
    baseline = [50, 3000]

    result = compare_distributions(observations, baseline, edges=EDGES)
    by_label = {b.label: b for b in result}

    assert by_label["0-100m"].observation_count == 2
    assert by_label["0-100m"].observation_pct == (2 / 3 * 100)
    assert by_label["100-250m"].observation_count == 1
    assert by_label["0-100m"].baseline_count == 1
    assert by_label[">1000m"].baseline_count == 1


def test_compare_distributions_handles_empty_group_without_division_error():
    result = compare_distributions([], [10, 20], edges=EDGES)
    by_label = {b.label: b for b in result}
    assert by_label["0-100m"].observation_pct == 0.0
    assert by_label["0-100m"].observation_count == 0
