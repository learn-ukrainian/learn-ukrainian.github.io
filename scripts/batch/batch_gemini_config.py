"""
Configuration for Gemini Batch Runner.
Defines tracks, phases, templates, and validation rules.

Module numbering source of truth: curriculum/l2-uk-en/curriculum.yaml
Module N = levels.{track}.modules[N-1] (1-indexed position in the array).
"""

from pathlib import Path

import yaml
from slug_utils import review_path as _review_path
from slug_utils import status_path as _status_path
from slug_utils import to_bare_slug

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
CURRICULUM_YAML = CURRICULUM_DIR / "curriculum.yaml"
PLANS_DIR = CURRICULUM_DIR / "plans"
PHASES_DIR = PROJECT_ROOT / "claude_extensions" / "phases" / "gemini"
QUICK_REF_DIR = PROJECT_ROOT / "claude_extensions" / "quick-ref"

# Model Tiering — Gemini (3 tiers, mirrors Claude: Pro≈Opus, Flash≈Sonnet, Flash-Lite≈Haiku)
PRO_MODEL = "gemini-3.1-pro-preview"                 # Deep reasoning: writing, content, review
FLASH_MODEL = "gemini-3-flash-preview"                 # Back online 2026-04-08
FLASH_LITE_MODEL = "gemini-3.1-flash-lite-preview"   # Fast structured output: skeleton, vocab, activities
GEMINI_REVIEW_MODEL = PRO_MODEL                      # Review needs Pro for strict schema + linguistic analysis
FALLBACK_MODEL = "auto"                              # Let gemini-cli route when a model is unavailable

# Timeouts (seconds) — the hard_timeout ceiling for LLM-dispatch steps.
#
# Semantics — IMPORTANT, rewritten 2026-04-24 to match post-#1184 reality:
#
#   - ``hard_timeout`` is the ONLY kill signal the watchdog honors
#     (scripts/agent_runtime/watchdog.py:294-332). Stall detection was
#     deleted on 2026-04-10 after four documented per-CLI failure modes
#     proved it unreliable (Gemini block-buffers stdout, Codex state-file
#     moves across versions, mtime fires only at startup, each CLI has
#     a different convention). Chasing them was whack-a-mole with no
#     ground truth.
#   - ``stall_timeout`` is still accepted by the runner signature for
#     backward compat but IGNORED by ``should_kill``. Do not rely on it.
#
# ---
# The hard_timeout is NOT a tuning knob for expected phase duration. It
# is a last-ditch "this process must have hung" ceiling — nothing less.
#
# Design evolution across this file (documented for the next engineer):
#
#   1. Original (pre-#1184): tight per-phase hard_timeouts made sense
#      because stall_timeout did the real work of catching stuck runs.
#   2. Post-#1184 (stall detection deleted): tight per-phase timeouts
#      became an anti-pattern — the clock was firing on healthy-but-slow
#      LLM work before any observability could intervene. User flagged
#      this 2026-04-24 ("what if it needs more time and you kill it...
#      really poor design").
#   3. Intermediate fix (same day): unified to 3600s / 1h as the ceiling.
#      User pushed back again: "we must not kill after 1h if it is
#      active. we have seen long running processes" — i.e. they have
#      observed real productive LLM work exceeding 1h, especially on
#      seminar-track reviews and heavy Opus reasoning.
#   4. Current (THIS change): 24h ceiling for all LLM-dispatch phases.
#      The ceiling exists as a last-resort safety for truly-pathological
#      runaway processes (CLI bug, infinite retry loop). In normal
#      operation it will never fire. External observability does the
#      real monitoring:
#        - Monitor tool (v6_build.py JSONL events — one line per phase)
#        - /api/delegate/active (last-activity timestamp per dispatch)
#        - Per-CLI session files (~/.codex/sessions/YYYY/MM/DD/rollout-*,
#          ~/.gemini/tmp/learn-ukrainian/chats/session-*.json,
#          ~/.claude/projects/<proj>/*.jsonl)
#      These tell the human operator "is this dispatch productive?"
#      The ceiling is there so a bug can't leak a subprocess forever.
#
# One exception: TIMEOUT_REVIEW_GEMINI_PROBE is a genuine liveness probe
# ("is the Gemini API alive?"), not an LLM reasoning task. 300s for that.

_ONE_HOUR = 3600
_ONE_DAY = 24 * _ONE_HOUR

TIMEOUT_SKELETON = _ONE_DAY
TIMEOUT_WRITE = _ONE_DAY
TIMEOUT_WRITE_NO_TOOLS = _ONE_DAY
TIMEOUT_VOCAB = _ONE_DAY
TIMEOUT_ACTIVITIES = _ONE_DAY
TIMEOUT_REVIEW_GEMINI_PROBE = 300  # Genuine probe — "is Gemini API alive"
TIMEOUT_REVIEW_CLAUDE = _ONE_DAY
TIMEOUT_PRE_VERIFY = _ONE_DAY
TIMEOUT_ANNOTATE = _ONE_DAY
TIMEOUT_PUBLISH = _ONE_DAY

# Per-call cap inside the cascade fallback loop. The dispatcher chains
# model fallbacks (pro → auto) and retries; this value is the per-call
# hard_timeout the fallback rungs inherit.
#
# Aligned to _ONE_DAY on 2026-04-24 (was 600s) for the same reason the
# phase timeouts above were unified: rungs fall over on ERRORS (rate
# limit, auth, model-unavailable) which surface fast. There is no
# correctness win to capping a slow-but-productive Pro call at 10 min —
# it just kills work the user wanted. See bridge architecture discussion
# thread 0f94b8c0 (Codex + Gemini both flagged this as a hidden ceiling
# silently overriding the 24h policy).
CASCADE_PER_CALL_MAX_S = _ONE_DAY

# Model Tiering — Claude (used by build_module_v5.py --use-claude phases)
# Change these to switch models across the entire pipeline without touching CLI flags.
# Research:      seminar tracks → Opus, core tracks → Sonnet
# Content:       always Opus (quality content generation)
# Apr 2026: Sonnet 4.6 is the better default on Pro — Opus burns ~2x faster.
# Use Opus ONLY where deep reasoning is critical (seminar content, final review).
# Ref: Anthropic guidance (Lydia Hallie, 2026-04-03)
CLAUDE_SONNET = "claude-sonnet-4-6"
CLAUDE_OPUS   = "claude-opus-4-7"

CLAUDE_MODEL_CORE_RESEARCH      = CLAUDE_SONNET  # Research — RAG search + summarization
CLAUDE_MODEL_CORE_CONTENT       = CLAUDE_OPUS    # Content — writing quality needs Opus
CLAUDE_MODEL_CORE_ACTIVITIES    = CLAUDE_SONNET  # Activities — schema-guided generation
CLAUDE_MODEL_SEMINAR_RESEARCH   = CLAUDE_SONNET  # Research — RAG search + summarization
CLAUDE_MODEL_SEMINAR_CONTENT    = CLAUDE_OPUS    # Content — seminar depth needs Opus
CLAUDE_MODEL_SEMINAR_ACTIVITIES = CLAUDE_SONNET  # Activities — schema-guided generation
CLAUDE_MODEL_FINAL_REVIEW       = CLAUDE_OPUS    # Final review — quality is non-negotiable

# Default phases dispatched via Claude (instead of Gemini).
# Set of phase letters: "A" = research, "B" = content, "C" = activities.
# Review is controlled separately via CLAUDE_DEFAULT_REVIEW.
# CLI --use-claude overrides this when provided.
CLAUDE_DEFAULT_PHASES: set[str] = {"A"}          # Research via Claude by default

# Default review agent: "claude" or "gemini".
# CLI --review-claude / --review overrides this.
CLAUDE_DEFAULT_REVIEW: str = "claude"

# Seminar tracks get research (phase 0) + review (phase 5)
SEMINAR_TRACKS = {
    "bio", "hist", "istorio", "lit", "oes", "ruth", "folk",
    "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-youth",
    "lit-drama",
}

# Professional tracks: need external research (not covered by State Standard)
# Use research-pro.md (terminology, ДСТУ norms, authentic examples) not research-seminar.md
PRO_TRACKS = {"b2-pro", "c1-pro"}

# --- Shared template sets (DRY: defined once, reused across all track configs) ---
_COMMON_TEMPLATES = {
    2: PHASES_DIR / "content.md",
    3: PHASES_DIR / "activities.md",
    5: PHASES_DIR / "review-legacy.md",
    "fix": PHASES_DIR / "fix.md",
    "fix-content": PHASES_DIR / "fix-content.md",
    "fix-activities": PHASES_DIR / "fix-activities.md",
}
SEMINAR_TEMPLATES = {0: PHASES_DIR / "research-seminar-v0.md", **_COMMON_TEMPLATES}
CORE_TEMPLATES = {1: PHASES_DIR / "research-core.md", **_COMMON_TEMPLATES}


def _seminar(quick_ref_name: str) -> dict:
    """Build a seminar track config. Only quick_ref differs between tracks."""
    return {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": SEMINAR_TEMPLATES,
        "quick_ref": QUICK_REF_DIR / f"{quick_ref_name}.md",
        "validation_phases": [2, 3],
    }


def _core(quick_ref_name: str) -> dict:
    """Build a core track config. Only quick_ref differs between tracks."""
    return {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": CORE_TEMPLATES,
        "quick_ref": QUICK_REF_DIR / f"{quick_ref_name}.md",
        "validation_phases": [2, 3],
    }


# Track definitions
TRACK_CONFIGS = {
    # --- Seminar tracks (Pro Model MANDATORY) ---
    "bio":            _seminar("BIO"),
    "hist":           _seminar("HIST"),
    "istorio":        _seminar("ISTORIO"),
    "lit":            _seminar("LIT"),
    "lit-essay":      _seminar("LIT"),
    "lit-hist-fic":   _seminar("LIT"),
    "lit-fantastika": _seminar("LIT"),
    "lit-war":        _seminar("LIT"),
    "lit-humor":      _seminar("LIT"),
    "lit-youth":      _seminar("LIT"),
    "lit-drama":      _seminar("LIT"),
    "folk":           _seminar("FOLK"),
    "oes":            _seminar("OES"),
    "ruth":           _seminar("RUTH"),
    # --- Core tracks (all Pro — flash too weak for quality content) ---
    "a1": _core("A1"),
    "a2": _core("A2"),
    "b1": _core("B1"),
    "b2": _core("B2"),
    "c1": _core("C1"),
    "c2": _core("C2"),
}

# Default for unlisted tracks
DEFAULT_CONFIG = {
    "type": "core",
    "model": FLASH_MODEL,
    "phases": [2, 3, 5],
    "templates": _COMMON_TEMPLATES,
    "quick_ref": None,
    "validation_phases": [2, 3],
}

# --- Module Index (loaded once from curriculum.yaml) ---

_module_index_cache = {}


def _load_curriculum():
    """Load curriculum.yaml once, cache the result."""
    if not _module_index_cache:
        data = yaml.safe_load(CURRICULUM_YAML.read_text(encoding="utf-8"))
        for level, info in data.get("levels", {}).items():
            modules = info.get("modules", [])
            # num_to_slug: 1-indexed position → slug
            # slug_to_num: slug → 1-indexed position
            num_to_slug = {}
            slug_to_num = {}
            for i, entry in enumerate(modules):
                num = i + 1
                # Core tracks have "39-buying-tickets" format, extract bare slug
                slug = to_bare_slug(entry)
                num_to_slug[num] = slug
                slug_to_num[slug] = num
            _module_index_cache[level] = {
                "num_to_slug": num_to_slug,
                "slug_to_num": slug_to_num,
                "total": len(modules),
                "raw_entries": modules,
            }
    return _module_index_cache


def get_module_index(track: str) -> dict:
    """Get the module index for a track.

    Returns dict with:
      num_to_slug: {1: 'knyahynia-olha', 2: 'kniaz-sviatoslav', ...}
      slug_to_num: {'knyahynia-olha': 1, 'kniaz-sviatoslav': 2, ...}
      total: int
      raw_entries: ['knyahynia-olha', 'kniaz-sviatoslav', ...] (as in curriculum.yaml)
    """
    idx = _load_curriculum()
    if track not in idx:
        raise ValueError(
            f"Track '{track}' not found in curriculum.yaml. "
            f"Available: {sorted(idx.keys())}"
        )
    return idx[track]


def slug_for_num(track: str, num: int) -> str:
    """Get slug for a module number. Raises ValueError if not found."""
    idx = get_module_index(track)
    if num not in idx["num_to_slug"]:
        raise ValueError(
            f"Module {num} not found in {track} "
            f"(has {idx['total']} modules, range 1-{idx['total']})"
        )
    return idx["num_to_slug"][num]


def num_for_slug(track: str, slug: str) -> int:
    """Get module number for a slug. Raises ValueError if not found."""
    idx = get_module_index(track)
    if slug not in idx["slug_to_num"]:
        raise ValueError(f"Slug '{slug}' not found in {track}")
    return idx["slug_to_num"][slug]


def get_track_config(track_name: str) -> dict:
    """Get config for a track, with quick_ref auto-detection."""
    config = TRACK_CONFIGS.get(track_name, DEFAULT_CONFIG).copy()

    # Auto-detect quick_ref if not set or file missing
    if not config.get("quick_ref") or not config["quick_ref"].exists():
        for variant in [track_name.upper(), track_name, track_name.lower()]:
            qr_path = QUICK_REF_DIR / f"{variant}.md"
            if qr_path.exists():
                config["quick_ref"] = qr_path
                break

    return config


def get_module_paths(track: str, slug: str) -> dict:
    """Resolve all file paths for a module. All tracks use bare slugs."""
    bare_slug = to_bare_slug(slug)
    track_dir = CURRICULUM_DIR / track
    plans_track_dir = PLANS_DIR / track

    return {
        "md": track_dir / f"{bare_slug}.md",
        "activities": track_dir / "activities" / f"{bare_slug}.yaml",
        "vocabulary": track_dir / "vocabulary" / f"{bare_slug}.yaml",
        "plan": plans_track_dir / f"{bare_slug}.yaml",
        "research": track_dir / "research" / f"{bare_slug}-research.md",
        "orchestration": track_dir / "orchestration" / bare_slug,
        "review": _review_path(track_dir, bare_slug),
        "status": _status_path(track_dir, bare_slug),
    }
