"""Document and data catalogue: load, validate and measure coverage (#9412).

The catalogue (``docs/knowledge/catalogue.yaml``) records document *families*
and logical *data stores*, not one entry per file. It extends the ADR-013
inventory (``scripts/docs/docs_inventory.py``) and the lifecycle contract in
``docs/architecture/docs-authority-lifecycle.md``; it does not replace them.

The coverage denominator is every path Git's index lists under the tracked
roots, so the check is sparse-checkout safe and never reads ``data/``.

``repository_check`` is what CI enforces (``tests/test_docs_catalogue_coverage.py``):
coverage and validation, a data_store entry for every ``data/`` store that a tracked
file under ``scripts/`` names, front matter and banners that agree with the
catalogue's superseded overrides, and a current generated family table in
``docs/README.md``. The search over all of it is ``scripts/docs/find.py``.

Store-name scan dialect (``store_literals``). Surface: every path Git's index lists
under ``scripts/``, any extension or none, read as its index blob through the privacy
gate; binary blobs are skipped, unreadable or withheld files fail the check. A store
name is ``data/<segments>.db|.sqlite|.sqlite3|.duckdb`` where ``data/`` is not preceded
by a word character, ``.`` or ``-``. Segment characters are anything except whitespace,
controls, quotes, ``<>|``, the shell terminators ``;&()``, ``{}$*?[]`` and ``\\``; a
backslash-escaped space is admitted in a shell word, and plain inner spaces inside a
single-line quoted span. ``.`` and ``..`` segments never name a store. Comments count.
Python path joins (``ROOT / "data" / "x.db"``) are read from the AST. Known limits: a
name assembled at run time (f-string fields, concatenation, variables, shell
expansions, globs) is not a literal and is covered only by the producers a data_store
entry declares; a quoted name with spaces that spans lines or sits inside mismatched
quotes (an apostrophe in prose) can be missed or over-read.
"""
from __future__ import annotations

import argparse
import ast
import json
import posixpath
import re
import shlex
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from scripts.docs.docs_inventory import EXCLUDED_PARTS
from scripts.docs.docs_inventory import metadata as inventory_metadata

CATALOGUE_PATH = 'docs/knowledge/catalogue.yaml'
SCHEMA_PATH = 'docs/knowledge/catalogue.schema.json'
TRACKED_ROOTS = ('docs', 'registry', 'curriculum/l2-uk-en/evidence')
OWNER_SOURCES = (('scripts/config/issue_streams.yaml', 'streams'),
                 ('scripts/config/area_assignments.yaml', 'assignments'))
TERMINAL_LIFECYCLES = frozenset({'active', 'archive'})
SQLITE_SIDECARS = ('-shm', '-wal', '-journal')
PLACEHOLDER_NAMES = frozenset({'.gitkeep', '.gitignore'})
WILDCARD = re.compile(r'[*?]')
# Characters outside the glob dialect: class/brace syntax and control characters.
FORBIDDEN_GLOB_CHARS = re.compile(r'[\[\]{}\x00-\x1f\x7f-\x9f]')
# C0, DEL and C1 controls (Unicode category Cc). A tracked path containing one is a
# validation error and is never catalogued, read or printed unescaped.
CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f-\x9f]')
# A full SHA-1 or SHA-256 object ID, the only thing ever written to a Git request.
OBJECT_ID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
REGULAR_MODES = frozenset({'100644', '100755'})


class GitProtocolError(subprocess.SubprocessError):
    """Git output is not the shape the reader requested; ``code`` names the rule."""

    def __init__(self, code: str, message: str):
        super().__init__(f'{code}: {message}')
        self.code = code


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL, timeout=60)


def toplevel(repo: Path) -> Path:
    """The worktree root; only Git's record terminator is removed, never path characters."""
    return Path(git(repo, 'rev-parse', '--show-toplevel').decode('utf-8').removesuffix('\n'))


@dataclass(frozen=True)
class IndexEntry:
    mode: str
    oid: str


def index_entries(repo: Path) -> dict[str, IndexEntry]:
    """Every path in Git's index (includes skip-worktree sparse paths) with its mode and object ID.

    Records come from NUL-separated ``ls-files -z --stage``; pathnames are data, split on
    NUL only and never written back to Git. Object IDs are validated before use.
    """
    entries = {}
    for record in git(repo, 'ls-files', '-z', '--stage').split(b'\0'):
        if not record:
            continue
        header, tab, raw_path = record.partition(b'\t')
        fields = header.decode('ascii', 'replace').split(' ')
        if not tab or len(fields) != 3 or not fields[0].isdigit() or not OBJECT_ID.match(fields[1]):
            raise GitProtocolError('index_record', 'malformed ls-files --stage record')
        mode, oid, stage = fields
        if stage != '0':
            raise GitProtocolError('unmerged_index', 'the index has unmerged entries; resolve conflicts first')
        entries[raw_path.decode('utf-8')] = IndexEntry(mode, oid)
    return dict(sorted(entries.items()))


def tracked_files(repo: Path) -> list[str]:
    """Every path in Git's index, sorted."""
    return list(index_entries(repo))


def shown(text: str) -> str:
    """A path or id for one line of text output: escaped (repr) unless every character is printable.

    Controls, line and paragraph separators, format characters (bidi overrides, U+FEFF)
    and other non-printing characters are escaped, so a value can never forge or hide
    output. Ordinary text, including Cyrillic and spaces, is printed as is.
    """
    return text if text.isprintable() else repr(text)


def control_path_error(path: str) -> str:
    return (f'tracked path {path!r} contains control characters; rename it '
            '(such paths are never catalogued or read)')


def under_roots(path: str, roots=TRACKED_ROOTS) -> bool:
    return any(path == root or path.startswith(root + '/') for root in roots)


# A directory's README or index note (prose) states what the directory holds and whether it is
# still used: public lifecycle text, not one of the private bodies the exclusion protects. A
# language tag counts only before a prose extension (README.uk.md), so index.js is no note.
DIRECTORY_NOTE = re.compile(r'(?:readme|index)(?:(?:\.[a-z]{2})?\.(?:md|markdown|txt|rst))?', re.IGNORECASE)


def is_directory_note(path: str) -> bool:
    """True for a README or index note in prose (README, README.md, index.uk.md, ...)."""
    return bool(DIRECTORY_NOTE.fullmatch(PurePosixPath(path).name))


def is_excluded(path: str) -> bool:
    """True when the docs inventory's privacy exclusion (one shared list) covers the body of ``path``.

    The exclusion keeps private bodies (handoffs, secrets, caches) out of every read and result;
    the README or index note of an excluded directory (``is_directory_note``) is exempt, because
    it is the public record of that directory's lifecycle.
    """
    return bool(EXCLUDED_PARTS.intersection(PurePosixPath(path).parts)) and not is_directory_note(path)


def root_of(pattern: str, roots=TRACKED_ROOTS) -> str | None:
    """The longest denominator root that is a literal prefix of ``pattern``."""
    matches = [r for r in roots if pattern.startswith(r + '/')]
    return max(matches, key=len) if matches else None


# ---------------------------------------------------------------- globs

# The catalogue glob dialect (one dialect for family paths and store names):
#   * literal characters match themselves;
#   * ``*`` matches any run of characters inside one path segment (never ``/``);
#   * ``?`` matches exactly one character inside one path segment;
#   * ``**`` is a whole segment and matches one or more segments (zero or more
#     when another segment follows it).
# Character classes (``[...]``), braces (``{a,b}``), empty, ``.`` and ``..``
# segments, a leading ``/`` and control characters are not part of it. A trailing
# ``/`` is allowed only on a store name, where it claims the subtree.
# docs/knowledge/catalogue.schema.json states the same rules as ``$defs/glob``.

def glob_error(pattern: object, *, subtree: bool = False) -> str | None:
    """Why ``pattern`` is outside the glob dialect, or None when it is inside it."""
    if not isinstance(pattern, str) or not pattern:
        return 'a glob must be a non-empty string'
    if FORBIDDEN_GLOB_CHARS.search(pattern):
        return ('character classes ([...]), braces ({...}) and control characters are not '
                'in the catalogue glob dialect; list each path or use * and ?')
    body = pattern[:-1] if subtree and pattern.endswith('/') else pattern
    if body.startswith('/'):
        return 'a glob is repository-relative and must not start with "/"'
    for segment in body.split('/'):
        if segment in ('', '.', '..'):
            return 'empty, "." and ".." path segments are not allowed'
        if '**' in segment and segment != '**':
            return '"**" must be a whole path segment'
    return None


def glob_regex(pattern: str) -> re.Pattern:
    """Compile one dialect glob; raises ValueError (with the reason) outside the dialect."""
    if (error := glob_error(pattern)) is not None:
        raise ValueError(f'glob {pattern!r} is not in the catalogue glob dialect: {error}')
    segments = pattern.split('/')
    out = ''
    for index, segment in enumerate(segments):
        last = index == len(segments) - 1
        if segment == '**':
            out += '.+' if last else '(?:[^/]+/)*'
            continue
        out += ''.join('[^/]*' if c == '*' else '[^/]' if c == '?' else re.escape(c) for c in segment)
        out += '' if last else '/'
    return re.compile(out + r'\Z')


def specificity(pattern: str) -> tuple[int, int, int]:
    """Exact paths beat globs, then more literal segments, then more literal characters."""
    segments = pattern.split('/')
    literal_segments = sum(not WILDCARD.search(s) for s in segments)
    literal_chars = len(WILDCARD.sub('', pattern))
    return (0 if WILDCARD.search(pattern) else 1, literal_segments, literal_chars)


def is_catch_all(pattern: str, roots=TRACKED_ROOTS) -> bool:
    """A glob is a catch-all unless the first segment below its root is fully literal.

    Without a literal first segment one glob spans many top-level families of a
    root (``docs/*/**``, ``docs/a*/**``, ``docs/*.md``); with no root prefix at
    all, the first segment of the whole glob must be literal (``**`` is a catch-all).
    """
    if WILDCARD.search(pattern) is None:
        return False
    root = root_of(pattern, roots)
    rest = pattern[len(root) + 1:] if root else pattern
    return bool(WILDCARD.search(rest.split('/', 1)[0]))


@dataclass(frozen=True)
class Glob:
    entry: str
    pattern: str
    regex: re.Pattern
    rank: tuple[int, int, int]

    @property
    def literal_dir(self) -> str:
        """The leading literal directory segments; every path the glob matches lies below it."""
        segments = self.pattern.split('/')[:-1]
        literal = []
        for segment in segments:
            if WILDCARD.search(segment):
                break
            literal.append(segment)
        return '/'.join(literal)


def compile_globs(entry_id: str, patterns: list[str]) -> list[Glob]:
    return [Glob(entry_id, p, glob_regex(p), specificity(p)) for p in patterns]


def ancestor_dirs(path: str) -> list[str]:
    """'' and every proper ancestor directory of ``path`` ('a/b/c.md' -> ['', 'a', 'a/b'])."""
    parts = path.split('/')[:-1]
    return [''] + ['/'.join(parts[:i]) for i in range(1, len(parts) + 1)]


# ---------------------------------------------------------------- loading

# Parsing bounds, checked before schema validation. The catalogue is ~110 KB,
# ~5,700 nodes and 5 collections deep; each bound leaves room for ~20x growth.
MAX_CATALOGUE_BYTES = 2 * 1024 * 1024
MAX_CATALOGUE_NODES = 100_000
MAX_CATALOGUE_DEPTH = 16
MERGE_TAG = 'tag:yaml.org,2002:merge'


class CatalogueLoadError(ValueError):
    """The catalogue file is outside the accepted YAML subset; ``code`` names the rule."""

    def __init__(self, code: str, message: str, mark: yaml.Mark | None = None):
        where = f' (line {mark.line + 1}, column {mark.column + 1})' if mark is not None else ''
        super().__init__(f'{code}: {message}{where}')
        self.code = code


class CatalogueLoader(yaml.SafeLoader):
    """Plain-data YAML only: no anchors, aliases, merge keys or explicit tags; unique string
    keys; at most MAX_CATALOGUE_NODES nodes and MAX_CATALOGUE_DEPTH nested collections.

    The bounds are enforced while composing, before the (recursive) composer descends,
    so no input can exhaust the stack or expand into a large object graph.
    """

    def __init__(self, stream):
        super().__init__(stream)
        self.nodes = 0
        self.depth = 0

    def compose_node(self, parent, index):
        event = self.peek_event()
        if isinstance(event, yaml.AliasEvent):
            raise CatalogueLoadError('alias', 'aliases are not allowed in the catalogue', event.start_mark)
        if event.anchor is not None:
            raise CatalogueLoadError('anchor', 'anchors are not allowed in the catalogue', event.start_mark)
        if event.tag is not None:
            raise CatalogueLoadError('tag', f'explicit tag {event.tag!r} is not allowed in the catalogue',
                                     event.start_mark)
        self.nodes += 1
        if self.nodes > MAX_CATALOGUE_NODES:
            raise CatalogueLoadError('too_many_nodes', f'more than {MAX_CATALOGUE_NODES} YAML nodes',
                                     event.start_mark)
        if not isinstance(event, (yaml.SequenceStartEvent, yaml.MappingStartEvent)):
            return super().compose_node(parent, index)
        self.depth += 1
        if self.depth > MAX_CATALOGUE_DEPTH:
            raise CatalogueLoadError('too_deep', f'more than {MAX_CATALOGUE_DEPTH} nested collections',
                                     event.start_mark)
        try:
            return super().compose_node(parent, index)
        finally:
            self.depth -= 1

    def flatten_mapping(self, node):
        for key_node, _ in node.value:
            if key_node.tag == MERGE_TAG:
                raise CatalogueLoadError('merge_key', 'merge keys (<<) are not allowed in the catalogue',
                                         key_node.start_mark)
        super().flatten_mapping(node)

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise CatalogueLoadError('non_string_key', f'mapping key {key!r} is not a string',
                                         key_node.start_mark)
            if key in seen:
                raise CatalogueLoadError('duplicate_key', f'duplicate mapping key {key!r}', key_node.start_mark)
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def parse(raw: bytes) -> dict:
    """Parse catalogue bytes with the restricted loader; raises CatalogueLoadError only."""
    if len(raw) > MAX_CATALOGUE_BYTES:
        raise CatalogueLoadError('too_large', f'file exceeds {MAX_CATALOGUE_BYTES} bytes')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise CatalogueLoadError('encoding', f'not UTF-8 at byte {exc.start}') from None
    try:
        data = yaml.load(text, Loader=CatalogueLoader)
    except CatalogueLoadError:
        raise
    except yaml.YAMLError as exc:
        mark = getattr(exc, 'problem_mark', None)
        problem = getattr(exc, 'problem', None) or type(exc).__name__
        raise CatalogueLoadError('syntax', str(problem), mark) from None
    except (ValueError, OverflowError) as exc:  # a scalar that matches a YAML type but cannot be built
        raise CatalogueLoadError('scalar', f'unconstructible scalar: {str(exc)[:200]}') from None
    if not isinstance(data, dict):
        raise CatalogueLoadError('not_mapping', 'the catalogue must be a YAML mapping')
    return data


def load(path: Path) -> dict:
    """Read at most MAX_CATALOGUE_BYTES + 1 bytes and parse them (see ``parse``)."""
    with path.open('rb') as handle:
        return parse(handle.read(MAX_CATALOGUE_BYTES + 1))


def owner_keys(repo: Path) -> set[str]:
    keys: set[str] = set()
    for rel, section in OWNER_SOURCES:
        data = yaml.safe_load(git(repo, 'show', f':{rel}').decode('utf-8')) or {}
        keys.update((data.get(section) or {}).keys())
    return keys


def store_regex(store: str) -> re.Pattern | None:
    """A store name ending in '/' claims its subtree; otherwise it is a dialect name or glob.

    Returns None for a name outside the dialect (``validate`` reports it).
    """
    if glob_error(store, subtree=True) is not None:
        return None
    return glob_regex(store + '**' if store.endswith('/') else store)


def strip_fragment(target: str) -> str:
    return target.split('#', 1)[0]


# ---------------------------------------------------------------- validation

@dataclass
class Report:
    denominator: int = 0
    resolved: dict[str, tuple[str, str]] = field(default_factory=dict)  # path -> (entry, lifecycle)
    uncovered: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    entry_counts: dict[str, int] = field(default_factory=dict)
    residual_paths: set[str] = field(default_factory=set)
    data_stores: int = 0
    schema_ok: bool = False
    searchable_entries: set[str] = field(default_factory=set)  # families whose bodies may be read
    private_entries: set[str] = field(default_factory=set)  # families that own privacy-excluded bodies
    store_literals: dict[str, list[str]] | None = None  # set by repository_check
    store_files_scanned: int = 0  # text files under scripts/ the store scan read
    markers_unverifiable: int = 0  # superseded Markdown overrides the privacy gate kept unread

    @property
    def ok(self) -> bool:
        return not self.errors and not self.uncovered

    def lifecycle_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(life for _, life in self.resolved.values()).items()))

    def to_json(self) -> dict:
        return {'denominator': self.denominator, 'covered': len(self.resolved),
                'store_literals': self.store_literals, 'store_files_scanned': self.store_files_scanned,
                'markers_unverifiable': self.markers_unverifiable,
                'uncovered': self.uncovered, 'errors': self.errors,
                'lifecycle_counts': self.lifecycle_counts(),
                'residual_paths': len(self.residual_paths), 'data_stores': self.data_stores,
                'entry_counts': dict(sorted(self.entry_counts.items())),
                'root_counts': {root: sum(under_roots(p, (root,)) for p in self.resolved)
                                for root in TRACKED_ROOTS}}


def schema_errors(catalogue: dict, schema: dict) -> list[str]:
    """Schema violations; for oneOf/anyOf failures report the most relevant branch error.

    A glob or store name that fails its pattern is reported with the dialect rule it breaks.
    """
    validator = Draft202012Validator(schema)
    defs = schema.get('$defs', {})
    found = []
    for error in sorted(validator.iter_errors(catalogue), key=lambda e: list(map(str, e.absolute_path))):
        detail = best_match(error.context) if error.context else error
        where = '/'.join(map(str, detail.absolute_path)) or '<root>'
        message = detail.message
        is_store = detail.schema is defs.get('storeName')
        if detail.validator == 'pattern' and (is_store or detail.schema is defs.get('glob')):
            reason = glob_error(detail.instance, subtree=is_store) or 'a store name must be a path below "data/"'
            message = f'{detail.instance!r} is not in the catalogue glob dialect: {reason}'
        found.append(f'schema: {where}: {message}')
    return found


def control_string_errors(catalogue: object) -> list[str]:
    """One error per string in the loaded catalogue (mapping keys included) holding a control character.

    Independent of the schema, so no schema pattern (for example a ``$`` that also matches
    before a final newline) can admit a control. The value is reported escaped and bounded.
    """
    errors = []
    stack: list[tuple[tuple, object]] = [((), catalogue)]
    while stack:
        where, node = stack.pop()
        if isinstance(node, dict):
            items = list(node.items())
            for key, _ in items:
                if isinstance(key, str) and (hit := CONTROL_CHARS.search(key)):
                    errors.append(_control_error(where, key, hit.group(), 'key '))
            stack.extend(((*where, key), value) for key, value in reversed(items))
        elif isinstance(node, list):
            stack.extend(((*where, index), value) for index, value in reversed(list(enumerate(node))))
        elif isinstance(node, str) and (hit := CONTROL_CHARS.search(node)):
            errors.append(_control_error(where, node, hit.group()))
    return errors


def _control_error(where: tuple, value: str, char: str, what: str = '') -> str:
    location = '/'.join(shown(part) if isinstance(part, str) else str(part) for part in where) or '<root>'
    shown_value = repr(value[:200]) + ('...' if len(value) > 200 else '')
    return (f'control: {location}: {what}{shown_value} contains control character U+{ord(char):04X}; '
            'C0, DEL and C1 controls are not allowed in any catalogue string')


def validate(catalogue: dict, schema: dict, files: list[str], owners: set[str],
             roots: tuple[str, ...] = TRACKED_ROOTS) -> Report:
    """Check structure, coverage, supersession and references; never raises on bad data.

    A tracked path with a control character is an error and is dropped before anything
    else sees it, so it is never resolved, counted, matched or read. A catalogue string
    with a control character is an error whatever the schema says, and the catalogue is
    then not schema_ok, so no local store is reconciled against it.
    """
    report = Report()
    report.errors.extend(control_path_error(p) for p in files if CONTROL_CHARS.search(p))
    files = [p for p in files if not CONTROL_CHARS.search(p)]
    controls = control_string_errors(catalogue)
    report.errors.extend(controls)
    found = schema_errors(catalogue, schema)
    if found:
        report.errors.extend(found)
        return report
    report.schema_ok = not controls
    tracked = set(files)
    denominator = [p for p in files if under_roots(p, roots)]
    report.denominator = len(denominator)
    entries = catalogue['entries']
    by_id: dict[str, dict] = {}
    for entry in entries:
        if entry['id'] in by_id:
            report.errors.append(f"duplicate entry id {entry['id']!r}")
        by_id[entry['id']] = entry
    # Fail closed: an id stays private if any entry using it is not content-searchable.
    report.searchable_entries = ({e['id'] for e in entries if e['content_searchable']}
                                 - {e['id'] for e in entries if not e['content_searchable']})
    # Store claims only ever match below data/; placeholders never count as a tracked store.
    data_files = [p for p in files if p.startswith('data/') and p.rsplit('/', 1)[-1] not in PLACEHOLDER_NAMES]

    globs: list[Glob] = []
    must_match: list[Glob] = []  # globs inside the rules, which must each match a tracked file
    for entry in entries:
        eid = shown(entry['id'])
        if entry['owner'] not in owners:
            report.errors.append(f"{eid}: owner {entry['owner']!r} is not a stream or area key")
        if entry['purpose'].strip().upper().startswith('TODO'):
            report.errors.append(f'{eid}: purpose is still a TODO placeholder')
        for item in entry.get('entrypoints', []):
            if strip_fragment(item['path']) not in tracked:
                report.errors.append(f"{eid}: entrypoint {item['path']!r} is not a tracked path")
        if entry['kind'] == 'data_store':
            report.data_stores += 1
            for producer in entry['producer']:
                if producer not in tracked:
                    report.errors.append(f'{eid}: producer {producer!r} is not a tracked path')
            if not entry['producer'] and not entry.get('producer_note'):
                report.errors.append(f'{eid}: data store without producer needs producer_note')
            claims = []
            for store in entry['store']:
                if (error := glob_error(store, subtree=True)) is not None:
                    report.errors.append(f'{eid}: store {store!r} is not in the catalogue glob dialect: {error}')
                else:
                    claims.append(store_regex(store))
            in_git = [p for p in data_files if any(claim.match(p) for claim in claims)]
            if entry['local_only'] and in_git:
                report.errors.append(f'{eid}: local_only is true but {len(in_git)} store files are tracked')
            elif not entry['local_only'] and not in_git:
                report.errors.append(f'{eid}: local_only is false but no store file is tracked')
            continue
        try:
            compiled = compile_globs(entry['id'], entry['paths'])
        except ValueError as exc:
            report.errors.append(f'{eid}: {exc}')
            continue
        for glob in compiled:
            if is_catch_all(glob.pattern, roots):
                report.errors.append(f'{eid}: glob {glob.pattern!r} is a catch-all (the first segment '
                                     'below its tracked root must be literal)')
            elif root_of(glob.pattern, roots) is None and glob.pattern not in roots:
                report.errors.append(f'{eid}: glob {glob.pattern!r} is outside the tracked roots')
            else:
                must_match.append(glob)
        globs.extend(compiled)

    # Resolve each tracked path to exactly one family: most specific glob wins. A glob can
    # only match paths below its literal directory, so each path tests only those globs.
    by_dir: dict[str, list[Glob]] = defaultdict(list)
    for glob in globs:
        by_dir[glob.literal_dir].append(glob)
    used: set[tuple[str, str]] = set()
    owner_of: dict[str, str] = {}
    for path in denominator:
        best: dict[str, tuple[int, int, int]] = {}
        for directory in ancestor_dirs(path):
            for glob in by_dir.get(directory, ()):
                if glob.regex.match(path):
                    used.add((glob.entry, glob.pattern))
                    if glob.rank > best.get(glob.entry, (-1, -1, -1)):
                        best[glob.entry] = glob.rank
        if not best:
            report.uncovered.append(path)
            continue
        top = max(best.values())
        winners = sorted(e for e, rank in best.items() if rank == top)
        if len(winners) > 1:
            report.errors.append(f'{shown(path)}: ambiguous match between {", ".join(map(shown, winners))}')
            continue
        owner_of[path] = winners[0]
    for glob in must_match:
        if (glob.entry, glob.pattern) not in used:
            report.errors.append(f'{shown(glob.entry)}: glob {glob.pattern!r} matches no tracked file')

    # Privacy follows ownership: a family that owns any inventory-excluded path
    # (docs_inventory.EXCLUDED_PARTS) must not be content-searchable.
    excluded_owned: dict[str, list[str]] = defaultdict(list)
    for path, eid in owner_of.items():
        if is_excluded(path):
            excluded_owned[eid].append(path)
    report.private_entries = set(excluded_owned)
    for eid, paths in sorted(excluded_owned.items()):
        if by_id[eid]['content_searchable']:
            report.errors.append(f'{shown(eid)}: owns {len(paths)} inventory-excluded path(s) such as {paths[0]!r}, '
                                 'so content_searchable must be false')

    lifecycle: dict[str, str] = {p: by_id[e]['lifecycle'] for p, e in owner_of.items()}
    supersession: dict[str, str] = {}
    for entry in entries:
        if entry.get('superseded_by'):
            supersession[f"id:{entry['id']}"] = entry['superseded_by']
        seen = set()
        for override in entry.get('overrides', []):
            path = override['path']
            if path in seen:
                report.errors.append(f"{shown(entry['id'])}: duplicate override for {path!r}")
            seen.add(path)
            if path not in tracked:
                report.errors.append(f"{shown(entry['id'])}: override {path!r} is not a tracked path")
            elif owner_of.get(path) != entry['id']:
                report.errors.append(f"{shown(entry['id'])}: override {path!r} resolves to "
                                     f"{owner_of.get(path)!r}, not this entry")
            else:
                lifecycle[path] = override['lifecycle']
            if override['lifecycle'] == 'superseded':
                supersession[path] = override['superseded_by']

    for item in catalogue.get('residual', []):
        path = item['path']
        if item['owner'] not in owners:
            report.errors.append(f"residual {path!r}: owner {item['owner']!r} is not a stream or area key")
        if path not in owner_of:
            report.errors.append(f'residual {path!r} is not a covered tracked path')
            continue
        overridden = any(o['path'] == path for o in by_id[owner_of[path]].get('overrides', []))
        if overridden:
            report.errors.append(f'residual {path!r} also has a lifecycle override')
        lifecycle[path] = 'residual'
        report.residual_paths.add(path)

    # Paths that inherit a superseded family default follow the family's link.
    follow = dict(supersession)
    for path, eid in owner_of.items():
        if lifecycle[path] == 'superseded' and path not in follow and by_id[eid].get('superseded_by'):
            follow[path] = by_id[eid]['superseded_by']
    report.errors.extend(_supersession_errors(supersession, follow, by_id, lifecycle, tracked))
    report.uncovered.sort()
    report.resolved = {p: (owner_of[p], lifecycle[p]) for p in owner_of}
    report.entry_counts = dict(Counter(owner_of.values()))
    for entry in entries:
        if entry['kind'] != 'data_store':
            report.entry_counts.setdefault(entry['id'], 0)
    return report


def _supersession_errors(links: dict[str, str], follow: dict[str, str], by_id: dict[str, dict],
                         lifecycle: dict[str, str], tracked: set[str]) -> list[str]:
    """Targets exist; no self-links or cycles; every chain ends at an active/archive node.

    A target is ``id:<entry>`` (catalogue entry) or a tracked path, optionally with
    ``#section``. A tracked target outside the denominator (code, rules) is terminal.
    """
    def node(target: str) -> str:
        return target if target.startswith('id:') else strip_fragment(target)

    def state(key: str) -> str | None:
        if key.startswith('id:'):
            entry = by_id.get(key[3:])
            return entry['lifecycle'] if entry else None
        if key in lifecycle:
            return lifecycle[key]
        return 'active' if key in tracked else None

    errors = []
    for start, raw in sorted(links.items()):
        chain, current, link = [start], start, raw
        while True:
            target = node(link)
            if target == current or target in chain:
                errors.append(f'supersession cycle or self-link: {" -> ".join(map(shown, [*chain, target]))}')
                break
            status = state(target)
            if status is None:
                errors.append(f'{shown(current)}: supersession target {link!r} does not exist')
                break
            chain.append(target)
            if status in TERMINAL_LIFECYCLES:
                break
            if status != 'superseded' or target not in follow:
                errors.append(f'{shown(start)}: supersession chain ends at {target!r} with lifecycle {status!r}')
                break
            current, link = target, follow[target]
    return errors


def coverage(repo: Path, catalogue_path: Path | None = None) -> Report:
    """Validate the repository's catalogue against its own Git index."""
    catalogue_path = catalogue_path or repo / CATALOGUE_PATH
    schema = json.loads((repo / SCHEMA_PATH).read_text(encoding='utf-8'))
    return validate(load(catalogue_path), schema, tracked_files(repo), owner_keys(repo))


# ---------------------------------------------------------------- local stores

def local_store_gaps(data_root: Path, catalogue: dict) -> tuple[int, list[str]]:
    """Names under ``data/`` that no data_store entry claims; reads names only, never contents.

    SQLite sidecars (-shm, -wal, -journal) belong to their database. A directory
    with no store of its own is checked child by child when stores name its children.
    Returns (entries checked, unmatched logical paths).
    """
    patterns = [s.rstrip('/') for e in catalogue.get('entries', []) if e.get('kind') == 'data_store'
                for s in e.get('store', []) if glob_error(s, subtree=True) is None]
    regexes = [glob_regex(p) for p in patterns]

    def claimed(logical: str) -> bool:
        base = next((logical[:-len(x)] for x in SQLITE_SIDECARS if logical.endswith(x)), logical)
        return any(regex.match(base) for regex in regexes)

    checked, unmatched = 0, []

    def walk(directory: Path, prefix: str) -> None:
        nonlocal checked
        for child in sorted(directory.iterdir(), key=lambda c: c.name):
            logical = f'{prefix}/{child.name}'
            checked += 1
            if claimed(logical):
                continue
            if child.is_dir() and not child.is_symlink() and any(p.startswith(logical + '/') for p in patterns):
                walk(child, logical)
            else:
                unmatched.append(logical)

    walk(data_root, 'data')
    return checked, unmatched


# ---------------------------------------------------------------- draft markers

DRAFT_SCAN_LINES = 30
DRAFT_MARKERS = (
    ('draft-heading', re.compile(r'^\s*#+\s*\W*draft\b', re.IGNORECASE | re.MULTILINE)),
    ('DRAFT', re.compile(r'\bDRAFT\b')),
    ('status-draft', re.compile(r'(?<!original )\bstatus\b[*_\s]*[:=][*_\s"\'`]*draft\b', re.IGNORECASE)),
    ('status-proposed', re.compile(r'(?<!original )\bstatus\b[*_\s]*[:=][*_\s"\'`]*proposed\b', re.IGNORECASE)),
    ('lifecycle-draft', re.compile(r'\blifecycle\b[*_\s]*[:=][*_\s"\'`]*draft\b', re.IGNORECASE)),
    ('work-in-progress', re.compile(r'\bwork[ -]in[ -]progress\b|\bWIP\b', re.IGNORECASE)),
    ('proposal', re.compile(r'\bproposal\b', re.IGNORECASE)),
)


def body_readable(report: Report, path: str) -> bool:
    """The privacy boundary for content reads: may this path's body be read at all?

    True only for a path that resolves to a family, is not privacy-excluded (``is_excluded``)
    and has no control character, and that either belongs to a content-searchable family or
    is the directory note (``is_directory_note``) of a family that owns private bodies: the
    privacy exclusion keeps those bodies unread, while the README that says what they are
    is read. A family made unsearchable for any other reason stays wholly unread, as does
    every unresolved path.
    ``read_heads`` is the only body reader and applies this gate itself, so a
    scanner cannot bypass it.
    """
    owner = report.resolved.get(path)
    return (owner is not None and (owner[0] in report.searchable_entries
                                   or (owner[0] in report.private_entries and is_directory_note(path)))
            and not is_excluded(path) and not CONTROL_CHARS.search(path))


def _index_blobs(repo: Path, objects: dict[str, str]) -> dict[str, bytes]:
    """Blob contents keyed by path, requested by index object ID.

    Call only via ``read_heads`` (the privacy-gated document reader) or ``store_literals``
    (which applies the same gate to ``scripts/`` paths before requesting any blob).

    ``objects`` maps each path to its index object ID. The ``cat-file --batch`` request
    holds validated object IDs only, never pathnames, and each response header must name
    the requested ID with type ``blob``, so no request can answer for another. A missing
    object is absent from the result; any other mismatch raises GitProtocolError.
    """
    order = list(objects.items())
    for _, oid in order:
        if not OBJECT_ID.match(oid):
            raise GitProtocolError('object_id', f'{oid[:80]!r} is not a full object ID')
    request = b''.join(oid.encode('ascii') + b'\n' for _, oid in order)
    out = subprocess.run(['git', '-C', str(repo), 'cat-file', '--batch'], input=request,
                         capture_output=True, check=True, timeout=300).stdout
    blobs, offset = {}, 0
    for path, oid in order:
        header_end = out.find(b'\n', offset)
        if header_end < 0:
            raise GitProtocolError('truncated', f'no response header for {oid}')
        header = out[offset:header_end].split(b' ')
        if header[0] != oid.encode('ascii'):
            raise GitProtocolError('response_mismatch', f'response names {header[0][:80]!r}, requested {oid}')
        if header[1:] == [b'missing']:
            offset = header_end + 1
            continue
        if len(header) != 3 or header[1] != b'blob' or not header[2].isdigit():
            raise GitProtocolError('not_blob', f'{oid} answered {b" ".join(header[1:])[:80]!r}, not a blob')
        start = header_end + 1
        end = start + int(header[2])
        if out[end:end + 1] != b'\n':
            raise GitProtocolError('truncated', f'blob {oid} is shorter than its header size')
        blobs[path] = out[start:end]
        offset = end + 1
    if offset != len(out):
        raise GitProtocolError('trailing_output', 'more responses than requests')
    return blobs


def read_heads(repo: Path, report: Report, paths: list[str],
               lines: int = DRAFT_SCAN_LINES) -> tuple[dict[str, str], int]:
    """The first ``lines`` lines of each body-readable path; binary blobs are skipped.

    Blobs are requested by the object ID in the index entry of each readable regular
    file. Returns (heads, number of paths withheld by ``body_readable``).
    """
    readable = [p for p in paths if body_readable(report, p)]
    entries = index_entries(repo)
    objects = {p: entries[p].oid for p in readable if p in entries and entries[p].mode in REGULAR_MODES}
    heads = {}
    for path, blob in _index_blobs(repo, objects).items():
        if b'\0' not in blob[:8192]:
            heads[path] = '\n'.join(blob.decode('utf-8', 'replace').splitlines()[:lines])
    return heads, len(paths) - len(readable)


def draft_scan(repo: Path, report: Report) -> dict:
    """Draft markers in the first lines of every readable resolved path, set against its lifecycle.

    ``active_with_marker`` lists paths that state a draft-like marker yet resolve to
    ``active``; ``draft_without_marker`` lists read paths that resolve to ``draft`` with no
    marker. Both need a reviewed disposition; ``proposal`` alone is a weak marker.
    Paths that ``body_readable`` withholds are counted in ``skipped_private``, never named.
    """
    paths = sorted(report.resolved)
    heads, skipped = read_heads(repo, report, paths)
    hits: dict[str, list[str]] = {}
    for path, text in heads.items():
        found = [name for name, pattern in DRAFT_MARKERS if pattern.search(text)]
        if found:
            hits[path] = found
    by_lifecycle = Counter(report.resolved[p][1] for p in hits)
    by_marker = Counter(name for found in hits.values() for name in found)
    return {
        'scanned': len(heads), 'skipped_private': skipped,
        'binary_or_missing': len(paths) - skipped - len(heads),
        'with_marker': len(hits), 'by_marker': dict(sorted(by_marker.items())),
        'with_marker_by_lifecycle': dict(sorted(by_lifecycle.items())),
        'active_with_marker': {p: hits[p] for p in sorted(hits) if report.resolved[p][1] == 'active'},
        'draft_without_marker': sorted(p for p, (_, life) in report.resolved.items()
                                       if life == 'draft' and p not in hits and body_readable(report, p)),
    }


# ---------------------------------------------------------------- data-store literals in code

CODE_ROOT = 'scripts/'
STORE_SUFFIXES = ('.db', '.sqlite', '.sqlite3', '.duckdb')
# One character of a store name. Excluded: whitespace (the quoted dialect re-admits the
# plain space), controls, quotes, '<>|', the shell terminators ';&()', the expansion and
# glob syntax '{}$*?[]' (a name built at run time is not a literal), '\' and the separator.
_NAME_CHAR = r'[^\s\x00-\x1f\x7f-\x9f\'"`<>|;&(){}$*?\[\]\\/]'
_STORE_EXTENSION = r'\.(?:db|sqlite3?|duckdb)(?!\w)'
# 'data/' not preceded by a word character, '.' or '-', so 'metadata/x.db' and 'test_data/x.db'
# are not data/ (the literal comes first so the engine can search for it). The name is the
# shortest run that ends in a store extension.
_STORE_START = r'data/(?<![\w.-]data/)'
STORE_WORD = re.compile(_STORE_START + rf'((?:{_NAME_CHAR}|\\ |/)+?{_STORE_EXTENSION})')
STORE_SPACED = re.compile(_STORE_START + rf'((?:{_NAME_CHAR}| |/)+?{_STORE_EXTENSION})')
# A single-line quoted span; inside one a store name may contain spaces.
QUOTED_SPAN = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"|`[^`\n]*`")
STORE_SEGMENT = re.compile(rf'{_NAME_CHAR}(?:(?:{_NAME_CHAR}| )*{_NAME_CHAR})?\Z')
# Blobs with a NUL in their first bytes are binary and carry no store names.
BINARY_PROBE = 8192


def _chain(node: ast.AST) -> list[ast.AST]:
    """The operands of a left-associated ``a / b / c`` path join, in order."""
    operands = []
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        operands.append(node.right)
        node = node.left
    operands.append(node)
    return operands[::-1]


def _joined_store(operands: list[ast.AST], bases: dict[str, str]) -> str | None:
    """'data/<...>.db' for a join that starts at a "data" segment or a data-directory name."""
    path: list[str] | None = None
    for operand in operands:
        text = operand.value if isinstance(operand, ast.Constant) and isinstance(operand.value, str) else None
        if path is None:
            if text is not None and text.strip('/') == 'data':
                path = ['data']
            elif isinstance(operand, ast.Name) and operand.id in bases:
                path = [bases[operand.id]]
            continue
        if text is None or not all(STORE_SEGMENT.match(part) for part in text.strip('/').split('/')):
            return None
        path.append(text.strip('/'))
    joined = '/'.join(path) if path else ''
    return joined if joined.endswith(STORE_SUFFIXES) else None


def _data_bases(tree: ast.Module) -> dict[str, str]:
    """Module-level names bound to a data directory ('DATA_DIR = ROOT / "data"' -> 'data')."""
    bases: dict[str, str] = {}
    for statement in tree.body:
        if not (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)):
            continue
        operands = _chain(statement.value)
        texts = [o.value if isinstance(o, ast.Constant) and isinstance(o.value, str) else None for o in operands]
        if 'data' in texts:
            rest = texts[texts.index('data'):]
            if all(t is not None and STORE_SEGMENT.match(t) for t in rest[1:]):
                bases[statement.targets[0].id] = '/'.join(rest)
    return bases


QUOTED_DATA = re.compile(r"""['"]data/?['"]""")
QUOTED_STORE = re.compile(r"""\.(?:db|sqlite3?|duckdb)['"]""")


def _store_name(name: str) -> str | None:
    """'data/<name>' when every segment of ``name`` is a valid store-name segment, else None."""
    parts = name.split('/')
    if all(STORE_SEGMENT.match(part) and part not in ('.', '..') for part in parts):
        return 'data/' + name
    return None


def store_names_in_text(text: str) -> set[str]:
    """Logical 'data/...' store names in any text: code, shell, config or prose.

    Two passes. The word pass reads ``data/<name>.<ext>`` with no whitespace except a
    backslash-escaped space (a shell word; also a bare or quoted literal in any language).
    The quoted pass reads each single-line '...', "..." or `...` span and also admits plain
    spaces inside a segment (never at its ends). Comments count too: stripping them needs a
    parser per language, and a store a comment names is a dependency worth recording, so an
    over-match costs one exemption while an under-match would let an unregistered store pass.
    """
    found: set[str] = set()
    if 'data/' not in text:
        return found
    for match in STORE_WORD.finditer(text):
        if (store := _store_name(match.group(1).replace('\\ ', ' '))) is not None:
            found.add(store)
    for span in QUOTED_SPAN.finditer(text):
        if 'data/' not in span.group():
            continue
        for match in STORE_SPACED.finditer(span.group()[1:-1]):
            if (store := _store_name(match.group(1))) is not None:
                found.add(store)
    return found


def store_literals_in_source(source: str, python: bool = True) -> set[str]:
    """Logical 'data/...' store paths a file names: its text, plus Python path joins.

    For Python source, path joins (``ROOT / "data" / "x.db"``, ``DATA_DIR / "x.db"`` with a
    module-level ``DATA_DIR = ROOT / "data"``) are read from the AST, which is parsed only
    when the source has both a quoted "data" segment and a quoted store name.
    """
    found = store_names_in_text(source)
    if not (python and QUOTED_DATA.search(source) and QUOTED_STORE.search(source)):
        return found
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return found
    bases = _data_bases(tree)
    for node in ast.walk(tree):
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                and (store := _joined_store(_chain(node), bases)) is not None):
            found.add(store)
    return found


@dataclass
class StoreScan:
    """What the store-name scan over ``scripts/`` read and found."""
    stores: dict[str, list[str]]  # store -> sorted files naming it
    scanned: int = 0  # text files read
    binary: int = 0  # files skipped as binary (a NUL byte in the first BINARY_PROBE bytes)
    unread: list[str] = field(default_factory=list)  # not a regular blob, missing, or not UTF-8
    withheld: list[str] = field(default_factory=list)  # refused by the privacy gate


def store_literals(repo: Path, files: dict[str, IndexEntry] | None = None) -> StoreScan:
    """Every logical data store named by any tracked text file under ``scripts/``.

    The surface is the repository's own: every path Git's index lists under ``scripts/``,
    whatever its extension, read as the index blob by object ID (never the worktree, so a
    sparse or CI checkout reads the same bytes). The privacy gate applies first: a path with
    a control character or an inventory-excluded component is never read and is reported
    as withheld. Binary blobs are skipped and counted. A symlink, submodule, missing blob or
    non-UTF-8 text is reported as unread; withheld and unread files fail the check.
    """
    files = index_entries(repo) if files is None else files
    scan = StoreScan({})
    objects = {}
    for path, entry in files.items():
        if not path.startswith(CODE_ROOT):
            continue
        if CONTROL_CHARS.search(path) or is_excluded(path):
            scan.withheld.append(path)
        elif entry.mode not in REGULAR_MODES:
            scan.unread.append(path)
        else:
            objects[path] = entry.oid
    blobs = _index_blobs(repo, objects)
    found: dict[str, set[str]] = defaultdict(set)
    for path in objects:
        blob = blobs.get(path)
        if blob is None:
            scan.unread.append(path)
            continue
        if b'\0' in blob[:BINARY_PROBE]:
            scan.binary += 1
            continue
        try:
            source = blob.decode('utf-8')
        except UnicodeDecodeError:
            scan.unread.append(path)
            continue
        scan.scanned += 1
        for store in store_literals_in_source(source, python=path.endswith('.py')):
            found[store].add(path)
    scan.stores = {store: sorted(paths) for store, paths in sorted(found.items())}
    scan.unread.sort()
    return scan


def store_literal_errors(catalogue: dict, literals: dict[str, list[str]]) -> list[str]:
    """A named store needs a data_store entry claiming it or a reasoned exemption; exemptions stay live."""
    claims = [store_regex(s) for e in catalogue.get('entries', []) if e.get('kind') == 'data_store'
              for s in e.get('store', [])]
    claims = [c for c in claims if c is not None]
    exempt = {item['literal']: item for item in catalogue.get('store_literal_exemptions', [])}
    errors = []
    for store, paths in literals.items():
        claimed = any(claim.match(store) for claim in claims)
        if claimed and store in exempt:
            errors.append(f'store literal {store!r} is claimed by a data_store entry and also exempted; '
                          'remove the exemption')
        elif not claimed and store not in exempt:
            errors.append(f'store literal {store!r} (named in {", ".join(map(shown, paths[:3]))}'
                          f'{" and more" if len(paths) > 3 else ""}) has no data_store entry; add its name to a '
                          'data_store entry\'s store list, or a reasoned store_literal_exemptions item')
    for literal in sorted(set(exempt) - set(literals)):
        errors.append(f'store_literal_exemptions: {literal!r} is no longer named in {CODE_ROOT}; remove it')
    return errors


def unclaimed_stores(catalogue: dict, literals: dict[str, list[str]]) -> list[str]:
    """Store names in code that no data_store entry claims and no exemption covers."""
    claims = [c for c in (store_regex(s) for e in catalogue.get('entries', []) if e.get('kind') == 'data_store'
                          for s in e.get('store', [])) if c is not None]
    exempt = {item['literal'] for item in catalogue.get('store_literal_exemptions', [])}
    return [s for s in literals if s not in exempt and not any(c.match(s) for c in claims)]


def store_stub(store: str) -> str:
    """A paste-ready data_store entry for a store literal that no entry claims."""
    stub = {'id': 'data-' + _slug(store.removeprefix('data/')), 'kind': 'data_store', 'store': [store],
            'producer': [], 'producer_note': 'TODO: the tracked script that writes it, or why none does',
            'local_only': True, 'purpose': 'TODO: one line saying what this store holds and who reads it',
            'keywords': sorted(set(re.findall(r'[a-z0-9]{3,}', store.lower())) - {'data'}) or ['todo'],
            'lifecycle': 'active', 'owner': 'infra-harness',
            'query': [{'surface': 'sqlite', 'how': f'read-only SQL on {store}'}], 'content_searchable': False}
    body = yaml.safe_dump([stub], sort_keys=False, allow_unicode=True, width=1000)
    return ''.join(f'  {line}' for line in body.splitlines(keepends=True))


# ---------------------------------------------------------------- in-place status markers

MARKDOWN_SUFFIX = '.md'
BANNER_PREFIX = '> **Superseded by:** '
MARKER_SCAN_LINES = 200


def superseded_markdown(catalogue: dict) -> dict[str, str]:
    """Markdown path -> replacement for every catalogue override that marks a .md file superseded."""
    return {o['path']: o['superseded_by'] for e in catalogue.get('entries', [])
            for o in e.get('overrides', []) if o.get('lifecycle') == 'superseded'
            and o['path'].endswith(MARKDOWN_SUFFIX)}


def banner_line(path: str, target: str) -> str:
    """The visible line ``> **Superseded by:** [target](relative link)`` for a superseded file."""
    linked = CATALOGUE_PATH if target.startswith('id:') else strip_fragment(target)
    fragment = '' if target.startswith('id:') or '#' not in target else '#' + target.split('#', 1)[1]
    href = posixpath.relpath(linked, posixpath.dirname(path) or '.') + fragment
    if any(c in href for c in ' ()<>'):
        href = f'<{href}>'
    return f'{BANNER_PREFIX}[{target}]({href})'


def _yaml_scalar(value: str) -> str:
    return yaml.safe_dump([value], default_flow_style=True, allow_unicode=True, width=10_000).strip()[1:-1]


def apply_marker(text: str, path: str, target: str) -> str:
    """``text`` with front-matter ``lifecycle: superseded`` / ``superseded_by`` and the banner line.

    Existing front matter keeps its other keys; an existing banner is replaced; a new
    banner goes after the first-line H1 (or at the top of the body). Idempotent.
    """
    lines = text.splitlines(keepends=True)
    wanted = {'lifecycle': 'superseded', 'superseded_by': _yaml_scalar(target)}
    if lines and lines[0].rstrip('\r\n') == '---':
        end = next((i for i, line in enumerate(lines[1:], 1) if line.rstrip('\r\n') in ('---', '...')), None)
        if end is None:
            raise ValueError(f'{path}: unterminated front matter')
        head = lines[1:end]
        for key, value in wanted.items():
            at = next((i for i, line in enumerate(head) if line.startswith(f'{key}:')), None)
            if at is None:
                head.append(f'{key}: {value}\n')
            else:
                head[at] = f'{key}: {value}\n'
        front, body = ['---\n', *head, lines[end]], lines[end + 1:]
    else:
        front = ['---\n', *(f'{k}: {v}\n' for k, v in wanted.items()), '---\n']
        body = ['\n', *lines] if lines and lines[0].strip() else lines
    banner = banner_line(path, target) + '\n'
    at = next((i for i, line in enumerate(body) if line.startswith(BANNER_PREFIX)), None)
    if at is not None:
        body[at] = banner
    else:
        first = next((i for i, line in enumerate(body) if line.strip()), None)
        if first is not None and body[first].startswith('# '):
            body[first + 1:first + 1] = ['\n', banner]
        else:
            body[first or 0:first or 0] = [banner, '\n']
    return ''.join(front + body)


def marker_errors(repo: Path, report: Report, catalogue: dict) -> tuple[list[str], int]:
    """Front matter, banners and catalogue overrides agree on every readable Markdown file.

    * A Markdown override marked superseded needs front-matter ``lifecycle: superseded``,
      ``superseded_by`` equal to the override target, and the banner line.
    * Front-matter ``lifecycle`` or ``superseded_by`` anywhere in the denominator must equal
      what the catalogue resolves for that path (override, residual or family default).
    Only body-readable paths are read; returns (errors, superseded overrides left unread).
    """
    expected = superseded_markdown(catalogue)
    by_id = {e['id']: e for e in catalogue.get('entries', [])}
    paths = sorted(p for p in report.resolved if p.endswith(MARKDOWN_SUFFIX))
    heads, _ = read_heads(repo, report, paths, lines=MARKER_SCAN_LINES)
    errors = []
    unverifiable = sum(1 for p in expected if p in report.resolved and p not in heads)
    for path in paths:
        if path not in heads:
            continue
        facts, problems = inventory_metadata(heads[path])
        family, resolved = report.resolved[path]
        target = expected.get(path) or (by_id[family].get('superseded_by') if resolved == 'superseded' else None)
        where = shown(path)
        for problem in problems:
            if problem.startswith(('lifecycle_', 'superseded_by_')):
                errors.append(f'{where}: front matter {problem.replace("_", " ")}')
        if 'lifecycle' in facts and facts['lifecycle'] != resolved:
            errors.append(f"{where}: front-matter lifecycle {facts['lifecycle']!r} disagrees with the catalogue "
                          f'({resolved!r} from {shown(family)}); add a catalogue override or fix the front matter')
        if 'superseded_by' in facts and facts['superseded_by'] != ([target] if target else []):
            errors.append(f"{where}: front-matter superseded_by {facts['superseded_by']!r} disagrees with the "
                          f'catalogue ({target!r})')
        if path in expected:
            if facts.get('lifecycle') != 'superseded' or facts.get('superseded_by') != [target]:
                errors.append(f'{where}: catalogue marks it superseded by {target!r}; its front matter must say '
                              f'lifecycle: superseded and superseded_by: {target} '
                              f'(python -m scripts.docs.catalogue mark --apply)')
            if banner_line(path, target) not in heads[path].splitlines():
                errors.append(f'{where}: missing the banner line {banner_line(path, target)!r} '
                              '(python -m scripts.docs.catalogue mark --apply)')
    return errors, unverifiable


# ---------------------------------------------------------------- generated entry map

README_PATH = 'docs/README.md'
README_BEGIN = ('<!-- BEGIN GENERATED: catalogue families. Edit docs/knowledge/catalogue.yaml, then run '
                'python -m scripts.docs.catalogue readme -->')
README_END = '<!-- END GENERATED: catalogue families -->'
STATUS_WORDS = {'active': 'current', 'archive': 'historical', 'superseded': 'superseded', 'draft': 'draft'}


def _cell(text: str) -> str:
    return ' '.join(text.split()).replace('|', '\\|')


def _code(text: str) -> str:
    fence = '``' if '`' in text else '`'
    pad = ' ' if fence == '``' else ''
    return f'{fence}{pad}{_cell(text)}{pad}{fence}'


def _status(entry: dict) -> str:
    word = STATUS_WORDS[entry['lifecycle']]
    return f"{word} → {_code(entry['superseded_by'])}" if entry.get('superseded_by') else word


def readme_block(catalogue: dict) -> str:
    """The generated family and store tables for docs/README.md, markers included."""
    families = [e for e in catalogue['entries'] if e['kind'] != 'data_store']
    stores = [e for e in catalogue['entries'] if e['kind'] == 'data_store']
    lines = [README_BEGIN, '',
             f'{len(families)} document families and {len(stores)} local data stores, generated from '
             '`docs/knowledge/catalogue.yaml`. Status words: current = `active`, historical = `archive`.',
             '', '### Document families', '',
             '| Family | Kind | Status | Paths | Purpose |', '| --- | --- | --- | --- | --- |']
    for entry in families:
        paths = ', '.join(_code(p) for p in entry['paths'])
        lines.append(f"| `{entry['id']}` | {entry['kind']} | {_status(entry)} | {paths} | "
                     f"{_cell(entry['purpose'])} |")
    lines += ['', '### Local data stores (untracked, under `data/`)', '',
              '| Store | Names | Status | How to query |', '| --- | --- | --- | --- |']
    for entry in stores:
        names = ', '.join(_code(s) for s in entry['store'])
        how = '; '.join(f"{q['surface']}: {_cell(q['how'])}" for q in entry['query'])
        lines.append(f"| `{entry['id']}` | {names} | {_status(entry)} | {how} |")
    return '\n'.join([*lines, '', README_END])


def render_readme(text: str, catalogue: dict) -> str:
    """``text`` with the generated block between its markers replaced; ValueError without one pair."""
    if text.count(README_BEGIN) != 1 or text.count(README_END) != 1 or text.index(README_BEGIN) > text.index(README_END):
        raise ValueError(f'{README_PATH} needs exactly one {README_BEGIN!r} ... {README_END!r} pair')
    start = text.index(README_BEGIN)
    end = text.index(README_END) + len(README_END)
    return text[:start] + readme_block(catalogue) + text[end:]


def readme_errors(repo: Path, report: Report, catalogue: dict, files: dict[str, IndexEntry]) -> list[str]:
    """The README's generated block in Git's index must equal what the catalogue generates now.

    Read through the gated reader like every other body, so it follows the index (stage
    the regenerated file) and a README that is not tracked is not checked.
    """
    if README_PATH not in files:
        return []
    heads, withheld = read_heads(repo, report, [README_PATH], lines=1_000_000)
    if README_PATH not in heads:
        return [f'{README_PATH}: not content-readable ({withheld} withheld), so its generated block cannot be checked']
    text = heads[README_PATH]
    try:
        current = render_readme(text, catalogue) == text
    except ValueError as exc:
        return [f'{README_PATH}: {str(exc)[:300]}']
    return [] if current else [f'{README_PATH}: the generated family table is stale; run '
                               'python -m scripts.docs.catalogue readme and stage the file']


# ---------------------------------------------------------------- whole-repository check

def repository_check(repo: Path, catalogue_path: Path | None = None) -> tuple[Report, dict]:
    """Everything CI enforces: coverage and validation, store literals, status markers, README block.

    Returns the report (with every error appended) and its catalogue. The extra checks
    run only on a schema-valid catalogue; their failures are typed by message prefix.
    """
    catalogue_path = catalogue_path or repo / CATALOGUE_PATH
    report = coverage(repo, catalogue_path)
    catalogue = load(catalogue_path)
    if not report.schema_ok:
        return report, catalogue
    files = index_entries(repo)
    scan = store_literals(repo, files)
    report.store_literals, report.store_files_scanned = scan.stores, scan.scanned
    report.errors.extend(f'{CODE_ROOT}: cannot read tracked file {shown(p)} (not a regular UTF-8 blob), '
                         'so its store names are unchecked' for p in scan.unread)
    report.errors.extend(f'{CODE_ROOT}: tracked file {shown(p)} is withheld by the privacy gate (an '
                         'inventory-excluded component), so its store names are unchecked; move it'
                         for p in scan.withheld)
    report.errors.extend(store_literal_errors(catalogue, scan.stores))
    errors, report.markers_unverifiable = marker_errors(repo, report, catalogue)
    report.errors.extend(errors)
    report.errors.extend(readme_errors(repo, report, catalogue, files))
    return report, catalogue


# ---------------------------------------------------------------- suggestions

def _slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'family'


def suggest(report: Report, catalogue: dict, roots: tuple[str, ...] = TRACKED_ROOTS) -> str:
    """Paste-ready YAML stubs (indented for ``entries:``), one per uncovered directory.

    Uncovered files directly under a root keep an exact path; nested uncovered
    directories fold into their shallowest uncovered ancestor directory.
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for path in report.uncovered:
        parent = str(PurePosixPath(path).parent)
        groups[path if parent in roots else parent].append(path)
    for key in sorted(groups, key=len):
        ancestor = next((a for a in groups if a != key and a not in groups[a] and key.startswith(a + '/')), None)
        if ancestor:
            groups[ancestor].extend(groups.pop(key))
    families = [e for e in catalogue.get('entries', []) if e.get('kind') != 'data_store']
    stubs = []
    for key, paths in sorted(groups.items()):
        exact = key in paths
        nearest = _nearest(key, families, roots)
        stub = {'id': _slug(key.split('/', 1)[-1]), 'kind': nearest.get('kind', 'doc_family'),
                'paths': [key] if exact else [f'{key}/**'],
                'purpose': 'TODO: one line saying what this family holds and who reads it',
                'keywords': sorted(set(re.findall(r'[a-z0-9]{3,}', key.split('/', 1)[-1].lower()))) or ['todo'],
                'lifecycle': 'active', 'owner': nearest.get('owner', 'docs-knowledge'),
                'query': [{'surface': 'git_grep',
                           'how': f"git grep -n -i -F '<term>' -- {shlex.quote(key)}"}],
                # The stub owns every path in its group, so one excluded path makes it private.
                'content_searchable': not any(is_excluded(p) for p in paths)}
        body = yaml.safe_dump([stub], sort_keys=False, allow_unicode=True, width=1000)
        note = f"  # {len(paths)} uncovered file(s); nearest family: {nearest.get('id', 'none')}\n"
        stubs.append(note + ''.join(f'  {line}' for line in body.splitlines(keepends=True)))
    return ''.join(stubs)


def _nearest(path: str, families: list[dict], roots: tuple[str, ...]) -> dict:
    """The family whose literal glob prefix shares the most segments below the root."""
    root = root_of(path, roots) or ''
    floor = len(root.split('/')) if root else 0

    def shared(pattern: str) -> int:
        count = 0
        for x, y in zip(WILDCARD.split(pattern, 1)[0].split('/'), path.split('/'), strict=False):
            if x != y:
                break
            count += 1
        return count
    scored = [(max((shared(p) for p in e.get('paths', [])), default=0), e) for e in families]
    best = max(scored, key=lambda item: item[0], default=(0, {}))
    return best[1] if best[0] > floor else {}


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='python -m scripts.docs.catalogue',
        description='Validate the document and data catalogue and its coverage of tracked files.\n'
                    'Use before adding a docs/registry/evidence family or a data/ store; '
                    'to find a document or store, use python -m scripts.docs.find instead.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  .venv/bin/python -m scripts.docs.catalogue check\n'
               '  .venv/bin/python -m scripts.docs.catalogue check --report-only --suggest\n'
               '  .venv/bin/python -m scripts.docs.catalogue check --json\n'
               '  .venv/bin/python -m scripts.docs.catalogue check --data-root ../primary-checkout/data\n'
               '  .venv/bin/python -m scripts.docs.catalogue draft-scan --json\n'
               '  .venv/bin/python -m scripts.docs.catalogue readme --check\n'
               '  .venv/bin/python -m scripts.docs.catalogue mark --apply\n'
               'Outputs: check and draft-scan print a report on stdout and never write files (data/ is read by '
               'name only); readme rewrites the generated block of docs/README.md; mark --apply writes '
               'front matter and banners into superseded Markdown files.\n'
               'Exit codes: 0 no errors, full coverage and no unmatched local store (or --report-only; '
               'draft-scan always reports with 0; readme/mark: done or nothing to change); 1 errors (including '
               'a tracked path with control characters, a data/ store named in scripts/ without an entry, '
               'a status marker that disagrees with the catalogue or a stale README block), uncovered paths '
               'or unmatched stores (readme --check: stale block; mark: files need markers); 2 invalid '
               'arguments; 3 unreadable '
               'repository or catalogue, an unmerged index or unexpected Git output, or a catalogue outside '
               'the accepted YAML subset (anchors, aliases, merge keys, tags, duplicate or non-string keys, '
               'unconstructible scalars, over 2 MiB, 100,000 nodes or 16 nesting levels); 4 internal error. Failures print a typed '
               'error (JSON with --json), never a traceback.\n'
               'Related: #9412; docs/knowledge/catalogue.yaml; docs/knowledge/catalogue.schema.json; '
               'scripts/docs/docs_inventory.py; docs/architecture/docs-authority-lifecycle.md.')
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check', help='Validate schema, coverage, globs, supersession, owners, producers, '
                           'data/ store names in scripts/, status markers and the README block (what CI enforces).',
                           description='Validate the catalogue against the Git index of --repo.')
    check.add_argument('--repo', type=Path, default=Path('.'),
                       help='Repository or worktree root (default: current directory); e.g. ../my-worktree.')
    check.add_argument('--catalogue', type=Path, default=None,
                       help=f'Catalogue file (default: <repo>/{CATALOGUE_PATH}).')
    check.add_argument('--report-only', action='store_true',
                       help='Print the report but exit 0 even when errors or gaps exist (default: off).')
    check.add_argument('--suggest', action='store_true',
                       help='Also print a paste-ready YAML stub for each uncovered path group and each '
                            'unclaimed data/ store name (default: off).')
    check.add_argument('--data-root', type=Path, default=None,
                       help='Local store directory to reconcile by name only (default: <repo>/data when it '
                            'exists; skipped otherwise, as in CI); e.g. ../primary-checkout/data.')
    check.add_argument('--json', action='store_true',
                       help='Print the full report as JSON, including per-entry counts (default: text).')
    drafts = sub.add_parser('draft-scan', help='List draft markers in the first 30 lines of every content-readable '
                            'catalogued path against the lifecycle it resolves to (review aid, not a gate).',
                            description='Read each catalogued path from the Git index of --repo and report '
                                        'draft-like markers that disagree with the resolved lifecycle. '
                                        'Inventory-excluded paths and content_searchable: false families '
                                        'are never read; they are counted as withheld.')
    drafts.add_argument('--repo', type=Path, default=Path('.'),
                        help='Repository or worktree root (default: current directory); e.g. ../my-worktree.')
    drafts.add_argument('--json', action='store_true', help='Print the scan as JSON (default: text).')
    readme = sub.add_parser('readme', help=f'Regenerate the family table block of {README_PATH} from the catalogue.',
                            description=f'Rewrite only the text between the generated-block markers of {README_PATH}.')
    readme.add_argument('--repo', type=Path, default=Path('.'),
                        help='Repository or worktree root (default: current directory); e.g. ../my-worktree.')
    readme.add_argument('--check', action='store_true',
                        help='Write nothing; exit 1 when the block differs from the catalogue (default: off).')
    readme.add_argument('--json', action='store_true', help='Print the result as JSON (default: text).')
    mark = sub.add_parser('mark', help='Add front-matter lifecycle/superseded_by and the visible banner to every '
                          'Markdown file a catalogue override marks superseded.',
                          description='Without --apply, list the files that need markers and exit 1 if any do.')
    mark.add_argument('--repo', type=Path, default=Path('.'),
                      help='Repository or worktree root (default: current directory); e.g. ../my-worktree.')
    mark.add_argument('--apply', action='store_true', help='Write the markers (default: list only).')
    mark.add_argument('--json', action='store_true', help='Print the result as JSON (default: text).')
    args = parser.parse_args(argv)
    if args.command == 'draft-scan':
        return _run('Draft scan', _draft_scan_command, args)
    if args.command == 'readme':
        return _run('README block', _readme_command, args)
    if args.command == 'mark':
        return _run('Status markers', _mark_command, args)
    return _run('Catalogue check', _check_command, args)


EXIT_UNREADABLE = 3
EXIT_INTERNAL = 4
UNREADABLE = (OSError, CatalogueLoadError, json.JSONDecodeError, UnicodeDecodeError, yaml.YAMLError,
              subprocess.SubprocessError)  # GitProtocolError is a SubprocessError


def _run(label: str, command, args: argparse.Namespace) -> int:
    """The CLI's totality boundary: any failure becomes a typed report and exit code, never a traceback."""
    try:
        return command(args)
    except UNREADABLE as exc:
        kind = 'catalogue_rejected' if isinstance(exc, CatalogueLoadError) else 'unreadable'
        code, message, status = getattr(exc, 'code', type(exc).__name__), str(exc), EXIT_UNREADABLE
    except Exception as exc:  # deliberate catch-all at the process boundary
        kind, code, message, status = 'internal_error', type(exc).__name__, str(exc), EXIT_INTERNAL
    message = message[:500]
    if args.json:
        print(json.dumps({'error': {'kind': kind, 'code': code, 'message': message}}, indent=2,
                         sort_keys=True, ensure_ascii=False))
    else:
        print(f'{label} could not run ({kind}): {code}: {message}')
    return status


def _check_command(args: argparse.Namespace) -> int:
    repo = toplevel(args.repo)
    catalogue_path = args.catalogue or repo / CATALOGUE_PATH
    report, catalogue = repository_check(repo, catalogue_path)
    data_root = args.data_root or repo / 'data'
    # Store names are reconciled only against a schema-valid catalogue.
    stores = local_store_gaps(data_root, catalogue) if data_root.is_dir() and report.schema_ok else None
    data = report.to_json()
    if args.json:
        data['local_stores'] = (None if stores is None
                                else {'checked': stores[0], 'unmatched': stores[1]})
        print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"denominator {data['denominator']}; covered {data['covered']}; "
              f"uncovered {len(report.uncovered)}; errors {len(report.errors)}; "
              f"families {len(report.entry_counts)}; data stores {report.data_stores}; "
              f"residual paths {data['residual_paths']}")
        print('roots: ' + ', '.join(f'{k} {v}' for k, v in data['root_counts'].items()))
        print('lifecycle: ' + ', '.join(f'{k} {v}' for k, v in data['lifecycle_counts'].items()))
        for error in report.errors:
            print(f'ERROR {error}')
        if report.store_literals is not None:
            print(f'data/ store names in {CODE_ROOT}: {len(report.store_literals)} '
                  f'(from {report.store_files_scanned} tracked text files)')
        for path in report.uncovered:
            print(f'UNCOVERED {shown(path)}')
        if stores is None:
            reason = 'catalogue failed schema validation' if data_root.is_dir() else 'no data directory'
            print(f'local stores: skipped ({reason})')
        else:
            print(f'local stores: {stores[0]} names checked; {len(stores[1])} unmatched')
            for logical in stores[1]:
                print(f'UNMATCHED STORE {shown(logical)}')
    if args.suggest and report.uncovered:
        print(suggest(report, catalogue))
    if args.suggest and report.store_literals:
        for store in unclaimed_stores(catalogue, report.store_literals):
            print(f'  # data/ store named in {CODE_ROOT} without an entry: {shown(store)}')
            print(store_stub(store), end='')
    store_gaps = bool(stores and stores[1])
    return 0 if args.report_only or (report.ok and not store_gaps) else 1


def _readme_command(args: argparse.Namespace) -> int:
    repo = toplevel(args.repo)
    catalogue = load(repo / CATALOGUE_PATH)
    path = repo / README_PATH
    text = path.read_text(encoding='utf-8')
    rendered = render_readme(text, catalogue)
    stale = rendered != text
    if stale and not args.check:
        path.write_text(rendered, encoding='utf-8')
    state = ('stale' if args.check else 'rewritten') if stale else 'current'
    if args.json:
        print(json.dumps({'path': README_PATH, 'state': state}, sort_keys=True))
    else:
        print(f'{README_PATH}: generated block {state}')
    return 1 if stale and args.check else 0


def _mark_command(args: argparse.Namespace) -> int:
    repo = toplevel(args.repo)
    report = coverage(repo)
    catalogue = load(repo / CATALOGUE_PATH)
    if not report.schema_ok:
        raise CatalogueLoadError('schema', 'the catalogue fails validation; run check first')
    changed, withheld = [], []
    for path, target in sorted(superseded_markdown(catalogue).items()):
        if not body_readable(report, path):
            withheld.append(path)  # a private family's file is never read or rewritten
            continue
        file = repo / path
        if file.is_symlink() or not file.is_file():
            withheld.append(path)
            continue
        text = file.read_text(encoding='utf-8')
        marked = apply_marker(text, path, target)
        if marked != text:
            changed.append(path)
            if args.apply:
                file.write_text(marked, encoding='utf-8')
    if args.json:
        print(json.dumps({'changed': changed, 'withheld': len(withheld), 'applied': args.apply}, sort_keys=True))
    else:
        verb = 'marked' if args.apply else 'needs markers'
        for path in changed:
            print(f'{verb}: {shown(path)}')
        print(f'{len(changed)} file(s) {verb}; {len(withheld)} withheld (not content-readable or not a file)')
    return 1 if changed and not args.apply else 0


def _draft_scan_command(args: argparse.Namespace) -> int:
    repo = toplevel(args.repo)
    scan = draft_scan(repo, coverage(repo))
    if args.json:
        print(json.dumps(scan, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    print(f"scanned {scan['scanned']}; withheld by the privacy gate {scan['skipped_private']}; "
          f"binary or missing {scan['binary_or_missing']}; with a marker {scan['with_marker']}")
    print('by marker: ' + ', '.join(f'{k} {v}' for k, v in scan['by_marker'].items()))
    print('by lifecycle: ' + ', '.join(f'{k} {v}' for k, v in scan['with_marker_by_lifecycle'].items()))
    for path, found in scan['active_with_marker'].items():
        print(f"ACTIVE WITH MARKER {path} ({', '.join(found)})")
    for path in scan['draft_without_marker']:
        print(f'DRAFT WITHOUT MARKER {path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
