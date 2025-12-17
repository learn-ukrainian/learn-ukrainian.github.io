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


def check_quiz_format(content: str) -> list[dict]:
    """Check that quiz activities use numbered items (1. 2. 3.), not bullets (-)."""
    violations = []

    # Find all quiz activities
    quiz_pattern = r'##\s*quiz:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    quizzes = re.findall(quiz_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in quizzes:
        # Check if the quiz uses bullets instead of numbered list
        # Look for question patterns with bullets
        bullet_questions = re.findall(r'^\s*-\s+[^\[]', body, re.MULTILINE)

        # Check for numbered questions
        numbered_questions = re.findall(r'^\s*\d+\.', body, re.MULTILINE)

        # If we have bullet questions but no numbered questions, it's an error
        if bullet_questions and not numbered_questions:
            violations.append({
                'type': 'QUIZ_FORMAT',
                'issue': f"Quiz '{title.strip()}' uses bullets (-) for questions instead of numbered list",
                'fix': "Use numbered items (1. 2. 3.) for quiz questions, not bullets. Format: '1. Question text?\\n   - [x] Correct\\n   - [ ] Wrong'"
            })

        # Check if questions are missing (only checkboxes)
        if not numbered_questions and not bullet_questions:
            # Look for checkboxes without clear question structure
            checkboxes = re.findall(r'^\s*-\s*\[[ xX]\]', body, re.MULTILINE)
            if checkboxes:
                violations.append({
                    'type': 'QUIZ_FORMAT',
                    'issue': f"Quiz '{title.strip()}' has checkboxes but no numbered questions",
                    'fix': "Each quiz question must start with a number (1. Question text?). Options follow with checkboxes."
                })

    return violations


def check_true_false_format(content: str) -> list[dict]:
    """Check that true-false activities don't embed TRUE/FALSE text in statements."""
    violations = []

    # Find all true-false activities
    tf_pattern = r'##\s*true-false:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    tf_activities = re.findall(tf_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in tf_activities:
        lines = body.split('\n')

        for i, line in enumerate(lines):
            # Check for embedded TRUE/FALSE markers in the statement itself
            # Pattern: "— TRUE" or "— FALSE" or "- TRUE" or "- FALSE" within the statement
            if re.search(r'—\s*(TRUE|FALSE|ПРАВДА|МІФ)', line, re.IGNORECASE):
                violations.append({
                    'type': 'TRUE_FALSE_FORMAT',
                    'issue': f"True-false '{title.strip()}' has embedded answer text '—TRUE/FALSE' in statement",
                    'fix': "Remove '— TRUE/FALSE' from statements. Use checkbox format: '- [x]' for true, '- [ ]' for false."
                })
                break  # One violation per activity is enough

            # Check for old format with answer callouts mixed in statement line
            if re.search(r'-\s+.*?\s+(TRUE|FALSE|ПРАВДА|МІФ)\b', line, re.IGNORECASE) and '> [!answer]' in line:
                violations.append({
                    'type': 'TRUE_FALSE_FORMAT',
                    'issue': f"True-false '{title.strip()}' has malformed answer callout in statement line",
                    'fix': "Separate statement and answer. Statement on one line, answer callout on next line."
                })
                break

    return violations


def check_unjumble_format(content: str) -> list[dict]:
    """Check that unjumble activities use > [!answer] callouts, not nested bullets."""
    violations = []

    # Find all unjumble activities
    unjumble_pattern = r'##\s*unjumble:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    unjumbles = re.findall(unjumble_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in unjumbles:
        # Check for old format: nested bullets for answers (- answer or   - answer)
        nested_bullet_answers = re.findall(r'^\s{2,}-\s+[^\[]', body, re.MULTILINE)

        # Check for correct format: > [!answer]
        has_answer_callouts = '> [!answer]' in body

        if nested_bullet_answers and not has_answer_callouts:
            violations.append({
                'type': 'UNJUMBLE_FORMAT',
                'issue': f"Unjumble '{title.strip()}' uses nested bullets for answers instead of callout blocks",
                'fix': "Use '> [!answer]' callout for unjumble answers, not nested bullets. Format: '1. jumbled words\\n   > [!answer] Correct sentence\\n   > (translation) [word count]'"
            })

        # Check if items are missing the required translation and word count
        items = re.findall(r'\d+\.\s+[^\n]+', body)
        for item_text in items:
            # Extract the full item (including subsequent lines until next item or callout)
            if '> [!answer]' in body:
                # Check if answer has translation and word count
                # Pattern: > (translation) [N words]
                if not re.search(r'>\s*\([^)]+\)\s*\[\d+\s+word', body, re.IGNORECASE):
                    # Allow if at least some items have it
                    pass  # Don't flag as error, just informational

    return violations


def check_matchup_format(content: str) -> list[dict]:
    """Check that match-up activities use table format or :: separator."""
    violations = []

    # Find all match-up activities
    matchup_pattern = r'##\s*match-up:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    matchups = re.findall(matchup_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in matchups:
        # Check for table format (| Left | Right |)
        has_table = bool(re.search(r'\|\s*Left\s*\|\s*Right\s*\|', body, re.IGNORECASE))

        # Check for :: separator format (- item :: item)
        has_separator_format = bool(re.search(r'-\s+[^:]+::[^:]+', body))

        # Check for invalid format: bullets without :: or table
        has_bullets = bool(re.findall(r'^\s*-\s+[^\[]', body, re.MULTILINE))

        if has_bullets and not has_table and not has_separator_format:
            # Check if it's just a plain bullet list without proper pairing
            violations.append({
                'type': 'MATCHUP_FORMAT',
                'issue': f"Match-up '{title.strip()}' uses bullets but not table or :: separator format",
                'fix': "Use table format '| Left | Right |' or separator format '- item :: item' for match-up activities."
            })

        # Check if table headers are correct
        if has_table:
            # Verify headers are exactly "Left" and "Right" or localized equivalents
            header_match = re.search(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', body)
            if header_match:
                left_header = header_match.group(1).strip()
                right_header = header_match.group(2).strip()

                valid_headers = [
                    ('Left', 'Right'),
                    ('left', 'right'),
                    ('Ukrainian', 'English'),
                    ('Українська', 'Англійська'),
                    ('Word', 'Translation'),
                    ('Слово', 'Переклад')
                ]

                # Check if headers match any valid pattern
                headers_ok = any(
                    (left_header.lower() == left.lower() and right_header.lower() == right.lower())
                    for left, right in valid_headers
                )

                if not headers_ok and '---' not in body[:100]:
                    # Might not be a table, could be a false positive
                    pass

    return violations


def check_fill_in_format(content: str) -> list[dict]:
    """Check that fill-in activities have both > [!answer] and > [!options]."""
    violations = []

    # Find all fill-in activities
    fill_in_pattern = r'##\s*fill-in:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    fill_ins = re.findall(fill_in_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in fill_ins:
        has_answer = '> [!answer]' in body
        has_options = '> [!options]' in body

        # Check if activity has numbered items
        has_items = bool(re.findall(r'^\s*\d+\.', body, re.MULTILINE))

        if has_items:
            # Count items and answer/options callouts
            items = re.findall(r'^\s*\d+\.', body, re.MULTILINE)
            num_items = len(items)

            num_answers = len(re.findall(r'>\s*\[!answer\]', body))
            num_options = len(re.findall(r'>\s*\[!options\]', body))

            if num_answers == 0:
                violations.append({
                    'type': 'FILL_IN_FORMAT',
                    'issue': f"Fill-in '{title.strip()}' missing '> [!answer]' callouts",
                    'fix': "Each fill-in item must have '> [!answer]' with the correct answer."
                })

            if num_options == 0:
                violations.append({
                    'type': 'FILL_IN_FORMAT',
                    'issue': f"Fill-in '{title.strip()}' missing '> [!options]' callouts",
                    'fix': "Each fill-in item must have '> [!options]' with pipe-separated options."
                })

            # Warn if counts don't match number of items
            if has_answer and num_answers < num_items:
                violations.append({
                    'type': 'FILL_IN_FORMAT',
                    'issue': f"Fill-in '{title.strip()}' has {num_items} items but only {num_answers} answers",
                    'fix': f"Add {num_items - num_answers} more '> [!answer]' callout(s) - one for each item."
                })

            if has_options and num_options < num_items:
                violations.append({
                    'type': 'FILL_IN_FORMAT',
                    'issue': f"Fill-in '{title.strip()}' has {num_items} items but only {num_options} option sets",
                    'fix': f"Add {num_items - num_options} more '> [!options]' callout(s) - one for each item."
                })

        # Check for blank placeholder ___
        if has_items and '___' not in body:
            violations.append({
                'type': 'FILL_IN_FORMAT',
                'issue': f"Fill-in '{title.strip()}' missing '___' blank placeholder in items",
                'fix': "Use '___' to indicate where the blank should be in each sentence."
            })

    return violations


def check_error_correction_format(content: str) -> list[dict]:
    """Check that error-correction activities have required callouts."""
    violations = []

    # Find all error-correction activities
    ec_pattern = r'##\s*error-correction:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    ec_activities = re.findall(ec_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in ec_activities:
        # Check if activity has numbered items
        has_items = bool(re.findall(r'^\s*\d+\.', body, re.MULTILINE))

        if has_items:
            items = re.findall(r'^\s*\d+\.', body, re.MULTILINE)
            num_items = len(items)

            num_errors = len(re.findall(r'>\s*\[!error\]', body))
            num_answers = len(re.findall(r'>\s*\[!answer\]', body))
            num_explanations = len(re.findall(r'>\s*\[!explanation\]', body))

            if num_errors == 0:
                violations.append({
                    'type': 'ERROR_CORRECTION_FORMAT',
                    'issue': f"Error-correction '{title.strip()}' missing '> [!error]' callouts",
                    'fix': "Each error-correction item must have '> [!error]' identifying the wrong word."
                })

            if num_answers == 0:
                violations.append({
                    'type': 'ERROR_CORRECTION_FORMAT',
                    'issue': f"Error-correction '{title.strip()}' missing '> [!answer]' callouts",
                    'fix': "Each error-correction item must have '> [!answer]' with the correct form."
                })

            if num_explanations == 0:
                violations.append({
                    'type': 'ERROR_CORRECTION_FORMAT',
                    'issue': f"Error-correction '{title.strip()}' missing '> [!explanation]' callouts",
                    'fix': "Each error-correction item REQUIRES '> [!explanation]' explaining why it's wrong and the rule."
                })

            # Warn if explanations are missing for some items
            if num_explanations > 0 and num_explanations < num_items:
                violations.append({
                    'type': 'ERROR_CORRECTION_FORMAT',
                    'issue': f"Error-correction '{title.strip()}' has {num_items} items but only {num_explanations} explanations",
                    'fix': "All error-correction items REQUIRE explanations - add missing ones."
                })

    return violations


def check_cloze_format(content: str) -> list[dict]:
    """Check that cloze activities use [___:N] placeholder format."""
    violations = []

    # Find all cloze activities
    cloze_pattern = r'##\s*cloze:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
    cloze_activities = re.findall(cloze_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in cloze_activities:
        # Check for placeholder format [___:N]
        placeholders = re.findall(r'\[___:(\d+)\]', body)

        # Check for old format {N}
        old_placeholders = re.findall(r'\{(\d+)\}', body)

        if old_placeholders and not placeholders:
            violations.append({
                'type': 'CLOZE_FORMAT',
                'issue': f"Cloze '{title.strip()}' uses old placeholder format {{N}}",
                'fix': "Use new format '[___:N]' for cloze placeholders, not '{{N}}'."
            })

        # Check if numbered items match placeholder count
        items = re.findall(r'^\s*\d+\.', body, re.MULTILINE)
        num_items = len(items)
        num_placeholders = len(placeholders)

        if placeholders and num_items != num_placeholders:
            violations.append({
                'type': 'CLOZE_FORMAT',
                'issue': f"Cloze '{title.strip()}' has {num_placeholders} placeholders but {num_items} option sets",
                'fix': f"Placeholder count and option count must match. Check passage and numbered options."
            })

        # Check if items have answers
        num_answers = len(re.findall(r'>\s*\[!answer\]', body))

        if num_items > 0 and num_answers == 0:
            violations.append({
                'type': 'CLOZE_FORMAT',
                'issue': f"Cloze '{title.strip()}' missing '> [!answer]' callouts",
                'fix': "Each cloze option set must have '> [!answer]' identifying the correct option."
            })

    return violations


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
    Check that section headings use H2 (##) not H1 (#).
    
    Docusaurus TOC shows H2-H3 by default. H1 should only be used for
    the page title (ONCE). Any additional H1 headings break the sidebar TOC.
    
    Two checks:
    1. Any H1 after the first one is an error (multiple H1s)
    2. Known section names (warm-up, activities, etc.) must be H2
    """
    violations = []
    
    # Reserved section words that should NOT be H1
    reserved_sections = [
        'warm-up', 'presentation', 'practice', 'cultural',
        'summary', 'activities', 'production', 'vocabulary',
        'reading', 'grammar', 'dialogue', 'підсумок', 'introduction'
    ]
    
    lines = content.split('\n')
    h1_count = 0
    first_h1_line = None
    
    for line_num, line in enumerate(lines, 1):
        # Check for H1 headings (^# but not ^##)
        if line.startswith('# ') and not line.startswith('## '):
            h1_count += 1
            heading = line[2:].strip()
            heading_lower = heading.lower()
            clean_heading = heading[:50] + ('...' if len(heading) > 50 else '')
            
            if h1_count == 1:
                first_h1_line = line_num
                # Still check if first H1 is a reserved section (shouldn't be)
                for reserved in reserved_sections:
                    if reserved in heading_lower:
                        violations.append({
                            'type': 'HEADING_LEVEL',
                            'line': line_num,
                            'issue': f"'{clean_heading}' is a section heading but uses H1 (#)",
                            'fix': f"Change '# {heading}' to '## {heading}' - reserved for page title only"
                        })
                        break
            else:
                # Any H1 after the first is definitely wrong
                violations.append({
                    'type': 'HEADING_LEVEL',
                    'line': line_num,
                    'issue': f"Multiple H1 headings: '{clean_heading}' should be H2 (##)",
                    'fix': f"Only one H1 allowed (page title). Change '# {heading}' to '## {heading}'"
                })
    
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
    
    # Activity format checks
    violations.extend(check_quiz_format(content))
    violations.extend(check_true_false_format(content))
    violations.extend(check_unjumble_format(content))
    violations.extend(check_matchup_format(content))
    violations.extend(check_fill_in_format(content))
    violations.extend(check_error_correction_format(content))
    violations.extend(check_cloze_format(content))

    return violations
