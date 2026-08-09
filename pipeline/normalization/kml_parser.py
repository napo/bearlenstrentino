"""Structural extraction of Placemark data from a parsed KML tree.

This is Milestone 1 scope: turn the KML DOM into plain Python records that
preserve every source field (folder/layer path, name, description,
coordinates, ExtendedData) without yet applying date parsing or
observation classification (Milestone 2/3 — see REFERENCES.md for the
milestone breakdown).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

_NS = "{http://www.opengis.net/kml/2.2}"


@dataclass
class ExtractedPlacemark:
    source_layer: "str | None"
    name_raw: "str | None"
    description_raw: "str | None"
    longitude: "float | None"
    latitude: "float | None"
    media_links: "list[str]" = field(default_factory=list)
    raw_properties: "dict[str, str]" = field(default_factory=dict)
    coordinate_error: "str | None" = None


def _stripped_text(el: "ET.Element | None") -> "str | None":
    """Whitespace-trimmed text, used for internal lookups (e.g. folder
    names used to build `source_layer`). Not used for the *_raw output
    fields, which preserve the source text exactly."""
    if el is None or el.text is None:
        return None
    text = el.text.strip()
    return text or None


def _raw_text(el: "ET.Element | None") -> "str | None":
    """Exact source text (no trimming), for name_raw/description_raw."""
    if el is None or el.text is None:
        return None
    return el.text


def _parse_coordinates(placemark: ET.Element) -> "tuple[float | None, float | None, str | None]":
    coords_el = placemark.find(f"{_NS}Point/{_NS}coordinates")
    if coords_el is None or not coords_el.text or not coords_el.text.strip():
        return None, None, "missing coordinates element"

    raw = coords_el.text.strip()
    parts = raw.split(",")
    if len(parts) < 2:
        return None, None, f"unparseable coordinate string: {raw!r}"

    try:
        longitude = float(parts[0].strip())
        latitude = float(parts[1].strip())
    except ValueError:
        return None, None, f"non-numeric coordinate string: {raw!r}"

    if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
        return None, None, f"coordinate out of range: {raw!r}"

    return longitude, latitude, None


def _extended_data(placemark: ET.Element) -> "dict[str, str]":
    props: dict[str, str] = {}
    for data_el in placemark.findall(f"{_NS}ExtendedData/{_NS}Data"):
        key = data_el.get("name")
        value_el = data_el.find(f"{_NS}value")
        if key and value_el is not None and value_el.text:
            props[key] = value_el.text.strip()
    return props


def _media_links(raw_properties: "dict[str, str]") -> "list[str]":
    links: list[str] = []
    if "gx_media_links" in raw_properties:
        links.extend(url.strip() for url in raw_properties["gx_media_links"].split() if url.strip())
    return links


def extract_placemarks(root: ET.Element) -> "list[ExtractedPlacemark]":
    """Extract every Placemark in `root`, tracking the Folder path each one
    belongs to (`source_layer`, joined with ' / ' for nested folders)."""
    results: list[ExtractedPlacemark] = []

    def _walk(node: ET.Element, trail: "list[str]") -> None:
        for child in node:
            if child.tag == f"{_NS}Folder":
                name = _stripped_text(child.find(f"{_NS}name"))
                _walk(child, trail + [name] if name else trail)
            elif child.tag == f"{_NS}Placemark":
                longitude, latitude, coordinate_error = _parse_coordinates(child)
                raw_properties = _extended_data(child)
                results.append(
                    ExtractedPlacemark(
                        source_layer=" / ".join(trail) if trail else None,
                        name_raw=_raw_text(child.find(f"{_NS}name")),
                        description_raw=_raw_text(child.find(f"{_NS}description")),
                        longitude=longitude,
                        latitude=latitude,
                        media_links=_media_links(raw_properties),
                        raw_properties=raw_properties,
                        coordinate_error=coordinate_error,
                    )
                )
            else:
                # Document, kml root, or any other wrapper: keep walking.
                _walk(child, trail)

    _walk(root, [])
    return results
