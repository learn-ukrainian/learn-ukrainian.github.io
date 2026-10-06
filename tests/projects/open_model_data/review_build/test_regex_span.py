"""Generic structural capture bindings use SYNTHETIC field bytes only."""

from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import bindings
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import selector


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(
    "mutation",
    [None, "wrong_span", "missing_capture", "missing_span", "absent_nested", "supporting_selector", "column_selector"],
)
def test_structural_capture_accept_and_refuse_wrong_source_span(bundle, nested, mutation):
    candidate = bundle["candidates"][0]
    part = candidate.slots[0]
    span = (len("SYNTHETIC "), len(part.text))
    rule = {
        "op": "regex_span",
        "values": [selector()],
        "pattern": r"SYNTHETIC (?P<field>sentence [0-9]+)",
        "group": "field",
        "trim": True,
    }
    if nested:
        rule.update(pattern=r"(?P<field>SYNTHETIC sentence [0-9]+)", nested={"pattern": r"sentence [0-9]+"})
    part = replace(part, text=part.text[slice(*span)], span=span)
    if mutation == "wrong_span":
        part = replace(part, span=(0, 9))
    elif mutation == "missing_capture":
        rule["pattern"] = "(?P<field>SYNTHETIC missing)"
    elif mutation == "missing_span":
        part = replace(part, span=None)
    elif mutation == "absent_nested":
        rule["nested"] = {"pattern": "SYNTHETIC absent"}
    elif mutation == "supporting_selector":
        rule["values"][0]["citation"] = 1
        part = replace(part, citations=part.citations * 2)
    elif mutation == "column_selector":
        rule["values"][0]["field"] = "source_field"
    candidate = replace(candidate, slots=(part,))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        if mutation:
            with pytest.raises(BuildError, match="binding_span"):
                bindings.check(candidate, {"schema": "binding-spec.v1", "rules": [rule]}, reader, {})
        else:
            assert bindings.check(candidate, {"schema": "binding-spec.v1", "rules": [rule]}, reader, {}) == {
                "regex_span"
            }
