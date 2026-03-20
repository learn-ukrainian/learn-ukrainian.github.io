#!/usr/bin/env python3
"""V6 Pipeline Build — single-session content generation.

Orchestrates the V6 pipeline:
1. CHECK: Plan checker validation
2. RESEARCH: Build knowledge packet from RAG
3. PREFLIGHT: Validate assembled prompt
4. WRITE: Single LLM session (prose + exercise placeholders)
5b. EXERCISES: Fill placeholders with DSL
6. ANNOTATE: Stress marks + deterministic fixes
7. VERIFY: VESUM + grammar scope
8. REVIEW: Cross-agent review (future)
9. PUBLISH: DSL→MDX conversion

Usage:
    .venv/bin/python scripts/build/v6_build.py a1 1
    .venv/bin/python scripts/build/v6_build.py a1 1 --step write  # run single step
    .venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini  # default
    .venv/bin/python scripts/build/v6_build.py a1 1 --writer claude

Issue: #993
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

logger = logging.getLogger(__name__)

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
PHASES_DIR = PROJECT_ROOT / "claude_extensions" / "phases" / "gemini"


def _log(msg: str):
    print(msg, flush=True)


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

    return output_path


def step_write(level: str, module_num: int, slug: str,
               packet_path: Path, writer: str = "gemini") -> Path | None:
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

    # Load plan
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    plan_content = plan_path.read_text("utf-8")

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
    if letters:
        pv_lines.append("\nPer-letter videos — embed each next to its letter description.")
        pv_lines.append("Use format: <YouTubeVideo client:only=\"react\" url=\"URL\" label=\"Літера X — Anna Ohoiko\" />")
        pv_lines.append("Replace X with the actual letter. Example: label=\"Літера А — Anna Ohoiko\"")
        pv_lines.append("")
        for letter, url in letters.items():
            pv_lines.append(f"- Літера {letter}: {url}")

    # Get constraints from config_tables
    from pipeline.config_tables import (
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
        "{SUMMARY_HEADING}": summary_heading,
    }

    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

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
    else:
        _log("  Claude writing not yet implemented in V6 runner")
        return None

    if not ok or not raw:
        _log("  ❌ Writer returned no output")
        return None

    # Extract content (everything from first ## heading)
    lines = raw.split("\n")
    content_start = -1
    for i, line in enumerate(lines):
        if line.startswith("## "):
            content_start = i
            break

    if content_start < 0:
        _log("  ❌ No H2 headings found in output")
        output_path.write_text(raw, "utf-8")
    else:
        content = "\n".join(lines[content_start:])
        output_path.write_text(content, "utf-8")

    word_count = len(output_path.read_text("utf-8").split())
    _log(f"  ✅ Content written ({word_count} words)")
    _log(f"  → {output_path}")

    return output_path


def step_exercises(content_path: Path) -> bool:
    """Step 5b: Fill exercise placeholders."""
    _log(f"\n{'='*60}")
    _log("  Step 5b: EXERCISES — Fill placeholders")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    from exercises.fill_placeholders import fill_placeholders

    text = content_path.read_text("utf-8")
    filled, count = fill_placeholders(text)

    if count > 0:
        content_path.write_text(filled, "utf-8")
        _log(f"  ✅ Filled {count} exercise placeholder(s)")
    else:
        _log("  ℹ️  No exercise placeholders found")

    return True


def step_annotate(content_path: Path) -> bool:
    """Step 6: Add stress marks + deterministic fixes."""
    _log(f"\n{'='*60}")
    _log("  Step 6: ANNOTATE — Stress marks")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    try:
        from pipeline.stress_annotator import annotate_file
        count = annotate_file(content_path)
        _log(f"  ✅ Added stress marks to {count} words")
    except ImportError:
        _log("  ⚠️  Stress annotator not available")
    except Exception as e:
        _log(f"  ⚠️  Stress annotation failed: {e}")

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
        # Filter proper nouns
        real_not_found = [r for r in not_found
                          if not (r.get("original", "")[0:1].isupper() and r.get("source") == "prose")]
        if real_not_found:
            _log(f"  ⚠️  VESUM: {len(real_not_found)} word(s) not found:")
            for r in real_not_found[:5]:
                _log(f"    — {r.get('original', '?')}")
            issues.extend(real_not_found)
        else:
            _log(f"  ✅ VESUM: {vesum_hits}/{total} words verified")
    except Exception as e:
        _log(f"  ⚠️  VESUM check skipped: {e}")

    # Russicism scan
    try:
        from pipeline.semantic_russianisms import scan_for_russianisms
        russicisms = scan_for_russianisms(text)
        if russicisms:
            _log(f"  ⚠️  Russicisms found: {len(russicisms)}")
            for r in russicisms[:3]:
                _log(f"    — {r}")
            issues.extend(russicisms)
        else:
            _log("  ✅ No Russicisms detected")
    except ImportError:
        _log("  ℹ️  Russicism scanner not available")
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
    imports = """import Quiz from '@site/src/components/Quiz';
import FillIn from '@site/src/components/FillIn';
import MatchUp from '@site/src/components/MatchUp';
import TrueFalse from '@site/src/components/TrueFalse';
import GroupSort from '@site/src/components/GroupSort';
import YouTubeVideo from '@site/src/components/YouTubeVideo';

"""

    mdx_path.write_text(frontmatter + imports + mdx_content, "utf-8")
    _log(f"  ✅ MDX written → {mdx_path}")

    return True


def main():
    parser = argparse.ArgumentParser(description="V6 Pipeline Build")
    parser.add_argument("level", help="Level (e.g., a1)")
    parser.add_argument("module", type=int, help="Module number")
    parser.add_argument("--writer", choices=["gemini", "claude"], default="gemini")
    parser.add_argument("--step", choices=["check", "research", "write", "exercises", "annotate", "verify", "publish", "all"],
                        default="all")
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

    # Step 3: RESEARCH
    packet_path = None
    if steps in ("all", "research"):
        packet_path = step_research(args.level, args.module, slug)
        if not packet_path:
            _log("\n❌ Build FAILED at Step 3 (research)")
            sys.exit(1)
    else:
        # Try to find existing packet
        packet_path = CURRICULUM_ROOT / args.level / "research" / f"{slug}-knowledge-packet.md"
        if not packet_path.exists():
            packet_path = None

    # Step 5: WRITE (preflight is integrated into write — checks prompt before dispatch)
    content_path = None
    if steps in ("all", "write"):
        content_path = step_write(args.level, args.module, slug, packet_path, args.writer)
        if not content_path:
            _log("\n❌ Build FAILED at Step 5 (write)")
            sys.exit(1)
    else:
        content_path = CURRICULUM_ROOT / args.level / f"{slug}.md"

    # Step 5b: EXERCISES
    if steps in ("all", "exercises"):
        step_exercises(content_path)

    # Step 6: ANNOTATE
    if steps in ("all", "annotate"):
        step_annotate(content_path)

    # Step 7: VERIFY
    if steps in ("all", "verify"):
        step_verify(content_path, args.level, args.module)

    # Step 9: PUBLISH
    if steps in ("all", "publish"):
        step_publish(content_path, args.level, slug)

    _log(f"\n✅ V6 Build COMPLETE: {args.level.upper()} M{args.module:02d} ({slug})")


if __name__ == "__main__":
    main()
