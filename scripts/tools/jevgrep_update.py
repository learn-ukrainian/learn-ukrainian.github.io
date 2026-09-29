#!/usr/bin/env python3
"""Keep the host's jevgrep CLI at npm ``latest`` and sync its user-level skill (#9134, #9146).

Run by ``learn-ukrainian-jevgrep-update.timer`` from the primary checkout. It
holds an exclusive lock for the whole run, then rebuilds both skill copies from
the active package so any earlier CLI/skill mismatch heals. It resolves
``latest`` (or ``JEVGREP_HOLD_VERSION``) from the public npm registry to an
exact version and checks the supply-chain guards on that metadata. It then
resolves the whole dependency closure from registry metadata alone: every spec
must be an exact ``x.y.z``, ``^x.y.z`` or ``~x.y.z`` and resolves to one exact
stable version. Every tarball in the closure is downloaded (no redirects,
size-capped), checked against its ``dist.integrity`` sha512, and its own
``package.json`` must match the metadata it was resolved from. Only then are
the tarballs extracted, without npm, into a nested ``node_modules`` layout in
their own version prefix, and a structural audit confirms that every resolved
dependency sits in its dependent's own ``node_modules``. npm is never run, so no
lifecycle script, git fetch or config file can act. The staged ``jg`` and both
skill texts are checked before ``~/.local/bin/jg`` is switched atomically; any
later failure restores the previous link and skill files without a download.
Child output is never recorded: the state log, ``--json`` and the journal carry
exit codes and fixed failure classifications only. Stdlib only.
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
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

PACKAGE = "@dzhng/jevgrep"
REGISTRY_HOST = "registry.npmjs.org"
REGISTRY_BASE = f"https://{REGISTRY_HOST}/"
REGISTRY_URL = f"{REGISTRY_BASE}@dzhng%2fjevgrep"
# The abbreviated ("corgi") packument npm itself resolves ranges from.
ABBREVIATED_ACCEPT = "application/vnd.npm.install-v1+json"
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
# Inside a version prefix, the same layout ``npm install -g`` produces.
LIB_REL = PurePosixPath("lib/node_modules")
PACKAGE_REL = LIB_REL / PACKAGE
PREFIX_BIN_REL = Path("bin/jg")
UPSTREAM_SKILL_REL = Path("dist/skills/jevgrep/SKILL.md")
FORBIDDEN_SCRIPTS = ("preinstall", "install", "postinstall")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")
_NUM = r"(0|[1-9]\d*)"
STABLE_VERSION_RE = re.compile(rf"{_NUM}\.{_NUM}\.{_NUM}")
# The only dependency specs the updater resolves: exact, caret or tilde on a full stable version.
DEPENDENCY_SPEC_RE = re.compile(rf"([\^~]?){_NUM}\.{_NUM}\.{_NUM}")
# npm package names; a validated name is safe as a path segment and in a log line.
PACKAGE_NAME_RE = re.compile(r"(?:@[A-Za-z0-9~-][A-Za-z0-9._~-]*/)?[A-Za-z0-9~-][A-Za-z0-9._~-]*")
BIN_NAME_RE = re.compile(r"[A-Za-z0-9_~-][A-Za-z0-9._~-]*")
BUNDLE_FIELDS = ("bundleDependencies", "bundledDependencies")

# Hold reasons (fixed labels; a closure label is suffixed ``:<dependency trail>``).
DEPENDENCY_SOURCE_REFUSED = "dependency_source_refused"
NO_SATISFYING_VERSION = "no_satisfying_version"
PEER_DEPENDENCY_REFUSED = "peer_dependency_refused"
DEPENDENCY_CYCLE = "dependency_cycle"
INSTALL_SCRIPT_REFUSED = "install_script_refused"
BIN_REFUSED = "bin_refused"
METADATA_INVALID = "metadata_invalid"
INTEGRITY_MISMATCH = "integrity_mismatch"
TARBALL_MANIFEST_MISMATCH = "tarball_manifest_mismatch"
TARBALL_ENTRY_REFUSED = "tarball_entry_refused"
TARBALL_UNREADABLE = "tarball_unreadable"
RESOURCE_LIMIT = "resource_limit"
CONFINEMENT_AUDIT_FAILED = "confinement_audit_failed"
PYTHON_TOO_OLD = "python_too_old"

KEEP_PREFIXES = 2
MAX_CLOSURE_PACKAGES = 64
MAX_METADATA_BYTES = 32 * 1024 * 1024
MAX_TARBALL_BYTES = 64 * 1024 * 1024
MAX_TOTAL_DOWNLOAD_BYTES = 256 * 1024 * 1024
MAX_EXTRACTED_BYTES = 512 * 1024 * 1024
MAX_TARBALL_ENTRIES = 20_000
MAX_MANIFEST_BYTES = 1024 * 1024
DOCTOR_TIMEOUT_S = 180
VERSION_TIMEOUT_S = 30

Runner = Callable[..., subprocess.CompletedProcess[str]]


class StepFailed(Exception):
    """A step failed; ``args[0]`` is a fixed classification, never child output."""


class NotFound(LookupError):
    """The registry answered 404 for a package or version."""


def _run(cmd: list[str], timeout: int, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout, env=env)


def _python_supported() -> bool:
    """Extraction needs the ``tarfile`` data filter (Python 3.12+); nothing is extracted without it."""
    return sys.version_info >= (3, 12) and hasattr(tarfile, "data_filter")


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


def _fetch_json(url: str, accept: str) -> dict[str, Any]:
    body = bytearray()
    try:
        _fetch(url, MAX_METADATA_BYTES, body.extend, accept=accept, timeout=60)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise NotFound(url) from exc
        raise
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("registry document is not an object")
    return data


def _registry_url(name: str, version: str | None = None) -> str:
    url = REGISTRY_BASE + urllib.parse.quote(name, safe="@")
    return f"{url}/{version}" if version else url


def _fetch_packument() -> dict[str, Any]:
    return _fetch_json(REGISTRY_URL, "application/json")


def _fetch_versions(name: str) -> dict[str, Any]:
    return _fetch_json(_registry_url(name), ABBREVIATED_ACCEPT)


def _fetch_manifest(name: str, version: str) -> dict[str, Any]:
    return _fetch_json(_registry_url(name, version), "application/json")


def _download(url: str, dest: Path) -> None:
    with dest.open("wb") as handle:
        _fetch(url, MAX_TARBALL_BYTES, handle.write, accept="application/octet-stream", timeout=120)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class Deps:
    home: Path = field(default_factory=Path.home)
    run: Runner = _run
    fetch_packument: Callable[[], dict[str, Any]] = _fetch_packument
    fetch_versions: Callable[[str], dict[str, Any]] = _fetch_versions
    fetch_manifest: Callable[[str, str], dict[str, Any]] = _fetch_manifest
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
    """Release-level guards on the root package; the closure resolver checks every node again."""
    meta = packument.get("versions", {}).get(version)
    if not isinstance(meta, dict):
        return [f"{version} is not in the registry"]
    failures = []
    dist = meta.get("dist") or {}
    if not dist.get("attestations"):
        failures.append("no npm provenance attestations")
    if not is_registry_url(dist.get("tarball")):
        failures.append(f"dist.tarball is not on https://{REGISTRY_HOST}/")
    if not _sri_sha512(dist.get("integrity")):
        failures.append("dist.integrity has no sha512")
    scripts = meta.get("scripts") or {}
    failures.extend(f"install script {name!r} present" for name in FORBIDDEN_SCRIPTS if name in scripts)
    if meta.get("hasInstallScript"):
        failures.append("registry marks hasInstallScript")
    bins = meta.get("bin")
    if not isinstance(bins, dict) or not bins.get("jg"):
        failures.append("bin.jg missing")
    return failures


# --- dependency closure (registry metadata only) ---------------------------------------


@dataclass
class Node:
    """One installed package instance: ``path`` is its directory relative to the version prefix."""

    name: str
    version: str
    meta: Mapping[str, Any]
    trail: str
    path: PurePosixPath
    children: list[Node] = field(default_factory=list)

    def walk(self) -> Iterator[Node]:
        yield self
        for child in self.children:
            yield from child.walk()


def _refuse(label: str, trail: str) -> StepFailed:
    return StepFailed(f"{label}:{trail}")


def _stable(version: object) -> tuple[int, int, int] | None:
    match = STABLE_VERSION_RE.fullmatch(version) if isinstance(version, str) else None
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def spec_bounds(spec: object) -> tuple[str, tuple[int, int, int], tuple[int, int, int] | None] | None:
    """``(operator, lower, exclusive upper)`` for an exact, caret or tilde spec; ``None`` for any other spec.

    npm semver: ``~x.y.z`` allows patch updates; ``^x.y.z`` allows changes that keep the
    left-most non-zero part, so ``^0.2.3`` stays in ``0.2.x`` and ``^0.0.3`` is exactly ``0.0.3``.
    """
    match = DEPENDENCY_SPEC_RE.fullmatch(spec) if isinstance(spec, str) else None
    if match is None:
        return None
    operator = match[1]
    x, y, z = int(match[2]), int(match[3]), int(match[4])
    if operator == "~":
        return operator, (x, y, z), (x, y + 1, 0)
    if operator == "^":
        upper = (x + 1, 0, 0) if x else (0, y + 1, 0) if y else (0, 0, z + 1)
        return operator, (x, y, z), upper
    return operator, (x, y, z), None


def pick_version(spec: str, versions: object) -> str | None:
    """The highest stable version in ``versions`` that satisfies a caret or tilde ``spec``."""
    bounds = spec_bounds(spec)
    if bounds is None or bounds[2] is None or not isinstance(versions, Mapping):
        return None
    _, lower, upper = bounds
    satisfying = [(parsed, v) for v in versions if (parsed := _stable(v)) and lower <= parsed < upper]
    return max(satisfying)[1] if satisfying else None


def _safe_relpath(path: object) -> str:
    """A package-relative path with no absolute prefix and no ``..``; ``ValueError`` otherwise."""
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or "\0" in path:
        raise ValueError("unsafe path")
    parts = [part for part in path.split("/") if part not in ("", ".")]
    if not parts or ".." in parts:
        raise ValueError("unsafe path")
    return "/".join(parts)


def normalize_bin(name: object, bins: object) -> dict[str, str]:
    """``bin`` as ``{command: package-relative path}``; a string form is named after the unscoped package."""
    if bins is None:
        return {}
    if isinstance(bins, str):
        if not isinstance(name, str):
            raise ValueError("bin string without a package name")
        bins = {name.rsplit("/", 1)[-1]: bins}
    if not isinstance(bins, dict):
        raise ValueError("bin is not an object")
    normalized = {}
    for command, target in bins.items():
        if not isinstance(command, str) or not BIN_NAME_RE.fullmatch(command) or command in {".", ".."}:
            raise ValueError("unsafe bin name")
        normalized[command] = _safe_relpath(target)
    return normalized


def _spec_map(meta: Mapping[str, Any], name: str) -> dict[str, Any]:
    specs = meta.get(name)
    if specs is None:
        return {}
    if not isinstance(specs, dict):
        raise ValueError(f"{name} is not an object")
    return specs


def manifest_projection(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """The fields a tarball ``package.json`` must share with its registry metadata, canonicalized.

    Older npm releases also copied ``optionalDependencies`` into ``dependencies`` on publish,
    so both sides compare the merged map; ``bundleDependencies`` and ``bundledDependencies``
    are one field; registry-injected ``_`` fields are never read.
    """
    optional = _spec_map(manifest, "optionalDependencies")
    return {
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "dependencies": {**_spec_map(manifest, "dependencies"), **optional},
        "optionalDependencies": optional,
        "peerDependencies": _spec_map(manifest, "peerDependencies"),
        "bundleDependencies": next((manifest[k] for k in BUNDLE_FIELDS if manifest.get(k)), None) or [],
        "bin": normalize_bin(manifest.get("name"), manifest.get("bin")),
    }


def _has_install_script(manifest: Mapping[str, Any]) -> bool:
    scripts = manifest.get("scripts")
    if scripts is not None and not isinstance(scripts, dict):
        return True
    return any(name in (scripts or {}) for name in FORBIDDEN_SCRIPTS)


def _node_refusal(meta: Mapping[str, Any], name: str, version: str) -> str | None:
    """Why ``meta`` cannot be installed as ``name@version``, from registry metadata alone."""
    if meta.get("name") != name or meta.get("version") != version:
        return METADATA_INVALID
    dist = meta.get("dist")
    if not isinstance(dist, dict) or not is_registry_url(dist.get("tarball")) or not _sri_sha512(dist.get("integrity")):
        return DEPENDENCY_SOURCE_REFUSED
    if meta.get("hasInstallScript") or _has_install_script(meta):
        return INSTALL_SCRIPT_REFUSED
    try:
        projection = manifest_projection(meta)
    except ValueError:
        return BIN_REFUSED if not isinstance(meta.get("bin"), dict | str | None) else METADATA_INVALID
    if projection["bundleDependencies"]:
        return DEPENDENCY_SOURCE_REFUSED
    peers_meta = meta.get("peerDependenciesMeta") or {}
    for peer in projection["peerDependencies"]:
        optional = isinstance(peers_meta, dict) and isinstance(peers_meta.get(peer), dict)
        if not (optional and peers_meta[peer].get("optional") is True):
            return PEER_DEPENDENCY_REFUSED
    return None


class _Resolver:
    """Resolves the full nested closure from registry metadata; nothing is downloaded or run."""

    def __init__(self, deps: Deps) -> None:
        self.deps = deps
        self.count = 0
        self.versions: dict[str, Mapping[str, Any]] = {}
        self.manifests: dict[tuple[str, str], Mapping[str, Any]] = {}

    def manifest(self, name: str, version: str) -> Mapping[str, Any]:
        key = (name, version)
        if key not in self.manifests:
            self.manifests[key] = self.deps.fetch_manifest(name, version)
        return self.manifests[key]

    def resolve(self, name: str, spec: object, trail: str) -> str:
        bounds = spec_bounds(spec)
        if bounds is None:
            raise _refuse(DEPENDENCY_SOURCE_REFUSED, trail)
        if bounds[2] is None:
            return str(spec)
        if name not in self.versions:
            try:
                self.versions[name] = self.deps.fetch_versions(name)
            except NotFound as exc:
                raise _refuse(NO_SATISFYING_VERSION, trail) from exc
        picked = pick_version(str(spec), self.versions[name].get("versions"))
        if picked is None:
            raise _refuse(NO_SATISFYING_VERSION, trail)
        return picked

    def node(
        self, meta: Mapping[str, Any], name: str, version: str, trail: str, path: PurePosixPath, seen: frozenset
    ) -> Node:
        self.count += 1
        if self.count > MAX_CLOSURE_PACKAGES:
            raise _refuse(RESOURCE_LIMIT, trail)
        if refusal := _node_refusal(meta, name, version):
            raise _refuse(refusal, trail)
        node = Node(name, version, meta, trail, path)
        # Optional dependencies are strict: a refused one holds the update like a required one.
        for dep, spec in sorted(manifest_projection(meta)["dependencies"].items()):
            if not PACKAGE_NAME_RE.fullmatch(dep) or len(dep) > 214:
                raise _refuse(DEPENDENCY_SOURCE_REFUSED, trail)
            dep_trail = f"{trail}>{dep}"
            dep_version = self.resolve(dep, spec, dep_trail)
            if (dep, dep_version) in seen:
                raise _refuse(DEPENDENCY_CYCLE, dep_trail)
            try:
                dep_meta = self.manifest(dep, dep_version)
            except NotFound as exc:
                raise _refuse(NO_SATISFYING_VERSION, dep_trail) from exc
            dep_path = path / "node_modules" / dep
            node.children.append(
                self.node(dep_meta, dep, dep_version, dep_trail, dep_path, seen | {(dep, dep_version)})
            )
        return node


def resolve_closure(deps: Deps, meta: Mapping[str, Any], version: str) -> Node:
    """The nested install tree of ``PACKAGE@version``: ``StepFailed`` on refusal, ``OSError``/``ValueError`` offline."""
    return _Resolver(deps).node(meta, PACKAGE, version, PACKAGE, PACKAGE_REL, frozenset({(PACKAGE, version)}))


def closure_summary(root: Node) -> list[dict[str, str]]:
    return [{"path": node.trail, "version": node.version} for node in root.walk()]


# --- tarball verification and extraction (no npm) ------------------------------------------


def _sri_sha512(integrity: object) -> list[str]:
    """Every sha512 digest named by an SRI string (several space-separated entries are allowed)."""
    if not isinstance(integrity, str):
        return []
    digests = []
    for token in integrity.split():
        algorithm, _, digest = token.partition("-")
        if algorithm == "sha512" and digest:
            digests.append(digest.split("?", 1)[0])
    return digests


def _sha512_b64(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 16):
            digest.update(chunk)
    return base64.b64encode(digest.digest()).decode("ascii")


def _package_entries(archive: tarfile.TarFile) -> Iterator[tuple[tarfile.TarInfo, str]]:
    """Yield ``(member, path inside the package)`` for every entry, refusing anything unsafe.

    Only regular files and directories under ``package/`` pass; absolute paths, ``..``,
    links, devices, duplicates and a shipped ``node_modules/`` are refused.
    """
    seen: set[str] = set()
    for count, member in enumerate(archive, start=1):
        if count > MAX_TARBALL_ENTRIES:
            raise StepFailed(RESOURCE_LIMIT)
        name = member.name
        if not name.startswith("package/") and name != "package":
            raise StepFailed(TARBALL_ENTRY_REFUSED)
        parts = [part for part in name[len("package") :].split("/") if part not in ("", ".")]
        if ".." in parts or "\\" in name or "\0" in name or not (member.isreg() or member.isdir()):
            raise StepFailed(TARBALL_ENTRY_REFUSED)
        if parts and parts[0] == "node_modules":
            raise StepFailed(TARBALL_ENTRY_REFUSED)
        rel = "/".join(parts)
        if rel in seen:
            raise StepFailed(TARBALL_ENTRY_REFUSED)
        seen.add(rel)
        if rel:
            yield member, rel


@dataclass
class Verified:
    node: Node
    tarball: Path
    unpacked_bytes: int


def verify_tarball(node: Node, tarball: Path) -> Verified:
    """Check one downloaded tarball: SRI, safe entries, and its own ``package.json`` against the metadata."""
    if _sha512_b64(tarball) not in _sri_sha512(node.meta["dist"]["integrity"]):
        raise StepFailed(INTEGRITY_MISMATCH)
    manifest_bytes: bytes | None = None
    files: set[str] = set()
    unpacked = 0
    try:
        with tarfile.open(tarball, "r:gz") as archive:
            for member, rel in _package_entries(archive):
                if not member.isreg():
                    continue
                files.add(rel)
                unpacked += member.size
                if unpacked > MAX_EXTRACTED_BYTES:
                    raise StepFailed(RESOURCE_LIMIT)
                if rel == "package.json":
                    if member.size > MAX_MANIFEST_BYTES:
                        raise StepFailed(RESOURCE_LIMIT)
                    handle = archive.extractfile(member)
                    manifest_bytes = handle.read() if handle else None
    except (tarfile.TarError, OSError, EOFError, zlib.error) as exc:
        raise StepFailed(TARBALL_UNREADABLE) from exc
    try:
        manifest = json.loads(manifest_bytes) if manifest_bytes is not None else None
    except ValueError:
        manifest = None
    if not isinstance(manifest, dict):
        raise StepFailed(TARBALL_MANIFEST_MISMATCH)
    try:
        tarball_view = manifest_projection(manifest)
    except ValueError as exc:
        raise StepFailed(BIN_REFUSED if "bin" in str(exc) or "path" in str(exc) else TARBALL_MANIFEST_MISMATCH) from exc
    if tarball_view != manifest_projection(node.meta):
        raise StepFailed(TARBALL_MANIFEST_MISMATCH)
    # npm would run these (and ``node-gyp rebuild`` for a binding.gyp); nothing here ever runs them.
    if _has_install_script(manifest) or "binding.gyp" in files:
        raise StepFailed(INSTALL_SCRIPT_REFUSED)
    if not set(tarball_view["bin"].values()) <= files:
        raise StepFailed(BIN_REFUSED)
    return Verified(node, tarball, unpacked)


def extract(verified: Verified, dest: Path) -> None:
    """Extract a verified tarball into ``dest`` with the ``data`` filter, stripping ``package/``."""
    if not _python_supported():
        raise StepFailed(PYTHON_TOO_OLD)
    dest.mkdir(parents=True, exist_ok=False)
    with tarfile.open(verified.tarball, "r:gz") as archive:
        members = [member.replace(name=rel, deep=False) for member, rel in _package_entries(archive)]
        archive.extractall(dest, members=members, filter="data")
    package = dest.resolve()
    for target in manifest_projection(verified.node.meta)["bin"].values():
        path = (dest / target).resolve()
        if not path.is_relative_to(package) or not path.is_file():
            raise StepFailed(BIN_REFUSED)
        path.chmod(path.stat().st_mode | 0o111)


def _dir_entries(directory: Path) -> set[str]:
    """Package names directly under a ``node_modules`` directory (scoped names as ``@scope/name``)."""
    if not directory.exists():
        return set()
    names = set()
    for child in directory.iterdir():
        if child.name.startswith("@") and child.is_dir() and not child.is_symlink():
            names.update(f"{child.name}/{grandchild.name}" for grandchild in child.iterdir())
        else:
            names.add(child.name)
    return names


def _manifest_is(path: Path, name: str, version: str) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(manifest, dict) and manifest.get("name") == name and manifest.get("version") == version


def audit_confinement(prefix: Path, root: Node) -> None:
    """Every resolved dependency sits in its dependent's own ``node_modules``, and nothing else does.

    Node resolves a ``require`` from the nearest ``node_modules`` upward, so a dependency present
    at ``<pkgdir>/node_modules/<dep>`` is never looked up in a sibling or ancestor directory.
    """
    if (prefix / "node_modules").exists() or _dir_entries(prefix / LIB_REL) != {PACKAGE}:
        raise _refuse(CONFINEMENT_AUDIT_FAILED, root.trail)
    for node in root.walk():
        package = prefix / node.path
        if package.is_symlink() or not _manifest_is(package / "package.json", node.name, node.version):
            raise _refuse(CONFINEMENT_AUDIT_FAILED, node.trail)
        for child in node.children:
            if not _manifest_is(package / "node_modules" / child.name / "package.json", child.name, child.version):
                raise _refuse(CONFINEMENT_AUDIT_FAILED, child.trail)
        if _dir_entries(package / "node_modules") != {child.name for child in node.children}:
            raise _refuse(CONFINEMENT_AUDIT_FAILED, node.trail)


# --- skill text ------------------------------------------------------------------------------


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


# --- install, switch, rollback ---------------------------------------------------------------


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


def _fetch_verified(run: Run, root: Node, workdir: Path) -> list[Verified]:
    """Download and verify every tarball in the closure; nothing is extracted until all pass."""
    verified: list[Verified] = []
    downloaded = unpacked = 0
    for index, node in enumerate(root.walk()):
        tarball = workdir / f"{index}.tgz"
        try:
            run.deps.download(node.meta["dist"]["tarball"], tarball)
        except OSError as exc:
            raise _refuse("tarball_download_failed", node.trail) from exc
        downloaded += tarball.stat().st_size
        try:
            if downloaded > MAX_TOTAL_DOWNLOAD_BYTES:
                raise StepFailed(RESOURCE_LIMIT)
            verified.append(verify_tarball(node, tarball))
        except StepFailed as exc:
            raise _refuse(exc.args[0], node.trail) from exc
        unpacked += verified[-1].unpacked_bytes
        if unpacked > MAX_EXTRACTED_BYTES:
            raise _refuse(RESOURCE_LIMIT, node.trail)
    return verified


def stage(run: Run, root: Node, version: str, prefix: Path) -> tuple[Path, Skill]:
    """Verify every tarball of the closure, extract them into ``prefix``, audit, and verify the staged jg."""
    if not _python_supported():
        raise StepFailed(PYTHON_TOO_OLD)
    with tempfile.TemporaryDirectory(prefix=".download-", dir=prefix.parent) as tmp:
        verified = _fetch_verified(run, root, Path(tmp))
        for item in verified:
            try:
                extract(item, prefix / item.node.path)
            except StepFailed as exc:
                raise _refuse(exc.args[0], item.node.trail) from exc
            except (tarfile.TarError, OSError) as exc:
                raise _refuse("extract_failed", item.node.trail) from exc
    # Before anything from the staged tree runs.
    audit_confinement(prefix, root)
    package = prefix / PACKAGE_REL
    skill = build_skill(run.deps, package, version)
    binary = prefix / PREFIX_BIN_REL
    target = package / manifest_projection(root.meta)["bin"]["jg"]
    binary.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(os.path.relpath(target, binary.parent), binary)
    run.verify("staged", binary, version)
    return binary, skill


def install(run: Run, root: Node, current: str | None, version: str) -> str:
    """Install ``version`` beside the active one and switch to it; return the record result."""
    home = run.deps.home
    link = home / BIN_LINK_REL
    prefixes = home / PREFIX_ROOT_REL
    if link.exists() and not link.is_symlink():
        raise StepFailed("bin_not_symlink")
    previous = os.readlink(link) if link.is_symlink() else None
    try:
        prefixes.mkdir(parents=True, exist_ok=True)
        prefix = Path(tempfile.mkdtemp(prefix=f"{version}-", dir=prefixes))
    except OSError as exc:
        raise StepFailed("prefix_create_failed") from exc
    try:
        binary, skill = stage(run, root, version, prefix)
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
    prune_prefixes(prefixes, link, previous)
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
        "closure": None,
        "upstream_skill_sha256": None,
        "detail": None,
        "exit_codes": run.exit_codes,
    }


def update(deps: Deps, *, dry_run: bool = False) -> tuple[int, dict[str, Any]]:
    """Run once under an exclusive lock; a run that finds the lock held does nothing and exits 0."""
    if not _python_supported():
        record = _record(deps, Run(deps), None)
        record.update(action="resolve", result="failed", detail=PYTHON_TOO_OLD)
        return 1, record
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
    except (OSError, ValueError, NotFound):
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
    closure = None
    if target is not None:
        record["target"] = target
        if target == current:
            record.update(action="none", result="ok")
        elif failures := guard_failures(packument, target):
            record.update(action="blocked", result="failed")
            run.failures.extend(failures)
        else:
            try:
                closure = resolve_closure(deps, packument["versions"][target], target)
            except StepFailed as exc:
                record.update(action="blocked", result="failed")
                run.failures.append(exc.args[0])
            except (OSError, ValueError, NotFound):
                record.update(action="resolve", result="failed")
                run.failures.append("registry_unreachable")
    if closure is not None:
        record["closure"] = closure_summary(closure)
        if dry_run:
            record.update(action="install", result="dry_run")
        else:
            record["action"] = "install"
            try:
                record["result"] = install(run, closure, current, target)
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
            "Task agents never run it. npm is never invoked."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/tools/jevgrep_update.py --dry-run --json\n"
            "  .venv/bin/python scripts/tools/jevgrep_update.py\n"
            f"  {HOLD_ENV}=0.4.4 .venv/bin/python scripts/tools/jevgrep_update.py   # pin temporarily\n"
            "\n"
            f"Guards: all metadata and tarballs come from https://{REGISTRY_HOST}/ only, with no redirects\n"
            "and size caps. The target release must carry npm provenance attestations, have no\n"
            "preinstall/install/postinstall script and declare bin.jg. Its dependency closure is resolved\n"
            "from registry metadata: dependencies and optionalDependencies must be exact x.y.z, ^x.y.z or\n"
            "~x.y.z and resolve to the highest satisfying stable version; any other spec, a required peer\n"
            "dependency, bundled dependencies, a cycle or more than 64 packages hold the update. Every\n"
            "tarball must be on the registry with a sha512 dist.integrity that matches, contain only plain\n"
            "files and directories under package/, carry a package.json whose name, version,\n"
            "dependencies, optionalDependencies, peerDependencies, bundleDependencies and bin equal the\n"
            "metadata, and have no install script or binding.gyp. Only after every tarball passes are they\n"
            "extracted (tarfile data filter) into a nested node_modules tree in a new prefix; an audit\n"
            "confirms each dependency sits in its dependent's own node_modules. The staged `jg --version`\n"
            "and `jg doctor` must pass and its upstream skill file must exist before ~/.local/bin/jg is\n"
            "switched; a failed switch or skill write restores the previous link and skill files.\n"
            "Every non-dry run first rebuilds both skill copies from the active package, so a failed\n"
            "skill restore (label skill_restore_failed) heals on the next run.\n"
            "\n"
            f"Outputs: ~/{PREFIX_ROOT_REL}/<version>-*/ (lib/node_modules/{PACKAGE} and bin/jg; the active\n"
            f"and previous prefixes are kept); ~/{BIN_LINK_REL} symlink; ~/.claude/skills/jevgrep/SKILL.md and\n"
            "~/.agents/skills/jevgrep/SKILL.md (tracked overlay + installed upstream skill body);\n"
            f"one JSON line appended to ~/{STATE_LOG_REL}. Records hold the resolved closure, exit codes\n"
            "and fixed hold reasons (label:dependency>trail) only, never child output. Every run holds\n"
            f"~/{LOCK_REL}; a run that finds it held reports action=locked, changes nothing and exits 0.\n"
            "--dry-run resolves the closure from metadata and writes nothing but the lock file.\n"
            "Exit codes: 0 up to date, updated and synced, or locked out by a running update; 1 guard,\n"
            "closure, download, verify, registry or sync failure (the previous version stays active);\n"
            "2 invalid arguments.\n"
            "Related: agents_extensions/shared/skills/jevgrep/UPSTREAM.md, "
            "packaging/systemd/learn-ukrainian-jevgrep-update.{service,timer}, issues #9134 #9146."
        ),
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the run record as JSON (default: one human-readable line)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the target and its closure from metadata only; no download, install, skill write or log line.",
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
