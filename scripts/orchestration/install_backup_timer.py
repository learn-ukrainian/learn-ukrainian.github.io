#!/usr/bin/env python3
"""Install the Learn Ukrainian backup systemd user units (preview by default).

Renders the learn-ukrainian-backup{,-retention}.{service,timer} templates from
packaging/systemd/ with @REPO_ROOT@ replaced by the primary checkout, verifies
them with systemd-analyze when available, and previews the result. Nothing is
written unless --apply is given; --enable (with --apply) also enables and
starts the two timers.
"""

from __future__ import annotations

import argparse
import difflib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = PROJECT_ROOT / "packaging" / "systemd"
UNIT_NAMES = (
    "learn-ukrainian-backup.service",
    "learn-ukrainian-backup.timer",
    "learn-ukrainian-backup-retention.service",
    "learn-ukrainian-backup-retention.timer",
)
TIMER_NAMES = tuple(name for name in UNIT_NAMES if name.endswith(".timer"))
REPO_ROOT_PLACEHOLDER = "@REPO_ROOT@"


class InstallError(RuntimeError):
    """The requested unit state could not be produced."""


def render_unit(template_path: Path, repo_root: Path) -> str:
    text = template_path.read_text(encoding="utf-8")
    if REPO_ROOT_PLACEHOLDER not in text and template_path.suffix == ".service":
        raise InstallError(f"{template_path.name} has no {REPO_ROOT_PLACEHOLDER} placeholder")
    return text.replace(REPO_ROOT_PLACEHOLDER, str(repo_root))


def render_units(repo_root: Path) -> dict[str, str]:
    rendered: dict[str, str] = {}
    for name in UNIT_NAMES:
        template = TEMPLATE_DIR / name
        if not template.is_file():
            raise InstallError(f"missing unit template: {template}")
        rendered[name] = render_unit(template, repo_root)
    return rendered


def verify_units(rendered: dict[str, str], work_dir: Path) -> str:
    analyzer = shutil.which("systemd-analyze")
    if analyzer is None:
        return "systemd-analyze unavailable; skipped verify"
    for name, text in rendered.items():
        (work_dir / name).write_text(text, encoding="utf-8")
    result = subprocess.run(
        [analyzer, "verify", *(str(work_dir / name) for name in UNIT_NAMES)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    detail = (result.stderr or result.stdout).strip()
    if result.returncode != 0:
        raise InstallError(f"systemd-analyze verify failed: {detail}")
    return "systemd-analyze verify: clean" + (f" ({detail})" if detail else "")


def systemctl_user(*arguments: str) -> subprocess.CompletedProcess[str]:
    systemctl = shutil.which("systemctl")
    if systemctl is None:
        raise InstallError("systemctl is unavailable; a Linux user manager is required")
    return subprocess.run(
        [systemctl, "--user", *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def preview(rendered: dict[str, str], unit_dir: Path) -> int:
    for name, text in rendered.items():
        destination = unit_dir / name
        print(f"--- {destination}")
        if destination.is_file() and destination.read_text(encoding="utf-8") == text:
            print("    (unchanged)")
            continue
        if destination.is_file():
            diff = difflib.unified_diff(
                destination.read_text(encoding="utf-8").splitlines(),
                text.splitlines(),
                fromfile=str(destination),
                tofile=f"{destination} (rendered)",
                lineterm="",
            )
            print("\n".join(diff))
        else:
            print(text, end="")
    print("Preview only. Re-run with --apply to write these units.")
    return 0


def apply(rendered: dict[str, str], unit_dir: Path, enable: bool) -> int:
    unit_dir.mkdir(parents=True, exist_ok=True)
    changed = []
    for name, text in rendered.items():
        destination = unit_dir / name
        if destination.is_file() and destination.read_text(encoding="utf-8") == text:
            continue
        destination.write_text(text, encoding="utf-8")
        os.chmod(destination, 0o644)
        changed.append(name)
    reload = systemctl_user("daemon-reload")
    if reload.returncode != 0:
        raise InstallError(f"systemctl --user daemon-reload failed: {reload.stderr.strip()}")
    print(f"wrote {len(changed)} unit(s) to {unit_dir}; daemon reloaded")
    if enable:
        result = systemctl_user("enable", "--now", *TIMER_NAMES)
        if result.returncode != 0:
            raise InstallError(f"systemctl --user enable failed: {result.stderr.strip()}")
        print(f"enabled and started: {', '.join(TIMER_NAMES)}")
    else:
        print(f"next step: systemctl --user enable --now {' '.join(TIMER_NAMES)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=PROJECT_ROOT,
        help="primary checkout substituted for @REPO_ROOT@ (default: this checkout)",
    )
    parser.add_argument(
        "--unit-dir",
        type=Path,
        default=Path.home() / ".config" / "systemd" / "user",
        help="systemd user unit directory (default: ~/.config/systemd/user)",
    )
    parser.add_argument("--apply", action="store_true", help="write the units and reload systemd")
    parser.add_argument(
        "--enable",
        action="store_true",
        help="with --apply, also enable and start the timers",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.enable and not args.apply:
        raise InstallError("--enable only makes sense together with --apply")
    repo_root = args.repo_root.expanduser().resolve()
    if not (repo_root / ".git").exists():
        raise InstallError(f"repository root is not a checkout: {repo_root}")
    rendered = render_units(repo_root)
    with tempfile.TemporaryDirectory(prefix="learn-ukrainian-backup-units.") as work_dir:
        print(verify_units(rendered, work_dir=Path(work_dir)))
    if args.apply:
        return apply(rendered, args.unit_dir.expanduser(), args.enable)
    return preview(rendered, args.unit_dir.expanduser())


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InstallError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
