"""Report-only measurements, strict folding and rule-specific pricing (#9929)."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess

import pytest

from scripts.ci import components as c
from scripts.ci.dependency_change_scope import _parse_name_status_z


@pytest.mark.parametrize(('expression', 'target'), [
    ('"tracked.json"', 'tracked.json'),
    ('Path("tracked.json")', 'tracked.json'),
    ('PurePosixPath("tracked.json")', 'tracked.json'),
    ('Path(__file__)', 'scripts/demo/reader.py'),
    ('Path(__file__).parent / "tracked.json"', 'scripts/demo/tracked.json'),
    ('Path(__file__).parents[1] / "tracked.json"', 'scripts/tracked.json'),
    ('Path(__file__).parents[2] / "tracked.json"', 'tracked.json'),
    ('Path(__file__).parents[INDEX] / "tracked.json"', 'scripts/tracked.json'),
    ('os.path.join(Path(__file__).parent, "assets", "tracked.json")', 'scripts/demo/assets/tracked.json'),
    ('DATA', 'scripts/demo/assets/tracked.json'),
])
def test_sound_path_forms(expression, target):
    source = ('from pathlib import Path, PurePosixPath\nimport os\n'
              'INDEX = 1\nROOT = Path(__file__).parent\nDATA = ROOT / "assets" / "tracked.json"\n'
              f'open({expression})\n')
    tree = ast.parse(source)
    folder = c.ReportFolder(tree, 'scripts/demo/reader.py')
    assert folder.target(tree.body[-1].value.args[0]) == target


@pytest.mark.parametrize('expression', [
    '"tracked" + ".json"', 'f"{ROOT}/tracked.json"', 'os.environ["DATA"]',
    'sys.argv[1]', 'get_path()', 'Path("a/../b")', 'Path("..") / "b"',
    'Path(__file__).resolve().parent', 'Path(__file__).absolute().parent',
    'Path("/absolute")', 'Path(__file__).parents[-1]', 'Path(__file__).parents[99]',
    'Path(__file__).parents[UNKNOWN]', 'str(Path(__file__))', 'Path("x", "y")',
    'Path(__file__).parents[2].parent', 'False',
])
def test_unproven_forms_are_rejected(expression):
    tree = ast.parse('from pathlib import Path\nimport os\nimport sys\nINDEX = 1\n' + f'open({expression})')
    assert c.ReportFolder(tree, 'scripts/demo/reader.py').target(tree.body[-1].value.args[0]) is None


@pytest.mark.parametrize('body', [
    'DATA = "fixed.json"\ndef read(DATA):\n    open(DATA)',
    'if enabled:\n    DATA = "fixed.json"\nopen(DATA)',
    'def read():\n    DATA = "fixed.json"\n    open(DATA)',
    'DATA = "fixed.json"\nDATA = "another.json"\nopen(DATA)',
    'DATA = "fixed.json"\ndef DATA(): pass\nopen(DATA)',
    'DATA = "fixed.json"\nfor DATA in paths: pass\nopen(DATA)',
    'DATA = "fixed.json"\n[DATA for DATA in paths]\nopen(DATA)',
    'DATA = "fixed.json"\ntry: pass\nexcept Exception as DATA: pass\nopen(DATA)',
    'DATA = "fixed.json"\nmatch arg:\n    case {"key": DATA}: pass\nopen(DATA)',
    'DATA = "fixed.json"\nmatch arg:\n    case {**DATA}: pass\nopen(DATA)',
    'from pathlib import Path\nfrom external import *\nopen(Path(__file__))',
    'DATA = "fixed.json"\nfrom external import *\nopen(DATA)',
    'from pathlib import Path\ndef read[Path]():\n    open(Path("fixed.json"))',
    'open(DATA)\nDATA = "fixed.json"',
    'from pathlib import Path\ndef read(Path):\n    open(Path("fixed.json"))',
    'from pathlib import Path\nPath.open = alternate\nopen(Path("fixed.json"))',
    '__file__ = "other.py"\nfrom pathlib import Path\nopen(Path(__file__))',
])
def test_shadowed_conditional_local_and_late_bindings_are_rejected(body):
    tree = ast.parse(body)
    expression = next(node for node in ast.walk(tree) if isinstance(node, ast.Call) and c.call_name(node.func) == 'open').args[0]
    assert c.ReportFolder(tree, 'scripts/demo/reader.py').target(expression) is None


def test_aliases_keywords_and_multiple_sites():
    sources = {'reader.py': b'from pathlib import Path as P\nfrom os.path import join as j\n'
               b'open(file=j(P("assets"), "x"))\nopen("x"); open("y")\n'}
    unresolved = [dict(path='reader.py', line=3, reason='unresolved-file-read'),
                  dict(path='reader.py', line=4, reason='unresolved-file-read')]
    result = c.report_edge_folds(sources, unresolved)
    assert result[0]['folded_target'] == 'assets/x'
    assert result[1]['classification'] == 'not-foldable'
    assert c.report_edge_folds({'broken.py': b'('}, [dict(path='broken.py', line=0, reason='parse-error')])[0]['folded_target'] is None


def test_read_load_sys_path_and_subprocess_sites():
    source = b'''from pathlib import Path
import sys
import subprocess
from importlib.util import spec_from_file_location
(Path(__file__).parent / "x").read_bytes()
spec_from_file_location("module", "tracked.py")
sys.path.insert(0, Path(__file__).parent)
subprocess.run([sys.executable, "tracked.py"])
subprocess.run(["python", "-m", "scripts.mod"])
subprocess.run(["python", "tracked.py"], shell=True)
subprocess.run(["python", "tracked.py"], cwd="elsewhere")
'''
    scan = c.scan_imports({'scripts/demo/reader.py': source}, set())
    result = c.report_edge_folds({'scripts/demo/reader.py': source}, scan['unresolved_edges'])
    by_line = {row['line']: row for row in result}
    assert by_line[5]['folded_target'] == 'scripts/demo/x'
    assert by_line[6]['folded_target'] == 'tracked.py'
    assert by_line[7]['folded_target'] == 'scripts/demo'
    assert by_line[8]['folded_target'] == 'tracked.py'
    assert all(by_line[line]['folded_target'] is None for line in (9, 10, 11))


def test_known_unsound_census_one_of_every_form():
    source = b'''from pathlib import Path
import subprocess
import sqlite3
import os
import shutil
import importlib
open(Path("x").resolve())
open(Path("x").absolute())
PARAM = "x"
def read(PARAM):
    open(PARAM)
if enabled:
    CONDITIONAL = "x"
open(CONDITIONAL)
SHADOW = "x"
def SHADOW(): pass
open(SHADOW)
importlib.import_module(".helper", "scripts.ci")
subprocess.run(["python", "-m", "scripts.mod"])
pytest_plugins = ("plugin",)
Path("x").rglob("*")
Path("x").glob("*")
Path("x").iterdir()
sqlite3.connect("x")
os.walk("x")
shutil.copy("x", "y")
'''
    result = c.report_unsound_census({'reader.py': source, 'scripts/mod.py': b'', 'scripts/__init__.py': b''})
    assert result['by_class'] == dict.fromkeys(c.REPORT_UNSOUND_CLASSES, 1)
    assert result['count'] == len(c.REPORT_UNSOUND_CLASSES)
    assert all(row['location'] == f"{row['path']}:{row['line']}" for row in result['occurrences'])
    assert c.report_unsound_census({'broken.py': b'('})['count'] == 0


@pytest.fixture
def measurement():
    manifest = copy.deepcopy(c.load_manifest())
    manifest['edges'] = []
    manifest['exact_paths'] = {}
    manifest['path_prefixes'] = [dict(path=f'src/{index}/', components=[component]) for index, component in enumerate(c.NODE_IDS)]
    manifest['path_prefixes'] += [dict(path=f'tests/{index}/', components=[component]) for index, component in enumerate(c.NODE_IDS)]
    manifest['shared_integration_tests'] = []
    for index, component in enumerate(c.NODE_IDS):
        manifest['components'][component]['test_files'] = [f'tests/{index}/test_contract.py']
        manifest['components'][component]['test_prefixes'] = []
    unresolved = [dict(path='src/1/reader.py', line=1, reason='unresolved-file-read'),
                  dict(path='src/7/shared.py', line=1, reason='sys-path')]
    graph = dict(file_edges=[('tests/1/test_reader.py', 'src/1/reader.py')], node_edges=[],
                 unresolved_edges=unresolved, missing_mandatory_edges=[])
    paths = [f'tests/{index}/test_contract.py' for index in range(8)] + ['tests/1/test_reader.py', 'src/0/data.json', 'src/1/reader.py', 'src/7/shared.py']
    return manifest, graph, paths


def test_rule_closure_r0_mandatory_shared_and_reverse_edges(measurement):
    manifest, graph, _ = measurement
    changed = ['src/0/data.json']
    assert c.report_closure(changed, manifest, graph, force=True) == c.affected(changed, manifest, graph)['components']
    assert c.report_closure(changed + [edge['path'] for edge in graph['unresolved_edges']], manifest, graph) == sorted(c.NODE_IDS)
    assert c.report_closure(changed, manifest, graph) == ['open-model-data']
    extra = [('src/1/reader.py', 'src/0/data.json')]
    assert c.report_closure(changed, manifest, graph, extra) == ['atlas-data', 'open-model-data']
    graph['node_edges'] = [('atlas-data', 'shared-core')]
    assert c.report_closure(changed, manifest, graph, extra) == sorted(c.NODE_IDS)
    graph['missing_mandatory_edges'] = ['mandatory']
    assert c.report_closure(changed, manifest, graph) == sorted(c.NODE_IDS)
    graph['missing_mandatory_edges'] = []
    manifest['edges'] = [dict(resolved=False)]
    assert c.report_closure(changed, manifest, graph) == sorted(c.NODE_IDS)
    assert c.report_closure([], manifest, graph) == []


def test_pricing_uses_own_unresolved_and_no_affected(measurement, monkeypatch):
    manifest, graph, paths = measurement
    monkeypatch.setattr(c, 'affected', lambda *a, **k: pytest.fail('pricer called affected'))
    durations = dict.fromkeys(paths, 1.0)
    durations.pop('tests/2/test_contract.py')
    r1 = c.report_price(['open-model-data'], manifest, paths, graph, graph['unresolved_edges'], durations)
    r2 = c.report_price(['open-model-data'], manifest, paths, graph, [], durations)
    assert 'tests/1/test_reader.py' not in r1['would_skip_test_files']
    assert 'tests/1/test_reader.py' in r2['would_skip_test_files']
    assert r2['would_skip_seconds'] == r1['would_skip_seconds'] + 1
    assert r2['unpriced_test_files'] == ['tests/2/test_contract.py']
    assert r2['would_skip_unpriced_test_files'] == ['tests/2/test_contract.py']


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, timeout=30).stdout


@pytest.fixture
def commits(tmp_path):
    git(tmp_path, 'init')
    git(tmp_path, 'config', 'user.name', 'Test')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    (tmp_path / '.gitignore').write_text('ignored.json\n')
    (tmp_path / 'ignored.json').write_text('tracked even though ignored\n')
    (tmp_path / 'old.txt').write_text('rename me\n' * 10)
    (tmp_path / 'deleted.txt').write_text('delete me\n')
    git(tmp_path, 'add', '-f', '.')
    git(tmp_path, 'commit', '-m', 'base')
    base = git(tmp_path, 'rev-parse', 'HEAD').decode().strip()
    (tmp_path / 'old.txt').rename(tmp_path / 'new.txt')
    (tmp_path / 'deleted.txt').unlink()
    (tmp_path / 'new-only.txt').write_text('new\n')
    git(tmp_path, 'add', '-A')
    git(tmp_path, 'commit', '-m', 'head')
    head = git(tmp_path, 'rev-parse', 'HEAD').decode().strip()
    (tmp_path / 'untracked.txt').write_text('disk is not the oracle\n')
    return tmp_path, base, head


def test_commit_tree_oracle_and_first_parent_rename_delete(commits):
    root, base, head = commits
    before, after = c.report_tracked_at(base, root), c.report_tracked_at(head, root)
    assert 'ignored.json' in before & after
    assert not {'new-only.txt', 'deleted.txt', 'untracked.txt'} & (before & after)
    parent, paths = c.report_merge_paths(head, root)
    assert parent == base
    assert paths == ['deleted.txt', 'new-only.txt', 'new.txt', 'old.txt']
    assert _parse_name_status_z(b'C100\0old\0new\0D\0gone\0R100\0before\0after\0') == ['after', 'before', 'gone', 'new', 'old']


def test_what_if_sound_both_tree_folds_and_ablation(commits, measurement, monkeypatch):
    root, _, head = commits
    manifest, graph, paths = measurement
    # Only ignored.json qualifies: new-only.txt exists at just one commit.
    sources = {'src/1/reader.py': b'open("ignored.json")\nopen("new-only.txt")\n', 'src/7/shared.py': b'import sys\nsys.path.insert(0, dynamic)\n'}
    graph['unresolved_edges'][1]['line'] = 2
    graph['unresolved_edges'].append(dict(path='src/1/reader.py', line=2, reason='unresolved-file-read'))
    manifest['exact_paths']['ignored.json'] = ['open-model-data']
    for changed in ('deleted.txt', 'new-only.txt', 'new.txt', 'old.txt'):
        manifest['exact_paths'][changed] = ['open-model-data']
    monkeypatch.setattr(c, 'import_graph', lambda *a: graph)
    monkeypatch.setattr(c, 'python_sources', lambda *a: sources)
    monkeypatch.setattr(c, 'tracked_paths', lambda *a: paths)
    report_dir = root / 'scripts/ci'
    report_dir.mkdir(parents=True)
    (report_dir / 'pytest-file-durations.json').write_text(json.dumps(dict.fromkeys(paths, 1)))
    prs = root / 'prs.txt'
    prs.write_text(f'123 {head} 2026-10-07T00:00:00Z\n')
    result = c.report_what_if(prs, manifest, root)
    assert result['prs_sha256'] == hashlib.sha256(prs.read_bytes()).hexdigest()
    assert result['prs'][0]['sound_fold_count'] == 1
    assert result['prs'][0]['R0_equals_affected']
    assert result['prs'][0]['rules']['R1']['unresolved_edge_count'] == 3
    assert result['prs'][0]['rules']['R2']['unresolved_edge_count'] == 2
    assert result['prs'][0]['rules']['R3']['unresolved_edge_count'] == 1
    assert result['blocking_set_counts'] == {'R1': 1, 'R2_union': 1}
    assert result['prs'][0]['rules']['R3']['components'] == ['atlas-data', 'open-model-data']
    assert result['aggregate']['R3'] == dict(narrowed_pr_count=1, pr_count=1, share_narrowed=1.0,
                                            total_would_skip_seconds=6.0, median_would_skip_seconds=6.0)
    assert 'UPPER BOUND, NOT ACHIEVABLE WITHOUT PROOF' in result['rule_labels']['R3']
    assert result == c.report_what_if(prs, manifest, root)
    prs.write_text('invalid\n')
    with pytest.raises(ValueError):
        c.report_what_if(prs, manifest, root)


def test_census_missing_mandatory_and_order(measurement, monkeypatch):
    manifest, graph, _ = measurement
    manifest['edges'] = [dict(id='missing', consumer='harness', producer='atlas-data', kind='import')]
    graph['missing_mandatory_edges'] = ['missing']
    monkeypatch.setattr(c, 'import_graph', lambda *a: graph)
    monkeypatch.setattr(c, 'python_sources', lambda *a: {'src/1/reader.py': b'open("x")', 'src/7/shared.py': b'import sys\nsys.path.insert(0, dynamic)'})
    result = c.report_census(manifest)
    assert result['by_class_component']['missing-mandatory-edge']['harness'] == 1
    assert result['by_class_component']['unresolved-file-read']['atlas-data'] == 1
    assert result['top_20_source_files']['sys-path'] == [dict(path='src/7/shared.py', count=1)]
    assert result == c.report_census(manifest)


def test_report_cli_routes_and_help(measurement, monkeypatch, capsys):
    manifest, _, _ = measurement
    monkeypatch.setattr(c, 'load_manifest', lambda: manifest)
    monkeypatch.setattr(c, 'report_census', lambda *a: {'census': True})
    monkeypatch.setattr(c, 'report_what_if', lambda *a: {'what-if': True})
    assert c.main(['census']) == 0
    assert json.loads(capsys.readouterr().out) == {'census': True}
    assert c.main(['what-if', '--prs', 'prs.txt']) == 0
    assert json.loads(capsys.readouterr().out) == {'what-if': True}
    for command in ('census', 'what-if'):
        with pytest.raises(SystemExit) as exc:
            c.parser().parse_args([command, '--help'])
        assert exc.value.code == 0
        help_text = capsys.readouterr().out
        assert all(word in help_text for word in ('Examples:', 'Outputs:', 'Exit codes:', 'Related:', 'hypothetical'))


def test_pricer_matches_existing_test_files_on_identical_inputs(measurement, monkeypatch):
    manifest, graph, paths = measurement
    monkeypatch.setattr(c, 'tracked_paths', lambda *a: paths)
    monkeypatch.setattr(c, 'import_graph', lambda *a: graph)
    for component in c.NODE_IDS:
        assert c.report_test_files(component, manifest, paths, graph, graph['unresolved_edges']) == c.test_files(component, manifest)


def test_legacy_wrapper_folds_counted_and_r2_rejects_identity_bindings():
    source = b'''from pathlib import Path
import importlib.util
ROOT = Path(__file__).resolve().parent
def load(name, target):
    return importlib.util.spec_from_file_location(name, target)
load("module", ROOT / "tracked.py")
'''
    result = c.report_unsound_census({'reader.py': source})
    assert result['by_class']['resolve-identity'] == 1
    edges = [dict(path='reader.py', line=6, reason='nonliteral-or-missing-load')]
    assert c.report_edge_folds({'reader.py': source}, edges)[0]['classification'] == 'not-foldable'
