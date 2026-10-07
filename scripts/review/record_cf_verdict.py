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
import time
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from learn_ukrainian_v4_runtime.agent_identity import normalize_seat
from learn_ukrainian_v4_runtime.model_families import canonical_cursor_model, is_cursor_auto_selector

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
    activity_role_refusal,
    load_model_catalog,
    resolve_catalog_model_id,
)
from scripts.review.reviewer_resolver import (
    FORMAL_CURSOR_REVIEW_MODELS,
    REVIEW_CANDIDATES,
    UNKNOWN_AUTHOR_FAMILY,
    UNRESOLVED_AUTHOR_FAMILIES,
    ResolverInputs,
    ReviewerResolution,
    evaluate_candidate,
    resolve_author_family,
    resolve_family,
    resolve_reviewer,
)
from scripts.review.security_paths import git_changed_paths, is_security_sensitive_change
from scripts.review.subject_seat import prepare_subject_exclusion
from scripts.review.target_resolution import TargetResolutionError
from scripts.review.verdict_parser import recognized_verdicts

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
# Kimi never reviews. Native Grok requires its own runtime attestation (#9769).
NATIVE_NON_REVIEWER_FAMILIES = frozenset({"xai", "moonshot"})


class RecordError(RuntimeError):
    """A review cannot be bound to a trustworthy exact-head verdict."""


def normalize_verdict(reply: str) -> str:
    tokens = {NORMALIZED[token.upper()] for token in recognized_verdicts(reply)}
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


def _merge_proof_object_store(start: Path | None = None) -> Path:
    """Find the checkout's shared objects without running Git or reading config."""
    cwd = start or Path.cwd()
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


def _is_clean_base_merge(entry: dict[str, Any], base_sha: str, *, checkout: Path | None = None) -> bool:
    """Bind a conflict-free base merge to commit metadata and raw local objects.

    ``checkout`` locates the object store; the default is the current directory.
    """
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
        objects = _merge_proof_object_store(checkout)
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


@dataclass(frozen=True)
class CommitAttribution:
    """One branch commit and the author family its provenance proves.

    ``family`` is None only for a Git-proven clean base merge, which authors nothing.
    """

    sha: str | None
    family: str | None
    source: str


def _attribute_commit(
    entry: dict[str, Any],
    *,
    repository: str,
    task_root: Path,
    base_sha: Callable[[], str],
    checkout: Path | None = None,
) -> CommitAttribution:
    """Resolve one commit's author family, retaining unresolvable authors as Unknown.

    ``entry`` has the GitHub commit-listing shape (``sha``, ``commit.message``,
    ``commit.tree.sha``, ``parents``). ``base_sha`` is called only when an
    untrailered commit needs the clean-merge proof.
    """
    commit_sha = entry.get("sha")
    message = (entry.get("commit") or {}).get("message")
    if not isinstance(message, str):
        raise RecordError("commit message unavailable")
    trailers = re.findall(r"(?m)^X-Agent:\s*([^\s]+)\s*$", message)
    if (
        not trailers
        and not re.search(r"(?m)^X-Agent:", message)
        and isinstance(commit_sha, str)
        and SHA.fullmatch(commit_sha)
        and _is_clean_base_merge(entry, base_sha(), checkout=checkout)
    ):
        return CommitAttribution(commit_sha, None, "clean-base-merge")
    if len(trailers) != 1 or "/" not in trailers[0]:
        raise RecordError("author model unknown: missing explicit X-Agent model trailer")
    harness, model = trailers[0].split("/", 1)
    if not harness or not model:
        raise RecordError("author model unknown")
    # Cursor has historically required harness-aware resolution; otherwise
    # resolve the model itself before consulting task provenance.
    family = resolve_author_family(f"{harness}:{model}" if harness == "cursor" else model)
    source = "trailer-model"
    if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
        if not TASK_ID.fullmatch(model):
            raise RecordError("author model unknown")
        task_file = _hot_or_archived(task_root, f"{model}.json")
        if not task_file.resolve().is_relative_to(task_root.resolve()):
            raise RecordError("author task provenance unavailable")
        if task_file.exists():
            # The common X-Agent trailer names a task, not a model. Resolve
            # that task's recorded model only after validating its provenance.
            try:
                author_task = json.loads(task_file.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise RecordError("author task provenance unavailable") from exc
            if (
                not isinstance(author_task, dict)
                or author_task.get("repository") != repository
                or not str(author_task.get("agent") or "").startswith(harness)
            ):
                raise RecordError("author task provenance conflicts with commit trailer")
            if harness.startswith("cursor") and is_cursor_auto_selector(author_task.get("model")):
                author_model = author_task["model"]
            elif harness.startswith("cursor"):
                author_model = (
                    author_task.get("resolved_model") if author_task.get("resolved_model_known") is True else None
                )
            else:
                author_model = author_task.get("model")
            family = resolve_author_family(str(author_model or ""))
            source = "task-record-archived" if task_file.parent.name == ARCHIVE_DIR_NAME else "task-record"
        elif harness in SINGLE_FAMILY_HARNESSES:
            family = SINGLE_FAMILY_HARNESSES[harness]
            source = "single-family-harness"
        else:
            family = UNKNOWN_AUTHOR_FAMILY
            source = "unresolved-author"
    if family in UNRESOLVED_AUTHOR_FAMILIES:
        # A committed author without a concrete identity is reviewable by any
        # known family (#9944). This does not grant Unknown a reviewer identity.
        family = UNKNOWN_AUTHOR_FAMILY
    return CommitAttribution(commit_sha if isinstance(commit_sha, str) else None, family, source)


def author_families(repository: str, pr_number: int, task_root: Path) -> set[str]:
    """Resolve a PR's GitHub-listed commits, including Unknown author families.

    A compatibility reader over :func:`_attribute_commit`. The recorder itself
    uses :func:`pr_review_facts`, which also binds the listing to the local
    ``git rev-list`` enumeration.
    """
    commits = _pages(Request("read-commits", repo=repository, number=pr_number))
    if not commits:
        raise RecordError("PR commit set unavailable")
    base: list[str] = []

    def base_sha() -> str:
        if not base:
            pr = _run_json(["gh", "pr", "view", str(pr_number), "--repo", repository, "--json", "baseRefOid"])
            value = pr.get("baseRefOid") if isinstance(pr, dict) else None
            if not isinstance(value, str) or not SHA.fullmatch(value):
                raise RecordError("PR base SHA unavailable; cannot prove clean base merge")
            base.append(value)
        return base[0]

    families = set()
    for entry in commits:
        family = _attribute_commit(entry, repository=repository, task_root=task_root, base_sha=base_sha).family
        if family is not None:
            families.add(family)
    if not families:
        raise RecordError("PR has no attributed author commits")
    return families


# --- complete branch review facts (#9739) ------------------------------------
#
# One calculation serves dispatch admission, reviewer selection and this
# recorder: every commit in ``git rev-list <base>..<head>`` (side parents
# included, no path filter or recent-commit limit), attributed exactly as the
# recorder attributes a commit, plus the incoming writer, plus the protected
# scope the whole branch and the proposed owned paths touch.

BRANCH_FACTS_TIMEOUT_S = 90.0
_GIT_STEP_TIMEOUT_S = 30.0
FACTS_AUTHORSHIP_UNKNOWN = "authorship_unknown"
FACTS_SCOPE_UNKNOWN = "scope_unknown"
FACTS_TARGET_UNKNOWN = "target_unknown"


class BranchFactsError(RecordError):
    """A branch review fact cannot be established; ``code`` names which one."""

    def __init__(self, code: str, message: str, *, timed_out: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.timed_out = timed_out


@dataclass(frozen=True)
class BranchReviewFacts:
    """Complete authorship and protected scope of one frozen branch target."""

    repository: str
    base_tip_sha: str
    head_sha: str
    merge_base_sha: str | None
    commits: tuple[CommitAttribution, ...]
    existing_families: frozenset[str]
    incoming_writer: str | None
    incoming_family: str | None
    changed_paths: tuple[str, ...]
    owned_paths: tuple[str, ...]
    subject_seats: frozenset[str]
    subject_families: frozenset[str]
    subject_evidence: tuple[str, ...]

    @property
    def author_families(self) -> frozenset[str]:
        """Every committed author family plus the incoming writer's (Cursor Auto stays its own family)."""
        incoming = frozenset({self.incoming_family}) if self.incoming_family else frozenset()
        return self.existing_families | incoming

    @property
    def excluded_families(self) -> frozenset[str]:
        """Every author family excluded from review, including Cursor Auto's own family."""
        return self.author_families

    @property
    def scope_paths(self) -> tuple[str, ...]:
        """Literal branch changes (both rename sides, deletions) plus the proposed owned paths."""
        return tuple(dict.fromkeys((*self.changed_paths, *self.owned_paths)))

    def resolver_inputs(self, *, risk: str, review_profile: str = "code", **overrides: Any) -> ResolverInputs:
        """Reviewer-resolver inputs carrying these facts; ``overrides`` set the remaining fields."""
        overrides.setdefault("domain", review_profile)
        overrides.setdefault("author_model", "")
        return ResolverInputs(
            author_families=self.author_families,
            review_profile=review_profile,
            risk=risk,
            changed_paths=self.changed_paths,
            owned_paths=self.scope_paths,
            subject_seats=self.subject_seats,
            subject_families=self.subject_families,
            subject_evidence=self.subject_evidence,
            **overrides,
        )

    def receipt(self) -> dict[str, Any]:
        """Privacy-safe summary for a dispatch or verdict record."""
        return {
            "repository": self.repository,
            "base_tip_sha": self.base_tip_sha,
            "head_sha": self.head_sha,
            "commits": len(self.commits),
            "existing_families": sorted(self.existing_families),
            "incoming_writer": self.incoming_writer,
            "incoming_family": self.incoming_family,
            "author_families": sorted(self.author_families),
            "subject_seats": sorted(self.subject_seats),
            "subject_families": sorted(self.subject_families),
            "scope_paths": len(self.scope_paths),
        }


def _facts_git(
    repo_root: Path, args: list[str], *, deadline: float, code: str, input_bytes: bytes | None = None
) -> bytes:
    """Run one bounded read-only Git step; a timeout or failure is an unknown fact, never a truncated one."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise BranchFactsError(code, "branch fact collection timed out; refusing a partial history", timed_out=True)
    # Ignore inherited Git redirection, replacement refs, grafts and commit
    # graphs: the enumeration must describe the repository's real objects.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_NO_REPLACE_OBJECTS": "1", "GIT_GRAFT_FILE": os.devnull})
    command = ["git", "-C", str(repo_root), "-c", "core.commitGraph=false", "--no-replace-objects", *args]
    try:
        proc = subprocess.run(
            command,
            input=input_bytes,
            capture_output=True,
            env=env,
            check=False,
            timeout=min(remaining, _GIT_STEP_TIMEOUT_S),
        )
    except subprocess.TimeoutExpired as exc:
        raise BranchFactsError(code, f"git {args[0]} timed out; refusing a partial history", timed_out=True) from exc
    except OSError as exc:
        raise BranchFactsError(code, f"git {args[0]} unavailable") from exc
    if proc.returncode:
        raise BranchFactsError(code, f"git {args[0]} failed")
    return proc.stdout


def _read_commit_entries(repo_root: Path, shas: list[str], *, deadline: float) -> list[dict[str, Any]]:
    """Read raw commits into the commit-listing shape :func:`_attribute_commit` takes."""
    if not shas:
        return []
    data = _facts_git(
        repo_root,
        ["cat-file", "--batch"],
        deadline=deadline,
        code=FACTS_AUTHORSHIP_UNKNOWN,
        input_bytes="".join(f"{sha}\n" for sha in shas).encode("ascii"),
    )
    entries: list[dict[str, Any]] = []
    position = 0
    try:
        for sha in shas:
            newline = data.index(b"\n", position)
            header = data[position:newline].decode("ascii").split()
            if len(header) != 3 or header[0] != sha or header[1] != "commit":
                raise BranchFactsError(FACTS_AUTHORSHIP_UNKNOWN, f"commit {sha[:12]} unavailable")
            size = int(header[2])
            body = data[newline + 1 : newline + 1 + size].decode("utf-8")
            position = newline + 1 + size + 1
            headers, _, message = body.partition("\n\n")
            lines = headers.splitlines()
            trees = [line[5:] for line in lines if line.startswith("tree ")]
            parents = [line[7:] for line in lines if line.startswith("parent ")]
            entries.append(
                {
                    "sha": sha,
                    "commit": {"message": message, "tree": {"sha": trees[0] if len(trees) == 1 else None}},
                    "parents": [{"sha": parent} for parent in parents],
                }
            )
    except (ValueError, UnicodeDecodeError) as exc:
        raise BranchFactsError(FACTS_AUTHORSHIP_UNKNOWN, "commit objects unreadable") from exc
    return entries


def incoming_writer_family(agent: str, model: str | None) -> str:
    """The family an incoming writer adds, resolved like a committed ``X-Agent: <agent>/<model>`` trailer.

    Cursor Auto resolves to its own Cursor family. Raises ``BranchFactsError``
    when the family is unknown.
    """
    harness = str(agent or "").strip().lower()
    concrete = str(model or "").strip()
    family = resolve_author_family(f"cursor:{concrete}" if harness == "cursor" else concrete)
    if (family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown") and harness in SINGLE_FAMILY_HARNESSES:
        family = SINGLE_FAMILY_HARNESSES[harness]
    if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
        raise BranchFactsError(
            FACTS_AUTHORSHIP_UNKNOWN, f"incoming writer family unknown ({harness}/{concrete or '(default)'})"
        )
    return family


def collect_branch_review_facts(
    *,
    repository: str,
    repo_root: Path,
    base_tip_sha: str,
    head_sha: str,
    task_root: Path,
    incoming_agent: str | None = None,
    incoming_model: str | None = None,
    owned_paths: Iterable[str] = (),
    subject_seats: Iterable[str] = (),
    subject_families: Iterable[str] = (),
    timeout_s: float = BRANCH_FACTS_TIMEOUT_S,
) -> BranchReviewFacts:
    """Collect complete authorship and protected scope for ``base_tip_sha..head_sha``.

    Commit membership is ``git rev-list <base>..<head>`` (A1), attributed by the
    recorder's own per-commit rules (trailer, hot or archived task record,
    Cursor attestation, single-family harness, Git-proven clean base merge).
    ``incoming_agent``/``incoming_model`` name the writer about to be
    dispatched, after any substitution. Scope is the literal diff against the
    merge-base (both rename sides and deletions) plus ``owned_paths``, with the
    subject seats ``prepare_subject_exclusion`` derives from it. A fresh branch
    passes ``head_sha == base_tip_sha``. Reads only; never fetches. Raises
    ``BranchFactsError`` (``code`` = authorship, scope or target unknown).
    """
    deadline = time.monotonic() + timeout_s
    for label, sha in (("base", base_tip_sha), ("head", head_sha)):
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise BranchFactsError(FACTS_TARGET_UNKNOWN, f"{label} SHA missing or invalid")
        try:
            _facts_git(repo_root, ["cat-file", "-e", f"{sha}^{{commit}}"], deadline=deadline, code=FACTS_TARGET_UNKNOWN)
        except BranchFactsError as exc:
            if exc.timed_out:
                raise
            raise BranchFactsError(
                FACTS_TARGET_UNKNOWN, f"{label} commit {sha[:12]} not available locally; fetch and retry"
            ) from exc
    listed = _facts_git(
        repo_root, ["rev-list", f"{base_tip_sha}..{head_sha}"], deadline=deadline, code=FACTS_AUTHORSHIP_UNKNOWN
    )
    shas = listed.decode("ascii", errors="strict").split()
    commits: list[CommitAttribution] = []
    for entry in _read_commit_entries(repo_root, shas, deadline=deadline):
        try:
            commits.append(
                _attribute_commit(
                    entry,
                    repository=repository,
                    task_root=task_root,
                    base_sha=lambda: base_tip_sha,
                    checkout=repo_root,
                )
            )
        except RecordError as exc:
            raise BranchFactsError(FACTS_AUTHORSHIP_UNKNOWN, f"commit {entry['sha'][:12]}: {exc}") from exc
        if time.monotonic() > deadline:
            raise BranchFactsError(
                FACTS_AUTHORSHIP_UNKNOWN, "branch fact collection timed out; refusing a partial history"
            )
    incoming_writer = None
    incoming_family = None
    if incoming_agent:
        incoming_writer = f"{incoming_agent}/{incoming_model or '(default)'}"
        incoming_family = incoming_writer_family(incoming_agent, incoming_model)
    merge_base = None
    changed: tuple[str, ...] = ()
    if shas:
        merge_base = (
            _facts_git(repo_root, ["merge-base", base_tip_sha, head_sha], deadline=deadline, code=FACTS_SCOPE_UNKNOWN)
            .decode("ascii")
            .strip()
        )
        try:
            changed = git_changed_paths(repo_root, merge_base, head_sha)
        except TargetResolutionError as exc:
            raise BranchFactsError(FACTS_SCOPE_UNKNOWN, str(exc)) from exc
    owned = tuple(str(path) for path in owned_paths)
    prepared = prepare_subject_exclusion(
        subject_seats=frozenset(subject_seats),
        subject_families=frozenset(subject_families),
        owned_paths=tuple(dict.fromkeys((*changed, *owned))),
    )
    if prepared.fail_closed_reason:
        raise BranchFactsError(FACTS_SCOPE_UNKNOWN, prepared.fail_closed_reason)
    return BranchReviewFacts(
        repository=repository,
        base_tip_sha=base_tip_sha,
        head_sha=head_sha,
        merge_base_sha=merge_base,
        commits=tuple(commits),
        existing_families=frozenset(commit.family for commit in commits if commit.family),
        incoming_writer=incoming_writer,
        incoming_family=incoming_family,
        changed_paths=changed,
        owned_paths=owned,
        subject_seats=prepared.seats,
        subject_families=prepared.families,
        subject_evidence=prepared.evidence,
    )


def structural_review_route(facts: BranchReviewFacts, *, risk: str, review_profile: str = "code") -> ReviewerResolution:
    """Resolve a formal reviewer outside every author family under the live catalog floors.

    Structural only (A2): no routing snapshot, so health and quota never decide
    feasibility; the resolver's own health semantics stay unchanged.
    """
    return resolve_reviewer(facts.resolver_inputs(risk=risk, review_profile=review_profile))


def pr_review_facts(
    repository: str,
    pr_number: int,
    *,
    head_sha: str,
    task_root: Path,
    repo_root: Path,
    subject_seats: Iterable[str] = (),
    subject_families: Iterable[str] = (),
) -> BranchReviewFacts:
    """Facts for an open PR's frozen head, bound to GitHub's listing of its commits (A1).

    The PR's base and head come from GitHub; membership comes from the local
    ``git rev-list``. Any difference between the two commit sets refuses.
    """
    pr = _run_json(["gh", "pr", "view", str(pr_number), "--repo", repository, "--json", "baseRefOid,headRefOid"])
    base = pr.get("baseRefOid") if isinstance(pr, dict) else None
    head = pr.get("headRefOid") if isinstance(pr, dict) else None
    if not isinstance(base, str) or not SHA.fullmatch(base):
        raise RecordError("PR base SHA unavailable; cannot prove clean base merge")
    if head != head_sha:
        raise RecordError("PR head moved since review; re-run exact-head review")
    listed = _pages(Request("read-commits", repo=repository, number=pr_number))
    if not listed:
        raise RecordError("PR commit set unavailable")
    github_shas = [entry.get("sha") for entry in listed]
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in github_shas):
        raise RecordError("PR commit set malformed")
    facts = collect_branch_review_facts(
        repository=repository,
        repo_root=repo_root,
        base_tip_sha=base,
        head_sha=head_sha,
        task_root=task_root,
        subject_seats=subject_seats,
        subject_families=subject_families,
    )
    if sorted(github_shas) != sorted(commit.sha or "" for commit in facts.commits):
        raise RecordError("PR commit set differs from the local base..head enumeration; fetch and retry")
    return facts


def _task_flag_values(task: dict[str, Any], key: str) -> tuple[str, ...]:
    value = task.get(key)
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RecordError(f"review task {key} malformed")
    return tuple(value)


def _require_qualified_reviewer(facts: BranchReviewFacts, *, task: dict[str, Any], model: str, family: str) -> None:
    """Evaluate the actual reviewer against the resolver's rules on the branch facts (AC-01).

    Protected seats and the risk floor bind as in selection; the reviewer need
    not be the resolver's current top choice, so quota or ladder order alone
    never invalidates a valid unchanged-head approval. The planned risk is the
    review's recorded ``review_risk`` (the resolver default when absent);
    path inference only raises it.
    """
    profile = str(task.get("review_profile") or "code").strip().casefold()
    # Seat aliases (``grok-build``) name the canonical route the catalog lists.
    agent = normalize_seat(str(task.get("agent") or "")) or ""
    if profile == "ukrainian":
        if agent not in {"claude", "codex", "agy"} or family not in {"anthropic", "openai", "google"}:
            raise RecordError("reviewer not qualified: Ukrainian review needs a Claude, GPT or Gemini seat")
        if facts.subject_seats or facts.subject_families or is_security_sensitive_change(facts.changed_paths):
            raise RecordError("reviewer not qualified: protected scope needs a code-profile review")
        return
    canonical = resolve_catalog_model_id(model)
    candidates = [
        candidate
        for candidate in REVIEW_CANDIDATES.values()
        if candidate.route == agent and resolve_catalog_model_id(candidate.concrete_model) == canonical
    ]
    if not candidates:
        raise RecordError(f"reviewer not qualified: {agent}/{model} is not a catalog review candidate")
    inputs = facts.resolver_inputs(risk=str(task.get("review_risk") or "medium"), review_profile=profile)
    results = [evaluate_candidate(candidate, inputs) for candidate in candidates]
    if not any(result.status == "eligible" for result in results):
        reasons = "; ".join(sorted({str(result.reason) for result in results}))
        raise RecordError(f"reviewer not qualified for this branch: {reasons}")


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


def _require_formal_reviewer(
    *, cursor: bool, reported: object, model: str, family: str, native_grok: bool = False
) -> None:
    """Refuse a verdict from an identity the reviewer resolver never selects (#9488).

    Through Cursor only a pinned formal seat counts, and only when the runtime
    reported its display name (``"Grok 4.7 256K High"``): a bare or other-variant
    slug (``grok-4.7``, ``grok-4.7-high-fast``) attests no variant, and Composer,
    Auto and Cursor-routed Claude are unpinned. Native Grok requires an attested
    runtime model (operator decision 2026-10-05, #9769); Kimi never reviews.
    On every harness the model must also
    hold a catalog review role (#9583), so Fable and retired models never approve.
    """
    if cursor:
        admitted = model in FORMAL_CURSOR_REVIEW_MODELS and reported != model
    else:
        admitted = family not in NATIVE_NON_REVIEWER_FAMILIES or (native_grok and model == "grok-4.7")
    if not admitted:
        raise RecordError(f"reviewer model unknown: {model!r} is not a formal reviewer on this harness")
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
    native_grok = task.get("agent") in {"grok", "grok-build"}
    reported = task.get("resolved_model") if cursor or native_grok else task.get("model")
    if cursor and task.get("resolved_model_known") is not True:
        raise RecordError("Cursor reviewer model unknown")
    source = task.get("resolved_model_source")
    if cursor and not (isinstance(source, str) and source in RUNTIME_REPORTED_MODEL_SOURCES):
        raise RecordError("Cursor reviewer model unattested: its source is not a runtime report")
    if native_grok and (task.get("resolved_model_known") is not True or source != "grok-model-usage"):
        raise RecordError("native Grok reviewer model unattested: modelUsage runtime report required")
    # Only Cursor's runtime reports display names; record its catalog id.
    model = canonical_cursor_model(reported) if cursor and isinstance(reported, str) else reported
    if native_grok:
        admitted_runtime_ids = load_model_catalog()["models"]["grok-4.7"].get("runtime_model_ids", [])
        if not isinstance(reported, str) or reported not in admitted_runtime_ids:
            raise RecordError("native Grok reviewer model unknown: runtime model is not admitted")
        model = "grok-4.7"
    if not isinstance(model, str) or not model or re.search(r"\s", model):
        raise RecordError("reviewer model unknown")
    family = resolve_family(model)
    if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
        raise RecordError("reviewer family unknown")
    _require_formal_reviewer(cursor=cursor, reported=reported, model=model, family=family, native_grok=native_grok)
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
    facts = pr_review_facts(
        repository,
        number,
        head_sha=sha,
        task_root=task_root,
        repo_root=root or _repo_root(),
        subject_seats=_task_flag_values(task, "review_subject_seats"),
        subject_families=_task_flag_values(task, "review_subject_families"),
    )
    if not facts.existing_families:
        raise RecordError("PR has no attributed author commits")
    if family in facts.excluded_families:
        raise RecordError("reviewer family equals an author family")
    _require_qualified_reviewer(facts, task=task, model=model, family=family)
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
