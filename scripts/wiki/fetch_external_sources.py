#!/usr/bin/env python3
"""Fetch and cache external sources for wiki enrichment.

One-time ingestion: fetches ULP blog articles, YouTube subtitles, and other
external articles. Caches to `data/external_articles/` as JSONL files.

JSONL schemas:
- Blog article caches keep the existing shape:
  `url, title, domain, text, char_count`
- YouTube caches write the richer channel/video shape required by #1324:
  `video_id, channel_id, speaker, publish_date, duration_s, url, title,
   description, subtitles`
  and also preserve legacy compatibility fields `text` and `char_count`
  derived from `subtitles`, so existing DB ingestion keeps working.

Usage:
    .venv/bin/python scripts/wiki/fetch_external_sources.py --ulp-blogs
    .venv/bin/python scripts/wiki/fetch_external_sources.py --other-blogs
    .venv/bin/python scripts/wiki/fetch_external_sources.py --channel-name realna-istoria
    .venv/bin/python scripts/wiki/fetch_external_sources.py --channel https://www.youtube.com/@SomeChannel
    .venv/bin/python scripts/wiki/fetch_external_sources.py --status
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import socket
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "external_articles"
EXT_RESOURCES = PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

# Rate limiting — requested in #1151.
BLOG_DELAY = 1.5
YOUTUBE_DELAY = 5.0
YOUTUBE_BATCH_PAUSE = 30.0
YOUTUBE_BATCH_SIZE = 20

# Tor proxy settings — password from env or torrc (local-only control port)
TOR_SOCKS_PROXY = "socks5://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = os.environ.get("TOR_CONTROL_PASSWORD", "")
COOKIE_FILE = Path("/tmp/yt-cookies.txt")
MAX_429_RETRIES = 3

YOUTUBE_SUBTITLE_LANGS = ("uk", "en")
YOUTUBE_STATUS_FILENAMES = ("ulp_blogs.jsonl", "other_blogs.jsonl")
YOUTUBE_RECORD_FIELDS = (
    "video_id",
    "channel_id",
    "speaker",
    "publish_date",
    "duration_s",
    "url",
    "title",
    "description",
    "subtitles",
)


@dataclass(frozen=True)
class YouTubeChannel:
    """Resolved YouTube channel scrape target."""

    key: str
    url: str
    output_filename: str
    speaker: str
    description: str

    @property
    def output_path(self) -> Path:
        return CACHE_DIR / self.output_filename

    @property
    def playlist_url(self) -> str:
        return normalize_channel_url(self.url, videos_tab=True)


YOUTUBE_CHANNELS: dict[str, YouTubeChannel] = {
    "ukrainian-lessons": YouTubeChannel(
        key="ukrainian-lessons",
        url="https://www.youtube.com/@UkrainianLessons",
        output_filename="ulp_youtube.jsonl",
        speaker="Anna Ohoiko",
        description="Ukrainian Lessons (Anna Ohoiko) — A1-B2 pedagogy, FMU, podcasts",
    ),
    "realna-istoria": YouTubeChannel(
        key="realna-istoria",
        url="https://www.youtube.com/@RealnaIstoria",
        output_filename="realna_istoria.jsonl",
        speaker="Akím Galímov",
        description="Реальна Історія — HIST, BIO, ISTORIO",
    ),
    "imtgsh": YouTubeChannel(
        key="imtgsh",
        url="https://www.youtube.com/@imtgsh",
        output_filename="imtgsh.jsonl",
        speaker="",
        description="imtgsh — history content",
    ),
    "istoria-movy": YouTubeChannel(
        key="istoria-movy",
        url="https://www.youtube.com/@Istoria-Movy",
        output_filename="istoria_movy.jsonl",
        speaker="",
        description="Istoria-Movy — history of Ukrainian language",
    ),
    "speak-ukrainian": YouTubeChannel(
        key="speak-ukrainian",
        url="https://www.youtube.com/@SpeakUkrainian",
        output_filename="speak_ukrainian.jsonl",
        speaker="",
        description="Speak Ukrainian — A1-A2 pedagogy",
    ),
    "red-purple": YouTubeChannel(
        key="red-purple",
        url="https://www.youtube.com/@RedPurpleUkrainian",
        output_filename="red_purple.jsonl",
        speaker="",
        description="Red Purple Ukrainian — A1 pedagogy",
    ),
}

LEGACY_CHANNEL_FLAGS = {
    "ulp": "ukrainian-lessons",
}


def load_external_urls() -> dict[str, list[str]]:
    """Extract unique URLs from external_resources.yaml, grouped by type."""
    with open(EXT_RESOURCES, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    resources = data.get("resources", {})
    ulp_blogs: set[str] = set()
    other_blogs: set[str] = set()
    youtube: set[str] = set()

    for entry in resources.values():
        for art in entry.get("articles", []):
            url = art.get("url", "").strip()
            if not url:
                continue
            if "ukrainianlessons" in url:
                ulp_blogs.add(url)
            else:
                other_blogs.add(url)
        for vid in entry.get("youtube", []):
            url = vid.get("url", "").strip()
            if url:
                youtube.add(url)

    return {
        "ulp_blogs": sorted(ulp_blogs),
        "other_blogs": sorted(other_blogs),
        "youtube": sorted(youtube),
    }


# ── Blog article fetching ─────────────────────────────────────


def fetch_blog_article(url: str) -> dict[str, Any] | None:
    """Fetch a blog article and extract clean text content."""
    try:
        resp = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (learn-ukrainian curriculum project)"},
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"  ❌ {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.find("div", class_="entry-content")
    content = article if article else soup
    text = content.get_text(separator="\n", strip=True)

    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)

    if len(text) < 50:
        print(f"  ⚠️  Too short ({len(text)} chars): {url}")
        return None

    title = ""
    title_tag = soup.find("h1") or soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    domain = urlparse(url).netloc.replace("www.", "")

    return {
        "url": url,
        "title": title,
        "domain": domain,
        "text": text[:10000],
        "char_count": len(text),
    }


def fetch_blogs(urls: list[str], output_file: Path) -> None:
    """Fetch blog articles and save as JSONL."""
    existing_urls: set[str] = set()
    if output_file.exists():
        with open(output_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    existing_urls.add(entry.get("url", ""))

    new_count = 0
    skip_count = 0
    fail_count = 0

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "a", encoding="utf-8") as f:
        for i, url in enumerate(urls, start=1):
            if url in existing_urls:
                skip_count += 1
                continue

            print(f"  [{i}/{len(urls)}] {url[:80]}")
            article = fetch_blog_article(url)
            if article:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")
                f.flush()
                new_count += 1
            else:
                fail_count += 1

            time.sleep(BLOG_DELAY)

    print(f"\n  ✅ Fetched: {new_count} | ⏭️  Skipped: {skip_count} | ❌ Failed: {fail_count}")
    print(f"  📄 {output_file}")


# ── YouTube subtitle fetching ─────────────────────────────────


class YouTubeRequestLimiter:
    """Enforce spacing between yt-dlp requests and longer batch pauses."""

    def __init__(
        self,
        *,
        request_delay: float = YOUTUBE_DELAY,
        batch_size: int = YOUTUBE_BATCH_SIZE,
        batch_pause: float = YOUTUBE_BATCH_PAUSE,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.request_delay = request_delay
        self.batch_size = batch_size
        self.batch_pause = batch_pause
        self.sleep_fn = sleep_fn
        self.request_count = 0

    def before_request(self, label: str) -> None:
        """Pause between yt-dlp requests so reruns behave politely."""
        if self.request_count > 0:
            print(f"  ⏱️  Waiting {self.request_delay:.0f}s before {label}...")
            self.sleep_fn(self.request_delay)
        self.request_count += 1

    def after_video(self, processed_videos: int) -> None:
        """Pause every N processed videos and log it."""
        if processed_videos > 0 and processed_videos % self.batch_size == 0:
            print(
                "  ⏳ Batch pause "
                f"({self.batch_pause:.0f}s after {processed_videos} processed videos)..."
            )
            self.sleep_fn(self.batch_pause)


def normalize_channel_url(channel_url: str, *, videos_tab: bool = False) -> str:
    """Normalize a YouTube channel URL for matching or playlist scraping."""
    normalized = channel_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("Channel URL cannot be empty")

    parsed = urlparse(normalized)
    if parsed.netloc not in {"youtube.com", "www.youtube.com"}:
        return normalized

    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[-1] == "videos":
        return normalized
    if videos_tab:
        return f"{normalized}/videos"
    return normalized


def resolve_named_channel(channel_name: str) -> YouTubeChannel:
    """Resolve a registry-backed channel name to a scrape target."""
    if channel_name in YOUTUBE_CHANNELS:
        return YOUTUBE_CHANNELS[channel_name]

    known = ", ".join(sorted(YOUTUBE_CHANNELS))
    raise ValueError(f"Unknown channel-name '{channel_name}'. Available: {known}")


def infer_channel_output_filename(channel_url: str) -> str:
    """Infer an output filename for an arbitrary YouTube channel URL."""
    normalized = normalize_channel_url(channel_url)
    for channel in YOUTUBE_CHANNELS.values():
        if normalize_channel_url(channel.url) == normalized:
            return channel.output_filename

    parsed = urlparse(normalized)
    parts = [part for part in parsed.path.split("/") if part]
    candidates = [part for part in parts if part not in {"videos", "featured", "playlists", "shorts"}]
    token = candidates[-1] if candidates else parsed.netloc
    token = token.lstrip("@")
    token = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", token)
    token = re.sub(r"[^a-zA-Z0-9]+", "_", token).strip("_").lower()
    if not token:
        raise ValueError(f"Could not infer output filename from channel URL '{channel_url}'")
    return f"{token}.jsonl"


def make_ad_hoc_channel(channel_url: str, output_name: str | None) -> YouTubeChannel:
    """Create a scrape target for `--channel` without mutating the registry."""
    output_filename = output_name or infer_channel_output_filename(channel_url)
    if not output_filename.endswith(".jsonl"):
        output_filename = f"{output_filename}.jsonl"
    key = Path(output_filename).stem.replace("_", "-")
    return YouTubeChannel(
        key=key,
        url=normalize_channel_url(channel_url),
        output_filename=output_filename,
        speaker="",
        description=f"Ad-hoc channel scrape: {channel_url}",
    )


def _extract_video_id(video_url: str) -> str:
    """Extract video ID from a YouTube URL."""
    if "v=" in video_url:
        return video_url.split("v=")[1].split("&")[0]
    if "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[1].split("?")[0]
    return ""


def load_existing_video_ids(output_file: Path) -> set[str]:
    """Read already-written video IDs so channel reruns resume instead of restart."""
    existing_ids: set[str] = set()
    if not output_file.exists():
        return existing_ids

    with open(output_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            video_id = str(entry.get("video_id", "")).strip()
            if video_id:
                existing_ids.add(video_id)
    return existing_ids


def _yt_dlp_base_cmd(use_tor: bool) -> list[str]:
    """Build the shared yt-dlp invocation using the repo venv explicitly."""
    cmd = [str(VENV_PYTHON), "-m", "yt_dlp"]
    if use_tor:
        cookie_file = _ensure_cookie_file()
        cmd.extend(["--proxy", TOR_SOCKS_PROXY, "--cookies", str(cookie_file)])
    else:
        cmd.extend(["--cookies-from-browser", "chrome"])
    return cmd


def _run_yt_dlp(
    args: list[str],
    *,
    limiter: YouTubeRequestLimiter,
    label: str,
    timeout: int,
    use_tor: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run yt-dlp with the shared rate limiter."""
    limiter.before_request(label)
    cmd = _yt_dlp_base_cmd(use_tor) + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def get_channel_video_urls(
    channel_url: str,
    *,
    limiter: YouTubeRequestLimiter,
    max_videos: int = 500,
) -> list[str]:
    """Get video URLs from a YouTube channel using yt-dlp flat-playlist mode."""
    playlist_url = normalize_channel_url(channel_url, videos_tab=True)
    print(f"  📡 Scraping channel: {playlist_url}")
    try:
        result = _run_yt_dlp(
            [
                "--flat-playlist",
                "--print",
                "url",
                "--playlist-end",
                str(max_videos),
                playlist_url,
            ],
            limiter=limiter,
            label="channel inventory",
            timeout=120,
        )
    except Exception as e:
        print(f"  ❌ Channel scrape failed: {e}")
        return []

    if result.returncode != 0:
        stderr = result.stderr.strip()
        print(f"  ❌ Channel scrape failed: {stderr or 'yt-dlp returned non-zero'}")
        return []

    urls = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    print(f"  📺 Found {len(urls)} videos")
    return urls


def _tor_is_running() -> bool:
    """Check if Tor SOCKS proxy is accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(("127.0.0.1", 9050))
        sock.close()
        return True
    except OSError:
        return False


def _tor_new_circuit() -> bool:
    """Request a new Tor circuit via the control port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("127.0.0.1", TOR_CONTROL_PORT))
        sock.recv(1024)

        sock.sendall(f'AUTHENTICATE "{TOR_CONTROL_PASSWORD}"\r\n'.encode())
        resp = sock.recv(1024).decode()
        if "250 OK" not in resp:
            print(f"    ⚠️  Tor auth failed: {resp.strip()}")
            sock.close()
            return False

        sock.sendall(b"SIGNAL NEWNYM\r\n")
        resp = sock.recv(1024).decode()
        sock.close()

        if "250 OK" in resp:
            print("    🔄 New Tor circuit requested, waiting 10s...")
            time.sleep(10)
            return True

        print(f"    ⚠️  Tor NEWNYM failed: {resp.strip()}")
        return False
    except Exception as e:
        print(f"    ⚠️  Tor control error: {e}")
        return False


def _ensure_cookie_file() -> Path:
    """Export Chrome YouTube cookies to a Netscape cookie file for Tor use."""
    if COOKIE_FILE.exists():
        age = time.time() - COOKIE_FILE.stat().st_mtime
        if age < 3600:
            return COOKIE_FILE

    try:
        from pycookiecheat import chrome_cookies

        cookies = chrome_cookies("https://www.youtube.com")
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for name, value in cookies.items():
                f.write(f".youtube.com\tTRUE\t/\tTRUE\t0\t{name}\t{value}\n")
        print(f"  🍪 Exported {len(cookies)} YouTube cookies")
    except Exception as e:
        print(f"  ⚠️  Cookie export failed: {e}")

    return COOKIE_FILE


def _parse_vtt(vtt_text: str) -> str:
    """Parse VTT subtitle content into plain text."""
    lines = []
    for line in vtt_text.split("\n"):
        line = line.strip()
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or line.startswith("NOTE")
            or re.match(r"^\d{2}:\d{2}", line)
            or re.match(r"^\d+$", line)
        ):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line)
        line = re.sub(r"^>>+\s*", "", line)
        if line:
            lines.append(line)

    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    text = " ".join(deduped)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_video_metadata(
    video_url: str,
    *,
    limiter: YouTubeRequestLimiter,
    use_tor: bool,
) -> dict[str, Any] | None:
    """Fetch YouTube metadata needed for the cached JSONL schema."""
    try:
        result = _run_yt_dlp(
            ["--dump-single-json", "--no-download", "--no-warnings", video_url],
            limiter=limiter,
            label="video metadata",
            timeout=60,
            use_tor=use_tor,
        )
    except Exception as e:
        print(f"    ❌ Metadata fetch failed: {e}")
        return None

    if result.returncode != 0 or not result.stdout.strip():
        stderr = result.stderr.strip()
        if stderr:
            print(f"    ❌ Metadata fetch failed: {stderr}")
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"    ❌ Metadata parse failed: {e}")
        return None


def _download_subtitle_text(
    video_id: str,
    *,
    limiter: YouTubeRequestLimiter,
    use_tor: bool,
) -> str:
    """Download subtitles via yt-dlp and return normalized plain text."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = str(Path(tmpdir) / "%(id)s.%(ext)s")
        for lang in YOUTUBE_SUBTITLE_LANGS:
            for attempt in range(MAX_429_RETRIES + 1):
                sub_file = Path(tmpdir) / f"{video_id}.{lang}.vtt"
                if sub_file.exists():
                    sub_file.unlink()

                try:
                    result = _run_yt_dlp(
                        [
                            "--write-sub",
                            "--write-auto-sub",
                            "--sub-lang",
                            lang,
                            "--sub-format",
                            "vtt",
                            "--skip-download",
                            "--no-warnings",
                            "-o",
                            output_template,
                            f"https://www.youtube.com/watch?v={video_id}",
                        ],
                        limiter=limiter,
                        label=f"subtitle fetch ({lang})",
                        timeout=90,
                        use_tor=use_tor,
                    )
                except subprocess.TimeoutExpired:
                    print(f"    ⏱️  Timeout fetching subs ({lang})")
                    break
                except Exception as e:
                    print(f"    ❌ yt-dlp error ({lang}): {e}")
                    break

                if sub_file.exists():
                    text = _parse_vtt(sub_file.read_text(encoding="utf-8"))
                    if len(text) >= 30:
                        return text
                    break

                is_429 = "429" in (result.stderr or "")
                if is_429 and use_tor and attempt < MAX_429_RETRIES:
                    print(f"    🚫 429 on {lang} (attempt {attempt + 1}/{MAX_429_RETRIES})")
                    _tor_new_circuit()
                    continue

                if is_429 and not use_tor:
                    print("    🚫 429 — start Tor for auto-rotation: tor &")
                break

    return ""


def _format_publish_date(raw_date: Any) -> str:
    """Normalize a yt-dlp upload date to ISO 8601 date form."""
    value = str(raw_date or "").strip()
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return value


def build_youtube_record(
    *,
    channel: YouTubeChannel,
    video_url: str,
    metadata: dict[str, Any],
    subtitles: str,
) -> dict[str, Any]:
    """Build a cached YouTube JSONL record, including compatibility fields."""
    video_id = str(metadata.get("id") or _extract_video_id(video_url)).strip()
    title = str(metadata.get("title", "")).strip()
    description = str(metadata.get("description", "") or "").strip()
    duration = metadata.get("duration") or 0
    try:
        duration_s = int(duration)
    except (TypeError, ValueError):
        duration_s = 0

    record = {
        "video_id": video_id,
        "channel_id": channel.key,
        "speaker": channel.speaker,
        "publish_date": _format_publish_date(
            metadata.get("upload_date") or metadata.get("release_date")
        ),
        "duration_s": duration_s,
        "url": str(metadata.get("webpage_url") or video_url).strip(),
        "title": title,
        "description": description,
        "subtitles": subtitles,
        "text": subtitles,
        "char_count": len(subtitles),
    }
    return record


def fetch_youtube_video(
    video_url: str,
    *,
    channel: YouTubeChannel,
    limiter: YouTubeRequestLimiter,
) -> dict[str, Any] | None:
    """Fetch metadata + subtitles for a single YouTube video."""
    video_id = _extract_video_id(video_url)
    if not video_id:
        return None

    use_tor = _tor_is_running()
    metadata = _fetch_video_metadata(video_url, limiter=limiter, use_tor=use_tor)
    if not metadata:
        return None

    subtitles = _download_subtitle_text(video_id, limiter=limiter, use_tor=use_tor)
    if not subtitles:
        return None

    return build_youtube_record(
        channel=channel,
        video_url=video_url,
        metadata=metadata,
        subtitles=subtitles,
    )


def fetch_youtube_subtitles(
    video_urls: list[str],
    *,
    channel: YouTubeChannel,
    output_file: Path,
    limiter: YouTubeRequestLimiter,
    fetcher: Callable[..., dict[str, Any] | None] = fetch_youtube_video,
) -> None:
    """Fetch subtitles for YouTube videos and save as JSONL with resume support."""
    existing_ids = load_existing_video_ids(output_file)

    new_count = 0
    skip_count = 0
    fail_count = 0
    processed_videos = 0

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "a", encoding="utf-8") as f:
        for index, url in enumerate(video_urls, start=1):
            video_id = _extract_video_id(url)
            if video_id in existing_ids:
                skip_count += 1
                continue

            print(f"  [{index}/{len(video_urls)}] {url}")
            record = fetcher(url, channel=channel, limiter=limiter)
            processed_videos += 1

            if record:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                existing_ids.add(record["video_id"])
                new_count += 1
                print(f"    ✅ {record['title'][:60]} ({record['char_count']} chars)")
            else:
                fail_count += 1
                print("    ⚠️  No subtitles found")

            limiter.after_video(processed_videos)

    print(f"\n  ✅ Fetched: {new_count} | ⏭️  Skipped: {skip_count} | ❌ No subs: {fail_count}")
    print(f"  📄 {output_file}")


# ── Status ────────────────────────────────────────────────────


def jsonl_inventory(path: Path) -> tuple[bool, int, int]:
    """Return presence, size, and record count for a JSONL cache file."""
    if not path.exists():
        return False, 0, 0

    with open(path, encoding="utf-8") as fh:
        count = sum(1 for line in fh if line.strip())
    return True, path.stat().st_size, count


def render_status(cache_dir: Path = CACHE_DIR) -> str:
    """Render a human-readable inventory of cached external sources."""
    lines = ["", "📊 External Sources Cache Status", "─" * 70]

    lines.append("Blog inventories:")
    for name in YOUTUBE_STATUS_FILENAMES:
        present, size, count = jsonl_inventory(cache_dir / name)
        if present:
            lines.append(f"  {name}: present=yes | size={size:,} bytes | records={count}")
        else:
            lines.append(f"  {name}: present=no | size=0 bytes | records=0")

    lines.append("")
    lines.append("Registered YouTube channels:")
    for channel in YOUTUBE_CHANNELS.values():
        present, size, count = jsonl_inventory(cache_dir / channel.output_filename)
        present_flag = "yes" if present else "no"
        lines.append(
            "  "
            f"{channel.key}: file={channel.output_filename} | present={present_flag} "
            f"| size={size:,} bytes | records={count}"
        )

    urls = load_external_urls()
    lines.append("")
    lines.append("URLs in external_resources.yaml:")
    lines.append(f"  ULP blogs: {len(urls['ulp_blogs'])}")
    lines.append(f"  Other blogs: {len(urls['other_blogs'])}")
    lines.append(f"  YouTube (from resources): {len(urls['youtube'])}")
    return "\n".join(lines)


def show_status() -> None:
    """Print the cache inventory report."""
    print(render_status())


# ── CLI ───────────────────────────────────────────────────────


def _fetch_channel(channel: YouTubeChannel) -> None:
    """Scrape a single YouTube channel and fetch subtitles."""
    print(f"\n📺 {channel.description}")
    limiter = YouTubeRequestLimiter()
    video_urls = get_channel_video_urls(channel.playlist_url, limiter=limiter)
    if not video_urls:
        print(f"  ❌ Channel scrape failed for {channel.key}")
        return

    fetch_youtube_subtitles(
        video_urls,
        channel=channel,
        output_file=channel.output_path,
        limiter=limiter,
    )


def _selected_channels(args: argparse.Namespace) -> list[YouTubeChannel]:
    """Resolve all YouTube channel requests from parsed CLI args."""
    selected: list[YouTubeChannel] = []
    seen_keys: set[str] = set()

    if args.channel_name:
        channel = resolve_named_channel(args.channel_name)
        selected.append(channel)
        seen_keys.add(channel.key)

    if args.channel:
        channel = make_ad_hoc_channel(args.channel, args.out)
        if channel.key not in seen_keys:
            selected.append(channel)
            seen_keys.add(channel.key)

    for key in YOUTUBE_CHANNELS:
        attr = f"yt_{key.replace('-', '_')}"
        if getattr(args, attr):
            channel = YOUTUBE_CHANNELS[key]
            if channel.key not in seen_keys:
                selected.append(channel)
                seen_keys.add(channel.key)

    for legacy_flag, key in LEGACY_CHANNEL_FLAGS.items():
        attr = f"yt_{legacy_flag.replace('-', '_')}"
        if getattr(args, attr):
            channel = YOUTUBE_CHANNELS[key]
            if channel.key not in seen_keys:
                selected.append(channel)
                seen_keys.add(channel.key)

    if args.all_youtube or args.all:
        for channel in YOUTUBE_CHANNELS.values():
            if channel.key not in seen_keys:
                selected.append(channel)
                seen_keys.add(channel.key)

    return selected


def main() -> None:
    channel_names = "\n".join(
        f"  {channel.key:<20s} {channel.output_filename:<24s} {channel.description}"
        for channel in YOUTUBE_CHANNELS.values()
    )
    parser = argparse.ArgumentParser(
        description="Fetch external sources for wiki enrichment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Registered YouTube channels:\n" + channel_names,
    )
    parser.add_argument("--ulp-blogs", action="store_true", help="Fetch ULP blog articles")
    parser.add_argument("--other-blogs", action="store_true", help="Fetch non-ULP articles")
    parser.add_argument("--all-blogs", action="store_true", help="Fetch all blog articles")

    parser.add_argument("--channel-name", help="Fetch a registered YouTube channel by registry key")
    parser.add_argument("--channel", help="Fetch an arbitrary YouTube channel URL")
    parser.add_argument("--out", help="Output filename for --channel (defaults to URL-derived name)")
    parser.add_argument("--all-youtube", action="store_true", help="Fetch all registered YouTube channels")

    for key, channel in YOUTUBE_CHANNELS.items():
        parser.add_argument(f"--yt-{key}", action="store_true", help=f"Fetch {channel.description}")
    for legacy_flag, key in LEGACY_CHANNEL_FLAGS.items():
        parser.add_argument(
            f"--yt-{legacy_flag}",
            action="store_true",
            help=f"Legacy alias for --channel-name {key}",
        )

    parser.add_argument("--all", action="store_true", help="Fetch everything + rebuild DB")
    parser.add_argument("--build-db", action="store_true", help="Rebuild SQLite FTS5 sources database")
    parser.add_argument("--status", action="store_true", help="Show cache status")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Copy data/external_articles/ to Google Drive, delete local",
    )
    args = parser.parse_args()

    if args.out and not args.channel:
        parser.error("--out requires --channel")

    if args.status:
        show_status()
        return

    if args.backup:
        _backup_to_gdrive()
        return

    if args.build_db:
        from wiki.build_sources_db import build

        build()
        return

    try:
        channels = _selected_channels(args)
    except ValueError as e:
        parser.error(str(e))

    fetch_requested = any(
        [
            args.ulp_blogs,
            args.other_blogs,
            args.all_blogs,
            args.all_youtube,
            args.all,
            bool(channels),
        ]
    )
    if not fetch_requested:
        parser.error("Specify what to fetch (use --help to see options)")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    urls = load_external_urls()

    if args.ulp_blogs or args.all_blogs or args.all:
        print(f"\n🌐 Fetching {len(urls['ulp_blogs'])} ULP blog articles...")
        fetch_blogs(urls["ulp_blogs"], CACHE_DIR / "ulp_blogs.jsonl")

    if args.other_blogs or args.all_blogs or args.all:
        print(f"\n🌐 Fetching {len(urls['other_blogs'])} other blog articles...")
        fetch_blogs(urls["other_blogs"], CACHE_DIR / "other_blogs.jsonl")

    for channel in channels:
        _fetch_channel(channel)

    show_status()

    if args.all:
        print("\n🔨 Rebuilding sources database...")
        from wiki.build_sources_db import build

        build()


def _backup_to_gdrive() -> None:
    """Copy cached external articles to Google Drive, then delete local copies."""
    import shutil

    gdrive_target = Path.home() / (
        "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com"
        "/My Drive/Projects/learn-ukrainian-data/external_articles"
    )

    if not CACHE_DIR.exists():
        print("❌ Nothing to back up — data/external_articles/ doesn't exist")
        return

    files = list(CACHE_DIR.glob("*.jsonl"))
    if not files:
        print("❌ No JSONL files to back up")
        return

    print(f"\n📦 Backing up {len(files)} files to Google Drive...")
    gdrive_target.mkdir(parents=True, exist_ok=True)

    for file_path in files:
        dest = gdrive_target / file_path.name
        shutil.copy2(file_path, dest)
        size = file_path.stat().st_size
        print(f"  ✅ {file_path.name} ({size:,} bytes) → Google Drive")

    print("\n🗑️  Deleting local copies...")
    for file_path in files:
        file_path.unlink()
        print(f"  🗑️  {file_path.name}")

    print("\n✅ Backup complete. Files on Google Drive at:")
    print(f"   {gdrive_target}")


if __name__ == "__main__":
    main()
