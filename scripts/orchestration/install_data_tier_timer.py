"""Render and install the nightly data-tier systemd user timer.

Use --check before installation; use --apply after the branch has merged.
--enable starts the timer only when paired with --apply.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = PROJECT_ROOT / "packaging" / "systemd"
UNITS = ("learn-ukrainian-data-tier.service", "learn-ukrainian-data-tier.timer")


class InstallError(RuntimeError):
    """The requested unit state could not be produced."""


def render_units(repo_root: Path) -> dict[str, str]:
    rendered = {}
    for name in UNITS:
        source = TEMPLATE_DIR / name
        if not source.is_file():
            raise InstallError(f"unit template missing: {name}")
        text = source.read_text(encoding="utf-8")
        if name.endswith(".service") and "@REPO_ROOT@" not in text:
            raise InstallError(f"unit placeholder missing: {name}")
        rendered[name] = text.replace("@REPO_ROOT@", str(repo_root))
    return rendered


def verify_units(rendered: dict[str, str]) -> None:
    analyzer = shutil.which("systemd-analyze")
    if analyzer is None:
        raise InstallError("systemd-analyze is unavailable")
    with tempfile.TemporaryDirectory(prefix="lu-data-tier-units-") as folder:
        paths = []
        for name, text in rendered.items():
            path = Path(folder) / name
            path.write_text(text, encoding="utf-8")
            paths.append(str(path))
        result = subprocess.run([analyzer, "verify", *paths], capture_output=True, text=True, check=False, timeout=60)
    if result.returncode:
        raise InstallError(f"systemd-analyze verify failed: {(result.stderr or result.stdout).strip()}")


def systemctl_user(*args: str) -> None:
    result = subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, check=False, timeout=60)
    if result.returncode:
        raise InstallError(f"systemctl --user failed: {result.stderr.strip()}")


def check(rendered: dict[str, str], unit_dir: Path) -> int:
    differences = []
    for name, content in rendered.items():
        target = unit_dir / name
        if not target.is_file() or target.read_text(encoding="utf-8") != content:
            differences.append(name)
    if differences:
        print("unit drift: " + ", ".join(differences))
        return 1
    print("units current: " + ", ".join(UNITS))
    return 0


def apply(rendered: dict[str, str], unit_dir: Path, *, enable: bool) -> int:
    unit_dir.mkdir(parents=True, exist_ok=True)
    changed = 0
    for name, content in rendered.items():
        target = unit_dir / name
        if (
            target.is_file()
            and target.read_text(encoding="utf-8") == content
            and target.stat().st_mode & 0o777 == 0o600
        ):
            continue
        target.touch(mode=0o600, exist_ok=True)
        os.chmod(target, 0o600)
        target.write_text(content, encoding="utf-8")
        changed += 1
    systemctl_user("daemon-reload")
    if enable:
        systemctl_user("enable", "--now", UNITS[1])
    print(f"wrote {changed} unit(s); daemon reloaded; timer {'enabled' if enable else 'not enabled'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Install the nightly data-tier systemd user units.\n"
            "Use --check to compare installed units, --apply to write them, and --enable after merge."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  <project-python> -m scripts.orchestration.install_data_tier_timer --check\n"
            "  <project-python> -m scripts.orchestration.install_data_tier_timer --apply --enable\n"
            "Outputs: owner-only units in the user systemd directory; --apply reloads the user manager.\n"
            "Exit codes: 0 = current or applied; 1 = drift or installation failure; 2 = invalid usage.\n"
            "Related: issue #9229 and packaging/systemd/learn-ukrainian-data-tier.*."
        ),
    )
    parser.add_argument(
        "--repo-root", type=Path, default=PROJECT_ROOT, help="Primary checkout root (default: this checkout)."
    )
    parser.add_argument(
        "--unit-dir",
        type=Path,
        default=Path.home() / ".config/systemd/user",
        help="User unit directory (default: ~/.config/systemd/user).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare rendered units with installed files; write nothing (default: false).",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Write units and reload the user manager (default: false)."
    )
    parser.add_argument(
        "--enable", action="store_true", help="With --apply, enable and start the timer (default: false)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check and args.apply:
        raise InstallError("--check and --apply are mutually exclusive")
    if args.enable and not args.apply:
        raise InstallError("--enable requires --apply")
    repo_root = args.repo_root.expanduser().resolve()
    if not (repo_root / ".git").is_dir():
        raise InstallError("repository root must be a primary checkout")
    rendered = render_units(repo_root)
    verify_units(rendered)
    if args.apply:
        return apply(rendered, args.unit_dir.expanduser(), enable=args.enable)
    return check(rendered, args.unit_dir.expanduser())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallError, OSError, subprocess.TimeoutExpired) as error:
        print(f"data-tier installer: {error}", file=sys.stderr)
        raise SystemExit(1) from error
