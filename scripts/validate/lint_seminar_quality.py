#!/usr/bin/env python3
"""Deterministic seminar-quality language linter for seminar plans and wiki text.

Seminar tracks (bio/hist/lit/istorio/oes/ruth) are *source-first* and stricter
than core language lessons. Two language-quality defect classes recur in the
plan corpus and are NOT caught by any existing validator
(``validate_plan_config.py`` = word targets / key sets;
``validate_plan_ordering.py`` = ``connects_to`` / ordering):

1. **Russianisms / calques** — e.g. ``арест`` (→ ``арешт``), ``постумно``
   (→ ``посмертно``), ``коерція`` (→ ``примус``), ``інакомисляч``
   (→ ``інакодумець``), ``власті`` (→ ``влада``), prison-sense ``термін``
   (→ ``строк``), singular ``дебат`` (→ ``дебати``). Proven defects: #2528.

2. **Latin-in-Cyrillic** — homoglyph substitutions inside a single word
   (``Cлово``, ``мистецтвoм``, ``Оспiщев``) and lazy Latin abbreviations glued
   to Cyrillic prose (``LIT-модулі``, ``L2-студентам``, ``hindsight-осуду``).
   Legitimate Latin (``X-променів``, ``STEM``, ``IEU``, ``Ems``, URLs) is
   allowlisted and NOT flagged.

This is a **precision-first pre-review filter**: it runs BEFORE the cross-family
content review to cut review rounds and catch mechanical defects deterministically.
Recall is intentionally bounded — the curated russianism list covers
high-confidence forms only; the cross-review handles the long tail. New
legitimate Latin tokens go in ``LATIN_ALLOWLIST``; new proven russianisms go in
``RUSSIANISMS``.

Use
===
    .venv/bin/python scripts/validate/lint_seminar_quality.py                 # all bio plans
    .venv/bin/python scripts/validate/lint_seminar_quality.py --track bio --json
    .venv/bin/python scripts/validate/lint_seminar_quality.py --paths curriculum/l2-uk-en/plans/bio/viktor-domontovych.yaml
    .venv/bin/python scripts/validate/lint_seminar_quality.py --paths wiki/figures
    .venv/bin/python scripts/validate/lint_seminar_quality.py --severity high  # gate on HIGH only

Exit codes
==========
- 0 — no findings at or above the selected ``--severity`` (default: any).
- 1 — at least one finding at or above the selected severity.

Related
=======
- Issue #2535 — audit + uplift existing 1-180 plans/wikis to the seminar standard.
- #2528 — the VESUM-verified постум/арест/Latin-homoglyph cleanup this codifies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"
WIKI_FIGURES_DIR = PROJECT_ROOT / "wiki" / "figures"

# Plan keys whose string values are identifiers / citation metadata, NOT prose.
# We never scan these: they legitimately carry ASCII slugs, module ids, and URLs.
SKIP_KEYS = frozenset({
    "slug", "module", "level", "cefr_min", "cefr_max", "track", "id",
    "connects_to", "prerequisites", "references", "sources", "source",
    "path", "url", "href", "link", "image", "images", "status",
    "vocabulary_hints",  # word-level; checked by vocab validators, often bare lemmas
})

CYRILLIC = "Ѐ-ӿ"
LATIN = "A-Za-z"
_UK_LETTER = rf"[{CYRILLIC}'ʼ’]"  # Cyrillic + apostrophe variants


def _boundary(stem: str, *, suffix: str = rf"{_UK_LETTER}*", prefix: str = "") -> re.Pattern[str]:
    """Whole-word Cyrillic matcher: ``stem`` not glued to another UK letter on
    the left, optionally preceded by ``prefix`` (e.g. ``(?:за|пере)?`` for
    prefixed russianisms like ``заарестовано``) and followed by an inflectional
    ``suffix`` on the right. The left-boundary lookbehind sits before the prefix,
    so ``парестезія`` (preceded by «п», prefix not «за/пере») stays unmatched."""
    return re.compile(
        rf"(?<!{_UK_LETTER})({prefix}{stem}{suffix})(?!{_UK_LETTER})",
        re.IGNORECASE,
    )


@dataclass(frozen=True)
class Rule:
    key: str
    pattern: re.Pattern[str]
    suggestion: str
    severity: str  # "high" | "advisory"
    note: str
    # Optional: only fire when one of these context stems appears within the
    # same string value (for context-dependent calques like prison-sense термін).
    requires_context: tuple[str, ...] = ()


# ── Curated russianism / calque rules (high precision, proven defects) ────────
RUSSIANISMS: tuple[Rule, ...] = (
    Rule("арест", _boundary("арест", prefix="(?:за|пере)?"), "арешт / заарешт-",
         "high", "«арест»/«заарестовано» is a Russianism; Ukrainian is «арешт»/«заарештовано» (#2528)."),
    Rule("постум", _boundary("постум"), "посмертно / посмертний",
         "high", "«постумно/постумний» is a Latinism-via-Russian; use «посмертно» (#2528)."),
    Rule("коерція", _boundary("коерц"), "примус",
         "advisory", "«коерція» (coercion) is a calque; use «примус»."),
    Rule("інакомисляч", _boundary("інакомисляч"), "інакодумець / дисидент",
         "advisory",
         "Person-form «інакомисляч(ий)» is a non-standard calque (NOT in VESUM, russian_shadow≈0.5); "
         "use «інакодумець»/«дисидент». NB «інакомислення» (abstract noun) is VESUM-codified — do NOT flag it."),
    Rule("голодовка", _boundary("голодовк"), "голодування",
         "advisory", "«голодовка» (hunger strike) is a Russianism; prefer «голодування»."),
    Rule("власті", _boundary("власт", suffix="(?:і|ей|ям|ями|ях)"), "влада / органи влади",
         "advisory", "«власті/властей/властями» (Russian plural of «власть») is a Russianism; "
         "Ukrainian uses «влада»/«органи влади». (Suffix-gated, so «властивість/властивий» are safe.)"),
    # Prison-sense «термін» → «строк»: ONLY in an imprisonment collocation.
    Rule("термін_строк", _boundary("термін", suffix=rf"{_UK_LETTER}*"),
         "строк (про ув'язнення)", "advisory",
         "Prison-sense «термін» should be «строк» (#2528); «термін» = deadline/terminology is fine.",
         requires_context=("ув'язн", "увʼязн", "покаранн", "тюрм", "відсид", "табор", "заслан")),
    # Singular «дебат» → pluralia tantum «дебати».
    Rule("дебат_sing", re.compile(
        rf"(?<!{_UK_LETTER})([Дд]ебат(?:у|ом|і)?)(?!{_UK_LETTER}|и)", ),
         "дебати", "advisory",
         "«дебати» is pluralia tantum in Ukrainian; singular «дебат» is a Russianism."),
)

# ── Latin-in-Cyrillic ────────────────────────────────────────────────────────
# Legitimate Latin tokens that may appear glued to Cyrillic with a hyphen, or
# standalone, inside Ukrainian prose. Matched case-sensitively as whole tokens.
LATIN_ALLOWLIST = frozenset({
    "X", "Y",                      # X-променів, осі X/Y
    "STEM", "STEAM",
    "IEU", "ESU", "EU", "USA", "UA", "USSR", "URSR", "OUN", "UPA", "KGB", "NKVD",
    "Ems",                         # Ems Ukaz (proper noun)
    "DNA", "RNA", "PhD", "MA", "BA", "CV",
})
# Roman numerals (XIX-столітні, XX-го, XVIII ст.) are legitimate notation.
_ROMAN_RE = re.compile(r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")

# A whitespace token is a URL/citation if it looks like one — never script-mix-flag it.
_URL_RE = re.compile(r"(https?://|www\.|\w+\.(?:org|com|net|ua|gov|edu)\b|wikipedia|@)", re.IGNORECASE)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_BARE_URL_RE = re.compile(r"https?://\S+|www\.\S+|\b\S+\.(?:org|com|net|ua|gov|edu)\S*", re.IGNORECASE)

_HAS_CYR = re.compile(rf"[{CYRILLIC}]")
_HAS_LAT = re.compile(rf"[{LATIN}]")
# A "word token": runs of letters/digits/hyphens/apostrophes (handles LIT-модулі).
_WORD_RE = re.compile(rf"[{LATIN}{CYRILLIC}0-9'’ʼ\-]+")


@dataclass(frozen=True)
class Finding:
    file: str
    field: str
    rule: str
    severity: str
    text: str
    suggestion: str
    note: str
    context: str


def _latin_run_allowed(run: str) -> bool:
    """Is a pure-Latin sub-token a legitimate (allowlisted) term?"""
    bare = run.strip("-'’ʼ")
    return (
        not bare
        or bare in LATIN_ALLOWLIST
        or (len(bare) == 1 and bare.isupper())   # single-letter notation: X-, Y-
        or bool(_ROMAN_RE.match(bare))           # roman numerals: XIX-, XVIII
    )


# Latin letter directly touching a Cyrillic letter (no separator) = homoglyph.
_ADJ_MIX = re.compile(rf"[{LATIN}][{CYRILLIC}]|[{CYRILLIC}][{LATIN}]")


def _scan_latin_in_cyrillic(value: str) -> list[tuple[str, str, str]]:
    """Return (matched_token, severity, note) for script-mixing defects.

    Two sub-patterns, distinguished by whether the scripts touch directly:
      * **intra-word homoglyph** — a Latin letter sits *directly* next to a
        Cyrillic letter (``Cлово``, ``мистецтвoм``, ``Оспiщев``). Always a defect;
        the single-letter / acronym allowlist does NOT apply, because a lone
        ``C`` glued inside a Cyrillic word is a homoglyph, not notation.
      * **hyphen-joined Latin abbreviation** — Latin and Cyrillic meet only
        across a hyphen (``LIT-модулі``, ``L2-студентам``, ``hindsight-осуду``);
        flagged unless every Latin run is allowlisted notation (``X-променів``,
        ``STEM-``, ``XIX-``).
    URLs / citation tokens are skipped.
    """
    out: list[tuple[str, str, str]] = []
    for token in _WORD_RE.findall(value):
        if not (_HAS_CYR.search(token) and _HAS_LAT.search(token)):
            continue
        if _URL_RE.search(token):
            continue
        if _ADJ_MIX.search(token):
            out.append((token, "high",
                        "Latin/Cyrillic homoglyph inside one word (script mix); "
                        "retype in pure Cyrillic (#2528)."))
            continue
        # Scripts meet only across hyphens: accept iff every Latin run is allowlisted.
        latin_runs = re.findall(rf"[{LATIN}0-9]+", token)
        if latin_runs and all(_latin_run_allowed(r) for r in latin_runs):
            continue
        out.append((token, "high",
                    "Latin abbreviation glued to Cyrillic prose; spell it out in Ukrainian "
                    "(e.g. LIT-модулі → «літературні модулі», L2 → «друга мова»)."))
    return out


def _iter_prose(node, *, key: str | None = None, path: str = ""):
    """Yield (field_path, string_value) for prose-bearing leaves, skipping
    identifier / citation keys."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in SKIP_KEYS:
                continue
            yield from _iter_prose(v, key=k, path=f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _iter_prose(v, key=key, path=f"{path}[{i}]")
    elif isinstance(node, str) and _HAS_CYR.search(node):
        yield path, node


def _excerpt(value: str, match: str) -> str:
    idx = value.find(match)
    if idx < 0:
        return value[:80]
    start, end = max(0, idx - 30), min(len(value), idx + len(match) + 30)
    return ("…" if start else "") + value[start:end].replace("\n", " ") + ("…" if end < len(value) else "")


def lint_plan(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - surfaced as a finding
        return [Finding(str(path), "<yaml>", "unparseable", "high",
                        str(exc)[:120], "", "Plan YAML failed to parse.", "")]
    if not isinstance(data, dict):
        return findings
    try:
        rel = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel = str(path)

    for field, value in _iter_prose(data):
        # Russianism / calque rules.
        for rule in RUSSIANISMS:
            if rule.requires_context and not any(c in value for c in rule.requires_context):
                continue
            m = rule.pattern.search(value)
            if m:
                hit = m.group(1)
                findings.append(Finding(rel, field, rule.key, rule.severity, hit,
                                        rule.suggestion, rule.note, _excerpt(value, hit)))
        # Latin-in-Cyrillic.
        for token, sev, note in _scan_latin_in_cyrillic(value):
            findings.append(Finding(rel, field, "latin_in_cyrillic", sev, token,
                                    "pure Cyrillic / spell out in Ukrainian", note,
                                    _excerpt(value, token)))
    return findings


def _strip_fenced_code(text: str) -> str:
    """Remove fenced-code bodies while preserving line numbers."""
    cleaned: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            cleaned.append("")
            continue
        cleaned.append("" if in_fence else line)
    return "\n".join(cleaned)


def _sanitize_text_line(line: str) -> str:
    """Drop text-mode allowlisted spans before applying prose rules."""
    line = _INLINE_CODE_RE.sub(" ", line)
    return _BARE_URL_RE.sub(" ", line)


def lint_text(path: Path) -> list[Finding]:
    """Lint a Markdown/wiki text file with the same language-quality rules."""
    findings: list[Finding] = []
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - surfaced as a finding
        return [Finding(str(path), "<read>", "unreadable", "high",
                        str(exc)[:120], "", "Text file failed to read.", "")]

    try:
        rel = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel = str(path)

    text = _strip_fenced_code(raw_text)
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        value = _sanitize_text_line(raw_line)
        if not _HAS_CYR.search(value):
            continue
        field = f"line {line_no}"
        for rule in RUSSIANISMS:
            if rule.requires_context and not any(c in value for c in rule.requires_context):
                continue
            m = rule.pattern.search(value)
            if m:
                hit = m.group(1)
                findings.append(Finding(rel, field, rule.key, rule.severity, hit,
                                        rule.suggestion, rule.note, _excerpt(value, hit)))
        for token, sev, note in _scan_latin_in_cyrillic(value):
            findings.append(Finding(rel, field, "latin_in_cyrillic", sev, token,
                                    "pure Cyrillic / spell out in Ukrainian", note,
                                    _excerpt(value, token)))
    return findings


_SEV_ORDER = {"high": 2, "advisory": 1}


def _mode_for_path(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    return "text" if path.suffix.lower() == ".md" else "plan"


def _iter_dir_paths(path: Path, requested: str) -> list[Path]:
    suffixes = {".yaml"} if requested == "plan" else {".md"} if requested == "text" else {".yaml", ".md"}
    return sorted(
        p for p in path.rglob("*")
        if p.is_file()
        and p.suffix.lower() in suffixes
        and not p.name.startswith(".")
        and not p.name.endswith(".bak")
        and not p.name.endswith(".sources.yaml")
    )


def _resolve_paths(args: argparse.Namespace) -> list[Path]:
    if args.paths:
        resolved: list[Path] = []
        for raw_path in args.paths:
            path = Path(raw_path)
            if path.is_dir():
                resolved.extend(_iter_dir_paths(path, args.format))
            else:
                resolved.append(path)
        return resolved
    if args.format == "text":
        return sorted(WIKI_FIGURES_DIR.glob("*.md"))
    track_dir = PLANS_DIR / args.track
    return sorted(p for p in track_dir.glob("*.yaml")
                  if not p.name.startswith(".") and not p.name.endswith(".bak"))


def _summary_unit(paths: list[Path], requested: str) -> str:
    modes = {_mode_for_path(path, requested) for path in paths}
    if modes == {"plan"}:
        return "plan(s)"
    if modes == {"text"}:
        return "text file(s)"
    return "file(s)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", default="bio", help="Track under plans/ (default: bio).")
    ap.add_argument("--paths", nargs="*", help="Explicit files/directories (overrides --track).")
    ap.add_argument("--format", choices=("plan", "text", "auto"), default="auto",
                    help="Input format: plan YAML, text Markdown, or auto by suffix (default: auto).")
    ap.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    ap.add_argument("--severity", choices=("high", "advisory"), default="advisory",
                    help="Minimum severity to report and to gate exit code on (default: advisory).")
    ap.add_argument("--quiet", action="store_true", help="Only print the summary line.")
    ap.add_argument("--systemic-threshold", type=int, default=20,
                    help="A rule firing in more than this many findings is collapsed to a "
                         "single 'systemic' summary line (default: 20).")
    args = ap.parse_args(argv)

    threshold = _SEV_ORDER[args.severity]
    paths = _resolve_paths(args)
    all_findings: list[Finding] = []
    for path in paths:
        lint_fn = lint_text if _mode_for_path(path, args.format) == "text" else lint_plan
        all_findings.extend(f for f in lint_fn(path) if _SEV_ORDER.get(f.severity, 2) >= threshold)

    if args.json:
        print(json.dumps([asdict(f) for f in all_findings], ensure_ascii=False, indent=2))
    else:
        # A rule that fires across many plans is a systemic/template issue, not a
        # per-plan defect. Collapse those into one summary line instead of spamming
        # a line per occurrence (e.g. the «Дебат N:» activity-heading template).
        rule_counts = Counter(f.rule for f in all_findings)
        unit = _summary_unit(paths, args.format)
        rule_files: dict[str, set[str]] = {}
        for f in all_findings:
            rule_files.setdefault(f.rule, set()).add(f.file)
        systemic = {r for r, c in rule_counts.items() if c > args.systemic_threshold}

        by_file: dict[str, list[Finding]] = {}
        for f in all_findings:
            if f.rule not in systemic:
                by_file.setdefault(f.file, []).append(f)
        if not args.quiet:
            for file, items in sorted(by_file.items()):
                print(f"\n{file}")
                for f in items:
                    tag = "❌" if f.severity == "high" else "⚠️ "
                    print(f"  {tag} [{f.rule}] «{f.text}» → {f.suggestion}")
                    print(f"      {f.context}")
            if systemic:
                print("\nSystemic (widespread — fix the template/generator once, not per-plan):")
                for r in sorted(systemic, key=lambda r: -rule_counts[r]):
                    eg = sorted(rule_files[r])[0]
                    print(f"  ⚠️  [{r}] {rule_counts[r]} hits across "
                          f"{len(rule_files[r])} {unit} — e.g. {eg}")
        n_high = sum(1 for f in all_findings if f.severity == "high")
        n_adv = len(all_findings) - n_high
        flagged = len({f.file for f in all_findings})
        print(f"\n{'─' * 60}")
        print(f"Scanned {len(paths)} {unit} · {flagged} flagged · "
              f"{len(systemic)} systemic rule(s) · {n_high} high · {n_adv} advisory")

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
