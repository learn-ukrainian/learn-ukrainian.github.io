"""C5: printed colon-list examples bound to complete Правопис paragraphs.

Raw spans define the frozen units. Only the reviewed dehyphenation transform
can change paragraph bytes; unresolved readings withhold records carrying them.
Raw example quotes and spans retain their printed identity; targets resolve splits.
"""

from collections.abc import Mapping
from typing import ClassVar

from ..attribution import Attribution
from ..bindings import example_boundaries
from ..contract import Candidate, Citation, Value, canonical, digest
from ..errors import BuildError, require
from ..gate import evidence_id
from ..transforms import Result, source_text_defects, transform, unresolved_overlaps
from . import ComponentContext

SOURCE = "pravopys_2019_official"
REGISTER_ID = "pravopys_2019"
STORE = "sources.db"
TABLE = "pravopys_paragraphs"
OPERATION = "printed_spelling_rule"
FROZEN_COUNT = 6196
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
DEHYPHENATION = {
    "store": "vesum.db",
    "table": "forms_all",
    "field": "word_form",
    "lookup_field": "word_form_folded",
    "normalizer": "vesum_fold",
    "hyphen_metadata": {
        "store": STORE,
        "table": TABLE,
        "field": "text",
        "source_column": "source_id",
        "source_id": SOURCE,
        "alternatives_field": "hyphen_alternatives",
        "count_field": "unresolved_hyphenations",
    },
}


def primary_citation(row: Mapping, field: str = "text") -> Citation:
    """Authenticate the actual composite primary key and whole-column bytes."""
    return Citation(
        REGISTER_ID,
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
        require(row["source_id"] == SOURCE and citation.source_id == REGISTER_ID, "attribution_unresolved")
        metadata = [r for r in reader.iter_rows(STORE, "pravopys_sources") if r["source_id"] == SOURCE]
        require(len(metadata) == 1, "attribution_unresolved")
        metadata = metadata[0]
        bibliography = metadata.get("citation")
        require(isinstance(bibliography, str) and bool(bibliography.strip()), "attribution_unresolved")
        if form == bibliography:
            require(bibliography.startswith("SYNTHETIC "), "attribution_unresolved")
            rendered = bibliography
        else:
            # The register's edition statement and paragraph placeholder map to
            # the held official edition, not to a second database source id.
            suffix = " § <номер>."
            require(form.startswith(bibliography + ". ") and form.endswith(suffix), "attribution_unresolved")
            edition = form.removesuffix(suffix).rstrip(".")
            document = reader.read_repository_config("docs/sources/pravopys-2019-official-source.md").decode("utf-8")
            require(edition in " ".join(document.split()), "attribution_unresolved")
            file_sha256 = metadata.get("file_sha256")
            require(
                isinstance(file_sha256, str) and len(file_sha256) == 64 and file_sha256 in document,
                "attribution_unresolved",
            )
            number = row.get("number")
            require(type(number) is int and 1 <= number <= 168, "attribution_unresolved")
            rendered = form.replace("<номер>", str(number))
            reader.field(
                Citation(
                    REGISTER_ID,
                    STORE,
                    "pravopys_sources",
                    f"source_id={SOURCE}",
                    "file_sha256",
                    citation.locator,
                    digest(file_sha256.encode("utf-8")),
                )
            )
        # This additional read pins the complete bibliography in the snapshot.
        held = Citation(
            REGISTER_ID,
            STORE,
            "pravopys_sources",
            f"source_id={SOURCE}",
            "citation",
            citation.locator,
            digest(bibliography.encode("utf-8")),
        )
        reader.field(held)
        return Attribution(rendered, form)


class PravopysComponent:
    spec: ClassVar[dict] = {
        "compatibility": [
            {
                "store": STORE,
                "table": TABLE,
                "source_id": REGISTER_ID,
                "role": "modern",
                "source_column": "source_id",
                "source_values": [SOURCE],
            }
        ],
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
                        {"op": "transform_resolved", "values": [PARAGRAPH], "transform": "dehyphenate@2"},
                    ],
                },
            },
        },
        "reasons": {
            "accepted": ["ok"],
            "rejected": [],
            "withheld": [
                "paragraph_hyphenation_unresolved",
                "source_text_defect",
                "hyphen_metadata_unavailable",
                "attribution_unresolved",
                "locator_unavailable",
                "catalog_inapplicable",
                "example_boundary_ambiguous",
            ],
            "excluded": [],
        },
        "transforms": {"dehyphenate@2": DEHYPHENATION},
        "unit_grain": (
            "Printed colon-list example span, or one unresolved list group withheld for boundary ambiguity; "
            "measured 6196 in 168 paragraphs."
        ),
        "reference_multiplicity": "One complete source paragraph and its held locator per printed example span.",
    }
    adapters: ClassVar[dict] = {REGISTER_ID: PravopysAttribution()}
    files: ClassVar[dict] = {}

    def iter_candidates(self, ctx: ComponentContext):
        for row in ctx.reader.iter_rows(STORE, TABLE):
            if row["source_id"] != SOURCE:
                continue
            citation = primary_citation(row)
            # Read through the pinned reader, rather than trust extractor text.
            _, raw = ctx.reader.field(citation)
            reason = "ok"
            normalized = raw
            try:
                resolved = transform("dehyphenate@2", raw, DEHYPHENATION, ctx.reader)
                normalized = resolved.text
                if source_text_defects(normalized, DEHYPHENATION, ctx.reader, original=raw):
                    reason = "source_text_defect"
            except BuildError as exc:
                if exc.code != "hyphen_metadata_unavailable":
                    raise
                reason = exc.code
            for span, boundary_reason in example_boundaries(raw):
                example = raw[span[0] : span[1]]
                unit_reason = reason
                # Inspect what this unit actually carries. The catalog currently
                # requires the complete paragraph; therefore other examples in
                # that response are visible too. Raw example spans keep identity.
                if reason == "ok" and (
                    unresolved_overlaps(resolved, None)
                    or unresolved_overlaps(Result(raw, unresolved=resolved.unresolved), span)
                ):
                    unit_reason = "paragraph_hyphenation_unresolved"
                if unit_reason == "ok" and boundary_reason != "ok":
                    unit_reason = boundary_reason
                response_transform = "dehyphenate@2"
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
