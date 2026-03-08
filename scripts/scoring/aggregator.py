"""
Aggregator for combining per-module metrics into track-level scores.

This module handles:
1. Aggregating individual module metrics into track totals
2. Calculating criterion scores based on metric values
3. Computing weighted final scores
"""

from dataclasses import dataclass, field

from .caps import apply_critical_caps
from .config import TrackConfig, get_track_config
from .metrics import ModuleMetrics


@dataclass
class TrackMetrics:
    """Aggregated metrics for an entire track."""
    track_id: str
    total_modules: int
    modules_found: int

    # Audit status
    passing_modules: int = 0
    failing_modules: int = 0
    unknown_modules: int = 0

    # Validation Tiers
    total_automated: int = 0
    total_llm_verified: int = 0
    total_gold_standard: int = 0

    # File coverage
    modules_with_md: int = 0
    modules_with_meta: int = 0
    modules_with_activities: int = 0
    modules_with_vocabulary: int = 0
    modules_with_status: int = 0

    # Callout totals
    total_quote_callouts: int = 0
    total_myth_buster_callouts: int = 0
    total_history_bite_callouts: int = 0
    total_analysis_callouts: int = 0
    total_context_callouts: int = 0
    total_resources_callouts: int = 0

    # Callout averages (calculated)
    avg_quote_callouts: float = 0.0
    avg_myth_buster_callouts: float = 0.0
    avg_analysis_callouts: float = 0.0

    # Agency metrics
    total_agency_markers: int = 0
    total_sentences: int = 0
    agency_marker_ratio: float = 0.0

    # Toponym metrics
    total_toponym_violations: int = 0
    total_ukrainian_toponyms: int = 0

    # Cross-references
    total_cross_references: int = 0
    avg_cross_references: float = 0.0

    # Literary metrics (for LIT track)
    avg_citation_ratio: float = 0.0
    total_stylistic_devices: int = 0
    total_analysis_sections: int = 0
    total_legacy_sections: int = 0

    # Vocabulary
    total_vocab_items: int = 0
    total_era_vocab_items: int = 0
    total_archaic_vocab_items: int = 0

    # Activity metrics
    total_activities: int = 0
    total_activity_items: int = 0
    total_critical_analysis_activities: int = 0
    total_reading_activities: int = 0
    total_essay_activities: int = 0

    # Word counts
    total_word_count: int = 0
    avg_word_count: float = 0.0

    # Naturalness (from status JSON)
    avg_naturalness_score: float = 0.0
    naturalness_scores: list[float] = field(default_factory=list)


def aggregate_track_metrics(
    module_metrics: list[ModuleMetrics],
    track_id: str
) -> TrackMetrics:
    """
    Aggregate per-module metrics into track totals.

    Args:
        module_metrics: List of ModuleMetrics from extract_all_module_metrics
        track_id: Track identifier

    Returns:
        TrackMetrics with all aggregated values
    """
    config = get_track_config(track_id)

    metrics = TrackMetrics(
        track_id=track_id,
        total_modules=config['module_count'],
        modules_found=len(module_metrics),
    )

    if not module_metrics:
        return metrics

    # Aggregate from each module
    citation_ratios = []
    word_counts = []

    for m in module_metrics:
        # Audit status
        if m.audit_status == 'pass':
            metrics.passing_modules += 1
        elif m.audit_status == 'fail':
            metrics.failing_modules += 1
        else:
            metrics.unknown_modules += 1

        # Validation Tiers
        if m.validation_tier == 'gold-standard':
            metrics.total_gold_standard += 1
        elif m.validation_tier == 'llm-verified':
            metrics.total_llm_verified += 1
        else:
            metrics.total_automated += 1

        # File coverage
        if m.md_exists:
            metrics.modules_with_md += 1
        if m.meta_exists:
            metrics.modules_with_meta += 1
        if m.activities_exists:
            metrics.modules_with_activities += 1
        if m.vocabulary_exists:
            metrics.modules_with_vocabulary += 1
        if m.status_exists:
            metrics.modules_with_status += 1

        # Callouts
        metrics.total_quote_callouts += m.quote_callouts
        metrics.total_myth_buster_callouts += m.myth_buster_callouts
        metrics.total_history_bite_callouts += m.history_bite_callouts
        metrics.total_analysis_callouts += m.analysis_callouts
        metrics.total_context_callouts += m.context_callouts
        metrics.total_resources_callouts += m.resources_callouts

        # Agency
        metrics.total_agency_markers += m.agency_markers
        metrics.total_sentences += m.total_sentences

        # Toponyms
        metrics.total_toponym_violations += m.toponym_violations
        metrics.total_ukrainian_toponyms += m.ukrainian_toponyms

        # Cross-references
        metrics.total_cross_references += m.cross_references

        # Literary metrics
        if m.citation_ratio > 0:
            citation_ratios.append(m.citation_ratio)
        metrics.total_stylistic_devices += m.stylistic_devices
        metrics.total_analysis_sections += m.analysis_sections
        metrics.total_legacy_sections += m.legacy_sections

        # Vocabulary
        metrics.total_vocab_items += m.vocab_items
        metrics.total_era_vocab_items += m.era_vocab_items
        metrics.total_archaic_vocab_items += m.archaic_vocab_items

        # Activities
        metrics.total_activities += m.activity_count
        metrics.total_activity_items += m.activity_items
        metrics.total_critical_analysis_activities += m.critical_analysis_activities
        metrics.total_reading_activities += m.reading_activities
        metrics.total_essay_activities += m.essay_activities

        # Word counts
        if m.word_count > 0:
            word_counts.append(m.word_count)
        metrics.total_word_count += m.word_count

        # Naturalness
        if m.naturalness_score is not None:
            metrics.naturalness_scores.append(m.naturalness_score)

    # Calculate averages
    n = len(module_metrics)
    if n > 0:
        metrics.avg_quote_callouts = metrics.total_quote_callouts / n
        metrics.avg_myth_buster_callouts = metrics.total_myth_buster_callouts / n
        metrics.avg_analysis_callouts = metrics.total_analysis_callouts / n
        metrics.avg_cross_references = metrics.total_cross_references / n

    if metrics.total_sentences > 0:
        metrics.agency_marker_ratio = metrics.total_agency_markers / metrics.total_sentences

    if citation_ratios:
        metrics.avg_citation_ratio = sum(citation_ratios) / len(citation_ratios)

    if word_counts:
        metrics.avg_word_count = sum(word_counts) / len(word_counts)

    if metrics.naturalness_scores:
        metrics.avg_naturalness_score = sum(metrics.naturalness_scores) / len(metrics.naturalness_scores)

    return metrics


def _score_audit_pass_rate(tm: TrackMetrics, total: int) -> float:
    rate = tm.passing_modules / total if total > 0 else 0
    return min(10.0, rate * 10.0)


def _score_activity_coverage(tm: TrackMetrics, total: int) -> float:
    rate = tm.modules_with_activities / total if total > 0 else 0
    return min(10.0, rate * 10.0)


def _score_vocabulary_coverage(tm: TrackMetrics, total: int) -> float:
    rate = tm.modules_with_vocabulary / total if total > 0 else 0
    return min(10.0, rate * 10.0)


def _score_internal_consistency(tm: TrackMetrics) -> float:
    avg = tm.avg_cross_references
    if avg >= 1.0:
        return 10.0
    elif avg >= 0.5:
        return 7.0
    elif avg >= 0.2:
        return 5.0
    elif avg > 0:
        return 3.0
    return 0.0


def _score_primary_source_integration(tm: TrackMetrics) -> float:
    avg = tm.avg_quote_callouts
    if avg >= 3.0:
        return 10.0
    elif avg >= 2.0:
        return 8.0
    elif avg >= 1.0:
        return 6.0
    elif avg >= 0.5:
        return 4.0
    elif avg > 0:
        return 2.0
    return 0.0


def _score_historical_accuracy(tm: TrackMetrics) -> float:
    if tm.avg_naturalness_score >= 9.0:
        return 10.0
    elif tm.avg_naturalness_score >= 8.0:
        return 9.0
    elif tm.avg_naturalness_score >= 7.0:
        return 8.0
    elif tm.avg_naturalness_score >= 6.0:
        return 7.0
    elif tm.avg_naturalness_score >= 5.0:
        return 6.0
    return 5.0


def _score_decolonization_perspective(tm: TrackMetrics) -> float:
    score = 0.0

    # Myth-busters (40% of score)
    avg_myth = tm.avg_myth_buster_callouts
    if avg_myth >= 2.0:
        score += 4.0
    elif avg_myth >= 1.0:
        score += 3.0
    elif avg_myth >= 0.5:
        score += 2.0
    elif avg_myth > 0:
        score += 1.0

    # Agency markers (40% of score)
    if tm.agency_marker_ratio >= 0.20:
        score += 4.0
    elif tm.agency_marker_ratio >= 0.15:
        score += 3.0
    elif tm.agency_marker_ratio >= 0.10:
        score += 2.0
    elif tm.agency_marker_ratio > 0:
        score += 1.0

    # Toponym compliance (20% of score)
    if tm.total_toponym_violations == 0:
        score += 2.0
    elif tm.total_toponym_violations <= 5:
        score += 1.0

    return min(10.0, score)


def _score_era_vocabulary(tm: TrackMetrics, total: int) -> float:
    if tm.modules_with_vocabulary == 0:
        return 0.0
    vocab_rate = tm.modules_with_vocabulary / total
    return min(10.0, vocab_rate * 10.0)


def _score_critical_analysis_skills(tm: TrackMetrics, total: int) -> float:
    if tm.total_critical_analysis_activities > 0:
        rate = tm.total_critical_analysis_activities / total
        return min(10.0, rate * 15 + 3.0)
    return 5.0


def _score_source_reliability(tm: TrackMetrics) -> float:
    avg = tm.avg_quote_callouts
    if avg >= 2.0:
        return 10.0
    elif avg >= 1.0:
        return 7.0
    elif avg > 0:
        return 4.0
    return 0.0


def _score_cultural_historical_context(tm: TrackMetrics, total: int) -> float:
    avg_context = tm.total_context_callouts / total if total > 0 else 0
    if avg_context >= 2.0:
        return 10.0
    elif avg_context >= 1.0:
        return 8.0
    elif avg_context >= 0.5:
        return 6.0
    elif avg_context > 0:
        return 4.0
    return 3.0


def _score_significance_assessment(tm: TrackMetrics, total: int) -> float:
    rate = tm.total_legacy_sections / total if total > 0 else 0
    if rate >= 0.8:
        return 10.0
    elif rate >= 0.5:
        return 8.0
    elif rate >= 0.3:
        return 6.0
    elif rate > 0:
        return 4.0
    return 0.0


def _score_literary_depth(tm: TrackMetrics, total: int) -> float:
    score = 0.0

    # Stylistic devices (50%)
    avg_devices = tm.total_stylistic_devices / total if total > 0 else 0
    if avg_devices >= 5:
        score += 5.0
    elif avg_devices >= 3:
        score += 4.0
    elif avg_devices >= 1:
        score += 2.5
    elif avg_devices > 0:
        score += 1.0

    # Analysis sections (50%)
    avg_sections = tm.total_analysis_sections / total if total > 0 else 0
    if avg_sections >= 3:
        score += 5.0
    elif avg_sections >= 2:
        score += 4.0
    elif avg_sections >= 1:
        score += 2.5
    elif avg_sections > 0:
        score += 1.0

    return min(10.0, score)


def _score_authentic_text_engagement(tm: TrackMetrics) -> float:
    ratio = tm.avg_citation_ratio
    if ratio >= 0.20:
        return 10.0
    elif ratio >= 0.15:
        return 9.0
    elif ratio >= 0.10:
        return 7.0
    elif ratio >= 0.05:
        return 5.0
    elif ratio > 0:
        return 3.0
    return 0.0


def _score_archaic_literary_vocab(tm: TrackMetrics) -> float:
    if tm.modules_with_vocabulary == 0:
        return 5.0
    rate = tm.total_archaic_vocab_items / max(1, tm.total_vocab_items)
    return min(10.0, 5.0 + rate * 50)


def _score_intertextual_links(tm: TrackMetrics) -> float:
    avg = tm.avg_cross_references
    if avg >= 1.0:
        return 10.0
    elif avg >= 0.5:
        return 7.0
    elif avg > 0:
        return 4.0
    return 0.0


def _score_skills_balance(tm: TrackMetrics) -> float:
    if tm.total_activities > 0:
        has_reading = tm.total_reading_activities > 0
        has_essay = tm.total_essay_activities > 0
        has_critical = tm.total_critical_analysis_activities > 0

        variety_score = 5.0
        if has_reading:
            variety_score += 1.5
        if has_essay:
            variety_score += 1.5
        if has_critical:
            variety_score += 2.0

        return min(10.0, variety_score)
    return 5.0


def _score_cefr_alignment(tm: TrackMetrics) -> float:
    if tm.avg_naturalness_score >= 8.0:
        return 10.0
    elif tm.avg_naturalness_score >= 6.0:
        return 8.0
    return 6.0


def _score_historiographical_methodology(tm: TrackMetrics, total: int) -> float:
    avg = tm.total_analysis_sections / total if total > 0 else 0
    if avg >= 2.0:
        return 10.0
    elif avg >= 1.0:
        return 7.0
    elif avg > 0:
        return 4.0
    return 2.0


def _score_source_criticism_skills(tm: TrackMetrics, total: int) -> float:
    if tm.total_critical_analysis_activities > 0:
        rate = tm.total_critical_analysis_activities / total
        return min(10.0, rate * 20 + 3.0)
    return 4.0


def _score_thematic_coherence(tm: TrackMetrics) -> float:
    avg = tm.avg_cross_references
    if avg >= 1.5:
        return 10.0
    elif avg >= 1.0:
        return 8.0
    elif avg >= 0.5:
        return 6.0
    elif avg > 0:
        return 4.0
    return 2.0


# Dispatch table: criterion_name -> scorer function
# Functions that need (tm, total) are wrapped with lambdas at call site.
_CRITERION_SCORERS: dict[str, object] = {
    # Universal
    'audit_pass_rate': _score_audit_pass_rate,
    'activity_coverage': _score_activity_coverage,
    'vocabulary_coverage': _score_vocabulary_coverage,
    'internal_consistency': _score_internal_consistency,
    # HIST
    'primary_source_integration': _score_primary_source_integration,
    'historical_accuracy': _score_historical_accuracy,
    'decolonization_perspective': _score_decolonization_perspective,
    'era_vocabulary': _score_era_vocabulary,
    'critical_analysis_skills': _score_critical_analysis_skills,
    # BIO
    'biographical_accuracy': _score_historical_accuracy,  # Same logic
    'source_reliability': _score_source_reliability,
    'cultural_historical_context': _score_cultural_historical_context,
    'significance_assessment': _score_significance_assessment,
    # LIT
    'literary_depth': _score_literary_depth,
    'authentic_text_engagement': _score_authentic_text_engagement,
    'archaic_literary_vocab': _score_archaic_literary_vocab,
    'intertextual_links': _score_intertextual_links,
    # Standard
    'grammar_content_coverage': _score_audit_pass_rate,  # Same logic
    'skills_balance': _score_skills_balance,
    'cefr_alignment': _score_cefr_alignment,
    # ISTORIO
    'historiographical_methodology': _score_historiographical_methodology,
    'source_criticism_skills': _score_source_criticism_skills,
    'thematic_coherence': _score_thematic_coherence,
}

# Criteria that only need TrackMetrics (no total)
_NO_TOTAL_CRITERIA = {
    'internal_consistency', 'primary_source_integration', 'historical_accuracy',
    'decolonization_perspective', 'biographical_accuracy', 'source_reliability',
    'authentic_text_engagement', 'archaic_literary_vocab', 'intertextual_links',
    'skills_balance', 'cefr_alignment', 'thematic_coherence',
}


def calculate_criterion_score(
    criterion_name: str,
    track_metrics: TrackMetrics,
    config: TrackConfig
) -> float:
    """
    Calculate score (0-10) for a single criterion.

    Args:
        criterion_name: Name of the criterion
        track_metrics: Aggregated track metrics
        config: Track configuration

    Returns:
        Score from 0.0 to 10.0
    """
    total = track_metrics.modules_found
    if total == 0:
        return 0.0

    # Static defaults
    if criterion_name in ('checkpoint_structure', 'state_standard_compliance'):
        return 8.0
    if criterion_name == 'chronological_coherence':
        return 9.0

    scorer = _CRITERION_SCORERS.get(criterion_name)
    if scorer is None:
        return 5.0

    if criterion_name in _NO_TOTAL_CRITERIA:
        return scorer(track_metrics)
    return scorer(track_metrics, total)


@dataclass
class TrackScore:
    """Complete scoring result for a track."""
    track_id: str
    track_name: str

    # Raw criterion scores (before caps)
    raw_criterion_scores: dict[str, float] = field(default_factory=dict)

    # Final criterion scores (after caps)
    final_criterion_scores: dict[str, float] = field(default_factory=dict)

    # Weighted contributions
    weighted_contributions: dict[str, float] = field(default_factory=dict)

    # Cap information
    caps_applied: list = field(default_factory=list)

    # Final scores
    total_weighted_score: float = 0.0  # Out of 10.0


def calculate_track_score(
    track_metrics: TrackMetrics,
    track_id: str
) -> TrackScore:
    """
    Calculate complete track score from aggregated metrics.

    This is the main scoring function that:
    1. Calculates scores for each criterion
    2. Applies critical failure caps
    3. Computes weighted final score

    Args:
        track_metrics: Aggregated metrics from aggregate_track_metrics
        track_id: Track identifier

    Returns:
        TrackScore with all scoring details
    """
    config = get_track_config(track_id)

    result = TrackScore(
        track_id=track_id,
        track_name=config['name'],
    )

    # Calculate raw scores for each criterion
    for criterion_name, _criterion_config in config['criteria'].items():
        score = calculate_criterion_score(criterion_name, track_metrics, config)
        result.raw_criterion_scores[criterion_name] = score

    # Convert track metrics to dict for cap checking
    metrics_dict = {
        'total_quote_callouts': track_metrics.total_quote_callouts,
        'total_myth_buster_callouts': track_metrics.total_myth_buster_callouts,
        'total_cross_references': track_metrics.total_cross_references,
        'total_analysis_sections': track_metrics.total_analysis_sections,
        'total_legacy_sections': track_metrics.total_legacy_sections,
        'agency_marker_ratio': track_metrics.agency_marker_ratio,
        'avg_citation_ratio': track_metrics.avg_citation_ratio,
    }

    # Apply critical failure caps
    final_scores, cap_results = apply_critical_caps(
        track_id,
        metrics_dict,
        result.raw_criterion_scores
    )

    result.final_criterion_scores = final_scores
    result.caps_applied = [c for c in cap_results if c.cap_applied]

    # Calculate weighted score
    total_weighted = 0.0
    for criterion_name, criterion_config in config['criteria'].items():
        score = final_scores.get(criterion_name, 0.0)
        weight = criterion_config['weight']
        contribution = score * weight
        result.weighted_contributions[criterion_name] = contribution
        total_weighted += contribution

    result.total_weighted_score = total_weighted

    return result
