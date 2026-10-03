"""Source-pattern regressions use a stable optional-parser fallback."""

import pytest


@pytest.fixture(autouse=True)
def stable_pattern_parser(request, monkeypatch):
    """Keep historical matcher assertions independent of host model availability.

    Hybrid real-model, missing-dependency and deadline tests own their parser
    lanes separately. This fixture changes neither their tests nor their gates.
    """
    if request.node.path.name not in {
        "test_antonenko_patterns.py",
        "test_antonenko_round2.py",
        "test_antonenko_round3.py",
    }:
        return
    from scripts.verification import temporal_protiah

    class Unavailable:
        def parse(self, text, budget):
            return None, "parser_unavailable"

    monkeypatch.setattr(temporal_protiah, "PARSER", Unavailable())
