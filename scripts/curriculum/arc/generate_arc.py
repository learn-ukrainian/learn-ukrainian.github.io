#!/usr/bin/env python3
"""Generate the machine-readable level arc YAML from the reviewed arc document.

The arc document (docs/epics/fresh-build-<level>-arc.md) is the reviewed
source of truth. This script parses its position tables deterministically and
emits curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml. No arc content is
typed by hand: every string in the YAML is copied from the document by the
parser, and any table cell the parser cannot read fails generation with the
row quoted.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import NoReturn

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

ARC_DOC_REL = "docs/epics/fresh-build-{level}-arc.md"
ARC_OUT_REL = "curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml"
SUPPORTED_LEVELS = ("a1",)

LITERACY_HEADER = ["Pos", "Slug", "Job", "Inventory (letters / signs)", "Est. lessons"]
MAIN_HEADER = ["Pos", "Slug", "Phase", "One-sentence job", "Skills duty", "L"]

SKILL_CODES = ("W", "Li", "R")
SKILLS_NONE = "—"
SKILLS_ALL = "all"

TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]*-[\s:|-]*\|?\s*$")
BACKTICK_RE = re.compile(r"`([^`]*)`")
LINE_REF_RE = re.compile(r"^:(\d+)(?:-(\d+))?$")
UNBACKTICKED_LINE_REF_RE = re.compile(r"(?<![\w`]):\d+(?:[-–]\d+)?")
PAREN_GROUP_RE = re.compile(r"\([^)]*\)")
BOLD_LETTER_COUNT_RE = re.compile(r"\*\*(\d+) letters\*\*")
POSITION_INT_RE = re.compile(r"^\d+$")
POSITION_RANGE_RE = re.compile(r"^(\d+)\s*[–-]\s*(\d+)$")
STATED_TOTAL_RE = re.compile(r"orientation only and total (\d+)")
STATED_TOTAL_SENTENCE_RE = re.compile(r"[^.]*orientation only and total \d+\.", re.S)


class ArcGenerationError(Exception):
    """The arc document cannot be parsed deterministically."""


def _fail(raw_row: str, message: str) -> NoReturn:
    raise ArcGenerationError(f"{message}\n  row: {raw_row.strip()}")


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _find_position_tables(doc_text: str) -> dict[str, list[tuple[str, list[str]]]]:
    """Return {'literacy': rows, 'main': rows} — (raw line, cells) per data row.

    A position table is a Markdown table whose first two header cells are
    ``Pos`` / ``Slug``. Exactly two shapes are known; any other shape fails.
    """
    lines = doc_text.splitlines()
    found: dict[str, list[tuple[str, list[str]]]] = {}
    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith("|") or i + 1 >= len(lines) or not TABLE_SEPARATOR_RE.match(lines[i + 1]):
            i += 1
            continue
        header = _split_row(lines[i])
        rows: list[tuple[str, list[str]]] = []
        j = i + 2
        while j < len(lines) and lines[j].strip().startswith("|"):
            rows.append((lines[j], _split_row(lines[j])))
            j += 1
        i = j
        if header[:2] != ["Pos", "Slug"]:
            continue
        if header == LITERACY_HEADER:
            shape = "literacy"
        elif header == MAIN_HEADER:
            shape = "main"
        else:
            raise ArcGenerationError(f"unknown position-table header: {header!r}")
        if shape in found:
            raise ArcGenerationError(f"duplicate {shape} position table in the arc document")
        found[shape] = rows
    missing = {"literacy", "main"} - found.keys()
    if missing:
        raise ArcGenerationError(f"position table(s) not found in the arc document: {sorted(missing)}")
    return found


def _stated_lesson_total(doc_text: str) -> tuple[int, str]:
    """The lesson total stated in the sizing paragraph after the main table.

    The paragraph immediately following the main position table must contain
    the sentence "… orientation only and total <N>." exactly once. Returns
    (N, sentence). Any deviation fails generation: the stated total is a
    review anchor, not decoration.
    """
    lines = doc_text.splitlines()
    table_end: int | None = None
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and TABLE_SEPARATOR_RE.match(lines[i + 1]):
            header = _split_row(lines[i])
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            if header == MAIN_HEADER:
                table_end = j
                break
            i = j
        else:
            i += 1
    if table_end is None:
        raise ArcGenerationError("main position table not found; cannot locate the stated lesson total")
    paragraph_lines: list[str] = []
    for line in lines[table_end:]:
        if not line.strip():
            if paragraph_lines:
                break
            continue
        paragraph_lines.append(line)
    paragraph = "\n".join(paragraph_lines)
    matches = list(STATED_TOTAL_RE.finditer(paragraph))
    if not matches:
        raise ArcGenerationError(
            "no stated lesson total (…orientation only and total <N>…) found "
            "in the paragraph after the main position table"
        )
    if len(matches) > 1:
        raise ArcGenerationError(
            f"multiple stated lesson totals in the sizing paragraph: {[m.group(0) for m in matches]!r}"
        )
    sentence_match = STATED_TOTAL_SENTENCE_RE.search(paragraph)
    sentence = " ".join(sentence_match.group(0).split()) if sentence_match else paragraph
    return int(matches[0].group(1)), sentence


def _position_int(cell: str, raw_row: str) -> int:
    if POSITION_INT_RE.match(cell):
        return int(cell)
    if POSITION_RANGE_RE.match(cell):
        _fail(raw_row, f"position cell {cell!r} is a range; only the first row of the main table may be a range")
    _fail(raw_row, f"position cell {cell!r} is not an integer")


def _int_cell(cell: str, raw_row: str, what: str) -> int:
    if not POSITION_INT_RE.match(cell):
        _fail(raw_row, f"{what} cell {cell!r} is not an integer")
    return int(cell)


def _slug(cell: str, raw_row: str) -> str:
    text = cell
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1]
    if not text or "`" in text:
        _fail(raw_row, f"slug cell {cell!r} is not a single backticked slug")
    return text


def _standard_line_refs(raw_row: str) -> list[list[int]]:
    """All backticked ``:NNN`` / ``:NNN-NNN`` references in the row, in order.

    A backticked span starting with ``:`` in any other form fails, an inverted
    range (start > end) fails, and a ``:NNN`` reference outside backticks
    fails: line references must be backticked.
    """
    refs: list[list[int]] = []
    for span in BACKTICK_RE.findall(raw_row):
        if not span.startswith(":"):
            continue
        match = LINE_REF_RE.match(span)
        if not match:
            _fail(raw_row, f"backticked reference `{span}` is not of the form `:NNN` or `:NNN-NNN` (ASCII hyphen)")
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if start > end:
            _fail(raw_row, f"backticked reference `{span}` is an inverted range ({start} > {end})")
        refs.append([start, end])
    stray = UNBACKTICKED_LINE_REF_RE.search(BACKTICK_RE.sub("", raw_row))
    if stray:
        _fail(raw_row, f"line reference {stray.group(0)!r} must be backticked")
    return refs


def _parse_skills(cell: str, raw_row: str) -> list[str]:
    text = PAREN_GROUP_RE.sub("", cell)
    tokens = [token.strip() for token in text.split(",")]
    if any(not token for token in tokens):
        _fail(raw_row, f"skills-duty cell {cell!r} has an empty skill token (trailing, leading, or doubled comma)")
    if tokens == [SKILLS_NONE]:
        return []
    if tokens == [SKILLS_ALL]:
        return list(SKILL_CODES)
    skills: list[str] = []
    for token in tokens:
        if token not in SKILL_CODES:
            _fail(
                raw_row, f"skills-duty token {token!r} is not one of {SKILL_CODES}, {SKILLS_NONE!r}, or {SKILLS_ALL!r}"
            )
        if token in skills:
            _fail(raw_row, f"skills-duty cell {cell!r} repeats skill code {token!r}")
        skills.append(token)
    return skills


def _is_cyrillic_letter(token: str) -> bool:
    return len(token) == 1 and "Ѐ" <= token <= "ӿ"


def _parse_letters(inventory_cell: str, raw_row: str) -> list[str]:
    """Letters of a literacy row, per the arc document's inventory rule.

    No bolded ``**N letters**`` count -> empty list, cell not scanned.
    Otherwise: text after the count, parenthesised groups deleted, cut at the
    first semicolon; keep whitespace-split tokens stripped of ``.,:`` that are
    exactly one Cyrillic letter, first occurrence only. Length must equal N.
    """
    match = BOLD_LETTER_COUNT_RE.search(inventory_cell)
    if not match:
        return []
    expected = int(match.group(1))
    text = PAREN_GROUP_RE.sub("", inventory_cell[match.end() :])
    text = text.split(";", 1)[0]
    letters: list[str] = []
    for token in text.split():
        token = token.strip(".,:")
        if _is_cyrillic_letter(token) and token not in letters:
            letters.append(token)
    if len(letters) != expected:
        _fail(
            raw_row,
            f"bolded count says {expected} letters but the rule extracts {len(letters)}: {letters!r}",
        )
    return letters


def parse_positions(doc_text: str) -> list[dict]:
    """Parse the arc document into one record per position (roll-up excluded)."""
    tables = _find_position_tables(doc_text)
    literacy_rows = tables["literacy"]
    main_rows = tables["main"]
    if not literacy_rows:
        raise ArcGenerationError("literacy position table has no data rows")
    if not main_rows:
        raise ArcGenerationError("main position table has no data rows")

    roll_raw, roll_cells = main_rows[0]
    roll_match = POSITION_RANGE_RE.match(roll_cells[0])
    if not roll_match:
        _fail(roll_raw, f"first row of the main table must be the literacy roll-up range row, got {roll_cells[0]!r}")
    roll_start, roll_end = int(roll_match.group(1)), int(roll_match.group(2))
    if roll_start != 1 or roll_end != len(literacy_rows):
        _fail(
            roll_raw,
            f"roll-up range {roll_cells[0]!r} does not span 1..{len(literacy_rows)} (the literacy table rows)",
        )
    roll_phase = roll_cells[2]
    roll_skills_text = roll_cells[4]
    roll_skills = _parse_skills(roll_skills_text, roll_raw)
    roll_total = _int_cell(roll_cells[5], roll_raw, "roll-up lesson total")
    _standard_line_refs(roll_raw)

    records: list[dict] = []
    for raw, cells in literacy_rows:
        records.append(
            {
                "position": _position_int(cells[0], raw),
                "slug": _slug(cells[1], raw),
                "est_lessons": _int_cell(cells[4], raw, "Est. lessons"),
                "job": cells[2],
                "inventory_text": cells[3],
                "phase": roll_phase,
                "skills_text": roll_skills_text,
                "skills": list(roll_skills),
                "standard_line_refs": _standard_line_refs(raw),
                "letters": _parse_letters(cells[3], raw),
            }
        )

    literacy_sum = sum(record["est_lessons"] for record in records)
    if literacy_sum != roll_total:
        raise ArcGenerationError(
            f"sum of literacy est_lessons is {literacy_sum}, but the roll-up row says {roll_total}\n  row: {roll_raw.strip()}"
        )

    for raw, cells in main_rows[1:]:
        records.append(
            {
                "position": _position_int(cells[0], raw),
                "slug": _slug(cells[1], raw),
                "est_lessons": _int_cell(cells[5], raw, "L"),
                "job": cells[3],
                "inventory_text": None,
                "phase": cells[2],
                "skills_text": cells[4],
                "skills": _parse_skills(cells[4], raw),
                "standard_line_refs": _standard_line_refs(raw),
            }
        )

    positions = [record["position"] for record in records]
    if positions != list(range(1, len(records) + 1)):
        raise ArcGenerationError(f"positions are not contiguous from 1 in document order: {positions!r}")
    slugs = [record["slug"] for record in records]
    if len(set(slugs)) != len(slugs):
        duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
        raise ArcGenerationError(f"duplicate slugs in the arc document: {duplicates!r}")

    stated_total, stated_sentence = _stated_lesson_total(doc_text)
    computed_total = sum(record["est_lessons"] for record in records)
    if computed_total != stated_total:
        raise ArcGenerationError(
            f"the stated lesson total is {stated_total} but the est_lessons cells sum to {computed_total}\n"
            f"  sentence: {stated_sentence}"
        )
    return records


def render_arc_yaml(doc_bytes: bytes, doc_rel_path: str) -> str:
    """Render the full _arc.yaml text for an arc document (bytes + repo-relative path)."""
    records = parse_positions(doc_bytes.decode("utf-8"))
    data = {
        "arc_schema": 1,
        "source": {
            "path": doc_rel_path,
            "sha256": hashlib.sha256(doc_bytes).hexdigest(),
        },
        "est_lessons_total": sum(record["est_lessons"] for record in records),
        "positions": records,
    }
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=10**6)


def generate_yaml(doc_path: Path) -> str:
    """Generate the _arc.yaml text from an arc document path."""
    doc_bytes = doc_path.read_bytes()
    try:
        rel_path = doc_path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel_path = doc_path.as_posix()
    return render_arc_yaml(doc_bytes, rel_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml from the reviewed arc document "
            "(docs/epics/fresh-build-<level>-arc.md) by parsing its position tables.\n"
            "Use it after the arc document changes; never edit _arc.yaml by hand — the committed YAML must be "
            "byte-identical to a fresh run of this generator."
        ),
        epilog="""Examples:
  .venv/bin/python scripts/curriculum/arc/generate_arc.py --level a1 --write
  .venv/bin/python scripts/curriculum/arc/generate_arc.py --level a1 --check

Outputs:
  --write   writes curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml (overwrites)
  --check   writes nothing; compares a fresh generation against the committed file
Exit codes:
  0  generation succeeded / committed file is byte-identical
  1  --check found the committed file missing or different
  2  the arc document could not be parsed (the offending row is quoted), or bad CLI usage
Related:
  Loader: scripts/curriculum/arc/loader.py (validates against schemas/arc.schema.json and source.sha256)
  Schema: schemas/arc.schema.json; source doc: docs/epics/fresh-build-a1-arc.md; issue #8411
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--level",
        default="a1",
        choices=SUPPORTED_LEVELS,
        help="Level whose arc is generated; selects docs/epics/fresh-build-<level>-arc.md and "
        "curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml (default: a1; only a1 exists today)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Compare a fresh generation against the committed _arc.yaml; exit 1 if missing or different",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write the generated YAML to curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml, overwriting it",
    )
    parser.add_argument(
        "--doc",
        type=Path,
        default=None,
        help="Override the arc document path (default: docs/epics/fresh-build-<level>-arc.md); "
        "used by tests with mutated temporary copies, e.g. --doc /tmp/arc.md",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override the _arc.yaml path that --write writes and --check compares against "
        "(default: curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    doc_path = args.doc or REPO_ROOT / ARC_DOC_REL.format(level=args.level)
    out_path = args.output or REPO_ROOT / ARC_OUT_REL.format(level=args.level)
    try:
        generated = generate_yaml(doc_path)
    except (ArcGenerationError, FileNotFoundError, UnicodeDecodeError) as exc:
        print(f"error: cannot generate the arc from {doc_path}: {exc}", file=sys.stderr)
        return 2
    if args.write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(generated, encoding="utf-8")
        print(f"wrote {out_path} ({len(generated.splitlines())} lines)")
        return 0
    if not out_path.exists():
        print(f"error: {out_path} does not exist; run with --write", file=sys.stderr)
        return 1
    committed = out_path.read_text(encoding="utf-8")
    if committed == generated:
        print(f"ok: {out_path} is byte-identical to a fresh generation from {doc_path}")
        return 0
    print(
        f"error: {out_path} differs from a fresh generation from {doc_path}; "
        "regenerate with --write (never edit _arc.yaml by hand)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
