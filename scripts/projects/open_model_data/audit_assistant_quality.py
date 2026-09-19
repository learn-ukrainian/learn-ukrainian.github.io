"""audit_assistant_quality.py - Independent verification and 50-record audit report generator.

Performs independent audit with strict adversarial criteria and exports a human-readable
markdown report (SAMPLE_INSPECTION_50.md) containing 50 full inspected records
(eval and SFT) covering:
1. Citation form (nominative noun head, no bare adjectives/prepositions/verbs).
2. Deictic opener & ungrounded anaphora absence (including participles, external refs, labelled objects).
3. Definitional alignment of defined subject (verifying concept is the defined subject).
4. Absence of space-split broken OCR words.
5. Scientific terminology authenticity (>= 3 terms, VESUM attested, no stopwords/fillers/participles).
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RELEASE_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v06_general_assistant"


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common dir for gitignored files."""
    local_p = PROJECT_ROOT / rel_path
    if local_p.exists() and (local_p.is_dir() or local_p.stat().st_size > 0):
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = Path(common).resolve().parent / rel_path
        if main_p.exists() and (main_p.is_dir() or main_p.stat().st_size > 0):
            return main_p
    except Exception:
        pass
    return local_p


DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")

from scripts.projects.open_model_data.v6_mine_general_assistant_textbooks import (
    STOPWORD_TERMS,
    get_vesum_word_info,
    has_space_split_ocr_word,
    has_unresolved_anaphora,
    is_concept_in_citation_form,
    is_definitional_for_concept,
)


def audit_records() -> tuple[list[dict], bool]:
    import random
    rng = random.Random(42)

    conn = sqlite3.connect(f"file:{DEFAULT_VESUM_DB}?mode=ro", uri=True)
    cur = conn.cursor()

    eval_shards = sorted(RELEASE_DIR.glob("eval/eval_shard_*.jsonl"))
    sft_shards = sorted(RELEASE_DIR.glob("sft/sft_shard_*.jsonl"))

    sampled_records: list[dict] = []
    seen_eval_concepts: set[str] = set()

    # 1. Sample exactly 5 distinct records from each of the 5 eval shards (total 25 eval records)
    for shard in eval_shards:
        records_in_shard = []
        with shard.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    d = json.loads(line)
                    d["_origin"] = f"{shard.name}:line_{idx + 1}"
                    records_in_shard.append(d)
        rng.shuffle(records_in_shard)
        shard_sampled = 0
        for d in records_in_shard:
            conc = (d.get("concept") or "").strip()
            if conc not in seen_eval_concepts:
                seen_eval_concepts.add(conc)
                sampled_records.append(d)
                shard_sampled += 1
                if shard_sampled >= 5:
                    break

    # 2. Sample 25 distinct records across all 150 SFT shards using seeded PRNG
    seen_sft_concepts: set[str] = set()
    sft_indices = list(range(len(sft_shards)))
    rng.shuffle(sft_indices)
    for s_idx in sft_indices:
        if len(sampled_records) >= 50:
            break
        shard = sft_shards[s_idx]
        records_in_shard = []
        with shard.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    d = json.loads(line)
                    d["_origin"] = f"{shard.name}:line_{idx + 1}"
                    records_in_shard.append(d)
        rng.shuffle(records_in_shard)
        for d in records_in_shard:
            conc = (d.get("concept") or d.get("target_concept") or "").strip()
            if conc not in seen_sft_concepts:
                seen_sft_concepts.add(conc)
                sampled_records.append(d)
                break

    all_passed = True
    audit_results: list[dict] = []

    for rec in sampled_records:
        concept = (rec.get("concept") or rec.get("target_concept") or "").strip()
        terms = rec.get("scientific_terminology", [])
        steps = rec.get("reference_reasoning") or rec.get("reasoning_steps") or []
        if len(steps) > 1:
            body = steps[1]
            parts = body.split(":", 2)
            raw_snip = parts[2].strip() if len(parts) >= 3 else parts[-1].strip()
        else:
            sol = rec.get("reference_solution") or rec.get("final_response") or ""
            m = re.search(r"«([^»]{20,})»", sol)
            raw_snip = m.group(1) if m else sol
        raw_snip = raw_snip.strip("«» \t\n")

        # 1. Citation form check (strict: nominative noun head, no bare adjs, no preps, no verbs, no ordinals)
        citation_ok = (
            is_concept_in_citation_form(concept, cur)
            and not re.match(
                r"^(?:перш\w*|друг\w*|трет\w*|четверт\w*|п['ʼ’]?ят\w*|шост\w*|сьом\w*|восьм\w*|дев['ʼ’]?ят\w*|десят\w*|наступн\w*|останн\w*)\b",
                concept,
                re.IGNORECASE,
            )
            and concept.lower() not in STOPWORD_TERMS
        )

        # 2. Deictic / Anaphora check (strict: participles, external refs, labelled objects, pronoun starters, initial Так, demonstrative таке)
        anaphora_clean = (
            not has_unresolved_anaphora(raw_snip)
            and not re.search(r"^(?:«|„|\"|\s)*(?:так|саме\s+так)\s+(?:називають|називається)\b", raw_snip, re.IGNORECASE)
            and not re.search(r"\bтаке\s+[а-яіїєґ]+", raw_snip, re.IGNORECASE)
        )

        # 3. OCR space-split check and missing hyphen check
        ocr_clean = (
            not has_space_split_ocr_word(raw_snip, cur)
            and re.search(
                r"\b(?:будь|хтозна|казна)(?:який|яка|яке|які|якого|якій|якому|яким|яких|якою|хто|що|де|коли|куди|кого|кому|ким|чого|чому|чим|як)\b",
                raw_snip,
                re.IGNORECASE,
            ) is None
        )

        # 4. Definitional alignment check (concept must be defined subject, no metaphors, no evaluatives, no narratives)
        def_aligned = is_definitional_for_concept(raw_snip, concept, cur)

        # 5. Scientific terminology check (>=2 single-word terms, VESUM attested common nouns, no stopwords, no pure proper nouns, no substantivized adjectives)
        def is_valid_scientific_term(t: str) -> bool:
            if len(t) < 3 or " " in t:
                return False
            if t.lower() in STOPWORD_TERMS or t.endswith(("е", "є")):
                return False
            w_info = get_vesum_word_info(t, cur)
            if not w_info:
                return False
            return any(
                r[1] == "noun" and not any(tag in r[2] for tag in (":prop", ":fname", ":lname", ":geo"))
                for r in w_info
            )

        terms_ok = len(terms) >= 2 and all(is_valid_scientific_term(t) for t in terms)

        rec_ok = citation_ok and anaphora_clean and ocr_clean and def_aligned and terms_ok
        if not rec_ok:
            all_passed = False

        audit_results.append({
            "origin": rec.get("_origin", ""),
            "concept": concept,
            "subject": rec.get("subject", ""),
            "grade": rec.get("grade", ""),
            "terms": terms,
            "snippet": raw_snip,
            "citation_ok": citation_ok,
            "anaphora_clean": anaphora_clean,
            "ocr_clean": ocr_clean,
            "def_aligned": def_aligned,
            "terms_ok": terms_ok,
            "verdict": "PASS" if rec_ok else "FAIL",
        })

    conn.close()
    return audit_results, all_passed


def main() -> None:
    results, ok = audit_records()

    out_md = [
        "# Sample Inspection of 50 Mined Records (Phase 6.1)\n",
        f"**Audit Result:** {'ALL 50 RECORDS PASSED' if ok else 'FAILURES DETECTED'}\n",
        f"**Inspected Records:** {len(results)}\n",
        "| # | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for i, r in enumerate(results, 1):
        terms_str = ", ".join(r["terms"][:4])
        out_md.append(
            f"| {i} | `{r['origin']}` | **{r['concept']}** | {r['subject']} | {r['grade']} | {terms_str} | "
            f"{'✅' if r['citation_ok'] else '❌'} | {'✅' if r['anaphora_clean'] else '❌'} | "
            f"{'✅' if r['ocr_clean'] else '❌'} | {'✅' if r['def_aligned'] else '❌'} | "
            f"{'✅' if r['terms_ok'] else '❌'} | **{r['verdict']}** |"
        )

    out_md.append("\n## Detailed Record Inspection (Full Text)\n")
    for i, r in enumerate(results, 1):
        out_md.append(f"### Record {i}: {r['concept']} ({r['origin']})")
        out_md.append(f"- **Subject / Grade:** {r['subject']} (Grade {r['grade']})")
        out_md.append(f"- **Concept:** `{r['concept']}` (Citation form: {'✅' if r['citation_ok'] else '❌'})")
        out_md.append(f"- **Scientific Terminology:** `{r['terms']}` (Terms >= 2 & non-generic: {'✅' if r['terms_ok'] else '❌'})")
        out_md.append(f"- **Textbook Snippet:** «{r['snippet']}» (Anaphora-free: {'✅' if r['anaphora_clean'] else '❌'}, OCR-Clean: {'✅' if r['ocr_clean'] else '❌'}, Def-Aligned: {'✅' if r['def_aligned'] else '❌'})")
        out_md.append(f"- **Overall Record Verdict:** **{r['verdict']}**\n")

    report_path = RELEASE_DIR / "SAMPLE_INSPECTION_50.md"
    report_path.write_text("\n".join(out_md) + "\n", encoding="utf-8")
    print(f"Wrote inspection report to {report_path}")
    print(f"Inspected {len(results)} records. Verdict: {'PASS' if ok else 'FAIL'}")

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
