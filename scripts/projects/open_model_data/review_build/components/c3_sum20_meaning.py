"""C3 card ingestion: SUM20 numbered senses and the // shades printed inside them.

Card sense evidence does not need a training-prompt discriminator. Each numbered
sense of an unquarantined article, and each of its // shades, is one unit with
its own definition, labels and ordered quotations, plus the article's printed
grammar line. The stored parse rows merge a shade's labels and quotations into
its numbered sense, so unit scope comes from the printed INTF/INTN and SHD
blocks of `article_html`. A sense whose stored rows do not align with its
printed block is withheld whole. Lexeme mapping and card sense minting belong
to assembly, not this extractor.
"""

import json
from bisect import bisect_right
from itertools import pairwise

from ..contract import Candidate
from ..errors import require
from .wp3_sources import (
    ARTICLE,
    CITATION,
    SENSE,
    STORE,
    Markup,
    authenticate,
    card_unit,
    fetch,
    query,
    sense_unit_key,
    value,
    within,
)

UNIT_QUERY = query(
    "SELECT s.id FROM sum20_senses s JOIN sum20_articles a ON a.id=s.article_id "
    "WHERE a.quarantine_reason='' ORDER BY a.id,s.sense_order,s.id"
)
# The closed HTML text-node transform. It is generic, despite the ULIF name.
HTML_TEXT = "ulif_html_text@1"


def squash(text):
    # The SUM20 parser pads inline blocks with spaces; printed spans do not.
    return "".join(text.split())


def stored_labels(sense):
    try:
        labels = json.loads(sense["register_labels"])
    except (TypeError, ValueError):
        return None
    return labels if isinstance(labels, list) and all(isinstance(x, str) for x in labels) else None


def printed_scopes(markup, sense, rows):
    """Split a numbered sense's printed block at its // shades.

    Returns `(definition, labels, quotation_rows)` for the numbered sense and then
    each shade, or None unless the stored definition, labels and quotations
    align exactly (whitespace aside) with the block the SUM20 parser enumerated.
    """

    def text(node):
        return markup.text[slice(*markup.span(node))]

    def printed(name, outer):
        return [n for n in markup.classed(name) if within(outer, n) and text(n)]

    entries = markup.classed("ENTRY")
    if len(entries) != 1 or markup.classed("LINKENTRY"):
        return None
    # The parser's enumeration: the first INTF, then every INTN, empty or not.
    intf, intn = ([n for n in markup.classed(name) if within(entries[0], n)] for name in ("INTF", "INTN"))
    blocks = intf[:1] + intn
    if any(a.end > b.start for a, b in pairwise(blocks)) or not 0 < sense["sense_order"] <= len(blocks):
        return None
    block = blocks[sense["sense_order"] - 1]
    shades, formulas, labels, ills = (printed(name, block) for name in ("SHD", "FORMULA", "PARAM", "ILL"))
    if any(within(a, b) for group in (shades, ills) for a in group for b in group):
        return None
    if any(within(outer, label) for label in labels for outer in (*ills, *formulas)):
        return None
    starts = [n.start for n in shades]
    scopes = [([], [], []) for _ in range(len(shades) + 1)]
    for part, nodes in ((0, formulas), (1, labels)):
        for node in nodes:
            scopes[bisect_right(starts, node.start)][part].append(node)
    # Like the SUM20 parser, an illustration is quoted by its first nonempty ILLTXT.
    quotes = [(ill, t[0]) for ill in ills if (t := [n for n in markup.classed("ILLTXT") if within(ill, n)])]
    quotes = [(ill, t) for ill, t in quotes if text(t)]
    if len(quotes) != len(rows) or any(
        squash(text(t)) != squash(r["citation_text"]) for (_, t), r in zip(quotes, rows, strict=True)
    ):
        return None
    for (ill, _), row in zip(quotes, rows, strict=True):
        scopes[bisect_right(starts, ill.start)][2].append(row)
    numbered = scopes[0][0]
    if len(numbered) != 1 or squash(text(numbered[0])) != squash(sense["definition"]):
        return None
    expected_labels = stored_labels(sense)
    if expected_labels is None or [squash(text(n)) for s in scopes for n in s[1]] != list(map(squash, expected_labels)):
        return None
    if any(len(s[0]) > 1 for s in scopes[1:]):
        return None
    return [(s[0][0] if s[0] else None, tuple(s[1]), tuple(s[2])) for s in scopes]


def sense_units(reader, sense, article, markup):
    """Every unit printed under one stored sense: `(shade, slots, context, response, reason)`."""

    def html(slot, node):
        return value(ARTICLE, article, "article_html", "sum20", slot, markup.span(node), HTML_TEXT)

    def quotation(row):
        return value(CITATION, row, "citation_text", "sum20", "sense_citations")

    rows = [
        dict(row)
        for row in reader.connections[STORE].execute(
            'SELECT * FROM sum20_citations WHERE article_id=? AND sense_ref=? ORDER BY "order",id',
            (article["id"], sense["sense_order"]),
        )
    ]
    slots = (value(ARTICLE, article, "stressed_headword", "sum20", "headword"),)
    lead = tuple(value(ARTICLE, article, field, "sum20", field) for field in ("grammar", "pos") if article[field])
    definition = value(SENSE, sense, "definition", "sum20", "definition")
    reason = None
    if not slots[0].text.strip():
        reason = "headword_unresolved"
    elif not definition.text.strip():
        reason = "definition_unresolved"
    elif any(not row["citation_text"].strip() for row in rows):
        reason = "citation_unresolved"
    scopes = None if reason else printed_scopes(markup, sense, rows)
    if scopes is None:
        # The stored, unscoped payload remains accounting evidence only.
        context = (
            *lead,
            value(SENSE, sense, "register_labels", "sum20", "register_labels"),
            *map(quotation, rows),
        )
        return [(0, slots, context, (definition,), reason or "sense_scope_unresolved")]
    units = []
    for shade, (formula, labels, quotes) in enumerate(scopes):
        context = (*lead, *(html("register_label", n) for n in labels), *map(quotation, quotes))
        if shade == 0:
            units.append((0, slots, context, (definition,), None))
        elif formula is None:
            units.append((shade, slots, context, (), "definition_unresolved"))
        else:
            units.append((shade, slots, context, (html("definition", formula),), None))
    return units


def as_candidate(key, unit):
    shade, slots, context, response, reason = unit
    return Candidate(
        "C3",
        f"{key}//{shade}" if shade else key,
        "withheld" if reason else "accepted",
        reason or "ok",
        (reason,) if reason else (),
        "sense_definition",
        slots,
        context,
        response,
        (),
    )


def iter_candidates(ctx):
    reader = ctx.reader
    markup = None
    for item in reader.connections[STORE].execute(UNIT_QUERY["sql"]):
        key = str(item[0])
        sense = fetch(reader, SENSE, key)
        article = fetch(reader, ARTICLE, sense["article_id"])
        if markup is None or markup[0] != article["id"]:
            markup = (article["id"], Markup(article["article_html"]))
        for unit in sense_units(reader, sense, article, markup[1]):
            yield as_candidate(key, unit)


def validate(ctx, unit):
    c = unit.candidate
    require(c.component == "C3" and c.operation == "sense_definition", "operation")
    authenticate(ctx, c, {ARTICLE, SENSE, CITATION}, "sum20")
    key, shade = sense_unit_key(c.unit_id)
    sense = fetch(ctx.reader, SENSE, key)
    article = fetch(ctx.reader, ARTICLE, sense["article_id"])
    require(article["quarantine_reason"] == "", "quarantined_source")
    require(unit == card_unit(ctx, c, SENSE), "binding_group")
    printed = {u[0]: u for u in sense_units(ctx.reader, sense, article, Markup(article["article_html"]))}
    require(shade in printed, "binding_group")
    expected = as_candidate(key, printed[shade])
    require((c.slots, c.context, c.response) == (expected.slots, expected.context, expected.response), "binding_sense")
    require(
        (c.outcome, c.reason, c.evidence, c.flags)
        == (expected.outcome, expected.reason, expected.evidence, expected.flags),
        "ingestion_outcome",
    )


def iter_card_units(ctx):
    for candidate in iter_candidates(ctx):
        unit = card_unit(ctx, candidate, SENSE)
        validate(ctx, unit)
        yield unit
