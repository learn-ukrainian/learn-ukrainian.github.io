"""Exact-source permission, attribution, and publication-vs-grounding regressions."""

import re
from unittest.mock import patch

import pytest
import yaml

from scripts.curriculum.evidence import publication

BOOK = "1-klas-bukvar-zaharijchuk-2025-1"
PRIVATE = [*(f"ulp-{i}-00-lesson-notes" for i in range(1, 7)), "anna-ohoiko-1000-words-2nd-ed", "anna-ohoiko-500-verbs"]


def record(file=BOOK, quote="Synthetic excerpt", page=39):
    return {"id": "T-001", "source": {"kind": "textbook", "file": file, "page": page}, "quote": quote}


def test_policy_denominator_and_private_denials():
    entries = publication.load_registry()
    allowed = {
        key: entry
        for key, entry in entries.items()
        if entry["publish"]["allowed"] and key not in publication.NAMED_EXCERPTS
    }
    assert len(allowed) == 162
    unconfirmed = {key for key, entry in entries.items() if entry["publish"].get("reason") == "title_unconfirmed"}
    assert unconfirmed == {"9-klas-tekhnolohiyi-bilenko-2026"}
    assert len(allowed) + len(unconfirmed) == 163
    assert {entry["grade"] for entry in allowed.values()} == set(range(1, 12))
    assert {key for key, entry in entries.items() if not entry["publish"]["allowed"] and key not in unconfirmed} == set(
        PRIVATE
    ) - publication.NAMED_EXCERPTS
    for key, entry in allowed.items():
        assert entry["file"] == key
        assert entry["publish"] == {
            "allowed": True,
            "limit_chars": 800,
            "attribution": "ukrainian-short",
        }


def test_attribution_and_exact_character_boundary():
    attribution = publication.quote_attribution(record(quote="x" * 800))
    assert attribution == "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 39"
    with pytest.raises(ValueError, match=r"^publication_limit:"):
        publication.quote_attribution(record(quote="x" * 801))
    # Unicode characters, not UTF-8 bytes; whitespace is counted, never stripped.
    assert publication.quote_attribution(record(quote="é" * 800)) == attribution
    with pytest.raises(ValueError, match=r"^publication_limit:"):
        publication.quote_attribution(record(quote="é" * 800 + " "))


@pytest.mark.parametrize(
    "file,year,chunk,citation",
    [
        (
            "5-klas-ukrmova-zabolotnyi-2023",
            2022,
            "s0003",
            "Заболотний, «Українська мова», 5 клас, 2022, с. 12",
        ),
        (
            "7-klas-tekhnolohiyi-bilenko-2024",
            2023,
            "s0001",
            "Біленко, «Технології», 7 клас, 2023, с. 12",
        ),
        (
            "9-klas-zarubizhna-literatura-kovbasenko-2026",
            2025,
            "s0000",
            "Ковбасенко, «Зарубіжна література», 9 клас, 2025, с. 12",
        ),
    ],
)
def test_citation_uses_imprint_year_instead_of_file_or_pack_year(file, year, chunk, citation):
    entries = publication.load_registry()
    entry = entries[file]
    proof = entry["year_provenance"]
    assert entry["year"] == proof["imprint_year"] == year
    assert proof["chunk_id"] == f"{file}_{chunk}"
    assert proof["status"] == "confirmed"
    assert proof["file_id_year"] != year
    rec = record(file=file, page=12)
    rec["source"]["year"] = proof["file_id_year"]
    assert publication.quote_attribution(rec) == publication.source_attribution(rec) == citation


def test_year_checks_cover_candidates_without_inventing_missing_imprints():
    entries = publication.load_registry()
    candidates = {
        key: entry for key, entry in entries.items() if key not in PRIVATE and key not in publication.NAMED_EXCERPTS
    }
    assert len(candidates) == 163
    for key, entry in candidates.items():
        proof = entry["year_provenance"]
        assert proof["source_file"] == key
        if proof["status"] == "confirmed":
            assert proof["imprint_year"] == entry["year"]
            assert proof["chunk_id"].startswith(f"{key}_s")
            assert str(entry["year"]) in proof["year_text"]
            assert proof["basis"] in {"catalogue_entry", "colophon_print_date", "title_page_imprint"}
            assert proof["page"] > 0
        else:
            assert proof["status"] == "unconfirmed"
            assert proof["checked_chunk_ids"]
            assert proof["searches"] == ["УДК", "ISBN", "Навчальне видання"]
            assert "imprint_year" not in proof
    withheld = entries["9-klas-tekhnolohiyi-bilenko-2026"]
    assert withheld["title"] is None
    assert withheld["title_search"]["status"] == "unconfirmed"
    assert "Пелагейченко" in withheld["title_search"]["searches"]
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(record(file=withheld["file"]))


@pytest.mark.parametrize(
    "file", [*(file for file in PRIVATE if file not in publication.NAMED_EXCERPTS), "unregistered", BOOK + ".txt"]
)
def test_denied_and_unregistered_sources(file):
    rec = record(file)
    rec["source"]["publish"] = {"allowed": True, "limit_chars": 9999, "attribution": "Fake"}
    with pytest.raises(ValueError, match=r"^owned_quote_refused:" if file in PRIVATE else r"^publication_right:"):
        publication.quote_attribution(rec)


@pytest.mark.parametrize("mutation", ["page", "author", "title", "year", "grade", "template"])
def test_attribution_is_required(mutation):
    entries = publication.load_registry()
    rec = record()
    if mutation == "page":
        rec["source"]["page"] = None
    elif mutation == "template":
        entries[BOOK]["publish"]["attribution"] = "Source"
    else:
        entries[BOOK][mutation] = None
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(rec, entries)


@pytest.mark.parametrize(
    "right", [{}, {"allowed": "true"}, {"allowed": True, "limit_chars": True}, {"allowed": True, "limit_chars": 0}]
)
def test_malformed_right_fails_closed(right):
    entries = publication.load_registry()
    entries[BOOK]["publish"] = right
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(record(), entries)


def test_source_kind_and_registry_identity_cannot_be_spoofed():
    rec = record()
    rec["source"]["kind"] = "literary"
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(rec)
    entries = publication.load_registry()
    entries[BOOK]["file"] = "another-source"
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(record(), entries)


@pytest.mark.parametrize("content", ["sources: []", "[]", "sources: [", "sources: null", "sources: {book: null}"])
def test_unavailable_or_malformed_registry(tmp_path, content):
    path = tmp_path / "registry.yaml"
    with pytest.raises(ValueError, match=r"^publication_registry_unreadable:"):
        publication.load_registry(path)
    path.write_text(content)
    with pytest.raises(ValueError, match=r"^publication_registry_unreadable:"):
        publication.load_registry(path)


def test_registry_is_reread_after_permission_withdrawal(tmp_path):
    entries = publication.load_registry()
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"sources": entries}))
    assert publication.quote_attribution(record(), publication.load_registry(path))
    entries[BOOK]["publish"]["allowed"] = False
    path.write_text(yaml.safe_dump({"sources": entries}))
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(record(), publication.load_registry(path))


def test_quoted_records_separates_grounding():
    lesson = {
        "steps": [
            {"id": "s1", "needs": ["quote"], "evidence": ["T-001"], "explains": ["T-002"], "ref": "T-003"},
            {"id": "s2", "needs": ["culture"], "explains": ["T-004"]},
        ]
    }
    expected = {"T-001": "s1", "T-002": "s1", "T-003": "s1"}
    assert publication.quoted_records(lesson) == expected
    assert publication.quoted_records({"lessons": [lesson]}) == expected


@pytest.mark.parametrize("field", ["grade", "page"])
@pytest.mark.parametrize("value", [0, -1, True, "1", 1.5, None])
def test_positive_integer_grade_and_page(field, value):
    entries = publication.load_registry()
    rec = record()
    (entries[BOOK] if field == "grade" else rec["source"])[field] = value
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(rec, entries)


def test_registry_is_cached_and_caller_mutations_are_isolated(tmp_path):
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"sources": publication.load_registry()}))
    with patch.object(publication.yaml, "safe_load", wraps=yaml.safe_load) as parse:
        entries = publication.load_registry(path)
        entries[BOOK]["publish"]["allowed"] = False
        assert publication.quote_attribution(record(), publication.load_registry(path))
        assert parse.call_count == 1


def test_registry_read_error_has_typed_reason(tmp_path):
    path = tmp_path / "registry.yaml"
    path.write_text("sources: {}")
    with patch.object(publication.Path, "read_text", side_effect=PermissionError):
        with pytest.raises(ValueError, match=r"^publication_registry_unreadable:"):
            publication.load_registry(path)


def test_every_allowed_source_has_confirmed_human_bibliography():
    for key, entry in publication.load_registry().items():
        if not entry["publish"]["allowed"] or key in publication.NAMED_EXCERPTS:
            continue
        citation = publication.quote_attribution(record(file=key))
        assert key not in citation
        assert not re.search(r"[A-Za-z]", citation)
        assert f"«{entry['title']}»" in citation
        assert ", с. 39" in citation
        assert entry["title_provenance"].get("heading") or entry["title_provenance"].get("title_text")
        if re.search(r"-20\d\d-[12]$", key):
            assert entry["part"] in (1, 2)
            assert entry["title_provenance"]["part_label"]


def test_unconfirmed_title_cannot_publish_even_with_allow_claim():
    entries = publication.load_registry()
    entries[BOOK]["title_provenance"] = None
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(record(), entries)
    for key, entry in entries.items():
        if entry["publish"].get("reason") == "title_unconfirmed":
            with pytest.raises(ValueError, match=r"^publication_right:"):
                publication.quote_attribution(record(file=key), entries)


def test_grade_ranges_and_parts_are_recorded_data():
    entries = publication.load_registry()
    key = "10-11-klas-mystectvo-nazarenko-2018"
    assert entries[key]["grade"] == 10
    assert entries[key]["grade_end"] == 11
    assert publication.quote_attribution(record(file=key, page=12)) == "Назаренко, «Мистецтво», 10–11 клас, 2018, с. 12"
    entries[BOOK]["part"] = 7
    assert "ч. 7" in publication.quote_attribution(record(), entries)


@pytest.mark.parametrize(
    "field,value",
    [
        ("grade_end", 0),
        ("grade_end", "11"),
        ("part", 0),
        ("part", True),
        ("title", BOOK),
        ("title", "English"),
        ("author", "Author"),
    ],
)
def test_invalid_bibliography_cannot_reach_learner(field, value):
    entries = publication.load_registry()
    entries[BOOK][field] = value
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(record(), entries)


@pytest.mark.parametrize("file", PRIVATE)
def test_private_credits_are_registry_owned_and_never_quote_rights(file):
    entries = publication.load_registry()
    rec = record(file)
    rec["supports"] = rec["quote"] = "PRIVATE TEXT MUST NEVER PRINT"
    rec["source"]["resource_credit"] = {"title": "Spoof", "url": "https://example.com/"}
    citation = publication.resource_citation(rec)
    assert citation["title"] == entries[file]["resource_credit"]["title"]
    assert citation["url"] == entries[file]["resource_credit"]["url"]
    assert citation["description"] == ""
    assert "PRIVATE" not in str(citation)
    if file in publication.NAMED_EXCERPTS:
        with pytest.raises(ValueError, match="publication_limit"):
            publication.quote_attribution({**rec, "quote": "x" * 201})
    else:
        with pytest.raises(ValueError, match="owned_quote_refused"):
            publication.quote_attribution(rec)


@pytest.mark.parametrize("field", ["episode_url", "url"])
def test_ulp_episode_link_keeps_homepage_credit(field):
    rec = record("ulp-1-00-lesson-notes")
    rec[field] = "https://www.ukrainianlessons.com/episode1/"
    citation = publication.resource_citation(rec)
    assert citation == {
        "title": "Ukrainian Lessons Podcast — Анна Огойко",
        "url": "https://www.ukrainianlessons.com/",
        "description": "<https://www.ukrainianlessons.com/episode1/>",
    }


@pytest.mark.parametrize("file", ["uni-unregistered", "9-klas-tekhnolohiyi-bilenko-2026"])
def test_grounding_without_citation_metadata_needs_no_right(file):
    assert publication.resource_citation(record(file)) is None


def test_resource_registry_failure_is_not_silently_omitted(tmp_path, monkeypatch):
    monkeypatch.setattr(publication, "REGISTRY_PATH", tmp_path / "absent")
    with pytest.raises(ValueError, match="publication_registry_unreadable"):
        publication.resource_citation(record())


def test_resource_bibliography_survives_quote_right_withdrawal():
    entries = publication.load_registry()
    entries[BOOK]["publish"]["allowed"] = False
    assert publication.resource_citation(record(), entries)["title"] == publication.source_attribution(
        record(), entries
    )


@pytest.mark.parametrize("credit", [{}, {"title": "", "url": "https://example.com/"}, {"title": "Credit", "url": None}])
def test_incomplete_resource_credit_is_omitted(credit):
    entries = publication.load_registry()
    entries[PRIVATE[0]]["resource_credit"] = credit
    assert publication.resource_citation(record(PRIVATE[0]), entries) is None


def test_resource_credit_is_bound_to_source_identity():
    rec = record(PRIVATE[0])
    rec["source"]["kind"] = "literary"
    assert publication.resource_citation(rec) is None
    entries = publication.load_registry()
    entries[PRIVATE[0]]["file"] = "other"
    assert publication.resource_citation(record(PRIVATE[0]), entries) is None


@pytest.mark.parametrize(
    "url", ["https://example.com/episode1/", "javascript:alert(1)", "https://www.ukrainianlessons.com/a>bad"]
)
def test_invalid_episode_url_does_not_reach_resource_description(url):
    rec = record(PRIVATE[0])
    rec["episode_url"] = url
    assert publication.resource_citation(rec)["description"] == ""


def test_textbook_resource_credit_never_publishes_author_supports():
    rec = record()
    rec["supports"] = "ZZauthor_supportsZZ"
    rec["source"]["author"] = "ZZuntrusted_authorZZ"
    citation = publication.resource_citation(rec)
    assert citation == {"title": publication.source_attribution(rec), "url": "", "description": ""}
    assert "ZZ" not in str(citation)


@pytest.mark.parametrize("slug,policy", list(publication.load_owned_rights().items()))
def test_every_owned_identity_denies_quotes_before_injected_registry(slug, policy):
    rec = record(slug)
    injected = {
        slug: {
            "file": slug,
            "kind": "textbook",
            "publish": {"allowed": True, "limit_chars": 800},
            "resource_credit": {"title": "Injected credit", "url": "https://example.com/"},
        }
    }
    with pytest.raises(
        ValueError,
        match=r"^publication_scope_incomplete:" if slug in publication.NAMED_EXCERPTS else r"^owned_quote_refused:",
    ):
        publication.quote_attribution(rec, injected)
    if policy["rights"] == "private_permission":
        with pytest.raises(ValueError, match=r"^private_citation_refused:"):
            publication.resource_citation(rec, injected)
        with pytest.raises(ValueError, match=r"^private_citation_refused:"):
            publication.source_attribution(rec, injected)
    else:
        assert publication.resource_citation(rec, {})["title"]


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        "schema: 1\nsources: {}",
        "schema: 2\nsources: {x: {rights: owned_cite_only}}",
        "schema: 1\nsources: {x: {rights: unrestricted}}",
        "schema: 1\nsources: [",
        "schema: 1\nsources: {x: {rights: owned_cite_only, publish: true}}",
        "schema: 1\nsources: {x: {rights: private_permission, title: secret}}",
        "schema: 1\nsources: {x: {rights: owned_cite_only, title: null}}",
        "schema: 1\nsources: {x: {rights: owned_cite_only, author: []}}",
        "schema: 1\nsources:\n  x: {rights: private_permission}\n  x: {rights: owned_cite_only}",
    ],
)
def test_malformed_owned_rights_fail_closed_even_for_injected_grants(tmp_path, monkeypatch, content):
    path = tmp_path / "rights.yaml"
    monkeypatch.setattr(publication, "OWNED_RIGHTS_PATH", path)
    for operation in (publication.quote_attribution, publication.resource_citation, publication.source_attribution):
        with pytest.raises(ValueError, match=r"^owned_rights_unreadable:"):
            operation(record(), publication.load_registry())
    path.write_text(content)
    for operation in (publication.quote_attribution, publication.resource_citation, publication.source_attribution):
        with pytest.raises(ValueError, match=r"^owned_rights_unreadable:"):
            operation(record(), publication.load_registry())


def test_owned_rights_withdrawal_is_immediate(tmp_path, monkeypatch):
    path = tmp_path / "rights.yaml"
    monkeypatch.setattr(publication, "OWNED_RIGHTS_PATH", path)
    path.write_text("schema: 1\nsources: {synthetic: {rights: owned_cite_only, title: Synthetic work}}")
    rec = record("synthetic")
    assert publication.resource_citation(rec, {})["title"] == "Synthetic work"
    path.write_text("schema: 1\nsources: {synthetic: {rights: private_permission}}")
    with pytest.raises(ValueError, match="private_citation_refused"):
        publication.resource_citation(rec, {})


def test_protected_denominator_includes_skips_legacy_works_and_ulp_seasons():
    new_ids = {
        "oho-a1-workbook",
        "oho-a1-transcripts",
        "oho-a1-unit-audio",
        "yak-inozemtsi-kozaka-riatuvaly",
        "yak-inozemtsi-kozaka-riatuvaly-audio",
        "ulp-premium-audio-anki",
        "fmu-1-premium",
        "ulp-charts",
        "yabluko-advanced",
        "chytanka-chomuchka",
        "dyvovyzhni-pryhody-zvychainykh",
        "lehendy-pro-kozakiv",
        "unikalni-ukrainski-rechi",
        "vydatni-ukrainky",
        "paska",
        "hto-bachyv-khomiaka",
        "teacher-a-slides",
        "teacher-b-notes",
        "operator-study-files",
    }
    existing = {
        "anna-ohoiko-1000-words-2nd-ed",
        "anna-ohoiko-500-verbs",
        "pohribnyi-ukrainska-literaturna-vymova-1992",
        *(f"ulp-{i}-00-lesson-notes" for i in range(1, 7)),
    }
    entries = publication.load_owned_rights()
    assert set(entries) == {*(f"owned-{ident}" for ident in new_ids), *existing}
    assert "owned-ulp-premium-s1-s6" not in entries
    private = {slug for slug, policy in entries.items() if policy["rights"] == "private_permission"}
    assert private == {"owned-teacher-a-slides", "owned-teacher-b-notes", "owned-operator-study-files"}
    assert all(set(entries[slug]) == {"rights"} for slug in private)


def owned_entries(chars=20000, unit_chars=2000):
    """Synthetic canonical metadata, separate from the driver's held-out proof."""
    import hashlib

    entries = publication.load_registry()
    for file in publication.NAMED_EXCERPTS:
        units = {
            str(i): {
                "number": str(i),
                "chars": unit_chars,
                "sha256": hashlib.sha256(("x" * unit_chars).encode()).hexdigest(),
            }
            for i in range(1, chars // unit_chars + 1)
        }
        entries[file]["canonical"] = {"canonical_chars": chars, "unit_count": len(units), "units": units}
    return entries


def owned_occurrence(size=120, *, lesson=1, step="s1", unit=1, file="ulp-1-00-lesson-notes", ref="T-001"):
    rec = record(file, "x" * size)
    rec["source"].update(chunk_id=f"{file}_l{unit:04d}_w001", section_id=None)
    return {"key": ("l2-uk-en", "a1", "synthetic", lesson, step, ref), "record": rec, "column": "lesson"}


def test_owned_excerpt_course_boundary_repeats_and_generated_copies():
    entries = owned_entries()
    first = owned_occurrence()
    boundary = owned_occurrence(80, lesson=2, unit=2)
    report = publication.check_occurrences([first, boundary, first], entries)
    assert report["errors"] == []
    assert report["sources"]["ulp-1-00-lesson-notes"]["lesson"] == 200
    over = publication.check_occurrences([first, owned_occurrence(120, lesson=2, unit=2)], entries)
    assert any(e.startswith("publication_course_limit:") for e in over["errors"])
    repeated_step = publication.check_occurrences([first, owned_occurrence(step="s2", unit=2)], entries)
    assert any(e.startswith("publication_course_limit:") for e in repeated_step["errors"])
    tampered = owned_occurrence(119)
    assert any(
        e.startswith("publication_scope_incomplete:")
        for e in publication.check_occurrences([first, tampered], entries)["errors"]
    )


def test_owned_excerpt_unit_and_lesson_caps():
    entries = owned_entries(60000, 2000)
    report = publication.check_occurrences([owned_occurrence(), owned_occurrence(120, lesson=2)], entries)
    assert any(e.startswith("publication_unit_limit:") for e in report["errors"])
    report = publication.check_occurrences([owned_occurrence(160), owned_occurrence(160, step="s2", unit=2)], entries)
    assert any(e.startswith("publication_lesson_limit:") for e in report["errors"])
    uses = [
        owned_occurrence(10, step=f"s{i}", unit=i, file=file)
        for i, file in enumerate(sorted(publication.NAMED_EXCERPTS)[:4], 1)
    ]
    assert any(
        e.startswith("publication_lesson_limit:") for e in publication.check_occurrences(uses, entries)["errors"]
    )
    uses = [
        owned_occurrence(180, step=f"s{i}", unit=i, file=file)
        for i, file in enumerate(sorted(publication.NAMED_EXCERPTS)[:3], 1)
    ]
    assert any(
        e.startswith("publication_lesson_limit:") for e in publication.check_occurrences(uses, entries)["errors"]
    )
    uses = [owned_occurrence(10, step=f"s{i}", unit=i) for i in range(1, 4)]
    assert any(
        e.startswith("publication_lesson_limit:") for e in publication.check_occurrences(uses, entries)["errors"]
    )


def test_owned_excerpt_nfc_original_and_exact_named_exception():
    entries = publication.load_registry()
    assert len(publication.NAMED_EXCERPTS) == 11
    assert {
        key for key, val in publication.load_owned_rights().items() if val.get("short_excerpts")
    } == publication.NAMED_EXCERPTS
    for file in publication.NAMED_EXCERPTS:
        assert publication.quote_attribution(record(file, "e\u0301" * 200), entries)
        with pytest.raises(ValueError, match="publication_limit"):
            publication.quote_attribution(record(file, "e\u0301" * 201), entries)
        assert entries[file]["canonical"]["canonical_chars"] == sum(
            unit["chars"] for unit in entries[file]["canonical"]["units"].values()
        )
    for file in (
        "anna-ohoiko-1000-words-2nd-ed",
        "anna-ohoiko-500-verbs",
        "owned-oho-a1-unit-audio",
        "owned-teacher-a-slides",
    ):
        with pytest.raises(ValueError, match="owned_quote_refused"):
            publication.quote_attribution(record(file))


@pytest.mark.parametrize("field", ["author", "title", "public_link"])
def test_owned_excerpt_required_attribution_never_uses_pack_spoof(field):
    entries = owned_entries()
    file = "ulp-1-00-lesson-notes"
    entries[file][field] = None
    rec = record(file)
    rec["source"].update(author="Spoof", title="Spoof", url="https://example.com/")
    with pytest.raises(ValueError, match="publication_scope_incomplete"):
        publication.quote_attribution(rec, entries)


@pytest.mark.parametrize("mutation", ["chars", "count", "hash", "number", "policy", "alias"])
def test_owned_excerpt_denominator_and_alias_tampering_fails(mutation):
    entries = owned_entries()
    file = "ulp-1-00-lesson-notes"
    entry = entries[file]
    if mutation == "chars":
        entry["canonical"]["canonical_chars"] += 1
    elif mutation == "count":
        entry["canonical"]["unit_count"] += 1
    elif mutation == "hash":
        entry["canonical"]["units"]["1"]["sha256"] = "bad"
    elif mutation == "number":
        entry["canonical"]["units"]["1"]["number"] = "2"
    elif mutation == "policy":
        entry["publish"]["limit_chars"] = 999
    elif mutation == "alias":
        entry["file"] = "invented-alias"
    code = "publication_denominator_drift" if mutation in {"chars", "count"} else "publication_scope_incomplete"
    with pytest.raises(ValueError, match=code):
        publication.validate_owned_policy(file, entry)


def test_owned_excerpt_example_activity_and_repeated_draft_occurrences():
    rec = owned_occurrence()["record"]
    ex = {**rec, "id": "EX-001", "text": rec["quote"]}
    del ex["quote"]
    pack = {"texts": [rec], "examples": [ex]}
    plan = {
        "n": 1,
        "steps": [
            {"id": "s1", "needs": ["quote", "example"], "evidence": ["T-001", "EX-001"], "practice": ["a1"]},
            {"id": "s2", "needs": ["quote"], "ref": "T-001", "practice": ["a2"]},
        ],
        "activities": [
            {"id": "a1", "focus": "host: {kind: quote, ref: T-001}"},
            {"id": "a2", "focus": "quote host refs T-001"},
        ],
    }
    found = publication.excerpt_occurrences(plan, pack)
    assert len(found) == 3 and all(row["record"]["quote"] == "x" * 120 for row in found)
    draft = {
        "steps": [{"id": "s1", "blocks": [{"kind": "example", "ref": "EX-001"}, {"kind": "example", "ref": "EX-001"}]}]
    }
    assert len(publication.excerpt_occurrences({"steps": []}, pack, draft=draft)) == 2
    with pytest.raises(ValueError, match="publication_scope_incomplete: actual excerpt exceeds planned reservation"):
        publication.enforce_publication(
            {"steps": [{"id": "s1", "needs": ["example"], "ref": "EX-001"}]}, pack, draft=draft
        )
    with pytest.raises(ValueError, match="publication_scope_incomplete"):
        publication.excerpt_occurrences(plan, {})
    plan["steps"][1]["practice"] = []
    with pytest.raises(ValueError, match="activity host step missing"):
        publication.excerpt_occurrences(plan, pack)


def test_owned_excerpt_full_sections_metadata_and_substring_proof():
    import sqlite3

    from scripts.curriculum.evidence.sources import Sources

    file = "ulp-1-00-lesson-notes"
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE textbook_sections(section_id INTEGER, source_file TEXT, section_number TEXT, full_text TEXT, page_start INTEGER);
        CREATE TABLE textbooks(chunk_id TEXT, source_file TEXT, parent_section_id INTEGER, text TEXT);
    """)
    conn.execute("INSERT INTO textbook_sections VALUES (1, ?, '1', ?, 1)", (file, "x\n y " * 1000))
    conn.execute("INSERT INTO textbooks VALUES (?, ?, NULL, ?)", (file + "_l0001_w001", file, "x  y " * 100))
    api = Sources()
    api._db = lambda: conn
    try:
        metadata = api.publication_metadata(file)
        assert metadata["canonical_chars"] == 5000 and metadata["unit_count"] == 1
        entry = publication.load_registry()[file]
        entry["canonical"] = __import__("copy").deepcopy(metadata)
        rec = record(file, "x y")
        rec["source"]["chunk_id"] = file + "_l0001_w001"
        assert publication.publication_unit(rec, entry, api) == "1"
        assert publication.validate_owned_policy(file, entry, api) == metadata
        entry["canonical"]["canonical_chars"] += 1
        entry["canonical"]["units"]["1"]["chars"] += 1
        with pytest.raises(ValueError, match="publication_denominator_drift"):
            publication.validate_owned_policy(file, entry, api)
        entry["canonical"] = metadata
        with pytest.raises(ValueError, match="quote_mismatch"):
            publication.publication_unit({**rec, "quote": "absent"}, entry, api)
        rec["source"]["section_id"] = 1
        with pytest.raises(ValueError, match="forged parent section"):
            publication.publication_unit(rec, entry, api)
        conn.execute("UPDATE textbooks SET parent_section_id=1")
        assert publication.publication_unit(rec, entry, api) == "1"
        rec["source"]["section_id"] = 2
        with pytest.raises(ValueError, match="cited parent differs"):
            publication.publication_unit(rec, entry, api)
        rec["source"]["section_id"] = 1
        conn.execute("UPDATE textbooks SET source_file='unregistered'")
        with pytest.raises(ValueError, match="quote_mismatch: cited chunk belongs to another source"):
            publication.publication_unit(rec, entry, api)
        conn.execute("INSERT INTO textbook_sections VALUES (2, ?, '1', 'x', 2)", (file,))
        with pytest.raises(ValueError, match="ambiguous canonical sections"):
            api.publication_metadata(file)
        conn.execute("DELETE FROM textbook_sections WHERE section_id=2")
        conn.execute("UPDATE textbook_sections SET full_text=''")
        with pytest.raises(ValueError, match="empty canonical section"):
            api.publication_metadata(file)
    finally:
        conn.close()


def test_owned_excerpt_unknown_unit_registered_relabel_and_right_withdrawal():
    entries = owned_entries()
    occurrence = owned_occurrence()
    occurrence["record"]["source"]["file"] = "ulp-2-00-lesson-notes"
    assert any(
        e.startswith("quote_mismatch:")
        for e in publication.check_occurrences([occurrence], entries)["errors"]
    )
    occurrence = owned_occurrence(unit=99)
    assert any("no canonical unit mapping" in e for e in publication.check_occurrences([occurrence], entries)["errors"])
    file = "ulp-1-00-lesson-notes"
    entries[file]["publish"]["allowed"] = False
    with pytest.raises(ValueError, match="publication_right"):
        publication.quote_attribution(record(file), entries)


@pytest.mark.parametrize("with_api", [False, True])
def test_owned_source_relabel_is_a_quote_mismatch(with_api):
    from types import SimpleNamespace

    entries = owned_entries()
    original = "owned-oho-a1-transcripts"
    claimed = "owned-oho-a1-workbook"
    rec = owned_occurrence(file=original)["record"]
    rec["source"]["file"] = claimed
    api = SimpleNamespace(get_textbook_chunk=lambda _: {"source_file": original}) if with_api else None
    with pytest.raises(ValueError, match=r"^quote_mismatch:"):
        publication.publication_unit(rec, entries[claimed], api)
    # Even a locator relabeled to the claimed prefix cannot change the DB identity.
    if with_api:
        rec["source"]["chunk_id"] = claimed + "_l0001_w001"
        with pytest.raises(ValueError, match=r"^quote_mismatch:"):
            publication.publication_unit(rec, entries[claimed], api)


@pytest.mark.parametrize("chunk_id", [None, "", 123])
def test_missing_or_malformed_publication_locator_remains_scope_incomplete(chunk_id):
    from types import SimpleNamespace

    entries = owned_entries()
    rec = owned_occurrence()["record"]
    file = rec["source"]["file"]
    rec["source"]["chunk_id"] = chunk_id
    with pytest.raises(ValueError, match=r"^publication_scope_incomplete:"):
        publication.publication_unit(rec, entries[file])
    rec["source"]["chunk_id"] = file + "_l0001_w001"
    api = SimpleNamespace(get_textbook_chunk=lambda _: None)
    with pytest.raises(ValueError, match=r"^publication_scope_incomplete:"):
        publication.publication_unit(rec, entries[file], api)


@pytest.mark.parametrize("field", ["canonical_chars", "unit_count"])
@pytest.mark.parametrize("value", [None, "20000", True, 0, -1])
def test_malformed_denominator_stays_distinct_from_drift(field, value):
    entries = owned_entries()
    file = "ulp-1-00-lesson-notes"
    entries[file]["canonical"][field] = value
    with pytest.raises(ValueError, match=r"^publication_scope_incomplete:"):
        publication.validate_owned_policy(file, entries[file])


@pytest.mark.parametrize("field", ["canonical_chars", "unit_count"])
def test_internally_inconsistent_denominator_reports_drift_without_db(field):
    entries = owned_entries()
    file = "ulp-1-00-lesson-notes"
    entries[file]["canonical"][field] *= 2
    report = publication.check_occurrences([owned_occurrence()], entries)
    assert report["status"] == "blocked"
    assert report["errors"] == [f"publication_denominator_drift: {file} canonical totals disagree with units"]


@pytest.mark.parametrize("kind,ref", [("quote", "T-001"), ("example", "EX-001")])
def test_draft_printed_alias_cannot_skip_rights(kind, ref):
    rec = owned_occurrence(file="owned-oho-a1-transcripts")["record"]
    rec["source"]["file"] += "-v2"
    rec["id"] = ref
    if kind == "example":
        rec["text"] = rec.pop("quote")
    pack = {"texts" if kind == "quote" else "examples": [rec]}
    draft = {"steps": [{"id": "s1", "blocks": [{"kind": kind, "ref": ref}]}]}
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.excerpt_occurrences({"steps": []}, pack, draft=draft, registry=owned_entries())


def test_nontextbook_example_retains_existing_admission():
    rec = {"id": "EX-001", "text": "Synthetic example", "source": {"kind": "literary", "file": "synthetic"}}
    plan = {"steps": [{"id": "s1", "needs": ["example"], "ref": "EX-001"}]}
    assert publication.excerpt_occurrences(plan, {"examples": [rec]}, registry=owned_entries()) == []


@pytest.mark.parametrize(
    "malformed",
    [
        None,
        [],
        {"units": []},
        {"units": {"1": {"chars": 1, "number": "1", "sha256": 1}}, "canonical_chars": 1, "unit_count": 1},
    ],
)
def test_owned_excerpt_malformed_canonical_metadata_has_stable_failure(malformed):
    entries = owned_entries()
    file = "ulp-1-00-lesson-notes"
    entries[file]["canonical"] = malformed
    with pytest.raises(ValueError, match="publication_scope_incomplete"):
        publication.validate_owned_policy(file, entries[file])


def test_owned_excerpt_book_grounding_credit_stays_metadata_only():
    rec = record("owned-oho-a1-workbook")
    rec["quote"] = rec["supports"] = "PRIVATE_SYNTHETIC_SENTINEL"
    citation = publication.resource_citation(rec)
    assert citation["url"] == "https://www.ukrainianlessons.com/oho-a1/"
    assert "Anna Ohoiko" in citation["title"]
    assert "PRIVATE_SYNTHETIC_SENTINEL" not in str(citation)


def test_owned_excerpt_unavailable_tracked_scope_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="publication_scope_incomplete: tracked course scope unavailable"):
        publication.tracked_inputs(tmp_path)
