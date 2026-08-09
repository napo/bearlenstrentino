from __future__ import annotations

from pipeline.normalization.text import strip_html


def test_strips_tags_but_keeps_text():
    html = '<img src="x.jpg" /><br>Un orso è stato avvistato.'
    assert strip_html(html) == "  Un orso è stato avvistato."


def test_no_tags_is_unchanged():
    assert strip_html("Nessun tag qui.") == "Nessun tag qui."
