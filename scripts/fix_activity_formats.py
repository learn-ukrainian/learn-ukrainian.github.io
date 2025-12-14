#!/usr/bin/env python3
"""Fix common activity format issues in module files."""
import re
import sys
from pathlib import Path

def fix_quiz_format(content: str) -> str:
    """Fix quiz format: change bullet questions to numbered questions."""
    # Pattern for quiz sections
    lines = content.split('\n')
    in_quiz = False
    result = []
    q_num = 0
    
    for i, line in enumerate(lines):
        if line.startswith('## quiz:'):
            in_quiz = True
            q_num = 0
            result.append(line)
        elif in_quiz and line.startswith('## '):
            in_quiz = False
            result.append(line)
        elif in_quiz and line.startswith('---'):
            in_quiz = False
            result.append(line)
        elif in_quiz and re.match(r'^- [^[\]]', line):
            # This is a quiz question (bullet starting a question, not checkbox)
            q_num += 1
            # Replace "- Question" with "N. Question"
            new_line = f"{q_num}. {line[2:]}"
            result.append(new_line)
        elif in_quiz and re.match(r'^  - \[', line):
            # Answer options - add one more space for indentation
            result.append('   ' + line[2:])
        else:
            result.append(line)
    
    return '\n'.join(result)

def fix_unjumble_format(content: str) -> str:
    """Fix unjumble format: change bullet answers to callout answers."""
    lines = content.split('\n')
    in_unjumble = False
    result = []
    item_num = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('## unjumble:'):
            in_unjumble = True
            item_num = 0
            result.append(line)
            i += 1
        elif in_unjumble and (line.startswith('## ') or line.startswith('---')):
            in_unjumble = False
            result.append(line)
            i += 1
        elif in_unjumble and re.match(r'^- [^[\]]', line):
            # This is an unjumble prompt (bullet starting item)
            item_num += 1
            # Replace "- jumbled words" with "N. jumbled words"
            new_line = f"{item_num}. {line[2:]}"
            result.append(new_line)
            i += 1
            # Check if next line is the answer (nested bullet)
            if i < len(lines) and lines[i].startswith('  - '):
                # Convert nested bullet to callout
                answer = lines[i][4:]  # Remove "  - "
                result.append(f"   > [!answer] {answer}")
                result.append("")  # Add blank line after each item
                i += 1
        else:
            result.append(line)
            i += 1
    
    return '\n'.join(result)

def fix_truefalse_format(content: str) -> str:
    """Fix true-false format: remove embedded TRUE/FALSE text."""
    lines = content.split('\n')
    in_truefalse = False
    result = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('## true-false:'):
            in_truefalse = True
            result.append(line)
            i += 1
        elif in_truefalse and (line.startswith('## ') or line.startswith('---')):
            in_truefalse = False
            result.append(line)
            i += 1
        elif in_truefalse and re.match(r'^- \[.\]', line):
            # This is a true-false statement
            # Remove embedded "— TRUE" or "— FALSE" or "(explanation)"
            cleaned = re.sub(r'\s*[—–-]\s*(TRUE|FALSE).*$', '', line)
            cleaned = cleaned.rstrip('.')  # Remove trailing period if any
            result.append(cleaned + '.')
            i += 1
            # Add explanation as callout if not already there
            if i < len(lines) and not lines[i].startswith('  >'):
                # Extract explanation from the original line if present
                match = re.search(r'(FALSE|TRUE)\s*[\(—–-]?\s*(.+)\)?$', line)
                if match:
                    is_correct = '[x]' in line
                    explanation = match.group(2).strip('() ')
                    if is_correct:
                        result.append(f"  > Correct!")
                    else:
                        result.append(f"  > Incorrect! {explanation}")
                    result.append("")
        else:
            result.append(line)
            i += 1
    
    return '\n'.join(result)

def fix_module(filepath: Path) -> bool:
    """Fix all activity format issues in a module file."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    content = fix_quiz_format(content)
    content = fix_unjumble_format(content)
    content = fix_truefalse_format(content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True
    return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: fix_activity_formats.py <module_file> [...]")
        sys.exit(1)
    
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if path.exists():
            changed = fix_module(path)
            print(f"{'Fixed' if changed else 'No changes'}: {filepath}")
        else:
            print(f"Not found: {filepath}")
