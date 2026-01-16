#!/usr/bin/env python3
"""
Generate C1-BIO landing page from curriculum manifest.

Creates landing page with modules ordered chronologically by birth year.

Usage:
    .venv/bin/python scripts/generate_c1_bio_landing.py
"""

import yaml
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
OUTPUT_PATH = PROJECT_ROOT / "docusaurus" / "docs" / "c1-bio" / "index.mdx"


def load_manifest() -> dict:
    """Load curriculum manifest."""
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_landing_page():
    """Generate C1-BIO landing page."""
    manifest = load_manifest()

    c1_bio = manifest["tracks"]["c1-bio"]
    modules = c1_bio["modules"]

    # Group modules by century for better organization
    medieval = []     # Before 1500
    early_modern = [] # 1500-1800
    nineteenth = []   # 1800-1900
    twentieth = []    # 1900-2000
    contemporary = [] # 2000+
    unknown = []      # No birth year

    for mod in modules:
        birth_year = mod.get("birth_year")
        if not birth_year:
            unknown.append(mod)
        elif birth_year < 1500:
            medieval.append(mod)
        elif birth_year < 1800:
            early_modern.append(mod)
        elif birth_year < 1900:
            nineteenth.append(mod)
        elif birth_year < 1980:
            twentieth.append(mod)
        else:
            contemporary.append(mod)

    # Build table rows for each era
    def build_table(mods: list) -> str:
        rows = []
        for mod in mods:
            slug = mod["slug"]
            title = mod["title"]
            birth = mod.get("birth_year", "?")
            death = mod.get("death_year", "")

            # Format life dates
            if death:
                dates = f"{birth}–{death}"
            elif birth != "?":
                dates = f"{birth}–"
            else:
                dates = "—"

            # Check if checkpoint
            is_checkpoint = "checkpoint" in title.lower() or mod.get("focus") == "checkpoint"

            if is_checkpoint:
                display = f"[{title}](./{slug}) <small>(Синтез)</small>"
            else:
                display = f"[{title}](./{slug})"

            rows.append(f"| {display} | {dates} |")

        return "\n".join(rows)

    # Count ready modules (those with MDX files)
    mdx_dir = OUTPUT_PATH.parent
    ready_count = len(list(mdx_dir.glob("*.mdx"))) - 1  # Exclude index.mdx
    total_count = len(modules)

    # Build content
    content = f"""---
sidebar_position: 1
title: C1-BIO - Біографії українців
---

# 🔍 C1-BIO — Біографії видатних українців

**На перевірці — {ready_count}/{total_count} модулів**

Цей трек знайомить вас із життям і досягненнями видатних українців — від середньовічних правителів до сучасних митців. Кожен модуль присвячений одній особистості, її внеску в українську культуру, історію та науку.

**Підхід:** Біографія як вікно в епоху — історичний та культурний контекст.

---

## 🏰 Середньовіччя та давня доба (до 1500)

| Модуль | Роки життя |
|--------|------------|
{build_table(medieval)}

---

## ⚔️ Козацька доба (1500–1800)

| Модуль | Роки життя |
|--------|------------|
{build_table(early_modern)}

---

## 📚 Національне відродження (1800–1900)

| Модуль | Роки життя |
|--------|------------|
{build_table(nineteenth)}

---

## 🎭 XX століття (1900–1980)

| Модуль | Роки життя |
|--------|------------|
{build_table(twentieth)}

---

## 🌟 Сучасники (від 1980)

| Модуль | Роки життя |
|--------|------------|
{build_table(contemporary)}

"""

    # Add unknown dates section if any
    if unknown:
        content += f"""---

## 📋 Інші модулі

| Модуль | Роки життя |
|--------|------------|
{build_table(unknown)}

"""

    # Add progress section
    content += f"""---

## Прогрес

- **Готові модулі:** {ready_count}
- **Заплановані модулі:** {total_count}
- **Завершення:** {round(ready_count / total_count * 100) if total_count > 0 else 0}%
"""

    return content


def main():
    print("Generating C1-BIO landing page...")

    content = generate_landing_page()

    # Write output
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Written: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
