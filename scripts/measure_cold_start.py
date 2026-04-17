"""
Measure agent cold-start cost.

Simulates a fresh agent orienting itself at session start and records the
cost in tool calls, bytes, estimated input tokens, and remaining file reads
not covered by the Monitor API.

The result is the baseline against which later Monitor API changes are
measured — per GH #1309 / reviewer BLOCKER "don't add endpoints before
measuring the real cold-start budget".

Usage:
    .venv/bin/python scripts/measure_cold_start.py
    .venv/bin/python scripts/measure_cold_start.py --label "pre-caching"
    .venv/bin/python scripts/measure_cold_start.py --json-only

Output:
    JSON summary on stdout. Markdown report appended to
    docs/monitor-api/cold-start-baseline.md unless --json-only is set.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_DOC = PROJECT_ROOT / "docs" / "monitor-api" / "cold-start-baseline.md"

# Endpoints a fresh agent should hit to get oriented. This list is the
# contract — changes to it represent changes to what "cold-start" means.
ORIENT_ENDPOINTS: list[str] = [
    "http://localhost:8765/api/orient",
]

# Files an agent currently reads on cold-start that are NOT covered by the
# API. Each file read is a separate tool call + context cost. Shrinking this
# list is the real cold-start win — an API endpoint can replace 5+ file
# reads with one call.
#
# Paths use the source of truth where possible. `.claude/rules/*` is deployed
# from `claude_extensions/rules/*` via `npm run claude:deploy`; the content
# is identical but the source path is present in every checkout (including
# fresh worktrees), so we measure there.
MANUAL_FILE_READS: list[str] = [
    "CLAUDE.md",
    "claude_extensions/rules/critical-rules.md",
    "claude_extensions/rules/non-negotiable-rules.md",
    "claude_extensions/rules/workflow.md",
    "docs/best-practices/agent-cooperation.md",
    "docs/session-state/current.md",
    "docs/WORKSTREAMS.md",
    "docs/MONITOR-API.md",
]


@dataclass
class EndpointResult:
    url: str
    status: int | None
    bytes: int
    elapsed_ms: float
    error: str | None = None


@dataclass
class FileReadResult:
    path: str
    exists: bool
    bytes: int


@dataclass
class ColdStartMeasurement:
    label: str
    timestamp: str
    api_calls: int
    api_bytes: int
    api_elapsed_ms: float
    file_reads: int
    file_bytes: int
    total_bytes: int
    est_input_tokens: int
    endpoints: list[EndpointResult] = field(default_factory=list)
    files: list[FileReadResult] = field(default_factory=list)
    notes: str = ""


def _estimate_tokens(total_bytes: int) -> int:
    """Rough token estimate — 4 chars per token is the common heuristic.

    This is an estimate, not a precise count. For tighter numbers later,
    swap in tiktoken against the actual model tokenizer. We keep it
    dependency-free here because the script runs in any venv.
    """
    return total_bytes // 4


DEFAULT_FETCH_TIMEOUT_S = 30.0


def _fetch(url: str, timeout: float = DEFAULT_FETCH_TIMEOUT_S) -> EndpointResult:
    start = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
            return EndpointResult(
                url=url,
                status=resp.status,
                bytes=len(body),
                elapsed_ms=round((time.monotonic() - start) * 1000, 1),
            )
    except urllib.error.URLError as exc:
        return EndpointResult(
            url=url,
            status=None,
            bytes=0,
            elapsed_ms=round((time.monotonic() - start) * 1000, 1),
            error=f"{type(exc).__name__}: {exc}",
        )
    except Exception as exc:
        return EndpointResult(
            url=url,
            status=None,
            bytes=0,
            elapsed_ms=round((time.monotonic() - start) * 1000, 1),
            error=f"{type(exc).__name__}: {exc}",
        )


def _read_file(relative_path: str) -> FileReadResult:
    path = PROJECT_ROOT / relative_path
    if not path.exists() or not path.is_file():
        return FileReadResult(path=relative_path, exists=False, bytes=0)
    return FileReadResult(
        path=relative_path, exists=True, bytes=path.stat().st_size
    )


def measure(label: str) -> ColdStartMeasurement:
    endpoints = [_fetch(url) for url in ORIENT_ENDPOINTS]
    files = [_read_file(p) for p in MANUAL_FILE_READS]

    api_bytes = sum(e.bytes for e in endpoints)
    api_elapsed = round(sum(e.elapsed_ms for e in endpoints), 1)
    file_bytes = sum(f.bytes for f in files)
    total_bytes = api_bytes + file_bytes

    return ColdStartMeasurement(
        label=label,
        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        api_calls=len(endpoints),
        api_bytes=api_bytes,
        api_elapsed_ms=api_elapsed,
        file_reads=sum(1 for f in files if f.exists),
        file_bytes=file_bytes,
        total_bytes=total_bytes,
        est_input_tokens=_estimate_tokens(total_bytes),
        endpoints=endpoints,
        files=files,
    )


def _render_markdown(m: ColdStartMeasurement) -> str:
    lines = [
        f"## {m.label} — {m.timestamp}",
        "",
        f"- **Tool calls**: {m.api_calls} API + {m.file_reads} file reads = **{m.api_calls + m.file_reads} total**",
        f"- **Bytes**: {m.api_bytes:,} API + {m.file_bytes:,} files = **{m.total_bytes:,} total**",
        f"- **Est. input tokens**: ~{m.est_input_tokens:,} (chars/4 heuristic)",
        f"- **API latency**: {m.api_elapsed_ms} ms across {m.api_calls} call(s)",
        "",
        "### API calls",
        "",
        "| URL | Status | Bytes | Elapsed ms | Error |",
        "|---|---|---|---|---|",
    ]
    for e in m.endpoints:
        lines.append(
            f"| `{e.url}` | {e.status or '—'} | {e.bytes:,} | {e.elapsed_ms} | {e.error or ''} |"
        )
    lines.extend(["", "### Manual file reads (NOT covered by API)", ""])
    lines.append("| Path | Exists | Bytes |")
    lines.append("|---|---|---|")
    for f in m.files:
        lines.append(f"| `{f.path}` | {'✅' if f.exists else '❌'} | {f.bytes:,} |")
    if m.notes:
        lines.extend(["", f"> {m.notes}"])
    lines.append("")
    return "\n".join(lines)


def _append_markdown(m: ColdStartMeasurement) -> None:
    BASELINE_DOC.parent.mkdir(parents=True, exist_ok=True)
    header = ""
    if not BASELINE_DOC.exists():
        header = (
            "# Monitor API Cold-Start Baseline\n\n"
            "Measurement log for GH #1309. Each run appends a new entry.\n"
            "Compare successive runs to confirm each P0/P1 change reduces cost.\n\n"
            "Run: `.venv/bin/python scripts/measure_cold_start.py --label \"<label>\"`\n\n"
            "---\n\n"
        )
    with BASELINE_DOC.open("a", encoding="utf-8") as fh:
        if header:
            fh.write(header)
        fh.write(_render_markdown(m))
        fh.write("\n---\n\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--label",
        default="baseline",
        help="Short label for this measurement (e.g. 'baseline', 'post-caching').",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only emit JSON to stdout; skip appending markdown report.",
    )
    args = parser.parse_args()

    m = measure(args.label)
    print(json.dumps(asdict(m), indent=2))
    if not args.json_only:
        _append_markdown(m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
