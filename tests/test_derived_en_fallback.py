from scripts.lexicon.derived_en_fallback import (
    derived_base_candidates,
    derived_translation_fallback,
    manifest_lemma_index,
)


def _base_entry(lemma: str, en: list[str] | None, source: str = "slovnyk.me: fixture") -> dict:
    entry: dict = {"lemma": lemma, "pos": "noun"}
    if en is not None:
        entry["enrichment"] = {"translation": {"en": en, "source": source}}
    return entry


def _index(*entries: dict) -> dict:
    return manifest_lemma_index({"entries": list(entries)})


def test_candidates_cover_diminutive_and_augmentative_examples() -> None:
    diminutive_bases = {row["base"] for row in derived_base_candidates("білочка")}
    assert "білка" in diminutive_bases
    assert all(row["kind"] == "diminutive" for row in derived_base_candidates("білочка"))

    augmentative_rows = derived_base_candidates("вовчище")
    assert all(row["kind"] == "augmentative" for row in augmentative_rows)
    assert "вовк" in {row["base"] for row in augmentative_rows}


def test_diminutive_fill_from_manifest_base() -> None:
    index = _index(_base_entry("білка", ["squirrel"]))

    translation = derived_translation_fallback(
        {"lemma": "білочка", "pos": "noun"},
        index,
        vesum_verify=False,
    )

    assert translation == {
        "en": ["squirrel (diminutive)"],
        "source": "slovnyk.me: fixture (diminutive of білка)",
    }


def test_augmentative_fill_from_manifest_base() -> None:
    index = _index(_base_entry("вовк", ["wolf"]))

    translation = derived_translation_fallback(
        {"lemma": "вовчище", "pos": "noun"},
        index,
        vesum_verify=False,
    )

    assert translation == {
        "en": ["wolf (augmentative)"],
        "source": "slovnyk.me: fixture (augmentative of вовк)",
    }


def test_no_fill_when_base_lacks_en() -> None:
    index = _index(
        _base_entry("білка", None),
        _base_entry("вовк", []),
        _base_entry("ведмідь", ["bear"], source=""),
    )

    assert derived_translation_fallback({"lemma": "білочка", "pos": "noun"}, index, vesum_verify=False) is None
    assert derived_translation_fallback({"lemma": "вовчище", "pos": "noun"}, index, vesum_verify=False) is None
    assert derived_translation_fallback({"lemma": "ведмедище", "pos": "noun"}, index, vesum_verify=False) is None


def test_no_fill_when_base_missing_or_not_noun() -> None:
    index = _index(
        {"lemma": "білка", "pos": "adjective", "enrichment": {"translation": {"en": ["white"], "source": "fixture"}}}
    )

    assert derived_translation_fallback({"lemma": "білочка", "pos": "noun"}, index, vesum_verify=False) is None
    assert derived_translation_fallback({"lemma": "вовчище", "pos": "noun"}, index, vesum_verify=False) is None
    assert derived_translation_fallback({"lemma": "білочка", "pos": "adjective"}, index, vesum_verify=False) is None


def test_vesum_gate_blocks_unattested_forms() -> None:
    index = _index(_base_entry("білка", ["squirrel"]))

    def attest_all(word: str, pos_filter: str | None) -> list[dict]:
        return [{"lemma": word, "pos": pos_filter or "noun", "tags": ""}]

    def reject_surface(word: str, pos_filter: str | None) -> list[dict]:
        if pos_filter is None:
            return []
        return [{"lemma": word, "pos": "noun", "tags": ""}]

    assert derived_translation_fallback({"lemma": "білочка", "pos": "noun"}, index, vesum_verify=attest_all) is not None
    assert derived_translation_fallback({"lemma": "білочка", "pos": "noun"}, index, vesum_verify=reject_surface) is None


def test_manifest_lemma_index_normalizes_stress_and_case() -> None:
    index = _index(_base_entry("Бі́лка", ["squirrel"]))

    translation = derived_translation_fallback(
        {"lemma": "біло́чка", "pos": "noun"},
        index,
        vesum_verify=False,
    )

    assert translation is not None
    assert translation["en"] == ["squirrel (diminutive)"]
