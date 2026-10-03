"""One LU_OPSEC_OVERRIDE admits at most one flagged publication per command, across processes (#9681).

Each command runs under its own bash, as an agent's command line does, with one
override and two flagged texts. The in-process publisher sends through a
recording fake gh; pushes go through a copy of the agent git shim to local bare
remotes. Outcomes are judged by what was sent: the fake's records and the
remotes' objects, never by scanner logs alone.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from tests.opsec.test_git_push_scan import REAL_GIT, _env, _git, _remote_has, push_sandbox  # noqa: F401
from tests.opsec_fixtures import CATALOG, ROOT, TOKEN

REASON = "synthetic false positive"
ANCHOR = "LU_OPSEC_OVERRIDE_ANCHOR"

# Runs one flow in a fresh interpreter: the real publishers from this checkout,
# the catalogue, matcher and override log pointed at the sandbox, and a fake gh
# that records every write (argv and frozen file payloads) instead of sending it.
DRIVER = r"""
import json, subprocess, sys
from pathlib import Path

config = json.loads(sys.argv[1])
sys.path[:0] = [config["root"], config["root"] + "/scripts"]
from scripts.opsec import prepublish as gate

gate.catalog = lambda: config["catalog"]
gate.private_tooling = lambda: Path(config["tooling"])
gate.primary_root = lambda cwd=None: Path(config["sandbox_root"])
work = Path(config["work"])
token = config["token"]
outcome = {}


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


def push(refspec):
    result = subprocess.run(["git", "push", "origin", refspec], cwd=work, capture_output=True, text=True)
    return {"status": result.returncode, "stderr": result.stderr}


flow = config["flow"]
if flow == "settle":
    from scripts.orchestration import dispatch_settle

    real = dispatch_settle.request_run
    dispatch_settle.request_run = lambda request, **kwargs: real(request, runner=fake, **kwargs)
    step("settle", lambda: dispatch_settle.push_and_maybe_open_pr(
        work, "feature", open_pr=True, title="clean title", body="body " + token))
elif flow == "finalize":
    import scripts.delegate as delegate

    real = delegate.request_run
    delegate.request_run = lambda request, **kwargs: real(request, runner=fake, **kwargs)
    step("finalize", lambda: repr(delegate._auto_finalize_dirty_worktree(
        worktree=work, task_id="impl-unit", agent=token, branch="feature", base_branch="trunk",
        open_pr=True, owned_paths=["file.txt"])))
elif flow == "publish-then-push":
    from scripts.publish.github import publish

    step("publish", lambda: publish(
        "issue-comment", repo="unit/public", number=1, body=config["body"], runner=fake, cwd=work,
        capture_output=True, text=True).returncode)
    step("push", lambda: push("HEAD:refs/heads/feature"))
elif flow == "push":
    step("push", lambda: push("HEAD:refs/heads/feature"))
print(json.dumps(outcome))
"""


def command(sandbox, argv, **extra):
    """Run argv as one command line: a fresh bash that stays its parent (no exec), as an agent's shell does."""
    env = _env(PATH=os.pathsep.join([str(sandbox.shim.parent), str(sandbox.real_git_dir), os.defpath]), **extra)
    return subprocess.run(
        ["bash", "-c", '"$@"; exit $?', "bash", *argv],
        cwd=sandbox.work,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


def drive(sandbox, flow, *, body="clean body", **extra):
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
        "flow": flow,
        "body": body,
    }
    extra.setdefault("GH_REPO", "unit/public")
    result = command(sandbox, [sys.executable, str(driver), json.dumps(config)], **extra)
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
    pushed = _remote_has(sandbox, flagged)
    assert pushed, outcome
    assert flagged_sends(sandbox) == [], outcome
    assert "override already consumed" in outcome["settle"], outcome
    assert len(log_rows(sandbox)) == 1


def test_delegate_auto_finalize_admits_one_flagged_publication(sandbox):
    """_auto_finalize_dirty_worktree: commit and child push, then the in-process draft PR."""
    (sandbox.work / "file.txt").write_text("dirty\n")
    outcome = drive(sandbox, "finalize", LU_OPSEC_OVERRIDE=REASON)
    sent_commit = _git(sandbox.work, "rev-parse", "HEAD")
    assert TOKEN in _git(sandbox.work, "log", "-1", "--format=%B")
    assert _remote_has(sandbox, sent_commit), outcome
    assert flagged_sends(sandbox) == [], outcome
    assert "override already consumed" in outcome["finalize"], outcome
    assert len(log_rows(sandbox)) == 1


def test_publisher_then_child_push_admits_one_flagged_publication(sandbox):
    """The review-9678 sequence: an in-process flagged publish, then a flagged child push."""
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "publish-then-push", body="body " + TOKEN, LU_OPSEC_OVERRIDE=REASON)
    assert outcome["publish"] == 0 and len(flagged_sends(sandbox)) == 1, outcome
    assert outcome["push"]["status"] != 0 and "override already consumed" in outcome["push"]["stderr"], outcome
    assert not _remote_has(sandbox, flagged)
    assert len(log_rows(sandbox)) == 1


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


# --- Command scope: a fresh command, a forged anchor, clean publishes ---


def test_a_second_command_with_the_same_reason_gets_its_own_override(sandbox):
    first = sandbox.commit("first " + TOKEN)
    outcome = drive(sandbox, "publish-then-push", body="body " + TOKEN, LU_OPSEC_OVERRIDE=REASON)
    assert outcome["push"]["status"] != 0 and not _remote_has(sandbox, first), outcome
    outcome = drive(sandbox, "push", LU_OPSEC_OVERRIDE=REASON)
    assert outcome["push"]["status"] == 0 and _remote_has(sandbox, first), outcome
    assert len(log_rows(sandbox)) == 2


def test_a_forged_anchor_naming_a_process_outside_the_command_claims_nothing(sandbox):
    """Setting the carried anchor to another live process does not mint a new claim."""
    flagged = sandbox.commit("subject " + TOKEN)
    with subprocess.Popen(["sleep", "60"]) as outsider:
        try:
            outcome = drive(
                sandbox,
                "publish-then-push",
                body="body " + TOKEN,
                LU_OPSEC_OVERRIDE=REASON,
                **{ANCHOR: f"{outsider.pid}:{REASON}"},
            )
        finally:
            outsider.kill()
    assert "override anchor" in str(outcome["publish"]), outcome
    assert "override anchor" in outcome["push"]["stderr"], outcome
    assert flagged_sends(sandbox) == [] and not _remote_has(sandbox, flagged)
    assert log_rows(sandbox) == [] and not list((sandbox.root / "batch_state/opsec").glob("consumed-*"))


def test_clean_publish_and_push_under_an_override_claim_nothing(sandbox):
    clean = sandbox.commit("clean subject")
    outcome = drive(sandbox, "publish-then-push", body="clean body", LU_OPSEC_OVERRIDE=REASON)
    assert outcome["publish"] == 0 and outcome["push"]["status"] == 0, outcome
    assert _remote_has(sandbox, clean) and sandbox.sent.exists()
    assert not (sandbox.root / "batch_state/opsec").exists()


def test_the_hook_claims_for_the_carried_anchor_without_a_process_lookup(monkeypatch):
    from scripts.opsec import git_push

    monkeypatch.setattr(git_push.subprocess, "run", lambda *a, **k: pytest.fail("looked up the caller"))
    assert git_push.claimant({ANCHOR: f"4242:{REASON}"}, REASON) == 4242


def test_the_shim_replaces_an_anchor_carried_for_another_reason(sandbox):
    """A stale anchor names nothing: the push claims for its own caller, so the flagged push is admitted once."""
    flagged = sandbox.commit("subject " + TOKEN)
    outcome = drive(sandbox, "push", LU_OPSEC_OVERRIDE=REASON, **{ANCHOR: "1:another reason"})
    assert outcome["push"]["status"] == 0 and _remote_has(sandbox, flagged), outcome
    assert len(log_rows(sandbox)) == 1
