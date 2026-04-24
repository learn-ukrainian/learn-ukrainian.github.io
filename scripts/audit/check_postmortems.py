#!/usr/bin/env python3
"""Validate bug postmortems and keep their index current.

Postmortems live at ``docs/bug-autopsies/``. This script validates the
minimum fields that make an autopsy useful and regenerates the INDEX.md
table between sentinel markers.

Usage:
    .venv/bin/python -m scripts.audit.check_postmortems
    .venv/bin/python -m scripts.audit.check_postmortems --quiet
    .venv/bin/python -m scripts.audit.check_postmortems --regenerate-index

Exit codes:
    0 = clean
    1 = validation errors
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
POSTMORTEM_DIR = PROJECT_ROOT / "docs" / "bug-autopsies"
INDEX_PATH = POSTMORTEM_DIR / "INDEX.md"

INDEX_START = "<!-- INDEX-START -->"
INDEX_END = "<!-- INDEX-END -->"
TABLE_HEADER = "| Date | Issue | Category | Summary |\n|------|-------|----------|---------|"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
DATE_LINE_RE = re.compile(r"^\*\*Date:\*\*\s*(.+?)\s*$", re.MULTILINE)
ISSUE_LINE_RE = re.compile(r"^\*\*Issue:\*\*\s*(.+?)\s*$", re.MULTILINE)
ISSUE_REF_RE = re.compile(r"(?:#\d+|github\.com/[^/\s]+/[^/\s]+/issues/\d+)")
COMMIT_REF_RE = re.compile(r"(?:\b[0-9a-f]{7,40}\b|github\.com/[^/\s]+/[^/\s]+/commit/[0-9a-f]+)")


@dataclass(frozen=True)
class IndexRow:
    """One row in docs/bug-autopsies/INDEX.md."""

    date: str
    issue: str
    category: str
    summary: str

    @classmethod
    def from_markdown_row(cls, line: str) -> IndexRow | None:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            return None
        if cells[0] in {"Date", "------"}:
            return None
        return cls(date=cells[0], issue=cells[1], category=cells[2], summary=cells[3])

    def to_markdown(self) -> str:
        return f"| {self.date} | {self.issue} | {self.category} | {self.summary} |"


@dataclass(frozen=True)
class PostmortemRecord:
    """One parsed postmortem file."""

    path: Path
    slug: str
    title: str
    date: str
    issue: str
    summary: str
    content: str


@dataclass
class CheckResult:
    """Aggregated postmortem validation findings."""

    errors: list[str] = field(default_factory=list)
    records: list[PostmortemRecord] = field(default_factory=list)
    index_changed: bool = False

    @property
    def exit_code(self) -> int:
        return 1 if self.errors else 0


def _postmortem_dir(project_root: Path) -> Path:
    return project_root / "docs" / "bug-autopsies"


def _index_path(project_root: Path) -> Path:
    return _postmortem_dir(project_root) / "INDEX.md"


def _relative(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _strip_title_prefix(title: str) -> str:
    title = title.strip()
    title = re.sub(r"^Bug Autopsy\s*[:—-]\s*", "", title)
    title = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[:—-]\s*", "", title)
    return title.strip()


def _first_title(content: str, fallback: str) -> str:
    match = TITLE_RE.search(content)
    if not match:
        return fallback
    return _strip_title_prefix(match.group(1))


def _date_from(path: Path, content: str) -> str:
    date_match = DATE_LINE_RE.search(content)
    if date_match:
        return date_match.group(1).strip()

    filename_match = re.search(r"\d{4}-\d{2}-\d{2}", path.name)
    if filename_match:
        return filename_match.group(0)

    title_match = re.search(r"\d{4}-\d{2}-\d{2}", content[:300])
    if title_match:
        return title_match.group(0)

    return "—"


def _issue_from(content: str) -> str:
    issue_line = ISSUE_LINE_RE.search(content)
    if issue_line:
        return issue_line.group(1).strip()

    issue_ref = re.search(r"#\d+", content[:800])
    if issue_ref:
        return issue_ref.group(0)

    return "—"


def _summary_from(title: str, content: str) -> str:
    symptom_line = re.search(r"^\*\*Symptom:\*\*\s*(.+?)\s*$", content, re.MULTILINE)
    if symptom_line:
        return symptom_line.group(1).strip()
    return title


def _load_postmortems(project_root: Path) -> list[PostmortemRecord]:
    postmortem_dir = _postmortem_dir(project_root)
    if not postmortem_dir.exists():
        return []

    records: list[PostmortemRecord] = []
    for path in sorted(postmortem_dir.glob("*.md")):
        if path.name == "INDEX.md":
            continue
        content = path.read_text("utf-8")
        title = _first_title(content, path.stem)
        records.append(
            PostmortemRecord(
                path=path,
                slug=path.stem,
                title=title,
                date=_date_from(path, content),
                issue=_issue_from(content),
                summary=_summary_from(title, content),
                content=content,
            )
        )
    return records


def _has_heading(content: str, accepted: tuple[str, ...]) -> bool:
    accepted_normalized = {item.lower() for item in accepted}
    for _, heading in HEADING_RE.findall(content):
        normalized = heading.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        if normalized in accepted_normalized:
            return True
    return False


def _has_bold_sentence_label(content: str, accepted: tuple[str, ...]) -> bool:
    for label in accepted:
        if re.search(rf"^\*\*{re.escape(label)}[.:]\*\*", content, re.MULTILINE | re.IGNORECASE):
            return True
    return False


def _has_symptom(record: PostmortemRecord) -> bool:
    content = record.content
    return (
        _has_heading(content, ("Symptom", "Symptoms", "What Broke", "What broke"))
        or _has_bold_sentence_label(content, ("Symptom", "What broke"))
    )


def _has_root_cause(record: PostmortemRecord) -> bool:
    content = record.content
    return (
        _has_heading(
            content,
            (
                "Root cause",
                "Root causes",
                "Root Causes (3 separate bugs)",
                "Why",
                "Why — Three Interacting Bugs",
            ),
        )
        or _has_bold_sentence_label(content, ("Root cause", "Root causes", "Why"))
    )


def _has_prevention(record: PostmortemRecord) -> bool:
    content = record.content
    return (
        _has_heading(content, ("Prevention", "Pinning test"))
        or _has_bold_sentence_label(content, ("Prevention",))
    )


def _links_section(content: str) -> str | None:
    link_heading = re.search(r"^##\s+Links\s*$", content, re.MULTILINE | re.IGNORECASE)
    if not link_heading:
        return None

    following_heading = re.search(
        r"^##\s+",
        content[link_heading.end() :],
        re.MULTILINE,
    )
    if following_heading:
        return content[link_heading.end() : link_heading.end() + following_heading.start()]
    return content[link_heading.end() :]


def _has_links(record: PostmortemRecord) -> bool:
    content = record.content
    if _links_section(content) is not None:
        return True

    # Historical autopsies predate a strict Links section. Accept the link
    # surfaces they already use so this automation does not force a backfill.
    return (
        bool(ISSUE_LINE_RE.search(content))
        or bool(ISSUE_REF_RE.search(content[:1000]))
        or _has_heading(content, ("Files Changed", "See also"))
        or "Origin: [" in content
    )


def _check_required_fields(record: PostmortemRecord, project_root: Path) -> list[str]:
    missing = []
    if not _has_symptom(record):
        missing.append("Symptom")
    if not _has_root_cause(record):
        missing.append("Root cause")
    if not _has_prevention(record):
        missing.append("Prevention")
    if not _has_links(record):
        missing.append("Links")

    errors = [
        f"{_relative(record.path, project_root)} — missing required field: {field}"
        for field in missing
    ]

    links = _links_section(record.content)
    if links is not None:
        if not ISSUE_REF_RE.search(links):
            errors.append(
                f"{_relative(record.path, project_root)} — Links section present but no GH issue ref"
            )
        if not COMMIT_REF_RE.search(links):
            errors.append(
                f"{_relative(record.path, project_root)} — Links section present but no commit SHA"
            )

    return errors


def _parse_existing_rows(index_text: str) -> list[IndexRow]:
    rows = []
    for line in index_text.splitlines():
        if not line.startswith("|"):
            continue
        row = IndexRow.from_markdown_row(line)
        if row is not None:
            rows.append(row)
    return rows


def _generated_row(record: PostmortemRecord) -> IndexRow:
    return IndexRow(
        date=record.date,
        issue=record.issue,
        category=record.slug,
        summary=record.summary,
    )


def _index_rows(records: list[PostmortemRecord], index_text: str) -> list[IndexRow]:
    existing_rows = _parse_existing_rows(index_text)
    if not existing_rows:
        return sorted(
            (_generated_row(record) for record in records),
            key=lambda row: (row.category.lower(), row.date, row.summary.lower()),
        )

    # Preserve historical rows exactly. Existing index categories sometimes
    # describe the failure class rather than the filename slug, and multi-bug
    # files intentionally have multiple rows. Use the table as curated data,
    # then append generated rows only for genuinely new files.
    rows = list(existing_rows)
    covered_categories = {row.category for row in rows}
    covered_issues = {row.issue for row in rows if row.issue != "—"}
    for record in records:
        if record.slug not in covered_categories and record.issue not in covered_issues:
            rows.append(_generated_row(record))

    return rows


def _build_index_block(rows: list[IndexRow]) -> str:
    table = "\n".join([TABLE_HEADER, *(row.to_markdown() for row in rows)])
    return f"{INDEX_START}\n{table}\n{INDEX_END}"


def _legacy_table_bounds(index_text: str) -> tuple[int, int] | None:
    header_match = re.search(
        r"^\| Date \| Issue \| Category \| Summary \|\n"
        r"^\|[- |]+\|\n",
        index_text,
        re.MULTILINE,
    )
    if not header_match:
        return None

    end = header_match.end()
    while True:
        next_newline = index_text.find("\n", end)
        if next_newline == -1:
            return header_match.start(), len(index_text)
        next_line_start = next_newline + 1
        if not index_text[next_line_start:].startswith("|"):
            return header_match.start(), next_newline
        end = next_line_start


def regenerate_index(project_root: Path = PROJECT_ROOT) -> bool:
    """Regenerate INDEX.md in place. Returns True if the file changed."""
    index_path = _index_path(project_root)
    if not index_path.exists():
        return False

    index_text = index_path.read_text("utf-8")
    records = _load_postmortems(project_root)
    new_block = _build_index_block(_index_rows(records, index_text))

    start = index_text.find(INDEX_START)
    end = index_text.find(INDEX_END)
    if start >= 0 and end >= 0:
        new_text = index_text[:start] + new_block + index_text[end + len(INDEX_END) :]
    else:
        legacy_bounds = _legacy_table_bounds(index_text)
        if legacy_bounds is None:
            separator = "\n\n" if not index_text.endswith("\n\n") else ""
            new_text = f"{index_text}{separator}{new_block}\n"
        else:
            legacy_start, legacy_end = legacy_bounds
            new_text = index_text[:legacy_start] + new_block + index_text[legacy_end:]

    if new_text == index_text:
        return False
    index_path.write_text(new_text, "utf-8")
    return True


def run_check(
    *,
    project_root: Path = PROJECT_ROOT,
    regenerate: bool = True,
    regenerate_on_failure: bool = False,
) -> CheckResult:
    """Validate postmortems and optionally regenerate the index."""
    result = CheckResult(records=_load_postmortems(project_root))
    postmortem_dir = _postmortem_dir(project_root)

    if not postmortem_dir.exists():
        result.errors.append(f"{_relative(postmortem_dir, project_root)} — directory missing")
        return result

    for record in result.records:
        result.errors.extend(_check_required_fields(record, project_root))

    if regenerate and (regenerate_on_failure or not result.errors):
        result.index_changed = regenerate_index(project_root)

    return result


def _print_errors(errors: list[str]) -> None:
    for error in errors:
        print(f"❌ {error}")


def main(argv: list[str] | None = None, *, project_root: Path = PROJECT_ROOT) -> int:
    parser = argparse.ArgumentParser(
        description="Validate docs/bug-autopsies/ postmortems and regenerate INDEX.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  default              validate + regenerate INDEX.md when validation passes\n"
            "  --quiet              print only errors; stdout is empty on success\n"
            "  --regenerate-index   regenerate INDEX.md even if validation fails\n"
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only errors; silent on success for SessionStart hooks",
    )
    parser.add_argument(
        "--regenerate-index",
        action="store_true",
        help="Regenerate INDEX.md even if validation fails",
    )
    args = parser.parse_args(argv)

    result = run_check(
        project_root=project_root,
        regenerate=(not args.quiet or args.regenerate_index),
        regenerate_on_failure=args.regenerate_index,
    )

    if args.quiet:
        _print_errors(result.errors)
        return result.exit_code

    _print_errors(result.errors)
    if result.index_changed:
        print(f"✅ regenerated {_relative(_index_path(project_root), project_root)}")
    print(f"✅ {len(result.records)} postmortems validated")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
