"""Cross-run identity reconciliation (Milestone 4 scope, minus the GitHub
Actions scheduling — see README.md).

The observation `id` is a deterministic fingerprint of layer + raw name +
rounded coordinates (pipeline.normalization.observations._stable_id), so
an unchanged record gets the same id "for free" across runs — exact
identity match costs nothing here. This module handles the three cases
that actually require logic:

1. An id seen before, still present: was its content (description,
   classification) modified? If so, log it and refresh
   `source_changed_at` — but always carry forward the original
   `first_seen_at` rather than resetting it to today.
2. An id seen before, now missing, but a plausible match exists among
   today's new ids (same layer, within FUZZY_DISTANCE_M, similar
   description text): treat it as the same record with an updated
   name/coordinate rather than as "removed + added" — this is the
   conservative fuzzy fallback documented in AGENTS.md/REFERENCES.md.
3. An id seen before, now missing, with no plausible match: don't
   declare it "removed" after a single miss (a transient fetch problem
   shouldn't read as the source deleting data) — only after
   MAX_CONSECUTIVE_MISSES_BEFORE_REMOVED consecutive runs.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from datetime import datetime
from difflib import SequenceMatcher

from pipeline.history.state import ObservationState
from pipeline.normalization.observations import NormalizedObservation
from pipeline.normalization.text import strip_html

FUZZY_DISTANCE_M = 25.0
FUZZY_TEXT_THRESHOLD = 0.6
MAX_CONSECUTIVE_MISSES_BEFORE_REMOVED = 2


def _content_hash(obs: NormalizedObservation) -> str:
    # HTML-stripped: Google re-signs embedded image URLs (gx_media_links)
    # on every single export, even when nothing else about a Placemark
    # changed — hashing the raw HTML would flag every record as
    # "modified" on every run. See REFERENCES.md changelog / real-world
    # verification notes.
    description = strip_html(obs.description_public or "")
    payload = f"{description}|{obs.observation_type}|{obs.classification_confidence}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


@dataclass
class ChangeLogEntry:
    kind: str  # "added" | "removed" | "modified" | "candidate_removed"
    id: str
    previous_id: "str | None" = None
    detail: "str | None" = None


@dataclass
class ReconciliationResult:
    observations: "list[NormalizedObservation]"
    new_state: "dict[str, ObservationState]"
    changes: "list[ChangeLogEntry]"


def reconcile(
    previous_state: "dict[str, ObservationState]",
    observations: "list[NormalizedObservation]",
    *,
    as_of: datetime,
) -> ReconciliationResult:
    as_of_iso = as_of.isoformat()
    current_by_id = {obs.id: obs for obs in observations}
    matched_ids = set(current_by_id) & set(previous_state)
    new_ids = set(current_by_id) - set(previous_state)
    gone_ids = set(previous_state) - set(current_by_id)

    changes: list[ChangeLogEntry] = []
    new_state: dict[str, ObservationState] = {}
    updated_observations: dict[str, NormalizedObservation] = {}

    # 1. Exact id matches.
    for oid in matched_ids:
        obs = current_by_id[oid]
        prev = previous_state[oid]
        content_hash = _content_hash(obs)
        changed = content_hash != prev.content_hash
        source_changed_at = as_of_iso if changed else prev.source_changed_at
        if changed:
            changes.append(
                ChangeLogEntry(kind="modified", id=oid, detail="description or classification changed")
            )

        updated_observations[oid] = replace(
            obs,
            first_seen_at=prev.first_seen_at,
            last_seen_at=as_of_iso,
            source_changed_at=source_changed_at,
        )
        new_state[oid] = ObservationState(
            id=oid,
            source_layer=obs.source_layer,
            longitude=obs.longitude,
            latitude=obs.latitude,
            description_snapshot=(obs.description_public or "")[:200],
            content_hash=content_hash,
            first_seen_at=prev.first_seen_at,
            last_seen_at=as_of_iso,
            source_changed_at=source_changed_at,
            consecutive_misses=0,
        )

    # 2. Fuzzy fallback for ids that disappeared but plausibly just moved
    #    slightly or had their name tweaked.
    unresolved_new = set(new_ids)
    unresolved_gone: set[str] = set()
    for gone_id in gone_ids:
        prev = previous_state[gone_id]
        best_candidate: "str | None" = None
        best_similarity = 0.0

        for candidate_id in unresolved_new:
            candidate = current_by_id[candidate_id]
            if candidate.source_layer != prev.source_layer:
                continue
            if None in (prev.longitude, prev.latitude, candidate.longitude, candidate.latitude):
                continue
            distance = _haversine_m(prev.longitude, prev.latitude, candidate.longitude, candidate.latitude)  # type: ignore[arg-type]
            if distance > FUZZY_DISTANCE_M:
                continue
            similarity = _text_similarity(
                prev.description_snapshot or "", (candidate.description_public or "")[:200]
            )
            if similarity >= FUZZY_TEXT_THRESHOLD and similarity > best_similarity:
                best_candidate, best_similarity = candidate_id, similarity

        if best_candidate is None:
            unresolved_gone.add(gone_id)
            continue

        candidate = current_by_id[best_candidate]
        content_hash = _content_hash(candidate)
        updated_observations[best_candidate] = replace(
            candidate, first_seen_at=prev.first_seen_at, last_seen_at=as_of_iso, source_changed_at=as_of_iso
        )
        new_state[best_candidate] = ObservationState(
            id=best_candidate,
            source_layer=candidate.source_layer,
            longitude=candidate.longitude,
            latitude=candidate.latitude,
            description_snapshot=(candidate.description_public or "")[:200],
            content_hash=content_hash,
            first_seen_at=prev.first_seen_at,
            last_seen_at=as_of_iso,
            source_changed_at=as_of_iso,
            consecutive_misses=0,
        )
        changes.append(
            ChangeLogEntry(
                kind="modified",
                id=best_candidate,
                previous_id=gone_id,
                detail=f"matched by proximity/text similarity (similarity={best_similarity:.2f}); "
                "coordinates or name likely changed",
            )
        )
        unresolved_new.discard(best_candidate)

    # 3. Genuinely new records.
    for new_id in unresolved_new:
        obs = current_by_id[new_id]
        content_hash = _content_hash(obs)
        updated_observations[new_id] = replace(
            obs, first_seen_at=as_of_iso, last_seen_at=as_of_iso, source_changed_at=as_of_iso
        )
        new_state[new_id] = ObservationState(
            id=new_id,
            source_layer=obs.source_layer,
            longitude=obs.longitude,
            latitude=obs.latitude,
            description_snapshot=(obs.description_public or "")[:200],
            content_hash=content_hash,
            first_seen_at=as_of_iso,
            last_seen_at=as_of_iso,
            source_changed_at=as_of_iso,
            consecutive_misses=0,
        )
        changes.append(ChangeLogEntry(kind="added", id=new_id))

    # 4. Genuinely gone: only declared "removed" after repeated misses.
    for gone_id in unresolved_gone:
        prev = previous_state[gone_id]
        misses = prev.consecutive_misses + 1
        if misses >= MAX_CONSECUTIVE_MISSES_BEFORE_REMOVED:
            changes.append(
                ChangeLogEntry(kind="removed", id=gone_id, detail=f"missing for {misses} consecutive runs")
            )
        else:
            new_state[gone_id] = replace(prev, consecutive_misses=misses)
            changes.append(
                ChangeLogEntry(
                    kind="candidate_removed", id=gone_id, detail=f"missing for {misses} consecutive run(s)"
                )
            )

    final_observations = [updated_observations[obs.id] for obs in observations]
    return ReconciliationResult(observations=final_observations, new_state=new_state, changes=changes)
