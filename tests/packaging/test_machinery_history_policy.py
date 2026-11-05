"""The machinery history policy admits only frozen retain/replace versions, during and after the rewrite.

Each case builds a small synthetic repository in tmp_path. Integration cases run the real
git-filter-repo 2.47.0 from its isolated tool venv, named by MACHINERY_FILTER_REPO_VENV
(for example /home/ops/ops-state/tools/git-filter-repo-2.47.0); they skip, with that
reason, when the variable is unset. A set variable that names anything other than
git-filter-repo 2.47.0 fails. No network and no live repository state is used.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[2] / "packaging" / "machinery-move" / "history_policy.py"
RENAME = "scripts/:lu_machinery/"
FILTER_REPO_ENV = "MACHINERY_FILTER_REPO_VENV"

pytestmark = pytest.mark.timeout(300)


def _git_env(home: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        HOME=str(home),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME="History Policy Test",
        GIT_AUTHOR_EMAIL="history-policy-test@example.invalid",
        GIT_COMMITTER_NAME="History Policy Test",
        GIT_COMMITTER_EMAIL="history-policy-test@example.invalid",
    )
    return env


class Repo:
    def __init__(self, path: Path, home: Path) -> None:
        self.path = path
        self.env = _git_env(home)

    def git(self, *args: str, stdin: bytes | None = None) -> str:
        git = shutil.which("git")
        assert git is not None
        result = subprocess.run(
            [git, "-C", str(self.path), "-c", "commit.gpgsign=false", *args],
            input=stdin,
            check=True,
            capture_output=True,
            env=self.env,
            timeout=120,
        )
        return result.stdout.decode().strip()

    def commit(self, files: dict[str, bytes | None], message: str) -> str:
        for name, content in files.items():
            if content is None:
                self.git("rm", "--quiet", "--", name)
                continue
            target = self.path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            self.git("add", "--", name)
        self.git("commit", "--quiet", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def tree(self, rev: str) -> dict[str, str]:
        listing = self.git("ls-tree", "-r", "--full-tree", rev)
        entries = {}
        for line in listing.splitlines():
            meta, path = line.split("\t", 1)
            entries[path] = meta.split()[2]
        return entries

    def reachable_objects(self) -> set[str]:
        return {line.split()[0] for line in self.git("rev-list", "--objects", "--all").splitlines()}

    def commit_map(self) -> dict[str, str]:
        lines = (self.path / ".git" / "filter-repo" / "commit-map").read_text().splitlines()[1:]
        return dict(line.split() for line in lines)


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


@pytest.fixture
def home(tmp_path: Path) -> Path:
    path = tmp_path / "home"
    path.mkdir()
    return path


@pytest.fixture
def source(tmp_path: Path, home: Path) -> Repo:
    path = tmp_path / "source"
    repo = Repo(path, home)
    path.mkdir()
    repo.git("init", "--quiet", "--initial-branch=main", "--object-format=sha1")
    return repo


@pytest.fixture
def filter_repo() -> Path:
    venv = os.environ.get(FILTER_REPO_ENV)
    if not venv:
        pytest.skip(f"{FILTER_REPO_ENV} is unset; the isolated git-filter-repo 2.47.0 venv is unavailable")
    executable = Path(venv) / "bin" / "git-filter-repo"
    assert executable.is_file(), f"{executable} is missing"
    version = subprocess.run(
        [
            str(Path(venv) / "bin" / "python"),
            "-I",
            "-c",
            "import importlib.metadata as m; print(m.version('git-filter-repo'))",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.strip()
    assert version == "2.47.0", f"{FILTER_REPO_ENV} names git-filter-repo {version}, not 2.47.0"
    return executable


class Policy:
    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.path = folder / "policy.tsv"
        self.rows: list[str] = []
        (folder / "replacements").mkdir(parents=True)

    def add(self, path: str, blob: str, action: str, replacement: bytes | None = None) -> None:
        digest = ""
        if replacement is not None:
            digest = hashlib.sha256(replacement).hexdigest()
            (self.folder / "replacements" / digest).write_bytes(replacement)
        self.rows.append("\t".join([path, blob, action, digest]) if digest else "\t".join([path, blob, action]))

    def freeze(self) -> str:
        data = ("source_path\tblob\taction\treplacement_sha256\n" + "".join(row + "\n" for row in self.rows)).encode()
        self.path.write_bytes(data)
        return hashlib.sha256(data).hexdigest()


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, timeout=300)


def rewrite(
    source: Repo,
    filter_repo: Path,
    policy: Policy,
    digest: str,
    *,
    include: list[str] | None = None,
    callback_body: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], Repo]:
    """Clone the source fresh and run git-filter-repo with the printed callback, as plan step 3 does."""
    clone = Repo(
        source.path.parent / f"extract-{len(list(source.path.parent.glob('extract-*')))}", Path(source.env["HOME"])
    )
    subprocess.run(
        ["git", "clone", "--quiet", "--no-local", str(source.path), str(clone.path)],
        check=True,
        capture_output=True,
        env=clone.env,
        timeout=120,
    )
    if callback_body is None:
        printed = run_tool("callback", "--policy", str(policy.path), "--policy-sha256", digest, "--path-rename", RENAME)
        assert printed.returncode == 0, printed.stderr
        callback_body = printed.stdout
    args = [str(filter_repo)]
    if include is not None:
        include_file = clone.path.parent / f"{clone.path.name}.include"
        include_file.write_text("".join(p + "\n" for p in include))
        args += ["--paths-from-file", str(include_file)]
    args += ["--path-rename", RENAME, "--file-info-callback", callback_body]
    result = subprocess.run(args, cwd=clone.path, capture_output=True, text=True, env=clone.env, timeout=300)
    return result, clone


def verify(clone: Repo, policy: Policy, digest: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return run_tool(
        "verify",
        "--repo",
        str(clone.path),
        "--policy",
        str(policy.path),
        "--policy-sha256",
        digest,
        "--commit-map",
        str(clone.path / ".git" / "filter-repo" / "commit-map"),
        "--path-rename",
        RENAME,
        *extra,
    )


# --- policy validation (no git-filter-repo needed) --------------------------------------


def test_check_policy_accepts_a_valid_policy_and_prints_its_freeze_digest(tmp_path: Path) -> None:
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", "1" * 40, "retain")
    policy.add("scripts/a.py", "2" * 40, "omit")
    policy.add("scripts/a.py", "3" * 40, "replace", b"sanitized\n")
    digest = policy.freeze()
    include = tmp_path / "include.txt"
    include.write_text("scripts/a.py\n")

    result = run_tool("check-policy", "--policy", str(policy.path), "--include", str(include))

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"policy_sha256={digest}" in result.stdout
    assert "rows=3 retain=1 omit=1 replace=1" in result.stdout


def test_check_policy_malformed_rows_and_duplicate_keys_are_findings(tmp_path: Path) -> None:
    policy = Policy(tmp_path / "policy")
    policy.rows += [
        "scripts/a.py\t" + "1" * 40 + "\tretain",
        "scripts/a.py\t" + "1" * 40 + "\tomit",  # duplicate (path, blob) key
        "scripts/b.py\t" + "A" * 40 + "\tretain",  # uppercase blob id
        "scripts/c.py\t" + "1" * 40 + "\tkeep",  # unknown action
        "scripts/d.py\t" + "1" * 40 + "\treplace",  # replace without a digest
        "scripts/e.py\t" + "1" * 40 + "\tomit\t" + "f" * 64,  # digest on a non-replace row
        "../f.py\t" + "1" * 40 + "\tretain",  # path escapes the tree
        "scripts/g.py\t" + "1" * 40,  # too few fields
    ]
    policy.freeze()

    result = run_tool("check-policy", "--policy", str(policy.path))

    assert result.returncode == 1
    for fragment in (
        "line 3: duplicate (path, blob) key, first listed on line 2",
        "line 4: blob must be 40 lowercase hex",
        "line 5: action must be retain, omit or replace",
        "line 6: replace needs a 64-hex replacement_sha256",
        "line 7: replacement_sha256 is only allowed for replace",
        "line 8: invalid source path",
        "line 9: expected 3 or 4 tab-separated fields",
    ):
        assert fragment in result.stdout


def test_check_policy_missing_tampered_or_contradictory_replacement_is_a_finding(tmp_path: Path) -> None:
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", "1" * 40, "replace", b"sanitized a\n")
    policy.add("scripts/b.py", "2" * 40, "replace", b"sanitized b\n")
    policy.add("scripts/c.py", blob_id(b"omitted c\n"), "omit")
    policy.add("scripts/c.py", "3" * 40, "replace", b"omitted c\n")  # replacement equals an omitted version
    policy.freeze()
    (policy.folder / "replacements" / hashlib.sha256(b"sanitized a\n").hexdigest()).unlink()
    (policy.folder / "replacements" / hashlib.sha256(b"sanitized b\n").hexdigest()).write_bytes(b"tampered\n")

    result = run_tool("check-policy", "--policy", str(policy.path))

    assert result.returncode == 1
    assert "for scripts/a.py is missing" in result.stdout
    assert "for scripts/b.py does not hash to its declared sha256" in result.stdout
    assert "for scripts/c.py hashes to a blob that the policy omits" in result.stdout


def test_check_policy_path_outside_the_include_list_is_a_finding(tmp_path: Path) -> None:
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", "1" * 40, "retain")
    policy.add("scripts/unlisted.py", "2" * 40, "retain")
    policy.freeze()
    include = tmp_path / "include.txt"
    include.write_text("scripts/a.py\n")

    result = run_tool("check-policy", "--policy", str(policy.path), "--include", str(include))

    assert result.returncode == 1
    assert "path scripts/unlisted.py is not in the include list" in result.stdout


def test_check_policy_missing_policy_is_unusable_input(tmp_path: Path) -> None:
    result = run_tool("check-policy", "--policy", str(tmp_path / "absent.tsv"))
    assert result.returncode == 2


def test_callback_refuses_to_print_for_a_digest_that_is_not_the_frozen_one(tmp_path: Path) -> None:
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", "1" * 40, "retain")
    policy.freeze()

    result = run_tool("callback", "--policy", str(policy.path), "--policy-sha256", "0" * 64, "--path-rename", RENAME)

    assert result.returncode == 2
    assert "does not match the frozen" in result.stderr
    assert result.stdout == ""


def test_h6_policy_keyed_on_output_paths_is_refused(tmp_path: Path) -> None:
    policy = Policy(tmp_path / "policy")
    policy.add("lu_machinery/a.py", "1" * 40, "retain")
    digest = policy.freeze()

    result = run_tool("callback", "--policy", str(policy.path), "--policy-sha256", digest, "--path-rename", RENAME)

    assert result.returncode == 2
    assert "inside the rename target" in result.stderr


# --- rewrites with the real git-filter-repo 2.47.0 ---------------------------------------


def test_h1_default_deny_unlisted_version_aborts_the_rewrite(source: Repo, filter_repo: Path, tmp_path: Path) -> None:
    source.commit({"scripts/a.py": b"v1\n"}, "c1")
    head = source.commit({"scripts/a.py": b"v2 unreviewed\n"}, "c2")
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", blob_id(b"v1\n"), "retain")
    digest = policy.freeze()

    result, clone = rewrite(source, filter_repo, policy, digest)

    assert result.returncode != 0
    assert "is not in the policy; default deny" in result.stderr
    assert clone.git("rev-parse", "refs/heads/main") == head, "an aborted rewrite must leave the refs untouched"
    assert not (clone.path / ".git" / "filter-repo" / "commit-map").exists()


def test_h2_omitted_version_is_absent_from_every_commit_while_retained_versions_remain(
    source: Repo, filter_repo: Path, tmp_path: Path
) -> None:
    versions = [b"v1 public\n", b"v2 confidential\n", b"v3 public\n"]
    for number, content in enumerate(versions, 1):
        source.commit({"scripts/a.py": content, "scripts/other.py": b"other %d\n" % number}, f"c{number}")
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", blob_id(versions[0]), "retain")
    policy.add("scripts/a.py", blob_id(versions[1]), "omit")
    policy.add("scripts/a.py", blob_id(versions[2]), "retain")
    for number in (1, 2, 3):
        policy.add("scripts/other.py", blob_id(b"other %d\n" % number), "retain")
    digest = policy.freeze()

    result, clone = rewrite(source, filter_repo, policy, digest)

    assert result.returncode == 0, result.stderr
    seen = [clone.tree(c).get("lu_machinery/a.py") for c in clone.git("rev-list", "--reverse", "HEAD").splitlines()]
    assert seen == [blob_id(versions[0]), None, blob_id(versions[2])]
    assert blob_id(versions[1]) not in clone.reachable_objects()
    checked = verify(clone, policy, digest)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert "checked=5 retained=5 replaced=0 omitted=1 findings=0" in checked.stdout


def test_h3_replacement_bytes_appear_exactly_and_the_original_blob_nowhere(
    source: Repo, filter_repo: Path, tmp_path: Path
) -> None:
    original = b"unsanitized original version\n"
    sanitized = b"sanitized replacement version\n"
    source.commit({"scripts/a.py": original, "scripts/b.py": original}, "c1")
    source.commit({"scripts/a.py": b"later\n"}, "c2")
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", blob_id(original), "replace", sanitized)
    policy.add("scripts/b.py", blob_id(original), "replace", sanitized)
    policy.add("scripts/a.py", blob_id(b"later\n"), "retain")
    digest = policy.freeze()

    result, clone = rewrite(source, filter_repo, policy, digest)

    assert result.returncode == 0, result.stderr
    first = clone.git("rev-list", "--max-parents=0", "HEAD")
    tree = clone.tree(first)
    assert tree["lu_machinery/a.py"] == tree["lu_machinery/b.py"] == blob_id(sanitized)
    shown = subprocess.run(
        ["git", "-C", str(clone.path), "cat-file", "blob", blob_id(sanitized)],
        capture_output=True,
        check=True,
        timeout=120,
    ).stdout
    assert shown == sanitized
    assert blob_id(original) not in clone.reachable_objects()
    checked = verify(clone, policy, digest)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert "retained=1 replaced=2" in checked.stdout


def test_h4_tampered_policy_or_replacement_is_refused_at_rewrite_time_and_by_verify(
    source: Repo, filter_repo: Path, tmp_path: Path
) -> None:
    sanitized = b"sanitized\n"
    source.commit({"scripts/a.py": b"original\n"}, "c1")
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", blob_id(b"original\n"), "replace", sanitized)
    digest = policy.freeze()
    printed = run_tool("callback", "--policy", str(policy.path), "--policy-sha256", digest, "--path-rename", RENAME)
    assert printed.returncode == 0, printed.stderr
    good, clone = rewrite(source, filter_repo, policy, digest, callback_body=printed.stdout)
    assert good.returncode == 0, good.stderr
    assert verify(clone, policy, digest).returncode == 0

    frozen_policy = policy.path.read_bytes()
    policy.path.write_bytes(frozen_policy + b"scripts/a.py\t" + b"9" * 40 + b"\tretain\n")
    tampered, _ = rewrite(source, filter_repo, policy, digest, callback_body=printed.stdout)
    assert tampered.returncode != 0
    assert "refusing to start: policy sha256" in tampered.stderr
    assert verify(clone, policy, digest).returncode == 2

    policy.path.write_bytes(frozen_policy)
    replacement = policy.folder / "replacements" / hashlib.sha256(sanitized).hexdigest()
    replacement.write_bytes(b"swapped after freeze\n")
    tampered, _ = rewrite(source, filter_repo, policy, digest, callback_body=printed.stdout)
    assert tampered.returncode != 0
    assert "refusing to start: replacement" in tampered.stderr
    after = verify(clone, policy, digest)
    assert after.returncode == 2
    assert "does not hash to its declared sha256" in after.stderr


def test_h5_verify_independently_catches_an_injected_surviving_omitted_version(
    source: Repo, filter_repo: Path, tmp_path: Path
) -> None:
    omitted = b"confidential\n"
    original = b"unsanitized\n"
    source.commit({"scripts/a.py": b"public\n", "scripts/b.py": original}, "c1")
    source.commit({"scripts/a.py": omitted}, "c2")
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", blob_id(b"public\n"), "retain")
    policy.add("scripts/a.py", blob_id(omitted), "omit")
    policy.add("scripts/b.py", blob_id(original), "replace", b"sanitized\n")
    digest = policy.freeze()
    result, clone = rewrite(source, filter_repo, policy, digest)
    assert result.returncode == 0, result.stderr
    assert verify(clone, policy, digest).returncode == 0

    (clone.path / "lu_machinery").mkdir(exist_ok=True)
    (clone.path / "lu_machinery" / "a.py").write_bytes(omitted)
    (clone.path / "lu_machinery" / "b.py").write_bytes(original)
    clone.git("add", "--", "lu_machinery/a.py", "lu_machinery/b.py")
    clone.git("commit", "--quiet", "-m", "inject")
    commit_map = clone.path / ".git" / "filter-repo" / "commit-map"
    commit_map.write_text(commit_map.read_text() + "1" * 40 + " " + "2" * 40 + "\n")

    checked = verify(clone, policy, digest)

    assert checked.returncode == 1
    assert f"omitted-version-survives path='lu_machinery/a.py' blob={blob_id(omitted)}" in checked.stdout
    assert f"replaced-original-survives path='lu_machinery/b.py' blob={blob_id(original)}" in checked.stdout
    assert "commit-map-names-missing-commit new=" + "2" * 40 in checked.stdout


def test_h6_path_rename_applies_a_source_keyed_policy_and_denies_uninvertible_output_paths(
    source: Repo, filter_repo: Path, tmp_path: Path, home: Path
) -> None:
    source.commit(
        {
            "scripts/a.py": b"machinery\n",
            "agents_extensions/shared/rules/r.md": b"rule\n",
            "product/excluded.py": b"never included\n",
        },
        "c1",
    )
    policy = Policy(tmp_path / "policy")
    policy.add("scripts/a.py", blob_id(b"machinery\n"), "retain")
    policy.add("agents_extensions/shared/rules/r.md", blob_id(b"rule\n"), "retain")
    digest = policy.freeze()
    include = ["scripts/a.py", "agents_extensions/shared/rules/r.md"]

    good, clone = rewrite(source, filter_repo, policy, digest, include=include)

    assert good.returncode == 0, good.stderr
    assert set(clone.tree("HEAD")) == {"lu_machinery/a.py", "agents_extensions/shared/rules/r.md"}
    checked = verify(clone, policy, digest)
    assert checked.returncode == 0, checked.stdout + checked.stderr

    denied, _ = rewrite(source, filter_repo, policy, digest, include=[*include, "product/excluded.py"])
    assert denied.returncode != 0
    assert "output path 'product/excluded.py' does not invert to a policy source path" in denied.stderr

    unrenamed = Repo(tmp_path / "unrenamed", home)
    subprocess.run(
        ["git", "clone", "--quiet", "--no-local", str(source.path), str(unrenamed.path)],
        check=True,
        capture_output=True,
        env=unrenamed.env,
        timeout=120,
    )
    checked = run_tool(
        "verify",
        "--repo",
        str(unrenamed.path),
        "--policy",
        str(policy.path),
        "--policy-sha256",
        digest,
        "--commit-map",
        str(clone.path / ".git" / "filter-repo" / "commit-map"),
        "--path-rename",
        RENAME,
    )
    assert checked.returncode == 1
    assert "path-does-not-invert path='scripts/a.py'" in checked.stdout
    assert "path-does-not-invert path='product/excluded.py'" in checked.stdout


def test_h7_transition_commits_do_not_inherit_an_earlier_retained_version(
    source: Repo, filter_repo: Path, tmp_path: Path
) -> None:
    # a: retain -> omit -> retain, with the omitted version also arriving through a merge.
    # b: omit -> retain.
    a1, a2, a3, a4 = b"a1 public\n", b"a2 confidential\n", b"a3 public\n", b"a4 confidential\n"
    b1, b2 = b"b1 confidential\n", b"b2 public\n"
    c1 = source.commit({"scripts/a.py": a1, "scripts/b.py": b1}, "c1")
    c2 = source.commit({"scripts/a.py": a2, "scripts/b.py": b2}, "c2")
    c3 = source.commit({"scripts/a.py": a3}, "c3")
    source.git("checkout", "--quiet", "-b", "side")
    s1 = source.commit({"scripts/a.py": a4}, "s1")
    source.git("checkout", "--quiet", "main")
    m1 = source.commit({"scripts/n.py": b"n\n"}, "m1")
    source.git("merge", "--quiet", "--no-ff", "-m", "merge side", "side")
    merge = source.git("rev-parse", "HEAD")
    c4 = source.commit({"scripts/a.py": a1}, "c4")
    source.git("branch", "--quiet", "-D", "side")
    assert source.tree(merge)["scripts/a.py"] == blob_id(a4)
    policy = Policy(tmp_path / "policy")
    for content, action in ((a1, "retain"), (a2, "omit"), (a3, "retain"), (a4, "omit")):
        policy.add("scripts/a.py", blob_id(content), action)
    policy.add("scripts/b.py", blob_id(b1), "omit")
    policy.add("scripts/b.py", blob_id(b2), "retain")
    policy.add("scripts/n.py", blob_id(b"n\n"), "retain")
    digest = policy.freeze()

    result, clone = rewrite(source, filter_repo, policy, digest)

    assert result.returncode == 0, result.stderr
    mapped = clone.commit_map()
    content = {
        name: clone.tree(mapped[sha])
        for name, sha in (("c1", c1), ("c2", c2), ("c3", c3), ("s1", s1), ("m1", m1), ("merge", merge), ("c4", c4))
    }
    assert content["c1"].get("lu_machinery/a.py") == blob_id(a1)
    assert "lu_machinery/b.py" not in content["c1"], "omit -> retain: the omitted first version is absent"
    assert "lu_machinery/a.py" not in content["c2"], "retain -> omit: c2 must not present a1 as its content"
    assert content["c2"]["lu_machinery/b.py"] == blob_id(b2)
    assert content["c3"]["lu_machinery/a.py"] == blob_id(a3)
    assert "lu_machinery/a.py" not in content["s1"]
    assert content["m1"]["lu_machinery/a.py"] == blob_id(a3)
    assert "lu_machinery/a.py" not in content["merge"], "a merge taking an omitted version must not keep a3"
    assert content["c4"]["lu_machinery/a.py"] == blob_id(a1)
    reachable = clone.reachable_objects()
    assert not {blob_id(a2), blob_id(a4), blob_id(b1)} & reachable
    checked = verify(clone, policy, digest)
    assert checked.returncode == 0, checked.stdout + checked.stderr
