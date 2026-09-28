"""Tests for vocab → Word Atlas cross-linking (render-time, integrity-gated).

Covers the normalize/match helper and its integrity-gating in the live
``vocab_items_to_components`` generator path: a link is emitted iff the lemma
has an Atlas page, never otherwise.
"""

from __future__ import annotations

import json

import pytest

from scripts.generate_mdx import atlas_links, resources
from scripts.generate_mdx.atlas_links import (
    atlas_href_for,
    english_content_words,
    lesson_word_is_proper,
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
    # Reset global state for test reliability
    atlas_links._warned_manifest_unavailable = False
    atlas_links._load_manifest_tables.cache_clear()

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
    def fake_href(word, **_sense):
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


# ── sense check (#9002) ──────────────────────────────────────────────────────

def _entry(lemma, slug, *, gloss="", pos="noun", en=None):
    entry = {"lemma": lemma, "url_slug": slug, "gloss": gloss, "pos": pos}
    if en is not None:
        entry["enrichment"] = {"translation": {"en": en, "source": "dmklinger"}}
    return entry


@pytest.fixture
def sense_atlas(tmp_path, monkeypatch):
    """Atlas fixture shaped like the published entries #9002 reviewed."""
    monkeypatch.setattr(atlas_links, "_vesum_has_proper_reading", lambda form: False)
    manifest = _write_json(
        tmp_path / "manifest.json",
        {
            "entries": [
                # Common nouns: Ukrainian gloss, English senses from dmklinger.
                _entry("поділля", "поділля", gloss="Низовинна місцевість; долина.",
                       en=["(colloquial) lowland, valley"]),
                _entry("реєстр", "реєстр", gloss="Список, письмовий перелік.",
                       en=["inventory (detailed list of all of the items on hand)"]),
                _entry("робота", "робота", gloss="work"),
                _entry("хто", "хто", pos="pronoun", en=["who", "who"]),
                _entry("бабусин", "бабусин", pos="adjective", gloss="Належний бабусі."),
                # Mixed-script senses as the published learner gloss and
                # dmklinger rows carry them (review cf-9002-r1-codex).
                _entry("належати", "належати", pos="verb",
                       gloss="to belong; should (impersonal) Conjugation: 2nd (-ать) | ―",
                       en=["to belong; should (impersonal)   Conjugation: 2nd (-ать) | ―",
                           "to belong (+ до, + genitive) (be a part or member of)"]),
                _entry("мусити", "мусити", pos="verb", gloss="to have to; must",
                       en=["to have to, must   Conjugation: 2nd (-ять) | ―", "must (be required to)"]),
                _entry("вона", "вона", pos="pronoun", en=["she"]),
                _entry("їсти", "їсти", pos="verb", en=["to eat"]),
                _entry("друг", "друг", en=["friend (person whose company one enjoys)"]),
                _entry("жнець", "жнець", gloss="Той, хто жне хлібні рослини.", en=["reaper (person who reaps)"]),
                _entry("жниця", "жниця", gloss="Жін. до жнець.", en=["female equivalent of жнець: female reaper"]),
                _entry("голово", "голово", gloss="chair, head (vocative)"),
                # Proper-noun articles.
                _entry("Київ", "київ", pos="proper noun",
                       en=["Kyiv (capital city of Ukraine) (proper noun)"]),
                _entry("Андрій", "андрій", gloss="Andrii", pos="proper noun",
                       en=["a male given name, Andriy, equivalent to English Andrew (proper noun)"]),
                _entry("Олена", "олена", pos="proper noun",
                       en=["Helen (female given name) (proper noun)", "Olena (female given name) (proper noun)"]),
                _entry("Карпати", "карпати", pos="proper noun:pl",
                       en=["Carpathians (mountainous system in Central Europe) (proper noun)"]),
            ]
        },
    )
    aliases = _write_json(
        tmp_path / "aliases.json",
        [
            {"a": "олену", "s": "олена"},
            {"a": "мусить", "s": "мусити"},
            {"a": "кого", "s": "хто"},
            {"a": "їй", "s": "вона"},
            # «їм» is both 'to them' (вона/вони) and 'I eat' (їсти); the alias file picks їсти.
            {"a": "їм", "s": "їсти"},
            {"a": "друга", "s": "друг"},
        ],
    )
    published = {
        "поділля", "реєстр", "робота", "хто", "бабусин", "київ", "андрій", "олена", "карпати",
        "належати", "мусити", "вона", "їсти", "друг", "жнець", "жниця", "голово",
    }

    def href(word, **sense):
        return atlas_href_for(word, manifest, aliases_path=aliases, published_slugs=published, **sense)

    return href


# The six links GPT-6 Sol verified wrong on #8950 (issue #9002), with the
# lesson card fields exactly as committed.
_WRONG_SENSE_CARDS = [
    ("folk/narodni-tantsi", "Поділля", "Podilia", "власна назва",
     "Поділля в описах козачка пов'язане з жвавою парною драматургією."),
    ("folk/pysankarstvo", "Поділля", "Podilia", "власна назва",
     "Поділля часто пояснюють через геометричну виразність писанки."),
    ("b2/advanced-conjunctions-ii", "реєстр", "register", "noun",
     "Реєстр визначає, чи пасує бо, оскільки або незважаючи на те що."),
    ("b2/active-participles-past", "реєстр", "register", "noun",
     "Реєстр визначає, чи звучить форма доречно."),
    ("b2/advanced-conjunctions-i", "реєстр", "register", "noun",
     "Реєстр визначає, чи доречна емоційна повторюваність."),
    ("b2/b2-final-exam", "реєстр", "register", "noun",
     "Реєстр має відповідати ситуації, адресатові і жанру."),
]


@pytest.mark.parametrize(
    "lesson, word, translation, pos, example",
    _WRONG_SENSE_CARDS,
    ids=[card[0] for card in _WRONG_SENSE_CARDS],
)
def test_wrong_sense_links_from_9002_are_dropped(sense_atlas, lesson, word, translation, pos, example):
    # Without the lesson's sense the spelling still resolves — the old bug.
    assert sense_atlas(word) is not None
    assert sense_atlas(word, translation=translation, pos=pos, example=example) is None


@pytest.mark.parametrize(
    "word, translation, pos, expected",
    [
        ("робота", "work", "noun", "/lexicon/робота/"),
        ("робо́та", "hard work; job", "noun", "/lexicon/робота/"),
        ("хто", "who", "pronoun", "/lexicon/хто/"),
        ("Київ", "Kyiv", "proper noun", "/lexicon/київ/"),
        # The article's English gloss carries the lesson romanisation.
        ("Андрій", "Andrii", "proper noun", "/lexicon/андрій/"),
        # An inflected proper noun still reaches its proper-noun lemma.
        ("Олену", "Olena (object form)", "proper noun", "/lexicon/олена/"),
        # Plural folding: "Carpathians" matches "the Carpathians".
        ("Карпати", "the Carpathians", "proper noun", "/lexicon/карпати/"),
    ],
)
def test_correct_links_survive_the_sense_check(sense_atlas, word, translation, pos, expected):
    assert sense_atlas(word, translation=translation, pos=pos) == expected


def test_english_translation_without_shared_word_drops_link(sense_atlas):
    assert sense_atlas("робота", translation="employment", pos="noun") is None


def test_article_without_english_sense_cannot_confirm_meaning(sense_atlas):
    assert sense_atlas("бабусин", translation="grandmother's", pos="adjective") is None
    # No translation to check against: only the proper-noun rule applies.
    assert sense_atlas("бабусин") == "/lexicon/бабусин/"


def test_non_english_translation_is_not_sense_checked(sense_atlas):
    assert sense_atlas("реєстр", translation="список, перелік", pos="іменник") == "/lexicon/реєстр/"


def test_proper_noun_from_mid_sentence_capital(sense_atlas, monkeypatch):
    # No proper-noun pos label and a lowercase headword: the example's
    # mid-sentence capital, confirmed by a VESUM proper-name reading, decides.
    monkeypatch.setattr(atlas_links, "_vesum_has_proper_reading", lambda form: form == "Поділля")
    example = "Вишивка з Поділля має свої кольори."
    assert lesson_word_is_proper("поділля", "noun", example)
    assert sense_atlas("поділля", pos="noun", example=example) is None


def test_capitalised_title_in_formal_address_is_not_a_proper_noun(sense_atlas):
    # b1/vocative-formal: formal address capitalises the title. VESUM has no
    # proper-name reading for «Голово», so the correct-sense link stays.
    card = {"translation": "chair, head (vocative)", "pos": "vocative", "example": "Шановна пані Голово!"}
    assert not lesson_word_is_proper("голово", card["pos"], card["example"])
    assert sense_atlas("голово", **card) == "/lexicon/голово/"


def test_sentence_start_capital_is_not_a_proper_noun(sense_atlas):
    example = "Поділля — це низовина біля річки."
    assert not lesson_word_is_proper("поділля", "noun", example)
    assert sense_atlas("поділля", pos="noun", example=example) == "/lexicon/поділля/"


def test_proper_noun_from_vesum_prop_tag(sense_atlas, monkeypatch):
    monkeypatch.setattr(atlas_links, "_vesum_has_proper_reading", lambda form: form == "Поділля")
    assert sense_atlas("Поділля") is None
    # Lowercase headword is not looked up as a name.
    assert sense_atlas("поділля") == "/lexicon/поділля/"


@pytest.mark.parametrize(
    "translation",
    ["language register (мовний реєстр)", "мовний реєстр (language register)", "register, мовний реєстр"],
)
def test_mixed_script_translation_is_sense_checked(sense_atlas, translation):
    # Review cf-9002-r1-codex: a Ukrainian note in the translation used to
    # skip the check, so «реєстр» 'language register' linked to 'inventory'.
    assert sense_atlas("реєстр", translation=translation, pos="noun") is None


@pytest.mark.parametrize(
    "word, translation, pos, expected",
    [
        # Review cf-9002-r1-codex: the article's English sense sits beside a
        # Ukrainian note ("Conjugation: 2nd (-ать)", "(+ до, + genitive)").
        ("належати", "to belong", "verb", "/lexicon/належати/"),
        # Inflected lesson forms reach their lemma's article: "has" ~ "have".
        ("мусить", "he/she has to", "verb form", "/lexicon/мусити/"),
        ("кого", "whom", "pronoun", "/lexicon/хто/"),
        ("їй", "to her", "pron", "/lexicon/вона/"),
        ("жниця", "female harvester", "noun", "/lexicon/жниця/"),
    ],
)
def test_correct_sense_links_behind_mixed_script_or_inflection_survive(sense_atlas, word, translation, pos, expected):
    assert sense_atlas(word, translation=translation, pos=pos) == expected


@pytest.mark.parametrize(
    "word, translation",
    [
        # Homonymous inflected forms whose alias picks another lemma.
        ("їм", "to them"),
        ("друга", "second (feminine)"),
    ],
)
def test_wrong_sense_inflected_forms_stay_unlinked(sense_atlas, word, translation):
    assert sense_atlas(word) is not None
    assert sense_atlas(word, translation=translation) is None


def test_preset_href_is_sense_checked_against_the_lesson_word(sense_atlas):
    # The pre-set slug is lowercase; the lesson's capitalised proper noun decides.
    assert sense_atlas("поділля", lesson_word="Поділля", pos="власна назва") is None


@pytest.mark.parametrize(
    "text, expected",
    [
        ("(colloquial) lowland, valley", {"colloquial", "lowland", "valley"}),
        ("Kyiv (capital city of Ukraine) (proper noun)", {"kyiv", "capital", "city", "ukraine"}),
        ("to the student", {"student"}),
        ("to", {"to"}),
        ("studies", {"study"}),
        ("boxes", {"box"}),
        ("grandmother's", {"grandmother"}),
        ("tomatoes", {"tomatoe", "tomato"}),
        ("he/she has to", {"he", "she", "have"}),
        ("these, whom", {"this", "who"}),
        ("lived", {"lived", "liv", "live"}),
        ("shopping", {"shopping", "shopp", "shoppe", "shop"}),
        ("city centre, colour", {"city", "center", "color"}),
        ("characterisation", {"characterization"}),
        ("gone grey", {"gone", "gray"}),
        # Only the English portion of a mixed-script gloss counts.
        ("language register (мовний реєстр)", {"language", "register"}),
        ("to belong; should (impersonal) Conjugation: 2nd (-ать) | ―", {"belong", "should", "impersonal"}),
        ("to belong (+ до, + genitive) (be a part or member of)", {"belong", "be", "part", "member"}),
        ("мовний реєстр", set()),
    ],
)
def test_english_content_words(text, expected):
    assert english_content_words(text) == expected


def test_vocab_component_passes_card_sense_to_resolver(monkeypatch):
    calls = []

    def fake_href(word, **sense):
        calls.append((word, sense))
        return None

    monkeypatch.setattr(resources, "atlas_href_for", fake_href)
    resources.vocab_items_to_components(
        [
            {"lemma": "реєстр", "translation": "register", "pos": "noun", "example": "Реєстр визначає."},
            {"lemma": "Поділля", "translation": "Podilia", "pos": "власна назва",
             "atlas_href": "/lexicon/поділля/"},
        ]
    )
    assert calls == [
        ("реєстр", {"translation": "register", "pos": "noun", "example": "Реєстр визначає.",
                    "lesson_word": "реєстр"}),
        ("поділля", {"translation": "Podilia", "pos": "власна назва", "example": "",
                     "lesson_word": "Поділля"}),
    ]
