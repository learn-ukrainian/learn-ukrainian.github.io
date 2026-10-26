"""Preserve worker-cited runtime scratch before lease deletion (#10000)."""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from scripts.fleet import ignored_task_output as output


class HeldWorkPreservationError(ValueError):
    """A privacy-safe typed refusal: the original lease must survive."""

    code = "runtime_tmp_held_work_preservation_failed"

    def __init__(self) -> None:
        super().__init__(self.code)


EVIDENCE_DIRNAME = "evidence"
EVIDENCE_SCHEMA = "runtime-evidence.v1"
class EvidencePreservationError(ValueError):
    """Evidence under the runtime lease could not be preserved; keep the lease."""

    code = "runtime_evidence_preservation_failed"


def _strings(value: Any) -> list[str]:
    """Keep report text literal, including Markdown nested in structured output."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return []


def evidence_names(root: Path, *, directories: list[str] | None = None) -> list[str] | None:
    """Relative regular-file names, including an empty list; None only when absent.

    The supported evidence directory is a fixed name, never a citation guess.
    Only regular files in real directories qualify; a symlink, special file or
    unreadable directory raises the typed refusal so the lease is retained. The
    existing 256 MiB retention cap applies, and exceeding it is a refusal, never
    a partial copy or a silent deletion.
    """
    evidence = root / EVIDENCE_DIRNAME
    try:
        info = evidence.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        raise EvidencePreservationError() from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise EvidencePreservationError()
    names: list[str] = []
    total = 0
    pending: list[tuple[str, str]] = [(str(evidence), "")]
    while pending:
        directory, prefix = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError:
            raise EvidencePreservationError() from None
        for entry in entries:
            relative = f"{prefix}{entry.name}"
            try:
                entry_info = entry.stat(follow_symlinks=False)
            except OSError:
                raise EvidencePreservationError() from None
            if stat.S_ISLNK(entry_info.st_mode):
                raise EvidencePreservationError()
            if stat.S_ISDIR(entry_info.st_mode):
                if directories is not None:
                    directories.append(relative)
                pending.append((entry.path, f"{relative}/"))
                continue
            if not stat.S_ISREG(entry_info.st_mode):
                raise EvidencePreservationError()
            total += entry_info.st_size
            names.append(relative)
    if directories is not None:
        directories.sort()
    return sorted(names)


def require_empty_evidence(root: Path) -> None:
    """Permit stateless cleanup only when no evidence entries need a receipt.

    Empty subdirectories are entries too. Re-enumerate on every call so an
    earlier empty inventory cannot authorize deletion after a writer adds data.
    """
    directories: list[str] = []
    if evidence_names(root, directories=directories) or directories:
        raise EvidencePreservationError()


def evidence_matches_receipt(root: Path, receipt: Mapping[str, Any]) -> bool:
    """Record-only receipts authorize disposal without a byte-retrieval requirement."""
    return receipt.get("mode") == "record-only"


def preserve_evidence(root: Path, *, primary: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a valid record-only receipt, including on unreadable or oversized evidence."""
    try:
        names = evidence_names(root) or []
        return output.record_only_receipt(root / EVIDENCE_DIRNAME, names, record)
    except (OSError, ValueError, RuntimeError):
        return output.record_only_receipt(root, [], record, error="inventory_failed")


def cited_paths(root: Path, record: Mapping[str, Any], response: str) -> list[str]:
    """Read file citations and explicit ``held_work`` relative file names.

    Markdown links, code spans, quotes, file URIs and line-number suffixes
    share the existing named-artifact token conventions. Delimited relative
    citations and held_work names are interpreted within the runtime root.
    Invalid prose tokens are ignored; explicit declarations remain strict.
    """
    text = "\n".join(
        [
            response,
            *_strings(
                {
                    key: record[key]
                    for key in ("response", "result", "report", "deliverable", "result_file")
                    if key in record
                }
            ),
        ]
    )
    token_pattern = re.compile(
        # Unicode letters on both sides make an apostrophe prose, not a delimiter.
        r"(?P<quote>[`\"]|(?<![^\W\d_])'|'(?![^\W\d_]))"
        r"(?P<quoted>[^\n]+?)(?!(?<=[^\W\d_])'(?=[^\W\d_]))(?P=quote)"
        r"|\[[^\]\n]*\]\((?P<link><[^>\n]+>|[^)]+)\)"
        r"|<(?P<angle>[^>\n]+)>|(?P<bare>[^\s`\"'<>(),;]+)"
    )
    candidates = []
    segments = [text]
    for segment in segments:
        for match in token_pattern.finditer(segment):
            quoted, link, angle, bare = (match[name] for name in ("quoted", "link", "angle", "bare"))
            candidates.append((quoted or link or angle or bare, False, bare is None))
            if quoted is not None:
                # A quoted sentence can contain a bare absolute path or nested citation.
                segments.append(quoted)
    declared = record.get("held_work", [])
    if not isinstance(declared, list) or any(not isinstance(path, str) or not path for path in declared):
        raise HeldWorkPreservationError()
    candidates.extend((path, True, True) for path in declared)
    names = set()
    for raw, explicit, relative_citation in candidates:
        raw = raw.removeprefix("<").removesuffix(">")
        candidate = raw if explicit else re.sub(r":\d+(?::\d+)?$", "", raw.rstrip(".:!?"))
        if candidate.startswith("file://"):
            candidate = candidate[7:]
        candidate = unquote(candidate)
        if not candidate or "\x00" in candidate:
            if explicit:
                raise HeldWorkPreservationError()
            continue
        for variable in ("$TMPDIR/", "${TMPDIR}/", "$LU_RUNTIME_TMP_ROOT/", "${LU_RUNTIME_TMP_ROOT}/"):
            if candidate.startswith(variable):
                candidate = str(root / candidate[len(variable) :])
                break
        path = Path(candidate)
        if path.is_absolute():
            if not path.is_relative_to(root):
                if explicit:
                    raise HeldWorkPreservationError()
                continue
            path = path.relative_to(root)
        elif not explicit and not relative_citation:
            continue
        if not path.parts or ".." in path.parts:
            if explicit:
                raise HeldWorkPreservationError()
            continue
        if not explicit and any(len(part.encode("utf-8")) > 255 for part in path.parts):
            # Oversized prose cannot name a file; declarations still fail strictly.
            continue
        names.add(path.as_posix())
    return sorted(names)


def preserve(root: Path, *, primary: Path, record: Mapping[str, Any], response: str) -> dict[str, Any] | None:
    """Receipt cited scratch without copying bytes or blocking lease deletion."""
    try:
        return output.record_only_receipt(root, cited_paths(root, record, response), record)
    except (OSError, ValueError, RuntimeError):
        return output.record_only_receipt(root, [], record, error="inventory_failed")
