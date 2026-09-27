"""Tests for vocab → Word Atlas cross-linking (render-time, integrity-gated).

Covers the normalize/match helper and its integrity-gating in the live
``vocab_items_to_components`` generator path: a link is emitted iff the lemma
has an Atlas page, never otherwise.
"""

from __future__ import annotations

import json

import pytest

from scripts.generate_mdx import resources
from scripts.generate_mdx.atlas_links import (
    atlas_href_for,
    normalize_lemma,
    slug_from_atlas_href,
    validated_atlas_href,
)

# ── normalize_lemma ──────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("робо́та", "робота"),        # combining acute stress stripped
        ("за́мок", "замок"),          # stress stripped
        ("Іван", "іван"),             # case folded
        ("  Київ  ", "київ"),         # whitespace + case
        ("", ""),                      # empty stays empty
    ],
)
def test_normalize_strips_stress_and_case(raw, expected):
    assert normalize_lemma(raw) == expected


def test_normalize_preserves_decomposable_ukrainian_letters():
    # й (U+0439) and ї (U+0457) NFD-decompose to base vowel + combining
    # breve/diaeresis. Those marks must survive — only stress is stripped —
    # else їжак would collapse to іжак and йти to ити.
    assert normalize_lemma("їжак") == "їжак"
    assert normalize_lemma("йти") == "йти"
    assert normalize_lemma("Україна") == "україна"


def test_normalize_canonicalizes_apostrophes():
    # Different apostrophe glyphs must collapse to one key so з'їсти matches.
    variants = ["з'їсти", "з’їсти", "зʼїсти", "з`їсти"]
    keys = {normalize_lemma(v) for v in variants}
    assert len(keys) == 1


# ── atlas_href_for (synthetic manifest) ──────────────────────────────────────

@pytest.fixture
def manifest(tmp_path):
    path = tmp_path / "lexicon-manifest.json"
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "entries": [
                    {"lemma": "робота", "url_slug": "робота", "gloss": "work"},
                    {"lemma": "Іван", "url_slug": "іван", "gloss": "Ivan"},
                    {"lemma": "їжак", "url_slug": "їжак", "gloss": "hedgehog"},
                    {"lemma": "", "url_slug": "broken"},  # ignored (no lemma)
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return str(path)


def test_href_exact_match(manifest):
    assert atlas_href_for("робота", manifest) == "/lexicon/робота/"


def test_href_stress_stripped_match(manifest):
    # Stressed surface form must resolve to the unstressed Atlas page.
    assert atlas_href_for("робо́та", manifest) == "/lexicon/робота/"


def test_href_case_insensitive_match(manifest):
    assert atlas_href_for("іван", manifest) == "/lexicon/іван/"
    assert atlas_href_for("ІВАН", manifest) == "/lexicon/іван/"


def test_href_preserves_yi_letter(manifest):
    assert atlas_href_for("їжак", manifest) == "/lexicon/їжак/"


def test_href_no_match_returns_none(manifest):
    assert atlas_href_for("неіснуючеслово", manifest) is None


def test_href_empty_returns_none(manifest):
    assert atlas_href_for("", manifest) is None
    assert atlas_href_for("   ", manifest) is None


def test_href_missing_manifest_is_graceful(tmp_path):
    missing = str(tmp_path / "does-not-exist.json")
    assert atlas_href_for("робота", missing) is None


def test_href_missing_manifest_warns_stderr(tmp_path, capsys):
    from scripts.generate_mdx import atlas_links
    # Reset global state for test reliability
    atlas_links._warned_manifest_unavailable = False
    atlas_links._load_index.cache_clear()

    missing = str(tmp_path / "does-not-exist.json")
    assert atlas_href_for("робота", missing) is None

    captured = capsys.readouterr()
    assert "WARNING: atlas manifest unavailable" in captured.err

    # Call again to ensure it only warns once per process
    assert atlas_href_for("робота", missing) is None
    captured2 = capsys.readouterr()
    assert "WARNING: atlas manifest unavailable" not in captured2.err


# ── integrity-gating inside the generator ────────────────────────────────────

def _write_json(path, payload) -> str:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(path)


def test_href_unique_alias_rewrites_to_canonical_lemma(tmp_path):
    """An inflected form that is not a published entry links to its one lemma."""
    manifest = _write_json(
        tmp_path / "manifest.json",
        {
            "entries": [
                {"lemma": "студент", "url_slug": "студент"},
                # Present in the manifest, absent from the published page set.
                {"lemma": "студентові", "url_slug": "студентові"},
            ]
        },
    )
    aliases = _write_json(
        tmp_path / "aliases.json",
        [{"a": "студентові", "k": "inflected_form", "s": "студент", "h": "студент"}],
    )
    published = {"студент"}
    assert atlas_href_for(
        "студентові",
        manifest,
        aliases_path=aliases,
        published_slugs=published,
    ) == "/lexicon/студент/"
    assert atlas_href_for(
        "студе́нтові",
        manifest,
        aliases_path=aliases,
        published_slugs=published,
    ) == "/lexicon/студент/"
    assert atlas_href_for(
        "студент",
        manifest,
        aliases_path=aliases,
        published_slugs=published,
    ) == "/lexicon/студент/"


def test_href_alias_preserves_yi(tmp_path):
    manifest = _write_json(
        tmp_path / "manifest.json",
        {"entries": [{"lemma": "їжак", "url_slug": "їжак"}]},
    )
    aliases = _write_json(
        tmp_path / "aliases.json",
        [{"a": "їжака", "s": "їжак"}],
    )
    assert atlas_href_for(
        "їжака",
        manifest,
        aliases_path=aliases,
        published_slugs={"їжак"},
    ) == "/lexicon/їжак/"


def test_href_ambiguous_alias_returns_none(tmp_path):
    manifest = _write_json(
        tmp_path / "manifest.json",
        {
            "entries": [
                {"lemma": "бал", "url_slug": "бал"},
                {"lemma": "баль", "url_slug": "баль"},
            ]
        },
    )
    aliases = _write_json(
        tmp_path / "aliases.json",
        [{"a": "bal", "s": "бал"}, {"a": "bal", "s": "баль"}],
    )
    assert atlas_href_for(
        "bal",
        manifest,
        aliases_path=aliases,
        published_slugs={"бал", "баль"},
    ) is None


def test_href_unpublished_without_alias_returns_none(tmp_path):
    manifest = _write_json(
        tmp_path / "manifest.json",
        {"entries": [{"lemma": "привид", "url_slug": "привид"}]},
    )
    aliases = _write_json(tmp_path / "aliases.json", [])
    assert atlas_href_for(
        "привид",
        manifest,
        aliases_path=aliases,
        published_slugs=set(),
    ) is None


def test_preset_href_is_rewritten_or_dropped(tmp_path):
    manifest = _write_json(
        tmp_path / "manifest.json",
        {"entries": [{"lemma": "студент", "url_slug": "студент"}]},
    )
    aliases = _write_json(
        tmp_path / "aliases.json",
        [{"a": "студентові", "s": "студент"}],
    )
    published = {"студент"}
    assert validated_atlas_href(
        "/lexicon/студентові/",
        manifest,
        aliases_path=aliases,
        published_slugs=published,
    ) == "/lexicon/студент/"
    assert validated_atlas_href(
        "/lexicon/немає-такого/",
        manifest,
        aliases_path=aliases,
        published_slugs=published,
    ) is None
    assert validated_atlas_href(None, manifest) is None
    assert slug_from_atlas_href("/lexicon/%") is None


def test_vocab_component_resolves_preset_href_instead_of_copying_it(monkeypatch):
    def fake_href(word, manifest_path=None, **kwargs):
        del manifest_path, kwargs
        return "/lexicon/студент/" if word == "студентові" else None

    monkeypatch.setattr(resources, "atlas_href_for", fake_href)
    out = resources.vocab_items_to_components(
        [
            {
                "lemma": "студентові",
                "translation": "to the student",
                "atlas_href": "/lexicon/студентові/",
            },
            {
                "lemma": "привид",
                "translation": "ghost",
                "atlas_href": "/lexicon/привид/",
            },
        ]
    )
    assert "/lexicon/студент/" in out
    assert "/lexicon/студентові/" not in out
    assert "/lexicon/привид/" not in out


def test_vocab_component_links_only_lemmas_with_atlas_pages(monkeypatch):
    """The generator emits atlas_href for lemmas that have a page, and omits it
    entirely for lemmas that do not — never a broken link."""
    def fake_href(word):
        return "/lexicon/робота/" if word == "робота" else None

    monkeypatch.setattr(resources, "atlas_href_for", fake_href)

    out = resources.vocab_items_to_components(
        [
            {"lemma": "робота", "translation": "work", "example": "Я люблю роботу."},
            {"lemma": "абракадабра", "translation": "nonsense"},
        ]
    )

    assert "/lexicon/робота/" in out
    assert "atlas_href" in out
    # The un-pageable lemma must not carry an atlas_href key/value.
    assert out.count("/lexicon/") == 1
