"""#10404: direct branch reviews preserve occupied author checkouts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_authoring_review_feasibility import SOL, mini_repo, pin_review_target
from tests.test_delegate import (
    _fixture_runtime_tmp_root,  # noqa: F401 - shared pytest fixture
    _fixture_worktree_lock_dir,  # noqa: F401 - shared pytest fixture
    _patch_worker_popen,
    _rendered_attempt_prompt,
    _review_code,
    _sanitize_git_env_for_test,
    _stub_node_modules_integrity_sweep,  # noqa: F401 - shared pytest fixture
    _stub_venv_integrity_sweep,  # noqa: F401 - shared pytest fixture
    _write_args,
    delegate,
)
from tests.test_record_cf_verdict import recorder_matcher  # noqa: F401 - shared pytest fixture

pytestmark = pytest.mark.usefixtures(
    "hermetic_monitor", "_fixture_runtime_tmp_root", "_fixture_worktree_lock_dir",
    "_stub_node_modules_integrity_sweep", "_stub_venv_integrity_sweep",
)


@pytest.fixture
def review_repo(tmp_path, monkeypatch):
    _sanitize_git_env_for_test(monkeypatch)
    repo = mini_repo(tmp_path, monkeypatch)
    (repo.root / ".gitignore").write_text(".worktrees/\nbatch_state/\nignored/\n")
    repo.git("add", ".gitignore")
    repo.git("commit", "-qm", f"ignore local output\n\nX-Agent: {SOL}")
    repo.commit(SOL, path="src/app.py", text="reviewed = True\n")
    head = repo.publish()
    repo.git("checkout", "-q", "-B", "main", "origin/main")
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    monkeypatch.setattr(delegate, "_local_repo_root", repo.root)
    monkeypatch.chdir(repo.root)
    monkeypatch.setenv("LU_TASKS_DIR", str(repo.root / "batch_state/tasks"))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    pin_review_target(monkeypatch, repo.sha("main"))
    _patch_worker_popen(monkeypatch)
    launches = []
    spawn = delegate.dispatch_isolation.spawn_detached_worker

    def observe_spawn(cmd, **kwargs):
        launches.append(cmd)
        return spawn(cmd, **kwargs)

    monkeypatch.setattr(delegate.dispatch_isolation, "spawn_detached_worker", observe_spawn)
    repo.launches = launches
    return repo, head


def author_state(repo, author):
    return {
        "head": repo.git("-C", str(author), "rev-parse", "HEAD"),
        "branch": repo.git("-C", str(author), "symbolic-ref", "HEAD"),
        "status": repo.git("-C", str(author), "status", "--porcelain=v1", "--ignored", "--untracked-files=all"),
        "refs": repo.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads"),
        "files": {str(p.relative_to(author)): p.read_bytes() for p in author.rglob("*") if p.is_file()},
    }


def review_args(head, **overrides):
    return _write_args(
        agent="grok", model="grok-4.7", task_id="snapshot-review", mode="read-only",
        branch="feature", pinned_head=head, review=True, review_profile="code",
        review_author_model="gpt-6.1-sol", review_risk="medium", prompt="Review the exact branch head.",
        **overrides,
    )


@pytest.mark.usefixtures("recorder_matcher")
@pytest.mark.parametrize("opsec_case", ["clean", "unavailable", "incompatible", "blocked"])
def test_dispatched_detached_review_binds_verdict_without_touching_author(
    review_repo, monkeypatch, tmp_path, synthetic_opsec, opsec_case,
):
    from scripts.opsec import prepublish
    from scripts.publish import github
    from scripts.review import record_cf_verdict as recorder
    from tests.opsec_fixtures import TOKEN, synthetic_rules
    from tests.test_record_cf_verdict import setup_record

    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    repo.git("worktree", "add", str(author), "feature")
    (author / "src/app.py").write_bytes(b"dirty author\x00\xff")
    before = author_state(repo, author)
    assert delegate.cmd_dispatch(review_args(head)) == 0
    path = delegate._state_path("snapshot-review")
    record = json.loads(path.read_text())
    assert record["worktree_branch"] is None
    # Synthetic completion and runtime attestation; no provider is invoked.
    record.update(status="done", resolved_model="grok-4.7-build", resolved_model_known=True,
                  resolved_model_source="grok-model-usage")
    path.write_text(json.dumps(record))
    path.with_suffix(".result").write_text("VERDICT: APPROVE")
    real_json = recorder._run_json
    _, comments, calls = setup_record(monkeypatch, tmp_path, head=head, branch="feature", families={"openai"})
    fake_json = recorder._run_json

    def route(args, **kwargs):
        if isinstance(args, github.Request) and args.verb == "issue-comment-json":
            return real_json(args, **kwargs)
        return fake_json(args, **kwargs)

    def transport(argv, **kwargs):
        payload = json.loads(Path(argv[argv.index("--input") + 1]).read_text())
        assert TOKEN not in payload["body"]
        posted = fake_json(github.Request("issue-comment-json", repo=record["repository"],
                                         number=42, body=payload["body"]))
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(posted), stderr="")

    monkeypatch.setattr(recorder, "_run_json", route)
    monkeypatch.setattr(github, "_send", transport)

    if opsec_case == "unavailable":
        monkeypatch.setattr(prepublish, "private_tooling", lambda: synthetic_opsec / "absent")
    elif opsec_case == "incompatible":
        (synthetic_opsec / "matcher.py").write_text("# no Matcher interface\n")
    elif opsec_case == "blocked":
        policy = json.loads(prepublish.POLICY.read_text())
        rules = json.loads((synthetic_opsec / "rules.json").read_text())
        rules.update(synthetic_rules(rule=policy["class6_block_ids"][0], level=6, pattern=TOKEN))
        (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
        path.with_suffix(".result").write_text(f"VERDICT: APPROVE\n{TOKEN}\nHarmless reviewer prose.")

    record_before = path.read_bytes()
    result_before = path.with_suffix(".result").read_bytes()
    if opsec_case in {"unavailable", "incompatible"}:
        reason = "private matcher or rules unavailable/incompatible"
        with pytest.raises(recorder.RecordError, match=f"publish_blocked: .*{reason}"):
            recorder.record("snapshot-review", pr_number=42, task_root=path.parent,
                            lock_root=tmp_path / "locks")
        assert comments == []
        assert calls == {"posts": 0, "statuses": 0}
        assert path.read_bytes() == record_before
        assert path.with_suffix(".result").read_bytes() == result_before
        assert author_state(repo, author) == before
        return

    receipt = recorder.record("snapshot-review", pr_number=42, task_root=path.parent,
                              lock_root=tmp_path / "locks")

    assert receipt["head"] == head
    assert receipt["comment"] == "posted"
    assert receipt["status"] == "posted"
    assert receipt["verdict"] == "APPROVED"
    assert recorder.parse_marker(comments[0]["body"])["sha"] == head
    assert recorder.parse_marker(comments[0]["body"])["verdict"] == "APPROVED"
    if opsec_case == "blocked":
        started = datetime.fromisoformat(record["started_at"]).astimezone(UTC).isoformat(timespec="microseconds")
        assert comments[0]["body"] == (
            f"### Cross-family review\nhead: {head}\nReviewer family: xai\nVERDICT: APPROVED\n"
            "Reviewer model: grok-4.7\nTask id: snapshot-review\n\nWithheld findings: unknown\n"
            "Findings are held privately.\n\n"
            f"<!-- cf-verdict v1 sha={head} task=snapshot-review started={started} "
            "verdict=APPROVED model=grok-4.7 family=xai -->"
        )
        prepublish.check_texts(record["repository"], [comments[0]["body"]], environment={})
        assert TOKEN not in comments[0]["body"]
        assert "Harmless reviewer prose." not in comments[0]["body"]
    assert calls == {"posts": 1, "statuses": 1}
    assert author_state(repo, author) == before
    assert path.read_bytes() == record_before
    assert path.with_suffix(".result").read_bytes() == result_before
    assert json.loads(path.read_text())["worktree_branch"] is None


@pytest.mark.parametrize("branch", ["main", "master", "unsafe..branch"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_snapshot_refuses_invalid_branch_before_fetch_or_success(review_repo, monkeypatch, capsys, branch, dry_run):
    repo, head = review_repo
    before = repo.snapshot()[:3]
    git_commands = []
    run = subprocess.run

    def observe_git(command, *args, **kwargs):
        if command[0] == "git":
            git_commands.append(command)
        return run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observe_git)
    args = review_args(head, dry_run=dry_run)
    args.branch = branch

    assert delegate.cmd_dispatch(args) == 1

    output = capsys.readouterr()
    diagnostic = "protected branches" if branch in {"main", "master"} else "valid git branch"
    assert diagnostic in output.err
    assert "planned new detached snapshot" not in output.err
    assert output.out == ""
    record = delegate._state_path("snapshot-review")
    assert not record.exists() or json.loads(record.read_text())["status"] == "failed"
    assert repo.launches == []
    assert not any("fetch" in command[1:] for command in git_commands)
    assert not any("worktree" in command and "add" in command for command in git_commands)
    assert not (repo.root / ".worktrees/dispatch/grok/snapshot-review").exists()
    assert repo.snapshot()[:3] == before


@pytest.mark.parametrize("branch", ["main", "master", "unsafe..branch", "feature", "  feature  "])
def test_snapshot_branch_name_validation_is_subprocess_free(review_repo, monkeypatch, branch):
    def refuse_subprocess(*args, **kwargs):
        pytest.fail("branch-name validation must not run subprocesses")

    monkeypatch.setattr(subprocess, "run", refuse_subprocess)
    monkeypatch.setattr(subprocess, "Popen", refuse_subprocess)
    if branch.strip() == "feature":
        assert delegate._validate_branch_reuse_name(branch) == "feature"
    else:
        with pytest.raises(ValueError):
            delegate._validate_branch_reuse_name(branch)


@pytest.mark.parametrize("branch", ["feature", "  feature  "])
def test_snapshot_valid_branch_dry_run_keeps_base_unresolved(review_repo, monkeypatch, branch):
    repo, head = review_repo
    git_commands = []
    run = subprocess.run

    def observe_git(command, *args, **kwargs):
        if command[0] == "git":
            git_commands.append(command)
        return run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observe_git)
    args = review_args(head, dry_run=True)
    args.branch = branch

    assert delegate.cmd_dispatch(args) == 0

    snapshot = repo.root / ".worktrees/dispatch/grok/snapshot-review"
    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert record["status"] == "dry_run"
    assert record["cwd"] == record["worktree_path"] == str(snapshot)
    assert record["worktree_base_sha"] is None
    assert record["worktree_branch"] is None
    assert record["worktree_reused"] is False
    assert record["review_branch"] == "feature"
    assert not snapshot.exists()
    assert repo.launches == []
    assert not any("fetch" in command[1:] for command in git_commands)
    assert not any("worktree" in command and "add" in command for command in git_commands)


@pytest.mark.parametrize("condition", ["clean", "dirty", "unattributed"])
@pytest.mark.parametrize("explicit_path", [False, True])
def test_direct_review_dry_run_plans_new_snapshot_without_touching_author(
    review_repo, monkeypatch, capsys, condition, explicit_path,
):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    repo.git("worktree", "add", str(author), "feature")
    (author / "ignored").mkdir()
    (author / "ignored/output.bin").write_bytes(b"retained output\x00\xff")
    if condition == "dirty":
        (author / "src/app.py").write_bytes(b"staged author bytes\x00\xff")
        repo.git("-C", str(author), "add", "src/app.py")
        (author / "src/app.py").write_bytes(b"unstaged author bytes\x00\xfe")
        (author / "untracked.bin").write_bytes(b"untracked author bytes\x00\xfd")
    author_record = delegate._state_path("author")
    if condition != "unattributed":
        delegate._write_state_atomic(author_record, {
            "task_id": "author", "status": "done", "mode": "workspace-write",
            "worktree_path": str(author), "worktree_branch": "feature", "keep_worktree": True,
            "worktree_reused": False,
        })
    record_before = author_record.read_bytes() if author_record.exists() else None
    before = author_state(repo, author)
    index = Path(repo.git("-C", str(author), "rev-parse", "--git-path", "index"))
    index_before = index.read_bytes()
    refs_before = repo.git("for-each-ref", "--format=%(refname) %(objectname)")
    trees_before = repo.git("worktree", "list", "--porcelain")
    snapshot = repo.root / ".worktrees/dispatch/grok" / (
        "explicit-review-snapshot" if explicit_path else "snapshot-review"
    )
    if explicit_path:
        snapshot.parent.mkdir(parents=True)
    git_commands = []
    run = subprocess.run

    def observe_git(command, *args, **kwargs):
        if command[0] == "git":
            git_commands.append(command)
        return run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observe_git)

    assert delegate.cmd_dispatch(review_args(
        head, dry_run=True, worktree=str(snapshot) if explicit_path else None,
    )) == 0

    output = capsys.readouterr().err
    assert f"planned new detached snapshot: path={snapshot} pinned_head={head}" in output
    assert "remote pin has not been fetched or validated" in output
    assert "branch reuse validated" not in output
    assert "[reused]" not in output
    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert record["status"] == "dry_run"
    assert record["cwd"] == record["worktree_path"] == str(snapshot)
    assert record["pinned_head"] == head
    assert record["worktree_branch"] is None
    assert record["worktree_base_sha"] is None
    assert record["worktree_reused"] is False
    assert not snapshot.exists()
    assert repo.launches == []
    assert not any("fetch" in command[1:] for command in git_commands)
    assert not any("worktree" in command and "add" in command for command in git_commands)
    assert author_state(repo, author) == before
    assert index.read_bytes() == index_before
    assert repo.git("for-each-ref", "--format=%(refname) %(objectname)") == refs_before
    assert repo.git("worktree", "list", "--porcelain") == trees_before
    assert (author_record.read_bytes() if author_record.exists() else None) == record_before
    assert (author / "ignored/output.bin").read_bytes() == b"retained output\x00\xff"
    if condition == "dirty":
        assert (author / "src/app.py").read_bytes() == b"unstaged author bytes\x00\xfe"
        assert (author / "untracked.bin").read_bytes() == b"untracked author bytes\x00\xfd"
        assert subprocess.run(
            ["git", "-C", str(author), "show", ":src/app.py"], capture_output=True, check=True, timeout=30,
        ).stdout == b"staged author bytes\x00\xff"
    else:
        assert (author / "src/app.py").read_bytes() == b"reviewed = True\n"


@pytest.mark.parametrize("condition", ["clean", "dirty", "unattributed", "unoccupied"])
@pytest.mark.parametrize("explicit_path", [False, True])
def test_direct_review_preserves_author_and_reaps_only_its_snapshot(review_repo, monkeypatch, condition, explicit_path):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    before = None
    if condition != "unoccupied":
        repo.git("worktree", "add", str(author), "feature")
        (author / "ignored").mkdir()
        (author / "ignored/output.bin").write_bytes(b"retained output\x00\xff")
        if condition == "dirty":
            (author / "src/app.py").write_bytes(b"staged author bytes\x00\xff")
            repo.git("-C", str(author), "add", "src/app.py")
            (author / "src/app.py").write_bytes(b"unstaged author bytes\x00\xfe")
            (author / "untracked.bin").write_bytes(b"untracked author bytes\x00\xfd")
        if condition != "unattributed":
            delegate._write_state_atomic(delegate._state_path("author"), {
                "task_id": "author", "status": "done", "mode": "workspace-write",
                "worktree_path": str(author), "worktree_branch": "feature", "keep_worktree": True,
                "worktree_reused": False,
            })
        before = author_state(repo, author)
    author_record = delegate._state_path("author")
    record_before = author_record.read_bytes() if author_record.exists() else None
    snapshot = repo.root / ".worktrees/dispatch/grok/snapshot-review"
    if explicit_path:
        snapshot.parent.mkdir(parents=True)
    args = review_args(head, worktree=str(snapshot) if explicit_path else None)

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert Path(record["cwd"]) == snapshot
    assert record["worktree_path"] == str(snapshot)
    assert record["worktree_branch"] is None
    assert record["worktree_base_sha"] == record["pinned_head"] == head
    assert record["worktree_reused"] is False
    assert record["worktree_layout"] == "dispatch"
    assert repo.git("-C", str(snapshot), "rev-parse", "HEAD") == head
    assert repo.git("-C", str(snapshot), "symbolic-ref", "-q", "HEAD", check=False) == ""
    assert (snapshot / "src/app.py").read_bytes() == b"reviewed = True\n"
    assert record["agent"] == "grok" and record["model"] == "grok-4.7"
    assert record["review_author_model"] == "gpt-6.1-sol"
    assert len(repo.launches) == 1
    assert before is None or author_state(repo, author) == before
    record.update(status="done")
    delegate._write_state_atomic(delegate._state_path("snapshot-review"), record)
    removal = delegate._settle_worktree_reap(
        snapshot, created_by_this_dispatch=True, settling_task_id="snapshot-review", task_record=record,
    )
    assert removal["action"] == "removed", removal
    assert removal["branch"] is None
    assert not snapshot.exists()
    assert repo.sha("feature") == head
    if before is not None:
        assert author_state(repo, author) == before
    assert (author_record.read_bytes() if author_record.exists() else None) == record_before


def test_remote_moves_after_admission_refuses_before_provider_start(review_repo, monkeypatch, capsys):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    repo.git("worktree", "add", str(author), "feature")
    before = author_state(repo, author)
    fetch = delegate._fetch_existing_branch

    def fetch_moved_branch(branch):
        repo.advance_remote(branch, SOL, path="src/app.py")
        fetch(branch)

    monkeypatch.setattr(delegate, "_fetch_existing_branch", fetch_moved_branch)

    assert delegate.cmd_dispatch(review_args(head)) == 1

    assert f"differs from the pinned head SHA {head}" in capsys.readouterr().err
    assert repo.launches == []
    assert author_state(repo, author) == before
    assert not (repo.root / ".worktrees/dispatch/grok/snapshot-review").exists()
    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert record["status"] == "failed"
    assert record["worktree_branch"] is None


@pytest.mark.parametrize("has_dispositions", [False, True], ids=["without", "with"])
def test_live_review_record_carries_the_brief_warning(review_repo, capsys, has_dispositions):
    """#10665: the launched review records the typed warning; the brief is never refused for it."""
    repo, head = review_repo
    brief = "Review the exact branch head.\n" + ("\n## Dispositions\n- follow_up: wording.\n" if has_dispositions else "")
    args = review_args(head)
    args.prompt = brief
    assert delegate.cmd_dispatch(args) == 0
    assert len(repo.launches) == 1
    record = json.loads(delegate._state_path("snapshot-review").read_text())
    warned = f"⚠ {delegate.REVIEW_BRIEF_NO_DISPOSITIONS}: " in capsys.readouterr().err
    if has_dispositions:
        assert not warned and "review_brief_warnings" not in record
    else:
        assert warned and record["review_brief_warnings"] == [delegate.REVIEW_BRIEF_NO_DISPOSITIONS]


def test_write_branch_continuation_reuses_the_existing_attached_tree(review_repo):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    repo.git("worktree", "add", str(author), "feature")
    before = author_state(repo, author)
    args = _write_args(
        agent="codex", model="gpt-6.1-sol", task_id="write-continuation", branch="feature",
        worktree=str(author), owned_path=["src/app.py"], prompt="Continue the existing task.",
    )

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("write-continuation").read_text())
    assert record["worktree_path"] == record["cwd"] == str(author)
    assert record["worktree_branch"] == "feature"
    assert record["review_branch"] is None
    assert record["worktree_reused"] is True
    assert record["worktree_base_sha"] == head
    assert author_state(repo, author) == before
    assert len(repo.launches) == 1


@pytest.mark.parametrize("pinned", [False, True])
def test_ordinary_read_only_branch_continuation_keeps_attached_tree(review_repo, pinned):
    repo, head = review_repo
    target = repo.root / ".worktrees/dispatch/codex/continuation"
    repo.git("worktree", "add", str(target), "feature")
    before = author_state(repo, target)
    args = _write_args(
        task_id="continuation", mode="read-only", branch="feature", worktree=str(target),
        pinned_head=head if pinned else None, prompt="Inspect the existing task checkout.",
    )

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("continuation").read_text())
    assert record["worktree_path"] == record["cwd"] == str(target)
    assert record["worktree_branch"] == "feature"
    assert record["worktree_reused"] is True
    assert record["worktree_base_sha"] == head
    assert repo.git("-C", str(target), "symbolic-ref", "HEAD") == "refs/heads/feature"
    assert author_state(repo, target) == before
    assert len(repo.launches) == 1


@pytest.mark.parametrize("explicit_path", [False, True])
def test_review_attempt_preserves_attached_input_and_prepares_in_that_tree(review_repo, monkeypatch, explicit_path):
    repo, head = review_repo
    target = repo.root / ".worktrees/dispatch/claude/attempt-review"
    repo.git("worktree", "add", str(target), "feature")
    _review_code(repo.root)
    _review_code(target)
    manifest = target / "local_state/manifest.yaml"
    manifest.parent.mkdir()
    manifest.write_text("review: test\n")
    repo.git("-C", str(target), "add", ".mcp", "requirements-lock.txt", "scripts/review", "local_state")
    repo.git("-C", str(target), "commit", "-qm", f"admitted attempt inputs\n\nX-Agent: {SOL}")
    head = repo.publish()
    prompt = _rendered_attempt_prompt(repo.root, repo.root / "batch_state/prompt.md", input_root=target)
    monkeypatch.setattr("scripts.agent_runtime.review_mcp.review_server_checkout", lambda: repo.root)
    prepared = []

    def prepare_attempt(**kwargs):
        prepared.append(kwargs)
        return SimpleNamespace(
            config_path=repo.root / "batch_state/attempt.json",
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )

    monkeypatch.setattr("scripts.agent_runtime.review_mcp.prepare_review_attempt", prepare_attempt)
    before = author_state(repo, target)
    args = _write_args(
        agent="claude", model="claude-opus-5-5", task_id="attempt-review", mode="read-only",
        branch="feature", worktree=str(target) if explicit_path else "auto",
        prompt=None, prompt_file=str(prompt), review_attempt=str(manifest),
        review_id="rev-test", attempt_id="att-test",
    )

    assert delegate.cmd_dispatch(args) == 0

    record = json.loads(delegate._state_path("attempt-review").read_text())
    assert record["worktree_path"] == record["cwd"] == str(target)
    assert record["worktree_branch"] == "feature"
    assert record["worktree_reused"] is True
    assert record["worktree_base_sha"] == head
    assert record["review_attempt"]["review_id"] == "rev-test"
    assert len(prepared) == 1
    assert prepared[0]["checkout_root"] == target
    assert prepared[0]["manifest_path"] == manifest
    assert author_state(repo, target) == before
    assert len(repo.launches) == 1


@pytest.mark.parametrize("relation", ["equal", "behind", "ahead", "divergent"])
@pytest.mark.parametrize("explicit_path", [False, True])
def test_snapshot_uses_remote_commit_independently_of_dirty_local_branch(review_repo, relation, explicit_path):
    repo, head = review_repo
    author = repo.root / ".worktrees/dispatch/codex/author"
    if relation in {"behind", "divergent"}:
        repo.git("branch", "-f", "feature", f"{head}~1")
    repo.git("worktree", "add", str(author), "feature")
    if relation in {"ahead", "divergent"}:
        (author / "src/app.py").write_bytes(b"local-only commit\x00\xff")
        repo.git("-C", str(author), "add", "src/app.py")
        repo.git("-C", str(author), "commit", "-qm", f"local work\n\nX-Agent: {SOL}")
    (author / "src/app.py").write_bytes(b"staged bytes\x00\xfe")
    repo.git("-C", str(author), "add", "src/app.py")
    (author / "src/app.py").write_bytes(b"unstaged bytes\x00\xfd")
    (author / "untracked.bin").write_bytes(b"untracked\x00\xfc")
    (author / "ignored").mkdir()
    (author / "ignored/output.bin").write_bytes(b"ignored\x00\xfb")
    author_record = delegate._state_path("author")
    delegate._write_state_atomic(author_record, {
        "task_id": "author", "status": "done", "mode": "workspace-write",
        "worktree_path": str(author), "worktree_branch": "feature", "keep_worktree": True,
        "worktree_reused": False,
    })
    before = author_state(repo, author)
    index = Path(repo.git("-C", str(author), "rev-parse", "--git-path", "index"))
    index_before = index.read_bytes()
    record_before = author_record.read_bytes()
    snapshot = repo.root / ".worktrees/dispatch/grok" / (
        "distinct-explicit-snapshot" if explicit_path else "snapshot-review"
    )
    snapshot.parent.mkdir(parents=True)

    assert delegate.cmd_dispatch(review_args(head, worktree=str(snapshot) if explicit_path else None)) == 0

    record = json.loads(delegate._state_path("snapshot-review").read_text())
    assert record["cwd"] == record["worktree_path"] == str(snapshot)
    assert record["worktree_base_sha"] == record["pinned_head"] == head
    assert record["worktree_branch"] is None
    assert repo.git("-C", str(snapshot), "rev-parse", "HEAD") == head
    assert repo.git("-C", str(snapshot), "symbolic-ref", "-q", "HEAD", check=False) == ""
    assert repo.git("-C", str(snapshot), "diff", "--exit-code", head) == ""
    assert (snapshot / "src/app.py").read_bytes() == b"reviewed = True\n"
    assert not (snapshot / "untracked.bin").exists()
    assert not (snapshot / "ignored").exists()
    assert author_state(repo, author) == before
    assert index.read_bytes() == index_before
    assert author_record.read_bytes() == record_before
    assert len(repo.launches) == 1


@pytest.mark.parametrize("shape", ["empty-directory", "nonempty-directory", "file"])
@pytest.mark.parametrize("explicit_path", [False, True])
@pytest.mark.parametrize("dry_run", [False, True])
def test_snapshot_refuses_existing_destination_before_fetch_or_success(
    review_repo, monkeypatch, capsys, shape, explicit_path, dry_run,
):
    repo, head = review_repo
    snapshot = repo.root / ".worktrees/dispatch/grok" / (
        "distinct-explicit-snapshot" if explicit_path else "snapshot-review"
    )
    snapshot.parent.mkdir(parents=True)
    if shape == "file":
        snapshot.write_bytes(b"existing destination\x00\xff")
    else:
        snapshot.mkdir()
        if shape == "nonempty-directory":
            (snapshot / "retained.bin").write_bytes(b"retained\x00\xfe")
    retained_record = delegate._state_path("unrelated-task")
    delegate._write_state_atomic(retained_record, {"task_id": "unrelated-task", "status": "done", "keep_worktree": True})
    record_before = retained_record.read_bytes()
    before = repo.snapshot()[:3]
    files_before = {str(p): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()}
    file_before = snapshot.read_bytes() if snapshot.is_file() else None
    git_commands = []
    run = subprocess.run

    def observe_git(command, *args, **kwargs):
        if command[0] == "git":
            git_commands.append(command)
        return run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observe_git)

    assert delegate.cmd_dispatch(review_args(
        head, dry_run=dry_run, worktree=str(snapshot) if explicit_path else None,
    )) == 1

    output = capsys.readouterr()
    assert "detached read-only worktree already exists" in output.err
    assert "planned new detached snapshot" not in output.err
    assert output.out == ""
    record = delegate._state_path("snapshot-review")
    assert not record.exists() or json.loads(record.read_text())["status"] == "failed"
    assert not any("fetch" in command[1:] for command in git_commands)
    assert not any("worktree" in command and "add" in command for command in git_commands)
    assert repo.launches == []
    assert repo.snapshot()[:3] == before
    assert retained_record.read_bytes() == record_before
    assert {str(p): p.read_bytes() for p in snapshot.rglob("*") if p.is_file()} == files_before
    assert (snapshot.read_bytes() if snapshot.is_file() else None) == file_before


@pytest.mark.parametrize("target_exists", [False, True])
@pytest.mark.parametrize("explicit_path", [False, True])
@pytest.mark.parametrize("dry_run", [False, True])
def test_snapshot_contained_symlink_uses_canonical_destination(
    review_repo, monkeypatch, capsys, target_exists, explicit_path, dry_run,
):
    repo, head = review_repo
    anchor = repo.root / ".worktrees/dispatch/grok"
    anchor.mkdir(parents=True)
    target = anchor / "canonical-snapshot"
    link = anchor / ("explicit-link" if explicit_path else "snapshot-review")
    if target_exists:
        target.mkdir()
        (target / "retained.bin").write_bytes(b"retained\x00\xff")
    link.symlink_to(target.name, target_is_directory=True)
    git_commands = []
    run = subprocess.run

    def observe_git(command, *args, **kwargs):
        if command[0] == "git":
            git_commands.append(command)
        return run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observe_git)

    assert delegate.cmd_dispatch(review_args(
        head, dry_run=dry_run, worktree=str(link) if explicit_path else None,
    )) == (1 if target_exists else 0)

    output = capsys.readouterr().err
    assert link.is_symlink() and link.readlink() == Path(target.name)
    if target_exists:
        assert "detached read-only worktree already exists" in output
        assert "planned new detached snapshot" not in output
        assert (target / "retained.bin").read_bytes() == b"retained\x00\xff"
    else:
        record = json.loads(delegate._state_path("snapshot-review").read_text())
        assert record["worktree_path"] == record["cwd"] == str(target)
        if dry_run:
            assert record["status"] == "dry_run"
            assert f"path={target} pinned_head={head}" in output
            assert not target.exists()
        else:
            assert repo.git("-C", str(target), "rev-parse", "HEAD") == head
            assert repo.git("-C", str(target), "symbolic-ref", "-q", "HEAD", check=False) == ""
    assert len(repo.launches) == (0 if target_exists or dry_run else 1)
    if target_exists or dry_run:
        assert not any("fetch" in command[1:] for command in git_commands)
        assert not any("worktree" in command and "add" in command for command in git_commands)


def test_snapshot_accepts_remote_without_local_branch(review_repo):
    repo, head = review_repo
    repo.git("branch", "-D", "feature")

    assert delegate.cmd_dispatch(review_args(head)) == 0

    snapshot = repo.root / ".worktrees/dispatch/grok/snapshot-review"
    assert repo.git("-C", str(snapshot), "rev-parse", "HEAD") == head
    assert repo.git("show-ref", "--verify", "refs/heads/feature", check=False) == ""
    assert len(repo.launches) == 1


@pytest.mark.parametrize("failure", ["missing-remote", "fetch-failure", "unresolved-commit"])
def test_snapshot_never_uses_cached_tracking_ref_on_remote_failure(review_repo, monkeypatch, capsys, failure):
    repo, head = review_repo
    assert repo.sha("origin/feature") == head
    if failure == "missing-remote":
        repo.git("--git-dir", str(repo.remote), "update-ref", "-d", "refs/heads/feature")
    elif failure == "fetch-failure":
        repo.git("config", "--unset-all", f"url.{repo.remote}.insteadOf")
        repo.git("config", f"url.{repo.remote.parent / 'unavailable.git'}.insteadOf",
                 "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git")
    else:
        resolve_sha = delegate._resolve_sha

        def unresolved_origin(path, ref="HEAD"):
            return None if ref == "origin/feature" else resolve_sha(path, ref)

        monkeypatch.setattr(delegate, "_resolve_sha", unresolved_origin)
    before = repo.snapshot()[:3]

    assert delegate.cmd_dispatch(review_args(head)) == 1

    output = capsys.readouterr().err
    assert ("was not found after fetch" if failure == "unresolved-commit" else "could not fetch existing branch") in output
    assert repo.launches == []
    assert not (repo.root / ".worktrees/dispatch/grok/snapshot-review").exists()
    assert repo.snapshot()[:3] == before
    assert json.loads(delegate._state_path("snapshot-review").read_text())["status"] == "failed"


@pytest.mark.parametrize("relation", ["ahead", "divergent"])
def test_attached_resolver_still_refuses_local_unpublished_history(review_repo, relation):
    repo, head = review_repo
    repo.git("checkout", "feature")
    if relation == "divergent":
        repo.git("reset", "--hard", f"{head}~1")
    repo.commit(SOL, path="src/app.py", text="local unpublished work\n")
    repo.git("checkout", "main")
    before = repo.snapshot()

    with pytest.raises(RuntimeError, match="not an ancestor"):
        delegate._resolve_worktree_base_sha(
            agent="codex", task_id="attached", raw_path=str(repo.root / ".worktrees/dispatch/codex/attached"),
            base="main", branch="feature", detached=False, pinned_head_sha=head,
        )

    assert repo.snapshot() == before
    assert repo.launches == []


def test_snapshot_dry_run_refuses_explicit_path_swapped_after_validation(review_repo, monkeypatch, capsys):
    repo, head = review_repo
    snapshot = repo.root / ".worktrees/dispatch/grok/explicit-snapshot"
    snapshot.mkdir(parents=True)
    outside = repo.root.parent / "outside-anchor"
    outside.mkdir()
    (outside / "retained.bin").write_bytes(b"retained\x00\xff")

    def swap():
        snapshot.rename(snapshot.with_name("original-destination"))
        snapshot.symlink_to(outside, target_is_directory=True)

    monkeypatch.setattr(delegate, "_warn_node_modules_integrity", swap)
    git_commands = []
    run = subprocess.run

    def observe_git(command, *args, **kwargs):
        if command[0] == "git":
            git_commands.append(command)
        return run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observe_git)

    assert delegate.cmd_dispatch(review_args(head, dry_run=True, worktree=str(snapshot))) == 1

    output = capsys.readouterr()
    assert "changed after validation" in output.err
    assert "planned new detached snapshot" not in output.err
    assert output.out == ""
    assert not delegate._state_path("snapshot-review").exists()
    assert (outside / "retained.bin").read_bytes() == b"retained\x00\xff"
    assert len(list(outside.iterdir())) == 1
    assert repo.launches == []
    assert not any("fetch" in command[1:] for command in git_commands)
    assert not any("worktree" in command and "add" in command for command in git_commands)
