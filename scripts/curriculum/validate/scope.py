"""The generated scope sidecar and the module title check (issue #8412, Brief B).

The scope (docs/epics/fresh-build-plan-schema.md §2 rule 5, §2a) is derived
from the lessons, never typed: the letter count and list (in order of first
introduction), the grammar-point count and ids, and the core-lemma count. No
``minutes`` until its constants exist — the validator keeps emitting
``not_checked: minutes_constants_undefined`` instead.

``plan-validate --write-scope`` writes ``lesson-plans/<level>/_scope/<slug>.yaml``;
a plain run checks it byte for byte (the same generate-and-check pattern as
``_arc.yaml`` in scripts/curriculum/arc/generate_arc.py). Output is
deterministic: fixed key order, UTF-8, a trailing newline, and files created
without group-write or any world bit (mode 0o600; a created ``_scope``
directory is 0o700).

The title check reads the module's ``title`` and ``subtitle`` only — never a
lesson's title. A run of two or more enumerated single letters there must
equal the scope letter list. "A run of enumerated single letters" is defined
mechanically (stated verbatim in the CLI's --help): a maximal sequence of two
or more tokens, each exactly one UPPERCASE Cyrillic letter, separated only by
commas, semicolons or whitespace. Because the letters must be uppercase, a
Ukrainian one-letter word inside a sentence (я, і, у, в, а, о — lowercase) can
never be misread as an enumeration, and one letter alone is not a run. Numbers
are not parsed: ASCII digits found in the title and subtitle are quoted in the
always-emitted ``not_checked: title_quantities_not_parsed``.
"""

from __future__ import annotations

import difflib
import os
import re
from pathlib import Path

import yaml

from . import codes
from .report import Outcome

SCOPE_SCHEMA_VERSION = 1

#: One uppercase Cyrillic letter (А-Я plus Є Ї І Ґ; lowercase-only letters such
#: as ь can never start a title run, which is what keeps one-letter Ukrainian
#: words out of the definition).
_UPPER = "А-ЯЄЇІҐ"
_ANY_LETTER = "А-Яа-яЄєЇїІіҐґЬь"

#: A run of enumerated single letters: two or more single uppercase Cyrillic
#: letter tokens separated only by commas, semicolons or whitespace. The
#: lookarounds keep multi-letter words (and digits/Latin) from splitting into
#: "letters".
LETTER_RUN_RE = re.compile(
    rf"(?<![0-9A-Za-z_{_ANY_LETTER}])"
    rf"[{_UPPER}]"
    rf"(?:(?:\s*[,;]|\s)\s*[{_UPPER}](?![0-9A-Za-z_{_ANY_LETTER}]))+"
)
_RUN_LETTER_RE = re.compile(rf"[{_UPPER}]")
_ASCII_DIGIT_RE = re.compile(r"[0-9]")


def compute_scope(plan: dict, level: str, slug: str) -> dict:
    """Derive the scope from the plan's lessons; fixed key order throughout."""
    letters: list[str] = []
    grammar_ids: list[str] = []
    core_ids: list[str] = []
    for lesson in plan["lessons"]:
        inventory = lesson["inventory"]
        for letter in (inventory.get("phonetics") or {}).get("letters") or []:
            if letter not in letters:
                letters.append(letter)
        for entry in inventory.get("grammar") or []:
            if entry["id"] not in grammar_ids:
                grammar_ids.append(entry["id"])
        for entry in inventory["vocabulary"]["core"]:
            if entry["evidence"] not in core_ids:
                core_ids.append(entry["evidence"])
    return {
        "scope_schema": SCOPE_SCHEMA_VERSION,
        "level": level,
        "module": slug,
        "letters": {"count": len(letters), "list": letters},
        "grammar": {"count": len(grammar_ids), "ids": grammar_ids},
        "vocabulary": {"core_count": len(core_ids)},
    }


def render_scope(scope: dict) -> bytes:
    """The deterministic sidecar bytes: fixed key order, UTF-8, trailing newline."""
    text = yaml.safe_dump(scope, sort_keys=False, allow_unicode=True, width=10**6)
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def scope_sidecar_path(plan_path: Path, slug: str) -> Path:
    return plan_path.parent / "_scope" / f"{slug}.yaml"


def write_scope_sidecar(plan_path: Path, slug: str, scope: dict) -> Path:
    """Write the sidecar; created files are 0o600, a created _scope dir 0o700."""
    sidecar = scope_sidecar_path(plan_path, slug)
    created_dir = not sidecar.parent.is_dir()
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    if created_dir:
        os.chmod(sidecar.parent, 0o700)
    sidecar.write_bytes(render_scope(scope))
    os.chmod(sidecar, 0o600)
    return sidecar


def check_scope_sidecar(report, plan: dict, plan_path: Path, *, write: bool) -> list[str]:
    """Byte-for-byte sidecar check (or write). Returns the scope letter list.

    The sidecar is keyed on plan["slug"] — which the loader has already made
    equal to the plan's file name and the requested slug — so single-plan mode
    and --all always read the same sidecar.
    """
    slug = plan["slug"]
    scope = compute_scope(plan, report.level, slug)
    letters = list(scope["letters"]["list"])
    if write:
        write_scope_sidecar(plan_path, slug, scope)
        return letters
    sidecar = scope_sidecar_path(plan_path, slug)
    if not sidecar.is_file():
        report.failures.append(
            Outcome(
                codes.SCOPE_SIDECAR_MISSING,
                f"{sidecar} does not exist; the scope is generated, never typed — "
                "run plan-validate --write-scope to create it (§2a)",
            )
        )
        return letters
    try:
        actual = sidecar.read_bytes()
    except OSError as error:
        report.failures.append(Outcome(codes.SCOPE_SIDECAR_MISSING, f"{sidecar} is unreadable: {error}"))
        return letters
    expected = render_scope(scope)
    if actual != expected:
        try:
            diff = "".join(
                difflib.unified_diff(
                    actual.decode("utf-8").splitlines(keepends=True),
                    expected.decode("utf-8").splitlines(keepends=True),
                    fromfile=f"{sidecar.name} (committed)",
                    tofile=f"{sidecar.name} (fresh generation)",
                )
            )
        except UnicodeDecodeError:
            diff = "<sidecar is not valid UTF-8>"
        report.failures.append(
            Outcome(
                codes.SCOPE_SIDECAR_STALE,
                f"{sidecar} differs byte for byte from a fresh generation; "
                "regenerate with plan-validate --write-scope (§2a). Diff:\n" + diff.rstrip("\n"),
            )
        )
    return letters


def letter_runs(text: str) -> list[list[str]]:
    """Every run of enumerated single letters in text, as lists of letters."""
    return [_RUN_LETTER_RE.findall(match.group(0)) for match in LETTER_RUN_RE.finditer(text)]


def check_title(report, plan: dict, scope_letters: list[str]) -> None:
    """The module title/subtitle letter-enumeration check (§2a; lesson titles are never read)."""
    title = plan.get("title") or ""
    subtitle = plan.get("subtitle") or ""
    scope_set = set(scope_letters)
    for field, text in (("title", title), ("subtitle", subtitle)):
        for run in letter_runs(text):
            missing = sorted(scope_set - set(run))
            extra = sorted(set(run) - scope_set)
            if missing or extra:
                parts = []
                if missing:
                    parts.append("missing: " + " ".join(missing))
                if extra:
                    parts.append("extra: " + " ".join(extra))
                report.failures.append(
                    Outcome(
                        codes.TITLE_LETTER_ENUMERATION_MISMATCH,
                        f"module {field} enumerates the letters {' '.join(run)} but the scope letter list "
                        f"is {' '.join(scope_letters) or '<empty>'} ({'; '.join(parts)}) (§2a)",
                    )
                )


def title_quantities_outcome(plan: dict | None):
    """The always-emitted title_quantities not_checked line, quoting ASCII digits."""
    if plan is None:
        return Outcome(
            codes.TITLE_QUANTITIES_NOT_PARSED,
            "the plan could not be loaded, so no title or subtitle digits could be quoted; "
            "digit quantities are never parsed (§2a)",
        )
    found = []
    for field in ("title", "subtitle"):
        text = plan.get(field) or ""
        digits = sorted(set(_ASCII_DIGIT_RE.findall(text)))
        if digits:
            found.append(f"{field} digits: {', '.join(digits)}")
    detail = "; ".join(found) if found else "no ASCII digits in the title or subtitle"
    return Outcome(
        codes.TITLE_QUANTITIES_NOT_PARSED,
        f"{detail}; digit quantities are not parsed — the plan review checks stated "
        "quantities against the scope sidecar (§2a)",
    )
