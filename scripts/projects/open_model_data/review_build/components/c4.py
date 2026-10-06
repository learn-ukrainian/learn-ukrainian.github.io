"""Registered C4 component; unauthenticated aggregator editions are excluded."""

from typing import ClassVar

from .c4_phraseology import iter_candidates, operation_spec
from .wp3_sources import REASONS, ULIF_ADAPTER


class C4:
    files: ClassVar[dict] = {}
    adapters: ClassVar[dict] = {"ulif": ULIF_ADAPTER}
    spec: ClassVar[dict] = {
        "operations": ["idiom_definition"],
        "reasons": REASONS,
        "unit_grain": "ULIF phraseology section; standalone phraseology dictionary not admitted (authenticated edition-held-text evidence unavailable).",
        "reference_multiplicity": "One record per section; all parsed author-labelled citations retained in source order.",
        "operation_specs": {"idiom_definition": operation_spec()},
    }

    def iter_candidates(self, ctx):
        yield from iter_candidates(ctx)


COMPONENT = C4()
