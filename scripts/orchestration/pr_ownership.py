"""Keep every open PR owned: ownerless alerts, accepted handoffs and queue custody.

The local merge-queue keeper calls ``keeper_tick`` after each ``--apply`` pass. A PR
with no live owning task (``scripts.fleet.pr_owner_check``) for ``GRACE`` raises one
request on the CTO channel to the CTO inbox. A live owner is the task on the PR's
branch, or the running task named by the ``X-Agent`` trailer on the PR head, on any
branch. The alert stays outstanding, with an hourly reminder, until a named successor
accepts the handoff here, the coordinator records custody of the open PR, or the PR
leaves the open set. Unobservable task telemetry is unknown: it never starts, advances
or clears an alert.

An accepted handoff makes the successor the PR's one owner while its task is live, from
any branch. Coordinator custody is that same handoff with a reason and a decision owner,
recorded with no dispatch task; the PR is not alerted again until that custody is
released or the PR is no longer open. Recording custody ends the current ownerless
episode immediately, and releasing it starts the grace period over. A queue-custody
handoff also names the predecessor whose only remaining step is waiting in the merge
queue; ``queue-exit`` then lets that predecessor end cleanly, but only while the
keeper's ownership check is running.

State is one JSON file next to the shared dispatch task store, written under a lock.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import github_client
from scripts.common.github_client import GitHubRateLimited
from scripts.common.task_store_paths import tasks_dir

GRACE = timedelta(minutes=15)
REMINDER = timedelta(minutes=60)
TICK_INTERVAL = timedelta(minutes=5)
# ``queue-exit`` needs a successful ownership check this recent: the alert is in place.
TICK_FRESH = timedelta(minutes=20)
CUSTODY_COVERS = ("ejection", "stale-approval", "merge-confirmation", "closeout")
CTO_INBOX = "claude-cto"
CTO_CHANNEL = "cto"
SENDER = "merge-queue-keeper"
TASK_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
HISTORY_LIMIT = 200
_ACTIVE = {"spawning", "running"}
_HEAD_TASK = re.compile(
    r"(?m)^X-Agent:[ \t]+(?P<agent>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)/(?P<task>[A-Za-z0-9._-]+)[ \t]*$"
)


class OwnershipError(RuntimeError):
    """Evidence needed for a decision is missing or contradictory."""

    code: str | None = None


class PublishBranchRequired(OwnershipError):
    """A workspace-write task accepted a PR head it was not dispatched to publish.

    Settlement fetches ``publish_branch`` or else the task's own worktree branch.
    A takeover that pushes an existing PR branch must be dispatched with
    ``--branch`` so that name is recorded. Unrecorded remote names stay ignored.
    """

    code = "publish_branch_required"

    def __init__(self, head: str) -> None:
        self.head = head
        super().__init__("publish_branch is not the PR head branch; re-dispatch with --branch " + head)


def state_path() -> Path:
    return tasks_dir().parent / "pr_ownership" / "state.json"


def pr_key(repo: str, number: int) -> str:
    return f"{repo.casefold()}#{number}"


def _empty() -> dict[str, Any]:
    return {"schema": 1, "last_tick": None, "episodes": {}, "handoffs": {}, "history": [], "outbox": []}


def _single_line(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and "\n" not in value and "\r" not in value


def _require_publish_branch(record: Mapping[str, Any] | None, pr: Mapping[str, Any]) -> None:
    """Refuse a workspace-write accept that would settle against a branch nobody pushed.

    ``record`` is the task named by ``LEARN_UKRAINIAN_DISPATCH_TASK_ID``. A missing
    record, or any mode other than workspace-write, is not this gate. Driver custody
    never reaches it.
    """
    if not isinstance(record, Mapping) or record.get("mode") != "workspace-write":
        return
    head = pr.get("headRefName")
    if isinstance(head, str) and head and record.get("publish_branch") == head:
        return
    shown = head if isinstance(head, str) and head else "<head>"
    raise PublishBranchRequired(shown)


def _refused(exc: OwnershipError) -> str:
    body: dict[str, Any] = {"accepted": False, "reason": str(exc)}
    if isinstance(exc.code, str) and exc.code:
        body["code"] = exc.code
    return json.dumps(body)


def decision_custody(handoff: Mapping[str, Any] | None) -> bool:
    """Coordinator custody of an open PR: a reason and a decision owner, not a task acceptance."""
    if not isinstance(handoff, dict):
        return False
    owner = handoff.get("decision_owner")
    return (
        _single_line(handoff.get("reason"))
        and _single_line(owner)
        and handoff.get("pr_state") == "OPEN"
        and handoff.get("successor") == owner
    )


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty()
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise OwnershipError(f"ownership state unreadable: {type(exc).__name__}") from exc
    if not isinstance(data, dict) or data.get("schema") != 1 or not all(
        isinstance(data.get(name), dict) for name in ("episodes", "handoffs")
    ):
        raise OwnershipError("ownership state malformed")
    try:
        for key, episode in data["episodes"].items():
            _at(episode["since"])
            for name in ("alerted_at", "notified_at"):
                if episode[name] is not None:
                    _at(episode[name])
            if type(episode.get("reminders", 0)) is not int:
                raise TypeError(key)
        for key, handoff in data["handoffs"].items():
            int(key.rpartition("#")[2])
            _at(handoff["accepted_at"])
            if not all(isinstance(handoff[name], str) and handoff[name] for name in ("successor", "head")):
                raise TypeError(key)
            if any(name in handoff for name in ("reason", "decision_owner", "pr_state")) and not decision_custody(handoff):
                raise TypeError(key)
        last = data.get("last_tick")
        if last is not None:
            _at(last["at"])
            if not isinstance(last.get("ok"), bool):
                raise TypeError("last_tick")
        if not isinstance(data.setdefault("history", []), list):
            raise TypeError("history")
        outbox = data.setdefault("outbox", [])
        if not isinstance(outbox, list) or not all(
            isinstance(entry, dict) and all(isinstance(entry.get(name), str) for name in ("kind", "key", "body"))
            for entry in outbox
        ):
            raise TypeError("outbox")
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise OwnershipError(f"ownership state malformed: {type(exc).__name__}") from exc
    return data


def _save(path: Path, data: dict[str, Any]) -> None:
    data["history"] = data["history"][-HISTORY_LIMIT:]
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


@contextmanager
def locked(path: Path) -> Iterator[dict[str, Any]]:
    """Read-modify-write the state under an exclusive lock; saves on clean exit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = load(path)
        yield data
        _save(path, data)


def _handoff_map(data: Mapping[str, Any]) -> dict[tuple[str, int], str]:
    """Successor task ids. Decision custody names a person, not a task, so it stays out."""
    result = {}
    for key, handoff in data["handoffs"].items():
        if decision_custody(handoff):
            continue
        repo, _, number = key.rpartition("#")
        result[(repo, int(number))] = handoff["successor"]
    return result


def _end_ownerless_episode(data: dict[str, Any], key: str, *, how: str, successor: str, now: datetime) -> None:
    """Drop this PR's ownerless episode so a later tick cannot inherit its clock.

    An episode that already alerted leaves one cleared notice for the next keeper
    tick. An episode still inside the grace period ends with no notice, as it does
    when an owner returns inside that period.
    """
    episode = data["episodes"].pop(key, None)
    if not episode or not episode.get("alerted_at"):
        return
    data.setdefault("outbox", []).extend(outbox_entries({
        "cleared": [{"pr": key, "how": how, "since": episode["since"]}],
    }))
    data["history"].append({"pr": key, "event": "cleared", "at": now.isoformat(), "successor": successor})


def accepted_handoffs(path: Path | None = None) -> dict[tuple[str, int], str]:
    """(casefolded repo, PR number) -> accepted successor task id, for the owner check.

    Decision custody names a person, not a task, and is left out.
    """
    return _handoff_map(load(path or state_path()))


def _at(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise ValueError("naive timestamp")
    return moment


def step(
    data: dict[str, Any],
    open_keys: set[str],
    findings: Mapping[str, Any],
    now: datetime,
) -> dict[str, list[dict[str, Any]]]:
    """Advance alert episodes for one complete observation; return the notices to send.

    ``open_keys`` are every open PR in the checked repositories; ``findings`` maps a key
    to its ``Finding`` (an ``unknown`` row restarts a pending episode and freezes a raised one).
    """
    notices: dict[str, list[dict[str, Any]]] = {"alert": [], "reminder": [], "cleared": []}
    episodes, handoffs = data["episodes"], data["handoffs"]
    stamp = now.isoformat()
    for key in sorted(set(episodes) - open_keys):
        episode = episodes.pop(key)
        if episode.get("alerted_at"):
            notices["cleared"].append({"pr": key, "how": "PR no longer open", "since": episode["since"]})
            data["history"].append({"pr": key, "event": "closed", "at": stamp})
    for key in sorted(set(handoffs) - open_keys):
        handoff = handoffs.pop(key)
        if decision_custody(handoff):
            data["history"].append({"pr": key, "event": "custody_released", "at": stamp, "how": "PR state changed"})
    for key in sorted(open_keys):
        finding = findings.get(key)
        if decision_custody(handoffs.get(key)):
            finding = None  # held for a decision: not ownerless while the PR stays open
        episode = episodes.get(key)
        if finding is not None and finding.unknown:
            if episode is not None and not episode["alerted_at"]:
                episodes.pop(key)  # unknown time never counts toward the grace period
            continue
        if finding is not None:
            if episode is None:
                episodes[key] = {
                    "since": stamp, "branch": finding.branch, "reason": finding.reason,
                    "last_task": finding.last_task, "alerted_at": None, "notified_at": None, "reminders": 0,
                }
                continue
            episode.update(reason=finding.reason, last_task=finding.last_task)
            if not episode["alerted_at"] and now - _at(episode["since"]) >= GRACE:
                episode["alerted_at"] = episode["notified_at"] = stamp
                notices["alert"].append({"pr": key, **episode})
                data["history"].append({"pr": key, "event": "alerted", "at": stamp, "reason": finding.reason})
            elif episode["alerted_at"] and now - _at(episode["notified_at"]) >= REMINDER:
                episode["notified_at"] = stamp
                episode["reminders"] = episode.get("reminders", 0) + 1
                notices["reminder"].append({"pr": key, **episode})
            continue
        if episode is None:
            continue
        if not episode["alerted_at"]:
            episodes.pop(key)  # an owner returned inside the grace period
            continue
        handoff = handoffs.get(key)
        if handoff and _at(handoff["accepted_at"]) >= _at(episode["since"]):
            episodes.pop(key)
            how = (
                f"custody recorded for {handoff['decision_owner']}"
                if decision_custody(handoff)
                else f"handoff accepted by {handoff['successor']}"
            )
            notices["cleared"].append({"pr": key, "how": how, "since": episode["since"]})
            data["history"].append({"pr": key, "event": "cleared", "at": stamp, "successor": handoff["successor"]})
        else:
            episode["reason"] = "a task owns the branch but no successor has accepted the handoff"
    return notices


def _message(kind: str, rows: list[dict[str, Any]]) -> str:
    lines = {
        "alert": "Ownerless PRs: no live owning task for 15 minutes. Seat one owner per PR, or record "
                 "custody with a reason and a decision owner "
                 "(python -m scripts.orchestration.pr_ownership accept --pr N --reason ... "
                 "--decision-owner ...). The alert stays outstanding until that acceptance is recorded.",
        "reminder": "Still ownerless PRs: no successor has accepted the handoff yet.",
        "cleared": "Ownerless-PR alerts cleared.",
    }[kind]
    body = [lines]
    for row in rows:
        detail = row.get("how") or row.get("reason")
        last = f" last task {row['last_task']}" if row.get("last_task") else ""
        body.append(f"- {row['pr']} ({row.get('branch', '')}) since {row['since']}: {detail}.{last}")
    return "\n".join(body)


def outbox_entries(notices: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    """Freeze one CTO inbox request per notice kind, body and key together.

    The key is the notices' logical identity (PR, episode start, reminder number), never
    the clock. The entry is saved before delivery and retried unchanged, so a retry after
    an unsaved delivery is a no-op or a reconciled key reuse (``deliver``), never a
    second alert.
    """
    entries = []
    for kind in ("alert", "reminder", "cleared"):
        rows = notices.get(kind) or []
        if not rows:
            continue
        identity = [[row["pr"], row["since"], row.get("reminders", 0) if kind == "reminder" else 0] for row in rows]
        digest = hashlib.sha256(json.dumps(sorted(identity)).encode()).hexdigest()[:24]
        entries.append({"kind": kind, "key": f"pr-ownership:{kind}:{digest}", "body": _message(kind, rows)})
    return entries


def deliver(outbox: list[dict[str, str]], service: Any) -> list[str]:
    """Send every outbox entry; returns the errors. Sent entries leave the outbox.

    The authority adds the channel's current context revision to each payload, so a
    retry after a lost save can differ from the delivered payload. The authority stores
    the key in the same transaction as the message, and only this module mints these
    keys, from the notice's identity: a "key reused" refusal proves this notice was
    already published, so the entry is reconciled as delivered.
    """
    from scripts.fleet_comms.authority import AuthorityServiceError

    errors = []
    for entry in list(outbox):
        try:
            # An ordinary CTO-channel request the CTO claims and acks. A supervisory request
            # is a launcher wake event: the CTO never consumes one.
            service.publish_message(
                sender=SENDER,
                body=entry["body"],
                channel=CTO_CHANNEL,
                recipients=(CTO_INBOX,),
                kind="request",
                correlation_id=f"pr-ownership:{entry['kind']}",
                provenance={"Source": "merge-queue-keeper", "Agent": SENDER, "Via": "pr-ownership"},
                idempotency_key=entry["key"],
            )
        except AuthorityServiceError as exc:
            if str(exc) != "idempotency_key_reused_with_different_payload":
                errors.append(f"{entry['key']}: {exc}")
                continue
        except Exception as exc:  # one entry never blocks the others
            errors.append(f"{entry['key']}: {type(exc).__name__}")
            continue
        outbox.remove(entry)
    return errors


@dataclass(frozen=True)
class Finding:
    """An open PR without a verifiably live owner; ``unknown`` when its owner cannot be observed."""

    repo: str
    number: int
    branch: str
    reason: str
    last_task: str | None = None
    unknown: bool = False


def liveness(record: Mapping[str, Any] | None) -> bool | None:
    """True for a live supervisor, False for a finished task or a provably gone or replaced
    supervisor, None when the record or the host gives no identity to observe.

    The identity is the one ``scripts.dispatcher.worker`` records (boot id and process
    start time), read here so that an unreadable source stays unknown instead of gone.
    """
    if record is None or record.get("status") not in _ACTIVE:
        return False
    pid, started = record.get("pid"), record.get("process_start")
    if not pid or not started:
        return None
    try:
        stat = Path(f"/proc/{int(pid)}/stat").read_text()
    except FileNotFoundError:
        return None if not Path("/proc/self/stat").exists() else False
    except (OSError, ValueError, TypeError):
        return None
    try:
        fields = stat.rsplit(")", 1)[1].split()
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        start_ticks = fields[19]
    except (OSError, IndexError):
        return None
    if fields[0] == "Z":
        return False
    return f"{boot}:{start_ticks}" == started


def _head_commit(pr: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """The commit at ``headRefOid``. With no oid, the last commit. Never a different oid."""
    commits = pr.get("commits")
    if not isinstance(commits, list):
        return None
    rows = [commit for commit in commits if isinstance(commit, dict)]
    if not rows:
        return None
    head = pr.get("headRefOid")
    if isinstance(head, str) and head:
        for commit in rows:
            if commit.get("oid") == head:
                return commit
        return None
    return rows[-1]


def _head_task_ids(pr: Mapping[str, Any]) -> list[str]:
    """Task ids from well-formed ``X-Agent`` trailers on the PR head commit."""
    commit = _head_commit(pr)
    if commit is None:
        return []
    parts = []
    for name in ("messageHeadline", "messageBody"):
        value = commit.get(name)
        if isinstance(value, str) and value:
            parts.append(value)
    message = "\n".join(parts).replace("\r\n", "\n").replace("\r", "\n")
    return [match.group("task") for match in _HEAD_TASK.finditer(message)]


def _with_head_commits(
    open_prs: Mapping[str, list[dict[str, Any]]],
    records: list[dict[str, Any]],
    repos: Mapping[str, Any],
    live: Callable[[Mapping[str, Any] | None], bool | None] = liveness,
) -> dict[str, list[dict[str, Any]]]:
    """``open_prs`` with the head commit attached, but only where the branch has no live owner.

    The head trailer can only matter for a PR the branch check would report, so every other
    PR costs no extra read. A failed read raises ``OwnershipError``: never a false alert.
    """
    from scripts.fleet import pr_owner_check as check

    pending = {
        (row.repo.casefold(), row.number)
        for row in check.evaluate(open_prs, records, repos, lambda record: live(record) is not False)
    }
    result: dict[str, list[dict[str, Any]]] = {}
    for slug, prs in open_prs.items():
        result[slug] = [
            _with_head_commit(slug, pr) if (slug.casefold(), int(pr["number"])) in pending else pr for pr in prs
        ]
    return result


def _with_head_commit(slug: str, pr: dict[str, Any]) -> dict[str, Any]:
    oid = pr.get("headRefOid")
    if pr.get("isCrossRepository") or not isinstance(oid, str) or not oid:
        return pr
    proc = github_client.run(
        ["gh", "api", f"repos/{slug}/git/commits/{oid}"],
        capture_output=True, text=True, check=False, timeout=60,
    )
    try:
        message = json.loads(proc.stdout).get("message") if proc.returncode == 0 else None
    except (ValueError, AttributeError):
        message = None
    if not isinstance(message, str):
        raise OwnershipError(f"cannot read the head commit of {slug}#{pr['number']}")
    headline, _, body = message.partition("\n")
    return {**pr, "commits": [{"oid": oid, "messageHeadline": headline, "messageBody": body}]}


def findings(
    open_prs: Mapping[str, list[dict[str, Any]]],
    records: list[dict[str, Any]],
    repos: Mapping[str, Any],
    handoffs: Mapping[tuple[str, int], str],
    live: Callable[[Mapping[str, Any] | None], bool | None] = liveness,
) -> list[Finding]:
    """The owner check (``pr_owner_check.evaluate``) with accepted handoffs and unknown liveness.

    An accepted successor owns the PR from any branch while it is live. So does a running
    task named by the head commit's ``X-Agent`` trailer. A PR is ownerless only when no
    candidate owner is live or unobservable; with an unobservable one it is unknown.
    """
    from scripts.fleet import pr_owner_check as check

    by_id = {record.get("task_id"): record for record in records if record.get("task_id")}
    successors = {}
    unobservable: set[tuple[str, int]] = set()
    seated = list(records)
    for slug, prs in open_prs.items():
        for pr in prs:
            key = (slug.casefold(), int(pr["number"]))
            record = by_id.get(handoffs.get(key))
            if record is not None:
                successors[key] = record
                seated.append({**record, "repository": slug, "worktree_branch": pr.get("headRefName")})
            if pr.get("isCrossRepository"):
                continue
            branch = pr.get("headRefName")
            if not isinstance(branch, str) or not branch:
                continue
            for task_id in _head_task_ids(pr):
                named = by_id.get(task_id)
                if named is None or check._record_repository(named, repos) != slug.casefold():
                    continue
                state = live(named)
                if state is False:
                    continue
                seated.append({**named, "worktree_branch": branch})
                if state is None:
                    unobservable.add(key)
    strict = check.evaluate(open_prs, seated, repos, lambda record: live(record) is True)
    lenient = {(f.repo, f.number) for f in check.evaluate(open_prs, seated, repos, lambda r: live(r) is not False)}
    result = []
    for row in strict:
        key = (row.repo.casefold(), row.number)
        successor = live(successors[key]) if key in successors else False
        if successor is True:
            continue  # the owner check never seats a task on a fork PR's branch
        unknown = (row.repo, row.number) not in lenient or successor is None or key in unobservable
        reason = "an owner is active but its supervisor cannot be observed (unknown)" if unknown else row.reason
        result.append(Finding(row.repo, row.number, row.branch, reason, row.last_task, unknown))
    return result


def _observe(handoffs: Mapping[tuple[str, int], str]) -> tuple[set[str], dict[str, Finding]]:
    """Every open PR key and its finding, across the owner check's default fleet repositories."""
    from scripts.dispatcher import store
    from scripts.fleet import pr_owner_check as check
    from scripts.orchestration.fleet_repos import load_fleet_repos

    repos = load_fleet_repos()
    records = store.list_tasks(strict=True)
    open_prs = {repos[k].github: check.fetch_open_prs(repos[k].github) for k in check.DEFAULT_REPO_KEYS}
    open_prs = _with_head_commits(open_prs, records, repos)
    rows = findings(open_prs, records, repos, handoffs)
    keys = {pr_key(slug, int(pr["number"])) for slug, prs in open_prs.items() for pr in prs}
    return keys, {pr_key(f.repo, f.number): f for f in rows}


def _default_service() -> Any:
    from scripts.fleet_comms.authority import AuthorityService

    return AuthorityService(root=None)


def keeper_tick(
    *,
    now: datetime | None = None,
    path: Path | None = None,
    observe: Callable[[Mapping[tuple[str, int], str]], tuple[set[str], dict[str, Any]]] = _observe,
    service_factory: Callable[[], Any] = _default_service,
) -> tuple[list[str], bool]:
    """Run one throttled ownership check; returns (log lines, failed)."""
    now = now or datetime.now(UTC)
    path = path or state_path()
    try:
        return _tick(now, path, observe, service_factory)
    except (OwnershipError, OSError) as exc:
        return [f"pr ownership: state unusable ({display(exc)}); alerts unchanged"], True


def display(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc)[:200]}" if str(exc) else type(exc).__name__


def _unknown_interval(data: dict[str, Any]) -> None:
    """The whole source is unknown: no pending episode may count this time toward grace."""
    for key in [key for key, episode in data["episodes"].items() if not episode["alerted_at"]]:
        data["episodes"].pop(key)


def _tick(now, path, observe, service_factory) -> tuple[list[str], bool]:
    with locked(path) as data:
        last = data.get("last_tick") or {}
        if last.get("ok") and now - _at(last["at"]) < TICK_INTERVAL:
            return [], False
        try:
            keys, findings = observe(_handoff_map(data))
        except GitHubRateLimited:
            # The queue pass reports this as a skip; so does the ownership check.
            _unknown_interval(data)
            data["last_tick"] = {"at": now.isoformat(), "ok": False, "error": "GitHubRateLimited"}
            return ["pr ownership: skipped (GitHub rate limited); raised alerts unchanged"], False
        except Exception as exc:  # any unreadable source is unknown
            _unknown_interval(data)
            data["last_tick"] = {"at": now.isoformat(), "ok": False, "error": type(exc).__name__}
            return [f"pr ownership: UNKNOWN ({type(exc).__name__}); raised alerts unchanged"], True
        findings = {
            key: finding for key, finding in findings.items()
            if not decision_custody(data["handoffs"].get(key))
        }
        notices = step(data, keys, findings, now)
        outbox = data.setdefault("outbox", [])
        outbox.extend(outbox_entries(notices))
        _save(path, data)  # the frozen payloads exist on disk before any delivery
        try:
            with service_factory() as service:
                errors = deliver(outbox, service)
        except Exception as exc:
            errors = [f"CTO inbox unavailable: {type(exc).__name__}"]
        data["last_tick"] = {"at": now.isoformat(), "ok": not errors}
        unknown = sorted(key for key, finding in findings.items() if finding.unknown)
        outstanding = sorted(key for key, episode in data["episodes"].items() if episode["alerted_at"])
        lines = [
            f"pr ownership: open={len(keys)} ownerless={len(findings) - len(unknown)} unknown={len(unknown)} "
            f"alerts_outstanding={len(outstanding)} new={len(notices['alert'])} cleared={len(notices['cleared'])} "
            f"undelivered={len(outbox)}"
        ]
        lines += [f"pr ownership alert outstanding: {key}" for key in outstanding]
        lines += [f"pr ownership unknown: {key}" for key in unknown]
        lines += [f"pr ownership delivery FAILED: {error}" for error in errors]
        return lines, bool(errors)


def _gh_pr(repo: str, number: int) -> dict[str, Any]:
    proc = github_client.run(
        ["gh", "pr", "view", str(number), "--repo", repo, "--json",
         "state,headRefOid,headRefName,baseRefName,isCrossRepository,commits"],
        capture_output=True, text=True, check=False, timeout=60,
    )
    try:
        pr = json.loads(proc.stdout) if proc.returncode == 0 else None
    except ValueError:
        pr = None
    if not isinstance(pr, dict) or not isinstance(pr.get("headRefOid"), str):
        raise OwnershipError(f"cannot read {repo}#{number}")
    return pr


def _queued_at(repo: str, number: int, head: str, base: str) -> bool | None:
    """Queue membership from one GitHub observation that also shows the PR head is ``head``.

    None when the head differs in that observation or the read fails: never queued.
    """
    from scripts.orchestration.integration_sweep import GitHubAdapter, SweepError

    try:
        return GitHubAdapter(Path.cwd()).queue_membership(
            repo, {"number": number, "headRefOid": head, "baseRefName": base}
        )
    except SweepError:
        return None


def _rerun_allowance(repo: str, number: int, head: str) -> str:
    """The head's one evidenced CI rerun, from the shared ledger every owner uses."""
    from scripts.opsec.prepublish import PublishBlocked
    from scripts.publish import recovery

    try:
        first = recovery.first_attempt(recovery.ledger_path(Path.cwd()), repo, number, head)
    except PublishBlocked:
        return "unknown"
    return recovery.spent_reason(first) if first else "unspent"


def accept(
    data: dict[str, Any],
    *,
    repo: str,
    number: int,
    pr: Mapping[str, Any],
    successor: str,
    records: list[dict[str, Any]],
    predecessor: str | None,
    custody: bool,
    now: datetime,
    rerun: str,
    repos: Mapping[str, Any],
    live: Callable[[Mapping[str, Any] | None], bool | None] | None = None,
) -> dict[str, Any]:
    """Record ``successor`` as the PR's one owner; refuse while another live owner remains.

    Who owns the PR follows the owner check exactly (repository, legacy records, forks,
    accepted handoffs), so a same-named branch elsewhere never counts.

    Inside a dispatched workspace-write task, the task id the dispatcher exports
    (``LEARN_UKRAINIAN_DISPATCH_TASK_ID``) must already record ``publish_branch`` as
    this PR's head branch. Otherwise settlement would fetch a branch that never
    reaches the remote. Coordinator custody does not call ``accept``.
    """
    live = live or liveness
    if pr.get("state") != "OPEN":
        raise OwnershipError(f"PR is {pr.get('state')}, not open")
    by_id = {record.get("task_id"): record for record in records}
    # The exported id is the running task. A record that is not in this snapshot
    # is not treated as workspace-write: the liveness check below still fails closed.
    task_id = os.environ.get(TASK_ENV)
    if task_id:
        _require_publish_branch(by_id.get(task_id), pr)
    if predecessor and not custody:
        raise OwnershipError("--from names a live predecessor and needs --custody")
    if (state := live(by_id.get(successor))) is not True:
        raise OwnershipError(f"successor {successor} is {'unknown' if state is None else 'not live'}")
    key = pr_key(repo, number)
    previous = data["handoffs"].get(key)
    # A decision owner is a person. The same string on a live task is not ownership.
    seated = (
        {(repo.casefold(), number): previous["successor"]}
        if previous and not decision_custody(previous) else {}
    )

    def owns(record: Mapping[str, Any]) -> bool:
        target = {repo: [{**pr, "number": number}]}
        return not findings(target, [dict(record)], repos, seated, live=lambda _record: True)

    if custody and not (
        (record := by_id.get(predecessor)) is not None and owns(record) and live(record) is True
    ):
        raise OwnershipError("queue custody needs the PR's live owner that is waiting in the queue (--from)")
    blocking = sorted(
        record["task_id"] for record in records
        if record.get("task_id") not in {successor, predecessor}
        and live(record) is not False and owns(record)
    )
    if blocking:
        raise OwnershipError(f"one owner at a time: {', '.join(blocking)} may still own this PR")
    handoff = {
        "successor": successor,
        "predecessor": predecessor,
        "accepted_at": now.isoformat(),
        "head": pr["headRefOid"],
        "custody": list(CUSTODY_COVERS) if custody else [],
        "rerun_allowance": rerun,
    }
    data["handoffs"][key] = handoff
    data["history"].append({"pr": key, "event": "accepted", "at": handoff["accepted_at"], **handoff})
    return handoff


def queue_exit(
    data: Mapping[str, Any],
    *,
    repo: str,
    number: int,
    pr: Mapping[str, Any],
    queued: bool | None,
    me: str,
    records: list[dict[str, Any]],
    now: datetime,
    live: Callable[[Mapping[str, Any] | None], bool | None] | None = None,
) -> list[str]:
    """Reasons ``me`` must keep waiting; empty means it may exit cleanly."""
    live = live or liveness
    reasons = []
    last = data.get("last_tick") or {}
    if not last.get("ok") or now - _at(last["at"]) > TICK_FRESH:
        reasons.append("the keeper's ownership alert has not run successfully in the last 20 minutes")
    handoff = data["handoffs"].get(pr_key(repo, number))
    if not handoff or handoff.get("predecessor") != me or tuple(handoff.get("custody") or ()) != CUSTODY_COVERS:
        reasons.append("no accepted queue custody names this task as predecessor")
    else:
        by_id = {record.get("task_id"): record for record in records}
        if handoff["successor"] == me or live(by_id.get(handoff["successor"])) is not True:
            reasons.append(f"custodian {handoff['successor']} is not verifiably live")
        if handoff["head"] != pr.get("headRefOid"):
            reasons.append("the PR head moved after custody was accepted")
    if pr.get("state") != "OPEN":
        reasons.append(f"PR is {pr.get('state')}: finish the closeout yourself")
    if queued is not True:
        reasons.append("the PR is not verifiably in the merge queue at the custody head")
    return reasons


def record_decision_custody(
    data: dict[str, Any],
    *,
    repo: str,
    number: int,
    pr: Mapping[str, Any],
    reason: str,
    decision_owner: str,
    records: list[dict[str, Any]],
    now: datetime,
    rerun: str,
    repos: Mapping[str, Any],
    live: Callable[[Mapping[str, Any] | None], bool | None] | None = None,
) -> dict[str, Any]:
    """Record coordinator custody on the existing handoff. No dispatch task is involved.

    Refuses while a live or unobservable owner remains, and when the PR is not open.
    """
    reason, decision_owner = reason.strip(), decision_owner.strip()
    if not _single_line(reason) or not _single_line(decision_owner):
        raise OwnershipError("recorded custody needs a single-line reason and decision owner")
    if pr.get("state") != "OPEN":
        raise OwnershipError(f"PR is {pr.get('state')}, not open")
    head = pr.get("headRefOid")
    if not isinstance(head, str) or not head:
        raise OwnershipError("PR head is unreadable")
    rows = findings(
        {repo: [{**dict(pr), "number": number}]}, records, repos, _handoff_map(data), live or liveness,
    )
    if any(row.unknown for row in rows):
        raise OwnershipError("an owner is active but its supervisor cannot be observed")
    if not rows:
        raise OwnershipError("a live owner already has this PR")
    handoff = {
        "successor": decision_owner,
        "predecessor": None,
        "accepted_at": now.isoformat(),
        "head": head,
        "custody": [],
        "rerun_allowance": rerun,
        "reason": reason,
        "decision_owner": decision_owner,
        "pr_state": "OPEN",
    }
    key = pr_key(repo, number)
    data["handoffs"][key] = handoff
    data["history"].append({"pr": key, "event": "accepted", "at": handoff["accepted_at"], **handoff})
    _end_ownerless_episode(
        data, key, how=f"custody recorded for {decision_owner}", successor=decision_owner, now=now,
    )
    return handoff


def release_decision_custody(
    data: dict[str, Any],
    *,
    repo: str,
    number: int,
    pr: Mapping[str, Any],
    now: datetime,
) -> dict[str, Any]:
    """Drop coordinator custody. A task acceptance is left in place."""
    key = pr_key(repo, number)
    handoff = data["handoffs"].get(key)
    if not decision_custody(handoff):
        if handoff:
            raise OwnershipError("this handoff is a task acceptance, not recorded custody")
        return {"released": False, "pr": key, "reason": "no recorded custody"}
    how = "released" if pr.get("state") == "OPEN" else "PR state changed"
    # Record already ends the episode. This catches one that no tick has seen since.
    _end_ownerless_episode(
        data, key, how=f"custody recorded for {handoff['decision_owner']}",
        successor=handoff["decision_owner"], now=now,
    )
    data["handoffs"].pop(key)
    data["history"].append({"pr": key, "event": "custody_released", "at": now.isoformat(), "how": how})
    return {"released": True, "pr": key, "how": how}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record PR ownership handoffs and queue custody, and check whether a queue-waiting "
            "owner may exit.\nThe merge-queue keeper runs the ownerless-PR alert itself; use this "
            "CLI as the successor, custodian or waiting owner. Not for judging review or CI state."
        ),
        epilog=(
            "Examples:\n"
            "  python -m scripts.orchestration.pr_ownership check\n"
            "  python -m scripts.orchestration.pr_ownership status\n"
            "  python -m scripts.orchestration.pr_ownership accept --pr 42\n"
            "  python -m scripts.orchestration.pr_ownership accept --pr 42 --custody --from TASK\n"
            "  python -m scripts.orchestration.pr_ownership accept --pr 42 --reason REASON --decision-owner OWNER\n"
            "  python -m scripts.orchestration.pr_ownership accept --pr 42 --release\n"
            "  python -m scripts.orchestration.pr_ownership queue-exit --pr 42\n\n"
            "accept --reason and --decision-owner records coordinator custody with no dispatch task.\n"
            "--release drops that custody. The PR is not alerted again while it stays open.\n"
            "Other accept and queue-exit act as the dispatch task named by LEARN_UKRAINIAN_DISPATCH_TASK_ID.\n"
            "Outputs: JSON on stdout (check: one line per PR without a live owner);\n"
            "  only accept writes the shared ownership state.\n"
            "Exit codes: 0 accepted / may exit / every PR owned / status printed;\n"
            "  1 refused / keep waiting / a PR is ownerless;\n"
            "  2 GitHub, task records or ownership state unreadable, or an owner unobservable (unknown).\n"
            "Related: scripts/fleet/pr_owner_check.py, scripts/orchestration/merge_queue_keeper.py, "
            "full-send references/pr-watch.md, epic #10453."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("status", help="Print outstanding alerts, handoffs and the last keeper tick")
    subs.add_parser("check", help="List open PRs with no live owner, counting accepted handoffs (read-only)")
    for name, text in (("accept", "Accept ownership of a PR as its named successor"),
                       ("queue-exit", "Exit 0 when this waiting owner may end under queue custody")):
        sub = subs.add_parser(name, help=text)
        sub.add_argument("--pr", type=int, required=True, help="PR number, e.g. 42")
        sub.add_argument("--repo", default=None,
                         help="owner/name (default: the default fleet repository)")
        if name == "accept":
            sub.add_argument("--custody", action="store_true",
                             help="Accept queue custody: ejection, stale approval, merge confirmation, closeout")
            sub.add_argument("--from", dest="predecessor",
                             help="Live predecessor task waiting in the queue; needs --custody")
            sub.add_argument("--reason", default=None,
                             help="Why the PR is held. With --decision-owner, records custody without a dispatch task")
            sub.add_argument("--decision-owner", default=None,
                             help="Who decides. With --reason, records custody without a dispatch task")
            sub.add_argument("--release", action="store_true",
                             help="Release recorded custody so an ownerless PR can alert again")
    return parser


def _coordinator_accept(args: argparse.Namespace, path: Path) -> int:
    """Record or release decision custody. Does not require a dispatch task id."""
    if args.release and (args.reason is not None or args.decision_owner is not None or args.custody or args.predecessor):
        print(json.dumps({"accepted": False, "reason": "release recorded custody on its own"}))
        return 1
    if not args.release and (args.custody or args.predecessor or not args.reason or not args.decision_owner):
        print(json.dumps({
            "accepted": False,
            "reason": "recorded custody needs --reason and --decision-owner, and not --custody",
        }))
        return 1
    from scripts.dispatcher import store
    from scripts.orchestration.fleet_repos import load_fleet_repos

    repos = load_fleet_repos()
    repo = args.repo or next(item.github for item in repos.values() if item.default)
    pr = _gh_pr(repo, args.pr)
    now = datetime.now(UTC)
    records = [] if args.release else store.list_tasks(strict=True)
    rerun = "unspent" if args.release else _rerun_allowance(repo, args.pr, pr["headRefOid"])
    with locked(path) as data:
        try:
            receipt = (
                release_decision_custody(data, repo=repo, number=args.pr, pr=pr, now=now)
                if args.release
                else record_decision_custody(
                    data, repo=repo, number=args.pr, pr=pr, reason=args.reason,
                    decision_owner=args.decision_owner, records=records, now=now, rerun=rerun, repos=repos,
                )
            )
        except OwnershipError as exc:
            print(json.dumps({"accepted": False, "reason": str(exc)}))
            return 1
    print(json.dumps({"accepted": True, "pr": pr_key(repo, args.pr), **receipt}))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = state_path()
    try:
        if args.command == "status":
            print(json.dumps(load(path), indent=2, sort_keys=True))
            return 0
        if args.command == "check":
            data = load(path)
            keys, rows = _observe(_handoff_map(data))
            rows = {key: row for key, row in rows.items() if not decision_custody(data["handoffs"].get(key))}
            for row in rows.values():
                print(json.dumps(asdict(row), sort_keys=True))
            print(f"{len(keys) - len(rows)}/{len(keys)} open PRs have a live owner", file=sys.stderr)
            if any(not row.unknown for row in rows.values()):
                return 1
            return 2 if rows else 0
        if args.command == "accept" and (
            args.release or args.reason is not None or args.decision_owner is not None
        ):
            return _coordinator_accept(args, path)
        me = os.environ.get(TASK_ENV)
        if not me:
            raise OwnershipError(f"{TASK_ENV} is unset: only a dispatch task can accept or exit")
        from scripts.dispatcher import store
        from scripts.orchestration.fleet_repos import load_fleet_repos

        repo = args.repo or next(r.github for r in load_fleet_repos().values() if r.default)
        records = store.list_tasks(strict=True)
        pr = _gh_pr(repo, args.pr)
        now = datetime.now(UTC)
        if args.command == "accept":
            rerun = _rerun_allowance(repo, args.pr, pr["headRefOid"])
            with locked(path) as data:
                try:
                    receipt = accept(
                        data, repo=repo, number=args.pr, pr=pr, successor=me, records=records,
                        predecessor=args.predecessor, custody=args.custody, now=now, rerun=rerun,
                        repos=load_fleet_repos(),
                    )
                except OwnershipError as exc:
                    print(_refused(exc))
                    return 1
            print(json.dumps({"accepted": True, "pr": pr_key(repo, args.pr), **receipt,
                              "review_budget": "carried by the PR's review ledger; read it before acting"}))
            return 0
        data = load(path)
        handoff = data["handoffs"].get(pr_key(repo, args.pr))
        # Membership is read together with the head, bound to the custody head.
        queued = _queued_at(repo, args.pr, handoff["head"], pr.get("baseRefName") or "main") if handoff else None
        reasons = queue_exit(data, repo=repo, number=args.pr, pr=pr, queued=queued,
                             me=me, records=records, now=now)
        print(json.dumps({"may_exit": not reasons, "reasons": reasons}))
        return 1 if reasons else 0
    except (OwnershipError, GitHubRateLimited, RuntimeError, ValueError, OSError, KeyError, TypeError) as exc:
        print(f"UNKNOWN: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
