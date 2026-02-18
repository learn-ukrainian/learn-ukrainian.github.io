#!/usr/bin/env python3
"""Deterministic Python Module Builder.

Replaces LLM-orchestrated SKILL.md with a deterministic Python pipeline.
Gemini only gets called for LLM tasks (research, content writing, reviewing).
State, cleanup, resume, verification — all in Python.

Usage:
    .venv/bin/python scripts/build_module.py {track} {num}                  # full pipeline (resume-aware)
    .venv/bin/python scripts/build_module.py {track} {num} --content-only   # prose only (phases 0-6b)
    .venv/bin/python scripts/build_module.py {track} {num} --enrich         # activities only (phases 3+7)
    .venv/bin/python scripts/build_module.py {track} {num} --verify         # just run audit, print PASS/FAIL
    .venv/bin/python scripts/build_module.py {track} {num} --rebuild        # nuke state, rebuild from Phase 0
    .venv/bin/python scripts/build_module.py {track} {num} --force-phase 2  # re-run specific phase only
    .venv/bin/python scripts/build_module.py {track} {num} --dry-run        # show plan without dispatching
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from batch_gemini_config import (
    CURRICULUM_DIR,
    PHASES_DIR,
    PRO_MODEL,
    PROJECT_ROOT,
    SEMINAR_TRACKS,
    get_module_paths,
    get_track_config,
    slug_for_num,
)

import yaml

# ---------------------------------------------------------------------------
# 1. Config Tables (data only, no logic)
# ---------------------------------------------------------------------------

TRACK_SKILLS: dict[str, tuple[str, str, str]] = {
    # track_pattern: (skill_file, skill_identity, persona_flavor)
    "a1":       ("full-rebuild-core-a", "Patient & Supportive Ukrainian Tutor", "The Helpful Neighbor"),
    "a2":       ("full-rebuild-core-a", "Patient & Supportive Ukrainian Tutor", "The Helpful Neighbor"),
    "b1-early": ("full-rebuild-core-a", "Patient & Supportive Ukrainian Tutor", "The Helpful Neighbor"),
    "b1-late":  ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "b2":       ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "b2-pro":   ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "c1":       ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "c1-pro":   ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "c2":       ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "c1-bio":   ("full-rebuild-c1-bio", "Professor of Ukrainian Arts (biography)", "The Archival Detective"),
    "b2-hist":  ("full-rebuild-b2-hist", "Professor of Ukrainian Arts (history)", "The Decolonial Lecturer"),
    "c1-hist":  ("full-rebuild-c1-hist", "Professor of Ukrainian Arts (historiography)", "The Source Critic"),
    "lit":      ("full-rebuild-lit", "Professor of Ukrainian Arts (literature)", "The Stylistic Critic"),
    "oes":      ("full-rebuild-oes", "Professor of Ukrainian Arts (paleography)", "The Paleographer"),
    "ruth":     ("full-rebuild-ruth", "Professor of Ukrainian Arts (Ruthenian)", "The Baroque Scholar"),
}

IMMERSION_RULES: dict[str, str] = {
    "a1-m01-02": (
        "TARGET: 5-15% Ukrainian, 85-95% English. ALL explanatory prose in English. "
        "ALL grammar explanations in English. ALL callout text in English. Ukrainian appears ONLY in: "
        "(1) example words/phrases in bold with [IPA] and (English translation), (2) vocabulary items. "
        "If you write a paragraph, it MUST be in English. Ukrainian sentences max 10 words."
    ),
    "a1-m03-05": (
        "TARGET: 10-25% Ukrainian, 75-90% English. ALL explanatory prose in English. "
        "Grammar explained in English. Ukrainian in examples and short phrases only — always with English translations. "
        "Callout text in English. Ukrainian sentences max 10 words."
    ),
    "a1-m06-10": (
        "TARGET: 15-35% Ukrainian, 65-85% English. Explanatory prose primarily in English. "
        "Grammar concepts explained in English with Ukrainian terminology introduced (bolded, with translation on first use). "
        "Examples increasingly in Ukrainian with translations. Callout text in English. Ukrainian sentences max 10 words."
    ),
    "a1-m11-20": (
        "TARGET: 25-40% Ukrainian, 60-75% English. Grammar RULES explained in English. "
        "But cultural notes, practical sections, and observations USE simple Ukrainian (2-3 sentence paragraphs, "
        "max 10 words per sentence) with English gloss in parentheses for new words. "
        "Provide 3-4 Ukrainian examples per grammar point (not just 1-2). "
        "Practice/drill instructions in Ukrainian. Some callout/tip text in Ukrainian. "
        "The student reads simple Ukrainian — use it for concrete, practical content "
        "while keeping abstract grammar explanations in English."
    ),
    "a1-m21+": (
        "TARGET: 35-55% Ukrainian, 45-65% English. Explanatory prose mixed — short Ukrainian sentences "
        "woven into English explanations. Grammar still anchored in English. "
        "Examples primarily Ukrainian with translations. Ukrainian sentences max 10 words."
    ),
    "a2-m01-20": (
        "TARGET: 50-60% Ukrainian, 40-50% English. Grammar theory in English, dialogues and examples in Ukrainian. "
        "Section intros can mix languages. Ukrainian sentences max 15 words. Max 2 clauses. "
        "All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles."
    ),
    "a2-m21-50": (
        "TARGET: 60-75% Ukrainian, 25-40% English. English only for abstract grammar concepts. "
        "Ukrainian for everything else — examples, dialogues, cultural context. "
        "Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. "
        "Simple subordinate clauses only. Aspect pairs introduced. No participles."
    ),
    "a2-m51-70": (
        "TARGET: 75-90% Ukrainian, 10-25% English. English only in vocabulary tables and brief grammar notes. "
        "Near-full Ukrainian immersion. Ukrainian sentences max 15 words. Max 2 clauses. "
        "All cases allowed. Simple subordinate clauses only. Full aspect pairs. No participles."
    ),
    "b1-bridge": (
        "Bridge modules: teach grammar metalanguage. English scaffolding for abstract concepts. "
        "Parenthetical equivalents for new terms. Sentences max 30 words."
    ),
    "b1-core": (
        "Full Ukrainian immersion. Grammar explained IN Ukrainian. "
        "English only for disambiguation of false friends. Sentences max 30 words."
    ),
    "b2+": (
        "Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words."
    ),
}

LEVEL_CONSTRAINTS: dict[str, str] = {
    "a1": (
        "HARD GRAMMAR RULES (audit will reject violations):\n"
        "- Max 10 words per Ukrainian sentence (STRICT — count every word)\n"
        "- ONLY 1 clause per sentence (no compound sentences)\n"
        "- Dative case FORBIDDEN (no мені, тобі, йому, їй, нам, вам, їм, -ові/-еві endings)\n"
        "- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)\n"
        "- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED\n"
        "- Only imperfective aspect verbs\n"
        "- No participles\n"
        "- Allowed cases: Nominative, Accusative, Locative (from M13), Genitive (basics), Vocative"
    ),
    "a2": (
        "GRAMMAR RULES:\n"
        "- Max 15 words per Ukrainian sentence\n"
        "- Max 2 clauses per sentence\n"
        "- All cases allowed\n"
        "- Simple subordinate clauses allowed (який/що/коли)\n"
        "- Aspect pairs introduced but not complex\n"
        "- No participles"
    ),
    "b1": (
        "GRAMMAR RULES:\n"
        "- Max 30 words per Ukrainian sentence\n"
        "- Max 4 clauses per sentence\n"
        "- All grammar constructions allowed\n"
        "- Participles allowed\n"
        "- Complex subordinate clauses allowed"
    ),
    "b2": (
        "GRAMMAR RULES:\n"
        "- Max 35 words per Ukrainian sentence\n"
        "- Max 6 clauses\n"
        "- Full grammar including adverbial participles"
    ),
    "c1": "No grammar restrictions. Full literary Ukrainian.",
    "c2": "No grammar restrictions. Full literary Ukrainian.",
}

# Activity configs per track/level
ACTIVITY_CONFIGS: dict[str, dict[str, str]] = {
    "a1": {
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "8", "ITEMS_MIN": "12",
        "VOCAB_COUNT_TARGET": "20",
        "FORBIDDEN_ACTIVITY_TYPES": "cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, anagram, unjumble, group-sort",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, match-up, anagram, unjumble, quiz",
    },
    "a2": {
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "10", "ITEMS_MIN": "12",
        "VOCAB_COUNT_TARGET": "25",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, essay-response, critical-analysis, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "error-correction, unjumble, fill-in",
    },
    "b1-bridge": {
        "ACTIVITY_COUNT_TARGET": "6", "ACTIVITY_MIN": "4", "ITEMS_MIN": "6",
        "VOCAB_COUNT_TARGET": "25",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, essay-response, critical-analysis",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "quiz, match-up, fill-in, error-correction, mark-the-words",
    },
    "b1-core": {
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "8", "ITEMS_MIN": "12",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, essay-response, critical-analysis, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, unjumble, error-correction",
    },
    "b2": {
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "10", "ITEMS_MIN": "14",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, select, translate",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, unjumble, error-correction",
    },
    "c1-core": {
        "ACTIVITY_COUNT_TARGET": "14", "ACTIVITY_MIN": "12", "ITEMS_MIN": "12",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, select, translate",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, unjumble, error-correction",
    },
    "c2": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, quiz, true-false",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "reading, essay-response, critical-analysis",
    },
    "b2-hist": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "25",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, fill-in, cloze, match-up, error-correction, unjumble, mark-the-words, group-sort, select, translate, anagram",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, true-false",
        "REQUIRED_TYPES": "reading, essay-response", "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study",
    },
    "c1-bio": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, authorial-intent, quiz, true-false",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, authorial-intent, quiz",
    },
    "c1-hist": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, quiz, true-false",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study",
    },
    "lit": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "0",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, authorial-intent, true-false",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study",
    },
    "b2-pro": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "35",
        "FORBIDDEN_ACTIVITY_TYPES": "",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, quiz, true-false",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "reading, essay-response, critical-analysis",
    },
    "c1-pro": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "40",
        "FORBIDDEN_ACTIVITY_TYPES": "",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, quiz, true-false",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "reading, essay-response, critical-analysis",
    },
    "oes": {
        "ACTIVITY_COUNT_TARGET": "7", "ACTIVITY_MIN": "6", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "35",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words, group-sort, select, translate",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, etymology-trace, transcription, grammar-identify, phonology-lab, grammar-lab, parallel-text, paleography-analysis, historical-writing, loanword-trace",
        "REQUIRED_TYPES": "transcription, etymology-trace, grammar-identify",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, etymology-trace, transcription, grammar-identify, phonology-lab, grammar-lab, parallel-text, paleography-analysis, historical-writing, loanword-trace",
    },
    "ruth": {
        "ACTIVITY_COUNT_TARGET": "7", "ACTIVITY_MIN": "6", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "35",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words, group-sort, select, translate",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, transcription, etymology-trace, grammar-identify, grammar-lab, parallel-text, paleography-analysis, historical-writing, register-identify, loanword-trace, comparative-style",
        "REQUIRED_TYPES": "transcription, etymology-trace, grammar-identify",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, transcription, etymology-trace, grammar-identify, grammar-lab, parallel-text, paleography-analysis, historical-writing, register-identify, loanword-trace, comparative-style",
    },
}


# ---------------------------------------------------------------------------
# 2. Resolver Functions
# ---------------------------------------------------------------------------

def get_track_skill(track: str, module_num: int) -> tuple[str, str, str]:
    """Return (skill_file, skill_identity, persona_flavor) for a track + module number."""
    # B1 split rule
    if track == "b1":
        key = "b1-early" if module_num <= 5 else "b1-late"
        return TRACK_SKILLS[key]

    # Lit sub-genres map to "lit"
    if track.startswith("lit-"):
        return TRACK_SKILLS["lit"]

    if track in TRACK_SKILLS:
        return TRACK_SKILLS[track]

    # Fallback: core-b for unknown
    return TRACK_SKILLS["b2"]


def get_immersion_rule(track: str, module_num: int) -> str:
    """Compute immersion rule from track + module number."""
    base = track.split("-")[0] if track not in ("b2-hist", "c1-bio", "c1-hist", "b2-pro", "c1-pro") else track

    if base == "a1":
        if module_num <= 2:
            return IMMERSION_RULES["a1-m01-02"]
        elif module_num <= 5:
            return IMMERSION_RULES["a1-m03-05"]
        elif module_num <= 10:
            return IMMERSION_RULES["a1-m06-10"]
        elif module_num <= 20:
            return IMMERSION_RULES["a1-m11-20"]
        else:
            return IMMERSION_RULES["a1-m21+"]
    elif base == "a2":
        if module_num <= 20:
            return IMMERSION_RULES["a2-m01-20"]
        elif module_num <= 50:
            return IMMERSION_RULES["a2-m21-50"]
        else:
            return IMMERSION_RULES["a2-m51-70"]
    elif base == "b1":
        if module_num <= 5:
            return IMMERSION_RULES["b1-bridge"]
        else:
            return IMMERSION_RULES["b1-core"]
    else:
        return IMMERSION_RULES["b2+"]


def get_level_constraints(track: str) -> str:
    """Get grammar constraint text for the base level."""
    base = track.split("-")[0]
    return LEVEL_CONSTRAINTS.get(base, LEVEL_CONSTRAINTS["c1"])


def get_activity_config(track: str, module_num: int) -> dict[str, str]:
    """Get activity configuration for a track + module number."""
    # Lit sub-genres all use "lit"
    if track.startswith("lit-"):
        return ACTIVITY_CONFIGS["lit"]

    if track == "b1":
        return ACTIVITY_CONFIGS["b1-bridge" if module_num <= 5 else "b1-core"]

    if track == "c1":
        return ACTIVITY_CONFIGS["c1-core"]

    if track in ACTIVITY_CONFIGS:
        return ACTIVITY_CONFIGS[track]

    # Fallback
    return ACTIVITY_CONFIGS["b2"]


def get_level_label(track: str) -> str:
    """Get human-readable level label (e.g., 'A1', 'C1-BIO')."""
    return track.upper().replace("-", "_").rstrip("_")


# ---------------------------------------------------------------------------
# 3. ModuleContext Dataclass + State Helpers
# ---------------------------------------------------------------------------

@dataclass
class ModuleContext:
    """All paths, config, state for a module build."""
    track: str
    module_num: int
    slug: str
    mode: str  # "full", "content-only", "enrich"

    # Paths (populated by preflight)
    paths: dict[str, Path] = field(default_factory=dict)
    orch_dir: Path = field(default=Path("."))

    # Plan/meta data
    plan: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)
    word_target: int = 0
    topic_title: str = ""
    content_outline: list[dict] = field(default_factory=list)

    # Config from tables
    skill_name: str = ""
    skill_identity: str = ""
    persona_flavor: str = ""
    immersion_rule: str = ""
    level_constraints: str = ""
    activity_config: dict[str, str] = field(default_factory=dict)
    model: str = PRO_MODEL

    # Track config from batch_gemini_config
    track_config: dict = field(default_factory=dict)

    # State tracking
    state: dict = field(default_factory=dict)
    state_path: Path = field(default=Path("."))

    # CLI flags
    dry_run: bool = False
    force_phase: str | None = None
    rebuild: bool = False


def _state_file(ctx: ModuleContext) -> Path:
    return ctx.orch_dir / "state.json"


def load_state(ctx: ModuleContext) -> dict:
    """Load state.json or return fresh state."""
    sf = _state_file(ctx)
    if sf.exists():
        try:
            return json.loads(sf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "slug": ctx.slug,
        "track": ctx.track,
        "module_num": ctx.module_num,
        "mode": ctx.mode,
        "phases": {},
        "last_updated": _now_iso(),
    }


def save_state(ctx: ModuleContext) -> None:
    """Persist state.json atomically."""
    ctx.state["last_updated"] = _now_iso()
    tmp = _state_file(ctx).with_suffix(".tmp")
    tmp.write_text(json.dumps(ctx.state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.rename(_state_file(ctx))


def is_phase_complete(ctx: ModuleContext, phase: str) -> bool:
    """Check if a phase is marked complete in state."""
    if ctx.force_phase == phase:
        return False
    return ctx.state.get("phases", {}).get(phase, {}).get("status") == "complete"


def mark_phase(ctx: ModuleContext, phase: str, status: str, **extra: Any) -> None:
    """Update phase status in state and persist."""
    if ctx.dry_run:
        return
    if "phases" not in ctx.state:
        ctx.state["phases"] = {}
    entry = {"status": status, "timestamp": _now_iso()}
    entry.update(extra)
    ctx.state["phases"][phase] = entry
    save_state(ctx)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# 4. Gemini Dispatch Helpers
# ---------------------------------------------------------------------------

VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")


def run_script(args: list[str], capture: bool = False, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a script via .venv/bin/python with cwd=PROJECT_ROOT."""
    cmd = [VENV_PYTHON] + args
    return subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=capture,
        text=True, timeout=timeout,
    )


def fill_template(
    template: Path, placeholders_yaml: Path, output: Path,
    overrides: dict[str, str] | None = None, strict: bool = False,
) -> bool:
    """Fill a template via fill_template.py. Returns True on success."""
    args = [
        str(SCRIPTS_DIR / "fill_template.py"),
        "--template", str(template),
        "--placeholders", str(placeholders_yaml),
        "--output", str(output),
    ]
    if not strict:
        args.append("--no-strict")
    for k, v in (overrides or {}).items():
        args.extend(["--set", f"{k}={v}"])

    result = run_script(args, capture=True)
    if result.returncode != 0:
        log(f"  fill_template FAILED: {result.stderr or result.stdout}")
        return False
    return True


def dispatch_gemini(
    prompt: str, task_id: str, model: str = PRO_MODEL,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
) -> tuple[bool, str]:
    """Dispatch a prompt to Gemini via ai_agent_bridge.py ask-gemini.

    Returns (success, raw_output_text).
    """
    args = [
        str(SCRIPTS_DIR / "ai_agent_bridge.py"), "ask-gemini",
        prompt,
        "--task-id", task_id,
        "--model", model,
    ]
    if stdout_only:
        args.append("--stdout-only")
    if allow_write:
        args.append("--allow-write")

    try:
        result = subprocess.run(
            [VENV_PYTHON] + args,
            cwd=str(PROJECT_ROOT), capture_output=True, text=True,
            timeout=timeout,
        )
        output_text = result.stdout or ""
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(output_text, encoding="utf-8")
        return result.returncode == 0, output_text
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT: Gemini dispatch {task_id} exceeded {timeout}s")
        return False, ""


def extract_phase_output(
    input_file: Path, phase_key: str, output_dir: Path, attempt: int = 1,
    tags: list[str] | None = None,
) -> bool:
    """Extract delimited content via extract_phase.py. Returns True if all tags found.

    Args:
        tags: Override expected tags (bypasses PHASE_TAGS lookup). Output files
              still use --phase for naming (e.g., phase-3-activities.yaml).
    """
    args = [
        str(SCRIPTS_DIR / "extract_phase.py"),
        str(input_file),
        "--output-dir", str(output_dir),
        "--attempt", str(attempt),
    ]
    if tags:
        args.extend(["--tags"] + tags)
        # Still pass --phase for output filename prefix
        args.extend(["--phase", phase_key])
    else:
        args.extend(["--phase", phase_key])
    result = run_script(args, capture=True)
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            log(f"    {line}")
    return result.returncode == 0


def run_verify(content_path: Path, content_only: bool = True) -> tuple[bool, str]:
    """Run otaman_verify.py or hetman_verify.py. Returns (passed, output)."""
    script = "otaman_verify.py" if content_only else "hetman_verify.py"
    result = run_script([str(SCRIPTS_DIR / script), str(content_path)], capture=True, timeout=300)
    output = (result.stdout or "") + (result.stderr or "")
    passed = result.returncode == 0
    return passed, output


# ---------------------------------------------------------------------------
# 5. Phase Functions
# ---------------------------------------------------------------------------

MAX_FIX_ITERATIONS = 3
MAX_REVIEW_RETRIES = 2

TMP_DIR = Path("/tmp")


def _gemini_output_path(slug: str, phase: str) -> Path:
    return TMP_DIR / f"gemini-output-{slug}-phase-{phase}.txt"


def _dispatch_prompt(ctx: ModuleContext, prompt_file: Path) -> str:
    """Build the standard dispatch prompt string."""
    return (
        f"Activate skill {ctx.skill_name}. "
        f"Read and execute the instructions at {PROJECT_ROOT}/{prompt_file.relative_to(PROJECT_ROOT)}"
    )


def phase_0_research(ctx: ModuleContext) -> bool:
    """Phase 0: Research."""
    phase = "0"
    if is_phase_complete(ctx, phase):
        log("  Phase 0: SKIP (already complete)")
        return True

    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    template_name = "phase-0-research-seminar.md" if is_seminar else "phase-0-research-core.md"
    template = PHASES_DIR / template_name

    # Fill template
    prompt_file = ctx.orch_dir / "phase-0-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log(f"  Phase 0: DRY-RUN — would dispatch research ({template_name})")
        return True

    # Dispatch
    log("  Phase 0: Dispatching research...")
    output_file = _gemini_output_path(ctx.slug, "0")
    ok, _ = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"yw-{ctx.slug}-p0",
        model=ctx.model, stdout_only=True, output_file=output_file,
    )
    if not ok:
        log("  Phase 0: FAILED — Gemini dispatch error")
        return False

    # Extract
    if not extract_phase_output(output_file, "0", ctx.orch_dir):
        log("  Phase 0: FAILED — extraction error")
        return False

    # Copy to canonical research path
    extracted = ctx.orch_dir / "phase-0-research.md"
    if extracted.exists():
        ctx.paths["research"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extracted, ctx.paths["research"])
        log(f"  Phase 0: Research saved ({ctx.paths['research'].stat().st_size:,} bytes)")
    else:
        log("  Phase 0: FAILED — extracted file not found")
        return False

    mark_phase(ctx, phase, "complete", task_id=f"yw-{ctx.slug}-p0")
    return True


def phase_0_5_enrich_plan(ctx: ModuleContext) -> bool:
    """Phase 0.5: Enrich plan with research findings.

    Reads research + plan, dispatches to Gemini, merges enriched
    content_outline and vocabulary_hints back into the plan file.
    Delegates to v2's implementation if available, otherwise runs inline.
    """
    phase = "0.5"
    if is_phase_complete(ctx, phase):
        log("  Phase 0.5: SKIP (already complete)")
        return True

    # Skip if research doesn't exist
    research_path = ctx.paths.get("research")
    if not research_path or not research_path.exists():
        log("  Phase 0.5: SKIP — no research file (Phase 0 must run first)")
        return True

    # Quality gate: research must score 9+/10 to avoid enriching from thin research
    MIN_RESEARCH_SCORE = 9
    try:
        from research_quality import assess_research_compat
        info = assess_research_compat(research_path, ctx.track)
        if info and info.get("score") is not None:
            score = info["score"]
            if score < MIN_RESEARCH_SCORE:
                log(f"  Phase 0.5: SKIP — research quality {score}/10 < {MIN_RESEARCH_SCORE} threshold")
                return True
            log(f"  Phase 0.5: Research quality {score}/10 — proceeding")
    except ImportError:
        log("  Phase 0.5: WARNING — research_quality not available, skipping quality gate")

    plan_path = ctx.paths.get("plan")
    if not plan_path or not plan_path.exists():
        log("  Phase 0.5: SKIP — no plan file")
        return True

    # Check if plan already has enrichment markers
    plan_text = plan_path.read_text(encoding="utf-8")
    plan = yaml.safe_load(plan_text) or {}
    has_enrichment = any(
        "\u2014" in str(p) or "learner error:" in str(p) or "cultural hook:" in str(p)
        for section in plan.get("content_outline", [])
        for p in section.get("points", [])
    )
    if has_enrichment and not ctx.force_phase:
        log("  Phase 0.5: SKIP — plan already appears enriched")
        mark_phase(ctx, phase, "complete", note="already-enriched")
        return True

    template = PHASES_DIR / "phase-0-5-enrich-plan.md"
    if not template.exists():
        log(f"  Phase 0.5: SKIP — template not found: {template}")
        return True

    prompt_file = ctx.orch_dir / "phase-0-5-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log("  Phase 0.5: DRY-RUN — would dispatch plan enrichment")
        return True

    log("  Phase 0.5: Dispatching plan enrichment...")
    output_file = _gemini_output_path(ctx.slug, "0.5")
    ok, raw_output = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"yw-{ctx.slug}-p0.5",
        model=ctx.model, stdout_only=True, output_file=output_file,
    )
    if not ok:
        log("  Phase 0.5: FAILED — Gemini dispatch error")
        return False

    # Extract enrichment from delimiters
    if "===ENRICHMENT_START===" in raw_output and "===ENRICHMENT_END===" in raw_output:
        start = raw_output.index("===ENRICHMENT_START===") + len("===ENRICHMENT_START===")
        end = raw_output.index("===ENRICHMENT_END===")
        enrichment_text = raw_output[start:end].strip()
    else:
        log("  Phase 0.5: FAILED — no ENRICHMENT delimiters in output")
        return False

    try:
        enrichment = yaml.safe_load(enrichment_text) or {}
    except yaml.YAMLError as e:
        log(f"  Phase 0.5: FAILED — YAML parse error: {e}")
        (ctx.orch_dir / "phase-0-5-enrichment-raw.md").write_text(enrichment_text, encoding="utf-8")
        return False

    if not enrichment.get("content_outline"):
        log("  Phase 0.5: FAILED — no content_outline in enrichment")
        return False

    # Backup original plan
    (ctx.orch_dir / "phase-0-5-original-plan.yaml").write_text(plan_text, encoding="utf-8")
    # Save enrichment artifact
    (ctx.orch_dir / "phase-0-5-enrichment.yaml").write_text(
        yaml.dump(enrichment, allow_unicode=True, default_flow_style=False), encoding="utf-8",
    )

    # Merge: replace section points, extend vocabulary_hints
    enriched_sections = {}
    for section in enrichment.get("content_outline", []):
        name = section.get("section", "")
        if name:
            enriched_sections[name] = section.get("points", [])
    for section in plan.get("content_outline", []):
        name = section.get("section", "")
        if name in enriched_sections:
            section["points"] = enriched_sections[name]
    enriched_vocab = enrichment.get("vocabulary_hints")
    if enriched_vocab and isinstance(enriched_vocab, dict):
        plan_vocab = plan.setdefault("vocabulary_hints", {})
        for cat in ("required", "recommended"):
            if cat in enriched_vocab and enriched_vocab[cat]:
                plan_vocab[cat] = enriched_vocab[cat]

    # Strip forbidden keys
    for key in ("words", "word_target", "word_count"):
        plan.pop(key, None)

    plan_path.write_text(
        yaml.dump(plan, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    total_points = sum(len(s.get("points", [])) for s in plan.get("content_outline", []))
    log(f"  Phase 0.5: Plan enriched ({total_points} points)")

    mark_phase(ctx, phase, "complete", task_id=f"yw-{ctx.slug}-p0.5")
    return True


def phase_1_meta(ctx: ModuleContext) -> bool:
    """Phase 1: Meta rebuild (content_outline generation)."""
    phase = "1"
    if is_phase_complete(ctx, phase):
        log("  Phase 1: SKIP (already complete)")
        return True

    template = PHASES_DIR / "phase-1-meta.md"
    prompt_file = ctx.orch_dir / "phase-1-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log("  Phase 1: DRY-RUN — would dispatch meta rebuild")
        return True

    log("  Phase 1: Dispatching meta rebuild...")
    output_file = _gemini_output_path(ctx.slug, "1")
    ok, _ = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"yw-{ctx.slug}-p1",
        model=ctx.model, stdout_only=True, output_file=output_file,
    )
    if not ok:
        return False

    if not extract_phase_output(output_file, "1", ctx.orch_dir):
        return False

    # Apply META_OUTLINE to meta file
    extracted = ctx.orch_dir / "phase-1-meta_outline.md"
    if not extracted.exists():
        log("  Phase 1: FAILED — META_OUTLINE not extracted")
        return False

    # Parse the outline and update meta
    outline_text = extracted.read_text(encoding="utf-8")
    meta_path = ctx.paths["meta"]
    if _apply_meta_outline(meta_path, outline_text):
        # Reload meta for Phase 2
        ctx.meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        ctx.content_outline = ctx.meta.get("content_outline", [])
        log(f"  Phase 1: Meta updated ({len(ctx.content_outline)} sections)")
    else:
        log("  Phase 1: WARNING — could not apply outline to meta (continuing)")

    mark_phase(ctx, phase, "complete", task_id=f"yw-{ctx.slug}-p1")
    return True


def _apply_meta_outline(meta_path: Path, outline_text: str) -> bool:
    """Parse META_OUTLINE output and update content_outline in meta.yaml."""
    try:
        # The outline is typically YAML content
        outline_data = yaml.safe_load(outline_text)
        if not outline_data:
            return False

        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        if not meta:
            return False

        # Handle both direct list and dict-with-key formats
        if isinstance(outline_data, dict) and "content_outline" in outline_data:
            meta["content_outline"] = outline_data["content_outline"]
        elif isinstance(outline_data, list):
            meta["content_outline"] = outline_data
        else:
            return False

        meta_path.write_text(
            yaml.dump(meta, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        return True
    except Exception as e:
        log(f"    _apply_meta_outline error: {e}")
        return False


def _build_section_budget_table(sections: list, word_target: int) -> str:
    """Build a markdown table of section word budgets for the whole-module template."""
    rows = ["| Section | Target | Write Minimum (1.5x) |", "|---------|--------|---------------------|"]
    for section in sections:
        title, words = _parse_section(section)
        if words <= 0:
            words = word_target // max(len(sections), 1)
        rows.append(f"| {title} | {words} | {int(words * 1.5)} |")
    rows.append(f"| **Total** | **{word_target}** | **{int(word_target * 1.5)}** |")
    return "\n".join(rows)


def phase_2_content(ctx: ModuleContext) -> bool:
    """Phase 2: Content (whole-module, single Gemini call)."""
    phase = "2"
    if is_phase_complete(ctx, phase):
        log("  Phase 2: SKIP (already complete)")
        return True

    sections = ctx.content_outline
    if not sections:
        log("  Phase 2: FAILED — no content_outline in meta")
        return False

    num_sections = len(sections)
    engagement_min = ctx.meta.get("engagement_min", 4)
    example_min = ctx.meta.get("example_min", 8)
    overshoot = int(ctx.word_target * 1.5)

    log(f"  Phase 2: Whole-module generation ({num_sections} sections, target: {ctx.word_target}w, overshoot: {overshoot}w)")

    template = PHASES_DIR / "phase-2-content.md"
    placeholders_yaml = ctx.orch_dir / "placeholders.yaml"
    prompt_file = ctx.orch_dir / "phase-2-prompt.md"

    overrides = {
        "OVERSHOOT_TARGET": str(overshoot),
        "ENGAGEMENT_MIN": str(engagement_min),
        "EXAMPLE_MIN": str(example_min),
        "SECTION_BUDGET_TABLE": _build_section_budget_table(sections, ctx.word_target),
    }

    if not fill_template(template, placeholders_yaml, prompt_file, overrides=overrides):
        return False

    if ctx.dry_run:
        log("  Phase 2: DRY-RUN — would dispatch whole-module content generation")
        return True

    # Dispatch
    output_file = _gemini_output_path(ctx.slug, "2")
    ok, _ = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"yw-{ctx.slug}-p2",
        model=ctx.model, stdout_only=True, output_file=output_file,
    )
    if not ok:
        log("  Phase 2: FAILED — dispatch error")
        return False

    # Extract content from delimited output
    content_text = None
    if output_file.exists():
        raw = output_file.read_text(encoding="utf-8")
        content_text = _extract_delimited_content(raw, "===CONTENT_START===", "===CONTENT_END===")

    if not content_text:
        log("  Phase 2: FAILED — no delimited content extracted")
        return False

    # Write content file
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(content_text, encoding="utf-8")

    total_words = len(content_text.split())
    pct = total_words * 100 // max(ctx.word_target, 1)
    log(f"  Phase 2: {total_words} words written ({pct}% of {ctx.word_target} target)")

    # Fail-fast: too thin
    if total_words < ctx.word_target * 0.5:
        log(f"  Phase 2: FAIL-FAST — only {total_words}w vs {ctx.word_target}w target")
        return False

    mark_phase(ctx, phase, "complete")
    return True


def _parse_section(section: Any) -> tuple[str, int]:
    """Parse a content_outline section entry. Returns (title, words)."""
    if isinstance(section, dict):
        title = section.get("section", section.get("title", "Untitled"))
        words = section.get("words", 0)
        return str(title), int(words)
    return str(section), 0


def _build_seam_context(
    section_text: str, prev_summary: str, callout_types_used: str,
    statistics_cited: str = "", openers_used: str = "", bio_facts_used: str = "",
) -> tuple[str, str, str, str, str]:
    """Build seam context from a section's text.

    Returns updated (prev_summary, callout_types_used, statistics_cited,
    openers_used, bio_facts_used).
    Each H3 includes its lead sentence so subsequent sections know
    what claims/facts were already made (not just the topic name).
    """
    # Extract H3 headers with their lead sentences
    h3_blocks = re.split(r"^### ", section_text, flags=re.MULTILINE)
    h3_entries = []
    for block in h3_blocks[1:]:  # skip text before first H3
        lines = block.strip().split("\n")
        title = lines[0].strip()
        # Find first real prose line (skip blank, callouts, examples)
        lead = ""
        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("> ", "* ", "- ", "_Приклади", "| ", "```")):
                continue
            # Take first ~120 chars of the lead sentence
            lead = stripped[:120].rstrip()
            if len(stripped) > 120:
                lead += "..."
            break
        if lead:
            h3_entries.append(f"- ### {title}\n  → {lead}")
        else:
            h3_entries.append(f"- ### {title}")
    h3_list = "\n".join(h3_entries) if h3_entries else ""

    # Extract last 2-3 paragraphs (non-empty lines at end)
    paragraphs = [p.strip() for p in section_text.split("\n\n") if p.strip()]
    last_paras = "\n\n".join(paragraphs[-3:]) if paragraphs else ""

    if h3_list and last_paras:
        new_summary = f"{h3_list}\n---\n{last_paras}"
    elif h3_list:
        new_summary = h3_list
    else:
        new_summary = last_paras

    # Extract callout types
    callouts = re.findall(r"\[!([\w-]+)\]", section_text)
    if callouts:
        existing = set(callout_types_used.split(", ")) if callout_types_used else set()
        existing.update(callouts)
        existing.discard("")
        callout_types_used = ", ".join(sorted(existing))

    # --- NEW: Extract statistics cited (numbers with units) ---
    stat_set = set(statistics_cited.split(" | ")) if statistics_cited else set()
    # Match patterns like "450 гектарів", "15 тисяч", "1893 року", "5500 до н. е."
    stat_patterns = re.findall(
        r"(\d[\d\s]*(?:гектар\w*|га|тисяч\w*|осіб|рок\w*|до н\.\s*е\.|столі\w*|градус\w*|кв\.\s*м|кілометр\w*|метр\w*))",
        section_text,
    )
    for s in stat_patterns:
        normalized = " ".join(s.split())  # collapse whitespace
        stat_set.add(normalized)
    stat_set.discard("")
    statistics_cited = " | ".join(sorted(stat_set)) if stat_set else ""

    # --- NEW: Extract rhetorical openers (first 3 words of each prose paragraph) ---
    opener_set = set(openers_used.split(" | ")) if openers_used else set()
    for para in section_text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        # Skip non-prose: headings, callouts, lists, tables, code blocks, examples
        if para.startswith(("#", ">", "* ", "- ", "| ", "```", "_Приклад")):
            continue
        # Skip short lines (likely formatting artifacts)
        words = para.split()
        if len(words) < 4:
            continue
        # Take first 3 words as the opener fingerprint
        opener = " ".join(words[:3])
        opener_set.add(opener)
    opener_set.discard("")
    openers_used = " | ".join(sorted(opener_set)) if opener_set else ""

    # --- NEW: Extract biographical facts from callouts ---
    bio_set = set(bio_facts_used.split(" | ")) if bio_facts_used else set()
    # Find [!biography] callout blocks and extract key claims
    bio_blocks = re.findall(
        r"\[!biography\].*?\n((?:>.*\n)*)", section_text, re.MULTILINE,
    )
    for block in bio_blocks:
        # Extract the first ~80 chars of the bio content as a fingerprint
        clean = re.sub(r"^>\s*", "", block, flags=re.MULTILINE).strip()
        lines = [l.strip() for l in clean.split("\n") if l.strip() and not l.strip().startswith("**")]
        if lines:
            bio_set.add(lines[0][:80].rstrip())
    bio_set.discard("")
    bio_facts_used = " | ".join(sorted(bio_set)) if bio_set else ""

    return new_summary, callout_types_used, statistics_cited, openers_used, bio_facts_used


def _sanitize_activities(path: Path) -> None:
    """Post-process generated activities YAML to fix common Gemini issues.

    - Remove 'hint'/'clue' fields from items (audit rejects them)
    - Convert hyphenated anagram scrambled to space-separated
    - Fix anagram letter mismatches (re-scramble from answer)
    - Cap match-up pairs at 10
    """
    import random
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return
        changed = False
        for activity in data:
            if not isinstance(activity, dict):
                continue
            atype = activity.get("type", "")

            # Cap match-up pairs at 10
            if atype == "match-up" and "pairs" in activity:
                if len(activity["pairs"]) > 10:
                    activity["pairs"] = activity["pairs"][:10]
                    changed = True

            for item in activity.get("items", []):
                if not isinstance(item, dict):
                    continue
                # Remove hint/clue fields
                for key in ("hint", "clue"):
                    if key in item:
                        del item[key]
                        changed = True
                # Fix anagram issues
                if atype == "anagram" and "scrambled" in item and "answer" in item:
                    s = item["scrambled"]
                    answer = item["answer"]
                    # Fix hyphenated: "а-б-в" → "а б в"
                    if "-" in s and " " not in s:
                        s = s.replace("-", " ")
                    # Verify letters match answer — if not, re-scramble
                    s_letters = sorted(s.replace(" ", "").lower())
                    a_letters = sorted(answer.lower())
                    if s_letters != a_letters:
                        letters = list(answer)
                        random.shuffle(letters)
                        # Avoid producing the answer itself
                        if "".join(letters) == answer and len(letters) > 1:
                            letters[0], letters[-1] = letters[-1], letters[0]
                        s = " ".join(letters)
                        changed = True
                    item["scrambled"] = s
        if changed:
            path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False),
                            encoding="utf-8")
    except Exception:
        pass  # Best-effort — audit will catch anything we miss


def phase_3a_activities(ctx: ModuleContext) -> bool:
    """Phase 3a: Activities generation (separate from vocabulary to avoid truncation)."""
    phase = "3a"
    if is_phase_complete(ctx, phase):
        log("  Phase 3a: SKIP (already complete)")
        return True

    template = PHASES_DIR / "phase-3-activities.md"
    prompt_file = ctx.orch_dir / "phase-3a-prompt.md"

    overrides = dict(ctx.activity_config)
    overrides["PHASE3_OUTPUT"] = "ACTIVITIES_ONLY"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file, overrides=overrides):
        return False

    if ctx.dry_run:
        log("  Phase 3a: DRY-RUN — would dispatch activities generation")
        return True

    log("  Phase 3a: Dispatching activities...")
    output_file = _gemini_output_path(ctx.slug, "3a")
    ok, _ = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file)
        + "\n\nIMPORTANT: Output ONLY the ===ACTIVITIES_START=== / ===ACTIVITIES_END=== block"
        + " and the ===FRICTION_START=== / ===FRICTION_END=== block."
        + " Do NOT output vocabulary. Vocabulary will be generated in a separate step.",
        task_id=f"yw-{ctx.slug}-p3a",
        model=ctx.model, stdout_only=True, output_file=output_file,
    )
    if not ok:
        return False

    if not extract_phase_output(output_file, "3", ctx.orch_dir, tags=["ACTIVITIES"]):
        # Retry once
        if not extract_phase_output(output_file, "3", ctx.orch_dir, tags=["ACTIVITIES"]):
            return False

    activities_extracted = ctx.orch_dir / "phase-3-activities.yaml"
    if activities_extracted.exists():
        ctx.paths["activities"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(activities_extracted, ctx.paths["activities"])
        _sanitize_activities(ctx.paths["activities"])
        log(f"  Phase 3a: Activities saved → {ctx.paths['activities'].name}")
    else:
        log("  Phase 3a: FAILED — no activities extracted")
        return False

    mark_phase(ctx, phase, "complete", task_id=f"yw-{ctx.slug}-p3a")
    return True


def phase_3b_vocabulary(ctx: ModuleContext) -> bool:
    """Phase 3b: Vocabulary generation (separate dispatch to avoid truncation)."""
    phase = "3b"
    if is_phase_complete(ctx, phase):
        log("  Phase 3b: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase 3b: DRY-RUN — would dispatch vocabulary generation")
        return True

    # Build a focused vocabulary prompt
    prompt = textwrap.dedent(f"""\
        # Phase 3b: Vocabulary Generation

        Generate the vocabulary list for module `{ctx.slug}`.

        ## Files to Read

        - Plan: `{ctx.paths['plan']}`
        - Meta: `{ctx.paths['meta']}`
        - Content: `{ctx.paths['md']}`

        ## Instructions

        1. Read the plan's vocabulary list
        2. Read the content file to see vocabulary in context
        3. Generate vocabulary YAML with: lemma, translation, pos, ipa, notes
        4. Target: {ctx.activity_config.get('VOCAB_COUNT_TARGET', '20')} items

        ## Output Format

        ```
        ===VOCABULARY_START===

        items:
          - lemma: "word"
            translation: "translation"
            pos: "noun"
            ipa: "[IPA]"

        ===VOCABULARY_END===
        ```

        Output ONLY the vocabulary block above. Nothing else.
    """)

    prompt_file = ctx.orch_dir / "phase-3b-prompt.md"
    prompt_file.write_text(prompt, encoding="utf-8")

    log("  Phase 3b: Dispatching vocabulary...")
    output_file = _gemini_output_path(ctx.slug, "3b")
    ok, _ = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"yw-{ctx.slug}-p3b",
        model=ctx.model, stdout_only=True, output_file=output_file,
    )
    if not ok:
        return False

    # Extract vocabulary — use tags override since phase "3" expects both
    args = [
        str(SCRIPTS_DIR / "extract_phase.py"),
        str(output_file),
        "--tags", "VOCABULARY",
        "--phase", "3",
        "--output-dir", str(ctx.orch_dir),
    ]
    result = run_script(args, capture=True)
    if result.returncode != 0:
        log(f"  Phase 3b: Extraction failed: {result.stderr or result.stdout}")
        return False

    vocab_extracted = ctx.orch_dir / "phase-3-vocabulary.yaml"
    if vocab_extracted.exists():
        ctx.paths["vocabulary"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(vocab_extracted, ctx.paths["vocabulary"])
        log(f"  Phase 3b: Vocabulary saved → {ctx.paths['vocabulary'].name}")
    else:
        log("  Phase 3b: FAILED — no vocabulary extracted")
        return False

    mark_phase(ctx, phase, "complete", task_id=f"yw-{ctx.slug}-p3b")
    return True


def phase_4_audit_fix(ctx: ModuleContext, content_only: bool = True) -> bool:
    """Phase 4: Audit + fix loop."""
    phase = "4" if content_only else "4-full"
    if is_phase_complete(ctx, phase):
        log(f"  Phase 4 ({'content-only' if content_only else 'full'}): SKIP (already complete)")
        return True

    if ctx.dry_run:
        log(f"  Phase 4: DRY-RUN — would run {'content-only' if content_only else 'full'} audit")
        return True

    for attempt in range(1, MAX_FIX_ITERATIONS + 1):
        log(f"  Phase 4: Audit attempt {attempt}/{MAX_FIX_ITERATIONS}...")
        passed, output = run_verify(ctx.paths["md"], content_only=content_only)

        # Save audit log
        log_file = ctx.orch_dir / f"audit-attempt-{attempt}.log"
        log_file.write_text(output, encoding="utf-8")

        if passed:
            log(f"  Phase 4: PASS (attempt {attempt})")
            mark_phase(ctx, phase, "complete", attempts=attempt)
            return True

        log(f"  Phase 4: FAIL (attempt {attempt})")

        if attempt >= MAX_FIX_ITERATIONS:
            log(f"  Phase 4: EXHAUSTED — {MAX_FIX_ITERATIONS} attempts failed")
            mark_phase(ctx, phase, "failed", attempts=attempt)
            return False

        # Build fix prompt from audit errors
        fix_prompt_file = ctx.orch_dir / f"phase-4-fix{attempt}-prompt.md"
        fix_prompt = _build_fix_prompt(ctx, output, content_only)
        fix_prompt_file.write_text(fix_prompt, encoding="utf-8")

        # Dispatch fix
        log(f"  Phase 4: Dispatching fix {attempt}...")
        fix_output = _gemini_output_path(ctx.slug, f"fix{attempt}")
        ok, raw_output = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"yw-{ctx.slug}-fix{attempt}",
            model=ctx.model, allow_write=True, output_file=fix_output,
        )
        if not ok:
            log(f"  Phase 4: Fix dispatch {attempt} failed")
            continue

        # Apply section-level fixes if Gemini returned delimited sections
        if fix_output.exists():
            fix_text = fix_output.read_text(encoding="utf-8")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)

    return False


def _apply_section_fixes(content_path: Path, fix_output: str) -> None:
    """Apply section-level fixes from delimited Gemini output.

    Expects format:
        ===SECTION_FIX_START===
        ## Section Title
        ...fixed content...
        ===SECTION_FIX_END===
    """
    # Extract all section fixes
    fixes = re.findall(
        r"===SECTION_FIX_START===\s*\n(.*?)===SECTION_FIX_END===",
        fix_output, re.DOTALL,
    )
    if not fixes:
        return

    content = content_path.read_text(encoding="utf-8")

    for fix_block in fixes:
        fix_block = fix_block.strip()
        # Extract the H2 title from the fix
        h2_match = re.match(r"^## (.+)$", fix_block, re.MULTILINE)
        if not h2_match:
            continue
        section_title = h2_match.group(1).strip()

        # Find and replace the section in the original content
        # Pattern: from "## Title" to the next "## " or end of file
        pattern = re.compile(
            rf"(^## {re.escape(section_title)}\s*\n)"  # Section header
            rf"(.*?)"                                    # Section body
            rf"(?=^## |\Z)",                             # Next section or EOF
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(content)
        if match:
            # Replace with fix block (which includes the ## header)
            replacement = fix_block + "\n\n"
            content = content[:match.start()] + replacement + content[match.end():]
            log(f"    Applied section fix: {section_title}")

    content_path.write_text(content, encoding="utf-8")


def _identify_affected_sections(audit_output: str, content_path: Path) -> list[str]:
    """Parse audit output to identify which H2 sections have issues.

    Returns a list of section titles (H2 headers) that contain errors.
    Returns empty list if issues are spread across many sections or can't be localized.
    """
    if not content_path.exists():
        return []

    content = content_path.read_text(encoding="utf-8")
    h2_headers = re.findall(r"^## (.+)$", content, re.MULTILINE)
    if not h2_headers:
        return []

    # Look for section references in audit output
    affected = set()
    audit_lower = audit_output.lower()
    for header in h2_headers:
        # Check if the header text appears near error indicators in the audit
        if header.lower() in audit_lower:
            affected.add(header)

    # Also check for line-number references — map line numbers to sections
    line_refs = re.findall(r"line\s+(\d+)", audit_output, re.IGNORECASE)
    if line_refs:
        lines = content.split("\n")
        current_section = None
        section_ranges: dict[str, tuple[int, int]] = {}
        for i, line in enumerate(lines, 1):
            m = re.match(r"^## (.+)$", line)
            if m:
                if current_section:
                    section_ranges[current_section] = (section_ranges[current_section][0], i - 1)
                current_section = m.group(1)
                section_ranges[current_section] = (i, len(lines))
        if current_section and current_section in section_ranges:
            section_ranges[current_section] = (section_ranges[current_section][0], len(lines))

        for ref in line_refs:
            line_num = int(ref)
            for header, (start, end) in section_ranges.items():
                if start <= line_num <= end:
                    affected.add(header)
                    break

    # Only return localized results (1-2 sections)
    if 1 <= len(affected) <= 2:
        return sorted(affected)
    return []


def _build_fix_prompt(ctx: ModuleContext, audit_output: str, content_only: bool) -> str:
    """Build a fix prompt from audit output.

    For large modules (4000+ words), attempts section-level targeting to avoid
    token truncation when asking Gemini to output the complete file.
    """
    lines = audit_output.strip().split("\n")
    error_excerpt = "\n".join(lines[-60:])

    fix_type = "content-only" if content_only else "full"

    # For content fixes on large modules, try section-level targeting
    section_fix = ""
    affected_sections = []
    if content_only and ctx.paths["md"].exists():
        word_count = len(ctx.paths["md"].read_text(encoding="utf-8").split())
        if word_count >= 3000:
            affected_sections = _identify_affected_sections(audit_output, ctx.paths["md"])
            if affected_sections:
                section_list = ", ".join(f'"{s}"' for s in affected_sections)
                section_fix = textwrap.dedent(f"""\

                    ## Section-Level Fix (IMPORTANT)

                    This is a large module ({word_count} words). To avoid token truncation,
                    fix ONLY the following section(s): {section_list}

                    **Output format:** Output ONLY the fixed section(s) between delimiters:

                    ```
                    ===SECTION_FIX_START===
                    ## {{section title}}
                    {{fixed section content}}
                    ===SECTION_FIX_END===
                    ```

                    Do NOT output the entire file. Only output the section(s) listed above.
                """)

    return textwrap.dedent(f"""\
        # Fix Phase — {fix_type} audit failures

        The following audit errors must be fixed for module `{ctx.slug}`:

        ## Audit Output (last 60 lines)

        ```
        {error_excerpt}
        ```

        ## Files to Fix

        - Content: `{ctx.paths['md']}`
        {"- Activities: `" + str(ctx.paths['activities']) + "`" if not content_only else ""}
        {"- Vocabulary: `" + str(ctx.paths['vocabulary']) + "`" if not content_only else ""}

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.
        {section_fix}
    """)


def phase_5_mdx(ctx: ModuleContext) -> bool:
    """Phase 5: MDX generation."""
    phase = "5"
    if is_phase_complete(ctx, phase):
        log("  Phase 5: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase 5: DRY-RUN — would generate MDX")
        return True

    log("  Phase 5: Generating MDX...")
    result = run_script([
        str(SCRIPTS_DIR / "generate_mdx.py"), "l2-uk-en", ctx.track, str(ctx.module_num),
    ], capture=True)

    if result.returncode != 0:
        log(f"  Phase 5: WARNING — MDX generation returned {result.returncode}")
        # Non-fatal: MDX gen can fail gracefully

    mark_phase(ctx, phase, "complete")
    return True


def _compute_audit_metrics(ctx: ModuleContext) -> dict[str, str]:
    """Compute audit metrics from actual module files for review templates."""
    metrics: dict[str, str] = {}

    # Word count
    content_path = ctx.paths["md"]
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())
        pct = word_count * 100 // max(ctx.word_target, 1)
        metrics["AUDIT_WORD_COUNT"] = str(word_count)
        metrics["WORD_PERCENT"] = str(pct)
    else:
        metrics["AUDIT_WORD_COUNT"] = "0"
        metrics["WORD_PERCENT"] = "0"

    # Activity count
    act_path = ctx.paths["activities"]
    if act_path.exists():
        try:
            act_data = yaml.safe_load(act_path.read_text(encoding="utf-8"))
            metrics["ACTIVITY_COUNT"] = str(len(act_data) if isinstance(act_data, list) else 0)
        except Exception:
            metrics["ACTIVITY_COUNT"] = "0"
    else:
        metrics["ACTIVITY_COUNT"] = "0"

    # Vocabulary count
    vocab_path = ctx.paths["vocabulary"]
    if vocab_path.exists():
        try:
            vocab_data = yaml.safe_load(vocab_path.read_text(encoding="utf-8"))
            if isinstance(vocab_data, list):
                metrics["VOCAB_COUNT"] = str(len(vocab_data))
            elif isinstance(vocab_data, dict):
                # Some vocab files have a top-level key wrapping the list
                for v in vocab_data.values():
                    if isinstance(v, list):
                        metrics["VOCAB_COUNT"] = str(len(v))
                        break
                else:
                    metrics["VOCAB_COUNT"] = "0"
            else:
                metrics["VOCAB_COUNT"] = "0"
        except Exception:
            metrics["VOCAB_COUNT"] = "0"
    else:
        metrics["VOCAB_COUNT"] = "0"

    # Engagement boxes (callout pattern [!type])
    if content_path.exists():
        content_text = content_path.read_text(encoding="utf-8")
        callouts = re.findall(r"\[![\w-]+\]", content_text)
        metrics["ENGAGEMENT_COUNT"] = str(len(callouts))
    else:
        metrics["ENGAGEMENT_COUNT"] = "0"

    # Immersion percent (estimate from Ukrainian/total character ratio)
    if content_path.exists():
        content_text = content_path.read_text(encoding="utf-8")
        # Count Cyrillic characters as Ukrainian
        cyrillic = len(re.findall(r"[\u0400-\u04FF]", content_text))
        latin = len(re.findall(r"[a-zA-Z]", content_text))
        total_alpha = cyrillic + latin
        if total_alpha > 0:
            metrics["IMMERSION_PERCENT"] = str(cyrillic * 100 // total_alpha)
        else:
            metrics["IMMERSION_PERCENT"] = "0"
    else:
        metrics["IMMERSION_PERCENT"] = "0"

    # Immersion target from immersion rule (extract percentage range)
    target_match = re.search(r"TARGET:\s*(\d+[-–]\d+%)", ctx.immersion_rule)
    if target_match:
        metrics["IMMERSION_TARGET"] = target_match.group(1)
    elif "100%" in ctx.immersion_rule or "Full" in ctx.immersion_rule:
        metrics["IMMERSION_TARGET"] = "98-100%"
    else:
        metrics["IMMERSION_TARGET"] = "see immersion rule"

    # Audit status — run quick content-only check
    if content_path.exists() and not ctx.dry_run:
        passed, _ = run_verify(content_path, content_only=True)
        metrics["AUDIT_STATUS"] = "PASS" if passed else "FAIL (content gates)"
    else:
        metrics["AUDIT_STATUS"] = "not yet audited"

    return metrics


def phase_6_review(ctx: ModuleContext) -> bool:
    """Phase 6: Green Team prose review (separate Gemini session)."""
    phase = "6"
    if is_phase_complete(ctx, phase):
        log("  Phase 6: SKIP (already complete)")
        return True

    template = PHASES_DIR / "phase-6-review.md"
    prompt_file = ctx.orch_dir / "phase-6-review-prompt.md"

    # Compute audit metrics for the review template
    overrides = _compute_audit_metrics(ctx)

    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file, overrides=overrides):
        return False

    if ctx.dry_run:
        log("  Phase 6: DRY-RUN — would dispatch prose review")
        return True

    for attempt in range(1, MAX_REVIEW_RETRIES + 1):
        task_id = f"gr-{ctx.slug}" if attempt == 1 else f"gr-{ctx.slug}-r{attempt}"
        log(f"  Phase 6: Dispatching prose review (attempt {attempt})...")
        output_file = _gemini_output_path(ctx.slug, f"6-r{attempt}")
        ok, _ = dispatch_gemini(
            f"Activate skill review-content-v4. Read and execute the instructions at "
            f"{PROJECT_ROOT}/{prompt_file.relative_to(PROJECT_ROOT)}",
            task_id=task_id,
            model=ctx.model, stdout_only=True, output_file=output_file,
        )
        if not ok:
            log(f"  Phase 6: Dispatch failed (attempt {attempt})")
            continue

        if not extract_phase_output(output_file, "6", ctx.orch_dir):
            log(f"  Phase 6: Extraction failed (attempt {attempt})")
            continue

        # Copy to canonical review path
        extracted = ctx.orch_dir / "phase-6-review.md"
        if extracted.exists():
            ctx.paths["review"].parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(extracted, ctx.paths["review"])

            # Anti-gaming check
            review_text = extracted.read_text(encoding="utf-8")
            if _is_rubber_stamp(review_text) and attempt < MAX_REVIEW_RETRIES:
                log(f"  Phase 6: Rubber-stamp detected — retrying with stronger prompt")
                continue

            log(f"  Phase 6: Review saved ({ctx.paths['review'].name})")
            mark_phase(ctx, phase, "complete", task_id=task_id, attempts=attempt)
            return True

    # Accept whatever we got after retries
    mark_phase(ctx, phase, "complete", task_id=f"gr-{ctx.slug}", note="accepted after retries")
    return True


def _is_rubber_stamp(review_text: str) -> bool:
    """Detect rubber-stamp reviews (gaming language, all 9+/10)."""
    gaming_phrases = [
        "ensuring a high score", "reflecting the fixes", "designed to pass",
        "reflects the improvements",
    ]
    for phrase in gaming_phrases:
        if phrase.lower() in review_text.lower():
            return True

    # Check for suspiciously high scores (all dimensions 9+ with no real issues)
    scores = re.findall(r"(\d+)/10", review_text)
    if len(scores) >= 3 and all(int(s) >= 9 for s in scores):
        # Check if there are substantive issues mentioned
        issue_words = ["issue", "problem", "error", "incorrect", "missing", "weak"]
        has_issues = any(w in review_text.lower() for w in issue_words)
        if not has_issues:
            return True

    return False


def _extract_delimited_content(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiter tags, handling code block wrapping."""
    # Strip code block markers Gemini sometimes wraps around delimiters
    cleaned = re.sub(r'```\w*\n', '', text)
    cleaned = re.sub(r'\n```', '', cleaned)
    pattern = re.compile(
        rf'{re.escape(start_tag)}\s*\n(.*?)\n\s*{re.escape(end_tag)}',
        re.DOTALL,
    )
    m = pattern.search(cleaned)
    return m.group(1).strip() if m else None


MAX_6B_ATTEMPTS = 5


def phase_6b_apply_fixes(ctx: ModuleContext) -> bool:
    """Phase 6b: Apply prose fixes from review using phase-fix-content.md template.

    Uses the structured template (not ad-hoc prompt), passes full review
    (no truncation), and runs a verify loop (max 3 attempts) to ensure
    prose quality gate passes before marking complete.
    """
    phase = "6b"
    if is_phase_complete(ctx, phase):
        log("  Phase 6b: SKIP (already complete)")
        return True

    review_path = ctx.paths["review"]
    if not review_path.exists():
        log("  Phase 6b: SKIP — no review file to apply")
        mark_phase(ctx, phase, "complete", note="no review file")
        return True

    if ctx.dry_run:
        log("  Phase 6b: DRY-RUN — would apply prose fixes via template")
        return True

    template = PHASES_DIR / "phase-fix-content.md"
    prompt_file = ctx.orch_dir / "phase-6b-prompt.md"

    # Build overrides for template placeholders
    overrides = {
        "REVIEW_PATH": str(ctx.paths["review"]),
        "CONTENT_PATH": str(ctx.paths["md"]),
        "PLAN_PATH": str(ctx.paths.get("plan", "")),
        "RESEARCH_PATH": str(ctx.paths.get("research", "")),
    }

    for attempt in range(1, MAX_6B_ATTEMPTS + 1):
        # Attempt 1: fix from review. Attempts 2+: keep previous fixes, target remaining violations.
        extra_overrides = dict(overrides)
        if attempt > 1:
            # Re-fill template with violation context appended
            violation_context = ctx.orch_dir / f"phase-6b-violations-{attempt}.md"
            if violation_context.exists():
                extra_section = violation_context.read_text(encoding="utf-8")
                # Write an augmented prompt with violation details
                if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file, overrides=extra_overrides):
                    log(f"  Phase 6b: Template fill failed (attempt {attempt})")
                    continue
                # Append violation details to the filled prompt
                current = prompt_file.read_text(encoding="utf-8")
                prompt_file.write_text(
                    current + "\n\n" + extra_section,
                    encoding="utf-8",
                )
            else:
                if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file, overrides=extra_overrides):
                    log(f"  Phase 6b: Template fill failed (attempt {attempt})")
                    continue
        else:
            if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file, overrides=extra_overrides):
                log("  Phase 6b: Template fill failed")
                return False

        task_id = f"yw-{ctx.slug}-6b" if attempt == 1 else f"yw-{ctx.slug}-6b-r{attempt}"
        log(f"  Phase 6b: Dispatching prose fixes (attempt {attempt}/{MAX_6B_ATTEMPTS})...")
        output_file = _gemini_output_path(ctx.slug, f"6b-a{attempt}")
        ok, raw_output = dispatch_gemini(
            _dispatch_prompt(ctx, prompt_file),
            task_id=task_id,
            model=ctx.model, allow_write=True, output_file=output_file,
        )

        if not ok:
            log(f"  Phase 6b: Dispatch failed (attempt {attempt})")
            continue

        # Extract fixed content from delimited output
        if output_file.exists():
            output_text = output_file.read_text(encoding="utf-8")
            fixed_content = _extract_delimited_content(
                output_text, "===CONTENT_START===", "===CONTENT_END===",
            )
            if fixed_content:
                ctx.paths["md"].write_text(fixed_content, encoding="utf-8")
                log(f"  Phase 6b: Fixed content written ({len(fixed_content)} chars)")
            else:
                # Gemini may have written directly to the file (allow_write=True)
                current_size = ctx.paths["md"].stat().st_size if ctx.paths["md"].exists() else 0
                log(f"  Phase 6b: No delimited content — checking if Gemini wrote directly ({current_size} bytes on disk)")

        # Run IPA lint as safety net
        run_script([str(SCRIPTS_DIR / "lint_ipa.py"), str(ctx.paths["md"]), "--fix"], capture=True)

        # Verify: run prose quality check directly (not full audit — that checks activities too)
        from audit.checks.prose_quality import check_prose_quality
        prose_content = ctx.paths["md"].read_text(encoding="utf-8")
        prose_violations = check_prose_quality(prose_content)
        critical_violations = [v for v in prose_violations if v["severity"] == "critical"]
        verify_output = "\n".join(
            f"[{v['severity']}] {v['type']}: {v['issue']}" for v in prose_violations
        ) or "No prose quality violations"
        verify_log = ctx.orch_dir / f"phase-6b-verify-{attempt}.log"
        verify_log.write_text(verify_output, encoding="utf-8")
        passed = len(critical_violations) == 0

        if passed:
            fixes = attempt - 1
            log(f"  Phase 6b: PASS{f' (after {fixes} retry/ies)' if fixes else ''}")
            mark_phase(ctx, phase, "complete", task_id=task_id, attempts=attempt)
            return True

        log(f"  Phase 6b: Verify FAILED (attempt {attempt})")

        if attempt < MAX_6B_ATTEMPTS:
            # Write violation details for next attempt
            violation_file = ctx.orch_dir / f"phase-6b-violations-{attempt + 1}.md"
            violation_file.write_text(textwrap.dedent(f"""\

                ## ADDITIONAL: Audit Violations Still Present (attempt {attempt} failed)

                The previous fix attempt did NOT resolve these audit violations.
                You MUST fix them this time. Focus specifically on these errors:

                ```
                {verify_output[-2000:]}
                ```

                **Priority fixes:**
                - Remove ALL `_Приклад(и):_` drill blocks from narrative prose — rewrite as flowing paragraphs
                - Remove ALL glossary-style `**word** —` definition lists from narrative — move to vocabulary YAML
                - Vary repetitive rhetorical patterns (не просто X, а Y)
                - Remove inline English translations from B1+ content
            """), encoding="utf-8")

    # Exhausted attempts — mark with note
    log(f"  Phase 6b: EXHAUSTED — {MAX_6B_ATTEMPTS} attempts, prose violations remaining")
    mark_phase(ctx, phase, "complete", task_id=f"yw-{ctx.slug}-6b",
               note="prose-violations-remaining", attempts=MAX_6B_ATTEMPTS)
    return True


def phase_7_final_review(ctx: ModuleContext) -> bool:
    """Phase 7: Final adversarial review."""
    phase = "7"
    if is_phase_complete(ctx, phase):
        log("  Phase 7: SKIP (already complete)")
        return True

    template = PHASES_DIR / "phase-7-final-review.md"
    prompt_file = ctx.orch_dir / "phase-7-prompt.md"

    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log("  Phase 7: DRY-RUN — would dispatch final review")
        return True

    log("  Phase 7: Dispatching final review...")
    output_file = _gemini_output_path(ctx.slug, "7")
    ok, _ = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"fr-{ctx.slug}",
        model=ctx.model, allow_write=True, output_file=output_file,
    )
    if not ok:
        log("  Phase 7: WARNING — dispatch failed")

    # Extract final review if present
    extract_phase_output(output_file, "7-final-review", ctx.orch_dir)

    mark_phase(ctx, phase, "complete", task_id=f"fr-{ctx.slug}")
    return True


# ---------------------------------------------------------------------------
# 6. Pipeline Runner
# ---------------------------------------------------------------------------

# Phase sequences by mode
PHASE_SEQUENCES = {
    "content-only": ["0", "0.5", "1", "2", "4", "6", "6b", "5"],
    "enrich":       ["3a", "3b", "4-full", "7", "5"],
    "full":         ["0", "0.5", "1", "2", "3a", "3b", "4-full", "6", "6b", "7", "5"],
}

# Map phase IDs to functions
PHASE_FUNCTIONS: dict[str, Any] = {
    "0":      lambda ctx: phase_0_research(ctx),
    "0.5":    lambda ctx: phase_0_5_enrich_plan(ctx),
    "1":      lambda ctx: phase_1_meta(ctx),
    "2":      lambda ctx: phase_2_content(ctx),
    "3a":     lambda ctx: phase_3a_activities(ctx),
    "3b":     lambda ctx: phase_3b_vocabulary(ctx),
    "4":      lambda ctx: phase_4_audit_fix(ctx, content_only=True),
    "4-full": lambda ctx: phase_4_audit_fix(ctx, content_only=False),
    "5":      lambda ctx: phase_5_mdx(ctx),
    "5-post": lambda ctx: phase_5_mdx(ctx),  # Post-enrich MDX regen
    "6":      lambda ctx: phase_6_review(ctx),
    "6b":     lambda ctx: phase_6b_apply_fixes(ctx),
    "7":      lambda ctx: phase_7_final_review(ctx),
}


def run_pipeline(ctx: ModuleContext) -> bool:
    """Execute the phase pipeline based on mode."""
    sequence = PHASE_SEQUENCES.get(ctx.mode, PHASE_SEQUENCES["full"])

    log(f"\nPipeline: {ctx.mode} mode — phases {', '.join(sequence)}")
    if ctx.dry_run:
        log("  (DRY-RUN — no Gemini dispatches)")
    log("")

    for phase_id in sequence:
        func = PHASE_FUNCTIONS.get(phase_id)
        if not func:
            log(f"  Unknown phase: {phase_id}")
            continue

        if not func(ctx):
            log(f"\n  PIPELINE STOPPED at phase {phase_id}")
            return False

    return True


def write_completion_report(ctx: ModuleContext, passed: bool) -> None:
    """Write completion report to orchestration dir."""
    content_path = ctx.paths["md"]
    word_count = 0
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())

    status = "CONTENT COMPLETE" if ctx.mode == "content-only" else "COMPLETE"
    verdict = "PASS" if passed else "FAIL"

    sections_info = ctx.state.get("phases", {}).get("2", {})
    sections_done = sections_info.get("sections_done", "?")
    sections_total = sections_info.get("sections_total", "?")

    report = textwrap.dedent(f"""\
        {"" if passed else ""}{"PASS" if passed else "FAIL"}: build_module.py {ctx.track} {ctx.module_num} — {status}

          Module:  {ctx.slug}
          Track:   {ctx.track}
          Mode:    {ctx.mode}
          Words:   {word_count} (target: {ctx.word_target})
          Sections: {sections_done}/{sections_total}
          Verdict: {verdict}
          Date:    {_now_iso()}

        {"  Next: run --enrich to add activities" if ctx.mode == "content-only" and passed else ""}
    """)

    completion_file = ctx.orch_dir / "completion.md"
    completion_file.write_text(report, encoding="utf-8")
    log(f"\nCompletion report → {completion_file}")


# ---------------------------------------------------------------------------
# 7. Preflight + Main
# ---------------------------------------------------------------------------

def preflight(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, compute config. Returns ModuleContext."""
    track = args.track
    num = args.num

    # Resolve slug
    slug = slug_for_num(track, num)
    log(f"Module: {track} #{num} → {slug}")

    # Determine mode
    if args.content_only:
        mode = "content-only"
    elif args.enrich:
        mode = "enrich"
    else:
        mode = "full"

    # Get paths
    paths = get_module_paths(track, slug)
    orch_dir = paths["orchestration"]

    # Create directories
    for d in [orch_dir, paths["md"].parent,
              paths["activities"].parent, paths["vocabulary"].parent,
              paths["review"].parent, paths["research"].parent,
              paths["status"].parent]:
        d.mkdir(parents=True, exist_ok=True)

    # Load plan
    plan_path = paths["plan"]
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan not found: {plan_path}")
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    # Load meta
    meta_path = paths["meta"]
    if not meta_path.exists():
        raise FileNotFoundError(f"Meta not found: {meta_path}")
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))

    # Compute config
    skill_name, skill_identity, persona_flavor = get_track_skill(track, num)
    immersion_rule = get_immersion_rule(track, num)
    level_constraints = get_level_constraints(track)
    activity_config = get_activity_config(track, num)
    track_config = get_track_config(track)

    # Word target: plan overrides config, config is fallback
    word_target = plan.get("word_target", 0)
    if not word_target:
        try:
            from audit.config import get_word_target as _get_wt
            word_target = _get_wt(track.upper().split("-")[0], num)
        except Exception:
            word_target = 0  # Audit will use its own config fallback
    topic_title = plan.get("title", slug.replace("-", " ").title())
    content_outline = meta.get("content_outline", [])

    ctx = ModuleContext(
        track=track, module_num=num, slug=slug, mode=mode,
        paths=paths, orch_dir=orch_dir,
        plan=plan, meta=meta,
        word_target=word_target, topic_title=topic_title,
        content_outline=content_outline,
        skill_name=skill_name, skill_identity=skill_identity,
        persona_flavor=persona_flavor,
        immersion_rule=immersion_rule, level_constraints=level_constraints,
        activity_config=activity_config,
        model=track_config.get("model", PRO_MODEL),
        track_config=track_config,
        dry_run=args.dry_run,
        force_phase=args.force_phase,
        rebuild=args.rebuild,
    )

    # Load or init state
    if args.rebuild:
        # Nuke state
        state_file = _state_file(ctx)
        if state_file.exists():
            state_file.unlink()
        ctx.state = load_state(ctx)
        log("State: RESET (--rebuild)")
    else:
        ctx.state = load_state(ctx)
        if ctx.state.get("phases"):
            completed = [p for p, v in ctx.state["phases"].items() if v.get("status") == "complete"]
            log(f"State: Loaded — phases complete: {', '.join(completed) or 'none'}")
        else:
            log("State: Fresh")

    return ctx


REVIEW_TIERS_DIR = PROJECT_ROOT / "claude_extensions" / "commands" / "review-tiers"

TIER_MAP: dict[str, str] = {
    "a1": "tier-1-beginner.md",
    "a2": "tier-1-beginner.md",
    "b1": "tier-2-core.md",
    "b2": "tier-2-core.md",
    "b2-pro": "tier-2-core.md",
    "b2-hist": "tier-3-seminar.md",
    "c1-bio": "tier-3-seminar.md",
    "c1-hist": "tier-3-seminar.md",
    "lit": "tier-3-seminar.md",
    "c1": "tier-4-advanced.md",
    "c1-pro": "tier-4-advanced.md",
    "c2": "tier-4-advanced.md",
}


def get_tier_guidance(track: str) -> str:
    """Read the appropriate review-tier guidance file for a track."""
    # Lit sub-genres map to "lit"
    key = "lit" if track.startswith("lit-") else track
    tier_file = TIER_MAP.get(key)
    if not tier_file:
        # Fallback: use base level
        base = track.split("-")[0]
        tier_file = TIER_MAP.get(base, "tier-2-core.md")
    path = REVIEW_TIERS_DIR / tier_file
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"(Tier guidance file not found: {tier_file})"


def write_placeholders(ctx: ModuleContext) -> None:
    """Write placeholders.yaml for template filling."""
    placeholders_path = ctx.orch_dir / "placeholders.yaml"

    # Skip if exists and not rebuilding
    if placeholders_path.exists() and not ctx.rebuild:
        log("Placeholders: Using existing")
        return

    level_label = get_level_label(ctx.track)
    quick_ref_path = ctx.track_config.get("quick_ref", "")

    placeholders = {
        "TRACK": ctx.track,
        "LEVEL": level_label,
        "SLUG": ctx.slug,
        "TOPIC_TITLE": ctx.topic_title,
        "MODULE_NUM": str(ctx.module_num),
        "PLAN_PATH": str(ctx.paths["plan"]),
        "META_PATH": str(ctx.paths["meta"]),
        "CONTENT_PATH": str(ctx.paths["md"]),
        "ACTIVITIES_PATH": str(ctx.paths["activities"]),
        "VOCAB_PATH": str(ctx.paths["vocabulary"]),
        "RESEARCH_PATH": str(ctx.paths["research"]),
        "REVIEW_PATH": str(ctx.paths["review"]),
        "QUICK_REF_PATH": str(quick_ref_path) if quick_ref_path else "",
        "SCHEMA_PATH": f"schemas/activities-{ctx.track}.schema.json",
        "WORD_TARGET": str(ctx.word_target),
        "SKILL_IDENTITY": ctx.skill_identity,
        "PERSONA_FLAVOR": ctx.persona_flavor,
        "PERSONA_VOICE": ctx.plan.get("persona", {}).get("voice", ""),
        "PERSONA_ROLE": ctx.plan.get("persona", {}).get("role", ""),
        "IMMERSION_RULE": ctx.immersion_rule,
        "LEVEL_CONSTRAINTS": ctx.level_constraints,
        "TIER_GUIDANCE": get_tier_guidance(ctx.track),
    }

    # Add activity config
    placeholders.update(ctx.activity_config)

    placeholders_path.write_text(
        yaml.dump(placeholders, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    log(f"Placeholders: Written ({len(placeholders)} keys)")


_log_fh = None


def _init_log(slug: str) -> None:
    """Open a log file in logs/ for this build run."""
    global _log_fh
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"build-{slug}-{ts}.log"
    _log_fh = open(log_path, "a", encoding="utf-8")  # noqa: SIM115
    _log_fh.write(f"=== build_module.py — {slug} — {ts} ===\n")
    print(f"Log: {log_path}", flush=True)


def log(msg: str) -> None:
    """Print to stdout and append to log file."""
    print(msg, flush=True)
    if _log_fh:
        _log_fh.write(msg + "\n")
        _log_fh.flush()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic Python Module Builder — orchestrates Gemini for curriculum generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s a1 12                  # Full pipeline (resume-aware)
              %(prog)s a1 12 --content-only   # Prose only (phases 0-6b)
              %(prog)s a1 12 --enrich         # Activities only (phases 3+7)
              %(prog)s a1 12 --verify         # Just run audit, print PASS/FAIL
              %(prog)s a1 12 --rebuild        # Nuke state, rebuild from Phase 0
              %(prog)s a1 12 --force-phase 2  # Re-run specific phase only
              %(prog)s a1 12 --dry-run        # Show plan without dispatching
        """),
    )
    parser.add_argument("track", help="Track identifier (a1, a2, b1, ..., c1-bio, b2-hist, lit, ...)")
    parser.add_argument("num", type=int, help="1-indexed module number within the track")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--content-only", action="store_true",
                            help="Prose only: phases 0-6b (no activities)")
    mode_group.add_argument("--enrich", action="store_true",
                            help="Activities only: phases 3, 4-full, 7 (requires existing content)")
    mode_group.add_argument("--verify", action="store_true",
                            help="Just run audit, print PASS/FAIL, exit")

    parser.add_argument("--rebuild", action="store_true",
                        help="Nuke state and rebuild from Phase 0")
    parser.add_argument("--force-phase", type=str, default=None,
                        help="Re-run a specific phase even if state says complete")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without dispatching to Gemini")

    args = parser.parse_args()

    # --verify mode: just run audit and exit
    if args.verify:
        try:
            slug = slug_for_num(args.track, args.num)
            paths = get_module_paths(args.track, slug)
            content_path = paths["md"]

            if not content_path.exists():
                log(f"FAIL: Content file not found: {content_path}")
                return 1

            # Try full verify first, fall back to content-only
            passed, output = run_verify(content_path, content_only=False)
            if not passed:
                # Try content-only
                passed_co, output_co = run_verify(content_path, content_only=True)
                if passed_co:
                    log(f"CONTENT-COMPLETE: {slug} (activities still needed)")
                    return 0
                else:
                    log(f"FAIL: {slug}")
                    # Print last 20 lines of output
                    for line in output_co.strip().split("\n")[-20:]:
                        log(f"  {line}")
                    return 1
            else:
                log(f"PASS: {slug} (fully complete)")
                return 0
        except Exception as e:
            log(f"ERROR: {e}")
            return 1

    # Main pipeline
    try:
        ctx = preflight(args)
        _init_log(ctx.slug)
        write_placeholders(ctx)

        ok = run_pipeline(ctx)
        write_completion_report(ctx, ok)

        if ok:
            # Run final verification
            if not ctx.dry_run:
                content_only = ctx.mode == "content-only"
                passed, output = run_verify(ctx.paths["md"], content_only=content_only)
                if passed:
                    log(f"\nVERDICT: PASS — {ctx.slug} {'content-complete' if content_only else 'fully complete'}")
                else:
                    log(f"\nVERDICT: FAIL — final verification failed")
                    for line in output.strip().split("\n")[-15:]:
                        log(f"  {line}")
                    return 1
            else:
                log(f"\nDRY-RUN COMPLETE — would build {ctx.slug} in {ctx.mode} mode")
            return 0
        else:
            log(f"\nPIPELINE FAILED — check logs in {ctx.orch_dir}")
            return 1

    except FileNotFoundError as e:
        log(f"ERROR: {e}")
        return 1
    except ValueError as e:
        log(f"ERROR: {e}")
        return 1
    except KeyboardInterrupt:
        log("\nInterrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
