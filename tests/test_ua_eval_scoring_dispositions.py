from __future__ import annotations

import copy
import json

import pytest

from scripts.projects.ua_eval_harness.build_scoring_dispositions import (
    DEFAULT_CONFIG,
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    DispositionError,
    decide_disposition,
    validate_dispositions,
)


def _policy() -> dict:
    return json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))["policy"]


def _committed() -> tuple[dict, dict]:
    manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    dispositions = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    return manifest, dispositions


def _rows_by_id(dispositions: dict, item_id: str) -> list[dict]:
    layout = dispositions["record_layout"]
    return [dict(zip(layout, row, strict=True)) for row in dispositions["rows"] if row[0] == item_id]


def test_upstream_labels_are_preserved_and_every_calque_edit_is_disposed() -> None:
    manifest, dispositions = _committed()

    validate_dispositions(dispositions, manifest=manifest)

    assert dispositions["semantics"]["upstream_tag_preserved"] is True
    assert dispositions["counts"]["upstream_f_calque_annotations"] == 354
    assert all(row[4] == "F/Calque" for row in dispositions["rows"])


def test_confirmed_dialect_is_standardization_not_headline_calque() -> None:
    status, headline, reason = decide_disposition(
        source_span=["діалектна"],
        attested=True,
        style_markers=["dialect"],
        policy=_policy(),
        contextual_disposition="REGIONAL_STANDARDIZATION",
        contextual_reason="context and independent heritage evidence confirm authentic usage",
    )

    assert status == "REGIONAL_STANDARDIZATION"
    assert headline is False
    assert "confirm authentic" in reason


def test_ambiguous_register_and_heritage_evidence_abstains() -> None:
    assert decide_disposition(
        source_span=["слово"],
        attested=True,
        style_markers=["arch"],
        policy=_policy(),
    )[0:2] == ("HERITAGE_CONFLICT", False)
    assert decide_disposition(
        source_span=["слово"],
        attested=True,
        style_markers=["slang"],
        policy=_policy(),
    )[0:2] == ("CONTESTED", False)


def test_disposition_logic_consumes_the_frozen_policy_mapping() -> None:
    policy = _policy()
    policy["bad_marker"] = "CONTESTED"

    status, headline, _reason = decide_disposition(
        source_span=["слово"],
        attested=True,
        style_markers=["bad"],
        policy=policy,
    )

    assert (status, headline) == ("CONTESTED", False)


def test_no_silent_override_of_upstream_tag() -> None:
    manifest, dispositions = _committed()
    edited = copy.deepcopy(dispositions)
    edited["rows"][0][4] = "REGIONAL_STANDARDIZATION"

    with pytest.raises(DispositionError, match="upstream tag was silently relabelled"):
        validate_dispositions(edited, manifest=manifest)


def test_probe_regressions_include_false_collision_and_bounded_abstentions() -> None:
    _manifest, dispositions = _committed()
    counts = dispositions["counts"]

    assert counts["raw_style_collision_spans"] == 49
    assert counts["raw_style_collision_spans_by_marker"] == {
        "arch": 3,
        "bad": 34,
        "rare": 2,
        "slang": 10,
    }
    assert counts["included_in_headline_calque"] == 338
    assert counts["excluded_from_headline_calque"] == 16
    slang_spans = {
        (row["item_id"], tuple(row["source_span"]))
        for row in (dict(zip(dispositions["record_layout"], raw_row, strict=True)) for raw_row in dispositions["rows"])
        if any("slang" in evidence["style_markers"] for evidence in row["evidence"]["exact_form_evidence"])
    }
    assert slang_spans == {
        ("ua-gec-test-0128-s0017", ("гайд",)),
        ("ua-gec-test-0252-s0016", ("апдейт",)),
        ("ua-gec-test-0324-s0042", ("імейли",)),
        ("ua-gec-test-0576-s0027", ("постить",)),
        ("ua-gec-test-0624-s0001", ("хоумскулерами",)),
        ("ua-gec-test-0624-s0035", ("хоумскулерів",)),
        ("ua-gec-test-0624-s0039", ("хоумскулерів",)),
        ("ua-gec-test-0683-s0001", ("плейлист",)),
        ("ua-gec-test-0838-s0034", ("постили",)),
        ("ua-gec-test-1799-s0020", ("лайків",)),
    }

    aunt = _rows_by_id(dispositions, "ua-gec-test-0017-s0010")
    roof = _rows_by_id(dispositions, "ua-gec-test-0111-s0007")
    collision = _rows_by_id(dispositions, "ua-gec-test-0339-s0007")
    speaker = _rows_by_id(dispositions, "ua-gec-test-0430-s0010")
    red = _rows_by_id(dispositions, "ua-gec-test-0843-s0006")

    assert next(row for row in aunt if row["source_span"] == ["тьоті"])["disposition"] == "REGISTER_STANDARDIZATION"
    assert {row["disposition"] for row in roof if row["source_span"] == ["кришею"]} == {"HERITAGE_CONFLICT"}
    assert next(row for row in collision if row["source_span"] == ["була"])["disposition"] == "HEADLINE_CALQUE"
    assert next(row for row in speaker if row["source_span"] == ["Спікери"])["disposition"] == "CONTESTED"
    assert {row["disposition"] for row in red if row["source_span"] == ["рижого"]} == {"REGISTER_STANDARDIZATION"}
