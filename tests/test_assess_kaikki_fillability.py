import json
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.lexicon.assess_kaikki_fillability import (
    is_clean_lemma,
    normalize_stress,
)


def test_normalize_stress():
    assert normalize_stress("абе́тка") == "абетка"
    assert normalize_stress("ба́тько") == "батько"
    assert normalize_stress("собака") == "собака"
    assert normalize_stress("") == ""


def test_is_clean_lemma():
    assert is_clean_lemma("собака") is True
    assert is_clean_lemma("кіт") is True
    assert is_clean_lemma("добрий день") is False  # whitespace
    assert is_clean_lemma("як справи?") is False  # ends in ?
    assert is_clean_lemma("він/вона") is False  # contains /
    assert is_clean_lemma("-ам") is False  # suffix affix (leading hyphen)
    assert is_clean_lemma("пра-") is False  # prefix affix (trailing hyphen)
    assert is_clean_lemma("будь-який") is True  # internal hyphen is a real lemma
    assert is_clean_lemma("жовто-блакитний") is True  # internal hyphen is a real lemma


def test_assess_kaikki_fillability_cli(tmp_path: Path):
    # Create a mock vocabulary.yaml
    vocab_dir = tmp_path / "curriculum/l2-uk-en/a1/hello"
    vocab_dir.mkdir(parents=True, exist_ok=True)
    vocab_file = vocab_dir / "vocabulary.yaml"

    vocab_data = [
        {"word": "соба́ка", "pos": "noun"},  # Clean, has stress
        {"word": "кіт", "pos": "noun"},      # Clean, no stress
        {"word": "добрий день", "pos": "phrase"}, # Unclean (whitespace)
        {"word": "як справи?", "pos": "phrase"},  # Unclean (ends in ?)
        {"word": "він/вона", "pos": "pronoun"}    # Unclean (contains /)
    ]
    with open(vocab_file, "w", encoding="utf-8") as f:
        yaml.dump(vocab_data, f)

    # Create a mock kaikki-uk.jsonl
    kaikki_file = tmp_path / "kaikki-uk.jsonl"
    kaikki_lines = [
        # собака - has gloss, etymology, example, ipa, stress
        {
            "word": "собака",
            "lang_code": "uk",
            "pos": "noun",
            "etymology_text": "Inherited from Proto-Slavic...",
            "sounds": [{"ipa": "[sɔˈbakɐ]"}],
            "head_templates": [{"name": "uk-noun", "args": {"1": "соба́ка"}}],
            "senses": [
                {
                    "glosses": ["dog"],
                    "examples": [{"text": "Гарний собака."}]
                }
            ]
        },
        # кіт - has gloss, ipa, but no etymology, no example
        {
            "word": "кіт",
            "lang_code": "uk",
            "pos": "noun",
            "sounds": [{"ipa": "[kʲit]"}],
            "senses": [
                {
                    "glosses": ["cat"]
                }
            ]
        }
    ]
    with open(kaikki_file, "w", encoding="utf-8") as f:
        for item in kaikki_lines:
            f.write(json.dumps(item) + "\n")

    # Create a mock manifest
    manifest_file = tmp_path / "lexicon-manifest.json"
    manifest_data = {
        "version": "0.1",
        "entries": [
            {
                "lemma": "кіт",
                "ipa": "[kʲit]",
                "enrichment": {
                    "meaning": {
                        "definitions": ["domestic cat"]
                    }
                }
            }
        ]
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    report_file = tmp_path / "report.md"

    # Run the script
    script_path = Path(__file__).parent.parent / "scripts/lexicon/assess_kaikki_fillability.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--kaikki", str(kaikki_file),
        "--vocab-glob", str(tmp_path / "curriculum/l2-uk-en/*/*/vocabulary.yaml"),
        "--manifest", str(manifest_file),
        "--out", str(report_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Assert stdout output
    assert "Raw Union Count (N): 5" in result.stdout
    assert "Clean Lemmas Count (M): 2" in result.stdout
    assert "Present: 2/2" in result.stdout
    assert "Has Gloss: 2/2" in result.stdout
    assert "Has Etymology: 1/2" in result.stdout
    assert "Has Example: 1/2" in result.stdout
    assert "Has IPA: 2/2" in result.stdout

    # Assert net add stdout output
    assert "Gloss: lacking 1, gaining 1" in result.stdout
    assert "Etymology: lacking 2, gaining 1" in result.stdout
    assert "Examples: lacking 2, gaining 1" in result.stdout
    assert "IPA: lacking 1, gaining 1" in result.stdout
    assert "Stress: lacking 2, gaining 1" in result.stdout

    # Assert report file exists and has content
    assert report_file.exists()
    report_text = report_file.read_text(encoding="utf-8")
    assert "## Kaikki Coverage over Clean Lemmas" in report_text
    assert "соба́ка" in report_text
    assert "кіт" in report_text
