"""C3 meanings: one verbatim definition per unquarantined article/sense."""

from ..contract import Candidate
from .wp3_sources import ARTICLE, CITATION, SENSE, STORE, fetch, identity, query, ref, value

UNIT_QUERY = query(
    "SELECT s.id FROM sum20_senses s JOIN sum20_articles a ON a.id=s.article_id WHERE coalesce(a.quarantine_reason,'')=''"
)


def operation_spec():
    head = ref("slots", "headword")
    definition = ref("response", "definition")
    labels = ref("context", "register_labels")
    citations = ref("context", "sense_citations", match="all", min=0)
    article = {**definition, "field": "article_id"}
    sense = {**definition, "field": "sense_order"}
    citation_query = query(
        'SELECT citation_text FROM sum20_citations WHERE article_id=? AND sense_ref=? ORDER BY "order",id'
    )
    has_citations = query("SELECT EXISTS(SELECT 1 FROM sum20_citations WHERE article_id=? AND sense_ref=?)")
    article_count = query(
        "SELECT count(*) FROM sum20_senses s JOIN sum20_articles a ON a.id=s.article_id WHERE a.id=? AND coalesce(a.quarantine_reason,'')=''"
    )
    discrimination = {
        "query": query(
            "SELECT NOT EXISTS(SELECT 1 FROM sum20_senses other "
            "JOIN sum20_articles a ON a.id=other.article_id "
            "WHERE a.stressed_headword=? AND coalesce(a.pos,'')=coalesce(?, '') "
            "AND coalesce(a.quarantine_reason,'')='' AND other.id<>? AND other.definition<>? "
            "AND (SELECT json_group_array(citation_text) FROM "
            '(SELECT citation_text FROM sum20_citations WHERE article_id=other.article_id AND sense_ref=other.sense_order ORDER BY "order",id))='
            "(SELECT json_group_array(citation_text) FROM "
            '(SELECT citation_text FROM sum20_citations WHERE article_id=? AND sense_ref=? ORDER BY "order",id)))'
        ),
        "parameters": [
            {**head, "field": "stressed_headword"},
            {**head, "field": "pos"},
            {**definition, "field": "id"},
            {**definition, "field": "definition"},
            article,
            sense,
        ],
        "expected": [1],
    }
    return {
        "unit_query": UNIT_QUERY,
        "frozen_count": 168,
        "unit_id": identity(SENSE, "response", "definition"),
        "unit_grain": "unquarantined SUM20 article sense",
        "binding": {
            "schema": "binding-spec.v1",
            "rules": [
                {
                    "op": "one_group",
                    "values": [
                        {**head, "field": "id"},
                        {**ref("context", "pos", match="all", min=0), "field": "id"},
                        article,
                        {**labels, "field": "article_id"},
                        {**citations, "field": "article_id"},
                    ],
                },
                {"op": "same_row", "values": [definition, labels]},
                {"op": "one_group", "values": [sense, {**citations, "field": "sense_ref"}]},
                {"op": "literal", "values": [{**head, "field": "quarantine_reason"}], "expected": ""},
                {
                    "op": "sequence_query_equal",
                    "values": [citations],
                    "normalizer": "identity",
                    "queries": [{"query": citation_query, "parameters": [article, sense]}],
                },
            ],
        },
        "applicability": {
            "with_citations": [
                {"query": has_citations, "parameters": [article, sense], "expected": [1]},
                discrimination,
            ],
            "single_sense": [
                {"query": has_citations, "parameters": [article, sense], "expected": [0]},
                {"query": article_count, "parameters": [article], "expected": [1]},
                discrimination,
            ],
        },
        "context_serializer": "json_array",
    }


def iter_candidates(ctx):
    reader = ctx.reader
    for key in reader.units(UNIT_QUERY):
        sense = fetch(reader, SENSE, key)
        article = fetch(reader, ARTICLE, sense["article_id"])
        citations = [
            dict(r)
            for r in reader.connections[STORE].execute(
                'SELECT * FROM sum20_citations WHERE article_id=? AND sense_ref=? ORDER BY "order",id',
                (sense["article_id"], sense["sense_order"]),
            )
        ]
        definition = value(SENSE, sense, "definition", "sum20", "definition")
        labels = value(SENSE, sense, "register_labels", "sum20", "register_labels")
        reason = None
        context = (labels, *(value(CITATION, row, "citation_text", "sum20", "sense_citations") for row in citations))
        slots = ()
        if not article["stressed_headword"]:
            reason = "headword_unresolved"
        elif not definition.text.strip():
            reason = "definition_unresolved"
        elif any(not c["citation_text"].strip() for c in citations):
            reason = "citation_unresolved"
        else:
            slots = (value(ARTICLE, article, "stressed_headword", "sum20", "headword"),)
            if article["pos"]:
                context = (value(ARTICLE, article, "pos", "sum20", "pos"), *context)
            siblings = [
                dict(r)
                for r in reader.connections[STORE].execute(
                    "SELECT * FROM sum20_senses WHERE article_id=? ORDER BY sense_order,id", (article["id"],)
                )
            ]
            if not citations and len(siblings) != 1:
                reason = "sense_not_visible"
            # The source examples must distinguish conflicting definitions.
            current = [r["citation_text"] for r in citations]
            for sibling in siblings:
                if sibling["id"] == sense["id"] or sibling["definition"] == sense["definition"]:
                    continue
                other = [
                    r[0]
                    for r in reader.connections[STORE].execute(
                        'SELECT citation_text FROM sum20_citations WHERE article_id=? AND sense_ref=? ORDER BY "order",id',
                        (article["id"], sibling["sense_order"]),
                    )
                ]
                if current and current == other:
                    reason = "context_not_discriminating"
        yield Candidate(
            "C3",
            key,
            "withheld" if reason else "accepted",
            reason or "ok",
            (reason,) if reason else (),
            "sense_definition",
            slots,
            context,
            (definition,),
            (),
        )
