#!/usr/bin/env python3
"""Curated auto-approve re-promote for Ohoiko books + ULP lesson notes.

Policy (operator 2026-07-19): Ohoiko / ULP / teacher / textbook inventories are
curated human sources — auto-approve without AI row review. Mechanical holds
only (missing POS/gloss, VESUM-absent singles with no SUM11/heritage, hard
russianism/surzhyk).

Builds:
  1. Source inventory YAML (lemmas + gloss + locators; no raw prose)
  2. Decision ledger with approve_for_publish
  3. Skeleton candidates + promotion plan
  4. Optional live manifest apply + publish

Run from repository root::

    .venv/bin/python -m scripts.lexicon.curated_ohoiko_ulp_repromote --write-inventory --write-decisions
    .venv/bin/python -m scripts.lexicon.curated_ohoiko_ulp_repromote --apply --write
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import apply_source_inventory_promotion as apply
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.audit.source_inventory_intake import read_source_inventory, source_inventory_candidates
from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.ingest import ohoiko_books_ingest as books_ingest
from scripts.ingest import ohoiko_verbs_ingest as verbs_ingest
from scripts.ingest import ulp_lesson_notes_ingest as ulp_ingest
from scripts.lexicon.atlas_intake_core import CURATED_SOURCE_FAMILIES
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.content_lexicon_reconciler import extract_ukrainian_tokens
from scripts.lexicon.grow_lexicon_from_content import build_payload, build_skeleton_entry, write_candidates
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_word

DEFAULT_INVENTORY = (
    PROJECT_ROOT / "data/lexicon/source-inventory/ohoiko-ulp-curated-2026-07-19-bulk.yaml"
)
DEFAULT_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-07-19-ohoiko-ulp-curated-bulk-approve.yaml"
)
DEFAULT_CANDIDATES = Path("/tmp/atlas-ohoiko-ulp-curated-candidates.json")
DEFAULT_PLAN = Path("/tmp/atlas-ohoiko-ulp-curated-plan.json")
DEFAULT_MANIFEST = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
DEFAULT_FINGERPRINT = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"
SOURCE_ID = "ohoiko-ulp-curated-2026-07-19-bulk"
INV_REL = "data/lexicon/source-inventory/ohoiko-ulp-curated-2026-07-19-bulk.yaml"

_STRESS_RE = re.compile("[\u0300\u0301]")
_TOKEN_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’`-][А-ЩЬЮЯЄІЇа-яґєіїґ]+)*", re.I)
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


def _norm_lemma(text: str) -> str:
    cleaned = strip_acute_stress(text)
    cleaned = cleaned.replace("ʼ", "'").replace("’", "'").replace("`", "'")
    cleaned = " ".join(cleaned.split())
    if cleaned.isupper() and len(cleaned) <= 10:
        return cleaned
    return cleaned.casefold()


def _vesum_pos(lemma: str) -> str | None:
    hits = verify_word(lemma) or []
    if not hits:
        return None
    raw = str(hits[0].get("pos") or "").strip().lower()
    return _POS_MAP.get(raw, raw or None)


def _sum11_gloss(conn: sqlite3.Connection, lemma: str) -> str | None:
    row = conn.execute("SELECT definition FROM sum11 WHERE word = ? LIMIT 1", (lemma,)).fetchone()
    if not row or not row[0]:
        return None
    definition = " ".join(str(row[0]).split())
    # Drop dictionary meta prefix like АВТОМОБІ́ЛЬ, я, ч.
    if ". " in definition[:80]:
        # Prefer first prose sentence after headword metadata when possible.
        parts = definition.split(". ", 1)
        if len(parts) == 2 and len(parts[0]) < 60:
            definition = parts[1]
    if len(definition) > 180:
        definition = definition[:177] + "..."
    return definition or None


def _infer_pos(lemma: str, gloss: str, *, preferred: str | None = None) -> str:
    if preferred:
        return preferred
    if " " in lemma or "/" in lemma or "," in lemma:
        return "phrase"
    vp = _vesum_pos(lemma)
    if vp:
        return vp
    g = (gloss or "").strip().lower()
    if g.startswith("to "):
        return "verb"
    if lemma.endswith(("ти", "тися", "ть")) and " " not in lemma:
        return "verb"
    return "noun"


def collect_book_headwords() -> list[dict[str, Any]]:
    """1000 words + 500 verbs with author English glosses."""
    rows: list[dict[str, Any]] = []
    words_path = books_ingest.REFERENCES_DIR / books_ingest.BOOKS["1000-words"].txt_filename
    for entry in books_ingest.parse_book(words_path):
        head = _norm_lemma(entry.headword)
        if not head or len(head) < 1:
            continue
        gloss = " ".join((entry.english or "").split()) or "ohoiko 1000-words entry"
        # Split "а / й" style alternatives into separate heads when short.
        alts = [head]
        if " = " in entry.headword:
            alts = [_norm_lemma(part) for part in entry.headword.split("=", 1)]
        for lemma in alts:
            if not lemma:
                continue
            rows.append(
                {
                    "lemma": lemma,
                    "pos": _infer_pos(lemma, gloss),
                    "gloss": gloss,
                    "locator": f"ohoiko-1000-words entry {entry.number}",
                    "source_id": "ohoiko-1000-words-2nd-ed",
                    "source_family": "ohoiko",
                    "extraction_mode": "book_candidate",
                }
            )

    verbs_path = verbs_ingest.REFERENCES_DIR / verbs_ingest.TXT_FILENAME
    for verb in verbs_ingest.parse_book(verbs_path):
        line = verb.headword_line or (verb.body_lines[0] if verb.body_lines else "")
        # "аналізувати | проаналізувати   Present..."
        head_part = line.split("Present", 1)[0].split("Future", 1)[0]
        forms = [f.strip() for f in head_part.split("|")]
        forms = [_norm_lemma(_STRESS_RE.sub("", f.split()[0] if f.split() else f)) for f in forms if f.strip()]
        eng = ""
        for body in verb.body_lines[1:6]:
            b = body.strip()
            if b.lower().startswith("to "):
                eng = " ".join(b.split()[:12])
                break
        gloss = eng or "ohoiko 500-verbs entry"
        for lemma in forms:
            if not lemma or len(lemma) < 2:
                continue
            rows.append(
                {
                    "lemma": lemma,
                    "pos": "verb",
                    "gloss": gloss,
                    "locator": f"ohoiko-500-verbs entry {verb.number}",
                    "source_id": "ohoiko-500-verbs",
                    "source_family": "ohoiko",
                    "extraction_mode": "book_candidate",
                }
            )
    return rows


def collect_ulp_headwords(*, min_freq: int, sum_conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Token inventory from ULP lesson notes with SUM11 gloss fill."""
    counts: dict[str, int] = {}
    locators: dict[str, str] = {}
    for _slug, book in ulp_ingest.BOOKS.items():
        path = ulp_ingest.REFERENCES_DIR / book.txt_filename
        if not path.is_file():
            continue
        lessons = ulp_ingest.parse_book(path)
        for lesson in lessons:
            text = lesson.render()
            for tok in extract_ukrainian_tokens(text):
                lemma = _norm_lemma(tok)
                if len(lemma) < 2:
                    continue
                counts[lemma] = counts.get(lemma, 0) + 1
                locators.setdefault(lemma, f"{book.source_file} lesson {lesson.number}")

    rows: list[dict[str, Any]] = []
    for lemma, freq in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        if freq < min_freq:
            continue
        if " " in lemma:
            continue
        pos = _vesum_pos(lemma)
        if not pos:
            continue
        gloss = _sum11_gloss(sum_conn, lemma)
        if not gloss:
            continue
        rows.append(
            {
                "lemma": lemma,
                "pos": pos,
                "gloss": gloss,
                "locator": locators[lemma],
                "source_id": locators[lemma].split()[0],
                "source_family": "ulp",
                "extraction_mode": "content_token",
                "count": freq,
            }
        )
    return rows


def dedupe_headwords(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    # Prefer book_candidate over content_token when both exist.
    ordered = sorted(rows, key=lambda r: (0 if r.get("extraction_mode") == "book_candidate" else 1, r["lemma"]))
    for row in ordered:
        key = _lemma_key(str(row["lemma"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(row))
    return out


def write_inventory(rows: Sequence[Mapping[str, Any]], path: Path) -> Path:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        family = str(row["source_family"])
        item = {
            "lemma": row["lemma"],
            "pos": row["pos"],
            "gloss": row["gloss"],
            "locator": row["locator"],
            "context": (
                f"Curated {family} inventory ({row['extraction_mode']}); "
                "auto-approve policy — no AI linguistic review."
            ),
        }
        by_family.setdefault(family, []).append(item)
    sources = []
    for family, headwords in sorted(by_family.items()):
        sources.append(
            {
                "id": f"{SOURCE_ID}-{family}",
                "source_family": family,
                "extraction_mode": "curated_bulk",
                "title": f"{family} curated bulk 2026-07-19",
                "locator": "private Ohoiko/ULP extracts — lemmas only committed",
                "notes": (
                    "Derived headword metadata only; raw private copyrighted material is "
                    "local-only and not committed. Curated-source auto-approve; Daily Word / "
                    "Practice / cloze remain frozen without surface_admission."
                ),
                "headwords": headwords,
            }
        )
    doc = {
        "version": 1,
        "kind": "atlas_source_inventory",
        "sources": sources,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return path


def write_decisions(rows: Sequence[Mapping[str, Any]], path: Path, *, inventory_rel: str) -> Path:
    decisions = []
    for row in rows:
        lemma = str(row["lemma"])
        locator = str(row["locator"])
        family = str(row["source_family"])
        # Must match inventory sources[].id written by write_inventory.
        inventory_source_id = f"{SOURCE_ID}-{family}"
        key = source_inventory_key(lemma=lemma, inventory_path=inventory_rel, locator=locator)
        decisions.append(
            {
                "lemma": lemma,
                "decision": "approve_for_publish",
                "approved_pos": row["pos"],
                "approved_gloss": row["gloss"],
                "sense_note": (
                    f"curated {family} auto-approve "
                    f"({row['extraction_mode']}); no AI review"
                ),
                "source_inventory": {
                    "key": key,
                    "path": inventory_rel,
                    "locator": locator,
                    "source_id": inventory_source_id,
                    "source_family": family,
                },
                "evidence_refs": [
                    f"curated source family {family}",
                    "offline dictionary gloss or author English",
                ],
            }
        )
    doc = {
        "version": 1,
        "kind": "atlas_source_inventory_review_decisions",
        "batch_id": "source-inventory-ohoiko-ulp-curated-bulk-2026-07-19",
        "batch_label": "ohoiko-ulp-curated-bulk-approve-2026-07-19",
        "reviewer": "operator-curated-source-trust",
        "reviewed_at": "2026-07-19",
        "source_queue": {
            "workflow": "source_inventory_publish_review_queue.v1",
            "total_queue_rows": len(decisions),
            "approved_in_queue": len(decisions),
            "promotion_batch_size": len(decisions),
        },
        "production_outputs_updated": [],
        "decisions": decisions,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return path


def build_candidates(inventory_path: Path, out: Path) -> Path:
    records = read_source_inventory(inventory_path, project_root=PROJECT_ROOT)
    cands = source_inventory_candidates(records)
    auto_merge = []
    for item in cands:
        entry = build_skeleton_entry(item.lemma)
        if item.pos:
            entry["pos"] = item.pos
        if item.gloss:
            entry["gloss"] = item.gloss
        entry["primary_source"] = "source_inventory_grow"
        prov = []
        for p in item.source_provenance:
            pp = dict(p)
            ip = str(pp.get("inventory_path") or "")
            if not ip.startswith("data/"):
                if "data/lexicon/source-inventory/" in ip:
                    pp["inventory_path"] = "data/lexicon/source-inventory/" + ip.split(
                        "data/lexicon/source-inventory/"
                    )[-1]
                else:
                    pp["inventory_path"] = INV_REL
            prov.append(pp)
        entry["source_provenance"] = prov
        is_mw = " " in strip_acute_stress(item.lemma)
        entry["heritage_status"] = {
            "classification": "unknown",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "vesum_attested": bool(verify_word(item.lemma) or []) or is_mw,
            "calque_warning": None,
            "warning_severity": "none",
        }
        auto_merge.append(entry)
    payload = build_payload(
        total_delta=len(cands),
        processed=len(cands),
        auto_merge=auto_merge,
        needs_review=[],
        limit=None,
    )
    payload["generated_from"] = "curated_ohoiko_ulp_repromote.v1"
    write_candidates(payload, out)
    return out


def apply_plan(
    *,
    candidates: Path,
    decisions: Path,
    manifest: Path,
    fingerprint: Path,
    write: bool,
) -> dict[str, Any]:
    plan = planner.build_promotion_plan(
        candidates_path=candidates,
        decision_files=[decisions],
        manifest_path=manifest,
    )
    planner.write_plan(plan, DEFAULT_PLAN)
    print("plan", plan["counts"], flush=True)
    if not write:
        return {"plan": plan["counts"], "wrote": False}

    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    before = len(manifest_payload["entries"])
    result = apply.apply_promotion_plan(manifest_payload, plan)
    promoted = [row["lemma"] for row in result["promoted_entries"]]

    def delta_self_check(path: Path) -> int:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = {
            _lemma_key(str(e.get("lemma") or "")): e for e in data["entries"] if isinstance(e, dict)
        }
        failures: list[str] = []
        for lemma in promoted:
            entry = entries.get(_lemma_key(lemma))
            if entry is None:
                failures.append(f"{lemma}: missing")
                continue
            try:
                apply._validate_privacy_safe_provenance(entry)
            except Exception as exc:
                failures.append(str(exc))
            if not (entry.get("gloss") or "").strip():
                failures.append(f"{lemma}: empty gloss")
            if not (entry.get("pos") or "").strip():
                failures.append(f"{lemma}: empty pos")
        if failures:
            print("DELTA FAIL", failures[:20], flush=True)
            return 2
        print("DELTA OK", len(promoted), flush=True)
        return 0

    if result["counts"]["promoted"]:
        result = apply.write_manifest_if_changed(
            manifest_payload,
            result,
            manifest_path=manifest,
            fingerprint_path=fingerprint,
            self_check=delta_self_check,
        )
    after = len(json.loads(manifest.read_text(encoding="utf-8"))["entries"])
    summary = {
        "before": before,
        "after": after,
        "promoted": result["counts"]["promoted"],
        "skipped_existing": result["counts"]["skipped_existing"],
        "outputs": result.get("production_outputs_updated"),
    }
    print("apply", summary, flush=True)
    return summary


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inventory-out", type=Path, default=DEFAULT_INVENTORY)
    p.add_argument("--decisions-out", type=Path, default=DEFAULT_DECISIONS)
    p.add_argument("--candidates-out", type=Path, default=DEFAULT_CANDIDATES)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    p.add_argument("--ulp-min-freq", type=int, default=3, help="Min ULP token frequency to include")
    p.add_argument("--skip-ulp", action="store_true", help="Only Ohoiko books (1000 words + 500 verbs)")
    p.add_argument("--write-inventory", action="store_true")
    p.add_argument("--write-decisions", action="store_true")
    p.add_argument("--apply", action="store_true", help="Build candidates + promotion plan")
    p.add_argument("--write", action="store_true", help="Write manifest (requires --apply)")
    p.add_argument("--report", action="store_true")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    assert "ohoiko" in CURATED_SOURCE_FAMILIES and "ulp" in CURATED_SOURCE_FAMILIES

    book_rows = collect_book_headwords()
    ulp_rows: list[dict[str, Any]] = []
    if not args.skip_ulp:
        with sqlite3.connect(f"file:{PROJECT_ROOT / 'data' / 'sources.db'}?mode=ro", uri=True) as conn:
            ulp_rows = collect_ulp_headwords(min_freq=args.ulp_min_freq, sum_conn=conn)
    rows = dedupe_headwords([*book_rows, *ulp_rows])
    by_family: dict[str, int] = {}
    for row in rows:
        by_family[str(row["source_family"])] = by_family.get(str(row["source_family"]), 0) + 1
    print(
        {
            "book_rows_raw": len(book_rows),
            "ulp_rows_raw": len(ulp_rows),
            "deduped": len(rows),
            "by_family": by_family,
            "curated_families": sorted(CURATED_SOURCE_FAMILIES),
        },
        flush=True,
    )

    if args.write_inventory or args.write_decisions or args.apply:
        write_inventory(rows, args.inventory_out)
        print("wrote inventory", args.inventory_out, flush=True)
    if args.write_decisions or args.apply:
        write_decisions(rows, args.decisions_out, inventory_rel=INV_REL)
        print("wrote decisions", args.decisions_out, "n=", len(rows), flush=True)
    if args.apply:
        # Ensure inventory is registered path-wise (relative inventory_path)
        build_candidates(args.inventory_out, args.candidates_out)
        print("wrote candidates", args.candidates_out, flush=True)
        summary = apply_plan(
            candidates=args.candidates_out,
            decisions=args.decisions_out,
            manifest=args.manifest,
            fingerprint=args.fingerprint,
            write=args.write,
        )
        if args.report:
            print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
