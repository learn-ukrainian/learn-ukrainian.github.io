from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.reads_content

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
