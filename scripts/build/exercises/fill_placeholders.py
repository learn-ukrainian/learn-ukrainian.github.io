"""V6 Step 5b: Fill exercise placeholders in generated content.

Reads markdown content with :::exercise-placeholder blocks, converts each
to the appropriate exercise DSL format that the DSL→MDX converter (#997)
will later transform into interactive React components.

Placeholder format (from writer):
```
:::exercise-placeholder
type: quiz
tests: gender identification
after: він/вона/воно test
items: 6
vocabulary: стіл, книга, вікно, кімната, ліжко, стілець
:::
```

Output DSL format:
```
:::quiz
title: "Він, вона, or воно?"
---
- q: "стіл"
  o: ["він", "вона", "воно"]
  a: 0
- q: "книга"
  o: ["він", "вона", "воно"]
  a: 1
:::
```

Issue: #996
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ExercisePlaceholder:
    """Parsed exercise placeholder from content."""
    exercise_type: str = ""
    tests: str = ""
    after: str = ""
    items: int = 4
    vocabulary: list[str] = field(default_factory=list)
    raw: str = ""


# Regex for finding exercise placeholder blocks
_RE_PLACEHOLDER = re.compile(
    r":::exercise-placeholder\s*\n(.*?):::",
    re.DOTALL,
)


def _parse_placeholder(block: str) -> ExercisePlaceholder:
    """Parse a single exercise placeholder block into structured data."""
    placeholder = ExercisePlaceholder(raw=block)

    for line in block.strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue

        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if key == "type":
            placeholder.exercise_type = value
        elif key == "tests":
            placeholder.tests = value
        elif key == "after":
            placeholder.after = value
        elif key == "items":
            try:
                placeholder.items = int(value)
            except ValueError:
                placeholder.items = 4
        elif key == "vocabulary":
            placeholder.vocabulary = [v.strip() for v in value.split(",") if v.strip()]

    return placeholder


def _generate_exercise_dsl(placeholder: ExercisePlaceholder) -> str:
    """Generate exercise DSL from a parsed placeholder.

    For now, generates a SKELETON that preserves the writer's intent.
    The skeleton contains the exercise type, title derived from the
    'tests' field, and vocabulary items as question stems.

    A future LLM pass or human review fills in the actual content
    (distractors, correct answers, etc.).
    """
    ex_type = placeholder.exercise_type or "quiz"
    tests = placeholder.tests or "practice"
    vocab = placeholder.vocabulary
    items = placeholder.items

    # Generate title from 'tests' field
    title = tests.strip().rstrip(".")
    if title and title[0].islower():
        title = title[0].upper() + title[1:]

    if ex_type == "quiz":
        return _generate_quiz(title, vocab, items)
    elif ex_type == "fill-in":
        return _generate_fill_in(title, vocab, items)
    elif ex_type == "match-up":
        return _generate_match_up(title, vocab, items)
    elif ex_type == "group-sort":
        return _generate_group_sort(title, vocab, items)
    elif ex_type == "true-false":
        return _generate_true_false(title, vocab, items)
    else:
        # Unknown type — return as comment for human review
        return (
            f"<!-- EXERCISE: type={ex_type}, tests={tests}, "
            f"items={items}, vocab={','.join(vocab)} -->\n"
        )


def _generate_quiz(title: str, vocab: list[str], items: int) -> str:
    """Generate quiz DSL skeleton."""
    lines = [':::quiz', f'title: "{title}"', '---']

    for word in vocab[:items]:
        lines.append(f'- q: "{word}"')
        lines.append('  o: ["?", "?", "?"]')
        lines.append('  a: 0')

    # Pad with empty items if vocab is shorter than items
    for _ in range(len(vocab), items):
        lines.append('- q: "?"')
        lines.append('  o: ["?", "?", "?"]')
        lines.append('  a: 0')

    lines.append(":::")
    return "\n".join(lines)


def _generate_fill_in(title: str, vocab: list[str], items: int) -> str:
    """Generate fill-in DSL skeleton."""
    lines = [':::fill-in', f'title: "{title}"', '---']

    for word in vocab[:items]:
        lines.append(f'- sentence: "___ ({word})"')
        lines.append(f'  answer: "{word}"')

    for _ in range(len(vocab), items):
        lines.append('- sentence: "___"')
        lines.append('  answer: "?"')

    lines.append(":::")
    return "\n".join(lines)


def _generate_match_up(title: str, vocab: list[str], items: int) -> str:
    """Generate match-up DSL skeleton."""
    lines = [':::match-up', f'title: "{title}"', '---']

    for word in vocab[:items]:
        lines.append(f'- left: "{word}"')
        lines.append('  right: "?"')

    lines.append(":::")
    return "\n".join(lines)


def _generate_group_sort(title: str, vocab: list[str], items: int) -> str:
    """Generate group-sort DSL skeleton."""
    lines = [':::group-sort', f'title: "{title}"', '---']
    lines.append("groups:")
    lines.append('  - name: "Group A"')
    group_a = ", ".join(f'"{w}"' for w in vocab[:items // 2])
    lines.append(f"    items: [{group_a}]")
    lines.append('  - name: "Group B"')
    group_b = ", ".join(f'"{w}"' for w in vocab[items // 2 : items])
    lines.append(f"    items: [{group_b}]")
    lines.append(":::")
    return "\n".join(lines)


def _generate_true_false(title: str, vocab: list[str], items: int) -> str:
    """Generate true-false DSL skeleton."""
    lines = [':::true-false', f'title: "{title}"', '---']

    for i in range(min(items, max(len(vocab), 4))):
        word = vocab[i] if i < len(vocab) else "?"
        lines.append(f'- statement: "{word}"')
        lines.append('  answer: true')

    lines.append(":::")
    return "\n".join(lines)


def fill_placeholders(content: str) -> tuple[str, int]:
    """Replace all exercise placeholders with DSL skeletons.

    Args:
        content: Markdown content with :::exercise-placeholder blocks.

    Returns:
        Tuple of (content with placeholders replaced, count of replacements).
    """
    count = 0

    def _replace(match: re.Match) -> str:
        nonlocal count
        block_content = match.group(1)
        placeholder = _parse_placeholder(block_content)
        dsl = _generate_exercise_dsl(placeholder)
        count += 1
        return dsl

    result = _RE_PLACEHOLDER.sub(_replace, content)
    return result, count


# CLI for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python scripts/build/exercises/fill_placeholders.py <content.md>")
        sys.exit(1)

    path = Path(sys.argv[1])
    text = path.read_text("utf-8")
    filled, n = fill_placeholders(text)

    if n:
        print(f"✅ Filled {n} placeholder(s)")
        print(filled)
    else:
        print("ℹ️  No placeholders found")
