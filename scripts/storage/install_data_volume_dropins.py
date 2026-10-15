"""Preview or install systemd user service guards for the data volume.

Drop-ins are written to a temporary file and renamed into place; a symlinked
drop-in, or a symlink in any directory from the home directory (or ``/``) down
to a drop-in directory, is refused in preview and apply alike.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.common.safe_unit_install import InstallError, install_unit, load_unit

TEMPLATE_ROOT = REPO_ROOT / "packaging" / "systemd" / "dropins"
DEFAULT_DESTINATION = Path("/etc/systemd/user")
# Every user's manager reads /etc/systemd/user, so drop-ins stay world-readable.
DROPIN_MODE = 0o644


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
            "thirteen data-volume.conf files (mode 0644, replaced by rename) under the destination; "
            "a symlinked drop-in or a symlinked directory on the way to it is refused.\n"
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
    if len(templates) != 13:
        parser.error(f"expected thirteen drop-in templates, found {len(templates)}")
    for template in templates:
        content = (
            template.read_text(encoding="utf-8")
            .replace("@REPO_ROOT@", root)
            .replace("@PRIVATE_ROOT@", private_root)
            # Intentional: the drop-in names this primary checkout's interpreter.
            # --apply refuses a dispatch worktree.
            .replace("@PYTHON@", str(REPO_ROOT / ".venv" / "bin" / "python"))
        )
        target = args.destination / template.parent.name / template.name
        try:
            if args.apply:
                install_unit(target, content.encode("utf-8"), mode=DROPIN_MODE)
            else:
                load_unit(target)
        except (InstallError, OSError) as exc:
            parser.exit(1, f"cannot {'write' if args.apply else 'inspect'} {target}: {exc}\n")
        print(f"{target}\n{content}", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
