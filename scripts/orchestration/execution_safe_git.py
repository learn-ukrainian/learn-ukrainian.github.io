"""Local cleanup/inventory Git with repository-configured execution disabled.

Denominator (git-config(1), https://git-scm.com/docs/git-config): index reads
(status/ls-files/worktree-remove) reach core.fsmonitor; status/removal also reach
filter.*.clean/process, and filter.*.smudge is suppressed. Hooks, pagers and alternate-ref enumeration
reach core.hooksPath, core.pager/pager.*, core.alternateRefsCommand. Diff reads
reach diff.external and diff.*.command/textconv. Disable these at command scope,
including named drivers discovered by non-executing `config --name-only`.

Remote proofs and preservation require explicit ``remote`` and ``commit``
profiles. Remote commands run in the primary checkout, never the linked worker;
SSH uses the system executable, helpers/askpass and arbitrary protocols are off.
Preservation refuses attribute transformations before staging and disables
signing and editors. Checkout/merge/rebase/tag/signature/help commands are not
admitted, so merge drivers and help/browser tools are unreachable. Remote
commands pin upload-pack, SSH and credential controls; custom VCS helpers and
ext transport are refused. Neither commit signing nor SSH signing-key commands
are admitted. Local-only commands cannot reach any transport.
GUI, email, trailer and CVS commands are also excluded, so guitool.*.cmd,
sendemail.*Cmd, trailer.*.cmd/command and gitcvs.dbDriver are unreachable.
Missing promisor objects cannot
start a fetch (--no-lazy-fetch); automatic gc/maintenance is disabled, so
gc.recentObjectsHook cannot be reached either. Only file/HTTPS/SSH protocols are
admitted for explicit remote proofs; other profiles deny all protocols.
Local/system/global config is not a trusted execution source.

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
        "cherry",
        "bundle",
        "update-ref",
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
REMOTE_COMMANDS = frozenset({"fetch", "ls-remote"})
COMMIT_COMMANDS = frozenset({"add", "commit"})
_FALSE = shutil.which("false", path=os.defpath) or "/usr/bin/false"
_SSH = shutil.which("ssh", path=os.defpath) or "/usr/bin/ssh"
_REMOTE_SETTINGS = (
    f"core.sshCommand={_SSH} -oBatchMode=yes -oConnectTimeout=5",
    "ssh.variant=ssh",
    "core.gitProxy=",
    "credential.helper=",
    "credential.interactive=false",
    f"core.askPass={_FALSE}",
    "protocol.file.allow=always",
    "protocol.https.allow=always",
    "protocol.ssh.allow=always",
    "transfer.fsckObjects=true",
    "fetch.fsckObjects=true",
    "fetch.writeCommitGraph=false",
)
_COMMIT_SETTINGS = (
    "commit.gpgSign=false",
    f"gpg.program={_FALSE}",
    f"gpg.openpgp.program={_FALSE}",
    f"gpg.x509.program={_FALSE}",
    f"gpg.ssh.program={_FALSE}",
    f"core.editor={_FALSE}",
    "core.autocrlf=false",
)


def primary_repository(cwd: Path) -> Path:
    """Resolve common metadata without executing Git or reading worker config.

    Cleanup supports the project's normal primary checkout and linked trees.
    Unrecognized metadata fails closed rather than running remote Git in a worker.
    """
    cwd = Path(cwd).resolve()
    dotgit = cwd / ".git"
    if dotgit.is_dir():
        return cwd
    lines = dotgit.read_text().splitlines()
    if not lines or not lines[0].startswith("gitdir: "):
        raise ValueError("cannot resolve primary repository")
    admin = Path(lines[0][8:])
    if not admin.is_absolute():
        admin = cwd / admin
    admin = admin.resolve()
    common = (admin / (admin / "commondir").read_text().strip()).resolve()
    if common.name != ".git" or admin.parent != common / "worktrees" or not common.is_dir():
        raise ValueError("cannot resolve primary repository")
    return common.parent


def _preserve_attributes(prefix, cwd, env, timeout):
    """Refuse transformations in current or staged attributes before add.

    A disabled clean filter cannot reproduce filtered storage. The same applies
    to EOL/encoding/ident transformations: preserve bytes or retain the tree.
    """
    paths = subprocess.run(
        [*prefix, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=cwd,
        env=env,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if paths.returncode:
        return paths
    for source in ([], ["--cached"]):
        attrs = subprocess.run(
            [
                *prefix,
                "check-attr",
                *source,
                "-z",
                "--stdin",
                "filter",
                "text",
                "eol",
                "working-tree-encoding",
                "ident",
            ],
            input=paths.stdout,
            cwd=cwd,
            env=env,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if attrs.returncode:
            return attrs
        fields = attrs.stdout.split(b"\0")
        if any(value not in {b"unspecified", b"unset"} for value in fields[2::3]):
            code = (
                "preserve_filter_attribute"
                if any(
                    fields[i + 1] == b"filter" and fields[i + 2] not in {b"unspecified", b"unset"}
                    for i in range(0, len(fields) - 1, 3)
                )
                else "preserve_transform_attribute"
            )
            return subprocess.CompletedProcess(attrs.args, 1, b"", code.encode())
    return None


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

    worktree-remove runs status in its target; status/diff/add/commit may
    inspect initialized submodules. Collect named drivers from each config
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
    profile: str = "local",
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run an admitted command with compulsory controls for its explicit profile."""
    if runner is not None and type(runner) is not SafeGitRunner:
        raise TypeError("runner must be a SafeGitRunner executable constraint")
    executable = GIT if runner is None else runner.executable
    if not Path(executable).is_absolute():
        raise ValueError("Git executable must be absolute")
    admitted = {"local": LOCAL_COMMANDS, "remote": REMOTE_COMMANDS, "commit": COMMIT_COMMANDS}
    if profile not in admitted or not args or args[0] not in admitted[profile]:
        raise ValueError("only local cleanup/inventory Git commands are admitted")
    if profile == "remote":
        cwd = primary_repository(cwd)
    if args[0] == "bundle" and (len(args) < 2 or args[1] not in {"create", "verify", "list-heads"}):
        raise ValueError("unsupported bundle operation")
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
    for setting in _REMOTE_SETTINGS if profile == "remote" else _COMMIT_SETTINGS if profile == "commit" else ():
        prefix.extend(["-c", setting])
    if profile == "remote":
        safe_env["GIT_ALLOW_PROTOCOL"] = "file:https:ssh"
        safe_env["GIT_SSH_COMMAND"] = f"{_SSH} -oBatchMode=yes -oConnectTimeout=5"
        safe_env["GIT_ASKPASS"] = _FALSE
    roots = [(Path(cwd), args[0] in {"status", "diff", "diff-index", "diff-tree", "add", "commit"})]
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
        if profile == "remote" and re.fullmatch(r"credential(?:\..+)?\.helper", key, re.I):
            prefix.extend(["-c", f"{key}="])
        if profile == "remote" and re.fullmatch(r"protocol\..+\.allow", key, re.I):
            value = (
                "always"
                if key.lower() in {"protocol.file.allow", "protocol.https.allow", "protocol.ssh.allow"}
                else "never"
            )
            prefix.extend(["-c", f"{key}={value}"])
    if profile == "remote":
        if any(re.fullmatch(r"remote\..+\.vcs", key, re.I) for key in keys):
            raise ValueError("custom remote VCS helpers are unsupported")
        if any(arg.startswith(("--upload-pack", "--exec")) or arg == "-u" for arg in args[1:]):
            raise ValueError("remote upload-pack override is unsupported")
        args = [args[0], "--upload-pack=git-upload-pack", *args[1:]]
        if args[0] == "fetch":
            args = [args[0], "--no-recurse-submodules", "--no-auto-maintenance", *args[1:]]
    if (
        profile == "commit"
        and args[0] == "commit"
        and any(
            arg.startswith("-S") or (arg.startswith("--") and "--gpg-sign".startswith(arg.split("=", 1)[0]))
            for arg in args[1:]
        )
    ):
        raise ValueError("preservation signing is unsupported")
    if profile == "commit" and not (
        args == ["add", "-A"]
        or (len(args) == 4 and args[:3] == ["commit", "--no-verify", "-m"])
    ):
        # Interactive add and commit trailers reach more configured programs.
        # This profile is solely the reaper's noninteractive preservation pair.
        raise ValueError("unsupported preservation operation")
    if profile == "commit" and args[0] == "add":
        failure = _preserve_attributes(prefix, cwd, safe_env, timeout)
        if failure is not None:
            if kwargs.get("check"):
                failure.check_returncode()
            if kwargs.get("text"):
                return subprocess.CompletedProcess(
                    failure.args, failure.returncode, failure.stdout.decode(), failure.stderr.decode()
                )
            return failure
    if args[0] in {"diff", "diff-tree", "diff-index"}:
        args = [args[0], "--no-ext-diff", "--no-textconv", *args[1:]]
    return subprocess.run([*prefix, *args], cwd=cwd, env=safe_env, timeout=timeout, **kwargs)
