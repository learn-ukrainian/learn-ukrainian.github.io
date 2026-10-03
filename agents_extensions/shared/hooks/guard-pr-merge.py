#!/usr/bin/env python3
"""PreToolUse guard — block unsafe `gh pr merge`, including `--admin`.

Reads the Claude Code hook payload on stdin (JSON with `tool_input.command`) and exits
2 (block) when the command is a `gh pr merge ...` whose target PR is a draft, has red
checks, has checks still running, or arms `--auto` on a branch that enforces nothing.

Division of labor with guard-admin-merge.py: that hook checks whether `--admin`
would bypass a blocking failure (#M-0.5). This hook applies the ordinary PR
readiness checks to every merge, including `--admin`.

Why a hook: GitHub branch protection stops only what is configured as required.
Without local enforcement, an uncoordinated or draft PR could be merged before
review or while checks are red. The fleet works across repositories with varied
protection settings, so the guard enforces invariants deterministically.

FAIL-CLOSED: if the PR, its draft flag, its check states, or the base branch's
protection can't be determined (gh error/timeout, no PR number), BLOCK. A merge gate
must not let an *unverifiable* merge through; a human can always run the merge directly,
outside the agent harness.

A red check blocks regardless of whether GitHub calls it required: "required" is a
config accident, red is red. So EVERY check counts unless its name marks it advisory.
`--auto` is the one verdict that consults protection, because it is the one thing
protection actually changes.

SCOPE, stated honestly: this is a discipline gate, not a sandbox. It matches the shapes a
careless merge actually takes — direct, wrapper-prefixed, `bash -c` wrapped, and xargs-fed
`gh pr merge`, in gh's real flag spellings — and fails closed on what it cannot read. It
cannot stop an agent that sets out to evade it: `gh api -X PUT repos/{o}/{r}/pulls/{n}/merge`
never says "gh pr merge" at all, and neither does a Python script hitting the REST API.
Nothing matching on Bash commands can close that, so the job is to make the CARELESS path
refuse, not the deliberate path impossible. Literal shell payloads and here-documents are parsed recursively; dynamic
payloads are refused whenever the raw command engages this guard.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _read_payload() -> dict | None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, RecursionError):
        return None
    return payload if isinstance(payload, dict) else None


def _command(payload: dict) -> str:
    return ((payload.get("tool_input") or {}).get("command") or "").strip()


def _may_merge(command: str) -> bool:
    # The shell drops quotes and backslashes before executing a command.
    probe = command.replace("\\", "").replace("'", "").replace('"', "")
    return ("gh" in probe or "scripts.publish" in probe) and "pr" in probe and "merge" in probe


# Ordinary Bash commands must remain usable even if guard dependencies are absent.
# Preserve the payload for main(), since stdin can only be consumed once.
if __name__ == "__main__":
    _CLI_PAYLOAD = _read_payload()
    if (
        _CLI_PAYLOAD is not None
        and isinstance(_CLI_PAYLOAD.get("tool_input", {}), dict)
        and isinstance(_CLI_PAYLOAD.get("tool_input", {}).get("command", ""), str)
        and not _may_merge(_command(_CLI_PAYLOAD))
    ):
        sys.exit(0)


for parent in Path(__file__).resolve().parents:
    if (parent / "scripts/publish").is_dir():
        sys.path.insert(0, str(parent))
        break

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Don't write __pycache__ next to deployed hooks (#9108).
sys.dont_write_bytecode = True
try:
    from shell_bash import REPAIR, UNREADABLE, ShellParseError, invoked_start, read_commands
except Exception as exc:
    print(
        f"guard dependency unavailable: shell_bash ({type(exc).__name__}); "
        "repair: uv pip install --python <canonical-checkout>/.venv/bin/python "
        "--require-hashes --only-binary=:all: -r requirements-hooks.txt; "
        "npm run agents:deploy",
        file=sys.stderr,
    )
    raise SystemExit(2) from None

try:
    from scripts.publish.merge_guard import (
        _checks_json_unsupported,
        _parse_status_rollup_rows,
        parse_checks,
        readiness_reason,
    )
    from scripts.publish.merge_guard import (
        _is_advisory as _is_advisory,
    )
    from scripts.publish.merge_guard import (
        _latest_rollup_rows as _latest_rollup_rows,
    )
    from scripts.publish.merge_guard import (
        _rollup_name as _rollup_name,
    )
    from scripts.publish.merge_guard import (
        _rollup_timestamp as _rollup_timestamp,
    )
    from scripts.publish.merge_guard import (
        _rollup_value as _rollup_value,
    )
except Exception:
    print(
        "guard dependency unavailable: merge readiness; repair: git restore scripts/publish/merge_guard.py; npm run agents:deploy",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


# Agent harnesses export CLICOLOR_FORCE/FORCE_COLOR, which beat NO_COLOR and make
# `gh --json` emit ANSI-colorized JSON on pipes -> json.loads fails -> every merge
# fail-closes (review B1, PR #5324). Every gh subprocess below runs with the force
# vars REMOVED and NO_COLOR pinned; _decolorize() strips any residual escapes.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _gh_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"CLICOLOR_FORCE", "FORCE_COLOR"}}
    env["NO_COLOR"] = "1"
    env["CLICOLOR"] = "0"
    return env


def _decolorize(text: str) -> str:
    return _ANSI_RE.sub("", text)


# A check is treated as merge-blocking unless its name marks it explicitly advisory.
# Same inversion as guard-admin-merge.py, and it matters more here: an allowlist of
# "known required" names would UNDER-block, and on a repo where GitHub marks nothing
# required, under-blocking is the entire failure mode this hook exists to close.
ADVISORY_NAME_MARKERS = ("advisory",)

_FAIL_BUCKETS = {"fail", "failure", "error", "cancel", "canceled", "cancelled", "timed_out", "action_required"}
_PENDING_BUCKETS = {"pending", "queued", "in_progress", "waiting", "expected"}
# Only these mean "done and fine". A non-advisory check in ANY other state — including a
# bucket gh grows later, or a row with no bucket at all — is undeterminable, not green.
_PASS_BUCKETS = {"pass", "success", "skipping", "skipped", "neutral"}

# strconv.ParseBool's false spellings (lowercased). gh is cobra/pflag, so every boolean
# flag also accepts `--flag=value`: `gh pr list --draft=notabool` fails with
# "strconv.ParseBool: parsing \"notabool\": invalid syntax", which proves the =value path
# is real and must be parsed here too — `--auto` and `--auto=true` are the same flag.
_FALSE_VALUES = {"false", "f", "0"}


def _flag_enabled(args: list[str], name: str) -> bool:
    """Whether a gh boolean flag is on, in either spelling (`--auto` / `--auto=true`).

    LAST occurrence wins, as pflag applies repeated flags in argument order — verified:
    `gh pr list --draft=false --draft=true` returns draft PRs. Returning on the FIRST
    match would read `--auto=false --auto` as off and wave through the very auto-merge
    gh is about to arm.

    A malformed value (`--auto=maybe`) makes gh itself exit non-zero, so reading it as ON
    is the fail-closed direction: the guard judges a command that could never merge anyway.
    """
    enabled = False
    for a in args:
        if a == f"--{name}":
            enabled = True
        elif a.startswith(f"--{name}="):
            enabled = a.split("=", 1)[1].strip().lower() not in _FALSE_VALUES
    return enabled


_UNREADABLE_MARKER = UNREADABLE
_UNPARSED = ["gh", "pr", "merge", UNREADABLE]
_MAX_SHELL_DEPTH = 8
_invoked_start = invoked_start


def _judged_segments(command: str, depth: int = 0, cwd: str | None = None, cwd_unreadable: bool = False):
    try:
        rows = read_commands(command, cwd=cwd, depth=depth)
        if re.search(r"\bmerge\b", command, re.I) and ("<(" in command or ">(" in command):
            from shell_bash import Invocation

            rows.append(Invocation(list(_UNPARSED), None))
        return rows
    except ShellParseError:
        from shell_bash import Invocation

        return [Invocation(list(_UNPARSED), None)] if _may_merge(command) else []


def _segments(command: str) -> list[list[str]]:
    try:
        rows = [segment.argv for segment in read_commands(command, include_payloads=False, diagnostic=True)]
        if re.search(r"\bmerge\b", command, re.I) and ("<(" in command or ">(" in command):
            rows.append(list(_UNPARSED))
        return rows
    except ShellParseError:
        return []


def _merge_args(seg: list[str]) -> list[str] | None:
    """Return the args of a `gh pr merge ...` segment this hook judges, else None.

    Skipped: `--disable-auto` (any spelling), which disarms auto-merge rather than
    merging anything and is exactly the remedy this hook's --auto verdict asks for.

    Admin merges are judged here as well as by ``guard-admin-merge.py``: the
    ordinary PR checks still apply when a command contains ``--admin``.
    """
    i, via_xargs = _invoked_start(seg)
    if (
        i + 3 < len(seg)
        and re.fullmatch(r"python(?:3(?:\.\d+)?)?", Path(seg[i]).name)
        and seg[i + 1 : i + 4] == ["-m", "scripts.publish", "pr-merge"]
    ):
        if "--help" in seg[i + 4 :]:
            return None
        args = []
        rest = seg[i + 4 :]
        j = 0
        while j < len(rest):
            key, sep, value = rest[j].partition("=")
            if key not in {"--number", "--repo", "--subject", "--body", "--body-file", "--match-head"}:
                return [_UNREADABLE_MARKER]
            if not sep:
                j += 1
                if j >= len(rest):
                    return [_UNREADABLE_MARKER]
                value = rest[j]
            if key == "--number":
                args.append(value)
            else:
                args.append(("--match-head-commit" if key == "--match-head" else key) + "=" + value)
            j += 1
    elif seg[i : i + 3] == ["gh", "pr", "merge"]:
        args = seg[i + 3 :]
    else:
        return None
    if via_xargs and _pr_selector(args) is None:
        # xargs appends stdin items, so the real selector is not in this command at all.
        # Falling back to the current branch's PR would judge one PR while gh merges
        # another; refuse instead.
        args = [*args, _UNREADABLE_MARKER]
    flags, _ = _classify(args)
    # `gh pr merge --help` prints help and merges nothing — reading the manual is not
    # the offence this guard is for. --help is a bool like any other, so it gets the same
    # spelling treatment (`--help=true`) rather than a bare-token check.
    if _flag_enabled(flags, "help") or "-h" in flags:
        return None
    if _flag_enabled(flags, "disable-auto"):
        return None
    return args


# Options of `gh pr merge` that consume the NEXT argv token as their value. Their values
# must never be mistaken for the PR selector: in `gh pr merge --subject 5`, the 5 is the
# commit subject and the real target is the current branch's PR. Judging the wrong PR is a
# fail-open (green PR #5 waves through a red current branch), not a cosmetic slip.
_VALUE_FLAGS = {
    "--subject",
    "-t",
    "--body",
    "-b",
    "--body-file",
    "-F",
    "--match-head-commit",
    "--author-email",
    "-A",
    # Inherited by every `gh pr` subcommand: `-R, --repo [HOST/]OWNER/REPO`.
    "--repo",
    "-R",
}


# Value-taking SHORTHANDS, by letter → canonical long name. pflag allows these inside a
# cluster (`-st subj` = squash + subject), with the value attached (`-tsubj`, `-Rowner/repo`
# — both verified against real gh), `=`-joined (`-t=subj`), or in the next token.
_VALUE_SHORTS = {"t": "--subject", "b": "--body", "F": "--body-file", "A": "--author-email", "R": "--repo"}

_LONG_VALUE_FLAGS = {"--subject", "--body", "--body-file", "--match-head-commit", "--author-email", "--repo"}


def _cluster_value(tok: str) -> tuple[str | None, str | None, bool]:
    """Inspect a shorthand cluster: → (canonical long name, attached value, needs_next).

    pflag scans a cluster left to right; the first value-taking letter consumes the rest
    of the token as its value, or the next token when nothing is attached. So in
    `-st green-subject`, `green-subject` is the SUBJECT — treating it as the PR selector
    would judge some other PR entirely.
    """
    j = 1
    while j < len(tok):
        ch = tok[j]
        if ch in _VALUE_SHORTS:
            name = _VALUE_SHORTS[ch]
            rest = tok[j + 1 :]
            if rest.startswith("="):
                return name, rest[1:], False
            if rest:
                return name, rest, False
            return name, None, True
        j += 1
    return None, None, False


def _parse_args(args: list[str]) -> tuple[list[str], list[str], dict[str, str]]:
    """Split argv into (flag tokens, positionals, option values keyed by long name).

    pflag takes the NEXT token as a string flag's value even when it looks like a flag,
    so `gh pr merge 5 --subject --disable-auto` is a normal merge whose subject happens
    to be "--disable-auto". Scanning raw argv would read that value as the flag and skip
    judging the merge entirely — a fail-open. Only tokens in FLAG position count.
    """
    flags: list[str] = []
    positionals: list[str] = []
    values: dict[str, str] = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            flags.append(a)
            name, _, value = a.partition("=")
            if value:
                if name in _LONG_VALUE_FLAGS:
                    values[name] = value
                i += 1
                continue
            if a in _LONG_VALUE_FLAGS and i + 1 < len(args):
                values[a] = args[i + 1]
                i += 2
                continue
            i += 1
            continue
        if a.startswith("-") and len(a) > 1:
            flags.append(a)
            name, attached, needs_next = _cluster_value(a)
            if name and attached is not None:
                values[name] = attached
                i += 1
                continue
            if name and needs_next and i + 1 < len(args):
                values[name] = args[i + 1]
                i += 2
                continue
            i += 1
            continue
        positionals.append(a)
        i += 1
    return flags, positionals, values


def _classify(args: list[str]) -> tuple[list[str], list[str]]:
    """(flags, positionals) — see _parse_args."""
    flags, positionals, _ = _parse_args(args)
    return flags, positionals


def _repo_option(args: list[str]) -> str | None:
    """The `-R/--repo` value, which retargets the whole command at another repo."""
    return _parse_args(args)[2].get("--repo")


def _repo_args(repo: str | None) -> list[str]:
    """`--repo X` argv for gh, so every lookup targets the repo the MERGE targets."""
    return ["--repo", repo] if repo else []


def _pr_selector(args: list[str]) -> str | None:
    """The `<number|url|branch>` selector of `gh pr merge`, or None for the current branch.

    gh accepts all three forms, so the selector is passed through verbatim rather than
    forced to a number — a URL selector names a PR in a possibly different repo, and
    resolving it as "whatever PR the cwd is on" would judge a different PR than gh merges.
    """
    _, positionals = _classify(args)
    return positionals[0] if positionals else None


def _pr_ref(args: list[str], repo: str | None = None, cwd: str | None = None) -> str | None:
    """The explicit PR selector; implicit current-branch discovery is refused."""
    del repo, cwd
    return _pr_selector(args)


def _owner_repo_from_url(url: str) -> str | None:
    """`owner/repo` from a PR URL — the PR's BASE repo, which is what protection guards.

    Taken from the PR's own `url` rather than `gh repo view` in cwd: the cwd can be a
    different repo entirely (a URL selector), and it is the base repo — not the fork a PR
    may come from — whose branch protection decides what `--auto` waits for.
    """
    m = re.match(r"https?://[^/]+/([^/]+)/([^/]+)/pull/\d+", url.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _canonical_pr_number(value: object) -> str | None:
    """Return GitHub's positive integer PR number in canonical decimal form."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return str(value)


def _pr_meta(pr: str, repo: str | None = None, cwd: str | None = None) -> dict | None:
    """Read the fields that identify the exact PR and its current body.

    A payload without a boolean `isDraft` is undeterminable, not "not a draft" — `{}` or
    `isDraft: null` must never read as a green light.  The receipt task binding is
    derived only from GitHub's integer ``number``; PR-body text is not an authority input.
    """
    try:
        out = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                pr,
                *_repo_args(repo),
                "--json",
                "isDraft,baseRefName,body,headRefOid,number,url",
            ],
            capture_output=True,
            env=_gh_env(),
            cwd=cwd,
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    try:
        data = json.loads(_decolorize(out.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        return None
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("isDraft"), bool)
        or not isinstance(data.get("body"), str)
        or _canonical_pr_number(data.get("number")) is None
    ):
        return None
    return data


_ROLLUP_FAIL = {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "ERROR", "STARTUP_FAILURE"}
_ROLLUP_PENDING = {"IN_PROGRESS", "QUEUED", "PENDING", "WAITING", "EXPECTED", "REQUESTED", "STALE"}
_ROLLUP_PASS = {"SUCCESS", "SKIPPED", "NEUTRAL"}


def _check_states_from_status_rollup(
    pr: str, repo: str | None = None, cwd: str | None = None
) -> tuple[list[str], list[str]] | None:
    """Fallback for the gh 2.46.0 ``pr checks --json`` compatibility gap."""
    try:
        out = subprocess.run(
            ["gh", "pr", "view", pr, *_repo_args(repo), "--json", "statusCheckRollup"],
            capture_output=True,
            env=_gh_env(),
            cwd=cwd,
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    try:
        data = json.loads(_decolorize(out.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("statusCheckRollup"), list):
        return None
    return _parse_status_rollup_rows(data["statusCheckRollup"])


def _check_states(pr: str, repo: str | None = None, cwd: str | None = None) -> tuple[list[str], list[str]] | None:
    """(failing, pending) non-advisory check names, or None if undeterminable."""
    try:
        out = subprocess.run(
            ["gh", "pr", "checks", pr, *_repo_args(repo), "--json", "name,bucket,state"],
            capture_output=True,
            env=_gh_env(),
            cwd=cwd,
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    if _checks_json_unsupported(out):
        return _check_states_from_status_rollup(pr, repo, cwd)
    text = (out.stdout or "").strip()
    if not text:
        # Empty output is ambiguous: a PR with zero checks (rc 0 → nothing to wait for)
        # vs a gh error / non-existent PR (rc != 0 → fail-CLOSED block). Reading an
        # *error* as "no failing checks" is the fail-open bug guard-admin-merge closed.
        return ([], []) if out.returncode == 0 else None
    try:
        rows = json.loads(_decolorize(text))
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list):
        return None
    return parse_checks(rows)


def _base_protected(owner_repo: str, base: str) -> bool | None:
    """True = protection with at least one required status check, False = the branch
    enforces nothing (403 on a free plan, 404 unprotected, protection without required
    checks, or an EMPTY required-checks list), None = undeterminable (→ fail-closed).

    The empty list matters: `required_status_checks` can be present with `contexts: []`
    and `checks: []`, which is truthy but requires nothing — auto-merge would wait for
    nothing and merge red, exactly as on an unprotected branch. Only a non-empty list
    gives `--auto` something to wait on.
    """
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{owner_repo}/branches/{base}/protection"],
            capture_output=True,
            env=_gh_env(),
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    if out.returncode != 0:
        err = f"{out.stderr or ''}{out.stdout or ''}"
        if "HTTP 403" in err or "HTTP 404" in err or "Branch not protected" in err:
            return False
        return None
    try:
        data = json.loads(_decolorize(out.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    required = data.get("required_status_checks")
    if not isinstance(required, dict):
        return False
    contexts = required.get("contexts") or []
    checks = required.get("checks") or []
    return bool(contexts or checks)


def _pr_snapshot(
    pr: str,
    repo: str | None = None,
    cwd: str | None = None,
) -> tuple[dict | None, tuple[list[str], list[str]] | None]:
    """Read independent PR metadata and check state concurrently."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        meta_future = pool.submit(_pr_meta, pr, repo, cwd)
        states_future = pool.submit(_check_states, pr, repo, cwd)
        return meta_future.result(), states_future.result()


_FOOTER = (
    "GitHub will merge a draft or a red PR without complaint — branch protection stops only\n"
    "what it was configured to require. That is the gap this hook covers. If the merge is genuinely intended, a human can\n"
    "run it directly, outside the agent harness.\n\n"
    "Hook source: .claude/hooks/guard-pr-merge.py\n"
)


def _block_msg(reason: str, guidance: str) -> str:
    return f"BLOCKED by guard-pr-merge: {reason}.\n\n{guidance}\n\n{_FOOTER}"


def _judge(args: list[str], cwd: str | None = None) -> str | None:
    """Block message for this `gh pr merge`, or None to allow."""
    if _UNREADABLE_MARKER in args:
        return _block_msg(
            "this merge's target cannot be read from the command itself",
            "The PR is not named here — it arrives on stdin (`xargs`), or is buried under more\n"
            "layers of `bash -c` than this guard unwraps. Judging the current branch's PR\n"
            "instead would verify one PR while gh merges another. Run the merge with the PR\n"
            "named explicitly (`gh pr merge <number> ...`).",
        )
    repo = _repo_option(args)
    pr = _pr_ref(args, repo, cwd=cwd)
    if not pr:
        return _block_msg(
            "could not determine which PR this merges",
            "Name the PR explicitly (`gh pr merge <number> ...`) so the merge can be verified.",
        )
    meta, states = _pr_snapshot(pr, repo, cwd=cwd)
    if meta is None:
        return _block_msg(
            f"could not verify PR {pr}'s draft status (gh error, timeout, or unexpected schema)",
            "An unverifiable merge is refused, not assumed safe. Re-check the PR with\n"
            "`gh pr view` and retry once gh answers.",
        )
    reason = readiness_reason(meta, states)
    if reason == "PR is a DRAFT":
        return _block_msg(
            f"PR {pr} is a DRAFT",
            "Draft PRs are never merged or armed — a draft is by definition not review-ready\n"
            "(the #189 incident: a draft was squash-merged before anyone reviewed it). Mark it\n"
            "ready (`python -m scripts.publish pr-ready --number <N>`) and get the review gate first.",
        )
    if reason == "check states unverifiable":
        return _block_msg(
            f"could not verify PR {pr} check states (gh error, timeout, or an unrecognized check state)",
            "An unverifiable merge is refused, not assumed safe. Re-read the checks with\n"
            "`gh pr checks` and retry once gh answers.",
        )
    failing, pending = states
    if reason == "FAILING checks":
        return _block_msg(
            f"PR {pr} has FAILING checks: {', '.join(failing)}",
            "Every non-advisory check counts, whether or not GitHub marks it required —\n"
            "'required' is a config accident, red is red. Fix the failures and re-run;\n"
            "do not merge over them.",
        )
    if _flag_enabled(_classify(args)[0], "auto"):
        base = str(meta.get("baseRefName") or "")
        if not base:
            return _block_msg(
                f"could not determine PR {pr}'s base branch",
                "--auto can only be verified against a known base branch.",
            )
        owner_repo = _owner_repo_from_url(str(meta.get("url") or ""))
        if not owner_repo:
            return _block_msg(
                f"could not determine which repo owns PR {pr} (no usable PR url)",
                "--auto is refused while its safety is unverifiable.",
            )
        protected = _base_protected(owner_repo, base)
        if protected is None:
            return _block_msg(
                f"could not determine whether {owner_repo}@{base} is protected (gh error/timeout)",
                "--auto is refused while its safety is unverifiable.",
            )
        if not protected:
            return _block_msg(
                f"--auto on {owner_repo}@{base}, which has no required status checks",
                "auto-merge fires regardless of checks here — merge manually after an explicit\n"
                "all-green read. Auto-merge only ever waits for REQUIRED checks, and this branch\n"
                "has none, so arming it merges the moment the PR is mergeable (two merges landed\n"
                "red this way).",
            )
        # Protected base with required checks: --auto is what it claims to be, so
        # still-running checks are exactly what it will wait for.
        return None
    if reason == "checks still running":
        return _block_msg(
            f"PR {pr} has checks still running: {', '.join(pending)}",
            "Wait for them to finish and read the result, or re-run with --auto — which this\n"
            "guard allows once it confirms the base branch really does have required checks\n"
            "for auto-merge to wait on. Merging now merges an unknown result.",
        )
    return None


def main() -> int:
    payload = _CLI_PAYLOAD if __name__ == "__main__" else _read_payload()
    if payload is None or not isinstance(payload.get("tool_input", {}), dict):
        sys.stderr.write(_block_msg("malformed hook payload", "Provide a Bash command object for review."))
        return 2
    if not isinstance(payload.get("tool_input", {}).get("command", ""), str):
        sys.stderr.write(_block_msg("malformed hook command", "Provide a literal Bash command for review."))
        return 2
    command = _command(payload)
    # Fast path: only engage on `gh ... pr ... merge` (leave every other command untouched).
    # Quote/backslash marks are dropped first, because the shell drops them BEFORE running
    # the command: `g\h pr merge 5` and `g'h' pr merge 5` both execute gh (verified:
    # `bash -c 'g\h --version'` prints gh's version). Testing the raw source would let a
    # merge past this early return before the real parser ever sees it. Normalizing only
    # ever sends MORE commands to the full parse — never fewer.
    if not _may_merge(command):
        return 0
    # Each segment arrives carrying the cwd it runs in, so a PR number is judged in the
    # repo the MERGE runs in, not the session's repo — `cd private-repo && gh pr merge 203`
    # judged from the public repo resolves a DIFFERENT PR #203, wrong in BOTH directions
    # (false block, or worse: false allow off a same-numbered green PR). Scoping that cwd
    # to its own shell level is _judged_segments' job: it is the only reader that knows
    # where a subshell or `bash -c` payload begins and ends.
    try:
        segments = read_commands(command, cwd=payload.get("cwd") or os.getcwd())
    except Exception as exc:
        sys.stderr.write(
            _block_msg(
                f"shell command cannot be read: {str(exc) if isinstance(exc, ShellParseError) else type(exc).__name__}",
                f"Use a literal merge command. Repair parser installation: {REPAIR}",
            )
        )
        return 2
    if re.search(r"\bmerge\b", command) and ("<(" in command or ">(" in command):
        sys.stderr.write(
            _block_msg(
                "process-substitution merge scope cannot be read", f"Use a literal merge command; repair: {REPAIR}"
            )
        )
        return 2
    for seg in segments:
        args = _merge_args(seg.argv)
        if args is not None and (any(row.redirect_unknown for row in segments) or "<(" in command or ">(" in command):
            args = [*args, UNREADABLE]
        if args is None:
            continue
        if UNREADABLE in args:
            sys.stderr.write(
                _block_msg("merge arguments cannot be read", f"Use literal arguments; repair parser: {REPAIR}")
            )
            return 2
        # `-R owner/repo` names the repo outright, so this merge does not depend on the cwd
        # it runs in — and an unreadable cwd has nothing left to fail closed about. Blocking
        # anyway made the escape hatch this very message advertises a no-op (#5333 r2).
        # Verified against real gh from /tmp, which is not a git repo at all:
        # `gh pr view 9 --repo cli/cli --json number` -> rc=0 `{"number":9}`. Without a
        # selector gh refuses (`argument required when using the --repo flag` -> rc=1), so
        # `-R` alone cannot wave a merge through: _pr_ref reads that rc and fails closed.
        if seg.cwd_unreadable and not _repo_option(args):
            sys.stderr.write(
                _block_msg(
                    "this merge's working directory cannot be read (a `cd` to a variable, "
                    "a substitution, or `cd -`; or a shell nesting this guard cannot follow)",
                    "The guard must judge the PR in the repo the merge actually runs in.\n"
                    "Use a literal `cd /path && gh pr merge ...`, or name the repo with\n"
                    "`-R owner/repo` (with the PR number: `gh pr merge 5 -R owner/repo`).",
                )
            )
            return 2
        # An unreadable cwd is a guess, not a location — `-R` got us here, so let gh resolve
        # from the repo name in this hook's own cwd rather than hand it a stale directory.
        blocked = _judge(args, cwd=None if seg.cwd_unreadable else seg.cwd)
        if blocked:
            sys.stderr.write(blocked)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
