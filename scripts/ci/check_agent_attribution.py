"""Fail a landed or proposed commit that carries no ``X-Agent`` attribution (#10736).

The contract is a LINE, not a Git trailer: ``^X-Agent: <agent>/<task-id>$`` somewhere
in the landed message. GitHub appends its own ``Co-authored-by`` paragraph to a squash
message, so the attribution is never the final paragraph and ``%(trailers)`` parsing
cannot see it; a line match can.

Modes
=====
``--merge-group BASE HEAD``
    ``BASE``/``HEAD`` are ``merge_group.base_sha``/``head_sha``. Each first-parent commit
    in ``BASE..HEAD`` is one pull request's squash commit with a terminal ``(#N)`` in its
    subject. For EACH commit this requires (a) at least one well-formed line and (b) that
    every distinct value found over the PR's own commits (fetched from
    ``refs/pull/N/head``) also appears in the landed message, so one PR's attribution
    cannot mask another's omission and a requeue with new heads is checked afresh.
``--pr BASE HEAD``
    Every non-merge commit in ``BASE..HEAD`` of a pull request carries a well-formed line.

Bot exemption
=============
A commit with no line is exempt only when GitHub's REST commit object for that exact SHA
proves an allowlisted app bot (``scripts.review.app_bot_authorship``). A Git author name or
a ``[bot]`` suffix proves nothing. A merge-group commit with no line is exempt only when
EVERY commit of its PR is so verified; a PR that mixes bot and agent commits keeps the
agent attribution requirement.

Fail closed
===========
A git or fetch error, a missing ``(#N)``, an empty chain, a non-ancestor base, a
non-squash commit shape, an unverifiable exemption or a malformed value is a typed
violation. Messages name codes, PR numbers and short SHAs; a malformed value is never
echoed.

Report-only switch
==================
Violations fail the run (exit 1) only when ``ATTRIBUTION_ENFORCE=1``. Any other value
prints the same findings as warnings and exits 0 until the repository setting that
produces the line is restored; invalid usage always exits 2. The step is documented in
``docs/runbooks/agent-attribution.md``.

Examples
========

    .venv/bin/python scripts/ci/check_agent_attribution.py --pr origin/main HEAD
    .venv/bin/python scripts/ci/check_agent_attribution.py --merge-group "$BASE_SHA" "$HEAD_SHA"
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.review.app_bot_authorship import verified_app_bot_login

ENFORCE_ENV = "ATTRIBUTION_ENFORCE"
GIT_TIMEOUT_SECONDS = 120
API_TIMEOUT_SECONDS = 30
_API_ROOT = "https://api.github.com"
_GITHUB_HTTPS = "https://github.com/"

# Any line that claims to be attribution; the grammar below decides whether it is one.
_CANDIDATE_LINE = re.compile(r"^X-Agent:.*$", re.MULTILINE)
_WELL_FORMED = re.compile(r"^X-Agent: (?P<value>[a-z][a-z0-9]*(?:-[a-z0-9]+)*/[A-Za-z0-9._-]+)$")
# The squash headline ends in the PR number; earlier "(#N)" references are issues.
_PR_SUFFIX = re.compile(r"\(#(?P<number>[1-9][0-9]*)\)$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

# GET path -> decoded JSON; raises on any transport or API failure.
GitHubGet = Callable[[str], object]


class GitFailure(Exception):
    """A git command failed; carries a value-light description."""


@dataclass(frozen=True)
class Violation:
    code: str
    detail: str
    commit: str | None = None
    pr: int | None = None

    def render(self) -> str:
        parts = [self.code]
        if self.pr is not None:
            parts.append(f"pr=#{self.pr}")
        if self.commit is not None:
            parts.append(f"commit={self.commit[:12]}")
        parts.append(self.detail)
        return " ".join(parts)


@dataclass(frozen=True)
class Attribution:
    """Attribution lines of one message: well-formed values and the count of malformed lines."""

    values: tuple[str, ...]
    malformed: int


@dataclass
class Report:
    mode: str
    checked: int = 0
    violations: list[Violation] = field(default_factory=list)


def extract_attribution(message: str) -> Attribution:
    """Well-formed ``X-Agent`` values (first-seen order, distinct) and the malformed-line count."""
    values: list[str] = []
    malformed = 0
    for match in _CANDIDATE_LINE.finditer(message):
        line = match.group(0)
        strict = _WELL_FORMED.fullmatch(line)
        if strict is None:
            malformed += 1
        elif strict.group("value") not in values:
            values.append(strict.group("value"))
    return Attribution(tuple(values), malformed)


def pr_number_from_subject(subject: str) -> int | None:
    """The terminal ``(#N)`` of a squash headline, else None."""
    match = _PR_SUFFIX.search(subject.rstrip())
    return int(match.group("number")) if match else None


def _git(*args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
            env=env,
            cwd=cwd,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitFailure(f"git {args[0]} did not run: {type(exc).__name__}") from exc
    if result.returncode != 0:
        raise GitFailure(f"git {args[0]} exited {result.returncode}")
    return result.stdout


def _resolve_commit(ref: str) -> str:
    sha = _git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()
    if not _SHA.fullmatch(sha):
        raise GitFailure("rev-parse returned no commit")
    return sha


def _commit(sha: str) -> tuple[tuple[str, ...], str]:
    """(parents, raw message) of ``sha`` from the commit object, byte for byte."""
    raw = _git("cat-file", "commit", sha)
    header, separator, message = raw.partition("\n\n")
    if not separator:
        raise GitFailure("commit object has no message separator")
    parents = tuple(line.split(" ", 1)[1] for line in header.split("\n") if line.startswith("parent "))
    return parents, message


def _bot_verified(get: GitHubGet | None, repository: str | None, sha: str) -> bool:
    """True only when GitHub's live REST object for exactly ``sha`` proves an allowlisted bot."""
    if get is None or repository is None or not _REPOSITORY.fullmatch(repository):
        return False
    try:
        commit = get(f"repos/{repository}/commits/{sha}")
    except Exception:
        return False
    return verified_app_bot_login(commit, sha, repository) is not None


def _source_commits(remote: str, pr: int, parent: str) -> tuple[str, ...]:
    """Non-merge commits of PR ``pr`` that its squash commit's first parent lacks."""
    env = None
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            url = _git("remote", "get-url", remote).strip()
        except GitFailure:
            url = ""
        if url.startswith(_GITHUB_HTTPS):
            # Header through the environment, never argv; credentials are not persisted.
            basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
            env = {
                **os.environ,
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": f"http.{_GITHUB_HTTPS}.extraheader",
                "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
            }
    _git("fetch", "--no-tags", "--quiet", remote, f"refs/pull/{pr}/head", env=env)
    head = _resolve_commit("FETCH_HEAD")
    listing = _git("rev-list", "--no-merges", f"{parent}..{head}")
    return tuple(listing.split())


def _bad_attribution(attribution: Attribution, sha: str, pr: int | None) -> Violation | None:
    if attribution.malformed:
        return Violation(
            "MALFORMED_ATTRIBUTION",
            f"{attribution.malformed} X-Agent line(s) do not match '<agent>/<task-id>'",
            sha,
            pr,
        )
    return None


def check_pr(base: str, head: str, *, github_get: GitHubGet | None = None, repository: str | None = None) -> Report:
    """Every non-merge commit in ``base..head`` carries a well-formed line or is a verified bot's."""
    report = Report("pr")
    try:
        base_sha, head_sha = _resolve_commit(base), _resolve_commit(head)
        shas = _git("rev-list", "--no-merges", f"{base_sha}..{head_sha}").split()
    except GitFailure as exc:
        report.violations.append(Violation("GIT_ERROR", str(exc)))
        return report
    if not shas:
        report.violations.append(Violation("EMPTY_CHAIN", "no non-merge commit in the range"))
        return report
    for sha in shas:
        report.checked += 1
        try:
            _, message = _commit(sha)
        except GitFailure as exc:
            report.violations.append(Violation("GIT_ERROR", str(exc), sha))
            continue
        attribution = extract_attribution(message)
        bad = _bad_attribution(attribution, sha, None)
        if bad is not None:
            report.violations.append(bad)
        elif not attribution.values and not _bot_verified(github_get, repository, sha):
            report.violations.append(
                Violation("MISSING_ATTRIBUTION", "no X-Agent line and no verified app-bot authorship", sha)
            )
    return report


def check_merge_group(
    base: str,
    head: str,
    *,
    remote: str = "origin",
    github_get: GitHubGet | None = None,
    repository: str | None = None,
) -> Report:
    """Each squash commit in the queue chain carries its PR's complete attribution."""
    report = Report("merge-group")
    try:
        base_sha, head_sha = _resolve_commit(base), _resolve_commit(head)
        _git("merge-base", "--is-ancestor", base_sha, head_sha)
        chain = _git("rev-list", "--first-parent", f"{base_sha}..{head_sha}").split()
    except GitFailure as exc:
        report.violations.append(Violation("GIT_ERROR", f"base is not an ancestor of head or unreadable: {exc}"))
        return report
    if not chain:
        report.violations.append(Violation("EMPTY_CHAIN", "no commit between base and head"))
        return report
    for sha in chain:
        report.checked += 1
        try:
            parents, message = _commit(sha)
        except GitFailure as exc:
            report.violations.append(Violation("GIT_ERROR", str(exc), sha))
            continue
        if len(parents) != 1:
            report.violations.append(
                Violation(
                    "UNEXPECTED_SHAPE", f"queue commit has {len(parents)} parents; expected one squash commit", sha
                )
            )
            continue
        report.violations.extend(
            _check_squash(sha, parents[0], message, remote=remote, github_get=github_get, repository=repository)
        )
    return report


def _check_squash(
    sha: str,
    parent: str,
    message: str,
    *,
    remote: str,
    github_get: GitHubGet | None,
    repository: str | None,
) -> list[Violation]:
    subject = message.split("\n", 1)[0]
    pr = pr_number_from_subject(subject)
    if pr is None:
        return [Violation("MISSING_PR_REFERENCE", "subject does not end in (#N)", sha)]
    landed = extract_attribution(message)
    bad = _bad_attribution(landed, sha, pr)
    if bad is not None:
        return [bad]
    try:
        sources = _source_commits(remote, pr, parent)
    except GitFailure as exc:
        return [Violation("FETCH_FAILED", f"cannot read refs/pull/{pr}/head: {exc}", sha, pr)]
    if not sources:
        return [Violation("EMPTY_SOURCE", f"refs/pull/{pr}/head adds no non-merge commit", sha, pr)]

    problems: list[Violation] = []
    expected: list[str] = []
    unattributed: list[str] = []
    for source in sources:
        try:
            _, source_message = _commit(source)
        except GitFailure as exc:
            problems.append(Violation("GIT_ERROR", str(exc), source, pr))
            continue
        attribution = extract_attribution(source_message)
        bad = _bad_attribution(attribution, source, pr)
        if bad is not None:
            problems.append(bad)
            continue
        if attribution.values:
            expected.extend(v for v in attribution.values if v not in expected)
        else:
            unattributed.append(source)
    if problems:
        return problems

    if not landed.values:
        # Exempt only when every PR commit is a verified app bot's (no agent commit to attribute).
        if not expected and all(_bot_verified(github_get, repository, s) for s in sources):
            return []
        return [Violation("MISSING_ATTRIBUTION", "landed message has no X-Agent line", sha, pr)]
    for source in unattributed:
        if not _bot_verified(github_get, repository, source):
            problems.append(
                Violation(
                    "SOURCE_UNATTRIBUTED",
                    "PR commit has no X-Agent line and no verified app-bot authorship",
                    source,
                    pr,
                )
            )
    missing = [value for value in expected if value not in landed.values]
    if missing:
        problems.append(
            Violation(
                "INCOMPLETE_ATTRIBUTION",
                f"landed message omits {len(missing)} of {len(expected)} PR value(s): " + ", ".join(missing),
                sha,
                pr,
            )
        )
    return problems


def _github_get_from_env() -> GitHubGet | None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None

    def get(path: str) -> object:
        request = urllib.request.Request(
            f"{_API_ROOT}/{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError(f"GET {path} failed: {type(exc).__name__}") from exc

    return get


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--merge-group", nargs=2, metavar=("BASE", "HEAD"), help="check a merge queue chain")
    mode.add_argument("--pr", nargs=2, metavar=("BASE", "HEAD"), help="check every commit of a pull request")
    parser.add_argument("--remote", default="origin", help="remote that serves refs/pull/N/head (default: origin)")
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="OWNER/REPO for app-bot verification (default: $GITHUB_REPOSITORY)",
    )
    return parser


def main(argv: list[str] | None = None, *, github_get: GitHubGet | None = None) -> int:
    args = build_parser().parse_args(argv)
    get = github_get if github_get is not None else _github_get_from_env()
    if args.merge_group:
        report = check_merge_group(*args.merge_group, remote=args.remote, github_get=get, repository=args.repository)
    else:
        report = check_pr(*args.pr, github_get=get, repository=args.repository)

    enforce = os.environ.get(ENFORCE_ENV) == "1"
    level = "error" if enforce else "warning"
    for violation in report.violations:
        print(f"::{level} title=agent-attribution::{violation.render()}")
    state = "enforce" if enforce else f"report-only ({ENFORCE_ENV}!=1)"
    print(f"agent-attribution: mode={report.mode} commits={report.checked} violations={len(report.violations)} {state}")
    if report.violations and not enforce:
        print(f"agent-attribution: not failing the run; set {ENFORCE_ENV}=1 to enforce")
    return 1 if report.violations and enforce else 0


if __name__ == "__main__":
    sys.exit(main())
