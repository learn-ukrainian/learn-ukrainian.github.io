"""Rewrite activity_hints in plan YAML files based on level/focus rules.

Deterministic — no LLM calls. Uses content_outline sections to craft
specific focus descriptions for seminar-style activities.

Usage:
    .venv/bin/python scripts/rewrite_activity_hints.py b2
    .venv/bin/python scripts/rewrite_activity_hints.py c1 --dry-run
    .venv/bin/python scripts/rewrite_activity_hints.py --all --dry-run
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

PLANS_DIR = Path("curriculum/l2-uk-en/plans")
LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")

_HINTS_RE = re.compile(
    r"(^activity_hints:\n(?:(?!^[a-z_]).+\n)*)", re.MULTILINE,
)


def classify_module(level: str, sequence: int, focus: str) -> str:
    """Return 'core', 'hybrid', or 'seminar'."""
    lv = level.upper()
    if lv in ("C1", "C2"):
        return "hybrid" if focus == "grammar" and lv == "C1" else "seminar"
    if lv == "B2":
        return "core" if focus == "grammar" else "seminar"
    if lv == "B1":
        return "core" if sequence <= 43 else "hybrid"
    return "core"


def extract_sections(plan: dict) -> list[dict]:
    """Return [{name, first_point}] from content_outline."""
    result: list[dict] = []
    for sec in plan.get("content_outline", []):
        pts = sec.get("points", sec.get("subsections", []))
        result.append({"name": sec.get("section", ""), "first_point": pts[0] if pts else ""})
    return result


def _s(sections: list[dict], idx: int) -> str:
    """Get section name at idx, falling back to idx 0 or default."""
    if idx < len(sections):
        return sections[idx]["name"]
    return sections[0]["name"] if sections else "основна тема модуля"


def _seminar_hints(sections: list[dict], level: str) -> list[dict]:
    s1, s2 = _s(sections, 0), _s(sections, 1)
    hints = [
        {"type": "reading",
         "focus": f"Прочитайте текст про {s1.lower()} і дайте відповіді на запитання щодо ключових понять."},
        {"type": "essay-response",
         "focus": f"Напишіть короткий текст (100-150 слів) про {s2.lower()}, використовуючи нову лексику модуля."},
        {"type": "critical-analysis",
         "focus": f"Проаналізуйте взаємозв'язок між поняттями у розділі «{s1}». Обґрунтуйте свою позицію прикладами з тексту."},
        {"type": "error-correction",
         "focus": f"Знайдіть і виправте граматичні та лексичні помилки в реченнях на тему {s1.lower()}."},
    ]
    if level.upper() in ("C1", "C2"):
        p1 = sections[0]["first_point"] if sections else ""
        if p1:
            hints.append({"type": "comparative-study",
                          "focus": f"Порівняйте різні підходи до {s1.lower()}: {p1[:80]}. Визначте спільне та відмінне."})
        else:
            hints.append({"type": "authorial-intent",
                          "focus": f"Визначте авторську позицію щодо {s1.lower()} та оцініть аргументацію тексту."})
    return hints


def _hybrid_hints(sections: list[dict]) -> list[dict]:
    s1, s2 = _s(sections, 0), _s(sections, 1)
    return [
        {"type": "reading",
         "focus": f"Прочитайте текст про {s1.lower()} і дайте відповіді на запитання."},
        {"type": "essay-response",
         "focus": f"Напишіть 5 речень, використовуючи нову лексику з розділу «{s2}»."},
        {"type": "fill-in",
         "focus": f"Вставте правильну граматичну форму у реченнях на тему {s1.lower()}."},
        {"type": "error-correction",
         "focus": f"Знайдіть і виправте помилки у реченнях на тему {s2.lower()}."},
        {"type": "quiz",
         "focus": f"Оберіть правильний варіант: лексика та граматика з розділу «{s1}»."},
        {"type": "match-up",
         "focus": f"З'єднайте терміни з розділу «{s2}» з їхніми визначеннями."},
    ]


def generate_hints(classification: str, sections: list[dict], level: str) -> list[dict]:
    if classification == "seminar":
        return _seminar_hints(sections, level)
    if classification == "hybrid":
        return _hybrid_hints(sections)
    return []


def render_hints_block(hints: list[dict]) -> str:
    lines = ["activity_hints:"]
    for h in hints:
        lines.append(f'  - type: {h["type"]}')
        lines.append(f'    focus: "{h["focus"]}"')
    return "\n".join(lines) + "\n"


def replace_hints_in_text(text: str, new_block: str) -> str | None:
    m = _HINTS_RE.search(text)
    if not m:
        return None
    return text[:m.start()] + new_block + text[m.end():]


def process_plan(path: Path, *, dry_run: bool = False) -> bool:
    text = path.read_text(encoding="utf-8")
    plan = yaml.safe_load(text)
    if not plan:
        return False

    level = plan.get("level", "")
    sequence = plan.get("sequence", 0)
    focus = plan.get("focus", "")
    classification = classify_module(level, sequence, focus)
    if classification == "core":
        return False

    sections = extract_sections(plan)
    hints = generate_hints(classification, sections, level)
    if not hints:
        return False

    new_block = render_hints_block(hints)
    new_text = replace_hints_in_text(text, new_block)
    if new_text is None:
        print(f"  SKIP {path.name}: no activity_hints block found")
        return False
    if new_text == text:
        return False

    if dry_run:
        print(f"\n{'='*60}")
        print(f"  {path.name}  [{level} seq={sequence} focus={focus}] -> {classification}")
        print(f"{'='*60}")
        print(new_block)
    else:
        path.write_text(new_text, encoding="utf-8")
        print(f"  WROTE {path.name} [{classification}]")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite activity_hints to seminar/hybrid types.")
    parser.add_argument("level", nargs="?", choices=LEVELS, help="Level to process (e.g. b2, c1).")
    parser.add_argument("--all", action="store_true", help="Process all levels.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")
    args = parser.parse_args()

    if not args.level and not args.all:
        parser.error("Provide a level or --all.")

    levels = list(LEVELS) if args.all else [args.level]
    total = 0
    for lv in levels:
        plan_dir = PLANS_DIR / lv
        if not plan_dir.is_dir():
            print(f"Skipping {lv}: {plan_dir} not found")
            continue
        plans = sorted(plan_dir.glob("*.yaml"))
        changed = sum(1 for p in plans if process_plan(p, dry_run=args.dry_run))
        label = "would change" if args.dry_run else "changed"
        print(f"\n{lv.upper()}: {changed}/{len(plans)} plans {label}")
        total += changed
    print(f"\nTotal: {total} plans {'would change' if args.dry_run else 'changed'}")


if __name__ == "__main__":
    main()
