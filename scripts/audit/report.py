"""
Report generation for module audits.

Generates markdown reports and console output for audit results.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from slug_utils import audit_report_path as _audit_report_path
from slug_utils import status_path as _status_path

from .report_helpers import (
    DRYNESS_FLAG_FIXES,
    LOW_DENSITY_SUGGESTIONS,
    build_gates_dict,
    compute_overall_status,
    gather_source_mtimes,
    sync_batch_state,
)


def save_status_cache(
    file_path: str,
    level_code: str,
    module_slug: str,
    results: dict,
    has_critical_failure: bool,
    critical_failure_reasons: list[str],
    plan_version: str = "2.0",
    review_violations: list | None = None,
    review_gate_status: str = "skipped",
) -> str:
    """Save status cache to {level}/status/{slug}.json."""
    md_path = Path(file_path)
    source_mtimes = gather_source_mtimes(md_path, module_slug)
    gates = build_gates_dict(results)

    # Review gate
    if review_violations is None:
        review_violations = []
    review_criticals = [v for v in review_violations if v.get('severity') == 'critical']
    gates['review'] = {
        "status": review_gate_status,
        "violations": len(review_criticals),
        "message": review_criticals[0]['message'] if review_criticals else "",
    }

    overall = compute_overall_status(gates, has_critical_failure, critical_failure_reasons)

    cache_data = {
        "module": module_slug,
        "level": level_code,
        "plan_version": plan_version,
        "last_audit": datetime.now().isoformat() + "Z",
        "audit_duration_ms": 0,
        "source_mtimes": source_mtimes,
        "gates": gates,
        "overall": overall
    }

    # Save file (merge with existing to preserve verification data)
    base_path = md_path.parent
    status_file = _status_path(base_path, module_slug)
    status_file.parent.mkdir(parents=True, exist_ok=True)

    existing_data = {}
    if status_file.exists():
        try:
            with open(status_file, encoding='utf-8') as f:
                existing_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    if 'verification' in existing_data:
        cache_data['verification'] = existing_data['verification']

    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)

    sync_batch_state(base_path, module_slug, overall.get("status", "fail"))
    return str(status_file)


def set_verification(
    status_file: str,
    tier: str,
    reviewer: str,
    score: float | None = None,
    evidence: str | None = None,
    critical_review: str | None = None
) -> bool:
    """
    Set verification data on an existing status JSON file.

    Args:
        status_file: Path to status/{slug}.json
        tier: 'llm-verified' or 'gold-standard'
        reviewer: Agent name (e.g., 'claude', 'gemini', 'human')
        score: Optional quality score (0-10)
        evidence: Optional evidence summary
        critical_review: Optional detailed review text

    Returns:
        True if successful, False otherwise
    """
    status_path = Path(status_file)
    if not status_path.exists():
        return False

    try:
        with open(status_path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    # Build verification block
    data['verification'] = {
        'tier': tier,
        'reviewer': reviewer,
        'timestamp': datetime.now().isoformat() + 'Z',
    }

    if score is not None:
        data['verification']['score'] = score
    if evidence:
        data['verification']['evidence'] = evidence
    if critical_review:
        data['verification']['critical_review'] = critical_review

    try:
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except OSError:
        return False


def _report_header(file_path: str, shown_level: str, module_num: int | None,
                    phase: str, pedagogy: str, target: int,
                    has_critical_failure: bool, naturalness: dict | None) -> list[str]:
    """Generate the header section of the audit report."""
    lines = []

    header_title = f"# Audit Report: {os.path.basename(file_path)}"
    if module_num is not None:
        header_title = f"# Audit Report: M{module_num:02d} — {os.path.basename(file_path)}"
    lines.append(header_title)

    meta_line = f"**Level:** {shown_level}"
    if module_num is not None:
        meta_line += f" | **Module:** M{module_num:02d}"
    meta_line += f" | **Phase:** {phase} | **Pedagogy:** {pedagogy} | **Target:** {target}"
    lines.append(meta_line)

    if naturalness:
        if isinstance(naturalness, dict):
            score = naturalness.get('score', 0)
            status = naturalness.get('status', 'PENDING')
        elif isinstance(naturalness, (int, float)):
            score = int(naturalness)
            status = 'PASS' if score >= 7 else 'FAIL'
        else:
            score, status = 0, 'PENDING'
        lines.append(f"**Naturalness:** {score}/10 ({status})")

    lines.append(f"**Overall Status:** {'❌ FAIL' if has_critical_failure else '✅ PASS'}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    return lines


def _report_config_section(config: dict, level_code: str, target: int,
                           module_focus: str | None) -> list[str]:
    """Generate the Configuration section of the audit report."""
    lines = ["## Configuration"]

    config_type = f"{level_code}"
    if module_focus:
        config_type += f"-{module_focus}"
    lines.append(f"**Type:** {config_type}")
    lines.append(f"**Word Target:** {target} words")

    min_act = config.get('min_activities', 0)
    max_act = config.get('max_activities', min_act + 4)
    lines.append(f"**Activities:** {min_act}-{max_act} required")
    lines.append(f"**Items per Activity:** ≥{config.get('min_items_per_activity', 1)} items")
    lines.append(f"**Unique Types:** ≥{config.get('min_types_unique', 2)} types required")

    priority_types = config.get('priority_types', set())
    if priority_types:
        lines.append(f"**Priority Types:** {', '.join(sorted(priority_types))}")

    required_types = config.get('required_types', set())
    if required_types:
        lines.append(f"**Required Types:** {', '.join(sorted(required_types))}")

    lines.append(f"**Engagement:** ≥{config.get('min_engagement', 3)} callouts")

    min_imm = config.get('min_immersion', 0)
    max_imm = config.get('max_immersion', 100)
    lines.append(f"**Immersion:** {min_imm}-{max_imm}%")
    lines.append(f"**Vocab Target:** ≥{config.get('min_vocab', 25)} words")

    translit = "Not allowed" if not config.get('transliteration_allowed', True) else "Allowed"
    lines.append(f"**Transliteration:** {translit}")
    lines.append("")

    return lines


def _report_activity_breakdown(activity_details: list[dict], config: dict | None,
                               unique_types: set | None) -> list[str]:
    """Generate the Activity Breakdown section of the audit report."""
    lines = ["## Activity Breakdown"]
    lines.append("| # | Type | Title | Items | Min | Status |")
    lines.append("|---|------|-------|-------|-----|--------|")

    for idx, act in enumerate(activity_details, 1):
        lines.append(f"| {idx} | {act['type']} | {act['title']} | {act['items']} | {act['target']} | {act['status']} |")

    lines.append("")
    lines.append("**Summary:**")

    total_acts = len(activity_details)
    min_act = config.get('min_activities', 0) if config else 0
    max_act = config.get('max_activities', min_act + 4) if config else total_acts
    # Activity counts are MINIMUMS per CLAUDE.md — exceeding max_act is a soft
    # warning, not a failure. Only undershooting min_act is a hard ❌.
    if total_acts < min_act:
        act_status = '❌'
    elif total_acts > max_act:
        act_status = '⚠️'
    else:
        act_status = '✅'
    lines.append(f"- Total activities: {total_acts} (target: ≥{min_act}, soft cap {max_act}) {act_status}")

    if unique_types:
        min_types = config.get('min_types_unique', 2) if config else 2
        types_status = '✅' if len(unique_types) >= min_types else '❌'
        lines.append(f"- Unique types: {len(unique_types)} (minimum: {min_types}) {types_status}")

    if config and config.get('priority_types'):
        priority_types = config['priority_types']
        priority_used = unique_types & priority_types if unique_types else set()
        priority_status = '✅' if priority_used else '❌'
        lines.append(f"- Priority types used: {len(priority_used)}/{len(priority_types)} ({', '.join(sorted(priority_used)) if priority_used else 'none'}) {priority_status}")

    if config and config.get('required_types'):
        required_types = config['required_types']
        required_used = unique_types & required_types if unique_types else set()
        all_required_present = required_types.issubset(unique_types) if unique_types else False
        required_status = '✅' if all_required_present else '❌'
        lines.append(f"- Required types used: {len(required_used)}/{len(required_types)} ({', '.join(sorted(required_used)) if required_used else 'none'}) {required_status}")

    low_density_count = sum(1 for act in activity_details if act['status'] == '❌')
    lines.append(f"- Low density activities: {low_density_count}")
    lines.append("")

    return lines


_DRYNESS_FLAG_FIXES = DRYNESS_FLAG_FIXES  # Re-export for backward compatibility


def _report_richness_section(richness_data: dict, richness_flags: list | None) -> list[str]:
    """Generate the Richness Details section of the audit report."""
    lines = ["", "## Richness Details"]
    score = richness_data.get('score', 0)
    threshold = richness_data.get('threshold', 95)
    lines.append(f"**Score:** {score}% (minimum: {threshold}%)")
    lines.append(f"**Module Type:** {richness_data.get('module_type', 'unknown')}")
    lines.append("")
    lines.append("### Score Breakdown")

    raw_counts = richness_data.get('raw', {})
    normalized = richness_data.get('normalized', {})
    targets = richness_data.get('targets', {})
    weights = richness_data.get('weights', {})

    if raw_counts:
        lines.append("| Metric | Count | Target | Score | Weight | Contribution |")
        lines.append("|--------|-------|--------|-------|--------|--------------|")
        total_contribution = 0

        sorted_metrics = sorted(raw_counts.keys(), key=lambda k: weights.get(k, 0), reverse=True)

        for metric in sorted_metrics:
            count = raw_counts[metric]
            target = targets.get(metric, '-')
            norm_score = normalized.get(metric, 0)
            weight = weights.get(metric, 0.05)
            contribution = norm_score * weight * 100
            total_contribution += contribution
            count_str = f"{count:.2f}" if isinstance(count, float) else str(count)
            target_str = str(target) if target != 0 else '-'
            lines.append(f"| {metric} | {count_str} | {target_str} | {norm_score:.0%} | {weight:.0%} | {contribution:.1f}% |")
        lines.append(f"| **TOTAL** | | | | | **{total_contribution:.1f}%** |")

    if richness_flags:
        lines.append("")
        lines.append("### Dryness Flags & Fixes")
        for flag in richness_flags:
            fix = _DRYNESS_FLAG_FIXES.get(flag, 'Address this issue to improve richness score')
            lines.append(f"- ❌ **{flag}**")
            lines.append("  - FIX:")
            for line in fix.split('\n'):
                lines.append(f"    {line}")

    return lines


def generate_report(
    file_path: str,
    phase: str,
    level_code: str,
    pedagogy: str,
    target: int,
    has_critical_failure: bool,
    results: dict,
    table_rows: list[str],
    lint_errors: list[str],
    pedagogical_violations: list[dict],
    recommendation: str,
    reasons: list[str],
    severity: int,
    low_density_activities: list[dict] | None = None,
    richness_data: dict | None = None,
    richness_flags: list | None = None,
    template_violations: list[dict] | None = None,
    naturalness: dict | None = None,
    module_num: int | None = None,
    config: dict | None = None,
    activity_details: list[dict] | None = None,
    unique_types: set | None = None,
    module_focus: str | None = None,
    display_level: str | None = None
) -> str:
    """Generate markdown report content."""
    report_lines = []
    shown_level = display_level if display_level else level_code

    # Header
    report_lines.extend(_report_header(
        file_path, shown_level, module_num, phase, pedagogy, target,
        has_critical_failure, naturalness
    ))

    # Configuration
    if config:
        report_lines.extend(_report_config_section(config, level_code, target, module_focus))

    # Activity Breakdown
    if activity_details:
        report_lines.extend(_report_activity_breakdown(activity_details, config, unique_types))

    # Lint errors
    if lint_errors:
        report_lines.append("## LINT ERRORS")
        for err in lint_errors:
            report_lines.append(f"- ❌ {err}")
        report_lines.append("")

    # Pedagogical violations
    if pedagogical_violations:
        report_lines.append("## PEDAGOGICAL VIOLATIONS")
        for v in pedagogical_violations:
            report_lines.append(f"- **[{v['type']}]** {v['issue']}")
            report_lines.append(f"  - FIX: {v['fix']}")
        report_lines.append("")

    # Template violations
    if template_violations:
        report_lines.append("## TEMPLATE COMPLIANCE")
        for v in template_violations:
            severity_icon = "❌" if v['severity'] == 'CRITICAL' else "⚠️"
            report_lines.append(f"- {severity_icon} **[{v['type']}]** {v['issue']}")
            report_lines.append(f"  - FIX: {v['fix']}")
        report_lines.append("")

    # Recommendation
    if recommendation != 'PASS':
        rec_icon = '🔄' if recommendation == 'REWRITE' else '📝'
        report_lines.append("## Recommendation")
        report_lines.append(f"**{rec_icon} {recommendation}** (severity {severity}/100)")
        report_lines.append("")
        if reasons:
            for reason in reasons:
                report_lines.append(f"- {reason}")
            report_lines.append("")

    # Gates
    report_lines.append("## Gates")
    keys_order = ['words', 'activities', 'density', 'unique_types', 'priority',
                  'engagement', 'audio', 'vocab', 'structure', 'lint', 'pedagogy', 'content_heavy', 'immersion', 'richness', 'grammar', 'naturalness', 'research']
    for k in keys_order:
        r = results.get(k)
        if r:
            if hasattr(r, 'icon'):
                report_lines.append(f"- **{k.capitalize()}:** {r.icon} {r.msg}")
            else:
                report_lines.append(f"- **{k.capitalize()}:** {r['icon']} {r['msg']}")

    # Richness details
    if richness_data:
        report_lines.extend(_report_richness_section(richness_data, richness_flags))

    # Low density activities
    if low_density_activities:
        report_lines.append("")
        report_lines.append("## Low Density Activities")
        report_lines.append("| Activity | Type | Items | Required | Fix |")
        report_lines.append("|----------|------|-------|----------|-----|")
        for act in low_density_activities:
            missing = act['target'] - act['items']
            report_lines.append(f"| {act['title']} | {act['type']} | {act['items']} | {act['target']} | Add {missing} more items |")
        report_lines.append("")

    # Section Audit
    report_lines.append("")
    report_lines.append("## Section Audit")
    report_lines.append("| Section | Status | Count | Notes |")
    report_lines.append("|---|---|---|---|")
    report_lines.extend(table_rows)

    return "\n".join(report_lines)


def save_report(file_path: str, report_content: str) -> str:
    """
    Save report to audit/ subdirectory as {bare_slug}-audit.md.

    Returns the report file path.
    """
    md_path = Path(os.path.abspath(file_path))
    report_dest = _audit_report_path(md_path.parent, md_path.stem)
    report_dest.parent.mkdir(parents=True, exist_ok=True)

    # Also check legacy name for manual content preservation
    legacy_path = report_dest.parent / f"{md_path.stem}-audit-report.md"

    # Preserve manual content if exists (check both new and legacy paths)
    manual_content = ""
    for check_path in (report_dest, legacy_path):
        if check_path.exists():
            try:
                existing_report = check_path.read_text(encoding='utf-8')
                if "<!-- MANUAL_NOTES -->" in existing_report:
                    parts = existing_report.split("<!-- MANUAL_NOTES -->")
                    if len(parts) > 1:
                        manual_content = "<!-- MANUAL_NOTES -->" + parts[1]
                        break
            except Exception:
                pass

    with open(report_dest, 'w', encoding='utf-8') as f:
        f.write(report_content)
        if manual_content:
            f.write("\n\n" + manual_content)

    return str(report_dest)


def print_gates(results: dict, level_code: str) -> None:
    """Print gate results to console."""
    print(f"\n--- STRICT GATES (Level {level_code}) ---")
    keys_order = ['persona', 'words', 'activities', 'density', 'unique_types', 'priority',
                  'engagement', 'audio', 'vocab', 'vocab_progression', 'structure', 'lint',
                  'pedagogy', 'content_heavy', 'grammar', 'naturalness', 'activity_quality', 'research']
    for k in keys_order:
        r = results.get(k)
        if r:
            if hasattr(r, 'icon'):  # GateResult dataclass
                print(f"{k.capitalize():<12} {r.icon} {r.msg}")
            else:  # dict
                print(f"{k.capitalize():<12} {r['icon']} {r['msg']}")

    imm = results.get('immersion')
    if imm:
        if hasattr(imm, 'icon'):
            print(f"Immersion    {imm.icon} {imm.msg}")
        else:
            print(f"Immersion    {imm['icon']} {imm['msg']}")

    richness = results.get('richness')
    if richness:
        if hasattr(richness, 'icon'):
            print(f"Richness     {richness.icon} {richness.msg}")
        else:
            print(f"Richness     {richness['icon']} {richness['msg']}")


def print_lint_errors(errors: list[str]) -> None:
    """Print lint errors to console."""
    if errors:
        print("\n❌ LINT ERRORS FOUND:")
        for err in errors:
            print(f"  - {err}")
        print("")


def print_pedagogical_violations(violations: list[dict]) -> None:
    """Print pedagogical violations to console."""
    if violations:
        print("\n📚 PEDAGOGICAL VIOLATIONS FOUND:")
        for v in violations:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")
        print("")


def print_template_violations(violations: list[dict]) -> None:
    """Print template compliance violations to console."""
    if violations:
        print("\n📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:")
        for v in violations:
            severity_icon = "🔴" if v['severity'] == 'CRITICAL' else "⚠️"
            print(f"  {severity_icon} [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")
        print("")


def print_recommendation(recommendation: str, reasons: list[str], severity: int) -> None:
    """Print recommendation to console."""
    if recommendation != 'PASS':
        if recommendation == 'REWRITE':
            rec_icon = '🔄'
            rec_color = 'REWRITE FROM SCRATCH'
        else:
            rec_icon = '📝'
            rec_color = 'UPDATE (patch fixes)'

        print(f"\n{rec_icon} RECOMMENDATION: {rec_color} (severity {severity}/100)")
        for reason in reasons:
            print(f"   → {reason}")
        print("")


def print_immersion_fix_hints(
    immersion_score: float,
    min_imm: int,
    max_imm: int,
    level_code: str,
    module_focus: str | None = None
) -> None:
    """Print hints for fixing immersion issues."""
    if immersion_score < min_imm:
        print(f"\n📚 IMMERSION TOO LOW ({immersion_score:.1f}% vs {min_imm}-{max_imm}% target)")
        print("   FIX: Convert simple explanations to Ukrainian")
        print("   FIX: Add more Ukrainian narratives/dialogues")
        print("   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)")
        if level_code in ('B1', 'B2', 'C1', 'C2') or level_code.startswith('B') or level_code.startswith('C'):
            print("   FIX: Write grammar rules in Ukrainian (not just examples)")

    elif immersion_score > max_imm:
        print(f"\n📚 IMMERSION TOO HIGH ({immersion_score:.1f}% vs {min_imm}-{max_imm}% target)")
        if level_code == 'A1':
            print("   FIX: Add English phonetic/alphabet explanations")
            print("   FIX: Expand English grammar theory sections")
            print("   FIX: Learner can't read Cyrillic yet - needs more English scaffolding")
        elif level_code == 'A2':
            print("   FIX: Add English explanations for case/aspect theory")
            print("   FIX: Expand English scaffolding for complex grammar")
        elif module_focus == 'grammar':
            print("   FIX: Add English grammar theory (this is a grammar-focused module)")
            print("   FIX: Explain complex concepts in English first, then Ukrainian examples")
            print("   FIX: Add 🔗 Language Link boxes comparing Ukrainian/English")
        else:
            print("   FIX: Add English context where needed")
            print("   FIX: Ensure translations are provided for complex passages")


def print_low_density_activities(low_density_activities: list[dict]) -> None:
    """Print which activities have insufficient items and how to fix them."""
    if not low_density_activities:
        return

    print("\n📊 ACTIVITIES WITH LOW DENSITY:")
    for act in low_density_activities:
        missing = act['target'] - act['items']
        print(f"  ❌ {act['title']}")
        print(f"     Current: {act['items']} items | Required: {act['target']} | Add: {missing} more")
        suggestion = LOW_DENSITY_SUGGESTIONS.get(act['type'], 'items to this activity')
        print(f"     → Add {missing} more {suggestion}")
    print("")


def append_mdx_errors_to_report(
    md_file_path: str,
    errors: list[str],
    warnings: list[str]
) -> bool:
    """
    Append MDX validation results to an existing review file.

    Args:
        md_file_path: Path to the source markdown file (used to find review file)
        errors: List of error messages from MDX validation
        warnings: List of warning messages from MDX validation

    Returns:
        True if successfully updated, False otherwise.
    """
    # Find the review file
    file_dir = os.path.dirname(os.path.abspath(md_file_path))
    file_name = os.path.basename(md_file_path)
    base_name = os.path.splitext(file_name)[0]

    target_dir = os.path.join(file_dir, 'audit') if not file_dir.endswith('audit') else file_dir

    report_path = os.path.join(target_dir, f"{base_name}-review.md")

    if not os.path.exists(report_path):
        # No review file exists - only create if there are actual issues
        if not errors and not warnings:
            return True  # Nothing to report, don't create file
        os.makedirs(target_dir, exist_ok=True)
        mdx_section = _format_mdx_section(errors, warnings)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Audit Report: {file_name}\n\n{mdx_section}")
        return True

    # Read existing report
    with open(report_path, encoding='utf-8') as f:
        content = f.read()

    # Remove existing MDX section if present
    import re
    content = re.sub(
        r'\n## MDX VALIDATION[\s\S]*?(?=\n## |\n<!-- MANUAL_NOTES -->|$)',
        '',
        content
    )

    # Find insertion point (after Gates section, before Section Audit)
    insertion_point = content.find('\n## Section Audit')
    if insertion_point == -1:
        # Fallback: insert before manual notes or at end
        insertion_point = content.find('<!-- MANUAL_NOTES -->')
        if insertion_point == -1:
            insertion_point = len(content)

    # Build MDX section
    mdx_section = _format_mdx_section(errors, warnings)

    # Insert MDX section
    new_content = content[:insertion_point] + mdx_section + content[insertion_point:]

    # Write updated report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def _format_mdx_section(errors: list[str], warnings: list[str]) -> str:
    """Format MDX validation results as markdown section."""
    lines = ["\n## MDX VALIDATION"]

    if errors:
        lines.append("### Errors")
        for err in errors:
            lines.append(f"- ❌ {err}")

    if warnings:
        lines.append("### Warnings")
        for warn in warnings:
            lines.append(f"- ⚠️ {warn}")

    if not errors and not warnings:
        lines.append("✅ No issues found")

    lines.append("")
    return "\n".join(lines)


def append_html_errors_to_report(
    md_file_path: str,
    errors: list[str],
    warnings: list[str],
    activities_found: int = 0
) -> bool:
    """
    Append HTML validation results to an existing review file.

    Args:
        md_file_path: Path to the source markdown file (used to find review file)
        errors: List of error messages from HTML validation
        warnings: List of warning messages from HTML validation
        activities_found: Number of interactive elements found

    Returns:
        True if successfully updated, False otherwise.
    """
    # Find the review file
    file_dir = os.path.dirname(os.path.abspath(md_file_path))
    file_name = os.path.basename(md_file_path)
    base_name = os.path.splitext(file_name)[0]

    target_dir = os.path.join(file_dir, 'audit') if not file_dir.endswith('audit') else file_dir

    report_path = os.path.join(target_dir, f"{base_name}-review.md")

    if not os.path.exists(report_path):
        # No review file exists - only create if there are actual issues
        if not errors and not warnings:
            return True  # Nothing to report, don't create file
        os.makedirs(target_dir, exist_ok=True)
        html_section = _format_html_section(errors, warnings, activities_found)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Audit Report: {file_name}\n\n{html_section}")
        return True

    # Read existing report
    with open(report_path, encoding='utf-8') as f:
        content = f.read()

    # Remove existing HTML section if present
    import re
    content = re.sub(
        r'\n## HTML VALIDATION[\s\S]*?(?=\n## |\n<!-- MANUAL_NOTES -->|$)',
        '',
        content
    )

    # Find insertion point (after MDX VALIDATION or Gates, before Section Audit)
    insertion_point = content.find('\n## Section Audit')
    if insertion_point == -1:
        # Try after MDX VALIDATION
        mdx_match = re.search(r'\n## MDX VALIDATION[\s\S]*?(?=\n## |$)', content)
        if mdx_match:
            insertion_point = mdx_match.end()
        else:
            # Fallback: insert before manual notes or at end
            insertion_point = content.find('<!-- MANUAL_NOTES -->')
            if insertion_point == -1:
                insertion_point = len(content)

    # Build HTML section
    html_section = _format_html_section(errors, warnings, activities_found)

    # Insert HTML section
    new_content = content[:insertion_point] + html_section + content[insertion_point:]

    # Write updated report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def _format_html_section(errors: list[str], warnings: list[str], activities_found: int) -> str:
    """Format HTML validation results as markdown section."""
    lines = ["\n## HTML VALIDATION"]

    if errors:
        lines.append("### Errors")
        for err in errors:
            lines.append(f"- ❌ {err}")

    if warnings:
        lines.append("### Warnings")
        for warn in warnings:
            lines.append(f"- ⚠️ {warn}")

    if not errors and not warnings:
        lines.append(f"✅ Renders correctly ({activities_found} interactive elements)")

    lines.append("")
    return "\n".join(lines)
