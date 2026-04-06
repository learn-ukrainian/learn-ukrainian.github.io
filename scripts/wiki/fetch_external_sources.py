#!/usr/bin/env python3
"""Fetch and cache external sources for wiki enrichment.

One-time ingestion: fetches ULP blog articles, YouTube subtitles, and other
external articles. Caches to data/external_articles/ as JSONL files.
The enrichment step reads from cache — no fetching during compilation.

Usage:
    # Fetch all ULP blog articles (243 URLs)
    .venv/bin/python scripts/wiki/fetch_external_sources.py --ulp-blogs

    # Fetch ALL ULP YouTube subtitles (channel scrape)
    .venv/bin/python scripts/wiki/fetch_external_sources.py --ulp-youtube

    # Fetch other external articles (Dobra Forma, etc.)
    .venv/bin/python scripts/wiki/fetch_external_sources.py --other-blogs

    # Fetch everything
    .venv/bin/python scripts/wiki/fetch_external_sources.py --all

    # Check what we have cached
    .venv/bin/python scripts/wiki/fetch_external_sources.py --status
"""

import argparse
import html
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "external_articles"
EXT_RESOURCES = PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"

# Rate limiting — YouTube is aggressive about rate limiting
BLOG_DELAY = 1.5        # seconds between blog requests
YOUTUBE_DELAY = 10.0    # seconds between YouTube requests
YOUTUBE_BATCH_PAUSE = 90  # pause every N videos to avoid rate limit
YOUTUBE_BATCH_SIZE = 10

# Tor proxy settings — password from env or torrc (local-only control port)
TOR_SOCKS_PROXY = "socks5://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = os.environ.get("TOR_CONTROL_PASSWORD", "")
COOKIE_FILE = Path("/tmp/yt-cookies.txt")
MAX_429_RETRIES = 3  # rotate circuit up to 3 times per video


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


def fetch_blog_article(url: str) -> dict | None:
    """Fetch a blog article and extract clean text content."""
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (learn-ukrainian curriculum project)"
        })
        resp.raise_for_status()
    except Exception as e:
        print(f"  ❌ {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove scripts, styles, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try to find article content (most blogs use <article> or main content div)
    article = soup.find("article") or soup.find("main") or soup.find("div", class_="entry-content")
    content = article if article else soup
    text = content.get_text(separator="\n", strip=True)

    # Clean up: collapse blank lines, strip
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
        "text": text[:10000],  # Cap at 10K chars per article
        "char_count": len(text),
    }


def fetch_blogs(urls: list[str], output_file: Path) -> None:
    """Fetch blog articles and save as JSONL."""
    # Load existing to skip already-fetched
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
        for i, url in enumerate(urls):
            if url in existing_urls:
                skip_count += 1
                continue

            print(f"  [{i+1}/{len(urls)}] {url[:80]}")
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


def get_channel_video_urls(channel_url: str, max_videos: int = 500) -> list[str]:
    """Get all video URLs from a YouTube channel using yt-dlp."""
    print(f"  📡 Scraping channel: {channel_url}")
    try:
        result = subprocess.run(
            [
                "yt-dlp", "--flat-playlist", "--print", "url",
                "--playlist-end", str(max_videos),
                channel_url,
            ],
            capture_output=True, text=True, timeout=120,
        )
        urls = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        print(f"  📺 Found {len(urls)} videos")
        return urls
    except Exception as e:
        print(f"  ❌ Channel scrape failed: {e}")
        return []


def _extract_video_id(video_url: str) -> str:
    """Extract video ID from a YouTube URL."""
    if "v=" in video_url:
        return video_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[1].split("?")[0]
    return ""


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
    """Request a new Tor circuit via the control port.

    Sends SIGNAL NEWNYM to get a fresh exit node (= new IP).
    Waits 10s for the circuit to establish.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("127.0.0.1", TOR_CONTROL_PORT))

        # Read banner
        sock.recv(1024)

        # Authenticate
        sock.sendall(f'AUTHENTICATE "{TOR_CONTROL_PASSWORD}"\r\n'.encode())
        resp = sock.recv(1024).decode()
        if "250 OK" not in resp:
            print(f"    ⚠️  Tor auth failed: {resp.strip()}")
            sock.close()
            return False

        # Request new circuit
        sock.sendall(b"SIGNAL NEWNYM\r\n")
        resp = sock.recv(1024).decode()
        sock.close()

        if "250 OK" in resp:
            print("    🔄 New Tor circuit requested, waiting 10s...")
            time.sleep(10)
            return True
        else:
            print(f"    ⚠️  Tor NEWNYM failed: {resp.strip()}")
            return False
    except Exception as e:
        print(f"    ⚠️  Tor control error: {e}")
        return False


def _ensure_cookie_file() -> Path:
    """Export Chrome YouTube cookies to a Netscape cookie file for Tor use.

    Cookies authenticate us as a real YouTube user when routing through Tor,
    since Tor exit nodes are flagged by YouTube's bot detection.
    """
    if COOKIE_FILE.exists():
        # Refresh if older than 1 hour
        age = time.time() - COOKIE_FILE.stat().st_mtime
        if age < 3600:
            return COOKIE_FILE

    try:
        from pycookiecheat import chrome_cookies
        cookies = chrome_cookies("https://www.youtube.com")
        with open(COOKIE_FILE, "w") as f:
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
        # Skip VTT header, timestamps, empty lines, NOTE blocks, position hints
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") \
                or line.startswith("Language:") or line.startswith("NOTE") \
                or re.match(r"^\d{2}:\d{2}", line) or re.match(r"^\d+$", line):
            continue
        # Strip VTT tags like <c> </c> <00:00:01.234>
        line = re.sub(r"<[^>]+>", "", line)
        # Decode HTML entities (&gt; &amp; etc.)
        line = html.unescape(line)
        # Strip >> speaker indicators
        line = re.sub(r"^>>+\s*", "", line)
        if line:
            lines.append(line)

    # Deduplicate consecutive identical lines (VTT repeats lines across cues)
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    text = " ".join(deduped)
    # Remove [Music], [Applause] etc.
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _yt_dlp_fetch_sub(video_id: str, lang: str, tmpdir: str,
                       use_tor: bool) -> subprocess.CompletedProcess:
    """Run yt-dlp to fetch subtitles, optionally through Tor."""
    output_template = str(Path(tmpdir) / "%(id)s.%(ext)s")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--write-sub", "--write-auto-sub",
        "--sub-lang", lang,
        "--sub-format", "vtt",
        "--skip-download",
        "--no-warnings",
        "-o", output_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    if use_tor:
        cookie_file = _ensure_cookie_file()
        cmd[3:3] = ["--proxy", TOR_SOCKS_PROXY, "--cookies", str(cookie_file)]
    else:
        cmd[3:3] = ["--cookies-from-browser", "chrome"]

    return subprocess.run(cmd, capture_output=True, text=True, timeout=90)


def fetch_youtube_subtitle(video_url: str) -> dict | None:
    """Fetch Ukrainian or English subtitles for a YouTube video via yt-dlp.

    Strategy:
    1. If Tor is running → route through Tor with exported cookies.
       On 429, rotate circuit and retry (up to MAX_429_RETRIES times).
    2. If Tor is not running → use --cookies-from-browser chrome directly.
    """
    video_id = _extract_video_id(video_url)
    if not video_id:
        return None

    import tempfile

    use_tor = _tor_is_running()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Try Ukrainian first, then English
        for lang in ["uk", "en"]:
            for attempt in range(MAX_429_RETRIES + 1):
                sub_file = Path(tmpdir) / f"{video_id}.{lang}.vtt"
                # Clean up from previous attempt
                if sub_file.exists():
                    sub_file.unlink()

                try:
                    result = _yt_dlp_fetch_sub(video_id, lang, tmpdir, use_tor)
                except subprocess.TimeoutExpired:
                    print(f"    ⏱️  Timeout fetching subs ({lang})")
                    break  # Don't retry timeouts
                except Exception as e:
                    print(f"    ❌ yt-dlp error ({lang}): {e}")
                    break

                if sub_file.exists():
                    vtt_text = sub_file.read_text(encoding="utf-8")
                    text = _parse_vtt(vtt_text)

                    if len(text) < 30:
                        break  # Try next language

                    title = _get_video_title(video_url)

                    return {
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "title": title,
                        "language": lang,
                        "text": text[:15000],
                        "char_count": len(text),
                    }

                # Check if 429 — rotate circuit and retry
                is_429 = result.stderr and "429" in result.stderr
                if is_429 and use_tor and attempt < MAX_429_RETRIES:
                    print(f"    🚫 429 on {lang} (attempt {attempt + 1}/"
                          f"{MAX_429_RETRIES})")
                    _tor_new_circuit()
                    continue

                # Not a 429 or can't retry — try next language
                if is_429 and not use_tor:
                    print("    🚫 429 — start Tor for auto-rotation: "
                          "tor &")
                break

    return None


def _get_video_title(video_url: str) -> str:
    """Get video title via yt-dlp metadata."""
    try:
        cmd = [sys.executable, "-m", "yt_dlp", "--print", "title",
               "--no-download"]
        if _tor_is_running():
            cmd += ["--proxy", TOR_SOCKS_PROXY, "--cookies", str(COOKIE_FILE)]
        else:
            cmd += ["--cookies-from-browser", "chrome"]
        cmd.append(video_url)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception:
        return ""


def fetch_youtube_subtitles(video_urls: list[str], output_file: Path) -> None:
    """Fetch subtitles for YouTube videos and save as JSONL."""
    existing_ids: set[str] = set()
    if output_file.exists():
        with open(output_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    existing_ids.add(entry.get("video_id", ""))

    new_count = 0
    skip_count = 0
    fail_count = 0

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "a", encoding="utf-8") as f:
        for i, url in enumerate(video_urls):
            vid = _extract_video_id(url)

            if vid in existing_ids:
                skip_count += 1
                continue

            fetched_this_batch = (i - skip_count) % YOUTUBE_BATCH_SIZE
            if fetched_this_batch == 0 and i > 0 and i > skip_count:
                print(f"  ⏳ Batch pause ({YOUTUBE_BATCH_PAUSE}s to avoid rate limiting)...")
                time.sleep(YOUTUBE_BATCH_PAUSE)

            print(f"  [{i+1}/{len(video_urls)}] {url}")
            sub = fetch_youtube_subtitle(url)
            if sub:
                f.write(json.dumps(sub, ensure_ascii=False) + "\n")
                f.flush()
                new_count += 1
                print(f"    ✅ {sub['title'][:60]} ({sub['char_count']} chars, {sub['language']})")
            else:
                fail_count += 1
                print("    ⚠️  No subtitles found")

            time.sleep(YOUTUBE_DELAY)

    print(f"\n  ✅ Fetched: {new_count} | ⏭️  Skipped: {skip_count} | ❌ No subs: {fail_count}")
    print(f"  📄 {output_file}")


# ── Status ────────────────────────────────────────────────────


def show_status() -> None:
    """Show what's cached."""
    print("\n📊 External Sources Cache Status")
    print(f"{'─' * 50}")

    for name in ["ulp_blogs.jsonl", "other_blogs.jsonl", "ulp_youtube.jsonl"]:
        path = CACHE_DIR / name
        if path.exists():
            with open(path) as fh:
                count = sum(1 for line in fh if line.strip())
            size = path.stat().st_size
            print(f"  {name}: {count} entries ({size:,} bytes)")
        else:
            print(f"  {name}: not yet fetched")

    # Compare to what's in external_resources.yaml
    urls = load_external_urls()
    print("\n  URLs in external_resources.yaml:")
    print(f"    ULP blogs: {len(urls['ulp_blogs'])}")
    print(f"    Other blogs: {len(urls['other_blogs'])}")
    print(f"    YouTube (from resources): {len(urls['youtube'])}")


# ── CLI ───────────────────────────────────────────────────────


# ── YouTube channels to ingest ────────────────────────────────
# Each entry: (flag_name, channel_url, output_filename, description)
# Track mapping (for wiki enrichment):
#   ulp          → A1-C2 core tracks (pedagogy, grammar, vocabulary)
#   realna-istoria → HIST, BIO, ISTORIO
#   imtgsh         → HIST, BIO, ISTORIO
#   komik-istoryk  → HIST, BIO, ISTORIO
#   istoria-movy   → OES, RUTH (history of Ukrainian language)
YOUTUBE_CHANNELS = [
    ("ulp", "https://www.youtube.com/@UkrainianLessons/videos",
     "ulp_youtube.jsonl", "Ukrainian Lessons (Anna Ohoiko) — A1-B2 pedagogy, FMU, podcasts"),
    ("realna-istoria", "https://www.youtube.com/channel/UCdlVTngmxbh0oNE1pCwS64g/videos",
     "realna_istoria.jsonl", "Реальна Історія — HIST, BIO, ISTORIO"),
    ("imtgsh", "https://www.youtube.com/@imtgsh/videos",
     "imtgsh.jsonl", "imtgsh — HIST, BIO, ISTORIO"),
    ("istoria-movy", "https://www.youtube.com/@Istoria-Movy/videos",
     "istoria_movy.jsonl", "Istoria-Movy — OES, RUTH (history of Ukrainian language)"),
    ("komik-istoryk", "https://www.youtube.com/@komikistoryk/videos",
     "komik_istoryk.jsonl", "Комік Історик — HIST, BIO, ISTORIO"),
]


def _fetch_channel(name: str, channel_url: str, output_file: Path,
                   description: str) -> None:
    """Scrape a single YouTube channel and fetch subtitles."""
    print(f"\n📺 {description}")
    video_urls = get_channel_video_urls(channel_url)
    if video_urls:
        print(f"  📺 {len(video_urls)} videos found")
        fetch_youtube_subtitles(video_urls, output_file)
    else:
        print(f"  ❌ Channel scrape failed for {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch external sources for wiki enrichment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "YouTube channels:\n"
            + "\n".join(f"  --yt-{c[0]:<20s} {c[3]}" for c in YOUTUBE_CHANNELS)
        ),
    )
    parser.add_argument("--ulp-blogs", action="store_true", help="Fetch ULP blog articles")
    parser.add_argument("--other-blogs", action="store_true", help="Fetch non-ULP articles")
    parser.add_argument("--all-blogs", action="store_true", help="Fetch all blog articles")

    # Add a flag per YouTube channel
    for name, _url, _file, desc in YOUTUBE_CHANNELS:
        parser.add_argument(f"--yt-{name}", action="store_true", help=desc)
    parser.add_argument("--all-youtube", action="store_true", help="Fetch ALL YouTube channels")

    parser.add_argument("--all", action="store_true", help="Fetch everything (blogs + all YouTube)")
    parser.add_argument("--status", action="store_true", help="Show cache status")
    parser.add_argument("--backup", action="store_true",
                        help="Copy data/external_articles/ to Google Drive, delete local")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.backup:
        _backup_to_gdrive()
        return

    # Check if any fetch flag is set
    fetch_flags = [args.ulp_blogs, args.other_blogs, args.all_blogs,
                   args.all_youtube, args.all]
    fetch_flags += [getattr(args, f"yt_{name.replace('-', '_')}") for name, *_ in YOUTUBE_CHANNELS]
    if not any(fetch_flags):
        parser.error("Specify what to fetch (use --help to see options)")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    urls = load_external_urls()

    # Blogs
    if args.ulp_blogs or args.all_blogs or args.all:
        print(f"\n🌐 Fetching {len(urls['ulp_blogs'])} ULP blog articles...")
        fetch_blogs(urls["ulp_blogs"], CACHE_DIR / "ulp_blogs.jsonl")

    if args.other_blogs or args.all_blogs or args.all:
        print(f"\n🌐 Fetching {len(urls['other_blogs'])} other blog articles...")
        fetch_blogs(urls["other_blogs"], CACHE_DIR / "other_blogs.jsonl")

    # YouTube channels
    for name, channel_url, output_file, description in YOUTUBE_CHANNELS:
        flag = getattr(args, f"yt_{name.replace('-', '_')}")
        if flag or args.all_youtube or args.all:
            _fetch_channel(name, channel_url, CACHE_DIR / output_file, description)

    show_status()


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

    for f in files:
        dest = gdrive_target / f.name
        shutil.copy2(f, dest)
        size = f.stat().st_size
        print(f"  ✅ {f.name} ({size:,} bytes) → Google Drive")

    print("\n🗑️  Deleting local copies...")
    for f in files:
        f.unlink()
        print(f"  🗑️  {f.name}")

    print("\n✅ Backup complete. Files on Google Drive at:")
    print(f"   {gdrive_target}")


if __name__ == "__main__":
    main()
