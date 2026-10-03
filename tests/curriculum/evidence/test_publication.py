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
    allowed = {key: entry for key, entry in entries.items() if entry["publish"]["allowed"]}
    assert len(allowed) == 162
    unconfirmed = {key for key, entry in entries.items() if entry["publish"].get("reason") == "title_unconfirmed"}
    assert unconfirmed == {"9-klas-tekhnolohiyi-bilenko-2026"}
    assert len(allowed) + len(unconfirmed) == 163
    assert {entry["grade"] for entry in allowed.values()} == set(range(1, 12))
    assert {key for key, entry in entries.items() if not entry["publish"]["allowed"] and key not in unconfirmed} == set(
        PRIVATE
    )
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
    candidates = {key: entry for key, entry in entries.items() if key not in PRIVATE}
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


@pytest.mark.parametrize("file", [*PRIVATE, "unregistered", BOOK + ".txt"])
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
        if not entry["publish"]["allowed"]:
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


@pytest.mark.parametrize('slug,policy', list(publication.load_owned_rights().items()))
def test_every_owned_identity_denies_quotes_before_injected_registry(slug, policy):
    rec = record(slug)
    injected = {slug: {'file': slug, 'kind': 'textbook', 'publish': {'allowed': True, 'limit_chars': 800},
                       'resource_credit': {'title': 'Injected credit', 'url': 'https://example.com/'}}}
    with pytest.raises(ValueError, match=r'^owned_quote_refused:'):
        publication.quote_attribution(rec, injected)
    if policy['rights'] == 'private_permission':
        with pytest.raises(ValueError, match=r'^private_citation_refused:'):
            publication.resource_citation(rec, injected)
        with pytest.raises(ValueError, match=r'^private_citation_refused:'):
            publication.source_attribution(rec, injected)
    else:
        assert publication.resource_citation(rec, {})['title']


@pytest.mark.parametrize('content', [
    '[]', 'schema: 1\nsources: {}', 'schema: 2\nsources: {x: {rights: owned_cite_only}}',
    'schema: 1\nsources: {x: {rights: unrestricted}}', 'schema: 1\nsources: [',
    'schema: 1\nsources: {x: {rights: owned_cite_only, publish: true}}',
    'schema: 1\nsources: {x: {rights: private_permission, title: secret}}',
    'schema: 1\nsources: {x: {rights: owned_cite_only, title: null}}',
    'schema: 1\nsources: {x: {rights: owned_cite_only, author: []}}',
    'schema: 1\nsources:\n  x: {rights: private_permission}\n  x: {rights: owned_cite_only}',
])
def test_malformed_owned_rights_fail_closed_even_for_injected_grants(tmp_path, monkeypatch, content):
    path = tmp_path / 'rights.yaml'
    monkeypatch.setattr(publication, 'OWNED_RIGHTS_PATH', path)
    for operation in (publication.quote_attribution, publication.resource_citation, publication.source_attribution):
        with pytest.raises(ValueError, match=r'^owned_rights_unreadable:'):
            operation(record(), publication.load_registry())
    path.write_text(content)
    for operation in (publication.quote_attribution, publication.resource_citation, publication.source_attribution):
        with pytest.raises(ValueError, match=r'^owned_rights_unreadable:'):
            operation(record(), publication.load_registry())


def test_owned_rights_withdrawal_is_immediate(tmp_path, monkeypatch):
    path = tmp_path / 'rights.yaml'
    monkeypatch.setattr(publication, 'OWNED_RIGHTS_PATH', path)
    path.write_text('schema: 1\nsources: {synthetic: {rights: owned_cite_only, title: Synthetic work}}')
    rec = record('synthetic')
    assert publication.resource_citation(rec, {})['title'] == 'Synthetic work'
    path.write_text('schema: 1\nsources: {synthetic: {rights: private_permission}}')
    with pytest.raises(ValueError, match='private_citation_refused'):
        publication.resource_citation(rec, {})


def test_protected_denominator_includes_skips_legacy_works_and_ulp_seasons():
    new_ids = {
        'oho-a1-workbook', 'oho-a1-transcripts', 'oho-a1-unit-audio',
        'yak-inozemtsi-kozaka-riatuvaly', 'yak-inozemtsi-kozaka-riatuvaly-audio',
        'ulp-premium-s1-s6', 'ulp-premium-audio-anki', 'fmu-1-premium', 'ulp-charts',
        'yabluko-advanced', 'chytanka-chomuchka', 'dyvovyzhni-pryhody-zvychainykh',
        'lehendy-pro-kozakiv', 'unikalni-ukrainski-rechi', 'vydatni-ukrainky', 'paska',
        'hto-bachyv-khomiaka', 'teacher-a-slides', 'teacher-b-notes', 'operator-study-files',
    }
    existing = {'anna-ohoiko-1000-words-2nd-ed', 'anna-ohoiko-500-verbs',
                'pohribnyi-ukrainska-literaturna-vymova-1992', *(f'ulp-{i}-00-lesson-notes' for i in range(1, 7))}
    entries = publication.load_owned_rights()
    assert set(entries) == {*(f'owned-{ident}' for ident in new_ids), *existing}
    private = {slug for slug, policy in entries.items() if policy['rights'] == 'private_permission'}
    assert private == {'owned-teacher-a-slides', 'owned-teacher-b-notes', 'owned-operator-study-files'}
    assert all(set(entries[slug]) == {'rights'} for slug in private)
