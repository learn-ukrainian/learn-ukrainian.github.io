"""C9: authenticated printed headings and complete verbatim headed bodies.

This is a precision-first grammar, not a claim of exhaustive heading recall.
It admits explicit section markers only. Ambiguous numbered lines, multiline
headings and Roman-number headings require a separately reviewed grammar.
Book identity is parsed from a single printed bibliographic entry, never from
chunk titles, filenames, grade metadata or inferred author/publisher names.
Missing or conflicting identity withholds the whole book. Source text is never
repaired: only numeric whole-line excision is applied; hyphens are preserved.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from ..attribution import Attribution
from ..contract import Candidate, Citation, Value, canonical, digest
from ..errors import require
from ..gate import evidence_id
from ..transforms import transform
from . import ComponentContext
from .c9_queries import BODY_QUERY, ELIGIBLE_SQL, END_QUERY, HEADING_QUERY, UNIT_QUERY

SOURCE_SCHOOL = "textbooks"
SOURCE_UNIVERSITY = "university-textbooks"
FROZEN_COUNT = 11099
ALLOWED = re.compile(r"(?:[1-9]|1[01]|10-11)-klas-.+|uni-.+")
PAGE_PATTERN = r"[ \t]*[0-9]+[ \t]*"
LINE_POLICY = {"patterns": [PAGE_PATTERN]}
HEADING = re.compile(
    r"(?:§[ \t]*|(?:Тема|ТЕМА|Розділ|РОЗДІЛ) )"
    r"[0-9]{1,3}(?:\.[ \t]*|[ \t]+)[^\r\n]+"
)
GRADE = re.compile(r"\b(?:[1-9]|1[01])(?:[-–](?:[1-9]|1[01]))?[- ]?(?:го|й|х)?\s*клас[уаів]*\b")
LEVEL = re.compile(r"\b(?:студентів|вищих навчальних закладів|закладів вищої освіти)\b", re.I)
# A single bibliographic paragraph carries all five required fields, with
# punctuation delimiting each verbatim span. Never infer missing fields.
IMPRINT = re.compile(
    r"(?P<title>[^\n/:]{3,180}?)\s*:\s*"
    r"(?P<level>(?:підручник|підруч\.|навчальний посібник|навч\.\s*посіб)[^/]{0,350})/\s*"
    r"(?P<authors>[^—]{1,300}?)\s*—\s*[^:\n]{1,80}:\s*"
    r"(?P<publisher>[^,\n]{1,120}?),\s*(?P<year>(?:19|20)[0-9]{2})\b",
    re.I,
)
CONTENTS = re.compile(r"(?m)^[ \t]*(?:ЗМІСТ|Зміст)[ \t]*$|\.{3,}[ \t]*[0-9]+[ \t]*$")
EXERCISE = re.compile(r"(?im)^[ \t]*(?:Вправа|Вправи|Завдання|Запитання)\b")
ANSWER = re.compile(r"(?im)^[ \t]*(?:Відповідь|Відповіді|Розв'язання|Розв’язання)\b")


@dataclass(frozen=True)
class Heading:
    row: Mapping
    span: tuple[int, int]
    text: str


@dataclass(frozen=True)
class Identity:
    row: Mapping
    fields: Mapping[str, tuple[int, int]]
    span: tuple[int, int]

    def text(self, key):
        start, end = self.fields[key]
        return self.row["full_text"][start:end]


def headings(row: Mapping) -> list[Heading]:
    """Explicit markers on physical lines; ingester labels are never examined."""
    result, offset = [], 0
    # split on LF only, agreeing with the independent SQL page-line reader.
    for found in re.finditer(r"[^\n]+\n?|\n", row["full_text"]):
        line = found.group()
        title = line.strip(" \t\r\n")
        match = HEADING.fullmatch(title)
        if match and len(title) <= 180:
            tail = re.sub(r"^(?:§[ \t]*|(?:Тема|ТЕМА|Розділ|РОЗДІЛ) )", "", title)
            number = re.match(r"[0-9]+", tail)
            after = tail[number.end() :]
            body = after[1:] if after.startswith(".") else after
            if int(number.group()) > 0 and body.strip(" \t"):
                start = offset + len(line) - len(line.lstrip(" \t\r\n"))
                result.append(Heading(row, (start, start + len(title)), title))
        offset += len(line)
    return result


def identity(pages: list[Mapping]) -> Identity | None:
    """Resolve one consistent source-printed imprint in the book's edge pages."""
    if not pages:
        return None
    matches = []
    for row in pages[:8] + pages[-8:]:
        for match in IMPRINT.finditer(row["full_text"]):
            fields = {key: match.span(key) for key in ("title", "authors", "publisher", "year")}
            # Trim only span boundaries; no source bytes are rewritten.
            for key, (start, end) in fields.items():
                raw = row["full_text"][start:end]
                fields[key] = (start + len(raw) - len(raw.lstrip()), end - len(raw) + len(raw.rstrip()))
            level = match.group("level")
            grade = LEVEL.search(level) if row["source_file"].startswith("uni-") else GRADE.search(level)
            if grade is None:
                continue
            fields["grade"] = tuple(n + match.start("level") for n in grade.span())
            if any(not row["full_text"][s:e].strip() for s, e in fields.values()):
                continue
            matches.append(Identity(row, fields, match.span()))
    fingerprints = {tuple(item.text(k) for k in sorted(item.fields)) for item in matches}
    return matches[0] if len(fingerprints) == 1 else None


def ocr_damaged(text: str) -> bool:
    """Fixed positive screens; threshold is any replacement/control character.

    Three question marks or five repeated punctuation marks also flag damage.
    This screen is conservative evidence, not semantic OCR certification.
    """
    return (
        "\ufffd" in text
        or any(unicodedata.category(c) in {"Cc", "Cs"} and c not in "\n\r\t" for c in text)
        or bool(re.search(r"\?{3,}|([@#$%])\1{4,}", text))
    )


def running_head_ambiguous(pages: list[Mapping]) -> bool:
    """Refuse recurring nonnumeric edge lines instead of deleting guessed text.

    A line must occur on at least three distinct pages and at least half the
    book. Only the first/last nonempty line, at most 180 characters, counts.
    Repeated prose may also trigger this conservative withholding screen.
    """
    edges = Counter()
    for page in pages:
        lines = [line.strip() for line in page["full_text"].split("\n") if line.strip()]
        if not lines:
            continue
        edges.update(
            {line for line in (lines[0], lines[-1]) if len(line) <= 180 and not re.fullmatch(PAGE_PATTERN, line)}
        )
    return any(count >= 3 and 2 * count >= len(pages) for count in edges.values())


def citation(row: Mapping) -> Citation:
    source = SOURCE_UNIVERSITY if row["source_file"].startswith("uni-") else SOURCE_SCHOOL
    return Citation(
        source,
        "sources.db",
        "textbook_sections",
        f"section_id={row['section_id']}",
        "full_text",
        f"page {row['page_start']}",
        digest(row["full_text"].encode("utf-8")),
    )


def value(row: Mapping, slot: str, span: tuple[int, int], name="verbatim") -> Value:
    text = transform(name, row["full_text"], LINE_POLICY if name == "line_excision@1" else None).text
    return Value(slot, text[slice(*span)], (citation(row),), span, name)


def unit_id(heading: Heading) -> str:
    return canonical(
        [["sources.db", "textbook_sections", f"section_id={heading.row['section_id']}", list(heading.span)]]
    ).decode("utf-8")


class TextbookAttribution:
    """Only maps an explicit bibliographic template; instruction prose refuses."""

    FORM = "{authors}. {title}. {grade}. {publisher}, {year}."

    def __init__(self):
        self._cache = WeakKeyDictionary()

    def resolve(self, form, source, row, reader):
        require(form == self.FORM, "attribution_unresolved")
        cache = self._cache.setdefault(reader, {})
        book = row["source_file"]
        require(bool(ALLOWED.fullmatch(book)), "attribution_unresolved")
        expected_source = SOURCE_UNIVERSITY if book.startswith("uni-") else SOURCE_SCHOOL
        require(source.source_id == expected_source, "attribution_unresolved")
        if book not in cache:
            connection = reader.connections["sources.db"]
            pages = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM textbook_sections WHERE source_file=? ORDER BY page_start", (book,)
                )
            ]
            cache[book] = identity(pages)
        item = cache[book]
        require(item is not None, "attribution_unresolved")
        # Pin the actual imprint column, including on response-page citations.
        reader.field(citation(item.row))
        return Attribution(form.format(**{key: item.text(key) for key in item.fields}), form)


def selector(area, slot, **extra):
    return {"area": area, "slot": slot, **extra}


ANCHOR = selector("slots", "section_title")
PARAMETERS = [{**ANCHOR, "field": "section_id"}, ANCHOR]
BINDING = {
    "schema": "binding-spec.v1",
    "rules": [
        {
            "op": "one_group",
            "values": [
                {**ANCHOR, "field": "source_file"},
                selector("slots", "book_title", field="source_file"),
                selector("slots", "grade", field="source_file"),
                selector("context", "textbook_identity_attestation", field="source_file"),
                selector("response", "body", match="all", field="source_file"),
            ],
        },
        {
            "op": "same_row",
            "values": [
                selector("slots", "book_title"),
                selector("slots", "grade"),
                selector("context", "textbook_identity_attestation"),
            ],
        },
        {
            "op": "set_query_equal",
            "values": [ANCHOR],
            "normalizer": "identity",
            "queries": [{"query": HEADING_QUERY, "parameters": PARAMETERS}],
        },
        {
            "op": "set_query_equal",
            "values": [selector("response", "body", match="all")],
            "normalizer": "identity",
            "queries": [{"query": BODY_QUERY, "parameters": PARAMETERS}],
        },
        {
            "op": "contiguous_pages",
            "values": [selector("response", "body", match="all", field="page_start")],
            "first": {**ANCHOR, "field": "page_start"},
            "next_heading": {"query": END_QUERY, "parameters": PARAMETERS},
            "source_field": "source_file",
        },
    ],
}

# The gate parses these declarative captures independently. Same-book and
# same-row checks alone would admit a title replaced by its publisher's span.
for _slot, _group in (("book_title", "title"), ("grade", "level")):
    _rule = {
        "op": "regex_span",
        "values": [selector("slots", _slot)],
        "pattern": IMPRINT.pattern,
        "flags": int(IMPRINT.flags),
        "group": _group,
        "trim": True,
    }
    if _slot == "grade":
        _rule["nested"] = {"pattern": f"(?:{GRADE.pattern})|(?:{LEVEL.pattern})", "flags": int(re.I)}
    BINDING["rules"].append(_rule)


class Textbooks:
    def __init__(self):
        self.files = {}
        adapter = TextbookAttribution()
        self.adapters = {SOURCE_SCHOOL: adapter, SOURCE_UNIVERSITY: adapter}
        self.spec = {
            "operations": ["verbatim_section"],
            "unit_grain": "printed_heading_explicit_marker_v1",
            "context_serializer": "text",
            "response_serializer": "text",
            "transforms": {"line_excision@1": LINE_POLICY},
            "reasons": {
                "accepted": ["printed_heading"],
                "rejected": [],
                "excluded": [],
                "withheld": [
                    "book_identity_unresolved",
                    "book_ocr_damage",
                    "ocr_damage",
                    "table_of_contents",
                    "exercise_without_answer",
                    "page_gap",
                    "empty_body",
                    "repeated_heading",
                    "running_head_unresolved",
                    "attribution_unresolved",
                    "locator_unavailable",
                    "catalog_inapplicable",
                ],
            },
            "operation_specs": {
                "verbatim_section": {
                    "unit_query": UNIT_QUERY,
                    "frozen_count": FROZEN_COUNT,
                    "binding": BINDING,
                    "unit_id": {
                        "format": "citation.v1",
                        "primary": [
                            {
                                "selector": ANCHOR,
                                "store": "sources.db",
                                "table": "textbook_sections",
                                "span": True,
                            }
                        ],
                    },
                }
            },
        }

    def iter_candidates(self, ctx: ComponentContext):
        connection = ctx.reader.connections["sources.db"]
        # Only filenames (never text) are read to authenticate the exact request
        # allowlist. The independent query's domain must equal that allowlist.
        eligible = {
            r[0] for r in connection.execute(f"SELECT DISTINCT source_file FROM textbook_sections WHERE {ELIGIBLE_SQL}")
        }
        supplied = set()
        for entry in ctx.request["compatibility"]:
            if entry["source_id"] in self.adapters and entry["table"] == "textbook_sections":
                supplied.update(entry.get("allowlisted_files", ()))
        require(supplied == eligible, "textbook_allowlist")
        pages_by_book = {}
        for row in connection.execute(
            f"SELECT * FROM textbook_sections WHERE {ELIGIBLE_SQL} ORDER BY source_file,page_start,section_id"
        ):
            pages_by_book.setdefault(row["source_file"], []).append(dict(row))
        for pages in pages_by_book.values():
            yield from self._book(pages)

    def _book(self, pages):
        printed = [heading for row in pages for heading in headings(row)]
        imprint = identity(pages)
        duplicates = Counter(h.text for h in printed)
        unresolved_head = running_head_ambiguous(pages)
        # Strictly greater than 30%, using integer arithmetic at the boundary.
        damaged_book = 10 * sum(ocr_damaged(p["full_text"]) for p in pages) > 3 * len(pages)
        for index, heading in enumerate(printed):
            reason = "printed_heading"
            slot_heading = value(heading.row, "section_title", heading.span)
            slots, context, response = [slot_heading], [], []
            next_heading = printed[index + 1] if index + 1 < len(printed) else None
            end_page = next_heading.row["page_start"] if next_heading else pages[-1]["page_start"] + 1
            start_page = heading.row["page_start"]
            selected = [p for p in pages if start_page <= p["page_start"] <= end_page]
            if next_heading and next_heading.span[0] == 0:
                selected = [p for p in selected if p["page_start"] < end_page]
            for page in selected:
                cleaned = transform("line_excision@1", page["full_text"], LINE_POLICY).text
                start = 0
                if page["section_id"] == heading.row["section_id"]:
                    start = len(transform("line_excision@1", page["full_text"][: heading.span[1]], LINE_POLICY).text)
                end = len(cleaned)
                if next_heading and page["section_id"] == next_heading.row["section_id"]:
                    end = len(transform("line_excision@1", page["full_text"][: next_heading.span[0]], LINE_POLICY).text)
                if start < end:
                    response.append(value(page, "body", (start, end), "line_excision@1"))
                else:
                    reason = "empty_body"
            if imprint is None:
                reason = "book_identity_unresolved"
            else:
                slots = [
                    value(imprint.row, "book_title", imprint.fields["title"]),
                    value(imprint.row, "grade", imprint.fields["grade"]),
                    slot_heading,
                ]
                context = [value(imprint.row, "textbook_identity_attestation", imprint.span)]
            if damaged_book:
                reason = "book_ocr_damage"
            elif any(ocr_damaged(p["full_text"]) for p in selected):
                reason = "ocr_damage"
            elif any(CONTENTS.search(p["full_text"]) for p in selected):
                reason = "table_of_contents"
            elif any(n > 1 for n in duplicates.values()):
                # Repeated marker lines can be running heads: withhold the book
                # rather than let them truncate an earlier response silently.
                reason = "repeated_heading"
            elif unresolved_head:
                reason = "running_head_unresolved"
            elif selected and [p["page_start"] for p in selected] != list(
                range(start_page, selected[-1]["page_start"] + 1)
            ):
                reason = "page_gap"
            else:
                body = "\n".join(v.text for v in response)
                if EXERCISE.search(body) and not ANSWER.search(body):
                    reason = "exercise_without_answer"
                elif not body.strip():
                    reason = "empty_body"
            outcome = "accepted" if reason == "printed_heading" else "withheld"
            yield Candidate(
                "C9",
                unit_id(heading),
                outcome,
                reason,
                () if outcome == "accepted" else (evidence_id(slot_heading.citations[0]),),
                "verbatim_section",
                tuple(slots),
                tuple(context),
                tuple(response),
                (),
            )


COMPONENT = Textbooks()
