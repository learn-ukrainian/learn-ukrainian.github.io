"""One pinned read transaction per DB; file stores are component-owned adapters.

No helper imports the much broader Sources client (which can perform network I/O).
SQL identifiers and primary keys are verified against schema, not interpolated raw.
"""

import json
import re
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from .contract import Citation, canonical, digest
from .errors import require


def identifier(name: str) -> str:
    require(bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)), "invalid_identifier")
    return '"' + name + '"'


def open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, isolation_level=None)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.set_authorizer(
            lambda action, *_: (
                sqlite3.SQLITE_DENY
                if action
                in {
                    sqlite3.SQLITE_ATTACH,
                    sqlite3.SQLITE_DETACH,
                }
                else sqlite3.SQLITE_OK
            )
        )
        connection.execute("BEGIN")
        connection.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
    except BaseException:
        connection.close()
        raise
    return connection


class FileStore(Protocol):
    """WP1 supplies official-reader rows and independent units from pinned files."""

    def row(self, table: str, row_key: str) -> Mapping: ...
    def units(self, query: dict) -> list[str]: ...
    def file_hashes(self) -> Mapping[str, str]: ...
    def all_rows(self, table: str) -> list[Mapping]: ...


class SnapshotReader:
    def __init__(self, databases: Mapping[str, Path], files: Mapping[str, FileStore] | None = None):
        self.connections: dict[str, sqlite3.Connection] = {}
        self.files = dict(files or {})
        self.reads: dict[tuple[str, str], set[tuple[str, str]]] = {}
        self._censused: set[tuple[str, str]] = set()
        try:
            require(len({p.resolve() for p in databases.values()}) == len(databases), "duplicate_database")
            for store, path in sorted(databases.items()):
                require(store not in self.files, "duplicate_store")
                self.connections[store] = open_readonly(path)
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self) -> None:
        for connection in self.connections.values():
            connection.close()

    def row(self, citation: Citation) -> dict:
        if citation.store in self.files:
            row = dict(self.files[citation.store].row(citation.table, citation.row_key))
            self._remember(citation.store, citation.table, citation.row_key, row)
            return row
        require(citation.store in self.connections, "unknown_store")
        conn = self.connections[citation.store]
        info = conn.execute(f"PRAGMA table_info({identifier(citation.table)})").fetchall()
        keys = [r["name"] for r in sorted(info, key=lambda r: r["pk"]) if r["pk"]]
        parts = citation.row_key.split(";")
        pairs = [p.split("=", 1) for p in parts]
        require(bool(keys) and all(len(p) == 2 for p in pairs), "invalid_row_key")
        supplied = dict(pairs)
        require(len(supplied) == len(pairs) and set(supplied) == set(keys), "invalid_row_key")
        where = " AND ".join(f"{identifier(k)}=?" for k in keys)
        rows = conn.execute(
            f"SELECT * FROM {identifier(citation.table)} WHERE {where}", [supplied[k] for k in keys]
        ).fetchall()
        require(len(rows) == 1, "row_unavailable")
        row = dict(rows[0])
        self._remember(citation.store, citation.table, citation.row_key, row)
        return row

    def _remember(self, store: str, table: str, row_key: str, row: dict) -> None:
        for value in row.values():
            if isinstance(value, str):
                raw = value.encode("utf-8")
            elif isinstance(value, bytes | bytearray | memoryview):
                raw = bytes(value)
            else:
                raw = canonical(value)
            self.reads.setdefault((store, table), set()).add((row_key, digest(raw)))

    def field(self, citation: Citation) -> tuple[str, object]:
        column, separator, pointer = citation.field.partition("#")
        row = self.row(citation)
        require(column in row and isinstance(row[column], str), "field_unavailable")
        raw = row[column]
        actual = digest(raw.encode("utf-8"))
        require(actual == citation.field_sha256, "field_digest")
        self.reads.setdefault((citation.store, citation.table), set()).add((citation.row_key, actual))
        selected = raw
        if separator:
            require(pointer == "" or pointer.startswith("/"), "json_pointer")
            selected = json.loads(raw)
            for segment in pointer.split("/")[1:]:
                key = segment.replace("~1", "/").replace("~0", "~")
                selected = selected[int(key)] if isinstance(selected, list) else selected[key]
        return raw, selected

    def units(self, query: dict) -> list[str]:
        store = query["store"]
        if store in self.files:
            units = self.files[store].units(query)
        else:
            require(store in self.connections and query.get("kind") == "sql", "unit_query")
            require(query["sql"].lstrip().upper().startswith(("SELECT ", "WITH ")), "unit_query")
            connection = self.connections[store]
            tables = set()

            def authorize(action, table, column, database, trigger):
                if action == sqlite3.SQLITE_READ and table != "sqlite_master":
                    tables.add(table)
                return (
                    sqlite3.SQLITE_DENY
                    if action in {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
                    else sqlite3.SQLITE_OK
                )

            connection.set_authorizer(authorize)
            try:
                rows = connection.execute(query["sql"], query.get("parameters", [])).fetchall()
            finally:
                connection.set_authorizer(
                    lambda action, *_: (
                        sqlite3.SQLITE_DENY
                        if action in {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
                        else sqlite3.SQLITE_OK
                    )
                )
            for table in sorted(tables):
                if (store, table) not in self._censused:
                    for _ in self.iter_rows(store, table):
                        pass
                    self._censused.add((store, table))
            require(all(len(r) == 1 for r in rows), "unit_query")
            units = [str(r[0]) for r in rows]
        require(len(units) == len(set(units)), "duplicate_unit_query")
        return sorted(units)

    def all_rows(self, store: str, table: str) -> list[dict]:
        return list(self.iter_rows(store, table))

    def iter_rows(self, store: str, table: str):
        if store in self.files:
            for item in self.files[store].all_rows(table):
                row = dict(item)
                require("row_key" in row, "invalid_row_key")
                self._remember(store, table, str(row["row_key"]), row)
                yield row
            return
        require(store in self.connections, "unknown_store")
        conn = self.connections[store]
        info = conn.execute(f"PRAGMA table_info({identifier(table)})").fetchall()
        keys = [r["name"] for r in sorted(info, key=lambda r: r["pk"]) if r["pk"]]
        require(bool(keys), "invalid_row_key")
        for item in conn.execute(f"SELECT * FROM {identifier(table)}"):
            row = dict(item)
            row_key = ";".join(f"{key}={row[key]}" for key in keys)
            self._remember(store, table, row_key, row)
            yield row

    def is_word(self, word: str, policy: dict) -> bool:
        # Reviewed spec identifies the exact VESUM form table and field.
        require(policy.get("store") == "vesum.db", "transform_policy")
        conn = self.connections[policy["store"]]
        query = f"SELECT * FROM {identifier(policy['table'])} WHERE {identifier(policy['field'])}=?"
        found = False
        info = conn.execute(f"PRAGMA table_info({identifier(policy['table'])})").fetchall()
        keys = [r["name"] for r in sorted(info, key=lambda r: r["pk"]) if r["pk"]]
        require(bool(keys), "invalid_row_key")
        for item in conn.execute(query, (word,)):
            row = dict(item)
            self._remember(policy["store"], policy["table"], ";".join(f"{key}={row[key]}" for key in keys), row)
            found = True
        return found

    def snapshots(self) -> dict[str, str]:
        return {
            f"{store}:{table}": f"{store}:{table}@{digest(canonical(sorted(pairs, key=lambda p: (p[0].encode('utf-8'), p[1]))))}"
            for (store, table), pairs in sorted(self.reads.items())
        }

    def file_hashes(self) -> dict:
        return {store: dict(adapter.file_hashes()) for store, adapter in sorted(self.files.items())}
