"""A bounded worker is dispatched only with a complete advisory envelope (#9275).

Operator decision 2026-09-30: there is no direct bounded dispatch. Every
dispatch that resolves to the catalog's bounded worker
(``execution_routing.sol_advised_bounded.preferred_worker``), or to its Gemini
Flash fallback without an explicit Ukrainian authoring/review classification,
needs an envelope from the catalog advisor route, bound to that dispatch.

Threat model (advisor decision on #9275): the rule is cooperative. It stops
omitted advice, stale or foreign bindings, accidental prompt drift and scope
overruns by processes that follow the dispatch path. It does not defend against
deliberate forgery by a process that can rewrite task records, results or
launcher code: such a process can recompute every digest kept here. Nothing in
this module authenticates who wrote a record or result.

The envelope is accepted only by reference to the advisor's task
(``delegate.py dispatch --advisory-task <task-id>``), never as a free file. The
advisor task must have run with ``--advisory-role bounded_advisory_envelope``
on the advisor model, read-only, and finished ``done``. Its canonical result
must hold exactly one fenced ``advisory-envelope`` JSON object with every
catalog ``output_fields`` key, typed and meaningful, plus the
``dispatch_args_sha256`` binding digest of the worker dispatch that the advisor
dispatch recorded as ``advisory_binding_sha256``.

The advisor's worker records ``advisory_seal`` beside the result when it
finishes: the SHA-256 of the result it wrote, of the envelope in it, and the
model and run nonce it ran. The seal is a consistency checksum. Admission
recomputes both digests and refuses a result edited or replaced after finish
without a matching record update; a writer that updates both is outside the
threat model above.

The bound brief is what the worker runs: the worker rebuilds the expected
prompt from the brief whose SHA-256 the envelope binds plus the dispatcher
blocks it can re-derive, and compares it with the exact bytes it hands the
provider (``verify_worker_admission``). It never trusts a prompt digest stored
in its own task record.

The worker also compares every admitted execution parameter
(``EXECUTION_FIELDS``: agent, model, mode, cwd, effort, timeouts, budget,
provider, harness, PR opening) with what it is about to run, and with the bound
dispatch arguments that set them, before any provider call.

Two completion gates run after the worker exits; neither stops a worker while
it runs. The envelope ceilings: ``delegate.py`` measures a bounded worker's
changes and fails the task when either ceiling is exceeded or cannot be
measured. The content exemption: a Gemini Flash write dispatch admitted as
Ukrainian content classifies its owned directories and globs by the files they
hold at admission, so ``delegate.py`` classifies every path the worker changed
(``exempt_change_problems``) and fails the task, never ``done``, when one is
code or the changes cannot be read.

This module is pure validation: it reads task records, results and the
repository tree, and raises ``AdvisoryRefused`` with a typed code.
``delegate.py`` computes the binding digest, calls it after route resolution
and again just before the task record is published, re-verifies it in the
worker before start and at the provider handoff, and runs both completion
gates at finalize.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import unicodedata
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.orchestration.worktree_paths import automatic_worktree_path
from scripts.review.model_catalog import (
    ADVISOR_ROUTE,
    BoundedExecutionPolicy,
    bounded_execution_policy,
    canonical_model_id,
)

ENVELOPE_FENCE = "advisory-envelope"
BINDING_FIELD = "dispatch_args_sha256"
_FENCE_RE = re.compile(r"^```" + re.escape(ENVELOPE_FENCE) + r"[ \t]*\n(.*?)\n```[ \t]*$", re.MULTILINE | re.DOTALL)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GLOB_CHARS = frozenset("*?[")
# Repo roots a bounded worker never owns: git metadata, dispatch worktrees,
# interpreter and dependency trees, and delegate's own task state.
_FORBIDDEN_ROOTS = frozenset({".git", ".worktrees", ".venv", "node_modules", "batch_state"})
# The only roots a Ukrainian authoring or review dispatch may own and stay
# exempt. Anything else — code roots, repo-root files, unresolvable or
# root-level-glob paths — makes the classification contradictory (fail closed).
_UKRAINIAN_CONTENT_ROOTS = frozenset({"curriculum", "wiki", "docs", "data", "plans"})
# File suffixes that are code wherever they live.
_CODE_SUFFIXES = frozenset(
    {
        ".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".astro", ".vue", ".svelte",
        ".sh", ".bash", ".css", ".scss", ".html", ".sql", ".toml", ".ini", ".cfg",
    }
)  # fmt: skip
# Git attributes that mark a file as code wherever it lives: a programming-language
# diff driver, or a linguist language other than these content formats.
_CODE_DIFF_DRIVERS = frozenset(
    {
        "ada", "bash", "cpp", "csharp", "css", "dts", "elixir", "fortran", "golang", "html", "java",
        "kotlin", "matlab", "objc", "pascal", "perl", "php", "python", "ruby", "rust", "scheme",
    }
)  # fmt: skip
_CONTENT_LINGUIST_LANGUAGES = frozenset({"markdown", "mdx", "yaml", "json", "text", "csv", "tsv"})
# A glob is content-only when its last segment ends in a literal extension.
_LITERAL_EXTENSION_RE = re.compile(r"\.([A-Za-z0-9_-]+)$")
_GIT_TIMEOUT_S = 60
SEAL_FIELD = "advisory_seal"

# Typed refusal codes.
ENVELOPE_REQUIRED = "BOUNDED_ENVELOPE_REQUIRED"
FLAG_CONFLICT = "ADVISORY_FLAG_CONFLICT"
TASK_NOT_FOUND = "ADVISORY_TASK_NOT_FOUND"
TASK_NOT_DONE = "ADVISORY_TASK_NOT_DONE"
TASK_WRONG_MODEL = "ADVISORY_TASK_WRONG_MODEL"
TASK_WRONG_ROLE = "ADVISORY_TASK_WRONG_ROLE"
RESULT_UNREADABLE = "ADVISORY_RESULT_UNREADABLE"
ENVELOPE_MISSING = "ADVISORY_ENVELOPE_MISSING"
ENVELOPE_INCOMPLETE = "ADVISORY_ENVELOPE_INCOMPLETE"
OWNED_PATHS_INVALID = "ADVISORY_OWNED_PATHS_INVALID"
BINDING_MISMATCH = "ADVISORY_BINDING_MISMATCH"
OWNED_PATHS_MISMATCH = "ADVISORY_OWNED_PATHS_MISMATCH"
ENVELOPE_CHANGED = "ADVISORY_ENVELOPE_CHANGED"
SEAL_MISSING = "ADVISORY_SEAL_MISSING"
SEAL_MISMATCH = "ADVISORY_SEAL_MISMATCH"
ADMISSION_MISSING = "BOUNDED_ADMISSION_MISSING"
ADMISSION_INVALID = "BOUNDED_ADMISSION_INVALID"
ADVISOR_ROUTE_REFUSED = "ADVISORY_ROLE_REFUSED"
EXECUTION_MISMATCH = "BOUNDED_EXECUTION_MISMATCH"
CEILING_EXCEEDED = "advisory_ceiling_exceeded"
CEILING_UNMEASURED = "advisory_ceiling_unmeasured"
EXEMPT_CODE_CHANGE = "advisory_exempt_code_change"
EXEMPT_CHANGES_UNMEASURED = "advisory_exempt_changes_unmeasured"

# The launch a bounded worker is admitted to run (``admitted_execution``); the
# worker compares each with what it is about to run before any provider call.
EXECUTION_FIELDS = (
    "agent", "model_id", "mode", "cwd", "effort", "hard_timeout", "silence_timeout",
    "initial_response_timeout", "max_budget_usd", "provider", "harness", "finalize_open_pr",
)  # fmt: skip
# The execution fields a dispatch argument of the same name sets; the envelope binds their digest.
_BOUND_EXECUTION_ARGS = (
    "mode", "effort", "hard_timeout", "silence_timeout", "initial_response_timeout",
    "max_budget_usd", "provider", "finalize_open_pr",
)  # fmt: skip


class AdvisoryRefused(Exception):
    """A bounded dispatch or an advisor dispatch is refused; ``code`` names why."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ValidatedEnvelope:
    """An envelope read from a finished advisor task, with the digests that bind it."""

    advisor_task_id: str
    advisor_model: str
    advisor_run_nonce: str | None
    result_path: str
    result_sha256: str
    envelope: dict[str, Any]
    envelope_sha256: str
    binding_sha256: str

    @property
    def owned_paths(self) -> list[str]:
        return list(self.envelope["owned_paths"])

    def state_record(
        self,
        requirement: str,
        *,
        args: Mapping[str, Any],
        prompt_sha256: str,
        repo_root: Path,
        execution: Mapping[str, Any] | None,
        research_block: str = "",
    ) -> dict[str, Any]:
        """What the worker's task record keeps: the envelope's source, digests, binding inputs, scope and ceilings.

        ``args`` (the dispatch arguments, hashing to ``advisory_args_sha256``)
        and ``prompt_sha256`` (the brief) are the two halves of the binding
        (``binding_digest``); the worker re-derives the binding from them and
        reads its admitted mode, owned paths and rules seat from ``args``.
        ``execution`` is the admitted launch, one value per ``EXECUTION_FIELDS``
        (None for a dry run, which starts no worker); ``research_block`` the
        research pointer block the dispatcher added to the prompt.
        """
        record: dict[str, Any] = {
            "requirement": requirement,
            "advisory_args": dict(args),
            "advisory_args_sha256": canonical_sha256(args),
            "prompt_sha256": prompt_sha256,
            "research_block": research_block,
            "repo_root": str(repo_root),
            "advisor_task_id": self.advisor_task_id,
            "advisor_model": self.advisor_model,
            "advisor_run_nonce": self.advisor_run_nonce,
            "result_path": self.result_path,
            "result_sha256": self.result_sha256,
            "envelope_sha256": self.envelope_sha256,
            "dispatch_args_sha256": self.binding_sha256,
            "owned_paths": self.owned_paths,
            "max_changed_files": self.envelope["max_changed_files"],
            "max_non_test_loc": self.envelope["max_non_test_loc"],
        }
        if execution is not None:
            record["admitted_execution"] = dict(execution)
        return record


def binding_digest(args_sha256: str, prompt_sha256: str | None) -> str:
    """The digest an envelope binds to: the dispatch-argument digest and the prompt-text digest."""
    payload = {"dispatch_args_sha256": args_sha256, "prompt_sha256": prompt_sha256}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def canonical_sha256(value: Mapping[str, Any]) -> str:
    """SHA-256 of a JSON object's canonical form (sorted keys, compact separators, ASCII)."""
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def envelope_sha256(envelope: Mapping[str, Any]) -> str:
    """SHA-256 of an envelope's canonical JSON (``canonical_sha256``)."""
    return canonical_sha256(envelope)


def _result_envelope_sha256(result_text: str) -> str | None:
    """The canonical digest of the result's one fenced envelope object; None when there is not exactly one."""
    blocks = _FENCE_RE.findall(result_text)
    if len(blocks) != 1:
        return None
    try:
        envelope = json.loads(blocks[0])
    except ValueError:
        return None
    return envelope_sha256(envelope) if isinstance(envelope, dict) else None


def seal_advisor_result(response: str, *, model: str | None, run_nonce: str | None) -> dict[str, Any]:
    """The finish-time consistency checksum an advisor's worker records beside the result it writes.

    ``response`` is the text written, UTF-8, to the canonical result; ``model``
    the model the worker ran. Admission refuses a result that no longer hashes
    to ``result_sha256`` or whose envelope no longer hashes to
    ``envelope_sha256``. The seal authenticates nothing: whoever can write the
    task record can recompute it (see the module threat model).
    """
    return {
        "result_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
        "envelope_sha256": _result_envelope_sha256(response),
        "advisor_model": canonical_model_id(model) or model,
        "run_nonce": run_nonce,
    }


def _normalized(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _path_segments(path: Any) -> list[str] | None:
    """``path`` resolved lexically to repo-relative segments (``./``, ``..``, repeated and trailing ``/``, ``\\``).

    None when it is blank, absolute, home-relative, climbs above the repository,
    or climbs after a glob (``**`` may match any depth, so ``..`` there has no
    lexical meaning).
    """
    text = str(path).strip().replace("\\", "/") if path is not None else ""
    if not text or text.startswith(("/", "~")):
        return None
    segments: list[str] = []
    for segment in text.split("/"):
        if segment in {"", "."}:
            continue
        if segment == "..":
            if not segments or any(_GLOB_CHARS & set(kept) for kept in segments):
                return None
            segments.pop()
            continue
        segments.append(segment)
    return segments or None


def _git(repo_root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    """``git --literal-pathspecs <args>`` in ``repo_root``; raises ``RuntimeError`` when it fails."""
    try:
        proc = subprocess.run(
            ["git", "--literal-pathspecs", *args],
            cwd=repo_root,
            input=stdin,
            capture_output=True,
            check=False,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"git {args[0]}: {exc}") from None
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip() or f"exit {proc.returncode}"
        raise RuntimeError(f"git {args[0]}: {detail}")
    return proc.stdout


def _tracked_entries(repo_root: Path, base: str) -> dict[str, str]:
    """``path -> git file mode`` for every file git tracks at or under ``base``, sparse or not."""
    entries: dict[str, str] = {}
    for record in _git(repo_root, "ls-files", "-s", "-z", "--", base).split(b"\0"):
        if record:
            meta, _, path = record.partition(b"\t")
            entries[path.decode("utf-8", "surrogateescape")] = meta.split()[0].decode("ascii")
    return entries


def _content_root_of(resolved: Path, root: Path) -> str | None:
    """The Ukrainian content root a resolved path lies under, or None."""
    try:
        parts = resolved.relative_to(root).parts
    except ValueError:
        return None
    return parts[0] if parts and parts[0] in _UKRAINIAN_CONTENT_ROOTS else None


def _disk_files(repo_root: Path, base: str) -> tuple[list[str], str | None]:
    """Files on disk at or under ``base``, following symlinked directories, and the first directory outside content.

    The walk stops at a directory whose real path leaves the Ukrainian content
    roots (returned second), so a symlink out of content is never walked.
    """
    root = repo_root.resolve()
    top = repo_root / base
    if not top.is_dir():
        return ([base] if top.exists() or top.is_symlink() else []), None
    files: list[str] = []
    seen: set[str] = set()
    for directory, subdirs, names in os.walk(top, followlinks=True):
        rel_dir = Path(directory).relative_to(repo_root).as_posix()
        real = Path(os.path.realpath(directory))
        if _content_root_of(real, root) is None:
            return files, rel_dir
        if str(real) in seen:
            subdirs[:] = []
            continue
        seen.add(str(real))
        subdirs.sort()
        files.extend(f"{rel_dir}/{name}" for name in sorted(names))
    return files, None


def _code_by_attributes(repo_root: Path, files: Sequence[str]) -> list[str]:
    """Files that git attributes mark as code (a code diff driver or a non-content linguist language)."""
    if not files:
        return []
    stdin = b"".join(name.encode("utf-8", "surrogateescape") + b"\0" for name in files)
    fields = _git(repo_root, "check-attr", "-z", "--stdin", "diff", "linguist-language", stdin=stdin).split(b"\0")
    code: set[str] = set()
    for index in range(0, len(fields) - 2, 3):
        name, attribute, value = (field.decode("utf-8", "surrogateescape") for field in fields[index : index + 3])
        value = value.casefold()
        if value in {"unspecified", "unset", "set"}:
            continue
        if (attribute == "diff" and value in _CODE_DIFF_DRIVERS) or (
            attribute == "linguist-language" and value not in _CONTENT_LINGUIST_LANGUAGES
        ):
            code.add(name)
    return sorted(code)


def _non_content_files(repo_root: Path, files: Sequence[str], *, symlinks: Iterable[str] = ()) -> list[tuple[str, str]]:
    """``(file, reason)`` for each of ``files`` that is not Ukrainian content, judged by the file and its target.

    A file is not content when it is a symlink that does not resolve
    (``symlinks`` names those git tracks as links, sparse or not), its resolved
    target leaves the content roots, the file or its resolved target has a code
    extension, or git attributes mark the file or its resolved target as code.
    Raises ``RuntimeError`` when git attributes cannot be read.
    """
    root = repo_root.resolve()
    links = set(symlinks)
    problems: dict[str, str] = {}
    queried: dict[str, list[str]] = {}  # path whose attributes are read -> the files it classifies
    for rel in files:
        target = repo_root / rel
        queried.setdefault(rel, []).append(rel)
        if (rel in links or target.is_symlink()) and not target.exists():
            problems[rel] = "is a symlink that cannot be resolved in this tree"
            continue
        resolved = target.resolve()
        if PurePosixPath(rel).suffix.lower() in _CODE_SUFFIXES or resolved.suffix.lower() in _CODE_SUFFIXES:
            problems[rel] = "is a code file"
            continue
        if _content_root_of(resolved, root) is None:
            problems[rel] = "resolves outside the Ukrainian content roots"
            continue
        resolved_rel = resolved.relative_to(root).as_posix()
        if resolved_rel != rel:
            queried.setdefault(resolved_rel, []).append(rel)
    for code_path in _code_by_attributes(repo_root, sorted(queried)):
        for rel in queried[code_path]:
            via = "" if code_path == rel else f" (its target {code_path!r})"
            problems.setdefault(rel, f"git attributes mark as code{via}")
    return sorted(problems.items())


def content_path_problem(path: Any, repo_root: Path) -> str | None:
    """Why ``path`` is not Ukrainian content only in ``repo_root``; None when every file it can match is.

    The path is normalized first (``././scripts``, ``curriculum/../scripts`` and
    ``scripts/`` classify like ``scripts``) and must start inside a Ukrainian
    content root. A glob must pin a literal non-code extension in its last
    segment and use no character class, so ``docs/**/*.p[y]``, ``docs/**/*.p?``
    and ``docs/**/*`` are code-capable. Then every file the path owns, as
    dispatch ownership reads it (``owned_path_matcher``), is enumerated from
    git's index and from disk, symlinks followed: each must resolve under a
    content root, and neither it nor its resolved target may be code by
    extension or by git attributes (``_non_content_files``). A directory is
    judged by the files it holds now; files a worker adds later are judged by
    the completion gate (``exempt_change_problems``). An unreadable tree is a
    problem (fail closed).
    """
    from scripts.guardrails.delegate_ownership import owned_path_matcher

    segments = _path_segments(path)
    if segments is None:
        return "is not a repository-relative path inside the repository"
    if segments[-1] == "**" and len(segments) > 1:
        segments = segments[:-1]  # ``dir/**`` owns the subtree, exactly as ``dir/`` does
    static: list[str] = []
    for segment in segments:
        if _GLOB_CHARS & set(segment):
            break
        static.append(segment)
    if not static or static[0] not in _UKRAINIAN_CONTENT_ROOTS:
        return "is outside the Ukrainian content roots"
    if PurePosixPath(segments[-1]).suffix.lower() in _CODE_SUFFIXES:
        return "names a code file"
    normalized = "/".join(segments)
    if len(static) < len(segments):
        if "[" in normalized:
            return "uses a character class, which can match a code file"
        extension = _LITERAL_EXTENSION_RE.search(segments[-1])
        if extension is None or f".{extension.group(1).lower()}" in _CODE_SUFFIXES:
            return "is a glob without a literal non-code extension, which can match a code file"
    matcher = owned_path_matcher(normalized)
    if matcher is None:
        return "owns no file"
    root = repo_root.resolve()
    base = "/".join(static)
    if _content_root_of((repo_root / base).resolve(), root) is None:
        return f"resolves outside the Ukrainian content roots ({base!r})"
    try:
        tracked = _tracked_entries(repo_root, base)
        on_disk, outside = _disk_files(repo_root, base)
    except (OSError, RuntimeError) as exc:
        return f"cannot be resolved in {repo_root} ({exc})"
    if outside is not None:
        return f"reaches directory {outside!r}, which resolves outside the Ukrainian content roots"
    files = sorted(rel for rel in {*tracked, *on_disk} if matcher(rel))
    try:
        problems = _non_content_files(
            repo_root, files, symlinks={rel for rel, mode in tracked.items() if mode == "120000"}
        )
    except RuntimeError as exc:
        return f"cannot be checked for code attributes in {repo_root} ({exc})"
    if problems:
        rel, reason = problems[0]
        return f"covers {rel!r}, which {reason}"
    return None


def exempt_change_problems(paths: Iterable[str], repo_root: Path) -> list[str]:
    """Why each path a content-exempt worker changed is not Ukrainian content; empty when every one is.

    The completion gate of a Ukrainian exemption: admission classifies the
    files an owned directory or glob holds then, not the ones a worker adds
    later. A changed path fails when it lies outside the content roots, is a
    ``.gitattributes`` file, or is not content as ``_non_content_files``
    judges it (resolved through symlinks). Deleted paths are judged by name.
    Raises ``RuntimeError`` when git attributes cannot be read.
    """
    problems: list[str] = []
    content: list[str] = []
    for rel in sorted({str(path) for path in paths}):
        segments = _path_segments(rel)
        if segments is None or segments[0] not in _UKRAINIAN_CONTENT_ROOTS:
            problems.append(f"{rel!r}, which is outside the Ukrainian content roots")
        elif segments[-1] == ".gitattributes":
            problems.append(f"{rel!r}, which changes git attributes")
        else:
            content.append(rel)
    problems.extend(f"{rel!r}, which {reason}" for rel, reason in _non_content_files(repo_root, content))
    return problems


def is_ukrainian_content_path(path: Any, repo_root: Path) -> bool:
    """True when every file ``path`` can match in ``repo_root`` is Ukrainian content (``content_path_problem``)."""
    return content_path_problem(path, repo_root) is None


def bounded_requirement(
    model_id: str | None,
    *,
    mode: str,
    task_family: str | None,
    review_profile: str | None,
    owned_paths: Iterable[str] = (),
    repo_root: Path,
    policy: BoundedExecutionPolicy | None = None,
) -> str | None:
    """Why this launch needs an advisory envelope, or None when it does not.

    ``model_id`` is the canonical catalog id of the model the admitted route
    launches, after aliases, ``--force-agent`` and any substitution. Every
    bounded-worker dispatch needs one. A Gemini Flash dispatch is the bounded
    fallback unless it is explicitly classified non-bounded — a Ukrainian
    authoring or review task family, or ``--review-profile ukrainian`` for a
    read-only review — and nothing contradicts that; missing or conflicting
    classification counts as bounded (fail closed). Either exemption owning a
    path that is not Ukrainian content only in ``repo_root``
    (``content_path_problem``) conflicts.
    """
    policy = policy or bounded_execution_policy()
    if model_id is None:
        return None
    if model_id == policy.bounded_worker_model_id:
        return f"{model_id} is the bounded worker"
    if model_id != policy.bounded_fallback_model_id:
        return None
    family = _normalized(task_family)
    ukrainian_family = family in policy.non_bounded_task_families
    conflicts: list[str] = []
    if ukrainian_family and review_profile == "code":
        conflicts.append(f"task family {family!r} with --review-profile code")
    if review_profile == "ukrainian" and family is not None and not ukrainian_family:
        conflicts.append(f"--review-profile ukrainian with non-Ukrainian task family {family!r}")
    if ukrainian_family or review_profile == "ukrainian":
        problems = sorted(
            f"{path!r} {problem}"
            for path in {str(path) for path in owned_paths}
            if (problem := content_path_problem(path, repo_root)) is not None
        )
        if problems:
            claim = f"task family {family!r}" if ukrainian_family else "--review-profile ukrainian"
            conflicts.append(f"{claim} owning code or non-content paths ({'; '.join(problems)})")
    if conflicts:
        return f"{model_id} with an ambiguous classification ({'; '.join(conflicts)}) is the bounded fallback"
    if ukrainian_family:
        return None
    if review_profile == "ukrainian" and mode == "read-only":
        return None
    if review_profile == "ukrainian":
        return (
            f"{model_id} in {mode} mode with --review-profile ukrainian but no Ukrainian authoring/review "
            "task family is the bounded fallback"
        )
    return (
        f"{model_id} without a Ukrainian authoring/review classification "
        f"(--research-task-family one of {sorted(policy.non_bounded_task_families)}, or read-only "
        "--review-profile ukrainian) is the bounded fallback"
    )


def validate_owned_path(path: Any, repo_root: Path) -> str:
    """Return ``path`` when it is a repo-relative path that exists or is creatable under an allowed root."""
    if not isinstance(path, str) or not path or path != path.strip():
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} must be a non-blank string")
    if any(unicodedata.category(char).startswith(("C", "Z")) and char != " " for char in path) or "\\" in path:
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} holds control, format or separator characters")
    pure = PurePosixPath(path)
    if pure.is_absolute() or path.startswith("~"):
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} must be repo-relative")
    segments = path.rstrip("/").split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} has an empty, '.' or '..' segment")
    if segments[0] in _FORBIDDEN_ROOTS:
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} is under a forbidden root {segments[0]!r}")
    static: list[str] = []
    for segment in segments:
        if _GLOB_CHARS & set(segment):
            break
        static.append(segment)
    if not static:
        raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} does not name a root directory")
    root = repo_root.resolve()
    top = repo_root / static[0]
    if not top.exists() and not top.is_symlink():
        raise AdvisoryRefused(
            OWNED_PATHS_INVALID, f"owned path {path!r} is not under an existing repository root ({static[0]!r})"
        )
    current = repo_root
    for index, segment in enumerate(static):
        current = current / segment
        if not current.exists() and not current.is_symlink():
            break
        try:
            current.resolve().relative_to(root)
        except ValueError:
            raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} leaves the repository") from None
        if current.is_file() and index < len(static) - 1:
            raise AdvisoryRefused(OWNED_PATHS_INVALID, f"owned path {path!r} descends into file {segment!r}")
    return path


def _require_text(envelope: Mapping[str, Any], field: str) -> None:
    value = envelope.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{field} must be a non-empty string")


def _require_text_list(envelope: Mapping[str, Any], field: str) -> None:
    value = envelope.get(field)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{field} must be a non-empty list of non-empty strings")


def _require_positive_int(envelope: Mapping[str, Any], field: str) -> None:
    value = envelope.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{field} must be a positive integer, got {value!r}")


def parse_envelope(
    result_text: str,
    *,
    repo_root: Path,
    policy: BoundedExecutionPolicy | None = None,
) -> dict[str, Any]:
    """The one ``advisory-envelope`` JSON object in ``result_text``, validated field by field."""
    policy = policy or bounded_execution_policy()
    blocks = _FENCE_RE.findall(result_text)
    if not blocks:
        raise AdvisoryRefused(ENVELOPE_MISSING, f"the advisor result holds no ```{ENVELOPE_FENCE} block")
    if len(blocks) > 1:
        raise AdvisoryRefused(ENVELOPE_MISSING, f"the advisor result holds {len(blocks)} ```{ENVELOPE_FENCE} blocks")
    try:
        envelope = json.loads(blocks[0])
    except ValueError as exc:
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"the envelope is not JSON: {exc}") from None
    if not isinstance(envelope, dict):
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, "the envelope must be a JSON object")
    expected = {*policy.advisor_output_fields, BINDING_FIELD}
    missing = sorted(expected - set(envelope))
    extra = sorted(set(envelope) - expected)
    if missing or extra:
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"envelope fields missing {missing}, unexpected {extra}")
    for field in policy.advisor_output_fields:
        if field in {"max_changed_files", "max_non_test_loc"}:
            _require_positive_int(envelope, field)
        elif field == "task_contract":
            _require_text(envelope, field)
        else:
            _require_text_list(envelope, field)
    binding = envelope[BINDING_FIELD]
    if not isinstance(binding, str) or not _SHA256_RE.fullmatch(binding):
        raise AdvisoryRefused(ENVELOPE_INCOMPLETE, f"{BINDING_FIELD} must be a lowercase sha256 hex digest")
    owned = [validate_owned_path(path, repo_root) for path in envelope["owned_paths"]]
    if len(set(owned)) != len(owned):
        raise AdvisoryRefused(OWNED_PATHS_INVALID, "owned_paths repeats a path")
    return envelope


def _read_record(state_path: Path, advisor_task_id: str) -> dict[str, Any]:
    try:
        record = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AdvisoryRefused(TASK_NOT_FOUND, f"no task record for advisory task {advisor_task_id!r}") from None
    except (OSError, ValueError) as exc:
        raise AdvisoryRefused(
            TASK_NOT_FOUND, f"advisory task {advisor_task_id!r} record is unreadable: {exc}"
        ) from None
    if not isinstance(record, dict) or record.get("task_id") != advisor_task_id:
        raise AdvisoryRefused(TASK_NOT_FOUND, f"advisory task {advisor_task_id!r} record does not name that task")
    return record


def load_envelope(
    advisor_task_id: str,
    *,
    state_path: Path,
    binding_sha256: str,
    repo_root: Path,
    policy: BoundedExecutionPolicy | None = None,
) -> ValidatedEnvelope:
    """Validate the advisor task's canonical record and result, and the envelope's binding to this dispatch."""
    policy = policy or bounded_execution_policy()
    record = _read_record(state_path, advisor_task_id)
    status = record.get("status")
    if status != "done":
        raise AdvisoryRefused(TASK_NOT_DONE, f"advisory task {advisor_task_id!r} is {status!r}, not 'done'")
    if record.get("advisory_role") != policy.advisor_role or record.get("advisory_route") != ADVISOR_ROUTE:
        raise AdvisoryRefused(
            TASK_WRONG_ROLE,
            f"advisory task {advisor_task_id!r} did not run as {policy.advisor_role!r} on {ADVISOR_ROUTE}",
        )
    if record.get("mode") != "read-only":
        raise AdvisoryRefused(TASK_WRONG_ROLE, f"advisory task {advisor_task_id!r} did not run read-only")
    recorded_model = record.get("model")
    if canonical_model_id(recorded_model) != policy.advisor_model_id or record.get("resolved_model_known") is False:
        raise AdvisoryRefused(
            TASK_WRONG_MODEL,
            f"advisory task {advisor_task_id!r} ran on {recorded_model!r}, not the advisor {policy.advisor_model_id}",
        )
    if record.get("advisory_binding_sha256") != binding_sha256:
        raise AdvisoryRefused(
            BINDING_MISMATCH,
            f"advisory task {advisor_task_id!r} was issued for dispatch arguments "
            f"{record.get('advisory_binding_sha256')!r}, not {binding_sha256}",
        )
    result_path = state_path.with_suffix(".result")
    recorded_result = record.get("result_file")
    if not isinstance(recorded_result, str) or Path(recorded_result).resolve() != result_path.resolve():
        raise AdvisoryRefused(
            RESULT_UNREADABLE,
            f"advisory task {advisor_task_id!r} result_file {recorded_result!r} is not its canonical result",
        )
    seal = record.get(SEAL_FIELD)
    if not isinstance(seal, dict):
        raise AdvisoryRefused(
            SEAL_MISSING, f"advisory task {advisor_task_id!r} has no finish-time {SEAL_FIELD} for its result"
        )
    if canonical_model_id(seal.get("advisor_model")) != policy.advisor_model_id:
        raise AdvisoryRefused(
            SEAL_MISMATCH,
            f"advisory task {advisor_task_id!r} result was sealed by {seal.get('advisor_model')!r}, "
            f"not the advisor {policy.advisor_model_id}",
        )
    if seal.get("run_nonce") != record.get("run_nonce"):
        raise AdvisoryRefused(
            SEAL_MISMATCH,
            f"advisory task {advisor_task_id!r} seal is from run {seal.get('run_nonce')!r}, "
            f"not the recorded run {record.get('run_nonce')!r}",
        )
    try:
        result_bytes = result_path.read_bytes()
        result_text = result_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AdvisoryRefused(RESULT_UNREADABLE, f"advisory task {advisor_task_id!r} result: {exc}") from None
    result_sha256 = hashlib.sha256(result_bytes).hexdigest()
    if seal.get("result_sha256") != result_sha256:
        raise AdvisoryRefused(
            SEAL_MISMATCH,
            f"advisory task {advisor_task_id!r} result hashes to {result_sha256}, "
            f"not the {seal.get('result_sha256')!r} its advisor sealed at finish",
        )
    envelope = parse_envelope(result_text, repo_root=repo_root, policy=policy)
    digest = envelope_sha256(envelope)
    if seal.get("envelope_sha256") != digest:
        raise AdvisoryRefused(
            SEAL_MISMATCH,
            f"advisory task {advisor_task_id!r} envelope hashes to {digest}, "
            f"not the {seal.get('envelope_sha256')!r} its advisor sealed at finish",
        )
    if envelope[BINDING_FIELD] != binding_sha256:
        raise AdvisoryRefused(
            BINDING_MISMATCH,
            f"the envelope is bound to dispatch arguments {envelope[BINDING_FIELD]}, not {binding_sha256}",
        )
    return ValidatedEnvelope(
        advisor_task_id=advisor_task_id,
        advisor_model=str(recorded_model),
        advisor_run_nonce=record.get("run_nonce"),
        result_path=str(result_path),
        result_sha256=result_sha256,
        envelope=envelope,
        envelope_sha256=digest,
        binding_sha256=binding_sha256,
    )


def require_unchanged(validated: ValidatedEnvelope, current: ValidatedEnvelope) -> None:
    """Refuse when the advisor record or result changed between validation and spawn."""
    if (current.result_sha256, current.envelope_sha256, current.advisor_run_nonce) != (
        validated.result_sha256,
        validated.envelope_sha256,
        validated.advisor_run_nonce,
    ):
        raise AdvisoryRefused(
            ENVELOPE_CHANGED,
            f"advisory task {validated.advisor_task_id!r} result changed after validation "
            f"(sha256 {validated.result_sha256} → {current.result_sha256})",
        )


def require_owned_paths_match(envelope_paths: Sequence[str], dispatch_paths: Sequence[str] | None) -> None:
    """The envelope's owned paths are the dispatch's ``--owned-path`` set, exactly."""
    declared = sorted({str(path).strip() for path in dispatch_paths or []})
    if declared != sorted(set(envelope_paths)):
        raise AdvisoryRefused(
            OWNED_PATHS_MISMATCH,
            f"--owned-path {declared} must equal the envelope owned_paths {sorted(set(envelope_paths))}",
        )


def _require_digest(admitted: Mapping[str, Any], field: str) -> str:
    value = admitted.get(field)
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise AdvisoryRefused(ADMISSION_INVALID, f"the recorded admission's {field} is not a sha256 digest")
    return value


def _verify_exemption(
    record: Mapping[str, Any],
    exemption: Mapping[str, Any],
    *,
    model_id: str,
    mode: str,
    repo_root: Path,
    policy: BoundedExecutionPolicy,
) -> None:
    """The recorded Ukrainian exemption still classifies this launch as non-bounded in ``repo_root``."""
    classified = exemption.get("classified_paths")
    if not isinstance(classified, list) or not all(isinstance(path, str) for path in classified):
        raise AdvisoryRefused(ADMISSION_INVALID, "the recorded exemption has no classified path list")
    owned = record.get("owned_paths") or []
    if (
        exemption.get("model_id") != model_id
        or exemption.get("mode") != mode
        or exemption.get("review_profile") != record.get("review_profile")
        or not isinstance(owned, list)
        or not set(map(str, owned)) <= set(classified)
    ):
        raise AdvisoryRefused(
            ADMISSION_INVALID, "the recorded exemption does not describe this task's model, mode, profile or paths"
        )
    requirement = bounded_requirement(
        model_id,
        mode=mode,
        task_family=exemption.get("task_family"),
        review_profile=exemption.get("review_profile"),
        owned_paths=classified,
        repo_root=repo_root,
        policy=policy,
    )
    if requirement is not None:
        raise AdvisoryRefused(ENVELOPE_REQUIRED, f"{requirement}; the recorded exemption does not hold")


# Stands in for the brief when the dispatcher blocks around it are rebuilt; a
# NUL byte never occurs in a dispatcher block.
_BRIEF_PLACEHOLDER = "\0bounded-advisory-brief\0"

PromptComposer = Callable[[str, ValidatedEnvelope, Mapping[str, Any]], str]


def _bound_execution_value(field: str, value: Any) -> Any:
    """A bound dispatch argument as the worker receives it (an empty effort or provider is not passed on)."""
    if field in {"effort", "provider"}:
        return value or None
    if field == "finalize_open_pr":
        return bool(value)
    return value


def _same_cwd(left: Any, right: Any) -> bool:
    return isinstance(left, str) and isinstance(right, str) and Path(left).resolve() == Path(right).resolve()


def _is_primary_read_only_worktree(
    admitted: Mapping[str, Any],
    args: Mapping[str, Any],
    record: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> bool:
    """#10025: a bound primary-root read runs in its exact automatic detached checkout."""
    root = admitted.get("repo_root")
    cwd = args.get("cwd")
    task_id = record.get("task_id")
    agent = execution.get("agent")
    if (
        execution.get("mode") != "read-only"
        or args.get("branch")
        or args.get("pr")
        or record.get("worktree_branch") is not None
        or not (
            (isinstance(cwd, str) and Path(cwd).is_absolute() and _same_cwd(cwd, root))
            or (
                record.get("read_only_primary_cwd") is True
                and isinstance(cwd, str)
                and Path(cwd) == Path(".")
            )
        )
        or not isinstance(root, str)
        or not isinstance(task_id, str)
        or not isinstance(agent, str)
    ):
        return False
    expected = automatic_worktree_path(agent, task_id, repo_root=Path(root))
    return _same_cwd(str(expected), execution.get("cwd")) and _same_cwd(
        record.get("worktree_path"),
        execution.get("cwd"),
    )


def _require_execution(
    admitted: Mapping[str, Any],
    args: Mapping[str, Any],
    record: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
    envelope_paths: Sequence[str],
) -> None:
    """The worker runs the admitted launch: every ``EXECUTION_FIELDS`` value, the bound arguments and owned scope.

    ``execution`` is what the worker is about to run. Each value must equal the
    one recorded at admission, and each that a dispatch argument sets must
    equal that bound argument, whose digest the envelope binds. The cwd is
    always compared: with the admitted cwd, with the recorded worktree, and with
    a bound ``--cwd`` when no worktree was requested. A read-only primary-root
    binding must instead resolve to its exact automatic detached worktree.
    """
    recorded = admitted.get("admitted_execution")
    if not isinstance(recorded, dict) or set(recorded) != set(EXECUTION_FIELDS):
        raise AdvisoryRefused(ADMISSION_INVALID, "the recorded admission carries no complete admitted execution")
    mismatches: list[str] = []
    for field in EXECUTION_FIELDS:
        actual, allowed = execution[field], recorded[field]
        if not (_same_cwd(actual, allowed) if field == "cwd" else actual == allowed):
            mismatches.append(f"{field} {actual!r} is not the admitted {allowed!r}")
    for field in _BOUND_EXECUTION_ARGS:
        if field in args and _bound_execution_value(field, args[field]) != execution[field]:
            mismatches.append(f"{field} {execution[field]!r} is not the bound argument {args[field]!r}")
    bound_paths = sorted({str(path).strip() for path in _as_list(args.get("owned_path")) if str(path).strip()})
    if bound_paths != sorted(set(envelope_paths)):
        mismatches.append(f"bound --owned-path {bound_paths} is not the envelope owned_paths")
    worktree = record.get("worktree_path")
    if worktree is not None and not _same_cwd(str(worktree), execution["cwd"]):
        mismatches.append(f"cwd {execution['cwd']!r} is not the admitted worktree {worktree!r}")
    bound_cwd = args.get("cwd")
    if not args.get("worktree") and bound_cwd is not None:
        if execution.get("mode") == "read-only" and (
            (Path(str(bound_cwd)).is_absolute() and _same_cwd(str(bound_cwd), admitted.get("repo_root")))
            or record.get("read_only_primary_cwd") is True
        ):
            if not _is_primary_read_only_worktree(admitted, args, record, execution):
                mismatches.append("cwd is not the automatic worktree of the bound primary --cwd")
        elif not _same_cwd(str(bound_cwd), execution["cwd"]):
            mismatches.append(f"cwd {execution['cwd']!r} is not the bound --cwd {bound_cwd!r}")
    if mismatches:
        raise AdvisoryRefused(EXECUTION_MISMATCH, "; ".join(mismatches))


def _require_bound_prompt(prompt: str, *, prompt_sha256: str, compose: Callable[[str], str]) -> str:
    """Refuse unless ``prompt`` is the bound brief inside the dispatcher blocks; returns the checked bytes' SHA-256.

    The dispatcher blocks are rebuilt around a placeholder brief; the text
    between them in ``prompt`` must hash to the bound ``prompt_sha256``, and
    rebuilding the prompt around that brief must give back ``prompt`` byte for
    byte, so any appended, prepended or altered instruction refuses.
    """
    head, found, tail = compose(_BRIEF_PLACEHOLDER).partition(_BRIEF_PLACEHOLDER)
    prompt_bytes = prompt.encode("utf-8")
    if not found or len(prompt) < len(head) + len(tail) or not prompt.startswith(head) or not prompt.endswith(tail):
        raise AdvisoryRefused(
            BINDING_MISMATCH, "the worker's prompt is not the bound brief within the permitted dispatcher blocks"
        )
    brief = prompt[len(head) : len(prompt) - len(tail)]
    if hashlib.sha256(brief.encode("utf-8")).hexdigest() != prompt_sha256:
        raise AdvisoryRefused(BINDING_MISMATCH, "the brief in the worker's prompt is not the brief the envelope binds")
    if compose(brief).encode("utf-8") != prompt_bytes:
        raise AdvisoryRefused(
            BINDING_MISMATCH, "the worker's prompt is not the bound brief within the permitted dispatcher blocks"
        )
    return hashlib.sha256(prompt_bytes).hexdigest()


def verify_worker_admission(
    record: Mapping[str, Any] | None,
    *,
    agent: str | None,
    model_id: str | None,
    mode: str,
    cwd: Path,
    execution: Mapping[str, Any],
    prompt: str,
    compose_prompt: PromptComposer,
    state_path_for: Callable[[str], Path],
    default_repo_root: Path,
    policy: BoundedExecutionPolicy | None = None,
) -> str | None:
    """The worker's backstop: refuse to start a bounded model its parent did not admit.

    ``record`` is the worker's own task record and ``prompt`` the exact text it
    hands the provider; the caller checks and submits the same object. A
    bounded-worker model runs only when the record carries the parent's
    admission and all of it re-verifies now: the recorded dispatch arguments
    hash to the argument half of the binding, the binding re-derives, the
    advisor's sealed result still loads and binds, the recorded ceilings and
    owned paths are the envelope's, the launch is the admitted one (every
    ``EXECUTION_FIELDS`` value, the bound arguments that set them, and the owned
    paths), and ``prompt`` is the envelope-bound brief
    inside exactly the blocks ``compose_prompt(brief, envelope, args)``
    rebuilds. The record's own prompt digests are never trusted for that.
    A Gemini Flash launch runs either with such an admission or with a
    recorded Ukrainian exemption that still classifies as non-bounded in
    ``cwd``.

    ``execution`` holds the remaining ``EXECUTION_FIELDS`` values the worker
    is about to run (effort, timeouts, budget, provider, harness, PR opening).

    Returns the SHA-256 of the checked prompt bytes for an envelope admission,
    None otherwise.
    """
    policy = policy or bounded_execution_policy()
    actual = {"agent": agent, "model_id": model_id, "mode": mode, "cwd": str(cwd), **execution}
    if set(actual) != set(EXECUTION_FIELDS):
        raise ValueError(f"agent, model_id, mode, cwd and execution must give exactly {list(EXECUTION_FIELDS)}")
    if model_id not in {policy.bounded_worker_model_id, policy.bounded_fallback_model_id}:
        return None
    if not record:
        raise AdvisoryRefused(ADMISSION_MISSING, f"{model_id} has no task record carrying a parent admission")
    if record.get("mode") != mode:
        raise AdvisoryRefused(ADMISSION_INVALID, f"the task record's mode {record.get('mode')!r} is not {mode!r}")
    admitted = record.get("advisory_envelope")
    if admitted is None and model_id == policy.bounded_fallback_model_id:
        exemption = record.get("advisory_exemption")
        if isinstance(exemption, dict):
            _verify_exemption(record, exemption, model_id=model_id, mode=mode, repo_root=cwd, policy=policy)
            return None
    if not isinstance(admitted, dict):
        raise AdvisoryRefused(
            ADMISSION_MISSING, f"{model_id} is a bounded model and its task record carries no advisory admission"
        )
    advisor_task_id = admitted.get("advisor_task_id")
    if not isinstance(advisor_task_id, str) or not advisor_task_id.strip():
        raise AdvisoryRefused(ADMISSION_INVALID, "the recorded admission names no advisor task")
    args_sha256 = _require_digest(admitted, "advisory_args_sha256")
    prompt_sha256 = _require_digest(admitted, "prompt_sha256")
    binding = _require_digest(admitted, BINDING_FIELD)
    args = admitted.get("advisory_args")
    if not isinstance(args, dict):
        raise AdvisoryRefused(ADMISSION_INVALID, "the recorded admission carries no dispatch arguments")
    if canonical_sha256(args) != args_sha256:
        raise AdvisoryRefused(BINDING_MISMATCH, "the recorded dispatch arguments do not hash to the bound digest")
    if binding_digest(args_sha256, prompt_sha256) != binding:
        raise AdvisoryRefused(
            BINDING_MISMATCH, "the recorded binding does not derive from its argument and prompt digests"
        )
    if record.get("prompt_sha256") != prompt_sha256:
        raise AdvisoryRefused(BINDING_MISMATCH, "the task's prompt is not the prompt the envelope was bound to")
    repo_root = admitted.get("repo_root")
    current = load_envelope(
        advisor_task_id,
        state_path=state_path_for(advisor_task_id),
        binding_sha256=binding,
        repo_root=Path(repo_root) if isinstance(repo_root, str) and repo_root else default_repo_root,
        policy=policy,
    )
    recorded = (
        admitted.get("result_sha256"),
        admitted.get("envelope_sha256"),
        admitted.get("advisor_run_nonce"),
        admitted.get("max_changed_files"),
        admitted.get("max_non_test_loc"),
        sorted(map(str, admitted.get("owned_paths") or [])),
    )
    now = (
        current.result_sha256,
        current.envelope_sha256,
        current.advisor_run_nonce,
        current.envelope["max_changed_files"],
        current.envelope["max_non_test_loc"],
        sorted(current.owned_paths),
    )
    if recorded != now:
        raise AdvisoryRefused(
            ENVELOPE_CHANGED,
            f"the recorded admission of advisory task {advisor_task_id!r} no longer matches its sealed envelope",
        )
    require_owned_paths_match(current.owned_paths, record.get("owned_paths"))
    _require_execution(admitted, args, record, execution=actual, envelope_paths=current.owned_paths)
    return _require_bound_prompt(
        prompt, prompt_sha256=prompt_sha256, compose=lambda brief: compose_prompt(brief, current, args)
    )


def worker_prompt_block(validated: ValidatedEnvelope) -> str:
    """The envelope as the bounded worker reads it, ceilings included."""
    envelope = validated.envelope

    def bullets(field: str) -> str:
        return "\n".join(f"- {item}" for item in envelope[field])

    return (
        "\n\n## Advisory envelope (bounded worker)\n\n"
        f"Issued by advisory task `{validated.advisor_task_id}` on {validated.advisor_model} "
        f"(result sha256 `{validated.result_sha256}`). Work only within it.\n\n"
        f"Task contract: {envelope['task_contract']}\n\n"
        f"Owned paths:\n{bullets('owned_paths')}\n\n"
        f"Scope ceilings, checked when the task finalizes (exceeding either fails the task): "
        f"at most {envelope['max_changed_files']} changed files and at most "
        f"{envelope['max_non_test_loc']} changed non-test lines (added plus deleted).\n\n"
        f"Constraints:\n{bullets('constraints')}\n\n"
        f"Risk boundaries:\n{bullets('risk_boundaries')}\n\n"
        f"Acceptance evidence:\n{bullets('acceptance_evidence')}\n\n"
        f"Escalation triggers — stop and report instead of continuing when:\n{bullets('escalation_triggers')}\n"
    )


def advisor_prompt_block(binding_sha256: str, policy: BoundedExecutionPolicy | None = None) -> str:
    """How the advisor must write its envelope so the bounded dispatch can admit it."""
    policy = policy or bounded_execution_policy()
    fields = ", ".join(f"`{field}`" for field in policy.advisor_output_fields)
    return (
        "\n\n## Advisory envelope output contract\n\n"
        f"You are the {policy.advisor_role} advisor for one bounded-worker dispatch. End your reply with "
        f"exactly one fenced block whose info string is `{ENVELOPE_FENCE}`, holding one JSON object with "
        f"exactly these keys: {fields}, and `{BINDING_FIELD}`.\n"
        "- `task_contract`: non-empty string.\n"
        "- `owned_paths`: non-empty list of repo-relative paths (dir/, dir/**, file or glob) under existing "
        "top-level roots; it must equal the worker dispatch's --owned-path set.\n"
        "- `max_changed_files`, `max_non_test_loc`: positive integers; the worker fails if it exceeds them.\n"
        "- `constraints`, `risk_boundaries`, `acceptance_evidence`, `escalation_triggers`: non-empty lists of "
        "non-empty strings.\n"
        f"- `{BINDING_FIELD}`: exactly `{binding_sha256}`.\n"
    )


def parse_numstat_z(text: str) -> list[tuple[int | None, int | None, str]]:
    """``git diff --numstat -z --no-renames`` entries: (added, deleted, path); binary counts are None."""
    entries: list[tuple[int | None, int | None, str]] = []
    for record in text.split("\0"):
        if not record:
            continue
        parts = record.split("\t", 2)
        if len(parts) != 3:
            raise ValueError(f"unexpected numstat record {record!r}")
        added, deleted, path = parts
        entries.append((None if added == "-" else int(added), None if deleted == "-" else int(deleted), path))
    return entries


def is_test_path(path: str) -> bool:
    """A test file: under a ``tests`` directory, or named ``test_*``, ``*_test.*`` or ``conftest.py``."""
    parts = PurePosixPath(path).parts
    name = parts[-1] if parts else ""
    return "tests" in parts[:-1] or name.startswith("test_") or "_test." in name or name == "conftest.py"


def ceiling_verdict(
    entries: Sequence[tuple[int | None, int | None, str]],
    *,
    max_changed_files: int,
    max_non_test_loc: int,
) -> dict[str, Any]:
    """Compare a worker's changes with the envelope ceilings; ``exceeded`` lists each breach."""
    changed_files = len({path for _added, _deleted, path in entries})
    non_test_loc = sum((added or 0) + (deleted or 0) for added, deleted, path in entries if not is_test_path(path))
    exceeded: list[str] = []
    if changed_files > max_changed_files:
        exceeded.append(f"changed_files {changed_files} > max_changed_files {max_changed_files}")
    if non_test_loc > max_non_test_loc:
        exceeded.append(f"non_test_loc {non_test_loc} > max_non_test_loc {max_non_test_loc}")
    return {
        "measured": True,
        "changed_files": changed_files,
        "non_test_loc": non_test_loc,
        "max_changed_files": max_changed_files,
        "max_non_test_loc": max_non_test_loc,
        "exceeded": exceeded,
    }
