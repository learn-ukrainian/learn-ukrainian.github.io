"""Deterministic screen + fix logic for the v5 pipeline.

Extracts deterministic fixes (euphony, H1 demotion, H2 correction, IPA removal,
YAML schema fixes) and the deterministic screen pass (metrics, audit, Russicism
scan, LLM filler scan, VESUM verify, rule engine, morphological validator,
content quality checks).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline_lib import ModuleContext

from pipeline.parsing import (
    DScreenResult,
    _compute_metrics_direct,
    _extract_h2_sections,
    _scan_llm_filler,
)

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency with pipeline_lib
def _log(msg: str) -> None:
    from pipeline_lib import log
    log(msg)


# ---------------------------------------------------------------------------
# Mtime cache to skip re-running fixes on unchanged files
# ---------------------------------------------------------------------------
_deterministic_fix_mtimes: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Individual fix steps (broken out for testability + readability)
# ---------------------------------------------------------------------------

def _fix_euphony(text: str, content_path: Path) -> tuple[str, int]:
    """Auto-fix euphony violations (в/у, з/із/зі). Returns (text, count)."""
    from audit.checks.euphony import auto_fix_euphony
    text, n = auto_fix_euphony(text, str(content_path))
    return text, n


def _fix_extra_h1(text: str) -> tuple[str, int]:
    """Demote extra H1 headings to H2. Summary/Підсумок stay H1."""
    _H1_ALLOWED = {'summary', 'підсумок'}
    lines = text.split('\n')
    h1_count = 0
    changed = False
    in_code_block = False
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if line.startswith('# ') and not line.startswith('## '):
            h1_count += 1
            if h1_count > 1:
                heading_text = line.lstrip('# ').strip().lower()
                if heading_text not in _H1_ALLOWED:
                    lines[i] = '#' + line
                    changed = True
    if changed:
        return '\n'.join(lines), 1
    return text, 0


def _fix_h2_titles(text: str, content_outline: list[dict]) -> tuple[str, int]:
    """Auto-correct H2 section titles to match content_outline via fuzzy matching."""
    from difflib import SequenceMatcher

    from audit.checks.outline_compliance import normalize_section_name

    expected_titles = {
        (s.get("section") or s.get("title", "")).strip(): (s.get("section") or s.get("title", "")).strip()
        for s in content_outline if s.get("section") or s.get("title")
    }
    if not expected_titles:
        return text, 0

    lines = text.split('\n')
    changed = False
    in_code_block = False
    for i, ln in enumerate(lines):
        if ln.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if ln.startswith('## ') and not ln.startswith('### '):
            md_title = ln[3:].strip()
            md_norm = normalize_section_name(md_title)
            exact_match = any(
                normalize_section_name(et) == md_norm for et in expected_titles
            )
            if not exact_match:
                best_score = 0.0
                best_expected = ""
                for et in expected_titles:
                    score = SequenceMatcher(
                        None, md_norm, normalize_section_name(et)
                    ).ratio()
                    if score > best_score:
                        best_score = score
                        best_expected = et
                if best_score >= 0.6 and best_expected:
                    lines[i] = f"## {best_expected}"
                    changed = True
                    _log(f"    Auto-fix: H2 title '{md_title}' → '{best_expected}' (similarity {best_score:.0%})")

    if changed:
        return '\n'.join(lines), 1
    return text, 0


def _fix_ipa_brackets(text: str) -> tuple[str, int]:
    """Strip IPA / phonetic brackets from text."""
    cleaned = re.sub(r' \[[^\]\n]{2,40}\] \(', ' (', text)
    if cleaned != text:
        n_ipa = text.count('[') - cleaned.count('[')
        return cleaned, n_ipa
    return text, 0


def _fix_yaml_activities(act_path: Path) -> int:
    """Run YAML schema fixes on activity file. Returns fix count."""
    from audit.checks.yaml_schema_validation import fix_yaml_file
    n, msgs = fix_yaml_file(act_path, dry_run=False)
    if n > 0:
        _log(f"    Auto-fix: {n} YAML schema fix(es) in {act_path.name}")
        for msg in msgs[:3]:
            _log(f"      {msg[:120]}")
    return n


def _fix_yaml_vocab(vocab_path: Path) -> int:
    """Run YAML text-level fixes on vocabulary file. Returns fix count."""
    from audit.checks.yaml_schema_validation import fix_raw_yaml_text
    raw = vocab_path.read_text("utf-8")
    fixed, fix_msgs = fix_raw_yaml_text(raw)
    if fix_msgs:
        vocab_path.write_text(fixed, "utf-8")
        _log(f"    Auto-fix: {len(fix_msgs)} vocab YAML text fix(es) in {vocab_path.name}")
        for msg in fix_msgs[:3]:
            _log(f"      {msg[:120]}")
    return len(fix_msgs)


def _fix_forbidden_activities(act_path: Path, content_path: Path) -> int:
    """Remove forbidden activities based on level/focus. Returns removal count."""
    import yaml as yaml_lib
    from audit.checks.yaml_schema_validation import remove_forbidden_activities
    from audit.core import detect_focus, detect_level, load_yaml_meta

    meta_data = load_yaml_meta(str(content_path)) if content_path else {}
    if not (content_path and content_path.exists()):
        return 0

    fm_str = yaml_lib.dump(meta_data, sort_keys=False, allow_unicode=True) if meta_data else ""
    level_code, module_num, _ = detect_level(str(content_path), fm_str)
    module_focus = detect_focus(fm_str, level_code, module_num,
                                meta_data.get("title", "") if meta_data else "", str(content_path))
    n_removed, _ = remove_forbidden_activities(act_path, level_code, module_focus, dry_run=False)
    if n_removed > 0:
        _log(f"    Auto-fix: removed {n_removed} forbidden activity(ies)")
    return n_removed


# ---------------------------------------------------------------------------
# Main orchestrator: _run_deterministic_fixes
# ---------------------------------------------------------------------------

def _run_deterministic_fixes(ctx: ModuleContext) -> int:
    """Run all zero-cost deterministic fixes on a module's files."""
    total = 0
    content_path = ctx.paths.get("md")

    target_files = [
        content_path,
        ctx.paths.get("vocabulary"),
        ctx.paths.get("activities"),
    ]
    current_max_mtime = max(
        (p.stat().st_mtime for p in target_files if p and p.exists()),
        default=0.0,
    )
    last_mtime = _deterministic_fix_mtimes.get(ctx.slug, 0.0)
    if current_max_mtime > 0 and current_max_mtime <= last_mtime:
        return 0

    # 1. Content text transforms — read once, apply all, write once
    if content_path and content_path.exists():
        try:
            text = content_path.read_text("utf-8")
            dirty = False

            # 1a. Euphony auto-fix
            try:
                text, n = _fix_euphony(text, content_path)
                if n > 0:
                    dirty = True
                    total += n
                    _log(f"    Auto-fix: {n} euphony violation(s)")
            except Exception as e:
                logger.warning("Auto-fix: euphony failed: %s", e)

            # 1b. Demote extra H1 headings to H2
            try:
                text, n = _fix_extra_h1(text)
                if n > 0:
                    dirty = True
                    total += n
                    _log("    Auto-fix: demoted extra H1 heading(s) to H2 (preserved Summary/Підсумок)")
            except Exception as e:
                logger.warning("Auto-fix: H1 demotion failed: %s", e)

            # 1c. Auto-correct H2 section titles to match content_outline
            try:
                if ctx.content_outline:
                    text, n = _fix_h2_titles(text, ctx.content_outline)
                    if n > 0:
                        dirty = True
                        total += n
            except Exception as e:
                logger.warning("Auto-fix: H2 title correction failed: %s", e)

            # 1d. Strip IPA / phonetic brackets
            try:
                text, n = _fix_ipa_brackets(text)
                if n > 0:
                    dirty = True
                    total += n
                    _log(f"    Auto-fix: stripped {n} IPA/phonetic bracket(s)")
            except Exception as e:
                logger.warning("Auto-fix: IPA strip failed: %s", e)

            if dirty:
                content_path.write_text(text, "utf-8")
        except Exception as e:
            logger.warning("Auto-fix: content read failed: %s", e)

    # 2. YAML schema fixes (activities)
    act_path = ctx.paths.get("activities")
    if act_path and act_path.exists():
        try:
            total += _fix_yaml_activities(act_path)
        except Exception as e:
            logger.warning("Auto-fix: YAML fix failed", exc_info=True)
            _log(f"    Auto-fix: YAML fix failed: {e}")

    # 3. YAML text-level fixes (vocab)
    vocab_path = ctx.paths.get("vocabulary")
    if vocab_path and vocab_path.exists():
        try:
            total += _fix_yaml_vocab(vocab_path)
        except Exception as e:
            logger.warning("Auto-fix: vocab YAML fix failed", exc_info=True)
            _log(f"    Auto-fix: vocab YAML fix failed: {e}")

    # 4. Forbidden activity removal
    if act_path and act_path.exists():
        try:
            total += _fix_forbidden_activities(act_path, content_path)
        except Exception as e:
            logger.warning("Auto-fix: forbidden activity check failed", exc_info=True)
            _log(f"    Auto-fix: forbidden activity check failed: {e}")

    new_max_mtime = max(
        (p.stat().st_mtime for p in target_files if p and p.exists()),
        default=0.0,
    )
    _deterministic_fix_mtimes[ctx.slug] = new_max_mtime

    return total


# ---------------------------------------------------------------------------
# Deterministic screen checks
# ---------------------------------------------------------------------------

def _run_russicism_scan(content_text: str, content_path: str) -> list[dict]:
    """Scan content for Russicisms. Returns list of issue dicts."""
    from audit.checks.russicism_detection import check_russicisms
    russicism_issues = check_russicisms(content_text, content_path)
    return [
        {
            "type": "RUSSIANISM",
            "severity": r.get("severity", "HIGH").upper(),
            "text": r.get("issue", ""),
            "fix": r.get("fix", ""),
        }
        for r in russicism_issues
    ]


def _run_ipa_scan(content_text: str) -> list[dict]:
    """Scan for banned IPA/phonetic brackets. Returns list of issue dicts."""
    _IPA_PATTERNS = [
        (re.compile(r'\[([a-z]+-)+[a-z]+\]'), "syllable breakdown"),
        (re.compile(r'\[[ɑɛɪɔʊəʃʒθðŋɾˈˌː\w\s]+\]'), "IPA transcription"),
    ]
    _IPA_WHITELIST = {"[Ø]"}
    issues = []
    for pattern, desc in _IPA_PATTERNS:
        matches = [m for m in pattern.finditer(content_text)
                   if m.group() not in _IPA_WHITELIST]
        for m in matches[:5]:
            line_num = content_text[:m.start()].count('\n') + 1
            issues.append({
                "type": "IPA_BANNED",
                "severity": "HIGH",
                "location": f"~line {line_num}",
                "text": f"Banned {desc}: {m.group()[:60]}",
                "fix": "Remove phonetic brackets. Use only stress marks (´) for pronunciation.",
            })
    return issues


def _run_vesum_verify(content_path: Path) -> tuple[dict, list[dict], str]:
    """Run VESUM word verification. Returns (stats, not_found_list, audit_suffix)."""
    from rag_batch_verify import verify_module as vesum_verify_module
    vesum_results, vesum_stats = vesum_verify_module(
        content_path, use_rag=False, skip_activities=False,
    )
    not_found = [r for r in vesum_results if r["status"] in ("❌", "⚠️")]
    n_not_found = vesum_stats.get("not_found", 0)
    n_partial = vesum_stats.get("rag_hits", 0)
    total_words = vesum_stats.get("total", 0)
    vesum_hits = vesum_stats.get("vesum_hits", 0)

    if n_not_found > 0 or n_partial > 0:
        _log(f"  D.0: VESUM verify: {total_words} words, "
             f"{vesum_hits} VESUM ✓, "
             f"{n_partial} RAG-only ⚠️, {n_not_found} not found ❌")
    else:
        _log(f"  D.0: VESUM verify: {total_words} words, "
             f"100% VESUM coverage ✅")

    pct = (vesum_hits / total_words * 100) if total_words else 100
    audit_suffix = f"\nVESUM: {vesum_hits}/{total_words} ({pct:.0f}%) verified"
    if n_not_found > 0:
        not_found_words = [r["original"] for r in not_found if r["status"] == "❌"][:10]
        audit_suffix += f"\n⚠️ VESUM not found ({n_not_found}): " + ", ".join(not_found_words)

    return vesum_stats, not_found, audit_suffix


def _run_rule_engine(content_text: str, ctx: ModuleContext) -> list[dict]:
    """Run rule engine checks. Returns list of issue dicts."""
    from audit.checks.rule_engine import run_rule_engine
    level_code = ctx.track.split("-")[0].upper()
    return run_rule_engine(content_text, level_code, ctx.module_num, ctx.track,
                           plan=getattr(ctx, "plan", None))


def _run_morphological_validator(content_text: str, ctx: ModuleContext) -> list[dict]:
    """Run VESUM morphological validator. Returns list of issue dicts."""
    from audit.checks.morphological_validator import validate_morphology
    level_code = ctx.track.split("-")[0].upper() if "-" in ctx.track else ctx.track.upper()
    return validate_morphology(content_text, level_code, ctx.module_num, ctx.track,
                               plan=getattr(ctx, "plan", None))


def _run_content_quality_checks(content_text: str, ctx: ModuleContext,
                                 vesum_not_found: list[dict]) -> list[dict]:
    """Run content quality pipeline checks. Returns list of issue dicts."""
    from audit.checks.content_quality_pipeline import run_content_quality_checks
    level_code = ctx.track.split("-")[0].upper() if "-" in ctx.track else ctx.track.upper()
    return run_content_quality_checks(
        content=content_text,
        level_code=level_code,
        module_num=ctx.module_num,
        plan=getattr(ctx, "plan", None),
        activities_path=ctx.paths.get("activities"),
        vesum_not_found=vesum_not_found,
    )


# ---------------------------------------------------------------------------
# Main orchestrator: _deterministic_screen
# ---------------------------------------------------------------------------

def _deterministic_screen(ctx: ModuleContext, skip_review: bool = False,
                          skip_activities: bool = False) -> DScreenResult:
    """Run all deterministic checks before LLM review.

    Args:
        skip_review: Skip review-related audit gates.
        skip_activities: Skip activity/vocab audit gates (for prose-only validation).
    """
    from pipeline_lib import run_verify, run_verify_prose_only

    result = DScreenResult(metrics={})

    # 1. Deterministic fixes (zero-cost)
    n_fixes = _run_deterministic_fixes(ctx)
    if n_fixes > 0:
        _log(f"  D.0: {n_fixes} deterministic fix(es) applied")

    # 2. Compute metrics (no audit subprocess)
    result.metrics = _compute_metrics_direct(ctx)

    # 3. H2 sections
    content_path = ctx.paths.get("md")
    if content_path and content_path.exists():
        result.h2_sections = _extract_h2_sections(content_path)
    else:
        result.h2_sections = "(content file not found)"

    # 4. Single audit run
    if content_path and content_path.exists():
        if skip_activities:
            result.audit_passed, result.audit_output = run_verify_prose_only(
                content_path)
        else:
            result.audit_passed, result.audit_output = run_verify(
                content_path, skip_review=skip_review)
        result.metrics["COMPUTED_AUDIT_STATUS"] = "PASS" if result.audit_passed else "FAIL"
    else:
        result.audit_passed = False
        result.audit_output = "NO_CONTENT"
        result.metrics["COMPUTED_AUDIT_STATUS"] = "NO_CONTENT"

    # Read content text once for subsequent checks
    content_text: str | None = None
    if content_path and content_path.exists():
        try:
            content_text = content_path.read_text("utf-8")
        except Exception as e:
            logger.warning("D.0: Failed to read content file: %s", e)

    # 5. Russicism scan
    if content_text is not None:
        try:
            result.deterministic_issues.extend(
                _run_russicism_scan(content_text, str(content_path)))
        except Exception as e:
            logger.warning("D.0: Russicism scan failed: %s", e)

    # 6. LLM filler scan
    if content_text is not None:
        try:
            result.deterministic_issues.extend(_scan_llm_filler(content_text))
        except Exception as e:
            logger.warning("D.0: LLM filler scan failed: %s", e)

    # 7. IPA / phonetic bracket scan
    if content_text is not None:
        result.deterministic_issues.extend(_run_ipa_scan(content_text))

    # 8. Word verification (VESUM only)
    if content_path and content_path.exists():
        try:
            stats, not_found, audit_suffix = _run_vesum_verify(content_path)
            result.vesum_stats = stats
            result.vesum_not_found = not_found
            result.audit_output += audit_suffix
        except Exception as e:
            logger.warning("D.0: VESUM word verification failed: %s", e)

    # 7.5 Rule engine
    if content_text is not None:
        try:
            rule_issues = _run_rule_engine(content_text, ctx)
            result.deterministic_issues.extend(rule_issues)
            if rule_issues:
                _log(f"  D.0: Rule engine: {len(rule_issues)} issue(s)")
        except Exception as e:
            logger.warning("D.0: Rule engine failed: %s", e)

    # 7.6 VESUM morphological validator
    if content_text is not None:
        try:
            morph_issues = _run_morphological_validator(content_text, ctx)
            result.deterministic_issues.extend(morph_issues)
            if morph_issues:
                _log(f"  D.0: Morphological validator: {len(morph_issues)} issue(s)")
        except Exception as e:
            logger.warning("D.0: Morphological validator failed: %s", e)

    # 9. Content quality pipeline checks
    if content_text is not None:
        try:
            cq_issues = _run_content_quality_checks(
                content_text, ctx, result.vesum_not_found)
            result.deterministic_issues.extend(cq_issues)
            if cq_issues:
                _log(f"  D.0: Content quality: {len(cq_issues)} issue(s)")
        except Exception as e:
            logger.warning("D.0: Content quality checks failed: %s", e)

    det_count = len(result.deterministic_issues)
    if det_count > 0:
        n_rules = sum(1 for i in result.deterministic_issues if i["type"] in ("PEDAGOGICAL", "DECODABILITY"))
        n_cq = sum(1 for i in result.deterministic_issues if i["type"] in (
            "UNTRANSLATED_NON_DECODABLE", "WALL_OF_TEXT", "LOW_ENGAGEMENT",
            "REPETITIVE_TRANSITIONS", "PLAN_SECTION_MISSING", "ACTIVITY_VESUM_FAIL"))
        _log(f"  D.0: {det_count} deterministic issue(s) found "
             f"({sum(1 for i in result.deterministic_issues if i['type'] == 'RUSSIANISM')} Russianisms, "
             f"{sum(1 for i in result.deterministic_issues if i['type'] == 'LLM_FILLER')} filler, "
             f"{n_rules} rule-engine, {n_cq} content-quality)")

    return result
