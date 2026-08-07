#!/usr/bin/env python3
"""Fail-closed scope gate for new Hramatka driver work.

The gate is intentionally wired to Hramatka only, while its decision function
accepts a configuration and stream registry so a later, separately approved
rollout can reuse the shape without copying policy. It never reads an
environment-variable bypass and never mutates GitHub.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from scripts.orchestration import issue_stream_audit

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
PRIVATE_REPOSITORY = "learn-ukrainian/learn-ukrainian-infra-private"
HRAMATKA_STREAM = "hramatka"
HRAMATKA_EPIC = 4542
HRAMATKA_PRIVATE_BOARD = 349
GH_TIMEOUT_SECONDS = 15.0

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_BODY_STREAM_TAG_RE = re.compile(r"(?im)^\s*(?:<!--\s*)?stream\s*[:=]\s*([a-z0-9][a-z0-9-]*)\s*(?:-->)?\s*$")

GATED_ACTIONS = frozenset({"new_dispatch", "new_scope", "new_pr"})
EXEMPT_ACTIONS = frozenset({"cleanup", "review", "escalate", "unblock_own_open_pr"})
ALL_ACTIONS = GATED_ACTIONS | EXEMPT_ACTIONS


class Outcome(StrEnum):
    """The only operational dispositions this gate can emit."""

    ALLOW = "ALLOW"
    ROUTE = "ROUTE"
    HOLD = "HOLD"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class IssueRef:
    """A repo-qualified GitHub issue identifier."""

    repository: str
    number: int

    def __post_init__(self) -> None:
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise ValueError("repository must be a qualified owner/name identifier")
        if not isinstance(self.number, int) or isinstance(self.number, bool) or self.number <= 0:
            raise ValueError("issue number must be a positive integer")

    def display(self) -> str:
        return f"{self.repository}#{self.number}"


@dataclass(frozen=True)
class ScopeGateConfig:
    """Hramatka-specific policy inputs, kept explicit for later reuse."""

    stream_name: str
    public_repository: str
    public_epic: int
    private_repository: str
    private_board: IssueRef
    operator_only_issues: frozenset[IssueRef]


HRAMATKA_SCOPE_GATE = ScopeGateConfig(
    stream_name=HRAMATKA_STREAM,
    public_repository=PUBLIC_REPOSITORY,
    public_epic=HRAMATKA_EPIC,
    private_repository=PRIVATE_REPOSITORY,
    private_board=IssueRef(PRIVATE_REPOSITORY, HRAMATKA_PRIVATE_BOARD),
    operator_only_issues=frozenset(
        {
            IssueRef(PRIVATE_REPOSITORY, 360),
            IssueRef(PRIVATE_REPOSITORY, 212),
        }
    ),
)


@dataclass(frozen=True)
class IssueObservation:
    """The minimal, non-title GitHub state needed for a scope decision."""

    labels: frozenset[str]
    body: str
    parent_number: int | None


@dataclass(frozen=True)
class GateDecision:
    """A machine-readable, non-mutating scope-gate result."""

    outcome: Outcome
    reason: str
    destination: str | None = None

    def as_json(self) -> dict[str, str]:
        payload = {"outcome": self.outcome.value, "reason": self.reason}
        if self.destination is not None:
            payload["destination"] = self.destination
        return payload


class IssueLookupUnavailable(RuntimeError):
    """GitHub did not return a trusted issue observation."""


IssueReader = Callable[[IssueRef], IssueObservation]


def load_stream_registry(repo_root: Path = REPO_ROOT) -> dict[str, list[int]]:
    """Read the canonical stream-to-epic registry without making a network call."""

    return issue_stream_audit.load_registry(repo_root / "scripts" / "config" / "issue_streams.yaml")


def _gh_issue_observation(issue: IssueRef) -> IssueObservation:
    """Read one repo-qualified issue through GitHub GraphQL.

    GitHub failures are deliberately normalized to ``IssueLookupUnavailable``:
    callers must not accidentally distinguish a private API outage from a
    trusted observation and allow fresh work.
    """

    owner, name = issue.repository.split("/", 1)
    query = (
        "query($owner:String!,$name:String!,$number:Int!){"
        "repository(owner:$owner,name:$name){issue(number:$number){"
        "number body labels(first:100){nodes{name}} parent{number}"
        "}}}"
    )
    try:
        proc = subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-F",
                f"owner={owner}",
                "-F",
                f"name={name}",
                "-F",
                f"number={issue.number}",
                "-f",
                f"query={query}",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
            text=True,
            timeout=GH_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IssueLookupUnavailable("GitHub issue authority is unavailable") from exc
    if proc.returncode != 0:
        raise IssueLookupUnavailable("GitHub issue authority is unavailable")

    try:
        payload = json.loads(proc.stdout)
        node = payload["data"]["repository"]["issue"]
        if not isinstance(node, Mapping) or node.get("number") != issue.number:
            raise ValueError("issue response does not identify the requested issue")
        body = node.get("body")
        labels_doc = node.get("labels")
        parent_doc = node.get("parent")
        label_nodes = labels_doc.get("nodes") if isinstance(labels_doc, Mapping) else None
        if not isinstance(body, str) or not isinstance(label_nodes, list):
            raise ValueError("issue response has an invalid shape")
        labels = frozenset(
            label["name"] for label in label_nodes if isinstance(label, Mapping) and isinstance(label.get("name"), str)
        )
        if len(labels) != len(label_nodes):
            raise ValueError("issue response contains an invalid label")
        parent_number = parent_doc.get("number") if isinstance(parent_doc, Mapping) else None
        if parent_number is not None and (
            not isinstance(parent_number, int) or isinstance(parent_number, bool) or parent_number <= 0
        ):
            raise ValueError("issue response contains an invalid parent")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise IssueLookupUnavailable("GitHub issue authority is unavailable") from exc
    return IssueObservation(labels=labels, body=body, parent_number=parent_number)


def _stream_destinations(stream_registry: Mapping[str, Sequence[int]]) -> dict[str, int]:
    """Map each stream to one canonical epic for named routing messages."""

    destinations: dict[str, int] = {}
    for stream, epics in stream_registry.items():
        if not isinstance(stream, str) or not stream:
            raise ValueError("stream registry contains an invalid stream name")
        if not isinstance(epics, Sequence) or isinstance(epics, (str, bytes)):
            raise ValueError("stream registry contains invalid epics")
        numbers = [epic for epic in epics if isinstance(epic, int) and not isinstance(epic, bool) and epic > 0]
        if len(numbers) != len(epics) or not numbers:
            raise ValueError("stream registry contains invalid epics")
        destinations[stream] = min(numbers)
    return destinations


def _epic_to_stream(stream_registry: Mapping[str, Sequence[int]]) -> dict[int, str]:
    """Map every configured epic to exactly one stream."""

    epics: dict[int, str] = {}
    for stream, numbers in stream_registry.items():
        for number in numbers:
            previous = epics.setdefault(number, stream)
            if previous != stream:
                raise ValueError(f"epic #{number} belongs to more than one stream")
    return epics


def _destination_for_stream(stream: str, destinations: Mapping[str, int]) -> str:
    return f"{stream} epic #{destinations[stream]}"


def _stream_from_private_tags(
    issue: IssueRef,
    observation: IssueObservation,
    *,
    config: ScopeGateConfig,
    destinations: Mapping[str, int],
) -> set[str]:
    """Read explicit private stream tags only; prose mentions never count."""

    streams: set[str] = set()
    if issue == config.private_board or observation.parent_number == config.private_board.number:
        streams.add(config.stream_name)

    for raw_label in observation.labels:
        label = raw_label.casefold().strip()
        if label == config.stream_name:
            streams.add(config.stream_name)
            continue
        for prefix in ("stream:", "stream/"):
            if label.startswith(prefix):
                candidate = label.removeprefix(prefix)
                if candidate in destinations:
                    streams.add(candidate)
                break

    for match in _BODY_STREAM_TAG_RE.finditer(observation.body):
        candidate = match.group(1).casefold()
        if candidate in destinations:
            streams.add(candidate)
    return streams


def _route_unassigned_private(config: ScopeGateConfig) -> GateDecision:
    return GateDecision(
        outcome=Outcome.ROUTE,
        reason="private issue has no exact Hramatka label, board tracking, or stream tag",
        destination=f"private Hramatka board #{config.private_board.number} triage",
    )


def _gate_public_issue(
    issue: IssueRef,
    observation: IssueObservation,
    *,
    config: ScopeGateConfig,
    destinations: Mapping[str, int],
    epic_streams: Mapping[int, str],
) -> GateDecision:
    # Only exact membership is evidence. A title/body/label mention of Hramatka
    # cannot override native stream ownership or become a percentage heuristic.
    membership_epic = observation.parent_number or issue.number
    stream = epic_streams.get(membership_epic)
    if stream == config.stream_name:
        return GateDecision(
            outcome=Outcome.ALLOW,
            reason=f"public issue is linked to {config.stream_name} epic #{config.public_epic}",
        )
    if stream is not None:
        return GateDecision(
            outcome=Outcome.ROUTE,
            reason=f"public issue belongs to {stream} through epic #{membership_epic}",
            destination=_destination_for_stream(stream, destinations),
        )
    return GateDecision(
        outcome=Outcome.ROUTE,
        reason="public issue has no exact stream membership",
        destination="stream triage (link the issue to exactly one stream epic)",
    )


def _gate_private_issue(
    issue: IssueRef,
    observation: IssueObservation,
    *,
    config: ScopeGateConfig,
    destinations: Mapping[str, int],
) -> GateDecision:
    streams = _stream_from_private_tags(issue, observation, config=config, destinations=destinations)
    if len(streams) > 1:
        return GateDecision(
            outcome=Outcome.HOLD,
            reason="private issue has conflicting explicit stream membership",
        )
    if streams == {config.stream_name}:
        return GateDecision(
            outcome=Outcome.ALLOW,
            reason="private issue is explicitly tracked by the Hramatka board, label, or stream tag",
        )
    if streams:
        stream = next(iter(streams))
        return GateDecision(
            outcome=Outcome.ROUTE,
            reason=f"private issue is explicitly tagged for {stream}",
            destination=_destination_for_stream(stream, destinations),
        )
    return _route_unassigned_private(config)


def evaluate_scope(
    *,
    action: str,
    issue: IssueRef,
    observation: IssueObservation | None,
    stream_registry: Mapping[str, Sequence[int]],
    config: ScopeGateConfig = HRAMATKA_SCOPE_GATE,
) -> GateDecision:
    """Classify one already-observed issue without a network call.

    ``observation=None`` represents an unavailable authority, not a negative
    lookup. New work therefore holds rather than slipping through as ALLOW.
    """

    if action not in ALL_ACTIONS:
        raise ValueError(f"unsupported action: {action}")
    if issue.repository not in {config.public_repository, config.private_repository}:
        raise ValueError("issue repository is not configured for the Hramatka scope gate")
    if action in EXEMPT_ACTIONS:
        return GateDecision(
            outcome=Outcome.ALLOW,
            reason=f"{action} does not create new Hramatka scope",
        )
    if issue in config.operator_only_issues:
        return GateDecision(
            outcome=Outcome.ESCALATE,
            reason=f"{issue.display()} is operator-only host mutation work and needs verified operator GO",
        )
    if issue.repository == config.public_repository and issue.number == config.public_epic:
        return GateDecision(
            outcome=Outcome.ALLOW,
            reason=f"public issue is the configured Hramatka epic #{config.public_epic}",
        )
    if observation is None:
        repository_kind = "private" if issue.repository == config.private_repository else "public"
        return GateDecision(
            outcome=Outcome.HOLD,
            reason=f"{repository_kind} issue authority is UNKNOWN; new Hramatka work is fail-closed",
        )

    destinations = _stream_destinations(stream_registry)
    if config.stream_name not in destinations or config.public_epic not in stream_registry[config.stream_name]:
        raise ValueError("stream registry does not match the configured Hramatka epic")
    if issue.repository == config.public_repository:
        return _gate_public_issue(
            issue,
            observation,
            config=config,
            destinations=destinations,
            epic_streams=_epic_to_stream(stream_registry),
        )
    return _gate_private_issue(issue, observation, config=config, destinations=destinations)


def decide_scope(
    *,
    action: str,
    issue: IssueRef,
    stream_registry: Mapping[str, Sequence[int]],
    reader: IssueReader = _gh_issue_observation,
    config: ScopeGateConfig = HRAMATKA_SCOPE_GATE,
) -> GateDecision:
    """Read authority only when the action needs a new-scope decision."""

    if action not in ALL_ACTIONS:
        raise ValueError(f"unsupported action: {action}")
    if issue.repository not in {config.public_repository, config.private_repository}:
        raise ValueError("issue repository is not configured for the Hramatka scope gate")
    if action in EXEMPT_ACTIONS or issue in config.operator_only_issues:
        return evaluate_scope(
            action=action,
            issue=issue,
            observation=None,
            stream_registry=stream_registry,
            config=config,
        )
    if issue.repository == config.public_repository and issue.number == config.public_epic:
        return evaluate_scope(
            action=action,
            issue=issue,
            observation=None,
            stream_registry=stream_registry,
            config=config,
        )
    try:
        observation = reader(issue)
    except IssueLookupUnavailable:
        observation = None
    return evaluate_scope(
        action=action,
        issue=issue,
        observation=observation,
        stream_registry=stream_registry,
        config=config,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=sorted(ALL_ACTIONS))
    parser.add_argument("--issue-repo", required=True, help="Qualified owner/name repository")
    parser.add_argument("--issue", required=True, type=int, help="Positive issue number in --issue-repo")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    reader: IssueReader = _gh_issue_observation,
    stream_registry: Mapping[str, Sequence[int]] | None = None,
    config: ScopeGateConfig = HRAMATKA_SCOPE_GATE,
) -> int:
    """Run the CLI, returning 0 only for a permitted new-scope decision."""

    args = _parser().parse_args(argv)
    try:
        issue = IssueRef(args.issue_repo, args.issue)
        registry = stream_registry if stream_registry is not None else load_stream_registry()
        decision = decide_scope(
            action=args.action,
            issue=issue,
            stream_registry=registry,
            reader=reader,
            config=config,
        )
    except (OSError, ValueError) as exc:
        _parser().error(str(exc))
        return 2  # pragma: no cover - argparse always raises SystemExit
    print(json.dumps(decision.as_json(), ensure_ascii=False, sort_keys=True))
    return 0 if decision.outcome is Outcome.ALLOW else 1


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
