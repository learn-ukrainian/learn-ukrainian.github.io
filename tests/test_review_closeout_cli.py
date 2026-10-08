"""Tests for scripts/review/closeout_cli.py — the state-file-backed CLI that
wires target resolution, scope baseline, findings, and reviewer resolution
together for the local-code-review skill."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from contextlib import chdir, redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common.git_context import sanitized_git_env
from tests.project_python import project_python


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # sanitized_git_env() strips GIT_DIR/GIT_WORK_TREE/etc — without it, running
    # this suite from inside a `git commit` pre-commit hook leaks the OUTER
    # repo's git env into these calls and silently operates on the wrong repo.
    return subprocess.run(
        ["git", *args], cwd=str(repo), check=True, capture_output=True, text=True, env=sanitized_git_env(), timeout=30
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "trunk")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "app.py").write_text("print('v1')\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _run_cli(state_file: Path, *args: str, real_process: bool = False) -> subprocess.CompletedProcess[str]:
    project_root = Path(__file__).resolve().parent.parent
    command = [str(project_python()), "-m", "scripts.review.closeout_cli", "--state-file", str(state_file), *args]
    if real_process:
        return subprocess.run(command, cwd=str(project_root), capture_output=True, text=True, timeout=30)

    # Every command still enters the CLI parser and checks its own result and
    # state file. Keep a real process case below for the launch boundary.
    from scripts.review import closeout_cli

    stdout, stderr = io.StringIO(), io.StringIO()
    with chdir(project_root), redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            returncode = closeout_cli.main(["--state-file", str(state_file), *args])
        except SystemExit as exc:
            returncode = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return subprocess.CompletedProcess(command, returncode, stdout.getvalue(), stderr.getvalue())


def test_full_flow_target_freeze_expansion_cycle_reviewer_findings(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"

    target_proc = _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo))
    assert target_proc.returncode == 0, target_proc.stderr
    target_payload = json.loads(target_proc.stdout)
    assert target_payload["changed_paths"] == ["feature.py"]

    freeze_proc = _run_cli(
        state_file,
        "freeze",
        "--issue",
        "#5283",
        "--intended-behavior",
        "add feature",
        "--non-goals",
        "no refactors",
        "--owner-boundary",
        "repo root",
        "--review-profile",
        "infra",
        "--risk",
        "low",
    )
    assert freeze_proc.returncode == 0, freeze_proc.stderr
    assert "#5283" in freeze_proc.stdout

    # No further local changes yet — expansion breaker must not trigger.
    expansion_proc = _run_cli(state_file, "check-expansion", "--repo-root", str(repo))
    assert json.loads(expansion_proc.stdout)["triggered"] is False

    # Simulate review-triggered scope creep: many more files than 2x baseline.
    for i in range(5):
        (repo / f"extra{i}.py").write_text("x = 1\n" * 20, encoding="utf-8")
    expansion_proc2 = _run_cli(state_file, "check-expansion", "--repo-root", str(repo))
    result2 = json.loads(expansion_proc2.stdout)
    assert result2["triggered"] is True

    cycle_proc = _run_cli(state_file, "record-cycle", "--outstanding-count", "5")
    assert json.loads(cycle_proc.stdout)["triggered"] is False
    cycle_proc2 = _run_cli(state_file, "record-cycle", "--outstanding-count", "5")
    cycle_proc3 = _run_cli(state_file, "record-cycle", "--outstanding-count", "5")
    assert json.loads(cycle_proc3.stdout)["triggered"] is True

    reviewer_proc = _run_cli(state_file, "resolve-reviewer", "--author-model", "claude")
    assert reviewer_proc.returncode == 0, reviewer_proc.stderr
    resolution = json.loads(reviewer_proc.stdout)
    # The default OpenAI formal CF catalog seat resolves to Astra.
    assert resolution["selected"]["name"] == "openai_frontier"
    assert resolution["selected"]["concrete_model"] == "gpt-6.1-sol"
    assert resolution["selected"]["route"] == "codex"
    assert resolution["policy_version"] == "deterministic-formal-routing.v2"
    assert resolution["resolved_risk"] == "medium"

    raise_proc = _run_cli(
        state_file, "finding", "raise", "--id", "F1", "--summary", "issue", "--source", "reviewer:grok"
    )
    assert raise_proc.returncode == 0, raise_proc.stderr
    apply_before_adjudicate = _run_cli(state_file, "finding", "apply", "--id", "F1")
    assert apply_before_adjudicate.returncode != 0

    adjudicate_proc = _run_cli(
        state_file,
        "finding",
        "adjudicate",
        "--id",
        "F1",
        "--disposition",
        "in_scope_blocker",
        "--rationale",
        "real bug",
    )
    assert adjudicate_proc.returncode == 0, adjudicate_proc.stderr
    apply_proc = _run_cli(state_file, "finding", "apply", "--id", "F1")
    assert apply_proc.returncode == 0, apply_proc.stderr

    report_proc = _run_cli(state_file, "finding", "report")
    assert "F1" in report_proc.stdout
    assert "applied" in report_proc.stdout

    # State persisted across every invocation via one JSON file.
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["baseline"]["issue_ref"] == "#5283"
    assert state["cycle_outstanding_counts"] == [5, 5, 5]
    assert len(state["findings"]) == 3  # raised, adjudicated, applied


def test_resolve_reviewer_persists_resolution_to_state_file(tmp_path):
    """resolve-reviewer must write a durable receipt to --state-file, not
    just print JSON to stdout — drivers read the resolution back from disk."""
    state_file = tmp_path / "state.json"
    assert not state_file.exists()

    proc = _run_cli(
        state_file, "resolve-reviewer", "--author-model", "claude", "--owned-path", "ordinary.py", real_process=True
    )
    assert proc.returncode == 0, proc.stderr

    assert state_file.exists()
    state = json.loads(state_file.read_text(encoding="utf-8"))
    resolution = state["resolved_reviewer"]
    selected = resolution["selected"]
    assert selected["concrete_model"] == "gpt-6.1-sol"
    assert selected["family"] == "openai"
    assert selected["route"] == "codex"
    assert resolution["policy_version"] == "deterministic-formal-routing.v2"
    # On-disk receipt matches the stdout payload exactly.
    assert resolution == json.loads(proc.stdout)


def test_code_reviewer_without_target_or_owned_path_refuses_with_typed_reason(tmp_path):
    state = tmp_path / "state.json"
    proc = _run_cli(state, "resolve-reviewer", "--author-model", "gpt-6.1-sol", "--risk", "low")
    assert proc.returncode == 1
    assert json.loads(proc.stderr)["error"].startswith("review_target_required:")
    assert not state.exists()


@pytest.mark.parametrize("field", ["base_sha", "head_sha"])
def test_state_file_sha_validation_precedes_git(tmp_path, monkeypatch, field):
    repo = _init_repo(tmp_path)
    state = tmp_path / "state.json"
    assert _run_cli(state, "target", "--mode", "commit", "--commit", "HEAD", "--repo-root", str(repo)).returncode != 0
    # A commit target needs a parent; use a local target's canonical structure.
    assert _run_cli(state, "target", "--mode", "local", "--repo-root", str(repo)).returncode == 0
    record = json.loads(state.read_text())
    record["target"][field] = "--not-a-sha"
    state.write_text(json.dumps(record))

    def unexpected(*_args):
        pytest.fail("invalid state-file SHA must refuse before git")

    monkeypatch.setattr("scripts.review.closeout_cli.git_changed_paths", unexpected)
    proc = _run_cli(state, "resolve-reviewer", "--author-model", "gpt-6.1-sol")
    assert proc.returncode == 1
    assert json.loads(proc.stderr)["error"] == "target_sha_invalid"


def test_resolve_reviewer_merges_into_existing_state_file(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"

    assert _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo)).returncode == 0
    assert _run_cli(state_file, *_freeze_kwargs()).returncode == 0

    proc = _run_cli(state_file, "resolve-reviewer", "--author-model", "claude")
    assert proc.returncode == 0, proc.stderr

    state = json.loads(state_file.read_text(encoding="utf-8"))
    # Prior lifecycle state survives the merge.
    assert state["baseline"]["issue_ref"] == "#5283"
    assert state["target"]["changed_paths"] == ["feature.py"]
    assert state["resolved_reviewer"]["selected"]["concrete_model"] == "gpt-6.1-sol"


def test_resolve_reviewer_persists_fail_closed_resolution(tmp_path):
    state_file = tmp_path / "state.json"
    proc = _run_cli(state_file, "resolve-reviewer", "--author-model", "unknown-seat", "--owned-path", "ordinary.py")
    assert proc.returncode != 0

    state = json.loads(state_file.read_text(encoding="utf-8"))
    resolution = state["resolved_reviewer"]
    assert resolution["selected"] is None
    assert resolution["fail_closed_reason"] is not None


def test_resolve_reviewer_cli_rejects_invalid_risk_and_fail_closed_identity(tmp_path):
    state_file = tmp_path / "state.json"
    invalid_risk = _run_cli(
        state_file,
        "resolve-reviewer",
        "--author-model",
        "codex",
        "--risk",
        "bogus",
    )
    assert invalid_risk.returncode != 0

    unknown_author = _run_cli(
        state_file,
        "resolve-reviewer",
        "--author-model",
        "unknown-seat",
        "--owned-path",
        "ordinary.py",
    )
    assert unknown_author.returncode != 0
    assert json.loads(unknown_author.stdout)["selected"] is None


def test_resolve_reviewer_cli_selects_single_reviewer_outside_union_for_cursor_auto(tmp_path):
    state_file = tmp_path / "state.json"
    proc = _run_cli(
        state_file,
        "resolve-reviewer",
        "--author-model",
        "cursor-auto",
        "--owned-path",
        "ordinary.py",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["fail_closed_reason"] is None
    assert payload["selected"] is not None
    assert payload["selected"]["family"] not in {"xai", "moonshot"}
    assert payload["quorum"] == []


@pytest.mark.parametrize("injected_grok", [False, True])
def test_resolve_reviewer_cli_excludes_grok_for_grok_adapter_path(tmp_path, monkeypatch, injected_grok):
    from scripts.review import reviewer_resolver

    # The adapter path raises either requested risk to critical, so inject
    # Grok into the effective ladder that the resolver actually walks.
    risk = "high" if injected_grok else "medium"
    if injected_grok:
        # Subject exclusion must still refuse a caller-supplied Grok ladder;
        # automatic ladders list only the attested Cursor Grok seat (#9488).
        monkeypatch.setitem(
            reviewer_resolver.REVIEW_LADDERS,
            "critical",
            (
                *reviewer_resolver.REVIEW_LADDERS["critical"],
                (
                    reviewer_resolver.GROK_4_7,
                    reviewer_resolver.GROK_4_7_CURSOR_FALLBACK,
                ),
            ),
        )
    state_file = tmp_path / "state.json"
    proc = _run_cli(
        state_file,
        "resolve-reviewer",
        "--author-model",
        "codex:gpt-6.1-sol",
        "--domain",
        "infra",
        "--risk",
        risk,
        "--owned-path",
        "scripts/agent_runtime/adapters/grok_build.py",
        "--routing-snapshot-file",
        str(_write_claude_unhealthy_snapshot(tmp_path)),
    )
    payload = json.loads(proc.stdout)
    assert payload["resolved_risk"] == "critical"
    grok_entries = [entry for entry in payload["trace"] if entry["family"] == "xai"]
    if injected_grok:
        assert {entry["name"] for entry in grok_entries} == {"grok-4.7", "grok-4.7-cursor-fallback"}
        for grok in grok_entries:
            assert grok["status"] == "excluded"
            assert "subject exclusion" in grok["reason"]
            assert "grok_build.py" in grok["reason"]
    else:
        assert [entry["name"] for entry in grok_entries] == ["grok-4.7", "grok-4.7-cursor-fallback"]
        assert grok_entries[0]["status"] == "excluded"
        assert "subject exclusion" in grok_entries[0]["reason"]
        assert "grok_build.py" in grok_entries[0]["reason"]
    selected = payload["selected"]
    assert selected is None or selected["family"] not in {"openai", "xai"}
    assert proc.returncode == (1 if selected is None else 0)


def _write_claude_unhealthy_snapshot(tmp_path: Path) -> Path:
    path = tmp_path / "routing.json"
    path.write_text(json.dumps({"claude": "unhealthy"}), encoding="utf-8")
    return path


def test_resolve_reviewer_cli_help_documents_subject_seat():
    proc = _run_cli(Path("/tmp/unused-closeout-state.json"), "resolve-reviewer", "--help")
    assert proc.returncode == 0, proc.stderr
    help_text = proc.stdout
    assert "--subject-seat" in help_text
    assert "--subject-family" in help_text
    assert "--owned-path" in help_text
    assert "Default: none" in help_text
    assert "grok_build.py" in help_text
    assert "Outputs:" in help_text
    assert "Exit codes:" in help_text
    assert "Related:" in help_text
    assert "refusing to guess" in help_text or "fails closed" in help_text


def test_resolve_reviewer_cli_rejects_learner_semantic_profile_before_dispatch(tmp_path):
    state_file = tmp_path / "state.json"
    unsupported = _run_cli(
        state_file,
        "resolve-reviewer",
        "--author-model",
        "claude",
        "--review-profile",
        "content",
    )

    assert unsupported.returncode != 0
    payload = json.loads(unsupported.stdout)
    assert payload["selected"] is None
    assert payload["trace"] == []
    assert "unsupported local-code-review profile" in payload["fail_closed_reason"]
    assert "post-build-review" in payload["fail_closed_reason"]


def test_behavior_proof_recording_round_trips_into_receipt(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"
    assert _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo)).returncode == 0
    assert _run_cli(state_file, *_freeze_kwargs("#5302")).returncode == 0

    common = (
        "--status",
        "pass",
        "--command",
        ".venv/bin/python -m scripts.review.closeout_cli --help",
        "--cwd",
        str(repo),
        "--exit-code",
        "0",
        "--observation",
        "command completed and printed help",
        "--evidence-ref",
        "test:closeout-cli-help",
    )
    aware = _run_cli(state_file, "behavior-proof", "record", "--surface", "source_aware", *common)
    blind = _run_cli(state_file, "behavior-proof", "record", "--surface", "source_blind", *common)
    assert aware.returncode == 0, aware.stderr
    assert blind.returncode == 0, blind.stderr

    recorded = json.loads(_run_cli(state_file, "behavior-proof", "emit").stdout)
    assert recorded["schema_version"] == "behavior-proof.v1"
    assert recorded["source_aware"]["clauses"][0]["claim"] == "add feature"
    assert recorded["source_blind"]["blind_enforced"] is False

    review_file = tmp_path / "review.json"
    review_file.write_text(
        json.dumps(
            {
                "schema_version": "code-review-findings.v1",
                "overall": {"correctness": "correct", "explanation": "clean", "confidence": 0.9},
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    project_root = Path(__file__).resolve().parent.parent
    verify = subprocess.run(
        [
            str(project_python()),
            "scripts/verify_review.py",
            "--review-file",
            str(review_file),
            "--mode",
            "local",
            "--repo-root",
            str(repo),
            "--expected-input-sha256",
            recorded["source_aware"]["clauses"][0]["target_input_sha256"],
            "--issue-ref",
            "#5302",
            "--scope-json",
            '{"owner_boundary":"repo root"}',
            "--author-model",
            "author-model",
            "--author-family",
            "openai",
            "--author-harness",
            "codex",
            "--author-selection-reason",
            "implementation",
            "--reviewer-model",
            "reviewer-model",
            "--reviewer-family",
            "xai",
            "--reviewer-harness",
            "grok",
            "--reviewer-selection-reason",
            "cross-family-review",
            "--tests-json",
            '{"commands":["pytest"],"passed":true}',
            "--behavior-proof-state-file",
            str(state_file),
            "--routing-lineage-json",
            '{"implementation_agent":"test","accountable_advisor":"test"}',
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert verify.returncode == 0, verify.stderr
    receipt = json.loads(verify.stdout)
    assert receipt["behavior_proof"]["source_aware"] == recorded["source_aware"]
    assert receipt["behavior_proof"]["source_blind"]["blind_enforcement"] == "declared-blind/unenforced"


def test_behavior_proof_record_rejects_malformed_proof_and_baseline_before_mutation(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"
    assert _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo)).returncode == 0
    assert _run_cli(state_file, *_freeze_kwargs()).returncode == 0

    record_args = (
        "behavior-proof",
        "record",
        "--surface",
        "source_aware",
        "--status",
        "pass",
        "--step",
        "open the feature",
        "--result",
        "feature opened",
        "--observation",
        "visible",
        "--evidence-ref",
        "test:manual",
    )
    valid_state = json.loads(state_file.read_text(encoding="utf-8"))
    for malformed in (None, [], "not-an-object"):
        state = json.loads(json.dumps(valid_state))
        state["behavior_proof"] = malformed
        state_file.write_text(json.dumps(state), encoding="utf-8")
        before = state_file.read_bytes()
        proc = _run_cli(state_file, *record_args)
        assert proc.returncode != 0
        assert json.loads(proc.stderr)["error"] == "behavior_proof_must_be_object"
        assert state_file.read_bytes() == before

    state = json.loads(json.dumps(valid_state))
    state["target_args"] = ["not", "an", "object"]
    state_file.write_text(json.dumps(state), encoding="utf-8")
    before = state_file.read_bytes()
    proc = _run_cli(state_file, *record_args)
    assert proc.returncode != 0
    assert json.loads(proc.stderr)["error"] == "target_args_must_be_object"
    assert state_file.read_bytes() == before

    state = json.loads(json.dumps(valid_state))
    state["baseline"].pop("target")
    state_file.write_text(json.dumps(state), encoding="utf-8")
    before = state_file.read_bytes()
    proc = _run_cli(state_file, *record_args)
    assert proc.returncode != 0
    assert json.loads(proc.stderr)["error"] == "baseline_target_invalid"
    assert state_file.read_bytes() == before

    state_file.write_text(json.dumps({"baseline": {"intended_behavior": "partial"}}), encoding="utf-8")
    proc = _run_cli(state_file, *record_args)
    assert proc.returncode != 0
    assert json.loads(proc.stderr)["error"] == "baseline_issue_ref_invalid"


def test_behavior_proof_record_rejects_empty_steps_and_emit_before_record(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"
    assert _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo)).returncode == 0
    assert _run_cli(state_file, *_freeze_kwargs()).returncode == 0

    emit = _run_cli(state_file, "behavior-proof", "emit")
    assert emit.returncode != 0
    assert json.loads(emit.stderr)["error"] == "no behavior proof recorded yet"

    common = (
        "behavior-proof",
        "record",
        "--surface",
        "source_aware",
        "--status",
        "pass",
        "--result",
        "done",
        "--observation",
        "visible",
        "--evidence-ref",
        "test:manual",
    )
    for flag in ("--command", "--step"):
        proc = _run_cli(state_file, *common, flag, "   ")
        assert proc.returncode != 0
        assert json.loads(proc.stderr)["error"] == "passing proof requires --command or --step"


def test_behavior_proof_na_is_versioned_and_preserves_explicit_blind_enforcement(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"
    assert _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo)).returncode == 0
    assert _run_cli(state_file, *_freeze_kwargs()).returncode == 0

    missing_reason = _run_cli(state_file, "behavior-proof", "record", "--surface", "source_blind", "--status", "n/a")
    assert missing_reason.returncode != 0
    assert json.loads(missing_reason.stderr)["error"] == "n/a proof requires --reason"
    recorded = _run_cli(
        state_file,
        "behavior-proof",
        "record",
        "--surface",
        "source_blind",
        "--status",
        "n/a",
        "--reason",
        "no user-visible surface",
    )
    assert recorded.returncode == 0, recorded.stderr
    proof = json.loads(recorded.stdout)
    assert proof["schema_version"] == "behavior-proof.v1"
    assert "blind_enforced" not in proof["source_blind"]

    explicit = _run_cli(
        state_file,
        "behavior-proof",
        "record",
        "--surface",
        "source_blind",
        "--status",
        "n/a",
        "--reason",
        "isolation unavailable",
        "--blind-enforced",
    )
    assert explicit.returncode == 0, explicit.stderr
    assert json.loads(explicit.stdout)["source_blind"]["blind_enforced"] is True


def test_closeout_cli_invalid_json_state_is_structured(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("{not-json", encoding="utf-8")
    proc = _run_cli(state_file, "target", "--mode", "local", real_process=True)
    assert proc.returncode != 0
    assert "state_invalid_json" in json.loads(proc.stderr)["error"]


def test_check_expansion_commit_mode_measures_committed_fixes_not_clean_tree(tmp_path):
    """A commit/branch/pr-mode baseline must be re-measured against the
    committed post-fix head, not the (always-clean) local working tree.

    Before the fix, check-expansion always called resolve_local_target,
    which reads clean_tree=True/no changed_paths for *any* committed fix —
    silently hiding real scope creep that landed as a commit rather than an
    uncommitted change.
    """
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "feature.py")
    _git(repo, "commit", "-q", "-m", "feature commit")
    state_file = tmp_path / "state.json"

    target_proc = _run_cli(state_file, "target", "--mode", "commit", "--commit", "HEAD", "--repo-root", str(repo))
    assert target_proc.returncode == 0, target_proc.stderr
    assert json.loads(target_proc.stdout)["changed_paths"] == ["feature.py"]

    freeze_proc = _run_cli(
        state_file,
        "freeze",
        "--issue",
        "#5286",
        "--intended-behavior",
        "add feature",
        "--non-goals",
        "no refactors",
        "--owner-boundary",
        "repo root",
    )
    assert freeze_proc.returncode == 0, freeze_proc.stderr

    # Positive: no further commits yet — re-diffing frozen base vs current
    # HEAD (still the same commit) must not trigger.
    expansion_clean = _run_cli(state_file, "check-expansion", "--repo-root", str(repo), "--current-head", "HEAD")
    assert expansion_clean.returncode == 0, expansion_clean.stderr
    assert json.loads(expansion_clean.stdout)["triggered"] is False

    # Negative (the bug this guards): commit review-triggered scope creep,
    # leaving the working tree clean again. A resolve_local_target-based
    # check would see clean_tree=True and silently miss this.
    for i in range(5):
        (repo / f"extra{i}.py").write_text("x = 1\n" * 20, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "review-triggered fix that overshot scope")
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""  # tree is clean

    expansion_after_commit = _run_cli(state_file, "check-expansion", "--repo-root", str(repo), "--current-head", "HEAD")
    assert expansion_after_commit.returncode == 0, expansion_after_commit.stderr
    result = json.loads(expansion_after_commit.stdout)
    assert result["triggered"] is True


def test_check_expansion_non_local_mode_requires_current_head(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "feature.py")
    _git(repo, "commit", "-q", "-m", "feature commit")
    state_file = tmp_path / "state.json"

    _run_cli(state_file, "target", "--mode", "commit", "--commit", "HEAD", "--repo-root", str(repo))
    _run_cli(
        state_file,
        "freeze",
        "--issue",
        "#5286",
        "--intended-behavior",
        "add feature",
        "--non-goals",
        "no refactors",
        "--owner-boundary",
        "repo root",
    )

    proc = _run_cli(state_file, "check-expansion", "--repo-root", str(repo))
    assert proc.returncode != 0
    assert "--current-head" in proc.stderr


def test_check_expansion_before_freeze_errors(tmp_path):
    repo = _init_repo(tmp_path)
    state_file = tmp_path / "state.json"
    proc = _run_cli(state_file, "check-expansion", "--repo-root", str(repo))
    assert proc.returncode != 0
    assert "freeze" in proc.stderr


def test_freeze_before_target_errors(tmp_path):
    state_file = tmp_path / "state.json"
    proc = _run_cli(
        state_file,
        "freeze",
        "--issue",
        "#1",
        "--intended-behavior",
        "x",
        "--non-goals",
        "y",
        "--owner-boundary",
        "z",
    )
    assert proc.returncode != 0
    assert "target" in proc.stderr


def _freeze_kwargs(issue: str = "#5283") -> tuple[str, ...]:
    return (
        "freeze",
        "--issue",
        issue,
        "--intended-behavior",
        "add feature",
        "--non-goals",
        "no refactors",
        "--owner-boundary",
        "repo root",
    )


def test_target_and_freeze_are_immutable_once_baseline_frozen(tmp_path):
    """Once a baseline is frozen, `target` must reject replacing the target
    and `freeze` must reject a second call — both must fail without mutating
    the original target, baseline, cycle history, or findings. A new review
    must use a new state file instead."""
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"

    target_proc = _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo))
    assert target_proc.returncode == 0, target_proc.stderr

    freeze_proc = _run_cli(state_file, *_freeze_kwargs())
    assert freeze_proc.returncode == 0, freeze_proc.stderr

    cycle_proc = _run_cli(state_file, "record-cycle", "--outstanding-count", "3")
    assert cycle_proc.returncode == 0, cycle_proc.stderr
    raise_proc = _run_cli(state_file, "finding", "raise", "--id", "F1", "--summary", "issue", "--source", "self-review")
    assert raise_proc.returncode == 0, raise_proc.stderr

    state_before = json.loads(state_file.read_text(encoding="utf-8"))

    # Adding more files after freeze, then trying to re-target, must be rejected.
    (repo / "extra.py").write_text("x = 1\n", encoding="utf-8")
    retarget_proc = _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo))
    assert retarget_proc.returncode != 0
    assert "immutable" in retarget_proc.stderr or "already frozen" in retarget_proc.stderr

    refreeze_proc = _run_cli(state_file, *_freeze_kwargs(issue="#9999"))
    assert refreeze_proc.returncode != 0
    assert "already frozen" in refreeze_proc.stderr

    state_after = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_after == state_before
    assert state_after["target"]["changed_paths"] == ["feature.py"]
    assert state_after["baseline"]["issue_ref"] == "#5283"
    assert state_after["cycle_outstanding_counts"] == [3]
    assert len(state_after["findings"]) == 1


def test_record_cycle_rejects_negative_outstanding_count(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "feature.py").write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / "state.json"

    _run_cli(state_file, "target", "--mode", "local", "--repo-root", str(repo))
    _run_cli(state_file, *_freeze_kwargs())
    ok_proc = _run_cli(state_file, "record-cycle", "--outstanding-count", "2")
    assert ok_proc.returncode == 0, ok_proc.stderr

    state_before = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_before["cycle_outstanding_counts"] == [2]

    bad_proc = _run_cli(state_file, "record-cycle", "--outstanding-count", "-1")
    assert bad_proc.returncode != 0
    assert "outstanding-count" in bad_proc.stderr

    state_after = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_after == state_before
    assert state_after["cycle_outstanding_counts"] == [2]


# --- #9739: a committed target's reviewer is chosen from its complete authorship ------------------


def test_resolve_reviewer_excludes_every_branch_author_and_agrees_with_the_recorder(tmp_path, monkeypatch):
    from scripts.review import record_cf_verdict as recorder
    from tests.test_authoring_review_feasibility import GROK, OPUS, REPOSITORY, SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    tasks = tmp_path / "tasks"
    repo.commit(OPUS, message="first author")
    repo.commit(SOL, message="latest author")
    state = tmp_path / "state.json"
    target = _run_cli(
        state,
        "target",
        "--mode",
        "branch",
        "--branch",
        "feature",
        "--base",
        "origin/main",
        "--repo-root",
        str(repo.root),
    )
    assert target.returncode == 0, target.stderr
    common = ("--author-model", "gpt-6.1-sol", "--repository", REPOSITORY, "--task-root", str(tasks))

    medium = _run_cli(state, "resolve-reviewer", *common, "--risk", "medium")
    payload = json.loads(medium.stdout)

    # The latest author alone (GPT) would select Opus; the earlier Claude author excludes it.
    assert medium.returncode == 0, medium.stdout
    assert payload["selected"]["name"] == "grok-4.7"
    assert payload["branch_facts"]["existing_families"] == ["anthropic", "openai"]
    trace = {entry["name"]: entry["reason"] for entry in payload["trace"]}
    assert "same family as author (anthropic)" in trace["claude-opus-5-5"]
    # The recorder, from its own collection of the same Git facts, accepts that reviewer and not Opus.
    frozen = json.loads(state.read_text())["target"]
    facts = recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=frozen["base_sha"],
        head_sha=frozen["head_sha"],
        task_root=tasks,
    )
    recorder._require_qualified_reviewer(
        facts, task={"agent": "cursor", "review_risk": "medium"}, model="grok-4.7", family="xai"
    )
    with pytest.raises(recorder.RecordError, match="not qualified"):
        recorder._require_qualified_reviewer(
            facts, task={"agent": "claude", "review_risk": "medium"}, model="claude-opus-5-5", family="anthropic"
        )

    # Grok reviews at every risk (#9769); an xAI author leaves no reviewer at all.
    repo.commit(GROK, message="third author")
    retarget = _run_cli(
        state,
        "target",
        "--mode",
        "branch",
        "--branch",
        "feature",
        "--base",
        "origin/main",
        "--repo-root",
        str(repo.root),
    )
    assert retarget.returncode == 0, retarget.stderr
    critical = _run_cli(state, "resolve-reviewer", *common, "--risk", "critical")
    assert critical.returncode == 1 and json.loads(critical.stdout)["selected"] is None


def test_resolve_reviewer_fails_closed_on_an_unattributed_commit(tmp_path, monkeypatch):
    from tests.test_authoring_review_feasibility import REPOSITORY, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    repo.commit(None, message="no trailer")
    state = tmp_path / "state.json"
    _run_cli(
        state,
        "target",
        "--mode",
        "branch",
        "--branch",
        "feature",
        "--base",
        "origin/main",
        "--repo-root",
        str(repo.root),
    )

    result = _run_cli(
        state,
        "resolve-reviewer",
        "--author-model",
        "gpt-6.1-sol",
        "--repository",
        REPOSITORY,
        "--task-root",
        str(tmp_path),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["selected"] is None
    assert "branch review facts unavailable" in payload["fail_closed_reason"]
    assert "missing explicit X-Agent" in payload["fail_closed_reason"]


def _point_origin_head(repo) -> None:
    repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")


def test_resolve_reviewer_attributes_only_the_branch_after_main_is_merged(tmp_path, monkeypatch):
    """A stale frozen base plus a later main merge must not inherit main's authors (#10009)."""
    from tests.test_authoring_review_feasibility import OPUS, REPOSITORY, SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    _point_origin_head(repo)
    tasks = tmp_path / "tasks"
    repo.commit(OPUS, message="branch author")
    state = tmp_path / "state.json"
    target = _run_cli(
        state,
        "target",
        "--mode",
        "branch",
        "--branch",
        "feature",
        "--base",
        "origin/main",
        "--repo-root",
        str(repo.root),
    )
    assert target.returncode == 0, target.stderr
    frozen_base = json.loads(state.read_text(encoding="utf-8"))["target"]["base_sha"]

    repo.git("checkout", "-q", "trunk")
    squash = repo.commit(f"{OPUS}\nX-Agent: {SOL}", path="src/app.py", message="main squash")
    repo.publish("trunk", to="main")
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", "origin/main", "-m", "sync base")
    head = repo.sha("HEAD")
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["target"]["base_sha"] == frozen_base
    saved["target"]["head_sha"] = head
    state.write_text(json.dumps(saved), encoding="utf-8")

    result = _run_cli(
        state,
        "resolve-reviewer",
        "--author-model",
        "gpt-6.1-sol",
        "--repository",
        REPOSITORY,
        "--task-root",
        str(tasks),
        "--risk",
        "medium",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["branch_facts"]["existing_families"] == ["anthropic"]
    assert payload["branch_facts"]["commits"] == 2
    assert payload["selected"]["name"] == "grok-4.7"
    trace = {entry["name"]: entry["reason"] for entry in payload["trace"]}
    assert "same family as author (anthropic)" in trace["claude-opus-5-5"]
    assert squash != head


def test_resolve_reviewer_still_refuses_a_branch_whose_only_commits_came_from_main(tmp_path, monkeypatch):
    from tests.test_authoring_review_feasibility import OPUS, REPOSITORY, SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    _point_origin_head(repo)
    state = tmp_path / "state.json"
    target = _run_cli(
        state,
        "target",
        "--mode",
        "branch",
        "--branch",
        "feature",
        "--base",
        "origin/main",
        "--repo-root",
        str(repo.root),
    )
    assert target.returncode == 0, target.stderr

    repo.git("checkout", "-q", "trunk")
    squash = repo.commit(f"{OPUS}\nX-Agent: {SOL}", path="src/app.py", message="main squash")
    repo.publish("trunk", to="main")
    saved = json.loads(state.read_text(encoding="utf-8"))
    saved["target"]["head_sha"] = squash
    state.write_text(json.dumps(saved), encoding="utf-8")

    result = _run_cli(
        state,
        "resolve-reviewer",
        "--author-model",
        "gpt-6.1-sol",
        "--repository",
        REPOSITORY,
        "--task-root",
        str(tmp_path),
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["selected"] is None
    assert "branch review facts unavailable" in payload["fail_closed_reason"]
    assert "missing explicit X-Agent" in payload["fail_closed_reason"]


def test_resolve_reviewer_refuses_a_clean_main_merge_with_no_branch_commit(tmp_path, monkeypatch):
    """A no-ff base merge is not an authored commit, so reviewer selection still refuses."""
    from tests.test_authoring_review_feasibility import OPUS, REPOSITORY, SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    _point_origin_head(repo)
    state = tmp_path / "state.json"
    target = _run_cli(
        state,
        "target",
        "--mode",
        "branch",
        "--branch",
        "feature",
        "--base",
        "origin/main",
        "--repo-root",
        str(repo.root),
    )
    assert target.returncode == 0, target.stderr

    repo.git("checkout", "-q", "trunk")
    repo.commit(f"{OPUS}\nX-Agent: {SOL}", path="src/app.py", message="main squash")
    repo.publish("trunk", to="main")
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", "origin/main", "-m", "sync base")
    saved = json.loads(state.read_text(encoding="utf-8"))
    saved["target"]["head_sha"] = repo.sha("HEAD")
    state.write_text(json.dumps(saved), encoding="utf-8")

    result = _run_cli(
        state,
        "resolve-reviewer",
        "--author-model",
        "gpt-6.1-sol",
        "--repository",
        REPOSITORY,
        "--task-root",
        str(tmp_path),
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["selected"] is None
    assert "branch review facts unavailable" in payload["fail_closed_reason"]
    assert "missing explicit X-Agent" in payload["fail_closed_reason"]


@pytest.mark.parametrize("base_name,excluded", [("main", True), ("release", False)])
def test_pr_mode_target_keeps_the_base_name_for_authorship_exclusion(tmp_path, monkeypatch, base_name, excluded):
    """A frozen PR target must exclude default-branch authors, and only those."""
    from scripts.review import target_resolution as resolution
    from tests.test_authoring_review_feasibility import OPUS, REPOSITORY, SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    _point_origin_head(repo)
    tasks = tmp_path / "tasks"
    repo.commit(OPUS, message="branch author")
    payload = {
        "number": 10028,
        "baseRefName": base_name,
        "baseRefOid": repo.sha("origin/main"),
        "headRefName": "feature",
        "headRefOid": repo.sha("feature"),
    }

    def fake_run_gh(args, cwd, timeout=30.0):
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(resolution, "_run_gh", fake_run_gh)
    state = tmp_path / "state.json"
    target = _run_cli(state, "target", "--mode", "pr", "--pr", "10028", "--repo-root", str(repo.root))
    assert target.returncode == 0, target.stderr
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["target_args"]["base"] == base_name
    assert saved["target"]["base_ref_name"] == base_name
    frozen_base = saved["target"]["base_sha"]

    repo.git("checkout", "-q", "trunk")
    repo.commit(f"{OPUS}\nX-Agent: {SOL}", path="src/app.py", message="main squash")
    repo.publish("trunk", to="main")
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", "origin/main", "-m", "sync base")
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["target"]["base_sha"] == frozen_base
    assert saved["target_args"]["base"] == base_name
    saved["target"]["head_sha"] = repo.sha("HEAD")
    state.write_text(json.dumps(saved), encoding="utf-8")

    result = _run_cli(
        state,
        "resolve-reviewer",
        "--author-model",
        "gpt-6.1-sol",
        "--repository",
        REPOSITORY,
        "--task-root",
        str(tasks),
        "--risk",
        "medium",
    )
    body = json.loads(result.stdout)
    if excluded:
        assert result.returncode == 0, result.stdout + result.stderr
        assert body["branch_facts"]["existing_families"] == ["anthropic"]
        assert body["selected"]["name"] == "grok-4.7"
    else:
        assert result.returncode == 1, result.stdout + result.stderr
        assert body["selected"] is None
        assert "missing explicit X-Agent" in body["fail_closed_reason"]
