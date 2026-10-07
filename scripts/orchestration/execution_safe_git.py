"""Local cleanup/inventory Git with repository-configured execution disabled.

Denominator (git-config(1), https://git-scm.com/docs/git-config): index reads
(status/ls-files/worktree-remove) reach core.fsmonitor; status/removal also reach
filter.*.clean/process, and filter.*.smudge is suppressed. Hooks, pagers and alternate-ref enumeration
reach core.hooksPath, core.pager/pager.*, core.alternateRefsCommand. Diff reads
reach diff.external and diff.*.command/textconv. Disable these at command scope,
including named drivers discovered by non-executing `config --name-only`.

No checkout/add/merge/rebase/commit/tag/signature/help/network command is admitted:
merge.*.driver, mergetool/difftool.*.cmd, editors, gpg.*.program/defaultKeyCommand,
help/browser/man/instaweb tools, core.gitProxy/core.sshCommand, ssh.variant,
credential.*.helper/core.askPass, remote.*.uploadpack/receivepack/vcs,
uploadpack.* hooks, protocol.ext, http proxy/auth and aliases cannot be reached.
GUI, email, trailer and CVS commands are also excluded, so guitool.*.cmd,
sendemail.*Cmd, trailer.*.cmd/command and gitcvs.dbDriver are unreachable.
Missing promisor objects cannot
start a fetch (--no-lazy-fetch); automatic gc/maintenance is disabled, so
gc.recentObjectsHook cannot be reached either. All protocols are denied as a
second fence. Local/system/global config is not a trusted execution source.

The optional runner is a value carrying only a fixed executable, never a
callback. Caller argv/environment cannot override the controls. This is not a
sandbox against concurrent same-user modification of the executable or config.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GIT = shutil.which("git", path=os.defpath) or "/usr/bin/git"
LOCAL_COMMANDS = frozenset(
    {
        "config",
        "status",
        "ls-files",
        "ls-tree",
        "rev-parse",
        "rev-list",
        "symbolic-ref",
        "worktree",
        "for-each-ref",
        "show-ref",
        "diff",
        "diff-tree",
        "diff-index",
        "check-attr",
        "check-ref-format",
        "merge-base",
        "cat-file",
        "branch",
        "remote",
    }
)
# Extracted from sibling_git's controls and the nested-artifact block. Values
# here are authoritative, and are always supplied after caller constraints.
_SETTINGS = (
    "core.fsmonitor=false",
    f"core.hooksPath={os.devnull}",
    "core.pager=",
    "core.alternateRefsCommand=",
    "diff.external=",
    "protocol.allow=never",
    "protocol.ext.allow=never",
    "submodule.recurse=false",
    "fetch.recurseSubmodules=false",
    "maintenance.auto=false",
    "gc.auto=0",
    "core.untrackedCache=false",
)
_DRIVER = re.compile(r"^(filter\..+\.(clean|smudge|process|required)|diff\..+\.(command|textconv)|pager\..+)$", re.I)


def safe_git_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Strip inherited Git injection and isolate config and command lookup."""
    result = {k: v for k, v in (os.environ if env is None else env).items() if not k.startswith("GIT_")}
    result.update(
        {
            "PATH": os.defpath,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_ALLOW_PROTOCOL": "",
            "GIT_PROTOCOL_FROM_USER": "0",
        }
    )
    return result


@dataclass(frozen=True)
class SafeGitRunner:
    """The only permitted runner injection: an absolute Git executable."""

    executable: str = GIT


def _execution_keys(prefix, roots, env, timeout):
    """Inspect config and initialized gitlinks without refreshing file contents.

    worktree-remove runs status in its target, and status/diff may inspect
    initialized submodules. Collect named drivers from each of those config
    scopes too; Git propagates the resulting -c controls to its child Git.
    """
    keys = set()
    seen = set()
    pending = list(roots)
    while pending:
        root, inspect_index = pending.pop()
        resolved = root.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        config = subprocess.run(
            [*prefix, "config", "--null", "--name-only", "--list"],
            cwd=root,
            env=env,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        if config.returncode:
            return keys, config
        keys.update(os.fsdecode(raw) for raw in config.stdout.split(b"\0") if raw)
        if not inspect_index:
            continue
        # ls-files --stage reads index metadata, never clean/smudge/process
        # filters; scalar fsmonitor/hooks controls already cover this probe.
        index = subprocess.run(
            [*prefix, "ls-files", "--stage", "-z"],
            cwd=root,
            env=env,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        if index.returncode:
            return keys, index
        gitlinks = [
            os.fsdecode(entry.split(b"\t", 1)[1])
            for entry in index.stdout.split(b"\0")
            if entry.startswith(b"160000 ") and b"\t" in entry
        ]
        if not gitlinks:
            continue
        # core.worktree can redirect the effective root. Git's child status
        # reads submodule config there, rather than beneath the caller's cwd.
        toplevel = subprocess.run(
            [*prefix, "rev-parse", "--show-toplevel"],
            cwd=root,
            env=env,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        if toplevel.returncode:
            return keys, toplevel
        worktree = Path(os.fsdecode(toplevel.stdout).removesuffix("\n"))
        for path in gitlinks:
            child = worktree / path
            if (child / ".git").exists():
                pending.append((child, True))
    return keys, None


def run_git(
    args: list[str],
    *,
    cwd: Path,
    runner: SafeGitRunner | None = None,
    env: dict[str, str] | None = None,
    timeout: float | None = 30,
    integrity: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run a local command; command-scoped controls are compulsory."""
    if runner is not None and type(runner) is not SafeGitRunner:
        raise TypeError("runner must be a SafeGitRunner executable constraint")
    executable = GIT if runner is None else runner.executable
    if not Path(executable).is_absolute():
        raise ValueError("Git executable must be absolute")
    if not args or args[0] not in LOCAL_COMMANDS:
        raise ValueError("only local cleanup/inventory Git commands are admitted")
    if args[0] == "worktree" and (len(args) < 2 or args[1] not in {"list", "remove", "unlock"}):
        raise ValueError("unsupported worktree operation")
    if args[0] == "remote" and (len(args) < 2 or args[1] not in {"get-url"}):
        raise ValueError("unsupported remote operation")
    if args[0] == "config" and any(
        arg == "edit"
        or (arg.startswith("--") and arg != "--" and "--edit".startswith(arg))
        or (arg.startswith("-") and not arg.startswith("--") and "e" in arg[1:])
        for arg in args[1:]
    ):
        raise ValueError("configuration editing may invoke an editor")
    if args[0] == "branch" and any(
        arg.startswith("--") and arg != "--" and "--edit-description".startswith(arg) for arg in args[1:]
    ):
        raise ValueError("branch description editing may invoke an editor")
    safe_env = safe_git_env(env)
    prefix = [executable, "--no-pager", "--no-lazy-fetch"]
    if integrity:
        prefix.extend(
            ["-c", f"core.attributesFile={os.devnull}", "-c", "core.trustctime=true", "-c", "core.checkStat=default"]
        )
    for setting in _SETTINGS:
        prefix.extend(["-c", setting])
    roots = [(Path(cwd), args[0] in {"status", "diff", "diff-index", "diff-tree"})]
    if args[0] == "worktree" and args[1] == "remove":
        target = Path(args[-1])
        roots.append((target if target.is_absolute() else Path(cwd) / target, True))
    keys, failure = _execution_keys(prefix, roots, safe_env, timeout)
    if failure is not None:
        # No unchecked command can follow a failed configuration inventory.
        if kwargs.get("check"):
            failure.check_returncode()
        if kwargs.get("text"):
            return subprocess.CompletedProcess(
                failure.args,
                failure.returncode,
                failure.stdout.decode("utf-8", "replace"),
                failure.stderr.decode("utf-8", "replace"),
            )
        return failure
    for key in sorted(keys):
        if _DRIVER.fullmatch(key):
            value = "false" if key.lower().endswith(".required") else ""
            prefix.extend(["-c", f"{key}={value}"])
    if args[0] in {"diff", "diff-tree", "diff-index"}:
        args = [args[0], "--no-ext-diff", "--no-textconv", *args[1:]]
    return subprocess.run([*prefix, *args], cwd=cwd, env=safe_env, timeout=timeout, **kwargs)
