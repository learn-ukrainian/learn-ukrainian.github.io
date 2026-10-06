"""Canned git and gh answers for hook-audit runs (#9807).

A recording stand-in may return output only after the same classifier has
accepted the requested launch. It never executes git or gh, never publishes,
and never writes git configuration. The healer's Python child is not started;
its git reads and config writes stay outside this process.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from tests.hooks_runtime.policy import identify_template

# Decision: (argv, executable, env, shell) -> template id, or None to fall through.
# The caller has already classified the launch. None means "do not answer".
Decide = Callable[[object, object, object, bool], str | None]

_ORIGINAL = None
_DECIDE: Decide | None = None
_INSTALLED = False
_LOCK = threading.Lock()
_CHECKS = {"norepo": 0}


def repo_root() -> Path:
    """Worktree that contains this test package. Hook fixtures anchor here."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Canned:
    """Stdout and stderr are text. The wrapper encodes them when the caller did not ask for text."""

    returncode: int
    stdout: str
    stderr: str


def _protected_git_dir() -> str:
    return f"{repo_root()}/.git"


def _unsupported_checks() -> Canned:
    """gh 2.46 ``pr checks --json`` failure. Empty stdout, the usage banner, exit 1."""
    stderr = (
        "unknown flag: --json\n"
        "Usage: gh pr checks [<number> | <url> | <branch>] [flags]\n"
        "Flags:\n"
        "-w, --watch\n"
    )
    return Canned(1, "", stderr)


def _meta() -> Canned:
    """Non-draft PR whose url and base make the protection lookup a closed endpoint."""
    body = (
        '{"isDraft":false,"baseRefName":"main","body":"reviewed",'
        '"headRefOid":"0123456789abcdef0123456789abcdef01234567",'
        '"number":5,"url":"https://github.com/owner/repo/pull/5"}\n'
    )
    return Canned(0, body, "")


def _rollup() -> Canned:
    """Empty rollup: no failing and no pending checks, so --auto continues to branch protection."""
    return Canned(0, '{"statusCheckRollup":[]}\n', "")


def _protection() -> Canned:
    """Branch protection with one required context. The stand-in does not call gh api."""
    body = '{"required_status_checks":{"contexts":["ci"],"checks":[]}}\n'
    return Canned(0, body, "")


def canned_for(template_id: str, argv: Sequence[str]) -> Canned:
    """Deterministic answer for one accepted template. Unknown ids are not answered."""
    root = repo_root()
    git_dir = _protected_git_dir()
    if template_id == "git-rev-parse-common-dir-absolute":
        # Import-time primary root: ``<root>/.git`` so the protected root is this worktree.
        return Canned(0, git_dir + "\n", "")
    if template_id == "git-rev-parse-toplevel-absolute":
        return Canned(0, str(root) + "\n", "")
    if template_id in {"git-rev-parse-git-dir", "git-rev-parse-git-common-dir"}:
        return Canned(0, git_dir + "\n", "")
    if template_id == "git-symbolic-ref-head":
        return Canned(0, "main\n", "")
    if template_id == "git-c-rev-parse-common-dir":
        # Name is not ``.git``, so the helper continues to ``rev-parse --show-toplevel``.
        return Canned(0, f"{root}/bare-common\n", "")
    if template_id == "git-c-rev-parse-toplevel":
        # Failure fixture: the unusual layout does not resolve, and no later git shape runs.
        return Canned(1, "", "")
    if template_id in {"gh-pr-view", "gh-pr-view-repo"}:
        return _meta()
    if template_id in {"gh-pr-view-rollup", "gh-pr-view-repo-rollup"}:
        return _rollup()
    if template_id == "gh-api-branch-protection":
        return _protection()
    if template_id in {"gh-pr-checks", "gh-pr-checks-repo"}:
        # ``--repo`` always takes the unsupported-checks fallback so that shape's
        # rollup runs. The no-repo form alternates success and that same fallback.
        if "--repo" in argv:
            return _unsupported_checks()
        with _LOCK:
            index = _CHECKS["norepo"]
            _CHECKS["norepo"] += 1
        if index % 2:
            return _unsupported_checks()
        return Canned(0, "[]\n", "")
    if template_id == "python-check-core-bare":
        # Success is empty because the hook discards the child's streams.
        # The child itself is not executed.
        return Canned(0, "", "")
    raise AssertionError(f"no canned answer for {template_id}")


class _FakeProcess:
    """Enough of ``Popen`` for ``subprocess.run`` to build a ``CompletedProcess``."""

    def __init__(self, args: object, canned: Canned, *, textual: bool) -> None:
        self.args = args
        self.returncode = canned.returncode
        if textual:
            self._stdout: str | bytes = canned.stdout
            self._stderr: str | bytes = canned.stderr
        else:
            self._stdout = canned.stdout.encode()
            self._stderr = canned.stderr.encode()
        self.pid = 0

    def communicate(self, input: object = None, timeout: float | None = None) -> tuple[str | bytes, str | bytes]:
        del input, timeout
        return self._stdout, self._stderr

    def poll(self) -> int:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        return self.returncode

    def kill(self) -> None:
        return None

    def __enter__(self) -> _FakeProcess:
        return self

    def __exit__(self, *exc: object) -> bool:
        del exc
        return False


def install(decide: Decide) -> None:
    """Replace ``subprocess.Popen`` once. Allowed templates never reach the real constructor."""
    global _ORIGINAL, _DECIDE, _INSTALLED
    import subprocess

    if _INSTALLED:
        _DECIDE = decide
        return
    _ORIGINAL = subprocess.Popen
    _DECIDE = decide

    def _popen(*args: object, **kwargs: object) -> object:
        popen_args = args[0] if args else kwargs.get("args")
        executable = kwargs.get("executable")
        if executable is None and len(args) >= 3:
            executable = args[2]
        shell = bool(kwargs.get("shell", False))
        env = kwargs.get("env")
        decision = _DECIDE
        template_id = decision(popen_args, executable, env, shell) if decision is not None else None
        if template_id is None:
            original = _ORIGINAL
            assert original is not None
            return original(*args, **kwargs)
        argv = popen_args if isinstance(popen_args, (list, tuple)) else ()
        # The decision already ran the classifier. Confirm the id still names this argv
        # before any canned bytes are built.
        if identify_template(tuple(str(part) for part in argv)) != template_id:
            original = _ORIGINAL
            assert original is not None
            return original(*args, **kwargs)
        textual = bool(kwargs.get("text") or kwargs.get("universal_newlines") or kwargs.get("encoding"))
        return _FakeProcess(popen_args, canned_for(template_id, tuple(str(part) for part in argv)), textual=textual)

    subprocess.Popen = _popen  # type: ignore[misc]
    _INSTALLED = True
