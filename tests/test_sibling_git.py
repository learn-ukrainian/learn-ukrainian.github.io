"""Synthetic product and adversarial proof for the closed sibling verbs (#9309)."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import types
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from scripts.fleet import sibling_git as sg
from scripts.orchestration import worktree_claims as wc
from scripts.orchestration.fleet_repos import FleetRepo

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "agents_extensions/shared/hooks/guard-primary-checkout-write.py"


def git(path, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_OPTIONAL_LOCKS": "0"})
    return subprocess.run(
        ["/usr/bin/git", "-C", str(path), *args], env=env, text=True, capture_output=True, check=True, timeout=30
    ).stdout.strip()


def commit(path, filename="file.txt", text="base\n"):
    (path / filename).write_text(text)
    git(path, "add", "--", filename)
    git(path, "-c", "core.hooksPath=/dev/null", "commit", "-m", "fixture")
    return git(path, "rev-parse", "HEAD")


def init(path):
    path.mkdir(parents=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "Fixture")
    commit(path, ".gitignore", ".worktrees/\nbatch_state/\n.venv/\n")
    commit(path)


def snapshot(path):
    # Includes files/index/refs/reflogs/config/worktree metadata and lock files.
    return {
        str(p.relative_to(path)): ("link", os.readlink(p))
        if p.is_symlink()
        else ("directory", p.stat().st_mode)
        if p.is_dir()
        else ("file", p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode)
        for p in path.rglob("*")
    }


@pytest.fixture
def world(tmp_path, monkeypatch):
    primary = tmp_path / "public repo"
    sibling = tmp_path / "sibling"
    upstream = tmp_path / "upstream"
    init(primary)
    init(sibling)
    protected_tree = primary / ".worktrees/dispatch/codex/protected fixture"
    protected_tree.parent.mkdir(parents=True)
    git(primary, "worktree", "add", "--detach", str(protected_tree), "main")
    git(sibling, "clone", "--bare", "--no-hardlinks", str(sibling), str(upstream))
    git(sibling, "remote", "add", "origin", "git@github.com:fixture/sibling.git")
    (primary / ".venv/bin").mkdir(parents=True)
    (primary / ".venv/bin/python").symlink_to(sys.executable)
    (primary / "batch_state/tasks").mkdir(parents=True)
    (primary / ".git" / wc.LOCK_DIR_NAME).mkdir()
    # Fixture SSH runs Git's real upload-pack against an isolated local remote;
    # no production transport override or local-remote flag exists.
    ssh = tmp_path / "fixture ssh"
    ssh.write_text(f"#!/bin/sh\nexec /usr/bin/git-upload-pack {shlex.quote(str(upstream))}\n")
    ssh.chmod(0o700)
    monkeypatch.setenv("HOME", str(tmp_path / "isolated home"))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "PYTHONSTARTUP", "PYTHONINSPECT"):
        monkeypatch.delenv(key, raising=False)
    catalog = {
        "public": FleetRepo("public", "fixture/public", "public repo", "public", True),
        "test": FleetRepo("test", "fixture/sibling", "sibling", "private"),
    }
    monkeypatch.setattr(sg, "load_fleet_repos", lambda: catalog)
    monkeypatch.setattr(sg, "primary_root", lambda: primary)
    original = sg.Git.__init__

    def fixture_init(self, hooks):
        original(self, hooks)
        self.env["GIT_SSH_COMMAND"] = shlex.quote(str(ssh))

    monkeypatch.setattr(sg.Git, "__init__", fixture_init)
    before = snapshot(primary)
    yield primary, sibling, upstream
    assert snapshot(primary) == before, "protected primary changed"


def invoke(verb, path=None, repo="test"):
    out, err = io.StringIO(), io.StringIO()
    args = [verb, "--repo", repo] + ([] if path is None else [str(path)])
    with redirect_stdout(out), redirect_stderr(err):
        result = sg.main(args)
    return result, out.getvalue(), err.getvalue()


def advance(world, tmp_path, filename="file.txt", text="fetched\n"):
    writer = tmp_path / "writer"
    git(tmp_path, "clone", "--no-hardlinks", str(world[2]), str(writer))
    git(writer, "config", "user.name", "Fixture")
    git(writer, "config", "user.email", "fixture@example.invalid")
    sha = commit(writer, filename, text)
    git(writer, "push", "origin", "main")
    return sha


def signed_advance(world, tmp_path, kind):
    """Real commit object with a signature header to trigger Git verification."""
    sha = advance(world, tmp_path)
    writer = tmp_path / "writer"
    armor = "SSH SIGNATURE" if kind == "ssh" else "PGP SIGNATURE"
    signature = f"gpgsig -----BEGIN {armor}-----\n Zml4dHVyZQ==\n -----END {armor}-----"
    raw = git(writer, "cat-file", "commit", sha)
    # Add a signed child of the already-pushed tip; never rewrite the fixture remote.
    raw = "\n".join(f"parent {sha}" if line.startswith("parent ") else line for line in raw.split("\n"))
    payload = tmp_path / "signed-commit"
    payload.write_text(raw.replace("\n\n", f"\n{signature}\n\n", 1) + "\n")
    signed = git(writer, "hash-object", "-t", "commit", "-w", str(payload))
    git(writer, "update-ref", "refs/heads/main", signed)
    git(writer, "push", "origin", "main")
    return signed


def tree(world, task="finished task"):
    primary, sibling, _ = world
    path = sibling / ".worktrees/dispatch/codex" / task
    path.parent.mkdir(parents=True, exist_ok=True)
    git(sibling, "worktree", "add", "--detach", str(path), "main")
    with wc.worktree_lock(path, lock_dir=primary / ".git" / wc.LOCK_DIR_NAME):
        pass
    # The test fixture establishes the dispatch lock before the preservation
    # baseline; this is normally created when the dispatch attaches the tree.
    return path


@pytest.fixture
def managed(world):
    # The outer fixture's snapshot must include this already-owned lock.
    primary, _, _ = world
    saved = snapshot(primary)
    path = tree(world)
    yield path
    _, lock = wc.lock_path(path, lock_dir=primary / ".git" / wc.LOCK_DIR_NAME)
    # Fixture-only teardown restores the pre-fixture snapshot after checking
    # that the operation changed no public state except our fixture setup.
    current = snapshot(primary)
    assert {k: v for k, v in current.items() if k != str(lock.relative_to(primary))} == saved
    lock.unlink()


def test_sync_main_product(world, tmp_path):
    sha = advance(world, tmp_path)
    code, out, err = invoke("sync-main")
    assert code == 0, err
    assert json.loads(out) == {"repo": "test", "verb": "sync-main", "head": sha, "changed": True}
    assert git(world[1], "rev-parse", "HEAD") == sha
    assert (world[1] / "file.txt").read_text() == "fetched\n"
    assert invoke("sync-main")[0] == 0


def test_status_product(world):
    code, out, err = invoke("status")
    assert code == 0, err
    value = json.loads(out)
    assert value["branch"] == "main" and value["clean"] and value["worktree_count"] == 1
    assert value["worktrees"][0]["location"] == "."
    assert value["worktrees"][0]["branch"] == "refs/heads/main"


def test_remove_exactly_one_product(world, managed):
    other = world[1] / ".worktrees/dispatch/codex/other"
    git(world[1], "worktree", "add", "--detach", str(other), "main")
    before = snapshot(world[0])
    code, _, err = invoke("worktree-remove", managed)
    assert code == 0, err
    assert not managed.exists() and other.exists()
    assert str(managed) not in git(world[1], "worktree", "list", "--porcelain")
    assert snapshot(world[0]) == before


@pytest.mark.parametrize("repo", ["public", "unknown", "", "../sibling"])
def test_registry_refusals(world, repo):
    assert invoke("status", repo=repo)[0] == 2


@pytest.mark.parametrize("content", [b"invalid pointer", b"\xff\xfe"])
def test_malformed_pointer_refuses_without_traceback_or_paths(world, content):
    _, sibling, _ = world
    (sibling / ".git").rename(sibling / "saved-git")
    (sibling / ".git").write_bytes(content)
    code, out, err = invoke("status")
    assert code == 2 and not out
    assert "Traceback" not in err and str(sibling) not in err
    assert "scripts.fleet.sibling_git status" in err


@pytest.mark.parametrize(
    "kind",
    [
        "symlink-checkout",
        "git-pointer",
        "shared-common",
        "core-worktree",
        "index-link",
        "refs-link",
        "config-hardlink",
        "alternates",
    ],
)
def test_repository_redirection(world, tmp_path, kind):
    primary, sibling, _ = world
    if kind == "symlink-checkout":
        sibling.rename(tmp_path / "saved")
        sibling.symlink_to(primary, target_is_directory=True)
    elif kind == "git-pointer":
        (sibling / ".git").rename(sibling / "saved-git")
        (sibling / ".git").write_text(f"gitdir: {primary / '.git'}\n")
    elif kind == "shared-common":
        (sibling / ".git/commondir").write_text(str(primary / ".git"))
    elif kind == "core-worktree":
        git(sibling, "config", "core.worktree", str(primary))
    elif kind in {"index-link", "refs-link"}:
        name = "index" if kind == "index-link" else "refs/heads/main"
        (sibling / ".git" / name).unlink()
        (sibling / ".git" / name).symlink_to(primary / ".git" / name)
    elif kind == "config-hardlink":
        (sibling / ".git/config").unlink()
        os.link(primary / ".git/config", sibling / ".git/config")
    else:
        (sibling / ".git/objects/info/alternates").write_text(str(primary / ".git/objects"))
    assert invoke("sync-main")[0] == 2


@pytest.mark.parametrize(
    "key",
    [
        "GIT_DIR",
        "GIT_COMMON_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_EXEC_PATH",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_GLOBAL",
    ],
)
def test_inherited_git_injection_dropped(world, tmp_path, monkeypatch, key):
    sha = advance(world, tmp_path)
    monkeypatch.setenv(key, str(world[0] / ".git"))
    if key == "GIT_CONFIG_COUNT":
        monkeypatch.setenv(key, "1")
        monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.worktree")
        monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(world[0]))
    code, _, err = invoke("sync-main")
    assert code == 0, err
    # Probe without caller injections using the fixture's independent runner.
    assert git(world[1], "rev-parse", "HEAD") == sha


def tripwire(world, tmp_path):
    target = world[0] / "tripwire"
    script = tmp_path / "tripwire executable"
    script.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(target))}\nexit 1\n")
    script.chmod(0o700)
    return script


@pytest.mark.parametrize(
    "kind",
    [
        "hooks",
        "fsmonitor",
        "filter-clean",
        "filter-smudge",
        "filter-process",
        "upload-pack",
        "remote-helper",
        "url-rewrite",
        "ssh-command",
        "global-filter",
        "gpg",
        "ssh-signature",
    ],
)
def test_executable_configuration_never_runs(world, tmp_path, monkeypatch, kind):
    if kind in {"gpg", "ssh-signature"}:
        sha = signed_advance(world, tmp_path, "ssh" if kind == "ssh-signature" else "gpg")
    else:
        advance(world, tmp_path)
    _, sibling, _ = world
    script = tripwire(world, tmp_path)
    if kind == "hooks":
        hookdir = sibling / ".git/hooks"
        for name in ("post-merge", "post-checkout", "reference-transaction"):
            shutil.copy(script, hookdir / name)
        git(sibling, "config", "core.hooksPath", str(hookdir))
    elif kind == "fsmonitor":
        git(sibling, "config", "core.fsmonitor", str(script))
    elif kind.startswith("filter-"):
        git(sibling, "config", f"filter.trip.{kind[7:]}", shlex.quote(str(script)))
        git(sibling, "config", "filter.trip.required", "true")
        (sibling / ".gitattributes").write_text("*.txt filter=trip\n")
    elif kind == "upload-pack":
        git(sibling, "config", "remote.origin.uploadpack", str(script))
    elif kind == "remote-helper":
        git(sibling, "config", "remote.origin.url", "ext::" + str(script))
    elif kind == "url-rewrite":
        git(sibling, "config", "url.ext::trip.insteadOf", "git@github.com:")
    elif kind == "ssh-command":
        git(sibling, "config", "core.sshCommand", str(script))
    elif kind in {"gpg", "ssh-signature"}:
        git(sibling, "config", "merge.verifySignatures", "true")
        if kind == "gpg":
            git(sibling, "config", "gpg.program", str(script))
        else:
            git(sibling, "config", "gpg.format", "ssh")
            git(sibling, "config", "gpg.ssh.program", str(script))
            signers = tmp_path / "allowed-signers"
            signers.write_text("fixture@example.invalid ssh-ed25519 Zml4dHVyZQ==\n")
            git(sibling, "config", "gpg.ssh.allowedSignersFile", str(signers))
    else:
        home = Path(os.environ["HOME"])
        home.mkdir()
        (home / ".gitconfig").write_text(f'[filter "trip"]\n process = {script}\n required = true\n')
        (sibling / ".gitattributes").write_text("*.txt filter=trip\n")
    code, _, err = invoke("sync-main")
    assert code == (0 if kind in {"hooks", "fsmonitor", "gpg", "ssh-signature"} else 2), err
    if kind in {"gpg", "ssh-signature"}:
        assert git(sibling, "rev-parse", "HEAD") == sha
    assert not (world[0] / "tripwire").exists()


@pytest.mark.parametrize("verb", ["status", "sync-main", "worktree-remove"])
@pytest.mark.parametrize(
    "key,refused",
    [
        ("gpg.program", False),
        ("gpg.openpgp.program", False),
        ("gpg.x509.program", False),
        ("gpg.ssh.program", False),
        ("gpg.future.program", True),
        ("gpg.ssh.defaultKeyCommand", True),
        ("merge.verifySignatures", False),
        ("merge.gpgSign", False),
        ("core.pager", False),
        ("pager.status", False),
        ("pager.fetch", False),
        ("pager.merge", False),
        ("pager.worktree", False),
        ("pager.diff", False),
        ("core.editor", False),
        ("sequence.editor", False),
        ("diff.external", False),
        ("diff.trip.command", True),
        ("diff.trip.textconv", True),
        ("credential.helper", False),
        ("credential.ssh://git@github.com.helper", True),
        ("core.askPass", False),
        ("core.gitProxy", True),
        ("http.proxy", True),
        ("http.ssh://git@github.com.proxy", True),
        ("remote.origin.proxy", True),
        ("remote.origin.proxyAuthMethod", True),
        ("core.alternateRefsCommand", True),
        ("gc.recentObjectsHook", True),
        ("extensions.partialClone", True),
        ("remote.hidden.promisor", True),
    ],
)
def test_swept_executable_keys_never_run(world, managed, tmp_path, key, refused, verb):
    sha = advance(world, tmp_path)
    sibling = world[1]
    script = tripwire(world, tmp_path)
    command = shlex.quote(str(script))
    value = command
    if key == "credential.helper" or key.startswith("http."):
        value = "!" + command
    elif key.endswith(".promisor"):
        value = "true"
        git(sibling, "config", "remote.hidden.url", "ext::" + command)
    elif key.startswith("merge."):
        value = "true"
        git(sibling, "config", "gpg.program", str(script))
    git(sibling, "config", "--add", key, value)
    if key == "credential.helper":
        # Empty helper override must clear every value, not just the last one.
        git(sibling, "config", "--add", key, "!" + command)
    if key.startswith("diff.trip."):
        (sibling / ".git/info/attributes").write_text("*.txt diff=trip\n")
    before = git(sibling, "rev-parse", "HEAD")
    code, _, err = invoke(verb, managed if verb == "worktree-remove" else None)
    assert code == (2 if refused else 0), err
    assert not (world[0] / "tripwire").exists()
    if refused:
        assert managed.exists()
        assert git(sibling, "rev-parse", "HEAD") == before
    elif verb == "sync-main":
        assert git(sibling, "rev-parse", "HEAD") == sha
    elif verb == "worktree-remove":
        assert not managed.exists()


@pytest.mark.parametrize("key", ["protocol.allow", "protocol.ext.allow", "protocol.file.allow", "protocol.ssh.allow"])
def test_protocol_configuration_cannot_enable_tripwire(world, tmp_path, key):
    advance(world, tmp_path)
    script = tripwire(world, tmp_path)
    git(world[1], "config", key, "always")
    assert invoke("sync-main")[0] == 0
    with sg.git_session() as runner:
        probe = runner.run(world[1], ["fetch", "--", "ext::" + shlex.quote(str(script)), "refs/heads/main"])
    assert probe.returncode != 0
    assert "transport 'ext' not allowed" in probe.stderr
    assert not (world[0] / "tripwire").exists()


@pytest.mark.parametrize("kind", ["gpg", "ssh"])
def test_signed_fixture_triggers_unprotected_verifier(world, tmp_path, kind):
    sha = signed_advance(world, tmp_path, kind)
    sibling = world[1]
    git(sibling, "fetch", str(world[2]), "main")
    fired = tmp_path / "unprotected-verifier-fired"
    script = tmp_path / "unprotected verifier"
    script.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(fired))}\nexit 1\n")
    script.chmod(0o700)
    git(sibling, "config", "merge.verifySignatures", "true")
    git(sibling, "config", "gpg.program" if kind == "gpg" else "gpg.ssh.program", str(script))
    if kind == "ssh":
        git(sibling, "config", "gpg.format", "ssh")
        git(sibling, "config", "gpg.ssh.allowedSignersFile", str(tmp_path / "signers"))
        (tmp_path / "signers").write_text("fixture@example.invalid ssh-ed25519 Zml4dHVyZQ==\n")
    with pytest.raises(subprocess.CalledProcessError):
        git(sibling, "merge", "--ff-only", sha)
    assert fired.exists(), "signed fixture did not reach the configured verifier"


@pytest.mark.parametrize("name", ["notes.txt", " leading.txt", "line\nbreak.txt"])
def test_sync_preserves_ignored_local_file(world, tmp_path, name):
    sibling = world[1]
    (sibling / ".git/info/exclude").write_text("*.txt\n")
    local = sibling / name
    local.write_text("ignored local work\n")
    advance(world, tmp_path, name, "upstream\n")
    old = git(sibling, "rev-parse", "HEAD")
    code, _, err = invoke("sync-main")
    assert code == 2
    assert ("control or formatting characters" if "\n" in name else "overwrite ignored local files") in err
    assert git(sibling, "rev-parse", "HEAD") == old
    assert local.read_text() == "ignored local work\n"


def test_sync_allows_unrelated_ignored_local_file(world, tmp_path):
    sibling = world[1]
    (sibling / ".git/info/exclude").write_text("notes.txt\n")
    (sibling / "notes.txt").write_text("ignored local work\n")
    sha = advance(world, tmp_path)
    code, _, err = invoke("sync-main")
    assert code == 0, err
    assert git(sibling, "rev-parse", "HEAD") == sha
    assert (sibling / "notes.txt").read_text() == "ignored local work\n"


@pytest.mark.parametrize("kind", ["file-to-directory", "directory-to-file", "after-probe"])
def test_merge_guard_preserves_ignored_local_collisions(world, tmp_path, monkeypatch, kind):
    sibling = world[1]
    (sibling / ".git/info/exclude").write_text("notes\n")
    advance(world, tmp_path)
    writer = tmp_path / "writer"
    incoming = "notes/item.txt" if kind == "file-to-directory" else "notes"
    if "/" in incoming:
        (writer / "notes").mkdir()
    commit(writer, incoming, "incoming\n")
    git(writer, "push", "origin", "main")
    local = sibling / ("notes/item.txt" if kind == "directory-to-file" else "notes")
    local.parent.mkdir(parents=True, exist_ok=True)
    if kind != "after-probe":
        local.write_text("ignored local work\n")
    else:
        original = sg.Git.text

        def inject_after_probe(self, path, *args):
            if args[0] == "merge":
                local.write_text("ignored local work\n")
            return original(self, path, *args)

        monkeypatch.setattr(sg.Git, "text", inject_after_probe)
    old = git(sibling, "rev-parse", "HEAD")
    old_content = (sibling / "file.txt").read_bytes()
    code, _, err = invoke("sync-main")
    assert code == 2 and "Git merge failed" in err
    assert git(sibling, "rev-parse", "HEAD") == old
    assert (sibling / "file.txt").read_bytes() == old_content
    assert local.read_text() == "ignored local work\n"


def test_new_commit_filter_attribute_refused(world, tmp_path):
    advance(world, tmp_path, ".gitattributes", "*.txt filter=required\n")
    old = git(world[1], "rev-parse", "HEAD")
    assert invoke("sync-main")[0] == 2
    assert git(world[1], "rev-parse", "HEAD") == old


@pytest.mark.parametrize("kind", ["dirty", "untracked", "diverged", "local-ahead", "branch", "fetch-failed"])
def test_sync_refusals_preserve_local_work(world, tmp_path, kind):
    _, sibling, upstream = world
    if kind == "dirty":
        (sibling / "file.txt").write_text("local edits\n")
    elif kind == "untracked":
        (sibling / "untracked").write_text("local\n")
    elif kind in {"diverged", "local-ahead"}:
        commit(sibling, text="local commit\n")
    elif kind == "branch":
        git(sibling, "checkout", "-b", "topic")
    else:
        upstream.rename(tmp_path / "missing upstream")
    if kind in {"dirty", "untracked", "diverged", "branch"}:
        advance(world, tmp_path)
    before = git(sibling, "rev-parse", "HEAD"), (sibling / "file.txt").read_bytes()
    assert invoke("sync-main")[0] == 2
    assert (git(sibling, "rev-parse", "HEAD"), (sibling / "file.txt").read_bytes()) == before


@pytest.mark.parametrize(
    "kind", ["locked", "dirty", "active", "busy", "outside", "unregistered", "missing-lock", "target-config"]
)
def test_removal_refusals(world, managed, tmp_path, kind):
    primary, sibling, _ = world
    target = managed
    record = None
    held = None
    if kind == "locked":
        git(sibling, "worktree", "lock", str(target))
    elif kind == "dirty":
        (target / "local").write_text("preserve\n")
    elif kind == "active":
        record = primary / "batch_state/tasks/active.json"
        record.write_text(json.dumps({"task_id": "active", "worktree_path": str(target), "status": "running"}))
    elif kind == "busy":
        held = wc.worktree_lock(target, lock_dir=primary / ".git" / wc.LOCK_DIR_NAME)
        held.__enter__()
    elif kind == "outside":
        target = primary
    elif kind == "unregistered":
        target = sibling / ".worktrees/dispatch/codex/unregistered"
        target.mkdir()
    elif kind == "missing-lock":
        _, lock = wc.lock_path(target, lock_dir=primary / ".git" / wc.LOCK_DIR_NAME)
        saved = lock.read_bytes()
        lock.unlink()
    else:
        git(sibling, "config", "extensions.worktreeConfig", "true")
        git(target, "config", "--worktree", "core.worktree", str(primary))
    before = snapshot(primary)
    assert invoke("worktree-remove", target)[0] == 2
    assert managed.exists()
    assert snapshot(primary) == before
    if held:
        held.__exit__(None, None, None)
    if record:
        record.unlink()
    if kind == "missing-lock":
        lock.write_bytes(saved)


def fixture_hook(primary, monkeypatch, *, deployed=False):
    for relative in (
        "scripts/__init__.py",
        "scripts/fleet/__init__.py",
        "scripts/fleet/sibling_git.py",
        "scripts/guardrails/worktree_containment.py",
    ):
        dest = primary / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    path = primary / (
        ".codex/hooks/guard-primary-checkout-write.py"
        if deployed
        else "agents_extensions/shared/hooks/guard-primary-checkout-write.py"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HOOK, path)
    shutil.copyfile(HOOK.parent / "shell_shlex.py", path.parent / "shell_shlex.py")
    spec = importlib.util.spec_from_file_location("fixture_guard", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "__file__", str(path))
    return module


def decide(hook, command, cwd):
    payload = {"tool_name": "Bash", "cwd": str(cwd), "tool_input": {"command": command}}
    with redirect_stderr(io.StringIO()):
        hook._read_payload = lambda: payload
        return hook.main()


@pytest.mark.parametrize("verb", ["status", "sync-main", "worktree-remove"])
def test_documented_verbs_through_deployed_hook(world, managed, tmp_path, monkeypatch, verb):
    primary, _, _ = world
    hook = fixture_hook(primary, monkeypatch, deployed=True)
    advance(world, tmp_path)
    command = f"{shlex.quote(str(primary / '.venv/bin/python'))} -m scripts.fleet.sibling_git {verb} --repo test"
    if verb == "worktree-remove":
        command += " " + shlex.quote(str(managed))
    before = snapshot(primary)
    assert decide(hook, command, primary) == 0
    payload = {"tool_name": "Bash", "cwd": str(primary), "tool_input": {"command": command}}
    # The pytest child tripwire injects PYTHONPATH during Popen. Leave its
    # already-installed instrumentation active, then clear that test-only
    # startup setting before the production hook evaluates the payload.
    assert "PYTHONPATH" not in os.environ
    deployed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os,runpy,sys; os.environ.pop('PYTHONPATH',None); runpy.run_path(sys.argv[1],run_name='__main__')",
            hook.__file__,
        ],
        cwd=primary,
        input=json.dumps(payload),
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert deployed.returncode == 0, deployed.stderr
    assert invoke(verb, managed if verb == "worktree-remove" else None)[0] == 0
    assert snapshot(primary) == before
    # Remove fixture-only code before the outer primary preservation check.
    shutil.rmtree(primary / "scripts")
    shutil.rmtree(primary / ".codex")


ATTACKS = [
    "true && {cmd}",
    "false && cd x; {cmd}",
    "cd missing/..; {cmd}",
    "cd x || {cmd}",
    "{cmd}; git reset --hard",
    "{cmd} && true",
    "{cmd} | cat",
    "{cmd} > out",
    "{cmd} 2>&1",
    "echo $({cmd})",
    "echo `{cmd}`",
    "env {cmd}",
    "PYTHONPATH=/tmp {cmd}",
    "GIT_DIR=/tmp {cmd}",
    "{cmd}\ntrue",
    "({cmd})",
    "{{ {cmd}; }}",
    "f() {{ {cmd}; }}; f",
    "{cmd} --force",
    "{cmd} --repo public",
    "{interpreter} -I -m scripts.fleet.sibling_git sync-main --repo test",
    "python -m scripts.fleet.sibling_git sync-main --repo test",
]


@pytest.mark.parametrize("shape", ATTACKS)
def test_invocation_attacks_refused(world, monkeypatch, shape):
    primary, _, _ = world
    hook = fixture_hook(primary, monkeypatch)
    interpreter = shlex.quote(str(primary / ".venv/bin/python"))
    cmd = f"{interpreter} -m scripts.fleet.sibling_git sync-main --repo test"
    command = shape.format(cmd=cmd, quoted=shlex.quote(cmd), interpreter=interpreter)
    before = snapshot(primary)
    assert decide(hook, command, primary) == 2
    assert snapshot(primary) == before
    shutil.rmtree(primary / "scripts")
    shutil.rmtree(primary / "agents_extensions")


@pytest.mark.parametrize(
    "shape",
    [
        "rg scripts.fleet.sibling_git scripts",
        "{interpreter} -m pytest -k scripts.fleet.sibling_git",
        "bash -c {quoted}",
        "eval {quoted}",
        "{interpreter} -c 'import scripts.fleet.sibling_git'",
        "{interpreter} -m scripts.fleet.sibling_gitx sync-main --repo test",
    ],
)
def test_module_mentions_without_word_pair_match_main(world, monkeypatch, shape):
    primary = world[0]
    hook = fixture_hook(primary, monkeypatch)
    interpreter = shlex.quote(str(primary / ".venv/bin/python"))
    cmd = f"{interpreter} -m scripts.fleet.sibling_git sync-main --repo test"
    command = shape.format(interpreter=interpreter, quoted=shlex.quote(cmd))
    baseline = types.ModuleType("main_guard_baseline")
    baseline.__file__ = hook.__file__
    source = git(ROOT, "show", "origin/main:agents_extensions/shared/hooks/guard-primary-checkout-write.py")
    exec(compile(source, baseline.__file__, "exec"), baseline.__dict__)
    before = snapshot(primary)
    try:
        assert decide(hook, command, primary) == decide(baseline, command, primary) == 0
        assert snapshot(primary) == before
    finally:
        shutil.rmtree(primary / "scripts")
        shutil.rmtree(primary / "agents_extensions")


@pytest.mark.parametrize(
    "kind", ["other-cwd", "module-link", "package-link", "pythonpath", "pythonhome", "bytecode", "shadow"]
)
def test_module_context_attacks(world, tmp_path, monkeypatch, kind):
    primary, _, _ = world
    hook = fixture_hook(primary, monkeypatch)
    cwd = primary
    if kind == "other-cwd":
        cwd = tmp_path
    elif kind in {"module-link", "package-link"}:
        name = "sibling_git.py" if kind == "module-link" else "__init__.py"
        path = primary / "scripts/fleet" / name
        path.unlink()
        path.symlink_to(ROOT / "scripts/fleet" / name)
    elif kind == "pythonpath":
        monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    elif kind == "pythonhome":
        monkeypatch.setenv("PYTHONHOME", str(tmp_path))
    elif kind == "bytecode":
        monkeypatch.delenv("PYTHONDONTWRITEBYTECODE")
    else:
        cwd = tmp_path / "shadow"
        cwd.mkdir()
        (cwd / "scripts").mkdir()
        (cwd / "scripts/__init__.py").write_text("raise RuntimeError('shadow')\n")
    cmd = f"{shlex.quote(str(primary / '.venv/bin/python'))} -m scripts.fleet.sibling_git status --repo test"
    before = snapshot(primary)
    assert decide(hook, cmd, cwd) == 2
    assert snapshot(primary) == before
    shutil.rmtree(primary / "scripts")
    shutil.rmtree(primary / "agents_extensions")


@pytest.mark.parametrize(
    "shape",
    [
        "git -C {sibling} merge --ff-only origin/main",
        "cd {sibling} && git merge --ff-only origin/main",
        "git -C {sibling} worktree remove {target}",
    ],
)
def test_raw_sibling_git_behavior_matches_main(world, monkeypatch, shape):
    primary, sibling, _ = world
    hook = fixture_hook(primary, monkeypatch)
    command = shape.format(sibling=shlex.quote(str(sibling)), target=shlex.quote(str(primary / "file.txt")))
    baseline = types.ModuleType("main_guard_baseline")
    baseline.__file__ = hook.__file__
    source = git(ROOT, "show", "origin/main:agents_extensions/shared/hooks/guard-primary-checkout-write.py")
    exec(compile(source, baseline.__file__, "exec"), baseline.__dict__)
    assert decide(hook, command, primary) == decide(baseline, command, primary)
    if "merge" in shape:
        assert decide(hook, command, primary) == 2
    shutil.rmtree(primary / "scripts")
    shutil.rmtree(primary / "agents_extensions")


def test_help_and_invalid_argv(world, capsys):
    with pytest.raises(SystemExit) as exc:
        sg.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert all(
        word in help_text
        for word in ("Examples", "Outputs:", "Exit codes:", "Related:", "sync-main", "worktree-remove")
    )
    for args in (
        ["fetch", "--repo", "test"],
        ["status", "--repo", "test", "/tmp"],
        ["worktree-remove", "--repo", "test"],
        ["status", "--rep", "test"],
    ):
        with pytest.raises(SystemExit) as exc:
            sg.main(args)
        assert exc.value.code == 2


def test_own_primary_marker_resolution(tmp_path):
    init(tmp_path / "public")
    primary = tmp_path / "public"
    assert sg.primary_root(primary) == primary
    worktree = primary / ".worktrees/dispatch/codex/task"
    worktree.parent.mkdir(parents=True)
    git(primary, "worktree", "add", "--detach", str(worktree))
    assert sg.primary_root(worktree) == primary


@pytest.mark.parametrize("raw", ["relative/path", "/tmp/../tmp", "/tmp/with\nnewline", "/tmp/with\u202ebidi"])
def test_plain_path_validation(raw):
    with pytest.raises(sg.Refusal):
        sg._plain_path(Path(raw), exists=False)


def test_unused_filter_is_safe(world):
    git(world[1], "config", "filter.unused.process", "exit 99")
    assert invoke("status")[0] == 0


@pytest.mark.parametrize("name", [" leading.txt", "trailing .txt", "line\nbreak.txt"])
def test_filter_paths_keep_exact_nul_delimited_names(world, tmp_path, name):
    _, sibling, _ = world
    commit(sibling, name, "local fixture\n")
    script = tripwire(world, tmp_path)
    git(sibling, "config", "filter.trip.clean", shlex.quote(str(script)))
    (sibling / ".git/info/attributes").write_text("*.txt filter=trip\n")
    assert invoke("status")[0] == 2
    assert not (world[0] / "tripwire").exists()


def test_detached_status(world):
    git(world[1], "checkout", "--detach")
    code, out, err = invoke("status")
    assert code == 0, err
    assert json.loads(out)["branch"] is None


@pytest.mark.parametrize(
    "kind", ["file", "https", "other-ssh", "uploadpack", "helper", "merge-options", "attribute-file"]
)
def test_closed_remote_and_configuration(world, kind):
    _, sibling, upstream = world
    if kind == "file":
        git(sibling, "config", "remote.origin.url", str(upstream))
    elif kind == "https":
        git(sibling, "config", "remote.origin.url", "https://github.com/fixture/sibling.git")
    elif kind == "other-ssh":
        git(sibling, "config", "remote.origin.url", "git@github.com:fixture/other.git")
    elif kind == "uploadpack":
        git(sibling, "config", "uploadpack.packObjectsHook", "exit 99")
    elif kind == "helper":
        git(sibling, "config", "remote.origin.vcs", "trip")
    elif kind == "merge-options":
        git(sibling, "config", "branch.main.mergeOptions", "--squash")
    else:
        git(sibling, "config", "core.attributesFile", "false")
    assert invoke("sync-main")[0] == 2


def test_supported_ssh_url_and_configured_filters_unused(world, tmp_path):
    sha = advance(world, tmp_path)
    git(world[1], "config", "remote.origin.url", "ssh://git@github.com/fixture/sibling.git")
    git(world[1], "config", "filter.unused.smudge", "exit 99")
    code, _, err = invoke("sync-main")
    assert code == 0, err
    assert git(world[1], "rev-parse", "HEAD") == sha


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_checkout_shared_file_refused(world, kind):
    primary, sibling, _ = world
    (sibling / "file.txt").unlink()
    if kind == "symlink":
        (sibling / "file.txt").symlink_to(primary / "file.txt")
    else:
        os.link(primary / "file.txt", sibling / "file.txt")
    assert invoke("sync-main")[0] == 2


def test_dirty_status_reports_state(world):
    (world[1] / "file.txt").write_text("local work\n")
    code, out, err = invoke("status")
    assert code == 0, err
    assert json.loads(out)["clean"] is False


def test_status_reports_registered_locked_worktree(world, managed):
    git(world[1], "worktree", "lock", str(managed))
    code, out, err = invoke("status")
    assert code == 0, err
    info = json.loads(out)
    assert info["worktree_count"] == 2
    assert info["worktrees"][1]["location"] == ".worktrees/dispatch/codex/finished task"
    assert info["worktrees"][1]["locked"] is True


def test_relative_interpreter_and_help_literal(world, monkeypatch):
    primary, _, _ = world
    hook = fixture_hook(primary, monkeypatch)
    assert decide(hook, ".venv/bin/python -m scripts.fleet.sibling_git --help", primary) == 0
    absolute = str(primary / ".venv/bin/python")
    assert decide(hook, f'"{absolute}" -m scripts.fleet.sibling_git status --repo test', primary) == 0
    shutil.rmtree(primary / "scripts")
    shutil.rmtree(primary / "agents_extensions")


def test_guard_tool_workdir_overrides_session_cwd(world, monkeypatch):
    primary, _, _ = world
    hook = fixture_hook(primary, monkeypatch)
    command = f"{shlex.quote(str(primary / '.venv/bin/python'))} -m scripts.fleet.sibling_git status --repo test"
    payload = {
        "tool_name": "Bash",
        "cwd": str(primary.parent),
        "tool_input": {"command": command, "workdir": str(primary)},
    }
    hook._read_payload = lambda: payload
    assert hook.main() == 0
    shutil.rmtree(primary / "scripts")
    shutil.rmtree(primary / "agents_extensions")
