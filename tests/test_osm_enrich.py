from __future__ import annotations

import math

import pytest

from pipeline.enrichment.enrich import build_indices, enrich_point
from pipeline.enrichment.osm_source import OsmPoint, OsmWay

ORIGIN_LON, ORIGIN_LAT = 11.0, 46.0

SEARCH_RADII = dict(road_search_radius_m=600, building_search_radius_m=500, settlement_search_radius_m=8000)


def offset(dx_m: float, dy_m: float) -> tuple[float, float]:
    """Local flat-earth approximation, accurate enough at the few-hundred-
    to few-thousand-meter scale used in these tests."""
    dlat = dy_m / 111_320
    dlon = dx_m / (111_320 * math.cos(math.radians(ORIGIN_LAT)))
    return ORIGIN_LON + dlon, ORIGIN_LAT + dlat


def make_road_way(highway_value: str, dx_m: float, length_m: float = 200) -> OsmWay:
    """A straight north-south segment, `dx_m` east of the origin."""
    lon1, lat1 = offset(dx_m, -length_m / 2)
    lon2, lat2 = offset(dx_m, length_m / 2)
    return OsmWay(tags={"highway": highway_value}, coordinates=[(lon1, lat1), (lon2, lat2)])


def make_square_building(cx_m: float, cy_m: float, half_side_m: float = 10) -> OsmWay:
    corners = [
        offset(cx_m - half_side_m, cy_m - half_side_m),
        offset(cx_m + half_side_m, cy_m - half_side_m),
        offset(cx_m + half_side_m, cy_m + half_side_m),
        offset(cx_m - half_side_m, cy_m + half_side_m),
    ]
    corners.append(corners[0])
    return OsmWay(tags={"building": "yes"}, coordinates=corners)


def test_distance_to_major_road():
    road = make_road_way("primary", dx_m=100)
    indices = build_indices(roads=[road], buildings=[], settlements=[], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert fields.distance_to_major_road_m is not None
    assert 90 <= fields.distance_to_major_road_m <= 110


def test_road_categories_are_kept_separate():
    major = make_road_way("primary", dx_m=100)
    track = make_road_way("track", dx_m=50)
    indices = build_indices(roads=[major, track], buildings=[], settlements=[], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert 40 <= fields.distance_to_track_m <= 60
    assert 90 <= fields.distance_to_major_road_m <= 110
    # "any road" only counts vehicular categories (major+minor), not track.
    assert 90 <= fields.distance_to_any_road_m <= 110


def test_distance_beyond_search_radius_is_none_not_guessed():
    far_road = make_road_way("primary", dx_m=5000)
    indices = build_indices(roads=[far_road], buildings=[], settlements=[], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert fields.distance_to_major_road_m is None


def test_road_length_within_buffer_is_clipped_to_the_buffer():
    # Road passes straight through the observation point; within a 250 m
    # radius buffer the clipped chord should equal the buffer diameter.
    long_road = make_road_way("residential", dx_m=0, length_m=2000)
    indices = build_indices(roads=[long_road], buildings=[], settlements=[], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert 480 <= fields.road_length_250m <= 520


def test_building_count_and_area_within_buffer():
    close_building = make_square_building(cx_m=50, cy_m=0, half_side_m=10)  # within 250m and 500m
    farther_building = make_square_building(cx_m=400, cy_m=0, half_side_m=10)  # only within 500m
    indices = build_indices(roads=[], buildings=[close_building, farther_building], settlements=[], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert fields.buildings_250m == 1
    assert fields.buildings_500m == 2
    assert fields.building_area_250m == pytest.approx(400, rel=0.1)  # 20m x 20m square


def test_unclosed_building_way_is_skipped_not_guessed():
    unclosed_way = OsmWay(
        tags={"building": "yes"},
        coordinates=[offset(0, 0), offset(10, 0), offset(10, 10)],
    )
    indices = build_indices(roads=[], buildings=[unclosed_way], settlements=[], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert fields.buildings_250m == 0


def test_nearest_settlement_reports_type_and_name():
    lon, lat = offset(2000, 0)
    settlement = OsmPoint(tags={"place": "village", "name": "Testolago"}, lon=lon, lat=lat)
    indices = build_indices(roads=[], buildings=[], settlements=[settlement], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert fields.nearest_settlement_type == "village"
    assert fields.nearest_settlement_name == "Testolago"
    assert 1900 <= fields.distance_to_settlement_m <= 2100


def test_tourism_features_within_1000m():
    near_lon, near_lat = offset(800, 0)
    far_lon, far_lat = offset(1500, 0)
    poi_near = OsmPoint(tags={"tourism": "viewpoint"}, lon=near_lon, lat=near_lat)
    poi_far = OsmPoint(tags={"tourism": "alpine_hut"}, lon=far_lon, lat=far_lat)
    indices = build_indices(roads=[], buildings=[], settlements=[], tourism=[poi_near, poi_far])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert fields.tourism_features_1000m == 1


def test_no_osm_data_at_all_returns_all_none_or_zero_not_guessed():
    indices = build_indices(roads=[], buildings=[], settlements=[], tourism=[])

    fields = enrich_point(ORIGIN_LON, ORIGIN_LAT, indices, **SEARCH_RADII)

    assert fields.distance_to_major_road_m is None
    assert fields.distance_to_building_m is None
    assert fields.distance_to_settlement_m is None
    assert fields.nearest_settlement_type is None
    assert fields.buildings_250m == 0
    assert fields.tourism_features_1000m == 0
