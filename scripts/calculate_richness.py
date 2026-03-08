#!/usr/bin/env python3
"""Calculate richness score for module content.

Richness measures how engaging and alive the content is beyond basic counts.
This is primarily for B1+ modules where full immersion enables rich content.

Usage:
    python3 scripts/calculate_richness.py <file>
    python3 scripts/calculate_richness.py <file> --json

IMPORTANT: Richness criteria vary by MODULE TYPE, not just level.
- Grammar modules: examples, dialogues, proverbs
- History modules: primary sources, decolonization, narrative
- Biography modules: quotes, legacy, timeline
- Style modules: exemplar texts, model answers, transformation
- LIT modules: philological analysis, essays, resources

Returns exit code 0 if richness >= threshold, 1 otherwise.
"""

import json
import re
import sys
from pathlib import Path

from calculate_richness_config import (
    DEFAULT_WEIGHTS,
    MODULE_TYPE_TARGETS,
    MODULE_TYPE_WEIGHTS,
)
from calculate_richness_counters import (
    calculate_paragraph_variety,
    calculate_variety_score,
    count_analysis_sections,
    count_citations,
    count_collocations,
    count_cultural_refs,
    count_decolonization,
    count_dialogues,
    count_engagement_boxes,
    count_essays,
    count_examples,
    count_external_yaml_resources,
    count_legacy_refs,
    count_mermaid_diagrams,
    count_primary_sources,
    count_proverbs,
    count_questions,
    count_quotes,
    count_realworld,
    count_register_notes,
    count_resources,
    count_tables,
    count_timeline_markers,
    count_video_embeds,
    count_visual_elements,
)
from calculate_richness_types import (
    extract_level,
    extract_module_type,
    get_prose_content,
)

# Re-export for backward compatibility
__all__ = [
    # Config
    'DEFAULT_WEIGHTS',
    'MODULE_TYPE_TARGETS',
    'MODULE_TYPE_WEIGHTS',
    # Types
    'extract_level',
    'extract_module_type',
    'get_prose_content',
    # Counters
    'calculate_paragraph_variety',
    'calculate_variety_score',
    'count_analysis_sections',
    'count_citations',
    'count_collocations',
    'count_cultural_refs',
    'count_decolonization',
    'count_dialogues',
    'count_engagement_boxes',
    'count_essays',
    'count_examples',
    'count_external_yaml_resources',
    'count_legacy_refs',
    'count_mermaid_diagrams',
    'count_primary_sources',
    'count_proverbs',
    'count_questions',
    'count_quotes',
    'count_realworld',
    'count_register_notes',
    'count_resources',
    'count_tables',
    'count_timeline_markers',
    'count_video_embeds',
    'count_visual_elements',
    # Scoring
    'calculate_richness_score',
    'detect_dryness_flags',
]


def _collect_raw_counts(module_type: str, prose: str, file_path: Path | None,
                        yaml_activity_types: set | None) -> dict:
    """Collect raw content counts based on module type."""
    raw = {
        'engagement': count_engagement_boxes(prose),
        'variety': calculate_variety_score(prose),
        'cultural': count_cultural_refs(prose),
        'visual': count_visual_elements(prose),
        'paragraph_var': calculate_paragraph_variety(prose),
    }

    if module_type == 'beginner':
        raw.update({
            'examples': count_examples(prose),
            'dialogues': count_dialogues(prose),
            'realworld': count_realworld(prose),
            'questions': count_questions(prose),
            'tables': count_tables(prose),
            'video_embeds': count_video_embeds(prose),
        })
    elif module_type == 'grammar':
        raw.update({
            'examples': count_examples(prose),
            'dialogues': count_dialogues(prose),
            'realworld': count_realworld(prose),
            'questions': count_questions(prose),
            'proverbs': count_proverbs(prose),
            'tables': count_tables(prose),
        })
    elif module_type == 'vocabulary':
        raw.update({
            'collocations': count_collocations(prose),
            'usage_examples': count_examples(prose),
            'register_notes': count_register_notes(prose),
        })
    elif module_type == 'history':
        raw.update({
            'primary_sources': count_primary_sources(prose),
            'timeline_markers': count_timeline_markers(prose),
            'decolonization': count_decolonization(prose),
            'questions': count_questions(prose),
        })
    elif module_type == 'biography':
        raw.update({
            'primary_sources': count_primary_sources(prose),
            'quotes': count_quotes(prose),
            'timeline_markers': count_timeline_markers(prose),
            'legacy': count_legacy_refs(prose),
            'questions': count_questions(prose),
        })
    elif module_type == 'academic':
        raw.update({
            'citations': count_citations(prose),
            'data_refs': count_citations(prose),
            'questions': count_questions(prose),
        })
    elif module_type == 'style':
        raw.update({
            'exemplar_texts': count_quotes(prose),
            'model_answers': count_examples(prose),
            'register_analysis': count_register_notes(prose),
        })
    elif module_type == 'literature':
        raw.update({
            'analysis_sections': count_analysis_sections(prose),
            'literary_citations': count_quotes(prose),
            'historical_context': count_timeline_markers(prose),
            'essays': count_essays(prose),
            'resources': count_resources(prose) + count_external_yaml_resources(file_path),
        })
    elif module_type == 'bridge':
        raw.update({
            'examples': count_examples(prose),
            'realworld': count_realworld(prose),
            'questions': count_questions(prose),
            'tables': count_tables(prose),
        })
    elif module_type == 'checkpoint':
        activity_type_count = (
            len(yaml_activity_types) if yaml_activity_types is not None else 8
        )
        raw.update({
            'activity_types': activity_type_count,
            'review_sections': len(re.findall(r'^##\s*[^\n]+', prose, re.MULTILINE)),
        })
    else:
        raw.update({
            'examples': count_examples(prose),
            'realworld': count_realworld(prose),
            'questions': count_questions(prose),
        })

    return raw


def _compute_weighted_score(raw: dict, targets: dict, weights: dict) -> tuple[int, dict, dict]:
    """Compute normalized scores and weighted total.

    Returns:
        Tuple of (score_int, normalized_dict, final_weights_dict).
    """
    normalized = {}
    for key in raw:
        if key in ('variety', 'paragraph_var'):
            normalized[key] = raw[key]
        else:
            target = targets.get(key, 1)
            if target > 0:
                normalized[key] = min(raw[key] / target, 1.0)
            else:
                normalized[key] = 1.0 if raw[key] == 0 else 0.5

    total = 0.0
    for k in normalized:
        weight = weights.get(k, 0.05)
        total += normalized[k] * weight

    weight_sum = sum(weights.get(k, 0.05) for k in normalized)
    if weight_sum > 0:
        total = total / weight_sum

    score = int(total * 100)

    final_weights = {}
    for k in normalized:
        raw_weight = weights.get(k, 0.05)
        final_weights[k] = raw_weight / weight_sum if weight_sum > 0 else 0

    return score, {k: round(v, 2) for k, v in normalized.items()}, final_weights


def calculate_richness_score(
    content: str,
    level: str,
    file_path: Path | None = None,
    yaml_activity_types: set | None = None,
) -> dict:
    """Calculate richness score and components based on module type.

    Args:
        content: Markdown content of the module
        level: CEFR level (A1, A2, B1, B2, C1, C2)
        file_path: Path to the module file (for type detection)
        yaml_activity_types: Set of activity types from YAML file (optional)
    """
    module_type = extract_module_type(content, file_path) if file_path else 'grammar'
    if level in ('A1', 'A2') and module_type in ('grammar', 'vocabulary', 'content'):
        module_type = 'beginner'
    targets = MODULE_TYPE_TARGETS.get(module_type, MODULE_TYPE_TARGETS['grammar'])
    weights = MODULE_TYPE_WEIGHTS.get(module_type, DEFAULT_WEIGHTS)

    prose = get_prose_content(content)
    raw = _collect_raw_counts(module_type, prose, file_path, yaml_activity_types)
    score, normalized, final_weights = _compute_weighted_score(raw, targets, weights)

    return {
        'score': score,
        'threshold': targets.get('threshold', 95),
        'passed': score >= targets.get('threshold', 95),
        'module_type': module_type,
        'raw': raw,
        'normalized': normalized,
        'targets': {k: targets.get(k, 0) for k in raw if k not in ('variety', 'paragraph_var')},
        'weights': final_weights,
    }


def _universal_dryness_flags(prose: str, module_type: str) -> list[str]:
    """Check universal dryness flags that apply to all module types."""
    flags = []

    if count_engagement_boxes(prose) < 2:
        flags.append('NO_ENGAGEMENT')

    wall_threshold = 800 if module_type in ('history', 'biography', 'literature') else 500
    paragraphs = re.split(r'\n\s*\n', prose)
    for p in paragraphs:
        if len(p.split()) > wall_threshold:
            flags.append('WALL_OF_TEXT')
            break

    if calculate_variety_score(prose) < 0.4:
        flags.append('REPETITIVE_STARTERS')

    return flags


def _type_specific_dryness_flags(prose: str, module_type: str, level: str,
                                 file_path: Path | None) -> list[str]:
    """Check dryness flags specific to a module type."""
    flags = []

    if module_type == 'beginner':
        if count_examples(prose) < 6:
            flags.append('NO_EXAMPLES')
    elif module_type == 'bridge':
        if count_examples(prose) < 10:
            flags.append('NO_EXAMPLES')
        if count_realworld(prose) < 1:
            flags.append('ABSTRACT_ONLY')
    elif module_type == 'grammar':
        dialogue_count = count_dialogues(prose)
        if level in ('B1', 'B2', 'C1', 'C2') and dialogue_count < 2:
            flags.append('LOW_DIALOGUE' if dialogue_count > 0 else 'NO_DIALOGUE')
        if count_examples(prose) < 12:
            flags.append('NO_EXAMPLES')
        if count_realworld(prose) < 2:
            flags.append('ABSTRACT_ONLY')
        if level in ('B1', 'B2') and count_proverbs(prose) == 0:
            flags.append('NO_PROVERBS')
    elif module_type == 'vocabulary':
        if count_collocations(prose) < 5:
            flags.append('NO_COLLOCATIONS')
        if count_register_notes(prose) < 2:
            flags.append('NO_REGISTER_NOTES')
    elif module_type == 'history':
        if count_primary_sources(prose) < 2:
            flags.append('NO_PRIMARY_SOURCES')
        if count_timeline_markers(prose) < 5:
            flags.append('NO_TIMELINE')
        if count_decolonization(prose) == 0:
            flags.append('NO_DECOLONIZATION_PERSPECTIVE')
    elif module_type == 'biography':
        if count_quotes(prose) < 2:
            flags.append('NO_QUOTES')
        if count_legacy_refs(prose) < 1:
            flags.append('NO_LEGACY_DISCUSSION')
        if count_timeline_markers(prose) < 5:
            flags.append('NO_TIMELINE')
    elif module_type == 'literature':
        if count_analysis_sections(prose) < 3:
            flags.append('NO_ANALYSIS')
        if count_quotes(prose) < 3:
            flags.append('NO_LITERARY_CITATIONS')
        if count_resources(prose) + count_external_yaml_resources(file_path) < 2:
            flags.append('NO_RESOURCES')
    elif module_type == 'style':
        if count_quotes(prose) < 2:
            flags.append('NO_EXEMPLAR_TEXTS')
        if count_register_notes(prose) < 3:
            flags.append('NO_REGISTER_ANALYSIS')
    elif module_type in ('content', 'cultural'):
        if count_examples(prose) < 8:
            flags.append('NO_EXAMPLES')
        if count_realworld(prose) == 0:
            flags.append('ABSTRACT_ONLY')

    return flags


def detect_dryness_flags(content: str, level: str, file_path: Path | None = None) -> list:
    """Detect dryness indicators based on module type."""
    prose = get_prose_content(content)
    module_type = extract_module_type(content, file_path) if file_path else 'grammar'
    if level in ('A1', 'A2') and module_type in ('grammar', 'vocabulary', 'content'):
        module_type = 'beginner'

    flags = _universal_dryness_flags(prose, module_type)
    flags.extend(_type_specific_dryness_flags(prose, module_type, level, file_path))

    if module_type in ('grammar', 'bridge') and count_tables(prose) == 0:
        flags.append('NO_TABLES')

    if module_type in ('grammar', 'vocabulary', 'content', 'cultural'):
        cultural_count = count_cultural_refs(prose)
        if level in ('B1', 'B2', 'C1', 'C2') and cultural_count < 2:
            flags.append('LOW_CULTURAL_ANCHOR' if cultural_count > 0 else 'NO_CULTURAL_ANCHOR')

    return flags


def _print_score_breakdown(result: dict, weights: dict) -> None:
    """Print formatted score breakdown table."""
    print("### Score Breakdown")
    print("| Metric | Count | Target | Score | Weight | Contribution |")
    print("|--------|-------|--------|-------|--------|--------------|")

    total_contribution = 0.0
    sorted_keys = sorted(
        result['raw'].keys(), key=lambda k: weights.get(k, 0), reverse=True
    )

    for key in sorted_keys:
        raw = result['raw'].get(key, 0)
        norm = result['normalized'].get(key, 0)
        target = result['targets'].get(key, '\u2014')
        weight = weights.get(key, 0.05)
        contribution = norm * weight * 100
        total_contribution += contribution

        if key in ('variety', 'paragraph_var'):
            count_str = f"{raw:.2f}"
            target_str = "-"
        else:
            count_str = str(raw)
            target_str = str(target)

        print(f"| {key} | {count_str} | {target_str} | {norm:.0%} | {weight:.0%} | {contribution:.1f}% |")

    print(f"| **TOTAL** | | | | | **{total_contribution:.1f}%** |")


def main():
    """CLI entry point for richness scoring."""
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python scripts/calculate_richness.py <file> [--json]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    output_json = '--json' in sys.argv

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    level = extract_level(file_path)

    result = calculate_richness_score(content, level, file_path)
    flags = detect_dryness_flags(content, level, file_path)

    if output_json:
        result['flags'] = flags
        print(json.dumps(result, indent=2))
    else:
        module_type = result.get('module_type', 'grammar')
        weights = result.get('weights', DEFAULT_WEIGHTS)

        print(f"Module Type: {module_type}")
        print(f"Richness Score: {result['score']}/100 (threshold: {result['threshold']})")
        print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
        print()
        _print_score_breakdown(result, weights)
        print()

        if flags:
            print("### Dryness Flags")
            for flag in flags:
                print(f"- {flag}")
            if len(flags) >= 2:
                print()
                print("> [!WARNING]")
                print("> 2+ flags: Content needs REWRITE, not just fix")
        else:
            print("Dryness Flags: None")

    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
