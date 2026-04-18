"""Wiki context provider — supplies compiled wiki articles to the build pipeline.

Given a track and slug, finds and returns relevant wiki articles as formatted
context for injection into build prompts (all tracks — core and seminar).
"""

import re
import unicodedata
from pathlib import Path

from .config import TRACK_DOMAINS, WIKI_DIR
from .sources_schema import load_sources_registry, registry_path_for

# Max chars of wiki context to inject into build prompts.
#
# History: originally 30K on the principle that "wiki should not dominate
# the prompt." That principle was wrong for seminar tracks, where the wiki
# IS the content (HIST/BIO/LIT/OES/RUTH articles are 15-35K each and carry
# the decolonized framing + factual backbone the writer needs). At 30K,
# seminar modules were losing 60%+ of their knowledge corpus after the
# first article.
#
# Decision 2026-04-18: raise uniformly to 100K across all tracks (core +
# seminar). Rationale:
#   - Gemini 3.1 Pro handles long context cleanly below the ~150K attention
#     dilution elbow; 100K wiki → ~180K total prompt stays in the safe band.
#   - Fits 3-4 full articles comfortably (post relevance-rank sort).
#   - Cost delta is acceptable vs the quality floor raise.
#   - If quality on instruction-adherence dimensions (plan adherence,
#     vocabulary coverage) drops, back off first — not past 80K.
WIKI_CONTEXT_BUDGET = 100_000
_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ'][A-Za-zА-Яа-яІіЇїЄєҐґ'’-]{1,}")
_STOPWORDS = {
    "and",
    "for",
    "from",
    "into",
    "that",
    "the",
    "their",
    "these",
    "this",
    "those",
    "when",
    "where",
    "with",
    "але",
    "або",
    "вже",
    "вона",
    "вони",
    "для",
    "його",
    "про",
    "при",
    "після",
    "перед",
    "саме",
    "та",
    "тому",
    "що",
    "як",
}


def get_wiki_context(
    track: str,
    slug: str,
    *,
    plan: dict | None = None,
    include_sources_registry: bool = False,
) -> str:
    """Get formatted wiki context for a module build.

    Finds wiki articles relevant to the track/slug and returns them
    as a formatted markdown block ready for prompt injection.

    Args:
        track: Any track (e.g., "a2", "folk", "hist", "bio").
        slug: Module slug (e.g., "genitive-intro", "dumy-lytsarski").

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
            score = _relevance_score(md_file, slug, track, plan=plan)
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
        content = strip_meta(content)

        if total_chars + len(content) > WIKI_CONTEXT_BUDGET:
            # If we haven't included anything yet, take a truncated version
            if not parts:
                remaining = WIKI_CONTEXT_BUDGET - total_chars
                content = content[:remaining] + "\n\n*(скорочено)*"
            else:
                break

        rel_path = md_path.relative_to(WIKI_DIR)
        registry_note = ""
        if include_sources_registry:
            registry = load_sources_registry(registry_path_for(md_path))
            if registry.sources:
                summary = ", ".join(f"{entry.id}={entry.file}" for entry in registry.sources)
                registry_note = f"\n\nSources: {summary}"

        parts.append(f"### Вікі: {rel_path}\n\n{content}{registry_note}")
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


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[-_/.:]+", " ", stripped)


def _tokenize(text: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(_normalize_text(text))
        if len(token) > 2 and token.lower() not in _STOPWORDS
    }


def _plan_query_tokens(plan: dict | None) -> tuple[set[str], set[str]]:
    if not plan:
        return set(), set()

    general_parts: list[str] = []
    scenario_parts: list[str] = []

    for field in ("title", "subtitle", "focus", "register"):
        value = plan.get(field)
        if value:
            general_parts.append(str(value))

    general_parts.extend(str(item) for item in (plan.get("objectives") or []))
    general_parts.extend(str(item) for item in (plan.get("grammar") or []))

    for section in plan.get("content_outline") or []:
        general_parts.append(str(section.get("section", "")))
        general_parts.extend(str(point) for point in (section.get("points") or [])[:5])

    for situation in plan.get("dialogue_situations") or []:
        setting = str(situation.get("setting", ""))
        motivation = str(situation.get("motivation", ""))
        speakers = " ".join(str(s) for s in (situation.get("speakers") or []))
        if setting:
            scenario_parts.append(setting)
        if motivation:
            scenario_parts.append(motivation)
        if speakers:
            scenario_parts.append(speakers)

    return _tokenize(" ".join(general_parts)), _tokenize(" ".join(scenario_parts))


def _relevance_score(md_path: Path, slug: str, track: str, *, plan: dict | None = None) -> int:
    """Score how relevant a wiki article is to a given module slug.

    Higher = more relevant. Scoring:
    - Exact slug match in filename: +100
    - Slug words in filename: +10 each
    - Same subdomain as slug's domain mapping: +5
    - Any article in track domain: +1 (baseline)
    - Plan/query overlap in path: +4 each
    - Dialogue-situation overlap in path: +14 each
    """
    score = 1  # baseline — it's in a relevant domain
    stem = md_path.stem.lower()
    slug_lower = slug.lower()

    # Exact match
    if stem == slug_lower:
        score += 100

    # Slug word overlap
    slug_words = _tokenize(slug_lower.replace("-", " "))
    stem_words = _tokenize(stem.replace("-", " "))
    overlap = slug_words & stem_words
    score += len(overlap) * 10

    # Partial match (slug word appears in stem or vice versa)
    for sw in slug_words:
        if len(sw) > 3 and sw in stem:
            score += 5

    general_tokens, scenario_tokens = _plan_query_tokens(plan)
    path_tokens = _tokenize(md_path.as_posix())
    score += len(general_tokens & path_tokens) * 4
    score += len(scenario_tokens & path_tokens) * 14

    return score


def strip_meta(content: str) -> str:
    """Strip the <!-- wiki-meta ... --> comment from article content.

    Shared between build-side injection (get_wiki_context) and review-side
    prompt assembly (scripts/wiki/compile.py:_build_review_prompt) — the
    reviewer must not score metadata as if it were prose.

    Bounded match prevents the greedy ``.*?`` failure mode flagged
    by Gemini review #348 (#1323). If the wiki-meta opening exists but the
    closing ``-->`` is missing, a naive ``.*?`` regex would cross into a
    later comment such as ``<!-- VERIFY -->`` and silently delete all
    prose between them.

    The body uses a tempered repetition ``(?:(?!<!--).)*?`` instead of
    ``[^<]*?``: it forbids the *start of a new HTML comment* but still
    allows bare ``<`` characters (Gemini review msg #350 (#1323) caught
    that ``[^<]`` would silently fail on valid YAML payloads containing
    a single ``<``, e.g. ``description: "A < B"``). A malformed
    wiki-meta still fails to match because there's no ``-->`` before the
    next ``<!--``, so we still avoid corrupting content. We additionally
    warn on a detected-opening-without-close so callers can surface the
    issue during compilation.
    """
    import re
    import sys

    pattern = re.compile(r"<!--\s*wiki-meta\b(?:(?!<!--).)*?-->", re.DOTALL)
    result, n = pattern.subn("", content)
    if n == 0 and re.search(r"<!--\s*wiki-meta\b", content):
        print(
            "⚠️  strip_meta: found `<!-- wiki-meta` opening without a matching "
            "`-->`; leaving content intact to prevent silent deletion.",
            file=sys.stderr,
        )
    return result.strip()


# Backwards-compat alias for any lingering internal callers.
_strip_meta = strip_meta
