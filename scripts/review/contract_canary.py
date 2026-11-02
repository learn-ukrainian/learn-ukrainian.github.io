"""Live canary evidence a change to the review output contract needs before it merges (#12399).

On 2026-11-01 PR #12372 changed the code-review output contract, passed review and CI,
and then no Codex, Claude or Grok review could settle (#12380, #12394, #12390). Its
tests used fixtures and its own review ran on the old dispatcher. A change to the paths
below therefore enters the merge queue only when, on its exact head, one live read-only
review per required reviewer route has settled ``done`` with a canonical receipt while
the candidate's own dispatcher supervised it.

The evidence is canary evidence, never a review of record. A canary task is pinned to a
head with no review branch and no PR, so ``record_cf_verdict`` refuses it ("review was
not branch-pinned"), and its receipt lives here, outside the PR comments the verdict
lookup reads. Runbook: ``docs/runbooks/review-contract-canary.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# The one declaration of the review output contract: bound schemas, the receipt gate, the
# verdict parser, the recorder, settlement, and each reviewer provider's schema or reply handling.
CONTRACT_PATHS: tuple[str, ...] = (
    "scripts/review/contract_canary.py",  # this gate: a change to it is proven on live routes too
    "schemas/code-review-findings.v1.schema.json",
    "scripts/review/review_contract.py",
    "scripts/review/verdict_parser.py",
    "scripts/review/record_cf_verdict.py",
    "scripts/review/settle.py",
    "scripts/dispatcher/worker.py",
    "scripts/dispatcher/output_schema.py",
    "scripts/dispatcher/providers/agy.py",
    "scripts/dispatcher/providers/claude.py",
    "scripts/dispatcher/providers/codex.py",
    "scripts/dispatcher/providers/cursor.py",
    "scripts/dispatcher/providers/muse.py",
    "scripts/dispatcher/providers/stream_json.py",
)

REASON = "needs-contract-canary"
SCHEMA = "review-contract-canary.v1"
RECEIPT_DIR = "review-contract-canary"
SHA = re.compile(r"[0-9a-f]{40}\Z")
ROUTE = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")


class CanaryError(ValueError):
    """A canary task or receipt that cannot be canary evidence."""


def touches_contract(paths: Iterable[str]) -> bool:
    """Whether a change to ``paths`` changes the review output contract."""
    return any(path in CONTRACT_PATHS for path in paths)


def _formal_candidates() -> dict[str, list[Any]]:
    """Formal-review candidates by route, from the authoritative catalog."""
    from scripts.review.model_catalog import load_model_catalog
    from scripts.review.reviewer_resolver import REVIEW_CANDIDATES

    models = load_model_catalog()["models"]
    routes: dict[str, list[Any]] = {}
    for candidate in REVIEW_CANDIDATES.values():
        if candidate.formal_review_eligible and models[candidate.concrete_model].get("lifecycle") == "active":
            routes.setdefault(candidate.route, []).append(candidate)
    return routes


def required_routes() -> tuple[str, ...]:
    """Every active formal reviewer route in the catalog. An empty or unreadable catalog raises."""
    try:
        routes = tuple(sorted(_formal_candidates()))
    except Exception as exc:
        raise CanaryError("reviewer routes unavailable") from exc
    if not routes or not all(ROUTE.fullmatch(route) for route in routes):
        raise CanaryError("reviewer routes unavailable")
    return routes


def _route_models(candidates: Sequence[Any]) -> set[str]:
    """The ``--model`` spellings a dispatch to these candidates records."""
    from scripts.dispatcher.providers.agy import transport_model
    from scripts.review.reviewer_resolver import candidate_dispatch_model

    names: set[str] = set()
    for candidate in candidates:
        names.update({candidate.concrete_model, candidate_dispatch_model(candidate)})
        if candidate.route == "agy":
            names.add(transport_model(candidate.concrete_model))
    return names


def _root() -> Path:
    from scripts.common.repo_root import main_checkout_root

    return main_checkout_root(Path(__file__).resolve().parents[2])


def receipt_root(root: Path | None = None) -> Path:
    return (root or _root()) / "batch_state" / RECEIPT_DIR


def _receipt_path(head: str, route: str, root: Path | None = None) -> Path:
    if not SHA.fullmatch(head) or not ROUTE.fullmatch(route):
        raise CanaryError("receipt identity invalid")
    return receipt_root(root) / head / f"{route}.json"


def _settled_receipt(record: Mapping[str, Any], result: str, *, head: str) -> dict:
    """The receipt a settled task supports, from facts no copy of the contract code changes.

    The receipt is bound to the exact head commit, which fixes the contract assets and the
    whole dispatcher tree, to the clean dispatcher checkout at that head that settled the
    task, and to the route and model. A verdict-bound task settles ``done`` only after that
    candidate dispatcher's own receipt gate accepted its reply, so the gate, running main's
    code, need not re-parse the reply with main's copy of the contract.
    """
    if not SHA.fullmatch(head):
        raise CanaryError("PR head is not a full commit SHA")
    checks = (
        (record.get("status") == "done", "task did not settle done"),
        (record.get("mode") == "read-only", "task is not read-only"),
        # Only a verdict-bound code or infra task outside a bound review attempt settles through the
        # dispatcher's canonical receipt gate (worker._receipt_failure).
        (record.get("require_review_verdict") is True and record.get("schema_version") == 2
         and record.get("review_profile") in {"code", "infra"} and not record.get("review_attempt"),
         "task did not settle through the receipt gate"),
        # The worktree started at the PR head and was still there when the task settled.
        (record.get("worktree_start_sha") == head and record.get("head_sha") == head,
         "task did not review the PR head"),
        # A canary is never a review of record: a branch- or PR-pinned task could be recorded as one.
        (not record.get("review_branch") and not record.get("pr"), "task is branch- or PR-pinned"),
    )
    for ok, why in checks:
        if not ok:
            raise CanaryError(why)
    code = record.get("dispatcher_code")
    if not isinstance(code, Mapping) or code.get("head") != head or code.get("clean") is not True:
        raise CanaryError("task was not supervised by the candidate's clean dispatcher")
    route = record.get("agent")
    candidates = _formal_candidates()
    if route not in candidates:
        raise CanaryError(f"route {route!r} is not a required reviewer route")
    if record.get("model") not in _route_models(candidates[route]):
        raise CanaryError(f"model {record.get('model')!r} is not a formal reviewer on route {route}")
    if record.get("result_sha256") != hashlib.sha256(result.encode()).hexdigest():
        raise CanaryError("result does not match the task record")
    return {
        "schema": SCHEMA,
        "eligible_as_review": False,
        "head": head,
        "route": route,
        "model": record["model"],
        "task_id": record.get("task_id"),
        "result_sha256": record["result_sha256"],
        "dispatcher_head": code["head"],
    }


def build_receipt(record: Mapping[str, Any], result: str, *, head: str) -> dict:
    """The canary receipt for one settled task, or ``CanaryError`` naming why it is not one.

    Recording also checks the reply is a canonical receipt with the recorder's copy of the
    contract, which is the candidate's when ``record`` runs from the candidate worktree.
    """
    from scripts.review.review_contract import ContractError, canonical_receipt_payload

    receipt = _settled_receipt(record, result, head=head)
    try:
        canonical_receipt_payload(result)
    except ContractError as exc:
        raise CanaryError("result is not a canonical receipt") from exc
    return receipt


def refusal(paths: Iterable[str], head: str, root: Path | None = None) -> str | None:
    """None when the change may queue; otherwise the typed detail of ``REASON``.

    A change outside ``CONTRACT_PATHS`` needs nothing. A contract change needs a valid
    receipt for every required route at ``head``, and each receipt must still be what its
    settled task record and reply build. An unknown route list, an unreadable receipt or
    task, and a receipt its task does not rebuild all refuse.
    """
    if not touches_contract(paths):
        return None
    try:
        routes = required_routes()
    except Exception as exc:  # an unreadable catalog must refuse, never crash the caller's run
        return f"unverifiable: {exc}" if isinstance(exc, CanaryError) else f"unverifiable: {type(exc).__name__}"
    missing: list[str] = []
    for route in routes:
        try:
            receipt = json.loads(_receipt_path(head, route, root).read_text(encoding="utf-8"))
        except FileNotFoundError:
            missing.append(route)
            continue
        except Exception:  # unreadable, malformed or too deeply nested: refuse, never crash
            return f"unverifiable: receipt for {route}"
        if not isinstance(receipt, dict) or (
            receipt.get("schema"), receipt.get("eligible_as_review"), receipt.get("head"), receipt.get("route")
        ) != (SCHEMA, False, head, route):
            return f"unverifiable: receipt for {route}"
        try:
            # The file is a claim; the settled task it names is the evidence.
            task, result = _load_task(str(receipt.get("task_id")))
            rebuilt = _settled_receipt(task, result, head=head)
        except Exception:
            return f"unverifiable: task behind the receipt for {route}"
        if rebuilt != receipt:
            return f"unverifiable: receipt for {route} does not match its task"
    return f"missing: {','.join(missing)}" if missing else None


def _load_task(task_id: str) -> tuple[dict, str]:
    """A dispatcher task record and its reply, decoded without newline translation."""
    from scripts.dispatcher import store

    task = store.read(task_id)
    result_file = task.get("result_file")
    if not isinstance(result_file, str):
        raise CanaryError("task has no result")
    return task, Path(result_file).read_bytes().decode("utf-8")


def record(task_id: str, root: Path | None = None) -> Path:
    """Write the receipt for one settled canary task at the head it reviewed.

    The keeper and ``pr-merge`` read receipts only at the PR's live head, so a receipt
    for any other head never admits anything.
    """
    task, result = _load_task(task_id)
    receipt = build_receipt(task, result, head=str(task.get("head_sha")))
    path = _receipt_path(receipt["head"], receipt["route"], root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("routes", help="Print the required reviewer routes")
    rec = sub.add_parser("record", help="Record one settled canary task as canary evidence")
    rec.add_argument("--task-id", required=True)
    chk = sub.add_parser("check", help="Print the refusal for a PR head, if any")
    chk.add_argument("--head", required=True)
    chk.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    try:
        if args.command == "routes":
            print("\n".join(required_routes()))
        elif args.command == "record":
            print(record(args.task_id))
        else:
            detail = refusal(args.paths, args.head)
            print(f"{REASON}: {detail}" if detail else "ok")
            return 1 if detail else 0
    except (CanaryError, ValueError, OSError) as exc:
        print(f"{REASON}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
