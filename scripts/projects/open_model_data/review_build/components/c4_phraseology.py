"""C4 ULIF phraseology: printed idiom, definition and author-labelled quotes."""

import json
import re

from ..bindings import check
from ..contract import Candidate
from ..errors import require
from .wp3_sources import (
    ENTRY,
    SECTION,
    STORE,
    Markup,
    anchor,
    authenticate,
    card_unit,
    fetch,
    identity,
    query,
    ref,
    section_value,
)


def operation_spec():
    idiom = ref("slots", "idiom")
    definition = ref("response", "definition")
    citations = ref("response", "citation", match="all")
    return {
        "unit_query": query("SELECT id FROM ulif_dictua_sections WHERE kind='phraseology'"),
        "frozen_count": 8133,
        "unit_id": identity(SECTION, "response", "definition"),
        "unit_grain": "ULIF phraseology section",
        "binding": {
            "schema": "binding-spec.v1",
            "rules": [
                {"op": "same_row", "values": [idiom, definition, citations]},
                {
                    "op": "one_group",
                    "values": [{**s, "field": "sense_or_group_id"} for s in (idiom, definition, citations)],
                },
                {"op": "literal", "values": [{**definition, "field": "kind"}], "expected": "phraseology"},
            ],
        },
        "response_serializer": "json_array",
    }


def phrase_spans(markup):
    bolds = [
        n
        for n in markup.tagged("b", outside=("i", "b"))
        if any(c.isalpha() for c in markup.text[slice(*markup.span(n))])
    ]
    if not bolds:
        return None, "headword_unresolved"
    lead = markup.span(bolds[0])
    # More than one top-level printed heading would require a different grain.
    if len(bolds) != 1:
        return None, "sense_not_visible"
    quote_spans = []
    for italic in markup.tagged("i", outside=("i",)):
        start, end = markup.span(italic)
        if start < lead[1]:
            continue
        author = re.match(r"\s*\([^()]+\)", markup.text[end:])
        if not author or not any(c.isalpha() for c in author.group()) or start == end:
            return None, "citation_unresolved"
        quote_spans.append((start, end + author.end()))
    if not quote_spans:
        return None, "citation_unresolved"
    start, end = lead[1], quote_spans[0][0]
    while start < end and markup.text[start] in " ,;:—–-":
        start += 1
    while end > start and markup.text[end - 1] in " ,;:—–-":
        end -= 1
    if start == end or not any(c.isalpha() for c in markup.text[start:end]):
        return None, "definition_unresolved"
    lead_end = lead[1]
    while lead_end > lead[0] and markup.text[lead_end - 1] in " ,;":
        lead_end -= 1
    return ((lead[0], lead_end), (start, end), quote_spans), None


def iter_candidates(ctx):
    reader = ctx.reader
    for item in reader.connections[STORE].execute(
        "SELECT * FROM ulif_dictua_sections WHERE kind='phraseology' ORDER BY id"
    ):
        row = dict(item)
        entry = fetch(reader, ENTRY, row["entry_id"])
        reason, slots, response = None, (), (anchor(row, "definition"),)
        if not entry["homonym_checked"]:
            reason = "homonym_unchecked"
        elif entry["status"] != "ok":
            reason = "parse_error"
        elif not entry["canonical_headword"]:
            reason = "headword_unresolved"
        else:
            try:
                markup = Markup(json.loads(row["payload_json"])["raw_html"])
                spans, reason = phrase_spans(markup)
                if reason is None:
                    idiom, definition, citations = spans
                    slots = (section_value(row, "idiom", idiom),)
                    response = (
                        section_value(row, "definition", definition),
                        *(section_value(row, "citation", span) for span in citations),
                    )
            except (KeyError, TypeError, ValueError):
                reason = "parse_error"
        yield Candidate(
            "C4",
            str(row["id"]),
            "withheld" if reason else "accepted",
            reason or "ok",
            (reason,) if reason else (),
            "idiom_definition",
            slots,
            (),
            response,
            (),
        )


def validate(ctx, unit):
    c = unit.candidate
    require(c.component == "C4" and c.operation == "idiom_definition", "operation")
    authenticate(ctx, c, {SECTION}, "ulif")
    require(unit == card_unit(ctx, c, SECTION), "binding_group")
    row = fetch(ctx.reader, SECTION, c.unit_id)
    require(row["kind"] == "phraseology", "binding_group")
    if c.outcome != "accepted":
        require(
            c.outcome == "withheld"
            and c.reason
            in {
                "homonym_unchecked",
                "parse_error",
                "headword_unresolved",
                "sense_not_visible",
                "definition_unresolved",
                "citation_unresolved",
            }
            and c.response == (anchor(row, "definition"),),
            "ingestion_outcome",
        )
        return
    require(c.reason == "ok" and not c.evidence and not c.flags and not c.context, "ingestion_outcome")
    check(c, operation_spec()["binding"], ctx.reader, {})
    entry = fetch(ctx.reader, ENTRY, row["entry_id"])
    require(entry["homonym_checked"] == 1 and entry["status"] == "ok", "homonym_unchecked")
    require(bool(entry["canonical_headword"]), "headword_unresolved")
    markup = Markup(json.loads(row["payload_json"])["raw_html"])
    spans, reason = phrase_spans(markup)
    require(reason is None, reason or "definition_unresolved")
    idiom, definition, citations = spans
    require(
        c.slots == (section_value(row, "idiom", idiom),)
        and c.response
        == (
            section_value(row, "definition", definition),
            *(section_value(row, "citation", span) for span in citations),
        ),
        "binding_group",
    )


def iter_card_units(ctx):
    for candidate in iter_candidates(ctx):
        unit = card_unit(ctx, candidate, SECTION)
        validate(ctx, unit)
        yield unit
