"""The boundary around a Kimi worker's worktree.

Delegate commits and pushes a Kimi worker's changes itself, after
``kimi_admission.refuse_kimi_changes`` finds no Ukrainian content in them.
While the worker runs, three things stop it from committing or publishing
that content on its own:

- ``install`` gives the worktree a worktree-scoped ``core.hooksPath`` whose
  ``pre-commit`` and ``pre-push`` hooks (``kimi_hooks/``) run :func:`main`:
  the same content check, plus the task's owned paths. The repository's other
  hooks keep running through links in that directory.
- ``install`` points every remote's push URL, in the worktree's own config,
  at an unusable URL.
- ``env_sanitize.build_agent_env`` launches every Kimi seat without a push
  credential.

``remove`` takes the boundary down; delegate calls it after its own check
passes and before it commits and pushes.

The content check reads the full post-image of every changed path and admits
only plain UTF-8 text without Cyrillic, so neither git's binary
classification nor another encoding hides Ukrainian content.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.agent_runtime.kimi_admission import FileChange

_REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_SOURCE = Path(__file__).resolve().parent / "kimi_hooks"
GUARDED_HOOKS = ("pre-commit", "pre-push")
# Directory under the worktree's own git dir that core.hooksPath points at.
HOOKS_DIR_NAME = "lu-kimi-hooks"
PUSH_BLOCK_URL = "kimi-push-disabled://delegate-pushes-after-the-content-check"
_SECTION = "kimiguard"
_EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
_GIT_TIMEOUT_S = 60
# `git config --unset` exit status when the key is not set.
_CONFIG_KEY_MISSING = 5


class BoundaryError(RuntimeError):
    """The Kimi worktree boundary could not be read, installed or checked."""


def _git(
    repo: Path, *args: str, env: Mapping[str, str] | None = None, stdin: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        input=stdin,
        capture_output=True,
        check=False,
        env=None if env is None else dict(env),
        timeout=_GIT_TIMEOUT_S,
    )


def _git_text(repo: Path, *args: str, env: Mapping[str, str] | None = None) -> str:
    proc = _git(repo, *args, env=env)
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip() or f"exit {proc.returncode}"
        raise BoundaryError(f"git {' '.join(args[:3])} failed: {detail}")
    return proc.stdout.decode("utf-8", "surrogateescape").strip()


def _worktree_config(repo: Path, key: str, *, env: Mapping[str, str] | None = None) -> list[str]:
    proc = _git(repo, "config", "--worktree", "--get-all", key, env=env)
    if proc.returncode == 1:
        return []
    if proc.returncode != 0:
        raise BoundaryError(f"cannot read {key}: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout.decode("utf-8", "surrogateescape").splitlines()


# --- change sets ----------------------------------------------------------------------


def parse_name_status(output: str) -> list[tuple[str, str]]:
    """``(status letter, path)`` pairs from ``git diff --name-status -z --no-renames``."""
    fields = output.split("\0")
    pairs: list[tuple[str, str]] = []
    for index in range(0, len(fields) - 1, 2):
        status, path = fields[index], fields[index + 1]
        if not status or not path:
            break
        pairs.append((status[0], path))
    return pairs


def _blob(repo: Path, spec: str, env: Mapping[str, str] | None) -> bytes | None:
    proc = _git(repo, "cat-file", "blob", spec, env=env)
    return proc.stdout if proc.returncode == 0 else None


def _worktree_file(path: Path) -> bytes | None:
    try:
        if path.is_symlink():  # git stores a symlink as its target
            return os.fsencode(os.readlink(path))
        return path.read_bytes() if path.is_file() else None
    except OSError:
        return None


def changes(
    repo: Path,
    pairs: Iterable[tuple[str, str]],
    *,
    after: str | None,
    env: Mapping[str, str] | None = None,
) -> list[FileChange]:
    """The ``FileChange`` of each changed path.

    ``after`` is the tree-ish of the post-images, ``""`` for the index, or
    None for the working tree. A post-image that cannot be read stays None,
    which the content check refuses.
    """
    from scripts.agent_runtime.kimi_admission import FileChange

    result = []
    for status, path in pairs:
        if status == "D":
            result.append(FileChange(path, None, deleted=True))
            continue
        post = _worktree_file(repo / path) if after is None else _blob(repo, f"{after}:{path}", env)
        result.append(FileChange(path, post))
    return result


def _diff_pairs(repo: Path, *args: str, env: Mapping[str, str] | None = None) -> list[tuple[str, str]]:
    output = _git_text(repo, "diff", "--name-status", "-z", "--no-renames", "--no-ext-diff", *args, "--", env=env)
    return parse_name_status(output)


def index_changes(repo: Path, *, env: Mapping[str, str] | None = None) -> list[FileChange]:
    """What the index would commit on top of HEAD (the tree git is about to commit)."""
    head = "HEAD" if _git(repo, "rev-parse", "--verify", "-q", "HEAD", env=env).returncode == 0 else _EMPTY_TREE
    return changes(repo, _diff_pairs(repo, "--cached", head, env=env), after="", env=env)


def commit_changes(repo: Path, base_ref: str, commit: str, *, env: Mapping[str, str] | None = None) -> list[FileChange]:
    """What ``commit`` changes since its merge base with ``base_ref``."""
    merge_base = _git_text(repo, "merge-base", base_ref, commit, env=env)
    return changes(repo, _diff_pairs(repo, merge_base, commit, env=env), after=commit, env=env)


def ownership_reasons(paths: Sequence[str], owned: Sequence[str]) -> list[str]:
    """Why changed ``paths`` are refused: outside the task's owned paths or off the Kimi allowlist."""
    from scripts.agent_runtime.kimi_admission import owned_path_reason
    from scripts.guardrails.delegate_ownership import path_is_owned

    if not owned:
        return ["the task declared no owned paths, so it may change none"]
    reasons: list[str] = []
    outside = [path for path in paths if not path_is_owned(path, owned)]
    if outside:
        shown = ", ".join(repr(path) for path in outside[:5])
        more = f" and {len(outside) - 5} more" if len(outside) > 5 else ""
        reasons.append(f"changed paths outside the owned paths ({shown}{more})")
    reasons.extend(reason for path in paths if (reason := owned_path_reason(path)))
    return reasons


# --- the hooks ------------------------------------------------------------------------


def hook_reasons(repo: Path, hook: str, refs: str = "") -> list[str]:
    """Why the ``pre-commit`` or ``pre-push`` hook refuses; empty when it admits."""
    from scripts.agent_runtime.kimi_admission import change_reasons

    owned = _worktree_config(repo, f"{_SECTION}.ownedpath")
    if hook == "pre-commit":
        change_sets = [index_changes(repo)]
    else:
        base = _worktree_config(repo, f"{_SECTION}.base")
        if not base:
            return [f"{_SECTION}.base is not set, so the pushed commits cannot be checked"]
        change_sets = []
        for line in refs.splitlines():
            fields = line.split()
            if len(fields) != 4:
                continue
            local_sha = fields[1]
            if set(local_sha) == {"0"}:  # a branch deletion adds no content
                continue
            change_sets.append(commit_changes(repo, base[-1], local_sha))
    reasons: list[str] = []
    for change_set in change_sets:
        reasons.extend(change_reasons(change_set))
        reasons.extend(ownership_reasons([change.path for change in change_set], owned))
    return list(dict.fromkeys(reasons))


def main(argv: Sequence[str] | None = None) -> int:
    """Hook entry point: ``kimi_boundary.py pre-commit`` or ``kimi_boundary.py pre-push`` (refs on stdin)."""
    from scripts.agent_runtime.kimi_admission import format_refusal

    args = list(sys.argv[1:] if argv is None else argv)
    hook = args[0] if args else ""
    if hook not in GUARDED_HOOKS:
        print(f"usage: kimi_boundary.py {{{'|'.join(GUARDED_HOOKS)}}}", file=sys.stderr)
        return 2
    agent = "kimi"
    try:
        repo = Path(_git_text(Path.cwd(), "rev-parse", "--show-toplevel"))
        agent = (_worktree_config(repo, f"{_SECTION}.agent") or [agent])[-1]
        reasons = hook_reasons(repo, hook, sys.stdin.read() if hook == "pre-push" else "")
    except (BoundaryError, OSError, subprocess.SubprocessError) as exc:
        reasons = [f"the {hook} check could not run ({exc})"]
    if reasons:
        action = "commit" if hook == "pre-commit" else "push"
        print(f"❌ {action} refused by the Kimi worktree boundary: {format_refusal(agent, reasons)}", file=sys.stderr)
        return 1
    return 0


# --- install and remove ---------------------------------------------------------------


def _git_dir(worktree: Path) -> Path | None:
    """The worktree's own git directory, read from ``.git`` without running git."""
    dot_git = worktree / ".git"
    if dot_git.is_dir():
        return dot_git
    try:
        text = dot_git.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text.startswith("gitdir:"):
        return None
    git_dir = Path(text.removeprefix("gitdir:").strip())
    return git_dir if git_dir.is_absolute() else worktree / git_dir


def is_installed(worktree: Path) -> bool:
    """Whether ``worktree`` carries a Kimi boundary; reads the filesystem only."""
    git_dir = _git_dir(worktree)
    return git_dir is not None and (git_dir / HOOKS_DIR_NAME).is_dir()


def _remotes(worktree: Path, env: Mapping[str, str] | None) -> list[str]:
    return _git_text(worktree, "remote", env=env).splitlines()


def install(
    worktree: Path,
    *,
    agent: str,
    base_ref: str,
    owned_paths: Sequence[str],
    env: Mapping[str, str] | None = None,
    python: str = sys.executable,
) -> None:
    """Install the boundary in ``worktree``; raises ``BoundaryError`` when any part cannot be set."""
    # Worktree-scoped settings need extensions.worktreeConfig (sparse-checkout enables it too).
    enabled = _git_text(
        worktree, "config", "--bool", "--default", "false", "--get", "extensions.worktreeConfig", env=env
    )
    if enabled != "true":
        _git_text(worktree, "config", "extensions.worktreeConfig", "true", env=env)
    remove(worktree, env=env)
    # The repository's own hooks, resolved before core.hooksPath points at ours.
    chain = Path(_git_text(worktree, "rev-parse", "--path-format=absolute", "--git-path", "hooks", env=env))
    hooks_dir = Path(_git_text(worktree, "rev-parse", "--path-format=absolute", "--git-path", HOOKS_DIR_NAME, env=env))
    try:
        hooks_dir.mkdir()
        for name in GUARDED_HOOKS:
            (hooks_dir / name).symlink_to(HOOKS_SOURCE / name)
        if chain.is_dir():
            for entry in sorted(chain.iterdir()):
                runnable = entry.is_file() and os.access(entry, os.X_OK)
                if runnable and entry.name not in GUARDED_HOOKS and not entry.name.endswith(".sample"):
                    (hooks_dir / entry.name).symlink_to(entry)
    except OSError as exc:
        raise BoundaryError(f"cannot create {hooks_dir}: {exc}") from exc
    settings = [
        (f"{_SECTION}.agent", agent),
        (f"{_SECTION}.python", python),
        (f"{_SECTION}.root", str(_REPO_ROOT)),
        (f"{_SECTION}.base", base_ref),
        (f"{_SECTION}.chainhooks", str(chain)),
        *((f"remote.{remote}.pushurl", PUSH_BLOCK_URL) for remote in _remotes(worktree, env)),
        ("core.hooksPath", str(hooks_dir)),
    ]
    for key, value in settings:
        _git_text(worktree, "config", "--worktree", key, value, env=env)
    for path in owned_paths:
        _git_text(worktree, "config", "--worktree", "--add", f"{_SECTION}.ownedpath", path, env=env)


def remove(worktree: Path, *, env: Mapping[str, str] | None = None) -> None:
    """Take the boundary down: hooks path, push block and settings; raises ``BoundaryError`` when a part stays."""
    commands = [
        ("config", "--worktree", "--unset-all", "core.hooksPath"),
        ("config", "--worktree", "--remove-section", _SECTION),
        *(
            ("config", "--worktree", "--fixed-value", "--unset-all", f"remote.{remote}.pushurl", PUSH_BLOCK_URL)
            for remote in _remotes(worktree, env)
        ),
    ]
    for command in commands:
        proc = _git(worktree, *command, env=env)
        # Exit 5 (unset) and 128 (remove-section) mean the setting was not there.
        if proc.returncode not in (0, _CONFIG_KEY_MISSING, 128):
            raise BoundaryError(f"git {' '.join(command[:4])} failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    git_dir = _git_dir(worktree)
    if git_dir is not None:
        shutil.rmtree(git_dir / HOOKS_DIR_NAME, ignore_errors=True)
    if is_installed(worktree):
        raise BoundaryError(f"cannot remove {git_dir / HOOKS_DIR_NAME if git_dir else HOOKS_DIR_NAME}")


if __name__ == "__main__":
    # The hooks run this file with ``python -I``, from the dispatcher's checkout.
    sys.path.insert(0, str(_REPO_ROOT))
    raise SystemExit(main())
