import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import codes

ROOT = Path(__file__).resolve().parents[3]


def validator(name):
    schema = json.loads((ROOT / f"schemas/evidence-words{name}-v1.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def synthetic_store():
    return {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "a" * 40,
            "sources_db": "b" * 64,
            "vesum": "c" * 64,
            "trie": "d" * 64,
            "ulif_forms": "pending",
        },
        "words": [
            {
                "id": "W-001",
                "lemma": "synthetic",
                "pos": "noun",
                "entry": {"source": "vesum", "entry_id": 1},
                "ulif": "pending",
                "forms": [
                    {
                        "form": "synthetic-form",
                        "tags": "noun:f:v_naz",
                        "stress_source": "pending",
                        "markers": [],
                        "learner": True,
                    }
                ],
            }
        ],
    }


def test_synthetic_request():
    request = {
        "request_schema": 1,
        "level": "a1",
        "words": [
            {"lemma": "synthetic", "pos": "noun", "want": "new", "entry": {"source": "vesum", "entry_id": 2}},
            {
                "lemma": "synthetic-other",
                "pos": "noun",
                "want": "W-002",
                "entry": {"source": "ulif", "homonym_index": 1},
            },
        ],
    }
    checker = validator("-request")
    checker.validate(request)
    for field in ("pos", "want", "lemma"):
        bad = deepcopy(request)
        bad["words"][0].pop(field)
        assert not checker.is_valid(bad)
    bad = deepcopy(request)
    bad["words"][0]["entry"]["hint"] = "synthetic hint"
    assert not checker.is_valid(bad)


def test_synthetic_store_and_pending_stress_contract():
    store = synthetic_store()
    checker = validator("")
    checker.validate(store)
    form = store["words"][0]["forms"][0]
    form["stressed"] = "synthetic-stressed"
    assert not checker.is_valid(store)
    for source in ("trie", "ulif", "none"):
        form["stress_source"] = source
        if source == "none":
            form["stressed"] = form["form"]  # equality is a verifier check, not expressible in JSON Schema
        checker.validate(store)
        missing = deepcopy(store)
        missing["words"][0]["forms"][0].pop("stressed")
        assert not checker.is_valid(missing)


def test_unresolved_store_cannot_merge_candidate_forms():
    store = synthetic_store()
    word = store["words"][0]
    word["entry"] = "unresolved"
    word["candidates"] = [{"entry_id": 1, "forms": ["synthetic-a"]}, {"entry_id": 2, "forms": ["synthetic-b"]}]
    checker = validator("")
    assert not checker.is_valid(store)
    word["forms"] = []
    checker.validate(store)
    del word["candidates"]
    assert not checker.is_valid(store)


@pytest.mark.parametrize(
    "location", [(), ("built_with",), ("words", 0), ("words", 0, "entry"), ("words", 0, "forms", 0)]
)
def test_no_extra_properties(location):
    store = synthetic_store()
    target = store
    for key in location:
        target = target[key]
    target["synthetic_extra"] = "unexpected"
    assert not validator("").is_valid(store)


def test_gloss_requires_source():
    store = synthetic_store()
    word = store["words"][0]
    word["gloss_en"] = "synthetic gloss"
    assert not validator("").is_valid(store)
    word["gloss_source"] = {"table": "dmklinger_uk_en", "id": 1}
    validator("").validate(store)


@pytest.mark.parametrize("marker", sorted(codes.EXCLUDING_MARKERS))
def test_all_excluding_markers_require_nonlearner_forms(marker):
    store = synthetic_store()
    form = store["words"][0]["forms"][0]
    checker = validator("")
    for markers in ([marker], [{"marker": marker, "origin": "synthetic", "marker_class": "synthetic"}]):
        form["markers"] = markers
        form["learner"] = True
        assert not checker.is_valid(store)
        form["learner"] = False
        checker.validate(store)
        assert len(store["words"][0]["forms"]) == 1
