from __future__ import annotations

from xml.etree import ElementTree as ET

from pipeline.acquisition.redact_kml import redact_kml_tree, serialize_kml
from pipeline.acquisition.validate import parse_kml
from pipeline.privacy.redactor import PiiRedactor


def test_redacts_names_across_all_placemarks_consistently(tmp_path, load_fixture):
    root = parse_kml(load_fixture("person_names.kml"))
    redactor = PiiRedactor(tmp_path / "name_mapping.csv")

    redacted_root, codes = redact_kml_tree(root, redactor)
    serialized = serialize_kml(redacted_root).decode("utf-8")

    assert "Mario Rossi" not in serialized
    assert "PERSON_0001" in serialized
    assert serialized.count("PERSON_0001") == 2  # same person, two placemarks
    assert "351 123 4567" not in serialized
    assert "Maso Fienile" in serialized  # place name, must not be redacted
    assert "Sopramonte di Trento" in serialized  # place name, must not be redacted
    assert len(set(codes)) == 2  # one PERSON code + one PHONE code

    # The original tree passed in must never be mutated in place.
    original_serialized = ET.tostring(root, encoding="unicode")
    assert "Mario Rossi" in original_serialized


def test_redaction_mapping_is_saved_for_later_reuse(tmp_path, load_fixture):
    root = parse_kml(load_fixture("person_names.kml"))
    mapping_path = tmp_path / "name_mapping.csv"
    redactor = PiiRedactor(mapping_path)

    redact_kml_tree(root, redactor)
    redactor.save()

    assert mapping_path.exists()
    content = mapping_path.read_text(encoding="utf-8")
    assert "PERSON_0001" in content
    assert "Mario Rossi" in content  # mapping file itself is private/gitignored
