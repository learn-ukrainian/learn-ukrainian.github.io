"""git push publication scan in Git's native pre-push hook (#9339); synthetic data, local bare remotes only.

Integration tests push through a copy of the agent git shim and judge the
outcome by what the local bare "public" remote holds, never by scanner logs.
In-process tests call the hook's main with hand-written pre-push input.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path

import pytest

from scripts.opsec import git_push
from scripts.opsec import prepublish as gate
from tests.opsec_fixtures import CATALOG, MATCHER, ROOT, TOKEN, make_tooling, synthetic_rules

REAL_GIT = shutil.which("git", path=os.defpath)
pytestmark = pytest.mark.skipif(REAL_GIT is None, reason="git unavailable")
ZERO = "0" * 40


def _env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT", "LU_OPSEC", "PYTHON"))}
    env.update(
        PATH=os.pathsep.join([str(Path(REAL_GIT).parent), os.defpath]),
        AGENT_REAL_GIT=REAL_GIT,
        # Shim pushes build the real public-repository client; it must fail closed, never reach GitHub.
        AGENT_REAL_GH=os.devnull,
        AGENT_NO_MERGE="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
    )
    env.update(extra)
    return env


def _git(cwd, *args, env=None, **kwargs):
    return subprocess.run(
        [REAL_GIT, *args], cwd=cwd, env=env or _env(), check=True, capture_output=True, text=True, timeout=60, **kwargs
    ).stdout.strip()


def _repository(path, *, bare=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(path.parent, "init", "-q", "-b", "trunk", *(["--bare"] if bare else []), str(path))
    if not bare:
        _git(path, "config", "user.email", "unit@example.invalid")
        _git(path, "config", "user.name", "unit")
    return path


@pytest.fixture
def push_sandbox(tmp_path):
    """A shim copy with synthetic tooling, a work repository and a bare local (public) remote."""
    root = tmp_path / "public-fixture"
    (root / "scripts/agent_runtime/shims").mkdir(parents=True)
    (root / "scripts/__init__.py").write_text("")
    shutil.copytree(ROOT / "scripts/opsec", root / "scripts/opsec", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(ROOT / "scripts/agent_runtime/shims/git", root / "scripts/agent_runtime/shims/git")
    (root / "scripts/config").mkdir()
    (root / "scripts/config/fleet_repos.yaml").write_text(json.dumps({"repos": CATALOG}))
    (root / ".venv").symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    _git(tmp_path, "init", "-q", str(root))
    tooling = make_tooling(tmp_path / "private-fixture/tools/public_opsec_scan")
    remote = _repository(tmp_path / "remote.git", bare=True)
    work = _repository(tmp_path / "work")
    (work / "file.txt").write_text("clean\n")
    _git(work, "add", "file.txt")
    _git(work, "commit", "-q", "-m", "clean base")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-q", "-u", "origin", "trunk")

    class Sandbox:
        shim = root / "scripts/agent_runtime/shims/git"

        def __init__(self):
            self.root, self.tooling, self.remote, self.work, self.tmp = root, tooling, remote, work, tmp_path

        def commit(self, message, cwd=None):
            cwd = cwd or self.work
            (cwd / "file.txt").write_text((cwd / "file.txt").read_text() + "x\n")
            _git(cwd, "commit", "-q", "-am", message)
            return _git(cwd, "rev-parse", "HEAD")

        def push(self, *args, cwd=None, **extra):
            return subprocess.run(
                [str(self.shim), *args],
                cwd=cwd or self.work,
                env=_env(**extra),
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )

        def remote_refs(self, remote=None):
            listing = _git(remote or self.remote, "for-each-ref", "--format=%(refname) %(objectname)")
            return dict(line.split() for line in listing.splitlines())

    return Sandbox()


def assert_blocked(result, sandbox, before, field):
    assert result.returncode != 0, result.stderr
    assert "OPSEC blocked: rule=synthetic-rule" in result.stderr and f"field={field}" in result.stderr, result.stderr
    assert TOKEN not in result.stderr and TOKEN not in result.stdout
    assert sandbox.remote_refs() == before


def _remote_has(sandbox, sha, remote=None):
    probe = [REAL_GIT, "cat-file", "-e", sha]
    return subprocess.run(probe, cwd=remote or sandbox.remote, env=_env(), timeout=30).returncode == 0


# --- Every text kind a push publishes; whole messages; multiple updates ---


def test_commit_message_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("clean subject\n\nbody " + TOKEN)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")
    assert "line=3" in result.stderr and not _remote_has(push_sandbox, sha)


def test_branch_name_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean")
    result = push_sandbox.push("push", "origin", f"HEAD:refs/heads/feature-{TOKEN}")
    assert_blocked(result, push_sandbox, before, "branch[1].name")


def test_lightweight_tag_name_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    _git(push_sandbox.work, "tag", f"v1-{TOKEN}")
    result = push_sandbox.push("push", "origin", "--tags")
    assert_blocked(result, push_sandbox, before, "tag[1].name")


def test_annotated_tag_message_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "release " + TOKEN)
    tag = _git(push_sandbox.work, "rev-parse", "v1")
    result = push_sandbox.push("push", "origin", "v1")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].message")


def test_follow_tags_annotated_tag_hit_is_refused(push_sandbox):
    """Tags Git adds to the push itself reach the hook as updates too."""
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean subject")
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "release " + TOKEN)
    tag = _git(push_sandbox.work, "rev-parse", "v1")
    result = push_sandbox.push("push", "--follow-tags", "origin", "trunk")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].message")


def test_one_hit_among_several_updates_sends_none_of_them(push_sandbox):
    before = push_sandbox.remote_refs()
    clean = push_sandbox.commit("clean subject")
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "release " + TOKEN)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/a", "HEAD:refs/heads/b", "v1")
    assert result.returncode != 0 and "OPSEC blocked" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before and not _remote_has(push_sandbox, clean)


def _object(cwd, kind, data: bytes):
    """Write a raw object without git's format checks, as a careless or hand-made object would be."""
    return (
        subprocess.run(
            [REAL_GIT, "hash-object", "-t", kind, "--literally", "-w", "--stdin"],
            cwd=cwd,
            env=_env(),
            input=data,
            capture_output=True,
            check=True,
            timeout=30,
        )
        .stdout.decode()
        .strip()
    )


def _tag(cwd, target, kind, name, message=b"clean release\n"):
    header = f"object {target}\ntype {kind}\ntag {name}\ntagger unit <unit@example.invalid> 0 +0000\n\n"
    return _object(cwd, "tag", header.encode() + message)


def _commit(cwd, message: bytes):
    tree, parent = _git(cwd, "rev-parse", "HEAD^{tree}"), _git(cwd, "rev-parse", "HEAD")
    identity = "unit <unit@example.invalid> 0 +0000"
    header = f"tree {tree}\nparent {parent}\nauthor {identity}\ncommitter {identity}\n\n"
    return _object(cwd, "commit", header.encode() + message)


def test_annotated_tag_embedded_name_hit_is_refused_under_a_clean_alias(push_sandbox):
    before = push_sandbox.remote_refs()
    tag = _tag(push_sandbox.work, _git(push_sandbox.work, "rev-parse", "HEAD"), "commit", f"v1-{TOKEN}")
    result = push_sandbox.push("push", "origin", f"{tag}:refs/tags/clean-alias")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].tagname")


def test_nested_tag_embedded_name_hit_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    inner = _tag(push_sandbox.work, _git(push_sandbox.work, "rev-parse", "HEAD"), "commit", f"v1-{TOKEN}")
    outer = _tag(push_sandbox.work, inner, "tag", "clean-outer")
    result = push_sandbox.push("push", "origin", f"{outer}:refs/tags/clean-alias")
    assert_blocked(result, push_sandbox, before, f"tag[{inner[:12]}].tagname")


def test_clean_nested_tag_passes(push_sandbox):
    inner = _tag(push_sandbox.work, _git(push_sandbox.work, "rev-parse", "HEAD"), "commit", "v1-clean")
    outer = _tag(push_sandbox.work, inner, "tag", "clean-outer")
    result = push_sandbox.push("push", "origin", f"{outer}:refs/tags/clean-alias")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/tags/clean-alias"] == outer


def test_commit_message_hit_after_a_nul_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = _commit(push_sandbox.work, b"clean subject\x00 " + TOKEN.encode() + b"\n")
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


@pytest.mark.parametrize("message", [b"clean subject\n\nclean body\n", b"clean subject\x00clean tail\n"])
def test_wholly_scanned_clean_raw_commit_is_delivered(push_sandbox, message):
    sha = _commit(push_sandbox.work, message)
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


def test_tag_message_hit_after_a_nul_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    tag = _tag(push_sandbox.work, head, "commit", "v1", b"clean release\x00 " + TOKEN.encode() + b"\n")
    result = push_sandbox.push("push", "origin", f"{tag}:refs/tags/v1")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].message")


def _signed_tag(cwd, target, name, message="clean release\n"):
    """A tag git treats as signed: merging it embeds the whole tag object in a mergetag header."""
    armor = "-----BEGIN PGP SIGNATURE-----\n\nAAAA\n-----END PGP SIGNATURE-----\n"
    tag = _tag(cwd, target, "commit", name, (message + armor).encode())
    _git(cwd, "update-ref", f"refs/tags/{name}", tag)
    return name


def _side(sandbox, branch, message="side work"):
    """A commit on a new branch off the base, leaving the work tree on trunk."""
    work = sandbox.work
    _git(work, "checkout", "-q", "-b", branch, "trunk")
    (work / f"{branch}.txt").write_text("side\n")
    _git(work, "add", f"{branch}.txt")
    _git(work, "commit", "-q", "-m", message)
    sha = _git(work, "rev-parse", "HEAD")
    _git(work, "checkout", "-q", "trunk")
    return sha


def _merge(sandbox, *tags):
    _git(sandbox.work, "merge", "-q", "--no-ff", "-m", "clean merge", *tags)
    merge = _git(sandbox.work, "rev-parse", "HEAD")
    assert _git(sandbox.work, "cat-file", "commit", merge).count("\nmergetag ") == len(tags)
    return merge


@pytest.mark.parametrize(
    ("name", "message", "field"),
    [
        pytest.param("v1", f"clean release\n\nbody {TOKEN}\n", "message", id="embedded-message"),
        pytest.param(f"v1-{TOKEN}", "clean release\n", "tagname", id="embedded-name"),
    ],
)
def test_mergetag_hit_under_a_clean_merge_message_is_refused(push_sandbox, name, message, field):
    before = push_sandbox.remote_refs()
    tag = _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), name, message)
    merge = _merge(push_sandbox, tag)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{merge[:12]}].mergetag[1].{field}")
    assert f"commit[{merge[:12]}].message" not in result.stderr


def test_clean_signed_tag_merge_still_delivers(push_sandbox):
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), "v1"))
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == merge


def test_octopus_merge_hit_in_the_second_mergetag_only_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    first = _signed_tag(push_sandbox.work, _side(push_sandbox, "one"), "v1")
    second = _signed_tag(push_sandbox.work, _side(push_sandbox, "two"), "v2", f"clean release\n\nbody {TOKEN}\n")
    merge = _merge(push_sandbox, first, second)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{merge[:12]}].mergetag[2].message")
    assert "mergetag[1]" not in result.stderr


def _unseparated(sandbox, kind):
    tree, parent = _git(sandbox.work, "rev-parse", "HEAD^{tree}"), _git(sandbox.work, "rev-parse", "HEAD")
    identity = "unit <unit@example.invalid> 0 +0000"
    if kind == "tag":
        raw = f"object {parent}\ntype commit\ntag v1\ntagger {identity}\nrelease {TOKEN}\n"
        return _object(sandbox.work, "tag", raw.encode()), "tag[{}]"
    raw = f"tree {tree}\nparent {parent}\nauthor {identity}\ncommitter {identity}\n"
    if kind == "mergetag":
        raw += f"mergetag object {parent}\n type commit\n tag v1\n release {TOKEN}\n\nclean merge\n"
        return _object(sandbox.work, "commit", raw.encode()), "commit[{}].mergetag[1]"
    return _object(sandbox.work, "commit", (raw + f"clean subject {TOKEN}\n").encode()), "commit[{}]"


@pytest.mark.parametrize("kind", ["commit", "tag", "mergetag"])
def test_object_without_a_header_body_separator_is_refused(push_sandbox, kind):
    before = push_sandbox.remote_refs()
    sha, position = _unseparated(push_sandbox, kind)
    ref = "refs/tags/v1" if kind == "tag" else "refs/heads/feature"
    result = push_sandbox.push("push", "origin", f"{sha}:{ref}")
    assert result.returncode != 0, result.stderr
    assert f"OPSEC: {position.format(sha[:12])} has no header/body separator; push refused." in result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before


@pytest.mark.parametrize(
    ("raw", "fields", "expected"),
    [
        pytest.param(b"tag v1\n\nclean\x00" + TOKEN.encode(), [(b"tag", b"v1")], ["clean\x00" + TOKEN], id="nul"),
        pytest.param(
            b"tag v1\nmergetag object x\n tag continuation-is-not-a-field\n \n\nbody " + TOKEN.encode(),
            [(b"tag", b"v1"), (b"mergetag", b"object x\ntag continuation-is-not-a-field\n")],
            ["body " + TOKEN],
            id="continuation",
        ),
        pytest.param(b"\nheader-like line\n\n" + TOKEN.encode(), [], ["header-like line", "", TOKEN], id="opens-empty"),
        pytest.param(
            b"encoding ISO-8859-1\n\ncaf\xe9 " + TOKEN.encode(),
            [(b"encoding", b"ISO-8859-1")],
            ["caf� " + TOKEN, "caf\xe9 " + TOKEN],
            id="declared-latin-1",
        ),
        pytest.param(
            b"encoding UTF-16\n\nab" + TOKEN.encode(), [(b"encoding", b"UTF-16")], ["ab" + TOKEN], id="declared-utf-16"
        ),
        pytest.param(
            b"encoding no-such-codec\n\n" + TOKEN.encode(), [(b"encoding", b"no-such-codec")], [TOKEN], id="unknown"
        ),
    ],
)
def test_split_object_keeps_every_reading_of_the_whole_message(raw, fields, expected):
    found_fields, message = git_push.split_object(raw, "commit[unit]")
    assert found_fields == fields
    assert message.split("\n")[: len(expected)] == expected
    assert TOKEN in message


@pytest.mark.parametrize("raw", [b"tag v1\nno separator " + TOKEN.encode(), b" opening continuation\n\nbody"])
def test_split_object_refuses_text_outside_any_message(raw):
    with pytest.raises(gate.PublishBlocked) as raised:
        git_push.split_object(raw, "commit[unit]")
    assert str(raised.value).startswith("OPSEC: commit[unit] ") and TOKEN not in str(raised.value)


def _unfold_seconds(size, repeats=5):
    """Best time to split a commit whose mergetag header continues over size bytes of 256-byte lines."""
    line = b" " + b"x" * 255
    raw = b"tree 0\nmergetag object 0" + (b"\n" + line) * (size // 256) + b"\n\nclean\n"
    best = float("inf")
    for _ in range(repeats):
        started = time.perf_counter()
        fields, _ = git_push.split_object(raw, "commit[unit]")
        best = min(best, time.perf_counter() - started)
    assert len(fields[1][1]) == len(b"object 0") + (size // 256) * 256
    return best


def test_continuation_unfolding_is_linear_in_the_header_size():
    """Four times the continuation costs about four times as long (quadratic unfolding costs sixteen)."""
    small, large = _unfold_seconds(512 << 10), _unfold_seconds(2 << 20)
    assert large < 8 * small, (small, large)
    assert _unfold_seconds(8 << 20, repeats=1) < 5


# --- A clean push is ordinary: delivered unchanged, with Git's own bookkeeping ---


def test_clean_push_delivers_unchanged_with_tracking_refs_and_upstream(push_sandbox):
    sha = push_sandbox.commit("clean subject\n\nclean body")
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "clean release")
    tag = _git(push_sandbox.work, "rev-parse", "v1")
    result = push_sandbox.push("push", "-u", "--follow-tags", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    refs = push_sandbox.remote_refs()
    assert refs["refs/heads/feature"] == sha and refs["refs/tags/v1"] == tag
    assert _git(push_sandbox.work, "rev-parse", "refs/remotes/origin/feature") == sha
    assert _git(push_sandbox.work, "config", "branch.trunk.merge") == "refs/heads/feature"


def test_lease_and_forced_updates_keep_git_semantics(push_sandbox):
    first = push_sandbox.commit("clean one")
    assert push_sandbox.push("push", "origin", "trunk").returncode == 0
    _git(push_sandbox.work, "reset", "-q", "--hard", "HEAD~1")
    rewritten = push_sandbox.commit("clean rewrite")
    stale = push_sandbox.push("push", "--force-with-lease=trunk:" + ZERO[:39] + "1", "origin", "trunk")
    assert stale.returncode != 0 and push_sandbox.remote_refs()["refs/heads/trunk"] == first
    leased = push_sandbox.push("push", f"--force-with-lease=trunk:{first}", "origin", "trunk")
    assert leased.returncode == 0, leased.stderr
    assert push_sandbox.remote_refs()["refs/heads/trunk"] == rewritten


def test_deletion_publishes_no_text_and_needs_no_matcher(push_sandbox):
    _git(push_sandbox.work, "push", "-q", "origin", f"trunk:refs/heads/feature-{TOKEN}")
    shutil.rmtree(push_sandbox.tooling)
    result = push_sandbox.push("push", "origin", f":refs/heads/feature-{TOKEN}")
    assert result.returncode == 0, result.stderr
    assert f"refs/heads/feature-{TOKEN}" not in push_sandbox.remote_refs()


def test_missing_matcher_fails_closed(push_sandbox):
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean")
    shutil.rmtree(push_sandbox.tooling)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode != 0 and "private matcher or rules unavailable" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_override_is_logged_and_single_use(push_sandbox):
    push_sandbox.commit("subject " + TOKEN)
    first = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", LU_OPSEC_OVERRIDE="synthetic false positive")
    assert first.returncode == 0, first.stderr
    log = push_sandbox.root / "batch_state/opsec/overrides.jsonl"
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["rule_ids"] == ["synthetic-rule"]
    assert rows[0]["reason"] == "synthetic false positive" and TOKEN not in log.read_text()
    push_sandbox.commit("second " + TOKEN)
    again = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", LU_OPSEC_OVERRIDE="synthetic false positive")
    assert again.returncode != 0 and "override already consumed" in again.stderr


def test_an_overridden_hit_is_scanned_again_on_the_next_push(push_sandbox):
    sha = push_sandbox.commit("subject " + TOKEN)
    overridden = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", LU_OPSEC_OVERRIDE="synthetic reason")
    assert overridden.returncode == 0, overridden.stderr
    before = push_sandbox.remote_refs()
    again = push_sandbox.push("push", "origin", "HEAD:refs/heads/other")
    assert_blocked(again, push_sandbox, before, f"commit[{sha[:12]}].message")


def test_rules_update_refuses_a_commit_an_earlier_push_passed(push_sandbox):
    sha = push_sandbox.commit("subject LATER-SENSITIVE")
    assert push_sandbox.push("push", "origin", "HEAD:refs/heads/feature").returncode == 0
    (push_sandbox.tooling / "rules.json").write_text(json.dumps(synthetic_rules(pattern="LATER-SENSITIVE")))
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/other")
    assert result.returncode != 0 and f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


# --- The scanned ids are the sent ids; failures, malformed input and the deadline send nothing ---

SIDE_EFFECT_MATCHER = (
    MATCHER
    + """
import os, subprocess, time
_plain_scan = Matcher.scan
def _scan_with_side_effects(self, text):
    if os.environ.get("UNIT_SLOW"):
        time.sleep(float(os.environ["UNIT_SLOW"]))
    plan = os.environ.get("UNIT_MOVE")
    if plan and not os.path.exists(plan + ".done"):
        open(plan + ".done", "w").close()
        cwd, ref, target = open(plan).read().split()
        subprocess.run(["git", "-C", cwd, "update-ref", ref, target], check=True)
    return _plain_scan(self, text)
Matcher.scan = _scan_with_side_effects
"""
)


@pytest.fixture
def side_effects(push_sandbox):
    (push_sandbox.tooling / "matcher.py").write_text(SIDE_EFFECT_MATCHER)
    return push_sandbox


def test_ref_moved_to_a_hit_during_the_scan_is_not_sent(side_effects):
    scanned = side_effects.commit("clean subject")
    tree = _git(side_effects.work, "rev-parse", "HEAD^{tree}")
    hit = _git(side_effects.work, "commit-tree", tree, "-p", scanned, "-m", "subject " + TOKEN)
    plan = side_effects.tmp / "move"
    plan.write_text(f"{side_effects.work} refs/heads/trunk {hit}")
    result = side_effects.push("push", "origin", "trunk:refs/heads/feature", UNIT_MOVE=str(plan))
    assert result.returncode == 0, result.stderr
    # Positive control: trunk moved to the hit while the scan ran, so a re-resolved push would send it.
    assert (side_effects.tmp / "move.done").exists() and _git(side_effects.work, "rev-parse", "trunk") == hit
    assert side_effects.remote_refs()["refs/heads/feature"] == scanned and not _remote_has(side_effects, hit)


def test_ref_moved_away_from_a_hit_during_the_scan_is_still_refused(side_effects):
    base = _git(side_effects.work, "rev-parse", "HEAD")
    hit = side_effects.commit("subject " + TOKEN)
    plan = side_effects.tmp / "move"
    plan.write_text(f"{side_effects.work} refs/heads/trunk {base}")
    before = side_effects.remote_refs()
    result = side_effects.push("push", "origin", "trunk:refs/heads/feature", UNIT_MOVE=str(plan))
    assert_blocked(result, side_effects, before, f"commit[{hit[:12]}].message")


def test_scan_past_its_deadline_sends_nothing(side_effects):
    side_effects.commit("clean subject")
    before = side_effects.remote_refs()
    started = time.perf_counter()
    result = side_effects.push(
        "push", "origin", "HEAD:refs/heads/feature", UNIT_SLOW="30", LU_OPSEC_PUSH_SCAN_TIMEOUT="1"
    )
    assert result.returncode != 0 and "OPSEC: push scan timed out; push refused." in result.stderr, result.stderr
    assert time.perf_counter() - started < 20 and side_effects.remote_refs() == before


def test_slow_scan_within_its_deadline_delivers(side_effects):
    sha = side_effects.commit("clean subject")
    result = side_effects.push("push", "origin", "HEAD:refs/heads/feature", UNIT_SLOW="0.2")
    assert result.returncode == 0, result.stderr
    assert side_effects.remote_refs()["refs/heads/feature"] == sha


def test_scanner_error_sends_nothing(push_sandbox):
    """A scanner that cannot import fails the hook, and Git sends nothing."""
    push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    (push_sandbox.root / "scripts/opsec/prepublish.py").write_text("raise ImportError\n")
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode != 0 and push_sandbox.remote_refs() == before


class FakePublic:
    """The canonical public repository client seam: the default-branch head it reports."""

    def __init__(self, head, *, fail=False):
        self.head, self.fail = head, fail
        self.calls = 0

    def default_head(self):
        if self.fail:
            pytest.fail("the public repository must not be asked")
        self.calls += 1
        return self.head


def update(sandbox, revision="HEAD", ref="refs/heads/feature", old=ZERO):
    """One pre-push record as Git writes it for <revision>:<ref>."""
    return (revision, _git(sandbox.work, "rev-parse", revision), ref, old)


def run_hook(sandbox, monkeypatch, client, *updates, stdin=None, url=None, remote="origin", **extra):
    """git_push.main in process on hand-written pre-push input; returns (status, caller hook calls)."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setattr(gate, "private_tooling", lambda: sandbox.tooling)
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: sandbox.root)
    monkeypatch.chdir(sandbox.work)
    monkeypatch.setattr(os, "environ", _env(**extra))
    if stdin is None:
        stdin = "".join(" ".join(record) + "\n" for record in (updates or [update(sandbox)])).encode()
    chained = []

    def chain(arguments, data, environment):
        chained.append((arguments, data, environment))
        return 0

    status = git_push.main([remote, url or str(sandbox.remote)], stdin=stdin, public_repository=client, chain=chain)
    return status, chained


@pytest.mark.parametrize(
    "stdin",
    [
        pytest.param("HEAD {sha} refs/heads/feature {zero}", id="no-final-newline"),
        pytest.param("{sha} refs/heads/feature {zero}\n", id="three-fields"),
        pytest.param("HEAD {sha} refs/heads/feature {zero} extra\n", id="five-fields"),
        pytest.param("HEAD {short} refs/heads/feature {zero}\n", id="short-id"),
        pytest.param("HEAD {upper} refs/heads/feature {zero}\n", id="uppercase-id"),
        pytest.param("HEAD {sha} heads/feature {zero}\n", id="not-a-full-ref"),
        pytest.param("HEAD {sha} refs/heads/fea\tture {zero}\n", id="control-character"),
        pytest.param("(delete) {sha} refs/heads/feature {zero}\n", id="deletion-with-an-object"),
        pytest.param("HEAD {zero} refs/heads/feature {sha}\n", id="zero-id-without-deletion"),
        pytest.param("HEAD {sha} refs/heads/feature {zero}\n\n", id="empty-line"),
        pytest.param("HEAD {sha} refs/heads/clean {zero}\nHEAD {sha} refs/heads/feature\n", id="bad-last-record"),
    ],
)
def test_malformed_pre_push_input_refuses_and_runs_nothing(push_sandbox, monkeypatch, capfd, stdin):
    sha = _git(push_sandbox.work, "rev-parse", "HEAD")
    data = stdin.format(sha=sha, short=sha[:39], upper=sha.upper(), zero=ZERO).encode()
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None, fail=True), stdin=data)
    err = capfd.readouterr().err
    assert status == 1 and not chained and "OPSEC: pre-push input malformed; push refused." in err, err


def test_wrong_hook_arguments_refuse(push_sandbox, monkeypatch, capfd):
    monkeypatch.chdir(push_sandbox.work)
    assert git_push.main(["origin"], stdin=b"", chain=lambda *a: pytest.fail("ran")) == 1
    assert "arguments malformed" in capfd.readouterr().err


@pytest.mark.parametrize("value", ["0", "-1", "soon", "inf", "nan"])
def test_invalid_deadline_refuses(push_sandbox, monkeypatch, capfd, value):
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), LU_OPSEC_PUSH_SCAN_TIMEOUT=value)
    assert status == 1 and not chained and "LU_OPSEC_PUSH_SCAN_TIMEOUT" in capfd.readouterr().err


def test_empty_input_publishes_nothing_and_runs_the_caller_hook(push_sandbox, monkeypatch):
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None, fail=True), stdin=b"")
    assert status == 0 and chained[0][1] == b""


def test_local_ref_expressions_with_spaces_are_read_from_the_right(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("subject " + TOKEN)
    record = ("HEAD^{/subject " + TOKEN + "}", hit, "refs/heads/feature", ZERO)
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), record)
    err = capfd.readouterr().err
    assert status == 1 and not chained and f"field=commit[{hit[:12]}].message" in err, err


def test_objects_are_read_by_the_supplied_id_not_the_local_ref(push_sandbox, monkeypatch, capfd):
    """The local ref names a clean commit now; the id Git supplied is the one sent."""
    hit = push_sandbox.commit("subject " + TOKEN)
    _git(push_sandbox.work, "reset", "-q", "--hard", "HEAD~1")
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(None), ("trunk", hit, "refs/heads/feature", ZERO))
    assert status == 1 and f"field=commit[{hit[:12]}].message" in capfd.readouterr().err


def test_missing_object_refuses(push_sandbox, monkeypatch, capfd):
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), ("HEAD", "e" * 40, "refs/heads/x", ZERO))
    assert status == 1 and not chained and "push scan step git cat-file failed" in capfd.readouterr().err


def test_parse_updates_follows_the_object_format():
    sha256 = "a" * 64
    assert git_push.parse_updates(f"HEAD {sha256} refs/heads/x {'0' * 64}\n".encode(), 64) == [
        (b"HEAD", sha256, "refs/heads/x", "0" * 64)
    ]
    with pytest.raises(gate.PublishBlocked, match="malformed"):
        git_push.parse_updates(f"HEAD {sha256} refs/heads/x {'0' * 64}\n".encode(), 40)
    assert git_push.parse_updates(f"(delete) {ZERO} refs/heads/x {'b' * 40}\n".encode(), 40)[0][0] == b"(delete)"


def test_clean_hook_runs_the_caller_hook_with_the_same_input_and_no_override(push_sandbox, monkeypatch):
    push_sandbox.commit("clean subject")
    record = update(push_sandbox)
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), record, LU_OPSEC_OVERRIDE="reason")
    ((arguments, data, environment),) = chained
    assert status == 0 and arguments == ["origin", str(push_sandbox.remote)]
    assert data == (" ".join(record) + "\n").encode() and "LU_OPSEC_OVERRIDE" not in environment


UNKNOWN_PID = 2**31 - 1  # Above any pid_max: ps finds no such process, so the claimant lookup fails.


def test_clean_push_with_an_override_needs_no_claimant(push_sandbox, monkeypatch):
    """#9678: a clean push never looks up the claimant, so a failed lookup cannot refuse it."""
    push_sandbox.commit("clean subject")
    monkeypatch.setattr(git_push.os, "getppid", lambda: UNKNOWN_PID)
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), LU_OPSEC_OVERRIDE="reason")
    assert status == 0 and len(chained) == 1 and "LU_OPSEC_OVERRIDE" not in chained[0][2]
    assert not (push_sandbox.root / "batch_state/opsec").exists()


def test_flagged_push_with_a_failed_claimant_lookup_is_refused(push_sandbox, monkeypatch, capfd):
    push_sandbox.commit("subject " + TOKEN)
    monkeypatch.setattr(git_push.os, "getppid", lambda: UNKNOWN_PID)
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), LU_OPSEC_OVERRIDE="reason")
    err = capfd.readouterr().err
    assert status == 1 and not chained and "override log unavailable; push refused" in err, err
    assert not (push_sandbox.root / "batch_state/opsec/overrides.jsonl").exists()


def test_flagged_push_claims_and_logs_the_override_once(push_sandbox, monkeypatch, capfd):
    push_sandbox.commit("clean subject")
    push_sandbox.commit("subject " + TOKEN)
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), LU_OPSEC_OVERRIDE="reason")
    assert status == 0 and len(chained) == 1, capfd.readouterr().err
    log = push_sandbox.root / "batch_state/opsec/overrides.jsonl"
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["rule_ids"] == ["synthetic-rule"] and rows[0]["reason"] == "reason"
    again, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None), LU_OPSEC_OVERRIDE="reason")
    assert again == 1 and not chained and "override already consumed" in capfd.readouterr().err


# --- History already on the public default branch is excluded by its verified authoritative head ---

FETCH_HINT = "fetching the public default branch lets the scan skip history that is already public"


def test_hit_in_public_main_history_is_neither_refused_nor_scanned(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 0 and chained, err
    assert "1 commit(s) scanned; public default-branch head present (1 public repository call(s))" in err
    assert "OPSEC blocked" not in err and TOKEN not in err and hit[:12] not in err


def test_new_hit_on_top_of_public_main_is_refused(push_sandbox, monkeypatch, capfd):
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    client = FakePublic(public_head)
    status, chained = run_hook(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 1 and not chained and client.calls == 1
    assert f"OPSEC blocked: rule=synthetic-rule class=1 field=commit[{hit[:12]}].message line=1" in err
    assert TOKEN not in err and FETCH_HINT not in err


def test_many_published_hits_and_one_new_hit_refuse_only_the_new_one(push_sandbox, monkeypatch, capfd):
    published = [push_sandbox.commit(f"published {number} " + TOKEN) for number in range(30)]
    new = push_sandbox.commit("new subject " + TOKEN)
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(published[-1]))
    err = capfd.readouterr().err
    assert status == 1 and err.count("rule=synthetic-rule") == 1 and f"field=commit[{new[:12]}].message" in err
    assert "1 commit(s) scanned" in err


def test_absent_public_head_scans_all_history_and_names_the_fetch(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    push_sandbox.commit("new clean work")
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic("e" * 40))
    err = capfd.readouterr().err
    assert status == 1 and f"field=commit[{hit[:12]}].message" in err and FETCH_HINT in err
    assert "3 commit(s) scanned; public default-branch head absent here" in err and TOKEN not in err


def test_absent_public_head_hint_is_only_for_history_older_than_the_tips(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("subject " + TOKEN)
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic("e" * 40))
    err = capfd.readouterr().err
    assert status == 1 and f"field=commit[{hit[:12]}].message" in err and FETCH_HINT not in err


def test_history_the_destination_already_has_is_still_scanned(push_sandbox):
    """What the destination advertises is no evidence; only the canonical public head excludes commits."""
    old = push_sandbox.commit("old " + TOKEN)
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")  # Pushed without the scan.
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean follow-up")
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{old[:12]}].message")
    assert "public default-branch head unavailable (1 public repository call(s))" in result.stderr


def test_forged_tracking_ref_does_not_suppress_the_scan(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    for ref in ("refs/remotes/origin/feature", "refs/remotes/origin/main", "refs/heads/main"):
        _git(push_sandbox.work, "update-ref", ref, sha)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


def test_one_public_repository_call_per_push_and_none_without_commits(push_sandbox, monkeypatch, capfd):
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    push_sandbox.commit("clean one")
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "clean release")
    client = FakePublic(head)
    records = (update(push_sandbox, "HEAD", "refs/heads/a"), update(push_sandbox, "HEAD~1", "refs/heads/b"))
    status, _ = run_hook(push_sandbox, monkeypatch, client, *records, update(push_sandbox, "v1", "refs/tags/v1"))
    assert status == 0 and client.calls == 1, capfd.readouterr().err
    deletion = ("(delete)", ZERO, "refs/heads/gone", head)
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(None, fail=True), deletion)
    assert status == 0, capfd.readouterr().err


def test_ref_name_and_tag_text_are_scanned_even_when_the_commit_is_public(push_sandbox, monkeypatch, capfd):
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    status, _ = run_hook(
        push_sandbox, monkeypatch, FakePublic(head), update(push_sandbox, "HEAD", f"refs/heads/{TOKEN}")
    )
    assert status == 1 and "field=branch[1].name" in capfd.readouterr().err
    tag = _tag(push_sandbox.work, head, "commit", "v1", f"release {TOKEN}\n".encode())
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(head), (tag, tag, "refs/tags/v1", ZERO))
    err = capfd.readouterr().err
    assert status == 1 and f"field=tag[{tag[:12]}].message" in err and "0 commit(s) scanned" in err, err


def test_public_merge_is_excluded_with_its_embedded_tag_text(push_sandbox, monkeypatch, capfd):
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), f"v1-{TOKEN}"))
    push_sandbox.commit("new clean work")
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(merge))
    err = capfd.readouterr().err
    assert status == 0 and chained, err
    assert "1 commit(s) scanned" in err and TOKEN not in err and merge[:12] not in err


def test_new_merge_on_top_of_public_main_has_its_mergetag_text_scanned(push_sandbox, monkeypatch, capfd):
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD")
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), f"v1-{TOKEN}"))
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 1 and f"field=commit[{merge[:12]}].mergetag[1].tagname" in err and "2 commit(s) scanned" in err


def head_runner(reply, *, calls):
    """A gh transport answering only the typed default-head read; records (argv, kwargs, document)."""

    def run(argv, **kwargs):
        assert argv[:5] == ["gh", "api", "--method", "POST", "graphql"], argv
        calls.append((argv, kwargs, json.loads(Path(argv[argv.index("--input") + 1]).read_text())))
        return reply(argv)

    return run


def _reply(status, body):
    return lambda argv: subprocess.CompletedProcess(
        argv, status, body if isinstance(body, str) else json.dumps(body), ""
    )


def _timeout(argv):
    raise subprocess.TimeoutExpired(argv, git_push.API_TIMEOUT)


def _head_body(head, *, name="unit/public", branch="main"):
    return {
        "data": {"repository": {"nameWithOwner": name, "defaultBranchRef": {"name": branch, "target": {"oid": head}}}}
    }


@pytest.mark.parametrize(
    "reply",
    [
        pytest.param(lambda head: _reply(1, ""), id="api-failure"),
        pytest.param(lambda head: _timeout, id="timeout"),
        pytest.param(lambda head: _reply(1, {"message": "Not Found", "status": "404"}), id="not-found"),
        pytest.param(lambda head: _reply(1, {"message": "API rate limit exceeded", "status": "403"}), id="rate-limit"),
        pytest.param(lambda head: _reply(0, json.dumps(_head_body(head))[:-7]), id="truncated"),
        pytest.param(lambda head: _reply(0, [head]), id="malformed"),
        pytest.param(
            lambda head: _reply(
                0, {"data": {"repository": {"nameWithOwner": "unit/public", "defaultBranchRef": None}}}
            ),
            id="no-branch",
        ),
        pytest.param(lambda head: _reply(0, _head_body(head, name="unit/forged")), id="wrong-repository"),
        pytest.param(
            lambda head: _reply(
                0, {"data": {"repository": {"defaultBranchRef": {"name": "main", "target": {"oid": head}}}}}
            ),
            id="no-repository-identity",
        ),
        pytest.param(lambda head: _reply(0, _head_body(head, branch="release")), id="wrong-branch"),
        pytest.param(lambda head: _reply(0, _head_body("main")), id="non-hex"),
        pytest.param(lambda head: _reply(0, _head_body(head.upper())), id="uppercase-hex"),
        pytest.param(lambda head: _reply(0, _head_body(head + "0" * 24)), id="long-hex"),
        pytest.param(
            lambda head: _reply(0, {**_head_body(head), "errors": [{"message": "partial"}]}), id="graphql-errors"
        ),
        pytest.param(lambda head: _reply(1, _head_body(head)), id="failed-exit"),
    ],
)
def test_every_failed_or_unbound_head_reply_excludes_nothing(push_sandbox, monkeypatch, capfd, reply):
    hit = push_sandbox.commit("published subject " + TOKEN)
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    calls = []
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public", _env(), runner=head_runner(reply(public_head), calls=calls)
    )
    status, _ = run_hook(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 1 and f"field=commit[{hit[:12]}].message" in err, err
    assert "public default-branch head unavailable (1 public repository call(s))" in err
    assert len(calls) == 1 and calls[0][1]["timeout"] == git_push.API_TIMEOUT


def test_real_client_excludes_on_a_bound_reply_from_the_catalogue_repository(push_sandbox, monkeypatch, capfd):
    push_sandbox.commit("published subject " + TOKEN)
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    calls = []
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public",
        _env(GH_REPO="unit/forged", LU_OPSEC_OVERRIDE="x"),
        runner=head_runner(_reply(0, _head_body(public_head, name="Unit/Public")), calls=calls),
    )
    status, _ = run_hook(push_sandbox, monkeypatch, client)
    assert status == 0, capfd.readouterr().err
    ((_, kwargs, document),) = calls
    assert document["variables"] == {"owner": "unit", "name": "public"}
    assert "nameWithOwner" in document["query"] and "LU_OPSEC_OVERRIDE" not in kwargs["env"]


def test_the_default_client_names_the_catalogue_public_repository(monkeypatch):
    """Never the push URL, GH_REPO or local git configuration."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    client = git_push.CanonicalPublicRepository.from_catalog({"GH_REPO": "unit/forged", "LU_OPSEC_OVERRIDE": "x"})
    assert client.repo == "github.com/unit/public" and "LU_OPSEC_OVERRIDE" not in client.environment
    monkeypatch.setattr(gate, "catalog", lambda: {"private": CATALOG["infra-private"]})
    assert git_push.CanonicalPublicRepository.from_catalog({}) is None


def _loose(store, sha):
    return store / sha[:2] / sha[2:]


def _write_loose(store, sha, raw):
    path = _loose(store, sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(0o644)
    path.write_bytes(zlib.compress(b"commit %d\0" % len(raw) + raw))


@pytest.mark.parametrize("store", ["own", "alternate"])
def test_altered_public_history_bytes_exclude_nothing(push_sandbox, monkeypatch, capfd, tmp_path, store):
    """Bytes under the authoritative head's id that name the hit as a parent must not hide the hit."""
    public_head = push_sandbox.commit("published clean")
    hit = push_sandbox.commit("subject " + TOKEN)
    genuine = subprocess.run(
        [REAL_GIT, "cat-file", "commit", public_head],
        cwd=push_sandbox.work,
        env=_env(),
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    forged = re.sub(rb"\nparent [0-9a-f]{40}\n", f"\nparent {hit}\n".encode(), genuine, count=1)
    objects = push_sandbox.work / ".git/objects"
    if store == "own":
        _write_loose(objects, public_head, forged)
    else:
        alternate = tmp_path / "alternate/objects"
        _write_loose(alternate, public_head, forged)
        _loose(objects, public_head).unlink()
        (objects / "info/alternates").write_text(f"{alternate}\n")
    # Positive control: git trusts the stored bytes and would exclude the hit.
    assert _git(push_sandbox.work, "rev-list", hit, f"^{public_head}") == ""
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 1 and f"field=commit[{hit[:12]}].message" in err, err
    assert "public default-branch head unverified here" in err and FETCH_HINT not in err


def test_history_verification_reads_every_public_commit(push_sandbox, monkeypatch):
    """A missing ancestor of the public head leaves its history unverified, so nothing is excluded."""
    root = _git(push_sandbox.work, "rev-parse", "HEAD")
    public_head = push_sandbox.commit("published clean")
    repository = git_push.Repository(REAL_GIT, _env())
    monkeypatch.chdir(push_sandbox.work)
    assert git_push.history_verified(repository, public_head, "sha1")
    _loose(push_sandbox.work / ".git/objects", root).unlink()
    assert not git_push.history_verified(repository, public_head, "sha1")


def _forge_commit_graph(work, child, parent):
    """Rewrite the commit-graph so child's first parent is parent, with a valid trailing checksum."""
    _git(work, "commit-graph", "write", "--reachable", "--no-progress")
    path = work / ".git/objects/info/commit-graph"
    data = bytearray(path.read_bytes())
    assert data[:4] == b"CGPH" and data[5] == 1  # Version 1 with SHA-1 ids.
    chunks = {
        bytes(data[8 + 12 * n : 12 + 12 * n]): int.from_bytes(data[12 + 12 * n : 20 + 12 * n], "big")
        for n in range(data[6])
    }
    count = int.from_bytes(data[chunks[b"OIDF"] + 255 * 4 : chunks[b"OIDF"] + 256 * 4], "big")
    ids = [bytes(data[chunks[b"OIDL"] + 20 * n : chunks[b"OIDL"] + 20 * n + 20]).hex() for n in range(count)]
    entry = chunks[b"CDAT"] + ids.index(child) * 36
    data[entry + 20 : entry + 24] = ids.index(parent).to_bytes(4, "big")
    data[-20:] = hashlib.sha1(bytes(data[:-20])).digest()
    path.chmod(0o644)
    path.write_bytes(bytes(data))


@pytest.mark.parametrize("helper", ["commit-graph", "replace"])
def test_local_parent_data_cannot_place_a_hit_inside_the_public_history(push_sandbox, monkeypatch, capfd, helper):
    """Only parents recorded in the hashed commits decide ancestry: no commit-graph or replacement object."""
    hit = push_sandbox.commit("subject " + TOKEN)
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD~1")
    if helper == "replace":
        tree = _git(push_sandbox.work, "rev-parse", f"{public_head}^{{tree}}")
        forged = _git(push_sandbox.work, "commit-tree", tree, "-p", hit, "-m", "clean base")
        _git(push_sandbox.work, "replace", public_head, forged)
    else:
        _forge_commit_graph(push_sandbox.work, public_head, hit)
    # Positive control: plain git, honouring the forged data, would exclude the hit.
    assert _git(push_sandbox.work, "rev-list", hit, f"^{public_head}") == ""
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(public_head))
    assert status == 1 and f"field=commit[{hit[:12]}].message" in capfd.readouterr().err


@pytest.mark.parametrize("extra", [(), ("-c", "core.useReplaceRefs=true")])
def test_replacement_object_does_not_hide_the_sent_commit(push_sandbox, extra):
    """git replace changes what readers see but not what the pack sends; scan the sent object."""
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    tree, parent = _git(push_sandbox.work, "rev-parse", "HEAD^{tree}", "HEAD^").split()
    clean = _git(push_sandbox.work, "commit-tree", tree, "-p", parent, "-m", "clean replacement")
    _git(push_sandbox.work, "replace", sha, clean)
    result = push_sandbox.push(*extra, "push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


@pytest.mark.parametrize("via_environment", [False, True])
def test_grafted_history_is_refused(push_sandbox, tmp_path, via_environment):
    """A graft hides a hit ancestor that the destination already holds as an unreferenced object."""
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    clean = push_sandbox.commit("clean follow-up")
    _git(push_sandbox.work, "push", "-q", "origin", f"{hit}:refs/heads/seed")
    _git(push_sandbox.work, "push", "-q", "origin", ":refs/heads/seed")  # Object stays, ref goes.
    before = push_sandbox.remote_refs()
    graft = tmp_path / "grafts" if via_environment else push_sandbox.work / ".git/info/grafts"
    graft.parent.mkdir(exist_ok=True)
    graft.write_text(f"{clean} {base}\n")
    extra = {"GIT_GRAFT_FILE": str(graft)} if via_environment else {}
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", **extra)
    assert result.returncode != 0 and "OPSEC: grafted history present; push refused." in result.stderr, result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before


def test_git_tracing_never_records_the_scan(push_sandbox, monkeypatch, tmp_path):
    """Caller tracing (environment or config) must not log the scan's own git calls."""
    push_sandbox.commit("clean subject")
    logs = {
        name: tmp_path / f"{name}.log" for name in ("GIT_TRACE", "GIT_TRACE_PACKET", "GIT_TRACE2", "GIT_TRACE2_EVENT")
    }
    config = tmp_path / "trace.gitconfig"
    config.write_text(f"[trace2]\n\tperfTarget = {tmp_path / 'config-perf.log'}\n")
    status, _ = run_hook(
        push_sandbox,
        monkeypatch,
        FakePublic(None),
        **{name: str(path) for name, path in logs.items()},
        GIT_CONFIG_GLOBAL=str(config),
        GIT_CURL_VERBOSE="1",
    )
    assert status == 0
    written = {path.name: path.read_text() for path in [*logs.values(), tmp_path / "config-perf.log"] if path.exists()}
    assert all(text == "" for text in written.values()), sorted(written)


# --- Shallow boundaries: refused only inside the scan set ---

SHALLOW_REFUSAL = "OPSEC: shallow boundary inside the scanned range"


def _orphan(cwd, message):
    """A parentless commit object no ref names."""
    return _git(cwd, "commit-tree", _git(cwd, "rev-parse", "HEAD^{tree}"), "-m", message)


def _shallow(work, *commits):
    """Mark commits as shallow boundaries, as a shallow clone (or a forger) would."""
    (work / ".git/shallow").write_text("".join(f"{sha}\n" for sha in commits))


def test_real_shallow_clone_with_its_boundary_pushed_is_refused(push_sandbox, tmp_path):
    push_sandbox.commit("subject " + TOKEN)
    push_sandbox.commit("clean follow-up")
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "1", f"file://{push_sandbox.remote}", str(shallow), "-b", "trunk")
    boundary = _git(shallow, "rev-parse", "HEAD")
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", cwd=shallow)
    assert result.returncode != 0 and f"{SHALLOW_REFUSAL} (commit[{boundary[:12]}])" in result.stderr, result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before


def test_boundaries_outside_the_scan_set_do_not_refuse_a_clean_push(push_sandbox):
    _shallow(
        push_sandbox.work, _orphan(push_sandbox.work, "unrelated one"), _orphan(push_sandbox.work, "unrelated two")
    )
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert "2 commit(s) scanned" in result.stderr and push_sandbox.remote_refs()["refs/heads/feature"] == sha


def test_boundary_inside_the_excluded_public_history_hides_only_public_history(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    boundary = push_sandbox.commit("published clean one")
    public_head = push_sandbox.commit("published clean two")
    push_sandbox.commit("new clean work")
    _shallow(push_sandbox.work, boundary)
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 0 and chained and "1 commit(s) scanned" in err and hit[:12] not in err, err


def test_forged_boundary_on_a_new_commit_hiding_a_hit_is_refused(push_sandbox, monkeypatch, capfd):
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    forged = push_sandbox.commit("clean cover")
    tip = push_sandbox.commit("clean tip")
    _shallow(push_sandbox.work, forged)
    # Positive control: git honours the forged entry and no longer walks to the hit.
    assert _git(push_sandbox.work, "rev-list", tip, f"^{public_head}").split() == [tip, forged]
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 1 and f"{SHALLOW_REFUSAL} (commit[{forged[:12]}])" in err and hit[:12] not in err, err


@pytest.mark.parametrize("forged", [["head"], ["middle"], ["base"], ["base", "middle", "head"]])
def test_forged_boundary_in_public_history_cannot_shrink_the_scan_set(push_sandbox, monkeypatch, capfd, forged):
    commits = {"base": _git(push_sandbox.work, "rev-parse", "HEAD")}
    commits["middle"] = push_sandbox.commit("published clean one")
    commits["head"] = push_sandbox.commit("published clean two")
    hit = push_sandbox.commit("new subject " + TOKEN)
    _shallow(push_sandbox.work, *(commits[name] for name in forged))
    status, _ = run_hook(push_sandbox, monkeypatch, FakePublic(commits["head"]))
    assert status == 1 and f"field=commit[{hit[:12]}].message" in capfd.readouterr().err


@pytest.mark.parametrize(
    "content", ["{sha}\n\n", "{sha}\r\n", "{short}\n", "not an id\n", "{sha} trailing\n", "{upper}\n"]
)
def test_malformed_shallow_file_is_refused(push_sandbox, monkeypatch, capfd, content):
    sha = _orphan(push_sandbox.work, "unrelated")
    push_sandbox.commit("clean subject")
    (push_sandbox.work / ".git/shallow").write_text(content.format(sha=sha, short=sha[:39], upper=sha.upper()))
    status, chained = run_hook(push_sandbox, monkeypatch, FakePublic(None))
    err = capfd.readouterr().err
    assert status == 1 and not chained and "OPSEC: shallow file malformed; push refused." in err, err


def test_shallow_boundaries_reader(tmp_path):
    path = tmp_path / "shallow"
    assert git_push.shallow_boundaries(str(path), 40) == set()
    path.write_text("")
    assert git_push.shallow_boundaries(str(path), 40) == set()
    path.write_text(f"{'a' * 40}\n{'b' * 40}")
    assert git_push.shallow_boundaries(str(path), 40) == {"a" * 40, "b" * 40}
    with pytest.raises(gate.PublishBlocked, match="shallow file malformed"):
        git_push.shallow_boundaries(str(path), 64)
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(gate.PublishBlocked, match="shallow file unreadable"):
        git_push.shallow_boundaries(str(fifo), 40)
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(gate.PublishBlocked, match="shallow file unreadable"):
        git_push.shallow_boundaries(str(directory), 40)


def test_linked_worktree_reads_the_shared_shallow_file(push_sandbox, tmp_path):
    linked = tmp_path / "linked"
    _git(push_sandbox.work, "worktree", "add", "-q", "-b", "linked", str(linked))
    (linked / "file.txt").write_text("linked\n")
    _git(linked, "commit", "-q", "-am", "clean linked work")
    boundary = _git(linked, "rev-parse", "HEAD")
    _shallow(push_sandbox.work, boundary)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", cwd=linked)
    assert result.returncode != 0 and f"{SHALLOW_REFUSAL} (commit[{boundary[:12]}])" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_alternate_shallow_file_option_is_refused(push_sandbox):
    push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("--shallow-file", os.devnull, "push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and "--shallow-file is not supported for a scanned push" in result.stderr
    assert push_sandbox.remote_refs() == before


def test_shallow_file_environment_variable_is_refused(push_sandbox, tmp_path):
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    cover = push_sandbox.commit("clean cover")
    alternate = tmp_path / "alternate-shallow"
    alternate.write_text(f"{cover}\n")
    # Positive control: git honours the variable and no longer walks to the hit.
    walked = _git(push_sandbox.work, "rev-list", cover, f"^{base}", env=_env(GIT_SHALLOW_FILE=str(alternate)))
    assert walked.split() == [cover] and hit not in walked
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", GIT_SHALLOW_FILE=str(alternate))
    assert result.returncode != 0 and "GIT_SHALLOW_FILE is not supported" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


# --- Every configuration route to the hooks path runs the scanner ---

PERMISSIVE_HOOK = "#!/bin/sh\ncat >/dev/null\nexit 0\n"


@pytest.fixture
def permissive_hooks(push_sandbox):
    """A hooks directory whose pre-push allows everything: what a redirected hooks path would run."""
    directory = push_sandbox.tmp / "permissive-hooks"
    directory.mkdir()
    (directory / "pre-push").write_text(PERMISSIVE_HOOK)
    (directory / "pre-push").chmod(0o755)
    return directory


def _route(sandbox, hooks, route):
    """(global options, environment) that set core.hooksPath to hooks by one configuration route."""
    if route == "command-line":
        return ["-c", f"core.hooksPath={hooks}"], {}
    if route == "command-line-key-case":
        return ["-c", f"CORE.HOOKSPATH={hooks}"], {}
    if route == "config-env":
        return ["--config-env", "core.hooksPath=UNIT_HOOKS"], {"UNIT_HOOKS": str(hooks)}
    if route == "config-env-equals":
        return ["--config-env=core.hooksPath=UNIT_HOOKS"], {"UNIT_HOOKS": str(hooks)}
    if route == "parameters":
        return [], {"GIT_CONFIG_PARAMETERS": f"'core.hooksPath'='{hooks}'"}
    if route == "count":
        return [], {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": str(hooks)}
    if route in ("repository", "worktree"):
        if route == "worktree":
            _git(sandbox.work, "config", "extensions.worktreeConfig", "true")
        _git(sandbox.work, "config", f"--{route.replace('repository', 'local')}", "core.hooksPath", str(hooks))
        return [], {}
    if route == "include":
        included = sandbox.tmp / "included.gitconfig"
        included.write_text(f"[core]\n\thooksPath = {hooks}\n")
        _git(sandbox.work, "config", "include.path", str(included))
        return [], {}
    global_config = sandbox.tmp / "global.gitconfig"
    global_config.write_text(f"[core]\n\thooksPath = {hooks}\n")
    return [], {"GIT_CONFIG_GLOBAL": str(global_config)}


ROUTES = [
    "command-line",
    "command-line-key-case",
    "config-env",
    "config-env-equals",
    "parameters",
    "count",
    "repository",
    "worktree",
    "include",
    "global",
]


@pytest.mark.parametrize("route", ROUTES)
def test_every_hooks_path_route_still_runs_the_scanner(push_sandbox, permissive_hooks, route):
    options, environment = _route(push_sandbox, permissive_hooks, route)
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push(*options, "push", "origin", "HEAD:refs/heads/feature", **environment)
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


@pytest.mark.parametrize("route", ROUTES)
def test_each_hooks_path_route_really_redirects_plain_git(push_sandbox, permissive_hooks, route):
    """Control: without the shim the same route runs the permissive hook and the hit is sent."""
    options, environment = _route(push_sandbox, permissive_hooks, route)
    sha = push_sandbox.commit("subject " + TOKEN)
    result = subprocess.run(
        [REAL_GIT, *options, "push", "origin", "HEAD:refs/heads/feature"],
        cwd=push_sandbox.work,
        env=_env(**environment),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


# --- Pushes that would skip the hook, or whose scanner is unusable, are refused ---

NO_VERIFY = ["--no-verify", "--no-verif", "--no-veri"]


@pytest.mark.parametrize("spelling", NO_VERIFY)
def test_each_no_verify_spelling_really_skips_the_hook_in_plain_git(push_sandbox, permissive_hooks, spelling):
    """Control: Git accepts these spellings and then runs no pre-push hook at all."""
    marker = push_sandbox.tmp / "ran"
    (permissive_hooks / "pre-push").write_text(f"#!/bin/sh\ntouch {marker}\nexit 1\n")
    result = subprocess.run(
        [REAL_GIT, "-c", f"core.hooksPath={permissive_hooks}", "push", spelling, "origin", "HEAD:refs/heads/x"],
        cwd=push_sandbox.work,
        env=_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0 and not marker.exists(), result.stderr


@pytest.mark.parametrize("spelling", [*NO_VERIFY, "--no-ver", "--no-v", "--no", "--n"])
@pytest.mark.parametrize("position", ["first", "middle", "last", "after-separator"])
def test_no_verify_in_any_spelling_and_position_is_refused(push_sandbox, spelling, position):
    push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    args = {
        "first": [spelling, "origin", "HEAD:refs/heads/feature"],
        "middle": ["origin", spelling, "HEAD:refs/heads/feature"],
        "last": ["origin", "HEAD:refs/heads/feature", spelling],
        "after-separator": ["origin", "--", "HEAD:refs/heads/feature", spelling],
    }[position]
    result = push_sandbox.push("push", *args)
    assert result.returncode == 2 and "--no-verify would skip the push scan" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


@pytest.mark.parametrize("args", [["--verify"], ["--no-verbose"], ["--no-atomic"], ["-q"]])
def test_options_that_keep_the_hook_are_not_refused(push_sandbox, args):
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("push", *args, "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


# --- Only Git's own commands run; every alias is refused before Git runs ---


def _chain(length):
    """publish -> a1 -> ... -> push: length expansions in all."""
    names = ["publish", *(f"a{index}" for index in range(1, length))]
    return {name: names[index + 1] if index + 1 < length else "push" for index, name in enumerate(names)}


# Each alias reaches push in plain Git (control below), most of them past the hook.
ALIASES = {
    "ordinary": {"publish": "push"},
    "carriage-return-no-verify": {"publish": "push\r--no-verify"},
    "carriage-return-quiet": {"publish": "push\r--quiet"},
    "no-verify": {"publish": "push --no-verify"},
    "quoted-no-verify": {"publish": "push '--no-'verify"},
    "nested": {"publish": "quiet", "quiet": "push -q --no-veri"},
    "chain-of-17": _chain(17),
    "alias-defined-alias": {"publish": "-c alias.send=push send"},
    "config-env-alias": {"publish": "--config-env=alias.send=UNIT_ALIAS send"},
    "hooks-path": {"publish": "--config-env=core.hooksPath=UNIT_HOOKS push"},
    "shell": {"publish": "!git push"},
    "loop": {"publish": "pong", "pong": "publish"},
}


def _configure(sandbox, aliases, scope):
    """Global options that define aliases by the scope's configuration route."""
    options = []
    for name, value in aliases.items():
        if scope == "repository":
            _git(sandbox.work, "config", f"alias.{name}", value)
        else:
            options += ["-c", f"alias.{name}={value}"]
    return options


def _alias_environment(sandbox):
    return {"UNIT_ALIAS": "push", "UNIT_HOOKS": str(sandbox.tmp / "no-hooks")}


def assert_not_a_git_command(result, sandbox, before, sha, name):
    assert result.returncode == 2, result.stderr
    assert f"OPSEC: '{name}' is not one of Git's own commands, so it was not run." in result.stderr, result.stderr
    assert "Run the Git command directly" in result.stderr, result.stderr
    assert sandbox.remote_refs() == before and not _remote_has(sandbox, sha)


@pytest.mark.parametrize("shape", ALIASES)
@pytest.mark.parametrize("scope", ["repository", "command-line"])
def test_every_alias_is_refused_with_nothing_sent(push_sandbox, shape, scope):
    options = _configure(push_sandbox, ALIASES[shape], scope)
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push(
        *options, "publish", "origin", "HEAD:refs/heads/feature", **_alias_environment(push_sandbox)
    )
    assert_not_a_git_command(result, push_sandbox, before, sha, "publish")


@pytest.mark.parametrize("shape", [shape for shape in ALIASES if shape != "loop"])
@pytest.mark.parametrize("scope", ["repository", "command-line"])
def test_each_alias_really_pushes_in_plain_git(push_sandbox, shape, scope):
    """Control: without the shim Git expands the alias to a push and the hit is sent."""
    options = _configure(push_sandbox, ALIASES[shape], scope)
    sha = push_sandbox.commit("subject " + TOKEN)
    result = subprocess.run(
        [REAL_GIT, *options, "publish", "origin", "HEAD:refs/heads/feature"],
        cwd=push_sandbox.work,
        env=_env(**_alias_environment(push_sandbox)),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


def test_alias_that_runs_no_push_is_refused_too(push_sandbox):
    _git(push_sandbox.work, "config", "alias.where", "rev-parse --show-toplevel")
    result = push_sandbox.push("where")
    assert result.returncode == 2 and "'where' is not one of Git's own commands" in result.stderr, result.stderr
    assert result.stdout == ""


def test_git_commands_run_unchanged(push_sandbox):
    sha = push_sandbox.commit("clean subject")
    _git(push_sandbox.work, "config", "alias.where", "rev-parse")  # Aliases of other names do not matter.
    status = push_sandbox.push("status", "--short")
    assert status.returncode == 0 and status.stderr == "", status.stderr
    log = push_sandbox.push("-c", "color.ui=never", "log", "--format=%H", "-1")
    assert log.returncode == 0 and log.stdout.strip() == sha, log.stderr
    # A git-<name> program in Git's exec path is one of Git's own commands.
    submodule = push_sandbox.push("submodule", "status")
    assert submodule.returncode == 0 and "OPSEC" not in submodule.stderr, submodule.stderr
    assert "refs/heads/feature" not in push_sandbox.remote_refs()


# --- A listed command is refused while an alias of its name exists ---


def assert_alias_refused(result, sandbox, before, sha, name):
    assert result.returncode == 2, result.stderr
    assert f"OPSEC: an alias named '{name}' is defined, so '{name}' was not run." in result.stderr, result.stderr
    assert sandbox.remote_refs() == before and not _remote_has(sandbox, sha)


def _plain(sandbox, *args, **extra):
    return subprocess.run(
        [REAL_GIT, *args], cwd=sandbox.work, env=_env(**extra), capture_output=True, text=True, timeout=60
    )


PUSH_ALIASES = ["push --no-verify", "push --quiet"]


@pytest.mark.parametrize("value", PUSH_ALIASES)
@pytest.mark.parametrize("scope", ["repository", "command-line"])
def test_alias_over_a_deprecated_builtin_is_refused(push_sandbox, value, scope):
    """Git looks an alias up before a deprecated builtin, so the alias pushes in place of whatchanged."""
    assert "whatchanged" in _git(push_sandbox.work, "--list-cmds=builtins,main").split()
    options = _configure(push_sandbox, {"whatchanged": value}, scope)
    pushing = [*options, "whatchanged", "origin", "HEAD:refs/heads/feature"]
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    assert_alias_refused(push_sandbox.push(*pushing), push_sandbox, before, sha, "whatchanged")
    control = _plain(push_sandbox, *pushing)
    assert control.returncode == 0, control.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


@pytest.mark.parametrize("route", ["option", "environment"])
@pytest.mark.parametrize("value", PUSH_ALIASES)
@pytest.mark.parametrize("scope", ["repository", "command-line"])
def test_alias_behind_a_program_that_cannot_start_is_refused(push_sandbox, route, value, scope):
    """A listed git-publish whose interpreter is missing fails to start; Git then expands alias.publish."""
    exec_path = push_sandbox.tmp / "exec-path"
    marker = push_sandbox.tmp / "ran"
    _program(exec_path, "publish", marker, interpreter=push_sandbox.tmp / "absent-interpreter")
    paths, environment = (
        ([f"--exec-path={exec_path}"], {}) if route == "option" else ([], {"GIT_EXEC_PATH": str(exec_path)})
    )
    assert "publish" in _git(push_sandbox.work, *paths, "--list-cmds=builtins,main", env=_env(**environment)).split()
    options = _configure(push_sandbox, {"publish": value}, scope)
    pushing = [*paths, *options, "publish", "origin", "HEAD:refs/heads/feature"]
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    assert_alias_refused(push_sandbox.push(*pushing, **environment), push_sandbox, before, sha, "publish")
    control = _plain(push_sandbox, *pushing, **environment)
    assert control.returncode == 0, control.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha and not marker.exists()


def _alias_source(sandbox, source, value):
    """Defines alias.whatchanged by one configuration route; returns (global options, environment)."""
    defining = sandbox.tmp / "aliases.gitconfig"
    _git(sandbox.tmp, "config", "--file", str(defining), "alias.whatchanged", value)
    if source == "system":
        return [], {"GIT_CONFIG_NOSYSTEM": "0", "GIT_CONFIG_SYSTEM": str(defining)}
    if source == "global":
        return [], {"GIT_CONFIG_GLOBAL": str(defining)}
    if source == "worktree":
        _git(sandbox.work, "config", "extensions.worktreeConfig", "true")
        _git(sandbox.work, "config", "--worktree", "alias.whatchanged", value)
        return [], {}
    if source == "include":
        _git(sandbox.work, "config", "include.path", str(defining))
        return [], {}
    if source == "conditional include":
        _git(sandbox.work, "config", f"includeIf.gitdir:{sandbox.work}/.git.path", str(defining))
        return [], {}
    if source == "upper-case command line":
        return ["-c", f"alias.WhatChanged={value}"], {}
    if source == "config-env":
        return ["--config-env=alias.whatchanged=UNIT_ALIAS"], {"UNIT_ALIAS": value}
    if source == "GIT_CONFIG_PARAMETERS":
        return [], {"GIT_CONFIG_PARAMETERS": f"'alias.whatchanged'='{value}'"}
    if source == "GIT_CONFIG_COUNT":
        return [], {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "alias.whatchanged", "GIT_CONFIG_VALUE_0": value}
    assert source == "GIT_CONFIG narrowing", source  # GIT_CONFIG narrows `git config`, not Git's alias lookup.
    _git(sandbox.work, "config", "alias.whatchanged", value)
    return [], {"GIT_CONFIG": os.devnull}


ALIAS_SOURCES = [
    "system",
    "global",
    "worktree",
    "include",
    "conditional include",
    "upper-case command line",
    "config-env",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG narrowing",
]


@pytest.mark.parametrize("source", ALIAS_SOURCES)
def test_alias_is_found_in_every_configuration_source(push_sandbox, source):
    options, environment = _alias_source(push_sandbox, source, "push --no-verify")
    pushing = [*options, "whatchanged", "origin", "HEAD:refs/heads/feature"]
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    assert_alias_refused(push_sandbox.push(*pushing, **environment), push_sandbox, before, sha, "whatchanged")
    if source == "worktree":
        return  # Git 2.53 looks aliases up without the worktree file; the shim refuses them all the same.
    control = _plain(push_sandbox, *pushing, **environment)
    assert control.returncode == 0, control.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


@pytest.mark.parametrize(
    ("options", "name"),
    [
        (["-c", "alias.status=push"], "status"),  # Git runs the builtin here, but the alias is refused all the same.
        (["-c", "alias.push=status"], "push"),
        (["-c", "alias.submodule=push"], "submodule"),  # over a git-<name> program in Git's exec path
    ],
)
def test_alias_over_any_listed_name_is_refused(push_sandbox, options, name):
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push(*options, name, "origin", "HEAD:refs/heads/feature")
    assert_alias_refused(result, push_sandbox, before, sha, name)


def test_failed_alias_lookup_refuses(push_sandbox):
    """A configuration Git cannot read leaves the aliases unknown (push skips the command list)."""
    (push_sandbox.tmp / "broken.gitconfig").write_text("[alias\n")
    sha = push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    pushing = ["push", "origin", "HEAD:refs/heads/feature"]
    result = push_sandbox.push(*pushing, GIT_CONFIG_GLOBAL=str(push_sandbox.tmp / "broken.gitconfig"))
    assert result.returncode == 2, result.stderr
    assert "OPSEC: could not check Git's aliases for 'push', so it was not run." in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before and not _remote_has(push_sandbox, sha)


def test_alias_lookup_that_hangs_refuses_after_its_time_limit(push_sandbox):
    """An include file that never delivers (a FIFO with no writer) holds Git's read open."""
    fifo = push_sandbox.tmp / "never-written"
    os.mkfifo(fifo)
    sha = push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    started = time.perf_counter()
    result = push_sandbox.push("-c", f"include.path={fifo}", "push", "origin", "HEAD:refs/heads/feature")
    assert 9 < time.perf_counter() - started < 60
    assert result.returncode == 2, result.stderr
    assert "OPSEC: could not check Git's aliases for 'push', so it was not run." in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before and not _remote_has(push_sandbox, sha)


def test_alias_lookup_latency_is_reported(push_sandbox):
    """Prints the added time of one `git status` through the shim (median of seven)."""
    times = {"shim": [], "plain": []}
    for _ in range(7):
        for kind in times:
            argv = [str(push_sandbox.shim) if kind == "shim" else REAL_GIT, "status", "--short"]
            started = time.perf_counter()
            subprocess.run(argv, cwd=push_sandbox.work, env=_env(), check=True, capture_output=True, timeout=60)
            times[kind].append(time.perf_counter() - started)
    shim, plain = (sorted(values)[3] for values in times.values())
    print(f"git status: plain git {plain:.3f}s, through the shim {shim:.3f}s, added {shim - plain:.3f}s")
    assert shim - plain < 5


def test_direct_push_still_scans_and_delivers(push_sandbox):
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    assert_blocked(
        push_sandbox.push("push", "origin", "HEAD:refs/heads/feature"),
        push_sandbox,
        before,
        f"commit[{sha[:12]}].message",
    )
    (push_sandbox.tooling / "rules.json").write_text(json.dumps(synthetic_rules(pattern="NEVER-PRESENT")))
    clean = push_sandbox.commit("clean follow-up")
    assert push_sandbox.push("push", "origin", "HEAD:refs/heads/feature").returncode == 0
    assert push_sandbox.remote_refs()["refs/heads/feature"] == clean


def _program(directory, name, marker, interpreter="/bin/sh"):
    directory.mkdir(exist_ok=True)
    program = directory / f"git-{name}"
    program.write_text(f"#!{interpreter}\ntouch {marker}\n")
    program.chmod(0o755)


def test_git_program_outside_the_exec_path_is_refused(push_sandbox):
    marker = push_sandbox.tmp / "ran"
    _program(push_sandbox.tmp / "bin", "publish", marker)
    path = os.pathsep.join([str(push_sandbox.tmp / "bin"), _env()["PATH"]])
    result = push_sandbox.push("publish", PATH=path)
    assert result.returncode == 2 and "'publish' is not one of Git's own commands" in result.stderr, result.stderr
    assert not marker.exists()
    control = subprocess.run([REAL_GIT, "publish"], cwd=push_sandbox.work, env=_env(PATH=path), timeout=60)
    assert control.returncode == 0 and marker.exists()


@pytest.mark.parametrize("route", ["option", "environment"])
def test_commands_are_listed_from_the_callers_exec_path(push_sandbox, route):
    """Under another exec path git-submodule is gone and Git would expand alias.submodule instead."""
    exec_path = push_sandbox.tmp / "exec-path"
    marker = push_sandbox.tmp / "ran"
    _program(exec_path, "unit", marker)
    options, environment = (
        ([f"--exec-path={exec_path}"], {}) if route == "option" else ([], {"GIT_EXEC_PATH": str(exec_path)})
    )
    assert push_sandbox.push(*options, "unit", **environment).returncode == 0 and marker.exists()
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    pushing = [*options, "-c", "alias.submodule=push", "submodule", "origin", "HEAD:refs/heads/feature"]
    assert_not_a_git_command(push_sandbox.push(*pushing, **environment), push_sandbox, before, sha, "submodule")
    control = subprocess.run(
        [REAL_GIT, *pushing], cwd=push_sandbox.work, env=_env(**environment), capture_output=True, text=True, timeout=60
    )
    assert control.returncode == 0, control.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


def test_mistyped_command_is_refused_before_autocorrect(push_sandbox):
    sha = push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("-c", "help.autocorrect=immediate", "psuh", "origin", "HEAD:refs/heads/feature")
    assert_not_a_git_command(result, push_sandbox, before, sha, "psuh")


def test_command_with_a_line_break_is_refused(push_sandbox):
    """A name spanning two listed commands is no command."""
    result = push_sandbox.push("add\nam")
    assert result.returncode == 2 and "is not one of Git's own commands" in result.stderr, result.stderr


def test_unlistable_commands_refuse(push_sandbox):
    result = push_sandbox.push("-C", str(push_sandbox.tmp / "absent"), "status")
    assert result.returncode == 2 and "could not list Git's commands" in result.stderr, result.stderr


# --- A push whose scanner is unusable is refused ---


@pytest.mark.parametrize("damage", ["remove-hook", "unexecutable-hook", "remove-chain", "remove-scanner"])
def test_unusable_scanner_refuses_before_git_runs(push_sandbox, damage):
    push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    hooks = push_sandbox.root / "scripts/opsec/push_hooks"
    if damage == "remove-hook":
        (hooks / "pre-push").unlink()
    elif damage == "unexecutable-hook":
        (hooks / "pre-push").chmod(0o644)
    elif damage == "remove-chain":
        (hooks / "chain").unlink()
    else:
        (push_sandbox.root / "scripts/opsec/git_push.py").unlink()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and "push refused" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_missing_interpreter_refuses(push_sandbox):
    push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    (push_sandbox.root / ".venv").unlink()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and "project interpreter unavailable" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_hook_without_the_shim_interpreter_refuses(push_sandbox):
    """Pinned without the shim (an inherited hooks path), the hook cannot scan and refuses."""
    push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    hooks = push_sandbox.root / "scripts/opsec/push_hooks"
    result = subprocess.run(
        [REAL_GIT, "-c", f"core.hooksPath={hooks}", "push", "origin", "HEAD:refs/heads/feature"],
        cwd=push_sandbox.work,
        env=_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0 and "OPSEC: push scanner unavailable; push refused." in result.stderr
    assert push_sandbox.remote_refs() == before


# --- The caller's own hooks still run ---

RECORDING_HOOK = """#!/bin/sh
printf '%s\\n' "$*" > "{log}.args"
cat > "{log}.input"
exit {status}
"""


def _caller_hook(directory, name, log, status=0):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(RECORDING_HOOK.format(log=log, status=status))
    (directory / name).chmod(0o755)


@pytest.mark.parametrize("where", ["repository-hooks", "configured-hooks-path", "command-line-hooks-path"])
def test_the_callers_pre_push_hook_runs_after_a_clean_scan(push_sandbox, where):
    log = push_sandbox.tmp / "caller"
    options = []
    if where == "repository-hooks":
        directory = push_sandbox.work / ".git/hooks"
    else:
        directory = push_sandbox.tmp / "caller-hooks"
        if where == "configured-hooks-path":
            _git(push_sandbox.work, "config", "core.hooksPath", str(directory))
        else:
            options = ["-c", f"core.hooksPath={directory}"]
    _caller_hook(directory, "pre-push", log)
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push(*options, "push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert Path(f"{log}.args").read_text() == f"origin {push_sandbox.remote}\n"
    assert Path(f"{log}.input").read_text() == f"HEAD {sha} refs/heads/feature {ZERO}\n"
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


def test_the_callers_refusing_pre_push_hook_still_refuses(push_sandbox):
    _caller_hook(push_sandbox.work / ".git/hooks", "pre-push", push_sandbox.tmp / "caller", status=1)
    push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    assert push_sandbox.push("push", "origin", "HEAD:refs/heads/feature").returncode != 0
    assert push_sandbox.remote_refs() == before


def test_the_callers_hook_does_not_run_when_the_scan_refuses(push_sandbox):
    log = push_sandbox.tmp / "caller"
    _caller_hook(push_sandbox.work / ".git/hooks", "pre-push", log)
    push_sandbox.commit("subject " + TOKEN)
    assert push_sandbox.push("push", "origin", "HEAD:refs/heads/feature").returncode != 0
    assert not Path(f"{log}.args").exists()


def test_the_callers_reference_transaction_hook_sees_the_tracking_update(push_sandbox):
    log = push_sandbox.tmp / "transaction"
    _caller_hook(push_sandbox.work / ".git/hooks", "reference-transaction", log)
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("push", "origin", "trunk")
    assert result.returncode == 0, result.stderr
    assert f"{sha} refs/remotes/origin/trunk" in Path(f"{log}.input").read_text()


def test_git_config_never_hides_the_callers_refusing_hook(push_sandbox):
    """A command-scope hooks path that `git config` under GIT_CONFIG would not report."""
    log = push_sandbox.tmp / "caller"
    directory = push_sandbox.tmp / "caller-hooks"
    _caller_hook(directory, "pre-push", log, status=1)
    sha = push_sandbox.commit("clean subject")
    before = push_sandbox.remote_refs()
    pushing = ["-c", f"core.hooksPath={directory}", "push", "origin", "HEAD:refs/heads/feature"]
    result = push_sandbox.push(*pushing, GIT_CONFIG=os.devnull)
    assert result.returncode == 2 and "OPSEC: GIT_CONFIG is set" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before and not _remote_has(push_sandbox, sha)
    assert not Path(f"{log}.args").exists()
    # Past the shim, the chain still finds the caller's hook, which runs and refuses.
    result = _pinned(push_sandbox, *pushing, GIT_CONFIG=os.devnull)
    assert result.returncode != 0, result.stderr
    assert Path(f"{log}.args").read_text() == f"origin {push_sandbox.remote}\n"
    assert push_sandbox.remote_refs() == before and not _remote_has(push_sandbox, sha)


# --- Private exemption only on the trusted transport route ---

FAKE_SSH = """#!/bin/sh
# Serve an ssh git URL from a local directory: the last argument is the remote command.
for last; do :; done
command=${last%% *}; path=${last#* }; path=${path#\\'}; path=${path%\\'}
exec git "${command#git-}" "$FAKE_SSH_ROOT/${path#/}"
"""


@pytest.fixture
def ssh_sandbox(push_sandbox, tmp_path):
    """Hosted-looking ssh URLs served from local bare repositories by an ssh program found on PATH."""
    served = tmp_path / "ssh-root"
    for name in ("private", "public"):
        _repository(served / "unit" / f"{name}.git", bare=True)
    programs = tmp_path / "ssh-bin"
    programs.mkdir()
    (programs / "ssh").write_text(FAKE_SSH)
    (programs / "ssh").chmod(0o755)
    push_sandbox.ssh_env = {
        "PATH": os.pathsep.join([str(programs), _env()["PATH"]]),
        "FAKE_SSH_ROOT": str(served),
    }
    push_sandbox.served = served
    push_sandbox.ssh_program = programs / "ssh"
    return push_sandbox


@pytest.mark.parametrize(
    "url", ["git@github.com:unit/private.git", "ssh://git@github.com/unit/private.git", "github.com:unit/private"]
)
@pytest.mark.parametrize("by_name", [False, True])
def test_private_remote_on_the_trusted_route_is_not_scanned(ssh_sandbox, url, by_name):
    sha = ssh_sandbox.commit("subject " + TOKEN)
    shutil.rmtree(ssh_sandbox.tooling)  # A scan would fail closed without the matcher.
    if by_name:
        _git(ssh_sandbox.work, "remote", "add", "hosted", url)
    result = ssh_sandbox.push("push", "hosted" if by_name else url, "HEAD:refs/heads/feature", **ssh_sandbox.ssh_env)
    assert result.returncode == 0, result.stderr
    assert _git(ssh_sandbox.served / "unit/private.git", "rev-parse", "refs/heads/feature") == sha


@pytest.mark.parametrize("route", ["GIT_SSH_COMMAND", "GIT_SSH", "core.sshCommand", "remote-vcs"])
def test_private_remote_on_a_configured_route_is_scanned(ssh_sandbox, route):
    url = "git@github.com:unit/private.git"
    _git(ssh_sandbox.work, "remote", "add", "hosted", url)
    sha = ssh_sandbox.commit("subject " + TOKEN)
    environment = dict(ssh_sandbox.ssh_env)
    if route.startswith("GIT_"):
        environment[route] = str(ssh_sandbox.ssh_program)
    elif route == "core.sshCommand":
        _git(ssh_sandbox.work, "config", "core.sshCommand", str(ssh_sandbox.ssh_program))
    else:
        _git(ssh_sandbox.work, "config", "remote.hosted.vcs", "unit")
    result = ssh_sandbox.push("push", "hosted", "HEAD:refs/heads/feature", **environment)
    assert result.returncode != 0, result.stderr
    if route != "remote-vcs":  # A vcs helper that does not exist fails in Git before any hook.
        assert f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert _git(ssh_sandbox.served / "unit/private.git", "for-each-ref") == ""


@pytest.mark.parametrize("url", ["git@github.com:unit/public.git", "ssh://git@github.com/unit/public.git"])
def test_public_ssh_remote_is_scanned(ssh_sandbox, url):
    sha = ssh_sandbox.commit("subject " + TOKEN)
    result = ssh_sandbox.push("push", url, "HEAD:refs/heads/feature", **ssh_sandbox.ssh_env)
    assert result.returncode != 0 and f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert _git(ssh_sandbox.served / "unit/public.git", "for-each-ref") == ""


REDIRECT_SSH = """#!/bin/sh
# Deliver every ssh git URL to the local public repository, whatever path it names.
for last; do :; done
command=${last%% *}
exec git "${command#git-}" "$FAKE_SSH_ROOT/unit/public.git"
"""


def _redirect(sandbox, shape):
    """(global options, environment) that set core.sshCommand to a redirect to the public receiver."""
    program = sandbox.tmp / "redirect-ssh"
    program.write_text(REDIRECT_SSH)
    program.chmod(0o755)
    if shape == "repository":
        _git(sandbox.work, "config", "core.sshCommand", str(program))
        return [], {}
    if shape == "command-line":
        return ["-c", f"core.sshCommand={program}"], {}
    if shape == "config-env":
        return ["--config-env=core.sshCommand=UNIT_SSH"], {"UNIT_SSH": str(program)}
    assert shape == "count", shape
    return [], {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.sshCommand", "GIT_CONFIG_VALUE_0": str(program)}


def _pinned(sandbox, *args, **extra):
    """Git run as the shim runs a push (hooks path pinned, scanner variables set), without the shim's checks."""
    hooks = sandbox.root / "scripts/opsec/push_hooks"
    command = args.index("push")
    return _plain(
        sandbox,
        *args[:command],
        "-c",
        f"core.hooksPath={hooks}",
        *args[command:],
        LU_OPSEC_PUSH_PYTHON=str(sandbox.root / ".venv/bin/python"),
        LU_OPSEC_REAL_GIT=REAL_GIT,
        **extra,
    )


def assert_nothing_served(sandbox, sha):
    for name in ("private", "public"):
        assert _git(sandbox.served / f"unit/{name}.git", "for-each-ref") == ""
        assert not _remote_has(sandbox, sha, sandbox.served / f"unit/{name}.git")


REDIRECT_SHAPES = ["repository", "command-line", "config-env", "count"]


@pytest.mark.parametrize("shape", REDIRECT_SHAPES)
def test_push_with_git_config_set_is_refused_before_git_runs(ssh_sandbox, shape):
    """GIT_CONFIG hides core.sshCommand from `git config` but not from the push, so the shim refuses it."""
    _git(ssh_sandbox.work, "remote", "add", "hosted", "git@github.com:unit/private.git")
    options, environment = _redirect(ssh_sandbox, shape)
    sha = ssh_sandbox.commit("subject " + TOKEN)
    pushing = [*options, "push", "hosted", "HEAD:refs/heads/feature"]
    result = ssh_sandbox.push(*pushing, GIT_CONFIG=os.devnull, **ssh_sandbox.ssh_env, **environment)
    assert result.returncode == 2, result.stderr
    assert "OPSEC: GIT_CONFIG is set" in result.stderr and "push refused." in result.stderr, result.stderr
    assert_nothing_served(ssh_sandbox, sha)
    # Control: plain Git delivers the same push to the public receiver.
    control = _plain(ssh_sandbox, *pushing, GIT_CONFIG=os.devnull, **ssh_sandbox.ssh_env, **environment)
    assert control.returncode == 0, control.stderr
    assert _git(ssh_sandbox.served / "unit/public.git", "rev-parse", "refs/heads/feature") == sha


@pytest.mark.parametrize("shape", REDIRECT_SHAPES)
def test_scanner_sees_the_route_git_config_hides(ssh_sandbox, shape):
    """Past the shim, the scanner's configuration reads still find core.sshCommand and scan the push."""
    _git(ssh_sandbox.work, "remote", "add", "hosted", "git@github.com:unit/private.git")
    options, environment = _redirect(ssh_sandbox, shape)
    sha = ssh_sandbox.commit("subject " + TOKEN)
    pushing = [*options, "push", "hosted", "HEAD:refs/heads/feature"]
    result = _pinned(ssh_sandbox, *pushing, GIT_CONFIG=os.devnull, **ssh_sandbox.ssh_env, **environment)
    assert result.returncode != 0 and f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert TOKEN not in result.stderr
    assert_nothing_served(ssh_sandbox, sha)


def test_trusted_route_reads_past_git_config(push_sandbox, monkeypatch):
    _git(push_sandbox.work, "config", "core.sshCommand", "ssh")
    url = "git@github.com:unit/private.git"
    assert _trusted(push_sandbox.work, monkeypatch, url, GIT_CONFIG=os.devnull) is False


def _trusted(work, monkeypatch, url, remote="origin", git=REAL_GIT, **extra):
    monkeypatch.chdir(work)
    environment = _env(GIT_EXEC_PATH=_git(work, "--exec-path"), **extra)
    return git_push.trusted_route(git_push.Repository(git, environment), remote, url)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/unit/private.git", True),
        ("git@github.com:unit/private.git", True),
        ("ssh://git@github.com/unit/private.git", True),
        ("http://github.com/unit/private.git", False),
        ("git://github.com/unit/private.git", False),
        ("ext::ssh github.com unit/private", False),
        ("unit::https://github.com/unit/private", False),
        ("/srv/unit/private.git", False),
    ],
)
def test_trusted_route_by_url(push_sandbox, monkeypatch, url, expected):
    assert _trusted(push_sandbox.work, monkeypatch, url) is expected


@pytest.mark.parametrize(
    "change",
    ["GIT_SSL_NO_VERIFY", "http.sslVerify", "url-scoped http.sslVerify", "GIT_EXEC_PATH", "relative git"],
)
def test_https_route_changes_are_untrusted(push_sandbox, monkeypatch, change):
    url = "https://github.com/unit/private.git"
    extra, git = {}, REAL_GIT
    if change == "GIT_SSL_NO_VERIFY":
        extra = {"GIT_SSL_NO_VERIFY": "1"}
    elif change == "http.sslVerify":
        _git(push_sandbox.work, "config", "http.sslVerify", "false")
    elif change == "url-scoped http.sslVerify":
        _git(push_sandbox.work, "config", "http.https://github.com/.sslVerify", "false")
    elif change == "relative git":
        git = "git"
    if change == "GIT_EXEC_PATH":
        monkeypatch.chdir(push_sandbox.work)
        environment = _env(GIT_EXEC_PATH=str(push_sandbox.tmp))
        assert not git_push.trusted_route(git_push.Repository(REAL_GIT, environment), "origin", url)
    else:
        assert _trusted(push_sandbox.work, monkeypatch, url, git=git, **extra) is False


def test_url_scoped_verification_for_another_host_keeps_the_route(push_sandbox, monkeypatch):
    _git(push_sandbox.work, "config", "http.https://elsewhere.invalid/.sslVerify", "false")
    assert _trusted(push_sandbox.work, monkeypatch, "https://github.com/unit/private.git") is True


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/unit/private.git", "github.com/unit/private"),
        ("https://user@github.com/unit/private", "github.com/unit/private"),
        ("git@github.com:unit/private.git", "github.com/unit/private"),
        ("ssh://git@github.com:22/unit/private.git", "github.com/unit/private"),
        ("github.com:unit/private.git", "github.com/unit/private"),
        ("git+ssh://github.com/unit/private.git", "github.com/unit/private"),
        ("../remote.git", "unknown"),
        ("/srv/unit/remote.git", "unknown"),
        ("file:///srv/unit/private.git", "unknown"),
        ("helper::github.com/unit/private", "unknown"),
        ("", "unknown"),
    ],
)
def test_push_url_destinations(url, expected):
    assert git_push.destination(url) == expected


# --- Recursive submodule pushes: every child is scanned in its own repository ---


@pytest.fixture
def submodules(push_sandbox):
    """work has submodule sub (remote sub.git), which has submodule leaf (remote leaf.git)."""
    tmp = push_sandbox.tmp
    allow = ["-c", "protocol.file.allow=always"]
    remotes = {}
    for name in ("leaf", "sub"):
        remotes[name] = _repository(tmp / f"{name}.git", bare=True)
        seed = _repository(tmp / f"{name}-seed")
        (seed / "file.txt").write_text(f"{name}\n")
        _git(seed, "add", "file.txt")
        _git(seed, "commit", "-q", "-m", f"clean {name} base")
        if name == "sub":
            _git(seed, *allow, "submodule", "add", "-q", str(remotes["leaf"]), "leaf")
            _git(seed, "commit", "-q", "-m", "clean leaf added")
        _git(seed, "push", "-q", str(remotes[name]), "trunk")
    _git(push_sandbox.work, *allow, "submodule", "add", "-q", str(remotes["sub"]), "sub")
    _git(push_sandbox.work, *allow, "submodule", "update", "-q", "--init", "--recursive")
    _git(push_sandbox.work, "commit", "-q", "-m", "clean sub added")
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")
    paths = {"sub": push_sandbox.work / "sub", "leaf": push_sandbox.work / "sub/leaf"}
    for path in paths.values():
        _git(path, "checkout", "-q", "-B", "trunk")
        _git(path, "config", "user.email", "unit@example.invalid")
        _git(path, "config", "user.name", "unit")
    push_sandbox.submodule_remotes = remotes
    push_sandbox.submodule_paths = paths
    return push_sandbox


def _bump(sandbox, leaf_message, sub_message="clean sub bump"):
    """New commits in leaf, then sub (recording leaf), then work (recording sub); returns their ids."""
    paths = sandbox.submodule_paths
    leaf = sandbox.commit(leaf_message, cwd=paths["leaf"])
    _git(paths["sub"], "add", "leaf")
    sub = sandbox.commit(sub_message, cwd=paths["sub"])
    _git(sandbox.work, "add", "sub")
    _git(sandbox.work, "commit", "-q", "-m", "clean work bump")
    return leaf, sub


RECURSION = {
    "option": ["push", "--recurse-submodules=on-demand"],
    "only": ["push", "--recurse-submodules=only"],
    "push-config": ["-c", "push.recurseSubmodules=on-demand", "push"],
    "submodule-recurse": ["-c", "submodule.recurse=true", "push"],
}
# Git hands configuration, not the command-line option, to the child pushes, so only these reach the leaf.
NESTED = ["push-config", "submodule-recurse"]


@pytest.mark.parametrize("recursion", NESTED)
def test_hit_in_a_nested_child_sends_nothing_anywhere(submodules, recursion):
    remotes = submodules.submodule_remotes
    before = {name: submodules.remote_refs(remote) for name, remote in remotes.items()}
    before_work = submodules.remote_refs()
    leaf, _ = _bump(submodules, "leaf subject " + TOKEN)
    result = submodules.push(*RECURSION[recursion], "origin", "trunk")
    assert result.returncode != 0 and f"field=commit[{leaf[:12]}].message" in result.stderr, result.stderr
    assert {name: submodules.remote_refs(remote) for name, remote in remotes.items()} == before
    assert submodules.remote_refs() == before_work and not _remote_has(submodules, leaf, remotes["leaf"])


@pytest.mark.parametrize("recursion", sorted(set(RECURSION) - set(NESTED)))
def test_one_level_recursion_never_sends_a_nested_hit(submodules, recursion):
    leaf, _ = _bump(submodules, "leaf subject " + TOKEN)
    submodules.push(*RECURSION[recursion], "origin", "trunk")
    assert not _remote_has(submodules, leaf, submodules.submodule_remotes["leaf"])


@pytest.mark.parametrize("recursion", sorted(RECURSION))
def test_hit_in_a_direct_child_is_refused(submodules, recursion):
    before = submodules.remote_refs()
    _, sub = _bump(submodules, "clean leaf work", "sub subject " + TOKEN)
    result = submodules.push(*RECURSION[recursion], "origin", "trunk")
    assert result.returncode != 0 and f"field=commit[{sub[:12]}].message" in result.stderr, result.stderr
    assert not _remote_has(submodules, sub, submodules.submodule_remotes["sub"])
    assert submodules.remote_refs() == before


@pytest.mark.parametrize("recursion", sorted(RECURSION))
def test_clean_recursive_push_delivers_every_child(submodules, recursion):
    leaf, sub = _bump(submodules, "clean leaf work")
    result = submodules.push(*RECURSION[recursion], "origin", "trunk")
    assert result.returncode == 0, result.stderr
    remotes = submodules.submodule_remotes
    assert (submodules.remote_refs(remotes["leaf"])["refs/heads/trunk"] == leaf) is (recursion in NESTED)
    assert submodules.remote_refs(remotes["sub"])["refs/heads/trunk"] == sub
    work = _git(submodules.work, "rev-parse", "HEAD")
    assert (submodules.remote_refs()["refs/heads/trunk"] == work) is (recursion != "only")


def test_without_recursion_children_are_not_pushed(submodules):
    """Control: a plain push leaves the children alone, so the recursion cases above exercise child pushes."""
    leaf, _ = _bump(submodules, "clean leaf work")
    assert submodules.push("push", "origin", "trunk").returncode == 0
    assert not _remote_has(submodules, leaf, submodules.submodule_remotes["leaf"])


# --- Cost of one ordinary clean push ---


def test_clean_push_latency_is_reported(push_sandbox):
    """Prints the added time of one ordinary clean push through the shim (median of five)."""
    times = {"shim": [], "plain": []}
    for number in range(5):
        for kind in times:
            push_sandbox.commit(f"clean {kind} {number}")
            argv = [str(push_sandbox.shim) if kind == "shim" else REAL_GIT, "push", "-q", "origin", "trunk"]
            started = time.perf_counter()
            subprocess.run(argv, cwd=push_sandbox.work, env=_env(), check=True, capture_output=True, timeout=60)
            times[kind].append(time.perf_counter() - started)
    shim, plain = (sorted(values)[2] for values in times.values())
    print(f"clean push: plain git {plain:.3f}s, through the shim {shim:.3f}s, added {shim - plain:.3f}s")
    assert shim - plain < 5
