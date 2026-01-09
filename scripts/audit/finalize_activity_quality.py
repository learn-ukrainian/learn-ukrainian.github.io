#!/usr/bin/env python3
"""
Finalize activity quality validation and generate reports.

This script:
1. Reads completed quality queue files (with manual validation)
2. Calculates quality scores per dimension
3. Evaluates CEFR-specific quality gates
4. Generates audit reports

Usage:
    python scripts/audit/finalize_activity_quality.py l2-uk-en b1 52
    python scripts/audit/finalize_activity_quality.py l2-uk-en b2 75
"""

import argparse
import sys
from pathlib import Path
import yaml
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# CEFR-Specific Quality Gates
QUALITY_GATES = {
    'A1': {
        'min_naturalness_avg': None,  # No strict gates (scaffolding phase)
        'max_difficulty_inappropriate': None,
        'min_engagement_avg': None,
        'min_distractor_quality': None,
        'min_variety_avg': None,
    },
    'A2': {
        'min_naturalness_avg': None,  # No strict gates (scaffolding phase)
        'max_difficulty_inappropriate': None,
        'min_engagement_avg': None,
        'min_distractor_quality': None,
        'min_variety_avg': None,
    },
    'B1': {
        'min_naturalness_avg': 3.5,  # Acceptable+
        'max_difficulty_inappropriate': 0.20,  # ≤20% of activities
        'min_engagement_avg': 3.0,  # Neutral+
        'min_distractor_quality': 4.0,  # Good
        'min_variety_avg': 60,  # 60% variety score
    },
    'B2': {
        'min_naturalness_avg': 4.0,  # Natural
        'max_difficulty_inappropriate': 0.15,  # ≤15%
        'min_engagement_avg': 3.5,  # Neutral to Engaging
        'min_distractor_quality': 4.2,  # Good+
        'min_variety_avg': 65,  # 65% variety score
    },
    'C1': {
        'min_naturalness_avg': 4.5,  # Highly Natural
        'max_difficulty_inappropriate': 0.10,  # ≤10%
        'min_engagement_avg': 4.0,  # Engaging
        'min_distractor_quality': 4.5,  # Good to Excellent
        'min_variety_avg': 70,  # 70% variety score
    },
    'C2': {
        'min_naturalness_avg': 4.8,  # Near-Native
        'max_difficulty_inappropriate': 0.05,  # ≤5%
        'min_engagement_avg': 4.5,  # Highly Engaging
        'min_distractor_quality': 5.0,  # Excellent
        'min_variety_avg': 75,  # 75% variety score
    },
}


def calculate_quality_scores(queue_data: Dict) -> Dict[str, Any]:
    """
    Calculate aggregate quality scores from queue data.

    Returns:
        Dict with quality scores and statistics
    """
    activities = queue_data.get('activities', [])

    if not activities:
        return {
            'total_activities': 0,
            'error': 'No activities found'
        }

    # Collect scores
    naturalness_scores = []
    engagement_scores = []
    distractor_scores = []
    variety_scores = []
    difficulty_assessments = []

    incomplete_activities = []

    for activity in activities:
        activity_id = activity.get('activity_id', 'unknown')

        # Manual validation fields
        naturalness = activity.get('naturalness')
        engagement = activity.get('engagement')
        distractor_score = activity.get('distractor_score')
        variety_score = activity.get('variety_score')
        difficulty = activity.get('difficulty')

        # Check if manual validation is complete
        if naturalness is None or engagement is None or difficulty is None:
            incomplete_activities.append(activity_id)
            continue

        naturalness_scores.append(naturalness)
        engagement_scores.append(engagement)
        difficulty_assessments.append(difficulty)

        # Distractor and variety scores are optional (some activities don't have them)
        if distractor_score is not None:
            distractor_scores.append(distractor_score)
        if variety_score is not None:
            variety_scores.append(variety_score)

    # Calculate averages
    naturalness_avg = sum(naturalness_scores) / len(naturalness_scores) if naturalness_scores else None
    engagement_avg = sum(engagement_scores) / len(engagement_scores) if engagement_scores else None
    distractor_avg = sum(distractor_scores) / len(distractor_scores) if distractor_scores else None
    variety_avg = sum(variety_scores) / len(variety_scores) if variety_scores else None

    # Calculate difficulty appropriateness
    total_activities_validated = len(difficulty_assessments)
    inappropriate_difficulty = sum(1 for d in difficulty_assessments if d != 'appropriate')
    difficulty_inappropriate_pct = inappropriate_difficulty / total_activities_validated if total_activities_validated > 0 else None

    return {
        'total_activities': len(activities),
        'validated_activities': total_activities_validated,
        'incomplete_activities': incomplete_activities,
        'naturalness_avg': naturalness_avg,
        'engagement_avg': engagement_avg,
        'distractor_quality_avg': distractor_avg,
        'variety_avg': variety_avg,
        'difficulty_appropriate_pct': 1 - difficulty_inappropriate_pct if difficulty_inappropriate_pct is not None else None,
        'difficulty_inappropriate_pct': difficulty_inappropriate_pct,
        'difficulty_breakdown': {
            'too_easy': sum(1 for d in difficulty_assessments if d == 'too_easy'),
            'appropriate': sum(1 for d in difficulty_assessments if d == 'appropriate'),
            'too_hard': sum(1 for d in difficulty_assessments if d == 'too_hard'),
        }
    }


def evaluate_quality_gates(
    quality_scores: Dict,
    level: str
) -> Dict[str, Any]:
    """
    Evaluate quality scores against CEFR gates.

    Returns:
        Dict with gate evaluation results
    """
    gates = QUALITY_GATES.get(level.upper(), {})

    # If no gates (A1/A2), pass by default
    if all(v is None for v in gates.values()):
        return {
            'result': 'PASS',
            'message': f'{level} has no strict quality gates (scaffolding phase)',
            'failed_gates': []
        }

    failed_gates = []

    # Check each gate
    if gates.get('min_naturalness_avg') and quality_scores.get('naturalness_avg'):
        if quality_scores['naturalness_avg'] < gates['min_naturalness_avg']:
            failed_gates.append({
                'dimension': 'naturalness',
                'required': gates['min_naturalness_avg'],
                'actual': quality_scores['naturalness_avg'],
                'message': f"Naturalness {quality_scores['naturalness_avg']:.1f} < {gates['min_naturalness_avg']}"
            })

    if gates.get('max_difficulty_inappropriate') and quality_scores.get('difficulty_inappropriate_pct'):
        if quality_scores['difficulty_inappropriate_pct'] > gates['max_difficulty_inappropriate']:
            failed_gates.append({
                'dimension': 'difficulty',
                'required': f"≤{gates['max_difficulty_inappropriate'] * 100:.0f}%",
                'actual': f"{quality_scores['difficulty_inappropriate_pct'] * 100:.0f}%",
                'message': f"Inappropriate difficulty {quality_scores['difficulty_inappropriate_pct']:.0%} > {gates['max_difficulty_inappropriate']:.0%}"
            })

    if gates.get('min_engagement_avg') and quality_scores.get('engagement_avg'):
        if quality_scores['engagement_avg'] < gates['min_engagement_avg']:
            failed_gates.append({
                'dimension': 'engagement',
                'required': gates['min_engagement_avg'],
                'actual': quality_scores['engagement_avg'],
                'message': f"Engagement {quality_scores['engagement_avg']:.1f} < {gates['min_engagement_avg']}"
            })

    if gates.get('min_distractor_quality') and quality_scores.get('distractor_quality_avg'):
        if quality_scores['distractor_quality_avg'] < gates['min_distractor_quality']:
            failed_gates.append({
                'dimension': 'distractor_quality',
                'required': gates['min_distractor_quality'],
                'actual': quality_scores['distractor_quality_avg'],
                'message': f"Distractor quality {quality_scores['distractor_quality_avg']:.1f} < {gates['min_distractor_quality']}"
            })

    if gates.get('min_variety_avg') and quality_scores.get('variety_avg'):
        if quality_scores['variety_avg'] < gates['min_variety_avg']:
            failed_gates.append({
                'dimension': 'variety',
                'required': f"{gates['min_variety_avg']}%",
                'actual': f"{quality_scores['variety_avg']:.0f}%",
                'message': f"Variety {quality_scores['variety_avg']:.0f}% < {gates['min_variety_avg']}%"
            })

    result = 'PASS' if len(failed_gates) == 0 else 'FAIL'

    return {
        'result': result,
        'failed_gates': failed_gates,
        'gates_checked': len([v for v in gates.values() if v is not None])
    }


def generate_report(
    queue_data: Dict,
    quality_scores: Dict,
    gate_evaluation: Dict
) -> str:
    """
    Generate markdown audit report.
    """
    module = queue_data.get('module', 'unknown')
    level = queue_data.get('level', 'unknown')
    module_number = queue_data.get('module_number', 0)

    # Pre-compute formatted values to avoid f-string complexity
    naturalness_score = f"{quality_scores.get('naturalness_avg'):.1f}" if quality_scores.get('naturalness_avg') else 'N/A'
    engagement_score = f"{quality_scores.get('engagement_avg'):.1f}" if quality_scores.get('engagement_avg') else 'N/A'
    distractor_score = f"{quality_scores.get('distractor_quality_avg'):.1f}" if quality_scores.get('distractor_quality_avg') else 'N/A'
    variety_score = f"{quality_scores.get('variety_avg'):.0f}%" if quality_scores.get('variety_avg') else 'N/A'
    difficulty_score = f"{quality_scores.get('difficulty_appropriate_pct'):.0%}" if quality_scores.get('difficulty_appropriate_pct') is not None else 'N/A'

    naturalness_gate = QUALITY_GATES[level]['min_naturalness_avg'] if QUALITY_GATES[level]['min_naturalness_avg'] else 'N/A'
    engagement_gate = QUALITY_GATES[level]['min_engagement_avg'] if QUALITY_GATES[level]['min_engagement_avg'] else 'N/A'
    distractor_gate = QUALITY_GATES[level]['min_distractor_quality'] if QUALITY_GATES[level]['min_distractor_quality'] else 'N/A'
    variety_gate = f"{QUALITY_GATES[level]['min_variety_avg']}%" if QUALITY_GATES[level]['min_variety_avg'] else 'N/A'
    difficulty_gate = f"≥{int((1 - QUALITY_GATES[level]['max_difficulty_inappropriate']) * 100)}%" if QUALITY_GATES[level]['max_difficulty_inappropriate'] else 'N/A'

    naturalness_status = '✅' if not any(g['dimension'] == 'naturalness' for g in gate_evaluation['failed_gates']) else '❌'
    engagement_status = '✅' if not any(g['dimension'] == 'engagement' for g in gate_evaluation['failed_gates']) else '❌'
    distractor_status = '✅' if not any(g['dimension'] == 'distractor_quality' for g in gate_evaluation['failed_gates']) else '❌'
    variety_status = '✅' if not any(g['dimension'] == 'variety' for g in gate_evaluation['failed_gates']) else '❌'
    difficulty_status = '✅' if not any(g['dimension'] == 'difficulty' for g in gate_evaluation['failed_gates']) else '❌'

    report = f"""# Activity Quality Audit Report

**Module:** {module}
**Level:** {level}
**Module Number:** {module_number}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Quality Gate Evaluation

**Result:** {'✅ PASS' if gate_evaluation['result'] == 'PASS' else '❌ FAIL'}

"""

    if gate_evaluation['result'] == 'FAIL':
        report += "### Failed Gates\n\n"
        for gate in gate_evaluation['failed_gates']:
            report += f"- **{gate['dimension']}:** {gate['message']}\n"
        report += "\n"

    report += f"""
## Quality Scores Summary

| Dimension | Score | {level} Gate | Status |
|-----------|-------|-------------|--------|
| **Naturalness** | {naturalness_score} | {naturalness_gate} | {naturalness_status} |
| **Engagement** | {engagement_score} | {engagement_gate} | {engagement_status} |
| **Distractor Quality** | {distractor_score} | {distractor_gate} | {distractor_status} |
| **Variety** | {variety_score} | {variety_gate} | {variety_status} |
| **Difficulty Appropriate** | {difficulty_score} | {difficulty_gate} | {difficulty_status} |

"""

    # Difficulty breakdown
    if quality_scores.get('difficulty_breakdown'):
        breakdown = quality_scores['difficulty_breakdown']
        report += f"""
### Difficulty Breakdown

- **Too Easy:** {breakdown.get('too_easy', 0)} activities
- **Appropriate:** {breakdown.get('appropriate', 0)} activities
- **Too Hard:** {breakdown.get('too_hard', 0)} activities

"""

    # Incomplete activities
    if quality_scores.get('incomplete_activities'):
        report += "### ⚠️ Incomplete Validation\n\n"
        report += f"{len(quality_scores['incomplete_activities'])} activities not fully validated:\n\n"
        for activity_id in quality_scores['incomplete_activities']:
            report += f"- `{activity_id}`\n"
        report += "\n"

    # Recommendations
    report += "## Recommendations\n\n"

    if gate_evaluation['result'] == 'FAIL':
        report += "### Required Actions\n\n"
        for gate in gate_evaluation['failed_gates']:
            if gate['dimension'] == 'naturalness':
                report += f"- **Improve Naturalness:** Rewrite activities with robotic/translated phrasing (scores 1-2)\n"
            elif gate['dimension'] == 'difficulty':
                report += f"- **Fix Difficulty:** Adjust activities that are too easy or too hard for {level}\n"
            elif gate['dimension'] == 'engagement':
                report += f"- **Increase Engagement:** Add cultural references, contemporary topics, or interesting contexts\n"
            elif gate['dimension'] == 'distractor_quality':
                report += f"- **Improve Distractors:** Ensure options target common errors and are plausible\n"
            elif gate['dimension'] == 'variety':
                report += f"- **Add Variety:** Reduce mechanical repetition in sentence structures\n"
        report += "\n"

    report += """
---

**Next Steps:**
1. Address failed quality gates (if any)
2. Rerun quality validation to confirm fixes
3. Proceed with module generation
"""

    return report


def finalize_quality(
    content_root: Path,
    level: str,
    module_num: int
) -> None:
    """
    Finalize quality validation for a module.
    """
    level_dir = content_root / level

    # Find queue file
    queue_files = list((level_dir / 'queue').glob(f'{module_num:02d}-*-quality.yaml'))
    if not queue_files:
        # Try without zero-padding
        queue_files = list((level_dir / 'queue').glob(f'{module_num}-*-quality.yaml'))

    if not queue_files:
        print(f"⚠️  No quality queue file found for {level.upper()} module {module_num}")
        return

    queue_file = queue_files[0]
    module_slug = queue_file.stem.replace('-quality', '')

    print(f"📄 Finalizing: {queue_file.name}")

    # Load queue
    with open(queue_file, 'r', encoding='utf-8') as f:
        queue_data = yaml.safe_load(f)

    # Calculate scores
    quality_scores = calculate_quality_scores(queue_data)

    if quality_scores.get('error'):
        print(f"❌ Error: {quality_scores['error']}")
        return

    if quality_scores.get('incomplete_activities'):
        print(f"⚠️  Warning: {len(quality_scores['incomplete_activities'])} activities not fully validated")

    # Evaluate gates
    gate_evaluation = evaluate_quality_gates(quality_scores, level)

    # Generate report
    report = generate_report(queue_data, quality_scores, gate_evaluation)

    # Write report
    audit_dir = level_dir / 'audit'
    audit_dir.mkdir(exist_ok=True)
    report_file = audit_dir / f'{module_slug}-quality.md'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Generated: {report_file.relative_to(content_root)}")
    print(f"\n{'✅ PASS' if gate_evaluation['result'] == 'PASS' else '❌ FAIL'}")

    if gate_evaluation['result'] == 'FAIL':
        print(f"   Failed {len(gate_evaluation['failed_gates'])} gates:")
        for gate in gate_evaluation['failed_gates']:
            print(f"   - {gate['dimension']}: {gate['message']}")


def main():
    parser = argparse.ArgumentParser(
        description='Finalize activity quality validation and generate reports'
    )
    parser.add_argument('content', help='Content identifier (e.g., l2-uk-en)')
    parser.add_argument('level', help='Level (a1, a2, b1, b2, c1, c2)')
    parser.add_argument('module', type=int, help='Module number')

    args = parser.parse_args()

    # Resolve paths
    repo_root = Path(__file__).parent.parent.parent
    content_root = repo_root / 'curriculum' / args.content

    if not content_root.exists():
        print(f"❌ Content directory not found: {content_root}")
        sys.exit(1)

    level = args.level.lower()
    level_dir = content_root / level

    if not level_dir.exists():
        print(f"❌ Level directory not found: {level_dir}")
        sys.exit(1)

    print(f"🔍 Finalizing quality validation for {args.content}/{level}/{args.module}")
    print()

    finalize_quality(content_root, level, args.module)


if __name__ == '__main__':
    main()
