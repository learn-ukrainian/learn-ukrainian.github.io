#!/usr/bin/env python3
"""
Hard gate checker for staged module generation.

Usage:
    python3 scripts/check_gate.py skeleton <file>
    python3 scripts/check_gate.py content <file>
    python3 scripts/check_gate.py activities <file>

Returns exit code 0 on PASS, 1 on FAIL.
Agent has NO discretion to override FAIL.
"""

import sys
import re
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from audit.config import (
    get_level_config,
    get_word_target,
    get_b1_immersion_range,
    LEVEL_CONFIG,
)


def parse_frontmatter(content: str) -> dict:
    """Extract frontmatter from module content."""
    fm = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def extract_level_and_module(file_path: Path) -> tuple[str, int]:
    """Extract level code and module number from file path."""
    # Pattern: curriculum/l2-uk-en/{level}/{num}-{slug}.md
    parts = file_path.parts
    level = None
    module_num = 0

    for i, part in enumerate(parts):
        if part in ('a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit'):
            level = part.upper()
            break

    # Extract module number from filename
    match = re.match(r'^(\d+)-', file_path.name)
    if match:
        module_num = int(match.group(1))

    return level, module_num


def count_words(content: str) -> int:
    """Count words in content (excluding frontmatter and activities)."""
    # Remove frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    # Remove activities section
    act_match = re.search(r'^#\s*(Activities|Вправи)\s*$', content, re.MULTILINE)
    if act_match:
        content = content[:act_match.start()]

    # Remove vocabulary section
    vocab_match = re.search(r'^#\s*(Vocabulary|Словник)\s*$', content, re.MULTILINE)
    if vocab_match:
        content = content[:vocab_match.start()]

    # Count words
    words = re.findall(r'\b\w+\b', content)
    return len(words)


def count_engagement_boxes(content: str) -> int:
    """Count engagement boxes (💡🎬🌍🎯🎮)."""
    patterns = [
        r'>\s*\[!tip\]',
        r'>\s*\[!note\]',
        r'>\s*\[!observe\]',
        r'💡\s*\*\*',
        r'🎬\s*\*\*',
        r'🌍\s*\*\*',
        r'🎯\s*\*\*',
        r'🎮\s*\*\*',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return count


def count_examples(content: str) -> int:
    """Count Ukrainian example sentences."""
    # Look for bold Ukrainian text or example patterns
    patterns = [
        r'\*\*[А-ЯІЇЄҐа-яіїєґ][^*]+\*\*',  # Bold Ukrainian
        r'^\s*[-–—]\s*[А-ЯІЇЄҐа-яіїєґ]',  # Bulleted Ukrainian
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return min(count, 100)  # Cap to avoid overcounting


def count_dialogues(content: str) -> int:
    """Count mini-dialogues (А:/Б: patterns)."""
    patterns = [
        r'^[АБВ]:\s',
        r'^\*\*[АБВ]:\*\*\s',
        r'^—\s*[А-ЯІЇЄҐа-яіїєґ]',  # Em-dash dialogue
        r'^>\s*—\s*[А-ЯІЇЄҐа-яіїєґ]',  # Em-dash dialogue inside blockquote
        r'^\*\*[А-ЯІЇЄҐа-яіїєґ]+:\*\*\s',  # **Speaker:** format
        r'^[А-ЯІЇЄҐа-яіїєґ]+:\s+[А-ЯІЇЄҐа-яіїєґ]',  # Speaker: text format
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return count // 2  # Pairs


def count_activities(content: str) -> tuple[int, set]:
    """Count activities and unique types."""
    activity_pattern = r'^##\s+(quiz|match-up|fill-in|true-false|group-sort|unjumble|anagram|error-correction|cloze|mark-the-words|dialogue-reorder|select|translate):'
    matches = re.findall(activity_pattern, content, re.MULTILINE | re.IGNORECASE)
    return len(matches), set(m.lower() for m in matches)


def count_vocab(content: str) -> int:
    """Count vocabulary items in table."""
    # Look for table rows in vocabulary section (# or ##)
    vocab_match = re.search(r'^##?\s*(Vocabulary|Словник)\s*$', content, re.MULTILINE)
    if not vocab_match:
        return 0

    vocab_section = content[vocab_match.end():]
    # Count table rows (| word | ... |)
    rows = re.findall(r'^\|[^|]+\|', vocab_section, re.MULTILINE)
    # Subtract header and separator rows
    return max(0, len(rows) - 2)


def calculate_immersion(content: str) -> float:
    """Calculate Ukrainian immersion percentage."""
    # Remove frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    # Remove activities and vocab
    for section in ['Activities', 'Вправи', 'Vocabulary', 'Словник']:
        match = re.search(rf'^#\s*{section}\s*$', content, re.MULTILINE)
        if match:
            content = content[:match.start()]
            break

    # Count Ukrainian vs total words
    ukr_words = len(re.findall(r'\b[а-яіїєґА-ЯІЇЄҐ]+\b', content))
    eng_words = len(re.findall(r'\b[a-zA-Z]+\b', content))

    total = ukr_words + eng_words
    if total == 0:
        return 100.0

    return (ukr_words / total) * 100


def check_skeleton_gate(file_path: Path, content: str) -> tuple[bool, list[str]]:
    """Check skeleton stage gate."""
    failures = []

    # 1. Frontmatter present
    fm = parse_frontmatter(content)
    if not fm:
        failures.append("Missing frontmatter")
    else:
        required = ['module', 'title', 'level']
        for key in required:
            if key not in fm:
                failures.append(f"Missing frontmatter key: {key}")

    # 2. Required sections present
    required_sections = ['# ', '## ']  # At least main title and subsections
    if not re.search(r'^#\s+\w', content, re.MULTILINE):
        failures.append("Missing main title (# heading)")

    # 3. Vocabulary section present
    if not re.search(r'^#\s*(Vocabulary|Словник)', content, re.MULTILINE):
        failures.append("Missing Vocabulary/Словник section")

    # 4. Activity placeholders or targets present
    # (skeleton should have activity specs or placeholders)

    return len(failures) == 0, failures


def check_content_gate(file_path: Path, content: str) -> tuple[bool, list[str]]:
    """Check content stage gate."""
    failures = []

    level, module_num = extract_level_and_module(file_path)
    if not level:
        failures.append(f"Cannot determine level from path: {file_path}")
        return False, failures

    # Get config for this level
    fm = parse_frontmatter(content)
    module_focus = fm.get('focus', None)
    config = get_level_config(level, module_focus)

    # 1. Word count
    word_target = get_word_target(level, module_num, module_focus)
    word_count = count_words(content)
    if word_count < word_target:
        failures.append(f"Words: {word_count}/{word_target} FAIL")

    # 2. Engagement boxes (B1+)
    if level in ('B1', 'B2', 'C1', 'C2'):
        min_engagement = config.get('min_engagement', 5)
        engagement_count = count_engagement_boxes(content)
        if engagement_count < min_engagement:
            failures.append(f"Engagement: {engagement_count}/{min_engagement} FAIL")

    # 3. Example sentences (B1+)
    if level in ('B1', 'B2', 'C1', 'C2'):
        min_examples = 24  # From architecture doc
        example_count = count_examples(content)
        if example_count < min_examples:
            failures.append(f"Examples: {example_count}/{min_examples} FAIL")

    # 4. Dialogues (B1+)
    if level in ('B1', 'B2', 'C1', 'C2'):
        min_dialogues = 4  # From architecture doc
        dialogue_count = count_dialogues(content)
        if dialogue_count < min_dialogues:
            failures.append(f"Dialogues: {dialogue_count}/{min_dialogues} FAIL")

    # 5. Immersion (level-specific)
    if level == 'B1':
        min_imm, max_imm = get_b1_immersion_range(module_num)
    else:
        min_imm = config.get('min_immersion', 0)
        max_imm = config.get('max_immersion', 100)

    if min_imm > 0:
        immersion = calculate_immersion(content)
        if immersion < min_imm:
            failures.append(f"Immersion: {immersion:.1f}% < {min_imm}% FAIL")
        elif immersion > max_imm:
            failures.append(f"Immersion: {immersion:.1f}% > {max_imm}% FAIL")

    # 6. Vocabulary count
    min_vocab = config.get('min_vocab', 10)
    vocab_count = count_vocab(content)
    if vocab_count < min_vocab:
        failures.append(f"Vocabulary: {vocab_count}/{min_vocab} FAIL")

    return len(failures) == 0, failures


def check_activities_gate(file_path: Path, content: str) -> tuple[bool, list[str]]:
    """Check activities stage gate."""
    failures = []

    level, module_num = extract_level_and_module(file_path)
    if not level:
        failures.append(f"Cannot determine level from path: {file_path}")
        return False, failures

    fm = parse_frontmatter(content)
    module_focus = fm.get('focus', None)
    config = get_level_config(level, module_focus)

    # 1. Activity count
    min_activities = config.get('min_activities', 8)
    activity_count, activity_types = count_activities(content)
    if activity_count < min_activities:
        failures.append(f"Activities: {activity_count}/{min_activities} FAIL")

    # 2. Activity type variety
    min_types = config.get('min_types_unique', 4)
    if len(activity_types) < min_types:
        failures.append(f"Activity types: {len(activity_types)}/{min_types} FAIL")

    # 3. Priority types used
    priority_types = config.get('priority_types', set())
    if priority_types and not activity_types.intersection(priority_types):
        failures.append(f"No priority activity types used (need: {priority_types})")

    # 4. Activity item counts (check each activity has minimum items)
    min_items = config.get('min_items_per_activity', 12)
    activity_sections = re.split(r'^##\s+(?:quiz|match-up|fill-in|true-false|group-sort|unjumble|anagram|error-correction|cloze|mark-the-words|dialogue-reorder|select|translate):', content, flags=re.MULTILINE | re.IGNORECASE)

    for i, section in enumerate(activity_sections[1:], 1):
        # Count numbered items
        items = len(re.findall(r'^\d+\.', section, re.MULTILINE))
        if items > 0 and items < min_items:
            # Find activity type
            type_match = re.search(r'^##\s+(\w+[-\w]*):', content[:content.find(section)], re.MULTILINE | re.IGNORECASE)
            act_type = type_match.group(1) if type_match else f"Activity {i}"
            failures.append(f"{act_type}: {items}/{min_items} items FAIL")

    return len(failures) == 0, failures


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/check_gate.py <stage> <file>")
        print("Stages: skeleton, content, activities")
        sys.exit(1)

    stage = sys.argv[1].lower()
    file_path = Path(sys.argv[2])

    if not file_path.exists():
        print(f"FAIL: File not found: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')

    # Run appropriate gate check
    if stage == 'skeleton':
        passed, failures = check_skeleton_gate(file_path, content)
    elif stage == 'content':
        passed, failures = check_content_gate(file_path, content)
    elif stage == 'activities':
        passed, failures = check_activities_gate(file_path, content)
    else:
        print(f"FAIL: Unknown stage: {stage}")
        print("Valid stages: skeleton, content, activities")
        sys.exit(1)

    # Output result
    if passed:
        print(f"PASS: {stage} gate")
        sys.exit(0)
    else:
        print(f"FAIL: {stage} gate")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)


if __name__ == '__main__':
    main()
