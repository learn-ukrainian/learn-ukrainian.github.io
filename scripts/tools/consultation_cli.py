#!/usr/bin/env python3
"""CLI for managing consultation proposals.

Usage:
  # List pending proposals
  .venv/bin/python scripts/consultation_cli.py list

  # Show detail for a proposal
  .venv/bin/python scripts/consultation_cli.py show <filename>

  # Approve a proposal (validates FIND strings, applies patches)
  .venv/bin/python scripts/consultation_cli.py approve <filename>

  # Approve with dry-run (validate only, don't apply)
  .venv/bin/python scripts/consultation_cli.py approve <filename> --dry-run

  # Reject a proposal
  .venv/bin/python scripts/consultation_cli.py reject <filename> --reason "Not applicable"

  # Batch approve all high-confidence proposals
  .venv/bin/python scripts/consultation_cli.py approve-all --confidence high

  # Batch approve with dry-run
  .venv/bin/python scripts/consultation_cli.py approve-all --confidence high --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

# Resolve paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from pipeline.consultation import TemplateChange, apply_template_patch

QUEUE_DIR = PROJECT_ROOT / "claude_extensions" / "consultation-queue"
APPLIED_DIR = QUEUE_DIR / "applied"
REJECTED_DIR = QUEUE_DIR / "rejected"
TEMPLATE_DIR = PROJECT_ROOT / "claude_extensions" / "phases" / "gemini"

# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

CONFIDENCE_COLORS = {"high": GREEN, "medium": YELLOW, "low": RED}


def _parse_file(path: Path) -> dict | None:
    try:
        return yaml.safe_load(path.read_text("utf-8"))
    except Exception:
        return None


def _list_queue() -> list[tuple[Path, dict]]:
    if not QUEUE_DIR.exists():
        return []
    results = []
    for f in sorted(QUEUE_DIR.iterdir()):
        if f.is_file() and f.suffix == ".yaml":
            data = _parse_file(f)
            if data:
                results.append((f, data))
    return results


def _resolve_template(file_field: str) -> Path | None:
    if not file_field:
        return None
    candidate = TEMPLATE_DIR / Path(file_field).name
    try:
        resolved = candidate.resolve()
        if not resolved.is_relative_to(TEMPLATE_DIR.resolve()):
            return None
    except (ValueError, OSError):
        return None
    return candidate if candidate.exists() else None


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace to single spaces for fuzzy matching."""
    import re
    return re.sub(r"\s+", " ", text).strip()


def _find_matches(find_text: str, content: str) -> bool:
    """Check if FIND text exists in content (exact or whitespace-normalized)."""
    if find_text in content:
        return True
    return _normalize_ws(find_text) in _normalize_ws(content)


def _validate_finds(data: dict) -> list[str]:
    """Validate FIND strings. Returns list of error messages."""
    errors = []
    for i, change in enumerate(data.get("proposed_changes", []), 1):
        file_field = change.get("file", "")
        find_text = change.get("find", "")
        if not file_field or not find_text:
            continue
        tpl = _resolve_template(file_field)
        if not tpl:
            errors.append(f"  Change #{i}: template not found: {Path(file_field).name}")
            continue
        content = tpl.read_text("utf-8")
        if not _find_matches(find_text, content):
            errors.append(f"  Change #{i}: FIND string not found in {tpl.name}")
    return errors


def _apply(data: dict) -> tuple[int, list[str]]:
    """Apply patches. Returns (num_applied, errors)."""
    changes = [
        TemplateChange(
            find=c.get("find", ""),
            replace=c.get("replace", ""),
            file=c.get("file", ""),
            rationale=c.get("rationale", ""),
        )
        for c in data.get("proposed_changes", [])
    ]

    templates: dict[str, list[TemplateChange]] = {}
    for change in changes:
        name = Path(change.file).name if change.file else ""
        if name:
            templates.setdefault(name, []).append(change)

    total = 0
    errors = []
    now = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")

    for tpl_name, tpl_changes in templates.items():
        tpl_path = _resolve_template(tpl_name)
        if not tpl_path:
            errors.append(f"template not found: {tpl_name}")
            continue
        output = TEMPLATE_DIR / f"consultation-patched-{now}-{tpl_name}"
        ok, applied = apply_template_patch(tpl_path, tpl_changes, output)
        if not ok:
            errors.append(f"patch failed for {tpl_name}")
        else:
            total += applied
            if applied > 0:
                shutil.copy2(output, tpl_path)
                output.unlink()

    return total, errors


# ==================== COMMANDS ====================


def cmd_list(args: argparse.Namespace) -> None:
    items = _list_queue()
    if not items:
        print(f"{DIM}No pending proposals{RESET}")
        return

    print(f"{BOLD}Pending proposals ({len(items)}):{RESET}\n")
    for path, data in items:
        num = data.get("consultation_num", "?")
        conf = data.get("confidence", "?")
        color = CONFIDENCE_COLORS.get(conf, "")
        source = data.get("source_module", "?")
        n_changes = len(data.get("proposed_changes", []))
        root = (data.get("root_cause", "") or "")[:120]

        print(f"  {BOLD}{source} #{num}{RESET}  {color}[{conf}]{RESET}  {n_changes} changes")
        print(f"  {DIM}{path.name}{RESET}")
        print(f"  {DIM}{root}...{RESET}")
        print()


def cmd_show(args: argparse.Namespace) -> None:
    path = QUEUE_DIR / args.filename
    if not path.exists():
        # Check applied/rejected
        for subdir, label in [(APPLIED_DIR, "applied"), (REJECTED_DIR, "rejected")]:
            if (subdir / args.filename).exists():
                path = subdir / args.filename
                print(f"{DIM}(status: {label}){RESET}\n")
                break
        else:
            print(f"{RED}Not found: {args.filename}{RESET}")
            sys.exit(1)

    data = _parse_file(path)
    if not data:
        print(f"{RED}Failed to parse: {path}{RESET}")
        sys.exit(1)

    num = data.get("consultation_num", "?")
    conf = data.get("confidence", "?")
    color = CONFIDENCE_COLORS.get(conf, "")

    print(f"{BOLD}{data.get('source_module', '?')} — Consultation #{num}{RESET}")
    print(f"Confidence: {color}{conf}{RESET}")
    print(f"\n{BOLD}Root Cause:{RESET}")
    print(data.get("root_cause", ""))

    print(f"\n{BOLD}Proposed Changes ({len(data.get('proposed_changes', []))}):{RESET}")
    for i, c in enumerate(data.get("proposed_changes", []), 1):
        print(f"\n  {BOLD}Change #{i}{RESET} — {DIM}{c.get('file', '?')}{RESET}")
        print(f"  {RED}FIND:{RESET}")
        for line in c.get("find", "").splitlines():
            print(f"    {RED}- {line}{RESET}")
        print(f"  {GREEN}REPLACE:{RESET}")
        for line in c.get("replace", "").splitlines():
            print(f"    {GREEN}+ {line}{RESET}")
        if c.get("rationale"):
            print(f"  {DIM}{c['rationale']}{RESET}")

    if data.get("additional_notes"):
        print(f"\n{DIM}Notes: {data['additional_notes']}{RESET}")


def cmd_approve(args: argparse.Namespace) -> None:
    path = QUEUE_DIR / args.filename
    if not path.exists():
        if (APPLIED_DIR / args.filename).exists():
            print(f"{DIM}Already approved: {args.filename}{RESET}")
            return
        print(f"{RED}Not found: {args.filename}{RESET}")
        sys.exit(1)

    data = _parse_file(path)
    if not data:
        print(f"{RED}Malformed YAML: {args.filename}{RESET}")
        sys.exit(1)

    num = data.get("consultation_num", "?")
    source = data.get("source_module", "?")

    # Validate
    errors = _validate_finds(data)
    if errors:
        print(f"{RED}FIND string validation failed for {source} #{num}:{RESET}")
        for e in errors:
            print(e)
        sys.exit(1)

    if args.dry_run:
        print(f"{GREEN}DRY RUN: {source} #{num} — all FIND strings validated OK{RESET}")
        return

    # Apply
    applied, apply_errors = _apply(data)

    APPLIED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), APPLIED_DIR / args.filename)

    print(f"{GREEN}Approved: {source} #{num} — {applied} changes applied{RESET}")
    if apply_errors:
        for e in apply_errors:
            print(f"  {YELLOW}Warning: {e}{RESET}")


def cmd_reject(args: argparse.Namespace) -> None:
    path = QUEUE_DIR / args.filename
    if not path.exists():
        if (REJECTED_DIR / args.filename).exists():
            print(f"{DIM}Already rejected: {args.filename}{RESET}")
            return
        print(f"{RED}Not found: {args.filename}{RESET}")
        sys.exit(1)

    data = _parse_file(path)
    source = data.get("source_module", "?") if data else "?"
    num = data.get("consultation_num", "?") if data else "?"

    if args.reason and data:
        data["rejected_reason"] = args.reason
        data["rejected_at"] = datetime.now(UTC).isoformat()
        path.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
            "utf-8",
        )

    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), REJECTED_DIR / args.filename)
    print(f"{RED}Rejected: {source} #{num}{RESET}")
    if args.reason:
        print(f"  {DIM}Reason: {args.reason}{RESET}")


def cmd_approve_all(args: argparse.Namespace) -> None:
    items = _list_queue()
    if args.confidence:
        items = [(p, d) for p, d in items if d.get("confidence") == args.confidence]

    if not items:
        print(f"{DIM}No matching proposals{RESET}")
        return

    print(f"{BOLD}{'DRY RUN: ' if args.dry_run else ''}Approving {len(items)} proposals (confidence={args.confidence or 'any'}):{RESET}\n")

    approved = 0
    failed = 0
    for path, data in items:
        num = data.get("consultation_num", "?")
        source = data.get("source_module", "?")
        filename = path.name

        errors = _validate_finds(data)
        if errors:
            print(f"  {RED}SKIP {source} #{num} — FIND mismatch{RESET}")
            for e in errors:
                print(f"    {e}")
            failed += 1
            continue

        if args.dry_run:
            print(f"  {GREEN}OK {source} #{num} — validated{RESET}")
            approved += 1
            continue

        applied, apply_errors = _apply(data)
        APPLIED_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), APPLIED_DIR / filename)
        print(f"  {GREEN}Approved {source} #{num} — {applied} changes{RESET}")
        if apply_errors:
            for e in apply_errors:
                print(f"    {YELLOW}{e}{RESET}")
        approved += 1

    print(f"\n{BOLD}Result: {approved} approved, {failed} skipped{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage consultation proposals")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List pending proposals")

    p_show = sub.add_parser("show", help="Show proposal detail")
    p_show.add_argument("filename", help="Queue filename")

    p_approve = sub.add_parser("approve", help="Approve and apply a proposal")
    p_approve.add_argument("filename", help="Queue filename")
    p_approve.add_argument("--dry-run", action="store_true", help="Validate only, don't apply")

    p_reject = sub.add_parser("reject", help="Reject a proposal")
    p_reject.add_argument("filename", help="Queue filename")
    p_reject.add_argument("--reason", default="", help="Rejection reason")

    p_all = sub.add_parser("approve-all", help="Batch approve proposals")
    p_all.add_argument("--confidence", choices=["high", "medium", "low"], help="Filter by confidence")
    p_all.add_argument("--dry-run", action="store_true", help="Validate only, don't apply")

    args = parser.parse_args()
    commands = {
        "list": cmd_list,
        "show": cmd_show,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "approve-all": cmd_approve_all,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
