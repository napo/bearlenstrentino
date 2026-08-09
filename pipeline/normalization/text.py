"""Small text utilities shared across normalization/history modules."""
from __future__ import annotations

import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub(" ", text)
