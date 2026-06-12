import json
from pathlib import Path

from scripts.lexicon.build_kaikki_lookup import build_lookup, lookup_key


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_lookup_key_strips_stress_and_lowercases() -> None:
    assert lookup_key("А́втобус") == "автобус"


def test_build_lookup_aggregates_ipa_etymology_and_pos(tmp_path: Path) -> None:
    raw = tmp_path / "kaikki-uk.jsonl"
    _write_jsonl(
        raw,
        [
            {
                "word": "соба́ка",
                "lang_code": "uk",
                "pos": "noun",
                "etymology_text": "Inherited from Proto-Slavic.",
                "sounds": [{"ipa": "[sɔˈbakɐ]"}],
                "senses": [{"glosses": ["dog"]}],
            },
            {
                "word": "собака",
                "lang_code": "uk",
                "pos": "noun",
                "etymology_text": "Borrowed note from a second line.",
                "sounds": [{"ipa": "[soˈbɑkɐ]"}, {"ipa": "[sɔˈbakɐ]"}],
                "senses": [{"glosses": []}],
            },
            {
                "word": "добрий день",
                "lang_code": "uk",
                "pos": "phrase",
                "sounds": [{"ipa": "[ˈdɔbrɪj dɛnʲ]"}],
            },
            {
                "word": "кіт",
                "lang_code": "en",
                "pos": "noun",
                "sounds": [{"ipa": "[kʲit]"}],
            },
        ],
    )

    lookup = build_lookup(raw)

    assert list(lookup) == ["собака"]
    assert lookup["собака"]["ipa"] == ["[sɔˈbakɐ]", "[soˈbɑkɐ]"]
    assert lookup["собака"]["pos"] == ["noun"]
    assert lookup["собака"]["etymology_text"] == (
        "Inherited from Proto-Slavic.\n\nBorrowed note from a second line."
    )
