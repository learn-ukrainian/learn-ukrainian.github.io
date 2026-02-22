#!/usr/bin/env python3
"""IPA linter for Ukrainian curriculum content.

Scans .md files for IPA transcriptions in square brackets and catches
systematic errors that Gemini consistently produces.

Errors detected:
  ʊ → u       Ukrainian has no lax /ʊ/ phoneme
  ɫ → l       Ukrainian uses alveolar lateral, not dark L
  tʃ → t͡ʃ    ч affricate needs tie-bar
  dʒ → d͡ʒ    дж affricate needs tie-bar
  ts → t͡s    ц affricate needs tie-bar (context-aware)
  dz → d͡z    дз affricate needs tie-bar (context-aware)
  w → ʋ       В is labiodental approximant (inside IPA brackets)
  v → ʋ       Same (inside IPA brackets)
  o → ɔ       Ukrainian о is open-mid back rounded [ɔ] (inside IPA brackets)
  e → ɛ       Ukrainian е is open-mid front unrounded [ɛ] (inside IPA brackets)
  i̯ → j       Non-syllabic i diacritic → standard palatal approximant (inside IPA brackets)

Usage:
  .venv/bin/python scripts/lint_ipa.py FILE              # lint one file
  .venv/bin/python scripts/lint_ipa.py FILE --fix        # auto-fix
  .venv/bin/python scripts/lint_ipa.py DIR/*.md          # batch lint
  .venv/bin/python scripts/lint_ipa.py DIR/*.md --fix    # batch fix
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

# Combining double inverted breve (tie-bar)
TIE = '\u0361'

# IPA vowels (for ts/dz context detection)
IPA_VOWELS = set('aeiouɛɪɔɑɐəæɒʉ')

# Characters that prove a bracket contains IPA (not markdown)
IPA_EVIDENCE = set('ˈˌɔɛɪʃʒʋŋθðæɑɐɜəɒɦɹɾʲʰ' + TIE)


@dataclass
class Issue:
    line: int
    col: int
    rule: str
    bad: str
    fix: str
    context: str  # surrounding text for display


@dataclass
class LintResult:
    path: Path
    issues: list = field(default_factory=list)
    fixed: int = 0


def is_ipa_bracket(content: str, after_char: str) -> bool:
    """Heuristic: is this [...] an IPA transcription?"""
    if not content:
        return False
    if content[0] == '!':  # callout [!tip]
        return False
    if after_char == '(':  # markdown link [text](url)
        return False
    # Contains IPA-specific characters?
    if any(c in IPA_EVIDENCE for c in content):
        return True
    # Contains known-bad IPA characters we're looking for?
    if any(c in content for c in 'ʊɫ'):
        return True
    # Contains ʃ or ʒ (IPA-only)?
    if 'ʃ' in content or 'ʒ' in content:
        return True
    return False


def find_brackets(line: str):
    """Yield (start, end, content, after_char) for each [...] in line."""
    i = 0
    while i < len(line):
        if line[i] == '[':
            depth = 1
            j = i + 1
            while j < len(line) and depth > 0:
                if line[j] == '[':
                    depth += 1
                elif line[j] == ']':
                    depth -= 1
                j += 1
            if depth == 0:
                content = line[i+1:j-1]
                after = line[j:j+1] if j < len(line) else ''
                yield i, j - 1, content, after
                i = j
            else:
                i += 1
        else:
            i += 1


# --- Global rules (IPA-specific chars guarantee context) ---

GLOBAL_RULES = [
    # (pattern, replacement, rule_id, description)
    # Simple string replacements
    ('ʊ', 'u', 'IPA-001', '/ʊ/ → /u/ (no lax vowel in Ukrainian)'),
    ('ɫ', 'l', 'IPA-002', '/ɫ/ → /l/ (no dark L in Ukrainian)'),
]

# Regex-based global rules (need negative lookbehind for tie-bar)
GLOBAL_REGEX_RULES = [
    # tʃ not preceded by tie-bar → t͡ʃ
    (re.compile(r'(?<!' + TIE + r')tʃ'), f't{TIE}ʃ', 'IPA-003', 'tʃ → t͡ʃ (ч needs tie-bar)'),
    # dʒ not preceded by tie-bar → d͡ʒ
    (re.compile(r'(?<!' + TIE + r')dʒ'), f'd{TIE}ʒ', 'IPA-004', 'dʒ → d͡ʒ (дж needs tie-bar)'),
]


def lint_global(text: str, line_offset: int = 0) -> list[Issue]:
    """Find issues using global rules (IPA-specific chars = guaranteed IPA context)."""
    issues = []
    lines = text.split('\n')

    for line_idx, line in enumerate(lines, start=1 + line_offset):
        # Simple string rules
        for bad, fix, rule_id, desc in GLOBAL_RULES:
            col = 0
            while True:
                pos = line.find(bad, col)
                if pos == -1:
                    break
                ctx = line[max(0, pos-15):pos+15]
                issues.append(Issue(line_idx, pos, rule_id, bad, fix, ctx))
                col = pos + 1

        # Regex rules
        for pattern, fix_str, rule_id, desc in GLOBAL_REGEX_RULES:
            for m in pattern.finditer(line):
                ctx = line[max(0, m.start()-15):m.end()+15]
                issues.append(Issue(line_idx, m.start(), rule_id, m.group(), fix_str, ctx))

    return issues


def lint_brackets(text: str) -> list[Issue]:
    """Find issues inside IPA brackets (w, v, ts, dz)."""
    issues = []
    lines = text.split('\n')

    for line_idx, line in enumerate(lines, start=1):
        for bstart, bend, content, after in find_brackets(line):
            if not is_ipa_bracket(content, after):
                continue

            # Check for non-syllabic i̯ (should be j — standard palatal approximant)
            # Ukrainian й is always [j]; i̯ is an alternative notation, not an allophone
            for m in re.finditer(r'i\u032F', content):
                abs_col = bstart + 1 + m.start()
                ctx = content[max(0, m.start()-10):m.end()+10]
                issues.append(Issue(line_idx, abs_col, 'IPA-011',
                                    'i̯', 'j', f'[...{ctx}...]'))
            # NOTE: u̯ is NOT normalized — it's a legitimate allophone of В
            # after vowels (жовтий [ˈʒɔu̯tɪj], любов [lʲuˈbɔu̯])

            # Check for /o/ (should be /ɔ/ in Ukrainian)
            for m in re.finditer(r'o', content):
                abs_col = bstart + 1 + m.start()
                ctx = content[max(0, m.start()-10):m.end()+10]
                issues.append(Issue(line_idx, abs_col, 'IPA-009',
                                    'o', 'ɔ', f'[...{ctx}...]'))

            # Check for /e/ (should be /ɛ/ in Ukrainian)
            for m in re.finditer(r'e', content):
                abs_col = bstart + 1 + m.start()
                ctx = content[max(0, m.start()-10):m.end()+10]
                issues.append(Issue(line_idx, abs_col, 'IPA-010',
                                    'e', 'ɛ', f'[...{ctx}...]'))

            # Check for /w/ (should be /ʋ/)
            for m in re.finditer(r'w', content):
                abs_col = bstart + 1 + m.start()
                ctx = content[max(0, m.start()-10):m.end()+10]
                issues.append(Issue(line_idx, abs_col, 'IPA-005',
                                    'w', 'ʋ', f'[...{ctx}...]'))

            # Check for /v/ (should be /ʋ/)
            # Match v that is NOT part of the ʋ character
            for m in re.finditer(r'v', content):
                abs_col = bstart + 1 + m.start()
                ctx = content[max(0, m.start()-10):m.end()+10]
                issues.append(Issue(line_idx, abs_col, 'IPA-006',
                                    'v', 'ʋ', f'[...{ctx}...]'))

            # Check for ts without tie-bar (ц affricate)
            # Match ts NOT preceded by tie-bar, followed by vowel, ʲ, ˈ, space, or ]
            for m in re.finditer(r'(?<!' + TIE + r')ts(?=[' +
                                 ''.join(IPA_VOWELS) + r'ʲˈ\s\]])', content):
                abs_col = bstart + 1 + m.start()
                ctx = content[max(0, m.start()-10):m.end()+10]
                issues.append(Issue(line_idx, abs_col, 'IPA-007',
                                    'ts', f't{TIE}s', f'[...{ctx}...]'))

            # Check for dz without tie-bar (дз affricate)
            for m in re.finditer(r'(?<!' + TIE + r')dz(?=[' +
                                 ''.join(IPA_VOWELS) + r'ʲˈʋ\s\]])', content):
                abs_col = bstart + 1 + m.start()
                ctx = content[max(0, m.start()-10):m.end()+10]
                issues.append(Issue(line_idx, abs_col, 'IPA-008',
                                    'dz', f'd{TIE}z', f'[...{ctx}...]'))

    return issues


def apply_fixes(text: str) -> tuple[str, int]:
    """Apply all IPA fixes to text. Returns (fixed_text, fix_count)."""
    count = 0

    # Phase 1: Global string replacements
    for bad, fix, _, _ in GLOBAL_RULES:
        n = text.count(bad)
        if n:
            text = text.replace(bad, fix)
            count += n

    # Phase 2: Global regex replacements
    for pattern, fix_str, _, _ in GLOBAL_REGEX_RULES:
        result = pattern.subn(fix_str, text)
        text = result[0]
        count += result[1]

    # Phase 3: Bracket-context replacements (w, v, ts, dz)
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        new_line = _fix_brackets_in_line(line)
        if new_line != line:
            # Count changes (approximate)
            count += sum(1 for a, b in zip(line, new_line) if a != b) // 2 or 1
        new_lines.append(new_line)

    return '\n'.join(new_lines), count


def _fix_brackets_in_line(line: str) -> str:
    """Fix IPA issues inside brackets on a single line."""
    result = []
    i = 0
    brackets = list(find_brackets(line))

    for bstart, bend, content, after in brackets:
        # Add text before this bracket
        result.append(line[i:bstart])

        if is_ipa_bracket(content, after):
            fixed = content
            # Fix i̯ → j (non-syllabic i diacritic → standard palatal approximant)
            # Must come before o/e replacements to avoid mangling diacritics
            fixed = fixed.replace('i\u032F', 'j')
            # Fix o → ɔ (Ukrainian о is open-mid [ɔ], not close-mid [o])
            fixed = fixed.replace('o', 'ɔ')
            # Fix e → ɛ (Ukrainian е is open-mid [ɛ], not close-mid [e])
            fixed = fixed.replace('e', 'ɛ')
            # Fix w → ʋ
            fixed = fixed.replace('w', 'ʋ')
            # Fix v → ʋ (v is U+0076, ʋ is U+028B — no collision)
            fixed = fixed.replace('v', 'ʋ')
            # Fix ts → t͡s (context: before vowel, ʲ, ˈ, space, end)
            fixed = re.sub(
                r'(?<!' + TIE + r')ts(?=[' + ''.join(IPA_VOWELS) + r'ʲˈ\s]|$)',
                f't{TIE}s', fixed
            )
            # Fix dz → d͡z
            fixed = re.sub(
                r'(?<!' + TIE + r')dz(?=[' + ''.join(IPA_VOWELS) + r'ʲˈʋ\s]|$)',
                f'd{TIE}z', fixed
            )
            result.append(f'[{fixed}]')
        else:
            result.append(f'[{content}]')

        i = bend + 1

    # Add remaining text after last bracket
    result.append(line[i:])
    return ''.join(result)


def lint_file(path: Path, fix: bool = False) -> LintResult:
    """Lint a single file. Returns LintResult."""
    result = LintResult(path=path)

    try:
        text = path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ERROR reading {path}: {e}", file=sys.stderr)
        return result

    # Find issues
    result.issues = lint_global(text) + lint_brackets(text)

    if fix and result.issues:
        fixed_text, fix_count = apply_fixes(text)
        path.write_text(fixed_text, encoding='utf-8')
        result.fixed = fix_count

    return result


def format_issues(result: LintResult, verbose: bool = True) -> str:
    """Format issues for display."""
    if not result.issues:
        return f"  ✅ {result.path.name}: clean"

    lines = []
    lines.append(f"  ❌ {result.path.name}: {len(result.issues)} IPA issues")

    if verbose:
        # Group by rule
        by_rule: dict[str, list[Issue]] = {}
        for issue in result.issues:
            by_rule.setdefault(issue.rule, []).append(issue)

        for rule_id, rule_issues in sorted(by_rule.items()):
            sample = rule_issues[0]
            lines.append(f"     {rule_id}: {sample.bad} → {sample.fix}  ({len(rule_issues)}x)")
            # Show first 3 locations
            for issue in rule_issues[:3]:
                lines.append(f"       L{issue.line}:{issue.col}  ...{issue.context}...")
            if len(rule_issues) > 3:
                lines.append(f"       ... and {len(rule_issues) - 3} more")

    if result.fixed:
        lines.append(f"     🔧 Fixed {result.fixed} issues")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='IPA linter for Ukrainian curriculum content',
        epilog='Exit code: 0 if clean, 1 if issues found (or fixed with --fix)'
    )
    parser.add_argument('files', nargs='+', type=Path, help='Files to lint')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues')
    parser.add_argument('-q', '--quiet', action='store_true', help='Only show summary')
    args = parser.parse_args()

    total_issues = 0
    total_fixed = 0
    total_files = 0
    dirty_files = 0

    for path in args.files:
        if not path.exists():
            print(f"  SKIP {path}: not found", file=sys.stderr)
            continue

        total_files += 1
        result = lint_file(path, fix=args.fix)
        total_issues += len(result.issues)
        total_fixed += result.fixed

        if result.issues:
            dirty_files += 1

        if not args.quiet:
            print(format_issues(result, verbose=True))

    # Summary
    print(f"\n  IPA Lint: {total_files} files, {total_issues} issues in {dirty_files} files", end='')
    if args.fix:
        print(f", {total_fixed} fixed")
    else:
        print()

    return 1 if total_issues > 0 and not args.fix else 0


if __name__ == '__main__':
    sys.exit(main())
