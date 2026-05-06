#!/usr/bin/env python3
"""Generic deterministic dictionary ingestion into ``data/sources.db``.

Adapters and expected source sizes:
- antonenko: Antonenko-Davydovych «Як ми говоримо», paragraph usage notes,
  roughly 500-700 rows for a full text file.
- karavansky: Karavansky Russian-Ukrainian difficult-lexis dictionary,
  roughly 5,000 rows.
- holovashchuk: Holovashchuk Ukrainian literary usage guide,
  roughly 3,000-8,000 rows depending on edition/text extraction.
- paronyms: Hrynchyshyn/Serbenska Ukrainian paronyms dictionary, roughly
  1,500 paronym pairs.

The input is UTF-8 plain text. PDF/OCR extraction is intentionally out of
scope; run this after the private materials have already been converted to
text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "sources.db"

SPACE_RE = re.compile(r"[ \t]+")
PAGE_LINE_RE = re.compile(r"^(?:\[?\s*(?:с\.|стор\.|page)\s*)?(\d{1,4})\s*\]?$", re.IGNORECASE)
INLINE_PAGE_RE = re.compile(r"\[(?:с\.|стор\.|page)\s*(\d{1,4})\]", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+")
QUOTE_RE = r"[«\"“](.+?)[»\"”]"


@dataclass(frozen=True)
class ParsedRow:
    values: dict[str, object]
    text_for_key: str


@dataclass(frozen=True)
class IngestResult:
    source: str
    parsed: int
    inserted: int
    skipped: int
    dry_run: bool


class Adapter(Protocol):
    source: str
    label: str
    table: str
    fts_table: str

    def ensure_schema(self, conn: sqlite3.Connection) -> None: ...

    def parse(self, text: str) -> list[ParsedRow]: ...

    def insert_row(self, conn: sqlite3.Connection, row: ParsedRow) -> bool: ...

    def force_clear(self, conn: sqlite3.Connection) -> None: ...

    def rebuild_fts(self, conn: sqlite3.Connection) -> None: ...


def _clean_text(text: str) -> str:
    return SPACE_RE.sub(" ", text.replace("\u00a0", " ")).strip()


def _split_blocks(text: str) -> list[tuple[int | None, str]]:
    """Split text into paragraph-like blocks while tracking standalone page markers."""
    blocks: list[tuple[int | None, str]] = []
    current_page: int | None = None
    parts: list[str] = []
    block_page: int | None = None

    def flush() -> None:
        nonlocal parts, block_page
        if parts:
            block = _clean_text(" ".join(parts))
            if block:
                inline_page = INLINE_PAGE_RE.search(block)
                page = int(inline_page.group(1)) if inline_page else block_page
                block = INLINE_PAGE_RE.sub("", block).strip()
                blocks.append((page, block))
        parts = []
        block_page = None

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = _clean_text(raw_line)
        if not line:
            flush()
            continue
        page_match = PAGE_LINE_RE.match(line)
        if page_match:
            flush()
            current_page = int(page_match.group(1))
            continue
        if block_page is None:
            block_page = current_page
        parts.append(line)
    flush()
    return blocks


def _first_sentence(text: str, max_chars: int = 160) -> str:
    sentence = SENTENCE_RE.split(text, maxsplit=1)[0].strip()
    if len(sentence) <= max_chars:
        return sentence
    return sentence[: max_chars - 1].rstrip() + "…"


def _entry_key(source: str, *parts: object) -> str:
    payload = "\n".join(str(part or "").strip().lower() for part in parts)
    return hashlib.sha256(f"{source}\n{payload}".encode()).hexdigest()


def _json_list(values: list[str]) -> str:
    cleaned = [value for value in (_clean_text(item) for item in values) if value]
    return json.dumps(cleaned, ensure_ascii=False)


def _split_list(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [_clean_text(part) for part in re.split(r"\s*[;,]\s*", text) if _clean_text(part)]


class BaseAdapter:
    source: str
    label: str
    table: str
    fts_table: str
    schema_sql: tuple[str, ...]

    def ensure_schema(self, conn: sqlite3.Connection) -> None:
        for statement in self.schema_sql:
            conn.execute(statement)

    def force_clear(self, conn: sqlite3.Connection) -> None:
        conn.execute(f"DELETE FROM {self.table} WHERE source_id = ?", (self.source,))
        self.rebuild_fts(conn)

    def rebuild_fts(self, conn: sqlite3.Connection) -> None:
        conn.execute(f"INSERT INTO {self.fts_table}({self.fts_table}) VALUES ('rebuild')")

    def _exists(self, conn: sqlite3.Connection, entry_key: str) -> bool:
        row = conn.execute(
            f"SELECT 1 FROM {self.table} WHERE source_id = ? AND entry_key = ? LIMIT 1",
            (self.source, entry_key),
        ).fetchone()
        return row is not None


class AntonenkoAdapter(BaseAdapter):
    """Paragraph-level usage notes from «Як ми говоримо»; expected ~500 rows."""

    source = "antonenko"
    label = "Антоненко-Давидович «Як ми говоримо»"
    table = "style_antonenko"
    fts_table = "style_antonenko_fts"
    schema_sql = (
        """
        CREATE TABLE IF NOT EXISTS style_antonenko (
            id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            entry_key TEXT NOT NULL,
            topic TEXT NOT NULL DEFAULT '',
            wrong_form TEXT NOT NULL DEFAULT '',
            right_form TEXT NOT NULL DEFAULT '',
            prose TEXT NOT NULL DEFAULT '',
            page INTEGER,
            source TEXT NOT NULL DEFAULT 'Антоненко-Давидович «Як ми говоримо»',
            UNIQUE(source_id, entry_key)
        )
        """,
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS style_antonenko_fts USING fts5(
            topic, wrong_form, right_form, prose,
            content='style_antonenko', content_rowid='id', tokenize='unicode61'
        )
        """,
    )

    def parse(self, text: str) -> list[ParsedRow]:
        rows: list[ParsedRow] = []
        for page, paragraph in _split_blocks(text):
            if len(paragraph) < 20:
                continue
            wrong, right = _extract_wrong_right(paragraph)
            topic = _first_sentence(paragraph)
            rows.append(
                ParsedRow(
                    values={
                        "topic": topic,
                        "wrong_form": wrong,
                        "right_form": right,
                        "prose": paragraph,
                        "page": page,
                    },
                    text_for_key=paragraph,
                )
            )
        return rows

    def insert_row(self, conn: sqlite3.Connection, row: ParsedRow) -> bool:
        values = row.values
        key = _entry_key(self.source, values["topic"], values["prose"])
        if self._exists(conn, key):
            return False
        conn.execute(
            """
            INSERT INTO style_antonenko (
                source_id, entry_key, topic, wrong_form, right_form, prose, page
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.source,
                key,
                values["topic"],
                values["wrong_form"],
                values["right_form"],
                values["prose"],
                values["page"],
            ),
        )
        return True


class KaravanskyAdapter(BaseAdapter):
    """RU -> UK difficult-lexis entries; expected ~5,000 rows."""

    source = "karavansky"
    label = "Караванський «Російсько-український словник складної лексики»"
    table = "karavansky_r2u"
    fts_table = "karavansky_r2u_fts"
    schema_sql = (
        """
        CREATE TABLE IF NOT EXISTS karavansky_r2u (
            id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            entry_key TEXT NOT NULL,
            ru_lemma TEXT NOT NULL,
            uk_translations TEXT NOT NULL DEFAULT '[]',
            notes TEXT NOT NULL DEFAULT '',
            pos TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'Караванський РУ-УК складна лексика',
            UNIQUE(source_id, entry_key)
        )
        """,
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS karavansky_r2u_fts USING fts5(
            ru_lemma, uk_translations, notes, pos,
            content='karavansky_r2u', content_rowid='id', tokenize='unicode61'
        )
        """,
    )

    def parse(self, text: str) -> list[ParsedRow]:
        rows: list[ParsedRow] = []
        for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
            line = _clean_text(raw_line)
            if not line or PAGE_LINE_RE.match(line):
                continue
            parsed = _parse_r2u_line(line)
            if parsed is None:
                continue
            rows.append(ParsedRow(values=parsed, text_for_key=line))
        return rows

    def insert_row(self, conn: sqlite3.Connection, row: ParsedRow) -> bool:
        values = row.values
        key = _entry_key(self.source, values["ru_lemma"], values["uk_translations"], values["notes"])
        if self._exists(conn, key):
            return False
        conn.execute(
            """
            INSERT INTO karavansky_r2u (
                source_id, entry_key, ru_lemma, uk_translations, notes, pos
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.source,
                key,
                values["ru_lemma"],
                values["uk_translations"],
                values["notes"],
                values["pos"],
            ),
        )
        return True


class HolovashchukAdapter(BaseAdapter):
    """Ukrainian literary word-usage guide entries; expected ~3,000-8,000 rows."""

    source = "holovashchuk"
    label = "Головашчук «Словник-довідник з українського літературного слововживання»"
    table = "style_holovashchuk"
    fts_table = "style_holovashchuk_fts"
    schema_sql = (
        """
        CREATE TABLE IF NOT EXISTS style_holovashchuk (
            id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            entry_key TEXT NOT NULL,
            lemma TEXT NOT NULL,
            correct_usage TEXT NOT NULL DEFAULT '',
            incorrect_variants TEXT NOT NULL DEFAULT '[]',
            register_notes TEXT NOT NULL DEFAULT '',
            examples TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'Головашчук літературне слововживання',
            UNIQUE(source_id, entry_key)
        )
        """,
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS style_holovashchuk_fts USING fts5(
            lemma, correct_usage, incorrect_variants, register_notes, examples,
            content='style_holovashchuk', content_rowid='id', tokenize='unicode61'
        )
        """,
    )

    def parse(self, text: str) -> list[ParsedRow]:
        rows: list[ParsedRow] = []
        for _page, block in _split_blocks(text):
            parsed = _parse_holovashchuk_block(block)
            if parsed is not None:
                rows.append(ParsedRow(values=parsed, text_for_key=block))
        return rows

    def insert_row(self, conn: sqlite3.Connection, row: ParsedRow) -> bool:
        values = row.values
        key = _entry_key(self.source, values["lemma"], values["correct_usage"], values["incorrect_variants"])
        if self._exists(conn, key):
            return False
        conn.execute(
            """
            INSERT INTO style_holovashchuk (
                source_id, entry_key, lemma, correct_usage,
                incorrect_variants, register_notes, examples
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.source,
                key,
                values["lemma"],
                values["correct_usage"],
                values["incorrect_variants"],
                values["register_notes"],
                values["examples"],
            ),
        )
        return True


class ParonymsAdapter(BaseAdapter):
    """Paronym pairs with meanings/examples; expected ~1,500 rows."""

    source = "paronyms"
    label = "Гринчишин/Сербенська «Словник паронімів української мови»"
    table = "paronyms_full"
    fts_table = "paronyms_full_fts"
    schema_sql = (
        """
        CREATE TABLE IF NOT EXISTS paronyms_full (
            id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            entry_key TEXT NOT NULL,
            lexeme_a TEXT NOT NULL,
            lexeme_b TEXT NOT NULL,
            meaning_a TEXT NOT NULL DEFAULT '',
            meaning_b TEXT NOT NULL DEFAULT '',
            usage_examples TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'Гринчишин/Сербенська пароніми',
            UNIQUE(source_id, entry_key)
        )
        """,
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS paronyms_full_fts USING fts5(
            lexeme_a, lexeme_b, meaning_a, meaning_b, usage_examples,
            content='paronyms_full', content_rowid='id', tokenize='unicode61'
        )
        """,
    )

    def parse(self, text: str) -> list[ParsedRow]:
        rows: list[ParsedRow] = []
        for _page, block in _split_blocks(text):
            parsed = _parse_paronym_block(block)
            if parsed is not None:
                rows.append(ParsedRow(values=parsed, text_for_key=block))
        return rows

    def insert_row(self, conn: sqlite3.Connection, row: ParsedRow) -> bool:
        values = row.values
        key = _entry_key(self.source, values["lexeme_a"], values["lexeme_b"], values["meaning_a"], values["meaning_b"])
        if self._exists(conn, key):
            return False
        conn.execute(
            """
            INSERT INTO paronyms_full (
                source_id, entry_key, lexeme_a, lexeme_b,
                meaning_a, meaning_b, usage_examples
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.source,
                key,
                values["lexeme_a"],
                values["lexeme_b"],
                values["meaning_a"],
                values["meaning_b"],
                values["usage_examples"],
            ),
        )
        return True


def _extract_wrong_right(text: str) -> tuple[str, str]:
    patterns = (
        rf"не\s+(?:кажіть|вживайте|слід\s+казати)\s+{QUOTE_RE}.*?(?:кажіть|уживайте|вживайте|треба|слід|краще|правильно)\s+{QUOTE_RE}",
        rf"замість\s+{QUOTE_RE}.*?(?:кажіть|уживайте|вживайте|треба|слід|краще|правильно)\s+{QUOTE_RE}",
        rf"{QUOTE_RE}\s*[—-]\s*(?:неправильно|помилково).*?{QUOTE_RE}\s*[—-]\s*(?:правильно|краще)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and len(match.groups()) >= 2:
            return _clean_text(match.group(1)), _clean_text(match.group(2))
    return "", ""


def _parse_r2u_line(line: str) -> dict[str, object] | None:
    line = _clean_text(line)
    if not line or line.startswith("#"):
        return None

    notes = ""
    if " #" in line:
        line, notes = line.split(" #", 1)
        notes = notes.strip()

    match = re.match(r"^(.+?)\s*(?:\t|=>|→|—|–|-|:)\s*(.+)$", line)
    if not match:
        return None

    ru_lemma = _clean_text(match.group(1).strip(" ."))
    rhs = _clean_text(match.group(2))
    pos = ""
    pos_match = re.match(r"^\(([^)]+)\)\s*(.+)$", rhs)
    if pos_match:
        pos = _clean_text(pos_match.group(1))
        rhs = _clean_text(pos_match.group(2))

    note_bits = re.findall(r"\(([^)]+)\)", rhs)
    if note_bits:
        notes = "; ".join([notes, *note_bits]).strip("; ")
        rhs = re.sub(r"\([^)]*\)", "", rhs)

    translations = _split_list(rhs)
    if not ru_lemma or not translations:
        return None
    return {
        "ru_lemma": ru_lemma,
        "uk_translations": _json_list(translations),
        "notes": notes,
        "pos": pos,
    }


def _parse_holovashchuk_block(block: str) -> dict[str, object] | None:
    block = _clean_text(block)
    if not block:
        return None
    head_match = re.match(r"^([^—–:\n.]{1,80})(?:\s*[—–:]\s*)?(.*)$", block)
    if not head_match:
        return None
    lemma = _clean_text(head_match.group(1).strip(" ."))
    rest = _clean_text(head_match.group(2) or block)
    if not lemma or len(lemma.split()) > 4:
        return None

    correct = _extract_labeled_text(rest, ("правильно", "нормативно", "correct"))
    incorrect = _extract_labeled_text(rest, ("неправильно", "не нормативно", "incorrect", "помилково"))
    register = _extract_labeled_text(rest, ("ремарка", "стиль", "register", "уживання"))
    examples = _extract_labeled_text(rest, ("приклади", "приклад", "examples", "example"))

    if not correct:
        correct = rest
    return {
        "lemma": lemma,
        "correct_usage": correct,
        "incorrect_variants": _json_list(_split_list(incorrect)),
        "register_notes": register,
        "examples": _json_list(_split_list(examples)),
    }


def _extract_labeled_text(text: str, labels: tuple[str, ...]) -> str:
    label_pattern = "|".join(re.escape(label) for label in labels)
    stop_labels = (
        "правильно|нормативно|correct|неправильно|не нормативно|incorrect|"
        "помилково|ремарка|стиль|register|уживання|приклади|приклад|examples|example"
    )
    match = re.search(
        rf"(?:{label_pattern})\s*:\s*(.*?)(?=(?:\b(?:{stop_labels})\s*:)|$)",
        text,
        flags=re.IGNORECASE,
    )
    return _clean_text(match.group(1)) if match else ""


def _parse_paronym_block(block: str) -> dict[str, object] | None:
    block = _clean_text(block)
    first_line_match = re.match(r"^([А-ЯІЇЄҐа-яіїєґ'’-]+)\s*[—–-]\s*([А-ЯІЇЄҐа-яіїєґ'’-]+)\.?\s*(.*)$", block)
    if not first_line_match:
        return None
    lexeme_a = _clean_text(first_line_match.group(1))
    lexeme_b = _clean_text(first_line_match.group(2))
    rest = _clean_text(first_line_match.group(3))

    examples = _extract_labeled_text(rest, ("приклади", "приклад", "examples", "example"))
    definitions = re.split(r"\b(?:приклади|приклад|examples|example)\s*:", rest, maxsplit=1, flags=re.IGNORECASE)[0]
    meaning_a, meaning_b = _extract_pair_meanings(definitions, lexeme_a, lexeme_b)

    if not meaning_a or not meaning_b:
        pieces = [piece.strip() for piece in re.split(r"\s*;\s*", definitions, maxsplit=1)]
        if len(pieces) == 2:
            meaning_a = meaning_a or _strip_leading_label(pieces[0], lexeme_a)
            meaning_b = meaning_b or _strip_leading_label(pieces[1], lexeme_b)

    return {
        "lexeme_a": lexeme_a,
        "lexeme_b": lexeme_b,
        "meaning_a": meaning_a,
        "meaning_b": meaning_b,
        "usage_examples": _json_list(_split_list(examples)),
    }


def _extract_pair_meanings(text: str, lexeme_a: str, lexeme_b: str) -> tuple[str, str]:
    labels = [
        ("a", lexeme_a),
        ("b", lexeme_b),
    ]
    spans: list[tuple[int, int, str]] = []
    for key, label in labels:
        match = re.search(rf"\b{re.escape(label)}\s*:", text, flags=re.IGNORECASE)
        if match:
            spans.append((match.start(), match.end(), key))
    if len(spans) < 2:
        return "", ""

    spans.sort()
    values: dict[str, str] = {}
    for index, (_start, end, key) in enumerate(spans):
        next_start = spans[index + 1][0] if index + 1 < len(spans) else len(text)
        values[key] = _clean_text(text[end:next_start].strip(" ;."))
    return values.get("a", ""), values.get("b", "")


def _strip_leading_label(text: str, label: str) -> str:
    return _clean_text(re.sub(rf"^{re.escape(label)}\s*[:—–-]\s*", "", text, flags=re.IGNORECASE))


ADAPTERS: dict[str, Adapter] = {
    "antonenko": AntonenkoAdapter(),
    "karavansky": KaravanskyAdapter(),
    "holovashchuk": HolovashchukAdapter(),
    "paronyms": ParonymsAdapter(),
}


def ingest(adapter: Adapter, input_path: Path, db_path: Path, *, dry_run: bool, force: bool) -> IngestResult:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    rows = adapter.parse(input_path.read_text(encoding="utf-8-sig"))
    if dry_run:
        return IngestResult(adapter.source, parsed=len(rows), inserted=0, skipped=0, dry_run=True)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        with conn:
            adapter.ensure_schema(conn)
            if force:
                adapter.force_clear(conn)
            inserted = 0
            skipped = 0
            for row in rows:
                if adapter.insert_row(conn, row):
                    inserted += 1
                else:
                    skipped += 1
            adapter.rebuild_fts(conn)
        return IngestResult(adapter.source, parsed=len(rows), inserted=inserted, skipped=skipped, dry_run=False)
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest supported private dictionary text files into SQLite FTS5 tables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Sources and expected input:
  antonenko    Paragraph usage notes from «Як ми говоримо»; blank line between notes.
  karavansky   RU -> UK entries, one per line: RU — UK1, UK2 (notes).
  holovashchuk Ukrainian lemma usage notes; one blank-line-separated entry per lemma.
  paronyms     Paronym-pair entries: СЛОВО — СЛОВО, followed by meanings/examples.

Examples:
  .venv/bin/python -m scripts.ingest.dictionary_ingest --source antonenko --input docs/references/private/antonenko.txt
  .venv/bin/python -m scripts.ingest.dictionary_ingest --source karavansky --input docs/references/private/karavansky.txt --dry-run
  .venv/bin/python -m scripts.ingest.dictionary_ingest --source paronyms --input docs/references/private/paronyms.txt --force
""",
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=sorted(ADAPTERS),
        help="Dictionary adapter to run.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="UTF-8 plain-text input file. PDF extraction is not handled here.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"SQLite sources.db path to update. Default: {DEFAULT_DB}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report row counts without creating tables or writing rows.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing rows for the selected source before inserting parsed rows.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    adapter = ADAPTERS[args.source]
    try:
        result = ingest(adapter, args.input, args.db, dry_run=args.dry_run, force=args.force)
    except (OSError, sqlite3.Error) as exc:
        print(f"dictionary_ingest: {exc}", file=sys.stderr)
        return 1

    if result.dry_run:
        print(f"[dry-run] parsed {result.parsed} {adapter.label} row(s); no database writes.")
    else:
        print(
            f"{adapter.label}: parsed {result.parsed}, "
            f"inserted {result.inserted}, skipped {result.skipped} -> {args.db}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
