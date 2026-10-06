"""C5: printed colon-list examples bound to complete Правопис paragraphs.

Raw spans define the frozen units. Only the reviewed dehyphenation transform
can change paragraph bytes; unresolved readings withhold the whole paragraph.
Examples needing a changed reading are withheld, retaining their raw identity.
"""

import json
import re
from collections.abc import Mapping
from typing import ClassVar

from ..attribution import Attribution
from ..bindings import example_items
from ..contract import Candidate, Citation, Value, canonical, digest
from ..errors import require
from ..gate import evidence_id
from ..transforms import transform
from . import ComponentContext

SOURCE = "pravopys_2019_official"
STORE = "sources.db"
TABLE = "pravopys_paragraphs"
OPERATION = "printed_spelling_rule"
FROZEN_COUNT = 11926
UNIT_QUERY = {
    "kind": "sql",
    "store": STORE,
    "sql": """SELECT json_array(json_array('sources.db','pravopys_paragraphs',
        'source_id=' || p.source_id || ';number=' || p.number,json(s.value)))
        FROM pravopys_paragraphs AS p,json_each(omd_example_spans(p.text)) AS s
        WHERE p.source_id=?""",
    "parameters": [SOURCE],
}
EXAMPLE = {"area": "slots", "slot": "example"}
PARAGRAPH = {"area": "response", "slot": "paragraph"}
LOCATOR = {"area": "response", "slot": "paragraph_locator"}
DEHYPHENATION = {"store": "vesum.db", "table": "forms_all", "field": "word_form"}
# Even forms with stress marks, apostrophes, or spaces at the printed line end
# must not silently retain a broken reading. Legitimate unresolved hyphens are
# conservatively withheld too; the stored alternatives are not an adjudication.
LINE_HYPHEN = re.compile(r"[^\W\d_][\w\u0300-\u036f'’ʼ]*-[ \t]*\r?\n[ \t]*[^\W\d_]")


def primary_citation(row: Mapping, field: str = "text") -> Citation:
    """Authenticate the actual composite primary key and whole-column bytes."""
    return Citation(
        SOURCE,
        STORE,
        TABLE,
        f"source_id={row['source_id']};number={row['number']}",
        field,
        row["locator"],
        digest(row[field].encode("utf-8")),
    )


def example_unit(citation: Citation, span: tuple[int, int]) -> str:
    """Use exactly the primary citation identity independently queried by SQL."""
    return canonical([[citation.store, citation.table, citation.row_key, list(span)]]).decode("utf-8")


class PravopysAttribution:
    """Accept only a complete register form authenticated by held bibliography."""

    def resolve(self, form, citation, row, reader) -> Attribution:
        require(row["source_id"] == SOURCE and citation.source_id == SOURCE, "attribution_unresolved")
        metadata = [r for r in reader.iter_rows(STORE, "pravopys_sources") if r["source_id"] == SOURCE]
        require(len(metadata) == 1, "attribution_unresolved")
        metadata = metadata[0]
        bibliography = metadata.get("citation")
        require(isinstance(bibliography, str) and bool(bibliography.strip()), "attribution_unresolved")
        require(form == bibliography, "attribution_unresolved")
        # This additional read pins the complete bibliography in the snapshot.
        held = Citation(
            SOURCE,
            STORE,
            "pravopys_sources",
            f"source_id={SOURCE}",
            "citation",
            citation.locator,
            digest(bibliography.encode("utf-8")),
        )
        reader.field(held)
        return Attribution(bibliography, form)


class PravopysComponent:
    spec: ClassVar[dict] = {
        "operations": [OPERATION],
        "operation_specs": {
            OPERATION: {
                "unit_query": UNIT_QUERY,
                "frozen_count": FROZEN_COUNT,
                "unit_id": {
                    "format": "citation.v1",
                    "primary": [{"selector": EXAMPLE, "store": STORE, "table": TABLE, "span": True}],
                },
                "binding": {
                    "schema": "binding-spec.v1",
                    "rules": [
                        {"op": "same_row", "values": [EXAMPLE, PARAGRAPH, LOCATOR]},
                        {
                            "op": "example_list",
                            "values": [EXAMPLE],
                            "citation_field": "text",
                            "locator_field": "locator",
                        },
                        {
                            "op": "whole_field",
                            "values": [PARAGRAPH],
                            "citation_field": "text",
                            "locator_field": "locator",
                        },
                        {
                            "op": "whole_field",
                            "values": [LOCATOR],
                            "citation_field": "locator",
                            "locator_field": "locator",
                        },
                        {"op": "pattern_absent", "values": [EXAMPLE, PARAGRAPH], "pattern": LINE_HYPHEN.pattern},
                        {"op": "literal", "values": [{**PARAGRAPH, "field": "unresolved_hyphenations"}], "expected": 0},
                        {"op": "literal", "values": [{**PARAGRAPH, "field": "hyphen_alternatives"}], "expected": "[]"},
                    ],
                },
            },
        },
        "reasons": {
            "accepted": ["ok"],
            "rejected": [],
            "withheld": [
                "paragraph_hyphenation",
                "example_hyphenation",
                "hyphen_metadata_unavailable",
                "attribution_unresolved",
                "locator_unavailable",
                "catalog_inapplicable",
            ],
            "excluded": [],
        },
        "transforms": {"dehyphenate@1": DEHYPHENATION},
        "unit_grain": "Printed colon-list example span in its own paragraph; measured 11926 in 168 paragraphs.",
        "reference_multiplicity": "One complete source paragraph and its held locator per printed example span.",
    }
    adapters: ClassVar[dict] = {SOURCE: PravopysAttribution()}
    files: ClassVar[dict] = {}

    def iter_candidates(self, ctx: ComponentContext):
        for row in ctx.reader.iter_rows(STORE, TABLE):
            if row["source_id"] != SOURCE:
                continue
            citation = primary_citation(row)
            # Read through the pinned reader, rather than trust extractor text.
            _, raw = ctx.reader.field(citation)
            reason = "ok"
            try:
                alternatives = json.loads(row["hyphen_alternatives"])
                valid = (
                    isinstance(alternatives, list)
                    and all(isinstance(a, str) for a in alternatives)
                    and type(row["unresolved_hyphenations"]) is int
                    and row["unresolved_hyphenations"] == len(alternatives)
                )
            except (ValueError, TypeError):
                valid = False
            if not valid or (not alternatives and row["hyphen_alternatives"] != "[]"):
                reason = "hyphen_metadata_unavailable"
            elif alternatives:
                reason = "paragraph_hyphenation"
            normalized = raw
            if reason == "ok" and LINE_HYPHEN.search(raw):
                normalized = transform("dehyphenate@1", raw, DEHYPHENATION, ctx.reader).text
                if LINE_HYPHEN.search(normalized):
                    reason = "paragraph_hyphenation"
            for span in example_items(raw):
                example = raw[span[0] : span[1]]
                unit_reason = "example_hyphenation" if reason == "ok" and LINE_HYPHEN.search(example) else reason
                response_transform = "dehyphenate@1" if normalized != raw else "verbatim"
                yield Candidate(
                    "C5",
                    example_unit(citation, span),
                    "accepted" if unit_reason == "ok" else "withheld",
                    unit_reason,
                    () if unit_reason == "ok" else (evidence_id(citation),),
                    OPERATION,
                    (Value("example", example, (citation,), span, "verbatim"),),
                    (),
                    (
                        Value("paragraph", normalized, (citation,), None, response_transform),
                        Value(
                            "paragraph_locator", row["locator"], (primary_citation(row, "locator"),), None, "verbatim"
                        ),
                    ),
                    (),
                )


COMPONENT = PravopysComponent()
