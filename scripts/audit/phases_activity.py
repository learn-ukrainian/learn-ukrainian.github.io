"""
Activity validation audit phases.

Handles YAML activity validation, activity answer checking,
and processing of activity sections for the audit pipeline.
"""

import sys

from .checks import (
    check_activity_header_format,
    check_activity_ukrainian_content,
    check_resources_placement,
    check_resources_required,
    check_unjumble_word_match,
    count_items,
)
from .checks.activities import (
    check_advanced_activities_presence,
    check_cloze_syntax_errors,
    check_error_correction_format,
    check_error_correction_hints,
    check_forbidden_activity_types,
    check_hints_in_activities,
    check_malformed_cloze_activities,
    check_mark_the_words_format,
    check_yaml_activity_types,
)
from .checks.activity_validation import (
    check_duplicate_options,
    check_english_hints_in_activities,
    check_fill_in_answer_in_options,
    check_mark_the_words_answers_in_text,
    check_morpheme_patterns,
    check_morpheme_pedagogy,
    check_quiz_single_correct,
    check_select_min_correct,
    check_seminar_reading_pairing,
    check_translate_single_correct,
    check_unjumble_empty_jumbled,
    check_unjumble_out_of_scope_dative,
    check_unjumble_runon_answer,
)
from .checks.external_resource_validation import (
    check_external_resources,
    fix_external_resource_url,
)
from .checks.yaml_lint import lint_yaml_file
from .checks.yaml_schema_validation import check_activity_yaml_schema
from .cleaners import clean_for_stats
from .config import (
    ACTIVITY_COMPLEXITY,
    ACTIVITY_KEYWORDS,
    EXCLUDE_KEYWORDS,
    VALID_ACTIVITY_TYPES,
)
from .parsing import AuditContext, AuditState


def _print_violations(violations: list, label: str, icon: str = "\u26a0\ufe0f",
                      show_fix: bool = False) -> None:
    """Print a violation list with consistent formatting."""
    if not violations:
        return
    print(f"  {icon}  {label}: {len(violations)}")
    for v in violations:
        print(f"     \u2192 {v['issue']}")
        if show_fix and v.get('fix'):
            print(f"     Fix: {v['fix']}")


def _run_yaml_lint_and_schema(ctx: AuditContext) -> list:
    """Run YAML lint and schema validation. Returns schema violations."""
    yaml_file = ctx.yaml_file
    yaml_schema_violations = []

    if yaml_file.exists():
        lint_errors = lint_yaml_file(str(yaml_file))
        if lint_errors:
            print(f"  \u274c YAML syntax violations: {len(lint_errors)}")
            for v in lint_errors:
                print(f"     \u274c [LINT] line {v['line']}: {v['message']}")
                print(f"        Fix: {v['fix']}")
            if any(v['severity'] == 'critical' for v in lint_errors):
                sys.exit(1)

    if yaml_file.exists():
        yaml_schema_violations = check_activity_yaml_schema(ctx.file_path, ctx.level_code, ctx.module_num)
        if yaml_schema_violations:
            print(f"  \u274c YAML schema violations: {len(yaml_schema_violations)}")
            for v in yaml_schema_violations:
                severity_icon = "\u274c" if v['severity'] == 'error' else "\u26a0\ufe0f"
                print(f"     {severity_icon} [{v['type']}] {v['message']}")

    return yaml_schema_violations


def _run_activity_format_checks(activities: list) -> tuple[list, list, list, list, list, list, list]:
    """Run format checks on parsed YAML activities. Returns 7 violation lists."""
    mark_words = check_mark_the_words_format(activities)
    hints = check_hints_in_activities(activities)
    ec_hints = check_error_correction_hints(activities)
    malformed_cloze = check_malformed_cloze_activities(activities)
    cloze_syntax = check_cloze_syntax_errors(activities)
    ec_format = check_error_correction_format(activities)
    invalid_types = check_yaml_activity_types(activities)

    _print_violations(mark_words, "mark-the-words format violations")
    _print_violations(hints, "hint violations")
    _print_violations(ec_hints, "error-correction hint violations", "\u274c", show_fix=True)
    _print_violations(malformed_cloze, "malformed cloze violations")
    _print_violations(cloze_syntax, "cloze syntax violations")
    _print_violations(ec_format, "malformed error-correction violations")
    _print_violations(invalid_types, "invalid activity types in YAML")

    return mark_words, hints, ec_hints, malformed_cloze, cloze_syntax, ec_format, invalid_types


def validate_yaml_activities(ctx: AuditContext, state: AuditState) -> tuple[list, list, list, list, list, list, list, list, list]:
    """Run all YAML activity validation checks."""
    yaml_schema_violations = []
    forbidden_type_violations = []

    if not ctx.skip_activities:
        yaml_schema_violations = _run_yaml_lint_and_schema(ctx)

    if ctx.yaml_activities:
        (mark_words_violations, hint_violations, error_correction_hint_violations,
         malformed_cloze_violations, cloze_syntax_violations,
         error_correction_violations, invalid_type_violations) = _run_activity_format_checks(ctx.yaml_activities)

        forbidden_type_violations = check_forbidden_activity_types(ctx.yaml_activities, ctx.level_code, ctx.module_focus)
        if forbidden_type_violations:
            print(f"  \U0001f534 FORBIDDEN activity types in seminar track: {len(forbidden_type_violations)}")
            for v in forbidden_type_violations:
                print(f"     \u2192 {v['issue']}")
                print(f"        Fix: {v['fix']}")
            state.fail(f"{len(forbidden_type_violations)} forbidden activity types (use --fix to remove)")
    else:
        mark_words_violations = []
        hint_violations = []
        error_correction_hint_violations = []
        malformed_cloze_violations = []
        cloze_syntax_violations = []
        error_correction_violations = []
        invalid_type_violations = []

    return (yaml_schema_violations, mark_words_violations, hint_violations,
            error_correction_hint_violations, malformed_cloze_violations,
            cloze_syntax_violations, error_correction_violations,
            invalid_type_violations, forbidden_type_violations)


def _print_detailed_violations(violations: list, label: str) -> None:
    """Print violations with severity, type, message, and suggestion fields."""
    if not violations:
        return
    print(f"  \u26a0\ufe0f  {label}: {len(violations)}")
    for v in violations:
        severity = "\U0001f534" if v['severity'] == 'critical' else "\u26a0\ufe0f"
        print(f"     {severity} [{v['type']}] {v.get('activity', '')}")
        print(f"        Issue: {v['message']}")
        print(f"        Fix: {v.get('suggestion', v.get('fix', ''))}")
        if 'pedagogical_issue' in v:
            print(f"        Why: {v['pedagogical_issue']}")


def _check_answer_correctness(activities: list) -> list:
    """Run all answer correctness checks and return combined violations."""
    violations = []
    violations.extend(check_select_min_correct(activities))
    violations.extend(check_quiz_single_correct(activities))
    violations.extend(check_fill_in_answer_in_options(activities))
    violations.extend(check_translate_single_correct(activities))
    violations.extend(check_mark_the_words_answers_in_text(activities))
    violations.extend(check_unjumble_runon_answer(activities))
    violations.extend(check_unjumble_out_of_scope_dative(activities))
    violations.extend(check_duplicate_options(activities))
    return violations


def _check_external_urls(ctx: AuditContext, state: AuditState) -> None:
    """Check external resource URLs in reading activities for seminar tracks."""
    if ctx.level_code.lower() not in ['lit', 'hist', 'istorio', 'bio']:
        return

    external_url_violations = check_external_resources(ctx.yaml_activities, ctx.module_title)
    if not external_url_violations:
        return

    print(f"  \U0001f517 External URL validation issues: {len(external_url_violations)}")
    for v in external_url_violations:
        severity = "\U0001f534" if v['severity'] == 'critical' else "\u26a0\ufe0f"
        print(f"     {severity} [{v['type']}] {v['activity']}")
        print(f"        URL: {v.get('url', 'N/A')}")
        print(f"        Issue: {v['message']}")
        if v.get('suggested_url'):
            print(f"        \u2705 Suggested fix: {v['suggested_url']}")
            if ctx.yaml_file and fix_external_resource_url(ctx.yaml_file, v['url'], v['suggested_url']):
                print(f"        \u2713 AUTO-FIXED: URL updated in {ctx.yaml_file.name}")
            else:
                print(f"        Fix: {v.get('suggestion', '')}")
        else:
            print(f"        Fix: {v.get('suggestion', '')}")
    state.has_critical_failure = True


def validate_activity_answers(ctx: AuditContext, state: AuditState) -> None:
    """Check structural correctness of activity answers and external URLs."""
    if not ctx.yaml_activities:
        return

    morpheme_violations = check_morpheme_patterns(ctx.yaml_activities)
    if morpheme_violations:
        print(f"  \u26a0\ufe0f  morpheme pattern violations: {len(morpheme_violations)}")
        for v in morpheme_violations:
            print(f"     \u2192 {v['activity']}: {v['message']}")

    _print_detailed_violations(check_morpheme_pedagogy(ctx.yaml_activities), "pedagogically weak morpheme activities")
    _print_detailed_violations(
        check_english_hints_in_activities(ctx.yaml_activities, ctx.level_code, ctx.module_num),
        "English hints in A2+ activities"
    )
    _print_detailed_violations(check_unjumble_empty_jumbled(ctx.yaml_activities), "unjumble activities with empty jumbled fields")

    seminar_pairing_violations = check_seminar_reading_pairing(ctx.yaml_activities, ctx.level_code)
    _print_detailed_violations(seminar_pairing_violations, "Seminar reading-analysis pairing issues")
    if any(v['severity'] == 'critical' for v in seminar_pairing_violations):
        state.has_critical_failure = True

    answer_correctness_violations = _check_answer_correctness(ctx.yaml_activities)
    _print_detailed_violations(answer_correctness_violations, "Activity answer correctness issues")
    if any(v['severity'] == 'critical' for v in answer_correctness_violations):
        state.has_critical_failure = True

    _check_external_urls(ctx, state)


def _get_density_target(act_type: str, config: dict, level_code: str, module_focus: str | None) -> int:
    """Get the minimum item count for an activity type based on complexity config."""
    density_target = config['min_items_per_activity']
    if act_type in ACTIVITY_COMPLEXITY:
        specific_key = f"{level_code}-{module_focus}" if module_focus else level_code
        complexity_rules = ACTIVITY_COMPLEXITY[act_type].get(specific_key)
        if not complexity_rules:
            complexity_rules = ACTIVITY_COMPLEXITY[act_type].get(level_code, {})
        if 'min_items' in complexity_rules:
            density_target = complexity_rules['min_items']
    return density_target


def _process_yaml_activities(ctx: AuditContext, state: AuditState) -> None:
    """Process YAML activities into activity details and density tracking."""
    print(f"  \U0001f4cb Found YAML activities file ({len(ctx.yaml_activities)} activities)")
    for activity in ctx.yaml_activities:
        act_type = activity.type.lower()
        if act_type not in VALID_ACTIVITY_TYPES and act_type.replace('-', '') not in [t.replace('-', '') for t in VALID_ACTIVITY_TYPES]:
            continue

        state.activity_count += 1
        state.total_activities += 1
        state.found_activity_types.append(act_type)

        items = count_items('', activity)
        density_target = _get_density_target(act_type, ctx.config, ctx.level_code, ctx.module_focus)
        title = getattr(activity, 'title', act_type)

        state.activity_details.append({
            'title': title, 'type': act_type,
            'items': items, 'target': density_target,
            'status': '\u2705' if items >= density_target else '\u274c'
        })

        if items >= density_target:
            state.valid_density_count += 1
        else:
            state.low_density_activities.append({
                'title': title, 'type': act_type,
                'items': items, 'target': density_target
            })

        print(f"  > {title}: {items} items (min {density_target})")


def process_activity_sections(ctx: AuditContext, state: AuditState) -> None:
    """Process YAML and embedded markdown activities, build activity details and table rows."""
    if ctx.use_yaml_activities:
        _process_yaml_activities(ctx, state)

    for title, text in ctx.section_map.items():
        title_lower = title.lower()
        is_core = False
        is_excluded = False
        is_activity = False

        matched_act_type = None
        for act in ACTIVITY_KEYWORDS:
            if act in title_lower:
                is_activity = True
                matched_act_type = act
        if is_activity:
            state.found_activity_types.append(matched_act_type)

        if not is_activity:
            for exc in EXCLUDE_KEYWORDS:
                if exc in title_lower:
                    is_excluded = True
                    break
            if not is_excluded:
                is_core = True

        cleaned_stats = clean_for_stats(text)
        count = len(cleaned_stats.split())

        status_icon = "\u26aa\ufe0f"
        note = "Skipped"

        if is_activity and not ctx.use_yaml_activities:
            state.activity_count += 1
            state.total_activities += 1
            items = count_items(text)
            density_target = ctx.config['min_items_per_activity']
            if matched_act_type in ACTIVITY_COMPLEXITY:
                 complexity_rules = ACTIVITY_COMPLEXITY[matched_act_type].get(ctx.level_code, {})
                 if 'min_items' in complexity_rules:
                     density_target = complexity_rules['min_items']

            state.activity_details.append({
                'title': title, 'type': matched_act_type,
                'items': items, 'target': density_target,
                'status': '\u2705' if items >= density_target else '\u274c'
            })

            if items >= density_target:
                state.valid_density_count += 1
            else:
                state.low_density_activities.append({
                    'title': title, 'type': matched_act_type,
                    'items': items, 'target': density_target
                })

            status_icon = "\U0001f3ae"
            note = f"Activity ({items} items, min {density_target})"
            print(f"  > {title}: {items} items (min {density_target})")
            display_count = items

        elif is_activity and ctx.use_yaml_activities:
            status_icon = "\u26aa\ufe0f"
            note = "Skipped (using YAML)"
            display_count = 0
        elif is_core and not is_excluded:
            status_icon = "\u2705"
            note = "Included in Core"
            display_count = count
        elif is_excluded:
            status_icon = "\u2796"
            note = "Excluded Type"
            display_count = count
        else:
            display_count = count

        state.table_rows.append(f"| **{title}** | {status_icon} | {display_count} | {note} |")


def run_activity_pedagogical_checks(ctx: AuditContext, state: AuditState,
                                     yaml_schema_violations: list,
                                     mark_words_violations: list,
                                     hint_violations: list,
                                     error_correction_hint_violations: list,
                                     malformed_cloze_violations: list,
                                     cloze_syntax_violations: list,
                                     error_correction_violations: list,
                                     invalid_type_violations: list) -> None:
    """Run activity-specific pedagogical checks."""
    ukrainian_content_violations = check_activity_ukrainian_content(ctx.content, ctx.level_code)
    for v in ukrainian_content_violations:
        state.pedagogical_violations.append({
            'type': v['type'], 'severity': 'error',
            'issue': v['issue'], 'fix': v['fix']
        })

    resources_violations = check_resources_placement(ctx.content)
    for v in resources_violations:
        state.pedagogical_violations.append({
            'type': v['type'], 'severity': 'warning',
            'issue': v['issue'], 'fix': v['fix']
        })

    missing_resources_violations = check_resources_required(ctx.content)
    for v in missing_resources_violations:
        state.pedagogical_violations.append({
            'type': v['type'], 'severity': 'warning',
            'issue': v['issue'], 'fix': v['fix']
        })

    unjumble_violations = check_unjumble_word_match(ctx.content)
    for v in unjumble_violations:
        state.pedagogical_violations.append({
            'type': v['type'], 'severity': 'error',
            'issue': v['issue'], 'fix': v['fix']
        })

    header_violations = check_activity_header_format(ctx.content)
    for v in header_violations:
        state.pedagogical_violations.append({
            'type': v['type'], 'severity': 'error',
            'issue': v['issue'], 'fix': v['fix']
        })

    # Append all violation lists to pedagogical violations
    for violation_list in [mark_words_violations, hint_violations,
                          error_correction_hint_violations, malformed_cloze_violations,
                          cloze_syntax_violations, error_correction_violations,
                          invalid_type_violations]:
        for v in violation_list:
            state.pedagogical_violations.append({
                'type': v['type'], 'severity': v['severity'],
                'issue': v['issue'], 'fix': v['fix']
            })

    for v in yaml_schema_violations:
        state.pedagogical_violations.append({
            'type': v['type'], 'severity': v['severity'],
            'issue': v['message'],
            'fix': 'Fix the activity YAML to match the schema in schemas/activities-base.schema.json',
            'blocking': True
        })

    if not ctx.skip_activities:
        advanced_presence_violations = check_advanced_activities_presence(state.found_activity_types, ctx.level_code, ctx.module_focus)
    else:
        advanced_presence_violations = []
    for v in advanced_presence_violations:
        state.pedagogical_violations.append({
            'type': v['type'], 'severity': v['severity'],
            'blocking': v.get('blocking', True),
            'issue': v['issue'], 'fix': v['fix']
        })
