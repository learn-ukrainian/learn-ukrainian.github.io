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
)

WITHHELD = {
    "homonym_unchecked",
    "homonym_mismatch",
    "parse_error",
    "headword_unresolved",
    "sense_not_visible",
    "definition_unresolved",
    "citation_unresolved",
}
SENSE_NUMBER = re.compile(r"\s(\d+)\.$")
AUTHOR = re.compile(r"\s*\([^()]+\)")
# A drama quotation opens with its speaker: `[Надія:]`, `[Фортунат (пошепки):]`.
SPEAKER = re.compile(r"\[[^\[\]]*:\]")
SPEAKER_BEFORE = re.compile(r"\[[^\[\]]*:\]\s*$")
SEPARATORS = re.compile(r"[\s;.,—–-]*")


def author_label(text):
    """A parenthetical opening with a capital letter: a source label, as in `(Ю. Смолич)`."""
    for match in re.finditer(r"\(([^()]*)\)", text):
        letter = next((c for c in match.group(1) if c.isalpha()), "")
        if letter.isupper():
            return True
    return False


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
    """Segment one printed phraseology paragraph.

    The heading is the paragraph's leading top-level bold: the idiom, then an
    optional printed sense number. The definition runs from the heading to the
    first quotation. A quotation is italic, may open with a speaker tag and
    closes with its parenthesized author label; only separators lie between
    and after quotations. Returns `(idiom, sense or None, definition, quotes)`
    spans. Anything else is withheld: a continuation sense whose idiom is
    printed in an earlier section, a second heading, a // shade, or quotation
    text outside italics.
    """
    text = markup.text
    heads = [n for n in markup.tagged("b", outside=("i", "b")) if markup.span(n)[0] < markup.span(n)[1]]
    if not heads or markup.span(heads[0])[0] != 0:
        return None, "headword_unresolved"
    lead = markup.span(heads[0])
    if not any(c.isalpha() for c in text[slice(*lead)]):
        return None, "headword_unresolved"
    if sum(any(c.isalpha() for c in text[slice(*markup.span(n))]) for n in heads) != 1:
        return None, "sense_not_visible"
    idiom_end, sense = lead[1], None
    while idiom_end > lead[0] and text[idiom_end - 1] in " ,;":
        idiom_end -= 1
    number = SENSE_NUMBER.search(text, lead[0], idiom_end)
    if number:
        sense, idiom_end = number.span(1), number.start()
        while idiom_end > lead[0] and text[idiom_end - 1] in " ,;":
            idiom_end -= 1
    quotes = []
    for italic in markup.tagged("i", outside=("i",)):
        start, end = markup.span(italic)
        if start < lead[1]:
            continue
        author = AUTHOR.match(text, end)
        if start == end or not author or not any(c.isalpha() for c in author.group()):
            return None, "citation_unresolved"
        if quotes and start < quotes[-1][1]:
            return None, "citation_unresolved"
        speaker = SPEAKER_BEFORE.search(text, quotes[-1][1] if quotes else lead[1], start)
        quotes.append((speaker.start() if speaker else start, author.end()))
    if not quotes:
        return None, "citation_unresolved"
    start, end = lead[1], quotes[0][0]
    while start < end and text[start] in " ,;:—–-":
        start += 1
    while end > start and text[end - 1] in " ,;:—–-":
        end -= 1
    definition = text[start:end]
    if not any(c.isalpha() for c in definition):
        return None, "definition_unresolved"
    gaps = [text[a:b] for a, b in zip((q[1] for q in quotes), (*(q[0] for q in quotes[1:]), len(text)), strict=True)]
    if any("//" in part for part in (definition, *gaps)):
        return None, "sense_not_visible"
    if SPEAKER.search(definition) or author_label(definition) or not all(map(SEPARATORS.fullmatch, gaps)):
        return None, "citation_unresolved"
    return ((lead[0], idiom_end), sense, (start, end), quotes), None


def phrase_values(row, spans):
    idiom, sense, definition, quotes = spans
    slots = (section_value(row, "idiom", idiom),)
    if sense:
        slots = (*slots, section_value(row, "sense", sense))
    response = (
        section_value(row, "definition", definition),
        *(section_value(row, "citation", span) for span in quotes),
    )
    return slots, response


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
        elif entry["grammatical_label"] == SURNAME_LABEL:
            reason = "homonym_mismatch"
        else:
            try:
                markup = Markup(json.loads(row["payload_json"])["raw_html"])
                spans, reason = phrase_spans(markup)
                if reason is None:
                    slots, response = phrase_values(row, spans)
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
            c.outcome == "withheld" and c.reason in WITHHELD and c.response == (anchor(row, "definition"),),
            "ingestion_outcome",
        )
        return
    require(c.reason == "ok" and not c.evidence and not c.flags and not c.context, "ingestion_outcome")
    check(c, operation_spec()["binding"], ctx.reader, {})
    entry = fetch(ctx.reader, ENTRY, row["entry_id"])
    require(entry["homonym_checked"] == 1 and entry["status"] == "ok", "homonym_unchecked")
    require(bool(entry["canonical_headword"]), "headword_unresolved")
    require(entry["grammatical_label"] != SURNAME_LABEL, "homonym_mismatch")
    markup = Markup(json.loads(row["payload_json"])["raw_html"])
    spans, reason = phrase_spans(markup)
    require(reason is None, reason or "definition_unresolved")
    require((c.slots, c.response) == phrase_values(row, spans), "binding_group")


def iter_card_units(ctx):
    for candidate in iter_candidates(ctx):
        unit = card_unit(ctx, candidate, SECTION)
        validate(ctx, unit)
        yield unit
