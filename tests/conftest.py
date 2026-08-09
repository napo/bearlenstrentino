from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "kml"


@pytest.fixture
def load_fixture():
    def _load(name: str) -> bytes:
        return (FIXTURES_DIR / name).read_bytes()

    return _load
