"""Public task-record causes and private diagnostics, copied from delegate (#9907).

The legacy delegate sink keeps its own copy until Phase B removes it. This
shared copy lets maintenance preserve the same closed causes, redaction,
private diagnostic permissions and rotation without importing delegate.
"""

from __future__ import annotations

import contextlib
import dataclasses
import errno
import fcntl
import functools
import json
import os
import re
import stat
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.secret_redactor import redact_text

_REPO_ROOT = Path(__file__).resolve().parents[2]


_NO_DELIVERABLE_UNKNOWN_COMMIT_COUNT_REASON = "commit_count_unknown"


_NO_DELIVERABLE_NO_COMMITS_REASON = "no_commits_no_changes"


_NO_DELIVERABLE_INVALID_DECLARATION_REASON = "invalid_delivery_declaration"


_NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON = "junk_only_worktree_changes"


_AUTO_FINALIZE_NOTHING_OWNED_REASON = "no_changes_under_owned_paths"


_AUTO_FINALIZE_NO_OWNED_PATHS_REASON = "no_owned_paths_declared"


_NO_DELIVERABLE_MISSING_REVIEW_VERDICT_REASON = "review_missing_verdict_line"


_REVIEW_UNSUPPORTED_VERDICT_REASON = "review_unsupported_verdict_token"


TYPED_CAUSE_CODES = frozenset(
    {
        "agy_model_identity_unverified",
        # Reading a Kimi worker's changes for the content check.
        "merge_base_unresolved",
        "temp_index_failed",
        "diff_command_failed",
        "changes_parse_failed",
        "file_unreadable",
        "changes_unreadable",
        "kimi_content_refused",
        # The worker-side Kimi admission and worktree boundary.
        "kimi_admission_refused",
        "kimi_worktree_mismatch",
        "review_admission_refused",
        "mechanical_admission_refused",
        "muse_worker_task_binding_refused",
        "boundary_remove_failed",
        "boundary_install_failed",
        # The worker's own outcome.
        "worker_failed",
        "worker_cancelled",
        "worker_timed_out",
        "worker_rate_limited",
        "worker_runtime_error",
        "worker_unexpected_error",
        "adapter_rejected",
        "runtime_returncode_missing",
        "read_only_checkout_mutation",
        "task_records_snapshot_failed",
        # Dispatch before the worker ran.
        "worktree_preparation_failed",
        "forward_configuration_failed",
        "dispatch_not_started",
        "worker_spawn_failed",
        "dispatch_isolation_failed",
        "dispatch_fallback_refused",
        # Finalize and auto-finalize.
        "finalize_failed",
        "interrupted_during_finalize",
        "finalize_skipped_paths",
        "auto_finalize_unsafe_branch",
        "auto_finalize_validation_changed",
        "auto_finalize_validation_unavailable",
        "auto_finalize_invalid_tree_path",
        "auto_finalize_fsck_failed",
        "auto_finalize_copy_timeout",
        "auto_finalize_object_hardening_violation",
        "auto_finalize_preparation_refused",
        "finalize_delivery_pending",
        "finalize_remote_unknown",
        "finalize_unpushed",
        "auto_finalize_dirty_unknown",
        "auto_finalize_changes_unknown",
        "auto_finalize_committed_scope_unknown",
        "auto_finalize_scope_check_timeout",
        "auto_finalize_committed_scope_unowned",
        "auto_finalize_remote_unknown",
        "auto_finalize_remote_unverified",
        "auto_finalize_head_moved",
        "auto_finalize_changes_remaining",
        "auto_finalize_unconfirmed",
        "auto_finalize_add_failed",
        "auto_finalize_commit_failed",
        "auto_finalize_push_failed",
        "auto_finalize_push_unexpected_ref",
        "auto_finalize_reset_failed",
        "auto_finalize_pr_failed",
        "auto_finalize_publish_blocked",
        "auto_finalize_opsec_blocked",
        "no_owned_paths_declared",
        "auto_finalize_failed",
        # Rescue.
        "rescue_worktree_unregistered",
        "rescue_tree_unavailable",
        "rescue_identity_unavailable",
        "rescue_commit_failed",
        "rescue_filtered_path",
        "rescue_embedded_repository",
        "rescue_new_gitlink",
        "rescue_input_unreadable",
        "rescue_input_changed",
        "rescue_push_url_unavailable",
        "rescue_push_failed",
        "rescue_remote_unverified",
        "rescue_step_failed",
        "remote_unreachable",
        # Review task records (``_review_task_failure_reason``) and the dead-worker settle.
        "read_only_checkout_snapshot_failed",
        "review_worker_not_started",
        "review_worker_returncode_missing",
        "review_worker_nonzero_exit",
        "review_worker_reported_failure",
        "worker_process_dead",
        "worktree_missing_at_settle",
    }
)


UNCLASSIFIED_CAUSE = "unclassified_error"


_PUBLIC_REASON_PHRASES = frozenset(
    {
        "activity probe unavailable",
        "ahead count unavailable",
        "already rescued at HEAD",
        "changed files unavailable",
        "clean disposable residue",
        "could not clean disposable residue",
        "disposable residue removed",
        "files exceed 5 MB",
        "HEAD unavailable",
        "invalid finished_at",
        "no finished_at",
        "no provable unpushed work",
        "no recorded worktree",
        "not a registered dispatch worktree",
        "rescue remote branch already exists at another head",
        "task attempt changed after rescue push; recovery ref preserved",
        "task is not terminal non-success",
        "task lease active",
        "task process alive",
        "task state changed",
        "unreadable task state",
        "worktree active",
        "worktree already removed",
        "worktree branch differs from task record",
        "worktree group has nonterminal task",
        "worktree group records disagree on branch",
        "worktree task inventory unavailable",
        "worktree dirty",
        "unpushed work - needs rescue",
        "unpushed state unknown - needs rescue",
        "rescued",
        "clean-tree",
        "not a git worktree",
        "move detection failed; nothing committed",
        "interrupted before the completion gates ran",
    }
)


PUBLIC_RECORD_REASON_FIELDS = (
    "last_error",
    "finalize_error",
    "incomplete_run_reason",
    "no_deliverable_reason",
    "failure_reason",
    "failure_code",
    "review_verdict_failure",
    "rescue_status",
    "kimi_content_refusal",
)


PUBLIC_RECORD_NESTED_REASON_FIELDS = (("auto_finalize", "error"), ("finalize_delivery", "reason"))


_PUBLIC_CAUSE_MAX_CHARS = 512


_PUBLIC_GIT_SUBCOMMANDS = frozenset(
    {
        "add", "am", "apply", "archive", "branch", "cat-file", "check-attr", "check-ignore", "check-ref-format",
        "checkout", "cherry-pick", "clean", "clone", "commit", "commit-tree", "config", "count-objects",
        "describe", "diff", "diff-files", "diff-index", "diff-tree", "fetch", "for-each-ref", "fsck", "gc",
        "hash-object", "init", "log", "ls-files", "ls-remote", "ls-tree", "merge", "merge-base", "mktree", "mv",
        "notes", "pack-refs", "prune", "pull", "push", "read-tree", "rebase", "reflog", "remote", "repack",
        "reset", "restore", "rev-list", "rev-parse", "rm", "show", "show-ref", "sparse-checkout", "stash",
        "status", "submodule", "switch", "symbolic-ref", "tag", "update-index", "update-ref", "var",
        "verify-commit", "worktree", "write-tree",
    }
)  # fmt: skip


_PUBLIC_ERROR_CLASS_RE = re.compile(
    r"[A-Z][A-Za-z0-9]{0,63}(?:Error|Exception|Exit|Interrupt|Expired|Refused|Unreadable|Blocked|Iteration|Warning)"
)


_PUBLIC_ERRNO_NAMES = frozenset(errno.errorcode.values())


_PUBLIC_INT_PARAM_RE = re.compile(r"(?:exit -?|count )\d{1,9}")


_GIT_SUBCOMMAND_RE = re.compile(r"[a-z][a-z-]{0,39}")


@functools.cache
def public_causes() -> frozenset[str]:
    """Every cause a public reason may name: the one closed registry (#9878).

    Delegate's own codes and phrases, the agent runtime's failure codes, AGY's
    incomplete-run reasons, the bounded-advisory refusal and gate codes, the
    exit-scan reasons, and the completion-gate and delivery causes.
    """
    from scripts.agent_runtime import bounded_advisory
    from scripts.agent_runtime.adapters.agy import AGY_INCOMPLETE_RUN_REASONS
    from scripts.agent_runtime.attempt_boundary import CLAUDE_ACCOUNT_REFUSAL_CODES
    from scripts.agent_runtime.failure_codes import RUNTIME_FAILURE_CODES
    from scripts.orchestration import worker_leftovers

    advisory = {
        getattr(bounded_advisory, name)
        for name in (
            "ENVELOPE_REQUIRED", "FLAG_CONFLICT", "TASK_NOT_FOUND", "TASK_NOT_DONE", "TASK_WRONG_MODEL",
            "TASK_WRONG_ROLE", "RESULT_UNREADABLE", "ENVELOPE_MISSING", "ENVELOPE_INCOMPLETE",
            "OWNED_PATHS_INVALID", "BINDING_MISMATCH", "OWNED_PATHS_MISMATCH", "ENVELOPE_CHANGED", "SEAL_MISSING",
            "SEAL_MISMATCH", "ADMISSION_MISSING", "ADMISSION_INVALID", "ADVISOR_ROUTE_REFUSED",
            "EXECUTION_MISMATCH", "CEILING_EXCEEDED", "CEILING_UNMEASURED", "EXEMPT_CODE_CHANGE",
            "EXEMPT_CHANGES_UNMEASURED", "DRIVER_BRIEF_REFUSED",
        )
        if isinstance(getattr(bounded_advisory, name, None), str)
    }  # fmt: skip
    delegate_causes = {
        _NO_DELIVERABLE_UNKNOWN_COMMIT_COUNT_REASON,
        _NO_DELIVERABLE_NO_COMMITS_REASON,
        _NO_DELIVERABLE_INVALID_DECLARATION_REASON,
        _NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON,
        _NO_DELIVERABLE_MISSING_REVIEW_VERDICT_REASON,
        _REVIEW_UNSUPPORTED_VERDICT_REASON,
        _AUTO_FINALIZE_NOTHING_OWNED_REASON,
        _AUTO_FINALIZE_NO_OWNED_PATHS_REASON,
        COMPLETION_GATE_RESPONSE_UNAVAILABLE,
        RECOVERY_REQUIRES_RERUN,
        _INTERRUPTED_BEFORE_COMPLETION_GATES,
        worker_leftovers.BACKGROUND_JOBS_REASON,
        worker_leftovers.SCAN_UNKNOWN_REASON,
        UNCLASSIFIED_CAUSE,
    }
    return frozenset(
        TYPED_CAUSE_CODES
        | _PUBLIC_REASON_PHRASES
        | RUNTIME_FAILURE_CODES
        | frozenset(AGY_INCOMPLETE_RUN_REASONS)
        | advisory
        | CLAUDE_ACCOUNT_REFUSAL_CODES
        | delegate_causes
    )


def _is_public_error(text: str) -> bool:
    """An exception class, optionally with its errno name: ``OSError EACCES``."""
    error_class, _, errno_name = text.partition(" ")
    return bool(_PUBLIC_ERROR_CLASS_RE.fullmatch(error_class)) and (not errno_name or errno_name in _PUBLIC_ERRNO_NAMES)


def _is_public_param(text: str) -> bool:
    """One fixed parameter: ``git <known subcommand>``, ``exit <n>``, ``count <n>``, or ``<ErrorClass>[ <ERRNO>]``."""
    if text.startswith("git "):
        return text[4:] in _PUBLIC_GIT_SUBCOMMANDS
    return bool(_PUBLIC_INT_PARAM_RE.fullmatch(text)) or _is_public_error(text)


def _is_public_item(text: str) -> bool:
    """A registered cause, alone or followed by fixed parameters (``cause, git push, exit 1``)."""
    if text in public_causes():
        return True
    cause, *params = text.split(", ")
    return cause in public_causes() and bool(params) and all(_is_public_param(param) for param in params)


def is_public_cause(value: object) -> bool:
    """Whether ``value`` may be published as it is: registered causes with fixed parameters, joined by ``; ``."""
    if not isinstance(value, str) or not value or len(value) > _PUBLIC_CAUSE_MAX_CHARS:
        return False
    return value in public_causes() or all(_is_public_item(item) for item in value.split("; "))


@dataclass(frozen=True)
class _TypedCause:
    """Why a refusal, rescue step or worker failed, in a form that may leave the machine (#9878).

    :meth:`public` renders only registered parts: the code (one of
    :func:`public_causes`), a known git subcommand, the exit status, a count
    and the exception class. ``path`` and ``diagnostic`` (the raw stderr or
    exception text) go only to the task's local diagnostic file.
    """

    code: str
    command: str | None = None
    exit_status: int | None = None
    error: str | None = None
    path: str | None = None
    count: int | None = None
    diagnostic: str = dataclasses.field(default="", compare=False, repr=False)
    missing: tuple[str, ...] = ()

    def public(self) -> str:
        parts = [self.code if self.code in public_causes() else UNCLASSIFIED_CAUSE]
        if self.command in _PUBLIC_GIT_SUBCOMMANDS:
            parts.append(f"git {self.command}")
        for label, number in (("exit", self.exit_status), ("count", self.count)):
            if isinstance(number, int) and not isinstance(number, bool) and abs(number) < 10**9:
                parts.append(f"{label} {number}")
        if self.error and _is_public_error(self.error):
            parts.append(self.error)
        return ", ".join(parts)


def public_cause(value: object) -> tuple[str | None, _TypedCause | None]:
    """The sink every public reason is written through: ``(public text, cause to record locally)`` (#9878).

    A :class:`_TypedCause` renders its public form. A string that is already
    a public cause (:func:`is_public_cause`) passes unchanged with nothing to
    record. Anything else (free text, an exception, another type) is replaced
    item by item with :data:`UNCLASSIFIED_CAUSE` (an exception keeps its class)
    and returned as the cause whose raw text the caller records in the task's
    local diagnostic file. Pure: it writes nothing.
    """
    if value is None:
        return None, None
    if isinstance(value, _TypedCause):
        return value.public(), value
    if isinstance(value, BaseException):
        cause = _exception_cause(UNCLASSIFIED_CAUSE, value)
        return cause.public(), cause
    if isinstance(value, str):
        if not value or is_public_cause(value):
            return value, None
        kept: list[str] = []
        for item in value.split("; "):
            public = item if _is_public_item(item) else UNCLASSIFIED_CAUSE
            if public not in kept:
                kept.append(public)
        text = "; ".join(kept)
        return (text if len(text) <= _PUBLIC_CAUSE_MAX_CHARS else UNCLASSIFIED_CAUSE), _TypedCause(
            UNCLASSIFIED_CAUSE, diagnostic=value
        )
    return UNCLASSIFIED_CAUSE, _TypedCause(UNCLASSIFIED_CAUSE, diagnostic=f"{type(value).__name__}: {value!r}")


def _public_record(state: Mapping[str, Any]) -> tuple[dict[str, Any], list[tuple[str, _TypedCause]]]:
    """``state`` with every public reason field through :func:`public_cause`, and the ``(field, cause)`` to record."""
    public = dict(state)
    recorded: list[tuple[str, _TypedCause]] = []
    for field in PUBLIC_RECORD_REASON_FIELDS:
        if field in public:
            public[field], cause = public_cause(public[field])
            if cause is not None:
                recorded.append((field, cause))
    for parent, key in PUBLIC_RECORD_NESTED_REASON_FIELDS:
        nested = public.get(parent)
        if isinstance(nested, Mapping) and key in nested:
            text, cause = public_cause(nested[key])
            public[parent] = {**nested, key: text}
            if cause is not None:
                recorded.append((f"{parent}.{key}", cause))
    return public, recorded


def _git_subcommand(args: Sequence[str] | str | None) -> str | None:
    """The subcommand of a ``git [options] <subcommand> ...`` argv, skipping global options and their values."""
    if not isinstance(args, (list, tuple)):
        return None
    words = [str(arg) for arg in args]
    index = 1 if words and Path(words[0]).name == "git" else 0
    while index < len(words):
        word = words[index]
        if word in ("-c", "-C"):
            index += 2
            continue
        if word.startswith("-"):
            index += 1
            continue
        return word if _GIT_SUBCOMMAND_RE.fullmatch(word) else None
    return None


def _exception_cause(
    code: str, exc: BaseException, *, command: Sequence[str] | None = None, path: str | None = None
) -> _TypedCause:
    """An exception as a :class:`_TypedCause`: its class (and errno name) public, its message local."""
    if isinstance(exc, _TypedFailure):
        return exc.cause
    errno_name = errno.errorcode.get(exc.errno, "") if isinstance(exc, OSError) and isinstance(exc.errno, int) else ""
    step = f"{' '.join(command)} " if command else ""
    return _TypedCause(
        code,
        command=_git_subcommand(list(command)) if command else None,
        error=f"{type(exc).__name__}{f' {errno_name}' if errno_name else ''}",
        path=path,
        diagnostic=f"{step}raised {type(exc).__name__}: {exc}",
    )


class _TypedFailure(RuntimeError):
    """A step failed with a :class:`_TypedCause`: ``str()`` is its public form, never the raw error (#9878).

    ``message`` is a literal for the local diagnostic; nothing read from git,
    the remote or the host enters the public form.
    """

    def __init__(self, message: str, cause: _TypedCause) -> None:
        super().__init__(cause.public())
        self.message = message
        self.cause = dataclasses.replace(
            cause, diagnostic=f"{message}: {cause.diagnostic}" if cause.diagnostic else message
        )

    @property
    def code(self) -> str:
        return self.cause.code


_DIAG_MAX_ENTRY_BYTES = 4096


_DIAG_MAX_FILE_BYTES = 256 * 1024


_DIAG_ROTATED_SUFFIX = ".prev"


_DIAG_TRUNCATED = "…[truncated]"


def _diagnostic_line(source: str, field: str, cause: _TypedCause) -> bytes:
    """One JSON line of at most :data:`_DIAG_MAX_ENTRY_BYTES`: the raw text secret-redacted, cut to fit."""
    diagnostic = redact_text(cause.diagnostic) or ""
    path = (redact_text(cause.path) or "")[:512] if cause.path else None

    def encode(text: str) -> bytes:
        entry = {
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": source[:64],
            "field": field[:64],
            "code": cause.code[:64],
            "public": cause.public(),
            **({"missing": list(cause.missing)} if cause.missing else {}),
            **({"path": path} if path else {}),
            "diagnostic": text,
        }
        return (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8")

    line = encode(diagnostic)
    if len(line) <= _DIAG_MAX_ENTRY_BYTES:
        return line
    # The longest prefix that fits, in encoded bytes (escapes and multi-byte characters included).
    low, high = 0, min(len(diagnostic), _DIAG_MAX_ENTRY_BYTES)
    while low < high:
        middle = (low + high + 1) // 2
        if len(encode(diagnostic[:middle] + _DIAG_TRUNCATED)) <= _DIAG_MAX_ENTRY_BYTES:
            low = middle
        else:
            high = middle - 1
    return encode(diagnostic[:low] + _DIAG_TRUNCATED)


def _open_diagnostic(directory_fd: int, name: str, flags: int = os.O_RDWR | os.O_APPEND | os.O_CREAT) -> int:
    """Open ``name`` in the trusted task directory: no symlink, a private regular file of ours, made 0600."""
    fd = os.open(name, flags | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, 0o600, dir_fd=directory_fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1:
            raise OSError(errno.EPERM, "diagnostic file is not a private regular file")
        if stat.S_IMODE(info.st_mode) != 0o600:
            os.fchmod(fd, 0o600)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _newest_lines(data: bytes, limit: int) -> bytes:
    """The newest whole lines of ``data`` that fit in ``limit`` bytes."""
    if len(data) <= limit:
        return data
    tail = data[len(data) - limit :]
    return tail if data[len(data) - limit - 1 : len(data) - limit] == b"\n" else tail.partition(b"\n")[2]


def _bound_diagnostic_fd(fd: int) -> None:
    """Cut the locked diagnostic file ``fd`` to its newest lines within :data:`_DIAG_MAX_FILE_BYTES`."""
    size = os.fstat(fd).st_size
    if size <= _DIAG_MAX_FILE_BYTES:
        return
    kept = _newest_lines(os.pread(fd, _DIAG_MAX_FILE_BYTES + 1, size - _DIAG_MAX_FILE_BYTES - 1), _DIAG_MAX_FILE_BYTES)
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    view = memoryview(kept)
    while view:
        view = view[os.write(fd, view) :]


def _bound_rotated_diagnostic(directory_fd: int, name: str) -> None:
    """Bring the rotated generation ``name`` within :data:`_DIAG_MAX_FILE_BYTES` and 0600, keeping its newest lines.

    A name that is not a private regular file of ours (a symlink, a hard
    link, another owner's file) is unlinked: the name alone goes, never what
    it points at. The caller holds the lock on the current diagnostic file;
    this one is locked too, against the writer that rotated it.
    """
    try:
        fd = _open_diagnostic(directory_fd, name, os.O_RDWR)
    except FileNotFoundError:
        return
    except OSError:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name, dir_fd=directory_fd)
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        _bound_diagnostic_fd(fd)
    finally:
        os.close(fd)


def _append_diagnostics(record_path: Path, causes: Sequence[tuple[str, _TypedCause]], *, source: str) -> str | None:
    """Append each ``(field, cause)`` with its raw text to the record's local ``.diag`` file (#9878).

    Writes only beside an existing task record, so a refused worker still
    leaves no task file behind. The task directory is opened without following
    a symlink and each file through it, never following one either, created
    0600 and refused unless it is a private regular file with one link.
    Entries are bounded (:data:`_DIAG_MAX_ENTRY_BYTES`). Each file is
    unconditionally bounded (:data:`_DIAG_MAX_FILE_BYTES`) and 0600: an
    oversized ``.diag`` rotates, and before every append the rotated
    ``.diag.prev`` is cut to its newest lines and made private, so neither a
    pre-existing oversized file nor a rotation leaves one over the limit.
    Returns the file's repository-relative path for a row to point at, or
    None when nothing was written; a write error never hides the failure
    being recorded.
    """
    if not causes:
        return None
    data = _newest_lines(
        b"".join(_diagnostic_line(source, field, cause) for field, cause in causes), _DIAG_MAX_FILE_BYTES
    )
    name = record_path.with_suffix(".diag").name
    try:
        directory_fd = os.open(record_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError:
        return None
    fd: int | None = None
    try:
        if not stat.S_ISREG(os.stat(record_path.name, dir_fd=directory_fd, follow_symlinks=False).st_mode):
            return None
        for _attempt in range(3):
            fd = _open_diagnostic(directory_fd, name)
            fcntl.flock(fd, fcntl.LOCK_EX)
            # Another writer may have rotated the file between our open and lock.
            if os.stat(name, dir_fd=directory_fd, follow_symlinks=False).st_ino != os.fstat(fd).st_ino:
                os.close(fd)
                fd = None
                continue
            if os.fstat(fd).st_size + len(data) > _DIAG_MAX_FILE_BYTES:
                os.replace(name, name + _DIAG_ROTATED_SUFFIX, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
                _bound_diagnostic_fd(fd)  # the rotated copy, still locked: never left over the limit
                os.close(fd)
                fd = None
                continue
            _bound_rotated_diagnostic(directory_fd, name + _DIAG_ROTATED_SUFFIX)
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view) :]
            break
        else:
            return None
    except OSError:
        return None
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory_fd)
    path = record_path.with_suffix(".diag")
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return f"{path.parent.name}/{path.name}"


_INTERRUPTED_BEFORE_COMPLETION_GATES = "interrupted before the completion gates ran"


COMPLETION_GATE_RESPONSE_UNAVAILABLE = "completion_gate_response_unavailable"


RECOVERY_REQUIRES_RERUN = "recovery_requires_rerun"
