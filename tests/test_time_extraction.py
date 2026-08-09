from __future__ import annotations

from pipeline.normalization.time_extraction import parse_event_time


def test_exact_time_with_colon():
    parsed = parse_event_time("18/07/2026. Ore 19:47. Orso si serve in un frutteto.")
    assert parsed.event_hour == 19
    assert parsed.event_minute == 47
    assert parsed.time_text_raw == "Ore 19:47"
    assert parsed.time_parse_status == "exact"


def test_exact_time_with_dot_separator():
    parsed = parse_event_time("Sopramonte di Trento. Alle 11.00 un ragazzino...")
    assert parsed.event_hour == 11
    assert parsed.event_minute == 0
    assert parsed.time_parse_status == "exact"


def test_approximate_time_verso_le():
    parsed = parse_event_time("Verso le 13, una giovane turista si imbatte in un'orsa.")
    assert parsed.event_hour == 13
    assert parsed.event_minute is None
    assert parsed.time_parse_status == "approximate"


def test_approximate_time_alle_ore_no_minutes():
    parsed = parse_event_time("L'evento e' avvenuto alle ore 20 nei pressi del paese.")
    assert parsed.event_hour == 20
    assert parsed.time_parse_status == "approximate"


def test_no_time_present():
    parsed = parse_event_time("Un orso e' stato avvistato ai margini del bosco.")
    assert parsed.event_hour is None
    assert parsed.time_parse_status == "not_present"


def test_empty_or_missing_description():
    assert parse_event_time(None).time_parse_status == "not_present"
    assert parse_event_time("   ").time_parse_status == "not_present"


def test_exact_takes_priority_over_approximate_when_both_could_match():
    # "alle 7:30" must be read as exact (7:30), not fall through to the
    # approximate "alle" pattern and lose the minutes.
    parsed = parse_event_time("La mattina alle 7:30 un cucciolo ha attraversato la strada.")
    assert parsed.event_hour == 7
    assert parsed.event_minute == 30
    assert parsed.time_parse_status == "exact"


def test_invalid_hour_is_rejected_not_guessed():
    parsed = parse_event_time("Alle 47:00 e' successo qualcosa.")
    assert parsed.time_parse_status == "not_present"
