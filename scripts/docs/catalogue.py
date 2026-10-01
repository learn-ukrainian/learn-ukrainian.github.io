"""Document and data catalogue: load, validate and measure coverage (#9412).

The catalogue (``docs/knowledge/catalogue.yaml``) records document *families*
and logical *data stores*, not one entry per file. It extends the ADR-013
inventory (``scripts/docs/docs_inventory.py``) and the lifecycle contract in
``docs/architecture/docs-authority-lifecycle.md``; it does not replace them.

The coverage denominator is every path Git's index lists under the tracked
roots, so the check is sparse-checkout safe and never reads ``data/``.
"""
from __future__ import annotations

import argparse
import json
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


def shown(path: str) -> str:
    """A path for one line of text output: escaped (repr) when it holds control characters."""
    return repr(path) if CONTROL_CHARS.search(path) else path


def control_path_error(path: str) -> str:
    return (f'tracked path {path!r} contains control characters; rename it '
            '(such paths are never catalogued or read)')


def under_roots(path: str, roots=TRACKED_ROOTS) -> bool:
    return any(path == root or path.startswith(root + '/') for root in roots)


def is_excluded(path: str) -> bool:
    """True when the docs inventory's privacy exclusion covers ``path`` (one shared list)."""
    return bool(EXCLUDED_PARTS.intersection(PurePosixPath(path).parts))


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


def compile_globs(entry_id: str, patterns: list[str]) -> list[Glob]:
    return [Glob(entry_id, p, glob_regex(p), specificity(p)) for p in patterns]


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

    @property
    def ok(self) -> bool:
        return not self.errors and not self.uncovered

    def lifecycle_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(life for _, life in self.resolved.values()).items()))

    def to_json(self) -> dict:
        return {'denominator': self.denominator, 'covered': len(self.resolved),
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

    globs: list[Glob] = []
    for entry in entries:
        eid = entry['id']
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
            in_git = [p for p in files if PurePosixPath(p).name not in PLACEHOLDER_NAMES
                      and any(claim.match(p) for claim in claims)]
            if entry['local_only'] and in_git:
                report.errors.append(f'{eid}: local_only is true but {len(in_git)} store files are tracked')
            elif not entry['local_only'] and not in_git:
                report.errors.append(f'{eid}: local_only is false but no store file is tracked')
            continue
        try:
            compiled = compile_globs(eid, entry['paths'])
        except ValueError as exc:
            report.errors.append(f'{eid}: {exc}')
            continue
        for glob in compiled:
            if is_catch_all(glob.pattern, roots):
                report.errors.append(f'{eid}: glob {glob.pattern!r} is a catch-all (the first segment '
                                     'below its tracked root must be literal)')
            elif root_of(glob.pattern, roots) is None and glob.pattern not in roots:
                report.errors.append(f'{eid}: glob {glob.pattern!r} is outside the tracked roots')
            elif not any(glob.regex.match(p) for p in denominator):
                report.errors.append(f'{eid}: glob {glob.pattern!r} matches no tracked file')
        globs.extend(compiled)

    # Resolve each tracked path to exactly one family: most specific glob wins.
    owner_of: dict[str, str] = {}
    for path in denominator:
        best: dict[str, tuple[int, int, int]] = {}
        for glob in globs:
            if glob.regex.match(path) and glob.rank > best.get(glob.entry, (-1, -1, -1)):
                best[glob.entry] = glob.rank
        if not best:
            report.uncovered.append(path)
            continue
        top = max(best.values())
        winners = sorted(e for e, rank in best.items() if rank == top)
        if len(winners) > 1:
            report.errors.append(f'{path}: ambiguous match between {", ".join(winners)}')
            continue
        owner_of[path] = winners[0]

    # Privacy follows ownership: a family that owns any inventory-excluded path
    # (docs_inventory.EXCLUDED_PARTS) must not be content-searchable.
    excluded_owned: dict[str, list[str]] = defaultdict(list)
    for path, eid in owner_of.items():
        if is_excluded(path):
            excluded_owned[eid].append(path)
    for eid, paths in sorted(excluded_owned.items()):
        if by_id[eid]['content_searchable']:
            report.errors.append(f'{eid}: owns {len(paths)} inventory-excluded path(s) such as {paths[0]!r}, '
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
                report.errors.append(f"{entry['id']}: duplicate override for {path!r}")
            seen.add(path)
            if path not in tracked:
                report.errors.append(f"{entry['id']}: override {path!r} is not a tracked path")
            elif owner_of.get(path) != entry['id']:
                report.errors.append(f"{entry['id']}: override {path!r} resolves to "
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
                errors.append(f'supersession cycle or self-link: {" -> ".join([*chain, target])}')
                break
            status = state(target)
            if status is None:
                errors.append(f'{current}: supersession target {link!r} does not exist')
                break
            chain.append(target)
            if status in TERMINAL_LIFECYCLES:
                break
            if status != 'superseded' or target not in follow:
                errors.append(f'{start}: supersession chain ends at {target!r} with lifecycle {status!r}')
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

    True only for a path that resolves to a content-searchable family and has no
    inventory-excluded component (docs_inventory.EXCLUDED_PARTS) and no control
    character. Everything else, including unresolved paths, stays unread.
    ``read_heads`` is the only body reader and applies this gate itself, so a
    scanner cannot bypass it.
    """
    owner = report.resolved.get(path)
    return (owner is not None and owner[0] in report.searchable_entries and not is_excluded(path)
            and not CONTROL_CHARS.search(path))


def _index_blobs(repo: Path, objects: dict[str, str]) -> dict[str, bytes]:
    """Blob contents keyed by path, requested by index object ID. Call only via read_heads.

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
                    'not a content search tool.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  .venv/bin/python -m scripts.docs.catalogue check\n'
               '  .venv/bin/python -m scripts.docs.catalogue check --report-only --suggest\n'
               '  .venv/bin/python -m scripts.docs.catalogue check --json\n'
               '  .venv/bin/python -m scripts.docs.catalogue check --data-root ../primary-checkout/data\n'
               '  .venv/bin/python -m scripts.docs.catalogue draft-scan --json\n'
               'Outputs: a report on stdout only; never writes files and reads data/ names, not contents.\n'
               'Exit codes: 0 no errors, full coverage and no unmatched local store (or --report-only; '
               'draft-scan always reports with 0); 1 errors (including a tracked path with control '
               'characters), uncovered paths or unmatched stores; 2 invalid arguments; 3 unreadable '
               'repository or catalogue, an unmerged index or unexpected Git output, or a catalogue outside '
               'the accepted YAML subset (anchors, aliases, merge keys, tags, duplicate or non-string keys, '
               'unconstructible scalars, over 2 MiB, 100,000 nodes or 16 nesting levels); 4 internal error. Failures print a typed '
               'error (JSON with --json), never a traceback.\n'
               'Related: #9412; docs/knowledge/catalogue.yaml; docs/knowledge/catalogue.schema.json; '
               'scripts/docs/docs_inventory.py; docs/architecture/docs-authority-lifecycle.md.')
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check', help='Validate schema, coverage, globs, supersession, owners and producers.',
                           description='Validate the catalogue against the Git index of --repo.')
    check.add_argument('--repo', type=Path, default=Path('.'),
                       help='Repository or worktree root (default: current directory); e.g. ../my-worktree.')
    check.add_argument('--catalogue', type=Path, default=None,
                       help=f'Catalogue file (default: <repo>/{CATALOGUE_PATH}).')
    check.add_argument('--report-only', action='store_true',
                       help='Print the report but exit 0 even when errors or gaps exist (default: off).')
    check.add_argument('--suggest', action='store_true',
                       help='Also print a paste-ready YAML stub for each uncovered path group (default: off).')
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
    args = parser.parse_args(argv)
    if args.command == 'draft-scan':
        return _run('Draft scan', _draft_scan_command, args)
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
    report = coverage(repo, catalogue_path)
    catalogue = load(catalogue_path)
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
        for path in report.uncovered:
            print(f'UNCOVERED {path}')
        if stores is None:
            reason = 'catalogue failed schema validation' if data_root.is_dir() else 'no data directory'
            print(f'local stores: skipped ({reason})')
        else:
            print(f'local stores: {stores[0]} names checked; {len(stores[1])} unmatched')
            for logical in stores[1]:
                print(f'UNMATCHED STORE {shown(logical)}')
    if args.suggest and report.uncovered:
        print(suggest(report, catalogue))
    store_gaps = bool(stores and stores[1])
    return 0 if args.report_only or (report.ok and not store_gaps) else 1


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
