from __future__ import annotations

import pytest

from scripts.audit import strip_internal_resource_entries as strip

pytestmark = pytest.mark.reads_content


def test_removes_internal_roles_keeps_real_resources() -> None:
    text = (
        '- title: "Wiki: pedagogy/a1/x"\n  role: internal wiki\n  source_ref: "Wiki: pedagogy/a1/x"\n  notes: brief\n'
        '- title: "Ukrainian Wikipedia: Greetings"\n  role: wiki\n  url: "https://uk.wikipedia.org/x"\n  notes: real\n'
        '- title: "Real article"\n  role: article\n  url: "https://example.com"\n  notes: keep\n'
    )
    new, removed = strip.strip_yaml(text)
    assert removed == ["Wiki: pedagogy/a1/x"]
    assert "internal wiki" not in new
    assert "Ukrainian Wikipedia: Greetings" in new  # legit role: wiki kept
    assert "Real article" in new


def test_url_bearing_catalog_provenance_is_kept() -> None:
    """A2 regression: a genuine external resource whose source_ref records its
    ``docs/resources/`` catalog provenance but carries a real off-site URL must NOT be
    stripped. Without the url-guard this removed 265/265 legitimate A2 resources."""
    assert not strip.is_internal_entry(
        role="article",
        title="ULP: Ukrainian Cases Chart",
        source_ref="docs/resources/ulp-articles-index.yaml: /ukrainian-cases-chart/",
        url="https://www.ukrainianlessons.com/ukrainian-cases-chart/",
    )


def test_strips_wrapped_resources_list_with_internal_urls() -> None:
    text = (
        "resources:\n"
        '  - title: "B1 grammar wiki: spatial prepositions"\n'
        '    url: "wiki/grammar/b1/prepositions-spatial-review.md"\n'
        "    type: internal\n"
        '  - title: "Real article"\n'
        "    role: article\n"
        '    url: "https://example.com/real"\n'
    )
    new, removed = strip.strip_yaml(text)
    assert removed == ["B1 grammar wiki: spatial prepositions"]
    assert "wiki/grammar/b1/prepositions-spatial-review.md" not in new
    assert "Real article" in new
    assert new.startswith("resources:\n")


def test_reference_and_resource_catalog_source_refs_are_kept() -> None:
    """B1 regression: docs/references/ (textbook corpus) and docs/resources/ (external
    catalog) are legit provenance dirs — a url-less textbook citation whose source_ref
    points there must NOT be stripped. Without the carve-out, 26 real B1 textbook
    citations were deleted."""
    # docs/references/ textbook citations are url-less by nature → always kept.
    assert not strip.is_internal_entry(
        role="textbook",
        title="9 клас: підрядні обставинні речення",
        source_ref="docs/references/textbooks-txt/9-klas-ukrajinska-mova-voron-2017.txt",
    )
    # docs/resources/ catalog entries are kept ONLY via the url-guard (real ones carry a URL)…
    assert not strip.is_internal_entry(
        role="article", title="ULP", source_ref="docs/resources/ulp-articles-index.yaml: /x/",
        url="https://ulp.com/x/",
    )
    # …a url-LESS docs/resources/ entry is still junk.
    assert strip.is_internal_entry(
        role="article", title="ULP", source_ref="docs/resources/ulp-articles-index.yaml: /x/"
    )
    # Other docs/ paths (internal authoring briefs) are still junk.
    assert strip.is_internal_entry(role="reference", title="Brief", source_ref="docs/pedagogy/brief.md")
    assert strip.is_internal_entry(role="curriculum", title="M77", source_ref="curriculum/l2-uk-en/b1/x/module.md")


def test_empty_module_becomes_bracket_list() -> None:
    new, removed = strip.strip_yaml('- title: t\n  role: internal synthesis\n  source_ref: "Synthesis of M1"\n  notes: x\n')
    assert new.strip() == "[]"
    assert removed == ["t"]
