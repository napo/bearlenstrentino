from __future__ import annotations

from pipeline.enrichment import osm_source


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload: dict):
        self._payload = payload
        self.last_data = None

    def post(self, url, data=None, headers=None, timeout=None):
        self.last_data = data
        return _FakeResponse(self._payload)


class _RetryThenSucceedSession:
    def __init__(self, status_codes, payload: dict):
        self._status_codes = list(status_codes)
        self._payload = payload
        self.calls = 0

    def post(self, url, data=None, headers=None, timeout=None):
        status = self._status_codes[self.calls]
        self.calls += 1
        return _FakeResponse(self._payload, status_code=status)


def test_around_clause_uses_lat_lon_order():
    coords = [(11.0, 46.0), (11.1, 46.1)]
    clause = osm_source._around_clause(coords, 500)
    assert clause == "(around:500,46.0,11.0,46.1,11.1)"


def test_build_way_query_contains_alternation_and_around():
    query = osm_source.build_way_query("highway", ["primary", "track"], [(11.0, 46.0)], 600)
    assert 'way["highway"~"^(primary|track)$"]' in query
    assert "(around:600,46.0,11.0)" in query
    assert "out geom;" in query


def test_build_building_query_uses_bare_existence_filter():
    query = osm_source.build_building_query([(11.0, 46.0)], 500)
    assert 'way["building"]' in query
    assert "~" not in query  # no regex alternation for a bare-tag filter


def test_bbox_clause_covers_extent_plus_margin():
    coords = [(11.0, 46.0), (11.2, 46.2)]
    bbox = osm_source._bbox_clause(coords, margin_deg=0.05)
    assert bbox == "(45.95,10.95,46.25,11.25)"


def test_build_settlement_query_uses_bbox_not_around():
    query = osm_source.build_settlement_query("place", ["village"], [(11.0, 46.0)], margin_deg=0.05)
    assert "around" not in query
    assert 'node["place"~"^(village)$"]' in query
    assert "(45.95,10.95,46.05,11.05)" in query


def test_build_tourism_query_covers_nodes_and_ways():
    query = osm_source.build_tourism_query([(11.0, 46.0)], 1200)
    assert 'node["tourism"~' in query
    assert 'way["tourism"~' in query
    assert "out center;" in query


def test_parse_ways_extracts_geometry_and_tags():
    elements = [
        {"type": "way", "tags": {"highway": "primary"}, "geometry": [{"lat": 46.0, "lon": 11.0}, {"lat": 46.1, "lon": 11.1}]},
        {"type": "node", "lat": 46.0, "lon": 11.0},  # not a way, must be ignored
        {"type": "way", "tags": {}},  # no geometry, must be ignored
    ]
    ways = osm_source.parse_ways(elements)
    assert len(ways) == 1
    assert ways[0].tags == {"highway": "primary"}
    assert ways[0].coordinates == [(11.0, 46.0), (11.1, 46.1)]


def test_parse_nodes_extracts_points():
    elements = [
        {"type": "node", "tags": {"place": "village", "name": "Testolago"}, "lat": 46.0, "lon": 11.0},
        {"type": "way", "geometry": []},  # not a node, must be ignored
    ]
    points = osm_source.parse_nodes(elements)
    assert len(points) == 1
    assert points[0].lon == 11.0 and points[0].lat == 46.0
    assert points[0].tags["name"] == "Testolago"


def test_parse_tourism_elements_uses_center_for_ways():
    elements = [
        {"type": "node", "tags": {"tourism": "viewpoint"}, "lat": 46.0, "lon": 11.0},
        {"type": "way", "tags": {"tourism": "camp_site"}, "center": {"lat": 46.2, "lon": 11.2}},
        {"type": "way", "tags": {"tourism": "camp_site"}},  # no center, must be ignored
    ]
    points = osm_source.parse_tourism_elements(elements)
    assert len(points) == 2
    assert points[1].lon == 11.2 and points[1].lat == 46.2


def test_run_query_retries_after_429_then_succeeds(monkeypatch):
    monkeypatch.setattr("pipeline.enrichment.osm_source.time.sleep", lambda _: None)
    session = _RetryThenSucceedSession([429, 200], {"elements": []})

    result = osm_source.run_query("dummy query", session=session, max_retries=3)

    assert result == {"elements": []}
    assert session.calls == 2


def test_fetch_roads_uses_injected_session_and_parses_result():
    payload = {
        "elements": [
            {"type": "way", "tags": {"highway": "track"}, "geometry": [{"lat": 46.0, "lon": 11.0}, {"lat": 46.01, "lon": 11.0}]},
        ]
    }
    session = _FakeSession(payload)

    ways = osm_source.fetch_roads([(11.0, 46.0)], radius_m=500, session=session)

    assert len(ways) == 1
    assert ways[0].tags == {"highway": "track"}
    assert "highway" in session.last_data["data"]
