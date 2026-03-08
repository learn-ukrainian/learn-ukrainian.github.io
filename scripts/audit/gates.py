"""
Gate evaluation logic for module auditing.

Evaluates various quality gates (word count, activities, density, etc.)
and computes recommendations based on violations.
"""

from dataclasses import dataclass


@dataclass
class GateResult:
    """Result of a gate evaluation."""
    status: str  # 'PASS', 'FAIL', 'WARN', 'INFO'
    icon: str
    msg: str


def evaluate_word_count(total_words: int, target: int, raw_words: int = 0) -> GateResult:
    """Evaluate word count gate.

    - PASS: at or above target (no upper limit - we love words!)
    - WARN: below target but within 100 words
    - FAIL: 100+ words below target
    """
    min_words = target - 100   # Hard fail threshold

    msg = f"{total_words}/{target}"
    if raw_words > total_words:
        msg += f" (raw: {raw_words})"

    if total_words >= target:
        return GateResult('PASS', '✅', msg)
    elif total_words >= min_words:
        # Within 100 words of target - warn but don't fail
        shortfall = target - total_words
        return GateResult('WARN', '⚠️', f"{msg} ({shortfall} short)")
    else:
        # More than 100 words short - fail
        return GateResult('FAIL', '❌', msg)


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
    is_a2_plus: bool = False,
    vocab_error: str | None = None,
) -> GateResult:
    """Evaluate structure gate."""
    if not has_summary:
        return GateResult('FAIL', '❌', "Missing '## Summary'")

    if is_a2_plus:
        if not has_activities:
            return GateResult('FAIL', '❌', "Missing '## Activities' header OR activities sidecar")
        if not has_vocab:
            if vocab_error:
                return GateResult('FAIL', '❌', f"Vocabulary sidecar {vocab_error}")
            return GateResult('FAIL', '❌', "Missing '## Vocabulary' header OR vocabulary sidecar")
    else:
        # Legacy/A1 checks
        if not has_vocab:
            if vocab_error:
                return GateResult('FAIL', '❌', f"Vocabulary sidecar {vocab_error}")
            return GateResult('FAIL', '❌', "Missing '## Vocabulary'")
        if not has_vocab_table:
            return GateResult('FAIL', '❌', "Missing Vocab Table")

    return GateResult('PASS', '✅', "Valid Structure")


def evaluate_persona(has_persona: bool, has_voice: bool, has_role: bool) -> GateResult:
    """Evaluate persona gate (Deterministic Curriculum Standard v2.2)."""
    if not has_persona:
        return GateResult('FAIL', '❌', "Missing 'persona' in plan YAML")
    if not has_voice:
        return GateResult('FAIL', '❌', "Missing 'persona.voice' in plan YAML")
    if not has_role:
        return GateResult('FAIL', '❌', "Missing 'persona.role' in plan YAML")
    return GateResult('PASS', '✅', "Persona Defined")


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


def evaluate_naturalness(score: int, status: str) -> GateResult:
    """Evaluate naturalness score gate.

    Target: 8/10 for content modules.
    PENDING status is informational (not blocking) — review sets the real score.
    """
    # Guard against None values (YAML null parses as None)
    if score is None:
        score = 0
    if status is None:
        status = "PENDING"

    if status == 'PENDING':
        if score > 0:
            return GateResult('INFO', 'ℹ️', f"{score}/10 (PENDING — awaiting review)")
        return GateResult('INFO', 'ℹ️', "PENDING — awaiting review")

    if status == 'PASS' and score >= 8:
        return GateResult('PASS', '✅', f"{score}/10 (High)")
    elif status == 'PASS' and score >= 7:
        # Strict requirement: Fail if below 8
        return GateResult('FAIL', '❌', f"{score}/10 (Acceptable but below 8/10 target)")
    elif score > 0:
        return GateResult('FAIL', '❌', f"{score}/10 ({status} - Requires rewrite)")
    else:
        return GateResult('FAIL', '❌', "Not scored")


def evaluate_grammar(grammar_file_exists: bool, summary: dict | None = None) -> GateResult:
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
        return GateResult('INFO', 'ℹ️', "N/A (covered by naturalness)")

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


def evaluate_activity_quality(quality_file_exists: bool, result: str | None = None,
                              failed_gates: int = 0, level: str | None = None) -> GateResult:
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


def evaluate_research_alignment(
    research_info: dict | None,
    content_exists: bool,
) -> GateResult:
    """Evaluate whether content reflects the current research quality.

    WARN-level gate — flags stale content but doesn't block audits.
    Uses content_alignment data from research_quality.assess_research().
    """
    if research_info is None:
        return GateResult('INFO', 'ℹ️', "N/A (no research file)")

    if not content_exists:
        return GateResult('INFO', 'ℹ️', "Content not yet written")

    alignment = research_info.get("content_alignment")
    if alignment is None:
        return GateResult('INFO', 'ℹ️', "N/A (no alignment data)")

    if alignment.get("refresh_recommended"):
        reasons = alignment.get("reasons", [])
        reason_str = reasons[0] if reasons else "research upgraded"
        return GateResult('WARN', '⚠️', f"Refresh recommended: {reason_str}")

    return GateResult('PASS', '✅', "Content aligned with research")


def _pedagogical_severity(violations: list) -> tuple[int, list[str]]:
    """Compute severity and reasons from pedagogical violation count and types."""
    severity = 0
    reasons = []

    ped_count = len(violations)
    if ped_count <= 0:
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

    violation_types = [v.get('type', '') for v in violations]

    grammar_viols = sum(1 for t in violation_types if t == 'GRAMMAR')
    if grammar_viols >= 3:
        severity += 20
        reasons.append(f"{grammar_viols} grammar-level violations (fundamental)")

    struc_viols = sum(1 for t in violation_types if t in ('SECTION_OUT_OF_ORDER', 'DUPLICATE_SYNONYMOUS_HEADERS', 'EMPTY_REQUIRED_SECTION'))
    if struc_viols >= 5:
        severity += 10
        reasons.append(f"Multiple structural inconsistencies ({struc_viols})")

    activity_viols = sum(
        1 for t in violation_types
        if t in ('ACTIVITY_MISUSE', 'LEVEL_RESTRICTION', 'FOCUS_MISMATCH')
    )
    if activity_viols >= 3:
        severity += 15
        reasons.append(f"{activity_viols} activity type violations")

    return severity, reasons


def _immersion_severity(
    immersion_score: float, min_imm: int, max_imm: int,
) -> tuple[int, list[str]]:
    """Compute severity and reasons from immersion deviation."""
    if min_imm <= 0 or max_imm <= 0:
        return 0, []

    if immersion_score < min_imm:
        deviation = min_imm - immersion_score
    elif immersion_score > max_imm:
        deviation = immersion_score - max_imm
    else:
        return 0, []

    if deviation > 20:
        return 40, [f"Immersion {deviation:.0f}% off target (major rebalancing needed)"]
    elif deviation > 10:
        return 20, [f"Immersion {deviation:.0f}% off target"]
    elif deviation > 5:
        return 10, [f"Immersion {deviation:.0f}% off target (minor)"]
    return 0, []


def _lint_severity(lint_errors: list) -> tuple[int, list[str]]:
    """Compute severity and reasons from lint errors."""
    lint_count = len(lint_errors)
    if lint_count == 0:
        return 0, []
    elif lint_count <= 2:
        return 2, []
    elif lint_count <= 5:
        return 10, [f"{lint_count} format errors"]
    else:
        return 20, [f"{lint_count} format errors (many)"]


def _gate_result_is_fail(result) -> bool:
    """Check if a gate result (GateResult or dict) has FAIL status."""
    if isinstance(result, GateResult):
        return result.status == 'FAIL'
    if isinstance(result, dict):
        return result.get('status') == 'FAIL'
    return False


def _gate_severity(results: dict) -> tuple[int, list[str]]:
    """Compute severity and reasons from structure, activities, and density gate results."""
    severity = 0
    reasons = []

    structure_result = results.get('structure', {})
    if _gate_result_is_fail(structure_result):
        severity += 20
        msg = structure_result.msg if isinstance(structure_result, GateResult) else structure_result.get('msg', 'missing sections')
        reasons.append(f"Structure issue: {msg}")

    if _gate_result_is_fail(results.get('activities', {})):
        severity += 15
        reasons.append("Activity count below minimum")

    if _gate_result_is_fail(results.get('density', {})):
        severity += 10
        reasons.append("Activity density below minimum")

    return severity, reasons


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

    s, r = _pedagogical_severity(pedagogical_violations)
    severity += s
    reasons.extend(r)

    s, r = _immersion_severity(immersion_score, min_imm, max_imm)
    severity += s
    reasons.extend(r)

    s, r = _lint_severity(lint_errors)
    severity += s
    reasons.extend(r)

    s, r = _gate_severity(results)
    severity += s
    reasons.extend(r)

    severity = min(100, severity)

    if severity == 0:
        return ('PASS', [], 0)
    elif severity < 40:
        return ('UPDATE', reasons, severity)
    elif severity < 75:
        reasons.insert(0, f"Revision recommended (severity {severity}/100)")
        return ('UPDATE', reasons, severity)
    else:
        return ('REWRITE', reasons, severity)
