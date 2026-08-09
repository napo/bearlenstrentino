from __future__ import annotations

from pipeline.normalization.dates import parse_event_date


def test_leading_full_date_is_parsed():
    parsed = parse_event_date("12/05/2024 - Un orso è stato avvistato ai margini del bosco.")
    assert parsed.event_date == "2024-05-12"
    assert parsed.event_year == 2024
    assert parsed.event_month == 5
    assert parsed.event_day == 12
    assert parsed.date_text_raw == "12/05/2024"
    assert parsed.date_parse_status == "full"


def test_leading_date_after_html_image_tag():
    text = '<img src="https://example.org/x.jpg" /><br><br>27/05/2026 - Una donna...'
    parsed = parse_event_date(text)
    assert parsed.date_parse_status == "full"
    assert parsed.event_date == "2026-05-27"


def test_parenthetical_leading_date():
    parsed = parse_event_date("Stenico (26/06/2026). Un escursionista attaccato.")
    assert parsed.date_parse_status == "full"
    assert parsed.event_date == "2026-06-26"


def test_incidental_second_date_does_not_override_leading_event_date():
    text = (
        "27/05/2026 - Una donna riprende un orso. La forestale conferma che "
        "l'orso era apparso nello stesso posto anche il 30/05/2026."
    )
    parsed = parse_event_date(text)
    assert parsed.event_date == "2026-05-27"
    assert parsed.date_parse_status == "full"


def test_tight_date_range_is_not_resolved_to_a_single_date():
    parsed = parse_event_date("27/05/2026-30/05/2026: presenza continuativa segnalata.")
    assert parsed.event_date is None
    assert parsed.date_parse_status == "range"
    assert parsed.date_text_raw == "27/05/2026-30/05/2026"


def test_dates_only_deep_in_text_are_ambiguous_not_guessed():
    text = "Testo lungo senza data all'inizio. " + "x" * 60 + " avvistato il 12/05/2024."
    parsed = parse_event_date(text)
    assert parsed.event_date is None
    assert parsed.date_parse_status == "ambiguous"


def test_month_and_year_without_day():
    parsed = parse_event_date("Segnalazione di giugno 2026 nei pressi del paese.")
    assert parsed.event_date is None
    assert parsed.event_year == 2026
    assert parsed.event_month == 6
    assert parsed.event_day is None
    assert parsed.date_parse_status == "year_month"


def test_day_month_without_year():
    parsed = parse_event_date("Avvistamento del 12/05, orario non precisato.")
    assert parsed.event_year is None
    assert parsed.event_month == 5
    assert parsed.event_day == 12
    assert parsed.date_parse_status == "day_month_no_year"


def test_year_only():
    parsed = parse_event_date("Un vecchio avvistamento risalente al 2019, dettagli incerti.")
    assert parsed.event_year == 2019
    assert parsed.date_parse_status == "year_only"


def test_no_date_at_all():
    parsed = parse_event_date("Nessuna informazione temporale in questo testo.")
    assert parsed.event_date is None
    assert parsed.date_parse_status == "not_present"


def test_empty_or_missing_description():
    assert parse_event_date(None).date_parse_status == "not_present"
    assert parse_event_date("   ").date_parse_status == "not_present"


def test_never_uses_scrape_timestamp_as_event_date():
    # Sanity check of the module's contract: parsing is a pure function of
    # the text only, it takes no "now"/fetch-timestamp argument at all.
    import inspect

    signature = inspect.signature(parse_event_date)
    assert list(signature.parameters) == ["description_raw"]
