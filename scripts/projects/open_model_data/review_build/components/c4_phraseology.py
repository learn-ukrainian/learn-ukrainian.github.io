"""C4 ULIF phraseology: printed idiom, definition and author-labelled quotes."""

import json
import re

from ..contract import Candidate
from .wp3_sources import ENTRY, SECTION, STORE, Markup, anchor, fetch, identity, query, ref, section_value


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
        if author and any(c.isalpha() for c in author.group()):
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
