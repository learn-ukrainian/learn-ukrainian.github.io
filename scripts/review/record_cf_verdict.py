#!/usr/bin/env python3
"""Record a completed branch-pinned cross-family or explicit red-team review."""

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
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from functools import cache, partial
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any, Literal

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from learn_ukrainian_v4_runtime.agent_identity import normalize_seat
from learn_ukrainian_v4_runtime.identity import _VALID_CONCRETE_FAMILIES
from learn_ukrainian_v4_runtime.model_families import canonical_cursor_model, is_cursor_auto_selector

from scripts.common.jsonl import jsonl_lines
from scripts.fleet.claude_account_lane import ClaudeAccount, account_from_record
from scripts.fleet_comms.review_publication import (
    DEFAULT_STATUS_CONTEXT,
    REVIEW_SCHEMA_VERSION,
    ReviewPublicationError,
)
from scripts.fleet_comms.review_publisher import post_commit_status
from scripts.opsec.prepublish import (
    PublishBlocked,
    absolute_path_spans,
    check_texts,
    normalize_for_scan,
    normalize_repository,
    publication_boundary,
    publication_cli,
)
from scripts.orchestration.fleet_repos import FleetRepoError, load_fleet_repos
from scripts.orchestration.integration_sweep import (
    CHUNK_VOIDS,
    ITEM_ID_RE,
    MARKER_PREFIX,
    NEEDS_SEAT,
    REJECTED,
    SHA,
    TRUSTED_ASSOCIATIONS,
    GitHubAdapter,
    SweepError,
    lookup_verdict,
    parse_marker,
)
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME, read_task_record
from scripts.publish.github import CfVerdictRecord, Request, request_run
from scripts.review.app_bot_authorship import VERIFIED_APP_BOT, listing_app_bot_login, verified_app_bot_login
from scripts.review.language_lane import is_ukrainian_review
from scripts.review.model_catalog import (
    REVIEW_ACTIVITY,
    activity_role_refusal,
    load_model_catalog,
    resolve_catalog_model_id,
)
from scripts.review.review_contract import (
    ContractError,
    ItemChunk,
    judge_item_reply,
    load_frozen_item_packet,
    reply_has_item_judgments,
)
from scripts.review.reviewer_resolver import (
    FORMAL_CURSOR_REVIEW_MODELS,
    REVIEW_CANDIDATES,
    UNKNOWN_AUTHOR_FAMILY,
    UNRESOLVED_AUTHOR_FAMILIES,
    ResolverInputs,
    ReviewerResolution,
    evaluate_candidate,
    normalize_review_task_id,
    red_team_seat_refusal,
    resolve_author_family,
    resolve_family,
    resolve_reviewer,
    review_task_id_comparison_keys,
)
from scripts.review.role_resolution import resolve_routing_reference
from scripts.review.security_paths import git_changed_paths, is_security_sensitive_change
from scripts.review.subject_seat import prepare_subject_exclusion
from scripts.review.target_resolution import TargetResolutionError, resolve_review_repository
from scripts.review.ukrainian_seats import (
    UKRAINIAN_SEAT_ROUTES,
    attested_author_families,
    required_ukrainian_seats,
)
from scripts.review.verdict_parser import (
    _FINDINGS_ENVELOPE_KEYS,
    _REVIEW_VERDICT_LINE_RE,
    MISSING_CAPABILITIES_FIELD,
    _commonmark_lines,
    _findings_json_verdicts,
    _top_level_json_values,
    _UnreadableFindings,
    _without_code_fences,
    checked_findings_payload,
    declares_incomplete_review,
    declares_missing_capabilities,
    invalid_findings_block,
    recognized_verdicts,
    review_score,
)

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
# Review rounds per PR, counted on the reviewed heads of the current PR (C-2902);
# a security-sensitive change gets the elevated budget.
DEFAULT_REVIEW_ROUNDS = 3
ELEVATED_REVIEW_ROUNDS = 5


class RecordError(RuntimeError):
    """A review cannot be bound to a trustworthy exact-head verdict."""


NESTED_TOO_DEEPLY = "review reply is nested too deeply to read its verdict"


def normalize_verdict(reply: str) -> str:
    try:
        return _normalize_verdict(reply)
    except RecursionError:
        # The JSON decoder's depth limit: the verdict cannot be read, so it is refused by name.
        raise RecordError(NESTED_TOO_DEEPLY) from None


def _normalize_verdict(reply: str) -> str:
    tokens = {NORMALIZED[token.upper()] for token in recognized_verdicts(reply)}
    visible = _without_code_fences(reply, keep_unclosed=False)
    verdict_line = any(_REVIEW_VERDICT_LINE_RE.match(line) for line in _commonmark_lines(visible))
    # The verdict line is the reply's stated verdict; it holds a findings block that approves with follow-ups.
    stated = next(iter(tokens)) if verdict_line and len(tokens) == 1 else None
    # Every top-level findings block must pass the verifier's schema, whether or not a verdict line is present.
    if reason := invalid_findings_block(reply, stated=stated):
        beside = " beside a verdict line" if verdict_line else ""
        raise RecordError(f"reply carries an invalid findings block{beside}: {reason}")
    if declares_incomplete_review(reply):
        raise RecordError("inconclusive: reviewer declares an incomplete review")
    if verdict_line:
        findings = {NORMALIZED[token] for token in _findings_json_verdicts(reply, stated=stated)}
        offset = 0
        for line in _commonmark_lines(visible, keepends=True):
            line_start = offset
            offset += len(line)
            match = re.match(r" {0,3}\{", line)
            if match is None:
                continue
            start = line_start + match.end() - 1
            try:
                _, end = json.JSONDecoder().raw_decode(visible, start)
            except ValueError:
                continue
            findings.update(NORMALIZED[token] for token in _findings_json_verdicts(visible[start:end], stated=stated))
        if findings and findings != tokens:
            raise RecordError("reply carries a findings payload contradicting a verdict line")
    if len(tokens) != 1:
        raise RecordError("review reply has missing or ambiguous VERDICT token")
    verdict = tokens.pop()
    # A reviewer that reports missing capabilities cannot approve, wherever the reply declares them.
    if verdict != "BLOCKED" and declares_missing_capabilities(reply):
        raise RecordError(
            f"reply carries {MISSING_CAPABILITIES_FIELD} with verdict {verdict}; only a BLOCKED reply may"
        )
    return verdict


def _review_verdict_and_count(reply: str) -> tuple[str, int | Literal["unknown"]]:
    """Use canonical validated findings; prose supplies no reliable count."""
    try:
        payload = json.loads(reply)
    except ValueError:
        payload = None
    except RecursionError:
        raise RecordError(NESTED_TOO_DEEPLY) from None
    if isinstance(payload, dict) and payload.get("schema_version") == REVIEW_SCHEMA_VERSION:
        # The closeout verifier's schema judges the reply itself, not a canonical subset of it.
        try:
            verdict, evidence = checked_findings_payload(payload)
        except ContractError as exc:
            raise RecordError(f"structured review verdict or findings invalid: {exc}") from None
        except ReviewPublicationError:
            raise RecordError("structured review verdict or findings invalid") from None
        if declares_incomplete_review(reply):
            raise RecordError("inconclusive: reviewer declares an incomplete review")
        return verdict, len(evidence.findings) if evidence is not None else "unknown"
    return normalize_verdict(reply), "unknown"


# A ledger line may carry a slug after F1 (`F1-seed-recharges-...: resolved`).
_PROSE_FINDING_ID = r"F[1-9][0-9]{0,3}(?:-[A-Za-z0-9][A-Za-z0-9._:-]{0,80})?"
_PROSE_FINDING_LINE = re.compile(
    rf"^\s*(?:[-*]\s+)?\**({_PROSE_FINDING_ID})(?![A-Za-z0-9._:-])\**"
    rf"(?P<rest>(?:\s*[:\u2014\u2013-]+)?(?:\s*(?i:still|remains?)\s+open\s*[:\u2014\u2013-]?)?"
    rf"(?:\s*(?:\[(P[0-3])\]|\((P[0-3])\)))?.*)$"
)
_PROSE_RESOLVED = re.compile(r"^(?:\s*[:\u2014\u2013-]+)?\s*(?i:resolved|fixed)\b")
_RESOLVED_AMBIGUOUS = re.compile(r"(?i)\b(?:no|not|incorrectly|unresolved|still\s+open|remains?\s+open)\b|\?")
_BLOCKING_PRIORITY = re.compile(r"(?i)(?<![A-Za-z0-9])p[0-2](?![A-Za-z0-9])")
_SECURITY_VERDICT = re.compile(
    r"(?i)\*{0,2}security_verdict\*{0,2}\s*[:\u2014\u2013\-]?\s*\*{0,2}\s*([A-Za-z]+)?"
)
_FINDING_LIKE = re.compile(
    rf"(?im)^[ \t]*(?:#{{1,6}}[ \t]+|[-*+][ \t]+|\d+\.[ \t]+|>[ \t]+)?\**({_PROSE_FINDING_ID})(?![A-Za-z0-9._:-])"
)
_RESIDUAL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
TRUNCATION_FLAG = "[Review reply truncated to fit GitHub's comment limit.]"
REPAIR_WITHHELD = "Repair round: P3 mapping withheld"


def _security_verdict_blocks(reply: str) -> bool:
    """True when a security verdict is present and is not an unambiguous pass."""
    mentions = list(_SECURITY_VERDICT.finditer(reply))
    return any((match.group(1) or "").upper() != "PASS" for match in mentions)


def p3_residuals(reply: str) -> tuple[str, ...] | None:
    """Open finding ids when every one of them is P3, or None when that reading does not apply.

    None keeps the reply's own verdict. A P0, P1, or P2 token anywhere in the reply,
    a security verdict that is not an unambiguous pass, an incomplete review, a malformed
    findings block, a finding with no readable priority, a truncated body, or a repair
    round whose mapping was withheld is None. An empty open set is None: a changes
    request with no findings is not an approval.
    """
    if not isinstance(reply, str) or _security_verdict_blocks(reply):
        return None
    if TRUNCATION_FLAG in reply or REPAIR_WITHHELD in reply:
        return None
    if _BLOCKING_PRIORITY.search(reply):
        return None
    if "BLOCKED" in {token.upper() for token in recognized_verdicts(reply)}:
        return None
    if declares_incomplete_review(reply) or declares_missing_capabilities(reply):
        return None
    if invalid_findings_block(reply):
        return None
    findings: dict[str, str] = {}
    structured: set[str] = set()
    try:
        payloads = list(_top_level_json_values(reply))
    except _UnreadableFindings:
        return None
    for payload in payloads:
        if not isinstance(payload, dict) or not (_FINDINGS_ENVELOPE_KEYS & payload.keys()):
            continue
        try:
            _verdict, evidence = checked_findings_payload(payload)
        except (ContractError, ReviewPublicationError):
            return None
        if evidence is None:
            continue
        for finding in evidence.findings:
            previous = findings.get(finding.finding_id)
            if previous is not None and previous != finding.priority:
                return None
            findings[finding.finding_id] = finding.priority
            structured.add(finding.finding_id)
    try:
        visible = _without_code_fences(reply, keep_unclosed=False)
    except (ValueError, ImportError):
        return None
    for line in _commonmark_lines(visible):
        match = _PROSE_FINDING_LINE.match(line)
        if match is None:
            continue
        finding_id = match.group(1)
        priority = match.group(3) or match.group(4)
        rest = match.group("rest") or ""
        if _PROSE_RESOLVED.match(rest):
            # Only the resolution clause is judged. A later sentence may say "not".
            clause = re.match(r"(?i)^(?:\s*[:\u2014\u2013-]+)?\s*(?:resolved|fixed)\b.{0,24}", rest)
            if finding_id in findings or _RESOLVED_AMBIGUOUS.search(clause.group(0) if clause else rest[:40]):
                return None
            continue
        if priority is None:
            return None
        if structured and finding_id not in structured:
            return None
        previous = findings.get(finding_id)
        if previous is not None and previous != priority:
            return None
        findings[finding_id] = priority
    for line in reply.splitlines():
        if _FINDING_LIKE.match(line) and _PROSE_FINDING_LINE.match(line) is None:
            return None
    if not findings or any(priority != "P3" for priority in findings.values()):
        return None
    if any(_RESIDUAL_ID.fullmatch(finding_id) is None for finding_id in findings):
        return None
    return tuple(findings)


def _require_sources_mcp_calls(task: dict[str, Any]) -> None:
    """Refuse Ukrainian verdicts without positive runtime Sources evidence (#10074)."""
    if not is_ukrainian_review(task):
        return
    count = task.get("sources_mcp_call_count")
    if type(count) is not int or count < 0:
        raise RecordError("Ukrainian review Sources MCP call count unknown; runtime evidence required")
    if count == 0:
        raise RecordError("Ukrainian review has zero Sources MCP calls")


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


def live_app_bot_login(repository: str, sha: str) -> str | None:
    """The allowlisted app bot GitHub reports as ``sha``'s author, read live for that SHA (#10531).

    Every lookup failure or disagreement returns None, which keeps the commit's
    authorship unknown and refused.
    """
    try:
        commit = _run_json(Request("read-commit", repo=repository, sha=sha))
    except RecordError:
        return None
    return verified_app_bot_login(commit, sha, repository)


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


@contextmanager
def isolated_object_store(checkout: Path | None = None) -> Iterator[dict[str, str]]:
    """A Git environment that reads the checkout's objects and writes only to a throwaway store.

    The bare repository imports no init templates, config, refs, grafts,
    attributes or index from the writable shared Git dir, and objects a proof
    writes (``merge-tree --write-tree``) never reach the shared store. Raises
    ``OSError`` when the checkout's object store is unavailable.
    """
    objects = _merge_proof_object_store(checkout)
    with TemporaryDirectory(prefix="cf-merge-") as isolated:
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
        yield {
            **{key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
            "GIT_DIR": isolated,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(proof_dir / "no-global-config"),
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_LAZY_FETCH": "1",
        }


CLEAN_BASE_MERGE = "clean-base-merge"
CLEAN_SYNC_MERGE = "clean-sync-merge"


def _is_clean_base_merge(entry: dict[str, Any], base_sha: str, *, checkout: Path | None = None) -> bool:
    """Whether ``entry`` is a Git-proven conflict-free merge of the base into the branch."""
    return _clean_merge_source(entry, base_sha, checkout=checkout) == CLEAN_BASE_MERGE


def _clean_merge_source(
    entry: dict[str, Any],
    base_sha: str,
    *,
    checkout: Path | None = None,
    range_shas: frozenset[str] = frozenset(),
) -> str | None:
    """Bind a conflict-free merge to commit metadata and raw local objects.

    Returns ``CLEAN_BASE_MERGE`` when the second parent is a base ancestor, or
    ``CLEAN_SYNC_MERGE`` when every parent is a base ancestor or one of
    ``range_shas``, the PR's own commits, each attributed on its own. In both
    cases the tree must equal Git's merge of the two parents, so the merge adds
    no content. Anything else returns None.

    ``checkout`` locates the object store; the default is the current directory.
    """
    commit_sha = entry.get("sha")
    commit_data = entry.get("commit")
    tree_data = commit_data.get("tree") if isinstance(commit_data, dict) else None
    tree = tree_data.get("sha") if isinstance(tree_data, dict) else None
    parent_data = entry.get("parents")
    if not isinstance(parent_data, list) or len(parent_data) != 2:
        return None
    parents = [parent.get("sha") if isinstance(parent, dict) else None for parent in parent_data]
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in [commit_sha, base_sha, tree, *parents]):
        return None
    git = ["git"]
    try:
        with isolated_object_store(checkout) as env:
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
                return None
            if [line[7:] for line in headers if line.startswith("parent ")] != parents:
                return None
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

            def in_base(sha: str) -> bool:
                probe = subprocess.run(
                    [*git, "merge-base", "--is-ancestor", sha, base_sha],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                if probe.returncode not in (0, 1):
                    raise subprocess.SubprocessError("ancestry unavailable")
                return probe.returncode == 0

            source = CLEAN_BASE_MERGE
            if not in_base(parents[1]):
                # A sync merge of the PR's own commits: each is attributed on its own.
                if not all(sha in range_shas or in_base(sha) for sha in parents):
                    return None
                source = CLEAN_SYNC_MERGE
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
        return None
    return source if merged.stdout.strip() == tree else None


@dataclass(frozen=True)
class CommitAttribution:
    """One author contribution to a branch commit, with its proven family.

    ``family`` is None only for a Git-proven clean base or sync merge, which authors nothing.
    """

    sha: str | None
    family: str | None
    source: str
    task_id: str | None = None
    record_task_id: str | None = None
    author_models: tuple[str, ...] = ()
    authorship: str | None = None


def _author_model_family(harness: str, model: str) -> str:
    """Resolve a model in its harness context; only Cursor accepts Auto selectors."""
    cursor = normalize_seat(harness.strip().lower().removesuffix("-tools")) == "cursor"
    if is_cursor_auto_selector(model) and not cursor:
        return UNKNOWN_AUTHOR_FAMILY
    return resolve_author_family(f"cursor:{model}" if cursor else model)


def _is_catalog_model_trailer(model: str) -> bool:
    """Accept explicit model forms, never arbitrary task-id suffixes."""
    catalog = load_model_catalog()
    model_id = resolve_catalog_model_id(model, catalog)
    if model_id is None:
        return False
    aliases = (model_id, *catalog["models"][model_id].get("aliases", []))
    pattern = (
        "(?:" + "|".join(re.escape(alias) for alias in aliases) + ")"
        r"(?:-(?:low|medium|high|xhigh|max))?(?:\[[^\[\]\s]+\])?"
    )
    candidates = [model, *(model[index + 1 :] for index, char in enumerate(model) if char in "/:")]
    return any(re.fullmatch(pattern, candidate, flags=re.IGNORECASE) for candidate in candidates)


def _attribute_commit(
    entry: dict[str, Any],
    *,
    repository: str,
    task_root: Path,
    base_sha: Callable[[], str],
    checkout: Path | None = None,
    unknown_history: Iterable[str] = (),
    app_bot_login: Callable[[str], str | None] | None = None,
    range_shas: frozenset[str] = frozenset(),
) -> CommitAttribution:
    """Resolve one commit's author family, retaining unresolvable authors as Unknown.

    ``entry`` has the GitHub commit-listing shape (``sha``, ``commit.message``,
    ``commit.tree.sha``, ``parents``). ``base_sha`` is called only when an
    untrailered commit needs the clean-merge proof; ``range_shas`` are the PR's
    own commits, which a clean sync merge may join. ``app_bot_login`` is called
    only for an untrailered commit that is neither a clean merge nor
    admitted unknown history; a login is GitHub's live proof that an
    allowlisted app bot authored it (#10531), recorded as ``verified_app_bot``
    without any model.
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
    ):
        merge_source = _clean_merge_source(entry, base_sha(), checkout=checkout, range_shas=range_shas)
        if merge_source is not None:
            return CommitAttribution(commit_sha, None, merge_source)
    if not trailers and not re.search(r"(?m)^X-Agent:", message) and commit_sha in unknown_history:
        return CommitAttribution(
            commit_sha, UNKNOWN_AUTHOR_FAMILY, "unknown_historical", authorship="unknown_historical"
        )
    if (
        not trailers
        and not re.search(r"(?m)^X-Agent:", message)
        and app_bot_login is not None
        and isinstance(commit_sha, str)
        and SHA.fullmatch(commit_sha)
        and app_bot_login(commit_sha) is not None
    ):
        return CommitAttribution(commit_sha, VERIFIED_APP_BOT, VERIFIED_APP_BOT, authorship=VERIFIED_APP_BOT)
    if len(trailers) != 1 or "/" not in trailers[0]:
        raise RecordError("author model unknown: missing explicit X-Agent model trailer")
    return _attribute_trailer(commit_sha, trailers[0], repository=repository, task_root=task_root)


def _attribute_trailer(commit_sha: str | None, trailer: str, *, repository: str, task_root: Path) -> CommitAttribution:
    """Resolve one trailer using the existing task/model provenance bindings."""
    if "/" not in trailer:
        raise RecordError("author model unknown: missing explicit X-Agent model trailer")
    harness, model = trailer.split("/", 1)
    if not harness or not model:
        raise RecordError("author model unknown")
    # Task provenance wins over family tokens embedded in the trailer's task id.
    task_file = None
    if TASK_ID.fullmatch(model):
        task_file = _hot_or_archived(task_root, f"{model}.json")
        if not task_file.resolve().is_relative_to(task_root.resolve()):
            raise RecordError("author task provenance unavailable")
    if task_file is not None and task_file.exists():
        # Resolve the recorded model only after validating the task provenance.
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
        family = _author_model_family(harness, str(author_model or ""))
        source = "task-record-archived" if task_file.parent.name == ARCHIVE_DIR_NAME else "task-record"
    else:
        # Require a complete model form; routing's catalog-prefix matching can
        # mistake task ids for models when their task records are missing.
        family = (
            _author_model_family(harness, model)
            if _is_catalog_model_trailer(model) or is_cursor_auto_selector(model)
            else UNKNOWN_AUTHOR_FAMILY
        )
        source = "trailer-model"
        if family in UNRESOLVED_AUTHOR_FAMILIES:
            if not TASK_ID.fullmatch(model):
                raise RecordError("author model unknown")
            # A task id without a task record is unresolved on every harness,
            # a single-family one included: the harness name is author-chosen
            # text, not a model (C-2902 F5).
            family = UNKNOWN_AUTHOR_FAMILY
            source = "unresolved-author"
    if family in UNRESOLVED_AUTHOR_FAMILIES:
        # A committed author without a concrete identity is collected as
        # Unknown (#9944); every review refuses it (require_resolved_branch_authors,
        # C-2902). Unknown is never a reviewer identity.
        family = UNKNOWN_AUTHOR_FAMILY
    has_record = source in {"task-record", "task-record-archived"}
    task_id = model if has_record or (TASK_ID.fullmatch(model) and not _is_catalog_model_trailer(model)) else None
    record_task_id = author_task.get("task_id") if has_record else None
    model_values = (
        (
            author_task.get("model"),
            author_model,
            author_task.get("resolved_model") if author_task.get("resolved_model_known") is True else None,
        )
        if has_record
        else (model,)
        if _is_catalog_model_trailer(model)
        else ()
    )
    if harness.startswith("cursor"):
        model_values = tuple(
            canonical_cursor_model(value) if isinstance(value, str) else value for value in model_values
        )
    author_models = tuple(
        dict.fromkeys(value for value in model_values if isinstance(value, str) and resolve_catalog_model_id(value))
    )
    return CommitAttribution(
        commit_sha if isinstance(commit_sha, str) else None,
        family,
        source,
        normalize_review_task_id(task_id, agent=harness) if task_id is not None else None,
        normalize_review_task_id(record_task_id, agent=harness) if isinstance(record_task_id, str) else None,
        author_models,
    )


def _attribute_commit_authors(
    entry: dict[str, Any],
    *,
    repository: str,
    task_root: Path,
    base_sha: Callable[[], str],
    checkout: Path | None = None,
    unknown_history: Iterable[str] = (),
    app_bot_login: Callable[[str], str | None] | None = None,
    range_shas: frozenset[str] = frozenset(),
) -> tuple[CommitAttribution, ...]:
    """Resolve every declared writer atomically; keep legacy zero/one admission."""
    message = (entry.get("commit") or {}).get("message")
    declared = re.findall(r"(?m)^X-Agent:[^\r\n]*", message) if isinstance(message, str) else []
    if len(declared) <= 1:
        return (
            _attribute_commit(
                entry,
                repository=repository,
                task_root=task_root,
                base_sha=base_sha,
                checkout=checkout,
                unknown_history=unknown_history,
                app_bot_login=app_bot_login,
                range_shas=range_shas,
            ),
        )
    authors = []
    for index, line in enumerate(declared, 1):
        prefix = f"author model unknown: {len(declared)} X-Agent trailers: member {index}"
        match = re.fullmatch(r"X-Agent:[^\S\r\n]*(\S+)[^\S\r\n]*", line)
        if match is None or "/" not in match[1]:
            raise RecordError(f"{prefix} malformed")
        try:
            author = _attribute_trailer(entry.get("sha"), match[1], repository=repository, task_root=task_root)
        except RecordError as exc:
            raise RecordError(f"{prefix}: {exc}") from exc
        if author.family in UNRESOLVED_AUTHOR_FAMILIES or not author.author_models:
            raise RecordError(f"{prefix} unresolved; refusing all authors")
        authors.append(author)
    return tuple(authors)


def author_families(repository: str, pr_number: int, task_root: Path) -> set[str]:
    """Resolve a PR's GitHub-listed commits, including Unknown author families.

    A compatibility reader over :func:`_attribute_commit_authors`. The recorder itself
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
    range_shas = frozenset(entry["sha"] for entry in commits if isinstance(entry.get("sha"), str))
    for entry in commits:
        authors = _attribute_commit_authors(
            entry,
            repository=repository,
            task_root=task_root,
            base_sha=base_sha,
            app_bot_login=listing_app_bot_login(commits, repository),
            range_shas=range_shas,
        )
        families.update(author.family for author in authors if author.family is not None)
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
    def unknown_history(self) -> tuple[str, ...]:
        return tuple(sorted(commit.sha for commit in self.commits if commit.source == "unknown_historical"))

    @property
    def app_bot_commits(self) -> tuple[str, ...]:
        """Commits GitHub proved were authored by an allowlisted app bot (#10531)."""
        return tuple(sorted(commit.sha for commit in self.commits if commit.source == VERIFIED_APP_BOT))

    @property
    def author_task_ids(self) -> frozenset[str]:
        """Author task identities retained from the complete branch's X-Agent trailers."""
        return frozenset(
            normalize_review_task_id(task_id)
            for commit in self.commits
            for task_id in (commit.task_id, commit.record_task_id)
            if task_id is not None
        )

    @property
    def author_families(self) -> frozenset[str]:
        """Every committed author family plus the incoming writer's (Cursor Auto stays its own family)."""
        incoming = frozenset({self.incoming_family}) if self.incoming_family else frozenset()
        return self.existing_families | incoming

    @property
    def excluded_families(self) -> frozenset[str]:
        """Every author family excluded from review, including Cursor Auto's own family."""
        if any(commit.source in {"unknown_historical", "suspect_historical"} for commit in self.commits):
            return self.author_families | _VALID_CONCRETE_FAMILIES
        return self.author_families

    @property
    def unresolved_authors(self) -> tuple[str, ...]:
        """Commits whose author family is unknown, so no reviewer can be proved outside it.

        Untrailered history a red-team admission receipt froze (``unknown_historical``)
        keeps its own qualification rules and is not counted here.
        """
        return tuple(
            commit.sha or "(unknown commit)"
            for commit in self.commits
            if commit.source == "unresolved-author"
            or (commit.family == UNKNOWN_AUTHOR_FAMILY and commit.source != "unknown_historical")
        )

    @property
    def scope_paths(self) -> tuple[str, ...]:
        """Literal branch changes (both rename sides, deletions) plus the proposed owned paths."""
        return tuple(dict.fromkeys((*self.changed_paths, *self.owned_paths)))

    @property
    def author_models(self) -> tuple[str | None, ...]:
        """Author models per unique commit; an unattributed commit adds None."""
        return tuple(
            model
            for _sha, model in dict.fromkeys(
                (commit.sha, model)
                for commit in self.commits
                # A clean (base or sync) merge authors nothing; a verified app bot has no model.
                if commit.source not in {CLEAN_BASE_MERGE, CLEAN_SYNC_MERGE, VERIFIED_APP_BOT}
                for model in (commit.author_models or (None,))
            )
        )

    @property
    def author_task_models(self) -> tuple[str, ...]:
        """The head commit's task-record author models."""
        return tuple(
            dict.fromkeys(
                model
                for commit in self.commits
                if commit.sha == self.head_sha and commit.source in {"task-record", "task-record-archived"}
                for model in commit.author_models
            )
        )

    def resolver_inputs(
        self, *, risk: str, claude_account: ClaudeAccount, review_profile: str = "code", **overrides: Any
    ) -> ResolverInputs:
        """Reviewer-resolver inputs carrying these facts; ``overrides`` set the remaining fields.

        ``claude_account`` is the account a claude reviewer runs as (#10630); it has no default.
        """
        overrides.setdefault("domain", review_profile)
        overrides.setdefault("author_model", "")
        overrides.setdefault("unknown_history", self.unknown_history)
        overrides.setdefault("app_bot_commits", self.app_bot_commits)
        return ResolverInputs(
            author_families=self.excluded_families,
            author_models=self.author_models,
            author_task_models=self.author_task_models,
            claude_account=claude_account,
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
        receipt = {
            "repository": self.repository,
            "base_tip_sha": self.base_tip_sha,
            "head_sha": self.head_sha,
            "commits": len({commit.sha for commit in self.commits}),
            "existing_families": sorted(self.existing_families),
            "incoming_writer": self.incoming_writer,
            "incoming_family": self.incoming_family,
            "author_families": sorted(self.author_families),
            "excluded_families": sorted(self.excluded_families),
            "subject_seats": sorted(self.subject_seats),
            "subject_families": sorted(self.subject_families),
            "scope_paths": len(self.scope_paths),
        }
        if self.unknown_history:
            receipt["unknown_history"] = list(self.unknown_history)
            receipt["authorship"] = "unknown_historical"
        if self.app_bot_commits:
            receipt["app_bot_commits"] = list(self.app_bot_commits)
        return receipt


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
            # Object headers end at LF; NEL/LS/PS are free text in author names.
            lines = jsonl_lines(headers)
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
    family = _author_model_family(harness, concrete)
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
    authorship_exclude_sha: str | None = None,
    unknown_history: Iterable[str] = (),
    app_bot_login: Callable[[str], str | None] | None = None,
) -> BranchReviewFacts:
    """Collect complete authorship and protected scope for ``base_tip_sha..head_sha``.

    Commit membership is ``git rev-list <base>..<head>`` (A1), attributed by the
    recorder's own per-commit rules (trailer, hot or archived task record,
    Cursor attestation, single-family harness, Git-proven clean base or sync
    merge, GitHub-proven app bot).
    ``incoming_agent``/``incoming_model`` name the writer about to be
    dispatched, after any substitution. Scope is the literal diff against the
    merge-base (both rename sides and deletions) plus ``owned_paths``, with the
    known subject seats ``prepare_subject_exclusion`` derives from it; shared
    or missing subject metadata remains unknown. A fresh branch
    passes ``head_sha == base_tip_sha``. Admission may exclude commits reachable
    from a frozen main/rebase tip with ``authorship_exclude_sha`` (#9988); this
    never narrows the diff or protected scope against the original base.
    Reads only; never fetches Git objects. An untrailered commit that no other
    rule attributes is checked with ``app_bot_login`` (default: a live GitHub
    read of that SHA, :func:`live_app_bot_login`). Raises
    ``BranchFactsError`` (``code`` = authorship, scope or target unknown).
    """
    deadline = time.monotonic() + timeout_s
    endpoints = [("base", base_tip_sha), ("head", head_sha)]
    if authorship_exclude_sha is not None:
        endpoints.append(("authorship exclusion", authorship_exclude_sha))
    for label, sha in endpoints:
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
    revisions = ["rev-list", f"{base_tip_sha}..{head_sha}"]
    if authorship_exclude_sha is not None:
        revisions.append(f"^{authorship_exclude_sha}")
    listed = _facts_git(repo_root, revisions, deadline=deadline, code=FACTS_AUTHORSHIP_UNKNOWN)
    shas = listed.decode("ascii", errors="strict").split()
    commits: list[CommitAttribution] = []
    unknown_history = frozenset(unknown_history)
    app_bot_login = app_bot_login or partial(live_app_bot_login, repository)
    range_shas = frozenset(shas)
    for entry in _read_commit_entries(repo_root, shas, deadline=deadline):
        try:
            commits.extend(
                _attribute_commit_authors(
                    entry,
                    repository=repository,
                    task_root=task_root,
                    # Clean main merges still need the existing object/tree
                    # proof, bound to the frozen main tip rather than a stale base.
                    base_sha=lambda: authorship_exclude_sha or base_tip_sha,
                    checkout=repo_root,
                    unknown_history=unknown_history,
                    app_bot_login=app_bot_login,
                    range_shas=range_shas,
                )
            )
        except RecordError as exc:
            raise BranchFactsError(FACTS_AUTHORSHIP_UNKNOWN, f"commit {entry['sha'][:12]}: {exc}") from exc
        if time.monotonic() > deadline:
            raise BranchFactsError(
                FACTS_AUTHORSHIP_UNKNOWN, "branch fact collection timed out; refusing a partial history"
            )
    # A proven clean merge of the excluded tip authors nothing, and it stays
    # in the facts. Dispatch can still admit the incoming writer. A branch
    # review refuses that range in refuse_excluded_only_range.
    incoming_writer = None
    incoming_family = None
    if incoming_agent:
        incoming_writer = f"{incoming_agent}/{incoming_model or '(default)'}"
        incoming_family = incoming_writer_family(incoming_agent, incoming_model)
    merge_base = None
    changed: tuple[str, ...] = ()
    if base_tip_sha != head_sha:
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


def structural_review_route(
    facts: BranchReviewFacts,
    *,
    risk: str,
    claude_account: ClaudeAccount,
    review_profile: str = "code",
    review_mode: str = "cross_family",
) -> ReviewerResolution:
    """Resolve a formal reviewer outside every author family under the live catalog floors.

    Structural only (A2): no routing snapshot, so health and quota never decide
    feasibility; the resolver's own health semantics stay unchanged.
    ``claude_account`` is the account a claude reviewer would run as: an
    unresolved one removes the claude seats (#10630).
    """
    inputs = facts.resolver_inputs(
        risk=risk, review_profile=review_profile, claude_account=claude_account, structural=True
    )
    if review_mode == "red_team" and facts.incoming_writer:
        # This is the declared new writer, never an assumed historical model.
        inputs = replace(inputs, author_models=(*inputs.author_models, facts.incoming_writer))
    return resolve_reviewer(inputs, review_mode=review_mode)


def _canonical_base_branch_name(base_branch: str) -> str:
    """Branch name behind the spellings target resolution already accepts.

    ``main``, ``origin/main``, ``remotes/origin/main``,
    ``refs/remotes/origin/main`` and ``refs/heads/main`` name one branch.
    A non-default ref keeps its own name, including a slash that is part of it.
    """
    name = base_branch.strip()
    for prefix in ("refs/remotes/origin/", "remotes/origin/", "refs/heads/", "origin/"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    return name


def authorship_exclude_sha(repo_root: Path, *, base_branch: str | None) -> str | None:
    """Current default-branch tip when ``base_branch`` names that branch.

    The same rule as dispatch admission (#9988): a review whose base is the
    default branch drops commits reachable from that branch's current tip.
    Any other base keeps the full enumeration. The tip is the local
    ``refs/remotes/origin/HEAD``. A checkout that has not recorded it returns
    None, so callers keep the previous enumeration rather than guessing a tip.
    Qualified spellings of that ref are reduced to the branch name first.
    """
    if not isinstance(base_branch, str) or not base_branch.strip():
        return None
    name = _canonical_base_branch_name(base_branch)
    try:
        ref = _facts_git(
            repo_root,
            ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            deadline=time.monotonic() + 30,
            code=FACTS_TARGET_UNKNOWN,
        )
    except BranchFactsError:
        return None
    pointed = ref.decode("ascii", errors="strict").strip()
    if not pointed.startswith("origin/"):
        return None
    if name != pointed.removeprefix("origin/"):
        return None
    try:
        tip = _facts_git(
            repo_root,
            ["rev-parse", f"{pointed}^{{commit}}"],
            deadline=time.monotonic() + 30,
            code=FACTS_TARGET_UNKNOWN,
        )
    except BranchFactsError:
        return None
    sha = tip.decode("ascii", errors="strict").strip()
    if not SHA.fullmatch(sha):
        return None
    return sha


def default_branch_review_base(repo_root: Path, head_sha: str, *, fetch: bool = True) -> tuple[str, str]:
    """The fetched default-branch tip and its merge-base with ``head_sha`` (C-2902 F6).

    Every branch review is attributed over ``merge-base..head`` with that tip
    excluded, at dispatch and at record. The default branch is the one origin
    advertises as ``HEAD``, fetched fresh into ``origin/<default>``. A caller's
    ``--base`` and the PR's base are never read: the author chooses both. Raises
    ``BranchFactsError`` when the remote, the fetch or a shared history is unavailable.
    ``fetch=False`` reads the existing ``origin/<default>`` without writing any ref
    or object, for read-only callers such as ``budget-check``.
    """
    from scripts.common.git_context import UnsafeBranchNameError, validate_plain_branch_name

    deadline = time.monotonic() + BRANCH_FACTS_TIMEOUT_S
    advertised = _facts_git(
        repo_root, ["ls-remote", "--symref", "origin", "HEAD"], deadline=deadline, code=FACTS_TARGET_UNKNOWN
    ).decode("utf-8", errors="replace")
    match = re.search(r"(?m)^ref: refs/heads/(\S+)\tHEAD$", advertised)
    try:
        name = validate_plain_branch_name(match.group(1), repo_root=repo_root) if match else None
    except UnsafeBranchNameError:
        name = None
    if name is None:
        raise BranchFactsError(FACTS_TARGET_UNKNOWN, "origin advertises no default branch")
    tracking = f"refs/remotes/origin/{name}"
    if fetch:
        _facts_git(
            repo_root,
            ["fetch", "--no-tags", "--no-write-fetch-head", "origin", f"+refs/heads/{name}:{tracking}"],
            deadline=deadline,
            code=FACTS_TARGET_UNKNOWN,
        )
    tip = (
        _facts_git(
            repo_root, ["rev-parse", "--verify", f"{tracking}^{{commit}}"], deadline=deadline, code=FACTS_TARGET_UNKNOWN
        )
        .decode("ascii", errors="replace")
        .strip()
    )
    if not SHA.fullmatch(tip) or not isinstance(head_sha, str) or not SHA.fullmatch(head_sha):
        raise BranchFactsError(FACTS_TARGET_UNKNOWN, "default-branch tip or head SHA invalid")
    try:
        merge_base = _facts_git(repo_root, ["merge-base", tip, head_sha], deadline=deadline, code=FACTS_TARGET_UNKNOWN)
    except BranchFactsError as exc:
        if exc.timed_out:
            raise
        raise BranchFactsError(
            FACTS_TARGET_UNKNOWN, f"head {head_sha[:12]} shares no available history with origin/{name}"
        ) from exc
    return tip, merge_base.decode("ascii", errors="replace").strip()


def _shas_not_reachable_from(repo_root: Path, shas: list[str], exclude_sha: str | None) -> list[str]:
    """Drop commits reachable from ``exclude_sha``, including that commit.

    One ``git rev-list --no-walk`` covers every valid SHA under a single
    deadline. Strings that are not commit SHAs stay, without starting Git.
    """
    if exclude_sha is None:
        return list(shas)
    pending = [sha for sha in shas if isinstance(sha, str) and SHA.fullmatch(sha)]
    if not pending:
        return [sha if isinstance(sha, str) else "" for sha in shas]
    listed = _facts_git(
        repo_root,
        ["rev-list", "--no-walk", "--stdin"],
        deadline=time.monotonic() + _GIT_STEP_TIMEOUT_S,
        code=FACTS_AUTHORSHIP_UNKNOWN,
        input_bytes=("\n".join((*pending, f"^{exclude_sha}")) + "\n").encode("ascii"),
    )
    reachable = set(listed.decode("ascii", errors="strict").split())
    kept: list[str] = []
    for sha in shas:
        if isinstance(sha, str) and SHA.fullmatch(sha):
            if sha in reachable:
                kept.append(sha)
        else:
            kept.append(sha if isinstance(sha, str) else "")
    return kept


def refuse_excluded_only_range(facts: BranchReviewFacts, *, repo_root: Path, exclude_sha: str | None) -> None:
    """Refuse a branch review that has no commit of its own.

    Fact collection stays quiet. Dispatch admits a known incoming writer onto
    a branch that has not authored a commit yet, including after a clean merge
    of the excluded tip, and a rebase plan still enumerates that range. The
    recorder and the resolver still refuse it: the frozen base and head are
    the same commit, every remaining commit is reachable from the excluded
    tip, or the only commits left are proven clean merges of it.
    """
    if facts.base_tip_sha == facts.head_sha:
        raise BranchFactsError(
            FACTS_AUTHORSHIP_UNKNOWN,
            "empty review range: the branch has no commits of its own",
        )
    if exclude_sha is None or facts.existing_families:
        return
    if any(commit.family is not None for commit in facts.commits):
        return
    if facts.commits:
        raise BranchFactsError(
            FACTS_AUTHORSHIP_UNKNOWN,
            "author model unknown: missing explicit X-Agent model trailer",
        )
    full = _facts_git(
        repo_root,
        ["rev-list", f"{facts.base_tip_sha}..{facts.head_sha}"],
        deadline=time.monotonic() + 30,
        code=FACTS_AUTHORSHIP_UNKNOWN,
    )
    if full.strip():
        raise BranchFactsError(
            FACTS_AUTHORSHIP_UNKNOWN,
            "author model unknown: missing explicit X-Agent model trailer",
        )


def pr_review_facts(
    repository: str,
    pr_number: int,
    *,
    head_sha: str,
    task_root: Path,
    repo_root: Path,
    subject_seats: Iterable[str] = (),
    subject_families: Iterable[str] = (),
    unknown_history: Iterable[str] = (),
    fetch: bool = True,
    current_head: bool = True,
) -> BranchReviewFacts:
    """Facts for an open PR's frozen head, bound to GitHub's listing of its commits (A1).

    The head comes from GitHub; the range is the fetched default branch to
    that head (:func:`default_branch_review_base`), never the PR's base, which
    the author can retarget. Membership comes from the local ``git rev-list``.
    Any difference from GitHub's listing refuses, so a PR whose base is not the
    default branch is refused rather than attributed over a shorter range.
    With ``current_head=False`` the facts are those of an earlier head the PR
    still contains: every commit of its range must be in GitHub's listing.
    """
    pr = _run_json(["gh", "pr", "view", str(pr_number), "--repo", repository, "--json", "headRefOid"])
    head = pr.get("headRefOid") if isinstance(pr, dict) else None
    if current_head and head != head_sha:
        raise RecordError("PR head moved since review; re-run exact-head review")
    listed = _pages(Request("read-commits", repo=repository, number=pr_number))
    if not listed:
        raise RecordError("PR commit set unavailable")
    github_shas = [entry.get("sha") for entry in listed]
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in github_shas):
        raise RecordError("PR commit set malformed")
    exclude, base = default_branch_review_base(repo_root, head_sha, fetch=fetch)
    facts = collect_branch_review_facts(
        repository=repository,
        repo_root=repo_root,
        base_tip_sha=base,
        head_sha=head_sha,
        task_root=task_root,
        subject_seats=subject_seats,
        subject_families=subject_families,
        authorship_exclude_sha=exclude,
        unknown_history=unknown_history,
        # GitHub's live listing of this PR carries each commit's author proof.
        app_bot_login=listing_app_bot_login(listed, repository),
    )
    refuse_excluded_only_range(facts, repo_root=repo_root, exclude_sha=exclude)
    if not current_head:
        # Commits pushed after the reviewed head need not be local; the reviewed range must be listed.
        if head_sha not in github_shas or not {commit.sha or "" for commit in facts.commits} <= set(github_shas):
            raise RecordError("PR no longer contains the reviewed head's commits")
        return facts
    differs = RecordError(
        "PR commit set differs from the local base..head enumeration from the default branch; "
        "target the default branch, or fetch and retry"
    )
    try:
        github_own = _shas_not_reachable_from(repo_root, github_shas, exclude)
    except BranchFactsError as exc:
        # A listed commit missing locally is a difference, not a partial read; a timeout stays one.
        if exc.timed_out:
            raise
        raise differs from exc
    if sorted(github_own) != sorted({commit.sha or "" for commit in facts.commits}):
        raise differs
    return facts


def admitted_unknown_history(
    *,
    repository: str,
    branch: str,
    head_sha: str,
    task_root: Path,
    repo_root: Path,
) -> tuple[str, ...]:
    """Read existing authoring receipts, never derive allowances from the review head.

    Both the frozen remote head and each allowed commit must precede the
    admission head, which must precede this review of the same branch.
    """
    allowed: set[str] = set()
    deadline = time.monotonic() + BRANCH_FACTS_TIMEOUT_S
    try:
        paths = (*task_root.glob("*.json"), *(task_root / ARCHIVE_DIR_NAME).glob("*.json"))
    except OSError as exc:
        raise BranchFactsError(FACTS_AUTHORSHIP_UNKNOWN, "RED_TEAM_REFUSED: task ledger unavailable") from exc
    for path in paths:
        try:
            task = read_task_record(path)
        except (OSError, ValueError) as exc:
            raise BranchFactsError(FACTS_AUTHORSHIP_UNKNOWN, f"task record {path} unreadable") from exc
        if not isinstance(task, dict) or task.get("status") == "dry_run":
            continue
        receipt = task.get("authoring_review_admission")
        if (
            not isinstance(receipt, dict)
            or receipt.get("repository") != repository
            or receipt.get("head_branch") != branch
        ):
            continue
        if receipt.get("review_plan") != "red_team" or not receipt.get("unknown_history") or receipt.get("refusal"):
            continue
        history = receipt["unknown_history"]
        admitted = receipt.get("head_sha")
        remote = receipt.get("history_remote_head_sha")
        reviewer = receipt.get("reviewer")
        if (
            receipt.get("check") != "structural"
            or receipt.get("applicable") is not True
            or "assumed_model" not in receipt
            or receipt["assumed_model"] is not None
            or not isinstance(reviewer, dict)
            or reviewer.get("review_mode") != "red_team"
            or not isinstance(history, list)
            or not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in history)
            or not isinstance(admitted, str)
            or not SHA.fullmatch(admitted)
            or not isinstance(remote, str)
            or not SHA.fullmatch(remote)
        ):
            raise BranchFactsError(FACTS_AUTHORSHIP_UNKNOWN, "historical authorship admission receipt malformed")
        ancestors = set(
            _facts_git(
                repo_root,
                ["rev-list", head_sha],
                deadline=deadline,
                code=FACTS_AUTHORSHIP_UNKNOWN,
            )
            .decode("ascii")
            .split()
        )
        if admitted not in ancestors:
            continue
        admitted_ancestors = set(
            _facts_git(
                repo_root,
                ["rev-list", admitted],
                deadline=deadline,
                code=FACTS_AUTHORSHIP_UNKNOWN,
            )
            .decode("ascii")
            .split()
        )
        remote_ancestors = set(
            _facts_git(
                repo_root,
                ["rev-list", remote],
                deadline=deadline,
                code=FACTS_AUTHORSHIP_UNKNOWN,
            )
            .decode("ascii")
            .split()
        )
        if remote not in admitted_ancestors or not set(history) <= remote_ancestors:
            raise BranchFactsError(
                FACTS_AUTHORSHIP_UNKNOWN, "historical authorship admission receipt conflicts with history"
            )
        allowed.update(history)
    return tuple(sorted(allowed))


def _task_flag_values(task: dict[str, Any], key: str) -> tuple[str, ...]:
    value = task.get(key)
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RecordError(f"review task {key} malformed")
    return tuple(value)


def _require_qualified_reviewer(
    facts: BranchReviewFacts, *, task: dict[str, Any], model: str, family: str, review_mode: str = "cross_family"
) -> None:
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
    # Lane flags and task-family aliases classify a review as Ukrainian even
    # when the profile field says code. The seat allowlist covers that too.
    if is_ukrainian_review(task) and (agent, family) not in UKRAINIAN_SEAT_ROUTES:
        raise RecordError("reviewer not qualified: Ukrainian review needs a Gemini or Sol seat")
    if profile == "ukrainian":
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
    inputs = facts.resolver_inputs(
        risk=str(task.get("review_risk") or "medium"),
        review_profile=profile,
        author_model=task.get("review_author_model") or "" if review_mode == "red_team" else "",
        # The reviewer ran as the account its own task record names (#10630); no quota decides a finished review.
        claude_account=account_from_record(task, agent=agent),
        structural=True,
    )
    results = [evaluate_candidate(candidate, inputs, review_mode=review_mode) for candidate in candidates]
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
def pr_lock(repository: str, number: int, lock_root: Path):
    """Serialize publication on one PR across its heads, so the comments a poster checked still hold."""
    lock_root.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(f"{repository}\0pr\0{number}".encode()).hexdigest() + ".lock"
    with (lock_root / name).open("a+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _coverage_tokens(
    denominator: Iterable[str] | None,
    coverage: Iterable[str] | None,
    void: str | None,
) -> tuple[str, str, str] | None:
    """Marker tokens for a chunk, or None when this verdict declares no item denominator."""
    if denominator is None and coverage is None and void is None:
        return None
    if denominator is None or coverage is None:
        raise RecordError("item coverage requires both a denominator and a coverage set")
    if void is not None and void not in CHUNK_VOIDS:
        raise RecordError("unknown chunk void reason")
    declared = tuple(denominator)
    covered = tuple(coverage)
    if not declared or declared != tuple(sorted(set(declared))):
        raise RecordError("denominator must be sorted, unique and non-empty")
    if any(ITEM_ID_RE.fullmatch(item) is None for item in declared):
        raise RecordError("item id is not a marker token")
    if void is not None:
        if covered:
            raise RecordError("a voided chunk covers no items")
        return ",".join(declared), "-", void
    if covered != tuple(sorted(set(covered))) or not set(covered) <= set(declared):
        raise RecordError("coverage must be a sorted unique subset of the denominator")
    if not covered:
        raise RecordError("a chunk verdict with no covered items needs a void reason")
    if any(ITEM_ID_RE.fullmatch(item) is None for item in covered):
        raise RecordError("item id is not a marker token")
    return ",".join(declared), ",".join(covered), ""


def build_comment(
    *,
    sha: str,
    task_id: str,
    started: str,
    verdict: str,
    model: str,
    family: str,
    reply: str,
    review_mode: str = "cross_family",
    review_profile: str = "code",
    sources_mcp_call_count: int | None = None,
    unknown_history: Iterable[str] = (),
    withheld_findings: int | Literal["unknown"] | None = None,
    app_bot: bool = False,
    score: int | None = None,
    author_models: Iterable[str | None] = (),
    denominator: Iterable[str] | None = None,
    coverage: Iterable[str] | None = None,
    void: str | None = None,
    residuals: Iterable[str] | None = None,
    repair_withheld: bool = False,
) -> str:
    if not SHA.fullmatch(sha):
        raise RecordError("reviewed SHA must be a full 40-hex commit SHA")
    if review_mode not in {"cross_family", "red_team"}:
        raise RecordError("unsupported review mode")
    reply = reply.replace(MARKER_PREFIX, "&lt;" + MARKER_PREFIX[1:])
    if MARKER_PREFIX in reply:
        raise RecordError("review reply contains reserved verdict marker")
    mode_field = " review_mode=red_team" if review_mode == "red_team" else ""
    history = tuple(sorted(set(unknown_history)))
    if history and (review_mode != "red_team" or not all(SHA.fullmatch(sha) for sha in history)):
        raise RecordError("unknown history requires red_team and full commit SHAs")
    history_field = f" unknown_history={','.join(history)}" if history else ""
    authorship_field = f" authorship={VERIFIED_APP_BOT}" if app_bot else ""
    ukrainian = is_ukrainian_review({"review_profile": review_profile})
    _require_sources_mcp_calls({"review_profile": review_profile, "sources_mcp_call_count": sources_mcp_call_count})
    profile_field = " review_profile=ukrainian" if ukrainian else ""
    sources_field = f" sources_calls={sources_mcp_call_count}" if sources_mcp_call_count is not None else ""
    tokens = _coverage_tokens(denominator, coverage, void)
    coverage_field = ""
    coverage_lines = ""
    if tokens is not None:
        declared_token, covered_token, void_token = tokens
        coverage_field = f" denominator={declared_token} coverage={covered_token}"
        coverage_lines = f"Denominator: {declared_token}\nCoverage: {covered_token}\n"
        if void_token:
            coverage_field += f" void={void_token}"
            coverage_lines += f"Chunk void: {void_token}\n"
    # The score is advisory (C-3020): stored for calibration, never read by a gate.
    score_text = f"{score}/10" if score is not None else "absent"
    authors = sorted({author for author in author_models if author})
    marker = (
        f"<!-- cf-verdict v1 sha={sha} task={task_id} started={started} verdict={verdict} "
        f"model={model} family={family}{mode_field}{history_field}{authorship_field}{profile_field}{sources_field}"
        f"{coverage_field} -->"
    )
    prefix = (
        ("### Adversarial red-team review\n" if review_mode == "red_team" else "### Cross-family review\n")
        + ("Review mode: red_team\n" if review_mode == "red_team" else "")
        + (
            f"Historical authorship: unknown_historical\nUnknown history: {','.join(history)}\nNo author model assumed.\n"
            if history
            else ""
        )
        + (f"Authorship: {VERIFIED_APP_BOT}\n" + ("" if history else "No author model assumed.\n") if app_bot else "")
        + ("Review profile: ukrainian\n" if ukrainian else "")
        + (f"Sources MCP calls: {sources_mcp_call_count}\n" if sources_mcp_call_count is not None else "")
        + f"head: {sha}\n"
        f"Reviewer family: {family}\n"
        f"VERDICT: {verdict}\n"
        f"Reviewer model: {model}\n"
        f"Review score: {score_text}\n"
        + (f"Authored by: {', '.join(authors)}\n" if authors else "")
        + f"Task id: {task_id}\n"
        + coverage_lines
        + "\n"
    )
    residual_ids = tuple(residuals or ())
    if any(_RESIDUAL_ID.fullmatch(item) is None for item in residual_ids):
        raise RecordError("residual finding id is not a marker token")
    # Listed after the reply so the record prefix stays the marker's fixed lines.
    residual_line = ""
    if residual_ids:
        residual_line = "Residuals: " + ", ".join(f"{item} (P3)" for item in residual_ids) + "\n\n"
    if withheld_findings is not None:
        return prefix + f"Withheld findings: {withheld_findings}\n" + "Findings are held privately.\n\n" + marker
    prefix += "<details><summary>Reviewer's reply</summary>\n\n"
    repair_note = f"{REPAIR_WITHHELD}\n\n" if repair_withheld else ""
    suffix = f"\n\n</details>\n\n{residual_line}{repair_note}{marker}"
    available = MAX_COMMENT_BYTES - len((prefix + suffix).encode())
    if available < 0:
        raise RecordError("comment metadata exceeds GitHub limit")
    if len(reply.encode()) > available:
        flag = f"\n\n{TRUNCATION_FLAG}"
        available -= len(flag.encode())
        if available < 0:
            raise RecordError("comment metadata exceeds GitHub limit")
        reply = reply.encode()[:available].decode("utf-8", errors="ignore") + flag
    return prefix + reply + suffix


def _reviewed_tree_entries(primary_root: Path, sha: str, directory: PurePosixPath) -> dict[str, str]:
    """Git mode of each entry in one directory of the reviewed commit; empty when unreadable."""
    listed = [] if directory == PurePosixPath(".") else ["--", f"{directory}/"]
    try:
        output = _facts_git(
            primary_root,
            ["--literal-pathspecs", "ls-tree", "-z", sha, *listed],
            deadline=time.monotonic() + _GIT_STEP_TIMEOUT_S,
            code=FACTS_TARGET_UNKNOWN,
        )
    except BranchFactsError:
        return {}
    entries = {}
    for entry in output.decode("utf-8", errors="surrogateescape").split("\0"):
        meta, tab, name = entry.partition("\t")
        if tab:
            entries[name] = meta.split(" ", 1)[0]
    return entries


def _removed_checkout_root(root: Path, primary_root: Path, sha: object) -> bool:
    """Whether ``root`` is a reviewed checkout that no longer exists, recorded inside the primary checkout.

    The dispatcher removes a read-only reviewer's worktree when its task settles,
    usually before the verdict is recorded. Its citations are then checked
    against the reviewed commit, which is what that worktree held.
    """
    if not isinstance(sha, str) or not SHA.fullmatch(sha) or ".." in root.parts or os.path.lexists(root):
        return False
    resolved_primary = primary_root.resolve(strict=True)
    # Existing ancestors resolve, so a symlinked parent cannot carry the root outside.
    resolved_root = root.resolve()
    return resolved_root != resolved_primary and resolved_root.is_relative_to(resolved_primary)


def repository_relative_reply(reply: str, *, task: dict[str, Any], primary_root: Path) -> str:
    """Rewrite checkout citations on scanner-stable lines; scan the final text."""
    checkout = task.get("worktree_path")
    roots = [primary_root]
    if isinstance(checkout, str) and Path(checkout).is_absolute():
        roots.insert(0, Path(checkout))
    reviewed = task.get("worktree_base_sha")

    def removed_checkout_citation(cited: PurePosixPath, suffix: str) -> bool:
        if cited == PurePosixPath("."):
            return not suffix
        entries = _reviewed_tree_entries(primary_root, reviewed, cited.parent)
        mode = entries.get(cited.as_posix())
        if suffix:
            # A file literally named with the annotation would make the citation ambiguous.
            return mode in {"100644", "100755"} and f"{cited}{suffix}" not in entries
        return mode in {"100644", "100755", "120000", "040000"}

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
                if root is not primary_root and _removed_checkout_root(root, primary_root, reviewed):
                    cited = PurePosixPath(path.relative_to(root).as_posix())
                    return cited.as_posix() + suffix if removed_checkout_citation(cited, suffix) else token
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


def _review_branch(task: dict[str, Any]) -> str:
    """Resolve reviewed identity without making it a checkout or cleanup branch."""
    from scripts.common.git_context import UnsafeBranchNameError, validate_plain_branch_name
    from scripts.guardrails.worktree_containment import PROTECTED_BRANCHES

    if any(task.get(key) for key in ("trial_label", "trial_role", "trial_qualified_task")):
        raise RecordError("MODEL_ROLE_TRIAL_REFUSED: a trial never supplies review of record")

    # V2 owns a separate checkout branch; only review_branch identifies its PR.
    fields = ("review_branch",) if task.get("schema_version") == 2 else ("review_branch", "worktree_branch")
    branches = []
    for field in fields:
        value = task.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            raise RecordError("invalid review branch identity")
        try:
            branch = validate_plain_branch_name(value, repo_root=".")
        except UnsafeBranchNameError as exc:
            raise RecordError("invalid review branch identity") from exc
        if branch in PROTECTED_BRANCHES:
            raise RecordError("protected review branch identity")
        branches.append(branch)
    if not branches:
        raise RecordError("review was not branch-pinned; re-run with --branch <PR head ref>")
    if len(set(branches)) != 1:
        raise RecordError("conflicting review branch identities")
    return branches[0]


def _task(task_id: str, task_root: Path) -> tuple[dict[str, Any], str]:
    """Detect accidental result edits before deriving a publication copy.

    A deliberate same-user writer can also replace the record's stored hash.
    """
    if not TASK_ID.fullmatch(task_id):
        raise RecordError("invalid task id")
    task_path = _hot_or_archived(task_root, f"{task_id}.json")
    # An archived review keeps its reply beside its record.
    result_path = task_path.with_suffix(".result")
    try:
        task = json.loads(task_path.read_text(encoding="utf-8"))
        raw_reply = result_path.read_bytes()
    except (OSError, ValueError) as exc:
        raise RecordError("review task record or reply unavailable") from exc
    if not isinstance(task, dict):
        raise RecordError("review task record malformed")
    if task.get("status") != "done":
        raise RecordError("review task is not done")
    expected = task.get("result_sha256")
    if expected is not None and hashlib.sha256(raw_reply).hexdigest() != expected:
        raise RecordError(f"terminal_result_digest_mismatch: task {task_id}; writer unknown")
    try:
        # Preserve read_text's universal-newline behaviour after checking the raw bytes.
        reply = raw_reply.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise RecordError("review task record or reply unavailable") from exc
    _review_branch(task)
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


def require_no_outside_rejection(comments: Any, sha: str) -> None:
    """A red-team review cannot supersede recorded outside-family dissent (#10437)."""
    if not isinstance(comments, Sequence) or isinstance(comments, (str, bytes)):
        raise RecordError("RED_TEAM_REFUSED: verdict marker data unavailable")
    for item in comments:
        body = item.get("body") if isinstance(item, Mapping) else None
        if not isinstance(body, str):
            raise RecordError("RED_TEAM_REFUSED: verdict marker data unavailable")
        if MARKER_PREFIX not in body:
            continue
        # Older records may retain the reviewer's REQUEST_CHANGES spelling.
        normalized = body.replace("verdict=REQUEST_CHANGES ", "verdict=CHANGES_REQUESTED ").replace(
            "VERDICT: REQUEST_CHANGES\n", "VERDICT: CHANGES_REQUESTED\n"
        )
        marker = parse_marker(normalized)
        if marker is None:
            raise RecordError("RED_TEAM_REFUSED: verdict marker data unavailable")
        if (
            marker["sha"] == sha
            and marker.get("review_mode", "cross_family") != "red_team"
            and marker["verdict"] in REJECTED
        ):
            raise RecordError("RED_TEAM_REFUSED: outside-family rejection exists for this head")


def require_resolved_branch_authors(facts: BranchReviewFacts) -> None:
    """Refuse a review when any branch commit's author family is unknown (C-2902 F1, F5, F9).

    An unknown author excludes no family and has no model, so no reviewer
    can be proved independent of it, in either review mode. A trailer task id
    without a task record is unknown on every harness. The family is read from
    the commit's ``X-Agent`` trailer (or the task record it names), never from
    the git author: the trailer is author-controlled, so a readable catalog
    trailer is trusted as that family. This refuses unresolvable attribution;
    it does not detect a forged catalog trailer. Untrailered history a red-team
    admission receipt froze keeps its own rules (``unresolved_authors``).
    """
    if facts.unresolved_authors:
        raise RecordError(
            "AUTHOR_UNRESOLVED: branch commits have no resolvable author family "
            f"({', '.join(facts.unresolved_authors)}); no reviewer can be proved outside them"
        )


def require_no_same_head_rejection(comments: Sequence[Mapping[str, Any]], sha: str, login: str, verdict: str) -> None:
    """Refuse an APPROVE the keeper would not land at this head, in every review mode (FR-06).

    The keeper's own reading decides: a same-head approval never clears a
    same-head rejection, and an unknown head (an edited or unattested marker,
    ``integration_sweep.lookup_verdict``) admits no approval, so the recorder
    never posts an approval the keeper would ignore.
    """
    if verdict != "APPROVED":
        return
    current = lookup_verdict(comments, sha, login)
    if current.state in REJECTED:
        raise RecordError(
            "APPROVE_REFUSED: a CHANGES_REQUESTED or BLOCKED verdict is recorded at this head; "
            "only an APPROVE at a new head clears it"
        )
    if current.state == "unknown":
        raise RecordError(
            f"APPROVE_REFUSED: the merge-queue keeper reads this head's verdict as unknown ({current.reason}) "
            "and would not land an APPROVE; escalate the verdict record or review a new head"
        )


def review_round_budget(facts: BranchReviewFacts) -> int:
    """Rounds one PR may spend: 5 on a security-sensitive change, else 3 (C-2902).

    The tier comes from the branch's own changed paths, the shared rule that
    raises a security-sensitive target to critical. The review task's
    caller-supplied risk never raises it: the dispatcher of a review can be
    the author.
    """
    if is_security_sensitive_change(facts.changed_paths, facts.scope_paths):
        return ELEVATED_REVIEW_ROUNDS
    return DEFAULT_REVIEW_ROUNDS


def _trusted_markers(comments: Sequence[Mapping[str, Any]], login: str) -> list[tuple[int, dict[str, Any]]]:
    """Comment index and parsed marker of each verdict ``login`` posted with a trusted association."""
    markers: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(comments):
        body = item.get("body") if isinstance(item, Mapping) else None
        if not isinstance(body, str) or MARKER_PREFIX not in body:
            continue
        if item.get("user", {}).get("login") != login or item.get("author_association") not in TRUSTED_ASSOCIATIONS:
            continue
        marker = parse_marker(body)
        if marker is not None:
            markers.append((index, marker))
    return markers


def _trusted_verdict_shas(comments: Sequence[Mapping[str, Any]], login: str) -> set[str]:
    """Heads named by verdict markers ``login`` posted with a trusted association."""
    return {marker["sha"] for _, marker in _trusted_markers(comments, login)}


# A post-approval base update is one merge, or a few; a longer first-parent walk is not one.
MAX_EXEMPT_BASE_MERGES = 10


def clean_base_merge_descent(repo_root: Path, *, approved: str, head: str, base_tip: str) -> list[str] | None:
    """The base commits ``head`` merges after ``approved``, when that is all it adds; else None.

    Every commit on the first-parent path from ``head`` back to ``approved``
    must be a Git-proven conflict-free merge of the base branch
    (:func:`_clean_merge_source`): its second parent is on ``base_tip`` and its
    tree is exactly Git's merge of its parents. A missing object, a conflict, a
    manual edit in a merge, any other commit, a path longer than
    ``MAX_EXEMPT_BASE_MERGES`` or a proof error proves nothing.
    """
    merged: list[str] = []
    current = head
    deadline = time.monotonic() + BRANCH_FACTS_TIMEOUT_S
    try:
        while current != approved:
            if len(merged) >= MAX_EXEMPT_BASE_MERGES:
                return None
            entry = _read_commit_entries(repo_root, [current], deadline=deadline)[0]
            if _clean_merge_source(entry, base_tip, checkout=repo_root) != CLEAN_BASE_MERGE:
                return None
            merged.append(entry["parents"][1]["sha"])
            current = entry["parents"][0]["sha"]
    except RecordError:
        return None
    return merged or None


def _clean_merge_descent_prover(
    repo_root: Path, head: str, *, fetch: bool = True
) -> Callable[[str, str], list[str] | None]:
    """:func:`clean_base_merge_descent` bound to the fetched default-branch tip, fetched once on first use.

    A tip that cannot be fetched proves no descent.
    """
    tip: list[str | None] = []

    def prove(approved: str, descendant: str) -> list[str] | None:
        if not tip:
            try:
                tip.append(default_branch_review_base(repo_root, head, fetch=fetch)[0])
            except RecordError:
                tip.append(None)
        base_tip = tip[0]
        if base_tip is None:
            return None
        return clean_base_merge_descent(repo_root, approved=approved, head=descendant, base_tip=base_tip)

    return prove


def _fully_approved(comments: Sequence[Mapping[str, Any]], head: str, login: str) -> bool:
    """Whether the keeper reads ``head`` as APPROVED, which needs every seat its profile requires (#12020)."""
    return lookup_verdict(comments, head, login).state == "APPROVED"


def budget_exempt_heads(
    comments: Sequence[Mapping[str, Any]],
    sha: str,
    login: str,
    *,
    prove: Callable[[str, str], list[str] | None],
    unrecorded: Iterable[str] = (),
) -> dict[str, dict[str, Any]]:
    """The reviewed heads, and ``sha``, that consume no review round, each with its receipt.

    A head is exempt when it descends from the last fully approved head before
    its first verdict only through clean merges of the base branch (``prove``,
    :func:`clean_base_merge_descent`). A head dispatched for review with no
    recorded verdict (``unrecorded``) is weighed like ``sha``, against the last
    fully approved head on record. The exemption changes accounting only:
    every head still needs its own exact-head verdict, no approval carries
    forward, a recorded rejection stands, and no verdict is dropped. Exemptions
    are re-proven from Git on every call, so a head whose proof is lost counts.
    """
    markers = _trusted_markers(comments, login)
    first: dict[str, int] = {}
    for index, marker in markers:
        first.setdefault(marker["sha"], index)
    order = sorted(first.items(), key=lambda item: item[1])
    order.extend((head, len(comments)) for head in dict.fromkeys([*sorted(unrecorded), sha]) if head not in first)
    exempt: dict[str, dict[str, Any]] = {}
    for head, start in order:
        prefix = comments[:start]
        latest: dict[str, int] = {}
        for index, marker in markers:
            if index < start:
                latest[marker["sha"]] = index
        anchor = next(
            (
                candidate
                for candidate, _ in sorted(latest.items(), key=lambda item: item[1], reverse=True)
                if _fully_approved(prefix, candidate, login)
            ),
            None,
        )
        if anchor is None:
            continue
        merges = prove(anchor, head)
        if merges:
            exempt[head] = {"approved_head": anchor, "base_merges": merges}
    return exempt


def require_review_round_within_budget(
    comments: Sequence[Mapping[str, Any]],
    sha: str,
    login: str,
    *,
    budget: int,
    pr: int,
    prove_merge_only: Callable[[str, str], list[str] | None] | None = None,
    grant: Callable[[], dict[str, Any] | None] | None = None,
    repair: Callable[[], dict[str, Any] | None] | None = None,
    repair_heads: frozenset[str] = frozenset(),
    dispatched_heads: Callable[[], frozenset[str]] | None = None,
) -> dict[str, Any]:
    """Refuse a verdict that would open a review round beyond this PR's budget.

    A round is one reviewed head: trusted verdicts on this PR are counted
    across heads, and more verdicts at an already reviewed head (a quorum seat,
    a later chunk of the same review, or a retried publication) open no new round.
    A round is spent when its
    reviewer is dispatched, so the head of every review run on record counts
    too, its verdict recorded or not (``review_lineage.dispatched_rounds``,
    #12098): ``dispatched_heads`` returns those heads other than ``sha``, read
    only for a new head. Earlier PRs are not read: no GitHub listing finds them
    reliably (search index lag, the 250-commit PR listing cap). Budget end is
    never approval.

    A head that only merges the base branch cleanly after the last fully
    approved head consumes no round (:func:`budget_exempt_heads`, proven with
    ``prove_merge_only``); it is checked only once the counted heads reach the
    budget. A sealed elevated-tier grant (``scripts/review/budget_grant.py``)
    admits rounds up to ``ELEVATED_REVIEW_ROUNDS`` in total: ``grant`` returns
    its receipt, None when the PR has no grant, or refuses. The lineage's one
    repair-verification round (``scripts/review/repair_round.py``) is outside
    the budget: ``repair`` returns its receipt or refuses, and ``repair_heads``
    names the heads it already admitted, which count as no budgeted round.
    Returns the result fields that record the exception used, else nothing.
    """
    recorded = _trusted_verdict_shas(comments, login)
    if sha in recorded:
        return {}
    heads = recorded | (dispatched_heads() if dispatched_heads is not None else frozenset())
    if len(heads) < budget:
        return {}
    exempt = (
        budget_exempt_heads(comments, sha, login, prove=prove_merge_only, unrecorded=heads - recorded)
        if prove_merge_only
        else {}
    )
    if sha in exempt:
        return {"budget_exemption": {"reason": CLEAN_BASE_MERGE, **exempt[sha]}}
    counted = heads - set(exempt) - repair_heads
    if len(counted) < budget:
        return {}
    unrecorded = sorted(counted - recorded)
    if unrecorded:
        listed = ", ".join(head[:12] for head in unrecorded)
        note = f" ({len(unrecorded)} dispatched with no recorded verdict: {listed})"
    else:
        note = ""
    if exempt:
        note += f" (and {len(exempt)} clean base merge head(s), which consume no round)"
    exhausted = (
        f"REVIEW_BUDGET_EXHAUSTED: PR #{pr} already has verdicts at {len(counted)} heads{note} and its budget "
        f"is {budget} rounds; budget end is never approval, escalate instead of recording round {len(counted) + 1}"
    )
    refusals: list[str] = []
    admissions = (
        ("budget_grant", grant, budget < len(counted) + 1 <= ELEVATED_REVIEW_ROUNDS),
        # Once per lineage: only a retry of the round already admitted at this head may run it again.
        ("repair_round", repair, not repair_heads - {sha}),
    )
    for field, admit, applies in admissions:
        if admit is None or not applies:
            continue
        try:
            receipt = admit()
        except RecordError as exc:
            refusals.append(str(exc))
            continue
        if receipt is not None:
            return {field: receipt}
    raise RecordError("; ".join([exhausted, *refusals]))


def _budget_grant(**kwargs: Any) -> dict[str, Any] | None:
    # The grant check builds on this module, so it is imported only when the default budget is spent.
    from scripts.review.budget_grant import admit_grant_round

    return admit_grant_round(**kwargs)


def _repair_round(**kwargs: Any) -> dict[str, Any] | None:
    # The repair round builds on this module, so it is imported only when the budget is spent.
    from scripts.review.repair_round import admit_repair_round

    return admit_repair_round(**kwargs)


def _dispatched_rounds(
    *,
    task_root: Path,
    repository: str,
    number: int,
    branch: str,
    comments: Sequence[Mapping[str, Any]],
    login: str,
    sha: str,
) -> dict[str, list[str]]:
    """Heads other than ``sha`` that a review run on record was dispatched at, with its task ids (#12098).

    An unreadable task ledger or reply refuses: those heads cannot be counted.
    """
    # The lineage reader builds on this module, so it is imported only when a new head is counted.
    from scripts.review.review_lineage import dispatched_rounds, lineage_runs

    runs = lineage_runs(task_root, repository=repository, number=number, branch=branch)
    return dispatched_rounds(runs=runs, comments=comments, login=login, exclude_head=sha)


def _repair_receipts(task_root: Path) -> Path:
    """Where the repair rounds' durable receipts live: beside the task ledger, never removed."""
    from scripts.review.repair_round import RECEIPT_DIR

    return task_root.parent / RECEIPT_DIR


def budget_admission(
    *,
    repository: str,
    number: int,
    branch: str,
    sha: str,
    facts: BranchReviewFacts,
    comments: Sequence[Mapping[str, Any]],
    login: str,
    task_root: Path,
    review_root: Path,
    fetch: bool = True,
    dispatched: Callable[[], dict[str, list[str]]] | None = None,
) -> dict[str, Any]:
    """The round decision for a verdict at ``sha``, shared by the recorder and ``budget-check``.

    It writes nothing; ``fetch=False`` also leaves the default-branch ref as it is.
    ``dispatched`` is the caller's own :func:`_dispatched_rounds` read, when it reports them too.
    """
    rounds = dispatched or partial(
        _dispatched_rounds,
        task_root=task_root,
        repository=repository,
        number=number,
        branch=branch,
        comments=comments,
        login=login,
        sha=sha,
    )
    from scripts.review.repair_round import repair_heads

    budget = review_round_budget(facts)
    receipts = _repair_receipts(task_root)
    return require_review_round_within_budget(
        comments,
        sha,
        login,
        budget=budget,
        pr=number,
        prove_merge_only=_clean_merge_descent_prover(review_root, sha, fetch=fetch),
        # A change whose paths already give it five rounds needs no grant.
        grant=partial(
            _budget_grant,
            repository=repository,
            number=number,
            branch=branch,
            changed_paths=facts.changed_paths,
            comments=comments,
            login=login,
            task_root=task_root,
        )
        if budget < ELEVATED_REVIEW_ROUNDS
        else None,
        repair=partial(
            _repair_round,
            repository=repository,
            number=number,
            branch=branch,
            head=sha,
            comments=comments,
            login=login,
            task_root=task_root,
            repo_root=review_root,
            receipt_root=receipts,
            fetch=fetch,
        ),
        repair_heads=repair_heads(receipts, repository=repository, number=number, branch=branch),
        dispatched_heads=lambda: frozenset(rounds()),
    )


def require_no_outside_review_in_flight(task_root: Path, repository: str, sha: str) -> None:
    """Read the active task ledger before red-team admission or publication."""
    try:
        # The shared iterator suppresses enumeration errors. Read locally so
        # both an unreadable directory and a failed glob refuse this guard.
        list(task_root.iterdir())
        for path in sorted(path for path in task_root.glob("*.json") if path.is_file()):
            task = read_task_record(path)
            if task is None:
                continue
            if any(task.get(key) for key in ("trial_label", "trial_role", "trial_qualified_task")):
                continue
            prep = task.get("worktree_prep")
            prep_sha = prep.get("base_sha") if isinstance(prep, dict) else None
            prep_matches = (
                isinstance(prep_sha, str)
                and SHA.fullmatch(prep_sha.casefold())
                and prep_sha.casefold() == sha.casefold()
            )
            # Prep rows lack review typing and repository metadata. Fail closed:
            # even non-review dispatches preparing this head briefly block red-team.
            review = (
                task.get("review")
                or task.get("pr") is not None
                or task.get("review_attempt")
                or task.get("require_review_verdict")
                or task.get("review_profile")
                or task.get("review_author_model")
                or task.get("review_risk")
                or task.get("type") == "review"
            )
            if (
                (review or prep_matches)
                and (
                    (
                        isinstance(task.get("repository"), str)
                        and normalize_repository(task["repository"]) == normalize_repository(repository)
                    )
                    or (prep_matches and task.get("repository") is None)
                )
                and task.get("status") in {"spawning", "running", "queued"}
                and task.get("review_mode", "cross_family") != "red_team"
                and (
                    prep_matches
                    or sha
                    in {
                        task.get(field)
                        for field in (
                            "pinned_head",
                            "worktree_base_sha",
                            "review_head",
                            "review_head_sha",
                            "pr_head_sha",
                            "head_sha",
                        )
                    }
                )
            ):
                raise RecordError("RED_TEAM_REFUSED: outside-family review in flight for this head")
    except (OSError, ValueError, TypeError) as exc:
        raise RecordError("RED_TEAM_REFUSED: task ledger unavailable") from exc


def _native_grok_reviewer_identity() -> tuple[str, list[str]]:
    """Resolve the native review holder and its own runtime attestations."""
    catalog = load_model_catalog()
    holder = resolve_routing_reference({"role": "legacy_reviewers", "seat": "xai_reviewer"}, catalog)
    return holder, catalog["models"][holder].get("runtime_model_ids", [])


def _require_formal_reviewer(
    *,
    cursor: bool,
    reported: object,
    model: str,
    family: str,
    native_grok: bool = False,
    review_context: Mapping[str, Any] | None = None,
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
        admitted = family not in NATIVE_NON_REVIEWER_FAMILIES or (
            native_grok and model == _native_grok_reviewer_identity()[0]
        )
    if not admitted:
        raise RecordError(f"reviewer model unknown: {model!r} is not a formal reviewer on this harness")
    # #9583: a model the catalog gives no review role never approves, on any harness.
    if refusal := activity_role_refusal(model, REVIEW_ACTIVITY, review_context=review_context):
        raise RecordError(f"reviewer model refused: {refusal}")


def reviewer_identity(task: Mapping[str, Any]) -> tuple[str, str]:
    """The attested reviewer model and family of a review task record, or a refusal.

    The recorder publishes a verdict only for this identity; the approval
    carry-over applies the same rule to every run in a PR's review lineage.
    """
    if any(task.get(key) for key in ("trial_label", "trial_role", "trial_qualified_task")):
        raise RecordError("MODEL_ROLE_TRIAL_REFUSED: a trial never supplies review of record")
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
        holder, admitted_runtime_ids = _native_grok_reviewer_identity()
        if not isinstance(reported, str) or reported not in admitted_runtime_ids:
            raise RecordError("native Grok reviewer model unknown: runtime model is not admitted")
        model = holder
    if not isinstance(model, str) or not model or re.search(r"\s", model):
        raise RecordError("reviewer model unknown")
    family = resolve_family(model)
    if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
        raise RecordError("reviewer family unknown")
    _require_formal_reviewer(
        cursor=cursor,
        reported=reported,
        model=model,
        family=family,
        native_grok=native_grok,
        review_context={
            "review_mode": task.get("review_mode"),
            "review_profile": task.get("review_profile"),
            "author_model": task.get("review_author_model"),
            "transport": "native_codex" if task.get("agent") == "codex" else task.get("agent"),
        },
    )
    return model, family


@dataclass(frozen=True)
class _TaskVerdict:
    repository: str
    branch: str
    sha: str
    model: str
    family: str
    verdict: str
    finding_count: int | Literal["unknown"]
    ukrainian: bool
    sources_count: int | None
    started: str


def _task_verdict(task: dict[str, Any], reply: str) -> _TaskVerdict:
    """The verdict a finished review task's record and sealed reply attest, or a refusal."""
    repository = task.get("repository")
    branch = _review_branch(task)
    sha = task.get("worktree_base_sha")
    if not isinstance(repository, str) or "/" not in repository:
        raise RecordError("review repository unavailable")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise RecordError("reviewed SHA missing or invalid")
    if task.get("pinned_head") is not None and task["pinned_head"] != sha:
        raise RecordError("reviewed SHA conflicts with pinned head")
    model, family = reviewer_identity(task)
    verdict, finding_count = _review_verdict_and_count(reply)
    _require_sources_mcp_calls(task)
    sources_count = task.get("sources_mcp_call_count")
    if type(sources_count) is not int or sources_count < 0:
        sources_count = None
    started_dt = datetime.fromisoformat(str(task.get("started_at") or "").replace("Z", "+00:00"))
    if started_dt.tzinfo is None:
        raise RecordError("review start timestamp missing timezone")
    started = started_dt.astimezone(UTC).isoformat(timespec="microseconds")
    return _TaskVerdict(
        repository,
        branch,
        sha,
        model,
        family,
        verdict,
        finding_count,
        is_ukrainian_review(task),
        sources_count,
        started,
    )


def _review_repository_root(repository: str, root: Path) -> Path:
    """The registered primary checkout of the task's target repository."""
    try:
        repo_keys = [key for key, repo in load_fleet_repos().items() if repo.github.casefold() == repository.casefold()]
        if len(repo_keys) != 1:
            raise RecordError("review repository is not uniquely registered")
        return resolve_review_repository(root, repo_keys[0], mode="pr")
    except (FleetRepoError, TargetResolutionError, OSError, subprocess.TimeoutExpired):
        raise RecordError("review repository checkout unavailable") from None


def _post_verdict(repository: str, number: int, comment: str, login: str) -> dict[str, Any]:
    """Post one verdict comment and read it back unedited from ``login``; returns the read-back comment."""
    data = _run_json(
        # The typed record is the publisher's only admitted marker carrier (#11127).
        Request("issue-comment-json", repo=repository, number=number, body=CfVerdictRecord(comment)),
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
    return readback


def _item_chunk(task: Mapping[str, Any], reply: str, verdict: str) -> ItemChunk | None:
    """Coverage declared by the frozen brief, or None when the brief has no item denominator."""
    try:
        packet = load_frozen_item_packet(task)
        if packet is None and not reply_has_item_judgments(reply):
            return None
        if packet is None:
            raise ContractError(
                "ITEM_JUDGMENTS_WITHOUT_DENOMINATOR: item judgments need the brief's frozen item packet"
            )
        return judge_item_reply(packet, reply, stated=verdict, ukrainian=is_ukrainian_review(task))
    except ContractError as exc:
        raise RecordError(str(exc)) from None


@publication_boundary(RecordError)
def record(
    task_id: str,
    *,
    pr_number: int | None = None,
    task_root: Path | None = None,
    lock_root: Path | None = None,
    review_mode: str | None = None,
    red_team_prompt: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root() if task_root is None or lock_root is None else None
    task_root = task_root or root / "batch_state" / "tasks"
    lock_root = lock_root or root / "batch_state" / "locks"
    task, reply = _task(task_id, task_root)
    review_mode = review_mode if review_mode is not None else task.get("review_mode", "cross_family")
    if not isinstance(review_mode, str) or review_mode not in {"cross_family", "red_team"}:
        raise RecordError("unsupported review mode")
    if task.get("review_mode", "cross_family") != review_mode:
        if review_mode == "red_team":
            raise RecordError("review mode conflicts with task: red_team requires stored review_mode=red_team")
        raise RecordError("review mode conflicts with task")
    if review_mode == "red_team":
        if is_ukrainian_review(task) or str(task.get("research_track") or "").strip().casefold().startswith("l2-uk"):
            raise RecordError("RED_TEAM_REFUSED: Ukrainian-language reviews stay cross-family")
        if str(task.get("review_profile") or "code").strip().casefold() != "code":
            raise RecordError("RED_TEAM_REFUSED: code review requires review_profile=code")
        try:
            prompt = red_team_prompt.read_text(encoding="utf-8") if red_team_prompt is not None else ""
        except (OSError, UnicodeError) as exc:
            raise RecordError("red-team prompt unavailable") from exc
        if not re.search(r"\bred[-_ ]team\b", prompt, re.IGNORECASE):
            raise RecordError("explicit adversarial red-team prompt required")
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if digest not in (task.get("prompt_sha256"), task.get("effective_prompt_sha256")):
            raise RecordError("red-team prompt digest does not match completed review task")
    elif red_team_prompt is not None:
        raise RecordError("red-team prompt requires review_mode=red_team")
    review = _task_verdict(task, reply)
    repository, branch, sha = review.repository, review.branch, review.sha
    model, family, stated, finding_count = review.model, review.family, review.verdict, review.finding_count
    ukrainian, sources_count, started = review.ukrainian, review.sources_count, review.started
    pr = _pr(repository, branch, pr_number)
    if pr.get("headRefName") != branch:
        raise RecordError("review branch does not match PR head ref")
    if pr.get("headRefOid") != sha:
        raise RecordError("PR head moved since review; re-run exact-head review")
    number = pr.get("number")
    if not isinstance(number, int) or number < 1:
        raise RecordError("PR number unavailable")
    # Task records and SHA locks stay in the provenance checkout. Git facts
    # and citations belong to the task's registered target repository.
    review_root = _review_repository_root(repository, root or _repo_root())
    unknown_history = (
        admitted_unknown_history(
            repository=repository,
            branch=branch,
            head_sha=sha,
            task_root=task_root,
            repo_root=review_root,
        )
        if review_mode == "red_team"
        else ()
    )
    facts = pr_review_facts(
        repository,
        number,
        head_sha=sha,
        task_root=task_root,
        repo_root=review_root,
        subject_seats=_task_flag_values(task, "review_subject_seats"),
        subject_families=_task_flag_values(task, "review_subject_families"),
        unknown_history=unknown_history,
    )
    if facts.unknown_history:
        frozen = task.get("review_branch_facts")
        if not isinstance(frozen, dict) or frozen.get("unknown_history") != list(facts.unknown_history):
            raise RecordError("unknown history conflicts with completed review task")
    if not facts.existing_families:
        raise RecordError("PR has no attributed author commits")
    if review_mode == "red_team":
        agent = str(task.get("agent") or "")
        reviewer_ids = {
            key
            for identity in (task_id, task.get("task_id"))
            if isinstance(identity, str)
            for key in review_task_id_comparison_keys(identity, agent=agent)
        }
        author_ids = {key for identity in facts.author_task_ids for key in review_task_id_comparison_keys(identity)}
        if reviewer_ids & author_ids:
            raise RecordError("SELF_REVIEW_DETECTED: reviewer task equals a branch author task")
        refusal = red_team_seat_refusal(
            (task.get("model"), task.get("resolved_model"), model),
            author_models=facts.author_models,
            author_model=task.get("review_author_model"),
            author_task_models=facts.author_task_models,
        )
        if refusal:
            raise RecordError(refusal)
    # Every mode, red team included (F9): an unresolved author has no model a seat rule can compare.
    require_resolved_branch_authors(facts)
    if review_mode != "red_team" and family in facts.excluded_families:
        raise RecordError("reviewer family equals an author family")
    _require_qualified_reviewer(facts, task=task, model=model, family=family, review_mode=review_mode)
    adapter = GitHubAdapter(Path.cwd())
    login = adapter.identity()
    reply = repository_relative_reply(reply, task=task, primary_root=review_root)
    chunk = _item_chunk(task, reply, stated)
    # The reply stays REQUEST_CHANGES. All-P3 open findings are an approval with residuals.
    residuals = p3_residuals(reply) if stated == "CHANGES_REQUESTED" else None
    verdict = "APPROVED" if residuals else stated
    comment_fields = dict(
        sha=sha,
        task_id=task_id,
        started=started,
        verdict=verdict,
        model=model,
        family=family,
        reply=reply,
        review_mode=review_mode,
        review_profile="ukrainian" if ukrainian else "code",
        sources_mcp_call_count=sources_count,
        unknown_history=facts.unknown_history,
        app_bot=bool(facts.app_bot_commits),
        score=review_score(reply),
        author_models=facts.author_models,
        denominator=None if chunk is None else chunk.denominator,
        coverage=None if chunk is None else chunk.coverage,
        void=None if chunk is None else chunk.void,
        residuals=residuals,
    )
    comment = build_comment(**comment_fields)
    destination = normalize_repository(repository)
    try:
        check_texts(destination, [comment], environment={})
    except PublishBlocked as exc:
        # Only a finding in this body permits a projection. Scanner availability
        # and publication failures retain their existing refusal behavior.
        if exc.indices != frozenset({0}):
            raise
        # Hidden findings cannot be listed, so the reply keeps its own verdict.
        if residuals is not None:
            residuals = None
            verdict = stated
            comment_fields["verdict"] = stated
            comment_fields["residuals"] = None
        comment = build_comment(**{**comment_fields, "reply": ""}, withheld_findings=finding_count)
        check_texts(destination, [comment], environment={})
    posted = False
    with pr_lock(repository, number, lock_root):
        # The PR may move while an earlier recorder owns the lock.
        current = _pr(repository, branch, number)
        if current.get("headRefOid") != sha:
            raise RecordError("PR head moved before publication")
        try:
            comments = adapter.comments(repository, number)
        except SweepError as exc:
            raise RecordError(f"comment lookup failed: {exc}") from exc
        # The capability failure module builds on this one, so it is imported only here.
        from scripts.review.capability_failure import require_unclassified

        require_unclassified(comments, login, task=task_id, started=started)
        if review_mode == "red_team":
            require_no_outside_rejection(comments, sha)
            require_no_outside_review_in_flight(task_root, repository, sha)
        if residuals is not None:
            reading = lookup_verdict(comments, sha, login)
            # A standing P0/P1/P2 or BLOCKED rejection, or an unknown head, keeps today's record.
            if reading.state in REJECTED or reading.state == "unknown":
                residuals = None
                verdict = stated
                comment_fields["verdict"] = stated
                comment_fields["residuals"] = None
                comment = build_comment(**comment_fields)
                check_texts(destination, [comment], environment={})
        budget_receipt = budget_admission(
            repository=repository,
            number=number,
            branch=branch,
            sha=sha,
            facts=facts,
            comments=comments,
            login=login,
            task_root=task_root,
            review_root=review_root,
        )
        from scripts.review.repair_round import (
            RepairRefused,
            receipt_at,
            record_admission,
            require_repair_verified,
        )

        repair = budget_receipt.get("repair_round")
        repaired = repair or receipt_at(
            _repair_receipts(task_root), repository=repository, number=number, branch=branch, head=sha
        )
        # A repair head stays changes-requested unless the reply attests that the delta is only the repair.
        if repaired is not None and residuals is not None:
            try:
                require_repair_verified(reply, repaired)
            except RepairRefused:
                residuals = None
                verdict = stated
                comment_fields["verdict"] = stated
                comment_fields["residuals"] = None
                comment = build_comment(**comment_fields, repair_withheld=True)
                check_texts(destination, [comment], environment={})
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
                        or marker["model"] != model
                        or marker["family"] != family
                        or marker.get("review_mode", "cross_family") != review_mode
                        or marker.get("unknown_history", []) != list(facts.unknown_history)
                        or marker.get("authorship") != (VERIFIED_APP_BOT if facts.app_bot_commits else None)
                        or marker.get("review_profile", "code") != ("ukrainian" if ukrainian else "code")
                        or marker.get("sources_calls") != sources_count
                        or list(marker.get("denominator") or ()) != list(chunk.denominator if chunk else ())
                        or list(marker.get("coverage") or ()) != list(chunk.coverage if chunk else ())
                        or marker.get("void") != (chunk.void if chunk else None)
                        or item.get("created_at") != item.get("updated_at")
                    ):
                        raise RecordError("existing verdict marker was edited or conflicts with task")
                    if marker["verdict"] == verdict:
                        existing = item
                        break
                    # The same reply recorded before P3 findings were accepted as residuals.
                    if residuals is not None and marker["verdict"] == "CHANGES_REQUESTED":
                        continue
                    raise RecordError("existing verdict marker was edited or conflicts with task")
        require_no_same_head_rejection(comments, sha, login, verdict)
        if repaired is not None and stated == "APPROVED":
            # The non-author reviewer, not the recorder, verifies that the delta is only the repair.
            require_repair_verified(reply, repaired)
        if repair is not None:
            # The admission receipt is durable before the verdict exists, so the round is spent even if posting fails.
            record_admission(_repair_receipts(task_root), repair)
        if existing is None:
            posted_comment = _post_verdict(repository, number, comment, login)
            posted = True
            comments = [*comments, posted_comment]
        if repair is not None:
            from scripts.review.repair_round import record_consumption

            record_consumption(
                _repair_receipts(task_root), repair, comment=str(posted_comment["id"] if posted else existing.get("id"))
            )
        state = "failure"
        pending_reason = ""
        if verdict == "APPROVED" or (chunk is not None and chunk.void):
            # Success is the keeper's own reading of the head with this record, never this
            # approval alone: another Ukrainian seat may still be missing (#12020), and a
            # declared item denominator may still be short (#12257). A voided chunk does not
            # count, so its own verdict does not decide the status.
            current = lookup_verdict(comments, sha, login)
            state = "success" if current.state == "APPROVED" else "failure" if current.state in REJECTED else "pending"
            if current.state == NEEDS_SEAT:
                profiled = [
                    marker
                    for item in comments
                    if isinstance(item.get("body"), str)
                    and (marker := parse_marker(item["body"])) is not None
                    and marker.get("sha") == sha
                    and (
                        marker.get("verdict") not in REJECTED
                        or (marker.get("verdict") == "CHANGES_REQUESTED" and p3_residuals(item["body"]) is not None)
                    )
                    and is_ukrainian_review(marker)
                ]
                open_seats = sorted(
                    required_ukrainian_seats(attested_author_families(profiled))
                    - set(current.ukrainian_seats)
                    - set(facts.excluded_families)
                )
                pending_reason = f"; awaiting Ukrainian seat: {'/'.join(open_seats) or 'none eligible'}"
            elif state == "pending":
                pending_reason = f"; head reads {current.state}"
        description = (
            f"review_mode=red_team unknown_history={len(facts.unknown_history)} "
            if facts.unknown_history
            else ("review_mode=red_team " if review_mode == "red_team" else "")
        ) + (
            f"VERDICT: {verdict} ({family}, sources={sources_count}) {task_id}"
            if ukrainian
            else f"VERDICT: {verdict} {family} {task_id}"
        )
        # The task id can be long; the pending reason must survive the 140-character limit.
        description = description[: 140 - len(pending_reason)] + pending_reason
        try:
            post_commit_status(
                repository=repository,
                head_sha=sha,
                state=state,
                context=DEFAULT_STATUS_CONTEXT,
                description=description,
            )
            status = "posted"
        except Exception as exc:
            status = f"failed: {exc}"
    result = {
        "pr": number,
        "head": sha,
        "task": task_id,
        "verdict": verdict,
        "score": comment_fields["score"],
        "review_mode": review_mode,
        "unknown_history": list(facts.unknown_history),
        "comment": "posted" if posted else "existing",
        "status": status,
    }
    if residuals:
        result["residuals"] = list(residuals)
    if facts.app_bot_commits:
        result.update({"authorship": VERIFIED_APP_BOT, "app_bot_commits": list(facts.app_bot_commits)})
    if chunk is not None:
        result["denominator"] = list(chunk.denominator)
        result["coverage"] = list(chunk.coverage)
        if chunk.void:
            result["void"] = chunk.void
    result.update(budget_receipt)
    return result


def budget_check(
    repository: str, number: int, *, task_root: Path | None = None, head: str | None = None
) -> dict[str, Any]:
    """The recorder's round decision for a verdict at the PR's current head, before any review runs.

    Every review run on record counts, its verdict recorded or not; ``unrecorded_rounds`` names
    each head that has runs but no recorded verdict, so a skipped recording is visible. ``head``,
    when given, must be the PR's current head.
    """
    root = _repo_root()
    task_root = task_root or root / "batch_state" / "tasks"
    pr = _run_json(["gh", "pr", "view", str(number), "--repo", repository, "--json", "headRefOid,headRefName,state"])
    if not isinstance(pr, dict) or pr.get("state") != "OPEN":
        raise RecordError(f"PR #{number} is not open")
    sha, branch = pr.get("headRefOid"), pr.get("headRefName")
    if not isinstance(sha, str) or not SHA.fullmatch(sha) or not isinstance(branch, str) or not branch:
        raise RecordError("PR head unavailable")
    if head is not None and head != sha:
        raise RecordError(f"PR #{number} head is {sha[:12]}, not the review head {head[:12]}")
    review_root = _review_repository_root(repository, root)
    # Read-only: the default-branch ref is read as it is, never fetched; a stale or missing one refuses.
    facts = pr_review_facts(repository, number, head_sha=sha, task_root=task_root, repo_root=review_root, fetch=False)
    adapter = GitHubAdapter(Path.cwd())
    login = adapter.identity()
    try:
        comments = adapter.comments(repository, number)
    except SweepError as exc:
        raise RecordError(f"comment lookup failed: {exc}") from exc
    heads = _trusted_verdict_shas(comments, login)
    dispatched = cache(
        partial(
            _dispatched_rounds,
            task_root=task_root,
            repository=repository,
            number=number,
            branch=branch,
            comments=comments,
            login=login,
            sha=sha,
        )
    )
    receipt = budget_admission(
        repository=repository,
        number=number,
        branch=branch,
        sha=sha,
        facts=facts,
        comments=comments,
        login=login,
        task_root=task_root,
        review_root=review_root,
        fetch=False,
        dispatched=dispatched,
    )
    already = sha in heads
    unrecorded = {head: tasks for head, tasks in dispatched().items() if head not in heads}
    return {
        "pr": number,
        "head": sha,
        "admitted": True,
        "reviewed_heads": len(heads | set(unrecorded)),
        "unrecorded_rounds": [{"head": head, "tasks": tasks} for head, tasks in sorted(unrecorded.items())],
        "budget": review_round_budget(facts),
        "head_already_reviewed": already,
        **receipt,
    }


def _open_pr_number(repository: str, branch: str) -> int | None:
    """The number of the one open PR whose head is ``branch``, None when it has none."""
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
            "number",
        ]
    )
    if not isinstance(matches, list) or len(matches) > 1:
        raise RecordError("branch must identify at most one open PR; pass --pr N")
    return matches[0]["number"] if matches else None


def dispatch_budget_check(
    repository: str, *, number: int | None, branch: str | None, head: str, task_root: Path
) -> dict[str, Any] | None:
    """Refuse a review dispatch at ``head`` once its PR's review dispatches, recorded or not, reach the budget (#12098).

    The dispatcher's own task records name each run's PR or review branch and its head
    (``review_lineage.dispatched_rounds``). A dispatch that names only one of PR and branch has
    the other read from GitHub first, so runs recorded under either count; with no review run of
    the repository on record, no round has been spent and nothing more is read. A head that
    already has a run opens no round, and while the other dispatched heads stay under the default
    budget the round is admitted. From there the recorder's own decision at the PR's current head
    applies (:func:`budget_check`), so the PR's tier, a clean base merge, a designated grant or the
    lineage's repair round may still admit it. A branch with no open PR gets the default budget.
    """
    from scripts.review.review_lineage import dispatched_rounds, lineage_runs, review_records

    records = review_records(task_root, repository=repository)
    if not records:
        return None
    if number is None and branch is not None:
        number = _open_pr_number(repository, branch)
    elif number is not None and branch is None:
        branch = _pr(repository, "", number)["headRefName"]
    runs = lineage_runs(task_root, repository=repository, number=number, branch=branch, records=records)
    heads = dispatched_rounds(runs=runs, comments=(), login="")
    if head in heads or len(heads) < DEFAULT_REVIEW_ROUNDS:
        return None
    if number is None:
        raise RecordError(
            f"REVIEW_BUDGET_EXHAUSTED: branch {branch} has review dispatches at {len(heads)} heads and no open PR; "
            f"its budget is {DEFAULT_REVIEW_ROUNDS} rounds; budget end is never approval, escalate instead"
        )
    return budget_check(repository, number, task_root=task_root, head=head)


def budget_check_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="record_cf_verdict.py budget-check",
        description="Ask the verdict recorder whether a review round at the PR's current head would be admitted.\n"
        "Run it before dispatching a reviewer; it reads only and writes no receipt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/review/record_cf_verdict.py budget-check "
        "--repository learn-ukrainian/learn-ukrainian.github.io --pr 42\n"
        "Outputs: JSON on stdout: admitted, the budget, unrecorded_rounds (heads reviewed with no recorded verdict)\n"
        "  and any exemption, grant or repair-round receipt.\n"
        "Exit codes: 0: admitted; 1: refused (the reason names what to escalate).\n"
        "Related: agents_extensions/shared/skills/review-loop/references/policy.md",
    )
    parser.add_argument("--repository", required=True, help="GitHub owner/name of the PR")
    parser.add_argument("--pr", type=int, required=True, help="Open PR number")
    args = parser.parse_args(argv)
    try:
        result = budget_check(args.repository, args.pr)
    except (RecordError, SweepError, ValueError) as exc:
        print(json.dumps({"pr": args.pr, "admitted": False, "refusal": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


@publication_boundary(RecordError)
def republish_withheld(
    task_id: str, *, pr_number: int, task_root: Path | None = None, lock_root: Path | None = None
) -> dict[str, Any]:
    """Publish the findings of a verdict that was recorded withheld, from the task's sealed reply.

    Nothing is recorded again: the reviewed head may have moved, no round,
    receipt or commit status is written, and the withheld comment stays as it
    is (a verdict comment is never edited). The new comment is exactly what the
    recorder publishes for this task now, with the branch facts re-derived at
    the reviewed head, which the PR must still contain. It is refused unless
    the reply's digest is sealed, every recorded verdict of this task is that
    comment or its withheld form, the withheld one is the PR's latest verdict,
    and the reply passes the publication scan.
    """
    root = _repo_root() if task_root is None or lock_root is None else None
    task_root = task_root or root / "batch_state" / "tasks"
    lock_root = lock_root or root / "batch_state" / "locks"
    task, reply = _task(task_id, task_root)
    if not isinstance(task.get("result_sha256"), str):
        raise RecordError("republication requires the review task's sealed reply digest")
    review = _task_verdict(task, reply)
    review_mode = task.get("review_mode", "cross_family")
    pr = _pr(review.repository, review.branch, pr_number)
    if pr.get("headRefName") != review.branch:
        raise RecordError("review branch does not match PR head ref")
    review_root = _review_repository_root(review.repository, root or _repo_root())
    facts = pr_review_facts(
        review.repository,
        pr_number,
        head_sha=review.sha,
        task_root=task_root,
        repo_root=review_root,
        subject_seats=_task_flag_values(task, "review_subject_seats"),
        subject_families=_task_flag_values(task, "review_subject_families"),
        unknown_history=(
            admitted_unknown_history(
                repository=review.repository,
                branch=review.branch,
                head_sha=review.sha,
                task_root=task_root,
                repo_root=review_root,
            )
            if review_mode == "red_team"
            else ()
        ),
        current_head=False,
    )
    reply = repository_relative_reply(reply, task=task, primary_root=review_root)
    comment_fields = dict(
        sha=review.sha,
        task_id=task_id,
        started=review.started,
        verdict=review.verdict,
        model=review.model,
        family=review.family,
        reply=reply,
        review_mode=review_mode,
        review_profile="ukrainian" if review.ukrainian else "code",
        sources_mcp_call_count=review.sources_count,
        unknown_history=facts.unknown_history,
        app_bot=bool(facts.app_bot_commits),
        score=review_score(reply),
        author_models=facts.author_models,
    )
    withheld = build_comment(**{**comment_fields, "reply": ""}, withheld_findings=review.finding_count)
    comment = build_comment(**comment_fields)
    check_texts(normalize_repository(review.repository), [comment], environment={})
    adapter = GitHubAdapter(Path.cwd())
    login = adapter.identity()
    result = {"pr": pr_number, "head": review.sha, "task": task_id, "verdict": review.verdict}
    # The PR lock keeps a verdict at another head from landing between the order check and the post.
    with pr_lock(review.repository, pr_number, lock_root):
        try:
            comments = adapter.comments(review.repository, pr_number)
        except SweepError as exc:
            raise RecordError(f"comment lookup failed: {exc}") from exc
        markers = _trusted_markers(comments, login)
        own = [comments[index] for index, marker in markers if (marker["sha"], marker["task"]) == (review.sha, task_id)]
        if not own:
            raise RecordError("no verdict of this task is recorded at its head")
        if any(item.get("created_at") != item.get("updated_at") for item in own):
            raise RecordError("existing verdict marker was edited")
        if any(item["body"] not in (withheld, comment) for item in own):
            raise RecordError("a recorded verdict of this task does not match its record and sealed reply")
        if any(item["body"] == comment for item in own):
            return {**result, "comment": "existing"}
        if comments[markers[-1][0]] is not own[-1]:
            raise RecordError("a later verdict is recorded on this PR; republishing would reorder the verdicts")
        comment_id = _post_verdict(review.repository, pr_number, comment, login)["id"]
    return {**result, "comment": "posted", "comment_id": comment_id}


def republish_withheld_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="record_cf_verdict.py republish-withheld",
        description="Publish the findings of a verdict recorded as withheld, once the cause is fixed.\n"
        "Posts the sealed reply beside the withheld comment; records no new verdict, round or status.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/review/record_cf_verdict.py republish-withheld "
        "--task-id review-unit --pr 42\n"
        "Outputs: JSON on stdout: the PR, head, task, verdict and whether a comment was posted.\n"
        "Exit codes: 0: posted, or the findings were already published; 1: refused.\n"
        "Related: agents_extensions/shared/skills/review-loop/SKILL.md",
    )
    parser.add_argument("--task-id", required=True, help="Review task whose verdict was recorded withheld")
    parser.add_argument("--pr", type=int, required=True, help="Open PR number the verdict is recorded on")
    args = parser.parse_args(argv)
    try:
        result = republish_withheld(args.task_id, pr_number=args.pr)
    except (RecordError, SweepError, ValueError) as exc:
        print(f"CF verdict republication refused: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


@publication_cli(RecordError)
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["budget-check"]:
        return budget_check_main(argv[1:])
    if argv[:1] == ["republish-withheld"]:
        return republish_withheld_main(argv[1:])
    if argv[:1] == ["budget-grant"]:
        # The grant verb builds on this module, so it is imported only when chosen.
        from scripts.review.budget_grant import main as budget_grant_main

        return budget_grant_main(argv[1:])
    if argv[:1] == ["capability-failure"]:
        # The capability failure verb builds on this module, so it is imported only when chosen.
        from scripts.review.capability_failure import main as capability_failure_main

        return capability_failure_main(argv[1:])
    parser = argparse.ArgumentParser(
        description="Publish a completed exact-head verdict; cross-family is the default.\n"
        "Use after the reviewer exits; same-family needs an explicit prompt-bound red-team review.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/review/record_cf_verdict.py --task-id review-unit --pr 1\n"
        "  .venv/bin/python scripts/review/record_cf_verdict.py --task-id review-unit --pr 1 "
        "--review-mode red_team --red-team-prompt brief.md\n"
        "  .venv/bin/python scripts/review/record_cf_verdict.py budget-check --repository owner/name --pr 1\n"
        "    (whether the next review round is admitted, before dispatch; see budget-check --help)\n"
        "  .venv/bin/python scripts/review/record_cf_verdict.py budget-grant digest <ruling.json>\n"
        "    (an elevated-tier grant ruling's digest; see budget-grant --help)\n"
        "  .venv/bin/python scripts/review/record_cf_verdict.py republish-withheld --task-id review-unit --pr 1\n"
        "    (publish the findings of a verdict recorded withheld; see republish-withheld --help)\n"
        "  .venv/bin/python scripts/review/record_cf_verdict.py capability-failure --task-id review-unit --pr 1 "
        "--capability test-execution --authority claude-cto\n"
        "    (classify a finished run that only lacked a capability; see capability-failure --help)\n"
        "Outputs: GitHub review comment and commit status; JSON publication receipt on stdout.\n"
        "Exit codes: 0: recorded; 1: refused or status publication failed.\nRelated: #9297, #9951",
    )
    parser.add_argument("--task-id", required=True, help="Completed branch-pinned review task id")
    parser.add_argument("--pr", type=int, help="Open PR number; otherwise resolve from review branch")
    parser.add_argument(
        "--review-mode",
        choices=("cross_family", "red_team"),
        help="Review mode (default: task review_mode, otherwise cross_family); red_team permits same-family",
    )
    parser.add_argument(
        "--red-team-prompt",
        type=Path,
        help="Prompt file used by the completed red-team task; required for red_team, default: none",
    )
    args = parser.parse_args(argv)
    try:
        result = record(
            args.task_id, pr_number=args.pr, review_mode=args.review_mode, red_team_prompt=args.red_team_prompt
        )
    except (RecordError, SweepError, ValueError) as exc:
        print(f"CF verdict refused: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "posted" else 1


if __name__ == "__main__":
    # Run as a file or with ``-m``, this module is ``__main__`` and defines its own ``RecordError``; the
    # refusals other modules raise subclass the package module's, so ``main`` must come from that one.
    from scripts.review.record_cf_verdict import main as package_main

    raise SystemExit(package_main())
