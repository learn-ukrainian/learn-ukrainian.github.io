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
MAX_DIGEST_BYTES = 8192  # a tracked digest is a compact paraphrase, not a paper
MAX_QUOTE_CHARS = 200  # single quoted span (blockquote line or "…"/«…») ceiling
# Cold-start announce cap: at most this many records may declare any one role.
MAX_COLD_START_PER_ROLE = 5

_CONSUMER_FS_KINDS = frozenset({"path", "prompt", "rubric", "test"})
_PRIVATE_PREFIX = "docs/references/private/"
_FENCE_LINE_RE = re.compile(r"^<!--\s*/?record:[a-z0-9][a-z0-9-]*\s*-->$")
_URL_RE = re.compile(r"https?://")

# Optional injected seams (kept out of normal CI: they must never require network).
MembershipResolver = Callable[[int, int], bool]
RefResolver = Callable[[str], bool]


class ProvenanceError(ValueError):
    """A provenance / digest-projection problem that invalidates a record."""


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
    open_marker = f"<!-- record:{record_id} -->"
    close_marker = f"<!-- /record:{record_id} -->"
    opens = [i for i, line in enumerate(lines) if line.strip() == open_marker]
    closes = [i for i, line in enumerate(lines) if line.strip() == close_marker]
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
        stripped = line.strip()
        if stripped.startswith("<!-- record:") or stripped.startswith("<!-- /record:"):
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
    """Resolve and safety-check a record's digest path (raises ProvenanceError)."""
    digest = record["provenance"]["digest"]
    if PurePosixPath(digest).as_posix().startswith(_PRIVATE_PREFIX):
        raise ProvenanceError(
            f"digest {digest!r} points under {_PRIVATE_PREFIX} (private-local, never tracked)"
        )
    resolved = _safe_repo_path(digest, project_root)
    if not resolved.exists():
        raise ProvenanceError(f"digest {digest!r} does not exist")
    if not resolved.is_file():
        raise ProvenanceError(f"digest {digest!r} is not a file")
    return resolved


def expected_content_hash(record: dict[str, Any], project_root: Path) -> str:
    """Full pipeline: resolve digest -> project -> normalize -> hash."""
    path = _digest_path(record, project_root)
    text = path.read_text("utf-8")
    projection = extract_digest_projection(
        text, record["id"], record["provenance"].get("digest_anchor")
    )
    return compute_content_hash(normalize_digest_projection(projection))


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
    if path.suffix == ".py":
        return (
            re.search(
                rf"^\s*(?:async\s+def|def|class)\s+{re.escape(symbol)}\b",
                text,
                re.MULTILINE,
            )
            is not None
        )
    return symbol in text


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


def _quoted_spans(text: str) -> list[str]:
    spans: list[str] = []
    spans += re.findall(r'"([^"\n]*)"', text)
    spans += re.findall(r"«([^»\n]*)»", text)
    for line in text.splitlines():
        if line.lstrip().startswith(">"):
            spans.append(line.lstrip()[1:].strip())
    return spans


def validate_digest_policy(record: dict[str, Any], project_root: Path) -> list[str]:
    """Enforce the digest copyright policy on the committed digest file."""
    rid = record["id"]
    try:
        path = _digest_path(record, project_root)
    except ProvenanceError:
        return []  # provenance validation already reported this
    raw = path.read_bytes()
    errors: list[str] = []
    if len(raw) > MAX_DIGEST_BYTES:
        errors.append(
            f"{rid}: digest is {len(raw)} bytes (max {MAX_DIGEST_BYTES}) — keep digests compact"
        )
    text = raw.decode("utf-8", errors="replace")
    spans = _quoted_spans(text)
    for span in spans:
        if len(span) > MAX_QUOTE_CHARS:
            errors.append(
                f"{rid}: digest has a quoted span of {len(span)} chars "
                f"(max {MAX_QUOTE_CHARS}) — paraphrase, do not copy"
            )
            break
    if spans and not _URL_RE.search(text):
        errors.append(
            f"{rid}: digest contains a quotation but no source URL — quotations "
            f"require provenance"
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
) -> CheckResult:
    """Run the full P1 validation contract. Hash drift is tracked separately from
    non-hash errors so that ``--reconcile`` can refuse mutation on the latter."""
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
def _content_hash_nodes(raw_text: str) -> dict[str, yaml.ScalarNode]:
    """Map record id -> its ``content_hash`` scalar node (with source marks)."""
    root = yaml.compose(raw_text)
    out: dict[str, yaml.ScalarNode] = {}
    if not isinstance(root, yaml.MappingNode):
        return out
    records_node = None
    for key, value in root.value:
        if isinstance(key, yaml.ScalarNode) and key.value == "records":
            records_node = value
            break
    if not isinstance(records_node, yaml.SequenceNode):
        return out
    for item in records_node.value:
        if not isinstance(item, yaml.MappingNode):
            continue
        rid = None
        hash_node = None
        for key, value in item.value:
            if not isinstance(key, yaml.ScalarNode):
                continue
            if key.value == "id" and isinstance(value, yaml.ScalarNode):
                rid = value.value
            elif key.value == "content_hash" and isinstance(value, yaml.ScalarNode):
                hash_node = value
        if rid is not None and hash_node is not None:
            out[rid] = hash_node
    return out


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
) -> tuple[str, list[str]]:
    """Return (new_text, changed_ids). Replaces only drifted ``content_hash`` scalar
    spans (targeted by ``target_ids`` if given), preserving all other bytes."""
    nodes = _content_hash_nodes(raw_text)
    replacements: list[tuple[int, int, str]] = []
    changed: list[str] = []
    for record in data["records"]:
        rid = record["id"]
        if target_ids is not None and rid not in target_ids:
            continue
        node = nodes.get(rid)
        if node is None:
            continue
        expected = expected_content_hash(record, project_root)
        if record["content_hash"] == expected:
            continue
        start = node.start_mark.index
        end = node.end_mark.index
        replacements.append((start, end, _render_scalar(expected, node.style)))
        changed.append(rid)
    new_text = raw_text
    for start, end, rendered in sorted(replacements, key=lambda r: r[0], reverse=True):
        new_text = new_text[:start] + rendered + new_text[end:]
    return new_text, changed


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
    parser.add_argument(
        "--id",
        action="append",
        default=[],
        dest="ids",
        help="Restrict --reconcile to the named record id(s). Repeatable.",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output.")
    parser.add_argument("--quiet", action="store_true", help="One-line summary only.")
    args = parser.parse_args(argv)

    registry_path = project_root / "docs" / "references" / "research-registry.yaml"
    raw_text, data = load_registry(registry_path)
    result = validate_registry(data, project_root=project_root)

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
        new_text, changed = reconcile_hashes(
            raw_text, data, project_root=project_root, target_ids=target_ids
        )
        if changed:
            _atomic_write(registry_path, new_text)
            print(f"Reconciled content_hash for: {', '.join(changed)}")
        else:
            print("No content_hash drift — nothing to reconcile.")
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
