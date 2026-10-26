"""Read-only, public-repository flow evidence. No transition or cleanup authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

from scripts.ci.check_issue_task_quality import MAX_AGE_S
from scripts.common import github_client
from scripts.orchestration import dead_worker_state, postmerge_criteria, task_lifecycle
from scripts.orchestration.execution_safe_git import primary_repository, run_git
from scripts.orchestration.integration_sweep import MARKER_PREFIX, REQUIRED_CHECKS, lookup_verdict, parse_marker
from scripts.orchestration.issue_stream_audit import load_registry, read_membership_index
from scripts.orchestration.reaper_lifecycle import journal_path
from scripts.orchestration.task_record_store import iter_task_records
from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES
from scripts.publish.github import GQL_READS, REST_READS
from scripts.secret_redactor import redact_text
from scripts.work.sources_public import public_repository_id

REPOSITORY = public_repository_id()
LIMIT = 50
SCAN_LIMIT = 10000
BYTE_LIMIT = 1024 * 1024
OUTPUT_LIMIT = 128 * 1024
SHA = re.compile(r"[0-9a-f]{40}")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


def timestamp(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.astimezone(UTC) if result.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def token(value):
    """Untrusted labels never become arbitrary output text."""
    return value if isinstance(value, str) and TOKEN.fullmatch(value) and redact_text(value) == value else "unknown"


def opaque(value):
    return "resource-" + hashlib.sha256(str(value).encode()).hexdigest()[:24]


def branch_label(value):
    if (
        isinstance(value, str)
        and not value.startswith(("/", "-"))
        and all(part not in {"", ".", ".."} for part in value.split("/"))
        and not any(ord(char) < 32 for char in value)
        and redact_text(value) == value
    ):
        return value
    return opaque(value)


def locator(path, root):
    try:
        relative = Path(path).resolve().relative_to(root.resolve()).as_posix()
        if not any(ord(c) < 32 for c in relative) and redact_text(relative) == relative:
            return relative
    except (OSError, ValueError, RuntimeError):
        pass
    return opaque(path)


class SourceUnavailable(Exception):
    """Only fixed reason codes, never transport errors or remote bodies, escape."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def local_read(route):
    """Only this fixed loopback API is reachable; redirects and proxies are off."""
    try:
        opener = build_opener(ProxyHandler({}), NoRedirect())
        with opener.open("http://localhost:8765" + route, timeout=5) as response:
            raw = response.read(BYTE_LIMIT + 1)
        if len(raw) > BYTE_LIMIT:
            raise ValueError
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except Exception:
        raise SourceUnavailable("local_source_unavailable") from None


class Reader:
    """Adapt supported readers with memory-only GitHub caching and fixed identity."""

    def __init__(self, root):
        self.root = root
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["GH_HOST"] = "github.com"
        self.github = github_client.GitHubClient(env=env, cwd=root, max_response_bytes=BYTE_LIMIT)
        # The existing client's supported in-memory fallback avoids cache/telemetry writes.
        self.github.cache_dir = None
        self.deadline = time.monotonic() + 60

    def budget(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise SourceUnavailable("read_budget_exhausted")
        return min(10, remaining)

    def request(self, method, endpoint, **kwargs):
        try:
            return self.github.request(method, endpoint, timeout=self.budget(), fresh=True, **kwargs)
        except (OSError, ValueError, subprocess.SubprocessError):
            raise SourceUnavailable("github_transport_unavailable") from None

    def get(self, operation, **fields):
        template, schema = REST_READS[operation]
        if set(fields) != set(schema):
            raise SourceUnavailable("invalid_read")
        endpoint = template.format(repo=REPOSITORY, **fields)
        result = self.request("GET", endpoint)
        if result.error:
            raise SourceUnavailable("github_source_unavailable")
        return result.value

    def listing(self, operation, **fields):
        template, _ = REST_READS[operation]
        base = template.format(repo=REPOSITORY, **fields)
        rows = []
        for page in range(1, 11):
            endpoint = base + ("&" if "?" in base else "?") + f"per_page=100&page={page}"
            result = self.request("GET", endpoint)
            if result.error or not isinstance(result.value, list):
                raise SourceUnavailable("github_list_incomplete")
            rows.extend(result.value)
            if len(result.value) < 100:
                return rows
        raise SourceUnavailable("github_list_incomplete")

    def queue(self, number, branch):
        owner, name = REPOSITORY.split("/")
        result = self.request(
            "POST",
            "graphql",
            payload={
                "query": GQL_READS["queue-status"],
                "variables": {"owner": owner, "name": name, "number": number, "branch": branch},
            },
        )
        try:
            if result.error or result.value.get("errors"):
                raise ValueError
            return result.value["data"]["repository"]["pullRequest"]
        except (KeyError, TypeError, ValueError):
            raise SourceUnavailable("queue_unknown") from None

    def git(self, *args, cwd=None):
        try:
            result = run_git(
                list(args),
                cwd=cwd or self.root,
                profile="remote" if args[0] == "ls-remote" else "local",
                capture_output=True,
                text=True,
                timeout=self.budget(),
                check=False,
            )
            if result.returncode or len(result.stdout) > BYTE_LIMIT:
                raise ValueError
            return result.stdout
        except (OSError, ValueError, subprocess.SubprocessError):
            raise SourceUnavailable("git_source_unavailable") from None


def task_links(task):
    """Use the same DoR association contract as the delegate/Work projection."""
    carrier = task.get("task_lifecycle") or {}
    identity = carrier.get("identity") or {}
    if identity.get("repository") == REPOSITORY:
        try:
            if task_lifecycle.lifecycle_id(identity) == carrier.get("lifecycle_id"):
                return {identity["github_issue_number"]}
        except (ValueError, KeyError, TypeError):
            pass
    preflight = task.get("dor_preflight") or {}
    counts = {}
    for number in preflight.get("issues") or []:
        if type(number) is int and number > 0:
            counts[number] = counts.get(number, 0) + 1
    for foreign in preflight.get("issue_repositories") or []:
        if isinstance(foreign, dict) and foreign.get("repo", foreign.get("repository")) != REPOSITORY:
            number = foreign.get("issue")
            if type(number) is int:
                counts[number] = counts.get(number, 0) - 1
    return {number for number, count in counts.items() if count > 0}


def read_tasks(root):
    directory = root / "batch_state/tasks"
    complete = directory.is_dir()
    records = []
    # The shared historical iterator includes redispatch attempts and the archive.
    for index, path in enumerate(iter_task_records(directory, include_archive=True)):
        if index >= SCAN_LIMIT:
            complete = False
            break
        try:
            if path.is_symlink() or path.stat().st_size > BYTE_LIMIT:
                raise ValueError
            row = json.loads(path.read_bytes())
            if not isinstance(row, dict):
                raise ValueError
            claims = {row[k] for k in ("repository_id", "repository") if row.get(k)}
            if claims != {REPOSITORY}:
                if len(claims) != 1:
                    complete = False
                continue
            if (
                not isinstance(row.get("task_id"), str)
                or not TOKEN.fullmatch(row["task_id"])
                or not isinstance(row.get("run_nonce"), str)
                or not TOKEN.fullmatch(row["run_nonce"])
            ):
                complete = False
                continue
            if not re.fullmatch(r"[0-9a-f]{16,64}", row["run_nonce"]) and token(row["run_nonce"]) == "unknown":
                complete = False
                continue
            row["_issues"] = task_links(row)
            records.append(row)
            if not row["_issues"]:
                complete = False
        except (OSError, ValueError, TypeError, KeyError):
            complete = False
    # The iterator deliberately suppresses directory failures. Check both directories too.
    for folder in (directory, directory / "archive"):
        try:
            if folder == directory or folder.exists():
                list(folder.iterdir())
        except OSError:
            complete = False
    return records, complete


def running(task):
    """Prove local process identity using reads only, without even signal zero."""
    if task.get("status") != "running":
        return False
    if task.get("schema_version") == 2 and task.get("process_start"):
        from scripts.dispatcher.worker import _identity

        pid = task.get("pid")
        return _identity(pid) == task["process_start"] if type(pid) is int and pid > 0 else None
    identity = task.get("worker_identity") or {}
    pid = task.get("pid")
    if type(pid) is not int or pid <= 0 or identity.get("pid") != pid or type(identity.get("start_time")) is not int:
        return None
    namespace = dead_worker_state._pid_namespace()
    if namespace is None or namespace != identity.get("pid_namespace"):
        return None
    try:
        actual = dead_worker_state._process_stat(str(pid))
        return actual == (pid, identity["start_time"]) and not dead_worker_state.process_is_zombie(pid)
    except (OSError, ValueError, IndexError):
        return None


def _path(root, raw):
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ValueError
    path = Path(raw)
    return path if path.is_absolute() else root / path


def resources(reader, tasks, prs, task_complete):
    result = {kind: [] for kind in ("tasks", "local_branches", "remote_branches", "worktrees", "temp_dirs", "prs")}
    coverage = {kind: "complete" for kind in result}
    if not task_complete:
        coverage.update({kind: "incomplete: task inventory or issue attribution incomplete" for kind in result})
    branches = set()
    paths = set()
    temps = set()
    for row in tasks:
        result["tasks"].append(
            {
                "id": row["task_id"] if token(row["task_id"]) != "unknown" else opaque(row["task_id"]),
                "nonce": row["run_nonce"],
                "status": token(row.get("status")),
            }
        )
        if row.get("worktree_branch"):
            branches.add(row["worktree_branch"])
        else:
            for kind in ("local_branches", "remote_branches"):
                coverage[kind] = "incomplete: task has no branch binding"
        for key, target in (("worktree_path", paths), ("runtime_tmp_root", temps)):
            if row.get(key):
                try:
                    target.add(_path(reader.root, row[key]))
                except ValueError:
                    coverage["worktrees" if key == "worktree_path" else "temp_dirs"] = (
                        "incomplete: invalid resource binding"
                    )
        if not row.get("runtime_tmp_root"):
            coverage["temp_dirs"] = "incomplete: task has no runtime temp inventory"
        if not row.get("worktree_path"):
            coverage["worktrees"] = "incomplete: task has no worktree binding"
    for pr in prs:
        result["prs"].append(
            {
                "number": pr["number"],
                "state": "MERGED" if pr.get("merged_at") else str(pr.get("state", "unknown")).upper(),
            }
        )
        head = pr.get("head") or {}
        if (head.get("repo") or {}).get("full_name") == REPOSITORY and head.get("ref"):
            branches.add(head["ref"])
    for kind, args in (
        ("local_branches", ("for-each-ref", "--format=%(refname:short)", "refs/heads/")),
        ("remote_branches", ("ls-remote", "--heads", f"https://github.com/{REPOSITORY}.git")),
    ):
        try:
            if kind == "remote_branches":
                effective = reader.git("ls-remote", "--get-url", f"https://github.com/{REPOSITORY}.git").strip()
                if effective != f"https://github.com/{REPOSITORY}.git":
                    raise SourceUnavailable("remote_identity_unknown")
            output = reader.git(*args)
            observed = (
                set(output.splitlines())
                if kind == "local_branches"
                else {line.split("\t", 1)[1].removeprefix("refs/heads/") for line in output.splitlines()}
            )
            result[kind] = [
                {"id": opaque(branch), "ref": branch_label(branch), "present": branch in observed}
                for branch in sorted(branches)
            ]
        except (SourceUnavailable, IndexError):
            coverage[kind] = "incomplete: branch listing unavailable"
    registered = None
    try:
        registered = {
            line[9:]
            for line in reader.git("worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")
        }
    except SourceUnavailable:
        coverage["worktrees"] = "incomplete: git worktree listing unavailable"
    for kind, owned in (("worktrees", paths), ("temp_dirs", temps)):
        for path in sorted(owned):
            item = {"path": locator(path, reader.root), "present": None}
            try:
                item["present"] = path.stat().st_mode is not None
            except FileNotFoundError:
                item["present"] = False
            except OSError:
                coverage[kind] = "incomplete: resource existence unknown"
            if kind == "worktrees" and item["present"]:
                try:
                    if not path.resolve().is_relative_to(reader.root):
                        raise SourceUnavailable("outside_repository")
                    item["dirty"] = bool(reader.git("status", "--porcelain", "--untracked-files=all", cwd=path))
                    item["registered"] = str(path) in registered if registered is not None else None
                except (SourceUnavailable, OSError):
                    item["dirty"] = None
                    coverage[kind] = "incomplete: worktree dirt unknown"
            elif kind == "worktrees" and registered is not None:
                item["registered"] = str(path) in registered
                if item["registered"]:
                    coverage[kind] = "incomplete: absent path remains registered"
            result[kind].append(item)
    for kind in result:
        if len(result[kind]) > LIMIT:
            result[kind] = result[kind][:LIMIT]
            coverage[kind] = "incomplete: output limit"
    return result, coverage


def read_reaps(root):
    rows = []
    complete = True
    try:
        with journal_path(root).open() as stream:
            for index, line in enumerate(stream):
                if index >= SCAN_LIMIT or len(line) > BYTE_LIMIT:
                    complete = False
                    break
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
    except (OSError, ValueError):
        complete = False
    return rows, complete


def cleaned(tasks, prs, inventory, coverage, reaps):
    if not tasks or not prs or not all(pr.get("merged_at") for pr in prs):
        return None
    if any(value != "complete" for value in coverage.values()):
        return None
    if any(task.get("status") not in RELEASED_TASK_STATUSES for task in tasks):
        return None
    if any(
        item.get("present") is not False
        for kind in ("local_branches", "remote_branches", "worktrees", "temp_dirs")
        for item in inventory[kind]
    ):
        return None
    matches = []
    for task in tasks:
        proof = task.get("worktree_reap_proof") or {}
        matching_pr = next((pr for pr in prs if pr["number"] == proof.get("pr_number")), None)
        if (
            not matching_pr
            or proof.get("schema") != "merged-reuse-reap.v1"
            or proof.get("owner") != task["task_id"]
            or proof.get("run_nonce") != task["run_nonce"]
            or proof.get("pr_state") != "MERGED"
            or proof.get("clean") is not True
            or proof.get("pr_head_sha") != (matching_pr.get("head") or {}).get("sha")
        ):
            return None
        match = next(
            (
                row
                for row in reversed(reaps)
                if row.get("schema_version") == "worktree-reaper-journal.v1"
                and row.get("event") == "reap"
                and row.get("action") in {"removed", "preserved_then_removed"}
                and row.get("path") == task.get("worktree_path")
                and row.get("branch") == task.get("worktree_branch")
                and (row.get("pr") or {}).get("number") == matching_pr["number"]
                and (row.get("pr") or {}).get("state") == "MERGED"
                and (row.get("pr") or {}).get("head_sha") == proof["pr_head_sha"]
                and timestamp(row.get("at"))
                and timestamp(task.get("started_at"))
                and timestamp(row["at"]) >= timestamp(task["started_at"])
            ),
            None,
        )
        if not match:
            return None
        matches.append(match["at"])
    return max(matches, key=timestamp)


def derive(issue, tasks, prs, review, checks, queue, cleanup_at=None):
    """Map affirmative facts to the approved nine states; preserve conflicts."""
    reasons = []
    state, at, source = "Created", None, "github.initial_issue_observation"
    candidates = []
    authors = [task for task in tasks if task.get("mode") != "read-only" and running(task) is True]
    reviewers = [
        task
        for task in tasks
        if task.get("mode") == "read-only"
        and running(task) is True
        and any(task.get("pinned_head") == (pr.get("head") or {}).get("sha") for pr in prs)
    ]
    if authors:
        candidates.append(("In progress", authors[0].get("started_at"), "native.task.started_at"))
    if reviewers:
        candidates.append(("In review", reviewers[0].get("started_at"), "native.review.started_at"))
    if (
        not candidates
        and not prs
        and any(
            task.get("status") == "spawning" and (task.get("dor_preflight") or {}).get("dor") == "PASS"
            for task in tasks
        )
    ):
        candidates.append(("Ready", None, "native.admitted_dispatch"))
    if review.get("verdict") == "CHANGES_REQUESTED" and review.get("current") is True:
        candidates.append(("Fixing", review.get("at"), "github.review.submitted_at"))
    if review.get("verdict") == "BLOCKED" and review.get("current") is True:
        reasons.append("canonical_review_blocked")
    if review.get("verdict") == "APPROVED" and review.get("current") is True and checks == "pending":
        candidates.append(("Testing", None, "github.exact_head_checks"))
    if queue and queue.get("isInMergeQueue") is True and queue.get("mergeQueueEntry"):
        candidates.append(("Queued", queue["mergeQueueEntry"].get("enqueuedAt"), "github.mergeQueueEntry"))
    if prs and all(pr.get("merged_at") for pr in prs):
        if authors or reviewers:
            reasons.append("running_owned_task_after_merge")
        candidates = [("Merged", max(pr["merged_at"] for pr in prs), "github.pr.merged_at")]
        if cleanup_at:
            candidates = [("Cleaned", cleanup_at, "common_reaper.reap.at")]
    unique = {candidate[0] for candidate in candidates}
    if len(unique) > 1:
        state, at, source = "unknown", None, "conflicting_affirmative_evidence"
        reasons.append("simultaneous_states:" + ",".join(sorted(unique)))
    elif candidates:
        state, at, source = candidates[0]
    if state == "Created" and (prs or any(task.get("status") in RELEASED_TASK_STATUSES for task in tasks)):
        state, at, source = "unknown", None, "no_current_state_evidence"
        reasons.append("native_done_is_not_delivery" if tasks else "open_pr_without_current_phase_evidence")
    if state == "Created" and issue.get("state") != "open":
        state, at, source = "unknown", None, "issue_delivery_evidence_unavailable"
        reasons.append("closed_or_unavailable_issue_without_delivery_evidence")
    if any(task.get("status") == "running" and running(task) is None for task in tasks):
        reasons.append("task_liveness_unknown")
    return state, at, source, reasons


def review_evidence(pr, reviews, ledger, comments, login=None):
    head = (pr.get("head") or {}).get("sha")
    eligible = [row for row in reviews if row.get("state") in {"APPROVED", "CHANGES_REQUESTED"}]
    latest = max(eligible, key=lambda row: row.get("submitted_at") or "", default=None)
    result = {
        "head_sha": head if SHA.fullmatch(str(head)) else None,
        "reviewed_sha": None,
        "current": None,
        "verdict": "unknown",
        "at": None,
    }
    if latest:
        sha = latest.get("commit_id")
        result.update(
            reviewed_sha=sha if SHA.fullmatch(str(sha)) else None,
            current=sha == head,
            verdict=latest["state"],
            at=latest.get("submitted_at"),
        )
    verdict = lookup_verdict(comments, str(head), login)
    # Canonical shared-identity comments are the repository's review of record.
    # A native approval alone does not certify the independent review gate.
    if verdict.state in {"APPROVED", "CHANGES_REQUESTED", "BLOCKED"}:
        matching = [
            row
            for row in comments
            if isinstance(row.get("body"), str)
            and (marker := parse_marker(row["body"]))
            and marker["sha"] == head
            and marker["task"] == verdict.task
        ]
        at = max((row.get("created_at") or "" for row in matching), default=None)
        result.update(reviewed_sha=head, current=True, verdict=verdict.state, at=at)
    elif any(MARKER_PREFIX in str(row.get("body", "")) for row in comments):
        stale = [parse_marker(row["body"]) for row in comments if isinstance(row.get("body"), str)]
        stale = [row for row in stale if row and row["sha"] != head]
        result.update(
            verdict="unknown", current=False if stale else None, reviewed_sha=stale[-1]["sha"] if stale else None
        )
    elif result["verdict"] == "APPROVED":
        result["verdict"] = "unknown"
    result["gate_evidence"] = verdict.state
    return result


def check_state(pr, checks, required):
    head = (pr.get("head") or {}).get("sha")
    if not checks or any(row.get("head_sha") != head for row in checks):
        return "unknown"
    from scripts.github_check_rollup import project_check_runs

    rows = project_check_runs(checks)
    # Never let an absent required-check list or a cancelled run look green.
    if any(
        row.get("conclusion") in {"CANCELLED", "FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}
        for row in rows
    ):
        return "failed"
    if not required:
        return "unknown"
    if any(name not in {row.get("name") for row in rows} for name in required):
        return "unknown"
    passed, pending, failed = task_lifecycle._checks_status(required, rows)
    return "failed" if failed else "passed" if passed else "pending" if pending else "unknown"


def report_issue(reader, number, tasks, task_complete, stream, driver, reaps):
    missing = []
    own = [row for row in tasks if number in row["_issues"]]
    try:
        issue = reader.get("issue", number=number)
        if issue.get("number") != number or "pull_request" in issue:
            raise SourceUnavailable("issue_identity_unknown")
    except (SourceUnavailable, AttributeError):
        issue = {"number": number}
        missing.append("github_issue_unknown")
    ledger = None
    try:
        digest = hashlib.sha256(REPOSITORY.encode()).hexdigest()[:16]
        path = reader.root / ".agent/task-lifecycle" / digest / f"issue-{number}.json"
        if path.exists():
            ledger = task_lifecycle.load_lifecycle(path)
            if ledger["identity"]["repository"] != REPOSITORY or ledger["identity"]["github_issue_number"] != number:
                raise ValueError
    except (OSError, ValueError, KeyError):
        ledger = None
        missing.append("lifecycle_invalid")
    numbers = set()
    if ledger and ledger["pr"]["number"]:
        numbers.add(ledger["pr"]["number"])
    try:
        for event in reader.listing("timeline", number=number):
            other = (event.get("source") or {}).get("issue") or {}
            candidate = other.get("number")
            if (
                "pull_request" in other
                and type(candidate) is int
                and candidate > 0
                and (
                    other.get("repository_url") == f"https://api.github.com/repos/{REPOSITORY}"
                    or (other.get("repository") or {}).get("full_name") == REPOSITORY
                )
            ):
                numbers.add(candidate)
    except (SourceUnavailable, AttributeError):
        missing.append("pr_association_list_incomplete")
    prs = []
    review = {"head_sha": None, "reviewed_sha": None, "current": None, "verdict": "unknown"}
    checks = "unknown"
    queue = None
    if len(numbers) > LIMIT:
        missing.append("pr_output_limit")
    for pr_number in sorted(numbers)[:LIMIT]:
        try:
            pr = reader.get("pull", number=pr_number)
            if pr.get("number") != pr_number or (pr.get("base", {}).get("repo") or {}).get("full_name") != REPOSITORY:
                raise SourceUnavailable("pr_identity_unknown")
            prs.append(pr)
        except (SourceUnavailable, AttributeError):
            missing.append("pr_source_unknown")
    active_prs = [pr for pr in prs if not pr.get("merged_at") and pr.get("state") == "open"]
    target = active_prs[0] if len(active_prs) == 1 else prs[0] if len(prs) == 1 else None
    if target:
        head = (target.get("head") or {}).get("sha")
        review["head_sha"] = head if SHA.fullmatch(str(head)) else None
        try:
            reviews = reader.listing("reviews", number=target["number"])
            comments = reader.listing("comments", number=target["number"])
            login = reader.get("identity").get("login")
            review = review_evidence(target, reviews, ledger, comments, login)
            if review["current"] is False:
                missing.append("moved_head_invalidates_review")
        except SourceUnavailable:
            missing.append("review_source_unknown")
        head = (target.get("head") or {}).get("sha")
        if SHA.fullmatch(str(head)):
            try:
                payload = reader.get("checks", sha=head)
                runs = payload.get("check_runs", [])
                if payload.get("total_count") != len(runs):
                    missing.append("checks_list_incomplete")
                else:
                    checks = check_state(target, runs, (ledger or {}).get("required_checks") or list(REQUIRED_CHECKS))
            except (SourceUnavailable, AttributeError):
                missing.append("checks_source_unknown")
        if checks == "unknown":
            missing.append("absent_ci_or_required_check_contract")
        if not target.get("merged_at"):
            try:
                queue = reader.queue(target["number"], target["base"]["ref"])
                if queue.get("headRefOid") != head:
                    queue = None
                    review.update(current=False, verdict="unknown")
                    checks = "unknown"
                    missing.append("head_changed_during_observation")
            except (SourceUnavailable, KeyError, AttributeError):
                missing.append("queue_unknown")
    inventory, coverage = resources(reader, own, prs, task_complete)
    if any(reason in missing for reason in ("pr_association_list_incomplete", "pr_output_limit", "pr_source_unknown")):
        coverage["prs"] = "incomplete: PR association or listing unavailable"
    if any(value != "complete" for value in coverage.values()):
        missing.append("owned_resource_coverage_incomplete")
    cleanup_at = cleaned(own, prs, inventory, coverage, reaps)
    state, at, source, reasons = derive(issue, own, prs, review, checks, queue, cleanup_at)
    if not issue.get("created_at") and state == "Created":
        state = "unknown"
    if len(active_prs) > 1:
        reasons.append("multiple_active_prs_phase_unknown")
        state, at, source = "unknown", None, "multiple_active_prs"
    if any(item.get("dirty") is True for item in inventory["worktrees"]):
        reasons.append("dirty_retained_worktree")
    if any(pr.get("merged_at") for pr in prs) and not cleanup_at:
        missing.append("cleanup_not_proven_by_terminal_matching_reaper_and_absence")
    failure = checks == "failed" or any(
        row.get("status") in {"failed", "cancelled", "timeout", "crashed"} for row in own
    )
    if failure:
        reasons.append("cancelled_or_failed_ci_or_native_task")
    now = datetime.now(UTC)
    observed_at = timestamp(at)
    age = round((now - observed_at).total_seconds()) if observed_at and observed_at <= now else None
    if age is None:
        missing.append("state_age_unknown_no_transition_timestamp")
    deadlines = []
    try:
        for item in postmerge_criteria.acceptance_items(issue.get("body") or ""):
            if not item.get("checked") and postmerge_criteria.POST_MERGE_RE.search(item["text"]):
                owner, due = postmerge_criteria.item_assignment(item["text"])
                if owner and due:
                    deadlines.append(due)
    except ValueError:
        missing.append("deadline_contract_invalid")
    overdue = any(now.date().isoformat() > due for due in deadlines) if deadlines else None
    if overdue is None:
        missing.append("overdue_unknown_no_authoritative_deadline_or_sla")
    if driver == "unknown":
        missing.append("accountable_driver_unknown")
    actions = {
        "Created": "establish DoR evidence",
        "Ready": "start owned author",
        "In progress": "finish and push source",
        "In review": "return exact-head review",
        "Fixing": "resolve material review findings",
        "Testing": "wait for required same-head checks",
        "Queued": "observe merge queue",
        "Merged": "driver verifies merged behavior and common cleanup",
        "Cleaned": "driver verifies delivery denominator",
    }
    workers = [
        row for row in own if running(row) is True and (row.get("mode") == "read-only") == (state == "In review")
    ]
    actor = token(workers[0].get("agent")) if workers and state in {"In progress", "In review", "Fixing"} else driver
    return {
        "issue": number,
        "lane": stream,
        "driver": driver,
        "state": state,
        "source": source,
        "state_since": observed_at.isoformat() if observed_at else None,
        "age_s": age,
        "review": review,
        "ci": checks,
        "flags": {"blocked": bool(reasons) or None, "failed": failure, "overdue": overdue, "unknown": bool(missing)},
        "reasons": sorted(set(reasons)),
        "missing_evidence": sorted(set(missing)),
        "next_actor": actor,
        "next_action": actions.get(state, "driver reconciles missing or conflicting evidence"),
        "resources": inventory,
        "coverage": coverage,
    }


def lane_driver(lane, registry):
    holders = set()
    for epic in registry.get(lane, []):
        try:
            response = local_read(f"/api/epics/v1/epic:{epic}?limit=0")
            lease = response.get("lease") or {}
            expiry = timestamp(lease.get("expires_at"))
            if (
                response.get("registered") is True
                and response.get("stream_name") == lane
                and lease.get("state") == "active"
                and expiry
                and expiry > datetime.now(UTC)
            ):
                agent = token((lease.get("holder") or {}).get("agent"))
                if agent != "unknown":
                    holders.add(agent)
        except (SourceUnavailable, AttributeError):
            return "unknown"
    if len(holders) != 1:
        return "unknown"
    # This is the launcher's existing stream-to-lane compatibility map.
    try:
        aliases = Path(__file__).parent / "config/launcher_stream_aliases.tsv"
        suffixes = {
            parts[2]
            for line in aliases.read_text().splitlines()
            if not line.startswith("#") and len(parts := line.split("\t")) == 3 and parts[1] == lane
        }
        if len(suffixes) == 1:
            return token(next(iter(holders)) + "-" + next(iter(suffixes)))
    except OSError:
        pass
    return "unknown"


def collect(reader, issue=None, lane=None):
    tasks, complete = read_tasks(reader.root)
    registry = load_registry()
    if lane is not None and lane not in registry:
        raise SourceUnavailable("lane_not_registered")
    missing = []
    selected = {issue} if issue else set()
    membership = read_membership_index(MAX_AGE_S, cache_path=reader.root / "batch_state/issue_stream_audit.json")
    index = (membership or {}).get("effective_membership") or {}
    if not membership or membership.get("repository") != REPOSITORY:
        index = {}
        missing.append("registered_membership_unavailable")
    if lane:
        selected.update(
            int(number)
            for number, entry in index.items()
            if entry.get("unique_stream") is True and entry.get("streams") == [lane]
        )
    if lane:
        try:
            projection = local_read("/api/work/v1/projection?" + urlencode({"stream": lane}))
            for item in projection.get("items") or []:
                if (
                    item.get("repository_id") == REPOSITORY
                    and item.get("resource_kind") == "issue"
                    and str(item.get("remote_id", "")).isdecimal()
                ):
                    candidate = int(item["remote_id"])
                    entry = index.get(str(candidate)) or {}
                    if entry.get("unique_stream") is True and entry.get("streams") == [lane]:
                        selected.add(candidate)
            if projection.get("orientation_bound", {}).get("complete") is not True:
                missing.append("lane_projection_incomplete")
        except SourceUnavailable:
            missing.append("lane_projection_unavailable")
        # Native lifecycle membership is independent of the dashboard's bounded list.
        for row in tasks:
            identity = (row.get("task_lifecycle") or {}).get("identity") or {}
            if identity.get("stream_epic") in registry[lane]:
                selected.update(row["_issues"])
    reaps, reaps_complete = read_reaps(reader.root)
    if not reaps_complete:
        missing.append("common_reaper_history_incomplete")
        reaps = []
    if len(selected) > LIMIT:
        missing.append("issue_output_limit")
    reports = []
    drivers = {}
    active = {number for row in tasks if row.get("status") not in RELEASED_TASK_STATUSES for number in row["_issues"]}
    open_issues = set((membership or {}).get("open_issue_numbers") or [])
    ordered = sorted(selected, key=lambda number: (number not in active, number not in open_issues, number))
    for number in ordered[:LIMIT]:
        entry = index.get(str(number)) or {}
        stream = (
            lane
            if lane
            else (entry.get("streams") or ["unknown"])[0]
            if entry.get("unique_stream") is True
            else "unknown"
        )
        if stream == "unknown":
            roots = [name for name, epics in registry.items() if number in epics]
            if len(roots) == 1:
                stream = roots[0]
        if stream not in drivers:
            drivers[stream] = lane_driver(stream, registry)
        reports.append(report_issue(reader, number, tasks, complete, stream, drivers[stream], reaps))
    if time.monotonic() >= reader.deadline:
        missing.append("read_budget_exhausted")
    return {
        "repository": REPOSITORY,
        "read_only": True,
        "observed_at": datetime.now(UTC).isoformat(),
        "selected_issues": len(selected),
        "reported_issues": len(reports),
        "issues": reports,
        "coverage": "incomplete" if missing or not complete else "complete",
        "missing_evidence": sorted(set(missing + ([] if complete else ["task_inventory_or_attribution_incomplete"]))),
    }


def positive(value):
    if not value.isdecimal() or int(value) <= 0:
        raise argparse.ArgumentTypeError("issue must be a positive integer, e.g. 11689")
    return int(value)


def parser():
    description = "Inspect public issue/lane flow evidence without changing live state.\nUse for progress and resource inspection; use the common reaper separately for cleanup."
    epilog = """Examples:
  .venv/bin/python -m scripts.flow status --issue 11689
  .venv/bin/python -m scripts.flow status --lane devops
Outputs: bounded JSON to stdout; no files, DB updates, leases, providers or cleanup.
Exit codes: 0 report produced (including explicit unknowns); 1 source/refusal/output failure; 2 usage error.
Related: docs/runbooks/flow-status.md; C2492; docs/best-practices/task-quality.md.
"""
    root = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = root.add_subparsers(dest="command", required=True, help="Command, e.g. status")
    status = commands.add_parser(
        "status",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Read bounded flow evidence",
    )
    selector = status.add_mutually_exclusive_group(required=True)
    selector.add_argument(
        "--issue", type=positive, help="Public GitHub issue number, e.g. 11689; default: no issue selector"
    )
    selector.add_argument("--lane", help="Registered stream name, e.g. devops; default: no lane selector")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        root = primary_repository(Path.cwd())
        result = collect(Reader(root), args.issue, args.lane)
        output = json.dumps(result, sort_keys=True, indent=2)
        if len(output.encode()) > OUTPUT_LIMIT:
            raise SourceUnavailable("output_limit_report_incomplete")
        print(output)
        return 0
    except SourceUnavailable as exc:
        print(json.dumps({"read_only": True, "error": str(exc), "coverage": "incomplete"}))
        return 1
    except Exception:
        # Never echo exceptions: upstream diagnostics may contain private bodies or host paths.
        print(
            json.dumps({"read_only": True, "error": "flow_sources_or_selection_unavailable", "coverage": "incomplete"})
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
