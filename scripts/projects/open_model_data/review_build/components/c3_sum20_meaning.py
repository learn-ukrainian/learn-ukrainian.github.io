"""C3 card ingestion: every numbered sense of an unquarantined SUM20 article.

Card sense evidence does not need a training-prompt discriminator. Preserve
all numbered units and their complete definition, labels and own quotations.
Lexeme mapping and card sense minting belong to assembly, not this extractor.
"""

from ..contract import Candidate
from ..errors import require
from .wp3_sources import ARTICLE, CITATION, SENSE, STORE, authenticate, card_unit, fetch, query, value

UNIT_QUERY = query(
    "SELECT s.id FROM sum20_senses s JOIN sum20_articles a ON a.id=s.article_id "
    "WHERE a.quarantine_reason='' ORDER BY a.id,s.sense_order,s.id"
)


def sense_values(reader, sense, article):
    citations = reader.connections[STORE].execute(
        'SELECT * FROM sum20_citations WHERE article_id=? AND sense_ref=? ORDER BY "order",id',
        (article["id"], sense["sense_order"]),
    )
    context = (
        value(SENSE, sense, "register_labels", "sum20", "register_labels"),
        *(value(CITATION, dict(row), "citation_text", "sum20", "sense_citations") for row in citations),
    )
    if article["pos"]:
        context = (value(ARTICLE, article, "pos", "sum20", "pos"), *context)
    return (
        (value(ARTICLE, article, "stressed_headword", "sum20", "headword"),),
        context,
        (value(SENSE, sense, "definition", "sum20", "definition"),),
    )


def iter_candidates(ctx):
    reader = ctx.reader
    for item in reader.connections[STORE].execute(UNIT_QUERY["sql"]):
        key = str(item[0])
        sense = fetch(reader, SENSE, key)
        article = fetch(reader, ARTICLE, sense["article_id"])
        slots, context, response = sense_values(reader, sense, article)
        reason = None
        if not slots[0].text.strip():
            reason = "headword_unresolved"
        elif not response[0].text.strip():
            reason = "definition_unresolved"
        elif any(not v.text.strip() for v in context if v.slot == "sense_citations"):
            reason = "citation_unresolved"
        yield Candidate(
            "C3",
            key,
            "withheld" if reason else "accepted",
            reason or "ok",
            (reason,) if reason else (),
            "sense_definition",
            slots,
            context,
            response,
            (),
        )


def validate(ctx, unit):
    c = unit.candidate
    require(c.component == "C3" and c.operation == "sense_definition", "operation")
    authenticate(ctx, c, {ARTICLE, SENSE, CITATION}, "sum20")
    sense = fetch(ctx.reader, SENSE, c.unit_id)
    article = fetch(ctx.reader, ARTICLE, sense["article_id"])
    require(article["quarantine_reason"] == "", "quarantined_source")
    require(unit == card_unit(ctx, c, SENSE), "binding_group")
    require((c.slots, c.context, c.response) == sense_values(ctx.reader, sense, article), "binding_sense")
    if c.outcome == "accepted":
        require(c.reason == "ok" and not c.evidence and not c.flags, "ingestion_outcome")
        require(bool(c.slots[0].text.strip()) and bool(c.response[0].text.strip()), "definition_unresolved")
        require(all(v.text.strip() for v in c.context if v.slot == "sense_citations"), "citation_unresolved")
    else:
        require(
            c.outcome == "withheld"
            and c.reason in {"headword_unresolved", "definition_unresolved", "citation_unresolved"},
            "ingestion_outcome",
        )


def iter_card_units(ctx):
    for candidate in iter_candidates(ctx):
        unit = card_unit(ctx, candidate, SENSE)
        validate(ctx, unit)
        yield unit
