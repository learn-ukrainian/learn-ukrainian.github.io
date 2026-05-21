"""Build a small VESUM lemma subset for Starlight vocabulary-table links.

The full VESUM database has millions of forms. The Astro remark plugin should
not query it during the site build, so this script scans committed Starlight
MDX vocabulary tables and writes only the form→lemma pairs that the plugin can
use safely.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

DEFAULT_CONTENT_ROOT = Path("starlight/src/content/docs")
DEFAULT_MANIFEST = Path("starlight/src/data/etymology-manifest.json")
DEFAULT_OUTPUT = Path("starlight/src/data/vesum-vocab-lemmas.json")
DEFAULT_VESUM_DB = Path("data/vesum.db")
VERSION = "2026-05-21-v1"
STRESS_MARKS = {"\u0300", "\u0301", "\u0341"}

VOCAB_TAB_LABELS = {"vocabulary", "словник"}
WORD_HEADERS = {"word", "слово"}
OPT_OUT_RE = re.compile(r"(?:vocab-etymology|etymology-links)\s*:\s*(?:off|false)", re.IGNORECASE)
TAB_OPEN_RE = re.compile(r"<TabItem\b(?P<attrs>[^>]*)>", re.IGNORECASE)
TAB_CLOSE_RE = re.compile(r"</TabItem>", re.IGNORECASE)
LABEL_RE = re.compile(r"""(?:^|\s)label\s*=\s*(?P<quote>["'])(?P<label>.*?)(?P=quote)""", re.DOTALL)


def normalize_lemma(value: str) -> str:
    """Lowercase and strip combining stress marks without changing й/ї."""
    decomposed = unicodedata.normalize("NFD", value.strip().lower())
    stripped = "".join(ch for ch in decomposed if ch not in STRESS_MARKS)
    return unicodedata.normalize("NFC", stripped)


def strip_markdown_inline(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"</?[^>]+>", "", value)
    value = value.replace("\\|", "|")
    value = re.sub(r"[*_`~]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in stripped:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    cells.append("".join(current).strip())
    return cells


def is_separator_row(line: str) -> bool:
    cells = split_markdown_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def tab_label(opening_line: str) -> str | None:
    match = TAB_OPEN_RE.search(opening_line)
    if not match:
        return None
    label_match = LABEL_RE.search(match.group("attrs"))
    if not label_match:
        return None
    return label_match.group("label")


def tab_opted_out(opening_line: str) -> bool:
    match = TAB_OPEN_RE.search(opening_line)
    return bool(match and OPT_OUT_RE.search(match.group("attrs")))


def vocabulary_tab_blocks(text: str) -> list[list[str]]:
    lines = text.splitlines()
    blocks: list[list[str]] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        label = tab_label(line)
        if label is None:
            index += 1
            continue

        body: list[str] = []
        index += 1
        while index < len(lines) and not TAB_CLOSE_RE.search(lines[index]):
            body.append(lines[index])
            index += 1

        if normalize_lemma(label) in VOCAB_TAB_LABELS and not tab_opted_out(line):
            blocks.append(body)

        index += 1

    return blocks


def extract_vocabulary_words_from_text(text: str) -> set[str]:
    words: set[str] = set()

    for block in vocabulary_tab_blocks(text):
        index = 0
        while index < len(block):
            line = block[index]
            if not line.lstrip().startswith("|"):
                index += 1
                continue

            table_lines: list[str] = []
            while index < len(block) and block[index].lstrip().startswith("|"):
                table_lines.append(block[index])
                index += 1

            if len(table_lines) < 2 or not is_separator_row(table_lines[1]):
                continue

            header = split_markdown_table_row(table_lines[0])
            if not header or normalize_lemma(strip_markdown_inline(header[0])) not in WORD_HEADERS:
                continue

            for row in table_lines[2:]:
                cells = split_markdown_table_row(row)
                if not cells:
                    continue
                word = strip_markdown_inline(cells[0])
                if word:
                    words.add(word)

    return words


def extract_vocabulary_words(content_root: Path) -> tuple[set[str], list[str]]:
    words: set[str] = set()
    files: list[str] = []
    for path in sorted(content_root.rglob("*.mdx")):
        extracted = extract_vocabulary_words_from_text(path.read_text(encoding="utf-8"))
        if extracted:
            words.update(extracted)
            files.append(str(path))
    return words, files


def load_manifest_lemma_keys(manifest_path: Path) -> set[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        normalize_lemma(entry["lemma"])
        for entry in manifest.get("entries", [])
        if isinstance(entry, dict) and entry.get("lemma")
    }


def single_token(value: str) -> bool:
    return bool(value.strip()) and not re.search(r"\s", value.strip())


def strip_reflexive_suffix(value: str) -> str:
    normalized = normalize_lemma(value)
    if normalized.endswith(("ся", "сь")):
        return normalized[:-2]
    return normalized


def choose_unambiguous_manifest_lemma(
    conn: sqlite3.Connection, form: str, manifest_lemma_keys: set[str]
) -> str | None:
    rows = conn.execute("SELECT DISTINCT lemma FROM forms WHERE word_form = ?", (form,)).fetchall()
    if not rows:
        return None

    by_key = {normalize_lemma(row[0]): row[0] for row in rows}
    if len(by_key) != 1:
        return None

    lemma_key, lemma = next(iter(by_key.items()))
    if lemma_key not in manifest_lemma_keys:
        return None
    return lemma


def build_vesum_vocab_lemmas(
    *,
    content_root: Path = DEFAULT_CONTENT_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST,
    vesum_db: Path = DEFAULT_VESUM_DB,
) -> dict:
    words, source_files = extract_vocabulary_words(content_root)
    manifest_lemma_keys = load_manifest_lemma_keys(manifest_path)

    form_to_lemma: dict[str, str] = {}
    skipped_multiword = 0
    direct_manifest_matches = 0
    ambiguous_or_missing = 0

    conn = sqlite3.connect(vesum_db)
    try:
        for word in sorted(words, key=normalize_lemma):
            normalized_word = normalize_lemma(word)
            if not single_token(normalized_word):
                skipped_multiword += 1
                continue
            if normalized_word in manifest_lemma_keys:
                direct_manifest_matches += 1
                continue

            candidates = [normalized_word]
            stripped = strip_reflexive_suffix(normalized_word)
            if stripped != normalized_word:
                candidates.append(stripped)
            lemma = None
            for candidate in candidates:
                lemma = choose_unambiguous_manifest_lemma(conn, candidate, manifest_lemma_keys)
                if lemma:
                    break

            if lemma:
                form_to_lemma[normalized_word] = lemma
            else:
                ambiguous_or_missing += 1
    finally:
        conn.close()

    return {
        "version": VERSION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "source": {
            "content_root": str(content_root),
            "manifest": str(manifest_path),
            "vesum_db": str(vesum_db),
            "mdx_files": source_files,
        },
        "stats": {
            "vocabulary_words": len(words),
            "direct_manifest_matches": direct_manifest_matches,
            "vesum_form_matches": len(form_to_lemma),
            "skipped_multiword": skipped_multiword,
            "ambiguous_or_missing": ambiguous_or_missing,
        },
        "form_to_lemma": dict(sorted(form_to_lemma.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content-root", type=Path, default=DEFAULT_CONTENT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    output = build_vesum_vocab_lemmas(
        content_root=args.content_root,
        manifest_path=args.manifest,
        vesum_db=args.vesum_db,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**output["stats"], "output_file": str(args.output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
