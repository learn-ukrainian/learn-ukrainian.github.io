"""Host-local build/verify CLI. Console diagnostics contain no source text."""

import argparse
import json
import sys
import traceback
from pathlib import Path

from .build import execute
from .components import REGISTRY, load_components, merge_adapters
from .errors import BuildError, require
from .output import OutputGuard


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise BuildError("cli_usage")


EPILOG = """Examples:
  .venv/bin/python -m scripts.projects.open_model_data.review_build build --out "$TMPDIR/rb1" --components C9
  .venv/bin/python -m scripts.projects.open_model_data.review_build build --config "$TMPDIR/request.json" --out "$TMPDIR/rb1"
  .venv/bin/python -m scripts.projects.open_model_data.review_build verify --config "$TMPDIR/request.json" --out "$TMPDIR/rb1"
Outputs: build writes private JSONL records, candidates, attribution notices, accounting,
  metrics, manifest and README under --out only; verify compares all pinned artifacts
  and generates private generic must-fail inputs under --out/mutation-fixtures.
  Errors write tracebacks only to --out/logs after the output guard succeeds. No DB updates.
Exit codes: 0 = build/verification succeeded; 1 = a gate or input failed; 2 = CLI usage refused.
Related: docs/projects/open-model-data/REVIEW_BUILD.md; issue #9817, epic #6321.
"""


def default_config() -> Path:
    """The shared staged request is available from every linked worktree."""
    root = Path(__file__).resolve().parents[4]
    git = root / ".git"
    if git.is_file():
        text = git.read_text().strip()
        if not text.startswith("gitdir: "):
            raise BuildError("code_identity")
        git = (root / text[8:]).resolve()
        common = git / "commondir"
        if common.exists():
            git = (git / common.read_text().strip()).resolve()
        root = git.parent
    return root / "batch_state/review_build/request.json"


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
            type=Path,
            default=default_config(),
            help="Host-local omd-review-request.v1 JSON descriptor (default: shared batch_state/review_build/request.json staged by component integration); e.g. $TMPDIR/request.json",
        )
        command.add_argument(
            "--components",
            nargs="+",
            action="extend",
            choices=sorted(REGISTRY),
            help="Component ids to build/verify, e.g. C3 C4; repeatable (default: all in config). Use the same selection for verify.",
        )
        command.add_argument(
            "--out",
            required=True,
            type=Path,
            help="Required host-only output directory outside all checkouts, e.g. $TMPDIR/rb1 (0700)",
        )
    return result


def main(argv: list[str] | None = None, *, _test_components=None) -> int:
    output = None
    try:
        args = parser().parse_args(argv)
        output = OutputGuard(args.out, (Path(__file__).resolve().parents[4],))
        request = json.loads(args.config.read_bytes())
        selected = args.components if args.components is not None else list(request["components"])
        require(bool(selected) and set(selected) <= set(request["components"]), "component_selection")
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
