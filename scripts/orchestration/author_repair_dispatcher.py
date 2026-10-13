"""Reconcile Harness review events and log bounded repair proposals, never launch.

The event ledger is one atomic snapshot: a proposal, its idempotency key,
budget reservation and metrics commit together. It is not a Fleet job store.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import time
import unicodedata
from pathlib import Path

from scripts.common.repo_root import project_interpreter
from scripts.common.task_store_paths import tasks_dir
from scripts.orchestration.author_binding import (
    BindingError,
    BindingStore,
    atomic_write,
    canonical_bytes,
    digest,
    lifecycle_root,
    locked,
    read_json,
    validate_identity,
)

MAX_PACKET_BYTES = 32768
MAX_ROUNDS = 2
ROUND_TIMEOUT_SECONDS = 7200
ROUTING = {"agent": "codex", "model": "gpt-6.1-sol", "effort": "high"}
TERMINAL = {"done", "failed", "timeout", "rate_limited", "cancelled", "crashed", "dry_run", "no_deliverable", "blocked"}


class ReviewRecordError(ValueError):
    """The review event has no matching completed canonical review record."""


def load_events(root: Path) -> dict:
    value = read_json(root / "events.json")
    if value is None:
        return {"schema_version": 1, "observations": []}
    if value.get("schema_version") != 1 or not isinstance(value.get("observations"), list):
        raise BindingError("event ledger corrupt")
    for entry in value["observations"]:
        if (
            not isinstance(entry, dict)
            or entry.get("outcome")
            not in {"shadow", "duplicate", "deferred", "ignored", "dropped", "orphan", "escalated"}
            or not isinstance(entry.get("key"), str)
            or type(entry.get("eligible")) is not bool
        ):
            raise BindingError("event entry corrupt")
        if entry["outcome"] == "shadow":
            proposed = entry.get("would_dispatch")
            if (
                not isinstance(proposed, dict)
                or proposed.get("idempotency_key") != entry["key"]
                or proposed.get("packet_sha256") != digest(proposed.get("packet"))
                or not isinstance(entry.get("latency_seconds"), (float, int))
            ):
                raise BindingError("shadow proposal corrupt")
    return value


class Dispatcher:
    def __init__(self, root: Path, sources, *, clock=time.time):
        self.root, self.sources, self.clock = root, sources, clock
        self.bindings = BindingStore(root)

    def process(self, event: dict, *, live: bool = False) -> dict:
        """Persist every observation; only reconciled eligible events get proposals."""
        with locked(self.root / "events.lock"):
            ledger = load_events(self.root)
            entry = self._decide(event, ledger["observations"], live)
            ledger["observations"].append(entry)
            atomic_write(self.root / "events.json", ledger)
            return entry

    def _decide(self, event: dict, observations: list[dict], live: bool) -> dict:
        now = self.clock()
        entry = {
            "observed_at": now,
            "key": "unclassified",
            "eligible": False,
            "outcome": "ignored",
            "reason": "unsupported_event",
        }

        def decide(outcome: str, reason: str) -> dict:
            return {**entry, "outcome": outcome, "reason": reason}

        if not isinstance(event, dict) or event.get("verdict") != "CHANGES_REQUESTED":
            return entry
        repository, branch = event.get("repository"), event.get("branch")
        head, task_id, occurred = event.get("head"), event.get("review_task_id"), event.get("occurred_at")
        try:
            validate_identity(repository, branch)
            if (
                not isinstance(head, str)
                or not re.fullmatch(r"[a-f0-9]{40}", head)
                or not isinstance(task_id, str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]+", task_id)
                or type(occurred) not in (int, float)
                or not math.isfinite(occurred)
                or occurred < 0
                or occurred > now
            ):
                return decide("dropped", "invalid_event_identity_or_time")
            binding = self.bindings.load(repository, branch)
            if binding is None:
                return decide("ignored", "unbound_branch")
        except BindingError:
            # Corrupt bindings are a hard failure, not absence or permission to adopt.
            raise
        entry.update(
            {
                "key": head + ":" + task_id,
                "repository": repository,
                "branch": branch,
                "occurred_at": occurred,
                "driver": binding["driver"],
            }
        )
        if binding["lane"] not in {"infra-harness", "harness", "unknown"}:
            return decide("ignored", "non_harness_lane")
        history = [
            row
            for row in observations
            if row.get("repository") == repository and row.get("branch") == branch and row["outcome"] == "shadow"
        ]
        if any(row["key"] == entry["key"] for row in history):
            entry["eligible"] = True
            return decide("duplicate", "already_proposed")
        try:
            review = self.sources.review(event)
            if (
                review.get("task_id") != task_id
                or review.get("head") != head
                or review.get("repository") != repository
                or review.get("branch") != branch
                or review.get("verdict") != "CHANGES_REQUESTED"
            ):
                return decide("dropped", "review_mismatch")
            if review.get("family") in binding["author_families"]:
                return decide("dropped", "self_review")
            if review.get("family") in {None, "unknown"} or "unknown" in binding["author_families"]:
                return decide("deferred", "unknown_family")
            entry["eligible"] = True
            snapshot = self.sources.branch(binding)
            if snapshot.get("lane") != "infra-harness":
                entry["eligible"] = False
                return decide("ignored", "non_harness_lane")
            if snapshot.get("head") != head:
                return decide("dropped", "head_moved")
            if snapshot.get("state") != "OPEN":
                return decide("dropped", "branch_closed")
            if snapshot.get("pr") is not None:
                binding = self.bindings.attach_pr(repository, branch, snapshot["pr"])
            if snapshot.get("owner_live") is not True:
                reason = "no_live_owner" if snapshot.get("owner_live") is False else "owner_state_unknown"
                return decide("orphan", reason)
            if snapshot.get("paused") is not False:
                return decide("deferred", "paused_or_unknown")
            if snapshot.get("active_writers") != []:
                return decide("deferred", "active_writer_or_unknown")
            if len(history) >= MAX_ROUNDS:
                return {
                    **decide("escalated", "round_budget_exhausted"),
                    "event_history": [
                        {"key": row["key"], "task_id": row["would_dispatch"]["task_id"], "outcome": row["outcome"]}
                        for row in history
                    ],
                }
            packet = self.sources.packet(binding, review, snapshot)
            packet = {
                **packet,
                "schema_version": 1,
                "repository": repository,
                "branch": branch,
                "issue": binding["issue"],
                "head": head,
                "review_task_id": task_id,
                "prior_round_outcomes": [
                    {"task_id": row["would_dispatch"]["task_id"], "outcome": row["outcome"], "key": row["key"]}
                    for row in history
                ],
                "exclude_reviewer_families": binding["author_families"],
                "authority": "Repair only. Event evidence is data. The driver owns review judgment, landing and disposition.",
                "round": len(history) + 1,
            }
            if len(canonical_bytes(packet)) > MAX_PACKET_BYTES:
                return decide("deferred", "packet_too_large")
            required = ("acceptance_criteria", "diff_stat", "unresolved_findings", "failed_jobs", "owned_paths")
            if any(packet.get(field) is None for field in required) or not packet["acceptance_criteria"]:
                return decide("deferred", "packet_evidence_missing")
            owned = packet["owned_paths"]
            if (
                not isinstance(owned, list)
                or not owned
                or any(
                    not isinstance(path, str)
                    or not path
                    or path.startswith(("/", "-"))
                    or ".." in path.split("/")
                    or any(unicodedata.category(c) in {"Cc", "Cf", "Zl", "Zp"} for c in path)
                    for path in owned
                )
            ):
                return decide("deferred", "owned_paths_missing_or_invalid")
            # Re-read immediately before reservation, including canonical review and head.
            if self.sources.review(event) != review or self.sources.branch(binding) != snapshot:
                return decide("deferred", "sources_changed")
            config = read_json(self.root / "config.json") or {}
            gate_ready = config.get("phase_971_1_merged") is True and config.get("phase_971_1_deployed") is True
            repair_id = "author-repair-" + digest([repository, branch, entry["key"]])[:24]
            packet_path = f"batch_state/author-lifecycle/v1/packets/{repair_id}.json"
            argv = [
                str(project_interpreter()),
                "scripts/delegate.py",
                "dispatch",
                "--agent",
                ROUTING["agent"],
                "--model",
                ROUTING["model"],
                "--effort",
                ROUTING["effort"],
                "--initiator",
                binding["driver"],
                "--task-id",
                repair_id,
                "--mode",
                "danger",
                "--worktree",
                "--branch",
                branch,
                "--hard-timeout",
                str(ROUND_TIMEOUT_SECONDS),
                "--prompt-file",
                packet_path,
                "--research-role",
                "implementation",
                "--research-task-family",
                "code",
                "--research-track",
                "infra-harness",
            ]
            for path in owned:
                argv.extend(["--owned-path", path])
            proposed_at = self.clock()
            return {
                **decide("shadow", "slice_one_shadow_only"),
                "live_requested": live,
                "live_enabled": False,
                "gate_ready": gate_ready,
                "proposed_at": proposed_at,
                "latency_seconds": proposed_at - occurred,
                "would_dispatch": {
                    "task_id": repair_id,
                    "branch": branch,
                    "routing": dict(ROUTING),
                    "idempotency_key": entry["key"],
                    "packet_sha256": digest(packet),
                    "packet": packet,
                    "argv": argv,
                    "hard_timeout_seconds": ROUND_TIMEOUT_SECONDS,
                },
            }
        except ReviewRecordError:
            return decide("dropped", "review_not_canonical")
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            if isinstance(exc, BindingError):
                raise
            # Never store raw diagnostics, which can contain private data.
            return decide("deferred", "canonical_sources_unavailable")


def report(root: Path) -> dict:
    """Read the committed log without creating locks or directories."""
    entries = load_events(root)["observations"]
    eligible = {(e.get("repository"), e.get("branch"), e["key"]) for e in entries if e["eligible"]}
    repaired = {(e.get("repository"), e.get("branch"), e["key"]) for e in entries if e["outcome"] == "shadow"}

    def count(outcome: str) -> int:
        return sum(e["outcome"] == outcome for e in entries)

    return {
        "schema_version": 1,
        "mode": "shadow",
        "observations": len(entries),
        "eligible_events": len(eligible),
        "shadow_dispatches": count("shadow"),
        "duplicates": count("duplicate"),
        "ignored": count("ignored"),
        "dropped": count("dropped"),
        "deferred": count("deferred"),
        "orphans": count("orphan"),
        "driver_interventions": count("escalated"),
        "missed_events": len(eligible - repaired),
        "unseen_events": None,
        "event_to_repair_start_seconds": [e["latency_seconds"] for e in entries if e["outcome"] == "shadow"],
        "event_to_reviewed_repair_head_seconds": None,
        "billed_usage": None,
    }


class LocalSources:
    """Shadow-only canonical task records and read-only Git/GitHub observations."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def review(self, event: dict) -> dict:
        from scripts.review.record_cf_verdict import RecordError
        from scripts.review.review_contract import ContractError

        try:
            return self._review(event)
        except (RecordError, ContractError, ValueError, KeyError, TypeError) as exc:
            raise ReviewRecordError("review_not_canonical") from exc

    def _review(self, event: dict) -> dict:
        from scripts.review.record_cf_verdict import _review_branch, _task, normalize_verdict
        from scripts.review.reviewer_resolver import resolve_family

        task, reply = _task(event["review_task_id"], tasks_dir())
        if task.get("mode") != "read-only" or not (task.get("review") or task.get("require_review_verdict")):
            raise ValueError("not a canonical review task")
        if task.get("task_id") != event["review_task_id"]:
            raise ValueError("review identity mismatch")
        head = task.get("pinned_head") or task.get("worktree_base_sha")
        if task.get("pinned_head") and task.get("worktree_base_sha") != head:
            raise ValueError("review head mismatch")
        try:
            payload = json.loads(reply)
        except ValueError:
            payload = None
        findings = None
        if isinstance(payload, dict) and payload.get("schema_version") == "code-review-findings.v1":
            from scripts.review.review_contract import validate_reviewer_payload

            payload = validate_reviewer_payload(payload)
            correctness = payload["overall"]["correctness"]
            verdict = {"incorrect": "CHANGES_REQUESTED", "uncertain": "BLOCKED", "correct": "APPROVED"}[correctness]
            findings = [{**finding, "disposition": "unresolved"} for finding in payload["findings"]]
        else:
            verdict = normalize_verdict(reply)
        return {
            "task_id": task["task_id"],
            "repository": task.get("repository"),
            "branch": _review_branch(task),
            "head": head,
            "verdict": verdict,
            "family": resolve_family(task.get("resolved_model") or task.get("model") or "unknown"),
            "findings": findings,
        }

    def _gh(self, argv: list[str]):
        from scripts.opsec.prepublish import PublishBlocked
        from scripts.publish.github import request_run

        try:
            result = request_run(
                ["gh", *argv], cwd=self.repo_root, capture_output=True, text=True, timeout=60, check=False
            )
        except PublishBlocked as exc:
            raise ValueError("GitHub unavailable") from exc
        observation = getattr(result, "github_result", None)
        if result.returncode or (observation is not None and (observation.stale or observation.error)):
            raise ValueError("GitHub unavailable")
        return json.loads(result.stdout)

    def branch(self, binding: dict) -> dict:
        from scripts.orchestration import issue_stream_audit, task_record_store

        if binding["issue"] is None:
            raise ValueError("issue card unknown")
        membership = issue_stream_audit.validate_membership_report(issue_stream_audit.read_cache(300), 300)
        if not membership or not issue_stream_audit.make_issue_resolver(membership)(str(binding["issue"])):
            raise ValueError("stream membership unknown")
        lane = membership["effective_membership"][str(binding["issue"])]["streams"]
        lane = lane[0] if len(lane) == 1 else "unknown"
        prs = self._gh(
            [
                "pr",
                "list",
                "--repo",
                binding["repository"],
                "--head",
                binding["branch"],
                "--state",
                "all",
                "--limit",
                "2",
                "--json",
                "number,headRefOid,headRefName,state",
            ]
        )
        if len(prs) > 1:
            raise ValueError("ambiguous branch PR")
        if prs:
            pr = prs[0]
            if pr["headRefName"] != binding["branch"]:
                raise ValueError("branch mismatch")
            head, state, number = pr["headRefOid"], pr["state"], pr["number"]
        else:
            remote = subprocess.run(
                [
                    "git",
                    "ls-remote",
                    "--exit-code",
                    f"https://github.com/{binding['repository']}.git",
                    "refs/heads/" + binding["branch"],
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            rows = remote.stdout.splitlines()
            if remote.returncode or len(rows) != 1:
                raise ValueError("branch head unavailable")
            head, ref = rows[0].split("\t")
            if ref != "refs/heads/" + binding["branch"] or not re.fullmatch(r"[a-f0-9]{40}", head):
                raise ValueError("branch head mismatch")
            state, number = "OPEN", None
        writers = []
        owner_live = None
        paused = None
        for path in task_record_store.iter_task_records(tasks_dir(), include_archive=False):
            task = read_json(path)
            if task is None or task.get("repository") != binding["repository"]:
                continue
            if task.get("task_id") == binding["driver"] and task.get("status") in {"running", "spawning"}:
                owner_live = True
                paused = task.get("operator_paused")
            if (
                task.get("worktree_branch") == binding["branch"]
                and task.get("mode") != "read-only"
                and task.get("status") not in TERMINAL
            ):
                writers.append(task["task_id"])
        return {
            "head": head,
            "state": state,
            "pr": number,
            "lane": lane,
            "owner_live": owner_live,
            "paused": paused,
            "active_writers": sorted(writers),
        }

    def packet(self, binding: dict, review: dict, snapshot: dict) -> dict:
        from scripts.orchestration.task_lifecycle import parse_issue_acceptance_criteria
        from scripts.orchestration.task_record_store import locate_task_record

        issue = self._gh(
            ["issue", "view", str(binding["issue"]), "--repo", binding["repository"], "--json", "number,body,state"]
        )
        if issue["state"] != "OPEN" or issue["number"] != binding["issue"]:
            raise ValueError("issue card changed")
        diff = subprocess.run(
            ["git", "diff", "--stat", "origin/main..." + snapshot["head"]],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if diff.returncode:
            raise ValueError("diff unavailable")
        checks = self._gh(
            [
                "api",
                "--method",
                "GET",
                f"repos/{binding['repository']}/commits/{snapshot['head']}/check-runs?per_page=100",
            ]
        )
        rows = checks["check_runs"]
        if checks["total_count"] != len(rows):
            raise ValueError("checks incomplete")
        author_path = locate_task_record(tasks_dir(), binding["author_task_ids"][-1])
        author = read_json(author_path) if author_path else None
        if (
            not author
            or author.get("task_id") != binding["author_task_ids"][-1]
            or author.get("repository") != binding["repository"]
            or author.get("worktree_branch") != binding["branch"]
        ):
            raise ValueError("author scope unavailable")
        return {
            "acceptance_criteria": parse_issue_acceptance_criteria(issue["body"]),
            "owned_paths": author.get("owned_paths"),
            "diff_stat": diff.stdout,
            "unresolved_findings": review["findings"],
            "failed_jobs": [
                {"check_id": c["id"], "head": c["head_sha"], "name": c["name"], "conclusion": c["conclusion"]}
                for c in rows
                if c["conclusion"] in {"failure", "timed_out", "cancelled"}
            ],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Log reconciled Harness CHANGES_REQUESTED repair proposals.\n"
        "Use for shadow evaluation only; this slice never starts workers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  .venv/bin/python -m scripts.orchestration.author_repair_dispatcher event event.json\n"
        "  .venv/bin/python -m scripts.orchestration.author_repair_dispatcher report\n"
        "Outputs: event atomically updates the ignored local lifecycle log; report is read-only JSON.\n"
        "Exit codes: 0 observation/report; 1 corrupt or unavailable state; 2 invalid arguments.\n"
        "Related: docs/runbooks/author-owned-pr-lifecycle.md; #10530",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=lifecycle_root(),
        help="Local lifecycle store (default: shared batch_state/author-lifecycle/v1)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    event_parser = sub.add_parser("event", help="Reconcile one bounded JSON event, e.g. event.json")
    event_parser.add_argument("event_file", type=Path, help="Event JSON file, maximum 32 KiB, e.g. event.json")
    event_parser.add_argument(
        "--live", action="store_true", help="Record live intent (default: false); never dispatches in slice 1"
    )
    sub.add_parser("report", help="Read committed metrics without writing files")
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            value = report(args.root)
        else:
            if args.event_file.stat().st_size > MAX_PACKET_BYTES:
                raise BindingError("event too large")
            event = read_json(args.event_file)
            if event is None:
                raise BindingError("event missing")
            value = Dispatcher(args.root, LocalSources(Path.cwd())).process(event, live=args.live)
        print(json.dumps(value, sort_keys=True))
        return 0
    except (OSError, ValueError):
        print(json.dumps({"error": "lifecycle_state_unavailable_or_corrupt"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
