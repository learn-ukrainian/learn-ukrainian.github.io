"""Preserve worker-cited runtime scratch before lease deletion (#10000)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from scripts.common.nofollow_walk import ComponentOpenError, open_leaf_descriptor
from scripts.fleet import ignored_task_output as output
from scripts.orchestration import worktree_artifacts as artifacts


class HeldWorkPreservationError(ValueError):
    """A privacy-safe typed refusal: the original lease must survive."""

    code = "runtime_tmp_held_work_preservation_failed"

    def __init__(self) -> None:
        super().__init__(self.code)


def _strings(value: Any) -> list[str]:
    """Keep report text literal, including Markdown nested in structured output."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return []


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
        names.add(path.as_posix())
    return sorted(names)


def preserve(root: Path, *, primary: Path, record: Mapping[str, Any], response: str) -> dict[str, Any] | None:
    """Copy selected regular files and prove retrieval before authorizing deletion.

    The existing cap, no-follow descriptor walks, verified copy and retrieval
    verifier apply. Missing prose citations and directory mentions are ignored;
    declarations must name files. No scratch inventory or symlink target is copied.
    """
    try:
        names = cited_paths(root, record, response)
        if not names:
            return None
        declared_names = set(cited_paths(root, {"held_work": record.get("held_work", [])}, ""))
        existing = []
        total = 0
        root_fd = artifacts._open_trusted_root(root)
        try:
            for name in names:
                parent_fd, owned = root_fd, False
                try:
                    try:
                        parent_fd, owned = artifacts._open_parent(root_fd, Path(name).parts[:-1])
                        leaf_fd, info = open_leaf_descriptor(parent_fd, Path(name).name)
                    except FileNotFoundError:
                        if name in declared_names:
                            raise HeldWorkPreservationError() from None
                        continue
                    except ComponentOpenError as exc:
                        if name not in declared_names and exc.kind == "non-directory":
                            continue
                        raise
                    os.close(leaf_fd)
                    if stat.S_ISDIR(info.st_mode) and name not in declared_names:
                        continue
                    if not stat.S_ISREG(info.st_mode):
                        raise HeldWorkPreservationError()
                    total += info.st_size
                    if total > output.MAX_PRESERVED_BYTES:
                        raise HeldWorkPreservationError()
                    existing.append(name)
                finally:
                    if owned:
                        os.close(parent_fd)
        finally:
            os.close(root_fd)
        if not existing:
            return None
        paths = output._path_inventory(root, existing)
        if any(entry.get("type") == "symlink" for entry in paths):
            raise HeldWorkPreservationError()
        total = sum(entry["size"] for entry in paths)
        if total > output.MAX_PRESERVED_BYTES:
            raise HeldWorkPreservationError()
        task_id = record.get("task_id")
        if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", task_id):
            raise HeldWorkPreservationError()
        # New attempts never overwrite an earlier worker's held evidence.
        location = primary / "batch_state" / "preserved" / task_id / ("held-" + uuid.uuid4().hex)
        if location.is_relative_to(root):
            raise HeldWorkPreservationError()
        # Check every destination ancestor before creating directories.
        for parent in reversed((location, *location.parents)):
            if parent.is_symlink():
                raise HeldWorkPreservationError()
        location.mkdir(parents=True, exist_ok=False)
        for name in existing:
            artifacts._copy_verified(root / name, location / name, source_root=root, destination_root=location)
        receipt = {
            "schema": "runtime-held-work.v1",
            "task_id": task_id,
            "run_nonce": record.get("run_nonce"),
            "count": len(paths),
            "bytes": total,
            "paths": paths,
            "location": location.relative_to(primary).as_posix(),
            "content_sha256": output._content_digest(location, existing),
            "runtime_tmp_sha256": hashlib.sha256(str(root).encode()).hexdigest(),
        }
        receipt["retrieval_proof_sha256"] = output.verify_retrieval(primary, receipt)
        if output._path_inventory(root, existing) != paths or output._path_inventory(location, existing) != paths:
            raise HeldWorkPreservationError()
        with location.with_suffix(".manifest.json").open("x", encoding="utf-8") as manifest:
            json.dump(receipt, manifest, sort_keys=True)
            manifest.write("\n")
            manifest.flush()
            os.fsync(manifest.fileno())
        return receipt
    except (OSError, ValueError, RuntimeError, ComponentOpenError):
        raise HeldWorkPreservationError() from None
