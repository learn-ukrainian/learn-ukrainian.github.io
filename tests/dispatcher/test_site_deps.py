"""Dispatch worktrees share one content-addressed store of site dependencies and stay isolated."""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from scripts.dispatcher import site_deps


def npm(*args, cwd):
    return subprocess.run(["npm", *args, "--no-audit", "--no-fund", "--offline"], cwd=cwd, check=True,
                          capture_output=True, text=True, timeout=60)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A fake repository holding a site that installs one local tarball with a bin script."""
    if shutil.which("npm") is None or shutil.which("node") is None:
        pytest.skip("real node and npm are required")
    for name, value in {"HOME": tmp_path, "npm_config_cache": tmp_path / "npm-cache",
                        "npm_config_userconfig": tmp_path / "user.npmrc",
                        "npm_config_globalconfig": tmp_path / "global.npmrc",
                        site_deps.STORE_ENV: tmp_path / "store"}.items():
        monkeypatch.setenv(name, str(value))
    monkeypatch.delenv(site_deps.DISABLE_ENV, raising=False)
    root = tmp_path / "repo"
    package = tmp_path / "pkg"
    (package / "bin").mkdir(parents=True)
    # The install script records an ambient variable to show what the install could see.
    seen = "require('fs').writeFileSync('seen', process.env.AMBIENT_INSTALL_INPUT || 'none')"
    (package / "package.json").write_text(json.dumps({
        "name": "localdep", "version": "1.0.0", "bin": "bin/run.js", "scripts": {"postinstall": f'node -e "{seen}"'},
    }))
    (package / "bin/run.js").write_text("#!/usr/bin/env node\nconsole.log('one')\n")
    (package / "bin/run.js").chmod(0o755)
    (package / "index.js").write_text("module.exports = 'one'\n")
    site = root / "site"
    site.mkdir(parents=True)
    tarball = npm("pack", str(package), "--pack-destination", str(site), cwd=site).stdout.strip().splitlines()[-1]
    (site / "package.json").write_text(json.dumps(
        {"name": "fixture", "version": "1.0.0", "dependencies": {"localdep": f"file:./{tarball}"}}))
    npm("install", "--ignore-scripts", cwd=site)
    shutil.rmtree(site / "node_modules")
    return root


def worktree(tmp_path, repo, name):
    target = tmp_path / name
    shutil.copytree(repo / "site", target / "site")
    return target


def test_worktrees_share_files_but_keep_separate_real_installs(tmp_path, repo):
    first, second = worktree(tmp_path, repo, "a"), worktree(tmp_path, repo, "b")
    assert site_deps.ensure(repo, first)["state"] == "installed"
    assert site_deps.ensure(repo, second)["state"] == "installed"
    for tree in (first, second):
        modules = tree / "site/node_modules"
        assert modules.is_dir() and not modules.is_symlink()
        assert not any(p.is_symlink() and not p.resolve().is_relative_to(modules.resolve())
                       for p in modules.rglob("*"))
    shared = "node_modules/localdep/index.js"
    one, two = ((tree / "site" / shared).stat() for tree in (first, second))
    assert (one.st_ino, one.st_nlink) == (two.st_ino, 3)
    assert not one.st_mode & stat.S_IWUSR
    assert (first / "site/node_modules/localdep/bin/run.js").stat().st_mode & stat.S_IXUSR
    assert (first / "site/node_modules/.bin/localdep").readlink() == Path("../localdep/bin/run.js")
    assert site_deps.status(repo)["blobs"] >= 3


def test_replacing_a_worktree_install_leaves_store_and_other_worktrees_intact(tmp_path, repo):
    first, second = worktree(tmp_path, repo, "a"), worktree(tmp_path, repo, "b")
    site_deps.ensure(repo, first)
    site_deps.ensure(repo, second)
    blob = next((tmp_path / "store/blobs").glob("*/*"))
    before = blob.read_bytes(), blob.stat().st_ino
    with pytest.raises(PermissionError):
        (second / "site/node_modules/localdep/index.js").write_text("changed")
    npm("ci", "--ignore-scripts", cwd=first / "site")
    shutil.rmtree(second / "site/node_modules")
    assert (blob.read_bytes(), blob.stat().st_ino) == before
    assert blob.stat().st_nlink == 1
    assert (first / "site/node_modules/localdep/index.js").read_text() == "module.exports = 'one'\n"


def test_every_install_input_changes_the_key(tmp_path, repo, monkeypatch):
    site = repo / "site"
    base = site_deps.install_key(site)[0]
    assert site_deps.install_key(site)[0] == base
    runtime = site_deps._runtime(site)
    monkeypatch.setattr(site_deps, "_runtime", lambda _site: {**runtime, "abi": "0"})
    assert site_deps.install_key(site)[0] != base
    monkeypatch.undo()
    for change in ("npmrc", "package.json", "tarball", "patches"):
        key = base
        if change == "npmrc":
            (site / ".npmrc").write_text("ignore-scripts=true\n")
        elif change == "package.json":
            package = json.loads((site / "package.json").read_text())
            (site / "package.json").write_text(json.dumps({**package, "description": "changed"}))
        elif change == "tarball":
            tarball = next(site.glob("*.tgz"))
            tarball.write_bytes(tarball.read_bytes() + b"\0")
        else:
            (site / "patches").mkdir()
            (site / "patches/x.patch").write_text("patch")
        key = site_deps.install_key(site)[0]
        assert key != base, change
        base = key


@pytest.mark.parametrize("name,value", [
    ("npm_config_ignore_scripts", "true"), ("npm_config_script_shell", "/bin/false"), ("NODE_OPTIONS", "--no-warnings"),
])
def test_npm_settings_and_node_options_change_the_key(repo, monkeypatch, name, value):
    base = site_deps.install_key(repo / "site")[0]
    monkeypatch.setenv(name, value)
    assert site_deps.install_key(repo / "site")[0] != base


def test_ambient_variables_never_reach_the_install(tmp_path, repo, monkeypatch):
    """A variable an install script reads cannot change the stored bytes behind an unchanged key."""
    base = site_deps.install_key(repo / "site")[0]
    monkeypatch.setenv("AMBIENT_INSTALL_INPUT", "leaked")
    target = worktree(tmp_path, repo, "a")
    site_deps.ensure(repo, target)
    assert (target / "site/node_modules/localdep/seen").read_text() == "none"
    assert "AMBIENT_INSTALL_INPUT" not in site_deps._install_env()
    assert site_deps.install_key(repo / "site")[0] == base


def test_everything_the_install_sees_is_in_the_key(tmp_path, repo, monkeypatch):
    site = repo / "site"
    base = site_deps.install_key(site)[0]
    # Variables that would otherwise reach install scripts are replaced by fixed values.
    monkeypatch.setenv("LANG", "C")
    monkeypatch.setenv("LC_ALL", "C")
    monkeypatch.setenv("TMPDIR", str(tmp_path / "other-tmp"))
    monkeypatch.setenv("PATH", f"{tmp_path / 'unrelated'}{os.pathsep}{os.environ['PATH']}")
    env = site_deps._install_env()
    assert env["LANG"] == "C.UTF-8" and not {"LC_ALL", "TMPDIR"} & env.keys()
    assert str(tmp_path / "unrelated") not in env["PATH"]
    assert site_deps.install_key(site)[0] == base
    # What is passed on, and the build tools the install would use, change the key.
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:3128")
    assert site_deps.install_key(site)[0] != base
    monkeypatch.delenv("HTTPS_PROXY")
    monkeypatch.setenv("HOME", str(tmp_path / "other-home"))
    assert site_deps.install_key(site)[0] != base
    monkeypatch.undo()
    monkeypatch.setattr(site_deps, "_toolchain", lambda _env: {"cc": ["/usr/bin/cc", "another compiler"]})
    assert site_deps.install_key(site)[0] != base


def test_store_file_with_a_changed_mode_is_replaced(tmp_path, repo):
    first, second = worktree(tmp_path, repo, "a"), worktree(tmp_path, repo, "b")
    site_deps.ensure(repo, first)
    shared = first / "site/node_modules/localdep/index.js"
    shared.chmod(0o755)
    site_deps.ensure(repo, second)
    fresh = (second / "site/node_modules/localdep/index.js").stat()
    assert stat.S_IMODE(fresh.st_mode) == 0o444 and fresh.st_ino != shared.stat().st_ino


def test_altered_store_file_is_not_reused_by_a_new_key(tmp_path, repo):
    first, second = worktree(tmp_path, repo, "a"), worktree(tmp_path, repo, "b")
    site_deps.ensure(repo, first)
    shared = first / "site/node_modules/localdep/index.js"
    shared.chmod(0o644)
    shared.write_text("module.exports = 'two'\n")  # same size as the original
    package = json.loads((second / "site/package.json").read_text())
    (second / "site/package.json").write_text(json.dumps({**package, "description": "second key"}))
    assert site_deps.ensure(repo, second)["state"] == "installed"
    assert (second / "site/node_modules/localdep/index.js").read_text() == "module.exports = 'one'\n"


def test_detached_files_can_be_edited_without_touching_the_store_or_siblings(tmp_path, repo):
    first, second = worktree(tmp_path, repo, "a"), worktree(tmp_path, repo, "b")
    site_deps.ensure(repo, first)
    site_deps.ensure(repo, second)
    with pytest.raises(ValueError):
        site_deps.detach(first, ["../outside"])
    assert site_deps.detach(first, ["localdep"])["detached"] >= 2
    edited = first / "site/node_modules/localdep/index.js"
    assert edited.stat().st_nlink == 1 and edited.stat().st_mode & stat.S_IWUSR
    edited.write_text("module.exports = 'patched'\n")
    (first / "site/node_modules/localdep/bin/run.js").chmod(0o700)
    assert (second / "site/node_modules/localdep/index.js").read_text() == "module.exports = 'one'\n"
    assert (second / "site/node_modules/localdep/bin/run.js").stat().st_mode & 0o777 == 0o555
    assert site_deps.detach(first)["detached"] == 0  # nothing left to detach
    assert site_deps.detach(second)["detached"] > 0  # the whole install, no paths given
    assert (second / "site/node_modules/localdep/index.js").stat().st_nlink == 1
    assert site_deps._altered(site_deps.store_root(repo), next((tmp_path / "store/trees").glob("*.json"))) is None


def test_store_file_edited_in_place_never_reaches_a_new_worktree(tmp_path, repo):
    first, second = worktree(tmp_path, repo, "a"), worktree(tmp_path, repo, "b")
    site_deps.ensure(repo, first)
    edited = first / "site/node_modules/localdep/index.js"
    edited.chmod(0o644)
    edited.write_text("module.exports = 'tampered'\n")
    assert site_deps.ensure(repo, second)["state"] == "installed"
    assert (second / "site/node_modules/localdep/index.js").read_text() == "module.exports = 'one'\n"
    assert (second / "site/node_modules/localdep/index.js").stat().st_ino != edited.stat().st_ino


def test_tree_linking_outside_itself_is_not_shared(tmp_path):
    modules = tmp_path / "node_modules"
    modules.mkdir()
    (modules / "escape").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(site_deps.NotCacheable):
        site_deps._ingest(tmp_path / "store", modules)


def test_provision_never_fails_creation(tmp_path, repo, monkeypatch):
    target = worktree(tmp_path, repo, "a")
    monkeypatch.setattr(site_deps, "populate", lambda *args: (_ for _ in ()).throw(OSError("disk full")))
    site_deps.provision(repo, target)
    assert not (target / "site/node_modules").exists()
    assert not list((target / "site").glob("node_modules.tmp-*"))


def test_existing_install_and_disabled_hook_are_left_alone(tmp_path, repo, monkeypatch):
    target = worktree(tmp_path, repo, "a")
    (target / "site/node_modules").mkdir()
    (target / "site/node_modules/own").write_text("kept")
    assert site_deps.ensure(repo, target)["state"] == "present"
    assert (target / "site/node_modules/own").read_text() == "kept"
    shutil.rmtree(target / "site/node_modules")
    monkeypatch.setenv(site_deps.DISABLE_ENV, "off")
    assert site_deps.ensure(repo, target)["state"] == "skipped"
    assert not (target / "site/node_modules").exists()
    assert site_deps.ensure(repo, tmp_path / "no-site")["state"] == "skipped"


def test_prune_keeps_what_trees_and_worktrees_use(tmp_path, repo):
    target = worktree(tmp_path, repo, "a")
    site_deps.ensure(repo, target)
    store = site_deps.store_root(repo)
    stray = store / "blobs/zz/stray"
    stray.parent.mkdir(parents=True)
    stray.write_text("unused")
    used = next(path for path in (target / "site/node_modules").rglob("index.js"))
    assert site_deps.prune(repo)["blobs"] == 1
    assert not stray.exists() and used.read_text() == "module.exports = 'one'\n"
    tree = next((store / "trees").glob("*.json"))
    os.utime(tree, (1, 1))
    other = store / "trees" / "other.json"
    other.write_text(json.dumps({"entries": []}))
    assert site_deps.prune(repo, keep=1)["trees"] == 1
    assert not tree.exists() and used.read_text() == "module.exports = 'one'\n"
