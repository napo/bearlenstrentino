"""Structural validation of a KML/KMZ payload before it enters the pipeline.

This only checks that the content is well-formed XML (unwrapping a KMZ
archive if needed) and contains a plausible number of Placemark elements.
It does not validate individual field content — that happens downstream
in `pipeline.normalization`.
"""
from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree as ET

KML_NAMESPACE = "http://www.opengis.net/kml/2.2"
_NS = {"kml": KML_NAMESPACE}


class InvalidSourceDataError(Exception):
    """Raised when downloaded content is not well-formed, non-empty KML/KMZ."""


def extract_kml_bytes(content: bytes) -> bytes:
    """Return the raw KML bytes, unwrapping a KMZ (zip) archive if needed."""
    if content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            kml_names = [n for n in archive.namelist() if n.lower().endswith(".kml")]
            if not kml_names:
                raise InvalidSourceDataError("KMZ archive does not contain a .kml entry")
            return archive.read(kml_names[0])
    return content


def parse_kml(content: bytes) -> ET.Element:
    """Parse KML bytes into an ElementTree root, unwrapping KMZ if necessary."""
    kml_bytes = extract_kml_bytes(content)
    try:
        return ET.fromstring(kml_bytes)
    except ET.ParseError as exc:
        raise InvalidSourceDataError(f"Malformed XML: {exc}") from exc


def validate_kml(content: bytes, *, min_placemarks: int = 1) -> ET.Element:
    """Parse and sanity-check KML content.

    Raises InvalidSourceDataError if the content is not well-formed or
    contains fewer than `min_placemarks` Placemark elements.
    """
    root = parse_kml(content)
    placemarks = root.findall(".//kml:Placemark", _NS)
    if len(placemarks) < min_placemarks:
        raise InvalidSourceDataError(
            f"Expected at least {min_placemarks} Placemark element(s), found {len(placemarks)}"
        )
    return root
