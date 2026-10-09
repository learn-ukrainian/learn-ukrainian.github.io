"""Load and validate the #9484 design freeze, without changing hook behavior."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"
MANIFEST = ROOT / "docs/design/guard-hooks-understood-forms.manifest.json"


def test_frozen_artifact_digests_and_legacy_prefix() -> None:
    manifest = json.loads(MANIFEST.read_text())
    for relative, digest in manifest["sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    oracle = json.loads((FIXTURES / "guard_bash_oracle.json").read_text())
    prefix = oracle["rows"][: oracle["legacy_row_count"]]
    canonical = json.dumps(prefix, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == manifest["legacy_rows_canonical_sha256"]
    assert len(prefix) == 605
    round1 = json.dumps(oracle["rows"][:1082], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(round1).hexdigest() == manifest["round1_rows_canonical_sha256"]
    assert len(json.loads((FIXTURES / "guard_bash_traffic.json").read_text())) == 400


def test_frozen_dispositions_have_hooks_and_recorded_ground_truth() -> None:
    oracle = json.loads((FIXTURES / "guard_bash_oracle.json").read_text())
    manifest = json.loads(MANIFEST.read_text())
    rows = oracle["rows"][oracle["legacy_row_count"] :]
    assert len({row["id"] for row in oracle["rows"]}) == len(oracle["rows"])
    assert dict(Counter(row["family"] for row in rows)) == manifest["new_oracle_families"]
    for row in rows:
        expected = row["expected"]
        assert row["hooks"] == [row["hook"]]
        assert row["hook"] in {"branch", "merge", "admin"}
        assert expected["disposition"] in {"allow", "block", "refuse"}
        assert (expected["reason_class"] is not None) == (expected["disposition"] == "refuse")
        truth = row["bash_truth"]
        assert truth["method"] == "real-bash-recording-git-gh"
        assert isinstance(truth["operation_seen"], bool)
        assert isinstance(truth["returncode"], int), row["id"]
        assert all(
            record["argv"] and (record["cwd"] == "<probe>" or record["cwd"].startswith("<probe>/"))
            for record in truth["records"]
        ), row["id"]
    limited = [row["id"] for row in rows if row["bash_truth"]["limitation"]]
    assert limited == manifest["ground_truth_limitations"]


def test_inspection_traffic_is_frozen_for_all_three_hooks() -> None:
    traffic = json.loads((FIXTURES / "guard_bash_understood_traffic.json").read_text())
    rows = traffic["rows"]
    assert len(rows) == len({row["command"] for row in rows}) == 60
    assert all(row["hooks"] == ["branch", "merge", "admin"] for row in rows)
    assert all(row["expected"] == {"disposition": "allow", "reason_class": None} for row in rows)
    assert {row["command"].split()[0] for row in rows} == {"grep", "rg", "git", "echo", "printf", "cat", "jq", "sed"}
    assert all(not row["bash_truth"]["limitation"] for row in rows)


def test_branch_policy_corrections_and_six_form_failure_edges() -> None:
    oracle = json.loads((FIXTURES / "guard_bash_oracle.json").read_text())
    rows = oracle["rows"][oracle["legacy_row_count"] :]
    corrections = [row for row in rows if row["family"] == "branch-policy-correction"]
    assert {row["command"] for row in corrections} == {
        "git checkout main",
        "git checkout -- file",
        "git branch -d merged",
        "git branch --list",
    }
    assert all(row["expected"]["disposition"] == "allow" for row in corrections)
    forms = {row["command"]: row for row in rows if row["family"] == "six-benign"}
    stopped = forms["cd missing || exit; git checkout -b f"]
    assert stopped["expected"]["disposition"] == "allow"
    assert not stopped["bash_truth"]["operation_seen"]
    for command in (
        "if cd missing; then :; fi; git checkout -b f",
        "f(){ cd missing; }; f; git checkout -b f",
    ):
        row = forms[command]
        assert row["expected"]["disposition"] == "refuse"
        assert row["bash_truth"]["operation_seen"]
        assert row["bash_truth"]["operation_contexts"] == ["<probe>/primary"]
    missing = forms["cd missing && git checkout -b evil"]
    assert missing["expected"]["disposition"] == "refuse"
    assert not missing["bash_truth"]["operation_seen"]
    assert forms["while false; do git checkout -b evil; done"]["expected"]["disposition"] == "allow"
    assert forms["git checkout -b followup"]["expected"]["disposition"] == "allow"
    appended = {row.get("supersedes"): row for row in rows if row.get("supersedes")}
    for prior in ("freeze-six-benign-003", "freeze-six-benign-005"):
        assert appended[prior]["expected"]["disposition"] == "block"
        assert appended[prior]["addition_reason"]
        assert appended[prior]["bash_truth"]["operation_contexts"] == ["<probe>/primary"]


def test_intentional_refusal_repair_and_acceptance_terms() -> None:
    manifest = json.loads(MANIFEST.read_text())
    spec = (ROOT / "docs/design/guard-hooks-understood-forms.md").read_text()
    assert "Run the git command directly in the verified worktree" in spec
    assert manifest["acceptance"] == {
        "unsafe_allows": 0,
        "wrong_context_judgments": 0,
        "max_oracle_overblocks": 4,
        "legacy_traffic_blocks": 0,
        "inspection_traffic_blocks": 0,
        "everyday_traffic_blocks": 0,
        "benign_baseline": "unchanged",
        "max_implementation_review_rounds": 2,
    }
    assert manifest["residual_classes"] == [
        "operation-invisible dynamic eval",
        "sourced scripts whose operation is absent from the submitted command",
        "REST merges",
    ]


def _oracle_module():
    spec = importlib.util.spec_from_file_location("freeze_b_oracle", ROOT / "scripts/hooks/bash_oracle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_round2_denominator_covers_everyday_traffic_and_all_hook_misparses() -> None:
    rows = json.loads((FIXTURES / "guard_bash_oracle.json").read_text())["rows"][1082:]
    traffic = [row for row in rows if row["family"] == "everyday-traffic"]
    assert len({row["command"] for row in traffic}) == 66
    assert len(traffic) == 198
    assert all(row["expected"]["disposition"] == "allow" for row in traffic)
    assert Counter(row["hook"] for row in traffic) == {"branch": 66, "merge": 66, "admin": 66}
    misparses = [row for row in rows if row["family"] == "condition9-misparse"]
    assert Counter(row["hook"] for row in misparses) == {"branch": 7, "merge": 7, "admin": 7}
    assert all(row["bash_truth"]["operation_seen"] for row in misparses)
    executors = [row for row in rows if row["family"] == "heldout-executors"]
    assert len(executors) == 15
    assert all(row["bash_truth"]["operation_seen"] for row in executors)
    assert all(row["expected"]["reason_class"] == "UNKNOWN_EXECUTOR" for row in executors)


@pytest.mark.parametrize(
    ("pr", "repo", "repository", "number"),
    [
        ("5", None, "github.com/fixture/default", "5"),
        ("7", "fixture/other", "github.com/fixture/other", "7"),
        ("5", "forge.example.invalid/fixture/other", "forge.example.invalid/fixture/other", "5"),
        ("https://forge.example.invalid/fixture/other/pull/5", None, "forge.example.invalid/fixture/other", "5"),
        ("https://github.com/fixture/other/pull/5", "fixture/wrong", "github.com/fixture/wrong", "5"),
    ],
)
def test_oracle_target_identity_is_independent_of_hook_parser(pr, repo, repository, number) -> None:
    oracle = _oracle_module()
    with patch.dict("os.environ", {"GH_REPO": "fixture/default"}):
        assert oracle.target_identity(pr, repo) == {"repository": repository, "pr": number}


@pytest.mark.parametrize("mutation", ["pr", "repository", "host", "omission", "admin-pr"])
def test_oracle_rejects_wrong_target_even_when_hook_exits_two(mutation) -> None:
    oracle = _oracle_module()
    rows = json.loads((FIXTURES / "guard_bash_oracle.json").read_text())["rows"]
    row = next(row for row in rows if row["id"] == "freeze-b-target-identity-005")
    if mutation != "admin-pr":
        row = next(row for row in rows if row["id"] == "freeze-b-target-identity-004")
    original_load = oracle.load_hook

    def mutant(name):
        module = original_load(name)
        if name == "guard-pr-merge":
            if mutation == "pr":
                module._pr_ref = lambda *args, **kwargs: "7"
            elif mutation in {"repository", "host"}:
                wrong = "fixture/wrong" if mutation == "repository" else "forge.example.invalid/fixture/other"
                module._repo_option = lambda *args: wrong
            elif mutation == "omission":
                module.read_commands = lambda *args, **kwargs: []
            # Force exit 2 despite the wrong lookup: equal exit codes do not
            # certify target equality, and generic refusal cannot mask it.
            original_main = module.main
            module.main = lambda: (original_main(), 2)[1]
        elif name == "guard-admin-merge" and mutation == "admin-pr":
            module._pr_number = lambda *args: "7"
        return module

    with patch.object(oracle, "load_hook", mutant):
        report = oracle.run_oracle(rows=[row], traffic=[])
    assert report["totals"]["misses"] == 1
    assert report["totals"]["expected_mismatches"] == 1
    assert report["totals"]["missing_target_judgments" if mutation == "omission" else "wrong_target_judgments"] == 1


def test_oracle_correct_merge_target_is_the_only_red_identity() -> None:
    oracle = _oracle_module()
    rows = json.loads((FIXTURES / "guard_bash_oracle.json").read_text())["rows"]
    row = next(row for row in rows if row["id"] == "freeze-b-target-identity-004")
    report = oracle.run_oracle(rows=[row], traffic=[])
    assert report["totals"]["expected_matches"] == 1
    assert report["totals"]["wrong_target_judgments"] == 0
    assert report["observations"][0]["targets"][0]["repository"] == "github.com/fixture/other"


def test_oracle_target_cwd_follows_execution_and_rejects_stale_initial_cwd() -> None:
    oracle = _oracle_module()
    row = {
        "id": "target-cwd-probe",
        "family": "test-only",
        "hook": "merge",
        "accepted": False,
        "command": "cd ../.. && gh pr merge 5 -R fixture/other",
        "cwd": "worktree",
        "expected": {"disposition": "block", "target": {"repository": "github.com/fixture/other", "pr": "5"}},
    }
    report = oracle.run_oracle(rows=[row], traffic=[])
    assert report["totals"]["expected_matches"] == 1
    original_load = oracle.load_hook

    def mutant(name):
        module = original_load(name)
        if name == "guard-pr-merge":
            from dataclasses import replace

            original_read = module.read_commands
            module.read_commands = lambda command, cwd=None, **kwargs: [
                replace(inv, cwd=cwd) for inv in original_read(command, cwd=cwd, **kwargs)
            ]
        return module

    with patch.object(oracle, "load_hook", mutant):
        report = oracle.run_oracle(rows=[row], traffic=[])
    assert report["totals"]["wrong_target_judgments"] == 1


def test_oracle_allowed_branches_and_intentional_refusals_use_frozen_dispositions():
    oracle = _oracle_module()
    rows = json.loads((FIXTURES / "guard_bash_oracle.json").read_text())["rows"]
    selected = [
        row
        for row in rows
        if row["id"]
        in {
            "freeze-branch-policy-correction-000",
            "freeze-intentional-refusal-000",
        }
    ]
    report = oracle.run_oracle(rows=selected, traffic=[])
    assert report["totals"]["expected_matches"] == len(selected) == 2
    assert report["totals"]["misses"] == report["totals"]["overblocks"] == 0
