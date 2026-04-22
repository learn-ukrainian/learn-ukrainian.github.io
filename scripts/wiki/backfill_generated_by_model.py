#!/usr/bin/env python3
"""Backfill ``generated_by_model`` into wiki article metadata."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wiki.config import WIKI_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "audit" / "phase-2a-wiki-metadata" / "report.md"
CHAT_DIR = Path.home() / ".gemini" / "tmp" / "learn-ukrainian" / "chats"
FIXED_MODEL = "gemini-2.5-pro"
UNKNOWN_MODEL = "unknown"
FALLBACK_CUTOVER = datetime.fromisoformat("2026-04-21T13:12:10+02:00")
WIKI_META_RE = re.compile(r"<!--\s*wiki-meta\b(?P<body>.*?)-->", re.DOTALL)
PROMPT_META_RE = re.compile(r"<!--\s*wiki-meta\s*\n(?P<body>.*?)-->", re.DOTALL)


@dataclass(frozen=True)
class SessionRecord:
    model: str
    timestamp: datetime
    session_name: str


@dataclass(frozen=True)
class ProvenanceDecision:
    model: str
    source: str


@dataclass(frozen=True)
class ArticleResult:
    path: Path
    model: str
    source: str
    had_current_meta: bool
    restored_meta_from: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Rewrite wiki files and write the audit report")
    return parser.parse_args()


def iter_wiki_articles() -> list[Path]:
    """Return wiki article paths, excluding reviews and the generated index."""
    return sorted(
        path
        for path in WIKI_DIR.rglob("*.md")
        if ".reviews" not in path.parts and path.name != "index.md"
    )


def parse_wiki_meta(article_text: str) -> tuple[dict, re.Match[str] | None]:
    """Parse the lightweight ``wiki-meta`` block without PyYAML."""
    match = WIKI_META_RE.search(article_text)
    if not match:
        return {}, None

    meta: dict[str, object] = {}
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
            meta[key] = items
        else:
            meta[key] = value
    meta.setdefault("generated_by_model", UNKNOWN_MODEL)
    return meta, match


def parse_prompt_wiki_meta(prompt_text: str) -> dict:
    """Parse the concrete wiki-meta example embedded in a compile prompt."""
    match = PROMPT_META_RE.search(prompt_text)
    if not match:
        return {}

    meta: dict[str, object] = {}
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [item.strip() for item in value[1:-1].split(",") if item.strip()]
        else:
            meta[key] = value
    return meta


def render_wiki_meta(meta: dict) -> str:
    """Render wiki-meta in a stable multiline format."""
    ordered_keys = ["slug", "domain", "tracks", "compiled", "generated_by_model"]
    lines = ["<!-- wiki-meta"]
    seen: set[str] = set()

    def _format(value: object) -> str:
        if isinstance(value, list):
            return "[" + ", ".join(str(item) for item in value) + "]"
        return str(value)

    for key in ordered_keys:
        if key in meta:
            lines.append(f"{key}: {_format(meta[key])}")
            seen.add(key)
    for key, value in meta.items():
        if key in seen or key == "sources":
            continue
        lines.append(f"{key}: {_format(value)}")
    lines.append("-->")
    return "\n".join(lines)


def run_git(*args: str, check: bool = True) -> str:
    """Run a git command from the project root and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def parse_iso_datetime(raw: str | None) -> datetime | None:
    """Parse ISO timestamps emitted by git and Gemini session logs."""
    value = (raw or "").strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def load_compile_sessions() -> dict[tuple[str, str], list[SessionRecord]]:
    """Map ``(domain, slug)`` to compile-session models from local Gemini JSON."""
    records: dict[tuple[str, str], list[SessionRecord]] = defaultdict(list)
    if not CHAT_DIR.exists():
        return records

    for path in sorted(CHAT_DIR.glob("session-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        messages = data.get("messages") or []
        if not messages:
            continue

        first_message = messages[0]
        content = first_message.get("content")
        if isinstance(content, str):
            prompt_text = content
        else:
            prompt_text = "\n".join(
                str(item.get("text", ""))
                for item in content or []
                if isinstance(item, dict)
            )

        if "Ти укладаєш" not in prompt_text or "<!-- wiki-meta" not in prompt_text:
            continue

        meta = parse_prompt_wiki_meta(prompt_text)
        domain = str(meta.get("domain") or "").strip()
        slug = str(meta.get("slug") or "").strip()
        if not domain or not slug:
            continue

        first_gemini = next(
            (
                message
                for message in messages
                if message.get("type") == "gemini" and message.get("model")
            ),
            None,
        )
        if not first_gemini:
            continue

        timestamp = parse_iso_datetime(first_gemini.get("timestamp"))
        if timestamp is None:
            continue

        records[(domain, slug)].append(
            SessionRecord(
                model=str(first_gemini["model"]).strip(),
                timestamp=timestamp,
                session_name=path.name,
            )
        )

    for article_records in records.values():
        article_records.sort(key=lambda record: record.timestamp)
    return records


def file_last_commit_time(path: Path) -> datetime | None:
    """Return the last commit timestamp for the current file path."""
    output = run_git("log", "-1", "--format=%cI", "--", str(path.relative_to(PROJECT_ROOT)), check=False)
    return parse_iso_datetime(output)


def load_head_text(path: Path) -> str:
    """Read the tracked ``HEAD`` version of a file for stable report diffs."""
    relpath = str(path.relative_to(PROJECT_ROOT))
    result = subprocess.run(
        ["git", "show", f"HEAD:{relpath}"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return path.read_text(encoding="utf-8")
    return result.stdout


def load_historical_meta(path: Path) -> tuple[dict, str | None]:
    """Find the most recent historical ``wiki-meta`` block for a path."""
    relpath = str(path.relative_to(PROJECT_ROOT))
    commit_ids = [line.strip() for line in run_git("log", "--follow", "--format=%H", "--", relpath).splitlines() if line.strip()]
    for commit_id in commit_ids:
        result = subprocess.run(
            ["git", "show", f"{commit_id}:{relpath}"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        meta, _ = parse_wiki_meta(result.stdout)
        if meta:
            return meta, commit_id
    return {}, None


def select_session_record(
    records: list[SessionRecord],
    *,
    compiled_date: str | None,
    last_commit_time: datetime | None,
) -> SessionRecord | None:
    """Pick the compile session that best matches the committed article."""
    candidates = records
    if compiled_date:
        same_day = [record for record in candidates if record.timestamp.date().isoformat() == compiled_date]
        if same_day:
            candidates = same_day
    if last_commit_time is not None:
        before_commit = [record for record in candidates if record.timestamp <= last_commit_time]
        if before_commit:
            candidates = before_commit

    models = {record.model for record in candidates}
    if len(models) == 1:
        return candidates[-1]
    if last_commit_time is not None and last_commit_time < FALLBACK_CUTOVER:
        fixed_candidates = [record for record in candidates if record.model == FIXED_MODEL]
        if fixed_candidates:
            return fixed_candidates[-1]
    return None


def decide_generated_by_model(
    *,
    meta: dict,
    path: Path,
    sessions: dict[tuple[str, str], list[SessionRecord]],
) -> ProvenanceDecision:
    """Infer the model used to generate one wiki article."""
    compiled_date = str(meta.get("compiled") or "").strip() or None
    if compiled_date and compiled_date < "2026-04-21":
        return ProvenanceDecision(
            model=FIXED_MODEL,
            source=f"compiled {compiled_date} before fallback ladder (fixed compiler model)",
        )

    last_commit_time = file_last_commit_time(path)
    if compiled_date == "2026-04-21" and last_commit_time is not None and last_commit_time < FALLBACK_CUTOVER:
        return ProvenanceDecision(
            model=FIXED_MODEL,
            source=f"committed {last_commit_time.isoformat()} before 2026-04-21 fallback cutover",
        )

    domain = str(meta.get("domain") or "").strip()
    candidate_keys = []
    meta_slug = str(meta.get("slug") or "").strip()
    if domain and meta_slug:
        candidate_keys.append(((domain, meta_slug), "metadata slug"))
    if domain and path.stem != meta_slug:
        candidate_keys.append(((domain, path.stem), "file stem"))

    for key, label in candidate_keys:
        record = select_session_record(
            sessions.get(key, []),
            compiled_date=compiled_date,
            last_commit_time=last_commit_time,
        )
        if record is not None:
            return ProvenanceDecision(
                model=record.model,
                source=(
                    f"local Gemini session ({label}) {record.session_name} "
                    f"at {record.timestamp.isoformat()}"
                ),
            )

    return ProvenanceDecision(
        model=UNKNOWN_MODEL,
        source="no article-specific local session match after fallback cutover",
    )


def normalize_meta(meta: dict) -> dict:
    """Keep only the stable wiki-meta keys we want to render."""
    cleaned = dict(meta)
    cleaned.pop("sources", None)
    return cleaned


def rewrite_article_text(original_text: str, meta: dict, *, had_current_meta: bool) -> str:
    """Rewrite or inject the wiki-meta block for one article."""
    rendered_meta = render_wiki_meta(normalize_meta(meta))
    _, match = parse_wiki_meta(original_text)
    if match:
        return original_text[:match.start()] + rendered_meta + original_text[match.end():]
    return rendered_meta + "\n\n" + original_text.lstrip("\n")


def is_flash_model(model: str) -> bool:
    """Return True for Flash-tier Gemini model identifiers."""
    return "flash" in model.lower()


def summarize_source(source: str) -> str:
    """Collapse per-article provenance into stable report buckets."""
    if source.startswith("local Gemini session (metadata slug)"):
        return "local Gemini session match on metadata slug"
    if source.startswith("local Gemini session (file stem)"):
        return "local Gemini session match on file stem"
    if "fallback cutover" in source:
        return "git last-commit time before 2026-04-21 fallback cutover"
    if "before fallback ladder" in source:
        return "compiled date before fallback ladder"
    return source


def build_report(results: list[ArticleResult]) -> str:
    """Render the audit report markdown."""
    total = len(results)
    source_counts = Counter(summarize_source(result.source) for result in results)
    model_counts = Counter(result.model for result in results)
    flash_paths = [result.path for result in results if is_flash_model(result.model)]
    unknown_paths = [result.path for result in results if result.model == UNKNOWN_MODEL]
    restored_meta = [result for result in results if not result.had_current_meta]

    lines = [
        "# Phase 2A Wiki Metadata Retrofit Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        f"- Articles scanned: {total}",
        f"- Flash articles flagged: {len(flash_paths)}",
        f"- Articles marked `unknown`: {len(unknown_paths)}",
        f"- Articles whose missing `wiki-meta` was restored from git history: {len(restored_meta)}",
        "",
        "## Backfill Sources",
        "",
    ]

    for source, count in sorted(source_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {count}: {source}")

    lines.extend([
        "",
        "## Model Distribution",
        "",
    ])
    for model, count in sorted(model_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {model}: {count}")

    lines.extend([
        "",
        "## Flash Articles",
        "",
    ])
    if flash_paths:
        lines.extend(f"- {path}" for path in flash_paths)
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Unknown Articles",
        "",
    ])
    if unknown_paths:
        lines.extend(f"- {path}" for path in unknown_paths)
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Restored Missing Metadata",
        "",
    ])
    if restored_meta:
        for result in restored_meta:
            origin = result.restored_meta_from or "unknown git commit"
            lines.append(f"- {result.path} — restored from git history ({origin})")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    sessions = load_compile_sessions()
    results: list[ArticleResult] = []

    for path in iter_wiki_articles():
        original_text = path.read_text(encoding="utf-8")
        head_text = load_head_text(path)
        _head_meta, head_match = parse_wiki_meta(head_text)
        meta, match = parse_wiki_meta(original_text)
        had_working_meta = match is not None
        had_head_meta = head_match is not None
        restored_meta_from: str | None = None

        if not had_working_meta:
            meta, restored_meta_from = load_historical_meta(path)
            meta = normalize_meta(meta)
            if not meta:
                relpath = path.relative_to(WIKI_DIR)
                meta = {
                    "slug": path.stem,
                    "domain": str(relpath.parent).replace("\\", "/"),
                    "compiled": "unknown",
                }
        elif not had_head_meta:
            _, restored_meta_from = load_historical_meta(path)

        decision = decide_generated_by_model(meta=meta, path=path, sessions=sessions)
        meta["generated_by_model"] = decision.model
        rewritten = rewrite_article_text(original_text, meta, had_current_meta=had_working_meta)

        if args.write and rewritten != original_text:
            path.write_text(rewritten, encoding="utf-8")

        results.append(
            ArticleResult(
                path=path.relative_to(PROJECT_ROOT),
                model=decision.model,
                source=decision.source,
                had_current_meta=had_head_meta,
                restored_meta_from=restored_meta_from if not had_head_meta else None,
            )
        )

    report = build_report(results)
    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
