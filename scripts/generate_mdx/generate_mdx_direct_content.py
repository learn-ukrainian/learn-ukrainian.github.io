"""Content section renderers for l2-uk-direct MDX generation.

Renders module-type-specific content sections (script_foundation, communicative,
vocabulary, grammar, checkpoint) into MDX markup. Used by generate_mdx_direct.
"""

from __future__ import annotations

from generate_mdx_direct_renderers import dump_json_for_jsx, escape_jsx_string

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


def _render_letter_grid(letter_list: list[dict], include_note: bool = False) -> str:
    """Build a LetterGrid JSX component from a list of letter dicts."""
    grid_data = [
        {
            "upper": l["upper"],
            "lower": l["lower"],
            "emoji": l.get("emoji", ""),
            "key_word": l.get("key_word", ""),
            **({"note": l.get("note", "")} if include_note else {}),
            "sound_type": l.get("sound_type", "consonant"),
        }
        for l in letter_list
    ]
    return f"<LetterGrid client:only=\"react\" letters={{JSON.parse(`{dump_json_for_jsx(grid_data)}`)}} />\n"


def _render_abetka_sessions(letters: list[dict]) -> list[str]:
    """Render letter groups for abetka module."""
    lines: list[str] = []
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
        lines.append(_render_letter_grid(session_letters, include_note=True))

        war_items = [
            {"letter": l["upper"], "video": l.get("pronunciation_video", "")}
            for l in session_letters
            if l.get("pronunciation_video")
        ]
        if war_items:
            lines.append(
                f'<WatchAndRepeat client:only=\"react\" items={{JSON.parse(`{dump_json_for_jsx(war_items)}`)}} '
                f'title="Повтори: {session["title"]}" isUkrainian />\n'
            )

    remaining = [l for l in letters if l["upper"] not in assigned]
    if remaining:
        lines.append("\n## Інші букви\n")
        lines.append(_render_letter_grid(remaining))

    return lines


def _render_abetka_apostrophe(data: dict) -> list[str]:
    """Render abetka-style apostrophe section."""
    lines: list[str] = []
    apostrophe = data.get("apostrophe")
    if apostrophe:
        lines.append("\n## Апостроф\n")
        lines.append(f"**{apostrophe['symbol']}** \u2014 {apostrophe.get('note', '')}\n")
        if apostrophe.get("example_word"):
            lines.append(f"\n{apostrophe.get('emoji', '')} *{apostrophe['example_word']}*\n")
    return lines


def _render_digraphs(data: dict) -> list[str]:
    """Render digraphs section."""
    lines: list[str] = []
    digraphs = data.get("digraphs")
    if digraphs:
        lines.append("\n## Буквосполучення\n")
        lines.append("*Дві букви \u2014 один звук*\n")
        for dg in digraphs:
            letters_str = dg.get("letters", "")
            note = dg.get("note", "")
            kw = dg.get("key_word", "")
            emoji = dg.get("emoji", "")
            lines.append(f"**{letters_str}** \u2014 {note}")
            if kw:
                lines.append(f"  {emoji} *{kw}*\n")
    return lines


def _render_abetka_stress(data: dict) -> list[str]:
    """Render abetka-style stress section."""
    lines: list[str] = []
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
    return lines


def _render_syllable_rule(data: dict) -> list[str]:
    """Render syllable rule section for generic script_foundation."""
    lines: list[str] = []
    syllable_rule = data.get("syllable_rule")
    if syllable_rule:
        lines.append("\n## Що таке склад?\n")
        lines.append(f"{syllable_rule.get('text', '')}\n")
        vowels = syllable_rule.get("vowels", [])
        if vowels:
            lines.append(f"\nГолосні: **{' '.join(vowels)}** ({len(vowels)} букв)\n")
        examples = syllable_rule.get("examples", [])
        if examples:
            lines.append("")
            for ex in examples:
                count = ex["syllables"]
                suffix = (
                    "склад" if count == 1
                    else "склади" if count < 5 else "складів"
                )
                lines.append(
                    f"- {ex.get('emoji', '')} **{ex['word']}** \u2192 "
                    f"{ex['split']} ({count} {suffix})"
                )
            lines.append("")
    return lines


def _render_syllable_table(table: dict) -> list[str]:
    """Render a single syllable table (CV or VC grid)."""
    lines: list[str] = []
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

    return lines


def _render_soft_consonants(data: dict) -> list[str]:
    """Render soft consonants section."""
    lines: list[str] = []
    soft = data.get("soft_consonants")
    if soft:
        lines.append("\n## М'які приголосні\n")
        lines.append(f"{soft.get('rule', '')}\n")
        soft_examples = soft.get("examples", [])
        if soft_examples:
            lines.append("")
            for ex in soft_examples:
                lines.append(
                    f"- {ex.get('hard', '')} \u2192 **{ex.get('soft', '')}** "
                    f"\u2014 {ex.get('note', '')}"
                )
            lines.append("")
        soft_words = soft.get("words", [])
        if soft_words:
            lines.append("")
            for w in soft_words:
                lines.append(
                    f"- {w.get('emoji', '')} **{w['word']}** "
                    f"\u2014 {w.get('note', '')}"
                )
            lines.append("")
    return lines


def _render_generic_apostrophe(data: dict) -> list[str]:
    """Render generic (non-abetka) apostrophe section."""
    lines: list[str] = []
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
    return lines


def _render_generic_stress(data: dict) -> list[str]:
    """Render generic (non-abetka) stress section."""
    lines: list[str] = []
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
                    f"\u2014 {pair.get('meaning1', '')}"
                )
                lines.append(
                    f"- {pair.get('emoji2', '')} **{pair['word2']}** "
                    f"\u2014 {pair.get('meaning2', '')}"
                )
                lines.append("")
    return lines


def _render_syllable_vocab(data: dict) -> list[str]:
    """Render vocabulary with syllable info for generic script_foundation."""
    lines: list[str] = []
    vocab = data.get("vocabulary")
    if vocab:
        words = []
        for v in vocab:
            count = v.get("syllables", 0)
            split = v.get("split", "")
            suffix = (
                "склад" if count == 1
                else "склади" if count < 5 else "складів"
            )
            examples = [f"{split} \u2014 {count} {suffix}"] if split else []
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
            f"<VocabCard client:only=\"react\" words={{JSON.parse("
            f"`{dump_json_for_jsx(words)}`)}} "
            f'title="Слова по складах" isUkrainian />\n'
        )
    return lines


def render_script_foundation(data: dict) -> str:
    """Render script_foundation modules (abetka, sklad, naholos)."""
    lines: list[str] = []
    letters = data.get("letters", [])

    if data.get("module") == "abetka" and letters:
        lines.extend(_render_abetka_sessions(letters))
        lines.extend(_render_abetka_apostrophe(data))
        lines.extend(_render_digraphs(data))
        lines.extend(_render_abetka_stress(data))
    else:
        lines.extend(_render_syllable_rule(data))
        for table in data.get("syllable_tables", []):
            lines.extend(_render_syllable_table(table))
        lines.extend(_render_soft_consonants(data))
        lines.extend(_render_generic_apostrophe(data))
        lines.extend(_render_generic_stress(data))
        if letters:
            lines.append(_render_letter_grid(letters))
        lines.extend(_render_syllable_vocab(data))

    return "\n".join(lines)


def render_communicative(data: dict) -> str:
    """Render communicative modules (pryvit, etc.)."""
    lines: list[str] = []

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
            f"<PhraseTable client:only=\"react\" groups={{JSON.parse(`{dump_json_for_jsx(groups)}`)}} isUkrainian />\n"
        )

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
            lines.append(f"<DialogueBox client:only=\"react\" {props} isUkrainian />\n")

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
            f"<VocabCard client:only=\"react\" words={{JSON.parse(`{dump_json_for_jsx(words)}`)}} isUkrainian />\n"
        )

    return "\n".join(lines)


def render_grammar(data: dict) -> str:
    """Render grammar modules."""
    lines: list[str] = []

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

    refs = data.get("references")
    if refs:
        lines.append("\n### Повторення\n")
        for ref in refs:
            lines.append(f"- {ref}")
        lines.append("")

    return "\n".join(lines)
