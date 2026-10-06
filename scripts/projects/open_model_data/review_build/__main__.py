"""Host-local build/verify CLI. Console diagnostics contain no source text."""

import argparse
import json
import sys
import traceback
from pathlib import Path

from .build import execute
from .errors import BuildError
from .output import OutputGuard


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise BuildError("cli_usage")


EPILOG = """Examples:
  .venv/bin/python -m scripts.projects.open_model_data.review_build build --config "$TMPDIR/request.json" --out "$TMPDIR/rb1"
  .venv/bin/python -m scripts.projects.open_model_data.review_build verify --config "$TMPDIR/request.json" --out "$TMPDIR/rb1"
Outputs: build writes private JSONL records, candidates, attribution notices, accounting,
  metrics, manifest and README under --out only; verify compares all pinned artifacts.
  Errors write tracebacks only to --out/logs after the output guard succeeds. No DB updates.
Exit codes: 0 = build/verification succeeded; 1 = a gate or input failed; 2 = CLI usage refused.
Related: docs/projects/open-model-data/REVIEW_BUILD.md; issue #9817, epic #6321.
"""


def parser() -> Parser:
    result = Parser(
        description="Build or verify a deterministic, cited private review artifact.\n"
        "Use only on host-local pinned inputs; never for uploads or training claims.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = result.add_subparsers(
        dest="command", required=True, help="build (write) or verify (re-read and compare)"
    )
    for name in ("build", "verify"):
        command = commands.add_parser(
            name,
            description=f"{name.capitalize()} a private review artifact.\n"
            "Use reviewed component specs; do not use draft catalogs or repository output paths.",
            epilog=EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="Write private artifacts" if name == "build" else "Recheck inputs and artifact bytes",
        )
        command.add_argument(
            "--config",
            required=True,
            type=Path,
            help="Required host-local omd-review-request.v1 JSON descriptor, e.g. $TMPDIR/request.json",
        )
        command.add_argument(
            "--out",
            required=True,
            type=Path,
            help="Required host-only output directory outside all checkouts, e.g. $TMPDIR/rb1 (0700)",
        )
    return result


def main(argv: list[str] | None = None) -> int:
    output = None
    try:
        args = parser().parse_args(argv)
        output = OutputGuard(args.out)
        result = execute(args.config, output, verify=args.command == "verify")
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        error = exc if isinstance(exc, BuildError) else BuildError("build_failure")
        if output is not None:
            try:
                output.write("logs/failure.txt", traceback.format_exc().encode())
            except Exception:
                error = BuildError("error_log_unavailable")
        print(json.dumps(error.diagnostic(), sort_keys=True), file=sys.stderr)
        return 2 if error.code == "cli_usage" else 1
    finally:
        if output is not None:
            output.close()


if __name__ == "__main__":
    raise SystemExit(main())
