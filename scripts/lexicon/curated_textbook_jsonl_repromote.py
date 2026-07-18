#!/usr/bin/env python3
"""Mine school-textbook JSONL (or textbooks table) and curated auto-approve to Atlas.

Reads all grade-*/**.jsonl under GDrive textbook_chunks (or --chunks-root),
or falls back to sources.db textbooks excluding private lexicon sources.

Policy: source_family=textbook → auto-approve with POS+gloss (SUM11/VESUM).

Usage::

    .venv/bin/python -m scripts.lexicon.curated_textbook_jsonl_repromote \\
      --write-inventory --write-decisions --apply --write --report
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import Counter
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
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.content_lexicon_reconciler import extract_ukrainian_tokens
from scripts.lexicon.grow_lexicon_from_content import build_payload, build_skeleton_entry, write_candidates
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_word

SOURCE_ID = "textbook-jsonl-curated-2026-07-19-bulk"
INV_REL = f"data/lexicon/source-inventory/oneshot/{SOURCE_ID}.yaml"
DEFAULT_INVENTORY = PROJECT_ROOT / INV_REL
DEFAULT_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-07-19-textbook-jsonl-curated-bulk-approve.yaml"
)
DEFAULT_CANDIDATES = Path("/tmp/atlas-textbook-jsonl-curated-candidates.json")
DEFAULT_PLAN = Path("/tmp/atlas-textbook-jsonl-curated-plan.json")
DEFAULT_MANIFEST = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
DEFAULT_FINGERPRINT = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"

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

# Private / non-school sources already handled by Ohoiko/ULP pipeline.
_SKIP_SOURCE_PREFIXES = (
    "ulp-",
    "anna-ohoiko-",
    "antonenko-",
    "pohribnyi-",
)


def resolve_chunks_root() -> Path | None:
    env = os.environ.get("LU_GDRIVE_DATA")
    roots: list[Path] = []
    if env:
        roots.append(Path(env) / "textbook_chunks")
    roots.extend(
        Path.home().glob(
            "Library/CloudStorage/GoogleDrive-*/My Drive/Projects/learn-ukrainian-data/textbook_chunks"
        )
    )
    roots.append(PROJECT_ROOT / "data" / "textbook_chunks")
    for root in roots:
        if root.is_dir() and any(root.glob("grade-*/*.jsonl")):
            return root
    return None


def _norm_lemma(text: str) -> str:
    cleaned = strip_acute_stress(text).replace("ʼ", "'").replace("’", "'").replace("`", "'")
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
    if ". " in definition[:80]:
        parts = definition.split(". ", 1)
        if len(parts) == 2 and len(parts[0]) < 60:
            definition = parts[1]
    if len(definition) > 180:
        definition = definition[:177] + "..."
    return definition or None


def iter_jsonl_texts(chunks_root: Path) -> Iterable[tuple[str, str, str]]:
    """Yield (source_file, chunk_id, text) from grade JSONL files."""
    for path in sorted(chunks_root.glob("grade-*/*.jsonl")):
        source_file = path.stem
        if source_file.startswith(_SKIP_SOURCE_PREFIXES):
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = obj.get("text") or ""
                if not text.strip():
                    continue
                chunk_id = str(obj.get("chunk_id") or f"{source_file}_row")
                yield source_file, chunk_id, text


def iter_db_texts(db_path: Path) -> Iterable[tuple[str, str, str]]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT source_file, chunk_id, text FROM textbooks WHERE text IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()
    for source_file, chunk_id, text in rows:
        if not source_file or not text:
            continue
        if str(source_file).startswith(_SKIP_SOURCE_PREFIXES):
            continue
        # skip pure lexicon private remnants
        yield str(source_file), str(chunk_id or source_file), str(text)


def mine_headwords(
    texts: Iterable[tuple[str, str, str]],
    *,
    min_freq: int,
    sum_conn: sqlite3.Connection,
    max_lemmas: int | None = None,
) -> list[dict[str, Any]]:
    from scripts.verification.vesum import verify_words

    counts: Counter[str] = Counter()
    locators: dict[str, str] = {}
    for source_file, chunk_id, text in texts:
        for tok in extract_ukrainian_tokens(text):
            lemma = _norm_lemma(tok)
            if len(lemma) < 2 or " " in lemma:
                continue
            counts[lemma] += 1
            locators.setdefault(lemma, f"{source_file}::{chunk_id}")

    frequent = [(lemma, freq) for lemma, freq in counts.most_common() if freq >= min_freq]
    print({"unique_tokens": len(counts), "freq_ge_min": len(frequent)}, flush=True)

    # Prefer forms that exist in SUM11 first (cheap SQL), then batch VESUM.
    sum_hits: dict[str, str] = {}
    batch_size = 500
    candidates = [lemma for lemma, _freq in frequent]
    for i in range(0, len(candidates), batch_size):
        chunk = candidates[i : i + batch_size]
        placeholders = ",".join("?" * len(chunk))
        for word, definition in sum_conn.execute(
            f"SELECT word, definition FROM sum11 WHERE word IN ({placeholders})",
            chunk,
        ):
            gloss = " ".join(str(definition or "").split())
            if not gloss:
                continue
            if ". " in gloss[:80]:
                parts = gloss.split(". ", 1)
                if len(parts) == 2 and len(parts[0]) < 60:
                    gloss = parts[1]
            if len(gloss) > 180:
                gloss = gloss[:177] + "..."
            sum_hits[str(word)] = gloss
        if (i // batch_size) % 20 == 0:
            print(f"  sum11 scanned {min(i + batch_size, len(candidates))}/{len(candidates)}", flush=True)

    sum_lemmas = [lemma for lemma in candidates if lemma in sum_hits]
    print({"sum11_attested": len(sum_lemmas)}, flush=True)

    pos_by_lemma: dict[str, str] = {}
    for i in range(0, len(sum_lemmas), batch_size):
        chunk = sum_lemmas[i : i + batch_size]
        verified = verify_words(chunk) or {}
        for lemma in chunk:
            hits = verified.get(lemma) or []
            if not hits:
                continue
            raw = str(hits[0].get("pos") or "").strip().lower()
            pos = _POS_MAP.get(raw, raw or None)
            if pos:
                pos_by_lemma[lemma] = pos
        print(f"  vesum scanned {min(i + batch_size, len(sum_lemmas))}/{len(sum_lemmas)}", flush=True)

    rows: list[dict[str, Any]] = []
    for lemma, freq in frequent:
        if lemma not in sum_hits or lemma not in pos_by_lemma:
            continue
        rows.append(
            {
                "lemma": lemma,
                "pos": pos_by_lemma[lemma],
                "gloss": sum_hits[lemma],
                "locator": locators[lemma],
                "source_id": SOURCE_ID,
                "source_family": "textbook",
                "extraction_mode": "textbook_jsonl_token",
                "count": freq,
            }
        )
        if max_lemmas is not None and len(rows) >= max_lemmas:
            break
    return rows


def write_inventory(rows: Sequence[Mapping[str, Any]], path: Path) -> Path:
    headwords = [
        {
            "lemma": r["lemma"],
            "pos": r["pos"],
            "gloss": r["gloss"],
            "locator": r["locator"],
            "context": (
                "Curated school-textbook inventory (JSONL/token mine); "
                "auto-approve policy — no AI linguistic review."
            ),
        }
        for r in rows
    ]
    doc = {
        "version": 1,
        "kind": "atlas_source_inventory",
        "sources": [
            {
                "id": SOURCE_ID,
                "source_family": "textbook",
                "extraction_mode": "curated_bulk",
                "title": "School textbook JSONL curated bulk 2026-07-19",
                "locator": "GDrive textbook_chunks grade JSONL / sources.db textbooks",
                "notes": (
                    "Derived headword metadata only; raw textbook prose is not committed. "
                    "Curated-source auto-approve; Daily Word / Practice / cloze frozen without "
                    "surface_admission."
                ),
                "headwords": headwords,
            }
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return path


def write_decisions(rows: Sequence[Mapping[str, Any]], path: Path) -> Path:
    decisions = []
    for row in rows:
        lemma = str(row["lemma"])
        locator = str(row["locator"])
        key = source_inventory_key(lemma=lemma, inventory_path=INV_REL, locator=locator)
        decisions.append(
            {
                "lemma": lemma,
                "decision": "approve_for_publish",
                "approved_pos": row["pos"],
                "approved_gloss": row["gloss"],
                "sense_note": "curated textbook auto-approve (JSONL mine); no AI review",
                "source_inventory": {
                    "key": key,
                    "path": INV_REL,
                    "locator": locator,
                    "source_id": SOURCE_ID,
                    "source_family": "textbook",
                },
                "evidence_refs": [
                    "curated source family textbook",
                    "VESUM POS + SUM11 gloss",
                ],
            }
        )
    doc = {
        "version": 1,
        "kind": "atlas_source_inventory_review_decisions",
        "batch_id": "source-inventory-textbook-jsonl-curated-bulk-2026-07-19",
        "batch_label": "textbook-jsonl-curated-bulk-approve-2026-07-19",
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
        entry["heritage_status"] = {
            "classification": "unknown",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "vesum_attested": bool(verify_word(item.lemma) or []),
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
    payload["generated_from"] = "curated_textbook_jsonl_repromote.v1"
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


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chunks-root", type=Path, default=None)
    p.add_argument("--from-db", action="store_true", help="Mine sources.db textbooks instead of JSONL")
    p.add_argument("--db", type=Path, default=PROJECT_ROOT / "data" / "sources.db")
    p.add_argument("--min-freq", type=int, default=3)
    p.add_argument("--max-lemmas", type=int, default=None)
    p.add_argument("--inventory-out", type=Path, default=DEFAULT_INVENTORY)
    p.add_argument("--decisions-out", type=Path, default=DEFAULT_DECISIONS)
    p.add_argument("--candidates-out", type=Path, default=DEFAULT_CANDIDATES)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    p.add_argument("--write-inventory", action="store_true")
    p.add_argument("--write-decisions", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--write", action="store_true")
    p.add_argument("--report", action="store_true")
    args = p.parse_args(argv)

    if args.from_db:
        texts = list(iter_db_texts(args.db))
        source_note = f"db:{args.db}"
    else:
        root = args.chunks_root or resolve_chunks_root()
        if root is None:
            print("JSONL root not found; falling back to sources.db", flush=True)
            texts = list(iter_db_texts(args.db))
            source_note = f"db-fallback:{args.db}"
        else:
            print(f"mining JSONL under {root}", flush=True)
            texts = list(iter_jsonl_texts(root))
            source_note = f"jsonl:{root}"

    print({"text_units": len(texts), "source": source_note, "min_freq": args.min_freq}, flush=True)
    with sqlite3.connect(f"file:{args.db}?mode=ro", uri=True) as conn:
        rows = mine_headwords(
            texts,
            min_freq=args.min_freq,
            sum_conn=conn,
            max_lemmas=args.max_lemmas,
        )
    print({"mined_rows": len(rows)}, flush=True)

    if args.write_inventory or args.write_decisions or args.apply:
        write_inventory(rows, args.inventory_out)
        print("wrote inventory", args.inventory_out, flush=True)
    if args.write_decisions or args.apply:
        write_decisions(rows, args.decisions_out)
        print("wrote decisions", args.decisions_out, "n=", len(rows), flush=True)
    if args.apply:
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
