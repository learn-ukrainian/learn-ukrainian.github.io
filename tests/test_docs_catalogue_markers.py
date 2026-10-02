"""Catalogue PR 2 (#9412): store names in code, in-place status markers, the generated README
block, engine-independent schema patterns and escaped diagnostics. Fixtures only; the
real-tree gate is ``tests/test_docs_catalogue_coverage.py``."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.docs import catalogue as cat
from scripts.docs.catalogue import (
    README_BEGIN,
    README_END,
    apply_marker,
    banner_line,
    main,
    readme_block,
    render_readme,
    repository_check,
    shown,
    store_literal_errors,
    store_literals_in_source,
    store_stub,
    validate,
)

REPO = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO / 'docs/knowledge/catalogue.schema.json').read_text(encoding='utf-8'))
BIDI = chr(0x202E)
BOM = chr(0xFEFF)
NEL = chr(0x85)
LS, PS = chr(0x2028), chr(0x2029)


def entry(eid, paths, **extra):
    data = {'id': eid, 'kind': 'doc_family', 'paths': paths, 'purpose': f'{eid} documents',
            'keywords': [eid], 'lifecycle': 'active', 'owner': 'infra-harness',
            'query': [{'surface': 'git_grep', 'how': f'git grep -n -F x -- {paths[0]}'}],
            'content_searchable': True}
    data.update(extra)
    return data


def store(eid, names, **extra):
    data = {'id': eid, 'kind': 'data_store', 'store': names, 'producer': ['scripts/build.py'], 'local_only': True,
            'purpose': f'{eid} store', 'keywords': [eid], 'lifecycle': 'active', 'owner': 'infra-harness',
            'query': [{'surface': 'sqlite', 'how': 'read-only SQL'}], 'content_searchable': False}
    data.update(extra)
    return data


def catalogue(*entries, **extra):
    return {'schema_version': 1,
            'denominator': {'tracked_roots': ['docs', 'registry', 'curriculum/l2-uk-en/evidence'],
                            'local_store_root': 'data'},
            'status_mapping': {'current': 'active', 'historical': 'archive', 'superseded': 'superseded'},
            'entries': list(entries), 'residual': [], **extra}


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=True, timeout=30).stdout


def make_repo(root, data, files):
    root.mkdir(parents=True, exist_ok=True)
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    git(root, 'config', 'user.name', 'Fixture')
    base = {
        'docs/knowledge/catalogue.schema.json': json.dumps(SCHEMA),
        'docs/knowledge/catalogue.yaml': yaml.safe_dump(data, allow_unicode=True),
        'scripts/build.py': "print('x')\n",
        'scripts/config/issue_streams.yaml': 'streams:\n  docs-knowledge: {epics: [1]}\n',
        'scripts/config/area_assignments.yaml': 'assignments:\n  infra-harness: {slots: []}\n',
    }
    for rel, text in {**base, **files}.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding='utf-8')
    git(root, 'add', '.')
    return root


def recatalogue(repo, data):
    (repo / 'docs/knowledge/catalogue.yaml').write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')
    git(repo, 'add', '.')


# ------------------------------------------------------------------ store names in scripts/

@pytest.mark.parametrize('source, expected', [
    ("DB = 'data/main.db'\n", {'data/main.db'}),
    ("p = f'{root}/data/telemetry/x.sqlite3'\n", {'data/telemetry/x.sqlite3'}),
    ("p = ROOT / 'data' / 'side' / 'k.sqlite'\n", {'data/side/k.sqlite'}),
    ("DATA_DIR = ROOT / 'data'\nDB = DATA_DIR / 'v.db'\n", {'data/v.db'}),
    ("BASE = ROOT / 'data' / 'lexicon'\nDB = BASE / 'cache' / 'raw.sqlite'\n", {'data/lexicon/cache/raw.sqlite'}),
    ("help = 'Defaults to data/a.db.'\n", {'data/a.db'}),
    ("# reads data/commented.db\n", {'data/commented.db'}),  # comments count: stricter, never laxer
    ("x = 'metadata/m.db'; y = 'test_data/t.db'; z = 'data/x.json'\n", set()),
    ("p = ROOT / 'data' / name / 'x.db'\n", set()),  # a dynamic segment is not a literal store name
    ("p = ROOT / 'other' / 'x.db'\n", set()),
    ("def broken(:\n  'data/syntax.db'\n", {'data/syntax.db'}),  # text match survives a parse error
])
def test_store_names_in_source(source, expected):
    assert store_literals_in_source(source) == expected


# Every form below names a store; each line is one file's text (the language does not matter).
@pytest.mark.parametrize('text, expected', [
    # the reviewer's mutations
    ('sqlite3 data/unclaimed9412.db "select 1"\n', {'data/unclaimed9412.db'}),  # .sh, unquoted
    ("const db = new Database('data/unclaimed9412.db');\n", {'data/unclaimed9412.db'}),  # .js
    ("DB = 'data/словник9412.db'\n", {'data/словник9412.db'}),
    ("DB = 'data/new store9412.db'\n", {'data/new store9412.db'}),
    # shell words: unquoted, single-quoted, double-quoted, escaped space, assignment, redirect
    ("cp 'data/single9412.db' /tmp\n", {'data/single9412.db'}),
    ('DB="data/double9412.sqlite3"; sqlite3 "$DB"\n', {'data/double9412.sqlite3'}),
    ('cp data/new\\ store9412.db x\n', {'data/new store9412.db'}),
    ('sqlite3 data/a9412.db<q.sql>out.txt\n', {'data/a9412.db'}),
    ('"data/двоє слів/каталог.duckdb"\n', {'data/двоє слів/каталог.duckdb'}),
    # config and markup
    ('store: data/yaml9412.db\nother: [data/b9412.sqlite, data/c9412.db]\n',
     {'data/yaml9412.db', 'data/b9412.sqlite', 'data/c9412.db'}),
    ('{"db": "data/json9412.db"}\n', {'data/json9412.db'}),
    ('ExecStart=/usr/bin/tool --db=../data/unit9412.db\n', {'data/unit9412.db'}),
    # comments count (one exemption at worst; a missed store would pass the gate)
    ('# reads data/comment9412.db at start\n', {'data/comment9412.db'}),
    ('// data/jscomment9412.db\n', {'data/jscomment9412.db'}),
    # a sidecar or copy names its store
    ('data/main.db-wal data/main.db.bak\n', {'data/main.db'}),
])
def test_store_names_in_any_text(text, expected):
    assert cat.store_names_in_text(text) == expected
    assert store_literals_in_source(text, python=False) == expected


@pytest.mark.parametrize('text', [
    'metadata/m.db test_data/t.db my-data/x.db .data/y.db\n',  # not the data/ root
    'data/x.dbx data/x.json data/x.db_old data/xdb\n',  # not a store extension
    "f'data/{name}.db' data/$NAME.db data/*.db data/x?.db data/[ab].db\n",  # built at run time or a glob
    "'data/../escape.db' 'data/./here.db' data//double.db\n",  # dot and empty segments
    '# see data/ and the backups/x.db\n',  # prose: a space after data/ ends the word
    "msg = 'see data/ and backups/x.db'\n",  # a quoted segment never starts with a space
    "msg = 'data/dir /x.db'\n",  # nor ends with one
])
def test_text_that_names_no_store(text):
    assert cat.store_names_in_text(text) == set()


def test_store_literal_errors_name_the_file_and_the_fix():
    data = catalogue(store('main', ['data/main.db']), store('tele', ['data/telemetry/']))
    literals = {'data/main.db': ['scripts/a.py'], 'data/telemetry/x.db': ['scripts/b.py'],
                'data/new.db': ['scripts/c.py', 'scripts/d.py']}
    errors = store_literal_errors(data, literals)
    assert len(errors) == 1
    assert "'data/new.db' (named in scripts/c.py, scripts/d.py) has no data_store entry" in errors[0]


def test_exemptions_must_be_live_and_not_redundant():
    data = catalogue(store('main', ['data/main.db']), store_literal_exemptions=[
        {'literal': 'data/main.db', 'reason': 'redundant'}, {'literal': 'data/gone.db', 'reason': 'stale entry'},
        {'literal': 'data/example.db', 'reason': 'help text only'}])
    errors = store_literal_errors(data, {'data/main.db': ['scripts/a.py'], 'data/example.db': ['scripts/b.py']})
    assert any("'data/main.db' is claimed by a data_store entry and also exempted" in e for e in errors)
    assert any("'data/gone.db' is no longer named in scripts/" in e for e in errors)
    assert not any('example.db' in e for e in errors)
    assert validate(data, SCHEMA, [], {'infra-harness'}).schema_ok


def test_store_stub_is_a_pasteable_entry_that_claims_the_name():
    [stub] = yaml.safe_load(store_stub('data/telemetry/new_thing.db'))
    assert stub['store'] == ['data/telemetry/new_thing.db'] and stub['kind'] == 'data_store'
    report = validate(catalogue(stub), SCHEMA, ['scripts/build.py'], {'infra-harness'})
    assert report.schema_ok  # it pastes cleanly, and the validator still demands a real purpose
    assert any('purpose is still a TODO placeholder' in e for e in report.errors)


def test_check_fails_on_an_unclaimed_store_and_suggests_a_stub(tmp_path, capsys):
    repo = make_repo(tmp_path / 'r', catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge')),
                     {'scripts/tool.py': "DB = 'data/fresh.db'\n"})
    assert main(['check', '--repo', str(repo), '--suggest']) == 1
    out = capsys.readouterr().out
    assert "ERROR store literal 'data/fresh.db' (named in scripts/tool.py)" in out
    stub_text = out[out.index('  # data/ store named in scripts/'):]
    stub = yaml.safe_load('\n'.join(stub_text.splitlines()[1:]))[0]
    assert stub['store'] == ['data/fresh.db']
    data = yaml.safe_load((repo / 'docs/knowledge/catalogue.yaml').read_text())
    data['entries'].append(store('data-fresh', ['data/fresh.db']))
    recatalogue(repo, data)
    assert main(['check', '--repo', str(repo)]) == 0


def test_store_scan_reads_tracked_regular_code_only(tmp_path):
    repo = make_repo(tmp_path / 'r', catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge')),
                     {'scripts/tool.py': "DB = 'data/a.db'\n"})
    (repo / 'scripts/untracked.py').write_text("DB = 'data/untracked.db'\n")
    os.symlink(repo / 'scripts/tool.py', repo / 'scripts/link.py')
    git(repo, 'add', 'scripts/link.py')
    scan = cat.store_literals(repo)
    assert scan.stores == {'data/a.db': ['scripts/tool.py']}
    assert scan.unread == ['scripts/link.py'] and scan.withheld == []


SCRIPT_SURFACE = {
    'scripts/run.sh': 'sqlite3 data/unquoted9412.db ".tables"\ncp \'data/single9412.db\' x\nDB="data/double9412.db"\n',
    'scripts/web/app.js': "const db = new Database('data/js9412.db');\n",
    'scripts/web/app.mjs': "export const DB = 'data/mjs9412.sqlite';\n",
    'scripts/web/app.ts': 'const DB: string = "data/ts9412.duckdb";\n',
    'scripts/config/stores.yaml': 'store: data/yaml9412.db\n',
    'scripts/config/stores.toml': 'db = "data/toml9412.db"\n',
    'scripts/config/stores.json': '{"db": "data/json9412.db"}\n',
    'scripts/README.md': 'Run against `data/markdown9412.db`.\n',
    'scripts/templates/x.j2': '{{ root }}/data/jinja9412.db\n',
    'scripts/units/x.service': 'ExecStart=/bin/tool --db data/unit9412.db\n',
    'scripts/units/x.timer': '# keeps data/timer9412.db fresh\n',
    'scripts/bin/tool': '#!/usr/bin/env bash\nexec sqlite3 data/shebang9412.db\n',
    'scripts/notes': 'no shebang, still text: data/plain9412.db\n',
    'scripts/unicode.py': "DB = 'data/словник9412.db'\nOTHER = 'data/new store9412.db'\n",
    'scripts/x.ps1': '$db = "data/ps9412.db"\n',
}


def test_store_scan_covers_every_tracked_text_file_under_scripts(tmp_path, capsys):
    """The surface is the index under scripts/, not a list of extensions."""
    repo = make_repo(tmp_path / 'r', catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge')),
                     SCRIPT_SURFACE)
    scan = cat.store_literals(repo)
    expected = {name for text in SCRIPT_SURFACE.values() for name in cat.store_names_in_text(text)}
    assert set(scan.stores) == expected and len(expected) == 18
    assert scan.stores['data/new store9412.db'] == ['scripts/unicode.py']
    assert scan.scanned == len(SCRIPT_SURFACE) + 3 and scan.unread == [] and scan.withheld == []
    assert main(['check', '--repo', str(repo)]) == 1
    out = capsys.readouterr().out
    for name in expected:
        assert f'ERROR store literal {name!r}' in out


def test_paths_outside_scripts_and_lookalike_names_are_not_required(tmp_path, capsys):
    repo = make_repo(tmp_path / 'r', catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge')),
                     {'tests/test_fixture.py': "DB = 'data/fixture9412.db'\n",
                      'tests/fixtures/run.sh': 'sqlite3 data/fixture9412.db\n',
                      'docs/knowledge/note.md': 'data/doc9412.db\n',
                      'scripts/lookalike.py': "M = 'metadata/m9412.db'; T = 'test_data/t9412.db'\n"
                                              "J = 'data/j9412.json'; F = f'data/{name}.db'\n"})
    assert cat.store_literals(repo).stores == {}
    assert main(['check', '--repo', str(repo)]) == 0, capsys.readouterr().out


def test_store_scan_reads_the_index_blob_not_the_worktree(tmp_path):
    repo = make_repo(tmp_path / 'r', catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge')),
                     {'scripts/tool.sh': 'sqlite3 data/staged9412.db\n'})
    (repo / 'scripts/tool.sh').write_text('sqlite3 data/unstaged9412.db\n')  # edited, not staged
    assert list(cat.store_literals(repo).stores) == ['data/staged9412.db']
    (repo / 'scripts/tool.sh').unlink()  # a sparse or deleted worktree file is still read from the index
    assert list(cat.store_literals(repo).stores) == ['data/staged9412.db']


def test_store_scan_skips_binary_and_fails_closed_on_unreadable_or_withheld(tmp_path, capsys):
    repo = make_repo(tmp_path / 'r', catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge')),
                     {'scripts/cache/helper.py': "DB = 'data/hidden9412.db'\n"})
    (repo / 'scripts/blob.bin').write_bytes(b'\0\1data/binary9412.db')
    (repo / 'scripts/latin1.txt').write_bytes('café data/latin9412.db\n'.encode('latin-1'))
    git(repo, 'add', '.')
    scan = cat.store_literals(repo)
    assert scan.stores == {} and scan.binary == 1
    assert scan.unread == ['scripts/latin1.txt'] and scan.withheld == ['scripts/cache/helper.py']
    assert main(['check', '--repo', str(repo)]) == 1
    out = capsys.readouterr().out
    assert "cannot read tracked file scripts/latin1.txt (not a regular UTF-8 blob)" in out
    assert 'tracked file scripts/cache/helper.py is withheld by the privacy gate' in out
    assert 'hidden9412' not in out and 'latin9412' not in out  # bodies are never echoed


# ------------------------------------------------------------------ in-place status markers

def test_apply_marker_adds_front_matter_and_banner_after_the_title():
    text = '# Old spec\n\nBody.\n'
    marked = apply_marker(text, 'docs/a/old.md', 'docs/b/new.md')
    assert marked == ('---\nlifecycle: superseded\nsuperseded_by: docs/b/new.md\n---\n\n# Old spec\n\n'
                      '> **Superseded by:** [docs/b/new.md](../b/new.md)\n\nBody.\n')
    assert apply_marker(marked, 'docs/a/old.md', 'docs/b/new.md') == marked  # idempotent


def test_apply_marker_keeps_existing_front_matter_and_replaces_an_old_banner():
    text = '---\ntitle: X\nlifecycle: active\n---\n# T\n\n> **Superseded by:** [old](old.md)\n'
    marked = apply_marker(text, 'docs/x.md', 'docs/y.md#part')
    assert marked.startswith('---\ntitle: X\nlifecycle: superseded\nsuperseded_by: docs/y.md#part\n---\n')
    assert '> **Superseded by:** [docs/y.md#part](y.md#part)' in marked
    assert marked.count('Superseded by') == 1


def test_banner_links_resolve_from_the_file_and_quote_awkward_targets():
    assert banner_line('docs/decisions/a.md', 'AGENTS.md') == '> **Superseded by:** [AGENTS.md](../../AGENTS.md)'
    assert banner_line('docs/a.md', 'docs/with space.md').endswith('(<with space.md>)')
    assert banner_line('docs/a.md', 'id:family-x') == ('> **Superseded by:** [id:family-x]'
                                                        '(knowledge/catalogue.yaml)')


def marker_repo(tmp_path, files, *overrides):
    data = catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge'),
                     entry('guide', ['docs/guide/**'], overrides=list(overrides)),
                     entry('guide-private', ['docs/guide/private/**'], content_searchable=False))
    return make_repo(tmp_path / 'r', data, {'docs/guide/private/p.md': '# Private\n', **files})


SUPERSEDED = {'path': 'docs/guide/old.md', 'lifecycle': 'superseded', 'superseded_by': 'docs/guide/new.md',
              'evidence': 'Replaced by the new guide.'}


def test_markers_are_required_for_superseded_markdown_overrides_and_mark_writes_them(tmp_path, capsys):
    repo = marker_repo(tmp_path, {'docs/guide/old.md': '# Old\n', 'docs/guide/new.md': '# New\n'}, SUPERSEDED)
    report, _ = repository_check(repo)
    errors = [e for e in report.errors if e.startswith('docs/guide/old.md')]
    assert len(errors) == 2 and 'lifecycle: superseded' in errors[0] and 'banner' in errors[1]
    assert main(['mark', '--repo', str(repo)]) == 1  # lists, writes nothing
    assert (repo / 'docs/guide/old.md').read_text() == '# Old\n'
    assert main(['mark', '--repo', str(repo), '--apply']) == 0
    capsys.readouterr()
    git(repo, 'add', '.')
    assert repository_check(repo)[0].errors == []
    assert main(['mark', '--repo', str(repo)]) == 0


@pytest.mark.parametrize('front, message', [
    ('lifecycle: archive', "front-matter lifecycle 'archive' disagrees with the catalogue ('active'"),
    ('superseded_by: docs/guide/new.md', 'front-matter superseded_by'),
    ('lifecycle: obsolete', 'front matter lifecycle unrecognized'),
])
def test_front_matter_that_disagrees_with_the_catalogue_fails(tmp_path, front, message):
    repo = marker_repo(tmp_path, {'docs/guide/a.md': f'---\n{front}\n---\n# A\n', 'docs/guide/new.md': '# N\n'})
    assert any(message in e for e in repository_check(repo)[0].errors), repository_check(repo)[0].errors


def test_front_matter_that_agrees_passes_and_private_files_are_never_read(tmp_path):
    repo = marker_repo(tmp_path, {'docs/guide/a.md': '---\nlifecycle: active\n---\n# A\n',
                                  'docs/guide/private/p.md': '---\nlifecycle: archive\n---\n'})
    report, _ = repository_check(repo)
    assert report.errors == [] and report.markers_unverifiable == 0


def test_a_wrong_replacement_in_front_matter_fails(tmp_path):
    marked = apply_marker('# Old\n', 'docs/guide/old.md', 'docs/guide/other.md')
    repo = marker_repo(tmp_path, {'docs/guide/old.md': marked, 'docs/guide/new.md': '# N\n',
                                  'docs/guide/other.md': '# O\n'}, SUPERSEDED)
    errors = repository_check(repo)[0].errors
    assert any("superseded_by ['docs/guide/other.md'] disagrees" in e for e in errors)
    assert any('missing the banner line' in e for e in errors)


# ------------------------------------------------------------------ generated README block

README = f'# Map\n\nIntro.\n\n{README_BEGIN}\n{README_END}\n\nTail.\n'


def test_readme_block_lists_every_family_and_store_and_escapes_cells():
    data = catalogue(entry('guide', ['docs/guide/**'], purpose='Pipes | and `ticks`'),
                     entry('old', ['docs/old/**'], lifecycle='superseded', superseded_by='docs/guide/a.md'),
                     store('main', ['data/main.db']))
    block = readme_block(data)
    assert '| `guide` | doc_family | current | `docs/guide/**` | Pipes \\| and `ticks` |' in block
    assert '| `old` | doc_family | superseded → `docs/guide/a.md` |' in block
    assert '| `main` | `data/main.db` | current | sqlite: read-only SQL |' in block
    rendered = render_readme(README, data)
    assert rendered.startswith('# Map\n\nIntro.\n\n') and rendered.endswith('\n\nTail.\n')
    assert render_readme(rendered, data) == rendered


@pytest.mark.parametrize('text', ['# no markers\n', f'{README_BEGIN}\n', f'{README_END}\n{README_BEGIN}\n',
                                  f'{README_BEGIN}\n{README_END}\n{README_BEGIN}\n{README_END}\n'])
def test_readme_markers_must_form_one_pair(text):
    with pytest.raises(ValueError):
        render_readme(text, catalogue(entry('guide', ['docs/guide/**'])))


def test_readme_command_and_drift_check(tmp_path, capsys):
    data = catalogue(entry('knowledge', ['docs/knowledge/**'], owner='docs-knowledge'),
                     entry('docs-map', ['docs/README.md']))
    repo = make_repo(tmp_path / 'r', data, {'docs/README.md': README})
    assert any('generated family table is stale' in e for e in repository_check(repo)[0].errors)
    assert main(['readme', '--repo', str(repo), '--check']) == 1
    assert main(['readme', '--repo', str(repo)]) == 0
    assert main(['readme', '--repo', str(repo), '--check']) == 0
    capsys.readouterr()
    assert any('stale' in e for e in repository_check(repo)[0].errors)  # the index still holds the old block
    git(repo, 'add', '.')
    assert repository_check(repo)[0].errors == []


# ------------------------------------------------------------------ escaped diagnostics

def test_shown_escapes_every_non_printable_but_not_ukrainian():
    assert shown('docs/ґанок.md') == 'docs/ґанок.md'
    assert shown(f'docs/a{BIDI}b.md') == repr(f'docs/a{BIDI}b.md')
    for char in ('\n', '\t', NEL, LS, PS, BOM):
        assert shown(f'x{char}y') == repr(f'x{char}y')


def test_messages_escape_ids_and_paths_even_when_validation_is_bypassed():
    tricky = f'docs/guide/a{BIDI}.md'
    data = catalogue(entry('one', [tricky]), entry('two', [tricky]))
    report = validate(data, {}, [tricky], {'infra-harness'}, ('docs',))
    [ambiguous] = [e for e in report.errors if 'ambiguous' in e]
    assert BIDI not in ambiguous and repr(tricky) in ambiguous
    data = catalogue(entry(f'bad{BIDI}id', ['docs/guide/**'], owner='nobody'))
    errors = validate(data, {}, ['docs/guide/a.md'], {'infra-harness'}, ('docs',)).errors
    assert errors and all(BIDI not in e for e in errors)


# ------------------------------------------------------------------ engine-independent schema patterns

def schema_patterns(node=SCHEMA, where='#'):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'pattern':
                yield where, value
            else:
                yield from schema_patterns(value, f'{where}/{key}')
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from schema_patterns(value, f'{where}/{index}')


def test_patterns_use_no_engine_dependent_constructs():
    found = list(schema_patterns())
    assert len(found) >= 10
    for where, pattern in found:
        # Remove escaped characters and bracket classes, then nothing engine-dependent may remain.
        bare = re.sub(r'\[(?:\\.|[^\]\\])*\]', '', re.sub(r'\\u[0-9a-f]{4}', '', pattern))
        assert not re.search(r'\\[sSwWdDbBAZz]', pattern), where
        assert '$' not in pattern, where
        assert '.' not in re.sub(r'\\.', '', bare), where  # an unescaped dot outside a class


def corpus():
    base = ['abc', 'docs/a.md', 'data/a.db', 'data/a/', 'id:ab', 'ab', 'docs/a/**', 'a b', 'Ґанок']
    odd = ['\n', '\r', NEL, LS, PS, BOM, chr(0xA0), chr(0x3000), chr(0x1F600), ' ', '\t', '.', '/', '..']
    out = list(base)
    for s in base:
        for c in odd:
            out += [s + c, c + s, s[:1] + c + s[1:]]
    out += [c * 3 for c in odd] + [BOM + BOM + BOM, LS + PS + ' ', NEL * 3, 'docs/../a.md', 'data/x/../y.db']
    return out


def test_whitespace_semantics_are_explicit():
    text = Draft202012Validator(SCHEMA['$defs']['text'])
    for value in (BOM * 3, LS + PS + ' ', chr(0x3000) * 3, chr(0xA0) * 3, '   '):
        assert not text.is_valid(value), repr(value)
    for value in ('abc', 'а б', BOM + 'ab', chr(0x1F600) * 3):
        assert text.is_valid(value), repr(value)


def test_python_and_ecma_engines_agree_on_every_schema_pattern():
    node = shutil.which('node')
    if node is None:
        if os.environ.get('CI'):
            pytest.fail('node is required in CI to compare the ECMA-262 engine')
        pytest.skip('node is not installed; CI runs this comparison')
    patterns = [p for _, p in schema_patterns()]
    strings = corpus()
    script = ('const d=JSON.parse(require("fs").readFileSync(0,"utf8"));'
              'console.log(JSON.stringify(d.p.map(p=>{const r=new RegExp(p,"u");return d.s.map(s=>r.test(s));})));')
    payload = json.dumps({'p': patterns, 's': strings})
    ecma = json.loads(subprocess.run([node, '-e', script], input=payload, capture_output=True, text=True,
                                     check=True, timeout=60).stdout)
    script_plain = script.replace('new RegExp(p,"u")', 'new RegExp(p)')
    ecma_plain = json.loads(subprocess.run([node, '-e', script_plain], input=payload, capture_output=True,
                                           text=True, check=True, timeout=60).stdout)
    for p, js, js_plain in zip(patterns, ecma, ecma_plain, strict=True):
        py = [re.search(p, s) is not None for s in strings]
        assert py == js, [(s, a, b) for s, a, b in zip(strings, py, js, strict=True) if a != b][:5]
        assert py == js_plain, [(s, a, b) for s, a, b in zip(strings, py, js_plain, strict=True) if a != b][:5]
