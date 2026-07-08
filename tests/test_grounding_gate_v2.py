from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from scripts.audit import grounding_gate_v2, grounding_shadow_compare
from scripts.audit.llm_reviewer_dispatch import enforce_grounding_against_tool_events


def _make_event(
    *,
    tool: str = "query_wikipedia",
    query: str = "Григорій Сковорода",
    output: str = "Сковорода Григорій Савич народився у 1722 році.",
    tool_call_id: str = "call-1",
) -> dict[str, Any]:
    return {
        "tool": tool,
        "input": {"query": query},
        "output": output,
        "tool_call_id": tool_call_id,
        "status": "completed",
    }


def test_fuzzy_near_miss():
    # 1. fuzzy near-miss (whitespace/diacritic/ellipsis variant of a real output) -> anchored=True
    events = [_make_event()]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "григорі́й   савич  народився"  # diacritics, extra spaces, lowercase
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=0.7)
    assert res.anchored is True
    assert res.abstained is False
    assert res.reason == "anchored"
    assert res.similarity > 0.7


def test_fabricated_excerpt():
    # 2. fabricated excerpt (in NO output) -> anchored=False, reason="digit_absent"
    events = [_make_event()]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода Григорій Савич народився у місті Парижі в 1900 році"
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
    assert res.anchored is False
    assert res.reason == "digit_absent"


def test_boilerplate_abstain():
    # 3. repeated boilerplate across >=2 unrelated outputs -> abstained=True
    # Unrelated outputs containing the same boilerplate
    events = [
        _make_event(output="Помилка: Не вдалося знайти результати за цим запитом. Спробуйте пізніше.", tool_call_id="call-1"),
        _make_event(output="Помилка: Не вдалося знайти результати за цим запитом. Спробуйте інший пошук.", tool_call_id="call-2"),
    ]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Помилка: Не вдалося знайти результати за цим запитом."
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=0.7)
    assert res.anchored is False
    assert res.abstained is True
    assert res.reason == "abstain_ambiguous"


def test_insufficient_mass():
    # 4. title-only / date-only / single short token -> anchored=False, reason="insufficient_mass"
    events = [_make_event()]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Григорій"  # Only 8 non-whitespace characters (< 15)
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=0.7)
    assert res.anchored is False
    assert res.reason == "insufficient_mass"


def test_ordered_ellipsis():
    # 5. ordered-ellipsis excerpt whose segments appear in order in ONE output -> anchored=True
    events = [_make_event()]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода [...] народився у 1722 році."
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=0.7)
    assert res.anchored is True
    assert res.reason == "anchored"


def test_ellipsis_split_across_events():
    # 6. ellipsis segments split across TWO outputs -> not anchored (no cross-event stitching)
    events = [
        _make_event(output="Сковорода Григорій Савич", tool_call_id="call-1"),
        _make_event(output="народився у 1722 році.", tool_call_id="call-2"),
    ]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода [...] народився у 1722 році."
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=0.7)
    assert res.anchored is False
    assert res.reason == "below_tau"


def test_present_but_irrelevant_excerpt():
    # 7. present-but-irrelevant excerpt (real string, unrelated claim) -> anchored=True
    # Layer A is provenance only; entailment rejection is Layer B, out of scope here.
    events = [_make_event()]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода Григорій Савич народився у 1722 році."
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=0.7)
    assert res.anchored is True
    assert res.reason == "anchored"


def test_tool_query_mismatch_soft_signal():
    # 8. tool/query mismatch but strong excerpt anchor -> anchored=True (soft signal only)
    events = [_make_event()]
    grounding = {
        "tool": "invalid_tool",
        "query": "unrelated search query",
        "evidence_excerpt": "Сковорода Григорій Савич народився у 1722 році."
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=0.7)
    assert res.anchored is True
    assert res.reason == "anchored"


def test_v2_flag_wiring():
    # 9. v2 flag wiring: enforce_grounding_against_tool_events(..., gate_version="v2")
    # keeps a real grounding, drops a fabricated one; and default call is byte-identical to before.
    payload = {
        "findings": [
            {
                "excerpt": "finding-1",
                "grounding": {
                    "tool": "query_wikipedia",
                    "query": "Григорій Сковорода",
                    "evidence_excerpt": "Сковорода Григорій Савич народився у 1722 році."
                }
            },
            {
                "excerpt": "finding-2",
                "grounding": {
                    "tool": "query_wikipedia",
                    "query": "Григорій Сковорода",
                    "evidence_excerpt": "Сковорода народився в Парижі у Франції в 1900 році"  # Fabricated, low similarity
                }
            }
        ],
        "fact_checks": [
            {
                "claim": "claim-1",
                "grounding": {
                    "tool": "query_wikipedia",
                    "query": "Григорій Сковорода",
                    "evidence_excerpt": "Сковорода Григорій Савич народився у 1722 році."
                }
            }
        ]
    }
    dispatch_meta = {
        "tool_events": [
            {
                "tool": "query_wikipedia",
                "input": {"query": "Григорій Сковорода"},
                "output": "Сковорода Григорій Савич народився у 1722 році.",
                "tool_call_id": "call-1",
                "status": "completed"
            }
        ]
    }

    # Test v2 behaviour: drops the second finding, keeps first finding and fact check, attaches diagnostics to fact check
    res_v2 = enforce_grounding_against_tool_events(payload, dispatch_meta, policy_family="seminar", gate_version="v2")
    assert len(res_v2.payload["findings"]) == 1
    assert res_v2.payload["findings"][0]["excerpt"] == "finding-1"
    assert len(res_v2.payload["fact_checks"]) == 1
    fc = res_v2.payload["fact_checks"][0]
    assert fc["anchor_similarity"] == 1.0
    assert fc["anchor_abstained"] is False
    assert fc["grounding_gate_version"] == "v2"

    # Test default (v1) behaviour: no diagnostic flags, keeps correct ones
    res_v1_default = enforce_grounding_against_tool_events(payload, dispatch_meta, policy_family="seminar")
    # v1 drops finding-2 because it's a fabricated substring
    assert len(res_v1_default.payload["findings"]) == 1
    fc_v1 = res_v1_default.payload["fact_checks"][0]
    assert "anchor_similarity" not in fc_v1
    assert "anchor_abstained" not in fc_v1
    assert "grounding_gate_version" not in fc_v1

    # Verify default call matches explicit gate_version="v1" exactly
    res_v1_explicit = enforce_grounding_against_tool_events(payload, dispatch_meta, policy_family="seminar", gate_version="v1")
    assert res_v1_default.payload == res_v1_explicit.payload


def test_shadow_compare_harness(tmp_path):
    # 10. Prove the shadow compare harness loads cells, dual-runs, and emits correct summary shape
    cell_payload = {
        "schema_version": "qg_bakeoff_run.v1",
        "seat": "test-seat",
        "arm": "tooled",
        "fixture": {"slug": "vesnianky"},
        "payload": {
            "fact_checks": [
                {
                    "claim": "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни.",
                    "grounding": {
                        "tool": "query_wikipedia",
                        "query": "Веснянки",
                        "evidence_excerpt": "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни."
                    }
                }
            ]
        },
        "dispatch": {
            "tool_events": [
                {
                    "tool": "query_wikipedia",
                    "input": {"query": "Веснянки"},
                    "output": "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни.",
                    "tool_call_id": "call-1",
                    "status": "completed"
                }
            ]
        }
    }

    cell_path = tmp_path / "cell_1.json"
    cell_path.write_text(json.dumps(cell_payload, ensure_ascii=False), encoding="utf-8")

    out_prefix = tmp_path / "shadow_report"

    # Mock fixtures dir to load an empty/missing or dummy fixtures directory
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    # Write a dummy fixture matching vesnianky
    dummy_fixture = {
        "slug": "vesnianky",
        "title": "Веснянки",
        "passage_md": "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни.",
        "claims": [
            {
                "claim": "Веснянки — це особливий жанр обрядових пісень, що відзначають пробудження природи та прихід весни.",
                "claim_id": "vesnianky-01",
                "is_true": True
            }
        ]
    }
    (fixtures_dir / "vesnianky.json").write_text(json.dumps(dummy_fixture, ensure_ascii=False), encoding="utf-8")

    # Run main with argparse mocks
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = argparse.Namespace(
            artifacts_dir=tmp_path,
            tau=0.75,
            out=out_prefix,
            fixtures_dir=fixtures_dir,
        )
        rc = grounding_shadow_compare.main()
        assert rc == 0

    # Verify JSON output
    json_out = Path(str(out_prefix) + ".json")
    assert json_out.exists()
    report = json.loads(json_out.read_text(encoding="utf-8"))
    assert report["metadata"]["total_groundings_checked"] == 1
    assert report["summary"]["recovered_legit"] == 0
    assert report["summary"]["regressions"] == 0

    # Verify Markdown output
    md_out = Path(str(out_prefix) + ".md")
    assert md_out.exists()
    md_text = md_out.read_text(encoding="utf-8")
    assert "# Grounding Gate Shadow Compare Report" in md_text


def test_near_copy_number_swap_rejected_at_default_tau():
    events = [_make_event(output="Сковорода народився у 1722 році")]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода народився у 1900 році"
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
    assert res.anchored is False
    assert res.reason == "digit_absent"


def test_name_swap_rejected_at_default_tau():
    events = [_make_event(output="Шевченко народився у 1722 році")]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода народився у 1722 році"
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
    assert res.anchored is False
    assert res.reason == "salient_token_absent"


def test_inflection_tolerance_at_default_tau():
    events = [_make_event(output="Григорій Сковорода народився у Львові")]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковородою народився у Львова"
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
    assert res.anchored is True


def test_single_shared_name_only():
    events = [_make_event(output="Сковорода було було було було")]
    # Excerpt has "Сковорода було було було було і Париж" where "Париж" is a second anchor, but it's not in the output
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода було було було було і Париж"
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
    assert res.anchored is False
    assert res.reason == "single_anchor"

    # But if the excerpt genuinely has only 1 anchor, we accept but set low-confidence
    grounding_single = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "Сковорода було було"
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding_single, events)
    assert res.anchored is True
    assert res.anchor_low_signal_reason == "no_digits,single_anchor"


def test_ellipsis_mass_12_to_14_still_anchors():
    events = [_make_event(output="Сковорода народився у 1722 році")]
    grounding = {
        "tool": "query_wikipedia",
        "query": "Григорій Сковорода",
        "evidence_excerpt": "народився [...] 1722"
    }
    res = grounding_gate_v2.anchor_evidence_to_events(grounding, events)
    assert res.anchored is True
    assert res.similarity == 1.0


def test_shadow_compare_harness_fp_counter(tmp_path):
    # Feeds a gold-FALSE claim which v2 anchors and asserts the FP counter reports it (NOT 0/0)
    cell_payload = {
        "schema_version": "qg_bakeoff_run.v1",
        "seat": "test-seat",
        "arm": "tooled",
        "fixture": {"slug": "vesnianky"},
        "payload": {
            "fact_checks": [
                {
                    "claim": "Веснянки — це шкідливі пісні.",
                    "grounding": {
                        "tool": "query_wikipedia",
                        "query": "Веснянки",
                        "evidence_excerpt": "Веснянки — це шкідливі пісні."
                    }
                }
            ]
        },
        "dispatch": {
            "tool_events": [
                {
                    "tool": "query_wikipedia",
                    "input": {"query": "Веснянки"},
                    "output": "Веснянки — це шкідливі пісні.",
                    "tool_call_id": "call-1",
                    "status": "completed"
                }
            ]
        }
    }

    cell_path = tmp_path / "cell_2.json"
    cell_path.write_text(json.dumps(cell_payload, ensure_ascii=False), encoding="utf-8")

    out_prefix = tmp_path / "shadow_report2"

    fixtures_dir = tmp_path / "fixtures"
    if not fixtures_dir.exists():
        fixtures_dir.mkdir()
    # Write a dummy fixture matching vesnianky but where the claim is False
    dummy_fixture = {
        "slug": "vesnianky",
        "title": "Веснянки",
        "passage_md": "Веснянки — це особливий жанр обрядових пісень. Веснянки — це шкідливі пісні.",
        "claims": [
            {
                "claim": "Веснянки — це шкідливі пісні.",
                "claim_id": "vesnianky-02",
                "is_true": False,
                "fabrication_class": "U"
            }
        ]
    }
    (fixtures_dir / "vesnianky.json").write_text(json.dumps(dummy_fixture, ensure_ascii=False), encoding="utf-8")

    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = argparse.Namespace(
            artifacts_dir=tmp_path,
            tau=0.75,
            out=out_prefix,
            fixtures_dir=fixtures_dir,
        )
        rc = grounding_shadow_compare.main()
        assert rc == 0

    # Verify JSON output
    json_out = Path(str(out_prefix) + ".json")
    assert json_out.exists()
    report = json.loads(json_out.read_text(encoding="utf-8"))

    # Assert FP counter reports it (NOT 0/0)
    assert report["summary"]["false_positives_on_fabricated"]["total_fabricated_checked"] == 1
    assert report["summary"]["false_positives_on_fabricated"]["v2_false_accepts"] == 1


def test_find_best_window_performance():
    # Make sure _find_best_window runs in well under a second for large input
    large_output = "Сковорода народився у 1722 році. " * 500
    large_excerpt = "Сковорода народився у 1722 році."
    import time
    t0 = time.perf_counter()
    score, span, _ = grounding_gate_v2._find_best_window(large_excerpt, large_output)
    t1 = time.perf_counter()
    duration = t1 - t0
    assert duration < 0.2
    assert score > 0.9
    assert span == (0, 32)

