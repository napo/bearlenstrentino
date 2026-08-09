from __future__ import annotations

from datetime import datetime, timezone

from pipeline.history.reconcile import reconcile
from pipeline.normalization.observations import NormalizedObservation

DAY1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
DAY2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
DAY3 = datetime(2026, 8, 3, tzinfo=timezone.utc)


def _obs(**overrides) -> NormalizedObservation:
    defaults = dict(
        id="obs_1",
        source_layer="Avvistamento a distanza",
        name_public="Bosco Alto",
        description_public="Un orso è stato avvistato ai margini del bosco.",
        longitude=11.0,
        latitude=46.0,
        coordinate_error=None,
        observation_type="sighting_direct",
        classification_confidence="high",
    )
    defaults.update(overrides)
    return NormalizedObservation(**defaults)


def test_brand_new_observation_is_added_with_first_seen_now():
    result = reconcile({}, [_obs()], as_of=DAY1)

    assert len(result.changes) == 1
    assert result.changes[0].kind == "added"
    [obs] = result.observations
    assert obs.first_seen_at == obs.last_seen_at == obs.source_changed_at == DAY1.isoformat()
    assert "obs_1" in result.new_state


def test_unchanged_observation_keeps_original_first_seen_at_across_runs():
    day1_result = reconcile({}, [_obs()], as_of=DAY1)
    day2_result = reconcile(day1_result.new_state, [_obs()], as_of=DAY2)

    [obs] = day2_result.observations
    assert obs.first_seen_at == DAY1.isoformat()
    assert obs.last_seen_at == DAY2.isoformat()
    assert obs.source_changed_at == DAY1.isoformat()  # content didn't change
    assert day2_result.changes == []  # no "modified" entry for an unchanged record


def test_modified_description_updates_source_changed_at_but_not_first_seen_at():
    day1_result = reconcile({}, [_obs()], as_of=DAY1)
    changed_obs = _obs(
        description_public="Un orso è stato avvistato ai margini del bosco, di sera."
    )

    day2_result = reconcile(day1_result.new_state, [changed_obs], as_of=DAY2)

    [obs] = day2_result.observations
    assert obs.first_seen_at == DAY1.isoformat()
    assert obs.source_changed_at == DAY2.isoformat()
    assert any(c.kind == "modified" and c.id == "obs_1" for c in day2_result.changes)


def test_missing_observation_becomes_candidate_removed_on_first_miss():
    day1_result = reconcile({}, [_obs()], as_of=DAY1)

    day2_result = reconcile(day1_result.new_state, [], as_of=DAY2)

    assert len(day2_result.changes) == 1
    assert day2_result.changes[0].kind == "candidate_removed"
    assert "obs_1" in day2_result.new_state  # still tracked, not dropped yet
    assert day2_result.observations == []


def test_observation_removed_after_two_consecutive_misses():
    day1_result = reconcile({}, [_obs()], as_of=DAY1)
    day2_result = reconcile(day1_result.new_state, [], as_of=DAY2)
    day3_result = reconcile(day2_result.new_state, [], as_of=DAY3)

    assert len(day3_result.changes) == 1
    assert day3_result.changes[0].kind == "removed"
    assert "obs_1" not in day3_result.new_state


def test_fuzzy_match_treats_small_coordinate_shift_as_modified_not_added_and_removed():
    original = _obs(id="obs_orig", longitude=11.00000, latitude=46.00000)
    day1_result = reconcile({}, [original], as_of=DAY1)

    # Same layer, near-identical description, coordinates nudged by ~1e-4
    # degrees (~10 m) — enough to change the id, not enough to be a
    # different real-world location.
    moved = _obs(
        id="obs_moved",
        longitude=11.00010,
        latitude=46.00005,
        description_public="Un orso è stato avvistato ai margini del bosco.",
    )
    day2_result = reconcile(day1_result.new_state, [moved], as_of=DAY2)

    kinds = [c.kind for c in day2_result.changes]
    assert kinds == ["modified"]
    assert day2_result.changes[0].previous_id == "obs_orig"
    [obs] = day2_result.observations
    assert obs.id == "obs_moved"
    assert obs.first_seen_at == DAY1.isoformat()  # carried forward, not reset


def test_fuzzy_match_does_not_cross_layers():
    original = _obs(id="obs_orig", source_layer="Predazioni", longitude=11.0, latitude=46.0)
    day1_result = reconcile({}, [original], as_of=DAY1)

    different_layer = _obs(
        id="obs_new",
        source_layer="Escrementi ambito abitato",
        longitude=11.00001,
        latitude=46.00001,
        description_public="Un orso è stato avvistato ai margini del bosco.",
    )
    day2_result = reconcile(day1_result.new_state, [different_layer], as_of=DAY2)

    kinds = sorted(c.kind for c in day2_result.changes)
    assert kinds == ["added", "candidate_removed"]


def test_content_hash_ignores_fields_outside_description_and_classification() -> None:
    # An id match with identical description/classification must never be
    # reported as modified, even if unrelated fields differ (e.g. media
    # links) — content_hash only covers description + observation_type +
    # classification_confidence.
    day1_result = reconcile({}, [_obs()], as_of=DAY1)
    same_content_different_media = _obs(
        media_links=["https://example.org/new-photo.jpg"]
    )

    day2_result = reconcile(day1_result.new_state, [same_content_different_media], as_of=DAY2)

    assert day2_result.changes == []
