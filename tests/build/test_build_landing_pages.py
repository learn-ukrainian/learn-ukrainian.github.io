"""Producer-derived non-arc freshness and default-byte compatibility (#9721)."""

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.build import build_landing_pages as gen

REPO = Path(__file__).resolve().parents[2]
NON_ARC = ('a2', 'b1', 'b2', 'c1', 'c2', 'hist', 'bio', 'istorio', 'lit', 'oes', 'ruth')
OUTPUTS = {f'{level}/index.mdx' for level in NON_ARC} | {'index.mdx'}


def snapshot(root):
    """Include directory membership, bytes and mtimes to detect even same-byte writes."""
    return {
        str(path.relative_to(root)): (path.is_dir(), path.stat().st_mtime_ns,
                                     None if path.is_dir() else path.read_bytes())
        for path in root.rglob('*')
    }


@pytest.fixture
def producer(tmp_path, monkeypatch):
    docs = tmp_path / 'site/src/content/docs'
    curriculum = tmp_path / 'curriculum/l2-uk-en'
    status = tmp_path / 'docs/l2-uk-en/level-status.yaml'
    status.parent.mkdir(parents=True)
    curriculum.mkdir(parents=True)
    configs = {level: {'planned': 4, 'description': 'Fixture description'} for level in (*NON_ARC, 'a1')}
    status.write_text(yaml.safe_dump(configs), encoding='utf-8')
    manifest = {'version': '1.0', 'levels': {}}
    for level in (*NON_ARC, 'a1'):
        manifest['levels'][level] = {
            'type': 'core' if level in gen.CORE_LEVELS else 'track',
            'modules': ['first', 'checkpoint-second', 'third', 'fourth'],
        }
        meta = curriculum / level / 'meta'
        meta.mkdir(parents=True)
        for slug in ('first', 'checkpoint-second', 'third'):
            (meta / f'{slug}.yaml').write_text(
                yaml.safe_dump({'title': f'Fixture "{slug}"'}), encoding='utf-8'
            )
        plans = curriculum / 'plans' / level
        plans.mkdir(parents=True)
        (plans / 'fourth.yaml').write_text('title: Plan fallback title\n', encoding='utf-8')
        out = docs / level
        out.mkdir(parents=True)
        for slug in ('first', 'checkpoint-second'):
            (out / f'{slug}.mdx').write_text('fixture module\n', encoding='utf-8')
        review = curriculum / level / 'review'
        review.mkdir()
        (review / 'first-review.md').write_text('fixture review\n', encoding='utf-8')
        audit = curriculum / level / 'audit'
        audit.mkdir()
        (audit / 'checkpoint-second-audit.md').write_text('fixture audit\n', encoding='utf-8')
    (curriculum / 'curriculum.yaml').write_text(yaml.safe_dump(manifest, sort_keys=False), encoding='utf-8')
    (docs / 'a1/index.mdx').write_text('arc-owned fixture\n', encoding='utf-8')
    (docs / 'unrelated.mdx').write_text('unrelated fixture\n', encoding='utf-8')
    monkeypatch.setattr(gen, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(gen, 'CURRICULUM_DIR', curriculum)
    monkeypatch.setattr(gen, 'DOCS_DIR', docs)
    monkeypatch.setattr(gen, 'LEVEL_STATUS_FILE', status)
    monkeypatch.setattr(gen.manifest_utils, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(gen.manifest_utils, 'CURRICULUM_PATH', curriculum)
    monkeypatch.setattr(gen.manifest_utils, 'MANIFEST_PATH', curriculum / 'curriculum.yaml')
    gen.manifest_utils.clear_manifest_cache()
    yield tmp_path
    gen.manifest_utils.clear_manifest_cache()


def test_default_derivation_and_fresh_check(producer, capsys):
    pages = gen.generated_pages(gen.load_level_status())
    assert {str(path.relative_to(gen.DOCS_DIR)) for path in pages} == OUTPUTS
    before = snapshot(producer)
    assert gen.main() == 0
    for path, (content, _, _) in pages.items():
        assert path.read_bytes() == content.encode('utf-8')
    for name in ('a1/index.mdx', 'unrelated.mdx'):
        path = 'site/src/content/docs/' + name
        assert snapshot(producer)[path] == before[path]
    # Captured from the original producer at ad17bcc2bf201a4ea019831ec855611814a4e4c1,
    # using this same synthetic input fixture; these freeze default bytes independently.
    original_hashes = {
        'a2/index.mdx': 'd6bfcee40f2a39eaccf7feed1e746a562ea2f59c60643acee22a1d28c23dc81a',
        'hist/index.mdx': 'a777ba466a739eb8227714a12e7385c7a2ba81f4fb2a0e8ebed90269d4402bea',
        'index.mdx': 'f66f03619fc5ccb521c7aa6f7b198219ed7defed5d19658939e1473aad20cf0c',
    }
    for name, digest in original_hashes.items():
        assert hashlib.sha256((gen.DOCS_DIR / name).read_bytes()).hexdigest() == digest
    core = (gen.DOCS_DIR / 'a2/index.mdx').read_text('utf-8')
    track = (gen.DOCS_DIR / 'hist/index.mdx').read_text('utf-8')
    assert 'status: "qa", isCheckpoint: true' in core
    assert 'status: "wip"' in core and 'status: "planned"' in core
    assert 'Plan fallback title' in core and r'Fixture \"first\"' in core
    assert 'status: "wip"' in track and 'status: "planned"' not in track
    before = snapshot(producer)
    assert gen.main(['--check']) == 0
    assert snapshot(producer) == before
    assert '12 non-arc landing/intro pages are current' in capsys.readouterr().out


@pytest.mark.parametrize('target', ['a2/index.mdx', 'hist/index.mdx', 'index.mdx'])
def test_stale_digest_valid_and_missing_output(producer, target, capsys):
    assert gen.main() == 0
    path = gen.DOCS_DIR / target
    path.write_bytes(path.read_bytes() + b'\n')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (producer / 'valid-digest.json').write_text(json.dumps({target: digest}))
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    assert snapshot(producer) == before
    err = capsys.readouterr().err
    assert f'stale: site/src/content/docs/{target}' in err
    assert 'regenerate' in err and str(producer) not in err
    path.unlink()
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert snapshot(producer) == before
    assert f'missing: site/src/content/docs/{target}' in capsys.readouterr().err


@pytest.mark.parametrize('change', ['planned', 'description', 'meta-title', 'plan-title',
                                    'mdx-added', 'mdx-removed', 'meta-removed',
                                    'audit-removed', 'member-added', 'member-removed'])
def test_changed_producer_input_refuses_retained_bytes(producer, change, capsys):
    assert gen.main() == 0
    if change in ('planned', 'description'):
        status = gen.load_level_status()
        status['a2'][change] = 9 if change == 'planned' else 'Changed description'
        gen.LEVEL_STATUS_FILE.write_text(yaml.safe_dump(status), encoding='utf-8')
    elif change == 'meta-title':
        (gen.CURRICULUM_DIR / 'a2/meta/first.yaml').write_text('title: Changed title\n')
    elif change == 'plan-title':
        (gen.CURRICULUM_DIR / 'plans/a2/fourth.yaml').write_text('title: Changed fallback\n')
    elif change == 'mdx-added':
        (gen.DOCS_DIR / 'a2/third.mdx').write_text('fixture module\n')
    elif change == 'mdx-removed':
        (gen.DOCS_DIR / 'a2/first.mdx').unlink()
    elif change == 'meta-removed':
        (gen.CURRICULUM_DIR / 'a2/meta/third.yaml').unlink()
    elif change == 'audit-removed':
        (gen.CURRICULUM_DIR / 'a2/audit/checkpoint-second-audit.md').unlink()
    else:
        path = gen.CURRICULUM_DIR / 'curriculum.yaml'
        manifest = yaml.safe_load(path.read_text())
        modules = manifest['levels']['a2']['modules']
        if change == 'member-added':
            modules.append('fifth')
        else:
            modules.pop()
        path.write_text(yaml.safe_dump(manifest))
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert snapshot(producer) == before
    assert 'stale: site/src/content/docs/a2/index.mdx' in capsys.readouterr().err


@pytest.mark.parametrize('removal', ['config', 'empty-config', 'core-list', 'track-list', 'manifest-level'])
def test_removed_source_detects_retained_managed_page(producer, removal, monkeypatch, capsys):
    assert gen.main() == 0
    level = 'hist' if removal == 'track-list' else 'a2'
    if removal in ('config', 'empty-config'):
        status = gen.load_level_status()
        if removal == 'config':
            del status[level]
        else:
            status[level] = {}
        gen.LEVEL_STATUS_FILE.write_text(yaml.safe_dump(status))
    elif removal.endswith('list'):
        attr = 'SPECIALIZED_TRACKS' if removal == 'track-list' else 'CORE_LEVELS'
        monkeypatch.setattr(gen, attr, [item for item in getattr(gen, attr) if item != level])
    else:
        path = gen.CURRICULUM_DIR / 'curriculum.yaml'
        manifest = yaml.safe_load(path.read_text())
        del manifest['levels'][level]
        path.write_text(yaml.safe_dump(manifest))
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert snapshot(producer) == before
    err = capsys.readouterr().err
    assert ('Cannot derive' if removal == 'manifest-level' else f'obsolete: site/src/content/docs/{level}/index.mdx') in err


@pytest.mark.parametrize('bad', ['', '[]', 'broken: [', '{}', 'a2: 42',
                               'a2: {planned: wrong}', 'a2: {planned: true}',
                               'a2: {planned: -1}', 'a2: {description: []}', None])
def test_bad_status_refuses_without_creating_output(producer, bad, capsys):
    shutil.rmtree(gen.DOCS_DIR)
    if bad is None:
        gen.LEVEL_STATUS_FILE.unlink()
    else:
        gen.LEVEL_STATUS_FILE.write_text(bad)
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert snapshot(producer) == before
    assert not gen.DOCS_DIR.exists()
    err = capsys.readouterr().err
    assert 'Cannot derive site/src/content/docs' in err
    assert 'level-status.yaml' in err and 'before regenerating' in err
    assert str(producer) not in err


@pytest.mark.parametrize('bad', [None, 'bad: [', '[]', 'levels: []',
                               'levels: {a2: {}}', 'levels: {a2: {modules: [null]}}'])
def test_bad_manifest_refuses_without_writes(producer, bad):
    path = gen.CURRICULUM_DIR / 'curriculum.yaml'
    if bad is None:
        path.unlink()
    else:
        path.write_text(bad)
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert snapshot(producer) == before


def test_missing_output_directory_and_unreadable_output(producer, capsys):
    shutil.rmtree(gen.DOCS_DIR)
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert snapshot(producer) == before
    assert not gen.DOCS_DIR.exists()
    assert 'missing: site/src/content/docs/index.mdx' in capsys.readouterr().err
    assert gen.main() == 0
    path = gen.DOCS_DIR / 'a2/index.mdx'
    path.unlink()
    path.mkdir()
    before = snapshot(producer)
    assert gen.main(['--check']) == 1
    assert snapshot(producer) == before
    assert 'unreadable: site/src/content/docs/a2/index.mdx' in capsys.readouterr().err


def test_arc_and_unrelated_changes_not_owned(producer):
    assert gen.main() == 0
    (gen.DOCS_DIR / 'a1/index.mdx').write_text('changed arc\n')
    (gen.DOCS_DIR / 'unrelated.mdx').write_text('changed unrelated\n')
    status = gen.load_level_status()
    status['a1'] = 'arc configuration is outside this check'
    status['unrelated'] = {'planned': 2}
    gen.LEVEL_STATUS_FILE.write_text(yaml.safe_dump(status))
    before = snapshot(producer)
    assert gen.main(['--check']) == 0
    assert snapshot(producer) == before


def test_default_skip_policy(producer, capsys):
    status = gen.load_level_status()
    del status['a2']
    status['hist'] = {}
    gen.LEVEL_STATUS_FILE.write_text(yaml.safe_dump(status))
    assert gen.main() == 0
    assert not (gen.DOCS_DIR / 'a2/index.mdx').exists()
    assert not (gen.DOCS_DIR / 'hist/index.mdx').exists()
    out = capsys.readouterr().out
    assert 'Skipping a1' in out and 'Skipping a2 - no config' in out and 'Skipping hist - no config' in out
    assert gen.main(['--check']) == 0


def test_compatibility_import_exposes_producer(producer):
    wrapper = importlib.import_module('scripts.build_landing_pages')
    assert Path(wrapper.__file__).resolve() == REPO / 'scripts/build/build_landing_pages.py'
    assert callable(wrapper.main) and callable(wrapper.generated_pages)


@pytest.mark.parametrize('entry', [['-m', 'scripts.build.build_landing_pages'],
                                 ['scripts/build/build_landing_pages.py'], ['scripts/build_landing_pages.py']])
def test_cli_help_misuse_fresh_stale_and_default(producer, entry):
    # Execute unchanged real source in a synthetic repository, never against live outputs.
    for relative in ('scripts/build/build_landing_pages.py', 'scripts/build_landing_pages.py',
                     'scripts/manifest_utils.py'):
        target = producer / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    before = snapshot(producer)
    help_result = subprocess.run([sys.executable, '-B', *entry, '--help'], cwd=producer,
                                 capture_output=True, text=True, check=False, timeout=60)
    assert help_result.returncode == 0
    for term in ('--check', 'Usage examples:', 'Outputs:', 'Exit codes:', 'Related:', 'write nothing'):
        assert term in help_result.stdout
    misuse = subprocess.run([sys.executable, '-B', *entry, '--unknown'], cwd=producer,
                            capture_output=True, text=True, check=False, timeout=60)
    assert misuse.returncode == 2 and 'unrecognized arguments' in misuse.stderr
    assert snapshot(producer) == before
    command = [sys.executable, '-B', *entry]
    generated = subprocess.run(command, cwd=producer, capture_output=True, text=True, check=False, timeout=60)
    assert generated.returncode == 0, generated.stderr
    before = snapshot(producer)
    fresh = subprocess.run([*command, '--check'], cwd=producer, capture_output=True, text=True, check=False, timeout=60)
    assert fresh.returncode == 0 and '12 non-arc' in fresh.stdout
    assert snapshot(producer) == before
    path = gen.DOCS_DIR / 'hist/index.mdx'
    path.write_bytes(b'stale fixture\n')
    before = snapshot(producer)
    stale = subprocess.run([*command, '--check'], cwd=producer, capture_output=True, text=True, check=False, timeout=60)
    assert stale.returncode == 1 and 'stale: site/src/content/docs/hist/index.mdx' in stale.stderr
    assert snapshot(producer) == before


@pytest.mark.parametrize('entry', [['-m', 'scripts.build.build_landing_pages'],
                                 ['scripts/build_landing_pages.py']])
def test_cli_refusal_missing_inputs_and_directories(producer, entry):
    for relative in ('scripts/build/build_landing_pages.py', 'scripts/build_landing_pages.py',
                     'scripts/manifest_utils.py'):
        target = producer / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    shutil.rmtree(gen.DOCS_DIR)
    gen.LEVEL_STATUS_FILE.unlink()
    before = snapshot(producer)
    result = subprocess.run([sys.executable, '-B', *entry, '--check'], cwd=producer,
                            capture_output=True, text=True, check=False, timeout=60)
    assert result.returncode == 1 and 'level-status.yaml' in result.stderr
    assert snapshot(producer) == before


def test_non_consumed_status_and_review_changes_are_equivalent(producer):
    assert gen.main() == 0
    status = gen.load_level_status()
    status['a2']['status'] = 'complete'
    status['a2']['introduction'] = 'Unused fixture field'
    gen.LEVEL_STATUS_FILE.write_text(yaml.safe_dump(status))
    (gen.CURRICULUM_DIR / 'a2/review/first-review.md').unlink()
    before = snapshot(producer)
    assert gen.main(['--check']) == 0
    assert snapshot(producer) == before
