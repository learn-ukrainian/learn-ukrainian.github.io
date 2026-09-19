#!/usr/bin/env python3
"""Run independent non-Gemini seat (Claude) judgment of all eval benchmark records.

Fulfills Phase 6.1 (#8139) requirement for Round 16:
'Then have a non-Gemini seat judge every eval record as definition or not,
 and publish its disagreements with the regex audit.'
"""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_DIR = REPO_ROOT / "data/projects/open_model_data/release/uldr_v06_general_assistant"
EVAL_DIR = RELEASE_DIR / "eval"
VESUM_DB = REPO_ROOT / "data/vesum.db"

# Import regex audit function
sys.path.insert(0, str(REPO_ROOT))
from scripts.projects.open_model_data.audit_assistant_quality import (
    audit_definitional_alignment,
)
from scripts.projects.open_model_data.v6_mine_general_assistant_textbooks import (
    get_vesum_cursor,
    is_definitional_for_concept,
)

logger = logging.getLogger(__name__)


def extract_json_block(text: str) -> list[dict]:
    """Extract JSON list from text or markdown codeblock."""
    m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
    if m:
        return json.loads(m.group(1))
    m2 = re.search(r"\[\s*\{[\s\S]*\}\s*\]", text)
    if m2:
        return json.loads(m2.group(0))
    raise ValueError(f"Could not parse JSON list from text:\n{text[:500]}")


def extract_snippet_from_record(r: dict) -> str:
    """Extract authentic textbook snippet from reasoning or reference solution."""
    for step in r.get("reference_reasoning", []):
        if "Текстологічна база" in step or "матеріал підручника" in step:
            m = re.search(r"[«„]([^»”]+)[»”]", step)
            if m:
                return m.group(1).strip()
    sol = r.get("reference_solution", "")
    m = re.search(r"\n[«„]([^»”\n]+)[»”]", sol)
    if m:
        return m.group(1).strip()
    for m in re.finditer(r"[«„]([^»”]+)[»”]", sol):
        cand = m.group(1).strip()
        if len(cand) > len(r.get("concept", "")) + 10:
            return cand
    return ""


def judge_batch_with_claude(batch: list[dict], batch_idx: int) -> list[dict]:
    """Send a batch of eval tasks to Claude via ask-claude bridge."""
    items_text = []
    for item in batch:
        snip = extract_snippet_from_record(item)
        item["extracted_snippet"] = snip
        items_text.append(
            f"Item {item['eval_id']}:\n"
            f"Subject: {item['subject']} (Grade {item['grade']})\n"
            f"Concept: {item['concept']}\n"
            f"Textbook Snippet: {snip}\n"
        )

    prompt = (
        "You are an independent Ukrainian curriculum and linguistic evaluator.\n"
        "For each textbook item below, determine whether the 'Textbook Snippet' constitutes a "
        "genuine, pedagogically valid scientific/academic definition of the 'Concept' (verdict: YES or NO).\n\n"
        "Guidelines:\n"
        "- YES (valid definition): The snippet clearly defines what the concept is (essential characteristics, "
        "genus + differentia, or core scholarly explanation in physics, biology, history, law, math, etc.).\n"
        "- NO (non-definition or defect): The snippet is merely a metaphor/figurative trope ('сторінка історії'), "
        "a quoted proverb ('Зміни місце...'), a negated assertion ('це не відмова...'), a contrastive concession "
        "('це теж закон, але...'), a restrictive copula ('це лише короткостроковий вияв...'), an evaluative/motivational "
        "commentary ('результат високого...', 'обов'язковий складник...', 'можливість дізнаватися...'), "
        "an example list ('це, наприклад,...'), a reader address ('ви будете пізнавати...'), "
        "an appositive clause with a finite verb instead of a copula definition ('Верхня палата – сенат – складалася...'), "
        "or a page-number splice ('... 10 Традиція – це...').\n\n"
        "Items to judge:\n"
        + "\n".join(items_text)
        + "\n\nRespond with ONLY a JSON list of objects with keys 'eval_id', 'verdict' ('YES' or 'NO'), and 'reason' (short string explanation)."
    )

    task_id = f"eval-seat-judge-b{batch_idx}"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/ai_agent_bridge/__main__.py"),
        "ask-claude",
        "-",
        "--from",
        "gemini-open-model-data",
        "--task-id",
        task_id,
    ]

    logger.info("Dispatching batch %d (%d items) to Claude...", batch_idx, len(batch))
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ask-claude failed for batch {batch_idx}: {proc.stderr}")

    parsed = extract_json_block(proc.stdout)
    return parsed


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.info("Starting independent seat evaluation of eval benchmark...")

    eval_files = sorted(EVAL_DIR.glob("eval_shard_*.jsonl"))
    if not eval_files:
        logger.error("No eval shards found in %s", EVAL_DIR)
        return 1

    all_records: list[dict] = []
    for f in eval_files:
        with f.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    all_records.append(json.loads(line))

    logger.info("Loaded %d eval benchmark records from %d shards.", len(all_records), len(eval_files))

    # Connect to VESUM for regex audit
    cur = get_vesum_cursor()

    cache_file = RELEASE_DIR / "eval_claude_verdicts.json"
    claude_verdicts: dict[str, dict] = {}
    if cache_file.exists():
        logger.info("Loading cached Claude verdicts from %s", cache_file)
        claude_verdicts = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        # Process in batches of 42
        batch_size = 42
        batches = [all_records[i : i + batch_size] for i in range(0, len(all_records), batch_size)]

        for idx, batch in enumerate(batches, 1):
            retries = 3
            while retries > 0:
                try:
                    results = judge_batch_with_claude(batch, idx)
                    for r in results:
                        claude_verdicts[r["eval_id"]] = r
                    break
                except Exception as e:
                    logger.warning("Batch %d failed (%s), retrying...", idx, e)
                    retries -= 1
                    if retries == 0:
                        raise
        cache_file.write_text(json.dumps(claude_verdicts, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved Claude verdicts to %s", cache_file)

    logger.info("Received Claude verdicts for %d / %d items.", len(claude_verdicts), len(all_records))

    # Compare with regex audit
    results_table: list[dict] = []
    disagreements: list[dict] = []

    for r in all_records:
        eid = r["eval_id"]
        concept = r["concept"]
        # Extract textbook snippet
        raw_snip = extract_snippet_from_record(r)

        # Regex audit check
        regex_audit_pass = audit_definitional_alignment(concept, raw_snip, cur)
        regex_miner_pass = is_definitional_for_concept(raw_snip, concept, cur)
        regex_verdict = "YES" if (regex_audit_pass and regex_miner_pass) else "NO"

        claude_info = claude_verdicts.get(eid, {"verdict": "UNKNOWN", "reason": "No response"})
        claude_verdict = claude_info.get("verdict", "UNKNOWN").upper()
        claude_reason = claude_info.get("reason", "")

        agreed = (regex_verdict == claude_verdict)
        item_res = {
            "eval_id": eid,
            "concept": concept,
            "subject": r["subject"],
            "grade": r["grade"],
            "snippet": raw_snip,
            "regex_verdict": regex_verdict,
            "claude_verdict": claude_verdict,
            "claude_reason": claude_reason,
            "agreed": agreed,
        }
        results_table.append(item_res)
        if not agreed:
            disagreements.append(item_res)

    # Generate Markdown Report
    report_lines = [
        "# Independent Non-Gemini Seat Judgment Report (Round 16)",
        "",
        "**Evaluation Seat:** Claude (Anthropic) via `ask-claude` bridge",
        f"**Total Eval Records Judged:** {len(all_records)}",
        f"**Regex Audit Consensus:** {len(all_records) - len(disagreements)} / {len(all_records)} ({((len(all_records) - len(disagreements)) / len(all_records) * 100):.1f}%)",
        f"**Total Disagreements:** {len(disagreements)}",
        "",
        "## Summary of Verdicts",
        f"- **Claude YES (Valid Definition):** {sum(1 for r in results_table if r['claude_verdict'] == 'YES')}",
        f"- **Claude NO (Non-Definition / Defect):** {sum(1 for r in results_table if r['claude_verdict'] == 'NO')}",
        f"- **Regex Audit YES:** {sum(1 for r in results_table if r['regex_verdict'] == 'YES')}",
        f"- **Regex Audit NO:** {sum(1 for r in results_table if r['regex_verdict'] == 'NO')}",
        "",
        "## Disagreements with Regex Audit",
    ]

    if not disagreements:
        report_lines.append("✅ **Zero disagreements.** Claude and the regex audit agreed on 100% of the eval records.\n")
    else:
        report_lines.append("| Eval ID | Concept | Subject | Regex Verdict | Claude Verdict | Claude Reasoning | Snippet |")
        report_lines.append("|---|---|---|---|---|---|---|")
        for d in disagreements:
            snip_esc = d["snippet"].replace("|", "\\|")
            report_lines.append(
                f"| `{d['eval_id']}` | **{d['concept']}** | {d['subject']} (Gr {d['grade']}) | `{d['regex_verdict']}` | `{d['claude_verdict']}` | {d['claude_reason']} | «{snip_esc}» |"
            )
        report_lines.append("")

    report_lines.append("## Full Record Ledger\n")
    report_lines.append("| # | Eval ID | Concept | Subject | Regex | Claude | Agreement | Claude Rationale |")
    report_lines.append("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(results_table, 1):
        agr_icon = "✅ AGREE" if r["agreed"] else "⚠️ DISAGREE"
        report_lines.append(
            f"| {i} | `{r['eval_id']}` | **{r['concept']}** | {r['subject']} | `{r['regex_verdict']}` | `{r['claude_verdict']}` | {agr_icon} | {r['claude_reason']} |"
        )

    out_path = RELEASE_DIR / "EVAL_INDEPENDENT_SEAT_JUDGMENT.md"
    out_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    logger.info("Wrote independent seat report to %s", out_path)

    print("\n================ INDEPENDENT SEAT JUDGMENT SUMMARY ================")
    print(f"Total Eval Records: {len(all_records)}")
    print(f"Agreements:         {len(all_records) - len(disagreements)} ({((len(all_records) - len(disagreements)) / len(all_records) * 100):.1f}%)")
    print(f"Disagreements:      {len(disagreements)}")
    print(f"Claude YES:         {sum(1 for r in results_table if r['claude_verdict'] == 'YES')}")
    print(f"Claude NO:          {sum(1 for r in results_table if r['claude_verdict'] == 'NO')}")
    print(f"Report Location:    {out_path}")
    print("===================================================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
