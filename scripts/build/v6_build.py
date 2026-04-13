#!/usr/bin/env python3
"""V6 Pipeline Build — two-call Skeleton->Flesh content generation.

Orchestrates the V6 pipeline:
1. CHECK: Plan checker validation
2. RESEARCH: Build knowledge packet from RAG
3. SKELETON: Paragraph-level structure plan (always on, --no-skeleton to skip)
4. WRITE: LLM session constrained by skeleton (prose + exercises)
5b. EXERCISES: Fill placeholders with DSL
5d. VERIFY EXERCISES: Check exercise items grounded in prose (#1016)
6. ANNOTATE: Stress marks + deterministic fixes
7. VERIFY: VESUM + grammar scope
8. REVIEW: Cross-agent adversarial review
9. PUBLISH: Assemble 4-tab MDX from prose (.md) + vocabulary YAML + activities YAML + resources

The Skeleton->Flesh architecture (#998) splits content generation into two calls
for all modules (use --no-skeleton to skip):
- Call 1 (Skeleton): Short output (~500-800 words) planning every paragraph
- Call 2 (Flesh): Full prose following the skeleton exactly

This prevents frontloading early sections and rushing later ones.
Use --no-skeleton to skip for quick iteration.

Usage:
    .venv/bin/python scripts/build/v6_build.py a1 1
    .venv/bin/python scripts/build/v6_build.py b1 1 --skeleton    # force skeleton
    .venv/bin/python scripts/build/v6_build.py b1 1 --no-skeleton # skip skeleton
    .venv/bin/python scripts/build/v6_build.py a1 1 --step write  # run single step
    .venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini  # default
    .venv/bin/python scripts/build/v6_build.py a1 1 --writer claude
    .venv/bin/python scripts/build/v6_build.py a1 1 --resume       # resume from last completed phase
    .venv/bin/python scripts/build/v6_build.py a1 1 --range 14     # batch (skips complete, rebuilds partial)
    .venv/bin/python scripts/build/v6_build.py a1 1 --range 14 --resume  # batch + resume partial modules

Issue: #993, #998
"""

from __future__ import annotations

import argparse
import fcntl
import io
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from analytics.cost_report import format_module_cost_summary
from batch_gemini_config import (
    # FLASH_MODEL removed from imports 2026-04-10 — Flash is unreliable and
    # GEMINI_FAMILY.fast now points directly at PRO_MODEL. When Flash is
    # stable again, re-add the import and flip v6_build.GEMINI_FAMILY.fast
    # back to FLASH_MODEL.
    PRO_MODEL,
    TIMEOUT_ACTIVITIES,
    TIMEOUT_ANNOTATE,
    TIMEOUT_PRE_VERIFY,
    TIMEOUT_PUBLISH,
    TIMEOUT_REVIEW_CLAUDE,
    TIMEOUT_REVIEW_GEMINI_PROBE,
    TIMEOUT_SKELETON,
    TIMEOUT_VOCAB,
    TIMEOUT_WRITE,
    TIMEOUT_WRITE_NO_TOOLS,
)

logger = logging.getLogger(__name__)

# Rate limit backoff — shared by all retry loops
_RATE_LIMIT_BACKOFF_S = 300  # 5 min — long enough for Gemini quota to recover
REVIEW_TARGET_SCORE = 9.0


def _handle_rate_limit_backoff(raw: str, attempt: int, max_attempts: int, phase: str) -> bool:
    """Check if dispatch returned a rate limit signal. If so, back off.

    Returns True if rate-limited (caller should continue the retry loop),
    False if this was a normal failure.
    """
    if raw != "__RATE_LIMITED__":
        return False
    if attempt < max_attempts:
        _log(f"  ⏳ Rate limited during {phase} (attempt {attempt}/{max_attempts}) — backing off {_RATE_LIMIT_BACKOFF_S}s...")
        time.sleep(_RATE_LIMIT_BACKOFF_S)
    else:
        _log(f"  ❌ Rate limited during {phase} — giving up after {max_attempts} attempts")
    return True


def _get_failing_audit_gates(level: str, slug: str) -> tuple[str, list[str]]:
    """Read the latest status JSON and return the overall status plus failing gates."""
    status_path = CURRICULUM_ROOT / level / "status" / f"{slug}.json"
    if not status_path.exists():
        return "missing", ["status-file-missing"]

    try:
        status = json.loads(status_path.read_text("utf-8"))
    except Exception:
        return "invalid", ["status-file-invalid"]

    overall_status = status.get("overall", {}).get("status", "unknown")
    gates = status.get("gates", {})
    failing = [
        gate_name
        for gate_name, gate_data in gates.items()
        if isinstance(gate_data, dict) and gate_data.get("status") == "fail"
    ]

    if failing:
        return overall_status, failing
    if overall_status in ("pass", "content-complete"):
        return overall_status, []
    return overall_status, ["overall-status"]

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
PIDRUCHNYK_URLS_PATH = PROJECT_ROOT / "data" / "pidruchnyk_urls.yaml"

_PIDRUCHNYK_AUTHOR_NAMES = {
    "avramenko": "Авраменко",
    "betsa": "Беца",
    "bolshakova": "Большакова",
    "borzenko": "Борзенко",
    "burnejko": "Бурнейко",
    "burneyko": "Бурнейко",
    "galimov": "Галімов",
    "gisem": "Гісем",
    "glazova": "Глазова",
    "glazov": "Глазова",
    "golub": "Голуб",
    "hlibovska": "Хлібовська",
    "karaman": "Караман",
    "khlibovska": "Хлібовська",
    "kovalenko": "Коваленко",
    "kravcova": "Кравцова",
    "kravtsova": "Кравцова",
    "litvinova": "Літвінова",
    "mishhenko": "Міщенко",
    "onatiy": "Онатій",
    "ponomarova": "Пономарьова",
    "pometun": "Пометун",
    "savchenko": "Савченко",
    "savchuk": "Савчук",
    "schupak": "Щупак",
    "semenog": "Семеног",
    "shchupak": "Щупак",
    "uhor": "Угор",
    "varzatska": "Варзацька",
    "vashulenko": "Вашуленко",
    "voron": "Ворон",
    "zabolotnij": "Заболотний",
    "zabolotnyi": "Заболотний",
    "zaharijchuk": "Захарійчук",
}


# ─── Module-level build lock ────────────────────────────────────────
# Prevents two v6_build.py processes from racing on the same module.
# Uses fcntl.flock (advisory lock) — automatically released on crash/exit.

class ModuleBuildLock:
    """File-based lock per module. Prevents concurrent builds on the same slug."""

    def __init__(self, level: str, slug: str):
        lock_dir = CURRICULUM_ROOT / level / "orchestration" / slug
        lock_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path = lock_dir / ".build.lock"
        self._fd: int | None = None

    def acquire(self) -> bool:
        """Try to acquire the lock. Returns False if another build holds it.

        Uses fcntl.flock (advisory lock) — automatically released when the
        process exits, even on crash or kill -9. Locks CANNOT get stuck.
        As extra safety: if the lock file's PID is dead, we steal the lock.
        """
        self._fd = os.open(str(self._lock_path), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Write PID for diagnostics
            os.ftruncate(self._fd, 0)
            os.write(self._fd, f"{os.getpid()}\n".encode())
            return True
        except OSError:
            # Another process holds the lock — check if it's still alive
            locked_pid_str = "?"
            try:
                os.lseek(self._fd, 0, os.SEEK_SET)
                locked_pid_str = os.read(self._fd, 32).decode().strip()
                locked_pid = int(locked_pid_str)
                # Check if the locking process is still running
                os.kill(locked_pid, 0)  # signal 0 = check existence
            except (ValueError, ProcessLookupError):
                # PID is dead or invalid — steal the lock
                # (This shouldn't normally happen since flock auto-releases,
                # but handles edge cases like NFS or manual lock file creation)
                os.close(self._fd)
                self._fd = os.open(str(self._lock_path), os.O_CREAT | os.O_RDWR | os.O_TRUNC)
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    os.write(self._fd, f"{os.getpid()}\n".encode())
                    _log("  🔓 Stale lock detected (dead PID) — acquired.")
                    return True
                except OSError:
                    pass
            except OSError:
                locked_pid_str = "?"

            os.close(self._fd)
            self._fd = None
            _log(f"  ⚠️  LOCKED by PID {locked_pid_str} — another build is running on this module. Skipping.")
            return False

    def release(self) -> None:
        """Release the lock."""
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None

PHASES_DIR = PROJECT_ROOT / "scripts" / "build" / "phases"


# ---------------------------------------------------------------------------
# Model Family — single source of truth for model selection (#1072)
# ---------------------------------------------------------------------------

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelFamily:
    """Model configuration for a writer/reviewer family (Claude, Gemini, or Codex).

    Each family has two tiers:
    - thinking: full reasoning model (write, review, section rewrite)
    - fast: efficient model (skeleton, activities, vocab)

    And a tool prefix for MCP tool instructions (empty for Codex, which
    uses shell commands instead of MCP JSON-RPC).
    """

    name: str           # "claude", "gemini", or "codex"
    thinking: str       # opus / pro / gpt-5.4 — for write, review, rewrite
    fast: str           # sonnet / flash / gpt-5.4 — for skeleton, activities, vocab
    tool_prefix: str    # "mcp__rag__" (Claude), "mcp_rag_" (Gemini), "" (Codex)


@dataclass(frozen=True)
class ReviewParseResult:
    """Deterministic parse of a review markdown file."""

    score: float
    verdict: str
    raw_scores: list[int]
    parsed_scores: list[dict]
    dim_floor_fail: bool
    passed: bool


CLAUDE_FAMILY = ModelFamily(
    name="claude",
    thinking="claude-opus-4-6",
    fast="claude-sonnet-4-6",
    tool_prefix="mcp__rag__",
)

GEMINI_FAMILY = ModelFamily(
    name="gemini",
    thinking=PRO_MODEL,
    # 2026-04-10: Flash is unreliable right now (slow / intermittent 300s
    # hard timeouts on every single call). The cascade (flash → pro → auto)
    # DOES recover, but each step wastes 300s waiting for Flash to fail
    # before falling back to Pro. Since the user's Google AI Pro quota is
    # fine, we point `fast` directly at Pro. When Flash stabilizes, flip
    # this back to FLASH_MODEL.
    fast=PRO_MODEL,
    tool_prefix="mcp_rag_",
)

CODEX_FAMILY = ModelFamily(
    name="codex",
    thinking="gpt-5.4",
    fast="gpt-5.4",
    # Codex uses shell commands for verification instead of MCP JSON-RPC.
    # Tool instructions are loaded from scripts/tools/codex_tool_instructions.md
    # and injected into the prompt. No tool_prefix needed.
    tool_prefix="",
)


def get_family(writer: str) -> ModelFamily:
    """Resolve writer/reviewer string to a ModelFamily."""
    if "claude" in writer:
        return CLAUDE_FAMILY
    if "gemini" in writer:
        return GEMINI_FAMILY
    if "codex" in writer:
        return CODEX_FAMILY
    raise ValueError(f"Unknown model family for writer: {writer}")


def _build_tool_instructions(writer: str) -> str:
    """Build MCP tool-use instructions for the writer prompt.

    Uses explicit conditional triggers (Gemini's recommendation) to guide
    when to use tools vs just write. Batching enforced to prevent excessive
    tool calls.

    For Codex writers, loads shell-command tool instructions from
    scripts/tools/codex_tool_instructions.md instead of MCP tool references.
    Codex runs via `codex exec --full-auto` and can execute arbitrary Python
    via subprocess, so it gets direct shell commands instead of MCP JSON-RPC.
    Issue: #1194
    """
    # Codex uses shell commands, not MCP — load from dedicated markdown file
    if "codex" in writer:
        instructions_path = PROJECT_ROOT / "scripts" / "tools" / "codex_tool_instructions.md"
        if instructions_path.exists():
            return "\n\n---\n\n" + instructions_path.read_text("utf-8")
        # Fallback: return empty if file missing (shouldn't happen)
        return ""

    # Tool name prefix differs by family (Claude vs Gemini MCP)
    p = get_family(writer).tool_prefix

    return (
        "\n\n---\n\n"
        "## Live Verification Tools (MCP)\n\n"
        "You have access to RAG-powered MCP tools to verify Ukrainian language "
        "constructs **live as you write**. The research phase is already complete; "
        "use these tools strictly for targeted verification to ensure zero "
        "Russianisms, accurate grammar, and authentic usage.\n\n"
        "**Core Tools:**\n"
        f"- `{p}verify_words` / `{p}verify_word` / `{p}verify_lemma` — VESUM morphological dictionary "
        "(409K lemmas, 6.7M forms). Returns full declension/conjugation.\n"
        f"- `{p}search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).\n"
        f"- `{p}search_literary` — Primary literary sources (chronicles, poetry, legal texts).\n"
        f"- `{p}query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).\n"
        f"- `{p}query_wikipedia` — Ukrainian Wikipedia.\n\n"
        "**Dictionary Tools (NEW — use these for quality):**\n"
        f"- `{p}search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** "
        "Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.\n"
        f"- `{p}query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is "
        "level-appropriate (A1/A2/B1 etc.).\n"
        f"- `{p}search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.\n"
        f"- `{p}search_etymology` — Грінченко (67K entries). Historical forms, etymology.\n"
        f"- `{p}search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.\n"
        f"- `{p}search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.\n"
        f"- `{p}translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.\n"
        f"- `{p}query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, "
        "concordance. Use when unsure if a collocation is natural.\n"
        f"- `{p}query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. "
        "Use when verify_lemma isn't enough.\n"
        f"- `{p}query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word "
        "might be a Russicism — finds the proper Ukrainian alternative.\n\n"
        "**WHEN to use tools (Specific Triggers):**\n\n"
        "1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**\n"
        "   - *Trigger:* You are about to use a word that sounds similar to Russian, "
        "a calque, or you are unsure of its exact Ukrainian equivalent.\n"
        f"   - *Action:* Use `{p}search_style_guide` first (it knows calques). "
        f"Then `{p}query_r2u` for the proper Ukrainian equivalent. "
        f"Then verify with `{p}verify_words`.\n"
        "   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).\n\n"
        "2. **Vocabulary Level Check:**\n"
        "   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.\n"
        f"   - *Action:* Use `{p}query_cefr_level` to verify the word's CEFR level.\n\n"
        "3. **Grammar & Morphology Doubts:**\n"
        "   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.\n"
        f"   - *Action:* Use `{p}verify_lemma` to pull the complete declension/conjugation.\n\n"
        "4. **Natural Expressions:**\n"
        "   - *Trigger:* You need a natural idiom or collocation for a dialogue.\n"
        f"   - *Action:* Use `{p}search_idioms` for Ukrainian expressions, "
        f"`{p}search_synonyms` for word variety.\n\n"
        "5. **Drafting Grammar Rules:**\n"
        "   - *Trigger:* You are explaining a spelling or phonetic rule.\n"
        f"   - *Action:* Use `{p}query_pravopys` to confirm the exact 2019 standard.\n\n"
        "6. **Checking Collocations & Frequency:**\n"
        "   - *Trigger:* You want to confirm a word combination is actually used by native speakers.\n"
        f"   - *Action:* Use `{p}query_grac` with mode='collocations' to see real-world usage.\n\n"
        "**MANDATORY Verification (these are NOT optional):**\n\n"
        "7. **Letter/Sound Decomposition (ALWAYS VERIFY):**\n"
        "   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.\n"
        f"   - *Action:* BEFORE writing the decomposition, call `{p}verify_word` on that word. "
        "The response shows the exact letter forms. Use ONLY what the tool returns. "
        "NEVER decompose a word from memory — your pre-training has wrong letter mappings "
        "(e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.\n"
        "   - *Example:* Before writing 'вулиця has letters В, У, Л...', call "
        f"`{p}verify_word(\"вулиця\")` and copy the letters from the result.\n\n"
        "8. **Phonetic Claims (ALWAYS VERIFY):**\n"
        "   - *Trigger:* You are stating how a letter sounds in a specific word, "
        "how many syllables a word has, or where stress falls.\n"
        f"   - *Action:* Call `{p}verify_word` to confirm. Ukrainian letters like є, ї, я, ю "
        "change sound value depending on position (after consonant vs word-initial). "
        "Do NOT guess — verify each claim.\n\n"
        "9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**\n"
        "   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.\n"
        f"   - *Action:* Use `{p}query_pravopys` or `{p}search_text` to confirm. "
        "If you can't verify it, flag with `<!-- VERIFY: claim -->`.\n\n"
        "**Efficiency Rules:**\n"
        f"- **Batch your checks:** Use `{p}verify_words` with 5-15 words at once.\n"
        "- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.\n"
        "- **Zero invention:** If VESUM doesn't know a word, don't use it.\n"
        "- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).\n\n"
        "IMPORTANT: After using tools, output your COMPLETE module content as plain text. "
        "Do NOT narrate your tool usage. Just output the final module content.\n"
    )

# Keywords to filter ENRICH-generated content from review findings.
# The reviewer shouldn't blame the writer for словník issues added by ENRICH.
_ENRICH_FILTER_KEYWORDS = (
    "словник", "slovnyk", "vocabulary table", "vocab tab",
    "enrich", "video", "youtube", "resource", "ресурси",
)


def _get_immersion_target_short(level: str, module_num: int) -> str:
    """Return a short immersion target string for the Hard Rules section.

    M01-M03 get an extra warning because the learner cannot read Cyrillic yet.
    """
    base = level.split("-")[0]
    if base == "a1":
        if module_num <= 3:
            return (
                "5-15% Ukrainian MAXIMUM. THE LEARNER CANNOT READ CYRILLIC YET. "
                "English must dominate completely. Ukrainian appears ONLY as bolded "
                "inline words with immediate English translation."
            )
        if module_num <= 6:
            return "5-15% Ukrainian"
        if module_num <= 14:
            return "10-20% Ukrainian"
        if module_num <= 24:
            return "15-25% Ukrainian"
        if module_num <= 34:
            return "15-30% Ukrainian"
        return "20-35% Ukrainian"
    elif base == "a2":
        if module_num <= 3:
            return "20-40% Ukrainian — bridge from A1, reviewing A1 grammar + introducing A2 metalanguage."
        elif module_num <= 7:
            return "30-50% Ukrainian — ramp up. Mix theory with applied Ukrainian (dialogues, pattern boxes)."
        elif module_num <= 20:
            return "45-65% Ukrainian — nearly half in Ukrainian. English for grammar theory only."
        elif module_num <= 50:
            return "55-75% Ukrainian — Ukrainian dominates. English for abstract grammar only."
        else:
            return "70-90% Ukrainian — near-full immersion. English only in vocabulary tab."
    elif base == "b1":
        return "40-60% Ukrainian"
    else:
        return "60-90%+ Ukrainian"


def _build_salad_phase_placeholders(level: str, module_num: int) -> dict[str, str]:
    """Resolve SALAD_* placeholders from the paragraph-language phase config.

    Uses audit/checks/language_salad.py:get_phase() as the source of truth.
    """
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from audit.checks.language_salad import get_phase
        phase = get_phase(level, module_num)
    except Exception:
        # Fallback if detector import fails — use conservative defaults
        return {
            "{SALAD_PHASE_NUMBER}": "?",
            "{SALAD_PHASE_NAME}": "unknown",
            "{SALAD_UK_PARAGRAPHS_ALLOWED}": "yes",
            "{SALAD_MIN_SENTENCES}": "3",
            "{SALAD_MAX_SENTENCES}": "8",
            "{SALAD_TRANSLATION_PCT}": "100",
        }

    return {
        "{SALAD_PHASE_NUMBER}": str(phase.number),
        "{SALAD_PHASE_NAME}": phase.name,
        "{SALAD_UK_PARAGRAPHS_ALLOWED}": (
            "YES — write Ukrainian paragraphs with full English translation blocks"
            if phase.allow_uk_paragraphs
            else "NO — isolated Ukrainian example sentences only, no multi-sentence UK prose paragraphs"
        ),
        "{SALAD_MIN_SENTENCES}": str(phase.min_paragraph_sentences),
        "{SALAD_MAX_SENTENCES}": str(phase.max_paragraph_sentences),
        "{SALAD_TRANSLATION_PCT}": f"{int(phase.translation_frequency * 100)}",
    }


def _build_dialogue_situations(plan: dict) -> str:
    """Build dialogue situation hints from plan's dialogue_situations field."""
    situations = plan.get("dialogue_situations", [])
    if not situations:
        return "(No specific dialogue situations in plan — pick a unique real-world setting that motivates the grammar.)"

    lines = ["**Module-specific dialogue settings (from plan):**"]
    for i, sit in enumerate(situations, 1):
        setting = sit.get("setting", "")
        speakers = sit.get("speakers", [])
        motivation = sit.get("motivation", "")
        lines.append(f"  {i}. **{setting}**")
        if speakers:
            lines.append(f"     Speakers: {', '.join(speakers)}")
        if motivation:
            lines.append(f"     Why: {motivation}")
    lines.append("\n  Use these settings. Do NOT substitute with a room description or generic greeting.")
    return "\n".join(lines)


def _extract_body(content: str) -> tuple[str, str]:
    """Extract lesson body (prose) and tail (Словник/Ресурси tabs).

    Returns (body, tail). Body is the prose content between TAB:Урок
    and TAB:Словник. Tail is everything from TAB:Словник onward.

    IMPORTANT: content.find("<!-- TAB:") matches TAB:Урок at pos 0,
    giving empty body. Always find Словник/Ресурси specifically.
    """
    slovnyk_idx = content.find("<!-- TAB:Словник -->")
    resursy_idx = content.find("<!-- TAB:Ресурси -->")
    if slovnyk_idx > 0:
        body = content[:slovnyk_idx].strip()
        tail = content[slovnyk_idx:]
    elif resursy_idx > 0:
        body = content[:resursy_idx].strip()
        tail = content[resursy_idx:]
    else:
        body = content
        tail = ""
    # Strip TAB:Урок marker
    body = body.replace("<!-- TAB:Урок -->", "").strip()
    return body, tail


def _clean_build_artifacts(level: str, slug: str) -> None:
    """Remove previous build artifacts for a clean full rebuild.

    Preserves: plan YAML, orchestration/index.md, friction.yaml.
    Removes: content .md, activities YAML, vocabulary YAML, review files,
    audit files, status cache, dispatch logs, prompts, skeleton, state.
    """
    import shutil

    base = CURRICULUM_ROOT / level
    orch = base / "orchestration" / slug

    removed = 0

    # Content + vocab + activities
    for path in [
        base / f"{slug}.md",
        base / "activities" / f"{slug}.yaml",
        base / "vocabulary" / f"{slug}.yaml",
    ]:
        if path.exists():
            path.unlink()
            removed += 1

    # Review files
    review_dir = base / "review"
    if review_dir.exists():
        for f in review_dir.glob(f"{slug}-review*"):
            f.unlink()
            removed += 1

    # Audit + status
    for path in [
        base / "audit" / f"{slug}-audit.md",
        base / "status" / f"{slug}.json",
    ]:
        if path.exists():
            path.unlink()
            removed += 1

    # Research
    research = base / "research" / f"{slug}-knowledge-packet.md"
    if research.exists():
        research.unlink()
        removed += 1

    # Orchestration artifacts (keep index.md and friction.yaml)
    if orch.exists():
        keep = {"index.md", "friction.yaml"}
        for f in orch.iterdir():
            if f.name in keep:
                continue
            if f.is_dir():
                shutil.rmtree(f)
                removed += 1
            else:
                f.unlink()
                removed += 1

    if removed > 0:
        _log(f"  🧹 Cleaned {removed} previous build artifact(s)")


def _log(msg: str):
    print(msg, flush=True)


def emit_event(event: str, **fields):
    line = json.dumps(
        {"event": event, "ts": datetime.now(UTC).isoformat(), **fields},
        ensure_ascii=False,
        default=str,
    )
    print(line, flush=True)


def _save_v6_state(level: str, slug: str, step: str, status: str = "complete"):
    """Write V6 pipeline state in V5-compatible format."""
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


# All phases in pipeline order (used by --resume).
#
# Also exported as ``PHASES`` for out-of-process consumers that need the
# canonical v6 phase list — specifically the monitor API's state_helpers
# module, which used to import from the retired pipeline_v5 module. Do
# NOT delete either alias — ``_ALL_PHASES`` is referenced locally by the
# many resume/state helpers throughout this file, while ``PHASES`` is the
# stable public name. They must stay in sync (which is free — they're
# the same list object).
_ALL_PHASES = [
    "check", "research", "skeleton", "pre-verify", "write",
    "exercises", "activities", "repair", "verify-exercises", "annotate",
    "vocab", "enrich", "verify", "review", "stress", "publish", "audit",
]
PHASES = _ALL_PHASES
_PHASE_SATISFIED_STATUSES = {"complete", "skipped"}

# Human-friendly labels for the v6 phases. Exposed alongside ``PHASES``
# for API consumers that want to render a phase name in a UI. Keys match
# ``PHASES`` exactly; any phase without an explicit label falls back to
# its kebab-case id via ``PHASE_LABELS.get(name, name)``.
PHASE_LABELS: dict[str, str] = {
    "check": "Plan check",
    "research": "Research",
    "skeleton": "Skeleton",
    "pre-verify": "Pre-verify",
    "write": "Write content",
    "exercises": "Exercises",
    "activities": "Activities",
    "repair": "Repair",
    "verify-exercises": "Verify exercises",
    "annotate": "Annotate",
    "vocab": "Vocabulary",
    "enrich": "Enrich",
    "verify": "Verify content",
    "review": "Review",
    "stress": "Stress marks",
    "publish": "Publish MDX",
    "audit": "Audit",
}

_PRE_BUILD_GATE_STEPS = {
    "all",
    "research",
    "pre-verify",
    "skeleton",
    "write",
    "activities",
    "review",
    "publish",
}


def _invalidate_phases(level: str, slug: str, phases_to_clear: list[str]) -> None:
    """Mark downstream phases as incomplete so --resume re-runs them.

    Used when an earlier step mutates artifacts (e.g., repair regenerates
    activities) and downstream work (publish, audit) is now stale.
    """
    import json

    state_path = CURRICULUM_ROOT / level / "orchestration" / slug / "state.json"
    if not state_path.exists():
        return
    try:
        state = json.loads(state_path.read_text())
    except Exception:
        return
    phases = state.get("phases", {})
    touched = False
    for name in phases_to_clear:
        if name in phases:
            phases.pop(name)
            touched = True
    if touched:
        state["phases"] = phases
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def _load_completed_phases(level: str, slug: str) -> set[str]:
    """Read state.json and return phase names satisfied for resume/skip logic."""
    import json

    state_path = CURRICULUM_ROOT / level / "orchestration" / slug / "state.json"
    if not state_path.exists():
        return set()
    try:
        state = json.loads(state_path.read_text())
    except Exception:
        return set()
    phases = state.get("phases", {})
    return {
        name for name, info in phases.items()
        if info.get("status") in _PHASE_SATISFIED_STATUSES
    }


def _all_phases_complete(level: str, slug: str) -> bool:
    """Check if all pipeline phases are complete for a module."""
    completed = _load_completed_phases(level, slug)
    return all(p in completed for p in _ALL_PHASES)


def _run_pre_build_gate(level: str, slug: str) -> bool:
    """Validate plan readiness before any step that consumes plan data."""
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        _log(f"  ❌ Plan not found: {plan_path}")
        return False

    plan_data = yaml.safe_load(plan_path.read_text("utf-8")) or {}
    outline = plan_data.get("content_outline") or []

    # 1. Summary section required
    has_summary = any(
        "summary" in s.get("section", "").lower() or "підсумок" in s.get("section", "").lower()
        for s in outline if isinstance(s, dict)
    )
    if not has_summary:
        _log("  ❌ PRE-BUILD GATE: Plan missing Summary/Підсумок section in content_outline")
        _log("     Fix: .venv/bin/python scripts/tools/fix_plans_phase1.py " + level)
        return False

    # 2. Vocabulary baseline required
    has_vocab = bool(plan_data.get("vocabulary_hints") or plan_data.get("vocabulary"))
    if not has_vocab:
        _log("  ⚠️  PRE-BUILD GATE: No vocabulary_hints or vocabulary in plan (non-blocking)")

    # 3. Word target sanity (required and positive before config comparison)
    plan_wt = plan_data.get("word_target")
    if isinstance(plan_wt, bool) or not isinstance(plan_wt, (int, float)):
        _log("  ❌ PRE-BUILD GATE: word_target missing or non-numeric")
        return False
    if plan_wt <= 0:
        _log("  ❌ PRE-BUILD GATE: word_target must be greater than zero")
        return False

    from validate.validate_plan_config import get_config_target
    config_wt = get_config_target(
        level,
        plan_data.get("sequence", 1),
        plan_data.get("focus"),
        slug=slug,
    )
    if plan_wt and plan_wt < config_wt * 0.95:
        _log(f"  ❌ PRE-BUILD GATE: word_target ({plan_wt}) below config minimum ({config_wt})")
        return False

    _log("  ✅ Pre-build readiness gate passed")
    return True


def _parse_review_result(review_text: str) -> ReviewParseResult:
    """Parse the deterministic score/verdict gates from a review markdown file."""
    # Dimension weights (must match v6-review.md)
    dimension_weights = {
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

    # Gemini sometimes outputs the score table twice. Only take the first 9.
    score_pattern = re.compile(r"\|\s*\d+\.\s*[^|]+\|\s*(\d+)/10\s*\|")
    all_raw_scores = [int(m.group(1)) for m in score_pattern.finditer(review_text)]
    raw_scores = all_raw_scores[:len(dimension_weights)]

    full_score_pattern = re.compile(r"\|\s*(\d+)\.\s*([^|]+)\|\s*(\d+)/10\s*\|([^|]*)\|")
    parsed_scores = []
    seen_dims: set[int] = set()
    for m in full_score_pattern.finditer(review_text):
        dim_num = int(m.group(1))
        if dim_num in seen_dims:
            continue
        seen_dims.add(dim_num)
        parsed_scores.append({
            "dimension": dim_num,
            "name": m.group(2).strip(),
            "score": int(m.group(3)),
            "evidence": m.group(4).strip(),
        })

    if raw_scores:
        available = min(len(raw_scores), len(dimension_weights))
        used_weights = {k: v for k, v in dimension_weights.items() if k <= available}
        weight_sum = sum(used_weights.values())
        weighted = sum(
            raw_scores[i] * dimension_weights.get(i + 1, 0)
            for i in range(available)
        )
        score = round(weighted / weight_sum, 1) if weight_sum > 0 else 0.0
    else:
        score = 0.0

    verdict = "UNKNOWN"
    for value in ("PASS", "REVISE", "REJECT"):
        if f"Verdict: {value}" in review_text or f"Verdict:{value}" in review_text:
            verdict = value
            break

    dim_floor_fail = False
    if parsed_scores:
        error_keywords = (
            "error", "incorrect", "wrong", "mistake", "factual",
            "помилк", "невірн", "хибн", "contradictory",
        )
        for dim in parsed_scores:
            dim_score = dim.get("score", 10)
            evidence = dim.get("evidence", "").lower()
            if dim_score < REVIEW_TARGET_SCORE and any(kw in evidence for kw in error_keywords):
                dim_floor_fail = True
                break

    passed = score >= 8.0 and verdict == "PASS" and not dim_floor_fail
    return ReviewParseResult(
        score=score,
        verdict=verdict,
        raw_scores=raw_scores,
        parsed_scores=parsed_scores,
        dim_floor_fail=dim_floor_fail,
        passed=passed,
    )


def _load_latest_review_result(level: str, slug: str) -> ReviewParseResult | None:
    """Parse the latest saved review for a module, if present."""
    review_dir = CURRICULUM_ROOT / level / "review"
    review_path = review_dir / f"{slug}-review.md"
    if not review_path.exists() and review_dir.exists():
        versioned = sorted(review_dir.glob(f"{slug}-review-r*.md"))
        if versioned:
            review_path = versioned[-1]
    if not review_path.exists():
        return None
    try:
        return _parse_review_result(review_path.read_text("utf-8"))
    except Exception:
        return None


def _audit_code_latest_mtime() -> float:
    """Return the latest mtime across scripts/audit/**/*.py.

    Used to detect when the audit engine itself has been updated since
    the last time a module's status.json was written. If yes, the stale
    status is not trustworthy — we must re-audit before deciding to skip.

    Cached at module load time via functools.lru_cache wrapping is
    deliberately avoided here: we want fresh values during long-running
    --range batches where a hot-patched audit file MIGHT legitimately
    exist. The scan is ~20 files and takes <5ms.
    """
    audit_dir = Path(__file__).resolve().parent.parent / "audit"
    if not audit_dir.exists():
        return 0.0
    latest = 0.0
    for py in audit_dir.rglob("*.py"):
        try:
            m = py.stat().st_mtime
            if m > latest:
                latest = m
        except OSError:
            continue
    return latest


def _is_status_stale(status_path: Path, content_path: Path) -> tuple[bool, str]:
    """Check whether a status.json cache is too old to trust.

    Stale if ANY of:
      - status.json does not exist
      - content.md mtime > status.json mtime (content was edited)
      - scripts/audit/*.py latest mtime > status.json mtime (audit engine
        was updated — previously-passing modules may now fail new checks,
        e.g. the salad detector wired in on 2026-04-10)

    Returns (is_stale, reason). Reason is empty when not stale.
    """
    if not status_path.exists():
        return True, "no status file"
    try:
        status_mtime = status_path.stat().st_mtime
    except OSError as exc:
        return True, f"status file unreadable: {exc}"

    if content_path.exists():
        try:
            content_mtime = content_path.stat().st_mtime
            if content_mtime > status_mtime + 1:  # 1s fudge for fs precision
                return True, "content edited since last audit"
        except OSError:
            pass  # tolerate — fall through to audit-code check

    audit_mtime = _audit_code_latest_mtime()
    if audit_mtime > status_mtime + 1:
        return True, "audit engine updated since last audit"

    return False, ""


def _should_skip_batch_module(level: str, slug: str, step: str,
                              review_threshold: float) -> tuple[bool, str]:
    """Decide whether batch mode should skip a module for the requested step.

    Skip policy — a module is ONLY skipped when ALL of these are true:

      - All required pipeline phases complete (every phase for non-review
        steps; the `review` phase only when `--step review`)
      - Status cache is FRESH (content + audit engine both older than
        status.json — otherwise re-audit before trusting it)
      - Audit overall == "pass" AND every tracked gate has status "pass"
        (gates in "info"/"pending" state are treated as unverified →
        re-run, never skip)
      - Latest review score ≥ review_threshold (default 9.0)

    Design intent: the skip logic is the LAST line of defense against
    shipping broken modules. Err on the side of re-running. User rule
    (2026-04-10): "never skip if audit not passing or review below 9."

    Bug fix 2026-04-11: the `--step review` branch used to short-circuit
    on review-score-only and ignore the audit. That let modules with
    failing immersion / density gates skip the heal pipeline because
    their old review still scored 9+. The audit-gate check is now
    enforced for every step, including review.
    """
    if step == "review":
        completed = _load_completed_phases(level, slug)
        if "review" not in completed:
            return False, "review not complete yet"
    elif not _all_phases_complete(level, slug):
        return False, "module incomplete"

    status_path = CURRICULUM_ROOT / level / "status" / f"{slug}.json"
    content_path = CURRICULUM_ROOT / level / f"{slug}.md"

    # Staleness check — stale cache = untrustworthy, force re-run.
    stale, stale_reason = _is_status_stale(status_path, content_path)
    if stale:
        return False, f"audit cache stale ({stale_reason})"

    # Parse the (fresh) status file
    try:
        import json
        status = json.loads(status_path.read_text("utf-8"))
    except Exception as e:
        return False, f"audit status unreadable: {e}"

    overall = status.get("overall", {}).get("status", "unknown")

    # Strict pass requirement: only `pass` counts. "content-complete" has
    # deferred gates BY DESIGN, which means something is not done yet —
    # so it's not skippable. User rule: never skip unless audit is truly
    # passing.
    if overall != "pass":
        failed_gates = [
            k for k, v in (status.get("gates") or {}).items()
            if isinstance(v, dict) and v.get("status") == "fail"
        ]
        reason = f"audit {overall}"
        if failed_gates:
            reason += f" (failed: {', '.join(failed_gates)})"
        return False, reason

    # Even when overall == "pass", any gate that isn't strictly "pass"
    # (e.g. "info"/"pending"/"deferred") is unverified and should force
    # a re-run. Naturalness="info" was the specific bug — it left the
    # overall at pass even though naturalness had never been scored.
    gates_dict = status.get("gates") or {}
    unverified_gates = [
        k for k, v in gates_dict.items()
        if isinstance(v, dict) and v.get("status") not in ("pass",)
    ]
    if unverified_gates:
        return False, f"unverified gates: {', '.join(unverified_gates)}"

    # Review score must meet the hard threshold.
    latest_review = _load_latest_review_result(level, slug)
    if latest_review is None:
        return False, "no saved review found"
    if latest_review.score < review_threshold:
        return False, f"latest review {latest_review.score}/10 < {review_threshold:.1f}"

    return True, (
        f"phases complete + audit pass + all gates pass + "
        f"review {latest_review.score}/10 >= {review_threshold:.1f}"
    )


def step_check(level: str, module_num: int, slug: str) -> bool:
    """Step 2: Run deterministic plan checker with auto-fix for Russicisms and VESUM failures."""
    _log(f"\n{'='*60}")
    _log("  Step 2: CHECK — Plan validation")
    _log(f"{'='*60}")

    from audit.check_plan import check_plan
    from tools.plan_autofix import auto_fix_plan, fix_russianisms_in_plan

    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        _log(f"  ❌ Plan not found: {plan_path}")
        return False

    # Load all slugs for prerequisite checking
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    all_slugs = data.get("levels", {}).get(level, {}).get("modules", [])

    # --- Pre-build readiness gate (Phase 3 of recovery plan, 2026-04-13) ---
    if not _run_pre_build_gate(level, slug):
        return False

    issues = check_plan(plan_path, all_slugs)

    # --- Auto-fix: Russicisms ---
    russicism_issues = [i for i in issues if i.check == "RUSSICISM"]
    if russicism_issues:
        # Convert PlanIssue objects to dicts expected by fix_russianisms_in_plan
        russicism_dicts = [
            {"issue_type": "RUSSICISM", "problem": i.message, "suggested_fix": i.fix}
            for i in russicism_issues
        ]
        n_fixed, changelog = fix_russianisms_in_plan(plan_path, russicism_dicts)
        if n_fixed > 0:
            # Re-read plan version after fix
            plan_data = yaml.safe_load(plan_path.read_text("utf-8"))
            new_version = plan_data.get("version", "?")
            _log(f"  ⚠️ Plan auto-fixed: {n_fixed} Russicism(s) corrected, version bumped to {new_version}")
            for entry in changelog:
                _log(f"    {entry}")

    # --- Auto-fix: VESUM vocabulary failures ---
    vesum_issues = [i for i in issues if i.check == "VESUM"]
    if vesum_issues:
        # Convert PlanIssue objects to dicts expected by auto_fix_plan
        # Extract word from message like "Vocabulary word 'X' not found in VESUM"
        vesum_not_found = []
        for vi in vesum_issues:
            match = re.search(r"'([^']+)'", vi.message)
            if match:
                vesum_not_found.append({"original": match.group(1), "status": "❌"})
        if vesum_not_found:
            n_fixed, changelog = auto_fix_plan(plan_path, vesum_not_found=vesum_not_found)
            if n_fixed > 0:
                plan_data = yaml.safe_load(plan_path.read_text("utf-8"))
                new_version = plan_data.get("version", "?")
                _log(f"  ⚠️ Plan auto-fixed: {n_fixed} VESUM-failed word(s) removed, version bumped to {new_version}")
                for entry in changelog:
                    _log(f"    {entry}")

    # --- Re-check after auto-fixes ---
    if russicism_issues or vesum_issues:
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


_SEMINAR_TRACKS = {"hist", "bio", "istorio", "lit", "folk", "oes", "ruth"}

def _resolve_persona(level: str, plan: dict | None = None) -> tuple[str, str]:
    """Resolve persona (voice, role) for a level/track. Plan persona overrides fallback.

    Source of truth: pipeline.config_tables.TRACK_PERSONAS
    """
    from pipeline.config_tables import DEFAULT_PERSONA, TRACK_PERSONAS

    if plan:
        persona = plan.get("persona", {})
        if isinstance(persona, dict) and persona.get("voice"):
            return persona["voice"], persona.get("role", "")

    level_lower = level.lower()
    if level_lower in TRACK_PERSONAS:
        return TRACK_PERSONAS[level_lower]
    base = level_lower.split("-")[0]
    if base in TRACK_PERSONAS:
        return TRACK_PERSONAS[base]
    return DEFAULT_PERSONA


def _get_persona_description(level: str, plan: dict | None = None) -> str:
    """Get a one-line persona description for chunk prompts."""
    voice, role = _resolve_persona(level, plan)
    desc = voice.lower()
    if not desc.startswith(("a ", "an ", "the ")):
        first_char = desc[0] if desc else ""
        article = "an" if first_char in "aeiou" else "a"
        desc = f"{article} {desc}"
    if role:
        desc += f" ({role})"
    return desc


def _is_seminar_track(level: str) -> bool:
    """Check if a level/track is a seminar track."""
    return level.lower() in _SEMINAR_TRACKS or level.lower().startswith("lit-")


def step_research(level: str, module_num: int, slug: str) -> Path | None:
    """Step 3: Build knowledge packet from wiki + discovery data.

    All tracks (core and seminar) use wiki articles as the primary knowledge
    source.  RAG textbook search is no longer used — the wiki compiler already
    distils textbook + literary + Wikipedia sources into verified articles.
    """
    _log(f"\n{'='*60}")
    _log("  Step 3: RESEARCH — Knowledge packet")
    _log(f"{'='*60}")

    output_dir = CURRICULUM_ROOT / level / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}-knowledge-packet.md"

    # All tracks use wiki-based packets (wiki articles + discovery + plan refs)
    packet = _build_wiki_packet(level, slug)

    output_path.write_text(packet, "utf-8")
    word_count = len(packet.split())
    _log(f"  ✅ Knowledge packet built ({word_count} words)")
    _log(f"  → {output_path}")

    return output_path


def _build_wiki_packet(level: str, slug: str) -> str:
    """Build knowledge packet from wiki articles + discovery data + plan refs.

    Wiki articles are compiled from primary sources (textbooks, literary texts,
    Wikipedia) — they're curated, structured, and verified.  Used for ALL tracks.
    """
    import yaml as _yaml

    lines = []
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan = _yaml.safe_load(plan_path.read_text("utf-8")) if plan_path.exists() else {}
    title = plan.get("title", slug)

    lines.append(f"# Knowledge Packet: {title}")
    lines.append(f"**Module:** {slug} | **Track:** {level.upper()}")
    lines.append("")

    # 1. Wiki articles (primary source — compiled knowledge)
    wiki_content = ""
    try:
        from wiki.context import get_wiki_context
        wiki_content = get_wiki_context(level, slug)
    except Exception as exc:
        _log(f"  ⚠️  Wiki unavailable: {exc}")

    if wiki_content:
        _log(f"  📚 Wiki context loaded ({len(wiki_content):,} chars)")
        lines.append(wiki_content)
        lines.append("")
    else:
        _log("  ℹ️  No wiki articles for this module — using discovery data only")

    # 2. Discovery data (RAG refs collected during discovery phase)
    discovery_path = CURRICULUM_ROOT / level / "discovery" / f"{slug}.yaml"
    if discovery_path.exists():
        discovery = _yaml.safe_load(discovery_path.read_text("utf-8")) or {}

        # Literary source snippets from discovery
        literary = discovery.get("rag_literary", [])
        if literary:
            lines.append("## Literary Sources (from discovery)")
            lines.append("")
            for chunk in literary[:10]:  # Cap at 10 to avoid bloat
                text = chunk.get("text", "").strip()
                if text and len(text) > 50:
                    chunk_id = chunk.get("chunk_id", "unknown")
                    score = chunk.get("score", 0)
                    lines.append(f"> **Source:** `{chunk_id}` (relevance: {score:.1f})")
                    lines.append(f"> {text[:500]}")
                    lines.append("")

        # Textbook chunks from discovery
        textbook = discovery.get("rag_chunks", [])
        if textbook:
            lines.append("## Textbook Excerpts (from discovery)")
            lines.append("")
            for chunk in textbook[:8]:
                text = chunk.get("text", "").strip()
                if text and len(text) > 50:
                    chunk_id = chunk.get("chunk_id", "unknown")
                    grade = chunk.get("grade", "?")
                    section = chunk.get("section_title", "")
                    lines.append(f"> **Source:** `{chunk_id}` | Grade {grade} | {section}")
                    lines.append(f"> {text[:500]}")
                    lines.append("")

    # 3. References from plan (if any)
    references = plan.get("references", [])
    if references:
        lines.append("## Plan References")
        lines.append("")
        for ref in references:
            if isinstance(ref, dict):
                ref_type = ref.get("type", "")
                author = ref.get("author", "")
                work = ref.get("work", "")
                note = ref.get("note", "")
                path = ref.get("path", "")
                parts = [p for p in [ref_type, author, work, note, path] if p]
                lines.append(f"- {' | '.join(parts)}")
            else:
                lines.append(f"- {ref}")
        lines.append("")

    return "\n".join(lines)


def step_pre_verify(level: str, module_num: int, slug: str,
                    writer: str = "claude-tools") -> str | None:
    """Step 3b: Pre-write verification — force MCP tool calls before writing.

    Dispatches a short, focused prompt that REQUIRES the LLM to call tools:
    - verify_words on all plan vocabulary
    - search_text for each section topic
    - query_pravopys for grammar rules
    - search_style_guide for calque detection
    - query_cefr_level for vocabulary level check

    Returns the verification results text, or None on failure.
    The results are injected into the write prompt so the writer has
    pre-verified facts — no need to call tools during writing.

    Issue: #1070
    """
    _log(f"\n{'='*60}")
    _log(f"  Step 3b: PRE-VERIFY — Tool-forced fact checking ({writer})")
    _log(f"{'='*60}")

    # Load template
    template_path = PHASES_DIR / "v6-pre-verify.md"
    if not template_path.exists():
        _log(f"  ❌ Template not found: {template_path}")
        return None

    template = template_path.read_text("utf-8")

    # Load plan
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        _log(f"  ❌ Plan not found: {plan_path}")
        return None

    plan = yaml.safe_load(plan_path.read_text("utf-8"))

    # Build vocabulary list for verification (guard against None YAML values)
    # v4 plans: list of {word, pos, definition} dicts
    # v3 plans: dict with {required: [...], recommended: [...]}
    # Accept both 'vocabulary_hints' (B1 convention) and 'vocabulary' (B2/C1
    # convention). The pipeline historically only read vocabulary_hints, which
    # meant B2 (68/93) and C1 (133/133) plans got zero vocabulary injected.
    vocab_hints = plan.get("vocabulary_hints") or plan.get("vocabulary") or {}
    if isinstance(vocab_hints, list):
        # v4 format: flat list of dicts or strings
        all_vocab = [
            v.get("word", str(v)) if isinstance(v, dict) else str(v)
            for v in vocab_hints
        ]
    elif isinstance(vocab_hints, dict):
        # v3 format: {required: [...], recommended: [...]}
        required = vocab_hints.get("required") or []
        recommended = vocab_hints.get("recommended") or []
        all_vocab = required + recommended
    else:
        all_vocab = []
    vocab_text = "\n".join(f"- {item}" for item in all_vocab) if all_vocab else "(No vocabulary hints in plan)"

    # Build section queries from content_outline (guard against None/malformed)
    sections = plan.get("content_outline") or []
    section_queries = []
    for s in sections:
        if not isinstance(s, dict):
            continue
        title = s.get("section") or ""
        points = s.get("points") or []
        points_text = "; ".join(str(p) for p in points[:3]) if points else ""
        section_queries.append(f"- **{title}**: {points_text}")
    queries_text = "\n".join(section_queries) if section_queries else "(No content outline)"

    # Fill template
    phase = str(plan.get("phase") or "")
    replacements = {
        "{MODULE_NUM}": str(module_num),
        "{TOPIC_TITLE}": plan.get("title", slug),
        "{LEVEL}": level.upper(),
        "{PHASE}": phase,
        "{PLAN_VOCABULARY}": vocab_text,
        "{SECTION_QUERIES}": queries_text,
    }
    prompt = template
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Save prompt for inspection
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = orch_dir / "v6-pre-verify-prompt.md"
    prompt_path.write_text(prompt, "utf-8")
    _log(f"  Prompt saved → {prompt_path.name} ({len(prompt)} chars)")

    # Dispatch — MUST use tools mode. Short prompt (~3-5K chars) encourages tool use.
    from build.dispatch import CLAUDE_WRITER_TOOLS
    from build.dispatch import dispatch_agent as _dispatch

    family = get_family(writer)
    agent = f"{family.name}-tools"
    # Codex uses shell commands for verification — no MCP tools needed.
    use_mcp = family.name != "codex"

    ok, raw = _dispatch(
        prompt, agent=agent, phase="pre-verify", orch_dir=orch_dir,
        timeout=TIMEOUT_PRE_VERIFY,
        mcp_tools=use_mcp,
        allowed_tools=CLAUDE_WRITER_TOOLS if family.name == "claude" else None,
        model=family.fast,  # Fast model sufficient — structured output, not creative
    )

    # Retry once on timeout — pre-verify is critical for grounding the writer
    if not ok or not raw:
        _log("  ⚠️  Pre-verify failed — retrying once")
        ok, raw = _dispatch(
            prompt, agent=agent, phase="pre-verify-retry", orch_dir=orch_dir,
            timeout=TIMEOUT_PRE_VERIFY,
            mcp_tools=use_mcp,
            allowed_tools=CLAUDE_WRITER_TOOLS if family.name == "claude" else None,
            model=family.fast,
        )

    if not ok or not raw:
        _log("  ❌ Pre-verify returned no output after retry")
        return None

    # Extract <verification> block
    verify_match = re.search(r"<verification>(.*?)</verification>", raw, re.DOTALL)
    if verify_match:
        verification_text = verify_match.group(1).strip()
    else:
        verification_text = raw.strip()
        _log("  ⚠️  No <verification> tags found — using full output")

    # Save verification results
    verify_path = orch_dir / "pre-verify-results.md"
    verify_path.write_text(verification_text, "utf-8")

    # Count tool usage indicators in the output
    tool_indicators = sum(1 for kw in ["VESUM", "Правопис", "textbook", "calque", "CEFR", "NOT FOUND", "Confirmed"]
                         if kw.lower() in verification_text.lower())
    _log(f"  ✅ Pre-verification complete ({len(verification_text)} chars, {tool_indicators} verification indicators)")
    _log(f"  → {verify_path}")

    _save_v6_state(level, slug, "pre-verify")
    return verification_text


def step_skeleton(level: str, module_num: int, slug: str,
                  packet_path: Path | None, writer: str = "gemini") -> str | None:
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
        if len(packet) > 30_000:
            packet = packet[:30_000] + "\n\n... (truncated for context window)"

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

    # Dispatch to writer — skeleton is structure planning, fast model sufficient
    from build.dispatch import dispatch_agent as _dispatch

    family = get_family(writer)
    ok, raw = _dispatch(
        prompt, agent=family.name, phase="skeleton", orch_dir=orch_dir, timeout=TIMEOUT_SKELETON,
        model=family.fast,
    )

    if not ok or not raw:
        _log("  ❌ Writer returned no skeleton output")
        return None

    # Extract skeleton from <skeleton> tags
    skeleton_match = re.search(r"<skeleton>(.*?)</skeleton>", raw, re.DOTALL)
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


def _parse_skeleton_sections(skeleton: str) -> list[dict]:
    """Parse skeleton text into H2 sections with word budgets.

    Each section dict has:
      - title: str (the H2 heading text, e.g. "Мене звати... (My name is...)")
      - body: str (the full skeleton text for that section)
      - words: int (word budget from the (~XXX words total) annotation, or 0)

    Returns empty list if skeleton has fewer than 2 H2 sections.
    """
    lines = skeleton.split("\n")
    sections: list[dict] = []
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            # Save previous section
            if current_title:
                sections.append({
                    "title": current_title,
                    "body": "\n".join(current_lines).strip(),
                    "words": _extract_word_budget(current_title),
                })
            current_title = line[3:].strip()
            current_lines = [line]
        elif current_title:
            current_lines.append(line)

    # Save last section
    if current_title:
        sections.append({
            "title": current_title,
            "body": "\n".join(current_lines).strip(),
            "words": _extract_word_budget(current_title),
        })

    return sections


def _extract_word_budget(title: str) -> int:
    """Extract word budget from skeleton heading like '## Title (~275 words total)'."""
    m = re.search(r"~(\d+)\s*words", title)
    return int(m.group(1)) if m else 0


def _build_section_summary(sections_so_far: list[str], max_words: int = 500) -> str:
    """Build a rolling summary of previously written sections for context handoff.

    Keeps the summary under max_words by taking the last N sections that fit.
    """
    if not sections_so_far:
        return ""

    combined = "\n\n".join(sections_so_far)
    words = combined.split()
    if len(words) <= max_words:
        return combined

    # Take from the end (most recent context is most relevant)
    truncated = " ".join(words[-max_words:])
    return f"[...previous sections truncated...]\n\n{truncated}"


# --- B1 friction fixes (#1189) ---------------------------------------------
# These constants/helpers feed _build_chunk_prompt() with the late-prompt
# vocab checklist + Russianism blocklist that were missing from the chunked
# write path. The non-chunked write path uses the same content via
# v6-write.md template substitution. Both paths must stay in sync.

_CHUNK_FORBIDDEN_WORDS_BLOCK = """## FORBIDDEN WORDS — never produce (#1189)

Never write any of these even once. Even in dialogues. Even in quoted examples. Even when illustrating a learner's mistake (use a `<!-- VERIFY -->` placeholder instead). The post-write toxic-token scanner halts the build the moment it sees one:

❌ хорошо ❌ конечно ❌ спасибо ❌ пожалуйста ❌ ничего ❌ сейчас ❌ тоже ❌ здесь ❌ кот ❌ кон

Use: добре · звичайно · дякую · будь ласка · нічого · зараз · теж · тут · кіт · кін

No ы, э, ё, ъ characters anywhere."""


def _chunk_required_vocab_block(plan: dict, section_index: int, total_sections: int) -> str:
    """Render the required-vocab checklist for a chunked section prompt.

    Pattern B (#1189) — writers were dropping abstract grammatical metalanguage
    (видова пара, дієвідміна, особове закінчення, прагматика, etc.) from the
    final B1 modules. The chunked path didn't surface these as a checklist;
    each section saw the full plan but no end-of-prompt reminder. We now
    inject a markdown checkbox list near the end of every section's prompt
    where Gemini's attention is highest, and on the FINAL section we add a
    sweep-up reminder so any vocab that didn't fit earlier gets included.
    """
    raw = plan.get("vocabulary_hints") or plan.get("vocabulary") or {}
    words: list[str] = []
    if isinstance(raw, list):
        words = [v.get("word", str(v)) if isinstance(v, dict) else str(v) for v in raw]
    elif isinstance(raw, dict):
        words = [str(w) for w in (raw.get("required") or [])]
    if not words:
        return ""

    checklist = "\n".join(f"- [ ] {w}" for w in words)
    is_final = section_index + 1 >= total_sections
    if is_final:
        instruction = (
            f"**This is the FINAL section ({total_sections}/{total_sections}).** "
            "Before you stop writing, review the prose you've written across "
            "this whole module. EVERY word in the checklist below MUST appear "
            "at least once with a bold Ukrainian form and English translation "
            "in a natural sentence. Sweep up any words that earlier sections "
            "did not include — even if it means adding a sentence or short "
            "paragraph that defines the term. Abstract grammatical metalanguage "
            "(видова пара, дієвідміна, особове закінчення, etc.) is the most "
            "frequently dropped category and the build hard-fails for it."
        )
    else:
        instruction = (
            "**Required module vocabulary** — every word below MUST appear "
            "somewhere in the module before it ends. If a word fits naturally "
            "in this section, include it now (bold + English translation). "
            "Otherwise leave it for a later section. The FINAL section will "
            "sweep up any unused words, but the more you place naturally now "
            "the better the prose flows."
        )

    return f"## REQUIRED VOCABULARY CHECKLIST (#1189)\n\n{instruction}\n\n{checklist}"


def _build_chunk_prompt(
    *,
    template: str,
    section: dict,
    section_index: int,
    total_sections: int,
    previous_summary: str,
    plan_content: str,
    packet: str,
    level: str,
    module_num: int,
    plan: dict,
    slug: str,
) -> str:
    """Build prompt for a single section chunk.

    Includes the section plan from skeleton, rolling summary of previous
    sections, and the research packet. Uses a streamlined prompt that
    focuses the writer on one section at a time.
    """
    from pipeline.config_tables import (
        get_immersion_rule,
        get_level_constraints,
        get_pedagogical_constraints,
    )

    word_target = section["words"] or 300  # fallback if no budget in skeleton
    phase = plan.get("phase", "")

    # Resolve persona from the SAME source as the single-call path (get_persona)
    persona_desc = _get_persona_description(level, plan)

    is_seminar = _is_seminar_track(level)
    lang_directive = " Весь контент пишеться **українською мовою**." if is_seminar else ""

    section_prompt = f"""# Section-by-Section Generation — Section {section_index + 1}/{total_sections}

You are {persona_desc}, writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else.{lang_directive}

**Module:** {module_num}: {plan.get("title", slug)} ({level.upper()}, {phase})
**Section to write:** {section["title"]}
**Word target for this section:** {word_target} words (aim for {int(word_target * 1.1)} to account for undershoot)

---

## Section Skeleton (follow this exactly)

{section["body"]}

---
"""

    if previous_summary:
        section_prompt += f"""## Previous Sections (for continuity — do NOT repeat this content)

<previous_context>
{previous_summary}
</previous_context>

Continue naturally from where the previous section ended. Do not re-introduce concepts already covered.

---
"""

    # Add plan for reference (trimmed to content_outline for this section)
    # Resolve language-salad phase placeholders (#1185)
    _salad_vars = _build_salad_phase_placeholders(level, module_num)
    _salad_phase_num = _salad_vars["{SALAD_PHASE_NUMBER}"]
    _salad_phase_name = _salad_vars["{SALAD_PHASE_NAME}"]
    _salad_uk_allowed = _salad_vars["{SALAD_UK_PARAGRAPHS_ALLOWED}"]
    _salad_min_sent = _salad_vars["{SALAD_MIN_SENTENCES}"]
    _salad_max_sent = _salad_vars["{SALAD_MAX_SENTENCES}"]
    _salad_xlat_pct = _salad_vars["{SALAD_TRANSLATION_PCT}"]

    section_prompt += f"""## Full Plan (for reference)

<plan_content>
{plan_content}
</plan_content>

---

## Knowledge Packet

<knowledge_packet>
{packet}
</knowledge_packet>

---

{{WIKI_CHUNK_CONTEXT}}

## CRITICAL: PARAGRAPH LANGUAGE RULE (#1185 — hard gate, audited automatically)

**You are in PHASE {_salad_phase_num}: {_salad_phase_name}**
- Ukrainian prose paragraphs: {_salad_uk_allowed}
- Paragraph length: {_salad_min_sent}–{_salad_max_sent} sentences
- Frequency of Ukrainian paragraphs that get an English translation block: {_salad_xlat_pct}%

**THE RULE (hard, non-negotiable):**

Each prose paragraph is MONOLINGUAL. A paragraph is either entirely English
OR entirely Ukrainian. NEVER mix English and Ukrainian sentences inside the
same paragraph. NEVER write sentence-by-sentence translation inside a paragraph.

A Ukrainian paragraph may be followed by its **full** English translation
in a blockquote + italics:

```
Називний відмінок — це основна форма слова, яка відповідає на питання
«хто?» або «що?». Ти завжди вчиш нове слово саме в цій формі.

> *The Nominative case is the dictionary form, which answers the questions
> "who?" or "what?". You always learn a new word in this form.*
```

The blockquote translates the WHOLE Ukrainian paragraph, not individual
sentences.

**FORBIDDEN patterns — the audit will REJECT the module for any of these:**

1. English prose with inline bolded UK terms + parenthetical translations:
   ❌ `The **Називний відмінок** (Nominative case) is the dictionary form. It answers **хто?** (who?) and **що?** (what?).`
   (This is the "inline-gloss salad" pattern. It violates monolingual paragraphs.)

2. More than 3 bolded vocabulary glosses `**term** (gloss)` in a single paragraph.

3. Sentence-by-sentence mixing:
   ❌ `Я читаю книгу. I am reading a book. Вона п'є каву. She is drinking coffee.`

4. Writing the whole module in English with Ukrainian only appearing as
   inline examples (at A1 M15+, A2, B1+ you MUST write Ukrainian prose
   paragraphs — {_salad_xlat_pct}% with translation blocks, the rest bare).

**ALLOWED patterns:**

- Isolated Ukrainian example sentences with tight gloss (grammar illustration):
  ✅ `For masculine nouns, use the **-ий** ending.`
     `**Гарний хлопчик.** — *A handsome boy.*`

- Inline bolded vocabulary tooltips (up to 3 per paragraph):
  ✅ `The word for cat is **кіт** (cat).`

- Dialogs with per-speaker-turn inline translations (dialogs are EXEMPT from
  the monolingual rule — see the dialog format below).

**How to structure a section when Ukrainian paragraphs are allowed:**

1. Open with an English explanation paragraph introducing the concept
2. Write a Ukrainian paragraph demonstrating the concept in use
3. Follow with a blockquote `> *English translation of the whole paragraph*`
4. Write another English explanation or analysis
5. Write another Ukrainian paragraph (translated or bare per the frequency target)

Before submitting, re-read each paragraph and verify: "Is every sentence
in this paragraph the same language?" If no, fix it.

---

## Other Rules

{get_immersion_rule(level, module_num)}

{get_level_constraints(level, plan)}

{get_pedagogical_constraints(level, module_num, plan)}

- **Engagement callouts are REQUIRED.** Every section MUST contain at
  least one callout box. The module as a whole MUST have ≥3 callouts,
  so with 4-5 sections you're naturally covered. Use the supported
  markers:
  ```
  :::note
  **Quick tip** — short explanation or memory aid (1-3 sentences).
  :::

  :::tip
  **Did you know?** — cultural or linguistic insight.
  :::

  :::info
  **Grammar box** — a focused explanation of one rule.
  :::
  ```
  Callouts are NOT optional decoration — the audit hard-fails the
  module if it has fewer than 3 across the whole file. Pick the flavor
  (note/tip/info) that matches what you're saying; the audit counts
  any of them.
- **NO IPA, NO Latin transliteration** — describe sounds by comparison.
- **Ukrainian quotes: «...»** for Ukrainian text.
- **Place exercise markers only** — write `<!-- INJECT_ACTIVITY: type, topic hint -->` where the skeleton places exercises. Do NOT write :::quiz or :::fill-in DSL directly.
- **You are a warm teacher** — natural teacher phrasing is fine. Avoid ONLY: self-congratulatory openers, gamified language, empty filler. No vocabulary tables or word count notes.
- **Zero Russian, zero Surzhyk, zero calques.**
- **NO stress marks** — a deterministic tool adds them later.
- **Dialogue formatting (EXEMPT from the monolingual rule):** Use blockquote `>` with speaker names in bold. Each turn on its own `>` line. Per-turn inline English translations in `*(English)*` ARE allowed for dialogs. NO blank lines between turns. Example:
  > — **Оксана:** Привіт! *(Hi!)*
  > — **Степан:** Добрий день! *(Good day!)*
  > — **Оксана:** Як справи? *(How are you?)*

{_chunk_required_vocab_block(plan, section_index, total_sections)}

{_CHUNK_FORBIDDEN_WORDS_BLOCK}

## Output

Write the section starting with the H2 heading **`## {section["title"]}`** (verbatim — do not paraphrase). Output ONLY the section content — no preamble, no summary, no notes.
"""
    # Wiki context is now in the knowledge packet (step_research handles it).
    # No separate chunk injection needed.
    section_prompt = section_prompt.replace("{WIKI_CHUNK_CONTEXT}", "")

    return section_prompt


def step_write_chunked(
    level: str, module_num: int, slug: str,
    packet_path: Path | None, writer: str = "gemini",
    skeleton: str = "",
    correction_directive: str = "",
) -> Path | None:
    """Write content section-by-section using skeleton sections as chunks.

    For modules with word_target >= 2000 and multiple skeleton H2 sections,
    generates each section in a separate LLM call with rolling context.
    Concatenates results into a single .md file.

    Returns the content path, or None on failure.
    """
    _log("  📦 CHUNKED generation — writing section-by-section")

    sections = _parse_skeleton_sections(skeleton)
    if len(sections) < 2:
        _log("  ⚠️  Skeleton has < 2 sections — falling back to single-call")
        return None  # caller falls back to single-call

    _log(f"  Skeleton has {len(sections)} sections:")
    for i, s in enumerate(sections):
        _log(f"    {i + 1}. {s['title']} (~{s['words']} words)")

    # Load plan and packet
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan_content = plan_path.read_text("utf-8")
    plan = yaml.safe_load(plan_content)

    packet = ""
    if packet_path and packet_path.exists():
        packet = packet_path.read_text("utf-8")
        if len(packet) > 30_000:
            packet = packet[:30_000] + "\n\n... (truncated for context window)"

    # Load write template for reference (used to pull content rules)
    is_seminar = _is_seminar_track(level)
    template_name = "v6-write-seminar.md" if is_seminar else "v6-write.md"
    template_path = PHASES_DIR / template_name
    template = template_path.read_text("utf-8") if template_path.exists() else ""

    from build.dispatch import dispatch_agent as _dispatch

    use_tools = writer.endswith("-tools")
    # Codex uses shell commands for verification, not MCP JSON-RPC
    use_mcp = use_tools and not writer.startswith("codex")
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)

    written_sections: list[str] = []

    for i, section in enumerate(sections):
        chunk_file = orch_dir / f"chunk-{i + 1:02d}.md"
        # Only load from cache if this is the first attempt (no correction directive)
        if not correction_directive and chunk_file.exists():
            chunk_content = chunk_file.read_text("utf-8")
            chunk_words = len(chunk_content.split())
            _log(f"\n  --- Chunk {i + 1}/{len(sections)}: {section['title']} ---")
            _log(f"  ⏭️  Loaded completed chunk {i + 1} from disk ({chunk_words} words)")
            written_sections.append(chunk_content)
            continue

        _log(f"\n  --- Chunk {i + 1}/{len(sections)}: {section['title']} ---")

        previous_summary = _build_section_summary(written_sections)

        prompt = _build_chunk_prompt(
            template=template,
            section=section,
            section_index=i,
            total_sections=len(sections),
            previous_summary=previous_summary,
            plan_content=plan_content,
            packet=packet,
            level=level,
            module_num=module_num,
            plan=plan,
            slug=slug,
        )

        # Inject correction directive on first chunk only
        if correction_directive and i == 0:
            prompt = correction_directive + "\n\n" + prompt

        # Save chunk prompt for inspection
        chunk_prompt_path = orch_dir / f"v6-chunk-{i + 1:02d}-prompt.md"
        chunk_prompt_path.write_text(prompt, "utf-8")

        # Dispatch — shorter timeout per section
        from build.dispatch import CLAUDE_WRITER_TOOLS

        chunk_retries = 3
        ok, raw = False, ""
        for attempt in range(1, chunk_retries + 1):
            if attempt > 1:
                _log(f"  🔄 Chunk {i + 1} retry attempt {attempt}/{chunk_retries}...")
            ok, raw = _dispatch(
                prompt, agent=writer, phase=f"write-chunk-{i + 1:02d}",
                orch_dir=orch_dir, timeout=TIMEOUT_WRITE if use_tools else TIMEOUT_WRITE_NO_TOOLS,
                mcp_tools=use_mcp,
                allowed_tools=CLAUDE_WRITER_TOOLS if (use_mcp and writer.startswith("claude")) else None,
            )
            if ok and raw:
                break
            if _handle_rate_limit_backoff(raw, attempt, chunk_retries, f"chunk-{i + 1}"):
                raw = ""  # Reset marker
                continue

        if not ok or not raw:
            _log(f"  ❌ Chunk {i + 1} failed after {chunk_retries} attempts — writer returned no output")
            return None

        # Extract from first ## heading
        lines = raw.split("\n")
        content_start = -1
        for j, line in enumerate(lines):
            if line.startswith("## "):
                content_start = j
                break

        chunk_content = "\n".join(lines[content_start:]) if content_start >= 0 else raw
        chunk_words = len(chunk_content.split())
        _log(f"  ✅ Chunk {i + 1}: {chunk_words} words")

        chunk_file.write_text(chunk_content, "utf-8")
        written_sections.append(chunk_content)

    # Concatenate all sections
    final_content = "\n\n".join(written_sections)

    # Strip any leaked tags
    final_content = re.sub(r"</?pacing_plan>", "", final_content)
    final_content = re.sub(r"</?skeleton>", "", final_content)

    output_dir = CURRICULUM_ROOT / level
    output_path = output_dir / f"{slug}.md"
    output_path.write_text(final_content, "utf-8")

    total_words = len(final_content.split())
    _log(f"\n  ✅ Chunked write complete: {total_words} words total ({len(sections)} sections)")
    _log(f"  → {output_path}")

    return output_path


def step_write(level: str, module_num: int, slug: str,
               packet_path: Path | None, writer: str = "gemini",
               correction_directive: str = "",
               skeleton: str = "",
               no_chunk: bool = False,
               verification_text: str = "") -> Path | None:
    """Step 5: Single LLM session — generate prose + exercise placeholders.

    When word_target >= 2000, the skeleton has multiple H2 sections, and
    --no-chunk is not set, delegates to step_write_chunked() for
    section-by-section generation. Falls back to single-call on failure.
    """
    _log(f"\n{'='*60}")
    _log(f"  Step 5: WRITE — Content generation ({writer})")
    _log(f"{'='*60}")

    # --- Chunking gate: section-by-section for large modules ---
    if skeleton and not no_chunk:
        plan_path_tmp = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
        if plan_path_tmp.exists():
            wt = yaml.safe_load(plan_path_tmp.read_text("utf-8")).get("word_target", 0)
            skeleton_sections = _parse_skeleton_sections(skeleton)
            if wt >= 2000 and len(skeleton_sections) >= 2:
                _log(f"  Chunking enabled: word_target={wt}, sections={len(skeleton_sections)}")
                result = step_write_chunked(
                    level, module_num, slug, packet_path,
                    writer=writer, skeleton=skeleton,
                    correction_directive=correction_directive,
                )
                if result is not None:
                    return result
                _log("  ⚠️  Chunked write failed — falling back to single-call")

    # Load template — use seminar prompt for seminar tracks
    is_seminar = _is_seminar_track(level)
    template_name = "v6-write-seminar.md" if is_seminar else "v6-write.md"
    template_path = PHASES_DIR / template_name
    if not template_path.exists():
        _log(f"  ❌ Template not found: {template_path}")
        return None
    if is_seminar:
        _log("  📚 Using seminar prompt template")

    template = template_path.read_text("utf-8")

    # Load plan (read once, parse once)
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan_content = plan_path.read_text("utf-8")
    plan = yaml.safe_load(plan_content)

    # Load knowledge packet (wiki-compiled articles — authoritative teaching content)
    packet = packet_path.read_text("utf-8") if packet_path and packet_path.exists() else ""
    # Wiki articles are 25-30K chars of compiled pedagogy.  Gemini's 1M context
    # handles this easily.  Truncation loses curated teaching content.
    if len(packet) > 30_000:
        packet = packet[:30_000] + "\n\n... (truncated for context window)"

    # Build section titles
    sections = plan.get("content_outline", [])
    section_titles = []
    for s in sections:
        name = s.get("section", "")
        words = s.get("words", 0)
        section_titles.append(f"- `## {name}` (~{words} words)")

    summary_heading = "Summary" if module_num <= 3 else "Підсумок — Summary" if module_num <= 14 else "Підсумок"

    # Add summary only if not already in the plan outline
    has_summary = any("Підсумок" in s.get("section", "") or "Summary" in s.get("section", "") for s in sections)
    if not has_summary:
        section_titles.append(f"- `## {summary_heading}` (~150 words)")

    # Build vocabulary hints (v4: list of {word,pos,definition}, v3: {required:[],recommended:[]})
    raw_vocab = plan.get("vocabulary_hints") or plan.get("vocabulary") or {}
    vocab_lines = []
    # Required vocab list — used for the late-prompt MANDATORY checklist (#1189).
    # Format: list of plain Ukrainian words; the checklist renders them as
    # markdown checkboxes near the end of the prompt where Gemini's attention
    # is highest. Empirically the writer drops abstract metalanguage first
    # (видова пара, дієвідміна, etc.) so we need a hard final reminder.
    required_vocab_words: list[str] = []
    if isinstance(raw_vocab, list):
        # v4 format
        words = [v.get("word", str(v)) if isinstance(v, dict) else str(v) for v in raw_vocab]
        if words:
            vocab_lines.append(f"**Vocabulary:** {', '.join(words)}")
            required_vocab_words = words
    elif isinstance(raw_vocab, dict):
        # v3 format
        for category in ("required", "recommended"):
            items = raw_vocab.get(category, [])
            if items:
                vocab_lines.append(f"**{category.capitalize()}:** {', '.join(str(i) for i in items)}")
                if category == "required":
                    required_vocab_words = [str(i) for i in items]

    # Render the late-prompt checklist (markdown checkboxes for visibility)
    if required_vocab_words:
        vocabulary_checklist = "\n".join(
            f"- [ ] {w}" for w in required_vocab_words
        )
    else:
        vocabulary_checklist = "_(no required vocabulary defined for this module)_"

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
        "{IMMERSION_TARGET_SHORT}": _get_immersion_target_short(level, module_num),
        **_build_salad_phase_placeholders(level, module_num),
        "{PEDAGOGICAL_CONSTRAINTS}": get_pedagogical_constraints(level, module_num, plan),
        "{LEVEL_CONSTRAINTS}": get_level_constraints(level, plan),
        "{VOCABULARY_HINTS}": "\n".join(vocab_lines),
        "{VOCABULARY_CHECKLIST}": vocabulary_checklist,
        "{PRONUNCIATION_VIDEOS}": "\n".join(pv_lines),
        "{GOLDEN_FRAGMENT}": get_golden_fragment(level, module_num),
        "{DIALOGUE_SITUATIONS}": _build_dialogue_situations(plan),
        "{SUMMARY_HEADING}": summary_heading,
        "{SKELETON_SECTION}": "",  # Populated below for seminar templates
        "{CORRECTION_SECTION}": "",  # Populated below for seminar templates
    }

    # Wiki context is in the knowledge packet (step_research handles it for all tracks).

    # Build skeleton/correction blocks for seminar template placeholders
    if is_seminar and skeleton:
        replacements["{SKELETON_SECTION}"] = (
            "---\n\n"
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
            "</skeleton>"
        )
        _log(f"  📐 Skeleton injected via seminar placeholder ({len(skeleton)} chars)")
    if is_seminar and correction_directive:
        replacements["{CORRECTION_SECTION}"] = correction_directive

    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Inject persona/voice — from plan or shared _PERSONAS fallback
    voice, role = _resolve_persona(level, plan)

    if voice:
        persona_section = (
            "\n\n---\n\n"
            "## Your Writing Identity\n\n"
            f"**You are: {voice}.**"
        )
        if role:
            persona_section += f" Your persona is *{role}*."
        persona_section += (
            "\n\nWrite with the authority, depth, and tone that this identity demands. "
            "A history professor writes differently from a language tutor. "
            "A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. "
            "Let your identity shape your word choice, pacing, and cultural sensitivity.\n"
        )
        prompt = persona_section + "\n" + prompt
        _log(f"  🎭 Persona: {voice} / {role}")

    # Inject pre-verified facts via {PRE_VERIFIED_FACTS} placeholder in template
    if verification_text:
        verify_section = (
            "## Pre-Verified Facts (from MCP tools — use these, do NOT guess)\n\n"
            "A verification step already called VESUM, textbooks, Правопис, and "
            "style guide tools. The results below are GROUND TRUTH. Use them:\n"
            "- If a word is marked ❌ NOT IN VESUM — do NOT use it\n"
            "- If a textbook excerpt is provided — use that pedagogy\n"
            "- If a calque is flagged — use the correct alternative\n"
            "- If CEFR says a word is above target — find a simpler synonym\n\n"
            "You do NOT need to call tools yourself — the facts are already verified.\n\n"
            "<pre_verified_facts>\n"
            f"{verification_text}\n"
            "</pre_verified_facts>\n"
        )
    else:
        verify_section = ""
    prompt = prompt.replace("{PRE_VERIFIED_FACTS}", verify_section)
    if verification_text:
        _log(f"  🔍 Pre-verified facts injected ({len(verification_text)} chars)")

    # Inject module friction (learnings from past builds that MUST be respected)
    friction_path = CURRICULUM_ROOT / level / "orchestration" / slug / "friction.yaml"
    if friction_path.exists():
        try:
            friction_entries = yaml.safe_load(friction_path.read_text("utf-8"))
            if isinstance(friction_entries, list):
                active = [f for f in friction_entries if f.get("status") == "active"]
                if active:
                    friction_lines = [
                        "\n\n## Module-Specific Constraints (from past build learnings)\n\n"
                        "**These are NON-NEGOTIABLE.** Previous builds of this module had these "
                        "errors. You MUST avoid them:\n"
                    ]
                    for f in active:
                        sev = f.get("severity", "medium").upper()
                        desc = f.get("description", "").strip()
                        friction_lines.append(f"\n- **[{sev}]** {desc}")
                    prompt += "\n".join(friction_lines) + "\n"
                    _log(f"  🔧 Friction injected: {len(active)} active constraint(s)")
        except Exception:
            pass  # Non-blocking

    # Inject skeleton section when provided (Skeleton->Flesh architecture)
    # (skipped for seminar templates — already handled via {SKELETON_SECTION} placeholder)
    if skeleton and not is_seminar:
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
    # (skipped for seminar templates — already handled via {CORRECTION_SECTION} placeholder)
    if correction_directive and not is_seminar:
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

    # Inject plan-point checklist as the LAST thing in the prompt.
    # Recency effect: the LLM attends most to what it just read.
    # This prevents the #1 review rejection: "plan point X was not covered."
    checklist_items = []
    for s in plan.get("content_outline", []):
        for p in s.get("points", []):
            checklist_items.append(f"- [ ] {str(p)[:120]}")
    if checklist_items:
        checklist = (
            "\n\n---\n\n"
            "## MANDATORY PRE-SUBMIT CHECKLIST\n\n"
            "**Before you output your final text, verify EVERY item below is covered "
            "in your output. If you skip ANY item, the module will be REJECTED.**\n\n"
            + "\n".join(checklist_items)
            + f"\n- [ ] Word count is {word_target}–{int(word_target * 1.5)} words"
            + "\n- [ ] No 'Let us...', 'In this section...', or formulaic openers"
            + "\n- [ ] Every exercise marker from the skeleton is placed"
            + "\n"
        )
        prompt = prompt + checklist

    # Inject tool instructions for -tools writers
    use_tools = writer.endswith("-tools")
    if use_tools:
        prompt = prompt + _build_tool_instructions(writer)

    # Dispatch via unified dispatcher
    from build.dispatch import CLAUDE_WRITER_TOOLS, dispatch_agent

    if writer == "gemini":
        ok, raw = dispatch_agent(
            prompt, agent="gemini", phase="write", orch_dir=orch_dir, timeout=TIMEOUT_WRITE_NO_TOOLS,
        )
    elif writer == "gemini-tools":
        ok, raw = dispatch_agent(
            prompt, agent="gemini-tools", phase="write", orch_dir=orch_dir,
            timeout=TIMEOUT_WRITE, mcp_tools=True,
        )
    elif writer in ("claude", "claude-tools"):
        ok, raw = dispatch_agent(
            prompt, agent=writer, phase="write", orch_dir=orch_dir,
            timeout=TIMEOUT_WRITE if use_tools else TIMEOUT_WRITE_NO_TOOLS,
            mcp_tools=use_tools, allowed_tools=CLAUDE_WRITER_TOOLS if use_tools else None,
        )
    elif writer in ("codex", "codex-tools"):
        # Codex uses workspace-write sandbox (--full-auto) so it can run
        # the shell-command verification tools injected into the prompt.
        # No MCP tools — Codex verifies via subprocess Python calls.
        # Issue: #1194
        ok, raw = dispatch_agent(
            prompt, agent="codex-tools" if use_tools else "codex", phase="write",
            orch_dir=orch_dir, timeout=TIMEOUT_WRITE,
        )
    else:
        _log(f"  ❌ Unknown writer: {writer}")
        return None

    if not ok or not raw:
        _log("  ❌ Writer returned no output")
        return None

    # Save pacing plan if present (for debugging)
    pacing_match = re.search(r"<pacing_plan>(.*?)</pacing_plan>", raw, re.DOTALL)
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
    final_content = re.sub(r"</?pacing_plan>", "", final_content)
    final_content = re.sub(r"</?skeleton>", "", final_content)

    output_path.write_text(final_content, "utf-8")
    word_count = len(final_content.split())
    _log(f"  ✅ Content written ({word_count} words)")
    _log(f"  → {output_path}")

    return output_path



def step_fix_output(
    level: str, module_num: int, slug: str,
    content: str, correction_directive: str,
    writer: str = "gemini",
) -> Path | None:
    """Fix a completed (but failing) draft in-place without chunking."""
    _log(f"\n{'='*60}")
    _log(f"  Step 5 (Fix): FIX OUTPUT — Holistic correction ({writer})")
    _log(f"{'='*60}")

    prompt = f"""You are an expert Ukrainian linguist and curriculum designer.
I have a completed draft of a curriculum module. However, it failed automated quality checks.

Here are the errors you MUST fix:
<errors>
{correction_directive}
</errors>

Here is the current draft:
<draft>
{content}
</draft>

Please output the FULL, CORRECTED draft.
Do not add any preamble, explanations, or markdown code block wrappers like ```markdown.
Start immediately with the first ## heading. Keep all other formatting exactly as is.
"""

    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)

    from build.dispatch import CLAUDE_WRITER_TOOLS, dispatch_agent

    use_tools = writer.endswith("-tools")
    if "gemini" in writer:
        base_writer = "gemini-tools"
    elif "codex" in writer:
        base_writer = "codex-tools"
    else:
        base_writer = writer

    if "claude" in writer:
        ok, raw = dispatch_agent(
            prompt, agent=writer, phase="write-fix", orch_dir=orch_dir,
            timeout=TIMEOUT_WRITE, mcp_tools=use_tools,
            allowed_tools=CLAUDE_WRITER_TOOLS if use_tools else None,
        )
    elif "codex" in writer:
        # Codex: shell-command tools via workspace-write, no MCP
        ok, raw = dispatch_agent(
            prompt, agent=base_writer, phase="write-fix", orch_dir=orch_dir,
            timeout=TIMEOUT_WRITE,
        )
    else:
        ok, raw = dispatch_agent(
            prompt, agent=base_writer, phase="write-fix", orch_dir=orch_dir,
            timeout=TIMEOUT_WRITE, mcp_tools=True,
        )

    if not ok or not raw:
        _log("  ❌ Writer returned no output during fix attempt")
        return None

    # Extract content (everything from first ## heading)
    lines = raw.split("\n")
    content_start = -1
    for i, line in enumerate(lines):
        if line.startswith("## "):
            content_start = i
            break

    final_content = raw if content_start < 0 else "\n".join(lines[content_start:])

    final_content = re.sub(r"</?pacing_plan>", "", final_content)
    final_content = re.sub(r"</?skeleton>", "", final_content)

    output_dir = CURRICULUM_ROOT / level
    output_path = output_dir / f"{slug}.md"

    # Guard: reject fix output that lost significant content.
    # The fix step sometimes summarizes instead of correcting, producing
    # a fraction of the original word count. Keep the original if so.
    # EXCEPTION: if the original has TOXIC violations (Russian characters,
    # Russianisms), accept the shorter clean version — a short clean module
    # is better than a long toxic one. The heal/review loop can expand it
    # later. (2026-04-12: a2/all-cases-practice exhausted 5 retries because
    # each fix was ~3000 words vs 6689 toxic original.)
    fix_words = len(final_content.split())
    orig_words = len(content.split())
    original_is_toxic = bool(re.search(
        r'[ъёыэ]|пожалуйста|спасибо|хорошо|конечно|ничего|сейчас|тоже|здесь',
        content, re.IGNORECASE,
    ))
    if orig_words > 500 and fix_words < orig_words * 0.6 and not original_is_toxic:
        _log(f"  ❌ Fix output too short ({fix_words} words vs {orig_words} original) — keeping original")
        return None
    if original_is_toxic and fix_words > 500:
        _log(f"  ⚠️  Fix output shorter ({fix_words} vs {orig_words}) but original was TOXIC — accepting clean version")

    output_path.write_text(final_content, "utf-8")

    _log(f"  ✅ Fixed content written ({fix_words} words)")
    return output_path

def step_write_with_retry(
    level: str, module_num: int, slug: str,
    packet_path: Path | None,
    writer: str = "gemini",
    max_retries: int = 4,
    skeleton: str = "",
    no_chunk: bool = False,
    verification_text: str = "",
) -> Path | None:
    """Write content with quick verify and retry loop.

    Strategy:
    - Up to 5 attempts (max_retries=4 → attempts 1-5)
    - Each retry uses same writer + correction directive (no model switching)
    - Never fall back to a different agent
    - On exhaustion: return output + flag for human review
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

    current_directive = ""  # No directive on first attempt

    for attempt in range(1, max_retries + 2):  # +2 because range is exclusive
        current_writer = writer
        _log(f"\n  📝 Write attempt {attempt}/{max_retries + 1} (writer: {current_writer})")

        if attempt == 1:
            output = step_write(
                level, module_num, slug, packet_path,
                writer=current_writer,
                correction_directive=current_directive,
                skeleton=skeleton,
                no_chunk=no_chunk,
                verification_text=verification_text,
            )
        else:
            # We already have a draft but it failed verify. Use step_fix_output.
            output_dir = CURRICULUM_ROOT / level
            output_path = output_dir / f"{slug}.md"
            if not output_path.exists():
                _log("  ❌ Could not find previous output for fix attempt")
                break
            prev_content = output_path.read_text("utf-8")
            output = step_fix_output(
                level, module_num, slug,
                content=prev_content,
                correction_directive=current_directive,
                writer=current_writer,
            )
        if output is None:
            _log(f"  ❌ Writer returned no output on attempt {attempt}")
            _log_stats(stats_path, slug, "WRITE_FAILED", attempt, current_writer, False)
            continue

        # Stub detection: if output is absurdly short, treat as transient
        # API failure and retry without correction directive (don't waste an
        # attempt on a correction that can't help a non-response).
        content = output.read_text("utf-8")
        word_count = len(content.split())
        if word_count < 100 and attempt <= max_retries:
            _log(f"  ⚠️  Stub response detected ({word_count} words) — transient API failure, retrying same writer")
            _log_stats(stats_path, slug, "STUB_RESPONSE", attempt, current_writer, False)
            continue  # retry WITHOUT correction directive

        # Quick verify
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

        # Post-error auto-query: search past friction files for matching patterns
        friction_hints = _query_friction_for_errors(level, slug, results)
        if friction_hints:
            _log(f"  🔍 Friction auto-query: {len(friction_hints)} relevant hint(s) from past builds")

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
        # Append friction hints from past builds (post-error auto-query)
        if friction_hints:
            current_directive += (
                "\n\nLEARNINGS FROM PAST BUILDS (same error patterns seen before):\n"
                + "\n".join(f"- {h}" for h in friction_hints)
            )
        _log("  🔄 Retrying with correction directive...")

        # Also save directive to disk for human inspection
        orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
        orch_dir.mkdir(parents=True, exist_ok=True)
        directive_path = orch_dir / f"correction-attempt-{attempt}.md"
        directive_path.write_text(current_directive, "utf-8")

    return None  # Should not reach here


def _query_friction_for_errors(level: str, slug: str, results: list) -> list[str]:
    """Post-error auto-query: search past friction files for matching error patterns.

    Scans all friction.yaml files across all modules (excluding current slug)
    and the global friction file. Returns a list of relevant hint strings
    that match the current error types.

    Inspired by mozilla-ai/cq's shared agent learning — agents shouldn't
    rediscover the same failures independently.
    """
    current_error_types = {r.check for r in results if r.severity == "ERROR"}
    if not current_error_types:
        return []

    hints: list[str] = []

    # 1. Search global friction
    global_path = PROJECT_ROOT / "docs" / "rules" / "global-friction.yaml"
    if global_path.exists():
        try:
            data = yaml.safe_load(global_path.read_text("utf-8"))
            for f in data.get("frictions", []):
                if f.get("status") == "active":
                    hints.append(f"[GLOBAL] {f.get('description', '').strip()}")
        except Exception:
            pass

    # 2. Search module-specific friction files across ALL modules
    for orch_dir in (CURRICULUM_ROOT / level / "orchestration").iterdir():
        if not orch_dir.is_dir() or orch_dir.name == slug:
            continue  # skip self
        friction_path = orch_dir / "friction.yaml"
        if not friction_path.exists():
            continue
        try:
            entries = yaml.safe_load(friction_path.read_text("utf-8"))
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if entry.get("status") != "active":
                    continue
                past_errors = set(entry.get("error_types", []))
                # Match if there's overlap in error types
                overlap = current_error_types & past_errors
                if overlap:
                    note = entry.get("note", "")
                    hints.append(
                        f"[{orch_dir.name}] Same errors ({', '.join(overlap)}): {note}"
                    )
        except Exception:
            continue

    # 3. Also scan other levels' friction files for cross-level patterns
    for level_dir in CURRICULUM_ROOT.iterdir():
        if not level_dir.is_dir() or level_dir.name == level:
            continue
        orch_root = level_dir / "orchestration"
        if not orch_root.exists():
            continue
        for orch_dir in orch_root.iterdir():
            if not orch_dir.is_dir():
                continue
            friction_path = orch_dir / "friction.yaml"
            if not friction_path.exists():
                continue
            try:
                entries = yaml.safe_load(friction_path.read_text("utf-8"))
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if entry.get("status") != "active":
                        continue
                    past_errors = set(entry.get("error_types", []))
                    overlap = current_error_types & past_errors
                    if overlap:
                        note = entry.get("note", "")
                        hints.append(
                            f"[{level_dir.name}/{orch_dir.name}] Same errors ({', '.join(overlap)}): {note}"
                        )
            except Exception:
                continue

    return hints[:10]  # cap at 10 to avoid bloating the prompt


def _save_structured_findings(review_text: str, orch_dir: Path, round_num: int):
    """Extract structured findings from review markdown and save as YAML.

    Parses the ## Findings section for [DIMENSION] [SEVERITY] blocks.
    Saves to orchestration for aggregation across modules (#1027, #1028).
    """
    findings = []
    # Match finding blocks: ```\n[DIMENSION] [SEVERITY]\n...\n```
    pattern = re.compile(
        r"```\s*\n\[(\w[\w\s&]*?)\]\s*\[(\w+)\]\s*\n"
        r"Location:\s*(.*?)\n"
        r"Issue:\s*(.*?)\n"
        r"Fix:\s*(.*?)\n```",
        re.DOTALL,
    )
    for m in pattern.finditer(review_text):
        findings.append({
            "dimension": m.group(1).strip(),
            "severity": m.group(2).strip(),
            "location": m.group(3).strip(),
            "issue": m.group(4).strip(),
            "fix": m.group(5).strip(),
        })

    # Also extract scores table
    score_pattern = re.compile(r"\|\s*(\d+)\.\s*([^|]+)\|\s*(\d+)/10\s*\|([^|]*)\|")
    scores = []
    for m in score_pattern.finditer(review_text):
        scores.append({
            "dimension": int(m.group(1)),
            "name": m.group(2).strip(),
            "score": int(m.group(3)),
            "evidence": m.group(4).strip()[:200],  # truncate long evidence
        })

    if findings or scores:
        data = {"round": round_num, "scores": scores, "findings": findings}
        out_path = orch_dir / f"review-structured-r{round_num}.yaml"
        out_path.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
            "utf-8",
        )


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


def step_repair(level: str, module_num: int, slug: str) -> tuple[bool, bool]:
    """Step 5f: Deterministic activity repair.

    Runs after step_activities. Applies structural fixes that don't need an
    LLM: strips parenthetical hints, deduplicates options, moves misplaced
    section types, drops disallowed types, enforces answer-in-options, etc.

    Returns (success, needs_regen):
      success    — True if repair ran cleanly (even if it did nothing)
      needs_regen — True if count fell below min and activities must be
                    regenerated before the module can ship
    """
    _log(f"\n{'='*60}")
    _log(f"  Step 5f: REPAIR — Deterministic activity fixes ({slug})")
    _log(f"{'='*60}")

    activity_path = CURRICULUM_ROOT / level / "activities" / f"{slug}.yaml"
    if not activity_path.exists():
        _log(f"  ⚠️  No activity file at {activity_path}, skipping")
        return True, False

    try:
        from build.activity_repair import repair_activities
        result = repair_activities(activity_path, level, module_num)
    except Exception as e:
        _log(f"  ⚠️  Repair failed with exception: {e}")
        return False, False

    if result.fixes_applied:
        _log(f"  🔧 Applied {result.fixes_applied} fix(es):")
        for line in result.fix_log:
            _log(f"    • {line}")
    else:
        _log("  ✅ No repairs needed")

    _log(
        f"  Final counts: {result.inline_count_after} inline "
        f"+ {result.workbook_count_after} workbook"
    )

    if result.needs_regen:
        _log(f"  ⚠️  Regen required ({len(result.needs_regen)}):")
        for reason in result.needs_regen:
            _log(f"    → {reason}")
        return True, True

    return True, False


def step_audit(content_path: Path, level: str, slug: str) -> bool:
    """Step 10: Full audit — writes status/{slug}.json with gate results.

    Runs the deterministic audit (word count, activities, vocab, naturalness,
    VESUM, stress, review violations) and saves the status cache that the
    monitor API reads.

    Non-blocking: a failing audit does NOT halt the build. The content is
    already published. Audit captures quality metrics for reporting and
    follow-up. Use the status file to find modules that need fixing.

    Reason this is a separate step (not merged into verify): v6's step_verify
    does quick VESUM+scope checks only. This runs the full gate battery
    including activity/vocab minimums, naturalness scoring, and writes the
    status JSON that monitor API consumes.
    """
    _log(f"\n{'='*60}")
    _log(f"  Step 10: AUDIT — Full quality gates ({slug})")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    status_path = CURRICULUM_ROOT / level / "status" / f"{slug}.json"
    previous_status_mtime: float | None = None
    if status_path.exists():
        try:
            previous_status_mtime = status_path.stat().st_mtime
        except OSError:
            previous_status_mtime = None
        try:
            status_path.unlink()
            _log(f"  🧹 Cleared stale status cache before audit: {status_path.name}")
        except OSError as exc:
            _log(f"  ⚠️  Could not clear stale status cache: {exc}")
            return False

    try:
        # Import lazily — audit has heavy deps (morphological analysis, etc.)
        from audit.core import audit_module as run_audit

        # audit_module() writes the status file as a side effect via
        # generate_output_and_report(). Returns True on pass, False on fail.
        # We don't halt on failure — just record the result in the status file.
        run_audit(str(content_path), skip_activities=False, skip_review=False)

        if status_path.exists():
            try:
                status_mtime = status_path.stat().st_mtime
            except OSError as exc:
                _log(f"  ⚠️  Audit wrote unreadable status file: {exc}")
                return False

            if previous_status_mtime is not None and status_mtime <= previous_status_mtime:
                _log("  ⚠️  Audit did not produce a fresh status file (mtime did not advance)")
                try:
                    status_path.unlink()
                except OSError:
                    pass
                return False

            _log(f"  ✅ Status written: {status_path.name}")
            # Report overall status from the file
            try:
                import json
                data = json.loads(status_path.read_text("utf-8"))
                overall = data.get("overall", {}).get("status", "unknown")
                gates = data.get("gates", {})
                failed = [k for k, v in gates.items() if isinstance(v, dict) and v.get("status") == "fail"]
                if overall == "pass":
                    _log("  🟢 All gates PASS")
                else:
                    _log(f"  🟡 Overall: {overall} — failed gates: {', '.join(failed) if failed else 'see status file'}")
            except Exception as e:
                _log(f"  ⚠️  Could not parse status file: {e}")
        else:
            _log("  ⚠️  Audit ran but no status file was written")
            return False

        return True
    except Exception as e:
        _log(f"  ⚠️  Audit failed with exception: {e}")
        return False


def step_annotate(content_path: Path) -> bool:
    """Step 8b: Add stress marks (after review, before publish).

    NOTE: Does NOT call _post_process_content — that runs earlier (step 6).
    Stress marks are added to the prose-only .md; publish uses the annotated
    prose when building the final MDX.
    """
    _log(f"\n{'='*60}")
    _log("  Step 8b: ANNOTATE — Stress marks")
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


def step_vocab(content_path: Path, level: str, module_num: int,
               slug: str, writer: str = "claude") -> Path | None:
    """Step 5c: Generate vocabulary YAML from the module content.

    The writer reads its own prose and produces a vocabulary list
    with contextual translations. No dictionary API lookups needed.
    """
    _log(f"\n{'='*60}")
    _log(f"  Step 5c: VOCAB — Writer generates словник ({writer})")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return None

    # Load vocab prompt template
    template_path = PHASES_DIR / "v6-vocab.md"
    if not template_path.exists():
        _log(f"  ⚠️  Vocab template not found: {template_path}")
        return None

    template = template_path.read_text("utf-8")

    # Load plan vocabulary
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8")) if plan_path.exists() else {}
    vocab_hints = plan.get("vocabulary_hints") or plan.get("vocabulary") or {}
    plan_vocab_text = yaml.dump(vocab_hints, allow_unicode=True, default_flow_style=False)

    # Load module content
    module_content = content_path.read_text("utf-8")

    # Build prompt
    prompt = template.replace("{PLAN_VOCABULARY}", plan_vocab_text)
    prompt = prompt.replace("{MODULE_CONTENT}", module_content)

    # Dispatch to writer — vocab uses Flash-Lite (dictionary-like structured output).
    from build.dispatch import dispatch_agent as _dispatch

    family = get_family(writer)
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)

    # Vocab is structured output — use fast/cheap model
    ok, raw = _dispatch(
        prompt, agent=family.name, phase="vocab", orch_dir=orch_dir, timeout=TIMEOUT_VOCAB,
        model=family.fast,
    )

    if not ok or not raw:
        _log("  ❌ Writer returned no vocabulary output")
        return None

    # Parse vocabulary YAML
    from build.vocab_gen import (
        dedupe_vocab,
        get_previous_vocab,
        parse_vocab_yaml,
        vesum_enrich_entry,
    )

    entries = parse_vocab_yaml(raw)
    if not entries:
        _log("  ⚠️  Could not parse vocabulary YAML")
        return None

    _log(f"  Writer produced {len(entries)} vocabulary entries")

    # Dedup against previous modules
    previous = get_previous_vocab(level, plan.get("sequence", 1))
    before_count = len(entries)
    entries = dedupe_vocab(entries, previous)
    deduped = before_count - len(entries)
    if deduped:
        _log(f"  Deduped: removed {deduped} words already taught")

    # VESUM enrichment
    entries = [vesum_enrich_entry(e) for e in entries]

    # Save vocabulary YAML
    vocab_dir = CURRICULUM_ROOT / level / "vocabulary"
    vocab_dir.mkdir(parents=True, exist_ok=True)
    vocab_path = vocab_dir / f"{slug}.yaml"
    vocab_data = {"vocabulary": entries}
    vocab_path.write_text(
        yaml.dump(vocab_data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        "utf-8",
    )

    words = [e for e in entries if not e.get("expression")]
    exprs = [e for e in entries if e.get("expression")]
    _log(f"  ✅ Vocabulary: {len(words)} words + {len(exprs)} expressions → {vocab_path.name}")

    _save_v6_state(level, slug, "vocab")
    return vocab_path


def _extract_verify_flags(content: str) -> list[dict]:
    """Extract <!-- VERIFY: ... --> flags from writer content.

    Writers are told to flag uncertain words/claims with these markers.
    We extract them early (before ENRICH might alter structure) so we can:
    1. Attempt automated VESUM resolution
    2. Pass unresolved flags to the reviewer
    3. Track resolution stats

    Issue: #1018
    """
    flags = []
    for m in re.finditer(r"<!--\s*VERIFY:\s*(.+?)\s*-->", content):
        flags.append({
            "claim": m.group(1).strip(),
            "resolved": False,
            "resolution": "",
        })
    return flags


def _resolve_verify_flags(flags: list[dict]) -> list[dict]:
    """Attempt to resolve VERIFY flags via VESUM lookup.

    For each flag, extracts the first Ukrainian word from the claim
    and checks if it exists in VESUM. If found, marks it resolved
    with the lemma and POS info.

    Returns the same list with resolved/resolution fields updated.
    """
    if not flags:
        return flags

    import sqlite3

    vesum_db = PROJECT_ROOT / "data" / "vesum.db"
    if not vesum_db.exists():
        return flags

    # Pattern to find Ukrainian words in a claim
    uk_word_pattern = re.compile(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ]+")

    try:
        db = sqlite3.connect(str(vesum_db))
        for flag in flags:
            # Extract Ukrainian words from the claim
            words = uk_word_pattern.findall(flag["claim"])
            if not words:
                continue

            for word in words:
                row = db.execute(
                    "SELECT lemma, pos FROM forms WHERE word_form = ? LIMIT 1",
                    (word.lower(),),
                ).fetchone()
                if row:
                    flag["resolved"] = True
                    flag["resolution"] = (
                        f"VESUM confirms: {word} -> lemma '{row[0]}', POS: {row[1]}"
                    )
                    break
            # If no word found in VESUM, try lemma lookup
            if not flag["resolved"]:
                for word in words:
                    row = db.execute(
                        "SELECT lemma, pos FROM forms WHERE lemma = ? LIMIT 1",
                        (word.lower(),),
                    ).fetchone()
                    if row:
                        flag["resolved"] = True
                        flag["resolution"] = (
                            f"VESUM confirms lemma: {row[0]}, POS: {row[1]}"
                        )
                        break
        db.close()
    except Exception as e:
        _log(f"  ⚠️  VESUM resolution failed: {e}")

    return flags


def _save_verify_flags(level: str, slug: str, flags: list[dict]) -> Path:
    """Save VERIFY flags to orchestration directory.

    Returns the path to the saved file.
    """
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    flags_path = orch_dir / "verify-flags.yaml"
    flags_path.write_text(
        yaml.dump(flags, allow_unicode=True, default_flow_style=False, sort_keys=False),
        "utf-8",
    )
    return flags_path


def step_verify_exercises(content_path: Path, level: str, slug: str) -> bool:
    """Step 5d: Verify exercise items are grounded in module prose.

    Informational check -- logs warnings but does NOT fail the build.
    Saves results to orchestration/{slug}/exercise-verification.json.

    Issue: #1016
    """
    import json

    _log(f"\n{'='*60}")
    _log("  Step 5d: VERIFY EXERCISES — Grounding check")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    from build.exercise_verify import format_verify_result, verify_exercises

    content = content_path.read_text("utf-8")

    # Load plan for vocabulary_hints check
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan = None
    if plan_path.exists():
        plan = yaml.safe_load(plan_path.read_text("utf-8"))

    # Load V6 activities YAML (separate from markdown content)
    activities_path = CURRICULUM_ROOT / level / "activities" / f"{slug}.yaml"
    activities = None
    if activities_path.exists():
        activities = yaml.safe_load(activities_path.read_text("utf-8"))
        _log(f"  Loaded activities from {activities_path}")

    result = verify_exercises(content, plan, activities=activities)
    _log(format_verify_result(result))

    # Run structural/pedagogical activity validation
    if activities_path and activities_path.exists():
        from build.activity_validator import format_report, validate_activities
        act_issues = validate_activities(activities_path)
        if act_issues:
            _log(format_report(act_issues))
        else:
            _log("  ✅ Activity structure valid")

    # Save results to orchestration
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    verify_path = orch_dir / "exercise-verification.json"

    data = {
        "total_items": result.total_items,
        "grounded_items": result.grounded_items,
        "ungrounded": result.ungrounded,
        "vocab_coverage": result.vocab_coverage,
        "all_grounded": result.all_grounded,
    }
    verify_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), "utf-8"
    )
    _log(f"  → {verify_path}")

    return True


def _check_activity_semantics(data: dict) -> list[str]:
    """Check inline activity ids for uniqueness and existence."""
    errors: list[str] = []
    seen: dict[str, int] = {}
    for i, activity in enumerate(data.get("inline", [])):
        if not isinstance(activity, dict):
            continue
        aid = activity.get("id")
        if not aid:
            errors.append(f"inline[{i}]: missing required 'id' field")
        elif aid in seen:
            errors.append(
                f"inline[{i}]: duplicate id '{aid}' "
                f"(first seen at inline[{seen[aid]}])"
            )
        else:
            seen[aid] = i
    return errors


def _build_activity_level_context(level: str, module_num: int, plan: dict) -> str:
    """Build level-aware context for the activity generator.

    Tells the generator WHO the learner is, what they can and can't do,
    what language to use for instructions, and which activity types are appropriate.
    """
    pv = plan.get("pronunciation_videos", {})
    video_text = ""
    if pv:
        video_text = (
            "\n**Pronunciation videos (Anna Ohoiko):**\n"
            f"- Overview: {pv.get('overview', 'N/A')}\n"
            f"- Full playlist: {pv.get('playlist', 'N/A')}\n"
            "Use these in exercises: reference specific videos, embed WatchAndRepeat activities.\n"
        )

    if level == "a1" and module_num <= 7:
        return (
            f"**Level: A1.1 (Module {module_num}/55) — COMPLETE BEGINNER**\n\n"
            "The learner is on their FIRST DAYS learning Ukrainian. They:\n"
            "- Cannot read Ukrainian yet (learning the alphabet)\n"
            "- Know zero Ukrainian grammar\n"
            "- Can recognize only a few words (мама, тато, привіт)\n\n"
            "**ALL instructions MUST be in English.** The learner cannot read Ukrainian instructions.\n\n"
            "**Best activity types for this level:**\n"
            "- image-to-letter: hear/see → pick the letter\n"
            "- letter-grid: interactive alphabet practice\n"
            "- match-up: letter ↔ sound, letter ↔ word\n"
            "- quiz: in ENGLISH about Ukrainian sounds ('What sound does В make?')\n"
            "- observe: show patterns in Ukrainian with English prompts\n"
            "- group-sort: sort letters into vowels/consonants\n"
            "- divide-words: split words into syllables (складоподіл)\n"
            "- count-syllables: count syllables by counting vowels\n"
            "- pick-syllables: select open/closed syllables\n"
            "- odd-one-out: find the word that doesn't belong\n"
            "- watch-and-repeat: pronunciation video practice\n"
            "- translate: single words/short phrases English→Ukrainian (multiple choice)\n"
            "- error-correction: find simple errors (gender agreement, missing ь)\n\n"
            "**DO NOT use:** cloze, mark-the-words, select, essay-response, unjumble "
            "(learner can't construct Ukrainian sentences yet).\n"
            f"{video_text}"
        )
    if level == "a1" and module_num <= 21:
        return (
            f"**Level: A1.2-A1.3 (Module {module_num}/55) — EARLY BEGINNER**\n\n"
            "The learner knows the alphabet and ~200 words. They:\n"
            "- Can read Ukrainian slowly\n"
            "- Know basic nouns, adjectives, simple verb forms\n"
            "- Cannot handle complex sentences or grammar terminology in Ukrainian\n\n"
            "**Instructions in simple English with Ukrainian key terms in bold.**\n"
            "Example: 'Choose the correct form of **мій/моя/моє**'\n\n"
            "**Good activity types:** quiz, fill-in (simple sentences), match-up, "
            "group-sort, true-false, observe, anagram, translate (English→Ukrainian), "
            "error-correction (simple), divide-words, count-syllables, odd-one-out, order.\n"
            f"{video_text}"
        )
    if level == "a1":
        return (
            f"**Level: A1.4+ (Module {module_num}/55) — BEGINNER**\n\n"
            "The learner knows ~500 words, basic grammar, can form sentences.\n\n"
            "**Instructions in simple Ukrainian with English translation in parentheses.**\n"
            "Example: 'Оберіть правильний варіант (Choose the correct option)'\n\n"
            "**All core activity types are appropriate.**\n"
            f"{video_text}"
        )
    if level == "a2":
        return (
            f"**Level: A2 (Module {module_num}/60) — ELEMENTARY**\n\n"
            "The learner knows ~1200 words, understands basic grammar.\n\n"
            "**Instructions in Ukrainian.** No English needed.\n\n"
            "**All core activity types are appropriate.** Include error-correction, "
            "cloze, unjumble for deeper practice.\n"
        )
    base = level.split("-")[0]
    if base in ("hist", "bio", "istorio", "lit", "oes", "ruth"):
        return (
            f"**Level: Seminar ({level.upper()}) — ADVANCED**\n\n"
            "The learner is at B2+ level. Full Ukrainian immersion.\n\n"
            "**Instructions in Ukrainian.** No English.\n\n"
            "**Use seminar activity types:** critical-analysis, essay-response, "
            "source-evaluation, reading, comparative-study, authorial-intent, debate, "
            "etymology-trace, translation-critique, transcription.\n"
        )
    # B1+ default
    return (
        f"**Level: {level.upper()} (Module {module_num})**\n\n"
        "**Instructions in Ukrainian.** All activity types appropriate.\n"
    )


def _build_pedagogy_patterns(plan: dict, level: str) -> str:
    """Load pedagogy pattern library and select patterns matching this module's topic.

    Returns formatted text for injection into the activities prompt.
    Issue: #1051
    """
    patterns_path = PROJECT_ROOT / "docs" / "rules" / "pedagogy-patterns.yaml"
    if not patterns_path.exists():
        return "(No pedagogy pattern library found.)"

    try:
        patterns_data = yaml.safe_load(patterns_path.read_text("utf-8"))
    except Exception:
        return "(Failed to load pedagogy patterns.)"

    all_patterns = patterns_data.get("patterns", {})
    if not all_patterns:
        return "(Pattern library is empty.)"

    # Build search terms from plan
    title = plan.get("title", "").lower()
    # Collect topic keywords from plan's content_outline section titles
    search_terms: set[str] = set()
    search_terms.update(title.split())
    for section in plan.get("content_outline", []):
        section_title = section.get("section", "").lower()
        search_terms.update(section_title.split())
    # Add activity hint focuses
    for hint in plan.get("activity_hints", []):
        focus = hint.get("focus", "").lower()
        search_terms.update(focus.split())

    # Match patterns by topic keywords (bidirectional substring for Cyrillic stems)
    matched: list[tuple[str, dict]] = []
    for pattern_id, pattern in all_patterns.items():
        topics = [t.lower() for t in pattern.get("topics", [])]
        hit = False
        for topic in topics:
            if topic in search_terms:
                hit = True
                break
            # Bidirectional substring: "склади" matches "склад", "складоподіл" matches "склад"
            for term in search_terms:
                if len(term) > 3 and (term in topic or topic in term):
                    hit = True
                    break
            if hit:
                break
        if hit:
            matched.append((pattern_id, pattern))

    if not matched:
        # Fallback: include general patterns
        for pattern_id, pattern in all_patterns.items():
            if pattern_id.startswith("general-"):
                matched.append((pattern_id, pattern))

    if not matched:
        return "(No matching patterns found for this module's topic.)"

    # Format matched patterns
    lines = []
    for pattern_id, pattern in matched:
        # Header with State Standard reference and bilingual name
        std_ref = pattern.get("standard_ref", "")
        назва = pattern.get("назва", "")
        name = pattern.get("name", "")
        header = f"### Pattern: {pattern_id}"
        if std_ref:
            header += f" [{std_ref}]"
        lines.append(header)
        if назва or name:
            lines.append(f"**{назва}** ({name})" if назва and name else f"**{назва or name}**")

        # Exercises
        for ex in pattern.get("exercises", []):
            ex_type = ex.get("type", "?")
            # Support both old (name_uk) and new (назва) format
            ex_name = ex.get("назва", "") or ex.get("name_uk", "")
            focus = ex.get("focus", "")
            focus_uk = ex.get("focus_uk", "")
            focus_text = f"{focus_uk} / {focus}" if focus_uk and focus else (focus_uk or focus)
            lines.append(f"- **{ex_type}** — {ex_name}: {focus_text}")
            example = ex.get("example")
            if example:
                instr = example.get("instruction_uk", "") or example.get("instruction", "")
                if instr:
                    lines.append(f"  - Instruction: *{instr}*")

        # Anti-patterns
        anti_patterns = pattern.get("anti_patterns", [])
        if anti_patterns:
            lines.append("**Anti-patterns (DO NOT generate):**")
            for ap in anti_patterns:
                ap_type = ap.get("type", "?")
                reason = ap.get("reason_uk", "") or ap.get("reason", "")
                lines.append(f"- ❌ {ap_type}: {reason}")

        lines.append("")

    return "\n".join(lines)


def step_activities(
    content_path: Path, level: str, module_num: int, slug: str,
    writer: str = "gemini-tools", max_retries: int = 4,
) -> Path | None:
    """Step 5e: Generate structured activity YAML from plan + prose.

    Separate LLM call that reads the generated prose and plan's activity_hints
    to produce activities/{slug}.yaml with inline + workbook exercises.
    Validates against JSON Schema with retry on parse/validation errors.

    Returns the path to the saved YAML file, or None on failure.
    Issue: #1042
    """
    import json

    import jsonschema

    _log(f"\n{'='*60}")
    _log(f"  Step 5e: ACTIVITIES — Structured YAML generation ({writer})")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return None

    # Load prompt template
    template_path = PHASES_DIR / "v6-activities.md"
    if not template_path.exists():
        _log(f"  ❌ Activity prompt template not found: {template_path}")
        return None

    template = template_path.read_text("utf-8")

    # Load plan
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        _log(f"  ❌ Plan not found: {plan_path}")
        return None
    plan = yaml.safe_load(plan_path.read_text("utf-8"))

    # Load module content
    module_content = content_path.read_text("utf-8")

    # Extract injection markers from prose — writers use various formats:
    # <!-- INJECT_ACTIVITY: quiz-case-identification -->  (strict kebab-case)
    # <!-- INJECT_ACTIVITY: quiz, Case Identification Drill -->  (type + description)
    # <!-- INJECT_ACTIVITY: quiz, Case Identification Drill, 8 items -->  (with count)
    injection_markers = re.findall(
        r"<!--\s*INJECT_ACTIVITY:\s*(.+?)\s*-->", module_content
    )
    if injection_markers:
        markers_text = "\n".join(f"- `<!-- INJECT_ACTIVITY: {m} -->`" for m in injection_markers)
    else:
        markers_text = "(No injection markers found in prose. All activities will go to workbook.)"

    # Build activity hints text
    activity_hints = plan.get("activity_hints", [])
    if activity_hints:
        hints_text = yaml.dump(activity_hints, allow_unicode=True, default_flow_style=False)
    else:
        hints_text = "(No activity_hints in plan. Generate appropriate exercises based on the content.)"

    # Build vocabulary text
    vocab_hints = plan.get("vocabulary_hints") or plan.get("vocabulary") or {}
    vocab_text = yaml.dump(vocab_hints, allow_unicode=True, default_flow_style=False)

    # Build tool instructions
    tool_instructions = _build_tool_instructions(writer)

    # Build level context — critical for activity language and type selection
    level_context = _build_activity_level_context(level, module_num, plan)

    # Build pedagogy patterns — topic-specific exercise recommendations (#1051)
    pedagogy_patterns = _build_pedagogy_patterns(plan, level)

    # Build item minimums table — per-type minItems from schema (prevents retry loops)
    from pipeline.config_tables import get_activity_config, get_item_minimums_table
    item_minimums_table = get_item_minimums_table(level, module_num)

    # Activity count targets from config — inline/workbook split is source of truth.
    # Pass the slug so checkpoint modules route to a1-checkpoint / a2-checkpoint
    # configs (audit demands ITEMS_MIN=10 for those, base a1/a2 only set 6/8).
    activity_config = get_activity_config(level, module_num, slug=slug)
    # Pull min_types_unique from the audit profile so the prompt can quote it
    # without hardcoding level-specific numbers (Gemini b1-activity-fix-review caught
    # hardcoded "5 distinct types" leaking from a B1-only fix into the shared template).
    try:
        from audit.config import get_level_config as _get_audit_cfg
        _module_focus = plan.get("focus") or plan.get("module_focus")
        _audit_profile = _get_audit_cfg(level.upper(), _module_focus)
        min_types_unique = str(_audit_profile.get("min_types_unique", 0))
    except Exception:
        min_types_unique = "0"
    total_target = activity_config.get("TOTAL_TARGET", activity_config.get("ACTIVITY_COUNT_TARGET", "12"))
    inline_min = activity_config.get("INLINE_MIN", "4")
    inline_max = activity_config.get("INLINE_MAX", "6")
    workbook_min = activity_config.get("WORKBOOK_MIN", str(int(total_target) - int(inline_min)))
    workbook_max = activity_config.get("WORKBOOK_MAX", str(int(total_target) + 4))
    inline_allowed = activity_config.get("INLINE_ALLOWED_TYPES", activity_config.get("ALLOWED_ACTIVITY_TYPES", ""))
    workbook_allowed = activity_config.get("WORKBOOK_ALLOWED_TYPES", activity_config.get("ALLOWED_ACTIVITY_TYPES", ""))
    inline_priority = activity_config.get("INLINE_PRIORITY_TYPES", activity_config.get("PRIORITY_TYPES", ""))
    workbook_priority = activity_config.get("WORKBOOK_PRIORITY_TYPES", activity_config.get("PRIORITY_TYPES", ""))
    items_min = activity_config.get("ITEMS_MIN", "6")
    vocab_count_target = activity_config.get("VOCAB_COUNT_TARGET", "25")
    forbidden_types = activity_config.get("FORBIDDEN_ACTIVITY_TYPES", "")
    allowed_types = activity_config.get("ALLOWED_ACTIVITY_TYPES", "")
    required_types = activity_config.get("REQUIRED_TYPES", "")

    # Fill template
    prompt = template
    replacements = {
        "{MODULE_NUM}": str(module_num),
        "{TOPIC_TITLE}": plan.get("title", slug),
        "{LEVEL}": level.lower(),
        "{MODULE_SLUG}": slug,
        "{INJECTION_MARKERS}": markers_text,
        "{PLAN_ACTIVITY_HINTS}": hints_text,
        "{PLAN_VOCABULARY}": vocab_text,
        "{MODULE_CONTENT}": module_content,
        "{TOOL_INSTRUCTIONS}": tool_instructions,
        "{LEVEL_CONTEXT}": level_context,
        "{PEDAGOGY_PATTERNS}": pedagogy_patterns,
        "{ITEM_MINIMUMS_TABLE}": item_minimums_table,
        # New inline/workbook split placeholders (preferred)
        "{TOTAL_TARGET}": total_target,
        "{INLINE_MIN}": inline_min,
        "{INLINE_MAX}": inline_max,
        "{WORKBOOK_MIN}": workbook_min,
        "{WORKBOOK_MAX}": workbook_max,
        "{INLINE_ALLOWED_TYPES}": inline_allowed,
        "{WORKBOOK_ALLOWED_TYPES}": workbook_allowed,
        "{INLINE_PRIORITY_TYPES}": inline_priority,
        "{WORKBOOK_PRIORITY_TYPES}": workbook_priority,
        "{ITEMS_MIN}": items_min,
        "{MIN_TYPES_UNIQUE}": min_types_unique,
        "{VOCAB_COUNT_TARGET}": vocab_count_target,
        "{FORBIDDEN_ACTIVITY_TYPES}": forbidden_types,
        "{ALLOWED_ACTIVITY_TYPES}": allowed_types,
        "{REQUIRED_TYPES}": required_types,
        # Backward compat
        "{ACTIVITY_COUNT_TARGET}": total_target,
        "{PRIORITY_TYPES}": activity_config.get("PRIORITY_TYPES", ""),
    }
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Save prompt for inspection
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = orch_dir / "v6-activities-prompt.md"
    prompt_path.write_text(prompt, "utf-8")
    _log(f"  Prompt saved → {prompt_path.name} ({len(prompt)} chars)")

    # Load JSON Schema for validation
    schema_path = PROJECT_ROOT / "schemas" / "activity-v2.schema.json"
    schema = json.loads(schema_path.read_text("utf-8"))

    # Dispatch with retry loop
    from build.dispatch import CLAUDE_WRITER_TOOLS
    from build.dispatch import dispatch_agent as _dispatch

    if "gemini" in writer:
        base_writer = "gemini-tools"
    elif "codex" in writer:
        base_writer = "codex-tools"
    else:
        base_writer = writer
    error_context = ""

    for attempt in range(1, max_retries + 2):
        _log(f"\n  📝 Activity generation attempt {attempt}/{max_retries + 1}")

        current_prompt = prompt
        if error_context:
            current_prompt = (
                f"<error_from_previous_attempt>\n{error_context}\n"
                "</error_from_previous_attempt>\n\n"
                "Fix the errors above and output the corrected YAML.\n\n"
                + prompt
            )

        # Dispatch — use tools mode for MCP access.
        # All activities use Pro — Flash produced weak exercises (scored 6-7/10).
        if "gemini" in base_writer:
            ok, raw = _dispatch(
                current_prompt, agent="gemini-tools", phase="activities",
                orch_dir=orch_dir, timeout=TIMEOUT_ACTIVITIES, mcp_tools=True,
            )
        elif "codex" in base_writer:
            # Codex uses shell commands for verification, not MCP.
            # workspace-write mode set by dispatch via agent name suffix.
            ok, raw = _dispatch(
                current_prompt, agent="codex-tools", phase="activities",
                orch_dir=orch_dir, timeout=TIMEOUT_ACTIVITIES,
            )
        else:
            # Activities are structured YAML — use fast model, not thinking
            ok, raw = _dispatch(
                current_prompt, agent="claude-tools", phase="activities",
                orch_dir=orch_dir, timeout=TIMEOUT_ACTIVITIES,
                mcp_tools=True, allowed_tools=CLAUDE_WRITER_TOOLS,
                model=CLAUDE_FAMILY.fast,
            )

        if not ok or not raw:
            if _handle_rate_limit_backoff(raw, attempt, max_retries + 1, "activities"):
                raw = ""
                continue
            _log(f"  ❌ Writer returned no output on attempt {attempt}")
            error_context = "Writer returned empty output. Please output valid YAML starting with version: '1.0'."
            continue

        # Reject tiny responses — likely commentary instead of YAML
        if len(raw.strip()) < 2000:
            _log(f"  ❌ Response too short ({len(raw.strip())} chars) — likely commentary, not YAML")
            error_context = (
                "Your response was too short and appears to be commentary instead of YAML. "
                "Output ONLY the raw YAML document. Your first character must be 'version:'. "
                "No markdown, no file paths, no explanation."
            )
            continue

        # Extract YAML from LLM output (strip markdown, commentary, fences)
        clean = raw.strip()
        # Remove markdown code fences
        if clean.startswith("```"):
            first_newline = clean.index("\n")
            clean = clean[first_newline + 1:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        # If output starts with non-YAML (markdown bold, commentary), find the
        # first line starting with a YAML root key or document separator
        if clean and not clean.startswith(("version", "module", "level", "inline", "workbook")):
            # Try to find a YAML root key
            found = False
            for yaml_start_key in ("version:", "module:", "level:", "inline:", "workbook:"):
                idx = clean.find(f"\n{yaml_start_key}")
                if idx != -1:
                    clean = clean[idx + 1:]
                    found = True
                    break
            # Fallback: strip everything before --- document separator
            if not found:
                sep_idx = clean.find("\n---\n")
                if sep_idx != -1:
                    clean = clean[sep_idx + 4:].lstrip("\n")

        # Strip leading YAML document separators (--- or ...)
        while clean.startswith("---"):
            clean = clean[3:].lstrip("\n")

        # Parse YAML
        try:
            data = yaml.safe_load(clean)
        except yaml.YAMLError as e:
            _log(f"  ❌ YAML parse error: {e}")
            error_context = f"YAML parse error: {e}"
            continue

        if not isinstance(data, dict):
            _log(f"  ❌ Expected YAML mapping, got {type(data).__name__}")
            error_context = f"Expected YAML mapping at root, got {type(data).__name__}"
            continue

        # Strip non-schema root keys (LLM commentary like "All 48 words verified...")
        valid_root_keys = {"version", "module", "level", "inline", "workbook"}
        extra_keys = [k for k in data if k not in valid_root_keys]
        for k in extra_keys:
            del data[k]

        # Strip letter-grid and watch-and-repeat before validation —
        # these are replaced deterministically by _inject_abetka_activities()
        # after this step. LLM generates wrong format; abetka injection fixes it.
        _DETERMINISTIC_TYPES = {"letter-grid", "watch-and-repeat"}
        for section in ("inline", "workbook"):
            if section in data and isinstance(data[section], list):
                data[section] = [
                    act for act in data[section]
                    if act.get("type") not in _DETERMINISTIC_TYPES
                ]

        # Re-dump after stripping deterministic types
        clean = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # Auto-fix missing 'title' field — LLMs often skip it but include 'instruction'.
        # Schema requires 'title' on all activity types.
        for section in ("inline", "workbook"):
            if section in data and isinstance(data[section], list):
                for act in data[section]:
                    if isinstance(act, dict) and "title" not in act and "instruction" in act:
                        act["title"] = act["instruction"][:80]

        # Strip parenthetical hints from fill-in sentences.
        # Gemini persistently generates "Я йду в ____ (магазин)." despite prompt rule.
        # Deterministic post-process: remove (hint) so learner must produce from context.
        _HINT_RE = re.compile(r"\s*\([^)]+\)\s*")
        hint_strip_count = 0
        for section in ("inline", "workbook"):
            for act in data.get(section, []) or []:
                if not isinstance(act, dict) or act.get("type") != "fill-in":
                    continue
                for item in act.get("items", []) or []:
                    if not isinstance(item, dict):
                        continue
                    sent = item.get("sentence", "")
                    cleaned = _HINT_RE.sub(" ", sent).strip()
                    # Fix double spaces and trailing space before punctuation
                    cleaned = re.sub(r"\s+", " ", cleaned)
                    cleaned = re.sub(r"\s+([.!?,;:])", r"\1", cleaned)
                    if cleaned != sent:
                        item["sentence"] = cleaned
                        hint_strip_count += 1
        if hint_strip_count:
            _log(f"  🔧 Stripped {hint_strip_count} parenthetical hints from fill-in sentences")
            clean = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # Validate against JSON Schema
        validator = jsonschema.Draft7Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        if errors:
            error_msgs = []
            for err in errors[:10]:  # Cap at 10 to avoid huge retry prompts
                path = ".".join(str(p) for p in err.absolute_path) or "(root)"
                error_msgs.append(f"[{path}] {err.message}")
            error_text = "\n".join(error_msgs)
            _log(f"  ❌ Schema validation failed ({len(errors)} error(s)):")
            for msg in error_msgs[:5]:
                _log(f"    {msg}")
            error_context = f"JSON Schema validation errors:\n{error_text}"
            continue

        # Strip forbidden activity types for this level
        _A1_FORBIDDEN_TYPES = {"translate", "error-correction", "cloze", "unjumble"}
        if level == "a1" and module_num <= 7:
            for section in ("inline", "workbook"):
                if section in data and isinstance(data[section], list):
                    before = len(data[section])
                    data[section] = [
                        act for act in data[section]
                        if act.get("type") not in _A1_FORBIDDEN_TYPES
                    ]
                    removed = before - len(data[section])
                    if removed:
                        _log(f"  🔧 Stripped {removed} forbidden activity type(s) from {section} (A1.1 level restriction)")
            # Re-dump after stripping
            clean = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # Additional semantic checks (inline id uniqueness + existence)
        semantic_errors = _check_activity_semantics(data)
        if semantic_errors:
            error_text = "\n".join(semantic_errors)
            _log(f"  ⚠️  Semantic issues: {len(semantic_errors)}")
            for msg in semantic_errors:
                _log(f"    {msg}")
            # Semantic issues are warnings, not retries

        # Validation passed — save the file
        activities_dir = CURRICULUM_ROOT / level / "activities"
        activities_dir.mkdir(parents=True, exist_ok=True)
        output_path = activities_dir / f"{slug}.yaml"
        output_path.write_text(clean, "utf-8")

        inline_count = len(data.get("inline", []))
        workbook_count = len(data.get("workbook", []))
        _log(f"  ✅ Activities generated: {inline_count} inline + {workbook_count} workbook")
        _log(f"  → {output_path}")

        _save_v6_state(level, slug, "activities")
        return output_path

    _log(f"  ❌ Activity generation failed after {max_retries + 1} attempts")
    return None


def _inject_abetka_activities(activities_path: Path, level: str, slug: str) -> None:
    """Inject letter-grid and watch-and-repeat from l2-uk-direct abetka data.

    Reads abetka-{1,2,3,4}.yaml, finds letters relevant to this module's plan,
    and adds deterministic activities to the workbook. Only runs for A1 modules
    whose plans have letter-grid or watch-and-repeat activity_hints.
    """
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        return

    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    hints = plan.get("activity_hints", [])
    hint_types = {h.get("type") for h in hints}

    if "letter-grid" not in hint_types and "watch-and-repeat" not in hint_types:
        return

    # Load all abetka files
    abetka_dir = PROJECT_ROOT / "curriculum" / "l2-uk-direct" / "a1"
    all_letters = []
    for i in range(1, 5):
        abetka_path = abetka_dir / f"abetka-{i}.yaml"
        if abetka_path.exists():
            abetka = yaml.safe_load(abetka_path.read_text("utf-8"))
            all_letters.extend(abetka.get("letters", []))

    if not all_letters:
        _log("  ⚠️  No abetka data found in l2-uk-direct")
        return

    # Load existing activities — remove LLM-generated letter-grid/watch-and-repeat/observe
    # (deterministic injection replaces them with properly split versions from abetka data)
    # LLMs sometimes generate "observe" instead of "watch-and-repeat" for video hints
    data = yaml.safe_load(activities_path.read_text("utf-8"))
    workbook = [
        act for act in data.get("workbook", [])
        if act.get("type") not in ("letter-grid", "watch-and-repeat", "observe")
    ]

    injected = 0

    # letter-grid: split into multiple activities by abetka group
    if "letter-grid" in hint_types:
        # Group letters by sound type / category
        vowels = [lt for lt in all_letters if lt.get("sound_type") == "vowel"]
        consonants = [lt for lt in all_letters if lt.get("sound_type") == "consonant"]

        # Split consonants into friendly, false friends, new shapes
        friendly = [lt for lt in consonants if lt["upper"] in {"К", "М", "Т"}]
        false_friends = [lt for lt in consonants if lt["upper"] in {"В", "Н", "Р", "С", "Х"}]
        new_shapes = [lt for lt in consonants if lt["upper"] not in {"К", "М", "Т", "В", "Н", "Р", "С", "Х"}]
        # Special letters (soft sign, iotated)
        special = [lt for lt in all_letters if lt["upper"] in {"Ь", "Ї", "Я", "Ю", "Є"}]

        for group_name, group_letters in [
            ("Голосні — Vowels", vowels),
            ("Friendly letters", friendly),
            ("False friends!", false_friends),
            ("New shapes", new_shapes),
            ("Special letters", special),
        ]:
            grid_entries = []
            for lt in group_letters:
                entry = {
                    "upper": lt["upper"],
                    "lower": lt["lower"],
                    "emoji": lt.get("emoji", ""),
                    "key_word": lt.get("key_word", ""),
                }
                if lt.get("sound_type"):
                    entry["sound_type"] = lt["sound_type"]
                grid_entries.append(entry)

            if grid_entries:
                workbook.append({
                    "type": "letter-grid",
                    "instruction": group_name,
                    "letters": grid_entries,
                })
                injected += 1

        if injected > 0:
            _log(f"  📝 Injected {injected} letter-grid activities from abetka")

    # watch-and-repeat: split by abetka file (groups of 7-10 letters)
    if "watch-and-repeat" in hint_types:
        for i in range(1, 5):
            abetka_path = abetka_dir / f"abetka-{i}.yaml"
            if not abetka_path.exists():
                continue
            abetka = yaml.safe_load(abetka_path.read_text("utf-8"))
            video_items = []
            for lt in abetka.get("letters", []):
                video_url = lt.get("pronunciation_video")
                if video_url:
                    video_items.append({
                        "video": video_url,
                        "letter": lt["upper"],
                        "word": lt.get("key_word", ""),
                        "note": lt.get("sentence", ""),
                    })

            if video_items:
                letters_str = ", ".join(item["letter"] for item in video_items)
                workbook.append({
                    "type": "watch-and-repeat",
                    "instruction": f"Watch and repeat: {letters_str}",
                    "items": video_items,
                })
                injected += 1
                _log(f"  📝 Injected watch-and-repeat: {letters_str} ({len(video_items)} videos)")

    if injected > 0:
        data["workbook"] = workbook
        activities_path.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
            "utf-8",
        )


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
    """Step 7: VESUM verification + grammar scope check + VERIFY flag resolution.

    VERIFY flags (<!-- VERIFY: ... -->) are writer-signaled uncertainties.
    They are a POSITIVE signal — the writer was honest about what it doesn't know.
    We extract them, attempt VESUM resolution, save results, and pass unresolved
    flags to the reviewer. They are NOT treated as errors. (Issue: #1018)
    """
    _log(f"\n{'='*60}")
    _log("  Step 7: VERIFY — VESUM + grammar checks")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    text = content_path.read_text("utf-8")
    issues = []

    # --- VERIFY flag resolution (#1018) ---
    # Extract before any other checks. These are non-blocking.
    slug = content_path.stem
    verify_flags = _extract_verify_flags(text)
    if verify_flags:
        _log(f"  📋 Found {len(verify_flags)} VERIFY flag(s) from writer")
        verify_flags = _resolve_verify_flags(verify_flags)
        resolved = [f for f in verify_flags if f["resolved"]]
        unresolved = [f for f in verify_flags if not f["resolved"]]
        if resolved:
            _log(f"  ✅ Resolved {len(resolved)} flag(s) via VESUM:")
            for f in resolved:
                _log(f"    ✓ {f['claim']} — {f['resolution']}")
        if unresolved:
            _log(f"  ℹ️  {len(unresolved)} flag(s) unresolved (will pass to reviewer):")
            for f in unresolved:
                _log(f"    ? {f['claim']}")
        _save_verify_flags(level, slug, verify_flags)

    # Load VESUM whitelist (global + per-module)
    try:
        from tools.vesum_whitelist import load_combined_whitelist
        whitelist = load_combined_whitelist(level, slug)
    except Exception:
        whitelist = set()

    # VESUM word check
    t0 = time.monotonic()
    try:
        from pipeline.screen import _run_vesum_verify
        stats, not_found, _ = _run_vesum_verify(content_path)
        vesum_hits = stats.get("vesum_hits", 0)
        total = stats.get("total", 0)
        # Filter proper nouns and whitelisted words (all modules)
        real_not_found = [
            r for r in not_found
            if not (r.get("original", "")[0:1].isupper() and r.get("source") == "prose")
            and r.get("original", "").lower() not in whitelist
        ]

        # A1 phonetics phase (M01-M03): also skip single letters, phonetic fragments,
        # and syllable parts that appear in letter/sound teaching content.
        if level == "a1" and module_num <= 3:
            _UKRAINIAN_LETTERS = set("абвгґдежзиійклмнопрстуфхцчшщьюяєї")
            _phonetic_fragments = {"йа", "йе", "йі", "йу", "шч", "дж", "дз"}
            real_not_found = [
                r for r in real_not_found
                if r.get("original", "").lower() not in _UKRAINIAN_LETTERS
                and r.get("original", "").lower() not in _phonetic_fragments
                and len(r.get("original", "")) >= 3  # Skip 1-2 char syllable parts
            ]
        if real_not_found:
            _log(f"  ⚠️  VESUM: {len(real_not_found)} word(s) not found:")
            for r in real_not_found[:5]:
                _log(f"    — {r.get('original', '?')}")
            issues.extend(real_not_found)
        else:
            _log(f"  ✅ VESUM: {vesum_hits}/{total} words verified")
        # Log whitelisted words that were filtered
        whitelisted_count = sum(
            1 for r in not_found
            if r.get("original", "").lower() in whitelist
        )
        if whitelisted_count > 0:
            _log(f"  ℹ️  {whitelisted_count} word(s) skipped via whitelist")
    except Exception as e:
        _log(f"  ⚠️  VESUM check skipped: {e}")
    _log(f"  ⏱ VESUM verify: {time.monotonic() - t0:.1f}s")

    # Russicism scan (regex-based on content text)
    t0 = time.monotonic()
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
    _log(f"  ⏱ Russicism scan: {time.monotonic() - t0:.1f}s")

    # IPA check (skip for phonetics M01-M03)
    if not (level == "a1" and module_num <= 3):
        t0 = time.monotonic()
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
        _log(f"  ⏱ IPA check: {time.monotonic() - t0:.1f}s")

    if issues:
        _log(f"\n  ⚠️  Verification found {len(issues)} issue(s) — review recommended")
    else:
        _log("\n  ✅ Verification PASSED — all clean")

    return len(issues) == 0


def _build_vesum_report(content: str, level: str = "", slug: str = "") -> str:
    """Pre-verify all Ukrainian words against VESUM for the reviewer.

    Extracts Ukrainian words (3+ characters) from the content, looks each up
    in the VESUM SQLite database, and returns a structured report. This gives
    the reviewer factual data instead of guessing about word existence.

    Whitelisted words (from global + per-module whitelists) are excluded from
    the "not found" list.
    """
    import sqlite3

    vesum_db = PROJECT_ROOT / "data" / "vesum.db"
    if not vesum_db.exists():
        return ""

    # Extract Ukrainian words (3+ chars to skip particles/prepositions)
    words = set(re.findall(r"\b[а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ]{2,}\b", content))
    if not words:
        return ""

    # Load whitelist
    whitelist: set[str] = set()
    if level and slug:
        try:
            from tools.vesum_whitelist import load_combined_whitelist
            whitelist = load_combined_whitelist(level, slug)
        except Exception:
            pass

    db = sqlite3.connect(str(vesum_db))
    try:
        verified = []
        not_found = []
        for word in sorted(words):
            if word.lower() in whitelist:
                continue
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

    # Only include verified count — listing 60+ ✓ words is noise
    if verified:
        report_lines.append(
            f"All {len(verified)} other words are confirmed to exist in VESUM."
        )
        report_lines.append("")

    report_lines.append("</vesum_verification>")
    return "\n".join(report_lines)


def step_review(content_path: Path, level: str, module_num: int,
                slug: str, writer: str = "claude",
                reviewer_override: str | None = None) -> tuple[bool, float, str]:
    """Step 8: Cross-agent adversarial review.

    If Claude wrote → Gemini reviews (and vice versa).
    Returns (passed, score, review_text).
    """
    _log(f"\n{'='*60}")
    _log("  Step 8: REVIEW — Cross-agent adversarial review")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False, 0.0, ""

    # Load review template
    template_path = PHASES_DIR / "v6-review.md"
    if not template_path.exists():
        _log(f"  ❌ Review template not found: {template_path}")
        return False, 0.0, ""

    template = template_path.read_text("utf-8")

    # Load plan and content
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan_content = plan_path.read_text("utf-8") if plan_path.exists() else ""
    plan = yaml.safe_load(plan_content) if plan_content else {}
    raw_content = content_path.read_text("utf-8")

    # .md files now contain ONLY prose (no TAB markers, no enrichment artifacts).
    # Strip any legacy TAB markers if still present (backward compat during migration).
    generated_content = raw_content
    if "<!-- TAB:Словник -->" in generated_content:
        generated_content = generated_content[:generated_content.index("<!-- TAB:Словник -->")].strip()
    generated_content = generated_content.replace("<!-- TAB:Урок -->", "").strip()
    generated_content = re.sub(r'\n{3,}', '\n\n', generated_content).strip()

    # Calculate deterministic word count — injected OUTSIDE content block
    prose_words = len(re.sub(r":::.*?:::", "", generated_content, flags=re.DOTALL).split())

    # Build review prompt
    if "claude" in writer:
        writer_model = "Claude"
    elif "codex" in writer:
        writer_model = "Codex"
    else:
        writer_model = "Gemini"
    prompt = template
    replacements = {
        "{MODULE_NUM}": str(module_num),
        "{TOPIC_TITLE}": plan.get("title", slug),
        "{LEVEL}": level.upper(),
        "{PHASE}": plan.get("phase", ""),
        "{WRITER_MODEL}": writer_model,
        "{WORD_TARGET}": str(plan.get("word_target", 1200)),
        "{WORD_CEILING}": str(int(plan.get("word_target", 1200) * 1.5)),
        "{WORD_COUNT}": str(prose_words),
        "{PLAN_CONTENT}": plan_content,
        "{GENERATED_CONTENT}": generated_content,
    }
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    # Inject VESUM verification data so the reviewer has facts, not guesses
    vesum_report = _build_vesum_report(generated_content, level=level, slug=slug)
    if vesum_report:
        prompt = prompt + "\n\n" + vesum_report
        _log(f"  VESUM pre-verification: injected ({len(vesum_report)} chars)")

    # Inject VERIFY flags from writer (#1018)
    # Unresolved flags are passed to the reviewer for human-quality verification.
    # Resolved flags are shown for context. VERIFY flags are a POSITIVE signal.
    flags_path = CURRICULUM_ROOT / level / "orchestration" / slug / "verify-flags.yaml"
    if flags_path.exists():
        try:
            all_flags = yaml.safe_load(flags_path.read_text("utf-8"))
            if all_flags:
                unresolved = [f for f in all_flags if not f.get("resolved")]
                resolved = [f for f in all_flags if f.get("resolved")]
                flag_inject = (
                    "\n\n## Writer Uncertainty Flags (VERIFY)\n\n"
                    "The writer honestly flagged these items as uncertain. "
                    "This is a POSITIVE signal — it means the writer was careful "
                    "rather than guessing. Please verify each claim:\n\n"
                )
                if unresolved:
                    flag_inject += "**Unresolved (needs your verification):**\n"
                    for f in unresolved:
                        flag_inject += f"- {f['claim']}\n"
                    flag_inject += "\n"
                if resolved:
                    flag_inject += "**Auto-resolved via VESUM (for context):**\n"
                    for f in resolved:
                        flag_inject += f"- {f['claim']} -- {f['resolution']}\n"
                    flag_inject += "\n"
                prompt += flag_inject
                _log(f"  VERIFY flags injected: {len(unresolved)} unresolved, {len(resolved)} resolved")
        except Exception:
            pass  # Non-blocking

    # Determine reviewer BEFORE building tool instructions (bug fix: tool prefix
    # must match the actual reviewer, not the cross-agent default)
    if reviewer_override:
        if "claude" in reviewer_override:
            reviewer = "claude"
        elif "codex" in reviewer_override:
            reviewer = "codex"
        else:
            reviewer = "gemini"
    else:
        # Cross-agent review: writer → opposite family reviews.
        # Gemini writes → Codex reviews (per user directive: Claude is for coding, not batch reviewing).
        # Claude writes → Gemini reviews.
        # Codex writes → Gemini reviews.
        if writer in ("claude", "claude-tools"):
            reviewer = "gemini"
        elif writer in ("gemini", "gemini-tools"):
            reviewer = "codex"
        else:
            reviewer = "gemini"

    # Build tool instructions for the reviewer.
    # Codex uses shell-out commands; Claude/Gemini use MCP tool references.
    if "codex" in reviewer:
        review_tools = _build_tool_instructions("codex-tools")
    else:
        p = get_family(reviewer).tool_prefix
        review_tools = (
            "\n\n## Verification Tools (MCP)\n\n"
            "You have MCP tools to VERIFY claims in the content. Use them to cite evidence:\n\n"
            "**Core Verification:**\n"
            f"- `{p}verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)\n"
            f"- `{p}verify_lemma` — full declension/conjugation for a lemma\n"
            f"- `{p}search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)\n"
            f"- `{p}query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.\n"
            f"- `{p}query_pravopys` — verify orthography rules (Правопис 2019)\n\n"
            "**Content Quality:**\n"
            f"- `{p}query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)\n"
            f"- `{p}search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)\n"
            f"- `{p}search_etymology` — historical forms, etymology (Грінченко, 67K entries)\n"
            f"- `{p}search_idioms` — verify idioms are authentic Ukrainian (25K entries)\n"
            f"- `{p}search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)\n"
            f"- `{p}query_grac` — check collocations and frequency in GRAC corpus (2B tokens)\n\n"
            "**Reference:**\n"
        f"- `{p}search_text` — check how textbooks teach the topic (Grades 1-11)\n"
        f"- `{p}search_literary` — verify literary references against primary sources\n"
        f"- `{p}query_wikipedia` — fact-check historical/cultural claims\n\n"
        "**Evidence standard:** A review that says \"this might be a Russicism\" is WEAK. "
        "A review that says \"`search_style_guide` confirms 'приймати участь' is a calque — "
        "correct form: 'брати участь'\" is STRONG. Cite tool results.\n"
    )
    prompt = prompt + review_tools

    # Save review prompt
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    review_prompt_path = orch_dir / "v6-review-prompt.md"
    review_prompt_path.write_text(prompt, "utf-8")

    # Dispatch to reviewer (cross-agent: writer's opposite)
    from build.dispatch import CLAUDE_REVIEWER_TOOLS
    from build.dispatch import dispatch_agent as _dispatch

    # reviewer already determined above (for tool prefix). Set reviewer_agent.
    if reviewer_override:
        reviewer_agent = reviewer_override
    elif reviewer == "gemini":
        reviewer_agent = "gemini-tools"
    elif reviewer == "codex":
        reviewer_agent = "codex-tools"
    else:
        reviewer_agent = "claude-tools"
    _log(f"  Reviewer: {reviewer_agent} (writer was {writer})")

    # Dispatch review — single call, no probe, no retry loop.
    if reviewer == "gemini":
        from batch_gemini_config import GEMINI_REVIEW_MODEL

        review_timeout = 900  # 15 min — generous for a ~30K prompt
        ok, raw = _dispatch(
            prompt, agent=reviewer_agent, phase="review", orch_dir=orch_dir,
            timeout=review_timeout, mcp_tools=True,
            model=GEMINI_REVIEW_MODEL,
        )
        if not ok or not raw:
            _log("  ❌ Gemini review failed — single attempt, no retry")
    elif reviewer == "codex":
        # Codex reviews via shell-out tools, not MCP. The tool instructions
        # were already injected into the prompt above. Dispatch without
        # mcp_tools so the codex adapter runs in workspace-write mode
        # (needed for shell-out tool access).
        review_timeout = 900
        ok, raw = _dispatch(
            prompt, agent=reviewer_agent, phase="review", orch_dir=orch_dir,
            timeout=review_timeout, mcp_tools=False,
        )
        if not ok or not raw:
            _log("  ❌ Codex review failed — single attempt, no retry")
    else:
        from batch_gemini_config import CLAUDE_MODEL_FINAL_REVIEW
        ok, raw = _dispatch(
            prompt, agent=reviewer_agent, phase="review", orch_dir=orch_dir,
            timeout=TIMEOUT_REVIEW_CLAUDE, mcp_tools=True, allowed_tools=CLAUDE_REVIEWER_TOOLS,
            model=CLAUDE_MODEL_FINAL_REVIEW,
        )

    if not ok or not raw:
        _log("  ❌ Reviewer returned no output")
        return False, 0.0, ""

    # Save review output — versioned + latest symlink
    review_dir = CURRICULUM_ROOT / level / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    # Determine round number from existing versioned files
    existing = sorted(review_dir.glob(f"{slug}-review-r*.md"))
    round_num = len(existing) + 1
    versioned_path = review_dir / f"{slug}-review-r{round_num}.md"
    versioned_path.write_text(raw, "utf-8")

    # Also save as the "latest" for backward compatibility
    review_path = review_dir / f"{slug}-review.md"
    review_path.write_text(raw, "utf-8")
    _log(f"  Review saved → {versioned_path.name} (round {round_num})")

    # Save structured findings to orchestration for aggregation (#1027)
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    _save_structured_findings(raw, orch_dir, round_num)

    parsed = _parse_review_result(raw)
    score = parsed.score

    all_score_matches = list(re.finditer(r"\|\s*\d+\.\s*[^|]+\|\s*(\d+)/10\s*\|", raw))
    if len(all_score_matches) > len(parsed.raw_scores):
        _log(
            f"  ⚠️  Parsed {len(all_score_matches)} scores — trimming to first {len(parsed.raw_scores)} "
            "(duplicate table in review)"
        )

    if parsed.raw_scores:
        _log(f"  Raw scores: {parsed.raw_scores}")
        if len(parsed.raw_scores) < 9:
            _log(f"  ⚠️  Only {len(parsed.raw_scores)}/9 dimensions parsed — score normalized")
        _log(f"  Weighted score (calculated): {score}/10")
    else:
        _log("  ⚠️  Could not parse any dimension scores")

    score_pass = score >= 8.0
    severity_pass = parsed.verdict == "PASS"

    for dim in parsed.parsed_scores:
        dim_score = dim.get("score", 10)
        evidence = dim.get("evidence", "").lower()
        error_keywords = (
            "error", "incorrect", "wrong", "mistake", "factual",
            "помилк", "невірн", "хибн", "contradictory",
        )
        if dim_score < REVIEW_TARGET_SCORE and any(kw in evidence for kw in error_keywords):
            dim_name = dim.get("name", "?")
            _log(f"  ⚠️  Dimension floor: {dim_name} = {dim_score}/10 with identified errors")

    passed = parsed.passed

    icon = "✅" if passed else "❌"
    floor_msg = " (dimension floor FAIL)" if parsed.dim_floor_fail else ""
    _log(
        f"  {icon} Review: {score}/10 (score gate: {'✅' if score_pass else '❌'}) — "
        f"{parsed.verdict} (severity gate: {'✅' if severity_pass else '❌'}){floor_msg}"
    )
    emit_event("review_score", level=level, slug=slug, round=round_num, score=score)

    return passed, score, raw


def _parse_review_fixes(review_text: str) -> list[dict]:
    """Parse <fixes> block from reviewer output into find/replace pairs.

    Expected format:
    <fixes>
    - find: "exact text"
      replace: "corrected text"
    </fixes>

    Returns list of dicts with 'find' and 'replace' keys.
    """
    # Strip markdown code fences that Gemini sometimes wraps around the review
    text = review_text
    if text.strip().startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text.strip())
        text = re.sub(r"\n?```\s*$", "", text)

    match = re.search(r"<fixes>\s*\n(.*?)</fixes>", text, re.DOTALL)
    if not match:
        return []

    fixes_text = match.group(1)
    try:
        fixes = yaml.safe_load(fixes_text)
        if isinstance(fixes, list):
            valid = []
            for fix in fixes:
                if not isinstance(fix, dict):
                    continue
                if "content" in fix and "replace" not in fix:
                    fix["replace"] = fix.pop("content")
                if "find" in fix and "replace" in fix:
                    valid.append(fix)
            return valid
    except Exception:
        pass
    return []


def _apply_review_fixes(review_text: str, content_path: Path) -> tuple[bool, int]:
    """Apply <fixes> find/replace pairs from reviewer to content.

    Returns (success, count_of_fixes_applied).
    Targeted fixes are better than section rewrites — they change
    only what the reviewer flagged, preserving everything else.

    The .md file now contains only prose (no TAB markers, no enrichment).
    The reviewer sees the same content. Stress marks may be present.

    Reviewed by Gemini (2026-03-28) — fixed: stress offset calculation,
    dangling combining chars, find_str stress stripping.
    Issue: #1124 — simplified after enrichment moved to publish.
    """
    STRESS_MARK = "\u0301"

    fixes = _parse_review_fixes(review_text)
    if not fixes:
        return False, 0

    content = content_path.read_text("utf-8")
    applied = 0

    for fix in fixes:
        find_str = fix.get("find", "")
        replace_str = fix.get("replace", "")
        if not find_str or find_str == replace_str:
            continue

        # Strip stress marks from find_str too — reviewer might include them
        find_unstressed = find_str.replace(STRESS_MARK, "")
        replace_unstressed = replace_str  # Keep replacement as-is

        # Try exact match first (handles no-stress-mark case)
        if find_unstressed in content:
            content = content.replace(find_unstressed, replace_unstressed, 1)
            applied += 1
            _log(f"  ✅ Fix applied: '{find_unstressed[:50]}...'")
            continue

        # Try whitespace-normalized match for multi-line fixes
        # Reviewer may output \n\n where content has \n, or vice versa
        # IMPORTANT: only normalize for MATCHING — apply to ORIGINAL content
        if "\n" in find_unstressed:
            import re as _re
            find_norm = _re.sub(r"\n\s*\n", "\n", find_unstressed).strip()
            content_norm = _re.sub(r"\n\s*\n", "\n", content).strip()
            if find_norm in content_norm:
                # Find the match position in normalized space, then locate the
                # corresponding span in the original content by scanning for the
                # first/last lines of the find string.
                find_lines = [l for l in find_unstressed.strip().splitlines() if l.strip()]
                if find_lines:
                    first_line = find_lines[0].strip()
                    last_line = find_lines[-1].strip()
                    start = content.find(first_line)
                    end = content.find(last_line, start) + len(last_line) if start >= 0 else -1
                    if start >= 0 and end > start:
                        content = content[:start] + replace_unstressed + content[end:]
                        applied += 1
                        _log(f"  ✅ Fix applied (whitespace-normalized): '{find_unstressed[:50]}...'")
                        continue

        # Try stress-mark-aware match: strip stress from content for matching
        content_unstressed = content.replace(STRESS_MARK, "")
        if find_unstressed in content_unstressed:
            # Map from unstressed position to stressed position
            pos_unstressed = content_unstressed.index(find_unstressed)

            # Walk through stressed content to find the real start position
            stressed_idx = 0
            unstressed_idx = 0
            while unstressed_idx < pos_unstressed and stressed_idx < len(content):
                if content[stressed_idx] != STRESS_MARK:
                    unstressed_idx += 1
                stressed_idx += 1
            start = stressed_idx

            # Find the end: walk through len(find_unstressed) base characters
            end = start
            base_count = 0
            while end < len(content) and base_count < len(find_unstressed):
                if content[end] != STRESS_MARK:
                    base_count += 1
                end += 1
            # Consume any trailing stress mark attached to the last character
            if end < len(content) and content[end] == STRESS_MARK:
                end += 1
            content = content[:start] + replace_unstressed + content[end:]
            applied += 1
            _log(f"  ✅ Fix applied (stress-aware): '{find_unstressed[:50]}...'")
            continue

        # Try punctuation-normalized regex match (handles « » vs " ", and - vs —)
        import re as _re
        find_regex = _re.escape(find_unstressed)
        # allow any quote type
        find_regex = _re.sub(r'(?:\\["\'«»]|["\'«»])', r'["\'«»]', find_regex)
        # allow any dash/hyphen
        find_regex = _re.sub(r'(?:\\[\-—–]|[-—–])', r'[-—–]', find_regex)

        matches = list(_re.finditer(find_regex, content_unstressed))
        if len(matches) == 1:
            match = matches[0]

            # Map unstressed match bounds back to stressed content
            pos_unstressed_start = match.start()
            pos_unstressed_end = match.end()

            stressed_idx = 0
            unstressed_idx = 0
            while unstressed_idx < pos_unstressed_start and stressed_idx < len(content):
                if content[stressed_idx] != STRESS_MARK:
                    unstressed_idx += 1
                stressed_idx += 1
            start = stressed_idx

            while unstressed_idx < pos_unstressed_end and stressed_idx < len(content):
                if content[stressed_idx] != STRESS_MARK:
                    unstressed_idx += 1
                stressed_idx += 1
            end = stressed_idx

            if end < len(content) and content[end] == STRESS_MARK:
                end += 1

            content = content[:start] + replace_unstressed + content[end:]
            applied += 1
            _log(f"  ✅ Fix applied (punctuation-aware): '{find_unstressed[:50]}...'")
            continue

        _log(f"  ⚠️  Fix not matched: '{find_unstressed[:60]}...'")

    if applied > 0:
        content_path.write_text(content, "utf-8")
        _log(f"  📝 {applied}/{len(fixes)} fixes applied to content")

    return applied > 0, applied


def _get_knowledge_packet_for_rewrite(level: str, slug: str) -> str:
    """Get knowledge packet for section rewrites.

    Contains wiki articles + discovery data (compiled knowledge).
    Returns empty string if no packet exists.
    """
    packet_path = CURRICULUM_ROOT / level / "research" / f"{slug}-knowledge-packet.md"
    if packet_path.exists():
        content = packet_path.read_text("utf-8")
        # Cap at 30K to leave room in the rewrite prompt
        if len(content) > 30_000:
            content = content[:30_000] + "\n\n*(truncated)*"
        _log(f"  📚 Knowledge packet loaded for rewrite ({len(content):,} chars)")
        return content
    return ""


def _rewrite_weak_sections(
    review_text: str, content_path: Path, level: str, slug: str,
    writer: str = "claude",
    verification_text: str = "",
) -> bool:
    """Rewrite entire sections that scored poorly — not find/replace.

    Find/replace breaks prose flow. Section rewriting preserves context
    because the rewriter sees the full section and rewrites holistically.

    Returns True if any sections were rewritten.
    """

    from build.dispatch import CLAUDE_WRITER_TOOLS
    from build.dispatch import dispatch_agent as _dispatch

    # Parse which sections scored <9 with error evidence
    weak_sections: list[dict] = []
    full_score_pattern = re.compile(r"\|\s*(\d+)\.\s*([^|]+)\|\s*(\d+)/10\s*\|([^|]*)\|")
    for m in full_score_pattern.finditer(review_text):
        dim_score = int(m.group(3))
        evidence = m.group(4).strip()
        if dim_score < 9:
            weak_sections.append({
                "dimension": m.group(2).strip(),
                "score": dim_score,
                "evidence": evidence,
            })

    if not weak_sections:
        return False

    # Extract findings for more detail
    findings_section = re.search(r"## Findings\s*\n(.*?)(?=\n## |\Z)", review_text, re.DOTALL)
    findings_text = findings_section.group(1).strip() if findings_section else ""

    # Read content — .md files now contain only prose (no TAB markers)
    content = content_path.read_text("utf-8")
    body = content.replace("<!-- TAB:Урок -->", "").strip()  # Legacy compat
    if "<!-- TAB:Словник -->" in body:
        body = body[:body.index("<!-- TAB:Словник -->")].strip()

    if len(body) < 200:
        _log(f"  ❌ Body too short for rewrite ({len(body)} chars)")
        return False

    original_word_count = len(body.split())

    # Build the rewrite prompt
    issues_summary = "\n".join(
        f"- {s['dimension']} ({s['score']}/10): {s['evidence'][:300]}"
        for s in weak_sections
    )

    # Load knowledge packet for grounding
    packet_path = CURRICULUM_ROOT / level / "research" / f"{slug}-knowledge-packet.md"
    packet_text = ""
    if packet_path.exists():
        packet_text = packet_path.read_text("utf-8")
        if len(packet_text) > 5000:
            packet_text = packet_text[:5000] + "\n... (truncated)"

    # Load pre-verified facts
    if not verification_text:
        verify_path = CURRICULUM_ROOT / level / "orchestration" / slug / "pre-verify-results.md"
        if verify_path.exists():
            verification_text = verify_path.read_text("utf-8")

    # Load persona for consistent voice
    plan_path_for_persona = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    persona_text = ""
    if plan_path_for_persona.exists():
        plan_for_persona = yaml.safe_load(plan_path_for_persona.read_text("utf-8"))
        persona = plan_for_persona.get("persona", {})
        if isinstance(persona, dict) and persona.get("voice"):
            persona_text = f"\n**Your identity: {persona['voice']}.**"
            if persona.get("role"):
                persona_text += f" Persona: *{persona['role']}*."
            persona_text += " Maintain this voice in your fixes.\n"

    prompt = f"""Fix ONLY the specific errors listed below. Do NOT rewrite from scratch.
{persona_text}
## CRITICAL RULE: Do NOT invent new claims or change text that wasn't flagged.

The review found specific errors. Fix THOSE errors ONLY. Every sentence you don't
touch is a sentence that stays correct. If you change something the review didn't
flag, you risk introducing NEW errors — and the score will DROP instead of improving.

## Errors to Fix
{issues_summary}

{f"Detailed findings:{chr(10)}{findings_text[:3000]}" if findings_text else ""}

## Pre-Verified Facts (GROUND TRUTH — use these for corrections)

These facts were verified by MCP tools (VESUM, textbooks, Правопис). When fixing
errors, use ONLY information from these verified facts. Do NOT invent phonetic
claims, grammar rules, or cultural facts that aren't here.

<pre_verified_facts>
{verification_text if verification_text else "(No pre-verified facts available)"}
</pre_verified_facts>

{f"## Knowledge Packet (textbook excerpts){chr(10)}<knowledge_packet>{chr(10)}{packet_text}{chr(10)}</knowledge_packet>" if packet_text else ""}

{_get_knowledge_packet_for_rewrite(level, slug)}

## Current Module ({original_word_count} words)

{body}

## Rules

1. Output the COMPLETE module — every section, every paragraph, every example.
2. Your output must be {original_word_count} words MINIMUM. Do NOT summarize or shorten.
3. Fix ONLY the errors listed above. Do NOT change text that wasn't flagged as an error.
4. Keep all ## section headings exactly as they appear above.
5. Keep all <!-- INJECT_ACTIVITY: --> markers in their current positions.
6. Do NOT invent phonetic claims. If the pre-verified facts don't confirm a claim, remove it.
7. Do NOT add new content that isn't in the knowledge packet or pre-verified facts.
7. Use warm, direct tone. No "Let us..." or "You have now mastered..." patterns.
8. Do NOT add preamble, explanation, or commentary. Start directly with ## heading.
"""

    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)

    # Backup content before rewrite — restore if validation fails
    backup_content = content_path.read_text("utf-8")

    # Rewrite with same family as writer (it wrote the content, can fix it)
    if "claude" in writer:
        ok, raw = _dispatch(
            prompt, agent="claude-tools", phase="section-rewrite",
            orch_dir=orch_dir, timeout=TIMEOUT_WRITE,
            mcp_tools=True, allowed_tools=CLAUDE_WRITER_TOOLS,
        )
    elif "codex" in writer:
        ok, raw = _dispatch(
            prompt, agent="codex-tools", phase="section-rewrite",
            orch_dir=orch_dir, timeout=TIMEOUT_WRITE,
        )
    else:
        ok, raw = _dispatch(
            prompt, agent="gemini-tools", phase="section-rewrite",
            orch_dir=orch_dir, timeout=TIMEOUT_WRITE, mcp_tools=True,
        )

    if not ok or not raw:
        _log("  ❌ Section rewrite failed — no output, keeping original")
        content_path.write_text(backup_content, "utf-8")
        return False

    # Strip any preamble/changes table before first ## heading
    first_h2 = raw.find("## ")
    if first_h2 > 0:
        raw = raw[first_h2:]
    # Also strip any "## Changes Made" or "## Changes" table that Claude likes to prepend
    if raw.startswith("## Changes"):
        next_h2 = raw.find("\n## ", 5)
        if next_h2 > 0:
            raw = raw[next_h2 + 1:]

    # Validate: section count
    original_h2s = re.findall(r"^## .+", body, re.MULTILINE)
    rewrite_h2s = re.findall(r"^## .+", raw, re.MULTILINE)
    if len(rewrite_h2s) != len(original_h2s):  # Gemini review: must be exact, plans are immutable
        _log(f"  ❌ Rewrite dropped sections ({len(original_h2s)} → {len(rewrite_h2s)}), rejecting — restoring original")
        content_path.write_text(backup_content, "utf-8")
        return False

    # Validate: word count (reject if <90% of original — means it was truncated)
    rewrite_words = len(raw.split())
    min_words = int(original_word_count * 0.9)  # Gemini review: 70% was too lenient
    if rewrite_words < min_words:
        _log(f"  ❌ Rewrite too short ({rewrite_words} words, need ≥{min_words}), rejecting — restoring original")
        content_path.write_text(backup_content, "utf-8")
        return False

    # Write the rewritten prose-only content (no TAB markers — #1124)
    content_path.write_text(raw.strip() + "\n", "utf-8")

    _log(f"  ✅ Section rewrite complete ({len(raw.split())} words, {len(rewrite_h2s)} sections)")
    return True


def _strip_dsl_blocks(text: str) -> tuple[str, int]:
    """Strip legacy DSL exercise blocks (:::quiz, :::fill-in, etc.) from content.

    Used when activities YAML exists — the YAML is the source of truth,
    so inline DSL exercises would create duplicates.

    Returns (stripped_text, count_stripped).
    """
    # Match :::type ... ::: blocks (DSL exercise format)
    # Match both V6 bare types (:::quiz) and legacy format (:::exercise[type])
    dsl_pattern = re.compile(
        r"^:::(?:quiz|fill-in|match-up|group-sort|true-false|exercise\[.*?\])\b.*?^:::$",
        re.MULTILINE | re.DOTALL,
    )
    stripped, count = dsl_pattern.subn("", text)
    # Clean up multiple blank lines left behind
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped, count


def _convert_tab_markers(content: str) -> str:
    """Convert <!-- TAB:name --> markers to <Tabs>/<TabItem> MDX components.

    Input:  <!-- TAB:Урок -->\n...content...\n<!-- TAB:Словник -->\n...
    Output: <Tabs syncKey="module-tab">
            <TabItem label="Урок">\n...content...\n</TabItem>
            <TabItem label="Словник">\n...
    """

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


def _load_activities(level: str, slug: str) -> dict | None:
    """Load activities/{slug}.yaml if it exists. Returns parsed dict or None."""
    activities_path = CURRICULUM_ROOT / level / "activities" / f"{slug}.yaml"
    if not activities_path.exists():
        return None
    try:
        data = yaml.safe_load(activities_path.read_text("utf-8"))
        if not isinstance(data, dict):
            return None
        return data
    except Exception as e:
        _log(f"  ⚠️  Failed to parse activities YAML: {e}")
        return None


def _inject_inline_activities(
    mdx_content: str, inline_activities: list[dict],
) -> tuple[str, list[dict]]:
    """Replace <!-- INJECT_ACTIVITY: {id} --> markers with rendered JSX.

    Returns (updated_content, unmatched_activities).
    Unmatched activities (marker not found in prose) are returned for
    fallback into the Зошит tab.
    """
    import re

    from build.activity_renderer import render_activity_to_jsx

    unmatched = []
    for act in inline_activities:
        act_id = act.get("id", "")
        # LLMs often inject extra text into the marker (e.g. <!-- INJECT_ACTIVITY: id, hint text -->)
        marker_pattern = re.compile(rf"<!--\s*INJECT_ACTIVITY:\s*{re.escape(act_id)}\b.*?-->", re.IGNORECASE)

        if marker_pattern.search(mdx_content):
            jsx = render_activity_to_jsx(act)
            # Use lambda to prevent re.sub from interpreting backslash
            # sequences (e.g. \n) in the JSX replacement string.
            # json.dumps produces \\n but re.sub string replacement
            # converts it back to a literal newline, breaking MDX parsing.
            mdx_content = marker_pattern.sub(lambda _, r=jsx: r, mdx_content, count=1)
        else:
            unmatched.append(act)

    return mdx_content, unmatched


def _build_workbook_tab(workbook_activities: list[dict]) -> str:
    """Render all workbook activities as JSX for the Зошит tab."""
    from build.activity_renderer import render_activity_to_jsx

    if not workbook_activities:
        return (
            ":::note\n"
            "Розши\u0301рені впра\u0301ви для цього\u0301 уро\u0301ку ще в розро\u0301бці.\n\n"
            "Advanced exercises for this module are in development. Check back soon!\n"
            ":::"
        )

    parts = []
    for act in workbook_activities:
        jsx = render_activity_to_jsx(act)
        parts.append(jsx)
        parts.append("")  # blank line between activities

    return "\n".join(parts)


def _safe_load_plan(plan_path: Path) -> dict:
    """Load a plan YAML file, returning empty dict on any error."""
    if not plan_path.exists():
        return {}
    try:
        return yaml.safe_load(plan_path.read_text("utf-8")) or {}
    except Exception:
        return {}


def _load_pidruchnyk_urls(path: Path = PIDRUCHNYK_URLS_PATH) -> dict[str, str]:
    """Load source_file -> pidruchnyk.com.ua URL mapping."""
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text("utf-8")) or {}
    except Exception:
        return {}
    return {
        str(source_file): str(url)
        for source_file, url in data.items()
        if isinstance(source_file, str) and isinstance(url, str) and url.strip()
    }


def _extract_source_year(source_file: str) -> int | None:
    """Extract textbook year from a source_file suffix."""
    match = re.search(r"-(\d{4})(?:-\d)?$", source_file)
    return int(match.group(1)) if match else None


def _resolve_source_author(source_file: str) -> str:
    """Resolve a Ukrainian surname label from the source_file."""
    for key, label in _PIDRUCHNYK_AUTHOR_NAMES.items():
        if key in source_file:
            return label
    parts = source_file.split("-")
    if len(parts) >= 4:
        return parts[3].capitalize()
    return source_file


def _resolve_source_subject(source_file: str) -> str:
    """Map a source_file to a display subject."""
    if "ukrlit" in source_file or "ukrajinska-literatura" in source_file:
        return "Українська література"
    if "istorija-ukrajiny" in source_file or "istoriya-ukr" in source_file or "istoria-ukr" in source_file:
        return "Історія України"
    if "istori" in source_file:
        return "Історія"
    return "Українська мова"


def _build_source_display_name(source_file: str) -> str:
    """Build a textbook display label from the source_file."""
    grade_match = re.match(r"(\d+)-klas", source_file)
    grade = grade_match.group(1) if grade_match else "?"
    year = _extract_source_year(source_file)
    author = _resolve_source_author(source_file)
    subject = _resolve_source_subject(source_file)
    if year is not None:
        return f"{author}. {subject}, {grade} клас ({year})"
    return f"{author}. {subject}, {grade} клас"


def _normalize_author_label(value: str) -> str:
    """Normalize author labels for lightweight title matching."""
    return re.sub(r"\s+", " ", value.strip().lower())


def _infer_reference_subject(title: str, notes: str) -> str:
    """Infer the referenced textbook subject from title/notes text."""
    text = f"{title} {notes}".lower()
    if any(token in text for token in ("літератур", "literature", "ukrlit")):
        return "Українська література"
    if any(token in text for token in ("істор", "history", "суспіль")):
        return "Історія"
    return "Українська мова"


def _parse_textbook_reference(ref: str | dict) -> dict | None:
    """Extract author/grade/year/subject metadata from a plan reference."""
    if isinstance(ref, str):
        title = ref.strip()
        notes = ""
    elif isinstance(ref, dict):
        title = str(ref.get("title", "")).strip()
        notes = str(ref.get("notes") or ref.get("note") or "").strip()
    else:
        return None

    if not title:
        return None

    grade_match = re.search(r"\bGrade\s+(\d+)\b|\b(\d+)\s*клас\b", title, flags=re.IGNORECASE)
    if not grade_match:
        return None
    grade = int(grade_match.group(1) or grade_match.group(2))

    author_match = re.match(r"([A-Za-zА-Яа-яЇїІіЄєҐґ'’`-]+)", title)
    if not author_match:
        return None
    author = author_match.group(1).replace("’", "'")
    year_match = re.search(r"\b(20\d{2})\b", title)

    return {
        "title": title,
        "notes": notes,
        "author": _normalize_author_label(author),
        "grade": grade,
        "year": int(year_match.group(1)) if year_match else None,
        "subject": _infer_reference_subject(title, notes),
    }


def _load_textbook_source_index(db_path: Path = SOURCES_DB_PATH) -> list[dict]:
    """Build a distinct source_file index for textbook reference resolution."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT DISTINCT source_file, grade, author FROM textbooks ORDER BY source_file"
        ).fetchall()
    finally:
        conn.close()

    index = []
    for source_file, grade, author in rows:
        index.append(
            {
                "source_file": str(source_file),
                "grade": int(grade) if str(grade).isdigit() else None,
                "year": _extract_source_year(str(source_file)),
                "author": _normalize_author_label(
                    _PIDRUCHNYK_AUTHOR_NAMES.get(str(author), _resolve_source_author(str(source_file)))
                ),
                "subject": _resolve_source_subject(str(source_file)),
            }
        )
    return index


def _resolve_textbook_source_file(
    ref: str | dict,
    pidruchnyk_urls: dict[str, str],
    source_index: list[dict] | None = None,
) -> str | None:
    """Resolve a plan textbook reference to a mapped source_file."""
    parsed = _parse_textbook_reference(ref)
    if not parsed:
        return None

    candidates = source_index if source_index is not None else _load_textbook_source_index()
    if not candidates:
        return None

    matches = [
        candidate
        for candidate in candidates
        if candidate["grade"] == parsed["grade"]
        and candidate["author"] == parsed["author"]
        and candidate["source_file"] in pidruchnyk_urls
    ]
    if not matches:
        return None

    subject_matches = [candidate for candidate in matches if candidate["subject"] == parsed["subject"]]
    if not subject_matches:
        return None
    matches = subject_matches

    if parsed["year"] is not None:
        year_matches = [candidate for candidate in matches if candidate["year"] == parsed["year"]]
        if year_matches:
            matches = year_matches

    matches.sort(key=lambda candidate: (candidate["year"] or 0, candidate["source_file"]), reverse=True)
    return matches[0]["source_file"]


def _build_pidruchnyk_section(
    plan: dict,
    pidruchnyk_urls: dict[str, str] | None = None,
    source_index: list[dict] | None = None,
) -> str:
    """Build a pidruchnyk textbook subsection from plan references."""
    if not isinstance(plan, dict):
        return ""

    pidruchnyk_urls = _load_pidruchnyk_urls() if pidruchnyk_urls is None else pidruchnyk_urls
    if not pidruchnyk_urls:
        return ""

    refs = plan.get("references", [])
    if not isinstance(refs, list):
        return ""

    source_index = source_index if source_index is not None else _load_textbook_source_index()
    seen: set[str] = set()
    bullets: list[str] = []

    for ref in refs:
        source_file = _resolve_textbook_source_file(ref, pidruchnyk_urls, source_index)
        if not source_file or source_file in seen:
            continue
        seen.add(source_file)
        bullets.append(
            f"- [{_build_source_display_name(source_file)}]({pidruchnyk_urls[source_file]})"
        )

    if not bullets:
        return ""

    return "\n".join(["### Підручники", *bullets])


def _build_resources_tab(level: str, slug: str) -> str:
    """Build Ресурси tab content from plan references + external_resources.yaml."""
    parts = ["**Джерела — References**", ""]

    # 1. Plan references
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if plan_path.exists():
        try:
            plan = yaml.safe_load(plan_path.read_text("utf-8"))
            refs = plan.get("references", [])
            if isinstance(refs, list):
                for ref in refs:
                    if isinstance(ref, str):
                        parts.append(f"- {ref}")
                    elif isinstance(ref, dict):
                        title = ref.get("title", "")
                        url = ref.get("url", "")
                        note = ref.get("note", "")
                        if url:
                            parts.append(f"- [{title}]({url})")
                        else:
                            parts.append(f"- {title}")
                        if note:
                            parts.append(f"  _{note}_")
        except Exception:
            pass

    # 2. External resources
    ext_path = PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
    lookup_key = f"{level}-{slug}"
    if ext_path.exists():
        try:
            ext_data = yaml.safe_load(ext_path.read_text("utf-8"))
            resources = ext_data.get("resources", {}).get(lookup_key, {})
            articles = resources.get("articles", [])
            for article in articles:
                title = article.get("title", "")
                url = article.get("url", "")
                source = article.get("source", "")
                if url:
                    parts.append(f"- [{title}]({url})")
                    if source:
                        parts.append(f"  _Source: {source}_")
        except Exception:
            pass

    if len(parts) <= 2:
        # No references found
        parts.append("_References will be added during review._")

    return "\n".join(parts)


def _build_slovnyk_tab(level: str, slug: str) -> str:
    """Build Словник tab content from vocabulary/{slug}.yaml or plan fallback.

    Priority:
    1. vocabulary/{slug}.yaml (writer-driven, has contextual translations)
    2. Fallback: plan vocabulary_hints (no prose translations)

    Issue: #1124 — moved from enrich.py to publish step.
    """
    # 1. Try writer-generated vocabulary YAML
    vocab_path = CURRICULUM_ROOT / level / "vocabulary" / f"{slug}.yaml"
    if vocab_path.exists():
        try:
            vocab_data = yaml.safe_load(vocab_path.read_text("utf-8"))
            if isinstance(vocab_data, dict) and vocab_data.get("vocabulary"):
                from build.vocab_gen import build_slovnyk_markdown
                entries = vocab_data["vocabulary"]
                expressions = [e for e in entries if e.get("expression")]
                additional = [e for e in entries if e.get("additional") and not e.get("expression")]
                plan_entries = [e for e in entries if not e.get("expression") and not e.get("additional")]
                result = build_slovnyk_markdown(plan_entries, additional, expressions)
                if result.strip():
                    return result
        except Exception as e:
            _log(f"  ⚠️  Vocabulary YAML parse error: {e}")

    # 2. Fallback: plan vocabulary_hints
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        return ""
    try:
        plan = yaml.safe_load(plan_path.read_text("utf-8"))
    except Exception:
        return ""

    from build.enrich import _build_slovnyk
    return _build_slovnyk(plan, slug=slug)


def _build_resources_tab_full(level: str, slug: str) -> str:
    """Build Ресурси tab from plan URLs + textbook links + external_resources.

    Three sources, in order:
    1. Plan references with explicit URLs (manually curated ULP/web links)
    2. Textbook references resolved to pidruchnyk.com.ua lesson-resource links
    3. External resources by exact slug match (curated articles/videos/podcasts)

    Dropped (issue #1175): ULP auto-matching, МійКлас auto-matching — tag-based
    fuzzy matching produced irrelevant links ("Г vs Ґ" in aspect modules).

    Issue: #1124, #1175
    """
    lines: list[str] = []

    # Load plan once (used by multiple sections below)
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    plan = _safe_load_plan(plan_path)

    # --- 1. Plan references with explicit URLs ---
    plan_refs_with_url = [
        ref for ref in plan.get("references", [])
        if isinstance(ref, dict) and ref.get("url")
    ]

    if plan_refs_with_url:
        lines.append("**Джерела — References**")
        lines.append("")
        for ref in plan_refs_with_url:
            title = ref.get("title", "")
            url = ref["url"]
            notes = ref.get("notes", "")
            lines.append(f"- [{title}]({url})")
            if notes:
                lines.append(f"  _{notes}_")
        lines.append("")

    # --- 2. Textbook links from plan references ---
    try:
        pidruchnyk_section = _build_pidruchnyk_section(plan)
        if pidruchnyk_section:
            lines.append(pidruchnyk_section)
            lines.append("")
    except Exception as e:
        _log(f"  ⚠️  Textbook links skipped: {e}")

    # --- 3. External resources by exact slug match ---
    try:
        from build.enrich import _load_external_resources
        # _load_external_resources uses exact slug match only (no fuzzy)
        ext_resources = _load_external_resources(slug, plan)
        if ext_resources:
            articles = [r for r in ext_resources if r["type"] == "articles"]
            videos = [r for r in ext_resources if r["type"] == "youtube"]
            podcasts = [r for r in ext_resources if r["type"] == "podcasts"]

            if articles:
                lines.append("**Статті — Articles**")
                lines.append("")
                for r in articles:
                    source = f" ({r['source']})" if r["source"] else ""
                    lines.append(f"- [{r['title']}]({r['url']}){source}")
                lines.append("")

            if videos:
                lines.append("**Відео — Videos**")
                lines.append("")
                for r in videos:
                    source = f" ({r['source']})" if r["source"] else ""
                    lines.append(f"- [{r['title']}]({r['url']}){source}")
                lines.append("")

            if podcasts:
                lines.append("**Подкасти — Podcasts**")
                lines.append("")
                for r in podcasts:
                    source = f" ({r['source']})" if r["source"] else ""
                    lines.append(f"- [{r['title']}]({r['url']}){source}")
                lines.append("")
    except Exception as e:
        _log(f"  ⚠️  External resources skipped: {e}")

    if not lines:
        return "_Ресурси будуть додані пізніше._"

    return "\n".join(lines)


def _sanitize_mdx(content: str) -> str:
    """Fix common MDX issues that break the acorn/MDX parser.

    1. Self-close void HTML elements: <br> → <br />, <hr> → <hr />
    2. Ensure blank lines around HTML block elements (required by MDX
       for block-level parsing — without them, <div> is parsed as inline
       inside a preceding paragraph, breaking tag nesting).
    3. Remove stray code fences (LLM artifact — unpaired ``` break MDX).
    4. Collapse triple+ blank lines to double.
    """
    import re

    # 1. Self-close void elements
    content = re.sub(r"<br\s*>", "<br />", content)
    content = re.sub(r"<br(?=\|)", "<br />", content)  # <br| in tables
    content = re.sub(r"<hr\s*>", "<hr />", content)

    # 2. Ensure blank lines around block-level HTML tags
    # MDX requires a blank line before/after HTML blocks for proper parsing.
    # Without it, the parser treats <div> as inline within a paragraph,
    # causing "Expected closing tag for <TabItem>" errors.
    block_tags = r"(?:div|table|section|article|aside|header|footer|nav|figure)"
    # Add blank line before opening block tag if preceded by non-blank text
    content = re.sub(
        rf"([^\n])\n(<{block_tags}[\s>])",
        r"\1\n\n\2",
        content,
    )
    # Add blank line after closing block tag if followed by non-blank text
    content = re.sub(
        rf"(</{block_tags}>)\n([^\n])",
        r"\1\n\n\2",
        content,
    )

    # 3. Remove stray code fences (unpaired ``` from LLM writer artifacts)
    fences = list(re.finditer(r"^```\w*\s*$", content, re.MULTILINE))
    if len(fences) % 2 != 0:
        # Odd number = unpaired. Remove the last one (usually a trailing artifact).
        last = fences[-1]
        content = content[:last.start()] + content[last.end():]

    # 4. Convert HTML comments to MDX comments (MDX doesn't support <!-- -->)
    # Remove exercise/activity marker comments entirely (orphaned placeholders).
    content = re.sub(r"<!--\s*(?:EXERCISE|INJECT_ACTIVITY)[^>]*-->", "", content)
    # Convert remaining HTML comments to MDX JSX comments
    content = re.sub(r"<!--\s*(.*?)\s*-->", r"{/* \1 */}", content)

    # 5. Collapse triple+ blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content


def step_publish(content_path: Path, level: str, slug: str) -> bool:
    """Step 9: Convert DSL→MDX + inject activities + build 4-tab structure.

    The 4 tabs are assembled from multiple sources:
    1. Урок: .md prose + inline activities from YAML
    2. Словник: vocabulary/{slug}.yaml or plan vocabulary_hints
    3. Зошит: activities/{slug}.yaml workbook section
    4. Ресурси: plan references + external_resources.yaml + ULP + МійКлас

    The .md file contains ONLY prose — no TAB markers, no enrichment artifacts.
    Issue: #1124
    """
    _log(f"\n{'='*60}")
    _log("  Step 9: PUBLISH — DSL→MDX + Activities")
    _log(f"{'='*60}")

    if not content_path or not content_path.exists():
        _log("  ❌ No content file")
        return False

    from build.activity_renderer import get_required_imports
    from generate_mdx.dsl_to_mdx import convert_dsl_to_mdx

    text = content_path.read_text("utf-8")

    # Strip any legacy TAB markers if still present (backward compat during migration)
    if "<!-- TAB:Словник -->" in text:
        text = text[:text.index("<!-- TAB:Словник -->")].strip()
    text = text.replace("<!-- TAB:Урок -->", "").strip()

    # --- Activity V2: load YAML if it exists ---
    activities_data = _load_activities(level, slug)
    inline_activities = activities_data.get("inline", []) if activities_data else []
    workbook_activities = activities_data.get("workbook", []) if activities_data else []
    all_v2_activities = inline_activities + workbook_activities

    if activities_data:
        # When activities YAML exists, strip legacy DSL blocks first
        # to avoid duplicate exercises (DSL in Урок + YAML in Зошит).
        text, dsl_strip_count = _strip_dsl_blocks(text)
        if dsl_strip_count > 0:
            _log(f"  Stripped {dsl_strip_count} legacy DSL block(s) (replaced by activities YAML)")

    # Convert blockquote dialogues to HTML divs (only at publish time, not in .md)
    from build.enrich import _format_dialogues
    text = _format_dialogues(text)

    # Always run convert_dsl_to_mdx — it handles YouTube URLs, bare links,
    # and stray quote cleanup in addition to DSL→MDX conversion.
    mdx_content, dsl_count = convert_dsl_to_mdx(text)
    if dsl_count > 0:
        _log(f"  Converted {dsl_count} DSL exercise(s) to MDX components")

    if activities_data:
        _log(f"  Activity V2: {len(inline_activities)} inline, {len(workbook_activities)} workbook")

        # Inject inline activities at markers
        mdx_content, unmatched = _inject_inline_activities(mdx_content, inline_activities)
        matched_count = len(inline_activities) - len(unmatched)
        if matched_count > 0:
            _log(f"  Injected {matched_count} inline activity/activities at markers")
        if unmatched:
            _log(f"  ⚠️  {len(unmatched)} inline activity/activities without markers → moved to Зошит")
            workbook_activities = unmatched + workbook_activities

    # Strip any remaining INJECT_ACTIVITY markers (unmatched = no inline activity)
    # HTML comments break MDX parsing — must be removed
    leftover_markers = re.findall(r"<!--\s*INJECT_ACTIVITY:.*?-->", mdx_content)
    if leftover_markers:
        for marker in leftover_markers:
            mdx_content = mdx_content.replace(marker, "")
        _log(f"  ⚠️  Stripped {len(leftover_markers)} unmatched INJECT_ACTIVITY marker(s)")
        mdx_content = re.sub(r"\n{3,}", "\n\n", mdx_content)

    # --- Build 4-tab structure from sources (#1124) ---
    # The .md is prose-only — assemble all tabs here.
    urok_content = mdx_content.strip()

    # Tab 2: Словник (from vocabulary YAML or plan fallback)
    slovnyk_content = _build_slovnyk_tab(level, slug)

    # Tab 3: Зошит (from activities YAML or placeholder)
    workbook_content = _build_workbook_tab(workbook_activities)

    # Tab 4: Ресурси (from plan + external resources)
    # Textbook references are rendered via pidruchnyk_urls.yaml when a mapping exists.
    resources_content = _build_resources_tab_full(level, slug)

    tab_parts = []
    tab_parts.append('<Tabs syncKey="module-tab">')

    # Tab 1: Урок
    tab_parts.append('<TabItem label="Урок">')
    tab_parts.append("")
    tab_parts.append(urok_content)
    tab_parts.append("")
    tab_parts.append("</TabItem>")

    # Tab 2: Словник
    if slovnyk_content.strip():
        tab_parts.append('<TabItem label="Словник">')
        tab_parts.append("")
        tab_parts.append(slovnyk_content.strip())
        tab_parts.append("")
        tab_parts.append("</TabItem>")

    # Tab 3: Зошит
    tab_parts.append('<TabItem label="Зошит">')
    tab_parts.append("")
    tab_parts.append(workbook_content)
    tab_parts.append("")
    tab_parts.append("</TabItem>")

    # Tab 4: Ресурси
    if resources_content.strip():
        tab_parts.append('<TabItem label="Ресурси">')
        tab_parts.append("")
        tab_parts.append(resources_content.strip())
        tab_parts.append("")
        tab_parts.append("</TabItem>")

    tab_parts.append("</Tabs>")
    mdx_content = "\n".join(tab_parts)

    # Sanitize MDX content — fix common issues that break the MDX parser
    mdx_content = _sanitize_mdx(mdx_content)

    # --- Write MDX ---
    mdx_dir = PROJECT_ROOT / "starlight" / "src" / "content" / "docs" / level
    mdx_dir.mkdir(parents=True, exist_ok=True)
    mdx_path = mdx_dir / f"{slug}.mdx"

    # Add MDX frontmatter
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    modules = data.get("levels", {}).get(level, {}).get("modules", [])
    order = modules.index(slug) + 1 if slug in modules else 1

    plan_title = slug.replace('-', ' ').title()
    plan_path_pub = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    try:
        plan_data = yaml.safe_load(plan_path_pub.read_text("utf-8"))
        if plan_data and "title" in plan_data:
            plan_title = plan_data["title"]
    except Exception:
        _log(f"  ⚠️  Could not read plan title from {plan_path_pub} — using slug fallback")

    frontmatter = f"""---
title: "{plan_title}"
sidebar:
  order: {order}
  label: "{order:02d}. {plan_title}"
pipeline: v6
build_status: draft
---

"""

    # Build imports — dynamic based on which components are used
    base_imports = [
        "import { Tabs, TabItem } from '@astrojs/starlight/components';",
        "import YouTubeVideo from '@site/src/components/YouTubeVideo';",
    ]

    # Legacy DSL imports (always included for backward compat when DSL exercises exist)
    if dsl_count > 0:
        for comp in ("Quiz", "FillIn", "MatchUp", "TrueFalse", "GroupSort"):
            imp = f"import {comp} from '@site/src/components/{comp}';"
            if imp not in base_imports:
                base_imports.append(imp)

    # Activity V2 imports
    if all_v2_activities:
        v2_imports = get_required_imports(all_v2_activities)
        for imp in v2_imports:
            if imp not in base_imports:
                base_imports.append(imp)

    # FlashcardDeck import (Словник tab uses it)
    if "FlashcardDeck" in mdx_content:
        fc_imp = "import FlashcardDeck from '@site/src/components/FlashcardDeck';"
        if fc_imp not in base_imports:
            base_imports.append(fc_imp)

    imports = "\n".join(sorted(base_imports)) + "\n\n"

    mdx_path.write_text(frontmatter + imports + mdx_content, "utf-8")
    _log(f"  ✅ MDX written → {mdx_path}")

    # Validate MDX
    from build.mdx_validate import validate_mdx
    mdx_errors = validate_mdx(mdx_path)
    if mdx_errors:
        _log(f"  ⚠️  MDX validation: {len(mdx_errors)} issue(s):")
        for err in mdx_errors[:5]:
            _log(f"    {err}")
    else:
        _log("  ✅ MDX validation passed")

    # Regenerate landing page so module status stays current
    try:
        from generate_landing_pages import generate_landing_page
        landing_mdx = generate_landing_page(level)
        if landing_mdx:
            landing_path = mdx_path.parent / "index.mdx"
            landing_path.write_text(landing_mdx, "utf-8")
            _log(f"  ✅ Landing page updated → {landing_path}")
    except Exception as e:
        _log(f"  ⚠️  Landing page update skipped: {e}")

    return True


def main():
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(description="V6 Pipeline Build")
    parser.add_argument("level", help="Level (e.g., a1)")
    parser.add_argument("module", type=int, help="Module number (or start of range with --range)")
    parser.add_argument("--range", type=int, default=None, metavar="END",
                        help="Build modules from MODULE to END (inclusive). E.g., a1 7 --range 14")
    parser.add_argument("--writer", choices=["gemini", "gemini-tools", "claude", "claude-tools", "codex", "codex-tools"], default="gemini-tools",
                        help="Default: gemini-tools. *-tools = with verification access during writing (MCP for Claude/Gemini, shell commands for Codex)")
    parser.add_argument("--reviewer", choices=["gemini", "gemini-tools", "claude", "claude-tools", "codex", "codex-tools"], default=None,
                        help="Override reviewer. Default: cross-agent (opposite of writer)")
    parser.add_argument("--step", choices=["check", "research", "pre-verify", "skeleton", "write", "exercises", "activities", "repair", "verify-exercises", "annotate", "enrich", "verify", "review", "publish", "audit", "all"],
                        default="all")
    skeleton_group = parser.add_mutually_exclusive_group()
    skeleton_group.add_argument("--skeleton", action="store_true", default=None,
                                help="Force skeleton step (default: always on)")
    skeleton_group.add_argument("--no-skeleton", action="store_true",
                                help="Skip skeleton step even for large modules")
    parser.add_argument("--no-chunk", action="store_true",
                        help="Disable section-by-section chunked generation (always single-call)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last completed phase (reads state.json, skips completed phases)")
    parser.add_argument("--review-threshold", type=float, default=REVIEW_TARGET_SCORE,
                        help="Batch review skip threshold: rerun review when latest score is below this value")
    parser.add_argument("--force-publish", action="store_true",
                        help="Publish even if audit gates still fail after heal (not recommended)")
    args = parser.parse_args()

    # --range: build multiple modules sequentially
    import subprocess as _subprocess
    if args.range is not None:
        manifest = CURRICULUM_ROOT / "curriculum.yaml"
        data = yaml.safe_load(manifest.read_text())
        end = args.range
        start = args.module
        if end < start:
            _log(f"❌ --range {end} is less than start module {start}")
            sys.exit(1)
        _log(f"\n{'='*60}")
        _log(f"  BATCH BUILD: {args.level.upper()} M{start:02d}–M{end:02d}")
        _log(f"{'='*60}")
        total = end - start + 1
        emit_event("batch_start", level=args.level, total=total)
        failed = []
        skipped = []
        for n in range(start, end + 1):
            # Auto-resume: resolve slug and check if fully complete
            _range_slugs = data.get("levels", {}).get(args.level, {}).get("modules", [])
            if n <= len(_range_slugs):
                _range_slug = _range_slugs[n - 1]
                skip_module, skip_reason = _should_skip_batch_module(
                    args.level, _range_slug, args.step, args.review_threshold,
                )
                if skip_module:
                    _log(f"\n  ⏭️  M{n:02d} ({_range_slug}) — {skip_reason}, skipping")
                    skipped.append(n)
                    continue

            _log(f"\n{'─'*60}")
            _log(f"  [{n - start + 1}/{end - start + 1}] Building M{n:02d}...")
            _log(f"{'─'*60}")
            try:
                result = _subprocess.run(
                    [str(PROJECT_ROOT / ".venv" / "bin" / "python"), __file__, args.level, str(n),
                     "--writer", args.writer,
                     "--step", args.step,
                     "--review-threshold", str(args.review_threshold),
                     *(["--force-publish"] if args.force_publish else []),
                     *(["--resume"] if args.resume else []),
                     *(["--reviewer", args.reviewer] if args.reviewer else []),
                     *(["--skeleton"] if getattr(args, "skeleton", False) else []),
                     *(["--no-skeleton"] if getattr(args, "no_skeleton", False) else []),
                     *(["--no-chunk"] if args.no_chunk else []),
                     ],
                    cwd=str(PROJECT_ROOT),
                    timeout=3600,  # 1 hour per module max
                )
                if result.returncode != 0:
                    failed.append(n)
                    _log(f"  ❌ M{n:02d} failed (rc={result.returncode})")
            except _subprocess.TimeoutExpired:
                failed.append(n)
                _log(f"  ❌ M{n:02d} timed out (1h)")
            except Exception as e:
                failed.append(n)
                _log(f"  ❌ M{n:02d} error: {e}")

        _log(f"\n{'='*60}")
        built = total - len(failed) - len(skipped)
        _log(f"  BATCH COMPLETE: {built}/{total} built, {len(skipped)} skipped (already complete)")
        if failed:
            _log(f"  Failed: {', '.join(f'M{n:02d}' for n in failed)}")
        _log(f"{'='*60}")
        emit_event(
            "batch_done",
            level=args.level,
            total=total,
            succeeded=total - len(failed),
            failed=len(failed),
        )
        sys.exit(1 if failed else 0)

    # Resolve slug
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    slugs = data.get("levels", {}).get(args.level, {}).get("modules", [])
    if args.module > len(slugs):
        _log(f"Module {args.module} not found (max {len(slugs)})")
        sys.exit(1)
    slug = slugs[args.module - 1]
    emit_event("module_start", level=args.level, slug=slug)

    def _emit_phase_done(phase: str, started_at: float):
        emit_event(
            "phase_done",
            level=args.level,
            slug=slug,
            phase=phase,
            duration_s=round(time.monotonic() - started_at, 3),
            ok=True,
        )

    def _emit_module_failed(phase: str, error: object):
        emit_event(
            "module_failed",
            level=args.level,
            slug=slug,
            phase=phase,
            error=str(error)[:200],
        )

    # Acquire build lock — prevents two processes from racing on the same module
    build_lock = ModuleBuildLock(args.level, slug)
    if not build_lock.acquire():
        sys.exit(2)  # Exit code 2 = locked by another build

    try:
        _build_start = time.monotonic()

        _log(f"\n🔨 V6 Build: {args.level.upper()} M{args.module:02d} ({slug})")
        _log(f"   Writer: {args.writer}")

        steps = args.step

        # --resume: load completed phases and restore dependency variables
        completed_phases: set[str] = set()
        # Resume mode loads completed phases + restores dependency state.
        # Note: even single-step invocations (--step audit, --step publish, etc.)
        # need phases loaded so restoration + heal paths have context to work with.
        if args.resume:
            completed_phases = _load_completed_phases(args.level, slug)
            if completed_phases:
                # If the last audit says this module is failing, auto-invalidate
                # the self-heal tail (audit + repair + publish + review) so the
                # pipeline actually re-runs those phases. Without this, --resume
                # on a failing module does nothing because every phase block is
                # guarded by "X not in completed_phases".
                _status_path = CURRICULUM_ROOT / args.level / "status" / f"{slug}.json"
                if _status_path.exists():
                    try:
                        import json as _json
                        _status_data = _json.loads(_status_path.read_text("utf-8"))
                        _overall = _status_data.get("overall", {}).get("status", "unknown")
                        if _overall not in ("pass", "content-complete"):
                            _failed_gates = [
                                k for k, v in (_status_data.get("gates") or {}).items()
                                if isinstance(v, dict) and v.get("status") == "fail"
                            ]
                            _log(
                                f"   🩹 Status shows {_overall} "
                                f"(failed gates: {', '.join(_failed_gates) or 'unknown'})"
                            )
                            _log("      Invalidating audit/repair/publish/review phases for retry")
                            _invalidate_phases(
                                args.level, slug,
                                ["audit", "repair", "publish", "review"],
                            )
                            for _p in ("audit", "repair", "publish", "review"):
                                completed_phases.discard(_p)

                        # Also invalidate review when score is below threshold
                        # (even if audit is passing — audit pass != review pass)
                        if "review" in completed_phases and steps in ("review", "all"):
                            _latest = _load_latest_review_result(args.level, slug)
                            _threshold = getattr(args, "review_threshold", REVIEW_TARGET_SCORE)
                            if _latest and _latest.score < _threshold:
                                _log(
                                    f"   🩹 Review score {_latest.score:.1f} < {_threshold:.1f} threshold"
                                )
                                _log("      Invalidating review phase for re-review")
                                _invalidate_phases(args.level, slug, ["review"])
                                completed_phases.discard("review")

                    except Exception as _e:
                        _log(f"   ⚠️  Could not inspect status for auto-invalidation: {_e}")

                _log(f"   Resuming — {len(completed_phases)} phase(s) already complete:")
                for p in _ALL_PHASES:
                    if p in completed_phases:
                        _log(f"     ⏭️  {p}")
            else:
                _log("   Resume requested but no completed phases found — starting fresh")

        # Pre-flight: check MCP server is running (VESUM, dictionaries, textbooks via SQLite)
        if "tools" in args.writer:
            import urllib.request
            try:
                resp = urllib.request.urlopen("http://127.0.0.1:8766/health", timeout=3)
                _log(f"   MCP server: ✅ running ({resp.read().decode()})")
            except Exception:
                _log("   ❌ MCP server is not running. Start it: ./services.sh start")
                _emit_module_failed("check", "MCP server is not running")
                sys.exit(1)

        # Clean previous build artifacts for a fresh full build (skip when resuming)
        if steps == "all" and not completed_phases:
            _clean_build_artifacts(args.level, slug)

        # --resume: restore dependency variables from disk if their phases are complete
        # These variables are normally set by earlier phases; when resuming we load from disk
        packet_path: Path | None = None
        skeleton_text: str = ""
        verification_text: str = ""
        content_path: Path | None = None
        final_score: float | None = None
        publish_completed: bool = False

        if completed_phases:
            # Restore packet_path (from research phase)
            if "research" in completed_phases:
                _p = CURRICULUM_ROOT / args.level / "research" / f"{slug}-knowledge-packet.md"
                if _p.exists():
                    packet_path = _p
                    _log(f"   Restored: packet_path ({_p.name})")

            # Restore skeleton_text (from skeleton phase)
            if "skeleton" in completed_phases:
                _s = CURRICULUM_ROOT / args.level / "orchestration" / slug / "skeleton.md"
                if _s.exists():
                    skeleton_text = _s.read_text("utf-8")
                    _log(f"   Restored: skeleton_text ({len(skeleton_text.split())} words)")

            # Restore verification_text (from pre-verify phase)
            if "pre-verify" in completed_phases:
                _v = CURRICULUM_ROOT / args.level / "orchestration" / slug / "pre-verify-results.md"
                if _v.exists():
                    verification_text = _v.read_text("utf-8")
                    _log(f"   Restored: verification_text ({len(verification_text)} chars)")

            # Restore content_path (from write phase)
            if "write" in completed_phases:
                _c = CURRICULUM_ROOT / args.level / f"{slug}.md"
                if _c.exists():
                    content_path = _c
                    _log(f"   Restored: content_path ({_c.name})")

        # Single-step and resumed builds can jump straight into plan-consuming
        # phases without re-running step_check(). Enforce the readiness gate
        # here so write/review/publish never bypass it.
        should_run_pre_build_gate = (
            steps in _PRE_BUILD_GATE_STEPS
            and not (steps == "all" and "check" not in completed_phases)
        )
        if should_run_pre_build_gate:
            _log("\n  Pre-flight: validating pre-build readiness gate")
            if not _run_pre_build_gate(args.level, slug):
                _log("\n❌ Build FAILED at pre-build readiness gate")
                _emit_module_failed("check", "Build FAILED at Step 2 (plan check)")
                sys.exit(1)

        # Step 2: CHECK
        if steps in ("all", "check") and "check" not in completed_phases:
            _phase_start = time.monotonic()
            if not step_check(args.level, args.module, slug):
                _log("\n❌ Build FAILED at Step 2 (plan check)")
                _emit_module_failed("check", "Build FAILED at Step 2 (plan check)")
                sys.exit(1)
            _save_v6_state(args.level, slug, "check")
            _emit_phase_done("check", _phase_start)

        # Step 3: RESEARCH
        if steps in ("all", "research") and "research" not in completed_phases:
            _phase_start = time.monotonic()
            packet_path = step_research(args.level, args.module, slug)
            if not packet_path:
                _log("\n❌ Build FAILED at Step 3 (research)")
                _emit_module_failed("research", "Build FAILED at Step 3 (research)")
                sys.exit(1)
            _save_v6_state(args.level, slug, "research")
            _emit_phase_done("research", _phase_start)
        elif steps not in ("all", "research") and packet_path is None:
            # Try to find existing packet (single-step mode, no resume)
            _p = CURRICULUM_ROOT / args.level / "research" / f"{slug}-knowledge-packet.md"
            if _p.exists():
                packet_path = _p

        # Step 4: SKELETON (always on, use --no-skeleton to skip)
        # Always use skeleton — matures the skeleton→flesh flow for B1+,
        # and improves structure even at A1/A2 word counts.
        # Use --no-skeleton to opt out.
        use_skeleton = not args.no_skeleton

        if steps in ("all", "skeleton") and "skeleton" not in completed_phases:
            if use_skeleton:
                _phase_start = time.monotonic()
                skeleton_text = step_skeleton(
                    args.level, args.module, slug, packet_path,
                    writer=args.writer,
                ) or ""
                if not skeleton_text and steps == "skeleton":
                    _log("\n  SKELETON step returned empty — continuing without skeleton")
                if skeleton_text or steps == "skeleton":
                    _emit_phase_done("skeleton", _phase_start)
            else:
                _log("\n  ⏭️  Skeleton skipped (--no-skeleton)")
                _save_v6_state(args.level, slug, "skeleton", status="skipped")
                completed_phases.add("skeleton")

        if use_skeleton and skeleton_text:
            _log(f"\n  📐 Skeleton active ({len(skeleton_text.split())} words) — will constrain writer")
        elif use_skeleton and not skeleton_text and "skeleton" not in completed_phases and steps == "all":
            # Skeleton failed. Decide whether to halt or limp onwards.
            #
            # Halting is appropriate ONLY on a fresh build (no existing content
            # on disk). When resuming against an already-written module — the
            # common case for batch heal/review passes — halting here means a
            # transient Gemini failure at step 4 blocks the ENTIRE module from
            # reaching audit / heal / review. That contradicts the "fix all
            # modules" workflow.
            #
            # If content.md already exists, proceed without skeleton:
            #   - step_write is guarded by `"write" not in completed_phases`,
            #     so it gets skipped when write is already done.
            #   - audit / heal / review still get to run against the existing
            #     content, which is what the user wanted in the first place.
            _existing_content = CURRICULUM_ROOT / args.level / f"{slug}.md"
            _write_already_done = "write" in completed_phases and _existing_content.exists()
            if _write_already_done:
                _log("\n  ⚠️  Skeleton generation failed, but content.md already exists —")
                _log("     proceeding without re-running skeleton. Audit + heal + review")
                _log("     will still run against the existing content.")
                content_path = _existing_content
            else:
                _log("\n  ❌ Skeleton was requested but generation failed — halting build")
                _log("     (no existing content to fall back on)")
                _log("     Re-run with --no-skeleton to skip, or fix the skeleton timeout")
                _emit_module_failed("skeleton", "Skeleton was requested but generation failed")
                sys.exit(1)

        # Try to load existing skeleton from disk if running single step
        if steps == "write" and not skeleton_text and use_skeleton:
            existing_skeleton = CURRICULUM_ROOT / args.level / "orchestration" / slug / "skeleton.md"
            if existing_skeleton.exists():
                skeleton_text = existing_skeleton.read_text("utf-8")
                _log(f"  📐 Loaded existing skeleton ({len(skeleton_text.split())} words)")

        # Step 3b: PRE-VERIFY — force tool calls before writing (#1070)
        if steps in ("all", "write", "pre-verify") and "pre-verify" not in completed_phases:
            # Only run pre-verify when using -tools writers (tools must be available)
            if "tools" in args.writer or steps == "pre-verify":
                _phase_start = time.monotonic()
                verification_text = step_pre_verify(
                    args.level, args.module, slug,
                    writer=args.writer if "tools" in args.writer else f"{args.writer}-tools",
                ) or ""
                _emit_phase_done("pre-verify", _phase_start)
            else:
                _log("\n  ⏭️  Pre-verify skipped (writer has no tools — use --writer claude-tools)")
                _save_v6_state(args.level, slug, "pre-verify", status="skipped")
                completed_phases.add("pre-verify")

        # Try to load existing pre-verify from disk if running single step
        if steps == "write" and not verification_text:
            existing_verify = CURRICULUM_ROOT / args.level / "orchestration" / slug / "pre-verify-results.md"
            if existing_verify.exists():
                verification_text = existing_verify.read_text("utf-8")
                _log(f"  🔍 Loaded existing pre-verify ({len(verification_text)} chars)")

        # Step 5: WRITE + QUICK VERIFY + RETRY
        if steps in ("all", "write") and "write" not in completed_phases:
            _phase_start = time.monotonic()
            content_path = step_write_with_retry(
                args.level, args.module, slug, packet_path,
                writer=args.writer, max_retries=4,
                skeleton=skeleton_text,
                no_chunk=args.no_chunk,
                verification_text=verification_text,
            )
            if not content_path:
                _log("\n❌ Build FAILED at Step 5 (write — all retries exhausted)")
                _emit_module_failed("write", "Build FAILED at Step 5 (write — all retries exhausted)")
                sys.exit(1)
            _save_v6_state(args.level, slug, "write")
            _emit_phase_done("write", _phase_start)
        elif content_path is None:
            content_path = CURRICULUM_ROOT / args.level / f"{slug}.md"

        # Step 5b: EXERCISES — legacy fallback (skip in full pipeline, ACTIVITIES replaces it)
        if steps == "exercises" and "exercises" not in completed_phases:
            # Only run when explicitly requested (single-step mode)
            _phase_start = time.monotonic()
            step_exercises(content_path)
            _save_v6_state(args.level, slug, "exercises")
            _emit_phase_done("exercises", _phase_start)
        elif steps == "all" and "exercises" not in completed_phases:
            _log(f"\n{'='*60}")
            _log("  Step 5b: EXERCISES — Skipped (ACTIVITIES step handles exercises)")
            _log(f"{'='*60}")
            _save_v6_state(args.level, slug, "exercises")

        # Normalize INJECT_ACTIVITY markers before activities step.
        # Writers produce various formats:
        #   <!-- INJECT_ACTIVITY: quiz, Case Identification Drill, 8 items -->
        #   <!-- INJECT_ACTIVITY: quiz-case-identification -->
        # Normalize all to kebab-case: <!-- INJECT_ACTIVITY: quiz-case-identification-drill -->
        if content_path and content_path.exists():
            _content = content_path.read_text("utf-8")
            _raw_markers = re.findall(r"(<!--\s*INJECT_ACTIVITY:\s*)(.+?)(\s*-->)", _content)
            if _raw_markers:
                for prefix, marker_text, suffix in _raw_markers:
                    # Normalize: lowercase, strip counts like "8 items"/"8 Items", replace non-alnum with hyphens
                    normalized = re.sub(r",?\s*\d+\s*items?", "", marker_text, flags=re.IGNORECASE)
                    normalized = normalized.lower().strip().strip(",")
                    # Keep only ASCII alphanumeric (markers are always Latin ids, not Cyrillic)
                    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
                    old = f"{prefix}{marker_text}{suffix}"
                    new = f"<!-- INJECT_ACTIVITY: {normalized} -->"
                    if old != new:
                        _content = _content.replace(old, new, 1)
                content_path.write_text(_content, "utf-8")

        # Step 5e: ACTIVITIES — structured YAML generation (#1042)
        if steps in ("all", "activities") and "activities" not in completed_phases:
            _phase_start = time.monotonic()
            activity_path = step_activities(
                content_path, args.level, args.module, slug,
                writer=args.writer,
            )
            if activity_path:
                # Inject deterministic abetka activities (letter-grid, watch-and-repeat)
                _inject_abetka_activities(activity_path, args.level, slug)
                _save_v6_state(args.level, slug, "activities")
                _emit_phase_done("activities", _phase_start)
            else:
                _log("\n❌ Build FAILED at Step 5e (activity generation)")
                _emit_module_failed("activities", "Build FAILED at Step 5e (activity generation)")
                sys.exit(1)

        # Step 5f: REPAIR — deterministic activity fixes (#1185)
        # Runs after activities. If repair drops count below minimum, regen
        # once more (max 1 retry) and repair again. This is the self-healing
        # loop: the first regen often produces structurally valid activities
        # once the broken ones are known.
        #
        # --resume compatibility: when repair mutates activities, downstream
        # phases (publish, audit) are stale and must be re-run. We invalidate
        # them in state.json so a subsequent --resume pass picks them up.
        if steps in ("all", "activities", "repair") and "repair" not in completed_phases:
            _phase_start = time.monotonic()
            _pre_activity_mtime = 0.0
            _activity_path = CURRICULUM_ROOT / args.level / "activities" / f"{slug}.yaml"
            if _activity_path.exists():
                _pre_activity_mtime = _activity_path.stat().st_mtime

            _repair_ok, needs_regen = step_repair(args.level, args.module, slug)
            regen_fired = False
            if needs_regen:
                _log("\n🔄 Activity count below minimum — regenerating once")
                regen_fired = True
                activity_path = step_activities(
                    content_path, args.level, args.module, slug,
                    writer=args.writer,
                )
                if activity_path:
                    _inject_abetka_activities(activity_path, args.level, slug)
                    # Repair the fresh output too
                    _repair_ok, needs_regen = step_repair(args.level, args.module, slug)
                    if needs_regen:
                        _log("\n⚠️  Still below minimum after regen — continuing anyway (audit will flag)")
                else:
                    _log("\n⚠️  Activity regen failed — continuing with repaired but short output")

            # Invalidate stale downstream phases if activities were actually changed.
            _post_mtime = _activity_path.stat().st_mtime if _activity_path.exists() else 0.0
            _activities_changed = regen_fired or _post_mtime > _pre_activity_mtime
            if _activities_changed:
                _log("  🔁 Activities changed — invalidating downstream phases (publish, audit) for --resume")
                _invalidate_phases(args.level, slug, ["publish", "audit"])
                completed_phases.discard("publish")
                completed_phases.discard("audit")

            _save_v6_state(args.level, slug, "repair")
            _emit_phase_done("repair", _phase_start)

        # Step 5d: VERIFY EXERCISES — grounding check (informational, non-blocking)
        if steps in ("all", "exercises", "verify-exercises") and "verify-exercises" not in completed_phases:
            _phase_start = time.monotonic()
            step_verify_exercises(content_path, args.level, slug)
            _save_v6_state(args.level, slug, "verify-exercises")
            _emit_phase_done("verify-exercises", _phase_start)

        # Step 6: POST-PROCESS (strip LLM artifacts — but NOT stress annotation yet)
        # Stress annotation moves to AFTER review to avoid wrong stress marks
        # causing review rejection.
        if steps == "all" and "annotate" not in completed_phases:
            if not content_path or not content_path.exists():
                _log("\n❌ Build FAILED — no content file exists (write step failed)")
                _emit_module_failed("annotate", "Build FAILED — no content file exists (write step failed)")
                sys.exit(1)
            _phase_start = time.monotonic()
            _post_process_content(content_path)
            _save_v6_state(args.level, slug, "annotate")
            _emit_phase_done("annotate", _phase_start)

        # Step 5c: VOCAB — writer generates словник YAML
        if steps in ("all", "write") and "vocab" not in completed_phases:
            _phase_start = time.monotonic()
            vocab_path = step_vocab(
                content_path, args.level, args.module, slug,
                writer=args.writer,
            )
            if vocab_path:
                _save_v6_state(args.level, slug, "vocab")
                _emit_phase_done("vocab", _phase_start)
            else:
                _log("\n❌ Build FAILED at Step 5c (vocabulary generation)")
                _emit_module_failed("vocab", "Build FAILED at Step 5c (vocabulary generation)")
                sys.exit(1)

        # Step 7b: ENRICH — SKIPPED (#1124: enrichment moved to publish step)
        # Kept for backward compat: mark as completed so pipeline doesn't stall
        if steps in ("all", "enrich") and "enrich" not in completed_phases:
            _log(f"\n{'='*60}")
            _log("  Step 7b: ENRICH — Skipped (enrichment moved to publish step, #1124)")
            _log(f"{'='*60}")
            _save_v6_state(args.level, slug, "enrich")

        # Step 7: VERIFY
        if steps in ("all", "verify") and "verify" not in completed_phases:
            _phase_start = time.monotonic()
            step_verify(content_path, args.level, args.module)
            _save_v6_state(args.level, slug, "verify")
            _emit_phase_done("verify", _phase_start)

        # Step 8: REVIEW + deterministic fix
        # If REVISE: reviewer outputs <fixes> with exact find/replace pairs.
        # We apply them deterministically — no LLM regeneration, no rewriting.
        # Then re-review to verify. No re-enrich needed (#1124).
        if steps in ("all", "review") and "review" not in completed_phases:
            _phase_start = time.monotonic()
            passed, score, review_text = step_review(
                content_path, args.level, args.module, slug,
                writer=args.writer, reviewer_override=args.reviewer,
            )
            if score == 0.0 and not review_text:
                _log("\n❌ Build FAILED at Step 8 (review — no output from reviewer)")
                _emit_module_failed("review", "Build FAILED at Step 8 (review — no output from reviewer)")
                sys.exit(1)
            _save_v6_state(args.level, slug, "review")
            final_score = score

            # Fix strategy:
            # 1. If PASSED → apply any <fixes> anyway (minor improvements), done.
            # 2. If score ≥ target → apply <fixes>, done (no re-review, avoids degradation).
            # 3. If score < target → apply <fixes>, re-review. If still failing, section rewrite + re-review.
            # 4. GUARANTEE: before leaving this block, ALWAYS apply the latest review's <fixes>.
            #    No review fix is ever left unapplied.


            # Apply deterministic fixes from R1.  NEVER fall back to LLM section
            # rewrite — evidence shows rewrites introduce new errors and degrade
            # scores (8.2→7.8 on a2-bridge, 2026-04-07).  Apply what matches,
            # skip what doesn't.
            r1_score = score
            fixes_applied, fix_count = _apply_review_fixes(review_text, content_path)
            if fixes_applied:
                _log(f"\n🔧 Applied {fix_count} deterministic fix(es) from R1")
                step_verify(content_path, args.level, args.module)

            # R2 only if R1 is below the target threshold.
            if r1_score < REVIEW_TARGET_SCORE:
                _log(
                    f"\n🔄 R1 score {r1_score}/10 < {REVIEW_TARGET_SCORE:.1f} — running R2 to measure improvement"
                )
                passed, score, review_text = step_review(
                    content_path, args.level, args.module, slug,
                    writer=args.writer, reviewer_override=args.reviewer,
                )
                _save_v6_state(args.level, slug, "review")

                # Apply R2 fixes
                r2_applied, r2_count = _apply_review_fixes(review_text, content_path)
                if r2_applied:
                    _log(f"\n🔧 Applied {r2_count} fix(es) from R2")
                    step_verify(content_path, args.level, args.module)

                delta = score - r1_score
                delta_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
                _log(f"\n📊 R1: {r1_score}/10 → R2: {score}/10 ({delta_str})")

                if passed:
                    _log(f"\n✅ Review PASSED ({score}/10)")
                elif score >= 8.0:
                    _log(f"\n✅ Score {score}/10 ≥ 8.0 — accepting")
                elif score >= 7.0:
                    _log(f"\n⚠️  Score {score}/10 — accepting with warnings (2 rounds done)")
                else:
                    _log(f"\n❌ Score {score}/10 < 7.0 — HALTING. Module has critical issues.")
                    _log("   Fix the plan or content manually, then re-run with --resume")
                    _emit_module_failed("review", f"Score {score}/10 < 7.0 — HALTING. Module has critical issues.")
                    return False  # Do not proceed to publish
            else:
                _log(
                    f"\n✅ R1 score {r1_score}/10 ≥ {REVIEW_TARGET_SCORE:.1f} — accepting with {fix_count} fix(es)"
                )

            # Run deterministic style cleanup if engagement is weak
            engagement_match = re.search(
                r"Engagement.*?(\d+)/10", review_text, re.IGNORECASE
            )
            if engagement_match:
                engagement = int(engagement_match.group(1))
                if engagement <= 7:
                    _log(f"\n🎨 Engagement {engagement}/10 — running style cleanup")
                    style_fixes = _post_process_content(content_path)
                    if style_fixes > 0:
                        _log(f"  Applied {style_fixes} deterministic style fixes")
            # Apply any remaining fixes from the final review (even PASS verdicts
            # may have minor style suggestions worth applying).
            if passed:
                latest_fixes = _parse_review_fixes(review_text)
                if latest_fixes:
                    final_applied, final_count = _apply_review_fixes(review_text, content_path)
                    if final_applied:
                        _log(f"\n🔧 Post-PASS fix pass: applied {final_count}/{len(latest_fixes)} minor fix(es)")

            # 2. Check for remaining known issues (Russianisms, calques)
            if content_path.exists():
                from build.quick_verify import _check_toxic_tokens
                remaining_toxins = _check_toxic_tokens(content_path.read_text("utf-8"))
                if remaining_toxins:
                    _log(f"\n⚠️  POST-REVIEW TOXIN CHECK: {len(remaining_toxins)} issue(s) remain:")
                    for t in remaining_toxins[:5]:
                        _log(f"    {t}")

            # Log final status
            if passed:
                _log(f"\n✅ Review PASSED ({score}/10)")
            elif score >= REVIEW_TARGET_SCORE:
                _log(f"\n✅ Score {score}/10 ≥ {REVIEW_TARGET_SCORE:.1f} — accepting")
            else:
                _log(f"\n⚠️  Score {score}/10 — accepting as final (fix rounds exhausted)")
            final_score = score
            _emit_phase_done("review", _phase_start)

        # Step 8b: ANNOTATE (stress marks — after review, before publish)
        # Skip for: seminar tracks (B2+ immersion), A1/A2 (stress in словník only,
        # not in prose — annotator heteronym bugs cause more harm than good at
        # beginner levels where every word is new).
        _SKIP_ANNOTATE_TRACKS = {"hist", "bio", "istorio", "lit", "folk", "oes", "ruth"}
        _SKIP_ANNOTATE_LEVELS = {"a2", "b1", "b2", "c1", "c2"}
        _skip_annotate = (
            args.level.lower() in _SKIP_ANNOTATE_TRACKS
            or args.level.lower().startswith("lit-")
            or args.level.lower() in _SKIP_ANNOTATE_LEVELS
        )
        if steps in ("all", "review", "publish", "annotate") and "stress" not in completed_phases:
            if _skip_annotate:
                reason = "seminar track" if args.level.lower() not in _SKIP_ANNOTATE_LEVELS else f"{args.level.upper()} — stress in словník only"
                _log(f"\n  ⏭️  Skipping stress marks ({reason})")
            else:
                _phase_start = time.monotonic()
                step_annotate(content_path)
                _emit_phase_done("stress", _phase_start)
            _save_v6_state(args.level, slug, "stress")

        # Step 9: PRE-PUBLISH AUDIT — detect issues before publishing MDX (#1185)
        # The proactive repair step earlier catches structural bugs, but the
        # audit may still surface problems that repair CAN fix (e.g. true-false
        # items with non-boolean `correct` field). Run audit first so those get
        # healed BEFORE we freeze the published MDX.
        #
        # NOTE: We intentionally run audit UNCONDITIONALLY when steps includes
        # audit/publish/all. The user explicitly asking for --step audit means
        # "audit and fix what you can" — gating on "audit not in completed_phases"
        # made the pipeline a no-op on already-built-but-failing modules.
        _pre_audit_ran = False
        if steps in ("all", "publish", "audit"):
            _phase_start = time.monotonic()
            step_audit(content_path, args.level, slug)
            _pre_audit_ran = True

            # Inspect the status file for activity-related failures. If any
            # gate that repair knows how to fix is red, run a second repair
            # pass and (if needed) regen activities.
            _status_path = CURRICULUM_ROOT / args.level / "status" / f"{slug}.json"
            _activity_gate_failed = False
            _salad_gate_failed = False
            _engagement_gate_failed = False
            _inline_english_gate_failed = False
            _immersion_gate_failed = False
            _overall_status = "unknown"
            if _status_path.exists():
                try:
                    _status = json.loads(_status_path.read_text("utf-8"))
                    _overall_status = _status.get("overall", {}).get("status", "unknown")
                    _gates = _status.get("gates", {})
                    for _gname in ("activities", "density", "activity_quality", "structure"):
                        _g = _gates.get(_gname)
                        if isinstance(_g, dict) and _g.get("status") == "fail":
                            _activity_gate_failed = True
                            break
                    # Lesson gate carries several sub-signals in its message.
                    # Parse the ones that require a writer regen to fix.
                    _lesson = _gates.get("lesson", {})
                    if isinstance(_lesson, dict):
                        _lesson_msg = _lesson.get("message", "")
                        _lesson_status = _lesson.get("status")
                        # Language salad — mixed paragraphs / inline-gloss overflow.
                        if "salad:" in _lesson_msg.lower() or "SALAD" in _lesson_msg:
                            _salad_gate_failed = True
                        # Engagement callouts missing — writer produced no
                        # :::note / :::tip / :::info boxes. Only trigger the
                        # regen branch if the lesson gate is actually failing
                        # (don't regen when the overall lesson passes but
                        # engagement is just a soft warning somewhere).
                        if (
                            _lesson_status == "fail"
                            and "engagement" in _lesson_msg.lower()
                        ):
                            # Look for the `engagement: X/Y` pattern and
                            # trigger regen when X < Y.
                            _eng_match = re.search(
                                r"engagement:\s*(\d+)\s*/\s*(\d+)",
                                _lesson_msg,
                                re.IGNORECASE,
                            )
                            if _eng_match:
                                _eng_have = int(_eng_match.group(1))
                                _eng_need = int(_eng_match.group(2))
                                if _eng_have < _eng_need:
                                    _engagement_gate_failed = True
                        # Inline English translations in prose — parenthetical
                        # glosses like "(He used to call often)" that break the
                        # immersion target. The writer prompt already forbids
                        # them; regen with the current prompt should clear it.
                        if "INLINE_ENGLISH_IN_PROSE" in _lesson_msg:
                            _inline_english_gate_failed = True
                        # Immersion — Ukrainian % below the level target. It
                        # reports as a sub-signal of the LESSON gate message
                        # ("immersion: 13.4% LOW (target 20-40% (M35))"), not
                        # as a standalone gate, so we parse it from the lesson
                        # message when the lesson gate is failing.
                        if (
                            _lesson_status == "fail"
                            and "immersion" in _lesson_msg.lower()
                            and "LOW" in _lesson_msg
                        ):
                            _immersion_gate_failed = True
                except Exception as e:
                    _log(f"  ⚠️  Could not parse status file for heal check: {e}")

            if _activity_gate_failed:
                _log("\n🩹 Audit flagged activity gate(s) — running heal pass")
                _activity_path = CURRICULUM_ROOT / args.level / "activities" / f"{slug}.yaml"
                _pre_heal_mtime = _activity_path.stat().st_mtime if _activity_path.exists() else 0.0

                _heal_ok, _heal_regen = step_repair(args.level, args.module, slug)
                if _heal_regen:
                    _log("\n🔄 Heal pass requires regen — regenerating activities")
                    _new_path = step_activities(
                        content_path, args.level, args.module, slug,
                        writer=args.writer,
                    )
                    if _new_path:
                        _inject_abetka_activities(_new_path, args.level, slug)
                        step_repair(args.level, args.module, slug)

                _post_heal_mtime = _activity_path.stat().st_mtime if _activity_path.exists() else 0.0
                if _post_heal_mtime > _pre_heal_mtime:
                    _log("  🔁 Heal modified activities — re-auditing before publish")
                    step_audit(content_path, args.level, slug)
                    # Re-read status after re-audit
                    try:
                        _status = json.loads(_status_path.read_text("utf-8"))
                        _overall_status = _status.get("overall", {}).get("status", "unknown")
                    except Exception:
                        pass

            # Prose regen heal: triggered by either
            #   (a) language salad in the lesson gate, OR
            #   (b) missing engagement callouts (:::note/:::tip/:::info count
            #       below the level's minimum).
            #
            # Both classes of failure are "the writer produced bad prose
            # that deterministic repair can't fix". The fix is identical:
            # re-run the chunked writer with the current prompt (which
            # includes both the paragraph-language rule AND the callout
            # requirement) and re-audit. Max 1 regen attempt per build
            # invocation to prevent loops.
            _salad_regen_ran = False
            _prose_regen_needed = (
                _salad_gate_failed
                or _engagement_gate_failed
                or _inline_english_gate_failed
                or _immersion_gate_failed
            )
            if _prose_regen_needed and content_path and content_path.exists():
                _reasons = []
                if _salad_gate_failed:
                    _reasons.append("language salad")
                if _engagement_gate_failed:
                    _reasons.append("missing engagement callouts")
                if _inline_english_gate_failed:
                    _reasons.append("inline English in prose")
                if _immersion_gate_failed:
                    _reasons.append("immersion below target")
                _log(f"\n🎨 Audit flagged {' + '.join(_reasons)} — regenerating prose")
                _log("   Writer prompt includes paragraph-language rule (#1185) and callout requirement.")
                _log("   Reusing research/skeleton/plan — only prose will be rewritten.")
                _pre_regen_mtime = content_path.stat().st_mtime

                # Load skeleton + packet + verification from disk directly.
                # --step audit without --step all doesn't restore main()'s
                # skeleton_text/packet_path locals, so we reload here. We
                # WANT the chunked writer path (which has the new salad rule),
                # so skeleton MUST be non-empty.
                _orch_dir = CURRICULUM_ROOT / args.level / "orchestration" / slug
                _heal_skeleton = skeleton_text
                if not _heal_skeleton:
                    _sk_path = _orch_dir / "skeleton.md"
                    if _sk_path.exists():
                        _heal_skeleton = _sk_path.read_text("utf-8")
                        _log(f"   Loaded skeleton from disk ({len(_heal_skeleton.split())} words)")
                    else:
                        _log(f"   ⚠️  No skeleton at {_sk_path} — will use single-shot path")

                _heal_packet: Path | None = packet_path
                if _heal_packet is None:
                    _pk = CURRICULUM_ROOT / args.level / "research" / f"{slug}-knowledge-packet.md"
                    if _pk.exists():
                        _heal_packet = _pk
                        _log(f"   Loaded packet from disk ({_pk.name})")

                _heal_verification = verification_text
                if not _heal_verification:
                    _vp = _orch_dir / "pre-verify-results.md"
                    if _vp.exists():
                        _heal_verification = _vp.read_text("utf-8")

                # CRITICAL: step_write_chunked caches individual section chunks
                # as chunk-NN.md files and reuses them on subsequent calls. We
                # need ALL chunks to be rewritten with the new salad rule, so
                # nuke the cache before regen.
                _chunk_cache_count = 0
                for _chunk_file in _orch_dir.glob("chunk-*.md"):
                    try:
                        _chunk_file.unlink()
                        _chunk_cache_count += 1
                    except OSError as _e:
                        _log(f"   ⚠️  Could not delete {_chunk_file.name}: {_e}")
                if _chunk_cache_count:
                    _log(f"   🗑️  Cleared {_chunk_cache_count} cached chunk(s) to force fresh regen")

                if _heal_packet is None:
                    _log("   ❌ No knowledge packet available on disk — cannot regenerate prose. Run --step research first.")
                    _new_content_path = None
                try:
                    _new_content_path = step_write_with_retry(
                        args.level, args.module, slug,
                        packet_path=_heal_packet,
                        writer=args.writer,
                        # Heal regen gets 3 attempts (was 1). The single-shot
                        # heal was producing friction reports labeled "Exhausted
                        # 1 attempts" because it couldn't apply a correction
                        # directive even when quick_verify had a clear fix path.
                        # 3 attempts = first regen + 2 corrected retries — same
                        # economics as the main write loop's recovery budget,
                        # capped lower to keep heal time bounded. (#1189)
                        max_retries=2,
                        skeleton=_heal_skeleton,
                        no_chunk=args.no_chunk,
                        verification_text=_heal_verification,
                    ) if _heal_packet is not None else None
                    if _new_content_path:
                        content_path = _new_content_path
                        _post_process_content(content_path)
                        _salad_regen_ran = True
                        _log("\n  🔁 Prose regenerated — re-auditing")
                        step_audit(content_path, args.level, slug)
                        # Re-check all the conditions that triggered the
                        # regen and report what cleared vs. what's still
                        # broken. If any blocker remains, the user will
                        # see it clearly in the log.
                        try:
                            _status = json.loads(_status_path.read_text("utf-8"))
                            _overall_status = _status.get("overall", {}).get("status", "unknown")
                            _lesson = _status.get("gates", {}).get("lesson", {})
                            _lesson_msg = _lesson.get("message", "") if isinstance(_lesson, dict) else ""
                            _still_salad = "salad" in _lesson_msg.lower() or "SALAD" in _lesson_msg
                            _still_eng_bad = False
                            if "engagement" in _lesson_msg.lower():
                                _m = re.search(
                                    r"engagement:\s*(\d+)\s*/\s*(\d+)",
                                    _lesson_msg, re.IGNORECASE,
                                )
                                if _m and int(_m.group(1)) < int(_m.group(2)):
                                    _still_eng_bad = True
                            if _salad_gate_failed and _still_salad:
                                _log("\n  ⚠️  Salad still present after regen — manual review needed")
                            elif _salad_gate_failed:
                                _log("\n  ✅ Salad cleared after regen")
                            if _engagement_gate_failed and _still_eng_bad:
                                _log("\n  ⚠️  Engagement still missing after regen — manual review needed")
                            elif _engagement_gate_failed:
                                _log("\n  ✅ Engagement callouts added after regen")
                        except Exception:
                            pass
                    else:
                        _log("\n  ❌ Prose regen failed — leaving original content intact")
                except Exception as _e:
                    _log(f"\n  ⚠️  Prose regen raised: {_e}")

            # Other content-level failures (immersion %, robotic prose, inline
            # English in UK paragraphs, etc.) still need a review+fix pass.
            # Engagement + salad are handled by the regen branch above, so by
            # the time we reach this block, any remaining failure is something
            # the pipeline can't deterministically heal.
            if (
                _overall_status not in ("pass", "content-complete")
                and not _activity_gate_failed
                and not _salad_regen_ran
            ):
                _log(
                    f"\n⚠️  Audit still failing ({_overall_status}) with content-level issues "
                    "that the heal loop cannot fix automatically."
                )
                _log("   These need a writer/review pass: immersion %, robotic prose,")
                _log("   inline English in UK prose — run `--step review` or regen prose.")

            _final_overall_status, _failing_audit_gates = _get_failing_audit_gates(args.level, slug)
            if _failing_audit_gates and not args.force_publish:
                _log("\n❌ PUBLISH BLOCKED: audit gates still failing after heal")
                _log(f"   Overall status: {_final_overall_status}")
                _log(f"   Failing gates: {', '.join(_failing_audit_gates)}")
                _log("   Re-run with --force-publish to override (not recommended)")
                _emit_phase_done("audit", _phase_start)
                return False
            _emit_phase_done("audit", _phase_start)

        # Step 10: PUBLISH — now runs AFTER audit + heal so MDX reflects final state
        # Re-publishes if audit just ran, even if publish was marked complete —
        # because the heal block may have modified activities.
        if steps in ("all", "review", "publish") and (_pre_audit_ran or "publish" not in completed_phases):
            _phase_start = time.monotonic()
            step_publish(content_path, args.level, slug)
            _save_v6_state(args.level, slug, "publish")
            _emit_phase_done("publish", _phase_start)
            publish_completed = True

        # Mark audit phase complete (it already ran pre-publish above)
        if _pre_audit_ran:
            _save_v6_state(args.level, slug, "audit")

        # Generate orchestration index (#1029)
        from build.orch_index import generate_index
        result = generate_index(args.level, slug)
        if result:
            _log(f"  📋 Orchestration index → {slug}/index.md")

        _build_elapsed = time.monotonic() - _build_start
        _minutes = int(_build_elapsed // 60)
        _seconds = int(_build_elapsed % 60)
        _log(f"\n✅ V6 Build COMPLETE: {args.level.upper()} M{args.module:02d} ({slug})")
        if args.range is None:
            cost_summary_line = format_module_cost_summary(args.level, slug)
            if cost_summary_line:
                _log(f"   {cost_summary_line}")
        _log(f"   Total time: {_minutes}m {_seconds}s")
        if publish_completed:
            if final_score is None:
                _final_review = _load_latest_review_result(args.level, slug)
                if _final_review:
                    final_score = _final_review.score
            emit_event(
                "module_done",
                level=args.level,
                slug=slug,
                ok=True,
                final_score=final_score,
                duration_s=round(_build_elapsed, 3),
            )

        return True
    finally:
        build_lock.release()


if __name__ == "__main__":
    raise SystemExit(0 if main() is not False else 1)
