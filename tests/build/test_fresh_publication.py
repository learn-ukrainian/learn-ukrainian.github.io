"""Rendered quote rights, verbatim excerpt, and visible attribution regressions."""

import html
import json
import subprocess

import pytest
import yaml

from scripts.build.fresh.assemble import (
    AssemblerError,
    _render_urok_markdown,
    assemble_expanded_document,
    build_resursy_entries,
    build_resursy_tab,
)
from scripts.curriculum.evidence import publication
from scripts.curriculum.resolver.classify import classify_unit
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument

BOOK = "1-klas-bukvar-zaharijchuk-2025-1"


@pytest.fixture
def publication_course(tmp_path, monkeypatch):
    """Real tracked synthetic publication inputs; no held-out oracle access."""
    from tests.curriculum.evidence.test_publication import owned_entries

    for path, content in {
        "docs/l2-uk-direct/textbook-selection.yaml": yaml.safe_dump({"sources": owned_entries()}),
        "site/src/data/lexicon-sentence-inventory.json": json.dumps({"rows": []}),
    }.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    monkeypatch.setattr(publication, "REGISTRY_PATH", tmp_path / "docs/l2-uk-direct/textbook-selection.yaml")
    monkeypatch.setattr(publication, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.mark.parametrize("surface", ["quote", "activity", "example", "grounding"])
@pytest.mark.parametrize("file", ["unregistered", "owned-oho-a1-transcripts-v2", BOOK])
def test_tracked_publication_checks_rights_before_named_accounting(publication_course, surface, file):
    from tests.curriculum.evidence.test_publication import owned_occurrence

    rec = owned_occurrence(file="owned-oho-a1-transcripts")["record"]
    rec["source"].update(file=file, page=1)
    step = {"id": "s1"}
    lesson = {"n": 1, "steps": [step]}
    pack = {"texts": [rec]}
    if surface == "quote":
        step.update(needs=["quote"], ref=rec["id"])
    elif surface == "activity":
        step["practice"] = ["a1"]
        lesson["activities"] = [{"id": "a1", "focus": "host: {kind: quote, ref: T-001}"}]
    elif surface == "example":
        rec = {**rec, "id": "EX-001", "text": rec["quote"]}
        del rec["quote"]
        pack = {"examples": [rec]}
        step.update(needs=["example"], ref=rec["id"])
    else:
        step["explains"] = [rec["id"]]
    plan = {"lessons": [lesson]}
    for category, document in (("lesson-plans", plan), ("evidence", pack)):
        path = publication_course / f"curriculum/l2-uk-en/{category}/a1/synthetic.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(document))
    subprocess.run(["git", "add", "."], cwd=publication_course, check=True, timeout=30)
    report = publication.course_report(publication_course)
    if surface == "grounding":
        assert report["status"] == "ok" and report["errors"] == []
        assert publication.enforce_publication(plan, pack) == []
    else:
        code = "quote_mismatch" if file == BOOK else "publication_right"
        assert report["status"] == "blocked"
        assert any(error.startswith(code + ":") for error in report["errors"])
        with pytest.raises(ValueError, match="^" + code + ":"):
            publication.quote_attribution(publication.excerpt_record(rec))


@pytest.mark.parametrize(
    "allowed,size,code",
    [(True, 800, None), (True, 801, "publication_limit"), (False, 20, "publication_right")],
)
def test_course_report_preserves_registry_permitted_textbook_quotes(publication_course, allowed, size, code):
    registry_path = publication.REGISTRY_PATH
    registry = yaml.safe_load(registry_path.read_text())
    registry["sources"][BOOK]["publish"]["allowed"] = allowed
    registry_path.write_text(yaml.safe_dump(registry))
    rec = {
        "id": "T-001", "quote": "x" * size,
        "source": {"kind": "textbook", "file": BOOK, "page": 1, "chunk_id": BOOK + "_s0001"},
    }
    lesson = {"n": 1, "steps": [{"id": "s1", "needs": ["quote"], "ref": "T-001"}]}
    for category, document in (("lesson-plans", {"lessons": [lesson]}), ("evidence", {"texts": [rec]})):
        path = publication_course / f"curriculum/l2-uk-en/{category}/a1/synthetic.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(document))
    subprocess.run(["git", "add", "."], cwd=publication_course, check=True, timeout=30)
    report = publication.course_report(publication_course)
    assert all(total["lesson"] == 0 for total in report["sources"].values())
    if code:
        assert report["status"] == "blocked"
        assert any(error.startswith(code + ":") for error in report["errors"])
    else:
        assert report["status"] == "ok" and report["errors"] == []
        assert publication.enforce_publication({"lessons": [lesson]}, {"texts": [rec]}) == []
        assert render_quote(file=BOOK, quote=rec["quote"], page=1)[0]


def render_quote(file=BOOK, quote="Synthetic exact excerpt", page=39):
    draft = {"steps": [{"id": "s1", "blocks": [{"kind": "quote", "ref": "T-001"}]}]}
    record = {"id": "T-001", "quote": quote, "source": {"kind": "textbook", "file": file, "page": page}}
    stressed = {"units": [{"tab": "urok", "step": "s1", "block": 0, "role": "record_print", "text": quote}]}
    return _render_urok_markdown(draft, stressed, {"texts": [record]}, {"words": []})


def test_rendered_quote_is_verbatim_and_attributed():
    quote = "Synthetic exact excerpt —  preserve  spacing!"
    markdown, units = render_quote(quote=quote)
    assert f"> {quote}\n>\n> — *Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 39*" in markdown
    assert units.texts()[0] == quote


@pytest.mark.parametrize(
    "file,quote,page,code",
    [
        ("ulp-1-00-lesson-notes", "Synthetic excerpt", 39, "publication_scope_incomplete"),
        ("not-registered", "Synthetic excerpt", 39, "publication_right"),
        ("9-klas-tekhnolohiyi-bilenko-2026", "Synthetic excerpt", 39, "publication_right"),
        ("anna-ohoiko-500-verbs", "Synthetic excerpt", 39, "owned_quote_refused"),
        (BOOK, "x" * 801, 39, "publication_limit"),
        (BOOK, "Synthetic excerpt", None, "publication_attribution"),
    ],
)
def test_renderer_cannot_bypass_quote_admission(file, quote, page, code):
    with pytest.raises(AssemblerError) as caught:
        render_quote(file, quote, page)
    assert caught.value.code == code


@pytest.mark.parametrize(
    "file,citation",
    [
        (BOOK, "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 12"),
        ("1-klas-bukvar-zaharijchuk-2025-2", "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 2, 2025, с. 12"),
        ("10-11-klas-mystectvo-nazarenko-2018", "Назаренко, «Мистецтво», 10–11 клас, 2018, с. 12"),
        ("5-klas-ukrmova-zabolotnyi-2023", "Заболотний, «Українська мова», 5 клас, 2022, с. 12"),
        ("7-klas-tekhnolohiyi-bilenko-2024", "Біленко, «Технології», 7 клас, 2023, с. 12"),
        (
            "9-klas-zarubizhna-literatura-kovbasenko-2026",
            "Ковбасенко, «Зарубіжна література», 9 клас, 2025, с. 12",
        ),
    ],
)
def test_quote_and_resources_show_same_human_citation(file, citation):
    markdown, _units = render_quote(file=file, page=12)
    assert citation in markdown
    pack = {
        "texts": [
            {
                "id": "T-001",
                "quote": "Synthetic excerpt",
                "source": {
                    "kind": "textbook",
                    "file": file,
                    "page": 12,
                    "work": "Spoofed English title",
                    "author": "Spoof",
                },
            }
        ]
    }
    tab = build_resursy_tab({"steps": [{"evidence": ["T-001"]}]}, pack)
    entry = tab["books"][0]
    assert entry["title"] == citation
    assert entry["pages"] == entry["author"] == ""
    assert file not in str(tab)


@pytest.mark.parametrize("file", ["9-klas-tekhnolohiyi-bilenko-2026", "uni-unregistered"])
def test_resources_omit_unconfirmed_title_with_warning(file):
    pack = {"texts": [{"id": "T-001", "source": {"kind": "textbook", "file": file, "page": 12}}]}
    warnings = []
    lesson = {"steps": [{"explains": ["T-001"]}]}
    assert build_resursy_entries(lesson, pack, warnings=warnings) == []
    assert build_resursy_tab(lesson, pack) == {}
    assert warnings == [{"code": "resource_citation_omitted", "record": "T-001", "reason": "citable_metadata_missing"}]


def test_bibliography_is_metadata_while_quote_prose_stays_checked():
    draft = {"status": "ok", "steps": [{"id": "s1", "blocks": [{"kind": "quote", "ref": "T-001"}]}]}
    pack = {"texts": [{"id": "T-001", "quote": "Цитата", "source": {"kind": "textbook", "file": BOOK, "page": 12}}]}
    plan = {
        "arc_ref": {"level": "a1", "position": 1},
        "lessons": [{"n": 1, "steps": [{"id": "s1", "evidence": ["T-001"]}]}],
    }
    expanded, provenance = assemble_expanded_document(draft, plan, pack, {"words": []}, "a1", "fixture", 1)
    document = ExpandedDocument.from_data(expanded)
    allowlist = Allowlist.from_records([])
    citation = next(unit for unit in document.units if unit.tab == "resursy")
    assert citation.text == "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 12"
    assert all(token.final == "skipped:vesum_exempt" for token in classify_unit(citation, allowlist))
    quote = next(unit for unit in document.units if unit.tab == "urok")
    assert all(token.needs_lookup for token in classify_unit(quote, allowlist))
    resource_span = next(span for span in provenance["spans"] if span["tab"] == "resursy")
    assert resource_span["ref"] == "T-001" and resource_span["source"] == "record"


def test_ulp_resource_renders_homepage_and_episode_without_private_text():
    from scripts.generate_mdx.resources import format_resources_for_mdx

    record = {
        "id": "T-001",
        "source": {"kind": "textbook", "file": "ulp-1-00-lesson-notes", "page": 12},
        "episode_url": "https://www.ukrainianlessons.com/episode1/",
        "quote": "PRIVATE QUOTE",
        "supports": "PRIVATE SUPPORTS",
    }
    resources = build_resursy_tab({"steps": [{"explains": ["T-001"]}]}, {"texts": [record]})
    rendered = format_resources_for_mdx(resources, True)
    assert "[Ukrainian Lessons Podcast — Анна Огойко](https://www.ukrainianlessons.com/)" in rendered
    assert "[https://www.ukrainianlessons.com/episode1/](https://www.ukrainianlessons.com/episode1/)" in rendered
    assert "<https://www.ukrainianlessons.com/episode1/>" not in rendered
    assert "PRIVATE" not in rendered


def test_missing_resource_record_and_registry_still_fail(tmp_path, monkeypatch):
    from scripts.curriculum.evidence import publication

    with pytest.raises(AssemblerError, match="text_not_found"):
        build_resursy_tab({"steps": [{"explains": ["T-001"]}]}, {"texts": []})
    monkeypatch.setattr(publication, "REGISTRY_PATH", tmp_path / "absent")
    with pytest.raises(AssemblerError, match="publication_registry_unreadable"):
        build_resursy_tab(
            {"steps": [{"explains": ["T-001"]}]},
            {"texts": [{"id": "T-001", "source": {"kind": "textbook", "file": BOOK, "page": 12}}]},
        )


@pytest.mark.parametrize("slug,policy", list(publication.load_owned_rights().items()))
def test_rendered_owned_quote_and_resources_for_every_protected_slug(slug, policy):
    from scripts.generate_mdx.resources import format_resources_for_mdx

    with pytest.raises(AssemblerError) as caught:
        render_quote(file=slug)
    assert caught.value.code == (
        "publication_scope_incomplete" if slug in publication.NAMED_EXCERPTS else "owned_quote_refused"
    )
    lesson = {"steps": [{"explains": ["T-001"]}]}
    pack = {
        "texts": [
            {
                "id": "T-001",
                "quote": "PRIVATE_SENTINEL",
                "supports": "PRIVATE_SENTINEL",
                "source": {"kind": "textbook", "file": slug, "page": 1, "work": "PRIVATE_SENTINEL"},
            }
        ]
    }
    if policy["rights"] == "private_permission":
        with pytest.raises(AssemblerError) as caught:
            build_resursy_tab(lesson, pack)
        assert caught.value.code == "private_citation_refused"
    else:
        resources = build_resursy_tab(lesson, pack)
        rendered = format_resources_for_mdx(resources, True)
        assert resources["books"][0]["title"] in html.unescape(rendered)
        assert "PRIVATE_SENTINEL" not in rendered


@pytest.mark.parametrize("operation", ["quote", "resource"])
def test_rendering_fails_when_owned_rights_are_unreadable(tmp_path, monkeypatch, operation):
    monkeypatch.setattr(publication, "OWNED_RIGHTS_PATH", tmp_path / "absent")
    with pytest.raises(AssemblerError) as caught:
        if operation == "quote":
            render_quote()
        else:
            build_resursy_tab(
                {"steps": [{"evidence": ["T-001"]}]},
                {"texts": [{"id": "T-001", "source": {"file": BOOK, "kind": "textbook"}}]},
            )
    assert caught.value.code == "owned_rights_unreadable"


def test_owned_excerpt_resources_distinguish_each_printed_quote_and_example(monkeypatch):
    rec = {"id": "T-001", "quote": "Synthetic text", "source": {"kind": "textbook", "file": "ulp-1-00-lesson-notes"}}
    ex = {"id": "EX-001", "text": "Synthetic example", "source": rec["source"]}
    lesson = {
        "steps": [
            {"id": "s1", "needs": ["quote"], "ref": "T-001"},
            {"id": "s2", "needs": ["example"], "ref": "EX-001"},
            {"id": "s3", "needs": ["quote"], "ref": "T-001"},
        ]
    }
    pack = {"texts": [rec], "examples": [ex]}
    entries = build_resursy_entries(lesson, pack)
    assert len(entries) == 3
    assert [row[2]["description"] for row in entries] == ["Excerpt 1", "Excerpt 2", "Excerpt 3"]
    assert all(row[2]["url"] == "https://www.ukrainianlessons.com/" for row in entries)
    assert all("Anna Ohoiko" in row[2]["title"] for row in entries)
    assert "Synthetic" not in str(entries) and "ulp-1-" not in str([row[2] for row in entries])
    registry = publication.load_registry()
    registry["ulp-1-00-lesson-notes"]["author"] = None
    monkeypatch.setattr(publication, "load_registry", lambda *args: registry)
    with pytest.raises(AssemblerError, match="publication_scope_incomplete"):
        build_resursy_entries(lesson, pack)


def test_owned_excerpt_assembly_blocks_unreserved_example():
    draft = {"status": "ok", "steps": [{"id": "s1", "blocks": [{"kind": "example", "ref": "EX-001"}]}]}
    plan = {"arc_ref": {"position": 1}, "lessons": [{"n": 1, "steps": [{"id": "s1"}]}]}
    pack = {
        "examples": [
            {
                "id": "EX-001",
                "text": "Synthetic example",
                "source": {"kind": "textbook", "file": "ulp-1-00-lesson-notes"},
            }
        ]
    }
    with pytest.raises(
        AssemblerError, match="publication_scope_incomplete: actual excerpt exceeds planned reservation"
    ):
        assemble_expanded_document(draft, plan, pack, {"words": []}, "a1", "synthetic", 1)


def test_owned_excerpt_assembly_render_and_resources_on_complete_synthetic_course(tmp_path, monkeypatch):
    import json
    import subprocess

    import yaml

    from tests.curriculum.evidence.test_publication import owned_entries, owned_occurrence

    registry = tmp_path / "docs/l2-uk-direct/textbook-selection.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text(yaml.safe_dump({"sources": owned_entries()}))
    inventory = tmp_path / "site/src/data/lexicon-sentence-inventory.json"
    inventory.parent.mkdir(parents=True)
    inventory.write_text(json.dumps({"rows": []}))
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    subprocess.run(["git", "add", "docs", "site"], cwd=tmp_path, check=True, timeout=30)
    monkeypatch.setattr(publication, "REGISTRY_PATH", registry)
    monkeypatch.setattr(publication, "REPO_ROOT", tmp_path)
    quote = owned_occurrence(60)["record"]
    example = {**quote, "id": "EX-001", "text": quote["quote"]}
    del example["quote"]
    pack = {"texts": [quote], "examples": [example]}
    lesson = {"n": 1, "steps": [{"id": "s1", "needs": ["quote", "example"], "evidence": ["T-001", "EX-001"]}]}
    plan = {"arc_ref": {"position": 1}, "lessons": [lesson]}
    draft = {
        "status": "ok",
        "steps": [{"id": "s1", "blocks": [{"kind": "quote", "ref": "T-001"}, {"kind": "example", "ref": "EX-001"}]}],
    }
    expanded, provenance = assemble_expanded_document(draft, plan, pack, {"words": []}, "a1", "synthetic", 1)
    assert len([unit for unit in expanded["units"] if unit["tab"] == "resursy"]) == 2
    markdown, _ = _render_urok_markdown(draft, expanded, pack, {"words": []})
    assert markdown.count("Anna Ohoiko") == 2
    assert "ulp-1-00" not in markdown and "_l0001" not in markdown
    resources = build_resursy_entries(lesson, pack, draft=draft)
    assert [row[2]["description"] for row in resources] == ["Excerpt 1", "Excerpt 2"]
    assert all(row[2]["url"] == "https://www.ukrainianlessons.com/" for row in resources)
    assert len([span for span in provenance["spans"] if span["tab"] == "resursy"]) == 2
