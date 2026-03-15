"""Activity renderers for l2-uk-direct MDX generation.

Each function converts a single activity dict (from YAML) into JSX markup
for embedding in an MDX page. Used by generate_mdx_direct.
"""

from __future__ import annotations

import json
from typing import Any


def dump_json_for_jsx(obj: Any) -> str:
    """Serialize to JSON suitable for embedding in JSX template literals."""
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    s = s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    s = s.replace("\\\\n", "\\n").replace('\\\\"', '\\"')
    return s


def escape_jsx_string(s: str) -> str:
    """Escape a string for safe inclusion in JSX attributes."""
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_activity(activity: dict) -> str:
    """Convert a single activity dict to JSX by dispatching on type."""
    act_type = activity.get("type", "")
    renderer = _ACTIVITY_RENDERERS.get(act_type)
    if renderer:
        return renderer(activity)
    return f"{{/* Unknown activity type: {act_type} */}}"


def _render_watch_and_repeat(activity: dict) -> str:
    """Render watch_and_repeat activity."""
    items = []
    for item in activity.get("items", []):
        entry: dict[str, str] = {"video": item["video"]}
        if "letter" in item:
            entry["letter"] = item["letter"]
        if "word" in item:
            entry["word"] = item["word"]
        if "note" in item:
            entry["note"] = item["note"]
        items.append(entry)

    title = activity.get("title", "")
    props = f"items={{JSON.parse(`{dump_json_for_jsx(items)}`)}}"
    if title:
        props += f' title="{escape_jsx_string(title)}"'
    return f"<WatchAndRepeat client:only=\"react\" {props} isUkrainian />\n"


def _render_classify(activity: dict) -> str:
    """Render classify activity."""
    categories = []
    for cat in activity.get("categories", []):
        entry: dict[str, Any] = {
            "label": cat["label"],
            "items": cat["items"],
        }
        if "symbol_hint" in cat:
            entry["symbolHint"] = cat["symbol_hint"]
        categories.append(entry)

    title = activity.get("title", "")
    instruction = activity.get("instruction", "")

    props = f"categories={{JSON.parse(`{dump_json_for_jsx(categories)}`)}}"
    if title:
        props += f' title="{escape_jsx_string(title)}"'
    if instruction:
        props += f' instruction="{escape_jsx_string(instruction)}"'
    return f"<Classify client:only=\"react\" {props} isUkrainian />\n"


def _render_image_to_letter(activity: dict) -> str:
    """Render image_to_letter activity."""
    items = []
    for item in activity.get("items", []):
        entry: dict[str, Any] = {
            "emoji": item["emoji"],
            "answer": item["answer"],
            "distractors": item["distractors"],
        }
        if "note" in item:
            entry["note"] = item["note"]
        items.append(entry)

    title = activity.get("title", "")
    props = f"items={{JSON.parse(`{dump_json_for_jsx(items)}`)}}"
    if title:
        props += f' title="{escape_jsx_string(title)}"'
    return f"<ImageToLetter client:only=\"react\" {props} isUkrainian />\n"


def _render_true_false(activity: dict) -> str:
    """Render true_false activity."""
    items = []
    for item in activity.get("items", []):
        entry: dict[str, Any] = {
            "statement": item["statement"],
            "isTrue": item["is_true"],
        }
        if "explanation" in item:
            entry["explanation"] = item["explanation"]
        items.append(entry)

    title = activity.get("title", "")
    instruction = activity.get("instruction", "")

    props = f"items={{JSON.parse(`{dump_json_for_jsx(items)}`)}}"
    if title:
        props += f' title="{escape_jsx_string(title)}"'
    if instruction:
        props += f' instruction="{escape_jsx_string(instruction)}"'
    return f"<TrueFalse client:only=\"react\" {props} isUkrainian />\n"


def _render_build_sentence(activity: dict) -> str:
    """Map build_sentence to Unjumble component."""
    lines = []
    for item in activity.get("items", []):
        words_str = " / ".join(item.get("words", []))
        answer_str = item.get("answer", "")
        hint = item.get("hint", "")
        lines.append(
            f'<Unjumble client:only=\"react\" words="{escape_jsx_string(words_str)}" '
            f'answer="{escape_jsx_string(answer_str)}"'
            + (f' hint="{escape_jsx_string(hint)}"' if hint else "")
            + " isUkrainian />"
        )
    return "\n".join(lines) + "\n"


def _render_match_sound(activity: dict) -> str:
    """Map match_sound to MatchUp component."""
    pairs = [
        {"left": item["letter"], "right": item["description"]}
        for item in activity.get("items", [])
    ]
    props = f"pairs={{JSON.parse(`{dump_json_for_jsx(pairs)}`)}}"
    return f"<MatchUp client:only=\"react\" {props} isUkrainian />\n"


def _render_pattern_drill(activity: dict) -> str:
    """Map pattern_drill to FillIn component."""
    items = []
    prompt = activity.get("prompt", "")
    for item in activity.get("items", []):
        given = item.get("given", "")
        answer = item.get("answer", "")
        sentence = f"{given} \u2192 ___"
        items.append({"sentence": sentence, "answer": answer})

    props = f"items={{JSON.parse(`{dump_json_for_jsx(items)}`)}}"
    if prompt:
        props += f' instruction="{escape_jsx_string(prompt)}"'
    return f"<FillIn client:only=\"react\" {props} isUkrainian />\n"


def _render_riddle(activity: dict) -> str:
    """Map riddle to Quiz component."""
    questions = []
    for item in activity.get("items", []):
        options = [
            {"text": opt, "correct": opt == item.get("answer", "")}
            for opt in item.get("options", [])
        ]
        questions.append({
            "question": item.get("clue", ""),
            "options": options,
        })

    props = f"questions={{JSON.parse(`{dump_json_for_jsx(questions)}`)}}"
    title = activity.get("title", "\u0417\u0430\u0433\u0430\u0434\u043a\u0438")
    return f'<Quiz client:only=\"react\" {props} instruction="{escape_jsx_string(title)}" isUkrainian />\n'


def _render_tongue_twister(activity: dict) -> str:
    """Map tongue_twister to WatchAndRepeat (text + optional video)."""
    items = []
    for item in activity.get("items", []):
        entry: dict[str, str] = {}
        entry["video"] = item.get("video", "")
        entry["word"] = item.get("text", "")
        if "note" in item:
            entry["note"] = item["note"]
        items.append(entry)

    title = activity.get("title", "\u0421\u043a\u043e\u0440\u043e\u043c\u043e\u0432\u043a\u0438")
    props = f"items={{JSON.parse(`{dump_json_for_jsx(items)}`)}}"
    return f'<WatchAndRepeat client:only=\"react\" {props} title="{escape_jsx_string(title)}" isUkrainian />\n'


def _render_reading(activity: dict) -> str:
    """Render reading activity."""
    text = activity.get("text", "")
    title = activity.get("title", "")
    tasks = activity.get("tasks", [])

    props = f'text="{escape_jsx_string(text)}" title="{escape_jsx_string(title)}"'
    if tasks:
        props += f" tasks={{JSON.parse(`{dump_json_for_jsx(tasks)}`)}}"
    return f"<ReadingActivity client:only=\"react\" {props} isUkrainian />\n"


def _render_proverb_drill(activity: dict) -> str:
    """Map proverb_drill to Quiz variant via sub-activity delegation."""
    sub_activity = activity.get("activity", {})
    sub_type = sub_activity.get("type", "true_false")

    if sub_type == "true_false":
        return _render_true_false(sub_activity)
    elif sub_type == "match_meaning":
        return _render_match_sound(sub_activity)
    else:
        return _render_pattern_drill(sub_activity)


# Dispatch table for activity types
_ACTIVITY_RENDERERS = {
    "watch_and_repeat": _render_watch_and_repeat,
    "classify": _render_classify,
    "image_to_letter": _render_image_to_letter,
    "true_false": _render_true_false,
    "build_sentence": _render_build_sentence,
    "match_sound": _render_match_sound,
    "pattern_drill": _render_pattern_drill,
    "riddle": _render_riddle,
    "tongue_twister": _render_tongue_twister,
    "reading": _render_reading,
    "proverb_drill": _render_proverb_drill,
}
