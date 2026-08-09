from __future__ import annotations

import pytest
from shapely.geometry import LineString, Point, Polygon

from pipeline.baseline.sampling import InsufficientSamplesError, sample_points_in_polygon

SQUARE = Polygon([(11.0, 46.0), (11.1, 46.0), (11.1, 46.1), (11.0, 46.1)])


def test_returns_exactly_n_points():
    points = sample_points_in_polygon(SQUARE, 50, seed=42)
    assert len(points) == 50


def test_all_points_fall_inside_the_polygon():
    points = sample_points_in_polygon(SQUARE, 200, seed=1)
    for lon, lat in points:
        assert SQUARE.contains(Point(lon, lat))


def test_same_seed_is_reproducible():
    a = sample_points_in_polygon(SQUARE, 100, seed=123)
    b = sample_points_in_polygon(SQUARE, 100, seed=123)
    assert a == b


def test_different_seeds_give_different_points():
    a = sample_points_in_polygon(SQUARE, 100, seed=1)
    b = sample_points_in_polygon(SQUARE, 100, seed=2)
    assert a != b


def test_raises_instead_of_returning_a_short_list():
    # A thin diagonal band: its bounding box is the full square, but its
    # actual area is tiny, so uniform samples in the bbox rarely land
    # inside it — this must fail loudly, not silently hand back fewer
    # points than requested.
    sliver = LineString([(11.0, 46.0), (11.1, 46.1)]).buffer(0.0002)
    with pytest.raises(InsufficientSamplesError):
        sample_points_in_polygon(sliver, 500, seed=1, max_attempts_multiplier=2)
