"""Milestone 10: descriptive comparison between observations and the
territorial baseline.

Deliberately simple: percentage-per-bucket comparisons only, no
regression or point-process modeling (see README.md, "Confronti
statistici" — "Evita test statistici complessi nel primo MVP"; a used-
available logistic regression is roadmap item M10b, not this module).

A gap between the observation and baseline distributions here is
consistent with several explanations at once — reporting/observation
bias, or real bear attraction to human-adjacent habitat edges (see
REFERENCES.md: Sıkdokur et al. 2024, Wilson et al. 2005, McFadden-Hiller
et al. 2016) — and this module does not and cannot adjudicate between
them. Say so wherever these numbers are presented.
"""
from __future__ import annotations

from dataclasses import dataclass

# Brief's own example bucketing (0-100m, 100-250m, 250-500m, 500-1000m,
# >1000m). Buckets are half-open on the lower bound: a value exactly at
# an edge (e.g. 100.0) falls into the bucket starting at that edge, not
# the one below it. `unit` is appended to labels as-is (e.g. "m" for
# distances, "" for a unitless brightness proxy) so this module isn't
# hardcoded to distance metrics.
DEFAULT_EDGES_M = (100, 250, 500, 1000)
DEFAULT_UNIT = "m"
UNKNOWN_LABEL = "sconosciuto (oltre il raggio di ricerca)"


def bin_label(
    value: "float | None",
    edges: "tuple[float, ...]" = DEFAULT_EDGES_M,
    *,
    unit: str = DEFAULT_UNIT,
    unknown_label: str = UNKNOWN_LABEL,
) -> str:
    if value is None:
        return unknown_label
    lower = 0
    for edge in edges:
        if value < edge:
            return f"{lower}-{edge:.0f}{unit}"
        lower = edge
    return f">{edges[-1]:.0f}{unit}"


def bin_labels_order(
    edges: "tuple[float, ...]" = DEFAULT_EDGES_M,
    *,
    unit: str = DEFAULT_UNIT,
    unknown_label: str = UNKNOWN_LABEL,
) -> "list[str]":
    labels = []
    lower = 0
    for edge in edges:
        labels.append(f"{lower}-{edge:.0f}{unit}")
        lower = edge
    labels.append(f">{edges[-1]:.0f}{unit}")
    labels.append(unknown_label)
    return labels


@dataclass
class BucketComparison:
    label: str
    observation_count: int
    observation_pct: float
    baseline_count: int
    baseline_pct: float


def compare_distributions(
    observation_values: "list[float | None]",
    baseline_values: "list[float | None]",
    *,
    edges: "tuple[float, ...]" = DEFAULT_EDGES_M,
    unit: str = DEFAULT_UNIT,
    unknown_label: str = UNKNOWN_LABEL,
) -> "list[BucketComparison]":
    labels = bin_labels_order(edges, unit=unit, unknown_label=unknown_label)
    obs_counts = {label: 0 for label in labels}
    base_counts = {label: 0 for label in labels}

    for value in observation_values:
        obs_counts[bin_label(value, edges, unit=unit, unknown_label=unknown_label)] += 1
    for value in baseline_values:
        base_counts[bin_label(value, edges, unit=unit, unknown_label=unknown_label)] += 1

    obs_total = len(observation_values)
    base_total = len(baseline_values)

    return [
        BucketComparison(
            label=label,
            observation_count=obs_counts[label],
            observation_pct=(obs_counts[label] / obs_total * 100) if obs_total else 0.0,
            baseline_count=base_counts[label],
            baseline_pct=(base_counts[label] / base_total * 100) if base_total else 0.0,
        )
        for label in labels
    ]
