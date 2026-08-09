from __future__ import annotations

import io

import pytest
from PIL import Image

from pipeline.enrichment.nightlight import (
    NightLightRaster,
    fetch_night_light_raster,
    sample_brightness,
)

BBOX = (10.0, 45.0, 11.0, 46.0)  # (min_lon, min_lat, max_lon, max_lat)


def _quadrant_image() -> Image.Image:
    # 100x100 image, four quadrants, each a distinct flat brightness.
    # Row 0 = north edge, row 99 = south edge (standard image convention).
    img = Image.new("RGB", (100, 100))
    for y in range(100):
        for x in range(100):
            north = y < 50
            west = x < 50
            if north and west:
                color = (10, 10, 10)
            elif north and not west:
                color = (200, 200, 200)
            elif not north and west:
                color = (50, 50, 50)
            else:
                color = (150, 150, 150)
            img.putpixel((x, y), color)
    return img


@pytest.fixture
def quadrant_raster() -> NightLightRaster:
    return NightLightRaster(image=_quadrant_image(), bbox=BBOX)


def test_sample_brightness_northwest_quadrant(quadrant_raster):
    assert sample_brightness(quadrant_raster, lon=10.25, lat=45.75) == 10


def test_sample_brightness_northeast_quadrant(quadrant_raster):
    assert sample_brightness(quadrant_raster, lon=10.75, lat=45.75) == 200


def test_sample_brightness_southwest_quadrant(quadrant_raster):
    assert sample_brightness(quadrant_raster, lon=10.25, lat=45.25) == 50


def test_sample_brightness_southeast_quadrant(quadrant_raster):
    assert sample_brightness(quadrant_raster, lon=10.75, lat=45.25) == 150


def test_sample_brightness_outside_bbox_is_none_not_guessed(quadrant_raster):
    assert sample_brightness(quadrant_raster, lon=20.0, lat=45.5) is None
    assert sample_brightness(quadrant_raster, lon=10.5, lat=50.0) is None


class _FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeSession:
    def __init__(self, content: bytes):
        self._content = content
        self.last_params = None

    def get(self, url, params=None, headers=None, timeout=None):
        self.last_params = params
        return _FakeResponse(self._content)


def test_fetch_night_light_raster_parses_image_from_response():
    buffer = io.BytesIO()
    _quadrant_image().save(buffer, format="TIFF")
    session = _FakeSession(buffer.getvalue())

    raster = fetch_night_light_raster(BBOX, width=100, height=100, session=session)

    assert raster.image.size == (100, 100)
    assert raster.bbox == BBOX
    assert session.last_params["LAYERS"] == "VIIRS_Black_Marble"
    assert session.last_params["BBOX"] == "10.0,45.0,11.0,46.0"
