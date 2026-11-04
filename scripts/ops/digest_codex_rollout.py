#!/usr/bin/env python3
"""Fleet session digester — keyword extract from Codex/Claude jsonl tails.

No LLM. Token-cheap local artifact for Watch Desk / SRE hosts.
See docs/ops/fleet-agent-eyes.md.

Env:
  DIGEST_LABEL  output label (default: local)
  DIGEST_ROOTS  colon-separated session roots
  DIGEST_REPO   repo root for logs/agent-digests/ (default: ~/projects/learn-ukrainian)
  DIGEST_MAX    max source files (default: 12)

Writes:
  logs/agent-digests/<label>-latest.md
  logs/agent-digests/index.md

Prints the output path plus ``bytes= sources= label=``.
"""

from __future__ import annotations

import json
import os
import re
from collections import deque
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.codex_accounts import CodexAccountRefused, codex_account_home

DEFAULT_LABEL = "local"
DEFAULT_REPO = Path.home() / "projects" / "learn-ukrainian"
DEFAULT_MAX = 12
MIN_SOURCE_BYTES = 64
TAIL_LINES = 500
SNIPPET_LIMIT = 16
SNIPPET_CHARS = 220


def default_roots(environ: Mapping[str, str] | None = None) -> list[tuple[str | None, Path]]:
    """Default session roots. Account a is unlabeled; bound ``b-sub`` is ``codex:b``.

    ``DIGEST_ROOTS`` bypasses this and stays unlabeled. Account a ignores
    ambient ``CODEX_HOME``. An unbound ``b-sub`` adds no root.
    """
    env = os.environ if environ is None else environ
    home = Path(env.get("HOME") or Path.home())
    roots: list[tuple[str | None, Path]] = [
        (None, codex_account_home("sub", env) / "sessions"),
        (None, home / ".claude" / "projects"),
        (None, home / ".gemini" / "tmp"),
        (None, home / ".config" / "gemini"),
    ]
    bound = _bound_sessions("b-sub", env)
    if bound is not None:
        roots.append(("codex:b", bound))
    return roots


def _bound_sessions(label: str, env: Mapping[str, str]) -> Path | None:
    try:
        return codex_account_home(label, env) / "sessions"
    except CodexAccountRefused:
        return None


# Material watch terms: blockers, failures, review/merge, fleet ops.
_MATERIAL_RE = re.compile(
    r"(?i)\b(?:"
    r"error|errors|fail(?:ed|ure|ing)?|exception|traceback|"
    r"blocked|blocker|stall(?:ed|ing)?|hung|hang(?:ing)?|timeout|"
    r"conflict|rejected|denied|panic|crash|abort(?:ed)?"
    r"|lease|occupancy|dispatch|worktree|"
    r"waiting|stuck|unable|cannot|"
    r"merge|review|pytest|github"
    r")\b|"
    r"#\d{2,}\b|"
    r"\bPR\s*#?\d+\b|"
    r"\bci\b",
)

# Session-start / rules-load noise that burns tokens without watch value.
_NOISE_RE = re.compile(
    r"(?i)(?:AGENTS\.md|CLAUDE\.md|GEMINI\.md|CODEX\.md|MEMORY\.md|"
    r"cold[_-]?start|cursor_cold_start|/api/rules|"
    r"operator-expectations|non-negotiable-rules|"
    r"SessionStart|loading rules|ruleset digest)",
)

_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6_RE = re.compile(r"\b(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}\b", re.IGNORECASE)
_USER_HOST_RE = re.compile(r"\b[\w.-]+@[\w.-]+\b")
_SSH_HINT_RE = re.compile(r"(?i)\b(?:ssh|scp)\s+\S+")
_LABEL_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

_TEXT_KEYS = frozenset(
    {
        "text",
        "content",
        "message",
        "error",
        "stderr",
        "stdout",
        "reason",
        "detail",
        "summary",
        "output",
        "prompt",
        "result",
    }
)
_SKIP_KEYS = frozenset(
    {
        "id",
        "session_id",
        "cwd",
        "path",
        "filepath",
        "home",
        "hostname",
        "host",
        "ip",
        "address",
    }
)


def env_label(environ: dict[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    raw = (env.get("DIGEST_LABEL") or DEFAULT_LABEL).strip() or DEFAULT_LABEL
    if not _LABEL_RE.fullmatch(raw):
        raise SystemExit(f"DIGEST_LABEL must match {_LABEL_RE.pattern}: {raw!r}")
    return raw


def env_max(environ: dict[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    raw = (env.get("DIGEST_MAX") or str(DEFAULT_MAX)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit(f"DIGEST_MAX must be an integer: {raw!r}") from exc
    if value < 1 or value > 100:
        raise SystemExit("DIGEST_MAX must be between 1 and 100")
    return value


def env_repo(environ: dict[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    raw = (env.get("DIGEST_REPO") or str(DEFAULT_REPO)).strip()
    return Path(raw).expanduser()


def env_roots(environ: dict[str, str] | None = None) -> list[tuple[str | None, Path]]:
    env = os.environ if environ is None else environ
    raw = (env.get("DIGEST_ROOTS") or "").strip()
    if raw:
        return [(None, Path(part).expanduser()) for part in raw.split(":") if part.strip()]
    return default_roots(env)


def collect_sources(roots: Iterable[tuple[str | None, Path]], limit: int) -> list[tuple[Path, str | None]]:
    """Collect jsonl tails, newest mtime first; rollout name is tie-break only.

    The account label travels with the file. It is ``None`` for account a and
    for an explicit ``DIGEST_ROOTS`` list.
    """
    found: list[tuple[Path, str | None]] = []
    seen: set[Path] = set()

    for label, root in roots:
        if not root.is_dir():
            continue
        try:
            hits = list(root.rglob("rollout-*.jsonl")) + list(root.rglob("*.jsonl"))
        except OSError:
            continue
        for path in hits:
            try:
                resolved = path.resolve()
                if resolved in seen or not path.is_file():
                    continue
                if path.stat().st_size < MIN_SOURCE_BYTES:
                    continue
            except OSError:
                continue
            seen.add(resolved)
            found.append((path, label))

    # mtime newest first; rollout-* wins only when timestamps tie.
    found.sort(key=lambda item: (-item[0].stat().st_mtime, 0 if "rollout-" in item[0].name else 1))
    return found[:limit]


def tail_lines(path: Path, count: int = TAIL_LINES) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return list(deque(handle, maxlen=count))
    except OSError:
        return []


def _walk_strings(value: Any, key: str | None = None) -> Iterable[str]:
    if key is not None and key.lower() in _SKIP_KEYS:
        return
    if isinstance(value, str):
        if key is None or key.lower() in _TEXT_KEYS or len(value) >= 24:
            yield value
        return
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from _walk_strings(child, str(child_key))
        return
    if isinstance(value, list):
        for item in value:
            yield from _walk_strings(item, key)


def strings_from_line(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped:
        return []
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return [stripped]
    if isinstance(payload, (dict, list, str)):
        return [item for item in _walk_strings(payload) if item.strip()]
    return []


def redact_opsec(text: str) -> str:
    """Strip IPs, user@host, and ssh command remnants from local snippets."""
    text = _IPV4_RE.sub("[redacted-ip]", text)
    text = _IPV6_RE.sub("[redacted-ip]", text)
    text = _USER_HOST_RE.sub("[redacted-host]", text)
    text = _SSH_HINT_RE.sub("[redacted-ssh]", text)
    return text


def _session_home(path: Path) -> Path | None:
    """Codex home for a file under ``<home>/sessions``. Other roots have none."""
    for parent in path.parents:
        if parent.name == "sessions":
            return parent.parent
    return None


def redact_home(text: str, home: Path) -> str:
    """Replace one account's resolved home and its directory name."""
    resolved = home.resolve()
    for variant in (str(resolved), str(home)):
        if variant:
            text = text.replace(variant, "[codex-home]")
    name = resolved.name
    if name and name not in {".", ".."}:
        text = re.sub(
            rf"(?<![A-Za-z0-9._-]){re.escape(name)}(?![A-Za-z0-9._-])",
            "[codex-home]",
            text,
        )
    return text


def is_noise(text: str) -> bool:
    return bool(_NOISE_RE.search(text))


def is_material(text: str) -> bool:
    return bool(_MATERIAL_RE.search(text))


def extract_snippets(
    lines: Iterable[str],
    limit: int = SNIPPET_LIMIT,
    *,
    home: Path | None = None,
) -> list[str]:
    snippets: list[str] = []
    seen: set[str] = set()
    for line in lines:
        for raw in strings_from_line(line):
            if is_noise(raw) or not is_material(raw):
                continue
            cleaned = " ".join(redact_opsec(raw).split())
            if home is not None:
                cleaned = redact_home(cleaned, home)
            if len(cleaned) > SNIPPET_CHARS:
                cleaned = cleaned[: SNIPPET_CHARS - 1].rstrip() + "…"
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            snippets.append(cleaned)
            if len(snippets) >= limit:
                return snippets
    return snippets


def source_label(path: Path) -> str:
    """Short display name: last three parts, no home/host topology."""
    return "/".join(path.parts[-3:])


def source_heading(path: Path, account: str | None) -> str:
    """Account b is named on the filename only, so the home directory is not shown."""
    if account:
        return f"{account}/{path.name}"
    return source_label(path)


def render_digest(
    *,
    label: str,
    sources: list[tuple[Path, str | None]],
    generated: datetime,
) -> str:
    rows: list[str] = [
        f"# Fleet session digest — {label}",
        "",
        f"Generated: {generated.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"Sources: {len(sources)}",
        "Method: keyword extract (no LLM)",
        "Ladder: shell digest (step 3). Prefer Monitor and GitHub+Fleet pulses first.",
        "",
    ]
    if not sources:
        rows.append("No session jsonl sources found under configured roots.")
        rows.append("")
        return "\n".join(rows)

    for path, account in sources:
        home = _session_home(path)
        heading = source_heading(path, account)
        if home is not None:
            heading = redact_home(heading, home)
        rows.append(f"## {heading}")
        rows.append("")
        snippets = extract_snippets(tail_lines(path), home=home)
        if snippets:
            for snippet in snippets:
                rows.append(f"- {snippet}")
        else:
            rows.append("- (no material keyword hits in last 500 lines)")
        rows.append("")
    return "\n".join(rows)


def render_index(digest_dir: Path, generated: datetime) -> str:
    rows = [
        "# Agent session digests",
        "",
        "Local artifacts. Do not commit. Charter: `docs/ops/fleet-agent-eyes.md`.",
        "",
        f"Refreshed: {generated.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "| Label | File | Bytes |",
        "| --- | --- | ---: |",
    ]
    latest = sorted(digest_dir.glob("*-latest.md"))
    if not latest:
        rows.append("| — | — | 0 |")
    else:
        for path in latest:
            label = path.name.removesuffix("-latest.md")
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            rows.append(f"| {label} | {path.name} | {size} |")
    rows.append("")
    return "\n".join(rows)


def write_digest(
    *,
    label: str,
    repo: Path,
    roots: list[tuple[str | None, Path]],
    limit: int,
) -> tuple[Path, int, int]:
    digest_dir = repo / "logs" / "agent-digests"
    digest_dir.mkdir(parents=True, exist_ok=True)
    sources = collect_sources(roots, limit)
    generated = datetime.now(UTC)
    body = render_digest(label=label, sources=sources, generated=generated)
    output = digest_dir / f"{label}-latest.md"
    output.write_text(body, encoding="utf-8")
    index = digest_dir / "index.md"
    index.write_text(render_index(digest_dir, generated), encoding="utf-8")
    return output, output.stat().st_size, len(sources)


def main() -> int:
    label = env_label()
    repo = env_repo()
    roots = env_roots()
    limit = env_max()
    output, size, sources = write_digest(label=label, repo=repo, roots=roots, limit=limit)
    print(output)
    print(f"bytes={size} sources={sources} label={label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
