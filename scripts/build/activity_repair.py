"""Activity auto-repair — deterministic fixes for activity YAML.

Takes a validated-with-issues activity YAML and fixes everything that can
be fixed without LLM calls. Returns the remaining issues that need LLM
regeneration (e.g., activity count below minimum can't be invented from
nothing).

Fixes applied (all deterministic, idempotent):
1. Parenthetical hints in fill-in sentences — strip "(магазин)" from
   "Я йду в ____ (магазин)"
2. Duplicate quiz options — deduplicate by normalized option text
3. Match-up duplicate pairs — keep first occurrence
4. Section placement — move WORKBOOK_ONLY types from inline to workbook,
   move INLINE_ONLY types from workbook to inline
5. Type allowlist violations — drop activities with types not allowed at
   this level (marks for regen if it drops count below minimum)
6. Answer not in options — add the answer to options, cap at level max
7. True-false missing/invalid correct field — drop the item

Usage:
    from build.activity_repair import repair_activities
    result = repair_activities(Path("curriculum/l2-uk-en/a1/activities/where-to.yaml"), "a1", 31)
    print(f"Fixed {result.fixes_applied}, {len(result.needs_regen)} issues need LLM")

    # CLI batch mode:
    .venv/bin/python scripts/build/activity_repair.py a1 --all
    .venv/bin/python scripts/build/activity_repair.py a2 --module 1
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# Ensure scripts/ on sys.path for pipeline imports
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.activity_schema import dedupe_quiz_options, normalize_quiz_option_text


@dataclass
class RepairResult:
    """Outcome of repairing one activity YAML file."""

    slug: str
    level: str
    fixes_applied: int = 0
    fix_log: list[str] = field(default_factory=list)
    needs_regen: list[str] = field(default_factory=list)
    # Counts after repair
    inline_count_after: int = 0
    workbook_count_after: int = 0
    # Was the file actually modified?
    modified: bool = False

    @property
    def can_ship(self) -> bool:
        """True if no regen-required issues remain."""
        return not self.needs_regen

    def __str__(self) -> str:
        lines = [
            f"=== {self.slug} ({self.level}) ===",
            f"  Fixes applied: {self.fixes_applied}",
        ]
        for f in self.fix_log:
            lines.append(f"    • {f}")
        if self.needs_regen:
            lines.append(f"  ❌ Needs regen ({len(self.needs_regen)}):")
            for n in self.needs_regen:
                lines.append(f"    → {n}")
        else:
            lines.append("  ✅ No regen needed")
        lines.append(f"  Final counts: {self.inline_count_after} inline + {self.workbook_count_after} workbook")
        return "\n".join(lines)


# Regex to strip parenthetical hints from fill-in sentences.
# "Я йду в ____ (магазин)." → "Я йду в ____."
_PAREN_HINT_RE = re.compile(r"\s*\([^)]+\)\s*")


def repair_activities(path: Path, level: str, module_num: int) -> RepairResult:
    """Apply deterministic fixes to an activity YAML file.

    Loads the file, applies every fix that doesn't require LLM reasoning,
    writes the file back if modified, and returns a RepairResult with
    remaining issues that need regeneration.
    """
    slug = path.stem
    result = RepairResult(slug=slug, level=level)
    structural_reasons_seen: set[str] = set()

    def add_regen(reason: str) -> None:
        if reason not in structural_reasons_seen:
            structural_reasons_seen.add(reason)
            result.needs_regen.append(reason)

    if not path.exists():
        result.needs_regen.append(f"file not found: {path}")
        return result

    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except yaml.YAMLError as e:
        add_regen(f"YAML parse error: {e}")
        return result

    if not isinstance(data, dict):
        add_regen("root is not a mapping")
        return result

    # Load level config for allowlists
    try:
        from pipeline.config_tables import (
            INLINE_ONLY_TYPES,
            WORKBOOK_ONLY_TYPES,
            get_activity_config,
        )
        config = get_activity_config(level, module_num)
    except Exception as e:
        add_regen(f"config load failed: {e}")
        return result

    inline_allowed = {
        t.strip() for t in config.get("INLINE_ALLOWED_TYPES", "").split(",") if t.strip()
    }
    workbook_allowed = {
        t.strip() for t in config.get("WORKBOOK_ALLOWED_TYPES", "").split(",") if t.strip()
    }

    section_shape_fixes = 0

    inline = data.setdefault("inline", [])
    if not isinstance(inline, list):
        add_regen(f"inline section is not a list: {type(inline).__name__}")
        inline = []
        section_shape_fixes += 1
    workbook = data.setdefault("workbook", [])
    if not isinstance(workbook, list):
        add_regen(f"workbook section is not a list: {type(workbook).__name__}")
        workbook = []
        section_shape_fixes += 1
    data["inline"] = inline
    data["workbook"] = workbook

    for section_name, section in (("inline", inline), ("workbook", workbook)):
        for act_index, act in enumerate(section):
            if not isinstance(act, dict):
                add_regen(
                    f"{section_name} activity {act_index} is not a mapping: {type(act).__name__}"
                )

    if section_shape_fixes:
        result.fixes_applied += section_shape_fixes
        result.fix_log.append(f"normalized {section_shape_fixes} malformed section(s) to empty lists")

    # -----------------------------------------------------------------
    # FIX 1: Parenthetical hints in fill-in sentences (deterministic)
    # -----------------------------------------------------------------
    hints_stripped = 0
    for section in (inline, workbook):
        for act in section:
            if not isinstance(act, dict) or act.get("type") != "fill-in":
                continue
            items = act.get("items", [])
            if not isinstance(items, list):
                add_regen("fill-in items is not a list")
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                sent = item.get("sentence", "")
                if not isinstance(sent, str):
                    continue
                cleaned = _PAREN_HINT_RE.sub(" ", sent).strip()
                cleaned = re.sub(r"\s+", " ", cleaned)
                cleaned = re.sub(r"\s+([.!?,;:])", r"\1", cleaned)
                if cleaned != sent:
                    item["sentence"] = cleaned
                    hints_stripped += 1
    if hints_stripped:
        result.fixes_applied += hints_stripped
        result.fix_log.append(f"stripped {hints_stripped} parenthetical hint(s) from fill-in")

    # -----------------------------------------------------------------
    # FIX 2: Deduplicate quiz options
    # -----------------------------------------------------------------
    dup_options_fixed = 0
    for section in (inline, workbook):
        for act in section:
            if not isinstance(act, dict) or act.get("type") != "quiz":
                continue
            items = act.get("items", [])
            if not isinstance(items, list):
                add_regen("quiz items is not a list")
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                opts = item.get("options", []) or []
                if not isinstance(opts, list):
                    continue
                correct_idx = item.get("correct")
                correct_key = (
                    normalize_quiz_option_text(opts[correct_idx])
                    if type(correct_idx) is int and 0 <= correct_idx < len(opts)
                    else None
                )
                unique, changed = dedupe_quiz_options(opts)
                if changed:
                    item["options"] = unique
                    # Reindex correct answer
                    if type(correct_idx) is int and correct_key is not None:
                        for new_index, option in enumerate(unique):
                            if normalize_quiz_option_text(option) == correct_key:
                                item["correct"] = new_index
                                break
                    dup_options_fixed += 1
    if dup_options_fixed:
        result.fixes_applied += dup_options_fixed
        result.fix_log.append(f"deduplicated {dup_options_fixed} quiz option set(s)")

    # -----------------------------------------------------------------
    # FIX 3: Match-up duplicate pairs
    # -----------------------------------------------------------------
    dup_pairs_fixed = 0
    for section in (inline, workbook):
        for act in section:
            if not isinstance(act, dict) or act.get("type") != "match-up":
                continue
            pairs = act.get("pairs", [])
            if not isinstance(pairs, list):
                add_regen("match-up pairs is not a list")
                continue
            if any(not isinstance(pair, dict) for pair in pairs):
                add_regen("match-up pairs contains non-mapping entries")
                continue
            seen_keys = set()
            unique_pairs = []
            for p in pairs:
                key = (p.get("left", ""), p.get("right", ""))
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_pairs.append(p)
            if len(unique_pairs) != len(pairs):
                act["pairs"] = unique_pairs
                dup_pairs_fixed += 1
    if dup_pairs_fixed:
        result.fixes_applied += dup_pairs_fixed
        result.fix_log.append(f"removed duplicate pairs in {dup_pairs_fixed} match-up(s)")

    # -----------------------------------------------------------------
    # FIX 4: Section placement — move WORKBOOK_ONLY from inline to workbook
    # and vice versa
    # -----------------------------------------------------------------
    moved_to_workbook = []
    moved_to_inline = []
    new_inline = []
    for act in inline:
        if not isinstance(act, dict):
            new_inline.append(act)
            continue
        atype = act.get("type", "")
        if atype in WORKBOOK_ONLY_TYPES:
            # Strip id (workbook activities don't have ids)
            act.pop("id", None)
            workbook.append(act)
            moved_to_workbook.append(atype)
        else:
            new_inline.append(act)
    data["inline"] = new_inline
    inline = new_inline

    new_workbook = []
    for act in workbook:
        if not isinstance(act, dict):
            new_workbook.append(act)
            continue
        atype = act.get("type", "")
        if atype in INLINE_ONLY_TYPES:
            # Inline activities need an id — generate a stable one
            if "id" not in act:
                act["id"] = f"{atype}-{len([a for a in new_inline if isinstance(a, dict)]) + 1}"
            new_inline.append(act)
            moved_to_inline.append(atype)
        else:
            new_workbook.append(act)
    data["inline"] = new_inline
    data["workbook"] = new_workbook
    inline = new_inline
    workbook = new_workbook

    if moved_to_workbook:
        result.fixes_applied += len(moved_to_workbook)
        result.fix_log.append(f"moved {len(moved_to_workbook)} WORKBOOK-ONLY type(s) from inline: {', '.join(sorted(set(moved_to_workbook)))}")
    if moved_to_inline:
        result.fixes_applied += len(moved_to_inline)
        result.fix_log.append(f"moved {len(moved_to_inline)} INLINE-ONLY type(s) from workbook: {', '.join(sorted(set(moved_to_inline)))}")

    # -----------------------------------------------------------------
    # FIX 5: Drop activities with types not in per-section allowlist.
    # Count-based regen is evaluated after the removals.
    # -----------------------------------------------------------------
    # Build list of allowlist violations first
    inline_violations = []
    for i, act in enumerate(inline):
        if not isinstance(act, dict):
            continue
        atype = act.get("type", "")
        if inline_allowed and atype and atype not in inline_allowed:
            inline_violations.append((i, atype))

    workbook_violations = []
    for i, act in enumerate(workbook):
        if not isinstance(act, dict):
            continue
        atype = act.get("type", "")
        if workbook_allowed and atype and atype not in workbook_allowed:
            workbook_violations.append((i, atype))

    # Drop violations (iterate in reverse to preserve indices)
    dropped_inline = []
    for i, atype in reversed(inline_violations):
        del inline[i]
        dropped_inline.append(atype)
    dropped_workbook = []
    for i, atype in reversed(workbook_violations):
        del workbook[i]
        dropped_workbook.append(atype)

    if dropped_inline:
        result.fixes_applied += len(dropped_inline)
        result.fix_log.append(f"dropped {len(dropped_inline)} inline activities with disallowed types: {', '.join(sorted(set(dropped_inline)))}")
    if dropped_workbook:
        result.fixes_applied += len(dropped_workbook)
        result.fix_log.append(f"dropped {len(dropped_workbook)} workbook activities with disallowed types: {', '.join(sorted(set(dropped_workbook)))}")

    # -----------------------------------------------------------------
    # FIX 6: Answer not in options — add the answer
    # -----------------------------------------------------------------
    answers_added = 0
    for section in (inline, workbook):
        for act in section:
            if not isinstance(act, dict) or act.get("type") != "fill-in":
                continue
            items = act.get("items", [])
            if not isinstance(items, list):
                add_regen("fill-in items is not a list")
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                answer = item.get("answer", "")
                opts = item.get("options", [])
                if not isinstance(opts, list):
                    add_regen("fill-in options is not a list")
                    continue
                if opts and answer and answer not in opts:
                    # Add answer, cap total at 4 for fill-in
                    new_opts = [answer, *opts[:3]]
                    item["options"] = new_opts
                    answers_added += 1
    if answers_added:
        result.fixes_applied += answers_added
        result.fix_log.append(f"added missing answer to options in {answers_added} fill-in item(s)")

    # -----------------------------------------------------------------
    # FIX 7: true-false missing/invalid correct — drop the item
    # -----------------------------------------------------------------
    tf_items_dropped = 0
    for section in (inline, workbook):
        for act in section:
            if not isinstance(act, dict) or act.get("type") != "true-false":
                continue
            items = act.get("items", [])
            if not isinstance(items, list):
                add_regen("true-false items is not a list")
                continue
            valid_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                correct = item.get("correct", item.get("isTrue"))
                if type(correct) is bool:
                    valid_items.append(item)
                else:
                    tf_items_dropped += 1
            act["items"] = valid_items
    if tf_items_dropped:
        result.fixes_applied += tf_items_dropped
        result.fix_log.append(f"dropped {tf_items_dropped} true-false item(s) with invalid 'correct' field")

    # -----------------------------------------------------------------
    # Final state: check counts
    # -----------------------------------------------------------------
    result.inline_count_after = len(inline)
    result.workbook_count_after = len(workbook)

    try:
        inline_min = int(config.get("INLINE_MIN", "0"))
        workbook_min = int(config.get("WORKBOOK_MIN", "0"))
    except (TypeError, ValueError):
        inline_min = workbook_min = 0

    if inline_min and result.inline_count_after < inline_min:
        result.needs_regen.append(
            f"inline count {result.inline_count_after} below minimum {inline_min}"
        )
    if workbook_min and result.workbook_count_after < workbook_min:
        result.needs_regen.append(
            f"workbook count {result.workbook_count_after} below minimum {workbook_min}"
        )

    # -----------------------------------------------------------------
    # Per-activity density check: each activity must have at least
    # ITEMS_MIN items. The audit's "density" gate counts activities
    # whose per-activity item count is below this threshold, and a
    # single offender fails the gate. step_repair previously only
    # checked TOTAL counts, so a module with enough activities but
    # one under-dense activity would silently skip regen and the
    # density failure would persist across every heal pass.
    # Added 2026-04-11 after a1 rebuild left 3 density failures in
    # my-family / my-morning / sounds-letters-and-hello untouched.
    # -----------------------------------------------------------------
    try:
        items_min = int(config.get("ITEMS_MIN", "0"))
    except (TypeError, ValueError):
        items_min = 0

    if items_min:
        try:
            # Reuse the audit's canonical counter so repair agrees with
            # what the gate sees — no drift between "what we flag" and
            # "what the audit flags".
            from audit.checks.activity_counting import count_items as _count_items
            from yaml_activities import ActivityParser

            parsed = ActivityParser().parse(path)
            under_dense = 0
            for a in parsed:
                n = _count_items('', a)
                if n < items_min:
                    under_dense += 1
            if under_dense:
                result.needs_regen.append(
                    f"{under_dense} activity/activities with fewer than "
                    f"{items_min} items (per-activity density)"
                )
        except Exception as _dens_err:
            # Density check is best-effort — do not crash repair if the
            # parser or counter trips on something. The audit will catch
            # it on the next pass.
            result.fix_log.append(f"density check skipped: {_dens_err}")

    # -----------------------------------------------------------------
    # Save if modified
    # -----------------------------------------------------------------
    if result.fixes_applied > 0:
        result.modified = True
        path.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main():
    import argparse

    parser = argparse.ArgumentParser(description="Repair activity YAML files deterministically.")
    parser.add_argument("level", help="Level (a1, a2, b1, ...)")
    parser.add_argument("--all", action="store_true", help="Repair all modules in level")
    parser.add_argument("--module", type=int, help="Repair single module by number")
    parser.add_argument("--slug", help="Repair single module by slug")
    args = parser.parse_args()

    act_dir = CURRICULUM_DIR / args.level / "activities"
    if not act_dir.exists():
        print(f"❌ Not found: {act_dir}")
        sys.exit(1)

    try:
        from batch_gemini_config import get_module_index, num_for_slug
    except ImportError:
        print("❌ batch_gemini_config not importable")
        sys.exit(1)

    targets: list[tuple[str, int]] = []  # (slug, module_num)

    if args.slug:
        try:
            num = num_for_slug(args.level, args.slug)
        except Exception:
            num = 1
        targets.append((args.slug, num))
    elif args.module:
        idx = get_module_index(args.level)
        slug = idx["num_to_slug"].get(args.module)
        if not slug:
            print(f"❌ Module {args.module} not found in {args.level}")
            sys.exit(1)
        targets.append((slug, args.module))
    elif args.all:
        idx = get_module_index(args.level)
        for num, slug in sorted(idx["num_to_slug"].items()):
            path = act_dir / f"{slug}.yaml"
            if path.exists():
                targets.append((slug, num))
    else:
        print("❌ Specify --all, --module N, or --slug SLUG")
        sys.exit(1)

    total_fixes = 0
    modules_modified = 0
    modules_need_regen = []

    for slug, num in targets:
        path = act_dir / f"{slug}.yaml"
        if not path.exists():
            continue
        try:
            result = repair_activities(path, args.level, num)
        except Exception as e:
            print(f"=== {slug} ({args.level}) ===")
            print(f"  ❌ Repair crashed: {e}")
            print()
            modules_need_regen.append((num, slug, [f"repair crashed: {e}"]))
            continue
        if result.modified or result.needs_regen:
            print(result)
            print()
        total_fixes += result.fixes_applied
        if result.modified:
            modules_modified += 1
        if result.needs_regen:
            modules_need_regen.append((num, slug, result.needs_regen))

    print("=" * 60)
    print("Summary:")
    print(f"  Modules scanned: {len(targets)}")
    print(f"  Modules modified: {modules_modified}")
    print(f"  Total fixes applied: {total_fixes}")
    print(f"  Modules needing regen: {len(modules_need_regen)}")
    if modules_need_regen:
        print()
        print("Regen command:")
        nums = ",".join(str(n) for n, _, _ in modules_need_regen[:20])
        print(f"  for i in {nums}; do .venv/bin/python scripts/build/v6_build.py {args.level} $i --step activities; done")


if __name__ == "__main__":
    _main()
