from __future__ import annotations

from pipeline.acquisition.media import download_media, is_cacheable_image_url


class _FakeResponse:
    def __init__(self, data: bytes, content_type: str):
        self._data = data
        self.headers = {"Content-Type": content_type}

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_is_cacheable_image_url():
    assert is_cacheable_image_url(
        "https://mymaps.usercontent.google.com/hostedimage/m/x/abc?fife=s16383"
    )
    assert not is_cacheable_image_url("https://www.youtube.com/embed/abc123")


def test_download_media_writes_file_with_extension_from_content_type(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pipeline.acquisition.media.urllib.request.urlopen",
        lambda request, timeout=None: _FakeResponse(b"\x89PNG-fake-bytes", "image/png"),
    )

    filename = download_media("https://mymaps.usercontent.google.com/x", tmp_path)

    assert filename is not None
    assert filename.endswith(".png")
    assert (tmp_path / filename).read_bytes() == b"\x89PNG-fake-bytes"


def test_download_media_skips_network_when_already_cached(tmp_path, monkeypatch):
    url = "https://mymaps.usercontent.google.com/x"
    calls = []
    monkeypatch.setattr(
        "pipeline.acquisition.media.urllib.request.urlopen",
        lambda request, timeout=None: calls.append(1) or _FakeResponse(b"data", "image/jpeg"),
    )

    first = download_media(url, tmp_path)
    second = download_media(url, tmp_path)

    assert first == second
    assert len(calls) == 1


def test_download_media_returns_none_for_unrecognized_content_type(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pipeline.acquisition.media.urllib.request.urlopen",
        lambda request, timeout=None: _FakeResponse(b"<html>not an image</html>", "text/html"),
    )

    assert download_media("https://mymaps.usercontent.google.com/x", tmp_path) is None


def test_download_media_returns_none_on_network_error(tmp_path, monkeypatch):
    def raise_error(request, timeout=None):
        raise OSError("network down")

    monkeypatch.setattr("pipeline.acquisition.media.urllib.request.urlopen", raise_error)

    assert download_media("https://mymaps.usercontent.google.com/x", tmp_path) is None
