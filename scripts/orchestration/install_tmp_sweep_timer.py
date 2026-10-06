"""Render and install the daily temp-sweep systemd user timer (#9737).

Use --check before installation; use --apply after the branch has merged.
--enable starts the timer only when paired with --apply.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from scripts.orchestration.install_data_tier_timer import InstallError, systemctl_user, verify_units

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
    differences = [
        name
        for name, content in rendered.items()
        if not (unit_dir / name).is_file() or (unit_dir / name).read_text(encoding="utf-8") != content
    ]
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
            "Install the daily temp-sweep systemd user units (unattributed scratch reap + batch_state report).\n"
            "Use --check to compare installed units, --apply to write them, and --enable after merge."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  <project-python> -m scripts.orchestration.install_tmp_sweep_timer --check\n"
            "  <project-python> -m scripts.orchestration.install_tmp_sweep_timer --apply --enable\n"
            "Outputs: owner-only units in the user systemd directory; --apply reloads the user manager.\n"
            "Exit codes: 0 = current or applied; 1 = drift or installation failure; 2 = invalid usage.\n"
            "Related: issue #9737, docs/runbooks/tmp-retention.md and packaging/systemd/learn-ukrainian-tmp-sweep.*."
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
        print(f"tmp-sweep installer: {error}", file=sys.stderr)
        raise SystemExit(1) from error
