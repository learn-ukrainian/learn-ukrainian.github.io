#!/usr/bin/env python3
"""
generate_objectives.py — Generate learning objectives for plans with TBD objectives.

Generates 3-5 objectives per plan based on content_outline sections and focus.
Uses C2-appropriate action verbs (analyze, synthesize, evaluate, produce, etc.)

Usage:
  .venv/bin/python scripts/generate_objectives.py --dry-run
  .venv/bin/python scripts/generate_objectives.py --level c2

GH issue: #702 (Tier 3.3)
"""

import argparse
import glob
import os
import sys
from pathlib import Path

import yaml

PLANS_ROOT = Path("curriculum/l2-uk-en/plans")

# C2-level action verbs in Ukrainian (Bloom's taxonomy: Analyze, Evaluate, Create)
ANALYZE_VERBS = [
    "Аналізувати", "Досліджувати", "Розрізняти", "Порівнювати",
    "Класифікувати", "Систематизувати", "Виявляти",
]
EVALUATE_VERBS = [
    "Оцінювати", "Критично аналізувати", "Обґрунтовувати",
    "Верифікувати", "Рецензувати",
]
CREATE_VERBS = [
    "Створювати", "Продукувати", "Конструювати", "Розробляти",
    "Формулювати", "Укладати", "Моделювати",
]
APPLY_VERBS = [
    "Застосовувати", "Демонструвати", "Використовувати",
    "Інтерпретувати", "Трансформувати",
]

# Focus-specific objective templates
FOCUS_TEMPLATES = {
    "stylistics": [
        "Аналізувати стилістичні засоби в текстах різних функціональних стилів",
        "Продукувати тексти із свідомим використанням стилістичних фігур",
        "Розрізняти авторські стилістичні прийоми та оцінювати їхню ефективність",
    ],
    "grammar": [
        "Систематизувати граматичні явища на рівні усвідомленого володіння",
        "Демонструвати безпомилкове вживання складних граматичних конструкцій",
        "Трансформувати граматичні структури між стилями та регістрами",
    ],
    "rhetoric": [
        "Конструювати переконливі аргументативні тексти із використанням риторичних стратегій",
        "Аналізувати риторичні прийоми в публічних промовах та дебатах",
        "Продукувати усні та письмові висловлювання з ефективною аргументацією",
    ],
    "literature": [
        "Аналізувати літературні твори на рівні глибокої текстуальної інтерпретації",
        "Критично оцінювати літературні тексти в контексті української та європейської традицій",
        "Продукувати вторинні тексти (рецензії, анотації, літературно-критичні есе)",
    ],
    "writing": [
        "Створювати тексти різних жанрів із дотриманням стилістичних норм",
        "Демонструвати майстерне володіння письмовим мовленням на рівні носія",
        "Редагувати та вдосконалювати власні тексти за критеріями стилістичної довершеності",
    ],
    "linguistics": [
        "Досліджувати мовні явища із застосуванням наукових методів",
        "Аналізувати мовну систему як об'єкт лінгвістичного дослідження",
        "Формулювати обґрунтовані висновки на основі мовних даних",
    ],
    "translation": [
        "Застосовувати перекладацькі стратегії для передачі стилістичних нюансів",
        "Аналізувати перекладацькі рішення та оцінювати їхню адекватність",
        "Продукувати переклади, що зберігають стилістичну специфіку оригіналу",
    ],
    "culture": [
        "Інтерпретувати культурні явища в контексті українського суспільства",
        "Аналізувати взаємозв'язки між мовою та культурною ідентичністю",
        "Демонструвати культурну компетентність у професійній комунікації",
    ],
}

# Default objectives for unknown focus areas
DEFAULT_TEMPLATES = [
    "Аналізувати ключові поняття та явища модуля на рівні глибокого розуміння",
    "Продукувати тексти академічного та професійного рівня за тематикою модуля",
    "Демонструвати вільне володіння спеціалізованою лексикою та термінологією",
    "Критично оцінювати джерела та формулювати обґрунтовані висновки",
]


def generate_objectives(plan_data):
    """Generate 3-5 objectives based on plan's focus and content_outline."""
    focus = plan_data.get("focus", "").lower()
    title = plan_data.get("title", "")
    outline = plan_data.get("content_outline", [])

    objectives = []

    # Get focus-specific templates
    # Check title first for more specific matches (e.g., "переклад" in title overrides "literature" focus)
    templates = None
    title_lower = title.lower() if title else ""

    # Title-based overrides (higher priority)
    title_to_focus = {
        "переклад": "translation",
        "риторик": "rhetoric",
        "стилістик": "stylistics",
        "лінгвіст": "linguistics",
        "корпус": "linguistics",
    }
    for keyword, focus_key in title_to_focus.items():
        if keyword in title_lower:
            templates = FOCUS_TEMPLATES.get(focus_key)
            break

    # Fall back to focus field
    if not templates:
        for key, tmpl in FOCUS_TEMPLATES.items():
            if key in focus:
                templates = tmpl
                break

    if not templates:
        for key, tmpl in FOCUS_TEMPLATES.items():
            if key in title_lower:
                templates = tmpl
                break

    if not templates:
        templates = DEFAULT_TEMPLATES

    # Take 3 objectives from templates
    objectives = list(templates[:3])

    # Generate 1-2 more from content_outline section names
    if outline and len(outline) >= 3:
        # Pick a middle section and last substantial section
        mid = outline[len(outline) // 2]
        section_name = mid.get("section", "")
        if section_name and "Практикум" not in section_name and "Checkpoint" not in section_name:
            # Create section-specific objective
            clean_name = section_name.split("(")[0].strip().split("—")[0].strip()
            if clean_name:
                obj = f"Застосовувати знання з теми «{clean_name}» у власній мовній практиці"
                if obj not in objectives:
                    objectives.append(obj)

    # Ensure we have at least 3 objectives
    while len(objectives) < 3:
        for tmpl in DEFAULT_TEMPLATES:
            if tmpl not in objectives:
                objectives.append(tmpl)
                break
        else:
            break

    return objectives[:5]


def main():
    parser = argparse.ArgumentParser(description="Generate objectives for TBD plans")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--level", type=str, default="c2")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    plans = sorted(glob.glob(f"{PLANS_ROOT}/{args.level}/*.yaml"))
    fixed = 0
    skipped = 0

    for pf in plans:
        with open(pf) as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        obj = data.get("objectives", [])
        needs_fix = (
            obj == ["TBD"] or obj == "TBD"
            or (isinstance(obj, list) and len(obj) == 1 and obj[0] == "TBD")
            or not obj  # Missing or empty
        )
        if needs_fix:
            new_objectives = generate_objectives(data)
            data["objectives"] = new_objectives
            fixed += 1

            if args.verbose:
                slug = data.get("slug", os.path.basename(pf))
                print(f"  {slug}: {len(new_objectives)} objectives")
                for o in new_objectives:
                    print(f"    - {o}")

            if not args.dry_run:
                with open(pf, "w") as f:
                    yaml.dump(
                        data, f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                        width=120,
                    )
        else:
            skipped += 1

    print(f"\n{args.level.upper()}: {fixed} plans updated, {skipped} already had objectives")
    if args.dry_run:
        print("(DRY RUN)")


if __name__ == "__main__":
    sys.exit(main())
