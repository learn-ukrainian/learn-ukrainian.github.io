"""Exact-target evidence verification for structured code-review findings.

Bound to :class:`scripts.review.target_resolution.ReviewTarget`. Verifies
verbatim quotes with **line-ending normalization only** — no backtick
stripping, no whitespace collapsing, no punctuation removal. Path safety
rejects absolute paths, drive paths, ``..``, symlink escapes, and locations
outside the reviewed target / changed surface.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from scripts.common.git_context import sanitized_git_env
from scripts.review.target_resolution import ReviewTarget

# Outcomes preserved as distinct classes (issue #5284).
OUTCOME_VERIFIED = "verified"
OUTCOME_LINE_MISMATCH = "line_mismatch"
OUTCOME_QUOTE_MISSING = "quote_missing"
OUTCOME_MALFORMED = "malformed"
OUTCOME_OUT_OF_SCOPE = "out_of_scope"

EVIDENCE_OUTCOMES = frozenset(
    {
        OUTCOME_VERIFIED,
        OUTCOME_LINE_MISMATCH,
        OUTCOME_QUOTE_MISSING,
        OUTCOME_MALFORMED,
        OUTCOME_OUT_OF_SCOPE,
    }
)

_DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:")
_HUNK_RE = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@")

TARGET_INPUT_FINGERPRINT_VERSION = "target-input-v1"


class EvidenceError(RuntimeError):
    """Evidence loading or path resolution failed closed."""


@dataclass(frozen=True)
class EvidenceCheckResult:
    outcome: str
    matched_line: int | None = None
    matched_text: str | None = None
    detail: str = ""


def normalize_line_endings(text: str) -> str:
    """Documented normalization: CRLF/CR → LF only. Nothing else."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_lines_preserve_content(text: str) -> list[str]:
    """Split on LF after line-ending normalization. Keep empty lines; no strip."""
    normalized = normalize_line_endings(text)
    if normalized == "":
        return []
    # splitlines(keepends=False) drops a trailing empty segment after final \n,
    # which matches how editors present "lines of a file."
    if normalized.endswith("\n"):
        normalized = normalized[:-1]
    return normalized.split("\n")


def is_safe_repo_relative_path(path: str) -> bool:
    """Structural path-string check (no filesystem I/O)."""
    if not path or not isinstance(path, str):
        return False
    if path.startswith(("/", "\\")):
        return False
    if _DRIVE_PATH_RE.match(path):
        return False
    if "\\" in path:
        return False
    parts = path.split("/")
    return not any(p in ("", ".", "..") for p in parts)


def resolve_safe_path(repo_root: Path, rel_path: str) -> Path:
    """Resolve ``rel_path`` under ``repo_root``; reject escapes and symlink walks out."""
    if not is_safe_repo_relative_path(rel_path):
        raise EvidenceError(f"unsafe_path:{rel_path!r}")
    root = repo_root.resolve()
    candidate = (root / rel_path).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EvidenceError(f"path_escapes_repo:{rel_path!r}") from exc
    # If the path exists and is a symlink, ensure the real file is still in-repo.
    if candidate.exists() or candidate.is_symlink():
        real = candidate.resolve(strict=False)
        try:
            real.relative_to(root)
        except ValueError as exc:
            raise EvidenceError(f"symlink_escape:{rel_path!r}") from exc
        return real
    return candidate


def _run_git(args: list[str], cwd: Path, *, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=sanitized_git_env(),
    )


def _run_git_bytes(
    args: list[str], cwd: Path, *, timeout: float = 30.0
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        timeout=timeout,
        env=sanitized_git_env(),
    )


def load_file_text(repo_root: Path, rel_path: str, target: ReviewTarget) -> str:
    """Load file content from the exact review target (local tree or head SHA)."""
    safe = resolve_safe_path(repo_root, rel_path)
    if target.mode == "local":
        if not safe.is_file():
            raise EvidenceError(f"file_unavailable:{rel_path}")
        try:
            return safe.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise EvidenceError(f"decode_failed:{rel_path}") from exc
        except OSError as exc:
            raise EvidenceError(f"read_failed:{rel_path}:{exc}") from exc
    if not target.head_sha:
        raise EvidenceError("target_missing_head_sha")
    # git path uses the repo-relative form, not the resolved real path.
    proc = _run_git(["show", f"{target.head_sha}:{rel_path}"], repo_root)
    if proc.returncode != 0:
        raise EvidenceError(f"file_unavailable:{rel_path}:{proc.stderr.strip()}")
    return proc.stdout


def _parse_new_side_lines(diff_text: str) -> set[int]:
    """Parse ``git diff -U0`` unified diff for new-side line numbers."""
    lines: set[int] = set()
    current: int | None = None
    remaining = 0
    for raw in diff_text.splitlines():
        hunk = _HUNK_RE.match(raw)
        if hunk:
            start = int(hunk.group(1))
            count = int(hunk.group(2) or "1")
            current = start
            remaining = count
            if count == 0:
                current = None
            continue
        if current is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            lines.add(current)
            current += 1
            remaining -= 1
            if remaining <= 0:
                current = None
        elif (raw.startswith("-") and not raw.startswith("---")) or raw.startswith("\\"):
            continue
        else:
            # context (shouldn't appear with -U0) or noise
            if remaining > 0 and not raw.startswith(("+", "-", "@")):
                current += 1
                remaining -= 1
                if remaining <= 0:
                    current = None
    return lines


def changed_lines_map(repo_root: Path, target: ReviewTarget) -> dict[str, set[int]]:
    """Map each changed path to the set of new-side line numbers introduced/altered.

    Untracked files in local mode: every line is treated as changed.
    """
    result: dict[str, set[int]] = {p: set() for p in target.changed_paths}
    if target.mode == "local":
        for path in target.changed_paths:
            full = resolve_safe_path(repo_root, path)
            # Untracked?
            status = _run_git(["status", "--porcelain", "--", path], repo_root)
            status_line = (status.stdout or "").strip()
            if status_line.startswith("??"):
                if full.is_file():
                    try:
                        text = full.read_text(encoding="utf-8")
                    except (UnicodeDecodeError, OSError):
                        # Fail closed for line accounting: empty set means present
                        # claims cannot invent a verified changed line.
                        result[path] = set()
                        continue
                    n = len(split_lines_preserve_content(text))
                    result[path] = set(range(1, n + 1)) if n else set()
                continue
            # Tracked working-tree changes (staged + unstaged) vs HEAD.
            proc = _run_git(["diff", "-U0", "HEAD", "--", path], repo_root)
            result[path] |= _parse_new_side_lines(proc.stdout or "")
            cached = _run_git(["diff", "-U0", "--cached", "HEAD", "--", path], repo_root)
            result[path] |= _parse_new_side_lines(cached.stdout or "")
        return result

    if not target.base_sha or not target.head_sha:
        raise EvidenceError("target_missing_base_or_head_for_changed_lines")
    for path in target.changed_paths:
        proc = _run_git(
            ["diff", "-U0", target.base_sha, target.head_sha, "--", path],
            repo_root,
        )
        if proc.returncode != 0:
            raise EvidenceError(f"diff_failed:{path}:{proc.stderr.strip()}")
        result[path] = _parse_new_side_lines(proc.stdout or "")
    return result


def path_surface_bytes(repo_root: Path, target: ReviewTarget, rel_path: str) -> bytes:
    """Exact patch or untracked file bytes for one path on the reviewed surface."""
    if not is_safe_repo_relative_path(rel_path):
        raise EvidenceError(f"unsafe_path:{rel_path!r}")
    if target.mode == "local":
        status = _run_git(["status", "--porcelain", "--", rel_path], repo_root)
        status_line = (status.stdout or "").strip()
        if status_line.startswith("??"):
            safe = resolve_safe_path(repo_root, rel_path)
            if not safe.is_file():
                raise EvidenceError(f"file_unavailable:{rel_path}")
            try:
                return safe.read_bytes()
            except OSError as exc:
                raise EvidenceError(f"read_failed:{rel_path}:{exc}") from exc
        # Working tree vs HEAD (staged + unstaged combined).
        proc = _run_git_bytes(["diff", "HEAD", "--", rel_path], repo_root)
        if proc.returncode not in (0, 1):
            err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
            raise EvidenceError(f"diff_failed:{rel_path}:{err}")
        return proc.stdout or b""

    if not target.base_sha or not target.head_sha:
        raise EvidenceError("target_missing_base_or_head_for_fingerprint")
    proc = _run_git_bytes(
        ["diff", target.base_sha, target.head_sha, "--", rel_path],
        repo_root,
    )
    if proc.returncode not in (0, 1):
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        raise EvidenceError(f"diff_failed:{rel_path}:{err}")
    return proc.stdout or b""


def compute_target_input_fingerprint(repo_root: Path, target: ReviewTarget) -> str:
    """Deterministic SHA-256 of target metadata plus exact patch/untracked bytes.

    Identifies the validated review target/bundle (not reviewer JSON). Changes
    when local sources, the changed-path set, base/head, or committed content
    change.
    """
    working_tree_head = ""
    if target.mode == "local":
        head_proc = _run_git(["rev-parse", "HEAD"], repo_root)
        if head_proc.returncode == 0:
            working_tree_head = (head_proc.stdout or "").strip()

    meta = {
        "fingerprint_version": TARGET_INPUT_FINGERPRINT_VERSION,
        "mode": target.mode,
        "base_sha": target.base_sha or "",
        "head_sha": target.head_sha or "",
        "working_tree_head": working_tree_head,
        "changed_paths": list(target.changed_paths),
        "non_test_loc": target.non_test_loc,
        "clean_tree": target.clean_tree,
        "description": target.description,
    }
    hasher = hashlib.sha256()
    hasher.update(TARGET_INPUT_FINGERPRINT_VERSION.encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(
        json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    for path in target.changed_paths:
        surface = path_surface_bytes(repo_root, target, path)
        hasher.update(b"\0path:")
        hasher.update(path.encode("utf-8"))
        hasher.update(b"\0len:")
        hasher.update(f"{len(surface)}".encode("ascii"))
        hasher.update(b"\0")
        hasher.update(surface)
    return hasher.hexdigest()


def build_target_manifest(repo_root: Path, target: ReviewTarget) -> dict:
    """Source-blind capture of head + target-input fingerprint before review."""
    input_sha256 = compute_target_input_fingerprint(repo_root, target)
    return {
        "schema_version": "code-review-target-manifest.v1",
        "mode": target.mode,
        "base_sha": target.base_sha,
        "head_sha": target.head_sha,
        "changed_paths": list(target.changed_paths),
        "non_test_loc": target.non_test_loc,
        "clean_tree": target.clean_tree,
        "description": target.description,
        "input_sha256": input_sha256,
    }


def find_verbatim_match(
    file_text: str, quote: str
) -> tuple[int | None, str | None]:
    """Return (1-based start line, matched text) of the first contiguous match.

    Matching uses line-ending normalization only. First match is deterministic
    for reporting an alternate location when the claimed range does not match.
    """
    file_lines = split_lines_preserve_content(file_text)
    quote_lines = split_lines_preserve_content(quote)
    if not quote_lines:
        return None, None
    n = len(quote_lines)
    for i in range(0, len(file_lines) - n + 1):
        window = file_lines[i : i + n]
        if window == quote_lines:
            matched = "\n".join(window)
            return i + 1, matched
    return None, None


def match_at_line(file_text: str, quote: str, start_line: int) -> tuple[bool, str | None]:
    """True if ``quote`` matches contiguously starting at 1-based ``start_line``."""
    file_lines = split_lines_preserve_content(file_text)
    quote_lines = split_lines_preserve_content(quote)
    if not quote_lines or start_line < 1:
        return False, None
    idx = start_line - 1
    end = idx + len(quote_lines)
    if end > len(file_lines):
        return False, None
    window = file_lines[idx:end]
    if window != quote_lines:
        return False, None
    return True, "\n".join(window)


def expected_end_line_for_quote(start_line: int, quote: str) -> int:
    """Inclusive end_line that exactly covers the verbatim span."""
    n = len(split_lines_preserve_content(quote))
    if n < 1:
        return start_line
    return start_line + n - 1


def verify_finding_evidence(
    finding: dict,
    *,
    repo_root: Path,
    target: ReviewTarget,
    changed_lines: dict[str, set[int]],
) -> EvidenceCheckResult:
    """Validate one schema-valid finding against the frozen target."""
    location = finding.get("location") or {}
    path = location.get("path")
    start_line = location.get("start_line")
    end_line = location.get("end_line")
    claim_type = location.get("claim_type")
    verbatim = finding.get("verbatim")

    if not isinstance(path, str) or not is_safe_repo_relative_path(path):
        return EvidenceCheckResult(OUTCOME_MALFORMED, detail="unsafe_or_invalid_path")
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        return EvidenceCheckResult(OUTCOME_MALFORMED, detail="invalid_line_types")
    if start_line < 1 or end_line < start_line:
        return EvidenceCheckResult(OUTCOME_MALFORMED, detail="invalid_line_range")
    if claim_type not in ("present", "missing"):
        return EvidenceCheckResult(OUTCOME_MALFORMED, detail="invalid_claim_type")
    if not isinstance(verbatim, str) or not verbatim:
        return EvidenceCheckResult(OUTCOME_MALFORMED, detail="empty_verbatim")

    try:
        resolve_safe_path(repo_root, path)
    except EvidenceError as exc:
        return EvidenceCheckResult(OUTCOME_MALFORMED, detail=str(exc))

    if path not in target.changed_paths:
        return EvidenceCheckResult(
            OUTCOME_OUT_OF_SCOPE,
            detail=f"path_not_in_changed_paths:{path}",
        )

    try:
        file_text = load_file_text(repo_root, path, target)
    except EvidenceError as exc:
        return EvidenceCheckResult(OUTCOME_QUOTE_MISSING, detail=str(exc))
    except (UnicodeDecodeError, OSError) as exc:
        return EvidenceCheckResult(
            OUTCOME_QUOTE_MISSING,
            detail=f"read_or_decode_failed:{path}:{exc}",
        )

    quote_lines = split_lines_preserve_content(verbatim)
    expected_end = expected_end_line_for_quote(start_line, verbatim)
    alternate_line, alternate_text = find_verbatim_match(file_text, verbatim)

    # Range must equal the exact verbatim span (blocks inflated ranges that
    # intersect unrelated changed lines).
    if end_line != expected_end:
        return EvidenceCheckResult(
            OUTCOME_LINE_MISMATCH,
            matched_line=alternate_line,
            matched_text=alternate_text,
            detail=(
                f"range_span_mismatch:claimed={start_line}-{end_line} "
                f"expected_end={expected_end} quote_lines={len(quote_lines)}"
                + (f" actual_match_at={alternate_line}" if alternate_line is not None else "")
            ),
        )

    at_claim, matched_text = match_at_line(file_text, verbatim, start_line)
    if at_claim:
        matched_line = start_line
    else:
        if alternate_line is None:
            return EvidenceCheckResult(
                OUTCOME_QUOTE_MISSING,
                detail="verbatim_not_found",
            )
        return EvidenceCheckResult(
            OUTCOME_LINE_MISMATCH,
            matched_line=alternate_line,
            matched_text=alternate_text,
            detail=f"matched_at_line:{alternate_line}",
        )

    path_changed = changed_lines.get(path, set())
    primary_lines = set(range(start_line, end_line + 1))
    # present: primary location must land on a changed line.
    # missing: contextual evidence may sit on an unchanged line; do not invent
    # a diff line for the absent code.
    if claim_type == "present" and not primary_lines & path_changed:
        return EvidenceCheckResult(
            OUTCOME_OUT_OF_SCOPE,
            matched_line=matched_line,
            matched_text=matched_text,
            detail=(
                f"primary_location_not_on_changed_line:"
                f"{path}:{start_line}-{end_line}"
            ),
        )

    return EvidenceCheckResult(
        OUTCOME_VERIFIED,
        matched_line=matched_line,
        matched_text=matched_text,
        detail=f"matched_at_line:{matched_line}",
    )
