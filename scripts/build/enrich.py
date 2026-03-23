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

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CURRICULUM_ROOT = _PROJECT_ROOT / "curriculum" / "l2-uk-en"

# VESUM database for POS lookup
_VESUM_DB = _PROJECT_ROOT / "data" / "vesum.db"

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

_translation_cache: dict[str, str] = {}


def _find_translation(word: str) -> str:
    """Find English translation for a Ukrainian word.

    Uses the translation tool chain: Wiktionary → Горох → e2u.
    Results are cached to avoid repeated HTTP calls.
    Failures return empty string (never crashes).
    """
    if word in _translation_cache:
        return _translation_cache[word]

    # Proper nouns
    _proper_nouns = {
        "Київ": "Kyiv", "Львів": "Lviv", "Одеса": "Odesa",
        "Харків": "Kharkiv", "Дніпро": "Dnipro", "Полтава": "Poltava",
    }
    if word in _proper_nouns:
        _translation_cache[word] = _proper_nouns[word]
        return _proper_nouns[word]

    # Use the unified translation chain (Wiktionary → Горох → e2u)
    try:
        from rag.source_query import translate_uk_to_en
        result = translate_uk_to_en(word)
        _translation_cache[word] = result
        return result
    except Exception:
        _translation_cache[word] = ""
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


def _extract_prose_vocab(content: str) -> list[str]:
    """Extract bold Ukrainian words from prose.

    Only extracts the Ukrainian words — NO translation extraction from prose.
    Translations come from plan vocabulary or fallback dictionary (deterministic).

    Returns deduplicated list of Ukrainian words found in **bold** markup.
    """
    bold_pattern = re.compile(r"\*\*([а-яА-ЯіІїЇєЄґҐ'ʼ ?!.,]+)\*\*")
    words: list[str] = []
    seen: set[str] = set()

    for match in bold_pattern.finditer(content):
        word = match.group(1).strip().rstrip(".,!?")
        if len(word) < 3:
            continue
        if not re.search(r"[аоуеиіяюєї]", word.lower()):
            continue
        if len(word) > 40:
            continue
        if word.lower() not in seen:
            seen.add(word.lower())
            words.append(word)

    return words


def _get_previous_vocab(level: str, current_seq: int) -> set[str]:
    """Collect all vocabulary from previous modules' plans to avoid repetition."""
    plans_dir = _CURRICULUM_ROOT / "plans" / level
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


def _build_slovnyk(plan: dict, content: str = "", slug: str = "") -> str:
    """Generate словник (vocabulary table) from writer-generated vocabulary YAML.

    Priority:
    1. vocabulary/{slug}.yaml (writer-driven, from step_vocab) — has contextual translations
    2. Fallback: plan vocabulary_hints (no prose translations)

    Issue: #1025
    """
    # 1. Try writer-generated vocabulary YAML
    level = plan.get("level", "").lower()
    if slug and level:
        vocab_path = _CURRICULUM_ROOT / level / "vocabulary" / f"{slug}.yaml"
        if vocab_path.exists():
            try:
                vocab_data = yaml.safe_load(vocab_path.read_text("utf-8"))
                if isinstance(vocab_data, dict) and vocab_data.get("vocabulary"):
                    from build.vocab_gen import build_slovnyk_markdown
                    entries = vocab_data["vocabulary"]
                    # Split into plan vocab, additional, and expressions
                    expressions = [e for e in entries if e.get("expression")]
                    additional = [e for e in entries if e.get("additional") and not e.get("expression")]
                    plan_entries = [e for e in entries if not e.get("expression") and not e.get("additional")]
                    return build_slovnyk_markdown(plan_entries, additional, expressions)
            except Exception:
                pass  # Fall through to plan-based fallback

    # 2. Fallback: plan vocabulary_hints (no contextual translations from prose)
    vocab = plan.get("vocabulary_hints", {})
    required = vocab.get("required", [])
    recommended = vocab.get("recommended", [])

    if not required and not recommended:
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

    lines.append("")
    return "\n".join(lines)


def _load_external_resources(slug: str, plan: dict) -> list[dict]:
    """Load curated external resources from external_resources.yaml.

    Tries exact slug match first, then topic-based fuzzy match using
    plan title and focus keywords.
    """
    er_path = _PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
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
    """Convert blockquote dialogues to visually separated dialogue blocks.

    Detects blockquote dialogue patterns like:
        > — **Привіт!** (Hi!)
        > — **Добре!** (Good!)

    And converts them to a styled dialogue div with each turn separated:
        <div class="dialogue">
        <p>— **Привіт!** (Hi!)</p>
        <p>— **Добре!** (Good!)</p>
        </div>

    Also handles non-blockquote dialogues (— at line start).
    """
    # Match a block of consecutive blockquote lines containing dialogue
    blockquote_dialogue = re.compile(
        r"((?:^> .+\n)+)",
        re.MULTILINE,
    )

    def _convert_blockquote(match: re.Match) -> str:
        block = match.group(1)
        lines = block.strip().split("\n")
        # Check if this block has dialogue markers (—)
        has_dialogue = any(re.match(r"^>\s*—\s", line) for line in lines)
        if not has_dialogue:
            return match.group(0)  # Not a dialogue, leave as blockquote

        parts = ['<div class="dialogue">\n']
        for line in lines:
            text = re.sub(r"^>\s*", "", line).strip()
            if text:
                parts.append(f"\n{text}\n")
        parts.append("\n</div>\n")
        return "\n".join(parts)

    result = blockquote_dialogue.sub(_convert_blockquote, content)

    # Also handle non-blockquote dialogues (— at line start)
    plain_dialogue = re.compile(
        r"((?:^— .+\n){2,})",
        re.MULTILINE,
    )

    def _convert_plain(match: re.Match) -> str:
        block = match.group(1)
        lines = block.strip().split("\n")
        parts = ['<div class="dialogue">\n']
        for line in lines:
            text = line.strip()
            if text:
                parts.append(f"\n{text}\n")
        parts.append("\n</div>\n")
        return "\n".join(parts)

    result = plain_dialogue.sub(_convert_plain, result)

    return result


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

    # 1. Revert any previously converted dialogues back to blockquote format,
    # then re-format. This ensures idempotent dialogue processing.
    if '<div class="dialogue">' in content:
        # Strip dialogue divs, restore blockquote lines
        def _restore_blockquote(m: re.Match) -> str:
            inner = m.group(1).strip()
            lines = [line.strip() for line in inner.split("\n") if line.strip()]
            return "\n".join(f"> {line}" for line in lines) + "\n"
        content = re.sub(
            r'<div class="dialogue">\s*\n(.*?)\n</div>',
            _restore_blockquote,
            content,
            flags=re.DOTALL,
        )

    # Format dialogues in content
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
    slovnyk = _build_slovnyk(plan, content, slug=slug)
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
    """Enrich a content file using its plan. Returns list of actions taken.

    Atomic write: enriches in memory, only writes if successful.
    If enrichment fails, the original file is preserved.
    """
    content = content_path.read_text("utf-8")
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    slug = plan.get("slug", plan_path.stem)

    try:
        enriched, actions = enrich(content, plan, slug=slug)
    except Exception as e:
        import logging
        logging.warning(f"Enrichment failed for {slug}: {e}")
        return []

    # Only write if enrichment produced content (not empty/truncated)
    if actions and len(enriched) >= len(content) * 0.5:
        content_path.write_text(enriched, "utf-8")
    elif actions:
        import logging
        logging.warning(f"Enrichment for {slug} produced suspiciously short output "
                       f"({len(enriched)} vs {len(content)}). Skipping write.")
        return []

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
