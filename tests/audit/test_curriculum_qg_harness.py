from __future__ import annotations

import json
from pathlib import Path

from scripts.audit.curriculum_qg_harness import (
    CHECKER_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    checker_config_hash,
    main,
    run_fixtures,
    scan_curriculum_module,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_FILE = PROJECT_ROOT / "tests" / "fixtures" / "curriculum_qg" / "fixtures.yaml"
B1_27_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "b1" / "aspect-in-imperatives"


def _result_by_id(report: dict) -> dict[str, dict]:
    return {row["id"]: row for row in report["results"]}


def _write_module(root: Path, body: str) -> Path:
    module_dir = root / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(body, encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def test_curriculum_qg_fixture_suite_matches_gold_expectations() -> None:
    report = run_fixtures(FIXTURE_FILE)

    assert report["summary"] == {"total": 8, "passed": 8, "failed": 0}
    by_id = _result_by_id(report)
    assert by_id["b1-27-restored-bad"]["actual_verdict"] == "FAIL"
    assert by_id["b1-27-current-production"]["actual_verdict"] == "PASS"
    assert by_id["a1-english-scaffold-allowed"]["actual_verdict"] == "PASS"
    assert by_id["a2-english-support-warning"]["actual_verdict"] == "WARN"
    assert by_id["a1-english-led-rejected"]["actual_verdict"] == "FAIL"
    assert by_id["b1-english-led-rejected"]["actual_verdict"] == "FAIL"
    assert by_id["b1-local-english-gloss-allowed"]["actual_verdict"] == "PASS"
    assert by_id["seminar-pathos-rejected"]["actual_verdict"] == "FAIL"


def test_b1_27_restored_bad_fixture_has_gold_spanned_findings() -> None:
    report = run_fixtures(FIXTURE_FILE)
    bad = _result_by_id(report)["b1-27-restored-bad"]
    evidence = bad["evidence"]
    findings = [
        finding
        for entry in evidence["dimensions"].values()
        for finding in entry["findings"]
    ]
    by_issue = {finding["issue_id"] for finding in findings}

    assert bad["passed"] is True
    assert bad["missing_findings"] == []
    assert {
        "AWKWARD_PASSIVE_RESULT_STATE",
        "UNNATURAL_ANTHROPOMORPHISM",
        "UKRAINIAN_GRAMMAR_CALQUE",
        "UNNATURAL_META_REGISTER",
        "CALQUED_PREPOSITION",
    } <= by_issue
    assert all(finding["file"] == "module.md" for finding in findings)
    assert all(isinstance(finding["line"], int) and finding["line"] > 0 for finding in findings)
    assert all(isinstance(finding["span"]["start"], int) for finding in findings)
    assert all(isinstance(finding["span"]["end"], int) for finding in findings)


def test_current_b1_27_scans_as_pass_with_compact_evidence_shape() -> None:
    module_text = (B1_27_DIR / "module.md").read_text(encoding="utf-8")

    assert module_text.strip()
    assert "Відкрийте застосунок" in module_text

    evidence = scan_curriculum_module(
        B1_27_DIR,
        level="b1",
        slug="aspect-in-imperatives",
    )

    assert evidence["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert evidence["checker_config"]["version"] == CHECKER_VERSION
    assert evidence["checker_config"]["config_hash"] == checker_config_hash()
    assert evidence["module_id"] == "b1/aspect-in-imperatives"
    assert evidence["verdict"] == "PASS"
    assert evidence["terminal_verdict"] == "PASS"
    assert evidence["llm_review"]["used"] is False
    assert evidence["llm_review"]["required"] is False
    assert evidence["dimensions"]["ukrainian_style"]["findings"] == []


def test_module_cli_warn_uses_terminal_verdict_for_exit_code(tmp_path: Path) -> None:
    module_dir = _write_module(
        tmp_path,
        "# Grammar Basics\n\n"
        "This section explains the grammar before Ukrainian examples appear in the lesson body.\n\n"
        "**Ми читаємо.**\n",
    )
    output = tmp_path / "evidence.json"

    code = main(
        [
            "--module-dir",
            str(module_dir),
            "--level",
            "a2",
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["verdict"] == "WARN"
    assert payload["terminal_verdict"] == "PASS"
