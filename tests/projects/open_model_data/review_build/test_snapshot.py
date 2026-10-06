import json
import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build.contract import Citation, canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader, identifier, open_readonly


def test_mode_ro_query_only_attach_and_memory_temp(bundle, tmp_path):
    conn = open_readonly(bundle["db"])
    try:
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
        assert conn.execute("PRAGMA temp_store").fetchone()[0] == 2
        for sql in (
            "DELETE FROM units",
            "CREATE TEMP TABLE bad (id)",
            "ATTACH DATABASE ':memory:' AS bad",
            "DETACH DATABASE main",
        ):
            with pytest.raises(sqlite3.DatabaseError):
                conn.execute(sql)
    finally:
        conn.close()
    missing = tmp_path / "SYNTHETIC missing.db"
    with pytest.raises(sqlite3.OperationalError):
        open_readonly(missing)
    assert not missing.exists()


def test_pinned_snapshot_and_special_character_uri(bundle, tmp_path):
    source = tmp_path / "SYNTHETIC #?%.db"
    source.write_bytes(bundle["db"].read_bytes())
    writer = sqlite3.connect(source)
    writer.execute("PRAGMA journal_mode=WAL")
    with SnapshotReader({"sources.db": source}) as reader:
        c = bundle["candidates"][0].slots[0].citations[0]
        before = reader.field(c)
        writer.execute("UPDATE units SET source_field='SYNTHETIC later' WHERE id=1")
        writer.commit()
        assert reader.field(c) == before
    writer.close()


def test_snapshot_digest_is_order_independent_and_includes_role_reads(bundle):
    citations = [c.slots[0].citations[0] for c in bundle["candidates"]]
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        for citation in citations:
            reader.field(citation)
        forward = reader.snapshots()
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        for citation in reversed(citations):
            reader.row(citation)
        assert reader.snapshots() == forward
        expected = {(c.row_key, c.field_sha256) for c in citations}
        expected = sorted(expected, key=lambda p: (p[0].encode(), p[1]))
        assert forward["sources.db:units"] == "sources.db:units@" + digest(canonical(expected))


def test_json_pointer_hashes_whole_column_and_primary_key_validation(bundle):
    raw = json.dumps({"SYNTHETIC/key": ["SYNTHETIC value"]})
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET source_field=? WHERE id=1", (raw,))
    citation = replace(
        bundle["candidates"][0].slots[0].citations[0],
        field="source_field#/SYNTHETIC~1key/0",
        field_sha256=digest(raw.encode()),
    )
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert reader.field(citation) == (raw, "SYNTHETIC value")
        for bad in (
            replace(citation, field_sha256="0" * 64),
            replace(citation, row_key="entry_id=1"),
            replace(citation, row_key="id=1;id=1"),
            replace(citation, row_key="id=99"),
            replace(citation, row_key="SYNTHETIC"),
            replace(citation, field="missing"),
            replace(citation, field="source_field#bad"),
            replace(citation, table="units; DROP TABLE units"),
        ):
            with pytest.raises(BuildError):
                reader.field(bad)
        with pytest.raises(BuildError):
            identifier("SYNTHETIC bad")
        with pytest.raises(BuildError):
            reader.units({"store": "sources.db", "kind": "sql", "sql": "SELECT id, source_field FROM units"})
        with pytest.raises(BuildError):
            reader.units({"store": "sources.db", "kind": "sql", "sql": "SELECT 1 FROM units"})
        with pytest.raises(BuildError):
            reader.units({"store": "sources.db", "kind": "sql", "sql": "DELETE FROM units"})
    with pytest.raises(BuildError, match="duplicate_database"):
        SnapshotReader({"sources.db": bundle["db"], "other.db": bundle["db"]})


def test_vesum_transform_queries_pinned_form_set(bundle, tmp_path):
    db = tmp_path / "synthetic-vesum.db"
    with sqlite3.connect(db) as writer:
        writer.execute("CREATE TABLE forms(id INTEGER PRIMARY KEY, form TEXT)")
        writer.execute("INSERT INTO forms VALUES(1, 'SYNTHETIC')")
    with SnapshotReader({"vesum.db": db}) as reader:
        policy = {"store": "vesum.db", "table": "forms", "field": "form"}
        assert reader.is_word("SYNTHETIC", policy)
        assert not reader.is_word("SYNTHETIC-missing", policy)
        assert "vesum.db:forms" in reader.snapshots()
        with pytest.raises(BuildError):
            reader.is_word("SYNTHETIC", {**policy, "store": "sources.db"})


def test_file_store_interface():
    class SyntheticStore:
        def row(self, table, key):
            return {"text": "SYNTHETIC file", "row_key": key}

        def units(self, query):
            return ["SYNTHETIC unit"]

        def file_hashes(self):
            return {"SYNTHETIC.json": digest(b"SYNTHETIC file")}

        def all_rows(self, table):
            return [self.row(table, "SYNTHETIC unit")]

    c = Citation(
        "synthetic",
        "ua-gec",
        "SYNTHETIC.json",
        "SYNTHETIC unit",
        "text",
        "SYNTHETIC locator",
        digest(b"SYNTHETIC file"),
    )
    with SnapshotReader({}, {"ua-gec": SyntheticStore()}) as reader:
        assert reader.field(c) == ("SYNTHETIC file", "SYNTHETIC file")
        assert reader.units({"store": "ua-gec", "kind": "glob"}) == ["SYNTHETIC unit"]
        assert len(reader.all_rows("ua-gec", "SYNTHETIC.json")) == 1
        assert reader.file_hashes()["ua-gec"]["SYNTHETIC.json"] == digest(b"SYNTHETIC file")
        assert "ua-gec:SYNTHETIC.json" in reader.snapshots()


def test_snapshot_can_pin_binary_metadata_without_treating_it_as_text(bundle):
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("ALTER TABLE units ADD COLUMN synthetic_blob BLOB")
        writer.execute("UPDATE units SET synthetic_blob=? WHERE id=1", (b"SYNTHETIC binary metadata",))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        reader.units(bundle["spec"]["unit_query"])
        reader.row(bundle["candidates"][0].slots[0].citations[0])
        assert reader.reads["sources.db", "units"] == {("id=1", digest(bundle["rows"][0]["source_field"].encode()))}


def test_snapshot_pins_only_cited_column_bytes_sorted_by_utf8_row_key(bundle):
    rows = bundle["rows"]
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        reader.units(bundle["spec"]["unit_query"])
        for index in (9, 1, 0):
            for area in ("slots", "response"):
                reader.row(getattr(bundle["candidates"][index], area)[0].citations[0])
        pairs = [
            (f"id={rows[i]['id']}", digest(rows[i][field].encode()))
            for i in (9, 1, 0)
            for field in ("source_field", "target_field")
        ]
        pairs.sort(key=lambda p: (p[0].encode("utf-8"), p[1]))
        assert reader.snapshots() == {"sources.db:units": "sources.db:units@" + digest(canonical(pairs))}
        before = reader.snapshots()
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET tags='SYNTHETIC irrelevant metadata'")
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        for index in (0, 1, 9):
            for area in ("slots", "response"):
                reader.field(getattr(bundle["candidates"][index], area)[0].citations[0])
        assert reader.snapshots() == before
