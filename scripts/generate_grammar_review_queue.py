#!/usr/bin/env python3
"""
Generate Grammar Review Queue

Extracts NLP/grammar warnings from audit output and formats them
for manual validation in Antigravity IDE with Gemini.

Usage:
    # Run audit and capture warnings
    python scripts/audit_module.py curriculum/l2-uk-en/a2/05-*.md > audit_output.txt

    # Generate review queue from audit output
    python scripts/generate_grammar_review_queue.py audit_output.txt > grammar_review_queue.md

    # Or run directly on a module
    python scripts/generate_grammar_review_queue.py curriculum/l2-uk-en/a2/05-*.md
"""

import sys
import re
from pathlib import Path
from datetime import datetime

def extract_activities_with_context(module_path: Path) -> list[dict]:
    """
    Extract all activities from a module with surrounding context.

    Returns list of activities with:
    - activity_type
    - title
    - body (full activity text)
    - line_number (approximate)
    - ukrainian_sentences (extracted for review)
    """
    content = module_path.read_text(encoding='utf-8')
    activities = []

    # Pattern: ## activity-type: Title
    activity_pattern = r'##\s*([a-z-]+):\s*([^\n]+)\n(.*?)(?=\n##\s|\n#\s|\Z)'
    matches = re.finditer(activity_pattern, content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        act_type = match.group(1).lower()
        title = match.group(2).strip()
        body = match.group(3)

        # Estimate line number
        line_num = content[:match.start()].count('\n') + 1

        # Extract Ukrainian sentences (very simple extraction)
        # Remove markdown syntax and extract Cyrillic text
        sentences = []
        for line in body.split('\n'):
            # Skip callout lines
            if '[!' in line:
                continue
            # Extract Cyrillic sentences
            cyrillic_matches = re.findall(r'[А-ЯІЇЄҐа-яіїєґ][^.!?]*[.!?]', line)
            sentences.extend(cyrillic_matches)

        activities.append({
            'type': act_type,
            'title': title,
            'body': body,
            'line_number': line_num,
            'sentences': sentences,
        })

    return activities


def extract_level_from_path(module_path: Path) -> str:
    """Extract level (a1, a2, b1) from file path."""
    parts = module_path.parts
    for part in parts:
        if part.lower() in ('a1', 'a2', 'b1', 'b2', 'c1', 'c2'):
            return part.upper()
    return 'UNKNOWN'


def generate_review_queue(module_path: Path) -> str:
    """
    Generate a grammar review queue document for manual Gemini validation.

    For now, this extracts ALL activities as potential review items.
    Later, we can integrate with nlp_uk to only extract flagged issues.
    """
    level = extract_level_from_path(module_path)
    module_name = module_path.stem

    output = []
    output.append(f"# Grammar Review Queue - {level} {module_name}")
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append(f"Source: `{module_path}`")
    output.append("")
    output.append("---")
    output.append("")
    output.append("## Instructions")
    output.append("")
    output.append("1. Copy each issue below")
    output.append("2. Paste into Gemini in Antigravity IDE")
    output.append("3. Include the Ukrainian Grammar Validator prompt (see `scripts/audit/ukrainian_grammar_validator_prompt.md`)")
    output.append("4. Review Gemini's validation response")
    output.append("5. Fix confirmed errors in the module")
    output.append("")
    output.append("---")
    output.append("")

    activities = extract_activities_with_context(module_path)

    issue_num = 1
    for activity in activities:
        # For error-correction activities, extract the error sentences
        if activity['type'] == 'error-correction':
            # Parse error-correction format
            items = re.findall(
                r'(\d+)\.\s*([^\n>]+)\n\s*>\s*\[!error\]\s*([^\n]+)\n\s*>\s*\[!answer\]\s*([^\n]+)',
                activity['body']
            )

            for item_num, error_sentence, error_word, correct_word in items:
                output.append(f"## Issue {issue_num}: Error-Correction Activity")
                output.append("")
                output.append(f"**File:** `{module_path}`")
                output.append(f"**Activity:** {activity['type']}: {activity['title']}")
                output.append(f"**Line:** ~{activity['line_number']}")
                output.append(f"**Item:** {item_num}")
                output.append("")
                output.append("**Error Sentence:**")
                output.append("```")
                output.append(error_sentence.strip())
                output.append("```")
                output.append("")
                output.append(f"**Flagged Error:** `{error_word.strip()}`")
                output.append(f"**Suggested Correction:** `{correct_word.strip()}`")
                output.append("")
                output.append("**Validation Request:**")
                output.append("```")
                output.append(f'Is "{error_word.strip()}" actually wrong in this context?')
                output.append(f'Is "{correct_word.strip()}" the correct form?')
                output.append(f"Level: {level}")
                output.append("```")
                output.append("")
                output.append("**Context:**")
                output.append("```markdown")
                # Show 5 lines of context
                context_lines = activity['body'].split('\n')[:10]
                output.append('\n'.join(context_lines))
                output.append("```")
                output.append("")
                output.append("---")
                output.append("")

                issue_num += 1

        # For fill-in activities, check the answers
        elif activity['type'] == 'fill-in':
            items = re.findall(
                r'(\d+)\.\s*([^\n>]+)\n\s*>\s*\[!answer\]\s*([^\n]+)',
                activity['body']
            )

            for item_num, sentence_with_blank, answer in items:
                # Reconstruct full sentence
                full_sentence = sentence_with_blank.replace('___', answer.strip())

                output.append(f"## Issue {issue_num}: Fill-in Activity")
                output.append("")
                output.append(f"**File:** `{module_path}`")
                output.append(f"**Activity:** {activity['type']}: {activity['title']}")
                output.append(f"**Line:** ~{activity['line_number']}")
                output.append(f"**Item:** {item_num}")
                output.append("")
                output.append("**Completed Sentence:**")
                output.append("```")
                output.append(full_sentence.strip())
                output.append("```")
                output.append("")
                output.append(f"**Answer:** `{answer.strip()}`")
                output.append("")
                output.append("**Validation Request:**")
                output.append("```")
                output.append(f'Is "{answer.strip()}" grammatically correct in this sentence?')
                output.append(f"Is the sentence natural Ukrainian for {level}?")
                output.append("```")
                output.append("")
                output.append("**Context:**")
                output.append("```markdown")
                context_lines = activity['body'].split('\n')[:10]
                output.append('\n'.join(context_lines))
                output.append("```")
                output.append("")
                output.append("---")
                output.append("")

                issue_num += 1

    if issue_num == 1:
        output.append("## No Issues Found")
        output.append("")
        output.append("No error-correction or fill-in activities detected in this module.")
        output.append("")

    output.append("---")
    output.append("")
    output.append("## Gemini Validation Prompt Template")
    output.append("")
    output.append("Paste this prompt + one issue above into Gemini:")
    output.append("")
    output.append("```")
    output.append("[First, paste the entire content of scripts/audit/ukrainian_grammar_validator_prompt.md]")
    output.append("")
    output.append("---")
    output.append("")
    output.append("Now validate this specific issue:")
    output.append("")
    output.append("**Sentence:** [paste sentence]")
    output.append("**Level:** [paste level]")
    output.append("**Flagged Issue:** [paste issue]")
    output.append("**Suggested Correction:** [paste correction]")
    output.append("**Context:** [paste context]")
    output.append("")
    output.append("Is this a real error or pedagogically acceptable? Respond in JSON.")
    output.append("```")
    output.append("")

    return '\n'.join(output)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_grammar_review_queue.py <module.md>")
        print("Example: python scripts/generate_grammar_review_queue.py curriculum/l2-uk-en/a2/05-*.md")
        sys.exit(1)

    module_path = Path(sys.argv[1])

    if not module_path.exists():
        print(f"Error: File not found: {module_path}")
        sys.exit(1)

    review_queue = generate_review_queue(module_path)
    print(review_queue)
