"""One LU_OPSEC_OVERRIDE admits at most one flagged publication per command, across processes (#9681).

Each command runs under its own bash, as an agent's command line does: the
line itself sets the override, then runs a driver that publishes two flagged
texts in some order. The in-process publisher sends through a recording fake
gh; pushes go through a copy of the agent git shim to local bare remotes.
Outcomes are judged by what was sent: the fake's records and the remotes'
objects, never by scanner logs alone.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from scripts.opsec import prepublish as gate
from scripts.publish import github as pub
from tests.opsec.test_git_push_scan import REAL_GIT, _env, _git, _remote_has, push_sandbox  # noqa: F401
from tests.opsec_fixtures import CATALOG, ROOT, TOKEN

REASON = "synthetic: false positive"

# Runs one flow in a fresh interpreter: the real publishers from this checkout,
# the catalogue, matcher and override log pointed at the sandbox, and a fake gh
# that records every write (argv and frozen file payloads) instead of sending it.
# The publisher is imported only when a step first needs it.
DRIVER = r"""
import json, os, subprocess, sys
from pathlib import Path

config = json.loads(sys.argv[1])
sys.path[:0] = [config["root"], config["root"] + "/scripts"]
work = Path(config["work"])
token = config["token"]
outcome = {"pid": os.getpid()}


def gate():
    from scripts.opsec import prepublish

    prepublish.catalog = lambda: config["catalog"]
    prepublish.private_tooling = lambda: Path(config["tooling"])
    prepublish.primary_root = lambda cwd=None: Path(config["sandbox_root"])
    return prepublish


def fake(argv, **kwargs):
    argv = [str(arg) for arg in argv]
    if Path(argv[0]).name != "gh":
        return subprocess.run(argv, **kwargs)
    if argv[1:3] == ["pr", "list"]:
        out = ""
    elif argv[1:3] == ["repo", "view"]:
        out = json.dumps({"defaultBranchRef": {"name": "trunk"}})
    else:
        files = [Path(argv[i + 1]).read_text() for i, arg in enumerate(argv[:-1]) if arg.endswith("-file")]
        with open(config["sent"], "a") as sent:
            sent.write(json.dumps({"argv": argv, "files": files}) + "\n")
        out = "https://github.com/unit/public/pull/1\n"
    text = kwargs.get("text")
    return subprocess.CompletedProcess(argv, 0, out if text else out.encode(), "" if text else b"")


def step(name, function):
    try:
        outcome[name] = function()
    except Exception as exc:
        outcome[name] = f"raised {type(exc).__name__}: {exc}"


def push():
    result = subprocess.run(["git", "push", "origin", "HEAD:refs/heads/feature"], cwd=work, capture_output=True, text=True)
    return {"status": result.returncode, "stderr": result.stderr}


def comment():
    gate()
    from scripts.publish.github import publish

    return publish(
        "issue-comment", repo="unit/public", number=1, body=config["body"], runner=fake, cwd=work,
        capture_output=True, text=True).returncode


def child_comment():
    child = dict(config, steps=["comment"])
    result = subprocess.run([sys.executable, sys.argv[0], json.dumps(child)], capture_output=True, text=True)
    return json.loads(result.stdout)["comment"]


def set_override():
    gate()
    os.environ["LU_OPSEC_OVERRIDE"] = config["reason"]


def imported():
    return "scripts.opsec.prepublish" in sys.modules


for name in config["steps"]:
    if name == "settle":
        from scripts.orchestration import dispatch_settle

        gate()
        real = dispatch_settle.request_run
        dispatch_settle.request_run = lambda request, **kwargs: real(request, runner=fake, **kwargs)
        step("settle", lambda: dispatch_settle.push_and_maybe_open_pr(
            work, "feature", open_pr=True, title="clean title", body="body " + token))
    elif name == "finalize":
        import scripts.delegate as delegate

        gate()
        real = delegate.request_run
        delegate.request_run = lambda request, **kwargs: real(request, runner=fake, **kwargs)
        # A task record in the sandbox, so the gate's reason lands in its local diagnostic file (#9878).
        delegate.tasks_dir = lambda: Path(config["sandbox_root"]) / "batch_state" / "tasks"
        delegate._write_state_atomic(delegate._state_path("impl-unit"), {"task_id": "impl-unit"})
        step("finalize", lambda: repr(delegate._auto_finalize_dirty_worktree(
            worktree=work, task_id="impl-unit", agent=token, branch="feature", base_branch="trunk",
            open_pr=True, owned_paths=["file.txt"])))
        diag = delegate._diagnostic_path("impl-unit")
        outcome["finalize_diag"] = diag.read_text(encoding="utf-8") if diag.exists() else ""
    else:
        step(name, {"push": push, "comment": comment, "child_comment": child_comment,
                    "set_override": set_override, "imported": imported}[name])
print(json.dumps(outcome))
"""


def command(sandbox, argv, **extra):
    """Run argv as one command line: a fresh bash that stays its parent (no exec), as an agent's shell does.

    An LU_OPSEC_OVERRIDE in extra is set by the command line itself, as an
    agent writes it, not inherited by the shell.
    """
    override = extra.pop("LU_OPSEC_OVERRIDE", None)
    line = ('export LU_OPSEC_OVERRIDE="$1"; ' if override is not None else "") + 'shift; "$@"; exit $?'
    env = _env(PATH=os.pathsep.join([str(sandbox.shim.parent), str(sandbox.real_git_dir), os.defpath]), **extra)
    return subprocess.run(
        ["bash", "-c", line, "bash", override or "", *argv],
        cwd=sandbox.work,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


def driver_config(sandbox, steps, body):
    driver = sandbox.tmp / "driver.py"
    driver.write_text(DRIVER)
    config = {
        "root": str(ROOT),
        "catalog": CATALOG,
        "tooling": str(sandbox.tooling),
        "sandbox_root": str(sandbox.root),
        "work": str(sandbox.work),
        "sent": str(sandbox.sent),
        "token": TOKEN,
        "steps": steps,
        "body": body,
        "reason": REASON,
    }
    return str(driver), json.dumps(config)


def drive(sandbox, *steps, body="clean body", **extra):
    extra.setdefault("GH_REPO", "unit/public")
    result = command(sandbox, [sys.executable, *driver_config(sandbox, list(steps), body)], **extra)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def log_rows(sandbox):
    log = sandbox.root / "batch_state/opsec/overrides.jsonl"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def flagged_sends(sandbox):
    """gh writes whose argv or frozen payload carried the flagged text."""
    if not sandbox.sent.exists():
        return []
    return [row for row in map(json.loads, sandbox.sent.read_text().splitlines()) if TOKEN in json.dumps(row)]


def assert_one_flagged_publication(sandbox, flagged_commit, outcome):
    """Exactly one of the flagged comment and the flagged push was sent, and one override was logged."""
    published = len(flagged_sends(sandbox)) + _remote_has(sandbox, flagged_commit)
    assert published == 1, outcome
    assert "override already consumed" in json.dumps(outcome), outcome
    rows = log_rows(sandbox)
    assert len(rows) == 1 and rows[0]["reason"] == REASON, rows


@pytest.fixture
def sandbox(push_sandbox):  # noqa: F811
    push_sandbox.sent = push_sandbox.tmp / "sent.jsonl"
    push_sandbox.real_git_dir = os.path.dirname(REAL_GIT)
    _git(push_sandbox.work, "checkout", "-q", "-b", "feature")
    return push_sandbox


# --- Reproduction per multi-process flow: one override, two flagged texts ---


def test_dispatch_settle_push_then_pr_admits_one_flagged_publication(sandbox):
    """push_and_maybe_open_pr: a child push (hook) and then the in-process typed publisher."""
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "settle", LU_OPSEC_OVERRIDE=REASON)
    assert _remote_has(sandbox, flagged), outcome
    assert flagged_sends(sandbox) == [], outcome
    assert "override already consumed" in outcome["settle"], outcome
    assert len(log_rows(sandbox)) == 1


def test_delegate_auto_finalize_admits_one_flagged_publication(sandbox):
    """_auto_finalize_dirty_worktree: commit and child push, then the in-process draft PR."""
    # This publication test crosses the real validation boundary too. Supply
    # committed gate inputs and the canonical base ref in its synthetic repo.
    _git(sandbox.work, "update-ref", "refs/remotes/origin/main", "trunk")
    (sandbox.work / "scripts/ci").mkdir(parents=True)
    (sandbox.work / "tests").mkdir()
    (sandbox.work / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    (sandbox.work / "scripts/ci/push_invariants.json").write_text(json.dumps({
        "schema_version": 1, "modules": ["tests/test_gate.py"], "node_ids": [],
    }))
    (sandbox.work / "tests/test_gate.py").write_text(
        "from pathlib import Path\ndef test_outgoing_file():\n    assert Path('file.txt').read_text() == 'dirty\\n'\n"
    )
    (sandbox.work / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n      - id: diff-check\n        name: diff check\n"
        "        entry: git diff --check\n        language: system\n        pass_filenames: false\n"
        "        stages: [pre-push]\n"
    )
    _git(sandbox.work, "add", "-A")
    _git(sandbox.work, "commit", "-m", "gate fixture")
    (sandbox.work / "file.txt").write_text("dirty\n")
    outcome = drive(sandbox, "finalize", LU_OPSEC_OVERRIDE=REASON)
    sent_commit = _git(sandbox.work, "rev-parse", "HEAD")
    assert TOKEN in _git(sandbox.work, "log", "-1", "--format=%B")
    assert _remote_has(sandbox, sent_commit), outcome
    assert flagged_sends(sandbox) == [], outcome
    # #9878: the result names the typed cause; the gate's own reason is kept in the local diagnostic.
    assert "auto_finalize_publish_blocked" in outcome["finalize"], outcome
    assert "override already consumed" not in outcome["finalize"], outcome
    assert "override already consumed" in outcome["finalize_diag"], outcome
    assert len(log_rows(sandbox)) == 1


# --- Every order of publication, import and override within one command ---


def test_publisher_then_child_push_admits_one_flagged_publication(sandbox):
    """The review-9678 sequence: an in-process flagged publish, then a flagged child push."""
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "comment", "push", body="body " + TOKEN, LU_OPSEC_OVERRIDE=REASON)
    assert outcome["comment"] == 0 and len(flagged_sends(sandbox)) == 1, outcome
    assert outcome["push"]["status"] != 0 and "override already consumed" in outcome["push"]["stderr"], outcome
    assert_one_flagged_publication(sandbox, flagged, outcome)


def test_push_before_the_publisher_is_imported_then_a_comment(sandbox):
    """Review-9681 F1: a flagged push, then a lazy publisher import and a flagged comment."""
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "imported", "push", "comment", body="body " + TOKEN, LU_OPSEC_OVERRIDE=REASON)
    assert outcome["imported"] is False and outcome["push"]["status"] == 0, outcome
    assert "override already consumed" in outcome["comment"], outcome
    assert_one_flagged_publication(sandbox, flagged, outcome)


def test_override_set_after_import_then_a_comment_and_a_push(sandbox):
    """Review-9681 F1: the publisher is imported, the override set in-process, then a comment and a push."""
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "set_override", "comment", "push", body="body " + TOKEN)
    assert outcome["comment"] == 0, outcome
    assert outcome["push"]["status"] != 0 and "override already consumed" in outcome["push"]["stderr"], outcome
    assert_one_flagged_publication(sandbox, flagged, outcome)


def test_override_set_after_import_then_a_push_and_a_comment(sandbox):
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "set_override", "push", "comment", body="body " + TOKEN)
    assert outcome["push"]["status"] == 0 and "override already consumed" in outcome["comment"], outcome
    assert_one_flagged_publication(sandbox, flagged, outcome)


def test_a_child_process_comment_then_the_parents_push(sandbox):
    """A publisher in a child process claims for the same command as its parent's push."""
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "child_comment", "push", body="body " + TOKEN, LU_OPSEC_OVERRIDE=REASON)
    assert outcome["child_comment"] == 0, outcome
    assert outcome["push"]["status"] != 0 and "override already consumed" in outcome["push"]["stderr"], outcome
    assert_one_flagged_publication(sandbox, flagged, outcome)


def test_two_programs_of_one_command_line_share_the_override(sandbox):
    """`export ...; publish; push`: bash runs the last program in place of itself, which must not mint a new use."""
    flagged = sandbox.commit("subject " + TOKEN)
    driver, comment = driver_config(sandbox, ["comment"], "body " + TOKEN)
    _, push = driver_config(sandbox, ["push"], "body " + TOKEN)
    # The inner bash sets the override and runs the push program in place of itself.
    line = 'export LU_OPSEC_OVERRIDE="$5"; echo "$$"; "$1" "$2" "$3"; "$1" "$2" "$4"'
    result = command(
        sandbox,
        ["bash", "-c", line, "bash", sys.executable, driver, comment, push, REASON],
        GH_REPO="unit/public",
    )
    shell, *rows = result.stdout.strip().splitlines()
    outcomes = [json.loads(row) for row in rows]
    assert outcomes[1]["pid"] == int(shell), outcomes  # The push program replaced the shell.
    assert outcomes[0]["comment"] == 0, outcomes
    assert outcomes[1]["push"]["status"] != 0, outcomes
    assert_one_flagged_publication(sandbox, flagged, outcomes)


def _submodule(sandbox):
    """A submodule with its own bare remote, recorded in the superproject and pushed clean."""
    allow = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "protocol.file.allow", "GIT_CONFIG_VALUE_0": "always"}
    remote = sandbox.tmp / "sub-remote.git"
    _git(sandbox.tmp, "init", "-q", "--bare", "-b", "trunk", str(remote))
    seed = sandbox.tmp / "sub-seed"
    _git(sandbox.tmp, "init", "-q", "-b", "trunk", str(seed))
    _git(
        seed,
        "-c",
        "user.email=unit@example.invalid",
        "-c",
        "user.name=unit",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "sub base",
    )
    _git(seed, "push", "-q", str(remote), "trunk")
    _git(sandbox.work, "submodule", "add", "-q", str(remote), "sub", env=_env(**allow))
    _git(sandbox.work, "commit", "-q", "-m", "add clean submodule")
    sub = sandbox.work / "sub"
    _git(sub, "config", "user.email", "unit@example.invalid")
    _git(sub, "config", "user.name", "unit")
    _git(sub, "checkout", "-q", "-b", "feature")  # On-demand pushes the superproject's branch name.
    return remote, sub, allow


def test_recursive_submodule_push_admits_one_flagged_publication(sandbox):
    """git push --recurse-submodules=on-demand: the submodule's hook and the superproject's hook."""
    remote, sub, allow = _submodule(sandbox)
    _git(sub, "commit", "-q", "--allow-empty", "-m", "sub subject " + TOKEN)
    sub_commit = _git(sub, "rev-parse", "HEAD")
    _git(sandbox.work, "add", "sub")
    super_commit = sandbox.commit("super subject " + TOKEN)
    result = command(
        sandbox,
        [str(sandbox.shim), "push", "--recurse-submodules=on-demand", "origin", "HEAD:refs/heads/feature"],
        LU_OPSEC_OVERRIDE=REASON,
        **allow,
    )
    # Git runs the superproject's pre-push hook first, which claims; the submodule
    # push is then refused and Git aborts the superproject push too.
    sent = [_remote_has(sandbox, sub_commit, remote), _remote_has(sandbox, super_commit)]
    assert sent.count(True) <= 1, result.stderr
    assert result.returncode != 0 and "override already consumed" in result.stderr, result.stderr
    assert len(log_rows(sandbox)) == 1


# --- Command scope: a fresh command, clean publishes ---


def test_a_second_command_with_the_same_reason_gets_its_own_override(sandbox):
    first = sandbox.commit("first " + TOKEN)
    outcome = drive(sandbox, "comment", "push", body="body " + TOKEN, LU_OPSEC_OVERRIDE=REASON)
    assert outcome["push"]["status"] != 0 and not _remote_has(sandbox, first), outcome
    outcome = drive(sandbox, "push", LU_OPSEC_OVERRIDE=REASON)
    assert outcome["push"]["status"] == 0 and _remote_has(sandbox, first), outcome
    assert len(log_rows(sandbox)) == 2


def test_clean_publish_and_push_under_an_override_claim_nothing(sandbox):
    clean = sandbox.commit("clean subject")
    outcome = drive(sandbox, "comment", "push", body="clean body", LU_OPSEC_OVERRIDE=REASON)
    assert outcome["comment"] == 0 and outcome["push"]["status"] == 0, outcome
    assert _remote_has(sandbox, clean) and sandbox.sent.exists()
    assert not (sandbox.root / "batch_state/opsec").exists()


# --- Only claimants receive the override (review-9681 F2) ---

# Records whether the override reached each Git the shim, the scanner and the
# hook chain run, then runs the real Git.
RECORDING_GIT = """#!/bin/sh
printf '%s\\t%s\\n' "$(env | grep -c '^LU_OPSEC_OVERRIDE')" "$*" >> "{log}"
exec "{git}" "$@"
"""
RECORDING_HOOK = """#!/bin/sh
env | grep '^LU_OPSEC_OVERRIDE' > "{log}.{name}"
cat > /dev/null
exit 0
"""


@pytest.mark.parametrize("subject", ["clean subject", "subject " + TOKEN])
def test_git_lookups_and_the_callers_hooks_receive_no_override(sandbox, subject):
    log = sandbox.tmp / "git-calls"
    wrapper = sandbox.tmp / "recording-git"
    wrapper.write_text(RECORDING_GIT.format(log=log, git=REAL_GIT))
    wrapper.chmod(0o755)
    hooks = sandbox.work / ".git/hooks"
    for name in ("pre-push", "reference-transaction"):
        (hooks / name).write_text(RECORDING_HOOK.format(log=sandbox.tmp / "hook", name=name))
        (hooks / name).chmod(0o755)
    sha = sandbox.commit(subject)
    result = command(
        sandbox, [str(sandbox.shim), "push", "origin", "feature"], LU_OPSEC_OVERRIDE=REASON, AGENT_REAL_GIT=str(wrapper)
    )
    assert result.returncode == 0 and _remote_has(sandbox, sha), result.stderr
    calls = [line.split("\t", 1) for line in log.read_text().splitlines()]
    receiving = [argv for count, argv in calls if count != "0"]
    # Only the push itself, the claimant's ancestor, receives it; every lookup ran without it.
    assert receiving == [f"-c core.hooksPath={sandbox.root}/scripts/opsec/push_hooks push origin feature"], calls
    assert len(calls) > 5, calls
    for name in ("pre-push", "reference-transaction"):
        assert (sandbox.tmp / f"hook.{name}").read_text() == "", name
    assert len(log_rows(sandbox)) == (TOKEN in subject)


def test_merge_readiness_reads_and_the_merge_receive_no_override(synthetic_opsec, monkeypatch, tmp_path):
    """pr-merge: gh reads before the scan, and the write after the override is claimed."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: tmp_path)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    head = "a" * 40
    calls = []

    def runner(args, **kwargs):
        calls.append((args[:3], kwargs["env"]))
        if args[:3] == ["gh", "pr", "view"]:
            out = json.dumps({"number": 1, "isDraft": False, "headRefOid": head})
        elif args[:3] == ["gh", "pr", "checks"]:
            out = "[]"
        elif args[:2] == ["gh", "api"]:
            pull = {
                "headRefOid": head,
                "isMergeQueueEnabled": False,
                "viewerMergeHeadlineText": "clean (#1)",
                "viewerMergeBodyText": "* " + TOKEN,
            }
            out = json.dumps({"data": {"repository": {"pullRequest": pull}}})
        else:
            out = ""
        return subprocess.CompletedProcess(args, 0, out, "")

    env = {**os.environ, gate.OVERRIDE: REASON}
    pub.publish("pr-merge", repo="unit/public", number=1, runner=runner, env=env)
    assert [argv for argv, _ in calls][-1] == ["gh", "pr", "merge"] and len(calls) >= 3, calls
    for argv, environment in calls:
        assert not any(key.startswith(gate.OVERRIDE) for key in environment), argv
    assert len((tmp_path / "batch_state/opsec/overrides.jsonl").read_text().splitlines()) == 1
