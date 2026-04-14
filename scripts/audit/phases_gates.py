"""
Gate evaluation audit phases.

Handles evaluation of core gates (words, activities, engagement, vocab,
structure, persona, lint), immersion, grammar/naturalness, activity quality,
content-heavy modules, and transliteration policy.
"""

import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from calculate_richness import calculate_richness_score, detect_dryness_flags
from slug_utils import grammar_path as _grammar_path
from slug_utils import quality_path as _quality_path
from slug_utils import to_bare_slug

from .checks.content_quality import (
    ACADEMIC_LATIN_ALLOWLIST,
    detect_track_from_path,
    is_academic_latin_context,
)
from .checks.content_recall_detection import (
    is_content_heavy_module,
    run_all_content_recall_checks,
)
from .checks.meta_validator import check_activity_hints_valid, check_research_file, check_seminar_meta_requirements
from .checks.state_standard_compliance import check_state_standard_compliance
from .checks.vocabulary import count_vocab_rows
from .cleaners import (
    calculate_immersion,
    clean_for_immersion,
    clean_for_stats,
)
from .config import get_a1_immersion_range, get_a2_immersion_range, get_b1_immersion_range
from .gates import (
    GateResult,
    evaluate_activity_count,
    evaluate_activity_quality,
    evaluate_audio,
    evaluate_content_heavy,
    evaluate_density,
    evaluate_engagement,
    evaluate_grammar,
    evaluate_immersion,
    evaluate_lint,
    evaluate_naturalness,
    evaluate_persona,
    evaluate_priority_types,
    evaluate_research_alignment,
    evaluate_richness,
    evaluate_unique_types,
    evaluate_vocab,
    evaluate_word_count,
)
from .lint import run_lint_checks
from .parsing import AuditContext, AuditState
from .report import print_immersion_fix_hints, print_low_density_activities


def _count_sandbox_lemmas(file_path: str) -> int | None:
    """Count lemma entries in the lexical sandbox for a module.

    Returns the number of lemmas, or None if no sandbox file exists.
    Lemmas appear as table data rows (``| lemma | ...``) or bullet entries
    (``- **word** ...``).
    """
    md_path = Path(file_path)
    bare_slug = to_bare_slug(md_path.stem)
    level_dir = md_path.parent
    sandbox_path = level_dir / "orchestration" / bare_slug / "lexical-sandbox.md"
    if not sandbox_path.exists():
        return None

    count = 0
    try:
        text = sandbox_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            # Table data rows: "| lemma | ..." but not header separators or header rows
            if (stripped.startswith("| ") and not stripped.startswith("|---") and not stripped.startswith("| Lemma")) or stripped.startswith("- **"):
                count += 1
    except OSError:
        return None
    return count


def count_words_and_engagement(ctx: AuditContext, state: AuditState) -> None:
    """Count words, engagement boxes, and audio links."""
    state.raw_words = len(ctx.body.split())
    core_lines = [line for line in ctx.core_content.split('\n') if not line.strip().startswith('|')]
    core_no_tables = '\n'.join(core_lines)
    core_cleaned = clean_for_stats(core_no_tables)
    state.total_words = len(core_cleaned.split())

    engagement_pattern = re.compile(
        r'(>\s*[\U0001f4a1\u26a1\U0001f3ac\U0001f3ad\U0001f4dc\u2694\ufe0f\U0001f517\U0001f30d\U0001f381\U0001f5e3\ufe0f\U0001f3e0\U0001f9ed\U0001f68c\U0001f687\U0001f39f\ufe0f\U0001f4f1\U0001f575\ufe0f\U0001f324\ufe0f\U0001f326\ufe0f\U0001f3b1\U0001f52e\U0001f1fa\U0001f1e6\U0001f550\ufe0f\u2753\U0001f6e0\ufe0f\U0001f482\U0001f96a\U0001f37a\U0001f6cd\ufe0f\U0001f3eb\U0001f3e5\U0001f48a\U0001f475\U0001f52c\U0001f3a8\U0001f504\U0001f4c5\U0001f343\u2744\ufe0f\U0001f682\u23f3\U0001f4da\U0001f372\U0001f963\U0001f957\U0001f959\U0001f95a\U0001f95b\U0001f9e9\u26a0\ufe0f\U0001f6d1\U0001f3af\U0001f3ae\U0001f393\U0001f50d])|'
        r'(>\s*\[!(note|tip|warning|caution|important|cultural|history-bite|myth-buster|quote|context|analysis|source|legacy|reflection|fact|culture|military|perspective|biography|folk-wisdom)\])|'
        r'(^:::(note|tip|warning|caution|important))',  # Starlight callout syntax (V6)
        re.MULTILINE,
    )
    state.engagement_count = len(engagement_pattern.findall(ctx.content))

    audio_pattern = re.compile(r'\[\U0001f50a\]\(.*?\)')
    state.audio_count = len(audio_pattern.findall(ctx.content))


def evaluate_core_gates(ctx: AuditContext, state: AuditState, structure_gate: GateResult) -> set:
    """Evaluate word count, activity, engagement, vocab, structure, persona, lint gates."""
    config = ctx.config
    vocab_target = config.get('min_vocab', 25)

    state.results['words'] = evaluate_word_count(state.total_words, ctx.target, state.raw_words)
    if state.results['words'].status == 'FAIL':
        state.has_critical_failure = True

    if ctx.skip_activities:
        deferred = GateResult('INFO', '\u23f3', "Deferred (content-only audit)")
        state.results['activities'] = deferred
        state.results['density'] = deferred
        state.results['unique_types'] = deferred
        state.results['priority'] = deferred
        unique_types = set()
    else:
        act_target = config['min_activities']
        state.results['activities'] = evaluate_activity_count(state.activity_count, act_target)
        if state.results['activities'].status == 'FAIL':
            state.has_critical_failure = True

        failed_density = state.total_activities - state.valid_density_count
        dens_threshold = config['min_items_per_activity']
        state.results['density'] = evaluate_density(failed_density, state.total_activities, dens_threshold, act_target)
        if state.results['density'].status == 'FAIL' and act_target > 0:
            state.has_critical_failure = True
            print_low_density_activities(state.low_density_activities)

        unique_types = set(state.found_activity_types)
        type_target = config['min_types_unique']
        state.results['unique_types'] = evaluate_unique_types(len(unique_types), type_target)
        if state.results['unique_types'].status == 'FAIL':
            state.has_critical_failure = True

        state.results['priority'] = evaluate_priority_types(unique_types, config['priority_types'])
        # Priority types are non-blocking for V6 modules with plan-driven activity_hints.
        # Downgrade FAIL → WARN so status.json/monitor API stay consistent with CLI output.
        has_plan_hints = ctx.plan_data and ctx.plan_data.get('activity_hints')
        if state.results['priority'].status == 'FAIL':
            if has_plan_hints:
                state.results['priority'] = GateResult('WARN', '⚠️', state.results['priority'].msg)
            else:
                state.has_critical_failure = True

        required_types = config.get('required_types', set())
        if required_types:
            missing_required = required_types - unique_types
            if missing_required:
                state.fail(f"Missing required activity types: {', '.join(sorted(missing_required))}")
                print(f"  \u274c Missing required activity types from meta.yaml: {', '.join(sorted(missing_required))}")

    eng_target = config.get('min_engagement', 3)
    state.results['engagement'] = evaluate_engagement(state.engagement_count, eng_target)
    if state.results['engagement'].status == 'FAIL':
        state.has_critical_failure = True

    state.results['audio'] = evaluate_audio(state.audio_count)

    if ctx.skip_activities:
        state.results['vocab'] = GateResult('INFO', '\u23f3', "Deferred (content-only audit)")
    else:
        vocab_count = len(ctx.vocab_data) if ctx.vocab_data else count_vocab_rows(ctx.content)
        state.results['vocab'] = evaluate_vocab(vocab_count, vocab_target)

    state.results['structure'] = structure_gate
    if state.results['structure'].status == 'FAIL':
        state.has_critical_failure = True

    # Persona was a V5 concept (writing persona in plan YAML). V6 controls tone
    # via prompt templates + golden fragments instead. Skip for V6 modules.
    if ctx.plan_data:
        state.results['persona'] = GateResult('INFO', 'ℹ️', "N/A (V6 — tone set by prompt template)")
    else:
        has_persona = ctx.meta_data is not None and 'persona' in (ctx.meta_data or {})
        has_voice = has_persona and 'voice' in ctx.meta_data['persona']
        has_role = has_persona and 'role' in ctx.meta_data['persona']
        state.results['persona'] = evaluate_persona(has_persona, has_voice, has_role)
        if state.results['persona'].status == 'FAIL':
            state.has_critical_failure = True

    state.lint_errors = run_lint_checks(ctx.content, ctx.section_map, ctx.module_num)
    state.results['lint'] = evaluate_lint(len(state.lint_errors))
    if state.results['lint'].status == 'FAIL':
        state.has_critical_failure = True

    meta_violations = check_seminar_meta_requirements(ctx.meta_data, ctx.level_code, ctx.pedagogy)
    research_violations = check_research_file(ctx.file_path)
    meta_violations.extend(research_violations)

    try:
        from research_quality import assess_research_compat, find_research_path
        _md_path = Path(ctx.file_path)
        _bare_slug = to_bare_slug(_md_path.stem)
        _research_path = find_research_path(_md_path.parent, _bare_slug)
        _research_info = None
        if _research_path:
            _research_info = assess_research_compat(_research_path, ctx.track_code.lower(), _md_path)
        state.results['research'] = evaluate_research_alignment(_research_info, _md_path.exists())
    except ImportError:
        state.results['research'] = GateResult('INFO', '\u2139\ufe0f', "N/A (research_quality not available)")

    activity_type_violations = check_activity_hints_valid(ctx.meta_data)
    meta_violations.extend(activity_type_violations)

    if meta_violations:
        print(f"  \U0001f4dc Meta YAML Validation: {len(meta_violations)} issues")
        for v in meta_violations:
             severity_icon = "\u274c" if v['severity'] == 'critical' else "\u26a0\ufe0f"
             print(f"     {severity_icon} [{v['type']}] {v['message']}")
             if v.get('fix'):
                 print(f"        Fix: {v['fix']}")
        if any(v['severity'] == 'critical' for v in meta_violations):
            state.has_critical_failure = True

    for v in meta_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': 'error' if v['severity'] == 'critical' else 'warning',
            'issue': v['message'],
            'fix': v.get('fix', '')
        })

    return unique_types


def evaluate_immersion(ctx: AuditContext, state: AuditState) -> tuple[float, int, int]:
    """Evaluate immersion gate and return (immersion_score, min_imm, max_imm)."""
    full_immersion_text = clean_for_immersion(ctx.body)
    immersion_score = calculate_immersion(full_immersion_text)

    if ctx.module_focus == 'checkpoint':
        min_imm, max_imm = 0, 100
        phase_label = " (checkpoint - no gate)"
    elif ctx.level_code == 'A1':
        sandbox_lemma_count = _count_sandbox_lemmas(ctx.file_path)
        min_imm, max_imm = get_a1_immersion_range(ctx.module_num)
        phase_label = f" (M{ctx.module_num:02d})"
        if sandbox_lemma_count is not None and sandbox_lemma_count < 20 and ctx.module_num > 10:
            phase_label += f" [sandbox:{sandbox_lemma_count}]"
    elif ctx.level_code == 'A2':
        min_imm, max_imm = get_a2_immersion_range(ctx.module_num)
        if ctx.module_num <= 20:
            phase_label = " (A2.1)"
        elif ctx.module_num <= 40:
            phase_label = " (A2.2)"
        else:
            phase_label = " (A2.3)"
    elif ctx.level_code == 'B1':
        min_imm, max_imm = get_b1_immersion_range(ctx.module_num)
        if ctx.module_num <= 5:
            phase_label = " (B1.0 Bridge)"
        elif ctx.module_num <= 10:
            phase_label = " (B1.1 Aspect)"
        elif ctx.module_num <= 20:
            phase_label = " (B1.2 Motion)"
        elif ctx.module_num <= 45:
            phase_label = " (B1.3-4 Complex)"
        elif ctx.module_num <= 65:
            phase_label = " (B1.5-6 Vocab)"
        else:
            phase_label = " (B1.7-8 Ukraine)"
    else:
        min_imm = ctx.config.get('min_immersion', 0)
        max_imm = ctx.config.get('max_immersion', 100)
        phase_label = f" ({ctx.module_focus})" if ctx.module_focus else ""

    from .gates import evaluate_immersion as _evaluate_immersion_gate
    state.results['immersion'] = _evaluate_immersion_gate(immersion_score, min_imm, max_imm, phase_label)
    if state.results['immersion'].status == 'FAIL':
        state.has_critical_failure = True
        print_immersion_fix_hints(immersion_score, min_imm, max_imm, ctx.level_code, ctx.module_focus)

    if ctx.level_code in ['B1', 'B2', 'C1', 'C2']:
        immersion_violations = check_state_standard_compliance(
            ctx.level_code, ctx.module_num, ctx.content, immersion_pct=immersion_score
        )
        for violation in immersion_violations:
            state.pedagogical_violations.append({
                'type': violation.code,
                'severity': 'warning',
                'issue': violation.message,
                'fix': violation.fix
            })

    return immersion_score, min_imm, max_imm


def evaluate_grammar_and_naturalness(ctx: AuditContext, state: AuditState) -> None:
    """Evaluate grammar validation + naturalness check."""
    if ctx.level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        yaml_activity_types = set(state.found_activity_types) if ctx.use_yaml_activities else None
        richness_result = calculate_richness_score(ctx.content, ctx.level_code, ctx.file_path, yaml_activity_types)
        richness_flags = detect_dryness_flags(ctx.content, ctx.level_code, ctx.file_path)
        state.results['richness'] = evaluate_richness(
            richness_result['score'],
            richness_result['threshold'],
            richness_result.get('module_type', 'grammar'),
            richness_flags,
        )
        if state.results['richness'].status == 'FAIL':
            state.has_critical_failure = True
            print(f"\n\u26a0\ufe0f  Richness below threshold ({richness_result['score']}% < {richness_result['threshold']}% min)")
            if richness_flags:
                print("   Dryness flags:")
                for flag in richness_flags:
                    print(f"     - {flag}")

    md_abs = Path(os.path.abspath(ctx.file_path))
    grammar_file = str(_grammar_path(md_abs.parent, md_abs.stem))
    if not os.path.exists(grammar_file):
        legacy_grammar = os.path.join(str(md_abs.parent), 'audit', f"{md_abs.stem}-grammar.yaml")
        if os.path.exists(legacy_grammar):
            grammar_file = legacy_grammar

    grammar_summary = None
    if os.path.exists(grammar_file):
        try:
            with open(grammar_file, encoding='utf-8') as f:
                grammar_data = yaml.safe_load(f)
                grammar_summary = grammar_data.get('summary', {})
        except Exception:
            pass

    state.results['grammar'] = evaluate_grammar(os.path.exists(grammar_file), grammar_summary)

    nat_score = 0
    nat_status = "PENDING"

    if ctx.meta_data and 'naturalness' in ctx.meta_data:
        nat_val = ctx.meta_data['naturalness']
        if isinstance(nat_val, dict):
            nat_score = nat_val.get('score', 0) or 0
            nat_status = nat_val.get('status', 'PENDING') or 'PENDING'
        elif isinstance(nat_val, (int, float)):
            nat_score = int(nat_val)
            nat_status = 'PASS' if nat_score >= 7 else 'FAIL'

    state.results['naturalness'] = evaluate_naturalness(nat_score, nat_status, ctx.level_code)
    if state.results['naturalness'].status == 'FAIL':
        state.has_critical_failure = True


def evaluate_activity_quality_gate(ctx: AuditContext, state: AuditState) -> None:
    """Evaluate activity quality gate from quality report file."""
    md_abs = Path(os.path.abspath(ctx.file_path))
    if ctx.skip_activities:
        state.results['activity_quality'] = GateResult('INFO', '\u23f3', "Deferred (content-only audit)")
        return

    quality_file = str(_quality_path(md_abs.parent, md_abs.stem))
    if not os.path.exists(quality_file):
        legacy_quality = os.path.join(str(md_abs.parent), 'audit', f"{md_abs.stem}-quality.md")
        if os.path.exists(legacy_quality):
            quality_file = legacy_quality
    quality_result = None
    quality_failed_gates = 0

    if os.path.exists(quality_file):
        try:
            with open(quality_file, encoding='utf-8') as f:
                quality_content = f.read()
                if '**Result:** \u2705 PASS' in quality_content:
                    quality_result = 'PASS'
                elif '**Result:** \u274c FAIL' in quality_content:
                    quality_result = 'FAIL'
                    failed_gates_section = re.search(r'### Failed Gates\n\n(.*?)\n\n', quality_content, re.DOTALL)
                    if failed_gates_section:
                        quality_failed_gates = len(re.findall(r'^- \*\*', failed_gates_section.group(1), re.MULTILINE))
        except Exception:
            pass

    state.results['activity_quality'] = evaluate_activity_quality(
        os.path.exists(quality_file),
        quality_result,
        quality_failed_gates,
        ctx.level_code
    )


def check_transliteration_policy(ctx: AuditContext, state: AuditState) -> None:
    """Check transliteration policy compliance."""
    transliteration_allowed = ctx.config.get('transliteration_allowed', True)
    if not transliteration_allowed:
        translit_ok = False
        if ctx.meta_data:
            if 'transliteration' not in ctx.meta_data:
                translit_ok = True
            else:
                val = ctx.meta_data['transliteration']
                translit_ok = (val is None or str(val).lower() == 'none')
        elif not ctx.meta_data and ctx.plan_data:
            # V6 modules: plan used as frontmatter, no meta sidecar.
            # Plan doesn't have 'transliteration' field — treat as compliant.
            translit_ok = True
        elif not ctx.frontmatter_str:
            # No frontmatter at all — compliant
            translit_ok = True
        if not translit_ok:
            translit_ok = bool(re.search(r'transliteration:\s*["\']?none["\']?', ctx.frontmatter_str or ''))
        if not translit_ok:
            print(f"\u274c AUDIT FAILED: Level {ctx.level_code} forbids transliteration. Set 'transliteration: none' in frontmatter.")
            state.has_critical_failure = True

        track_for_translit = detect_track_from_path(ctx.file_path)
        is_bridge_module = (ctx.level_code == 'B1' and ctx.module_num <= 5)
        content_lines = ctx.content.split('\n')
        for line_idx, line in enumerate(content_lines):
            if '___' in line or '[___:' in line:
                continue
            if re.search(r'\((Dat|Acc|Gen|Loc|Ins|Nom|Voc)\)', line):
                continue
            # Skip heading lines — bilingual headings (e.g., "## Підсумок (Summary)")
            # are standard A1-A2 practice, not transliteration
            if line.lstrip().startswith('#'):
                continue
            translit_pattern = re.search(r'[\u0400-\u04ff]+\s*\(([A-Za-z]+)\)', line)
            if translit_pattern:
                latin_part = translit_pattern.group(1)
                if latin_part.upper() in ACADEMIC_LATIN_ALLOWLIST:
                    continue
                if is_academic_latin_context(line, content_lines, line_idx, track_for_translit):
                    continue
                if is_bridge_module:
                    continue
                print(f"\u274c AUDIT FAILED: Transliteration detected: '{translit_pattern.group()}'. Remove Latin in parentheses.")
                state.has_critical_failure = True
                break


def evaluate_advanced_gates(ctx: AuditContext, state: AuditState) -> None:
    """Evaluate richness, grammar, naturalness, activity quality, content-heavy, transliteration gates."""
    evaluate_grammar_and_naturalness(ctx, state)

    evaluate_activity_quality_gate(ctx, state)

    if ctx.skip_activities:
        state.results['content_heavy'] = GateResult('INFO', '\u23f3', "Deferred (content-only audit)")
    else:
        is_ch = is_content_heavy_module(ctx.level_code, ctx.module_num, ctx.module_focus or "")
        content_recall_violations = []
        if is_ch:
            content_recall_violations = run_all_content_recall_checks(
                ctx.content, ctx.level_code, ctx.module_focus or "",
                yaml_activities=ctx.yaml_activities
            )

        min_act = ctx.config.get('min_activities', 10)
        max_act = ctx.config.get('max_activities', min_act + 4)

        state.results['content_heavy'] = evaluate_content_heavy(
            is_ch, state.activity_count, content_recall_violations,
            min_act=min_act, max_act=max_act
        )

    check_transliteration_policy(ctx, state)
