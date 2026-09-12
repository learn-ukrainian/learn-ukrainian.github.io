"""Assemble parallel lesson pages using the existing V7 component renderer."""
from __future__ import annotations

import copy
import json
import re
import unicodedata
from pathlib import Path

import yaml

from scripts.generate_mdx.core import generate_mdx, parse_frontmatter
from scripts.yaml_activities import ActivityParser


def _rows(path: Path, key: str) -> list[dict]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return value.get(key, []) if isinstance(value, dict) else value


def _activities(path: Path) -> tuple[list, list]:
    """Bridge the gold writer's answer-form translations to V7's data model.

    Preserve placement separately: ActivityParser otherwise flattens the two
    lists and drops placement, which would duplicate inline tasks on a landing.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    parser = ActivityParser()
    all_items, workbook = [], []
    for placement in ("inline", "workbook"):
        for original in raw.get(placement, []):
            item = copy.deepcopy(original)
            if item.get("type") == "unjumble" and "words" in item:
                item["items"] = item["words"]
            if item.get("type") == "true-false" and "statements" in item:
                item["items"] = item["statements"]
            if item.get("type") == "observe" and "pairs" in item:
                item["examples"] = [f'{row["left"]} — {row["right"]}' for row in item["pairs"]]
                item["prompt"] = item["instruction"]
            if item.get("type") == "translate":
                for row in item.get("items", []):
                    if "source" not in row and "sentence" in row:
                        row["source"] = row["sentence"]
                    if "options" not in row and "answer" in row:
                        row["options"] = [{"text": row["answer"], "correct": True}]
            parsed = parser._parse_activity(item)
            all_items.append(parsed)
            if placement == "workbook":
                workbook.append(parsed)
    return all_items, workbook


def _lemma(item: dict) -> str:
    return unicodedata.normalize("NFD", str(item.get("lemma", item.get("word", "")))).replace("\u0301", "").casefold()


def _frontmatter(mdx: str, **extra: object) -> str:
    data, body = parse_frontmatter(mdx)
    data.update(extra)
    return "---\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False) + "---\n" + body


def assemble_lessons(module_dir: Path, output_dir: Path, plan_path: Path, *, validated: bool = True) -> dict[str, str]:
    """Emit index.mdx and numbered pages; vocabulary accumulates by first use.

    ``output_dir`` is the module directory under the canonical site level. Source
    artifacts remain in ``module_dir/lesson-N``; no source content is rewritten.
    """
    manifest = yaml.safe_load((module_dir / "lessons.yaml").read_text(encoding="utf-8"))
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    lessons = manifest["lessons"]
    numbers = [item["n"] for item in lessons]
    if numbers != list(range(1, len(lessons) + 1)):
        raise ValueError("Lesson numbers must be contiguous and start at 1")
    slug = plan.get("slug")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("Plan slug must be a lowercase URL slug")
    level = "a1"
    base = f"/{level}/{slug}/"
    pages: dict[str, str] = {}
    vocabulary: dict[str, dict] = {}
    workbook = []
    resources: dict[str, dict] = {}
    cards = []
    tab_links = []
    for offset, lesson in enumerate(lessons):
        n = lesson["n"]
        source = module_dir / f"lesson-{n}"
        activities, lesson_workbook = _activities(source / "activities.yaml")
        for item in _rows(source / "vocabulary.yaml", "vocabulary"):
            vocabulary.setdefault(_lemma(item), item)
        lesson_resources = _rows(source / "resources.yaml", "resources")
        for item in lesson_resources:
            resources.setdefault(json.dumps(item, sort_keys=True, ensure_ascii=False), item)
        workbook.extend(lesson_workbook)
        metadata = dict(plan, title=lesson["title"], level=level)
        mdx = generate_mdx(
            re.sub(r"^(>\s*\*\*[^*]+)\*\*:", r"\1:**",
                   (source / "module.md").read_text(encoding="utf-8"), flags=re.MULTILINE), n,
            yaml_activities=activities, meta_data=metadata,
            vocab_items=list(vocabulary.values()), external_resources={"books": lesson_resources},
            level="a1", pipeline_version="v7-upgrade", build_status="validated",
        ).replace("\n{/**/}\n", "\n")
        previous = base if offset == 0 else f"{base}{n - 1}/"
        following = f"{base}{n + 1}/" if offset + 1 < len(lessons) else base
        for label, anchor in [("Vocabulary", "vocabulary"), ("Activities", "activities"), ("Resources", "resources")]:
            mdx = mdx.replace(f'<TabItem label="{label}">', f'<TabItem label="{label}">\n\n<span id="{anchor}"></span>')
        mdx = _frontmatter(mdx, draft=not validated, prev=previous, next=following, lesson=n, module_slug=slug)
        mdx += f'\n<nav aria-label="Lesson navigation">\n\n[Previous]({previous}) · [Module]({base}) · [Next]({following})\n\n</nav>\n'
        pages[str(n)] = mdx
        cards.append(f'- [{n}. {lesson["title"]}]({base}{n}/) — {lesson["minutes"]} min')
        tab_links.append((n, lesson["title"]))
    objectives = plan.get("objectives", [])
    intro = "## Objectives\n\n" + "\n".join(f"- {item}" for item in objectives)
    intro += "\n\n## Lessons\n\n" + "\n".join(cards)
    landing = generate_mdx(
        intro, int(plan.get("sequence", 1)), yaml_activities=workbook,
        meta_data=dict(plan, level=level), vocab_items=list(vocabulary.values()),
        external_resources={"books": list(resources.values())}, level="a1",
        pipeline_version="v7-upgrade", build_status="validated",
    ).replace("\n{/**/}\n", "\n")
    for label, anchor in [("Vocabulary", "vocabulary"), ("Activities", "activities"), ("Resources", "resources")]:
        links = " · ".join(f"[{n}. {title}]({base}{n}/#{anchor})" for n, title in tab_links)
        landing = landing.replace(f'<TabItem label="{label}">', f'<TabItem label="{label}">\n\n{links}')
    pages = {"index": _frontmatter(landing, draft=not validated, lessons=[
        {"n": item["n"], "title": item["title"], "minutes": item["minutes"], "href": f'{base}{item["n"]}/'}
        for item in lessons
    ]), **pages}
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in pages.items():
        (output_dir / f"{name}.mdx").write_text(content, encoding="utf-8")
    return pages
