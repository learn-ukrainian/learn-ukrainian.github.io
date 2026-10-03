"""Call every sources MCP tool and record each persistent write it attempts (#9551).

Run as a script in a fresh interpreter: the audit hook it installs cannot be
removed, so it must not run inside the pytest process.

What counts as a persistent write, and is refused before it happens:

* an SQLite statement that would change a file-backed database (create, alter,
  drop, insert, update, delete, attach, or a ``journal_mode`` change), seen by an
  authorizer installed on every connection;
* opening a missing SQLite file read-write, which creates it;
* a Python file open for writing, or a mkdir, rename, remove, rmdir, truncate,
  link, chmod or utime.

The server's request log (``LU_MCP_SOURCES_LOG_DIR``) is the one allowed write.
Network calls are recorded, not refused. ``--hermetic`` points the sources DB, VESUM
and the Wikipedia cache at ``--scratch``, fills the first two with
``sources_probe_fixture`` rows, replaces the network with that module's synthetic
pages, and skips sleeps, so every read-only tool's lookup finds its row and runs
its success path, and the result does not depend on host data. Without it the
tools read the host's databases, refused writes included, and use the live network.

``--inject-writer TOOL`` is the audit's own mutation test: it makes TOOL write to
the sources DB after each successful lookup, which the audit must report.

Prints one JSON object per tool on stdout; in hermetic runs ``hit`` says whether
the result shows the fixture row the call was meant to find.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import sources_probe_fixture as fixture  # Sibling module; this file runs as a script.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_SOURCES_DB = "LU_SOURCES_DB"
SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"

_SQLITE_WRITE_ACTIONS = frozenset(
    getattr(sqlite3, name)
    for name in (
        "SQLITE_ALTER_TABLE",
        "SQLITE_ANALYZE",
        "SQLITE_ATTACH",
        "SQLITE_CREATE_INDEX",
        "SQLITE_CREATE_TABLE",
        "SQLITE_CREATE_TRIGGER",
        "SQLITE_CREATE_VIEW",
        "SQLITE_CREATE_VTABLE",
        "SQLITE_DELETE",
        "SQLITE_DROP_INDEX",
        "SQLITE_DROP_TABLE",
        "SQLITE_DROP_TRIGGER",
        "SQLITE_DROP_VIEW",
        "SQLITE_DROP_VTABLE",
        "SQLITE_INSERT",
        "SQLITE_REINDEX",
        "SQLITE_UPDATE",
    )
)
_PERSISTENT_PRAGMAS = frozenset({"journal_mode", "user_version", "application_id", "auto_vacuum", "page_size"})
_OPEN_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_FS_EVENTS = frozenset(
    {
        "os.rename",
        "os.remove",
        "os.rmdir",
        "os.truncate",
        "os.symlink",
        "os.link",
        "os.chmod",
        "os.utime",
        "shutil.rmtree",
        "shutil.move",
    }
)

# Arguments that reach each tool's lookup path, found in the hermetic fixture
# (sources_probe_fixture.py) and in the host stores alike.
TOOL_ARGUMENTS: dict[str, dict[str, Any]] = {
    "search_sources": {"query": "мова"},
    "search_text": {"query": "мова"},
    "search_literary": {"query": "мова"},
    "search_resources": {"query": "мова"},
    "search_external": {"query": "мова"},
    "get_full_text": {"work": "Слово про мову"},
    "get_chunk_context": {"chunk_id": "probe-textbook_c0001"},
    "collection_stats": {},
    "mcp_server_identity": {},
    "check_modern_form": {"word": "мова"},
    "verify_word": {"word": "мова"},
    "verify_quote": {"text": "Рідна мова співає в серці", "author": "Зондовий"},
    "verify_source_attribution": {"source": "grinchenko_1907", "claim": "хата"},
    "verify_words": {"words": ["мова"]},
    "vet_vocabulary": {"words": ["мова"]},
    "verify_lemma": {"lemma": "мова"},
    "inspect_word": {"word": "мова"},
    "inspect_words": {"words": ["мова"]},
    "inspect_lemma": {"lemma": "мова"},
    "verify_stress": {"word": "мова"},
    "verify_stresses": {"words": ["мова"]},
    "check_text": {"text": "Мова: приймати участь."},
    "query_wikipedia": {"query": "Київ"},
    "query_grac": {"query": "мова"},
    "query_ulif": {"word": "привіт"},
    "query_ulif_synonyms": {"word": "привіт"},
    "query_ulif_antonyms": {"word": "добрий"},
    "query_ulif_phraseology": {"word": "рука"},
    "query_ulif_records": {"words": ["мова"]},
    "query_r2u": {"word": "язык"},
    "query_pravopys": {"topic": "апостроф"},
    "search_ua_gec_errors": {"query": "приймати участь"},
    "search_style_guide": {"query": "приймати участь"},
    "query_cefr_level": {"query": "мова"},
    "search_definitions": {"query": "мова"},
    "search_grinchenko_1907": {"query": "хата"},
    "search_esum": {"query": "мова"},
    "search_idioms": {"query": "рука"},
    "search_synonyms": {"query": "мова"},
    "translate_en_uk": {"query": "language"},
    "query_e2u": {"word": "language"},
    "query_sum20": {"word": "мова"},
    "query_slovnyk_me": {"word": "мова"},
    "search_slovnyk_me": {"query": "мова"},
    "search_heritage": {"query": "хата"},
    "check_russian_shadow": {"word": "являється"},
}

# Text each read-only tool's hermetic result shows only when its lookup found the
# fixture row. The tools that persist a fetch are absent: they are denied to
# reviewers and are probed on a cache miss, where their write happens.
HERMETIC_HITS: dict[str, str] = {
    "search_sources": "ext-probe-1",
    "search_text": "`probe-textbook`",
    "search_literary": "probe-literary_c0001",
    "search_resources": "Мова щодня",
    "search_external": "ext-probe-1",
    "get_full_text": "Рідна мова співає в серці.",
    "get_chunk_context": "**[probe-textbook_c0001]**",
    "collection_stats": '"slovnyk_me_entries": 2',
    "mcp_server_identity": '"sources_db_meta_identity": {"scheme"',
    "check_modern_form": '"is_modern_codified": true',
    "verify_word": "matches in VESUM",
    "verify_quote": '"matched": true',
    "verify_source_attribution": '"evidence_count": 1',
    "verify_words": "Found: 1/1",
    "vet_vocabulary": "VESUM: valid",
    "verify_lemma": "### noun (2 forms)",
    "inspect_word": "Status: CLEAN",
    "inspect_words": "CLEAN (clean=1",
    "inspect_lemma": "Total paradigm forms: 2",
    "verify_stress": "ok: мо́ва",
    "verify_stresses": '"entry_key": "мова#1"',
    "check_text": '"correct": "брати участь"',
    "query_grac": "frequency = 1,000",
    "query_ulif_records": '"phrase": "рідна мова"',
    "query_r2u": "мова, язик",
    "query_pravopys": "Pravopys section 7",
    "search_ua_gec_errors": "**Correction**: брати участь",
    "search_style_guide": "Приймати участь – брати участь",
    "query_cefr_level": "мова (A1, іменник)",
    "search_definitions": "Found 1 results in **СУМ-11**",
    "search_grinchenko_1907": "Found 1 results in **Грінченко**",
    "search_esum": "Found 1 results in **ЕСУМ**",
    "search_idioms": "Found 1 results in **Фразеологічний**",
    "search_synonyms": "Синоніми: мова, говір",
    "translate_en_uk": "Found 1 results in **Балла EN→UK**",
    "query_e2u": "**language**: language мова",
    "query_sum20": "Official СУМ-20 entries for 'мова'",
    "query_slovnyk_me": "entry for 'мова'",
    "search_slovnyk_me": "slovnyk.me result(s)",
    "search_heritage": "heritage evidence row(s)",
    "check_russian_shadow": '"matches_russian": true',
}


class SideEffects:
    """Records refused writes for the tool currently running."""

    def __init__(self, allowed_dirs: list[Path]) -> None:
        self.allowed = [os.path.realpath(path) for path in allowed_dirs]
        self.current: list[str] = []
        self.network: list[str] = []
        self._pending = threading.local()
        self._lock = threading.Lock()
        self.opened = 0
        self.guarded = 0
        # Hermetic runs: every database must live here; a connection elsewhere is an escape.
        self.store_root: str | None = None
        self.escapes: list[str] = []

    def guard_connect(self, connect: Any) -> Any:
        """Wrap ``sqlite3.connect`` so every connection gets the write authorizer.

        An authorizer cannot be installed from the audit hook (the connection is not
        initialised yet), so the hook only counts connections and ``unguarded``
        reports any that bypassed this wrapper.
        """

        def guarded_connect(database: Any, *args: Any, **kwargs: Any) -> sqlite3.Connection:
            conn = connect(database, *args, **kwargs)
            conn.set_authorizer(
                self._authorizer(os.fsdecode(database) if isinstance(database, bytes) else str(database))
            )
            with self._lock:
                self.guarded += 1
            return conn

        return guarded_connect

    def unguarded(self) -> int:
        with self._lock:
            return self.opened - self.guarded

    def _allowed(self, path: object) -> bool:
        if isinstance(path, int):
            return True  # An already-open descriptor; its open was checked.
        if isinstance(path, bytes):
            path = os.fsdecode(path)
        real = os.path.realpath(str(path))
        return real == os.devnull or any(real == root or real.startswith(root + os.sep) for root in self.allowed)

    def refuse(self, what: str) -> None:
        self.current.append(what)
        raise PermissionError(f"side-effect probe refused: {what}")

    def audit(self, event: str, args: tuple[Any, ...]) -> None:
        if event == "open":
            path, mode, flags = args
            writing = bool(flags & _OPEN_WRITE_FLAGS) if isinstance(flags, int) else bool(set(str(mode)) & set("wax+"))
            if writing and not self._allowed(path):
                self.refuse(f"open-for-write {path}")
        elif event == "os.mkdir":
            path = args[0]
            if not self._allowed(path) and not os.path.isdir(path):
                self.refuse(f"mkdir {path}")
        elif event in _FS_EVENTS:
            if not self._allowed(args[0]):
                self.refuse(f"{event} {args[0]}")
        elif event == "sqlite3.connect":
            database = os.fsdecode(args[0]) if isinstance(args[0], bytes) else str(args[0])
            self._pending.database = database
            self._check_hermetic(database)
            read_only = "mode=ro" in database or "mode=memory" in database or database in {"", ":memory:"}
            if not read_only:
                target = database.removeprefix("file:").split("?", 1)[0]
                if not os.path.exists(target) and not self._allowed(target):
                    self.refuse(f"sqlite-create {target}")
        elif event == "sqlite3.connect/handle":
            with self._lock:
                self.opened += 1

    def _check_hermetic(self, database: str) -> None:
        if self.store_root is None or "mode=memory" in database or database in {"", ":memory:"}:
            return
        path = unquote(urlsplit(database).path) if database.startswith("file:") else database
        real = os.path.realpath(path)
        if not (real == self.store_root or real.startswith(self.store_root + os.sep)):
            self.escapes.append(real)

    def _authorizer(self, database: str):
        in_memory = "mode=memory" in database or database in {"", ":memory:"}

        def authorize(action: int, arg1: str | None, arg2: str | None, db_name: str | None, _source: str | None):
            if in_memory or db_name == "temp":
                return sqlite3.SQLITE_OK
            if action in _SQLITE_WRITE_ACTIONS or (
                action == sqlite3.SQLITE_PRAGMA and arg1 in _PERSISTENT_PRAGMAS and arg2 is not None
            ):
                self.current.append(f"sqlite-write {action}:{arg1} on {os.path.basename(database.split('?')[0])}")
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        return authorize


def _sample(name: str, schema: dict[str, Any]) -> Any:
    if schema.get("enum"):
        return schema["enum"][0]
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = next((item for item in kind if item != "null"), "string")
    if kind == "array":
        return [_sample(name, schema.get("items") or {"type": "string"})]
    if kind == "object":
        return {
            key: _sample(key, sub)
            for key, sub in (schema.get("properties") or {}).items()
            if key in schema.get("required", [])
        }
    if kind == "integer":
        return 1
    if kind == "number":
        return 0.5
    if kind == "boolean":
        return False
    return "привіт"


def _arguments(tool: Any) -> dict[str, Any]:
    if tool.name in TOOL_ARGUMENTS:
        return dict(TOOL_ARGUMENTS[tool.name])
    schema = tool.input_schema or {}
    properties = schema.get("properties") or {}
    return {key: _sample(key, properties.get(key, {})) for key in schema.get("required", [])}


class _OneWorkerExecutor(ThreadPoolExecutor):
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        super().__init__(max_workers=1)


def _hermetic(scratch: Path, effects: SideEffects) -> None:
    import requests

    def fake_request(_session: Any, method: str, url: str, *_args: Any, **_kwargs: Any) -> requests.Response:
        effects.network.append(f"{method.upper()} {url.split('?')[0]}")
        content_type, body = fixture.fake_page(url)
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.headers["Content-Type"] = content_type
        response._content = body.encode("utf-8")
        response.encoding = "utf-8"
        return response

    requests.Session.request = fake_request  # type: ignore[method-assign]
    # Retry back-off on the empty stores and the DictUA courtesy pause would only add wall time.
    time.sleep = lambda _seconds: None  # type: ignore[assignment]
    # The server reaches these modules under both names (scripts/ and the repo root are on sys.path).
    redirects = {
        "SOURCES_DB_PATH": ("wiki.sources_db", "scripts.wiki.sources_db"),
        "_DEFAULT_DB": ("rag.wiki_cache", "scripts.rag.wiki_cache"),
        "VESUM_DB_PATH": ("rag.config", "scripts.rag.config", "scripts.verification.vesum"),
    }
    stores = {"SOURCES_DB_PATH": "sources.db", "_DEFAULT_DB": "wiki_cache.db", "VESUM_DB_PATH": "vesum.db"}
    for attribute, modules in redirects.items():
        for name in modules:
            setattr(importlib.import_module(name), attribute, scratch / stores[attribute])
    # search_sources fans its corpora out over threads sharing one connection. With the
    # probe's Python authorizer on that connection, a thread holding SQLite's mutex waits
    # for the GIL while another holds the GIL and waits for the mutex. One worker keeps
    # the same queries and writes without that deadlock (production has no authorizer).
    for name in ("wiki.sources_db", "scripts.wiki.sources_db"):
        importlib.import_module(name).ThreadPoolExecutor = _OneWorkerExecutor
    effects.store_root = os.path.realpath(scratch)


def _inject_writer(server: Any, tool: str) -> None:
    """Make ``tool`` store a row in the sources DB once its lookup has found the fixture row.

    The write is refused like any other, so the call then reports an error; the refused
    write is recorded only if the lookup before it succeeded.
    """
    handler_name = f"handle_{tool}"
    original = getattr(server, handler_name)

    async def lookup_then_write(args: dict) -> Any:
        result = await original(args)
        content = result[0] if isinstance(result, tuple) else result
        if HERMETIC_HITS[tool] not in "\n".join(block.text for block in content):
            return result
        conn = sqlite3.connect(os.environ[ENV_SOURCES_DB])
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS injected_cache (value TEXT)")
            conn.execute("INSERT INTO injected_cache VALUES (?)", (json.dumps(args, ensure_ascii=False),))
            conn.commit()
        finally:
            conn.close()
        return result

    setattr(server, handler_name, lookup_then_write)


def _record_network(effects: SideEffects) -> None:
    import requests

    original = requests.Session.request

    def recorded(session: Any, method: str, url: str, *args: Any, **kwargs: Any) -> Any:
        effects.network.append(f"{method.upper()} {url.split('?')[0]}")
        return original(session, method, url, *args, **kwargs)

    requests.Session.request = recorded  # type: ignore[method-assign]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--scratch", type=Path, required=True, help="Directory for the request log and hermetic stores."
    )
    parser.add_argument("--hermetic", action="store_true", help="Fake the network and use scratch stores.")
    parser.add_argument("--tool", action="append", default=[], help="Probe only this tool (repeatable).")
    parser.add_argument(
        "--inject-writer",
        metavar="TOOL",
        action="append",
        default=[],
        help="Mutation test: TOOL writes to the sources DB after its lookup (repeatable).",
    )
    args = parser.parse_args(argv)

    scratch = args.scratch.resolve()
    log_dir = scratch / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["LU_MCP_SOURCES_LOG_DIR"] = str(log_dir)
    for key in ("LU_REVIEW_ATTEMPT_ID", "LU_REVIEW_MANIFEST_SHA256", "LU_REVIEW_LEDGER_PATH", "LU_REVIEW_ACCESS"):
        os.environ.pop(key, None)
    sys.dont_write_bytecode = True

    if args.hermetic:
        fixture.build(scratch)
        # The store's own override, honoured by every resolver of the active sources DB.
        os.environ[ENV_SOURCES_DB] = str(scratch / "sources.db")
    effects = SideEffects([log_dir])
    # Before the server import, so a module that binds ``connect`` at import is guarded too.
    sqlite3.connect = effects.guard_connect(sqlite3.connect)  # type: ignore[assignment]
    spec = importlib.util.spec_from_file_location("sources_side_effects_server", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = server
    spec.loader.exec_module(server)
    if args.hermetic:
        _hermetic(scratch, effects)
    else:
        _record_network(effects)
    for name in args.inject_writer:
        _inject_writer(server, name)
    sys.addaudithook(effects.audit)

    tools = asyncio.run(server.list_tools())
    selected = [tool for tool in tools if not args.tool or tool.name in args.tool]
    for tool in selected:
        effects.current = []
        effects.network = []
        effects.escapes = []
        effects.opened = effects.guarded = 0
        arguments = _arguments(tool)
        content, is_error, _typed = asyncio.run(server._dispatch_tool_call(tool.name, dict(arguments)))
        text = "\n".join(block.text for block in content) if content else ""
        if effects.unguarded():
            effects.current.append("sqlite-connection opened without the write authorizer")
        print(
            json.dumps(
                {
                    "tool": tool.name,
                    "read_only_hint": tool.annotations.read_only_hint,
                    "destructive_hint": tool.annotations.destructive_hint,
                    "arguments": arguments,
                    "writes": sorted(set(effects.current)),
                    "network": sorted(set(effects.network)),
                    "escapes": sorted(set(effects.escapes)),
                    "is_error": is_error,
                    "hit": HERMETIC_HITS[tool.name] in text if args.hermetic and tool.name in HERMETIC_HITS else None,
                    "result_head": text[:160],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
