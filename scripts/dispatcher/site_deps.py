"""One shared, content-addressed store for the site dependencies of every dispatch worktree.

``npm ci`` copies every package into each worktree (about 570 MB of ``site/node_modules``), so a
handful of live worktrees filled the disk. The store keeps each distinct file once and gives each
worktree its own real ``site/node_modules`` made of hard links to those files: the same mechanism
pnpm's store uses, but over the tree ``npm ci`` produces from ``site/package-lock.json``, so a
worktree runs exactly the packages CI installs. (``pnpm import`` does not reproduce that lockfile:
it ignores npm ``overrides`` and resolves different versions.)

Isolation, as in ``git.provision_links``: no worktree path is a link into the primary checkout or
into another worktree. Deleting or replacing a worktree install (``npm ci``, ``rm -r``) unlinks
names and never touches the store. Store files are read-only, so a tool that edits a package file
in place fails loudly instead of silently changing every other worktree.

A tree is addressed by a key over everything that can change the installed bytes: the lockfile and
``package.json``, project ``.npmrc`` files, local ``file:``/``link:`` inputs and ``patches/``, the
Node and npm versions and module ABI, platform, architecture and libc, and the effective npm
configuration. File identity is the SHA-256 of the content plus the executable bit, so two keys
that differ in a native build share only the files that really are identical.

``python -m scripts.dispatcher.site_deps {ensure|status|prune}``.
"""

import argparse
import fcntl
import hashlib
import json
import logging
import os
import shutil
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

LOGGER = logging.getLogger(__name__)
LAYOUT = 1
SITE = "site"
INSTALL_INPUTS = ("package.json", "package-lock.json", ".npmrc")
INSTALL_TIMEOUT = 900
KEEP_TREES = 3
# The install runs in a controlled environment, so ambient variables an install script might read
# (a custom esbuild binary path, a compiler override) cannot change its bytes behind the key. These
# only let node, npm and node-gyp run and reach the registry; they carry no install semantics.
PASSTHROUGH_ENV = frozenset({
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
})
# Everything else that is passed on decides what is installed, so it is part of the key.
KEYED_ENV_PREFIX = "npm_config_"
KEYED_ENV = frozenset({"NODE_OPTIONS"})
# Tool caches npm scripts write under node_modules at run time; never part of an install.
RUNTIME_CACHES = frozenset({".cache", ".vite", ".vite-temp", ".astro"})
# Rewritten by npm itself, so it is copied rather than shared.
COPIED = frozenset({".package-lock.json"})
STORE_ENV = "LEARN_UKRAINIAN_DEP_STORE"
DISABLE_ENV = "LEARN_UKRAINIAN_SITE_DEPS"


class NotCacheable(Exception):
    """The installed tree cannot be shared without breaking worktree isolation."""


def store_root(repo: Path) -> Path:
    """The store lives beside the worktrees' repository so that hard links stay on one filesystem."""
    configured = os.environ.get(STORE_ENV)
    return Path(configured) if configured else Path(repo) / ".git" / "dispatch-dep-store" / f"v{LAYOUT}"


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() or p.is_symlink()):
        digest.update(f"{path.relative_to(root).as_posix()}\0".encode())
        digest.update((os.readlink(path) if path.is_symlink() else _sha256(path)).encode())
    return digest.hexdigest()


def _local_inputs(site: Path) -> dict[str, str]:
    """Digests of every non-registry input the install reads: file:/link: targets and patches."""
    specs: set[str] = set()
    package = json.loads((site / "package.json").read_text(encoding="utf-8"))
    for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        specs.update(v for v in package.get(field, {}).values() if v.startswith(("file:", "link:")))
    lock = json.loads((site / "package-lock.json").read_text(encoding="utf-8"))
    for entry in lock.get("packages", {}).values():
        if entry.get("link") and entry.get("resolved"):
            specs.add(f"link:{entry['resolved']}")
        elif str(entry.get("resolved", "")).startswith("file:"):
            specs.add(entry["resolved"])
    inputs = {}
    candidates = {spec: (site / spec.split(":", 1)[1]) for spec in specs}
    candidates["patches/"] = site / "patches"
    for name, path in sorted(candidates.items()):
        resolved = path.resolve()
        if not resolved.is_relative_to(site.resolve()) or not resolved.exists():
            if name != "patches/":
                raise NotCacheable(f"local install input {name} is missing or outside the site directory")
            continue
        inputs[name] = _tree_digest(resolved) if resolved.is_dir() else _sha256(resolved)
    return inputs


def _keyed_env() -> dict[str, str]:
    return {name: value for name, value in sorted(os.environ.items())
            if name.lower().startswith(KEYED_ENV_PREFIX) or name in KEYED_ENV}


def _install_env() -> dict[str, str]:
    """The only environment node and npm see: the passthrough names plus the variables the key covers."""
    return {**{name: os.environ[name] for name in PASSTHROUGH_ENV if name in os.environ}, **_keyed_env()}


def _run(argv, cwd, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, check=True, capture_output=True, text=True, timeout=kwargs.pop("timeout", 60),
                          env=_install_env(), **kwargs)


def _runtime(site: Path) -> dict:
    probe = ("const r=process.report.getReport().header;console.log(JSON.stringify({node:process.version,"
             "abi:process.versions.modules,platform:process.platform,arch:process.arch,"
             "libc:r.glibcVersionRuntime?'glibc-'+r.glibcVersionRuntime:'other'}))")
    runtime = json.loads(_run(["node", "-e", probe], site).stdout)
    runtime["npm"] = _run(["npm", "--version"], site).stdout.strip()
    return runtime


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def install_key(site: Path) -> tuple[str, dict]:
    """The key and the human-readable facts it covers; any change to them is a different install."""
    facts = {
        "layout": LAYOUT,
        "runtime": _runtime(site),
        # Digests only: user npm configuration can hold registry credentials, and facts are stored.
        "npm_config": _digest(json.loads(_run(["npm", "config", "ls", "-l", "--json"], site).stdout)),
        "env": {name: _digest(value) for name, value in _keyed_env().items()},
        "inputs": {name: _sha256(site / name) for name in INSTALL_INPUTS if (site / name).is_file()},
        "local": _local_inputs(site),
    }
    return hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest(), facts


@contextmanager
def _locked(path: Path, mode: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle, mode)
        yield


def _blob(store: Path, name: str) -> Path:
    return store / "blobs" / name[:2] / name


def _ingest(store: Path, modules: Path) -> dict:
    """Move the files of a freshly installed tree into the store and describe the tree."""
    root = modules.resolve()
    entries: list[list] = []

    def link(here: Path, rel: str) -> None:
        target = os.readlink(here)
        if os.path.isabs(target) or not (here.parent / target).resolve().is_relative_to(root):
            raise NotCacheable(f"{rel} links outside the installed tree")
        entries.append(["l", rel, target])

    for directory, subdirs, files in os.walk(modules):
        here = Path(directory)
        relative = here.relative_to(modules)
        top = not relative.parts
        if top:
            subdirs[:] = [d for d in subdirs if d not in RUNTIME_CACHES]
        for name in sorted(subdirs):
            rel = (relative / name).as_posix()
            link(here / name, rel) if (here / name).is_symlink() else entries.append(["d", rel])
        for name in sorted(files):
            path, rel = here / name, (relative / name).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                link(path, rel)
            elif stat.S_ISREG(info.st_mode):
                executable = bool(info.st_mode & stat.S_IXUSR)
                digest = _sha256(path) + ("x" if executable else "")
                entries.append(["c" if top and name in COPIED else "f", rel, digest])
                _keep(store, path, digest, executable, info.st_size)
            else:
                raise NotCacheable(f"{rel} is neither a file, directory nor link")
    return {"entries": entries}


def _keep(store: Path, path: Path, digest: str, executable: bool, size: int) -> None:
    blob = _blob(store, digest)
    blob.parent.mkdir(parents=True, exist_ok=True)
    path.chmod(0o555 if executable else 0o444)
    try:
        os.link(path, blob)
    except FileExistsError:
        if blob.stat().st_size != size:
            raise NotCacheable(f"store entry {digest} does not match the installed file") from None


def _write_manifest(store: Path, key: str, facts: dict, tree: dict) -> None:
    target = store / "trees" / f"{key}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    # A sibling file renamed into place: a reader never sees a half-written manifest.
    temporary = target.with_name(f".{key}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump({"facts": facts, **tree}, handle)
    os.replace(temporary, target)


def populate(repo: Path, site: Path, key: str, facts: dict) -> None:
    """Install once in a staging directory (never in a worktree) and move the result into the store."""
    store = store_root(repo)
    staging = store / "staging" / f"{key[:12]}-{os.getpid()}"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    try:
        for name in (*INSTALL_INPUTS, "patches"):
            source = site / name
            if source.is_dir():
                shutil.copytree(source, staging / name)
            elif source.is_file():
                shutil.copy2(source, staging / name)
        for name in facts["local"]:
            if name != "patches/":
                target = name.split(":", 1)[1]
                (staging / target).parent.mkdir(parents=True, exist_ok=True)
                source = site / target
                shutil.copytree(source, staging / target) if source.is_dir() else shutil.copy2(source, staging / target)
        _run(["npm", "ci", "--prefer-offline", "--no-audit", "--no-fund"], staging, timeout=INSTALL_TIMEOUT)
        tree = _ingest(store, staging / "node_modules")
        _write_manifest(store, key, facts, tree)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _altered(store: Path, manifest: Path) -> list[Path] | None:
    """None when the tree is stored and every store file still has the content its name says.

    Otherwise the store files that do not (an empty list when the tree was never stored).

    Hard links share one inode, so a tool that edits a package file in place changes it for every worktree
    and for the store. The check runs before each reuse, so such a file never reaches a new worktree.
    """
    if not manifest.is_file():
        return []
    altered = []
    for name in sorted({e[2] for e in json.loads(manifest.read_text(encoding="utf-8"))["entries"]
                        if e[0] in ("f", "c")}):
        blob = _blob(store, name)
        try:
            intact = _sha256(blob) == name[:64]
        except OSError:
            intact = False
        if not intact:
            altered.append(blob)
    return altered or None


def materialize(repo: Path, site: Path, key: str) -> dict:
    """Give the worktree its own real node_modules of hard links; never replaces an existing install."""
    store = store_root(repo)
    destination = site / "node_modules"
    manifest = json.loads((store / "trees" / f"{key}.json").read_text(encoding="utf-8"))
    if destination.exists() or destination.is_symlink():
        return {"state": "present"}
    building = site / f"node_modules.tmp-{os.getpid()}"
    shutil.rmtree(building, ignore_errors=True)
    stats = {"state": "installed", "linked": 0, "copied": 0}
    try:
        building.mkdir()
        for kind, rel, *rest in manifest["entries"]:
            path = building / rel
            if kind == "d":
                path.mkdir(parents=True, exist_ok=True)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if kind == "l":
                os.symlink(rest[0], path)
                continue
            blob = _blob(store, rest[0])
            if kind == "f":
                try:
                    os.link(blob, path)
                    stats["linked"] += 1
                    continue
                except OSError:
                    LOGGER.warning("Cannot hard-link %s into the worktree; copying it", rel)
            shutil.copy2(blob, path)
            path.chmod(0o755 if rest[0].endswith("x") else 0o644)
            stats["copied"] += 1
        os.rename(building, destination)
    except BaseException:
        shutil.rmtree(building, ignore_errors=True)
        raise
    return stats


def ensure(repo: Path, worktree: Path) -> dict:
    """Install the worktree's site dependencies from the store, filling the store first on a miss."""
    repo, worktree = Path(repo), Path(worktree)
    site = worktree / SITE
    if os.environ.get(DISABLE_ENV) == "off" or not all((site / name).is_file() for name in INSTALL_INPUTS[:2]):
        return {"state": "skipped"}
    if (site / "node_modules").exists() or (site / "node_modules").is_symlink():
        return {"state": "present"}
    store = store_root(repo)
    key, facts = install_key(site)
    manifest = store / "trees" / f"{key}.json"
    with _locked(store / "prune.lock", fcntl.LOCK_SH):
        if _altered(store, manifest) is not None:
            with _locked(store / "locks" / f"{key}.lock", fcntl.LOCK_EX):
                altered = _altered(store, manifest)
                if altered is not None:
                    # Unlinking leaves worktrees that still hold the old inode as they are; only new ones differ.
                    for blob in altered:
                        blob.unlink(missing_ok=True)
                    manifest.unlink(missing_ok=True)
                    populate(repo, site, key, facts)
        result = materialize(repo, site, key)
    prune(repo, keep=KEEP_TREES, blocking=False)
    return {**result, "key": key}


def prune(repo: Path, keep: int = KEEP_TREES, *, blocking: bool = True) -> dict:
    """Drop all but the newest trees, then the store files no remaining tree and no worktree uses."""
    store = store_root(repo)
    if not store.is_dir():
        return {"trees": 0, "blobs": 0}
    path = store / "prune.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            return {"trees": 0, "blobs": 0}
        trees = sorted((store / "trees").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for stale in trees[keep:]:
            stale.unlink()
        wanted = set()
        for tree in trees[:keep]:
            wanted.update(entry[2] for entry in json.loads(tree.read_text(encoding="utf-8"))["entries"]
                          if entry[0] in ("f", "c"))
        removed = 0
        for blob in (store / "blobs").glob("*/*"):
            if blob.name not in wanted and blob.stat().st_nlink == 1:
                blob.unlink()
                removed += 1
    return {"trees": len(trees[keep:]), "blobs": removed}


def status(repo: Path) -> dict:
    store = store_root(repo)
    blobs = [p for p in (store / "blobs").glob("*/*")] if store.is_dir() else []
    return {"store": str(store), "trees": len(list((store / "trees").glob("*.json"))) if store.is_dir() else 0,
            "blobs": len(blobs), "bytes": sum(p.stat().st_size for p in blobs)}


def provision(repo: Path, worktree: Path) -> None:
    """Best-effort hook for worktree creation: a task never fails because dependencies could not be shared."""
    try:
        result = ensure(repo, worktree)
    except (NotCacheable, OSError, ValueError, subprocess.SubprocessError) as exc:
        LOGGER.warning("Site dependencies were not provisioned for %s: %s", worktree, exc)
        return
    LOGGER.info("Site dependencies for %s: %s", worktree, result)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("ensure", "status", "prune"))
    parser.add_argument("--worktree", type=Path, default=Path.cwd(), help="the dispatch worktree (default: here)")
    args = parser.parse_args(argv)
    common = _run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], args.worktree).stdout.strip()
    repo = Path(common).parent
    if args.action == "ensure":
        result = ensure(repo, args.worktree)
    else:
        result = status(repo) if args.action == "status" else prune(repo)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
