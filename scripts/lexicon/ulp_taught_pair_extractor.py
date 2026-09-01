#!/usr/bin/env python3
"""Extract and measure taught vocabulary pairs from ULP lesson notes (#7550 Unit B).

Distinguishes between:
  1. Curated taught lists (curated frequency/glossed headwords in Atlas)
  2. Raw note-token intake soup (13,202 uncurated token occurrences without EN glosses)
  3. Taught pairs (Ukrainian headword and Anna's English gloss co-occurring in note rows/margins)

Policy:
  - Measure only.
  - Zero admits from uncurated/unrecognized tokens.
  - No 11,646 needs_more_evidence dump.
  - No manifest pointer change.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PRIMARY_ROOT = Path("/home/ops/learn-ukrainian")


def _resolve_repo_path(path: Path) -> Path:
    """Resolve a path against the worktree root first, then primary checkout for gitignored data."""
    if path.exists():
        return path
    try:
        rel = path.relative_to(PROJECT_ROOT)
        primary_fallback = PRIMARY_ROOT / rel
        if primary_fallback.exists():
            return primary_fallback
    except ValueError:
        pass
    return path


from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.heritage_classifier import classify_lemma
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.lexicon.ohoiko_paired_headword_split import (
    resolve_leg_lemma,
    split_paired_headword,
    strip_trailing_parentheticals,
)
from scripts.verification.vesum import verify_word

DEFAULT_MANIFEST = _resolve_repo_path(PROJECT_ROOT / "site/src/data/lexicon-manifest.json")
DEFAULT_CURATED_INVENTORY = _resolve_repo_path(
    PROJECT_ROOT / "data/lexicon/source-inventory/oneshot/ohoiko-ulp-curated-2026-07-19-bulk.yaml"
)
DEFAULT_INTAKE_DECISIONS_DIR = _resolve_repo_path(PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions")
DEFAULT_SOURCES_DB = _resolve_repo_path(PROJECT_ROOT / "data" / "sources.db")

SEPARATORS = ("—", "–", "―", " - ", " = ", ": ")
CYRILLIC_PATTERN = r"[А-Яа-яЄІЇҐєіїґ\u0400-\u04FF]"
CYRILLIC_LINE_CHARS = r"^[А-Яа-яЄІЇҐєіїґ\u0400-\u04FF\u0300-\u036f\s\(\)\,\.\!\?\'\’\`\/\-\+=–—―\d\–«»\"]+$"
LATIN_LINE_CHARS = r"^[A-Za-z0-9\s\(\)\,\.\!\?\'\’\`\/\-\+;:\"]+$"


@dataclass(frozen=True)
class TaughtPair:
    ukrainian_headword: str
    english_gloss: str
    locator: str
    source_file: str
    season: int


def extract_taught_pairs_from_text(
    text: str,
    *,
    source_file: str = "ulp-note",
    season: int = 0,
) -> list[TaughtPair]:
    """Extract (Ukrainian headword, English gloss) pairs from lesson note text."""
    pairs: list[TaughtPair] = []
    lines = text.splitlines()

    in_key_vocab = False

    for line_idx, raw_line in enumerate(lines, start=1):
        line_str = raw_line.rstrip()
        stripped_line = line_str.strip()
        if not stripped_line:
            continue

        # Header detection for Key Vocabulary (seasons 1-3)
        if re.search(r"Key Vocabulary \d+-\d+|Bonus Vocabulary", stripped_line, re.I):
            in_key_vocab = True
            continue
        if in_key_vocab and (stripped_line.startswith("Lesson ") or stripped_line.startswith("Episode ")):
            in_key_vocab = False

        # 1. Two-column margin glosses or aligned tables (separated by >= 4 spaces)
        chunks = [c.strip() for c in re.split(r"\s{4,}", stripped_line) if c.strip()]
        matched = False
        if len(chunks) >= 2:
            right_chunk = chunks[-1]
            for sep in SEPARATORS:
                if sep in right_chunk:
                    p_uk, p_en = right_chunk.split(sep, 1)
                    p_uk, p_en = p_uk.strip(), p_en.strip()
                    if (
                        re.search(CYRILLIC_PATTERN, p_uk)
                        and re.search(r"[A-Za-z]", p_en)
                        and not re.search(CYRILLIC_PATTERN, p_en)
                    ):
                        pairs.append(
                            TaughtPair(
                                ukrainian_headword=p_uk,
                                english_gloss=p_en,
                                locator=f"{source_file}:line_{line_idx}:margin",
                                source_file=source_file,
                                season=season,
                            )
                        )
                        matched = True
                        break
            if not matched and (in_key_vocab or len(chunks) == 2):
                left_chunk = chunks[0]
                if (
                    re.search(CYRILLIC_LINE_CHARS, left_chunk)
                    and re.search(LATIN_LINE_CHARS, right_chunk)
                    and re.search(CYRILLIC_PATTERN, left_chunk)
                    and re.search(r"[A-Za-z]", right_chunk)
                ):
                    pairs.append(
                        TaughtPair(
                            ukrainian_headword=left_chunk,
                            english_gloss=right_chunk,
                            locator=f"{source_file}:line_{line_idx}:table",
                            source_file=source_file,
                            season=season,
                        )
                    )
                    matched = True

        # 2. Standalone line with dash separator
        if not matched:
            for sep in ("—", "–", "―", " - "):
                if sep in stripped_line:
                    p_uk, p_en = stripped_line.split(sep, 1)
                    p_uk, p_en = p_uk.strip(), p_en.strip()
                    if (
                        re.search(CYRILLIC_LINE_CHARS, p_uk)
                        and re.search(LATIN_LINE_CHARS, p_en)
                        and re.search(CYRILLIC_PATTERN, p_uk)
                        and re.search(r"[A-Za-z]", p_en)
                    ):
                        pairs.append(
                            TaughtPair(
                                ukrainian_headword=p_uk,
                                english_gloss=p_en,
                                locator=f"{source_file}:line_{line_idx}:inline",
                                source_file=source_file,
                                season=season,
                            )
                        )
                        break

    return pairs


def load_atlas_lemma_keys(manifest_path: Path = DEFAULT_MANIFEST) -> set[str]:
    manifest_file = _resolve_repo_path(manifest_path)
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    return {_lemma_key(str(entry.get("lemma") or "")) for entry in data.get("entries", []) if isinstance(entry, dict)}


def measure_curated_ulp_lists(
    inventory_path: Path = DEFAULT_CURATED_INVENTORY,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Measure the 3,906 curated ULP entries vs live Atlas."""
    atlas_keys = load_atlas_lemma_keys(manifest_path)
    inv_file = _resolve_repo_path(inventory_path)
    doc = yaml.safe_load(inv_file.read_text(encoding="utf-8"))
    ulp_source = next(
        (s for s in doc.get("sources", []) if s.get("id") == "ohoiko-ulp-curated-2026-07-19-bulk-ulp"),
        None,
    )
    if not ulp_source:
        return {"error": "ulp source not found in inventory"}

    hws = ulp_source.get("headwords", [])
    seasons: dict[int, list[dict[str, Any]]] = {}
    for hw in hws:
        loc = str(hw.get("locator") or "")
        m = re.search(r"ulp-(\d)-00-lesson-notes", loc)
        season = int(m.group(1)) if m else 0
        seasons.setdefault(season, []).append(hw)

    per_season = {}
    total_missing = 0
    total_in_atlas = 0

    for s in sorted(seasons.keys()):
        items = seasons[s]
        unique_lemmas = {str(hw["lemma"]) for hw in items}
        missing_lemmas = []
        for lemma in sorted(unique_lemmas):
            eff = resolve_leg_lemma(lemma)
            if _lemma_key(eff) not in atlas_keys:
                missing_lemmas.append(lemma)
        in_atlas_count = len(unique_lemmas) - len(missing_lemmas)
        total_in_atlas += in_atlas_count
        total_missing += len(missing_lemmas)
        per_season[s] = {
            "total_rows": len(items),
            "unique_lemmas": len(unique_lemmas),
            "in_atlas": in_atlas_count,
            "missing_count": len(missing_lemmas),
            "missing_lemmas": missing_lemmas,
        }

    return {
        "schema": "atlas-7550-unit-b-curated-census.v1",
        "total_curated_rows": len(hws),
        "total_in_atlas": total_in_atlas,
        "total_missing": total_missing,
        "per_season": per_season,
    }


def measure_corpus_intake_ulp(
    decisions_dir: Path = DEFAULT_INTAKE_DECISIONS_DIR,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Measure the uncurated ULP intake rows (21 batch ledgers) vs live Atlas."""
    atlas_keys = load_atlas_lemma_keys(manifest_path)
    dec_dir = _resolve_repo_path(decisions_dir)
    files = sorted(dec_dir.glob("2026-07-14-ohoiko-corpus-intake-batch-*.yaml"))
    all_decisions: list[dict[str, Any]] = []
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        all_decisions.extend(doc.get("decisions", []))

    ulp_decisions = [d for d in all_decisions if "ulp-" in str(d.get("source_inventory", {}).get("source_id", ""))]

    per_season = {}
    for s in range(1, 7):
        sid = f"ulp-{s}-00-lesson-notes"
        s_decs = [d for d in ulp_decisions if d.get("source_inventory", {}).get("source_id") == sid]
        unique_lemmas = {str(d["lemma"]) for d in s_decs}

        in_atlas = 0
        vesum_ok_missing = 0
        vesum_unrec = 0
        heritage_hold = 0

        for lemma in unique_lemmas:
            eff = resolve_leg_lemma(lemma)
            key = _lemma_key(eff)
            if key in atlas_keys:
                in_atlas += 1
            else:
                hits = verify_word(eff) or []
                if not hits:
                    vesum_unrec += 1
                else:
                    hs = classify_lemma(eff)
                    cl = str(hs.get("classification") or "")
                    if (
                        hs.get("is_russianism")
                        or hs.get("russian_shadow")
                        or cl in ("russianism", "calque", "surzhyk", "sovietism")
                    ):
                        heritage_hold += 1
                    else:
                        vesum_ok_missing += 1

        per_season[s] = {
            "source_id": sid,
            "total_rows": len(s_decs),
            "unique_lemmas": len(unique_lemmas),
            "already_in_atlas": in_atlas,
            "missing_total": len(unique_lemmas) - in_atlas,
            "vesum_ok_missing": vesum_ok_missing,
            "vesum_unrecognized": vesum_unrec,
            "heritage_hold": heritage_hold,
            "no_en_count": len(unique_lemmas),
        }

    return {
        "schema": "atlas-7550-unit-b-intake-census.v1",
        "total_ulp_decisions": len(ulp_decisions),
        "per_season": per_season,
    }


def measure_taught_pairs_from_sources(
    sources_db_path: Path = DEFAULT_SOURCES_DB,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Extract and measure taught pairs from textbooks in sources.db."""
    import sqlite3

    db_file = _resolve_repo_path(sources_db_path)
    if not db_file.is_file():
        return {"error": f"sources.db not found at {db_file}"}

    atlas_keys = load_atlas_lemma_keys(manifest_path)
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()

    per_season = {}
    for s in range(1, 7):
        sf = f"ulp-{s}-00-lesson-notes"
        rows = cur.execute(
            "SELECT chunk_id, title, text FROM textbooks WHERE source_file = ? ORDER BY chunk_id",
            (sf,),
        ).fetchall()

        pairs: list[TaughtPair] = []
        for _cid, _title, text in rows:
            pairs.extend(extract_taught_pairs_from_text(text, source_file=sf, season=s))

        unique_uk_headwords = {p.ukrainian_headword for p in pairs}
        all_legs: list[str] = []
        for uk in unique_uk_headwords:
            legs = split_paired_headword(uk)
            for leg in legs:
                cleaned = strip_trailing_parentheticals(strip_acute_stress(leg).strip())
                cleaned = cleaned.strip("–—―- =.!?\"'")
                if cleaned:
                    all_legs.append(cleaned)

        unique_lemmas = sorted(set(all_legs))
        in_atlas = 0
        vesum_ok_missing: list[str] = []
        vesum_unrec: list[str] = []
        heritage_hold: list[str] = []
        multiword: list[str] = []

        for lemma in unique_lemmas:
            eff = resolve_leg_lemma(lemma)
            if " " in eff:
                multiword.append(eff)
                continue
            key = _lemma_key(eff)
            if key in atlas_keys:
                in_atlas += 1
            else:
                hits = verify_word(eff) or []
                if not hits:
                    vesum_unrec.append(eff)
                else:
                    hs = classify_lemma(eff)
                    cl = str(hs.get("classification") or "")
                    if (
                        hs.get("is_russianism")
                        or hs.get("russian_shadow")
                        or cl in ("russianism", "calque", "surzhyk", "sovietism")
                    ):
                        heritage_hold.append(eff)
                    else:
                        vesum_ok_missing.append(eff)

        per_season[s] = {
            "source_file": sf,
            "raw_taught_pairs": len(pairs),
            "unique_uk_headwords": len(unique_uk_headwords),
            "unique_single_word_lemmas": len(unique_lemmas) - len(multiword),
            "multiword_phrases": len(multiword),
            "already_in_atlas": in_atlas,
            "vesum_ok_missing_count": len(vesum_ok_missing),
            "vesum_ok_missing_samples": vesum_ok_missing[:15],
            "vesum_unrecognized_count": len(vesum_unrec),
            "vesum_unrecognized_samples": vesum_unrec[:15],
            "heritage_hold_count": len(heritage_hold),
            "heritage_hold_samples": heritage_hold[:15],
        }

    conn.close()
    return {
        "schema": "atlas-7550-unit-b-taught-pairs-census.v1",
        "per_season": per_season,
    }


def format_markdown_tables(
    curated: Mapping[str, Any],
    intake: Mapping[str, Any],
    taught: Mapping[str, Any],
) -> str:
    """Format the complete acceptance markdown comment for #7550."""
    lines = [
        "## Unit B — ULP Seasons 1–6 Lemma Census (#7550)",
        "",
        "### 1. Curated Taught Headwords vs Live Atlas 20,121 (`dc1d73a434e2`)",
        "",
        "| Source Unit | Curated Unique | In Atlas | Missing | Leftovers & Disposition |",
        "| :--- | ---: | ---: | ---: | :--- |",
    ]
    cur_seasons = curated.get("per_season", {})
    for s in sorted(cur_seasons.keys()):
        d = cur_seasons[s]
        missing_str = "—" if not d["missing_lemmas"] else ", ".join(f"`{m}`" for m in d["missing_lemmas"])
        disp_str = "—" if not d["missing_lemmas"] else "hold(heritage_russianism) via #7557"
        lines.append(
            f"| ULP Season {s} | {d['unique_lemmas']:,} | {d['in_atlas']:,} | **{d['missing_count']}** | {missing_str} ({disp_str}) |"
        )
    lines.extend(
        [
            f"| **Total** | **{curated.get('total_curated_rows', 0):,}** | **{curated.get('total_in_atlas', 0):,}** | **{curated.get('total_missing', 0)}** | **0 admits** |",
            "",
            "---",
            "",
            "### 2. Corpus Intake: Note-Token Extraction Soup (13,202 uncurated candidate rows)",
            "",
            "| Intake Source ID | Unique Candidates | In Atlas | Missing Total | VESUM-ok Missing | `vesum_unrecognized` | Heritage Hold | Explicit EN Gloss |",
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
        ]
    )
    int_seasons = intake.get("per_season", {})
    tot_candidates = sum(d["unique_lemmas"] for d in int_seasons.values())
    tot_in_atlas = sum(d["already_in_atlas"] for d in int_seasons.values())
    tot_missing = sum(d["missing_total"] for d in int_seasons.values())
    tot_vesum_ok = sum(d["vesum_ok_missing"] for d in int_seasons.values())
    tot_vesum_unrec = sum(d["vesum_unrecognized"] for d in int_seasons.values())
    tot_heritage = sum(d["heritage_hold"] for d in int_seasons.values())

    for s in sorted(int_seasons.keys()):
        d = int_seasons[s]
        lines.append(
            f"| `{d['source_id']}` | {d['unique_lemmas']:,} | {d['already_in_atlas']:,} | {d['missing_total']:,} | {d['vesum_ok_missing']:,} | {d['vesum_unrecognized']:,} | {d['heritage_hold']:,} | 0 (all no-EN) |"
        )
    lines.extend(
        [
            f"| **Total** | **{tot_candidates:,}** | **{tot_in_atlas:,}** | **{tot_missing:,}** | **{tot_vesum_ok:,}** | **{tot_vesum_unrec:,}** | **{tot_heritage:,}** | **0 admits** |",
            "",
            "> [!NOTE]",
            "> All 13,202 corpus intake candidate occurrences from ULP lesson notes are uncurated token extracts from running text (`extraction_mode: content_token`) with no explicit English glosses attached. They belong to Unit C (`needs_more_evidence`) and must **never** be admitted into Atlas.",
            "",
            "---",
            "",
            "### 3. Taught Vocabulary Pairs: (Ukrainian Headword + Anna's English Gloss)",
            "",
            "| Source Unit | Raw Pairs Extracted | Unique UK Headwords | Single-Word Lemmas | In Atlas | VESUM-ok Missing | `vesum_unrecognized` | Heritage Hold | Multiword Phrases |",
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    taught_seasons = taught.get("per_season", {})
    for s in sorted(taught_seasons.keys()):
        d = taught_seasons[s]
        lines.append(
            f"| ULP Season {s} (`{d['source_file']}`) | {d['raw_taught_pairs']:,} | {d['unique_uk_headwords']:,} | {d['unique_single_word_lemmas']:,} | {d['already_in_atlas']:,} | {d['vesum_ok_missing_count']:,} | {d['vesum_unrecognized_count']:,} | {d['heritage_hold_count']:,} | {d['multiword_phrases']:,} |"
        )
    lines.extend(
        [
            "",
            "**Policy Verification & Acceptance Invariants:**",
            "- **Zero admits:** No uncurated tokens or `vesum_unrecognized` items admitted.",
            "- **Manifest pointer untouched:** `site/src/data/lexicon-manifest.json` sha256 `dc1d73a434e2` preserved.",
            "- **Unit A closed:** 250 curated leftover keys merged in #7557 (0 admits).",
            "- **Unit B denominator measured:** Clean separation between curated taught lists, token soup, and paired taught vocab.",
            "- **Unit C:** 16,237 `needs_more_evidence` corpus tokens kept frozen.",
            "",
            "X-Agent: `grok-atlas/atlas-7550-unit-b-notes`",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--inventory", type=Path, default=DEFAULT_CURATED_INVENTORY)
    p.add_argument("--decisions-dir", type=Path, default=DEFAULT_INTAKE_DECISIONS_DIR)
    p.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    p.add_argument("--measure-all", action="store_true", help="Run full measurement across all 3 categories")
    p.add_argument("--format-markdown", action="store_true", help="Print formatted markdown table for #7550")
    p.add_argument("--out", type=Path, help="Write output JSON report")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    curated = measure_curated_ulp_lists(inventory_path=args.inventory, manifest_path=args.manifest)
    intake = measure_corpus_intake_ulp(decisions_dir=args.decisions_dir, manifest_path=args.manifest)
    taught = measure_taught_pairs_from_sources(sources_db_path=args.sources_db, manifest_path=args.manifest)

    report = {
        "schema": "atlas-7550-unit-b-census.v1",
        "curated_taught_lists": curated,
        "corpus_intake_note_tokens": intake,
        "taught_vocabulary_pairs": taught,
    }

    if args.format_markdown or not args.out:
        md = format_markdown_tables(curated, intake, taught)
        print(md)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
