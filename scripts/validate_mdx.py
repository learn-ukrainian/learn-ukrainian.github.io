#!/usr/bin/env python3
"""
MDX Validator

Validates that MDX output contains all content from source MD.
Catches content loss during MD→MDX conversion.

Usage:
    python scripts/validate_mdx.py [lang_pair] [level] [module_num]
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass

# Add scripts directory to path for audit imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from audit.report import append_mdx_errors_to_report

PROJECT_ROOT = SCRIPT_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
DOCUSAURUS_DIR = PROJECT_ROOT / "docusaurus" / "docs"

@dataclass
class ValidationResult:
    module: str
    passed: bool
    errors: list[str]
    warnings: list[str]

def extract_text_content(content: str, include_jsx: bool = False) -> set[str]:
    """Extract meaningful text fragments from content."""
    # Remove frontmatter
    content = re.sub(r'^---[\s\S]*?---\n', '', content)

    # Remove code blocks
    content = re.sub(r'```[\s\S]*?```', '', content)

    # Remove import statements
    content = re.sub(r'^import .*$', '', content, flags=re.MULTILINE)

    if include_jsx:
        # Extract content from JSX template literals `...`
        jsx_strings = re.findall(r'`([^`]*)`', content)
        content = content + ' ' + ' '.join(jsx_strings)

    # Remove JSX component tags but keep content
    content = re.sub(r'<\w+[^>]*>', '', content)
    content = re.sub(r'</\w+>', '', content)

    # Remove markdown formatting but keep text
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    content = re.sub(r'\*([^*]+)\*', r'\1', content)
    content = re.sub(r'`([^`]+)`', r'\1', content)

    # Remove URLs
    content = re.sub(r'https?://\S+', '', content)

    # Extract words (Ukrainian and English)
    words = set()
    for match in re.findall(r'[\w\u0400-\u04FF]+', content):
        if len(match) > 2:  # Skip very short words
            words.add(match.lower())

    return words

def extract_vocabulary(content: str) -> set[str]:
    """Extract Ukrainian vocabulary words from Vocabulary section.

    Only extracts the first column (the actual vocabulary word) to avoid
    false positives from IPA, translations, and grammar notes.
    """
    vocab = set()

    # Find vocabulary section (H1 or H2 level)
    # May have emoji prefix like "📚 Vocabulary" but no other words before it
    # This prevents matching "## match-up: Café Vocabulary" etc.
    match = re.search(r'^#+\s+[^\w]*(?:Vocabulary|Словник)\s*$[\s\S]*?(?=^#+\s|\Z)', content, re.MULTILINE)
    if not match:
        return vocab

    vocab_section = match.group(0)

    # Process each table row - extract only the FIRST column (the vocabulary word)
    for line in vocab_section.split('\n'):
        line = line.strip()
        if not line.startswith('|'):
            continue
        # Split by | and get the first data cell (index 1 after split)
        cells = line.split('|')
        if len(cells) < 2:
            continue
        first_cell = cells[1].strip()
        # Skip header row and separator
        if not first_cell or first_cell.startswith('-') or first_cell.lower() in ('word', 'слово', 'ukrainian', 'термін'):
            continue
        # Extract Cyrillic words from first column only
        cyrillic_words = re.findall(r'[\u0400-\u04FF]+', first_cell)
        for word in cyrillic_words:
            if len(word) > 2:
                vocab.add(word.lower())

    return vocab

def extract_activity_content(content: str) -> dict[str, set[str]]:
    """Extract content from activities."""
    activities = {}

    # Find activity sections (H2 level)
    matches = re.findall(r'^##\s+([\w-]+):\s*([^\n]+)\n([\s\S]*?)(?=^#+|$)', content, re.MULTILINE)

    for activity_type, title, body in matches:
        key = f"{activity_type}:{title}"
        words = set()

        # Extract text content
        for match in re.findall(r'[\w\u0400-\u04FF]+', body):
            if len(match) > 2:
                words.add(match.lower())

        activities[key] = words

    return activities


def validate_cloze_components(mdx_content: str) -> list[str]:
    """
    Validate that Cloze components have properly structured blanks.

    Checks:
    1. Each blank object has 'index', 'answer', and 'options' properties
    2. Number of [___:N] markers matches number of blanks
    3. Indices are sequential (0, 1, 2, ...)
    """
    import json
    errors = []

    # Find all <Cloze components - extract title, passage, and blanks separately
    cloze_starts = list(re.finditer(r'<Cloze\s+', mdx_content))

    for match in cloze_starts:
        start_pos = match.end()
        # Find component end
        end_pos = mdx_content.find('/>', start_pos)
        if end_pos == -1:
            continue
        component = mdx_content[match.start():end_pos + 2]

        # Extract title
        title_match = re.search(r'title="([^"]+)"', component)
        title = title_match.group(1) if title_match else "Unknown"

        # Extract passage
        passage_match = re.search(r'passage=\{`([^`]*)`\}', component)
        passage = passage_match.group(1) if passage_match else ""

        # Extract blanks JSON - find JSON.parse(` and then count brackets to find the array end
        blanks_start = component.find('blanks={JSON.parse(`')
        if blanks_start == -1:
            continue
        json_start = blanks_start + len('blanks={JSON.parse(`')

        # Find the matching closing bracket by counting
        bracket_count = 0
        json_end = json_start
        started = False
        for i in range(json_start, len(component)):
            char = component[i]
            if char == '[':
                bracket_count += 1
                started = True
            elif char == ']':
                bracket_count -= 1
            if started and bracket_count == 0:
                json_end = i + 1
                break

        blanks_json = component[json_start:json_end]

        # Validate this cloze component
        try:
            blanks = json.loads(blanks_json)
        except json.JSONDecodeError as e:
            errors.append(f"Cloze '{title}': Invalid JSON in blanks array: {e}")
            continue

        # Count [___:N] markers in passage
        markers = re.findall(r'\[___:(\d+)\]', passage)
        num_markers = len(markers)
        num_blanks = len(blanks)

        if num_markers != num_blanks:
            errors.append(f"Cloze '{title}': {num_markers} markers but {num_blanks} blanks defined")

        # Validate each blank has required properties
        required_props = {'index', 'answer', 'options'}
        for i, blank in enumerate(blanks):
            missing = required_props - set(blank.keys())
            if missing:
                errors.append(f"Cloze '{title}': blank {i} missing properties: {', '.join(missing)}")

            # Validate index is correct
            if 'index' in blank and blank['index'] != i:
                errors.append(f"Cloze '{title}': blank {i} has wrong index {blank['index']} (expected {i})")

            # Validate options is a list
            if 'options' in blank and not isinstance(blank['options'], list):
                errors.append(f"Cloze '{title}': blank {i} options is not a list")

            # Validate answer is in options
            if 'answer' in blank and 'options' in blank:
                if blank['answer'] not in blank['options']:
                    errors.append(f"Cloze '{title}': blank {i} answer '{blank['answer']}' not in options")

    return errors

def validate_module(md_path: Path, mdx_path: Path) -> ValidationResult:
    """Validate that MDX contains all content from MD."""
    errors = []
    warnings = []

    if not md_path.exists():
        return ValidationResult(
            module=md_path.name,
            passed=False,
            errors=[f"Source MD not found: {md_path}"],
            warnings=[]
        )

    if not mdx_path.exists():
        return ValidationResult(
            module=md_path.name,
            passed=False,
            errors=[f"MDX not found: {mdx_path}"],
            warnings=[]
        )

    md_content = md_path.read_text(encoding='utf-8')
    mdx_content = mdx_path.read_text(encoding='utf-8')

    # Check vocabulary
    md_vocab = extract_vocabulary(md_content)
    mdx_vocab = extract_vocabulary(mdx_content)

    missing_vocab = md_vocab - mdx_vocab
    if missing_vocab:
        # Filter out common false positives
        missing_vocab = {w for w in missing_vocab if len(w) > 3}
        if missing_vocab:
            warnings.append(f"Vocabulary words possibly missing: {', '.join(list(missing_vocab)[:5])}")

    # Check overall text content (include JSX strings for MDX)
    md_words = extract_text_content(md_content, include_jsx=False)
    mdx_words = extract_text_content(mdx_content, include_jsx=True)

    # Key Ukrainian words that should definitely be present
    ukrainian_words = {w for w in md_words if re.match(r'^[\u0400-\u04FF]+$', w) and len(w) > 3}
    missing_ukrainian = ukrainian_words - mdx_words

    if len(missing_ukrainian) > len(ukrainian_words) * 0.2:  # More than 20% missing
        warnings.append(f"Some Ukrainian content may be missing ({len(missing_ukrainian)}/{len(ukrainian_words)} words)")

    # Check activities are present
    md_activities = re.findall(r'##\s+(quiz|match-up|fill-in|true-false|unjumble|group-sort|anagram|error-correction|cloze|select|translate|dialogue-reorder):', md_content, re.IGNORECASE)
    mdx_components = re.findall(r'<(Quiz|MatchUp|FillIn|TrueFalse|Unjumble|GroupSort|Anagram|ErrorCorrection|Cloze|Select|Translate|DialogueReorder)', mdx_content)

    # Normalize names for comparison
    md_activity_types = {a.lower().replace('-', '') for a in md_activities}
    mdx_component_types = {c.lower() for c in mdx_components}

    missing_activities = md_activity_types - mdx_component_types
    if missing_activities:
        errors.append(f"Activity types missing in MDX: {', '.join(missing_activities)}")

    # Validate Cloze components have properly structured blanks
    cloze_errors = validate_cloze_components(mdx_content)
    errors.extend(cloze_errors)

    # Check [!solution] callouts are converted to <details> elements (may have leading whitespace)
    md_solution_count = len(re.findall(r'^\s*>\s*\[!solution\]', md_content, re.IGNORECASE | re.MULTILINE))
    mdx_details_count = len(re.findall(r'<details\s+className=["\']solution-block["\']', mdx_content))
    
    if md_solution_count > 0:
        if mdx_details_count == 0:
            errors.append(f"[!solution] callouts ({md_solution_count}) not converted to <details> elements")
        elif mdx_details_count < md_solution_count:
            warnings.append(f"Some [!solution] callouts may not be converted ({mdx_details_count}/{md_solution_count} found)")
        
        # Verify balanced tags
        details_open = len(re.findall(r'<details\s', mdx_content))
        details_close = len(re.findall(r'</details>', mdx_content))
        if details_open != details_close:
            errors.append(f"Unbalanced <details> tags: {details_open} opens, {details_close} closes")

    passed = len(errors) == 0

    return ValidationResult(
        module=md_path.name,
        passed=passed,
        errors=errors,
        warnings=warnings
    )

def main():
    args = sys.argv[1:]
    lang_pair = args[0] if args else 'l2-uk-en'
    target_level = args[1].lower() if len(args) > 1 else None
    target_module = int(args[2]) if len(args) > 2 else None

    print('\n🔍 MDX Validator\n')

    curriculum_path = CURRICULUM_DIR / lang_pair
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']

    total_passed = 0
    total_failed = 0
    all_results = []

    for level in levels:
        if target_level and level != target_level:
            continue

        level_path = curriculum_path / level
        if not level_path.exists():
            continue

        module_files = sorted(level_path.glob('*.md'))
        if not module_files:
            continue

        print(f'📁 Level {level.upper()}')

        for md_file in module_files:
            match = re.match(r'^(\d+)', md_file.name)
            if not match:
                continue

            module_num = int(match.group(1))

            if target_module and module_num != target_module:
                continue

            mdx_file = DOCUSAURUS_DIR / level / f'module-{str(module_num).zfill(2)}.mdx'

            result = validate_module(md_file, mdx_file)
            all_results.append(result)

            # Write MDX validation results to review file (even if clean, to clear old warnings)
            append_mdx_errors_to_report(
                str(md_file),
                result.errors,
                result.warnings
            )

            if result.passed:
                total_passed += 1
                status = '✅'
            else:
                total_failed += 1
                status = '❌'

            print(f'  {status} Module {str(module_num).zfill(2)}', end='')

            if result.errors:
                print(f' - {result.errors[0]}')
            elif result.warnings:
                print(f' - ⚠️ {result.warnings[0]}')
            else:
                print()

    print(f'\n{"="*50}')
    print(f'Results: {total_passed} passed, {total_failed} failed')

    if total_failed > 0:
        print('\n❌ VALIDATION FAILED')
        sys.exit(1)
    else:
        print('\n✅ VALIDATION PASSED')
        sys.exit(0)

if __name__ == '__main__':
    main()
