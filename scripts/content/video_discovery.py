"""Video/blog discovery for the build pipeline.

Searches curated YouTube channels for relevant content, downloads transcripts,
and scores relevance using Gemini Flash. Also matches blog articles from
ukrainianlessons.com and Dobra Forma against module topics.

Non-blocking: all exceptions caught, returns empty/default results on failure.

Used by phase_discover() in pipeline_v5.py.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# Import helpers — keyword building, blog/RAG search, formatting
from content.video_discovery_helpers import (
    _default_qdrant_check,
    _search_blog_dbs,
    build_discovery_keywords,
    build_search_keywords,
    cap_query,
    format_blog_discovery,
    format_rag_discovery,
)
from content.video_discovery_helpers import (
    search_rag as _search_rag_impl,
)

logger = logging.getLogger(__name__)

TRANSCRIPT_CAP = 50_000
MAX_QUERY_LENGTH = 120  # yt-dlp search breaks with very long queries

# Paths to blog databases (relative to project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOG_DB_PATHS: list[Path] = [
    _PROJECT_ROOT / "docs" / "resources" / "ukrainianlessons" / "blog_db.json",
    _PROJECT_ROOT / "docs" / "resources" / "dobraforma" / "dobraforma_db.json",
    _PROJECT_ROOT / "docs" / "resources" / "talkukrainian" / "talkukrainian_db.json",
    _PROJECT_ROOT / "docs" / "resources" / "verba" / "verba_db.json",
]
PODCAST_DB_PATH = _PROJECT_ROOT / "docs" / "resources" / "podcasts" / "podcast_db.json"
CURATED_RESOURCES_PATH = _PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
SCORE_DB_PATH = _PROJECT_ROOT / "docs" / "resources" / "ukrainianlessons" / "resource_module_scores_final.json"


# ---------------------------------------------------------------------------
# Blog discovery — DB loading and curated/score search (stateful caches)
# ---------------------------------------------------------------------------

_blog_db_cache: list[dict] | None = None
_score_db_cache: dict | None = None
_curated_cache: dict | None = None


def _load_blog_dbs() -> list[dict]:
    """Load all blog + podcast database files. Returns flat list of article dicts."""
    global _blog_db_cache
    if _blog_db_cache is not None:
        return _blog_db_cache
    articles: list[dict] = []
    for db_path in BLOG_DB_PATHS:
        if not db_path.exists():
            continue
        try:
            data = json.loads(db_path.read_text("utf-8"))
            articles.extend(data.get("articles", []))
        except Exception as e:
            logger.debug("Failed to load blog DB %s: %s", db_path, e)

    if PODCAST_DB_PATH.exists():
        try:
            pod_data = json.loads(PODCAST_DB_PATH.read_text("utf-8"))
            episodes = pod_data if isinstance(pod_data, list) else pod_data.get("episodes", [])
            for ep in episodes:
                articles.append({
                    "id": ep.get("id", ""),
                    "url": ep.get("url", ""),
                    "title": ep.get("title", ""),
                    "topics": ep.get("tags", []),
                    "description": ep.get("summary", ""),
                    "suggested_level": "",
                    "content_type": "podcast_episode",
                    "source": "ukrainianlessons.com",
                    "series": ep.get("season", ""),
                    "season": ep.get("season", 0),
                    "episode": ep.get("episode_number", 0),
                })
        except Exception as e:
            logger.debug("Failed to load podcast DB: %s", e)
    _blog_db_cache = articles
    return articles


def _load_score_db() -> dict:
    """Load pre-computed module->resource score mappings."""
    global _score_db_cache
    if _score_db_cache is not None:
        return _score_db_cache
    if not SCORE_DB_PATH.exists():
        _score_db_cache = {}
        return _score_db_cache
    try:
        _score_db_cache = json.loads(SCORE_DB_PATH.read_text("utf-8"))
    except Exception:
        _score_db_cache = {}
    return _score_db_cache


def _load_curated_resources() -> dict:
    """Load curated per-module resources from external_resources.yaml."""
    global _curated_cache
    if _curated_cache is not None:
        return _curated_cache
    if not CURATED_RESOURCES_PATH.exists():
        _curated_cache = {}
        return _curated_cache
    try:
        data = yaml.safe_load(CURATED_RESOURCES_PATH.read_text("utf-8"))
        _curated_cache = data.get("resources", {})
    except Exception as e:
        logger.debug("Failed to load curated resources: %s", e)
        _curated_cache = {}
    return _curated_cache


def _search_curated_resources(module_slug, results, seen_urls):
    """Layer 0: Curated per-module resources from external_resources.yaml."""
    curated = _load_curated_resources()
    matching_keys = [k for k in curated if k == module_slug or k.endswith(f"-{module_slug}")]
    for key in matching_keys:
        module_resources = curated.get(key, {})
        if not module_resources:
            continue
        for cat, score in [("articles", 1.0), ("websites", 0.95)]:
            for item in module_resources.get(cat, []):
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append({
                        "url": url,
                        "title": item.get("title", ""),
                        "source": item.get("source", "curated"),
                        "relevance_score": score,
                        "topics": [],
                    })


def _search_score_db(module_slug, level, results, seen_urls):
    """Layer 1: Pre-computed score DB."""
    score_db = _load_score_db()
    slug_variants = [f"{level.lower()}-{module_slug}", module_slug]
    for slug_key in slug_variants:
        if slug_key in score_db:
            for entry in score_db[slug_key]:
                url = entry.get("resource_url", "")
                if url and url not in seen_urls and entry.get("score", 0) >= 60:
                    seen_urls.add(url)
                    results.append({
                        "url": url,
                        "title": entry.get("resource_title", ""),
                        "source": "ukrainianlessons.com",
                        "relevance_score": entry.get("score", 0) / 100.0,
                        "topics": [],
                    })


def search_blogs(
    module_slug: str,
    level: str,
    topic_title: str,
    keywords: list[str],
    max_results: int = 5,
) -> list[dict]:
    """Find relevant blog/podcast articles for a module.

    Three-layer approach:
    0. Curated per-module resources (external_resources.yaml)
    1. Pre-computed score DB (resource_module_scores_final.json)
    2. Keyword + topic matching against blog/podcast DBs

    Returns list of dicts with: url, title, source, relevance_score, topics.
    """
    results: list[dict] = []
    seen_urls: set[str] = set()

    _search_curated_resources(module_slug, results, seen_urls)
    _search_score_db(module_slug, level, results, seen_urls)
    _search_blog_dbs(level, topic_title, keywords, results, seen_urls, _load_blog_dbs)

    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    return results[:max_results]


# ---------------------------------------------------------------------------
# RAG availability check
# ---------------------------------------------------------------------------

def _is_qdrant_available() -> bool:
    """Check if Qdrant is reachable without loading heavy models."""
    return _default_qdrant_check()


def search_rag(
    keywords: list[str],
    track: str,
    level: str = "",
    limit_text: int = 5,
    limit_images: int = 3,
    limit_literary: int = 3,
    is_qdrant_available_fn=None,
) -> dict[str, list[dict]]:
    """Search RAG collections. Wrapper that defaults to module-level _is_qdrant_available."""
    return _search_rag_impl(
        keywords, track, level, limit_text, limit_images, limit_literary,
        is_qdrant_available_fn=is_qdrant_available_fn or _is_qdrant_available,
    )


# Channel allowlist
DEFAULT_CHANNELS: list[dict[str, Any]] = [
    {"name": "Ukrainian Lessons", "handle": "@UkrainianLessons", "tracks": ["*"]},
    {"name": "Ukrainian with Olha", "handle": "@ukrainianwitholha", "tracks": ["*"]},
    {"name": "Let's Learn Ukrainian", "handle": "@LetsLearnUkrainian", "tracks": ["*"]},
    {"name": "Speak Ukrainian", "handle": "@SpeakUkrainian", "tracks": ["*"]},
    {"name": "Learn Ukrainian Language", "handle": "@LearnUkrainianLanguage", "tracks": ["*"]},
    {"name": "Learn Ukrainian with Vakulenko", "handle": "@learnukrainianwithvakulenko", "tracks": ["*"]},
    {"name": "VERBA SCHOOL", "handle": "@VERBA_SCHOOL", "tracks": ["*"]},
    {"name": "Red Purple Ukrainian", "handle": "@redpurple_ua", "tracks": ["*"]},
    {"name": "Ukrainian Guy", "handle": "@ukrainianguy", "tracks": ["*"]},
    {"name": "Bright Kids Ukrainian", "handle": "@BrightKidsUkrainianSchool", "tracks": ["a1", "a2"]},
    {"name": "Listen & Read", "handle": "@listen-read", "tracks": ["*"]},
    {"name": "UkrainerNet", "handle": "@ukrainernet", "tracks": ["*"]},
    {"name": "Ukrainian Online School", "handle": "@ukrainian-online-school", "tracks": ["*"]},
    {"name": "\u0420\u0435\u0430\u043b\u044c\u043d\u0430 \u0406\u0441\u0442\u043e\u0440\u0456\u044f", "handle": "@realnaistoriia", "tracks": ["hist", "istorio", "bio"]},
    {"name": "Harvard Ukrainian Research Institute", "handle": "@ukrainianresearchinstitute1041", "tracks": ["hist", "istorio", "bio", "lit"]},
    {"name": "\u041a\u043e\u043c\u0456\u043a \u0406\u0441\u0442\u043e\u0440\u0438\u043a", "handle": "@komikistoryk", "tracks": ["hist", "istorio", "bio"]},
    {"name": "\u0406\u041c\u0422\u0413\u0428", "handle": "@imtgsh", "tracks": ["hist", "istorio", "bio"]},
    {"name": "\u0406\u0441\u0442\u043e\u0440\u0456\u044f \u041c\u043e\u0432\u0438", "handle": "@Istoria-Movy", "tracks": ["oes", "ruth"]},
    {"name": "\u0421\u0443\u0441\u043f\u0456\u043b\u044c\u043d\u0435 \u041a\u0443\u043b\u044c\u0442\u0443\u0440\u0430", "handle": "@SuspilneKultura", "tracks": ["lit", "b2", "c1", "c2"]},
    {"name": "\u0421\u0443\u0441\u043f\u0456\u043b\u044c\u043d\u0435 \u0414\u043e\u043a", "handle": "@SuspilneDoc", "tracks": ["hist", "bio", "lit", "b2", "c1"]},
    {"name": "Repainted Fox", "handle": "@repaintedfox", "tracks": ["b1", "b2", "c1"]},
    {"name": "Klopotenko", "handle": "@klopotenko", "tracks": ["a2", "b1", "b2"]},
    {"name": "Radio Khartia", "handle": "@RadioKhartia", "tracks": ["lit", "c1", "c2"]},
]


@dataclass
class VideoCandidate:
    url: str
    channel: str
    title: str
    transcript: str = ""
    relevance_score: float = 0.0
    relevance_note: str = ""
    transcript_excerpt: str = ""
    embed_suggestion: str = ""


@dataclass
class DiscoveryResult:
    discovered_at: str = ""
    query_keywords: list[str] = field(default_factory=list)
    videos: list[VideoCandidate] = field(default_factory=list)
    blogs: list[dict] = field(default_factory=list)
    rag_chunks: list[dict] = field(default_factory=list)
    rag_images: list[dict] = field(default_factory=list)
    rag_literary: list[dict] = field(default_factory=list)
    error: str | None = None
    warning: str | None = None


# ---------------------------------------------------------------------------
# SRT cleaning
# ---------------------------------------------------------------------------

def clean_srt(text: str) -> str:
    """Strip SRT metadata (timestamps, sequence numbers), dedup consecutive lines."""
    lines = text.splitlines()
    final: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d+$", line):
            continue
        if "-->" in line:
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if not line:
            continue
        if not final or final[-1] != line:
            final.append(line)
    return " ".join(final)


# ---------------------------------------------------------------------------
# Transcript download
# ---------------------------------------------------------------------------

def download_transcript(url: str) -> str:
    """Download Ukrainian auto-subs via yt-dlp. Returns plain text or empty string."""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "subs"
            cmd = [
                "yt-dlp", url,
                "--write-subs", "--write-auto-subs",
                "--sub-langs", "uk",
                "--convert-subs", "srt",
                "--skip-download",
                "--output", f"{tmp_path}.%(ext)s",
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
            srt_file = None
            for f in Path(tmp_dir).glob("*.uk.srt"):
                srt_file = f
                break
            if srt_file is None or not srt_file.exists():
                return ""
            srt_text = srt_file.read_text(encoding="utf-8", errors="replace")
            text = clean_srt(srt_text)
            return text[:TRANSCRIPT_CAP] if len(text) > TRANSCRIPT_CAP else text
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug("Transcript download failed for %s: %s", url, e)
        return ""
    except Exception as e:
        logger.debug("Unexpected error downloading transcript for %s: %s", url, e)
        return ""


# ---------------------------------------------------------------------------
# Channel filtering & search
# ---------------------------------------------------------------------------

def filter_channels(channels: list[dict], track: str) -> list[dict]:
    """Filter channel allowlist by track relevance.

    Returns track-specific channels first, then generic (*) channels.
    This ordering lets callers search specific channels first and
    stop early to avoid rate limiting.
    """
    base_track = track.split("-")[0].lower()
    specific = []
    generic = []
    for ch in channels:
        tracks = ch.get("tracks", [])
        if base_track in tracks or track.lower() in tracks:
            specific.append(ch)
        elif "*" in tracks:
            generic.append(ch)
    return specific + generic


_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_REJECTED_LANGS = {"ru", "be", "bg"}  # Russian, Belarusian, Bulgarian


def _filter_ukrainian_keywords(keywords: list[str]) -> list[str]:
    """Keep only keywords containing Cyrillic characters (Ukrainian terms)."""
    return [kw for kw in keywords if _CYRILLIC_RE.search(kw)]


def search_channel(keywords: list[str], channel_handle: str, max_results: int = 3) -> list[dict]:
    """Search YouTube via yt-dlp for videos matching keywords.

    Uses channel-specific search URL (youtube.com/@handle/search?query=...)
    to find relevant videos within the target channel. Falls back to global
    ytsearch if channel search fails.

    Uses only Cyrillic keywords for search (English kills Ukrainian results).
    Rejects explicitly Russian/Belarusian/Bulgarian videos; allows unknown language.
    """
    uk_keywords = _filter_ukrainian_keywords(keywords)
    if not uk_keywords:
        uk_keywords = keywords
    fetch_count = max_results * 3

    # Primary: channel-specific search via YouTube tab URL
    # Use ONLY the first keyword (module title) — additional keywords like
    # section titles ("Читання", "Вступ") are generic and kill channel search results
    from urllib.parse import quote
    short_query = uk_keywords[0][:60] if uk_keywords else ""
    channel_url = f"https://www.youtube.com/{channel_handle}/search?query={quote(short_query)}"
    videos = _yt_dlp_search(channel_url, fetch_count, max_results, flat_playlist=True)
    if videos:
        return videos

    # Fallback: global search with more keywords for context
    full_query = cap_query(uk_keywords)
    search_term = f"ytsearch{fetch_count}:{full_query}"
    return _yt_dlp_search(search_term, fetch_count, max_results, flat_playlist=False)


_RATE_LIMIT_PATTERNS = ("Connection reset by peer", "HTTP Error 429", "UNEXPECTED_EOF")


def _yt_dlp_search(
    search_term: str, fetch_count: int, max_results: int,
    *, flat_playlist: bool = False, _retry: int = 0,
) -> list[dict]:
    """Run yt-dlp search and parse results. Returns list of {url, title} dicts.

    Detects YouTube rate limiting (connection resets, 429s, SSL EOF) and
    backs off with increasing delays up to 2 retries.
    """
    cmd = ["yt-dlp", search_term, "--print", "%(title)s\t%(id)s\t%(language)s"]
    if flat_playlist:
        cmd += ["--flat-playlist", "--playlist-end", str(fetch_count)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        # Detect rate limiting in stderr even if returncode != 0
        stderr = result.stderr or ""
        if result.returncode != 0:
            if _retry < 2 and any(p in stderr for p in _RATE_LIMIT_PATTERNS):
                import time
                wait = 10 * (_retry + 1)  # 10s, 20s
                logger.info("YouTube rate limit detected, waiting %ds (retry %d/2)", wait, _retry + 1)
                time.sleep(wait)
                return _yt_dlp_search(search_term, fetch_count, max_results,
                                      flat_playlist=flat_playlist, _retry=_retry + 1)
            return []
        videos = []
        for line in result.stdout.strip().splitlines():
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            title, vid_id, lang = parts[0], parts[1], parts[2]
            if lang and lang.lower() in _REJECTED_LANGS:
                continue
            videos.append({
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "title": title,
            })
            if len(videos) >= max_results:
                break
        return videos
    except subprocess.TimeoutExpired:
        if _retry < 2:
            import time
            wait = 10 * (_retry + 1)
            logger.info("YouTube request timed out, waiting %ds (retry %d/2)", wait, _retry + 1)
            time.sleep(wait)
            return _yt_dlp_search(search_term, fetch_count, max_results,
                                  flat_playlist=flat_playlist, _retry=_retry + 1)
        return []
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Gemini scoring
# ---------------------------------------------------------------------------

def score_candidates(
    candidates: list[VideoCandidate],
    topic: str,
    outline: list[dict],
    vocab: list[str],
    dispatch_fn: Callable[..., tuple[bool, str]],
    model: str = "gemini-2.5-flash",
) -> list[VideoCandidate]:
    """Score candidates for relevance using Gemini Flash. Modifies in-place."""
    if not candidates:
        return candidates

    sections_str = ", ".join(
        s.get("section", s.get("title", ""))
        for s in outline if s.get("section") or s.get("title")
    ) or "(no outline)"
    vocab_str = ", ".join(vocab[:20]) if vocab else "(no vocab)"

    candidate_blocks = []
    for i, c in enumerate(candidates):
        excerpt = c.transcript[:2000] if c.transcript else "(no transcript)"
        candidate_blocks.append(
            f"### Candidate {i + 1}\n"
            f"- URL: {c.url}\n"
            f"- Title: {c.title}\n"
            f"- Channel: {c.channel}\n"
            f"- Transcript excerpt:\n{excerpt}\n"
        )

    prompt = (
        "# Video Discovery: Relevance Scoring\n\n"
        "## Module Context\n"
        f"Topic: {topic}\n"
        f"Sections: {sections_str}\n"
        f"Vocabulary: {vocab_str}\n\n"
        "## Candidates\n\n"
        + "\n".join(candidate_blocks)
        + "\n## Instructions\n\n"
        "Rate each candidate's TOPIC relevance to this specific module (0.0-1.0).\n\n"
        "Scoring guide:\n"
        "- 0.9-1.0: Video directly teaches or demonstrates the module's grammar/topic\n"
        "- 0.7-0.8: Video covers closely related material that reinforces the module\n"
        "- 0.4-0.6: Video is tangentially related (same domain but different focus)\n"
        "- 0.1-0.3: Video is in Ukrainian but unrelated to the module topic\n"
        "- 0.0: Completely irrelevant or wrong language\n\n"
        "IMPORTANT: A video being in Ukrainian or at the right level is NOT enough.\n"
        "The video must actually cover the MODULE TOPIC (grammar point, historical figure,\n"
        "cultural theme, etc.). A cooking video is irrelevant to a grammar module even\n"
        "if it's B1-level Ukrainian.\n\n"
        "For each, suggest where it could be embedded (after which section).\n"
        "Extract a short transcript excerpt (1-2 sentences) that's most relevant.\n\n"
        "## Output (between delimiters)\n\n"
        "===DISCOVERY_SCORES_START===\n"
        "- video_url: \"...\"\n"
        "  relevance_score: 0.0-1.0\n"
        "  relevance_note: \"...\"\n"
        "  embed_suggestion: \"After section X -- reason\"\n"
        "  transcript_excerpt: \"...\"\n"
        "===DISCOVERY_SCORES_END===\n"
    )

    try:
        ok, response = dispatch_fn(
            prompt,
            task_id="video-discovery-score",
            model=model,
            stdout_only=True,
            timeout=120,
        )
        if not ok:
            logger.warning("Gemini scoring failed")
            return candidates

        match = re.search(
            r"===DISCOVERY_SCORES_START===\s*(.*?)\s*===DISCOVERY_SCORES_END===",
            response,
            re.DOTALL,
        )
        if not match:
            logger.warning("Could not parse scoring response delimiters")
            return candidates

        try:
            scores = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            logger.warning("Could not parse YAML in scoring response")
            return candidates

        if not isinstance(scores, list):
            return candidates

        url_to_score = {
            entry.get("video_url", ""): entry
            for entry in scores if isinstance(entry, dict)
        }
        for c in candidates:
            entry = url_to_score.get(c.url, {})
            c.relevance_score = float(entry.get("relevance_score", 0.0))
            c.relevance_note = str(entry.get("relevance_note", ""))
            c.embed_suggestion = str(entry.get("embed_suggestion", ""))
            c.transcript_excerpt = str(entry.get("transcript_excerpt", ""))

    except Exception as e:
        logger.warning("Scoring failed: %s", e)

    return candidates


# ---------------------------------------------------------------------------
# Full discovery pipeline
# ---------------------------------------------------------------------------

def run_discovery(
    topic: str,
    keywords: list[str],
    outline: list[dict],
    vocab: list[str],
    dispatch_fn: Callable[..., tuple[bool, str]],
    track: str = "",
    channels: list[dict[str, Any]] | None = None,
    max_per_channel: int = 2,
) -> DiscoveryResult:
    """Search -> transcript -> score -> rank. Non-blocking: always returns a result."""
    result = DiscoveryResult(
        discovered_at=datetime.now(UTC).isoformat(),
        query_keywords=keywords,
    )

    try:
        channel_list = channels if channels is not None else DEFAULT_CHANNELS
        if track:
            channel_list = filter_channels(channel_list, track)
        if not channel_list:
            result.error = f"No channels match track '{track}'"
            return result

        all_candidates: list[VideoCandidate] = []
        seen_urls: set[str] = set()
        # Search track-specific channels first (filter_channels orders them),
        # cap total to avoid YouTube rate limiting in batch runs.
        max_channel_searches = 5
        target_videos = max_per_channel * 3  # stop early when we have enough
        searches_done = 0
        for ch in channel_list:
            if searches_done >= max_channel_searches:
                break
            if len(all_candidates) >= target_videos:
                break
            # Rate-limit: small delay between YouTube requests
            if searches_done > 0:
                import time
                time.sleep(1.5)
            videos = search_channel(keywords, ch["handle"], max_results=max_per_channel)
            searches_done += 1  # noqa: SIM113 — counter for rate-limiting, not loop index
            for v in videos:
                if v["url"] not in seen_urls:
                    seen_urls.add(v["url"])
                    all_candidates.append(VideoCandidate(
                        url=v["url"],
                        channel=ch["name"],
                        title=v["title"],
                    ))

        if not all_candidates:
            result.warning = "No videos found across channels"
            return result

        for c in all_candidates[:8]:
            c.transcript = download_transcript(c.url)

        with_text = [c for c in all_candidates if c.transcript]
        if with_text:
            score_candidates(with_text, topic, outline, vocab, dispatch_fn)

        all_candidates.sort(key=lambda c: c.relevance_score, reverse=True)
        result.videos = all_candidates

    except Exception as e:
        result.error = str(e)
        logger.warning("Discovery failed: %s", e)

    return result


# ---------------------------------------------------------------------------
# YAML serialization
# ---------------------------------------------------------------------------

def write_discovery_yaml(result: DiscoveryResult, path: Path) -> None:
    """Serialize DiscoveryResult to YAML."""
    data: dict[str, Any] = {
        "discovered_at": result.discovered_at,
        "query_keywords": result.query_keywords,
        "error": result.error,
        "warning": result.warning,
        "videos": [
            {
                "url": v.url,
                "channel": v.channel,
                "title": v.title,
                "relevance_score": v.relevance_score,
                "relevance_note": v.relevance_note,
                "transcript_excerpt": v.transcript_excerpt,
                "embed_suggestion": v.embed_suggestion,
            }
            for v in result.videos
        ],
        "blogs": result.blogs,
        "rag_chunks": result.rag_chunks,
        "rag_images": result.rag_images,
        "rag_literary": result.rag_literary,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def read_discovery_yaml(path: Path) -> DiscoveryResult:
    """Deserialize DiscoveryResult from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data:
        return DiscoveryResult()
    result = DiscoveryResult(
        discovered_at=data.get("discovered_at", ""),
        query_keywords=data.get("query_keywords", []),
        error=data.get("error"),
        blogs=data.get("blogs", []),
        rag_chunks=data.get("rag_chunks", []),
        rag_images=data.get("rag_images", []),
        rag_literary=data.get("rag_literary", []),
    )
    for v in data.get("videos", []):
        result.videos.append(VideoCandidate(
            url=v.get("url", ""),
            channel=v.get("channel", ""),
            title=v.get("title", ""),
            relevance_score=float(v.get("relevance_score", 0.0)),
            relevance_note=v.get("relevance_note", ""),
            transcript_excerpt=v.get("transcript_excerpt", ""),
            embed_suggestion=v.get("embed_suggestion", ""),
        ))
    return result


# ---------------------------------------------------------------------------
# Template formatting
# ---------------------------------------------------------------------------

def format_discovery_for_template(result: DiscoveryResult) -> str:
    """Format as markdown for {VIDEO_DISCOVERY} placeholder."""
    sections: list[str] = []

    relevant = [v for v in result.videos if v.relevance_score >= 0.5]
    if relevant:
        lines: list[str] = ["### Videos"]
        for v in relevant:
            lines.append(f"- **{v.title}** ({v.channel})")
            lines.append(f"  URL: {v.url}")
            lines.append(f"  Score: {v.relevance_score:.1f} -- {v.relevance_note}")
            if v.embed_suggestion:
                lines.append(f"  Suggested placement: {v.embed_suggestion}")
            if v.transcript_excerpt:
                lines.append(f"  Key excerpt: {v.transcript_excerpt}")
            lines.append("")
        sections.append("\n".join(lines))

    if result.blogs:
        sections.append(format_blog_discovery(result.blogs))

    if result.rag_chunks or result.rag_images or result.rag_literary:
        rag_text = format_rag_discovery(
            result.rag_chunks, result.rag_images, result.rag_literary,
        )
        if "(No RAG content found)" not in rag_text:
            sections.append(rag_text)

    if not sections:
        if result.error:
            return "(No discoveries available)"
        return "(No relevant resources found)"

    return "\n\n".join(sections)
