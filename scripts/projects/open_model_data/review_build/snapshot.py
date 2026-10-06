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
    def __init__(
        self,
        databases: Mapping[str, Path],
        files: Mapping[str, FileStore] | None = None,
        *,
        repository_root: Path | None = None,
    ):
        self.connections: dict[str, sqlite3.Connection] = {}
        self.files = dict(files or {})
        self.reads: dict[tuple[str, str], set[tuple[str, str]]] = {}
        self.repository_root = (repository_root or Path(__file__).resolve().parents[4]).resolve()
        self.repository_configs: dict[str, bytes] = {}
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

    def read_repository_config(self, name: str) -> bytes:
        """Adapters read each repository config once; the manifest pins its bytes."""
        path = Path(name)
        require(not path.is_absolute() and bool(path.parts) and ".." not in path.parts, "repository_config")
        target = (self.repository_root / path).resolve()
        require(target.is_relative_to(self.repository_root), "repository_config")
        key = path.as_posix()
        if key not in self.repository_configs:
            self.repository_configs[key] = target.read_bytes()
        return self.repository_configs[key]

    def repository_config_hashes(self) -> dict[str, str]:
        return {name: digest(content) for name, content in sorted(self.repository_configs.items())}

    def row(self, citation: Citation) -> dict:
        if citation.store in self.files:
            row = dict(self.files[citation.store].row(citation.table, citation.row_key))
            self._remember_citation(citation, row)
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
        self._remember_citation(citation, row)
        return row

    def _remember_citation(self, citation: Citation, row: dict) -> None:
        column = citation.field.partition("#")[0]
        require(column in row and isinstance(row[column], str), "field_unavailable")
        actual = digest(row[column].encode("utf-8"))
        require(actual == citation.field_sha256, "field_digest")
        self.reads.setdefault((citation.store, citation.table), set()).add((citation.row_key, actual))

    def field(self, citation: Citation) -> tuple[str, object]:
        column, separator, pointer = citation.field.partition("#")
        row = self.row(citation)
        # row() authenticated and pinned these column bytes already.
        raw = row[column]
        selected = raw
        if separator:
            require(pointer == "" or pointer.startswith("/"), "json_pointer")
            selected = json.loads(raw)
            for segment in pointer.split("/")[1:]:
                key = segment.replace("~1", "/").replace("~0", "~")
                selected = selected[int(key)] if isinstance(selected, list) else selected[key]
        return raw, selected

    def units(self, query: dict) -> list[str]:
        units = [str(value) for value in self.query_values(query)]
        require(len(units) == len(set(units)), "duplicate_unit_query")
        return sorted(units)

    def query_values(self, query: dict) -> list:
        """One-column read results; set rules permit repeated source variants."""
        store = query["store"]
        if store in self.files:
            units = self.files[store].units(query)
        else:
            require(store in self.connections and query.get("kind") == "sql", "unit_query")
            require(query["sql"].lstrip().upper().startswith(("SELECT ", "WITH ")), "unit_query")
            connection = self.connections[store]
            # The connection's read-only authorizer already denies ATTACH and
            # DETACH. Unit queries count keys; they do not invent field hashes
            # by scanning unrelated columns/rows after the query.
            rows = connection.execute(query["sql"], query.get("parameters", [])).fetchall()
            require(all(len(r) == 1 for r in rows), "unit_query")
            units = [r[0] for r in rows]
        return units

    def all_rows(self, store: str, table: str) -> list[dict]:
        return list(self.iter_rows(store, table))

    def iter_rows(self, store: str, table: str):
        if store in self.files:
            for item in self.files[store].all_rows(table):
                row = dict(item)
                require("row_key" in row, "invalid_row_key")
                yield row
            return
        require(store in self.connections, "unknown_store")
        conn = self.connections[store]
        info = conn.execute(f"PRAGMA table_info({identifier(table)})").fetchall()
        keys = [r["name"] for r in sorted(info, key=lambda r: r["pk"]) if r["pk"]]
        require(bool(keys), "invalid_row_key")
        for item in conn.execute(f"SELECT * FROM {identifier(table)}"):
            row = dict(item)
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
            require(isinstance(row[policy["field"]], str), "field_unavailable")
            row_key = ";".join(f"{key}={row[key]}" for key in keys)
            self.reads.setdefault((policy["store"], policy["table"]), set()).add(
                (row_key, digest(row[policy["field"]].encode("utf-8")))
            )
            found = True
        return found

    def snapshots(self) -> dict[str, str]:
        return {
            f"{store}:{table}": f"{store}:{table}@{digest(canonical(sorted(pairs, key=lambda p: (p[0].encode('utf-8'), p[1]))))}"
            for (store, table), pairs in sorted(self.reads.items())
        }

    def file_hashes(self) -> dict:
        return {store: dict(adapter.file_hashes()) for store, adapter in sorted(self.files.items())}
