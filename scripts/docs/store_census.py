"""SQLite store registry and census (#11092, DB plan step 1).

The registry is the ``store_registry`` section of ``docs/knowledge/catalogue.yaml``:

* ``stores``: one row per named physical store file, present or declared in code but
  absent, with owner, kind, activity, write entry points (``file:function``), journal
  and busy settings, protection class, the nightly backup fact and retention.
* ``families``: stores whose path is chosen by a caller argument or a key, as a path
  rule plus, where one is knowable, a census glob in the catalogue glob dialect.
* ``evidence_dirs``: top-level ``batch_state/`` directories the census does not walk;
  their SQLite files are classified by the directory row (residual G1).
* ``non_stores``: SQLite-shaped files that are not project stores (zero-byte
  placeholders, coverage.py data, backup, test and experiment copies), by exact path
  or glob, so a new copy elsewhere is flagged instead of absorbed.

``registry_errors`` (static, CI) checks owners, that each write entry point is defined in
tracked code, that a recorded busy timeout equals what the writer (or the shared helper
named in ``busy_setters``) sets, that each backup fact equals what
``scripts/config/backup-allowlist.json`` selects (read only; DevOps owns that file), that
protection agrees with the backup fact, that examples match their globs and that every
SQLite ``data/`` store name in ``scripts/`` is registered.

``census`` (filesystem, read-only) walks ``data/``, ``.agent/``, ``.mcp/`` and
``batch_state/`` below a root, finds every SQLite file by extension (``.db``,
``.sqlite``, ``.sqlite3``) or by its 16-byte header, and flags files no row claims. With
``expect_present`` it also flags present-claimed stores that are missing, declared-absent
stores that exist, and a journal mode that disagrees with header byte 18. It reads at
most 100 bytes per file; coverage.py data is confirmed by its ``coverage_schema`` table
through a read-only, immutable open. Nothing is written, moved or locked. A directory
that cannot be walked or a file that cannot be read or vanishes mid-walk makes the scan
incomplete (never "not a store"); the report names it by relative path and error code.

Known limit (residual G1): stores written through a directory outside the walked roots
(``--db``, ``--work-dir`` or ``--state-dir`` elsewhere, temporary directories) are not
seen, and files inside evidence directories are classified by directory, not per file.
"""
from __future__ import annotations

import ast
import errno
import fnmatch
import os
import re
import sqlite3
import stat
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from scripts.docs import catalogue as cat
from scripts.lib.readonly_sqlite import open_readonly

REGISTRY_KEY = 'store_registry'
CENSUS_ROOTS = ('data', '.agent', '.mcp', 'batch_state')
SQLITE_SUFFIXES = ('.db', '.sqlite', '.sqlite3')
SQLITE_SIDECARS = ('-wal', '-shm', '-journal')
SQLITE_MAGIC = b'SQLite format 3\x00'
HEADER_BYTES = 100
GIT_COMMON_DIR = '<git-common-dir>'
ALLOWLIST_PATH = 'scripts/config/backup-allowlist.json'
# Header byte 18 (file format write version): 1 for a rollback journal, 2 for WAL.
JOURNAL_HEADER = {'delete': 1, 'wal': 2}
# task_record_is_staged in scripts/backup-data.sh: the only batch_state/tasks files the nightly stages.
TASK_RECORD_SUFFIXES = ('.json', '.result', '.diag', '.md', '.prompt')
# Connection openers whose ``timeout=`` (seconds) sets the busy timeout: sqlite3/aiosqlite
# ``connect``, scripts/api/resilience.connect_sqlite and scripts/control_plane/storage.connect
# (imported as cp_connect).
CONNECT_CALLS = frozenset({'connect', 'connect_sqlite', 'cp_connect'})
BUSY_PRAGMA = re.compile(r'PRAGMA\s+busy_timeout\s*=\s*([^\s;]+)', re.IGNORECASE)
UNEVALUATED = 'unevaluated'  # a busy setting whose value is not a literal or module constant


# ---------------------------------------------------------------- backup facts

def _segments_match(pattern: str, path: str) -> bool:
    """``path`` equals ``pattern`` segment by segment (a shell glob per segment, never across '/')."""
    want, have = pattern.split('/'), path.split('/')
    return len(want) == len(have) and all(fnmatch.fnmatchcase(h, w) for w, h in zip(want, have, strict=True))


def _under(root: str, path: str) -> bool:
    """``path`` lies strictly inside the tree ``root`` (whose segments may be shell globs)."""
    depth = len(root.split('/'))
    parts = path.split('/')
    return len(parts) > depth and _segments_match(root, '/'.join(parts[:depth]))


def _task_record_is_staged(path: str) -> bool:
    if path.endswith('.lock'):
        return False
    return path.startswith('batch_state/tasks/archive/') or path.endswith(TASK_RECORD_SUFFIXES)


def _selects(row: dict, path: str) -> bool:
    kind, root = row.get('kind'), row.get('path', '')
    if kind in ('file', 'glob_files'):
        return _segments_match(root, path)
    if kind == 'tree':
        return _under(root, path)
    if kind == 'task_records':
        return _under(root, path) and _task_record_is_staged(path)
    return False  # epic_glob names .claude/ epic directories, never a store


def backup_fact(path: str, allowlist: dict) -> str:
    """'keep' when a keep row stages ``path``, else 'drop' when a drop row names it, else 'none'.

    Mirrors the row kinds of scripts/backup-data.sh (file, tree, glob_files and the
    task_records filter); ``path`` is repository-relative.
    """
    if any(_selects(row, path) for row in allowlist.get('keep', [])):
        return 'keep'
    if any(_selects(row, path) for row in allowlist.get('drop', [])):
        return 'drop'
    return 'none'


# ---------------------------------------------------------------- claims

def registry(catalogue: dict) -> dict:
    return catalogue.get(REGISTRY_KEY) or {}


@dataclass(frozen=True)
class Claim:
    section: str  # stores | families | non_stores
    key: str  # the row's path or id
    row: dict


@dataclass(frozen=True)
class Claims:
    exact: dict[str, Claim]
    patterns: list[tuple[object, Claim]]

    @classmethod
    def of(cls, reg: dict) -> Claims:
        exact = {row['path']: Claim('stores', row['path'], row) for row in reg.get('stores', [])}
        for row in reg.get('non_stores', []):
            for path in row.get('paths', []):
                exact.setdefault(path, Claim('non_stores', row['id'], row))
        patterns = [(cat.glob_regex(row['glob']), Claim(section, row['id'], row))
                    for section in ('families', 'non_stores') for row in reg.get(section, [])
                    if row.get('glob') and cat.glob_error(row['glob']) is None]
        return cls(exact, patterns)

    def classify(self, path: str) -> Claim | None:
        """An exact row wins; then the first matching family glob, then the first non-store glob."""
        if path in self.exact:
            return self.exact[path]
        return next((claim for regex, claim in self.patterns if regex.match(path)), None)


def evidence_dir(path: str, reg: dict) -> dict | None:
    """The first evidence row whose directory equals ``path`` or contains it."""
    return next((row for row in reg.get('evidence_dirs', [])
                 if _segments_match(row['path'], path) or _under(row['path'], path)), None)


# ---------------------------------------------------------------- static validation

def _definition(tree: ast.Module, name: str) -> ast.AST | None:
    """The definition of ``name`` (``function`` or ``Class.method``) at module or class level."""
    scope: list[ast.stmt] = tree.body
    found: ast.AST | None = None
    for part in name.split('.'):
        found = next((n for n in scope if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                      and n.name == part), None)
        if found is None:
            return None
        scope = found.body
    return found


def _parse(source: str) -> ast.Module | None:
    try:
        return ast.parse(source)
    except (SyntaxError, ValueError):
        return None


def _writer_defined(source: str, name: str) -> bool:
    tree = _parse(source)
    return tree is not None and _definition(tree, name) is not None


def _number(node: ast.AST, constants: dict[str, float]) -> float | None:
    """A numeric literal, a module-level numeric constant, or a product or quotient of them."""
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div)):
        left, right = _number(node.left, constants), _number(node.right, constants)
        if left is None or right is None or (isinstance(node.op, ast.Div) and right == 0):
            return None
        return left * right if isinstance(node.op, ast.Mult) else left / right
    return None


def _module_constants(tree: ast.Module) -> dict[str, float]:
    constants: dict[str, float] = {}
    for stmt in tree.body:
        targets = (stmt.targets if isinstance(stmt, ast.Assign)
                   else [stmt.target] if isinstance(stmt, ast.AnnAssign) and stmt.value is not None else [])
        value = _number(stmt.value, constants) if targets else None
        for target in targets:
            if isinstance(target, ast.Name) and value is not None:
                constants[target.id] = value
    return constants


def _sql_text(node: ast.AST, constants: dict[str, float]) -> str | None:
    """A string literal, or an f-string whose fields are numeric constants ('?' otherwise)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    parts = []
    for value in node.values:
        if isinstance(value, ast.FormattedValue):
            number = _number(value.value, constants)
            parts.append('?' if number is None else f'{number:g}')
        else:
            parts.append(str(value.value))
    return ''.join(parts)


def _call_name(func: ast.AST) -> str | None:
    return func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None


def writer_busy_ms(source: str, name: str) -> int | str | None:
    """The busy timeout in ms that the last busy setting in ``name`` gives, in source order.

    A setting is a ``timeout=`` (seconds) on a CONNECT_CALLS call or a ``PRAGMA busy_timeout``
    passed to ``execute``. None when ``name`` sets none (it inherits a default or a helper's
    value); UNEVALUATED when the last setting is not a literal or module constant.
    """
    tree = _parse(source)
    node = _definition(tree, name) if tree is not None else None
    if node is None:
        return None
    constants = _module_constants(tree)
    settings: list[tuple[int, int, int | str]] = []
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        called = _call_name(call.func)
        if called in CONNECT_CALLS:
            for keyword in call.keywords:
                if keyword.arg == 'timeout':
                    seconds = _number(keyword.value, constants)
                    settings.append((call.lineno, call.col_offset,
                                     UNEVALUATED if seconds is None else round(seconds * 1000)))
        elif called in ('execute', 'executescript') and call.args:
            text = _sql_text(call.args[0], constants)
            if text is not None and (match := BUSY_PRAGMA.search(text)):
                try:
                    value: int | str = round(float(match.group(1)))
                except ValueError:
                    value = UNEVALUATED
                settings.append((call.lineno, call.col_offset, value))
    return max(settings, key=lambda setting: setting[:2])[2] if settings else None


def writer_files(catalogue: dict) -> set[str]:
    """Every file a write entry point or a busy setter names."""
    reg = registry(catalogue)
    return {w.partition(':')[0] for section in ('stores', 'families') for row in reg.get(section, [])
            for w in [*row.get('writers', []), *row.get('busy_setters', [])]}


def _where(section: str, row: dict) -> str:
    return f"{REGISTRY_KEY}.{section} {row.get('path') or row.get('id')!r}"


def registry_errors(catalogue: dict, tracked: set[str], owners: set[str], allowlist: dict,
                    sources: dict[str, str], literals: dict[str, list[str]] | None = None) -> list[str]:
    """Registry consistency. ``sources`` maps writer files to their text; a missing key is unreadable."""
    reg = registry(catalogue)
    if not reg:
        return []  # tests/test_store_census.py requires the repository catalogue to carry one
    errors: list[str] = []
    claims = Claims.of(reg)
    keys: Counter = Counter()
    family_ids = {row['id'] for row in reg.get('families', [])}
    entries = {e['id']: e for e in catalogue.get('entries', [])}

    def owner(here: str, row: dict) -> None:
        if row['owner'] not in owners:
            errors.append(f"{here}: owner {row['owner']!r} is not a stream or area key")

    def fact(here: str, path: str, declared: str) -> None:
        if (actual := backup_fact(path, allowlist)) != declared:
            errors.append(f'{here}: backup is {declared!r} but {ALLOWLIST_PATH} gives {actual!r} for {path!r}')

    def defined(here: str, label: str, refs: list[str]) -> list[str]:
        """The refs whose function is defined in a readable tracked file; errors for the rest."""
        good = []
        for ref in refs:
            path, _, name = ref.partition(':')
            if path not in tracked:
                errors.append(f'{here}: {label} {ref!r} names an untracked file')
            elif path not in sources:
                errors.append(f'{here}: {label} file {path!r} could not be read, so {name!r} is unverified')
            elif not _writer_defined(sources[path], name):
                errors.append(f'{here}: {label} {ref!r}: {name!r} is not defined in {path}')
            else:
                good.append(ref)
        return good

    def busy(here: str, row: dict, writers: list[str], setters: list[str]) -> None:
        """busy_ms equals what the code sets: each busy setter, else each writer, for an explicit
        source; a default source is wrong when a writer sets a timeout itself."""
        explicit, recorded = row['busy_source'] == 'explicit', row['busy_ms']
        if row.get('busy_setters') and not explicit:
            errors.append(f"{here}: busy_setters is for busy_source explicit, not {row['busy_source']!r}")
            return
        for ref in setters if row.get('busy_setters') else writers:
            path, _, name = ref.partition(':')
            value = writer_busy_ms(sources[path], name)
            if not explicit:
                if value is not None:
                    errors.append(f"{here}: busy_source {row['busy_source']!r} but {ref!r} sets the busy "
                                  f'timeout itself ({value}); record it as explicit')
            elif value is None:
                errors.append(f'{here}: busy_source explicit but {ref!r} sets no busy timeout; name the '
                              'shared helper that sets it in busy_setters')
            elif value == UNEVALUATED:
                errors.append(f'{here}: {ref!r} sets the busy timeout from a value the check cannot evaluate; '
                              'name the function that sets a literal or module constant in busy_setters')
            elif value != recorded:
                errors.append(f'{here}: busy_ms {recorded} but {ref!r} sets {value} (its last busy setting)')

    def store_like(section: str, row: dict) -> None:
        here = _where(section, row)
        owner(here, row)
        writers = defined(here, 'writer', row.get('writers', []))
        setters = defined(here, 'busy setter', row.get('busy_setters', []))
        if not row.get('writers') and not row.get('writer_note'):
            errors.append(f'{here}: no writers, so writer_note must say why')
        if (row['busy_ms'] is None) != (row['busy_source'] in ('no_writer', 'not_applicable')):
            errors.append(f"{here}: busy_ms is null exactly when busy_source is no_writer or not_applicable")
        busy(here, row, writers, setters)
        protection, backup = row['protection'], row['backup']
        if backup == 'keep' and protection != 'keep':
            errors.append(f'{here}: the nightly keeps it (backup keep) but protection is {protection!r}; '
                          'a lower class is a backup reduction (operator-authorized, DB plan step 6)')
        if backup != 'keep' and protection == 'keep' and not row.get('protection_gap'):
            errors.append(f'{here}: protection keep while the nightly does not keep it needs protection_gap')
        if backup == 'keep' and row.get('protection_gap'):
            errors.append(f'{here}: protection_gap is set but the nightly already keeps it; remove the gap')

    for row in reg.get('stores', []):
        here = _where('stores', row)
        keys[row['path']] += 1
        store_like('stores', row)
        present = row['presence'] == 'present'
        if present == (row['activity'] == 'not_created'):
            errors.append(f'{here}: activity not_created is for declared-absent stores only')
        if not present and not row.get('absent_reason'):
            errors.append(f'{here}: a declared-absent store needs absent_reason')
        if present and row['journal'] == 'unknown':
            errors.append(f'{here}: a present store records its journal mode (wal or delete)')
        if row['kind'] in ('staged', 'orphan') and row['activity'] != row['kind']:
            errors.append(f"{here}: kind {row['kind']!r} needs activity {row['kind']!r}")
        if row['path'].startswith(GIT_COMMON_DIR + '/'):
            if row['backup'] != 'none':
                errors.append(f'{here}: the Git common directory is outside every allowlist root, so backup is none')
        else:
            fact(here, row['path'], row['backup'])
            if PurePosixPath(row['path']).parts[0] in CENSUS_ROOTS and evidence_dir(row['path'], reg) is not None:
                errors.append(f'{here}: lies inside an evidence directory, which the census never walks')
        if row.get('family') is not None and row['family'] not in family_ids:
            errors.append(f"{here}: family {row['family']!r} is not a families row")
        if (entry_id := row.get('catalogue_entry')) is not None:
            entry = entries.get(entry_id)
            names = entry.get('store', []) if entry and entry.get('kind') == 'data_store' else None
            if names is None:
                errors.append(f'{here}: catalogue_entry {entry_id!r} is not a data_store entry')
            elif not any((rx := cat.store_regex(s)) is not None and rx.match(row['path']) for s in names):
                errors.append(f"{here}: catalogue_entry {entry_id!r} does not claim {row['path']!r}")

    for section in ('families', 'non_stores'):
        for row in reg.get(section, []):
            here = _where(section, row)
            keys[row['id']] += 1
            if section == 'families':
                store_like(section, row)
            else:
                owner(here, row)
                for path in row.get('paths', []):
                    keys[path] += 1
                    fact(here, path, row['backup'])
            glob, example = row.get('glob'), row.get('example')
            if section == 'non_stores' and bool(glob) == bool(row.get('paths')):
                errors.append(f'{here}: a non-store row has either a glob or paths')
            if not glob:
                if example is not None:
                    errors.append(f'{here}: an example needs a glob')
                continue
            if (error := cat.glob_error(glob)) is not None:
                errors.append(f'{here}: glob {glob!r} is outside the catalogue glob dialect: {error}')
                continue
            if PurePosixPath(glob).parts[0] not in CENSUS_ROOTS:
                errors.append(f'{here}: glob {glob!r} is outside the census roots {", ".join(CENSUS_ROOTS)}')
            if example is None:
                errors.append(f'{here}: a glob row needs an example path')
                continue
            if not cat.glob_regex(glob).match(example):
                errors.append(f'{here}: example {example!r} does not match glob {glob!r}')
            fact(here, example, row['backup'])
            claim = claims.classify(example)
            owned = claim is not None and (claim.row is row or claim.row.get('family') == row.get('id'))
            if not owned:
                errors.append(f"{here}: example {example!r} resolves to {claim.key if claim else None!r}, "
                              'not this row (an earlier glob shadows it)')

    for row in reg.get('evidence_dirs', []):
        here = _where('evidence_dirs', row)
        keys[row['path']] += 1
        owner(here, row)
        if not row['path'].startswith('batch_state/') or row['path'].count('/') != 1:
            errors.append(f'{here}: evidence directories are top-level batch_state/ directories')
        if not _under(row['path'], row['example']):
            errors.append(f"{here}: example {row['example']!r} is not inside {row['path']!r}")
        elif (first := evidence_dir(row['example'], reg)) is not row:
            errors.append(f"{here}: example {row['example']!r} resolves to the earlier row {first['path']!r}")
        fact(here, row['example'], row['backup'])

    errors.extend(f'{REGISTRY_KEY}: {key!r} is registered {n} times' for key, n in sorted(keys.items()) if n > 1)
    if literals is not None:
        errors.extend(_literal_errors(catalogue, reg, claims, literals))
    return errors


def _literal_errors(catalogue: dict, reg: dict, claims: Claims, literals: dict[str, list[str]]) -> list[str]:
    """Every SQLite ``data/`` store name in scripts/ is a registered store, a family glob or literal,
    or a store_literal_exemptions item."""
    exempt = {item['literal'] for item in catalogue.get('store_literal_exemptions', [])}
    named = {lit for row in reg.get('families', []) for lit in row.get('literals', [])}
    errors = []
    for store, paths in sorted(literals.items()):
        if not store.endswith(SQLITE_SUFFIXES) or store in exempt or store in named:
            continue
        claim = claims.classify(store)
        if claim is None or claim.section == 'non_stores':
            errors.append(f'{REGISTRY_KEY}: SQLite store {store!r} (named in {", ".join(paths[:3])}) has no '
                          'stores row or families glob or literal')
    for literal in sorted(named - set(literals)):
        errors.append(f'{REGISTRY_KEY}: family literal {literal!r} is no longer named in scripts/; remove it')
    return errors


# ---------------------------------------------------------------- filesystem census

@dataclass
class Census:
    root: str
    presence_checked: bool = False
    walked_roots: list[str] = field(default_factory=list)
    found: dict[str, str] = field(default_factory=dict)  # path -> claiming section, or 'unregistered'
    unregistered: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)  # files that contradict the row claiming them
    present: list[str] = field(default_factory=list)  # store rows found
    missing: list[str] = field(default_factory=list)  # present-claimed store rows not found
    evidence: list[str] = field(default_factory=list)  # evidence directories present, not walked
    # Paths the walk could not read: {'code', 'path' (relative), 'reason' (errno name)}.
    incomplete: list[dict] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.incomplete

    @property
    def ok(self) -> bool:
        return (self.complete and not self.unregistered and not self.problems
                and not (self.presence_checked and self.missing))

    def unreadable(self, code: str, logical: str, exc: OSError) -> None:
        """Record a path the census could not read; the scan is then incomplete, never passing."""
        reason = errno.errorcode.get(exc.errno, type(exc).__name__) if exc.errno else type(exc).__name__
        self.incomplete.append({'code': code, 'path': logical, 'reason': reason})

    def counts(self, reg: dict) -> dict:
        rows = {row['path']: row for row in reg.get('stores', [])}
        present = [rows[p] for p in self.present]
        return {
            'files_found': len(self.found),
            'by_claim': dict(sorted(Counter(self.found.values()).items())),
            'named_stores_present': len(present),
            'by_activity': dict(sorted(Counter(r['activity'] for r in present).items())),
            'active_by_kind': dict(sorted(Counter(r['kind'] for r in present if r['activity'] == 'active').items())),
            'declared_absent_rows': sum(r['presence'] == 'declared_absent' for r in rows.values()),
            'family_rows': len(reg.get('families', [])),
            'unregistered': len(self.unregistered),
            'problems': len(self.problems),
            'missing': len(self.missing) if self.presence_checked else None,
            'evidence_dirs_not_walked': len(self.evidence),
            'unreadable': len(self.incomplete),
        }

    def to_json(self, reg: dict) -> dict:
        return {'root_walked': sorted(self.walked_roots), 'presence_checked': self.presence_checked,
                'counts': self.counts(reg), 'unregistered': self.unregistered, 'problems': self.problems,
                'missing': self.missing if self.presence_checked else None,
                'evidence_dirs_not_walked': self.evidence, 'complete': self.complete,
                'incomplete': self.incomplete, 'ok': self.ok}


def _header(path: Path) -> bytes:
    """At most HEADER_BYTES of ``path``; OSError (unreadable, vanished) propagates to the caller."""
    with path.open('rb') as handle:
        return handle.read(HEADER_BYTES)


def _read_header(result: Census, logical: str, path: Path) -> bytes | None:
    """The header, or None after recording why it could not be read."""
    try:
        return _header(path)
    except FileNotFoundError as exc:
        result.unreadable('vanished_file', logical, exc)
    except OSError as exc:
        result.unreadable('unreadable_file', logical, exc)
    return None


def _is_coverage_data(path: Path) -> bool:
    """coverage.py data has a ``coverage_schema`` table; read through a read-only, immutable open."""
    try:
        conn = open_readonly(path, immutable=True)
    except sqlite3.Error:
        return False
    try:
        return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'coverage_schema'"
                            ).fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def _resolve(root: Path, logical: str) -> Path | None:
    """A registry path on disk; ``<git-common-dir>/`` resolves through ``git rev-parse``."""
    if not logical.startswith(GIT_COMMON_DIR + '/'):
        return root / logical
    try:
        out = subprocess.run(['git', '-C', str(root), 'rev-parse', '--git-common-dir'], capture_output=True,
                             text=True, check=True, timeout=30).stdout.removesuffix('\n')
    except (OSError, subprocess.SubprocessError):
        return None
    common = Path(out)
    return (common if common.is_absolute() else root / common) / logical.split('/', 1)[1]


def _lstat_mode(result: Census, kind: str, logical: str, path: Path) -> int | None:
    """The ``lstat`` mode of ``path``, or None after recording a vanished or unreadable ``kind``."""
    try:
        return path.lstat().st_mode
    except FileNotFoundError as exc:
        result.unreadable(f'vanished_{kind}', logical, exc)
    except OSError as exc:
        result.unreadable(f'unreadable_{kind}', logical, exc)
    return None


def _files(root: Path, top: str, reg: dict, result: Census):
    """(logical path, Path) for every regular file below ``root/top``; symlinks and evidence dirs pruned.

    A directory the walk cannot list and an entry it cannot stat are recorded in
    ``result.incomplete`` (os.walk would otherwise skip them silently).
    """
    def walk_error(exc: OSError) -> None:
        try:
            logical = Path(os.fsdecode(exc.filename)).relative_to(root).as_posix()
        except (TypeError, ValueError):
            logical = top
        kind = 'vanished' if isinstance(exc, FileNotFoundError) else 'unreadable'
        result.unreadable(f'{kind}_directory', logical, exc)

    for directory, dirs, files in os.walk(root / top, onerror=walk_error, followlinks=False):
        rel = Path(directory).relative_to(root).as_posix()
        kept = []
        for name in sorted(dirs):
            logical = f'{rel}/{name}'
            mode = _lstat_mode(result, 'directory', logical, root / logical)
            if mode is None or stat.S_ISLNK(mode):
                continue
            row = evidence_dir(logical, reg)
            if row is not None and _segments_match(row['path'], logical):
                result.evidence.append(logical)
                continue
            kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            logical, path = f'{rel}/{name}', Path(directory) / name
            mode = _lstat_mode(result, 'file', logical, path)
            if mode is not None and stat.S_ISREG(mode):
                yield logical, path


def census(root: Path, catalogue: dict, *, expect_present: bool = False) -> Census:
    """Every SQLite file under the census roots of ``root``, classified against the registry."""
    reg = registry(catalogue)
    claims = Claims.of(reg)
    result = Census(root=str(root), presence_checked=expect_present)
    for top in CENSUS_ROOTS:
        if not (root / top).is_dir() or (root / top).is_symlink():
            continue
        result.walked_roots.append(top)
        for logical, path in _files(root, top, reg, result):
            if logical.endswith(SQLITE_SIDECARS):
                continue
            header = _read_header(result, logical, path)
            if header is None:
                continue  # recorded as incomplete: an unreadable file is never "not a store"
            if not (header.startswith(SQLITE_MAGIC) or logical.lower().endswith(SQLITE_SUFFIXES)):
                continue
            claim = claims.classify(logical)
            result.found[logical] = claim.section if claim else 'unregistered'
            if claim is None:
                result.unregistered.append(logical)
            else:
                _check_claim(result, logical, path, header, claim)
    for row in reg.get('stores', []):
        logical = row['path']
        if PurePosixPath(logical).parts[0] in CENSUS_ROOTS:
            exists = logical in result.found
        else:
            resolved = _resolve(root, logical)
            exists = resolved is not None and resolved.is_file() and not resolved.is_symlink()
            if exists and (header := _read_header(result, logical, resolved)) is not None:
                _check_claim(result, logical, resolved, header, Claim('stores', logical, row))
        if row['presence'] == 'present':
            (result.present if exists else result.missing).append(logical)
        elif exists:
            result.problems.append(f'{logical}: registered as declared_absent but present; update its row')
    result.unregistered.sort()
    return result


def _check_claim(result: Census, logical: str, path: Path, header: bytes, claim: Claim) -> None:
    row, is_sqlite = claim.row, header.startswith(SQLITE_MAGIC)
    if claim.section == 'non_stores':
        if row['class'] == 'zero_byte_placeholder' and header:
            result.problems.append(f'{logical}: registered as a zero-byte placeholder but is not empty')
        elif row['class'] == 'coverage_data' and not (is_sqlite and _is_coverage_data(path)):
            result.problems.append(f'{logical}: matches a coverage.py data row but is not coverage.py data')
        return
    if claim.section == 'stores' and result.presence_checked and (declared := JOURNAL_HEADER.get(row['journal'])):
        actual = header[18] if is_sqlite and len(header) > 18 else None
        if actual != declared:
            result.problems.append(f"{logical}: registry journal {row['journal']!r} but header byte 18 is "
                                   f'{actual!r} (1 rollback journal, 2 WAL)')


def census_lines(result: Census, reg: dict) -> list[str]:
    """The plain-text census report."""
    counts = result.counts(reg)

    def listed(mapping: dict) -> str:
        return ', '.join(f'{k} {v}' for k, v in mapping.items()) or 'none'

    lines = [f"census roots walked: {', '.join(result.walked_roots) or 'none'}; SQLite files found "
             f"{counts['files_found']} ({listed(counts['by_claim'])})",
             f"named stores present {counts['named_stores_present']} ({listed(counts['by_activity'])}); "
             f"active by kind: {listed(counts['active_by_kind'])}",
             f"declared-absent rows {counts['declared_absent_rows']}; family rows {counts['family_rows']}; "
             f"evidence directories not walked {counts['evidence_dirs_not_walked']}",
             'presence: ' + (f"checked, {counts['missing']} missing" if result.presence_checked
                             else 'not checked (pass --expect-present on the store host)')]
    if not result.complete:
        lines.append(f'scan: INCOMPLETE, {len(result.incomplete)} path(s) could not be read; the census proves '
                     'nothing until they are readable')
    lines += [f"INCOMPLETE SCAN {item['code']} {item['path']} ({item['reason']})" for item in result.incomplete]
    lines += [f'UNREGISTERED SQLITE {p}' for p in result.unregistered]
    lines += [f'REGISTRY MISMATCH {p}' for p in result.problems]
    if result.presence_checked:
        lines += [f'MISSING STORE {p}' for p in result.missing]
    return lines
