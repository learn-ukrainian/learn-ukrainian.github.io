"""V6 Step 7b: ENRICH — словник, videos, dialogue formatting, resources.

Deterministic enrichment step. Reads plan YAML and injects structural
elements into generated content that the LLM writer doesn't produce:

1. Словник (vocabulary table) from plan vocabulary_hints
2. YouTube video embeds from plan pronunciation_videos
3. External resources section from plan references
4. Dialogue block formatting (:::dialogue wrappers)

Runs after ANNOTATE, before VERIFY.

Issue: #1009
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from build.text_utils import parse_vocab_hint


def _vocab_table_rows(items: list) -> list[str]:
    """Generate markdown table rows from vocabulary hint items."""
    rows = []
    for item in items:
        word, translation = parse_vocab_hint(item)
        rows.append(f"| **{word}** | {translation} |")
    return rows


def _build_slovnyk(plan: dict) -> str:
    """Generate словник (vocabulary table) from plan vocabulary_hints."""
    vocab = plan.get("vocabulary_hints", {})
    required = vocab.get("required", [])
    recommended = vocab.get("recommended", [])

    if not required and not recommended:
        return ""

    lines = [
        "",
        "## Словник — Vocabulary",
        "",
        "### Required words",
        "",
        "| Слово | Translation |",
        "|-------|-------------|",
        *_vocab_table_rows(required),
    ]

    if recommended:
        lines.extend([
            "",
            "### Recommended words",
            "",
            "| Слово | Translation |",
            "|-------|-------------|",
            *_vocab_table_rows(recommended),
        ])

    lines.append("")
    return "\n".join(lines)


def _build_video_embeds(plan: dict) -> str:
    """Generate YouTube video embed section from plan pronunciation_videos."""
    pv = plan.get("pronunciation_videos", {})
    if not pv:
        return ""

    lines = ["", "## Video Resources", ""]

    overview = pv.get("overview", "")
    if overview:
        label = pv.get("credit", "Ukrainian Lessons")
        lines.append(f'<YouTubeVideo client:only="react" url="{overview}" label="Overview — {label}" />')
        lines.append("")

    playlist = pv.get("playlist", "")
    if playlist:
        lines.append(f"📋 [Full playlist]({playlist})")
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

    lines = ["", "## Resources", ""]

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
    # Pattern: 2+ consecutive lines starting with — (em dash)
    dialogue_pattern = re.compile(
        r"((?:^— .+\n){2,})",
        re.MULTILINE,
    )

    def _wrap(match: re.Match) -> str:
        block = match.group(1).rstrip("\n")
        return f":::dialogue\n{block}\n:::\n"

    return dialogue_pattern.sub(_wrap, content)


def enrich(content: str, plan: dict) -> tuple[str, list[str]]:
    """Enrich content with vocabulary table, videos, resources, and dialogue formatting.

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

    # 2. Build enrichment sections
    slovnyk = _build_slovnyk(plan)
    videos = _build_video_embeds(plan)
    resources = _build_resources(plan)

    # 3. Append enrichment sections before Summary (if it exists)
    # Find the Summary heading to insert enrichments before it
    summary_match = re.search(
        r"^(## (?:Підсумок|Summary).*$)",
        content,
        re.MULTILINE,
    )

    enrichments = ""
    if videos:
        enrichments += videos
        actions.append("video-embeds")
    if slovnyk:
        enrichments += slovnyk
        actions.append("slovnyk-table")
    if resources:
        enrichments += resources
        actions.append("external-resources")

    if enrichments:
        if summary_match:
            # Insert before Summary
            insert_pos = summary_match.start()
            content = content[:insert_pos] + enrichments + "\n" + content[insert_pos:]
        else:
            # Append at end
            content = content.rstrip() + "\n" + enrichments

    return content, actions


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
