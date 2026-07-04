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
