from __future__ import annotations

from pipeline.acquisition.fingerprint import semantic_fingerprint
from pipeline.normalization.kml_parser import ExtractedPlacemark


def _placemark(**overrides) -> ExtractedPlacemark:
    defaults = dict(
        source_layer="Avvistamento a distanza",
        name_raw="Vallene",
        description_raw='<img src="https://example.org/a.jpg" />Un orso è stato avvistato.',
        longitude=11.0,
        latitude=46.0,
    )
    defaults.update(overrides)
    return ExtractedPlacemark(**defaults)


def test_fingerprint_ignores_volatile_image_urls():
    # Google re-signs gx_media_links/img src tokens on every export even
    # when the actual report text is unchanged (verified against the live
    # source) — the fingerprint must not change just because of that.
    a = [_placemark(description_raw='<img src="https://example.org/token-AAA.jpg" />Un orso è stato avvistato.')]
    b = [_placemark(description_raw='<img src="https://example.org/token-ZZZ999.jpg" />Un orso è stato avvistato.')]

    assert semantic_fingerprint(a) == semantic_fingerprint(b)


def test_fingerprint_changes_when_real_text_changes():
    a = [_placemark(description_raw="Un orso è stato avvistato.")]
    b = [_placemark(description_raw="Un orso è stato avvistato due volte.")]

    assert semantic_fingerprint(a) != semantic_fingerprint(b)


def test_fingerprint_changes_when_coordinates_change():
    a = [_placemark(longitude=11.0)]
    b = [_placemark(longitude=11.5)]

    assert semantic_fingerprint(a) != semantic_fingerprint(b)


def test_fingerprint_is_order_independent():
    p1 = _placemark(name_raw="Vallene")
    p2 = _placemark(name_raw="Cadine")

    assert semantic_fingerprint([p1, p2]) == semantic_fingerprint([p2, p1])
