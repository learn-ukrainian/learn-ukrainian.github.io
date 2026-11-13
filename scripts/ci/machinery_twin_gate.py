"""Fail a merge-queue candidate when a member PR changes a machinery path without a landed twin.

Decision TWIN-FREEZE-1113 (docs/decisions/decisions.yaml, dec-018). Until the product's in-tree
machinery copy is gone, a change to a path that machinery's rename map classifies as
``machinery`` lands in learn-ukrainian/machinery first. The product PR body then cites that
change on its own line::

    Machinery-Twin: learn-ukrainian/machinery#384 <40-hex merge commit SHA>

The gate checks, through the GitHub API (read-only), that the cited PR belongs to
learn-ukrainian/machinery, is merged into ``main`` and that the SHA is its merge commit. A
reference without the SHA does not count. An approved cutover deletion or forwarding
replacement cites the existing machinery PR that already holds the code; nothing new is needed.
Whether the cited change covers the product change is for the exact-head review, not this gate.

Classification comes from ``lu_machinery/lint/rename-map.json`` at the pinned machinery commit,
verified against its pinned SHA-256; a map that cannot be read or verified fails the gate. Paths
the map does not list are not machinery. The gate turns itself off once the merged branch tip
holds no machinery-classified path outside ``RESIDUAL_PATHS``.

On ``merge_group`` (enforcing) every member PR of the candidate is checked, membership proven by
``scripts.ci.queue_review_gate``, each against its squash commit's paths and its body as read
when the gate runs, so a body edited after the PR's own CI still decides the landing. On
``pull_request`` the same check only warns: ``ci.yml`` does not rerun on body edits, and a red PR
gate would outlive a corrected body.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path

from scripts.ci.queue_review_gate import (
    API_TIMEOUT_SECONDS,
    DEFAULT_ATTEMPTS,
    DEFAULT_RETRY_DELAY_SECONDS,
    GateError,
    Retryable,
    _git_out,
    ensure_commit,
    graphql_post,
    parse_event,
    read_queue,
    resolve_members,
    squash_chain,
)

MACHINERY_REPOSITORY = "learn-ukrainian/machinery"
RENAME_MAP_PATH = "lu_machinery/lint/rename-map.json"
RENAME_MAP_COMMIT = "bbcbe9817ef20985b6677361079232a1d8beeddc"
RENAME_MAP_SHA256 = "5b72679da7cb48f4ed9805df256361f63aa40b0d6d37f54a79825699e5b5ef96"
# Machinery-classified paths the product keeps after the cutover (operator keep-list).
RESIDUAL_PATHS = frozenset({"scripts/dispatcher/providers/opencode.py"})

_CITATION = re.compile(
    rf"^[ \t]*Machinery-Twin:[ \t]*{re.escape(MACHINERY_REPOSITORY)}#([1-9][0-9]*)[ \t]+([0-9a-f]{{40}})[ \t]*\r?$",
    re.MULTILINE,
)
_SHA = re.compile(r"[0-9a-f]{40}\Z")

GetJson = Callable[[str], object]


def rest_get() -> GetJson:
    """REST GET through the shared GitHub client; any failure raises Retryable."""
    from scripts.common import github_client

    def get(path: str) -> object:
        try:
            completed = github_client.run(
                ["gh", "api", path], fresh=True, capture_output=True, text=True, timeout=API_TIMEOUT_SECONDS
            )
        except Exception as error:  # rate limit, transport or client refusal: never an answer
            raise Retryable(f"GET {path} failed: {type(error).__name__}") from None
        if completed.returncode != 0:
            raise Retryable(f"GET {path} failed (exit {completed.returncode})")
        try:
            return json.loads(completed.stdout)
        except ValueError:
            raise Retryable(f"GET {path} returned undecodable JSON") from None

    return get


def machinery_rows(get: GetJson) -> frozenset[str]:
    """Paths the pinned rename map classifies as machinery; anything unverifiable fails closed."""
    document = get(f"repos/{MACHINERY_REPOSITORY}/contents/{RENAME_MAP_PATH}?ref={RENAME_MAP_COMMIT}")
    try:
        if not isinstance(document, dict) or document.get("encoding") != "base64":
            raise ValueError("not a base64 file response")
        raw = base64.b64decode(document["content"], validate=False)
        if hashlib.sha256(raw).hexdigest() != RENAME_MAP_SHA256:
            raise ValueError("SHA-256 differs from the pin")
        rows = json.loads(raw)
        if not isinstance(rows, dict) or not rows:
            raise ValueError("not a non-empty object")
        if not all(isinstance(key, str) and value in ("machinery", "product") for key, value in rows.items()):
            raise ValueError("a row is not machinery or product")
    except (KeyError, TypeError, ValueError, binascii.Error) as error:
        raise GateError(f"rename map {RENAME_MAP_PATH}@{RENAME_MAP_COMMIT[:12]} unverified: {error}") from None
    return frozenset(path for path, owner in rows.items() if owner == "machinery")


def expired(merged_paths: Iterable[str], rows: frozenset[str]) -> bool:
    """True once merged product state holds no machinery path outside the agreed residual."""
    return not (rows.intersection(merged_paths) - RESIDUAL_PATHS)


def citation_problem(get: GetJson, number: int, sha: str) -> str | None:
    """Why ``Machinery-Twin: …#number sha`` is not landed evidence, or None when it is."""
    pull = get(f"repos/{MACHINERY_REPOSITORY}/pulls/{number}")
    try:
        repository = pull["base"]["repo"]["full_name"]  # type: ignore[index]
        base_ref = pull["base"]["ref"]  # type: ignore[index]
        merged, merge_sha = pull["merged"], pull["merge_commit_sha"]  # type: ignore[index]
    except (KeyError, TypeError):
        raise Retryable(f"{MACHINERY_REPOSITORY}#{number} unreadable") from None
    if repository != MACHINERY_REPOSITORY or base_ref != "main":
        return f"{MACHINERY_REPOSITORY}#{number} is not a pull request into {MACHINERY_REPOSITORY} main"
    if merged is not True:
        return f"{MACHINERY_REPOSITORY}#{number} is not merged"
    if merge_sha != sha:
        return f"{sha[:12]} is not the merge commit of {MACHINERY_REPOSITORY}#{number}"
    return None


def findings(
    changed: Iterable[str],
    body: str | None,
    *,
    rows: frozenset[str],
    merged_paths: Iterable[str],
    get: GetJson,
) -> list[str]:
    """Findings for one PR; an empty list means it may land."""
    if expired(merged_paths, rows):
        return []
    frozen = sorted(rows.intersection(changed))
    if not frozen:
        return []
    shown = ", ".join(frozen[:5]) + (f" and {len(frozen) - 5} more" if len(frozen) > 5 else "")
    cited = _CITATION.findall(body or "")
    if not cited:
        return [
            f"changes machinery path(s) {shown} but the body has no "
            f"'Machinery-Twin: {MACHINERY_REPOSITORY}#<PR> <merge commit SHA>' line"
        ]
    problems = [citation_problem(get, int(number), sha) for number, sha in cited]
    return [f"changes machinery path(s) {shown}: {problem}" for problem in problems if problem]


def _paths(*args: str) -> list[str]:
    return [path for path in _git_out(args[0], "-z", *args[1:]).split("\0") if path]


def _tree_paths(commit: str) -> list[str]:
    ensure_commit(commit)
    return _paths("ls-tree", "-r", "--name-only", commit)


def _changed_paths(base: str, head: str) -> list[str]:
    # --no-renames: a moved machinery file counts as its old path deleted.
    return _paths("diff", "--no-renames", "--name-only", base, head)


def _body(get: GetJson, repository: str, number: int) -> str | None:
    """The PR body as GitHub holds it now (None when empty)."""
    pull = get(f"repos/{repository}/pulls/{number}")
    body = pull.get("body", ...) if isinstance(pull, dict) else ...
    if body is not None and not isinstance(body, str):
        raise Retryable(f"#{number} body unreadable")
    return body


def evaluate_queue(payload: object, post: Callable, get: GetJson) -> list[str]:
    event = parse_event(payload)
    tip, entries = read_queue(post, event)
    members = resolve_members(event, squash_chain(event, tip), entries)
    rows = machinery_rows(get)
    merged = _tree_paths(tip)
    result: list[str] = []
    for member in members:
        body = _body(get, event.repository, member.squash.pr)
        changed = _changed_paths(member.squash.parent, member.squash.sha)
        result += [
            f"#{member.squash.pr}: {item}" for item in findings(changed, body, rows=rows, merged_paths=merged, get=get)
        ]
    if expired(merged, rows):
        print(f"machinery twin gate: expired: {event.branch} holds no machinery path outside the residual")
    return result


def evaluate_pull_request(payload: object, get: GetJson) -> list[str]:
    try:
        pull = payload["pull_request"]  # type: ignore[index]
        repository = payload["repository"]["full_name"]  # type: ignore[index]
        number, base, head = pull["number"], pull["base"]["sha"], pull["head"]["sha"]
        if type(number) is not int or not all(isinstance(sha, str) and _SHA.fullmatch(sha) for sha in (base, head)):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise GateError("pull_request event unreadable") from None
    body = _body(get, repository, number)
    ensure_commit(head)
    merge_base = _git_out("merge-base", base, head)
    return findings(
        _changed_paths(merge_base, head), body, rows=machinery_rows(get), merged_paths=_tree_paths(base), get=get
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail a merge-queue candidate when a member PR changes a machinery-classified path without\n"
        f"citing a merged {MACHINERY_REPOSITORY} twin (decision TWIN-FREEZE-1113). Warns only on pull_request.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ci.machinery_twin_gate\n"
            "  GITHUB_EVENT_NAME=pull_request .venv/bin/python -m scripts.ci.machinery_twin_gate --event-file event.json\n"
            "Body line: Machinery-Twin: learn-ukrainian/machinery#<PR> <40-hex merge commit SHA>\n"
            "Inputs: GITHUB_EVENT_NAME (merge_group or pull_request), GITHUB_EVENT_PATH, GITHUB_TOKEN; a checkout\n"
            "with full history and an origin remote.\n"
            "Outputs: ::error:: (merge_group) or ::warning:: (pull_request) annotations; fetches missing commits only.\n"
            "Exit codes: 0 pass, expired, or pull_request; 1 a finding or unverifiable input on merge_group; 2 bad arguments.\n"
            "Related: .github/workflows/ci.yml (CI Gate); scripts/ci/queue_review_gate.py; docs/decisions/decisions.yaml."
        ),
    )
    parser.add_argument("--event-file", help="event JSON; default: $GITHUB_EVENT_PATH")
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS, help="fresh reads after an API error")
    parser.add_argument("--retry-delay", type=float, default=DEFAULT_RETRY_DELAY_SECONDS, help="seconds between reads")
    args = parser.parse_args(argv)
    if args.attempts < 1 or args.retry_delay < 0:
        parser.error("--attempts must be at least 1 and --retry-delay non-negative")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    enforcing = event_name == "merge_group"
    level = "error" if enforcing else "warning"
    event_file = args.event_file or os.environ.get("GITHUB_EVENT_PATH", "")
    for attempt in range(1, args.attempts + 1):
        try:
            if event_name not in ("merge_group", "pull_request"):
                raise GateError(f"unsupported event {event_name!r}")
            if not event_file or not os.environ.get("GITHUB_TOKEN"):
                raise GateError("GITHUB_EVENT_PATH (or --event-file) and GITHUB_TOKEN are required")
            try:
                payload = json.loads(Path(event_file).read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise GateError(f"event file unreadable: {type(error).__name__}") from None
            if enforcing:
                result = evaluate_queue(payload, graphql_post(), rest_get())
            else:
                result = evaluate_pull_request(payload, rest_get())
        except Retryable as error:
            print(f"attempt {attempt}/{args.attempts}: {error}", file=sys.stderr)
            if attempt < args.attempts:
                time.sleep(args.retry_delay)
                continue
            print(f"::{level}::machinery twin gate: unverifiable: {error}")
            return int(enforcing)
        except GateError as error:
            print(f"::{level}::machinery twin gate: unverifiable: {error}")
            return int(enforcing)
        for item in result:
            print(f"::{level}::machinery twin gate: {item}")
        if not result:
            print("machinery twin gate: no unlanded machinery change")
        return int(enforcing and bool(result))
    return int(enforcing)


if __name__ == "__main__":
    sys.exit(main())
