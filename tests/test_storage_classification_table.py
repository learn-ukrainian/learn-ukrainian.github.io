"""Frozen data/ classification against the independent Git index inventory."""

from __future__ import annotations

import csv
import io
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import pytest

from scripts.storage import build_classification_table as classification

ROOT = Path(__file__).resolve().parents[1]
BASE = "b6b69a52f7cf8658651a1eafa3f02d003ad98b7e"
TABLE = ROOT / "registry/artifacts/classification-v1.tsv"


@pytest.fixture(scope="module")
def generated() -> tuple[str, list[dict[str, str]]]:
    table, _, _ = classification.build(ROOT, BASE)
    return table, list(csv.DictReader(io.StringIO(table), delimiter="\t"))


def test_frozen_rows_and_git_index_totals(generated: tuple[str, list[dict[str, str]]]) -> None:
    table, rows = generated
    assert table == TABLE.read_text(encoding="utf-8")
    assert len(rows) == 1708
    assert sum(int(row["size"]) for row in rows) == 993_288_549
    assert Counter(row["class"] for row in rows) == {"K": 1107, "A": 597, "S": 4}

    # A private base-commit index keeps this check valid after later migration
    # phases remove data/ paths from the live worktree index.
    with tempfile.TemporaryDirectory(prefix=".classification-index-", dir=ROOT) as scratch:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        subprocess.run(["git", "read-tree", BASE], cwd=ROOT, env=env, check=True)
        index = subprocess.check_output(["git", "ls-files", "-s", "data"], cwd=ROOT, env=env)
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
    ).stdout
    assert sum(int(size) for size in sizes.splitlines()) == sum(int(row["size"]) for row in rows)


def test_repeated_generation_is_byte_identical(generated: tuple[str, list[dict[str, str]]]) -> None:
    assert classification.build(ROOT, BASE)[0] == generated[0]


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
        "data/textbooks": "120000",
        "data/vesum": "120000",
        "data/telemetry/.gitkeep": "100644",
        "data/ubertext-freq/.gitignore": "100644",
    }
    for row in rows:
        if row["class"] == "A":
            assert row["reason"].startswith("external;") or ".py;" in row["reason"]
            assert "regenerable" in row["reason"]
