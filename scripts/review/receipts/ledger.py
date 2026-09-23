"""Append-only local ledger of one review attempt's sources calls.

Activated by the three environment variables below, which the dispatch sets
on the sources MCP process. The file layout is
``batch_state/review-receipts/<review_id>/<attempt_id>.jsonl`` plus a
``<attempt_id>.jsonl.sha256`` sidecar. ``LU_REVIEW_LEDGER_PATH`` is that
jsonl path; the review id is the parent directory name and must equal the
attempt id's sibling stem.

Writes replace the whole file atomically and only by appending one JSON
line. File mode is 0o600. Snapshot hashes come from
``Sources._fingerprint`` (sources.db), ``Sources._vesum_identity`` (VESUM
build metadata), and ``stress.source_info`` (the trie digest).
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.curriculum.evidence.lock import atomic_write

ENV_ATTEMPT_ID = "LU_REVIEW_ATTEMPT_ID"
ENV_MANIFEST_SHA256 = "LU_REVIEW_MANIFEST_SHA256"
ENV_LEDGER_PATH = "LU_REVIEW_LEDGER_PATH"
ENV_KEYS = (ENV_ATTEMPT_ID, ENV_MANIFEST_SHA256, ENV_LEDGER_PATH)

# Principle 4a of the review contract. A call to any other tool is refused.
REVIEW_TOOLS = frozenset(
    {
        "verify_words",
        "inspect_word",
        "inspect_words",
        "verify_stress",
        "query_sum20",
        "query_ulif",
        "query_pravopys",
        "search_style_guide",
        "search_text",
        "query_r2u",
        "search_heritage",
        "check_russian_shadow",
        "search_ua_gec_errors",
        "query_grac",
        "query_cefr_level",
        "verify_quote",
    }
)

_TOKEN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
_LOCK = threading.Lock()
_DEFAULT_SOURCES: Any = None
_DEFAULT_SNAPSHOTS: dict[str, Any] | None = None


class LedgerError(Exception):
    """The ledger file, its sidecar, or the recording environment is unusable."""


class ReceiptNotFound(LedgerError):
    """``lookup`` did not find this receipt id in a readable ledger."""


class LedgerHashStaleLastLine(LedgerError):
    """The sidecar matches the ledger minus its last complete line (crash recovery state)."""


@contextmanager
def _flock_path(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_APPEND, 0o600)
    try:
        os.fchmod(fd, 0o600)
    except BaseException:
        os.close(fd)
        raise
    with open(fd, "a") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _token(value: str) -> bool:
    return bool(re.fullmatch(_TOKEN, value))


def _sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def dumps(record: dict[str, Any]) -> str:
    """One canonical JSON object, UTF-8, stable key order."""
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def freeze_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """JSON-stable copy of the arguments the handler will see."""
    return json.loads(dumps(arguments))


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".sha256")


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_verified(path: Path, *, allow_missing: bool = False) -> bytes:
    """Return ledger bytes, or b'' when allow_missing=True and the file is not yet created.

    A missing ledger without allow_missing=True raises LedgerError.
    A present file whose sidecar is missing or different is refused, reporting
    LedgerHashStaleLastLine if the hash matches the ledger minus its last complete line.
    """
    path = Path(path)
    if not path.exists():
        if _sidecar(path).exists():
            raise LedgerError(f"sidecar without ledger: {path}")
        if allow_missing:
            return b""
        raise LedgerError(f"ledger missing: {path}")
    content = path.read_bytes()
    side = _sidecar(path)
    if not side.is_file():
        raise LedgerError(f"ledger sidecar missing: {side}")
    recorded = side.read_text(encoding="ascii")
    expected_digest = _digest(content) + "\n"
    if recorded != expected_digest:
        if content.endswith(b"\n"):
            prev_newline = content.rfind(b"\n", 0, -1)
            content_minus_last = content[: prev_newline + 1] if prev_newline != -1 else b""
            if recorded == _digest(content_minus_last) + "\n":
                raise LedgerHashStaleLastLine(f"ledger hash stale by last line: {side}")
        raise LedgerError(f"ledger sidecar mismatch: {side}")
    return content


def _write_verified(path: Path, content: bytes) -> None:
    atomic_write(path, content)
    atomic_write(_sidecar(path), (_digest(content) + "\n").encode("ascii"))
    for target in (path, _sidecar(path)):
        if (target.stat().st_mode & 0o777) != 0o600:
            os.chmod(target, 0o600)


def create_empty_ledger(path: Path | str) -> Path:
    """Create an empty ledger file (0 bytes) and its .sha256 sidecar.

    Sets permissions to 0o600.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    _write_verified(target, b"")
    return target


def append(
    ledger_path: Path,
    *,
    review_id: str,
    attempt_id: str,
    manifest_sha256: str,
    tool: str,
    server_version: str,
    arguments: dict[str, Any],
    snapshots: dict[str, Any],
    status: str,
    result: str,
    outcome_facts: dict[str, Any] | None = None,
) -> str:
    """Append one call and return its receipt id. The result text is stored whole."""
    if status not in {"ok", "error", "refused"}:
        raise LedgerError(f"status {status!r} is not ok, error, or refused")
    if not isinstance(result, str):
        raise LedgerError("result must be a string")
    if not _token(review_id) or not _token(attempt_id) or not _sha256(manifest_sha256):
        raise LedgerError("review id, attempt id, or manifest hash is malformed")
    if outcome_facts is None:
        from scripts.review.receipts.outcomes import classify_outcome

        outcome_facts = classify_outcome(tool, status, result)
    path = Path(ledger_path)
    lock_path = path.with_name(path.name + ".lock")
    with _LOCK, _flock_path(lock_path):
        existing = _read_verified(path, allow_missing=True)
        if existing and not existing.endswith(b"\n"):
            raise LedgerError(f"ledger {path} does not end in a newline")
        seq = existing.count(b"\n") + 1
        body = {
            "arguments": arguments,
            "attempt_id": attempt_id,
            "manifest_sha256": manifest_sha256,
            "outcome_facts": outcome_facts,
            "result": result,
            "review_id": review_id,
            "seq": seq,
            "server_version": server_version,
            "snapshots": snapshots,
            "status": status,
            "tool": tool,
        }
        receipt_id = "rr-" + hashlib.sha256(dumps(body).encode("utf-8")).hexdigest()[:20]
        record = {**body, "receipt_id": receipt_id}
        line = dumps(record).encode("utf-8") + b"\n"
        updated = existing + line
        if not updated.startswith(existing):
            raise LedgerError("append would rewrite earlier ledger bytes")
        _write_verified(path, updated)
        return receipt_id


def records(ledger_path: Path) -> list[dict[str, Any]]:
    """Return every record. A missing file is an empty ledger; a bad sidecar is an error."""
    content = _read_verified(Path(ledger_path))
    found: list[dict[str, Any]] = []
    for raw in content.splitlines():
        if not raw:
            continue
        record = json.loads(raw)
        if not isinstance(record, dict):
            raise LedgerError(f"ledger line is not an object: {ledger_path}")
        found.append(record)
    return found


def lookup(ledger_path: Path, receipt_id: str) -> dict[str, Any]:
    """Return the record for ``receipt_id``. Raises ``ReceiptNotFound`` when it is absent."""
    for record in records(ledger_path):
        if record.get("receipt_id") == receipt_id:
            return record
    raise ReceiptNotFound(f"receipt {receipt_id!r} is not in {ledger_path}")


def collect_snapshots(*, sources: Any = None, trie_digest: str | None = None) -> dict[str, Any]:
    """Local snapshot hashes. Default arguments use the process-wide Sources session.

    ``sources`` and ``trie_digest`` exist so tests can hash fixture files
    without opening the live databases or the stress trie. Only the no-argument
    call is cached.
    """
    global _DEFAULT_SNAPSHOTS
    use_default = sources is None and trie_digest is None
    if use_default and _DEFAULT_SNAPSHOTS is not None:
        return json.loads(dumps(_DEFAULT_SNAPSHOTS))
    if sources is None:
        sources = _default_sources()
    db_digest, db_meta = sources._fingerprint(sources.sources_db)
    vesum_digest, vesum_meta = sources._vesum_identity()
    if trie_digest is None:
        from scripts.verification.stress import source_info

        trie_digest = str(source_info()["digest"])
    snapshot = {
        "sources_db": {"digest": db_digest, "metadata": dict(db_meta)},
        "vesum": {"digest": vesum_digest, "metadata": dict(vesum_meta)},
        "trie": {"digest": trie_digest},
    }
    if use_default:
        _DEFAULT_SNAPSHOTS = snapshot
    return snapshot


def _default_sources() -> Any:
    global _DEFAULT_SOURCES
    if _DEFAULT_SOURCES is None:
        from scripts.curriculum.evidence.sources import Sources

        _DEFAULT_SOURCES = Sources()
    return _DEFAULT_SOURCES


@dataclass(frozen=True)
class ReviewSession:
    """One review attempt bound to a ledger path."""

    mode: str
    review_id: str
    attempt_id: str
    manifest_sha256: str
    ledger_path: Path
    error: str = ""

    def record(
        self,
        *,
        tool: str,
        arguments: dict[str, Any],
        status: str,
        result: str,
        server_version: str,
        outcome_facts: dict[str, Any] | None = None,
    ) -> str:
        if self.mode != "on":
            raise LedgerError(self.error or "review recording is not configured")
        try:
            snapshots = collect_snapshots()
        except Exception as exc:
            snapshots = {"error": type(exc).__name__}
        return append(
            self.ledger_path,
            review_id=self.review_id,
            attempt_id=self.attempt_id,
            manifest_sha256=self.manifest_sha256,
            tool=tool,
            server_version=server_version,
            arguments=arguments,
            snapshots=snapshots,
            status=status,
            result=result,
            outcome_facts=outcome_facts,
        )


def session_from_environ(environ: Any = None) -> ReviewSession | None:
    """Return a session when any review variable is set, or None when all are unset.

    A partial or malformed set is ``mode='incomplete'`` so the server can
    refuse the call instead of running a tool it cannot record.
    """
    env = os.environ if environ is None else environ
    values = {key: str(env.get(key, "") or "").strip() for key in ENV_KEYS}
    if not any(values.values()):
        return None
    missing = [key for key, value in values.items() if not value]
    attempt_id = values[ENV_ATTEMPT_ID]
    manifest = values[ENV_MANIFEST_SHA256]
    raw_path = values[ENV_LEDGER_PATH]
    problems: list[str] = []
    if missing:
        problems.append("missing " + ", ".join(missing))
    if attempt_id and not _token(attempt_id):
        problems.append("attempt id is not a token")
    if manifest and not _sha256(manifest):
        problems.append("manifest hash is not 64 lowercase hex characters")
    review_id = ""
    ledger_path = Path(raw_path) if raw_path else Path(".")
    if raw_path:
        if ledger_path.name != f"{attempt_id}.jsonl":
            problems.append("ledger filename must be <attempt_id>.jsonl")
        review_id = ledger_path.parent.name
        if not _token(review_id):
            problems.append("ledger parent directory must be the review id")
    if problems:
        return ReviewSession(
            "incomplete",
            review_id or "unset",
            attempt_id or "unset",
            manifest,
            ledger_path,
            "; ".join(problems),
        )
    return ReviewSession("on", review_id, attempt_id, manifest, ledger_path)
