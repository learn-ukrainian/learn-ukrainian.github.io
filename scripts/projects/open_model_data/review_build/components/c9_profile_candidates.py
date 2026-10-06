"""Generate unapproved bibliographic locator candidates for human/author inspection.

Candidates are never loaded by the extractor. Only inspected entries copied to
c9_profiles.json become component data. No page prose is written to that file.
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path

from .c9_identity import FIELDS, GRADE, LEVEL
from .c9_queries import ELIGIBLE_SQL

IMPRINT = re.compile(
    r"(?P<title>[^\n/:]{3,180}?)\s*:\s*"
    r"(?P<level>(?:підручник|підручн?\.|навчальний посібник|навч\.\s*посіб)[^/]{0,350})/\s*"
    r"(?P<authors>[^—–]{1,300}?)\s*(?:[—–]|[ \t]+-[ \t]+)\s*[^:\n]{1,80}:\s*"
    r"(?P<publisher>[^,\n]{1,120}?),\s*(?P<year>(?:19|20)[0-9]{2})\b",
    re.I,
)


def locator(text, start, end):
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    first, last = text[:start].count("\n") + 1, text[:end].count("\n") + 1
    return {
        "lines": [first, last],
        "columns": [start - (text.rfind("\n", 0, start) + 1), end - (text.rfind("\n", 0, end) + 1)],
        "text": text[start:end],
    }, [start, end]


def candidates(pages):
    result = {}
    for row in pages:
        text, book = row["full_text"], row["source_file"]
        for match in IMPRINT.finditer(text):
            grammar = LEVEL if book.startswith("uni-") else GRADE
            level = grammar.search(match.group("level"))
            if level is None:
                continue
            spans = {key: match.span(key) for key in FIELDS if key != "grade"}
            spans["grade"] = [i + match.start("level") for i in level.span()]
            # Candidate only: expose preceding line locators for wrapped titles.
            start, end = spans["title"]
            start = text.rfind("\n", 0, start) + 1
            spans["title"] = start, end
            fields, offsets = {}, {}
            for key, (start, end) in spans.items():
                fields[key], offsets[key] = locator(text, start, end)
            result.setdefault(book, []).append(
                {
                    "page_index": row["page_start"],
                    "identity_source": "imprint",
                    "fields": fields,
                    "field_offsets": offsets,
                }
            )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate private C9 bibliographic locator candidates.\n"
        "Use for title/imprint inspection; candidates never authorize admission.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example:
  /path/to/shared/.venv/bin/python -m scripts.projects.open_model_data.review_build.components.c9_profile_candidates --database /absolute/sources.db --out "$TMPDIR/c9-candidates.json"
Outputs: private 0600 JSON at --out; existing output refused; database opened read-only.
Exit codes: 0 generated; 2 invalid arguments; other failures raise and exit nonzero.
Related: Refs #8341; components/c9_profiles.json; private review build C9.
""",
    )
    parser.add_argument(
        "--database", required=True, type=Path, help="Absolute source SQLite database, opened read-only"
    )
    parser.add_argument("--out", required=True, type=Path, help="Private candidate JSON file outside repository")
    args = parser.parse_args(argv)
    if not args.database.is_absolute():
        parser.error("--database must be absolute")
    with sqlite3.connect(args.database.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"SELECT * FROM (SELECT *,row_number() OVER (PARTITION BY source_file ORDER BY page_start) AS ordinal "
            f"FROM textbook_sections WHERE {ELIGIBLE_SQL}) WHERE ordinal<=4 ORDER BY source_file,page_start"
        )
        result = candidates(rows)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump({"schema": "c9-profile-candidates.v1", "books": result}, handle, ensure_ascii=False, indent=2)
    args.out.chmod(0o600)
    print(json.dumps({"candidate_books": len(result)}))


if __name__ == "__main__":
    main()
