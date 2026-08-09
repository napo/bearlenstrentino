"""Write NormalizedObservation records to the public CSV/GeoJSON outputs
(`data/normalized/observations.csv` and `.geojson`).

CSV is kept flat and simple on purpose so it opens cleanly in pandas, R,
QGIS, and DuckDB without preprocessing (see README.md).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from pipeline.normalization.observations import NormalizedObservation

CSV_FIELDS = [
    "id",
    "source_layer",
    "name_public",
    "description_public",
    "longitude",
    "latitude",
    "coordinate_error",
    "media_links",
    "media_local",
    "redaction_applied",
    "redaction_codes",
    "first_seen_at",
    "last_seen_at",
    "source_changed_at",
    "event_date",
    "event_year",
    "event_month",
    "event_day",
    "date_text_raw",
    "date_parse_status",
    "event_hour",
    "event_minute",
    "time_text_raw",
    "time_parse_status",
    "observation_type",
    "classification_method",
    "classification_confidence",
]


def _csv_row(obs: NormalizedObservation) -> dict:
    return {
        "id": obs.id,
        "source_layer": obs.source_layer or "",
        "name_public": obs.name_public or "",
        "description_public": obs.description_public or "",
        "longitude": obs.longitude if obs.longitude is not None else "",
        "latitude": obs.latitude if obs.latitude is not None else "",
        "coordinate_error": obs.coordinate_error or "",
        "media_links": ";".join(obs.media_links),
        "media_local": ";".join(m or "" for m in obs.media_local),
        "redaction_applied": obs.redaction_applied,
        "redaction_codes": ";".join(obs.redaction_codes),
        "first_seen_at": obs.first_seen_at or "",
        "last_seen_at": obs.last_seen_at or "",
        "source_changed_at": obs.source_changed_at or "",
        "event_date": obs.event_date or "",
        "event_year": obs.event_year if obs.event_year is not None else "",
        "event_month": obs.event_month if obs.event_month is not None else "",
        "event_day": obs.event_day if obs.event_day is not None else "",
        "date_text_raw": obs.date_text_raw or "",
        "date_parse_status": obs.date_parse_status,
        "event_hour": obs.event_hour if obs.event_hour is not None else "",
        "event_minute": obs.event_minute if obs.event_minute is not None else "",
        "time_text_raw": obs.time_text_raw or "",
        "time_parse_status": obs.time_parse_status,
        "observation_type": obs.observation_type,
        "classification_method": obs.classification_method,
        "classification_confidence": obs.classification_confidence,
    }


def write_csv(observations: "list[NormalizedObservation]", path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for obs in observations:
            writer.writerow(_csv_row(obs))


def _to_feature(obs: NormalizedObservation) -> dict:
    geometry = None
    if obs.longitude is not None and obs.latitude is not None:
        geometry = {"type": "Point", "coordinates": [obs.longitude, obs.latitude]}
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "id": obs.id,
            "source_layer": obs.source_layer,
            "name_public": obs.name_public,
            "description_public": obs.description_public,
            "coordinate_error": obs.coordinate_error,
            "media_links": obs.media_links,
            "media_local": obs.media_local,
            "redaction_applied": obs.redaction_applied,
            "redaction_codes": obs.redaction_codes,
            "first_seen_at": obs.first_seen_at,
            "last_seen_at": obs.last_seen_at,
            "source_changed_at": obs.source_changed_at,
            "event_date": obs.event_date,
            "event_year": obs.event_year,
            "event_month": obs.event_month,
            "event_day": obs.event_day,
            "date_text_raw": obs.date_text_raw,
            "date_parse_status": obs.date_parse_status,
            "event_hour": obs.event_hour,
            "event_minute": obs.event_minute,
            "time_text_raw": obs.time_text_raw,
            "time_parse_status": obs.time_parse_status,
            "observation_type": obs.observation_type,
            "classification_method": obs.classification_method,
            "classification_confidence": obs.classification_confidence,
        },
    }


def write_geojson(observations: "list[NormalizedObservation]", path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    feature_collection = {
        "type": "FeatureCollection",
        "features": [_to_feature(obs) for obs in observations],
    }
    path.write_text(
        json.dumps(feature_collection, ensure_ascii=False, indent=2), encoding="utf-8"
    )
