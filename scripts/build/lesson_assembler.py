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
            if item.get("type") == "unjumble" and "words" in item and "items" not in item:
                item["items"] = item["words"]
            if item.get("type") == "unjumble":
                for row in item.get("items", []):
                    if "answer" not in row and "sentence" in row:
                        row["answer"] = row["sentence"]
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
            if item.get("type") == "odd-one-out":
                for row in item.get("items", []):
                    options = row.get("options")
                    if isinstance(row.get("correct"), int) or not isinstance(options, list):
                        continue
                    texts = []
                    odd_index = None
                    for index, option in enumerate(options):
                        if isinstance(option, dict):
                            texts.append(str(option.get("text") or option.get("word") or ""))
                            if option.get("correct") is True and odd_index is None:
                                odd_index = index
                        else:
                            texts.append(str(option))
                    if odd_index is not None:
                        row["correct"] = odd_index
                        row["words"] = texts
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


# A1 tabs are bilingual in generate_mdx (Ukrainian first, English after).
_A1_TAB_LABELS = {
    "Vocabulary": "Словник — Vocabulary",
    "Activities": "Вправи — Activities",
    "Resources": "Ресурси — Resources",
}


def _plan_level(plan: dict) -> str:
    raw = str(plan.get("level") or plan.get("base_level") or "a1").strip().lower()
    return raw.split("-")[0] if raw else "a1"


def _is_a1(level: str) -> bool:
    return _plan_level({"level": level}) == "a1"


_DANGLING_LEAD_IN = re.compile(
    r"(?i)(?:The (?:safest|useful) A1 pattern is:|Treat the first phrases as whole expressions:|"
    r"The core call frame is:|Official Ukrainian emergency numbers[^\n]*:)\s*"
)
_NARRATOR_HELLO = re.compile(r"(?m)^Привіт!?\s*")


def _clean_a1_landing_prose(body: str) -> str | None:
    """A1 landing prose: module-9 shape after stripping broken original extras.

    Tables, tip boxes, and code fences belong in lessons, not on the landing.
    If nothing usable remains, return None (lesson list only — never dump plan YAML).
    """
    body = re.sub(r"^# [^\n]+\n", "", body)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    body = re.sub(r":::tip(?:\[[^\]]*\])?.*?:::", "", body, flags=re.DOTALL)
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    body = re.sub(r"(?m)^\s*\|.*\|\s*$\n?", "", body)
    body = _DANGLING_LEAD_IN.sub("", body)
    body = _NARRATOR_HELLO.sub("", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if len(body) < 40:
        return None
    return body


def _original_intro(module_dir: Path, slug: str) -> str | None:
    """Usable A1 landing prose from the previous edition, or None if there is none."""
    candidates = [module_dir.parent.parent / "a1-v1" / slug / "module.md"]
    if len(module_dir.parents) >= 4:
        candidates.append(module_dir.parents[3] / "site/src/content/docs/a1-v1" / f"{slug}.mdx")
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".mdx":
            match = re.search(
                r'<TabItem label="Lesson">\s*(.*?)(?=^## |^</TabItem>)',
                text, flags=re.DOTALL | re.MULTILINE,
            )
            body = match.group(1) if match else ""
        else:
            body = re.split(r"^## ", text, maxsplit=1, flags=re.MULTILINE)[0]
        cleaned = _clean_a1_landing_prose(body)
        if cleaned:
            return cleaned
    return None


def _writer_landing_overview(module_dir: Path) -> str | None:
    """Optional Gemini-authored 9-shape overview (upgrade writer, lesson 1)."""
    path = module_dir / "landing-overview.md"
    if not path.is_file():
        return None
    return _clean_a1_landing_prose(path.read_text(encoding="utf-8"))


def _landing_intro(level: str, module_dir: Path, slug: str, cards: list[str]) -> str:
    """Level-specific landing Lesson tab. A1 is bilingual; A2+ is Ukrainian-only.

    A1 prefers a writer landing-overview.md, then a *cleaned* original opening.
    If neither exists, the landing is the lesson list only — never plan YAML.
    A2+ never copies an English-carrier original (full immersion).
    """
    if _is_a1(level):
        intro = _writer_landing_overview(module_dir) or _original_intro(module_dir, slug) or ""
        heading = "## Уроки — Lessons"
        return f"{intro}\n\n{heading}\n\n" + "\n".join(cards) if intro else f"{heading}\n\n" + "\n".join(cards)
    heading = "## Уроки"
    return f"{heading}\n\n" + "\n".join(cards)


_EXAMPLE_FENCE = re.compile(
    r"```(?:text)?\r?\n(.*?)```(?:[ \t]*\n(?:(?!\|)[^\n]{0,100}\n){0,3})?((?:\|[^\n]*\|\n)+)?",
    re.DOTALL,
)


def _rows_from_support_table(table: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in table.splitlines():
        cells = [cell.strip().strip("*") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        if set(cells[1]) <= set("-: ") or "English" in cells[1] or "Україн" in cells[0]:
            continue
        rows.append((cells[0], cells[1]))
    return rows


def _normalize_a1_example_fences(markdown: str) -> str:
    """A1: learner examples are bilingual bullets (module 9), never ```text fences."""

    def replace(match: re.Match[str]) -> str:
        fence_body, table = match.group(1), match.group(2) or ""
        pairs = _rows_from_support_table(table)
        if not pairs:
            pairs = [(line.strip(), "") for line in fence_body.splitlines() if line.strip()]
        lines = []
        for uk, en in pairs:
            if en:
                lines.append(f"- **{uk}** — {en}")
            else:
                lines.append(f"- **{uk}**")
        return "\n".join(lines) + "\n\n"

    return _EXAMPLE_FENCE.sub(replace, markdown)


_MODULE_COMPLETION_HEADING = re.compile(
    r"(?im)^###\s+.*(?:Заве.?ршення мо.?дуля|Module completion)\s*$"
)
_FOLLOWING_SUPPORT_TABLE = re.compile(
    r"\A\s*((?:\|[^\n]*\|\n)+)",
)


def _normalize_a1_module_close(markdown: str) -> str:
    """Last A1 lesson: module-9 close is 'Підсумок модуля — Module summary' + bullets, not a completion table."""
    match = _MODULE_COMPLETION_HEADING.search(markdown)
    if not match:
        return markdown
    rest = markdown[match.end():]
    table_match = _FOLLOWING_SUPPORT_TABLE.search(rest)
    heading = "### Підсумок модуля — Module summary\n\n"
    if not table_match:
        return markdown[: match.start()] + heading + rest.lstrip("\n")
    bullets = []
    for uk, en in _rows_from_support_table(table_match.group(1)):
        if en:
            bullets.append(f"- **{uk}** — {en}")
        else:
            bullets.append(f"- **{uk}**")
    body = "\n".join(bullets) + "\n\n" + rest[table_match.end():].lstrip("\n")
    return markdown[: match.start()] + heading + body


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
    level = _plan_level(plan)
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
        body = (source / "module.md").read_text(encoding="utf-8")
        if _is_a1(level):
            body = _normalize_a1_example_fences(body)
            if n == numbers[-1]:
                body = _normalize_a1_module_close(body)
        mdx = generate_mdx(
            re.sub(r"^(>\s*\*\*[^*]+)\*\*:", r"\1:**", body, flags=re.MULTILINE), n,
            yaml_activities=activities, meta_data=metadata,
            vocab_items=list(vocabulary.values()), external_resources={"books": lesson_resources},
            level=level, pipeline_version="v7-upgrade", build_status="validated",
        ).replace("\n{/**/}\n", "\n")
        previous = base if offset == 0 else f"{base}{n - 1}/"
        following = f"{base}{n + 1}/" if offset + 1 < len(lessons) else base
        for label, anchor in [("Vocabulary", "vocabulary"), ("Activities", "activities"), ("Resources", "resources")]:
            tab = _A1_TAB_LABELS[label] if _is_a1(level) else label
            mdx = mdx.replace(f'<TabItem label="{tab}">', f'<TabItem label="{tab}">\n\n<span id="{anchor}"></span>')
        mdx = _frontmatter(mdx, draft=not validated, prev=previous, next=following, lesson=n, module_slug=slug)
        mdx += f'\n<nav aria-label="Lesson navigation">\n\n[Previous]({previous}) · [Module]({base}) · [Next]({following})\n\n</nav>\n'
        pages[str(n)] = mdx
        cards.append(f'- [{n}. {lesson["title"]}]({base}{n}/) — {lesson["minutes"]} min')
        tab_links.append((n, lesson["title"]))
    intro = _landing_intro(level, module_dir, slug, cards)
    landing = generate_mdx(
        intro, int(plan.get("sequence", 1)), yaml_activities=workbook,
        meta_data=dict(plan, level=level), vocab_items=list(vocabulary.values()),
        external_resources={"books": list(resources.values())}, level=level,
        pipeline_version="v7-upgrade", build_status="validated",
    ).replace("\n{/**/}\n", "\n")
    for label, anchor in [("Vocabulary", "vocabulary"), ("Activities", "activities"), ("Resources", "resources")]:
        tab = _A1_TAB_LABELS[label] if _is_a1(level) else label
        links = " · ".join(f"[{n}. {title}]({base}{n}/#{anchor})" for n, title in tab_links)
        landing = landing.replace(f'<TabItem label="{tab}">', f'<TabItem label="{tab}">\n\n{links}')
    pages = {"index": _frontmatter(landing, draft=not validated, lessons=[
        {"n": item["n"], "title": item["title"], "minutes": item["minutes"], "href": f'{base}{item["n"]}/'}
        for item in lessons
    ]), **pages}
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in pages.items():
        (output_dir / f"{name}.mdx").write_text(content, encoding="utf-8")
    return pages
