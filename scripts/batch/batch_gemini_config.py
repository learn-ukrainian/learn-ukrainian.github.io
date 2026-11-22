"""
Configuration for Gemini Batch Runner.
Defines tracks, phases, templates, and validation rules.

Module numbering source of truth: curriculum/l2-uk-en/curriculum.yaml
Module N = levels.{track}.modules[N-1] (1-indexed position in the array).
"""

from pathlib import Path

import yaml
from lu_machinery.agent_runtime.adapters import acpx
from lu_machinery.common.repo_root import project_interpreter
from lu_machinery.review import model_catalog

try:
    from slug_utils import review_path as _review_path
    from slug_utils import status_path as _status_path
    from slug_utils import to_bare_slug
except ModuleNotFoundError:  # imported as scripts.batch.batch_gemini_config: repo root on path, scripts/ is not
    from scripts.slug_utils import review_path as _review_path
    from scripts.slug_utils import status_path as _status_path
    from scripts.slug_utils import to_bare_slug


def __getattr__(name: str) -> str:
    """Resolve ``VENV_PYTHON`` on first use, not at import.

    A release snapshot and a copied tree have no ``.venv``. Import of this
    module (the sense-lint and API startup chain) must succeed there; the
    interpreter is needed only when a later spawn asks for it.
    """
    if name != "VENV_PYTHON":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = str(project_interpreter(PROJECT_ROOT.resolve()))
    globals()["VENV_PYTHON"] = value
    return value


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
CURRICULUM_YAML = CURRICULUM_DIR / "curriculum.yaml"
PLANS_DIR = CURRICULUM_DIR / "plans"
PHASES_DIR = PROJECT_ROOT / "agents_extensions/shared" / "phases" / "gemini"
QUICK_REF_DIR = PROJECT_ROOT / "agents_extensions/shared" / "quick-ref"


class GeminiSeatUnavailable(RuntimeError):
    """The installed lu-machinery catalog assigns no executable Gemini seat for one or more roles."""

    def __init__(self, roles: tuple[str, ...], reason: str) -> None:
        super().__init__(
            f"no Gemini seat for role {', '.join(map(repr, roles))} in the installed lu-machinery "
            f"catalog ({reason}); install a lu-machinery release that assigns one"
        )
        self.roles = roles


GEMINI_ROLES = ("review", "routine")


def _gemini_seat(role: str, catalog: dict) -> str:
    """Return the AGY wire id the validated ``catalog`` assigns to ``role``, or raise ``GeminiSeatUnavailable``.

    ``review``: the AGY ACP participant pin, the only model ``ask-agy``/``ask-gemini`` admit
    (review, judge and every caller that dispatches through the bridge).
    ``routine``: the catalog's AGY orchestrator seat as its AGY wire id (native ``agy`` generation).
    Either seat must be an active catalog model with the AGY transport.
    """
    if role not in GEMINI_ROLES:
        raise GeminiSeatUnavailable((role,), "unknown role")
    try:
        if role == "review":
            wire_id = acpx.ACPX_SUPPORTED_PARTICIPANTS["agy"]["model"]
        else:
            wire_id = catalog["models"][catalog["orchestrator_seats"]["agy"]["model_id"]]["routing_wire_ids"]["agy"]
        if isinstance(wire_id, str) and wire_id:
            model_catalog.require_execution_model(wire_id, transport="agy", catalog=catalog)
            return wire_id
    except Exception as exc:  # any lookup or admission failure means this role has no seat; the cause is chained
        raise GeminiSeatUnavailable((role,), f"{type(exc).__name__}: {exc}") from exc
    raise GeminiSeatUnavailable((role,), f"seat is {wire_id!r}")


def _gemini_seats() -> tuple[str, str]:
    """Resolve both roles at import, so every caller fails at import; no placeholder and no default.

    The catalog is loaded and validated once, before either role, so a role never inherits an
    error that belongs to the catalog as a whole. A catalog that cannot be loaded or validated,
    whatever the validator raises, yields no seat for any role; the cause is chained and its
    message names the bad entry where the validator does.
    """
    try:
        catalog = model_catalog.load_model_catalog()
    except Exception as exc:
        raise GeminiSeatUnavailable(GEMINI_ROLES, f"the catalog is invalid: {type(exc).__name__}: {exc}") from exc
    review, routine = (_gemini_seat(role, catalog) for role in GEMINI_ROLES)
    return review, routine


# The two Gemini roles, resolved from the installed catalog at import (no model literals).
GEMINI_REVIEW_MODEL, GEMINI_ROUTINE_MODEL = _gemini_seats()
# Tier names are compatibility aliases. Their callers dispatch through the AGY ACP bridge,
# which admits only the review seat.
PRO_MODEL = GEMINI_REVIEW_MODEL
FLASH_MODEL = GEMINI_REVIEW_MODEL
FLASH_LITE_MODEL = GEMINI_REVIEW_MODEL

# Timeouts (seconds) — the hard_timeout ceiling for LLM-dispatch steps.
#
# Semantics — IMPORTANT, rewritten 2026-04-24 to match post-#1184 reality:
#
#   - ``hard_timeout`` is the ONLY kill signal the watchdog honors
#     (lu_machinery/agent_runtime/watchdog.py). Stall detection was
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
# Sonnet is the routine default; reserve Opus for consequential judgment.
# Use Opus ONLY where deep reasoning is critical (seminar content, final review).
# Ref: Anthropic guidance (Lydia Hallie, 2026-04-03)
CLAUDE_SONNET = "claude-sonnet-5-5"
CLAUDE_OPUS   = "claude-opus-5-5"

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

PRO_TRACKS: set[str] = set()

# --- Shared template sets (DRY: defined once, reused across all track configs) ---
_COMMON_TEMPLATES = {
    2: PHASES_DIR / "content.md",
    3: PHASES_DIR / "activities.md",
    5: PHASES_DIR / "phase-5-review.md",
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
