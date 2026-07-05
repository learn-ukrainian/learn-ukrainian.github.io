from __future__ import annotations

from scripts.audit import strip_internal_resource_entries as strip


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


def test_detects_internal_hiding_under_valid_role() -> None:
    # role: wiki but title/source_ref point at an internal pedagogy brief.
    entry_locked = {"role": "wiki", "title": "Wiki: pedagogy/a1/who-am-i (LOCKED 2026-04-23)", "source_ref": "Wiki: pedagogy/a1/who-am-i"}
    # role: checkpoint source with a Synthesis title.
    entry_synth = {"role": "checkpoint source", "title": "Synthesis of M42-M46 content", "source_ref": "Synthesis of M42-M46 content"}
    # curriculum/ source path prerequisite.
    entry_prereq = {"role": "prerequisite pattern", "title": "Internal module M43", "source_ref": "curriculum/l2-uk-en/a1/x/module.md"}
    for e in (entry_locked, entry_synth, entry_prereq):
        assert strip.is_internal_entry(role=e["role"], title=e["title"], source_ref=e["source_ref"])


def test_keeps_genuine_external_and_standard_reference() -> None:
    assert not strip.is_internal_entry(role="official source", title="DSNS contacts", source_ref="https://bezpeka.dsns.gov.ua")
    assert not strip.is_internal_entry(role="standard reference", title="State Standard 2024, §4.2.4.1", source_ref="State Standard 2024, §4.2.4.1")
    assert not strip.is_internal_entry(role="wiki", title="Ukrainian Wikipedia: Greetings", source_ref="https://uk.wikipedia.org/x")


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


def test_role_and_title_junk_still_stripped_despite_url() -> None:
    # The strong role/title signals stay strict even when a URL is present.
    assert strip.is_internal_entry(role="internal wiki", title="X", source_ref="", url="https://x.com")
    assert strip.is_internal_entry(role="wiki", title="Wiki: pedagogy/a1/foo", source_ref="", url="https://x.com")
    assert strip.is_internal_entry(role="prerequisite pattern", title="Prior module", source_ref="", url="https://x.com")


def test_source_ref_junk_without_url_still_stripped() -> None:
    # A repo-pointing source_ref with NO external URL is still build-provenance junk.
    assert strip.is_internal_entry(role="reference", title="Brief", source_ref="docs/pedagogy/brief.md", url="")


def test_reference_and_resource_catalog_source_refs_are_kept() -> None:
    """B1 regression: docs/references/ (textbook corpus) and docs/resources/ (external
    catalog) are legit provenance dirs — a url-less textbook citation whose source_ref
    points there must NOT be stripped. Without the carve-out, 26 real B1 textbook
    citations were deleted."""
    assert not strip.is_internal_entry(
        role="textbook",
        title="9 клас: підрядні обставинні речення",
        source_ref="docs/references/textbooks-txt/9-klas-ukrajinska-mova-voron-2017.txt",
    )
    assert not strip.is_internal_entry(
        role="article", title="ULP", source_ref="docs/resources/ulp-articles-index.yaml: /x/"
    )
    # Other docs/ paths (internal authoring briefs) are still junk.
    assert strip.is_internal_entry(role="reference", title="Brief", source_ref="docs/pedagogy/brief.md")
    assert strip.is_internal_entry(role="curriculum", title="M77", source_ref="curriculum/l2-uk-en/b1/x/module.md")


def test_empty_module_becomes_bracket_list() -> None:
    new, removed = strip.strip_yaml('- title: t\n  role: internal synthesis\n  source_ref: "Synthesis of M1"\n  notes: x\n')
    assert new.strip() == "[]"
    assert removed == ["t"]


def test_mdx_empty_state_note() -> None:
    mdx = (
        "<TabItem label=\"Resources\">\n\n"
        ":::info[🎧 🔗 External Resources]\n\n"
        "**🔗 Online resources:**\n"
        "- 🔗 **Synthesis of M1** — internal note.\n"
        ":::\n\n</TabItem>\n"
    )
    out = strip.strip_mdx(mdx, ["Synthesis of M1"])
    assert "Synthesis of M1" not in out
    assert strip._EMPTY_NOTE in out
