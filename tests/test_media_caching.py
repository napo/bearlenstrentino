from __future__ import annotations

from datetime import datetime, timezone

from pipeline.normalization.kml_parser import ExtractedPlacemark
from pipeline.normalization.observations import normalize_placemarks
from pipeline.privacy.redactor import PiiRedactor

AS_OF = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

CACHEABLE_URL = "https://mymaps.usercontent.google.com/hostedimage/m/x/abc?fife=s16383"
YOUTUBE_URL = "https://www.youtube.com/embed/emlZoHNTucE"


def _placemark(media_links):
    return ExtractedPlacemark(
        source_layer="Avvistamenti",
        name_raw="Cadine",
        description_raw="Un orso attraversa la strada.",
        longitude=11.02,
        latitude=46.02,
        media_links=media_links,
    )


def test_media_local_empty_by_default_no_network_touched(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = _placemark([CACHEABLE_URL])

    [obs] = normalize_placemarks([placemark], redactor, as_of=AS_OF)

    assert obs.media_local == []


def test_cacheable_image_url_uses_injected_downloader(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = _placemark([CACHEABLE_URL])
    calls = []

    def fake_downloader(url, dest_dir):
        calls.append((url, dest_dir))
        return "fake123.jpg"

    [obs] = normalize_placemarks(
        [placemark],
        redactor,
        as_of=AS_OF,
        media_cache_dir=tmp_path / "media",
        media_downloader=fake_downloader,
    )

    assert obs.media_local == ["media/fake123.jpg"]
    assert calls == [(CACHEABLE_URL, tmp_path / "media")]


def test_youtube_link_never_passed_to_downloader(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = _placemark([YOUTUBE_URL])

    def failing_downloader(url, dest_dir):
        raise AssertionError("downloader should not be called for a non-image link")

    [obs] = normalize_placemarks(
        [placemark],
        redactor,
        as_of=AS_OF,
        media_cache_dir=tmp_path / "media",
        media_downloader=failing_downloader,
    )

    assert obs.media_local == [None]


def test_failed_download_yields_none_not_a_crash(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = _placemark([CACHEABLE_URL])

    [obs] = normalize_placemarks(
        [placemark],
        redactor,
        as_of=AS_OF,
        media_cache_dir=tmp_path / "media",
        media_downloader=lambda url, dest_dir: None,
    )

    assert obs.media_local == [None]


def test_media_local_order_matches_media_links_order(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    placemark = _placemark([YOUTUBE_URL, CACHEABLE_URL])

    [obs] = normalize_placemarks(
        [placemark],
        redactor,
        as_of=AS_OF,
        media_cache_dir=tmp_path / "media",
        media_downloader=lambda url, dest_dir: "cached.jpg",
    )

    assert obs.media_local == [None, "media/cached.jpg"]
