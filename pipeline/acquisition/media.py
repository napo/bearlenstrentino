"""Caches photos referenced by observations locally, so the public site
can display them without hot-linking to the source URLs.

mymaps.usercontent.google.com serves `Cross-Origin-Resource-Policy:
same-site` on these images (confirmed by hand, see project notes): any
browser loading them from a different origin — i.e. this site — gets
the request blocked, regardless of the image otherwise being public and
unauthenticated. Caching a local copy at acquisition time is the fix.

Downloads are content-addressed (filename = hash of the source URL) and
idempotent: an existing cached file is never re-fetched. A single failed
download never raises — a missing photo isn't worth failing the whole
acquisition run over; callers get None and the observation simply
publishes without a local copy for that link.
"""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

_EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

_CACHEABLE_PREFIX = "https://mymaps.usercontent.google.com/"


def is_cacheable_image_url(url: str) -> bool:
    return url.startswith(_CACHEABLE_PREFIX)


def download_media(url: str, dest_dir: Path) -> "str | None":
    """Downloads `url` into `dest_dir`. Returns the written filename
    (not a full path), or None if the download failed or the response
    wasn't a recognized image type. Skips the network entirely if a
    cached copy already exists.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]

    if dest_dir.exists():
        existing = list(dest_dir.glob(f"{digest}.*"))
        if existing:
            return existing[0].name

    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
            extension = _EXTENSION_BY_CONTENT_TYPE.get(content_type)
            if extension is None:
                return None
            data = response.read()
    except Exception:
        return None

    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{digest}{extension}"
    (dest_dir / filename).write_bytes(data)
    return filename
