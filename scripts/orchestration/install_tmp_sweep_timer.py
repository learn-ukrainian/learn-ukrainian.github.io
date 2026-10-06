"""Render and install the daily temp-sweep systemd user timer (#9737).

Use --check before installation; use --apply after the branch has merged.
--enable starts the timer only when paired with --apply. The unit directory
and unit files are never followed through symlinks: a symlinked unit file, or
a symlink anywhere from the home directory down to the unit directory, is
refused, and units are replaced by rename within the directory.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from scripts.common.safe_unit_install import InstallError, open_unit_dir, read_unit, write_unit
from scripts.orchestration.install_data_tier_timer import systemctl_user, verify_units

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = PROJECT_ROOT / "packaging" / "systemd"
UNITS = ("learn-ukrainian-tmp-sweep.service", "learn-ukrainian-tmp-sweep.timer")


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


def check(rendered: dict[str, str], unit_dir: Path) -> int:
    dir_fd = open_unit_dir(unit_dir)
    try:
        installed = {name: read_unit(dir_fd, name) if dir_fd is not None else None for name in rendered}
    finally:
        if dir_fd is not None:
            os.close(dir_fd)
    differences = [name for name, content in rendered.items() if (installed[name] or (b"",))[0] != content.encode()]
    if differences:
        print("unit drift: " + ", ".join(differences))
        return 1
    print("units current: " + ", ".join(UNITS))
    return 0


def apply(rendered: dict[str, str], unit_dir: Path, *, enable: bool) -> int:
    dir_fd = open_unit_dir(unit_dir, create=True)
    if dir_fd is None:
        raise InstallError("unit directory vanished during installation")
    changed = 0
    try:
        for name, content in rendered.items():
            if read_unit(dir_fd, name) == (content.encode(), 0o600):
                continue
            write_unit(dir_fd, name, content.encode(), mode=0o600)
            changed += 1
    finally:
        os.close(dir_fd)
    systemctl_user("daemon-reload")
    if enable:
        systemctl_user("enable", "--now", UNITS[1])
    print(f"wrote {changed} unit(s); daemon reloaded; timer {'enabled' if enable else 'not enabled'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Install the daily temp-sweep systemd user units (unattributed scratch reap + batch_state report).\n"
            "Use --check to compare installed units, --apply to write them, and --enable after merge."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --check\n"
            "  .venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --apply\n"
            "  .venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --apply --enable\n"
            "Outputs: owner-only (0600) units in the user systemd directory, replaced by rename; a symlinked "
            "unit file, or a symlink in any directory from home down to the unit directory, is refused; "
            "--apply reloads the user manager, --enable starts the timer.\n"
            "Exit codes: 0 = current or applied; 1 = drift or installation failure; 2 = invalid usage "
            "(--check with --apply, --enable without --apply, or a non-primary --repo-root).\n"
            "Related: issue #9737, docs/runbooks/tmp-retention.md and packaging/systemd/learn-ukrainian-tmp-sweep.*."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Primary checkout rendered into the units (default: this checkout; example: the main clone path).",
    )
    parser.add_argument(
        "--unit-dir",
        type=Path,
        default=Path.home() / ".config/systemd/user",
        help=(
            "User unit directory; no directory from home down to it may be a symlink (default: ~/.config/systemd/user)."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Compare rendered units with installed files; write nothing (default mode when --apply is absent).",
    )
    mode.add_argument("--apply", action="store_true", help="Write units and reload the user manager (default: false).")
    parser.add_argument(
        "--enable", action="store_true", help="With --apply, enable and start the timer (default: false)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.enable and not args.apply:
        parser.error("--enable requires --apply")
    repo_root = args.repo_root.expanduser().resolve()
    if not (repo_root / ".git").is_dir():
        parser.error("--repo-root must be a primary checkout (its .git is a directory)")
    rendered = render_units(repo_root)
    verify_units(rendered)
    if args.apply:
        return apply(rendered, args.unit_dir.expanduser(), enable=args.enable)
    return check(rendered, args.unit_dir.expanduser())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallError, OSError, subprocess.TimeoutExpired) as error:
        print(f"tmp-sweep installer: {error}", file=sys.stderr)
        raise SystemExit(1) from error
