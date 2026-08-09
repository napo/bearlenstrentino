"""Milestones 2-3: turn extracted placemarks into the public normalized
schema.

This module populates: a stable identity, the source layer,
publication-safe (redacted) text, coordinates, media links, a best-effort
event date (Milestone 3, `pipeline.normalization.dates`), and a
conservative observation-type classification (Milestone 3,
`pipeline.normalization.classification`).

first_seen_at / last_seen_at / source_changed_at are set to the current
fetch timestamp on every run: this module does not yet compare against a
previous run's output to preserve a record's true first-seen date across
days — that cross-run history tracking is Milestone 4. Treat these three
fields as identical and not yet meaningful until M4 lands.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pipeline.acquisition.media import download_media, is_cacheable_image_url
from pipeline.normalization.classification import classify_observation
from pipeline.normalization.dates import parse_event_date
from pipeline.normalization.kml_parser import ExtractedPlacemark
from pipeline.normalization.time_extraction import parse_event_time
from pipeline.privacy.redactor import PiiRedactor


def _stable_id(placemark: ExtractedPlacemark) -> str:
    """Deterministic fingerprint identity (see AGENTS.md / REFERENCES.md
    identity strategy): hash of layer + raw name + rounded coordinates.

    Uses the true `name_raw` (not the redacted public name) as hash input
    so the id stays stable even if the redaction mapping changes; the
    hash itself is one-way and does not republish the name.
    """
    lon = round(placemark.longitude, 5) if placemark.longitude is not None else None
    lat = round(placemark.latitude, 5) if placemark.latitude is not None else None
    key = f"{placemark.source_layer}|{placemark.name_raw}|{lon}|{lat}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"obs_{digest}"


@dataclass
class NormalizedObservation:
    id: str
    source_layer: "str | None"
    name_public: "str | None"
    description_public: "str | None"
    longitude: "float | None"
    latitude: "float | None"
    coordinate_error: "str | None"
    media_links: "list[str]" = field(default_factory=list)
    media_local: "list[str | None]" = field(default_factory=list)
    redaction_applied: bool = False
    redaction_codes: "list[str]" = field(default_factory=list)
    first_seen_at: "str | None" = None
    last_seen_at: "str | None" = None
    source_changed_at: "str | None" = None
    event_date: "str | None" = None
    event_year: "int | None" = None
    event_month: "int | None" = None
    event_day: "int | None" = None
    date_text_raw: "str | None" = None
    date_parse_status: str = "not_present"
    event_hour: "int | None" = None
    event_minute: "int | None" = None
    time_text_raw: "str | None" = None
    time_parse_status: str = "not_present"
    observation_type: str = "unknown"
    classification_method: str = "unknown"
    classification_confidence: str = "unknown"


def _redact_optional(text: "str | None", redactor: PiiRedactor) -> "tuple[str | None, list[str]]":
    if not text:
        return text, []
    return redactor.redact(text)


def normalize_placemarks(
    placemarks: "list[ExtractedPlacemark]",
    redactor: PiiRedactor,
    *,
    as_of: datetime,
    media_cache_dir: "Path | None" = None,
    media_downloader=download_media,
) -> "list[NormalizedObservation]":
    as_of_iso = as_of.isoformat()
    results: list[NormalizedObservation] = []

    for placemark in placemarks:
        name_public, name_codes = _redact_optional(placemark.name_raw, redactor)
        description_public, description_codes = _redact_optional(
            placemark.description_raw, redactor
        )
        all_codes = [*name_codes, *description_codes]

        # Date parsing and classification run on the true source text —
        # neither depends on personal names, and using the authoritative
        # text avoids any chance of a PERSON_/PHONE_ code interfering with
        # keyword or date matching.
        parsed_date = parse_event_date(placemark.description_raw)
        parsed_time = parse_event_time(placemark.description_raw)
        classification = classify_observation(placemark.source_layer, placemark.description_raw)

        # Caching is opt-in (media_cache_dir=None by default) so unit
        # tests never touch the network — see pipeline/acquisition/media.py
        # for why a local copy is needed at all (source images block
        # cross-site embedding).
        media_local: "list[str | None]" = []
        if media_cache_dir is not None:
            for link in placemark.media_links:
                if is_cacheable_image_url(link):
                    filename = media_downloader(link, media_cache_dir)
                    media_local.append(f"media/{filename}" if filename else None)
                else:
                    media_local.append(None)

        results.append(
            NormalizedObservation(
                id=_stable_id(placemark),
                source_layer=placemark.source_layer,
                name_public=name_public,
                description_public=description_public,
                longitude=placemark.longitude,
                latitude=placemark.latitude,
                coordinate_error=placemark.coordinate_error,
                media_links=list(placemark.media_links),
                media_local=media_local,
                redaction_applied=bool(all_codes),
                redaction_codes=sorted(set(all_codes)),
                first_seen_at=as_of_iso,
                last_seen_at=as_of_iso,
                source_changed_at=as_of_iso,
                event_date=parsed_date.event_date,
                event_year=parsed_date.event_year,
                event_month=parsed_date.event_month,
                event_day=parsed_date.event_day,
                date_text_raw=parsed_date.date_text_raw,
                date_parse_status=parsed_date.date_parse_status,
                event_hour=parsed_time.event_hour,
                event_minute=parsed_time.event_minute,
                time_text_raw=parsed_time.time_text_raw,
                time_parse_status=parsed_time.time_parse_status,
                observation_type=classification.observation_type,
                classification_method=classification.classification_method,
                classification_confidence=classification.classification_confidence,
            )
        )

    return results
