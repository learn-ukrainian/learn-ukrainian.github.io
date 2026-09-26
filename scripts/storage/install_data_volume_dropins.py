"""Preview or install systemd user service guards for the data volume."""

from __future__ import annotations

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "packaging" / "systemd" / "dropins"
DEFAULT_DESTINATION = Path("/etc/systemd/user")


def _is_primary_checkout() -> bool:
    return ".worktrees" not in REPO_ROOT.parts and (REPO_ROOT / ".git").is_dir()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or install guarded ExecStart drop-ins for every Learn Ukrainian "
            "user service and timer service.\n"
            "Use before the data-volume migration window; --apply writes systemd "
            "configuration, but does not reload or start units."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python "
            "scripts/storage/install_data_volume_dropins.py\n"
            "  .venv/bin/python "
            "scripts/storage/install_data_volume_dropins.py --apply\n"
            "Outputs: prints each target and complete rendered content; --apply writes "
            "ten data-volume.conf files under the destination.\n"
            "Exit codes: 0 on success; 1 for an unsafe or failed write; 2 for "
            "invalid arguments.\n"
            "Related: packaging/systemd/dropins/, "
            "docs/runbooks/storage-topology.md, issue #8804."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the rendered drop-ins (default: preview only; no writes).",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION,
        help="Systemd user-unit directory (default: /etc/systemd/user; example: /tmp/user-units).",
    )
    args = parser.parse_args()

    if args.apply and not _is_primary_checkout():
        parser.error("--apply must run from the primary checkout, not a dispatch worktree")

    root = str(REPO_ROOT)
    private_root = str(REPO_ROOT.parent / "learn-ukrainian-infra-private")
    if any(char.isspace() or char == "%" for char in root + private_root):
        parser.error("repository paths cannot contain whitespace or systemd percent specifiers")

    templates = sorted(TEMPLATE_ROOT.glob("*.service.d/data-volume.conf"))
    if len(templates) != 10:
        parser.error(f"expected ten drop-in templates, found {len(templates)}")
    for template in templates:
        content = (
            template.read_text(encoding="utf-8").replace("@REPO_ROOT@", root).replace("@PRIVATE_ROOT@", private_root)
        )
        target = args.destination / template.parent.name / template.name
        print(f"{target}\n{content}", end="")
        if args.apply:
            if target.is_symlink() or target.parent.is_symlink():
                parser.error(f"refusing symlink destination: {target}")
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            except OSError as exc:
                parser.exit(1, f"cannot write {target}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
