"""Tests for BIO wiki subject and VERIFY-marker gates."""

from __future__ import annotations

import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from validate.check_wiki_subject import check_wiki_file
from validate.check_wiki_verify_markers import find_verify_markers_text


def _write_wiki(tmp_path, slug: str, h1: str, meta_slug: str | None = None):
    path = tmp_path / f"{slug}.md"
    path.write_text(
        f"# {h1}\n\n"
        "<!-- wiki-meta\n"
        f"slug: {meta_slug or slug}\n"
        "domain: figures\n"
        "-->\n\n"
        "## Короткий зміст\n"
        "Текст статті.\n",
        encoding="utf-8",
    )
    return path


def test_wiki_subject_flags_h1_for_different_figure(tmp_path):
    path = _write_wiki(
        tmp_path,
        "anatol-petrytskyi",
        "Микола Куліш: Драматургія мовного вибору",
        meta_slug="anatol-petrytskyi",
    )

    finding = check_wiki_file(path, plan_title="Анатоль Петрицький: Сценограф")

    assert finding is not None
    assert finding.file_slug == "anatol-petrytskyi"
    assert finding.frontmatter_slug == "anatol-petrytskyi"
    assert "Микола Куліш" in finding.h1


def test_wiki_subject_accepts_panteleimon_kulish_not_mykola_false_positive(tmp_path):
    path = _write_wiki(
        tmp_path,
        "panteleimon-kulish",
        "Біографія: Пантелеймон Куліш: Європеєць на хуторі",
    )

    assert check_wiki_file(path, plan_title="Пантелеймон Куліш: Європеєць на хуторі") is None


def test_wiki_subject_accepts_geo_shkurupii_g_letter_variant(tmp_path):
    # Canonical H1 uses the restored letter ґ («Ґео»); the plan title carries
    # the Soviet-orthography г («Гео»). Same person — must NOT be flagged.
    path = _write_wiki(
        tmp_path,
        "heo-shkurupii",
        "Ґео Шкурупій: «Король Футуропрерій» Розстріляного відродження",
    )

    assert check_wiki_file(
        path, plan_title="Гео Шкурупій: Король футуропрерій та доля футуриста"
    ) is None


def test_wiki_subject_verify_marker_gate_flags_survivor():
    findings = find_verify_markers_text("Текст <!-- VERIFY: дата -->\nVERIFY: джерело")

    assert len(findings) == 2
    assert findings[0].line == 1
    assert findings[1].line == 2
