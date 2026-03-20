"""Convert Exercise DSL blocks to MDX/React components.

Parses :::exercise[type] blocks in markdown and converts them to
the corresponding React components for Starlight rendering.

Usage:
    from generate_mdx.dsl_to_mdx import convert_dsl_to_mdx
    mdx_content = convert_dsl_to_mdx(markdown_content)

Issue: #997
"""

from __future__ import annotations

import json
import re

# Parse :::exercise[type] blocks
_EXERCISE_RE = re.compile(
    r':::exercise\[([^\]]+)\]\n(.*?)\n:::', re.DOTALL
)


def _convert_multiple_choice(content: str) -> str:
    """Convert multiple-choice DSL to <Quiz> component."""
    lines = content.strip().split("\n")
    question = lines[0] if lines else "Choose the correct answer"

    items = []
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("- [x]"):
            text = line[5:].strip()
            items.append({"text": text, "correct": True})
        elif line.startswith("- [ ]"):
            text = line[5:].strip()
            items.append({"text": text, "correct": False})

    if not items:
        return f"<!-- Failed to parse multiple-choice exercise -->\n{content}"

    quiz_data = [{
        "question": question,
        "options": [{"text": i["text"], "correct": i["correct"]} for i in items],
    }]

    return (
        f'<Quiz client:only="react" questions={{{json.dumps(quiz_data, ensure_ascii=False)}}} />'
    )


def _convert_cloze(content: str) -> str:
    """Convert cloze DSL to <FillIn> component."""
    lines = content.strip().split("\n")

    items = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("<!--"):
            continue
        # Find {answer} pattern
        match = re.search(r'\{([^}]+)\}', line)
        if match:
            answer = match.group(1)
            # Create the sentence with blank
            sentence = line[:match.start()] + "___" + line[match.end():]
            # Clean up the explanation part after —
            items.append({
                "sentence": sentence.split("—")[0].strip(),
                "answer": answer,
            })

    if not items:
        return f"<!-- Failed to parse cloze exercise -->\n{content}"

    return (
        f'<FillIn client:only="react" items={{{json.dumps(items, ensure_ascii=False)}}} />'
    )


def _convert_match(content: str) -> str:
    """Convert match DSL to <MatchUp> component."""
    pairs = []
    lines = content.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("|") and "---" not in line and "Left" not in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 2:
                pairs.append({"left": cells[0], "right": cells[1]})

    if not pairs:
        return f"<!-- Failed to parse match exercise -->\n{content}"

    return (
        f'<MatchUp client:only="react" pairs={{{json.dumps(pairs, ensure_ascii=False)}}} />'
    )


def _convert_true_false(content: str) -> str:
    """Convert true-false DSL to <TrueFalse> component."""
    items = []
    lines = content.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("- [true]"):
            items.append({"statement": line[8:].strip(), "answer": True})
        elif line.startswith("- [false]"):
            items.append({"statement": line[9:].strip(), "answer": False})

    if not items:
        return f"<!-- Failed to parse true-false exercise -->\n{content}"

    return (
        f'<TrueFalse client:only="react" items={{{json.dumps(items, ensure_ascii=False)}}} />'
    )


def _convert_group_sort(content: str) -> str:
    """Convert group-sort DSL to <GroupSort> component."""
    import yaml

    try:
        data = yaml.safe_load(content)
        groups = data.get("groups", [])
        if groups:
            return (
                f'<GroupSort client:only="react" groups={{{json.dumps(groups, ensure_ascii=False)}}} />'
            )
    except Exception:
        pass

    return f"<!-- Failed to parse group-sort exercise -->\n{content}"


def _convert_read_and_answer(content: str) -> str:
    """Convert read-and-answer DSL to <ReadingActivity> component."""
    # Split into text block and questions
    parts = content.strip().split("\n\n")
    text_block = ""
    questions = []

    for part in parts:
        if part.startswith(">"):
            text_block = part.replace("> ", "").replace(">", "")
        else:
            for line in part.split("\n"):
                match = re.match(r'\d+\.\s+(.+?)\s*—\s*\{(.+?)\}', line)
                if match:
                    questions.append({
                        "question": match.group(1),
                        "answer": match.group(2),
                    })

    if not text_block or not questions:
        return f"<!-- Failed to parse read-and-answer exercise -->\n{content}"

    data = {"text": text_block, "questions": questions}
    return (
        f'<ReadingActivity client:only="react" data={{{json.dumps(data, ensure_ascii=False)}}} />'
    )


_CONVERTERS = {
    "multiple-choice": _convert_multiple_choice,
    "quiz": _convert_multiple_choice,  # alias
    "cloze": _convert_cloze,
    "fill-in": _convert_cloze,  # alias
    "match": _convert_match,
    "match-up": _convert_match,  # alias
    "true-false": _convert_true_false,
    "group-sort": _convert_group_sort,
    "read-and-answer": _convert_read_and_answer,
}


def convert_dsl_to_mdx(text: str) -> tuple[str, int]:
    """Convert all :::exercise[type] blocks to MDX components.

    Returns (mdx_content, count_of_conversions).
    """
    count = 0

    def _replace(match):
        nonlocal count
        exercise_type = match.group(1)
        content = match.group(2)

        converter = _CONVERTERS.get(exercise_type)
        if converter:
            count += 1
            return converter(content)
        else:
            return f"<!-- Unknown exercise type: {exercise_type} -->\n{match.group(0)}"

    result = _EXERCISE_RE.sub(_replace, text)
    return result, count
