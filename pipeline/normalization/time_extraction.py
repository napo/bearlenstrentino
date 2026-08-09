"""Time-of-day extraction from free-text descriptions, additional to
(not replacing) the calendar date parser in dates.py.

Same conservative philosophy as the date parser: never invent a time,
always keep the exact matched substring, and distinguish "exact" (hour
and minutes both found, e.g. "Ore 19:47" or "Alle 11.00") from
"approximate" (only an hour, typically introduced by "verso" — "around"
— e.g. "Verso le 13") from "not_present". Never guessed from context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.normalization.text import strip_html

# Real source examples this was built against: "Ore 19:47", "Ore 06:30",
# "Alle 11.00" (dot separator), "alle 7:00", "alle 17:45", "alle ore 20"
# (no minutes), "Verso le 13" (no minutes, approximate framing).
_EXACT_TIME_RE = re.compile(r"\b(?:ore|alle)\s+(?:ore\s+)?(\d{1,2})[:.](\d{2})\b", re.IGNORECASE)
_APPROX_TIME_RE = re.compile(r"\b(?:verso le|alle(?:\s+ore)?)\s+(\d{1,2})\b", re.IGNORECASE)


@dataclass
class ParsedTime:
    event_hour: "int | None" = None
    event_minute: "int | None" = None
    time_text_raw: "str | None" = None
    time_parse_status: str = "not_present"  # "exact" | "approximate" | "not_present"


def parse_event_time(description_raw: "str | None") -> ParsedTime:
    if not description_raw or not description_raw.strip():
        return ParsedTime()

    text = strip_html(description_raw)

    exact = _EXACT_TIME_RE.search(text)
    if exact:
        hour, minute = int(exact.group(1)), int(exact.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return ParsedTime(
                event_hour=hour,
                event_minute=minute,
                time_text_raw=exact.group(0),
                time_parse_status="exact",
            )

    approx = _APPROX_TIME_RE.search(text)
    if approx:
        hour = int(approx.group(1))
        if 0 <= hour <= 23:
            return ParsedTime(
                event_hour=hour,
                event_minute=None,
                time_text_raw=approx.group(0),
                time_parse_status="approximate",
            )

    return ParsedTime()
