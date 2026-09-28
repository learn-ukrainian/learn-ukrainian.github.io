"""Host updater for the jevgrep CLI and its user-level skill (#9134).

Every subprocess and registry call is injected: no network, no npm, temp HOME.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.tools import jevgrep_update as updater

REPO = Path(__file__).resolve().parents[1]
OVERLAY = (REPO / updater.OVERLAY_REL).read_text(encoding="utf-8")


def _meta(*, attestations: bool = True, scripts: dict[str, str] | None = None, bin_jg: bool = True) -> dict[str, Any]:
    dist: dict[str, Any] = {"tarball": "https://example.invalid/t.tgz"}
    if attestations:
        dist["attestations"] = {"provenance": {"predicateType": "https://slsa.dev/provenance/v1"}}
    return {
        "scripts": scripts or {"test": "bun test"},
        "bin": {"jg": "dist/bin/index.js"} if bin_jg else {},
        "dist": dist,
    }


def _packument(latest: str, overrides: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    versions = {"0.4.4": _meta(), latest: _meta(), **(overrides or {})}
    return {"dist-tags": {"latest": latest}, "versions": versions}


class FakeHost:
    """A fake `jg` + `npm` whose installs rewrite a fake package directory."""

    def __init__(self, root: Path, installed: str | None = "0.4.4", doctor_fails: frozenset[str] = frozenset()):
        self.package = root / "npm" / "lib" / "node_modules" / "@dzhng" / "jevgrep"
        self.installed = installed
        self.doctor_fails = doctor_fails
        self.calls: list[list[str]] = []
        if installed:
            self._materialize(installed)

    def upstream(self, version: str) -> str:
        return f"---\nname: jevgrep\ndescription: upstream\n---\n\n# Jevgrep\n\nUpstream body for {version}.\n"

    def _materialize(self, version: str) -> None:
        (self.package / "dist/skills/jevgrep").mkdir(parents=True, exist_ok=True)
        (self.package / "package.json").write_text(json.dumps({"name": updater.PACKAGE, "version": version}))
        (self.package / updater.UPSTREAM_SKILL_REL).write_text(self.upstream(version), encoding="utf-8")

    def run(self, cmd: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
        self.calls.append(cmd)
        if cmd == ["jg", "--version"]:
            if self.installed is None:
                raise FileNotFoundError("jg")
            return subprocess.CompletedProcess(cmd, 0, f"{self.installed}\n", "")
        if cmd == ["jg", "doctor"]:
            code = 1 if self.installed in self.doctor_fails else 0
            return subprocess.CompletedProcess(cmd, code, "", "doctor failed" if code else "")
        if cmd[:2] == ["npm", "install"]:
            version = cmd[-1].rsplit("@", 1)[1]
            self.installed = version
            self._materialize(version)
            return subprocess.CompletedProcess(cmd, 0, "", "")
        raise AssertionError(f"unexpected command {cmd}")

    def installs(self) -> list[list[str]]:
        return [cmd for cmd in self.calls if cmd[:2] == ["npm", "install"]]


def _deps(tmp_path: Path, host: FakeHost, packument: dict[str, Any], environ: dict[str, str] | None = None):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return updater.Deps(
        home=home,
        run=host.run,
        fetch_packument=lambda: packument,
        package_dir=lambda: host.package if host.installed else None,
        repo_root=REPO,
        environ=environ or {},
        now=lambda: "2026-09-28T00:00:00+00:00",
    )


def _skill_paths(home: Path) -> list[Path]:
    return [home / rel for rel in updater.SKILL_TARGETS_REL]


def _log(home: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (home / updater.STATE_LOG_REL).read_text().splitlines()]


def test_up_to_date_skips_install_and_syncs_skill(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.4.4"))
    code, record = updater.update(deps)
    assert code == 0
    assert host.installs() == []
    assert record["action"] == "none" and record["result"] == "ok"
    for path in _skill_paths(deps.home):
        assert "Upstream body for 0.4.4." in path.read_text(encoding="utf-8")
    assert _log(deps.home)[0]["upstream_skill_sha256"] == record["upstream_skill_sha256"]


def test_newer_release_installs_exact_version_verifies_and_syncs(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.5.0"))
    code, record = updater.update(deps)
    assert code == 0
    assert host.installs() == [
        ["npm", "install", "-g", "--ignore-scripts", "--no-audit", "--no-fund", "@dzhng/jevgrep@0.5.0"]
    ]
    assert ["jg", "doctor"] in host.calls
    assert (record["current"], record["target"], record["action"], record["result"]) == (
        "0.4.4",
        "0.5.0",
        "install",
        "ok",
    )
    for path in _skill_paths(deps.home):
        text = path.read_text(encoding="utf-8")
        assert "auto-synced from @dzhng/jevgrep 0.5.0" in text
        assert "Upstream body for 0.5.0." in text


def test_missing_attestations_blocks_install(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.5.0", {"0.5.0": _meta(attestations=False)}))
    code, record = updater.update(deps)
    assert code == 1
    assert host.installs() == []
    assert record["action"] == "blocked"
    assert "attestations" in record["detail"]
    assert host.installed == "0.4.4"


@pytest.mark.parametrize("script", ["preinstall", "install", "postinstall"])
def test_install_script_blocks_install(tmp_path: Path, script: str) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.5.0", {"0.5.0": _meta(scripts={script: "node x.js"})}))
    code, record = updater.update(deps)
    assert code == 1
    assert host.installs() == []
    assert script in record["detail"]


def test_missing_bin_blocks_install(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.5.0", {"0.5.0": _meta(bin_jg=False)}))
    code, record = updater.update(deps)
    assert code == 1
    assert host.installs() == []
    assert "bin.jg" in record["detail"]


def test_doctor_failure_rolls_back_to_previous_version(tmp_path: Path) -> None:
    host = FakeHost(tmp_path, doctor_fails=frozenset({"0.5.0"}))
    deps = _deps(tmp_path, host, _packument("0.5.0"))
    code, record = updater.update(deps)
    assert code == 1
    assert [cmd[-1] for cmd in host.installs()] == ["@dzhng/jevgrep@0.5.0", "@dzhng/jevgrep@0.4.4"]
    assert host.installed == "0.4.4"
    assert record["result"] == "rolled_back"
    assert "jg doctor" in record["detail"]
    for path in _skill_paths(deps.home):
        assert "auto-synced from @dzhng/jevgrep 0.4.4" in path.read_text(encoding="utf-8")


def test_hold_version_overrides_latest(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    packument = _packument("0.6.0", {"0.5.0": _meta()})
    deps = _deps(tmp_path, host, packument, {"JEVGREP_HOLD_VERSION": "0.5.0"})
    code, record = updater.update(deps)
    assert code == 0
    assert [cmd[-1] for cmd in host.installs()] == ["@dzhng/jevgrep@0.5.0"]
    assert record["target"] == "0.5.0"


def test_hold_version_must_be_exact(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.5.0"), {"JEVGREP_HOLD_VERSION": "latest"})
    code, record = updater.update(deps)
    assert code == 1
    assert host.installs() == []
    assert record["action"] == "resolve"


def test_synced_file_is_overlay_marker_and_upstream_body(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.4.4"))
    updater.update(deps)
    expected = (
        OVERLAY
        + "\n## Upstream skill (auto-synced from @dzhng/jevgrep 0.4.4, overlay above wins)\n"
        + "\n# Jevgrep\n\nUpstream body for 0.4.4.\n"
    )
    for path in _skill_paths(deps.home):
        assert path.read_text(encoding="utf-8") == expected
        assert path.stat().st_mode & 0o777 == 0o644
    assert "description: upstream" not in expected


def test_writes_nothing_outside_skill_paths_and_state_log(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.5.0"))
    updater.update(deps)
    written = {path.relative_to(deps.home) for path in deps.home.rglob("*") if path.is_file()}
    assert written == {*updater.SKILL_TARGETS_REL, updater.STATE_LOG_REL}


def test_dry_run_neither_installs_nor_writes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, _packument("0.5.0"))
    assert updater.main(["--dry-run", "--json"], deps) == 0
    record = json.loads(capsys.readouterr().out)
    assert (record["action"], record["result"], record["dry_run"]) == ("install", "dry_run", True)
    assert host.installs() == []
    assert list(deps.home.rglob("*")) == []


def test_registry_failure_keeps_current_and_still_syncs(tmp_path: Path) -> None:
    host = FakeHost(tmp_path)
    deps = _deps(tmp_path, host, {})

    def offline() -> dict[str, Any]:
        raise OSError("network unreachable")

    deps.fetch_packument = offline
    code, record = updater.update(deps)
    assert code == 1
    assert host.installs() == []
    assert "network unreachable" in record["detail"]
    assert all(path.is_file() for path in _skill_paths(deps.home))


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
