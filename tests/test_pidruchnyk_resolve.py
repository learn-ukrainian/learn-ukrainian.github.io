"""Tests for pidruchnyk textbook resolution in the publish step."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.v6_build import _build_pidruchnyk_section, _load_pidruchnyk_urls


def test_publish_helper_emits_one_pidruchnyk_bullet(tmp_path):
    mapping_path = tmp_path / "pidruchnyk_urls.yaml"
    mapping_path.write_text(
        yaml.safe_dump(
            {
                "7-klas-ukrmova-avramenko-2024": "https://pidruchnyk.com.ua/2876-ukrainska-mova-avramenko-7-klas-2024.html",
                "7-klas-ukrlit-avramenko-2024": "https://pidruchnyk.com.ua/2863-ukrainska-literatura-avramenko-7-klas-2024.html",
                "8-klas-ukrmova-zabolotnyi-2025": "https://pidruchnyk.com.ua/2902-ukrainska-mova-zabolotnyi-8-klas-2025.html",
            },
            allow_unicode=True,
            sort_keys=True,
        ),
        "utf-8",
    )
    pidruchnyk_urls = _load_pidruchnyk_urls(mapping_path)
    plan = {
        "references": [
            {"title": "Авраменко Grade 7, §12"},
            {"title": "Умовний Grade 7, §12"},
        ]
    }
    source_index = [
        {
            "source_file": "7-klas-ukrmova-avramenko-2024",
            "grade": 7,
            "year": 2024,
            "author": "авраменко",
            "subject": "Українська мова",
        },
        {
            "source_file": "7-klas-ukrlit-avramenko-2024",
            "grade": 7,
            "year": 2024,
            "author": "авраменко",
            "subject": "Українська література",
        },
        {
            "source_file": "7-klas-ukrmova-umovnyi-2024",
            "grade": 7,
            "year": 2024,
            "author": "умовний",
            "subject": "Українська мова",
        },
    ]

    section = _build_pidruchnyk_section(plan, pidruchnyk_urls, source_index)

    assert section.count("- [") == 1
    assert "2876-ukrainska-mova-avramenko-7-klas-2024.html" in section


def test_unknown_refs_are_silently_dropped():
    plan = {
        "references": [
            {"title": "Невідомий Grade 6, §10"},
        ]
    }
    pidruchnyk_urls = {
        "6-klas-ukrmova-avramenko-2023": "https://pidruchnyk.com.ua/2592-ukrmova-6-klas-avramenko.html",
    }
    source_index = [
        {
            "source_file": "6-klas-ukrmova-avramenko-2023",
            "grade": 6,
            "year": 2023,
            "author": "авраменко",
            "subject": "Українська мова",
        }
    ]

    section = _build_pidruchnyk_section(plan, pidruchnyk_urls, source_index)

    assert section == ""


def test_missing_yaml_entry_does_not_emit_na_or_broken_link():
    plan = {
        "references": [
            {"title": "Авраменко Grade 7, §12"},
        ]
    }
    pidruchnyk_urls: dict[str, str] = {}
    source_index = [
        {
            "source_file": "7-klas-ukrmova-avramenko-2024",
            "grade": 7,
            "year": 2024,
            "author": "авраменко",
            "subject": "Українська мова",
        }
    ]

    section = _build_pidruchnyk_section(plan, pidruchnyk_urls, source_index)

    assert section == ""
    assert "N/A" not in section
    assert "http" not in section
