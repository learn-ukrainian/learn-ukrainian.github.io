from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from scripts.audit import generate_source_inventory_review_candidates as review
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

pytestmark = pytest.mark.reads_content

FIRST_BATCH = decisions.DEFAULT_DECISION_DIR / "2026-06-29-first-approved-publish-batch.yaml"


def _first_decision() -> dict[str, object]:
    payload = yaml.safe_load(FIRST_BATCH.read_text(encoding="utf-8"))
    return payload["decisions"][0]


def _candidate_payload_for(row: dict[str, object]) -> dict[str, object]:
    source_inventory = row["source_inventory"]
    assert isinstance(source_inventory, dict)
    return {
        "generated_from": "fixture",
        "counts": {"total_delta": 1, "processed": 1, "auto_merge": 0, "needs_review": 1},
        "auto_merge": [],
        "needs_review": [
            {
                "reason": "heritage_status flags russian_shadow",
                "entry": {
                    "lemma": row["lemma"],
                    "pos": "noun",
                    "primary_source": "source_inventory_grow",
                    "source_provenance": [
                        {
                            "source_family": source_inventory["source_family"],
                            "inventory_path": source_inventory["path"],
                            "source_locator": source_inventory["locator"],
                            "source_id": source_inventory["source_id"],
                            "context": "fixture context",
                        }
                    ],
                    "enrichment": {
                        "translation": {"en": [row["approved_gloss"]]},
                        "meaning": {
                            "definitions": [
                                {"text": "dictionary definition must not replace approved gloss"}
                            ]
                        },
                    },
                },
            }
        ],
        "review_only": {"production_outputs_updated": []},
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_plan_maps_approved_decision_to_manifest_addition(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates = tmp_path / "candidates.json"
    payload = _candidate_payload_for(decision)
    payload["needs_review"][0]["entry"]["source_provenance"].append(
        {
            "source_family": "textbook",
            "inventory_path": "data/lexicon/source-inventory/other.yaml",
            "source_locator": "topic_index.other.words[0]",
            "source_id": "unapproved-duplicate-source",
            "context": "fixture duplicate context",
        }
    )
    _write_json(candidates, payload)

    plan = planner.build_promotion_plan(
        candidates_path=candidates,
        decision_files=[FIRST_BATCH],
    )

    assert plan["production_outputs_updated"] == []
    assert plan["counts"]["approved_decisions"] == 20
    assert plan["counts"]["proposed_additions"] == 1
    assert plan["counts"]["missing_candidates"] == 19
    addition = plan["proposed_manifest_additions"][0]
    assert addition["lemma"] == decision["lemma"]
    assert addition["source_inventory_key"] == decision["source_inventory"]["key"]
    assert addition["approved_pos"] == decision["approved_pos"]
    assert addition["approved_gloss"] == decision["approved_gloss"]
    assert addition["candidate_bucket"] == "needs_review"
    assert addition["manifest_entry"]["lemma"] == decision["lemma"]
    assert addition["manifest_entry"]["pos"] == decision["approved_pos"]
    assert addition["manifest_entry"]["gloss"] == decision["approved_gloss"]
    assert addition["manifest_entry"]["primary_source"] == "source_inventory_grow"
    assert addition["manifest_entry"]["course_usage"] == []
    assert len(addition["manifest_entry"]["source_provenance"]) == 1
    assert addition["manifest_entry"]["source_provenance"][0]["source_id"] == (
        decision["source_inventory"]["source_id"]
    )


def test_plan_skips_existing_lemmas_when_manifest_supplied(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates = tmp_path / "candidates.json"
    manifest = tmp_path / "manifest.json"
    _write_json(candidates, _candidate_payload_for(decision))
    _write_json(manifest, {"entries": [{"lemma": decision["lemma"]}]})

    plan = planner.build_promotion_plan(
        candidates_path=candidates,
        decision_files=[FIRST_BATCH],
        manifest_path=manifest,
    )

    assert plan["counts"]["proposed_additions"] == 0
    assert plan["counts"]["skipped_existing"] == 1
    assert plan["skipped_existing"][0]["reason"] == "already_in_manifest"


def test_candidate_matching_uses_stable_source_key_not_queue_id(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates = tmp_path / "candidates.json"
    payload = _candidate_payload_for(decision)
    payload["needs_review"][0]["entry"]["queue_id"] = "source-inventory-publish-review-9999"
    _write_json(candidates, payload)

    plan = planner.build_promotion_plan(candidates_path=candidates, decision_files=[FIRST_BATCH])

    assert plan["counts"]["proposed_additions"] == 1
    assert plan["proposed_manifest_additions"][0]["source_inventory_key"] == (
        decision["source_inventory"]["key"]
    )


@pytest.mark.parametrize(
    "bad_path",
    [
        PROJECT_ROOT / "site/src/data/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "site/public/lexicon/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "data/telemetry/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/status/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/audit/source-inventory-approved-promotion-plan.md",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/review/source-inventory-approved-promotion-plan.md",
    ],
)
def test_plan_output_rejects_repository_paths(bad_path: Path) -> None:
    with pytest.raises(SourceInventoryError):
        planner.resolve_ephemeral_plan_output_path(bad_path)


def test_write_plan_and_report_stay_ephemeral(tmp_path: Path) -> None:
    plan = {
        "workflow": planner.WORKFLOW_ID,
        "policy": "fixture",
        "production_outputs_updated": [],
        "counts": {
            "approved_decisions": 0,
            "proposed_additions": 0,
            "skipped_existing": 0,
            "missing_candidates": 0,
        },
        "proposed_manifest_additions": [],
        "skipped_existing": [],
        "missing_candidates": [],
    }

    plan_path = planner.write_plan(plan, tmp_path / "plan.json")
    report_path = planner.write_report(plan, tmp_path / "plan.md")

    assert json.loads(plan_path.read_text(encoding="utf-8"))["production_outputs_updated"] == []
    assert "Source Inventory Approved Promotion Plan" in report_path.read_text(encoding="utf-8")



def test_plan_carries_surface_admission_to_manifest_entry(tmp_path: Path) -> None:
    payload = yaml.safe_load(FIRST_BATCH.read_text(encoding="utf-8"))
    decision = payload["decisions"][0]
    payload["decisions"] = [decision]
    decision["surface_admission"] = {"daily": False, "practice": True, "cloze": False}
    decision_path = tmp_path / "decision.yaml"
    decision_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    candidates = tmp_path / "candidates.json"
    _write_json(candidates, _candidate_payload_for(decision))

    plan = planner.build_promotion_plan(candidates_path=candidates, decision_files=[decision_path])
    addition = plan["proposed_manifest_additions"][0]

    assert addition["surface_admission"] == {"daily": False, "practice": True, "cloze": False}
    assert addition["manifest_entry"]["surface_admission"] == {
        "daily": False,
        "practice": True,
        "cloze": False,
    }



def test_plan_drops_candidate_surface_admission_without_decision_opt_in(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates_payload = _candidate_payload_for(decision)
    candidates_payload["needs_review"][0]["entry"]["surface_admission"] = {
        "daily": True,
        "practice": True,
        "cloze": True,
    }
    candidates = tmp_path / "candidates.json"
    _write_json(candidates, candidates_payload)

    plan = planner.build_promotion_plan(candidates_path=candidates, decision_files=[FIRST_BATCH])
    addition = plan["proposed_manifest_additions"][0]

    assert addition["surface_admission"] == {}
    assert "surface_admission" not in addition["manifest_entry"]


@pytest.fixture
def synthetic_flow(tmp_path: Path) -> tuple[Path, Path]:
    """Synthetic candidate and approval, independent of corpus and databases."""
    inventory = {
        "path": "data/lexicon/source-inventory/synthetic.yaml",
        "locator": "items[0]", "source_id": "synthetic", "source_family": "fixture",
    }
    inventory["key"] = decisions.source_inventory_key(
        lemma="synthetic-item", inventory_path=inventory["path"], locator=inventory["locator"],
    )
    row = {
        "lemma": "synthetic-item", "decision": "approve_for_publish",
        "approved_pos": "noun", "approved_gloss": "synthetic gloss",
        "sense_note": "fixture only", "source_inventory": inventory,
        "evidence_refs": ["synthetic evidence"],
    }
    candidate = tmp_path / "synthetic-input.json"
    _write_json(candidate, _candidate_payload_for(row))
    ledger = tmp_path / "synthetic-decisions.yaml"
    ledger.write_text(yaml.safe_dump({"batch_id": "synthetic", "batch_label": "fixture", "decisions": [row]}))
    return candidate, ledger


@pytest.mark.parametrize("explicit", [False, True])
def test_api_defaults_and_overrides_preserve_all_artifact_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_flow: tuple[Path, Path], explicit: bool,
) -> None:
    source, ledger = synthetic_flow
    caller = tmp_path / "caller"
    caller.mkdir()
    monkeypatch.setenv("TMPDIR", str(caller))
    monkeypatch.setattr(review.tempfile, "gettempdir", lambda: str(tmp_path / "stale"))
    monkeypatch.setattr(review, "COMMITTED_SOURCE_INVENTORIES", ())
    monkeypatch.setattr(review, "screen_auto_merge_lemma_validity", lambda payload: [])
    monkeypatch.setattr(review.grow, "generate_candidates", lambda **kwargs: json.loads(source.read_bytes()))
    # Isolate corpus validation; real decision parsing and source-key matching still run.
    monkeypatch.setattr(decisions, "validate_committed_decision_files", lambda paths: {"files": len(paths)})
    candidate_path = tmp_path / "override-candidates.json" if explicit else caller / review.DEFAULT_OUT.name
    result = review.generate_review_candidates(**({"out": candidate_path} if explicit else {}))
    candidate_bytes = candidate_path.read_bytes()
    plan = planner.build_promotion_plan(
        decision_files=[ledger], **({"candidates_path": candidate_path} if explicit else {}),
    )
    plan_path = planner.write_plan(plan, **({"out": tmp_path / "override-plan.json"} if explicit else {}))
    report_path = planner.write_report(plan, **({"out": tmp_path / "override-report.md"} if explicit else {}))
    assert plan_path == (tmp_path / "override-plan.json" if explicit else caller / planner.DEFAULT_OUT.name)
    assert report_path == (tmp_path / "override-report.md" if explicit else caller / planner.DEFAULT_REPORT_OUT.name)
    assert plan["counts"]["proposed_additions"] == 1
    assert plan["proposed_manifest_additions"][0]["manifest_entry"]["gloss"] == "synthetic gloss"
    assert plan["production_outputs_updated"] == []
    assert candidate_path.read_bytes() == candidate_bytes
    assert json.loads(candidate_bytes) == result
    assert plan_path.read_bytes() == (json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    assert report_path.read_bytes() == (planner.format_report(plan) + "\n").encode()


@pytest.mark.parametrize("combined", [False, True])
@pytest.mark.parametrize("explicit", [False, True])
def test_synthetic_cli_candidate_to_plan_readback_across_processes(
    tmp_path: Path, synthetic_flow: tuple[Path, Path], combined: bool, explicit: bool,
) -> None:
    source, ledger = synthetic_flow
    caller = tmp_path / "caller"
    caller.mkdir()
    environment = {**os.environ, "TMPDIR": str(caller)}
    setup = """
import json
import sys
from pathlib import Path
from scripts.audit import generate_source_inventory_review_candidates as review
from scripts.audit import plan_source_inventory_promotion as planner
review.COMMITTED_SOURCE_INVENTORIES = ()
review.screen_auto_merge_lemma_validity = lambda payload: []
source = Path(sys.argv[1])
review.grow.generate_candidates = lambda **kwargs: json.loads(source.read_bytes())
planner.decisions.validate_committed_decision_files = lambda paths: {"files": len(paths)}
"""
    candidates = tmp_path / "override-candidates.json" if explicit else caller / review.DEFAULT_OUT.name
    plan_path = tmp_path / "override-plan.json" if explicit else caller / planner.DEFAULT_OUT.name
    report_path = tmp_path / "override-report.md" if explicit else caller / planner.DEFAULT_REPORT_OUT.name
    if not combined:
        writer = subprocess.run(
            [sys.executable, "-c", setup + "raise SystemExit(review.main(sys.argv[2:]))", str(source),
             *(["--out", str(candidates)] if explicit else [])],
            env=environment, capture_output=True, text=True, timeout=30, check=False,
        )
        assert writer.returncode == 0, writer.stderr
        assert candidates.exists()  # The writer has exited; the consumer has not run.
        before = candidates.read_bytes()
    planner_code = "raise SystemExit(planner.main(['--decision-file', sys.argv[2]] + sys.argv[3:]))"
    reader = subprocess.run(
        [sys.executable, "-c", setup + planner_code, str(source), str(ledger),
         *(["--generate-candidates"] if combined else []),
         *(["--candidates", str(candidates), "--out", str(plan_path), "--report-out", str(report_path)]
           if explicit else [])],
        env=environment, capture_output=True, text=True, timeout=30, check=False,
    )
    assert reader.returncode == 0, reader.stderr
    plan = json.loads(plan_path.read_bytes())
    assert plan["counts"]["proposed_additions"] == 1
    assert plan["production_outputs_updated"] == []
    assert plan["proposed_manifest_additions"][0]["lemma"] == "synthetic-item"
    assert report_path.read_bytes() == (planner.format_report(plan) + "\n").encode()
    assert plan_path.read_bytes() == (json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    if not combined:
        assert candidates.read_bytes() == before
    expected = set() if explicit else {review.DEFAULT_OUT.name, planner.DEFAULT_OUT.name, planner.DEFAULT_REPORT_OUT.name}
    assert {path.name for path in caller.iterdir()} == expected


@pytest.mark.parametrize("writer", [planner.write_plan, planner.write_report])
def test_plan_api_default_refuses_repository_tmpdir(
    monkeypatch: pytest.MonkeyPatch, writer: Callable[..., Path],
) -> None:
    monkeypatch.setenv("TMPDIR", str(PROJECT_ROOT / "site/src/data"))
    with pytest.raises(SourceInventoryError, match="must not write under"):
        writer({})


@pytest.mark.parametrize("output_flag", ["--out", "--report-out"])
def test_planner_cli_refuses_repository_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_flow: tuple[Path, Path], output_flag: str,
) -> None:
    source, ledger = synthetic_flow
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(decisions, "validate_committed_decision_files", lambda paths: {"files": len(paths)})
    assert planner.main([
        "--candidates", str(source), "--decision-file", str(ledger),
        output_flag, str(PROJECT_ROOT / "site/src/data/forbidden.json"),
    ]) == 2
