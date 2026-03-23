"""V6 Step 7b: ENRICH — tabs, словник, videos, dialogue formatting, resources.

Deterministic enrichment step. Reads plan YAML and injects structural
elements into generated content that the LLM writer doesn't produce:

1. Tab structure (Урок / Словник / Зошит / Ресурси)
2. Словник (vocabulary table) from plan vocabulary_hints
3. YouTube video embeds from plan pronunciation_videos
4. External resources section from plan references
5. Dialogue block formatting (:::dialogue wrappers)

Runs after ANNOTATE, before VERIFY.

Issue: #1009, #1012
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import yaml
from build.text_utils import parse_vocab_hint

# VESUM database for POS lookup
_VESUM_DB = Path(__file__).resolve().parent.parent.parent / "data" / "vesum.db"

# Ukrainian POS labels
_POS_LABELS = {
    "noun": "ім.",
    "verb": "дієсл.",
    "adj": "прикм.",
    "adv": "присл.",
    "numr": "числ.",
    "prep": "прийм.",
    "conj": "спол.",
    "part": "част.",
    "intj": "виг.",
    "pron": "займ.",
}

# Gender from VESUM tags
_GENDER_MAP = {":m:": "ч.", ":f:": "ж.", ":n:": "с."}


def _vesum_lookup(word: str) -> tuple[str, str]:
    """Look up a word in VESUM for POS and gender.

    Returns (pos_label, gender_label) — empty strings if not found.
    """
    if not _VESUM_DB.exists():
        return "", ""
    try:
        db = sqlite3.connect(str(_VESUM_DB))
        row = db.execute(
            "SELECT pos, tags FROM forms WHERE lemma = ? LIMIT 1",
            (word.lower(),),
        ).fetchone()
        if not row:
            # Try as word_form (not lemma)
            row = db.execute(
                "SELECT pos, tags FROM forms WHERE word_form = ? LIMIT 1",
                (word.lower(),),
            ).fetchone()
        db.close()
        if not row:
            return "", ""
        pos = _POS_LABELS.get(row[0], "")
        gender = ""
        if row[0] == "noun":
            for tag, label in _GENDER_MAP.items():
                if tag in row[1]:
                    gender = label
                    break
        return pos, gender
    except Exception:
        return "", ""

def _find_translation_nearby(word: str, content: str) -> str:
    """Search content for a translation of a Ukrainian word using broader patterns.

    Looks for patterns like:
    - word ... means "translation"
    - word ... is "translation"
    - word (translation)
    - word, which means "translation"
    - known cognates (кафе→cafe, метро→metro)
    """
    # Common cognates/proper nouns that are self-explanatory
    # Common words + cognates/proper nouns
    # This is a fallback — ideally the writer provides translations inline
    cognates = {
        # Cognates
        "кафе": "cafe", "метро": "metro", "банк": "bank", "аптека": "pharmacy",
        "автобус": "bus", "телефон": "phone", "університет": "university",
        # Cities
        "Київ": "Kyiv", "Львів": "Lviv", "Одеса": "Odesa",
        "Харків": "Kharkiv", "Дніпро": "Dnipro", "Полтава": "Poltava",
        # Common A1 words that writers often skip translating
        "день": "day", "ніч": "night", "сон": "dream", "дім": "home",
        "хліб": "bread", "сіль": "salt", "кінь": "horse", "дуб": "oak",
        "хата": "house", "мак": "poppy", "ніс": "nose", "око": "eye",
        "вухо": "ear", "рот": "mouth", "ліс": "forest", "кіт": "cat",
        "пес": "dog", "вовк": "wolf", "лис": "fox",
        "з'їв": "ate", "їжа": "food", "молоко": "milk",
        "наголос": "stress (accent)", "склад": "syllable",
        "літера": "letter", "звук": "sound",
        "голосний": "vowel", "приголосний": "consonant",
        "камінь": "stone", "камін": "fireplace", "ґудзик": "button",
        "маленький": "small", "великий": "big", "гарний": "beautiful",
        "тверді": "hard", "м'які": "soft",
        "м'який знак": "soft sign", "апостроф": "apostrophe",
    }
    if word in cognates:
        return cognates[word]

    # Search for "word" near English text in content (within 100 chars)
    escaped = re.escape(word)
    # Pattern: word ... (English in parentheses)
    match = re.search(
        rf"(?:\*\*)?{escaped}(?:\*\*)?\s*\(([a-zA-Z][^)]+)\)",
        content,
    )
    if match:
        return match.group(1).strip()

    # Pattern: word ... means/is "English"
    match = re.search(
        rf"(?:\*\*)?{escaped}(?:\*\*)?\s+(?:means?|is)\s+[\"\"']?([a-zA-Z][^\"\"'\n.]+)",
        content,
    )
    if match:
        return match.group(1).strip().rstrip(".,;:")

    return ""


# Tab markers — PUBLISH step converts these to <Tabs>/<TabItem>
TAB_MARKER = "<!-- TAB:{name} -->"


def _vocab_table_rows(items: list) -> list[str]:
    """Generate markdown table rows from vocabulary hint items with VESUM data."""
    rows = []
    for item in items:
        word, translation = parse_vocab_hint(item)
        pos, gender = _vesum_lookup(word)
        rows.append(f"| **{word}** | {translation} | {pos} | {gender} |")
    return rows


def _extract_prose_vocab(content: str) -> list[tuple[str, str]]:
    """Extract bold Ukrainian words/phrases WITH translations from prose.

    Scans for patterns like:
    - **word** (translation)
    - **word** — "translation"
    - **word** — translation.
    - **expression?** — "translation"

    Returns list of (word, translation) tuples. Translation may be empty.
    Filters out fragments, single letters, and non-word artifacts.
    """
    # Pattern: **Ukrainian text** followed by optional translation
    # Captures: group(1)=Ukrainian word/phrase, group(2)=translation (if present)
    patterns = [
        # **word** (translation) — most common
        re.compile(r"\*\*([а-яА-ЯіІїЇєЄґҐ'ʼ ?!.,]+)\*\*\s*\(([^)]+)\)"),
        # **word** — "translation" or **word** — translation
        re.compile(r'\*\*([а-яА-ЯіІїЇєЄґҐ\'ʼ ?!.,]+)\*\*\s*[—–-]\s*["\"]?([^""\n.!?]+)["\"]?'),
        # **word** means "translation"
        re.compile(r'\*\*([а-яА-ЯіІїЇєЄґҐ\'ʼ ?!.,]+)\*\*\s+means?\s+["\"]?([^""\n.!?]+)["\"]?'),
        # **word** alone (no translation) — lowest priority
        re.compile(r"\*\*([а-яА-ЯіІїЇєЄґҐ'ʼ ?!.,]+)\*\*"),
    ]

    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    # Try patterns in priority order — first match wins for each word
    for pattern in patterns:
        for match in pattern.finditer(content):
            word = match.group(1).strip().rstrip(".,!?")
            # Skip fragments: must be 3+ chars and contain at least one vowel
            if len(word) < 3:
                continue
            if not re.search(r"[аоуеиіяюєї]", word.lower()):
                continue
            # Skip overly long phrases (>50 chars = sentence, not expression)
            if len(word) > 50:
                continue
            if word.lower() in seen:
                continue
            seen.add(word.lower())

            # Extract translation if captured
            translation = ""
            if match.lastindex and match.lastindex >= 2:
                raw_trans = match.group(2).strip().strip('"').strip()
                # Validate: must be a real translation, not context/description
                is_english = bool(re.search(r"[a-zA-Z]", raw_trans))
                word_count = len(raw_trans.split())
                # Real translations are 1-5 words ("family", "I have", "how are you")
                is_translation_length = 1 <= word_count <= 5
                # Reject grammar/style descriptors
                is_descriptor = bool(re.search(
                    r"\b(masculine|feminine|neuter|informal|formal|plural|"
                    r"singular|literally|more|general|everyday|literary|"
                    r"archaic|colloquial)\b",
                    raw_trans.lower(),
                ))
                if is_english and is_translation_length and not is_descriptor:
                    translation = raw_trans

            results.append((word, translation))

    return results


def _get_previous_vocab(level: str, current_seq: int) -> set[str]:
    """Collect all vocabulary from previous modules' plans to avoid repetition."""
    plans_dir = Path(__file__).resolve().parent.parent.parent / "curriculum" / "l2-uk-en" / "plans" / level
    if not plans_dir.is_dir():
        return set()

    previous_words: set[str] = set()
    for plan_file in plans_dir.glob("*.yaml"):
        try:
            plan_data = yaml.safe_load(plan_file.read_text("utf-8"))
            if not isinstance(plan_data, dict):
                continue
            seq = plan_data.get("sequence", 999)
            if seq >= current_seq:
                continue
            vocab = plan_data.get("vocabulary_hints", {})
            for category in ("required", "recommended"):
                for item in vocab.get(category, []):
                    word, _ = parse_vocab_hint(item)
                    previous_words.add(word.lower())
        except Exception:
            continue

    return previous_words


def _build_slovnyk(plan: dict, content: str = "") -> str:
    """Generate словник (vocabulary table) from plan vocabulary_hints + prose extraction.

    Deduplicates against vocabulary from previous modules to only show NEW words.
    """
    vocab = plan.get("vocabulary_hints", {})
    required = vocab.get("required", [])
    recommended = vocab.get("recommended", [])

    # Get words already taught in previous modules
    level = plan.get("level", "").lower()
    current_seq = plan.get("sequence", 1)
    previous_vocab = _get_previous_vocab(level, current_seq) if level else set()

    # Extract words+translations from prose
    prose_entries = _extract_prose_vocab(content) if content else []

    # Build set of known words (lowercase) for deduplication
    known_words: set[str] = set()
    for item in required + recommended:
        word, _ = parse_vocab_hint(item)
        known_words.add(word.lower())

    # Words from prose not in plan AND not in previous modules
    additional: list[tuple[str, str]] = [
        (word, trans) for word, trans in prose_entries
        if word.lower() not in known_words and word.lower() not in previous_vocab
    ]

    if not required and not recommended and not additional:
        return ""

    lines = []

    if required:
        lines.extend([
            "",
            "### Обов'язкові слова — Required words",
            "",
            "| Слово | Переклад | Частина мови | Рід |",
            "|-------|----------|-------------|-----|",
            *_vocab_table_rows(required),
        ])

    if recommended:
        lines.extend([
            "",
            "### Рекомендовані слова — Recommended words",
            "",
            "| Слово | Переклад | Частина мови | Рід |",
            "|-------|----------|-------------|-----|",
            *_vocab_table_rows(recommended),
        ])

    if additional:
        # Split into single words and expressions (multi-word phrases)
        # Only include REAL expressions — not example sentences like "Це мама"
        single_words = [(w, t) for w, t in additional if " " not in w]
        expressions = [
            (w, t) for w, t in additional
            if " " in w
            and not w.startswith("Це ")  # Skip "Це X" example sentences
            and len(w.split()) <= 5  # Max 5 words — longer is a sentence
        ]

        if single_words:
            lines.extend([
                "",
                "### Додаткові слова з уроку — Additional words from the lesson",
                "",
                "| Слово | Переклад | Частина мови | Рід |",
                "|-------|----------|-------------|-----|",
            ])
            for word, trans in single_words:
                # If no translation found, try harder — search content for nearby English
                if not trans:
                    trans = _find_translation_nearby(word, content)
                pos, gender = _vesum_lookup(word)
                lines.append(f"| **{word}** | {trans} | {pos} | {gender} |")

        if expressions:
            lines.extend([
                "",
                "### Вирази — Expressions",
                "",
                "| Вираз | Переклад |",
                "|-------|----------|",
            ])
            for expr, trans in expressions:
                lines.append(f"| **{expr}** | {trans} |")

    lines.append("")
    return "\n".join(lines)


def _load_external_resources(slug: str, plan: dict) -> list[dict]:
    """Load curated external resources from external_resources.yaml.

    Tries exact slug match first, then topic-based fuzzy match using
    plan title and focus keywords.
    """
    er_path = Path(__file__).resolve().parent.parent.parent / "docs" / "resources" / "external_resources.yaml"
    if not er_path.exists():
        return []

    try:
        er_data = yaml.safe_load(er_path.read_text("utf-8"))
        resources = er_data.get("resources", {})
    except Exception:
        return []

    # 1. Try exact slug match
    if slug in resources:
        return _flatten_resources(resources[slug])

    # 2. Try with level prefix
    level = plan.get("level", "").lower()
    prefixed = f"{level}-{slug}"
    if prefixed in resources:
        return _flatten_resources(resources[prefixed])

    # No fuzzy matching — only exact slug matches.
    # external_resources.yaml uses old V2 slugs that don't map to V3.
    # TODO: remap external_resources.yaml to V3 slugs (#1022)

    return []


def _flatten_resources(resource_data: dict) -> list[dict]:
    """Flatten a resource entry (articles, youtube, podcasts) into a flat list."""
    items = []
    for category in ("articles", "youtube", "podcasts"):
        for item in resource_data.get(category, []):
            items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": item.get("source", item.get("channel", "")),
                "type": category,
            })
    return items


def _build_video_embeds(plan: dict) -> str:
    """Generate YouTube video embed section from plan pronunciation_videos."""
    pv = plan.get("pronunciation_videos", {})
    if not pv:
        return ""

    lines = []

    overview = pv.get("overview", "")
    if overview:
        label = pv.get("credit", "Ukrainian Lessons")
        lines.append(f'<YouTubeVideo client:only="react" url="{overview}" label="Overview — {label}" />')
        lines.append("")

    playlist = pv.get("playlist", "")
    if playlist:
        lines.append(f"[Повний плейлист / Full playlist]({playlist})")
        lines.append("")

    # Per-letter videos
    for key in ("vowels", "consonants", "special", "letters"):
        letter_dict = pv.get(key, {})
        if letter_dict:
            credit = pv.get("credit", "Ukrainian Lessons")
            for letter, url in letter_dict.items():
                lines.append(
                    f'<YouTubeVideo client:only="react" url="{url}" '
                    f'label="Літера {letter} — {credit}" />'
                )
                lines.append("")

    return "\n".join(lines)


def _build_resources(plan: dict, slug: str = "") -> str:
    """Generate external resources section from plan references + external_resources.yaml."""
    refs = plan.get("references", [])
    ext_resources = _load_external_resources(slug, plan) if slug else []

    if not refs and not ext_resources:
        return ""

    lines = []

    # Plan references (textbook citations, ULP episodes)
    if refs:
        lines.append("**Джерела — References**")
        lines.append("")
        for ref in refs:
            title = ref.get("title", "")
            url = ref.get("url", "")
            notes = ref.get("notes", "")
            if url:
                lines.append(f"- [{title}]({url})")
            else:
                lines.append(f"- {title}")
            if notes:
                lines.append(f"  _{notes}_")
        lines.append("")

    # External curated resources (ULP blog, Dobra Forma, Talk Ukrainian, etc.)
    if ext_resources:
        # Group by type
        articles = [r for r in ext_resources if r["type"] == "articles"]
        videos = [r for r in ext_resources if r["type"] == "youtube"]
        podcasts = [r for r in ext_resources if r["type"] == "podcasts"]

        if articles:
            lines.append("**Статті — Articles**")
            lines.append("")
            for r in articles:
                source = f" ({r['source']})" if r["source"] else ""
                lines.append(f"- [{r['title']}]({r['url']}){source}")
            lines.append("")

        if videos:
            lines.append("**Відео — Videos**")
            lines.append("")
            for r in videos:
                source = f" ({r['source']})" if r["source"] else ""
                lines.append(f"- [{r['title']}]({r['url']}){source}")
            lines.append("")

        if podcasts:
            lines.append("**Подкасти — Podcasts**")
            lines.append("")
            for r in podcasts:
                source = f" ({r['source']})" if r["source"] else ""
                lines.append(f"- [{r['title']}]({r['url']}){source}")
            lines.append("")

    lines.append("")
    return "\n".join(lines)


def _format_dialogues(content: str) -> str:
    """Wrap dialogue blocks in :::dialogue containers.

    Detects patterns like:
    — Привіт! Як справи?
    — Добре, дякую! А у тебе?

    And wraps them in :::dialogue ... ::: blocks.
    """
    dialogue_pattern = re.compile(
        r"((?:^— .+\n){2,})",
        re.MULTILINE,
    )

    def _wrap(match: re.Match) -> str:
        block = match.group(1).rstrip("\n")
        return f":::dialogue\n{block}\n:::\n"

    return dialogue_pattern.sub(_wrap, content)


def enrich(content: str, plan: dict, slug: str = "") -> tuple[str, list[str]]:
    """Enrich content with tab structure, vocabulary, videos, resources, dialogues.

    Organizes content into 4 tabs:
    - Урок (Lesson): prose + inline exercises + videos from plan
    - Словник (Vocabulary): word tables from vocabulary_hints
    - Зошит (Workbook): "Coming soon" placeholder
    - Ресурси (Resources): external links, textbook references

    Tab boundaries are marked with <!-- TAB:name --> comments.
    The PUBLISH step converts these to <Tabs>/<TabItem> components.

    Args:
        content: Module markdown content (after annotation).
        plan: Parsed plan YAML dict.

    Returns:
        Tuple of (enriched content, list of enrichment actions taken).
    """
    actions: list[str] = []

    # 1. Format dialogues in existing content
    new_content = _format_dialogues(content)
    if new_content != content:
        actions.append("dialogue-formatting")
        content = new_content

    # 2. Strip existing enrichment (idempotent — safe to re-run)
    # Remove existing tab markers and everything after the first non-Урок tab
    if "<!-- TAB:Словник -->" in content:
        # Content was already enriched — strip everything from Словник tab onward
        slovnyk_pos = content.index("<!-- TAB:Словник -->")
        content = content[:slovnyk_pos].strip()
    if "<!-- TAB:Урок -->" in content:
        # Strip the Урок tab marker itself (we'll re-add it)
        content = content.replace("<!-- TAB:Урок -->", "").strip()

    # Also remove old V5-era section headings
    content = re.sub(
        r"\n## (?:Video Resources|Відео — Video|Словник — Vocabulary|Resources|Ресурси — Resources)\n.*?(?=\n## |\Z)",
        "",
        content,
        flags=re.DOTALL,
    )
    # Remove inline video sections from previous enrichment
    content = re.sub(
        r"\n### Відео — Video\n.*?(?=\n## |\n<!-- TAB:|\Z)",
        "",
        content,
        flags=re.DOTALL,
    )
    # Remove any writer-generated vocabulary tables (the ENRICH step generates proper ones)
    content = re.sub(
        r"\n### (?:Додаткові слова|Additional words|Вирази|Словник|Vocabulary).*?(?=\n## |\n<!-- TAB:|\Z)",
        "",
        content,
        flags=re.DOTALL,
    )

    # 3. Build tab content
    slovnyk = _build_slovnyk(plan, content)
    videos = _build_video_embeds(plan)
    resources = _build_resources(plan, slug=slug)

    # 4. Insert inline videos into the prose (Урок tab)
    # Videos go right before Summary if it exists, otherwise at end of prose
    if videos:
        summary_match = re.search(r"^(## (?:Підсумок|Summary))", content, re.MULTILINE)
        video_section = f"\n### Відео — Video\n\n{videos}\n"
        if summary_match:
            content = content[:summary_match.start()] + video_section + "\n" + content[summary_match.start():]
        else:
            content = content.rstrip() + "\n" + video_section
        actions.append("video-embeds")

    # 5. Assemble with tab markers
    parts = []

    # Tab 1: Урок (the prose content with inline exercises and videos)
    parts.append("<!-- TAB:Урок -->")
    parts.append(content.strip())

    # Tab 2: Словник
    if slovnyk:
        parts.append("\n<!-- TAB:Словник -->")
        parts.append(slovnyk.strip())
        actions.append("slovnyk-table")

    # Tab 3: Зошит (Coming soon)
    parts.append("\n<!-- TAB:Зошит -->")
    parts.append(
        ":::note\n"
        "Розширені вправи для цього уроку ще в розробці.\n\n"
        "Advanced exercises for this module are in development. "
        "Check back soon!\n"
        ":::"
    )
    actions.append("workbook-placeholder")

    # Tab 4: Ресурси
    if resources:
        parts.append("\n<!-- TAB:Ресурси -->")
        parts.append(resources.strip())
        actions.append("external-resources")

    enriched = "\n\n".join(parts)
    actions.append("tab-structure")

    return enriched, actions


def enrich_file(content_path: Path, plan_path: Path) -> list[str]:
    """Enrich a content file using its plan. Returns list of actions taken."""
    content = content_path.read_text("utf-8")
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    slug = plan.get("slug", plan_path.stem)

    enriched, actions = enrich(content, plan, slug=slug)

    if actions:
        content_path.write_text(enriched, "utf-8")

    return actions


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: .venv/bin/python scripts/build/enrich.py <content.md> <plan.yaml>")
        sys.exit(1)

    content_p = Path(sys.argv[1])
    plan_p = Path(sys.argv[2])
    result = enrich_file(content_p, plan_p)

    if result:
        print(f"✅ Enriched: {', '.join(result)}")
    else:
        print("ℹ️  No enrichments needed")
