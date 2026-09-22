"""CLI entry point for scripts.curriculum.evidence: build-words and words-verify."""

from __future__ import annotations

import argparse
import sys

from . import codes, verify, words


def main(argv: list[str] | None = None) -> int:
    args_list = sys.argv[1:] if argv is None else argv

    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.evidence",
        description=(
            "Curriculum evidence CLI: build and verify source-grounded word stores.\n"
            "Use to create per-level dictionary evidence or verify its integrity against locks."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Commands:\n"
            "  build-words   Build or update a level word store from a request YAML\n"
            "  words-verify  Verify integrity of a level word store against sources and ledger\n\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-words a1 --request req.yaml\n"
            "  .venv/bin/python -m scripts.curriculum.evidence words-verify a1\n\n"
            "Outcome Codes:\n"
            f"{codes.help_text()}\n"
        ),
    )
    parser.add_argument(
        "command", choices=["build-words", "build_words", "words-verify", "words_verify"], help="Command to run"
    )
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the command")

    if not args_list or args_list[0] in {"-h", "--help"}:
        parser.print_help()
        return 0

    cmd = args_list[0]
    rest = args_list[1:]

    if cmd in {"build-words", "build_words"}:
        return words.main(rest)
    elif cmd in {"words-verify", "words_verify"}:
        return verify.main(rest)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
