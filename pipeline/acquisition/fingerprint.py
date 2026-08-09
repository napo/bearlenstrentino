"""Semantic fingerprint of the source's actual content.

Google re-signs embedded image URLs (`gx_media_links`, `<img src="...">`)
on every single KML export, so two fetches of an otherwise-unchanged
source differ byte-for-byte every time (verified directly against the
live source: same Placemark text, different image tokens, different
overall SHA-256, identical byte size). A raw byte hash is therefore
useless for deciding whether anything worth republishing changed.

This fingerprint instead hashes only what a reader would recognize as
"the data": layer, name, HTML-stripped description text, and
coordinates — so the redacted KML copy (and the git history built on top
of it, once Milestone 4's automation exists) only changes when the
source's actual content does.
"""
from __future__ import annotations

import hashlib

from pipeline.normalization.kml_parser import ExtractedPlacemark
from pipeline.normalization.text import strip_html


def semantic_fingerprint(placemarks: "list[ExtractedPlacemark]") -> str:
    parts = [
        f"{p.source_layer}|{p.name_raw}|{strip_html(p.description_raw or '')}|{p.longitude}|{p.latitude}"
        for p in placemarks
    ]
    parts.sort()
    payload = "\n".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
