"""Public binding integrity and host-local keyed evidence. No private text in errors."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from scripts.common.jsonl import jsonl_lines as split_jsonl_lines
from scripts.curriculum.validate import a1_reference
from scripts.review.model_catalog import load_model_catalog, resolve_catalog_model_id
from scripts.review.receipts import ledger

from . import formulas, lock, sources
from . import reference_sense_v1 as matcher

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = "registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml"
BINDINGS = "_sense_bindings.yaml"
# Anna Ohoiko's A1 dictionary chooses the English after the request note and ULIF (operator, 2026-10-03).
BOOK_METHOD = sources.REFERENCE_SOURCE
# What CI cannot check for each binding method without the local receipt.
LOCAL_PROOF_METHODS = {
    matcher.METHOD: "private_commitment",
    BOOK_METHOD: "private_commitment",
    "reviewed.v1": "review_provenance",
}
CI_NOTICE = "unverifiable in CI (local receipt required)"


def local_proof(binding: dict) -> str | None:
    """What CI cannot check for this binding; a formula needs a receipt only when it commits to the book."""
    if binding.get("method") == formulas.METHOD:
        return "private_commitment" if "commitment" in binding else None
    return LOCAL_PROOF_METHODS.get(binding.get("method"))


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
    values = [json.loads(line) for line in split_jsonl_lines(path.read_text()) if line.strip()]
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
        if word.get("kind") == "formula":
            return []
        return [
            r
            for r in self.inventory
            if a1_reference.normalize(word["lemma"])
            in {a1_reference.normalize(v) for v in (r["lemma"], *r.get("variants", []))}
        ]

    def labelled(self, word: dict) -> list[dict]:
        """POS-compatible entries whose printed headword, stress and terminal punctuation removed, is the lemma."""
        return [
            r
            for r in self.inventory
            if printed_headword(r["stressed"]) == word["lemma"] and compatible_pos(r["pos"], word["pos"])
        ]

    def select(self, word: dict, rows: list[dict], payload: dict | None, **kwargs) -> sources.GlossSelection:
        """An exact or reviewed binding wins; Anna's dictionary follows the note and ULIF; else the plain first meaning.

        A formula takes only its own ``formula_row.v1`` binding.
        """
        binding = self.entries.get(word["id"])
        if word.get("kind") == "formula":
            if self.invalid:
                return sources.GlossSelection(reason="formula_binding_invalid")
            if not binding:
                return sources.GlossSelection(reason="formula_binding_missing")
            pool = candidate_list(word, rows)
            selected = next((c for c in pool if all(c[k] == binding.get(k) for k in matcher.REF_FIELDS)), None)
            reference_valid = "commitment" not in binding or (
                binding.get("inventory") == INVENTORY
                and binding.get("locator")
                in {
                    r["locator"]
                    for r in self.inventory
                    if any(
                        formulas.printed_headword(v) == formulas.printed_headword(word["text"])
                        for v in (r["lemma"], r.get("stressed", ""), *r.get("variants", []))
                    )
                }
            )
            if (
                not reference_valid
                or binding.get("method") != formulas.METHOD
                or binding.get("word") != word["id"]
                or selected is None
                or word.get("definition_sha256") != formulas.definition_digest(word)
                or binding.get("definition_sha256") != word.get("definition_sha256")
                or binding.get("candidates_sha256") != digest(pool)
            ):
                return sources.GlossSelection(reason="formula_binding_invalid")
            return sources.GlossSelection(
                binding["span"],
                "dmklinger_uk_en",
                {k: binding[k] for k in matcher.REF_FIELDS},
                basis={"method": formulas.METHOD, "binding": f"{BINDINGS}#{word['id']}"},
            )
        if self.invalid:
            return sources.GlossSelection(reason="reference_binding_invalid")
        if binding and binding["method"] == BOOK_METHOD:
            if binding["inventory"] != INVENTORY or binding["locator"] not in {
                r["locator"] for r in self.labelled(word)
            }:
                return sources.GlossSelection(reason="reference_binding_invalid")
            selection = sources.select_gloss(word, rows, payload, reference=binding, **kwargs)
            if not selection.by_reference:
                return selection
            basis = {"method": BOOK_METHOD, "binding": f"{BINDINGS}#{word['id']}", "locator": binding["locator"]}
            return replace(selection, basis=basis)
        if binding:
            if binding["method"] == formulas.METHOD:
                return sources.GlossSelection(reason="reference_binding_invalid")
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
                basis={"method": binding["method"], "binding": f"{BINDINGS}#{word['id']}"},
            )
        if word.get("gloss_basis"):
            return sources.GlossSelection(reason="reference_binding_invalid")
        return sources.select_gloss(word, rows, payload, **kwargs)


def printed_headword(label: str) -> str:
    """A printed dictionary label as a lemma: stress marks and terminal punctuation removed."""
    return sources.unstressed_headword(label).strip().rstrip(".,;:!?…").strip()


def book_choice(
    word: dict, rows: list[dict], payload: dict | None, meanings: list[str], *, pronoun_entry: bool | None = None
) -> tuple[dict, int] | None:
    """Anna Ohoiko's A1 dictionary chooses the English for a word it prints.

    The first open-dictionary learner candidate (inside a ULIF-pinned row
    when ULIF decides the homonym) equal to one of her meanings, compared as
    ``reference_sense_v1`` normalises, is the gloss. If none equals and ULIF
    pinned no row, her first meaning's head is the gloss when it is a learner
    gloss (verbs with ``to``). Returns the choice and the index of the meaning
    that made it, or ``None``: the plain first meaning.
    """
    pos = word["pos"]
    pool, ulif_pinned = sources.reference_pool(word, rows, payload, pronoun_entry=pronoun_entry)
    keys = [set(matcher.atoms(meaning, pos)) for meaning in meanings]
    for candidate in pool:
        key = matcher.normalize(candidate["head"], pos)
        index = next((i for i, atoms in enumerate(keys) if key in atoms), None)
        if index is not None:
            return {"gloss": candidate["span"], "match": "dictionary"}, index
    if ulif_pinned or not meanings:
        return None
    group = matcher.classify(meanings[0])
    heads = () if group.reason else matcher.source_atoms(group.head)
    if not heads:
        return None
    head = sources._gloss_head(heads[0])
    gloss = "to " + head.removeprefix("to ") if pos == "verb" else head
    return ({"gloss": gloss, "match": "book"}, 0) if sources.is_learner_gloss(gloss) else None


def compatible_pos(book_pos: str, pos: str) -> bool:
    """Her noun, verb and adjective labels bind a POS; adverb or unlabelled entries cover the closed classes."""
    open_class = {"noun", "verb", "adj"}
    return book_pos == pos or book_pos == "unlabelled" or (book_pos not in open_class and pos not in open_class)


def book_binding(word: dict, choice: dict, private: dict, key: bytes, key_id: str) -> dict:
    return {
        "word": word["id"],
        "method": BOOK_METHOD,
        **choice,
        "inventory": INVENTORY,
        "locator": private["locator"],
        "commitment": keyed(private, key),
        "key_id": key_id,
    }


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
        {
            **{k: c[k] for k in matcher.REF_FIELDS},
            "labels": list(c["labels"]),
            "definitions": list(c["definitions"]),
            **({"headword": c["headword"]} if word.get("kind") == "formula" else {}),
        }
        for c in matcher.candidates(word, rows)
    ]


def formula_binding(word: dict, pool: list[dict], chosen: dict) -> dict:
    """Pin only an eligible printed candidate; no formula review dispatch required."""
    if chosen not in pool or word.get("definition_sha256") != formulas.definition_digest(word):
        raise ValueError("formula_binding_invalid")
    return {
        "word": word["id"],
        "method": formulas.METHOD,
        "definition_sha256": word["definition_sha256"],
        "candidates_sha256": digest(pool),
        **{k: chosen[k] for k in matcher.REF_FIELDS},
    }


def choose_formula(
    word: dict, pool: list[dict], inventory: list[dict], private: dict | None = None
) -> tuple[dict | None, dict]:
    """Private meaning selects public wording, then request note, then source order.

    Diagnostics carry only public coordinates, locators and reason codes.
    """
    if not pool:
        return None, {"word": word["id"], "reason": "formula_binding_missing"}
    names = {formulas.printed_headword(word["text"])}
    for member in inventory:
        if not any(
            formulas.printed_headword(v) in names
            for v in (member["lemma"], member.get("stressed", ""), *member.get("variants", []))
        ):
            continue
        reference = (private or {}).get(member["locator"])
        if reference is None:
            continue
        group = matcher.classify(reference["meaning"])
        if group.reason:
            continue
        meanings = {
            matcher.normalize(a, "formula")
            for part in re.split(r"[!?]+(?:\s+|$)", group.head)
            for a in matcher.source_atoms(part)
        }
        chosen = next((c for c in pool if matcher.normalize(c["span"], "formula") in meanings), None)
        if chosen is not None:
            return chosen, {"word": word["id"], "reason": "formula_reference_match", "locator": member["locator"]}
    note = word.get("note", "")
    group = matcher.classify(note)
    meanings = (
        {matcher.normalize(a, "formula") for a in matcher.source_atoms(group.head)} if not group.reason else set()
    )
    chosen = next((c for c in pool if matcher.normalize(c["span"], "formula") in meanings), None)
    return (
        (chosen, {"word": word["id"], "reason": "formula_note_match"})
        if chosen
        else (pool[0], {"word": word["id"], "reason": "formula_first_meaning"})
    )


def auto_formula_binding(
    word: dict,
    rows: list[dict],
    inventory: list[dict],
    private: dict | None = None,
    key: bytes | None = None,
    key_id: str | None = None,
) -> tuple[dict | None, dict]:
    pool = candidate_list(word, rows)
    chosen, decision = choose_formula(word, pool, inventory, private)
    if chosen is None:
        if rows:
            raise ValueError("formula_gloss_ineligible")
        return None, decision
    binding = formula_binding(word, pool, chosen)
    if decision["reason"] == "formula_reference_match" and key is not None and key_id:
        binding.update(
            inventory=INVENTORY,
            locator=decision["locator"],
            commitment=keyed(private[decision["locator"]], key),
            key_id=key_id,
        )
    return binding, {**decision, **{k: chosen[k] for k in ("id", "span_index", "atom_index")}}


def rows_for(word: dict, api: sources.Sources) -> list[dict]:
    if word.get("kind") == "formula":
        return api.formula_rows(word).raw
    return api.gloss_rows([(word["lemma"], word["pos"])]).raw.get((word["lemma"], word["pos"]), [])


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
