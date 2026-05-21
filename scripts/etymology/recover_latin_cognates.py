"""Recover Latin-script ESUM cognate forms damaged as Cyrillic OCR text."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

DEFAULT_DB = Path("data/sources.db")

CYRILLIC_SCRIPT_MARKERS = {
    "р.",
    "бр.",
    "др.",
    "болг.",
    "схв.",
    "слн.",
    "мак.",
    "срб.",
    "церк.-сл.",
    "прасл.",
    "псл.",
    "стел.",
    "укр.",
}

NON_CYRILLIC_SCRIPT_MARKERS = {
    "п.",
    "ч.",
    "слц.",
    "вл.",
    "нл.",
    "полаб.",
    "лит.",
    "латиш.",
    "прус.",
    "лат.",
    "гр.",
    "рум.",
    "угор.",
    "нвн.",
    "н.",
    "дангл.",
    "англ.",
    "двн.",
    "гот.",
    "фр.",
    "іт.",
    "ісп.",
    "тур.",
    "тат.",
    "тюрк.",
    "чу́в.",
    "чув.",
    "узб.",
    "туркм.",
    "башк.",
    "ягноб.",
    "ар.",
    "євр.",
    "ід.",
    "іє.",
    "дінд.",
    "ав.",
    "лтс.",
    "перс.",
}

# Longer OCR clusters that need context. These are applied before the
# character table so ambiguous glyphs such as г and і can resolve differently
# inside known Latin clusters (rdz, -nty-, -nti-, -str-).
SEQUENCE_CONFUSIONS: tuple[tuple[str, str], ...] = (
    ("пії", "nti"),
    ("піу", "nty"),
    ("ПІЇ", "NTI"),
    ("ПІУ", "NTY"),
    ("бей", "dce"),
    ("БЕЙ", "DCE"),
    ("дг", "dz"),
    ("ДГ", "DZ"),
    ("зку", "sty"),
    ("ЗКУ", "STY"),
    ("зіг", "str"),
    ("ЗІГ", "STR"),
    ("с^", "cj"),
    ("С^", "Cj"),
    ("ійК", "juk"),
    ("ійк", "juk"),
    ("аша", "awia"),
)

CONFUSIONS: dict[str, str] = {
    "5": "s",
    "8": "s",
    "0": "o",
    "1": "l",
    "а": "a",
    "А": "A",
    "б": "d",
    "Б": "D",
    "в": "b",
    "В": "B",
    "г": "r",
    "Г": "R",
    "д": "d",
    "Д": "D",
    "е": "e",
    "Е": "E",
    "з": "s",
    "З": "S",
    "и": "u",
    "И": "U",
    "і": "i",
    "І": "l",  # ABBYY uses U+0406 for Latin small l in forms like аІІаЬеіа.
    "ї": "i",
    "Ї": "I",
    "й": "j",
    "Й": "J",
    "к": "k",
    "К": "K",
    "л": "l",
    "Л": "L",
    "м": "m",
    "М": "M",
    "н": "n",
    "Н": "N",
    "о": "o",
    "О": "O",
    "п": "n",
    "П": "N",
    "р": "p",
    "Р": "P",
    "с": "c",
    "С": "C",
    "т": "m",
    "Т": "M",
    "у": "y",
    "У": "Y",
    "ф": "f",
    "Ф": "F",
    "х": "h",
    "Х": "H",
    "ц": "c",
    "Ц": "C",
    "ч": "ch",
    "Ч": "Ch",
    "ш": "m",
    "Ш": "M",
    "щ": "w",
    "Щ": "W",
    "ь": "b",
    "Ь": "b",
    "ю": "u",
    "Ю": "U",
    "я": "ia",
    "Я": "Ia",
}


def normalize_marker(marker: str) -> str:
    """Normalize ESUM marker spacing enough for script-scope checks."""

    return re.sub(r"\s+", "", marker).strip()


def should_recover_marker(marker: str) -> bool:
    """Return True for language markers whose cognate form should be Latinized."""

    normalized = normalize_marker(marker)
    if normalized in CYRILLIC_SCRIPT_MARKERS:
        return False
    if normalized in NON_CYRILLIC_SCRIPT_MARKERS:
        return True

    parts = re.findall(r"[^\s]+?\.", marker)
    if len(parts) > 1:
        return all(should_recover_marker(part) for part in parts)

    return False


def _is_latin_char(char: str) -> bool:
    if "A" <= char <= "Z" or "a" <= char <= "z":
        return True
    return "LATIN" in unicodedata.name(char, "")


def _is_plausible_latin(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False

    latin_letters = sum(1 for char in letters if _is_latin_char(char))
    cyrillic_letters = sum(1 for char in letters if "CYRILLIC" in unicodedata.name(char, ""))
    if latin_letters / len(letters) < 0.8:
        return False
    if cyrillic_letters:
        return False

    meaningful = sum(1 for char in text if char.isalpha() or char in {"-", "'", "’", "ˊ", "ˈ", " "})
    return meaningful / max(len(text), 1) >= 0.7


def _has_recoverable_damage(text: str) -> bool:
    return any(char in CONFUSIONS for char in text)


def recover_latin(text: str) -> str:
    """Return a plausible Latin recovery candidate, or the original text."""

    if not text:
        return text
    if not _has_recoverable_damage(text):
        return text

    recovered = text
    for damaged, replacement in SEQUENCE_CONFUSIONS:
        recovered = recovered.replace(damaged, replacement)
    recovered = "".join(CONFUSIONS.get(char, char) for char in recovered)
    recovered = re.sub(r"\s+", " ", recovered).strip()

    if _is_plausible_latin(recovered):
        return recovered
    return text


def recover_cognate_forms(cognate_forms: dict[str, Any]) -> dict[str, str]:
    """Recover eligible cognate forms while leaving Cyrillic-script markers out."""

    recovered: dict[str, str] = {}
    for marker, form in cognate_forms.items():
        if not isinstance(marker, str) or not isinstance(form, str):
            continue
        if not should_recover_marker(marker):
            continue
        candidate = recover_latin(form)
        if _is_plausible_latin(candidate):
            recovered[marker] = candidate
    return recovered


def ensure_recovered_column(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(esum_cognate_forms)")}
    if "cognate_forms_recovered" not in columns:
        conn.execute("ALTER TABLE esum_cognate_forms ADD COLUMN cognate_forms_recovered TEXT NOT NULL DEFAULT '{}'")


def _load_forms(raw_json: str) -> dict[str, Any]:
    try:
        decoded = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def recover_database(db_path: Path, dry_run: bool = False) -> dict[str, int | float]:
    """Populate esum_cognate_forms.cognate_forms_recovered from cognate_forms."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if not dry_run:
            ensure_recovered_column(conn)

        rows = conn.execute(
            """
            SELECT entry_id, cognate_forms
            FROM esum_cognate_forms
            ORDER BY entry_id
            """
        ).fetchall()

        entries_with_eligible = 0
        entries_with_recovered = 0
        recovered_forms_total = 0

        updates: list[tuple[str, int]] = []
        for row in rows:
            forms = _load_forms(row["cognate_forms"])
            if any(should_recover_marker(marker) for marker in forms):
                entries_with_eligible += 1
            recovered = recover_cognate_forms(forms)
            if recovered:
                entries_with_recovered += 1
                recovered_forms_total += len(recovered)
            updates.append((json.dumps(recovered, ensure_ascii=False, sort_keys=True), row["entry_id"]))

        if not dry_run:
            with conn:
                conn.executemany(
                    """
                    UPDATE esum_cognate_forms
                    SET cognate_forms_recovered = ?
                    WHERE entry_id = ?
                    """,
                    updates,
                )

        coverage_pct = round(
            (entries_with_recovered / entries_with_eligible * 100) if entries_with_eligible else 0.0,
            2,
        )
        return {
            "rows_processed": len(rows),
            "entries_with_non_cyrillic_markers": entries_with_eligible,
            "entries_with_recovered_latin": entries_with_recovered,
            "recovered_forms_total": recovered_forms_total,
            "coverage_pct": coverage_pct,
        }
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    stats = recover_database(args.db, dry_run=args.dry_run)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
