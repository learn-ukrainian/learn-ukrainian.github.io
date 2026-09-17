"""Deterministic, index-backed documentation inventory (ADR-013 / #5536)."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import subprocess
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt

ROOT_FILES = frozenset({'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'README.md'})
DOC_SUFFIXES = frozenset({'.md', '.mdx', '.rst', '.txt', '.adoc'})
# Explicit read boundary: arbitrary tracked data/private corpora are not inputs.
READ_ROOTS = frozenset({'docs', 'scripts', 'site', 'tests', 'agents_extensions',
                        'contracts', 'memory', 'audit'})
EXCLUDED_PARTS = frozenset({'session-state', 'node_modules', '__pycache__',
                            '.claude', '.codex', '.agent', '.gemini',
                            'private', 'secrets', 'credentials', 'cache', 'caches'})
OUTPUT_ROOT = 'audit/docs-inventory'
OUTPUT_NAMES = frozenset({'manifest.json', 'references.json', 'summary.md', 'digest.sha256'})
PARSE_LIMIT = 512 * 1024
METADATA_LIMIT = 16 * 1024
PARSER = MarkdownIt('commonmark')
LIFECYCLES = frozenset({'draft', 'active', 'superseded', 'archive'})


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)


def permitted(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if path in ROOT_FILES:
        return True
    return bool(parts and parts[0] in READ_ROOTS and not EXCLUDED_PARTS.intersection(parts)
                and not path.startswith(OUTPUT_ROOT + '/')
                and not (path.startswith('docs/knowledge/inventory/')
                         and PurePosixPath(path).name in OUTPUT_NAMES))


def is_document(path: str) -> bool:
    return permitted(path) and (path in ROOT_FILES or PurePosixPath(path).suffix.lower() in DOC_SUFFIXES)


def index_entries(repo: Path) -> dict[str, tuple[str, str]]:
    result = {}
    for record in git(repo, 'ls-files', '--stage', '-z').split(b'\0'):
        if not record:
            continue
        header, raw_path = record.split(b'\t', 1)
        mode, oid, stage = header.decode('ascii').split()
        path = raw_path.decode('utf-8')
        if stage != '0':
            raise ValueError('Unmerged index; resolve conflicts before inventorying.')
        if permitted(path) and mode in {'100644', '100755'}:
            result[path] = (mode, oid)
    return dict(sorted(result.items()))


@contextmanager
def blobs(repo: Path):
    """Read tracked objects, never worktree files or symlink destinations."""
    process = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
    try:
        def read(oid: str) -> bytes:
            process.stdin.write(oid.encode('ascii') + b'\n')
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3 or header[1] != b'blob':
                raise ValueError('Tracked blob unavailable.')
            data = process.stdout.read(int(header[2]))
            if process.stdout.read(1) != b'\n':
                raise ValueError('Invalid Git blob response.')
            return data
        yield read
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()


def histories(repo: Path, paths: set[str]) -> dict[str, dict]:
    """History through HEAD, following paths but intentionally not renames."""
    result = {}
    current = None
    for part in git(repo, 'log', 'HEAD', '--format=%x00%H %cI', '--name-only',
                    '-z', '--no-renames', '--diff-filter=AMDT').split(b'\0'):
        token = part.removeprefix(b'\n').decode('utf-8')
        if re.fullmatch(r'[0-9a-f]{40,64} \S+', token):
            current = token.split(' ', 1)
        elif token in paths and current:
            row = result.setdefault(token, {'latest_commit': current[0],
                                            'latest_at': current[1],
                                            'first_at': current[1], 'commit_count': 0})
            row['first_at'] = current[1]
            row['commit_count'] += 1
    return result


class UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in keys:
                raise yaml.constructor.ConstructorError(None, None, 'invalid or duplicate key', node.start_mark)
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def metadata(text: str) -> tuple[dict, list[str]]:
    """Only typed lifecycle facts escape; no arbitrary YAML values or errors."""
    facts, errors = {}, []
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return facts, errors
    end = next((i for i, line in enumerate(lines[1:], 1) if line in {'---', '...'}), None)
    if end is None:
        return facts, ['frontmatter_unterminated']
    raw = '\n'.join(lines[1:end])
    if len(raw.encode()) > METADATA_LIMIT:
        return facts, ['frontmatter_too_large']
    try:
        depth = 0
        for count, token in enumerate(yaml.scan(raw)):
            if isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)):
                return facts, ['frontmatter_alias_forbidden']
            if isinstance(token, (yaml.tokens.BlockMappingStartToken, yaml.tokens.BlockSequenceStartToken,
                                  yaml.tokens.FlowMappingStartToken, yaml.tokens.FlowSequenceStartToken)):
                depth += 1
            elif isinstance(token, (yaml.tokens.BlockEndToken, yaml.tokens.FlowMappingEndToken,
                                    yaml.tokens.FlowSequenceEndToken)):
                depth -= 1
            if depth > 32 or count > 2048:
                return facts, ['frontmatter_complexity_limit']
        value = yaml.load(raw, Loader=UniqueLoader)
    except (yaml.YAMLError, RecursionError):
        return facts, ['frontmatter_invalid_yaml']
    if not isinstance(value, dict):
        return facts, ['frontmatter_not_mapping']
    for key in ('lifecycle', 'status'):
        if key in value:
            item = value[key]
            if not isinstance(item, str):
                errors.append(f'{key}_not_string')
            elif item.lower() in LIFECYCLES:
                facts[key] = item.lower()
            else:
                errors.append(f'{key}_unrecognized')
    for key in ('supersedes', 'superseded_by'):
        if key in value:
            items = value[key] if isinstance(value[key], list) else [value[key]]
            if all(isinstance(item, str) for item in items):
                facts[key] = sorted(set(items))
            else:
                errors.append(f'{key}_not_string_or_list')
    return facts, errors


def location(path: str) -> str:
    parts = PurePosixPath(path).parts
    if path in ROOT_FILES:
        return 'root_instruction'
    if 'archive' in parts or 'archives' in parts:
        return 'archive'
    if parts[0] == 'audit' or 'generated' in parts:
        return 'generated'
    if 'reference' in parts or 'references' in parts:
        return 'reference'
    if path.startswith(('agents_extensions/shared/rules/', 'contracts/')):
        return 'binding_rule'
    if path.startswith('docs/architecture/adr/'):
        return 'adr'
    if path.startswith(('docs/plans/', 'docs/epics/')):
        return 'planning'
    if path.startswith(('docs/queues/', 'docs/dispatch-briefs/', 'docs/status/')):
        return 'operational'
    return 'curated' if parts[0] == 'docs' else 'supporting'


def target(source: str, raw: str, tracked: set[str]) -> str | None:
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    if '\\' in path or '\x00' in path:
        return None
    relative = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
    candidates = [path.lstrip('/')] if path.startswith('/') else [relative, path]
    # Preserve relative Markdown semantics before accepting repo-root code paths.
    for candidate in candidates:
        if candidate in tracked:
            return candidate
    return None


def references(text: str) -> list[tuple[str, str]]:
    found = []
    for token in PARSER.parse(text):
        for child in token.children or []:
            if child.type == 'link_open':
                found.append(('markdown_link', child.attrGet('href') or ''))
            elif child.type == 'image':
                found.append(('markdown_image', child.attrGet('src') or ''))
            elif child.type == 'code_inline':
                found.append(('code_path', child.content))
    return found


def build(repo: Path) -> tuple[dict, dict]:
    entries = index_entries(repo)
    tracked = set(entries)
    paths = {path for path in entries if is_document(path)}
    head = git(repo, 'rev-parse', 'HEAD').decode().strip()
    history = histories(repo, paths)
    records, edges = [], set()
    duplicates, normalized = defaultdict(list), defaultdict(list)
    with blobs(repo) as read:
        for path in sorted(paths):
            mode, oid = entries[path]
            data = read(oid)
            content_hash = digest(data)
            duplicates[content_hash].append(path)
            row = {'path': path, 'type': PurePosixPath(path).suffix.lstrip('.').lower(),
                   'bytes': len(data), 'lines': len(data.splitlines()), 'sha256': content_hash,
                   'git_blob': oid, 'git_mode': mode, 'history': history.get(path),
                   'location': location(path), 'metadata_errors': [],
                   'authority_markers': [], 'candidate_lifecycle': None,
                   'unresolved_local_references': 0, 'analysis': 'complete'}
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                text = None
                row['analysis'] = 'non_utf8'
            if len(data) > PARSE_LIMIT:
                row['analysis'] = 'size_limit'
            if text is not None and row['analysis'] == 'complete':
                normalized[digest(' '.join(text.split()).encode())].append(path)
                facts, row['metadata_errors'] = metadata(text)
                lifecycle = facts.get('lifecycle', facts.get('status'))
                if lifecycle:
                    row['candidate_lifecycle'] = {'value': lifecycle, 'confidence': 'explicit',
                                                  'evidence': 'frontmatter'}
                elif row['location'] == 'archive':
                    row['candidate_lifecycle'] = {'value': 'archive', 'confidence': 'location_only',
                                                  'evidence': 'archive_path_component'}
                # Record marker labels, never arbitrary prose or metadata bodies.
                row['authority_markers'] = sorted({match.lower() for match in re.findall(
                    r'(?im)^\*\*(Status|Authority|Frozen by|Deciders):?\*\*\s*:?', text[:METADATA_LIMIT])})
                refs = references(text) if row['type'] in {'md', 'mdx'} else []
                for key in ('supersedes', 'superseded_by'):
                    refs.extend((key, item) for item in facts.get(key, []))
                # Root instruction bodies are classified, not included in the graph.
                if path not in ROOT_FILES:
                    for kind, raw in refs:
                        resolved = target(path, raw, tracked)
                        if resolved:
                            edges.add((path, resolved, kind))
                        elif kind != 'code_path' and raw and not raw.startswith('#'):
                            try:
                                external = bool(urlsplit(raw).scheme or urlsplit(raw).netloc)
                            except ValueError:
                                external = False
                            if not external:
                                row['unresolved_local_references'] += 1
            records.append(row)
    graph = {'schema_version': 1, 'edges': [dict(source=s, target=t, kind=k)
                                           for s, t, k in sorted(edges)]}
    inbound, outbound = Counter(t for _, t, _ in edges), Counter(s for s, _, _ in edges)
    for row in records:
        row['inbound_references'] = inbound[row['path']]
        row['outbound_references'] = outbound[row['path']]
    tracked_facts = [[p, *entries[p]] for p in entries]
    manifest = {'schema_version': 1, 'git_commit': head, 'source': 'git_index',
                'tracked_file_digest': digest(canonical(tracked_facts)),
                'history_scope': 'HEAD, path history without rename following',
                'history_shallow': git(repo, 'rev-parse', '--is-shallow-repository').strip() == b'true',
                'policy': {'parse_limit_bytes': PARSE_LIMIT, 'root_files': sorted(ROOT_FILES),
                           'read_roots': sorted(READ_ROOTS),
                           'excluded_components': sorted(EXCLUDED_PARTS)},
                'counts': {'documents': len(records), 'eligible_tracked_files': len(entries),
                           'references': len(edges)},
                'documents': records,
                'exact_duplicates': sorted(v for v in duplicates.values() if len(v) > 1),
                'whitespace_duplicate_candidates': sorted(v for v in normalized.values()
                                                          if len(v) > 1 and
                                                          len({entries[p][1] for p in v}) > 1)}
    inventory_digest = digest(canonical({'manifest': manifest, 'graph': graph}))
    manifest['inventory_digest'] = inventory_digest
    graph['inventory_digest'] = inventory_digest
    return manifest, graph


def summary(manifest: dict) -> str:
    rows = manifest['documents']
    lines = ['# Documentation inventory', '', f"Digest: `{manifest['inventory_digest']}`", '',
             f"Git commit: `{manifest['git_commit']}`; source: Git index blobs.", '',
             f"Documents: {len(rows)}; references: {manifest['counts']['references']}.", '',
             '| Location | Documents |', '| --- | ---: |']
    lines.extend(f'| {key} | {value} |' for key, value in sorted(Counter(r['location'] for r in rows).items()))
    lines.extend(['', f"Metadata errors: {sum(bool(r['metadata_errors']) for r in rows)} documents.",
                  f"Analysis omitted: {sum(r['analysis'] != 'complete' for r in rows)} documents.",
                  f"Exact duplicate groups: {len(manifest['exact_duplicates'])}.",
                  f"Whitespace duplicate groups: {len(manifest['whitespace_duplicate_candidates'])}.",
                  '', 'Candidates are evidence for review, not reclassification. No document bodies are emitted.',
                  'See manifest.json and references.json for paths and backlinks.', ''])
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Inventory tracked documentation deterministically from Git index blobs.\n'
                    'Use for docs-knowledge evidence; not for live state or OpenWiki generation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n  /home/ops/learn-ukrainian/.venv/bin/python scripts/docs/docs_inventory.py\n'
               '  /home/ops/learn-ukrainian/.venv/bin/python scripts/docs/docs_inventory.py --output audit/docs-inventory/run\n'
               'Outputs: manifest.json, references.json, summary.md, digest.sha256; overwrites generated output only.\n'
               'Exit codes: 0 success; 1 invalid Git/input/output; 2 invalid CLI arguments.\n'
               'Related: #5536, #5535; docs/knowledge/inventory/README.md; ADR-013.')
    parser.add_argument('--repo', type=Path, default=Path('.'),
                        help='Repository root (default: current directory); e.g. /path/to/worktree.')
    parser.add_argument('--output', type=Path, default=Path(OUTPUT_ROOT),
                        help='Output directory relative to repository root (default: audit/docs-inventory); '
                             'must be inside audit/docs-inventory to prevent source overwrites.')
    args = parser.parse_args(argv)
    try:
        repo = Path(git(args.repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
        output = (repo / args.output).resolve()
        boundary = repo / OUTPUT_ROOT
        if not output.is_relative_to(boundary) or boundary.resolve() != boundary:
            raise ValueError('Output must stay inside audit/docs-inventory without symlink escapes.')
        for name in OUTPUT_NAMES:
            if (output / name).is_symlink():
                raise ValueError('Output file must not be a symlink.')
        manifest, graph = build(repo)
        output.mkdir(parents=True, exist_ok=True)
        for name, data in {'manifest.json': canonical(manifest), 'references.json': canonical(graph),
                           'summary.md': summary(manifest).encode(),
                           'digest.sha256': (manifest['inventory_digest'] + '\n').encode()}.items():
            (output / name).write_bytes(data)
        print(json.dumps({'inventory_digest': manifest['inventory_digest'], **manifest['counts']}, sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError):
        # Never echo raw Git/parser errors or private input paths.
        print('Inventory failed: check repository/index, UTF-8 paths, and output boundary.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
