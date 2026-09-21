"""Real Git fixtures for docs inventory input, graph, and repeatability boundaries."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import validate

from scripts.docs.docs_inventory import build, canonical, digest, main, metadata

pytestmark = pytest.mark.reads_content


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL, timeout=30)


def put(repo, path, text):
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.email', 'fixture@example.invalid')
    git(tmp_path, 'config', 'user.name', 'Fixture')
    files = {
        '.gitignore': 'docs/ignored.md\naudit/docs-inventory/\n',
        'docs/a.md': '---\nlifecycle: active\nsupersedes: b.md\n---\n'
                     '# A\n[B](b.md#section) [code](../scripts/example.py) '
                     '[excluded](session-state/private.md) [outside](https://example.invalid)\n'
                     '`scripts/example.py`\n',
        'docs/b.md': '# B\n',
        'docs/copy.md': '# B\n',
        'docs/spaced.md': '#  B\n',
        'docs/session-state/private.md': 'SENSITIVE SENTINEL',
        'docs/private/note.md': 'SENSITIVE SENTINEL',
        'wiki/page.md': 'SENSITIVE SENTINEL',
        'curriculum/a1/lesson.md': 'SENSITIVE SENTINEL',
        'data/book.md': 'SENSITIVE SENTINEL',
        '.claude/rules.md': 'SENSITIVE SENTINEL',
        'scripts/example.py': 'print("example")\n',
        'scripts/config/policy.yaml': 'value: true\n',
        **{p: '# Instruction\n[private](docs/b.md)\n' for p in
           ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'README.md')},
    }
    for path, text in files.items():
        put(tmp_path, path, text)
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'fixture')
    put(tmp_path, 'docs/ignored.md', 'IGNORED SENTINEL')
    put(tmp_path, 'docs/untracked.md', 'UNTRACKED SENTINEL')
    return tmp_path


def test_tracked_only_exclusions_graph_and_duplicates(repo):
    manifest, graph = build(repo)
    rows = {r['path']: r for r in manifest['documents']}
    assert set(rows) == {'docs/a.md', 'docs/b.md', 'docs/copy.md', 'docs/spaced.md',
                         'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'README.md'}
    output = canonical([manifest, graph]).decode()
    for forbidden in ('SENSITIVE', 'IGNORED', 'UNTRACKED', 'ignored.md', 'untracked.md',
                      'session-state/private.md', 'wiki/page.md', 'data/book.md'):
        assert forbidden not in output
    assert {'source': 'docs/a.md', 'target': 'docs/b.md', 'kind': 'supersedes'} in graph['edges']
    assert {'source': 'docs/a.md', 'target': 'scripts/example.py', 'kind': 'code_path'} in graph['edges']
    assert rows['docs/a.md']['unresolved_local_references'] == 1
    assert rows['docs/b.md']['inbound_references'] == 2
    assert rows['AGENTS.md']['outbound_references'] == 0
    assert ['docs/b.md', 'docs/copy.md'] in manifest['exact_duplicates']
    assert ['docs/b.md', 'docs/copy.md', 'docs/spaced.md'] in manifest['whitespace_duplicate_candidates']
    assert rows['docs/a.md']['candidate_lifecycle']['value'] == 'active'
    assert rows['docs/a.md']['history']['commit_count'] == 1


def test_determinism_index_sparse_and_digest(repo, tmp_path_factory):
    first = build(repo)
    put(repo, 'docs/a.md', 'UNSTAGED SECRET')
    (repo / 'docs/b.md').unlink()  # A sparse/missing worktree file is still inventoried.
    assert canonical(build(repo)) == canonical(first)
    clone = tmp_path_factory.mktemp('clone')
    git(clone, 'clone', '-q', str(repo), '.')
    assert canonical(build(clone)) == canonical(first)
    git(repo, 'add', 'docs/a.md')
    changed, graph = build(repo)
    assert changed['git_commit'] == first[0]['git_commit']
    assert changed['inventory_digest'] != first[0]['inventory_digest']
    expected = changed.pop('inventory_digest')
    graph.pop('inventory_digest')
    assert digest(canonical({'manifest': changed, 'graph': graph})) == expected


@pytest.mark.parametrize(('body', 'error'), [
    ('---\nstatus: [broken\n---\n', 'frontmatter_invalid_yaml'),
    ('---\n- item\n---\n', 'frontmatter_not_mapping'),
    ('---\nstatus: true\n---\n', 'status_not_string'),
    ('---\nsupersedes: [one, 2]\n---\n', 'supersedes_not_string_or_list'),
    ('---\nstatus: active\nstatus: draft\n---\n', 'frontmatter_invalid_yaml'),
    ('---\na: &a [*a]\n---\n', 'frontmatter_alias_forbidden'),
    ('---\na: ' + '[' * 40 + 'x' + ']' * 40 + '\n---\n', 'frontmatter_complexity_limit'),
    ('---\nstatus: active', 'frontmatter_unterminated'),
    ('---\nstatus: mystery\n---\n', 'status_unrecognized'),
])
def test_malformed_metadata(body, error):
    _, errors = metadata(body)
    assert error in errors


def test_symlinks_conflicts_and_analysis_limits(repo):
    (repo / 'docs/link.md').symlink_to('a.md')
    put(repo, 'docs/large.md', 'A' * (512 * 1024 + 1))
    (repo / 'docs/binary.md').write_bytes(b'\xff\xfe')
    put(repo, 'docs/marker.md', '**Status:** Binding\n**Authority**: contract\n')
    git(repo, 'add', 'docs/link.md', 'docs/large.md', 'docs/binary.md', 'docs/marker.md')
    manifest, _ = build(repo)
    rows = {r['path']: r for r in manifest['documents']}
    assert 'docs/link.md' not in rows
    assert rows['docs/large.md']['analysis'] == 'size_limit'
    assert rows['docs/binary.md']['analysis'] == 'non_utf8'
    assert rows['docs/marker.md']['authority_markers'] == ['authority', 'status']
    oid = git(repo, 'rev-parse', 'HEAD:docs/a.md').decode().strip()
    subprocess.run(['git', '-C', str(repo), 'update-index', '--index-info'],
                   input=f'100644 {oid} 1\tdocs/conflict.md\n'.encode(), check=True, timeout=30)
    with pytest.raises(ValueError, match='Unmerged'):
        build(repo)


def test_cli_identical_outputs_schema_and_output_guard(repo):
    script = Path(__file__).resolve().parents[1] / 'scripts/docs/docs_inventory.py'
    command = [sys.executable, str(script), '--repo', str(repo)]
    subprocess.run(command, check=True, capture_output=True, timeout=60)
    output = repo / 'audit/docs-inventory'
    first = {p.name: p.read_bytes() for p in output.iterdir()}
    subprocess.run(command, check=True, capture_output=True, timeout=60)
    assert first == {p.name: p.read_bytes() for p in output.iterdir()}
    schema = json.loads((script.parents[2] / 'docs/knowledge/inventory/manifest.schema.json').read_text())
    validate(json.loads(first['manifest.json']), schema)
    assert len(first['summary.md']) < 3000
    assert main(['--repo', str(repo), '--output', 'docs']) == 1
    (output / 'manifest.json').unlink()
    (output / 'manifest.json').symlink_to(repo / 'docs/a.md')
    assert main(['--repo', str(repo)]) == 1


def test_reference_definitions_encoding_and_config(repo):
    put(repo, 'docs/space name.md', '# Space\n')
    put(repo, 'docs/links.md', '**Supersedes:** [previous](space%20name.md)\n'
                             '[ref][x]\n\n[x]: <space%20name.md#heading>\n'
                             '`scripts/config/policy.yaml`\n'
                             '```md\n[fake](b.md)\n```\n')
    git(repo, 'add', 'docs/space name.md', 'docs/links.md')
    _, graph = build(repo)
    edges = [e for e in graph['edges'] if e['source'] == 'docs/links.md']
    assert {'source': 'docs/links.md', 'target': 'docs/space name.md', 'kind': 'supersedes'} in edges
    assert {e['target'] for e in edges} == {'docs/space name.md', 'scripts/config/policy.yaml'}
