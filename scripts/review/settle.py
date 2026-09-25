"""Prepare and record the one bounded settle attempt for an unsupported finding.

The language seat judges whether a quoted source attests the disputed construction
in its sense. This module checks only identity, receipt provenance and return shape.
The prompt is rendered by ``scripts.review.prompts.render`` from this task's own
manifest, and the outcome is written through ``findings_db.record_settle_outcome``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.evidence.lock import atomic_write
from scripts.review import findings_db as db
from scripts.review.prompts.eligibility import pin_refusals
from scripts.review.prompts.render import render_prompt
from scripts.review.receipts import ledger

REPO_ROOT = Path(__file__).resolve().parents[2]
TREE = "curriculum/l2-uk-en"
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")

# Distinct authorities, rather than distinct calls, are required for a conflict.
# Ambiguous signal tools have no authority here and cannot establish a conflict.
SOURCES = {
    "verify_words": "vesum",
    "inspect_word": "vesum",
    "inspect_words": "vesum",
    "verify_stress": "stress",
    "query_sum20": "sum20",
    "query_ulif": "ulif",
    "query_pravopys": "pravopys",
    "search_style_guide": "style_guide",
    "search_text": "style_guide",
    "query_r2u": "r2u",
    "search_heritage": "heritage",
    "search_ua_gec_errors": "ua_gec",
    "query_grac": "grac",
    "query_cefr_level": "cefr",
}

# The categories name the steps of the accepted contract's "The settle step".
# A citation to a call from another category cannot stand in for the required search.
SEARCH_TOOLS = {
    "lemma": frozenset({"verify_words", "inspect_word", "inspect_words", "query_sum20", "query_ulif", "query_r2u"}),
    "construction": frozenset({"search_text", "search_style_guide", "search_ua_gec_errors", "query_grac"}),
    "style_prose": frozenset({"search_text"}),
    "ua_gec_context": frozenset({"search_ua_gec_errors"}),
    "grac": frozenset({"query_grac"}),
    "pravopys": frozenset({"query_pravopys"}),
    "counterevidence": frozenset(SOURCES),
}


class SettleError(Exception):
    """A settle task or return failed its structural contract."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _save_exclusive(path: Path, content: bytes) -> None:
    """Publish a complete reply without replacing another settle session's file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _safe_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_file() or not resolved.is_relative_to(root.resolve()):
        raise SettleError("document must be an existing file within the repository")
    return resolved.relative_to(root.resolve()).as_posix()


def _item(conn: Any, item_id: int) -> Any:
    row = conn.execute("SELECT * FROM settle_items WHERE item_id = ?", (item_id,)).fetchone()
    if row is None or row["kind"] != "unsupported_by_source":
        raise SettleError(f"item {item_id} is not an unsupported_by_source settle item")
    if row["outcome"] is not None:
        raise db.SettleAlreadyDecided(f"settle item {item_id} is already decided")
    return row


def _original_finding(conn: Any, item: Any) -> dict[str, Any]:
    try:
        review_id, attempt_id, finding_id = item["finding_ref"].split("/", 2)
    except ValueError as exc:
        raise SettleError("item finding_ref is malformed") from exc
    row = conn.execute(
        "SELECT f.finding_json, a.manifest_sha256, a.kind, a.lesson_n FROM findings f"
        " JOIN attempts a ON a.review_id = f.review_id AND a.attempt_id = f.attempt_id"
        " WHERE f.review_id = ? AND f.attempt_id = ? AND f.finding_id = ?",
        (review_id, attempt_id, finding_id),
    ).fetchone()
    if row is None or row["manifest_sha256"] != item["manifest_sha256"]:
        raise SettleError("settle item does not match a recorded finding and manifest")
    finding = json.loads(row["finding_json"])
    if "unsupported_by_source" not in finding:
        raise SettleError("recorded finding has no unsupported_by_source branch")
    return finding


def _context(document: str, finding: dict[str, Any]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for location in finding.get("locations", []):
        quote = location.get("quote") if isinstance(location, dict) else None
        if not isinstance(quote, str) or not quote:
            continue
        positions = [match.start() for match in re.finditer(re.escape(quote), document)]
        if not positions:
            raise SettleError("a disputed quote is absent from the current document")
        for occurrence, position in enumerate(positions, start=1):
            start, end = max(0, position - 160), min(len(document), position + len(quote) + 160)
            spans.append(
                {
                    "quote": quote,
                    "context": document[start:end],
                    "location": json.dumps(location, ensure_ascii=False),
                    "occurrence": occurrence,
                }
            )
    if not spans:
        raise SettleError("finding has no quoted disputed span")
    return spans


def _prior_searches(
    finding: dict[str, Any], prior_ledger: Path, review_id: str, attempt_id: str, manifest: str
) -> list[dict[str, Any]]:
    indexed = {entry["receipt_id"]: entry for entry in ledger.records(prior_ledger)}
    searches: list[dict[str, Any]] = []
    for search in finding["unsupported_by_source"]["searches"]:
        receipt = search["receipt"]
        entry = indexed.get(receipt)
        if entry is None or (entry.get("review_id"), entry.get("attempt_id"), entry.get("manifest_sha256")) != (
            review_id,
            attempt_id,
            manifest,
        ):
            raise SettleError(f"original search receipt {receipt} is not in the review attempt ledger")
        searches.append(
            {
                "receipt": receipt,
                "tool": entry["tool"],
                "arguments": entry["arguments"],
                "outcome": search["outcome"],
                "result": entry["result"],
            }
        )
    if not searches:
        raise SettleError("original finding has no recorded searches")
    return searches


def prepare(
    item_id: int,
    *,
    db_path: Path,
    document_path: Path,
    prior_ledger: Path,
    review_id: str,
    attempt_id: str,
    manifest_path: Path,
    prompt_path: Path,
    repo_root: Path = REPO_ROOT,
    parameters_path: Path | None = None,
) -> str:
    """Write the settle manifest and exact rendered prompt; return the prompt sha256."""
    if not TOKEN.fullmatch(review_id) or not TOKEN.fullmatch(attempt_id):
        raise SettleError("review_id and attempt_id must be ledger tokens")
    root = repo_root.resolve()
    with closing(db.connect(db_path)) as conn:
        item = _item(conn, item_id)
        finding = _original_finding(conn, item)
        expected = (
            f"{TREE}/lesson-plans/{item['level']}/{item['slug']}.yaml"
            if item["lesson_n"] is None
            else f"site/src/content/docs/{item['level']}/{item['slug']}/{item['lesson_n']}.mdx"
        )
        actual = _safe_path(document_path, root)
        if actual != expected:
            raise SettleError(f"document path is {actual}; expected {expected}")
        document_bytes = document_path.read_bytes()
        spans = _context(document_bytes.decode("utf-8"), finding)
        source_review, source_attempt, _ = item["finding_ref"].split("/", 2)
        searches = _prior_searches(finding, prior_ledger, source_review, source_attempt, item["manifest_sha256"])
        manifest = {
            "kind": "settle",
            "settle_schema": 1,
            "item_id": item_id,
            "level": item["level"],
            "slug": item["slug"],
            "lesson": item["lesson_n"],
            "finding_ref": item["finding_ref"],
            "source_manifest_sha256": item["manifest_sha256"],
            "review_id": review_id,
            "attempt_id": attempt_id,
            "call_budget": db.load_parameters(parameters_path)["settle_call_budget"],
            "finding_text": yaml.safe_dump(finding, allow_unicode=True, sort_keys=False),
            "disputed_spans_text": yaml.safe_dump(spans, allow_unicode=True, sort_keys=False),
            "reviewer_searches_text": yaml.safe_dump(searches, allow_unicode=True, sort_keys=False),
            "inputs": {"document": {"path": actual, "sha256": _sha(document_bytes)}},
        }
    refusals = pin_refusals(manifest, root)
    if refusals:
        raise SettleError("; ".join(str(refusal) for refusal in refusals))
    data = yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False).encode("utf-8")
    atomic_write(manifest_path, data)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".settle-prompt-", dir=prompt_path.parent) as temp_dir:
        temporary_prompt = Path(temp_dir) / prompt_path.name
        _, prompt_sha, _ = render_prompt(manifest_path, repo_root=root, output_path=temporary_prompt)
        for suffix in ("", ".sha256", ".files_read.json"):
            os.replace(Path(f"{temporary_prompt}{suffix}"), Path(f"{prompt_path}{suffix}"))
    return prompt_sha


class _UniqueLoader(yaml.SafeLoader):
    """Do not let a repeated YAML key silently replace an earlier outcome."""


def _unique_mapping(loader: _UniqueLoader, node: yaml.MappingNode) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise SettleError(f"duplicate reply key {key!r}")
        result[key] = loader.construct_object(value_node)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _source(entry: dict[str, Any]) -> str | None:
    authority = SOURCES.get(entry.get("tool"))
    if authority == "style_guide" and entry.get("tool") == "search_text":
        source_file = entry.get("arguments", {}).get("source_file")
        return f"style_guide:{source_file}" if isinstance(source_file, str) and source_file else None
    return authority


def validate_reply(reply_bytes: bytes, manifest_bytes: bytes, ledger_path: Path) -> tuple[str, list[str]]:
    """Validate structure only; never decide whether quoted evidence supports a claim."""
    manifest = yaml.safe_load(manifest_bytes)
    if manifest.get("kind") != "settle" or manifest.get("settle_schema") != 1:
        raise SettleError("not a settle manifest")
    try:
        reply = yaml.load(reply_bytes, Loader=_UniqueLoader)
    except yaml.YAMLError as exc:
        raise SettleError(f"invalid reply YAML: {exc}") from exc
    required = {
        "settle_schema",
        "item_id",
        "review_id",
        "attempt_id",
        "manifest_sha256",
        "outcome",
        "reason",
        "evidence",
        "broadened_searches",
    }
    if not isinstance(reply, dict) or set(reply) != required or reply.get("settle_schema") != 1:
        raise SettleError("reply must carry exactly the settle return fields and one outcome")
    if reply["outcome"] not in db.SEAT_OUTCOMES or not isinstance(reply["outcome"], str):
        raise SettleError("reply must name exactly one of the four settle outcomes")
    if (reply["item_id"], reply["review_id"], reply["attempt_id"], reply["manifest_sha256"]) != (
        manifest["item_id"],
        manifest["review_id"],
        manifest["attempt_id"],
        _sha(manifest_bytes),
    ):
        raise SettleError("reply identity does not match this settle attempt manifest")
    if not isinstance(reply["reason"], str) or not reply["reason"].strip():
        raise SettleError("settle seat must state its judgment")
    records = ledger.records(ledger_path)
    if len(records) > manifest["call_budget"]:
        raise SettleError(f"settle call budget exceeded: {len(records)} > {manifest['call_budget']}")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if (record.get("review_id"), record.get("attempt_id"), record.get("manifest_sha256")) != (
            manifest["review_id"],
            manifest["attempt_id"],
            _sha(manifest_bytes),
        ):
            raise SettleError("ledger contains a call from another settle attempt")
        indexed[record["receipt_id"]] = record

    def citation(value: Any) -> tuple[str, dict[str, Any]]:
        if not isinstance(value, dict) or set(value) != {"receipt", "quote"}:
            raise SettleError("each citation needs a receipt and quoted receipt text")
        receipt, quote = value["receipt"], value["quote"]
        if not isinstance(receipt, str) or receipt not in indexed:
            raise SettleError(f"receipt {receipt!r} is outside this settle attempt ledger")
        record = indexed[receipt]
        if not isinstance(quote, str) or not quote.strip() or quote not in record["result"]:
            raise SettleError("cited quote is not in the stored receipt result")
        return receipt, record

    if not isinstance(reply["evidence"], list) or not isinstance(reply["broadened_searches"], list):
        raise SettleError("evidence and broadened_searches must be lists")
    evidence = [citation(value) for value in reply["evidence"]]
    searches: dict[str, str] = {}
    for value in reply["broadened_searches"]:
        if not isinstance(value, dict) or set(value) != {"category", "receipt", "quote"}:
            raise SettleError("each broadened search needs category, receipt and quote")
        category = value["category"]
        if category not in SEARCH_TOOLS or category in searches:
            raise SettleError("unknown or repeated broadened search category")
        receipt, record = citation({"receipt": value["receipt"], "quote": value["quote"]})
        if receipt in searches.values() or record["tool"] not in SEARCH_TOOLS[category]:
            raise SettleError("broadened search receipt is duplicated or uses the wrong tool")
        if category == "style_prose" and record.get("arguments", {}).get("source_file") != (
            "antonenko-davydovych-yak-my-hovorymo"
        ):
            raise SettleError("style prose search must name the contract's source_file")
        searches[category] = receipt
    outcome = reply["outcome"]
    if outcome in {"supported_defect", "refuted"} and not any(
        record.get("status") == "ok" and record.get("outcome_facts", {}).get("hits", 0) > 0 for _, record in evidence
    ):
        raise SettleError(f"{outcome} needs a cited receipt with hits")
    if outcome == "source_conflict":
        sources = {
            _source(record)
            for _, record in evidence
            if record.get("status") == "ok" and record.get("outcome_facts", {}).get("hits", 0) > 0
        }
        sources.discard(None)
        if len(sources) < 2:
            raise SettleError("source_conflict needs hit receipts from two different sources")
    if outcome == "unresolved" and set(searches) != set(SEARCH_TOOLS):
        raise SettleError("unresolved must cite every required broadened search and counterevidence")
    return outcome, list(dict.fromkeys([*(receipt for receipt, _ in evidence), *searches.values()]))


def record(
    reply_path: Path,
    *,
    manifest_path: Path,
    ledger_path: Path,
    db_path: Path,
    decided_by: str,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Record a validated reply once and preserve its exact bytes beside the module state."""
    if not TOKEN.fullmatch(decided_by):
        raise SettleError("decided_by must be a dispatch seat token")
    manifest_bytes = manifest_path.read_bytes()
    manifest = yaml.safe_load(manifest_bytes)
    with closing(db.connect(db_path)) as conn:
        item = _item(conn, manifest["item_id"])
        if (item["level"], item["slug"], item["lesson_n"], item["finding_ref"], item["manifest_sha256"]) != (
            manifest["level"],
            manifest["slug"],
            manifest["lesson"],
            manifest["finding_ref"],
            manifest["source_manifest_sha256"],
        ):
            raise SettleError("manifest does not match the open settle item")
        refusals = pin_refusals(manifest, repo_root)
        if refusals:
            raise SettleError("; ".join(str(refusal) for refusal in refusals))
        pin = manifest["inputs"]["document"]
        if _sha((repo_root / pin["path"]).read_bytes()) != pin["sha256"]:
            raise SettleError("disputed document changed since settle manifest")
        reply_bytes = reply_path.read_bytes()
        outcome, receipts = validate_reply(reply_bytes, manifest_bytes, ledger_path)
        state = repo_root / TREE / "evidence" / item["level"] / "_state" / item["slug"]
        saved = state / f"settle-{item['item_id']}.reply.yaml"
        try:
            _save_exclusive(saved, reply_bytes)
        except FileExistsError as exc:
            raise SettleError("settle reply already saved; no second attempt") from exc
        try:
            db.record_settle_outcome(conn, item["item_id"], outcome, receipts, decided_by)
        except BaseException:
            saved.unlink()
            raise
        return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare one sourced settle task or record its validated reply.\nUse after record opens an unsupported_by_source item; never retry a decided item.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.review.settle prepare 1 --db batch_state/review-findings/a1.sqlite --document site/src/content/docs/a1/module/2.mdx --prior-ledger batch_state/review-receipts/R/A.jsonl --review-id settle-R --attempt-id A1 --manifest settle.manifest.yaml --prompt settle.prompt.md\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.review.settle record reply.yaml --db batch_state/review-findings/a1.sqlite --manifest settle.manifest.yaml --ledger settle.jsonl --decided-by language-seat\n"
            "Outputs: prepare writes a manifest, prompt and render sidecars; record writes a saved reply and updates settle_items.\n"
            "Exit codes: 0 accepted; 1 malformed task, reply or filesystem error.\n"
            "Related: scripts/review/prompts/settle.md.j2; docs/epics/fresh-build-review-contracts.md The settle step."
        ),
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root (default: this checkout)")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Write one settle manifest and rendered prompt")
    prep.add_argument("item_id", type=int, help="Open settle_items.item_id")
    prep.add_argument("--db", type=Path, required=True, help="Findings SQLite database for the item's level")
    prep.add_argument("--document", type=Path, required=True, help="Current plan YAML or lesson MDX in this module")
    prep.add_argument("--prior-ledger", type=Path, required=True, help="Original review attempt's receipt JSONL")
    prep.add_argument("--review-id", required=True, help="New settle review id (ledger token)")
    prep.add_argument("--attempt-id", required=True, help="New settle attempt id (ledger token)")
    prep.add_argument("--manifest", type=Path, required=True, help="Output settle manifest YAML")
    prep.add_argument("--prompt", type=Path, required=True, help="Output rendered settle prompt Markdown")
    rec = sub.add_parser("record", help="Validate and record the sole settle outcome")
    rec.add_argument("reply", type=Path, help="Seat's YAML reply")
    rec.add_argument("--db", type=Path, required=True, help="Findings SQLite database for the item's level")
    rec.add_argument("--manifest", type=Path, required=True, help="Exact settle manifest YAML")
    rec.add_argument("--ledger", type=Path, required=True, help="This settle attempt's receipt JSONL")
    rec.add_argument("--decided-by", required=True, help="Trusted dispatch seat identifier")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            digest = prepare(
                args.item_id,
                db_path=args.db,
                document_path=args.document,
                prior_ledger=args.prior_ledger,
                review_id=args.review_id,
                attempt_id=args.attempt_id,
                manifest_path=args.manifest,
                prompt_path=args.prompt,
                repo_root=args.repo_root,
            )
            print(f"prompt_sha256: {digest}")
        else:
            outcome = record(
                args.reply,
                manifest_path=args.manifest,
                ledger_path=args.ledger,
                db_path=args.db,
                decided_by=args.decided_by,
                repo_root=args.repo_root,
            )
            print(f"outcome: {outcome}")
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        yaml.YAMLError,
        db.FindingsDbError,
        ledger.LedgerError,
        SettleError,
    ) as exc:
        parser.exit(1, f"settle: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
