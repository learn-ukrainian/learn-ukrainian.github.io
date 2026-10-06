"""C3 ULIF section census; only source-readable groups become records."""

import json
from collections import Counter

from ..contract import Candidate
from .wp3_sources import (
    ENTRY,
    SECTION,
    STORE,
    Markup,
    anchor,
    fetch,
    identity,
    query,
    ref,
    section_value,
    unaccent,
    value,
)

COUNTS = {"synonyms": 75955, "antonyms": 2103}


def operation_spec(operation):
    head = ref("slots", "headword")
    sense = ref("slots", "sense")
    members = ref("response", "members")
    return {
        "unit_query": query("SELECT id FROM ulif_dictua_sections WHERE kind=?", [operation]),
        "frozen_count": COUNTS[operation],
        "unit_id": identity(SECTION, "response", "members"),
        "binding": {
            "schema": "binding-spec.v1",
            "rules": [
                {
                    "op": "one_group",
                    "values": [
                        {**head, "field": "id"},
                        {**members, "field": "entry_id"},
                        {**sense, "field": "entry_id"},
                    ],
                },
                {"op": "same_row", "values": [sense, members]},
                {
                    "op": "one_group",
                    "values": [{**sense, "field": "sense_or_group_id"}, {**members, "field": "sense_or_group_id"}],
                },
                {"op": "literal", "values": [{**members, "field": "kind"}], "expected": operation},
                {"op": "literal", "values": [{**head, "field": "homonym_checked"}], "expected": 1},
                {"op": "literal", "values": [{**head, "field": "status"}], "expected": "ok"},
            ],
        },
        "unit_grain": "ULIF relation section",
    }


def relation_span(markup, entry, operation):
    headword = unaccent(entry["canonical_headword"])
    bolds = [
        n
        for n in markup.tagged("b", outside=("i", "b"))
        if any(c.isalpha() for c in markup.text[slice(*markup.span(n))])
    ]
    if not any(unaccent(markup.text[slice(*markup.span(n))]).strip(" ,;.") == headword for n in bolds):
        return None, "headword_unresolved"
    if operation == "synonyms":
        if len(bolds) < 2:
            return None, "sense_not_visible"
        start = markup.span(bolds[0])[0]
        end = markup.span(bolds[1])[0]
        while end > start and markup.text[end - 1] in " ,;":
            end -= 1
        # A bare repetition of the headword cannot disambiguate several groups.
        if unaccent(markup.text[start:end]) == headword:
            return None, "sense_not_visible"
        return (start, end), None
    rows = markup.tagged("tr")
    cells = markup.tagged("td")
    if len(rows) < 2:
        return None, "sense_not_visible"
    header = [n for n in cells if rows[0].start <= n.start and n.end <= rows[0].end]
    definitions = [n for n in cells if rows[1].start <= n.start and n.end <= rows[1].end]
    if len(header) != 2 or len(definitions) != 2:
        return None, "sense_not_visible"
    matches = [
        i for i, n in enumerate(header) if unaccent(markup.text[slice(*markup.span(n))]).strip(" ,;.") == headword
    ]
    if len(matches) != 1:
        return None, "headword_unresolved"
    span = markup.span(definitions[matches[0]])
    return (span, None) if span[0] < span[1] else (None, "sense_not_visible")


def iter_candidates(ctx):
    reader = ctx.reader
    rows = (
        reader.connections[STORE]
        .execute("SELECT * FROM ulif_dictua_sections WHERE kind IN ('synonyms','antonyms') ORDER BY kind,id")
        .fetchall()
    )
    groups = Counter((row["entry_id"], row["kind"]) for row in rows)
    for item in rows:
        row = dict(item)
        entry = fetch(reader, ENTRY, row["entry_id"])
        operation = row["kind"]
        reason, slots, response = None, (), (anchor(row, "members"),)
        if not entry["homonym_checked"]:
            reason = "homonym_unchecked"
        elif entry["status"] != "ok":
            reason = "parse_error"
        elif not entry["canonical_headword"]:
            reason = "headword_unresolved"
        else:
            try:
                payload = json.loads(row["payload_json"])
                markup = Markup(payload["raw_html"])
                if not markup.text:
                    reason = "empty_source"
                else:
                    span, reason = relation_span(markup, entry, operation)
                    if reason is None:
                        sense = section_value(row, "sense", span)
                        # Printed lead/gloss is required even for a single group,
                        # since every current relation template displays a sense.
                        if groups[row["entry_id"], operation] > 1 and not sense.text.strip():
                            reason = "sense_not_visible"
                        else:
                            slots = (value(ENTRY, entry, "canonical_headword", "ulif", "headword"), sense)
                            response = (section_value(row, "members"),)
            except (KeyError, TypeError, ValueError):
                reason = "parse_error"
        yield Candidate(
            "C3",
            str(row["id"]),
            "withheld" if reason else "accepted",
            reason or "ok",
            (reason,) if reason else (),
            operation,
            slots,
            (),
            response,
            (),
        )
