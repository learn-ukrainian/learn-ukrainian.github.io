"""#12378 under REVIEW-BOUNDARY-1101: review execution exists only inside the read-only boundary.

Read-only AGY runs whole inside it; read-only native Claude runs each Bash command inside it.
"""

import ipaddress
import json
import os
import shutil
import subprocess

import pytest

from scripts.agent_runtime.attempt_network import load_allowlist
from scripts.common.repo_root import project_interpreter
from scripts.dispatcher import agy_sandbox
from tests.dispatcher.test_providers_b import _bwrap_usable, _launch, _linked_worktree


def test_review_checkout_exposes_project_interpreter(tmp_path):
    """Defect: literal .venv/bin/python is missing or an existing foreign interpreter is replaced."""
    worktree, head = _linked_worktree(tmp_path)
    assert agy_sandbox._link_interpreter(worktree) is True
    result = subprocess.run([str(worktree / ".venv/bin/python"), "-c", "print('review-interpreter-ok')"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "review-interpreter-ok\n"
    assert agy_sandbox._link_interpreter(worktree) is False  # the project link is kept, not recreated
    assert agy_sandbox._input_state(worktree) == {"head": head, "clean": True}
    untracked = worktree / ".venv-other"
    untracked.write_text("not the interpreter\n")
    assert agy_sandbox._input_state(worktree) == {"head": head, "clean": False}
    untracked.unlink()
    (worktree / "README.md").write_text("changed\n")
    assert agy_sandbox._input_state(worktree) == {"head": head, "clean": False}
    subprocess.run(["git", "-C", str(worktree), "add", "README.md"], check=True, timeout=30)
    assert agy_sandbox._input_state(worktree) == {"head": head, "clean": False}
    subprocess.run(["git", "-C", str(worktree), "restore", "--staged", "--worktree", "README.md"],
                   check=True, timeout=30)
    subprocess.run(["git", "-C", str(worktree), "add", ".venv"], check=True, timeout=30)
    assert agy_sandbox._input_state(worktree) == {"head": head, "clean": False}
    other = tmp_path / "foreign"
    other.mkdir()
    (other / ".venv").mkdir()
    with pytest.raises(ValueError, match="not the project interpreter"):
        agy_sandbox._link_interpreter(other)
    assert (other / ".venv").is_dir() and not (other / ".venv").is_symlink()
    (other / ".venv").rmdir()
    (other / ".venv").symlink_to(tmp_path)
    with pytest.raises(ValueError, match="not the project interpreter"):
        agy_sandbox._link_interpreter(other)


@pytest.mark.skipif(not _bwrap_usable(), reason="needs a usable unprivileged bubblewrap")
def test_second_shell_command_runs_when_repo_does_not_ignore_venv(tmp_path):
    """Defect class: the boundary's own interpreter link refuses later shell commands."""
    worktree, head = _linked_worktree(tmp_path)
    task_id = "repeated-shell"
    for index, command in enumerate(("git rev-parse HEAD", "git diff HEAD", ".venv/bin/python -c 'print(42)'")):
        argv, env, _cwd_file = _claude_shell(tmp_path, worktree, task_id, command)
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60, check=False, cwd=worktree)
        assert run.returncode == 0, run.stdout + run.stderr
        assert run.stdout == (head + "\n" if index == 0 else "" if index == 1 else "42\n")
    receipts = [json.loads(line) for line in (tmp_path / f"{task_id}.shell.jsonl").read_text().splitlines()]
    assert len(receipts) == 3
    for receipt in receipts:
        assert receipt["status"] == "ran" and receipt["canary_passed"] is True
        assert receipt["input"] == {"start": {"head": head, "clean": True}, "end": {"head": head, "clean": True}}
    assert (worktree / ".venv").resolve() == project_interpreter().parent.parent.resolve()
    assert subprocess.run(["git", "-C", str(worktree), "status", "--porcelain=v1"], check=True,
                          capture_output=True, text=True, timeout=30).stdout == "?? .venv\n"
    assert subprocess.run(["git", "-C", str(worktree), "diff", "HEAD", "--exit-code"],
                          check=False, timeout=30).returncode == 0


_PY = ".venv/bin/python"
_GIT_ID = "'-c','user.email=s@example.invalid','-c','user.name=S'"
# Each Grok cf-12404-grok-r1 bypass class (F1 publication and primary write, F2 private egress) must
# fail inside the boundary; the granted capabilities must work. "{remote}" and "{primary}" are host
# paths filled in per run; {metadata} is the link-local cloud metadata address and {private} an
# RFC 1918 address, built from integers at run time. The fetch case stands in for any in-sandbox fetcher, such as AGY's web tool.
_CASES = {
    "F1-python-git-push": (False, f"{_PY} -c \"import subprocess,sys; "
                                  f"sys.exit(subprocess.run(['git','push','{{remote}}','HEAD:refs/heads/pwned']).returncode)\""),
    "F1-python-git-commit": (False, f"{_PY} -c \"import subprocess,sys; sys.exit(subprocess.run(['git',{_GIT_ID},"
                                    "'commit','--allow-empty','-qm','x']).returncode)\""),
    # zsh where installed; otherwise another shell than the sh the launcher runs, so -c still nests.
    "F1-zsh-git-push": (False, "$(command -v zsh || command -v dash || command -v bash) -c "
                               "'git push {remote} HEAD:refs/heads/pwned'"),
    "F1-sh-git-push-github": (False, "git push https://github.com/example/repo.git HEAD:refs/heads/pwned"),
    "F1-curl-github-api-post": (False, "curl -sS --max-time 10 -X POST https://api.github.com/repos/example/repo/pulls/1/merge"),
    "F1-python-primary-write": (False, f"{_PY} -c \"open('{{primary}}/review-mutation-probe','w').write('x')\""),
    "F2-curl-metadata-proxy": (False, "curl -sS --max-time 10 https://{metadata}/latest/meta-data/"),
    "F2-curl-metadata-direct": (False, "curl -sS --noproxy '*' --max-time 5 http://{metadata}/latest/meta-data/"),
    "F2-curl-rfc1918-proxy": (False, "curl -sS --max-time 10 https://{private}/"),
    "F2-curl-rfc1918-direct": (False, "curl -sS --noproxy '*' --max-time 5 http://{private}/"),
    "F2-fetch-metadata": (False, f"{_PY} -c \"import urllib.request as u; "
                                 "u.urlopen('https://{metadata}/latest/meta-data/', timeout=10)\""),
    # GitHub writes through gh: native Claude's gh relay refuses them; AGY's sandbox has no gh login.
    "F1-gh-pr-merge": (False, "gh pr merge 1 --squash"),
    "F1-gh-api-post": (False, "gh api -X POST repos/example/repo/issues -f title=x"),
    "F1-gh-pr-view-web": (False, "gh pr view 1 -cw"),
    # Destination selectors: the host's gh would connect to them outside the boundary (cf-12521-sol-r1 F1).
    "F2-gh-repo-host": (False, "gh pr view 1 --repo localhost:9/a/b --json number"),
    "F2-gh-url-operand": (False, "gh issue view https://localhost:9/a/b/issues/1"),
    "granted-shell-scratch": (True, "echo ok > \"$TMPDIR/probe\" && cat \"$TMPDIR/probe\""),
    "granted-interpreter": (True, f"{_PY} -c \"import pytest; print('interpreter-ok')\""),
    "granted-named-test": (True, f"{_PY} -m pytest -q -p no:cacheprovider test_probe.py"),
    "granted-project-scratch": (True, f"{_PY} -c \"import os, tempfile; "
                                      "tempfile.TemporaryDirectory(dir=os.environ['LU_SCRATCH_ROOT']).cleanup()\""),
}


# Claude Code's prefix wrapper ends this way; the boundary must return the working-directory record.
_CLAUDE_WRAPPER = "source /nonexistent/snapshot.sh 2>/dev/null || true && eval {command} < /dev/null && pwd -P >| {cwd_file}"


def _claude_shell(tmp_path, worktree, task_id, command, prefix=agy_sandbox.SHELL_PREFIX):
    """Run ``command`` the way Claude Code runs a Bash call under CLAUDE_CODE_SHELL_PREFIX."""
    claude_tmp = tmp_path / "claude-tmp"
    claude_tmp.mkdir(exist_ok=True)
    cwd_file = claude_tmp / "claude-ab12-cwd"
    script = _CLAUDE_WRAPPER.format(command="'" + command.replace("'", "'\\''") + "'", cwd_file=cwd_file)
    env = {**os.environ, "CLAUDE_CODE_TMPDIR": str(claude_tmp),
           agy_sandbox.SHELL_ENV_PYTHON: str(project_interpreter()), agy_sandbox.SHELL_ENV_TASK: task_id,
           agy_sandbox.SHELL_ENV_WORKTREE: str(worktree), agy_sandbox.SHELL_ENV_LOG: str(tmp_path / f"{task_id}.shell.jsonl")}
    return [str(prefix), script], env, cwd_file


def _claude_receipt(tmp_path, task_id):
    lines = (tmp_path / f"{task_id}.shell.jsonl").read_text().splitlines()
    assert len(lines) == 1
    receipt = json.loads(lines[0])
    receipt["canary"] = {"passed": receipt.pop("canary_passed")}
    return receipt


# Claude's shell prefix must load boundary code only from the dispatcher checkout it really lives in.
_PREFIX_CASES = {"F3-prefix-root-not-checkout": "root_not_checkout",
                 "F3-prefix-root-is-reviewed-worktree": "root_is_reviewed_worktree"}


@pytest.mark.skipif(not _bwrap_usable(), reason="needs a usable unprivileged bubblewrap")
@pytest.mark.parametrize("route,case", [*((route, case) for route in ("agy", "claude") for case in sorted(_CASES)),
                                        *(("claude", case) for case in _PREFIX_CASES)])
def test_review_boundary_refuses_bypass_classes_and_keeps_execution(tmp_path, route, case):
    """Defect: a review shell or interpreter publishes, writes the primary checkout or reaches a private address."""
    worktree, _head = _linked_worktree(tmp_path)
    if case in _PREFIX_CASES:
        base = tmp_path / "loose" if case == "F3-prefix-root-not-checkout" else worktree
        prefix = base / "scripts" / "dispatcher" / "claude_review_shell"
        prefix.parent.mkdir(parents=True)
        shutil.copy2(agy_sandbox.SHELL_PREFIX, prefix)
        marker = tmp_path / "ran"
        argv, env, _cwd_file = _claude_shell(tmp_path, worktree, "prefix", f"touch {marker}", prefix=prefix)
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60, check=False, cwd=worktree)
        assert (run.returncode, run.stderr) == (
            125, f"claude read-only boundary refused: claude_review_shell_{_PREFIX_CASES[case]}\n")
        assert not marker.exists()
        return
    granted, template = _CASES[case]
    primary = tmp_path / "repo"
    (worktree / "test_probe.py").write_text("def test_probe():\n    assert 1 + 1 == 2\n")
    subprocess.run(["git", "-C", str(worktree), "add", "test_probe.py"], check=True, timeout=30)
    subprocess.run(["git", "-C", str(worktree), "-c", "user.email=s@example.invalid", "-c", "user.name=S",
                    "commit", "-qm", "probe"], check=True, timeout=30)
    head = subprocess.run(["git", "-C", str(worktree), "rev-parse", "HEAD"], check=True, capture_output=True,
                          text=True, timeout=30).stdout.strip()
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True, timeout=30)
    command = template.format(remote=remote, primary=primary, metadata=ipaddress.ip_address(2852039166),
                              private=ipaddress.ip_address(167772161))
    scratches = set(agy_sandbox.ensure_scratch_root().glob("claude-shell-*"))
    if route == "agy":
        argv, env = _launch(tmp_path, worktree, "adversarial", ["/bin/sh", "-c", command])
    else:
        argv, env, cwd_file = _claude_shell(tmp_path, worktree, "adversarial", command)
    run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=180, check=False, cwd=worktree)
    if route == "agy":
        receipt = json.loads((tmp_path / "adversarial.sandbox.json").read_text())
    else:
        receipt = _claude_receipt(tmp_path, "adversarial")
    assert receipt["status"] == "ran" and receipt["canary"]["passed"] is True, (receipt.get("reason"), run.stderr)
    if granted:
        assert run.returncode == 0, run.stdout + run.stderr
    else:
        assert run.returncode != 0, run.stdout + run.stderr
    # Outcome checks on the host, independent of the command's own exit status.
    assert subprocess.run(["git", "-C", str(remote), "for-each-ref"], check=True, capture_output=True, text=True,
                          timeout=30).stdout == ""
    assert receipt["input"] == {"start": {"head": head, "clean": True}, "end": {"head": head, "clean": True}}
    assert not (primary / "review-mutation-probe").exists()
    if route == "agy":
        assert not (worktree / ".venv").exists()  # the boundary removes the link it created
        allowlist = load_allowlist("agy")
        assert all(record["destination"].split(":")[0] in allowlist for record in receipt.get("egress", []))
    else:
        # The shell has no network and no egress proxy; the link stays for the run's next command.
        assert "egress" not in receipt
        assert (worktree / ".venv").resolve() == project_interpreter().parent.parent.resolve()
        assert set(agy_sandbox.ensure_scratch_root().glob("claude-shell-*")) <= scratches  # removed with the command
        if "-gh-" in case:  # the relay itself refused, not gh failing afterwards (cf-12521-sol-r2 F2)
            assert receipt["gh"][0]["refused"] and "review boundary: " in run.stderr
        if granted:
            assert cwd_file.read_text().strip() == str(worktree.resolve())
