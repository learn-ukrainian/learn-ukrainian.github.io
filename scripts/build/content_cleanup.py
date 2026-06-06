"""Deterministic post-review content cleanup — strip LLM artifacts.

Extracted from ``v6_build.py`` (#2747 slice 3) so the live post-processor
registry (``post_processors/_migrations.py``) can run this mutator without
importing the OBSOLETE ``v6_build`` module. The function is pure
stdlib + ``yaml`` — no sqlite, research, or pipeline imports — so pulling
it in is cheap (which is the whole reason ``_migrations`` resolves callables
lazily).

``v6_build`` re-imports ``post_process_content`` under its historical name
``_post_process_content`` so its own build flow and the existing test
monkeypatches keep working unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

# Project curriculum root. Defined locally (matching learner_immersion.py /
# orch_index.py) so this module has no dependency on v6_build's globals.
# This file lives at scripts/build/, so parents[2] is the repo root.
CURRICULUM_ROOT = Path(__file__).resolve().parents[2] / "curriculum" / "l2-uk-en"


def _log(msg: str) -> None:
    print(msg, flush=True)


def post_process_content(content_path: Path) -> int:
    """Deterministic post-processing: strip LLM artifacts."""
    text = content_path.read_text("utf-8")
    original_len = len(text)
    fixes = 0

    # 1. Strip duplicate summary section (LLM sometimes writes two)
    # Keep the first "## Підсумок" or "## Summary", remove subsequent ones
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
    # .md files should contain only prose — no TAB markers (#1124)
    if "<!-- TAB:" in text:
        tab_pos = text.index("<!-- TAB:")
        text = text[:tab_pos].rstrip() + "\n"
        fixes += 1
        _log("  🔧 Stripped writer-generated tab markers")

    # 6. Strip writer-generated YouTube video embeds ONLY when plan has pronunciation_videos
    # (publish step will add them properly). Seminar modules without pronunciation_videos
    # may legitimately embed inline videos — don't strip those. (Gemini review #9)
    slug = content_path.stem
    level_dir = content_path.parent.name
    plan_path = CURRICULUM_ROOT / "plans" / level_dir / f"{slug}.yaml"
    has_plan_videos = False
    if plan_path.exists():
        try:
            plan_data = yaml.safe_load(plan_path.read_text("utf-8"))
            has_plan_videos = bool(plan_data.get("pronunciation_videos"))
        except Exception:
            pass
    if has_plan_videos:
        video_pattern = re.compile(r'\n*<YouTubeVideo\s[^>]*/?>\s*\n*')
        new_text = video_pattern.sub("\n", text)
        if new_text != text:
            video_count = text.count("<YouTubeVideo") - new_text.count("<YouTubeVideo")
            fixes += 1
            text = new_text
            _log(f"  🔧 Stripped {video_count} writer-generated YouTube embeds (ENRICH handles videos)")

    # 7. Strip motivational closers — LLMs consistently produce these despite prompting
    motivational_patterns = [
        r"By mastering these[^.]*\.",
        r"You have successfully[^.]*\.",
        r"Your journey[^.]*has officially begun[^.]*\.",
        r"You now have the (?:foundational )?tools[^.]*\.",
        r"you have laid the groundwork[^.]*\.",
        r"you are (?:now )?ready to[^.]*\.",
    ]
    for pat in motivational_patterns:
        new_text = re.sub(pat, "", text, flags=re.IGNORECASE)
        if new_text != text:
            fixes += 1
            text = new_text
            _log(f"  🔧 Stripped motivational closer: {pat[:40]}...")

    # Clean up double blank lines from stripped content
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 8. Gemini style cleanup — strip empty intensifiers (deterministic, pre-review)
    # These inflate prose without adding meaning. The write prompt bans them,
    # but Gemini uses them anyway. Cheaper to strip here than waste review rounds.
    _BANNED_INTENSIFIERS = [
        "надзвичайно", "абсолютно", "буквально", "безумовно",
        "неймовірно", "колосально", "грандіозно", "шалено",
        "фантастично",
    ]
    intensifier_count = 0
    for word in _BANNED_INTENSIFIERS:
        # Match the word with optional trailing comma/space, case-insensitive
        # Don't strip if it's inside a quoted source (between «»)
        pattern = re.compile(rf"\b{word}\b\s*,?\s*", re.IGNORECASE)
        matches = pattern.findall(text)
        if matches and len(matches) > 2:
                text = pattern.sub("", text)
                intensifier_count += len(matches)
    if intensifier_count:
        # Fix capitalization after removal (lowercase letter after period)
        text = re.sub(r'(\.\s+)([а-яіїєґ])', lambda m: m.group(1) + m.group(2).upper(), text)
        fixes += 1
        _log(f"  🔧 Stripped {intensifier_count} empty intensifiers (Gemini style cleanup)")

    # 9. Strip stray single quotes from exercise DSL values
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
