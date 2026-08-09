from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
import requests

from pipeline.acquisition.fetch import (
    DEFAULT_MAP_ID,
    RawSnapshot,
    build_kml_url,
    fetch_raw,
    read_last_hash,
    save_local_raw,
    write_last_hash,
)


class _FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


class _FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, headers=None, timeout=None):
        self.calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_build_kml_url_uses_forcekml():
    url = build_kml_url(DEFAULT_MAP_ID)
    assert url == f"https://www.google.com/maps/d/kml?mid={DEFAULT_MAP_ID}&forcekml=1"


def test_fetch_raw_returns_content_and_hash():
    content = b"<kml>ok</kml>"
    session = _FakeSession([_FakeResponse(content)])

    snapshot = fetch_raw(DEFAULT_MAP_ID, session=session)

    assert snapshot.content == content
    assert snapshot.sha256 == hashlib.sha256(content).hexdigest()
    assert snapshot.byte_size == len(content)


def test_fetch_raw_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("pipeline.acquisition.fetch.time.sleep", lambda _: None)
    session = _FakeSession([requests.ConnectionError("boom"), _FakeResponse(b"<kml>ok</kml>")])

    snapshot = fetch_raw(DEFAULT_MAP_ID, session=session, max_retries=3)

    assert snapshot.content == b"<kml>ok</kml>"
    assert session.calls == 2


def test_fetch_raw_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr("pipeline.acquisition.fetch.time.sleep", lambda _: None)
    session = _FakeSession([requests.ConnectionError("boom")] * 3)

    with pytest.raises(RuntimeError):
        fetch_raw(DEFAULT_MAP_ID, session=session, max_retries=3)


def test_save_local_raw_writes_content_and_manifest(tmp_path):
    snapshot = RawSnapshot(
        content=b"<kml>ok</kml>",
        sha256="abc123",
        fetched_at=datetime(2024, 5, 12, tzinfo=timezone.utc),
        byte_size=13,
    )

    raw_path = save_local_raw(snapshot, tmp_path)

    assert raw_path.read_bytes() == b"<kml>ok</kml>"
    assert (raw_path.parent / "manifest.json").exists()


def test_last_hash_roundtrip(tmp_path):
    state_file = tmp_path / "last_hash.txt"
    assert read_last_hash(state_file) is None

    write_last_hash(state_file, "deadbeef")

    assert read_last_hash(state_file) == "deadbeef"
