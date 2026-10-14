"""Muse DevOps and Harness/monitor recall canary using the shared mint and score implementation.

This CLI never opens, renews or closes a lease. A failed canary requires exiting
the driver; the launcher supervisor owns closure. No provider is invoked.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agents_extensions.shared.session_streams.inventory import stream_anchor_id
from scripts.common.epic_selector import validate_epic
from scripts.orchestration.launcher_aliases import load_launcher_aliases
from scripts.session_canary import grok_lane

ROOT = Path(__file__).resolve().parents[2]
MODEL = "muse-wonder-full-1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Examples:\n"
            "  <project-python> -m scripts.session_canary.muse_lane mint --epic devops\n"
            "  <project-python> -m scripts.session_canary.muse_lane score --epic devops --answers answers.json\n"
            "Outputs: recall artifacts and handoff diary; never a provider call or lease mutation.\n"
            "Exit codes: 0 PASS/minted; 1 missing anchors or artifacts; 2 refused/FAIL-HANDOFF.\n"
            "Related: docs/runbooks/muse-driver.md (#10553, #10511). The launcher owns the lease."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", type=Path, default=ROOT, help="Checkout root; default is this module's checkout")
    subparsers = parser.add_subparsers(dest="command", required=True)
    mint = subparsers.add_parser("mint", help="Freeze ten durable admitted-stream recall anchors")
    mint.add_argument("--epic", required=True, help="devops or monitor, including their supported launcher aliases")
    mint.add_argument("--stream", default=None, help="Optional canonical admitted stream; default from registry")
    mint.add_argument("--handoff", default=None, help="Handoff file override; default ranked Muse/INTERIM handoff")
    mint.add_argument(
        "--out-dir", default=None, help="Artifacts directory; default .claude/<canonical-stream>-epic/canary"
    )
    mint.add_argument("--stream-limit", type=int, default=40, help="Maximum stream entries read; default 40")
    mint.set_defaults(func=grok_lane.cmd_mint)
    score = subparsers.add_parser("score", help="Score recall; below 8/10 requires handoff and exit")
    score.add_argument("--epic", required=True, help="devops or monitor, including their supported launcher aliases")
    score.add_argument("--stream", default=None, help="Optional canonical admitted stream; default from registry")
    score.add_argument("--handoff", default=None, help="Diary override; default the handoff bound by mint")
    score.add_argument(
        "--out-dir", default=None, help="Artifacts directory; default .claude/<canonical-stream>-epic/canary"
    )
    score.add_argument("--answers", required=True, help="JSON anchor-id to recalled answer map, e.g. answers.json")
    score.add_argument("--context-tokens", type=int, default=0, help="Observed context tokens; default 0 (unknown)")
    score.set_defaults(
        func=grok_lane.cmd_score,
        model=MODEL,
        pass_ratio=grok_lane.DEFAULT_PASS_RATIO,
        threshold=grok_lane.DEFAULT_SIM_THRESHOLD,
        no_hydrate=False,
    )
    parser.set_defaults(preferred=["MUSE-DRIVER-HANDOFF.md", "INTERIM-DRIVER-HANDOFF.md"])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.epic = load_launcher_aliases().get(args.epic, args.epic)
        validate_epic(args.epic)
        from scripts.lib.rules_core import resolve_seat
        from scripts.orchestration.driver_agent_type import resolve_driver_agent_type

        if args.epic not in {"devops", "monitor"} or resolve_seat(lane=args.epic, provider="muse") != "core":
            raise ValueError("MUSE_STREAM_NOT_ADMITTED")
        if resolve_driver_agent_type(args.epic, provider="muse") != "infra-orchestrator":
            raise ValueError("MUSE_LANE_CLASSIFICATION_UNKNOWN")
        expected = stream_anchor_id(args.epic, ROOT)
        if args.stream not in {None, expected}:
            raise ValueError("MUSE_STREAM_NOT_ADMITTED")
        args.stream = expected
        result = int(args.func(args))
        if args.command == "score" and result != 0:
            print("ACTION: exit this Muse driver; the launcher closes its lease.", file=sys.stderr)
        return result
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
