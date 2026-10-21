"""Tests for scripts/lexicon/generate_vesum_form_shards.py (#5882 residual).

Uses small in-test SQLite fixtures — the real ``data/vesum.db`` (409K
lemmas, 6.7M forms) is never required for these tests (binding design point
7: "Unit tests use small fixtures").
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon.generate_vesum_form_shards import (
    MAX_SHARD_P95_GZ_BYTES,
    MAX_TOTAL_GZ_BYTES,
    ShardSizeBudgetError,
    generate,
)
from scripts.lexicon.vesum_form_key import (
    fnv1a32,
    load_vesum_form_key_vectors,
    vesum_form_key,
    vesum_shard_id,
)

FIXTURE_DB_PATH = Path(__file__).resolve().parent / "fixtures" / "vesum_sample.db"


def _build_db(tmp_path: Path, rows: list[tuple[str, str]]) -> Path:
    """rows: (word_form, lemma) pairs, mirroring the real ``forms`` table
    shape (word_form, lemma, tags, pos) — tags/pos are unused by the
    generator, so the fixture omits them."""
    db_path = tmp_path / "vesum_fixture.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    conn.executemany(
        "INSERT INTO forms (word_form, lemma, tags, pos) VALUES (?, ?, '', '')",
        rows,
    )
    conn.commit()
    conn.close()
    return db_path


def test_vesum_form_key_matches_golden_vectors() -> None:
    for case in load_vesum_form_key_vectors():
        assert vesum_form_key(case["input"]) == case["expected"], case


def test_shard_id_is_stable_zero_padded_and_in_range() -> None:
    shard_count = 4096
    for word in ["привіт", "книжка", "п'ять", "Ґанок", "тест"]:
        key = vesum_form_key(word)
        shard_id = vesum_shard_id(key, shard_count)
        assert len(shard_id) >= 3
        assert 0 <= int(shard_id, 16) < shard_count
        # Deterministic: same key always hashes to the same shard.
        assert vesum_shard_id(key, shard_count) == shard_id


def test_fnv1a32_hash_is_deterministic() -> None:
    assert fnv1a32("привіт") == fnv1a32("привіт")
    assert 0 <= fnv1a32("привіт") <= 0xFFFFFFFF
    assert fnv1a32("привіт") != fnv1a32("книжка")


def test_generate_writes_every_shard_and_groups_lemmas_by_normalized_key(
    tmp_path: Path,
) -> None:
    db_path = _build_db(
        tmp_path,
        [
            ("книжка", "книжка"),
            ("книжки", "книжка"),
            # Homograph: "коси" is both a form of "коса" (braid/scythe) and of
            # "косити" (to mow) in real VESUM — simulate with two lemmas here.
            ("коси", "коса"),
            ("коси", "косити"),
            # Apostrophe-variant forms must collapse to ONE key (typewriter
            # apostrophe vs the canonical VESUM modifier-letter apostrophe).
            ("п'ять", "п'ять"),
            ("п’ять", "п'ять"),
        ],
    )
    shard_count = 16
    out_dir = tmp_path / "shards"
    manifest_out = tmp_path / "manifest.json"

    manifest = generate(
        db_path=db_path,
        out_dir=out_dir,
        manifest_out=manifest_out,
        shard_count=shard_count,
    )

    # Every shard id in range is written, even empty ones — a 404 at runtime
    # is unambiguously a publish/fetch problem, never "no forms hashed here".
    written = sorted(p.name for p in out_dir.glob("*.json") if p.name != "_manifest.json")
    assert written == [f"{i:03x}.json" for i in range(shard_count)]

    # Distinct normalized keys: книжка, книжки, коси, п'ять (apostrophe
    # variants collapsed) = 4.
    assert manifest["totalForms"] == 4

    shard_for = {}
    for shard_path in out_dir.glob("*.json"):
        if shard_path.name == "_manifest.json":
            continue
        payload = json.loads(shard_path.read_text(encoding="utf-8"))
        for key, lemmas in payload.items():
            shard_for[key] = (shard_path.stem, lemmas)

    apostrophe_key = vesum_form_key("п'ять")
    assert shard_for[apostrophe_key][1] == ["п'ять"]
    homograph_key = vesum_form_key("коси")
    assert shard_for[homograph_key][1] == ["коса", "косити"]
    # Lemmas land in the shard the key actually hashes to.
    assert shard_for[homograph_key][0] == vesum_shard_id(homograph_key, shard_count)

    # Manifest is committed-artifact-small and self-describing.
    assert manifest["schema"] == "atlas-vesum-form-shards"
    assert manifest["hashAlgorithm"] == "fnv1a32"
    assert manifest["shardCount"] == shard_count
    assert manifest["shardsWritten"] == shard_count
    assert manifest_out.exists()
    assert json.loads(manifest_out.read_text(encoding="utf-8")) == manifest


def test_generate_enforces_total_gz_size_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _build_db(tmp_path, [("книжка", "книжка"), ("книжки", "книжка")])
    monkeypatch.setattr("scripts.lexicon.generate_vesum_form_shards.MAX_TOTAL_GZ_BYTES", 1)

    with pytest.raises(ShardSizeBudgetError):
        generate(
            db_path=db_path,
            out_dir=tmp_path / "shards",
            manifest_out=tmp_path / "manifest.json",
            shard_count=16,
        )


def test_generate_enforces_shard_p95_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _build_db(tmp_path, [("книжка", "книжка"), ("книжки", "книжка")])
    monkeypatch.setattr("scripts.lexicon.generate_vesum_form_shards.MAX_SHARD_P95_GZ_BYTES", 1)

    with pytest.raises(ShardSizeBudgetError):
        generate(
            db_path=db_path,
            out_dir=tmp_path / "shards",
            manifest_out=tmp_path / "manifest.json",
            shard_count=16,
        )


def test_generate_no_enforce_budget_bypasses_the_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _build_db(tmp_path, [("книжка", "книжка")])
    monkeypatch.setattr("scripts.lexicon.generate_vesum_form_shards.MAX_TOTAL_GZ_BYTES", 1)

    manifest = generate(
        db_path=db_path,
        out_dir=tmp_path / "shards",
        manifest_out=tmp_path / "manifest.json",
        shard_count=16,
        enforce_budget=False,
    )
    assert manifest["sizeBudget"]["enforced"] is False


def test_generate_missing_db_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        generate(
            db_path=tmp_path / "does-not-exist.db",
            out_dir=tmp_path / "shards",
            manifest_out=tmp_path / "manifest.json",
            shard_count=16,
        )


@pytest.mark.skipif(not FIXTURE_DB_PATH.exists(), reason="tests/fixtures/vesum_sample.db not present")
def test_generate_against_repo_vesum_fixture_smoke(tmp_path: Path) -> None:
    """Real (small) VESUM sample database — checks the generator round-trips
    real row shapes (word_form, lemma, tags, pos) without special-casing."""
    conn = sqlite3.connect(str(FIXTURE_DB_PATH))
    try:
        rows = conn.execute("SELECT word_form, lemma FROM forms").fetchall()
    finally:
        conn.close()
    expected_keys = {vesum_form_key(w) for w, _ in rows if w and w.strip()}

    manifest = generate(
        db_path=FIXTURE_DB_PATH,
        out_dir=tmp_path / "shards",
        manifest_out=tmp_path / "manifest.json",
        shard_count=64,
    )

    assert manifest["totalForms"] == len(expected_keys)
    assert manifest["sizeBudget"]["totalGzBytes"] <= MAX_TOTAL_GZ_BYTES
    assert manifest["sizeBudget"]["shardP95GzBytes"] <= MAX_SHARD_P95_GZ_BYTES
