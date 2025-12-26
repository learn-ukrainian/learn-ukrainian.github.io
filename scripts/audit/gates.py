"""
Gate evaluation logic for module auditing.

Evaluates various quality gates (word count, activities, density, etc.)
and computes recommendations based on violations.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GateResult:
    """Result of a gate evaluation."""
    status: str  # 'PASS', 'FAIL', 'WARN', 'INFO'
    icon: str
    msg: str


def evaluate_word_count(total_words: int, target: int) -> GateResult:
    """Evaluate word count gate."""
    max_words = target + 1000  # Allow up to 1000 words over target for rich content
    if total_words >= target:
        if total_words > max_words:
            return GateResult('WARN', '⚠️', f"{total_words}/{target} (>{max_words} may be too long)")
        return GateResult('PASS', '✅', f"{total_words}/{target}")
    return GateResult('FAIL', '❌', f"{total_words}/{target}")


def evaluate_activity_count(count: int, target: int) -> GateResult:
    """Evaluate activity count gate."""
    if count >= target:
        return GateResult('PASS', '✅', f"{count}/{target}")
    return GateResult('FAIL', '❌', f"{count}/{target}")


def evaluate_density(failed_count: int, total: int, threshold: int, act_target: int) -> GateResult:
    """Evaluate activity density gate."""
    if (failed_count == 0 and total > 0) or (act_target == 0 and total == 0):
        return GateResult('PASS', '✅', f"All > {threshold}")
    return GateResult('FAIL', '❌', f"{failed_count} < {threshold}")


def evaluate_unique_types(unique_count: int, target: int) -> GateResult:
    """Evaluate unique activity types gate."""
    if unique_count >= target:
        return GateResult('PASS', '✅', f"{unique_count}/{target} types")
    return GateResult('FAIL', '❌', f"{unique_count}/{target} types")


def evaluate_priority_types(unique_types: set, priority_types: set) -> GateResult:
    """Evaluate priority activity types gate."""
    if not priority_types:
        return GateResult('PASS', '✅', "N/A (LIT)")
    if unique_types.intersection(priority_types):
        return GateResult('PASS', '✅', "Priority types used")
    return GateResult('FAIL', '❌', "No priority types")


def evaluate_engagement(count: int, target: int) -> GateResult:
    """Evaluate engagement boxes gate."""
    if count >= target:
        return GateResult('PASS', '✅', f"{count}/{target}")
    return GateResult('FAIL', '❌', f"{count}/{target}")


def evaluate_audio(count: int) -> GateResult:
    """Evaluate audio links (informational only)."""
    if count > 0:
        return GateResult('INFO', '✅', f"{count} links")
    return GateResult('INFO', 'ℹ️', "No audio")


def evaluate_vocab(count: int, target: int) -> GateResult:
    """Evaluate vocabulary count gate."""
    if count >= target:
        return GateResult('PASS', '✅', f"{count}/{target}")
    return GateResult('FAIL', '❌', f"{count} < {target}")


def evaluate_structure(has_summary: bool, has_vocab: bool, has_vocab_table: bool) -> GateResult:
    """Evaluate structure gate."""
    if not has_summary:
        return GateResult('FAIL', '❌', "Missing '## Summary'")
    if not has_vocab:
        return GateResult('FAIL', '❌', "Missing '## Vocabulary'")
    if not has_vocab_table:
        return GateResult('FAIL', '❌', "Missing Vocab Table")
    return GateResult('PASS', '✅', "Valid Structure")


def evaluate_lint(error_count: int) -> GateResult:
    """Evaluate lint errors gate."""
    if error_count == 0:
        return GateResult('PASS', '✅', "Clean Format")
    return GateResult('FAIL', '❌', f"{error_count} Format Errors")


def evaluate_pedagogy(violation_count: int) -> GateResult:
    """Evaluate pedagogical violations gate."""
    if violation_count == 0:
        return GateResult('PASS', '✅', "Level-appropriate")
    return GateResult('FAIL', '❌', f"{violation_count} violations")


def evaluate_richness(
    score: int,
    threshold: int,
    module_type: str,
    flags: list
) -> GateResult:
    """Evaluate richness score gate."""
    if score >= threshold:
        if flags:
            return GateResult('WARN', '⚠️', f"{score}/{threshold} ({module_type}) - {len(flags)} flags")
        return GateResult('PASS', '✅', f"{score}/{threshold} ({module_type})")
    if len(flags) >= 2:
        return GateResult('FAIL', '❌', f"{score}/{threshold} ({module_type}) - REWRITE needed")
    return GateResult('FAIL', '❌', f"{score}/{threshold} ({module_type})")


def evaluate_immersion(
    score: float,
    min_imm: int,
    max_imm: int,
    phase_label: str = ""
) -> GateResult:
    """Evaluate immersion gate."""
    if min_imm > 0:
        if score < min_imm:
            return GateResult(
                'FAIL', '❌',
                f"{score:.1f}% LOW (target {min_imm}-{max_imm}%{phase_label})"
            )
        elif score > max_imm:
            return GateResult(
                'FAIL', '❌',
                f"{score:.1f}% HIGH (target {min_imm}-{max_imm}%{phase_label})"
            )
        return GateResult(
            'PASS', '🇺🇦',
            f"{score:.1f}% (target {min_imm}-{max_imm}%{phase_label})"
        )
    return GateResult('PASS', '🇺🇦', f"{score:.1f}%{phase_label}")


def compute_recommendation(
    pedagogical_violations: list,
    lint_errors: list,
    results: dict,
    immersion_score: float,
    min_imm: int,
    max_imm: int,
    level_code: str
) -> tuple[str, list[str], int]:
    """
    Analyze violations and recommend UPDATE vs REWRITE.

    Returns:
        tuple: (recommendation, reasoning_list, severity_score)
    """
    severity = 0
    reasons = []

    # 1. Pedagogical violations
    ped_count = len(pedagogical_violations)
    if ped_count == 0:
        pass
    elif ped_count <= 3:
        severity += 10
        reasons.append(f"{ped_count} pedagogical violations (minor)")
    elif ped_count <= 6:
        severity += 25
        reasons.append(f"{ped_count} pedagogical violations (moderate)")
    elif ped_count <= 10:
        severity += 45
        reasons.append(f"{ped_count} pedagogical violations (significant)")
    else:
        severity += 60
        reasons.append(f"{ped_count} pedagogical violations (severe - consider rewrite)")

    # 2. Violation types (some are worse than others)
    violation_types = [v.get('type', '') for v in pedagogical_violations]

    grammar_viols = sum(1 for t in violation_types if t == 'GRAMMAR')
    if grammar_viols >= 3:
        severity += 15
        reasons.append(f"{grammar_viols} grammar-level violations (fundamental)")

    activity_viols = sum(
        1 for t in violation_types
        if t in ('ACTIVITY_MISUSE', 'LEVEL_RESTRICTION', 'FOCUS_MISMATCH')
    )
    if activity_viols >= 3:
        severity += 15
        reasons.append(f"{activity_viols} activity type violations")

    # 3. Immersion deviation
    if min_imm > 0 and max_imm > 0:
        if immersion_score < min_imm:
            deviation = min_imm - immersion_score
        elif immersion_score > max_imm:
            deviation = immersion_score - max_imm
        else:
            deviation = 0

        if deviation > 20:
            severity += 30
            reasons.append(f"Immersion {deviation:.0f}% off target (major rebalancing needed)")
        elif deviation > 10:
            severity += 15
            reasons.append(f"Immersion {deviation:.0f}% off target")
        elif deviation > 5:
            severity += 5
            reasons.append(f"Immersion {deviation:.0f}% off target (minor)")

    # 4. Lint errors
    lint_count = len(lint_errors)
    if lint_count == 0:
        pass
    elif lint_count <= 2:
        severity += 5
    elif lint_count <= 5:
        severity += 15
        reasons.append(f"{lint_count} format errors")
    else:
        severity += 25
        reasons.append(f"{lint_count} format errors (many)")

    # 5. Structure failures
    structure_result = results.get('structure', {})
    if isinstance(structure_result, GateResult):
        if structure_result.status == 'FAIL':
            severity += 40
            reasons.append(f"Structure issue: {structure_result.msg}")
    elif isinstance(structure_result, dict) and structure_result.get('status') == 'FAIL':
        severity += 40
        reasons.append(f"Structure issue: {structure_result.get('msg', 'missing sections')}")

    # 6. Activity gates
    activities_result = results.get('activities', {})
    if isinstance(activities_result, GateResult):
        if activities_result.status == 'FAIL':
            severity += 15
            reasons.append("Activity count below minimum")
    elif isinstance(activities_result, dict) and activities_result.get('status') == 'FAIL':
        severity += 15
        reasons.append("Activity count below minimum")

    density_result = results.get('density', {})
    if isinstance(density_result, GateResult):
        if density_result.status == 'FAIL':
            severity += 10
            reasons.append("Activity density below minimum")
    elif isinstance(density_result, dict) and density_result.get('status') == 'FAIL':
        severity += 10
        reasons.append("Activity density below minimum")

    vocab_result = results.get('vocab', {})
    if isinstance(vocab_result, GateResult):
        if vocab_result.status == 'FAIL':
            severity += 20
            reasons.append("Vocabulary count below minimum")
    elif isinstance(vocab_result, dict) and vocab_result.get('status') == 'FAIL':
        severity += 20
        reasons.append("Vocabulary count below minimum")

    # Clamp severity
    severity = min(100, severity)

    # Determine recommendation
    if severity == 0:
        return ('PASS', [], 0)
    elif severity < 30:
        return ('UPDATE', reasons, severity)
    elif severity < 60:
        reasons.insert(0, f"Borderline case (severity {severity}/100)")
        return ('UPDATE', reasons, severity)
    else:
        return ('REWRITE', reasons, severity)
