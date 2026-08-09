"""Milestone 3: conservative observation-type classification.

Prefers the source's own folder (`source_layer`) when it unambiguously
names an evidence type (e.g. "Escrementi ambito abitato" -> scat); falls
back to keyword matching on the free-text description when the layer
only describes spatial/narrative context and says nothing about what was
actually observed (e.g. "Presso le case" — near houses).

`classification_confidence` is a qualitative flag (high/medium/low/
unknown), not a calibrated statistical probability — never present it as
one (see AGENTS.md).

Specific evidence keywords (tracks, scat, camera-trap, collision,
predation) are checked before generic sighting verbs, so a description
that only mentions a track or a footprint is never classified as
`sighting_direct` just because it also contains an incidental word like
"visto" elsewhere.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Folders whose name alone unambiguously names the evidence type, per
# inspection of the real source map (see REFERENCES.md, Milestone 3 row).
# Matched by substring, not exact equality: the source has been observed
# to rename folders slightly over time (e.g. "Fototrappolaggio" vs.
# "Fototrappolaggio (abitati-siti agricoli)") — substring matching on the
# stable keyword survives that drift. Folder names not listed here (e.g.
# "Presso le case", which describes location, not evidence) fall through
# to the text heuristic below.
_LAYER_KEYWORDS: "list[tuple[str, str, str]]" = [
    ("escrementi", "scat", "high"),
    ("fototrappol", "camera_trap", "high"),
    ("incidenti stradali", "vehicle_collision", "high"),
    ("predazioni", "predation_evidence", "high"),
    ("avvistamento a distanza", "sighting_direct", "high"),
    ("avvistamento orsa", "sighting_direct", "high"),
    ("incontri ravvicinati", "sighting_direct", "high"),
]

# Order matters: more specific evidence types are checked first so they
# take priority over generic sighting verbs mentioned in the same text.
_TEXT_KEYWORDS: "list[tuple[re.Pattern[str], str]]" = [
    (re.compile(r"fototrappol", re.IGNORECASE), "camera_trap"),
    (re.compile(r"\bescrement", re.IGNORECASE), "scat"),
    (re.compile(r"\bpel[oi]\b", re.IGNORECASE), "hair"),
    (re.compile(r"\bimpront[ae]|\borme\b|\btracc", re.IGNORECASE), "tracks_or_signs"),
    (re.compile(r"\bincidente|\binvestit", re.IGNORECASE), "vehicle_collision"),
    (
        re.compile(r"predaz|sbranat|sbranaz|uccis[oi] (?:un |una )?(?:capr|pecor|vitell)", re.IGNORECASE),
        "predation_evidence",
    ),
    (re.compile(r"avvist|ripres[oa]|\bvist[oa]\b|\bvideo\b|filmat", re.IGNORECASE), "sighting_direct"),
]


@dataclass
class Classification:
    observation_type: str = "unknown"
    classification_method: str = "unknown"
    classification_confidence: str = "unknown"


def _classify_from_text(description_raw: "str | None") -> "tuple[str, str] | None":
    if not description_raw:
        return None
    for pattern, obs_type in _TEXT_KEYWORDS:
        if pattern.search(description_raw):
            return obs_type, "low"
    return None


def classify_observation(
    source_layer: "str | None", description_raw: "str | None"
) -> Classification:
    layer_key = (source_layer or "").strip().lower()
    for keyword, obs_type, confidence in _LAYER_KEYWORDS:
        if keyword in layer_key:
            return Classification(
                observation_type=obs_type,
                classification_method="source_layer",
                classification_confidence=confidence,
            )

    text_result = _classify_from_text(description_raw)
    if text_result:
        obs_type, confidence = text_result
        return Classification(
            observation_type=obs_type,
            classification_method="text_heuristic",
            classification_confidence=confidence,
        )

    return Classification()
