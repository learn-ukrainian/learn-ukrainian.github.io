"""Load the tmux driver lane registry and build each lane's launch plan (#10814).

``scripts/config/driver_lanes.json`` is the one lane data file. The context
guard, the boot relaunch and any keeper read it through this module, so session
names, launchers, models and thresholds cannot drift between them. Every lane
is addressed by its tmux session name (``=<session>:``), never by a pane id,
because pane ids do not survive a tmux server restart.

The tracked file holds only generic, repo-relative launchers. A host adds its
machine-specific wrappers and account directories in an ignored local config
(``LU_DRIVER_LANES_LOCAL``, default
``$XDG_CONFIG_HOME/learn-ukrainian/driver-lanes.local.json``)::

    {"lanes": {"cto": {"wrapper": ["<launcher path>", "<argument>"],
                       "env": {"CLAUDE_CONFIG_DIR": "<account directory>"}}}}

A ``wrapper`` replaces the generic launcher command: one executable path, or a
list of command words. Every word must be plain (letters, digits and
``_@%+=:,./-``), so shell syntax in the config is refused, and the words reach
the pane as an argument vector that no shell parses. A malformed lane entry is
refused for that lane only: it is logged and the lane is not started. ``env``
adds environment variables to the lane's tmux session. Values never appear in
printed plans.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATA_FILE = REPO_ROOT / "scripts" / "config" / "driver_lanes.json"
LOCAL_ENV = "LU_DRIVER_LANES_LOCAL"
KINDS = frozenset({"claude", "codex", "grok"})
SESSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
ENV_KEY_RE = re.compile(r"[A-Z_][A-Z0-9_]*\Z")
# One wrapper word: only the characters shlex leaves unquoted, so no shell syntax, whitespace or
# control character can appear.
WRAPPER_WORD_RE = re.compile(r"[A-Za-z0-9_@%+=:,./-]+\Z")
# The marker the relaunch looks for when a launcher exits (for example on a lease conflict).
EXIT_MARKER = "lane-relaunch: launcher exited rc="
# The pane runs the launcher's argument vector as "$@" under this fixed script, so no config or lane
# value is ever parsed as shell syntax. It reports the exit status, then keeps a shell open.
PANE_SCRIPT = f'"$@"; printf "\\n{EXIT_MARKER}%s\\n" "$?"; exec bash'
PANE_ARGV0 = "lane-launch"
SETTINGS = (
    "claude_handoff_pct",
    "codex_max_compactions",
    "codex_drop_pct",
    "handoff_renudge_seconds",
    "quit_retry_seconds",
    "handoff_alert_seconds",
    "human_active_seconds",
)


class LaneConfigError(ValueError):
    """The lane data file or the local config is invalid."""


@dataclass(frozen=True)
class Lane:
    session: str
    name: str
    kind: str
    epic: str
    sender: str
    goal: str
    launcher: str
    model: str
    effort: str
    lead: bool = False
    kick: str = ""
    provider_args: tuple[str, ...] = ()
    account_env: tuple[str, ...] = ()
    path_prepend: tuple[str, ...] = ()

    @property
    def target(self) -> str:
        """The tmux target of the lane's active pane, matched by exact session name."""
        return f"={self.session}:"


@dataclass(frozen=True)
class Registry:
    lanes: tuple[Lane, ...]
    settings: dict[str, int]
    guard_sender: str = ""

    def by_session(self, session: str) -> Lane:
        for lane in self.lanes:
            if lane.session == session:
                return lane
        raise KeyError(session)


@dataclass(frozen=True)
class LaunchPlan:
    session: str
    argv: tuple[str, ...]
    cwd: str
    env: dict[str, str] = field(default_factory=dict)
    wrapper: bool = False

    @property
    def command(self) -> str:
        """The launcher as one quoted line, for display only; it is never executed."""
        return shlex.join(self.argv)

    def pane_argv(self) -> list[str]:
        """The pane command as an argument vector, which tmux executes directly without a shell.

        The fixed ``PANE_SCRIPT`` runs the launcher words as ``"$@"``, reports the
        exit status and keeps a shell open; the words are never parsed as shell syntax.
        """
        return ["bash", "-c", PANE_SCRIPT, PANE_ARGV0, *self.argv]

    def describe(self) -> dict[str, Any]:
        """A printable plan: environment keys only, never their values."""
        return {
            "session": self.session,
            "command": self.command,
            "cwd": self.cwd,
            "env_keys": sorted(self.env),
            "source": "local-wrapper" if self.wrapper else "generic",
        }


def _string(raw: dict[str, Any], key: str, where: str, *, required: bool = True) -> str:
    value = raw.get(key, "" if not required else None)
    if not isinstance(value, str) or (required and not value):
        raise LaneConfigError(f"{where}: {key} must be a non-empty string")
    return value


def _strings(raw: dict[str, Any], key: str, where: str) -> tuple[str, ...]:
    value = raw.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise LaneConfigError(f"{where}: {key} must be a list of non-empty strings")
    return tuple(value)


def _relative(path: str, where: str) -> str:
    if Path(path).is_absolute() or ".." in Path(path).parts:
        raise LaneConfigError(f"{where}: {path!r} must be repo-relative")
    return path


def parse_registry(data: Any) -> Registry:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise LaneConfigError("lane data: schema_version must be 1")
    settings = {}
    for key in SETTINGS:
        value = data.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise LaneConfigError(f"lane data: {key} must be a positive integer")
        settings[key] = value
    guard_sender = _string(data, "guard_sender", "lane data")
    raw_lanes = data.get("lanes")
    if not isinstance(raw_lanes, list) or not raw_lanes:
        raise LaneConfigError("lane data: lanes must be a non-empty list")
    lanes = []
    for index, raw in enumerate(raw_lanes):
        where = f"lanes[{index}]"
        if not isinstance(raw, dict):
            raise LaneConfigError(f"{where}: must be an object")
        session = _string(raw, "session", where)
        if not SESSION_RE.match(session):
            raise LaneConfigError(f"{where}: session {session!r} is not a plain tmux session name")
        kind = _string(raw, "kind", where)
        if kind not in KINDS:
            raise LaneConfigError(f"{where}: kind must be one of {sorted(KINDS)}")
        account_env = _strings(raw, "account_env", where)
        if not all(ENV_KEY_RE.match(key) for key in account_env):
            raise LaneConfigError(f"{where}: account_env holds an invalid variable name")
        lead = raw.get("lead", False)
        if not isinstance(lead, bool):
            raise LaneConfigError(f"{where}: lead must be a boolean")
        lanes.append(
            Lane(
                session=session,
                name=_string(raw, "name", where),
                kind=kind,
                epic=_string(raw, "epic", where),
                sender=_string(raw, "sender", where),
                goal=_relative(_string(raw, "goal", where), where),
                launcher=_relative(_string(raw, "launcher", where), where),
                model=_string(raw, "model", where),
                effort=_string(raw, "effort", where),
                lead=lead,
                kick=_string(raw, "kick", where, required=False),
                provider_args=_strings(raw, "provider_args", where),
                account_env=account_env,
                path_prepend=tuple(_relative(p, where) for p in _strings(raw, "path_prepend", where)),
            )
        )
    for attr in ("session", "name"):
        values = [getattr(lane, attr) for lane in lanes]
        if len(set(values)) != len(values):
            raise LaneConfigError(f"lane data: duplicate lane {attr}")
    return Registry(lanes=tuple(lanes), settings=settings, guard_sender=guard_sender)


def load_registry(path: Path | None = None) -> Registry:
    source = path or DATA_FILE
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LaneConfigError(f"cannot read lane data {source.name}: {exc}") from exc
    return parse_registry(data)


def default_local_config_path(environ: dict[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    if env.get(LOCAL_ENV):
        return Path(env[LOCAL_ENV])
    base = env.get("XDG_CONFIG_HOME") or str(Path(env.get("HOME", "~")).expanduser() / ".config")
    return Path(base) / "learn-ukrainian" / "driver-lanes.local.json"


def parse_wrapper(value: Any) -> tuple[str, ...]:
    """Validate a local ``wrapper``: one executable path, or a list of command words.

    Raises ``LaneConfigError`` for anything else, including any shell syntax,
    whitespace or control character in a word.
    """
    words = [value] if isinstance(value, str) else value
    if not isinstance(words, list) or not words or not all(isinstance(word, str) for word in words):
        raise LaneConfigError("wrapper must be an executable path or a non-empty list of command words")
    for word in words:
        if not WRAPPER_WORD_RE.match(word):
            raise LaneConfigError(f"wrapper word {word!r} holds whitespace or shell syntax")
    if words[0].startswith("-"):
        raise LaneConfigError(f"wrapper executable {words[0]!r} must not start with '-'")
    return tuple(words)


def _local_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise LaneConfigError("must be an object")
    wrapper = entry.get("wrapper")
    env = entry.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(k, str) and ENV_KEY_RE.match(k) and isinstance(v, str) for k, v in env.items()
    ):
        raise LaneConfigError("env must map variable names to strings")
    return {"wrapper": None if wrapper is None else parse_wrapper(wrapper), "env": dict(env)}


def load_local_config(path: Path) -> dict[str, dict[str, Any]]:
    """Read the ignored per-host overrides; a missing file means no overrides.

    The file can name commands to run, so a symlink, a file owned by another
    user, or a group/world-writable file is refused as a whole. A malformed lane
    entry is kept as ``{"refused": <reason>}``: ``launch_plan`` raises for that
    lane only, so it is logged and never started while the other lanes run.
    """
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {}
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise LaneConfigError("local lane config must be a regular file, not a symlink")
    if info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise LaneConfigError("local lane config must be owned by this user and not group/world-writable")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LaneConfigError(f"cannot read local lane config: {exc}") from exc
    lanes = data.get("lanes", {}) if isinstance(data, dict) else None
    if not isinstance(lanes, dict):
        raise LaneConfigError("local lane config: lanes must be an object keyed by session")
    out: dict[str, dict[str, Any]] = {}
    for session, entry in lanes.items():
        try:
            out[session] = _local_entry(entry)
        except LaneConfigError as exc:
            out[session] = {"refused": f"local lane config: {session}: {exc}"}
    return out


def generic_argv(lane: Lane) -> tuple[str, ...]:
    argv = [f"./{lane.launcher}", "--epic", lane.epic, "--model", lane.model, "--effort", lane.effort]
    if lane.kick:
        argv.append(lane.kick)
    if lane.provider_args:
        argv += ["--", *lane.provider_args]
    return tuple(argv)


def launch_plan(
    lane: Lane,
    *,
    repo_root: Path,
    local: dict[str, dict[str, Any]] | None = None,
    base_path: str | None = None,
) -> LaunchPlan:
    """Build the lane's launch: generic launcher unless the local config names a wrapper.

    Raises ``LaneConfigError`` when the lane's local entry was refused.
    """
    override = (local or {}).get(lane.session, {})
    if "refused" in override:
        raise LaneConfigError(override["refused"])
    env = dict(override.get("env") or {})
    if lane.path_prepend:
        inherited = os.environ.get("PATH", "") if base_path is None else base_path
        prefix = ":".join(str(repo_root / part) for part in lane.path_prepend)
        env["PATH"] = f"{prefix}:{inherited}" if inherited else prefix
    wrapper = override.get("wrapper")
    return LaunchPlan(
        session=lane.session,
        argv=wrapper or generic_argv(lane),
        cwd=str(repo_root),
        env=env,
        wrapper=bool(wrapper),
    )


def relaunch_order(registry: Registry) -> list[Lane]:
    """Data-file order, with lead lanes (the CTO) last so they find the others running."""
    return [lane for lane in registry.lanes if not lane.lead] + [lane for lane in registry.lanes if lane.lead]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print the validated tmux driver lane registry as JSON (sessions, launchers, thresholds).\n"
            "Use it to inspect lane data or to feed a keeper; it never touches tmux."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ops.driver_lanes\n"
            "  .venv/bin/python scripts/ops/driver_lanes.py --data scripts/config/driver_lanes.json\n"
            "Outputs: JSON on stdout; nothing is written.\n"
            "Exit codes: 0 valid; 1 invalid lane data; 2 invalid arguments.\n"
            "Related: scripts/config/driver_lanes.json, scripts/ops/context_guard.py, "
            "scripts/ops/lane_relaunch.py, issue #10814."
        ),
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DATA_FILE,
        help="Lane data file (default: scripts/config/driver_lanes.json).",
    )
    args = parser.parse_args(argv)
    try:
        registry = load_registry(args.data)
    except LaneConfigError as exc:
        print(f"invalid lane data: {exc}", file=sys.stderr)
        return 1
    payload = {
        "settings": registry.settings,
        "guard_sender": registry.guard_sender,
        "lanes": [{**lane.__dict__, "target": lane.target} for lane in registry.lanes],
    }
    print(json.dumps(payload, indent=1, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
