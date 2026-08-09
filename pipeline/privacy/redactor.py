"""Conservative, deterministic redaction of person names and phone numbers.

This module implements the ONLY sanctioned transformation of source text
content in the whole pipeline (see AGENTS.md, "conservazione del dato
originale"). It is intentionally biased towards over-redaction: a false
positive (a place name mistaken for a person) produces a harmless code in
public text; a false negative (a missed real name) is a privacy leak. When
in doubt, this module redacts.

Limitations (documented, not hidden):

- Only sequences of 2+ consecutive Title-Case tokens are treated as
  candidate person names; lone first names, nicknames, and initials are
  NOT caught by this heuristic.
- The exclusion list of toponym/designator prefixes (Malga, Maso, Monte,
  San...) is a small, hand-curated set for the Trentino/Italian context
  and will need extending as new false positives are found in real data.
- Matching a new mention to an already-known code is by exact
  case-insensitive string match against previously seen variants;
  spelling variants of the same person's name are not automatically
  unified (each distinct spelling gets its own code unless it exactly
  matches a stored variant).
- This is not an NLP model. It will not catch names that don't look like
  "Firstname Lastname" (e.g. a single first name, a nickname, an
  initial), and it may occasionally redact a two-word proper noun that is
  neither a place nor a person.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

_TITLE_TOKEN = r"[A-ZÀ-ÖÙ-Ý][a-zà-öù-ÿ'’]+"
_PERSON_NAME_RE = re.compile(rf"(?:{_TITLE_TOKEN}\s+){{1,3}}{_TITLE_TOKEN}")

# Matches runs of 9-13 digits, allowing spaces/dots/slashes/hyphens as
# separators. Deliberately requires >=9 digits so that DD/MM/YYYY dates
# (8 digits) are never mistaken for a phone number.
_PHONE_RE = re.compile(r"(?:\+39\s?)?(?:\d[\s./-]?){8,12}\d")

# If the FIRST token of a matched 2+ Title-Case sequence is one of these
# (lowercased), treat the whole sequence as a place/feature/business name
# rather than a person, e.g. "Maso Camponzin", "Hotel Scoiattolo", "Bar La
# Perla", "Zona Fontana Fila". These are locations and businesses that
# reports commonly and openly refer to by name (streets, hotels, bars,
# zones) — deliberately kept public rather than redacted, per project
# decision: only person names and contact details are pseudonymized, not
# place/business references. Small and Trentino-specific by design:
# extend as new false positives emerge in real data, rather than trying
# to be exhaustive up front.
_PLACE_PREFIXES = {
    "malga", "maso", "monte", "passo", "lago", "rio", "val", "valle",
    "localita", "località", "loc", "via", "piazza", "parco", "cima",
    "doss", "dos", "pian", "piano", "colle", "rifugio", "baita", "forra",
    "bosco", "prato", "orto", "sorgente", "cascata", "sella", "malghe",
    "comune", "provincia", "trentino", "san", "santa", "sant", "ponte",
    "villa", "borgo", "castel", "castello", "zona", "strada", "fontana",
    "campo", "pista", "hotel", "bar", "ristorante", "residence", "camping",
    "agritur", "agriturismo", "albergo", "pensione", "trattoria",
    "pizzeria", "vecchio", "vecchia", "nuovo", "nuova",
    "alla", "allo", "alle", "ai", "al", "dei", "degli", "delle",
}

_CODE_PREFIXES = {"person": "PERSON", "phone": "PHONE"}


@dataclass
class _MappingEntry:
    code: str
    variants: set[str] = field(default_factory=set)


class PiiRedactor:
    """Detects candidate person names and phone numbers and replaces them
    with stable codes, backed by a local CSV mapping file.

    The mapping file must never be committed to version control (see
    AGENTS.md / README.md) — it is the only place the real names live.
    """

    def __init__(self, mapping_path: Path):
        self._mapping_path = mapping_path
        self._by_code: dict[str, _MappingEntry] = {}
        self._by_variant: dict[str, str] = {}  # lowercase variant -> code
        self._load()

    def _load(self) -> None:
        if not self._mapping_path.exists():
            return
        with self._mapping_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                code = row["code"]
                variants = {v.strip() for v in row["variants"].split(";") if v.strip()}
                entry = self._by_code.setdefault(code, _MappingEntry(code=code))
                entry.variants |= variants
                for variant in variants:
                    self._by_variant[variant.lower()] = code

    def save(self) -> None:
        self._mapping_path.parent.mkdir(parents=True, exist_ok=True)
        with self._mapping_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["code", "variants"])
            for entry in self._by_code.values():
                writer.writerow([entry.code, ";".join(sorted(entry.variants))])

    def _next_code(self, kind: str) -> str:
        prefix = _CODE_PREFIXES[kind]
        existing_numbers = [
            int(code.split("_")[1])
            for code in self._by_code
            if code.startswith(prefix + "_")
        ]
        return f"{prefix}_{max(existing_numbers, default=0) + 1:04d}"

    def _code_for(self, text: str, kind: str) -> str:
        key = text.lower()
        code = self._by_variant.get(key)
        if code is None:
            code = self._next_code(kind)
            self._by_code[code] = _MappingEntry(code=code, variants={text})
            self._by_variant[key] = code
        else:
            self._by_code[code].variants.add(text)
        return code

    @staticmethod
    def _is_place_like(matched_text: str) -> bool:
        first_token = matched_text.split()[0].lower()
        return first_token in _PLACE_PREFIXES

    def redact(self, text: str) -> "tuple[str, list[str]]":
        """Return (redacted_text, codes_used_in_order_of_first_appearance)."""
        codes_used: list[str] = []

        def _replace_phone(match: re.Match[str]) -> str:
            candidate = match.group(0)
            digits = re.sub(r"\D", "", candidate)
            if len(digits) < 9:
                return candidate
            code = self._code_for(digits, "phone")
            codes_used.append(code)
            return code

        def _replace_person(match: re.Match[str]) -> str:
            candidate = match.group(0)
            if self._is_place_like(candidate):
                return candidate
            code = self._code_for(candidate, "person")
            codes_used.append(code)
            return code

        # Phone numbers first: their digit runs could otherwise interfere
        # with adjacent text once names are replaced by PERSON_NNNN codes.
        redacted = _PHONE_RE.sub(_replace_phone, text)
        redacted = _PERSON_NAME_RE.sub(_replace_person, redacted)
        return redacted, codes_used
