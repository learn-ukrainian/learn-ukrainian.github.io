"""Gate: committed lesson atlas_href values must not be dead or ambiguous.

Classification uses the census oracle (published search index + alias file),
not ``atlas_href_for``.
"""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

import pytest

from scripts.lexicon.lesson_atlas_link_census import (
    ALIAS,
    AMBIGUOUS,
    DEAD,
    DEFAULT_ALIASES,
    DEFAULT_DOCS,
    DEFAULT_SEARCH_INDEX,
    ENTRY,
    PublishedCatalog,
    blocking_atlas_hrefs,
    decode_lexicon_slug,
    load_published_catalog,
    mask_atlas_href_fields,
)

pytestmark = [pytest.mark.reads_content, pytest.mark.repo_wide]


def test_decode_percent_and_nfc():
    assert decode_lexicon_slug(urllib.parse.quote("їжак")) == "їжак"
    assert decode_lexicon_slug("%") is None
    assert decode_lexicon_slug("%ZZ") is None
    nfd_yi = "і\u0308жак"  # NFD ї + жак
    assert decode_lexicon_slug(nfd_yi) == "їжак"


def test_classify_rules_on_a_tiny_catalog():
    catalog = PublishedCatalog(
        entries=frozenset({"студент", "склянка", "бал", "баль"}),
        aliases={
            "студентові": frozenset({"студент"}),
            "склянку": frozenset({"склянка"}),
            "bal": frozenset({"бал", "баль"}),
            "orphan": frozenset({"немає-в-індексі"}),
        },
    )
    assert catalog.classify("студент") == ENTRY
    assert catalog.classify("студентові") == ALIAS
    assert catalog.classify("склянку") == ALIAS
    assert catalog.classify("bal") == AMBIGUOUS
    assert catalog.classify("orphan") == DEAD
    assert catalog.classify("неіснуюче") == DEAD


def test_published_data_classifies_known_inflected_forms():
    catalog = load_published_catalog(DEFAULT_SEARCH_INDEX, DEFAULT_ALIASES)
    assert catalog.classify("студент") == ENTRY
    assert catalog.classify("склянка") == ENTRY
    assert catalog.classify("студентові") == ALIAS
    assert catalog.classify("склянку") == ALIAS
    assert catalog.classify("atlas-8734-not-a-word") == DEAD


def test_mask_atlas_href_ignores_link_edits_only():
    before = '{"word":"студент","atlas_href":"/lexicon/студент/","pos":"noun"}'
    rewritten = '{"word":"студент","atlas_href":"/lexicon/інший/","pos":"noun"}'
    removed = '{"word":"студент","pos":"noun"}'
    prose = '{"word":"інше","atlas_href":"/lexicon/студент/","pos":"noun"}'
    assert mask_atlas_href_fields(before) == mask_atlas_href_fields(rewritten)
    assert mask_atlas_href_fields(before) == mask_atlas_href_fields(removed)
    assert mask_atlas_href_fields(before) != mask_atlas_href_fields(prose)


def test_gate_fails_on_a_planted_dead_link(tmp_path: Path):
    docs = tmp_path / "site" / "src" / "content" / "docs" / "a2"
    docs.mkdir(parents=True)
    (docs / "planted.mdx").write_text(
        '<VocabCard client:only="react" words={JSON.parse(`'
        '[{"word":"привид","translation":"ghost","atlas_href":"/lexicon/atlas-8734-planted-dead/"}]'
        '`)} />\n',
        encoding="utf-8",
    )
    catalog = load_published_catalog(DEFAULT_SEARCH_INDEX, DEFAULT_ALIASES)
    hits = blocking_atlas_hrefs(docs.parent, catalog)
    assert len(hits) == 1
    assert hits[0].classification == DEAD
    assert hits[0].slug == "atlas-8734-planted-dead"
    assert hits[0].word == "привид"


def test_committed_lesson_atlas_hrefs_are_not_dead_or_ambiguous():
    catalog = load_published_catalog(DEFAULT_SEARCH_INDEX, DEFAULT_ALIASES)
    hits = blocking_atlas_hrefs(DEFAULT_DOCS, catalog)
    preview = [
        f"{hit.path} word={hit.word} /lexicon/{hit.slug}/ {hit.classification}"
        for hit in hits[:12]
    ]
    assert hits == [], (
        f"{len(hits)} dead or ambiguous lesson atlas_href values:\n" + "\n".join(preview)
    )


def test_census_help_mentions_when_not_to_use_it():
    from scripts.lexicon.lesson_atlas_link_census import build_parser

    help_text = build_parser().format_help()
    assert "Do NOT use it to generate" in help_text
    assert "Exit codes:" in help_text
    assert "--search-index" in help_text


def test_planted_ambiguous_alias_is_blocking(tmp_path: Path):
    docs = tmp_path / "docs" / "a2"
    docs.mkdir(parents=True)
    (docs / "planted.mdx").write_text(
        json.dumps({"atlas_href": "/lexicon/bal/", "word": "bal"}, ensure_ascii=False),
        encoding="utf-8",
    )
    catalog = load_published_catalog(DEFAULT_SEARCH_INDEX, DEFAULT_ALIASES)
    hits = blocking_atlas_hrefs(docs.parent, catalog)
    assert len(hits) == 1
    assert hits[0].classification == AMBIGUOUS
    assert hits[0].slug == "bal"
