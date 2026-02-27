#!/usr/bin/env python3
"""generate_mdx_direct.py — Convert l2-uk-direct YAML modules to MDX pages.

Usage:
    .venv/bin/python scripts/generate_mdx_direct.py --module curriculum/l2-uk-direct/a1/abetka.yaml
    .venv/bin/python scripts/generate_mdx_direct.py --all --level a1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

CURRICULUM_ROOT = Path("curriculum/l2-uk-direct")
OUTPUT_ROOT = Path("starlight/src/content/docs/direct")

# Activity type → React component name
ACTIVITY_COMPONENT_MAP: dict[str, str] = {
    "watch_and_repeat": "WatchAndRepeat",
    "classify": "Classify",
    "image_to_letter": "ImageToLetter",
    "true_false": "TrueFalse",
    "build_sentence": "Unjumble",
    "match_sound": "MatchUp",
    "pattern_drill": "FillIn",
    "riddle": "Quiz",
    "tongue_twister": "WatchAndRepeat",
    "reading": "ReadingActivity",
    "proverb_drill": "Quiz",
}

# Module type → renderer function name
MODULE_RENDERERS = {
    "script_foundation",
    "communicative",
    "vocabulary",
    "grammar",
    "checkpoint",
}

# Pre-literacy gate: modules 1-2 can only use these activity types
PRE_LITERACY_ACTIVITIES = {"watch_and_repeat", "classify", "image_to_letter"}

# Session grouping for abetka: letter groups by pedagogical sequence
ABETKA_SESSIONS = [
    {
        "title": "Голосні",
        "subtitle": "Vowels — 10 letters",
        "filter": lambda l: l["sound_type"] == "vowel",
    },
    {
        "title": "Сонорні",
        "subtitle": "Sonorants — Л, М, Н, Р",
        "filter": lambda l: l["upper"] in {"Л", "М", "Н", "Р"},
    },
    {
        "title": "Дзвінкі приголосні",
        "subtitle": "Voiced consonants — Б, В, Г, Ґ, Д, Ж, З",
        "filter": lambda l: l["upper"] in {"Б", "В", "Г", "Ґ", "Д", "Ж", "З"},
    },
    {
        "title": "Глухі приголосні",
        "subtitle": "Voiceless — К, П, С, Т, Ф, Х, Ц, Ч, Ш, Щ",
        "filter": lambda l: l["upper"]
        in {"К", "П", "С", "Т", "Ф", "Х", "Ц", "Ч", "Ш", "Щ"},
    },
    {
        "title": "Особливі",
        "subtitle": "Special — Й, Ь, apostrophe, digraphs",
        "filter": lambda l: l["upper"] in {"Й", "Ь"},
    },
]


# ──────────────────────────────────────────────
# JSON/JSX Helpers
# ──────────────────────────────────────────────


def dump_json_for_jsx(obj: Any) -> str:
    """Serialize to JSON suitable for embedding in JSX template literals."""
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    # Escape backticks and ${} for JSX template literal safety
    s = s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    # Undo double-escape of already-escaped chars in JSON strings
    s = s.replace("\\\\n", "\\n").replace('\\\\"', '\\"')
    return s


def escape_jsx_string(s: str) -> str:
    """Escape a string for safe inclusion in JSX attributes."""
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


# ──────────────────────────────────────────────
# Module Loaders
# ──────────────────────────────────────────────


def load_module(path: Path) -> dict:
    """Load and validate a l2-uk-direct module YAML."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict at root of {path}, got {type(data).__name__}")

    required = {"module", "track", "level", "type", "title"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Missing required keys in {path}: {missing}")

    if data["type"] not in MODULE_RENDERERS:
        raise ValueError(
            f"Unknown module type '{data['type']}' in {path}. "
            f"Must be one of: {MODULE_RENDERERS}"
        )

    return data


# ──────────────────────────────────────────────
# Import Collector
# ──────────────────────────────────────────────


def collect_imports(module_data: dict) -> list[str]:
    """Determine which React components to import based on module content."""
    imports: set[str] = set()

    # Content-driven imports
    if module_data.get("letters"):
        imports.add("LetterGrid")

    if module_data.get("vocabulary"):
        imports.add("VocabCard")

    if module_data.get("phrases"):
        imports.add("PhraseTable")

    if module_data.get("dialogues"):
        imports.add("DialogueBox")

    # Activity-driven imports
    for activity in module_data.get("activities", []):
        act_type = activity.get("type", "")
        component = ACTIVITY_COMPONENT_MAP.get(act_type)
        if component:
            imports.add(component)

    # Map component names to import paths
    import_lines = []
    for comp in sorted(imports):
        import_lines.append(f"import {comp} from '../../../../components/{comp}';")

    return import_lines


# ──────────────────────────────────────────────
# Activity Renderers
# ──────────────────────────────────────────────


def render_activity(activity: dict) -> str:
    """Convert a single activity dict to JSX."""
    act_type = activity.get("type", "")

    if act_type == "watch_and_repeat":
        return _render_watch_and_repeat(activity)
    elif act_type == "classify":
        return _render_classify(activity)
    elif act_type == "image_to_letter":
        return _render_image_to_letter(activity)
    elif act_type == "true_false":
        return _render_true_false(activity)
    elif act_type == "build_sentence":
        return _render_build_sentence(activity)
    elif act_type == "match_sound":
        return _render_match_sound(activity)
    elif act_type == "pattern_drill":
        return _render_pattern_drill(activity)
    elif act_type == "riddle":
        return _render_riddle(activity)
    elif act_type == "tongue_twister":
        return _render_tongue_twister(activity)
    elif act_type == "reading":
        return _render_reading(activity)
    elif act_type == "proverb_drill":
        return _render_proverb_drill(activity)
    else:
        return f"{{/* Unknown activity type: {act_type} */}}"


def _render_watch_and_repeat(activity: dict) -> str:
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
    return f"<WatchAndRepeat client:load {props} isUkrainian />\n"


def _render_classify(activity: dict) -> str:
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
    return f"<Classify client:load {props} isUkrainian />\n"


def _render_image_to_letter(activity: dict) -> str:
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
    return f"<ImageToLetter client:load {props} isUkrainian />\n"


def _render_true_false(activity: dict) -> str:
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
    return f"<TrueFalse client:load {props} isUkrainian />\n"


def _render_build_sentence(activity: dict) -> str:
    """Map build_sentence to Unjumble component."""
    lines = []
    for item in activity.get("items", []):
        words_str = " / ".join(item.get("words", []))
        answer_str = item.get("answer", "")
        hint = item.get("hint", "")
        lines.append(
            f'<Unjumble client:load words="{escape_jsx_string(words_str)}" '
            f'answer="{escape_jsx_string(answer_str)}"'
            + (f' hint="{escape_jsx_string(hint)}"' if hint else "")
            + " isUkrainian />"
        )
    return "\n".join(lines) + "\n"


def _render_match_sound(activity: dict) -> str:
    """Map match_sound to MatchUp component."""
    pairs = []
    for item in activity.get("items", []):
        pairs.append({"left": item["letter"], "right": item["description"]})

    props = f"pairs={{JSON.parse(`{dump_json_for_jsx(pairs)}`)}}"
    return f"<MatchUp client:load {props} isUkrainian />\n"


def _render_pattern_drill(activity: dict) -> str:
    """Map pattern_drill to FillIn component."""
    items = []
    prompt = activity.get("prompt", "")
    for item in activity.get("items", []):
        given = item.get("given", "")
        answer = item.get("answer", "")
        sentence = f"{given} → ___"
        items.append({"sentence": sentence, "answer": answer})

    props = f"items={{JSON.parse(`{dump_json_for_jsx(items)}`)}}"
    if prompt:
        props += f' instruction="{escape_jsx_string(prompt)}"'
    return f"<FillIn client:load {props} isUkrainian />\n"


def _render_riddle(activity: dict) -> str:
    """Map riddle to Quiz component."""
    questions = []
    for item in activity.get("items", []):
        options = []
        for opt in item.get("options", []):
            options.append({"text": opt, "correct": opt == item.get("answer", "")})
        questions.append({
            "question": item.get("clue", ""),
            "options": options,
        })

    props = f"questions={{JSON.parse(`{dump_json_for_jsx(questions)}`)}}"
    title = activity.get("title", "Загадки")
    return f'<Quiz client:load {props} instruction="{escape_jsx_string(title)}" isUkrainian />\n'


def _render_tongue_twister(activity: dict) -> str:
    """Map tongue_twister to WatchAndRepeat (text + optional video)."""
    items = []
    for item in activity.get("items", []):
        entry: dict[str, str] = {}
        if "video" in item:
            entry["video"] = item["video"]
        else:
            # Use empty video placeholder; component handles missing video gracefully
            entry["video"] = ""
        entry["word"] = item.get("text", "")
        if "note" in item:
            entry["note"] = item["note"]
        items.append(entry)

    title = activity.get("title", "Скоромовки")
    props = f"items={{JSON.parse(`{dump_json_for_jsx(items)}`)}}"
    return f'<WatchAndRepeat client:load {props} title="{escape_jsx_string(title)}" isUkrainian />\n'


def _render_reading(activity: dict) -> str:
    text = activity.get("text", "")
    title = activity.get("title", "")
    tasks = activity.get("tasks", [])

    props = f'text="{escape_jsx_string(text)}" title="{escape_jsx_string(title)}"'
    if tasks:
        props += f" tasks={{JSON.parse(`{dump_json_for_jsx(tasks)}`)}}"
    return f"<ReadingActivity client:load {props} isUkrainian />\n"


def _render_proverb_drill(activity: dict) -> str:
    """Map proverb_drill to Quiz variant."""
    # proverb_drill has nested activity with sub-types; simplify to quiz
    sub_activity = activity.get("activity", {})
    sub_type = sub_activity.get("type", "true_false")

    if sub_type == "true_false":
        return _render_true_false(sub_activity)
    elif sub_type == "match_meaning":
        return _render_match_sound(sub_activity)
    else:
        # fill_gap → FillIn
        return _render_pattern_drill(sub_activity)


# ──────────────────────────────────────────────
# Content Renderers by Module Type
# ──────────────────────────────────────────────


def render_script_foundation(data: dict) -> str:
    """Render script_foundation modules (abetka, sklad, naholos)."""
    lines: list[str] = []
    letters = data.get("letters", [])

    if data.get("module") == "abetka" and letters:
        # Group letters into pedagogical sessions
        assigned: set[str] = set()

        for session in ABETKA_SESSIONS:
            session_letters = [
                l for l in letters if session["filter"](l) and l["upper"] not in assigned
            ]
            if not session_letters:
                continue

            for l in session_letters:
                assigned.add(l["upper"])

            lines.append(f"\n## {session['title']}\n")
            lines.append(f"*{session['subtitle']}*\n")

            # LetterGrid for this group
            grid_data = [
                {
                    "upper": l["upper"],
                    "lower": l["lower"],
                    "emoji": l.get("emoji", ""),
                    "key_word": l.get("key_word", ""),
                    "note": l.get("note", ""),
                    "sound_type": l.get("sound_type", "consonant"),
                }
                for l in session_letters
            ]
            lines.append(
                f"<LetterGrid client:load letters={{JSON.parse(`{dump_json_for_jsx(grid_data)}`)}} />\n"
            )

            # WatchAndRepeat for this group's videos
            war_items = [
                {
                    "letter": l["upper"],
                    "video": l.get("pronunciation_video", ""),
                }
                for l in session_letters
                if l.get("pronunciation_video")
            ]
            if war_items:
                lines.append(
                    f'<WatchAndRepeat client:load items={{JSON.parse(`{dump_json_for_jsx(war_items)}`)}} '
                    f'title="Повтори: {session["title"]}" isUkrainian />\n'
                )

        # Handle any unassigned letters
        remaining = [l for l in letters if l["upper"] not in assigned]
        if remaining:
            lines.append("\n## Інші букви\n")
            grid_data = [
                {
                    "upper": l["upper"],
                    "lower": l["lower"],
                    "emoji": l.get("emoji", ""),
                    "key_word": l.get("key_word", ""),
                    "sound_type": l.get("sound_type", "consonant"),
                }
                for l in remaining
            ]
            lines.append(
                f"<LetterGrid client:load letters={{JSON.parse(`{dump_json_for_jsx(grid_data)}`)}} />\n"
            )

        # Apostrophe section
        apostrophe = data.get("apostrophe")
        if apostrophe:
            lines.append("\n## Апостроф\n")
            lines.append(
                f"**{apostrophe['symbol']}** — {apostrophe.get('note', '')}\n"
            )
            if apostrophe.get("example_word"):
                lines.append(
                    f"\n{apostrophe.get('emoji', '')} *{apostrophe['example_word']}*\n"
                )

        # Digraphs section
        digraphs = data.get("digraphs")
        if digraphs:
            lines.append("\n## Буквосполучення\n")
            lines.append("*Дві букви — один звук*\n")
            for dg in digraphs:
                letters_str = dg.get("letters", "")
                note = dg.get("note", "")
                kw = dg.get("key_word", "")
                emoji = dg.get("emoji", "")
                lines.append(f"**{letters_str}** — {note}")
                if kw:
                    lines.append(f"  {emoji} *{kw}*\n")

        # Stress section
        stress = data.get("stress")
        if stress:
            lines.append("\n## Наголос\n")
            lines.append(f"{stress.get('rule', '')}\n")
            lines.append(f"\n{stress.get('marker', '')}\n")
            if stress.get("examples"):
                lines.append("")
                for ex in stress["examples"]:
                    lines.append(f"- **{ex['word']}** (наголос: *{ex['stressed_syllable']}*)")
                lines.append("")

    else:
        # Generic script_foundation (sklad, naholos, etc.)

        # Syllable rule section
        syllable_rule = data.get("syllable_rule")
        if syllable_rule:
            lines.append("\n## Що таке склад?\n")
            lines.append(f"{syllable_rule.get('text', '')}\n")
            vowels = syllable_rule.get("vowels", [])
            if vowels:
                lines.append(
                    f"\nГолосні: **{' '.join(vowels)}** ({len(vowels)} букв)\n"
                )
            examples = syllable_rule.get("examples", [])
            if examples:
                lines.append("")
                for ex in examples:
                    count = ex["syllables"]
                    suffix = (
                        "склад"
                        if count == 1
                        else "склади" if count < 5 else "складів"
                    )
                    lines.append(
                        f"- {ex.get('emoji', '')} **{ex['word']}** → "
                        f"{ex['split']} ({count} {suffix})"
                    )
                lines.append("")

        # Syllable tables (CV / VC grids)
        tables = data.get("syllable_tables", [])
        for table in tables:
            lines.append(f"\n## {table.get('title', '')}\n")
            if table.get("subtitle"):
                lines.append(f"*{table['subtitle']}*\n")

            if table.get("type") == "cv":
                consonants = table.get("consonants", [])
                vowels = table.get("vowels", [])
                header = "| |" + " | ".join(f"**{v}**" for v in vowels) + " |"
                divider = "|---|" + "|".join("---" for _ in vowels) + "|"
                lines.append(header)
                lines.append(divider)
                for c in consonants:
                    row = (
                        f"| **{c}** |"
                        + " | ".join(f"{c}{v.lower()}" for v in vowels)
                        + " |"
                    )
                    lines.append(row)
                lines.append("")

            elif table.get("type") == "vc":
                vowels = table.get("vowels", [])
                consonants = table.get("consonants", [])
                header = "| |" + " | ".join(f"**{c}**" for c in consonants) + " |"
                divider = "|---|" + "|".join("---" for _ in consonants) + "|"
                lines.append(header)
                lines.append(divider)
                for v in vowels:
                    row = (
                        f"| **{v}** |"
                        + " | ".join(f"{v.lower()}{c.lower()}" for c in consonants)
                        + " |"
                    )
                    lines.append(row)
                lines.append("")

        # Soft consonants
        soft = data.get("soft_consonants")
        if soft:
            lines.append("\n## М'які приголосні\n")
            lines.append(f"{soft.get('rule', '')}\n")
            soft_examples = soft.get("examples", [])
            if soft_examples:
                lines.append("")
                for ex in soft_examples:
                    lines.append(
                        f"- {ex.get('hard', '')} → **{ex.get('soft', '')}** "
                        f"— {ex.get('note', '')}"
                    )
                lines.append("")
            soft_words = soft.get("words", [])
            if soft_words:
                lines.append("")
                for w in soft_words:
                    lines.append(
                        f"- {w.get('emoji', '')} **{w['word']}** "
                        f"— {w.get('note', '')}"
                    )
                lines.append("")

        # Apostrophe
        apostrophe = data.get("apostrophe")
        if apostrophe:
            lines.append("\n## Апостроф\n")
            lines.append(f"{apostrophe.get('rule', '')}\n")
            apo_examples = apostrophe.get("examples", [])
            if apo_examples:
                lines.append("")
                for ex in apo_examples:
                    lines.append(
                        f"- {ex.get('emoji', '')} **{ex['word']}** "
                        f"({ex.get('split', '')})"
                    )
                lines.append("")

        # Stress
        stress = data.get("stress")
        if stress:
            lines.append("\n## Наголос\n")
            lines.append(f"{stress.get('rule', '')}\n")
            if stress.get("marker"):
                lines.append(f"\n{stress['marker']}\n")
            meaning = stress.get("meaning_change")
            if meaning:
                lines.append(f"\n### {meaning.get('note', '')}\n")
                pairs = meaning.get("pairs", [])
                for pair in pairs:
                    lines.append(
                        f"- {pair.get('emoji1', '')} **{pair['word1']}** "
                        f"— {pair.get('meaning1', '')}"
                    )
                    lines.append(
                        f"- {pair.get('emoji2', '')} **{pair['word2']}** "
                        f"— {pair.get('meaning2', '')}"
                    )
                    lines.append("")

        # Letters grid (if module has letters)
        if letters:
            grid_data = [
                {
                    "upper": l["upper"],
                    "lower": l["lower"],
                    "emoji": l.get("emoji", ""),
                    "key_word": l.get("key_word", ""),
                    "sound_type": l.get("sound_type", "consonant"),
                }
                for l in letters
            ]
            lines.append(
                f"<LetterGrid client:load letters={{JSON.parse("
                f"`{dump_json_for_jsx(grid_data)}`)}} />\n"
            )

        # Vocabulary with syllable info
        vocab = data.get("vocabulary")
        if vocab:
            words = []
            for v in vocab:
                count = v.get("syllables", 0)
                split = v.get("split", "")
                suffix = (
                    "склад"
                    if count == 1
                    else "склади" if count < 5 else "складів"
                )
                examples = [f"{split} — {count} {suffix}"] if split else []
                words.append(
                    {
                        "word": v.get("word", ""),
                        "emoji": v.get("emoji", ""),
                        "image_url": v.get("image_url"),
                        "pronunciation_video": "",
                        "examples": examples,
                        "category": "",
                        "question": "",
                    }
                )
            lines.append("\n## Слова по складах\n")
            lines.append(
                f"<VocabCard client:load words={{JSON.parse("
                f"`{dump_json_for_jsx(words)}`)}} "
                f'title="Слова по складах" isUkrainian />\n'
            )

    return "\n".join(lines)


def render_communicative(data: dict) -> str:
    """Render communicative modules (pryvit, etc.)."""
    lines: list[str] = []

    # Phrases by function
    phrases = data.get("phrases")
    if phrases:
        groups = []
        for group in phrases:
            groups.append({
                "function": group.get("function", ""),
                "phrases": [
                    {
                        "phrase": p.get("phrase", ""),
                        "context": p.get("context", ""),
                        "emoji": p.get("emoji", ""),
                    }
                    for p in group.get("items", [])
                ],
            })
        lines.append(
            f"<PhraseTable client:load groups={{JSON.parse(`{dump_json_for_jsx(groups)}`)}} isUkrainian />\n"
        )

    # Dialogues
    dialogues = data.get("dialogues")
    if dialogues:
        for dlg in dialogues:
            exchanges = [
                {
                    "speaker": ex.get("speaker", ""),
                    "text": ex.get("text", ""),
                    "emoji": ex.get("emoji", ""),
                }
                for ex in dlg.get("exchanges", [])
            ]
            title = dlg.get("title", "")
            props = f"exchanges={{JSON.parse(`{dump_json_for_jsx(exchanges)}`)}}"
            if title:
                props += f' title="{escape_jsx_string(title)}"'
            lines.append(f"<DialogueBox client:load {props} isUkrainian />\n")

    return "\n".join(lines)


def render_vocabulary_module(data: dict) -> str:
    """Render vocabulary modules."""
    lines: list[str] = []

    vocab = data.get("vocabulary")
    if vocab:
        words = [
            {
                "word": w.get("word", ""),
                "emoji": w.get("emoji", ""),
                "image_url": w.get("image_url"),
                "pronunciation_video": w.get("pronunciation_video", ""),
                "examples": w.get("examples", []),
                "category": w.get("category", ""),
                "question": w.get("question", ""),
            }
            for w in vocab
        ]
        lines.append(
            f"<VocabCard client:load words={{JSON.parse(`{dump_json_for_jsx(words)}`)}} isUkrainian />\n"
        )

    return "\n".join(lines)


def render_grammar(data: dict) -> str:
    """Render grammar modules."""
    lines: list[str] = []

    # Grammar patterns (tables rendered as markdown)
    patterns = data.get("patterns")
    if patterns:
        for pattern in patterns:
            lines.append(f"\n## {pattern.get('title', '')}\n")
            if pattern.get("question_word"):
                lines.append(f"**{pattern['question_word']}**\n")
            if pattern.get("explanation"):
                lines.append(f"{pattern['explanation']}\n")
            if pattern.get("examples"):
                for ex in pattern["examples"]:
                    lines.append(f"- {ex}")
                lines.append("")

    return "\n".join(lines)


def render_checkpoint(data: dict) -> str:
    """Render checkpoint modules (assessment only)."""
    lines: list[str] = []

    summary = data.get("summary")
    if summary:
        lines.append(f"\n{summary}\n")

    # Checkpoints reference prior modules
    refs = data.get("references")
    if refs:
        lines.append("\n### Повторення\n")
        for ref in refs:
            lines.append(f"- {ref}")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Main MDX Generator
# ──────────────────────────────────────────────


def generate_mdx(data: dict, order: int = 1) -> str:
    """Generate a complete MDX string from a module data dict."""
    module_type = data["type"]
    title = data["title"]
    slug = data["module"]

    # Collect imports
    import_lines = collect_imports(data)

    # Build frontmatter
    frontmatter = [
        "---",
        f'title: "{escape_jsx_string(title)}"',
        f"sidebar:",
        f"  order: {order}",
    ]

    # Add description from standard_ref if present
    if data.get("standard_ref"):
        frontmatter.append(f'  badge:')
        frontmatter.append(f'    text: "{data["level"].upper()}"')

    frontmatter.append("---")

    # Render body by module type
    if module_type == "script_foundation":
        body = render_script_foundation(data)
    elif module_type == "communicative":
        body = render_communicative(data)
    elif module_type == "vocabulary":
        body = render_vocabulary_module(data)
    elif module_type == "grammar":
        body = render_grammar(data)
    elif module_type == "checkpoint":
        body = render_checkpoint(data)
    else:
        body = f"{{/* Module type '{module_type}' not yet implemented */}}"

    # Overview video
    overview = data.get("overview_video")
    overview_credit = data.get("overview_credit", "")
    overview_section = ""
    if overview:
        vid_id_match = __import__("re").search(
            r"(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})", overview
        )
        if vid_id_match:
            vid_id = vid_id_match.group(1)
            # Use a linked thumbnail instead of a raw iframe to avoid
            # YouTube "sign in to prove you are not a robot" bot detection.
            overview_section = (
                f"\n## Огляд\n\n"
                f'<a href="{overview}" target="_blank" rel="noopener noreferrer" '
                f'style={{{{ display: "block", maxWidth: "640px", margin: "0 auto", position: "relative" }}}}>\n'
                f'  <img\n'
                f'    src="https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"\n'
                f'    alt="Overview video"\n'
                f'    style={{{{ width: "100%", borderRadius: "8px", display: "block" }}}}\n'
                f"  />\n"
                f'  <span style={{{{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", '
                f'fontSize: "2rem", color: "#fff", background: "rgba(255,0,0,0.8)", '
                f'width: "64px", height: "44px", display: "flex", alignItems: "center", '
                f'justifyContent: "center", borderRadius: "12px" }}}}>▶</span>\n'
                f"</a>\n"
            )
            if overview_credit:
                overview_section += f"\n*{overview_credit}*\n"

    # Activities section
    activities = data.get("activities", [])
    activities_section = ""
    if activities:
        activities_section = "\n## Вправи\n\n"
        for act in activities:
            activities_section += render_activity(act) + "\n"

    # Playlist credit
    playlist_credit = ""
    if data.get("playlist_credit"):
        playlist_credit = (
            f"\n---\n\n"
            f"*Відео: [{data['playlist_credit']}]({data.get('playlist', '')})*\n"
        )

    # Assemble MDX
    mdx_parts = [
        "\n".join(frontmatter),
        "",
        "\n".join(import_lines),
        "",
        f"# {title}",
        "",
    ]

    if overview_section:
        mdx_parts.append(overview_section)

    mdx_parts.append(body)

    if activities_section:
        mdx_parts.append(activities_section)

    if playlist_credit:
        mdx_parts.append(playlist_credit)

    return "\n".join(mdx_parts) + "\n"


# ──────────────────────────────────────────────
# Manifest & File Discovery
# ──────────────────────────────────────────────


def load_manifest(level: str) -> list[str]:
    """Load module ordering from manifest.yaml."""
    manifest_path = CURRICULUM_ROOT / "manifest.yaml"
    if not manifest_path.exists():
        # Fallback: discover YAML files in level directory
        level_dir = CURRICULUM_ROOT / level
        if not level_dir.exists():
            return []
        return sorted(
            [p.stem for p in level_dir.glob("*.yaml") if p.stem != "manifest"],
        )

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    if not manifest:
        return []

    # manifest.yaml structure: levels -> a1 -> sequence -> [slug1, slug2, ...]
    levels = manifest.get("levels", {})
    level_data = levels.get(level, {})
    return level_data.get("sequence", level_data.get("modules", []))


def process_module(yaml_path: Path, order: int = 1) -> Path | None:
    """Process a single module YAML → MDX. Returns output path or None on error."""
    try:
        data = load_module(yaml_path)
    except (ValueError, yaml.YAMLError) as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None

    level = data.get("level", "a1")
    slug = data["module"]

    mdx_content = generate_mdx(data, order=order)

    out_dir = OUTPUT_ROOT / level
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.mdx"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(mdx_content)

    return out_path


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate MDX pages from l2-uk-direct YAML modules"
    )
    parser.add_argument(
        "--module",
        type=Path,
        help="Path to a single module YAML file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all modules for a level",
    )
    parser.add_argument(
        "--level",
        default="a1",
        help="Level to process (default: a1)",
    )

    args = parser.parse_args()

    if args.module:
        print(f"Processing: {args.module}")
        out = process_module(args.module)
        if out:
            print(f"  → {out}")
        else:
            sys.exit(1)

    elif args.all:
        level = args.level
        manifest = load_manifest(level)

        if not manifest:
            # Discover files directly
            level_dir = CURRICULUM_ROOT / level
            if not level_dir.exists():
                print(f"ERROR: Level directory not found: {level_dir}", file=sys.stderr)
                sys.exit(1)
            yaml_files = sorted(level_dir.glob("*.yaml"))
            if not yaml_files:
                print(f"No YAML modules found in {level_dir}", file=sys.stderr)
                sys.exit(1)

            print(f"Processing {len(yaml_files)} modules from {level_dir} (no manifest)")
            for i, yf in enumerate(yaml_files, 1):
                print(f"  [{i}] {yf.name}")
                out = process_module(yf, order=i)
                if out:
                    print(f"      → {out}")
        else:
            print(f"Processing {len(manifest)} modules from manifest ({level})")
            for i, slug in enumerate(manifest, 1):
                yaml_path = CURRICULUM_ROOT / level / f"{slug}.yaml"
                if not yaml_path.exists():
                    print(f"  [{i}] {slug} — MISSING ({yaml_path})", file=sys.stderr)
                    continue
                print(f"  [{i}] {slug}")
                out = process_module(yaml_path, order=i)
                if out:
                    print(f"      → {out}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
