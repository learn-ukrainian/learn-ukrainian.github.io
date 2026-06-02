"""Tests for scripts/validate/check_discovery_integrity.py."""

from __future__ import annotations

import os
import sys

import yaml

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from validate.check_discovery_integrity import check_discovery_file


def _write_discovery(tmp_path, slug: str, topic: str):
    path = tmp_path / f"{slug}.yaml"
    path.write_text(
        yaml.safe_dump({"query_keywords": [topic]}, allow_unicode=True),
        encoding="utf-8",
    )
    return path


def test_discovery_integrity_flags_different_figure_topic(tmp_path):
    path = _write_discovery(tmp_path, "anatol-petrytskyi", "Микола Куліш: Драматургія")

    finding = check_discovery_file(path, plan_title="Анатоль Петрицький: Сценограф")

    assert finding is not None
    assert finding.slug == "anatol-petrytskyi"
    assert finding.topic == "Микола Куліш: Драматургія"
    assert finding.plan_title == "Анатоль Петрицький: Сценограф"


def test_discovery_integrity_accepts_matching_figure_topic(tmp_path):
    path = _write_discovery(tmp_path, "ivan-mazepa", "Іван Мазепа: Анатомія вибору")

    assert check_discovery_file(path, plan_title="Іван Мазепа: Анатомія вибору") is None
