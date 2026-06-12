"""Tests for vocab → Word Atlas cross-linking (render-time, integrity-gated).

Covers the normalize/match helper and its integrity-gating in the live
``vocab_items_to_components`` generator path: a link is emitted iff the lemma
has an Atlas page, never otherwise.
"""

from __future__ import annotations

import json

import pytest

from scripts.generate_mdx import resources
from scripts.generate_mdx.atlas_links import atlas_href_for, normalize_lemma

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


# ── integrity-gating inside the generator ────────────────────────────────────

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
