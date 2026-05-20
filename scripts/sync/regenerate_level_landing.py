"""Regenerate a level's starlight landing-page MDX to match A1's shape.

A1's `starlight/src/content/docs/a1/index.mdx` is the canonical shape:
- Frontmatter: `title`, `description`, `template: splash` (no `sidebar:` block).
- Component props: `title` (Ukrainian level title for the hero), `subtitle`
  (English "X/N modules complete"), `moduleCount`, `wordTarget`, `color`.
- Modules: unit-grouped (`{unit: "...", items: [...]}`) where each item is
  `{num, slug, title, sub, status}`. Unit labels come from the plan
  YAML `phase:` field (Ukrainian, e.g. `"A1.2 [Мій світ]"`); item
  `title`/`sub` come from `title` / `subtitle` in the plan.

A1 itself is **NOT regenerated** — it's hand-maintained per operator
preference (their working tree carries manual edits). This script
preserves a1 by skipping it.

Levels currently supported (data-present in `curriculum.yaml` +
`scripts/common/thresholds.LEVEL_THRESHOLDS`): a2, b1. b2/c1/c2 will
work once those have plan files + `LEVEL_TITLE_UK` entries below.

Usage:
    .venv/bin/python scripts/sync/regenerate_level_landing.py a2 b1
    .venv/bin/python scripts/sync/regenerate_level_landing.py --all

Why not extend `scripts/build/build_landing_pages.py`?
    That generator currently produces the OLD shape (`levelName=`,
    `totalPlanned=`, flat module list, `sidebar:` frontmatter). Extending
    it would either (a) break callers of the old shape mid-flight or
    (b) require a parallel code path. This new module is the forward
    surface; the legacy generator can be retired once b2/c1/c2 + all
    seminar tracks migrate. Tracking issue intentionally not filed yet —
    operator preference is to land the data fix first, then decide.
"""
from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.common.thresholds import LEVEL_THRESHOLDS

DOCS_DIR = ROOT / "starlight" / "src" / "content" / "docs"
CURRICULUM_YAML = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
PLANS_DIR = ROOT / "curriculum" / "l2-uk-en" / "plans"

# Mirrors LevelLanding.tsx default colors so the emitted file is
# self-contained and matches the component fallback exactly.
LEVEL_COLORS: dict[str, str] = {
    "a1": "#2E7D32", "a2": "#1565C0", "b1": "#E65100",
    "b2": "#C62828", "c1": "#6A1B9A", "c2": "#8D6E00",
}

# English level name used in the splash frontmatter `description` and the
# `subtitle=` prop. Keeps the format identical to a1's "First Steps — N modules".
LEVEL_DESC_EN: dict[str, str] = {
    "a1": "First Steps", "a2": "Pre-Intermediate", "b1": "Intermediate",
    "b2": "Upper-Intermediate", "c1": "Advanced", "c2": "Mastery",
}

# Ukrainian title shown as the big hero H1 (component prop `title`).
# This is NOT derivable from plan data — it's a curated phrase per level.
LEVEL_TITLE_UK: dict[str, str] = {
    "a1": "Перші кроки",
    "a2": "Перші кроки далі",
    "b1": "Жива мова",
    # b2/c1/c2: add once the operator picks a Ukrainian level motto.
}

# a1 is intentionally OUT — its mdx carries manual operator edits.
SUPPORTED_LEVELS: tuple[str, ...] = ("a2", "b1")


def _build_units(level: str, manifest: dict) -> list[tuple[str, list[dict]]]:
    """Group modules by their plan's `phase:` field, preserving manifest order.

    Modules without a plan file still surface in the landing page using
    the manifest slug; their title falls back to the title-cased slug
    and their sub is empty. This is the right behavior because the
    landing page reflects the *manifest* (the source of truth for what
    modules exist) — silently dropping unplanned modules would hide
    in-flight curriculum work.
    """
    slugs = manifest["levels"][level]["modules"]
    units: OrderedDict[str, list[dict]] = OrderedDict()

    for slug in slugs:
        plan_path = PLANS_DIR / level / f"{slug}.yaml"
        if plan_path.exists():
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            phase = (plan.get("phase") or "Untriaged").strip()
            title = (plan.get("title") or slug).strip()
            sub = (plan.get("subtitle") or "").strip()
            seq = plan.get("sequence") or (slugs.index(slug) + 1)
        else:
            phase = "Untriaged"
            title = slug.replace("-", " ").title()
            sub = ""
            seq = slugs.index(slug) + 1

        units.setdefault(phase, []).append({
            "num": int(seq),
            "slug": slug,
            "title": title,
            "sub": sub,
            "status": "locked",
        })

    return list(units.items())


def _render_mdx(level: str, units: list[tuple[str, list[dict]]],
                total_modules: int, word_target: int) -> str:
    """Render the MDX content matching a1/index.mdx structure exactly."""
    color = LEVEL_COLORS.get(level, "#0057B8")
    title_uk = LEVEL_TITLE_UK.get(level, level.upper())
    desc_en = LEVEL_DESC_EN.get(level, level.upper())
    front_title = f"{level.upper()} — {desc_en}"
    front_desc = f"{desc_en} — {total_modules} modules"
    subtitle_prop = f"{desc_en} — 0/{total_modules} modules complete"

    lines: list[str] = [
        "---",
        f'title: "{front_title}"',
        f'description: "{front_desc}"',
        "template: splash",
        "---",
        "",
        "import LevelLanding from '@site/src/components/LevelLanding';",
        "",
        "<LevelLanding",
        "  client:load",
        f'  level="{level.upper()}"',
        f'  title="{title_uk}"',
        f'  subtitle="{subtitle_prop}"',
        f"  moduleCount={{{total_modules}}}",
        f"  wordTarget={{{word_target}}}",
        f'  color="{color}"',
        "  modules={[",
    ]

    for unit_label, items in units:
        unit_lit = unit_label.replace('"', '\\"')
        lines.append("    {")
        lines.append(f'      unit: "{unit_lit}",')
        lines.append("      items: [")
        for it in items:
            title_lit = it["title"].replace('"', '\\"')
            sub_lit = it["sub"].replace('"', '\\"')
            sub_field = f', sub: "{sub_lit}"' if sub_lit else ""
            lines.append(
                f'        {{ num: {it["num"]}, slug: "{it["slug"]}", '
                f'title: "{title_lit}"{sub_field}, status: "{it["status"]}" }},'
            )
        lines.append("      ]")
        lines.append("    },")

    lines.append("  ]}")
    lines.append("/>")
    lines.append("")
    return "\n".join(lines)


def regenerate(level: str) -> Path:
    """Regenerate the landing page MDX for one level. Returns the file path."""
    if level == "a1":
        raise ValueError(
            "Refusing to regenerate a1 — it's hand-maintained. "
            "Update LEVEL_TITLE_UK + remove this guard if that changes."
        )
    if level not in LEVEL_TITLE_UK:
        raise ValueError(
            f"No Ukrainian level title configured for {level!r}. "
            "Add it to LEVEL_TITLE_UK in this script first."
        )
    manifest = yaml.safe_load(CURRICULUM_YAML.read_text(encoding="utf-8"))
    if level not in manifest.get("levels", {}):
        raise ValueError(f"Level {level!r} not in curriculum.yaml")

    units = _build_units(level, manifest)
    total_modules = sum(len(items) for _, items in units)
    thresholds = LEVEL_THRESHOLDS.get(level.upper())
    word_target = thresholds.target_words if thresholds else 0

    mdx = _render_mdx(level, units, total_modules, word_target)
    out_path = DOCS_DIR / level / "index.mdx"
    out_path.write_text(mdx, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "levels",
        nargs="*",
        help=f"Levels to regenerate (e.g. a2 b1). Supported: {' '.join(SUPPORTED_LEVELS)}",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Regenerate every level in SUPPORTED_LEVELS.",
    )
    args = parser.parse_args()

    targets: list[str]
    targets = list(SUPPORTED_LEVELS) if args.all else (args.levels or [])

    if not targets:
        parser.error("Specify level(s) or --all")

    for level in targets:
        if level == "a1":
            print("skip a1 (hand-maintained)")
            continue
        path = regenerate(level)
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
