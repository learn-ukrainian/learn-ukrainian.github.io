import json
from pathlib import Path

import pytest

from scripts.audit.generate_search_index import classification_code
from scripts.lexicon import heritage_classifier
from scripts.lexicon.enrich_manifest import _SLOVNYK_CACHE_SCHEMA_VERSION
from scripts.lexicon.heritage_classifier import (
    _cached_slovnyk_hits,
    bound_evidence,
    card_headword_matches,
    classify_lemma,
    classify_surface_form,
    compute_warning_severity,
    is_normative_locator,
    modern_headword_labels,
    names_headword,
    normative_citations,
    resolve_usage_label,
    shares_referent,
    support_passages,
)

DB = Path(__file__).resolve().parent / "fixtures" / "heritage_sample.db"
VESUM_DB = Path(__file__).resolve().parent / "fixtures" / "vesum_sample.db"


def test_surface_drugoje_literary_quote_does_not_create_heritage_badge() -> None:
    status = classify_surface_form("другоє", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] == "unknown"
    assert status["is_russianism"] is False
    assert status["russian_shadow"] is True
    assert status["attestations"] == []


def test_dialect_heritage_forms_are_not_blocked_by_russian_shadow() -> None:
    for word in ("ягілка", "гагілка"):
        lemma_status = classify_lemma(word, db_path=DB, vesum_db_path=VESUM_DB)
        surface_status = classify_surface_form(word, db_path=DB, vesum_db_path=VESUM_DB)

        assert lemma_status["classification"] == "dialect"
        assert lemma_status["is_russianism"] is False
        assert lemma_status["russian_shadow"] is True
        assert surface_status["classification"] == "dialect"
        assert surface_status["is_russianism"] is False
        assert surface_status["attestations"]


def test_sum11_only_entry_is_not_standard_attestation() -> None:
    status = classify_surface_form("перекличка", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] != "standard"
    assert all(attestation["source"] != "sum11" for attestation in status["attestations"])


def test_slash_separated_atlas_lemmas_merge_variant_attestations() -> None:
    status = classify_lemma("вчителька / учителька", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] == "standard"
    assert status["is_russianism"] is False
    assert {attestation["ref"] for attestation in status["attestations"]} == {"вчителька", "учителька"}


def test_specified_russianisms_keep_standard_alternatives() -> None:
    expected = {
        "протиріччя": "суперечність",
        "діюча": "чинна",
    }

    for word, alternative in expected.items():
        status = classify_surface_form(word, db_path=DB, vesum_db_path=VESUM_DB)

        assert status["classification"] == "russianism"
        assert status["is_russianism"] is True
        # #9603: a replacement suggestion is gate evidence, not a named
        # lemma-level authority, so the public Atlas label stays unresolved.
        assert (
            classification_code({"primary_source": "built_vocabulary", "heritage_status": status})
            is None
        )
        assert resolve_usage_label(status)["scope"] == "unresolved"
        assert any(
            attestation["source"] == "standard_alternative" and attestation["ref"] == alternative
            for attestation in status["attestations"]
        )


def test_withheld_vykliuchno_has_no_learner_facing_authentic_sense() -> None:
    status = classify_surface_form("виключно", db_path=DB, vesum_db_path=VESUM_DB)
    warning = status["calque_warning"]
    assert warning["kind"] == "sense_restricted"
    assert "authentic_sense" not in warning


def test_atlas_heritage_labels_use_source_backed_evidence() -> None:
    expected = {
        "глагол": "authentic-archaism",
        "опришок": "historism",
        "ягілка": "dialect",
        "гагілка": "dialect",
    }

    for lemma, classification in expected.items():
        status = classify_lemma(lemma, db_path=DB, vesum_db_path=VESUM_DB)

        assert status["classification"] == classification
        assert status["is_russianism"] is False
        # #9603: attestations are preserved; without the article headword and
        # its dictionary card nothing binds a public label. «глагол» cites only
        # the book title of Антоненко-Давидович, with no excerpt naming the
        # word, so its calque record stays unresolved.
        assert classification_code({"primary_source": "built_vocabulary", "heritage_status": status}) is None
        if lemma == "глагол":
            assert resolve_usage_label(status, headword=lemma)["reason"] == "no_headword_bound_evidence"
        assert any(
            attestation["source"] in {"grinchenko_1907", "esum"}
            for attestation in status["attestations"]
        )


def test_fixture_supports_search_heritage_db_path() -> None:
    from wiki.sources_db import search_heritage

    expected_families = {
        "глагол": "grinchenko",
        "опришок": "esum",
        "ягілка": "esum",
        "гагілка": "esum",
    }

    for lemma, source_family in expected_families.items():
        hits = search_heritage(lemma, include_live_slovnyk=False, db_path=DB)

        assert any(hit["source_family"] == source_family for hit in hits)


def test_common_modern_lemmas_do_not_get_heritage_badges() -> None:
    for lemma in (
        "бути",
        "автобус",
        "журналіст",
        "книга",
        "білий",
        "гарний",
        "адреса",
        "банкір",
        "вельми",
        "гетьман",
        "десятина",
    ):
        status = classify_lemma(lemma, db_path=DB, vesum_db_path=VESUM_DB)

        assert status["classification"] == "standard"
        assert status["is_russianism"] is False


def _write_slovnyk_cache(cache_dir: Path, lemma: str, *, schema_version: int) -> None:
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / f"{lemma}.json").write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "lemma": lemma,
                "lookup_word": lemma,
                "lookups": {
                    "newsum": {
                        "dictionary_slug": "newsum",
                        "dictionary_label": "Словник української мови у 20 томах (СУМ-20)",
                        "word": lemma,
                        "text": "КОБІТА, и, ж., зах. Те саме, що жінка.",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_kobita_ignores_cached_sum20_regional_evidence(monkeypatch, tmp_path) -> None:
    cache_dir = tmp_path / "slovnyk_cache"
    _write_slovnyk_cache(cache_dir, "кобіта", schema_version=_SLOVNYK_CACHE_SCHEMA_VERSION)
    monkeypatch.setenv("LEXICON_SLOVNYK_CACHE", str(cache_dir))

    status = classify_lemma("кобіта", db_path=DB, vesum_db_path=VESUM_DB)

    assert status["classification"] == "standard"
    assert status["is_russianism"] is False
    assert not any("СУМ-20" in attestation["source"] for attestation in status["attestations"])
    assert [(attestation["source"], attestation["ref"]) for attestation in status["attestations"]] == [
        ("VESUM", "кобіта")
    ]


def test_cached_slovnyk_hits_rejects_stale_schema_version(monkeypatch, tmp_path) -> None:
    """#6524 P2 (codex re-verdict): heritage_classifier's own cache reader loaded
    the raw JSON with no version gate, so a stale v2 row (carrying the #6465
    corrupted-join text) still surfaced as a heritage attestation. A row that is
    not on the current schema version must read as a cache miss, not as data."""
    cache_dir = tmp_path / "slovnyk_cache"
    _write_slovnyk_cache(cache_dir, "кобіта", schema_version=2)
    monkeypatch.setenv("LEXICON_SLOVNYK_CACHE", str(cache_dir))

    assert _cached_slovnyk_hits("кобіта") == []

    stale_dir = tmp_path / "slovnyk_cache_current"
    _write_slovnyk_cache(stale_dir, "кобіта", schema_version=_SLOVNYK_CACHE_SCHEMA_VERSION)
    monkeypatch.setenv("LEXICON_SLOVNYK_CACHE", str(stale_dir))

    hits = _cached_slovnyk_hits("кобіта")
    assert len(hits) == 1
    assert hits[0]["source_family"] == "slovnyk_me"


_NAMED_LEXICAL_CALQUE = {
    "kind": "participle",
    "corrections": ["чинний"],
    "source": ["antonenko-p144"],
}


@pytest.mark.parametrize(
    ("heritage_status", "vesum_attested", "max_sovietization_risk", "expected"),
    [
        # #9603: is_russianism from a replacement suggestion alone (no named,
        # lemma-scoped authority) is unresolved, never a red lemma warning.
        (
            {"classification": "russianism", "is_russianism": True, "attestations": []},
            False,
            0,
            "none",
        ),
        # A Russian morphological shadow alone is never normative authority.
        (
            {
                "classification": "unknown",
                "is_russianism": False,
                "russian_shadow": True,
                "attestations": [],
            },
            False,
            0,
            "none",
        ),
        (
            {
                "classification": "unknown",
                "is_russianism": False,
                "russian_shadow": True,
                "attestations": [{"source": "standard_alternative", "ref": "ануж"}],
            },
            False,
            0,
            "none",
        ),
        (
            {
                "classification": "unknown",
                "is_russianism": False,
                "russian_shadow": True,
                "attestations": [{"source": "literary_fts", "ref": "chunk"}],
            },
            False,
            0,
            "none",
        ),
        (
            {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": True,
                "attestations": [],
            },
            False,
            0,
            "none",
        ),
        (
            {
                "classification": "standard",
                "is_russianism": True,
                "russian_shadow": True,
                "attestations": [],
            },
            False,
            0,
            "none",
        ),
        (
            {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": True,
                "attestations": [{"source": "VESUM", "ref": "слово"}],
            },
            True,
            0,
            "treasured",
        ),
        (
            {
                "classification": "dialect",
                "is_russianism": False,
                "russian_shadow": True,
                "attestations": [],
            },
            False,
            0,
            "treasured",
        ),
        # #9603 D05: a citation is not evidence; ``participle`` is not a scope.
        (
            {
                "classification": "unknown",
                "is_russianism": False,
                "russian_shadow": False,
                "attestations": [],
                "curated_calque": _NAMED_LEXICAL_CALQUE,
            },
            False,
            0,
            "none",
        ),
        (
            {
                "classification": "russianism",
                "is_russianism": True,
                "attestations": [],
                "curated_calque": {**_NAMED_LEXICAL_CALQUE, "kind": "lexical"},
            },
            False,
            0,
            "none",
        ),
        # A curated record without a named normative authority is unresolved.
        (
            {
                "classification": "unknown",
                "is_russianism": False,
                "attestations": [],
                "curated_calque": {"kind": "lexical", "corrections": ["чинний"], "source": ["ua-gec"]},
            },
            False,
            0,
            "none",
        ),
        # #7982: an unresolved calque claim on an archaism is neutral, not green.
        (
            {
                "classification": "authentic-archaism",
                "attestations": [{"source": "grinchenko_1907", "ref": "9370"}],
                "calque_warning": {"kind": "lexical", "citations": ["antonenko:Як ми говоримо"]},
            },
            True,
            0,
            "none",
        ),
        # Sense- and phrase-scoped cautions about this headword stay yellow.
        (
            {
                "classification": "standard",
                "attestations": [{"source": "VESUM", "ref": "біля"}],
                "curated_calque": {"kind": "sense_restricted", "corrections": ["близько"], "source": ["litvinova-7"]},
            },
            True,
            0,
            "calque_yellow",
        ),
        (
            {
                "classification": "standard",
                "attestations": [{"source": "VESUM", "ref": "приймати"}],
                "calque_warning": {"kind": "phrasal", "standard_alternatives": ["брати участь"]},
            },
            True,
            0,
            "calque_yellow",
        ),
        # #9603: the recommended replacement of a calque (reverse calque) is
        # never branded; it keeps its own positive attestation.
        (
            {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "attestations": [{"source": "grinchenko_1907", "ref": "чинний"}],
                "reverse_calques": [{"calque": "діючий"}],
            },
            True,
            0,
            "treasured",
        ),
        (
            {
                "classification": "unknown",
                "is_russianism": False,
                "russian_shadow": False,
                "attestations": [],
            },
            False,
            2,
            "soviet_def_blue",
        ),
        (
            {
                "classification": "unknown",
                "is_russianism": False,
                "russian_shadow": True,
                "attestations": [],
            },
            False,
            2,
            "soviet_def_blue",
        ),
    ],
)
def test_compute_warning_severity_is_pure(
    heritage_status: dict,
    vesum_attested: bool,
    max_sovietization_risk: int,
    expected: str,
) -> None:
    assert (
        compute_warning_severity(
            heritage_status,
            vesum_attested=vesum_attested,
            max_sovietization_risk=max_sovietization_risk,
        )
        == expected
    )


def test_connection_pooling_same_thread_reuses_connection() -> None:
    from scripts.lexicon.heritage_classifier import _source_conn, close_cached_connections
    close_cached_connections()
    with _source_conn(DB) as conn1:
        with _source_conn(DB) as conn2:
            assert conn1 is conn2
    close_cached_connections()


def test_connection_pooling_usable_after_context_exit() -> None:
    from scripts.lexicon.heritage_classifier import _source_conn, close_cached_connections
    close_cached_connections()
    with _source_conn(DB) as conn:
        pass
    # Connection remains open and cached for future queries
    with _source_conn(DB) as conn2:
        row = conn2.execute("SELECT 1").fetchone()
        assert row[0] == 1
    close_cached_connections()


def test_connection_pooling_close_cached_connections() -> None:
    from scripts.lexicon.heritage_classifier import _source_conn, close_cached_connections
    with _source_conn(DB) as conn1:
        pass
    close_cached_connections()
    with _source_conn(DB) as conn2:
        assert conn1 is not conn2
    close_cached_connections()


def test_connection_pooling_query_only_mode() -> None:
    import sqlite3

    import pytest

    from scripts.lexicon.heritage_classifier import _source_conn, close_cached_connections
    with _source_conn(DB) as conn:
        try:
            conn.execute("CREATE TABLE _test_ro_fail (id INT)")
            pytest.fail("Should have raised OperationalError in query_only mode")
        except sqlite3.OperationalError:
            pass
    close_cached_connections()


def test_resolve_primary_checkout_matches_git_common_dir() -> None:
    """_source_db_path's primary-checkout fallback is portable, not hardcoded (#6571).

    _resolve_primary_checkout must agree with resolve_main_root and, when set,
    point at a directory owning the shared ``.git`` store (a primary checkout,
    not a worktree gitdir)."""
    from scripts.guardrails.worktree_containment import (
        NotAGitRepositoryError,
        resolve_main_root,
    )
    from scripts.lexicon import heritage_classifier

    resolved = heritage_classifier._resolve_primary_checkout()
    try:
        expected = resolve_main_root(heritage_classifier.ROOT)
    except NotAGitRepositoryError:
        assert resolved is None
        return
    assert resolved == expected
    assert (resolved / ".git").is_dir()


def test_source_db_path_has_no_hardcoded_absolute_path() -> None:
    """The heritage classifier must not carry a hardcoded operator path (#6571)."""
    from scripts.lexicon import heritage_classifier as hc

    src = Path(hc.__file__).read_text(encoding="utf-8")
    assert "/Users/krisztiankoos/projects/learn-ukrainian" not in src


def test_convergence_calques_receive_yellow_severity_and_alternatives() -> None:
    """Pre-Soviet attestation or VESUM membership must not create false-positive green badges for convergence calques (#7982).

    #9603: their curated records cite only the book title «Як ми говоримо»,
    with no excerpt naming the headword, so the claim is unresolved: neutral
    (neither a lemma warning nor a green defence), with the replacement and
    gate fields preserved.
    """
    # 1. Lexical calque with historical attestation: мисль -> думка
    mysl = classify_lemma("мисль", db_path=DB, vesum_db_path=VESUM_DB)
    assert mysl["classification"] == "calque"
    assert mysl["warning_severity"] == "none"
    assert resolve_usage_label(mysl, headword="мисль")["reason"] == "no_headword_bound_evidence"
    assert mysl["is_russianism"] is False
    assert mysl.get("calque_warning") is not None
    assert mysl["calque_warning"]["standard_alternatives"] == ["думка"]

    # Surface form must also inherit calque warning and yellow severity
    mysli = classify_surface_form("мислі", db_path=DB, vesum_db_path=VESUM_DB)
    assert mysli["classification"] == "calque"
    assert mysli["warning_severity"] == "none"
    assert mysli.get("calque_warning") is not None
    assert mysli["calque_warning"]["standard_alternatives"] == ["думка"]

    # 2. Authentic archaism with calque warning: глагол -> дієслово, слово
    hlahol = classify_lemma("глагол", db_path=DB, vesum_db_path=VESUM_DB)
    assert hlahol["classification"] == "authentic-archaism"
    assert hlahol["warning_severity"] == "none"
    assert hlahol["is_russianism"] is False
    assert hlahol.get("calque_warning") is not None
    assert hlahol["calque_warning"]["standard_alternatives"] == ["дієслово", "слово"]

    # 3. Sense-restricted calque: строїти -> будувати, споруджувати
    stroyity = classify_lemma("строїти", db_path=DB, vesum_db_path=VESUM_DB)
    assert stroyity["warning_severity"] == "calque_yellow"
    assert stroyity["is_russianism"] is False
    assert stroyity.get("calque_warning") is not None
    assert stroyity["calque_warning"]["kind"] == "sense_restricted"
    assert "будувати" in stroyity["calque_warning"]["standard_alternatives"]


def test_sense_restricted_vidnoshennia_preserves_standard_and_mathematical_sense() -> None:
    """відношення must retain standard classification, calque_yellow severity, and mathematical authentic sense (#7982)."""
    res = classify_lemma("відношення", db_path=DB, vesum_db_path=VESUM_DB)
    assert res["classification"] == "standard"
    assert res["warning_severity"] == "calque_yellow"
    assert res["is_russianism"] is False
    assert res.get("calque_warning") is not None
    assert res["calque_warning"]["kind"] == "sense_restricted"
    auth_sense = (res["calque_warning"].get("authentic_sense") or "").lower()
    assert "математичне" in auth_sense or "mathematical" in auth_sense or "числове" in auth_sense
    alternatives = res["calque_warning"]["standard_alternatives"]
    assert "ставлення" in alternatives
    assert "стосунки" in alternatives


def test_poizdka_retains_standard_without_calque_warning() -> None:
    """поїздка is a standard short-trip noun (СУМ-20 / СУМ-11) and must not be flagged as a calque (#7982)."""
    res = classify_lemma("поїздка", db_path=DB, vesum_db_path=VESUM_DB)
    assert res["classification"] == "standard"
    assert res["warning_severity"] in ("none", "treasured")
    assert res["is_russianism"] is False
    assert res.get("calque_warning") is None


# --- #9603 usage-label scope ------------------------------------------------

_SUM20_VOZNYI = "ВО́ЗНИЙ, ного, ч., іст. Судовий урядовець у Польщі (до XIX ст.)."
_SUM20_DYVAN_SENSE = "ДИВА́Н, у, ч. 1. іст. Дорадчий орган у султанській Туреччині. 2. М'який меблевий виріб."
_SUM20_HOMONYM = "ДИВА́Н ² , у, ч., іст. Дорадчий орган у султанській Туреччині."
_SUM20_HOROD = "ГОРО́Д, а, ч. Ділянка землі, перев. при садибі, для вирощування овочів."
_VTS_KRYN = "крин -у, ч. , заст. Лілея."


def _card(card_id: str, text: str) -> dict:
    return {"id": card_id, "definitions": [text]}


@pytest.mark.parametrize(
    ("definition", "classes", "ambiguous"),
    [
        (_SUM20_VOZNYI, {"historism"}, False),
        (_SUM20_DYVAN_SENSE, set(), False),
        (_SUM20_HOMONYM, {"historism"}, True),
        (_SUM20_HOROD, set(), False),
        (_VTS_KRYN, {"authentic-archaism"}, False),
        ("I г`ород -а, ч. , спорт. Місце. II гор`од -у, ч. Ділянка.", set(), True),
        # Whole-token markers only: «хвіст.» must not read as «іст.».
        ("ХВІСТ, хвоста́, ч. Задня частина тіла.", set(), False),
    ],
)
def test_modern_headword_labels_bind_only_the_headword_slot(definition, classes, ambiguous) -> None:
    assert modern_headword_labels(definition) == (classes, ambiguous)


@pytest.mark.parametrize(
    ("citations", "expected"),
    [
        (["antonenko-p044", "glazova-10"], ["antonenko-p044", "glazova-10"]),
        (["antonenko:200 Другий та інший"], ["antonenko:200 Другий та інший"]),
        (["slovnyk:davydov"], ["slovnyk:davydov"]),
        (["state-standard:avramenko-7"], ["state-standard:avramenko-7"]),
        (["ua-gec:F/Calque n=2", "grinchenko", "sum-11", "sum-20", "grok-3098"], []),
        (["state-standard", "slovnyk-dicts", "legacy-manifest", "classifier:is_russianism"], []),
        (["slovnyk:foreign_shtepa"], []),
        ("antonenko-p091", ["antonenko-p091"]),
        (None, []),
    ],
)
def test_normative_citations_name_only_normative_authorities(citations, expected) -> None:
    assert normative_citations(citations) == expected


def test_reverse_calque_never_brands_its_recommended_replacement() -> None:
    # Stored DB shape for «бути» (является → бути).
    status = {
        "classification": "standard",
        "attestations": [{"source": "VESUM", "ref": "бути"}],
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
        "calque_warning": None,
        "warning_severity": "calque_yellow",
        "reverse_calques": [
            {"calque": "являтися", "kind": "sense_restricted", "source": ["avramenko-9", "zabolotnyi-9"]}
        ],
    }
    label = resolve_usage_label(status, headword="бути")
    assert label == {"code": None, "scope": "reverse", "authority": [], "evidence": None, "reason": "reverse"}
    assert compute_warning_severity(status, vesum_attested=True) == "treasured"
    assert classification_code({"lemma": "бути", "heritage_status": status}) is None


def test_sense_restricted_calque_stays_contextual() -> None:
    status = {
        "classification": "standard",
        "attestations": [{"source": "VESUM", "ref": "біля"}],
        "curated_calque": {
            "kind": "sense_restricted",
            "corrections": ["близько"],
            "calque_sense": "approximately before a quantity",
            "source": ["grinchenko", "litvinova-7", "ua-gec"],
        },
    }
    label = resolve_usage_label(status, headword="біля")
    assert label["scope"] == "sense"
    assert label["code"] is None
    # A citation names where to look; only an excerpt binds an authority.
    assert label["authority"] == []
    assert label["evidence"] == "approximately before a quantity"
    assert classification_code({"lemma": "біля", "heritage_status": status}) is None
    bound = {
        **status["curated_calque"],
        "evidence": ["7-klas-ukrmova-litvinova-2024_s0010: Кажемо близько ста учнів, а не біля ста учнів."],
    }
    label = resolve_usage_label({**status, "curated_calque": bound}, headword="біля")
    assert label["scope"] == "sense"
    assert label["authority"] == ["7-klas-ukrmova-litvinova-2024_s0010"]


def test_stale_db_russianism_without_scope_is_unresolved() -> None:
    # Stored DB shape for «вид»/«другий» written by calque-cluster reconciliation.
    status = {
        "classification": "russianism",
        "attestations": [
            {"source": "VESUM", "ref": "другий"},
            {"source": "standard_alternative", "ref": "інший"},
        ],
        "is_russianism": True,
        "russian_shadow": True,
        "vesum_attested": True,
        "calque_warning": {"standard_alternatives": ["інший"]},
        "warning_severity": "russianism_red",
    }
    label = resolve_usage_label(status, headword="другий")
    assert label["scope"] == "unresolved"
    assert label["code"] is None
    assert compute_warning_severity(status, vesum_attested=True) == "none"
    assert classification_code({"lemma": "другий", "heritage_status": status}) is None


def test_stale_severity_alone_never_labels() -> None:
    for severity in ("russianism_red", "calque_yellow", "treasured"):
        status = {"classification": "standard", "warning_severity": severity, "attestations": []}
        assert resolve_usage_label(status)["code"] is None
        assert classification_code({"lemma": "слово", "heritage_status": status}) is None


_SUM20_ATTACHED_HOMONYM = "ДИВА́Н², у, ч., іст. Дорадчий орган у султанській Туреччині."
_ESUM_HRYD = {
    "source": "esum",
    "ref": "гридь:1:592",
    "word": "гридь",
    "detail": "гридь (іст.) «нижча верхівка княжої дружини», грйдень «охоронець князя» Ж; — р. (іст.) гридь",
}
_HRYD_GLOSS = "У стародавній Русі — нижча верства княжої дружини."
# Real excerpts: sources MCP style_guide id 44 / antonenko p031; calque_corrections evidence.
_MIRO_SUPPORT = {
    "locator": "antonenko-davydovych-yak-my-hovorymo_p031",
    "passage": '"У нас провели такі міроприємства" і под. Такого слова не було й нема в українській мові.',
}
_MIRO_STORED_EVIDENCE = "Антоненко-Давидович: Відповідником до російських мера, мероприятие є захід, а в множині — заходи"
_SLID_STORED_EVIDENCE = (
    "9-klas-ukrajinska-mova-voron-2017_s0232: следующий — тут: наступний; "
    "Як правильно перекласти ... следующий? ... наступний"
)
_BAZH_EVIDENCE = "antonenko-davydovych-yak-my-hovorymo_p099: Бажаючий – що (котрий, який) бажає – охочий"


@pytest.mark.parametrize(
    ("headword", "status", "cards", "expected_code", "expected_reason"),
    [
        # СУМ-20 headword label binds the historism.
        ("возний", {"classification": "historism"}, [_card("sum20", _SUM20_VOZNYI)], "hist", "lemma"),
        # The label belongs to sense 1 only (диван): no word-level label.
        (
            "диван",
            {"classification": "historism"},
            [_card("sum20", _SUM20_DYVAN_SENSE)],
            None,
            "СУМ-20_headword_unlabelled",
        ),
        # A homonym-indexed card cannot label one Atlas headword.
        ("диван", {"classification": "historism"}, [_card("sum20", _SUM20_HOMONYM)], None, "СУМ-20_headword_unlabelled"),
        (
            "диван",
            {"classification": "historism"},
            [_card("sum20", _SUM20_ATTACHED_HOMONYM)],
            None,
            "СУМ-20_headword_unlabelled",
        ),
        # The modern dictionary has the headword unlabelled (город).
        (
            "город",
            {"classification": "authentic-archaism"},
            [_card("sum20", _SUM20_HOROD)],
            None,
            "СУМ-20_headword_unlabelled",
        ),
        # ВТС is the modern fallback when СУМ-20 is absent.
        ("крин", {"classification": "authentic-archaism"}, [_card("vts", _VTS_KRYN)], "arch", "lemma"),
        # D04: a card for another headword or malformed text authorises nothing.
        (
            "живий",
            {"classification": "historism"},
            [_card("sum20", "ВОЗНИЙ, ного, ч., іст. Судовий урядовець.")],
            None,
            "no_headword_bound_label",
        ),
        ("слово", {"classification": "dialect"}, [_card("sum20", "garbage діал.")], None, "no_headword_bound_label"),
        (None, {"classification": "historism"}, [_card("sum20", _SUM20_VOZNYI)], None, "no_headword_bound_label"),
        # ЕСУМ cognate marker (або: «п. діал.») never labels the headword.
        (
            "або",
            {
                "classification": "dialect",
                "attestations": [
                    {"source": "esum", "ref": "або:1:37", "word": "або", "detail": "або «чи»; — п. діал. «елементарний»"}
                ],
            },
            None,
            None,
            "no_headword_bound_label",
        ),
        # Грінченко quotation substring (хвіст.) never labels the headword.
        (
            "зловити",
            {
                "classification": "historism",
                "attestations": [
                    {"source": "grinchenko_1907", "ref": "1", "word": "зловити", "detail": "Зловив зайця за хвіст."}
                ],
            },
            [_card("sum20", "ЗЛОВИ́ТИ, влю́, ви́ш, док. Схопити.")],
            None,
            "СУМ-20_headword_unlabelled",
        ),
        # Borrowing is an etymological claim: ЕСУМ on the headword binds it.
        (
            "диван",
            {
                "classification": "borrowing",
                "attestations": [
                    {
                        "source": "esum",
                        "ref": "диван:2:63",
                        "word": "диван",
                        "detail": "диван «канапа» — запозичення з турецької",
                    }
                ],
            },
            None,
            "borr",
            "lemma",
        ),
        (
            "диван",
            {
                "classification": "borrowing",
                "attestations": [{"source": "esum", "ref": "x:1:1", "word": "канапа", "detail": "канапа — запозичення"}],
            },
            None,
            None,
            "no_headword_etymology",
        ),
    ],
)
def test_register_labels_need_headword_bound_evidence(headword, status, cards, expected_code, expected_reason) -> None:
    label = resolve_usage_label(status, headword=headword, definition_cards=cards)
    assert label["code"] == expected_code
    assert label["reason"] == expected_reason
    if expected_code:
        assert label["scope"] == "lemma"
        assert label["authority"]


def test_esum_headword_marker_binds_historical_witness() -> None:
    """D02: гридь (іст.) in the ЕСУМ headword slot with the article's referent."""
    status = {"classification": "historism", "attestations": [_ESUM_HRYD]}
    label = resolve_usage_label(status, headword="гридь", gloss=_HRYD_GLOSS)
    assert label == {
        "code": "hist",
        "scope": "lemma",
        "authority": ["ЕСУМ, т. 1, с. 592"],
        "evidence": "гридь (іст.) «нижча верхівка княжої дружини»",
        "reason": "lemma",
    }
    assert compute_warning_severity(status, vesum_attested=True, headword="гридь") == "treasured"
    entry = {"lemma": "гридь", "gloss": _HRYD_GLOSS, "heritage_status": status}
    assert classification_code(entry) == "hist"


@pytest.mark.parametrize(
    ("headword", "gloss", "attestations", "cards"),
    [
        ("гридь", "sofa; couch", [_ESUM_HRYD], None),
        ("гридь", None, [_ESUM_HRYD], None),
        (
            "гридь",
            _HRYD_GLOSS,
            [{**_ESUM_HRYD, "detail": "гридь «нижча верхівка княжої дружини», гридниця (іст.) «приміщення»"}],
            None,
        ),
        ("гридня", _HRYD_GLOSS, [_ESUM_HRYD], None),
        ("гридь", _HRYD_GLOSS, [{**_ESUM_HRYD, "source": "grinchenko_1907"}], None),
        # A modern card for the headword decides modern register.
        ("гридь", _HRYD_GLOSS, [_ESUM_HRYD], [_card("vts", "гридь -і, ж., збірн. Нижча верства княжої дружини.")]),
    ],
)
def test_esum_marker_outside_headword_slot_or_referent_does_not_bind(headword, gloss, attestations, cards) -> None:
    label = resolve_usage_label(
        {"classification": "historism", "attestations": attestations},
        headword=headword,
        definition_cards=cards,
        gloss=gloss,
    )
    assert label["code"] is None
    assert label["scope"] == "unresolved"


def test_bound_treasured_label_precedes_curated_russianism() -> None:
    status = {
        "classification": "authentic-archaism",
        "is_russianism": True,
        "curated_calque": {"kind": "lexical", "evidence": [_BAZH_EVIDENCE]},
    }
    assert resolve_usage_label(status, headword="крин", definition_cards=[_card("vts", _VTS_KRYN)])["code"] == "arch"
    # An unbound archaism does not hide a headword-bound lexical calque.
    assert resolve_usage_label(status, headword="бажаючий")["code"] == "calq"


def test_curated_lexical_russianism_bound_by_a_passage_is_retained() -> None:
    status = {
        "classification": "russianism",
        "is_russianism": True,
        "curated_calque": {
            "kind": "lexical",
            "corrections": ["захід"],
            "note": "рос. мероприятие; use захід / заходи",
            "source": ["antonenko-p044", "glazova-10"],
            "evidence": [_MIRO_STORED_EVIDENCE],
            "normative_support": [_MIRO_SUPPORT],
        },
    }
    label = resolve_usage_label(status, headword="міроприємство")
    assert label["code"] == "rus"
    assert label["scope"] == "lemma"
    assert label["authority"] == ["antonenko-davydovych-yak-my-hovorymo_p031"]
    assert "Такого слова не було" in label["evidence"]
    assert compute_warning_severity(status, vesum_attested=False, headword="міроприємство") == "russianism_red"
    entry = {"lemma": "міроприємство", "heritage_status": status}
    assert classification_code(entry) == "rus"
    assert classification_code({**entry, "primary_source": "surzhyk_to_avoid"}) == "avoid"


@pytest.mark.parametrize(
    ("headword", "record", "reason"),
    [
        # Actual stored DB evidence names the Russian etymon and the replacement only.
        (
            "міроприємство",
            {"kind": "lexical", "source": ["antonenko-p044"], "evidence": [_MIRO_STORED_EVIDENCE]},
            "no_headword_bound_evidence",
        ),
        # D01: a translation drill about «следующий» does not bind «слідуючий».
        (
            "слідуючий",
            {"kind": "lexical", "source": ["voron-9", "zabolotnyi-5"], "evidence": [_SLID_STORED_EVIDENCE]},
            "no_headword_bound_evidence",
        ),
        # D05: unrecognised kind, null evidence, bare citations, wrong source, wrong headword.
        ("слово", {"kind": "unspecified", "source": ["antonenko-p001"]}, "curated_kind_without_scope"),
        (
            "слово",
            {"kind": "participle", "evidence": ["antonenko-p001: слово тут ужито неправильно"]},
            "curated_kind_without_scope",
        ),
        ("слово", {"kind": "lexical", "source": ["antonenko-p001"], "evidence": None}, "no_headword_bound_evidence"),
        (
            "бажаючий",
            {"kind": "lexical", "evidence": ["antonenko:Бажаючий", "antonenko:153 Крокувати, простувати, іти"]},
            "no_headword_bound_evidence",
        ),
        (
            "бажаючий",
            {"kind": "lexical", "evidence": ["ua-gec-annotation: тут слово бажаючий виправлено на охочий"]},
            "no_headword_bound_evidence",
        ),
        ("бажаний", {"kind": "lexical", "evidence": [_BAZH_EVIDENCE]}, "no_headword_bound_evidence"),
        (None, {"kind": "lexical", "evidence": [_BAZH_EVIDENCE]}, "no_headword_bound_evidence"),
    ],
)
def test_curated_record_without_headword_bound_evidence_is_unresolved(headword, record, reason) -> None:
    status = {"classification": "russianism", "is_russianism": True, "curated_calque": record}
    label = resolve_usage_label(status, headword=headword)
    assert label == {"code": None, "scope": "unresolved", "authority": [], "evidence": None, "reason": reason}
    assert compute_warning_severity(status, vesum_attested=False, headword=headword) == "none"
    entry = {"lemma": headword, "primary_source": "surzhyk_to_avoid", "heritage_status": status}
    assert classification_code(entry) is None


def test_actual_db_avoid_row_without_bound_evidence_gets_no_browse_code() -> None:
    """D01: «діюча» has only avoid provenance and a Russian shadow."""
    status = {
        "classification": "unknown",
        "attestations": [],
        "is_russianism": False,
        "russian_shadow": True,
        "vesum_attested": False,
        "calque_warning": None,
        "warning_severity": "russianism_red",
    }
    entry = {"lemma": "діюча", "primary_source": "surzhyk_to_avoid", "heritage_status": status}
    assert classification_code(entry) is None


def test_phrasal_calque_and_unattested_curated_record() -> None:
    phrase = {"classification": "unknown", "calque_warning": {"kind": "phrasal", "citations": ["antonenko-p091"]}}
    assert resolve_usage_label(phrase)["scope"] == "phrase"
    assert resolve_usage_label(phrase)["authority"] == []
    bare = {"classification": "calque", "curated_calque": {"kind": "lexical", "corrections": ["x"]}}
    assert resolve_usage_label(bare, headword="слово")["reason"] == "no_headword_bound_evidence"
    assert resolve_usage_label({})["scope"] == "none"
    assert resolve_usage_label(None)["scope"] == "none"


def test_scope_helpers() -> None:
    assert card_headword_matches(_SUM20_VOZNYI, "возний")
    assert not card_headword_matches(_SUM20_VOZNYI, "живий")
    assert card_headword_matches(_SUM20_ATTACHED_HOMONYM, "диван")
    assert card_headword_matches(_VTS_KRYN, "крин")
    assert card_headword_matches("БРА́ТИ УЧА́СТЬ, у чому. Бути учасником.", "брати участь")
    assert not card_headword_matches("garbage діал.", "слово")
    assert not card_headword_matches(_SUM20_VOZNYI, None)
    assert modern_headword_labels(_SUM20_ATTACHED_HOMONYM) == ({"historism"}, True)

    assert names_headword(_MIRO_SUPPORT["passage"], "міроприємство")
    assert not names_headword(_SLID_STORED_EVIDENCE, "слідуючий")
    assert names_headword("Вид — це не тип.", "вид")
    assert not names_headword("Види бувають різні.", "вид")
    assert names_headword("Тут треба брати участь у грі.", "брати участь")
    assert not names_headword("Тут треба брати у грі участь.", "брати участь")
    assert not names_headword("будь-що", None)

    assert is_normative_locator("antonenko-davydovych-yak-my-hovorymo_p031")
    assert is_normative_locator("Антоненко-Давидович")
    assert is_normative_locator("11-klas-ukrajinska-mova-avramenko-2019_s0074")
    assert not is_normative_locator("voron-9")
    assert not is_normative_locator("ua-gec")
    assert not is_normative_locator("5-klas-istoriya-hisem-2022_s0001")

    assert bound_evidence({"evidence": [_BAZH_EVIDENCE, _MIRO_STORED_EVIDENCE]}, "бажаючий") == [
        ("antonenko-davydovych-yak-my-hovorymo_p099", "Бажаючий – що (котрий, який) бажає – охочий")
    ]
    support = {"normativeSupport": [_MIRO_SUPPORT, {"locator": "", "passage": "x"}]}
    assert len(bound_evidence(support, "міроприємство")) == 1
    assert bound_evidence({}, "слово") == []

    assert shares_referent("нижча верхівка княжої дружини", _HRYD_GLOSS)
    assert not shares_referent("нижча верхівка княжої дружини", "sofa")
    assert not shares_referent("у на до", "у на до")

    glazova = {"locator": "11-klas-ukrajinska-mova-glazova-2019_s0263", "passage": "міроприємство — захід"}
    assert support_passages({"normativeSupport": [_MIRO_SUPPORT, {"locator": "x"}], "currentNormSupport": [glazova]}) == [
        _MIRO_SUPPORT,
        glazova,
    ]


def test_curated_map_carries_evidence_and_pair_passages(monkeypatch, tmp_path) -> None:
    """Producer: excerpts reach the record; the stored ``participle`` kind still states no scope."""
    pairs = tmp_path / "heritage_pairs.yaml"
    pairs.write_text(
        "pairs:\n"
        "  - calqueLabel: бажаючий\n"
        "    kind: lexical\n"
        "    corrections: [охочий]\n"
        "    citations: ['antonenko:Бажаючий']\n"
        "    normativeSupport:\n"
        "      - locator: antonenko-davydovych-yak-my-hovorymo_p099\n"
        "        passage: 'висловити автори оголошення незграбним утвором бажаючий'\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(heritage_classifier, "HERITAGE_PAIRS_YAML", pairs)
    monkeypatch.setattr(heritage_classifier, "_CURATED_CALQUE_MAP", None)
    record = heritage_classifier._curated_calque_map()["бажаючий"]
    assert record["kind"] == "participle"
    assert record["evidence"]
    assert record["normative_support"][0]["locator"] == "antonenko-davydovych-yak-my-hovorymo_p099"
    warning = {"kind": record["kind"], "evidence": record["evidence"], "normative_support": record["normative_support"]}
    assert resolve_usage_label({"classification": "calque", "calque_warning": warning}, headword="бажаючий")["reason"] == (
        "curated_kind_without_scope"
    )
    lexical = {**warning, "kind": "lexical"}
    label = resolve_usage_label({"classification": "calque", "calque_warning": lexical}, headword="бажаючий")
    assert label["scope"] == "lemma"
    assert "antonenko-davydovych-yak-my-hovorymo_p099" in label["authority"]
    monkeypatch.setattr(heritage_classifier, "_CURATED_CALQUE_MAP", None)


def test_manifest_curated_record_carries_pair_passages(monkeypatch) -> None:
    """Producer (enrich_manifest): the stored record gets the excerpts that may bind it (#9603)."""
    from scripts.lexicon import enrich_manifest as em

    def pair(calque: str, passage: str) -> dict:
        return {
            "calque": calque,
            "kind": "lexical",
            "corrections": ["інше"],
            "note": "",
            "source": [f"antonenko:{calque}"],
            "evidence": [f"antonenko:{calque}"],
            "normative_support": [{"locator": "antonenko-fixture_p000", "passage": passage}],
        }

    participle = pair("бажаючий", "незграбним утвором бажаючий автори хотіли")
    lexical = pair("фіктивнослово", "слово фіктивнослово у мові вживати не слід")
    monkeypatch.setattr(
        em, "_HERITAGE_PAIRS_DATA_CACHE", ({"бажаючий": participle, "фіктивнослово": lexical}, {}, {})
    )
    monkeypatch.setattr(
        em,
        "CURATED_CALQUES",
        {"бажаючий": {"corrections": ["охочий"], "note": "усі бажаючі → усі охочі", "source": ["antonenko-p099"]}},
    )
    # A calque_corrections row keeps its stored ``participle`` kind; passages travel with it.
    record = em._curated_calque("бажаючий", "бажаючий")
    assert record["kind"] == "participle"
    assert record["normative_support"] == participle["normative_support"]
    status = {"classification": "calque", "curated_calque": record}
    assert resolve_usage_label(status, headword="бажаючий")["reason"] == "curated_kind_without_scope"
    assert em._finalize_heritage_status(status, morphology=None, definition_cards=[], headword="бажаючий")[
        "warning_severity"
    ] == "none"

    # A heritage-pair lexical record binds through its passage, given the headword.
    record = em._curated_calque("фіктивнослово", "фіктивнослово")
    assert record["normative_support"] == lexical["normative_support"]
    status = {"classification": "calque", "curated_calque": record}
    assert em._finalize_heritage_status(status, morphology=None, definition_cards=[], headword="фіктивнослово")[
        "warning_severity"
    ] == "calque_yellow"
    assert em._finalize_heritage_status(status, morphology=None, definition_cards=[])["warning_severity"] == "none"


def test_classifier_stores_scope_from_headword_bound_excerpts() -> None:
    """Producer (classify_lemma): severity follows the excerpts carried into the record."""
    # Heritage-pair passage names «міроприємства»: a lemma-scoped calque.
    miro = classify_lemma("міроприємство", db_path=DB, vesum_db_path=VESUM_DB)
    assert miro["calque_warning"]["kind"] == "lexical"
    assert miro["calque_warning"]["normative_support"]
    assert miro["warning_severity"] == "calque_yellow"
    # The stored excerpt is about «следующий», not «слідуючий»: neutral.
    slid = classify_lemma("слідуючий", db_path=DB, vesum_db_path=VESUM_DB)
    assert slid["calque_warning"]["evidence"]
    assert slid["warning_severity"] == "none"
    # ``participle`` states no scope even with bound excerpts.
    bazh = classify_lemma("бажаючий", db_path=DB, vesum_db_path=VESUM_DB)
    assert bazh["calque_warning"]["kind"] == "participle"
    assert bazh["warning_severity"] == "none"


def test_esum_helpers_fail_closed() -> None:
    from scripts.lexicon.heritage_classifier import _esum_locator

    assert _esum_locator("гридь:1:592") == "ЕСУМ, т. 1, с. 592"
    assert _esum_locator("malformed") == "ЕСУМ"
    # A headword-slot marker of another class does not bind this classification.
    status = {"classification": "dialect", "attestations": [_ESUM_HRYD]}
    assert resolve_usage_label(status, headword="гридь", gloss=_HRYD_GLOSS)["code"] is None
