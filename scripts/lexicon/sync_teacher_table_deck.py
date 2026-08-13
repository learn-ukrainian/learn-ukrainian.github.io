"""Sync the Combined Master Vocabulary Table into the public Practice special set.

The source document remains private.  This module deliberately reads only the
table immediately following the exact requested heading; it is not a general
document-vocabulary miner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
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
TITLE = "From the lessons"
TITLE_UK = "З уроків"
DESCRIPTION = "Words from live classroom lessons."


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


def _ukrainian_column_index(header_cells: list[str]) -> int:
    normalized = [_normalize_text(cell).casefold() for cell in header_cells]
    if "english" not in normalized:
        raise TeacherTableSyncError("target table header must include an English column")

    # Current master-table exports have used both names for the Ukrainian source
    # column.  Prefer the explicit Ukrainian header when both are present.
    for candidate in ("ukrainian", "current"):
        if candidate in normalized:
            return normalized.index(candidate)
    raise TeacherTableSyncError(
        "target table header must include a Ukrainian or Current source column",
    )


def extract_teacher_table(docx_path: Path, heading: str) -> tuple[TeacherTableReport, list[str]]:
    """Extract ordered, unique Ukrainian cells from the table after *heading*."""

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

    ukrainian_column = _ukrainian_column_index(_row_cells(rows[0]))
    raw_data_rows = len(rows) - 1
    seen: set[str] = set()
    lemma_keys: list[str] = []
    for row in rows[1:]:
        cells = _row_cells(row)
        value = cells[ukrainian_column] if ukrainian_column < len(cells) else ""
        if value and value not in seen:
            seen.add(value)
            lemma_keys.append(value)

    report = TeacherTableReport(
        raw_data_rows=raw_data_rows,
        unique_uk=len(lemma_keys),
        multiword=sum(1 for key in lemma_keys if any(char.isspace() for char in key)),
        first5=lemma_keys[:5],
        last5=lemma_keys[-5:],
        sha256_docx=hashlib.sha256(docx_bytes).hexdigest(),
    )
    return report, lemma_keys


def _read_previous_lemma_count(site_data_path: Path) -> int:
    if not site_data_path.exists():
        return 0
    try:
        payload = json.loads(site_data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TeacherTableSyncError(f"cannot read existing site data: {site_data_path}") from exc
    lemma_keys = payload.get("lemma_keys") if isinstance(payload, dict) else None
    if not isinstance(lemma_keys, list) or not all(isinstance(key, str) for key in lemma_keys):
        raise TeacherTableSyncError(
            f"existing site data has no valid lemma_keys list: {site_data_path}",
        )
    return len(set(lemma_keys))


def write_site_data(
    lemma_keys: list[str],
    *,
    site_data_path: Path = DEFAULT_SITE_DATA_PATH,
    allow_shrink: bool = False,
) -> None:
    """Write the public, lemma-only special-set payload after the shrink guard."""

    previous_count = _read_previous_lemma_count(site_data_path)
    if len(lemma_keys) < previous_count and not allow_shrink:
        raise TeacherTableSyncError(
            "refusing to shrink teacher-table deck from "
            f"{previous_count} to {len(lemma_keys)} keys; pass --allow-shrink to confirm",
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
        description="Extract the table after an exact DOCX heading into the Teacher table Practice set.",
    )
    parser.add_argument("--docx", type=Path, required=True, help="Private teacher master DOCX path.")
    parser.add_argument(
        "--heading",
        required=True,
        help="Exact heading whose next table is the Combined Master Vocabulary Table.",
    )
    parser.add_argument(
        "--write-site-data",
        action="store_true",
        help="Write site/src/data/lexicon-teacher-table-deck.json after the shrink guard.",
    )
    parser.add_argument(
        "--allow-shrink",
        action="store_true",
        help="Allow --write-site-data to replace a larger existing key set.",
    )
    parser.add_argument("--report", type=Path, help="Optional JSON report output path.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report, lemma_keys = extract_teacher_table(args.docx, args.heading)
        if args.write_site_data:
            write_site_data(lemma_keys, allow_shrink=args.allow_shrink)
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
