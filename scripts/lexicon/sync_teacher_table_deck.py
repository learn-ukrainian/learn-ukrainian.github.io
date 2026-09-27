"""Sync the Combined Master Vocabulary Table into the public Practice special set.

The source document remains private.  This module deliberately reads only the
table immediately following the exact requested heading; it is not a general
document-vocabulary miner.

Besides the legacy lemma-only special set, the table sync produces the deck
entries used by the teacher practice shard (#8843): one entry per normalised
Ukrainian key, with the teacher's English, the source rows, a stable entry id
derived from the normalised key only, and a ``firstSeen`` order key that is
carried forward from the previous published deck.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}
DOCUMENT_XML = "word/document.xml"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SITE_DATA_PATH = PROJECT_ROOT / "site/src/data/lexicon-teacher-table-deck.json"
SCHEMA = "lexicon-teacher-table-deck-v1"
DECK_ID = "virtual_teacher_table"
TITLE = "Dev's example deck"
TITLE_UK = "Приклад розробника"
DESCRIPTION = "Shared example from the developer's classroom list."
HEADING = "Combined Master Vocabulary Table (#3)"
FROZEN_KEYS_SCHEMA = "teacher-table-frozen-keys"
FROZEN_KEYS_SCHEMA_VERSION = 1
ENTRY_ID_PREFIX = "tt-"
STRESS_MARKS = frozenset({"\u0301", "\u0300"})
APOSTROPHE_VARIANTS = str.maketrans(
    {"\u2019": "'", "\u02bc": "'", "\u2018": "'", "`": "'", "\u00b4": "'", "\u2032": "'"}
)


class TeacherTableSyncError(ValueError):
    """The supplied DOCX does not satisfy the narrowly-scoped source contract."""


@dataclass(frozen=True)
class TeacherTableReport:
    raw_data_rows: int
    unique_uk: int
    multiword: int
    first5: list[str]
    last5: list[str]
    sha256_docx: str


def _normalize_text(value: str) -> str:
    """Collapse Word's layout whitespace without splitting a multiword expression."""

    return " ".join(value.split())


def _paragraph_text(paragraph: ET.Element) -> str:
    return "".join(text.text or "" for text in paragraph.findall(".//w:t", NS))


def _cell_text(cell: ET.Element) -> str:
    paragraphs = [_normalize_text(_paragraph_text(paragraph)) for paragraph in cell.findall("./w:p", NS)]
    return _normalize_text(" ".join(paragraph for paragraph in paragraphs if paragraph))


def _row_cells(row: ET.Element) -> list[str]:
    return [_cell_text(cell) for cell in row.findall("./w:tc", NS)]


def _find_target_table(document_xml: bytes, heading: str) -> ET.Element:
    try:
        root = ET.fromstring(document_xml)
    except ET.ParseError as exc:
        raise TeacherTableSyncError(f"{DOCUMENT_XML} is not valid XML") from exc

    body = root.find("w:body", NS)
    if body is None:
        raise TeacherTableSyncError(f"{DOCUMENT_XML} has no document body")

    heading_index: int | None = None
    for index, child in enumerate(list(body)):
        if child.tag == f"{{{WORD_NS}}}p" and _paragraph_text(child) == heading:
            heading_index = index
            break

    if heading_index is None:
        raise TeacherTableSyncError(f"exact heading not found: {heading!r}")

    for child in list(body)[heading_index + 1 :]:
        if child.tag == f"{{{WORD_NS}}}tbl":
            return child

    raise TeacherTableSyncError(f"no table follows exact heading: {heading!r}")


def _english_column_index(header_cells: list[str]) -> int:
    normalized = [_normalize_text(cell).casefold() for cell in header_cells]
    if "english" not in normalized:
        raise TeacherTableSyncError("target table header must include an English column")
    return normalized.index("english")


def _ukrainian_column_index(header_cells: list[str]) -> int:
    normalized = [_normalize_text(cell).casefold() for cell in header_cells]
    _english_column_index(header_cells)

    # Current master-table exports have used both names for the Ukrainian source
    # column.  Prefer the explicit Ukrainian header when both are present.
    for candidate in ("ukrainian", "current"):
        if candidate in normalized:
            return normalized.index(candidate)
    raise TeacherTableSyncError(
        "target table header must include a Ukrainian or Current source column",
    )


@dataclass(frozen=True)
class TeacherTableRow:
    """One data row of the master table; ``row`` is the 1-based data-row position."""

    row: int
    uk: str
    en: str


def normalize_uk_key(value: str) -> str:
    """Normalised Ukrainian key: stress marks stripped, apostrophes unified, case-folded.

    This is the only input of the stable entry id and of the Atlas join, so a
    corrected meaning, a moved row, or a capitalisation variant keeps the same id.
    """

    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(char for char in decomposed if char not in STRESS_MARKS)
    composed = unicodedata.normalize("NFC", stripped).translate(APOSTROPHE_VARIANTS)
    return " ".join(composed.split()).casefold()


def entry_id_for_key(normalized_key: str) -> str:
    return ENTRY_ID_PREFIX + hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()[:12]


def extract_teacher_rows(docx_path: Path, heading: str) -> tuple[str, list[TeacherTableRow]]:
    """Return the DOCX SHA-256 and every data row (Ukrainian + English) after *heading*."""

    try:
        docx_bytes = docx_path.read_bytes()
    except OSError as exc:
        raise TeacherTableSyncError(f"cannot read DOCX: {docx_path}") from exc
    try:
        with zipfile.ZipFile(docx_path) as archive:
            document_xml = archive.read(DOCUMENT_XML)
    except (OSError, zipfile.BadZipFile) as exc:
        raise TeacherTableSyncError(f"not a readable DOCX archive: {docx_path}") from exc
    except KeyError as exc:
        raise TeacherTableSyncError(f"DOCX is missing {DOCUMENT_XML}") from exc

    table = _find_target_table(document_xml, heading)
    rows = table.findall("./w:tr", NS)
    if not rows:
        raise TeacherTableSyncError("target table has no rows")
    header = _row_cells(rows[0])
    uk_column = _ukrainian_column_index(header)
    en_column = _english_column_index(header)
    result: list[TeacherTableRow] = []
    for position, row in enumerate(rows[1:], start=1):
        cells = _row_cells(row)
        uk = cells[uk_column] if uk_column < len(cells) else ""
        en = cells[en_column] if en_column < len(cells) else ""
        result.append(TeacherTableRow(row=position, uk=uk, en=en))
    return hashlib.sha256(docx_bytes).hexdigest(), result


@dataclass(frozen=True)
class DeckBuild:
    entries: list[dict[str, object]]
    merges: list[dict[str, object]]
    source_keys: list[str]
    raw_data_rows: int


def _distinct_meanings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    meanings: list[str] = []
    for value in values:
        folded = value.casefold()
        if value and folded not in seen:
            seen.add(folded)
            meanings.append(value)
    return meanings


def previous_first_seen(previous_entries: Sequence[dict[str, object]] | None) -> dict[str, int]:
    """Map normalised key -> carried ``firstSeen`` from a previous deck artifact."""

    carried: dict[str, int] = {}
    for entry in previous_entries or []:
        key = entry.get("key")
        first_seen = entry.get("firstSeen")
        if isinstance(key, str) and isinstance(first_seen, int) and not isinstance(first_seen, bool):
            carried[key] = first_seen
    return carried


def build_deck_entries(
    rows: list[TeacherTableRow],
    previous_entries: Sequence[dict[str, object]] | None = None,
) -> DeckBuild:
    """Merge rows into one entry per normalised key and assign order keys.

    ``firstSeen`` is copied from *previous_entries* for every surviving key.  A
    key that is new in this document gets ``max(previous) + n`` in row order, so
    newer keys always sort after older ones.  Without any previous order keys
    (first sync) the earliest source row number is the order key.
    """

    groups: dict[str, list[TeacherTableRow]] = {}
    source_keys: list[str] = []
    seen_source_keys: set[str] = set()
    for row in rows:
        if not row.uk:
            continue
        if not row.en:
            raise TeacherTableSyncError(f"table row {row.row} has no English meaning")
        groups.setdefault(normalize_uk_key(row.uk), []).append(row)
        if row.uk not in seen_source_keys:
            seen_source_keys.add(row.uk)
            source_keys.append(row.uk)

    carried = previous_first_seen(previous_entries)
    next_order = max(carried.values(), default=0)
    entries: list[dict[str, object]] = []
    merges: list[dict[str, object]] = []
    ids: dict[str, str] = {}
    for key, group in groups.items():
        entry_id = entry_id_for_key(key)
        if entry_id in ids:
            raise TeacherTableSyncError(f"entry id collision between {ids[entry_id]!r} and {key!r}")
        ids[entry_id] = key
        if key in carried:
            first_seen = carried[key]
        elif carried:
            next_order += 1
            first_seen = next_order
        else:
            first_seen = group[0].row
        meanings = _distinct_meanings([row.en for row in group])
        entry: dict[str, object] = {
            "entryId": entry_id,
            "key": key,
            "uk": group[0].uk,
            "en": "; ".join(meanings),
            "firstSeen": first_seen,
            "multiword": any(char.isspace() for char in group[0].uk),
            "sourceRows": [row.row for row in group],
            "sourceKeys": list(dict.fromkeys(row.uk for row in group)),
        }
        entries.append(entry)
        if len(group) > 1:
            merges.append(
                {
                    "entryId": entry_id,
                    "uk": group[0].uk,
                    "rows": [row.row for row in group],
                    "spellings": entry["sourceKeys"],
                    "meanings": [row.en for row in group],
                    "differentEnglish": len(meanings) > 1,
                }
            )
    return DeckBuild(entries=entries, merges=merges, source_keys=source_keys, raw_data_rows=len(rows))


def frozen_keys_payload(docx_sha256: str, build: DeckBuild, heading: str = HEADING) -> dict[str, object]:
    """Frozen denominator: every distinct source key with the document hash."""

    return {
        "schema": FROZEN_KEYS_SCHEMA,
        "schemaVersion": FROZEN_KEYS_SCHEMA_VERSION,
        "docxSha256": docx_sha256,
        "heading": heading,
        "rawDataRows": build.raw_data_rows,
        "sourceKeyCount": len(build.source_keys),
        "entryCount": len(build.entries),
        "keys": build.source_keys,
    }


def extract_teacher_table(docx_path: Path, heading: str) -> tuple[TeacherTableReport, list[str]]:
    """Extract ordered, unique Ukrainian cells from the table after *heading*."""

    docx_sha256, rows = extract_teacher_rows(docx_path, heading)
    lemma_keys = list(dict.fromkeys(row.uk for row in rows if row.uk))
    report = TeacherTableReport(
        raw_data_rows=len(rows),
        unique_uk=len(lemma_keys),
        multiword=sum(1 for key in lemma_keys if any(char.isspace() for char in key)),
        first5=lemma_keys[:5],
        last5=lemma_keys[-5:],
        sha256_docx=docx_sha256,
    )
    return report, lemma_keys


def _read_previous_lemma_keys(site_data_path: Path) -> list[str]:
    if not site_data_path.exists():
        return []
    try:
        payload = json.loads(site_data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TeacherTableSyncError(f"cannot read existing site data: {site_data_path}") from exc
    lemma_keys = payload.get("lemma_keys") if isinstance(payload, dict) else None
    if not isinstance(lemma_keys, list) or not all(isinstance(key, str) for key in lemma_keys):
        raise TeacherTableSyncError(
            f"existing site data has no valid lemma_keys list: {site_data_path}",
        )
    return lemma_keys


def write_site_data(
    lemma_keys: list[str],
    *,
    site_data_path: Path = DEFAULT_SITE_DATA_PATH,
    allow_shrink: bool = False,
) -> None:
    """Write the public, lemma-only special-set payload after the shrink guard.

    The guard compares normalised keys: merging capitalisation or apostrophe
    variants of one word is not a shrink, but dropping a word is.
    """

    current = {normalize_uk_key(key) for key in lemma_keys}
    dropped = [key for key in _read_previous_lemma_keys(site_data_path) if normalize_uk_key(key) not in current]
    if dropped and not allow_shrink:
        raise TeacherTableSyncError(
            f"refusing to shrink teacher-table deck: {len(dropped)} previous keys would be dropped "
            f"(first: {dropped[:3]}); pass --allow-shrink to confirm",
        )

    payload = {
        "schema": SCHEMA,
        "id": DECK_ID,
        "title": TITLE,
        "titleUk": TITLE_UK,
        "description": DESCRIPTION,
        "lemma_keys": lemma_keys,
    }
    site_data_path.parent.mkdir(parents=True, exist_ok=True)
    site_data_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract the table after an exact DOCX heading into the Teacher table Practice set.\n"
            "Use for a table-only report or legacy key-list write; use "
            "`python -m scripts.lexicon.teacher_deck refresh` to rebuild the whole teacher deck."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.lexicon.sync_teacher_table_deck --docx /private/master.docx \\
      --heading "Combined Master Vocabulary Table (#3)"
  .venv/bin/python -m scripts.lexicon.sync_teacher_table_deck --docx /private/master.docx \\
      --heading "Combined Master Vocabulary Table (#3)" --write-site-data
Outputs: JSON report on stdout (and --report); --write-site-data rewrites
  site/src/data/lexicon-teacher-table-deck.json (one key per normalised entry).
Exit codes: 0 success; 1 unreadable DOCX, missing heading/table/columns, or shrink refused.
Related: #8843; scripts/lexicon/teacher_deck.py; docs/practice/teacher-deck-artifacts.md.
""",
    )
    parser.add_argument(
        "--docx", type=Path, required=True, help="Private teacher master DOCX path (e.g. /private/master.docx)."
    )
    parser.add_argument(
        "--heading",
        required=True,
        help=f"Exact heading whose next table is the master vocabulary table (e.g. {HEADING!r}).",
    )
    parser.add_argument(
        "--write-site-data",
        action="store_true",
        help="Write site/src/data/lexicon-teacher-table-deck.json after the shrink guard (default: report only).",
    )
    parser.add_argument(
        "--allow-shrink",
        action="store_true",
        help="Allow --write-site-data to drop previously published keys (default: refuse).",
    )
    parser.add_argument("--report", type=Path, help="Optional JSON report output path (default: stdout only).")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report, _lemma_keys = extract_teacher_table(args.docx, args.heading)
        if args.write_site_data:
            _sha, rows = extract_teacher_rows(args.docx, args.heading)
            entries = build_deck_entries(rows).entries
            write_site_data([str(entry["uk"]) for entry in entries], allow_shrink=args.allow_shrink)
    except TeacherTableSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    payload = asdict(report)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
