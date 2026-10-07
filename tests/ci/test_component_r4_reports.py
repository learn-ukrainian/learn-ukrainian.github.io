"""Held-out synthetic controls for hypothetical terminal test obligations (#9929)."""
from __future__ import annotations

import copy

import pytest

from scripts.ci import components as c


@pytest.fixture
def r4_case():
    manifest = copy.deepcopy(c.load_manifest())
    manifest['edges'] = []
    manifest['exact_paths'] = {}
    manifest['path_prefixes'] = [dict(path=f'src/{index}/', components=[component])
                                 for index, component in enumerate(c.NODE_IDS)]
    manifest['path_prefixes'] += [dict(path='tests/', components=['atlas-data'])]
    manifest['shared_integration_tests'] = []
    for component in c.NODE_IDS:
        manifest['components'][component]['test_files'] = []
        manifest['components'][component]['test_prefixes'] = []
    paths = ['src/0/changed.py', 'src/1/reader.py', 'src/7/shared.py',
             'tests/test_reader.py', 'tests/test_other.py', 'tests/test_free.py']
    graph = dict(file_edges=[('tests/test_reader.py', 'src/0/changed.py'),
                             ('src/1/reader.py', 'tests/test_reader.py'),
                             ('tests/test_other.py', 'src/1/reader.py')],
                 node_edges=[('open-model-data', 'shared-core')],
                 unresolved_edges=[], missing_mandatory_edges=[])
    return manifest, graph, paths, dict.fromkeys(paths, b'')


def run(case, changed=('src/0/changed.py',), unresolved=(), extra=(), durations=None):
    manifest, graph, paths, sources = case
    return c.report_r4(changed, manifest, paths, graph, unresolved,
                       durations if durations is not None else dict.fromkeys(paths, 2.0),
                       c.report_r4_context(manifest, paths, sources), extra)


@pytest.mark.parametrize('changed', [('src/0/changed.py',), ('tests/test_reader.py',)])
def test_terminal_tests_never_propagate_or_lift_component_imports(r4_case, changed):
    result = run(r4_case, changed)
    assert result['selected_test_files'] == ['tests/test_reader.py']
    assert result['would_skip_test_files'] == ['tests/test_free.py', 'tests/test_other.py']
    assert 'src/1/reader.py' not in result['affected_production_files']
    assert not result['full_selection']


def test_test_directory_helper_is_a_production_vertex(r4_case):
    _, graph, paths, sources = r4_case
    paths.append('tests/helpers/local.py')
    sources['tests/helpers/local.py'] = b''
    graph['file_edges'] = [('tests/helpers/local.py', 'src/0/changed.py'),
                           ('tests/test_other.py', 'tests/helpers/local.py')]
    result = run(r4_case)
    assert result['selected_test_files'] == ['tests/test_other.py']
    assert 'tests/helpers/local.py' in result['affected_production_files']
    assert not result['full_selection']


@pytest.mark.parametrize(('path', 'source', 'kind'), [
    ('src/0/conftest.py', b'', 'changed-conftest'),
    ('src/0/plugin.py', b'def pytest_sessionstart(session): pass', 'changed-pytest-plugin'),
    ('src/0/declaration.py', b'pytest_plugins = dynamic', 'changed-pytest-plugin'),
    ('src/0/plugin.py', b'', 'changed-pytest-plugin'),
    ('tests/helpers/local.py', b'', 'changed-shared-fixture-helper'),
    ('scripts/common/util.py', b'', 'changed-shared-source-helper'),
    ('scripts/storage/util.py', b'', 'changed-shared-source-helper'),
    ('scripts/config.py', b'', 'changed-shared-source-helper'),
    ('scripts/sources/util.py', b'', 'changed-shared-source-helper'),
    ('scripts/wiki/util.py', b'', 'changed-shared-source-helper'),
    ('src/0/pyproject.toml', b'', 'changed-dependency'),
    ('src/0/package-lock.json', b'', 'changed-dependency'),
    ('.github/workflows/check.yml', b'', 'changed-workflow'),
    ('scripts/ci/check.py', b'', 'changed-workflow'),
    ('src/0/path.py', b'import sys\nsys.path.insert(0, dynamic)', 'changed-sys-path'),
    ('src/7/shared.py', b'', 'changed-plan-shared-core'),
    ('unknown/new.py', b'', 'changed-unmapped'),
])
def test_each_changed_always_run_class_selects_everything(r4_case, path, source, kind):
    manifest, _, paths, sources = r4_case
    if path not in paths:
        paths.append(path)
    sources[path] = source
    if kind not in {'changed-unmapped', 'changed-plan-shared-core'}:
        manifest['exact_paths'][path] = ['open-model-data']
    if path == 'src/0/plugin.py' and not source:
        sources['tests/test_free.py'] = b'pytest_plugins = ["src.0.plugin"]'
    result = run(r4_case, [path])
    assert result['full_selection']
    assert result['components'] == sorted(c.NODE_IDS)
    assert result['would_skip_test_files'] == []
    assert kind in {entry['class'] for entry in result['always_run_causes']}


def test_unresolved_test_source_is_only_its_own_obligation(r4_case):
    result = run(r4_case, changed=[], unresolved=[dict(path='tests/test_reader.py', line=1, reason='unresolved-file-read')])
    assert result['selected_test_files'] == ['tests/test_reader.py']
    assert result['affected_production_files'] == []
    assert 'tests/test_other.py' in result['would_skip_test_files']
    assert not result['full_selection']


@pytest.mark.parametrize('path', ['src/1/reader.py', 'src/7/shared.py'])
def test_unresolved_production_source_is_always_affected_without_global_trigger(r4_case, path):
    _, graph, _, _ = r4_case
    graph['file_edges'] = [('tests/test_other.py', path), ('tests/test_reader.py', 'tests/test_other.py')]
    result = run(r4_case, changed=[], unresolved=[dict(path=path, line=1, reason='unresolved-file-read')])
    assert result['selected_test_files'] == ['tests/test_other.py']
    assert result['production_seed_files'] == [path]
    assert not result['full_selection']


@pytest.mark.parametrize(('path', 'source'), [
    ('tests/conftest.py', b''),
    ('src/0/plugin.py', b'def pytest_sessionstart(session): pass'),
    ('tests/helpers/local.py', b''),
])
def test_unresolved_global_fixture_or_plugin_forces_full_selection(r4_case, path, source):
    _, _, paths, sources = r4_case
    paths.append(path)
    sources[path] = source
    result = run(r4_case, unresolved=[dict(path=path, line=1, reason='sys-path')])
    assert result['full_selection']
    assert not result['skip_justifications']


def test_changed_or_unconditional_reader_reaching_global_fixture_is_full(r4_case):
    _, graph, paths, sources = r4_case
    paths.append('tests/conftest.py')
    sources['tests/conftest.py'] = b''
    graph['file_edges'].append(('tests/conftest.py', 'src/0/changed.py'))
    assert run(r4_case)['full_selection']
    assert run(r4_case, changed=[], unresolved=[dict(path='src/0/changed.py', line=1, reason='unresolved-file-read')])['full_selection']


@pytest.mark.parametrize('kind', ['runtime', 'artifact', 'schema'])
def test_explicit_contracts_propagate_to_production_then_terminal_tests(r4_case, kind):
    manifest, _, _, _ = r4_case
    manifest['edges'] = [dict(id='contract', kind=kind, producer='open-model-data', consumer='atlas-data', resolved=True)]
    result = run(r4_case)
    assert result['selected_test_files'] == ['tests/test_other.py', 'tests/test_reader.py']
    assert result['would_skip_test_files'] == ['tests/test_free.py']
    assert not result['full_selection']


def test_shared_manifest_obligations_always_run(r4_case):
    manifest, _, _, _ = r4_case
    manifest['shared_integration_tests'] = ['tests/test_free.py']
    manifest['components']['shared-core']['test_files'] = ['tests/test_other.py']
    manifest['components']['shared-core']['test_prefixes'] = ['tests/test_reader']
    result = run(r4_case, changed=[])
    assert result['selected_test_files'] == ['tests/test_free.py', 'tests/test_other.py', 'tests/test_reader.py']
    assert result['production_seed_files'] == []
    assert not result['full_selection']


def test_r2_folded_edges_pricing_and_absence_certificates(r4_case):
    # Give a tracked data file product ownership rather than an unmapped trigger.
    manifest, _, paths, _ = r4_case
    manifest['exact_paths']['input.json'] = ['open-model-data']
    paths.append('input.json')
    result = run(r4_case, changed=['input.json'], extra=[('src/1/reader.py', 'input.json')],
                 durations={'tests/test_other.py': 3.0, 'tests/test_free.py': 5.0})
    assert result['selected_test_files'] == ['tests/test_other.py']
    assert result['selected_seconds'] == 3.0
    assert result['would_skip_seconds'] == 5.0
    assert result['would_skip_unpriced_test_files'] == ['tests/test_reader.py']
    assert {row['test_file'] for row in result['skip_justifications']} == set(result['would_skip_test_files'])
    assert all(not row['reachable_from_production_seeds'] and not row['always_run_obligation']
               and 'No path from the changed set' in row['reason'] for row in result['skip_justifications'])


def test_missing_mandatory_or_unresolved_manifest_edges_stay_full(r4_case):
    manifest, graph, _, _ = r4_case
    graph['missing_mandatory_edges'] = ['missing']
    assert run(r4_case)['full_selection']
    graph['missing_mandatory_edges'] = []
    manifest['edges'] = [dict(id='unknown', kind='artifact', producer='open-model-data', consumer='atlas-data', resolved=False)]
    assert run(r4_case)['full_selection']


def test_r4_preserves_inputs_and_reports_no_production_effects(r4_case, monkeypatch):
    frozen = copy.deepcopy(r4_case)
    monkeypatch.setattr(c, 'affected', lambda *a, **k: pytest.fail('R4 called production affected'))
    run(r4_case)
    assert r4_case == frozen


def test_context_handles_literal_recursive_plugin_targets_and_parse_errors(r4_case):
    manifest, _, paths, sources = r4_case
    sources.update({'src/0/decl.py': b'pytest_plugins: tuple = ("src.1.reader",)\n',
                    'src/1/reader.py': b'pytest_plugins = "src.0.changed"\n',
                    'src/0/broken.py': b'('})
    paths.extend(['src/0/decl.py', 'src/0/broken.py'])
    context = c.report_r4_context(manifest, paths, sources)
    assert context['global_files']['src/0/decl.py'] == 'pytest-plugin'
    assert context['global_files']['src/1/reader.py'] == 'pytest-plugin'
    assert context['global_files']['src/0/changed.py'] == 'pytest-plugin'
    assert 'src/0/broken.py' not in context['global_files']
