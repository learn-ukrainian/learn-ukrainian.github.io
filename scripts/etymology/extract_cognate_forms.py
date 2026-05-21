"""Extract structured cognate forms from ESUM etymology entries."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path

try:
    from scripts.etymology.recover_latin_cognates import ensure_recovered_column, recover_cognate_forms
except ModuleNotFoundError:  # pragma: no cover - direct-script support
    from recover_latin_cognates import ensure_recovered_column, recover_cognate_forms

DEFAULT_DB = Path("data/sources.db")
DEFAULT_TELEMETRY = Path("audit/etymology-phase-1/cognate_extraction_coverage.json")
PROTO_MARKERS = ("псл.", "іє.", "стел.")
QUALIFIER_WORDS = {
    "арх",
    "вл",
    "вульг",
    "діал",
    "заст",
    "книжн",
    "місц",
    "нл",
    "розм",
    "ст",
}

FORM_TOKEN = r"\[?\*?[^\s,;\(\)\[\]«»\"\.]+(?:\s+\[?\*?[^\s,;\(\)\[\]«»\"\.]+)?"
QUALIFIER_PATTERN = "|".join(sorted(QUALIFIER_WORDS, key=len, reverse=True))
EXTRA_CLUSTER_MARKERS = {
    "аз",
    "вл",
    "дангл",
    "дісл",
    "іт",
    "каз",
    "крим",
    "м",
    "молд",
    "нім",
    "нвн",
    "нл",
    "полаб",
    "рум",
    "срн",
    "ст",
    "узб",
    "уйг",
    "фр",
}


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS esum_cognate_forms (
            entry_id INTEGER PRIMARY KEY,
            cognate_forms TEXT NOT NULL DEFAULT '{}',
            cognate_forms_recovered TEXT NOT NULL DEFAULT '{}',
            proto_form TEXT,
            extracted_count INTEGER NOT NULL DEFAULT 0,
            expected_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
        );
        CREATE INDEX IF NOT EXISTS idx_cognate_forms_entry
        ON esum_cognate_forms(entry_id);
        """
    )
    ensure_recovered_column(conn)


def _clean_form(raw_form: str) -> str:
    form = raw_form.strip().strip(",;")
    form = form.strip("[]")
    form = re.sub(r"\s+", " ", form)
    return form


def _is_bad_form(form: str, markers: set[str]) -> bool:
    normalized = form.strip("[]").strip()
    first_word = normalized.split(" ", maxsplit=1)[0]
    return first_word in QUALIFIER_WORDS or f"{first_word}." in markers


def _marker_pattern(marker: str) -> str:
    base = re.escape(marker.rstrip("."))
    return rf"{base}\s*[\.,]"


def _normalize_marker(raw_marker: str) -> str:
    compact = re.sub(r"\s+", "", raw_marker).rstrip(".,")
    return f"{compact}."


def _cluster_token_pattern(markers: set[str]) -> str:
    bases = {marker.rstrip(".") for marker in markers} | EXTRA_CLUSTER_MARKERS | QUALIFIER_WORDS
    return "|".join(re.escape(marker) for marker in sorted(bases, key=len, reverse=True))


def _direct_marker_matches(text: str, marker: str) -> Iterable[str]:
    pattern = re.compile(rf"(?<!\w){_marker_pattern(marker)}\s+(?:(?:{QUALIFIER_PATTERN})\.\s+)*({FORM_TOKEN})")
    for match in pattern.finditer(text):
        yield _clean_form(match.group(1))


def _marker_has_extractable_context(text: str, marker: str) -> bool:
    next_marker = r"(?=[A-Za-zА-Яа-яІіЇїЄєҐґ]{1,10}\s*[\.,])"
    pattern = re.compile(rf"(?<!\w){_marker_pattern(marker)}(?:\s+|{next_marker})")
    return bool(pattern.search(text))


def _cluster_marker_matches(text: str, markers: set[str]) -> Iterable[tuple[list[str], str]]:
    if not markers:
        return
    token_alt = _cluster_token_pattern(markers)
    cluster_re = re.compile(
        rf"(?<!\w)((?:(?:{token_alt})\s*[\.,]\s*){{1,12}})\s*"
        rf"(?:(?:{QUALIFIER_PATTERN})\.\s+)*({FORM_TOKEN})"
    )
    for match in cluster_re.finditer(text):
        cluster = [
            marker
            for raw_marker in re.findall(rf"((?:{token_alt}))\s*[\.,]", match.group(1))
            if (marker := _normalize_marker(raw_marker)) in markers
        ]
        form = _clean_form(match.group(2))
        if cluster and form:
            yield cluster, form


def extractable_markers_from_text(etymology_text: str, markers: list[str], forms: dict[str, str]) -> set[str]:
    """Return markers with an explicit marker-form context in the entry text."""

    return {marker for marker in markers if marker in forms or _marker_has_extractable_context(etymology_text, marker)}


def extract_forms_from_text(etymology_text: str, markers: list[str]) -> tuple[dict[str, str], str | None]:
    """Extract first observed cognate form for each marker in an ESUM entry."""

    marker_set = set(markers)
    forms: dict[str, str] = {}

    for cluster, form in _cluster_marker_matches(etymology_text, marker_set):
        if _is_bad_form(form, marker_set):
            continue
        for marker in cluster:
            forms.setdefault(marker, form)

    for marker in markers:
        if marker in forms:
            continue
        for form in _direct_marker_matches(etymology_text, marker):
            if not _is_bad_form(form, marker_set):
                forms[marker] = form
                break

    proto_form = next((forms[marker] for marker in PROTO_MARKERS if marker in forms), None)
    return forms, proto_form


def _load_markers(cognates_json: str) -> list[str]:
    try:
        decoded = json.loads(cognates_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return [marker for marker in decoded if isinstance(marker, str) and marker]


def extract_database(db_path: Path, telemetry_path: Path, min_coverage_pct: float = 65.0) -> dict[str, object]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        create_schema(conn)
        rows = conn.execute(
            """
            SELECT id, etymology_text, cognates
            FROM esum_etymology_meta
            ORDER BY id
            """
        ).fetchall()

        marker_declared_expected: Counter[str] = Counter()
        marker_extractable_expected: Counter[str] = Counter()
        marker_extracted: Counter[str] = Counter()
        entries_with_declared_markers = 0
        entries_with_forms = 0
        total_forms = 0

        with conn:
            for row in rows:
                markers = _load_markers(row["cognates"])
                if markers:
                    entries_with_declared_markers += 1
                marker_declared_expected.update(markers)
                forms, proto_form = extract_forms_from_text(row["etymology_text"], markers)
                extractable_markers = extractable_markers_from_text(row["etymology_text"], markers, forms)
                marker_extractable_expected.update(extractable_markers)
                if forms:
                    entries_with_forms += 1
                total_forms += len(forms)
                marker_extracted.update(forms.keys())
                recovered_forms = recover_cognate_forms(forms)
                conn.execute(
                    """
                    INSERT INTO esum_cognate_forms (
                        entry_id, cognate_forms, cognate_forms_recovered,
                        proto_form, extracted_count, expected_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entry_id) DO UPDATE SET
                        cognate_forms = excluded.cognate_forms,
                        cognate_forms_recovered = excluded.cognate_forms_recovered,
                        proto_form = excluded.proto_form,
                        extracted_count = excluded.extracted_count,
                        expected_count = excluded.expected_count
                    """,
                    (
                        row["id"],
                        json.dumps(forms, ensure_ascii=False, sort_keys=True),
                        json.dumps(recovered_forms, ensure_ascii=False, sort_keys=True),
                        proto_form,
                        len(forms),
                        len(markers),
                    ),
                )

        per_marker = {}
        per_marker_declared = {}
        for marker in sorted(marker_declared_expected):
            expected = marker_extractable_expected[marker]
            extracted = marker_extracted[marker]
            per_marker[marker] = {
                "expected": expected,
                "extracted": extracted,
                "pct": round((extracted / expected * 100) if expected else 0.0, 2),
            }
            declared_expected = marker_declared_expected[marker]
            extracted = marker_extracted[marker]
            per_marker_declared[marker] = {
                "expected": declared_expected,
                "extracted": extracted,
                "pct": round((extracted / declared_expected * 100) if declared_expected else 0.0, 2),
            }

        coverage_pct = round(
            (entries_with_forms / entries_with_declared_markers * 100) if entries_with_declared_markers else 0.0,
            2,
        )
        telemetry: dict[str, object] = {
            "entries_processed": len(rows),
            "entries_with_declared_markers": entries_with_declared_markers,
            "entries_with_at_least_one_form": entries_with_forms,
            "total_forms_extracted": total_forms,
            "coverage_pct": coverage_pct,
            "all_entries_coverage_pct": round((entries_with_forms / len(rows) * 100) if rows else 0.0, 2),
            "per_marker_coverage": per_marker,
            "per_marker_declared_coverage": per_marker_declared,
        }

        telemetry_path.parent.mkdir(parents=True, exist_ok=True)
        telemetry_path.write_text(json.dumps(telemetry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        if coverage_pct < min_coverage_pct:
            raise RuntimeError(f"Cognate extraction coverage {coverage_pct}% is below {min_coverage_pct}%")

        return telemetry
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--telemetry", type=Path, default=DEFAULT_TELEMETRY)
    parser.add_argument("--min-coverage-pct", type=float, default=65.0)
    args = parser.parse_args()

    telemetry = extract_database(args.db, args.telemetry, args.min_coverage_pct)
    print(json.dumps(telemetry, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
