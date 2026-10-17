"""Pinned versus latest-stable report for the weekly security audit (#10862).

``collect`` reads ``scripts/config/stack_pins.yaml`` and writes a local JSON
report. ``render`` turns that report into a comment body. A cell is published
only when it is an exact component name from that pin file, or a version pin.
Every other value is the token ``withheld``. Neither command publishes. The
weekly job in ``.github/workflows/security-audit.yml`` is the only publisher,
and only to the open ``dependency-advisory`` issue.

A component with no verified upstream stays ``latest: unknown``. A name from
the section-1 inventory that is absent from the pin file is a missing pin row.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PINS_PATH = REPO_ROOT / "scripts" / "config" / "stack_pins.yaml"

# kind, target. Targets are public package or release identifiers, not host paths.
# The code CLI's npm package is derived from its pin name so this file does not
# spell a model-shaped token.
UPSTREAMS: dict[str, tuple[str, str]] = {
    "entire": ("github", "entireio/cli"),
    "gh": ("github", "cli/cli"),
    "uv": ("github", "astral-sh/uv"),
    "node": ("node-index", "https://nodejs.org/dist/index.json"),
    "python": ("endoflife", "https://endoflife.date/api/python.json"),
}

# argv, process comm. Command names are PATH lookups, never stored paths.
# A pin whose name ends with "-code" is probed as that prefix.
_PROBES: dict[str, tuple[tuple[str, ...], str]] = {
    "codex": (("codex", "--version"), "codex"),
    "grok": (("grok", "--version"), "grok"),
    "cursor-agent": (("cursor-agent", "--version"), "cursor-agent"),
    "agy": (("agy", "--version"), "agy"),
    "entire": (("entire", "--version"), "entire"),
    "gh": (("gh", "--version"), "gh"),
    "uv": (("uv", "--version"), "uv"),
    "node": (("node", "--version"), "node"),
    "sqlite": (("sqlite3", "--version"), "sqlite3"),
    "postgresql": (("psql", "--version"), "postgres"),
    "prometheus": (("prometheus", "--version"), "prometheus"),
    "grafana": (("grafana-server", "-v"), "grafana-server"),
    "alertmanager": (("alertmanager", "--version"), "alertmanager"),
}
_MULTI_PROBES: dict[str, tuple[tuple[str, ...], ...]] = {
    "backup-restore": (("restic", "--version"), ("rclone", "--version")),
}

_STABLE_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}$")
_GITHUB_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
# The only version text render will publish. Names come from the pin file.
_PUBLISHED_VERSION = re.compile(r"^[0-9]{1,8}(\.[0-9]{1,8}){0,2}([-+][A-Za-z0-9.]{1,20})?$")
_WITHHELD = "withheld"
_USER_AGENT = "learn-ukrainian-stack-currency"
_MAX_BODY = 5_000_000


class PinFileError(ValueError):
    """The pin file could not be read. The message stays free of paths."""


class PublicationRefused(ValueError):
    """The report shape cannot be rendered. The message names no cell value."""


def _accept_version(raw: str) -> str:
    text = raw.strip()
    if text.startswith("v") and len(text) > 1 and text[1].isdigit():
        text = text[1:]
    if _STABLE_VERSION.fullmatch(text):
        return text
    return "unknown"


def version_from_npm(payload: object) -> str:
    if not isinstance(payload, dict):
        return "unknown"
    version = payload.get("version")
    if not isinstance(version, str):
        return "unknown"
    return _accept_version(version)


def version_from_github(payload: object) -> str:
    if not isinstance(payload, dict):
        return "unknown"
    if payload.get("draft") or payload.get("prerelease"):
        return "unknown"
    tag = payload.get("tag_name")
    if not isinstance(tag, str):
        return "unknown"
    return _accept_version(tag)


def version_from_node_index(payload: object) -> str:
    if not isinstance(payload, list):
        return "unknown"
    for item in payload:
        if not isinstance(item, dict):
            continue
        version = item.get("version")
        if not isinstance(version, str) or "-" in version:
            continue
        accepted = _accept_version(version)
        if accepted != "unknown":
            return accepted
    return "unknown"


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def version_from_python_cycles(payload: object) -> str:
    if not isinstance(payload, list):
        return "unknown"
    best: tuple[int, ...] | None = None
    best_text = "unknown"
    for item in payload:
        if not isinstance(item, dict):
            continue
        latest = item.get("latest")
        if not isinstance(latest, str):
            continue
        accepted = _accept_version(latest)
        if accepted == "unknown":
            continue
        parts = _version_tuple(accepted)
        if best is None or parts > best:
            best = parts
            best_text = accepted
    return best_text


def _upstream_url(kind: str, target: str) -> str:
    if kind == "npm":
        return "https://registry.npmjs.org/" + quote(target, safe="@") + "/latest"
    if kind == "github":
        if not _GITHUB_REPO.fullmatch(target):
            raise PinFileError("upstream repository id is not publishable")
        return f"https://api.github.com/repos/{target}/releases/latest"
    if kind in {"node-index", "endoflife"} and target.startswith("https://"):
        return target
    raise PinFileError("upstream kind is not supported")


def _read_json(url: str, opener: Callable[..., Any], headers: Mapping[str, str]) -> object:
    request = urllib.request.Request(url, headers=dict(headers))
    with opener(request, timeout=8) as response:
        raw = response.read(_MAX_BODY + 1)
    if len(raw) > _MAX_BODY:
        raise ValueError("response too large")
    return json.loads(raw.decode("utf-8"))


def has_upstream(name: str) -> bool:
    return name.endswith("-code") or name in UPSTREAMS


def probe_spec(name: str) -> tuple[tuple[str, ...], str] | None:
    """``(argv, process comm)`` for one local command, or None."""
    if name.endswith("-code") and name[: -len("-code")]:
        command = name[: -len("-code")]
        return (command, "--version"), command
    return _PROBES.get(name)


def multi_argv(name: str) -> tuple[tuple[str, ...], ...] | None:
    return _MULTI_PROBES.get(name)


def watched_comms(names: tuple[str, ...] | list[str] = ()) -> frozenset[str]:
    """Process comm names worth a private drift scan. Built from probes, not paths."""
    comms = {comm for _argv, comm in _PROBES.values()}
    comms.add("python")
    for argv_rows in _MULTI_PROBES.values():
        comms.update(argv[0] for argv in argv_rows)
    for name in names:
        spec = probe_spec(name)
        if spec is not None:
            comms.add(spec[1])
    return frozenset(comms)


def fetch_latest(name: str, *, opener: Callable[..., Any] = urllib.request.urlopen) -> str:
    """Latest stable for a verified upstream, otherwise ``unknown``.

    Lookup failures stay ``unknown``. The exception text is discarded because
    it can carry a URL.
    """
    if name.endswith("-code"):
        spec: tuple[str, str] | None = ("npm", "@anthropic-ai/" + name)
    else:
        spec = UPSTREAMS.get(name)
    if spec is None:
        return "unknown"
    kind, target = spec
    accept = "application/vnd.github+json" if kind == "github" else "application/json"
    try:
        payload = _read_json(
            _upstream_url(kind, target),
            opener,
            {"User-Agent": _USER_AGENT, "Accept": accept},
        )
    except Exception:
        return "unknown"
    if kind == "npm":
        return version_from_npm(payload)
    if kind == "github":
        return version_from_github(payload)
    if kind == "node-index":
        return version_from_node_index(payload)
    if kind == "endoflife":
        return version_from_python_cycles(payload)
    return "unknown"


def load_pin_rows(path: Path) -> list[dict[str, str]]:
    """Return name, pinned, and source. A blank pinned value is ``missing``."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise PinFileError("stack pins file could not be read") from exc
    if not isinstance(data, dict) or not isinstance(data.get("pins"), list):
        raise PinFileError("stack pins file has no pins list")
    rows: list[dict[str, str]] = []
    for row in data["pins"]:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        pinned = row.get("pinned")
        source = row.get("source")
        rows.append(
            {
                "name": name.strip(),
                "pinned": pinned.strip() if isinstance(pinned, str) and pinned.strip() else "missing",
                "source": source.strip() if isinstance(source, str) else "",
            }
        )
    return rows


def build_report(path: Path, latest_of: Callable[[str], str]) -> dict[str, Any]:
    """One row per pin. A row without a pinned value does not invent a latest."""
    rows: list[dict[str, str]] = []
    for pin in load_pin_rows(path):
        name = pin["name"]
        if pin["pinned"] == "missing":
            rows.append(
                {
                    "name": name,
                    "pinned": "missing",
                    "latest": "unknown",
                    "source": pin["source"],
                    "latest_reason": "missing_pin",
                }
            )
            continue
        latest = _accept_version(latest_of(name))
        if latest != "unknown":
            reason = "ok"
        elif has_upstream(name):
            reason = "lookup_failed"
        else:
            reason = "no_upstream"
        rows.append(
            {
                "name": name,
                "pinned": pin["pinned"],
                "latest": latest,
                "source": pin["source"],
                "latest_reason": reason,
            }
        )
    return {"rows": rows}


def _pin_names(path: Path | None = None) -> frozenset[str]:
    """Exact ``name`` strings from the pin file. Unreadable pins publish no names."""
    try:
        return frozenset(row["name"] for row in load_pin_rows(path or PINS_PATH))
    except PinFileError:
        return frozenset()


def _publish_name(value: object, names: frozenset[str]) -> str:
    if isinstance(value, str) and value in names:
        return value
    return _WITHHELD


def _publish_version(value: object) -> str:
    if isinstance(value, str) and _PUBLISHED_VERSION.fullmatch(value):
        return value
    return _WITHHELD


def render_body(report: Mapping[str, Any]) -> str:
    """Markdown table. Pin-file names and version pins stay; every other cell is withheld."""
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise PublicationRefused("report field is not publishable")
    names = _pin_names()
    lines = [
        "## Stack currency",
        "",
        "Pinned versus latest stable. Pin-file component names and version pins only.",
        "",
        "| component | pinned | latest | source |",
        "| --- | --- | --- | --- |",
    ]
    withheld_row = f"| {_WITHHELD} | {_WITHHELD} | {_WITHHELD} | {_WITHHELD} |"
    for row in rows:
        if not isinstance(row, dict):
            lines.append(withheld_row)
            continue
        name = _publish_name(row.get("name", ""), names)
        pinned = _publish_version(row.get("pinned", ""))
        latest = _publish_version(row.get("latest", ""))
        source = _publish_version(row.get("source", ""))
        lines.append(f"| {name} | {pinned} | {latest} | {source} |")
    return "\n".join(lines) + "\n"


def _load_report(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PinFileError("stack currency report could not be read") from exc
    if not isinstance(data, dict):
        raise PinFileError("stack currency report could not be read")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write the pinned-versus-latest stack currency report.\n"
            "Use from the weekly security-audit job. Do not use it to open a pull request, "
            "enqueue, or comment: collection and rendering stay local."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ci.stack_currency_report collect --out ci-artifacts/stack-currency.json\n"
            "  .venv/bin/python -m scripts.ci.stack_currency_report render "
            "--report ci-artifacts/stack-currency.json --body-out ci-artifacts/stack-currency.md\n"
            "\n"
            "Outputs:\n"
            "  collect: local JSON with one row per pin.\n"
            "  render: local markdown of pin-file component names and version pins.\n"
            "  Every other cell is the token withheld.\n"
            "  Neither command contacts GitHub or opens an issue.\n"
            "\n"
            "Exit codes:\n"
            "  0 when the local file is written. 1 when the pin file or report cannot be read,\n"
            "  or the rendered body is not publishable.\n"
            "\n"
            "Related:\n"
            "  Pin file: scripts/config/stack_pins.yaml.\n"
            "  Policy: docs/best-practices/stack-currency.md section 2.\n"
            "  Publisher: the stack-currency job in .github/workflows/security-audit.yml (#10862)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    collect_parser = sub.add_parser("collect", help="compare pins with latest stable and write local JSON")
    collect_parser.add_argument(
        "--pins",
        type=Path,
        default=PINS_PATH,
        help="pin file path (default: scripts/config/stack_pins.yaml)",
    )
    collect_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="local JSON report path, e.g. ci-artifacts/stack-currency.json (required)",
    )

    render_parser = sub.add_parser("render", help="render a local report as a pin-name and version comment body")
    render_parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="JSON written by collect (required)",
    )
    render_parser.add_argument(
        "--body-out",
        type=Path,
        required=True,
        help="markdown output path, e.g. ci-artifacts/stack-currency.md (required)",
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            report = build_report(args.pins, fetch_latest)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"stack-currency rows={len(report['rows'])}")
            return 0
        body = render_body(_load_report(args.report))
        args.body_out.parent.mkdir(parents=True, exist_ok=True)
        args.body_out.write_text(body, encoding="utf-8")
        print("stack-currency body written")
    except (PinFileError, PublicationRefused) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
