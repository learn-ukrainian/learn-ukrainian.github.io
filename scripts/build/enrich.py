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
from pathlib import Path

import yaml
from build.text_utils import parse_vocab_hint

# Tab markers — PUBLISH step converts these to <Tabs>/<TabItem>
TAB_MARKER = "<!-- TAB:{name} -->"


def _vocab_table_rows(items: list) -> list[str]:
    """Generate markdown table rows from vocabulary hint items."""
    rows = []
    for item in items:
        word, translation = parse_vocab_hint(item)
        rows.append(f"| **{word}** | {translation} |")
    return rows


def _extract_prose_vocab(content: str) -> list[str]:
    """Extract bold Ukrainian words/phrases from prose that aren't in plan vocabulary.

    Scans for **word** patterns in the content and returns Ukrainian words
    that the writer introduced but weren't in vocabulary_hints.
    """
    # Match **word** patterns — Ukrainian text only
    bold_pattern = re.compile(r"\*\*([а-яА-ЯіІїЇєЄґҐ'ʼ ]+)\*\*")
    words = []
    seen: set[str] = set()
    for match in bold_pattern.finditer(content):
        word = match.group(1).strip()
        if len(word) >= 2 and word.lower() not in seen:
            seen.add(word.lower())
            words.append(word)
    return words


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

    # Extract words from prose that aren't in the plan vocabulary
    prose_words = _extract_prose_vocab(content) if content else []

    # Build set of known words (lowercase) for deduplication
    known_words: set[str] = set()
    for item in required + recommended:
        word, _ = parse_vocab_hint(item)
        known_words.add(word.lower())

    # Words from prose not in plan AND not in previous modules
    additional = [
        w for w in prose_words
        if w.lower() not in known_words and w.lower() not in previous_vocab
    ]

    if not required and not recommended and not additional:
        return ""

    lines = []

    if required:
        lines.extend([
            "",
            "### Обов'язкові слова — Required words",
            "",
            "| Слово | Translation |",
            "|-------|-------------|",
            *_vocab_table_rows(required),
        ])

    if recommended:
        lines.extend([
            "",
            "### Рекомендовані слова — Recommended words",
            "",
            "| Слово | Translation |",
            "|-------|-------------|",
            *_vocab_table_rows(recommended),
        ])

    if additional:
        lines.extend([
            "",
            "### Додаткові слова з уроку — Additional words from the lesson",
            "",
            "| Слово | Translation |",
            "|-------|-------------|",
        ])
        for word in additional:
            lines.append(f"| **{word}** |  |")

    lines.append("")
    return "\n".join(lines)


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


def _build_resources(plan: dict) -> str:
    """Generate external resources section from plan references."""
    refs = plan.get("references", [])
    if not refs:
        return ""

    lines = []

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


def enrich(content: str, plan: dict) -> tuple[str, list[str]]:
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

    # 2. Build tab content
    slovnyk = _build_slovnyk(plan, content)
    videos = _build_video_embeds(plan)
    resources = _build_resources(plan)

    # 3. Find Summary section — it stays in the Урок tab
    # Remove Video/Словник/Resources sections if they were injected before (rebuild)
    content = re.sub(
        r"\n## (?:Video Resources|Відео — Video|Словник — Vocabulary|Resources|Ресурси — Resources)\n.*?(?=\n## |\Z)",
        "",
        content,
        flags=re.DOTALL,
    )

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

    enriched, actions = enrich(content, plan)

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
