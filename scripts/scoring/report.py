"""
Report generation for track scoring.

Generates formatted output showing:
- Automated metrics summary
- Criterion scores with evidence
- Critical caps applied
- Gap analysis for improvement
"""

from datetime import datetime
from typing import Optional

from .aggregator import TrackMetrics, TrackScore
from .config import get_track_config
from .caps import check_cap_violations
from .sampling import calculate_sampling_metrics


def format_metrics_table(track_metrics: TrackMetrics) -> str:
    """
    Format aggregated metrics as a table.

    Args:
        track_metrics: Aggregated track metrics

    Returns:
        Formatted string with metrics table
    """
    lines = [
        "AUTOMATED METRICS (from extract_track_metrics.py):",
        "┌─────────────────────────────────┬─────────┬─────────────────────────────┐",
        "│ Metric                          │ Total   │ Per Module Avg              │",
        "├─────────────────────────────────┼─────────┼─────────────────────────────┤",
    ]

    n = track_metrics.modules_found if track_metrics.modules_found > 0 else 1

    # Callout metrics
    metrics_data = [
        ("[!quote] callouts", track_metrics.total_quote_callouts, track_metrics.avg_quote_callouts),
        ("[!myth-buster] callouts", track_metrics.total_myth_buster_callouts, track_metrics.avg_myth_buster_callouts),
        ("[!history-bite] callouts", track_metrics.total_history_bite_callouts, track_metrics.total_history_bite_callouts / n),
        ("[!analysis] callouts", track_metrics.total_analysis_callouts, track_metrics.avg_analysis_callouts),
        ("Agency markers", track_metrics.total_agency_markers, track_metrics.total_agency_markers / n),
        ("Toponym violations", track_metrics.total_toponym_violations, track_metrics.total_toponym_violations / n),
        ("Cross-references", track_metrics.total_cross_references, track_metrics.avg_cross_references),
        ("Stylistic devices", track_metrics.total_stylistic_devices, track_metrics.total_stylistic_devices / n),
        ("Analysis sections", track_metrics.total_analysis_sections, track_metrics.total_analysis_sections / n),
        ("Legacy sections", track_metrics.total_legacy_sections, track_metrics.total_legacy_sections / n),
    ]

    for name, total, avg in metrics_data:
        if total > 0 or name in ("[!quote] callouts", "Cross-references"):  # Always show key metrics
            lines.append(f"│ {name:<31} │ {total:>7,} │ {avg:>27.2f} │")

    lines.append("├─────────────────────────────────┼─────────┼─────────────────────────────┤")

    # Coverage metrics
    coverage_data = [
        ("Modules with activities", track_metrics.modules_with_activities, track_metrics.modules_found),
        ("Modules with vocabulary", track_metrics.modules_with_vocabulary, track_metrics.modules_found),
        ("Modules with status JSON", track_metrics.modules_with_status, track_metrics.modules_found),
    ]

    for name, count, total in coverage_data:
        pct = (count / total * 100) if total > 0 else 0
        lines.append(f"│ {name:<31} │ {count:>3}/{total:<3} │ {pct:>26.0f}% │")

    lines.append("└─────────────────────────────────┴─────────┴─────────────────────────────┘")

    return "\n".join(lines)


def format_validation_table(track_metrics: TrackMetrics) -> str:
    """Format validation tiers table."""
    total = track_metrics.modules_found
    if total == 0:
        return ""

    automated = track_metrics.total_automated
    llm = track_metrics.total_llm_verified
    gold = track_metrics.total_gold_standard

    lines = [
        "VALIDATION TIERS:",
        "┌───────────────────────────────┬───────┬────────┐",
        "│ Tier                          │ Count │ %      │",
        "├───────────────────────────────┼───────┼────────┤",
        f"│ Tier 1: Automated             │ {automated:>5} │ {automated/total*100:>5.1f}% │",
        f"│ Tier 2: LLM Verified          │ {llm:>5} │ {llm/total*100:>5.1f}% │",
        f"│ Tier 3: Gold Standard         │ {gold:>5} │ {gold/total*100:>5.1f}% │",
        "└───────────────────────────────┴───────┴────────┘",
    ]
    return "\n".join(lines)


def format_scores_table(track_score: TrackScore) -> str:
    """
    Format criterion scores as a table.

    Args:
        track_score: Calculated track score

    Returns:
        Formatted string with scores table
    """
    config = get_track_config(track_score.track_id)

    lines = [
        "CRITERIA SCORES (with evidence):",
        "┌─────────────────────────────────┬────────┬───────┬──────────┬─────────────────────────────┐",
        "│ Criterion                       │ Weight │ Score │ Weighted │ Evidence                    │",
        "├─────────────────────────────────┼────────┼───────┼──────────┼─────────────────────────────┤",
    ]

    for criterion_name, criterion_config in config['criteria'].items():
        name = criterion_config['name'][:31]
        weight = criterion_config['weight']
        score = track_score.final_criterion_scores.get(criterion_name, 0.0)
        weighted = track_score.weighted_contributions.get(criterion_name, 0.0)

        # Generate evidence summary
        evidence = _get_evidence_summary(criterion_name, track_score)

        # Truncate evidence if too long
        if len(evidence) > 27:
            evidence = evidence[:24] + "..."

        lines.append(f"│ {name:<31} │ {weight:>5.0%} │ {score:>5.1f} │ {weighted:>8.2f} │ {evidence:<27} │")

    lines.append("├─────────────────────────────────┼────────┼───────┼──────────┼─────────────────────────────┤")
    lines.append(f"│ {'TOTAL':<31} │ {'100%':>6} │       │ {track_score.total_weighted_score:>8.2f} │                             │")
    lines.append("└─────────────────────────────────┴────────┴───────┴──────────┴─────────────────────────────┘")

    return "\n".join(lines)


def _get_evidence_summary(criterion_name: str, track_score: TrackScore) -> str:
    """Get brief evidence summary for a criterion."""
    # This is a simplified version - could be enhanced with actual metrics
    score = track_score.final_criterion_scores.get(criterion_name, 0.0)

    evidence_map = {
        'audit_pass_rate': lambda s: f"Based on status JSONs",
        'primary_source_integration': lambda s: f"[!quote] callouts",
        'historical_accuracy': lambda s: f"Naturalness gate",
        'decolonization_perspective': lambda s: f"Myth+agency metrics",
        'era_vocabulary': lambda s: f"Vocab file coverage",
        'chronological_coherence': lambda s: f"Timeline verified",
        'critical_analysis_skills': lambda s: f"Analysis activities",
        'activity_coverage': lambda s: f"Activity files",
        'vocabulary_coverage': lambda s: f"Vocab files",
        'internal_consistency': lambda s: f"Cross-refs",
        'literary_depth': lambda s: f"Devices+sections",
        'authentic_text_engagement': lambda s: f"Citation ratio",
        'biographical_accuracy': lambda s: f"Naturalness gate",
        'source_reliability': lambda s: f"Quote diversity",
        'significance_assessment': lambda s: f"Legacy sections",
        'cultural_historical_context': lambda s: f"Context callouts",
    }

    if criterion_name in evidence_map:
        return evidence_map[criterion_name](score)
    return f"Score: {score:.1f}/10"


def format_caps_section(track_score: TrackScore) -> str:
    """
    Format critical caps section.

    Args:
        track_score: Calculated track score

    Returns:
        Formatted string with caps information
    """
    lines = ["CRITICAL CAPS APPLIED:"]

    if not track_score.caps_applied:
        lines.append("  ✅ No caps triggered (all thresholds met)")
    else:
        for cap in track_score.caps_applied:
            lines.append(f"  ⚠️  {cap.cap_name}: {cap.cap_reason}")
            lines.append(f"      Original: {cap.original_score:.1f} → Capped: {cap.capped_score:.1f}")

    return "\n".join(lines)


def format_gaps_section(track_score: TrackScore, track_metrics: TrackMetrics) -> str:
    """
    Format gap analysis section showing what needs improvement.

    Args:
        track_score: Calculated track score
        track_metrics: Aggregated track metrics

    Returns:
        Formatted string with gap analysis
    """
    lines = ["GAPS TO 10/10:"]

    config = get_track_config(track_score.track_id)

    # Find criteria scoring below 9
    gaps = []
    for criterion_name, score in track_score.final_criterion_scores.items():
        if score < 9.0:
            criterion_config = config['criteria'].get(criterion_name, {})
            weight = criterion_config.get('weight', 0)
            name = criterion_config.get('name', criterion_name)
            gaps.append((name, score, weight, criterion_name))

    # Sort by weight (most impactful gaps first)
    gaps.sort(key=lambda x: -x[2])

    if not gaps:
        lines.append("  ✅ All criteria at 9+ (excellent)")
        return "\n".join(lines)

    for name, score, weight, criterion_name in gaps[:5]:  # Top 5 gaps
        lines.append(f"")
        lines.append(f"  ❌ {name} ({score:.1f}/10):")
        fix = _get_fix_suggestion(criterion_name, track_metrics)
        lines.append(f"     → FIX: {fix}")

    # Calculate projected score if gaps fixed
    max_improvement = sum((10.0 - score) * weight for _, score, weight, _ in gaps)
    projected = min(10.0, track_score.total_weighted_score + max_improvement)
    lines.append(f"")
    lines.append(f"PROJECTED SCORE AFTER FIXES: {projected:.1f}/10")

    # Add Sampling Recommendations if coverage is low
    total = track_metrics.modules_found
    if total > 0 and (track_metrics.total_llm_verified + track_metrics.total_gold_standard) / total < 0.2:
        lines.append(f"")
        lines.append(f"SAMPLING RECOMMENDATIONS (Tier 2/3):")
        # Note: In a real scenario we'd need the raw module data here.
        # For now, we add a placeholder note that sampling is advised.
        lines.append(f"  ⚠️  Validation coverage is low. Run validation pipeline on risk-prioritized modules.")

    return "\n".join(lines)


def _get_fix_suggestion(criterion_name: str, track_metrics: TrackMetrics) -> str:
    """Get fix suggestion for a criterion gap."""
    fixes = {
        'audit_pass_rate': f"Fix {track_metrics.failing_modules} failing modules",
        'primary_source_integration': f"Add [!quote] callouts ({track_metrics.total_quote_callouts} currently)",
        'decolonization_perspective': f"Add [!myth-buster] callouts, increase agency markers",
        'era_vocabulary': f"Create vocabulary files for {track_metrics.total_modules - track_metrics.modules_with_vocabulary} modules",
        'activity_coverage': f"Add activity files for {track_metrics.total_modules - track_metrics.modules_with_activities} modules",
        'vocabulary_coverage': f"Add vocabulary files for {track_metrics.total_modules - track_metrics.modules_with_vocabulary} modules",
        'internal_consistency': f"Add 'Related:' cross-references ({track_metrics.total_cross_references} currently)",
        'literary_depth': f"Add analysis sections ({track_metrics.total_analysis_sections} currently)",
        'authentic_text_engagement': f"Increase citation ratio (currently {track_metrics.avg_citation_ratio:.1%})",
        'significance_assessment': f"Add legacy/impact sections ({track_metrics.total_legacy_sections} currently)",
        'critical_analysis_skills': f"Add critical-analysis activities",
    }

    return fixes.get(criterion_name, "Improve this criterion")


def generate_track_report(
    track_metrics: TrackMetrics,
    track_score: TrackScore,
    output_format: str = 'console'
) -> str:
    """
    Generate complete track scoring report.

    Args:
        track_metrics: Aggregated track metrics
        track_score: Calculated track score
        output_format: 'console' or 'markdown'

    Returns:
        Formatted report string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    if output_format == 'markdown':
        return _generate_markdown_report(track_metrics, track_score, timestamp)

    return _generate_console_report(track_metrics, track_score, timestamp)


def _generate_console_report(
    track_metrics: TrackMetrics,
    track_score: TrackScore,
    timestamp: str
) -> str:
    """Generate console-formatted report."""
    lines = [
        "",
        "═" * 70,
        f"  {track_score.track_name} Scoring Report",
        f"  Generated: {timestamp} | Modules: {track_metrics.modules_found} | Coverage: {track_metrics.modules_found / track_metrics.total_modules * 100:.0f}%",
        "═" * 70,
        "",
        format_metrics_table(track_metrics),
        "",
        format_validation_table(track_metrics),
        "",
        format_scores_table(track_score),
        "",
        format_caps_section(track_score),
        "",
        format_gaps_section(track_score, track_metrics),
        "",
        "═" * 70,
        f"  FINAL SCORE: {track_score.total_weighted_score:.2f}/10",
        "═" * 70,
        "",
    ]

    return "\n".join(lines)


def _generate_markdown_report(
    track_metrics: TrackMetrics,
    track_score: TrackScore,
    timestamp: str
) -> str:
    """Generate markdown-formatted report."""
    config = get_track_config(track_score.track_id)

    lines = [
        f"# {track_score.track_name} Scoring Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Modules:** {track_metrics.modules_found}/{track_metrics.total_modules}",
        f"**Final Score:** {track_score.total_weighted_score:.2f}/10",
        "",
        "---",
        "",
        "## Automated Metrics",
        "",
        "| Metric | Total | Per Module Avg |",
        "|--------|-------|----------------|",
    ]

    n = track_metrics.modules_found if track_metrics.modules_found > 0 else 1
    metrics_data = [
        ("[!quote] callouts", track_metrics.total_quote_callouts, track_metrics.avg_quote_callouts),
        ("[!myth-buster] callouts", track_metrics.total_myth_buster_callouts, track_metrics.avg_myth_buster_callouts),
        ("Agency markers", track_metrics.total_agency_markers, track_metrics.total_agency_markers / n),
        ("Cross-references", track_metrics.total_cross_references, track_metrics.avg_cross_references),
        ("Activities coverage", track_metrics.modules_with_activities, f"{track_metrics.modules_with_activities}/{track_metrics.modules_found}"),
        ("Vocabulary coverage", track_metrics.modules_with_vocabulary, f"{track_metrics.modules_with_vocabulary}/{track_metrics.modules_found}"),
    ]

    for name, total, avg in metrics_data:
        if isinstance(avg, float):
            lines.append(f"| {name} | {total:,} | {avg:.2f} |")
        else:
            lines.append(f"| {name} | {total:,} | {avg} |")

    # Validation Tiers
    total = track_metrics.modules_found
    if total > 0:
        lines.extend([
            "",
            "## Validation Tiers",
            "",
            "| Tier | Count | % |",
            "|------|-------|---|",
            f"| Tier 1: Automated | {track_metrics.total_automated} | {track_metrics.total_automated/total*100:.1f}% |",
            f"| Tier 2: LLM Verified | {track_metrics.total_llm_verified} | {track_metrics.total_llm_verified/total*100:.1f}% |",
            f"| Tier 3: Gold Standard | {track_metrics.total_gold_standard} | {track_metrics.total_gold_standard/total*100:.1f}% |",
        ])

    lines.extend([
        "",
        "## Criteria Scores",
        "",
        "| Criterion | Weight | Score | Weighted |",
        "|-----------|--------|-------|----------|",
    ])

    for criterion_name, criterion_config in config['criteria'].items():
        name = criterion_config['name']
        weight = criterion_config['weight']
        score = track_score.final_criterion_scores.get(criterion_name, 0.0)
        weighted = track_score.weighted_contributions.get(criterion_name, 0.0)
        lines.append(f"| {name} | {weight:.0%} | {score:.1f}/10 | {weighted:.2f} |")

    lines.append(f"| **TOTAL** | 100% | — | **{track_score.total_weighted_score:.2f}/10** |")

    # Caps section
    lines.extend(["", "## Critical Caps", ""])
    if not track_score.caps_applied:
        lines.append("✅ No caps triggered")
    else:
        for cap in track_score.caps_applied:
            lines.append(f"- ⚠️ **{cap.cap_name}**: {cap.cap_reason}")

    # Gaps section
    lines.extend(["", "## Gaps to 10/10", ""])

    gaps = []
    for criterion_name, score in track_score.final_criterion_scores.items():
        if score < 9.0:
            criterion_config = config['criteria'].get(criterion_name, {})
            weight = criterion_config.get('weight', 0)
            name = criterion_config.get('name', criterion_name)
            fix = _get_fix_suggestion(criterion_name, track_metrics)
            gaps.append((name, score, fix))

    if not gaps:
        lines.append("✅ All criteria at 9+ (excellent)")
    else:
        for name, score, fix in gaps:
            lines.append(f"- **{name}** ({score:.1f}/10): {fix}")

    return "\n".join(lines)
