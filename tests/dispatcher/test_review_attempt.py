"""Bound review attempts: admission, single-use identity and execution inside the attempt boundary."""

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


def test_bound_attempt_runs_only_inside_the_attempt_boundary_with_the_exact_prompt(attempt, tmp_path, monkeypatch):
    """A bound attempt is claimed, prepared and run by the runtime's boundary, and its record binds the result.

    Defect class: a bound review executes outside isolation, or with altered prompt bytes (#12114).
    """
    from types import SimpleNamespace

    from scripts.agent_runtime import attempt_boundary, review_mcp, runner
    from scripts.dispatcher import headroom

    args = cli.build_parser().parse_args(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", *attempt,
                                          "--review-access", "full"])
    binding = store.review_binding(vars(args))
    rendered = b"Rendered review prompt\nattempt: review/attempt\n"
    prompt = cli._PromptPath(tmp_path / "tasks" / "task.prompt")
    prompt.content = rendered
    workspace = tmp_path / "checkout"
    workspace.mkdir()
    spec = TaskSpec("task", "codex", "gpt-6.1-sol", "high", "read-only", workspace, prompt,
                    tmp_path / "tasks" / "task.result", options=dict(review_attempt=str(tmp_path / "manifest.yaml")))
    record = store.new_record(spec, dict(key="public", github="example/public"), "codex/task", "a" * 40,
                              dict(vars(args), research_owned_path=[]), binding=binding)
    record["review_contract"] = dict(input_root=str(tmp_path))
    path = store.create(record, rendered)

    for name in ("check_plan", "check_runtime"):
        monkeypatch.setattr(headroom, name, lambda *_a, **_k: None)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_a, **_k: None)
    monkeypatch.setattr(worker, "settle_left_worktrees", lambda *_a, **_k: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *_a: {})
    trees = []
    monkeypatch.setattr(attempt_boundary, "verify_full_review_tree", lambda *a: trees.append(a))
    receipts = tmp_path / "review-receipts" / "review"

    def prepare(review_id, attempt_id, manifest, harness, **kwargs):
        # The supervisor has claimed the attempt before preparing it on that claim.
        assert (receipts / "attempt.jsonl").read_bytes() == b"" and kwargs["claimed"] is True
        assert kwargs["receipts_root"] == tmp_path / "review-receipts" and kwargs["review_access"] == "full"
        config = receipts / "attempt.mcp.json"
        config.write_text("{}")
        (receipts / "attempt.jsonl.sha256").write_text(store.digest(b"") + "\n")  # as preparation writes it
        return review_mcp.ReviewMcpPlan(config, {}, receipts / "attempt.jsonl", receipts / "attempt.jsonl.sha256",
                                        binding["manifest_sha256"], review_id, attempt_id, harness)

    monkeypatch.setattr(review_mcp, "prepare_review_attempt", prepare)
    calls = []

    def invoke_runtime(agent, text, **kwargs):
        calls.append((agent, text, kwargs))
        return SimpleNamespace(ok=True, response="review: done\n", identity_state="unknown", observed_model=None,
                               observed_model_source=None, failure_code=None, stderr_excerpt=None)

    monkeypatch.setattr(runner, "invoke", invoke_runtime)
    worker.supervise(path, {}, 60)

    assert trees == [(tmp_path / "manifest.yaml", workspace)]
    [(agent, text, kwargs)] = calls
    assert (agent, text) == ("codex", rendered.decode())  # verbatim: no dispatch-context header
    config = kwargs["tool_config"]
    assert {key: config[key] for key in ("review_id", "attempt_id", "review_access", "review_cwd")} == dict(
        review_id="review", attempt_id="attempt", review_access="full", review_cwd=str(workspace))
    assert config["strict_mcp_config"] is True and config["mcp_server_names"] == ["sources"]
    assert (kwargs["mode"], kwargs["cwd"], kwargs["allow_runner_failover"]) == ("read-only", workspace, False)
    done = store.read("task")
    assert done["status"] == "done" and done["resolved_model_known"] is False
    assert spec.final_file.read_bytes() == b"review: done\n"
    assert done["result_sha256"] == store.digest(b"review: done\n") and done["sources_mcp_call_count"] == 0
    # The recorder's binding accepts exactly this saved result for this attempt.
    from scripts.review.record import _verify_task_return

    _verify_task_return(b"review: done\n", "task", prompt.parent, **binding)


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


def test_bound_attempt_cannot_spend_an_exhausted_branch_pr_budget(attempt, tmp_path, monkeypatch, capsys):
    """Defect class: a bound attempt is charged to a branch's ordinary PR review budget (#12216)."""
    from scripts.dispatcher import review_attempt
    from scripts.review import record_cf_verdict as recorder

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    for index in range(3):
        (tasks / f"prior-{index}.json").write_text(json.dumps(dict(
            task_id=f"prior-{index}", schema_version=2, repository="example/public", status="failed",
            mode="read-only", review_profile="infra", review_branch="review/target",
            worktree_base_sha=str(index + 1) * 40,
        )))
    before = {path.name: path.read_bytes() for path in tasks.iterdir()}
    monkeypatch.setattr(recorder, "_open_pr_number", lambda *_: None)
    budget = Mock(wraps=checks.check_review_budget)
    monkeypatch.setattr(checks, "check_review_budget", budget)
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (tmp_path / "checkout", "codex/review", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(checks, "check_branch_author_families", lambda *a: None)
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    monkeypatch.setattr(worker, "settle_left_worktrees", lambda: None)
    monkeypatch.setattr(review_attempt, "admit", lambda *a: {})
    launch = Mock()
    monkeypatch.setattr(worker, "start", launch)

    for selector in (("--branch", "review/target"), ("--pr", "42")):
        assert invoke(attempt, *selector, "--review-profile", "infra") == 2
        error = capsys.readouterr().err
        assert "review_attempt_pr_selector_unsupported" in error
        assert "docs/runbooks/formal-review-attempt-isolation.md#running-a-bound-attempt" in error
        assert "--pinned-head" in error
        budget.assert_not_called()
        launch.assert_not_called()
        git.create_worktree.assert_not_called()
        assert {path.name: path.read_bytes() for path in tasks.iterdir()} == before

    assert invoke([], "--branch", "review/target", "--review-profile", "infra") == 2
    assert "REVIEW_BUDGET_EXHAUSTED" in capsys.readouterr().err
    budget.assert_called_once()
    launch.assert_not_called()
    git.create_worktree.assert_not_called()
    assert {path.name: path.read_bytes() for path in tasks.iterdir()} == before

    budget.reset_mock()
    assert invoke(attempt, "--pinned-head", "a" * 40, "--review-profile", "infra") == 0
    budget.assert_not_called()
    launch.assert_called_once()


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
    (archive / "prior.json").write_text(json.dumps(dict(task_id="prior", schema_version=schema, status="failed", review_attempt={
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

    # A sandbox receipt must not shadow its running task in ownership lookups.
    records[0]["status"] = "running"
    (tmp_path / "first.json").write_text(json.dumps(records[0]))
    (tmp_path / "first.sandbox.json").write_text(json.dumps({"schema": 1, "task_id": "first", "status": "ran"}))
    listed = store.list_tasks(strict=True)
    assert listed == records
    assert {record["task_id"]: record for record in listed}["first"]["status"] == "running"


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


def _run_manifest_ukrainian_attempt(
    attempt, tmp_path, monkeypatch, reply: str, *, ledger_records=(), foreign_records=()
):
    from types import SimpleNamespace

    from scripts.agent_runtime import attempt_boundary, review_mcp, runner
    from scripts.dispatcher import headroom
    from scripts.review.receipts.ledger import dumps

    args = cli.build_parser().parse_args([
        "dispatch",
        "--agent",
        "agy",
        "--model",
        "gemini-3.8-flash-high",
        *attempt,
        "--review-profile",
        "ukrainian",
    ])
    binding = store.review_binding(vars(args))
    rendered = b"Rendered review prompt\nattempt: review/attempt\n"
    prompt = cli._PromptPath(tmp_path / "tasks" / "task.prompt")
    prompt.content = rendered
    workspace = tmp_path / "checkout"
    workspace.mkdir(exist_ok=True)
    spec = TaskSpec(
        "task",
        "agy",
        "gemini-3.8-flash-high",
        "high",
        "read-only",
        workspace,
        prompt,
        tmp_path / "tasks" / "task.result",
        options=dict(review_attempt=str(tmp_path / "manifest.yaml")),
    )
    record = store.new_record(
        spec,
        dict(key="public", github="example/public"),
        "agy/task",
        "a" * 40,
        dict(vars(args), research_owned_path=[]),
        binding=binding,
    )
    record["review_contract"] = dict(input_root=str(tmp_path))
    path = store.create(record, rendered)

    for name in ("check_plan", "check_runtime"):
        monkeypatch.setattr(headroom, name, lambda *_a, **_k: None)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_a, **_k: None)
    monkeypatch.setattr(worker, "settle_left_worktrees", lambda *_a, **_k: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *_a: {})
    monkeypatch.setattr(attempt_boundary, "verify_full_review_tree", lambda *a: None)
    receipts = tmp_path / "review-receipts" / "review"
    receipts.mkdir(parents=True, exist_ok=True)
    ledger_file = receipts / "attempt.jsonl"

    if foreign_records:
        foreign_receipts = tmp_path / "review-receipts" / "foreign_review"
        foreign_receipts.mkdir(parents=True, exist_ok=True)
        foreign_file = foreign_receipts / "attempt.jsonl"
        foreign_lines = b"".join(dumps(r).encode() + b"\n" for r in foreign_records)
        foreign_file.write_bytes(foreign_lines)
        (foreign_receipts / "attempt.jsonl.sha256").write_text(store.digest(foreign_lines) + "\n")

    def prepare(review_id, attempt_id, manifest, harness, **kwargs):
        config = receipts / "attempt.mcp.json"
        config.write_text("{}")
        ledger_lines = b"".join(dumps(r).encode() + b"\n" for r in ledger_records)
        ledger_file.write_bytes(ledger_lines)
        (receipts / "attempt.jsonl.sha256").write_text(store.digest(ledger_lines) + "\n")
        return review_mcp.ReviewMcpPlan(
            config,
            {},
            ledger_file,
            receipts / "attempt.jsonl.sha256",
            binding["manifest_sha256"],
            review_id,
            attempt_id,
            harness,
        )

    monkeypatch.setattr(review_mcp, "prepare_review_attempt", prepare)
    monkeypatch.setattr(review_mcp, "review_attempt_tool_config", lambda *a, **k: {})

    def invoke_runtime(agent, text, **kwargs):
        return SimpleNamespace(
            ok=True,
            response=reply,
            identity_state="observed",
            observed_model="gemini-3.8-flash-high",
            observed_model_source="provider",
            failure_code=None,
            stderr_excerpt=None,
        )

    monkeypatch.setattr(runner, "invoke", invoke_runtime)
    worker.supervise(path, {}, 60)
    done = store.read("task")
    return done, spec.final_file.read_text(), binding


def test_manifest_bound_ukrainian_review_supported_claim_accepted(attempt, tmp_path, monkeypatch):
    """A valid receipt quote in this attempt's ledger is accepted and counted in claims_total."""
    manifest_sha = store.digest(b"inputs: []\n")
    rec = {
        "receipt_id": "rr-supported1111111111",
        "review_id": "review",
        "attempt_id": "attempt",
        "manifest_sha256": manifest_sha,
        "tool": "verify_words",
        "result": "паляниця: attested in VESUM as noun",
    }
    reply = (
        "VERDICT: APPROVE\n"
        "```ukrainian-item-judgments\n"
        + json.dumps({
            "schema": "ukrainian-item-judgments.v1",
            "items": [
                {
                    "id": "card-1",
                    "verdict": "APPROVE",
                    "finding": "Attested word",
                    "sources": "VESUM",
                    "evidence": [{"receipt": "rr-supported1111111111", "quote": "attested in VESUM"}],
                }
            ],
        })
        + "\n```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec]
    )
    assert done["claims_total"] == 1
    assert done["claims_unsupported"] == 0
    assert done["unknown_items"] == 0
    assert done["dropped_claims"] == []
    assert "rr-supported1111111111" in final_text
    assert "_approval_void" not in final_text


def test_manifest_bound_ukrainian_review_fabricated_quote_dropped_and_counted(
    attempt, tmp_path, monkeypatch
):
    """A fabricated quote not present in the receipt result is dropped and counts as unsupported."""
    manifest_sha = store.digest(b"inputs: []\n")
    rec = {
        "receipt_id": "rr-supported1111111111",
        "review_id": "review",
        "attempt_id": "attempt",
        "manifest_sha256": manifest_sha,
        "tool": "verify_words",
        "result": "паляниця: attested in VESUM as noun",
    }
    reply = (
        "VERDICT: APPROVE\n"
        "```ukrainian-item-judgments\n"
        + json.dumps({
            "schema": "ukrainian-item-judgments.v1",
            "items": [
                {
                    "id": "card-1",
                    "verdict": "APPROVE",
                    "finding": "Attested word",
                    "sources": "VESUM",
                    "evidence": [{"receipt": "rr-supported1111111111", "quote": "fabricated quote never returned"}],
                }
            ],
        })
        + "\n```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec]
    )
    assert done["claims_total"] == 1
    assert done["claims_unsupported"] == 1
    assert done["unknown_items"] == 0
    assert len(done["dropped_claims"]) == 1
    assert done["dropped_claims"][0]["reason"] == "quote_not_in_result"
    assert "fabricated quote never returned" not in final_text
    assert "_approval_void" in final_text


def test_manifest_bound_ukrainian_review_foreign_attempt_receipt_dropped(attempt, tmp_path, monkeypatch):
    """A citation referencing a receipt from another attempt is dropped and counted as unsupported."""
    foreign_rec = {
        "receipt_id": "rr-foreign99999999999",
        "review_id": "other_review",
        "attempt_id": "other_attempt",
        "manifest_sha256": "f" * 64,
        "tool": "verify_words",
        "result": "some foreign result",
    }
    reply = (
        "VERDICT: APPROVE\n"
        "```ukrainian-item-judgments\n"
        + json.dumps({
            "schema": "ukrainian-item-judgments.v1",
            "items": [
                {
                    "id": "card-1",
                    "verdict": "APPROVE",
                    "finding": "Foreign citation",
                    "sources": "VESUM",
                    "evidence": [{"receipt": "rr-foreign99999999999", "quote": "some foreign result"}],
                }
            ],
        })
        + "\n```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, foreign_records=[foreign_rec]
    )
    assert done["claims_total"] == 1
    assert done["claims_unsupported"] == 1
    assert len(done["dropped_claims"]) == 1
    assert done["dropped_claims"][0]["reason"] == "foreign_attempt_receipt"
    assert "rr-foreign99999999999" not in final_text


def test_manifest_bound_ukrainian_review_unknown_item_leaves_denominator_incomplete(
    attempt, tmp_path, monkeypatch
):
    """An item marked unknown is counted in unknown_items and leaves denominator coverage incomplete."""
    from scripts.review.review_contract import build_item_packet, judge_item_reply

    reply = (
        "VERDICT: APPROVE\n"
        "```ukrainian-item-judgments\n"
        + json.dumps({
            "schema": "ukrainian-item-judgments.v1",
            "items": [
                {
                    "id": "card-1",
                    "verdict": "APPROVE",
                    "finding": "Known good",
                    "sources": "VESUM",
                },
                {
                    "id": "card-2",
                    "verdict": "unknown",
                    "finding": "Inconclusive evidence",
                    "sources": "none",
                },
            ],
        })
        + "\n```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(attempt, tmp_path, monkeypatch, reply)
    assert done["unknown_items"] == 1
    assert done["claims_total"] == 0
    assert done["claims_unsupported"] == 0

    packet = build_item_packet([{"id": "card-1", "text": "тест"}, {"id": "card-2", "text": "приклад"}])
    chunk = judge_item_reply(packet, final_text, stated="APPROVED")
    assert chunk.denominator == ("card-1", "card-2")
    assert chunk.coverage == ("card-1",)
    assert "card-2" not in chunk.coverage
