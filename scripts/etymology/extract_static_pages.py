"""Generate static HTML etymology pages for ESUM entries.

Per Decision Card 2026-05-15-etymology-feature-design + 2026-05-15 architectural
pivot (POC): pages are emitted as RAW HTML into `starlight/public/etymology/`
rather than MDX into `starlight/src/content/docs/etymology/`. Reason: 31k pages
overwhelm Starlight's content-collection pass (SIGABRT at 8GB heap, 19+ min
build at 16GB heap — verified 2026-05-15). Static HTML in `public/` is served
as-is by Astro / github.io without entering the MDX pipeline.

Trade-off: pages have minimal Starlight chrome (no sidebar, no built-in
search). Etymology pages were `sidebar.hidden: true` under the MDX design
anyway. A separate landing + search shipped in Phase 2 handles browse/search
needs; the interactive explorer in Phase 3 handles cognate-tree navigation.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.etymology.transliterate import transliterate
except ModuleNotFoundError:  # pragma: no cover - supports direct script execution
    from transliterate import transliterate

DEFAULT_DB = Path("data/sources.db")
DEFAULT_OUTPUT_DIR = Path("starlight/public/etymology")
ARCHIVE_URL = "https://archive.org/search?query=Етимологічний%20словник%20української%20мови"
SITE_TITLE = "Learn Ukrainian"
MARKER_LABELS = {
    "ав.": "Авестійська",
    "болг.": "Болгарська",
    "бр.": "Білоруська",
    "гот.": "Готська",
    "гр.": "Грецька",
    "дінд.": "Давньоіндійська",
    "др.": "Давньоруська",
    "іє.": "Індоєвропейська",
    "лат.": "Латинська",
    "лит.": "Литовська",
    "п.": "Польська",
    "псл.": "Праслов'янська",
    "р.": "Російська",
    "слн.": "Словенська",
    "слц.": "Словацька",
    "стел.": "Старослов'янська",
    "схв.": "Сербохорватська",
    "ч.": "Чеська",
}

# Single inline CSS shipped to /etymology/etymology.css. Light/dark aware,
# Cyrillic-friendly system stack, mobile-responsive, no external dependencies.
ETYMOLOGY_CSS = """\
:root {
  --bg: #ffffff;
  --fg: #1f1f1f;
  --muted: #5a5a5a;
  --accent: #c2410c;
  --border: #e2e2e2;
  --code-bg: #f5f5f5;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #15181c;
    --fg: #e7e7e7;
    --muted: #a0a0a0;
    --accent: #fb923c;
    --border: #2a2e34;
    --code-bg: #1f2228;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--fg); }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", system-ui, sans-serif;
  line-height: 1.6;
  font-size: 17px;
}
header, main, footer { max-width: 760px; margin: 0 auto; padding: 1rem 1.25rem; }
header { border-bottom: 1px solid var(--border); }
header nav { font-size: 0.875rem; color: var(--muted); }
header nav a { color: var(--accent); text-decoration: none; }
header nav a:hover { text-decoration: underline; }
h1 { font-size: 2.5rem; font-weight: 700; margin: 1rem 0 0.5rem; letter-spacing: -0.01em; }
h2 { font-size: 1.25rem; font-weight: 600; margin: 2rem 0 0.75rem; border-bottom: 1px solid var(--border); padding-bottom: 0.35rem; }
p { margin: 0.75rem 0; }
.ref { color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem; }
table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
th, td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
th { font-weight: 600; color: var(--muted); font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.04em; }
.etymology-body { white-space: pre-wrap; word-wrap: break-word; }
.proto { background: var(--code-bg); padding: 0.5rem 0.75rem; border-radius: 4px; margin: 1rem 0; }
.proto strong { color: var(--accent); }
.muted { color: var(--muted); }
.entries-list { list-style: none; padding: 0; }
.entries-list li { padding: 0.75rem 0; border-bottom: 1px solid var(--border); }
.entries-list li a { color: var(--accent); text-decoration: none; font-weight: 600; }
.entries-list li a:hover { text-decoration: underline; }
.entries-list .summary { color: var(--muted); font-size: 0.9rem; }
footer { border-top: 1px solid var(--border); margin-top: 3rem; padding-top: 1rem; color: var(--muted); font-size: 0.875rem; }
footer a { color: var(--accent); text-decoration: none; }
footer a:hover { text-decoration: underline; }
@media (max-width: 600px) {
  body { font-size: 16px; }
  h1 { font-size: 2rem; }
  header, main, footer { padding: 0.75rem 1rem; }
  table { font-size: 0.875rem; }
  th, td { padding: 0.4rem 0.5rem; }
}
"""


@dataclass(frozen=True)
class Entry:
    id: int
    lemma: str
    vol: int
    page: int
    etymology_text: str
    cognate_forms: dict[str, str]
    proto_form: str | None
    slug: str
    page_slug: str


def _esc(value: str) -> str:
    """Escape user-supplied text for HTML."""
    return html.escape(value, quote=True)


def _summary(value: str, length: int = 80) -> str:
    collapsed = re.sub(r"\s+", " ", value).strip()
    return _esc(collapsed[:length])


def _page_stem(entry: sqlite3.Row, slug_counts: Counter[tuple[str, int, int]], ordinal: int) -> str:
    slug = transliterate(entry["lemma"]) or f"entry-{entry['id']}"
    if slug_counts[(slug, entry["vol"], entry["page"])] > 1:
        return f"{slug}-{entry['vol']}-{entry['page']}-{ordinal}"
    return f"{slug}-{entry['vol']}-{entry['page']}"


def load_entries(db_path: Path) -> list[Entry]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                e.id,
                e.lemma,
                e.vol,
                e.page,
                e.etymology_text,
                COALESCE(f.cognate_forms, '{}') AS cognate_forms,
                f.proto_form
            FROM esum_etymology_meta e
            LEFT JOIN esum_cognate_forms f ON f.entry_id = e.id
            ORDER BY e.lemma COLLATE NOCASE, e.vol, e.page, e.id
            """
        ).fetchall()
    finally:
        conn.close()

    slug_counts: Counter[tuple[str, int, int]] = Counter(
        (transliterate(row["lemma"]) or f"entry-{row['id']}", row["vol"], row["page"]) for row in rows
    )
    seen: Counter[tuple[str, int, int]] = Counter()
    entries = []
    for row in rows:
        slug = transliterate(row["lemma"]) or f"entry-{row['id']}"
        key = (slug, row["vol"], row["page"])
        seen[key] += 1
        try:
            cognate_forms = json.loads(row["cognate_forms"])
        except json.JSONDecodeError:
            cognate_forms = {}
        if not isinstance(cognate_forms, dict):
            cognate_forms = {}
        entries.append(
            Entry(
                id=row["id"],
                lemma=row["lemma"],
                vol=row["vol"],
                page=row["page"],
                etymology_text=row["etymology_text"],
                cognate_forms={str(key): str(value) for key, value in cognate_forms.items()},
                proto_form=row["proto_form"],
                slug=slug,
                page_slug=_page_stem(row, slug_counts, seen[key]),
            )
        )
    return entries


def _render_html_shell(title: str, description: str, lemma_display: str, body_inner: str) -> str:
    """Wrap inner body content in a full HTML5 document."""
    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title>
<meta name="description" content="{_esc(description)}">
<link rel="stylesheet" href="/etymology/etymology.css">
</head>
<body>
<header>
<nav>
<a href="/">{SITE_TITLE}</a> ›
<a href="/etymology/">Етимологія</a> ›
<span>{_esc(lemma_display)}</span>
</nav>
</header>
<main>
{body_inner}
</main>
<footer>
<a href="/etymology/">Усі статті</a> · <a href="/etymology/explore/">Інтерактивний дослідник</a> · <a href="/">Курс</a>
</footer>
</body>
</html>
"""


def render_entry_page(entry: Entry) -> str:
    """Render a single-entry etymology page as HTML."""
    cognate_rows = [
        f"<tr><td>{_esc(MARKER_LABELS.get(marker, marker))} ({_esc(marker)})</td><td>{_esc(form)}</td></tr>"
        for marker, form in sorted(entry.cognate_forms.items())
    ]
    if cognate_rows:
        cognate_block = (
            "<table>\n"
            "<thead><tr><th>Мова</th><th>Форма</th></tr></thead>\n"
            f"<tbody>\n{chr(10).join(cognate_rows)}\n</tbody>\n"
            "</table>"
        )
    else:
        cognate_block = "<p class=\"muted\"><em>Структурованих форм когнатів для цієї статті не вилучено.</em></p>"

    proto_block = ""
    if entry.proto_form:
        proto_block = (
            f"\n<div class=\"proto\"><strong>Праслов'янське:</strong> {_esc(entry.proto_form)}</div>"
        )

    body_inner = f"""<h1>{_esc(entry.lemma)}</h1>
<p class="ref">Том {entry.vol}, с. {entry.page} • Етимологічний словник української мови (ЕСУМ)</p>

<h2>Когнати</h2>
{cognate_block}{proto_block}

<h2>Етимологія</h2>
<div class="etymology-body">{_esc(entry.etymology_text)}</div>

<h2>Джерело</h2>
<p>ЕСУМ, том {entry.vol}, с. {entry.page}. <a href="{ARCHIVE_URL}">Архів вікі-ресурсів</a></p>"""

    title = f"{entry.lemma} — Етимологія | {SITE_TITLE}"
    description = f"Етимологія слова «{entry.lemma}» — ЕСУМ, том {entry.vol}, с. {entry.page}"
    return _render_html_shell(title, description, entry.lemma, body_inner)


def render_landing_page(entries: list[Entry]) -> str:
    """Render a polysemy landing page listing all entries that share a slug."""
    unique_lemmas = sorted({entry.lemma for entry in entries})
    title_display = " / ".join(unique_lemmas[:3])
    items = "\n".join(
        f'<li><a href="{entry.page_slug}/">том {entry.vol}, с. {entry.page}</a> — '
        f'<span class="summary">{_summary(entry.etymology_text)}…</span></li>'
        for entry in entries
    )
    body_inner = f"""<h1>{_esc(title_display)}</h1>
<p class="ref">Це слово має кілька статей в ЕСУМ — від різних коренів або різних значень.</p>

<ul class="entries-list">
{items}
</ul>"""
    title = f"{title_display} — Етимологія | {SITE_TITLE}"
    description = f"Етимологія слова «{title_display}» — кілька статей в ЕСУМ"
    return _render_html_shell(title, description, title_display, body_inner)


def _write_css(output_dir: Path) -> None:
    """Write the shared etymology.css stylesheet."""
    (output_dir / "etymology.css").write_text(ETYMOLOGY_CSS, encoding="utf-8")


def generate_pages(db_path: Path, output_dir: Path) -> dict[str, int]:
    entries = load_entries(db_path)
    grouped: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.slug].append(entry)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_css(output_dir)

    files_written = 0
    for slug, slug_entries in sorted(grouped.items()):
        if len(slug_entries) == 1:
            (output_dir / f"{slug}.html").write_text(
                render_entry_page(slug_entries[0]), encoding="utf-8"
            )
            files_written += 1
            continue

        (output_dir / f"{slug}.html").write_text(
            render_landing_page(slug_entries), encoding="utf-8"
        )
        files_written += 1
        for entry in slug_entries:
            (output_dir / f"{entry.page_slug}.html").write_text(
                render_entry_page(entry), encoding="utf-8"
            )
            files_written += 1

    return {
        "entries": len(entries),
        "slug_groups": len(grouped),
        "files_written": files_written,
        "polysemy_landing_pages": sum(1 for slug_entries in grouped.values() if len(slug_entries) > 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = generate_pages(args.db, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
