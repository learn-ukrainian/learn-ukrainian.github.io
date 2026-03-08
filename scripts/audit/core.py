"""
Core audit orchestration module.

Contains the main audit_module function that coordinates all checks
and produces the final audit report. All logic is delegated to
specialized submodules.
"""

import os
import re
import sys
from pathlib import Path

import yaml

# Add project root to path for shared module imports
SCRIPT_DIR = Path(__file__).parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from slug_utils import to_bare_slug
from yaml_activities import ActivityParser

from .checks.outline_compliance import (
    check_outline_compliance,
    print_section_summary,
)
from .cleaners import extract_core_content
from .config import get_level_config, get_word_target
from .gates import GateResult, evaluate_structure
from .loaders import (
    get_module_number_from_curriculum,
    load_yaml_meta,
    load_yaml_plan,
    load_yaml_vocab,
)
from .parsing import (
    AuditContext,
    AuditState,
    detect_focus,
    detect_level,
    parse_frontmatter,
    parse_sections,
    validate_required_metadata,
)
from .phases_activity import (
    process_activity_sections,
    run_activity_pedagogical_checks,
    validate_activity_answers,
    validate_yaml_activities,
)
from .phases_content import run_content_quality_checks
from .phases_gates import (
    count_words_and_engagement,
    evaluate_advanced_gates,
    evaluate_core_gates,
    evaluate_immersion,
)
from .phases_report import generate_output_and_report
from .validators import (
    check_structure,
    validate_checkpoint_coverage,
    validate_checkpoint_format,
    validate_tone,
)

# Re-export for backward compatibility (used by tests)
from .lint import check_typography  # noqa: F401


def _load_and_resolve(file_path: str, skip_activities: bool, skip_review: bool) -> tuple[AuditContext, AuditState]:
    """Load files, parse frontmatter, detect level/config, build AuditContext."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    state = AuditState()

    meta_data = load_yaml_meta(file_path)
    plan_data = load_yaml_plan(file_path)

    if meta_data and plan_data:
        print(f"  \U0001f4cb Loaded Plan from: plans/{plan_data.get('level', '').lower()}/{os.path.basename(file_path).replace('.md', '.yaml')}")
        PLAN_FIELDS_TO_MERGE = [
            'title', 'subtitle', 'content_outline', 'word_target',
            'vocabulary_hints', 'activity_hints', 'focus', 'pedagogy',
            'prerequisites', 'connects_to', 'objectives', 'learning_outcomes',
            'grammar', 'module_type', 'sources', 'immersion', 'register', 'phase'
        ]
        for fld in PLAN_FIELDS_TO_MERGE:
            if fld in plan_data and fld not in meta_data:
                    meta_data[fld] = plan_data[fld]

    vocab_data, vocab_error = load_yaml_vocab(file_path)

    if meta_data:
        frontmatter_str = yaml.dump(meta_data, sort_keys=False, allow_unicode=True)
        body = content
        print("  \U0001f4cb Loaded Metadata from YAML sidecar")
    else:
        frontmatter_str, body = parse_frontmatter(content)

    if not frontmatter_str:
        print("Error: No YAML frontmatter found (checked embedded and sidecar).")
        state.fail("No YAML frontmatter found")
        print("\nCritical Failures:")
        for reason in state.critical_failure_reasons:
            print(f"  \u2022 {reason}")
        sys.exit(1)

    level_code, module_num, track_code = detect_level(file_path, frontmatter_str)

    display_level = level_code
    track_match = re.search(r'/([abc][12]-[a-z]+)/', file_path.lower())
    if track_match:
        display_level = track_match.group(1).upper()
    elif re.search(r'/lit/', file_path.lower()):
        display_level = 'LIT'

    if module_num == 999:
        curriculum_module_num = get_module_number_from_curriculum(file_path, level_code)
        if curriculum_module_num is not None:
            module_num = curriculum_module_num

    module_focus = detect_focus(frontmatter_str, level_code, module_num, meta_data.get('title') if meta_data else "", file_path)

    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else level_code

    title_match = re.search(r"title:\s*['\"]?([^'\"\n]+)['\"]?", frontmatter_str)
    module_title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

    print(f"\n\U0001f4cb Auditing: {display_level} M{module_num:02d} \u2014 {module_title}")

    target = get_word_target(level_code, module_num, module_focus)
    if meta_data and 'word_target' in meta_data:
        target = int(meta_data['word_target'])
    elif plan_data and 'word_target' in plan_data:
        target = int(plan_data['word_target'])

    print(f"   File: {file_path} | Target: {target} words")

    if not meta_data:
        missing_meta = validate_required_metadata(frontmatter_str)
        if missing_meta:
            print(f"\u274c AUDIT FAILED: Missing Frontmatter Fields: {', '.join(missing_meta)}")
            state.fail(f"Missing Frontmatter Fields: {', '.join(missing_meta)}")
            print("\nCritical Failures:")
            for reason in state.critical_failure_reasons:
                print(f"  \u2022 {reason}")
            sys.exit(1)

    config = get_level_config(level_code, module_focus)

    if meta_data and meta_data.get('activity_hints'):
        meta_required_types = set()
        for hint in meta_data['activity_hints']:
            if isinstance(hint, dict) and 'type' in hint:
                meta_required_types.add(hint['type'])
        if meta_required_types:
            config = dict(config)
            config['required_types'] = meta_required_types
            print(f"  \U0001f4cb Required activity types from meta: {', '.join(sorted(meta_required_types))}")

    pedagogy = "Not Specified"
    pedagogy_match = re.search(r'^pedagogy:\s*(.+)$', frontmatter_str, re.MULTILINE)
    if pedagogy_match:
        pedagogy = pedagogy_match.group(1).strip()

    section_map = parse_sections(body)
    core_content = extract_core_content(body)

    yaml_activities = None
    yaml_file = Path(file_path).parent / 'activities' / (Path(file_path).stem + '.yaml')

    if skip_activities:
        print("  \u23f3 Content-only audit: activities/vocab gates DEFERRED")
        use_yaml_activities = False
    else:
        if not yaml_file.exists():
            yaml_file = Path(file_path).with_suffix('.activities.yaml')
        if yaml_file.exists():
            parser = ActivityParser()
            try:
                yaml_activities = parser.parse(yaml_file)
            except Exception as e:
                print(f"  \u274c Error parsing YAML activities: {e}")
        use_yaml_activities = yaml_activities is not None

    ctx = AuditContext(
        file_path=file_path, content=content, body=body,
        frontmatter_str=frontmatter_str, meta_data=meta_data,
        plan_data=plan_data, vocab_data=vocab_data, vocab_error=vocab_error,
        level_code=level_code, module_num=module_num, track_code=track_code,
        display_level=display_level, module_focus=module_focus,
        module_title=module_title, target=target, config=config,
        section_map=section_map, core_content=core_content, phase=phase,
        pedagogy=pedagogy, skip_activities=skip_activities,
        skip_review=skip_review, yaml_activities=yaml_activities,
        use_yaml_activities=use_yaml_activities, yaml_file=yaml_file,
    )

    return ctx, state


def _check_template_compliance(ctx: AuditContext, state: AuditState) -> None:
    """Check template compliance (Issue #398, #389)."""
    TEMPLATE_COMPLIANCE_ENABLED_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1']
    if ctx.level_code not in TEMPLATE_COMPLIANCE_ENABLED_LEVELS:
        return

    try:
        from . import template_parser
        from .checks import template_compliance as tc_module

        module_slug = Path(ctx.file_path).stem
        track_match = re.search(r'/([abc][12](?:-[a-z0-9]+)?|lit)/', ctx.file_path.lower())
        full_level = track_match.group(1) if track_match else ctx.level_code.lower()
        module_id_for_mapping = f"{full_level}-{module_slug}"

        meta_for_template = ctx.meta_data if ctx.meta_data else {}
        template_path = template_parser.resolve_template(module_id_for_mapping, meta_for_template)
        template_structure = template_parser.parse_template(template_path)

        if template_structure is None:
            print(f"  \u2139\ufe0f  No template mapping for {module_id_for_mapping} (skipping template compliance)")
        else:
            print(f"  \U0001f4cb Template: {template_path} (pedagogy: {template_structure.pedagogy})")
            state.template_violations = tc_module.check_template_compliance(
                content=ctx.content, meta=meta_for_template, template=template_structure
            )

        if state.template_violations:
            critical_count = sum(1 for v in state.template_violations if v['severity'] == 'CRITICAL')
            warning_count = sum(1 for v in state.template_violations if v['severity'] == 'WARNING')
            info_count = sum(1 for v in state.template_violations if v['severity'] == 'INFO')
            print(f"  \u26a0\ufe0f  Template violations: {critical_count} critical, {warning_count} warnings, {info_count} info")
            for violation in state.template_violations[:3]:
                severity_icon = "\U0001f534" if violation['severity'] == 'CRITICAL' else "\u26a0\ufe0f" if violation['severity'] == 'WARNING' else "\u2139\ufe0f"
                print(f"     {severity_icon} [{violation['type']}] {violation['issue']}")
            if critical_count > 0:
                state.fail(f"{critical_count} Critical Template Violations")

    except ImportError as e:
        print(f"  \u26a0\ufe0f  Template compliance not available: {e}")
    except Exception as e:
        print(f"  \u26a0\ufe0f  Template resolution error: {e}")


def _check_outline_and_structure(ctx: AuditContext, state: AuditState) -> GateResult:
    """Check outline compliance, structure, tone, checkpoints, fill-in options."""
    # Outline compliance
    outline_violations = check_outline_compliance(ctx.file_path, ctx.level_code, ctx.module_num)
    if outline_violations:
        error_count = sum(1 for v in outline_violations if v['severity'] == 'error')
        warning_count = sum(1 for v in outline_violations if v['severity'] == 'warning')
        print(f"  \u26a0\ufe0f  Outline compliance: {error_count} errors, {warning_count} warnings")
        for v in outline_violations[:3]:
            severity_icon = "\u274c" if v['severity'] == 'error' else "\u26a0\ufe0f"
            print(f"     {severity_icon} [{v['type']}] {v['message'].split(chr(10))[0]}")
        if error_count > 0:
            state.fail(f"{error_count} Outline Compliance Errors")

    print_section_summary(ctx.file_path, word_target=ctx.target)

    tone_errors = validate_tone(ctx.content)
    if tone_errors:
        for err in tone_errors:
            print(f"\u274c Tone violation: {err}")
            state.fail(err)

    # Structure gate
    struct_flags = check_structure(ctx.content)
    has_vocab_data = ctx.vocab_data is not None

    activities_yaml_path = Path(ctx.file_path).parent / 'activities' / (Path(ctx.file_path).stem + '.yaml')
    if not activities_yaml_path.exists():
        activities_yaml_path = Path(ctx.file_path).with_suffix('.activities.yaml')
    has_activities_data = activities_yaml_path.exists()

    has_resources_data = False
    resources_path = Path('docs/resources/external_resources.yaml')
    if resources_path.exists():
        with resources_path.open('r', encoding='utf-8') as f:
            try:
                resources_data = yaml.safe_load(f)
                all_resources = resources_data.get('resources', {})
                module_slug = Path(ctx.file_path).stem
                has_resources_data = module_slug in all_resources or f"{ctx.level_code.lower()}-{module_slug}" in all_resources
            except Exception:
                pass

    has_summary = struct_flags['summary']
    if ctx.meta_data and (ctx.meta_data.get('summary') or ctx.meta_data.get('description')):
        has_summary = True

    is_clean_md_standard = ctx.level_code in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'LIT', 'OES', 'RUTH')

    structure_gate = evaluate_structure(
        has_summary=has_summary,
        has_vocab=struct_flags['vocab_header'] or has_vocab_data or ctx.skip_activities,
        has_vocab_table=struct_flags['vocab_table'] or has_vocab_data or ctx.skip_activities,
        has_activities=struct_flags['activities_header'] or has_activities_data or ctx.skip_activities,
        has_resources=struct_flags['resources_header'] or has_resources_data,
        is_a2_plus=is_clean_md_standard,
        vocab_error=ctx.vocab_error,
    )

    if structure_gate.status == 'FAIL':
        print(f"\u274c Structure check failed: {structure_gate.msg}")
        state.fail(f"Structure: {structure_gate.msg}")

    # Duplicate vocabulary check
    if ctx.vocab_data and ctx.level_code in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        has_embedded_vocab = bool(re.search(r'^#\s*(\u0421\u043b\u043e\u0432\u043d\u0438\u043a|Vocabulary)', ctx.content, re.MULTILINE))
        if has_embedded_vocab:
            vocab_section_match = re.search(r'^#\s*(\u0421\u043b\u043e\u0432\u043d\u0438\u043a|Vocabulary)\s*\n(.*?)(?=^#|\Z)', ctx.content, re.MULTILINE | re.DOTALL)
            if vocab_section_match:
                vocab_section = vocab_section_match.group(2)
                has_embedded_table = '|' in vocab_section and re.search(r'\|.*\|.*\|', vocab_section)
                if has_embedded_table:
                    print("\u26a0\ufe0f  DUPLICATE VOCABULARY: Both YAML sidecar and embedded markdown table exist.")

    # Checkpoint format validation
    if ctx.module_focus == 'checkpoint':
        checkpoint_errors = validate_checkpoint_format(ctx.content)
        coverage_errors = validate_checkpoint_coverage(ctx.content, ctx.frontmatter_str)
        checkpoint_errors.extend(coverage_errors)
        if checkpoint_errors:
            print("\u274c CHECKPOINT FORMAT ERRORS:")
            for err in checkpoint_errors:
                print(f"  \u2192 {err}")
            state.fail("Checkpoint Format Errors")

    # Fill-in options check
    for title, text in ctx.section_map.items():
        if title.lower().startswith('fill-in'):
            if '> [!options]' not in text:
                print(f"\u274c AUDIT FAILED: Activity '{title}' missing mandatory > [!options] block.")
                sys.exit(1)
            if not re.search(r'^\s*\d+\.', text, re.MULTILINE):
                print(f"\u274c AUDIT FAILED: Activity '{title}' missing numbered items (1. ...).")
                sys.exit(1)

    return structure_gate


def _run_pedagogical_and_content_checks(ctx: AuditContext, state: AuditState,
                                         yaml_schema_violations: list,
                                         mark_words_violations: list,
                                         hint_violations: list,
                                         error_correction_hint_violations: list,
                                         malformed_cloze_violations: list,
                                         cloze_syntax_violations: list,
                                         error_correction_violations: list,
                                         invalid_type_violations: list) -> None:
    """Run pedagogical checks, content quality, and activity violation aggregation."""
    run_content_quality_checks(ctx, state)
    run_activity_pedagogical_checks(
        ctx, state,
        yaml_schema_violations, mark_words_violations, hint_violations,
        error_correction_hint_violations, malformed_cloze_violations,
        cloze_syntax_violations, error_correction_violations,
        invalid_type_violations,
    )

    from .gates import evaluate_pedagogy
    blocking_pedagogy = [v for v in state.pedagogical_violations if v.get('blocking', True)]
    state.results['pedagogy'] = evaluate_pedagogy(len(blocking_pedagogy))
    if state.results['pedagogy'].status == 'FAIL':
        state.has_critical_failure = True


def audit_module(file_path: str, skip_activities: bool = False,
                 skip_review: bool = False) -> bool:
    """
    Orchestrates the audit process for a single module file.
    Returns True on success, False on failure.
    """
    ctx, state = _load_and_resolve(file_path, skip_activities, skip_review)

    _check_template_compliance(ctx, state)

    structure_gate = _check_outline_and_structure(ctx, state)

    count_words_and_engagement(ctx, state)

    (yaml_schema_violations, mark_words_violations, hint_violations,
     error_correction_hint_violations, malformed_cloze_violations,
     cloze_syntax_violations, error_correction_violations,
     invalid_type_violations, forbidden_type_violations) = validate_yaml_activities(ctx, state)

    validate_activity_answers(ctx, state)

    process_activity_sections(ctx, state)

    unique_types = evaluate_core_gates(ctx, state, structure_gate)

    _run_pedagogical_and_content_checks(
        ctx, state,
        yaml_schema_violations, mark_words_violations, hint_violations,
        error_correction_hint_violations, malformed_cloze_violations,
        cloze_syntax_violations, error_correction_violations,
        invalid_type_violations,
    )

    immersion_score, min_imm, max_imm = evaluate_immersion(ctx, state)

    evaluate_advanced_gates(ctx, state)

    return generate_output_and_report(ctx, state, immersion_score, min_imm, max_imm, unique_types)
