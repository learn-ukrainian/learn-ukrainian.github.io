"""Fail a merge-queue candidate unless every member PR's current head carries an approved review.

GitHub's merge queue builds each candidate on top of the entry ahead of it: the event's
``base_sha`` is that entry's candidate, not the branch, and the
``gh-readonly-queue/<branch>/pr-<N>-<base>`` ref names only the last PR. (Run 42975253378
built #12959 on #12956's candidate two minutes before #12956 merged.) Membership is
therefore proven, never guessed:

1. One GraphQL read returns the branch tip and every merge-queue entry, paginated until
   the reported total is reached.
2. Git gives the first-parent chain from the candidate's merge base with that tip to the
   candidate. Commits below the merge base have landed, each after its own candidate
   passed this gate. Each chain commit must be one squash commit (exactly one parent, the
   previous commit) whose subject ends in ``(#N)``; the event's base must be an ancestor.
3. Every chain commit must be the ``headCommit`` of exactly one entry, whose pull request
   is open against the branch and has the number in the commit subject. The chain's last
   commit must belong to the PR the ref names.
4. The PR's current head must be the head the candidate included: merging that head into
   the squash commit's parent with ``git merge-tree --write-tree`` must reproduce the
   squash commit's tree, and GitHub must have a check suite for that head created before the
   entry's ``enqueuedAt``: no GitHub field names the entry's source head, and a head pushed
   after the enqueue (even one with an identical tree, or an empty commit) fails.
5. GitHub's latest ``fleet/cross-family-review`` status on that head must be ``success``.
   GitHub keeps one current state per context (the newest wins), so an older success
   never overrides a later failure, and a moved head carries no approval at all.

Any API error, unreadable Git object, malformed field or disagreement fails closed. API
errors and membership disagreements (an entry merging between reads) are retried a
bounded number of times on a fresh read; a review finding is final.

This guards against an accidental landing without review. It is not a trust boundary: a
status written with the shared credential, or a candidate that edits this workflow, is
outside what it checks.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

STATUS_CONTEXT = "fleet/cross-family-review"
GITHUB_HTTPS = "https://github.com/"
GIT_TIMEOUT_SECONDS = 300
API_TIMEOUT_SECONDS = 30
MAX_PAGES = 20
DEFAULT_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 15.0

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_PR_SUFFIX = re.compile(r"\(#([1-9][0-9]*)\)\Z")

QUEUE_QUERY = """
query($owner: String!, $name: String!, $branch: String!, $qualified: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    ref(qualifiedName: $qualified) { target { oid } }
    mergeQueue(branch: $branch) {
      entries(first: 100, after: $after) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes {
          position
          enqueuedAt
          headCommit { oid }
          pullRequest { number state baseRefName headRefOid }
        }
      }
    }
  }
}
"""

Post = Callable[[str, dict], object]


class GateError(Exception):
    """The candidate cannot be shown to be reviewed; final."""


class Retryable(GateError):
    """An API failure or a membership disagreement that a fresh read may resolve."""


@dataclass(frozen=True)
class Event:
    repository: str
    branch: str
    base: str
    head: str
    ref_pr: int


@dataclass(frozen=True)
class Squash:
    sha: str
    parent: str
    pr: int


@dataclass(frozen=True)
class Member:
    squash: Squash
    position: int
    head: str
    enqueued_at: datetime


@dataclass(frozen=True)
class HeadFacts:
    state: str | None
    seen_before_enqueue: bool


def parse_event(payload: object) -> Event:
    """The merge-group identity from the event, validated field by field."""
    try:
        if not isinstance(payload, dict) or payload["action"] != "checks_requested":
            raise ValueError("not a checks_requested merge_group event")
        group = payload["merge_group"]
        repository = payload["repository"]["full_name"]
        base, head = group["base_sha"], group["head_sha"]
        base_ref, head_ref = group["base_ref"], group["head_ref"]
        if not all(isinstance(value, str) for value in (repository, base, head, base_ref, head_ref)):
            raise ValueError("event identity fields must be strings")
        if not _REPOSITORY.fullmatch(repository) or not _SHA.fullmatch(base) or not _SHA.fullmatch(head):
            raise ValueError("invalid repository or SHA")
        if not base_ref.startswith("refs/heads/") or len(base_ref) == len("refs/heads/"):
            raise ValueError("invalid base ref")
        branch = base_ref.removeprefix("refs/heads/")
        match = re.fullmatch(
            rf"refs/heads/gh-readonly-queue/{re.escape(branch)}/pr-([1-9][0-9]*)-([0-9a-f]{{40}})", head_ref
        )
        if match is None or match[2] != base or base == head:
            raise ValueError("queue ref does not match the event's base")
    except (KeyError, TypeError, ValueError) as error:
        raise GateError(f"merge_group event unreadable: {error}") from None
    return Event(repository, branch, base, head, int(match[1]))


def _git(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT_SECONDS, env=env
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GateError(f"git {args[0]} failed: {error}") from None


def _git_out(*args: str, env: dict[str, str] | None = None) -> str:
    result = _git(*args, env=env)
    if result.returncode != 0:
        raise GateError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout.strip()


def _fetch_env(remote: str) -> dict[str, str] | None:
    """Token header through the environment, never argv; nothing is persisted."""
    token = os.environ.get("GITHUB_TOKEN")
    url = _git("remote", "get-url", remote).stdout.strip()
    if not token or not url.startswith(GITHUB_HTTPS):
        return None
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    return {
        **os.environ,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": f"http.{GITHUB_HTTPS}.extraheader",
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
    }


def ensure_commit(sha: str, remote: str = "origin") -> None:
    """Make ``sha`` readable locally, fetching it from ``remote`` when absent."""
    if _git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0:
        return
    fetched = _git("fetch", "--no-tags", "--quiet", remote, sha, env=_fetch_env(remote))
    if fetched.returncode != 0 or _git("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        raise Retryable(f"commit {sha[:12]} unavailable (fetch exit {fetched.returncode})")


def squash_chain(event: Event, tip: str) -> list[Squash]:
    """The candidate's unlanded first-parent chain, oldest first, each commit one PR's squash.

    The event's base is the previous entry's candidate, not the branch, so the chain starts
    at the candidate's merge base with the branch tip. Everything below it has landed.
    """
    ensure_commit(tip)
    bases = _git_out("merge-base", "--all", tip, event.head).split()
    if len(bases) != 1:
        raise GateError("the candidate has no single merge base with the branch tip")
    boundary = bases[0]
    shas = _git_out("rev-list", "--first-parent", "--reverse", f"{boundary}..{event.head}").split()
    if not shas or shas[-1] != event.head:
        raise GateError("the candidate is already on the branch or its chain does not end at it")
    if _git("merge-base", "--is-ancestor", event.base, event.head).returncode != 0:
        raise GateError("the event base is not an ancestor of the candidate")
    chain: list[Squash] = []
    previous = boundary
    for sha in shas:
        parents = _git_out("rev-list", "--parents", "-n", "1", sha).split()[1:]
        if parents != [previous]:
            raise GateError(f"queue commit {sha[:12]} is not a single-parent squash on the chain")
        match = _PR_SUFFIX.search(_git_out("log", "-1", "--format=%s", sha))
        if match is None:
            raise GateError(f"queue commit {sha[:12]} subject does not end in (#N)")
        chain.append(Squash(sha, previous, int(match[1])))
        previous = sha
    return chain


def graphql_post() -> Post:
    """GraphQL through the shared GitHub client; any failure raises Retryable.

    The client authenticates from ``GITHUB_TOKEN`` in the environment, so the credential
    never appears on argv, and ``fresh=True`` never answers from its cache.
    """
    from scripts.common import github_client

    def post(query: str, variables: dict) -> object:
        argv = ["gh", "api", "graphql", "-f", f"query={query}"]
        for name, value in variables.items():
            if value is not None:
                argv += ["-f", f"{name}={value}"]
        try:
            completed = github_client.run(argv, fresh=True, capture_output=True, text=True, timeout=API_TIMEOUT_SECONDS)
        except Exception as error:  # rate limit, transport or client refusal: never an answer
            raise Retryable(f"GraphQL request failed: {type(error).__name__}") from None
        if completed.returncode != 0:
            raise Retryable(f"GraphQL request failed (exit {completed.returncode})")
        try:
            document: object = json.loads(completed.stdout)
        except ValueError:
            raise Retryable("GraphQL response undecodable") from None
        return document

    return post


def _data(document: object) -> dict:
    data = document.get("data") if isinstance(document, dict) and not document.get("errors") else None
    if not isinstance(data, dict):
        raise Retryable("GraphQL returned errors or no data")
    return data


def read_queue(post: Post, event: Event) -> tuple[str, list[dict]]:
    """The branch tip and every queue entry, read until the reported total is complete."""
    owner, name = event.repository.split("/", 1)
    variables = {"owner": owner, "name": name, "branch": event.branch, "qualified": f"refs/heads/{event.branch}"}
    tip: str | None = None
    total: int | None = None
    entries: list[dict] = []
    after: str | None = None
    for _ in range(MAX_PAGES):
        try:
            repository = _data(post(QUEUE_QUERY, {**variables, "after": after}))["repository"]
            page_tip = repository["ref"]["target"]["oid"]
            connection = repository["mergeQueue"]["entries"]
            page_total, info, nodes = connection["totalCount"], connection["pageInfo"], connection["nodes"]
            more, after = info["hasNextPage"], info["endCursor"]
        except (KeyError, TypeError) as error:
            raise Retryable(f"queue read malformed: {type(error).__name__}") from None
        if not isinstance(page_tip, str) or not _SHA.fullmatch(page_tip) or (tip is not None and page_tip != tip):
            raise Retryable("branch tip missing or changed between pages")
        if type(page_total) is not int or (total is not None and page_total != total) or not isinstance(nodes, list):
            raise Retryable("queue total missing or changed between pages")
        tip, total = page_tip, page_total
        entries.extend(nodes)
        if more is not True:
            break
        if not isinstance(after, str) or not after:
            raise Retryable("queue page cursor missing")
    else:
        raise Retryable("queue has more pages than the read limit")
    if len(entries) != total:
        raise Retryable(f"queue read returned {len(entries)} of {total} entries")
    return tip, entries


def _timestamp(value: object) -> datetime:
    """A GitHub server timestamp (``2026-11-11T09:30:37Z``), timezone-aware."""
    try:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ValueError
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise Retryable("GitHub timestamp missing or malformed") from None
    if parsed.tzinfo is None:
        raise Retryable("GitHub timestamp has no timezone")
    return parsed


def resolve_members(event: Event, chain: list[Squash], entries: list[dict]) -> list[Member]:
    """Map every unlanded chain commit to exactly one queue entry and its PR's current head."""
    by_commit: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise Retryable("queue entry malformed")
        commit = entry.get("headCommit")
        if commit is None:
            continue  # not built yet: behind every running candidate
        oid = commit.get("oid") if isinstance(commit, dict) else None
        if not isinstance(oid, str) or not _SHA.fullmatch(oid) or oid in by_commit:
            raise Retryable("queue entry commit malformed or duplicated")
        by_commit[oid] = entry
    members: list[Member] = []
    for squash in chain:
        if squash.sha not in by_commit:
            raise Retryable(f"queue commit {squash.sha[:12]} (#{squash.pr}) has no queue entry and has not landed")
        entry = by_commit[squash.sha]
        pr, position = entry.get("pullRequest"), entry.get("position")
        if not isinstance(pr, dict) or type(position) is not int:
            raise Retryable("queue entry pull request malformed")
        enqueued_at = _timestamp(entry.get("enqueuedAt"))
        number, head = pr.get("number"), pr.get("headRefOid")
        if number != squash.pr:
            raise GateError(f"queue commit {squash.sha[:12]} says #{squash.pr} but its entry is #{number}")
        if pr.get("state") != "OPEN" or pr.get("baseRefName") != event.branch:
            raise Retryable(f"#{number} is not open against {event.branch}")
        if not isinstance(head, str) or not _SHA.fullmatch(head):
            raise Retryable(f"#{number} head unreadable")
        members.append(Member(squash, position, head, enqueued_at))
    numbers = [member.squash.pr for member in members]
    if len(set(numbers)) != len(numbers):
        raise GateError("a pull request appears twice in the candidate")
    if members[-1].squash.sha != event.head or numbers[-1] != event.ref_pr:
        raise GateError(f"the candidate's last commit does not belong to #{event.ref_pr}")
    return members


def includes_head(member: Member) -> bool:
    """True only when the PR's current head, merged into the squash parent, gives the squash tree."""
    ensure_commit(member.head)
    merged = _git("merge-tree", "--write-tree", member.squash.parent, member.head)
    tree = merged.stdout.split("\n", 1)[0].strip()
    return (
        merged.returncode == 0
        and _SHA.fullmatch(tree) is not None
        and tree == _git_out("rev-parse", f"{member.squash.sha}^{{tree}}")
    )


def head_facts(post: Post, event: Event, members: list[Member]) -> dict[str, HeadFacts]:
    """Each member head's current review state, and whether GitHub saw that head before the enqueue.

    No GitHub field names the source head a queue entry was built from. A head that differs from
    the included one reached the repository after the entry was enqueued, and so did every check
    suite GitHub created for it. A check suite created before ``enqueuedAt`` (a server timestamp)
    therefore shows the current head predates the entry; a head pushed afterwards, even with an
    identical tree, fails.
    """
    owner, name = event.repository.split("/", 1)
    declarations = "".join(f", $h{index}: GitObjectID!" for index in range(len(members)))
    fields = "".join(
        f" h{index}: object(oid: $h{index}) {{ ... on Commit {{ oid"
        " status { context(name: $context) { state } }"
        " checkSuites(first: 100) { totalCount nodes { createdAt } } } }"
        for index in range(len(members))
    )
    query = f"query($owner: String!, $name: String!, $context: String!{declarations}) {{ repository(owner: $owner, name: $name) {{{fields} }} }}"
    variables = {"owner": owner, "name": name, "context": STATUS_CONTEXT}
    variables.update({f"h{index}": member.head for index, member in enumerate(members)})
    repository = _data(post(query, variables)).get("repository")
    if not isinstance(repository, dict):
        raise Retryable("review status read returned no repository")
    facts: dict[str, HeadFacts] = {}
    for index, member in enumerate(members):
        head = member.head
        try:
            commit = repository[f"h{index}"]
            if commit["oid"] != head:
                raise ValueError
            status = commit["status"]
            context = None if status is None else status["context"]
            state = None if context is None else context["state"]
            suites = commit["checkSuites"]
            created = [_timestamp(node["createdAt"]) for node in suites["nodes"]]
            total = suites["totalCount"]
        except (KeyError, TypeError, ValueError):
            raise Retryable(f"review status unreadable for {head[:12]}") from None
        if state is not None and not isinstance(state, str):
            raise Retryable(f"review status malformed for {head[:12]}")
        seen = any(moment < member.enqueued_at for moment in created)
        if not seen and type(total) is int and total > len(created):
            raise Retryable(f"check suites for {head[:12]} exceed one page")
        facts[head] = HeadFacts(state, seen)
    return facts


def evaluate(event: Event, post: Post) -> list[str]:
    """Findings for one complete read; an empty list means every member is approved."""
    tip, entries = read_queue(post, event)
    members = resolve_members(event, squash_chain(event, tip), entries)
    facts = head_facts(post, event, members)
    findings: list[str] = []
    for member in members:
        label = f"#{member.squash.pr} (queue position {member.position}, candidate commit {member.squash.sha[:12]}, head {member.head})"
        if not includes_head(member):
            findings.append(f"{label}: the candidate was not built from this PR's current head")
            continue
        if not facts[member.head].seen_before_enqueue:
            findings.append(f"{label}: the current head reached GitHub after the PR was enqueued")
            continue
        state = facts[member.head].state
        if state is None:
            findings.append(f"{label}: no {STATUS_CONTEXT} status on the current head")
        elif state != "SUCCESS":
            findings.append(f"{label}: latest {STATUS_CONTEXT} status is {state.lower()}, not success")
        else:
            print(f"{label}: {STATUS_CONTEXT} success")
    return findings


def run(event: Event, post: Post, *, attempts: int, delay: float, sleep: Callable[[float], None] = time.sleep) -> int:
    for attempt in range(1, attempts + 1):
        try:
            findings = evaluate(event, post)
        except Retryable as error:
            print(f"attempt {attempt}/{attempts}: {error}", file=sys.stderr)
            if attempt == attempts:
                print(f"::error::queue review gate: candidate unverifiable: {error}")
                return 1
            sleep(delay)
            continue
        except GateError as error:
            print(f"::error::queue review gate: candidate unverifiable: {error}")
            return 1
        for finding in findings:
            print(f"::error::queue review gate: {finding}")
        if not findings:
            print(f"queue review gate: every PR in candidate {event.head} has an approved current head")
        return int(bool(findings))
    return 1


def main(argv: list[str] | None = None) -> int:
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.ci._location import module_name

    module = module_name(__spec__, __file__)
    parser = argparse.ArgumentParser(
        description="Fail a merge-queue candidate unless every PR in it has an approved cross-family review\n"
        f"({STATUS_CONTEXT} = success) on its current head. Use inside ci.yml on merge_group only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            f"  .venv/bin/python -m {module}\n"
            f"  .venv/bin/python -m {module} --event-file event.json --attempts 1\n"
            "Inputs: GITHUB_EVENT_NAME=merge_group, GITHUB_EVENT_PATH, GITHUB_TOKEN; a checkout of the candidate\n"
            "with full first-parent history and an origin remote.\n"
            "Outputs: one line per member PR on stdout, ::error:: annotations; fetches missing commits, no other writes.\n"
            "Exit codes: 0 every member approved; 1 a member unapproved or the candidate unverifiable; 2 invalid arguments.\n"
            "Related: .github/workflows/ci.yml (CI Gate); docs/runbooks/ci-gate.md; scripts/review/record_cf_verdict.py."
        ),
    )
    parser.add_argument("--event-file", help="merge_group event JSON; default: $GITHUB_EVENT_PATH")
    parser.add_argument(
        "--attempts",
        type=int,
        default=DEFAULT_ATTEMPTS,
        help=f"fresh reads after an API error or membership disagreement; default: {DEFAULT_ATTEMPTS}",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY_SECONDS,
        help=f"seconds between reads; default: {DEFAULT_RETRY_DELAY_SECONDS:g}",
    )
    args = parser.parse_args(argv)
    if args.attempts < 1 or args.retry_delay < 0:
        parser.error("--attempts must be at least 1 and --retry-delay non-negative")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event_file = args.event_file or os.environ.get("GITHUB_EVENT_PATH", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    try:
        if event_name != "merge_group":
            raise GateError(f"unsupported event {event_name!r}; this gate runs on merge_group only")
        if not event_file or not token:
            raise GateError("GITHUB_EVENT_PATH (or --event-file) and GITHUB_TOKEN are required")
        try:
            payload = json.loads(Path(event_file).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise GateError(f"event file unreadable: {type(error).__name__}") from None
        event = parse_event(payload)
    except GateError as error:
        print(f"::error::queue review gate: {error}")
        return 1
    return run(event, graphql_post(), attempts=args.attempts, delay=args.retry_delay)


if __name__ == "__main__":
    sys.exit(main())
