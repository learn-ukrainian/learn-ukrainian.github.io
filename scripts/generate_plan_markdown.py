#!/usr/bin/env python3
"""
Generate human-readable markdown from YAML plans.

Usage:
    .venv/bin/python scripts/generate_plan_markdown.py b2-hist
    .venv/bin/python scripts/generate_plan_markdown.py b2-hist --diff  # Compare with archived

This allows comparing new YAML-based plans with old markdown plans.
"""

import argparse
import re
import sys
from pathlib import Path

from slug_utils import to_bare_slug
import yaml
import subprocess


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def get_modules_in_phase(phase: dict, module_plans: dict) -> list:
    """Get module plans that belong to a phase."""
    start, end = phase.get('modules', [0, 0])
    # We need to match by module number - but YAML files don't have numbers
    # We'll need to infer from the level plan or meta files
    return []


def generate_plan_markdown(level: str, base_path: Path) -> str:
    """Generate markdown from YAML plans."""
    plans_dir = base_path / "curriculum/l2-uk-en/plans"
    level_plan_path = plans_dir / f"{level}.yaml"
    module_plans_dir = plans_dir / level

    # Also check meta files for additional info
    meta_dir = base_path / f"curriculum/l2-uk-en/{level}/meta"

    if not level_plan_path.exists():
        raise FileNotFoundError(f"Level plan not found: {level_plan_path}")

    level_plan = load_yaml(level_plan_path)

    # Load all module plans
    module_plans = {}
    if module_plans_dir.exists():
        for yaml_file in sorted(module_plans_dir.glob("*.yaml")):
            plan = load_yaml(yaml_file)
            # Use slug from file content, or filename as fallback
            slug = plan.get('slug') or yaml_file.stem
            module_plans[slug] = plan

    # Load all meta files for additional info (like module numbers)
    meta_files = {}
    if meta_dir.exists():
        for yaml_file in sorted(meta_dir.glob("*.yaml")):
            try:
                meta = load_yaml(yaml_file)
                if meta:
                    slug = meta.get('slug') or yaml_file.stem
                    meta_files[slug] = meta
            except Exception:
                pass

    # Build slug to number mapping - prefer meta files as they have proper IDs
    slug_to_num = {}

    # First, build from meta files (most reliable - have b2-hist-XX format)
    for slug, meta in meta_files.items():
        # Try multiple fields - prefer ones with number format
        for field in ['id', 'module']:
            field_val = str(meta.get(field) or '')
            match = re.search(r'-(\d+)$', field_val)
            if match:
                slug_to_num[slug] = int(match.group(1))
                break

    # For plan files, also try the filename which often has the number prefix
    for yaml_file in sorted(module_plans_dir.glob("*.yaml")) if module_plans_dir.exists() else []:
        filename = yaml_file.stem
        # Try to get slug from the plan file content first
        plan_content = module_plans.get(filename, {})
        if not plan_content:
            # filename might have number prefix, try stripping it
            stripped = to_bare_slug(filename)
            plan_content = module_plans.get(stripped, {})
        slug = plan_content.get('slug') or filename
        # Normalize slug by stripping number prefix
        slug = to_bare_slug(slug)
        if slug not in slug_to_num:
            # Try filename pattern like "01-trypillian-civilization"
            match = re.match(r'^(\d+)-', filename)
            if match:
                slug_to_num[slug] = int(match.group(1))

    # Also check plan files' module/id fields as fallback
    for slug, plan in module_plans.items():
        if slug not in slug_to_num:
            module_id = plan.get('module') or plan.get('id') or ''
            match = re.search(r'-(\d+)$', module_id)
            if match:
                slug_to_num[slug] = int(match.group(1))

    # Generate markdown
    lines = []

    # Header
    track_name = level_plan.get('track', level).title()
    lines.append(f"# {level.upper()} Curriculum Plan: {track_name} Track")
    lines.append("")
    lines.append(f"**Generated from YAML plans**")
    lines.append(f"**Modules:** {len(meta_files)} module meta files found")

    # Try multiple locations for prerequisites
    prereq = level_plan.get('prerequisite') or level_plan.get('overview', {}).get('prerequisites', [])
    if isinstance(prereq, list):
        prereq = ', '.join(str(p).upper() for p in prereq) if prereq else 'N/A'
    lines.append(f"**Prerequisite:** {prereq}")

    vocab_target = level_plan.get('vocabulary_target') or level_plan.get('vocabulary', {}).get('new_words', 'N/A')
    lines.append(f"**Vocabulary Target:** {vocab_target}")

    immersion = level_plan.get('immersion') or level_plan.get('constraints', {}).get('immersion_target', 'N/A')
    if immersion and immersion != 'N/A':
        immersion = f"{float(immersion) * 100:.0f}%" if isinstance(immersion, (int, float)) else immersion
    lines.append(f"**Immersion:** {immersion}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Track overview - check multiple possible locations
    overview_text = level_plan.get('notes') or level_plan.get('overview', {}).get('description', '')
    if overview_text:
        lines.append("## Track Overview")
        lines.append("")
        lines.append(overview_text.strip())
        lines.append("")

    # Vocabulary focus areas
    vocab_focus = level_plan.get('vocabulary', {}).get('focus_areas', [])
    if vocab_focus:
        lines.append("### Vocabulary Focus")
        lines.append("")
        for area in vocab_focus:
            lines.append(f"- {area}")
        lines.append("")

    # Pedagogy notes
    pedagogy = level_plan.get('pedagogy_notes', {})
    if pedagogy:
        lines.append("### Pedagogical Approach")
        lines.append("")
        if pedagogy.get('approach'):
            lines.append(f"**Approach:** {pedagogy['approach']}")
        if pedagogy.get('structure'):
            lines.append("")
            lines.append("**Structure:**")
            for item in pedagogy['structure']:
                lines.append(f"- {item}")
        if pedagogy.get('decolonization'):
            lines.append("")
            lines.append("**Decolonization:**")
            for item in pedagogy['decolonization']:
                lines.append(f"- {item}")
        lines.append("")

    if overview_text or vocab_focus or pedagogy:
        lines.append("---")
        lines.append("")

    # Phases
    lines.append("## Phase Structure")
    lines.append("")

    phases = level_plan.get('phases', [])
    for phase in phases:
        phase_id = phase.get('id', '')
        phase_name = phase.get('name', 'Unknown')
        module_range = phase.get('modules', [0, 0])
        start, end = module_range if len(module_range) == 2 else (0, 0)
        focus = phase.get('focus', '')
        era = phase.get('era', '')

        # Format phase header: use ID if available, otherwise just name
        if phase_id:
            phase_header = f"### Phase {phase_id}: {phase_name} (M{start:02d}-{end:02d})"
        else:
            phase_header = f"### {phase_name} (M{start:02d}-{end:02d})"
        lines.append(phase_header)
        lines.append("")

        # Add phase metadata (author, focus, key_works) if available
        author = phase.get('author', '')
        key_works = phase.get('key_works', [])
        if focus:
            lines.append(f"**Focus:** {focus}")
        if author:
            lines.append(f"**Author:** {author}")
        if key_works:
            lines.append(f"**Key Works:** {', '.join(key_works)}")
        if focus or author or key_works:
            lines.append("")

        # Table header
        lines.append("| # | Slug | Title (UK) | Word Target | Objectives |")
        lines.append("|---|------|------------|-------------|------------|")

        # Find modules in this range
        phase_modules = []
        for slug, num in slug_to_num.items():
            if start <= num <= end:
                phase_modules.append((num, slug))

        phase_modules.sort(key=lambda x: x[0])

        for num, slug in phase_modules:
            # Get info from module plan or meta
            plan = module_plans.get(slug, {})
            meta = meta_files.get(slug, {})

            title = plan.get('title') or meta.get('title') or slug
            word_target = plan.get('word_target') or meta.get('word_target') or '-'
            objectives = plan.get('objectives') or meta.get('objectives') or []
            obj_count = len(objectives) if isinstance(objectives, list) else 0

            lines.append(f"| {num:02d} | {slug} | {title} | {word_target} | {obj_count} obj |")

        if not phase_modules:
            lines.append("| - | (no modules found in range) | - | - | - |")

        lines.append("")

    # Summary statistics
    lines.append("---")
    lines.append("")
    lines.append("## Statistics")
    lines.append("")

    total_words = 0
    total_objectives = 0
    modules_with_outline = 0

    for slug, plan in module_plans.items():
        if plan.get('word_target'):
            total_words += plan['word_target']
        if plan.get('content_outline'):
            modules_with_outline += 1
        if plan.get('objectives'):
            total_objectives += len(plan['objectives'])

    # Also count from meta if plan is sparse
    for slug, meta in meta_files.items():
        if slug not in module_plans:
            if meta.get('word_target'):
                total_words += meta['word_target']
            if meta.get('objectives'):
                total_objectives += len(meta['objectives'])

    lines.append(f"- **Module plans (YAML):** {len(module_plans)}")
    lines.append(f"- **Meta files:** {len(meta_files)}")
    lines.append(f"- **Modules with content_outline:** {modules_with_outline}")
    lines.append(f"- **Total word target:** {total_words:,}")
    lines.append(f"- **Total objectives:** {total_objectives}")
    lines.append("")

    # Detail section - show content outlines
    if module_plans:
        lines.append("---")
        lines.append("")
        lines.append("## Module Details (from YAML plans)")
        lines.append("")

        # Sort by module number if possible
        sorted_modules = []
        for slug, plan in module_plans.items():
            num = slug_to_num.get(slug, 999)
            sorted_modules.append((num, slug, plan))
        sorted_modules.sort(key=lambda x: x[0])

        for num, slug, plan in sorted_modules:
            title = plan.get('title', slug)
            lines.append(f"### M{num:02d}: {title}")
            lines.append("")

            if plan.get('subtitle'):
                lines.append(f"*{plan['subtitle']}*")
                lines.append("")

            if plan.get('objectives'):
                lines.append("**Objectives:**")
                for obj in plan['objectives']:
                    lines.append(f"- {obj}")
                lines.append("")

            if plan.get('content_outline'):
                lines.append("**Content Outline:**")
                lines.append("")
                lines.append("| Section | Words |")
                lines.append("|---------|-------|")
                for section in plan['content_outline']:
                    sec_name = section.get('section', '-')
                    sec_words = section.get('words', '-')
                    lines.append(f"| {sec_name} | {sec_words} |")
                lines.append("")
                lines.append(f"**Total:** {plan.get('word_target', '-')} words")
                lines.append("")

            if plan.get('grammar'):
                # Handle grammar items that might be strings or dicts
                grammar_items = []
                for g in plan['grammar']:
                    if isinstance(g, dict):
                        grammar_items.append(g.get('point') or g.get('name') or str(g))
                    else:
                        grammar_items.append(str(g))
                lines.append(f"**Grammar:** {', '.join(grammar_items)}")
                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate markdown from YAML plans")
    parser.add_argument("level", help="Level to generate (e.g., b2-hist, c1-bio)")
    parser.add_argument("--diff", action="store_true", help="Compare with archived plan")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    base_path = Path(__file__).parent.parent

    try:
        markdown = generate_plan_markdown(args.level, base_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown)
        print(f"Written to {output_path}")
    elif args.diff:
        # Write to temp file and diff with archived
        import tempfile
        archive_path = base_path / f"docs/l2-uk-en/_archive/{args.level.upper()}-CURRICULUM-PLAN.md"

        if not archive_path.exists():
            # Try without uppercase
            archive_path = base_path / f"docs/l2-uk-en/_archive/{args.level}-CURRICULUM-PLAN.md"

        if not archive_path.exists():
            print(f"Warning: Archived plan not found at {archive_path}", file=sys.stderr)
            print(markdown)
            sys.exit(0)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(markdown)
            tmp_path = tmp.name

        print(f"=== DIFF: {archive_path.name} (old) vs generated (new) ===")
        print()

        # Use diff with context
        result = subprocess.run(
            ['diff', '-u', '--color=always', str(archive_path), tmp_path],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Cleanup
        Path(tmp_path).unlink()
    else:
        print(markdown)


if __name__ == "__main__":
    main()
