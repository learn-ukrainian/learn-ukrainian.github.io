#!/usr/bin/env python3
"""
Generate human-readable markdown from YAML plans.

Usage:
    .venv/bin/python scripts/generate_plan_markdown.py hist
    .venv/bin/python scripts/generate_plan_markdown.py hist --diff  # Compare with archived

This allows comparing new YAML-based plans with old markdown plans.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml
from slug_utils import to_bare_slug


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def get_modules_in_phase(phase: dict, module_plans: dict) -> list:
    """Get module plans that belong to a phase."""
    _start, _end = phase.get('modules', [0, 0])
    # We need to match by module number - but YAML files don't have numbers
    # We'll need to infer from the level plan or meta files
    return []


def _load_module_plans(module_plans_dir: Path) -> dict:
    """Load all module YAML plans from a directory."""
    module_plans = {}
    if module_plans_dir.exists():
        for yaml_file in sorted(module_plans_dir.glob("*.yaml")):
            plan = load_yaml(yaml_file)
            slug = plan.get('slug') or yaml_file.stem
            module_plans[slug] = plan
    return module_plans


def _load_meta_files(meta_dir: Path) -> dict:
    """Load all meta YAML files from a directory."""
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
    return meta_files


def _build_slug_to_num(
    meta_files: dict,
    module_plans: dict,
    module_plans_dir: Path,
) -> dict[str, int]:
    """Build mapping from slug to module number."""
    slug_to_num: dict[str, int] = {}

    # From meta files (most reliable - have hist-XX format)
    for slug, meta in meta_files.items():
        for field in ['id', 'module']:
            field_val = str(meta.get(field) or '')
            match = re.search(r'-(\d+)$', field_val)
            if match:
                slug_to_num[slug] = int(match.group(1))
                break

    # From plan filenames (often have number prefix)
    for yaml_file in sorted(module_plans_dir.glob("*.yaml")) if module_plans_dir.exists() else []:
        filename = yaml_file.stem
        plan_content = module_plans.get(filename, {})
        if not plan_content:
            stripped = to_bare_slug(filename)
            plan_content = module_plans.get(stripped, {})
        slug = plan_content.get('slug') or filename
        slug = to_bare_slug(slug)
        if slug not in slug_to_num:
            match = re.match(r'^(\d+)-', filename)
            if match:
                slug_to_num[slug] = int(match.group(1))

    # From plan files' module/id fields as fallback
    for slug, plan in module_plans.items():
        if slug not in slug_to_num:
            module_id = plan.get('module') or plan.get('id') or ''
            match = re.search(r'-(\d+)$', module_id)
            if match:
                slug_to_num[slug] = int(match.group(1))

    return slug_to_num


def _render_header(level_plan: dict, level: str, meta_count: int) -> list[str]:
    """Render the markdown header section."""
    lines = []
    track_name = level_plan.get('track', level).title()
    lines.append(f"# {level.upper()} Curriculum Plan: {track_name} Track")
    lines.append("")
    lines.append("**Generated from YAML plans**")
    lines.append(f"**Modules:** {meta_count} module meta files found")

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
    return lines


def _render_overview(level_plan: dict) -> list[str]:
    """Render track overview, vocabulary focus, and pedagogy sections."""
    lines = []
    overview_text = level_plan.get('notes') or level_plan.get('overview', {}).get('description', '')
    if overview_text:
        lines.append("## Track Overview")
        lines.append("")
        lines.append(overview_text.strip())
        lines.append("")

    vocab_focus = level_plan.get('vocabulary', {}).get('focus_areas', [])
    if vocab_focus:
        lines.append("### Vocabulary Focus")
        lines.append("")
        for area in vocab_focus:
            lines.append(f"- {area}")
        lines.append("")

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

    return lines


def _render_phase(
    phase: dict,
    slug_to_num: dict[str, int],
    module_plans: dict,
    meta_files: dict,
) -> list[str]:
    """Render a single phase section."""
    lines = []
    phase_id = phase.get('id', '')
    phase_name = phase.get('name', 'Unknown')
    module_range = phase.get('modules', [0, 0])
    start, end = module_range if len(module_range) == 2 else (0, 0)
    focus = phase.get('focus', '')

    if phase_id:
        phase_header = f"### Phase {phase_id}: {phase_name} (M{start:02d}-{end:02d})"
    else:
        phase_header = f"### {phase_name} (M{start:02d}-{end:02d})"
    lines.append(phase_header)
    lines.append("")

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

    lines.append("| # | Slug | Title (UK) | Word Target | Objectives |")
    lines.append("|---|------|------------|-------------|------------|")

    phase_modules = [
        (num, slug) for slug, num in slug_to_num.items()
        if start <= num <= end
    ]
    phase_modules.sort(key=lambda x: x[0])

    for num, slug in phase_modules:
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
    return lines


def _render_statistics(
    module_plans: dict,
    meta_files: dict,
) -> list[str]:
    """Render summary statistics section."""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## Statistics")
    lines.append("")

    total_words = 0
    total_objectives = 0
    modules_with_outline = 0

    for _slug, plan in module_plans.items():
        if plan.get('word_target'):
            total_words += plan['word_target']
        if plan.get('content_outline'):
            modules_with_outline += 1
        if plan.get('objectives'):
            total_objectives += len(plan['objectives'])

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
    return lines


def _render_module_detail(num: int, slug: str, plan: dict) -> list[str]:
    """Render detail section for a single module."""
    lines = []
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
    return lines


def generate_plan_markdown(level: str, base_path: Path) -> str:
    """Generate markdown from YAML plans."""
    plans_dir = base_path / "curriculum/l2-uk-en/plans"
    level_plan_path = plans_dir / f"{level}.yaml"
    module_plans_dir = plans_dir / level
    meta_dir = base_path / f"curriculum/l2-uk-en/{level}/meta"

    if not level_plan_path.exists():
        raise FileNotFoundError(f"Level plan not found: {level_plan_path}")

    level_plan = load_yaml(level_plan_path)

    module_plans = _load_module_plans(module_plans_dir)
    meta_files = _load_meta_files(meta_dir)
    slug_to_num = _build_slug_to_num(meta_files, module_plans, module_plans_dir)

    # Generate markdown
    lines = []
    lines.extend(_render_header(level_plan, level, len(meta_files)))
    lines.extend(_render_overview(level_plan))

    # Phases
    lines.append("## Phase Structure")
    lines.append("")
    for phase in level_plan.get('phases', []):
        lines.extend(_render_phase(phase, slug_to_num, module_plans, meta_files))

    # Statistics
    lines.extend(_render_statistics(module_plans, meta_files))

    # Module details
    if module_plans:
        lines.append("---")
        lines.append("")
        lines.append("## Module Details (from YAML plans)")
        lines.append("")

        sorted_modules = sorted(
            ((slug_to_num.get(slug, 999), slug, plan)
             for slug, plan in module_plans.items()),
            key=lambda x: x[0],
        )
        for num, slug, plan in sorted_modules:
            lines.extend(_render_module_detail(num, slug, plan))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate markdown from YAML plans")
    parser.add_argument("level", help="Level to generate (e.g., hist, bio)")
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
