"""Report installed distribution drift against the repository's flat pip lock."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

DEFAULT_LOCK = Path(__file__).resolve().parents[2] / "requirements-lock.txt"


def parse_freeze(text: str) -> dict[str, str]:
    """Parse `uv pip list --format freeze` output, retaining exact versions."""
    installed: dict[str, str] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        name, separator, version = line.partition("==")
        if not separator or not name or not version:
            raise ValueError(f"installed list line {number} is not a name==version pin")
        key = canonicalize_name(name)
        if key in installed:
            raise ValueError(f"installed list repeats {key}")
        installed[key] = version
    return installed


def parse_lock(text: str, *, directory: Path) -> dict[str, str | None]:
    """Parse exact pins; a direct URL has no version available to compare."""
    locked: dict[str, str | None] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("#"):
            continue
        line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
        if not line:
            continue
        if line.startswith("./"):
            project_file = directory / line / "pyproject.toml"
            try:
                project = tomllib.loads(project_file.read_text(encoding="utf-8"))["project"]
                name, version = project["name"], project["version"]
            except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
                raise ValueError(f"lock line {number} has unreadable local project metadata") from exc
        else:
            try:
                requirement = Requirement(line)
            except InvalidRequirement as exc:
                raise ValueError(f"lock line {number} is not a valid requirement") from exc
            if requirement.marker is not None and not requirement.marker.evaluate():
                continue
            name = requirement.name
            if requirement.url is not None and not requirement.specifier:
                version = None
            else:
                specs = list(requirement.specifier)
                if len(specs) != 1 or specs[0].operator != "==" or "*" in specs[0].version:
                    raise ValueError(f"lock line {number} is not an exact pin")
                version = specs[0].version
        key = canonicalize_name(name)
        if key in locked:
            if locked[key] == version:
                continue
            raise ValueError(f"lock has conflicting pins for {key}")
        locked[key] = version
    return locked


def compare(
    installed: dict[str, str], locked: dict[str, str | None]
) -> tuple[list[str], list[str], list[str]]:
    """Return missing, extra, and version-mismatched distribution names."""
    missing = sorted(locked.keys() - installed.keys())
    extra = sorted(installed.keys() - locked.keys())
    changed = []
    for name in sorted(locked.keys() & installed.keys()):
        pin = locked[name]
        if pin is None:
            continue
        expected = Version(pin)
        actual = Version(installed[name])
        if expected != (actual if expected.local else Version(actual.public)):
            changed.append(name)
    return missing, extra, changed


def _compact(label: str, names: list[str]) -> str:
    shown = ", ".join(names[:8])
    suffix = f", +{len(names) - 8} more" if len(names) > 8 else ""
    return f"{label}={len(names)}" + (f" ({shown}{suffix})" if names else "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare installed Python distributions with requirements-lock.txt.\n"
            "Run after host dependency changes or before a proposed venv resync; "
            "do not use it to prove dependency consistency."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  /path/to/project/.venv/bin/python scripts/maintenance/venv_lock_drift.py "
            "--python /path/to/project/.venv/bin/python\n"
            "  /path/to/project/.venv/bin/python scripts/maintenance/venv_lock_drift.py "
            "--python /path/to/venv/bin/python --lock requirements-lock.txt\n\n"
            "Outputs: Compact counts and sample distribution names; writes no files. "
            "Requires uv on PATH. Run uv pip check separately for dependency consistency.\n"
            "Exit codes: 0 exact match, 1 drift, 2 invalid input or inspection failure.\n"
            "Related: #9204; URL requirements are checked by distribution name only."
        ),
    )
    parser.add_argument(
        "--python", required=True, type=Path,
        help="Interpreter whose installed distributions are checked; example: /path/to/venv/bin/python.",
    )
    parser.add_argument(
        "--lock", type=Path, default=DEFAULT_LOCK,
        help="Flat requirements lock to compare (default: repository requirements-lock.txt); example: requirements-lock.txt.",
    )
    args = parser.parse_args(argv)
    try:
        if not args.python.is_file():
            raise ValueError("--python must name an existing interpreter file")
        locked = parse_lock(args.lock.read_text(encoding="utf-8"), directory=args.lock.resolve().parent)
        result = subprocess.run(
            ["uv", "pip", "list", "--python", str(args.python), "--format", "freeze"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        installed = parse_freeze(result.stdout)
    except ValueError as exc:
        print(f"venv-lock check failed: {exc}", file=sys.stderr)
        return 2
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"venv-lock check failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    missing, extra, changed = compare(installed, locked)
    print(f"lock={len(locked)} installed={len(installed)}")
    print("; ".join((_compact("missing", missing), _compact("extra", extra), _compact("version", changed))))
    return 1 if missing or extra or changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
