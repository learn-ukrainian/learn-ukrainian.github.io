"""Bound review admission must preserve isolation while the v2 runtime is pending."""

import json
from unittest.mock import Mock

import pytest

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.dispatcher.types import TaskSpec


@pytest.fixture
def attempt(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("inputs: []\n")
    return ["--review-id", "review", "--attempt-id", "attempt", "--review-attempt", str(manifest)]


def invoke(attempt, *flags):
    return cli.main(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--prompt", "Review", *attempt, *flags])


@pytest.mark.parametrize("flags", [("--mode", "workspace-write"), ("--cwd", "existing")])
def test_attempt_cannot_write_or_reuse_a_worktree(attempt, monkeypatch, capsys, flags):
    """Defect class: formal binding on a write task or reused checkout defeats isolation."""
    launch = Mock()
    monkeypatch.setattr(worker, "start", launch)
    assert invoke(attempt, *flags) == 2
    assert "review attempt requires" in capsys.readouterr().err
    launch.assert_not_called()


def test_bound_launch_refuses_until_runtime_isolation_is_wired(attempt, monkeypatch, capsys):
    """Defect class: metadata alone must not authorize an unisolated paid launch."""
    create = Mock()
    monkeypatch.setattr(git, "create_worktree", create)
    assert invoke(attempt) == 2
    assert "review_attempt_runtime_unavailable" in capsys.readouterr().err
    create.assert_not_called()


def test_dry_run_reports_binding_without_spending_attempt(attempt, tmp_path, monkeypatch, capsys):
    """Defect class: planning must not reserve an id or silently drop its binding."""
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/review", "a" * 40))
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    for _ in range(2):
        assert invoke(attempt, "--dry-run") == 0
        plan = json.loads(capsys.readouterr().out)
        assert plan["review_attempt"] == dict(review_id="review", attempt_id="attempt",
                                             manifest_sha256=store.digest(b"inputs: []\n"))
        assert plan["review_access"] == "isolated"
    assert not (tmp_path / "tasks").exists()


@pytest.mark.parametrize("suffix", [".jsonl", ".jsonl.sha256", ".mcp.json", ".codex-home", ".agy-home"])
def test_legacy_artifact_spends_attempt_even_without_task_record(attempt, tmp_path, suffix, capsys):
    """Defect class: failed legacy preparation leaves spent ids without a task record."""
    receipts = tmp_path / "review-receipts" / "review"
    receipts.mkdir(parents=True)
    (receipts / f"attempt{suffix}").symlink_to("missing")
    assert invoke(attempt, "--dry-run") == 2
    assert "already spent" in capsys.readouterr().err


@pytest.mark.parametrize("schema", [1, 2])
def test_archived_record_spends_attempt_across_manifest_changes(attempt, tmp_path, schema, capsys):
    """Defect class: archival, failure or a new manifest must not permit id reuse."""
    archive = tmp_path / "tasks" / "archive"
    archive.mkdir(parents=True)
    (archive / "prior.json").write_text(json.dumps(dict(schema_version=schema, status="failed", review_attempt={
        "review_id": "review", "attempt_id": "attempt", "manifest_sha256": "b" * 64})))
    assert invoke(attempt, "--dry-run") == 2
    assert "already spent" in capsys.readouterr().err


@pytest.mark.parametrize("access", [None, "isolated", "full"])
@pytest.mark.parametrize("sha_only", [False, True])
def test_record_stores_binding_and_exact_submitted_prompt(attempt, tmp_path, access, sha_only):
    """Defect class: losing binding or hashing different prompt bytes breaks attestation."""
    if sha_only:
        attempt[-1] = store.digest(b"inputs: []\n")
    if access:
        attempt += ["--review-access", access]
    args = cli.build_parser().parse_args(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", *attempt])
    binding = store.review_binding(vars(args))
    prompt = cli._PromptPath(tmp_path / "tasks" / "task.prompt")
    prompt.content = b"Review\n"
    spec = TaskSpec("task", "codex", "gpt-6.1-sol", None, "read-only", tmp_path, prompt, tmp_path / "result")
    record = store.new_record(spec, dict(key="public", github="example/public"), "codex/task", "a" * 40,
                              dict(vars(args), research_owned_path=[]))
    store.create(record, b"Review\n")
    record = store.read("task")
    assert record["schema_version"] == 2 and record["review_attempt"] == binding
    assert binding == dict(review_id="review", attempt_id="attempt", manifest_sha256=store.digest(b"inputs: []\n"))
    assert record["prompt_sha256"] == store.digest(b"Review\n") and record["review_access"] == (access or "isolated")


@pytest.mark.parametrize("flags", [["--review-access", "isolated"], ["--attempt-id", "attempt"],
                                  ["--review-id", "../review", "--attempt-id", "attempt", "--review-attempt", "a" * 64]])
def test_partial_or_unsafe_binding_refused_without_launch(flags, capsys):
    """Defect class: partial bindings or path tokens cannot identify a unique safe attempt."""
    assert invoke(flags) == 2
    expected = "must be used together" if len(flags) == 2 else "invalid review"
    assert expected in capsys.readouterr().err
