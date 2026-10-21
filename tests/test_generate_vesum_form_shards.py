"""Tests for scripts/lexicon/generate_vesum_form_shards.py (#5882 residual).

Uses small in-test SQLite fixtures — the real ``data/vesum.db`` (409K
lemmas, 6.7M forms) is never required for these tests (binding design point
7: "Unit tests use small fixtures").
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.lexicon.generate_vesum_form_shards import (
    generate,
)
from scripts.lexicon.vesum_form_key import (
    load_vesum_form_key_vectors,
    vesum_form_key,
    vesum_shard_id,
)


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
