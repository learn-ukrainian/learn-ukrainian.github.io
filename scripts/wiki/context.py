"""Wiki context provider — supplies compiled wiki articles to the build pipeline.

Given a track and slug, finds and returns relevant wiki articles as formatted
context for injection into seminar build prompts.
"""

from pathlib import Path

from .config import TRACK_DOMAINS, WIKI_DIR

# Max chars of wiki context to inject into build prompts.
# The seminar write prompt is already ~5K + plan ~3K + knowledge packet ~8K.
# Wiki context should be substantial but not dominate.
WIKI_CONTEXT_BUDGET = 30_000


def get_wiki_context(track: str, slug: str) -> str:
    """Get formatted wiki context for a seminar module build.

    Finds wiki articles relevant to the track/slug and returns them
    as a formatted markdown block ready for prompt injection.

    Args:
        track: Seminar track (e.g., "folk", "hist", "bio").
        slug: Module slug (e.g., "dumy-lytsarski").

    Returns:
        Formatted markdown string with wiki articles, or empty string
        if no relevant articles found.
    """
    if not WIKI_DIR.exists():
        return ""

    # 1. Find articles in the track's wiki domains
    domains = TRACK_DOMAINS.get(track, [])
    if not domains:
        return ""

    # 2. Collect all articles from relevant domains
    candidate_articles: list[tuple[Path, int]] = []  # (path, relevance_score)
    for domain in domains:
        domain_dir = WIKI_DIR / domain
        if not domain_dir.exists():
            continue
        for md_file in domain_dir.rglob("*.md"):
            if md_file.name == "index.md":
                continue
            # Score by slug match
            score = _relevance_score(md_file, slug, track)
            candidate_articles.append((md_file, score))

    if not candidate_articles:
        return ""

    # 3. Sort by relevance (highest first)
    candidate_articles.sort(key=lambda x: -x[1])

    # 4. Build context within budget
    parts: list[str] = []
    total_chars = 0

    for md_path, _score in candidate_articles:
        content = md_path.read_text(encoding="utf-8")
        # Strip wiki-meta comment
        content = _strip_meta(content)

        if total_chars + len(content) > WIKI_CONTEXT_BUDGET:
            # If we haven't included anything yet, take a truncated version
            if not parts:
                remaining = WIKI_CONTEXT_BUDGET - total_chars
                content = content[:remaining] + "\n\n*(скорочено)*"
            else:
                break

        rel_path = md_path.relative_to(WIKI_DIR)
        parts.append(f"### Вікі: {rel_path}\n\n{content}")
        total_chars += len(content)

    if not parts:
        return ""

    body = "\n\n---\n\n".join(parts)
    return (
        "<wiki_context>\n"
        "## Compiled Wiki Knowledge\n\n"
        "The following articles from the project wiki provide compiled knowledge "
        "relevant to this module. Use them as authoritative context — they were "
        "compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).\n\n"
        f"{body}\n"
        "</wiki_context>"
    )


def _relevance_score(md_path: Path, slug: str, track: str) -> int:
    """Score how relevant a wiki article is to a given module slug.

    Higher = more relevant. Scoring:
    - Exact slug match in filename: +100
    - Slug words in filename: +10 each
    - Same subdomain as slug's domain mapping: +5
    - Any article in track domain: +1 (baseline)
    """
    score = 1  # baseline — it's in a relevant domain
    stem = md_path.stem.lower()
    slug_lower = slug.lower()

    # Exact match
    if stem == slug_lower:
        score += 100

    # Slug word overlap
    slug_words = set(slug_lower.replace("-", " ").split())
    stem_words = set(stem.replace("-", " ").split())
    overlap = slug_words & stem_words
    score += len(overlap) * 10

    # Partial match (slug word appears in stem or vice versa)
    for sw in slug_words:
        if len(sw) > 3 and sw in stem:
            score += 5

    return score


def _strip_meta(content: str) -> str:
    """Strip the <!-- wiki-meta ... --> comment from article content."""
    import re
    return re.sub(r"<!--\s*wiki-meta\b.*?-->", "", content, flags=re.DOTALL).strip()
