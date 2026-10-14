"""C3 ULIF section census; only source-readable groups become records."""

import json
import re
import unicodedata
from collections import Counter

from ..bindings import check
from ..contract import Candidate
from ..errors import require
from .wp3_sources import (
    ENTRY,
    SECTION,
    STORE,
    SURNAME_LABEL,
    Markup,
    anchor,
    authenticate,
    card_unit,
    fetch,
    identity,
    query,
    ref,
    section_value,
    unaccent,
    value,
)

COUNTS = {"synonyms": 75955, "antonyms": 2103}
WITHHELD = {
    "homonym_unchecked",
    "homonym_mismatch",
    "parse_error",
    "headword_unresolved",
    "empty_source",
    "sense_not_visible",
}


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


def stressed(text):
    return re.sub("\u0301+", "\u0301", unicodedata.normalize("NFD", text)).casefold().strip(" ,;.")


def names_sibling(reader, markup, entry):
    """Whether the printed stressed headword names a sibling homonym but not this entry.

    Only a printed stress mark is evidence; unstressed printing cannot tell
    homonyms apart and leaves the reviewed headword check in force.
    """
    headword = unaccent(entry["canonical_headword"])
    printed = {
        stressed(markup.text[slice(*markup.span(n))])
        for n in markup.tagged("b", outside=("i", "b"))
        if unaccent(markup.text[slice(*markup.span(n))]).strip(" ,;.") == headword
    }
    printed = {form for form in printed if "\u0301" in form}
    if not printed or stressed(entry["canonical_headword"]) in printed:
        return False
    siblings = reader.connections[STORE].execute(
        "SELECT canonical_headword FROM ulif_dictua_entries WHERE normalized_query=? AND id!=?",
        (entry["normalized_query"], entry["id"]),
    )
    return any(stressed(row[0]) in printed for row in siblings)


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
        elif entry["grammatical_label"] == SURNAME_LABEL:
            reason = "homonym_mismatch"
        else:
            try:
                payload = json.loads(row["payload_json"])
                markup = Markup(payload["raw_html"])
                if not markup.text:
                    reason = "empty_source"
                else:
                    span, reason = relation_span(markup, entry, operation)
                    if reason is None and names_sibling(reader, markup, entry):
                        reason = "homonym_mismatch"
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


def validate(ctx, unit):
    c = unit.candidate
    require(c.component == "C3" and c.operation in COUNTS, "operation")
    authenticate(ctx, c, {ENTRY, SECTION}, "ulif")
    require(unit == card_unit(ctx, c, SECTION), "binding_group")
    row = fetch(ctx.reader, SECTION, c.unit_id)
    require(row["kind"] == c.operation, "binding_group")
    if c.outcome != "accepted":
        require(
            c.outcome == "withheld" and c.reason in WITHHELD and c.response == (anchor(row, "members"),),
            "ingestion_outcome",
        )
        return
    require(c.reason == "ok" and not c.evidence and not c.flags and not c.context, "ingestion_outcome")
    check(c, operation_spec(c.operation)["binding"], ctx.reader, {})
    entry = fetch(ctx.reader, ENTRY, row["entry_id"])
    require(entry["grammatical_label"] != SURNAME_LABEL, "homonym_mismatch")
    markup = Markup(json.loads(row["payload_json"])["raw_html"])
    span, reason = relation_span(markup, entry, c.operation)
    require(reason is None, reason or "sense_not_visible")
    require(not names_sibling(ctx.reader, markup, entry), "homonym_mismatch")
    require(
        c.slots == (value(ENTRY, entry, "canonical_headword", "ulif", "headword"), section_value(row, "sense", span))
        and c.response == (section_value(row, "members"),),
        "binding_group",
    )


def iter_card_units(ctx):
    for candidate in iter_candidates(ctx):
        unit = card_unit(ctx, candidate, SECTION)
        validate(ctx, unit)
        yield unit
