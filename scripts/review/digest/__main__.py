"""CLI entry point for module digest generator (#8430 WP 15 Part R2a).

Usage:
  .venv/bin/python -m scripts.review.digest <level> <slug> --up-to <n> [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import codes
from .error import DigestError
from .generator import ALLOWED_LEVELS, build_digest, check_digest, write_digest


def build_parser() -> argparse.ArgumentParser:
    """Build argparse parser meeting agents_extensions/shared/rules/cli-help-standard.md."""
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review.digest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Generate or verify deterministic module digest across lessons 1...n-1 of a module.\n"
            "Use during lesson review prep to aggregate recorded state; do NOT use to alter curriculum content."
        ),
        epilog=(
            "Outputs:\n"
            "  Writes curriculum/l2-uk-en/evidence/<level>/_state/<slug>/digest-upto-<n>.yaml and its .lock sidecar\n"
            "  (read-only under --check; no files written or modified).\n\n"
            "Exit codes:\n"
            "  0 = success (digest written or --check verified byte-stable)\n"
            "  1 = failure (missing inputs, lock mismatch, byte drift, or schema error)\n\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.digest a1 mod-01 --up-to 3\n"
            "  .venv/bin/python -m scripts.review.digest a1 mod-01 --up-to 3 --check\n"
            "  .venv/bin/python -m scripts.review.digest a1 mod-01 --up-to 1\n\n"
            "Related:\n"
            "  Issues #8430 (WP 15 Part R2a), #8397. Schemas: schemas/module-digest-v1.schema.json.\n\n"
            "Outcome codes:\n"
            + codes.help_text()
        ),
    )

    parser.add_argument(
        "level",
        choices=ALLOWED_LEVELS,
        help="CEFR level directory under curriculum/l2-uk-en/, e.g. a1, a2",
    )
    parser.add_argument(
        "slug",
        help="module slug identifying plan and state directory, e.g. mod-01",
    )
    parser.add_argument(
        "--up-to",
        type=int,
        required=True,
        help="lesson number bound integer (1-indexed); digests lessons 1...n-1, e.g. --up-to 3",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="recompute digest and verify byte-stability against disk without writing (default: False)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="optional repository root directory override (default: repository root)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI execution entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.check:
            path, sha256 = check_digest(
                args.level,
                args.slug,
                args.up_to,
                repo_root=args.repo_root,
            )
            print(f"ok: {path.name} verified byte-stable ({sha256})")
        else:
            doc = build_digest(
                args.level,
                args.slug,
                args.up_to,
                repo_root=args.repo_root,
            )
            path, sha256 = write_digest(doc, repo_root=args.repo_root)
            print(f"ok: wrote {path} ({sha256})")
        return 0
    except DigestError as exc:
        print(f"error: {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: unhandled_exception: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
