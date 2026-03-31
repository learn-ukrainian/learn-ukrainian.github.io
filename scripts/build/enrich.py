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

    # 2. Fallback: plan vocabulary_hints → table + FlashcardDeck
    vocab = plan.get("vocabulary_hints", {})
    required = vocab.get("required", [])
    recommended = vocab.get("recommended", [])

    if not required and not recommended:
        return ""

    GENDER_COLORS = {
        "ч.": "#0057B8", "м.": "#0057B8",
        "ж.": "#C2185B", "ф.": "#C2185B",
        "с.": "#E65100", "н.": "#E65100",
    }

    lines = []

    # Dictionary tables
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

    # Flashcards below
    all_items = required + recommended
    cards = []
    for item in all_items:
        word, translation = parse_vocab_hint(item)
        pos, gender = _vesum_lookup(word)
        front = word.replace('"', '\\"')
        back = translation.replace('"', '\\"')
        parts = [f'front: "{front}", back: "{back}"']
        if pos:
            parts.append(f'subtitle: "{pos}"')
        if gender:
            parts.append(f'tag: "{gender}"')
            color = GENDER_COLORS.get(gender, "")
            if color:
                parts.append(f'tagColor: "{color}"')
        cards.append("{ " + ", ".join(parts) + " }")

    cards_js = ", ".join(cards)
    lines.extend([
        "",
        "### Картки — Flashcards",
        "",
        f'<FlashcardDeck client:only="react" cards={{[{cards_js}]}} />',
        "",
    ])

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
    """Generate YouTube video embed section from plan pronunciation_videos.

    Only emits content if there are actual videos (overview or per-letter).
    A bare playlist link alone is not useful — skip it.
    """
    pv = plan.get("pronunciation_videos", {})
    if not pv:
        return ""

    # Skip if no real video content (just a playlist link)
    has_overview = bool(pv.get("overview"))
    has_letters = any(pv.get(k) for k in ("vowels", "consonants", "special", "letters"))
    if not has_overview and not has_letters:
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

    # Per-letter videos — organized by group with subheadings
    _GROUP_LABELS = {
        "vowels": "Голосні — Vowels",
        "consonants": "Приголосні — Consonants",
        "special": "Спеціальні — Special letters",
        "letters": "Літери — Letters",
    }
    for key in ("vowels", "consonants", "special", "letters"):
        letter_dict = pv.get(key, {})
        if not letter_dict:
            continue
        # Filter out null values
        valid_letters = {k: v for k, v in letter_dict.items() if v and v != "null"}
        if not valid_letters:
            continue
        credit = pv.get("credit", "Ukrainian Lessons")
        group_label = _GROUP_LABELS.get(key, key.capitalize())
        lines.append(f"#### {group_label}")
        lines.append("")
        for letter, url in valid_letters.items():
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

    # МійКлас grammar references (#1040) — auto-matched by plan grammar/focus
    miyklas_entries: list[dict] = []
    try:
        from build.miyklas import build_miyklas_resource_entries
        miyklas_entries = build_miyklas_resource_entries(plan)
    except Exception as e:
        print(f"  ⚠️  МійКлас resource entries skipped: {e}")

    if not refs and not ext_resources and not miyklas_entries:
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

    if miyklas_entries:
        lines.append("**Граматика — Grammar (МійКлас)**")
        lines.append("")
        for entry in miyklas_entries:
            lines.append(f"- [{entry['title']}]({entry['url']}) ({entry['source']})")
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

    # ULP resources (Anna Ohoiko — Ukrainian Lessons Podcast)
    ulp_links = _load_resource_file("ulp-resources.yaml", slug, plan)
    if not ulp_links:
        # Fallback: auto-match from tag-based index (#1056)
        ulp_links = _match_resource_index("ulp-articles-index.yaml", plan)
    if ulp_links:
        articles = [l for l in ulp_links if l.get("type") == "article"]
        podcasts = [l for l in ulp_links if l.get("type") == "podcast"]
        if articles:
            lines.append("**Anna Ohoiko — Ukrainian Lessons**")
            lines.append("")
            for link in articles:
                lines.append(f"- [{link['title']}]({link['url']})")
            lines.append("")
        if podcasts:
            lines.append("**Подкасти — Podcasts**")
            lines.append("")
            for link in podcasts:
                lines.append(f"- [{link['title']}]({link['url']})")
            lines.append("")

    # МійКлас resources — handled by build_miyklas_resource_entries() above (PR #1069)
    # Old _match_resource_index("miyklas-url-index.yaml") removed to avoid duplicates.

    lines.append("")
    return "\n".join(lines)


def _load_resource_file(filename: str, slug: str, plan: dict) -> list[dict]:
    """Load resource links for a module from a YAML mapping file.

    Files like miyklas-resources.yaml and ulp-resources.yaml have structure:
      {level}: {slug}: [{title, url, ...}, ...]
    """
    path = _PROJECT_ROOT / "docs" / "resources" / filename
    if not path.exists():
        return []

    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except Exception:
        return []

    level = plan.get("level", "").lower()
    if not level or level not in data:
        return []

    level_data = data[level]
    return level_data.get(slug, [])


def _match_resource_index(filename: str, plan: dict, max_results: int = 3) -> list[dict]:
    """Auto-match resources from a tag-based index YAML (#1040, #1056).

    Reads a YAML file with sections containing tagged lesson entries.
    Matches plan topics against tags using bidirectional substring matching.
    Returns list of {title, url, type} dicts compatible with the enrich format.
    """
    path = _PROJECT_ROOT / "docs" / "resources" / filename
    if not path.exists():
        return []

    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except Exception:
        return []

    if not isinstance(data, dict):
        return []

    base_url = data.get("base_url", "")

    # Build search terms from plan
    search_terms: set[str] = set()
    title = plan.get("title", "").lower()
    search_terms.update(title.split())
    for section in plan.get("content_outline", []):
        search_terms.update(section.get("section", "").lower().split())
    for hint in plan.get("activity_hints", []):
        search_terms.update(hint.get("focus", "").lower().split())

    # Collect all lessons from all sections
    all_lessons: list[dict] = []
    for key, value in data.items():
        if key in ("base_url",):
            continue
        if isinstance(value, list):
            all_lessons.extend(value)
        elif isinstance(value, dict):
            # Nested: grade_5: { lessons: [...], lexicology: [...] }
            for _sub_key, sub_val in value.items():
                if isinstance(sub_val, list):
                    all_lessons.extend(sub_val)

    # Match by tags
    matched: list[dict] = []
    for lesson in all_lessons:
        if not isinstance(lesson, dict) or "path" not in lesson:
            continue
        tags = [t.lower() for t in lesson.get("tags", [])]
        hit = False
        for tag in tags:
            if tag in search_terms:
                hit = True
                break
            for term in search_terms:
                if len(term) > 3 and (term in tag or tag in term):
                    hit = True
                    break
            if hit:
                break
        if hit:
            url = base_url + lesson["path"] if not lesson["path"].startswith("http") else lesson["path"]
            matched.append({
                "title": lesson.get("title", ""),
                "url": url,
                "type": "article",
                "topic": ", ".join(tags[:3]),
            })
            if len(matched) >= max_results:
                break

    return matched


def _format_dialogues(content: str) -> str:
    """Convert blockquote dialogues to visually separated dialogue blocks.

    Detects blockquote dialogue patterns like:
        > — **Привіт!** (Hi!)
        > — **Добре!** (Good!)

    And converts them to POC lesson design HTML:
        <div class="dialogue">
        <div class="dialogue-line"><span class="speaker">Оленка:</span> Привіт!</div>
        <div class="dialogue-line"><span class="speaker">Тарас:</span> Добре!</div>
        </div>

    Also handles non-blockquote dialogues (— at line start).
    """

    def _format_dialogue_line(text: str) -> str:
        """Format a single dialogue line with POC design classes."""
        # Extract speaker name if present: **Name:** text or — **Name:** text
        speaker_match = re.match(r"^—?\s*\*\*([^*]+):\*\*\s*(.*)", text)
        if speaker_match:
            speaker = speaker_match.group(1)
            content = speaker_match.group(2)
            return f'<div class="dialogue-line"><span class="speaker">{speaker}:</span> {content}</div>'
        # Plain em-dash line
        if text.startswith("—"):
            return f'<div class="dialogue-line">{text}</div>'
        return f'<div class="dialogue-line">{text}</div>'

    # Match a block of blockquote lines containing dialogue.
    # Allow blank lines (^>\s*$ or empty line) between turns — writers often
    # separate dialogue lines with blanks for readability.
    blockquote_dialogue = re.compile(
        r"((?:^>[ \t]*.+\n|^>\s*\n|^\s*\n(?=^>))+)",
        re.MULTILINE,
    )

    def _convert_blockquote(match: re.Match) -> str:
        block = match.group(1)
        lines = block.strip().split("\n")
        has_dialogue = any(
            re.match(r"^>\s*(?:—\s|\*\*[^*]+:\*\*)", line) for line in lines
        )
        if not has_dialogue:
            return match.group(0)

        parts = ['<div class="dialogue">\n']
        for line in lines:
            text = re.sub(r"^>\s*", "", line).strip()
            if text:
                parts.append(_format_dialogue_line(text))
                parts.append("\n")
        parts.append("</div>\n")
        return "\n".join(parts)

    result = blockquote_dialogue.sub(_convert_blockquote, content)

    # Also handle non-blockquote dialogues:
    # 1. Plain em-dash format (— at line start)
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
                parts.append(_format_dialogue_line(text))
                parts.append("\n")
        parts.append("</div>\n")
        return "\n".join(parts)

    result = plain_dialogue.sub(_convert_plain, result)

    # 2. Named speaker format (**Name:** text) — 2+ consecutive turns
    named_dialogue = re.compile(
        r"((?:^\*\*[А-ЯІЇЄҐа-яіїєґA-Za-z]+:\*\* .+\n(?:\n|$)){2,})",
        re.MULTILINE,
    )

    def _convert_named(match: re.Match) -> str:
        block = match.group(1)
        lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
        parts = ['<div class="dialogue">\n']
        for line in lines:
            parts.append(_format_dialogue_line(line))
            parts.append("\n")
        parts.append("</div>\n")
        return "\n".join(parts)

    result = named_dialogue.sub(_convert_named, result)

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
    original_content = content  # Preserve for safety check + diagnostics

    # 1. Revert any previously converted dialogue HTML back to blockquote markdown.
    # The .md source should contain clean markdown, not HTML divs.
    # Dialogue → HTML conversion happens in PUBLISH (step_publish), not here.
    if '<div class="dialogue' in content:
        def _restore_blockquote(m: re.Match) -> str:
            inner = m.group(1).strip()
            raw_lines = re.findall(
                r'<div class="dialogue-line">(?:<span class="speaker">([^<]+)</span>\s*)?(.*?)</div>',
                inner,
            )
            restored = []
            for speaker, text in raw_lines:
                if speaker:
                    restored.append(f"> — **{speaker}** {text}")
                elif text.strip():
                    restored.append(f"> {text.strip()}")
            return "\n".join(restored) + "\n" if restored else ""
        content = re.sub(
            r'<div class="dialogue">\s*\n(.*?)\n</div>',
            _restore_blockquote,
            content,
            flags=re.DOTALL,
        )
        # Clean stray > lines left between dialogue blocks
        content = re.sub(r'\n>\s*\n', '\n', content)
        # Also clean dialogue-line divs inside blockquotes (> <div ...>)
        def _clean_blockquoted_divs(m: re.Match) -> str:
            line = m.group(1)
            match = re.search(
                r'<div class="dialogue-line">(?:<span class="speaker">([^<]+)</span>\s*)?(.*?)</div>',
                line,
            )
            if match:
                speaker, text = match.group(1), match.group(2)
                if speaker:
                    return f"> — **{speaker}** {text}"
                return f"> {text.strip()}" if text.strip() else ""
            return m.group(0)
        content = re.sub(r'^> (.+)$', _clean_blockquoted_divs, content, flags=re.MULTILINE)
        actions.append("dialogue-cleanup")

    # 2. Strip existing enrichment (idempotent — safe to re-run)
    # Remove existing tab markers and everything after the first non-Урок tab
    _pre_strip_words = len(content.split())
    if "<!-- TAB:Словник -->" in content:
        # Content was already enriched — strip everything from Словник tab onward
        slovnyk_pos = content.index("<!-- TAB:Словник -->")
        content = content[:slovnyk_pos].strip()
    if "<!-- TAB:Урок -->" in content:
        # Strip the Урок tab marker itself (we'll re-add it)
        content = content.replace("<!-- TAB:Урок -->", "").strip()

    # Also remove old V5-era section headings
    _before = len(content.split())
    content = re.sub(
        r"\n## (?:Video Resources|Відео — Video|Словник — Vocabulary|Resources|Ресурси — Resources)\n.*?(?=\n## |\Z)",
        "",
        content,
        flags=re.DOTALL,
    )
    _after = len(content.split())
    if _after < _before * 0.5:
        import logging
        logging.error(f"enrich: V5 heading strip ate {_before - _after} words ({_before}→{_after})")

    # Remove inline video sections from previous enrichment
    # Note: match with optional stress marks (Ві́део or Відео)
    _before = len(content.split())
    content = re.sub(
        r"\n### В[іi]\u0301?део — Video\n.*?(?=\n## |\n### |\n<!-- TAB:|\Z)",
        "",
        content,
        flags=re.DOTALL,
    )
    _after = len(content.split())
    if _after < _before * 0.5:
        import logging
        logging.error(f"enrich: video strip ate {_before - _after} words ({_before}→{_after})")

    # Remove any writer-generated vocabulary tables (the ENRICH step generates proper ones)
    _before = len(content.split())
    content = re.sub(
        r"\n### (?:Додаткові слова|Additional words|Вирази|Словник|Vocabulary).*?(?=\n## |\n<!-- TAB:|\Z)",
        "",
        content,
        flags=re.DOTALL,
    )
    _after = len(content.split())
    if _after < _before * 0.5:
        import logging
        logging.error(f"enrich: vocab strip ate {_before - _after} words ({_before}→{_after})")

    _post_strip_words = len(content.split())
    if _post_strip_words < _pre_strip_words * 0.3:
        import logging
        logging.error(
            f"enrich: stripping removed {_pre_strip_words - _post_strip_words} of "
            f"{_pre_strip_words} words! Restoring original content."
        )
        content = original_content
        # Re-strip only tab markers (safe)
        if "<!-- TAB:Словник -->" in content:
            content = content[:content.index("<!-- TAB:Словник -->")].strip()
        content = content.replace("<!-- TAB:Урок -->", "").strip()

    # 3. Build tab content
    slovnyk = _build_slovnyk(plan, content, slug=slug)
    resources = _build_resources(plan, slug=slug)

    # 4. Videos handled by watch-and-repeat activity injection — not by enrich.

    # 5. Assemble with tab markers
    parts = []

    # Safety: if content stripping left an empty body, something is wrong.
    # Refuse to produce an enriched file with empty Урок tab.
    # Real modules have 1000+ words. A completely empty body after stripping
    # means the regex ate the prose — refuse to enrich to prevent data loss.
    if not content.strip():
        import logging
        logging.error(
            f"enrich: body content is only {len(content.strip().split())} words "
            f"after stripping — refusing to enrich (would lose prose). "
            f"First 200 chars: {content.strip()[:200]!r}"
        )
        return original_content, []

    # Tab 1: Урок (the prose content with inline exercises and videos)
    parts.append("<!-- TAB:Урок -->")
    parts.append(content.strip())

    # Tab 2: Словник
    if slovnyk:
        parts.append("\n<!-- TAB:Словник -->")
        parts.append(slovnyk.strip())
        actions.append("slovnyk-table")

    # Tab 3: Зошит (workbook — extended exercises + watch-and-repeat activities)
    # Videos are handled by watch-and-repeat activity injection, not here.
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
