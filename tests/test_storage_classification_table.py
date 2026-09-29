"""Frozen data/ classification against the independent Git index inventory."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import pytest

from scripts.storage import build_classification_table as classification

ROOT = Path(__file__).resolve().parents[1]
BASE = "10b39479b1ca8f97c3f7cf7547e71d58141947b1"
TABLE = ROOT / "registry/artifacts/classification-v1.tsv"
META = TABLE.with_suffix(".meta.json")


@pytest.fixture(scope="module")
def generated() -> tuple[str, list[dict[str, str]]]:
    table, _, _ = classification.build(ROOT, BASE)
    return table, list(csv.DictReader(io.StringIO(table), delimiter="\t"))


@pytest.mark.repo_wide
def test_frozen_rows_and_git_index_totals(generated: tuple[str, list[dict[str, str]]]) -> None:
    table, rows = generated
    assert table == TABLE.read_text(encoding="utf-8")
    assert len(rows) == 1706
    assert sum(int(row["size"]) for row in rows) == 993_288_299
    assert Counter(row["class"] for row in rows) == {"K": 1099, "A": 605, "S": 2}
    assert set(rows[0]) == {"path", "mode", "blob", "size", "class", "group", "reason", "judgment"}
    assert all(classification.classify(row["path"]) is not None for row in rows)

    # A private base-commit index keeps this check valid after later migration
    # phases remove data/ paths from the live worktree index.
    with tempfile.TemporaryDirectory(prefix=".classification-index-", dir=ROOT) as scratch:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        subprocess.run(["git", "read-tree", BASE], cwd=ROOT, env=env, check=True, timeout=30)
        index = subprocess.check_output(["git", "ls-files", "-s", "data"], cwd=ROOT, env=env, timeout=30)
    entries = [line.split(b"\t", 1) for line in index.splitlines()]
    assert len(entries) == len(rows)
    indexed = {path.decode(): (meta.split()[0].decode(), meta.split()[1].decode()) for meta, path in entries}
    assert indexed == {row["path"]: (row["mode"], row["blob"]) for row in rows}
    blobs = b"\n".join(meta.split()[1] for meta, _ in entries) + b"\n"
    sizes = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectsize)"],
        cwd=ROOT,
        input=blobs,
        stdout=subprocess.PIPE,
        check=True,
        timeout=120,
    ).stdout
    assert sum(int(size) for size in sizes.splitlines()) == sum(int(row["size"]) for row in rows)


def test_repeated_generation_is_byte_identical(generated: tuple[str, list[dict[str, str]]]) -> None:
    assert classification.build(ROOT, BASE)[0] == generated[0]


def test_meta_matches_table_generator_and_git_base(generated: tuple[str, list[dict[str, str]]]) -> None:
    table, rows = generated
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert meta["base_commit"] == BASE
    assert meta["rows"] == len(rows)
    assert meta["bytes"] == sum(int(row["size"]) for row in rows)
    assert meta["classes"] == {
        key: {
            "rows": sum(row["class"] == key for row in rows),
            "bytes": sum(int(row["size"]) for row in rows if row["class"] == key),
        }
        for key in ("K", "A", "S")
    }
    assert meta["table_sha256"] == hashlib.sha256(table.encode()).hexdigest()
    assert (
        meta["generator_blob"]
        == subprocess.check_output(
            ["git", "hash-object", "scripts/storage/build_classification_table.py"], cwd=ROOT, text=True, timeout=30
        ).strip()
    )


def test_unmatched_paths_fail_and_list_every_path(monkeypatch: pytest.MonkeyPatch) -> None:
    paths = ("data/unclassified-one.txt", "data/unclassified-two.txt")

    def fake_git(_repo: Path, *args: str, env: dict[str, str] | None = None) -> bytes:
        if args[0] == "rev-parse":
            return b"0" * 40 + b"\n"
        if args[0] == "read-tree":
            return b""
        if args[0] == "ls-files":
            return b"".join(b"100644 " + b"1" * 40 + b" 0\t" + path.encode() + b"\0" for path in paths)
        raise AssertionError("unmatched paths must fail before object reads")

    monkeypatch.setattr(classification, "git", fake_git)
    with pytest.raises(ValueError, match="unmatched data paths") as error:
        classification.build(ROOT, BASE)
    for path in paths:
        assert path in str(error.value)


def test_special_rows_and_artifact_reasons(generated: tuple[str, list[dict[str, str]]]) -> None:
    rows = generated[1]
    special = {row["path"]: row["mode"] for row in rows if row["class"] == "S"}
    assert special == {
        "data/telemetry/.gitkeep": "100644",
        "data/ubertext-freq/.gitignore": "100644",
    }
    assert {row["judgment"] for row in rows} == {"rule", "judgment"}
    assert all("judgment:" not in row["reason"] for row in rows)
    navsi_catalog = next(row for row in rows if row["path"] == "data/corpus_audit/navsi200-catalog.json")
    assert (navsi_catalog["class"], navsi_catalog["group"], navsi_catalog["reason"], navsi_catalog["judgment"]) == (
        "K",
        "corpus_audit_controls",
        "frozen scraped snapshot, no committed producer",
        "judgment",
    )
    split_pools = [
        row
        for row in rows
        if row["path"].startswith("data/lexicon/source-inventory/grade-") and "-headwords-" in row["path"]
    ]
    assert len(split_pools) == 8
    assert all(row["class"] == "A" and row["group"] == "lexicon_headword_candidates" for row in split_pools)
    for row in rows:
        if row["class"] == "A":
            assert row["reason"].startswith("external;") or ".py;" in row["reason"]
            assert "regenerable" in row["reason"]
