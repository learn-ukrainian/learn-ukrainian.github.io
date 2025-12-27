#!/usr/bin/env python3
"""
Markdown to YAML Activity Converter

Extracts activities from existing Markdown module files and converts them to
the new YAML format.

Usage:
    python scripts/md_to_yaml.py <md_file>
    python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/01-dative.md
    python scripts/md_to_yaml.py --dir curriculum/l2-uk-en/a1/
    python scripts/md_to_yaml.py --all

Options:
    --output PATH   Output directory (default: same directory as source)
    --dry-run       Show what would be converted without writing files
    --force         Overwrite existing .activities.yaml files
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))


# =============================================================================
# ACTIVITY PARSING (adapted from generate_mdx.py)
# =============================================================================

def parse_quiz(content: str) -> list[dict]:
    """Parse quiz activity from markdown."""
    items = []

    # Split by numbered questions (1., 2., etc.)
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:  # Skip first empty split
        lines = block.strip().split('\n')
        if not lines:
            continue

        # First line is the question
        question = lines[0].strip()
        options = []
        explanation = None

        for line in lines[1:]:
            line = line.strip()

            # Option: - [x] or - [ ]
            option_match = re.match(r'-\s*\[(x|\s)\]\s*(.+)', line, re.IGNORECASE)
            if option_match:
                is_correct = option_match.group(1).lower() == 'x'
                text = option_match.group(2).strip()
                options.append({'text': text, 'correct': is_correct})
                continue

            # Explanation: > text
            if line.startswith('>'):
                explanation = line[1:].strip()

        if question and len(options) >= 4:
            item = {'question': question, 'options': options}
            if explanation:
                item['explanation'] = explanation
            items.append(item)

    return items


def parse_match_up(content: str) -> list[dict]:
    """Parse match-up activity from markdown."""
    pairs = []

    # Try table format first
    table_rows = re.findall(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', content)
    for left, right in table_rows:
        left = left.strip()
        right = right.strip()
        # Skip header rows
        if left == 'Ukrainian' or left == 'Left' or left.startswith('-'):
            continue
        if left and right:
            pairs.append({'left': left, 'right': right})

    if pairs:
        return pairs

    # Try :: separator format
    for line in content.split('\n'):
        line = line.strip()
        if '::' in line:
            parts = line.split('::')
            if len(parts) == 2:
                pairs.append({'left': parts[0].strip(), 'right': parts[1].strip()})

    return pairs


def parse_fill_in(content: str) -> list[dict]:
    """Parse fill-in activity from markdown."""
    items = []

    # Split by numbered items
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if not lines:
            continue

        sentence = lines[0].strip()
        answer = None
        options = []
        explanation = None

        for line in lines[1:]:
            line = line.strip()

            # Answer callout
            if line.startswith('> [!answer]'):
                answer = line.replace('> [!answer]', '').strip()
            # Options callout
            elif line.startswith('> [!options]'):
                opts_str = line.replace('> [!options]', '').strip()
                options = [o.strip() for o in opts_str.split('|')]
            # Explanation (regular > without callout)
            elif line.startswith('>') and not line.startswith('> [!'):
                explanation = line[1:].strip()

        if sentence and answer and options:
            item = {'sentence': sentence, 'answer': answer, 'options': options}
            if explanation:
                item['explanation'] = explanation
            items.append(item)

    return items


def parse_true_false(content: str) -> list[dict]:
    """Parse true-false activity from markdown."""
    items = []

    for line in content.split('\n'):
        line = line.strip()

        # Format: - [x] statement (true) or - [ ] statement (false)
        match = re.match(r'-\s*\[(x|\s)\]\s*(.+)', line, re.IGNORECASE)
        if match:
            is_true = match.group(1).lower() == 'x'
            statement = match.group(2).strip()
            items.append({'statement': statement, 'correct': is_true})

        # Explanation on next line
        elif line.startswith('>') and items:
            items[-1]['explanation'] = line[1:].strip()

    return items


def parse_group_sort(content: str) -> list[dict]:
    """Parse group-sort activity from markdown."""
    groups = []
    current_group = None

    for line in content.split('\n'):
        line = line.strip()

        # Group header: ### Group Name
        if line.startswith('###'):
            if current_group and current_group['items']:
                groups.append(current_group)
            current_group = {'name': line.replace('###', '').strip(), 'items': []}

        # Item: - item
        elif line.startswith('-') and current_group is not None:
            item = line[1:].strip()
            if item:
                current_group['items'].append(item)

    if current_group and current_group['items']:
        groups.append(current_group)

    return groups


def parse_unjumble(content: str) -> list[dict]:
    """Parse unjumble activity from markdown."""
    items = []

    # Split by numbered items
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if not lines:
            continue

        # First line: scrambled words separated by /
        scrambled = lines[0].strip()
        words = [w.strip() for w in scrambled.split('/')]
        answer = None

        for line in lines[1:]:
            line = line.strip()
            if line.startswith('> [!answer]'):
                answer = line.replace('> [!answer]', '').strip()
                break

        if words and answer:
            items.append({'words': words, 'answer': answer})

    return items


def parse_anagram(content: str) -> list[dict]:
    """Parse anagram activity from markdown (A1 only)."""
    items = []

    # Split by numbered items
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if not lines:
            continue

        # First line: scrambled letters (space-separated)
        scrambled = lines[0].strip()
        answer = None
        hint = None

        for line in lines[1:]:
            line = line.strip()
            if line.startswith('> [!answer]'):
                answer = line.replace('> [!answer]', '').strip()
            elif line.startswith('>'):
                # Hint in parentheses
                hint_match = re.search(r'\(([^)]+)\)', line)
                if hint_match:
                    hint = hint_match.group(1)

        if scrambled and answer:
            item = {'scrambled': scrambled, 'answer': answer}
            if hint:
                item['hint'] = hint
            items.append(item)

    return items


def parse_error_correction(content: str) -> list[dict]:
    """Parse error-correction activity from markdown."""
    items = []

    # Split by numbered items
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if not lines:
            continue

        sentence = lines[0].strip()
        error = None
        answer = None
        options = []
        explanation = None

        for line in lines[1:]:
            line = line.strip()

            if line.startswith('> [!error]'):
                error = line.replace('> [!error]', '').strip()
            elif line.startswith('> [!answer]'):
                answer = line.replace('> [!answer]', '').strip()
            elif line.startswith('> [!options]'):
                opts_str = line.replace('> [!options]', '').strip()
                options = [o.strip() for o in opts_str.split('|')]
            elif line.startswith('> [!explanation]'):
                explanation = line.replace('> [!explanation]', '').strip()

        if sentence and error and answer and options and explanation:
            items.append({
                'sentence': sentence,
                'error': error,
                'answer': answer,
                'options': options,
                'explanation': explanation
            })

    return items


def parse_cloze(content: str) -> dict:
    """Parse cloze activity from markdown."""
    lines = content.strip().split('\n')

    # Extract passage (lines before numbered items)
    passage_lines = []
    blanks = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Numbered item: 1. opt1 | opt2 | opt3
        num_match = re.match(r'^(\d+)\.\s*(.+)', line)
        if num_match:
            blank_id = int(num_match.group(1))
            options_str = num_match.group(2).strip()

            # Check for inline options
            if '|' in options_str:
                options = [o.strip() for o in options_str.split('|')]
                answer = options[0]  # First is correct
            else:
                # Old format: look for [!answer] on next line
                answer = options_str
                options = [answer]
                if i + 1 < len(lines) and '[!answer]' in lines[i + 1]:
                    answer = lines[i + 1].replace('> [!answer]', '').strip()
                    i += 1

            blanks.append({
                'id': blank_id,
                'answer': answer,
                'options': options[:4] if len(options) >= 4 else options + [''] * (4 - len(options))
            })
        elif not num_match and not line.startswith('>'):
            passage_lines.append(line)

        i += 1

    passage = ' '.join(passage_lines).strip()

    # Convert [___:N] to {N} format
    passage = re.sub(r'\[___:(\d+)\]', r'{\1}', passage)

    return {'passage': passage, 'blanks': blanks}


def parse_mark_the_words(content: str) -> dict:
    """Parse mark-the-words activity from markdown."""
    lines = content.strip().split('\n')

    instruction = ''
    passage = ''
    correct_words = []

    for line in lines:
        line = line.strip()

        # Extract words in [brackets]
        words = re.findall(r'\[([^\]]+)\]', line)
        if words:
            correct_words.extend(words)
            # Remove brackets for passage
            passage = re.sub(r'\[([^\]]+)\]', r'\1', line)
        elif line.startswith('>'):
            # Skip explanation lines
            continue
        elif not passage and line:
            instruction = line

    return {
        'instruction': instruction or 'Mark the indicated words.',
        'passage': passage,
        'correct_words': correct_words
    }


def parse_dialogue_reorder(content: str) -> list[dict]:
    """Parse dialogue-reorder activity from markdown."""
    lines = []
    order = 1

    for line in content.split('\n'):
        line = line.strip()

        # Format: - A: text or - B: text
        match = re.match(r'-\s*([AB]?):\s*(.+)', line)
        if match:
            speaker = match.group(1) if match.group(1) else None
            text = match.group(2).strip()
            item = {'order': order, 'text': text}
            if speaker:
                item['speaker'] = speaker
            lines.append(item)
            order += 1

    return lines


def parse_select(content: str) -> list[dict]:
    """Parse select (multiple correct) activity from markdown."""
    items = []

    # Split by numbered items
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if not lines:
            continue

        question = lines[0].strip()
        options = []
        explanation = None

        for line in lines[1:]:
            line = line.strip()

            # Option: - [x] or - [ ]
            option_match = re.match(r'-\s*\[(x|\s)\]\s*(.+)', line, re.IGNORECASE)
            if option_match:
                is_correct = option_match.group(1).lower() == 'x'
                text = option_match.group(2).strip()
                options.append({'text': text, 'correct': is_correct})

            # Explanation
            elif line.startswith('>'):
                explanation = line[1:].strip()

        if question and options:
            item = {'question': question, 'options': options}
            if explanation:
                item['explanation'] = explanation
            items.append(item)

    return items


def parse_translate(content: str) -> list[dict]:
    """Parse translate activity from markdown."""
    items = []

    # Split by numbered items
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if not lines:
            continue

        source = lines[0].strip()
        options = []
        explanation = None

        for line in lines[1:]:
            line = line.strip()

            # Option: - [x] or - [ ]
            option_match = re.match(r'-\s*\[(x|\s)\]\s*(.+)', line, re.IGNORECASE)
            if option_match:
                is_correct = option_match.group(1).lower() == 'x'
                text = option_match.group(2).strip()
                options.append({'text': text, 'correct': is_correct})

            # Explanation
            elif line.startswith('>'):
                explanation = line[1:].strip()

        if source and options:
            item = {'source': source, 'options': options}
            if explanation:
                item['explanation'] = explanation
            items.append(item)

    return items


# =============================================================================
# MAIN EXTRACTION LOGIC
# =============================================================================

ACTIVITY_PARSERS = {
    'quiz': parse_quiz,
    'match-up': parse_match_up,
    'fill-in': parse_fill_in,
    'true-false': parse_true_false,
    'group-sort': parse_group_sort,
    'unjumble': parse_unjumble,
    'anagram': parse_anagram,
    'error-correction': parse_error_correction,
    'cloze': parse_cloze,
    'mark-the-words': parse_mark_the_words,
    'dialogue-reorder': parse_dialogue_reorder,
    'select': parse_select,
    'translate': parse_translate,
}


def extract_activities_section(md_content: str) -> Optional[str]:
    """Extract the # Activities section from markdown."""
    # Find # Activities or # Вправи section
    match = re.search(r'^#\s*(Activities|Вправи)\s*\n(.*?)(?=^#\s+[^#]|\Z)',
                      md_content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(2).strip()
    return None


def parse_activities_section(activities_md: str) -> list[dict]:
    """Parse activities section into list of activity dicts."""
    activities = []

    # Split by ## activity-type: title
    activity_blocks = re.split(r'^##\s+(\w[\w-]*):\s*(.+?)\s*$',
                               activities_md, flags=re.MULTILINE)

    # activity_blocks: ['', 'quiz', 'Title', 'content', 'match-up', 'Title2', 'content2', ...]
    i = 1
    while i < len(activity_blocks) - 1:
        activity_type = activity_blocks[i].strip()
        title = activity_blocks[i + 1].strip()
        content = activity_blocks[i + 2].strip() if i + 2 < len(activity_blocks) else ''

        parser = ACTIVITY_PARSERS.get(activity_type)
        if parser:
            parsed = parser(content)

            if activity_type == 'cloze':
                # Cloze returns dict with passage and blanks
                activity = {
                    'type': activity_type,
                    'title': title,
                    'passage': parsed['passage'],
                    'blanks': parsed['blanks']
                }
            elif activity_type == 'mark-the-words':
                activity = {
                    'type': activity_type,
                    'title': title,
                    'instruction': parsed['instruction'],
                    'passage': parsed['passage'],
                    'correct_words': parsed['correct_words']
                }
            elif activity_type in ['match-up']:
                activity = {
                    'type': activity_type,
                    'title': title,
                    'pairs': parsed
                }
            elif activity_type in ['group-sort']:
                activity = {
                    'type': activity_type,
                    'title': title,
                    'groups': parsed
                }
            elif activity_type in ['dialogue-reorder']:
                activity = {
                    'type': activity_type,
                    'title': title,
                    'lines': parsed
                }
            else:
                activity = {
                    'type': activity_type,
                    'title': title,
                    'items': parsed
                }

            activities.append(activity)
        else:
            print(f"  Warning: Unknown activity type '{activity_type}'", file=sys.stderr)

        i += 3

    return activities


def strip_activities_from_md(md_content: str) -> str:
    """
    Remove activities section from markdown, keeping Summary and Vocabulary.

    Finds: # Activities or # Вправи
    Stops before: # Summary, # Підсумок, # Vocabulary, # Словник
    """
    # Find where activities start
    activities_start = re.search(r'^#\s*(Activities|Вправи)\s*$', md_content, re.MULTILINE)
    if not activities_start:
        return md_content

    start_pos = activities_start.start()

    # Find where to stop (next major section after activities)
    remaining = md_content[activities_start.end():]
    next_section = re.search(r'^#\s*(Summary|Підсумок|Vocabulary|Словник)\s*$', remaining, re.MULTILINE)

    if next_section:
        end_pos = activities_start.end() + next_section.start()
        # Keep the next section header
        return md_content[:start_pos] + md_content[end_pos:]
    else:
        # No next section found - just remove to end (shouldn't happen in valid modules)
        return md_content[:start_pos]


def convert_md_to_yaml(md_path: Path, output_dir: Path = None,
                       dry_run: bool = False, force: bool = False,
                       strip: bool = False) -> Optional[Path]:
    """
    Convert a markdown module file to YAML activities file.

    Returns the path to the created YAML file, or None if no activities found.
    """
    if not md_path.exists():
        print(f"Error: File not found: {md_path}", file=sys.stderr)
        return None

    # Read markdown
    md_content = md_path.read_text(encoding='utf-8')

    # Extract activities section
    activities_md = extract_activities_section(md_content)
    if not activities_md:
        print(f"  No activities section found in {md_path.name}")
        return None

    # Parse activities
    activities = parse_activities_section(activities_md)
    if not activities:
        print(f"  No activities parsed from {md_path.name}")
        return None

    # Determine output path
    if output_dir is None:
        output_dir = md_path.parent

    yaml_filename = md_path.stem + '.activities.yaml'
    yaml_path = output_dir / yaml_filename

    if yaml_path.exists() and not force:
        print(f"  Skip: {yaml_path.name} already exists (use --force to overwrite)")
        return None

    if dry_run:
        print(f"  Would create: {yaml_path}")
        print(f"    {len(activities)} activities: {', '.join(a['type'] for a in activities)}")
        if strip:
            print(f"  Would strip activities from: {md_path.name}")
        return yaml_path

    # Write YAML
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(f"# Activities extracted from {md_path.name}\n")
        f.write(f"# Generated by md_to_yaml.py\n\n")
        yaml.dump(activities, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=120)

    print(f"  Created: {yaml_path.name} ({len(activities)} activities)")

    # Strip activities from MD if requested
    if strip:
        stripped_content = strip_activities_from_md(md_content)
        md_path.write_text(stripped_content, encoding='utf-8')
        print(f"  Stripped activities from: {md_path.name}")

    return yaml_path


def convert_directory(dir_path: Path, output_dir: Path = None,
                      dry_run: bool = False, force: bool = False) -> tuple[int, int]:
    """Convert all .md files in a directory."""
    md_files = sorted(dir_path.glob('*.md'))

    if not md_files:
        print(f"No .md files found in {dir_path}")
        return 0, 0

    converted = 0
    skipped = 0

    for md_file in md_files:
        # Skip non-module files
        if md_file.name.startswith('_') or 'review' in md_file.name.lower():
            continue

        result = convert_md_to_yaml(md_file, output_dir, dry_run, force)
        if result:
            converted += 1
        else:
            skipped += 1

    return converted, skipped


def main():
    parser = argparse.ArgumentParser(
        description='Convert Markdown activities to YAML format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s module.md                        Convert single file
  %(prog)s --dir curriculum/l2-uk-en/a1/    Convert all in directory
  %(prog)s --all                            Convert entire curriculum
  %(prog)s module.md --dry-run              Preview without writing
  %(prog)s module.md --force                Overwrite existing YAML
'''
    )

    parser.add_argument('file', nargs='?', help='Markdown module file to convert')
    parser.add_argument('--dir', type=Path, help='Convert all .md files in directory')
    parser.add_argument('--all', action='store_true', help='Convert entire curriculum')
    parser.add_argument('--output', type=Path, help='Output directory')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--force', action='store_true', help='Overwrite existing YAML files')
    parser.add_argument('--strip', action='store_true', help='Remove activities from MD after extraction')

    args = parser.parse_args()

    if not args.file and not args.dir and not args.all:
        parser.print_help()
        sys.exit(1)

    if args.all:
        base_path = Path(__file__).parent.parent / 'curriculum' / 'l2-uk-en'
        total_converted = 0
        total_skipped = 0

        for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
            level_dir = base_path / level
            if level_dir.exists():
                print(f"\n{level.upper()}")
                converted, skipped = convert_directory(
                    level_dir, args.output, args.dry_run, args.force
                )
                total_converted += converted
                total_skipped += skipped

        print(f"\nTotal: {total_converted} converted, {total_skipped} skipped")

    elif args.dir:
        print(f"Converting files in {args.dir}...")
        converted, skipped = convert_directory(args.dir, args.output, args.dry_run, args.force)
        print(f"\nTotal: {converted} converted, {skipped} skipped")

    else:
        md_path = Path(args.file)
        result = convert_md_to_yaml(md_path, args.output, args.dry_run, args.force, args.strip)
        sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
