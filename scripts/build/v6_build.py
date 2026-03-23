#!/usr/bin/env python3
"""V6 Pipeline Build — two-call Skeleton->Flesh content generation.

Orchestrates the V6 pipeline:
1. CHECK: Plan checker validation
2. RESEARCH: Build knowledge packet from RAG
3. SKELETON: Paragraph-level structure plan (auto for word_target >= 3000)
4. WRITE: LLM session constrained by skeleton (prose + exercises)
5b. EXERCISES: Fill placeholders with DSL
6. ANNOTATE: Stress marks + deterministic fixes
7b. ENRICH: Словник, videos, resources, dialogue formatting
7. VERIFY: VESUM + grammar scope
8. REVIEW: Cross-agent adversarial review
9. PUBLISH: DSL→MDX conversion

The Skeleton->Flesh architecture (#998) splits content generation into two calls
for modules with word_target >= 3000:
- Call 1 (Skeleton): Short output (~500-800 words) planning every paragraph
- Call 2 (Flesh): Full prose following the skeleton exactly

This prevents frontloading early sections and rushing later ones.
Modules under 3000 words (e.g., A1) skip the skeleton step.

Usage:
    .venv/bin/python scripts/build/v6_build.py a1 1
    .venv/bin/python scripts/build/v6_build.py b1 1 --skeleton    # force skeleton
    .venv/bin/python scripts/build/v6_build.py b1 1 --no-skeleton # skip skeleton
    .venv/bin/python scripts/build/v6_build.py a1 1 --step write  # run single step
    .venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini  # default
    .venv/bin/python scripts/build/v6_build.py a1 1 --writer claude

Issue: #993, #998
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

logger = logging.getLogger(__name__)

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
PHASES_DIR = PROJECT_ROOT / "scripts" / "build" / "phases"


def _log(msg: str):
    print(msg, flush=True)


def _save_v6_state(level: str, slug: str, step: str, status: str = "complete"):
    """Write V6 pipeline state in V5-compatible format."""
    import json
    from datetime import datetime

    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    state_path = orch_dir / "state.json"

    # Load existing state or create new
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
        except Exception:
            state = {}
    else:
        state = {}

    # V6 uses mode "v6" — API will detect this
    state["mode"] = "v6"
    state["track"] = level
    state["slug"] = slug

    # Map V6 steps to phase entries
    phases = state.get("phases", {})
    phases[step] = {
        "status": status,
        "ts": datetime.now(tz=UTC).isoformat(),
    }
    state["phases"] = phases

    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def step_check(level: str, module_num: int, slug: str) -> bool:
    """Step 2: Run deterministic plan checker."""
    _log(f"\n{'='*60}")
    _log("  Step 2: CHECK — Plan validation")
    _log(f"{'='*60}")

    from audit.check_plan import check_plan

    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        _log(f"  ❌ Plan not found: {plan_path}")
        return False

    # Load all slugs for prerequisite checking
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    all_slugs = data.get("levels", {}).get(level, {}).get("modules", [])

    issues = check_plan(plan_path, all_slugs)
    errors = [i for i in issues if i.severity == "ERROR"]

    if errors:
        _log(f"  ❌ Plan check FAILED ({len(errors)} error(s)):")
        for issue in errors:
            _log(f"    {issue}")
        return False

    warnings = [i for i in issues if i.severity == "WARNING"]
    if warnings:
        _log(f"  ⚠️  Plan check PASSED with {len(warnings)} warning(s)")
    else:
        _log("  ✅ Plan check PASSED")
    return True


def step_research(level: str, module_num: int, slug: str) -> Path | None:
    """Step 3: Build knowledge packet from RAG."""
    _log(f"\n{'='*60}")
    _log("  Step 3: RESEARCH — Knowledge packet")
    _log(f"{'='*60}")

    from research.build_knowledge_packet import build_packet

    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    output_dir = CURRICULUM_ROOT / level / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}-knowledge-packet.md"

    _log("  Building knowledge packet from plan + RAG...")
    packet = build_packet(plan_path)
    output_path.write_text(packet, "utf-8")

    result_count = packet.count("> **Source:**")
    _log(f"  ✅ Knowledge packet built ({result_count} textbook excerpts)")
    _log(f"  → {output_path}")

    # Assess research quality (AC: assess_research.py can score the packet)
    try:
        from research.research_quality import assess_research_compat

        assessment = assess_research_compat(output_path, level)
        if assessment and assessment.get("score") is not None:
            score = assessment["score"]
            quality = assessment.get("quality", "unknown")
            _log(f"  Research quality: {score}/10 ({quality})")

            if score < 7:
                _log("  ⚠️  Research quality below 7/10 — topic may have limited textbook coverage")

            # Save assessment to orchestration directory
            import json
            orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
            orch_dir.mkdir(parents=True, exist_ok=True)
            assess_path = orch_dir / "research-quality.json"
            assess_path.write_text(
                json.dumps(assessment, indent=2, ensure_ascii=False, default=str),
                "utf-8",
            )
        else:
            _log("  ℹ️  Research quality: no rubric for this track")
    except Exception as e:
        _log(f"  ⚠️  Research quality assessment failed: {e}")

    return output_path


def step_skeleton(level: str, module_num: int, slug: str,
                  packet_path: Path, writer: str = "gemini") -> str | None:
    """Step 4: Generate paragraph-level skeleton for large modules.

    Produces a detailed structural plan (~500-800 words) that constrains
    the writer to balanced sections, preventing frontloading and rushed endings.

    Returns the skeleton text, or None on failure.
    """
    _log(f"\n{'='*60}")
    _log(f"  Step 4: SKELETON — Structure planning ({writer})")
    _log(f"{'='*60}")

    # Load template
    template_path = PHASES_DIR / "v6-skeleton.md"
    if not template_path.exists():
        _log(f"  ❌ Template not found: {template_path}")
        return None

    template = template_path.read_text("utf-8")

    # Load plan
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan_content = plan_path.read_text("utf-8")
    plan = yaml.safe_load(plan_content)

    # Load knowledge packet
    packet = ""
    if packet_path and packet_path.exists():
        packet = packet_path.read_text("utf-8")
        if len(packet) > 8000:
            packet = packet[:8000] + "\n\n... (truncated for context window)"

    word_target = plan.get("word_target", 1200)
    phase = plan.get("phase", "")

    # Summary heading (same logic as step_write)
    summary_heading = (
        "Summary" if module_num <= 3
        else "Підсумок — Summary" if module_num <= 14
        else "Підсумок"
    )

    # Fill template
    prompt = template
    replacements = {
        "{TOPIC_TITLE}": plan.get("title", slug),
        "{MODULE_NUM}": str(module_num),
        "{LEVEL}": level.upper(),
        "{PHASE}": phase,
        "{WORD_TARGET}": str(word_target),
        "{WORD_OVERSHOOT}": str(int(word_target * 1.1)),
        "{PLAN_CONTENT}": plan_content,
        "{KNOWLEDGE_PACKET}": packet,
        "{SUMMARY_HEADING}": summary_heading,
    }

    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Save prompt for inspection
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = orch_dir / "v6-skeleton-prompt.md"
    prompt_path.write_text(prompt, "utf-8")
    _log(f"  Prompt saved → {prompt_path.name} ({len(prompt)} chars)")

    # Dispatch to writer
    if writer == "gemini":
        from batch_gemini_config import PRO_MODEL
        from pipeline.core import dispatch_gemini
        _log(f"  Dispatching to Gemini ({PRO_MODEL})...")
        ok, raw = dispatch_gemini(
            prompt, task_id=f"v6-skeleton-{slug}",
            model=PRO_MODEL,
            stdout_only=True, timeout=300,
        )
    elif writer == "claude":
        import subprocess

        from batch_gemini_config import CLAUDE_MODEL_CORE_CONTENT

        model = CLAUDE_MODEL_CORE_CONTENT
        _log(f"  Dispatching to Claude ({model})...")
        try:
            result = subprocess.run(
                ["claude", "-p", "--model", model,
                 "--output-format", "text"],
                input=prompt,
                capture_output=True, text=True, timeout=300,
                cwd=str(PROJECT_ROOT),
            )
            ok = result.returncode == 0
            raw = result.stdout if ok else ""
            if not ok:
                _log(f"  ❌ Claude returned error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            _log("  ❌ Claude timed out (300s)")
            ok = False
            raw = ""
    else:
        _log(f"  ❌ Unknown writer: {writer}")
        return None

    if not ok or not raw:
        _log("  ❌ Writer returned no skeleton output")
        return None

    # Extract skeleton from <skeleton> tags
    import re as _re
    skeleton_match = _re.search(r"<skeleton>(.*?)</skeleton>", raw, _re.DOTALL)
    if skeleton_match:
        skeleton_text = skeleton_match.group(1).strip()
    else:
        # Fall back to entire output if no tags found
        skeleton_text = raw.strip()
        _log("  ⚠️  No <skeleton> tags found — using full output")

    # Save skeleton
    skeleton_path = orch_dir / "skeleton.md"
    skeleton_path.write_text(skeleton_text, "utf-8")
    skeleton_words = len(skeleton_text.split())
    _log(f"  ✅ Skeleton generated ({skeleton_words} words)")
    _log(f"  → {skeleton_path}")

    _save_v6_state(level, slug, "skeleton")
    return skeleton_text


def step_write(level: str, module_num: int, slug: str,
               packet_path: Path, writer: str = "gemini",
               correction_directive: str = "",
               skeleton: str = "") -> Path | None:
    """Step 5: Single LLM session — generate prose + exercise placeholders."""
    _log(f"\n{'='*60}")
    _log(f"  Step 5: WRITE — Content generation ({writer})")
    _log(f"{'='*60}")

    # Load template
    template_path = PHASES_DIR / "v6-write.md"
    if not template_path.exists():
        _log(f"  ❌ Template not found: {template_path}")
        return None

    template = template_path.read_text("utf-8")

    # Load plan (read once, parse once)
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan_content = plan_path.read_text("utf-8")
    plan = yaml.safe_load(plan_content)

    # Load knowledge packet
    packet = packet_path.read_text("utf-8") if packet_path and packet_path.exists() else ""
    # Truncate if too long (keep concise as Gemini requested)
    if len(packet) > 8000:
        packet = packet[:8000] + "\n\n... (truncated for context window)"

    # Build section titles
    sections = plan.get("content_outline", [])
    section_titles = []
    for s in sections:
        name = s.get("section", "")
        words = s.get("words", 0)
        section_titles.append(f"- `## {name}` (~{words} words)")
    # Add summary
    summary_heading = "Summary" if module_num <= 3 else "Підсумок — Summary" if module_num <= 14 else "Підсумок"
    section_titles.append(f"- `## {summary_heading}` (~150 words)")

    # Build vocabulary hints
    vocab = plan.get("vocabulary_hints", {})
    vocab_lines = []
    for category in ("required", "recommended"):
        items = vocab.get(category, [])
        if items:
            vocab_lines.append(f"**{category.capitalize()}:** {', '.join(str(i) for i in items)}")

    # Build pronunciation videos
    pv = plan.get("pronunciation_videos", {})
    pv_lines = []
    if pv.get("overview"):
        pv_lines.append(f"Overview: {pv['overview']}")
    if pv.get("playlist"):
        pv_lines.append(f"Playlist: {pv['playlist']}")
    # Merge letter videos
    letters = {}
    for key in ("vowels", "consonants", "special", "letters"):
        letters.update(pv.get(key, {}))
    credit = pv.get("credit", "Ukrainian Lessons")
    if letters:
        pv_lines.append("\nPer-letter videos — embed each next to its letter description.")
        pv_lines.append(f'Use format: <YouTubeVideo client:only="react" url="URL" label="Літера X — {credit}" />')
        pv_lines.append(f'Replace X with the actual letter. Example: label="Літера А — {credit}"')
        pv_lines.append("")
        for letter, url in letters.items():
            pv_lines.append(f"- Літера {letter}: {url}")

    # Get constraints from config_tables
    from pipeline.config_tables import (
        get_golden_fragment,
        get_immersion_rule,
        get_level_constraints,
        get_pedagogical_constraints,
    )

    phase = plan.get("phase", "")
    word_target = plan.get("word_target", 1200)

    # Fill template
    prompt = template
    replacements = {
        "{TOPIC_TITLE}": plan.get("title", slug),
        "{MODULE_NUM}": str(module_num),
        "{LEVEL}": level.upper(),
        "{PHASE}": phase,
        "{WORD_TARGET}": str(word_target),
        "{WORD_CEILING}": str(int(word_target * 1.5)),
        "{PLAN_CONTENT}": plan_content,
        "{KNOWLEDGE_PACKET}": packet,
        "{EXACT_SECTION_TITLES}": "\n".join(section_titles),
        "{IMMERSION_RULE}": get_immersion_rule(level, module_num),
        "{PEDAGOGICAL_CONSTRAINTS}": get_pedagogical_constraints(level, module_num, plan),
        "{LEVEL_CONSTRAINTS}": get_level_constraints(level, plan),
        "{VOCABULARY_HINTS}": "\n".join(vocab_lines),
        "{PRONUNCIATION_VIDEOS}": "\n".join(pv_lines),
        "{GOLDEN_FRAGMENT}": get_golden_fragment(level, module_num),
        "{SUMMARY_HEADING}": summary_heading,
    }

    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Inject skeleton section when provided (Skeleton->Flesh architecture)
    if skeleton:
        skeleton_section = (
            "\n\n---\n\n"
            "## Skeleton — Follow This Structure Exactly\n\n"
            "A detailed paragraph-level skeleton was generated for this module. "
            "You MUST follow it precisely:\n"
            "- Write every paragraph listed, in the order listed\n"
            "- Hit each paragraph's word budget (+-10%)\n"
            "- Place exercises exactly where the skeleton says\n"
            "- Use the specific examples named in the skeleton\n"
            "- Do NOT skip paragraphs, reorder sections, or add unplanned content\n\n"
            "The skeleton replaces Step 1 (Pacing Plan) — do NOT output a "
            "<pacing_plan> block. Start writing immediately from the first section.\n\n"
            "<skeleton>\n"
            f"{skeleton}\n"
            "</skeleton>\n"
        )
        # Insert before "## Output Format" so it's the last constraint seen
        if "## Output Format" in prompt:
            prompt = prompt.replace(
                "## Output Format",
                skeleton_section + "\n## Output Format",
            )
        else:
            prompt += skeleton_section
        _log(f"  📐 Skeleton injected ({len(skeleton)} chars)")

    # Inject correction directive at top of prompt (for retries)
    if correction_directive:
        prompt = correction_directive + "\n\n" + prompt
        _log(f"  ⚠️  Correction directive injected ({len(correction_directive)} chars)")

    # Save prompt for inspection
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = orch_dir / "v6-prompt.md"
    prompt_path.write_text(prompt, "utf-8")
    _log(f"  Prompt saved → {prompt_path.name} ({len(prompt)} chars)")

    # Dispatch to writer
    output_dir = CURRICULUM_ROOT / level
    output_path = output_dir / f"{slug}.md"

    if writer == "gemini":
        from batch_gemini_config import PRO_MODEL
        from pipeline.core import dispatch_gemini
        _log(f"  Dispatching to Gemini ({PRO_MODEL})...")
        ok, raw = dispatch_gemini(
            prompt, task_id=f"v6-{slug}",
            model=PRO_MODEL,
            stdout_only=True, timeout=600,
        )
    elif writer == "claude":
        import subprocess

        from batch_gemini_config import CLAUDE_MODEL_CORE_CONTENT

        model = CLAUDE_MODEL_CORE_CONTENT
        _log(f"  Dispatching to Claude ({model})...")

        # Pipe prompt content via stdin to Claude CLI
        # -p flag with stdin: cat prompt | claude -p --output-format text
        try:
            result = subprocess.run(
                ["claude", "-p", "--model", model,
                 "--output-format", "text"],
                input=prompt,
                capture_output=True, text=True, timeout=600,
                cwd=str(PROJECT_ROOT),
            )
            ok = result.returncode == 0
            raw = result.stdout if ok else ""
            if not ok:
                _log(f"  ❌ Claude returned error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            _log("  ❌ Claude timed out (600s)")
            ok = False
            raw = ""
    else:
        _log(f"  ❌ Unknown writer: {writer}")
        return None

    if not ok or not raw:
        _log("  ❌ Writer returned no output")
        return None

    # Save pacing plan if present (for debugging)
    import re as _re
    pacing_match = _re.search(r"<pacing_plan>(.*?)</pacing_plan>", raw, _re.DOTALL)
    if pacing_match:
        pacing_text = pacing_match.group(1).strip()
        _log(f"  📐 Pacing plan:\n{pacing_text}")
        pacing_path = orch_dir / "pacing-plan.txt"
        pacing_path.write_text(pacing_text, "utf-8")

    # Extract content (everything from first ## heading)
    lines = raw.split("\n")
    content_start = -1
    for i, line in enumerate(lines):
        if line.startswith("## "):
            content_start = i
            break

    if content_start < 0:
        _log("  ❌ No H2 headings found in output")
        final_content = raw
    else:
        final_content = "\n".join(lines[content_start:])

    # Strip any pacing_plan/skeleton tags that leaked into content
    final_content = _re.sub(r"</?pacing_plan>", "", final_content)
    final_content = _re.sub(r"</?skeleton>", "", final_content)

    output_path.write_text(final_content, "utf-8")
    word_count = len(final_content.split())
    _log(f"  ✅ Content written ({word_count} words)")
    _log(f"  → {output_path}")

    return output_path


def step_write_with_retry(
    level: str, module_num: int, slug: str,
    packet_path: Path,
    writer: str = "gemini",
    max_retries: int = 2,
    skeleton: str = "",
) -> Path | None:
    """Write content with quick verify and retry loop.

    Strategy (from Gemini consultation #982):
    - Retry 1: same model + correction directive
    - Retry 2: switch model (circuit breaker)
    - Retry 3 (exhausted): return None → flag for human review
    - Always regenerate WHOLE module (not sections)
    - Do NOT include failed output in retry (prevents anchoring)
    """
    from build.quick_verify import (
        build_correction_directive,
        format_results,
        has_errors,
        quick_verify,
    )

    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8"))

    # Stats log
    stats_path = CURRICULUM_ROOT / level / "build-stats.jsonl"

    other_writer = "claude" if writer == "gemini" else "gemini"

    current_directive = ""  # No directive on first attempt

    for attempt in range(1, max_retries + 2):  # +2 because range is exclusive
        current_writer = writer if attempt <= max_retries else other_writer
        _log(f"\n  📝 Write attempt {attempt}/{max_retries + 1} (writer: {current_writer})")

        output = step_write(
            level, module_num, slug, packet_path,
            writer=current_writer,
            correction_directive=current_directive,
            skeleton=skeleton,
        )
        if output is None:
            _log(f"  ❌ Writer returned no output on attempt {attempt}")
            _log_stats(stats_path, slug, "WRITE_FAILED", attempt, current_writer, False)
            continue

        # Quick verify
        content = output.read_text("utf-8")
        results = quick_verify(content, plan)
        _log(format_results(results))

        # Persist quick verify results for API access (AC10)
        _save_quick_verify(level, slug, results, attempt)

        if not has_errors(results):
            _log(f"  ✅ Quick verify PASSED on attempt {attempt}")
            _log_stats(stats_path, slug, "PASS", attempt, current_writer, True)
            return output

        # Failed — log and prepare retry
        error_types = ", ".join(set(r.check for r in results if r.severity == "ERROR"))
        _log_stats(stats_path, slug, error_types, attempt, current_writer, False)

        if attempt > max_retries:
            _log(f"  ❌ Exhausted {max_retries + 1} attempts. Flag for human review.")
            # Write error report
            report_dir = CURRICULUM_ROOT / level / "build-errors"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"{slug}-errors.md"
            report_path.write_text(
                f"# Build Error Report: {slug}\n\n"
                f"## Attempts: {max_retries + 1}\n\n"
                + "\n".join(str(r) for r in results)
                + "\n\n## Correction Directive\n\n"
                + build_correction_directive(results),
                "utf-8",
            )
            _log(f"  → Error report: {report_path}")

            # Auto-generate friction entry for failed build
            _generate_friction(level, slug, results, max_retries + 1)

            return output  # Return the output anyway (human can fix)

        # Build correction directive for next attempt — injected into prompt
        current_directive = build_correction_directive(results)
        _log("  🔄 Retrying with correction directive...")

        # Also save directive to disk for human inspection
        orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
        orch_dir.mkdir(parents=True, exist_ok=True)
        directive_path = orch_dir / f"correction-attempt-{attempt}.md"
        directive_path.write_text(current_directive, "utf-8")

    return None  # Should not reach here


def _generate_friction(level: str, slug: str, results: list,
                       attempts: int):
    """Auto-generate friction entry when all retries are exhausted.

    Creates or appends to orchestration/{slug}/friction.yaml so that
    future builds can learn from repeated failures.
    """
    from datetime import datetime

    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    friction_path = orch_dir / "friction.yaml"

    error_types = sorted({r.check for r in results if r.severity == "ERROR"})

    entry = {
        "source": "auto-generated",
        "date": datetime.now(tz=UTC).strftime("%Y-%m-%d"),
        "error_types": error_types,
        "status": "active",
        "note": f"V6 build failed after {attempts} attempts",
    }

    # Load existing friction entries or start fresh
    existing = []
    if friction_path.exists():
        try:
            loaded = yaml.safe_load(friction_path.read_text("utf-8"))
            if isinstance(loaded, list):
                existing = loaded
        except Exception:
            pass

    existing.append(entry)
    friction_path.write_text(
        yaml.dump(existing, allow_unicode=True, default_flow_style=False,
                  sort_keys=False),
        "utf-8",
    )
    _log(f"  → Friction entry added: {friction_path}")


def _log_stats(stats_path: Path, slug: str, error_type: str,
               attempt: int, model: str, success: bool):
    """Append retry stats to JSONL file."""
    import json
    from datetime import datetime

    stats_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "slug": slug,
        "error_type": error_type,
        "attempt": attempt,
        "model": model,
        "success": success,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }
    with open(stats_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _save_quick_verify(level: str, slug: str, results: list, attempt: int):
    """Persist quick verify results to orchestration for API access."""
    import json
    from datetime import datetime

    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    qv_path = orch_dir / "quick-verify.json"

    data = {
        "attempt": attempt,
        "passed": not any(r.severity == "ERROR" for r in results),
        "errors": [{"check": r.check, "severity": r.severity, "message": r.message}
                   for r in results if r.severity == "ERROR"],
        "warnings": [{"check": r.check, "severity": r.severity, "message": r.message}
                     for r in results if r.severity == "WARNING"],
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }
    qv_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def step_exercises(content_path: Path) -> bool:
    """Step 5b: Fill any remaining exercise placeholders.

    In V6, the writer produces exercises directly as DSL blocks.
    This step is a FALLBACK — it only fills :::exercise-placeholder
    blocks that the writer may have left unfilled.
    """
    _log(f"\n{'='*60}")
    _log("  Step 5b: EXERCISES — Check for unfilled placeholders")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    from exercises.fill_placeholders import fill_placeholders

    text = content_path.read_text("utf-8")

    # Count writer-produced exercises
    import re
    direct_exercises = len(re.findall(
        r"^:::(quiz|fill-in|match-up|group-sort|true-false)\b",
        text, re.MULTILINE,
    ))
    if direct_exercises:
        _log(f"  ✅ Writer produced {direct_exercises} exercise(s) directly")

    # Fill any remaining placeholders (fallback)
    filled, count = fill_placeholders(text)

    if count > 0:
        content_path.write_text(filled, "utf-8")
        _log(f"  ✅ Filled {count} exercise placeholder(s)")
    else:
        _log("  ℹ️  No exercise placeholders found")

    return True


def _post_process_content(content_path: Path) -> int:
    """Deterministic post-processing: strip LLM artifacts."""
    text = content_path.read_text("utf-8")
    original_len = len(text)
    fixes = 0

    # 1. Strip duplicate summary section (LLM sometimes writes two)
    # Keep the first "## Підсумок" or "## Summary", remove subsequent ones
    import re
    summary_headings = list(re.finditer(
        r"^## (?:Підсумок|Summary).*$", text, re.MULTILINE
    ))
    if len(summary_headings) > 1:
        # Keep first, remove everything from second summary heading onward
        cut_pos = summary_headings[1].start()
        text = text[:cut_pos].rstrip() + "\n"
        fixes += 1
        _log("  🔧 Removed duplicate summary section")

    # 2. Strip "Content notes" meta-section (LLM self-audit artifact)
    content_notes = re.search(
        r"\n\*\*Content notes:\*\*.*$", text, re.DOTALL
    )
    if content_notes:
        text = text[:content_notes.start()].rstrip() + "\n"
        fixes += 1
        _log("  🔧 Removed Content notes meta-section")

    # 3. Strip trailing --- separator before content notes
    text = re.sub(r"\n---\s*$", "\n", text)

    # 4. Strip ALL manual stress marks (combining acute U+0301)
    # The writer sometimes adds them despite being told not to.
    # The stress annotator adds correct ones later.
    clean = text.replace("\u0301", "")
    if clean != text:
        stress_count = len(text) - len(clean)
        fixes += 1
        text = clean
        _log(f"  🔧 Stripped {stress_count} manual stress marks")

    # 5. Strip writer-generated tab markers and vocab tables
    # The ENRICH step generates these properly — writer copies are garbage
    if "<!-- TAB:" in text:
        tab_pos = text.index("<!-- TAB:")
        text = text[:tab_pos].rstrip() + "\n"
        fixes += 1
        _log("  🔧 Stripped writer-generated tab markers")

    # 6. Strip stray single quotes from exercise DSL values
    # LLMs sometimes produce: q: "'text'" or answer: "'word'"
    stray_quote_pattern = re.compile(
        r'''((?:q|answer|sentence|left|right|statement|name):\s*")'([^"]*)'("?)'''
    )
    new_text = stray_quote_pattern.sub(r'\1\2\3', text)
    if new_text != text:
        fixes += 1
        text = new_text
        _log("  🔧 Stripped stray quotes from exercise DSL")

    if len(text) != original_len:
        content_path.write_text(text, "utf-8")

    return fixes


def step_annotate(content_path: Path) -> bool:
    """Step 6: Add stress marks + deterministic fixes."""
    _log(f"\n{'='*60}")
    _log("  Step 6: ANNOTATE — Stress marks + post-processing")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    # Post-processing first (strip LLM artifacts before stress annotation)
    _post_process_content(content_path)

    try:
        from pipeline.stress_annotator import annotate_file
        count = annotate_file(content_path)
        _log(f"  ✅ Added stress marks to {count} words")
    except ImportError:
        _log("  ⚠️  Stress annotator not available")
    except Exception as e:
        _log(f"  ⚠️  Stress annotation failed: {e}")

    return True


def step_enrich(content_path: Path, level: str, slug: str) -> bool:
    """Step 7b: ENRICH — словник, videos, resources, dialogue formatting."""
    _log(f"\n{'='*60}")
    _log("  Step 7b: ENRICH — Словник, videos, resources")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        _log(f"  ⚠️  Plan not found: {plan_path}")
        return True  # Non-blocking

    from build.enrich import enrich_file

    actions = enrich_file(content_path, plan_path)
    if actions:
        _log(f"  ✅ Enriched: {', '.join(actions)}")
    else:
        _log("  ℹ️  No enrichments needed")

    return True


def step_verify(content_path: Path, level: str, module_num: int) -> bool:
    """Step 7: VESUM verification + grammar scope check."""
    _log(f"\n{'='*60}")
    _log("  Step 7: VERIFY — VESUM + grammar checks")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    text = content_path.read_text("utf-8")
    issues = []

    # VESUM word check
    try:
        from pipeline.screen import _run_vesum_verify
        stats, not_found, _ = _run_vesum_verify(content_path)
        vesum_hits = stats.get("vesum_hits", 0)
        total = stats.get("total", 0)
        # Filter proper nouns and phonetic fragments
        _phonetic_fragments = {"йа", "йе", "йі", "йу", "шч", "ка", "пт", "пте", "дж", "дз"}
        real_not_found = [
            r for r in not_found
            if not (r.get("original", "")[0:1].isupper() and r.get("source") == "prose")
            and r.get("original", "").lower() not in _phonetic_fragments
        ]
        if real_not_found:
            _log(f"  ⚠️  VESUM: {len(real_not_found)} word(s) not found:")
            for r in real_not_found[:5]:
                _log(f"    — {r.get('original', '?')}")
            issues.extend(real_not_found)
        else:
            _log(f"  ✅ VESUM: {vesum_hits}/{total} words verified")
    except Exception as e:
        _log(f"  ⚠️  VESUM check skipped: {e}")

    # Russicism scan (regex-based on content text)
    try:
        from build.quick_verify import SEVERE_RUSSIANISMS
        content_lower = text.lower()
        russicisms = [w for w in SEVERE_RUSSIANISMS if w in content_lower]
        # Also check for Russian-only word forms
        russian_words = ["букварь", "учебник", "тетрадь", "хорошо", "конечно",
                         "сейчас", "здесь", "тоже", "пожалуйста", "спасибо"]
        russicisms.extend(w for w in russian_words if w in content_lower)
        if russicisms:
            _log(f"  ⚠️  Russicisms found: {', '.join(set(russicisms))}")
            issues.extend(russicisms)
        else:
            _log("  ✅ No Russicisms detected")
    except Exception as e:
        _log(f"  ⚠️  Russicism scan failed: {e}")

    # IPA check (skip for phonetics M01-M03)
    if not (level == "a1" and module_num <= 3):
        try:
            from pipeline.screen import _run_ipa_scan
            ipa_issues = _run_ipa_scan(text)
            if ipa_issues:
                _log(f"  ⚠️  IPA/Latin transliteration found: {len(ipa_issues)} issue(s)")
                issues.extend(ipa_issues)
            else:
                _log("  ✅ No IPA/Latin transliteration")
        except Exception as e:
            _log(f"  ⚠️  IPA check failed: {e}")

    if issues:
        _log(f"\n  ⚠️  Verification found {len(issues)} issue(s) — review recommended")
    else:
        _log("\n  ✅ Verification PASSED — all clean")

    return len(issues) == 0


def _build_vesum_report(content: str) -> str:
    """Pre-verify all Ukrainian words against VESUM for the reviewer.

    Extracts Ukrainian words (3+ characters) from the content, looks each up
    in the VESUM SQLite database, and returns a structured report. This gives
    the reviewer factual data instead of guessing about word existence.
    """
    import re
    import sqlite3

    vesum_db = PROJECT_ROOT / "data" / "vesum.db"
    if not vesum_db.exists():
        return ""

    # Extract Ukrainian words (3+ chars to skip particles/prepositions)
    words = set(re.findall(r"\b[а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ]{2,}\b", content))
    if not words:
        return ""

    db = sqlite3.connect(str(vesum_db))
    try:
        verified = []
        not_found = []
        for word in sorted(words):
            row = db.execute(
                "SELECT lemma, pos FROM forms WHERE word_form = ? LIMIT 1",
                (word.lower(),),
            ).fetchone()
            if row:
                verified.append(f"  ✓ {word} → lemma: {row[0]}, POS: {row[1]}")
            else:
                not_found.append(f"  ✗ {word} — NOT IN VESUM")
    finally:
        db.close()

    report_lines = [
        "<vesum_verification>",
        "The following Ukrainian words from the content were verified against "
        "VESUM (415K lemmas). Use this data to check linguistic claims — "
        "do NOT guess about words.",
        "",
        f"Verified: {len(verified)} words | Not found: {len(not_found)} words",
        "",
    ]

    if not_found:
        report_lines.append(
            "Words NOT in VESUM (may be errors, proper nouns, or valid words "
            "missing from dict):"
        )
        report_lines.extend(not_found[:50])
        report_lines.append("")

    # Include a sample of verified words so reviewer can spot-check
    if verified:
        report_lines.append(
            "Sample of verified words (all confirmed to exist in Ukrainian):"
        )
        report_lines.extend(verified[:50])
        report_lines.append("")

    report_lines.append("</vesum_verification>")
    return "\n".join(report_lines)


def step_review(content_path: Path, level: str, module_num: int,
                slug: str, writer: str = "claude") -> tuple[bool, float]:
    """Step 8: Cross-agent adversarial review.

    If Claude wrote → Gemini reviews (and vice versa).
    Returns (passed, score).
    """
    _log(f"\n{'='*60}")
    _log("  Step 8: REVIEW — Cross-agent adversarial review")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False, 0.0

    # Load review template
    template_path = PHASES_DIR / "v6-review.md"
    if not template_path.exists():
        _log(f"  ❌ Review template not found: {template_path}")
        return False, 0.0

    template = template_path.read_text("utf-8")

    # Load plan and content
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan_content = plan_path.read_text("utf-8") if plan_path.exists() else ""
    plan = yaml.safe_load(plan_content) if plan_content else {}
    generated_content = content_path.read_text("utf-8")

    # Build review prompt
    writer_model = "Claude Opus" if writer == "claude" else "Gemini Pro"
    prompt = template
    replacements = {
        "{MODULE_NUM}": str(module_num),
        "{TOPIC_TITLE}": plan.get("title", slug),
        "{LEVEL}": level.upper(),
        "{PHASE}": plan.get("phase", ""),
        "{WRITER_MODEL}": writer_model,
        "{WORD_TARGET}": str(plan.get("word_target", 1200)),
        "{PLAN_CONTENT}": plan_content,
        "{GENERATED_CONTENT}": generated_content,
    }
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Inject VESUM verification data so the reviewer has facts, not guesses
    vesum_report = _build_vesum_report(generated_content)
    if vesum_report:
        prompt = prompt + "\n\n" + vesum_report
        _log(f"  VESUM pre-verification: injected ({len(vesum_report)} chars)")

    # Save review prompt
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    review_prompt_path = orch_dir / "v6-review-prompt.md"
    review_prompt_path.write_text(prompt, "utf-8")

    # Dispatch to reviewer (cross-agent: writer's opposite)
    reviewer = "gemini" if writer == "claude" else "claude"
    _log(f"  Reviewer: {reviewer} (writer was {writer})")

    if reviewer == "gemini":
        from batch_gemini_config import PRO_MODEL
        from pipeline.core import dispatch_gemini
        _log(f"  Dispatching to Gemini ({PRO_MODEL})...")
        ok, raw = dispatch_gemini(
            prompt, task_id=f"v6-review-{slug}",
            model=PRO_MODEL,
            stdout_only=True, timeout=600,
        )
    else:
        import subprocess
        _log("  Dispatching to Claude for review...")
        try:
            result = subprocess.run(
                ["claude", "-p", "--model", "claude-opus-4-6",
                 "--output-format", "text"],
                input=prompt,
                capture_output=True, text=True, timeout=600,
                cwd=str(PROJECT_ROOT),
            )
            ok = result.returncode == 0
            raw = result.stdout if ok else ""
        except subprocess.TimeoutExpired:
            _log("  ❌ Claude review timed out")
            ok = False
            raw = ""

    if not ok or not raw:
        _log("  ❌ Reviewer returned no output")
        return False, 0.0

    # Save review output
    review_dir = CURRICULUM_ROOT / level / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"{slug}-review.md"
    review_path.write_text(raw, "utf-8")
    _log(f"  Review saved → {review_path}")

    # Parse raw dimension scores from review output and calculate weighted total
    import re

    # Dimension weights (must match v6-review.md)
    DIMENSION_WEIGHTS = {
        1: 0.15,  # Plan adherence
        2: 0.15,  # Linguistic accuracy
        3: 0.15,  # Pedagogical quality
        4: 0.10,  # Vocabulary coverage
        5: 0.15,  # Exercise quality
        6: 0.10,  # Engagement & tone
        7: 0.05,  # Structural integrity
        8: 0.05,  # Cultural accuracy
        9: 0.10,  # Dialogue & conversation quality
    }

    # Extract per-dimension scores from the markdown table
    score_pattern = re.compile(r"\|\s*\d+\.\s*[^|]+\|\s*(\d+)/10\s*\|")
    raw_scores = [int(m.group(1)) for m in score_pattern.finditer(raw)]

    if raw_scores:
        # Use available scores even if fewer than 9 — normalize by available weights
        available = min(len(raw_scores), len(DIMENSION_WEIGHTS))
        used_weights = {k: v for k, v in DIMENSION_WEIGHTS.items() if k <= available}
        weight_sum = sum(used_weights.values())
        weighted = sum(
            raw_scores[i] * DIMENSION_WEIGHTS.get(i + 1, 0)
            for i in range(available)
        )
        # Normalize: if only 8 of 9 dimensions, scale up proportionally
        score = round(weighted / weight_sum * 1.0, 1) if weight_sum > 0 else 0.0
        _log(f"  Raw scores: {raw_scores}")
        if available < len(DIMENSION_WEIGHTS):
            _log(f"  ⚠️  Only {available}/9 dimensions parsed — score normalized")
        _log(f"  Weighted score (calculated): {score}/10")
    else:
        score = 0.0
        _log("  ⚠️  Could not parse any dimension scores")

    # Parse verdict (reviewer judges severity, pipeline judges score)
    verdict = "UNKNOWN"
    for v in ("PASS", "REVISE", "REJECT"):
        if f"Verdict: {v}" in raw or f"Verdict:{v}" in raw:
            verdict = v
            break

    # Two independent gates
    score_pass = score >= 8.0
    severity_pass = verdict == "PASS"
    passed = score_pass and severity_pass

    icon = "✅" if passed else "❌"
    _log(f"  {icon} Review: {score}/10 (score gate: {'✅' if score_pass else '❌'}) — {verdict} (severity gate: {'✅' if severity_pass else '❌'})")

    return passed, score, raw


def _build_review_correction(review_text: str) -> str:
    """Extract findings from a review and build a correction directive for retry.

    Parses [DIMENSION] [SEVERITY] findings and formats them as a
    correction directive that goes at the top of the retry prompt.
    """
    import re

    lines = [
        "<correction_directive>",
        "CRITICAL: Your previous module was reviewed and scored below 8.0/10.",
        "You must rewrite the module FROM SCRATCH, fixing ALL issues below.",
        "All original constraints from the writing prompt still apply.\n",
    ]

    # Extract the raw findings section
    findings_section = re.search(
        r"## Findings\n(.*?)(?=\n## Verdict|\Z)",
        review_text,
        re.DOTALL,
    )

    if findings_section:
        for line in findings_section.group(1).strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("```"):
                if "critical" in line.lower() or "major" in line.lower():
                    lines.append(f"- FIX: {line}")
                elif "minor" in line.lower():
                    lines.append(f"- NOTE: {line}")
                elif line.startswith("Location:") or line.startswith("Issue:") or line.startswith("Fix:"):
                    lines.append(f"  {line}")

    # Also extract the linguistic scan errors
    linguistic_section = re.search(
        r"## Linguistic Scan\n(.*?)(?=\n## |\Z)",
        review_text,
        re.DOTALL,
    )
    if linguistic_section:
        scan_text = linguistic_section.group(1).strip()
        if scan_text and "no linguistic errors" not in scan_text.lower():
            lines.append(f"\n- FIX (Linguistic): {scan_text[:500]}")

    if len(lines) <= 4:
        # No specific findings extracted — use generic directive
        lines.append("- The reviewer found quality issues. Write more carefully.")

    lines.append("</correction_directive>")
    return "\n".join(lines)


def _convert_tab_markers(content: str) -> str:
    """Convert <!-- TAB:name --> markers to <Tabs>/<TabItem> MDX components.

    Input:  <!-- TAB:Урок -->\n...content...\n<!-- TAB:Словник -->\n...
    Output: <Tabs syncKey="module-tab">
            <TabItem label="Урок">\n...content...\n</TabItem>
            <TabItem label="Словник">\n...
    """
    import re

    tab_pattern = re.compile(r"<!-- TAB:(.+?) -->")
    tabs = list(tab_pattern.finditer(content))

    if not tabs:
        return content

    parts = []
    parts.append('<Tabs syncKey="module-tab">')

    for i, match in enumerate(tabs):
        tab_name = match.group(1)
        start = match.end()
        end = tabs[i + 1].start() if i + 1 < len(tabs) else len(content)
        tab_content = content[start:end].strip()

        parts.append(f'<TabItem label="{tab_name}">')
        parts.append("")
        parts.append(tab_content)
        parts.append("")
        parts.append("</TabItem>")

    parts.append("</Tabs>")

    return "\n".join(parts)


def step_publish(content_path: Path, level: str, slug: str) -> bool:
    """Step 9: Convert DSL→MDX."""
    _log(f"\n{'='*60}")
    _log("  Step 9: PUBLISH — DSL→MDX")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    from generate_mdx.dsl_to_mdx import convert_dsl_to_mdx

    text = content_path.read_text("utf-8")
    mdx_content, count = convert_dsl_to_mdx(text)

    if count > 0:
        _log(f"  Converted {count} exercise(s) to MDX components")

    # Write MDX
    mdx_dir = PROJECT_ROOT / "starlight" / "src" / "content" / "docs" / level
    mdx_dir.mkdir(parents=True, exist_ok=True)
    mdx_path = mdx_dir / f"{slug}.mdx"

    # Add MDX frontmatter
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    modules = data.get("levels", {}).get(level, {}).get("modules", [])
    order = modules.index(slug) + 1 if slug in modules else 1

    frontmatter = f"""---
title: "{slug.replace('-', ' ').title()}"
sidebar:
  order: {order}
  label: "{order:02d}. {slug.replace('-', ' ').title()}"
pipeline: v6
build_status: draft
---

"""

    # Add component imports
    imports = """import { Tabs, TabItem } from '@astrojs/starlight/components';
import Quiz from '@site/src/components/Quiz';
import FillIn from '@site/src/components/FillIn';
import MatchUp from '@site/src/components/MatchUp';
import TrueFalse from '@site/src/components/TrueFalse';
import GroupSort from '@site/src/components/GroupSort';
import YouTubeVideo from '@site/src/components/YouTubeVideo';
import DialogueBox from '@site/src/components/DialogueBox';

"""

    # Convert tab markers to <Tabs>/<TabItem> wrappers
    mdx_content = _convert_tab_markers(mdx_content)

    mdx_path.write_text(frontmatter + imports + mdx_content, "utf-8")
    _log(f"  ✅ MDX written → {mdx_path}")

    return True


def main():
    parser = argparse.ArgumentParser(description="V6 Pipeline Build")
    parser.add_argument("level", help="Level (e.g., a1)")
    parser.add_argument("module", type=int, help="Module number")
    parser.add_argument("--writer", choices=["gemini", "claude"], default="gemini",
                        help="Default: gemini (Claude CLI truncates long-form content)")
    parser.add_argument("--step", choices=["check", "research", "skeleton", "write", "exercises", "annotate", "enrich", "verify", "review", "publish", "all"],
                        default="all")
    skeleton_group = parser.add_mutually_exclusive_group()
    skeleton_group.add_argument("--skeleton", action="store_true", default=None,
                                help="Force skeleton step (default: auto for word_target >= 3000)")
    skeleton_group.add_argument("--no-skeleton", action="store_true",
                                help="Skip skeleton step even for large modules")
    args = parser.parse_args()

    # Resolve slug
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    slugs = data.get("levels", {}).get(args.level, {}).get("modules", [])
    if args.module > len(slugs):
        _log(f"Module {args.module} not found (max {len(slugs)})")
        sys.exit(1)
    slug = slugs[args.module - 1]

    _log(f"\n🔨 V6 Build: {args.level.upper()} M{args.module:02d} ({slug})")
    _log(f"   Writer: {args.writer}")

    steps = args.step

    # Step 2: CHECK
    if steps in ("all", "check") and not step_check(args.level, args.module, slug):
        _log("\n❌ Build FAILED at Step 2 (plan check)")
        sys.exit(1)
    if steps in ("all", "check"):
        _save_v6_state(args.level, slug, "check")

    # Step 3: RESEARCH
    packet_path = None
    if steps in ("all", "research"):
        packet_path = step_research(args.level, args.module, slug)
        if not packet_path:
            _log("\n❌ Build FAILED at Step 3 (research)")
            sys.exit(1)
        _save_v6_state(args.level, slug, "research")
    else:
        # Try to find existing packet
        packet_path = CURRICULUM_ROOT / args.level / "research" / f"{slug}-knowledge-packet.md"
        if not packet_path.exists():
            packet_path = None

    # Step 4: SKELETON (auto for word_target >= 3000, or forced via --skeleton)
    skeleton_text = ""
    plan_path = CURRICULUM_ROOT / "plans" / args.level / f"{slug}.yaml"
    word_target = yaml.safe_load(plan_path.read_text("utf-8")).get("word_target", 1200) if plan_path.exists() else 1200

    use_skeleton = (
        args.skeleton
        or (not args.no_skeleton and word_target >= 3000)
    )

    if steps in ("all", "skeleton") and use_skeleton:
        skeleton_text = step_skeleton(
            args.level, args.module, slug, packet_path,
            writer=args.writer,
        ) or ""
        if not skeleton_text and steps == "skeleton":
            _log("\n  SKELETON step returned empty — continuing without skeleton")
    elif steps == "skeleton":
        _log(f"\n  ℹ️  Skeleton skipped (word_target={word_target} < 3000, use --skeleton to force)")

    if use_skeleton and skeleton_text:
        _log(f"\n  📐 Skeleton active ({len(skeleton_text.split())} words) — will constrain writer")
    elif use_skeleton and not skeleton_text:
        _log("\n  ⚠️  Skeleton was requested but generation failed — writing without skeleton")

    # Try to load existing skeleton from disk if running single step
    if steps == "write" and not skeleton_text and use_skeleton:
        existing_skeleton = CURRICULUM_ROOT / args.level / "orchestration" / slug / "skeleton.md"
        if existing_skeleton.exists():
            skeleton_text = existing_skeleton.read_text("utf-8")
            _log(f"  📐 Loaded existing skeleton ({len(skeleton_text.split())} words)")

    # Step 5: WRITE + QUICK VERIFY + RETRY
    content_path = None
    if steps in ("all", "write"):
        content_path = step_write_with_retry(
            args.level, args.module, slug, packet_path,
            writer=args.writer, max_retries=2,
            skeleton=skeleton_text,
        )
        if not content_path:
            _log("\n❌ Build FAILED at Step 5 (write — all retries exhausted)")
            sys.exit(1)
        _save_v6_state(args.level, slug, "write")
    else:
        content_path = CURRICULUM_ROOT / args.level / f"{slug}.md"

    # Step 5b: EXERCISES
    if steps in ("all", "exercises"):
        step_exercises(content_path)
        _save_v6_state(args.level, slug, "exercises")

    # Step 6: ANNOTATE
    if steps in ("all", "annotate"):
        step_annotate(content_path)
        _save_v6_state(args.level, slug, "annotate")

    # Step 7b: ENRICH
    if steps in ("all", "enrich"):
        step_enrich(content_path, args.level, slug)
        _save_v6_state(args.level, slug, "enrich")

    # Step 7: VERIFY
    if steps in ("all", "verify"):
        step_verify(content_path, args.level, args.module)
        _save_v6_state(args.level, slug, "verify")

    # Step 8: REVIEW with retry loop
    # If review fails, inject findings as correction directive and rebuild
    max_review_retries = 3
    if steps in ("all", "review"):
        for review_attempt in range(1, max_review_retries + 1):
            _log(f"\n  📋 Review attempt {review_attempt}/{max_review_retries}")

            passed, score, review_text = step_review(
                content_path, args.level, args.module, slug,
                writer=args.writer,
            )
            _save_v6_state(args.level, slug, "review")

            if passed:
                _log(f"\n✅ Review PASSED on attempt {review_attempt} ({score}/10)")
                break

            if review_attempt >= max_review_retries:
                _log(f"\n⚠️  Review failed after {max_review_retries} attempts ({score}/10) — flag for human")
                break

            # Build correction directive from review findings
            correction = _build_review_correction(review_text)
            _log(f"  🔄 Rebuilding with review correction directive ({len(correction)} chars)...")

            # Save correction for inspection
            orch_dir = CURRICULUM_ROOT / args.level / "orchestration" / slug
            orch_dir.mkdir(parents=True, exist_ok=True)
            corr_path = orch_dir / f"review-correction-{review_attempt}.md"
            corr_path.write_text(correction, "utf-8")

            # Re-run WRITE → EXERCISES → ANNOTATE → ENRICH → VERIFY
            content_path = step_write(
                args.level, args.module, slug, packet_path,
                writer=args.writer,
                correction_directive=correction,
                skeleton=skeleton_text,
            )
            if not content_path:
                _log("  ❌ Rebuild failed — writer returned no output")
                break

            step_exercises(content_path)
            step_annotate(content_path)
            step_enrich(content_path, args.level, slug)
            step_verify(content_path, args.level, args.module)

    # Step 9: PUBLISH
    if steps in ("all", "publish"):
        step_publish(content_path, args.level, slug)
        _save_v6_state(args.level, slug, "publish")

    _log(f"\n✅ V6 Build COMPLETE: {args.level.upper()} M{args.module:02d} ({slug})")


if __name__ == "__main__":
    main()
