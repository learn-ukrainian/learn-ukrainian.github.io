#!/usr/bin/env python3
"""Hramatka-specific quality-gate rule set (selectable, never mixed with curriculum PHRASE_RULES).

Deterministic ($0, no-LLM) checks for generative hramatka lesson_json artifacts.
Call local Python APIs only — never shell out to MCP.

Tier-1: russianism/surzhyk/calque · invalid distractor (incl. degenerate reuse) · answer-key placeholder
Tier-2: structural activity integrity · empty learner surface · task-language CEFR · invented form

Issue: load-bearing QG for hramatka (#5187 feedback). Calibrated against real
generated-lesson defects, not just synthetic planted faults (#5254).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Prefer sibling imports when AUDIT_DIR is on sys.path (CLI harness mode).
try:
    from checks.russicism_detection import check_russicisms, check_ua_gec_calques
    from llm_qg_store import CONTENT_FILES, content_sha_for_module
except ImportError:  # pragma: no cover - package import under pytest
    from scripts.audit.checks.russicism_detection import (
        check_russicisms,
        check_ua_gec_calques,
    )
    from scripts.audit.llm_qg_store import CONTENT_FILES, content_sha_for_module

from scripts.lexicon.heritage_classifier import (
    classify_surface_form,
    has_positive_attestation,
)
from scripts.verification.vesum import verify_word

RULE_SET_ID = "hramatka"
CHECKER_VERSION = "hramatka_ua_qg_rules.v2"
EVIDENCE_SCHEMA_VERSION = "hramatka_ua_qg_evidence.v1"
FIXTURE_SCHEMA_VERSION = "hramatka_ua_qg_fixtures.v1"

DIMENSION_ORDER = (
    "russianism_calque",
    "distractor_quality",
    "answer_key_integrity",
    "activity_structure",
    "learner_surface",
    "task_cefr",
    "invented_form",
)
SEVERITY_WEIGHTS = {"critical": 2.5, "warning": 0.75, "info": 0.0}

# Internal / privacy fields — never land in learner-facing serialization.
_EXCLUDED_KEYS = frozenset(
    {
        "provenance",
        "mark",
        "phase",
        "note",
        "teacher_notes",
        "teacher-notes",
        "system_prompt",
        "system-prompt",
        "rationale",
        "metadata",
        "edited",
        "last_error",
        "accepted",
        "status",
        "version",
        "duration",
        "method",
        "focus",
        "id",  # block/activity UUIDs are internal
        "chars",
        "source",  # anchor.source is teacher-pipeline provenance
        "gates",
        "generator",
        "external_options",
    }
)

# Keys retained when walking activity trees (learner-facing surface).
_ACTIVITY_KEEP_KEYS = frozenset(
    {
        "type",
        "title",
        "level",
        "mode",
        "activity",
        "answer_key",
        "hint",
        "explanation",
        "payload",
        "instruction",
        "items",
        "options",
        "pairs",
        "prompt",
        "statement",
        "term",
        "gloss",
        "text",
        "correct",
        "left",
        "right",
        "index",
        "left_index",
        "right_index",
        "guidance",
        "blanks",
        "answers",
        "blank_count",
        "stem",
        "choices",
        "question",
        "label",
        "value",
        "gloss_lang",
    }
)

_CYRILLIC_TOKEN_RE = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ][А-Яа-яЁёІіЇїЄєҐґ'ʼ’\-]*")
# Pedagogical stress annotation (наголос) — combining acute/grave accent after a
# vowel, e.g. "соро́чка". Real hramatka anchors carry these; stripped before
# tokenizing so a stressed word attests against VESUM as one token instead of
# shattering into fragments ("соро" + "чка") that false-fire NON_VESUM_FORM /
# RUSSIAN_SHADOW_RUSSICISM. Verified against real generated soak lessons (#5254).
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")
# Whole-value placeholders only — ellipsis inside a real answer is not a placeholder.
_PLACEHOLDER_EXACT_RE = re.compile(
    r"(?:"
    r"TODO|XXX|TBD|"
    r"\.\.\.|…|"
    r"answer\s*here|"
    r"відповідь\s*тут|"
    r"placeholder|"
    r"\[\s*\]|"
    r"\{\s*\}"
    r")",
    re.IGNORECASE,
)
_OPTION_PREFIX_RE = re.compile(r"^[а-яіїєґa-z0-9]+[).\:\-]\s*", re.IGNORECASE)
# Cloze blanks: ____ / {{slot}} / [___] / [___:1]
_CLOZE_BLANK_RE = re.compile(r"_{2,}|\{\{[^}]+\}\}|\[_{1,}(?::[^\]]+)?\]")
_APOSTROPHES = ("'", "ʼ", "’", "`")
_FREE_RESPONSE_TYPES = frozenset(
    {
        "continue-sentence",
        "continue_sentence",
        "roleplay-dialog",
        "roleplay",
        "short-writing",
        "free-writing",
        "discussion",
        "glossary",
        "reading",
        "text",
    }
)

_CEFR_RANK = {"a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6}
_HERITAGE_SAFE = frozenset(
    {
        "authentic-archaism",
        "dialect",
        "historism",
        "borrowing",
        "standard",
    }
)


@dataclass(frozen=True, slots=True)
class AdaptedLesson:
    """Learner-facing module-dir payload derived from lesson_json."""

    title: str
    level: str
    slug: str
    module_md: str
    activities: list[dict[str, Any]]
    vocabulary: list[Any]
    resources: list[Any]
    content_hash: str
    excluded_keys_seen: tuple[str, ...] = ()
    learner_strings: tuple[tuple[str, str], ...] = ()  # (path, text)


@dataclass
class _ScanContext:
    level: str
    texts: dict[str, str]
    activities: list[dict[str, Any]]
    learner_strings: list[tuple[str, str]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def checker_config_hash() -> str:
    """Stable hash for the hramatka deterministic rule configuration."""
    payload = {
        "checker_version": CHECKER_VERSION,
        "rule_set": RULE_SET_ID,
        "dimensions": DIMENSION_ORDER,
        "severity_weights": SEVERITY_WEIGHTS,
        "excluded_keys": sorted(_EXCLUDED_KEYS),
        "checks": [
            "russianism_calque",
            "invalid_distractor",
            "degenerate_distractor_reuse",
            "answer_key_placeholder",
            "structural_activity_integrity",
            "empty_learner_surface",
            "task_language_cefr",
            "invented_form",
        ],
    }
    return _sha256_text(_json_dumps(payload))


def _line_no(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _span_for_excerpt(text: str, excerpt: str, line_hint: int | None = None) -> dict[str, int | None]:
    start = text.find(excerpt)
    if start < 0 and line_hint:
        lines = text.splitlines(keepends=True)
        prefix_len = sum(len(line) for line in lines[: max(line_hint - 1, 0)])
        line_text = lines[line_hint - 1] if 0 <= line_hint - 1 < len(lines) else ""
        line_offset = line_text.find(excerpt)
        if line_offset >= 0:
            start = prefix_len + line_offset
    if start < 0:
        return {"start": None, "end": None}
    return {"start": start, "end": start + len(excerpt)}


def _finding(
    *,
    issue_id: str,
    rule_id: str,
    dimension: str,
    severity: str,
    file: str,
    line: int,
    excerpt: str,
    message: str,
    text: str,
    source: str = "hramatka_deterministic",
) -> dict[str, Any]:
    span = _span_for_excerpt(text, excerpt, line)
    return {
        "issue_id": issue_id,
        "rule_id": rule_id,
        "dimension": dimension,
        "severity": severity,
        "source": source,
        "file": file,
        "line": line,
        "span": span,
        "excerpt": excerpt[:160],
        "message": message,
    }


def _strip_internal(value: Any, *, seen_excluded: set[str] | None = None) -> Any:
    """Deep-copy JSON-like data, dropping excluded internal keys."""
    excluded = seen_excluded if seen_excluded is not None else set()
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, child in value.items():
            key_s = str(key)
            if key_s in _EXCLUDED_KEYS:
                excluded.add(key_s)
                continue
            out[key_s] = _strip_internal(child, seen_excluded=excluded)
        return out
    if isinstance(value, list):
        return [_strip_internal(item, seen_excluded=excluded) for item in value]
    return value


def _collect_strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    """Collect non-empty string leaves from a learner-facing tree."""
    out: list[tuple[str, str]] = []
    if isinstance(value, str):
        text = value.strip()
        if text:
            out.append((path or "text", text))
        return out
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            out.extend(_collect_strings(child, child_path))
        return out
    if isinstance(value, list):
        for idx, child in enumerate(value):
            out.extend(_collect_strings(child, f"{path}[{idx}]"))
        return out
    return out


def _normalize_level(level: Any) -> str:
    return str(level or "b1").strip().lower()


def _slug_from_title(title: str, fallback: str = "hramatka-lesson") -> str:
    raw = re.sub(r"[^\w\s\-а-яіїєґА-ЯІЇЄҐ]", "", title, flags=re.UNICODE)
    raw = re.sub(r"\s+", "-", raw.strip()).strip("-").casefold()
    return raw[:80] if raw else fallback


def adapt_lesson_json(
    lesson: Mapping[str, Any],
    *,
    slug: str | None = None,
) -> AdaptedLesson:
    """Field-disciplined lesson_json → learner-facing module payload.

    KEEP: title, level, anchor.text, block.activity, block.answer_key, hint/explanation
    EXCLUDE: provenance, mark, phase, teacher notes, system-prompt, rationale, metadata
    """
    if not isinstance(lesson, Mapping):
        raise ValueError("lesson_json must be a mapping")

    seen_excluded: set[str] = set()
    title = str(lesson.get("title") or "").strip()
    level = _normalize_level(lesson.get("level"))
    clean_slug = slug or _slug_from_title(title)

    anchor = lesson.get("anchor")
    anchor_text = ""
    if isinstance(anchor, Mapping):
        anchor_text = str(anchor.get("text") or "").strip()
        for key in anchor:
            if str(key) in _EXCLUDED_KEYS or str(key) in {"source", "chars"}:
                seen_excluded.add(str(key))
    elif isinstance(anchor, str):
        anchor_text = anchor.strip()

    activities: list[dict[str, Any]] = []
    blocks = lesson.get("blocks")
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, Mapping):
                continue
            for key in block:
                if str(key) in _EXCLUDED_KEYS:
                    seen_excluded.add(str(key))
            cleaned_block: dict[str, Any] = {}
            block_type = block.get("type")
            if block_type is not None:
                cleaned_block["type"] = block_type
            activity = block.get("activity")
            if isinstance(activity, Mapping):
                cleaned_block["activity"] = _strip_internal(activity, seen_excluded=seen_excluded)
            answer_key = block.get("answer_key")
            if answer_key is not None:
                cleaned_block["answer_key"] = _strip_internal(answer_key, seen_excluded=seen_excluded)
            for keep in ("hint", "explanation"):
                if keep in block and block[keep] is not None:
                    cleaned_block[keep] = _strip_internal(block[keep], seen_excluded=seen_excluded)
            if cleaned_block:
                activities.append(cleaned_block)

    # Top-level internal keys recorded for auditability of exclusion discipline.
    for key in lesson:
        if str(key) in _EXCLUDED_KEYS:
            seen_excluded.add(str(key))

    module_lines = [f"# {title}" if title else "# Hramatka lesson", ""]
    if anchor_text:
        module_lines.extend(["## Anchor", "", anchor_text, ""])
    for idx, act in enumerate(activities, start=1):
        act_body = act.get("activity") if isinstance(act.get("activity"), Mapping) else act
        act_title = ""
        if isinstance(act_body, Mapping):
            act_title = str(act_body.get("title") or act.get("type") or f"Activity {idx}")
        else:
            act_title = str(act.get("type") or f"Activity {idx}")
        module_lines.extend([f"## {act_title}", ""])
        for path, text in _collect_strings(act):
            if path.endswith(".type") or path.endswith(".level") or path.endswith(".mode"):
                continue
            module_lines.append(text)
            module_lines.append("")

    module_md = "\n".join(module_lines).rstrip() + "\n"
    learner_strings = _collect_strings({"title": title, "anchor": anchor_text, "activities": activities})

    canonical = {
        "title": title,
        "level": level,
        "slug": clean_slug,
        "anchor_text": anchor_text,
        "activities": activities,
    }
    content_hash = _sha256_text(_json_dumps(canonical))

    return AdaptedLesson(
        title=title,
        level=level,
        slug=clean_slug,
        module_md=module_md,
        activities=activities,
        vocabulary=[],
        resources=[],
        content_hash=content_hash,
        excluded_keys_seen=tuple(sorted(seen_excluded)),
        learner_strings=tuple(learner_strings),
    )


def write_adapted_module_dir(adapted: AdaptedLesson, dest: Path) -> Path:
    """Serialize an AdaptedLesson into CONTENT_FILES under dest."""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "module.md").write_text(adapted.module_md, encoding="utf-8")
    (dest / "activities.yaml").write_text(
        yaml.safe_dump(adapted.activities, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (dest / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (dest / "resources.yaml").write_text("[]\n", encoding="utf-8")
    meta = {
        "rule_set": RULE_SET_ID,
        "level": adapted.level,
        "slug": adapted.slug,
        "title": adapted.title,
        "content_hash": adapted.content_hash,
        "excluded_keys_seen": list(adapted.excluded_keys_seen),
    }
    (dest / "hramatka_adapter_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return dest


def adapt_lesson_json_to_module_dir(
    lesson: Mapping[str, Any],
    dest: Path,
    *,
    slug: str | None = None,
) -> AdaptedLesson:
    """Adapt lesson_json and write a harness-compatible module directory."""
    adapted = adapt_lesson_json(lesson, slug=slug)
    write_adapted_module_dir(adapted, dest)
    return adapted


# ---------------------------------------------------------------------------
# Token / form helpers
# ---------------------------------------------------------------------------


def _strip_stress_marks(text: str) -> str:
    return _STRESS_MARK_RE.sub("", text)


def _cyrillic_tokens(text: str) -> list[str]:
    return _CYRILLIC_TOKEN_RE.findall(_strip_stress_marks(text))


def _apostrophe_variants(token: str) -> list[str]:
    """Generate apostrophe + case variants for VESUM lookup."""
    variants: list[str] = []
    seen: set[str] = set()
    base_forms = [token, token.casefold()]
    for form in base_forms:
        for apo in _APOSTROPHES:
            candidate = form
            for other in _APOSTROPHES:
                candidate = candidate.replace(other, apo)
            if candidate not in seen:
                seen.add(candidate)
                variants.append(candidate)
        if form not in seen:
            seen.add(form)
            variants.append(form)
    return variants


# Optional path overrides — tests inject controlled SQLite DBs so CI never
# depends on ambient sources.db / vesum.db fullness. Production leaves these None.
_SOURCES_DB_OVERRIDE: Path | None = None
_VESUM_DB_OVERRIDE: Path | None = None
_HERITAGE_DB_OVERRIDE: Path | None = None


def _vesum_hits(token: str) -> list[dict]:
    """VESUM lookup tolerant of apostrophe orthography and proper-noun case.

    Missing VESUM DB → empty + detector_unavailable (never crash the gate).
    """
    try:
        for variant in _apostrophe_variants(token):
            hits = verify_word(variant, db_path=_VESUM_DB_OVERRIDE)
            if hits:
                return hits
    except (FileNotFoundError, OSError, sqlite3.Error) as exc:
        _mark_detector_unavailable("vesum", str(exc))
        return []
    return []


def _vesum_detector_unavailable() -> bool:
    """True when this scan already recorded VESUM as unavailable."""
    store = _ACTIVE_UNAVAILABLE.get()
    return bool(store and "vesum" in store)


def _is_probable_proper_noun(token: str) -> bool:
    """Capitalized / title-case tokens are proper-noun or sentence-initial candidates.

    Invented-form and russian-shadow gates must not flag place names (Львів),
    personal names (Оля), or sentence-initial ordinary words that look capitalized.
    ALL-CAPS acronyms are also excluded (not ordinary invented lemmas).
    """
    if not token:
        return False
    if token.isupper() and len(token) >= 2:
        return True
    return token[0].isupper()


def _normalize_option(text: str) -> str:
    cleaned = _OPTION_PREFIX_RE.sub("", str(text or "").strip())
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    if isinstance(value, (int, float, bool)):
        return False
    text = str(value).strip()
    if not text:
        return True
    # Whole value is a placeholder token, not merely contains "…" inside prose.
    return bool(_PLACEHOLDER_EXACT_RE.fullmatch(text))


def _activity_body(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    activity = entry.get("activity")
    if isinstance(activity, Mapping):
        return activity
    return entry


def _payload(activity: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = activity.get("payload")
    return payload if isinstance(payload, Mapping) else {}


def _answer_key_for(entry: Mapping[str, Any], activity: Mapping[str, Any]) -> Any:
    """Prefer structured activity-level answer_key over free-text block key."""
    act_key = activity.get("answer_key")
    block_key = entry.get("answer_key") if "answer_key" in entry else None
    if isinstance(act_key, (Mapping, list)):
        return act_key
    if block_key is not None:
        return block_key
    return act_key


def _load_activities_from_module(module_dir: Path) -> list[dict[str, Any]]:
    path = module_dir / "activities.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, Mapping) and isinstance(data.get("activities"), list):
        return [item for item in data["activities"] if isinstance(item, dict)]
    return []


def _read_module_texts(module_dir: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for name in CONTENT_FILES:
        path = module_dir / name
        if path.exists():
            texts[name] = path.read_text(encoding="utf-8")
    return texts


def _locate_in_texts(texts: Mapping[str, str], excerpt: str) -> tuple[str, int, str]:
    for name in ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml"):
        text = texts.get(name, "")
        if excerpt and excerpt in text:
            return name, _line_no(text, text.find(excerpt)), text
    # Fallback: module.md body
    text = texts.get("module.md", "")
    return "module.md", 1, text


def _heritage_safe(status: Mapping[str, Any]) -> bool:
    classification = str(status.get("classification") or "")
    if classification in {"authentic-archaism", "dialect", "historism", "borrowing"}:
        return True
    try:
        attested = bool(status.get("vesum_attested") or has_positive_attestation(status))
    except (FileNotFoundError, OSError, sqlite3.Error) as exc:
        _mark_detector_unavailable("heritage_classifier", str(exc))
        attested = bool(status.get("vesum_attested"))
    return classification == "standard" and attested


def _unknown_token_status() -> dict[str, Any]:
    return {
        "classification": "unknown",
        "attestations": [],
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": False,
        "sovietization_risk": 0,
        "calque_warning": None,
    }


def _hyphen_compound_all_attested(token: str) -> bool:
    """True when every hyphen-separated part of a compound is its own VESUM word.

    Appositive noun+noun compounds (текст-опора, речення-опора, держав-учасниць)
    are not VESUM lemmas as a whole, but both halves independently are. Without
    this check the per-token russian-shadow / invented-form pass sees one
    VESUM-absent blob and misfires — a real false-fail found on real generated
    hramatka content (#5254).
    """
    if "-" not in token:
        return False
    parts = [p for p in token.split("-") if p]
    if len(parts) < 2:
        return False
    return all(_vesum_hits(part) for part in parts)


def _classify_token(token: str) -> dict[str, Any]:
    """Classify with VESUM-first short-circuit (performance + apostrophe tolerance).

    Partial sources.db / missing VESUM → degrade to unknown (no crash).
    """
    if _vesum_hits(token) or _hyphen_compound_all_attested(token):
        return {
            "classification": "standard",
            "attestations": [{"source": "vesum", "ref": token}],
            "is_russianism": False,
            "russian_shadow": False,
            "vesum_attested": True,
            "sovietization_risk": 0,
            "calque_warning": None,
        }
    if _is_probable_proper_noun(token):
        # Proper nouns / capitalized names absent from VESUM are not russianisms
        # or invented forms; content lane may still review them.
        return {
            "classification": "proper_noun",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "vesum_attested": False,
            "sovietization_risk": 0,
            "calque_warning": None,
        }
    # heritage_classifier always overrides when it attests; russian-shadow is a signal.
    try:
        return classify_surface_form(
            token.casefold(),
            db_path=_HERITAGE_DB_OVERRIDE,
            vesum_db_path=_VESUM_DB_OVERRIDE,
        )
    except (FileNotFoundError, OSError, sqlite3.Error) as exc:
        _mark_detector_unavailable("heritage_classifier", str(exc))
        return _unknown_token_status()


def _is_russianism_token(token: str, status: Mapping[str, Any] | None = None) -> bool:
    """Return True when token is a russianism after heritage override."""
    if _is_probable_proper_noun(token):
        return False
    # Without VESUM we cannot assert "VESUM-absent ∧ russian-shadow".
    if _vesum_detector_unavailable():
        return False
    status = status or _classify_token(token)
    if status.get("is_russianism"):
        return True
    if _heritage_safe(status):
        return False
    if status.get("classification") in {"proper_noun", "borrowing"}:
        return False
    # VESUM-absent AND russian-shadow AND NOT heritage → russianism
    return bool((not status.get("vesum_attested")) and status.get("russian_shadow"))


def _is_invented_form(token: str, status: Mapping[str, Any] | None = None) -> bool:
    """Flag only lower-case non-proper forms that fail VESUM + heritage gates.

    Precision rules (noisy gate is useless):
    - Proper nouns / capitalized names / ALL-CAPS → never invented.
    - Heritage-safe (standard/borrowing/dialect/archaism/historism) → never invented.
    - VESUM unavailable this scan → stay quiet (cannot prove absence).
    - Russian-shadow forms route to RUSSIAN_SHADOW_RUSSICISM, not NON_VESUM_FORM.
    """
    if _is_probable_proper_noun(token):
        return False
    if _vesum_detector_unavailable():
        return False
    status = status or _classify_token(token)
    if _heritage_safe(status):
        return False
    if status.get("classification") in {"proper_noun", "borrowing"}:
        return False
    if status.get("is_russianism") or status.get("russian_shadow"):
        return False
    if status.get("vesum_attested"):
        return False
    # VESUM-absent AND NOT russian-shadow AND NOT heritage
    return str(status.get("classification") or "unknown") in {"unknown", ""}


# ---------------------------------------------------------------------------
# Synonym + CEFR local lookups (direct SQL; same DBs as sources_db)
# ---------------------------------------------------------------------------

# Scan-scoped map of unavailable sub-detectors → reason. Partial sources.db
# (CI stripped builds) must degrade, never crash the harness.
_ACTIVE_UNAVAILABLE: ContextVar[dict[str, str] | None] = ContextVar(
    "hramatka_qg_unavailable_detectors",
    default=None,
)


def _mark_detector_unavailable(detector: str, reason: str) -> None:
    store = _ACTIVE_UNAVAILABLE.get()
    if store is None:
        return
    store.setdefault(detector, reason)


def _is_missing_table_error(exc: BaseException) -> bool:
    if not isinstance(exc, sqlite3.OperationalError):
        return False
    msg = str(exc).casefold()
    return "no such table" in msg or "no such column" in msg


def _sources_conn():
    db = _SOURCES_DB_OVERRIDE or (PROJECT_ROOT / "data" / "sources.db")
    if not db.exists():
        return None
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    return conn


def _synonym_lemmas(word: str) -> set[str]:
    """Return known synonym partners for a Ukrainian lemma (local sources.db)."""
    word_n = word.casefold().strip()
    if not word_n:
        return set()
    partners: set[str] = set()
    conn = _sources_conn()
    if conn is None:
        _mark_detector_unavailable("ukrajinet_synonyms", "sources.db missing")
        return partners
    try:
        rows = conn.execute(
            "SELECT words FROM ukrajinet WHERE words LIKE ? COLLATE NOCASE LIMIT 40",
            (f"%{word_n}%",),
        ).fetchall()
        for row in rows:
            raw = row["words"]
            try:
                members = json.loads(raw) if isinstance(raw, str) else raw
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(members, list):
                continue
            normalized = [str(m).casefold().strip() for m in members if isinstance(m, str)]
            # Only pure Cyrillic single-token members count.
            cyr = [m for m in normalized if _CYRILLIC_TOKEN_RE.fullmatch(m)]
            if word_n in cyr:
                partners.update(m for m in cyr if m != word_n)
    except sqlite3.OperationalError as exc:
        if _is_missing_table_error(exc):
            _mark_detector_unavailable("ukrajinet_synonyms", str(exc))
            return partners
        raise
    finally:
        conn.close()
    return partners


def _are_synonyms(a: str, b: str) -> bool:
    a_n = a.casefold().strip()
    b_n = b.casefold().strip()
    if not a_n or not b_n or a_n == b_n:
        return False
    return b_n in _synonym_lemmas(a_n) or a_n in _synonym_lemmas(b_n)


def _cefr_level_for(word: str) -> str | None:
    conn = _sources_conn()
    if conn is None:
        _mark_detector_unavailable("puls_cefr", "sources.db missing")
        return None
    try:
        row = conn.execute(
            "SELECT level FROM puls_cefr WHERE word = ? COLLATE NOCASE LIMIT 1",
            (word,),
        ).fetchone()
        if row and row["level"]:
            return str(row["level"]).strip().lower()
        row = conn.execute(
            "SELECT level FROM puls_cefr WHERE lower(word) = ? LIMIT 1",
            (word.casefold(),),
        ).fetchone()
        if row and row["level"]:
            return str(row["level"]).strip().lower()
    except sqlite3.OperationalError as exc:
        if _is_missing_table_error(exc):
            _mark_detector_unavailable("puls_cefr", str(exc))
            return None
        raise
    finally:
        conn.close()
    return None


def _cefr_exceeds(task_level: str, word_level: str) -> bool:
    """Flag only clear over-level words (≥2 CEFR bands above the lesson)."""
    return _CEFR_RANK.get(word_level, 0) >= _CEFR_RANK.get(task_level, 0) + 2


def _antonenko_title_hit(text: str) -> list[str]:
    """Return Antonenko style-guide titles whose *bad multi-word form* appears in text.

    Only multi-token left-hand sides of ``bad – good`` titles count. Single-token
    left sides (e.g. "Жити–бути") are too ambiguous for a deterministic gate.

    Missing ``style_guide`` (CI stripped sources.db) → empty + detector_unavailable.
    """
    conn = _sources_conn()
    if conn is None:
        _mark_detector_unavailable("antonenko_style_guide", "sources.db missing")
        return []
    hits: list[str] = []
    folded = text.casefold()
    try:
        rows = conn.execute(
            "SELECT word FROM style_guide WHERE word LIKE '%–%' OR word LIKE '%—%'"
        ).fetchall()
        for row in rows:
            title = str(row["word"] or "").strip()
            if not title:
                continue
            parts = re.split(r"\s*[–—]\s*", title, maxsplit=1)
            if len(parts) < 2:
                continue
            bad_side = parts[0].strip().casefold()
            # Require multi-word bad form (e.g. "приймати участь").
            tokens = _cyrillic_tokens(bad_side)
            if len(tokens) < 2:
                continue
            for candidate in re.split(r"[,;]", bad_side):
                cand = candidate.strip()
                cand_tokens = _cyrillic_tokens(cand)
                if len(cand_tokens) < 2:
                    continue
                if cand in folded:
                    hits.append(title)
                    break
    except sqlite3.OperationalError as exc:
        if _is_missing_table_error(exc):
            _mark_detector_unavailable("antonenko_style_guide", str(exc))
            return []
        raise
    finally:
        conn.close()
    return hits


# ---------------------------------------------------------------------------
# Check classes
# ---------------------------------------------------------------------------


def _safe_curated_russicisms(text: str, file_path: str) -> list[dict]:
    """Curated regex russicisms; never let a broken helper crash the gate."""
    try:
        return list(check_russicisms(text, file_path=file_path) or [])
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
        _mark_detector_unavailable("check_russicisms", str(exc))
        return []


def _safe_ua_gec_calques(text: str, file_path: str) -> list[dict]:
    """UA-GEC calques (CSV-backed); degrade if the lookup table cannot load."""
    try:
        return list(check_ua_gec_calques(text, file_path=file_path) or [])
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
        _mark_detector_unavailable("ua_gec_calques", str(exc))
        return []


def check_russianism_calque(ctx: _ScanContext) -> list[dict[str, Any]]:
    """Tier-1: curated regex + UA-GEC + VESUM/shadow with heritage override."""
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    surfaces = list(ctx.learner_strings)
    if not surfaces:
        for file, text in ctx.texts.items():
            surfaces.append((file, text))

    for _path, text in surfaces:
        if not text or not text.strip():
            continue
        file, line, file_text = _locate_in_texts(ctx.texts, text[:80] if len(text) > 80 else text)

        # 1) Curated regex / high-precision patterns (reused from qg_adapters stack)
        for violation in _safe_curated_russicisms(text, file):
            excerpt = str(violation.get("matched") or text[:80])
            # check_russicisms aggregates; pull matched terms from issue when needed
            issue = str(violation.get("issue") or "Russicism detected")
            key = ("RUSSICISM_DETECTED", issue[:80])
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                _finding(
                    issue_id="RUSSICISM_DETECTED",
                    rule_id="hramatka_russianism_curated",
                    dimension="russianism_calque",
                    severity=str(violation.get("severity") or "warning"),
                    file=file,
                    line=line,
                    excerpt=excerpt if excerpt in file_text else text[:80],
                    message=issue,
                    text=file_text,
                )
            )

        # 2) UA-GEC exact-span calques — multi-word only (single tokens are too noisy;
        # curated check_russicisms already covers high-precision single-token forms).
        for violation in _safe_ua_gec_calques(text, file):
            matched = str(violation.get("matched") or "")
            if not matched or " " not in matched.strip():
                continue
            key = ("UA_GEC_CALQUE", matched.casefold())
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                _finding(
                    issue_id="UA_GEC_CALQUE",
                    rule_id="hramatka_ua_gec_calque",
                    dimension="russianism_calque",
                    severity="warning",
                    file=file,
                    line=line,
                    excerpt=matched,
                    message=str(violation.get("issue") or f"UA-GEC calque: {matched}"),
                    text=file_text,
                )
            )

        # 3) Antonenko structured title hits
        for title in _antonenko_title_hit(text):
            key = ("ANTONENKO_CALQUE", title.casefold())
            if key in seen:
                continue
            seen.add(key)
            # Excerpt = bad side of title
            bad = re.split(r"\s*[–—]\s*|\s+-\s+", title, maxsplit=1)[0].strip()
            findings.append(
                _finding(
                    issue_id="ANTONENKO_CALQUE",
                    rule_id="hramatka_antonenko_style_guide",
                    dimension="russianism_calque",
                    severity="warning",
                    file=file,
                    line=line,
                    excerpt=bad[:160],
                    message=f"Antonenko-Davydovych style guide flags: {title}",
                    text=file_text,
                )
            )

        # 4) Per-token russian-shadow + heritage override (VESUM-first short-circuit)
        for token in _cyrillic_tokens(text):
            if len(token) < 3 or token.endswith("-"):
                continue
            status = _classify_token(token)
            if _heritage_safe(status) or status.get("vesum_attested"):
                continue
            if _is_russianism_token(token, status):
                key = ("RUSSIAN_SHADOW_RUSSICISM", token.casefold())
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    _finding(
                        issue_id="RUSSIAN_SHADOW_RUSSICISM",
                        rule_id="hramatka_russian_shadow_not_heritage",
                        dimension="russianism_calque",
                        severity="critical",
                        file=file,
                        line=line,
                        excerpt=token,
                        message=(
                            f"Form '{token}' is absent from VESUM with Russian-shadow morphology "
                            "and no heritage attestation (heritage_classifier does not override)."
                        ),
                        text=file_text,
                    )
                )
    return findings


def check_invented_forms(ctx: _ScanContext) -> list[dict[str, Any]]:
    """Tier-2: VESUM-absent AND NOT russian-shadow AND NOT heritage → NON_VESUM_FORM."""
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    surfaces = list(ctx.learner_strings) or [(f, t) for f, t in ctx.texts.items()]
    for _path, text in surfaces:
        if not text:
            continue
        file, line, file_text = _locate_in_texts(ctx.texts, text[:80] if len(text) > 80 else text)
        for token in _cyrillic_tokens(text):
            if len(token) < 4 or token.endswith("-"):
                continue
            key = token.casefold()
            if key in seen:
                continue
            status = _classify_token(token)
            if not _is_invented_form(token, status):
                continue
            seen.add(key)
            findings.append(
                _finding(
                    issue_id="NON_VESUM_FORM",
                    rule_id="hramatka_invented_form",
                    dimension="invented_form",
                    severity="warning",
                    file=file,
                    line=line,
                    excerpt=token,
                    message=(
                        f"Form '{token}' is not in VESUM, has no Russian-shadow signal, "
                        "and no heritage attestation — likely invented form."
                    ),
                    text=file_text,
                )
            )
    return findings


def _iter_mc_items(activity: Mapping[str, Any]) -> Iterable[tuple[str, list[str], Any]]:
    """Yield (prompt, options, correct_answer) for multiple-choice style items."""
    payload = _payload(activity)
    items = payload.get("items") or activity.get("items") or []
    if not isinstance(items, list):
        return
    answer_key = activity.get("answer_key")
    key_items: list[Any] = []
    if isinstance(answer_key, Mapping) and isinstance(answer_key.get("items"), list):
        key_items = list(answer_key["items"])

    for idx, item in enumerate(items):
        if not isinstance(item, Mapping):
            continue
        options_raw = item.get("options") or item.get("choices") or []
        if not isinstance(options_raw, list) or not options_raw:
            continue
        options = [str(o) for o in options_raw]
        correct: Any = item.get("correct")
        if correct is None and idx < len(key_items):
            entry = key_items[idx]
            correct = entry.get("correct") if isinstance(entry, Mapping) else entry
        yield str(item.get("prompt") or item.get("question") or item.get("stem") or ""), options, correct

    # Cloze blanks carry their own per-blank distractor options — same shape,
    # answer already resolved (no answer_key fallback needed).
    blanks = payload.get("blanks")
    if isinstance(blanks, list):
        for idx, blank in enumerate(blanks):
            if not isinstance(blank, Mapping):
                continue
            options_raw = blank.get("options") or []
            if not isinstance(options_raw, list) or not options_raw:
                continue
            options = [str(o) for o in options_raw]
            yield str(blank.get("id") or f"blank[{idx}]"), options, blank.get("answer")


def _resolve_correct_option(options: Sequence[str], correct: Any) -> str | None:
    if correct is None:
        return None
    if isinstance(correct, bool):
        return None
    if isinstance(correct, int):
        if 0 <= correct < len(options):
            return options[correct]
        return None
    correct_s = str(correct).strip()
    # Letter key: "а" / "a" / "б"
    if len(correct_s) == 1:
        letters_ua = "абвгдеєжзиіїклмнопрстуфхцчшщьюя"
        letters_en = "abcdefghijklmnopqrstuvwxyz"
        alphabet = letters_ua if correct_s.casefold() in letters_ua else letters_en
        try:
            idx = alphabet.index(correct_s.casefold())
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
    # Exact or prefix match against options
    for opt in options:
        if opt.strip() == correct_s or _normalize_option(opt) == _normalize_option(correct_s):
            return opt
        if opt.strip().casefold().startswith(correct_s.casefold()):
            return opt
    return correct_s


def check_invalid_distractors(ctx: _ScanContext) -> list[dict[str, Any]]:
    """Tier-1: distractors must be real VESUM forms, distinct, non-duplicate, non-synonym."""
    findings: list[dict[str, Any]] = []
    file_text = ctx.texts.get("activities.yaml") or ctx.texts.get("module.md") or ""
    # Same distractor set reused verbatim across items — a real generation defect
    # (soak-verified, #5254): the model gets stuck and copy-pastes one "filler"
    # pair everywhere, so the learner can answer by pattern-matching the filler
    # instead of reading the text. Tracked across the whole lesson, not just one
    # activity, because the real defect repeats across activity boundaries too.
    distractor_set_locations: dict[tuple[str, ...], list[tuple[int, int]]] = {}

    for act_idx, entry in enumerate(ctx.activities):
        activity = _activity_body(entry)
        for item_idx, (_prompt, options, correct) in enumerate(_iter_mc_items(activity)):
            if len(options) < 2:
                continue
            correct_opt = _resolve_correct_option(options, correct)
            correct_norm = _normalize_option(correct_opt or "")
            correct_tokens = _cyrillic_tokens(correct_norm)
            correct_lemma = correct_tokens[0] if len(correct_tokens) == 1 else correct_norm

            seen_norms: set[str] = set()
            item_distractor_norms: set[str] = set()
            for opt in options:
                norm = _normalize_option(opt)
                if not norm:
                    findings.append(
                        _finding(
                            issue_id="INVALID_DISTRACTOR",
                            rule_id="hramatka_empty_distractor",
                            dimension="distractor_quality",
                            severity="critical",
                            file="activities.yaml",
                            line=1,
                            excerpt=str(opt)[:80] or "(empty)",
                            message=f"Activity[{act_idx}] item[{item_idx}]: empty distractor option.",
                            text=file_text,
                        )
                    )
                    continue

                # Skip the correct answer itself.
                if correct_norm and norm.casefold() == correct_norm.casefold():
                    seen_norms.add(norm.casefold())
                    continue
                if correct_opt and opt.strip() == str(correct_opt).strip():
                    seen_norms.add(norm.casefold())
                    continue

                # Duplicate / near-duplicate
                if norm.casefold() in seen_norms:
                    findings.append(
                        _finding(
                            issue_id="DUPLICATE_DISTRACTOR",
                            rule_id="hramatka_duplicate_distractor",
                            dimension="distractor_quality",
                            severity="warning",
                            file="activities.yaml",
                            line=1,
                            excerpt=norm,
                            message=f"Activity[{act_idx}] item[{item_idx}]: duplicate distractor '{norm}'.",
                            text=file_text,
                        )
                    )
                    continue
                seen_norms.add(norm.casefold())
                item_distractor_norms.add(norm.casefold())

                tokens = _cyrillic_tokens(norm)
                # Single-token distractors: require VESUM form
                if len(tokens) == 1:
                    form = tokens[0]
                    if not _vesum_hits(form):
                        findings.append(
                            _finding(
                                issue_id="NON_VESUM_DISTRACTOR",
                                rule_id="hramatka_distractor_not_vesum",
                                dimension="distractor_quality",
                                severity="critical",
                                file="activities.yaml",
                                line=1,
                                excerpt=form,
                                message=(
                                    f"Activity[{act_idx}] item[{item_idx}]: distractor '{form}' "
                                    "is not a real Ukrainian form (VESUM)."
                                ),
                                text=file_text,
                            )
                        )
                    # Synonym collision with answer
                    if correct_lemma and _are_synonyms(correct_lemma, form):
                        findings.append(
                            _finding(
                                issue_id="SYNONYM_DISTRACTOR",
                                rule_id="hramatka_synonym_collision",
                                dimension="distractor_quality",
                                severity="critical",
                                file="activities.yaml",
                                line=1,
                                excerpt=form,
                                message=(
                                    f"Activity[{act_idx}] item[{item_idx}]: distractor '{form}' "
                                    f"is a known synonym of the answer '{correct_lemma}'."
                                ),
                                text=file_text,
                            )
                        )
                    # Optional morphological collision — only when activity type looks grammatical
                    act_type = str(activity.get("type") or "").casefold()
                    if (
                        "grammar" in act_type
                        or "morph" in act_type
                        or "case" in act_type
                    ) and correct_tokens and len(correct_tokens) == 1:
                        ans_forms = _vesum_hits(correct_tokens[0])
                        dis_forms = _vesum_hits(form)
                        if ans_forms and dis_forms:
                            ans_tags = {f.get("tags") for f in ans_forms}
                            dis_tags = {f.get("tags") for f in dis_forms}
                            if ans_tags & dis_tags and form.casefold() != correct_tokens[0].casefold():
                                findings.append(
                                    _finding(
                                        issue_id="MORPH_COLLISION_DISTRACTOR",
                                        rule_id="hramatka_morph_collision",
                                        dimension="distractor_quality",
                                        severity="info",
                                        file="activities.yaml",
                                        line=1,
                                        excerpt=form,
                                        message=(
                                            f"Activity[{act_idx}] item[{item_idx}]: distractor '{form}' "
                                            "shares morphological tags with the answer — review for grammar items."
                                        ),
                                        text=file_text,
                                    )
                                )
                elif not tokens:
                    # No Ukrainian content at all in distractor
                    findings.append(
                        _finding(
                            issue_id="NON_VESUM_DISTRACTOR",
                            rule_id="hramatka_distractor_not_vesum",
                            dimension="distractor_quality",
                            severity="critical",
                            file="activities.yaml",
                            line=1,
                            excerpt=norm[:80],
                            message=(
                                f"Activity[{act_idx}] item[{item_idx}]: distractor has no Ukrainian "
                                "word forms to verify."
                            ),
                            text=file_text,
                        )
                    )

            if len(item_distractor_norms) >= 2:
                key = tuple(sorted(item_distractor_norms))
                distractor_set_locations.setdefault(key, []).append((act_idx, item_idx))

    for distractor_set, locations in distractor_set_locations.items():
        if len(locations) < 3:
            continue
        first_act, first_item = locations[0]
        findings.append(
            _finding(
                issue_id="DEGENERATE_DISTRACTOR_REUSE",
                rule_id="hramatka_degenerate_distractor_reuse",
                dimension="distractor_quality",
                severity="critical",
                file="activities.yaml",
                line=1,
                excerpt=" / ".join(distractor_set)[:160],
                message=(
                    f"Distractor set {list(distractor_set)} is reused verbatim across "
                    f"{len(locations)} items (first: activity[{first_act}] item[{first_item}]) — "
                    "learner can answer by pattern-matching the filler, not by reading the text."
                ),
                text=file_text,
            )
        )
    return findings


def check_answer_key_placeholders(ctx: _ScanContext) -> list[dict[str, Any]]:
    """Tier-1: empty / TODO / XXX / ellipsis / whitespace-only answer keys."""
    findings: list[dict[str, Any]] = []
    file_text = ctx.texts.get("activities.yaml") or ctx.texts.get("module.md") or ""

    for act_idx, entry in enumerate(ctx.activities):
        activity = _activity_body(entry)
        act_type = str(activity.get("type") or entry.get("type") or "")
        # Glossary / free-response may legitimately lack rigid answer keys.
        if act_type in _FREE_RESPONSE_TYPES or act_type in {"reading", "text", "anchor"}:
            continue
        answer_key = _answer_key_for(entry, activity)
        if answer_key is None:
            findings.append(
                _finding(
                    issue_id="ANSWER_KEY_PLACEHOLDER",
                    rule_id="hramatka_missing_answer_key",
                    dimension="answer_key_integrity",
                    severity="critical",
                    file="activities.yaml",
                    line=1,
                    excerpt=f"activity[{act_idx}].answer_key=null",
                    message=f"Activity[{act_idx}] ({act_type}): answer_key is missing/null.",
                    text=file_text,
                )
            )
            continue
        if _is_placeholder(answer_key):
            excerpt = str(answer_key)[:80] if answer_key is not None else "(empty)"
            findings.append(
                _finding(
                    issue_id="ANSWER_KEY_PLACEHOLDER",
                    rule_id="hramatka_answer_key_placeholder",
                    dimension="answer_key_integrity",
                    severity="critical",
                    file="activities.yaml",
                    line=1,
                    excerpt=excerpt or "(empty)",
                    message=f"Activity[{act_idx}] ({act_type}): answer_key looks like a placeholder.",
                    text=file_text,
                )
            )
            continue
        # Nested empty items list
        if isinstance(answer_key, Mapping):
            for nested_key in ("items", "pairs", "answers", "blanks"):
                nested = answer_key.get(nested_key)
                if isinstance(nested, list) and len(nested) == 0:
                    findings.append(
                        _finding(
                            issue_id="ANSWER_KEY_PLACEHOLDER",
                            rule_id="hramatka_answer_key_empty_list",
                            dimension="answer_key_integrity",
                            severity="critical",
                            file="activities.yaml",
                            line=1,
                            excerpt=f"answer_key.{nested_key}=[]",
                            message=(
                                f"Activity[{act_idx}] ({act_type}): answer_key.{nested_key} is empty."
                            ),
                            text=file_text,
                        )
                    )
    return findings


def check_structural_integrity(ctx: _ScanContext) -> list[dict[str, Any]]:
    """Tier-2: schema-level activity integrity (cloze, match-up, MC, empty items)."""
    findings: list[dict[str, Any]] = []
    file_text = ctx.texts.get("activities.yaml") or ""

    for act_idx, entry in enumerate(ctx.activities):
        activity = _activity_body(entry)
        act_type = str(activity.get("type") or entry.get("type") or payload_type(activity))
        payload = _payload(activity)
        answer_key = _answer_key_for(entry, activity)

        items = payload.get("items")
        if items is not None and isinstance(items, list) and len(items) == 0:
            findings.append(
                _finding(
                    issue_id="EMPTY_PAYLOAD_ITEMS",
                    rule_id="hramatka_empty_payload_items",
                    dimension="activity_structure",
                    severity="critical",
                    file="activities.yaml",
                    line=1,
                    excerpt=f"activity[{act_idx}].payload.items=[]",
                    message=f"Activity[{act_idx}] ({act_type}): payload.items is empty.",
                    text=file_text,
                )
            )

        # Multiple choice: each item needs ≥2 options
        if act_type in {"multiple-choice", "mc", "multiple_choice"} or payload.get("type") in {
            "multiple-choice",
            "mc",
        }:
            raw_items = items if isinstance(items, list) else []
            for item_idx, item in enumerate(raw_items):
                if not isinstance(item, Mapping):
                    continue
                options = item.get("options") or item.get("choices") or []
                if not isinstance(options, list) or len(options) < 2:
                    findings.append(
                        _finding(
                            issue_id="MC_TOO_FEW_OPTIONS",
                            rule_id="hramatka_mc_min_options",
                            dimension="activity_structure",
                            severity="critical",
                            file="activities.yaml",
                            line=1,
                            excerpt=str(item.get("prompt") or item)[:80],
                            message=(
                                f"Activity[{act_idx}] item[{item_idx}]: multiple-choice needs ≥2 options."
                            ),
                            text=file_text,
                        )
                    )

        # Match-up cardinality
        if act_type in {"match-up", "match_up", "matching"} or payload.get("type") in {
            "match-up",
            "match_up",
        }:
            pairs = payload.get("pairs") or []
            if isinstance(pairs, list):
                lefts = [p for p in pairs if isinstance(p, Mapping) and p.get("left") not in (None, "")]
                rights = [p for p in pairs if isinstance(p, Mapping) and p.get("right") not in (None, "")]
                if len(lefts) != len(rights):
                    findings.append(
                        _finding(
                            issue_id="MATCHUP_CARDINALITY",
                            rule_id="hramatka_matchup_cardinality",
                            dimension="activity_structure",
                            severity="critical",
                            file="activities.yaml",
                            line=1,
                            excerpt=f"left={len(lefts)} right={len(rights)}",
                            message=(
                                f"Activity[{act_idx}]: match-up left/right cardinality mismatch "
                                f"({len(lefts)} vs {len(rights)})."
                            ),
                            text=file_text,
                        )
                    )
                if isinstance(answer_key, Mapping):
                    key_pairs = answer_key.get("pairs")
                    if isinstance(key_pairs, list) and pairs and len(key_pairs) != len(pairs):
                        findings.append(
                            _finding(
                                issue_id="ANSWER_KEY_SHAPE",
                                rule_id="hramatka_matchup_key_shape",
                                dimension="activity_structure",
                                severity="critical",
                                file="activities.yaml",
                                line=1,
                                excerpt=f"pairs={len(pairs)} key_pairs={len(key_pairs)}",
                                message=(
                                    f"Activity[{act_idx}]: answer_key.pairs length does not match payload pairs."
                                ),
                                text=file_text,
                            )
                        )

        # Cloze blank count vs answers
        if act_type in {"cloze", "fill-blank", "fill_blank", "gap-fill"} or payload.get("type") in {
            "cloze",
            "fill-blank",
            "gap-fill",
        }:
            stems: list[str] = []
            if isinstance(payload.get("text"), str):
                stems.append(str(payload["text"]))
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        stems.append(item)
                    elif isinstance(item, Mapping):
                        stems.append(str(item.get("text") or item.get("stem") or item.get("prompt") or ""))
            blank_count = sum(len(_CLOZE_BLANK_RE.findall(stem)) for stem in stems)
            # Prefer explicit payload.blanks cardinality when present.
            payload_blanks = payload.get("blanks")
            if isinstance(payload_blanks, list) and payload_blanks:
                blank_count = max(blank_count, len(payload_blanks))
            answer_count = 0
            if isinstance(answer_key, Mapping):
                for key in ("answers", "blanks", "items"):
                    nested = answer_key.get(key)
                    if isinstance(nested, list):
                        answer_count = len(nested)
                        break
                if answer_count == 0 and answer_key.get("answer") is not None:
                    answer_count = 1
            elif isinstance(answer_key, list):
                answer_count = len(answer_key)
            elif isinstance(answer_key, str) and answer_key.strip():
                # Free-text keys often use " · " / numbered lists.
                parts = [p for p in re.split(r"\s*[·|;]\s*|\n+", answer_key) if p.strip()]
                answer_count = len(parts) if parts else 1
            if blank_count and answer_count and blank_count != answer_count:
                findings.append(
                    _finding(
                        issue_id="CLOZE_BLANK_MISMATCH",
                        rule_id="hramatka_cloze_blank_count",
                        dimension="activity_structure",
                        severity="critical",
                        file="activities.yaml",
                        line=1,
                        excerpt=f"blanks={blank_count} answers={answer_count}",
                        message=(
                            f"Activity[{act_idx}]: cloze blank count ({blank_count}) "
                            f"≠ answer count ({answer_count})."
                        ),
                        text=file_text,
                    )
                )
    return findings


def payload_type(activity: Mapping[str, Any]) -> str:
    payload = _payload(activity)
    return str(payload.get("type") or "")


def check_empty_learner_surface(ctx: _ScanContext) -> list[dict[str, Any]]:
    """Tier-2: blank title / instruction / statement (not only answer_key)."""
    findings: list[dict[str, Any]] = []
    file_text = ctx.texts.get("module.md") or ""
    title_line = next((ln for ln in file_text.splitlines() if ln.startswith("#")), "#")
    title = title_line.lstrip("#").strip()
    if not title or title.casefold() in {"hramatka lesson", "untitled"}:
        findings.append(
            _finding(
                issue_id="EMPTY_LEARNER_SURFACE",
                rule_id="hramatka_empty_title",
                dimension="learner_surface",
                severity="critical",
                file="module.md",
                line=1,
                excerpt=title_line[:80] or "(missing title)",
                message="Lesson title is blank or placeholder.",
                text=file_text,
            )
        )

    act_text = ctx.texts.get("activities.yaml") or ""
    for act_idx, entry in enumerate(ctx.activities):
        activity = _activity_body(entry)
        act_title = str(activity.get("title") or "").strip()
        if not act_title:
            findings.append(
                _finding(
                    issue_id="EMPTY_LEARNER_SURFACE",
                    rule_id="hramatka_empty_activity_title",
                    dimension="learner_surface",
                    severity="warning",
                    file="activities.yaml",
                    line=1,
                    excerpt=f"activity[{act_idx}].title",
                    message=f"Activity[{act_idx}]: title is blank.",
                    text=act_text,
                )
            )
        payload = _payload(activity)
        act_type = str(activity.get("type") or entry.get("type") or "")
        instruction = str(payload.get("instruction") or activity.get("instruction") or "").strip()
        if payload and not instruction and act_type not in _FREE_RESPONSE_TYPES:
            findings.append(
                _finding(
                    issue_id="EMPTY_LEARNER_SURFACE",
                    rule_id="hramatka_empty_instruction",
                    dimension="learner_surface",
                    severity="warning",
                    file="activities.yaml",
                    line=1,
                    excerpt=f"activity[{act_idx}].instruction",
                    message=f"Activity[{act_idx}]: instruction is blank.",
                    text=act_text,
                )
            )
        items = payload.get("items")
        if isinstance(items, list):
            for item_idx, item in enumerate(items):
                if isinstance(item, Mapping):
                    statement = item.get("statement")
                    if "statement" in item and not str(statement or "").strip():
                        findings.append(
                            _finding(
                                issue_id="EMPTY_LEARNER_SURFACE",
                                rule_id="hramatka_empty_statement",
                                dimension="learner_surface",
                                severity="warning",
                                file="activities.yaml",
                                line=1,
                                excerpt=f"activity[{act_idx}].items[{item_idx}].statement",
                                message=f"Activity[{act_idx}] item[{item_idx}]: statement is blank.",
                                text=act_text,
                            )
                        )
    return findings


def check_task_language_cefr(ctx: _ScanContext) -> list[dict[str, Any]]:
    """Tier-2: CEFR of INSTRUCTIONS/ITEMS only; never grade the teacher anchor.

    Lenient by design: only flag words clearly ≥2 CEFR bands above the lesson,
    only in task language (instruction / item prompts), never proper nouns.
    """
    findings: list[dict[str, Any]] = []
    lesson_level = _normalize_level(ctx.level)
    act_text = ctx.texts.get("activities.yaml") or ""

    task_strings: list[tuple[str, str]] = []
    for act_idx, entry in enumerate(ctx.activities):
        activity = _activity_body(entry)
        payload = _payload(activity)
        for key in ("instruction",):
            val = payload.get(key) or activity.get(key)
            if isinstance(val, str) and val.strip():
                task_strings.append((f"activity[{act_idx}].{key}", val))
        items = payload.get("items")
        if isinstance(items, list):
            for item_idx, item in enumerate(items):
                if isinstance(item, str):
                    task_strings.append((f"activity[{act_idx}].items[{item_idx}]", item))
                elif isinstance(item, Mapping):
                    for field_name in ("prompt", "question", "stem", "statement", "text"):
                        val = item.get(field_name)
                        if isinstance(val, str) and val.strip():
                            task_strings.append(
                                (f"activity[{act_idx}].items[{item_idx}].{field_name}", val)
                            )

    seen: set[str] = set()
    for path, text in task_strings:
        for token in _cyrillic_tokens(text):
            # Proper nouns / names are not CEFR-vocab items.
            if _is_probable_proper_noun(token):
                continue
            # Skip very short tokens (particles, answer-key letters).
            if len(token) < 3:
                continue
            word_level = _cefr_level_for(token)
            if not word_level:
                continue
            if not _cefr_exceeds(lesson_level, word_level):
                continue
            key = token.casefold()
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                _finding(
                    issue_id="TASK_CEFR_OVERLEVEL",
                    rule_id="hramatka_task_cefr",
                    dimension="task_cefr",
                    severity="warning",
                    file="activities.yaml",
                    line=1,
                    excerpt=token,
                    message=(
                        f"{path}: task word '{token}' is CEFR {word_level.upper()} "
                        f"but lesson level is {lesson_level.upper()}."
                    ),
                    text=act_text,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Aggregate / scan
# ---------------------------------------------------------------------------


def _dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for finding in findings:
        key = (
            finding.get("issue_id"),
            finding.get("file"),
            finding.get("line"),
            finding.get("excerpt"),
            finding.get("rule_id"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(finding)
    return out


def _dimension_scores(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    dimensions: dict[str, dict[str, Any]] = {}
    for dim in DIMENSION_ORDER:
        dim_findings = [f for f in findings if f.get("dimension") == dim]
        penalty = sum(SEVERITY_WEIGHTS.get(str(f.get("severity")), 0.0) for f in dim_findings)
        score = max(0.0, round(10.0 - penalty, 1))
        has_critical = any(f.get("severity") == "critical" for f in dim_findings)
        has_warning = any(f.get("severity") == "warning" for f in dim_findings)
        dimensions[dim] = {
            "score": score,
            "verdict": "FAIL" if has_critical else "WARN" if has_warning else "PASS",
            "findings": dim_findings,
        }
    return dimensions


def _aggregate(dimensions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    scored = {
        dim: float(entry.get("score", 0.0))
        for dim, entry in dimensions.items()
        if isinstance(entry.get("score"), int | float)
    }
    min_dim = min(scored, key=scored.__getitem__) if scored else None
    has_fail = any(entry.get("verdict") == "FAIL" for entry in dimensions.values())
    has_warn = any(entry.get("verdict") == "WARN" for entry in dimensions.values())
    return {
        "verdict": "FAIL" if has_fail else "WARN" if has_warn else "PASS",
        "terminal_verdict": "FAIL" if has_fail else "PASS",
        "min_score": scored[min_dim] if min_dim else None,
        "min_dim": min_dim,
        "failing_dims": [dim for dim, entry in dimensions.items() if entry.get("verdict") == "FAIL"],
        "warning_dims": [dim for dim, entry in dimensions.items() if entry.get("verdict") == "WARN"],
    }


def scan_hramatka_module(
    module_dir: Path,
    *,
    level: str | None = None,
    slug: str | None = None,
    fixture_id: str | None = None,
    learner_strings: Sequence[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Scan an adapted (or hand-built) module directory with hramatka rules."""
    module_dir = module_dir.resolve()
    texts = _read_module_texts(module_dir)
    activities = _load_activities_from_module(module_dir)

    meta_level = level
    meta_slug = slug or module_dir.name
    meta_path = module_dir / "hramatka_adapter_meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta_level = meta_level or meta.get("level")
            meta_slug = slug or meta.get("slug") or meta_slug
        except (OSError, json.JSONDecodeError):
            pass
    clean_level = _normalize_level(meta_level or "b1")

    strings = list(learner_strings or [])
    if not strings:
        strings = _collect_strings({"activities": activities})
        if texts.get("module.md"):
            strings.append(("module.md", texts["module.md"]))

    ctx = _ScanContext(
        level=clean_level,
        texts=texts,
        activities=activities,
        learner_strings=strings,
    )

    unavailable: dict[str, str] = {}
    token = _ACTIVE_UNAVAILABLE.set(unavailable)
    try:
        findings = _dedupe_findings(
            [
                *check_russianism_calque(ctx),
                *check_invalid_distractors(ctx),
                *check_answer_key_placeholders(ctx),
                *check_structural_integrity(ctx),
                *check_empty_learner_surface(ctx),
                *check_task_language_cefr(ctx),
                *check_invented_forms(ctx),
            ]
        )
    finally:
        _ACTIVE_UNAVAILABLE.reset(token)

    dimensions = _dimension_scores(findings)
    aggregate = _aggregate(dimensions)
    config_hash = checker_config_hash()
    detector_status = {
        name: {"status": "detector_unavailable", "reason": reason}
        for name, reason in sorted(unavailable.items())
    }

    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "rule_set": RULE_SET_ID,
        "module_id": f"{clean_level}/{meta_slug}",
        "level": clean_level,
        "slug": meta_slug,
        "checker_config": {
            "version": CHECKER_VERSION,
            "config_hash": config_hash,
            "rule_set": RULE_SET_ID,
        },
        "content_sha": content_sha_for_module(module_dir),
        "verdict": aggregate["verdict"],
        "terminal_verdict": aggregate["terminal_verdict"],
        "aggregate": aggregate,
        "dimensions": dimensions,
        "detector_status": detector_status,
        "checker_runs": [
            {
                "source": "hramatka_deterministic",
                "checker": CHECKER_VERSION,
                "config_hash": config_hash,
                "provider": None,
                "model": None,
            }
        ],
        "llm_review": {
            "used": False,
            "required": aggregate["verdict"] != "PASS",
            "provider": None,
            "model": None,
            "reason": (
                "Residual LLM judge is required for semantic 'accidentally-also-correct' "
                "distractors and pedagogical fit — not covered deterministically."
            ),
        },
        "provenance": {
            "created_at": _now_z(),
            "run_id": f"hramatka-qg-{uuid4().hex}",
            "source": "hramatka_qg_rules",
            "fixture_id": fixture_id,
        },
    }


def scan_hramatka_lesson(
    lesson: Mapping[str, Any],
    *,
    slug: str | None = None,
    fixture_id: str | None = None,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    """Adapt lesson_json then scan with hramatka rules."""
    adapted = adapt_lesson_json(lesson, slug=slug)
    if work_dir is None:
        with tempfile.TemporaryDirectory(prefix="hramatka-qg-") as raw:
            dest = Path(raw) / adapted.slug
            write_adapted_module_dir(adapted, dest)
            return scan_hramatka_module(
                dest,
                level=adapted.level,
                slug=adapted.slug,
                fixture_id=fixture_id,
                learner_strings=adapted.learner_strings,
            )
    dest = work_dir / adapted.slug
    write_adapted_module_dir(adapted, dest)
    return scan_hramatka_module(
        dest,
        level=adapted.level,
        slug=adapted.slug,
        fixture_id=fixture_id,
        learner_strings=adapted.learner_strings,
    )


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _expected_findings_pass(
    evidence: Mapping[str, Any],
    expected: list[Mapping[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    actual: list[Mapping[str, Any]] = []
    dimensions = evidence.get("dimensions")
    if isinstance(dimensions, Mapping):
        for entry in dimensions.values():
            if isinstance(entry, Mapping) and isinstance(entry.get("findings"), list):
                actual.extend(item for item in entry["findings"] if isinstance(item, Mapping))

    missing: list[dict[str, Any]] = []
    for wanted in expected:
        issue_id = str(wanted.get("issue_id") or "")
        excerpt = _normalize_text(wanted.get("excerpt"))
        dimension = str(wanted.get("dimension") or "")
        severity = str(wanted.get("severity") or "")

        matched = False
        for item in actual:
            if issue_id and item.get("issue_id") != issue_id:
                continue
            if dimension and item.get("dimension") != dimension:
                continue
            if severity and item.get("severity") != severity:
                continue
            actual_excerpt = _normalize_text(item.get("excerpt"))
            if excerpt and excerpt not in actual_excerpt and actual_excerpt not in excerpt:
                continue
            matched = True
            break
        if not matched:
            missing.append(dict(wanted))
    return not missing, missing


def _write_fixture_module(root: Path, fixture: Mapping[str, Any]) -> Path:
    """Write a fixture as either lesson_json adaptation or raw CONTENT_FILES."""
    fixture_id = str(fixture.get("id") or "fixture")
    level = _normalize_level(fixture.get("level") or "b1")
    slug = str(fixture.get("slug") or fixture_id)
    module_dir = root / level / slug
    module_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(fixture.get("lesson_json"), Mapping):
        adapt_lesson_json_to_module_dir(fixture["lesson_json"], module_dir, slug=slug)
        return module_dir

    module = fixture.get("module")
    if not isinstance(module, Mapping):
        raise ValueError(f"fixture {fixture_id} needs lesson_json or module mapping")
    for name in CONTENT_FILES:
        value = module.get(name)
        if value is None:
            value = "[]\n" if name.endswith((".yaml", ".yml")) else ""
        (module_dir / name).write_text(str(value).rstrip() + "\n", encoding="utf-8")
    return module_dir


def evaluate_fixture(fixture: Mapping[str, Any], *, temp_root: Path) -> dict[str, Any]:
    """Evaluate one labeled hramatka fixture against gold expectations."""
    fixture_id = str(fixture.get("id") or "")
    level = _normalize_level(fixture.get("level") or "b1")
    slug = str(fixture.get("slug") or fixture_id)

    if fixture.get("source_lesson_json"):
        raw = fixture["source_lesson_json"]
        path = Path(raw) if Path(str(raw)).is_absolute() else PROJECT_ROOT / str(raw)
        lesson = json.loads(path.read_text(encoding="utf-8"))
        evidence = scan_hramatka_lesson(lesson, slug=slug, fixture_id=fixture_id, work_dir=temp_root)
    elif isinstance(fixture.get("lesson_json"), Mapping):
        evidence = scan_hramatka_lesson(
            fixture["lesson_json"],
            slug=slug,
            fixture_id=fixture_id,
            work_dir=temp_root,
        )
    else:
        module_dir = _write_fixture_module(temp_root, fixture)
        evidence = scan_hramatka_module(
            module_dir,
            level=level,
            slug=slug,
            fixture_id=fixture_id,
        )

    expected_verdict = str(fixture.get("expected_verdict") or "").upper()
    verdict_passed = not expected_verdict or evidence["verdict"] == expected_verdict
    expected_findings = fixture.get("expected_findings")
    if not isinstance(expected_findings, list):
        expected_findings = []
    findings_passed, missing_findings = _expected_findings_pass(evidence, expected_findings)

    # Load-bearing: a green on a lesson carrying a planted fault is a TEST FAILURE.
    # (Covered by expected_verdict FAIL + expected_findings matching.)
    return {
        "id": fixture_id,
        "level": level,
        "slug": slug,
        "expected_verdict": expected_verdict,
        "actual_verdict": evidence["verdict"],
        "passed": verdict_passed and findings_passed,
        "missing_findings": missing_findings,
        "evidence": evidence,
    }


def run_fixtures(path: Path) -> dict[str, Any]:
    """Run a hramatka fixture YAML file."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("fixture file must be a mapping")
    if data.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        raise ValueError(f"unsupported fixture schema: {data.get('schema_version')}")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("fixture file must contain a fixtures list")

    with tempfile.TemporaryDirectory(prefix="hramatka-qg-fixtures-") as raw_tmp:
        tmp_root = Path(raw_tmp)
        results = [
            evaluate_fixture(fixture, temp_root=tmp_root)
            for fixture in fixtures
            if isinstance(fixture, Mapping)
        ]
    passed = sum(1 for result in results if result["passed"])
    return {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "rule_set": RULE_SET_ID,
        "fixture_file": str(path),
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
        "results": results,
    }


def all_findings(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Flatten dimension findings from evidence."""
    out: list[dict[str, Any]] = []
    dimensions = evidence.get("dimensions")
    if isinstance(dimensions, Mapping):
        for entry in dimensions.values():
            if isinstance(entry, Mapping) and isinstance(entry.get("findings"), list):
                out.extend(f for f in entry["findings"] if isinstance(f, dict))
    return out
