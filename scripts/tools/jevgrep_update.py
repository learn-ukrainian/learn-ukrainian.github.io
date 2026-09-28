#!/usr/bin/env python3
"""Keep the host's jevgrep CLI at npm ``latest`` and sync its user-level skill (#9134).

Run by ``learn-ukrainian-jevgrep-update.timer`` from the primary checkout. It
holds an exclusive lock for the whole run, then rebuilds both skill copies from
the active package so any earlier CLI/skill mismatch heals. It resolves
``latest`` (or ``JEVGREP_HOLD_VERSION``) from the public npm registry to an
exact version and checks the supply-chain guards on that metadata. It then
downloads the tarball named by the same metadata (no redirects, size-capped),
verifies its sha512 against ``dist.integrity``, and installs that local file
into its own version prefix with npm configuration isolated from the host. The
staged ``jg`` and both skill texts are checked before ``~/.local/bin/jg`` is
switched atomically; any later failure restores the previous link and skill
files without a download. Child output is never recorded: the state log,
``--json`` and the journal carry exit codes and fixed failure classifications
only. Stdlib only.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PACKAGE = "@dzhng/jevgrep"
REGISTRY_HOST = "registry.npmjs.org"
REGISTRY_BASE = f"https://{REGISTRY_HOST}/"
REGISTRY_URL = f"{REGISTRY_BASE}@dzhng%2fjevgrep"
HOLD_ENV = "JEVGREP_HOLD_VERSION"
REPO_ROOT = Path(__file__).resolve().parents[2]
OVERLAY_REL = Path("agents_extensions/shared/skills/jevgrep/SKILL.md")
SKILL_TARGETS_REL = (
    Path(".claude/skills/jevgrep/SKILL.md"),
    Path(".agents/skills/jevgrep/SKILL.md"),
)
BIN_LINK_REL = Path(".local/bin/jg")
PREFIX_ROOT_REL = Path(".local/share/learn-ukrainian/jevgrep")
STATE_LOG_REL = Path(".local/state/learn-ukrainian/jevgrep-update.jsonl")
LOCK_REL = Path(".local/state/learn-ukrainian/jevgrep-update.lock")
PACKAGE_REL = Path("node_modules/@dzhng/jevgrep")
UPSTREAM_SKILL_REL = Path("dist/skills/jevgrep/SKILL.md")
FORBIDDEN_SCRIPTS = ("preinstall", "install", "postinstall")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")
KEEP_PREFIXES = 2
MAX_METADATA_BYTES = 8 * 1024 * 1024
MAX_TARBALL_BYTES = 64 * 1024 * 1024
INSTALL_TIMEOUT_S = 900
DOCTOR_TIMEOUT_S = 180
VERSION_TIMEOUT_S = 30

Runner = Callable[..., subprocess.CompletedProcess[str]]


class StepFailed(Exception):
    """A step failed; ``args[0]`` is a fixed classification, never child output."""


def _run(cmd: list[str], timeout: int, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout, env=env)


class _RefuseRedirect(urllib.request.HTTPRedirectHandler):
    """Every 30x is an error: registry traffic never follows a redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


_OPENER = urllib.request.build_opener(_RefuseRedirect)


def is_registry_url(url: object) -> bool:
    if not isinstance(url, str):
        return False
    parts = urllib.parse.urlsplit(url)
    return parts.scheme == "https" and parts.hostname == REGISTRY_HOST and parts.port is None


def _fetch(url: str, limit: int, sink: Callable[[bytes], object], *, accept: str, timeout: int) -> None:
    """Stream ``url`` into ``sink``: public registry over HTTPS only, no redirects, at most ``limit`` bytes."""
    if not is_registry_url(url):
        raise OSError("url is not on the public registry")
    request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "learn-ukrainian-jevgrep-update"})
    with _OPENER.open(request, timeout=timeout) as response:
        if not is_registry_url(response.geturl()):
            raise OSError("response left the public registry")
        total = 0
        while chunk := response.read(1 << 16):
            total += len(chunk)
            if total > limit:
                raise OSError("response exceeds size cap")
            sink(chunk)


def _fetch_packument() -> dict[str, Any]:
    body = bytearray()
    _fetch(REGISTRY_URL, MAX_METADATA_BYTES, body.extend, accept="application/json", timeout=30)
    return json.loads(body)


def _download(url: str, dest: Path) -> None:
    with dest.open("wb") as handle:
        _fetch(url, MAX_TARBALL_BYTES, handle.write, accept="application/octet-stream", timeout=120)


def npm_env(environ: Mapping[str, str], empty_config: Path) -> dict[str, str]:
    """The caller's environment without any npm setting; user and global config point at an empty file."""
    env = {key: value for key, value in environ.items() if not key.lower().startswith("npm_config_")}
    env["NPM_CONFIG_USERCONFIG"] = str(empty_config)
    env["NPM_CONFIG_GLOBALCONFIG"] = str(empty_config)
    return env


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class Deps:
    home: Path = field(default_factory=Path.home)
    run: Runner = _run
    fetch_packument: Callable[[], dict[str, Any]] = _fetch_packument
    download: Callable[[str, Path], None] = _download
    repo_root: Path = REPO_ROOT
    environ: Mapping[str, str] = field(default_factory=lambda: os.environ)
    now: Callable[[], str] = _utc_now


@dataclass
class Run:
    """Everything one run records. Child stdout/stderr never enter it."""

    deps: Deps
    failures: list[str] = field(default_factory=list)
    exit_codes: dict[str, int] = field(default_factory=dict)
    skill_sha256: str | None = None

    def call(self, step: str, cmd: list[str], timeout: int, env: Mapping[str, str] | None = None) -> tuple[int, str]:
        """Run a child; record its exit code under ``step``; return code and stdout for parsing only."""
        try:
            result = self.deps.run(cmd, timeout, env=env)
            code, stdout = result.returncode, result.stdout or ""
        except OSError:
            code, stdout = 127, ""
        except subprocess.TimeoutExpired:
            code, stdout = 124, ""
        self.exit_codes[step] = code
        return code, stdout

    def version_of(self, step: str, binary: Path) -> str | None:
        code, stdout = self.call(step, [str(binary), "--version"], VERSION_TIMEOUT_S)
        match = VERSION_RE.search(stdout) if code == 0 else None
        return match.group(0) if match else None

    def verify(self, label: str, binary: Path, version: str) -> None:
        if self.version_of(f"{label}_version", binary) != version:
            raise StepFailed(f"{label}_version_mismatch")
        code, _ = self.call(f"{label}_doctor", [str(binary), "doctor"], DOCTOR_TIMEOUT_S)
        if code != 0:
            raise StepFailed(f"{label}_doctor_failed")


def resolve_target(packument: Mapping[str, Any], environ: Mapping[str, str]) -> str:
    target = environ.get(HOLD_ENV, "").strip() or packument["dist-tags"]["latest"]
    if not isinstance(target, str) or not VERSION_RE.fullmatch(target):
        raise ValueError("target is not an exact version")
    return target


def guard_failures(packument: Mapping[str, Any], version: str) -> list[str]:
    meta = packument.get("versions", {}).get(version)
    if not isinstance(meta, dict):
        return [f"{version} is not in the registry"]
    failures = []
    dist = meta.get("dist") or {}
    if not dist.get("attestations"):
        failures.append("no npm provenance attestations")
    if not is_registry_url(dist.get("tarball")):
        failures.append(f"dist.tarball is not on https://{REGISTRY_HOST}/")
    if _sri_sha512(dist.get("integrity")) is None:
        failures.append("dist.integrity has no sha512")
    scripts = meta.get("scripts") or {}
    failures.extend(f"install script {name!r} present" for name in FORBIDDEN_SCRIPTS if name in scripts)
    if meta.get("hasInstallScript"):
        failures.append("registry marks hasInstallScript")
    bins = meta.get("bin")
    if not isinstance(bins, dict) or not bins.get("jg"):
        failures.append("bin.jg missing")
    return failures


def _sri_sha512(integrity: object) -> str | None:
    if not isinstance(integrity, str):
        return None
    for token in integrity.split():
        algorithm, _, digest = token.partition("-")
        if algorithm == "sha512" and digest:
            return digest.split("?", 1)[0]
    return None


def _sha512_b64(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 16):
            digest.update(chunk)
    return base64.b64encode(digest.digest()).decode("ascii")


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + len("\n---\n") :]
    return text


def compose_skill(overlay: str, upstream: str, version: str) -> str:
    if not overlay.endswith("\n"):
        overlay += "\n"
    marker = f"\n## Upstream skill (auto-synced from {PACKAGE} {version}, overlay above wins)\n"
    return overlay + marker + _strip_frontmatter(upstream)


@dataclass(frozen=True)
class Skill:
    content: str
    upstream_sha256: str


def build_skill(deps: Deps, package: Path, version: str) -> Skill:
    """Compose the skill text from one package directory whose package.json is ``version``."""
    try:
        manifest = json.loads((package / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StepFailed("package_manifest_unreadable") from exc
    if manifest.get("name") != PACKAGE or manifest.get("version") != version:
        raise StepFailed("package_version_mismatch")
    try:
        upstream = (package / UPSTREAM_SKILL_REL).read_text(encoding="utf-8")
    except OSError as exc:
        raise StepFailed("upstream_skill_missing") from exc
    try:
        overlay = (deps.repo_root / OVERLAY_REL).read_text(encoding="utf-8")
    except OSError as exc:
        raise StepFailed("overlay_missing") from exc
    return Skill(compose_skill(overlay, upstream, version), hashlib.sha256(upstream.encode("utf-8")).hexdigest())


def _atomic_write(target: Path, content: str) -> None:
    if target.parent.is_symlink():
        raise OSError(f"refusing symlinked skill directory: {target.parent}")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=".SKILL.md.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def write_skills(home: Path, content: str) -> None:
    """Write both skill copies or neither: a failed write restores the copies already replaced."""
    targets = [home / rel for rel in SKILL_TARGETS_REL]
    previous = {target: target.read_text(encoding="utf-8") if target.is_file() else None for target in targets}
    written: list[Path] = []
    try:
        for target in targets:
            if previous[target] != content:
                _atomic_write(target, content)
                written.append(target)
    except OSError as exc:
        try:
            for target in written:
                old = previous[target]
                if old is None:
                    target.unlink(missing_ok=True)
                else:
                    _atomic_write(target, old)
        except OSError:
            raise StepFailed("skill_restore_failed") from exc
        raise StepFailed("skill_write_failed") from exc


def _package_of(binary: Path) -> Path | None:
    """Return the jevgrep package directory that ``binary`` resolves into."""
    if not binary.exists():
        return None
    for parent in binary.resolve().parents:
        manifest = parent / "package.json"
        if manifest.is_file():
            try:
                if json.loads(manifest.read_text(encoding="utf-8")).get("name") == PACKAGE:
                    return parent
            except (OSError, ValueError):
                return None
    return None


def _set_link(link: Path, target: str | None) -> None:
    """Point ``link`` at ``target`` atomically (temp symlink + rename); ``None`` removes it."""
    if target is None:
        link.unlink(missing_ok=True)
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    tmp = link.with_name(f".{link.name}.{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)
    os.symlink(target, tmp)
    try:
        os.replace(tmp, link)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


def _prefix_in(root: Path, link_target: str | None, link: Path) -> Path | None:
    if link_target is None:
        return None
    resolved = (link.parent / link_target).resolve()
    for prefix in (child for child in root.iterdir() if child.is_dir()):
        if resolved.is_relative_to(prefix.resolve()):
            return prefix
    return None


def prune_prefixes(root: Path, link: Path, previous: str | None) -> None:
    """Remove every version prefix under ``root`` except the one ``link`` points into now and ``previous``."""
    active = _prefix_in(root, os.readlink(link) if link.is_symlink() else None, link)
    if active is None:
        return
    keep = {active} | ({kept} if (kept := _prefix_in(root, previous, link)) else set())
    for child in root.iterdir():
        if child not in keep and child.is_dir() and not child.is_symlink():
            shutil.rmtree(child, ignore_errors=True)


def stage(run: Run, meta: Mapping[str, Any], version: str, prefix: Path) -> tuple[Path, Skill]:
    """Download, verify and install ``version`` into ``prefix``; verify the staged jg and build the skill."""
    dist = meta["dist"]
    with tempfile.TemporaryDirectory(prefix=".download-", dir=prefix.parent) as tmp:
        tarball = Path(tmp) / f"jevgrep-{version}.tgz"
        try:
            run.deps.download(dist["tarball"], tarball)
        except OSError as exc:
            raise StepFailed("tarball_download_failed") from exc
        if _sha512_b64(tarball) != _sri_sha512(dist["integrity"]):
            raise StepFailed("tarball_integrity_mismatch")
        empty_config = Path(tmp) / "empty.npmrc"
        empty_config.touch()
        install = [
            "npm",
            "install",
            "--prefix",
            str(prefix),
            "--ignore-scripts",
            "--no-package-lock",
            "--no-audit",
            "--no-fund",
            f"--registry={REGISTRY_BASE}",
            str(tarball),
        ]
        code, _ = run.call("npm_install", install, INSTALL_TIMEOUT_S, env=npm_env(run.deps.environ, empty_config))
        if code != 0:
            raise StepFailed("npm_install_failed")
    package = prefix / PACKAGE_REL
    skill = build_skill(run.deps, package, version)
    binary = (package / meta["bin"]["jg"]).resolve()
    if not binary.is_relative_to(package.resolve()) or not binary.is_file():
        raise StepFailed("staged_bin_missing")
    run.verify("staged", binary, version)
    return binary, skill


def install(run: Run, meta: Mapping[str, Any], current: str | None, version: str) -> str:
    """Install ``version`` beside the active one and switch to it; return the record result."""
    home = run.deps.home
    link = home / BIN_LINK_REL
    root = home / PREFIX_ROOT_REL
    if link.exists() and not link.is_symlink():
        raise StepFailed("bin_not_symlink")
    previous = os.readlink(link) if link.is_symlink() else None
    try:
        root.mkdir(parents=True, exist_ok=True)
        prefix = Path(tempfile.mkdtemp(prefix=f"{version}-", dir=root))
    except OSError as exc:
        raise StepFailed("prefix_create_failed") from exc
    try:
        binary, skill = stage(run, meta, version, prefix)
    except StepFailed as exc:
        run.failures.append(exc.args[0])
        shutil.rmtree(prefix, ignore_errors=True)
        return "failed"

    try:
        _set_link(link, str(binary))
        run.verify("switched", link, version)
        write_skills(home, skill.content)
    except (StepFailed, OSError) as exc:
        label = exc.args[0] if isinstance(exc, StepFailed) else "switch_failed"
        run.failures.append(label)
        if label == "skill_restore_failed":
            run.skill_sha256 = None
        return rollback(run, link, previous, current, prefix)
    run.skill_sha256 = skill.upstream_sha256
    prune_prefixes(root, link, previous)
    return "ok"


def rollback(run: Run, link: Path, previous: str | None, current: str | None, prefix: Path) -> str:
    """Restore the previous link (no download) and re-verify it; drop the failed prefix."""
    try:
        _set_link(link, previous)
    except OSError:
        run.failures.append("rollback_link_failed")
        return "rollback_failed"
    shutil.rmtree(prefix, ignore_errors=True)
    if previous is None:
        return "failed"
    try:
        if current is None:
            raise StepFailed("rollback_previous_unverified")
        run.verify("rollback", link, current)
    except StepFailed as exc:
        run.failures.append(exc.args[0])
        return "rollback_failed"
    return "rolled_back"


def sync_active_skill(run: Run, version: str) -> None:
    """Rewrite both skill copies from the active package (the one ``~/.local/bin/jg`` resolves into)."""
    package = _package_of(run.deps.home / BIN_LINK_REL)
    if package is None:
        raise StepFailed("active_package_not_found")
    skill = build_skill(run.deps, package, version)
    write_skills(run.deps.home, skill.content)
    run.skill_sha256 = skill.upstream_sha256


def _record(deps: Deps, run: Run, current: str | None) -> dict[str, Any]:
    return {
        "time": deps.now(),
        "current": current,
        "target": None,
        "action": None,
        "result": None,
        "upstream_skill_sha256": None,
        "detail": None,
        "exit_codes": run.exit_codes,
    }


def update(deps: Deps, *, dry_run: bool = False) -> tuple[int, dict[str, Any]]:
    """Run once under an exclusive lock; a run that finds the lock held does nothing and exits 0."""
    lock_path = deps.home / LOCK_REL
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            record = _record(deps, Run(deps), None)
            record.update(action="locked", result="skipped")
            if dry_run:
                record["dry_run"] = True
            return 0, record
        return _update_locked(deps, dry_run=dry_run)


def _update_locked(deps: Deps, *, dry_run: bool) -> tuple[int, dict[str, Any]]:
    run = Run(deps)
    link = deps.home / BIN_LINK_REL
    current = run.version_of("current_version", link) if link.exists() else None
    record = _record(deps, run, current)
    if dry_run:
        record["dry_run"] = True
    elif current is not None:
        # Self-heal: whatever an earlier run left behind, the skills now match the active CLI.
        try:
            sync_active_skill(run, current)
        except StepFailed as exc:
            run.failures.append(exc.args[0])
    try:
        packument = deps.fetch_packument()
    except (OSError, ValueError):
        packument = None
        record.update(action="resolve", result="failed")
        run.failures.append("registry_unreachable")
    target = None
    if packument is not None:
        try:
            target = resolve_target(packument, deps.environ)
        except (ValueError, KeyError, TypeError, AttributeError):
            record.update(action="resolve", result="failed")
            run.failures.append("invalid_target")
    if target is not None:
        record["target"] = target
        if target == current:
            record.update(action="none", result="ok")
        elif failures := guard_failures(packument, target):
            record.update(action="blocked", result="failed")
            run.failures.extend(failures)
        elif dry_run:
            record.update(action="install", result="dry_run")
        else:
            record["action"] = "install"
            try:
                record["result"] = install(run, packument["versions"][target], current, target)
            except StepFailed as exc:
                record["result"] = "failed"
                run.failures.append(exc.args[0])

    if not dry_run and not link.exists():
        run.failures.append("jg_not_installed_skill_not_synced")
    record["upstream_skill_sha256"] = run.skill_sha256
    record["detail"] = "; ".join(run.failures) or None
    exit_code = 0 if record["result"] in {"ok", "dry_run"} and not run.failures else 1
    if dry_run:
        return exit_code, record
    log_path = deps.home / STATE_LOG_REL
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return exit_code, record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Keep the host's jevgrep CLI (@dzhng/jevgrep, bin jg) at npm latest and sync the user-level skill.\n"
            "Run by the learn-ukrainian-jevgrep-update timer; the driver or operator may run it by hand.\n"
            "Task agents never run it."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/tools/jevgrep_update.py --dry-run --json\n"
            "  .venv/bin/python scripts/tools/jevgrep_update.py\n"
            f"  {HOLD_ENV}=0.4.4 .venv/bin/python scripts/tools/jevgrep_update.py   # pin temporarily\n"
            "\n"
            f"Guards: metadata and tarball come from https://{REGISTRY_HOST}/ only, with no redirects\n"
            "and size caps (8 MiB metadata, 64 MiB tarball). The target release must carry npm\n"
            "provenance attestations, have no preinstall/install/postinstall script, declare bin.jg,\n"
            f"and name a tarball on {REGISTRY_HOST} with a sha512 dist.integrity. That tarball is\n"
            "checked against dist.integrity and installed from the local file into its own prefix with\n"
            f"--ignore-scripts --no-package-lock --registry={REGISTRY_BASE}; npm runs with no inherited\n"
            "npm_config_* variables and empty user and global config files. The staged `jg --version`\n"
            "and `jg doctor` must pass and its upstream skill file must exist before ~/.local/bin/jg is\n"
            "switched; a failed switch or skill write restores the previous link and skill files.\n"
            "Every non-dry run first rebuilds both skill copies from the active package, so a failed\n"
            "skill restore (label skill_restore_failed) heals on the next run.\n"
            "\n"
            f"Outputs: ~/{PREFIX_ROOT_REL}/<version>-*/ (the active and previous prefixes are kept);\n"
            f"~/{BIN_LINK_REL} symlink; ~/.claude/skills/jevgrep/SKILL.md and\n"
            "~/.agents/skills/jevgrep/SKILL.md (tracked overlay + installed upstream skill body);\n"
            f"one JSON line appended to ~/{STATE_LOG_REL}. Records hold exit codes and fixed\n"
            f"failure classifications only, never child output. Every run holds ~/{LOCK_REL};\n"
            "a run that finds it held reports action=locked, changes nothing and exits 0.\n"
            "--dry-run writes nothing but the lock file.\n"
            "Exit codes: 0 up to date, updated and synced, or locked out by a running update; 1 guard,\n"
            "download, install, verify, registry or sync failure (the previous version stays active);\n"
            "2 invalid arguments.\n"
            "Related: agents_extensions/shared/skills/jevgrep/UPSTREAM.md, "
            "packaging/systemd/learn-ukrainian-jevgrep-update.{service,timer}, issue #9134."
        ),
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the run record as JSON (default: one human-readable line)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the target and check the guards only; no download, install, skill write or state-log line.",
    )
    return parser


def main(argv: list[str] | None = None, deps: Deps | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, record = update(deps or Deps(), dry_run=args.dry_run)
    if args.json:
        print(json.dumps(record, sort_keys=True))
    else:
        line = f"jevgrep: current={record['current']} target={record['target']} action={record['action']} "
        line += f"result={record['result']}"
        if record["detail"]:
            line += f" detail={record['detail']}"
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
