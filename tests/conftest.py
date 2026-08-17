"""
Pytest configuration and shared fixtures for audit tests.

Provides reusable content snippets and module templates for testing.
"""

import contextlib
import ipaddress
import os
import socket
import sqlite3
import sys
from collections.abc import Collection
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _get_breadcrumb_file() -> Path | None:
    breadcrumb_dir_str = os.environ.get("PYTEST_BREADCRUMB_DIR", ".pytest_breadcrumbs")
    if not breadcrumb_dir_str:
        return None
    dir_path = Path(breadcrumb_dir_str)
    dir_path.mkdir(parents=True, exist_ok=True)
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    return dir_path / f"breadcrumb_{worker_id}.txt"


def _append_breadcrumb(line: str) -> None:
    breadcrumb_file = _get_breadcrumb_file()
    if breadcrumb_file:
        with open(breadcrumb_file, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            with contextlib.suppress(OSError):
                os.fsync(f.fileno())


def pytest_runtest_logstart(nodeid: str, location: tuple[str, int | None, str]) -> None:
    _append_breadcrumb(f"START {nodeid}\n")


def pytest_runtest_logfinish(nodeid: str, location: tuple[str, int | None, str]) -> None:
    _append_breadcrumb(f"FINISH {nodeid}\n")



def _require_data_artifact(
    relative_path: str,
    *,
    required_sqlite_tables: Collection[str] = (),
) -> Path:
    """Return a local data artifact or skip tests that cannot run without it."""
    data_root = Path(os.environ.get("LEARN_UKRAINIAN_TEST_DATA_ROOT", _REPO_ROOT))
    artifact = data_root / relative_path
    if not artifact.is_file():
        pytest.skip(f"requires {relative_path} (not provisioned in CI)")

    if required_sqlite_tables:
        try:
            with sqlite3.connect(f"file:{artifact}?mode=ro", uri=True) as connection:
                available_tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
        except sqlite3.Error:
            available_tables = set()
        missing_tables = sorted(set(required_sqlite_tables) - available_tables)
        if missing_tables:
            pytest.skip(
                f"requires {relative_path} with SQLite tables: "
                f"{', '.join(missing_tables)} (not provisioned in CI)"
            )
    return artifact


@pytest.fixture
def requires_sources_db() -> Path:
    """Skip a test requiring the complete uncommitted sources corpus database."""
    return _require_data_artifact(
        "data/sources.db",
        required_sqlite_tables=(
            "external_articles",
            "external_fts",
            "literary_fts",
            "literary_texts",
            "textbook_sections",
            "textbooks",
            "textbooks_fts",
            "ukrainian_wiki",
            "ukrainian_wiki_fts",
            "wikipedia",
            "wikipedia_fts",
        ),
    )


@pytest.fixture
def requires_vesum_db() -> Path:
    """Skip a test requiring the uncommitted VESUM database."""
    return _require_data_artifact("data/vesum.db", required_sqlite_tables=("forms",))


@pytest.fixture
def requires_literary_wave12_jsonl() -> Path:
    """Skip a test requiring the uncommitted Wave 12 literary corpus fixture."""
    return _require_data_artifact(
        "data/literary_texts/wave12-krupnytsky-orlyk-biohrafiia.jsonl"
    )


@pytest.fixture(autouse=True)
def _isolate_llm_qg_runtime_stores(tmp_path, monkeypatch):
    """Every test writes llm_qg runtime state (DB + circuit sidecar) to tmp_path.

    Root cause (2026-07-07): llm_qg_store resolves its stores via env-var-or-
    PROJECT_ROOT-default; tests exercising qg_workflow/store paths without
    overriding the env minted data/telemetry/llm_qg_live_circuit.json in every
    checkout/worktree they ran in — one such stray got swept into PR #4743 by
    git add -A. Hermetic by default; tests that need a specific path still
    monkeypatch their own.
    """
    monkeypatch.setenv("LEARN_UKRAINIAN_LLM_QG_DB", str(tmp_path / "llm_qg.db"))
    monkeypatch.setenv("LEARN_UKRAINIAN_LLM_QG_CIRCUIT", str(tmp_path / "llm_qg_live_circuit.json"))


@pytest.fixture(autouse=True)
def _isolate_write_ownership_ledger(tmp_path_factory, monkeypatch):
    """Every test gets its own write-path ownership ledger.

    Root cause (2026-07-25): the ledger path was a module constant baked into
    default arguments, so the suite admitted against the LIVE fleet ledger in
    batch_state/. Dispatch tests then saw whatever real dispatches happened to
    be running: eight of them failed on a busy machine and passed on an idle
    one, which is indistinguishable from flakiness and silently erodes the
    pre-push pytest signal. Tests that want the real ledger override this.

    The directory comes from ``tmp_path_factory``, NOT from the test's own
    ``tmp_path``: an autouse fixture that creates a subdirectory there breaks
    every test asserting its ``tmp_path`` is empty. Caught in CI by
    test_grok_envelope_failure_skips_forensics_when_unconfigured after the
    first version of this fixture did exactly that.
    """
    ledger_dir = tmp_path_factory.mktemp("write-ownership")
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(ledger_dir / "write-ownership.sqlite3"))
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_TASK_STATE_DIR", str(ledger_dir))


class SocketBlockedError(RuntimeError):
    """Raised when a unit test attempts an un-opted outbound network connection (#6968)."""


def _is_localhost_host(host: object) -> bool:
    """Return True if host is loopback or local machine identifier."""
    if not host:
        return True
    if isinstance(host, bytes):
        try:
            host = host.decode("utf-8")
        except UnicodeDecodeError:
            return False
    if not isinstance(host, str):
        return False

    host_lower = host.lower()
    if host_lower in {"localhost", "127.0.0.1", "::1", "0.0.0.0", "::"}:
        return True
    if host_lower.endswith(".localhost"):
        return True
    with contextlib.suppress(OSError):
        if host_lower in {socket.gethostname().lower(), socket.getfqdn().lower()}:
            return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_unspecified
    except ValueError:
        return False


def _is_localhost_address(address: object) -> bool:
    """Return True if address is AF_UNIX (str/bytes) or AF_INET(6) pointing to localhost."""
    if address is None:
        return True
    if isinstance(address, (str, bytes)):
        return True
    if isinstance(address, tuple) and address:
        return _is_localhost_host(address[0])
    return False


_ORIG_SOCKET_CONNECT = socket.socket.connect
_ORIG_SOCKET_CONNECT_EX = socket.socket.connect_ex
_ORIG_SOCKET_SENDTO = socket.socket.sendto


def _guarded_connect(sock_self: socket.socket, address: object) -> object:
    if getattr(sock_self, "family", None) == getattr(socket, "AF_UNIX", None):
        return _ORIG_SOCKET_CONNECT(sock_self, address)
    if _is_localhost_address(address):
        return _ORIG_SOCKET_CONNECT(sock_self, address)
    host = address[0] if isinstance(address, tuple) and address else address
    raise SocketBlockedError(
        f"Outbound network connection to '{host}' blocked by socket-guard. "
        f"Unit tests must be hermetic and not rely on live external services. "
        f"If this test legitimately requires live network, mark it with @pytest.mark.live_network."
    )


def _guarded_connect_ex(sock_self: socket.socket, address: object) -> int:
    if getattr(sock_self, "family", None) == getattr(socket, "AF_UNIX", None):
        return _ORIG_SOCKET_CONNECT_EX(sock_self, address)
    if _is_localhost_address(address):
        return _ORIG_SOCKET_CONNECT_EX(sock_self, address)
    host = address[0] if isinstance(address, tuple) and address else address
    raise SocketBlockedError(
        f"Outbound network connection to '{host}' blocked by socket-guard. "
        f"Unit tests must be hermetic and not rely on live external services. "
        f"If this test legitimately requires live network, mark it with @pytest.mark.live_network."
    )


def _guarded_sendto(sock_self: socket.socket, data: bytes, *args: object) -> int:
    address = args[-1] if args else None
    if (
        address is not None
        and getattr(sock_self, "family", None) != getattr(socket, "AF_UNIX", None)
        and not _is_localhost_address(address)
    ):
        host = address[0] if isinstance(address, tuple) and address else address
        raise SocketBlockedError(
            f"Outbound network connection to '{host}' blocked by socket-guard. "
            f"Unit tests must be hermetic and not rely on live external services. "
            f"If this test legitimately requires live network, mark it with @pytest.mark.live_network."
        )
    return _ORIG_SOCKET_SENDTO(sock_self, data, *args)


@pytest.fixture(autouse=True)
def _socket_guard(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse outbound network connections to non-localhost hosts in unit tests (#6968).

    Tests that legitimately make live network requests must be explicitly
    marked with ``@pytest.mark.live_network``.
    """
    if request.node.get_closest_marker("live_network"):
        return
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", _guarded_connect_ex)
    monkeypatch.setattr(socket.socket, "sendto", _guarded_sendto)


# =============================================================================
# MODULE TEMPLATES
# =============================================================================

@pytest.fixture
def minimal_module_b1():
    """Minimal valid B1 module structure."""
    return """---
module: 1
title: Test Module
level: B1
pedagogy: PPP
cefr: B1.1
phase: Grammar
objectives:
  - Test objective
---

# Presentation

This is the presentation section with content.

# Practice

Practice content here.

# Production

Production content here.

# Vocabulary

| Слово | Переклад | Примітки |
|-------|----------|----------|
| слово | word | noun |
"""


@pytest.fixture
def minimal_module_a1():
    """Minimal valid A1 module structure."""
    return """---
module: 1
title: Test Module
level: A1
pedagogy: PPP
cefr: A1.1
phase: Basics
objectives:
  - Test objective
---

# Presentation

This is the presentation section with content.

# Practice

Practice content here.

# Production

Production content here.

# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
"""


# =============================================================================
# ACTIVITY SNIPPETS
# =============================================================================

@pytest.fixture
def valid_quiz_b1():
    """Valid B1 quiz with proper word counts."""
    return """
## quiz: Частини мови

1. Яка частина мови в українській граматиці називає предмети та поняття для опису світу?
   - [x] Іменник
   - [ ] Дієслово
   - [ ] Прикметник
   - [ ] Прислівник

2. Яка частина мови в українській мові позначає дію або стан суб'єкта речення?
   - [ ] Іменник
   - [x] Дієслово
   - [ ] Прикметник
   - [ ] Прислівник
"""


@pytest.fixture
def valid_error_correction():
    """Valid error-correction with all required callouts."""
    return """
## error-correction: Виправлення

1. Він ходить до школа.
   > [!error] школа
   > [!answer] школи
   > [!options] школа | школи | школу | школою
   > [!explanation] Після прийменника "до" вживаємо родовий відмінок.

2. Вона читає книгу на стіл.
   > [!error] стіл
   > [!answer] столі
   > [!options] стіл | столі | столу | столом
   > [!explanation] Після прийменника "на" (місце) вживаємо місцевий відмінок.
"""


@pytest.fixture
def valid_unjumble():
    """Valid unjumble with answer callout."""
    return """
## unjumble: Речення

1. я / люблю / Україну / дуже / сильно
   > [!answer] Я дуже сильно люблю Україну.

2. вона / читає / книгу / цікаву / про / історію
   > [!answer] Вона читає цікаву книгу про історію.
"""


@pytest.fixture
def valid_match_up():
    """Valid match-up with proper pairs."""
    return """
## match-up: Терміни

| Термін | Переклад |
|--------|----------|
| слово | word |
| речення | sentence |
| граматика | grammar |
| відмінок | case |
| дієслово | verb |
| іменник | noun |
| прикметник | adjective |
| прислівник | adverb |
| займенник | pronoun |
| сполучник | conjunction |
"""


# =============================================================================
# VOCABULARY FIXTURES
# =============================================================================

@pytest.fixture
def valid_vocab_table_b1():
    """Valid B1 vocabulary table (3 columns)."""
    return """
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
| відмінок | case | noun |
| дієслово | verb | noun |
| іменник | noun | noun |
"""


@pytest.fixture
def valid_vocab_table_a1():
    """Valid A1 vocabulary table (6 columns with IPA)."""
    return """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
| читати | /tʃɪˈtatɪ/ | to read | verb | - | impf |
"""


@pytest.fixture
def invalid_vocab_missing_ipa():
    """Invalid A1 vocabulary - missing IPA."""
    return """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
"""


# =============================================================================
# CONTENT WITH ISSUES
# =============================================================================

@pytest.fixture
def content_with_russian_chars():
    """Content with Russian-only characters."""
    return """---
module: 1
title: Test
level: B1
---

# Test

Прикметник "красивый" не є українським.
"""


@pytest.fixture
def content_clean_ukrainian():
    """Clean Ukrainian content without Russian chars."""
    return """---
module: 1
title: Test
level: B1
---

# Test

Прикметник "красивий" є українським словом.
Граматика української мови цікава.
"""


@pytest.fixture
def quiz_with_short_prompts():
    """Quiz with prompts that are too short for B1."""
    return """
## quiz: Тест

1. Яка це частина мови?
   - [x] Іменник
   - [ ] Дієслово

2. Що це таке?
   - [x] Граматика
   - [ ] Лексика
"""


# =============================================================================
# PPP STRUCTURE FIXTURES
# =============================================================================

@pytest.fixture
def valid_ppp_structure():
    """Content with valid PPP structure."""
    return """---
module: 1
title: Test
level: B1
pedagogy: PPP
---

# Presentation

Content here.

# Practice

Practice content.

# Production

Production content.
"""


@pytest.fixture
def invalid_ppp_missing_section():
    """PPP content missing Production section."""
    return """---
module: 1
title: Test
level: B1
pedagogy: PPP
---

# Presentation

Content here.

# Practice

Practice content.
"""


@pytest.fixture(autouse=True)
def _enable_formal_shielded_cf_for_unit_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit tests may still exercise isolation helpers; production CLI stays retired.

    Production / drivers leave LU_FORMAL_SHIELDED_CF unset so review-pr refuses.
    """
    monkeypatch.setenv("LU_FORMAL_SHIELDED_CF", "1")
