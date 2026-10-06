"""Host-local build/verify CLI. Console diagnostics contain no source text."""

import argparse
import json
import sys
import traceback
from pathlib import Path

from .build import execute
from .components import REGISTRY, load_components, merge_adapters
from .errors import BuildError
from .export import export_build
from .output import OutputGuard
from .request import init_request, read_request, repository_root


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise BuildError("cli_usage")


EPILOG = """Examples:
  .venv/bin/python -m scripts.projects.open_model_data.review_build init-request
  .venv/bin/python -m scripts.projects.open_model_data.review_build build --out "$TMPDIR/rb1" --components C9
  .venv/bin/python -m scripts.projects.open_model_data.review_build build --config "$TMPDIR/request.json" --out "$TMPDIR/rb1"
  .venv/bin/python -m scripts.projects.open_model_data.review_build verify --config "$TMPDIR/request.json" --out "$TMPDIR/rb1"
  .venv/bin/python -m scripts.projects.open_model_data.review_build export --from "$TMPDIR/rb1" --out "$TMPDIR/rb1-subset" --include source_id=ulif
Outputs: init-request creates a 0600 location-only request in a 0700 parent; build writes private JSONL records, candidates, attribution notices, accounting,
  metrics, manifest and README under --out only; verify compares all pinned artifacts
  and generates private generic must-fail inputs under --out/mutation-fixtures.
  Export writes unchanged selected record bytes, accounting, licence notices,
  a pinned register and its own manifest; it never reads live build inputs.
  Errors write tracebacks only to --out/logs after the output guard succeeds. No DB updates.
Exit codes: 0 = build/verification succeeded; 1 = a gate or input failed; 2 = CLI usage refused.
Related: docs/projects/open-model-data/REVIEW_BUILD.md; issue #9817, epic #6321.
"""


def default_config() -> Path:
    """The shared location-only request is available from every linked worktree."""
    return repository_root() / "batch_state/review_build/request.json"


def parser() -> Parser:
    result = Parser(
        description="Build or verify a deterministic, cited private review artifact.\n"
        "Use only on host-local pinned inputs; never for uploads or training claims.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = result.add_subparsers(
        dest="command",
        required=True,
        help="init-request (locations), build (write), verify (compare) or export (filter)",
    )
    initialize = commands.add_parser(
        "init-request",
        description="Create a private location-only v2 request.\nUse before the first build; existing files are never overwritten.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Initialize host-local input locations (0600 file, 0700 parent)",
    )
    initialize.add_argument(
        "--path",
        type=Path,
        default=default_config(),
        help="Request destination, e.g. $TMPDIR/rb1/request.json (default: shared batch_state/review_build/request.json)",
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
            type=Path,
            default=default_config(),
            help="Host-local omd-review-request.v2 location-only JSON (default: shared batch_state/review_build/request.json; create with init-request); e.g. $TMPDIR/request.json",
        )
        command.add_argument(
            "--components",
            nargs="+",
            action="extend",
            choices=sorted(REGISTRY),
            help="Component ids to build/verify, e.g. C3 C4; repeatable (default: all registered ids). Use the same selection for verify.",
        )
        command.add_argument(
            "--out",
            required=True,
            type=Path,
            help="Required host-only output directory outside all checkouts, e.g. $TMPDIR/rb1 (0700)",
        )
    export = commands.add_parser(
        "export",
        description="Export a subset of an already verified private build.\n"
        "Use the build's pinned register; never for uploads or live source extraction.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Filter a verified build by source, licence reference or permission status",
    )
    export.add_argument(
        "--from",
        dest="build",
        required=True,
        type=Path,
        help="Verified build directory, e.g. $TMPDIR/rb1; requires a matching verification receipt",
    )
    export.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Empty private export directory outside checkouts and the input build, e.g. $TMPDIR/rb1-subset",
    )
    for flag in ("include", "exclude"):
        export.add_argument(
            f"--{flag}",
            action="append",
            default=[],
            metavar="KEY=VALUE",
            help=f"Repeatable {flag} criterion: source_id, licence_ref or permission_status; "
            "e.g. source_id=ulif (default: none). Values within a key are alternatives; "
            "include keys combine with AND; any exclude match drops the whole record.",
        )
    return result


def main(argv: list[str] | None = None, *, _test_components=None) -> int:
    output = None
    try:
        args = parser().parse_args(argv)
        if args.command == "init-request":
            init_request(args.path)
            print(json.dumps({"status": "request_initialized"}, sort_keys=True))
            return 0
        protected = (Path(__file__).resolve().parents[4],)
        if args.command == "export":
            protected += (args.build.resolve(),)
        output = OutputGuard(args.out, protected)
        if args.command == "export":
            result = export_build(args.build, output, include=args.include, exclude=args.exclude)
            print(json.dumps(result, sort_keys=True))
            return 0
        output.write("verification.json", b'{"schema":"omd-review-verification.v1","status":"unverified"}\n')
        read_request(args.config)
        selected = args.components if args.components is not None else sorted(REGISTRY)
        loaded = load_components(selected, _test_overrides=_test_components)
        adapters = merge_adapters(*(component.adapters for component in loaded.values()))
        result = execute(
            args.config,
            output,
            verify=args.command == "verify",
            components=selected,
            adapters=adapters,
            component_objects=loaded,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        error = exc if isinstance(exc, BuildError) else BuildError("build_failure")
        if output is not None and error.code not in {"export_overlap", "export_output_not_empty"}:
            try:
                output.write("logs/failure.txt", traceback.format_exc().encode())
            except Exception:
                error = BuildError("error_log_unavailable")
        diagnostic = error.diagnostic()
        if error.code == "request_missing":
            diagnostic["hint"] = "Run init-request (or init-request --path P and use --config P)."
        elif error.code == "request_schema":
            diagnostic["hint"] = "Use omd-review-request.v2; v1 admission policy is refused. Run init-request."
        print(json.dumps(diagnostic, sort_keys=True), file=sys.stderr)
        return 2 if error.code == "cli_usage" else 1
    finally:
        if output is not None:
            output.close()


if __name__ == "__main__":
    raise SystemExit(main())
