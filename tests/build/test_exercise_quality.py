import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from audit.checks.contract_compliance import check_contract_compliance


def _contract(*items):
    return {
        "teaching_beats": {"section_order": [], "sections": []},
        "activity_obligations": [{"type": item} for item in items],
    }


def _content(*markers):
    return "\n".join(f"<!-- INJECT_ACTIVITY: {marker} -->" for marker in markers)


@pytest.mark.parametrize(
    ("obligations", "markers", "missing"),
    [
        (("quiz", "fill-in", "match-up"), ("fill-in-b", "quiz-a", "match-up-c"), None),
        (("quiz", "fill-in", "match-up"), ("quiz-a", "fill-in-b"), "match-up"),
        (("quiz", "quiz", "fill-in"), ("quiz-a", "fill-in-b"), "quiz"),
        (("quiz", "fill-in"), ("quiz-a", "fill-in-b", "match-up-c"), None),
    ],
)
def test_activity_obligations_are_multiset_membership(obligations, markers, missing):
    violations = [
        item
        for item in check_contract_compliance(_content(*markers), _contract(*obligations))
        if item["type"] == "ACTIVITY_ORDER"
    ]
    if missing is None:
        assert violations == []
    else:
        assert len(violations) == 1
        assert missing in violations[0]["message"]
