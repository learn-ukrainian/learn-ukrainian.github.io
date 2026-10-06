"""Reviewed bibliographic profiles; missing or changed verbatim fields refuse."""

import json
import re
from dataclasses import dataclass

from ..errors import require

PROFILE_PATH = "scripts/projects/open_model_data/review_build/components/c9_profiles.json"
FIELDS = ("title", "authors", "grade", "publisher", "year")
CATALOGUE = re.compile(r"^[ \t]*[A-ZА-ЯІЇЄҐÂ0-9][ \t]*[-–]?[0-9]{2,4}[ \t]+")
GRADE = re.compile(
    r"\b(?:[1-9]|1[01])(?:[ \t]*\((?:10|11)\)|[-–](?:[1-9]|1[01]))?[ \t]*[- ]?(?:го|й|х)?\s*(?:клас[уаів]*\b|кл\.)",
    re.I,
)
LEVEL = re.compile(r"\b(?:студентів|вищих навчальних закладів|закладів вищої освіти)\b", re.I)


@dataclass(frozen=True)
class Identity:
    fields: dict
    field_rows: dict

    def text(self, key):
        return self.field_rows[key]["full_text"][slice(*self.fields[key])]


def load_profiles(reader):
    data = json.loads(reader.read_repository_config(PROFILE_PATH))
    require(data.get("schema") == "c9-book-profiles.v1", "identity_profiles")
    return data["books"]


def field_span(text, field):
    """Line bounds plus character columns, both LF-based and independently checked."""
    lines = text.split("\n")
    first, last = field["lines"]
    start_col, end_col = field["columns"]
    if not (1 <= first <= last <= len(lines)):
        return None
    if not (0 <= start_col <= len(lines[first - 1]) and 0 <= end_col <= len(lines[last - 1])):
        return None
    start = sum(len(line) + 1 for line in lines[: first - 1]) + start_col
    end = sum(len(line) + 1 for line in lines[: last - 1]) + end_col
    if start >= end or text[start:end] != field["text"]:
        return None
    return start, end


def identity(pages, profiles):
    """Authenticate each designated title/imprint field within the same book."""
    if not pages:
        return None
    profile = profiles.get(pages[0]["source_file"])
    if profile is None or profile.get("identity_source") not in {"title_page", "imprint"}:
        return None
    if set(profile.get("fields", {})) != set(FIELDS):
        return None
    fields, field_rows = {}, {}
    for key in FIELDS:
        field = profile["fields"][key]
        if field.get("identity_source", profile["identity_source"]) not in {"title_page", "imprint"}:
            return None
        rows = [
            p
            for p in pages
            if p["source_file"] == pages[0]["source_file"]
            and p["page_start"] == field.get("page_index", profile["page_index"])
        ]
        if len(rows) != 1:
            return None
        row = rows[0]
        span = field_span(row["full_text"], field)
        if span is None or list(span) != profile.get("field_offsets", {}).get(key):
            return None
        fields[key] = span
        field_rows[key] = row
    # Strip a printed library code by the same rule for every book; no rewritten bytes.
    title = field_rows["title"]["full_text"][slice(*fields["title"])]
    match = CATALOGUE.match(title)
    if match:
        fields["title"] = (fields["title"][0] + match.end(), fields["title"][1])
    if not all(field_rows[key]["full_text"][slice(*span)].strip() for key, span in fields.items()):
        return None
    level = field_rows["grade"]["full_text"][slice(*fields["grade"])]
    grammar = LEVEL if pages[0]["source_file"].startswith("uni-") else GRADE
    if not grammar.fullmatch(level) or not re.fullmatch(r"(?:19|20)[0-9]{2}", profile["fields"]["year"]["text"]):
        return None
    return Identity(fields, field_rows)


def profile_binding(profiles):
    """Gate re-reads designated page and spans, independently of candidate citations."""
    rules = []
    selectors = [
        ({"area": "slots", "slot": slot}, field) for slot, field in (("book_title", "title"), ("grade", "grade"))
    ] + [
        ({"area": "context", "slot": "textbook_identity_attestation", "index": index}, field)
        for index, field in enumerate(FIELDS)
    ]
    for selector, field in selectors:
        cases = []
        for book, profile in sorted(profiles.items()):
            f = profile["fields"][field]
            # SQL uses line+column locators encoded below as exact prefix lengths.
            prefix = profile["field_offsets"][field]
            start, end = prefix
            if field == "title" and (match := CATALOGUE.match(f["text"])):
                start += match.end()
            quote = lambda s: "'" + s.replace("'", "''") + "'"  # noqa: E731
            cases.append(
                f"WHEN source_file={quote(book)} AND page_start={f.get('page_index', profile['page_index'])} "
                f"THEN substr(full_text,{start + 1},{end - start})"
            )
        sql = "SELECT CASE " + " ".join(cases) + " END FROM textbook_sections WHERE source_file=? AND section_id=?"
        if not cases:
            sql = "SELECT NULL FROM textbook_sections WHERE source_file=? AND section_id=?"
        sql = (
            "SELECT expected FROM ("
            + sql.replace(" END FROM", " END AS expected FROM")
            + ") WHERE expected IS NOT NULL"
        )
        rules.append(
            {
                "op": "set_query_equal",
                "values": [selector],
                "normalizer": "identity",
                "queries": [
                    {
                        "query": {"kind": "sql", "store": "sources.db", "sql": sql, "parameters": []},
                        "parameters": [
                            {"area": "slots", "slot": "section_title", "field": "source_file"},
                            {**selector, "field": "section_id"},
                        ],
                    }
                ],
            }
        )
    return rules
