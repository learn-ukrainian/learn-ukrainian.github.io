#!/usr/bin/env python3
"""Record a completed branch-pinned cross-family review on its exact PR head."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.fleet_comms.review_publication import DEFAULT_STATUS_CONTEXT
from scripts.fleet_comms.review_publisher import post_commit_status
from scripts.opsec.prepublish import absolute_path_spans, normalize_for_scan, publication_boundary, publication_cli
from scripts.orchestration.integration_sweep import (
    MARKER_PREFIX,
    SHA,
    TRUSTED_ASSOCIATIONS,
    GitHubAdapter,
    SweepError,
    parse_marker,
)
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.publish.github import Request, request_run
from scripts.review.model_catalog import (
    REVIEW_ACTIVITY,
    VALID_CODEX_EFFORTS,
    activity_role_refusal,
    is_cursor_auto_selector,
    model_aliases,
)
from scripts.review.reviewer_resolver import (
    CURSOR_AUTO_UNION_FAMILY,
    FORMAL_CURSOR_REVIEW_DISPATCH_MODELS,
    FORMAL_CURSOR_REVIEW_MODELS,
    UNRESOLVED_AUTHOR_FAMILIES,
    canonical_cursor_review_model,
    resolve_author_family,
    resolve_family,
)

VERDICT_LINE = re.compile(r"(?im)^\s*VERDICT:\s*(APPROVE|APPROVED|REQUEST_CHANGES|CHANGES_REQUESTED|BLOCKED)\b")
NORMALIZED = {
    "APPROVE": "APPROVED",
    "APPROVED": "APPROVED",
    "REQUEST_CHANGES": "CHANGES_REQUESTED",
    "CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "BLOCKED": "BLOCKED",
}
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*\Z")
MAX_COMMENT_BYTES = 65_000
# Kimi CLI task records can identify the harness without naming its model;
# this harness is single-family and always runs Moonshot models.
SINGLE_FAMILY_HARNESSES = {"kimi": "moonshot"}
# ``resolved_model_source`` values the Cursor adapter writes only when the model
# came out of the runtime's own output (``scripts/agent_runtime/adapters/cursor.py``
# ``parse``: stream-json stdout, this invocation's transcript, stderr JSON events).
# The ``unattested-harness`` / ``pending`` / ``unknown`` fallbacks and any other
# value are not runtime reports, so a receipt carrying them proves no model.
RUNTIME_REPORTED_MODEL_SOURCES = frozenset({"cursor-stream-json", "cursor-transcript", "cursor-stderr-json"})
# Families the resolver never selects through a native harness: Grok reviews
# only through the attested Cursor seat and Kimi never reviews (core.md P2).
NATIVE_NON_REVIEWER_FAMILIES = frozenset({"xai", "moonshot"})


class RecordError(RuntimeError):
    """A review cannot be bound to a trustworthy exact-head verdict."""


def normalize_verdict(reply: str) -> str:
    tokens = {NORMALIZED[token.upper()] for token in VERDICT_LINE.findall(reply)}
    if len(tokens) != 1:
        raise RecordError("review reply has missing or ambiguous VERDICT token")
    return tokens.pop()


@publication_boundary(RecordError)
def _run_json(args: list[str], *, input_text: str | None = None) -> Any:
    try:
        process = request_run(args, input=input_text, capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RecordError("GitHub lookup or publication unavailable") from exc
    if process.returncode:
        raise RecordError((process.stderr or process.stdout or "GitHub command failed")[:500])
    try:
        return json.loads(process.stdout)
    except ValueError as exc:
        raise RecordError("GitHub returned invalid JSON") from exc


def _pages(args: list[str]) -> list[dict[str, Any]]:
    data = _run_json(Request(args.verb, **args.fields, paginate=True, slurp=True))
    if not isinstance(data, list) or not all(isinstance(page, list) for page in data):
        raise RecordError("paginated GitHub data incomplete")
    items = [item for page in data for item in page]
    if not all(isinstance(item, dict) for item in items):
        raise RecordError("paginated GitHub data malformed")
    return items


def _hot_or_archived(task_root: Path, name: str) -> Path:
    """``task_root / name``, else its copy in ``archive/`` (#8625), else the hot path."""
    hot = task_root / name
    archived = task_root / ARCHIVE_DIR_NAME / name
    return archived if not hot.exists() and archived.exists() else hot


def _merge_proof_object_store() -> Path:
    """Find the checkout's shared objects without running Git or reading config."""
    cwd = Path.cwd()
    for root in (cwd, *cwd.parents):
        marker = root / ".git"
        if marker.is_dir():
            git_dir = marker
        elif marker.is_file():
            text = marker.read_text(encoding="utf-8").strip()
            if not text.startswith("gitdir: ") or "\n" in text:
                raise OSError("invalid Git directory pointer")
            git_dir = (root / text[8:]).resolve(strict=True)
        else:
            continue
        common_file = git_dir / "commondir"
        if common_file.is_file():
            git_dir = git_dir / common_file.read_text(encoding="utf-8").strip()
        objects = (git_dir / "objects").resolve(strict=True)
        if not objects.is_dir():
            raise OSError("Git object store unavailable")
        return objects
    raise OSError("Git checkout unavailable")


def _is_clean_base_merge(entry: dict[str, Any], base_sha: str) -> bool:
    """Bind a conflict-free base merge to GitHub metadata and raw local objects."""
    commit_sha = entry.get("sha")
    commit_data = entry.get("commit")
    tree_data = commit_data.get("tree") if isinstance(commit_data, dict) else None
    tree = tree_data.get("sha") if isinstance(tree_data, dict) else None
    parent_data = entry.get("parents")
    if not isinstance(parent_data, list) or len(parent_data) != 2:
        return False
    parents = [parent.get("sha") if isinstance(parent, dict) else None for parent in parent_data]
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in [commit_sha, base_sha, tree, *parents]):
        return False
    git = ["git"]
    try:
        objects = _merge_proof_object_store()
        with TemporaryDirectory(prefix="cf-merge-") as isolated:
            # Construct a bare repository without importing init templates, config,
            # refs, grafts, attributes, or an index from the writable shared Git dir.
            proof_dir = Path(isolated)
            (proof_dir / "objects/info").mkdir(parents=True)
            (proof_dir / "refs").mkdir()
            (proof_dir / "HEAD").write_text("ref: refs/heads/proof\n", encoding="utf-8")
            (proof_dir / "config").write_text(
                "[core]\n\trepositoryformatversion = 0\n\tbare = true\n"
                # Commit graphs can also be read from the alternate object store.
                f"\tcommitGraph = false\n\tattributesFile = {os.devnull}\n",
                encoding="utf-8",
            )
            (proof_dir / "objects/info/alternates").write_text(
                json.dumps(str(objects), ensure_ascii=False) + "\n", encoding="utf-8"
            )
            env = {
                **{key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
                "GIT_DIR": isolated,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": str(proof_dir / "no-global-config"),
                "GIT_ATTR_NOSYSTEM": "1",
                "GIT_NO_LAZY_FETCH": "1",
            }
            commit = subprocess.run(
                [*git, "cat-file", "commit", commit_sha],
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            headers = commit.stdout.partition("\n\n")[0].splitlines()
            if [line[5:] for line in headers if line.startswith("tree ")] != [tree]:
                return False
            if [line[7:] for line in headers if line.startswith("parent ")] != parents:
                return False
            base = subprocess.run(
                [*git, "cat-file", "-e", f"{base_sha}^{{commit}}"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if base.returncode:
                raise RecordError("base object not available locally; fetch and retry")
            subprocess.run(
                [*git, "merge-base", "--is-ancestor", parents[1], base_sha],
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            merged = subprocess.run(
                [*git, "merge-tree", "--write-tree", "--no-messages", *parents],
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        # Missing objects, conflicts, unsupported Git, and timeouts prove no exemption.
        return False
    return merged.stdout.strip() == tree


def _names_catalog_model(text: str) -> bool:
    """True when ``text`` is a catalog model identity, optionally with an effort suffix.

    Unlike ``canonical_model_id`` this never reads a longer name such as a task
    title (``gpt-6.1-sol-fix-thing``, ``9714-opus-finish``) as a model.
    """
    aliases = {alias.casefold() for alias in model_aliases()}
    base, _, effort = text.casefold().rpartition("-")
    return text.casefold() in aliases or (effort in VALID_CODEX_EFFORTS and base in aliases)


def _author_task_family(harness: str, task_id: str, repository: str, task_root: Path) -> str | None:
    """The family recorded by the task(s) a ``harness/task_id`` trailer names; None if no record exists.

    Delegate strips the dispatching agent from the trailer, so ``cursor-9714-x``
    and ``cursor/9714-x`` both sign ``cursor/9714-x``; a legacy unprefixed
    ``9714-x`` record signs the same. Every record present must agree.
    """
    families = set()
    for name in dict.fromkeys((f"{harness}-{task_id}", f"{harness}/{task_id}", task_id)):
        if not TASK_ID.fullmatch(name):
            continue
        task_file = _hot_or_archived(task_root, f"{name}.json")
        if not task_file.resolve().is_relative_to(task_root.resolve()):
            raise RecordError("author task provenance unavailable")
        if not task_file.exists():
            continue
        try:
            author_task = json.loads(task_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RecordError("author task provenance unavailable") from exc
        if not isinstance(author_task, dict):
            raise RecordError("author task provenance unavailable")
        if author_task.get("repository") != repository or not str(author_task.get("agent") or "").startswith(harness):
            raise RecordError("author task provenance conflicts with commit trailer")
        if harness.startswith("cursor"):
            if author_task.get("resolved_model_known") is not True:
                raise RecordError("author family unknown")
            author_model = author_task.get("resolved_model")
        else:
            author_model = author_task.get("model")
        families.add(resolve_author_family(str(author_model or "")))
    if len(families) > 1:
        raise RecordError("author task provenance conflicts across task records")
    return families.pop() if families else None


def author_families(repository: str, pr_number: int, task_root: Path) -> set[str]:
    """Resolve authored commits; exempt only Git-proven clean base merges, fail closed."""
    commits = _pages(Request("read-commits", repo=repository, number=pr_number))
    if not commits:
        raise RecordError("PR commit set unavailable")
    families = set()
    base_sha = None
    for entry in commits:
        message = (entry.get("commit") or {}).get("message")
        if not isinstance(message, str):
            raise RecordError("commit message unavailable")
        trailers = re.findall(r"(?m)^X-Agent:\s*([^\s]+)\s*$", message)
        if not trailers and not re.search(r"(?m)^X-Agent:", message):
            commit_sha = entry.get("sha")
            if isinstance(commit_sha, str) and SHA.fullmatch(commit_sha):
                if base_sha is None:
                    pr = _run_json(["gh", "pr", "view", str(pr_number), "--repo", repository, "--json", "baseRefOid"])
                    base_sha = pr.get("baseRefOid") if isinstance(pr, dict) else None
                    if not isinstance(base_sha, str) or not SHA.fullmatch(base_sha):
                        raise RecordError("PR base SHA unavailable; cannot prove clean base merge")
                if _is_clean_base_merge(entry, base_sha):
                    continue
        if len(trailers) != 1 or "/" not in trailers[0]:
            raise RecordError("author model unknown: missing explicit X-Agent model trailer")
        harness, model = trailers[0].split("/", 1)
        if not harness or not model or not TASK_ID.fullmatch(model):
            raise RecordError("author model unknown")
        # The common X-Agent trailer names a task, whose recorded model decides
        # before any reading of the trailer text as a model name.
        family = _author_task_family(harness, model, repository, task_root)
        if family is None:
            if _names_catalog_model(model) or is_cursor_auto_selector(model):
                # Cursor has historically required harness-aware resolution.
                family = resolve_author_family(f"{harness}:{model}" if harness == "cursor" else model)
            elif harness in SINGLE_FAMILY_HARNESSES:
                family = SINGLE_FAMILY_HARNESSES[harness]
            else:
                raise RecordError("author task provenance unavailable")
        if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
            raise RecordError("author family unknown")
        if family == CURSOR_AUTO_UNION_FAMILY:
            raise RecordError("author family mixed or unknown")
        families.add(family)
    if not families:
        raise RecordError("PR has no attributed author commits")
    return families


def _repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True, timeout=30
        )
    except subprocess.TimeoutExpired as exc:
        raise RecordError("Git repository lookup timed out after 30 seconds") from exc
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RecordError("Git repository lookup failed") from exc
    return Path(result.stdout.strip()).resolve().parent


@contextmanager
def sha_lock(repository: str, sha: str, lock_root: Path):
    lock_root.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(f"{repository}\0{sha}".encode()).hexdigest() + ".lock"
    with (lock_root / name).open("a+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def build_comment(*, sha: str, task_id: str, started: str, verdict: str, model: str, family: str, reply: str) -> str:
    if MARKER_PREFIX in reply:
        raise RecordError("review reply contains reserved verdict marker")
    marker = f"<!-- cf-verdict v1 sha={sha} task={task_id} started={started} verdict={verdict} model={model} family={family} -->"
    prefix = (
        "### Cross-family review\n"
        f"head: {sha}\n"
        f"Reviewer family: {family}\n"
        f"VERDICT: {verdict}\n"
        f"Reviewer model: {model}\n"
        f"Task id: {task_id}\n\n"
        "<details><summary>Reviewer's reply</summary>\n\n"
    )
    suffix = f"\n\n</details>\n\n{marker}"
    available = MAX_COMMENT_BYTES - len((prefix + suffix).encode())
    if available < 0:
        raise RecordError("comment metadata exceeds GitHub limit")
    if len(reply.encode()) > available:
        flag = "\n\n[Review reply truncated to fit GitHub's comment limit.]"
        available -= len(flag.encode())
        if available < 0:
            raise RecordError("comment metadata exceeds GitHub limit")
        reply = reply.encode()[:available].decode("utf-8", errors="ignore") + flag
    return prefix + reply + suffix


def repository_relative_reply(reply: str, *, task: dict[str, Any], primary_root: Path) -> str:
    """Rewrite checkout citations on scanner-stable lines; scan the final text."""
    checkout = task.get("worktree_path")
    roots = [primary_root]
    if isinstance(checkout, str) and Path(checkout).is_absolute():
        roots.insert(0, Path(checkout))

    def replace(token: str) -> str:
        # The scanner alone owns boundaries. Only interpret a terminal citation
        # annotation, and resolve the actual cited file rather than a suffixed name.
        filename, colon, annotation = token.partition(":")
        suffix = colon + annotation
        if suffix and not re.fullmatch(r":[1-9][0-9]*(?::[1-9][0-9]*)?", suffix):
            return token
        path = Path(filename)
        # Do not hide an escape or change the meaning of a symlink/.. walk.
        if ".." in path.parts:
            return token
        for root in roots:
            if not path.is_relative_to(root):
                continue
            try:
                resolved_root = root.resolve(strict=True)
                resolved_primary = primary_root.resolve(strict=True)
                if (
                    not resolved_primary.is_dir()
                    or not resolved_root.is_dir()
                    or resolved_root == Path(resolved_root.anchor)
                    or not resolved_root.is_relative_to(resolved_primary)
                ):
                    continue
                # Resolve parents to reject escapes, but cite the final directory
                # entry itself: the project interpreter can link outside the repo.
                resolved_path = resolved_root if path == root else path.parent.resolve(strict=True) / path.name
                if not resolved_path.is_relative_to(resolved_root):
                    return token
                mode = resolved_path.lstat().st_mode
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode) or stat.S_ISLNK(mode)):
                    return token
                if suffix and (not stat.S_ISREG(mode) or Path(token).exists() or Path(token).is_symlink()):
                    return token
            except (OSError, RuntimeError, ValueError):
                return token
            return path.relative_to(root).as_posix() + suffix
        return token

    # Normalization can compose across a token boundary or reveal traversal.
    # Preserve the entire altered line so its absolute paths reach the scanner.
    lines = []
    for line in reply.splitlines(keepends=True):
        rewritten = line
        spans = absolute_path_spans(line)
        if normalize_for_scan(line) == line:
            for start, end in reversed(spans):
                rewritten = rewritten[:start] + replace(line[start:end]) + rewritten[end:]
            if normalize_for_scan(rewritten) != rewritten:
                rewritten = line
        lines.append(rewritten)
    return "".join(lines)


def _task(task_id: str, task_root: Path) -> tuple[dict[str, Any], str]:
    if not TASK_ID.fullmatch(task_id):
        raise RecordError("invalid task id")
    task_path = _hot_or_archived(task_root, f"{task_id}.json")
    # An archived review keeps its reply beside its record.
    result_path = task_path.with_suffix(".result")
    try:
        task = json.loads(task_path.read_text(encoding="utf-8"))
        reply = result_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise RecordError("review task record or reply unavailable") from exc
    if not isinstance(task, dict):
        raise RecordError("review task record malformed")
    if task.get("status") != "done":
        raise RecordError("review task is not done")
    if not task.get("worktree_branch"):
        raise RecordError("review was not branch-pinned; re-run with --branch <PR head ref>")
    return task, reply


def _pr(repository: str, branch: str, number: int | None) -> dict[str, Any]:
    if number is None:
        matches = _run_json(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository,
                "--state",
                "open",
                "--head",
                branch,
                "--limit",
                "2",
                "--json",
                "number,headRefOid,headRefName",
            ]
        )
        if not isinstance(matches, list) or len(matches) != 1:
            raise RecordError("branch must identify exactly one open PR; pass --pr N")
        return matches[0]
    data = _run_json(
        ["gh", "pr", "view", str(number), "--repo", repository, "--json", "number,headRefOid,headRefName,state"]
    )
    if not isinstance(data, dict) or data.get("state") != "OPEN":
        raise RecordError("PR is not open")
    return data


def _cursor_requested_model(task: dict[str, Any], reported: object) -> object:
    """Return the slug a Cursor review was dispatched with (#9714).

    Once the runtime reports, delegate overwrites ``model`` with that report, so the
    adapter's ``substitution`` request is the surviving pin; records without one
    keep ``model``. Present request metadata must name a Cursor request and agree
    with a still-pinned ``model``, and the runtime's own report never stands in
    for the request. A preflight agent substitution onto Cursor keeps its routing
    record outermost and nests this run's adapter receipt under
    ``runtime_attribution`` (``delegate._merge_agent_substitution``); the nested
    receipt is the request, and must launch the routed slug and attest the report.
    """
    substitution = task.get("substitution")
    if isinstance(substitution, dict) and substitution.get("kind") == "agent-substitution":
        runtime = substitution.get("runtime_attribution")
        if (
            substitution.get("actual_agent") != "cursor"
            or not isinstance(runtime, dict)
            or runtime.get("kind") is not None
            or runtime.get("actual_provider") != "cursor"
            or runtime.get("requested_model") != substitution.get("actual_model")
            or not isinstance(runtime.get("actual_model"), str)
            or runtime["actual_model"].strip() != reported
        ):
            raise RecordError("Cursor reviewer request metadata malformed")
        substitution = runtime
    if substitution is None:
        requested = task.get("model")
    else:
        requested = substitution.get("requested_model") if isinstance(substitution, dict) else None
        if (
            not isinstance(substitution, dict)
            or substitution.get("requested_provider") != "cursor"
            or not isinstance(requested, str)
            or not requested
            or requested != requested.strip()
        ):
            raise RecordError("Cursor reviewer request metadata malformed")
        pinned = task.get("model")
        if isinstance(pinned, str) and pinned in FORMAL_CURSOR_REVIEW_DISPATCH_MODELS and pinned != requested:
            raise RecordError(f"Cursor reviewer request ambiguous: model {pinned!r}, substitution {requested!r}")
    if isinstance(requested, str) and requested == reported:
        raise RecordError("Cursor reviewer request unknown: only the runtime report survives")
    return requested


def _require_formal_reviewer(*, cursor: bool, requested: object, reported: object, model: str, family: str) -> None:
    """Refuse a verdict from an identity the reviewer resolver never selects (#9488).

    Through Cursor only a pinned formal seat counts, and only when the runtime
    reported its display name (``"Grok 4.7 256K High"``, ``"Claude Opus 5.5 300K
    High"``): a bare or other-variant slug (``grok-4.7``, ``claude-opus-5-5-high``)
    attests no variant, and Composer and Auto are unpinned. Through any other harness Grok
    never judges and Kimi never reviews. A run requested with a formal seat's exact
    slug counts only when the runtime attests that same seat (#9714). On every
    harness the model must also hold a catalog review role (#9583), so Fable and
    retired models never approve.
    """
    if cursor:
        admitted = model in FORMAL_CURSOR_REVIEW_MODELS and reported != model
    else:
        admitted = family not in NATIVE_NON_REVIEWER_FAMILIES
    if not admitted:
        raise RecordError(f"reviewer model unknown: {model!r} is not a formal reviewer on this harness")
    expected = FORMAL_CURSOR_REVIEW_DISPATCH_MODELS.get(requested) if cursor and isinstance(requested, str) else None
    if expected is not None and model != expected:
        raise RecordError(f"Cursor reviewer model mismatch: requested {expected!r}, runtime attested {model!r}")
    # #9583: a model the catalog gives no review role never approves, on any harness.
    if refusal := activity_role_refusal(model, REVIEW_ACTIVITY):
        raise RecordError(f"reviewer model refused: {refusal}")


@publication_boundary(RecordError)
def record(
    task_id: str, *, pr_number: int | None = None, task_root: Path | None = None, lock_root: Path | None = None
) -> dict[str, Any]:
    root = _repo_root() if task_root is None or lock_root is None else None
    task_root = task_root or root / "batch_state" / "tasks"
    lock_root = lock_root or root / "batch_state" / "locks"
    task, reply = _task(task_id, task_root)
    repository = task.get("repository")
    branch = task["worktree_branch"]
    sha = task.get("worktree_base_sha")
    if not isinstance(repository, str) or "/" not in repository:
        raise RecordError("review repository unavailable")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise RecordError("reviewed SHA missing or invalid")
    cursor = task.get("agent") == "cursor"
    reported = task.get("resolved_model") if cursor else task.get("model")
    if cursor and task.get("resolved_model_known") is not True:
        raise RecordError("Cursor reviewer model unknown")
    source = task.get("resolved_model_source")
    if cursor and not (isinstance(source, str) and source in RUNTIME_REPORTED_MODEL_SOURCES):
        raise RecordError("Cursor reviewer model unattested: its source is not a runtime report")
    # Only Cursor's runtime reports display names; record its catalog id.
    model = canonical_cursor_review_model(reported) if cursor and isinstance(reported, str) else reported
    if not isinstance(model, str) or not model or re.search(r"\s", model):
        raise RecordError("reviewer model unknown")
    family = resolve_family(model)
    if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
        raise RecordError("reviewer family unknown")
    requested = _cursor_requested_model(task, reported) if cursor else task.get("model")
    _require_formal_reviewer(cursor=cursor, requested=requested, reported=reported, model=model, family=family)
    verdict = normalize_verdict(reply)
    started_dt = datetime.fromisoformat(str(task.get("started_at") or "").replace("Z", "+00:00"))
    if started_dt.tzinfo is None:
        raise RecordError("review start timestamp missing timezone")
    started = started_dt.astimezone(UTC).isoformat(timespec="microseconds")
    pr = _pr(repository, branch, pr_number)
    if pr.get("headRefName") != branch:
        raise RecordError("review branch does not match PR head ref")
    if pr.get("headRefOid") != sha:
        raise RecordError("PR head moved since review; re-run exact-head review")
    number = pr.get("number")
    if not isinstance(number, int) or number < 1:
        raise RecordError("PR number unavailable")
    families = author_families(repository, number, task_root)
    if family in families:
        raise RecordError("reviewer family equals an author family")
    adapter = GitHubAdapter(Path.cwd())
    login = adapter.identity()
    reply = repository_relative_reply(reply, task=task, primary_root=root or _repo_root())
    comment = build_comment(
        sha=sha, task_id=task_id, started=started, verdict=verdict, model=model, family=family, reply=reply
    )
    posted = False
    with sha_lock(repository, sha, lock_root):
        # The PR may move while an earlier recorder owns the lock.
        current = _pr(repository, branch, number)
        if current.get("headRefOid") != sha:
            raise RecordError("PR head moved before publication")
        try:
            comments = adapter.comments(repository, number)
        except SweepError as exc:
            raise RecordError(f"comment lookup failed: {exc}") from exc
        existing = None
        for item in comments:
            body = item.get("body")
            if not isinstance(body, str):
                raise RecordError("comment lookup partial")
            if MARKER_PREFIX in body:
                marker = parse_marker(body)
                if marker is None and f"sha={sha}" in body:
                    raise RecordError("unparseable marker on reviewed SHA")
                if (
                    marker
                    and marker["sha"] == sha
                    and marker["task"] == task_id
                    and item.get("user", {}).get("login") == login
                    and item.get("author_association") in TRUSTED_ASSOCIATIONS
                ):
                    if (
                        marker["started"] != started
                        or marker["verdict"] != verdict
                        or marker["model"] != model
                        or marker["family"] != family
                        or item.get("created_at") != item.get("updated_at")
                    ):
                        raise RecordError("existing verdict marker was edited or conflicts with task")
                    existing = item
                    break
        if existing is None:
            data = _run_json(
                Request("issue-comment-json", repo=repository, number=number, body=comment),
            )
            comment_id = data.get("id") if isinstance(data, dict) else None
            if not isinstance(comment_id, int):
                raise RecordError("comment post response lacked id; retry to reconcile")
            readback = _run_json(Request("read-comment", repo=repository, number=comment_id))
            if (
                not isinstance(readback, dict)
                or readback.get("body") != comment
                or readback.get("user", {}).get("login") != login
                or readback.get("author_association") not in TRUSTED_ASSOCIATIONS
                or readback.get("created_at") != readback.get("updated_at")
            ):
                raise RecordError("comment readback mismatch; publication state unknown")
            posted = True
        description = f"VERDICT: {verdict} {family} {task_id}"[:140]
        try:
            post_commit_status(
                repository=repository,
                head_sha=sha,
                state="success" if verdict == "APPROVED" else "failure",
                context=DEFAULT_STATUS_CONTEXT,
                description=description,
            )
            status = "posted"
        except Exception as exc:
            status = f"failed: {exc}"
    return {
        "pr": number,
        "head": sha,
        "task": task_id,
        "verdict": verdict,
        "comment": "posted" if posted else "existing",
        "status": status,
    }


@publication_cli(RecordError)
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish a completed exact-head cross-family verdict.\nUse after the reviewer exits; not to author or approve your own review.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/review/record_cf_verdict.py --task-id review-unit --pr 1\nOutputs and exit codes: Local publication receipt and GitHub review text/status. 0: recorded; 1: refused.\nRelated: #9297",
    )
    parser.add_argument("--task-id", required=True, help="Completed branch-pinned review task id")
    parser.add_argument("--pr", type=int, help="Open PR number; otherwise resolve from review branch")
    args = parser.parse_args(argv)
    try:
        result = record(args.task_id, pr_number=args.pr)
    except (RecordError, SweepError, ValueError) as exc:
        print(f"CF verdict refused: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "posted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
