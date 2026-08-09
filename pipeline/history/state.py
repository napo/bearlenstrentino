"""Persistent per-observation state used to reconcile identity across
pipeline runs (see pipeline.history.reconcile).

Stored publicly (data/history/state.json): it contains no personal data,
only ids, coordinates, a redacted description snippet, and timestamps —
everything here is already safe to publish (see AGENTS.md).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ObservationState:
    id: str
    source_layer: "str | None"
    longitude: "float | None"
    latitude: "float | None"
    description_snapshot: "str | None"
    content_hash: str
    first_seen_at: str
    last_seen_at: str
    source_changed_at: str
    consecutive_misses: int = field(default=0)


def load_state(path: Path) -> "dict[str, ObservationState]":
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: ObservationState(**item) for item in raw}


def save_state(path: Path, state: "dict[str, ObservationState]") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(s) for s in state.values()]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
