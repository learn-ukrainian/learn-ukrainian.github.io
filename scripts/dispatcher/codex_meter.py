"""Estimate one bound Codex account's spend from the dispatcher's shared task records."""

from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal
from pathlib import Path

from scripts.agent_runtime.codex_accounts import (
    CODEX_ACCOUNT_ALIASES,
    CODEX_BOUND_ACCOUNTS,
    CodexAccountRefused,
    load_codex_account_binding,
    resolve_codex_account_label,
)
from scripts.common.task_store_paths import tasks_dir
from scripts.orchestration.task_record_store import iter_task_records, read_task_record

# Standard USD per million tokens, matching scripts/config/model_catalog.yaml.
# Luna cached input: https://developers.openai.com/api/docs/models/gpt-6-luna
# These are standard-rate estimates, excluding cache writes, tools and service-tier premiums.
STANDARD_RATES = {
    "gpt-6-luna": (Decimal("0.10"), Decimal("0.01"), Decimal("0.50")),
    "gpt-6.1-terra": (Decimal("1"), Decimal("0.05"), Decimal("5")),
    "gpt-6.1-sol": (Decimal("2"), Decimal("0.10"), Decimal("10")),
}


def task_cost(record: dict) -> Decimal:
    """Codex input_tokens includes cached_input_tokens; output includes reasoning."""
    rates = STANDARD_RATES.get(record.get("model"))
    usage = record.get("usage")
    if rates is None or not isinstance(usage, dict):
        raise ValueError("price or usage unavailable")
    tokens = [usage.get(name) for name in ("input_tokens", "cached_input_tokens", "output_tokens")]
    if any(type(value) is not int or value < 0 for value in tokens):
        raise ValueError("invalid token usage")
    input_tokens, cached, output = tokens
    if cached > input_tokens:
        raise ValueError("invalid cached input usage")
    return ((input_tokens - cached) * rates[0] + cached * rates[1] + output * rates[2]) / 1_000_000


def estimate(directory: Path, budget: Decimal, account: str = "api") -> dict:
    spent, priced, unknown, pending = Decimal(0), 0, 0, 0
    if not directory.is_dir():
        raise ValueError("task store unavailable")
    for path in iter_task_records(directory, include_archive=True):
        try:
            record = read_task_record(path)
            if record is None:
                continue
        except (OSError, ValueError):
            unknown += 1
            continue
        if not isinstance(record, dict):
            unknown += 1
            continue
        if record.get("agent") != "codex" or record.get("codex_account") != account:
            continue
        if record.get("status") in ("spawning", "running") and record.get("usage") is None:
            pending += 1
            continue
        try:
            spent += task_cost(record)
            priced += 1
        except ValueError:
            unknown += 1
    return {"spent_usd": str(spent), "remaining_usd": str(budget - spent) if not unknown else None,
            "budget_usd": str(budget), "priced_tasks": priced, "unknown_tasks": unknown,
            "pending_tasks": pending, "basis": "estimate from our own logs at standard token prices"}


def main(argv: list[str] | None = None) -> int:
    # Named as they are run: this module by its import name, the dispatcher and catalog by checkout path.
    entry = f"-m {__spec__.name}" if __spec__ is not None else os.fspath(__file__)
    package = Path(__file__).absolute().parents[1].name
    dispatch, catalog = f"{package}/dispatch.py", f"{package}/config/model_catalog.yaml"
    parser = argparse.ArgumentParser(
        description="Estimate spend and remaining budget for one bound Codex account's dispatch tasks.\n"
        "Use for fleet usage meters, not provider billing or an authoritative credit balance.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Examples:\n  .venv/bin/python {entry}\n"
        f"  .venv/bin/python {entry} --json\n"
        f"  .venv/bin/python {entry} --account b-sub\n"
        "Outputs: stdout only; reads task records and the private account binding, never credentials.\n"
        "Exit codes: 0 estimate printed; 1 configuration, store or usage incomplete.\n"
        f"Related: {dispatch} dispatch --codex-account api|b-sub|b-api; {catalog}.",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON (default: one meter line)")
    bound = (*CODEX_BOUND_ACCOUNTS, *(name for name, label in CODEX_ACCOUNT_ALIASES.items() if label in CODEX_BOUND_ACCOUNTS))
    parser.add_argument("--account", choices=bound, default="api",
                        help="Bound Codex route to meter: api (account a), b-sub or b-api (default: api)")
    args = parser.parse_args(argv)
    args.account = resolve_codex_account_label(args.account)
    meter = f"{'Codex API' if args.account.endswith('api') else 'Codex subscription'} [{args.account}]"
    try:
        report = estimate(tasks_dir(), load_codex_account_binding(label=args.account).budget_usd, args.account)
    except (CodexAccountRefused, OSError, ValueError):
        print(f"{meter}: UNKNOWN (binding or task store unavailable)")
        return 1
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        remaining = "UNKNOWN" if report["remaining_usd"] is None else f"${Decimal(report['remaining_usd']):.6f}"
        print(f"{meter}: spent ${Decimal(report['spent_usd']):.6f}; remaining {remaining} "
              f"of ${Decimal(report['budget_usd']):.2f}; {report['basis']}; "
              f"{report['priced_tasks']} priced, {report['pending_tasks']} pending, {report['unknown_tasks']} unknown")
    return 1 if report["unknown_tasks"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
