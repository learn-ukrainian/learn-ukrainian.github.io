import json
import random
import string
from dataclasses import asdict, fields, replace

import pytest

from scripts.projects.open_model_data.review_build.contract import (
    Candidate,
    Citation,
    Value,
    candidate_from_dict,
    canonical,
    digest,
    record_id,
)
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.transforms import REGISTRY, transform


def test_exact_contract_and_roundtrip(bundle):
    assert [f.name for f in fields(Citation)] == [
        "source_id",
        "store",
        "table",
        "row_key",
        "field",
        "locator",
        "field_sha256",
    ]
    assert [f.name for f in fields(Value)] == ["slot", "text", "citations", "span", "transform"]
    assert [f.name for f in fields(Candidate)] == [
        "component",
        "unit_id",
        "outcome",
        "reason",
        "evidence",
        "operation",
        "slots",
        "context",
        "response",
        "flags",
    ]
    candidate = bundle["candidates"][0]
    assert candidate_from_dict(json.loads(json.dumps(asdict(candidate)))) == candidate
    assert record_id(candidate) == record_id(replace(candidate, outcome="excluded", reason="synthetic_excluded"))
    assert record_id(candidate) != record_id(replace(candidate, unit_id="SYNTHETIC other"))
    value = candidate.slots[0]
    raw = {
        "component": candidate.component,
        "operation": candidate.operation,
        "unit_id": candidate.unit_id,
        "values": [
            [v.slot, v.text, [list(asdict(c).values()) for c in v.citations], v.span, v.transform]
            for v in candidate.slots + candidate.context + candidate.response
        ],
    }
    assert record_id(candidate) == digest(canonical(raw))
    assert record_id(candidate) != record_id(replace(candidate, slots=(replace(value, span=(0, 1)),)))
    assert candidate_from_dict({**asdict(candidate), "slots": [{**asdict(value), "span": [0, 1]}]}).slots[0].span == (
        0,
        1,
    )
    assert canonical({"b": 2, "a": "SYNTHETIC"}) == b'{"a":"SYNTHETIC","b":2}'


@pytest.mark.parametrize("seed", range(12))
def test_verbatim_property(seed):
    text = "SYNTHETIC " + "".join(random.Random(seed).choices(string.printable, k=300))
    assert transform("verbatim", text).text == text


@pytest.mark.parametrize("seed", range(12))
def test_html_text_node_order_property(seed):
    generator = random.Random(seed)
    nodes = ["SYNTHETIC " + "".join(generator.choices(string.ascii_letters, k=20)) for _ in range(8)]
    html = "<div>" + "".join(f"<b>{node}</b> " for node in nodes) + "</div>"
    assert transform("ulif_html_text@1", html).text == " ".join(nodes)
    assert transform("ulif_html_text@1", "<i>SYNTHETIC &amp; text</i>").text == "SYNTHETIC & text"


@pytest.mark.parametrize("seed", range(12))
def test_line_excision_only_removes_declared_whole_lines(seed):
    generator = random.Random(seed)
    lines = [f"SYNTHETIC {'HEAD' if generator.random() < 0.3 else 'body'} {i}\n" for i in range(20)]
    result = transform("line_excision@1", "".join(lines), {"patterns": [r"SYNTHETIC HEAD \d+"]})
    assert result.text == "".join(line for line in lines if not line.startswith("SYNTHETIC HEAD"))
    assert result.dropped_lines == tuple((i, i) for i, line in enumerate(lines, 1) if line.startswith("SYNTHETIC HEAD"))


@pytest.mark.parametrize("seed", range(12))
def test_dehyphenation_requires_positive_join_and_negative_hyphen_witness(seed):
    generator = random.Random(seed)
    left, right = ["".join(generator.choices(string.ascii_letters, k=8)) for _ in range(2)]

    class SyntheticWords:
        def __init__(self, forms):
            self.forms = forms

        def is_word(self, word, policy):
            return word in self.forms

    text = f"SYNTHETIC {left}-\n{right}"
    for forms, joins in ((set(), False), ({left + right, left + "-" + right}, False), ({left + right}, True)):
        result = transform("dehyphenate@1", text, reader=SyntheticWords(forms))
        assert result.text == (text.replace("-\n", "") if joins else text)
        assert bool(result.joins) == joins
        if joins:
            start, end, joined = result.joins[0]
            assert text[start:end] == left + "-\n" + right
            assert joined == left + right


def test_registry_is_closed_and_bad_policies_fail():
    assert set(REGISTRY) == {"verbatim", "ulif_html_text@1", "line_excision@1", "dehyphenate@1"}
    with pytest.raises(TypeError):
        REGISTRY["SYNTHETIC paraphrase"] = lambda s: s
    for name, policy in (("paraphrase", {}), ("line_excision@1", {}), ("dehyphenate@1", {})):
        with pytest.raises(BuildError):
            transform(name, "SYNTHETIC text", policy)
