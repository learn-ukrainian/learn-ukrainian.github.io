"""SYNTHETIC optional-set bindings must prove absence independently."""

from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import bindings
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader


def test_optional_empty_set_requires_independent_empty_query(bundle):
    candidate = bundle["candidates"][0]
    selector = {"area": "context", "slot": "SYNTHETIC optional", "match": "all", "min": 0}
    query = {"kind": "sql", "store": "sources.db", "sql": "SELECT target_field FROM units WHERE id=0"}
    rule = {"op": "set_query_equal", "values": [selector], "normalizer": "identity", "queries": [{"query": query}]}
    spec = {"schema": "binding-spec.v1", "rules": [rule]}
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert bindings.expand(candidate, selector) == []
        assert bindings.check(candidate, spec, reader, {}) == {"set_query_equal"}
        query["sql"] = "SELECT target_field FROM units WHERE id=1"
        with pytest.raises(BuildError, match="binding_set"):
            bindings.check(candidate, spec, reader, {})
        value = replace(candidate.response[0], slot="SYNTHETIC optional")
        assert bindings.check(replace(candidate, context=(value,)), spec, reader, {}) == {"set_query_equal"}
        selector.pop("min")
        with pytest.raises(BuildError, match="binding_selector"):
            bindings.expand(candidate, selector)
        selector["min"] = -1
        with pytest.raises(BuildError, match="binding_selector"):
            bindings.expand(candidate, selector)
        rule["values"] = []
        with pytest.raises(BuildError, match="binding_set"):
            bindings.check(candidate, spec, reader, {})
