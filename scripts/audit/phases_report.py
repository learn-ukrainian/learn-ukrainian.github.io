"""
Report generation and finalization audit phases.

Handles printing gates, generating reports, review validation,
gaming detection, and saving status caches.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from calculate_richness import calculate_richness_score, detect_dryness_flags
from slug_utils import to_bare_slug

from .checks.review_gaming import check_review_gaming
from .checks.review_validation import check_review_validity
from .gates import compute_recommendation
from .parsing import AuditContext, AuditState
from .report import (
    generate_report,
    print_gates,
    print_lint_errors,
    print_pedagogical_violations,
    print_recommendation,
    print_template_violations,
    save_report,
    save_status_cache,
)


def print_and_save_report(ctx: AuditContext, state: AuditState,
                           immersion_score: float, min_imm: int, max_imm: int,
                           unique_types: set) -> None:
    """Print gates, violations, generate report, and save."""
    print_gates(state.results, ctx.level_code)
    print_lint_errors(state.lint_errors)
    print_pedagogical_violations(state.pedagogical_violations)
    print_template_violations(state.template_violations)

    if state.vocab_blocking:
        print("\n\u274c MISSING CORE VOCABULARY (blocking):")
        for v in state.vocab_blocking:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     \u2192 FIX: {v['fix']}")

    if state.vocab_warnings:
        print("\n\u26a0\ufe0f  VOCABULARY WARNINGS (informational):")
        for v in state.vocab_warnings:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     \u2192 FIX: {v['fix']}")

    all_violations_for_severity = state.pedagogical_violations + state.vocab_blocking + state.vocab_warnings + state.template_violations
    recommendation, reasons, severity = compute_recommendation(
        all_violations_for_severity, state.lint_errors, state.results, immersion_score,
        min_imm, max_imm, ctx.level_code
    )
    print_recommendation(recommendation, reasons, severity)

    all_violations_for_report = state.pedagogical_violations + state.vocab_blocking + state.vocab_warnings

    richness_data = None
    richness_flags_for_report = None
    if ctx.level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        yaml_activity_types = set(state.found_activity_types) if ctx.use_yaml_activities else None
        richness_data = calculate_richness_score(ctx.content, ctx.level_code, ctx.file_path, yaml_activity_types)
        richness_flags_for_report = detect_dryness_flags(ctx.content, ctx.level_code, ctx.file_path)

    naturalness_data = ctx.meta_data.get('naturalness') if ctx.meta_data else None

    report_content = generate_report(
        ctx.file_path, ctx.phase, ctx.level_code, ctx.pedagogy, ctx.target,
        state.has_critical_failure, state.results, state.table_rows,
        state.lint_errors, all_violations_for_report,
        recommendation, reasons, severity,
        state.low_density_activities,
        richness_data=richness_data,
        richness_flags=richness_flags_for_report,
        template_violations=state.template_violations,
        naturalness=naturalness_data,
        module_num=ctx.module_num,
        config=ctx.config,
        activity_details=state.activity_details,
        unique_types=unique_types,
        module_focus=ctx.module_focus,
        display_level=ctx.display_level
    )
    report_path = save_report(ctx.file_path, report_content)
    print(f"\nReport: {report_path}")


def check_review_gaming_phase(ctx: AuditContext, state: AuditState,
                               module_slug: str, review_violations: list,
                               review_gate_status: str) -> tuple[list, str]:
    """Run review gaming detection on the review file."""
    from slug_utils import review_path as _review_path_fn
    _review_base = Path(ctx.file_path).parent
    _review_canonical = _review_path_fn(_review_base, module_slug)
    _review_file_path = None
    if _review_canonical.exists():
        _review_file_path = _review_canonical
    else:
        _bare = to_bare_slug(module_slug)
        _legacy = _review_base / 'audit' / f'{_bare}-review.md'
        if _legacy.exists():
            _review_file_path = _legacy

    if _review_file_path:
        try:
            _review_text = _review_file_path.read_text(encoding='utf-8')
            gaming_review_violations = check_review_gaming(
                _review_text, ctx.content, ctx.file_path, ctx.level_code, module_slug
            )
            if gaming_review_violations:
                g_crits = [v for v in gaming_review_violations if v['severity'] == 'critical']
                g_warns = [v for v in gaming_review_violations if v['severity'] == 'warning']
                print(f"  \U0001f3ad Review Gaming: {len(g_crits)} critical, {len(g_warns)} warnings")
                for v in g_crits:
                    print(f"     \u274c [{v['type']}] {v['message']}")
                    state.critical_failure_reasons.append(v['message'])
                for v in g_warns:
                    print(f"     \u26a0\ufe0f  [{v['type']}] {v['message']}")
                review_violations.extend(gaming_review_violations)
                if g_crits and review_gate_status == "pass":
                    review_gate_status = "fail"
                    state.has_critical_failure = True
        except OSError:
            pass

    return review_violations, review_gate_status


def validate_review_and_finalize(ctx: AuditContext, state: AuditState) -> bool:
    """Run review validation, gaming detection, save status cache, return final verdict."""
    review_violations = []
    review_gate_status = "skipped"
    if ctx.skip_activities or ctx.skip_review:
        review_gate_status = "deferred"
    elif ctx.plan_data:
        # V6 modules: review has different format (Scores table + Findings + Verdict).
        # Skip V5 review validation — V6 review quality is checked by the build pipeline.
        review_gate_status = "pass"
        print("  ℹ️  V6 module — skipping V5 review format validation")
    elif not state.has_critical_failure:
        module_slug_for_review = Path(ctx.file_path).stem
        review_violations = check_review_validity(ctx.file_path, ctx.level_code, module_slug_for_review)
        if review_violations:
            criticals = [v for v in review_violations if v['severity'] == 'critical']
            warnings = [v for v in review_violations if v['severity'] == 'warning']
            print(f"  \U0001f575\ufe0f  Review Validation: {len(criticals)} critical, {len(warnings)} warnings")
            for v in criticals:
                print(f"     \u274c [{v['type']}] {v['message']}")
                state.critical_failure_reasons.append(v['message'])
            for v in warnings:
                print(f"     \u26a0\ufe0f  [{v['type']}] {v['message']}")
            if criticals:
                review_gate_status = "fail"
                state.has_critical_failure = True
            else:
                review_gate_status = "pass"
        else:
            review_gate_status = "pass"

        review_violations, review_gate_status = check_review_gaming_phase(
            ctx, state, module_slug_for_review, review_violations, review_gate_status
        )
    else:
        review_gate_status = "skipped"

    try:
        module_slug = Path(ctx.file_path).stem
        plan_ver = ctx.meta_data.get('version', '2.0') if ctx.meta_data else '2.0'
        cache_path = save_status_cache(
            ctx.file_path,
            ctx.level_code,
            module_slug,
            state.results,
            state.has_critical_failure,
            state.critical_failure_reasons,
            plan_version=plan_ver,
            review_violations=review_violations,
            review_gate_status=review_gate_status,
        )
        print(f"Status: {cache_path}")
    except Exception as e:
        print(f"\u26a0\ufe0f Failed to save status cache: {e}")

    if state.has_critical_failure:
        print("\n\u274c AUDIT FAILED. Correct errors before proceeding.")
        if state.critical_failure_reasons:
            print("\nCritical Failures:")
            for reason in state.critical_failure_reasons:
                print(f"  \u2022 {reason}")
        return False
    else:
        print("\n\u2705 AUDIT PASSED.")
        return True


def generate_output_and_report(ctx: AuditContext, state: AuditState,
                                immersion_score: float, min_imm: int, max_imm: int,
                                unique_types: set) -> bool:
    """Print gates, generate report, run review validation, save status cache."""
    print_and_save_report(ctx, state, immersion_score, min_imm, max_imm, unique_types)
    return validate_review_and_finalize(ctx, state)
