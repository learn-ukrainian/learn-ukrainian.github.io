#!/usr/bin/env python3
"""
Remove vocabulary lists from B1+ curriculum plans.

Replaces prescriptive vocabulary lists with content guidance that preserves
thematic and pop culture direction while allowing vocabulary to emerge from content.
"""

import re
from pathlib import Path

# Plans to clean up
PLANS_TO_CLEAN = ['B1', 'B2', 'C1', 'C2', 'LIT']

# Vocabulary targets by level
VOCAB_TARGETS = {
    'B1': '25+',
    'B2': '30+',
    'C1': '30+',
    'C2': '30+',
    'LIT': '20+'
}

CONTENT_GUIDANCE_TEMPLATE = """**Content Guidance:**
Vocabulary will emerge naturally from thematic content and should meet:
- Richness targets: {target} words per module
- Integration: 80% in activities, 50% in lesson text
- Register and complexity appropriate to {level} level

{keywords}"""


def extract_cultural_keywords(vocab_line: str) -> str:
    """
    Extract important keywords from vocabulary list that should be preserved as thematic guidance.

    Looks for:
    - Place names (capitalized)
    - Cultural terms
    - Pop culture references
    """
    words = [w.strip() for w in vocab_line.split(',')]

    keywords = []
    for word in words[:15]:  # First 15 words
        # Keep proper nouns (place names)
        if word and word[0].isupper():
            keywords.append(word)
        # Keep specific cultural/thematic terms
        elif any(term in word.lower() for term in ['культура', 'традиція', 'музика', 'кіно', 'спорт', 'фестиваль']):
            keywords.append(word)

    if keywords:
        return f"**Key themes/places:** {', '.join(keywords[:10])}\n\n"
    return ""


def remove_vocabulary_lists(content: str, level: str) -> tuple[str, int]:
    """
    Remove **Vocabulary (N words):** sections from curriculum plan.
    Preserves cultural keywords as thematic guidance.

    Returns:
        (cleaned_content, count_removed)
    """

    # Pattern to match vocabulary sections
    vocab_pattern = re.compile(
        r'\*\*Vocabulary \(\d+\s+words?\):\*\*\s*\n'
        r'(.*?)'
        r'(?=\n\*\*[A-Z]|\n####|\n---|\Z)',
        re.DOTALL
    )

    matches = list(vocab_pattern.finditer(content))
    count = len(matches)

    if count == 0:
        return content, 0

    target = VOCAB_TARGETS.get(level, '25+')

    # Replace each match individually to extract keywords
    def replace_vocab(match):
        vocab_content = match.group(1).strip()
        # Extract first line (usually the word list)
        first_line = vocab_content.split('\n')[0] if vocab_content else ''

        # Extract cultural keywords if present
        keywords = extract_cultural_keywords(first_line)

        return CONTENT_GUIDANCE_TEMPLATE.format(
            target=target,
            level=level,
            keywords=keywords
        )

    cleaned = vocab_pattern.sub(replace_vocab, content)

    return cleaned, count


def add_header_note(content: str, level: str) -> str:
    """Add note at top of plan explaining vocabulary approach."""

    # Find the position after the header block (after the first ---)
    header_end = content.find('\n---\n')
    if header_end == -1:
        return content

    # Find the second --- (end of front matter)
    second_divider = content.find('\n---\n', header_end + 5)
    if second_divider == -1:
        insert_pos = header_end + 5
    else:
        insert_pos = second_divider + 5

    note = f"""
## Vocabulary Approach (B1+)

**From B1 onwards, vocabulary is not prescribed in this plan.** Instead, vocabulary emerges naturally from the module's thematic content and is validated against:

- **Richness targets:** {VOCAB_TARGETS[level]} unique words per module (enforced by audit)
- **Integration requirements:** 80% used in activities, 50% in lesson text (enforced by audit)
- **Register appropriateness:** Vocabulary complexity matches {level} proficiency level

The "Content Guidance" sections below provide **thematic direction** and **pop culture anchors** to guide vocabulary selection, but builders have flexibility to choose words that best serve the pedagogical goals.

**Why this approach?**
- Content-driven vocabulary is more authentic and contextual
- Historical/cultural modules require domain-specific terminology
- Pop culture references evolve and need flexibility
- Quality is enforced through metrics, not prescriptive lists

---
"""

    return content[:insert_pos] + note + content[insert_pos:]


def main():
    print("=" * 80)
    print("CURRICULUM PLAN CLEANUP: Remove B1+ Vocabulary Lists")
    print("=" * 80)
    print()

    project_root = Path(__file__).parent.parent
    plan_dir = project_root / 'docs' / 'l2-uk-en'

    for level in PLANS_TO_CLEAN:
        plan_file = plan_dir / f'{level}-CURRICULUM-PLAN.md'

        if not plan_file.exists():
            print(f"⏭️  {level}: Plan not found, skipping")
            continue

        print(f"📖 Processing {level}-CURRICULUM-PLAN.md...")

        # Read original
        content = plan_file.read_text(encoding='utf-8')
        original_lines = len(content.split('\n'))

        # Remove vocabulary lists
        cleaned, count_removed = remove_vocabulary_lists(content, level)

        # Add header note
        final = add_header_note(cleaned, level)
        final_lines = len(final.split('\n'))

        # Create backup
        backup_file = plan_dir / f'{level}-CURRICULUM-PLAN_BEFORE_CLEANUP.md'
        backup_file.write_text(content, encoding='utf-8')

        # Write cleaned version
        plan_file.write_text(final, encoding='utf-8')

        lines_removed = original_lines - final_lines
        print(f"   ✓ Removed {count_removed} vocabulary lists")
        print(f"   ✓ Reduced by {lines_removed} lines")
        print(f"   ✓ Backup: {backup_file.name}")
        print()

    print("=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review cleaned plans for any formatting issues")
    print("2. Update audit script to skip plan-matching for B1+")
    print("3. Use cleaned plans for C1 development")
    print()
    print("Backups saved as: *-CURRICULUM-PLAN_BEFORE_CLEANUP.md")
    print("(Can be deleted after verification)")


if __name__ == '__main__':
    main()
