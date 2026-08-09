"""Download the source KML export and persist the true raw snapshot locally.

The true raw content (as downloaded from Google, unmodified) may contain
personal data present in the source and must never be committed to version
control — see AGENTS.md and README.md ("Privacy: pseudonimizzazione").
It is saved under a caller-provided local/CI-only directory instead.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from pipeline.acquisition.validate import InvalidSourceDataError

DEFAULT_MAP_ID = "1d43YdLzznhl-VxXOz6kg5ZKLdf5RjG4"
USER_AGENT = (
    "BearLensTrentino/0.1 "
    "(open-source bear-report transparency project; contact via repository issues)"
)


def build_kml_url(map_id: str) -> str:
    return f"https://www.google.com/maps/d/kml?mid={map_id}&forcekml=1"


@dataclass(frozen=True)
class RawSnapshot:
    content: bytes
    sha256: str
    fetched_at: datetime
    byte_size: int


def fetch_raw(
    map_id_or_url: str,
    *,
    session: "requests.Session | None" = None,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> RawSnapshot:
    """Download the KML export and return it with its content hash.

    Does not write anything to disk and does not validate KML structure —
    see `pipeline.acquisition.validate.validate_kml` for that.
    """
    url = map_id_or_url if map_id_or_url.startswith("http") else build_kml_url(map_id_or_url)
    http = session or requests.Session()
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = http.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
            response.raise_for_status()
            content = response.content
            if not content:
                raise InvalidSourceDataError("Empty response body from source")
            return RawSnapshot(
                content=content,
                sha256=hashlib.sha256(content).hexdigest(),
                fetched_at=datetime.now(timezone.utc),
                byte_size=len(content),
            )
        except (requests.RequestException, InvalidSourceDataError) as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Failed to fetch source after {max_retries} attempt(s): {last_error}"
    ) from last_error


def save_local_raw(snapshot: RawSnapshot, base_dir: Path) -> Path:
    """Persist the true raw snapshot to a local, non-public directory.

    `base_dir` must be a location excluded from version control
    (`data/_local_raw/` by default — see `.gitignore`).
    """
    day_dir = base_dir / snapshot.fetched_at.strftime("%Y/%m/%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    raw_path = day_dir / "source.kml"
    raw_path.write_bytes(snapshot.content)
    manifest = {
        "fetched_at": snapshot.fetched_at.isoformat(),
        "sha256": snapshot.sha256,
        "byte_size": snapshot.byte_size,
    }
    (day_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return raw_path


def read_last_hash(state_file: Path) -> "str | None":
    if not state_file.exists():
        return None
    content = state_file.read_text(encoding="utf-8").strip()
    return content or None


def write_last_hash(state_file: Path, sha256: str) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(sha256, encoding="utf-8")
