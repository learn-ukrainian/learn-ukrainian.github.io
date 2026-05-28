"""Universal rules registry — V7.2 Step 4 scaffold.

Loads `R-<NAME>.md` fragments from `scripts/build/universal_rules/` and exposes
filtering + topologically-sorted access. The Step 5 prompt generator will
consume this to compose writer + reviewer prompts; Step 4 only ships the
registry + loader (the legacy `scripts/build/phases/linear-write.md`
template still drives builds during the migration).

Design + roadmap: `docs/best-practices/universal-rules-registry.md`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

UNIVERSAL_RULES_DIR = Path(__file__).resolve().parent / "universal_rules"

VALID_SLOTS = frozenset(
    {
        "writer.preamble",
        "writer.body",
        "reviewer.rubric",
        "shared.contract",
    }
)

VALID_LEVELS = frozenset({"a1", "a2", "b1", "b2", "c1", "c2", "all"})
VALID_TRACKS = frozenset({"core", "seminar", "all"})

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


class RuleRegistryError(Exception):
    """Base class for registry errors."""


class MalformedFragmentError(RuleRegistryError):
    """Fragment frontmatter is missing, malformed, or violates the schema."""


class MissingDependencyError(RuleRegistryError):
    """A `depends_on` entry names a rule id that does not exist as a fragment."""


class CircularDependencyError(RuleRegistryError):
    """Topological sort detected a cycle among `depends_on` edges."""


@dataclass(frozen=True)
class Rule:
    """A single universal-rules registry fragment.

    `id` is the bare form (`R-VESUM-ALL-WORDS`); `telemetry_id` restores the
    leading `#` that matches the pipeline's existing `rule_id` telemetry
    constants (e.g. `RULE_VESUM_ALL_WORDS = "#R-VESUM-ALL-WORDS"`).
    """

    id: str
    description: str
    levels: tuple[str, ...]
    tracks: tuple[str, ...]
    activity_profiles: tuple[str, ...]
    slot: str
    depends_on: tuple[str, ...]
    body: str
    source_path: Path

    @property
    def telemetry_id(self) -> str:
        return f"#{self.id}"


def _coerce_str_list(
    path: Path, field: str, value: object, allowed: frozenset[str] | None
) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MalformedFragmentError(
            f"{path}: applies_to.{field} must be a non-empty list, got {value!r}"
        )
    if any(not isinstance(v, str) for v in value):
        raise MalformedFragmentError(
            f"{path}: applies_to.{field} entries must all be strings"
        )
    if allowed is not None:
        bad = [v for v in value if v not in allowed]
        if bad:
            raise MalformedFragmentError(
                f"{path}: applies_to.{field} has unknown values {bad}; "
                f"expected subset of {sorted(allowed)}"
            )
    return tuple(value)


def _parse_fragment(path: Path) -> Rule:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise MalformedFragmentError(
            f"{path}: missing YAML frontmatter (expected '---' fenced block at top)"
        )
    raw_yaml, body = match.group(1), match.group(2).strip()
    try:
        meta = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as exc:
        raise MalformedFragmentError(
            f"{path}: invalid YAML frontmatter: {exc}"
        ) from exc
    if not isinstance(meta, dict):
        raise MalformedFragmentError(f"{path}: frontmatter must be a mapping")

    required = {"id", "applies_to", "slot"}
    missing = required - meta.keys()
    if missing:
        raise MalformedFragmentError(
            f"{path}: missing required frontmatter fields: {sorted(missing)}"
        )

    rule_id = meta["id"]
    if not isinstance(rule_id, str) or not rule_id.startswith("R-"):
        raise MalformedFragmentError(
            f"{path}: id must be a string starting with 'R-' (no '#' prefix), got {rule_id!r}"
        )
    expected_stem = rule_id
    if path.stem != expected_stem:
        raise MalformedFragmentError(
            f"{path}: filename stem {path.stem!r} must match id {expected_stem!r}"
        )

    slot = meta["slot"]
    if slot not in VALID_SLOTS:
        raise MalformedFragmentError(
            f"{path}: invalid slot {slot!r}; expected one of {sorted(VALID_SLOTS)}"
        )

    applies_to = meta["applies_to"]
    if not isinstance(applies_to, dict):
        raise MalformedFragmentError(
            f"{path}: applies_to must be a mapping, got {type(applies_to).__name__}"
        )

    levels = _coerce_str_list(path, "levels", applies_to.get("levels", ["all"]), VALID_LEVELS)
    tracks = _coerce_str_list(path, "tracks", applies_to.get("tracks", ["all"]), VALID_TRACKS)
    activity_profiles = _coerce_str_list(
        path, "activity_profiles", applies_to.get("activity_profiles", ["all"]), None
    )

    depends_on = meta.get("depends_on", []) or []
    if not isinstance(depends_on, list) or any(not isinstance(x, str) for x in depends_on):
        raise MalformedFragmentError(
            f"{path}: depends_on must be a list of strings"
        )

    description = meta.get("description", "")
    if not isinstance(description, str):
        raise MalformedFragmentError(f"{path}: description must be a string")

    return Rule(
        id=rule_id,
        description=description,
        levels=levels,
        tracks=tracks,
        activity_profiles=activity_profiles,
        slot=slot,
        depends_on=tuple(depends_on),
        body=body,
        source_path=path,
    )


def load_all_rules(directory: Path | None = None) -> list[Rule]:
    """Discover and parse every `R-*.md` fragment under `directory`.

    Returns rules in filename-alphabetical order. The loader globs
    `R-*.md` (not `*.md`) so `README.md` and any sibling docs are
    naturally excluded.

    Each invocation re-reads the filesystem; callers that need caching
    should wrap their own.
    """
    base = directory if directory is not None else UNIVERSAL_RULES_DIR
    if not base.is_dir():
        raise RuleRegistryError(
            f"universal rules directory does not exist: {base}"
        )
    rules: list[Rule] = []
    seen_ids: dict[str, Path] = {}
    for path in sorted(base.glob("R-*.md")):
        rule = _parse_fragment(path)
        if rule.id in seen_ids:
            raise MalformedFragmentError(
                f"duplicate rule id {rule.id!r}: {seen_ids[rule.id]} and {path}"
            )
        seen_ids[rule.id] = path
        rules.append(rule)
    return rules


def _matches(values: tuple[str, ...], target: str) -> bool:
    return "all" in values or target in values


def _topological_sort(
    rules: list[Rule], full_index: dict[str, Rule]
) -> list[Rule]:
    """Sort `rules` so each rule appears after its `depends_on` entries.

    Validates every `depends_on` id against `full_index` (the *complete*
    registry, not the filtered subset) — a filtered-out parent that does
    not exist anywhere still raises `MissingDependencyError`. Tie-break is
    input order (= filename-alphabetical from `load_all_rules`).
    """
    selected_ids = {r.id for r in rules}
    for rule in rules:
        for dep in rule.depends_on:
            if dep not in full_index:
                raise MissingDependencyError(
                    f"{rule.id} depends_on {dep!r}, but no such rule fragment exists"
                )
    output: list[Rule] = []
    emitted: set[str] = set()
    remaining = list(rules)
    progress = True
    while remaining and progress:
        progress = False
        next_remaining: list[Rule] = []
        for rule in remaining:
            in_set_deps = [d for d in rule.depends_on if d in selected_ids]
            if all(d in emitted for d in in_set_deps):
                output.append(rule)
                emitted.add(rule.id)
                progress = True
            else:
                next_remaining.append(rule)
        remaining = next_remaining
    if remaining:
        raise CircularDependencyError(
            "circular dependency among rules: "
            + ", ".join(sorted(r.id for r in remaining))
        )
    return output


def load_applicable_rules(
    level: str,
    track: str,
    activity_profile: str,
    slot: str | None = None,
    directory: Path | None = None,
) -> list[Rule]:
    """Return rules whose `applies_to` predicates match.

    Args:
        level: One of {a1, a2, b1, b2, c1, c2}. Rules with `levels: [all]`
            match every level.
        track: One of {core, seminar}. Rules with `tracks: [all]` match
            every track.
        activity_profile: Free-form profile string (e.g. `default`).
            Rules with `activity_profiles: [all]` match every profile.
        slot: Optional. If provided, only fragments whose `slot` matches
            are returned. `None` returns every slot.
        directory: Optional override for the registry directory (testing).

    Returns:
        Rules in topological order: every `depends_on` precedes its
        dependents. Tie-break is filename-alphabetical.
    """
    all_rules = load_all_rules(directory)
    full_index = {r.id: r for r in all_rules}
    filtered = [
        r
        for r in all_rules
        if _matches(r.levels, level)
        and _matches(r.tracks, track)
        and _matches(r.activity_profiles, activity_profile)
        and (slot is None or r.slot == slot)
    ]
    return _topological_sort(filtered, full_index)


def get_rule(rule_id: str, directory: Path | None = None) -> Rule:
    """Fetch a single rule by id (`R-X` form, no `#` prefix)."""
    for rule in load_all_rules(directory):
        if rule.id == rule_id:
            return rule
    raise KeyError(f"no rule fragment with id={rule_id!r}")
