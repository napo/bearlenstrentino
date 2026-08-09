from __future__ import annotations

import zipfile

from pipeline.acquisition.validate import parse_kml
from pipeline.normalization.kml_parser import extract_placemarks


def test_extracts_single_placemark_with_layer_and_description(load_fixture):
    root = parse_kml(load_fixture("simple.kml"))
    placemarks = extract_placemarks(root)

    assert len(placemarks) == 1
    p = placemarks[0]
    assert p.source_layer == "Avvistamento a distanza"
    assert p.name_raw == "Bosco Alto"
    assert "avvistato" in p.description_raw
    assert p.longitude == 11.1234
    assert p.latitude == 46.1234
    assert p.coordinate_error is None


def test_multi_folder_and_extended_data(load_fixture):
    root = parse_kml(load_fixture("multi_folder.kml"))
    placemarks = extract_placemarks(root)
    assert len(placemarks) == 3

    by_name = {p.name_raw: p for p in placemarks}

    trap = by_name["Malga Bianca"]
    assert trap.source_layer == "Fototrappolaggio"
    assert trap.media_links == ["https://example.org/photo.jpg"]
    assert trap.raw_properties["gx_media_links"] == "https://example.org/photo.jpg"

    accident = by_name["Ponte Vecchio"]
    assert accident.source_layer == "Incidenti stradali"
    assert "(15/07/2024)" in accident.description_raw

    no_desc = by_name["Senza descrizione"]
    assert no_desc.description_raw is None
    assert no_desc.source_layer == "Incidenti stradali"


def test_missing_and_invalid_coordinates_are_flagged_not_dropped(load_fixture):
    root = parse_kml(load_fixture("invalid_coordinates.kml"))
    placemarks = extract_placemarks(root)
    assert len(placemarks) == 3
    by_name = {p.name_raw: p for p in placemarks}

    missing = by_name["Coordinate mancanti"]
    assert missing.longitude is None
    assert missing.coordinate_error == "missing coordinates element"

    malformed = by_name["Coordinate malformate"]
    assert malformed.longitude is None
    assert "non-numeric" in malformed.coordinate_error

    out_of_range = by_name["Coordinate fuori intervallo"]
    assert out_of_range.longitude is None
    assert "out of range" in out_of_range.coordinate_error


def test_kmz_archive_is_transparently_unwrapped(tmp_path, load_fixture):
    kmz_path = tmp_path / "source.kmz"
    with zipfile.ZipFile(kmz_path, "w") as archive:
        archive.writestr("doc.kml", load_fixture("simple.kml"))

    root = parse_kml(kmz_path.read_bytes())
    placemarks = extract_placemarks(root)
    assert len(placemarks) == 1
