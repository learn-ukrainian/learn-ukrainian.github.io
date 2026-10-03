import json
from pathlib import Path

import pytest

from scripts.audit.generate_search_index import classification_code
from scripts.lexicon.enrich_manifest import _SLOVNYK_CACHE_SCHEMA_VERSION
from scripts.lexicon.heritage_classifier import (
    _cached_slovnyk_hits,
    classify_lemma,
    classify_surface_form,
    compute_warning_severity,
    modern_headword_labels,
    normative_citations,
    resolve_usage_label,
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
        # #9603: ЕСУМ/Грінченко attestations are preserved, but their markers
        # may belong to a sense, cognate or quotation, so they never label the
        # headword by themselves. «глагол» keeps «калька» only through its
        # curated lexical record naming Антоненко-Давидович.
        assert classification_code({"primary_source": "built_vocabulary", "heritage_status": status}) == (
            "calq" if lemma == "глагол" else None
        )
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
        # Positive control: a curated lexical calque naming Антоненко-Давидович.
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
            "calque_yellow",
        ),
        # Positive control: a named lexical Russianism stays red.
        (
            {
                "classification": "russianism",
                "is_russianism": True,
                "attestations": [],
                "curated_calque": {**_NAMED_LEXICAL_CALQUE, "kind": "lexical"},
            },
            False,
            0,
            "russianism_red",
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
    """Pre-Soviet attestation or VESUM membership must not create false-positive green badges for convergence calques (#7982)."""
    # 1. Lexical calque with historical attestation: мисль -> думка
    mysl = classify_lemma("мисль", db_path=DB, vesum_db_path=VESUM_DB)
    assert mysl["classification"] == "calque"
    assert mysl["warning_severity"] == "calque_yellow"
    assert mysl["is_russianism"] is False
    assert mysl.get("calque_warning") is not None
    assert mysl["calque_warning"]["standard_alternatives"] == ["думка"]

    # Surface form must also inherit calque warning and yellow severity
    mysli = classify_surface_form("мислі", db_path=DB, vesum_db_path=VESUM_DB)
    assert mysli["classification"] == "calque"
    assert mysli["warning_severity"] == "calque_yellow"
    assert mysli.get("calque_warning") is not None
    assert mysli["calque_warning"]["standard_alternatives"] == ["думка"]

    # 2. Authentic archaism with calque warning: глагол -> дієслово, слово
    hlahol = classify_lemma("глагол", db_path=DB, vesum_db_path=VESUM_DB)
    assert hlahol["classification"] == "authentic-archaism"
    assert hlahol["warning_severity"] == "calque_yellow"
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
    assert label["authority"] == ["litvinova-7"]
    assert label["evidence"] == "approximately before a quantity"
    assert classification_code({"lemma": "біля", "heritage_status": status}) is None


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


@pytest.mark.parametrize(
    ("status", "cards", "expected_code", "expected_reason"),
    [
        # СУМ-20 headword label binds the historism.
        ({"classification": "historism"}, [_card("sum20", _SUM20_VOZNYI)], "hist", "lemma"),
        # The label belongs to sense 1 only (диван): no word-level label.
        ({"classification": "historism"}, [_card("sum20", _SUM20_DYVAN_SENSE)], None, "СУМ-20_headword_unlabelled"),
        # A homonym-indexed card cannot label one Atlas headword.
        ({"classification": "historism"}, [_card("sum20", _SUM20_HOMONYM)], None, "СУМ-20_headword_unlabelled"),
        # The modern dictionary has the headword unlabelled (город).
        ({"classification": "authentic-archaism"}, [_card("sum20", _SUM20_HOROD)], None, "СУМ-20_headword_unlabelled"),
        # ВТС is the modern fallback when СУМ-20 is absent.
        ({"classification": "authentic-archaism"}, [_card("vts", _VTS_KRYN)], "arch", "lemma"),
        # ЕСУМ cognate marker (або: «п. діал.») never labels the headword.
        (
            {
                "classification": "dialect",
                "attestations": [{"source": "esum", "ref": "або:1:37", "word": "або", "detail": "або «чи»; — п. діал. «елементарний»"}],
            },
            None,
            None,
            "no_modern_dictionary_label",
        ),
        # Грінченко quotation substring (хвіст.) never labels the headword.
        (
            {
                "classification": "historism",
                "attestations": [{"source": "grinchenko_1907", "ref": "1", "word": "зловити", "detail": "Зловив зайця за хвіст."}],
            },
            [_card("sum20", "ЗЛОВИ́ТИ, влю́, ви́ш, док. Схопити.")],
            None,
            "СУМ-20_headword_unlabelled",
        ),
        # Borrowing is an etymological claim: ЕСУМ on the headword binds it.
        (
            {
                "classification": "borrowing",
                "attestations": [{"source": "esum", "ref": "диван:2:63", "word": "диван", "detail": "диван «канапа» — запозичення з турецької"}],
            },
            None,
            "borr",
            "lemma",
        ),
        (
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
def test_treasured_labels_need_headword_bound_modern_evidence(status, cards, expected_code, expected_reason) -> None:
    headword = "диван" if status["classification"] == "borrowing" else "слово"
    label = resolve_usage_label(status, headword=headword, definition_cards=cards)
    assert label["code"] == expected_code
    assert label["reason"] == expected_reason
    if expected_code:
        assert label["scope"] == "lemma"
        assert label["authority"]


def test_bound_treasured_label_precedes_curated_russianism() -> None:
    status = {
        "classification": "authentic-archaism",
        "is_russianism": True,
        "curated_calque": {**_NAMED_LEXICAL_CALQUE, "kind": "lexical"},
    }
    assert resolve_usage_label(status, definition_cards=[_card("vts", _VTS_KRYN)])["code"] == "arch"
    # Unbound archaism does not hide a named lexical calque.
    assert resolve_usage_label(status)["code"] == "calq"


def test_curated_lexical_russianism_with_named_authority_is_retained() -> None:
    status = {
        "classification": "russianism",
        "is_russianism": True,
        "curated_calque": {
            "kind": "lexical",
            "corrections": ["захід"],
            "note": "рос. мероприятие; use захід / заходи",
            "source": ["antonenko-p044", "glazova-10"],
        },
    }
    label = resolve_usage_label(status, headword="міроприємство")
    assert label["code"] == "rus"
    assert label["scope"] == "lemma"
    assert label["authority"] == ["antonenko-p044", "glazova-10"]
    assert classification_code({"lemma": "міроприємство", "heritage_status": status}) == "rus"


def test_phrasal_calque_and_unattested_curated_record() -> None:
    phrase = {"classification": "unknown", "calque_warning": {"kind": "phrasal", "citations": ["antonenko-p091"]}}
    assert resolve_usage_label(phrase)["scope"] == "phrase"
    bare = {"classification": "calque", "curated_calque": {"kind": "lexical", "corrections": ["x"]}}
    assert resolve_usage_label(bare)["reason"] == "curated_record_without_named_authority"
    assert resolve_usage_label({})["scope"] == "none"
    assert resolve_usage_label(None)["scope"] == "none"
