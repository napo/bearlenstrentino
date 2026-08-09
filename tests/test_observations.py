from __future__ import annotations

from datetime import datetime, timezone

from pipeline.normalization.kml_parser import ExtractedPlacemark
from pipeline.normalization.observations import normalize_placemarks
from pipeline.privacy.redactor import PiiRedactor

AS_OF = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def test_redacts_name_and_description_and_tracks_codes(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = ExtractedPlacemark(
        source_layer="Incontri ravvicinati",
        name_raw="Cadine",
        description_raw="Mario Rossi ha visto l'orso vicino a Maso Fienile.",
        longitude=11.02,
        latitude=46.02,
    )

    [obs] = normalize_placemarks([placemark], redactor, as_of=AS_OF)

    assert obs.name_public == "Cadine"
    assert "Mario Rossi" not in obs.description_public
    assert "Maso Fienile" in obs.description_public
    assert obs.redaction_applied is True
    assert obs.redaction_codes == ["PERSON_0001"]


def test_no_redaction_needed_when_no_pii_present(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = ExtractedPlacemark(
        source_layer="Avvistamento a distanza",
        name_raw="Bosco Alto",
        description_raw="Un orso è stato avvistato ai margini del bosco.",
        longitude=11.1234,
        latitude=46.1234,
    )

    [obs] = normalize_placemarks([placemark], redactor, as_of=AS_OF)

    assert obs.redaction_applied is False
    assert obs.redaction_codes == []


def test_stable_id_is_deterministic_and_identity_based_on_raw_name(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = ExtractedPlacemark(
        source_layer="Predazioni",
        name_raw="Malga Bianca",
        description_raw="Danno a un allevamento.",
        longitude=11.5,
        latitude=46.5,
    )

    [obs1] = normalize_placemarks([placemark], redactor, as_of=AS_OF)
    [obs2] = normalize_placemarks([placemark], redactor, as_of=AS_OF)

    assert obs1.id == obs2.id
    assert obs1.id.startswith("obs_")


def test_different_placemarks_get_different_ids(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    a = ExtractedPlacemark(
        source_layer="Predazioni", name_raw="Malga Bianca",
        description_raw="x", longitude=11.5, latitude=46.5,
    )
    b = ExtractedPlacemark(
        source_layer="Predazioni", name_raw="Malga Rossa",
        description_raw="x", longitude=11.6, latitude=46.6,
    )

    [obs_a] = normalize_placemarks([a], redactor, as_of=AS_OF)
    [obs_b] = normalize_placemarks([b], redactor, as_of=AS_OF)

    assert obs_a.id != obs_b.id


def test_missing_coordinates_are_preserved_as_none_not_dropped(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = ExtractedPlacemark(
        source_layer="Test",
        name_raw="Senza coordinate",
        description_raw="Nessun punto.",
        longitude=None,
        latitude=None,
        coordinate_error="missing coordinates element",
    )

    [obs] = normalize_placemarks([placemark], redactor, as_of=AS_OF)

    assert obs.longitude is None
    assert obs.latitude is None
    assert obs.coordinate_error == "missing coordinates element"


def test_timestamps_use_as_of_for_single_run_scope(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = ExtractedPlacemark(
        source_layer="Test", name_raw="X", description_raw="y",
        longitude=11.0, latitude=46.0,
    )

    [obs] = normalize_placemarks([placemark], redactor, as_of=AS_OF)

    assert obs.first_seen_at == obs.last_seen_at == obs.source_changed_at == AS_OF.isoformat()
