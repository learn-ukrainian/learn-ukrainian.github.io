"""#12378 under REVIEW-BOUNDARY-1101: review execution exists only inside the AGY read-only boundary."""

import ipaddress
import json
import subprocess

import pytest

from scripts.agent_runtime.attempt_network import load_allowlist
from scripts.dispatcher import agy_sandbox
from tests.dispatcher.test_providers_b import _bwrap_usable, _launch, _linked_worktree


def test_review_checkout_exposes_project_interpreter(tmp_path):
    """Defect: literal .venv/bin/python is missing or an existing foreign interpreter is replaced."""
    assert agy_sandbox._link_interpreter(tmp_path) is True
    result = subprocess.run([str(tmp_path / ".venv/bin/python"), "-c", "print('review-interpreter-ok')"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "review-interpreter-ok\n"
    assert agy_sandbox._link_interpreter(tmp_path) is False  # the project link is kept, not recreated
    other = tmp_path / "foreign"
    other.mkdir()
    (other / ".venv").mkdir()
    with pytest.raises(ValueError, match="not the project interpreter"):
        agy_sandbox._link_interpreter(other)
    assert (other / ".venv").is_dir() and not (other / ".venv").is_symlink()


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
    "granted-shell-scratch": (True, "echo ok > \"$TMPDIR/probe\" && cat \"$TMPDIR/probe\""),
    "granted-interpreter": (True, f"{_PY} -c \"import pytest; print('interpreter-ok')\""),
    "granted-named-test": (True, f"{_PY} -m pytest -q -p no:cacheprovider test_probe.py"),
    "granted-project-scratch": (True, f"{_PY} -c \"import os, tempfile; "
                                      "tempfile.TemporaryDirectory(dir=os.environ['LU_SCRATCH_ROOT']).cleanup()\""),
}


@pytest.mark.skipif(not _bwrap_usable(), reason="needs a usable unprivileged bubblewrap")
@pytest.mark.parametrize("case", sorted(_CASES))
def test_agy_review_boundary_refuses_bypass_classes_and_keeps_execution(tmp_path, case):
    """Defect: a review shell or interpreter publishes, writes the primary checkout or reaches a private address."""
    granted, template = _CASES[case]
    worktree, _head = _linked_worktree(tmp_path)
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
    argv, env = _launch(tmp_path, worktree, "adversarial", ["/bin/sh", "-c", command])
    run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=180, check=False, cwd=worktree)
    receipt = json.loads((tmp_path / "adversarial.sandbox.json").read_text())
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
    assert not (worktree / ".venv").exists()  # the boundary removes the link it created
    allowlist = load_allowlist("agy")
    assert all(record["destination"].split(":")[0] in allowlist for record in receipt.get("egress", []))
