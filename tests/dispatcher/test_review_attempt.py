"""Bound review admission must preserve isolation while the v2 runtime is pending."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

import pytest

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.dispatcher.types import TaskSpec
from scripts.review.record import attested_return, dispatch_prompt_sha256


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
    launch = Mock()
    monkeypatch.setattr(worker, "start", launch)
    assert invoke(attempt, *flags) == 2
    assert "review attempt requires" in capsys.readouterr().err
    launch.assert_not_called()


def test_bound_launch_refuses_until_runtime_isolation_is_wired(attempt, monkeypatch, capsys):
    create = Mock()
    monkeypatch.setattr(git, "create_worktree", create)
    assert invoke(attempt) == 2
    assert "review_attempt_runtime_unavailable" in capsys.readouterr().err
    create.assert_not_called()


def test_dry_run_reports_binding_without_spending_attempt(attempt, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path, "codex/review", "a" * 40))
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    # The synthetic head has no Git history to read branch authorship from.
    monkeypatch.setattr(checks, "check_branch_author_families", lambda *a: None)
    for _ in range(2):
        assert invoke(attempt, "--dry-run") == 0
        plan = json.loads(capsys.readouterr().out)
        assert plan["review_attempt"] == dict(review_id="review", attempt_id="attempt",
                                             manifest_sha256=store.digest(b"inputs: []\n"))
        assert plan["review_access"] == "isolated"
    assert not (tmp_path / "tasks").exists()


@pytest.mark.parametrize("suffix", [".jsonl", ".jsonl.sha256", ".mcp.json", ".codex-home", ".agy-home"])
def test_legacy_artifact_spends_attempt_even_without_task_record(attempt, tmp_path, suffix, capsys):
    receipts = tmp_path / "review-receipts" / "review"
    receipts.mkdir(parents=True)
    (receipts / f"attempt{suffix}").symlink_to("missing")
    assert invoke(attempt, "--dry-run") == 2
    assert "already spent" in capsys.readouterr().err


@pytest.mark.parametrize("schema", [1, 2])
def test_archived_record_spends_attempt_across_manifest_changes(attempt, tmp_path, schema, capsys):
    archive = tmp_path / "tasks" / "archive"
    archive.mkdir(parents=True)
    (archive / "prior.json").write_text(json.dumps(dict(schema_version=schema, status="failed", review_attempt={
        "review_id": "review", "attempt_id": "attempt", "manifest_sha256": "b" * 64})))
    assert invoke(attempt, "--dry-run") == 2
    assert "already spent" in capsys.readouterr().err


@pytest.mark.parametrize("access", [None, "isolated", "full"])
def test_binding_snapshot_attests_v2_return_and_survives_record_corruption(attempt, tmp_path, access):
    if access:
        attempt += ["--review-access", access]
    args = cli.build_parser().parse_args(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", *attempt])
    binding = store.review_binding(vars(args))
    store.check_review_attempt(binding, claim=True)
    # Admission's snapshot must survive a subsequent manifest edit.
    (tmp_path / "manifest.yaml").write_text("changed\n")
    prompt = cli._PromptPath(tmp_path / "tasks" / "task.prompt")
    prompt.content = b"Review\n"
    spec = TaskSpec("task", "codex", "gpt-6.1-sol", None, "read-only", tmp_path, prompt, prompt.with_suffix(".result"))
    record = store.new_record(spec, dict(key="public", github="example/public"), "codex/task", "a" * 40,
                              dict(vars(args), research_owned_path=[]), binding=binding)
    store.create(record, b"Review\n")
    record = store.read("task")
    assert record["schema_version"] == 2 and record["review_attempt"] == binding
    assert binding == dict(review_id="review", attempt_id="attempt", manifest_sha256=store.digest(b"inputs: []\n"))
    assert record["prompt_sha256"] == store.digest(b"Review\n") and record["review_access"] == (access or "isolated")
    data = f"reviewer:\n  prompt_sha256: '{record['prompt_sha256']}'\n".encode()
    spec.final_file.write_bytes(data)
    record.update(status="done", result_sha256=store.digest(data))
    store.replace(record)
    assert dispatch_prompt_sha256("task", prompt.parent, **binding) == store.digest(b"Review\n")
    assert attested_return(data, task_id="task", tasks_dir=prompt.parent, manifest_path=tmp_path / "manifest.yaml",
                           root=tmp_path, **binding) == data
    store.record_path("task").write_text("{")
    with pytest.raises(ValueError, match="unreadable task record"):
        store.check_review_attempt(binding, claim=True)
    assert (tmp_path / "review-receipts/review/attempt.jsonl").is_file()


@pytest.mark.parametrize("flags", [["--review-access", "isolated"], ["--attempt-id", "attempt"],
                                  ["--review-id", "../review", "--attempt-id", "attempt", "--review-attempt", "a" * 64]])
def test_partial_or_unsafe_binding_refused_without_launch(flags, capsys):
    assert invoke(flags) == 2
    expected = "must be used together" if len(flags) == 2 else "invalid review"
    assert expected in capsys.readouterr().err


@pytest.mark.parametrize("manifest", ["a" * 64, "."])
def test_manifest_must_be_a_file(attempt, manifest, capsys):
    attempt[-1] = manifest
    assert invoke(attempt, "--dry-run") == 2
    assert "must name a manifest file" in capsys.readouterr().err


def test_strict_listing_skips_evidence_append_beside_task_records(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    records = [{"task_id": task_id, "status": "done", "result_file": None} for task_id in ("first", "second")]
    for record in records:
        (tmp_path / f"{record['task_id']}.json").write_text(json.dumps(record))
    (tmp_path / "first.evidence-append.json").write_text("[]")

    assert store.list_tasks(strict=True) == records


def test_concurrent_admissions_claim_one_pair_for_different_tasks(attempt, tmp_path, monkeypatch):
    from scripts.agent_runtime import review_mcp

    binding = dict(review_id="review", attempt_id="attempt", manifest_sha256="a" * 64)
    barrier, create = Barrier(2), review_mcp._create_file

    def exclusive(*args):
        barrier.wait(timeout=10)  # Force both admissions past the record/artifact scan.
        create(*args)

    monkeypatch.setattr(review_mcp, "_create_file", exclusive)

    def admit(task_id):
        try:
            store.check_review_attempt(binding, claim=True)
        except ValueError:
            return "spent"
        store.create(dict(task_id=task_id, prompt_file=str(tmp_path / f"{task_id}.prompt"),
                          review_attempt=binding), b"Review")
        return "admitted"

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(admit, ["first", "second"])) == ["admitted", "spent"]
    assert len(store.list_tasks()) == 1
