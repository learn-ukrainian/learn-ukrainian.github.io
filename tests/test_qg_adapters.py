from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from scripts.audit import qg_schema
from scripts.audit.qg_adapters import (
    DeterministicRuleAdapter,
    LlmJudgmentAdapter,
    ScorerInput,
    UaGecGoldFixtureAdapter,
    dimensions_from_findings,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_FILE = PROJECT_ROOT / "tests" / "fixtures" / "curriculum_qg" / "fixtures.yaml"


def _fixture_by_id(fixture_id: str) -> dict[str, Any]:
    payload = yaml.safe_load(FIXTURE_FILE.read_text(encoding="utf-8"))
    for fixture in payload["fixtures"]:
        if fixture["id"] == fixture_id:
            return fixture
    raise AssertionError(f"missing fixture {fixture_id}")


def _write_fixture_module(tmp_path: Path, fixture: dict[str, Any]) -> Path:
    module_dir = tmp_path / fixture["slug"]
    module_dir.mkdir()
    for name, body in fixture["module"].items():
        (module_dir / name).write_text(str(body).rstrip() + "\n", encoding="utf-8")
    return module_dir


def test_deterministic_adapter_normalizes_b1_27_fixture_findings(tmp_path: Path) -> None:
    fixture = _fixture_by_id("b1-27-restored-bad")
    module_dir = _write_fixture_module(tmp_path, fixture)

    findings = DeterministicRuleAdapter().findings(
        ScorerInput(
            module_dir=module_dir,
            level=fixture["level"],
            slug=fixture["slug"],
            fixture_id=fixture["id"],
        )
    )

    by_issue = {finding["issue_id"] for finding in findings}
    assert "AWKWARD_PASSIVE_RESULT_STATE" in by_issue
    assert "CALQUED_PREPOSITION" in by_issue
    assert all(finding["confidence"] == "deterministic" for finding in findings)
    assert all(finding["detector"]["adapter"] == "curriculum_qg_harness" for finding in findings)
    for finding in findings:
        qg_schema.validate_finding(finding)


def test_deterministic_adapter_wraps_russianism_calque_gate() -> None:
    findings = DeterministicRuleAdapter().findings(
        ScorerInput(
            text="Він буде приймати участь у вправі.",
            file="curriculum/l2-uk-en/b1/example/module.md",
        )
    )

    assert [finding["issue_id"] for finding in findings] == ["RUSSICISM_DETECTED"]
    finding = findings[0]
    qg_schema.validate_finding(finding)
    assert finding["confidence"] == "deterministic"
    assert finding["issue_class"] == "calque"
    assert finding["contact_source_lang"] == "ru"


def test_deterministic_adapter_wires_912_semantic_false_friend_linter(tmp_path: Path) -> None:
    plan_path = tmp_path / "aspect-in-imperatives.yaml"
    plan_path.write_text(
        "vocabulary_hints:\n  required:\n    - 'лук (onion) — everyday food'\n",
        encoding="utf-8",
    )

    findings = DeterministicRuleAdapter().findings(ScorerInput(plan_path=plan_path))

    assert len(findings) == 1
    finding = findings[0]
    qg_schema.validate_finding(finding)
    assert finding["issue_id"] == "SEMANTIC_FALSE_FRIEND"
    assert finding["confidence"] == "deterministic"
    assert finding["suggested_replacement"] == ["цибуля"]
    assert finding["sense_context"]["word"] == "лук"
    assert finding["line"] == 3
    assert isinstance(finding["span"]["start"], int)


def test_deterministic_adapter_ignores_missing_plan_path(tmp_path: Path) -> None:
    findings = DeterministicRuleAdapter().findings(ScorerInput(plan_path=tmp_path / "missing.yaml"))

    assert findings == []


def test_ua_gec_fixture_adapter_preserves_gold_tag_and_noisy_axis_hook() -> None:
    findings = UaGecGoldFixtureAdapter(contested_sidecar_path=Path("non-existent-sidecar.json")).findings(
        ScorerInput(fixture_id="ua-gec-gold-001")
    )

    assert len(findings) == 1
    finding = findings[0]
    qg_schema.validate_finding(finding)
    assert finding["confidence"] == "lookup_heuristic"
    assert finding["ua_gec_tag"] == "F/Calque"
    assert finding["detector"]["adapter"] == "ua_gec_gold_fixture"
    gold = finding["metadata"]["ua_gec_gold"]
    assert gold["gold_relabelled"] is False
    assert gold["contested_flag"] is None
    assert gold["contested_flag_follow_up"] == "#4364"
    assert "gold_noise" in gold["known_limitations"]


def test_ua_gec_fixture_adapter_loads_contested_sidecar(tmp_path: Path) -> None:
    sidecar_path = tmp_path / "sidecar.contested.json"
    sidecar_data = {
        "ua-gec-gold-001": {"contested": True, "evidence": []},
        "ua-gec-gold-002": {"contested": False, "evidence": []},
    }
    sidecar_path.write_text(json.dumps(sidecar_data), encoding="utf-8")

    # Load first item (contested=True)
    findings = UaGecGoldFixtureAdapter(contested_sidecar_path=sidecar_path).findings(
        ScorerInput(fixture_id="ua-gec-gold-001")
    )
    assert findings[0]["metadata"]["ua_gec_gold"]["contested_flag"] is True

    # Load second item (contested=False)
    findings = UaGecGoldFixtureAdapter(contested_sidecar_path=sidecar_path).findings(
        ScorerInput(fixture_id="ua-gec-gold-002")
    )
    assert findings[0]["metadata"]["ua_gec_gold"]["contested_flag"] is False


def test_llm_placeholder_adapter_normalizes_supplied_judgment_without_dispatch() -> None:
    findings = LlmJudgmentAdapter().findings(
        ScorerInput(
            llm_judgments=[
                {
                    "issue_id": "LLM_UNNATURAL_COLLOCATION",
                    "issue_class": "collocation",
                    "dimension": "naturalness",
                    "severity": "warning",
                    "file": "module.md",
                    "line": 7,
                    "span": {"start": 12, "end": 31},
                    "excerpt": "неприродна сполука",
                    "message": "Placeholder reviewer judgment for #4309.",
                    "contact_source_lang": "unknown",
                    "provider": "placeholder",
                    "model": "none",
                    "prompt_version": "pending-4309",
                }
            ]
        )
    )

    assert len(findings) == 1
    finding = findings[0]
    qg_schema.validate_finding(finding)
    assert finding["confidence"] == "llm_judgment"
    assert finding["detector"]["adapter"] == "llm_judgment_placeholder"
    assert finding["metadata"]["llm"]["placeholder_only"] is True


def test_three_adapter_sources_share_one_schema_record() -> None:
    deterministic = DeterministicRuleAdapter().findings(
        ScorerInput(
            text="Він буде приймати участь у вправі.",
            file="curriculum/l2-uk-en/b1/example/module.md",
        )
    )[:1]
    ua_gec = UaGecGoldFixtureAdapter().findings(ScorerInput(fixture_id="ua-gec-gold-033"))
    llm = LlmJudgmentAdapter().findings(
        ScorerInput(
            llm_judgments=[
                {
                    "issue_id": "LLM_STYLE_REVIEW",
                    "issue_class": "fluency",
                    "dimension": "naturalness",
                    "severity": "info",
                    "file": "module.md",
                    "line": None,
                    "span": None,
                    "excerpt": "стилістично сумнівний фрагмент",
                    "message": "Placeholder LLM-only judgment.",
                }
            ]
        )
    )
    findings = [*deterministic, *ua_gec, *llm]

    record = qg_schema.build_evidence_record(
        profile="curriculum_llm_compact",
        evidence_kind="fixture",
        fixture_id="adapter-compatibility",
        dimensions=dimensions_from_findings(findings),
        verdict="WARN",
        terminal_verdict="PASS",
    )

    qg_schema.validate_record(record)
    assert {finding["confidence"] for finding in findings} == {
        "deterministic",
        "lookup_heuristic",
        "llm_judgment",
    }
