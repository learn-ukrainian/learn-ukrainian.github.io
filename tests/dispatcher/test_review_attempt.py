"""Bound review attempts: admission, single-use identity and execution inside the attempt boundary."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

import pytest

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.dispatcher.types import TaskSpec
from scripts.review.record import attested_return, dispatch_prompt_sha256
from scripts.review.render_contract import trusted_core_context


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


@pytest.mark.parametrize("path_status", ["done", "failed", "timeout", "cancelled", "overcap"])
@pytest.mark.parametrize("harness", ["codex", "claude", "agy"])
def test_bound_attempt_runs_only_inside_the_attempt_boundary_with_the_exact_prompt(
    attempt, tmp_path, monkeypatch, path_status, harness,
):
    """A bound attempt is claimed, prepared and run by the runtime's boundary, and its record binds the result.

    Defect class: a bound review loses egress evidence on success, provider failure, timeout or cancellation (#12947).
    """
    import os
    import socket
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace

    from scripts.agent_runtime import attempt_boundary, review_mcp, runner
    from scripts.agent_runtime.attempt_network import MAX_EGRESS_DESTINATIONS, AttemptEgress
    from scripts.agent_runtime.errors import AgentTimeoutError, AgentUnavailableError
    from scripts.dispatcher import headroom
    from scripts.review.render_contract import trusted_core_context

    args = cli.build_parser().parse_args(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", *attempt,
                                          "--review-access", "full"])
    binding = store.review_binding(vars(args))
    prefix, dependency = trusted_core_context()
    rendered = (prefix + "Rendered review prompt\nattempt: review/attempt\n").encode()
    prompt = cli._PromptPath(tmp_path / "tasks" / "task.prompt")
    prompt.content = rendered
    workspace = tmp_path / "checkout"
    workspace.mkdir()
    spec = TaskSpec("task", harness, "gpt-6.1-sol", "high", "read-only", workspace, prompt,
                    tmp_path / "tasks" / "task.result", options=dict(review_attempt=str(tmp_path / "manifest.yaml")))
    record = store.new_record(spec, dict(key="public", github="example/public"), "codex/task", "a" * 40,
                              dict(vars(args), research_owned_path=[]), binding=binding)
    record["review_contract"] = dict(input_root=str(tmp_path), machinery_dependencies={"rules_core": dependency},
                                     prompt_sha256=store.digest(rendered))
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

    boundaries = []

    def prepare_boundary(agent, mode, session_id, config):
        # Real proxy + real cleanup; only the provider and OS launch are planted.
        boundary = object.__new__(attempt_boundary.AttemptBoundary)
        boundary.temp = tempfile.TemporaryDirectory(prefix="eg-", dir=tmp_path)
        boundary.workspace = workspace
        boundary.connection = None
        boundary.egress_evidence = {}
        # AF_UNIX paths must stay below the kernel's small length limit.
        boundary.egress = AttemptEgress(Path(boundary.temp.name) / "egress.sock")
        boundary.tool_config = config
        boundaries.append(boundary)
        return boundary

    def invoke_runtime(agent, text, **kwargs):
        calls.append((agent, text, kwargs))
        proxy = boundaries[-1].egress

        async def refuse_dns(host):
            raise ValueError("planted DNS failure")

        monkeypatch.setattr(proxy, "_resolve", refuse_dns)
        hosts = ["audit.example"]
        if path_status == "overcap":
            hosts = [f"audit-{index}.example" for index in range(MAX_EGRESS_DESTINATIONS + 3)]
            hosts += ["audit-0.example", f"audit-{MAX_EGRESS_DESTINATIONS}.example"]
        for host in hosts:
            with socket.socket(socket.AF_UNIX) as client:
                client.settimeout(5)
                directory = os.open(proxy.endpoint.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    client.connect(f"/proc/self/fd/{directory}/{proxy.endpoint.name}")
                finally:
                    os.close(directory)
                client.sendall(f"CONNECT {host}:443 HTTP/1.1\r\n\r\n".encode())
                assert client.recv(1024).startswith(b"HTTP/1.1 403")
        if path_status == "failed":
            raise AgentUnavailableError("planted provider failure")
        if path_status == "timeout":
            raise AgentTimeoutError(agent, 60)
        if path_status == "cancelled":
            import signal

            os.kill(os.getpid(), signal.SIGTERM)
            raise AssertionError("supervisor cancellation must unwind")
        return SimpleNamespace(ok=True, response="review: done\n", identity_state="unknown", observed_model=None,
                               observed_model_source=None, failure_code=None, stderr_excerpt=None)

    monkeypatch.setattr(attempt_boundary, "prepare_attempt_boundary", prepare_boundary)
    monkeypatch.setattr(runner, "prepare_trail_isolation", lambda **kwargs: None)
    monkeypatch.setattr(runner, "_invoke_impl", invoke_runtime)
    worker.supervise(path, {}, 60)

    assert trees == [(tmp_path / "manifest.yaml", workspace)]
    [(agent, text, kwargs)] = calls
    assert (agent, text) == (harness, rendered.decode())
    assert kwargs["rules_core_delivery"] is runner.RulesCoreDelivery.BOUND
    config = kwargs["tool_config"]
    assert {key: config[key] for key in ("review_id", "attempt_id", "review_access", "review_cwd")} == dict(
        review_id="review", attempt_id="attempt", review_access="full", review_cwd=str(workspace))
    assert config["strict_mcp_config"] is True and config["mcp_server_names"] == ["sources"]
    assert (kwargs["mode"], kwargs["cwd"], kwargs["allow_runner_failover"]) == ("read-only", workspace, False)
    done = store.read("task")
    assert done["status"] == ("done" if path_status == "overcap" else path_status), done.get("error")
    expected_records = [{"destination": "audit.example:443", "bytes": 0}]
    if path_status == "overcap":
        expected_records = [{"destination": f"audit-{index}.example:443", "bytes": 0}
                            for index in range(MAX_EGRESS_DESTINATIONS)]
    assert done["review_attempt_egress"] == {
        "records": expected_records, "overflow_count": 4 if path_status == "overcap" else 0,
    }
    assert not boundaries[0].egress.thread.is_alive()
    assert not Path(boundaries[0].temp.name).exists()
    print(json.dumps({"task_record": done}, sort_keys=True))
    if path_status in {"done", "overcap"}:
        assert done["resolved_model_known"] is False
        assert spec.final_file.read_bytes() == b"review: done\n"
        assert done["result_sha256"] == store.digest(b"review: done\n") and done["sources_mcp_call_count"] == 0
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


def test_lexical_render_admission_rejects_tampering(tmp_path, monkeypatch):
    """Defect class: lexical admission refuses valid renders or accepts altered prompts/identity/schema."""
    import subprocess
    from functools import partial
    from pathlib import Path

    from scripts.agent_runtime import attempt_boundary, review_mcp
    from scripts.dispatcher import review_attempt
    from scripts.review.prompts.render import render_prompt
    from tests.review.test_prompts import _setup_lexical_fixture

    manifest_path, manifest, _ = _setup_lexical_fixture(tmp_path)
    prompt_file = tmp_path / "lexical.prompt"
    prompt, _, _ = render_prompt(manifest_path, repo_root=tmp_path, output_path=prompt_file,
                                 review_id="review", attempt_id="attempt", review_access="isolated")
    args = cli.build_parser().parse_args([
        "dispatch", "--agent", "agy", "--model", "gemini-3.8-flash-high", "--effort", "high",
        "--mode", "read-only", "--review-profile", "ukrainian", "--review-author-model", "gpt-6.1-sol",
        "--review-id", "review", "--attempt-id", "attempt", "--review-attempt", str(manifest_path),
        "--prompt-file", str(prompt_file), "--review-access", "isolated",
    ])
    binding = store.review_binding(vars(args))
    for command in (["git", "init", "-q"], ["git", "add", manifest["inputs"]["candidates"]["path"]],
                    ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                     "commit", "-qm", "Public candidate fixture"]):
        subprocess.run(command, cwd=tmp_path, check=True, capture_output=True, timeout=30)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, timeout=30).decode().strip()
    # Exercise the real server contract against the checkout containing this change.
    checkout = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(review_mcp, "check_review_contract",
                        partial(review_mcp.check_review_contract, server_checkout=checkout))
    contract = review_attempt.admit(args, prompt.encode(), binding, tmp_path, sha)
    assert contract["templates"] == ["lexical-review.md.j2"]
    assert attempt_boundary.authorized_closure(manifest, tmp_path) == {
        manifest["inputs"]["candidates"]["path"]: (tmp_path / manifest["inputs"]["candidates"]["path"]).read_bytes()
    }
    with pytest.raises(ValueError, match="review_render_record_stale"):
        review_attempt.admit(args, (prompt + "altered").encode(), binding, tmp_path, sha)
    for name, invalid in (("review_profile", "code"), ("review_author_model", None), ("effort", "low"),
                          ("output_schema", "override.json")):
        original = getattr(args, name)
        setattr(args, name, invalid)
        reason = "attempt_output_schema_unsupported" if name == "output_schema" else "lexical_review_identity_required"
        with pytest.raises(ValueError, match=reason):
            review_attempt.admit(args, prompt.encode(), binding, tmp_path, sha)
        setattr(args, name, original)


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
    monkeypatch.setattr(git, "review_branch_start", lambda *a, **k: "a" * 40)
    monkeypatch.setattr(git, "worktree_plan", lambda *a, **k: (tmp_path / "checkout", "codex/review", "a" * 40))
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
    prefix, dependency = trusted_core_context()
    rendered = (prefix + "Rendered review prompt\nattempt: review/attempt\n").encode()
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
    record["review_contract"] = dict(input_root=str(tmp_path), machinery_dependencies={"rules_core": dependency},
                                     prompt_sha256=store.digest(rendered))
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
        "arguments": {"words": ["паляниця"]},
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
    assert done["claims_total"] == 2
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
        "arguments": {"words": ["паляниця"]},
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
    assert done["claims_total"] == 2
    assert done["claims_unsupported"] == 2
    assert done["unknown_items"] == 0
    assert len(done["dropped_claims"]) == 2
    assert done["dropped_claims"][1]["claim"] == {"sources": "VESUM"}
    assert done["dropped_claims"][1]["reason"] == "claim_not_in_captured_output"
    assert done["dropped_claims"][1]["captured_event_ids"] == []
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
        "arguments": {"words": ["паляниця"]},
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
    assert done["claims_total"] == 2
    assert done["claims_unsupported"] == 2
    assert len(done["dropped_claims"]) == 2
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
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply,
        ledger_records=[{
            "receipt_id": "rr-known", "review_id": "review", "attempt_id": "attempt",
            "manifest_sha256": store.digest(b"inputs: []\n"),
            "tool": "verify_words", "arguments": {"words": ["тест"]}, "result": "VESUM: тест",
        }],
    )
    assert done["unknown_items"] == 1
    assert done["claims_total"] == 1
    assert done["claims_unsupported"] == 0

    packet = build_item_packet([{"id": "card-1", "text": "тест"}, {"id": "card-2", "text": "приклад"}])
    chunk = judge_item_reply(packet, final_text, stated="APPROVED", ukrainian=True)
    assert chunk.denominator == ("card-1", "card-2")
    assert chunk.coverage == ("card-1",)
    assert "card-2" not in chunk.coverage


def test_manifest_bound_ukrainian_review_yaml_fabricated_quote_dropped_and_counted(
    attempt, tmp_path, monkeypatch
):
    """A YAML return with fabricated quote is validated, dropped, and counted in claims_unsupported."""
    import yaml

    manifest_sha = store.digest(b"inputs: []\n")
    rec = {
        "receipt_id": "rr-supported1111111111",
        "review_id": "review",
        "attempt_id": "attempt",
        "manifest_sha256": manifest_sha,
        "tool": "verify_words",
        "arguments": {"words": ["паляниця"]},
        "result": "паляниця: attested in VESUM as noun",
    }
    reply = (
        "VERDICT: APPROVE\n"
        "```yaml\n"
        + yaml.safe_dump({
            "review_schema": 1,
            "kind": "settle",
            "evidence": [
                {
                    "receipt": "rr-supported1111111111",
                    "quote": "fabricated quote not in result",
                }
            ],
        })
        + "```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec]
    )
    assert done["claims_total"] == 1
    assert done["claims_unsupported"] == 1
    assert len(done["dropped_claims"]) == 1
    assert done["dropped_claims"][0]["reason"] == "quote_not_in_result"
    assert "fabricated quote not in result" not in final_text


def test_manifest_bound_ukrainian_review_two_items_one_void_preserves_valid_item(
    attempt, tmp_path, monkeypatch
):
    """An unsupported claim on one item voids only that item, preserving unrelated valid items."""
    from scripts.review.review_contract import build_item_packet, judge_item_reply

    manifest_sha = store.digest(b"inputs: []\n")
    rec = {
        "receipt_id": "rr-supported1111111111",
        "review_id": "review",
        "attempt_id": "attempt",
        "manifest_sha256": manifest_sha,
        "tool": "verify_words",
        "arguments": {"words": ["паляниця"]},
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
                    "quote": "паляниця",
                    "evidence": [{"receipt": "rr-supported1111111111", "quote": "attested in VESUM"}],
                },
                {
                    "id": "card-2",
                    "verdict": "APPROVE",
                    "finding": "Fabricated quote",
                    "sources": "VESUM",
                    "quote": "хліб",
                    "evidence": [{"receipt": "rr-supported1111111111", "quote": "fake quote"}],
                },
            ],
        })
        + "\n```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec]
    )
    assert done["claims_total"] == 4
    assert done["claims_unsupported"] == 2
    assert len(done["dropped_claims"]) == 2
    assert done["dropped_claims"][1]["claim"] == {"sources": "VESUM"}
    assert done["dropped_claims"][1]["reason"] == "claim_not_in_captured_output"
    assert done["dropped_claims"][1]["captured_event_ids"] == []
    assert done["dropped_claims"][0]["item_id"] == "card-2"
    assert done["dropped_claims"][0]["reason"] == "quote_not_in_result"

    packet = build_item_packet([{"id": "card-1", "text": "паляниця"}, {"id": "card-2", "text": "хліб"}])
    chunk = judge_item_reply(packet, final_text, stated="APPROVED", ukrainian=True)
    assert chunk.denominator == ("card-1", "card-2")
    assert chunk.coverage == ("card-1",)
    assert "card-2" not in chunk.coverage
    assert chunk.void is None


def test_manifest_bound_ukrainian_review_yaml_finding_fabricated_expected_dropped_and_counted(
    attempt, tmp_path, monkeypatch
):
    """A YAML finding with valid evidence receipt but fabricated sibling expected text drops expected."""
    import yaml

    manifest_sha = store.digest(b"inputs: []\n")
    rec = {
        "receipt_id": "rr-supported1111111111",
        "review_id": "review",
        "attempt_id": "attempt",
        "manifest_sha256": manifest_sha,
        "tool": "verify_words",
        "arguments": {"words": ["паляниця"]},
        "result": "паляниця: attested in VESUM as noun",
    }
    reply = (
        "VERDICT: APPROVE\n"
        "```yaml\n"
        + yaml.safe_dump({
            "review_schema": 1,
            "kind": "lesson",
            "findings": [
                {
                    "id": "F-1",
                    "claim": "Spelling issue",
                    "expected": "fabricated expected text",
                    "evidence": {
                        "receipt": "rr-supported1111111111",
                    },
                }
            ],
        })
        + "```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec]
    )
    assert done["claims_total"] == 2
    assert done["claims_unsupported"] == 1
    assert len(done["dropped_claims"]) == 1
    assert done["dropped_claims"][0]["item_id"] == "F-1"
    assert done["dropped_claims"][0]["reason"] == "quote_not_in_result"
    assert "fabricated expected text" not in final_text
    # Receipt itself was valid and retained
    assert "rr-supported1111111111" in final_text


def test_manifest_bound_ukrainian_review_yaml_finding_valid_expected_retained(
    attempt, tmp_path, monkeypatch
):
    """A YAML finding with valid evidence receipt and matching expected text retains both."""
    import yaml

    manifest_sha = store.digest(b"inputs: []\n")
    rec = {
        "receipt_id": "rr-supported1111111111",
        "review_id": "review",
        "attempt_id": "attempt",
        "manifest_sha256": manifest_sha,
        "tool": "verify_words",
        "arguments": {"words": ["паляниця"]},
        "result": "паляниця: attested in VESUM as noun",
    }
    reply = (
        "VERDICT: APPROVE\n"
        "```yaml\n"
        + yaml.safe_dump({
            "review_schema": 1,
            "kind": "lesson",
            "findings": [
                {
                    "id": "F-1",
                    "claim": "Spelling issue",
                    "expected": "attested in VESUM",
                    "evidence": {
                        "receipt": "rr-supported1111111111",
                    },
                }
            ],
        })
        + "```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec]
    )
    assert done["claims_total"] == 2
    assert done["claims_unsupported"] == 0
    assert len(done["dropped_claims"]) == 0
    assert "attested in VESUM" in final_text
    assert "rr-supported1111111111" in final_text


def test_manifest_bound_ukrainian_review_per_item_receipt_only_rejected_as_malformed_claim(
    attempt, tmp_path, monkeypatch
):
    """Per-item evidence containing only receipt without quote is rejected as malformed_claim."""
    from scripts.review.review_contract import build_item_packet, judge_item_reply

    manifest_sha = store.digest(b"inputs: []\n")
    rec = {
        "receipt_id": "rr-supported1111111111",
        "review_id": "review",
        "attempt_id": "attempt",
        "manifest_sha256": manifest_sha,
        "tool": "verify_words",
        "arguments": {"words": ["паляниця"]},
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
                    "quote": "паляниця",
                    "evidence": [{"receipt": "rr-supported1111111111"}],
                },
            ],
        })
        + "\n```\n"
    )
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec]
    )
    assert done["claims_total"] == 2
    assert done["claims_unsupported"] == 2
    assert len(done["dropped_claims"]) == 2
    assert done["dropped_claims"][1]["claim"] == {"sources": "VESUM"}
    assert done["dropped_claims"][1]["reason"] == "claim_not_in_captured_output"
    assert done["dropped_claims"][1]["captured_event_ids"] == []
    assert done["dropped_claims"][0]["item_id"] == "card-1"
    assert done["dropped_claims"][0]["reason"] == "malformed_claim"

    packet = build_item_packet([{"id": "card-1", "text": "паляниця"}])
    chunk = judge_item_reply(packet, final_text, stated="APPROVED", ukrainian=True)
    assert chunk.denominator == ("card-1",)
    assert chunk.coverage == ()


@pytest.mark.parametrize("claim,output", [
    ("Example Reference page 7", "Example Reference page 2"),
    ("Rule 8: soft-group", "Rule 8: hard-group"),
    ("VESUM tag noun:inanim:f:v_naz", "VESUM tag noun:anim:f:v_naz"),
])
def test_ukrainian_claim_text_cannot_hide_behind_valid_receipt_quote(attempt, tmp_path, monkeypatch, claim, output):
    """A valid receipt quote must not launder an assertion contradicted by that same output."""
    rec = {
        "receipt_id": "rr-same-attempt", "review_id": "review", "attempt_id": "attempt",
        "manifest_sha256": store.digest(b"inputs: []\n"), "tool": "verify_word",
        "arguments": {"word": "example"}, "result": output,
    }
    unrelated = {**rec, "receipt_id": "rr-other-event", "arguments": {"word": "other"}, "result": claim}
    reply = "VERDICT: APPROVE\n```ukrainian-item-judgments\n" + json.dumps({
        "schema": "ukrainian-item-judgments.v1", "items": [{
            "id": "card-1", "verdict": "APPROVE", "finding": "Appropriate activity.",
            "sources": claim, "evidence": [{"receipt": rec["receipt_id"], "quote": output}],
        }],
    }) + "\n```\n"
    done, final_text, _ = _run_manifest_ukrainian_attempt(
        attempt, tmp_path, monkeypatch, reply, ledger_records=[rec, unrelated],
    )
    assert done["claims_total"] == 2
    assert done["claims_unsupported"] == 1
    assert done["dropped_claims"][0]["claim"] == {"sources": claim}
    assert done["dropped_claims"][0]["reason"] == "claim_not_in_captured_output"
    assert done["dropped_claims"][0]["captured_event_ids"] == ["rr-same-attempt"]
    row = json.loads(final_text.split("```ukrainian-item-judgments\n")[1].split("\n```")[0])["items"][0]
    assert row["_approval_void"] is True
    assert row["evidence"] == [{"receipt": rec["receipt_id"], "quote": output}]


# --- Codex account b in bound attempts (#12504, C-4635) -------------------------------------------------------------


@pytest.fixture
def codex_accounts_ab(tmp_path, monkeypatch):
    """Account a's default home and account b's bound home, each holding its own distinct login."""
    import os

    a = tmp_path / "home" / ".codex"
    a.mkdir(parents=True)
    b = tmp_path / "codex-b"
    b.mkdir(mode=0o700)
    for home, body in ((a, b'{"login": "account-a"}'), (b, b'{"login": "account-b"}')):
        (home / "auth.json").write_bytes(body)
        (home / "auth.json").chmod(0o600)
    binding = tmp_path / "codex_accounts.json"
    binding.write_text(json.dumps({"schema_version": 1, "accounts": {"b-sub": {"codex_home": str(b), "budget_usd": 200}}}))
    binding.chmod(0o600)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "codex").write_text("#!/bin/sh\nexit 0\n")  # `codex login status` reports a login
    (bin_dir / "codex").chmod(0o755)
    monkeypatch.setenv("HOME", str(a.parent))
    monkeypatch.setenv("LU_CODEX_ACCOUNTS_FILE", str(binding))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    for name in ("CODEX_HOME", "OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN"):
        monkeypatch.setenv(name, "unset")  # recorded, so teardown also undoes the supervisor's own CODEX_HOME
        monkeypatch.delenv(name)
    return a, b


@pytest.mark.parametrize("label,admitted", [
    (None, True), ("sub", True), ("b-sub", True), ("api", False), ("b-api", False),
])
def test_bound_attempt_admits_only_subscription_codex_accounts(label, admitted):
    """Defect class: a bound attempt refuses account b, or runs on an API-billed route with no spending cap."""
    from types import SimpleNamespace

    from scripts.dispatcher import review_attempt

    args = SimpleNamespace(review_access=None, full_checkout=False, output_schema=None, codex_account=label,
                           prompt_file=None)
    expected = "review_attempt_prompt_file_required" if admitted else "review_attempt_account_unsupported"
    with pytest.raises(ValueError, match=expected):
        review_attempt.admit(args, b"", {}, None, "a" * 40)


def test_unknown_codex_account_refuses_a_bound_attempt_before_it_is_spent(attempt, tmp_path, monkeypatch, capsys):
    """Defect class: an unknown account label is substituted by a known one, or spends the attempt id."""
    launch = Mock()
    monkeypatch.setattr(worker, "start", launch)
    assert invoke(attempt, "--codex-account", "c-sub") == 2
    assert "codex_account_unknown" in capsys.readouterr().err
    launch.assert_not_called()
    assert not (tmp_path / "tasks").exists()


@pytest.mark.parametrize("label", ["c-sub", "API", ""])
def test_attempt_boundary_refuses_an_unknown_codex_account_without_staging(codex_accounts_ab, tmp_path, label):
    from scripts.agent_runtime.attempt_boundary import stage_codex_account_auth
    from scripts.review.isolation import ReviewIsolationError

    with pytest.raises(ReviewIsolationError, match="attempt_codex_account_unknown"):
        stage_codex_account_auth(label, tmp_path / "staged")
    assert not (tmp_path / "staged").exists()


def test_attempt_boundary_stages_each_codex_account_own_login(codex_accounts_ab, tmp_path):
    """Defect class: a b-sub attempt authenticates with account a's login, or the default account changes source."""
    from scripts.agent_runtime.attempt_boundary import stage_codex_account_auth

    a, b = codex_accounts_ab
    for label, own in ((None, a), ("sub", a), ("b-sub", b), ("b", b)):
        staged = tmp_path / f"staged-{label}"
        env = stage_codex_account_auth(label, staged)
        assert (staged / ".codex" / "auth.json").read_bytes() == (own / "auth.json").read_bytes()
        assert env["CODEX_HOME"] == str(staged / ".codex")


@pytest.mark.parametrize("case,code", [
    ("ambient_home", "attempt_codex_account_ambient_conflict"),
    ("ambient_key", "attempt_codex_account_ambient_conflict"),
    ("unbound", "attempt_codex_account_binding_missing"),
    ("logged_out", "attempt_codex_account_not_logged_in"),
    ("keyring_login", "attempt_codex_account_login_missing"),
])
def test_attempt_boundary_never_substitutes_account_a_for_b(codex_accounts_ab, tmp_path, monkeypatch, case, code):
    """Defect class: when account b's login cannot be staged, account a's (or an ambient credential) is used."""
    from scripts.agent_runtime.attempt_boundary import stage_codex_account_auth
    from scripts.review.isolation import ReviewIsolationError

    a, b = codex_accounts_ab
    if case == "ambient_home":
        monkeypatch.setenv("CODEX_HOME", str(a))
    elif case == "ambient_key":
        monkeypatch.setenv("OPENAI_API_KEY", "fixture-credential")
    elif case == "unbound":
        monkeypatch.setenv("LU_CODEX_ACCOUNTS_FILE", str(tmp_path / "absent.json"))
    elif case == "logged_out":
        codex = tmp_path / "bin" / "codex"
        codex.write_text("#!/bin/sh\nexit 1\n")
    else:
        (b / "auth.json").unlink()  # `codex login status` passes, but the login is not a stageable file
    staged = tmp_path / "staged"
    with pytest.raises(ReviewIsolationError) as refused:
        stage_codex_account_auth("b-sub", staged)
    assert str(refused.value) == code
    login = staged / ".codex" / "auth.json"
    assert not login.exists() or login.read_bytes() != (a / "auth.json").read_bytes()


def test_bound_attempt_on_codex_b_runs_as_account_b(codex_accounts_ab, attempt, tmp_path, monkeypatch):
    """A b-sub attempt routes its label into the boundary, and the supervisor runs, stages and is metered as b.

    Defect class: a bound attempt on b stages account a's login, or its usage and rate limits count against a.
    """
    import os
    from types import SimpleNamespace

    from scripts.agent_runtime import attempt_boundary, review_mcp, runner, usage
    from scripts.dispatcher import headroom

    a, b = codex_accounts_ab
    args = cli.build_parser().parse_args(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", *attempt,
                                          "--codex-account", "b-sub", "--review-access", "full"])
    binding = store.review_binding(vars(args))
    prefix, dependency = trusted_core_context()
    rendered = (prefix + "Rendered review prompt\nattempt: review/attempt\n").encode()
    prompt = cli._PromptPath(tmp_path / "tasks" / "task.prompt")
    prompt.content = rendered
    workspace = tmp_path / "checkout"
    workspace.mkdir()
    spec = TaskSpec("task", "codex", "gpt-6.1-sol", "high", "read-only", workspace, prompt,
                    tmp_path / "tasks" / "task.result", options=dict(review_attempt=str(tmp_path / "manifest.yaml")),
                    codex_account="b-sub")
    record = store.new_record(spec, dict(key="public", github="example/public"), "codex/task", "a" * 40,
                              dict(vars(args), research_owned_path=[]), binding=binding)
    assert record["codex_account"] == "b-sub"
    record["review_contract"] = dict(input_root=str(tmp_path), machinery_dependencies={"rules_core": dependency},
                                     prompt_sha256=store.digest(rendered))
    path = store.create(record, rendered)
    for name in ("check_plan", "check_runtime"):
        monkeypatch.setattr(headroom, name, lambda *_a, **_k: None)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_a, **_k: None)
    monkeypatch.setattr(worker, "settle_left_worktrees", lambda *_a, **_k: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *_a: {})
    monkeypatch.setattr(attempt_boundary, "verify_full_review_tree", lambda *a: None)
    receipts = tmp_path / "review-receipts" / "review"

    def prepare(review_id, attempt_id, manifest, harness, **kwargs):
        config = receipts / "attempt.mcp.json"
        config.write_text("{}")
        (receipts / "attempt.jsonl.sha256").write_text(store.digest(b"") + "\n")
        return review_mcp.ReviewMcpPlan(config, {}, receipts / "attempt.jsonl", receipts / "attempt.jsonl.sha256",
                                        binding["manifest_sha256"], review_id, attempt_id, harness)

    monkeypatch.setattr(review_mcp, "prepare_review_attempt", prepare)
    seen = []

    def invoke_runtime(agent, text, **kwargs):
        label = kwargs["tool_config"][attempt_boundary.CODEX_ACCOUNT_KEY]
        staged = tmp_path / "boundary-home"
        attempt_boundary.stage_codex_account_auth(label, staged)  # what AttemptBoundary stages for this label
        seen.append((label, os.environ["CODEX_HOME"], usage.current_codex_account(),
                     (staged / ".codex" / "auth.json").read_bytes()))
        return SimpleNamespace(ok=True, response="review: done\n", identity_state="unknown", observed_model=None,
                               observed_model_source=None, failure_code=None, stderr_excerpt=None)

    monkeypatch.setattr(runner, "invoke", invoke_runtime)
    worker.supervise(path, {}, 60)

    assert store.read("task")["error"] is None, store.read("task")["error"]
    assert seen == [("b-sub", str(b), "b-sub", (b / "auth.json").read_bytes())]
    assert seen[0][3] != (a / "auth.json").read_bytes()
    assert store.read("task")["status"] == "done"


@pytest.mark.parametrize("suffix", [" ", " ", "　"])
def test_attempt_boundary_refuses_a_bound_home_that_staging_would_rename(codex_accounts_ab, tmp_path, monkeypatch, suffix):
    """F1 (#12732 round 1): a bound home named like account a's home plus trailing whitespace stays b's.

    Defect class: staging normalizes the bound CODEX_HOME (``str.strip``) into another directory and copies
    account a's login for b.
    """
    from scripts.agent_runtime.attempt_boundary import stage_codex_account_auth
    from scripts.review.isolation import ReviewIsolationError

    a, b = codex_accounts_ab
    twin = a.parent / f".codex{suffix}"
    twin.mkdir(mode=0o700)
    (twin / "auth.json").write_bytes((b / "auth.json").read_bytes())
    (twin / "auth.json").chmod(0o600)
    binding = tmp_path / "codex_accounts.json"
    binding.write_text(json.dumps({"schema_version": 1, "accounts": {"b-sub": {"codex_home": str(twin), "budget_usd": 200}}}))
    staged = tmp_path / "staged"
    with pytest.raises(ReviewIsolationError, match=r"^attempt_codex_account_home_not_canonical$"):
        stage_codex_account_auth("b-sub", staged)
    login = staged / ".codex" / "auth.json"
    assert not login.exists() or login.read_bytes() != (a / "auth.json").read_bytes()
