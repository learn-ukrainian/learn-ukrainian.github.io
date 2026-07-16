"""Exact-target evidence verification for structured code-review findings.

Bound to :class:`scripts.review.target_resolution.ReviewTarget`. Verifies
verbatim quotes with **line-ending normalization only** — no backtick
stripping, no whitespace collapsing, no punctuation removal. Path safety
rejects absolute paths, drive paths, ``..``, symlink escapes, and locations
outside the reviewed target / changed surface.
"""

from __future__ import annotations

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


def load_file_text(repo_root: Path, rel_path: str, target: ReviewTarget) -> str:
    """Load file content from the exact review target (local tree or head SHA)."""
    safe = resolve_safe_path(repo_root, rel_path)
    if target.mode == "local":
        if not safe.is_file():
            raise EvidenceError(f"file_unavailable:{rel_path}")
        return safe.read_text(encoding="utf-8")
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
                    text = full.read_text(encoding="utf-8", errors="ignore")
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


def find_verbatim_match(
    file_text: str, quote: str
) -> tuple[int | None, str | None]:
    """Return (1-based start line, matched text) if quote is a contiguous match.

    Matching uses line-ending normalization only. The first match wins
    (deterministic for a fixed file).
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

    matched_line, matched_text = find_verbatim_match(file_text, verbatim)
    if matched_line is None:
        return EvidenceCheckResult(
            OUTCOME_QUOTE_MISSING,
            detail="verbatim_not_found",
        )

    claimed = start_line
    if matched_line != claimed:
        # Prefer line_mismatch over out_of_scope so a wrong line number that
        # still quotes real code surfaces the actual matched line.
        return EvidenceCheckResult(
            OUTCOME_LINE_MISMATCH,
            matched_line=matched_line,
            matched_text=matched_text,
            detail=f"matched_at_line:{matched_line}",
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
