#!/usr/bin/env python3
"""Pipeline v6 — minimal LLM calls, no fix loops.

Phases:
  1. Preflight (writer, 1 call) — feasibility + Russianisms + coherence
  2. Write content (writer, 1 call) — .md only
  3. Write activities+vocab (writer, 1 call) — reads .md, produces YAMLs
  4. Deterministic audit (no LLM) — gates + plan adherence + stress verification
  5. Review + fix (reviewer, 1 call) — quality review AND audit fix
  6. Final audit (no LLM) — pass/fail, 1 YAML syntax retry

Issue: #960
"""
from __future__ import annotations

import logging
import re
import sys
import textwrap
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from batch_gemini_config import (
    FLASH_MODEL,
    PHASES_DIR,
    PRO_MODEL,
    slug_for_num,
)
from pipeline.core import (
    ModuleContext,
    _get_content_template,
    build_placeholders,
    fill_template,
    log,
    run_verify,
    write_review_with_hash,
)
from pipeline.dispatch import dispatch_gemini
from pipeline.prompt_preflight import run_prompt_preflight
from pipeline.screen import _deterministic_screen, _run_deterministic_fixes
from pipeline.state import (
    executor_deterministic,
    executor_llm,
    is_complete,
    load_state,
    mark_complete,
    mark_failed,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent-agnostic dispatch
# ---------------------------------------------------------------------------

def _dispatch(prompt: str, task_id: str, model: str, timeout: int = 900) -> tuple[bool, str]:
    """Dispatch to Gemini or Claude based on model name."""
    if model.startswith("claude"):
        return _dispatch_claude(prompt, model, timeout)
    return dispatch_gemini(prompt, task_id, model=model, stdout_only=True, timeout=timeout)


def _dispatch_claude(prompt: str, model: str, timeout: int = 900) -> tuple[bool, str]:
    """Call Claude CLI with plain prompt."""
    import shutil
    import subprocess as _sp

    claude_bin = shutil.which("claude") or "claude"
    cmd = [claude_bin, "--model", model, "-p", "--output-format", "text"]

    try:
        result = _sp.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            log(f"  dispatch: Claude error (rc={result.returncode}): {err[:200]}")
            return False, ""
        return True, result.stdout.strip()
    except FileNotFoundError:
        log("  dispatch: Claude CLI not found")
        return False, ""
    except _sp.TimeoutExpired:
        log(f"  dispatch: Claude timeout ({timeout}s)")
        return False, ""


# ---------------------------------------------------------------------------
# Phase 1: Preflight (reuses existing single-call preflight)
# ---------------------------------------------------------------------------

def phase_preflight(ctx: ModuleContext, state: dict) -> bool:
    """Preflight: feasibility + Russianisms + plan coherence."""
    phase = "preflight"
    if is_complete(state, phase):
        log("  preflight: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  preflight: DRY-RUN")
        return True

    def _dispatch(prompt_text):
        return dispatch_gemini(
            prompt_text, task_id="preflight",
            model=FLASH_MODEL, stdout_only=True, timeout=300,
        )

    result = run_prompt_preflight(
        ctx.paths["md"].parent / "content-prompt.md" if (ctx.paths["md"].parent / "content-prompt.md").exists()
        else ctx.orch_dir / "content-prompt.md",
        ctx.track, ctx.module_num, ctx.orch_dir,
        dispatch_fn=_dispatch,
        plan_path=ctx.paths.get("plan"),
    )

    if result.high_issues:
        # Try auto-fix Russianisms
        russicism_issues = [i for i in result.high_issues if i.issue_type == "RUSSICISM"]
        if russicism_issues:
            try:
                from plan_autofix import fix_russianisms_in_plan
                plan_path = ctx.paths.get("plan")
                if plan_path and plan_path.exists():
                    issue_dicts = [{"issue_type": i.issue_type, "problem": i.problem,
                                    "suggested_fix": i.suggested_fix} for i in russicism_issues]
                    n_fixes, _changes = fix_russianisms_in_plan(plan_path, issue_dicts)
                    if n_fixes > 0:
                        log(f"  preflight: Fixed {n_fixes} Russicism(s) in plan")
                        ctx.plan = yaml.safe_load(plan_path.read_text("utf-8"))
                        ctx.placeholders = {}
                        build_placeholders(ctx)
            except Exception as e:
                log(f"  preflight: Russicism auto-fix failed — {e}")

        non_russicism_high = [i for i in result.high_issues if i.issue_type != "RUSSICISM"]
        if non_russicism_high:
            log(f"  preflight: BLOCKED — {len(non_russicism_high)} HIGH issue(s)")
            for hi in non_russicism_high:
                log(f"    → {hi.problem[:150]}")
            mark_failed(state, phase, ctx, attempts=1, note="preflight-blocked",
                        executor=executor_llm("gemini", FLASH_MODEL))
            return False

    ctx.state.setdefault("phases", {}).setdefault(phase, {})["status"] = result.status
    mark_complete(state, phase, ctx, attempts=1, executor=executor_llm("gemini", FLASH_MODEL))
    return True


# ---------------------------------------------------------------------------
# Phase 2: Write content (.md only)
# ---------------------------------------------------------------------------

def phase_write_content(ctx: ModuleContext, state: dict) -> bool:
    """Write module content — single LLM call producing .md file."""
    phase = "content"
    if is_complete(state, phase):
        log("  content: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  content: DRY-RUN")
        return True

    # Build prompt from template
    template_name = _get_content_template(ctx.track, ctx.module_num, ctx.plan)
    template = PHASES_DIR / template_name
    if not template.exists():
        log(f"  content: Template not found: {template}")
        return False

    prompt_file = ctx.orch_dir / "content-prompt.md"
    sections = ctx.plan.get("content_outline", [])
    word_target = ctx.word_target
    overshoot = int(word_target * 1.2)

    overrides = {
        "OVERSHOOT_TARGET": str(overshoot),
        "SECTION_BUDGET_TABLE": _build_section_budget_table(sections, word_target),
        "FOLK_MATERIAL": getattr(ctx, "_folk_material", ""),
    }

    if not fill_template(template, ctx.placeholders, prompt_file, overrides=overrides):
        log("  content: Template fill failed")
        return False

    # Prepend curriculum context so the writer knows where this module sits
    prompt_text = prompt_file.read_text("utf-8")
    level = ctx.track.upper()
    title = ctx.plan.get("title", ctx.slug)
    subtitle = ctx.plan.get("subtitle", "")
    phase_label = ctx.plan.get("phase", "")
    prev_slug = slug_for_num(ctx.track, ctx.module_num - 1) if ctx.module_num > 1 else None
    next_slug = slug_for_num(ctx.track, ctx.module_num + 1)

    curriculum_header = (
        f"**Curriculum context:** This is Module {ctx.module_num} of the {level} track "
        f"(Ukrainian for English speakers). "
        f"Title: \"{title}\""
    )
    if subtitle:
        curriculum_header += f" — {subtitle}"
    if phase_label:
        curriculum_header += f". Phase: {phase_label}"
    if prev_slug:
        curriculum_header += f". Previous module: {prev_slug.replace('-', ' ').title()}"
    if next_slug:
        curriculum_header += f". Next module: {next_slug.replace('-', ' ').title()}"
    curriculum_header += ".\n\n"

    prompt_text = curriculum_header + prompt_text
    prompt_file.write_text(prompt_text, "utf-8")

    writer_model = getattr(ctx, "writer_model", ctx.model)
    log(f"  content: Dispatching write ({word_target}w target, {overshoot}w overshoot, model={writer_model})...")
    ok, raw = _dispatch(
        prompt_text,
        task_id=f"v6-{ctx.slug}-content",
        model=writer_model, timeout=900,
    )

    if not ok:
        log("  content: Dispatch failed")
        mark_failed(state, phase, ctx, attempts=1, note="dispatch-failed",
                    executor=executor_llm("gemini", ctx.model))
        return False

    # Extract content between delimiters
    content = _extract_content(raw)
    if not content:
        log("  content: No content extracted from response")
        mark_failed(state, phase, ctx, attempts=1, note="no-content",
                    executor=executor_llm("gemini", ctx.model))
        return False

    ctx.paths["md"].parent.mkdir(parents=True, exist_ok=True)
    ctx.paths["md"].write_text(content, "utf-8")
    word_count = len(content.split())
    log(f"  content: {word_count} words written ({word_count * 100 // word_target}% of {word_target} target)")

    mark_complete(state, phase, ctx, attempts=1, executor=executor_llm("gemini", ctx.model))
    return True


# ---------------------------------------------------------------------------
# Phase 3: Write activities + vocabulary
# ---------------------------------------------------------------------------

def phase_write_activities(ctx: ModuleContext, state: dict) -> bool:
    """Write activities YAML + vocabulary YAML — reads .md, produces YAMLs."""
    phase = "activities"
    if is_complete(state, phase):
        log("  activities: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  activities: DRY-RUN")
        return True

    content_text = ctx.paths["md"].read_text("utf-8") if ctx.paths["md"].exists() else ""
    if not content_text:
        log("  activities: No content file — skipping")
        return False

    plan_yaml = yaml.dump(ctx.plan, allow_unicode=True, default_flow_style=False)
    activity_hints = ctx.plan.get("activity_hints", [])
    vocab_hints = ctx.plan.get("vocabulary_hints", {})

    prompt = _build_activities_prompt(ctx, content_text, plan_yaml, activity_hints, vocab_hints)

    prompt_file = ctx.orch_dir / "activities-prompt.md"
    prompt_file.write_text(prompt, "utf-8")

    writer_model = getattr(ctx, "writer_model", ctx.model)
    log(f"  activities: Dispatching activities + vocabulary generation (model={writer_model})...")
    ok, raw = _dispatch(
        prompt,
        task_id=f"v6-{ctx.slug}-activities",
        model=writer_model, timeout=600,
    )

    if not ok:
        log("  activities: Dispatch failed")
        mark_failed(state, phase, ctx, attempts=1, note="dispatch-failed",
                    executor=executor_llm("gemini", ctx.model))
        return False

    # Extract and save activities YAML
    activities_yaml = _extract_delimited(raw, "===ACTIVITIES_START===", "===ACTIVITIES_END===")
    vocab_yaml = _extract_delimited(raw, "===VOCABULARY_START===", "===VOCABULARY_END===")

    if activities_yaml:
        acts_path = ctx.paths.get("activities") or (ctx.paths["md"].parent / "activities" / f"{ctx.slug}.yaml")
        acts_path.parent.mkdir(parents=True, exist_ok=True)
        acts_path.write_text(activities_yaml, "utf-8")
        log(f"  activities: Saved activities YAML ({len(activities_yaml)} chars)")
    else:
        log("  activities: WARNING — no activities extracted")

    if vocab_yaml:
        vocab_path = ctx.paths.get("vocabulary") or (ctx.paths["md"].parent / "vocabulary" / f"{ctx.slug}.yaml")
        vocab_path.parent.mkdir(parents=True, exist_ok=True)
        vocab_path.write_text(vocab_yaml, "utf-8")
        log(f"  activities: Saved vocabulary YAML ({len(vocab_yaml)} chars)")
    else:
        log("  activities: WARNING — no vocabulary extracted")

    mark_complete(state, phase, ctx, attempts=1, executor=executor_llm("gemini", ctx.model))
    return True


# ---------------------------------------------------------------------------
# Phase 4: Deterministic audit (no LLM)
# ---------------------------------------------------------------------------

def phase_audit(ctx: ModuleContext, state: dict) -> tuple[bool, str]:
    """Run deterministic audit — gates + plan adherence + stress verification.

    Returns (passed, audit_output) for use by review phase.
    """
    log("  audit: Running deterministic checks...")

    # Run deterministic fixes first
    _run_deterministic_fixes(ctx)

    # Screen (side effect: populates ctx with screen data for downstream checks)
    _deterministic_screen(ctx, skip_review=True)

    # Plan adherence
    plan_adherence_text = ""
    try:
        from audit.checks.plan_adherence import check_plan_adherence
        plan_path = ctx.paths.get("plan")
        md_path = ctx.paths.get("md")
        activities_path = ctx.paths.get("activities")
        if plan_path and md_path:
            result = check_plan_adherence(md_path, plan_path, activities_path or Path("/dev/null"))
            if result.issues:
                high = [i for i in result.issues if i.severity in ("CRITICAL", "HIGH")]
                medium = [i for i in result.issues if i.severity == "MEDIUM"]
                log(f"  audit: Plan adherence: {len(high)} HIGH, {len(medium)} MEDIUM")
                lines = ["## Plan Adherence Issues (MUST FIX)\n"]
                for issue in [*high, *medium]:
                    lines.append(f"- **[{issue.severity}] {issue.check_type}** in `{issue.section}`")
                    lines.append(f"  - Expected: {issue.expected}")
                    lines.append(f"  - Actual: {issue.actual}")
                    lines.append(f"  - Fix: {issue.fix_hint}")
                    lines.append("")
                plan_adherence_text = "\n".join(lines)
            else:
                log("  audit: Plan adherence: all checks passed")
    except ImportError:
        log("  audit: Plan adherence module not available")

    # Stress verification
    stress_issues = _verify_stress_marks(ctx)

    # Full audit
    passed, audit_output = run_verify(ctx.paths["md"])

    # Combine issues
    if plan_adherence_text:
        audit_output += "\n\n" + plan_adherence_text
        passed = False
    if stress_issues:
        audit_output += "\n\n" + stress_issues
        # Stress issues are auto-fixable, don't fail audit for them

    if passed:
        log("  audit: ALL GATES PASS")
    else:
        gate_failures = audit_output.count("❌")
        log(f"  audit: {gate_failures} gate failure(s)")

    return passed, audit_output


# ---------------------------------------------------------------------------
# Phase 5: Review + fix (reviewer, 1 call)
# ---------------------------------------------------------------------------

def phase_review_fix(ctx: ModuleContext, state: dict, audit_output: str) -> bool:
    """Review quality AND fix audit failures — single reviewer call."""
    phase = "review"
    if is_complete(state, phase):
        log("  review: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  review: DRY-RUN")
        return True

    # Build review+fix prompt
    content_text = ctx.paths["md"].read_text("utf-8") if ctx.paths["md"].exists() else ""
    activities_text = ""
    acts_path = ctx.paths.get("activities")
    if acts_path and acts_path.exists():
        activities_text = acts_path.read_text("utf-8")
    vocab_text = ""
    vocab_path = ctx.paths.get("vocabulary")
    if vocab_path and vocab_path.exists():
        vocab_text = vocab_path.read_text("utf-8")

    plan_yaml = yaml.dump(ctx.plan, allow_unicode=True, default_flow_style=False)

    prompt = _build_review_fix_prompt(
        ctx, content_text, activities_text, vocab_text, plan_yaml, audit_output,
    )

    prompt_file = ctx.orch_dir / "review-fix-prompt.md"
    prompt_file.write_text(prompt, "utf-8")

    reviewer_model = getattr(ctx, "reviewer_model", PRO_MODEL)
    log(f"  review: Dispatching review + fix (model={reviewer_model})...")
    ok, raw = _dispatch(
        prompt,
        task_id=f"v6-{ctx.slug}-review-fix",
        model=reviewer_model, timeout=900,
    )

    if not ok:
        log("  review: Dispatch failed")
        mark_failed(state, phase, ctx, attempts=1, note="dispatch-failed",
                    executor=executor_llm("gemini", PRO_MODEL))
        return False

    # Save raw output
    (ctx.orch_dir / "review-fix-raw.md").write_text(raw, "utf-8")

    # Extract review text
    review_text = _extract_delimited(raw, "===REVIEW_START===", "===REVIEW_END===")
    if review_text:
        write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
        (ctx.orch_dir / "review-result.md").write_text(review_text, "utf-8")
        log(f"  review: Review saved ({len(review_text.split())} words)")

    # Extract fixed content
    fixed_content = _extract_delimited(raw, "===CONTENT_START===", "===CONTENT_END===")
    if fixed_content and len(fixed_content.split()) > 100:
        ctx.paths["md"].write_text(fixed_content, "utf-8")
        log(f"  review: Fixed content saved ({len(fixed_content.split())} words)")

    # Extract fixed activities
    fixed_activities = _extract_delimited(raw, "===ACTIVITIES_START===", "===ACTIVITIES_END===")
    if fixed_activities:
        acts_path = ctx.paths.get("activities")
        if acts_path:
            acts_path.write_text(fixed_activities, "utf-8")
            log("  review: Fixed activities saved")

    # Extract fixed vocabulary
    fixed_vocab = _extract_delimited(raw, "===VOCABULARY_START===", "===VOCABULARY_END===")
    if fixed_vocab:
        vocab_path = ctx.paths.get("vocabulary")
        if vocab_path:
            vocab_path.write_text(fixed_vocab, "utf-8")
            log("  review: Fixed vocabulary saved")

    mark_complete(state, phase, ctx, attempts=1,
                  executor=executor_llm("gemini", PRO_MODEL))
    return True


# ---------------------------------------------------------------------------
# Phase 6: Final audit (no LLM)
# ---------------------------------------------------------------------------

def phase_final_audit(ctx: ModuleContext, state: dict) -> bool:
    """Final audit — pass/fail. One YAML syntax retry allowed."""
    phase = "final_audit"

    _run_deterministic_fixes(ctx)
    passed, audit_output = run_verify(ctx.paths["md"])

    if passed:
        log("  final: PASS — all gates green")
        mark_complete(state, phase, ctx, attempts=1,
                      executor=executor_deterministic("audit"))
        return True

    # One retry: if YAML parse errors, try to fix syntax
    if "YAML" in audit_output or "parse" in audit_output.lower():
        log("  final: YAML syntax issues detected — attempting auto-fix...")
        _fix_yaml_syntax(ctx)
        _run_deterministic_fixes(ctx)
        passed, audit_output = run_verify(ctx.paths["md"])
        if passed:
            log("  final: PASS (after YAML syntax fix)")
            mark_complete(state, phase, ctx, attempts=2,
                          executor=executor_deterministic("audit"))
            return True

    log("  final: FAIL — audit gates not met")
    log(f"  final: Output:\n{audit_output[:500]}")
    mark_failed(state, phase, ctx, attempts=2, note="final-audit-failed",
                executor=executor_deterministic("audit"))
    return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_section_budget_table(sections: list[dict], word_target: int) -> str:
    """Build section budget table from plan outline."""
    lines = ["| Section | Target Words |", "|---|---|"]
    for s in sections:
        section_name = s.get("section", "Untitled")
        words = s.get("words", 0)
        lines.append(f"| {section_name} | {words}+ |")
    lines.append(f"| **TOTAL** | **{word_target}+** (aim for ~{int(word_target * 1.2)}) |")
    return "\n".join(lines)


def _extract_content(raw: str) -> str:
    """Extract markdown content from LLM response."""
    # Try delimited extraction first
    content = _extract_delimited(raw, "===CONTENT_START===", "===CONTENT_END===")
    if content:
        return content

    # Fallback: strip markdown code fences and take everything
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:markdown|md)?\s*\n", "", cleaned)
    cleaned = re.sub(r"\n```\s*$", "", cleaned)

    # Remove any preamble before the first heading
    first_heading = re.search(r"^#{1,2}\s", cleaned, re.MULTILINE)
    if first_heading and first_heading.start() > 200:
        cleaned = cleaned[first_heading.start():]

    return cleaned.strip()


def _extract_delimited(raw: str, start: str, end: str) -> str:
    """Extract text between delimiters."""
    s = raw.find(start)
    e = raw.find(end)
    if s == -1 or e == -1 or e <= s:
        return ""
    return raw[s + len(start):e].strip()


def _verify_stress_marks(ctx: ModuleContext) -> str:
    """Verify stress marks in content using ukrainian-word-stress."""
    md_path = ctx.paths.get("md")
    if not md_path or not md_path.exists():
        return ""

    try:
        from ukrainian_word_stress import Stressifier, StressSymbol
    except ImportError:
        log("  audit: ukrainian-word-stress not installed — skipping stress check")
        return ""

    content = md_path.read_text("utf-8")

    # Find words with combining acute accent (U+0301)
    stressed_pattern = re.compile(r'(\b\w+\u0301\w*\b)')
    stressed_words = stressed_pattern.findall(content)

    if not stressed_words:
        return ""

    stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
    issues = []
    fixes_applied = 0

    for word in set(stressed_words):
        # Strip the stress mark to get the base form
        base = word.replace('\u0301', '')
        correct = stressifier(base)

        if correct != word and '\u0301' in correct:
            issues.append(f"  ❌ '{word}' → should be '{correct}'")
            # Auto-fix in content
            content = content.replace(word, correct)
            fixes_applied += 1

    if fixes_applied > 0:
        md_path.write_text(content, "utf-8")
        log(f"  audit: Fixed {fixes_applied} wrong stress mark(s)")

    if issues:
        return "## Stress Mark Issues\n\n" + "\n".join(issues)
    return ""


def _fix_yaml_syntax(ctx: ModuleContext) -> None:
    """Attempt basic YAML syntax fixes on activities and vocabulary files."""
    for key in ("activities", "vocabulary"):
        path = ctx.paths.get(key)
        if not path or not path.exists():
            continue
        try:
            yaml.safe_load(path.read_text("utf-8"))
        except yaml.YAMLError as e:
            log(f"  final: YAML syntax error in {key}: {e}")
            # Basic fixes: strip trailing whitespace, fix indentation
            text = path.read_text("utf-8")
            text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
            text = text.replace('\t', '  ')
            path.write_text(text, "utf-8")


def _load_activity_examples() -> str:
    """Load activity schema examples YAML for the prompt."""
    examples_path = PHASES_DIR / "activity-schema-examples.yaml"
    if examples_path.exists():
        return examples_path.read_text("utf-8")
    return "(activity examples not found)"


def _build_activities_prompt(
    ctx: ModuleContext, content_text: str, plan_yaml: str,
    activity_hints: list, vocab_hints: dict,
) -> str:
    """Build prompt for activities + vocabulary generation."""
    hints_text = yaml.dump(activity_hints, allow_unicode=True, default_flow_style=False) if activity_hints else "No activity hints in plan."
    vocab_text = yaml.dump(vocab_hints, allow_unicode=True, default_flow_style=False) if vocab_hints else "No vocabulary hints in plan."
    examples = _load_activity_examples()

    return textwrap.dedent(f"""\
        # Generate Activities and Vocabulary for: {ctx.slug}

        Read the module content below and produce TWO outputs:
        1. Activities YAML (interactive exercises that test the LANGUAGE skills taught)
        2. Vocabulary YAML (all Ukrainian words introduced in the content)

        ## Module Content

        ```markdown
        {content_text[:15000]}
        ```

        ## Plan Activity Hints

        ```yaml
        {hints_text}
        ```

        ## Plan Vocabulary Hints

        ```yaml
        {vocab_text}
        ```

        ## Activity YAML Schema — COPY THIS FORMAT EXACTLY

        Below are working examples for EVERY activity type. Your output MUST use the same
        field names. Wrong field names (e.g., `prompt` instead of `left`, `text` instead of
        `statement`) will cause validation failure.

        ```yaml
        {examples}
        ```

        **KEY RULES:**
        - `match-up` uses `pairs:` with `left:` / `right:` (NOT `items:` with `prompt:` / `answer:`)
        - `true-false` uses `statement:` (NOT `text:`)
        - `quiz` options use `text:` and `correct:` (bool)
        - `classify` uses `categories:` with `label:` and `items:`
        - `group-sort` uses `groups:` with `name:` and `items:`
        - NO `id` field on any activity — the system generates IDs
        - Minimum 6 items per activity
        - Minimum 8 activities total

        ## Vocabulary Rules
        - Extract ALL Ukrainian words taught in the content
        - Each entry: word, translation, part of speech, example sentence
        - Include words from vocabulary_hints.required (mandatory)
        - Include words from vocabulary_hints.recommended if used in content

        ## Output Format

        Output activities between these delimiters:
        ===ACTIVITIES_START===
        (bare YAML list — no `activities:` wrapper)
        ===ACTIVITIES_END===

        Output vocabulary between these delimiters:
        ===VOCABULARY_START===
        (YAML list of vocabulary entries)
        ===VOCABULARY_END===
    """)


def _build_review_fix_prompt(
    ctx: ModuleContext, content_text: str, activities_text: str,
    vocab_text: str, plan_yaml: str, audit_output: str,
) -> str:
    """Build prompt for combined review + fix."""
    return textwrap.dedent(f"""\
        # Review and Fix: {ctx.slug}

        You are reviewing a Ukrainian language module. Your job:
        1. Review the content for quality (language, pedagogy, engagement)
        2. Fix ALL audit failures listed below
        3. Return the corrected files

        ## Plan

        ```yaml
        {plan_yaml[:8000]}
        ```

        ## Current Content

        ```markdown
        {content_text[:20000]}
        ```

        ## Current Activities

        ```yaml
        {activities_text[:5000]}
        ```

        ## Current Vocabulary

        ```yaml
        {vocab_text[:3000]}
        ```

        ## Audit Results (MUST FIX ALL)

        ```
        {audit_output[:3000]}
        ```

        ## Review Criteria
        - Language quality: no Russianisms, natural Ukrainian, correct grammar
        - Plan adherence: all content_outline points covered, all required vocabulary present
        - Pedagogy: appropriate for the level, good pacing, engaging
        - Structure: proper section headers, Summary/Підсумок section present
        - Activities: test language skills (not content recall), sufficient items per activity

        ## Output Format

        First, output your review:
        ===REVIEW_START===
        (Your structured review with scores and specific issues found)
        ===REVIEW_END===

        Then, output ALL corrected files (even if unchanged):
        ===CONTENT_START===
        (Complete corrected markdown content)
        ===CONTENT_END===

        ===ACTIVITIES_START===
        (Complete corrected activities YAML — bare list, no wrapper)
        ===ACTIVITIES_END===

        ===VOCABULARY_START===
        (Complete corrected vocabulary YAML)
        ===VOCABULARY_END===

        **CRITICAL: Fix ALL audit failures. Every issue in the audit output must be addressed.
        Do not skip any. Count your fixes — if less than the number of issues, go back and fix more.**
    """)


# ---------------------------------------------------------------------------
# Main pipeline runner
# ---------------------------------------------------------------------------

def run_v6(ctx: ModuleContext) -> bool:
    """Run the v6 pipeline."""
    state = load_state(ctx)

    writer_model = getattr(ctx, "writer_model", ctx.model)
    reviewer_model = getattr(ctx, "reviewer_model", PRO_MODEL)

    log(f"\nPipeline v6: {ctx.slug}")
    log(f"  Track: {ctx.track}, Module: {ctx.module_num}")
    log(f"  Word target: {ctx.word_target}")
    log(f"  Writer: {writer_model}, Reviewer: {reviewer_model}")

    # Phase 1: Preflight
    if not phase_preflight(ctx, state):
        return False

    # Phase 2: Write content
    if not phase_write_content(ctx, state):
        return False

    # Phase 3: Write activities + vocabulary
    if not phase_write_activities(ctx, state):
        return False

    # Phase 4: Deterministic audit
    passed, audit_output = phase_audit(ctx, state)

    if passed:
        log("  pipeline: Audit passed — skipping review")
        # Still mark review as complete (no issues to fix)
        mark_complete(state, "review", ctx, attempts=0,
                      executor=executor_deterministic("audit-pass"))
        mark_complete(state, "final_audit", ctx, attempts=1,
                      executor=executor_deterministic("audit"))
        return True

    # Phase 5: Review + fix
    if not phase_review_fix(ctx, state, audit_output):
        return False

    # Phase 6: Final audit
    return phase_final_audit(ctx, state)
