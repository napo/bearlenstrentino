from __future__ import annotations

import csv
import json

from pipeline.normalization.observations import NormalizedObservation
from pipeline.normalization.export import write_csv, write_geojson


def _sample_observation(**overrides) -> NormalizedObservation:
    defaults = dict(
        id="obs_deadbeef12345678",
        source_layer="Avvistamento a distanza",
        name_public="Bosco Alto",
        description_public="Un orso è stato avvistato.",
        longitude=11.1234,
        latitude=46.1234,
        coordinate_error=None,
        media_links=["https://example.org/photo.jpg"],
        redaction_applied=False,
        redaction_codes=[],
        first_seen_at="2026-08-08T12:00:00+00:00",
        last_seen_at="2026-08-08T12:00:00+00:00",
        source_changed_at="2026-08-08T12:00:00+00:00",
    )
    defaults.update(overrides)
    return NormalizedObservation(**defaults)


def test_write_csv_round_trips_basic_fields(tmp_path):
    path = tmp_path / "observations.csv"
    write_csv([_sample_observation()], path)

    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "obs_deadbeef12345678"
    assert row["name_public"] == "Bosco Alto"
    assert row["longitude"] == "11.1234"
    assert row["media_links"] == "https://example.org/photo.jpg"
    assert row["redaction_applied"] == "False"


def test_write_csv_handles_missing_coordinates_without_crashing(tmp_path):
    path = tmp_path / "observations.csv"
    obs = _sample_observation(longitude=None, latitude=None, coordinate_error="missing coordinates element")
    write_csv([obs], path)

    with path.open(newline="", encoding="utf-8") as fh:
        [row] = list(csv.DictReader(fh))

    assert row["longitude"] == ""
    assert row["coordinate_error"] == "missing coordinates element"


def test_write_geojson_produces_valid_feature_collection(tmp_path):
    path = tmp_path / "observations.geojson"
    write_geojson([_sample_observation()], path)

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    feature = data["features"][0]
    assert feature["geometry"] == {"type": "Point", "coordinates": [11.1234, 46.1234]}
    assert feature["properties"]["id"] == "obs_deadbeef12345678"


def test_write_geojson_uses_null_geometry_for_missing_coordinates(tmp_path):
    path = tmp_path / "observations.geojson"
    obs = _sample_observation(longitude=None, latitude=None, coordinate_error="missing coordinates element")
    write_geojson([obs], path)

    data = json.loads(path.read_text(encoding="utf-8"))

    feature = data["features"][0]
    assert feature["geometry"] is None
    assert feature["properties"]["coordinate_error"] == "missing coordinates element"
