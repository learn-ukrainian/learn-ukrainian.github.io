#!/usr/bin/env python3
"""Validate the Project Research Registry (ADR-011, P1: data + validation only).

The registry lives at ``docs/references/research-registry.yaml``: one record per
actionable research finding, each pointing to a tracked compact digest under
``docs/references/research-digests/``. This tool enforces the P1 contract that JSON
Schema cannot express — lifecycle invariants, canonical ``content_hash``
reconciliation, provenance path safety, typed-consumer resolution, stream-ownership,
the digest copyright policy, and cold-start caps — plus the structural schema at
``schemas/research_registry.schema.json``.

This is a *data + validation* slice. It deliberately does NOT touch the cold-start
manifest, the knowledge API, orient/bootstrap, task routing runtime, the learner
content corpus, embeddings, or build knowledge packets. Those are later ADR-011
phases (P2+).

Two modes:
    --check      (default) report-only. NEVER mutates the registry — byte-for-byte
                 read-only. Exits non-zero on any validation error or hash drift.
    --reconcile  recompute and rewrite drifted ``content_hash`` values. This is the
                 only mutation path; it refuses to run if any NON-hash validation
                 error exists. ``--id`` restricts reconciliation to named records.

Reconciliation replaces only the ``content_hash`` scalar spans (located via the YAML
parser's source marks) in reverse offset order and writes atomically, preserving all
unrelated bytes, ordering, and comments.

Usage:
    .venv/bin/python scripts/audit/check_research_registry.py --check
    .venv/bin/python scripts/audit/check_research_registry.py --reconcile
    .venv/bin/python scripts/audit/check_research_registry.py --reconcile --id unlp-2026-cefr-assessment
    .venv/bin/python scripts/audit/check_research_registry.py --json

Exit codes:
    0 = clean
    1 = warnings (advisory)
    2 = errors or hash drift (block CI)

Related:
    - docs/architecture/adr/adr-011-project-research-registry.md
    - schemas/research_registry.schema.json
    - scripts/audit/check_adrs.py (sibling audit conventions)
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "docs" / "references" / "research-registry.yaml"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "research_registry.schema.json"
STREAMS_PATH = PROJECT_ROOT / "scripts" / "config" / "issue_streams.yaml"
DECISIONS_PATH = PROJECT_ROOT / "docs" / "decisions" / "decisions.yaml"

# Digest copyright policy (ADR-011 §"Digest content policy"). These are a
# repository fair-use / worktree-safety contract enforced where deterministic.
# Ceiling applies to the per-record PROJECTION (the exact hashed body), not to a
# whole shared file that may host several records' fenced sections.
MAX_DIGEST_BYTES = 4096  # ADR-011 compact record-body contract
MAX_QUOTE_CHARS = 200  # single quoted span (blockquote line or "…"/«…»/“…”) ceiling
# Cold-start announce cap: at most this many records may declare any one role.
MAX_COLD_START_PER_ROLE = 5

_CONSUMER_FS_KINDS = frozenset({"path", "prompt", "rubric", "test"})
_REFERENCES_PREFIX = "docs/references/"
_PRIVATE_PREFIX = "docs/references/private/"
_FENCE_LINE_RE = re.compile(r"^<!--\s*/?record:[a-z0-9][a-z0-9-]*\s*-->$")
_URL_RE = re.compile(r"https?://")

# Optional injected seams (kept out of normal CI: they must never require network).
MembershipResolver = Callable[[int, int], bool]
RefResolver = Callable[[str], bool]


class ProvenanceError(ValueError):
    """A provenance / digest-projection problem that invalidates a record."""


def _load_atlas_intake_registry():
    """Load ``scripts/audit/atlas_intake_registry.py`` by file path, bypassing
    the ``scripts.audit`` package ``__init__``.

    ``from scripts.audit import atlas_intake_registry`` would run
    ``scripts/audit/__init__.py``, which imports ``scripts/audit/config.py``,
    which does a bare ``from config import ...`` — resolved against
    ``sys.path[0]``. When THIS file is invoked as a bare script
    (``python scripts/audit/check_research_registry.py``, not ``-m``), Python
    sets ``sys.path[0]`` to this file's own directory (``scripts/audit/``) —
    so ``config`` self-shadows against ``scripts/audit/config.py`` instead of
    the intended ``scripts/config.py``, crashing on a circular partial import.
    Loading the sibling module directly by path sidesteps the whole package
    init and is safe under both bare-script and ``-m``/import invocation.
    """
    import importlib.util

    name = "check_research_registry._atlas_intake_registry"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).resolve().parent / "atlas_intake_registry.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Register BEFORE exec: dataclasses' introspection looks the module up in
    # sys.modules by ``cls.__module__`` while the class body is executing.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_registry(path: Path = REGISTRY_PATH) -> tuple[str, dict[str, Any]]:
    """Return (raw_text, parsed_document). Raw text is preserved for reconcile."""
    raw = path.read_text("utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse to a mapping")
    return raw, data


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def load_streams(path: Path = STREAMS_PATH) -> dict[str, list[int]]:
    """Return {stream_key: [epic_numbers]} from the issue-stream registry."""
    doc = yaml.safe_load(path.read_text("utf-8")) or {}
    streams = doc.get("streams") or {}
    return {
        key: [int(n) for n in (spec.get("epics") or [])]
        for key, spec in streams.items()
    }


def load_decision_ids(path: Path = DECISIONS_PATH) -> set[str]:
    """Return the set of decision-journal ids (the repository decision registry)."""
    if not path.exists():
        return set()
    doc = yaml.safe_load(path.read_text("utf-8")) or {}
    return {
        str(dec["id"])
        for dec in (doc.get("decisions") or [])
        if isinstance(dec, dict) and dec.get("id")
    }


# --------------------------------------------------------------------------- #
# Path safety
# --------------------------------------------------------------------------- #
def _safe_repo_path(rel: str, project_root: Path) -> Path:
    """Resolve a repo-relative path, rejecting absolute paths, ``..``, and escapes."""
    posix = PurePosixPath(rel)
    if posix.is_absolute() or rel.startswith("/") or rel.startswith("~"):
        raise ProvenanceError(f"{rel!r} is not a repo-relative path")
    if ".." in posix.parts:
        raise ProvenanceError(f"{rel!r} escapes the repository via '..'")
    resolved = (project_root / rel).resolve()
    root = project_root.resolve()
    if resolved != root and not resolved.is_relative_to(root):
        raise ProvenanceError(f"{rel!r} resolves outside the repository")
    return resolved


def _path_has_symlink(project_root: Path, rel: str) -> bool:
    """True if any path component of ``rel`` (walked from ``project_root``) is a
    symlink. Checked against the UNRESOLVED join so a symlinked component cannot
    hide behind ``Path.resolve()`` before this test runs."""
    current = project_root
    for part in PurePosixPath(rel).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


# --------------------------------------------------------------------------- #
# Digest projection + canonical content hash
# --------------------------------------------------------------------------- #
def extract_digest_projection(text: str, record_id: str, anchor: str | None) -> str:
    """Extract the raw projection to hash.

    No anchor -> the whole dedicated digest. With an anchor -> exactly the content
    between ``<!-- record:<id> -->`` and ``<!-- /record:<id> -->`` (fences excluded),
    where ``<id>`` is the record id and ``anchor`` must equal it.
    """
    if anchor is None:
        return text
    if anchor != record_id:
        raise ProvenanceError(
            f"digest_anchor {anchor!r} must equal record id {record_id!r}"
        )
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = norm.split("\n")
    # Same whitespace tolerance as _FENCE_LINE_RE / normalize_digest_projection:
    # both `<!-- record:id -->` and `<!--record:id-->` (and any spacing in between).
    open_re = re.compile(rf"^<!--\s*record:{re.escape(record_id)}\s*-->$")
    close_re = re.compile(rf"^<!--\s*/record:{re.escape(record_id)}\s*-->$")
    opens = [i for i, line in enumerate(lines) if open_re.match(line.strip())]
    closes = [i for i, line in enumerate(lines) if close_re.match(line.strip())]
    if not opens or not closes:
        raise ProvenanceError(f"digest is missing the fence for record {record_id!r}")
    if len(opens) > 1 or len(closes) > 1:
        raise ProvenanceError(f"digest has a duplicate fence for record {record_id!r}")
    start, end = opens[0], closes[0]
    if end < start:
        raise ProvenanceError(
            f"digest fence for record {record_id!r} is mismatched (close before open)"
        )
    section = lines[start + 1 : end]
    for line in section:
        if _FENCE_LINE_RE.match(line.strip()):
            raise ProvenanceError(
                f"digest has a nested fence inside record {record_id!r}"
            )
    return "\n".join(section)


def normalize_digest_projection(projection: str) -> str:
    """Canonical normalization (ADR-011): CRLF/CR->LF, drop fence lines, strip
    trailing whitespace per line, drop the trailing blank-line run, join with \\n."""
    text = projection.replace("\r\n", "\n").replace("\r", "\n")
    kept: list[str] = []
    for line in text.split("\n"):
        if _FENCE_LINE_RE.match(line.strip()):
            continue
        kept.append(line.rstrip())
    while kept and kept[-1] == "":
        kept.pop()
    return "\n".join(kept)


def compute_content_hash(normalized: str) -> str:
    """SHA-256 over the UTF-8-encoded normalized projection, ``sha256:``-prefixed."""
    return "sha256:" + sha256(normalized.encode("utf-8")).hexdigest()


def _digest_path(record: dict[str, Any], project_root: Path) -> Path:
    """Resolve and safety-check a record's digest path (raises ProvenanceError).

    Allows both a dedicated per-record digest and an ADR-011-permitted shared
    reference document (e.g. ``docs/references/unlp-reading-notes.md``) -- anything
    tracked under ``docs/references/`` except ``docs/references/private/``. Rejects
    symlinks outright (the simplest deterministic policy against a tracked-looking
    path windowing into private/local data) and requires the resolved target to
    stay under ``docs/references/`` too, not just the lexical spelling.
    """
    digest = record["provenance"]["digest"]
    digest_posix = PurePosixPath(digest).as_posix()
    if not digest_posix.startswith(_REFERENCES_PREFIX):
        raise ProvenanceError(
            f"digest {digest!r} must be a tracked path under {_REFERENCES_PREFIX} "
            f"(dedicated digest or ADR-011-permitted shared reference)"
        )
    if digest_posix.startswith(_PRIVATE_PREFIX):
        raise ProvenanceError(
            f"digest {digest!r} points under {_PRIVATE_PREFIX} (private-local, never tracked)"
        )
    if _path_has_symlink(project_root, digest):
        raise ProvenanceError(f"digest {digest!r} passes through a symlink — not allowed")
    resolved = _safe_repo_path(digest, project_root)
    references_root = (project_root / "docs" / "references").resolve()
    if resolved != references_root and not resolved.is_relative_to(references_root):
        raise ProvenanceError(f"digest {digest!r} resolves outside {_REFERENCES_PREFIX}")
    private_root = references_root / "private"
    if resolved == private_root or resolved.is_relative_to(private_root):
        raise ProvenanceError(f"digest {digest!r} resolves under {_PRIVATE_PREFIX}")
    if not resolved.exists():
        raise ProvenanceError(f"digest {digest!r} does not exist")
    if not resolved.is_file():
        raise ProvenanceError(f"digest {digest!r} is not a file")
    return resolved


def _read_digest_text(path: Path) -> str:
    """Read a digest file as UTF-8, turning decode/IO failures into a record-scoped
    ``ProvenanceError`` instead of an uncaught traceback."""
    try:
        return path.read_text("utf-8")
    except UnicodeDecodeError as exc:
        raise ProvenanceError(f"{path} is not valid UTF-8: {exc}") from exc
    except OSError as exc:
        raise ProvenanceError(f"{path} could not be read: {exc}") from exc


def _record_projection(record: dict[str, Any], project_root: Path) -> str:
    """Resolve, read, and extract this record's raw digest projection (the exact
    per-record body used for both hashing and the copyright/size policy)."""
    path = _digest_path(record, project_root)
    text = _read_digest_text(path)
    return extract_digest_projection(
        text, record["id"], record["provenance"].get("digest_anchor")
    )


def expected_content_hash(record: dict[str, Any], project_root: Path) -> str:
    """Full pipeline: resolve digest -> project -> normalize -> hash."""
    return compute_content_hash(
        normalize_digest_projection(_record_projection(record, project_root))
    )


# --------------------------------------------------------------------------- #
# Semantic validators (each returns a list of record-scoped error strings)
# --------------------------------------------------------------------------- #
def validate_provenance(record: dict[str, Any], project_root: Path) -> list[str]:
    rid = record["id"]
    try:
        _digest_path(record, project_root)
        # Force projection extraction so fence problems surface here too.
        expected_content_hash(record, project_root)
    except ProvenanceError as exc:
        return [f"{rid}: provenance invalid — {exc}"]
    return []


def validate_lifecycle(record: dict[str, Any], all_ids: set[str]) -> list[str]:
    rid = record["id"]
    state = record["state"]
    if state == "proposed":
        if not record.get("ownership"):
            return [
                f"{rid}: 'proposed' record must reference exactly one stream-owned "
                f"issue (ownership.issue + ownership.stream)"
            ]
    elif state == "adopted":
        if not record.get("consumer"):
            return [f"{rid}: 'adopted' record must carry a typed consumer {{kind, ref}}"]
    elif state == "deferred":
        if not record.get("reason"):
            return [f"{rid}: 'deferred' record must carry a non-empty reason"]
    elif state == "superseded":
        repl = record.get("replacement")
        if not repl:
            return [f"{rid}: 'superseded' record must carry a replacement record id"]
        if repl == rid:
            return [f"{rid}: 'superseded' record cannot replace itself"]
        if repl not in all_ids:
            return [f"{rid}: replacement {repl!r} does not exist"]
    return []


def validate_supersession_cycles(records: list[dict[str, Any]]) -> list[str]:
    """Detect supersession cycles (A->B->A) among superseded records."""
    by_id = {r["id"]: r for r in records}
    successor: dict[str, str] = {}
    for rec in records:
        if rec["state"] == "superseded":
            repl = rec.get("replacement")
            if repl and repl != rec["id"] and repl in by_id:
                successor[rec["id"]] = repl
    errors: list[str] = []
    reported: set[frozenset[str]] = set()
    for start in successor:
        seen = [start]
        cur = start
        while cur in successor:
            cur = successor[cur]
            if cur in seen:
                cycle = frozenset(seen[seen.index(cur):])
                if cycle not in reported:
                    reported.add(cycle)
                    chain = " -> ".join([*seen[seen.index(cur):], cur])
                    errors.append(f"supersession cycle: {chain}")
                break
            seen.append(cur)
    return errors


def _resolve_symbol(path: Path, symbol: str) -> bool:
    text = path.read_text("utf-8", errors="replace")
    if path.suffix != ".py":
        return symbol in text
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return symbol in text  # unparsable file: fall back to a substring match
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == symbol
        ):
            return True
    # Module-level constants: `SYMBOL = ...` / `SYMBOL: Type = ...` at top level only.
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == symbol for t in node.targets
        ):
            return True
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == symbol
        ):
            return True
    return False


def validate_consumer(
    record: dict[str, Any],
    *,
    project_root: Path,
    decision_ids: set[str],
    issue_resolver: RefResolver | None = None,
    corpus_resolver: RefResolver | None = None,
) -> list[str]:
    """Resolve a typed consumer, failing closed. Only called when a consumer is set."""
    rid = record["id"]
    consumer = record["consumer"]
    kind = consumer["kind"]
    ref = consumer["ref"]

    if kind in _CONSUMER_FS_KINDS:
        file_part, _, symbol = ref.partition("::")
        try:
            resolved = _safe_repo_path(file_part, project_root)
        except ProvenanceError as exc:
            return [f"{rid}: consumer ref {ref!r} — {exc}"]
        if not resolved.is_file():
            return [f"{rid}: consumer ref {ref!r} does not resolve to a file"]
        if symbol and not _resolve_symbol(resolved, symbol):
            return [f"{rid}: consumer symbol '::{symbol}' not found in {file_part}"]
        return []
    if kind == "decision":
        if ref not in decision_ids:
            return [f"{rid}: consumer decision {ref!r} is not in the decision registry"]
        return []
    if kind == "issue":
        if issue_resolver is None:
            return [
                f"{rid}: consumer kind 'issue' needs an injected resolver — offline "
                f"P1 cannot verify issue {ref!r}"
            ]
        if not (ref.isdigit() and int(ref) >= 1):
            return [f"{rid}: consumer issue ref {ref!r} is not a positive integer"]
        if not issue_resolver(ref):
            return [f"{rid}: consumer issue {ref!r} did not resolve"]
        return []
    if kind == "corpus":
        if corpus_resolver is None:
            return [
                f"{rid}: consumer kind 'corpus' needs an injected resolver — offline "
                f"P1 cannot verify corpus intake {ref!r}"
            ]
        if not corpus_resolver(ref):
            return [f"{rid}: consumer corpus intake {ref!r} did not resolve"]
        return []
    return [f"{rid}: unknown consumer kind {kind!r}"]  # unreachable if schema-valid


def validate_ownership(
    record: dict[str, Any],
    streams: dict[str, list[int]],
    membership_resolver: MembershipResolver | None = None,
) -> list[str]:
    """Validate ownership.stream is declared exactly once as an epic. Only called
    when ownership is set. Live issue membership is checked only if a resolver is
    injected — offline P1 does not claim native-subissue membership."""
    rid = record["id"]
    own = record["ownership"]
    stream = own["stream"]
    declarations = [key for key, epics in streams.items() if stream in epics]
    if not declarations:
        return [
            f"{rid}: ownership.stream {stream} is not a declared stream epic in "
            f"issue_streams.yaml"
        ]
    if len(declarations) > 1:
        return [
            f"{rid}: ownership.stream {stream} is declared as an epic in multiple "
            f"streams ({', '.join(sorted(declarations))}) — duplicate epic declaration"
        ]
    if membership_resolver is not None and not membership_resolver(own["issue"], stream):
        return [
            f"{rid}: ownership.issue {own['issue']} is not a live child of stream "
            f"epic {stream}"
        ]
    return []


# Straight double quotes, Ukrainian guillemets, and curly English quotes -- all
# allowed to span multiple lines, since a quote broken across lines is still one
# quoted span for copyright purposes.
_QUOTE_SPAN_PATTERNS = (
    re.compile(r'"([^"]*)"'),
    re.compile(r"«([^»]*)»"),
    re.compile(r"“([^”]*)”"),  # “ … ”
)


def _quoted_spans(projection: str) -> list[str]:
    """Extract quoted spans from a digest projection, combining contiguous Markdown
    blockquote lines into one span (a blank or non-blockquote line ends a span) so
    that a quote split across several short ``>`` lines cannot dodge the char cap."""
    spans: list[str] = []
    for pattern in _QUOTE_SPAN_PATTERNS:
        spans.extend(pattern.findall(projection))
    blockquote: list[str] = []
    for line in projection.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(">"):
            blockquote.append(stripped[1:].strip())
            continue
        if blockquote:
            spans.append(" ".join(blockquote))
            blockquote = []
    if blockquote:
        spans.append(" ".join(blockquote))
    return spans


def validate_digest_policy(record: dict[str, Any], project_root: Path) -> list[str]:
    """Enforce the digest copyright policy on this record's PROJECTION only (the
    same fenced section used for hashing) -- never on a whole shared digest file,
    so an anchored record can't be penalized for, or borrow attribution from,
    another section."""
    rid = record["id"]
    try:
        projection = _record_projection(record, project_root)
    except ProvenanceError:
        return []  # provenance validation already reported this
    errors: list[str] = []
    projection_bytes = projection.encode("utf-8")
    if len(projection_bytes) > MAX_DIGEST_BYTES:
        errors.append(
            f"{rid}: digest record body is {len(projection_bytes)} bytes "
            f"(max {MAX_DIGEST_BYTES}) — keep the per-record digest compact"
        )
    spans = _quoted_spans(projection)
    for span in spans:
        if len(span) > MAX_QUOTE_CHARS:
            errors.append(
                f"{rid}: digest has a quoted span of {len(span)} chars "
                f"(max {MAX_QUOTE_CHARS}) — paraphrase, do not copy"
            )
            break
    if spans and not (record["provenance"].get("source_url") or _URL_RE.search(projection)):
        errors.append(
            f"{rid}: digest contains a quotation but no source URL in this record's "
            f"provenance.source_url or its own projection — quotations require "
            f"in-record provenance, not another section's URL"
        )
    return errors


def validate_cold_start(records: list[dict[str, Any]]) -> list[str]:
    """No more than MAX_COLD_START_PER_ROLE records may declare any one role."""
    counts: Counter[str] = Counter()
    for rec in records:
        for role in rec.get("cold_start_roles") or []:
            counts[role] += 1
    return [
        f"cold_start_roles: role {role!r} declared by {count} records "
        f"(max {MAX_COLD_START_PER_ROLE})"
        for role, count in sorted(counts.items())
        if count > MAX_COLD_START_PER_ROLE
    ]


# --------------------------------------------------------------------------- #
# Aggregated result
# --------------------------------------------------------------------------- #
@dataclass
class CheckResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    drift: list[str] = field(default_factory=list)  # record ids whose hash drifted

    @property
    def exit_code(self) -> int:
        if self.errors or self.drift:
            return 2
        if self.warnings:
            return 1
        return 0


def validate_schema(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    return [
        f"schema: {'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]


def validate_registry(
    data: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    schema: dict[str, Any] | None = None,
    streams: dict[str, list[int]] | None = None,
    decision_ids: set[str] | None = None,
    membership_resolver: MembershipResolver | None = None,
    issue_resolver: RefResolver | None = None,
    corpus_resolver: RefResolver | None = None,
    raw_text: str | None = None,
) -> CheckResult:
    """Run the full P1 validation contract. Hash drift is tracked separately from
    non-hash errors so that ``--reconcile`` can refuse mutation on the latter.

    ``raw_text`` (the registry's source bytes, decoded) is optional but should
    always be supplied by the CLI: it lets us reject a ``content_hash`` written as
    a YAML alias, which is invisible once ``data`` has gone through
    ``yaml.safe_load``.
    """
    result = CheckResult()
    schema = schema if schema is not None else load_schema()

    schema_errors = validate_schema(data, schema)
    if schema_errors:
        # Semantic checks assume structural validity; stop here.
        result.errors.extend(schema_errors)
        return result

    streams = streams if streams is not None else load_streams()
    decision_ids = decision_ids if decision_ids is not None else load_decision_ids()
    records = data["records"]

    if raw_text is not None:
        result.errors.extend(validate_content_hash_scalars(raw_text, records))

    ids = [rec["id"] for rec in records]
    seen: set[str] = set()
    for rid in ids:
        if rid in seen:
            result.errors.append(f"duplicate record id: {rid!r}")
        seen.add(rid)
    all_ids = set(ids)

    for record in records:
        prov_errors = validate_provenance(record, project_root)
        result.errors.extend(prov_errors)
        result.errors.extend(validate_lifecycle(record, all_ids))
        result.errors.extend(validate_digest_policy(record, project_root))
        if record.get("consumer"):
            result.errors.extend(
                validate_consumer(
                    record,
                    project_root=project_root,
                    decision_ids=decision_ids,
                    issue_resolver=issue_resolver,
                    corpus_resolver=corpus_resolver,
                )
            )
        if record.get("ownership"):
            result.errors.extend(
                validate_ownership(record, streams, membership_resolver)
            )
        # Hash drift only when provenance/projection is sound.
        if not prov_errors and record["content_hash"] != expected_content_hash(
            record, project_root
        ):
            result.drift.append(record["id"])

    result.errors.extend(validate_supersession_cycles(records))
    result.errors.extend(validate_cold_start(records))
    return result


# --------------------------------------------------------------------------- #
# Reconciliation (the only mutation path)
# --------------------------------------------------------------------------- #
def _skip_event(events: list[yaml.Event], i: int) -> int:
    """Advance past one complete node value starting at ``events[i]``."""
    ev = events[i]
    if isinstance(ev, (yaml.ScalarEvent, yaml.AliasEvent)):
        return i + 1
    if isinstance(ev, yaml.SequenceStartEvent):
        i += 1
        while not isinstance(events[i], yaml.SequenceEndEvent):
            i = _skip_event(events, i)
        return i + 1
    if isinstance(ev, yaml.MappingStartEvent):
        i += 1
        while not isinstance(events[i], yaml.MappingEndEvent):
            i = _skip_event(events, i)  # key
            i = _skip_event(events, i)  # value
        return i + 1
    raise ValueError(f"unexpected YAML event while scanning for content_hash: {ev!r}")


def _content_hash_events(raw_text: str) -> dict[str, yaml.Event]:
    """Map record id -> the raw parser event for its ``content_hash`` value.

    Walks ``yaml.parse()`` events directly instead of ``yaml.compose()``/
    ``yaml.safe_load()``. Composing (and safe_load) resolve a YAML alias (``*h``)
    to the SAME node object as its anchor definition -- so a ``content_hash: *h``
    aliasing e.g. an anchor on ``summary`` would silently read back as if it were a
    plain scalar written at the *anchor's* source position. Reconciling from that
    resolved node then splices the new hash into the anchor's span (corrupting the
    field it was borrowed from) and leaves the alias undefined, while reporting
    success. Scanning events instead lets us see that this record's value was an
    ``AliasEvent``, not a ``ScalarEvent``, at the exact position it was written.
    """
    events = list(yaml.parse(raw_text, Loader=yaml.SafeLoader))
    idx = 0
    while not isinstance(events[idx], yaml.MappingStartEvent):
        idx += 1
    idx += 1  # enter the root mapping
    record_starts: list[int] = []
    while not isinstance(events[idx], yaml.MappingEndEvent):
        key_ev = events[idx]
        idx += 1
        if (
            isinstance(key_ev, yaml.ScalarEvent)
            and key_ev.value == "records"
            and isinstance(events[idx], yaml.SequenceStartEvent)
        ):
            idx += 1
            while not isinstance(events[idx], yaml.SequenceEndEvent):
                if isinstance(events[idx], yaml.MappingStartEvent):
                    record_starts.append(idx)
                idx = _skip_event(events, idx)
            idx += 1  # consume SequenceEndEvent
        else:
            idx = _skip_event(events, idx)

    out: dict[str, yaml.Event] = {}
    for start in record_starts:
        i = start + 1
        rid: str | None = None
        hash_event: yaml.Event | None = None
        while not isinstance(events[i], yaml.MappingEndEvent):
            key_ev = events[i]
            i += 1
            if (
                isinstance(key_ev, yaml.ScalarEvent)
                and key_ev.value == "id"
                and isinstance(events[i], yaml.ScalarEvent)
            ):
                rid = events[i].value
                i = _skip_event(events, i)
            elif isinstance(key_ev, yaml.ScalarEvent) and key_ev.value == "content_hash":
                hash_event = events[i]
                i = _skip_event(events, i)
            else:
                i = _skip_event(events, i)
        if rid is not None and hash_event is not None:
            out[rid] = hash_event
    return out


def validate_content_hash_scalars(
    raw_text: str, records: list[dict[str, Any]]
) -> list[str]:
    """Reject a ``content_hash`` written as a YAML alias (e.g. ``*h``) rather than a
    literal scalar. This is a non-hash validation error: it must block both
    ``--check`` and ``--reconcile`` (never silently resolved, never mutated)."""
    events_by_id = _content_hash_events(raw_text)
    errors: list[str] = []
    for record in records:
        rid = record["id"]
        event = events_by_id.get(rid)
        if event is not None and not isinstance(event, yaml.ScalarEvent):
            errors.append(
                f"{rid}: content_hash is a YAML alias (e.g. *anchor), not a literal "
                f"plain/quoted scalar — write an explicit sha256:... value"
            )
    return errors


def _render_scalar(new_value: str, style: str | None) -> str:
    if style == '"':
        return '"' + new_value + '"'
    if style == "'":
        return "'" + new_value.replace("'", "''") + "'"
    return new_value


def reconcile_hashes(
    raw_text: str,
    data: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    target_ids: set[str] | None = None,
) -> tuple[str, list[str], list[str]]:
    """Return (new_text, changed_ids, unresolved_ids). Replaces only drifted
    ``content_hash`` scalar spans (targeted by ``target_ids`` if given), preserving
    all other bytes. ``unresolved_ids`` lists in-scope, drifted records whose
    ``content_hash`` could not be located as a literal scalar to rewrite (e.g. a
    YAML alias) -- the caller must treat this as failure, never as success."""
    events_by_id = _content_hash_events(raw_text)
    replacements: list[tuple[int, int, str]] = []
    changed: list[str] = []
    unresolved: list[str] = []
    for record in data["records"]:
        rid = record["id"]
        if target_ids is not None and rid not in target_ids:
            continue
        expected = expected_content_hash(record, project_root)
        if record["content_hash"] == expected:
            continue  # not drifted -- nothing to reconcile for this record
        event = events_by_id.get(rid)
        if event is None or not isinstance(event, yaml.ScalarEvent):
            unresolved.append(rid)
            continue
        start = event.start_mark.index
        end = event.end_mark.index
        replacements.append((start, end, _render_scalar(expected, event.style)))
        changed.append(rid)
    new_text = raw_text
    for start, end, rendered in sorted(replacements, key=lambda r: r[0], reverse=True):
        new_text = new_text[:start] + rendered + new_text[end:]
    return new_text, changed, unresolved


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, "utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _reconcile_command(record_id: str) -> str:
    return (
        f".venv/bin/python scripts/audit/check_research_registry.py "
        f"--reconcile --id {record_id}"
    )


def _run_strict_adoption(
    data: dict[str, Any],
    *,
    project_root: Path,
    max_age_s: int,
    as_json: bool,
    raw_text: str | None = None,
) -> int:
    """Strict adoption gate (ADR-011 P4).

    Re-runs the full P1 contract, but with membership + issue resolvers injected
    from a FRESH issue-stream audit cache so ``proposed`` records are gated on
    exact one-effective-epic ownership and ``adopted``/issue consumers must
    resolve to an open, uniquely-owned issue. The cache is produced by a
    separate live auditor run — this path never touches the network. A
    missing/stale/malformed/future-skewed cache **fails the gate closed** (exit
    2) rather than silently passing unverifiable ownership. The ``corpus``
    resolver is real and deterministic (the declared Atlas intake source-family
    registry) and needs no cache — it is always injected, cache or no cache.
    """
    # Local import keeps offline --check free of the orchestration package. When
    # the validator is run as a bare script (``python scripts/audit/...``) rather
    # than imported, the repo root is not on sys.path yet — append it (never
    # prepend: that could shadow the real ``scripts`` package with a same-named
    # directory under a test project root).
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))
    from scripts.orchestration import issue_stream_audit as isa

    atlas_intake_registry = _load_atlas_intake_registry()

    report = isa.read_membership_index(max_age_s)
    if report is None:
        message = (
            "strict adoption gate: no fresh issue-stream membership cache "
            f"(<= {max_age_s}s old). Refresh it first: "
            ".venv/bin/python -m scripts.orchestration.issue_stream_audit --json"
        )
        if as_json:
            print(json.dumps({"ok": False, "errors": [message], "cache": "missing"}, indent=2))
        else:
            print(f"STRICT ADOPTION GATE FAILED (fail-closed):\n  - {message}", file=sys.stderr)
        return 2

    result = validate_registry(
        data,
        project_root=project_root,
        raw_text=raw_text,
        membership_resolver=isa.make_membership_resolver(report),
        issue_resolver=isa.make_issue_resolver(report),
        # Real deterministic corpus resolver (ADR-011 P4, codex/gemini review):
        # the declared intake registry is a static, offline, always-available
        # source of truth — unlike issue/membership resolution it needs no live
        # cache, so it is injected unconditionally, not gated on cache freshness.
        corpus_resolver=atlas_intake_registry.is_registered_source_family,
    )
    if as_json:
        print(
            json.dumps(
                {
                    "ok": result.exit_code == 0,
                    "errors": result.errors,
                    "drift": result.drift,
                    "cache": "fresh",
                },
                indent=2,
            )
        )
        return result.exit_code
    if result.errors:
        print("STRICT ADOPTION GATE FAILED:", file=sys.stderr)
        for err in result.errors:
            print(f"  - {err}", file=sys.stderr)
    if result.drift:
        print("Research registry hash DRIFT (blocks adoption):", file=sys.stderr)
        for rid in result.drift:
            print(f"  - {rid}: {_reconcile_command(rid)}", file=sys.stderr)
    if result.exit_code == 0:
        print("Strict adoption gate: ownership + consumers verified against fresh cache.")
    return result.exit_code


def main(argv: list[str] | None = None, *, project_root: Path = PROJECT_ROOT) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the ADR-011 Project Research Registry.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Report-only (default). Never mutates. Non-zero on error or drift.",
    )
    mode.add_argument(
        "--reconcile",
        action="store_true",
        help="Recompute and rewrite drifted content_hash values (the only mutation path).",
    )
    mode.add_argument(
        "--strict-adoption",
        action="store_true",
        help=(
            "Strict adoption gate (ADR-011 P4). Re-validates ownership and issue "
            "consumers against a FRESH, offline issue-stream audit cache — never "
            "the network. Fails closed if the cache is missing/stale. Distinct from "
            "the default offline --check, which never verifies live membership."
        ),
    )
    parser.add_argument(
        "--id",
        action="append",
        default=[],
        dest="ids",
        help="Restrict --reconcile to the named record id(s). Repeatable.",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=3600,
        help="Strict-adoption: max age (seconds) of the issue-stream cache (default 3600).",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output.")
    parser.add_argument("--quiet", action="store_true", help="One-line summary only.")
    args = parser.parse_args(argv)

    registry_path = project_root / "docs" / "references" / "research-registry.yaml"
    raw_text, data = load_registry(registry_path)

    if args.strict_adoption:
        return _run_strict_adoption(
            data,
            project_root=project_root,
            max_age_s=args.max_age,
            as_json=args.json,
            raw_text=raw_text,
        )

    result = validate_registry(data, project_root=project_root, raw_text=raw_text)

    if args.reconcile:
        if result.errors:
            print(
                "Refusing to reconcile: fix these non-hash validation errors first:",
                file=sys.stderr,
            )
            for err in result.errors:
                print(f"  - {err}", file=sys.stderr)
            return 2
        target_ids = set(args.ids) or None
        if target_ids:
            known = {rec["id"] for rec in data["records"]}
            unknown = target_ids - known
            if unknown:
                print(f"Unknown record id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
                return 2
        new_text, changed, unresolved = reconcile_hashes(
            raw_text, data, project_root=project_root, target_ids=target_ids
        )
        if unresolved:
            print(
                "Refusing to reconcile: content_hash for these drifted record(s) is "
                "not a literal scalar (e.g. a YAML alias) and cannot be safely "
                f"rewritten: {', '.join(sorted(unresolved))}",
                file=sys.stderr,
            )
            return 2
        if not changed:
            print("No content_hash drift — nothing to reconcile.")
            return 0
        # Never write an unvalidated candidate: parse + fully re-validate the new
        # text with the same project root before touching the file, and confirm
        # every record we meant to fix no longer drifts in the candidate.
        candidate_data = yaml.safe_load(new_text)
        candidate_result = validate_registry(
            candidate_data, project_root=project_root, raw_text=new_text
        )
        if candidate_result.errors:
            print(
                "Refusing to write: the reconciled registry fails validation:",
                file=sys.stderr,
            )
            for err in candidate_result.errors:
                print(f"  - {err}", file=sys.stderr)
            return 2
        still_drifted = sorted(set(changed) & set(candidate_result.drift))
        if still_drifted:
            print(
                "Refusing to write: these record(s) would still drift after "
                f"reconciliation: {', '.join(still_drifted)}",
                file=sys.stderr,
            )
            return 2
        _atomic_write(registry_path, new_text)
        print(f"Reconciled content_hash for: {', '.join(changed)}")
        return 0

    # --check (default): report-only, byte-for-byte read-only.
    if args.json:
        payload = {
            "errors": result.errors,
            "warnings": result.warnings,
            "drift": result.drift,
            "reconcile_commands": [_reconcile_command(rid) for rid in result.drift],
            "ok": result.exit_code == 0,
        }
        print(json.dumps(payload, indent=2))
        return result.exit_code

    if args.quiet:
        parts = []
        if result.errors:
            parts.append(f"{len(result.errors)} error(s)")
        if result.drift:
            parts.append(f"{len(result.drift)} hash drift")
        print("research-registry: " + ("; ".join(parts) if parts else "clean"))
        return result.exit_code

    if result.errors:
        print("Research registry ERRORS:", file=sys.stderr)
        for err in result.errors:
            print(f"  - {err}", file=sys.stderr)
    if result.drift:
        print("Research registry hash DRIFT:", file=sys.stderr)
        for rid in result.drift:
            print(f"  - {rid}: digest changed. Reconcile: {_reconcile_command(rid)}", file=sys.stderr)
    if not result.errors and not result.drift:
        print(f"Research registry: {len(data['records'])} records — all clean.", file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
