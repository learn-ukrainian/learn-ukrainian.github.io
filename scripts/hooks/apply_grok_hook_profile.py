#!/usr/bin/env python3
"""Idempotently set Grok harness hook profile (operator hook audit 2026-08-06).

Default action: disable Claude-compat hooks so Grok does not inherit the fat
`.claude/settings.json` PreToolUse stack. Writes `~/.grok/config.toml` unless
`--config` is passed. Dry-run by default; pass `--apply` to write.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_CONFIG = Path.home() / ".grok" / "config.toml"

SNIPPET = """
# Hook audit 2026-08-06 — Grok must not inherit Claude's fat project hooks.
# Thin Grok guards (if any) live under ~/.grok/hooks/ or <project>/.grok/hooks/.
# See docs/best-practices/hook-audit.md and docs/runbooks/grok-hook-profile.md
[compat.claude]
hooks = false
""".lstrip()


def ensure_compat_claude_hooks_false(text: str) -> tuple[str, bool]:
    """Return (new_text, changed)."""
    # Already correct
    if re.search(
        r"(?ms)^\[compat\.claude\][^\[]*^hooks\s*=\s*false\s*$",
        text,
    ):
        return text, False
    # Section exists with hooks = true → flip
    if re.search(r"(?ms)^\[compat\.claude\]", text):
        new = re.sub(
            r"(?ms)(^\[compat\.claude\][^\[]*?^hooks\s*=\s*)\w+",
            r"\1false",
            text,
            count=1,
        )
        if new != text:
            return new, True
        # section without hooks key
        new = re.sub(
            r"(?ms)(^\[compat\.claude\]\s*\n)",
            r"\1hooks = false\n",
            text,
            count=1,
        )
        return new, new != text
    # Append
    body = text.rstrip() + ("\n\n" if text.strip() else "") + SNIPPET
    if not body.endswith("\n"):
        body += "\n"
    return body, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes (default is dry-run)",
    )
    args = parser.parse_args(argv)
    path: Path = args.config
    text = "" if not path.exists() else path.read_text(encoding="utf-8")
    new_text, changed = ensure_compat_claude_hooks_false(text)
    if not changed:
        print(f"ok: {path} already has [compat.claude] hooks = false")
        return 0
    if not args.apply:
        print(f"dry-run: would update {path}")
        print("--- proposed tail ---")
        print(SNIPPET if not text.strip() else "(patch existing [compat.claude] or append block)")
        print("re-run with --apply to write")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_text, encoding="utf-8")
    print(f"applied: {path}  ([compat.claude] hooks = false)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
