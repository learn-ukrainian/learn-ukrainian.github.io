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
    """Evaluate word count gate.

    - PASS: at or above target (no upper limit - we love words!)
    - WARN: below target but within 100 words
    - FAIL: 100+ words below target
    """
    min_words = target - 100   # Hard fail threshold

    if total_words >= target:
        return GateResult('PASS', '✅', f"{total_words}/{target}")
    elif total_words >= min_words:
        # Within 100 words of target - warn but don't fail
        shortfall = target - total_words
        return GateResult('WARN', '⚠️', f"{total_words}/{target} ({shortfall} short)")
    else:
        # More than 100 words short - fail
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
    """Evaluate vocabulary count gate.
    
    Note: As of Issue #340, vocab_count is a SOFT TARGET (warning, not blocking).
    Content-driven vocabulary extraction means modules may have fewer explicit
    vocab table entries while vocabulary is used throughout content.
    """
    if count >= target:
        return GateResult('PASS', '✅', f"{count}/{target}")
    # Soft target - warn but don't block
    return GateResult('WARN', '⚠️', f"{count} < {target} (soft target)")


def evaluate_structure(
    has_summary: bool,
    has_vocab: bool,
    has_vocab_table: bool,
    has_activities: bool = True,
    has_resources: bool = True,
    is_a2_plus: bool = False
) -> GateResult:
    """Evaluate structure gate."""
    if not has_summary:
        return GateResult('FAIL', '❌', "Missing '## Summary'")
    
    if is_a2_plus:
        if not has_activities:
            return GateResult('FAIL', '❌', "Missing '## Activities' header")
        if not has_vocab:
            return GateResult('FAIL', '❌', "Missing '## Vocabulary' header")
    else:
        # Legacy/A1 checks
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
            return GateResult('WARN', '⚠️', f"{score}% ({module_type}) - {len(flags)} flags")
        return GateResult('PASS', '✅', f"{score}% ({module_type})")
    if len(flags) >= 2:
        return GateResult('FAIL', '❌', f"{score}% < {threshold}% min ({module_type}) - REWRITE needed")
    return GateResult('FAIL', '❌', f"{score}% < {threshold}% min ({module_type})")


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


def evaluate_grammar(grammar_file_exists: bool, summary: dict = None) -> GateResult:
    """Evaluate grammar validation status.

    Checks if the module has been grammar-validated by looking for
    the -grammar.yaml file in the audit folder.

    Args:
        grammar_file_exists: Whether the grammar validation file exists
        summary: Optional summary dict from the grammar file with counts

    Returns:
        GateResult with validation status
    """
    if not grammar_file_exists:
        return GateResult('INFO', '⏳', "Pending validation")

    if summary:
        confirmed = summary.get('errors_confirmed', 0)
        rejected = summary.get('errors_rejected', 0)
        total = summary.get('total_items', 0)
        needs_review = summary.get('needs_review', 0)

        if needs_review > 0:
            return GateResult('WARN', '⚠️', f"Validated ({needs_review} need review)")
        elif rejected > 0:
            return GateResult('WARN', '⚠️', f"Validated ({rejected}/{total} rejected)")
        else:
            return GateResult('PASS', '✅', f"Validated ({confirmed}/{total} confirmed)")

    return GateResult('PASS', '✅', "Validated")


def evaluate_activity_quality(quality_file_exists: bool, result: str = None,
                              failed_gates: int = 0, level: str = None) -> GateResult:
    """Evaluate activity quality validation status (optional check).

    Checks if the module has been quality-validated by looking for
    the -quality.md file in the audit folder.

    This is an OPTIONAL, INFORMATIONAL gate. Quality validation is not
    required for audit pass/fail - it's a supplementary manual validation
    workflow for B1+ modules.

    Args:
        quality_file_exists: Whether the quality validation report exists
        result: Optional 'PASS' or 'FAIL' status from report
        failed_gates: Number of failed quality gates
        level: Module level (for context)

    Returns:
        GateResult with validation status (always INFO, never blocks audit)
    """
    if not quality_file_exists:
        if level and level.upper() in ['B1', 'B2', 'C1', 'C2']:
            return GateResult('INFO', '📋', "Quality validation available (optional)")
        return GateResult('INFO', 'ℹ️', "Quality validation N/A (A1/A2)")

    if result == 'FAIL':
        return GateResult('INFO', '⚠️', f"Quality gates: {failed_gates} failed (see report)")
    elif result == 'PASS':
        return GateResult('INFO', '✅', "Quality gates: All passed")

    return GateResult('INFO', '📋', "Quality report exists")


def evaluate_content_heavy(
    is_content_heavy: bool,
    activity_count: int,
    content_recall_violations: list,
    min_act: int = 10,
    max_act: int = 12
) -> GateResult:
    """Evaluate content-heavy module compliance.
    
    Content-heavy modules (B2 history, C1 literature/biography/folk/arts)
    should have appropriate activity counts and test language, not recall.
    
    Args:
        is_content_heavy: Whether module is content-heavy type
        activity_count: Number of activities in module
        content_recall_violations: List of content recall violations
        min_act: Minimum required activities (default 10)
        max_act: Maximum allowed activities (default 12)
        
    Returns:
        GateResult with content-heavy compliance status
    """
    if not is_content_heavy:
        return GateResult('INFO', 'ℹ️', "N/A (standard module)")
    
    issues = []
    
    # Check activity count
    if activity_count > max_act:
        issues.append(f"Too many activities: {activity_count} (target {min_act}-{max_act})")
    elif activity_count < min_act:
        issues.append(f"Too few activities: {activity_count} (target {min_act}-{max_act})")
    
    # Check content recall violations
    recall_count = len([v for v in content_recall_violations if v.get('type') == 'CONTENT_RECALL'])
    ref_missing = len([v for v in content_recall_violations if v.get('type') == 'MISSING_TEXT_REFERENCE'])
    year_cloze = len([v for v in content_recall_violations if v.get('type') == 'CLOZE_YEAR_BLANK'])
    year_fill_in = len([v for v in content_recall_violations if v.get('type') == 'FILL_IN_YEAR_ANSWER'])

    if recall_count > 0:
        issues.append(f"{recall_count} content recall patterns")
    if ref_missing > 0:
        issues.append(f"{ref_missing} quizzes missing text refs")
    if year_cloze > 0:
        issues.append(f"{year_cloze} cloze with year blanks")
    if year_fill_in > 0:
        issues.append(f"{year_fill_in} fill-in with year answers")
    
    if issues:
        return GateResult('WARN', '⚠️', "; ".join(issues))
    
    return GateResult('PASS', '✅', f"Content-heavy OK ({activity_count} activities)")


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

    # 1. Pedagogical & Template violations
    ped_count = len(pedagogical_violations)
    if ped_count == 0:
        pass
    elif ped_count <= 3:
        severity += 5
        reasons.append(f"{ped_count} violations (minor)")
    elif ped_count <= 6:
        severity += 15
        reasons.append(f"{ped_count} violations (moderate)")
    elif ped_count <= 10:
        severity += 30
        reasons.append(f"{ped_count} violations (significant)")
    else:
        severity += 50
        reasons.append(f"{ped_count} violations (severe - consider revision)")

    # 2. Violation types (some are worse than others)
    violation_types = [v.get('type', '') for v in pedagogical_violations]

    grammar_viols = sum(1 for t in violation_types if t == 'GRAMMAR')
    if grammar_viols >= 3:
        severity += 20
        reasons.append(f"{grammar_viols} grammar-level violations (fundamental)")

    # Structural violations are weighted LESS if they are purely about flags/sections
    struc_viols = sum(1 for t in violation_types if t in ('SECTION_OUT_OF_ORDER', 'DUPLICATE_SYNONYMOUS_HEADERS', 'EMPTY_REQUIRED_SECTION'))
    if struc_viols >= 5:
        severity += 10 # Cap the impact of many structural issues
        reasons.append(f"Multiple structural inconsistencies ({struc_viols})")

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
            severity += 40
            reasons.append(f"Immersion {deviation:.0f}% off target (major rebalancing needed)")
        elif deviation > 10:
            severity += 20
            reasons.append(f"Immersion {deviation:.0f}% off target")
        elif deviation > 5:
            severity += 10
            reasons.append(f"Immersion {deviation:.0f}% off target (minor)")

    # 4. Lint errors
    lint_count = len(lint_errors)
    if lint_count == 0:
        pass
    elif lint_count <= 2:
        severity += 2
    elif lint_count <= 5:
        severity += 10
        reasons.append(f"{lint_count} format errors")
    else:
        severity += 20
        reasons.append(f"{lint_count} format errors (many)")

    # 5. Structure failures (Hard structural issues like missing Summary)
    structure_result = results.get('structure', {})
    if isinstance(structure_result, GateResult):
        if structure_result.status == 'FAIL':
            severity += 20 # Reduced from 40
            reasons.append(f"Structure issue: {structure_result.msg}")
    elif isinstance(structure_result, dict) and structure_result.get('status') == 'FAIL':
        severity += 20 # Reduced from 40
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

    # vocab_count is now a soft target (Issue #340) - no severity impact
    vocab_result = results.get('vocab', {})
    if isinstance(vocab_result, GateResult):
        if vocab_result.status == 'WARN':
            # Informational only - no severity
            pass
    elif isinstance(vocab_result, dict) and vocab_result.get('status') == 'WARN':
        pass

    # Clamp severity
    severity = min(100, severity)

    # Determine recommendation
    if severity == 0:
        return ('PASS', [], 0)
    elif severity < 40: # Increased threshold for PASS/UPDATE
        return ('UPDATE', reasons, severity)
    elif severity < 75: # Increased threshold for UPDATE/REWRITE
        reasons.insert(0, f"Revision recommended (severity {severity}/100)")
        return ('UPDATE', reasons, severity)
    else:
        return ('REWRITE', reasons, severity)
