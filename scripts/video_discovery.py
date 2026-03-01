"""Video/blog discovery for the build pipeline.

Searches curated YouTube channels for relevant content, downloads transcripts,
and scores relevance using Gemini Flash. Non-blocking: all exceptions caught,
returns empty/default results on failure.

Used by phase_discover_v4() in build_module.py.
"""

from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

logger = logging.getLogger(__name__)

TRANSCRIPT_CAP = 50_000

# Channel allowlist — categorized by track relevance.
# tracks: ["*"] = all tracks, or specific track IDs.
DEFAULT_CHANNELS: list[dict[str, Any]] = [
    # Language learning (core A1-C2)
    {"name": "Anna Ohoiko", "handle": "@annaohoiko", "tracks": ["*"]},
    {"name": "Ukrainian with Olha", "handle": "@ukrainianwitholha", "tracks": ["*"]},
    {"name": "Let's Learn Ukrainian", "handle": "@LetsLearnUkrainian", "tracks": ["*"]},
    {"name": "Learn Ukrainian Language", "handle": "@LearnUkrainianLanguage", "tracks": ["*"]},
    {"name": "Listen & Read", "handle": "@listen-read", "tracks": ["*"]},
    {"name": "UkrainerNet", "handle": "@ukrainernet", "tracks": ["*"]},
    # History (HIST, ISTORIO, BIO)
    {"name": "Реальна Історія", "handle": "@realhistoryua", "tracks": ["hist", "istorio", "bio"]},
    {"name": "Harvard Ukrainian Research Institute", "handle": "@ukrainianresearchinstitute1041", "tracks": ["hist", "istorio", "bio", "lit"]},
    {"name": "Комік Історик", "handle": "@komikistoryk", "tracks": ["hist", "istorio", "bio"]},
    {"name": "ІМТГШ", "handle": "@imtgsh", "tracks": ["hist", "istorio"]},
    # Historical linguistics (OES, RUTH)
    {"name": "Історія Мови", "handle": "@Istoria-Movy", "tracks": ["oes", "ruth"]},
    # Culture & documentary (B2+, LIT, cultural modules)
    {"name": "Суспільне Культура", "handle": "@SuspilneKultura", "tracks": ["lit", "b2", "c1", "c2"]},
    {"name": "Суспільне Док", "handle": "@SuspilneDoc", "tracks": ["hist", "bio", "lit", "b2", "c1"]},
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
    blogs: list[dict] = field(default_factory=list)  # future
    error: str | None = None


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
    """Filter channel allowlist by track relevance."""
    base_track = track.split("-")[0].lower()
    return [
        ch for ch in channels
        if "*" in ch.get("tracks", [])
        or base_track in ch.get("tracks", [])
        or track.lower() in ch.get("tracks", [])
    ]


def search_channel(keywords: list[str], channel_handle: str, max_results: int = 3) -> list[dict]:
    """Search YouTube via yt-dlp for videos matching keywords on a channel."""
    query = " ".join(keywords)
    search_term = f"ytsearch{max_results}:{query} {channel_handle}"
    try:
        result = subprocess.run(
            ["yt-dlp", search_term, "--get-id", "--get-title"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return []
        lines = [ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()]
        # yt-dlp outputs title then id alternating
        videos = []
        for i in range(0, len(lines) - 1, 2):
            videos.append({
                "url": f"https://www.youtube.com/watch?v={lines[i + 1]}",
                "title": lines[i],
            })
        return videos
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
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
        "Rate each candidate's relevance to this module (0.0-1.0).\n"
        "For each, suggest where it could be embedded (after which section).\n"
        "Extract a short transcript excerpt (1-2 sentences) that's most relevant.\n\n"
        "## Output (between delimiters)\n\n"
        "===DISCOVERY_SCORES_START===\n"
        "- video_url: \"...\"\n"
        "  relevance_score: 0.0-1.0\n"
        "  relevance_note: \"...\"\n"
        "  embed_suggestion: \"After section X — reason\"\n"
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
    """Search → transcript → score → rank. Non-blocking: always returns a result."""
    result = DiscoveryResult(
        discovered_at=datetime.now(timezone.utc).isoformat(),
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
        for ch in channel_list:
            videos = search_channel(keywords, ch["handle"], max_results=max_per_channel)
            for v in videos:
                if v["url"] not in seen_urls:
                    seen_urls.add(v["url"])
                    all_candidates.append(VideoCandidate(
                        url=v["url"],
                        channel=ch["name"],
                        title=v["title"],
                    ))

        if not all_candidates:
            result.error = "No videos found across channels"
            return result

        # Download transcripts (cap at 8 to limit network time)
        for c in all_candidates[:8]:
            c.transcript = download_transcript(c.url)

        # Score candidates that have transcripts
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
    if result.error and not result.videos:
        return "(No video discoveries available)"

    relevant = [v for v in result.videos if v.relevance_score >= 0.5]
    if not relevant:
        return "(No relevant videos found)"

    lines: list[str] = []
    for v in relevant:
        lines.append(f"- **{v.title}** ({v.channel})")
        lines.append(f"  URL: {v.url}")
        lines.append(f"  Score: {v.relevance_score:.1f} — {v.relevance_note}")
        if v.embed_suggestion:
            lines.append(f"  Suggested placement: {v.embed_suggestion}")
        if v.transcript_excerpt:
            lines.append(f"  Key excerpt: {v.transcript_excerpt}")
        lines.append("")
    return "\n".join(lines)
