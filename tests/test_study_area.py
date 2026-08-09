from __future__ import annotations

import pytest

from pipeline.baseline.study_area import fetch_study_area


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self._payload = payload

    def get(self, url, params=None, headers=None, timeout=None):
        return _FakeResponse(self._payload)


SAMPLE_RESULT = [
    {
        "osm_type": "relation",
        "osm_id": 45756,
        "display_name": "Provincia di Trento, Trentino-Alto Adige/Südtirol, Italia",
        "geojson": {
            "type": "Polygon",
            "coordinates": [[[11.0, 46.0], [11.1, 46.0], [11.1, 46.1], [11.0, 46.1], [11.0, 46.0]]],
        },
    }
]


def test_fetch_study_area_parses_geometry_and_metadata():
    session = _FakeSession(SAMPLE_RESULT)

    geometry, metadata = fetch_study_area(session=session)

    assert geometry.geom_type == "Polygon"
    assert geometry.bounds == (11.0, 46.0, 11.1, 46.1)
    assert metadata["osm_id"] == 45756
    assert metadata["osm_type"] == "relation"
    assert metadata["source"] == "Nominatim (OpenStreetMap)"


def test_fetch_study_area_raises_on_empty_result():
    session = _FakeSession([])
    with pytest.raises(ValueError):
        fetch_study_area(session=session)
