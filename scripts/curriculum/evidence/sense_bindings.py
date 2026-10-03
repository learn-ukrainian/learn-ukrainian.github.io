"""Public binding integrity and host-local keyed evidence. No private text in errors."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.validate import a1_reference
from scripts.review.model_catalog import load_model_catalog, resolve_catalog_model_id
from scripts.review.receipts import ledger

from . import lock, sources
from . import reference_sense_v1 as matcher

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = "registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml"
BINDINGS = "_sense_bindings.yaml"
CI_NOTICE = "unverifiable in CI (local receipt required)"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def keyed(value: object, key: bytes) -> str:
    if len(key) < 32:
        raise ValueError("commitment_key_invalid")
    return hmac.new(key, canonical(value), hashlib.sha256).hexdigest()


def public_entries(path: Path) -> list[dict]:
    """Disambiguate repeated page locators by their public inventory row position."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = [row for source in payload["sources"] for row in source["headwords"]]
    return [{**row, "locator": f"{row['locator']}#{index + 1}"} for index, row in enumerate(rows)]


def private_entries(path: Path, inventory: list[dict]) -> dict[str, dict]:
    """Require total, unique, inventory-bound coverage before any selection."""
    values = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    by_locator = {row["locator"]: row for row in values}
    if len(by_locator) != len(values) or set(by_locator) != {row["locator"] for row in inventory}:
        raise ValueError("private_inventory_coverage_invalid")
    for row in inventory:
        private = by_locator[row["locator"]]
        if (
            private.get("inventory_label", private.get("printed_label")) != row["stressed"]
            or not isinstance(private.get("meaning"), str)
            or not private["meaning"].strip()
        ):
            raise ValueError("private_entry_invalid")
    return by_locator


def load(path: Path, level: str) -> dict[str, dict]:
    if not path.exists():
        return {}
    lock.require(path)
    payload = yaml.safe_load(path.read_text())
    schema = json.loads((ROOT / "schemas/evidence-sense-bindings-v1.schema.json").read_text())
    if list(Draft202012Validator(schema).iter_errors(payload)) or payload["level"] != level:
        raise ValueError("sense_bindings_invalid")
    entries = payload["bindings"]
    if len({entry["word"] for entry in entries}) != len(entries):
        raise ValueError("sense_bindings_duplicate")
    return {entry["word"]: entry for entry in entries}


def write(path: Path, level: str, entries: dict[str, dict]) -> str:
    return lock.write(
        path,
        lock.yaml_bytes(
            {
                "bindings_schema": 1,
                "level": level,
                "matcher": matcher.VERSION,
                "bindings": [entries[k] for k in sorted(entries)],
            }
        ),
    )


@dataclass
class Context:
    level: str
    entries: dict[str, dict]
    inventory: list[dict]
    invalid: bool = False

    @classmethod
    def read(cls, level: str, evidence_dir: Path, inventory_path: Path | None = None) -> Context:
        inventory = public_entries(inventory_path or a1_reference.INVENTORY_PATH) if level == "a1" else []
        try:
            entries = load(evidence_dir / BINDINGS, level)
        except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError):
            return cls(level, {}, inventory, True)
        return cls(level, entries, inventory)

    def members(self, word: dict) -> list[dict]:
        return [
            r
            for r in self.inventory
            if a1_reference.normalize(word["lemma"])
            in {a1_reference.normalize(v) for v in (r["lemma"], *r.get("variants", []))}
        ]

    def select(self, word: dict, rows: list[dict], payload: dict | None, **kwargs) -> sources.GlossSelection:
        """An exact binding wins; any other word, reference member or not, takes the plain first meaning."""
        binding = self.entries.get(word["id"])
        if self.invalid:
            return sources.GlossSelection(reason="reference_binding_invalid")
        if binding:
            candidates = matcher.candidates(word, rows, pronoun_entry=kwargs.get("pronoun_entry"))
            selected = next(
                (c for c in candidates if all(c[k] == binding.get(k) for k in matcher.REF_FIELDS)),
                None,
            )
            if binding["method"] == matcher.METHOD and (
                binding["inventory"] != INVENTORY
                or binding["locator"] not in {r["locator"] for r in self.members(word)}
            ):
                selected = None
            if selected is None:
                return sources.GlossSelection(reason="reference_binding_invalid")
            return sources.GlossSelection(
                binding["span"],
                "dmklinger_uk_en",
                {k: binding[k] for k in matcher.REF_FIELDS},
            )
        if word.get("gloss_basis"):
            return sources.GlossSelection(reason="reference_binding_invalid")
        return sources.select_gloss(word, rows, payload, **kwargs)

    def basis(self, word_id: str) -> dict | None:
        binding = self.entries.get(word_id)
        return {"method": binding["method"], "binding": f"{BINDINGS}#{word_id}"} if binding else None


def reference_binding(word: dict, ref: dict, private: dict, key: bytes, key_id: str) -> dict:
    return {
        "word": word["id"],
        "method": matcher.METHOD,
        **ref,
        "inventory": INVENTORY,
        "locator": private["locator"],
        "commitment": keyed(private, key),
        "key_id": key_id,
    }


def candidate_list(word: dict, rows: list[dict]) -> list[dict]:
    """Reviewable public values only; their digest is the review's exact subject."""
    return [
        {**{k: c[k] for k in matcher.REF_FIELDS}, "labels": list(c["labels"]), "definitions": list(c["definitions"])}
        for c in matcher.candidates(word, rows)
    ]


def reviewed_binding(
    word: dict,
    pool: list[dict],
    row_id: int,
    span_index: int,
    task_id: str,
    tasks_dir: Path,
    author_model: str | None = None,
    *,
    atom_index: int = 0,
) -> dict:
    """Derive reviewer identity from a sealed terminal dispatch and MCP ledger."""
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", task_id):
        raise ValueError("review_task_invalid")
    task = json.loads((tasks_dir / f"{task_id}.json").read_text())
    if task.get("task_id") != task_id or task.get("status") != "done" or task.get("review_profile") != "ukrainian":
        raise ValueError("review_not_done_or_unrelated")
    if task.get("agent") == "cursor" and not task.get("resolved_model_known"):
        raise ValueError("review_identity_unknown")
    recorded_author = task.get("review_author_model")
    if not recorded_author or (author_model is not None and recorded_author != author_model):
        raise ValueError("review_author_identity_invalid")
    if task.get("effort") != "high":
        raise ValueError("review_effort_invalid")
    catalog = load_model_catalog()
    model = task.get("resolved_model") if task.get("resolved_model_known") else task.get("model")
    model_id = resolve_catalog_model_id(model, catalog)
    author_id = resolve_catalog_model_id(recorded_author, catalog)
    if not model_id or not author_id:
        raise ValueError("review_identity_unknown")
    seat, author = catalog["models"][model_id], catalog["models"][author_id]
    if (
        seat["family"] == author["family"]
        or seat["family"] not in {"openai", "anthropic", "google"}
        or seat["lifecycle"] not in {"active", "fallback"}
        or "ukrainian_review" not in seat["roles"]
    ):
        raise ValueError("review_family_invalid")
    transport = {"claude": "native_claude", "codex": "native_codex", "agy": "agy", "cursor": "cursor"}.get(
        task.get("agent")
    )
    if transport not in seat["transports"]:
        raise ValueError("review_harness_invalid")
    result = Path(task["result_file"]).read_bytes()
    if hashlib.sha256(result).hexdigest() != task.get("result_sha256"):
        raise ValueError("review_result_changed")
    verdict = json.loads(result)
    chosen = next(
        (c for c in pool if c["id"] == row_id and c["span_index"] == span_index and c["atom_index"] == atom_index), None
    )
    subject = {"word": word["id"], "candidates_sha256": digest(pool), **(chosen or {})}
    if chosen is None or verdict.get("verdict") != "APPROVE" or verdict.get("subject") != subject:
        raise ValueError("review_subject_stale_or_unapproved")
    attempt = task.get("review_attempt") or {}
    if not all(attempt.get(k) for k in ("review_id", "attempt_id", "manifest_sha256")):
        raise ValueError("review_sources_unproven")
    # Existing append-only ledger verifies its sidecar; result assertions alone
    # cannot establish a sources call or bind it to this review attempt.
    receipt_path = tasks_dir.parent / "review-receipts" / attempt["review_id"] / f"{attempt['attempt_id']}.jsonl"
    if not all(re.fullmatch(r"[a-zA-Z0-9_-]+", attempt[k]) for k in ("review_id", "attempt_id")) or not re.fullmatch(
        r"[0-9a-f]{64}", attempt["manifest_sha256"]
    ):
        raise ValueError("review_sources_unproven")
    receipts = ledger.records(receipt_path)

    def proves_call(receipt: dict, tool: str) -> bool:
        arguments = receipt.get("arguments", {})
        queried = (
            arguments.get("words", [])
            if tool == "verify_words"
            else [arguments.get("query" if tool == "query_cefr_level" else "word")]
        )
        return (
            receipt.get("review_id") == attempt["review_id"]
            and receipt.get("attempt_id") == attempt["attempt_id"]
            and receipt.get("manifest_sha256") == attempt["manifest_sha256"]
            and receipt.get("tool") == tool
            and receipt.get("status") == "ok"
            and not receipt.get("outcome_facts", {}).get("unavailable", True)
            and word["lemma"] in queried
        )

    if not all(
        any(proves_call(r, tool) for r in receipts)
        for tool in ("verify_words", "query_cefr_level", "check_russian_shadow")
    ):
        raise ValueError("review_sources_unproven")
    finished = task.get("finished_at", "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}T", finished):
        raise ValueError("review_date_invalid")
    return {
        "word": word["id"],
        "method": "reviewed.v1",
        **{k: chosen[k] for k in matcher.REF_FIELDS},
        "reviewer": {
            "task_id": task_id,
            "model": model,
            "author_model": recorded_author,
            "family": seat["family"],
            "harness": task.get("harness") or task["agent"],
            "date": finished[:10],
            "candidates_sha256": digest(pool),
            "result_sha256": task["result_sha256"],
        },
    }


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=30).stdout


def receipt_payload(bindings: Path, private: dict, key: bytes, key_id: str, repo: Path) -> dict:
    """The head and all public/private selection inputs are part of the seal."""
    if git(repo, "status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError("receipt_requires_clean_head")
    return {
        "bindings_sha256": hashlib.sha256(bindings.read_bytes()).hexdigest(),
        "private_input_commitment": keyed(private, key),
        "key_id": key_id,
        "matcher": matcher.VERSION,
        "head": git(repo, "rev-parse", "HEAD").decode().strip(),
    }


def write_receipt(path: Path, payload: dict, key: bytes) -> None:
    lock.atomic_write(path, canonical({"payload": payload, "seal": keyed(payload, key)}), mode=0o600)


def verify_receipt(path: Path, payload: dict, key: bytes) -> bool:
    try:
        receipt = json.loads(path.read_bytes())
        return receipt["payload"] == payload and hmac.compare_digest(receipt["seal"], keyed(payload, key))
    except (OSError, ValueError, KeyError, TypeError):
        return False
