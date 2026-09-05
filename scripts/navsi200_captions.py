"""Fetcher and ledger builder for navsi200 YouTube auto-captions (#4705).

Fetches Ukrainian auto-captions via yt-dlp, saves raw transcripts into gitignored
storage, and records a coverage ledger tracking availability, character counts,
and content hashes without committing any verbatim captions or teacher names.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from navsi200_catalog import PRIORITY_TOPICS, load_catalog

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "data" / "corpus_audit" / "navsi200-catalog.json"
DEFAULT_LEDGER_PATH = PROJECT_ROOT / "data" / "corpus_audit" / "navsi200-captions-ledger.json"
DEFAULT_CAPTIONS_DIR = PROJECT_ROOT / "data" / "native-reviewer-lessons" / "navsi200-captions"

DEFAULT_YT_DLP_BIN = ".venv/bin/yt-dlp"

TEACHER_NAME_PATTERNS = (
    re.compile(r"\s*від\s+Анни\s+Огойко\b", re.IGNORECASE),
    re.compile(r"\s*від\s+Анни\b", re.IGNORECASE),
    re.compile(r"\s*Анн[аиеіу]\s+Огойк[оаиуе]\b", re.IGNORECASE),
    re.compile(r"\s*Огойк[оаиуе]\b", re.IGNORECASE),
)


def scrub_teacher_names(text: str) -> str:
    """Remove teacher names and attributions to preserve privacy.

    Args:
        text: Title or description string.

    Returns:
        Sanitized string with teacher names stripped and whitespace normalized.
    """
    cleaned = text
    for pattern in TEACHER_NAME_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    # Strip lingering trailing delimiters or whitespace
    cleaned = re.sub(r"[\s\-:|]+$", "", cleaned).strip()
    return cleaned


def clean_vtt_text(vtt_text: str) -> str:
    """Parse WebVTT subtitle content into clean, plain Ukrainian text.

    Strips WEBVTT headers, timestamps, formatting tags, and duplicate cues.

    Args:
        vtt_text: Raw WebVTT string.

    Returns:
        Normalized plain text string.
    """
    lines: list[str] = []
    for raw_line in vtt_text.splitlines():
        line = raw_line.strip()
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

    deduped: list[str] = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    text = " ".join(deduped)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest of a file.

    Args:
        file_path: Path to file.

    Returns:
        Hexadecimal hash string.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def fetch_single_caption(
    video_id: str,
    output_dir: Path,
    yt_dlp_bin: str = DEFAULT_YT_DLP_BIN,
    timeout: int = 30,
) -> tuple[str, int, str | None]:
    """Fetch Ukrainian auto-captions for a single video using yt-dlp.

    Args:
        video_id: 11-character YouTube video ID.
        output_dir: Local directory for storing raw subtitle files.
        yt_dlp_bin: Path to yt-dlp binary.
        timeout: Subprocess execution timeout in seconds.

    Returns:
        Tuple of (status, char_count, sha256_hash).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    vtt_path = output_dir / f"{video_id}.uk.vtt"
    srt_path = output_dir / f"{video_id}.uk.srt"

    # Reuse existing caption file if present
    for existing in (vtt_path, srt_path):
        if existing.exists() and existing.stat().st_size > 0:
            content = existing.read_text(encoding="utf-8", errors="replace")
            cleaned = clean_vtt_text(content)
            sha = compute_file_sha256(existing)
            return "available", len(cleaned), sha

    out_tmpl = str(output_dir / f"{video_id}.%(ext)s")
    cmd = [
        yt_dlp_bin,
        "--write-auto-subs",
        "--skip-download",
        "--sub-langs",
        "uk",
        "--sub-format",
        "vtt",
        "-o",
        out_tmpl,
        f"https://www.youtube.com/watch?v={video_id}",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "timeout", 0, None
    except Exception as e:
        logger.warning("Failed executing yt-dlp for %s: %s", video_id, e)
        return f"error_{type(e).__name__.lower()}", 0, None

    # Check if subtitle file was downloaded
    for target in (vtt_path, srt_path):
        if target.exists() and target.stat().st_size > 0:
            content = target.read_text(encoding="utf-8", errors="replace")
            cleaned = clean_vtt_text(content)
            sha = compute_file_sha256(target)
            return "available", len(cleaned), sha

    combined = f"{proc.stderr}\n{proc.stdout}".lower()
    if (
        "sign in to confirm you’re not a bot" in combined
        or "sign in to confirm you're not a bot" in combined
        or "login_required" in combined
    ):
        return "bot_blocked", 0, None
    elif "no subtitles" in combined or "there's no subtitles" in combined:
        return "no_captions", 0, None
    elif proc.returncode != 0:
        return "unavailable", 0, None

    return "no_captions", 0, None


def order_lessons_by_priority(lessons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order lessons so priority topics come first in canonical order.

    Priority order:
    1. пароніми
    2. наголос
    3. лексична норма
    4. найтиповіші завдання ЗНО
    Followed by all remaining non-priority lessons.

    Args:
        lessons: List of lesson dicts from catalog.

    Returns:
        Ordered list of unique lesson dicts.
    """
    ordered: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for p_topic in PRIORITY_TOPICS:
        target = p_topic.strip().lower()
        for lesson in lessons:
            lid = lesson["id"]
            if lid in seen_ids:
                continue
            primary = lesson.get("topic", "").lower()
            topics = [t.lower() for t in lesson.get("topics", [])]
            if primary == target or target in topics:
                ordered.append(lesson)
                seen_ids.add(lid)

    # Add any remaining priority lessons not caught by specific topic names
    for lesson in lessons:
        lid = lesson["id"]
        if lid not in seen_ids and lesson.get("is_priority"):
            ordered.append(lesson)
            seen_ids.add(lid)

    # Append remaining non-priority lessons
    for lesson in lessons:
        lid = lesson["id"]
        if lid not in seen_ids:
            ordered.append(lesson)
            seen_ids.add(lid)

    return ordered


def build_caption_ledger(
    catalog: dict[str, Any],
    captions_dir: Path = DEFAULT_CAPTIONS_DIR,
    yt_dlp_bin: str = DEFAULT_YT_DLP_BIN,
    max_workers: int = 8,
    limit: int | None = None,
    priority_only: bool = False,
) -> dict[str, Any]:
    """Execute caption fetching and construct coverage ledger.

    Args:
        catalog: Loaded catalog dictionary.
        captions_dir: Path to directory for storing raw captions.
        yt_dlp_bin: Path to yt-dlp binary.
        max_workers: Number of concurrent fetch worker threads.
        limit: Optional maximum number of lessons to process.
        priority_only: If True, only process priority lessons.

    Returns:
        Dictionary conforming to the coverage ledger schema.
    """
    raw_lessons = catalog.get("lessons", [])
    ordered = order_lessons_by_priority(raw_lessons)

    if priority_only:
        ordered = [l for l in ordered if l.get("is_priority")]

    if limit is not None and limit > 0:
        ordered = ordered[:limit]

    def _process_one(lesson: dict[str, Any]) -> dict[str, Any]:
        video_id = lesson["video_id"]
        raw_title = lesson.get("title", "")
        title = scrub_teacher_names(raw_title)
        topic = lesson.get("topic", "")
        is_priority = bool(lesson.get("is_priority", False))

        status, char_count, sha256_hash = fetch_single_caption(
            video_id=video_id,
            output_dir=captions_dir,
            yt_dlp_bin=yt_dlp_bin,
        )

        return {
            "video_id": video_id,
            "title": title,
            "topic": topic,
            "caption_lang": "uk",
            "status": status,
            "char_count": char_count,
            "sha256": sha256_hash,
            "is_priority": is_priority,
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        entries = list(executor.map(_process_one, ordered))

    status_counts: dict[str, int] = {}
    priority_status_counts: dict[str, int] = {}
    total_chars = 0
    priority_count = 0

    for entry in entries:
        st = entry["status"]
        status_counts[st] = status_counts.get(st, 0) + 1
        total_chars += entry["char_count"]

        if entry["is_priority"]:
            priority_count += 1
            priority_status_counts[st] = priority_status_counts.get(st, 0) + 1

    summary = {
        "total_lessons": len(entries),
        "priority_lessons": priority_count,
        "non_priority_lessons": len(entries) - priority_count,
        "total_chars": total_chars,
        "status_counts": status_counts,
        "priority_status_counts": priority_status_counts,
    }

    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat()
    return {
        "version": 1,
        "description": "YouTube Ukrainian auto-captions coverage ledger for navsi200 catalog (#4705)",
        "generated_at": now_iso,
        "caption_lang": "uk",
        "summary": summary,
        "lessons": entries,
        "entries": entries,
    }


def save_caption_ledger(ledger: dict[str, Any], path: Path | str | None = None) -> Path:
    """Serialize and save ledger to JSON.

    Args:
        ledger: Ledger dictionary.
        path: Optional target path, defaults to `DEFAULT_LEDGER_PATH`.

    Returns:
        Path of written ledger file.
    """
    target = Path(path) if path else DEFAULT_LEDGER_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return target


def load_caption_ledger(path: Path | str | None = None) -> dict[str, Any]:
    """Load and return caption coverage ledger dictionary.

    Args:
        path: Path to ledger JSON file. Defaults to `DEFAULT_LEDGER_PATH`.

    Returns:
        Parsed ledger dictionary.
    """
    target = Path(path) if path else DEFAULT_LEDGER_PATH
    if not target.exists():
        raise FileNotFoundError(f"Ledger file not found: {target}")
    with target.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def main() -> None:
    """CLI entrypoint for navsi200 caption fetching."""
    parser = argparse.ArgumentParser(
        description=(
            "Fetch navsi200 YouTube captions and generate a coverage ledger.\n"
            "Use to refresh caption coverage; not for publishing raw transcripts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples (run from the repository root):
  .venv/bin/python scripts/navsi200_captions.py --priority-only --limit 5
  .venv/bin/python scripts/navsi200_captions.py --max-workers 4

Outputs: Raw captions in the captions directory and a JSON coverage ledger.
Exit codes: 0 on success; nonzero on invalid arguments or processing errors.
Related: scripts/navsi200_catalog.py; #4705.
""",
    )
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_PATH, help="Catalog JSON path (default: data/corpus_audit/navsi200-catalog.json)")
    parser.add_argument("--output", type=Path, default=DEFAULT_LEDGER_PATH, help="Output ledger JSON path (default: data/corpus_audit/navsi200-captions-ledger.json)")
    parser.add_argument("--captions-dir", type=Path, default=DEFAULT_CAPTIONS_DIR, help="Raw captions directory (default: data/native-reviewer-lessons/navsi200-captions)")
    parser.add_argument("--max-workers", type=int, default=8, help="Max worker threads (default: 8; example: 4)")
    parser.add_argument("--limit", type=int, default=None, help="Limit videos processed (default: all; example: 5)")
    parser.add_argument("--priority-only", action="store_true", help="Process only priority topics (default: process all topics)")
    parser.add_argument("--yt-dlp", type=str, default=DEFAULT_YT_DLP_BIN, help="Path to yt-dlp binary (default: .venv/bin/yt-dlp; relative to current directory)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    logger.info("Loading catalog from %s", args.catalog)
    catalog = load_catalog(args.catalog)

    logger.info("Building caption ledger (max_workers=%d, priority_only=%s)...", args.max_workers, args.priority_only)
    ledger = build_caption_ledger(
        catalog=catalog,
        captions_dir=args.captions_dir,
        yt_dlp_bin=args.yt_dlp,
        max_workers=args.max_workers,
        limit=args.limit,
        priority_only=args.priority_only,
    )

    out_file = save_caption_ledger(ledger, args.output)
    logger.info("Saved coverage ledger to %s", out_file)
    logger.info("Summary: %s", json.dumps(ledger["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
