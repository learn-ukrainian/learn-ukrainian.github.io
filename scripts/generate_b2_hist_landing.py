#!/usr/bin/env python3
"""Generate B2-HIST landing page from manifest."""

import yaml
from pathlib import Path

# Phase titles in Ukrainian
PHASE_TITLES = {
    "HIST.1": "Витоки та ранні цивілізації",
    "HIST.2": "Київська Русь",
    "HIST.3": "Монгольська доба та Галицько-Волинь",
    "HIST.4": "Литовсько-польська доба",
    "HIST.5": "Становлення козацтва",
    "HIST.6": "Хмельницький і козацька держава",
    "HIST.7": "Мазепа і кінець Гетьманщини",
    "HIST.8": "Імперська доба",
    "HIST.9": "Перша світова війна і революція",
    "HIST.10": "Радянський період і трагедії",
    "HIST.11": "Повоєнна радянська Україна",
    "HIST.12": "Незалежність і сучасність",
    "HIST.13": "Російська агресія",
}

def extract_phase_num(phase_str):
    """Extract phase number from phase string like 'HIST.1 [Origins]'."""
    if not phase_str:
        return "HIST.0"
    return phase_str.split()[0]

def phase_sort_key(phase):
    """Sort phases numerically (HIST.1, HIST.2, ..., HIST.13)."""
    try:
        return int(phase.split(".")[1])
    except (IndexError, ValueError):
        return 0

def generate_landing_page():
    """Generate the B2-HIST landing page."""

    # Load manifest
    manifest_path = Path("curriculum/l2-uk-en/curriculum.yaml")
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    modules = manifest["tracks"]["b2-hist"]["modules"]

    # Group modules by phase
    phases = {}
    for i, mod in enumerate(modules, 1):
        phase = extract_phase_num(mod.get("phase", ""))
        if phase not in phases:
            phases[phase] = []
        phases[phase].append({
            "num": i,
            "slug": mod["slug"],
            "title": mod["title"],
            "type": mod.get("type", ""),
            "tags": mod.get("tags", [])
        })

    # Count completed modules (for now all are skeleton)
    completed = 0  # Will update when modules have content

    # Generate markdown
    output = []

    # Header
    output.append("""---
sidebar_position: 1
title: B2-HIST - Історія України
---

# B2-HIST - Історія України

**В розробці** (140 модулів)

## Історія України — від витоків до сьогодення!

Цей трек — подорож крізь тисячоліття української історії. Від Трипільської культури до сучасної незалежності — ви вивчатимете історію українською мовою на рівні B2.

**Чого ви навчитеся:**
- Давня історія — Трипілля, скіфи, Київська Русь
- Козацька доба — Запорозька Січ, Богдан Хмельницький
- Національне відродження — XIX-XX століття
- Сучасна Україна — незалежність, Революція Гідності

**Підхід:** Деколонізована перспектива з опорою на українські джерела

---
""")

    # Generate phase sections
    for phase_num in sorted(phases.keys(), key=phase_sort_key):
        phase_title = PHASE_TITLES.get(phase_num, phase_num)
        mods = phases[phase_num]

        output.append(f"\n## {phase_num}: {phase_title}\n")
        output.append("\n| # | Модуль | Статус |")
        output.append("|---|--------|--------|")

        for mod in mods:
            title = mod["title"]
            slug = mod["slug"]
            num = mod["num"]
            mod_type = mod["type"]
            tags = mod["tags"]

            # Format title with type indicator - use slug for URL
            if mod_type == "synthesis":
                display = f"[{title}](./{slug}) <small>(Синтез)</small>"
            else:
                display = f"[{title}](./{slug})"

            # Status - check if new/expanded
            if "new" in tags:
                status = "📝"  # skeleton/new
            elif "expanded" in tags:
                status = "📝"  # skeleton/expanded
            else:
                status = "📝"  # For now all skeleton

            output.append(f"| {num} | {display} | {status} |")

    # Progress section
    output.append("""

---

## Прогрес

- **Готові модулі:** 0 (інфраструктура завершена)
- **Заплановані модулі:** 140
- **Завершення:** 0% (скелети готові, контент в розробці)

## Умовні позначення

- ✅ — Модуль завершено
- 📝 — Скелет (контент в розробці)
""")

    return "\n".join(output)

if __name__ == "__main__":
    content = generate_landing_page()

    output_path = Path("docusaurus/docs/b2-hist/index.mdx")
    with open(output_path, "w") as f:
        f.write(content)

    print(f"Generated {output_path}")
    print(f"Total lines: {len(content.splitlines())}")
