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

pytestmark = pytest.mark.reads_content

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from tests.test_citation_resolution_fixture import _collect_citation_resolution_issues
from wiki.source_attribution import connect_sources_db


def _sources_db_has_required_tables() -> bool:
    """Return True if sources.db is populated enough for this invariant.

    CI doesn't ship sources.db (it's a large generated data file, not
    committed), so these tests can only run in environments with a
    populated DB — e.g. a developer's main checkout after ingestion.
    We check for the ``textbook_sections`` table specifically because
    every resolution path in this test ultimately hits it.
    """
    try:
        with connect_sources_db() as conn:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='textbook_sections' LIMIT 1"
            ).fetchone()
            return row is not None
    except sqlite3.Error:
        return False


if not _sources_db_has_required_tables():
    pytest.skip(
        "sources.db not populated in this environment (CI-normal); "
        "citation resolution invariant requires a full DB. "
        "Run locally after ingestion to exercise this test.",
        allow_module_level=True,
    )


_SOURCES_SECTION_BLOCK_RE = re.compile(r"^## Джерела.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
_PUBLISHED_LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")

KNOWN_DRIFT: dict[str, dict] = {
    # All 7 A1 wiki articles previously listed here were fixed (closing
    # issues #1488-#1494). The invariant now runs strict for the full A1
    # wiki corpus.
    #
    # 51 B2 grammar wiki articles cite textbook files that are external
    # or not yet ingested into sources.db (tracked under issue #8403).
    # 42 other B2 grammar wiki articles resolve completely cleanly (strict invariant).
    'wiki/grammar/b2/academic-writing.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S4 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1256',
        ],
    },
    'wiki/grammar/b2/advanced-case-semantics.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S4 -> textbook 4-klas-ukrmova-zaharijchuk_s0073',
            'unresolved registry entry S6 -> textbook 4-klas-ukrmova-zaharijchuk_s0071',
        ],
    },
    'wiki/grammar/b2/advanced-conjunctions-i.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1292',
        ],
    },
    'wiki/grammar/b2/b2-final-exam.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S11 -> textbook 3-klas-ukrainska-mova-savchuk-2020-2_s0059',
            'unresolved registry entry S14 -> textbook 1-klas-bukvar-bolshakova-2018-2_s0050',
            'unresolved registry entry S4 -> textbook 9-klas-ukrajinska-mova-zabolotnij-2017_s5209',
            'unresolved registry entry S5 -> textbook 9-klas-ukrmova-zabolotnyi-2017_s5270',
            'unresolved registry entry S8 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1240',
        ],
    },
    'wiki/grammar/b2/checkpoint-cases-morphology.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 4-klas-ukrmova-zaharijchuk_s1914',
        ],
    },
    'wiki/grammar/b2/checkpoint-communication.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S13 -> textbook 3-klas-ukrainska-mova-savchuk-2020-2_s0059',
            'unresolved registry entry S16 -> textbook 1-klas-bukvar-bolshakova-2018-2_s0050',
            'unresolved registry entry S18 -> textbook 9-klas-ukrmova-zabolotnyi-2017_s0230',
        ],
    },
    'wiki/grammar/b2/checkpoint-syntax-i.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 9-klas-ukrajinska-mova-voron-2017_s5136',
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1292',
            'unresolved registry entry S4 -> textbook 8-klas-ukrmova-onatiy-2025_s4685',
            'unresolved registry entry S6 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1261',
        ],
    },
    'wiki/grammar/b2/checkpoint-syntax-ii.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 5-klas-ukrmova-litvinova-2022_s2403',
            'unresolved registry entry S12 -> textbook 3-klas-ukrainska-mova-savchuk-2020-2_s0059',
            'unresolved registry entry S14 -> textbook 9-klas-ukrmova-zabolotnyi-2017_s0230',
            'unresolved registry entry S5 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1261',
        ],
    },
    'wiki/grammar/b2/complex-syntax-ellipsis-parcelling.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1284',
            'unresolved registry entry S5 -> textbook 7-klas-ukrlit-mishhenko-2015_s3693',
        ],
    },
    'wiki/grammar/b2/conditional-mood-particles.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 7-klas-ukrmova-litvinova-2024_s3951',
        ],
    },
    'wiki/grammar/b2/correlative-constructions.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 5-klas-ukrmova-litvinova-2022_s2396',
        ],
    },
    'wiki/grammar/b2/dative-advanced.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 9-klas-ukrajinska-mova-zabolotnij-2017_s5215',
        ],
    },
    'wiki/grammar/b2/detached-members.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1268',
            'unresolved registry entry S5 -> textbook 8-klas-ukrmova-onatiy-2025_s4685',
            'unresolved registry entry S6 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1265',
        ],
    },
    'wiki/grammar/b2/direct-indirect-speech.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0342',
            'unresolved registry entry S6 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0345',
        ],
    },
    'wiki/grammar/b2/discussion-debate.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S9 -> textbook 1-klas-bukvar-bolshakova-2018-1_s0003',
        ],
    },
    'wiki/grammar/b2/emphasis-and-inversion.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1262',
            'unresolved registry entry S5 -> textbook 7-klas-ukrlit-mishhenko-2015_s3693',
        ],
    },
    'wiki/grammar/b2/genitive-advanced.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 4-klas-ukrmova-zaharijchuk_s1914',
        ],
    },
    'wiki/grammar/b2/homogeneous-members.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 5-klas-ukrmova-litvinova-2022_s2393',
        ],
    },
    'wiki/grammar/b2/idioms-animals.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 3-klas-ukrainska-mova-vashulenko-2020-1_s0132',
        ],
    },
    'wiki/grammar/b2/kharchuvannia-i-kukhnia.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 7-klas-ukrmova-zabolotnyi-2024_s0248',
            'unresolved registry entry S3 -> textbook 7-klas-istoria-ukr-pometun-2024_s0189',
        ],
    },
    'wiki/grammar/b2/law-justice-vocabulary.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1257',
        ],
    },
    'wiki/grammar/b2/lexical-stylistic-devices.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1249',
        ],
    },
    'wiki/grammar/b2/mistsia-i-oriientyry.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S4 -> textbook 9-klas-ukrajinska-mova-zabolotnij-2017_s5211',
            'unresolved registry entry S5 -> textbook 9-klas-ukrmova-zabolotnyi-2017_s5272',
        ],
    },
    'wiki/grammar/b2/modern-diaspora.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 11-klas-istoriya-ukr-galimov-2024_s0454',
            'unresolved registry entry S4 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0021',
        ],
    },
    'wiki/grammar/b2/multi-clause-sentences.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 9-klas-ukrajinska-mova-zabolotnij-2017_s0232',
            'unresolved registry entry S2 -> textbook 9-klas-ukrajinska-mova-zabolotnij-2017_s0233',
            'unresolved registry entry S6 -> textbook 9-klas-ukrajinska-mova-zabolotnij-2017_s0246',
            'unresolved registry entry S8 -> textbook 9-klas-ukrajinska-mova-zabolotnij-2017_s0232',
        ],
    },
    'wiki/grammar/b2/mystetstvo-i-literatura.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S6 -> textbook 5-klas-ukrlit-zabolotnyi-2022_s0004',
            'unresolved registry entry S9 -> textbook 9-klas-ukrajinska-literatura-mishhenko-2017_s0002',
        ],
    },
    'wiki/grammar/b2/nauka-i-doslidzhennia.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0118',
            'unresolved registry entry S4 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0041',
        ],
    },
    'wiki/grammar/b2/neologisms-borrowings.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S11 -> textbook 7-klas-ukrmova-zabolotnyi-2024_s0260',
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0026',
        ],
    },
    'wiki/grammar/b2/news-analysis.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S4 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0082',
        ],
    },
    'wiki/grammar/b2/numeral-declension-time-dates.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S9 -> textbook 6-klas-ukrlit-kovalenko-2023_s0172',
        ],
    },
    'wiki/grammar/b2/parenthetical-expressions.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0194',
            'unresolved registry entry S5 -> textbook 5-klas-ukrmova-litvinova-2022_s0275',
        ],
    },
    'wiki/grammar/b2/phrases-word-combinations.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0153',
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0174',
            'unresolved registry entry S8 -> textbook 5-klas-ukrmova-litvinova-2022_s0275',
        ],
    },
    'wiki/grammar/b2/politics-government-vocabulary.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0143',
        ],
    },
    'wiki/grammar/b2/predicate-types.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1261',
        ],
    },
    'wiki/grammar/b2/proverbs-nature-time-caution.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 5-klas-ukrlit-zabolotnyi-2022_s0034',
            'unresolved registry entry S6 -> textbook 5-klas-ukrlit-zabolotnyi-2022_s0286',
        ],
    },
    'wiki/grammar/b2/proverbs-work-wisdom-character.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S8 -> textbook 1-klas-bukvar-bolshakova-2018-1_s0003',
        ],
    },
    'wiki/grammar/b2/questions-deliberative-rhetorical.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1267',
        ],
    },
    'wiki/grammar/b2/reflexive-passive.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S4 -> textbook 4-klas-ukrayinska-mova-varzatska-2021-1_s1892',
        ],
    },
    'wiki/grammar/b2/register-business-ukrainian.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S5 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1284',
        ],
    },
    'wiki/grammar/b2/register-formal-informal.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S6 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1284',
        ],
    },
    'wiki/grammar/b2/register-formal-written.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S6 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1255',
        ],
    },
    'wiki/grammar/b2/register-literary-ukrainian.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1270',
            'unresolved registry entry S4 -> textbook 9-klas-ukrajinska-literatura-mishhenko-2017_s4979',
        ],
    },
    'wiki/grammar/b2/register-practice-cross-register-rewriting.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S4 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1284',
        ],
    },
    'wiki/grammar/b2/register-public-discourse.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S10 -> external https://www.president.gov.ua/ua/documents/constitution/konstituciya-ukrayini-rozdil-i',
            'unresolved registry entry S2 -> textbook 7-klas-ukrmova-zabolotnyi-2024_s3962',
        ],
    },
    'wiki/grammar/b2/religion-in-ukraine.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 11-klas-istoriya-ukr-galimov-2024_s0873',
            'unresolved registry entry S6 -> textbook 8-klas-istoria-ukr-galimov-2025_s3997',
        ],
    },
    'wiki/grammar/b2/secondary-sentence-members.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 8-klas-ukrmova-onatiy-2025_s4685',
            'unresolved registry entry S2 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1265',
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1292',
            'unresolved registry entry S9 -> textbook 5-klas-ukrmova-litvinova-2022_s2389',
        ],
    },
    'wiki/grammar/b2/sport-i-dozvillia.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S8 -> textbook ulp-5-00-lesson-notes_l0199',
        ],
    },
    'wiki/grammar/b2/stylistic-connectors.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S1 -> textbook 11-klas-ukrajinska-mova-voron-2019_s1261',
            'unresolved registry entry S9 -> external https://uk.wikipedia.org/wiki/Сполучник',
        ],
    },
    'wiki/grammar/b2/syntactic-stylistic-devices.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 11-klas-ukrajinska-mova-voron-2019_s0056',
        ],
    },
    'wiki/grammar/b2/tradytsii-i-zvychai.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S2 -> textbook 6-klas-ukrlit-kovalenko-2023_s2758',
        ],
    },
    'wiki/grammar/b2/word-formation-place-object-names.md': {
        "issue": "#8403",
        "fragments": [
            'unresolved registry entry S3 -> textbook 3-klas-ukrainska-mova-vashulenko-2020-1_s1765',
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


PUBLISHED_CITATION_TARGETS = _published_targets()


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
    assert not any("orphan inline ref" in issue for issue in issues), (
        f"{rel_path} has orphan inline citations: {issues}"
    )

    if rel_path in KNOWN_DRIFT:
        expected = KNOWN_DRIFT[rel_path]
        for fragment in expected["fragments"]:
            assert any(fragment in issue for issue in issues), (
                f"{rel_path} drift changed; expected fragment {fragment!r}, got {issues!r}"
            )
        for issue in issues:
            assert any(fragment in issue for fragment in expected["fragments"]), (
                f"{rel_path} has unexpected citation issue: {issue!r}"
            )
        pytest.xfail(expected["issue"])

    assert not issues, f"{rel_path} has unresolved citations: {issues}"
