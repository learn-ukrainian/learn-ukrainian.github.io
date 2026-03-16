"""
Content quality and pedagogical audit phases.

Handles vocabulary checks, format checks, content detectors (purity,
imperial terminology, russicisms, colonial framing, euphony, prose quality),
and pedagogical compliance.
"""

from .checks import (
    check_content_quality,
    check_markdown_format,
    check_section_order,
    run_pedagogical_checks,
)
from .checks.colonial_framing import check_colonial_framing
from .checks.content_gaming import check_content_gaming
from .checks.content_purity import check_content_purity
from .checks.imperial_terminology import check_imperial_terminology
from .checks.prose_quality import check_prose_quality
from .checks.russicism_detection import check_russicisms
from .checks.state_standard_compliance import check_state_standard_compliance
from .checks.vocabulary import (
    check_metalanguage_scaffolding,
    check_vocab_matches_plan,
    check_vocab_table_format,
    extract_vocab_from_section,
    get_cumulative_vocab,
)
from .checks.vocabulary_integration import check_vocabulary_integration
from .parsing import AuditContext, AuditState


def run_vocab_and_format_checks(ctx: AuditContext, state: AuditState) -> None:
    """Run vocabulary plan compliance, metalanguage scaffolding, markdown format, and section order checks."""
    if ctx.vocab_data:
        vocab_words = set()
        for item in ctx.vocab_data:
            uk = item.get('lemma', '')
            if uk:
                vocab_words.add(uk.lower())
    else:
        vocab_words = extract_vocab_from_section(ctx.content)

    if ctx.level_code.upper() in ('A1', 'A2'):
        plan_violations = check_vocab_matches_plan(
            ctx.file_path, ctx.level_code, ctx.module_num, vocab_words
        )
        state.vocab_blocking = [v for v in plan_violations if v.get('blocking', True)]
        state.vocab_warnings = [v for v in plan_violations if not v.get('blocking', True)]
        if state.vocab_blocking:
            state.has_critical_failure = True

    cumulative_vocab = get_cumulative_vocab(ctx.level_code, ctx.module_num - 1)
    metalang_violations = check_metalanguage_scaffolding(
        ctx.content, vocab_words, ctx.level_code, ctx.module_num, cumulative_vocab
    )
    state.pedagogical_violations.extend(metalang_violations)

    markdown_violations = check_markdown_format(ctx.content, ctx.track_code)
    state.pedagogical_violations.extend(markdown_violations)

    if not ctx.vocab_data:
        vocab_format_violations = check_vocab_table_format(ctx.content, ctx.level_code)
        state.pedagogical_violations.extend(vocab_format_violations)

    section_order_violations = check_section_order(ctx.content)
    for v in section_order_violations:
        state.pedagogical_violations.append({
            'type': v['type'].upper(),
            'severity': v['severity'],
            'issue': v['message'],
            'fix': "Reorder sections to: Summary \u2192 Activities \u2192 Self-Assessment \u2192 External \u2192 Vocabulary",
            'line': v.get('line', 0)
        })


def run_content_detectors(ctx: AuditContext, state: AuditState) -> None:
    """Run content quality detectors: purity, imperial, russicism, colonial, euphony, prose, gaming."""
    content_quality_violations = check_content_quality(ctx.content, ctx.level_code, ctx.module_num, ctx.file_path)

    yaml_content_str = ""
    if ctx.yaml_file.exists():
        yaml_content_str = ctx.yaml_file.read_text(encoding='utf-8')
    purity_violations = check_content_purity(ctx.content, yaml_content_str)

    if purity_violations:
        print(f"  \u2728 Purity violations found: {len(purity_violations)}")
        for v in purity_violations:
            print(f"     \u274c [{v['type']}] {v['issue']}")
        content_quality_violations.extend(purity_violations)

    imperial_violations = check_imperial_terminology(ctx.content, ctx.file_path)
    if imperial_violations:
        errors = [v for v in imperial_violations if v["severity"] == "error"]
        warnings = [v for v in imperial_violations if v["severity"] == "warning"]
        if errors:
            print(f"  \U0001f6a9 Imperial framing violations: {len(errors)} error(s), {len(warnings)} warning(s)")
        else:
            print(f"  \u26a0\ufe0f  Imperial framing warnings: {len(warnings)}")
        for v in imperial_violations:
            icon = "\u274c" if v["severity"] == "error" else "\u26a0\ufe0f "
            print(f"     {icon} [{v['type']}] {v['issue']}")
        content_quality_violations.extend(imperial_violations)

    russicism_violations = check_russicisms(ctx.content, ctx.file_path)
    if russicism_violations:
        for v in russicism_violations:
            sev_icon = "\u274c" if v['severity'] == 'critical' else "\u26a0\ufe0f"
            print(f"     {sev_icon} [{v['type']}] {v['issue']}")
        content_quality_violations.extend(russicism_violations)

    colonial_violations = check_colonial_framing(ctx.content, ctx.file_path)
    if colonial_violations:
        print(f"  \U0001f3db\ufe0f  Colonial framing warnings: {len(colonial_violations)}")
        for v in colonial_violations:
            print(f"     \u26a0\ufe0f  [{v['type']}] {v['issue']}")
        content_quality_violations.extend(colonial_violations)

    # Euphony detector disabled — too many false positives on letter lists
    # and non-prose content. See check_euphony_violations() if re-enabling.
    # euphony_violations = check_euphony_violations(ctx.content, ctx.file_path)
    # if euphony_violations:
    #     print(f"  \U0001f3b5 Euphony violations: {len(euphony_violations)}")
    #     for v in euphony_violations:
    #         print(f"     \u26a0\ufe0f  [{v['type']}] {v['issue']}")
    #     content_quality_violations.extend(euphony_violations)

    prose_violations = check_prose_quality(ctx.content)
    if prose_violations:
        print(f"  \u2728 Prose quality violations found: {len(prose_violations)}")
        for v in prose_violations:
            print(f"     \u274c [{v['type']}] {v['issue']}")
        content_quality_violations.extend(prose_violations)

    gaming_violations = check_content_gaming(ctx.content, ctx.file_path)
    if gaming_violations:
        print(f"  \U0001f3ad Content gaming violations found: {len(gaming_violations)}")
        for v in gaming_violations:
            sev_icon = "\u274c" if v['severity'] == 'critical' else "\u26a0\ufe0f"
            print(f"     {sev_icon} [{v['type']}] {v['issue']}")
        content_quality_violations.extend(gaming_violations)

    for v in content_quality_violations:
        state.pedagogical_violations.append({
            'type': v['type'],
            'severity': v['severity'],
            'blocking': v['severity'] == 'critical',
            'issue': v['issue'],
            'fix': v['fix']
        })


def run_content_quality_checks(ctx: AuditContext, state: AuditState) -> None:
    """Run content quality, purity, imperial, russicism, colonial, euphony, prose checks."""
    ped_violations = run_pedagogical_checks(
        ctx.content, ctx.core_content, ctx.level_code, ctx.module_num, ctx.pedagogy, ctx.yaml_activities, ctx.module_focus
    )
    state.pedagogical_violations.extend(ped_violations)

    state_standard_violations = check_state_standard_compliance(
        ctx.level_code, ctx.module_num, ctx.content, immersion_pct=None
    )
    for violation in state_standard_violations:
        state.pedagogical_violations.append({
            'type': violation.code,
            'severity': 'blocking',
            'issue': violation.message,
            'fix': violation.fix
        })

    integration_data = check_vocabulary_integration(ctx.content, ctx.level_code, ctx.module_num, ctx.yaml_activities)
    if integration_data['total'] > 0:
        print(f"  \U0001f4ca Vocabulary Integration: Lesson {integration_data['lesson_rate']:.1f}%, Activities {integration_data['activity_rate']:.1f}%")

        if integration_data['lesson_rate'] < 50:
            state.pedagogical_violations.append({
                'type': 'LOW_LESSON_INTEGRATION',
                'severity': 'warning',
                'issue': f"Only {integration_data['lesson_rate']:.1f}% of core vocabulary used in lesson text.",
                'fix': f"Use more core words in the prose: {', '.join(integration_data['missing'][:5])}..."
            })
        if integration_data['activity_rate'] < 80:
            state.pedagogical_violations.append({
                'type': 'LOW_ACTIVITY_INTEGRATION',
                'severity': 'warning',
                'issue': f"Only {integration_data['activity_rate']:.1f}% of core vocabulary used in activities.",
                'fix': f"Add activities using: {', '.join(integration_data['missing'][:5])}..."
            })

    run_vocab_and_format_checks(ctx, state)
    run_content_detectors(ctx, state)
