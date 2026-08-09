from __future__ import annotations

from pipeline.normalization.classification import classify_observation


def test_unambiguous_layer_wins_with_high_confidence():
    result = classify_observation("Escrementi ambito abitato", "Trovati escrementi sul sentiero.")
    assert result.observation_type == "scat"
    assert result.classification_method == "source_layer"
    assert result.classification_confidence == "high"


def test_camera_trap_layer():
    result = classify_observation(
        "Fototrappolaggio (abitati-siti agricoli)", "Immagine catturata di notte."
    )
    assert result.observation_type == "camera_trap"
    assert result.classification_method == "source_layer"


def test_camera_trap_layer_survives_source_renaming_the_folder():
    # The live source has been observed to rename this folder from
    # "Fototrappolaggio (abitati-siti agricoli)" to just "Fototrappolaggio"
    # — substring matching on the stable keyword must survive that drift.
    result = classify_observation("Fototrappolaggio", "")
    assert result.observation_type == "camera_trap"
    assert result.classification_method == "source_layer"


def test_vehicle_collision_layer():
    result = classify_observation("Incidenti stradali", "Incidente stradale, nessun ferito.")
    assert result.observation_type == "vehicle_collision"
    assert result.classification_method == "source_layer"


def test_predation_layer():
    result = classify_observation("Predazioni", "Danno a un allevamento di pecore.")
    assert result.observation_type == "predation_evidence"
    assert result.classification_method == "source_layer"


def test_ambiguous_layer_falls_back_to_text_heuristic():
    result = classify_observation("Presso le case", "Trovate delle impronte nel fango.")
    assert result.observation_type == "tracks_or_signs"
    assert result.classification_method == "text_heuristic"
    assert result.classification_confidence == "low"


def test_track_only_text_is_never_classified_as_direct_sighting():
    result = classify_observation(None, "Rinvenute orme e tracce di passaggio, nessun avvistamento.")
    assert result.observation_type == "tracks_or_signs"


def test_unknown_layer_and_uninformative_text_yields_unknown():
    result = classify_observation("Layer sconosciuto", "Testo generico senza indizi.")
    assert result.observation_type == "unknown"
    assert result.classification_method == "unknown"
    assert result.classification_confidence == "unknown"


def test_missing_layer_and_description_yields_unknown():
    result = classify_observation(None, None)
    assert result.observation_type == "unknown"


def test_confidence_is_never_presented_as_a_probability():
    # Contract check: confidence must be one of the qualitative buckets,
    # never a float (see AGENTS.md — no fabricated statistics).
    result = classify_observation("Predazioni", "x")
    assert result.classification_confidence in {"high", "medium", "low", "unknown"}
