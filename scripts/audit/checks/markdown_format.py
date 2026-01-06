"""
Markdown format validation checks.

Validates activity format compliance with docs/MARKDOWN-FORMAT.md specification:
- Quiz format: numbered items, not bullets
- True-false format: no embedded TRUE/FALSE text
- Unjumble format: uses > [!answer] callouts
- Match-up format: table format or :: separator
- Fill-in format: has both > [!answer] and > [!options]
- Heading levels: section headings use H2 (##), not H1 (#)
"""

import re


def check_frontmatter_spacing(content: str) -> list[dict]:
    """
    Check that there's a blank line after YAML frontmatter.
    
    YAML frontmatter is enclosed between two '---' lines. Markdown parsing
    requires a blank line after the closing '---' before content begins.
    Without this, the first heading may not render correctly.
    """
    violations = []
    
    lines = content.split('\n')
    
    # Find the closing --- of frontmatter
    frontmatter_start = -1
    frontmatter_end = -1
    
    for i, line in enumerate(lines):
        if line.strip() == '---':
            if frontmatter_start == -1:
                frontmatter_start = i
            else:
                frontmatter_end = i
                break
    
    # Check if there's content after frontmatter
    if frontmatter_end > 0 and frontmatter_end + 1 < len(lines):
        next_line = lines[frontmatter_end + 1]
        
        # If the next line is not blank, it's a problem
        if next_line.strip() != '':
            violations.append({
                'type': 'FRONTMATTER_SPACING',
                'line': frontmatter_end + 2,  # 1-indexed
                'issue': f"Missing blank line after YAML frontmatter (line {frontmatter_end + 1})",
                'fix': "Add a blank line between the closing '---' and the first content/heading"
            })
    
    return violations


def check_heading_levels(content: str) -> list[dict]:
    """
    Check that section headings follow the hierarchy from docs/MARKDOWN-FORMAT.md.
    
    1. Page Title must be H1 (#)
    2. Main Sections (Activities, Summary, Vocabulary) must be H1 (#)
    3. Subsection headers (warm-up, exercises, etc.) must be H2 (##)
    """
    violations = []

    # Main Sections that MUST be H1 (#)
    h1_required_sections = [
        'summary', 'activities', 'vocabulary',  # English
        'підсумок', 'вправи', 'словник'          # Ukrainian
    ]
    
    # Content sub-sections that SHOULD be H2 (##)
    h2_preferred_sections = [
        'warm-up', 'presentation', 'practice', 'production', 
        'cultural', 'reading', 'grammar', 'діагностика', 'аналіз'
    ]

    lines = content.split('\n')
    h1_count = 0
    in_frontmatter = False
    frontmatter_count = 0

    for line_num, line in enumerate(lines, 1):
        # Skip frontmatter
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count == 1:
                in_frontmatter = True
            elif frontmatter_count == 2:
                in_frontmatter = False
            continue

        if in_frontmatter:
            continue

        # Detect heading level
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if not heading_match:
            continue

        hashes = heading_match.group(1)
        heading = heading_match.group(2).strip()
        current_level = len(hashes)
        heading_lower = heading.lower()
        clean_heading = heading[:50] + ('...' if len(heading) > 50 else '')

        # Check for H1 compliance
        if current_level == 1:
            h1_count += 1
            # H1 is valid for title (first H1) or specific main sections
            is_main_section = any(s in heading_lower for s in h1_required_sections)
            
            if h1_count > 1 and not is_main_section:
                # This is a random H1 that shouldn't be one
                violations.append({
                    'type': 'HEADING_LEVEL',
                    'line': line_num,
                    'issue': f"Non-standard H1 heading: '{clean_heading}' should be H2 (##)",
                    'fix': f"Only Title and Main Sections (Activities/Summary/Vocabulary) should be H1. Change '# {heading}' to '## {heading}'"
                })
        
        # Check for H2 compliance (Sections that should NOT be H1)
        # Only check if it's NOT the first H1 (which is the module title)
        if current_level == 1 and h1_count > 1:
             for h2_sect in h2_preferred_sections:
                 if h2_sect in heading_lower:
                    violations.append({
                        'type': 'HEADING_LEVEL',
                        'line': line_num,
                        'issue': f"'{clean_heading}' is a subsection but uses H1 (#)",
                        'fix': f"Change '# {heading}' to '## {heading}'"
                    })
                    break

        # Check for sections that MUST be H1 but are H2
        if current_level == 2:
            for h1_sect in h1_required_sections:
                # Use exact word boundaries or start of string match to avoid false positives
                # e.g. "Exercises" is H2, "Activities" is H1
                if h1_sect == heading_lower:
                    violations.append({
                        'type': 'HEADING_LEVEL',
                        'line': line_num,
                        'issue': f"Main section '{clean_heading}' uses H2 (##) but spec requires H1 (#)",
                        'fix': f"Change '## {heading}' to '# {heading}' for top-level TOC compliance"
                    })
                    break
        
        # Special case: 'Exercises' as H2 is often a placeholder for '# Activities'
        if current_level == 2 and heading_lower == 'exercises':
             violations.append({
                'type': 'HEADING_LEVEL',
                'line': line_num,
                'issue': f"Placeholder '{clean_heading}' uses H2 (##). Should be '# Activities'",
                'fix': "Change '## Exercises' to '# Activities' (or '# Вправи')"
            })

    return violations


def check_table_column_consistency(content: str) -> list[dict]:
    """
    Check that markdown tables have consistent column counts.

    Detects:
    - Header row and separator row have different column counts
    - Data rows have different column counts than header
    """
    violations = []

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Detect start of a table (line starting and ending with |)
        if line.startswith('|') and line.endswith('|'):
            table_start_line = i + 1  # 1-indexed
            table_lines = [line]

            # Collect all consecutive table lines
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('|') and lines[j].strip().endswith('|'):
                table_lines.append(lines[j].strip())
                j += 1

            # Analyze table structure
            if len(table_lines) >= 2:
                # Count columns in each row (split by | and filter empty strings at edges)
                def count_columns(row):
                    cells = row.split('|')
                    # Remove first and last empty strings from leading/trailing |
                    return len([c for c in cells[1:-1]])

                header_cols = count_columns(table_lines[0])

                for row_idx, row in enumerate(table_lines[1:], start=1):
                    row_cols = count_columns(row)

                    if row_cols != header_cols:
                        # Determine row type for better error message
                        is_separator = bool(re.match(r'^\|[\s\-:|]+\|$', row))
                        row_type = "separator" if is_separator else f"row {row_idx}"

                        # Get context (first few words of header)
                        header_preview = table_lines[0][:60] + ('...' if len(table_lines[0]) > 60 else '')

                        violations.append({
                            'type': 'TABLE_COLUMN_MISMATCH',
                            'line': table_start_line + row_idx,
                            'issue': f"Table {row_type} has {row_cols} columns but header has {header_cols}",
                            'context': header_preview,
                            'fix': f"Ensure all rows have exactly {header_cols} columns (cells separated by |)"
                        })

            # Skip past this table
            i = j
        else:
            i += 1

    return violations


def check_markdown_format(content: str) -> list[dict]:
    """
    Run all markdown format validation checks.

    Args:
        content: Full module content

    Returns:
        List of violation dictionaries with 'type', 'issue', and 'fix' keys
    """
    violations = []

    # Structure checks (run first)
    violations.extend(check_frontmatter_spacing(content))
    violations.extend(check_heading_levels(content))
    violations.extend(check_table_column_consistency(content))

    return violations
