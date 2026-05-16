"""Parsers for the /goal status-line grammar.

Grammar source of truth: ``claude_extensions/rules/goal-driven-runs.md``.
Every /goal turn ends with one of:

* ``GOAL_STATUS turn=N/M blocked=N/M no_progress=N/M queue_head=<token>``
* ``GOAL_WAIT signal=<id> reason="..."`` (suspend until ``<id>`` fires)
* ``GOAL_DONE reason="<one-line>"``
* ``GOAL_ABORT reason="..." last_cmd="..." last_cwd="..." last_output="..."
  next_action="..." queue_head=<token>``

The harness needs a single deterministic parser so the Stop hook + tests
agree on what the agent emitted. Hand-rolling per-call regex inside shell
hooks was the original failure mode (issue #1933).
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

STATUS_KIND = "GOAL_STATUS"
WAIT_KIND = "GOAL_WAIT"
DONE_KIND = "GOAL_DONE"
ABORT_KIND = "GOAL_ABORT"

TERMINAL_KINDS: tuple[str, ...] = (DONE_KIND, ABORT_KIND)
ALL_KINDS: tuple[str, ...] = (STATUS_KIND, WAIT_KIND, DONE_KIND, ABORT_KIND)

_HEADER_RE = re.compile(r"^(GOAL_STATUS|GOAL_WAIT|GOAL_DONE|GOAL_ABORT)\b(.*)$")


@dataclass
class StatusLine:
    """One parsed /goal status line."""

    kind: str
    fields: dict[str, str] = field(default_factory=dict)
    raw: str = ""

    @property
    def is_terminal(self) -> bool:
        return self.kind in TERMINAL_KINDS

    @property
    def is_wait(self) -> bool:
        return self.kind == WAIT_KIND

    @property
    def signal(self) -> str | None:
        return self.fields.get("signal") if self.is_wait else None


def parse_status_line(text: str) -> StatusLine | None:
    """Parse a single line; returns ``None`` if no recognized header."""
    stripped = text.strip()
    match = _HEADER_RE.match(stripped)
    if not match:
        return None
    kind, rest = match.group(1), match.group(2).strip()
    return StatusLine(kind=kind, fields=_parse_kv(rest), raw=stripped)


def find_last_status_line(blob: str) -> StatusLine | None:
    """Bottom-up scan of ``blob``; returns the last recognized status line."""
    for line in reversed(blob.splitlines()):
        parsed = parse_status_line(line)
        if parsed is not None:
            return parsed
    return None


def _parse_kv(rest: str) -> dict[str, str]:
    """Tokenize ``key=val key2="quoted val"`` payloads."""
    if not rest:
        return {}
    try:
        tokens = shlex.split(rest, posix=True)
    except ValueError:
        # Malformed quoting — fall back to whitespace split so we still
        # surface the kind, and downstream validation can complain.
        tokens = rest.split()
    out: dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            continue
        key, _, val = token.partition("=")
        if key:
            out[key.strip()] = val
    return out
