"""Host updater for the jevgrep CLI and its user-level skill (#9134).

Every subprocess, registry and download call is injected: no network, no npm, temp HOME.
"""

from __future__ import annotations

import base64
import email.message
import fcntl
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import urllib.response
from pathlib import Path
from typing import Any

import pytest

from scripts.tools import jevgrep_update as updater

REPO = Path(__file__).resolve().parents[1]
OVERLAY = (REPO / updater.OVERLAY_REL).read_text(encoding="utf-8")
LEGACY_LINK = "../lib/node_modules/@dzhng/jevgrep/dist/bin/index.js"
SECRET = "npm_FAKEtoken0123456789SECRET"
PYODIDE = {
    "version": "0.25.1",
    "resolved": "https://registry.npmjs.org/pyodide/-/pyodide-0.25.1.tgz",
    "integrity": "sha512-cHlvZGlkZQ==",
}


def _tarball_bytes(version: str) -> bytes:
    return json.dumps({"version": version}).encode("utf-8")


def _sri(data: bytes) -> str:
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode("ascii")


def _meta(
    version: str,
    *,
    attestations: bool = True,
    scripts: dict[str, str] | None = None,
    bin_jg: bool = True,
    tarball: str | None = None,
    integrity: str | None = "auto",
) -> dict[str, Any]:
    dist: dict[str, Any] = {"tarball": tarball or f"https://registry.npmjs.org/@dzhng/jevgrep/-/jevgrep-{version}.tgz"}
    if integrity == "auto":
        dist["integrity"] = _sri(_tarball_bytes(version))
    elif integrity is not None:
        dist["integrity"] = integrity
    if attestations:
        dist["attestations"] = {"provenance": {"predicateType": "https://slsa.dev/provenance/v1"}}
    return {
        "scripts": scripts or {"test": "bun test"},
        "bin": {"jg": "dist/bin/index.js"} if bin_jg else {},
        "dist": dist,
    }


def _packument(latest: str, overrides: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    versions = {v: _meta(v) for v in ("0.4.4", "0.5.0", "0.6.0", "0.7.0", latest)}
    return {"dist-tags": {"latest": latest}, "versions": {**versions, **(overrides or {})}}


def _package_version(binary: Path) -> str | None:
    for parent in binary.resolve().parents:
        if (parent / "package.json").is_file():
            return json.loads((parent / "package.json").read_text())["version"]
    return None


class FakeHost:
    """A fake npm + jg over a real temp HOME. Every child also prints a fake credential."""

    def __init__(
        self,
        home: Path,
        installed: str | None = "0.4.4",
        *,
        npm_fails: frozenset[str] = frozenset(),
        doctor_fails: frozenset[str] = frozenset(),
        link_doctor_fails: frozenset[str] = frozenset(),
        no_skill: frozenset[str] = frozenset(),
        staged: dict[str, dict[str, Any] | None] | None = None,
        hidden_lockfile: bool = True,
    ):
        self.home = home
        self.link = home / updater.BIN_LINK_REL
        self.npm_fails = npm_fails
        self.doctor_fails = doctor_fails
        self.link_doctor_fails = link_doctor_fails
        self.no_skill = no_skill
        self.staged = staged or {}
        self.hidden_lockfile = hidden_lockfile
        self.calls: list[list[str]] = []
        self.npm_envs: list[dict[str, str]] = []
        self.npm_config_texts: list[str] = []
        self.downloads: list[str] = []
        home.mkdir(parents=True, exist_ok=True)
        if installed:
            self.legacy = home / ".local/lib/node_modules/@dzhng/jevgrep"
            self._materialize(self.legacy, installed)
            self.link.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(LEGACY_LINK, self.link)

    @staticmethod
    def upstream(version: str) -> str:
        return f"---\nname: jevgrep\ndescription: upstream\n---\n\n# Jevgrep\n\nUpstream body for {version}.\n"

    def _materialize(self, package: Path, version: str) -> None:
        (package / "dist/bin").mkdir(parents=True, exist_ok=True)
        (package / "package.json").write_text(json.dumps({"name": updater.PACKAGE, "version": version}))
        (package / "dist/bin/index.js").write_text("#!/usr/bin/env node\n")
        if version not in self.no_skill:
            (package / "dist/skills/jevgrep").mkdir(parents=True, exist_ok=True)
            (package / updater.UPSTREAM_SKILL_REL).write_text(self.upstream(version), encoding="utf-8")

    def download(self, url: str, dest: Path) -> None:
        self.downloads.append(url)
        dest.write_bytes(_tarball_bytes(url.rsplit("jevgrep-", 1)[1].removesuffix(".tgz")))

    def _stage_dependencies(self, prefix: Path, version: str) -> None:
        """Place dependency dirs and the hidden lockfile npm writes; a ``None`` entry is on disk only."""
        packages: dict[str, dict[str, Any] | None] = {
            updater.PACKAGE_REL.as_posix(): {
                "version": version,
                "resolved": f"file:../.download-x/jevgrep-{version}.tgz",
                "integrity": _sri(_tarball_bytes(version)),
            },
            "node_modules/pyodide": PYODIDE,
            **self.staged,
        }
        for key in packages:
            (prefix / key).mkdir(parents=True, exist_ok=True)
            if key != updater.PACKAGE_REL.as_posix():
                (prefix / key / "package.json").write_text(json.dumps({"name": key.rsplit("node_modules/", 1)[1]}))
        if self.hidden_lockfile:
            lockfile = {"lockfileVersion": 3, "packages": {k: v for k, v in packages.items() if v is not None}}
            (prefix / updater.HIDDEN_LOCKFILE_REL).write_text(json.dumps(lockfile))

    def _leak(self, cmd: list[str], code: int, stdout: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, code, f"{stdout}{SECRET}\n", f"token={SECRET}\n")

    def run(self, cmd: list[str], timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        self.calls.append(cmd)
        if cmd[:2] == ["npm", "install"]:
            assert env is not None
            self.npm_envs.append(env)
            for key in ("NPM_CONFIG_USERCONFIG", "NPM_CONFIG_GLOBALCONFIG"):
                self.npm_config_texts.append(Path(env[key]).read_text(encoding="utf-8"))
            prefix = Path(cmd[cmd.index("--prefix") + 1])
            version = json.loads(Path(cmd[-1]).read_bytes())["version"]
            if version in self.npm_fails:
                return self._leak(cmd, 1)
            self._materialize(prefix / updater.PACKAGE_REL, version)
            self._stage_dependencies(prefix, version)
            return self._leak(cmd, 0)
        binary = Path(cmd[0])
        if not binary.exists():
            raise FileNotFoundError(cmd[0])
        version = _package_version(binary)
        if cmd[1:] == ["--version"]:
            return self._leak(cmd, 0, f"{version} ")
        if cmd[1:] == ["doctor"]:
            fails = version in self.doctor_fails or (cmd[0] == str(self.link) and version in self.link_doctor_fails)
            return self._leak(cmd, 1 if fails else 0)
        raise AssertionError(f"unexpected command {cmd}")

    def installs(self) -> list[list[str]]:
        return [cmd for cmd in self.calls if cmd[:2] == ["npm", "install"]]

    def active_version(self) -> str | None:
        return _package_version(self.link) if self.link.exists() else None


def _deps(host: FakeHost, packument: dict[str, Any], environ: dict[str, str] | None = None) -> updater.Deps:
    return updater.Deps(
        home=host.home,
        run=host.run,
        fetch_packument=lambda: packument,
        download=host.download,
        repo_root=REPO,
        environ=environ or {},
        now=lambda: "2026-09-28T00:00:00+00:00",
    )


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "home"


def _skill_paths(home: Path) -> list[Path]:
    return [home / rel for rel in updater.SKILL_TARGETS_REL]


def _log(home: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (home / updater.STATE_LOG_REL).read_text().splitlines()]


def _prefixes(home: Path) -> list[str]:
    root = home / updater.PREFIX_ROOT_REL
    return sorted(child.name.split("-", 1)[0] for child in root.iterdir()) if root.is_dir() else []


def _assert_skills_at(home: Path, version: str) -> None:
    for path in _skill_paths(home):
        assert f"auto-synced from @dzhng/jevgrep {version}," in path.read_text(encoding="utf-8")


def test_up_to_date_skips_install_and_syncs_skill(home: Path) -> None:
    host = FakeHost(home)
    code, record = updater.update(_deps(host, _packument("0.4.4")))
    assert code == 0
    assert host.installs() == [] and host.downloads == []
    assert record["action"] == "none" and record["result"] == "ok"
    _assert_skills_at(home, "0.4.4")
    assert _log(home)[0]["upstream_skill_sha256"] == record["upstream_skill_sha256"]


def test_newer_release_installs_verified_tarball_into_version_prefix_and_switches(home: Path) -> None:
    host = FakeHost(home)
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 0, record
    assert host.downloads == ["https://registry.npmjs.org/@dzhng/jevgrep/-/jevgrep-0.5.0.tgz"]
    [install] = host.installs()
    prefix = Path(install[3])
    assert prefix.parent == home / updater.PREFIX_ROOT_REL and prefix.name.startswith("0.5.0-")
    assert install[:3] == ["npm", "install", "--prefix"]
    assert install[4:9] == [
        "--ignore-scripts",
        "--no-package-lock",
        "--no-audit",
        "--no-fund",
        "--registry=https://registry.npmjs.org/",
    ]
    assert install[-1].endswith("jevgrep-0.5.0.tgz")
    staged = prefix / updater.PACKAGE_REL / "dist/bin/index.js"
    assert [str(staged), "doctor"] in host.calls
    assert host.calls.index([str(staged), "doctor"]) < host.calls.index([str(host.link), "doctor"])
    assert os.readlink(host.link) == str(staged)
    assert host.legacy.is_dir(), "the legacy npm -g install is never deleted"
    assert (record["current"], record["target"], record["action"], record["result"]) == (
        "0.4.4",
        "0.5.0",
        "install",
        "ok",
    )
    assert record["exit_codes"]["npm_install"] == 0 and record["exit_codes"]["switched_doctor"] == 0
    for path in _skill_paths(home):
        text = path.read_text(encoding="utf-8")
        assert "auto-synced from @dzhng/jevgrep 0.5.0" in text and "Upstream body for 0.5.0." in text


def test_first_install_without_jg_creates_link(home: Path) -> None:
    host = FakeHost(home, installed=None)
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 0 and record["current"] is None and record["result"] == "ok"
    assert host.active_version() == "0.5.0"
    _assert_skills_at(home, "0.5.0")


@pytest.mark.parametrize(
    ("meta", "reason"),
    [
        (_meta("0.5.0", attestations=False), "attestations"),
        (_meta("0.5.0", bin_jg=False), "bin.jg"),
        ({**_meta("0.5.0"), "hasInstallScript": True}, "hasInstallScript"),
        (_meta("0.5.0", tarball="https://mirror.example/jevgrep-0.5.0.tgz"), "dist.tarball"),
        (_meta("0.5.0", tarball="http://registry.npmjs.org/@dzhng/jevgrep/-/jevgrep-0.5.0.tgz"), "dist.tarball"),
        (_meta("0.5.0", integrity=None), "sha512"),
        (_meta("0.5.0", integrity="sha1-abc"), "sha512"),
    ],
)
def test_guard_blocks_install(home: Path, meta: dict[str, Any], reason: str) -> None:
    host = FakeHost(home)
    code, record = updater.update(_deps(host, _packument("0.5.0", {"0.5.0": meta})))
    assert code == 1
    assert host.installs() == [] and host.downloads == []
    assert record["action"] == "blocked" and reason in record["detail"]
    assert os.readlink(host.link) == LEGACY_LINK


NON_REGISTRY_SPECS = [
    "git+https://github.com/x/y.git",
    "git+ssh://git@github.com/x/y.git#abc",
    "git://github.com/x/y",
    "github:x/y",
    "gitlab:x/y",
    "bitbucket:x/y",
    "x/y",
    "https://example.com/y.tgz",
    "http://registry.npmjs.org/y/-/y-1.0.0.tgz",
    "file:../y",
    "link:../y",
    "../y",
    "y.tgz",
    "npm:other@1.0.0",
    "1.0.0#abc",
    "latest",
]


@pytest.mark.parametrize("spec", NON_REGISTRY_SPECS)
@pytest.mark.parametrize("field", updater.DEPENDENCY_FIELDS)
def test_non_registry_dependency_spec_is_refused_before_npm(home: Path, field: str, spec: str) -> None:
    host = FakeHost(home)
    meta = {**_meta("0.5.0"), field: {"pyodide": "0.25.1", "y": spec}}
    code, record = updater.update(_deps(host, _packument("0.5.0", {"0.5.0": meta})))
    assert code == 1
    assert host.installs() == [] and host.downloads == []
    assert (record["action"], record["result"], record["detail"]) == ("blocked", "failed", "dependency_source_refused")
    assert os.readlink(host.link) == LEGACY_LINK


@pytest.mark.parametrize("bundle", [{"bundleDependencies": ["y"]}, {"bundledDependencies": True}])
def test_bundled_dependencies_are_refused_before_npm(home: Path, bundle: dict[str, Any]) -> None:
    host = FakeHost(home)
    meta = {**_meta("0.5.0"), "dependencies": {"y": "1.0.0"}, **bundle}
    code, record = updater.update(_deps(host, _packument("0.5.0", {"0.5.0": meta})))
    assert code == 1 and host.installs() == [] and host.downloads == []
    assert record["detail"] == "dependency_source_refused"


@pytest.mark.parametrize(
    "spec", ["0.25.1", "^1.2.3", "~1.2", ">=1.0.0 <2.0.0", "1.x || >=2.5.0 || 5.0.0 - 7.2.3", "*", "", "1.0.0-rc.1"]
)
def test_plain_semver_dependency_ranges_pass_the_guard(spec: str) -> None:
    meta = {**_meta("0.5.0"), "dependencies": {"y": spec}, "bundleDependencies": []}
    assert updater.guard_failures({"versions": {"0.5.0": meta}}, "0.5.0") == []


@pytest.mark.parametrize(
    ("staged", "hidden_lockfile"),
    [
        ({"node_modules/evil": {"resolved": "git+ssh://git@github.com/x/evil.git#abc", "integrity": "sha512-x"}}, True),
        ({"node_modules/evil": {"resolved": "https://evil.example/evil-1.0.0.tgz", "integrity": "sha512-x"}}, True),
        (
            {"node_modules/evil": {"resolved": "http://registry.npmjs.org/evil/-/evil-1.0.0.tgz", "integrity": "x"}},
            True,
        ),
        ({"node_modules/pyodide/node_modules/evil": {"resolved": "file:../evil", "integrity": "sha512-x"}}, True),
        ({"node_modules/evil": {"resolved": "../evil", "link": True}}, True),
        ({"node_modules/evil": {"resolved": "https://registry.npmjs.org/evil/-/evil-1.0.0.tgz"}}, True),
        ({"node_modules/@scope/evil": None}, True),
        ({}, False),
    ],
    ids=["git", "other-host", "http", "nested-file", "link", "no-integrity", "not-in-lockfile", "no-lockfile"],
)
def test_non_registry_staged_package_never_switches_and_removes_prefix(
    home: Path, staged: dict[str, dict[str, Any] | None], hidden_lockfile: bool
) -> None:
    host = FakeHost(home, staged=staged, hidden_lockfile=hidden_lockfile)
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert len(host.installs()) == 1
    assert (record["result"], record["detail"]) == ("failed", "dependency_source_refused")
    assert os.readlink(host.link) == LEGACY_LINK
    assert _prefixes(home) == []
    staged_prefix = updater.PREFIX_ROOT_REL.as_posix()
    assert not any(staged_prefix in cmd[0] for cmd in host.calls if cmd[0] != "npm"), "nothing staged ever ran"
    _assert_skills_at(home, "0.4.4")


def test_registry_only_staged_tree_passes_including_nested_and_scoped(tmp_path: Path) -> None:
    packages = {
        updater.PACKAGE_REL.as_posix(): {"resolved": "file:../.download-x/jevgrep.tgz"},
        "node_modules/pyodide": PYODIDE,
        "node_modules/@types/node": PYODIDE,
        "node_modules/pyodide/node_modules/ws": PYODIDE,
    }
    for key in packages:
        (tmp_path / key).mkdir(parents=True)
    (tmp_path / "node_modules/.bin").mkdir()
    (tmp_path / updater.HIDDEN_LOCKFILE_REL).write_text(json.dumps({"lockfileVersion": 3, "packages": packages}))
    assert updater.staged_sources_from_registry(tmp_path)
    (tmp_path / "node_modules/pyodide/node_modules/stray").mkdir()
    assert not updater.staged_sources_from_registry(tmp_path)


@pytest.mark.parametrize("script", ["preinstall", "install", "postinstall"])
def test_install_script_blocks_install(home: Path, script: str) -> None:
    host = FakeHost(home)
    meta = _meta("0.5.0", scripts={script: "node x.js"})
    code, record = updater.update(_deps(host, _packument("0.5.0", {"0.5.0": meta})))
    assert code == 1
    assert host.installs() == []
    assert script in record["detail"]


def test_integrity_mismatch_never_installs(home: Path) -> None:
    host = FakeHost(home)
    meta = _meta("0.5.0", integrity=_sri(b"other bytes"))
    code, record = updater.update(_deps(host, _packument("0.5.0", {"0.5.0": meta})))
    assert code == 1
    assert host.downloads and host.installs() == []
    assert record["result"] == "failed" and "tarball_integrity_mismatch" in record["detail"]
    assert os.readlink(host.link) == LEGACY_LINK
    assert _prefixes(home) == []


def test_staged_doctor_failure_never_switches(home: Path) -> None:
    host = FakeHost(home, doctor_fails=frozenset({"0.5.0"}))
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert record["result"] == "failed" and "staged_doctor_failed" in record["detail"]
    assert os.readlink(host.link) == LEGACY_LINK
    assert [str(host.link), "doctor"] not in host.calls
    assert _prefixes(home) == []
    _assert_skills_at(home, "0.4.4")


def test_missing_upstream_skill_never_switches(home: Path) -> None:
    host = FakeHost(home, no_skill=frozenset({"0.5.0"}))
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert "upstream_skill_missing" in record["detail"]
    assert os.readlink(host.link) == LEGACY_LINK
    _assert_skills_at(home, "0.4.4")


def test_post_switch_failure_restores_previous_link_without_download(home: Path) -> None:
    host = FakeHost(home, link_doctor_fails=frozenset({"0.5.0"}))
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert record["result"] == "rolled_back"
    assert "switched_doctor_failed" in record["detail"]
    assert len(host.downloads) == 1 and len(host.installs()) == 1
    assert os.readlink(host.link) == LEGACY_LINK
    assert record["exit_codes"]["rollback_version"] == 0 and record["exit_codes"]["rollback_doctor"] == 0
    assert _prefixes(home) == []
    _assert_skills_at(home, "0.4.4")


def test_rollback_that_does_not_pass_doctor_is_reported(home: Path) -> None:
    host = FakeHost(home, link_doctor_fails=frozenset({"0.5.0", "0.4.4"}))
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert record["result"] == "rollback_failed"
    assert "rollback_doctor_failed" in record["detail"]
    assert os.readlink(host.link) == LEGACY_LINK


def test_skill_write_failure_after_switch_rolls_back_cli_and_skill(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    host = FakeHost(home)
    for path in _skill_paths(home):
        path.parent.mkdir(parents=True)
        path.write_text("previous skill\n", encoding="utf-8")
    real_write = updater._atomic_write

    def flaky(target: Path, content: str) -> None:
        if target == home / updater.SKILL_TARGETS_REL[1] and "0.5.0" in content:
            raise OSError("disk full")
        real_write(target, content)

    monkeypatch.setattr(updater, "_atomic_write", flaky)
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert record["result"] == "rolled_back" and "skill_write_failed" in record["detail"]
    assert os.readlink(host.link) == LEGACY_LINK
    for path in _skill_paths(home):
        assert "0.5.0" not in path.read_text(encoding="utf-8")
    _assert_skills_at(home, "0.4.4")


def test_write_skills_restores_the_copy_already_written(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first, second = _skill_paths(home)
    for path in (first, second):
        path.parent.mkdir(parents=True)
        path.write_text("old\n", encoding="utf-8")
    real_write = updater._atomic_write

    def flaky(target: Path, content: str) -> None:
        if target == second and content == "new\n":
            raise OSError("disk full")
        real_write(target, content)

    monkeypatch.setattr(updater, "_atomic_write", flaky)
    with pytest.raises(updater.StepFailed, match=r"^skill_write_failed$"):
        updater.write_skills(home, "new\n")
    assert first.read_text() == "old\n" and second.read_text() == "old\n"


def test_failed_skill_restore_is_reported_and_healed_by_the_next_run(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    host = FakeHost(home)
    first, second = _skill_paths(home)
    real_write = updater._atomic_write
    new_written = False

    def broken_disk(target: Path, content: str) -> None:
        nonlocal new_written
        if new_written or (target == second and "0.5.0" in content):
            raise OSError("disk full")
        real_write(target, content)
        new_written = "0.5.0" in content

    monkeypatch.setattr(updater, "_atomic_write", broken_disk)
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert "skill_restore_failed" in record["detail"] and record["upstream_skill_sha256"] is None
    assert host.active_version() == "0.4.4"
    assert "@dzhng/jevgrep 0.5.0," in first.read_text(encoding="utf-8"), "the mismatch this test heals"

    monkeypatch.setattr(updater, "_atomic_write", real_write)
    code, record = updater.update(_deps(host, _packument("0.4.4")))
    assert code == 0 and record["action"] == "none"
    assert host.active_version() == "0.4.4"
    _assert_skills_at(home, "0.4.4")


def test_every_run_first_resyncs_skills_from_the_active_package(home: Path) -> None:
    host = FakeHost(home, link_doctor_fails=frozenset({"0.5.0"}))
    for path in _skill_paths(home):
        path.parent.mkdir(parents=True)
        path.write_text("stale skill from another version\n", encoding="utf-8")
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1 and record["result"] == "rolled_back"
    _assert_skills_at(home, "0.4.4")


def test_upgrades_keep_only_active_and_previous_prefix(home: Path) -> None:
    host = FakeHost(home)
    for version in ("0.5.0", "0.6.0", "0.7.0"):
        code, record = updater.update(_deps(host, _packument(version)))
        assert code == 0 and record["result"] == "ok", record
    assert _prefixes(home) == ["0.6.0", "0.7.0"]
    assert host.active_version() == "0.7.0"
    assert host.legacy.is_dir()


def test_prune_rereads_the_active_link_and_keeps_active_and_previous(tmp_path: Path) -> None:
    root = tmp_path / "prefixes"
    for name in ("a", "b", "c"):
        (root / name / "bin").mkdir(parents=True)
    link = tmp_path / "jg"
    os.symlink(str(root / "c/bin"), link)
    updater.prune_prefixes(root, link, str(root / "a/bin"))
    assert sorted(child.name for child in root.iterdir()) == ["a", "c"]
    link.unlink()
    updater.prune_prefixes(root, link, None)
    assert sorted(child.name for child in root.iterdir()) == ["a", "c"], "no active link: prune nothing"


@pytest.mark.parametrize("dry_run", [False, True])
def test_run_while_lock_is_held_does_nothing(home: Path, dry_run: bool) -> None:
    host = FakeHost(home)
    lock_path = home / updater.LOCK_REL
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as held:
        before = {path: path.read_bytes() for path in home.rglob("*") if path.is_file()}
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        code, record = updater.update(_deps(host, _packument("0.5.0")), dry_run=dry_run)
    assert code == 0
    assert (record["action"], record["result"]) == ("locked", "skipped")
    assert host.calls == [] and host.downloads == []
    assert {path: path.read_bytes() for path in home.rglob("*") if path.is_file()} == before
    assert os.readlink(host.link) == LEGACY_LINK


@pytest.mark.parametrize(
    "host_kwargs",
    [
        {"npm_fails": frozenset({"0.5.0"})},
        {"doctor_fails": frozenset({"0.5.0"})},
        {"link_doctor_fails": frozenset({"0.5.0", "0.4.4"})},
        {},
    ],
)
def test_child_output_never_reaches_records(
    home: Path, capsys: pytest.CaptureFixture[str], host_kwargs: dict[str, frozenset[str]]
) -> None:
    host = FakeHost(home, **host_kwargs)
    for argv in (["--json"], []):
        updater.main(argv, _deps(host, _packument("0.5.0")))
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    assert SECRET not in (home / updater.STATE_LOG_REL).read_text(encoding="utf-8")


def test_hold_version_overrides_latest(home: Path) -> None:
    host = FakeHost(home)
    code, record = updater.update(_deps(host, _packument("0.6.0"), {"JEVGREP_HOLD_VERSION": "0.5.0"}))
    assert code == 0
    assert host.downloads == ["https://registry.npmjs.org/@dzhng/jevgrep/-/jevgrep-0.5.0.tgz"]
    assert record["target"] == "0.5.0" and host.active_version() == "0.5.0"


def test_hold_version_must_be_exact(home: Path) -> None:
    host = FakeHost(home)
    code, record = updater.update(_deps(host, _packument("0.5.0"), {"JEVGREP_HOLD_VERSION": "latest"}))
    assert code == 1
    assert host.installs() == []
    assert record["action"] == "resolve" and record["detail"] == "invalid_target"


def test_synced_file_is_overlay_marker_and_upstream_body(home: Path) -> None:
    host = FakeHost(home)
    updater.update(_deps(host, _packument("0.4.4")))
    expected = (
        OVERLAY
        + "\n## Upstream skill (auto-synced from @dzhng/jevgrep 0.4.4, overlay above wins)\n"
        + "\n# Jevgrep\n\nUpstream body for 0.4.4.\n"
    )
    for path in _skill_paths(home):
        assert path.read_text(encoding="utf-8") == expected
        assert path.stat().st_mode & 0o777 == 0o644
    assert "description: upstream" not in expected


def test_writes_only_prefixes_link_skills_and_state_log(home: Path) -> None:
    host = FakeHost(home)
    before = {path for path in home.rglob("*") if path.is_file() and not path.is_symlink()}
    updater.update(_deps(host, _packument("0.5.0")))
    new = {path.relative_to(home) for path in home.rglob("*") if path.is_file() and not path.is_symlink()} - {
        path.relative_to(home) for path in before
    }
    outside_prefixes = {rel for rel in new if not rel.is_relative_to(updater.PREFIX_ROOT_REL)}
    assert outside_prefixes == {*updater.SKILL_TARGETS_REL, updater.STATE_LOG_REL, updater.LOCK_REL}
    assert not list((home / updater.PREFIX_ROOT_REL).glob(".download-*"))


def test_dry_run_neither_downloads_installs_nor_writes(home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    host = FakeHost(home)
    before = sorted(home.rglob("*"))
    assert updater.main(["--dry-run", "--json"], _deps(host, _packument("0.5.0"))) == 0
    record = json.loads(capsys.readouterr().out)
    assert (record["action"], record["result"], record["dry_run"]) == ("install", "dry_run", True)
    assert host.installs() == [] and host.downloads == []
    lock = home / updater.LOCK_REL
    assert set(home.rglob("*")) - set(before) == {lock, lock.parent, lock.parent.parent}
    assert (home / updater.LOCK_REL).read_bytes() == b""


def test_registry_failure_keeps_current_and_still_syncs(home: Path) -> None:
    host = FakeHost(home)
    deps = _deps(host, {})

    def offline() -> dict[str, Any]:
        raise OSError("network unreachable")

    deps.fetch_packument = offline
    code, record = updater.update(deps)
    assert code == 1
    assert host.installs() == []
    assert record["detail"] == "registry_unreachable"
    _assert_skills_at(home, "0.4.4")


def test_regular_file_at_bin_path_is_not_replaced(home: Path) -> None:
    host = FakeHost(home, installed=None)
    host.link.parent.mkdir(parents=True)
    host.link.write_text("#!/bin/sh\n")
    code, record = updater.update(_deps(host, _packument("0.5.0")))
    assert code == 1
    assert "bin_not_symlink" in record["detail"] and host.installs() == []
    assert host.link.read_text() == "#!/bin/sh\n"


def test_download_refuses_non_registry_urls(tmp_path: Path) -> None:
    for url in ("https://mirror.example/jevgrep.tgz", "http://registry.npmjs.org/x.tgz"):
        with pytest.raises(OSError):
            updater._download(url, tmp_path / "t.tgz")


class _FakeRegistry(urllib.request.HTTPSHandler):
    """Answers every HTTPS request locally with one fixed status, Location and body."""

    def __init__(self, status: int, body: bytes = b"{}") -> None:
        super().__init__()
        self.status = status
        self.body = body

    def https_open(self, req: urllib.request.Request) -> urllib.response.addinfourl:
        headers = email.message.Message()
        headers["Location"] = "https://registry.npmjs.org/elsewhere"
        response = urllib.response.addinfourl(io.BytesIO(self.body), headers, req.full_url, code=self.status)
        response.msg = "fake"
        return response


def test_module_opener_follows_no_redirect() -> None:
    redirectors = [h for h in updater._OPENER.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
    assert redirectors and all(isinstance(h, updater._RefuseRedirect) for h in redirectors)


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirects_are_refused_for_metadata_and_tarball(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    monkeypatch.setattr(updater, "_OPENER", urllib.request.build_opener(updater._RefuseRedirect, _FakeRegistry(status)))
    with pytest.raises(urllib.error.HTTPError, match="redirect refused"):
        updater._fetch_packument()
    with pytest.raises(urllib.error.HTTPError, match="redirect refused"):
        updater._download("https://registry.npmjs.org/@dzhng/jevgrep/-/jevgrep-0.5.0.tgz", tmp_path / "t.tgz")


def test_size_caps_apply_to_metadata_and_tarball(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert (updater.MAX_METADATA_BYTES, updater.MAX_TARBALL_BYTES) == (8 * 1024 * 1024, 64 * 1024 * 1024)
    monkeypatch.setattr(
        updater, "_OPENER", urllib.request.build_opener(updater._RefuseRedirect, _FakeRegistry(200, b"x" * 11))
    )
    monkeypatch.setattr(updater, "MAX_METADATA_BYTES", 10)
    monkeypatch.setattr(updater, "MAX_TARBALL_BYTES", 10)
    with pytest.raises(OSError, match="size cap"):
        updater._fetch_packument()
    with pytest.raises(OSError, match="size cap"):
        updater._download("https://registry.npmjs.org/@dzhng/jevgrep/-/jevgrep-0.5.0.tgz", tmp_path / "t.tgz")


def test_redirected_registry_is_a_registry_failure(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(updater, "_OPENER", urllib.request.build_opener(updater._RefuseRedirect, _FakeRegistry(302)))
    host = FakeHost(home)
    deps = _deps(host, {})
    deps.fetch_packument = updater._fetch_packument
    code, record = updater.update(deps)
    assert code == 1 and record["detail"] == "registry_unreachable" and host.installs() == []


def test_npm_runs_with_isolated_config(home: Path) -> None:
    host = FakeHost(home)
    evil = "https://evil.example/"
    (home / ".npmrc").write_text(f"@dzhng:registry={evil}\nregistry={evil}\n", encoding="utf-8")
    environ = {
        "PATH": "/usr/bin",
        "HOME": str(home),
        "npm_config_@dzhng:registry": evil,
        "NPM_CONFIG_REGISTRY": evil,
        "npm_config_userconfig": str(home / ".npmrc"),
        "Npm_Config_GlobalConfig": str(home / ".npmrc"),
    }
    code, record = updater.update(_deps(host, _packument("0.5.0"), environ))
    assert code == 0, record
    [install], [env] = host.installs(), host.npm_envs
    assert "--no-package-lock" in install and "--ignore-scripts" in install
    assert f"--registry={updater.REGISTRY_BASE}" in install
    assert not any("evil" in arg for arg in install)
    assert not any("evil" in value for value in env.values())
    npm_keys = {key for key in env if key.lower().startswith("npm_config_")}
    assert npm_keys == {"NPM_CONFIG_USERCONFIG", "NPM_CONFIG_GLOBALCONFIG"}
    assert Path(env["NPM_CONFIG_USERCONFIG"]) != home / ".npmrc"
    assert host.npm_config_texts == ["", ""]
    assert env["PATH"] == "/usr/bin"


def test_help_meets_cli_standard() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/tools/jevgrep_update.py"), "--help"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    for required in ("Examples:", "Outputs:", "Exit codes:", "Related:", "--dry-run", "--json"):
        assert required in result.stdout


def test_jevgrep_systemd_templates_verify(tmp_path: Path) -> None:
    analyzer = shutil.which("systemd-analyze")
    if analyzer is None:
        pytest.skip("systemd-analyze unavailable")
    source = REPO / "packaging/systemd"
    names = ("learn-ukrainian-jevgrep-update.service", "learn-ukrainian-jevgrep-update.timer")
    for name in names:
        rendered = (source / name).read_text(encoding="utf-8")
        rendered = rendered.replace("@REPO_ROOT@", str(REPO)).replace("@PYTHON@", sys.executable)
        (tmp_path / name).write_text(rendered, encoding="utf-8")
    result = subprocess.run(
        [analyzer, "verify", *(str(tmp_path / name) for name in names)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    timer = (source / "learn-ukrainian-jevgrep-update.timer").read_text(encoding="utf-8")
    assert "RandomizedDelaySec=20min" in timer and "Persistent=true" in timer
