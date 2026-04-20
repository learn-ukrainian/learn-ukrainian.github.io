from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki import query_builder


def _write_fixture(tmp_path: Path, *, track: str = "a1", slug: str = "demo", query_keywords: list[str], objectives: list[str]) -> Path:
    curriculum_dir = tmp_path / "curriculum" / "l2-uk-en"
    discovery_dir = curriculum_dir / track / "discovery"
    plans_dir = curriculum_dir / "plans" / track
    discovery_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)

    discovery_path = discovery_dir / f"{slug}.yaml"
    discovery_path.write_text(
        yaml.safe_dump({"query_keywords": query_keywords}, allow_unicode=True),
        encoding="utf-8",
    )
    (plans_dir / f"{slug}.yaml").write_text(
        yaml.safe_dump({"objectives": objectives}, allow_unicode=True),
        encoding="utf-8",
    )
    return discovery_path


def test_build_query_buckets_keeps_ukrainian_phrases_and_objective_tokens(tmp_path, monkeypatch):
    discovery_path = _write_fixture(
        tmp_path,
        query_keywords=[
            "Звуки і літери",
            "Голосні звуки",
            "Sounds and Letters",
        ],
        objectives=[
            "Розрізняти звуки й букви та чути наголос у слові",
        ],
    )
    monkeypatch.setattr(query_builder, "CURRICULUM_DIR", tmp_path / "curriculum" / "l2-uk-en")

    bucket_a, bucket_b = query_builder.build_query_buckets(discovery_path, "a1")

    assert '"звуки і літери"' in bucket_a
    assert '"голосні звуки"' in bucket_a
    assert "наголос" in bucket_b
    assert "розрізняти" in bucket_b
    assert "sounds" not in bucket_b


def test_build_query_buckets_normalizes_apostrophes_without_dropping_tokens(tmp_path, monkeypatch):
    discovery_path = _write_fixture(
        tmp_path,
        query_keywords=["М'який знак і апостроф", "Пом’якшення приголосних"],
        objectives=["Пояснювати м’якість і роль апострофа"],
    )
    monkeypatch.setattr(query_builder, "CURRICULUM_DIR", tmp_path / "curriculum" / "l2-uk-en")

    bucket_a, bucket_b = query_builder.build_query_buckets(discovery_path, "a1")

    assert '"м\'який знак і апостроф"' in bucket_a
    assert "м'який" in bucket_b
    assert "апострофа" in bucket_b


def test_build_query_buckets_excludes_short_or_non_cyrillic_bucket_a_lines(tmp_path, monkeypatch):
    discovery_path = _write_fixture(
        tmp_path,
        query_keywords=["Привіт", "abc", "Hi there"],
        objectives=["Use hello politely"],
    )
    monkeypatch.setattr(query_builder, "CURRICULUM_DIR", tmp_path / "curriculum" / "l2-uk-en")

    bucket_a, bucket_b = query_builder.build_query_buckets(discovery_path, "a1")

    assert bucket_a == []
    assert bucket_b == {"привіт"}


def test_build_query_buckets_dedupes_phrase_variants_after_normalization(tmp_path, monkeypatch):
    discovery_path = _write_fixture(
        tmp_path,
        query_keywords=[
            "Букви і звуки мови",
            "Букви і звуки мови",
            "Букви і звуки   мови",
        ],
        objectives=[],
    )
    monkeypatch.setattr(query_builder, "CURRICULUM_DIR", tmp_path / "curriculum" / "l2-uk-en")

    bucket_a, bucket_b = query_builder.build_query_buckets(discovery_path, "a1")

    assert bucket_a == ['"букви і звуки мови"']
    assert {"букви", "звуки", "мови"} <= bucket_b


def test_build_query_buckets_tolerates_missing_plan_file(tmp_path, monkeypatch):
    curriculum_dir = tmp_path / "curriculum" / "l2-uk-en"
    discovery_dir = curriculum_dir / "a1" / "discovery"
    discovery_dir.mkdir(parents=True)
    discovery_path = discovery_dir / "demo.yaml"
    discovery_path.write_text(
        yaml.safe_dump({"query_keywords": ["Апостроф і наголос"]}, allow_unicode=True),
        encoding="utf-8",
    )
    monkeypatch.setattr(query_builder, "CURRICULUM_DIR", curriculum_dir)

    bucket_a, bucket_b = query_builder.build_query_buckets(discovery_path, "a1")

    assert bucket_a == ['"апостроф і наголос"']
    assert {"апостроф", "наголос"} <= bucket_b
