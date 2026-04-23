"""CI invariant for published citation resolution.

EPIC #1451 Phase 4-A, issue #1460.

Every published ``[S#]`` citation in committed curriculum/wiki markdown must:
1. resolve to a sibling ``*.sources.yaml`` registry entry; and
2. resolve from that registry entry to a concrete record in ``sources.db``.

The published surface in this repo currently consists of:
- locked wiki articles under ``wiki/``
- top-level published module markdown under ``curriculum/l2-uk-en/{a1..c2}/``
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from pathlib import Path

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from wiki.source_attribution import connect_sources_db, resolve_chunk_attribution_any_corpus_with_conn
from wiki.sources_schema import extract_short_citation_ids, load_sources_registry

_SOURCES_SECTION_BLOCK_RE = re.compile(r"^## Джерела.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
_TEXTBOOK_SECTION_RE = re.compile(r"_s(\d+)$")
_CHUNK_ROW_RE = re.compile(r"_c(\d+)$")
_BARE_SECTION_RE = re.compile(r"^S(\d+)$")
_PUBLISHED_LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")

KNOWN_DRIFT = {
    "wiki/pedagogy/a1/food-and-drink.md": {
        "issue": "#1488",
        "fragments": ["unresolved registry entry S12 -> external ext-article-1"],
    },
    "wiki/pedagogy/a1/hey-friend.md": {
        "issue": "#1489",
        "fragments": [
            "orphan inline ref S2447",
            "orphan inline ref S3165",
            "orphan inline ref S3336",
            "orphan inline ref S4715",
        ],
    },
    "wiki/pedagogy/a1/my-family.md": {
        "issue": "#1490",
        "fragments": [
            "orphan inline ref S2435",
            "orphan inline ref S2452",
            "orphan inline ref S3129",
        ],
    },
    "wiki/pedagogy/a1/reading-ukrainian.md": {
        "issue": "#1491",
        "fragments": ["unresolved registry entry S12 -> external ext-article-1"],
    },
    "wiki/pedagogy/a1/stress-and-melody.md": {
        "issue": "#1492",
        "fragments": [
            "orphan inline ref S606",
            "orphan inline ref S1503",
            "orphan inline ref S1548",
            "orphan inline ref S2298",
        ],
    },
    "wiki/pedagogy/a1/things-have-gender.md": {
        "issue": "#1493",
        "fragments": [
            "malformed registry:",
            "Unsupported wiki source type: textbook-chunk",
        ],
    },
    "wiki/pedagogy/a1/who-am-i.md": {
        "issue": "#1494",
        "fragments": [
            "unresolved registry entry S8 -> morphological-dictionary VESUM",
            "unresolved registry entry S9 -> explanatory-dictionary СУМ-11",
        ],
    },
}


def _strip_sources_section(text: str) -> str:
    return _SOURCES_SECTION_BLOCK_RE.sub("", text)


def _iter_published_wiki_articles() -> list[Path]:
    published: list[Path] = []
    for path in sorted(Path("wiki").rglob("*.md")):
        if "/.reviews/" in path.as_posix():
            continue
        text = path.read_text(encoding="utf-8")
        if "lifecycle: locked" not in text:
            continue
        published.append(path)
    return published


def _iter_published_module_markdown() -> list[Path]:
    published: list[Path] = []
    for level in _PUBLISHED_LEVELS:
        root = Path("curriculum/l2-uk-en") / level
        if not root.exists():
            continue
        published.extend(
            path
            for path in sorted(root.glob("*.md"))
            if not path.name.startswith(("README", "INDEX"))
        )
    return published


def _published_targets() -> list[Path]:
    return _iter_published_wiki_articles() + _iter_published_module_markdown()


def _citation_ids_for_markdown(path: Path) -> set[str]:
    text = _strip_sources_section(path.read_text(encoding="utf-8"))
    return set(extract_short_citation_ids(text))


def _registry_entry_resolves_to_sources_db(entry, conn: sqlite3.Connection) -> bool:
    file_value = str(entry.file or "").strip()
    entry_type = str(entry.type or "").strip()
    if not file_value:
        return False

    match = _BARE_SECTION_RE.fullmatch(file_value)
    if entry_type == "textbook-chunk" and match:
        return (
            conn.execute(
                "SELECT 1 FROM textbook_sections WHERE section_id = ? LIMIT 1",
                (int(match.group(1)),),
            ).fetchone()
            is not None
        )

    if entry_type == "textbook":
        match = _TEXTBOOK_SECTION_RE.search(file_value)
        if match:
            return (
                conn.execute(
                    "SELECT 1 FROM textbook_sections WHERE section_id = ? LIMIT 1",
                    (int(match.group(1)),),
                ).fetchone()
                is not None
            )
        match = _CHUNK_ROW_RE.search(file_value)
        if match:
            return (
                conn.execute(
                    "SELECT 1 FROM textbooks WHERE id = ? LIMIT 1",
                    (int(match.group(1)),),
                ).fetchone()
                is not None
            )
        if _BARE_SECTION_RE.fullmatch(file_value):
            return (
                conn.execute(
                    "SELECT 1 FROM textbook_sections WHERE section_id = ? LIMIT 1",
                    (int(file_value[1:]),),
                ).fetchone()
                is not None
            )

    if entry_type == "literary":
        match = _CHUNK_ROW_RE.search(file_value)
        if match:
            return (
                conn.execute(
                    "SELECT 1 FROM literary_texts WHERE id = ? LIMIT 1",
                    (int(match.group(1)),),
                ).fetchone()
                is not None
            )
        return (
            conn.execute(
                "SELECT 1 FROM literary_texts WHERE chunk_id = ? LIMIT 1",
                (file_value,),
            ).fetchone()
            is not None
        )

    if entry_type == "external":
        return (
            conn.execute(
                "SELECT 1 FROM external_articles WHERE chunk_id = ? OR url = ? LIMIT 1",
                (file_value, file_value),
            ).fetchone()
            is not None
        )

    if entry_type == "wikipedia":
        title = file_value.split("/", 1)[1] if file_value.startswith("wikipedia/") else file_value
        return (
            conn.execute(
                "SELECT 1 FROM wikipedia WHERE title = ? LIMIT 1",
                (title,),
            ).fetchone()
            is not None
        )

    if entry_type == "ukrainian_wiki":
        if file_value.startswith("ukrainian_wiki/"):
            slug = file_value.split("/", 1)[1].split("_", 1)[0]
            return (
                conn.execute(
                    "SELECT 1 FROM ukrainian_wiki WHERE article_slug = ? LIMIT 1",
                    (slug,),
                ).fetchone()
                is not None
            )
        return (
            conn.execute(
                "SELECT 1 FROM ukrainian_wiki WHERE passage_id = ? LIMIT 1",
                (file_value,),
            ).fetchone()
            is not None
        )

    # Dictionary authorities are currently not addressable to a concrete
    # sources.db row from the committed registry shape.
    if entry_type in {"explanatory-dictionary", "morphological-dictionary"}:
        return False

    resolved = resolve_chunk_attribution_any_corpus_with_conn(conn, file_value)
    return resolved is not None


def _collect_citation_resolution_issues(path: Path, conn: sqlite3.Connection) -> list[str]:
    citation_ids = _citation_ids_for_markdown(path)
    if not citation_ids:
        return []

    registry_path = path.with_suffix(".sources.yaml")
    if not registry_path.exists():
        return [f"missing registry: {registry_path.name}"]

    try:
        registry = load_sources_registry(registry_path)
    except Exception as exc:  # pragma: no cover - exercised by locked drift fixture.
        return [f"malformed registry: {exc}"]

    registry_by_id = registry.by_id()
    issues: list[str] = []
    for citation_id in sorted(citation_ids, key=lambda value: int(value[1:])):
        entry = registry_by_id.get(citation_id)
        if entry is None:
            issues.append(f"orphan inline ref {citation_id}")
            continue
        if not _registry_entry_resolves_to_sources_db(entry, conn):
            issues.append(
                f"unresolved registry entry {citation_id} -> {entry.type} {entry.file}"
            )
    return issues


PUBLISHED_CITATION_TARGETS = _published_targets()


def test_seeded_fake_inline_citation_is_rejected(tmp_path: Path) -> None:
    article_path = tmp_path / "wiki" / "pedagogy" / "a1" / "fake.md"
    article_path.parent.mkdir(parents=True)
    article_path.write_text(
        "# Fake\n\n"
        "<!-- wiki-meta\n"
        "slug: fake\n"
        "domain: pedagogy/a1\n"
        "tracks: [a1]\n"
        "lifecycle: locked\n"
        "-->\n\n"
        "Текст із фальшивим посиланням [S999].\n",
        encoding="utf-8",
    )
    article_path.with_suffix(".sources.yaml").write_text(
        "sources:\n"
        "  - id: S1\n"
        "    file: 11-klas-ukrmova-avramenko-2019_s0077\n"
        "    type: textbook\n",
        encoding="utf-8",
    )

    with sqlite3.connect(":memory:") as conn:
        issues = _collect_citation_resolution_issues(article_path, conn)

    assert issues == ["orphan inline ref S999"]


@pytest.mark.parametrize(
    "path",
    PUBLISHED_CITATION_TARGETS,
    ids=lambda path: path.as_posix(),
)
def test_published_citations_resolve_invariant(path: Path) -> None:
    with connect_sources_db() as conn:
        issues = _collect_citation_resolution_issues(path, conn)

    if not issues:
        return

    rel_path = path.as_posix()
    if rel_path in KNOWN_DRIFT:
        expected = KNOWN_DRIFT[rel_path]
        for fragment in expected["fragments"]:
            assert any(fragment in issue for issue in issues), (
                f"{rel_path} drift changed; expected fragment {fragment!r}, got {issues!r}"
            )
        pytest.xfail(expected["issue"])

    assert not issues, f"{rel_path} has unresolved citations: {issues}"
