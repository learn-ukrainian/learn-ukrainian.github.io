#!/usr/bin/env python3
"""Pipeline shared utilities — single source of truth for build pipeline functions.

Consolidates shared utilities from build_module.py (v1) and build_module_v2.py (v2)
into a clean library with no monkey-patching. Used by build_module_v3.py and external
scripts.

Key design decisions:
  - dispatch_gemini: includes rate-limit fallback (from v2)
  - dispatch_gemini_raw: original no-fallback version (for external scripts)
  - mark_phase: always uses FileLock (merged v1 base + v2 locking)
  - log: thread-safe by default (no string hacks)
  - No monkey-patching anywhere
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from batch_gemini_config import (
    CURRICULUM_DIR,
    FLASH_MODEL,
    PHASES_DIR,
    PRO_MODEL,
    PROJECT_ROOT,
    SEMINAR_TRACKS,
    PRO_TRACKS,
    get_module_index,
    get_module_paths,
    get_track_config,
    slug_for_num,
    CLAUDE_MODEL_FINAL_REVIEW,
)

# ============================================================================
# 1. Config Tables (data only, no logic)
# ============================================================================

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
    "hist":  ("full-rebuild-hist", "Professor of Ukrainian Arts (history)", "The Decolonial Lecturer"),
    "istoriohrafiia":  ("full-rebuild-istoriohrafiia", "Professor of Ukrainian Arts (historiography)", "The Source Critic"),
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
    "hist": {
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
    "istoriohrafiia": {
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


# ============================================================================
# 2. Resolver Functions
# ============================================================================

def get_track_skill(track: str, module_num: int) -> tuple[str, str, str]:
    """Return (skill_file, skill_identity, persona_flavor) for a track + module number."""
    if track == "b1":
        key = "b1-early" if module_num <= 5 else "b1-late"
        return TRACK_SKILLS[key]
    if track.startswith("lit-"):
        return TRACK_SKILLS["lit"]
    if track in TRACK_SKILLS:
        return TRACK_SKILLS[track]
    return TRACK_SKILLS["b2"]


def get_immersion_rule(track: str, module_num: int) -> str:
    """Compute immersion rule from track + module number."""
    base = track.split("-")[0] if track not in ("hist", "c1-bio", "istoriohrafiia", "b2-pro", "c1-pro") else track
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
    if track.startswith("lit-"):
        return ACTIVITY_CONFIGS["lit"]
    if track == "b1":
        return ACTIVITY_CONFIGS["b1-bridge" if module_num <= 5 else "b1-core"]
    if track == "c1":
        return ACTIVITY_CONFIGS["c1-core"]
    if track in ACTIVITY_CONFIGS:
        return ACTIVITY_CONFIGS[track]
    return ACTIVITY_CONFIGS["b2"]


def get_level_label(track: str) -> str:
    """Get human-readable level label (e.g., 'A1', 'C1-BIO')."""
    return track.upper().replace("-", "_").rstrip("_")


_TRACK_FOCUS_MAP: dict[str, tuple[str, str | None]] = {
    "hist": ("B2", "history"),
    "c1-bio": ("C1", "biography"),
    "istoriohrafiia": ("C1", "history"),
    "b2-pro": ("B2", "professional"),
    "c1-pro": ("C1", "professional"),
    "lit": ("C1", "literature"),
    "oes": ("C2", "seminar"),
    "ruth": ("C2", "seminar"),
}


def track_to_level_focus(track: str) -> tuple[str, str | None]:
    """Map track name to (level_code, module_focus) for config resolution."""
    if track.startswith("lit-"):
        return ("C1", "literature")
    if track in _TRACK_FOCUS_MAP:
        return _TRACK_FOCUS_MAP[track]
    return (track.upper().split("-")[0], None)


# ============================================================================
# 3. ModuleContext Dataclass
# ============================================================================

@dataclass
class ModuleContext:
    """All paths, config, state for a module build."""
    track: str
    module_num: int
    slug: str
    mode: str  # "full", "content-only", "enrich", "e2e", "v3"

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
    claude_review: bool = False


# ============================================================================
# 4. State Helpers
# ============================================================================

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ============================================================================
# 5. Thread-safe Locks (from v2)
# ============================================================================

_HAS_FILELOCK = False
try:
    from filelock import FileLock
    _HAS_FILELOCK = True
except ImportError:
    warnings.warn(
        "filelock not installed — parallel 4a+4b will run sequentially. "
        "Install with: pip install filelock",
        stacklevel=1,
    )
    class FileLock:  # type: ignore[no-redef]
        def __init__(self, path: str | Path):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a: Any):
            pass

_state_lock: FileLock | None = None
_log_lock = threading.Lock()


def _init_state_lock(ctx: ModuleContext) -> None:
    """Create a file-based lock for thread-safe state writes."""
    global _state_lock
    lock_path = ctx.orch_dir / "state.json.lock"
    _state_lock = FileLock(str(lock_path))


# ============================================================================
# 6. mark_phase — Merged v1 base + v2 FileLock (always locks)
# ============================================================================

def mark_phase(ctx: ModuleContext, phase: str, status: str, **extra: Any) -> None:
    """Update phase status in state and persist (thread-safe via FileLock)."""
    if ctx.dry_run:
        return
    lock = _state_lock or FileLock(str(ctx.orch_dir / "state.json.lock"))
    with lock:
        if "phases" not in ctx.state:
            ctx.state["phases"] = {}
        entry = {"status": status, "timestamp": _now_iso()}
        entry.update(extra)
        ctx.state["phases"][phase] = entry
        save_state(ctx)


# Backward-compat alias
mark_phase_locked = mark_phase


# ============================================================================
# 7. Logging (thread-safe, no string hacks)
# ============================================================================

_log_fh = None


def _init_log(slug: str) -> None:
    """Open a log file in logs/ for this build run."""
    global _log_fh
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"build-{slug}-{ts}.log"
    _log_fh = open(log_path, "a", encoding="utf-8")  # noqa: SIM115
    _log_fh.write(f"=== pipeline — {slug} — {ts} ===\n")
    print(f"Log: {log_path}", flush=True)


def log(msg: str) -> None:
    """Print to stdout and append to log file (thread-safe)."""
    with _log_lock:
        print(msg, flush=True)
        if _log_fh:
            _log_fh.write(msg + "\n")
            _log_fh.flush()


# ============================================================================
# 8. Phase Sequence + Artifact Cleanup
# ============================================================================

PHASE_SEQUENCE = [
    "0", "0.5", "1", "2", "3", "4ab", "6", "6b", "5", "7", "8",
]


def _phase_state_ids(phase_id: str) -> list[str]:
    """Map v2 phase IDs to state.json phase IDs."""
    if phase_id == "4ab":
        return ["3a", "3b"]
    if phase_id == "5":
        return ["5-enrich"]
    if phase_id == "7":
        return ["7-final"]
    return [phase_id]


PHASE_ARTIFACT_PATTERNS: dict[str, list[str]] = {
    "0":    ["phase-0-*"],
    "0.5":  ["phase-0-5-*"],
    "1":    ["phase-1-*"],
    "2":    ["phase-2-*"],
    "3":    ["phase3-*", "phase-3-*", "phase-3a-*", "phase-3b-*"],
    "4ab":  ["phase-4a-*", "phase-4b-*", "phase4a-*", "phase4b-*", "phase-4-*"],
    "6":    ["phase-6-*"],
    "6b":   ["phase-6b-*"],
    "5":    ["phase5-*", "phase-5-*"],
    "7":    ["phase7-*", "phase-7-*"],
    "8":    ["phase-8-*", "phase8-*"],
}


def _external_artifacts_for_phase(ctx: ModuleContext, phase_id: str) -> list[Path]:
    """Return paths to audit/review/status files produced by a phase."""
    slug = ctx.slug
    paths = ctx.paths
    result: list[Path] = []
    if phase_id in ("3", "5", "7"):
        audit_dir = paths["md"].parent / "audit"
        for ext in ["-audit.md", "-audit.log", "-grammar.yaml", "-quality.md"]:
            f = audit_dir / f"{slug}{ext}"
            if f.exists():
                result.append(f)
        status_f = paths["status"]
        if status_f.exists():
            result.append(status_f)
    if phase_id == "6":
        review_f = paths["review"]
        if review_f.exists():
            result.append(review_f)
    if phase_id == "8":
        completion = ctx.orch_dir / "completion.md"
        if completion.exists():
            result.append(completion)
        mdx_dir = PROJECT_ROOT / "docusaurus" / "docs" / ctx.track
        mdx_file = mdx_dir / f"{ctx.slug}.mdx"
        if mdx_file.exists():
            result.append(mdx_file)
    return result


def clean_phase_artifacts(ctx: ModuleContext, phase_id: str, forward: bool = False) -> int:
    """Delete orchestration artifacts for a phase (and all subsequent if forward=True)."""
    if forward:
        try:
            idx = PHASE_SEQUENCE.index(phase_id)
        except ValueError:
            idx = 0
        phases_to_clean = PHASE_SEQUENCE[idx:]
    else:
        phases_to_clean = [phase_id]

    deleted = 0
    orch_dir = ctx.orch_dir
    for pid in phases_to_clean:
        patterns = PHASE_ARTIFACT_PATTERNS.get(pid, [])
        for pattern in patterns:
            for f in orch_dir.glob(pattern):
                f.unlink()
                deleted += 1
        for f in _external_artifacts_for_phase(ctx, pid):
            f.unlink()
            deleted += 1
        if "phases" in ctx.state and pid in ctx.state["phases"]:
            del ctx.state["phases"][pid]
        for state_id in _phase_state_ids(pid):
            if "phases" in ctx.state and state_id in ctx.state["phases"]:
                del ctx.state["phases"][state_id]

    if deleted > 0:
        save_state(ctx)
    return deleted


# ============================================================================
# 9. Gemini Dispatch Helpers
# ============================================================================

VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
TMP_DIR = Path("/tmp")
MAX_FIX_ITERATIONS = 3


def run_script(args: list[str], capture: bool = False, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a script via .venv/bin/python with cwd=PROJECT_ROOT."""
    cmd = [VENV_PYTHON] + args
    return subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=capture,
        text=True, timeout=timeout,
    )


def _run_with_heartbeat(
    cmd: list[str], label: str, timeout: int = 1800,
    heartbeat_interval: int = 30, **kwargs,
) -> subprocess.CompletedProcess:
    """Run a subprocess with periodic heartbeat logging."""
    stop_event = threading.Event()
    t0 = time.time()

    def _heartbeat():
        while not stop_event.wait(heartbeat_interval):
            elapsed = int(time.time() - t0)
            m, s = divmod(elapsed, 60)
            print(f"    ⏳ {label} — {m}m {s:02d}s elapsed...", flush=True)

    thread = threading.Thread(target=_heartbeat, daemon=True)
    thread.start()
    try:
        result = subprocess.run(cmd, timeout=timeout, **kwargs)
        return result
    finally:
        stop_event.set()
        thread.join(timeout=2)


def dispatch_gemini_raw(
    prompt: str, task_id: str, model: str = PRO_MODEL,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
) -> tuple[bool, str]:
    """Dispatch a prompt to Gemini via ai_agent_bridge.py (no rate-limit fallback).

    Returns (success, raw_output_text).
    """
    args = [
        str(SCRIPTS_DIR / "ai_agent_bridge.py"), "ask-gemini",
        "-",  # read prompt from stdin
        "--task-id", task_id,
        "--model", model,
    ]
    if stdout_only:
        args.append("--stdout-only")
    if allow_write:
        args.append("--allow-write")
    try:
        result = _run_with_heartbeat(
            [VENV_PYTHON] + args,
            label=f"Gemini {task_id}",
            timeout=timeout,
            cwd=str(PROJECT_ROOT), capture_output=True, text=True,
            input=prompt,
        )
        output_text = result.stdout or ""
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(output_text, encoding="utf-8")
        return result.returncode == 0, output_text
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT: Gemini dispatch {task_id} exceeded {timeout}s")
        return False, ""


# Rate limit / auth failure signatures in Gemini CLI output
_RATE_LIMIT_PATTERNS = [
    "Error authenticating",
    "FatalAuthenti",
    "RESOURCE_EXHAUSTED",
    "rate limit",
    "quota exceeded",
    "429",
]


def _is_rate_limited(output: str) -> bool:
    """Check if dispatch failed due to rate limiting or auth exhaustion."""
    lower = output.lower()
    return any(p.lower() in lower for p in _RATE_LIMIT_PATTERNS)


def dispatch_gemini(
    prompt: str, task_id: str, model: str = PRO_MODEL,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
) -> tuple[bool, str]:
    """Dispatch a prompt to Gemini with stdout_only=True and flash→pro fallback.

    This is the default dispatch used by the pipeline. Always forces stdout_only=True.
    If the specified model is Flash and it fails due to rate limiting, retries with Pro.
    """
    ok, output = dispatch_gemini_raw(
        prompt, task_id, model=model,
        stdout_only=True,  # Always stdout-only in pipeline
        allow_write=allow_write, output_file=output_file, timeout=timeout,
    )
    # Fallback: if flash failed due to rate limit, retry with pro
    if not ok and model == FLASH_MODEL and _is_rate_limited(output):
        log("  [fallback] Flash rate-limited, retrying with pro model...")
        ok, output = dispatch_gemini_raw(
            prompt, task_id, model=PRO_MODEL,
            stdout_only=True, allow_write=allow_write,
            output_file=output_file, timeout=timeout,
        )
        if ok:
            log("  [fallback] Pro model succeeded")
    return ok, output


# ============================================================================
# 10. Template & Extraction Helpers
# ============================================================================

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


def _gemini_output_path(slug: str, phase: str) -> Path:
    return TMP_DIR / f"gemini-output-{slug}-phase-{phase}.txt"


def _dispatch_prompt(ctx: ModuleContext, prompt_file: Path) -> str:
    """Build the standard dispatch prompt string."""
    content = prompt_file.read_text("utf-8")
    return f"Activate skill {ctx.skill_name}.\n\n{content}"


def extract_phase_output(
    input_file: Path, phase_key: str, output_dir: Path, attempt: int = 1,
    tags: list[str] | None = None,
) -> bool:
    """Extract delimited content via extract_phase.py. Returns True if all tags found."""
    args = [
        str(SCRIPTS_DIR / "extract_phase.py"),
        str(input_file),
        "--output-dir", str(output_dir),
        "--attempt", str(attempt),
    ]
    if tags:
        args.extend(["--tags"] + tags)
        args.extend(["--phase", phase_key])
    else:
        args.extend(["--phase", phase_key])
    result = run_script(args, capture=True)
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            log(f"    {line}")
    return result.returncode == 0


def _extract_delimited_content(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiter tags, handling code block wrapping.

    Uses the LONGEST match when multiple delimiter pairs exist.
    """
    cleaned = re.sub(r'```\w*\n', '', text)
    cleaned = re.sub(r'\n```', '', cleaned)
    pattern = re.compile(
        rf'{re.escape(start_tag)}\s*\n(.*?)\n\s*{re.escape(end_tag)}',
        re.DOTALL,
    )
    matches = pattern.findall(cleaned)
    if not matches:
        return None
    best = max(matches, key=len)
    return best.strip()


# ============================================================================
# 11. Verify Helpers
# ============================================================================

def run_verify(content_path: Path, content_only: bool = True,
               skip_review: bool = False) -> tuple[bool, str]:
    """Run verification gate. Returns (passed, output)."""
    if skip_review:
        audit_script = str(PROJECT_ROOT / "scripts" / "audit_module.sh")
        result = subprocess.run(
            [audit_script, "--skip-review", str(content_path)],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, output

    script = "otaman_verify.py" if content_only else "hetman_verify.py"
    result = run_script([str(SCRIPTS_DIR / script), str(content_path)], capture=True, timeout=300)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output


def write_review_with_hash(review_path: Path, review_text: str,
                           content_path: Path) -> None:
    """Write review file with embedded content hash for staleness detection."""
    content_hash = hashlib.md5(content_path.read_bytes()).hexdigest()[:12]
    header = f"<!-- content-hash: {content_hash} -->\n"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(header + review_text, "utf-8")


# Prose-only verification (from v2) — ignores review + activity gates
_NON_PROSE_GATES = {"review", "activities", "density", "unique_types", "priority",
                    "engagement", "activity_quality"}
_ACTIVITY_PEDAGOGY_CODES = {
    "MISSING_ADVANCED_ACTIVITY",
    "MISSING_REQUIRED_ACTIVITY",
    "ACTIVITY_TYPE_MISMATCH",
}


def run_verify_prose_only(content_path: Path) -> tuple[bool, str]:
    """Run audit_module.sh --skip-activities and check only prose-relevant gates."""
    audit_script = str(PROJECT_ROOT / "scripts" / "audit_module.sh")
    result = subprocess.run(
        [audit_script, "--skip-activities", str(content_path)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300,
    )
    output = (result.stdout or "") + (result.stderr or "")

    track_dir = content_path.parent
    slug = content_path.stem
    bare_slug = slug.split("-", 1)[1] if slug[0].isdigit() and "-" in slug else slug
    status_file = track_dir / "status" / f"{bare_slug}.json"

    if not status_file.exists():
        return False, output + "\nNo status JSON produced by audit"

    status = json.loads(status_file.read_text(encoding="utf-8"))
    gates = status.get("gates", {})

    activity_ped_count = 0
    for code in _ACTIVITY_PEDAGOGY_CODES:
        activity_ped_count += output.count(f"[{code}]")

    failing = []
    for gate_name, gate_data in gates.items():
        if gate_name in _NON_PROSE_GATES:
            continue
        if gate_data.get("status") == "fail":
            msg = gate_data.get("message", "")
            if gate_name == "lesson" and "pedagogy" in msg:
                ped_match = re.search(r"pedagogy:\s*(\d+)\s*violation", msg)
                if ped_match:
                    total_ped = int(ped_match.group(1))
                    if activity_ped_count >= total_ped:
                        continue
                    real_ped = total_ped - activity_ped_count
                    msg = re.sub(r"pedagogy:\s*\d+\s*violations?",
                                 f"pedagogy: {real_ped} violations", msg)
            failing.append(f"{gate_name}: {msg}")

    if failing:
        return False, output + "\nProse-relevant failures:\n" + "\n".join(f"  {f}" for f in failing)
    return True, output


# ============================================================================
# 12. Fix Prompt Helpers
# ============================================================================

def _parse_section(section: Any) -> tuple[str, int]:
    """Parse a content_outline section entry. Returns (title, words)."""
    if isinstance(section, dict):
        title = section.get("section", section.get("title", "Untitled"))
        words = section.get("words", 0)
        return str(title), int(words)
    return str(section), 0


def _identify_affected_sections(audit_output: str, content_path: Path) -> list[str]:
    """Parse audit output to identify which H2 sections have issues."""
    if not content_path.exists():
        return []
    content = content_path.read_text(encoding="utf-8")
    h2_headers = re.findall(r"^## (.+)$", content, re.MULTILINE)
    if not h2_headers:
        return []

    affected = set()
    audit_lower = audit_output.lower()
    for header in h2_headers:
        if header.lower() in audit_lower:
            affected.add(header)

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

    if 1 <= len(affected) <= 2:
        return sorted(affected)
    return []


def _apply_section_fixes(content_path: Path, fix_output: str) -> None:
    """Apply section-level fixes from delimited Gemini output."""
    fixes = re.findall(
        r"===SECTION_FIX_START===\s*\n(.*?)===SECTION_FIX_END===",
        fix_output, re.DOTALL,
    )
    if not fixes:
        return
    content = content_path.read_text(encoding="utf-8")
    for fix_block in fixes:
        fix_block = fix_block.strip()
        h2_match = re.match(r"^## (.+)$", fix_block, re.MULTILINE)
        if not h2_match:
            continue
        section_title = h2_match.group(1).strip()
        pattern = re.compile(
            rf"(^## {re.escape(section_title)}\s*\n)"
            rf"(.*?)"
            rf"(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(content)
        if match:
            replacement = fix_block + "\n\n"
            content = content[:match.start()] + replacement + content[match.end():]
            log(f"    Applied section fix: {section_title}")
    content_path.write_text(content, encoding="utf-8")


def _build_schema_hint(ctx: ModuleContext, audit_output: str) -> str:
    """If audit output contains YAML_SCHEMA_VIOLATION, extract schema definitions."""
    if "YAML_SCHEMA_VIOLATION" not in audit_output:
        return ""
    failing_types = list(dict.fromkeys(
        m.group(1) for m in re.finditer(r"'type':\s*'([a-z_-]+)'", audit_output)
    ))
    if not failing_types:
        return ""
    track = ctx.track if hasattr(ctx, "track") else ""
    schemas_dir = Path(__file__).parent.parent / "schemas"
    schema_path = schemas_dir / f"activities-{track}.schema.json"
    if not schema_path.exists():
        level_code = track.split("-")[0] if "-" not in track else track
        schema_path = schemas_dir / f"activities-{level_code}.schema.json"
    if not schema_path.exists():
        schema_path = schemas_dir / "activities-base.schema.json"
    if not schema_path.exists():
        return ""
    try:
        schema = json.loads(schema_path.read_text("utf-8"))
        defs = schema.get("definitions", {})
        hints = []
        for failing_type in failing_types:
            type_def = defs.get(f"{failing_type}-{track}") or defs.get(failing_type)
            if not type_def:
                continue
            required = type_def.get("required", [])
            props = list(type_def.get("properties", {}).keys())
            additional = type_def.get("additionalProperties", True)
            no_extra = additional is False
            hints.append(
                f"### `{failing_type}` (from {schema_path.name})\n"
                f"**Required fields:** {', '.join(f'`{r}`' for r in required)}\n"
                f"**Allowed fields:** {', '.join(f'`{p}`' for p in props)}\n"
                f"**additionalProperties:** `{additional}`"
                f"{' — ANY unlisted field = schema violation' if no_extra else ''}\n"
            )
        if not hints:
            return ""
        return "\n\n## Schema Reference (fix activities to match these)\n\n" + "\n".join(hints)
    except Exception:
        return ""


def _build_fix_prompt(ctx: ModuleContext, audit_output: str, content_only: bool) -> str:
    """Build a fix prompt from audit output."""
    lines = audit_output.strip().split("\n")
    tail = lines[-60:]
    schema_lines = [ln for ln in lines if "YAML_SCHEMA_VIOLATION" in ln and ln not in tail]
    if schema_lines:
        tail = schema_lines + ["", "--- (tail of audit output) ---", ""] + tail
    error_excerpt = "\n".join(tail)
    fix_type = "content-only" if content_only else "full"
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
    schema_hint = _build_schema_hint(ctx, audit_output)
    return textwrap.dedent(f"""\
        # Fix Phase — {fix_type} audit failures

        The following audit errors must be fixed for module `{ctx.slug}`:

        ## Audit Output (last 60 lines)

        ```
        {error_excerpt}
        ```
        {schema_hint}

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


# ============================================================================
# 13. Claude CLI Helpers
# ============================================================================

def _claude_cli() -> str:
    """Return path to the claude CLI executable."""
    return shutil.which("claude") or "claude"


def _run_claude_headless(prompt: str, timeout: int = 300, model: str | None = None) -> tuple[bool, str]:
    """Call `claude -p <prompt>` headlessly and return (success, output)."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    cmd = [_claude_cli()]
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["-p", prompt, "--output-format", "text"])
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(PROJECT_ROOT), env=env,
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            log(f"  Claude CLI error (rc={result.returncode}): {err[:200]}")
            return False, ""
        return True, result.stdout.strip()
    except FileNotFoundError:
        log("  Claude CLI not found — install claude and ensure it is on PATH")
        return False, ""
    except Exception as e:
        log(f"  Claude CLI exception: {e}")
        return False, ""


def _apply_file_fixes(fix_response: str, ctx: ModuleContext) -> int:
    """Parse and apply OLD/NEW file fixes from Claude final review output."""
    blocks = re.findall(
        r"===FIX_START===\s*\n(.*?)===FIX_END===",
        fix_response, re.DOTALL,
    )
    applied = 0
    for block in blocks:
        file_match = re.search(r"^FILE:\s*(.+)$", block, re.MULTILINE)
        old_match = re.search(r"---OLD---\s*\n(.*?)---NEW---", block, re.DOTALL)
        new_match = re.search(r"---NEW---\s*\n(.*?)$", block, re.DOTALL)
        if not (file_match and old_match and new_match):
            log("    FIX: skipping malformed block")
            continue
        rel_path = file_match.group(1).strip()
        target = PROJECT_ROOT / rel_path
        if not target.exists():
            log(f"    FIX: file not found: {rel_path}")
            continue
        old_text = old_match.group(1).rstrip("\n")
        new_text = new_match.group(1).rstrip("\n")
        content = target.read_text(encoding="utf-8")
        if old_text not in content:
            log(f"    FIX: old text not found in {target.name} — skipping")
            continue
        content = content.replace(old_text, new_text, 1)
        target.write_text(content, encoding="utf-8")
        log(f"    FIX applied: {target.name}")
        applied += 1
    return applied


def dispatch_claude_final_review(ctx: ModuleContext) -> tuple[bool, str, str]:
    """Phase 9: Full final QA gate via headless Claude CLI.

    Returns (success, verdict, report_text).
    """
    def _read(path: Path | None) -> str:
        if path and path.exists():
            return path.read_text(encoding="utf-8")
        return "(file not found)"

    content_text   = _read(ctx.paths.get("md"))
    activities_text = _read(ctx.paths.get("activities"))
    vocab_text     = _read(ctx.paths.get("vocab"))
    plan_path = PROJECT_ROOT / f"curriculum/l2-uk-en/plans/{ctx.track}/{ctx.slug}.yaml"
    plan_text      = _read(plan_path)
    meta_text      = _read(ctx.paths.get("meta"))
    review_text    = _read(ctx.paths.get("review"))

    _, audit_output = run_verify(ctx.paths["md"], content_only=False)

    content_rel   = f"curriculum/l2-uk-en/{ctx.track}/{ctx.slug}.md"
    activities_rel = f"curriculum/l2-uk-en/{ctx.track}/activities/{ctx.slug}.yaml"
    vocab_rel     = f"curriculum/l2-uk-en/{ctx.track}/vocabulary/{ctx.slug}.yaml"

    system_prompt = (
        "You are the final adversarial QA gate for Ukrainian language curriculum modules. "
        "A Gemini pipeline built this module. Your job is to catch semantic errors, "
        "pedagogical traps, and LLM artifacts that automated audits cannot detect. "
        "Trust nothing — verify everything by reading the actual file contents. "
        "Apply fixes directly using the structured format. Be the adversary."
    )

    user_prompt = f"""# Phase 9: Final QA Review — {ctx.slug}

**Track:** {ctx.track} | **Module:** #{ctx.module_num}

---

## Files

### Content ({content_rel})
```markdown
{content_text}
```

### Activities ({activities_rel})
```yaml
{activities_text}
```

### Vocabulary ({vocab_rel})
```yaml
{vocab_text}
```

### Plan (source of truth)
```yaml
{plan_text}
```

### Meta
```yaml
{meta_text}
```

### Existing Review (Green Team)
```markdown
{review_text}
```

### Fresh Audit Output
```
{audit_output}
```

---

## Your Task

Perform a deep adversarial review. Check ALL of the following:

**Ukrainian Language Quality:**
- No Russianisms (кушати, получати, приймати участь, слідуючий)
- No Russian characters (ы, э, ё, ъ)
- Gender agreement, case agreement, verb aspect correct

**Pedagogical Correctness:**
- No vocabulary outside the plan's vocabulary_hints used in activities
- No grammar forms beyond this module's level (check plan.grammar_focus)
- No forward references to future modules presented as teachable content
- Unjumble activities: words array contains all words+punctuation in the answer
- Fill-in activities: answer produces a grammatical sentence when inserted

**Factual Accuracy:**
- Dates, names, translations correct
- Historical/cultural claims accurate and not contested

**LLM Artifacts:**
- Purple prose, grandiose openers
- "Це не просто X, а Y" overuse
- Folk etymology presented as fact
- False statistics or invented percentages

**Plan Compliance:**
- All content_outline sections present
- Required vocabulary used in prose
- Objectives map to self-check questions

---

## Output Format

First, list every issue you found (be specific — quote the exact text, state the file and line context, explain what's wrong and what the correct version should be).

Then output fixes using EXACTLY this format for each fix (no code fences around the blocks):

===FIX_START===
FILE: {content_rel}
---OLD---
exact text to replace (must exist verbatim in the file)
---NEW---
exact replacement text
===FIX_END===

You may use multiple FIX blocks. The FILE field must be one of:
- {content_rel}
- {activities_rel}
- {vocab_rel}

Finally, output your verdict:

===VERDICT===
APPROVE
===END_VERDICT===

Verdict guide:
- APPROVE: audit passes, no remaining issues after fixes
- NEEDS_WORK: fixed what you could, minor issues remain (still pass audit)
- REJECT: content is thin (<70% word target), unfixable Russianisms, broken activities, or factual errors in core claims

Do not rubber-stamp. A verdict of APPROVE on a module with real unfixed issues is a failure.
"""

    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    claude_model_f = getattr(ctx, "claude_model_F", None)
    log(f"  Phase 9 (Claude): Calling headless claude for final QA review{f' [{claude_model_f}]' if claude_model_f else ''}...")
    ok, report = _run_claude_headless(full_prompt, timeout=600, model=claude_model_f)
    if not ok:
        return False, "", ""
    log(f"  Phase 9 (Claude): Review complete ({len(report)} chars)")

    fixes_applied = _apply_file_fixes(report, ctx)
    if fixes_applied:
        log(f"  Phase 9 (Claude): Applied {fixes_applied} fix(es)")

    verdict_match = re.search(
        r"===VERDICT===\s*\n\s*(APPROVE|NEEDS_WORK|REJECT)\s*\n\s*===END_VERDICT===",
        report,
    )
    verdict = verdict_match.group(1) if verdict_match else "NEEDS_WORK"
    log(f"  Phase 9 (Claude): Verdict → {verdict}")
    return True, verdict, report


# ============================================================================
# 14. Review Tier Helpers
# ============================================================================

REVIEW_TIERS_DIR = PROJECT_ROOT / "claude_extensions" / "commands" / "review-tiers"

TIER_MAP: dict[str, str] = {
    "a1": "tier-1-beginner.md",
    "a2": "tier-1-beginner.md",
    "b1": "tier-2-core.md",
    "b2": "tier-2-core.md",
    "b2-pro": "tier-2-core.md",
    "hist": "tier-3-seminar.md",
    "c1-bio": "tier-3-seminar.md",
    "istoriohrafiia": "tier-3-seminar.md",
    "lit": "tier-3-seminar.md",
    "c1": "tier-4-advanced.md",
    "c1-pro": "tier-4-advanced.md",
    "c2": "tier-4-advanced.md",
}


def get_tier_guidance(track: str) -> str:
    """Read the appropriate review-tier guidance file for a track."""
    key = "lit" if track.startswith("lit-") else track
    tier_file = TIER_MAP.get(key)
    if not tier_file:
        base = track.split("-")[0]
        tier_file = TIER_MAP.get(base, "tier-2-core.md")
    path = REVIEW_TIERS_DIR / tier_file
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"(Tier guidance file not found: {tier_file})"


def _is_tier1(track: str) -> bool:
    key = "lit" if track.startswith("lit-") else track
    tier_file = TIER_MAP.get(key)
    if not tier_file:
        base = track.split("-")[0]
        tier_file = TIER_MAP.get(base, "tier-2-core.md")
    return tier_file == "tier-1-beginner.md"


def _get_scoring_section(track: str) -> str:
    """Return the STEP 4 scoring block with tier-appropriate dimensions."""
    if _is_tier1(track):
        return """### STEP 4: Score 7 Dimensions

| # | Dimension | Weight | Auto-fail |
|---|-----------|--------|-----------|
| 1 | Experience Quality | 1.5 | <7 |
| 2 | Language | 1.1 | <8 |
| 3 | Pedagogy | 1.2 | <7 |
| 4 | Activities | 1.3 | <7 |
| 5 | Beginner Safety | 1.3 | <7 |
| 6 | LLM Fingerprint | 1.0 | <7 |
| 7 | Linguistic Accuracy | 1.5 | <9 |

**Weighted Overall:**
```
Overall = (Experience x 1.5 + Language x 1.1 + Pedagogy x 1.2 +
          Activities x 1.3 + Beginner_Safety x 1.3 + LLM x 1.0 +
          Linguistic_Accuracy x 1.5) / 8.9
```

**Why 7 dimensions?** A1/A2 modules are short and topic-constrained, so Coherence, Relevance, Educational, Immersion, Richness, and Factual Accuracy are noise at this level — they auto-pass trivially and waste reviewer attention. Focus scoring on what actually differentiates good beginner modules."""
    else:
        return """### STEP 4: Score 13 Dimensions

| # | Dimension | Auto-fail |
|---|-----------|-----------|
| 1 | Experience Quality | <7 |
| 2 | Coherence | <7 |
| 3 | Relevance | <7 |
| 4 | Educational | <7 |
| 5 | Language | <8 |
| 6 | Pedagogy | <7 |
| 7 | Immersion | <6 |
| 8 | Activities | <7 |
| 9 | Richness | <6 |
| 10 | Beginner Safety | <7 |
| 11 | LLM Fingerprint | <7 |
| 12 | Linguistic Accuracy | <9 |
| 13 | Factual Accuracy | <8 |

**Weighted Overall:**
```
Overall = (Experience x 1.5 + Coherence x 1.0 + Relevance x 1.0 + Educational x 1.2 +
          Language x 1.1 + Pedagogy x 1.2 + Immersion x 1.0 + Activities x 1.3 +
          Richness x 0.9 + Beginner_Safety x 1.3 + LLM x 1.0 + Linguistic_Accuracy x 1.5 +
          Factual_Accuracy x 1.5) / 15.5
```

**Factual Accuracy note:** ALL tracks — verify callout boxes (`[!did-you-know]`, `[!myth-buster]`, `[!culture-note]`, `[!fun-fact]`) for fabricated claims. Seminar tracks — additionally verify against research notes/Key Facts Ledger. Do NOT auto-score 9 for any track."""


def _get_scoring_output_table(track: str) -> str:
    if _is_tier1(track):
        return """| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | X/10 | <7 | [specific finding] |
| 2 | Language | X/10 | <8 | [specific finding] |
| 3 | Pedagogy | X/10 | <7 | [specific finding] |
| 4 | Activities | X/10 | <7 | [specific finding] |
| 5 | Beginner Safety | X/10 | <7 | ["Would I Continue?" X/5] |
| 6 | LLM Fingerprint | X/10 | <7 | [specific finding] |
| 7 | Linguistic Accuracy | X/10 | <9 | [specific finding] |"""
    else:
        return """| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | X/10 | <7 | [specific finding] |
| 2 | Coherence | X/10 | <7 | [specific finding] |
| 3 | Relevance | X/10 | <7 | [specific finding] |
| 4 | Educational | X/10 | <7 | [specific finding] |
| 5 | Language | X/10 | <8 | [specific finding] |
| 6 | Pedagogy | X/10 | <7 | [specific finding] |
| 7 | Immersion | X/10 | <6 | [actual % vs target] |
| 8 | Activities | X/10 | <7 | [specific finding] |
| 9 | Richness | X/10 | <6 | [specific finding] |
| 10 | Beginner Safety | X/10 | <7 | ["Would I Continue?" X/5] |
| 11 | LLM Fingerprint | X/10 | <7 | [specific finding] |
| 12 | Linguistic Accuracy | X/10 | <9 | [specific finding] |
| 13 | Factual Accuracy | X/10 | <8 | [specific finding or "N/A — core track"] |"""


def _read_phase_file(filename: str) -> str:
    path = PHASES_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"(Phase file not found: {filename})"


# ============================================================================
# 15. Write Placeholders
# ============================================================================

def write_placeholders(ctx: ModuleContext) -> None:
    """Write placeholders.yaml for template filling."""
    placeholders_path = ctx.orch_dir / "placeholders.yaml"
    if placeholders_path.exists() and not ctx.rebuild and not getattr(ctx, "force_phase", False):
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
        "D1_OUTPUT_FORMAT": _read_phase_file("phase-D1-output-format.md"),
        "SCORING_SECTION": _get_scoring_section(ctx.track),
        "SCORING_OUTPUT_TABLE": _get_scoring_output_table(ctx.track),
    }
    placeholders.update(ctx.activity_config)
    placeholders_path.write_text(
        yaml.dump(placeholders, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    log(f"Placeholders: Written ({len(placeholders)} keys)")


# ============================================================================
# 16. Archive Helpers (from v2)
# ============================================================================

ARCHIVE_DIR = PROJECT_ROOT / "_archive"
ARCHIVE_WORD_THRESHOLD = 2000
ARCHIVE_GIT_REF = os.environ.get("ARCHIVE_GIT_REF", "944f3524a^")
ARCHIVE_SKIP_TRACKS: set[str] = {"c1-bio", "istoriohrafiia", "lit"}


def detect_archived_prose(track: str, slug: str) -> tuple[bool, str, Path | None]:
    """Check for restorable archived prose."""
    if track in ARCHIVE_SKIP_TRACKS:
        return False, "", None
    track_archive = ARCHIVE_DIR / track
    if track_archive.is_dir():
        ts_dirs = sorted(
            [d for d in track_archive.iterdir() if d.is_dir() and not d.name.startswith("_")],
            reverse=True,
        )
        for ts_dir in ts_dirs:
            md_path = ts_dir / f"{slug}.md"
            if md_path.exists():
                word_count = len(md_path.read_text(encoding="utf-8").split())
                if word_count >= ARCHIVE_WORD_THRESHOLD:
                    return True, f"filesystem: {ts_dir.name} ({word_count}w)", ts_dir
                log(f"  Archive: found {md_path.name} but only {word_count}w (need {ARCHIVE_WORD_THRESHOLD})")
    if not track_archive.is_dir():
        try:
            git_path = f"curriculum/l2-uk-en/{track}/{slug}.md"
            result = subprocess.run(
                ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(PROJECT_ROOT),
            )
            if result.returncode == 0 and result.stdout:
                word_count = len(result.stdout.split())
                if word_count >= ARCHIVE_WORD_THRESHOLD:
                    return True, f"git:{ARCHIVE_GIT_REF} ({word_count}w)", None
        except (subprocess.TimeoutExpired, OSError):
            pass
    return False, "", None


def restore_from_archive(ctx: ModuleContext, archive_dir: Path | None) -> bool:
    """Restore archived prose (and optionally activities/vocab) to live paths."""
    slug = ctx.slug
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_dir is not None:
        src_md = archive_dir / f"{slug}.md"
        if not src_md.exists():
            log(f"  Restore: {src_md} not found")
            return False
        shutil.copy2(src_md, content_path)
        log(f"  Restore: prose {src_md.name} → {content_path.name}")
    else:
        git_path = f"curriculum/l2-uk-en/{ctx.track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0 or not result.stdout:
            log("  Restore: git extraction failed")
            return False
        content_path.write_text(result.stdout, encoding="utf-8")
        log(f"  Restore: git:{ARCHIVE_GIT_REF}:{git_path} → {content_path.name}")
    if not content_path.exists():
        return False
    word_count = len(content_path.read_text(encoding="utf-8").split())
    if word_count < ARCHIVE_WORD_THRESHOLD:
        log(f"  Restore: REJECTED — only {word_count}w (need {ARCHIVE_WORD_THRESHOLD})")
        content_path.unlink()
        return False
    for sub, dest_key in [("activities", "activities"), ("vocabulary", "vocabulary")]:
        if archive_dir is not None:
            src = archive_dir / sub / f"{slug}.yaml"
            if src.exists():
                ctx.paths[dest_key].parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, ctx.paths[dest_key])
                log(f"  Restore: {sub}/{slug}.yaml")
        else:
            git_sub = f"curriculum/l2-uk-en/{ctx.track}/{sub}/{slug}.yaml"
            r = subprocess.run(
                ["git", "show", f"{ARCHIVE_GIT_REF}:{git_sub}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(PROJECT_ROOT),
            )
            if r.returncode == 0 and r.stdout.strip():
                ctx.paths[dest_key].parent.mkdir(parents=True, exist_ok=True)
                ctx.paths[dest_key].write_text(r.stdout, encoding="utf-8")
                log(f"  Restore: git {sub}/{slug}.yaml")
    pct = word_count * 100 // max(ctx.word_target, 1)
    log(f"  Restore: {word_count} words ({pct}% of {ctx.word_target} target)")
    return True


def _check_archive_fits_outline(ctx: ModuleContext) -> tuple[bool, list[str], list[str]]:
    """Check if archived prose covers the sections from the current content_outline."""
    archive_dir = getattr(ctx, "archive_dir", None)
    slug = ctx.slug
    if archive_dir is not None:
        src = archive_dir / f"{slug}.md"
        if not src.exists():
            return False, [], []
        content = src.read_text(encoding="utf-8")
    else:
        git_path = f"curriculum/l2-uk-en/{ctx.track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            return False, [], []
        content = result.stdout
    archive_h2s = {h.strip().lower() for h in re.findall(r"^## (.+)$", content, re.MULTILINE)}
    outline = ctx.content_outline
    if not outline:
        word_count = len(content.split())
        return word_count >= ARCHIVE_WORD_THRESHOLD, [], []
    matched = []
    missing = []
    for section in outline:
        title, _ = _parse_section(section)
        if title.strip().lower() in archive_h2s:
            matched.append(title)
        else:
            missing.append(title)
    total = len(outline)
    coverage = len(matched) / total if total > 0 else 0
    return coverage >= 0.7, matched, missing


# ============================================================================
# 17. Phase 2 Content Generation (from v1, used as fallback by Phase B)
# ============================================================================

def _build_section_budget_table(sections: list, word_target: int) -> str:
    """Build a markdown table of section word budgets."""
    rows = ["| Section | Target | Write Minimum (1.5x) |", "|---------|--------|---------------------|"]
    for section in sections:
        title, words = _parse_section(section)
        if words <= 0:
            words = word_target // max(len(sections), 1)
        rows.append(f"| {title} | {words} | {int(words * 1.5)} |")
    rows.append(f"| **Total** | **{word_target}** | **{int(word_target * 1.5)}** |")
    return "\n".join(rows)


def _build_phase2_expansion_prompt(
    ctx: ModuleContext, current_text: str, current_words: int,
    deficit: int, had_truncation: bool = False,
) -> str:
    """Build a prompt telling Gemini to expand thin content to meet word target."""
    sections: list[tuple[str, int]] = []
    current_section = ""
    section_text: list[str] = []
    for line in current_text.split("\n"):
        h2_match = re.match(r'^##\s+(.+)', line)
        if h2_match:
            if current_section and section_text:
                wc = len(" ".join(section_text).split())
                sections.append((current_section, wc))
            current_section = h2_match.group(1)
            section_text = []
        else:
            section_text.append(line)
    if current_section and section_text:
        wc = len(" ".join(section_text).split())
        sections.append((current_section, wc))
    section_report = "\n".join(f"- **{name}**: {wc} words" for name, wc in sections)
    research_path = ctx.paths.get("research", "")
    overshoot = ctx.word_target if had_truncation else int(ctx.word_target * 1.5)
    return f"""# Phase 2: EXPAND — Content is {current_words} words, need {ctx.word_target}+

> **Persona reminder:** You are {ctx.skill_identity}. Write in the voice of {ctx.persona_flavor}. Maintain your voice throughout.

## Problem

Your previous output was **{current_words} words** — far below the **{ctx.word_target} word minimum**.
You need to add approximately **{deficit} more words** of substantive content.

### Current section word counts:
{section_report}

## Your Task

Read the current content file at `{ctx.paths["md"]}` and the original prompt at `{ctx.orch_dir / "phase-2-prompt.md"}`.

**Rewrite the ENTIRE module** with dramatically expanded content. Every H3 subsection needs:
- 80-100+ words minimum (many of yours currently have 20-40)
- 2+ full example sentences in context
- Explanatory prose, not just headings and bullet points
- Callout boxes, comparison tables, cultural connections

**DO NOT just add filler.** Each section needs real depth:
- Historical examples with dates and specifics
- Primary source quotes (from research file)
- Detailed explanations of concepts
- Cultural context and connections

## Critical Rules
- Write at least **{overshoot} words** (1.5x target)
- Use research file: `{research_path}`
- Immersion: {ctx.immersion_rule}
- Output between `===CONTENT_START===` and `===CONTENT_END===` delimiters

## Output Format

===CONTENT_START===
{{entire rewritten module with dramatically expanded content}}
===CONTENT_END===

===WORD_COUNTS===
Section "{{name}}": {{count}} words
...
Total: {{total}} words
===WORD_COUNTS===
"""


def _prefetch_sources_for_phase_B(ctx: ModuleContext) -> str:
    """Pre-fetch primary source excerpts from RAG for Phase B content generation.

    For seminar tracks: extracts section names + key terms from plan/meta,
    searches literary RAG, returns formatted excerpts Gemini can cite.
    """
    track_key = "lit" if ctx.track.startswith("lit-") else ctx.track
    if track_key not in SEMINAR_TRACKS:
        return ""

    # Extract search terms from content_outline section names + topic title
    search_terms = []
    topic = ctx.meta.get("topic_title", ctx.slug.replace("-", " "))
    search_terms.append(topic)
    for section in ctx.content_outline:
        section_name = section.get("section", "")
        if section_name:
            search_terms.append(section_name)
    # Add vocabulary hints as search terms
    vocab_hints = ctx.plan.get("vocabulary_hints", {})
    for term in vocab_hints.get("required", [])[:3]:
        search_terms.append(term)
    # Cap at 5 searches
    search_terms = [t for t in search_terms if t.strip()][:5]
    if not search_terms:
        return ""

    try:
        from rag.query import search_literary
    except ImportError:
        return ""

    results = []
    seen_chunks = set()
    for term in search_terms:
        try:
            hits = search_literary(term, limit=2)
        except Exception:
            continue
        for hit in hits:
            cid = hit.get("chunk_id", "")
            if cid in seen_chunks:
                continue
            seen_chunks.add(cid)
            work = hit.get("work", "unknown")
            year = hit.get("year", "?")
            genre = hit.get("genre", "")
            text = hit.get("text", "")[:300]
            results.append(
                f"**{work}** ({year}, {genre}):\n> {text}"
            )

    if not results:
        return ""

    return "\n\n".join(results[:8])  # Cap at 8 excerpts


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

    word_target_tokens = ctx.word_target * 2 // 1000
    primary_sources = _prefetch_sources_for_phase_B(ctx)
    overrides = {
        "OVERSHOOT_TARGET": str(overshoot),
        "ENGAGEMENT_MIN": str(engagement_min),
        "EXAMPLE_MIN": str(example_min),
        "SECTION_BUDGET_TABLE": _build_section_budget_table(sections, ctx.word_target),
        "WORD_TARGET_TOKENS": str(word_target_tokens),
        "PRIMARY_SOURCE_EXCERPTS": primary_sources or "(No primary source excerpts available from RAG)",
    }
    if not fill_template(template, placeholders_yaml, prompt_file, overrides=overrides):
        return False

    if ctx.dry_run:
        log("  Phase 2: DRY-RUN — would dispatch whole-module content generation")
        return True

    MAX_P2_ATTEMPTS = 3
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)
    last_friction = None

    for attempt in range(1, MAX_P2_ATTEMPTS + 1):
        attempt_suffix = "" if attempt == 1 else f"-r{attempt}"
        task_suffix = "" if attempt == 1 else f"-r{attempt}"

        if attempt > 1 and content_path.exists():
            current_text = content_path.read_text(encoding="utf-8")
            current_words = len(current_text.split())
            deficit = ctx.word_target - current_words
            had_truncation = last_friction and "TOKEN_LIMIT_TRUNCATION" in last_friction
            if had_truncation:
                log(f"  Phase 2: Adjusting expansion target to {ctx.word_target}w (1.0x) due to previous truncation")
            expand_prompt = _build_phase2_expansion_prompt(
                ctx, current_text, current_words, deficit, had_truncation
            )
            expand_prompt_file = ctx.orch_dir / f"phase-2-expand-{attempt}.md"
            expand_prompt_file.write_text(expand_prompt, encoding="utf-8")
            dispatch_file = expand_prompt_file
            log(f"  Phase 2: Retry {attempt}/{MAX_P2_ATTEMPTS} — expanding {current_words}w → {ctx.word_target}w target")
        else:
            dispatch_file = prompt_file

        output_file = _gemini_output_path(ctx.slug, f"2{attempt_suffix}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, dispatch_file),
            task_id=f"yw-{ctx.slug}-p2{task_suffix}",
            model=ctx.model, stdout_only=True, output_file=output_file,
        )
        if not ok:
            log(f"  Phase 2: Dispatch failed (attempt {attempt})")
            continue

        content_text = None
        if output_file.exists():
            raw = output_file.read_text(encoding="utf-8")
            content_text = _extract_delimited_content(raw, "===CONTENT_START===", "===CONTENT_END===")
            friction = _extract_delimited_content(raw, "===FRICTION_START===", "===FRICTION_END===")
            if friction:
                friction_file = ctx.orch_dir / f"phase-2-friction-{attempt}.md"
                friction_file.write_text(friction, encoding="utf-8")
                log(f"  Phase 2: Friction report saved → {friction_file.name}")
                is_real_truncation = (
                    "TOKEN_LIMIT_TRUNCATION" in friction
                    and "YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION" not in friction
                )
                if is_real_truncation:
                    log("  Phase 2: ⚠ Gemini reported token limit truncation")
                last_friction = friction if is_real_truncation else last_friction

        if not content_text:
            log(f"  Phase 2: No delimited content extracted (attempt {attempt})")
            continue

        content_path.write_text(content_text, encoding="utf-8")
        total_words = len(content_text.split())
        pct = total_words * 100 // max(ctx.word_target, 1)
        log(f"  Phase 2: {total_words} words written ({pct}% of {ctx.word_target} target)")

        if total_words >= ctx.word_target * 0.75:
            mark_phase(ctx, phase, "complete", words=total_words, attempts=attempt)
            return True
        log(f"  Phase 2: Too thin — {total_words}w vs {ctx.word_target}w target (attempt {attempt})")

    log(f"  Phase 2: FAIL — exhausted {MAX_P2_ATTEMPTS} attempts, content still under 50% of target")
    return False


# ============================================================================
# 18. Phase B Content (from v2, renamed from phase_2_v2)
# ============================================================================

def phase_B_content(ctx: ModuleContext) -> bool:
    """Phase B: Write Prose. Checks archived prose against plan+research outline.

    Archive is used only if it covers >=70% of the content_outline sections.
    Falls back to phase_2_content if archive doesn't fit.
    """
    phase = "2"
    if getattr(ctx, "refresh", False) and is_phase_complete(ctx, phase):
        state_phases = ctx.state.get("phases", {})
        downstream = [k for k in state_phases if k >= "2"]
        for k in downstream:
            del state_phases[k]
        save_state(ctx)
        log(f"  Phase 2: RESET (--refresh flag, cleared {len(downstream)} phases)")
    elif is_phase_complete(ctx, phase):
        log("  Phase 2: SKIP (already complete)")
        return True

    content_path = ctx.paths["md"]
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())
        if word_count >= ctx.word_target * 0.8:
            refresh_needed = False
            research_path = ctx.paths.get("research")
            if research_path and research_path.exists():
                try:
                    from research_quality import assess_research_compat
                    info = assess_research_compat(research_path, ctx.track, content_path)
                    if info and info.get("content_alignment", {}).get("refresh_recommended"):
                        refresh_needed = True
                        reasons = info["content_alignment"].get("reasons", [])
                        log("  Phase 2: Research-content misalignment detected")
                        for r in reasons:
                            log(f"    - {r}")
                except ImportError:
                    pass
            if refresh_needed and getattr(ctx, "refresh", False):
                log("  Phase 2: --refresh flag set — regenerating prose from research")
            elif refresh_needed:
                log("  Phase 2: ADOPT (use --refresh to regenerate from updated research)")
                mark_phase(ctx, phase, "complete", note="adopted-stale-prose", words=word_count)
                return True
            else:
                log(f"  Phase 2: ADOPT — existing prose found ({word_count}w, target {ctx.word_target}w)")
                mark_phase(ctx, phase, "complete", note="adopted-existing-prose", words=word_count)
                return True

    if getattr(ctx, "is_archived", False):
        fits, matched, missing = _check_archive_fits_outline(ctx)
        archive_source = getattr(ctx, "archive_source", "unknown")
        if fits:
            log(f"  Phase 2: Archive fits outline — {len(matched)}/{len(matched)+len(missing)} sections match")
            if missing:
                log(f"  Phase 2: Missing sections (will be caught in Phase 3): {', '.join(missing)}")
            if ctx.dry_run:
                log(f"  Phase 2: DRY-RUN — would restore from archive ({archive_source})")
                return True
            archive_dir = getattr(ctx, "archive_dir", None)
            if restore_from_archive(ctx, archive_dir):
                mark_phase(ctx, phase, "complete", note="restored-from-archive",
                           source=archive_source,
                           sections_matched=len(matched),
                           sections_missing=len(missing))
                return True
            else:
                log("  Phase 2: Archive restore FAILED — falling back to generation")
        else:
            log(f"  Phase 2: Archive does NOT fit outline — only {len(matched)}/{len(matched)+len(missing)} sections match")
            log("  Phase 2: Generating fresh prose instead")

    if ctx.dry_run and not ctx.content_outline:
        log("  Phase 2: DRY-RUN — would generate prose (outline depends on Phase 1)")
        return True

    return phase_2_content(ctx)


# ============================================================================
# 19. Phase E (MDX) + Phase F (Final Review) Delegates
# ============================================================================

def phase_8_mdx(ctx: ModuleContext) -> bool:
    """Phase 8/E: MDX generation + lint. Deterministic, no LLM."""
    phase = "8"
    if is_phase_complete(ctx, phase):
        log("  Phase 8: SKIP (already complete)")
        return True
    if ctx.dry_run:
        log("  Phase 8: DRY-RUN — would generate MDX")
        return True
    log("  Phase 8: Generating MDX...")
    result = run_script([
        str(SCRIPTS_DIR / "generate_mdx.py"), "l2-uk-en", ctx.track, str(ctx.module_num),
    ], capture=True)
    if result.returncode != 0:
        log(f"  Phase 8: WARNING — MDX generation returned {result.returncode}")
    mark_phase(ctx, phase, "complete")
    return True


def phase_9_final_review(ctx: ModuleContext) -> bool:
    """Phase 9/F: Final adversarial QA gate via Claude API."""
    if not getattr(ctx, "final_review", False):
        return True
    phase = "9-final-review"
    if is_phase_complete(ctx, phase):
        log("  Phase 9: SKIP (already complete)")
        return True
    if ctx.dry_run:
        log("  Phase 9: DRY-RUN — would call Claude API for final review")
        return True

    ok, verdict, report = dispatch_claude_final_review(ctx)
    if not ok:
        log("  Phase 9: FAILED — Claude CLI unavailable")
        return False

    final_review_path = ctx.paths["review"].parent / f"{ctx.slug}-final-review.md"
    write_review_with_hash(final_review_path, report, ctx.paths["md"])
    log(f"  Phase 9: Report saved → {final_review_path.name}")
    orch_report = ctx.orch_dir / "phase-9-final-review.md"
    orch_report.write_text(report, encoding="utf-8")

    if "===FIX_START===" in report:
        passed, audit_out = run_verify(ctx.paths["md"], content_only=False)
        audit_log = ctx.orch_dir / "phase9-post-fix-audit.log"
        audit_log.write_text(audit_out, encoding="utf-8")
        if not passed:
            log(f"  Phase 9: Post-fix audit FAILED (verdict: {verdict})")
            if verdict == "REJECT":
                mark_phase(ctx, phase, "failed", verdict=verdict)
                return False
            log("  Phase 9: Audit failed but verdict is not REJECT — marking NEEDS_WORK")
        else:
            log("  Phase 9: Post-fix audit PASS")

    if verdict == "REJECT":
        log("  Phase 9: REJECT — module needs rebuild")
        mark_phase(ctx, phase, "failed", verdict=verdict)
        return False

    mark_phase(ctx, phase, "complete", verdict=verdict)
    return True


# ============================================================================
# 20. Preflight (from v1 + v2)
# ============================================================================

def preflight(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, compute config. Returns ModuleContext."""
    track = args.track
    num = args.num
    slug = slug_for_num(track, num)
    log(f"Module: {track} #{num} → {slug}")

    if getattr(args, "content_only", False):
        mode = "content-only"
    elif getattr(args, "enrich", False):
        mode = "enrich"
    else:
        mode = "full"

    paths = get_module_paths(track, slug)
    orch_dir = paths["orchestration"]
    for d in [orch_dir, paths["md"].parent,
              paths["activities"].parent, paths["vocabulary"].parent,
              paths["review"].parent, paths["research"].parent,
              paths["status"].parent]:
        d.mkdir(parents=True, exist_ok=True)

    plan_path = paths["plan"]
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan not found: {plan_path}")
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    meta_path = paths["meta"]
    if not meta_path.exists():
        raise FileNotFoundError(f"Meta not found: {meta_path}")
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))

    skill_name, skill_identity, persona_flavor = get_track_skill(track, num)
    immersion_rule = get_immersion_rule(track, num)
    level_constraints = get_level_constraints(track)
    activity_config = get_activity_config(track, num)
    track_config = get_track_config(track)

    word_target = plan.get("word_target", 0)
    if not word_target:
        try:
            from audit.config import get_word_target as _get_wt
            level_code, module_focus = track_to_level_focus(track)
            word_target = _get_wt(level_code, num, module_focus)
        except Exception:
            word_target = 0
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
        dry_run=getattr(args, "dry_run", False),
        force_phase=getattr(args, "force_phase", None),
        rebuild=getattr(args, "rebuild", False),
    )

    is_dry = getattr(args, "dry_run", False)
    if getattr(args, "rebuild", False):
        if is_dry:
            ctx.state = load_state(ctx)
            log("State: RESET (--rebuild) — DRY-RUN, no artifacts deleted")
        else:
            ctx.state = load_state(ctx)
            deleted = clean_phase_artifacts(ctx, PHASE_SEQUENCE[0], forward=True)
            state_file = _state_file(ctx)
            lock_file = state_file.with_suffix(".json.lock")
            for f in [state_file, lock_file]:
                if f.exists():
                    f.unlink()
            ctx.state = load_state(ctx)
            log(f"State: RESET (--rebuild) — deleted {deleted} artifacts")
    else:
        ctx.state = load_state(ctx)
        if not is_dry:
            if getattr(args, "force_phase", None):
                deleted = clean_phase_artifacts(ctx, args.force_phase, forward=False)
                if deleted:
                    log(f"Cleaned {deleted} artifacts for phase {args.force_phase}")
            restart_from = getattr(args, "restart_from", None)
            if restart_from:
                deleted = clean_phase_artifacts(ctx, restart_from, forward=True)
                if deleted:
                    log(f"Cleaned {deleted} artifacts from phase {restart_from} onward")
        if ctx.state.get("phases"):
            completed = [p for p, v in ctx.state["phases"].items() if v.get("status") == "complete"]
            log(f"State: Loaded — phases complete: {', '.join(completed) or 'none'}")
        else:
            log("State: Fresh")
    return ctx


def _bootstrap_meta_from_plan(track: str, slug: str) -> None:
    """Create minimal meta.yaml from plan if meta doesn't exist yet."""
    paths = get_module_paths(track, slug)
    meta_path = paths["meta"]
    plan_path = paths["plan"]
    if meta_path.exists():
        return
    if not plan_path.exists():
        return
    try:
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        log(f"  bootstrap: WARNING — plan YAML parse error for {slug}, skipping bootstrap: {e}")
        return
    wt = plan.get("word_target", 0)
    if not wt:
        try:
            from audit.config import get_word_target as _get_wt
            level_code, module_focus = track_to_level_focus(track)
            mod_num = int(slug.split("-")[-1]) if slug[0].isdigit() else 1
            wt = _get_wt(level_code, mod_num, module_focus)
        except Exception:
            wt = 0
    minimal_meta = {
        "slug": slug,
        "title": plan.get("title", slug.replace("-", " ").title()),
        "word_target": wt,
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(yaml.dump(minimal_meta, allow_unicode=True), encoding="utf-8")


def preflight_v2(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, detect archive. Returns ModuleContext."""
    track, num = args.track, args.num
    slug = slug_for_num(track, num)
    _bootstrap_meta_from_plan(track, slug)

    args.content_only = False
    args.enrich = False
    ctx = preflight(args)
    ctx.mode = "e2e"
    ctx.state["mode"] = "e2e"
    _init_state_lock(ctx)

    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    if is_seminar:
        is_archived, archive_source, archive_dir = detect_archived_prose(ctx.track, ctx.slug)
    else:
        is_archived, archive_source, archive_dir = False, "", None

    ctx.is_archived = is_archived  # type: ignore[attr-defined]
    ctx.archive_source = archive_source  # type: ignore[attr-defined]
    ctx.archive_dir = archive_dir  # type: ignore[attr-defined]
    ctx.force_research = getattr(args, "force_research", False)  # type: ignore[attr-defined]
    ctx.refresh = getattr(args, "refresh", False)  # type: ignore[attr-defined]
    ctx.restart_from = getattr(args, "restart_from", None)  # type: ignore[attr-defined]
    ctx.claude_review = getattr(args, "claude_review", False)  # type: ignore[attr-defined]
    ctx.final_review = getattr(args, "final_review", False)  # type: ignore[attr-defined]

    if is_archived:
        log(f"Archive: DETECTED — {archive_source}")
    else:
        log("Archive: none found")
    return ctx


# ============================================================================
# 21. Completion Reports
# ============================================================================

def write_completion_report_v2(ctx: ModuleContext, passed: bool) -> None:
    """Write completion report to orchestration dir."""
    content_path = ctx.paths["md"]
    word_count = 0
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())
    verdict = "PASS" if passed else "FAIL"
    is_archived = getattr(ctx, "is_archived", False)
    sections_info = ctx.state.get("phases", {}).get("2", {})
    sections_done = sections_info.get("sections_done", "?")
    sections_total = sections_info.get("sections_total", "?")
    report = textwrap.dedent(f"""\
        {verdict}: pipeline {ctx.track} {ctx.module_num}

          Module:   {ctx.slug}
          Track:    {ctx.track}
          Mode:     {ctx.mode}
          Words:    {word_count} (target: {ctx.word_target})
          Sections: {sections_done}/{sections_total}
          Archive:  {'yes — ' + getattr(ctx, 'archive_source', '') if is_archived else 'no'}
          Verdict:  {verdict}
          Date:     {_now_iso()}
    """)
    completion_file = ctx.orch_dir / "completion.md"
    completion_file.write_text(report, encoding="utf-8")
    log(f"\nCompletion report → {completion_file}")


# ============================================================================
# 22. Validation Helpers
# ============================================================================

def _validate_activities_yaml(path: Path) -> bool:
    """Check if an activities YAML file passes schema validation."""
    try:
        from audit.checks.yaml_schema_validation import validate_activity_yaml_file
        valid, errors = validate_activity_yaml_file(path)
        if not valid:
            for e in errors[:3]:
                err_str = e.replace('\n', ' ')
                if len(err_str) > 200:
                    err_str = err_str[:197] + "..."
                log(f"    Schema error: {err_str}")
        return valid
    except Exception as e:
        log(f"    Schema validation error: {e}")
        return False
