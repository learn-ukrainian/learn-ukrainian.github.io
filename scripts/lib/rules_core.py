"""The rules core every agent seat loads, read from the local checkout.

One loader for every seat: launchers (``scripts/lib/rules_core.sh``), ``delegate.py``
workers and review dispatches, ACP asks and discussion legs
(``agent_runtime.runner.invoke_inter_agent``), the legacy bridge prompt builders,
and ``GET /api/rules?scope=...``. Everything here is offline: files come from the
checkout this module runs from (or an explicit ``root``), never from the environment,
the working directory or the Monitor API.

Seats:
    core     ``agents_extensions/shared/rules/core.md``
    content  the core plus ``core-curriculum.md`` (curriculum seats)

An absent, unreadable or empty core file refuses: every entry point raises
``RulesCoreMissing`` (naming the repo-relative path) before any side effect, and the
CLI exits 3. Nothing here warns and continues without the core.

A seat is ``content`` when asked for explicitly (``--seat`` / ``LU_RULES_SEAT``) or
when a driver lane's ``driver_agent_type`` is the curriculum orchestrator;
otherwise it is ``core``.

Task scopes (``task:<name>``) name the reference sources ``task-scoped-reading.md``
selects for a task; ``/api/rules?scope=task:<name>`` serves them, and
``_load-via-api.md`` lists the same selection for offline reads.

Usage:
    rules_core.py [--root DIR] [--seat core|content] [--lane LANE] [--provider P]
                  [--format text|block|toml|kimi-agent-file|seat|json] [--output PATH]

Exit codes:
    0  printed (or wrote) the requested form
    2  usage error
    3  a core source file is missing or unreadable
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR_REL = "agents_extensions/shared/rules"
CORE_REL = f"{RULES_DIR_REL}/core.md"
CONTENT_ADDENDUM_REL = f"{RULES_DIR_REL}/core-curriculum.md"
SEATS = ("core", "content")
SEAT_ENV = "LU_RULES_SEAT"
CONTENT_AGENT_TYPES = frozenset({"curriculum-orchestrator"})
# Same separator as the legacy /api/rules bundle, so a scope assembles alike.
FILE_SEP = "\n\n---\n\n"
BLOCK_OPEN = "<rules-core"
BLOCK_CLOSE = "</rules-core>"
# Seeds a first turn where the harness only accepts the core as an initial prompt.
ACK_PROMPT = (
    "The rules core above is loaded for this session. Reply only 'Rules core loaded.' and wait for instructions."
)
PILLAR_HEADING = re.compile(r"^## (P\d+) — .*$", re.MULTILINE)

_SKILLS = "agents_extensions/shared/skills"
_RULES = RULES_DIR_REL


@dataclass(frozen=True)
class TaskScope:
    """One ``task-scoped-reading.md`` row: the phrase naming it and its sources."""

    row: str
    sources: tuple[str, ...]


TASK_SCOPES: dict[str, TaskScope] = {
    "repo-change": TaskScope(
        "Any repository change",
        (f"{_RULES}/critical-rules.md", f"{_RULES}/delegate-must-use-worktree.md", f"{_RULES}/workflow.md"),
    ),
    "cli": TaskScope("CLI implementation", (f"{_RULES}/cli-help-standard.md",)),
    "curriculum": TaskScope("Curriculum planning", (f"{_RULES}/non-negotiable-rules.md",)),
    "fresh-build": TaskScope("Core fresh lesson-based build", ("docs/epics/fresh-build-build-program.md",)),
    "routing": TaskScope("Assigning workers", (f"{_RULES}/model-assignment.md", f"{_RULES}/workflow.md")),
    "driver": TaskScope(
        "Explicitly assigned epic/track driver",
        (
            f"{_RULES}/fleet-comms-coordination.md",
            f"{_RULES}/fleet-driver-routing.md",
            "docs/best-practices/fleet-shared-doctrine.md",
            "docs/best-practices/fleet-role-scorecard.md",
            f"{_SKILLS}/drive-epic/SKILL.md",
        ),
    ),
    "fleet-comms": TaskScope("Fleet Comms action", (f"{_RULES}/fleet-comms-coordination.md",)),
    "intake": TaskScope("Non-trivial intake", (f"{_SKILLS}/entire-context/SKILL.md",)),
    "review": TaskScope("Code/infra review", (f"{_SKILLS}/local-code-review/SKILL.md",)),
    "task-family": TaskScope("Task archive", (f"{_SKILLS}/task-family-manager/SKILL.md",)),
    "rollover": TaskScope("Rollover preparation", (f"{_SKILLS}/thread-rollover/SKILL.md",)),
}


class RulesCoreError(Exception):
    """A requested seat, scope or source cannot be served."""


class RulesCoreMissing(RulesCoreError):
    """A core source file is absent, unreadable or empty; the message names its path."""


def normalize_seat(seat: str | None) -> str | None:
    value = (seat or "").strip().lower()
    return value if value in SEATS else None


def resolve_seat(
    seat: str | None = None,
    *,
    lane: str | None = None,
    provider: str = "claude",
    env: dict[str, str] | None = None,
) -> str:
    """Explicit seat, else ``LU_RULES_SEAT``, else the driver lane's agent type."""
    explicit = normalize_seat(seat)
    if explicit:
        return explicit
    from_env = normalize_seat((os.environ if env is None else env).get(SEAT_ENV))
    if from_env:
        return from_env
    if lane:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.orchestration.driver_agent_type import resolve_driver_agent_type

        if resolve_driver_agent_type(lane, provider=provider) in CONTENT_AGENT_TYPES:
            return "content"
    return "core"


def core_dir(root: Path | None = None) -> Path:
    """Directory holding the core files: the rules directory of ``root``, else of this checkout."""
    return (ROOT if root is None else Path(root)) / RULES_DIR_REL


def seat_sources(seat: str) -> tuple[str, ...]:
    if seat == "core":
        return (CORE_REL,)
    if seat == "content":
        return (CORE_REL, CONTENT_ADDENDUM_REL)
    raise RulesCoreError(f"unknown seat {seat!r} (expected one of {', '.join(SEATS)})")


def scope_sources(scope: str) -> tuple[str, ...]:
    """Repo-relative sources for ``core``, ``content`` or ``task:<name>``."""
    if scope in SEATS:
        return seat_sources(scope)
    if scope.startswith("task:"):
        name = scope.removeprefix("task:")
        if name in TASK_SCOPES:
            return TASK_SCOPES[name].sources
        raise RulesCoreError(f"unknown task scope {name!r} (expected one of {', '.join(sorted(TASK_SCOPES))})")
    raise RulesCoreError(f"unknown scope {scope!r} (expected core, content, or task:<name>)")


def source_path(rel: str, root: Path | None = None) -> Path:
    if rel in (CORE_REL, CONTENT_ADDENDUM_REL):
        return core_dir(root) / Path(rel).name
    return (ROOT if root is None else Path(root)) / rel


def assemble(sources: tuple[str, ...], root: Path | None = None) -> str:
    """Join sources the way the legacy bundle does; every source must be readable and non-empty."""
    parts: list[str] = []
    for rel in sources:
        path = source_path(rel, root)
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RulesCoreMissing(f"rules source unavailable: {rel} ({exc.__class__.__name__})") from exc
        if not body.strip():
            raise RulesCoreMissing(f"rules source unavailable: {rel} (empty)")
        parts.append(body.rstrip() + "\n")
    return FILE_SEP.join(parts).rstrip() + "\n"


def core_text(seat: str = "core", root: Path | None = None) -> str:
    return assemble(seat_sources(seat), root)


def core_block(seat: str = "core", root: Path | None = None) -> str:
    """The core framed for injection into a prompt or system prompt."""
    text = core_text(seat, root)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f'{BLOCK_OPEN} seat="{seat}" sha256="{digest}">\n{text}{BLOCK_CLOSE}'


def require_core(seat: str | None = None, root: Path | None = None) -> str:
    """Refuse unless the seat's core sources are all readable; returns the resolved seat.

    Entry points call this before their first side effect (a worktree, a task record,
    a process); ``with_core`` then reads the same files again when it builds the prompt.

    Raises:
        RulesCoreMissing: a source is absent, unreadable or empty (message names the path).
    """
    resolved = resolve_seat(seat)
    core_text(resolved, root)
    return resolved


def with_core(prompt: str, seat: str | None = None, root: Path | None = None) -> str:
    """Prepend the core block to ``prompt``; unchanged if the prompt already starts with it.

    Only a leading block counts: a core quoted further down (an attachment, a
    fenced file) does not stand in for the preamble.

    Raises:
        RulesCoreMissing: the core is absent, unreadable or empty; nothing is sent without it.
    """
    block = core_block(resolve_seat(seat), root)
    if prompt.startswith(block):
        return prompt
    return f"{block}\n\n{prompt}"


def pillar_anchors(text: str) -> tuple[str, str]:
    """First and last ``## P<n> — `` heading lines, in pillar-number order."""
    found = [(int(m.group(1)[1:]), m.group(0)) for m in PILLAR_HEADING.finditer(text)]
    if not found:
        raise RulesCoreError("no '## P<n> — ' pillar headings found")
    found.sort()
    return found[0][1], found[-1][1]


def toml_basic_string(text: str) -> str:
    """Encode ``text`` as one TOML basic string (for ``codex -c key=<value>``)."""
    out = ['"']
    for ch in text:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif code < 0x20 or code == 0x7F:
            out.append(f"\\u{code:04X}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def kimi_agent_file_text(block: str) -> str:
    """A Kimi Code agent file that keeps the default prompt and appends the core.

    Kimi renders ``${base_prompt}`` as its default system prompt; any other
    ``${...}`` in the body would be template-substituted, so it is refused.
    """
    if "${" in block:
        raise RulesCoreError("the rules core contains '${', which Kimi agent files would substitute")
    return (
        "---\n"
        "name: rules-core\n"
        "description: Kimi Code default agent with the project rules core appended.\n"
        "---\n"
        "${base_prompt}\n\n"
        f"{block}\n"
    )


def _render(fmt: str, seat: str, root: Path) -> str:
    if fmt == "seat":
        return seat + "\n"
    if fmt == "text":
        return core_text(seat, root)
    block = core_block(seat, root)
    if fmt == "block":
        return block + "\n"
    if fmt == "toml":
        return toml_basic_string(block) + "\n"
    if fmt == "kimi-agent-file":
        return kimi_agent_file_text(block)
    text = core_text(seat, root)
    first, last = pillar_anchors(text)
    payload = {
        "seat": seat,
        "sources": list(seat_sources(seat)),
        "bytes": len(text.encode("utf-8")),
        "block_bytes": len(block.encode("utf-8")),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "first_anchor": first,
        "last_anchor": last,
    }
    return json.dumps(payload, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the rules core for an agent seat from the local checkout.",
        epilog=(
            "Examples:\n"
            "  rules_core.py --format json\n"
            "  rules_core.py --lane core --format seat\n"
            "  rules_core.py --seat content --format block\n"
            "Exit codes: 0 printed; 2 usage error; 3 a core source is missing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="checkout to read (default: this checkout)")
    parser.add_argument("--seat", choices=SEATS, help=f"seat to load (default: ${SEAT_ENV}, then --lane, then core)")
    parser.add_argument("--lane", help="driver lane; a curriculum-orchestrator lane is a content seat")
    parser.add_argument("--provider", default="claude", help="slot provider for --lane lookup (default: claude)")
    parser.add_argument(
        "--format",
        choices=("text", "block", "toml", "kimi-agent-file", "seat", "json"),
        default="block",
        help="text: sources joined; block: framed for a prompt; toml: block as a TOML string; "
        "kimi-agent-file: Kimi agent definition; seat: resolved seat; json: sizes and anchors",
    )
    parser.add_argument("--output", type=Path, help="write to this file instead of stdout")
    args = parser.parse_args(argv)
    seat = resolve_seat(args.seat, lane=args.lane, provider=args.provider)
    try:
        rendered = _render(args.format, seat, args.root)
    except RulesCoreMissing as exc:
        print(f"rules_core: {exc}", file=sys.stderr)
        return 3
    except RulesCoreError as exc:
        print(f"rules_core: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
