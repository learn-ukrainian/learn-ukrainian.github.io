#!/usr/bin/env python3
"""Report repeated learner-facing concepts that may need continuity signposts.

This is advisory. It does not decide whether repetition is bad; it points
reviewers to places where a repeated concept may need wording like
"You already practiced X in Module N; now use it for Y."
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_RE = re.compile(r"""num:\s*(?P<num>\d+),\s*slug:\s*['"](?P<slug>[^'"]+)['"]""")

DEFAULT_TERMS: dict[str, tuple[str, ...]] = {
    "склад": ("склад", "склади", "складів", "складом", "складу"),
    "голосний": ("голосний", "голосні", "голосних", "голосного"),
    "наголос": ("наголос", "наголоси", "наголосом"),
    "м'який знак": ("м'який знак", "м’який знак"),
    "апостроф": ("апостроф", "apostrophe"),
}

BRIDGE_CUES = (
    "already",
    "again",
    "as in module",
    "from module",
    "module 1",
    "module 2",
    "module 3",
    "module 4",
    "module 5",
    "previous",
    "quick review",
    "review",
    "checkpoint",
    "reuse",
    "same skill",
    "same idea",
    "deeper",
    "you practiced",
    "you saw",
    "ви вже",
    "ти вже",
    "пригад",
    "повтор",
    "у модулі",
    "в модулі",
    "той самий",
)


@dataclass(frozen=True)
class Module:
    num: int
    slug: str
    path: Path
    text: str


@dataclass(frozen=True)
class Finding:
    module_num: int
    slug: str
    term: str
    first_seen_num: int
    first_seen_slug: str
    line: int
    snippet: str


def module_order(level: str, root: Path = ROOT) -> list[tuple[int, str]]:
    data_path = root / "starlight" / "src" / "data" / f"{level}-modules.ts"
    data = data_path.read_text(encoding="utf-8")
    modules = [(int(m.group("num")), m.group("slug")) for m in MODULE_RE.finditer(data)]
    return sorted(modules, key=lambda item: item[0])


def load_modules(level: str, first: int | None = None, root: Path = ROOT) -> list[Module]:
    modules: list[Module] = []
    for num, slug in module_order(level, root):
        if first is not None and num > first:
            continue
        path = root / "curriculum" / "l2-uk-en" / level / slug / "module.md"
        if path.exists():
            modules.append(Module(num, slug, path, path.read_text(encoding="utf-8")))
    return modules


def _normalized(text: str) -> str:
    return text.casefold().replace("’", "'")


def _variant_patterns(variants: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    patterns: list[re.Pattern[str]] = []
    seen: set[str] = set()
    for variant in variants:
        normalized_variant = _normalized(variant)
        if normalized_variant in seen:
            continue
        seen.add(normalized_variant)
        patterns.append(
            re.compile(rf"(?<!\w){re.escape(normalized_variant)}(?!\w)")
        )
    return tuple(patterns)


def _term_positions(normalized_text: str, variants: tuple[str, ...]) -> list[int]:
    positions: set[int] = set()
    for pattern in _variant_patterns(variants):
        positions.update(match.start() for match in pattern.finditer(normalized_text))
    return sorted(positions)


def _line_number(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def _snippet(text: str, offset: int, radius: int = 90) -> str:
    start = max(0, offset - radius)
    end = min(len(text), offset + radius)
    return " ".join(text[start:end].split())


def _has_bridge_cue(normalized_text: str, offset: int) -> bool:
    start = max(0, offset - 350)
    end = min(len(normalized_text), offset + 500)
    context = normalized_text[start:end]
    return any(cue in context for cue in BRIDGE_CUES)


def find_unsignposted_repetition(
    modules: list[Module],
    terms: dict[str, tuple[str, ...]] = DEFAULT_TERMS,
) -> list[Finding]:
    first_seen: dict[str, Module] = {}
    findings: list[Finding] = []

    for module in modules:
        normalized_text = _normalized(module.text)
        for label, variants in terms.items():
            positions = _term_positions(normalized_text, variants)
            if not positions:
                continue
            first = first_seen.get(label)
            if first is None:
                first_seen[label] = module
                continue
            if any(_has_bridge_cue(normalized_text, offset) for offset in positions):
                continue
            offset = positions[0]
            findings.append(
                Finding(
                    module_num=module.num,
                    slug=module.slug,
                    term=label,
                    first_seen_num=first.num,
                    first_seen_slug=first.slug,
                    line=_line_number(module.text, offset),
                    snippet=_snippet(module.text, offset),
                )
            )
    return findings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", default="a1", help="Level to scan, e.g. a1")
    parser.add_argument("--first", type=int, help="Only scan the first N modules")
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit 1 when findings are present. Default is report-only exit 0.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    modules = load_modules(args.level, args.first)
    if not modules:
        print(f"Error: no modules found for level '{args.level}'.")
        return 1
    findings = find_unsignposted_repetition(modules)

    print(f"Continuity scan: level={args.level} modules={len(modules)} findings={len(findings)}")
    if not findings:
        print("No un-signposted repeated key concepts found.")
        return 0

    for finding in findings:
        print(
            f"- {args.level.upper()} M{finding.module_num} {finding.slug}:{finding.line} "
            f"repeats '{finding.term}' first seen in M{finding.first_seen_num} "
            f"{finding.first_seen_slug}"
        )
        print(f"  snippet: {finding.snippet}")

    return 1 if args.fail_on_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
