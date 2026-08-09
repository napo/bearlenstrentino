"""Milestone 9: uniform random territorial baseline sampling.

Rejection sampling: draw a point uniformly within the study area
polygon's bounding box, keep it only if it actually falls inside the
polygon. This answers "what does a random point in the study area look
like", which is the right baseline for asking whether observations
cluster in more accessible areas than the territory generally offers
(see REFERENCES.md: Kays et al. 2021, Airst & Fleming 2024 validate
uniform-random control points at a similar scale; Steen et al. 2024
finds environmentally-stratified sampling more accurate for
distribution modeling, which is why this is documented as the MVP
choice, not the only one — see the "known limitations" note below).

Deliberately NOT weighted by habitat suitability, accessibility, or
anything else: an unweighted uniform sample is what makes the later
observation-vs-baseline comparison (Milestone 10) interpretable as "is
the territory near observations different from the territory in
general", not "different from where a model already expected animals".
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep


class InsufficientSamplesError(Exception):
    """Raised when rejection sampling can't reach the requested N within
    the attempt budget — surfaces the problem instead of silently
    returning fewer points than asked for."""


@dataclass
class SamplingManifest:
    method: str
    n_requested: int
    n_sampled: int
    seed: int
    crs: str
    attempts: int
    study_area: dict


def sample_points_in_polygon(
    polygon: BaseGeometry,
    n: int,
    *,
    seed: int,
    max_attempts_multiplier: int = 500,
) -> "list[tuple[float, float]]":
    """Returns exactly `n` (lon, lat) points uniformly distributed inside
    `polygon`, using a Mersenne Twister seeded with `seed` for
    reproducibility. Raises InsufficientSamplesError rather than
    returning a short list if the attempt budget is exhausted (e.g. a
    pathologically thin/sliver polygon relative to its bounding box)."""
    rng = random.Random(seed)
    prepared = prep(polygon)
    min_lon, min_lat, max_lon, max_lat = polygon.bounds

    points: "list[tuple[float, float]]" = []
    attempts = 0
    max_attempts = n * max_attempts_multiplier

    while len(points) < n and attempts < max_attempts:
        attempts += 1
        lon = rng.uniform(min_lon, max_lon)
        lat = rng.uniform(min_lat, max_lat)
        candidate = Point(lon, lat)
        if prepared.contains(candidate):
            points.append((lon, lat))

    if len(points) < n:
        raise InsufficientSamplesError(
            f"Only sampled {len(points)}/{n} points after {attempts} attempts "
            f"(budget: {max_attempts}). The polygon may be small/thin relative "
            "to its bounding box, or n/max_attempts_multiplier need adjusting."
        )

    return points
