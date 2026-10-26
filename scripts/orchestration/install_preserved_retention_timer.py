"""Install the daily C-2481 backstop. Enable only after review and merge."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from scripts.common.safe_unit_install import InstallError, open_unit_dir, read_unit, write_unit
from scripts.orchestration.install_data_tier_timer import systemctl_user, verify_units

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = PROJECT_ROOT / "packaging/systemd"
UNITS = ("learn-ukrainian-preserved-retention.service", "learn-ukrainian-preserved-retention.timer")


def render_units(repo_root: Path) -> dict[str, str]:
    return {name: (TEMPLATE_DIR / name).read_text().replace("@REPO_ROOT@", str(repo_root)) for name in UNITS}


def install(rendered: dict[str, str], unit_dir: Path, *, apply: bool, enable: bool) -> int:
    fd = open_unit_dir(unit_dir, create=apply)
    if apply and fd is None:
        raise InstallError("unit directory vanished during installation")
    drift = False
    try:
        for name, content in rendered.items():
            current = read_unit(fd, name) if fd is not None else None
            if current == (content.encode(), 0o600):
                continue
            drift = True
            if apply:
                write_unit(fd, name, content.encode(), mode=0o600)
    finally:
        if fd is not None:
            os.close(fd)
    if apply:
        systemctl_user("daemon-reload")
        if enable:
            systemctl_user("enable", "--now", UNITS[1])
    print("units applied" if apply else "unit drift" if drift else "units current")
    return int(drift and not apply)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install daily preserved residue backstop user units. Default: read-only check. Enable after merge.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n  .venv/bin/python -m scripts.orchestration.install_preserved_retention_timer --check\n"
            "  .venv/bin/python -m scripts.orchestration.install_preserved_retention_timer --apply --enable\n"
            "Outputs: owner-only user units; --apply reloads systemd; --enable starts the timer.\n"
            "Exit codes: 0 current/applied, 1 drift or install error, 2 invalid usage.\n"
            "Related: C-2481, scripts.hygiene.preserved_retention, install_tmp_sweep_timer."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Primary checkout rendered into units (default: this checkout; example: primary clone).",
    )
    parser.add_argument(
        "--unit-dir",
        type=Path,
        default=Path.home() / ".config/systemd/user",
        help="User unit directory, no symlinks (default: ~/.config/systemd/user; example: fixture/units).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Compare without writing (default).")
    mode.add_argument("--apply", action="store_true", help="Write units and reload systemd (default: false).")
    parser.add_argument(
        "--enable", action="store_true", help="With --apply, enable timer after merge (default: false)."
    )
    args = parser.parse_args(argv)
    if args.enable and not args.apply:
        parser.error("--enable requires --apply")
    repo = args.repo_root.expanduser().resolve()
    if not (repo / ".git").is_dir():
        parser.error("--repo-root must be a primary checkout")
    rendered = render_units(repo)
    verify_units(rendered)
    return install(rendered, args.unit_dir.expanduser(), apply=args.apply, enable=args.enable)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"preserved-retention installer: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
