"""Hermetic contracts for module-envelope Layer-B qualification collection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import layerb_candidates, layerb_collect_emissions, layerb_qualify

ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
STUB = ROOT / "tests" / "fixtures" / "layerb" / "fake_layerb_qualification_judge.py"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _case_artifact(
    directory: Path,
    *,
    artifact_name: str,
    case_id: str,
    fixture_id: str,
    raw: str,
    fact_check_id: str,
) -> dict[str, Any]:
    event = {
        "tool": "query_wikipedia",
        "input": {"query": fixture_id},
        "output": raw,
        "status": "completed",
        "document_id": f"synthetic-{fixture_id}",
    }
    fact_check = {
        "fact_check_id": fact_check_id,
        "claim": raw,
        "verdict": "CONFIRMED",
        "grounding": {"tool": "query_wikipedia", "query": fixture_id, "evidence_excerpt": raw},
    }
    artifact = {
        "schema_version": "qg_bakeoff_run.v1",
        "fixture": {"slug": fixture_id},
        "payload": {"fact_checks": [fact_check]},
        "dispatch": {"tool_events": [event]},
    }
    candidates = layerb_candidates.materialize_candidates(fact_check["grounding"], [event]).candidates
    assert len(candidates) == 1
    candidate = candidates[0].to_dict()
    candidate["expected_source_relation"] = "ENTAILS"
    candidate["expected_support_spans"] = [{"start": 0, "end": len(raw), "role": "SUPPORTS"}]
    path = directory / artifact_name
    _write_json(path, artifact)
    artifact_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "case_id": case_id,
        "artifact_sha256": artifact_sha256,
        "fixture_id": fixture_id,
        "fact_check_id": fact_check_id,
        "fact_check_index": 0,
        "claim": raw,
        "evidence_excerpt": raw,
        "expected_reviewer_verdict": "CONFIRMED",
        "expected_layer_a_decision": "ANCHOR",
        "anchor_scan_complete": True,
        "candidate_set_complete": True,
        "candidates_by_event_output_id": {candidates[0].event_output_id: [candidate]},
        "expected_aggregate_relation": "ENTAILS",
        "expected_fact_check_decision": "ACCEPT",
        "failure_class": "ALTERED_CLAIM_VALUE",
    }


def _shared_artifact_cases(directory: Path) -> list[dict[str, Any]]:
    """Build two anchored labels that share one module artifact and raw output."""

    raw = "Іван Франко народився 1856 року."
    event = {
        "tool": "query_wikipedia",
        "input": {"query": "shared-module"},
        "output": raw,
        "status": "completed",
        "document_id": "synthetic-shared-module",
    }
    fact_checks = [
        {
            "fact_check_id": f"shared-fact-{index}",
            "claim": raw,
            "verdict": "CONFIRMED",
            "grounding": {"tool": "query_wikipedia", "query": "shared-module", "evidence_excerpt": raw},
        }
        for index in range(2)
    ]
    artifact = {
        "schema_version": "qg_bakeoff_run.v1",
        "fixture": {"slug": "shared-module"},
        "payload": {"fact_checks": fact_checks},
        "dispatch": {"tool_events": [event]},
    }
    candidate = layerb_candidates.materialize_candidates(fact_checks[0]["grounding"], [event]).candidates[0].to_dict()
    candidate["expected_source_relation"] = "ENTAILS"
    candidate["expected_support_spans"] = [{"start": 0, "end": len(raw), "role": "SUPPORTS"}]
    path = directory / "shared.json"
    _write_json(path, artifact)
    artifact_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return [
        {
            "case_id": f"openrouter-deepseek-deepseek-v4-pro__shared.json#fact_checks[{index}]::shared-{index}",
            "artifact_sha256": artifact_sha256,
            "fixture_id": "shared-module",
            "fact_check_id": fact_check["fact_check_id"],
            "fact_check_index": index,
            "claim": raw,
            "evidence_excerpt": raw,
            "expected_reviewer_verdict": "CONFIRMED",
            "expected_layer_a_decision": "ANCHOR",
            "anchor_scan_complete": True,
            "candidate_set_complete": True,
            "candidates_by_event_output_id": {candidate["event_output_id"]: [candidate]},
            "expected_aggregate_relation": "ENTAILS",
            "expected_fact_check_decision": "ACCEPT",
            "failure_class": "ALTERED_CLAIM_VALUE",
        }
        for index, fact_check in enumerate(fact_checks)
    ]


def _datasets(tmp_path: Path, *, include_gemma: bool = False) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    main_case = _case_artifact(
        tmp_path,
        artifact_name="deepseek.json",
        case_id="openrouter-deepseek-deepseek-v4-pro__main.json#fact_checks[0]::main",
        fixture_id="main-module",
        raw="Іван Франко народився 1856 року.",
        fact_check_id="main-fact",
    )
    main_cases = [main_case]
    if include_gemma:
        main_cases.append(
            _case_artifact(
                tmp_path,
                artifact_name="gemma.json",
                case_id="openrouter-google-gemma-4-31b-it__main.json#fact_checks[0]::gemma",
                fixture_id="gemma-module",
                raw="Леся Українка народилася 1871 року.",
                fact_check_id="gemma-fact",
            )
        )
    probe_case = _case_artifact(
        tmp_path,
        artifact_name="probe.json",
        case_id="adversarial-layer-b-fixture.json#fact_checks[0]::probe",
        fixture_id="probe-module",
        raw="Михайло Грушевський народився 1866 року.",
        fact_check_id="probe-fact",
    )
    main_path = tmp_path / "main-labels.json"
    probe_path = tmp_path / "probe-labels.json"
    _write_json(main_path, {"schema_version": "qg-layer-b-labels.v2", "cases": main_cases})
    _write_json(probe_path, {"schema_version": "qg-layer-b-labels.v2", "cases": [probe_case]})
    return main_path, probe_path, main_case, probe_case


def _layer_a_probes(path: Path) -> Path:
    _write_json(
        path,
        {
            "probes": [
                {
                    "id": f"layer-a-fail-closed-{index}",
                    "passed": True,
                    "serializer_window": {"candidate_id": f"layer-a-{index}", "raw_window": f"probe {index}"},
                }
                for index in range(6)
            ]
        },
    )
    return path


def _collector_args(
    main_path: Path,
    probe_path: Path,
    output_dir: Path,
    *,
    calls: int,
    family: str = "claude",
    eligibility: str = "all",
    dry_run: bool = False,
) -> list[str]:
    args = [
        "--main-labels",
        str(main_path),
        "--probe-labels",
        str(probe_path),
        "--output-dir",
        str(output_dir),
        "--judge-command",
        f"{VENV_PYTHON} {STUB}",
        "--judge-family",
        family,
        "--judge-model",
        "qualification-stub",
        "--judge-model-version",
        "qualification-stub-2026-07-12",
        "--provider-account-lane",
        "subscription:test",
        "--judge-input-usd-per-mtok",
        "1.0",
        "--judge-output-usd-per-mtok",
        "1.0",
        "--max-judge-calls",
        str(calls),
        "--eligibility",
        eligibility,
    ]
    if dry_run:
        args.append("--dry-run")
    return args


def _counter_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def test_happy_path_emission_shape_matches_scorer_response_contract(tmp_path: Path, monkeypatch) -> None:
    main_path, probe_path, main_case, _probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    output_dir = tmp_path / "collector"

    assert layerb_collect_emissions.main(_collector_args(main_path, probe_path, output_dir, calls=2)) == 0

    emission = json.loads((output_dir / "emissions.json").read_text(encoding="utf-8"))["emissions"][
        main_case["case_id"]
    ]
    candidates = layerb_qualify._candidate_rows(main_case)
    windows, _hashes, window_errors = layerb_qualify._validate_windows(candidates, emission)
    relations, response_errors = layerb_qualify._response_relations(main_case, candidates, emission, windows)

    assert not window_errors
    assert not response_errors
    assert relations == {
        candidates[0]["candidate_id"]: {
            "relation": "ENTAILS",
            "support_spans": [{"start": 0, "end": len(main_case["claim"]), "role": "SUPPORTS"}],
        }
    }
    assert _counter_lines(counter) == 2


def test_collector_emissions_round_trip_through_scorer_without_judge_or_delimiter_failures(
    tmp_path: Path, monkeypatch
) -> None:
    main_path, probe_path, _main_case, _probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    output_dir = tmp_path / "collector"
    assert layerb_collect_emissions.main(_collector_args(main_path, probe_path, output_dir, calls=2)) == 0
    calls_before_score = _counter_lines(counter)
    score_dir = tmp_path / "score"

    assert (
        layerb_qualify.main(
            [
                "--main-labels",
                str(main_path),
                "--probe-labels",
                str(probe_path),
                "--emissions",
                str(output_dir / "emissions.json"),
                "--route",
                str(output_dir / "route.json"),
                "--layer-a-probes",
                str(_layer_a_probes(tmp_path / "layer-a-probes.json")),
                "--output-dir",
                str(score_dir),
                "--max-judge-calls",
                "2",
            ]
        )
        == 0
    )
    report = json.loads((score_dir / "qualification-report.json").read_text(encoding="utf-8"))
    failures = report["thresholds"]["integrity"]["failures"]

    assert not [failure for failure in failures if failure.startswith("JUDGE_")]
    assert not [failure for failure in failures if failure.startswith("DELIMITER_INTEGRITY_FAILURE")]
    assert _counter_lines(counter) == calls_before_score


def test_one_module_envelope_covers_multiple_cases_with_one_judge_call(tmp_path: Path, monkeypatch) -> None:
    main_path, probe_path, _main_case, probe_case = _datasets(tmp_path)
    shared_cases = _shared_artifact_cases(tmp_path)
    _write_json(main_path, {"schema_version": "qg-layer-b-labels.v2", "cases": shared_cases})
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    output_dir = tmp_path / "collector"

    assert layerb_collect_emissions.main(_collector_args(main_path, probe_path, output_dir, calls=2)) == 0

    emissions = json.loads((output_dir / "emissions.json").read_text(encoding="utf-8"))["emissions"]
    assert set(emissions) == {shared_cases[0]["case_id"], shared_cases[1]["case_id"], probe_case["case_id"]}
    assert _counter_lines(counter) == 2


@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("LAYERB_STUB_RELATION", "NO_RELATION"),
        ("LAYERB_STUB_CONFIDENCE", "low"),
        ("LAYERB_STUB_SPANS", "empty"),
        ("LAYERB_STUB_SPANS", "out-of-bounds"),
        ("LAYERB_STUB_INJECTION", "true"),
    ],
)
def test_probes_first_aborts_on_bad_probe_without_running_main(
    tmp_path: Path, monkeypatch, setting: str, value: str
) -> None:
    main_path, probe_path, main_case, probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    monkeypatch.setenv(setting, value)
    output_dir = tmp_path / "collector"

    assert layerb_collect_emissions.main(_collector_args(main_path, probe_path, output_dir, calls=2)) == 2

    emissions = json.loads((output_dir / "emissions.json").read_text(encoding="utf-8"))["emissions"]
    assert probe_case["case_id"] in emissions
    assert main_case["case_id"] not in emissions
    assert _counter_lines(counter) == 1


def test_max_judge_calls_is_fail_closed_before_any_dispatch(tmp_path: Path, monkeypatch) -> None:
    main_path, probe_path, _main_case, _probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))

    assert layerb_collect_emissions.main(_collector_args(main_path, probe_path, tmp_path / "collector", calls=1)) == 2
    assert _counter_lines(counter) == 0


def test_resume_reuses_response_cache_without_repaying_for_modules(tmp_path: Path, monkeypatch) -> None:
    main_path, probe_path, _main_case, _probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    output_dir = tmp_path / "collector"
    args = _collector_args(main_path, probe_path, output_dir, calls=2)

    assert layerb_collect_emissions.main(args) == 0
    assert _counter_lines(counter) == 2
    assert layerb_collect_emissions.main([*args, "--resume"]) == 0
    assert _counter_lines(counter) == 2


def test_resume_refuses_stale_cache_request_hash(tmp_path: Path, monkeypatch) -> None:
    main_path, probe_path, _main_case, probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    output_dir = tmp_path / "collector"
    args = _collector_args(main_path, probe_path, output_dir, calls=2)

    assert layerb_collect_emissions.main(args) == 0
    for cache_path in (output_dir / "cache").glob("*.json"):
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        fact_checks = cache["response"]["fact_checks"]
        if fact_checks[0]["fact_check_id"] == probe_case["fact_check_id"]:
            cache["request_sha256"] = "0" * 64
            _write_json(cache_path, cache)
            break
    else:
        raise AssertionError("probe response cache was not written")

    assert layerb_collect_emissions.main([*args, "--resume"]) == 2
    assert _counter_lines(counter) == 2


def test_bridge_failure_emits_audited_probe_row_without_running_main(tmp_path: Path, monkeypatch) -> None:
    main_path, probe_path, main_case, probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    monkeypatch.setenv("LAYERB_STUB_EXIT", "7")
    output_dir = tmp_path / "collector"

    assert layerb_collect_emissions.main(_collector_args(main_path, probe_path, output_dir, calls=2)) == 2

    emissions = json.loads((output_dir / "emissions.json").read_text(encoding="utf-8"))["emissions"]
    assert emissions[probe_case["case_id"]]["status"] == "failure"
    assert main_case["case_id"] not in emissions
    assert _counter_lines(counter) == 1


def test_dry_run_serializes_all_windows_without_calling_judge(tmp_path: Path, monkeypatch, capsys) -> None:
    main_path, probe_path, _main_case, _probe_case = _datasets(tmp_path)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))

    assert (
        layerb_collect_emissions.main(
            _collector_args(main_path, probe_path, tmp_path / "collector", calls=2, dry_run=True)
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)

    assert summary["judge_calls_made"] == 0
    assert summary["serializer_hash_checks"] == 2
    assert _counter_lines(counter) == 0


def test_deepseek_only_filters_google_reviewer_rows_for_gemini(tmp_path: Path, monkeypatch) -> None:
    main_path, probe_path, deepseek_case, probe_case = _datasets(tmp_path, include_gemma=True)
    counter = tmp_path / "calls.log"
    monkeypatch.setenv("LAYERB_STUB_COUNTER", str(counter))
    output_dir = tmp_path / "collector"

    assert (
        layerb_collect_emissions.main(
            _collector_args(
                main_path,
                probe_path,
                output_dir,
                calls=2,
                family="gemini",
                eligibility="deepseek-only",
            )
        )
        == 0
    )
    emissions = json.loads((output_dir / "emissions.json").read_text(encoding="utf-8"))["emissions"]

    assert set(emissions) == {deepseek_case["case_id"], probe_case["case_id"]}
    assert _counter_lines(counter) == 2
