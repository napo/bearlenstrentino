"""Milestone 8c: artificial night light as an observer-effort proxy
(Ditmer et al. 2021 — see REFERENCES.md: night light was the single
strongest predictor of black bear report rate in their study, stronger
than housing density, land cover, or road density).

IMPORTANT — this is a documented approximation, not the calibrated VIIRS
radiance product used in that literature. The actual VIIRS DNB radiance
source (EOG/mines.edu) requires an authenticated login this project does
not have configured (verified directly: the download endpoint redirects
to an OpenID Connect login). This module instead uses NASA GIBS' public,
unauthenticated WMS endpoint for the "VIIRS Black Marble" layer, which
serves a pre-rendered visualization (an 8-bit RGB image stretched for
display), not raw radiance in nW/cm2/sr.

The resulting `night_light_proxy` value (0-255) is only a RELATIVE
brightness indicator suitable for ranking/comparing locations against
each other — never present it as calibrated radiance, and never compare
its absolute values to published radiance figures.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import requests
from PIL import Image

GIBS_WMS_URL = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
USER_AGENT = (
    "BearLensTrentino/0.1 (night light proxy lookup, manual/periodic; "
    "contact via repository issues)"
)
DEFAULT_LAYER = "VIIRS_Black_Marble"
# A specific, known-good Black Marble composite date. GIBS also serves
# more recent dates; this one was verified reachable during development.
DEFAULT_TIME = "2016-01-01"


@dataclass
class NightLightRaster:
    image: "Image.Image"  # RGB
    bbox: "tuple[float, float, float, float]"  # (min_lon, min_lat, max_lon, max_lat)


def fetch_night_light_raster(
    bbox: "tuple[float, float, float, float]",
    *,
    width: int = 1024,
    height: int = 1024,
    time: str = DEFAULT_TIME,
    layer: str = DEFAULT_LAYER,
    session: "requests.Session | None" = None,
) -> NightLightRaster:
    min_lon, min_lat, max_lon, max_lat = bbox
    http = session or requests.Session()
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "STYLES": "",
        "BBOX": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "FORMAT": "image/tiff",
        "SRS": "EPSG:4326",
        "TIME": time,
    }
    response = http.get(GIBS_WMS_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=90)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    return NightLightRaster(image=image, bbox=bbox)


def sample_brightness(raster: NightLightRaster, lon: float, lat: float) -> "int | None":
    """Returns the max(R,G,B) channel value at (lon, lat), or None if the
    point falls outside the raster's bbox — never guessed."""
    min_lon, min_lat, max_lon, max_lat = raster.bbox
    if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
        return None

    width, height = raster.image.size
    x = int((lon - min_lon) / (max_lon - min_lon) * (width - 1))
    # Row 0 is the NORTH edge (max_lat): y increases southward.
    y = int((max_lat - lat) / (max_lat - min_lat) * (height - 1))
    r, g, b = raster.image.getpixel((x, y))
    return max(r, g, b)
