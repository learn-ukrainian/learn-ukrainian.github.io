"""Wiki compilation state — tracks what's compiled, what's pending.

State is stored in wiki/.state/progress.yaml and updated after each
article compilation. Build events are logged to wiki/.state/build.log.jsonl.
"""

import json
from datetime import UTC, datetime, timezone
from pathlib import Path

import yaml

from .config import WIKI_DIR, WIKI_STATE_DIR

# ── Build log (JSONL) ──────────────────────────────────────────────


def log_event(track: str, slug: str, event: str, **data: object) -> None:
    """Append a structured event to the build log.

    Events: compile, review_round, rewrite, review_pass, review_fail, error.
    All extra kwargs become fields in the JSON line.

    Log file: wiki/.state/build.log.jsonl
    Read with: .venv/bin/python scripts/wiki/compile.py --log [--track a2]
    """
    _ensure_state_dir()
    log_path = WIKI_STATE_DIR / "build.log.jsonl"
    entry = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "track": track,
        "slug": slug,
        "event": event,
        **data,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_log(*, track: str | None = None,
             last_n: int = 200) -> list[dict]:
    """Read recent build log entries, optionally filtered by track."""
    log_path = WIKI_STATE_DIR / "build.log.jsonl"
    if not log_path.exists():
        return []
    entries = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if track and entry.get("track") != track:
                continue
            entries.append(entry)
    return entries[-last_n:]


def _ensure_state_dir() -> None:
    """Create state directory if it doesn't exist."""
    WIKI_STATE_DIR.mkdir(parents=True, exist_ok=True)
    # .gitignore the state dir — it's local build state
    gitignore = WIKI_STATE_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# Local build state — not committed\n*\n!.gitignore\n")


def load_progress() -> dict:
    """Load compilation progress from state file.

    Returns:
        {
            "articles": {
                "folk/genres/bylyny": {
                    "status": "compiled",
                    "compiled_at": "2026-04-03T...",
                    "source_count": 5,
                    "word_count": 2400,
                    "model": "gemini-2.5-pro",
                },
                ...
            },
            "last_updated": "2026-04-03T...",
        }
    """
    _ensure_state_dir()
    path = WIKI_STATE_DIR / "progress.yaml"
    if not path.exists():
        return {"articles": {}, "last_updated": None}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        "articles": data.get("articles", {}),
        "last_updated": data.get("last_updated"),
    }


def save_progress(progress: dict) -> None:
    """Save compilation progress to state file."""
    _ensure_state_dir()
    progress["last_updated"] = datetime.now(UTC).isoformat()
    path = WIKI_STATE_DIR / "progress.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(progress, f, default_flow_style=False, allow_unicode=True)


def mark_compiled(article_key: str, *, source_count: int = 0,
                  word_count: int = 0, model: str = "") -> None:
    """Mark an article as compiled in the progress tracker.

    Args:
        article_key: Wiki path relative to wiki/ (e.g., "folk/genres/bylyny").
        source_count: Number of source chunks used.
        word_count: Word count of the compiled article.
        model: Model used for compilation.
    """
    progress = load_progress()
    progress["articles"][article_key] = {
        "status": "compiled",
        "compiled_at": datetime.now(UTC).isoformat(),
        "source_count": source_count,
        "word_count": word_count,
        "model": model,
    }
    save_progress(progress)


def is_compiled(article_key: str) -> bool:
    """Check if an article has already been compiled."""
    progress = load_progress()
    entry = progress["articles"].get(article_key)
    return entry is not None and entry.get("status") == "compiled"


def get_status_summary() -> dict:
    """Get a summary of compilation progress.

    Returns:
        {
            "total_compiled": int,
            "by_domain": {"folk": 3, "periods": 0, ...},
            "total_words": int,
            "last_updated": str | None,
        }
    """
    progress = load_progress()
    articles = progress["articles"]

    by_domain: dict[str, int] = {}
    total_words = 0
    for key, info in articles.items():
        if info.get("status") != "compiled":
            continue
        # Domain is the first path component
        domain = key.split("/")[0]
        by_domain[domain] = by_domain.get(domain, 0) + 1
        total_words += info.get("word_count", 0)

    return {
        "total_compiled": sum(by_domain.values()),
        "by_domain": by_domain,
        "total_words": total_words,
        "last_updated": progress["last_updated"],
    }


def list_wiki_articles() -> list[dict]:
    """List all compiled wiki articles from disk.

    Scans wiki/ for .md files (excluding index.md and .state/).

    Returns list of:
        {"path": "folk/genres/bylyny.md", "word_count": int, "title": str}
    """
    articles = []
    for md_file in sorted(WIKI_DIR.rglob("*.md")):
        # Skip dotdirs (.state, .reviews), index files, and dotfiles
        rel = md_file.relative_to(WIKI_DIR)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if rel.name == "index.md":
            continue
        if rel.name.startswith("."):
            continue

        text = md_file.read_text(encoding="utf-8")
        # Extract title from first H1
        title = ""
        for line in text.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        word_count = len(text.split())
        articles.append({
            "path": str(rel),
            "word_count": word_count,
            "title": title,
        })
    return articles
