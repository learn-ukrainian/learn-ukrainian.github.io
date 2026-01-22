"""
Report generation for module audits.

Generates markdown reports and console output for audit results.
"""

import os
from typing import Optional


def generate_report(
    file_path: str,
    phase: str,
    level_code: str,
    pedagogy: str,
    target: int,
    has_critical_failure: bool,
    results: dict,
    table_rows: list[str],
    lint_errors: list[str],
    pedagogical_violations: list[dict],
    recommendation: str,
    reasons: list[str],
    severity: int,
    low_density_activities: list[dict] = None,
    richness_data: dict = None,
    richness_flags: list = None,
    template_violations: list[dict] = None,
    naturalness: dict = None,
    module_num: int = None,
    config: dict = None,
    activity_details: list[dict] = None,
    unique_types: set = None,
    module_focus: str = None
) -> str:
    """Generate markdown report content."""
    report_lines = []

    # Build header with module number if available
    header_title = f"# Audit Report: {os.path.basename(file_path)}"
    if module_num is not None:
        header_title = f"# Audit Report: M{module_num:02d} — {os.path.basename(file_path)}"
    report_lines.append(header_title)

    # Metadata line with module number
    meta_line = f"**Level:** {level_code}"
    if module_num is not None:
        meta_line += f" | **Module:** M{module_num:02d}"
    meta_line += f" | **Phase:** {phase} | **Pedagogy:** {pedagogy} | **Target:** {target}"
    report_lines.append(meta_line)
    
    # Add Naturalness Score to header if available
    if naturalness:
        score = naturalness.get('score', 0)
        status = naturalness.get('status', 'PENDING')
        report_lines.append(f"**Naturalness:** {score}/10 ({status})")
        
    report_lines.append(f"**Overall Status:** {'❌ FAIL' if has_critical_failure else '✅ PASS'}")
    report_lines.append("")

    # Add Configuration section
    if config:
        report_lines.append("## Configuration")

        # Build config type label
        config_type = f"{level_code}"
        if module_focus:
            config_type += f"-{module_focus}"
        report_lines.append(f"**Type:** {config_type}")

        report_lines.append(f"**Word Target:** {target} words")

        min_act = config.get('min_activities', 0)
        max_act = config.get('max_activities', min_act + 4)
        report_lines.append(f"**Activities:** {min_act}-{max_act} required")

        report_lines.append(f"**Items per Activity:** ≥{config.get('min_items_per_activity', 1)} items")
        report_lines.append(f"**Unique Types:** ≥{config.get('min_types_unique', 2)} types required")

        priority_types = config.get('priority_types', set())
        if priority_types:
            report_lines.append(f"**Priority Types:** {', '.join(sorted(priority_types))}")

        required_types = config.get('required_types', set())
        if required_types:
            report_lines.append(f"**Required Types:** {', '.join(sorted(required_types))}")

        report_lines.append(f"**Engagement:** ≥{config.get('min_engagement', 3)} callouts")

        min_imm = config.get('min_immersion', 0)
        max_imm = config.get('max_immersion', 100)
        report_lines.append(f"**Immersion:** {min_imm}-{max_imm}%")

        report_lines.append(f"**Vocab Target:** ≥{config.get('min_vocab', 25)} words")

        translit = "Not allowed" if not config.get('transliteration_allowed', True) else "Allowed"
        report_lines.append(f"**Transliteration:** {translit}")

        report_lines.append("")

    # Add Activity Breakdown section
    if activity_details:
        report_lines.append("## Activity Breakdown")
        report_lines.append("| # | Type | Title | Items | Min | Status |")
        report_lines.append("|---|------|-------|-------|-----|--------|")

        for idx, act in enumerate(activity_details, 1):
            title = act['title']
            act_type = act['type']
            items = act['items']
            target = act['target']
            status = act['status']
            report_lines.append(f"| {idx} | {act_type} | {title} | {items} | {target} | {status} |")

        report_lines.append("")
        report_lines.append("**Summary:**")

        # Total activities
        total_acts = len(activity_details)
        min_act = config.get('min_activities', 0) if config else 0
        max_act = config.get('max_activities', min_act + 4) if config else total_acts
        act_status = '✅' if min_act <= total_acts <= max_act else '❌'
        report_lines.append(f"- Total activities: {total_acts} (target: {min_act}-{max_act}) {act_status}")

        # Unique types
        if unique_types:
            min_types = config.get('min_types_unique', 2) if config else 2
            types_status = '✅' if len(unique_types) >= min_types else '❌'
            report_lines.append(f"- Unique types: {len(unique_types)} (minimum: {min_types}) {types_status}")

        # Priority types
        if config and config.get('priority_types'):
            priority_types = config['priority_types']
            priority_used = unique_types & priority_types if unique_types else set()
            priority_status = '✅' if priority_used else '❌'
            report_lines.append(f"- Priority types used: {len(priority_used)}/{len(priority_types)} ({', '.join(sorted(priority_used)) if priority_used else 'none'}) {priority_status}")

        # Required types
        if config and config.get('required_types'):
            required_types = config['required_types']
            required_used = unique_types & required_types if unique_types else set()
            all_required_present = required_types.issubset(unique_types) if unique_types else False
            required_status = '✅' if all_required_present else '❌'
            report_lines.append(f"- Required types used: {len(required_used)}/{len(required_types)} ({', '.join(sorted(required_used)) if required_used else 'none'}) {required_status}")

        # Low density count
        low_density_count = sum(1 for act in activity_details if act['status'] == '❌')
        report_lines.append(f"- Low density activities: {low_density_count}")

        report_lines.append("")

    if lint_errors:
        report_lines.append("## LINT ERRORS")
        for err in lint_errors:
            report_lines.append(f"- ❌ {err}")
        report_lines.append("")

    if pedagogical_violations:
        report_lines.append("## PEDAGOGICAL VIOLATIONS")
        for v in pedagogical_violations:
            report_lines.append(f"- **[{v['type']}]** {v['issue']}")
            report_lines.append(f"  - FIX: {v['fix']}")
        report_lines.append("")

    if template_violations:
        report_lines.append("## TEMPLATE COMPLIANCE")
        for v in template_violations:
            severity_icon = "❌" if v['severity'] == 'CRITICAL' else "⚠️"
            report_lines.append(f"- {severity_icon} **[{v['type']}]** {v['issue']}")
            report_lines.append(f"  - FIX: {v['fix']}")
        report_lines.append("")

    if recommendation != 'PASS':
        rec_icon = '🔄' if recommendation == 'REWRITE' else '📝'
        report_lines.append("## Recommendation")
        report_lines.append(f"**{rec_icon} {recommendation}** (severity {severity}/100)")
        report_lines.append("")
        if reasons:
            for reason in reasons:
                report_lines.append(f"- {reason}")
            report_lines.append("")

    report_lines.append("## Gates")
    keys_order = ['words', 'activities', 'density', 'unique_types', 'priority',
                  'engagement', 'audio', 'vocab', 'structure', 'lint', 'pedagogy', 'content_heavy', 'immersion', 'richness', 'grammar', 'naturalness']
    for k in keys_order:
        r = results.get(k)
        if r:
            if hasattr(r, 'icon'):  # GateResult dataclass
                report_lines.append(f"- **{k.capitalize()}:** {r.icon} {r.msg}")
            else:  # dict
                report_lines.append(f"- **{k.capitalize()}:** {r['icon']} {r['msg']}")

    # Add richness details section (B1+ and LIT)
    if richness_data:
        report_lines.append("")
        report_lines.append("## Richness Details")
        score = richness_data.get('score', 0)
        threshold = richness_data.get('threshold', 95)
        report_lines.append(f"**Score:** {score}% (minimum: {threshold}%)")
        report_lines.append(f"**Module Type:** {richness_data.get('module_type', 'unknown')}")
        report_lines.append("")
        report_lines.append("### Score Breakdown")
        raw_counts = richness_data.get('raw', {})
        normalized = richness_data.get('normalized', {})
        targets = richness_data.get('targets', {})
        weights = richness_data.get('weights', {})
        
        if raw_counts:
            report_lines.append("| Metric | Count | Target | Score | Weight | Contribution |")
            report_lines.append("|--------|-------|--------|-------|--------|--------------|")
            total_contribution = 0
            
            # Sort by weight (descending)
            sorted_metrics = sorted(raw_counts.keys(), key=lambda k: weights.get(k, 0), reverse=True)
            
            for metric in sorted_metrics:
                count = raw_counts[metric]
                target = targets.get(metric, '-')
                norm_score = normalized.get(metric, 0)
                weight = weights.get(metric, 0.05)
                contribution = norm_score * weight * 100
                total_contribution += contribution
                # Format values for readability
                if isinstance(count, float):
                    count_str = f"{count:.2f}"
                else:
                    count_str = str(count)
                target_str = str(target) if target != 0 else '-'
                report_lines.append(f"| {metric} | {count_str} | {target_str} | {norm_score:.0%} | {weight:.0%} | {contribution:.1f}% |")
            report_lines.append(f"| **TOTAL** | | | | | **{total_contribution:.1f}%** |")
        if richness_flags:
            report_lines.append("")
            report_lines.append("### Dryness Flags & Fixes")
            flag_fixes = {
                'NO_ENGAGEMENT': '''Add 2+ engagement boxes. Use this exact format:

> 💡 **Чи знали ви?**
>
> [Interesting fact about the grammar/vocabulary topic in Ukrainian]

> 🇺🇦 **Культурний момент**
>
> [Cultural context connecting grammar to Ukrainian life/places]

> 🌍 **У реальному житті**
>
> [Practical scenario where this grammar is used]''',

                'WALL_OF_TEXT': 'Break paragraphs > 500 words. Insert headers (##), bullet lists, or callout boxes every 200-300 words.',

                'REPETITIVE_STARTERS': 'Vary sentence starters. Instead of repeating "Доконаний вид...", use: "Коли...", "Якщо...", "Зверніть увагу:", "Порівняйте:", questions, examples.',

                'NO_DIALOGUE': '''Add 4+ mini-dialogues. Use this exact format:

**Діалог: [Location in Ukraine]**

> — [Speaker 1 line with **bolded** grammar examples]
> — [Speaker 2 response with **bolded** grammar examples]
> — [Speaker 1 continuation]
> — [Speaker 2 conclusion]

Example locations: На Бесарабському ринку, У львівській кав'ярні, В одеському трамваї, На Подолі''',

                'LOW_DIALOGUE': '''Add more mini-dialogues (need 4+ total). Use this exact format:

**Діалог: [Location in Ukraine]**

> — [Speaker 1 line with **bolded** grammar examples]
> — [Speaker 2 response with **bolded** grammar examples]
> — [Speaker 1 continuation]
> — [Speaker 2 conclusion]''',

                'NO_EXAMPLES': 'Add 24+ example sentences. Each grammar point needs 3-4 examples showing the pattern in context.',

                'ABSTRACT_ONLY': '''Add 3+ real-world boxes. Use this exact format:

> 🌍 **У реальному житті**
>
> [Specific scenario: "На співбесіді...", "У магазині...", "На вокзалі..."]
> [Example sentence showing grammar in that context]''',

                'NO_COLLOCATIONS': 'Add 5+ collocations in format: **слово** + noun/verb (e.g., **важка** робота, **приймати** рішення)',

                'NO_REGISTER_NOTES': 'Add register notes: Mark words as (розм.) for colloquial, (офіц.) for formal, (книжн.) for literary.',

                'NO_PRIMARY_SOURCES': '''Add 2+ primary source quotes. Use this format:

> «[Exact quote from historical document]»
> — *[Source name], [year]*''',

                'NO_TIMELINE': 'Add 5+ timeline markers: specific years (1876, 1918), periods (XVIII ст.), sequences (спочатку... потім... нарешті).',

                'NO_DECOLONIZATION_PERSPECTIVE': 'Add Ukrainian perspective on historical events. Avoid Russocentric framing. Use Ukrainian names for cities/people.',

                'NO_QUOTES': '''Add 2+ direct quotes from the subject. Use this format:

> «[Exact quote from the person]»
> — *[Person name], [context/year]*''',

                'NO_LEGACY': 'Add a "Спадщина" or "Вплив" section discussing lasting influence on Ukrainian culture/literature/language.',

                'NO_ANALYSIS': '''Add 3+ analysis section headers. Use keywords in headers:

## 1. Аналіз [topic]: [subtitle]
## 2. Інтерпретація [aspect]: [subtitle]
## 3. Символіка [element]: [subtitle]''',

                'NO_LITERARY_CITATIONS': '''Add 3+ literary citations. Use this exact format:

«[Quote from the literary work, minimum 20 characters]»

Example: «Зібравши троянців в остатки / І швидше прийнявши присягу»''',

                'NO_RESOURCES': '''Add 2+ resource blocks. Use this format:

> [!resources] Додаткові ресурси
>
> - [Resource 1 with link or description]
> - [Resource 2 with link or description]''',

                'NO_EXEMPLAR_TEXTS': '''Add 2+ exemplar text excerpts. Use this format:

**Зразок [style type]:**

> «[Extended quote showing the style, 50+ words]»
> — *[Source]*''',

                'NO_REGISTER_ANALYSIS': 'Add 3+ register analysis notes explaining when to use formal vs informal, written vs spoken variants.',

                'NO_CULTURAL_ANCHOR': '''Add 3+ cultural references. Use this exact format:

> 🇺🇦 **Культурний момент**
>
> [Reference to Ukrainian place (Київ, Львів, Одеса, Карпати), tradition, or custom]
> [How it connects to the grammar/vocabulary being taught]
> [Example sentence using the grammar with cultural context]''',

                'LOW_CULTURAL_ANCHOR': '''Add more cultural references (need 3+ total). Include:
- Named Ukrainian places (Поділ, Бесарабський ринок, Острозька академія)
- Ukrainian traditions or customs
- Contemporary Ukrainian life examples''',

                'NO_PROVERBS': '''Add 1+ Ukrainian proverb. Use this format:

Українці кажу|ть: «[Proverb in Ukrainian]»

Зверніть увагу: **[word]** — [aspect] вид, бо [explanation why this aspect is used].

Example: «Не кажи гоп, поки не перескочиш» — **перескочиш** is perfective because it's about the result.''',
            }
            for flag in richness_flags:
                fix = flag_fixes.get(flag, 'Address this issue to improve richness score')
                report_lines.append(f"- ❌ **{flag}**")
                report_lines.append(f"  - FIX:")
                # Format multi-line fixes properly
                for line in fix.split('\n'):
                    report_lines.append(f"    {line}")

    # Add low density activities section if any
    if low_density_activities:
        report_lines.append("")
        report_lines.append("## Low Density Activities")
        report_lines.append("| Activity | Type | Items | Required | Fix |")
        report_lines.append("|----------|------|-------|----------|-----|")
        for act in low_density_activities:
            title = act['title']
            act_type = act['type']
            items = act['items']
            target = act['target']
            missing = target - items
            fix = f"Add {missing} more items"
            report_lines.append(f"| {title} | {act_type} | {items} | {target} | {fix} |")
        report_lines.append("")

    report_lines.append("")
    report_lines.append("## Section Audit")
    report_lines.append("| Section | Status | Count | Notes |")
    report_lines.append("|---|---|---|---|")
    report_lines.extend(table_rows)

    return "\n".join(report_lines)


def save_report(file_path: str, report_content: str) -> str:
    """
    Save report to audit/ subdirectory.

    Returns the report file path.
    """
    file_dir = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]

    if not file_dir.endswith('audit'):
        target_dir = os.path.join(file_dir, 'audit')
    else:
        target_dir = file_dir

    os.makedirs(target_dir, exist_ok=True)
    report_path = os.path.join(target_dir, f"{base_name}-review.md")

    # Preserve manual content if exists
    manual_content = ""
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                existing_report = f.read()
                if "<!-- MANUAL_NOTES -->" in existing_report:
                    parts = existing_report.split("<!-- MANUAL_NOTES -->")
                    if len(parts) > 1:
                        manual_content = "<!-- MANUAL_NOTES -->" + parts[1]
        except Exception:
            pass

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        if manual_content:
            f.write("\n\n" + manual_content)

    return report_path


def print_gates(results: dict, level_code: str) -> None:
    """Print gate results to console."""
    print(f"\n--- STRICT GATES (Level {level_code}) ---")
    keys_order = ['words', 'activities', 'density', 'unique_types', 'priority',
                  'engagement', 'audio', 'vocab', 'structure', 'lint', 'pedagogy', 'content_heavy', 'grammar', 'naturalness', 'activity_quality']
    for k in keys_order:
        r = results.get(k)
        if r:
            if hasattr(r, 'icon'):  # GateResult dataclass
                print(f"{k.capitalize():<12} {r.icon} {r.msg}")
            else:  # dict
                print(f"{k.capitalize():<12} {r['icon']} {r['msg']}")

    imm = results.get('immersion')
    if imm:
        if hasattr(imm, 'icon'):
            print(f"Immersion    {imm.icon} {imm.msg}")
        else:
            print(f"Immersion    {imm['icon']} {imm['msg']}")

    richness = results.get('richness')
    if richness:
        if hasattr(richness, 'icon'):
            print(f"Richness     {richness.icon} {richness.msg}")
        else:
            print(f"Richness     {richness['icon']} {richness['msg']}")


def print_lint_errors(errors: list[str]) -> None:
    """Print lint errors to console."""
    if errors:
        print("\n❌ LINT ERRORS FOUND:")
        for err in errors:
            print(f"  - {err}")
        print("")


def print_pedagogical_violations(violations: list[dict]) -> None:
    """Print pedagogical violations to console."""
    if violations:
        print("\n📚 PEDAGOGICAL VIOLATIONS FOUND:")
        for v in violations:
            print(f"  [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")
        print("")


def print_template_violations(violations: list[dict]) -> None:
    """Print template compliance violations to console."""
    if violations:
        print("\n📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:")
        for v in violations:
            severity_icon = "🔴" if v['severity'] == 'CRITICAL' else "⚠️"
            print(f"  {severity_icon} [{v['type']}] {v['issue']}")
            print(f"     → FIX: {v['fix']}")
        print("")


def print_recommendation(recommendation: str, reasons: list[str], severity: int) -> None:
    """Print recommendation to console."""
    if recommendation != 'PASS':
        if recommendation == 'REWRITE':
            rec_icon = '🔄'
            rec_color = 'REWRITE FROM SCRATCH'
        else:
            rec_icon = '📝'
            rec_color = 'UPDATE (patch fixes)'

        print(f"\n{rec_icon} RECOMMENDATION: {rec_color} (severity {severity}/100)")
        for reason in reasons:
            print(f"   → {reason}")
        print("")


def print_immersion_fix_hints(
    immersion_score: float,
    min_imm: int,
    max_imm: int,
    level_code: str,
    module_focus: Optional[str] = None
) -> None:
    """Print hints for fixing immersion issues."""
    if immersion_score < min_imm:
        print(f"\n📚 IMMERSION TOO LOW ({immersion_score:.1f}% vs {min_imm}-{max_imm}% target)")
        print(f"   FIX: Convert simple explanations to Ukrainian")
        print(f"   FIX: Add more Ukrainian narratives/dialogues")
        print(f"   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)")
        if level_code in ('B1', 'B2', 'C1', 'C2') or level_code.startswith('B') or level_code.startswith('C'):
            print(f"   FIX: Write grammar rules in Ukrainian (not just examples)")

    elif immersion_score > max_imm:
        print(f"\n📚 IMMERSION TOO HIGH ({immersion_score:.1f}% vs {min_imm}-{max_imm}% target)")
        if level_code == 'A1':
            print(f"   FIX: Add English phonetic/alphabet explanations")
            print(f"   FIX: Expand English grammar theory sections")
            print(f"   FIX: Learner can't read Cyrillic yet - needs more English scaffolding")
        elif level_code == 'A2':
            print(f"   FIX: Add English explanations for case/aspect theory")
            print(f"   FIX: Expand English scaffolding for complex grammar")
        elif module_focus == 'grammar':
            print(f"   FIX: Add English grammar theory (this is a grammar-focused module)")
            print(f"   FIX: Explain complex concepts in English first, then Ukrainian examples")
            print(f"   FIX: Add 🔗 Language Link boxes comparing Ukrainian/English")
        else:
            print(f"   FIX: Add English context where needed")
            print(f"   FIX: Ensure translations are provided for complex passages")


def print_low_density_activities(low_density_activities: list[dict]) -> None:
    """Print which activities have insufficient items and how to fix them."""
    if not low_density_activities:
        return

    print(f"\n📊 ACTIVITIES WITH LOW DENSITY:")
    for act in low_density_activities:
        title = act['title']
        act_type = act['type']
        items = act['items']
        target = act['target']
        missing = target - items

        print(f"  ❌ {title}")
        print(f"     Current: {items} items | Required: {target} | Add: {missing} more")

        # Type-specific suggestions
        if act_type == 'fill-in':
            print(f"     → Add {missing} more gap-fill sentences with [blank] placeholders")
        elif act_type == 'match-up':
            print(f"     → Add {missing} more matching pairs (Ukrainian ↔ English)")
        elif act_type == 'quiz':
            print(f"     → Add {missing} more multiple-choice questions")
        elif act_type == 'true-false':
            print(f"     → Add {missing} more true/false statements")
        elif act_type == 'unjumble':
            print(f"     → Add {missing} more sentences to unscramble")
        elif act_type == 'group-sort':
            print(f"     → Add {missing} more items to sort into categories")
        elif act_type == 'error-correction':
            print(f"     → Add {missing} more sentences with errors to find")
        elif act_type == 'cloze':
            print(f"     → Add {missing} more blanks in the passage")
        elif act_type == 'anagram':
            print(f"     → Add {missing} more words to unscramble")
        elif act_type == 'translate':
            print(f"     → Add {missing} more translation items")
        elif act_type == 'mark-the-words':
            print(f"     → Add {missing} more words to mark in the text")
        elif act_type == 'select':
            print(f"     → Add {missing} more multi-select questions")
        else:
            print(f"     → Add {missing} more items to this activity")
    print("")


def append_mdx_errors_to_report(
    md_file_path: str,
    errors: list[str],
    warnings: list[str]
) -> bool:
    """
    Append MDX validation results to an existing review file.

    Args:
        md_file_path: Path to the source markdown file (used to find review file)
        errors: List of error messages from MDX validation
        warnings: List of warning messages from MDX validation

    Returns:
        True if successfully updated, False otherwise.
    """
    # Find the review file
    file_dir = os.path.dirname(os.path.abspath(md_file_path))
    file_name = os.path.basename(md_file_path)
    base_name = os.path.splitext(file_name)[0]

    if not file_dir.endswith('audit'):
        target_dir = os.path.join(file_dir, 'audit')
    else:
        target_dir = file_dir

    report_path = os.path.join(target_dir, f"{base_name}-review.md")

    if not os.path.exists(report_path):
        # No review file exists - only create if there are actual issues
        if not errors and not warnings:
            return True  # Nothing to report, don't create file
        os.makedirs(target_dir, exist_ok=True)
        mdx_section = _format_mdx_section(errors, warnings)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Audit Report: {file_name}\n\n{mdx_section}")
        return True

    # Read existing report
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove existing MDX section if present
    import re
    content = re.sub(
        r'\n## MDX VALIDATION[\s\S]*?(?=\n## |\n<!-- MANUAL_NOTES -->|$)',
        '',
        content
    )

    # Find insertion point (after Gates section, before Section Audit)
    insertion_point = content.find('\n## Section Audit')
    if insertion_point == -1:
        # Fallback: insert before manual notes or at end
        insertion_point = content.find('<!-- MANUAL_NOTES -->')
        if insertion_point == -1:
            insertion_point = len(content)

    # Build MDX section
    mdx_section = _format_mdx_section(errors, warnings)

    # Insert MDX section
    new_content = content[:insertion_point] + mdx_section + content[insertion_point:]

    # Write updated report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def _format_mdx_section(errors: list[str], warnings: list[str]) -> str:
    """Format MDX validation results as markdown section."""
    lines = ["\n## MDX VALIDATION"]

    if errors:
        lines.append("### Errors")
        for err in errors:
            lines.append(f"- ❌ {err}")

    if warnings:
        lines.append("### Warnings")
        for warn in warnings:
            lines.append(f"- ⚠️ {warn}")

    if not errors and not warnings:
        lines.append("✅ No issues found")

    lines.append("")
    return "\n".join(lines)


def append_html_errors_to_report(
    md_file_path: str,
    errors: list[str],
    warnings: list[str],
    activities_found: int = 0
) -> bool:
    """
    Append HTML validation results to an existing review file.

    Args:
        md_file_path: Path to the source markdown file (used to find review file)
        errors: List of error messages from HTML validation
        warnings: List of warning messages from HTML validation
        activities_found: Number of interactive elements found

    Returns:
        True if successfully updated, False otherwise.
    """
    # Find the review file
    file_dir = os.path.dirname(os.path.abspath(md_file_path))
    file_name = os.path.basename(md_file_path)
    base_name = os.path.splitext(file_name)[0]

    if not file_dir.endswith('audit'):
        target_dir = os.path.join(file_dir, 'audit')
    else:
        target_dir = file_dir

    report_path = os.path.join(target_dir, f"{base_name}-review.md")

    if not os.path.exists(report_path):
        # No review file exists - only create if there are actual issues
        if not errors and not warnings:
            return True  # Nothing to report, don't create file
        os.makedirs(target_dir, exist_ok=True)
        html_section = _format_html_section(errors, warnings, activities_found)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Audit Report: {file_name}\n\n{html_section}")
        return True

    # Read existing report
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove existing HTML section if present
    import re
    content = re.sub(
        r'\n## HTML VALIDATION[\s\S]*?(?=\n## |\n<!-- MANUAL_NOTES -->|$)',
        '',
        content
    )

    # Find insertion point (after MDX VALIDATION or Gates, before Section Audit)
    insertion_point = content.find('\n## Section Audit')
    if insertion_point == -1:
        # Try after MDX VALIDATION
        mdx_match = re.search(r'\n## MDX VALIDATION[\s\S]*?(?=\n## |$)', content)
        if mdx_match:
            insertion_point = mdx_match.end()
        else:
            # Fallback: insert before manual notes or at end
            insertion_point = content.find('<!-- MANUAL_NOTES -->')
            if insertion_point == -1:
                insertion_point = len(content)

    # Build HTML section
    html_section = _format_html_section(errors, warnings, activities_found)

    # Insert HTML section
    new_content = content[:insertion_point] + html_section + content[insertion_point:]

    # Write updated report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def _format_html_section(errors: list[str], warnings: list[str], activities_found: int) -> str:
    """Format HTML validation results as markdown section."""
    lines = ["\n## HTML VALIDATION"]

    if errors:
        lines.append("### Errors")
        for err in errors:
            lines.append(f"- ❌ {err}")

    if warnings:
        lines.append("### Warnings")
        for warn in warnings:
            lines.append(f"- ⚠️ {warn}")

    if not errors and not warnings:
        lines.append(f"✅ Renders correctly ({activities_found} interactive elements)")

    lines.append("")
    return "\n".join(lines)
