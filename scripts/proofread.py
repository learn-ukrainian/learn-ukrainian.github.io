#!/usr/bin/env python3
"""Prose proofreading script for curriculum modules.

DEPRECATION NOTICE (pipeline use):
    As of 2026-02-25, proofreading's best features (track calibration, bilingual
    exemptions, Russianism lookup tables, LLM filler detection) have been absorbed
    into Phase D of build_module_v3.py. This script is no longer called as a pipeline
    step. It remains available as a **standalone dev tool** for ad-hoc quality checks
    and for calibration coverage testing (verifying Phase D catches everything
    proofread.py catches, per track, before fully deprecating).

Reads module content as a professional Ukrainian language editor would —
naturally, for coherence and language quality. Flags incoherent passages,
Russianisms, anglicisms, propaganda, and motivational filler.
Optionally auto-fixes via LLM rewrite.

Usage:
    .venv/bin/python scripts/proofread.py a1 17               # single module (dry-run)
    .venv/bin/python scripts/proofread.py a1 --range 1-10     # range
    .venv/bin/python scripts/proofread.py a1 --all            # all modules
    .venv/bin/python scripts/proofread.py a1 17 --fix         # auto-fix
    .venv/bin/python scripts/proofread.py a1 --all --agent gemini
    .venv/bin/python scripts/proofread.py a1 --all --agent claude
    .venv/bin/python scripts/proofread.py a1 17 --evaluate    # run dual-LLM evaluation

GitHub issue: #640
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from batch_gemini_config import (
    PRO_MODEL,
    PROJECT_ROOT,
    get_module_index,
    get_module_paths,
    slug_for_num,
)

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
CLAUDE_DEFAULT_MODEL = "claude-sonnet-4-6"
START_TAG = "===PROOFREAD_START==="
END_TAG = "===PROOFREAD_END==="


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
PROOFREAD_PROMPT_TEMPLATE = """\
You are an experienced Ukrainian language editor improving a {level_label} lesson for
English-speaking learners. Your job is NOT to strip content — it's to make weak passages
BETTER. Read the lesson naturally, paragraph by paragraph. When you find a passage that
doesn't work, rewrite it so it does. Your rewrites must be concrete, educational, and
match the voice and level of the surrounding content.

This is a {level_label} module. Calibrate your editing accordingly:
{track_calibration}
- A1/A2: BILINGUAL BY DESIGN. A1 is 0-30% Ukrainian, A2 is 30-55% Ukrainian. Mixing
  English explanations with Ukrainian examples is the correct pedagogy — do NOT flag this
  as LANGUAGE_BLENDER. Friendly, encouraging tone. Simple sentences are expected — don't
  flag short paragraphs as problems. Motivational encouragement woven into teaching is
  GOOD — keep it. Focus on: Russianisms, factual errors, and passages where fluff replaces
  actual teaching.
- B1 modules 1-5: Bilingual "Metalanguage Bridge" phase — same rules as A1/A2, do NOT
  flag bilingual content as LANGUAGE_BLENDER.
- B1 modules 6+, B2: Fully immersed (100% Ukrainian prose). Flag any English outside of
  vocabulary tables. Expect coherent paragraphs with logical flow. Flag disconnected ideas.
  Tone can be warmer than academic but should be substantive.
- C1/C2: Academic prose quality. Flag coherence, style, and any informality.

YOUR EDITING PRINCIPLES:
- IMPROVE, don't destroy. Every rewrite should teach MORE than the original, not less.
- PRESERVE the author's intent. If a paragraph tries to explain something but does it
  poorly, rewrite it to explain it well — don't delete it.
- MATCH the surrounding voice. Your rewrite should be invisible — it should read like
  the original author wrote it on a better day.
- Only use DELETE for truly empty sentences (pure cheerleading with zero information that
  cannot be salvaged into teaching content). This should be rare.

Flag and REWRITE these issues:

LANGUAGE (highest priority)
1. RUSSIANISM (ZERO TOLERANCE): Russian words, grammar patterns, Surzhyk, or imperial
   framing are NEVER acceptable. Replace each instance with its proper Ukrainian equivalent.
   Examples: здача → решта, вообще → взагалі, получити → отримати, добавити → додати,
   хватить → вистачить, обязательно → обов'язково. Severity: always HIGH.
   In seminar tracks (HIST, ISTORIOHRAFIIA, C1-BIO, LIT, OES, RUTH): also flag any imperial
   framing — "brotherly nations", "Little Russian", Soviet-era terminology for Ukrainian
   culture or history. Replace with Ukrainian academic standard terminology.
2. ANGLICISM: English syntax calqued into Ukrainian (e.g., "Я є студент" from "I am a
   student"). Rewrite using natural Ukrainian grammar.

COHERENCE
3. WORD_SALAD: Paragraphs that string together unrelated claims with no logical thread.
   Rewrite to pick ONE clear point and develop it properly.
4. INCOHERENT_CALLOUT: Callout boxes (>[!tip], >[!context], etc.) with disconnected ideas.
   Rewrite to have a single coherent message.
5. ORPHAN_SENTENCE: A sentence that doesn't connect to its neighbors. Rewrite to bridge
   the gap or merge it into an adjacent paragraph.

CONTENT QUALITY
6. LLM_FILLER: Generic AI-generated padding that sounds authoritative but says nothing.
   Telltale signs: "It's worth noting that...", "This is particularly important because...",
   "interestingly", "One of the key aspects", "Let's explore", "Let's dive in".
   Rewrite these into concrete, specific teaching content.
7. MOTIVATIONAL_FILLER: Full paragraphs of pure motivation with zero educational content.
   In core modules (A1-B2): rewrite to weave the encouragement into actual teaching.
   In seminar tracks: replace with substantive content. Only DELETE if truly unsalvageable.
8. DEAD_PARAGRAPH: A paragraph that could be deleted without any loss. Before deleting,
   ask: could this be rewritten to actually teach something useful here? If yes, rewrite.
9. LANGUAGE_BLENDER: Random Ukrainian/English alternation within a paragraph (not counting
   deliberate glossing like "word (translation)"). Rewrite for consistent language use.
   IMPORTANT: A1/A2 modules are intentionally bilingual (English explanations + Ukrainian
   examples). Do NOT flag bilingual teaching as LANGUAGE_BLENDER at these levels. Only flag
   truly jarring switches that break reading flow. At B2+ and seminar tracks, flag any
   unexpected language mixing.

SOURCE & FRAMING (seminar tracks especially)
10. SOURCE_VERIFICATION: Claims lacking clear academic basis, or based on Russian-language
    sources. Rewrite to ground in Ukrainian academic consensus, or flag for manual review.
11. HISTORICAL_INTEGRITY: Soviet/Russian imperial framing or non-standard interpretations.
    Rewrite to align with Ukrainian academic consensus.

For each issue, output:
- type: issue type from list above
- severity: HIGH (must fix) or LOW (nice to fix)
- location: section name where the issue appears
- text: the EXACT problematic text (preserve all markdown formatting)
- fix: your REWRITE that preserves all markdown formatting (bold, links, callout syntax, etc.)
  Use DELETE only as last resort for truly empty content.

IMPORTANT for YAML output:
- Use YAML block scalars (| or >) for text and fix fields to avoid quote escaping issues
- Do NOT modify YAML frontmatter (the --- block at the top of the file)

Output format:
===PROOFREAD_START===
issues:
  - type: WORD_SALAD
    severity: HIGH
    location: "Section name"
    text: |
      Ukraine is a very digital country. Prices are always written as digits.
      Being able to tell 50 from 15 is a real superpower in daily life.
    fix: |
      In Ukrainian shops and menus, prices are written as digits — so reading
      numbers quickly is a practical everyday skill. The difference between
      п'ятдесят (50) and п'ятнадцять (15) matters when you're paying!
  - type: LLM_FILLER
    severity: LOW
    location: "Section name"
    text: |
      It's worth noting that Ukrainian grammar has some interesting features
      that make it particularly unique among Slavic languages.
    fix: |
      Ukrainian uses seven grammatical cases, each changing a word's ending
      to show its role in a sentence.
===PROOFREAD_END===

If no issues found, output:
===PROOFREAD_START===
issues: []
===PROOFREAD_END===

CRITICAL: You MUST wrap your output in ===PROOFREAD_START=== and ===PROOFREAD_END=== delimiters.
Only output the structured YAML between delimiters. No commentary before or after.

---

MODULE CONTENT TO PROOFREAD:

"""

EVALUATE_PROMPT_TEMPLATE = """\
You are a senior Ukrainian language quality evaluator. Review the provided module content
and the proofreader's findings (issues).

EVALUATION CRITERIA (The proofreader used these definitions):
1. RUSSIANISM (ZERO TOLERANCE): Russian words, grammar patterns, Surzhyk, or imperial framing.
2. ANGLICISM: English syntax calqued into Ukrainian.
3. WORD_SALAD: Paragraphs that string together unrelated claims with no logical thread.
4. INCOHERENT_CALLOUT: Callout boxes with disconnected ideas.
5. ORPHAN_SENTENCE: A sentence that doesn't connect to its neighbors.
6. LLM_FILLER: Generic AI-generated padding that sounds authoritative but says nothing.
7. MOTIVATIONAL_FILLER: Full paragraphs of pure motivation with zero educational content.
8. DEAD_PARAGRAPH: A paragraph that could be deleted without any loss.
9. LANGUAGE_BLENDER: Random Ukrainian/English alternation within a paragraph. (A1/A2/B1.1-5 are intentionally bilingual).
10. SOURCE_VERIFICATION: Claims lacking clear academic basis, or based on Russian-language sources.
11. HISTORICAL_INTEGRITY: Soviet/Russian imperial framing or non-standard interpretations.

For EACH issue found by the proofreader, evaluate:
- correct_diagnosis: Is this text actually problematic based on the definitions? (yes/no)
- rewrite_acceptable: Does the rewrite improve the text, preserve intent, and maintain voice? (yes/no)
- no_new_errors: Is the rewrite free of new grammar/factual errors? (yes/no)

MISSED ISSUES:
Did the proofreader miss anything critical?
ONLY list missed Russianisms, factual errors, or broken markdown. Do NOT list stylistic preferences.

Output ONLY the YAML block, no commentary.

Format:
===EVALUATE_START===
evaluations:
  - issue_index: 1
    correct_diagnosis: yes
    rewrite_acceptable: yes
    no_new_errors: yes
missed_issues:
  - type: RUSSIANISM
    text: "..."
    fix_suggestion: "..."
===EVALUATE_END===

---
MODULE CONTENT:
{content}

---
PROOFREADER FINDINGS:
{findings}
"""


# ---------------------------------------------------------------------------
# LLM dispatch
# ---------------------------------------------------------------------------
def dispatch_gemini(prompt: str, task_id: str, model: str, timeout: int = 1800) -> tuple[bool, str]:
    """Dispatch prompt to Gemini via ai_agent_bridge.py ask-gemini (stdin pipe)."""
    args = [
        VENV_PYTHON,
        str(SCRIPTS_DIR / "ai_agent_bridge.py"), "ask-gemini",
        "-",  # read prompt from stdin
        "--task-id", task_id,
        "--model", model,
        "--stdout-only",
    ]
    try:
        result = subprocess.run(
            args, capture_output=True, text=True,
            input=prompt,
            timeout=timeout, cwd=str(PROJECT_ROOT),
        )
        return result.returncode == 0, result.stdout or ""
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT: Gemini dispatch {task_id} exceeded {timeout}s")
        return False, ""


def dispatch_claude(
    prompt: str, task_id: str, model: str, timeout: int = 600,
    start_tag: str = START_TAG, end_tag: str = END_TAG
) -> tuple[bool, str]:
    """Dispatch prompt to Claude CLI headlessly."""
    claude_bin = shutil.which("claude") or "claude"
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    cmd = [claude_bin, "--model", model, "-p", "--output-format", "text"]
    cmd.extend(["--append-system-prompt",
                 f"CRITICAL: Your output MUST contain {start_tag} and "
                 f"{end_tag} delimiters wrapping the structured YAML. "
                 "Output without these delimiters is automatically discarded."])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            input=prompt, timeout=timeout,
            cwd=str(PROJECT_ROOT), env=env,
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            log(f"  Claude CLI error (rc={result.returncode}): {err[:300]}")
            return False, ""
        return True, result.stdout.strip()
    except FileNotFoundError:
        log("  Claude CLI not found — ensure 'claude' is on PATH")
        return False, ""
    except subprocess.TimeoutExpired:
        log(f"  Claude CLI TIMEOUT ({timeout}s)")
        return False, ""


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------
def _extract_delimiter_tolerant(text: str, start_tag: str, end_tag: str) -> dict | list | None:
    if start_tag not in text:
        return None

    # Try exact extraction
    s = text.rindex(start_tag) + len(start_tag)
    if end_tag in text[s:]:
        e = text.index(end_tag, s)
        raw = text[s:e].strip()
    else:
        # Tolerant: start tag present, end tag missing
        raw = text[s:]
        lines = raw.split("\n")
        yaml_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("─") or stripped.startswith("✅"):
                break
            if stripped.startswith("===") and stripped.endswith("==="):
                break
            yaml_lines.append(line)
        while yaml_lines and not yaml_lines[-1].strip():
            yaml_lines.pop()
        raw = "\n".join(yaml_lines).strip()

    if not raw:
        return None

    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        log(f"  YAML parse error: {exc}")
        return None

    return parsed


def extract_proofread_output(text: str) -> list[dict] | None:
    """Extract issues list from delimited LLM output. Returns None on parse failure."""
    parsed = _extract_delimiter_tolerant(text, START_TAG, END_TAG)
    if isinstance(parsed, dict) and "issues" in parsed:
        issues = parsed["issues"]
        if issues is None:
            return []
        return issues if isinstance(issues, list) else None

    return None


# ---------------------------------------------------------------------------
# Fix application
# ---------------------------------------------------------------------------
def apply_fixes(md_path: Path, issues: list[dict]) -> int:
    """Apply fixes from proofread issues to the .md file. Returns count of fixes applied."""
    content = md_path.read_text("utf-8")
    fixes_applied = 0

    for issue in issues:
        text = issue.get("text", "").rstrip()
        fix = issue.get("fix", "").rstrip()
        if not text or not fix:
            continue

        if text not in content:
            log(f"  SKIP (text not found): {text[:60]}...")
            continue

        if fix.upper() == "DELETE":
            # Replace first occurrence only, clean up resulting blank lines
            content = content.replace(text, "", 1)
            # Collapse triple+ newlines to double
            while "\n\n\n" in content:
                content = content.replace("\n\n\n", "\n\n")
            fixes_applied += 1
            log(f"  DELETED: {text[:60]}...")
        else:
            # Replace first occurrence only to avoid global corruption
            content = content.replace(text, fix, 1)
            fixes_applied += 1
            log(f"  FIXED: {text[:60]}...")

    if fixes_applied > 0:
        md_path.write_text(content, "utf-8")

    return fixes_applied


def run_audit(md_path: Path) -> bool:
    """Run audit_module.py on the file. Returns True if passed."""
    result = subprocess.run(
        [VENV_PYTHON, str(SCRIPTS_DIR / "audit_module.py"), str(md_path)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    return result.returncode == 0


def regenerate_mdx(level: str, num: int) -> bool:
    """Regenerate MDX via generate_mdx.py. Returns True on success."""
    result = subprocess.run(
        [VENV_PYTHON, str(SCRIPTS_DIR / "generate_mdx.py"), "l2-uk-en", level, str(num)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Core proofreading
# ---------------------------------------------------------------------------
def proofread_module(
    level: str, num: int, slug: str,
    agent: str, model: str,
    fix: bool, verbose: bool,
    no_mdx: bool = False,
) -> tuple[list[dict], str]:
    """Proofread a single module. Returns tuple of (list of issues, stripped content)."""
    paths = get_module_paths(level, slug)
    md_path = Path(paths["md"])

    if not md_path.exists():
        log(f"  SKIP: {md_path} does not exist")
        return [], ""

    raw_content = md_path.read_text("utf-8")
    if not raw_content.strip():
        log(f"  SKIP: {md_path} is empty")
        return [], ""

    # Strip YAML frontmatter before sending to LLM (avoid accidental edits)
    content = raw_content
    if content.startswith("---"):
        end_fm = content.find("\n---", 3)
        if end_fm != -1:
            content = content[end_fm + 4:].lstrip("\n")

    # Determine track-specific calibration
    track_calib = ""
    if level in ["hist", "istoriohrafiia"]:
        track_calib = "- TRACK CALIBRATION (HISTORY): Historical narrative. Expect structured storytelling, debunking of imperial/Soviet myths, and factual recounting of events based strictly on Ukrainian academic sources. Flag any Russian imperial framing."
    elif level == "c1-bio":
        track_calib = "- TRACK CALIBRATION (C1-BIO): Biographical narrative. Expect formal recounting of life events, legacy, and societal impact based on Ukrainian academic consensus. Flag subjective, overly dramatic framing, or imperial bias."
    elif level == "lit":
        track_calib = "- TRACK CALIBRATION (LIT): Literary analysis. Expect poetic terms, analysis of stylistics, and discussion of literary movements. Flag non-academic interpretations."
    elif level in ["oes", "ruth"]:
        track_calib = "- TRACK CALIBRATION (OES/RUTH): Old East Slavic and Ruthenian historical linguistics. Expect highly academic analysis of historical texts and linguistic evolution. Flag anachronisms or Soviet linguistic framing."
    else:
        track_calib = "- TRACK CALIBRATION (CORE): Core language acquisition. Expect practical grammar, everyday vocabulary, and conversational scenarios."

    # Build prompt — use concatenation, not .format(), to avoid crashes on {braces}
    level_label = level.upper()
    prompt = PROOFREAD_PROMPT_TEMPLATE.replace("{level_label}", level_label).replace("{track_calibration}", track_calib) + content
    # Include model short name in task_id to avoid collisions in parallel runs
    model_short = model.split("/")[-1].split("-preview")[0].replace(".", "")
    task_id = f"proofread-{slug}-{model_short}"

    log(f"\n{'='*60}")
    log(f"Proofreading: {level}/{slug} (module {num})")
    log(f"  Agent: {agent} | Model: {model}")
    log(f"  Content: {len(raw_content)} chars, {len(raw_content.split())} words")

    if agent == "gemini":
        ok, output = dispatch_gemini(prompt, task_id, model)
    else:
        ok, output = dispatch_claude(prompt, task_id, model)

    if not ok:
        log(f"  ERROR: LLM dispatch failed for {slug}")
        return [], content

    if verbose:
        log(f"\n--- LLM OUTPUT ---\n{output}\n--- END OUTPUT ---\n")

    issues = extract_proofread_output(output)
    if issues is None:
        log(f"  ERROR: Could not parse proofread output for {slug}")
        if verbose:
            log(f"  Raw output snippet: {output[:500]}")
        return [], content

    if not issues:
        log(f"  CLEAN: No issues found in {slug}")
        return [], content

    # Print issues
    high_count = sum(1 for i in issues if i.get("severity") == "HIGH")
    low_count = len(issues) - high_count
    log(f"  FOUND: {len(issues)} issues ({high_count} HIGH, {low_count} LOW)")

    for i, issue in enumerate(issues, 1):
        severity = issue.get("severity", "?")
        itype = issue.get("type", "UNKNOWN")
        location = issue.get("location", "?")
        text_preview = (issue.get("text", ""))[:80]
        fix_preview = (issue.get("fix", ""))[:80]
        marker = "!!" if severity == "HIGH" else "  "
        log(f"  {marker} [{severity}] {itype} @ {location}")
        log(f"       Text: {text_preview}...")
        if fix_preview:
            log(f"       Fix:  {fix_preview}...")

    # Apply fixes if requested
    if fix and issues:
        log(f"\n  Applying fixes to {md_path.name}...")
        applied = apply_fixes(md_path, issues)
        log(f"  Applied {applied}/{len(issues)} fixes")

        if applied > 0:
            log("  Running post-fix audit...")
            audit_ok = run_audit(md_path)
            log(f"  Audit: {'PASS' if audit_ok else 'FAIL'}")

            if not no_mdx:
                log("  Regenerating MDX...")
                mdx_ok = regenerate_mdx(level, num)
                log(f"  MDX: {'OK' if mdx_ok else 'FAIL'}")
            else:
                log("  Skipping MDX regeneration (--no-mdx)")

    return issues, content


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_module(level: str, num: int, slug: str, issues: list[dict], content: str) -> dict:
    # Fix #1: Inject explicit 1-based index so LLMs don't miscount
    indexed_issues = []
    for j, iss in enumerate(issues, 1):
        indexed = dict(iss)
        indexed["issue_index"] = j
        indexed_issues.append(indexed)
    findings_yaml = yaml.dump({"issues": indexed_issues}, allow_unicode=True, sort_keys=False)
    prompt = EVALUATE_PROMPT_TEMPLATE.replace("{content}", content).replace("{findings}", findings_yaml)
    
    log(f"\n{'='*60}")
    log(f"Evaluating: {level}/{slug} (module {num})")
    
    # 1. Dispatch Gemini Pro
    task_id_gem = f"eval-{slug}-gemini"
    log("  Dispatching to Gemini Pro...")
    ok_gem, out_gem = dispatch_gemini(prompt, task_id_gem, "gemini-3.1-pro-preview")
    
    gemini_eval = None
    if ok_gem:
        parsed = _extract_delimiter_tolerant(out_gem, "===EVALUATE_START===", "===EVALUATE_END===")
        if isinstance(parsed, dict):
            gemini_eval = parsed
    
    # 2. Dispatch Claude Opus
    task_id_claude = f"eval-{slug}-claude"
    log("  Dispatching to Claude Opus...")
    ok_claude, out_claude = dispatch_claude(
        prompt, task_id_claude, "claude-opus-4-6", timeout=900,
        start_tag="===EVALUATE_START===", end_tag="===EVALUATE_END==="
    )
    
    claude_eval = None
    if ok_claude:
        parsed = _extract_delimiter_tolerant(out_claude, "===EVALUATE_START===", "===EVALUATE_END===")
        if isinstance(parsed, dict):
            claude_eval = parsed
            
    if claude_eval is None:
        log("  Opus unavailable or failed. Evaluating with Gemini only.")

    # 3. Print per-module summary table and aggregate metrics
    log(f"\n  === Evaluation: {level}/{slug} ===")
    
    # Fix #4: Use :<2 for issue index to handle double digits
    log("  | #  | Type       | Sev  | Pro: Correct? | Pro: Apply? | Opus: Correct? | Opus: Apply? | Agreement |")
    log("  |----|------------|------|---------------|-------------|----------------|--------------|-----------|")
    
    def get_eval_row(e_list, idx):
        """Fix #3: Cast both sides to str to handle LLM typing quirks (quoted vs unquoted ints)."""
        if not e_list: return None
        for item in e_list:
            if str(item.get("issue_index")) == str(idx):
                return item
        return None
        
    metrics = {"correct": 0, "apply": 0, "safe": 0}
    
    for i, issue in enumerate(issues, 1):
        itype = issue.get("type", "UNKNOWN")
        sev = issue.get("severity", "?")
        
        gem_row = get_eval_row(gemini_eval.get("evaluations", []) if gemini_eval else [], i)
        cla_row = get_eval_row(claude_eval.get("evaluations", []) if claude_eval else [], i)
        
        g_c = str(gem_row.get("correct_diagnosis", "n/a")).lower() if gem_row else "n/a"
        g_a = str(gem_row.get("rewrite_acceptable", "n/a")).lower() if gem_row else "n/a"
        g_s = str(gem_row.get("no_new_errors", "n/a")).lower() if gem_row else "n/a"
        
        c_c = str(cla_row.get("correct_diagnosis", "n/a")).lower() if cla_row else "n/a"
        c_a = str(cla_row.get("rewrite_acceptable", "n/a")).lower() if cla_row else "n/a"
        c_s = str(cla_row.get("no_new_errors", "n/a")).lower() if cla_row else "n/a"
        
        # Fix #2: Check all 3 dimensions for agreement (including safety)
        agreement = "AGREE"
        if g_c != "n/a" and c_c != "n/a":
            _yes = ["yes", "true", "1"]
            if (g_c in _yes) != (c_c in _yes):
                agreement = "DISAGREE"
            if (g_a in _yes) != (c_a in _yes):
                agreement = "DISAGREE"
            if (g_s in _yes) != (c_s in _yes):
                agreement = "DISAGREE"
        elif g_c == "n/a" and c_c == "n/a":
            agreement = "N/A"
        else:
            agreement = "PARTIAL"
            
        valid_evals = 0
        correct_yes = 0
        apply_yes = 0
        safe_yes = 0
        
        for row in [gem_row, cla_row]:
            if row:
                valid_evals += 1
                if str(row.get("correct_diagnosis", "")).lower() in ["yes", "true", "1"]: correct_yes += 1
                if str(row.get("rewrite_acceptable", "")).lower() in ["yes", "true", "1"]: apply_yes += 1
                if str(row.get("no_new_errors", "")).lower() in ["yes", "true", "1"]: safe_yes += 1
                
        if valid_evals > 0:
            metrics["correct"] += (correct_yes / valid_evals)
            metrics["apply"] += (apply_yes / valid_evals)
            metrics["safe"] += (safe_yes / valid_evals)
            
        g_c_str = "yes" if g_c in ["yes", "true", "1"] else ("no" if g_c in ["no", "false", "0"] else g_c)
        g_a_str = "yes" if g_a in ["yes", "true", "1"] else ("no" if g_a in ["no", "false", "0"] else g_a)
        c_c_str = "yes" if c_c in ["yes", "true", "1"] else ("no" if c_c in ["no", "false", "0"] else c_c)
        c_a_str = "yes" if c_a in ["yes", "true", "1"] else ("no" if c_a in ["no", "false", "0"] else c_a)
        
        short_itype = itype[:10] if len(itype) > 10 else itype
        
        log(f"  | {i:<2} | {short_itype:<10} | {sev:<4} | {g_c_str:<13} | {g_a_str:<11} | {c_c_str:<14} | {c_a_str:<12} | {agreement:<9} |")
        
    prec = (metrics["correct"] / len(issues)) * 100 if len(issues) > 0 else 0
    rewr = (metrics["apply"] / len(issues)) * 100 if len(issues) > 0 else 0
    safe = (metrics["safe"] / len(issues)) * 100 if len(issues) > 0 else 0
    log(f"\n  Precision: {prec:.0f}% | Rewrite quality: {rewr:.0f}% | Safety: {safe:.0f}%")
        
    out_dir = PROJECT_ROOT / "tests" / "proofread-results"
    out_dir.mkdir(parents=True, exist_ok=True)
    res = {
        "level": level,
        "slug": slug,
        "issues_count": len(issues),
        "metrics": {
            "precision": prec,
            "rewrite_quality": rewr,
            "safety": safe,
        },
        "gemini": gemini_eval,
        "claude": claude_eval,
    }
    out_file = out_dir / f"eval-{level}-{slug}.json"
    out_file.write_text(json.dumps(res, indent=2, ensure_ascii=False), "utf-8")
    log(f"  Saved evaluation to tests/proofread-results/eval-{level}-{slug}.json")

    return res


# ---------------------------------------------------------------------------
# Module resolution
# ---------------------------------------------------------------------------
def resolve_modules(level: str, num: int | None, build_all: bool, build_range: str | None) -> list[int]:
    """Resolve which module numbers to process."""
    index = get_module_index(level)
    total = index["total"]

    if build_all:
        return list(range(1, total + 1))

    if build_range:
        parts = build_range.split("-")
        if len(parts) != 2:
            log(f"ERROR: Invalid range format '{build_range}'. Use N-M (e.g. 1-20)")
            sys.exit(2)
        start, end = int(parts[0]), int(parts[1])
        if start < 1 or end > total or start > end:
            log(f"ERROR: Range {start}-{end} out of bounds (1-{total})")
            sys.exit(2)
        return list(range(start, end + 1))

    if num is not None:
        if num < 1 or num > total:
            log(f"ERROR: Module {num} out of bounds (1-{total})")
            sys.exit(2)
        return [num]

    log("ERROR: Specify a module number, --all, or --range")
    sys.exit(2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Proofread curriculum modules for coherence, language quality, and content integrity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s a1 17               Single module (dry-run by default)
  %(prog)s a1 --range 1-10     Range of modules
  %(prog)s a1 --all            All modules in level
  %(prog)s a1 17 --fix         Auto-fix flagged passages
  %(prog)s a1 --all --agent claude --verbose
  %(prog)s a1 17 --evaluate    Run independent dual-LLM evaluation
""",
    )
    parser.add_argument("level", help="Track identifier (a1, a2, b1, etc.)")
    parser.add_argument("num", type=int, nargs="?", default=None,
                        help="1-indexed module number (optional with --all or --range)")
    parser.add_argument("--all", action="store_true", dest="build_all",
                        help="Process all modules in the track")
    parser.add_argument("--range", type=str, default=None, dest="build_range",
                        help="Process range of modules (e.g. 1-20)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print findings only, don't write fixes (default behavior)")
    parser.add_argument("--fix", action="store_true",
                        help="Apply LLM-generated rewrites to content files")
    parser.add_argument("--agent", choices=["gemini", "claude"], default="gemini",
                        help="Which LLM to use (default: gemini)")
    parser.add_argument("--model", type=str, default=None,
                        help="Override specific model (e.g. gemini-3.1-pro-preview)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full LLM output, not just summary")
    parser.add_argument("--evaluate", action="store_true",
                        help="Run independent quality evaluation by Gemini and Claude")
    parser.add_argument("--no-mdx", action="store_true", dest="no_mdx",
                        help="Skip MDX regeneration after fixes (for pipeline integration)")

    args = parser.parse_args()

    # Resolve model
    if args.model:
        model = args.model
    elif args.agent == "gemini":
        model = "gemini-3.1-pro-preview"
    else:
        model = CLAUDE_DEFAULT_MODEL

    # Resolve modules
    modules = resolve_modules(args.level, args.num, args.build_all, args.build_range)

    log(f"Proofread: {args.level} | {len(modules)} module(s) | agent={args.agent} | model={model}")
    if args.fix:
        log("Mode: FIX (will apply rewrites)")
    else:
        log("Mode: DRY-RUN (print findings only)")

    total_issues: list[dict] = []
    modules_with_issues = 0

    for num in modules:
        try:
            slug = slug_for_num(args.level, num)
        except (ValueError, KeyError) as exc:
            log(f"  SKIP module {num}: {exc}")
            continue

        issues, content = proofread_module(
            level=args.level,
            num=num,
            slug=slug,
            agent=args.agent,
            model=model,
            fix=args.fix,
            verbose=args.verbose,
            no_mdx=getattr(args, "no_mdx", False),
        )
        total_issues.extend(issues)
        if issues:
            modules_with_issues += 1
            if args.evaluate:
                evaluate_module(args.level, num, slug, issues, content)

    # Summary
    log(f"\n{'='*60}")
    log(f"SUMMARY: {len(modules)} modules scanned")
    log(f"  Modules with issues: {modules_with_issues}")
    log(f"  Total issues: {len(total_issues)}")
    high = sum(1 for i in total_issues if i.get("severity") == "HIGH")
    low = len(total_issues) - high
    log(f"  HIGH: {high} | LOW: {low}")

    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(main())
