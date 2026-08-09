"""Milestone 3: extract a best-effort event date from free-text
descriptions.

This never uses the scrape/fetch timestamp as the event date, and never
invents a date the source text doesn't support: when the text is
ambiguous or lacks a date, `event_date` stays None and
`date_parse_status` records why (see AGENTS.md, "distinguere dati
osservati e derivati").

Only DD/MM/YYYY-style numeric dates (with `/` or `.` as separator) are
treated as "full" dates. A `-` between two full dates is treated as a
range separator, not a date-internal separator, precisely so a range
like "27/05/2026-30/05/2026" isn't mistaken for a single malformed date.

Heuristic, not exhaustive: Italian free text can express dates in ways
this module does not attempt to parse (e.g. "il mercoledì prima di
Ferragosto"). Those fall through to `date_parse_status="not_present"`
rather than being guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.normalization.text import strip_html

_FULL_DATE_RE = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b")
_DAY_MONTH_RE = re.compile(r"\b(\d{1,2})[/.](\d{1,2})\b")
_YEAR_ONLY_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_MONTHS_IT = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5,
    "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10,
    "novembre": 11, "dicembre": 12,
}
_MONTH_YEAR_RE = re.compile(
    r"\b(" + "|".join(_MONTHS_IT) + r")\s+((?:19|20)\d{2})\b", re.IGNORECASE
)

# A date found further into the text than this is treated as less likely
# to be THIS record's event date (vs. an incidental date mentioned later
# in the narrative, e.g. "...è tornato anche il 30/05/2026").
_LEADING_WINDOW_CHARS = 60


@dataclass
class ParsedDate:
    event_date: "str | None" = None
    event_year: "int | None" = None
    event_month: "int | None" = None
    event_day: "int | None" = None
    date_text_raw: "str | None" = None
    date_parse_status: str = "not_present"


def _valid_full_date(day: int, month: int, year: int) -> bool:
    return 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100


def parse_event_date(description_raw: "str | None") -> ParsedDate:
    if not description_raw or not description_raw.strip():
        return ParsedDate()

    text = strip_html(description_raw)
    full_matches = [
        m for m in _FULL_DATE_RE.finditer(text)
        if _valid_full_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    ]

    if full_matches:
        if len(full_matches) >= 2:
            first, second = full_matches[0], full_matches[1]
            between = text[first.end():second.start()]
            if re.fullmatch(r"\s*-\s*", between):
                return ParsedDate(
                    date_text_raw=text[first.start():second.end()].strip(),
                    date_parse_status="range",
                )

        first = full_matches[0]
        if first.start() <= _LEADING_WINDOW_CHARS:
            day, month, year = (
                int(first.group(1)), int(first.group(2)), int(first.group(3))
            )
            return ParsedDate(
                event_date=f"{year:04d}-{month:02d}-{day:02d}",
                event_year=year,
                event_month=month,
                event_day=day,
                date_text_raw=first.group(0),
                date_parse_status="full",
            )

        return ParsedDate(
            date_text_raw="; ".join(m.group(0) for m in full_matches),
            date_parse_status="ambiguous",
        )

    month_year_match = _MONTH_YEAR_RE.search(text)
    if month_year_match:
        return ParsedDate(
            event_year=int(month_year_match.group(2)),
            event_month=_MONTHS_IT[month_year_match.group(1).lower()],
            date_text_raw=month_year_match.group(0),
            date_parse_status="year_month",
        )

    day_month_match = _DAY_MONTH_RE.search(text)
    if day_month_match:
        day, month = int(day_month_match.group(1)), int(day_month_match.group(2))
        if 1 <= day <= 31 and 1 <= month <= 12:
            return ParsedDate(
                event_day=day,
                event_month=month,
                date_text_raw=day_month_match.group(0),
                date_parse_status="day_month_no_year",
            )
        return ParsedDate(date_text_raw=day_month_match.group(0), date_parse_status="failed")

    year_only_match = _YEAR_ONLY_RE.search(text)
    if year_only_match:
        return ParsedDate(
            event_year=int(year_only_match.group(0)),
            date_text_raw=year_only_match.group(0),
            date_parse_status="year_only",
        )

    return ParsedDate()
