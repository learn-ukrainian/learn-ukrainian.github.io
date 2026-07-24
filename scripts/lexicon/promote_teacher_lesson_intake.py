#!/usr/bin/env python3
"""Promote reviewed private teacher-lesson intake into the Word Atlas.

The reviewed full-document ledger contains privacy-safe decision metadata but
its source inventory is deliberately local-only.  This command derives an
ephemeral candidate payload and matching ephemeral decisions from that ledger,
plus the committed curated-headword inventory.  It never writes a raw source
path, document name, or personal name into a public Atlas entry.

Single-token source forms are collapsed to an unambiguous VESUM base lemma;
multi-word expressions remain intact.  Learner-English anchors prefer the
curated vocabulary table, the hydrated Atlas, Kaikki, Dmklinger, and the
cached slovnyk UK→EN dictionary in that order.  A Ukrainian source surface is
never used as an English gloss.

Run from the repository root after building an explicit VESUM shadow database::

    .venv/bin/python -m scripts.lexicon.promote_teacher_lesson_intake \
      --vesum-db /tmp/vesum-shadow.db --apply --write --report
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import uuid
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import apply_source_inventory_promotion as apply
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.lexicon import enrich_manifest as enrich_module
from scripts.lexicon import verify_manifest

DEFAULT_INTAKE_DIR = PROJECT_ROOT / "data" / "lexicon" / "intake"
DEFAULT_JOURNAL = DEFAULT_INTAKE_DIR / "private_teacher_lesson_intake_journal.json"
DEFAULT_LOCK = DEFAULT_INTAKE_DIR / "promotion.lock"
STAGED_MANIFEST = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.staged.json"
STAGED_FINGERPRINT = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.staged.fingerprint.json"


def _atomic_write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = path.parent
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
        tf.write(content)
        tf.flush()
        os.fsync(tf.fileno())
        temp_name = tf.name
    os.replace(temp_name, path)


def _atomic_write_json(path: Path, data: Any) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    _atomic_write_file(path, content)


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()
from scripts.audit.source_inventory_intake import read_source_inventory, source_inventory_candidates
from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.enrich_manifest import (
    _dmklinger_key,
    _kaikki_translation,
    _load_kaikki_lookup,
    _load_slovnyk_cache_file,
    _parse_translations,
    _slovnyk_cache_path,
    _slovnyk_ukreng_translation,
)
from scripts.lexicon.grow_lexicon_from_content import build_payload, build_skeleton_entry, write_candidates
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_words

DEFAULT_FULL_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/2026-07-23-alona-full-document-intake.yaml"
)
DEFAULT_CURATED_INVENTORY = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-2026-07-18-bulk.yaml"
)
DEFAULT_MANIFEST = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
DEFAULT_FINGERPRINT = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"
DEFAULT_CANDIDATES = Path("/tmp/atlas-private-teacher-lesson-candidates.json")
DEFAULT_DECISIONS = Path("/tmp/atlas-private-teacher-lesson-decisions.yaml")
DEFAULT_PLAN = Path("/tmp/atlas-private-teacher-lesson-plan.json")

# The ledger's original inventory path contains the private contributor's name.
# Public entries retain the source family and a generic, reproducible intake id,
# but must never expose that name in an Atlas payload.
PUBLIC_INVENTORY_PATH = "data/lexicon/source-inventory/oneshot/private-teacher-lesson-intake.yaml"
PUBLIC_SOURCE_ID = "private_teacher_lesson"
PUBLIC_SOURCE_TITLE = "Curated private teacher lesson intake"
PUBLIC_EXTRACTION_MODE = "reviewed_teacher_lesson_intake"

_POS_MAP = {
    "adj": "adjective",
    "adjective": "adjective",
    "adv": "adverb",
    "adverb": "adverb",
    "verb": "verb",
    "noun": "noun",
    "prep": "preposition",
    "preposition": "preposition",
    "conj": "conjunction",
    "numr": "numeral",
    "numeral": "numeral",
    "pron": "pronoun",
    "pronoun": "pronoun",
    "part": "particle",
    "intj": "interjection",
    "abbr": "abbreviation",
}
_UKRAINIAN_LETTERS = frozenset("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя")


@dataclass(frozen=True)
class IntakeRow:
    """One reviewed source row, reduced to public-safe promotion fields."""

    lemma: str
    pos: str
    gloss: str | None
    locator: str
    source_kind: str


def _normalise(text: object) -> str:
    value = strip_acute_stress(str(text or ""))
    value = value.replace("ʼ", "'").replace("’", "'").replace("`", "'")
    return " ".join(value.split()).casefold()


def _is_expression(lemma: str) -> bool:
    return " " in lemma


def _is_english(text: str | None) -> bool:
    if not text:
        return False
    normalised = " ".join(text.split()).casefold()
    if "gloss pending" in normalised or "teacher-lesson headword" in normalised:
        return False
    letters = {char.casefold() for char in normalised if char.isalpha()}
    has_latin = any("a" <= char <= "z" for char in letters)
    has_ukrainian = bool(letters & _UKRAINIAN_LETTERS)
    return has_latin and not has_ukrainian


def _mapped_pos(raw: object) -> str | None:
    text = str(raw or "").strip().casefold()
    return _POS_MAP.get(text)


def _fallback_pos(lemma: str, gloss: str | None) -> str:
    if _is_expression(lemma):
        return "phrase"
    if (gloss or "").casefold().startswith("to ") or lemma.endswith(("ти", "тися")):
        return "verb"
    return "noun"


def _read_full_rows(path: Path) -> list[IntakeRow]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or not isinstance(payload.get("decisions"), list):
        raise ValueError(f"{path}: expected a decision ledger with decisions")
    rows: list[IntakeRow] = []
    for row in payload["decisions"]:
        if not isinstance(row, Mapping) or row.get("decision") != "approve_for_publish":
            continue
        source = row.get("source_inventory")
        if not isinstance(source, Mapping):
            raise ValueError(f"{path}: approved decision lacks source_inventory")
        lemma = _normalise(row.get("lemma"))
        locator = str(source.get("locator") or "").strip()
        if not lemma or not locator:
            raise ValueError(f"{path}: approved decision lacks lemma or locator")
        approved_gloss = str(row.get("approved_gloss") or "").strip()
        rows.append(
            IntakeRow(
                lemma=lemma,
                pos=str(row.get("approved_pos") or "").strip(),
                gloss=approved_gloss if _is_english(approved_gloss) else None,
                locator=locator,
                source_kind="full_document",
            )
        )
    return rows


def _read_curated_rows(path: Path) -> list[IntakeRow]:
    rows: list[IntakeRow] = []
    for item in source_inventory_candidates(read_source_inventory(path, project_root=PROJECT_ROOT)):
        for provenance in item.source_provenance:
            locator = str(provenance.get("source_locator") or "").strip()
            if not locator:
                raise ValueError(f"{path}: curated inventory entry lacks source locator")
            rows.append(
                IntakeRow(
                    lemma=_normalise(item.lemma),
                    pos=str(item.pos or "").strip(),
                    gloss=str(item.gloss or "").strip() or None,
                    locator=locator,
                    source_kind="curated_headword",
                )
            )
    return rows


def _vesum_analyses(lemmas: Iterable[str], vesum_db: Path) -> dict[str, list[dict[str, Any]]]:
    singles = sorted({lemma for lemma in lemmas if lemma and not _is_expression(lemma)})
    analyses: dict[str, list[dict[str, Any]]] = {}
    for start in range(0, len(singles), 500):
        batch = singles[start : start + 500]
        analyses.update(verify_words(batch, db_path=vesum_db))
    return analyses


def _canonical_lemma(lemma: str, analyses: Sequence[Mapping[str, Any]]) -> str:
    """Use a VESUM base only when its lexical identity is unambiguous."""
    if _is_expression(lemma):
        return lemma
    bases = {_normalise(row.get("lemma")) for row in analyses if _normalise(row.get("lemma"))}
    return next(iter(bases)) if len(bases) == 1 else lemma


def _vesum_pos(analyses: Sequence[Mapping[str, Any]]) -> str | None:
    mapped = sorted({_mapped_pos(row.get("pos")) for row in analyses if _mapped_pos(row.get("pos"))})
    return mapped[0] if len(mapped) == 1 else None


def _manifest_glosses(path: Path) -> dict[str, str]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = manifest.get("entries") if isinstance(manifest, Mapping) else None
    if not isinstance(entries, list):
        raise ValueError(f"{path}: manifest entries must be a list")
    result: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        gloss = str(entry.get("gloss") or "").strip()
        if gloss and _is_english(gloss):
            result.setdefault(_lemma_key(str(entry.get("lemma") or "")), gloss)
    return result


def _dmklinger_glosses(lemmas: Iterable[str], sources_db: Path | None) -> tuple[dict[str, str], set[str]]:
    """Return local Dmklinger English anchors and SUM-11 attestations.

    Dmklinger is intentionally indexed in-process: the source table contains
    only about 30k rows, whereas normalised lookups must serve thousands of
    VESUM-resolved lemmas.  SUM-11 is Ukrainian-only, so it supplies
    dictionary-attestation evidence for enrichment but never masquerades as an
    English learner gloss.
    """
    if sources_db is None or not sources_db.is_file():
        return {}, set()
    wanted = {_dmklinger_key(lemma): _lemma_key(lemma) for lemma in lemmas if not _is_expression(lemma)}
    if not wanted:
        return {}, set()
    anchors: dict[str, str] = {}
    sum11_attested: set[str] = set()
    with sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True) as conn:
        for word, translations in conn.execute("SELECT word, translations FROM dmklinger_uk_en"):
            key = _dmklinger_key(str(word or ""))
            target = wanted.get(key)
            if not target or target in anchors:
                continue
            terms = _parse_translations(translations)
            if terms and _is_english(terms[0]):
                anchors[target] = terms[0]
        wanted_words = sorted({_normalise(lemma) for lemma in lemmas if not _is_expression(lemma)})
        for start in range(0, len(wanted_words), 500):
            batch = wanted_words[start : start + 500]
            placeholders = ",".join("?" for _ in batch)
            for (word,) in conn.execute(
                f"SELECT word FROM sum11 WHERE word IN ({placeholders}) COLLATE NOCASE", batch
            ):
                sum11_attested.add(_lemma_key(str(word)))
    return anchors, sum11_attested


def _dictionary_glosses(lemmas: Iterable[str], sources_db: Path | None) -> tuple[dict[str, str], set[str]]:
    """Read local Kaikki and slovnyk fallbacks without network requests.

    Dmklinger and SUM-11 are deliberately left to ``enrich_manifest`` when its
    local sources database is available.  This promoter has no sources-db
    dependency, so it remains runnable in a sparse checkout while still using
    the two file-backed dictionary fallbacks available here.
    """
    lemma_list = sorted(set(lemmas))
    dmklinger, sum11_attested = _dmklinger_glosses(lemma_list, sources_db)
    kaikki = _load_kaikki_lookup()
    result: dict[str, str] = {}
    for lemma in lemma_list:
        if _is_expression(lemma):
            continue
        key = _lemma_key(lemma)
        if dmklinger.get(key):
            result[key] = dmklinger[key]
            continue
        translation = _kaikki_translation(kaikki, lemma)
        terms = translation.get("en") if isinstance(translation, Mapping) else None
        if isinstance(terms, list) and terms and _is_english(str(terms[0])):
            result.setdefault(key, str(terms[0]).strip())
            continue
        cache = _load_slovnyk_cache_file(_slovnyk_cache_path(lemma))
        # ``_slovnyk_ukreng_translation`` populates a missing cache row.  This
        # bulk promoter must stay deterministic and bounded, so only consume an
        # already cached UK→EN response; enrich_manifest owns live lookups.
        lookups = cache.get("lookups") if isinstance(cache, Mapping) else None
        if not isinstance(lookups, Mapping) or "ukreng" not in lookups:
            continue
        translation = _slovnyk_ukreng_translation(lemma, cache)
        terms = translation.get("en") if isinstance(translation, Mapping) else None
        if isinstance(terms, list) and terms and _is_english(str(terms[0])):
            result.setdefault(key, str(terms[0]).strip())
    return result, sum11_attested


def _build_rows(
    full_decisions: Path,
    curated_inventory: Path,
    manifest: Path,
    vesum_db: Path,
    sources_db: Path | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    source_rows = [*_read_full_rows(full_decisions), *_read_curated_rows(curated_inventory)]
    analyses = _vesum_analyses((row.lemma for row in source_rows), vesum_db)
    canonical_rows: dict[str, list[IntakeRow]] = defaultdict(list)
    canonical_analyses: dict[str, list[dict[str, Any]]] = {}
    for row in source_rows:
        row_analyses = analyses.get(row.lemma, [])
        canonical = _canonical_lemma(row.lemma, row_analyses)
        canonical_rows[canonical].append(row)
        canonical_analyses.setdefault(canonical, row_analyses)

    manifest_glosses = _manifest_glosses(manifest)
    dictionary_glosses, sum11_attested = _dictionary_glosses(canonical_rows, sources_db)
    candidates: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    source_rows_collapsed = 0
    gloss_fallbacks = 0
    for lemma in sorted(canonical_rows, key=_lemma_key):
        rows = canonical_rows[lemma]
        source_rows_collapsed += len(rows) - 1
        first = rows[0]
        analyses_for_lemma = canonical_analyses.get(lemma, [])
        pos = "phrase" if _is_expression(lemma) else (_vesum_pos(analyses_for_lemma) or _fallback_pos(lemma, first.gloss))
        gloss = next((row.gloss for row in rows if _is_english(row.gloss)), None)
        if not gloss:
            key = _lemma_key(lemma)
            gloss = manifest_glosses.get(key) or dictionary_glosses.get(key)
            gloss_fallbacks += bool(gloss)
        if not gloss:
            # The reviewed ledger's Ukrainian echo is not a valid learner-English
            # anchor.  Retain the source in the candidates report but do not claim
            # an invented translation; enrichment can provide Dmklinger/SUM-11 when
            # the data-enabled pipeline is available.
            continue

        primary = first
        provenance = {
            "source_family": "teacher_lesson",
            "extraction_mode": PUBLIC_EXTRACTION_MODE,
            "inventory_path": PUBLIC_INVENTORY_PATH,
            "inventory_locator": primary.locator,
            "source_id": PUBLIC_SOURCE_ID,
            "source_title": PUBLIC_SOURCE_TITLE,
            "source_locator": primary.locator,
        }
        entry = build_skeleton_entry(lemma)
        entry.update(
            {
                "pos": pos,
                "gloss": gloss,
                "primary_source": "source_inventory_grow",
                "source_provenance": [provenance],
                "surface_admission": {"practice": True},
                "heritage_status": {
                    "classification": "unknown",
                    "attestations": [],
                    "is_russianism": False,
                    "russian_shadow": False,
                    "vesum_attested": bool(analyses_for_lemma) or _is_expression(lemma),
                    "calque_warning": None,
                    "warning_severity": "none",
                },
            }
        )
        candidates.append(entry)
        key = source_inventory_key(
            lemma=lemma,
            inventory_path=PUBLIC_INVENTORY_PATH,
            locator=primary.locator,
        )
        decisions.append(
            {
                "lemma": lemma,
                "decision": "approve_for_publish",
                "approved_pos": pos,
                "approved_gloss": gloss,
                "sense_note": "reviewed private teacher-lesson intake; public provenance redacted",
                "source_inventory": {
                    "key": key,
                    "path": PUBLIC_INVENTORY_PATH,
                    "locator": primary.locator,
                    "source_id": PUBLIC_SOURCE_ID,
                    "source_family": "teacher_lesson",
                },
                "evidence_refs": ["reviewed private teacher-lesson intake", "VESUM or curated English anchor"],
                "surface_admission": {"practice": True},
            }
        )
    report = {
        "source_rows": len(source_rows),
        "canonical_lemmas": len(canonical_rows),
        "collapsed_source_rows": source_rows_collapsed,
        "candidates_with_english_anchor": len(candidates),
        "held_without_english_anchor": len(canonical_rows) - len(candidates),
        "dictionary_or_manifest_gloss_fallbacks": gloss_fallbacks,
        "sum11_attested_canonical_lemmas": len(sum11_attested),
    }
    return candidates, decisions, report


def _write_decisions(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    payload = {
        "version": 1,
        "kind": "atlas_source_inventory_review_decisions",
        "batch_id": "private-teacher-lesson-promotion-2026-07-23",
        "batch_label": "private-teacher-lesson-practice-promotion",
        "reviewer": "operator-reviewed-teacher-lesson-intake",
        "reviewed_at": "2026-07-23",
        "source_queue": {
            "workflow": "source_inventory_publish_review_queue.v1",
            "total_queue_rows": len(rows),
            "approved_in_queue": len(rows),
            "promotion_batch_size": len(rows),
        },
        "production_outputs_updated": [],
        "decisions": list(rows),
    }
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")


def promote(
    *,
    full_decisions: Path,
    curated_inventory: Path,
    manifest: Path,
    fingerprint: Path,
    vesum_db: Path,
    sources_db: Path | None,
    candidates_out: Path,
    decisions_out: Path,
    write: bool,
    allow_held: bool = False,
) -> dict[str, Any]:
    candidates, decisions, report = _build_rows(
        full_decisions, curated_inventory, manifest, vesum_db, sources_db
    )
    payload = build_payload(
        total_delta=len(candidates),
        processed=len(candidates),
        auto_merge=candidates,
        needs_review=[],
        limit=None,
    )
    payload["generated_from"] = "promote_teacher_lesson_intake.v1"
    write_candidates(payload, candidates_out)
    _write_decisions(decisions, decisions_out)
    plan = planner.build_promotion_plan(
        candidates_path=candidates_out,
        decision_files=[decisions_out],
        manifest_path=manifest,
    )
    planner.write_plan(plan, DEFAULT_PLAN)
    if plan["counts"]["missing_candidates"]:
        raise RuntimeError(f"promotion plan has {plan['counts']['missing_candidates']} missing candidates")
    if write and report["held_without_english_anchor"] and not allow_held:
        raise RuntimeError(
            "refusing a partial teacher-lesson promotion: "
            f"{report['held_without_english_anchor']} canonical entries lack a learner-English anchor. "
            "Pass --allow-held to promote the ready candidates with English anchors while holding the rest."
        )
    result: dict[str, Any] = {"intake": report, "plan": plan["counts"], "wrote": False}
    if not write:
        return result

    DEFAULT_INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_LOCK, "w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            base_sha256 = _sha256_file(manifest)
            tx_id = str(uuid.uuid4())
            journal_record: dict[str, Any] = {
                "schema_version": "promotion-journal.v1",
                "tx_id": tx_id,
                "base_sha256": base_sha256,
                "phase": "PREPARED",
                "promoted_count": len(candidates),
            }
            _atomic_write_json(DEFAULT_JOURNAL, journal_record)

            # PHASE 1: STAGE MANIFEST
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            applied = apply.apply_promotion_plan(manifest_payload, plan, source_family="teacher_lesson")
            _atomic_write_json(STAGED_MANIFEST, manifest_payload)
            staged_sha256 = _sha256_file(STAGED_MANIFEST)
            journal_record.update({
                "phase": "MANIFEST_STAGED",
                "staged_sha256": staged_sha256,
                "promoted": applied["counts"]["promoted"],
            })
            _atomic_write_json(DEFAULT_JOURNAL, journal_record)

            # PHASE 2: ENRICH STAGED MANIFEST
            if applied["counts"]["promoted"]:
                enrich_module.enrich(manifest_path=STAGED_MANIFEST, fingerprint_path=STAGED_FINGERPRINT)
            enriched_sha256 = _sha256_file(STAGED_MANIFEST)
            journal_record.update({
                "phase": "ENRICHED",
                "enriched_sha256": enriched_sha256,
            })
            _atomic_write_json(DEFAULT_JOURNAL, journal_record)

            # PHASE 3: VERIFY STAGED MANIFEST
            verify_code = verify_manifest.main(["--manifest", str(STAGED_MANIFEST)])
            if verify_code != 0:
                raise RuntimeError(f"staged manifest failed verification with exit code {verify_code}")
            journal_record.update({
                "phase": "VERIFIED",
            })
            _atomic_write_json(DEFAULT_JOURNAL, journal_record)

            # PHASE 4: PUBLISH (Compare-And-Swap + Atomic Replace)
            current_sha256 = _sha256_file(manifest)
            if current_sha256 != base_sha256:
                raise RuntimeError("Production manifest mutated concurrently; aborting promotion CAS publish")
            os.replace(STAGED_MANIFEST, manifest)
            if STAGED_FINGERPRINT.is_file():
                os.replace(STAGED_FINGERPRINT, fingerprint)

            # PHASE 5: PUBLISHED
            journal_record.update({
                "phase": "PUBLISHED",
                "final_sha256": _sha256_file(manifest),
            })
            _atomic_write_json(DEFAULT_JOURNAL, journal_record)

            result.update({"applied": applied["counts"], "wrote": bool(applied["counts"]["promoted"]), "journal": journal_record})
            return result
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-decisions", type=Path, default=DEFAULT_FULL_DECISIONS)
    parser.add_argument("--curated-inventory", type=Path, default=DEFAULT_CURATED_INVENTORY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--vesum-db", type=Path, required=True, help="Explicit verified VESUM shadow database")
    parser.add_argument(
        "--sources-db",
        type=Path,
        help="Optional read-only local sources.db for Dmklinger and SUM-11 fallbacks",
    )
    parser.add_argument("--candidates-out", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--decisions-out", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--apply", action="store_true", help="Build the promotion plan")
    parser.add_argument("--write", action="store_true", help="Apply the plan to the manifest")
    parser.add_argument("--allow-held", action="store_true", help="Allow promoting ready candidates while holding anchorless rows")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)
    if args.write and not args.apply:
        parser.error("--write requires --apply")
    if not args.apply:
        parser.error("--apply is required to build a promotion plan")
    if not args.vesum_db.is_file():
        parser.error(f"--vesum-db is not a file: {args.vesum_db}")
    summary = promote(
        full_decisions=args.full_decisions,
        curated_inventory=args.curated_inventory,
        manifest=args.manifest,
        fingerprint=args.fingerprint,
        vesum_db=args.vesum_db,
        sources_db=args.sources_db,
        candidates_out=args.candidates_out,
        decisions_out=args.decisions_out,
        write=args.write,
        allow_held=args.allow_held,
    )
    if args.report:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
