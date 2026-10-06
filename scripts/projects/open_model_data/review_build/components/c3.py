"""Registered C3 component: ULIF relations and official SUM20 meanings."""

from typing import ClassVar

from . import c3_relations, c3_sum20_meaning
from .wp3_sources import REASONS, SUM20_ADAPTER, SUM20_COMPATIBILITY, ULIF_ADAPTER, ULIF_COMPATIBILITY


class C3:
    files: ClassVar[dict] = {}
    adapters: ClassVar[dict] = {"ulif": ULIF_ADAPTER, "sum20": SUM20_ADAPTER}
    spec: ClassVar[dict] = {
        "compatibility": [*ULIF_COMPATIBILITY, *SUM20_COMPATIBILITY],
        "operations": ["synonyms", "antonyms", "sense_definition"],
        "reasons": REASONS,
        "unit_grain": "ULIF synonyms/antonyms section; unquarantined SUM20 article sense (operation-specific census)",
        "reference_multiplicity": "One record per unit; all selected sense citations retained in source order.",
        "operation_specs": {
            **{op: c3_relations.operation_spec(op) for op in c3_relations.COUNTS},
            "sense_definition": c3_sum20_meaning.operation_spec(),
        },
    }

    def iter_candidates(self, ctx):
        yield from c3_relations.iter_candidates(ctx)
        yield from c3_sum20_meaning.iter_candidates(ctx)


COMPONENT = C3()
