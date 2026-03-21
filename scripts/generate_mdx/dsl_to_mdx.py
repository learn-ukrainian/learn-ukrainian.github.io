"""Convert Exercise DSL blocks to MDX/React components.

Parses exercise blocks in markdown and converts them to
the corresponding React components for Starlight rendering.

Supports two DSL formats:
  - Legacy: :::exercise[type]  (markdown-style content)
  - V6:     :::type            (YAML-style content from fill_placeholders.py)

Usage:
    from generate_mdx.dsl_to_mdx import convert_dsl_to_mdx
    mdx_content = convert_dsl_to_mdx(markdown_content)

Issue: #997
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

# Allow imports from scripts/ when run from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build.text_utils import strip_stray_quotes as _strip_stray_quotes

# ---------------------------------------------------------------------------
# Regex: match both :::exercise[type] (legacy) and :::type (V6) blocks
# Group 1 = legacy type, Group 2 = V6 type, Group 3 = body
# ---------------------------------------------------------------------------
_EXERCISE_RE = re.compile(
    r":::(?:exercise\[([^\]]+)\]|(\w[\w-]*))\n(.*?)\n:::",
    re.DOTALL,
)

# Known V6 exercise types (bare :::type format)
_V6_TYPES = {"quiz", "fill-in", "match-up", "group-sort", "true-false"}

# ---------------------------------------------------------------------------
# YouTube URL → <YouTubeVideo> component
# ---------------------------------------------------------------------------
_YOUTUBE_RE = re.compile(
    r"(?:^|\n)\s*(?:https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)(?:&\S*)?)",
    re.MULTILINE,
)


def _youtube_replace(match: re.Match) -> str:
    """Convert a bare YouTube URL to a <YouTubeVideo> component."""
    video_id = match.group(1)
    url = f"https://www.youtube.com/watch?v={video_id}"
    return f'\n<YouTubeVideo client:only="react" url="{url}" />'


# ---------------------------------------------------------------------------
# V6 helpers
# ---------------------------------------------------------------------------

def _parse_v6_body(body: str) -> tuple[str, str]:
    """Split V6 body into title and YAML content (after ---)."""
    parts = body.split("---", 1)
    title = ""
    yaml_text = body
    if len(parts) == 2:
        header = parts[0].strip()
        yaml_text = parts[1].strip()
        # Extract title from header
        for line in header.split("\n"):
            line = line.strip()
            if line.startswith("title:"):
                title = line[len("title:"):].strip().strip('"').strip("'")
    return title, yaml_text



def _clean_item(obj):
    """Recursively strip stray quotes from strings in dicts/lists."""
    if isinstance(obj, str):
        return _strip_stray_quotes(obj)
    if isinstance(obj, list):
        return [_clean_item(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _clean_item(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# V6 converters
# ---------------------------------------------------------------------------

def _convert_v6_quiz(body: str) -> str:
    """Convert V6 quiz DSL to <Quiz> component."""
    _title, yaml_text = _parse_v6_body(body)
    try:
        items = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return f"<!-- Failed to parse V6 quiz -->\n{body}"

    if not isinstance(items, list) or not items:
        return f"<!-- Failed to parse V6 quiz: no items -->\n{body}"

    questions = []
    for item in items:
        q = _strip_stray_quotes(item.get("q", ""))
        options_raw = item.get("o", [])
        answer_idx = item.get("a", 0)
        options = []
        for i, opt in enumerate(options_raw):
            opt = _strip_stray_quotes(str(opt))
            options.append({"text": opt, "correct": i == answer_idx})
        questions.append({"question": q, "options": options})

    return (
        f'<Quiz client:only="react" '
        f'questions={{{json.dumps(questions, ensure_ascii=False)}}} />'
    )


def _convert_v6_fill_in(body: str) -> str:
    """Convert V6 fill-in DSL to <FillIn> component."""
    _title, yaml_text = _parse_v6_body(body)
    try:
        items = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return f"<!-- Failed to parse V6 fill-in -->\n{body}"

    if not isinstance(items, list) or not items:
        return f"<!-- Failed to parse V6 fill-in: no items -->\n{body}"

    fill_items = []
    for item in items:
        sentence = _strip_stray_quotes(item.get("sentence", ""))
        answer = _strip_stray_quotes(item.get("answer", ""))
        fill_items.append({"sentence": sentence, "answer": answer})

    return (
        f'<FillIn client:only="react" '
        f'items={{{json.dumps(fill_items, ensure_ascii=False)}}} />'
    )


def _convert_v6_match_up(body: str) -> str:
    """Convert V6 match-up DSL to <MatchUp> component."""
    _title, yaml_text = _parse_v6_body(body)
    try:
        items = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return f"<!-- Failed to parse V6 match-up -->\n{body}"

    if not isinstance(items, list) or not items:
        return f"<!-- Failed to parse V6 match-up: no items -->\n{body}"

    pairs = []
    for item in items:
        left = _strip_stray_quotes(item.get("left", ""))
        right = _strip_stray_quotes(item.get("right", ""))
        pairs.append({"left": left, "right": right})

    return (
        f'<MatchUp client:only="react" '
        f'pairs={{{json.dumps(pairs, ensure_ascii=False)}}} />'
    )


def _convert_v6_group_sort(body: str) -> str:
    """Convert V6 group-sort DSL to <GroupSort> component."""
    _title, yaml_text = _parse_v6_body(body)
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return f"<!-- Failed to parse V6 group-sort -->\n{body}"

    # data could be a dict with 'groups' key, or the YAML might contain it
    groups = None
    if isinstance(data, dict):
        groups = data.get("groups", [])
    if not groups:
        return f"<!-- Failed to parse V6 group-sort: no groups -->\n{body}"

    groups = _clean_item(groups)
    return (
        f'<GroupSort client:only="react" '
        f'groups={{{json.dumps(groups, ensure_ascii=False)}}} />'
    )


def _convert_v6_true_false(body: str) -> str:
    """Convert V6 true-false DSL to <TrueFalse> component."""
    _title, yaml_text = _parse_v6_body(body)
    try:
        items = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return f"<!-- Failed to parse V6 true-false -->\n{body}"

    if not isinstance(items, list) or not items:
        return f"<!-- Failed to parse V6 true-false: no items -->\n{body}"

    tf_items = []
    for item in items:
        statement = _strip_stray_quotes(item.get("statement", ""))
        answer = bool(item.get("answer", False))
        tf_items.append({"statement": statement, "answer": answer})

    return (
        f'<TrueFalse client:only="react" '
        f'items={{{json.dumps(tf_items, ensure_ascii=False)}}} />'
    )


_V6_CONVERTERS = {
    "quiz": _convert_v6_quiz,
    "fill-in": _convert_v6_fill_in,
    "match-up": _convert_v6_match_up,
    "group-sort": _convert_v6_group_sort,
    "true-false": _convert_v6_true_false,
}

# ---------------------------------------------------------------------------
# Legacy converters (:::exercise[type] with markdown-style content)
# ---------------------------------------------------------------------------


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


_LEGACY_CONVERTERS = {
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def convert_dsl_to_mdx(text: str) -> tuple[str, int]:
    """Convert all exercise DSL blocks to MDX components.

    Handles both legacy :::exercise[type] and V6 :::type formats.
    Also converts bare YouTube URLs to <YouTubeVideo> components.

    Returns (mdx_content, count_of_conversions).
    """
    count = 0

    def _replace(match: re.Match) -> str:
        nonlocal count
        legacy_type = match.group(1)  # from :::exercise[type]
        v6_type = match.group(2)      # from :::type
        body = match.group(3)

        if legacy_type:
            # Legacy format: :::exercise[type]
            converter = _LEGACY_CONVERTERS.get(legacy_type)
            if converter:
                count += 1
                return converter(body)
            return f"<!-- Unknown exercise type: {legacy_type} -->\n{match.group(0)}"

        if v6_type:
            # V6 format: :::type
            v6_converter = _V6_CONVERTERS.get(v6_type)
            if v6_converter:
                count += 1
                return v6_converter(body)
            # Not a known exercise type — leave untouched (could be
            # an admonition like :::note or :::tip)
            return match.group(0)

        return match.group(0)

    result = _EXERCISE_RE.sub(_replace, text)

    # Convert bare YouTube URLs
    def _yt_replace(m: re.Match) -> str:
        nonlocal count
        count += 1
        return _youtube_replace(m)

    result = _YOUTUBE_RE.sub(_yt_replace, result)

    # Clean stray quotes that leaked from DSL: "'text'" → "text"
    result = re.sub(r"\"'([^\"]*)'\"", r'"\1"', result)

    return result, count
