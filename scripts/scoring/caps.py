"""
Critical failure cap logic for track scoring.

Certain metric thresholds cap maximum scores regardless of other criteria.
This ensures that fundamental issues (like missing primary sources in HIST tracks)
cannot be hidden by high scores in other areas.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CapResult:
    """Result of applying a critical cap."""
    cap_applied: bool
    original_score: float
    capped_score: float
    cap_name: str
    cap_reason: str
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None


@dataclass
class CapCondition:
    """Definition of a critical cap condition."""
    name: str
    criterion: str  # Which criterion this caps
    max_score: float  # Maximum score if condition is met
    metric_name: str  # Which metric to check
    threshold: float  # Threshold value (condition met if metric <= threshold)
    reason_template: str  # Template for reason message


# =============================================================================
# CRITICAL CAP DEFINITIONS
# =============================================================================

# Caps that apply to specific tracks
CRITICAL_CAPS: dict[str, list[CapCondition]] = {
    'b2-hist': [
        CapCondition(
            name='zero_myth_busters',
            criterion='decolonization_perspective',
            max_score=4.0,
            metric_name='total_myth_buster_callouts',
            threshold=0,
            reason_template='0 [!myth-buster] callouts: cannot score high without active myth-busting',
        ),
        CapCondition(
            name='zero_quotes',
            criterion='primary_source_integration',
            max_score=3.0,
            metric_name='total_quote_callouts',
            threshold=0,
            reason_template='0 [!quote] blocks: no primary source integration',
        ),
        CapCondition(
            name='low_agency',
            criterion='decolonization_perspective',
            max_score=6.0,
            metric_name='agency_marker_ratio',
            threshold=0.10,
            reason_template='Agency marker ratio {actual:.1%} < 10%: passive/external framing of Ukrainian history',
        ),
        CapCondition(
            name='zero_cross_references',
            criterion='internal_consistency',
            max_score=5.0,
            metric_name='total_cross_references',
            threshold=0,
            reason_template='0 cross-references: no module connections',
        ),
    ],
    'c1-hist': [
        CapCondition(
            name='zero_quotes',
            criterion='primary_source_integration',
            max_score=3.0,
            metric_name='total_quote_callouts',
            threshold=0,
            reason_template='0 [!quote] blocks: no primary source integration',
        ),
        CapCondition(
            name='zero_cross_references',
            criterion='internal_consistency',
            max_score=5.0,
            metric_name='total_cross_references',
            threshold=0,
            reason_template='0 cross-references: no thematic connections',
        ),
    ],
    'c1-bio': [
        CapCondition(
            name='zero_quotes',
            criterion='source_reliability',
            max_score=4.0,
            metric_name='total_quote_callouts',
            threshold=0,
            reason_template='0 direct quotes: no engagement with subject\'s own words',
        ),
        CapCondition(
            name='no_legacy',
            criterion='significance_assessment',
            max_score=6.0,
            metric_name='total_legacy_sections',
            threshold=0,
            reason_template='0 legacy/impact sections: no significance assessment',
        ),
        CapCondition(
            name='zero_cross_references',
            criterion='internal_consistency',
            max_score=5.0,
            metric_name='total_cross_references',
            threshold=0,
            reason_template='0 cross-references: no connections between biographies',
        ),
    ],
    'lit': [
        CapCondition(
            name='no_analysis',
            criterion='literary_depth',
            max_score=5.0,
            metric_name='total_analysis_sections',
            threshold=0,
            reason_template='0 analysis sections: no literary analysis',
        ),
        CapCondition(
            name='low_citation',
            criterion='authentic_text_engagement',
            max_score=5.0,
            metric_name='avg_citation_ratio',
            threshold=0.05,
            reason_template='Citation ratio {actual:.1%} < 5%: too little direct text engagement',
        ),
        CapCondition(
            name='zero_cross_references',
            criterion='internal_consistency',
            max_score=5.0,
            metric_name='total_cross_references',
            threshold=0,
            reason_template='0 cross-references: no intertextual connections',
        ),
    ],
    'standard': [
        CapCondition(
            name='zero_cross_references',
            criterion='internal_consistency',
            max_score=5.0,
            metric_name='total_cross_references',
            threshold=0,
            reason_template='0 cross-references: no module connections',
        ),
    ],
}


def get_caps_for_track(track_id: str) -> list[CapCondition]:
    """
    Get critical cap conditions for a track.

    Args:
        track_id: Track identifier

    Returns:
        List of CapCondition objects for the track
    """
    # Check if it's a specialized track
    if track_id in CRITICAL_CAPS:
        return CRITICAL_CAPS[track_id]

    # Check if it's a standard track variant
    standard_tracks = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    if track_id in standard_tracks:
        return CRITICAL_CAPS.get('standard', [])

    return []


def apply_critical_caps(
    track_id: str,
    aggregated_metrics: dict,
    criterion_scores: dict[str, float]
) -> tuple[dict[str, float], list[CapResult]]:
    """
    Apply critical failure caps to criterion scores.

    Args:
        track_id: Track identifier
        aggregated_metrics: Dictionary of aggregated track metrics
        criterion_scores: Dictionary of criterion -> score (0-10)

    Returns:
        Tuple of (updated_scores, list_of_cap_results)
    """
    caps = get_caps_for_track(track_id)
    updated_scores = criterion_scores.copy()
    cap_results = []

    for cap in caps:
        # Get the metric value
        metric_value = aggregated_metrics.get(cap.metric_name, 0)

        # Check if cap condition is met
        if metric_value <= cap.threshold:
            criterion = cap.criterion
            original_score = criterion_scores.get(criterion, 10.0)

            # Apply cap only if it would actually lower the score
            if original_score > cap.max_score:
                updated_scores[criterion] = cap.max_score

                # Format the reason
                reason = cap.reason_template
                if '{actual' in reason:
                    reason = reason.format(actual=metric_value)

                cap_results.append(CapResult(
                    cap_applied=True,
                    original_score=original_score,
                    capped_score=cap.max_score,
                    cap_name=cap.name,
                    cap_reason=reason,
                    threshold_value=cap.threshold,
                    actual_value=metric_value,
                ))
            else:
                # Cap not needed - score already at or below cap
                cap_results.append(CapResult(
                    cap_applied=False,
                    original_score=original_score,
                    capped_score=original_score,
                    cap_name=cap.name,
                    cap_reason=f"Score {original_score:.1f} already ≤ cap {cap.max_score:.1f}",
                    threshold_value=cap.threshold,
                    actual_value=metric_value,
                ))

    return updated_scores, cap_results


def check_cap_violations(
    track_id: str,
    aggregated_metrics: dict
) -> list[dict]:
    """
    Check which caps would be triggered by current metrics.

    Useful for gap analysis to identify what needs improvement.

    Args:
        track_id: Track identifier
        aggregated_metrics: Dictionary of aggregated track metrics

    Returns:
        List of cap violation details
    """
    caps = get_caps_for_track(track_id)
    violations = []

    for cap in caps:
        metric_value = aggregated_metrics.get(cap.metric_name, 0)

        if metric_value <= cap.threshold:
            reason = cap.reason_template
            if '{actual' in reason:
                reason = reason.format(actual=metric_value)

            violations.append({
                'cap_name': cap.name,
                'criterion': cap.criterion,
                'max_score': cap.max_score,
                'metric': cap.metric_name,
                'current_value': metric_value,
                'threshold': cap.threshold,
                'reason': reason,
            })

    return violations
