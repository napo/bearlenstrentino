from __future__ import annotations

from pipeline.privacy.redactor import PiiRedactor


def test_redacts_person_name_and_reuses_same_code_for_repeat_mention(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")

    text1, codes1 = redactor.redact("Una donna, Mario Rossi, ha visto l'orso.")
    text2, codes2 = redactor.redact("Mario Rossi conferma l'avvistamento.")

    assert "Mario Rossi" not in text1
    assert "Mario Rossi" not in text2
    assert codes1 == codes2 == ["PERSON_0001"]
    assert "PERSON_0001" in text1 and "PERSON_0001" in text2


def test_does_not_redact_known_place_name_prefixes(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    text, codes = redactor.redact("L'orso è stato visto vicino a Maso Fienile.")
    assert "Maso Fienile" in text
    assert codes == []


def test_does_not_redact_place_name_with_lowercase_connector(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    text, codes = redactor.redact("Avvistamento vicino a Sopramonte di Trento.")
    assert "Sopramonte di Trento" in text
    assert codes == []


def test_does_not_redact_businesses_streets_and_zones(tmp_path):
    # Streets, hotels, bars and zones are what reports commonly and openly
    # refer to — the project keeps these public, only person names and
    # contact details are pseudonymized.
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    cases = [
        "L'orso è stato visto vicino a Hotel Scoiattolo.",
        "Avvistamento segnalato al Bar La Perla.",
        "Nei pressi di Campo Carlo Magno.",
        "Zona Fontana Fila interessata da un passaggio.",
        "L'evento è avvenuto in Strada Brigolina.",
        "Fototrappola posizionata presso Agritur Ai Castioni.",
    ]
    for text in cases:
        redacted, codes = redactor.redact(text)
        assert redacted == text
        assert codes == []


def test_redacts_phone_number(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    text, codes = redactor.redact("Per segnalazioni chiamare 351 123 4567.")
    assert "351 123 4567" not in text
    assert len(codes) == 1
    assert codes[0].startswith("PHONE_")


def test_does_not_mistake_a_date_for_a_phone_number(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    text, codes = redactor.redact("Avvistamento del 27/05/2026 confermato.")
    assert "27/05/2026" in text
    assert codes == []


def test_mapping_persists_across_instances(tmp_path):
    mapping_path = tmp_path / "name_mapping.csv"

    redactor1 = PiiRedactor(mapping_path)
    redactor1.redact("Mario Rossi ha segnalato l'orso.")
    redactor1.save()

    redactor2 = PiiRedactor(mapping_path)
    text, codes = redactor2.redact("Mario Rossi conferma.")
    assert codes == ["PERSON_0001"]
    assert "Mario Rossi" not in text


def test_different_people_get_different_codes(tmp_path):
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")
    _, codes1 = redactor.redact("Mario Rossi ha visto l'orso.")
    _, codes2 = redactor.redact("Anna Bianchi conferma l'avvistamento.")
    assert codes1 != codes2
