"""Exact-artifact certification at word-card acceptance and export boundaries.

Only the repository review ledger grants approval. A run reads that authority
once, hashes each dependency once, and discards its cache on exit. Reimports and
cached packages therefore consult current withdrawals and snapshot bindings.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.atlas import word_card_golden_set as gold
from scripts.common.jsonl import jsonl_lines

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REVIEW_EVIDENCE_PATH = PROJECT_ROOT / "docs/atlas/word-cards/review-evidence-ledger.json"
PERMISSIONS_REGISTER_PATH = PROJECT_ROOT / "docs/sources/permissions-register.yaml"
SCHEMA_PATH = PROJECT_ROOT / "schemas/word-card-v1.schema.json"
IMPLEMENTATION_PATHS = (
    *sorted(PROJECT_ROOT.glob("scripts/atlas/*.py")),
    *sorted(PROJECT_ROOT.glob("scripts/review/**/*.py")),
    PROJECT_ROOT / "scripts/dispatcher/providers/agy.py",
    PROJECT_ROOT / "scripts/dispatcher/types.py",
    PROJECT_ROOT / "scripts/agent_runtime/adapters/agy.py",
    PROJECT_ROOT / "scripts/audit/generate_practice_deck.py",
    PROJECT_ROOT / "scripts/lexicon/teacher_deck_shard.py",
    PROJECT_ROOT / "scripts/practice/densify_paradigm_from_lexemes.py",
    PROJECT_ROOT / "scripts/lexicon/runner/ulif_dictua_parse.py",
    PROJECT_ROOT / "scripts/lexicon/source_attribution.py",
    PROJECT_ROOT / "scripts/lexicon/ulif_raw_cache.py",
    PROJECT_ROOT / "scripts/lexicon/lemma_normalization.py",
    PROJECT_ROOT / "scripts/wiki/sources_db.py",
    PROJECT_ROOT / "scripts/lexicon/manifest_io.py",
    PROJECT_ROOT / "scripts/lexicon/publish_manifest.py",
    PROJECT_ROOT / "scripts/lexicon/export_open_dataset.py",
    PROJECT_ROOT / "scripts/open_dataset/publish.py",
    PROJECT_ROOT / "scripts/open_dataset/russification.py",
    PROJECT_ROOT / "scripts/open_dataset/hydrate.py",
    PROJECT_ROOT / "scripts/config/vesum_source.lock.json",
    PROJECT_ROOT / "scripts/projects/open_model_data/source_completeness_manifest.py",
    PROJECT_ROOT / "scripts/projects/open_model_data/word_cards/dataset_projection.py",
)
RULE_PATHS = (
    *sorted(PROJECT_ROOT.glob("schemas/word-card-*.schema.json")),
    PROJECT_ROOT / "docs/atlas/word-cards/schema.md",
    PROJECT_ROOT / "docs/atlas/word-cards/identity.md",
    PROJECT_ROOT / "docs/atlas/word-cards/export-invariants.md",
    PROJECT_ROOT / "docs/atlas/word-cards/acceptance-export-path-census.json",
    PROJECT_ROOT / "docs/atlas/word-cards/golden-set-spec.md",
    PROJECT_ROOT / "docs/atlas/word-cards/certification-spec.md",
    PROJECT_ROOT / "agents_extensions/shared/rules/ukrainian-linguistics.md",
    PROJECT_ROOT / "agents_extensions/shared/rules/mcp-sources-and-dictionaries.md",
    PROJECT_ROOT / "registry/atlas/source-completeness/manifest-contract.md",
    PROJECT_ROOT / "docs/sources/permissions-register.yaml",
    PROJECT_ROOT / "scripts/config/model_catalog.yaml",
)


class UncertifiedCardRefusal(ValueError):
    """No acceptance or export output may be written after this refusal."""


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class CertificationAuthority:
    """Authority snapshot and dependency hashes for one acceptance/export run."""

    def __init__(self) -> None:
        self.hashes: dict[Path, str] = {}
        self.snapshots: dict[tuple[str, str], str] = {}
        self.json_values: dict[Path, Any] = {}
        self.certifications: dict[str, dict] = {}
        self.ledger = json.loads(REVIEW_EVIDENCE_PATH.read_bytes())
        if self.ledger.get("schema_version") != "word-card-review-evidence.v1":
            raise UncertifiedCardRefusal("unsupported review evidence ledger")
        reviews = self.ledger["approved_reviews"]
        if not isinstance(reviews, list):
            raise UncertifiedCardRefusal("approved_reviews must be a list")
        self.reviews = {r["card_id"]: r for r in reviews}
        if len(self.reviews) != len(reviews):
            raise UncertifiedCardRefusal("duplicate card review evidence")
        self.validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_bytes()))
        self.implementation = self.fingerprint(IMPLEMENTATION_PATHS)
        self.rules = self.fingerprint(RULE_PATHS)
        self.register = self.file_hash(PERMISSIONS_REGISTER_PATH)

    def file_hash(self, path: Path) -> str:
        if path not in self.hashes:
            with path.open("rb") as source:
                self.hashes[path] = hashlib.file_digest(source, "sha256").hexdigest()
        return self.hashes[path]

    def fingerprint(self, paths: tuple[Path, ...]) -> str:
        return digest({p.relative_to(PROJECT_ROOT).as_posix(): self.file_hash(p) for p in paths})

    def snapshot(self, category: str, name: str) -> str:
        if (category, name) in self.snapshots:
            return self.snapshots[category, name]
        binding = self.ledger["snapshot_bindings"][category][name]
        relative = Path(binding["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise UncertifiedCardRefusal("snapshot authority must be repository relative")
        path = (PROJECT_ROOT / relative).resolve()
        if not path.is_relative_to(PROJECT_ROOT.resolve()):
            raise UncertifiedCardRefusal("snapshot authority must be repository relative")
        # A lock may name a canonical data digest instead of being the data.
        # Its bytes are still bound by the review's implementation fingerprint.
        if "json_keys" in binding or binding.get("canonical_json") is True:
            if path not in self.json_values:
                self.json_values[path] = json.loads(path.read_bytes())
            value = self.json_values[path]
            for key in binding.get("json_keys", []):
                value = value[key]
            self.snapshots[category, name] = digest(value) if binding.get("canonical_json") is True else value
        else:
            self.snapshots[category, name] = self.file_hash(path)
        return self.snapshots[category, name]


_AUTHORITY: ContextVar[dict[str, CertificationAuthority] | None] = ContextVar("word_card_authority", default=None)


@contextmanager
def certification_run() -> Iterator[None]:
    """Reuse authority within this run, never across separately invoked runs."""
    current = _AUTHORITY.get()
    token = _AUTHORITY.set(current if current is not None else {})
    try:
        yield
    finally:
        _AUTHORITY.reset(token)


def looks_like_card(value: Any) -> bool:
    return isinstance(value, dict) and bool(
        {"card_id", "card_kind", "build", "quality", "assertions"}.intersection(value)
    )


@certification_run()
def load_certified_card_for_export(card: Any, *, required_approval: str = "dataset") -> dict[str, Any]:
    """Return only the exact certified card, with approval for this projection.

    There are no caller-supplied approvals, snapshot overrides or draft bypasses.
    Tests redirect the authority files to temporary fixtures.
    """
    try:
        if isinstance(card, str):
            card = json.loads(card)
        if not isinstance(card, dict) or "card_id" not in card:
            raise UncertifiedCardRefusal("entry is not a certified word card")
        state = _AUTHORITY.get()
        authority = state.get("authority")
        if authority is None:
            authority = CertificationAuthority()
            state["authority"] = authority
        if not authority.validator.is_valid(card):
            raise UncertifiedCardRefusal("invalid word-card schema")
        review = card["quality"]["linguistic_review"]
        build = card["build"]
        evidence = authority.reviews.get(card["card_id"], {})
        if build["rules_version"] in {f"a1-slice{i}-v1" for i in range(2, 7)}:
            return _load_code_first_card(card, evidence, authority, required_approval)
        if (card["state"] != "active" or card["quality"]["identity_confidence"] not in {"high", "medium"}
                or not isinstance(review.get("record"), str) or not review["record"].strip()
                or not isinstance(review.get("lane"), str) or not review["lane"].strip()
                or review["status"] != "reviewed" or required_approval not in review.get("approved_for", [])
                or evidence.get("status") != "active"
                or not isinstance(evidence.get("approved_for"), list)
                or required_approval not in evidence.get("approved_for", [])
                or evidence.get("record") != review.get("record")
                or evidence.get("lane") != review.get("lane")):
            raise UncertifiedCardRefusal("missing, withdrawn or inapplicable certification")
        if (build["rules_version"] != "rules-v1"
                or build["card_version"] != "cv_" + digest({k: v for k, v in card.items() if k != "build"})[:24]
                or evidence.get("card_version") != build["card_version"]
                or evidence.get("build_sha256") != digest(build)
                or evidence.get("implementation_sha256") != authority.implementation
                or evidence.get("rules_sha256") != authority.rules):
            raise UncertifiedCardRefusal("certification does not match artifact, implementation or rules")
        inputs = build["inputs"]
        for category in ("S", "V", "I", "O"):
            if not isinstance(inputs.get(category), dict) or not inputs[category]:
                raise UncertifiedCardRefusal("missing source or removal snapshot")
            for name, snapshot in inputs[category].items():
                if snapshot["content_sha256"] != authority.snapshot(category, name):
                    raise UncertifiedCardRefusal("source or removal snapshot changed")
        if ("vesum" not in inputs["V"] or "overlay" not in inputs["O"]
                or "suppressions" not in inputs["O"]
                or inputs["R"]["rules"]["version"] != build["rules_version"]
                or inputs["R"]["normaliser"]["version"] != "norm-v1"
                or inputs["R"]["register"]["content_sha256"] != authority.register):
            raise UncertifiedCardRefusal("missing or stale rules, permissions or suppression binding")
        reference = evidence.get("certification_receipt")
        gold.validate(reference, gold.REF, "mandatory Phase 5 certification receipt")
        key = digest(reference)
        if key not in authority.certifications:
            authority.certifications[key] = verify_certification_receipt(reference, REVIEW_EVIDENCE_PATH.parent)
        receipt = authority.certifications[key]
        if receipt["cards"].get(card["card_id"]) != digest(card):
            raise UncertifiedCardRefusal("card is outside exact-artifact certification")
        return card
    except UncertifiedCardRefusal:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise UncertifiedCardRefusal("missing or invalid certification authority") from exc


def _load_code_first_card(card: dict, evidence: dict, authority: CertificationAuthority, required_approval: str) -> dict:
    """Use exact A1 input bindings without requiring pilot-only serialization."""
    build = card["build"]
    if (card["state"] != "active" or card["quality"]["identity_confidence"] not in {"high", "medium"}
            or evidence.get("status") != "active" or required_approval not in evidence.get("approved_for", [])
            or not isinstance(evidence.get("record"), str) or not evidence["record"].strip()
            or not isinstance(evidence.get("lane"), str) or not evidence["lane"].strip()
            or evidence.get("card_version") != build["card_version"]
            or build["card_version"] != "cv_" + digest({k: v for k, v in card.items() if k != "build"})[:24]
            or evidence.get("build_sha256") != digest(build)
            or evidence.get("implementation_sha256") != authority.implementation
            or evidence.get("rules_sha256") != authority.rules):
        raise UncertifiedCardRefusal("missing, withdrawn, stale or inapplicable code-first approval")
    reference = evidence.get("certification_receipt")
    if not isinstance(reference, dict):
        raise UncertifiedCardRefusal("missing code-first certification receipt")
    gold.validate(reference, gold.REF, "mandatory code-first certification receipt")
    key = digest(reference)
    if key not in authority.certifications:
        authority.certifications[key] = verify_certification_receipt(reference, REVIEW_EVIDENCE_PATH.parent)
    receipt = authority.certifications[key]
    if receipt["schema_version"] != "word-card-certification-receipt.v2" or receipt["cards"].get(card["card_id"]) != digest(card):
        raise UncertifiedCardRefusal("card is outside exact code-first certification")
    return card


@certification_run()
def certified_inventory(manifest: Any, *, required_approval: str = "dataset") -> list[dict[str, Any]]:
    """Check both inventories, including mixed legacy/card manifests, before writes."""
    if not isinstance(manifest, dict):
        raise UncertifiedCardRefusal("invalid card inventory")
    if set(manifest) - {"cards", "entries", "version", "generated_at", "manifest_fingerprint"}:
        raise UncertifiedCardRefusal("unreviewed fields outside card inventory")
    for key in ("version", "generated_at"):
        if key in manifest and not isinstance(manifest[key], str):
            raise UncertifiedCardRefusal("invalid card inventory metadata")
    if "manifest_fingerprint" in manifest:
        fingerprint = manifest["manifest_fingerprint"]
        if (not isinstance(fingerprint, dict) or set(fingerprint) != {"schema_version", "fingerprint"}
                or type(fingerprint["schema_version"]) is not int or not isinstance(fingerprint["fingerprint"], str)):
            raise UncertifiedCardRefusal("invalid card inventory fingerprint")
    cards = []
    for key in ("cards", "entries"):
        if key in manifest:
            if not isinstance(manifest[key], list):
                raise UncertifiedCardRefusal("invalid card inventory")
            cards.extend(manifest[key])
    if not cards:
        raise UncertifiedCardRefusal("empty certified inventory")
    for card in cards:
        load_certified_card_for_export(card, required_approval=required_approval)
    if len({card["card_id"] for card in cards}) != len(cards):
        raise UncertifiedCardRefusal("duplicate certified card")
    return cards


def card_entry_type(card: dict[str, Any]) -> str:
    """Map schema card kinds to the existing Atlas article classification."""
    return {"lexeme": "lemma", "mwe": "multiword_term", "proper_name": "proper_name"}[card["card_kind"]]


def card_head(card: dict[str, Any]) -> str:
    return card["key_at_creation"]["spelling"]


def card_field(card: dict[str, Any], name: str) -> str | None:
    selected = card.get("fields", {}).get(name, {}).get("selected")
    for assertion in card.get("assertions", []):
        if assertion.get("assertion_id") == selected and assertion.get("status") == "active":
            value = assertion.get("value")
            return value.strip() or None if isinstance(value, str) else None
    return None


def guard_card_inventory(manifest: dict[str, Any], *, required_approval: str = "site") -> None:
    """Legacy evidence stays evidence; a card inventory must pass certification."""
    entries = manifest.get("entries", [])
    if ("cards" in manifest or manifest.get("certified") is True
            or (isinstance(entries, list) and any(looks_like_card(entry) for entry in entries))):
        certified_inventory(manifest, required_approval=required_approval)


# Phase 5 consumes independent evidence. It never appoints evaluators or creates gold.
FACETS = ("identity", "sense_binding", "stress", "source_fidelity", "citation_validity", "abstention")
CONTROL_FACETS = {"wrong-homonym": "identity", "wrong-stress": "stress",
                  "unsupported-definition": "source_fidelity"}
FROZEN = gold.obj({"implementation_sha256": gold.SHA, "rules_sha256": gold.SHA,
                   "inputs_sha256": gold.SHA})
PROJECTIONS = gold.obj({facet: gold.obj({"gold_field": gold.TEXT, "card_pointer": gold.TEXT}) for facet in FACETS})
CERTIFICATION_SPEC = gold.obj({
    "schema_version": {"const": "word-card-certification-spec.v1"},
    "gold_spec": gold.REF, "gold_seal": gold.REF, "isolation": gold.REF,
    "complete_data_receipt": gold.REF, "mechanics_receipt": gold.REF,
    "frozen": FROZEN, "author": gold.ACTOR,
    "evaluators": gold.array(gold.ADJUDICATOR, 2),
    "projections": PROJECTIONS,
    "cases": gold.array(gold.obj({"case_id": gold.TEXT, "card": gold.REF})),
    "controls": gold.array(gold.obj({"control_id": gold.TEXT, "case_id": gold.TEXT,
                                    "class": {"enum": list(CONTROL_FACETS)}, "card": gold.REF}), 3),
})
CODE_FIRST_SPEC = gold.obj({
    "schema_version": {"const": "word-card-certification-spec.v2"},
    "frozen": FROZEN, "author": gold.ACTOR,
    "batches": gold.array(gold.obj({
        "batch": {"enum": ["slice2", "slice3", "slice4", "slice5", "slice6"]},
        "assembly": gold.REF, "sources": gold.REF,
    })),
    "original50_receipt": {"anyOf": [gold.REF, {"type": "null"}]},
    "complete_data_receipt": {"anyOf": [gold.REF, {"type": "null"}]},
    "mechanics_receipt": {"anyOf": [gold.REF, {"type": "null"}]},
    "original50_selection": gold.REF, "original50_input": gold.REF,
    "removal_snapshots": {"anyOf": [gold.obj({"overlay": gold.SHA, "suppressions": gold.SHA}), {"type": "null"}]},
})
MECHANICS = gold.obj({
    "schema_version": {"const": "word-card-mechanics-acceptance.v1"},
    "status": {"const": "MECHANICS_ACCEPTED"}, "frozen": FROZEN,
    "cards_sha256": gold.SHA, "accepted_by": gold.ACTOR,
    "evidence": gold.array(gold.REF),
})
TASK_ACTOR = gold.obj({"task_id": gold.TEXT, "run_nonce": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
                       "model": gold.TEXT, "family": gold.TEXT})
OFFSET = {"type": "integer", "minimum": 0}
SPAN = {"type": "array", "items": OFFSET, "minItems": 2, "maxItems": 2}
FREEZER = gold.obj({"identity": gold.TEXT, "model": gold.TEXT, "record": gold.REF, "model_record": gold.REF,
    "identity_span": SPAN, "model_span": SPAN, "model_identity_span": SPAN,
    "task": {"anyOf": [TASK_ACTOR, {"type": "null"}]}})
NATIVE50 = gold.obj({
    "schema_version": {"const": "a1-original50-inspection.v1"}, "frozen": FROZEN,
    "selection_sha256": gold.SHA, "input_sha256": gold.SHA, "scope_sha256": gold.SHA,
    "authors": gold.array(TASK_ACTOR), "freezer": FREEZER, "producer": TASK_ACTOR,
    "transcript": gold.REF, "result": gold.REF,
})
NATIVE_CALL = gold.obj({"conversation_id": gold.TEXT, "step_index": OFFSET, "quote": gold.TEXT, "span": SPAN})
NATIVE_SCORE = gold.obj({"verdict": {"const": "pass"}, "reason": gold.TEXT,
    "findings": {"type": "array", "maxItems": 0}, "calls": gold.array(NATIVE_CALL)})
NATIVE_JUDGMENTS = gold.obj({"schema_version": {"const": "a1-original50-judgments.v1"},
    "scope_sha256": gold.SHA, "items": gold.array(gold.obj({"card_id": gold.TEXT,
        "card_version": gold.TEXT, "meaning": NATIVE_SCORE, "stress": NATIVE_SCORE}), 50)})
CODE_FIRST_DATA = gold.obj({"schema_version": {"const": "a1-complete-data-replay.v1"},
    "inputs": gold.obj(dict.fromkeys(gold.INPUT_NAMES, gold.REF)), "universe_count": gold.COUNT,
    "candidate_entry_count": gold.COUNT, "roles": gold.obj({"assembler": gold.ACTOR})})
ORIGINAL50_SELECTION_SHA256 = "21ee21005e6d79025541d41db4484fa889b9c145154d3eec101c8357db9a8c21"
ORIGINAL50_INPUT_SHA256 = "431c517ea6bde6b9df66bf4a2733cb5dba62097c31817e16f16207476f0cc15b"


def _native50_scope(inspection: dict, packet: dict, spec: dict) -> str:
    gold.validate(inspection, NATIVE50, "native original50 inspection")
    gold.require(spec["original50_selection"]["sha256"] == inspection["selection_sha256"]
                 == ORIGINAL50_SELECTION_SHA256
                 and spec["original50_input"]["sha256"] == inspection["input_sha256"]
                 == ORIGINAL50_INPUT_SHA256, "original50_selection_or_input_changed")
    scope = digest({"frozen": spec["frozen"], "original50": packet["original50"]})
    gold.require(len(packet["original50"]) == 50 and inspection["frozen"] == spec["frozen"]
                 and inspection["scope_sha256"] == scope
                 and all(r["current_version_matches"] and not any(a["missing"] for a in r["assertions"])
                         for r in packet["original50"]), "original50_membership_version_or_source_changed")
    return scope


def _native_task(actor: dict, task_root: Path, *, qualified_reviewer: bool = False) -> tuple[dict, str]:
    from scripts.review import record_cf_verdict as reviews

    task, reply = reviews._task(actor["task_id"], task_root)
    gold.require(task.get("run_nonce") == actor["run_nonce"] and bool(task.get("result_sha256"))
                 and task.get("repository") == "learn-ukrainian/learn-ukrainian.github.io"
                 and task.get("resolved_model_known") is True and task.get("returncode") == 0
                 and task.get("error") is None,
                 "original50_task_identity_mismatch")
    model = task["resolved_model"]
    if qualified_reviewer:
        model, family = reviews.reviewer_identity({**task, "model": model})
    else:
        family = reviews._author_model_family(task["agent"], model)
        gold.require(family not in reviews.UNRESOLVED_AUTHOR_FAMILIES, "original50_actor_model_unknown")
    gold.require((model, family) == (actor["model"], actor["family"]), "original50_actor_model_mismatch")
    return task, reply


def _native50_freezer(freezer: dict, authors: list[dict], producer: dict, base: Path) -> None:
    from scripts.review.record_cf_verdict import UNRESOLVED_AUTHOR_FAMILIES, resolve_family

    gold.require(resolve_family(freezer["model"]) not in UNRESOLVED_AUTHOR_FAMILIES,
                 "original50_freezer_model_unknown")
    freeze_record = gold.reference(freezer["record"], base).decode("utf-8")
    model_record = gold.reference(freezer["model_record"], base).decode("utf-8")
    for field, record, span in (("identity", freeze_record, "identity_span"),
                               ("identity", model_record, "model_identity_span"),
                               ("model", model_record, "model_span")):
        start, end = freezer[span]
        gold.require(0 <= start < end <= len(record) and record[start:end] == freezer[field],
                     "original50_freezer_identity_untraceable")
    gold.require(freezer["identity"].removeprefix("session:") not in
                 {a["task_id"].removeprefix("session:") for a in [*authors, producer]},
                 "original50_freezer_not_independent")


def _native50_sources(score: dict, facet: str, lemma: str, calls: dict) -> None:
    from scripts.agent_runtime.adapters.agy import _SAVED_OUTPUT_POINTER_RE
    from scripts.review.receipts.outcomes import classify_outcome

    gold.require(bool(score["reason"].strip()) and bool(score["calls"]), "original50_per_card_sources_missing")
    for reference in score["calls"]:
        call = calls.get((reference["conversation_id"], reference["step_index"]), {})
        parameters = call.get("parameters", {})
        tool = parameters.get("ToolName")
        allowed = {"query_sum20", "query_ulif_records", "search_slovnyk_me"}
        if facet == "stress":
            allowed.add("verify_stress")
        arguments = parameters.get("Arguments")
        arguments = json.loads(arguments) if isinstance(arguments, str) else arguments
        body = call.get("output")
        subjects = [arguments.get(k) for k in ("word", "lemma", "query")] if isinstance(arguments, dict) else []
        words = arguments.get("words") if isinstance(arguments, dict) else None
        subjects.extend(words if isinstance(words, list) else [words])
        gold.require(tool in allowed and isinstance(arguments, dict)
                     and lemma in subjects
                     and isinstance(body, str) and bool(body.strip()) and not call.get("output_missing")
                     and _SAVED_OUTPUT_POINTER_RE.search(body) is None,
                     "original50_per_card_sources_missing")
        outcome = classify_outcome(tool, "ok", body)
        start, end = reference["span"]
        gold.require(outcome["status"] == "hits_found" and outcome["hits"] > 0
                     and 0 <= start < end <= len(body) and body[start:end] == reference["quote"],
                     "original50_source_quote_unsupported")


def _verify_native50(inspection: dict, packet: dict, spec: dict, base: Path,
                     authority: CertificationAuthority) -> list[dict]:
    """Replay real task custody and per-card Sources evidence; write no authority."""
    from scripts.dispatcher.providers import agy
    from scripts.review import record_cf_verdict as reviews

    scope = _native50_scope(inspection, packet, spec)
    primary = reviews._review_repository_root("learn-ukrainian/learn-ukrainian.github.io", PROJECT_ROOT)
    task_root = primary / "batch_state/tasks"
    authors = inspection["authors"]
    gold.require(len({a["task_id"] for a in authors}) == len(authors), "original50_duplicate_authors")
    author_tasks = [_native_task(author, task_root)[0] for author in authors]
    freezer, producer = inspection["freezer"], inspection["producer"]
    _native50_freezer(freezer, authors, producer, base)
    if freezer["task"] is not None:
        _native_task(freezer["task"], task_root)
        gold.require((freezer["identity"], freezer["model"]) ==
                     (freezer["task"]["task_id"], freezer["task"]["model"]), "original50_freezer_identity_mismatch")
    identities = {a["task_id"] for a in authors} | {producer["task_id"]}
    identities.update(t["task_identity"]["task_id"] for t in author_tasks
                      if isinstance(t.get("task_identity"), dict) and t["task_identity"].get("task_id"))
    gold.require(freezer["identity"].removeprefix("session:") not in
                 {identity.removeprefix("session:") for identity in identities}, "original50_freezer_not_independent")
    task, reply = _native_task(producer, task_root, qualified_reviewer=True)
    gold.require(task.get("agent") == "agy" and producer["family"] == "google"
                 and producer["family"] not in {a["family"] for a in authors}
                 and producer["task_id"] not in {a["task_id"] for a in authors}
                 and reviews.is_ukrainian_review(task)
                 and task.get("resolved_model_known") is True
                 and task.get("resolved_model_source") == agy.MODEL_SOURCE
                 and task.get("resolved_model") == producer["model"], "original50_untrusted_producer")
    transcript = gold.reference(inspection["transcript"], base)
    log = reviews._hot_or_archived(task_root, "logs/" + producer["task_id"] + ".stdout.log")
    gold.require(transcript == log.read_bytes(), "original50_transcript_not_runner_bound")
    result = gold.reference(inspection["result"], base)
    gold.require(gold.sha(result) == task["result_sha256"] and gold.decode(result) == json.loads(reply),
                 "original50_result_not_task_bound")
    parsed = agy.parse(transcript.decode("utf-8"), "", 0, None)
    gold.require(not parsed.error and parsed.text == reply and parsed.resolved_model == producer["model"]
                 and agy.identity_failure(task["model"], parsed.resolved_model) is None,
                 "original50_transcript_model_or_result_mismatch")
    calls: dict[tuple, dict] = {}
    for line in jsonl_lines(transcript.decode("utf-8")):
        if not line.strip():
            continue
        event = json.loads(line)
        key = agy._completed_sources_call(event)
        if key is not None:
            gold.require(key not in calls or calls[key] == event["step_update"]["tool_info"],
                         "original50_conflicting_sources_call")
            calls[key] = event["step_update"]["tool_info"]
    gold.require(task.get("sources_mcp_call_count") == parsed.sources_mcp_call_count == len(calls),
                 "original50_sources_capture_count_mismatch")
    judgments = gold.decode(result)
    gold.validate(judgments, NATIVE_JUDGMENTS, "native original50 judgments")
    expected = {row["card_id"]: row for row in packet["original50"]}
    gold.require(judgments["scope_sha256"] == scope and len(judgments["items"]) == 50
                 and len({r["card_id"] for r in judgments["items"]}) == 50
                 and {r["card_id"] for r in judgments["items"]} == set(expected), "original50_judgment_denominator")
    for row in judgments["items"]:
        card = expected[row["card_id"]]
        admission = authority.reviews.get(row["card_id"], {})
        gold.require(row["card_version"] == card["card_version"], "original50_judgment_version_changed")
        gold.require(admission.get("status") == "active" and admission.get("card_version") == row["card_version"]
                     and bool(admission.get("record")) and admission.get("original50_inspection") == spec["original50_receipt"]
                     and admission.get("original50_authors") == authors
                     and admission.get("original50_freezer") == freezer, "original50_not_steward_admitted")
        lemma = card["card"]["key_at_creation"]["spelling"]
        for facet in ("meaning", "stress"):
            _native50_sources(row[facet], facet, lemma, calls)
    return [{"id": a["task_id"], "family": a["family"]} for a in authors]
FINDING = gold.obj({"code": {"enum": ["invented_ukrainian", "wrong_identity", "material"]},
                    "owner": gold.TEXT, "dependency": gold.TEXT, "evidence": gold.REF})
SCORE = gold.obj({"facet": {"enum": list(FACETS)}, "verdict": {"enum": ["pass", "fail"]},
                  "reason": gold.TEXT, "source_claims_sha256": gold.SHA,
                  "findings": gold.array(FINDING, 0)})
ASSESSMENTS = gold.obj({
    "schema_version": {"const": "word-card-language-evaluation.v1"},
    "spec_sha256": gold.SHA,
    "reports": gold.array(gold.obj({"evaluator_id": gold.TEXT,
                                   "items": gold.array(gold.obj({
                                       "item_id": gold.TEXT, "card_sha256": gold.SHA,
                                       "inspected_complete_card": {"const": True},
                                       "scores": gold.array(SCORE, len(FACETS)),
                                   }))}), 2),
})


def frozen_artifact(authority: CertificationAuthority, cards: list[dict]) -> dict:
    """Bind code, parser, rules, and every declared live input, without approval."""
    for card in cards:
        gold.require(authority.validator.is_valid(card), "Invalid evaluated card schema")
        gold.require(card["build"]["card_version"] ==
                     "cv_" + digest({key: value for key, value in card.items() if key != "build"})[:24],
                     "Invalid evaluated card version")
        inputs = card["build"]["inputs"]
        for category in ("S", "V", "I", "O"):
            gold.require(bool(inputs.get(category)), "Missing evaluated input snapshot")
            for name, snapshot in inputs[category].items():
                gold.require(snapshot["content_sha256"] == authority.snapshot(category, name),
                             "Evaluated source snapshot changed")
        gold.require("vesum" in inputs["V"] and {"overlay", "suppressions"} <= inputs["O"].keys(),
                     "Missing evaluated source authority")
        gold.require(inputs["R"]["register"]["content_sha256"] == authority.register
                     and inputs["R"]["rules"]["version"] == card["build"]["rules_version"] == "rules-v1"
                     and inputs["R"]["normaliser"]["version"] == "norm-v1", "Stale evaluated rules")
    return {"implementation_sha256": authority.implementation, "rules_sha256": authority.rules,
            "inputs_sha256": digest({card["card_id"]: card["build"]["inputs"] for card in cards})}


def evaluate_a1_assertions(assembly: dict, sources: dict, batch_name: str) -> dict:
    """Replay the real A1 consumer on its unchanged, repository-pinned batch.

    This is assertion evidence only. It grants no review, audit or export approval.
    """
    from scripts.atlas import a1_slice3_inputs, a1_slice4_inputs, a1_slice5_inputs, a1_slice6_inputs
    from scripts.atlas import a1_word_cards as a1
    from scripts.atlas import word_card_foundation as foundation

    if batch_name == "slice2":
        manifest = a1.load(a1.ROOT / a1.MANIFEST)
        gold.require(a1.digest(manifest) == a1.MANIFEST_SHA256, "Reviewed manifest changed")
        inventory = a1.load(a1.ROOT / "registry/atlas/a1-v1-inventory.json")
        base = a1.load(a1.ROOT / "registry/atlas/identity/registry.json")
        companion = a1.load(a1.ROOT / a1.COMPANION)
        batch = None
        validate = a1._inputs
    else:
        gold.require(batch_name in {"slice3", "slice4", "slice5", "slice6"}, "Unknown A1 batch")
        reader = {"slice3": a1_slice3_inputs, "slice4": a1_slice4_inputs,
                  "slice5": a1_slice5_inputs, "slice6": a1_slice6_inputs}[batch_name]
        manifest, inventory, base, companion, batch = reader.load_batch(a1.ROOT)
        validate = batch.validate_inputs
    effective, _ = validate(inventory, base, companion, manifest, sources, manifest["allocation_pins"])
    foundation.registry_check(effective)
    register = foundation.load_register(PERMISSIONS_REGISTER_PATH)
    rebuilt = a1.build(inventory, base, companion, manifest, sources, manifest["allocation_pins"], register, batch=batch)
    gold.require(a1.canonical(assembly) == a1.canonical(rebuilt), "Delivered A1 artifact changed")
    # verify calls check_assertion for every assertion, including context fields.
    result: dict = a1.verify(assembly, sources, manifest, batch=batch, register=register, inventory=inventory)
    result["inputs_sha256"] = digest({"assembly": assembly, "sources": sources, "manifest": manifest})
    return result


def _evaluate_code_first(spec_path: Path, spec_sha256: str, spec: dict) -> dict:
    from scripts.atlas import word_card_assertion_check as assertion_check

    gold.validate(spec, CODE_FIRST_SPEC, "code-first certification specification")
    base = spec_path.parent
    state = _AUTHORITY.get()
    authority = state.get("authority") if state is not None else None
    if authority is None:
        authority = CertificationAuthority()
    decisions, cards, inputs, batches = [], [], {}, []
    for row in spec["batches"]:
        gold.require(row["batch"] not in inputs, "Duplicate A1 batch")
        assembly = gold.decode(gold.reference(row["assembly"], base))
        sources = gold.decode(gold.reference(row["sources"], base))
        result = evaluate_a1_assertions(assembly, sources, row["batch"])
        decisions.extend(result["assertion_decisions"])
        cards.extend(assembly["cards"])
        inputs[row["batch"]] = result["inputs_sha256"]
        batches.append((assembly, sources))
    gold.require(len({card["card_id"] for card in cards}) == len(cards), "Duplicate code-first card")
    gold.require(len({d["assertion_id"] for d in decisions}) == len(decisions), "Duplicate code-first assertion")
    frozen = {"implementation_sha256": authority.implementation, "rules_sha256": authority.rules,
              "inputs_sha256": digest(inputs)}
    gold.require(spec["frozen"] == frozen, "Frozen code-first artifact changed")
    counts = assertion_check.summarize(decisions)
    holds = []
    # The existing steward ledger remains current-input authority. Names are
    # batch-qualified because A1 uses the same input names across its slices.
    for row, (assembly, _) in zip(spec["batches"], batches, strict=True):
        for category in ("S", "V", "I", "O"):
            for name, binding in assembly["cards"][0]["build"]["inputs"][category].items():
                identity = row["batch"] + ":" + name
                try:
                    current = authority.snapshot(category, identity)
                except (OSError, ValueError, KeyError, TypeError):
                    holds.append("current_input_authority_missing:" + category + ":" + identity)
                    continue
                if binding["content_sha256"] != current:
                    holds.append("current_input_changed:" + category + ":" + identity)
    if spec["removal_snapshots"] is None:
        holds.append("current_removal_authority_missing")
    else:
        for name, expected in spec["removal_snapshots"].items():
            if expected != authority.snapshot("O", name):
                holds.append("current_removal_snapshot_changed:" + name)
    if any(d["status"] != "supported" and d["reason"] != "context_selection_requires_judgment" for d in decisions):
        holds.append("unsupported_assertions_cannot_be_certified")
    from scripts.atlas import word_card_foundation as foundation
    from scripts.atlas import word_card_human_audit as human

    packet = human.make_packet(cards, decisions, batches, foundation.load_register(PERMISSIONS_REGISTER_PATH), frozen,
        gold.decode(gold.reference(spec["original50_selection"], base)),
        gold.decode(gold.reference(spec["original50_input"], base)))
    audit = human.audit_status(packet, authority.ledger)
    if audit != "HUMAN_AUDIT_ACCEPTED":
        holds.append(audit)
    if any(not row["current_version_matches"] or any(a["missing"] for a in row["assertions"])
           for row in packet["original50"]):
        holds.append("original50_source_or_version_unresolved")
    for name in ("original50_receipt", "complete_data_receipt", "mechanics_receipt"):
        if spec[name] is None:
            holds.append("missing_" + name)
    native_authors = []
    original50_refusal = None
    if spec["original50_receipt"] is not None:
        from scripts.review.record_cf_verdict import RecordError

        try:
            original = gold.decode(gold.reference(spec["original50_receipt"], base))
            native_authors = _verify_native50(original, packet, spec,
                (base / spec["original50_receipt"]["path"]).parent, authority)
        except (OSError, ValueError, TypeError, KeyError, RecordError) as exc:
            holds.append("original50_refused:" + type(exc).__name__)
            original50_refusal = {"type": type(exc).__name__, "detail": str(exc)}
    for name in ("complete_data_receipt", "mechanics_receipt"):
        if spec[name] is not None:
            for card in cards:
                row = authority.reviews.get(card["card_id"], {})
                prerequisites = row.get("code_first_prerequisites", {})
                if (row.get("status") != "active" or not row.get("record")
                        or row.get("card_version") != card["build"]["card_version"]
                        or prerequisites.get("frozen") != frozen or prerequisites.get(name) != spec[name]):
                    holds.append(name + "_not_steward_admitted")
                    break
    if spec["mechanics_receipt"] is not None:
        mechanics = gold.decode(gold.reference(spec["mechanics_receipt"], base))
        gold.validate(mechanics, MECHANICS, "accepted code-first mechanics")
        gold.require(mechanics["frozen"] == frozen and mechanics["cards_sha256"] == digest(cards),
                     "Mechanics binds another code-first artifact")
        if not native_authors:
            holds.append("mechanics_independent_acceptance_unbound")
        else:
            gold.require(all(mechanics["accepted_by"]["id"] != author["id"]
                             and mechanics["accepted_by"]["family"] != author["family"]
                             for author in [spec["author"], *native_authors]), "Self-accepted mechanics")
        for ref in mechanics["evidence"]:
            gold.reference(ref, (base / spec["mechanics_receipt"]["path"]).parent)
    if spec["complete_data_receipt"] is not None:
        data = gold.decode(gold.reference(spec["complete_data_receipt"], base))
        gold.validate(data, CODE_FIRST_DATA, "code-first complete-data replay")
        gold.complete_data(data, (base / spec["complete_data_receipt"]["path"]).parent)
    return {"schema_version": "word-card-certification-receipt.v2",
            "status": "HELD" if holds else "CERTIFIED",
            "spec": {"path": spec_path.name, "sha256": spec_sha256}, "frozen": frozen,
            "case_count": len(cards), "assertion_counts": counts, "assertion_decisions": decisions,
            "human_packet": packet, "human_audit_status": audit,
            "original50_refusal": original50_refusal,
            "holds": holds, "cards": {card["card_id"]: digest(card) for card in cards}}


def evaluate_certification(spec_path: Path, spec_sha256: str,
                           evaluation_path: Path | None, evaluation_sha256: str | None) -> dict:
    """Replay pinned prerequisites and return a deterministic private exact-artifact receipt.

    Trusted pins must come from the independent steward, never from the author.
    This checks evidence and literal projections; language judgments remain external.
    Retain the returned receipt beside the specification; its references are relative
    to that directory.
    No files, approvals, release state, or review ledger entries are written.
    """
    _, spec = gold.read(spec_path, spec_sha256)
    if spec.get("schema_version") == "word-card-certification-spec.v2":
        gold.require(evaluation_path is None and evaluation_sha256 is None,
                     "Code-first evidence cannot consume a sample pass")
        return _evaluate_code_first(spec_path, spec_sha256, spec)
    if evaluation_path is None or evaluation_sha256 is None:
        raise ValueError("Legacy certification requires a pinned evaluation")
    gold.validate(spec, CERTIFICATION_SPEC, "certification specification")
    base = spec_path.parent
    gold_path = base / spec["gold_spec"]["path"]
    gold_spec_sha = spec["gold_spec"]["sha256"]
    seal_path = base / spec["gold_seal"]["path"]
    seal_raw = gold.reference(spec["gold_seal"], base)
    gold.require(seal_path.name == "seal.json", "Invalid sealed gold path")
    verified = gold.verify(gold_path, gold_spec_sha, seal_path.parent,
                           base / spec["isolation"]["path"], spec["isolation"]["sha256"])
    gold.require(verified["seal_sha256"] == gold.sha(seal_raw), "Gold seal changed during verification")
    _, source_spec = gold.read(gold_path, gold_spec_sha)
    gold.require(spec["complete_data_receipt"]["sha256"] ==
                 source_spec["inputs"]["complete_data_receipt"]["sha256"], "Different complete-data receipt")
    gold.reference(spec["complete_data_receipt"], base)
    gold.require(spec["frozen"]["implementation_sha256"] == source_spec["assembler_build_sha256"],
                 "Gold custody binds another implementation")
    _, membership = gold.read(seal_path.parent / "membership.json")
    _, answers = gold.read(seal_path.parent / "answers.json")
    gold.require([row["case_id"] for row in spec["cases"]] == [row["case_id"] for row in membership["cases"]],
                 "Reduced, duplicated or reordered gold denominator")
    cards = [gold.decode(gold.reference(row["card"], base)) for row in spec["cases"]]
    gold.require(len({card["card_id"] for card in cards}) == len(cards), "Duplicate evaluated card identity")
    state = _AUTHORITY.get()
    authority = state.get("authority") if state is not None else None
    if authority is None:
        authority = CertificationAuthority()
    gold.require(spec["frozen"] == frozen_artifact(authority, cards), "Frozen artifact changed")
    mechanics_path = base / spec["mechanics_receipt"]["path"]
    mechanics = gold.decode(gold.reference(spec["mechanics_receipt"], base))
    gold.validate(mechanics, MECHANICS, "accepted mechanics receipt")
    gold.require(mechanics["frozen"] == spec["frozen"]
                 and mechanics["cards_sha256"] == digest(cards), "Mechanics binds another artifact")
    authors = [spec["author"], source_spec["roles"]["assembler"]]
    gold.require(all(mechanics["accepted_by"]["id"] != actor["id"]
                     and mechanics["accepted_by"]["family"] != actor["family"] for actor in authors),
                 "Self-accepted mechanics")
    for ref in mechanics["evidence"]:
        gold.reference(ref, mechanics_path.parent)
    evaluators = spec["evaluators"]
    gold.require(len({actor["id"] for actor in evaluators}) == len(evaluators)
                 and len({actor["family"] for actor in evaluators}) >= 2, "Duplicate or same-family evaluators")
    for actor in evaluators:
        gold.require(all(actor["id"] != author["id"] and actor["family"] != author["family"] for author in authors),
                     "Self-certification refused")
        gold.reference(actor["qualification"], base)
    gold.require(set(row["class"] for row in spec["controls"]) == set(CONTROL_FACETS),
                 "Missing planted control class")
    case_cards = {row["case_id"]: card for row, card in zip(spec["cases"], cards, strict=True)}
    expectations = {row["case_id"]: {item["field"]: item for item in row["expectations"]}
                    for row in answers["cases"]}
    gold.require(len({row["gold_field"] for row in spec["projections"].values()}) == len(FACETS)
                 and len({row["card_pointer"] for row in spec["projections"].values()}) == len(FACETS),
                 "Facets must have distinct gold fields and card projections")
    gold.require({row["gold_field"] for row in spec["projections"].values()} == set(source_spec["required_fields"]),
                 "Unscored sealed gold fields")
    items = {key: (key, card, None) for key, card in case_cards.items()}
    for control in spec["controls"]:
        key, case_id = control["control_id"], control["case_id"]
        gold.require(key not in items and case_id in case_cards, "Duplicate or unknown control identity")
        card = gold.decode(gold.reference(control["card"], base))
        gold.require(authority.validator.is_valid(card), "Invalid control card schema")
        facet = CONTROL_FACETS[control["class"]]
        pointer = spec["projections"][facet]["card_pointer"]
        original = case_cards[case_id]
        gold.require(gold.canonical(card) != gold.canonical(original)
                     and card["card_id"] == original["card_id"], "Unchanged or foreign control")
        # A control replaces exactly one frozen facet projection, never unrelated card data.
        clone = json.loads(json.dumps(original))
        parent_pointer, _, leaf = pointer.rpartition("/")
        parent = gold.pointer_value(clone, parent_pointer) if parent_pointer else clone
        leaf = leaf.replace("~1", "/").replace("~0", "~")
        value = gold.pointer_value(card, pointer)
        if isinstance(parent, list):
            parent[int(leaf)] = value
        else:
            parent[leaf] = value
        gold.require(gold.canonical(clone) == gold.canonical(card)
                     and gold.canonical(gold.pointer_value(original, pointer)) != gold.canonical(value),
                     "Control must alter only its target facet")
        items[key] = (case_id, card, control["class"])
    _, assessment = gold.read(evaluation_path, evaluation_sha256)
    gold.validate(assessment, ASSESSMENTS, "independent language evaluation")
    gold.require(assessment["spec_sha256"] == spec_sha256, "Evaluation belongs to another frozen specification")
    gold.require(sorted(row["evaluator_id"] for row in assessment["reports"]) ==
                 sorted(actor["id"] for actor in evaluators), "Incomplete or duplicate evaluator coverage")
    scores = {facet: {"passed": 0, "denominator": len(cards) * len(evaluators)} for facet in FACETS}
    controls = {name: {"detected": 0, "denominator": sum(row["class"] == name for row in spec["controls"])
                       * len(evaluators)} for name in CONTROL_FACETS}
    findings = []
    for report in assessment["reports"]:
        gold.require(sorted(row["item_id"] for row in report["items"]) == sorted(items),
                     "Reduced or duplicate evaluation denominator")
        for row in report["items"]:
            key = row["item_id"]
            case_id, card, control_class = items[key]
            gold.require(row["card_sha256"] == digest(card), "Evaluation binds another card")
            gold.require(sorted(score["facet"] for score in row["scores"]) == sorted(FACETS),
                         "Missing or duplicate semantic facet")
            failed_facets = set()
            for score in row["scores"]:
                facet = score["facet"]
                projection = spec["projections"][facet]
                expected = expectations[case_id][projection["gold_field"]]
                gold.require(score["source_claims_sha256"] == digest(expected), "Unbound source inspection")
                observed = gold.pointer_value(card, projection["card_pointer"])
                wanted = expected["claims"][0]["value"] if expected["state"] == "value" else None
                literal_pass = gold.canonical(observed) == gold.canonical(wanted)
                passed = score["verdict"] == "pass" and not score["findings"] and literal_pass
                gold.require(score["verdict"] != "fail" or bool(score["findings"]),
                             "Failed criterion requires source-gap or repair owner")
                gold.require(not score["findings"] or score["verdict"] == "fail", "Hidden material finding")
                for finding in score["findings"]:
                    gold.reference(finding["evidence"], evaluation_path.parent)
                if not passed:
                    failed_facets.add(facet)
                    if control_class is None or facet != CONTROL_FACETS[control_class]:
                        findings.append({"item_id": key, "evaluator_id": report["evaluator_id"], "facet": facet,
                                         "findings": score["findings"] or [{"code": "material", "owner": "open-model-data",
                                                                             "dependency": "repair literal source mismatch"}]})
                if control_class is None:
                    scores[facet]["passed"] += int(passed)
            if control_class is not None:
                target = CONTROL_FACETS[control_class]
                target_score = next(score for score in row["scores"] if score["facet"] == target)
                detected = target in failed_facets and target_score["verdict"] == "fail"
                controls[control_class]["detected"] += int(detected)
                if not detected:
                    findings.append({"item_id": key, "evaluator_id": report["evaluator_id"], "facet": target,
                                     "findings": [{"code": "material", "owner": report["evaluator_id"],
                                                   "dependency": "repair missed planted control"}]})
    status = "CERTIFIED" if not findings else "FAILED"
    return {"schema_version": "word-card-certification-receipt.v1", "status": status,
            "spec": {"path": spec_path.name, "sha256": spec_sha256},
            "evaluation": {"path": Path(os.path.relpath(evaluation_path, base)).as_posix(),
                           "sha256": evaluation_sha256},
            "frozen": spec["frozen"], "gold_seal_sha256": verified["seal_sha256"],
            "case_count": len(cards), "strata": source_spec["strata"],
            "evaluators": evaluators, "scores": scores, "controls": controls, "findings": findings,
            "cards": {card["card_id"]: digest(card) for card in cards}}


def _read_certification_receipt(ref: dict, base: Path) -> tuple[dict, Path]:
    """Validate the receipt envelope before dereferencing or replaying its evidence."""
    legacy_shape = gold.obj({
        "schema_version": {"const": "word-card-certification-receipt.v1"},
        "spec": gold.REF, "evaluation": gold.REF,
        **{key: {} for key in ("status", "frozen", "gold_seal_sha256", "case_count", "strata",
                              "evaluators", "scores", "controls", "findings", "cards")},
    })
    try:
        receipt = gold.decode(gold.reference(ref, base))
        code_first_shape = gold.obj({
            "schema_version": {"const": "word-card-certification-receipt.v2"}, "spec": gold.REF,
            **{key: {} for key in ("status", "frozen", "case_count", "assertion_counts",
                                  "assertion_decisions", "human_packet", "human_audit_status", "holds", "cards",
                                  "original50_refusal")},
        })
        gold.validate(receipt, {"oneOf": [legacy_shape, code_first_shape]}, "exact-artifact receipt")
    except (OSError, ValueError, TypeError) as exc:
        raise UncertifiedCardRefusal("Invalid exact-artifact receipt") from exc
    return receipt, (base / ref["path"]).parent


def verify_certification_receipt(ref: dict, base: Path) -> dict:
    """Replay a pinned receipt against current evidence; a copied CERTIFIED is insufficient."""
    receipt, base = _read_certification_receipt(ref, base)
    spec, evaluation = receipt["spec"], receipt.get("evaluation")
    replay = evaluate_certification(base / spec["path"], spec["sha256"],
                                    base / evaluation["path"] if evaluation else None,
                                    evaluation["sha256"] if evaluation else None)
    if gold.canonical(replay) != gold.canonical(receipt) or replay["status"] != "CERTIFIED":
        raise UncertifiedCardRefusal("Failed or stale certification receipt")
    return receipt


def certification_summary(ref: dict, base: Path) -> dict:
    """Return aggregate evaluation evidence without protected IDs, paths, or source text."""
    receipt, base = _read_certification_receipt(ref, base)
    # Failed evaluations remain publishable as failed, but their evidence must replay too.
    spec, evaluation = receipt["spec"], receipt.get("evaluation")
    replay = evaluate_certification(base / spec["path"], spec["sha256"],
                                    base / evaluation["path"] if evaluation else None,
                                    evaluation["sha256"] if evaluation else None)
    if gold.canonical(replay) != gold.canonical(receipt):
        raise UncertifiedCardRefusal("Stale evaluation summary")
    if receipt["schema_version"] == "word-card-certification-receipt.v2":
        return {"schema_version": "word-card-certification-summary.v2", "status": receipt["status"],
                "receipt_sha256": ref["sha256"], "case_count": receipt["case_count"],
                "assertion_counts": receipt["assertion_counts"], "holds": receipt["holds"],
                "human_audit_status": receipt["human_audit_status"]}
    codes: dict[str, int] = {}
    for row in receipt["findings"]:
        for finding in row["findings"]:
            codes[finding["code"]] = codes.get(finding["code"], 0) + 1
    return {"schema_version": "word-card-certification-summary.v1", "status": receipt["status"],
            "receipt_sha256": ref["sha256"], "case_count": receipt["case_count"],
            "evaluator_count": len(receipt["evaluators"]), "scores": receipt["scores"],
            "controls": receipt["controls"], "finding_count": len(receipt["findings"]), "finding_codes": codes}
