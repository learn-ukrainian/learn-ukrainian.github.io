"""External resource handling for MDX generation.

Provides URL validation, YouTube embed conversion, discovery resource loading,
resource merging/deduplication, and vocabulary table formatting.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .utils import escape_jsx


def validate_and_clean_url(url: str, title: str = '') -> str:
    """Validate and clean URL for markdown link formatting.

    Detects and fixes common URL issues:
    - Incomplete angle brackets: <https://...  -> https://...
    - Unmatched parentheses in URL
    """
    if not url:
        return url

    original_url = url

    # Remove angle brackets if present (not needed in YAML, causes issues)
    if url.startswith('<'):
        if not url.endswith('>'):
            print(f"  \u26a0\ufe0f  Malformed URL (missing closing '>'): {title}")
            print(f"      {url}")
            url = url.lstrip('<')
        else:
            url = url[1:-1]  # Remove both angle brackets

    # Check for unmatched parentheses
    open_parens = url.count('(')
    close_parens = url.count(')')
    if open_parens != close_parens:
        print(f"  \u26a0\ufe0f  URL has unmatched parentheses: {title}")
        print(f"      {url}")
        print(f"      Expected {open_parens} closing parentheses, found {close_parens}")

    if url != original_url:
        print(f"      Fixed to: {url}")

    return url


# ---------------------------------------------------------------------------
# YouTube embed helper
# ---------------------------------------------------------------------------

_YT_VIDEO_LINK_RE = re.compile(
    r'\[([^\]]+)\]'                              # [link text]
    r'\('                                        # (
    r'(https?://(?:www\.)?'                      # http(s)://
    r'(?:youtube\.com/watch\?v=|youtu\.be/)'     # youtube.com/watch?v= or youtu.be/
    r'[^\)]+)'                                   # video ID + params
    r'\)'                                        # )
    r'\.?'                                       # optional trailing period
)

_YT_VID_ID_RE = re.compile(r'(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})')


_YT_JINJA_RE = re.compile(
    r'\{%\s*youtubeVideo\s+"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w-]+[^"]*?)"\s*%\}'
)
# Also match {% youtubeVideo id="VIDEO_ID" %} variant (Gemini sometimes produces this)
_YT_JINJA_ID_RE = re.compile(
    r'\{%\s*youtubeVideo\s+id="([A-Za-z0-9_-]{11})"\s*%\}'
)


def embed_youtube_video_links(body: str) -> str:
    """Replace YouTube markdown links with inline ``<YouTubeVideo>`` components.

    Transforms ``[text](youtube-watch-url)`` into a React component that shows
    a thumbnail and plays the video inline when clicked (no page navigation).
    Only matches watch / short-link URLs -- playlist links are left as-is.

    Also handles Jinja/Nunjucks-style ``{% youtubeVideo "url" %}`` tags that
    Gemini sometimes produces instead of markdown links.
    """

    def _yt_replace(m: re.Match) -> str:
        text = m.group(1)
        url = m.group(2)
        vid_match = _YT_VID_ID_RE.search(url)
        if not vid_match:
            return m.group(0)
        label = escape_jsx(text)
        return (
            f'\n\n<YouTubeVideo client:load url="{url}" label="{label}" />\n\n'
        )

    def _yt_jinja_replace(m: re.Match) -> str:
        url = m.group(1)
        vid_match = _YT_VID_ID_RE.search(url)
        if not vid_match:
            return m.group(0)
        return (
            f'\n\n<YouTubeVideo client:load url="{url}" label="Video" />\n\n'
        )

    def _yt_jinja_id_replace(m: re.Match) -> str:
        vid_id = m.group(1)
        url = f"https://www.youtube.com/watch?v={vid_id}"
        return (
            f'\n\n<YouTubeVideo client:load url="{url}" label="Video" />\n\n'
        )

    body = _YT_JINJA_ID_RE.sub(_yt_jinja_id_replace, body)
    body = _YT_JINJA_RE.sub(_yt_jinja_replace, body)
    return _YT_VIDEO_LINK_RE.sub(_yt_replace, body)


# ---------------------------------------------------------------------------
# Discovery -> MDX resources bridge
# ---------------------------------------------------------------------------

def load_discovery_resources(level_dir: Path, slug: str) -> dict:
    """Load discovery.yaml and convert to external_resources format.

    Reads from the canonical sidecar location: discovery/{slug}.yaml.
    Filters blogs with relevance_score >= 0.5 and maps content_type
    to the appropriate resource category (podcasts vs articles).

    Returns dict with keys: articles, podcasts (matching format_resources_for_mdx).
    """
    discovery_path = level_dir / "discovery" / f"{slug}.yaml"
    if not discovery_path.exists():
        return {}

    try:
        data = yaml.safe_load(discovery_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not data or not isinstance(data, dict):
        return {}

    articles: list[dict] = []
    podcasts: list[dict] = []

    for blog in data.get("blogs", []):
        score = blog.get("relevance_score", 0)
        if score < 0.5:
            continue
        item = {
            "title": blog.get("title", ""),
            "url": blog.get("url", ""),
            "source": blog.get("source", ""),
            "relevance": "high" if score >= 0.7 else "medium",
        }
        content_type = blog.get("content_type", "")
        if content_type.startswith("podcast_episode"):
            podcasts.append(item)
        else:
            articles.append(item)

    result: dict[str, list] = {}
    if articles:
        result["articles"] = articles
    if podcasts:
        result["podcasts"] = podcasts
    return result


def merge_resources(curated: dict, discovery: dict) -> dict:
    """Merge curated and discovery resources, deduplicating by URL.

    Curated items appear first (higher priority). For each category
    (articles, podcasts, youtube, websites, books), items are merged
    and deduplicated by URL.
    """
    if not discovery:
        return curated
    if not curated:
        return discovery

    merged = dict(curated)  # shallow copy
    for category in ("articles", "podcasts", "youtube", "websites", "books"):
        curated_items = curated.get(category, [])
        discovery_items = discovery.get(category, [])
        if not discovery_items:
            continue
        seen_urls = {item.get("url", "") for item in curated_items if item.get("url")}
        deduped = list(curated_items)
        for item in discovery_items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped.append(item)
        merged[category] = deduped
    return merged


def format_resources_for_mdx(resources: dict, is_ukrainian_forced: bool = False) -> str:
    """Format external resources for MDX output (emoji template).

    Args:
        resources: Dict with keys: podcasts, youtube, articles, books, websites
        is_ukrainian_forced: Whether to force Ukrainian headers

    Returns:
        Formatted markdown string for [!resources] callout block
    """
    if not resources or not any(resources.get(t) for t in ['podcasts', 'youtube', 'articles', 'books', 'websites']):
        return ""

    header_title = "Зовнішні ресурси" if is_ukrainian_forced else "External Resources"

    lines = []
    lines.append(f"> [!resources] \U0001f517 {header_title}")
    lines.append(">")

    # Emoji icons per resource type
    display_names = {
        'Podcasts': 'Подкасти',
        'YouTube': 'YouTube',
        'Articles': 'Статті',
        'Books': 'Книги',
        'Websites': 'Сайти'
    }

    resource_config = [
        ('podcasts', '\U0001f3a7', 'Podcasts'),
        ('youtube', '\U0001f4fa', 'YouTube'),
        ('articles', '\U0001f4d6', 'Articles'),
        ('books', '\U0001f4da', 'Books'),
        ('websites', '\U0001f310', 'Websites')
    ]

    # Priority and relevance maps for sorting
    priority_map = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1, None: 0}
    relevance_priority = {'high': 3, 'medium': 2, 'low': 1}

    for resource_type, icon, display_name in resource_config:
        items = resources.get(resource_type, [])
        if not items:
            continue

        final_display_name = display_names.get(display_name, display_name) if is_ukrainian_forced else display_name

        # Sort by: priority (1->5, highest first) -> relevance (high->low) -> title (A->Z)
        sorted_items = sorted(
            items,
            key=lambda x: (
                -priority_map.get(x.get('priority'), 0),
                -relevance_priority.get(x.get('relevance', 'low'), 0),
                x.get('title', '').lower()
            )
        )

        # Add section header
        lines.append(f"> **{icon} {final_display_name}:**")

        # Format each item
        for item in sorted_items:
            title = item.get('title', 'Unknown')
            url = validate_and_clean_url(item.get('url', ''), title)

            if resource_type == 'podcasts':
                desc = item.get('match_reason') or item.get('description', '')
                if desc:
                    lines.append(f"> - [{title}]({url}) \u2014 {desc}")
                else:
                    lines.append(f"> - [{title}]({url})")

            elif resource_type == 'articles':
                source = item.get('source', '')
                desc = item.get('description', source)
                if desc:
                    lines.append(f"> - [{title}]({url}) \u2014 {desc}")
                else:
                    lines.append(f"> - [{title}]({url})")

            elif resource_type == 'books':
                author = item.get('author', 'Unknown')
                pages = item.get('pages', '')
                desc = item.get('description', '')

                parts = [f"{title} by {author}"]
                if pages:
                    parts.append(f"(pages: {pages})")
                if desc:
                    parts.append(f"\u2014 {desc}")
                lines.append(f"> - {' '.join(parts)}")

            elif resource_type == 'youtube':
                channel = item.get('channel', '')
                if channel:
                    lines.append(f"> - [{title}]({url}) \u2014 {channel}")
                else:
                    lines.append(f"> - [{title}]({url})")

            elif resource_type == 'websites':
                source = item.get('source', '')
                desc = item.get('description', source)
                if desc:
                    lines.append(f"> - [{title}]({url}) \u2014 {desc}")
                else:
                    lines.append(f"> - [{title}]({url})")

        # Add blank line between sections
        lines.append(">")

    # Remove trailing blank line
    if lines and lines[-1] == ">":
        lines.pop()

    return '\n'.join(lines)


# =============================================================================
# VOCABULARY HELPERS
# =============================================================================

def vocab_items_to_markdown(items: list[dict], header_text: str = "Vocabulary") -> str:
    """Tier 1/2 (A1/A2): 6 columns (Scaffolding)."""
    lines = [
        f"## {header_text}",
        "",
        "| Word | IPA | English | POS | Gender | Note |",
        "| --- | --- | --- | --- | --- | --- |"
    ]
    for item in items:
        # Map gender m/f/n -> ch/zh/s
        g_map = {'m': '\u0447', 'f': '\u0436', 'n': '\u0441', 'pl': 'pl', '-': '-', '': ''}
        raw_g = item.get('gender', '')
        g_val = g_map.get(raw_g, raw_g)

        # Map POS propn -> name
        raw_p = item.get('pos', '')
        p_val = 'name' if raw_p == 'propn' else raw_p

        line = f"| {item.get('lemma')} | {item.get('ipa','')} | {item.get('translation','')} | {p_val} | {g_val} | {item.get('usage','')} |"
        lines.append(line)

    return '\n'.join(lines)


def b1_vocab_items_to_markdown(items: list[dict], header_text: str = "\u0421\u043b\u043e\u0432\u043d\u0438\u043a") -> str:
    """Tier 3/4 (B1-C2): 5 columns (Ukrainian, IPA included)."""
    lines = [
        f"## {header_text}",
        "",
        "| \u0421\u043b\u043e\u0432\u043e | \u0412\u0438\u043c\u043e\u0432\u0430 | \u041f\u0435\u0440\u0435\u043a\u043b\u0430\u0434 | \u0427\u041c | \u041f\u0440\u0438\u043c\u0456\u0442\u043a\u0430 |",
        "| --- | --- | --- | --- | --- |"
    ]
    for item in items:
        # Map POS to Ukrainian abbreviation
        pos_map = {
            'noun': '\u0456\u043c', 'verb': '\u0434\u0456\u0454\u0441\u043b', 'adj': '\u043f\u0440\u0438\u043a\u043c', 'adv': '\u043f\u0440\u0438\u0441\u043b',
            'prep': '\u043f\u0440\u0438\u0439\u043c', 'conj': '\u0441\u043f\u043e\u043b', 'pron': '\u0437\u0430\u0439\u043c', 'phrase': '\u0444\u0440\u0430\u0437\u0430',
            'propn': '\u043d\u0430\u0437\u0432\u0430'
        }
        raw_p = item.get('pos', '')
        p_val = pos_map.get(raw_p, raw_p)

        line = f"| **{item.get('lemma')}** | {item.get('ipa','')} | {item.get('translation','')} | {p_val} | {item.get('usage','')} |"
        lines.append(line)

    return '\n'.join(lines)
