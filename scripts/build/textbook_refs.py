"""Resolve textbook chunk references to pidruchnyk.com.ua deep links.

Each module's wiki article cites textbook chunks like "Source 8" which map
to chunk_ids in data/sources.db.  This module resolves those to clickable
URLs pointing to the exact page in the PDF on pidruchnyk.com.ua.

URL pattern: https://pidruchnyk.com.ua/uploads/book/{source_file}.pdf#page={N}
Page number extracted from the chunk title field ("Сторінка 73" → 73).

Usage:
    from build.textbook_refs import get_textbook_links
    links = get_textbook_links("a2", "genitive-intro")
    # Returns: [{"author": "Голуб", "grade": 6, "year": "2023",
    #            "title": "Українська мова, 6 клас",
    #            "url": "https://pidruchnyk.com.ua/uploads/book/...pdf#page=73"}, ...]
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
WIKI_DIR = PROJECT_ROOT / "wiki"

# pidruchnyk.com.ua hosts PDFs at this base URL
_PDF_BASE = "https://pidruchnyk.com.ua/uploads/book"

# Manual overrides: source_file → actual PDF filename on pidruchnyk
# (site naming is inconsistent — some use hyphens, some underscores, some different spelling)
_PDF_OVERRIDES: dict[str, str] = {
    # Grade 5: underscores, no "klas"
    "5-klas-ukrmova-avramenko-2022": "5_ukrmova_avramenko_2022",
    "5-klas-ukrmova-golub-2022": "5_ukrmova_golub_2022",
    "5-klas-ukrmova-litvinova-2022": "5_ukrmova_litvinova_2022",
    "5-klas-ukrmova-zabolotnyi-2023": "5-ukrmova-zabolotny-2023",
    # Grade 10/11: zabolotnyi uses different transliteration on site
    "10-klas-ukrmova-zabolotnyi-2018": "10-klas-ukrajinska-mova-zabolotnij-2018",
}

# Fallback: shkola.in.ua (Issuu viewer, no page deep-links but textbook is viewable)
_SHKOLA_OVERRIDES: dict[str, str] = {
    "4-klas-ukrmova-zaharijchuk": "https://shkola.in.ua/4-klas-ukrainska-mova-zaharijchuk.html",
    "5-klas-ukrmova-uhor-2022-1": "https://shkola.in.ua/5-klas-ukrainska-mova-uhor-2022.html",
    "6-klas-ukrmova-betsa-2023": "https://shkola.in.ua/6-klas-ukrainska-mova-betsa-2023.html",
    "6-klas-ukrmova-zabolotnyi-2020": "https://shkola.in.ua/2835-ukrainska-mova-6-klas-zabolotnyi-2023.html",
    "7-klas-ukrmova-litvinova-2024": "https://shkola.in.ua/7-klas-ukrainska-mova-litvinova-2024.html",
    "9-klas-ukrajinska-mova-avramenko-2017": "https://shkola.in.ua/9-klas-ukrainska-mova-avramenko-2017.html",
    "9-klas-ukrajinska-mova-voron-2017": "https://shkola.in.ua/9-klas-ukrainska-mova-voron-2017.html",
    "9-klas-ukrajinska-mova-zabolotnij-2017": "https://shkola.in.ua/9-klas-ukrainska-mova-zabolotnyi-2017.html",
    "9-klas-ukrmova-zabolotnyi-2017": "https://shkola.in.ua/9-klas-ukrainska-mova-zabolotnyi-2017.html",
    "11-klas-ukrmova-zabolotnyi-2019": "https://shkola.in.ua/11-klas-ukrainska-mova-zabolotnyi-2019.html",
}

# Source files not on either site
_PDF_NOT_AVAILABLE: set[str] = set()  # All covered by pidruchnyk or shkola fallback

# Author display names (source_file fragment → Ukrainian name)
_AUTHORS = {
    "avramenko": "Авраменко О. М.",
    "zabolotnyi": "Заболотний О. В.",
    "zabolotnij": "Заболотний О. В.",
    "golub": "Голуб Н. Б.",
    "litvinova": "Літвінова І. М.",
    "glazova": "Глазова О. П.",
    "voron": "Ворон А. А.",
    "karaman": "Караман С. О.",
    "bolshakova": "Большакова І. О.",
    "vashulenko": "Вашуленко М. С.",
    "kravcova": "Кравцова Н. М.",
    "zaharijchuk": "Захарійчук М. Д.",
    "betsa": "Беца І. Ф.",
    "onatiy": "Онатій А. В.",
    "uhor": "Угор О. М.",
    "semenog": "Семеног О. М.",
}


def _parse_page(title: str) -> int | None:
    """Extract page number from chunk title like 'Сторінка 73'."""
    m = re.search(r"Сторінка\s+(\d+)", title)
    return int(m.group(1)) if m else None


def _parse_author(source_file: str) -> str:
    """Extract author display name from source_file."""
    for key, name in _AUTHORS.items():
        if key in source_file:
            return name
    return source_file


def _parse_grade(source_file: str) -> int | None:
    """Extract grade from source_file like '6-klas-ukrmova-...'."""
    m = re.match(r"(\d+)-klas", source_file)
    return int(m.group(1)) if m else None


def _parse_year(source_file: str) -> str:
    """Extract year from source_file like '...-2023'."""
    m = re.search(r"-(\d{4})(?:-\d)?$", source_file)
    return m.group(1) if m else ""


def get_textbook_links(level: str, slug: str, max_refs: int = 5) -> list[dict]:
    """Get textbook deep links for a module based on its wiki article sources.

    Reads the wiki article to find Source N references, resolves them to
    textbook chunks in SQLite, and builds pidruchnyk.com.ua PDF deep links.

    Returns list of dicts with: author, grade, year, title, url, page
    """
    if not SOURCES_DB.exists():
        return []

    # Find the wiki article for this module
    from wiki.config import TRACK_WRITE_DOMAIN
    domain = TRACK_WRITE_DOMAIN.get(level, "")
    if not domain:
        return []

    wiki_path = WIKI_DIR / domain / f"{slug}.md"
    if not wiki_path.exists():
        return []

    wiki_text = wiki_path.read_text("utf-8")

    # Extract Source N references
    source_nums = set(int(m.group(1)) for m in re.finditer(r"Source\s+(\d+)", wiki_text))
    if not source_nums:
        return []

    # The wiki compiler assigns Source N based on the order chunks appear
    # in the enrichment. We need to find which chunk_ids were used.
    # Strategy: look for chunk_ids referenced in the wiki article's meta comment
    meta_match = re.search(r"<!--\s*wiki-meta\b(.*?)-->", wiki_text, re.DOTALL)
    chunk_ids = []
    if meta_match:
        meta = meta_match.group(1)
        # Extract chunk_ids from sources list in meta
        chunk_ids = re.findall(r"([\w-]+_s\d+)", meta)

    # If no chunk_ids in meta, search SQLite for chunks matching this module's topics
    # Fall back to plan references
    if not chunk_ids:
        return _refs_from_plan(level, slug)

    # Resolve chunk_ids to PDF URLs
    conn = sqlite3.connect(str(SOURCES_DB))
    conn.row_factory = sqlite3.Row
    seen_books: dict[str, dict] = {}  # source_file → best ref

    for cid in chunk_ids:
        row = conn.execute(
            "SELECT source_file, title FROM textbooks WHERE chunk_id = ?", (cid,)
        ).fetchone()
        if not row:
            continue

        sf = row["source_file"]
        page = _parse_page(row["title"])

        # Only Ukrainian language textbooks
        if "ukrmova" not in sf and "ukrajinska-mova" not in sf:
            continue

        # Keep the lowest page per book (most representative)
        existing_page = seen_books.get(sf, {}).get("page")
        if sf not in seen_books or (page is not None and (existing_page is None or page < existing_page)):
            seen_books[sf] = {
                "author": _parse_author(sf),
                "grade": _parse_grade(sf),
                "year": _parse_year(sf),
                "source_file": sf,
                "page": page,
            }

    conn.close()

    # Build final links
    results = []
    for sf, info in sorted(seen_books.items()):
        # Skip textbooks not available anywhere
        if sf in _PDF_NOT_AVAILABLE:
            continue

        grade = info["grade"] or "?"
        year = info["year"]

        # Resolve URL: pidruchnyk override → pidruchnyk original → shkola fallback
        if sf in _SHKOLA_OVERRIDES:
            url = _SHKOLA_OVERRIDES[sf]
            # shkola.in.ua uses Issuu, no page deep-linking
        else:
            pdf_name = _PDF_OVERRIDES.get(sf, sf)
            url = f"{_PDF_BASE}/{pdf_name}.pdf"
            if info["page"]:
                url += f"#page={info['page']}"

        results.append({
            "author": info["author"],
            "grade": grade,
            "year": year,
            "title": f"Українська мова, {grade} клас ({year})",
            "url": url,
            "page": info["page"],
        })

    return results[:max_refs]


def _refs_from_plan(level: str, slug: str) -> list[dict]:
    """Fallback: extract textbook references from plan YAML."""
    import yaml

    plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        return []

    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    refs = plan.get("references", [])
    results = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        title = ref.get("title", "")
        # Only textbook refs (not ULP or web)
        if "url" in ref and "ukrainianlessons" in ref.get("url", ""):
            continue
        if any(author in title for author in ("Заболотний", "Авраменко", "Голуб", "Большакова", "Вашуленко", "Захарійчук")):
            results.append({
                "author": title.split(" Grade")[0] if " Grade" in title else title,
                "grade": "",
                "year": "",
                "title": title,
                "url": "",
                "page": None,
            })

    return results[:5]


def format_textbook_section(links: list[dict]) -> str:
    """Format textbook links as markdown for the Ресурси tab."""
    if not links:
        return ""

    lines = ["## Підручники (Textbooks)", ""]
    for link in links:
        if link["url"]:
            page_info = f", стор. {link['page']}" if link.get("page") else ""
            lines.append(
                f"- [{link['author']} — {link['title']}]({link['url']}){page_info}"
            )
        else:
            lines.append(f"- {link['author']} — {link['title']}")
    lines.append("")
    return "\n".join(lines)
