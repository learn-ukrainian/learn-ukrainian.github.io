"""C9: authenticated printed headings and complete verbatim headed bodies.

This is a precision-first grammar, not a claim of exhaustive heading recall.
It admits explicit section markers only. Ambiguous numbered lines, multiline
headings and Roman-number headings require a separately reviewed grammar.
Book identity is parsed from a single printed bibliographic entry, never from
chunk titles, filenames, grade metadata or inferred author/publisher names.
Missing or conflicting identity withholds the whole book. Source text is never
repaired: only page-number and authenticated running-head line excision is
applied; hyphens are preserved.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import ClassVar
from weakref import WeakKeyDictionary

from ..attribution import Attribution
from ..contract import Candidate, Citation, Value, canonical, digest, values
from ..errors import require
from ..gate import REASONING, evidence_id
from ..transforms import transform
from . import ComponentContext
from .c9_queries import BODY_QUERY, ELIGIBLE_SQL, END_QUERY, EXCISION_QUERY, HEADING_QUERY, UNIT_QUERY

SOURCE_SCHOOL = "textbooks"
SOURCE_UNIVERSITY = "textbooks_university"
FROZEN_COUNT = 7261
ALLOWED = re.compile(r"(?:[1-9]|1[01]|10-11)-klas-.+|uni-.+")
PAGE_PATTERN = r"[ \t]*[0-9]+[ \t]*"
LINE_POLICY = {
    "patterns": [PAGE_PATTERN],
    "line_query": EXCISION_QUERY,
    "table": "textbook_sections",
    "field": "full_text",
}
HEADING = re.compile(
    r"(?:§[ \t]*|(?:Тема|ТЕМА|Розділ|РОЗДІЛ) )"
    r"[0-9]{1,3}(?:\.[ \t]*|[ \t]+)[^\r\n]+"
)
GRADE = re.compile(r"\b(?:[1-9]|1[01])(?:[-–](?:[1-9]|1[01]))?[- ]?(?:го|й|х)?\s*(?:клас[уаів]*\b|кл\.)", re.I)
LEVEL = re.compile(r"\b(?:студентів|вищих навчальних закладів|закладів вищої освіти)\b", re.I)
# A single bibliographic paragraph carries all five required fields, with
# punctuation delimiting each verbatim span. Never infer missing fields.
IMPRINT = re.compile(
    r"(?P<title>[^\n/:]{3,180}?)\s*:\s*"
    r"(?P<level>(?:підручник|підручн?\.|навчальний посібник|навч\.\s*посіб)[^/]{0,350})/\s*"
    r"(?P<authors>[^—–]{1,300}?)\s*(?:[—–]|[ \t]+-[ \t]+)\s*[^:\n]{1,80}:\s*"
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
            {
                line
                for line in (lines[0], lines[-1])
                if len(line) <= 180 and not re.fullmatch(PAGE_PATTERN, line) and not HEADING.fullmatch(line)
            }
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


def value(row: Mapping, slot: str, span: tuple[int, int], name="verbatim", reader=None) -> Value:
    text = transform(
        name, row["full_text"], LINE_POLICY if name == "line_excision@1" else None, reader, citation(row)
    ).text
    return Value(slot, text[slice(*span)], (citation(row),), span, name)


def unit_id(heading: Heading) -> str:
    return canonical(
        [["sources.db", "textbook_sections", f"section_id={heading.row['section_id']}", list(heading.span)]]
    ).decode("utf-8")


class TextbookAttribution:
    """Only maps an explicit bibliographic template; instruction prose refuses."""

    FORMS: ClassVar[dict[str, str]] = {
        SOURCE_SCHOOL: "<author(s)>. <title>. <grade>. <publisher>, <year>. С. <page>.",
        SOURCE_UNIVERSITY: "<author(s)>. <title>. <level>. <publisher>, <year>. С. <page>.",
    }

    def __init__(self):
        self._cache = WeakKeyDictionary()

    def resolve(self, form, source, row, reader):
        cache = self._cache.setdefault(reader, {})
        book = row["source_file"]
        require(bool(ALLOWED.fullmatch(book)), "attribution_unresolved")
        expected_source = SOURCE_UNIVERSITY if book.startswith("uni-") else SOURCE_SCHOOL
        require(source.source_id == expected_source, "attribution_unresolved")
        require(form == self.FORMS[expected_source], "attribution_unresolved")
        require(type(row["page_start"]) is int and row["page_start"] >= 0, "attribution_unresolved")
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
        replacements = {
            "author(s)": item.text("authors"),
            "title": item.text("title"),
            "grade" if expected_source == SOURCE_SCHOOL else "level": item.text("grade"),
            "publisher": item.text("publisher"),
            "year": item.text("year"),
            "page": str(row["page_start"]),
        }
        bibliography = re.sub(r"<([^>]+)>", lambda match: replacements[match.group(1)], form)
        return Attribution(bibliography, form)


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


# Frozen filename-only admission inventory, measured with the independent census.
# These source identifiers are metadata; no textbook page text is embedded.
ALLOWLISTED_FILES = (
    "1-klas-angliiska-mova-pukhta-2024",
    "1-klas-bukvar-zaharijchuk-2025-1",
    "1-klas-bukvar-zaharijchuk-2025-2",
    "1-klas-matematyka-lystopad-2025",
    "1-klas-mystetstvo-rublia-2024",
    "1-klas-ya-doslidzhuiu-svit-zharkova-2024-1",
    "1-klas-ya-doslidzhuiu-svit-zharkova-2024-2",
    "10-11-klas-mystectvo-nazarenko-2018",
    "10-11-klas-tekhnolohiyi-khodzycka-2019",
    "10-klas-algebra-ister-2018",
    "10-klas-angliiska-mova-burenko-2018",
    "10-klas-biologija-i-ekologija-zadorozhnij-2018-stand",
    "10-klas-ekonomika-krupska-2018",
    "10-klas-fizyka-barjakhtar-2018",
    "10-klas-geografija-bojko-2018",
    "10-klas-geometrija-ister-2018",
    "10-klas-himija-grygorovych-2018",
    "10-klas-hromadianska-gisem-2018",
    "10-klas-informatika-rudenko-2018-stand",
    "10-klas-istorija-ukrajiny-gisem-2018",
    "10-klas-matematika-merzljak-2018",
    "10-klas-ukrajinska-literatura-avramenko-2018",
    "10-klas-ukrajinska-mova-avramenko-2018",
    "10-klas-ukrmova-glazova-2018",
    "10-klas-ukrmova-karaman-2018",
    "10-klas-vsesvitnia-istoriia-gisem-2018-stand",
    "10-klas-zakhyst-fuka-2023",
    "10-klas-zarubizhna-literatura-voloshhuk-2018",
    "11-klas-algebra-ister-2019-prof",
    "11-klas-angliiska-mova-kuchma-2019",
    "11-klas-astronomiya-pryshliak-2019",
    "11-klas-biologiia-i-ekologia-shalamov-2019",
    "11-klas-ekonomika-homiak-2019",
    "11-klas-fizika-astronomiia-zasekina-2019-standart",
    "11-klas-himia-grygorovych-2019",
    "11-klas-informatyka-rudenko-2019",
    "11-klas-istoriya-ukr-gisem-2024",
    "11-klas-istoriya-ukr-hlibovska-2024",
    "11-klas-istoriya-vsesvit-schupak-2024",
    "11-klas-matematyka-nelin-2019",
    "11-klas-pravoznavstvo-narovlianskyi-2019",
    "11-klas-ukrajinska-literatura-avramenko-2019",
    "11-klas-ukrajinska-mova-avramenko-2019",
    "11-klas-ukrajinska-mova-glazova-2019",
    "11-klas-zakhist-vitchizni-gudima-2019-med",
    "11-klas-zarubizhna-literatura-voloshhuk-2019",
    "2-klas-angliiska-mova-hubarieva-2024",
    "2-klas-matematyka-ister-2025",
    "2-klas-mystetstvo-rublia-2024",
    "2-klas-ukrmova-bolshakova-2019-1",
    "2-klas-ukrmova-bolshakova-2019-2",
    "2-klas-ukrmova-vashulenko-2019-1",
    "2-klas-ukrmova-vashulenko-2019-2",
    "2-klas-ya-doslidzhuiu-svit-hrushchynska-2019",
    "2-klas-ya-doslidzhuiu-svit-morze-2019",
    "3-klas-angliiska-mova-karpiuk-2020",
    "3-klas-informatyka-morze-2025",
    "3-klas-matematyka-lystopad-2020-1",
    "3-klas-matematyka-lystopad-2020-2",
    "3-klas-mystetstvo-arystova-2025",
    "3-klas-ukrainska-mova-savchenko-2020-2",
    "3-klas-ya-doslidzhuiu-svit-zharkova-2020-1",
    "3-klas-ya-doslidzhuiu-svit-zharkova-2020-2",
    "4-klas-angliiska-mova-hubarieva-2021",
    "4-klas-informatyka-vorontsova-2021",
    "4-klas-matematyka-ister-2021-1",
    "4-klas-matematyka-ister-2021-2",
    "4-klas-mystetstvo-rublia-2021",
    "4-klas-ukrayinska-mova-kravtsova-2021-1",
    "4-klas-ukrayinska-mova-ponomarova-2021-1",
    "4-klas-ukrayinska-mova-savchenko-2021-2",
    "4-klas-ukrayinska-mova-zaharijchuk-2021-1",
    "4-klas-ya-doslidzhuiu-svit-zharkova-2021-1",
    "4-klas-ya-doslidzhuiu-svit-zharkova-2021-2",
    "5-klas-angliiska-mova-pakhomova-2022",
    "5-klas-etyka-meleshchenko-2022",
    "5-klas-informatyka-morze-2022",
    "5-klas-istoriya-schupak-2022",
    "5-klas-matematyka-ister-2022",
    "5-klas-mystetstvo-rublia-2022",
    "5-klas-piznaiemo-pryrodu-korshevniuk-2022",
    "5-klas-tekhnolohiyi-bilenko-2023",
    "5-klas-ukrlit-avramenko-2022",
    "5-klas-ukrmova-avramenko-2022",
    "5-klas-ukrmova-golub-2022",
    "5-klas-ukrmova-zabolotnyi-2023",
    "5-klas-zarubizhna-literatura-voloshchuk-2022",
    "5-klas-zdorovia-vorontsova-2022",
    "6-klas-angliiska-mova-pakhomova-2023",
    "6-klas-etyka-martyniuk-2023",
    "6-klas-heohrafiya-zapotockyi-2023",
    "6-klas-informatyka-bondarenko-2023",
    "6-klas-istoriia-shchupak-2023",
    "6-klas-istoriya-gisem-2023",
    "6-klas-matematyka-tarasenkova-2023-1",
    "6-klas-matematyka-tarasenkova-2023-2",
    "6-klas-mystetstvo-rublia-2023",
    "6-klas-piznaemo-pryrodu-korshevniuk-2023",
    "6-klas-tekhnolohiyi-bilenko-2023",
    "6-klas-ukrlit-avramenko-2023",
    "6-klas-ukrmova-avramenko-2023",
    "6-klas-ukrmova-golub-2023",
    "6-klas-ukrmova-litvinova-2023",
    "6-klas-zdorovia-vorontsova-2023",
    "7-klas-algebra-merzliak-2024",
    "7-klas-angliiska-mova-kosta-2024",
    "7-klas-biolohiya-sobol-2024",
    "7-klas-fizyka-bariakhtar-2024",
    "7-klas-heometriya-merzliak-2024",
    "7-klas-informatyka-bondarenko-2024",
    "7-klas-istoria-ukr-hlibovska-2024",
    "7-klas-istoriya-shchupak-2024-full",
    "7-klas-khimiya-hryhorovych-2024",
    "7-klas-mystetstvo-masol-2024",
    "7-klas-tekhnolohiyi-bilenko-2024",
    "7-klas-ukrlit-avramenko-2024",
    "7-klas-ukrlit-zabolotnyi-2024",
    "7-klas-ukrmova-avramenko-2024",
    "7-klas-zdorovia-guschyna-2024",
    "8-klas-algebra-tarasenkova-2025",
    "8-klas-biolohiya-anderson-2025",
    "8-klas-finans-plastun-2025",
    "8-klas-fizyka-bariakhtar-2025",
    "8-klas-heohrafiya-hilberh-2025",
    "8-klas-hromadianska-osvita-vasylkiv-2025",
    "8-klas-informatyka-ryvkind-2025",
    "8-klas-istoria-ukr-hlibovska-2025",
    "8-klas-istoria-ukr-schupak-2025",
    "8-klas-istoria-vsesvitnia-ladychenko-2025",
    "8-klas-khimiya-hryhorovych-2025",
    "8-klas-mystetstvo-komarovska-2025",
    "8-klas-pryrodnychi-nauky-mandrenko-2025",
    "8-klas-tekhnolohiyi-bilenko-2025",
    "8-klas-ukrlit-avramenko-2025",
    "8-klas-ukrlit-zabolotnyi-2025",
    "8-klas-ukrmova-avramenko-2025",
    "8-klas-ukrmova-zabolotnyi-2025",
    "8-klas-zarlit-voloschuk-2025",
    "8-klas-zdorovia-vasylenko-2025",
    "9-klas-algebra-merzliak-2017",
    "9-klas-algebra-tarasenkova-2026",
    "9-klas-biolohiya-zadorozhnyi-2026",
    "9-klas-finansova-rolik-2026",
    "9-klas-fizyka-bariakhtar-2022",
    "9-klas-fizyka-zasiekina-2026",
    "9-klas-geografiia-boiko-2026",
    "9-klas-heometriya-bevz-2026",
    "9-klas-heometriya-merzliak-2017",
    "9-klas-hromadianska-osvita-pometun-2026",
    "9-klas-informatyka-morze-2026",
    "9-klas-istorija-ukrajini-gisem-2017",
    "9-klas-khimiya-popel-2017",
    "9-klas-khimiya-yaroshenko-2026",
    "9-klas-mystetstvo-kondratova-2025",
    "9-klas-mystetstvo-masol-2017",
    "9-klas-pravoznavstvo-berendieiev-2026",
    "9-klas-tekhnolohiyi-bilenko-2026",
    "9-klas-ukrajinska-literatura-avramenko-2017",
    "9-klas-ukrajinska-mova-avramenko-2017",
    "9-klas-ukrlit-zabolotnyi-2026",
    "9-klas-vsesvitnia-istoriia-pometun-2026",
    "9-klas-zarubizhna-literatura-kovbasenko-2026",
    "9-klas-zdorovia-gushchyna-2026",
    "uni-istoriya-kalynichenko-olianych-2025",
    "uni-istoriya-levytska-2015",
    "uni-mystetstvo-levytska-2015",
    "uni-mystetstvo-petutina-2012",
    "uni-ukrlit-dvulychanska-2017",
    "uni-ukrlit-kalinichenko-2024",
    "uni-ukrmova-corpus-linguistics-khpi-2021-part-1",
    "uni-ukrmova-corpus-linguistics-khpi-2021-part-2",
    "uni-ukrmova-dialectology-torchynska-2017",
    "uni-ukrmova-historical-grammar-kupchynska-piletskyi-2024",
    "uni-ukrmova-lexicology-filon-khomik-2010",
    "uni-ukrmova-morphology-volkova-maslo-2012",
    "uni-ukrmova-orthography-strokal-2021",
    "uni-ukrmova-phonetics-komarova-2015",
    "uni-ukrmova-prof-haluzynska-2006",
    "uni-ukrmova-punctuation-marynenko-2021",
    "uni-ukrmova-sociolinguistics-masenko-2010",
    "uni-ukrmova-stylistics-sharapa-tytarenko-2025",
    "uni-ukrmova-sulm-attestation-vspu-2021",
    "uni-ukrmova-syntax-herman-2021",
    "uni-ukrmova-text-linguistics-shevel-bilyk-2024",
)


def compatibility(books):
    """Reviewed row-role partitions for the exact admitted textbook files."""
    return [
        {
            "store": "sources.db",
            "table": "textbook_sections",
            "source_id": source,
            "role": "textbook",
            "source_column": "source_file",
            "source_values": files,
            "allowlisted_files": files,
            "sensitive": None,
        }
        for source, files in (
            (SOURCE_SCHOOL, sorted(book for book in books if not book.startswith("uni-"))),
            (SOURCE_UNIVERSITY, sorted(book for book in books if book.startswith("uni-"))),
        )
        if files
    ]


class Textbooks:
    def __init__(self):
        self.files = {}
        adapter = TextbookAttribution()
        self.adapters = {SOURCE_SCHOOL: adapter, SOURCE_UNIVERSITY: adapter}
        self.spec = {
            "compatibility": compatibility(ALLOWLISTED_FILES),
            "operations": ["verbatim_section"],
            "unit_grain": "printed_section_first_occurrence_v2",
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
                    "reasoning_marker_in_source",
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
        # Only filenames (never text) are read to authenticate the component's
        # frozen allowlist. The independent query's domain must equal that allowlist.
        eligible = {
            r[0] for r in connection.execute(f"SELECT DISTINCT source_file FROM textbook_sections WHERE {ELIGIBLE_SQL}")
        }
        supplied = set()
        for entry in self.spec["compatibility"]:
            if entry["source_id"] in self.adapters and entry["table"] == "textbook_sections":
                supplied.update(entry.get("allowlisted_files", ()))
        require(supplied == eligible, "textbook_allowlist")
        pages_by_book = {}
        for row in connection.execute(
            f"SELECT * FROM textbook_sections WHERE {ELIGIBLE_SQL} ORDER BY source_file,page_start,section_id"
        ):
            pages_by_book.setdefault(row["source_file"], []).append(dict(row))
        for pages in pages_by_book.values():
            yield from self._book(pages, ctx.reader)

    def _book(self, pages, reader):
        printed, seen, section_openings = [], set(), set()
        for row in pages:
            contents = bool(CONTENTS.search(row["full_text"]))
            edge_offsets, offset = [], 0
            for found in re.finditer(r"[^\n]+\n?|\n", row["full_text"]):
                line = found.group()
                if line.strip(" \t\r\n") and not re.fullmatch(PAGE_PATTERN, line.strip(" \t\r\n")):
                    edge_offsets.append(offset + len(line) - len(line.lstrip(" \t\r\n")))
                offset += len(line)
            previous = seen.copy()
            for heading in headings(row):
                if (
                    not contents
                    and heading.text in previous
                    and edge_offsets
                    and heading.span[0] in (edge_offsets[0], edge_offsets[-1])
                ):
                    continue
                printed.append(heading)
                if not contents:
                    section_openings.add(unit_id(heading))
                if not contents:
                    seen.add(heading.text)
        imprint = identity(pages)
        candidates = []
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
                cleaned = transform("line_excision@1", page["full_text"], LINE_POLICY, reader, citation(page)).text
                start = 0
                if page["section_id"] == heading.row["section_id"]:
                    start = len(
                        transform(
                            "line_excision@1", page["full_text"][: heading.span[1]], LINE_POLICY, reader, citation(page)
                        ).text
                    )
                end = len(cleaned)
                if next_heading and page["section_id"] == next_heading.row["section_id"]:
                    end = len(
                        transform(
                            "line_excision@1",
                            page["full_text"][: next_heading.span[0]],
                            LINE_POLICY,
                            reader,
                            citation(page),
                        ).text
                    )
                if start < end:
                    response.append(value(page, "body", (start, end), "line_excision@1", reader))
                elif not cleaned:
                    # A page containing only excised running heads/numbers is
                    # still a contiguous source page, not an empty section.
                    response.append(Value("body", "", (citation(page),), None, "line_excision@1"))
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
            candidates.append(
                Candidate(
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
            )
        groups = {}
        for candidate in candidates:
            if candidate.unit_id in section_openings:
                title = next(v.text for v in candidate.slots if v.slot == "section_title")
                groups.setdefault(title, []).append(candidate)
        ambiguous = {
            c.unit_id
            for group in groups.values()
            if len({"".join(v.text for v in c.response) for c in group}) > 1
            for c in group
        }
        for candidate in candidates:
            if candidate.unit_id in ambiguous and candidate.reason not in {
                "book_identity_unresolved",
                "book_ocr_damage",
                "ocr_damage",
                "table_of_contents",
            }:
                anchor = next(v for v in candidate.slots if v.slot == "section_title")
                candidate = replace(
                    candidate,
                    outcome="withheld",
                    reason="repeated_heading",
                    evidence=(evidence_id(anchor.citations[0]),),
                )
            if candidate.outcome == "accepted" and any(REASONING.search(v.text) for v in values(candidate)):
                anchor = next(v for v in candidate.slots if v.slot == "section_title")
                candidate = replace(
                    candidate,
                    outcome="withheld",
                    reason="reasoning_marker_in_source",
                    evidence=(evidence_id(anchor.citations[0]),),
                )
            yield candidate


COMPONENT = Textbooks()
