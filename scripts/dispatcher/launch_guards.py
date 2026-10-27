"""Legacy launch refusals for dispatch v2: PR freeze, host, model pause, DoR, primary checkout, write claims.

Each guard is a mechanical copy of the legacy ``scripts/delegate.py`` function it names, adapted only to v2's
argument names and repository root. Refusals keep the legacy stderr text and exit code (``Refused``); all
run before any task record, worktree or branch exists, in the legacy order, except the write-path claim
(``WriteClaim``): it is taken once the worktree exists, immediately before the task record, so nothing
that can wait (the worktree lock, the checkout) ever runs while it is held.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.dispatcher import admission, git

_WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})
_CANONICAL_GITHUB_REPO = "learn-ukrainian/learn-ukrainian.github.io"
# delegate.py _ADMISSION_REFUSED_EXIT / _ADMISSION_DISK_REFUSED_EXIT (5122-5125).
_ADMISSION_REFUSED_EXIT = 3
_ADMISSION_DISK_REFUSED_EXIT = 4
CURSOR_AUTO_IMPLEMENTATION_ROLE = "implementation"
_BLOCKQUOTE_LINE_RE = re.compile(r"^\s*>.*$", re.MULTILINE)
_DOR_ISSUE_RE = re.compile(
    r"(?<![\w/=])(?:"
    r"https://github\.com/(?P<url_repo>[\w.-]+/[\w.-]+)/issues/(?P<url_number>\d+)\b"
    r"|(?P<short_repo>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/"
    r"(?!(?:[A-Za-z0-9._-]+\.(?i:md|markdown|py|pyi|rst|txt))#)"
    r"(?=[A-Za-z0-9._-]*[A-Za-z0-9_-]#)[A-Za-z0-9._-]+)"
    r"#(?P<short_number>\d+)\b(?![/\\])"
    r"|#(?P<number>\d+)\b)"
)
# delegate.py _CLEAN_TREE_UNTRACKED_RECEIPT_ALLOWLIST (#6967).
_CLEAN_TREE_UNTRACKED_RECEIPT_ALLOWLIST: tuple[str, ...] = ("batch_state/atlas-jobs/receipts/",)


class Refused(ValueError):
    """A legacy refusal: ``text`` is printed verbatim to stderr and ``code`` is the exit status."""

    def __init__(self, text: str, code: int = 2):
        super().__init__(text)
        self.text, self.code = text, code


def _dispatch_is_review_typed(args) -> bool:
    """delegate.py _dispatch_is_review_typed (17404) over v2's flags (``--risk`` is v2's review risk)."""
    return (
        getattr(args, "pr", None) is not None
        or bool(getattr(args, "review_attempt", None))
        or bool(getattr(args, "require_review_verdict", False))
        or bool(getattr(args, "review_profile", None))
        or bool(getattr(args, "review_author_model", None))
        or bool(getattr(args, "risk", None))
    )


def _declared_owned_paths(raw: object) -> tuple[str, ...] | None:
    """delegate.py _declared_owned_paths (6716)."""
    if not isinstance(raw, (list, tuple)):
        return None
    paths = tuple(str(item) for item in raw if isinstance(item, str) and item.strip())
    return paths or None


def check_open_pr_freeze(args, repository: dict) -> None:
    """delegate.py _check_open_pr_freeze (5272): refuse a new PR-opening write while too many public PRs are open."""
    from scripts.orchestration import pr_freeze

    worktree = getattr(args, "worktree", None)
    if not pr_freeze.opens_new_pr(
        mode=str(getattr(args, "mode", "") or ""),
        repo_role=str(repository.get("role", "") or ""),
        pr=getattr(args, "pr", None),
        cwd=getattr(args, "cwd", None),
        review=_dispatch_is_review_typed(args),
        reused_worktree=bool(worktree) and (Path(worktree) / ".git").exists(),
    ):
        return
    decision = pr_freeze.evaluate(repository["github"], branch=getattr(args, "branch", None))
    if decision.warning:
        print(f"⚠️  {decision.warning}", file=sys.stderr)
    if decision.refused:
        raise Refused(f"❌ {decision.refusal_line(repository['github'])}", _ADMISSION_REFUSED_EXIT)


def check_early_host(mode: str) -> None:
    """delegate.py _early_host_refusal (5235) + _report_dispatch_admission (5170) with no force reason.

    v2 never forwards to another host and has no ``--force-admission``, so the precheck always applies.
    """
    from scripts.orchestration import dispatch_admission

    try:
        decision = dispatch_admission.precheck(mode)
    except ValueError as exc:
        raise Refused(f"❌ invalid dispatch admission threshold: {exc}") from None
    if decision is None or decision.exempt:
        return
    if decision.admitted:
        print(f"🚦 dispatch admission: admitted — {decision.summary()}", file=sys.stderr)
        return
    raise Refused(
        f"❌ {decision.refusal_line()}",
        _ADMISSION_DISK_REFUSED_EXIT if decision.disk_refused else _ADMISSION_REFUSED_EXIT,
    )


def check_model_pause(args) -> None:
    """Operator model pauses and plan-headroom stops (target_admission._refuse_paused, new_dispatch=True).

    v2 pins ``--model`` and never substitutes, so the requested and selected models are the same one.
    No Claude account is passed (the claude lane's headroom reads as unknown) until v2 resolves one.
    As in legacy (delegate.py 19069 ``review=_dispatch_is_review_typed(args)``), only the claude lane's
    headroom holds a review dispatch; operator pauses bind every dispatch.
    """
    from scripts.agent_runtime.model_pause import ModelPausedRefused, account_used_pct, refuse_paused_models

    review = _dispatch_is_review_typed(args)
    used_pct = account_used_pct(None)
    try:
        refuse_paused_models(
            [args.model], used_pct=lambda lane: used_pct(lane) if not review or lane == "claude" else None
        )
    except ModelPausedRefused as exc:
        raise Refused(f"❌ {exc}") from None


def _strip_quoted_content(prompt: str) -> str:
    """delegate.py _strip_quoted_content (2893): drop closed fences and blockquotes before the DoR scan."""
    from scripts.review.verdict_parser import _without_code_fences

    without_fences = _without_code_fences(prompt, keep_unclosed=True)
    return _BLOCKQUOTE_LINE_RE.sub("", without_fences)


def _registered_stream_epics() -> frozenset[int]:
    """delegate.py _registered_stream_epics (13780)."""
    import yaml

    from scripts.orchestration import issue_stream_audit

    try:
        registry = issue_stream_audit.load_registry()
    except (OSError, ValueError, AttributeError, TypeError, yaml.YAMLError):
        return frozenset()
    return frozenset(epic for epics in registry.values() for epic in epics)


def _run_dor_preflight(
    prompt: str, allow_reason: str | None, *, dispatch_repo: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """delegate.py _run_dor_preflight (13797) without the lifecycle carrier, which v2 does not accept."""
    from scripts.ci import check_issue_task_quality
    from scripts.ci.check_issue_task_quality import NON_OVERRIDABLE, AdmissionState, admission_state

    distinct: dict[tuple[str, int], tuple[str, int]] = {}
    for match in _DOR_ISSUE_RE.finditer(_strip_quoted_content(prompt)):
        repo = match.group("url_repo") or match.group("short_repo") or dispatch_repo
        if repo.casefold() == _CANONICAL_GITHUB_REPO.casefold():
            repo = _CANONICAL_GITHUB_REPO
        number = int(match.group("url_number") or match.group("short_number") or match.group("number"))
        distinct.setdefault((repo.casefold(), number), (repo, number))
    candidates = sorted(distinct.values(), key=lambda issue: (issue[1], issue[0].casefold()))
    if not candidates:
        return None, None
    epic_numbers = _registered_stream_epics()
    epics = [c for c in candidates if c[0] == _CANONICAL_GITHUB_REPO and c[1] in epic_numbers]
    tasks = [c for c in candidates if c not in epics]
    warnings: dict[str, str] = {}
    unknown: dict[str, str] = {}
    non_overridable: set[str] = set()
    membership_records: dict[str, Any] = {}
    issue_numbers: list[int] = []
    checker = Path(check_issue_task_quality.__file__)
    issue_repositories: list[dict[str, Any]] = []

    def check(batch: list[tuple[str, int]]) -> None:
        for repo, number in batch:
            label = str(number) if repo.casefold() == _CANONICAL_GITHUB_REPO.casefold() else f"{repo}#{number}"
            recorded = False
            try:
                issue = subprocess.run(
                    ["gh", "api", f"repos/{repo}/issues/{number}"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                if issue.returncode:
                    raise ValueError("issue lookup failed")
                issue_payload = json.loads(issue.stdout)
                if not isinstance(issue_payload, dict) or issue_payload.get("number") != number:
                    raise ValueError("issue lookup must identify the requested number")
                if "pull_request" in issue_payload:
                    continue
                issue_numbers.append(number)
                recorded = True
                if repo.casefold() != _CANONICAL_GITHUB_REPO.casefold():
                    issue_repositories.append({"issue": number, "repo": repo})
                result = subprocess.run(
                    [sys.executable, str(checker), "--issue", str(number), "--repo", repo, "--strict", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=135,
                    check=False,
                )
                payload = json.loads(result.stdout)
                if not isinstance(payload, dict):
                    raise ValueError("checker result must be an object")
                codes = set(payload.get("missing") or [])
                non_overridable.update(codes & NON_OVERRIDABLE)
                # Old checker payloads retain their existing meaning. A missing
                # section is explicitly unchecked, never evidence of membership.
                if "membership" in payload:
                    membership_records[label] = payload["membership"] or {"status": "unchecked"}
                state = admission_state(payload)
                if state is AdmissionState.UNKNOWN and result.returncode == 1:
                    unknown[label] = ",".join(payload["missing"])
                elif result.returncode or state is not AdmissionState.PASS:
                    warnings[label] = ",".join(payload.get("missing") or ["checker_error"])
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError, ValueError):
                if not recorded:
                    issue_numbers.append(number)
                    if repo.casefold() != _CANONICAL_GITHUB_REPO.casefold():
                        issue_repositories.append({"issue": number, "repo": repo})
                warnings[label] = "checker_error"

    check(tasks)
    stream_epics: list[int] = []
    if epics:
        if not issue_numbers:
            # No task issue was checked (none named, or all were pull requests): the epic is all the
            # brief names. An epic is not a task card, so its own card verdict cannot admit the brief,
            # and no override applies.
            names = ", ".join(f"#{number}" for _repo, number in epics)
            return (
                f"❌ DoR refused: dor_epic_only_no_task_issue: the brief names only the stream epic {names}; "
                "name the task issue it implements (#9276)"
            ), None
        stream_epics = [number for _repo, number in epics]
    if not issue_numbers:
        return None, None
    verdict = AdmissionState.WARN if warnings else AdmissionState.UNKNOWN if unknown else AdmissionState.PASS
    record: dict[str, Any] = {"issues": issue_numbers, "warnings": warnings, "dor": verdict.value}
    if unknown:
        record["unknown"] = unknown
    if membership_records:
        record["membership"] = membership_records
    if stream_epics:
        record["stream_epic"] = stream_epics
    if issue_repositories:
        record["issue_repositories"] = issue_repositories
    if allow_reason is not None:
        record["allow_warn_reason"] = allow_reason
    if non_overridable:
        return "❌ DoR refused: " + ",".join(
            sorted(non_overridable)
        ) + "; fix the card or ancestry; no override applies", record
    if warnings and allow_reason is None:
        details = "; ".join(
            f"{('#' + label) if label.isdigit() else label}: {missing}" for label, missing in warnings.items()
        )
        return f"❌ DoR issue card WARN ({details}); fix the issue or pass --allow-dor-warn REASON", record
    if unknown:
        details = "; ".join(f"{('#' + label) if label.isdigit() else label}: {codes}" for label, codes in unknown.items())
        print(f"⚠️ DoR UNKNOWN (timeout) ({details}); membership unverified", file=sys.stderr)
    return None, record


def _cursor_auto_refusal(args, *, agent: str, model: str | None, dor_record: dict[str, Any] | None) -> str | None:
    """delegate.py _cursor_auto_refusal (17458): Cursor Auto runs only a PASS-DoR implementation write."""
    from scripts.ci.check_issue_task_quality import AdmissionState
    from scripts.review.model_catalog import (
        CURSOR_AUTO_OUTSIDE_CODING_TASK_CODE,
        cursor_pinned_models,
        is_cursor_auto_selector,
    )

    if agent != "cursor" or not is_cursor_auto_selector(model):
        return None
    reasons: list[str] = []
    role = str(getattr(args, "research_role", None) or "").strip()
    if not role:
        reasons.append(f"the task is unclassified (no --research-role {CURSOR_AUTO_IMPLEMENTATION_ROLE})")
    elif role != CURSOR_AUTO_IMPLEMENTATION_ROLE:
        reasons.append(f"--research-role {role[:64]!r} is not {CURSOR_AUTO_IMPLEMENTATION_ROLE}")
    if args.mode not in _WRITE_CAPABLE_MODES:
        reasons.append(f"mode {args.mode} is not write-capable")
    if _dispatch_is_review_typed(args):
        reasons.append("the dispatch is review-typed")
    if not _declared_owned_paths(getattr(args, "owned_path", None)):
        reasons.append("no --owned-path")
    if not dor_record or not dor_record.get("issues"):
        reasons.append("no DoR issue card was checked")
    elif (
        ("dor" in dor_record and dor_record["dor"] != AdmissionState.PASS.value)
        or dor_record.get("warnings")
        or dor_record.get("unknown")
        or dor_record.get("allow_warn_reason") is not None
    ):
        reasons.append("the DoR issue card is not PASS")
    if not reasons:
        return None
    pins = " or ".join(f"--model {pin}" for pin in cursor_pinned_models())
    return (
        f"❌ dispatch refused: {CURSOR_AUTO_OUTSIDE_CODING_TASK_CODE}: --agent cursor --model {model} runs only a "
        f"--research-role {CURSOR_AUTO_IMPLEMENTATION_ROLE} write dispatch with owned paths and a PASS DoR issue card ({'; '.join(reasons)}); "
        f"pin a concrete model: {pins} (operator decision 2026-09-30, #9274)"
    )


def check_dor(args, agent: str, prompt: str, repository: dict) -> dict[str, Any]:
    """delegate.py cmd_dispatch 14679-14714 and 15159-15177: ``--allow-dor-warn``, the DoR preflight, Cursor Auto.

    v2 holds the final prompt (stdin included) before any side effect, so the single check here is the one
    legacy binds Auto admission to. Returns the task-record fields legacy persists (16334, 16346-16348).
    """
    from scripts.review.model_catalog import is_cursor_auto_selector

    dor_reason = getattr(args, "allow_dor_warn", None)
    if dor_reason is not None:
        dor_reason = str(dor_reason).strip()
        if not dor_reason:
            raise Refused("❌ --allow-dor-warn requires a non-empty reason")
    dor_record: dict[str, Any] | None = None
    if args.mode in _WRITE_CAPABLE_MODES:
        dor_error, dor_record = _run_dor_preflight(prompt, dor_reason, dispatch_repo=repository["github"])
        if dor_error:
            raise Refused(dor_error)
    if cursor_auto_error := _cursor_auto_refusal(args, agent=agent, model=args.model, dor_record=dor_record):
        raise Refused(cursor_auto_error)
    fields: dict[str, Any] = {"dor_preflight": dor_record}
    if agent == "cursor" and dor_record and is_cursor_auto_selector(args.model):
        fields["cursor_auto_admission"] = {
            "admitted": dor_record.get("dor", "PASS") == "PASS", "model": args.model, "issues": list(dor_record["issues"]),
        }
    return fields


def _format_dirty_entries(entries: list[dict[str, str]], *, limit: int = 10) -> str:
    """delegate.py _format_dirty_entries (3560)."""
    shown = [f"{entry.get('xy', '').strip() or '??'} {entry.get('path', '')}" for entry in entries[:limit]]
    if len(entries) > limit:
        shown.append(f"... and {len(entries) - limit} more")
    return ", ".join(shown) if shown else "(none)"


def _is_untracked_receipt_allowlisted(entry: dict[str, str]) -> bool:
    """delegate.py _is_untracked_receipt_allowlisted (3573)."""
    if entry.get("kind") != "untracked" and entry.get("xy", "").strip() != "??":
        return False
    raw_path = (entry.get("path") or "").replace("\\", "/")
    if raw_path.startswith("./"):
        raw_path = raw_path[2:]
    raw_path = raw_path.lstrip("/")
    for prefix in _CLEAN_TREE_UNTRACKED_RECEIPT_ALLOWLIST:
        clean_prefix = prefix.strip("/")
        if raw_path == clean_prefix or raw_path.startswith(clean_prefix + "/"):
            return True
    return False


def _resolve_dirty_primary_checkout_error(*, mode: str, root: Path) -> str | None:
    """delegate.py _resolve_dirty_primary_checkout_error (3588); ``root`` is the dispatcher's primary checkout."""
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    from scripts.guardrails import worktree_containment as wc

    try:
        status = wc.primary_checkout_dirty_status(root)
    except Exception as exc:
        return (
            "❌ could not verify primary checkout cleanliness before "
            f"write-capable dispatch: {type(exc).__name__}: {exc}"
        )

    if not status.get("protected_branch") or not status.get("dirty"):
        return None

    raw_entries = status.get("entries") or []
    entries = [entry for entry in raw_entries if not _is_untracked_receipt_allowlisted(entry)]
    if not entries:
        return None

    extra_diagnostic = ""
    try:
        from scripts.guardrails import primary_write_guard as pwg

        writable = pwg.get_writable_tracked_files(root)
        if writable:
            offenders = [str(f.relative_to(root)) for f in writable]
            extra_diagnostic = f"   writable tracked files (guard OFF): {', '.join(offenders)}\n"
        else:
            extra_diagnostic = "   writable tracked files (guard ON): (none)\n"
    except Exception as exc:
        extra_diagnostic = f"   could not check write guard status: {exc}\n"

    return (
        "❌ primary checkout is dirty; refusing write-capable dispatch before "
        "creating branch/worktree residue.\n"
        f"   checkout role: {status.get('role')}\n"
        f"   head: {status.get('head_sha')}\n"
        f"   command: {status.get('checked_command')}\n"
        f"   branch: {status.get('branch')}\n"
        f"   dirty files: {_format_dirty_entries(entries)}\n"
        f"{extra_diagnostic}"
        "   Clean/stash the primary checkout, or keep only gitignored local "
        "runtime state, then retry."
    )


def _resolve_primary_integrity_error(*, mode: str, root: Path) -> str | None:
    """delegate.py _resolve_primary_integrity_error (3642): block new writes while the primary is drifted."""
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    try:
        from scripts.audit.check_primary_integrity import check_primary_integrity
        from scripts.common.task_store_paths import tasks_dir

        ok, message = check_primary_integrity(root, fix=False, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  primary-integrity watchdog errored ({type(exc).__name__}: {exc}); "
            "proceeding — the health-poll canary will surface persistent failures",
            file=sys.stderr,
        )
        return None

    if ok:
        return None

    return (
        "❌ primary checkout drift is UNREPAIRED; refusing to start a new "
        "write-capable dispatch (it would branch from a wrong base). Running "
        "dispatches are not touched.\n"
        f"   watchdog: {message}\n"
        "   Inspect the primary checkout and run the explicit doctor only when "
        "appropriate: .venv/bin/python scripts/audit/check_primary_integrity.py "
        "--fix. Evidence is under "
        "data/telemetry/primary-integrity/events.jsonl."
    )


def check_primary(mode: str) -> None:
    """delegate.py cmd_dispatch 14990-14998: the dirty-primary refusal, then the primary-integrity refusal.

    Sequential, as in legacy: a dirty refusal returns before the integrity watchdog writes its telemetry.
    """
    if error := _resolve_dirty_primary_checkout_error(mode=mode, root=git.ROOT):
        raise Refused(error)
    if error := _resolve_primary_integrity_error(mode=mode, root=git.ROOT):
        raise Refused(error)


def admit_write_claim(args, task_id: str, cwd: Path) -> bool:
    """delegate.py cmd_dispatch 15570-15626: write-path ownership admission, immediately before the task record.

    The ledger reads holder liveness from the shared task store, where v2 records live. The requeue
    notification goes only to a caller who named ``--initiator`` (legacy always has an attribution), and
    is deduplicated per dispatch attempt by a fresh nonce: v2 mints the record's run nonce only later.
    Returns whether this dispatcher now holds ledger rows.
    """
    import uuid

    from scripts.guardrails.delegate_ownership import (
        GuardMode,
        admit_write_paths,
        env_guard_mode,
        env_queue_wait_s,
        publish_requeue_notice,
    )

    initiator, notice_nonce = getattr(args, "initiator", None), uuid.uuid4().hex
    guard_mode = env_guard_mode()
    try:
        ownership = admit_write_paths(
            task_id=task_id,
            cwd=cwd,
            mode=str(args.mode),
            owned_paths=_declared_owned_paths(getattr(args, "owned_path", None)),
            allow_path_overlap=getattr(args, "allow_path_overlap", None),
            pid=os.getpid(),
            guard_mode=guard_mode,
            wait_s=env_queue_wait_s(),
            on_queued=lambda notice: print(f"⏳ {notice}", file=sys.stderr, flush=True),
            requeue_on_timeout=True,
            on_requeued=(lambda notice: publish_requeue_notice(
                notice, task_id=task_id, initiator=initiator, run_nonce=notice_nonce,
            )) if initiator else None,
        )
    except Exception as own_exc:
        # WARN (opt-in via DELEGATE_OWNERSHIP_MODE=warn): never crash on ledger I/O.
        # REFUSE (default after #5645): fail closed so conflicts cannot proceed.
        print(f"⚠️  write-path ownership: ledger error: {own_exc}", file=sys.stderr)
        if guard_mode == GuardMode.REFUSE:
            raise Refused(f"❌ write-path ownership refused (ledger error) for task_id={task_id!r}") from None
        return False
    if ownership.queue_timeout:
        raise Refused(f"❌ {ownership.reason} for task_id={task_id!r}")
    if ownership.would_refuse or ownership.override_reason:
        suffix = f" (conflicts={len(ownership.conflicts)})" if ownership.conflicts else ""
        print(f"⚠️  write-path ownership: {ownership.reason}{suffix}", file=sys.stderr)
    if not ownership.admitted:
        raise Refused(f"❌ write-path ownership refused for task_id={task_id!r}: {ownership.reason}")
    return not ownership.skipped


def bind_write_claim(task_id: str, pid: int, cwd: Path) -> None:
    """delegate.py cmd_dispatch 16634-16647: bind the claim rows to the long-lived supervisor pid.

    Unlike the legacy best-effort bind, the rebind proves ownership: it succeeds only while every row of
    the task still names this dispatcher's pid. A claim reclaimed meanwhile (rows gone or re-owned), a bind
    that updates zero rows, or a ledger error refuses the launch.
    """
    from scripts.guardrails.delegate_ownership import update_write_claim_pid

    try:
        bound = update_write_claim_pid(task_id, int(pid), cwd=cwd, owner_pid=os.getpid())
    except Exception as own_exc:
        bound, detail = 0, f"ledger error: {own_exc}"
    else:
        detail = "the claim is no longer held by this dispatcher"
    if not bound:
        message = f"write-path ownership lost before launch for task_id={task_id!r}: {detail}"[:500]
        raise admission.LaunchRefused(message, {"status": "failed", "error": f"write_claim_lost: {message}"})


class WriteClaim:
    """This dispatcher's write-path claim, from admission until the supervisor owns it.

    Admission runs after worktree preparation, so the claim exists only from just before the task record
    is created. ``worker.start`` calls ``bind`` with signals deferred, right after the supervisor exists
    and before it receives its payload; from then on the supervisor pid owns the rows and the ledger
    releases them when it ends. Leaving the context releases this dispatcher's rows unless the supervisor
    took them over; an interrupt during admission releases whatever the admission committed.
    """

    def __init__(self, args, task_id: str, cwd: Path):
        self.mode, self.task_id, self.cwd = str(args.mode), task_id, cwd
        self.spawned = False
        try:
            self.held = admit_write_claim(args, task_id, cwd)
        except Refused:
            raise
        except BaseException:
            # The ledger may have committed this dispatcher's rows before the interrupt landed.
            self.held = self.mode in _WRITE_CAPABLE_MODES
            self.__exit__()
            raise

    def bind(self, pid: int) -> None:
        if self.held:
            bind_write_claim(self.task_id, pid, self.cwd)
        self.spawned = True

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        if not self.held or self.spawned:
            return
        from scripts.guardrails.delegate_ownership import OwnershipLedger

        try:
            # Only rows still naming this dispatcher's pid: a claim another writer reclaimed stays theirs.
            OwnershipLedger(cwd=self.cwd).release(self.task_id, pid=os.getpid())
        except Exception as own_exc:
            print(f"⚠️  write-path ownership: failed to release write claim: {own_exc}", file=sys.stderr)
