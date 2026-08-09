from __future__ import annotations

import pytest

from pipeline.acquisition.validate import InvalidSourceDataError, validate_kml


def test_rejects_malformed_xml():
    with pytest.raises(InvalidSourceDataError):
        validate_kml(b"<kml><Document>")


def test_rejects_content_with_no_placemarks():
    content = b"""<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2">
    <Document><name>Vuota</name></Document></kml>"""
    with pytest.raises(InvalidSourceDataError):
        validate_kml(content)


def test_accepts_well_formed_kml_with_placemarks(load_fixture):
    root = validate_kml(load_fixture("simple.kml"))
    assert root is not None


def test_rejects_kmz_without_kml_entry():
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "not a kml file")

    with pytest.raises(InvalidSourceDataError):
        validate_kml(buffer.getvalue())
