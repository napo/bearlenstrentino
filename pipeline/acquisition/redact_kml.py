"""Produce a publication-safe copy of a KML document with detected personal
data replaced by stable codes (see `pipeline.privacy.redactor`).

This is the only point in the pipeline where source text is modified
before being written to a location that may be committed to version
control. The input tree is never mutated in place: callers keep the
original (true) tree for local-only use and get back a separate,
redacted tree safe to publish.

Note on fidelity: the source KML wraps `<description>` content in CDATA
sections containing literal HTML. Re-serializing via ElementTree XML-escapes
that HTML instead of preserving the CDATA wrapper. This is expected and
harmless (any KML/XML consumer parses both forms identically) — the
redacted copy is explicitly a derived, publication-safe artifact, not a
byte-identical copy of the source (only the private, unpublished raw file
is byte-identical, see AGENTS.md).
"""
from __future__ import annotations

from copy import deepcopy
from xml.etree import ElementTree as ET

from pipeline.privacy.redactor import PiiRedactor

_NS = "{http://www.opengis.net/kml/2.2}"


def redact_kml_tree(root: ET.Element, redactor: PiiRedactor) -> "tuple[ET.Element, list[str]]":
    """Return (redacted_copy_of_root, all_codes_introduced_or_reused).

    Every `<name>` and `<description>` text node in the tree is passed
    through `redactor` — this includes Document/Folder names as well as
    Placemark fields, since we cannot guarantee personal data never
    appears in a folder/document title.
    """
    redacted_root = deepcopy(root)
    all_codes: list[str] = []
    for tag in ("name", "description"):
        for element in redacted_root.iter(f"{_NS}{tag}"):
            if element.text:
                redacted_text, codes = redactor.redact(element.text)
                element.text = redacted_text
                all_codes.extend(codes)
    return redacted_root, all_codes


def serialize_kml(root: ET.Element) -> bytes:
    ET.register_namespace("", "http://www.opengis.net/kml/2.2")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
