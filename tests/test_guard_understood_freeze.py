"""Load and validate the #9484 design freeze, without changing hook behavior."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

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
        assert all(record["argv"] and record["cwd"].startswith("<probe>/") for record in truth["records"])
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
        "benign_baseline": "unchanged",
        "max_implementation_review_rounds": 2,
    }
    assert manifest["residual_classes"] == [
        "operation-invisible dynamic eval",
        "sourced scripts whose operation is absent from the submitted command",
        "REST merges",
    ]
