from __future__ import annotations

from pipeline.history.state import ObservationState, load_state, save_state


def _sample_state(**overrides) -> ObservationState:
    defaults = dict(
        id="obs_aaaa",
        source_layer="Avvistamento a distanza",
        longitude=11.0,
        latitude=46.0,
        description_snapshot="Un orso è stato avvistato.",
        content_hash="deadbeef",
        first_seen_at="2026-08-01T00:00:00+00:00",
        last_seen_at="2026-08-01T00:00:00+00:00",
        source_changed_at="2026-08-01T00:00:00+00:00",
    )
    defaults.update(overrides)
    return ObservationState(**defaults)


def test_load_state_returns_empty_dict_when_file_missing(tmp_path):
    assert load_state(tmp_path / "state.json") == {}


def test_save_and_load_state_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    states = {"obs_aaaa": _sample_state(), "obs_bbbb": _sample_state(id="obs_bbbb", consecutive_misses=1)}

    save_state(path, states)
    loaded = load_state(path)

    assert set(loaded) == {"obs_aaaa", "obs_bbbb"}
    assert loaded["obs_bbbb"].consecutive_misses == 1
    assert loaded["obs_aaaa"].source_layer == "Avvistamento a distanza"
