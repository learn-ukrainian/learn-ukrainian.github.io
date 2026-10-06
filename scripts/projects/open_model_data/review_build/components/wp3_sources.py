"""Source-only citation helpers and authenticated official bibliography adapters."""

import json
import re
from bisect import bisect_left
from dataclasses import dataclass
from html.parser import HTMLParser

from ..attribution import Attribution
from ..contract import Citation, Value, digest
from ..errors import require
from ..snapshot import identifier
from ..transforms import transform

STORE = "sources.db"
ENTRY = "ulif_dictua_entries"
SECTION = "ulif_dictua_sections"
ARTICLE = "sum20_articles"
SENSE = "sum20_senses"
CITATION = "sum20_citations"

# Reviewed WP3 source admission, formerly carried by the host request.
# Dictionaries have no row-level sensitivity concept or UA-GEC corpus policy.
ULIF_COMPATIBILITY = [
    {
        "store": STORE,
        "table": ENTRY,
        "source_id": "ulif",
        "role": "modern",
        "source_column": "status",
        "source_values": ["ok"],
        "sensitive": None,
    },
    {
        "store": STORE,
        "table": SECTION,
        "source_id": "ulif",
        "role": "modern",
        "source_column": "kind",
        "source_values": ["synonyms", "antonyms", "phraseology"],
        "sensitive": None,
    },
]
SUM20_COMPATIBILITY = [
    {
        "store": STORE,
        "table": ARTICLE,
        "source_id": "sum20",
        "role": "modern",
        "source_column": "quarantine_reason",
        "source_values": [""],
        "quarantine": "quarantine_reason",
        "sensitive": None,
    },
    *[
        {
            "store": STORE,
            "table": table,
            "source_id": "sum20",
            "role": "modern",
            "source_column": "article_id",
            "source_values": list(range(1, 90)),
            "sensitive": None,
        }
        for table in (SENSE, CITATION)
    ],
]


def query(sql, parameters=()):
    return {"kind": "sql", "store": STORE, "sql": sql, "parameters": list(parameters)}


def ref(area, slot, **extra):
    return {"area": area, "slot": slot, **extra}


def identity(table, area, slot):
    return {"primary": [{"selector": ref(area, slot), "store": STORE, "table": table, "key": "id"}], "separator": ";"}


def fetch(reader, table, key):
    rows = reader.connections[STORE].execute(f"SELECT * FROM {identifier(table)} WHERE id=?", (key,)).fetchall()
    require(len(rows) == 1, "row_unavailable")
    return dict(rows[0])


def cite(table, row, field, source):
    column = field.partition("#")[0]
    require(isinstance(row[column], str), "field_unavailable")
    locator = f"{source}: {table}, id={row['id']}"
    if "entry_id" in row:
        locator += f", entry={row['entry_id']}, group={row['sense_or_group_id']}"
    if "article_id" in row:
        locator += f", article={row['article_id']}, sense={row.get('sense_order', row.get('sense_ref'))}"
    return Citation(source, STORE, table, f"id={row['id']}", field, locator, digest(row[column].encode("utf-8")))


def value(table, row, field, source, slot, span=None, transformation="verbatim"):
    selected = row[field.partition("#")[0]]
    if "#" in field:
        selected = json.loads(selected)
        for part in field.partition("#")[2].split("/")[1:]:
            selected = selected[part]
    text = transform(transformation, selected).text
    if span is not None:
        text = text[span[0] : span[1]]
    return Value(slot, text, (cite(table, row, field, source),), span, transformation)


def section_value(row, slot, span=None):
    return value(SECTION, row, "payload_json#/raw_html", "ulif", slot, span, "ulif_html_text@1")


def anchor(row, slot):
    # Withheld accounting rows still authenticate the section's primary key,
    # even if the held payload is malformed or has no HTML field.
    return value(SECTION, row, "payload_json", "ulif", slot)


def unaccent(text):
    import unicodedata

    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).replace("\u0301", "")).casefold()


@dataclass(frozen=True)
class Node:
    tag: str
    start: int
    end: int
    parents: tuple[str, ...]
    attrs: dict


class Markup(HTMLParser):
    """Offsets in the framework's exact HTML transform, with structural tags.

    No text is inserted. Node ranges map the original text-node offsets through
    precisely the same whitespace collapse as ulif_html_text@1.
    """

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.length = 0
        self.stack = []
        self.nodes = []
        self.feed(html)
        self.close()
        self.raw_text = "".join(self.parts)
        positions, chars = [], []
        for match in re.finditer(r"\s+|\S", self.raw_text):
            positions.append(match.start())
            chars.append(" " if match.group().isspace() else match.group())
        if chars and chars[0] == " ":
            chars.pop(0)
            positions.pop(0)
        if chars and chars[-1] == " ":
            chars.pop()
            positions.pop()
        self.text = "".join(chars)
        self.positions = positions
        require(self.text == transform("ulif_html_text@1", html).text, "markup_transform")

    def handle_starttag(self, tag, attrs):
        if tag not in {"br", "hr", "img", "input", "meta", "link", "wbr"}:
            self.stack.append((tag, self.length, tuple(n[0] for n in self.stack), dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for name, start, parents, attrs in self.stack[i:]:
                    self.nodes.append(Node(name, start, self.length, parents, attrs))
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.parts.append(data)
        self.length += len(data)

    def span(self, node):
        start = bisect_left(self.positions, node.start)
        end = bisect_left(self.positions, node.end)
        while start < end and self.text[start].isspace():
            start += 1
        while end > start and self.text[end - 1].isspace():
            end -= 1
        return start, end

    def tagged(self, tag, outside=()):
        return sorted(
            (n for n in self.nodes if n.tag == tag and not set(outside) & set(n.parents)), key=lambda n: n.start
        )


class UlifAdapter:
    """Resolve the register's full form from its reviewed bibliography and entry."""

    FORM_SHA = "a441989b57304acf0e6d6df0acb8e5567b840204c13abe8d907c960c1ff1ec87"

    def resolve(self, form, citation, row, reader):
        require(digest(form.encode()) == self.FORM_SHA and citation.source_id == "ulif", "attribution_unresolved")
        require(citation.table in {ENTRY, SECTION}, "attribution_unresolved")
        entry = row if citation.table == ENTRY else fetch(reader, ENTRY, row["entry_id"])
        require(bool(entry.get("canonical_headword")) and bool(entry.get("retrieved_at")), "attribution_unresolved")
        for field in ("canonical_headword", "retrieved_at"):
            reader.row(cite(ENTRY, entry, field, "ulif"))
        suffix = " (entry reference and retrieval date per field)"
        require(form.endswith(suffix), "attribution_unresolved")
        bibliography = (
            form[: -len(suffix)]
            + f"; entry={entry['id']}; homonym={entry['homonym_index']}; retrieved={entry['retrieved_at']}"
        )
        return Attribution(bibliography, form)


class Sum20Adapter:
    FORM_SHA = "ad322587a6d22c6714e741f1c719b05a7170d7f5d06fdc2490c2a0f7bcf5151c"

    def resolve(self, form, citation, row, reader):
        require(digest(form.encode()) == self.FORM_SHA and citation.source_id == "sum20", "attribution_unresolved")
        require(citation.table in {ARTICLE, SENSE, CITATION}, "attribution_unresolved")
        article = row if citation.table == ARTICLE else fetch(reader, ARTICLE, row["article_id"])
        require(not article.get("quarantine_reason"), "attribution_unresolved")
        require(
            bool(article.get("fetched_at")) and str(article.get("official_url", "")).startswith("https://sum20ua.com/"),
            "attribution_unresolved",
        )
        for field in ("official_url", "fetched_at"):
            reader.row(cite(ARTICLE, article, field, "sum20"))
        suffix = " — official edition only, never a mirror (docs/best-practices/atlas-source-presentation.md)."
        require(form.endswith(suffix), "attribution_unresolved")
        return Attribution(
            form[: -len(suffix)] + f"; {article['official_url']}; retrieved={article['fetched_at']}", form
        )


ULIF_ADAPTER = UlifAdapter()
SUM20_ADAPTER = Sum20Adapter()
REASONS = {
    "accepted": ["ok"],
    "rejected": [],
    "withheld": [
        "attribution_unresolved",
        "locator_unavailable",
        "catalog_inapplicable",
        "parse_error",
        "empty_source",
        "sense_not_visible",
        "headword_unresolved",
        "homonym_unchecked",
        "definition_unresolved",
        "citation_unresolved",
        "context_not_discriminating",
    ],
    "excluded": [],
}
