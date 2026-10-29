"""The uk-preamble runner extension: plan candidate cells and preflight them.

A sealed request bundle (private, G1) is one JSON object::

    {"bundle": "uk-behaviour-v2/requests", "split": "development",
     "items": [{"family": "<family>", "item": {<candidate-visible request item>}}]}

Each item is rendered once by its production adapter, so both candidates
receive identical bytes, and planned as one ``TaskSpec`` per candidate seat and
repeat 1-3 for the inherited ``uk_preamble.runner.Executor``. Paid execution
stays refused until the manifest admits the baseline; ``preflight`` only
writes prompts privately and validates each dispatch with the dispatcher's dry
run.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts.eval.uk_preamble.common import HarnessError, Seat, read_json, sha256_text
from scripts.eval.uk_preamble.runner import TaskSpec

from . import adapters
from .contract import CANDIDATE_SEATS, FAMILIES, HARNESS, PRIVATE_PROMPT_SLOTS, REPEATS, SCORER, SPLITS

BUNDLE_SCHEMA = "uk-behaviour-v2/requests"
TASK_PREFIX = "ukb"


def load_bundle(path: Path) -> dict[str, Any]:
    bundle = read_json(path)
    if not isinstance(bundle, dict) or bundle.get("bundle") != BUNDLE_SCHEMA:
        raise HarnessError(f"{path.name} is not a {BUNDLE_SCHEMA} bundle")
    if bundle.get("split") not in SPLITS:
        raise HarnessError("bundle split is unknown")
    items = bundle.get("items")
    if not isinstance(items, list) or not items:
        raise HarnessError("bundle has no items")
    ids = [entry.get("item", {}).get("item_id") for entry in items]
    if len(ids) != len(set(ids)):
        raise HarnessError("bundle item ids repeat")
    return bundle


def render_item(family: str, item: dict[str, Any], prompts: dict[str, bytes]) -> str:
    """The candidate request bytes of one item; ``prompts`` holds pin-checked private prompts."""
    contract = FAMILIES[family]
    if family in ("fresh_lesson", "fresh_activities"):
        return adapters.render_fresh(family, item)
    if family == "v7_module":
        return adapters.render_v7(item, adapters.production_asset(family))
    if contract.prompt in PRIVATE_PROMPT_SLOTS.values():
        if family not in prompts:
            raise HarnessError(f"{family} needs its accepted private prompt")
        return adapters.render_review(family, item, prompts[family])
    return adapters.render_review(family, item, adapters.production_asset(family))


def _opaque(item_id: str) -> str:
    return hashlib.sha256(item_id.encode("utf-8")).hexdigest()[:10]


def plan_cells(
    bundle: dict[str, Any],
    prompts: dict[str, bytes],
    run_tag: str,
    seats: Sequence[Seat] | None = None,
    repeats: int = REPEATS,
) -> list[TaskSpec]:
    """One task per seat x item x repeat; identical request bytes for every seat."""
    seats = list(seats or CANDIDATE_SEATS.values())
    tasks = []
    for entry in bundle["items"]:
        family, item = entry["family"], entry["item"]
        if family not in FAMILIES:
            raise HarnessError(f"unknown family {family!r}")
        try:
            prompt = render_item(family, item, prompts)
        except adapters.AdapterError as exc:
            raise HarnessError(f"{_opaque(item.get('item_id', ''))}: {exc}") from exc
        meta = {
            "family": family,
            "item_sha256": sha256_text(item["item_id"]),
            "judging_mode": item["judging_mode"],
            "split": bundle["split"],
            "tool_policy": adapters.tool_policy(family),
            "harness": HARNESS,
            "scorer": SCORER,
        }
        for seat in seats:
            for repeat in range(1, repeats + 1):
                task_id = f"{TASK_PREFIX}-{run_tag}-{seat.code}-{_opaque(item['item_id'])}-r{repeat}"
                tasks.append(
                    TaskSpec(
                        task_id=task_id,
                        seat=seat,
                        kind=FAMILIES[family].kind,
                        variant="baseline",
                        repeat=repeat,
                        item_ids=(item["item_id"],),
                        prompt=prompt,
                        meta=meta,
                    )
                )
    return tasks


def admission_refusal(manifest: dict[str, Any]) -> str | None:
    """Why paid execution is refused, or None once the manifest admits it."""
    if manifest.get("baseline_authorized_by_this_artifact") is not True:
        return "the manifest does not authorize the baseline; G1-G4 seals and a separate GO come first"
    missing = [entry["ref"] for entry in manifest.get("private_references", []) if not entry.get("sha256")]
    if missing:
        return f"{len(missing)} private references are still unsealed"
    return None
