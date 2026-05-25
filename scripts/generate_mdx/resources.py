"""External resource handling for MDX generation.

Provides URL validation, YouTube embed conversion, discovery resource loading,
resource merging/deduplication, and vocabulary table formatting.
"""

from __future__ import annotations

import json
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

# Plain URL in bullet list: "- Label: https://www.youtube.com/watch?v=..."
# or standalone line: "https://www.youtube.com/watch?v=..."
_YT_PLAIN_URL_RE = re.compile(
    r'^(\s*[-*]\s+(.+?):\s+)'                       # bullet + label + colon
    r'(https?://(?:www\.)?'                          # http(s)://
    r'(?:youtube\.com/watch\?v=|youtu\.be/)'         # youtube.com/watch?v= or youtu.be/
    r'[A-Za-z0-9_=&?%.-]+)'                           # video ID + URL params (no spaces)
    r'\s*$',                                         # end of line
    re.MULTILINE,
)

# Standalone bare URL on its own line (no bullet, no label)
_YT_BARE_URL_RE = re.compile(
    r'^(\s*)'                                        # optional leading whitespace
    r'(https?://(?:www\.)?'                          # http(s)://
    r'(?:youtube\.com/watch\?v=|youtu\.be/)'         # youtube.com/watch?v= or youtu.be/
    r'[A-Za-z0-9_=-]+)'                              # video ID + params
    r'\s*$',                                         # end of line
    re.MULTILINE,
)

# iframe embeds (Gemini sometimes produces these instead of markdown links)
# Matches: <iframe ... src="https://www.youtube.com/embed/VIDEO_ID" ...></iframe>
# Also matches when inside callout boxes (> <iframe ...)
_YT_IFRAME_RE = re.compile(
    r'>?\s*<iframe[^>]*src="(https?://(?:www\.)?youtube\.com/embed/[A-Za-z0-9_-]+)"[^>]*>'
    r'(?:</iframe>)?',
    re.IGNORECASE,
)


def embed_youtube_video_links(body: str) -> str:
    """Replace YouTube markdown links with inline ``<YouTubeVideo>`` components.

    Transforms ``[text](youtube-watch-url)`` into a React component that shows
    a thumbnail and plays the video inline when clicked (no page navigation).
    Only matches watch / short-link URLs -- playlist links are left as-is.

    Also handles Jinja/Nunjucks-style ``{% youtubeVideo "url" %}`` tags that
    Gemini sometimes produces instead of markdown links.
    """

    def _yt_component(url: str, label: str = "Video") -> str | None:
        """Build <YouTubeVideo> JSX if url has a valid video ID, else None."""
        if not _YT_VID_ID_RE.search(url):
            return None
        safe_url = escape_jsx(url)
        safe_label = escape_jsx(label)
        return f'\n\n<YouTubeVideo client:only="react" url="{safe_url}" label="{safe_label}" />\n\n'

    def _yt_replace(m: re.Match) -> str:
        # Don't replace YouTube links inside markdown table cells
        start = m.start()
        line_start = body.rfind('\n', 0, start) + 1
        line_prefix = body[line_start:start].strip()
        if line_prefix.startswith('|') or line_prefix.endswith('|'):
            return m.group(0)  # Leave table links as-is
        return _yt_component(m.group(2), m.group(1)) or m.group(0)

    def _yt_jinja_replace(m: re.Match) -> str:
        return _yt_component(m.group(1)) or m.group(0)

    def _yt_jinja_id_replace(m: re.Match) -> str:
        return _yt_component(f"https://www.youtube.com/watch?v={m.group(1)}") or m.group(0)

    def _yt_plain_url_replace(m: re.Match) -> str:
        return _yt_component(m.group(3), m.group(2).strip()) or m.group(0)

    def _yt_bare_url_replace(m: re.Match) -> str:
        return _yt_component(m.group(2)) or m.group(0)

    def _yt_iframe_replace(m: re.Match) -> str:
        embed_url = m.group(1)
        # Convert embed URL to watch URL for the component
        watch_url = embed_url.replace("/embed/", "/watch?v=")
        return _yt_component(watch_url) or m.group(0)

    # Strip [!video] callout wrappers — these are just containers for iframes
    body = re.sub(r'>\s*\[!video\]\s*\n', '', body)

    # Process in order: specific patterns first, then general
    body = _YT_IFRAME_RE.sub(_yt_iframe_replace, body)
    body = _YT_JINJA_ID_RE.sub(_yt_jinja_id_replace, body)
    body = _YT_JINJA_RE.sub(_yt_jinja_replace, body)
    body = _YT_VIDEO_LINK_RE.sub(_yt_replace, body)
    body = _YT_PLAIN_URL_RE.sub(_yt_plain_url_replace, body)
    return _YT_BARE_URL_RE.sub(_yt_bare_url_replace, body)


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


RESOURCE_ROLE_ICONS = {
    'textbook': '📚',
    'book': '📚',
    'youtube': '📺',
    'video': '🎥',
    'blog': '📝',
    'podcast': '🎧',
    'audio': '🎧',
    'article': '📄',
    'wiki': '🔗',
    'website': '🔗',
}

RESOURCE_GROUPS = (
    ('books', '📚', 'Books', 'Книги', {'textbook', 'book'}),
    ('videos', '📺', 'Videos', 'Відео', {'youtube', 'video'}),
    ('articles', '📝', 'Articles', 'Статті', {'blog', 'article'}),
    ('audio', '🎧', 'Audio', 'Аудіо', {'podcast', 'audio'}),
    ('online', '🔗', 'Online resources', 'Онлайн-ресурси', {'wiki', 'website'}),
)

_PIPELINE_METADATA_LINE_RE = re.compile(
    r"\b(?:writer telemetry|retrieved chunk(?:_id)?\b)",
    re.IGNORECASE,
)
_PIPELINE_METADATA_FRAGMENT_RE = re.compile(
    r"\([^)]*\b(?:packet_)?chunk_id\b[^)]*\)"
    r"|\([^)]*\b(?:wiki|vesum)_query_id\b[^)]*\)"
    r"|\bknowledge packet anchor\s+[A-Za-z0-9_-]+\s*:?"
    r"|\b(?:packet_)?chunk_id\s*[:=]\s*[\w./:-]+"
    r"|\b(?:wiki|vesum)_query_id\s*[:=]\s*[\w./:-]+",
    re.IGNORECASE,
)

LEGACY_RESOURCE_ROLE = {
    'podcasts': 'podcast',
    'youtube': 'youtube',
    'articles': 'article',
    'books': 'textbook',
    'websites': 'wiki',
}


def _resource_role(item: dict, legacy_bucket: str | None = None) -> str:
    role = str(item.get('role') or '').strip().lower()
    if role:
        return role
    if legacy_bucket is not None:
        return LEGACY_RESOURCE_ROLE.get(legacy_bucket, legacy_bucket)
    return 'textbook'


def _iter_resources_by_role(resources: dict | list) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {group_id: [] for group_id, *_ in RESOURCE_GROUPS}
    if isinstance(resources, list):
        iterable = [(None, resources)]
    else:
        iterable = [(key, value) for key, value in resources.items()]

    role_to_group = {
        role: group_id
        for group_id, _icon, _en, _uk, roles in RESOURCE_GROUPS
        for role in roles
    }
    for bucket, items in iterable:
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            role = _resource_role(item, bucket)
            group_id = role_to_group.get(role, 'online')
            grouped[group_id].append({**item, 'role': role})
    return grouped


def _resource_sort_key(item: dict) -> tuple[int, int, str]:
    priority_map = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1, None: 0}
    relevance_priority = {'high': 3, 'medium': 2, 'low': 1}
    return (
        -priority_map.get(item.get('priority'), 0),
        -relevance_priority.get(item.get('relevance', 'low'), 0),
        str(item.get('title', '')).lower(),
    )


def _public_resource_text(value: object) -> str:
    """Return learner-facing resource text with pipeline metadata removed."""
    text = str(value or '').strip()
    if not text:
        return ''

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not _PIPELINE_METADATA_LINE_RE.search(line)
    ]
    text = ' '.join(lines)
    text = _PIPELINE_METADATA_FRAGMENT_RE.sub('', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    text = re.sub(r'^[\s,.;:()/-]+|[\s,;:()/-]+$', '', text)
    return text


def _public_resource_description(item: dict) -> str:
    for key in ('match_reason', 'description', 'notes', 'channel', 'source'):
        desc = _public_resource_text(item.get(key))
        if desc:
            return desc
    return ''


def _format_textbook_resource(item: dict) -> list[str]:
    title = _public_resource_text(item.get('title')) or 'Unknown'
    author = _public_resource_text(item.get('author'))
    pages = item.get('pages') or item.get('page') or ''
    desc = _public_resource_description(item)
    source_ref = _public_resource_text(item.get('source_ref')) or title

    display_title = source_ref
    if pages and str(pages) not in display_title:
        display_title = f"{display_title}, p. {pages}"
    if author and not display_title.startswith(author):
        display_title = f"{author} — {display_title}"

    lines = [f"> - 📚 **{display_title}**"]
    if desc:
        lines.append(f">   {desc}")
    return lines


def _format_linked_resource(item: dict) -> str:
    role = _resource_role(item)
    icon = RESOURCE_ROLE_ICONS.get(role, '🔗')
    title = _public_resource_text(item.get('title')) or 'Unknown'
    url = validate_and_clean_url(str(item.get('url') or ''), title)
    desc = _public_resource_description(item)
    label = f"[{title}]({url})" if url else f"**{title}**"
    suffix = f" — {desc}" if desc else ""
    return f"> - {icon} {label}{suffix}"


def format_resources_for_mdx(resources: dict | list, is_ukrainian_forced: bool = False) -> str:
    """Format external resources for MDX output, grouped by resource role."""
    if not resources:
        return ""

    grouped = _iter_resources_by_role(resources)
    if not any(grouped.values()):
        return ""

    header_title = "Зовнішні ресурси" if is_ukrainian_forced else "External Resources"

    lines = [f"> [!resources] 🔗 {header_title}", ">"]

    for group_id, icon, english_name, ukrainian_name, _roles in RESOURCE_GROUPS:
        items = grouped[group_id]
        if not items:
            continue
        display_name = ukrainian_name if is_ukrainian_forced else english_name
        lines.append(f"> **{icon} {display_name}:**")
        for item in sorted(items, key=_resource_sort_key):
            if _resource_role(item) in {'textbook', 'book'}:
                lines.extend(_format_textbook_resource(item))
            else:
                lines.append(_format_linked_resource(item))
        lines.append(">")

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


def vocab_items_to_components(items: list[dict], header_text: str = "Vocabulary") -> str:
    """Tier 1/2 (A1/A2): flashcards plus browsable vocabulary cards."""
    cards = []
    words = []
    for item in items:
        lemma = str(item.get('lemma') or item.get('word') or '').strip()
        translation = str(item.get('translation') or '').strip()
        example = str(item.get('example') or item.get('usage') or '').strip()
        if not lemma:
            continue

        cards.append({
            "front": lemma,
            "back": translation,
        })

        entry = {
            "word": lemma,
            "translation": translation,
            "pos": item.get('pos', ''),
            "gender": item.get('gender', ''),
            "example": example,
            "examples": [value for value in (translation, example) if value],
        }
        words.append({key: value for key, value in entry.items() if value not in (None, "", [])})

    card_json = json.dumps(cards, ensure_ascii=False, separators=(',', ':')).replace('`', '\\`').replace('${', '\\${')
    word_json = json.dumps(words, ensure_ascii=False, separators=(',', ':')).replace('`', '\\`').replace('${', '\\${')
    return (
        f"## {header_text}\n\n"
        f"<VocabCard client:only=\"react\" words={{JSON.parse(`{word_json}`)}} title=\"{escape_jsx(header_text)}\" />\n\n"
        f"<FlashcardDeck client:only=\"react\" cards={{JSON.parse(`{card_json}`)}} />"
    )


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
