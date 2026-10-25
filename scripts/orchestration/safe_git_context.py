"""Fresh, driver-configured Git execution with borrowed or received objects, never borrowed config.

The caller owns destination, identity and scratch storage. The source repository
contributes resolved refs, objects and plaintext snapshot-selection metadata;
its execution configuration is never imported. Finalization receives objects
over fetch, which re-hashes them, instead of borrowing the source store.
Same-user tampering with driver code/storage is outside this execution boundary.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from scripts.orchestration.fleet_repos import FleetRepo, load_fleet_repos

GIT = shutil.which("git", path=os.defpath) or "/usr/bin/git"
CANONICAL_ORIGIN = "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git"


class SnapshotRefusal(RuntimeError):
    """Unsupported or unstable inputs; the source worktree is retained."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class SafeGitContext:
    """One fresh bare repo and allowlisted environment, disposed on exit.

    ``local_remote`` is an explicit driver/test injection, never inferred from
    source config. Production rescue supplies the registered HTTPS destination.
    """

    def __init__(
        self,
        *,
        objects: Path,
        temp_root: Path,
        origin: str = CANONICAL_ORIGIN,
        token: str | None = None,
        local_remote: bool = False,
        borrow_objects: bool = True,
        repository: FleetRepo | None = None,
    ) -> None:
        registered = load_fleet_repos()
        selected = repository or next(repo for repo in registered.values() if repo.default)
        if registered.get(selected.key) != selected:
            raise SnapshotRefusal("rescue_push_url_unavailable")
        canonical = f"https://github.com/{selected.github}.git"
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", selected.github):
            raise SnapshotRefusal("rescue_push_url_unavailable")
        if origin != canonical and not (local_remote and Path(origin).is_absolute()):
            raise SnapshotRefusal("rescue_push_url_unavailable")
        self.repository = selected.github
        self.objects = objects.resolve(strict=True)
        self.lfs_objects = self.objects.parent / "lfs/objects"
        self.temp_root = temp_root
        self.origin = origin
        self.token = token
        self.local_remote = local_remote
        # Finalize contexts never borrow: isolate_objects receives everything.
        self.borrow_objects = borrow_objects
        self._source: tuple[str, Path] | None = None

    def __enter__(self) -> SafeGitContext:
        self._scratch = tempfile.TemporaryDirectory(prefix="lu-safe-git-", dir=self.temp_root)
        try:
            self.root = Path(self._scratch.name)
            self.git_dir = self.root / "publish.git"
            home = self.root / "home"
            template = self.root / "empty-template"
            home.mkdir()
            template.mkdir()
            self.env = {
                "PATH": os.defpath,
                "HOME": str(home),
                "TMPDIR": str(self.root),
                "LC_ALL": "C",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_NO_REPLACE_OBJECTS": "1",
                "GIT_NO_LAZY_FETCH": "1",
            }
            subprocess.run(
                [GIT, "init", "--bare", f"--template={template}", str(self.git_dir)],
                cwd=self.root,
                env=self.env,
                capture_output=True,
                check=True,
                timeout=60,
            )
            # Overwrite init's defaults: this is the sole configuration source.
            identity = ""
            if self.token:
                header = base64.b64encode(f"x-access-token:{self.token}".encode()).decode()
                identity = f'[http "{self.origin}"]\n\textraHeader = "Authorization: Basic {header}"\n'
            self.git_dir.joinpath("config").write_text(
                "[core]\n\trepositoryformatversion = 0\n\tbare = true\n"
                "\tfilemode = true\n\tsymlinks = true\n\tcommitGraph = false\n\tuseReplaceRefs = false\n"
                '[protocol]\n\tallow = never\n[protocol "https"]\n\tallow = always\n'
                + ('[protocol "file"]\n\tallow = always\n' if self.local_remote else "")
                + f'[remote "origin"]\n\turl = "{self.origin}"\n'
                # A finalize repository holds only the snapshots it received.
                # Negotiation finds the destination's copy of the base, so a
                # push never packs history this repository never fetched.
                + "[push]\n\tnegotiate = true\n"
                + "[user]\n\tname = Dispatch rescue\n\temail = dispatch@users.noreply.github.com\n"
                + identity,
                encoding="utf-8",
            )
            self.git_dir.joinpath("config").chmod(0o600)
            self.env.update(
                GIT_DIR=str(self.git_dir),
                GIT_INDEX_FILE=str(self.root / "index"),
            )
            if self.borrow_objects:
                self.env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = (
                    '"' + str(self.objects).replace("\\", "\\\\").replace('"', '\\"') + '"'
                )
            return self
        except BaseException:
            self._scratch.cleanup()
            raise

    def __exit__(self, *_exc) -> None:
        self._scratch.cleanup()

    def run(
        self,
        *args: str,
        work_tree: Path | None = None,
        index: Path | None = None,
        stdin: str | None = None,
        network: bool = False,
        binary: bool = False,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess:
        env = dict(self.env)
        if index is not None:
            env["GIT_INDEX_FILE"] = str(index)
        if work_tree is not None:
            env["GIT_WORK_TREE"] = str(work_tree)
        proc = subprocess.run(
            [GIT, *args],
            cwd=self.root,
            env=env,
            input=None if stdin is None else stdin.encode("utf-8", "surrogateescape"),
            capture_output=True,
            check=False,
            timeout=timeout if timeout is not None else (120 if network else 60),
        )
        if binary:
            return proc
        return subprocess.CompletedProcess(
            proc.args,
            proc.returncode,
            proc.stdout.decode("utf-8", "surrogateescape"),
            proc.stderr.decode("utf-8", "surrogateescape"),
        )

    def isolate_objects(self, *, base: str, head: str) -> None:
        """Receive the commit graph through a fetch whose receiver re-hashes every object.

        The source store may be the worker's own, and Git does not re-hash an
        object it reads from local storage. Every byte the checks read therefore
        arrives over the fetch protocol into this empty repository: index-pack
        names each object by the hash of what it received. A forged object
        stored under a real name arrives under a different name, so the
        requested one stays missing and any later read of it fails. Reads
        never fall back to the source store: nothing here points at it.
        """
        self.env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
        common = self.objects.parent
        admin = self.source_git_dir
        forbidden = [root / name for root in {common, admin} for name in ("info/grafts", "shallow")]
        replacements = common / "refs/replace"
        packed = common / "packed-refs"
        if (
            any(os.path.lexists(path) for path in forbidden)
            or (replacements.exists() and any(replacements.iterdir()))
            or (
                packed.exists()
                and any(
                    fields[-1].startswith(b"refs/replace/")
                    for line in packed.read_bytes().splitlines()
                    if (fields := line.split())
                )
            )
        ):
            raise SnapshotRefusal("auto_finalize_object_hardening_violation")
        for path in (common / "config", admin / "config.worktree"):
            if path.exists():
                config = self.run("config", "--no-includes", "--file", str(path), "--get-all", "core.graftFile")
                if config.returncode != 1:
                    raise SnapshotRefusal("auto_finalize_object_hardening_violation")
        self._serve(self.objects)
        self.objects = self.git_dir / "objects"
        tips = [base, getattr(self, "driver_base", base), head]
        # Commits only: their parents decide attribution, so all of them,
        # not a shallow window, must arrive before any merge-base is computed.
        self._receive(tips, "--filter=tree:0")
        if self.run("rev-list", "--missing=error", *dict.fromkeys(tips)).returncode:
            raise SnapshotRefusal("auto_finalize_fsck_failed")

    def _serve(self, objects: Path) -> None:
        """Answer the next fetches from the objects of ``objects`` alone, which each fetch re-hashes."""
        if any(os.path.lexists(objects / "info" / name) for name in ("alternates", "http-alternates")):
            raise SnapshotRefusal("auto_finalize_object_hardening_violation")
        # upload-pack serves only object bytes: an empty repository supplies
        # refs and configuration, the source store supplies objects.
        server = Path(tempfile.mkdtemp(prefix="source-", suffix=".git", dir=self.root))
        subprocess.run(
            [GIT, "init", "--bare", f"--template={self.root / 'empty-template'}", str(server)],
            cwd=self.root,
            env={key: value for key, value in self.env.items() if key not in {"GIT_DIR", "GIT_INDEX_FILE"}},
            capture_output=True,
            check=True,
            timeout=60,
        )
        upload = server.with_name(server.name + "-upload-pack")
        upload.write_text(
            "#!/bin/sh\nexec env "
            + shlex.join(
                [
                    f"GIT_DIR={server}",
                    f"GIT_OBJECT_DIRECTORY={objects}",
                    "GIT_NO_REPLACE_OBJECTS=1",
                    GIT,
                    "-c",
                    "core.commitGraph=false",
                    "-c",
                    "uploadpack.allowFilter=true",
                    "-c",
                    "uploadpack.allowAnySHA1InWant=true",
                    "upload-pack",
                ]
            )
            + ' "$@"\n'
        )
        upload.chmod(0o700)
        self._source = (server.as_uri(), upload)

    def _receive(self, oids, *options: str) -> None:
        """Fetch named objects from the source store and prove each one arrived."""
        wanted = sorted(set(oids))
        if not wanted:
            return
        if self._source is None:
            raise SnapshotRefusal("auto_finalize_fsck_failed")
        url, upload = self._source
        listing = "".join(oid + "\n" for oid in wanted)
        try:
            fetched = self.run(
                "-c",
                "protocol.file.allow=always",
                "-c",
                "transfer.fsckObjects=true",
                "fetch",
                # No negotiation: haves would let the source omit trees and
                # blobs this partial repository has never received.
                "--refetch",
                "--no-tags",
                "--no-write-fetch-head",
                "--no-auto-maintenance",
                "--recurse-submodules=no",
                f"--upload-pack={shlex.quote(str(upload))}",
                *options,
                url,
                "--stdin",
                stdin=listing,
                network=True,
            )
            if fetched.returncode:
                raise SnapshotRefusal("auto_finalize_fsck_failed")
            # Partial-clone fetches tolerate absent objects. Lazy fetching is
            # off, so check every requested name directly.
            present = self.run("cat-file", "--batch-check=%(objectname)", stdin=listing)
        except subprocess.TimeoutExpired as exc:
            raise SnapshotRefusal("auto_finalize_copy_timeout") from exc
        if present.returncode or present.stdout.split() != wanted:
            raise SnapshotRefusal("auto_finalize_fsck_failed")

    def _require_closure(self, commits, *options: str) -> None:
        """Every tree (and, without a filter, every blob) of each commit is present."""
        try:
            listed = self.run("rev-list", "--objects", "--no-walk", "--missing=error", *options, *commits)
        except subprocess.TimeoutExpired as exc:
            raise SnapshotRefusal("auto_finalize_copy_timeout") from exc
        if listed.returncode:
            raise SnapshotRefusal("auto_finalize_fsck_failed")

    def _root_trees(self, commits) -> list[str]:
        # Read from the received commits: their trees may not be here yet.
        return self.checked("log", "--no-walk", "--format=%T", *commits).split() if commits else []

    def receive_trees(self, commits) -> None:
        """Receive every tree of the commits the history checks read, and their attribute files.

        check-attr treats a missing .gitattributes blob as no attributes, so
        each one in these trees must arrive and be proven present as well.
        """
        if self._source is None:
            return
        commits = sorted(set(commits))
        trees = self._root_trees(commits)
        self._receive(trees, "--filter=blob:none")
        self._require_closure(commits, "--filter=blob:none")
        attributes = set()
        for tree in set(trees):
            for row in self.checked("ls-tree", "-r", "-z", tree).split("\0"):
                metadata, _, name = row.partition("\t")
                if name.rpartition("/")[2] == ".gitattributes" and metadata.split()[1] == "blob":
                    attributes.add(metadata.split()[2])
        self._receive(attributes)

    def fetch_remote_commits(self, ref: str, *tips: str) -> None:
        """Receive the commit graph of a destination ref; trees are never needed."""
        proc = self.run(
            "-c",
            "transfer.fsckObjects=true",
            "fetch",
            "--no-tags",
            "--no-write-fetch-head",
            "--no-auto-maintenance",
            "--recurse-submodules=no",
            "--filter=tree:0",
            *(f"--negotiation-tip={tip}" for tip in tips),
            "origin",
            ref,
            network=True,
        )
        if proc.returncode:
            raise SnapshotRefusal("rescue_input_unreadable")

    def receive_publication(
        self, *, head: str, base: str, objects: Path | None = None, exclusions: tuple[str, ...] | None = None,
    ) -> None:
        """Receive the validation and packing snapshots, re-hashed.

        Preserve the original preparation range and add the outgoing range.
        Packing may also read a previous remote tip as a delta base. Excluded
        ancestors need their trees for the outgoing-object walk.
        ``objects``, when given, is a store that already holds them all.
        """
        if exclusions == ():
            # An unavailable destination boundary must not turn the outgoing
            # range into the source's entire history.
            raise SnapshotRefusal("auto_finalize_remote_unverified")
        if self._source is None:
            raise SnapshotRefusal("auto_finalize_validation_unavailable")
        if objects is not None:
            self._serve(objects)
        driver = getattr(self, "driver_base", base)
        # Keep the original preparation range: Git's packer can read an old
        # branch-tip blob as a delta base even when that tip is already remote.
        scoped = self.checked("rev-list", head, "--not", base, driver).split()
        if exclusions is not None:
            scoped.extend(self.checked("rev-list", head, "--not", *exclusions).split())
        commits = sorted({base, head, *scoped})
        self._receive(self._root_trees(commits), "--no-filter")
        self._require_closure(commits)
        if exclusions is not None:
            self.receive_trees(set(exclusions) - set(commits))

    def prepare_validation(
        self, *, head: str, branch: str, base: str, interpreter: Path, exclusions: tuple[str, ...] | None = None,
    ) -> None:
        """Materialize an isolated checkout with the validated driver's trusted hook chain.

        Subprocesses which clear GIT_* still discover only our configuration,
        refs and objects. No worker hook, config or tracking ref is imported.
        Code run in the checkout can write this repository, so it is never
        the one a credentialed push reads.
        """
        self.receive_publication(head=head, base=base, exclusions=exclusions)
        checkout = self.root / "checkout"
        checkout.mkdir()
        self.checked("config", "core.bare", "false")
        self.checked("config", "core.worktree", str(checkout))
        (checkout / ".git").write_text(f"gitdir: {self.git_dir}\n")
        self.checked("update-ref", f"refs/heads/{branch}", head)
        self.checked("symbolic-ref", "HEAD", f"refs/heads/{branch}")
        self.checked("update-ref", "refs/remotes/origin/main", base)
        self.checked("read-tree", "--reset", "-u", head, work_tree=checkout)
        shutil.copyfile(self.root / "index", self.git_dir / "index")
        self.env["GIT_INDEX_FILE"] = str(self.git_dir / "index")
        # The canonical launcher discovers the shared interpreter through
        # .venv. This link exists only in the disposable validation checkout.
        if os.path.lexists(checkout / ".venv") or not interpreter.is_file():
            raise SnapshotRefusal("auto_finalize_validation_unavailable")
        (checkout / ".venv").symlink_to(interpreter.parent.parent, target_is_directory=True)
        trusted = self.root / "trusted"
        hooks = trusted / ".githooks"
        hooks.mkdir(parents=True)
        driver = getattr(self, "driver_base", base)
        self.receive_trees([driver])
        paths = self.checked("ls-tree", "-r", "-z", driver, "--", ".githooks", "scripts/common/test_slots.py")
        self._receive([row.split("\t", 1)[0].split()[2] for row in paths.split("\0") if row])
        for row in paths.split("\0"):
            if not row:
                continue
            metadata, name = row.split("\t", 1)
            mode, kind, oid = metadata.split()
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise SnapshotRefusal("auto_finalize_validation_unavailable")
            destination = trusted / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            blob = self.run("cat-file", "blob", oid, binary=True)
            if blob.returncode:
                raise SnapshotRefusal("auto_finalize_validation_unavailable")
            destination.write_bytes(blob.stdout)
            destination.chmod(0o755 if mode == "100755" else 0o644)
        if not (hooks / "pre-push").is_file() or not os.access(hooks / "pre-push", os.X_OK):
            raise SnapshotRefusal("auto_finalize_validation_unavailable")
        self.checked("config", "core.hooksPath", str(hooks))
        self.checkout = checkout

    def prepare_lfs(self, *, head: str, exclusions: tuple[str, ...]) -> tuple[str, ...]:
        """Select outgoing pointers from re-hashed trees and seal their verified local bytes.

        Only refs proved at the pinned destination exclude history. Neither
        worker LFS configuration nor the validation checkout selects storage.
        All reads and verification finish before the transport obtains a token.
        """
        commits = self.checked("rev-list", head, "--not", *exclusions).split()
        # receive_publication already rehashed these snapshots. Prove their
        # closure here without fetching and storing them a second time.
        self._require_closure(commits)
        objects = self.checked("rev-list", "--objects", "--no-object-names", head, "--not", *exclusions)
        sizes = self.checked("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)", stdin=objects + "\n") if objects else ""
        lfs = shutil.which("git-lfs", path=os.defpath)
        if not lfs:
            raise SnapshotRefusal("auto_finalize_validation_unavailable")
        pointers = {}
        for row in sizes.splitlines():
            blob, kind, size = row.split()
            if kind != "blob" or int(size) >= 1024:
                continue
            data = self.run("cat-file", "blob", blob, binary=True)
            if data.returncode:
                raise SnapshotRefusal("auto_finalize_fsck_failed")
            # Git LFS treats an empty blob as an empty file, with no upload.
            if not data.stdout:
                continue
            recognized = subprocess.run(
                [lfs, "pointer", "--check", "--no-strict", "--stdin"],
                cwd=self.root, env=self.env, input=data.stdout,
                capture_output=True, check=False, timeout=60,
            )
            if recognized.returncode == 1 and not data.stdout.startswith(b"version https://git-lfs.github.com/spec/"):
                continue
            if recognized.returncode:
                raise SnapshotRefusal("auto_finalize_fsck_failed")
            # A native-recognized representation we cannot verify must refuse,
            # rather than silently drop an ordinary push's LFS obligation.
            pointer = re.fullmatch(
                rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (0|[1-9][0-9]*)\n",
                data.stdout,
            )
            if pointer is None:
                raise SnapshotRefusal("auto_finalize_fsck_failed")
            oid, length = pointer[1].decode(), int(pointer[2])
            if oid in pointers and pointers[oid] != length:
                raise SnapshotRefusal("auto_finalize_fsck_failed")
            pointers[oid] = length
        for oid, length in pointers.items():
            source = self.lfs_objects / oid[:2] / oid[2:4] / oid
            destination = self.git_dir / "lfs/objects" / oid[:2] / oid[2:4] / oid
            try:
                if any(path.is_symlink() for path in (source, *source.parents)):
                    raise SnapshotRefusal("auto_finalize_fsck_failed")
                fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, "rb") as incoming:
                    info = os.fstat(incoming.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size != length:
                        raise SnapshotRefusal("auto_finalize_fsck_failed")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open("xb") as outgoing:
                        digest = hashlib.sha256()
                        copied = 0
                        while chunk := incoming.read(1024 * 1024):
                            copied += len(chunk)
                            digest.update(chunk)
                            outgoing.write(chunk)
                    if copied != length or digest.hexdigest() != oid:
                        raise SnapshotRefusal("auto_finalize_fsck_failed")
            except OSError as exc:
                raise SnapshotRefusal("auto_finalize_fsck_failed") from exc
        return tuple(sorted(pointers))

    def read_source_ref(self, source: Path, ref: str, *, symbolic: bool = False) -> subprocess.CompletedProcess[str]:
        """Plumbing-only read of source refs: no worktree, network, hooks or index."""
        env = {
            key: self.env[key]
            for key in (
                "PATH",
                "HOME",
                "LC_ALL",
                "GIT_CONFIG_NOSYSTEM",
                "GIT_CONFIG_GLOBAL",
                "GIT_TERMINAL_PROMPT",
                "GIT_NO_REPLACE_OBJECTS",
                "GIT_NO_LAZY_FETCH",
            )
        }
        args = ["--symbolic-full-name", ref] if symbolic else ["--verify", "--quiet", f"{ref}^{{commit}}"]
        return subprocess.run(
            [GIT, f"--git-dir={source}", "rev-parse", *args],
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )

    def checked(self, *args: str, **kwargs) -> str:
        proc = self.run(*args, **kwargs)
        if proc.returncode:
            raise SnapshotRefusal("rescue_input_unreadable")
        return proc.stdout.strip() if "-z" not in args else proc.stdout

    def refuse_tree(self, base: str, tree: str) -> None:
        """Reject named filters and newly introduced gitlinks, including committed work."""
        paths = self.checked("diff-tree", "-r", "--no-renames", "--name-only", "-z", base, tree).split("\0")
        paths = [path for path in paths if path]
        for source in (base, tree):
            self._refuse_filters(paths, source=source)
        old = self.checked("ls-tree", "-r", "-z", base).split("\0")
        existing = {line for line in old if line.startswith("160000 ")}
        new = self.checked("ls-tree", "-r", "-z", tree).split("\0")
        if any(line.startswith("160000 ") and line not in existing for line in new):
            raise SnapshotRefusal("rescue_new_gitlink")

    def _refuse_filters(self, paths: list[str], *, source: str | None = None, work_tree: Path | None = None) -> None:
        if not paths:
            return
        options = (f"--source={source}",) if source else ()
        output = self.checked(
            "check-attr",
            *options,
            "-z",
            "--stdin",
            "filter",
            work_tree=work_tree,
            stdin="\0".join(paths) + "\0",
        ).split("\0")
        if any(output[i] not in {"unspecified", "unset"} for i in range(2, len(output), 3)):
            raise SnapshotRefusal("rescue_filtered_path")

    def capture(
        self,
        work_tree: Path,
        head: str,
        *,
        worker_index: Path | None = None,
        exclude_file: Path | None = None,
    ) -> str:
        """Hermetic add -A of the working post-image, seeded from HEAD, with stability proof."""
        self.checked("read-tree", head)
        # Per-repository exclusions are plaintext selection data, not config.
        # Copy them explicitly so a fresh repo does not sweep ignored output in.
        self._exclude_snapshot = None
        if exclude_file is not None:
            before_excludes = self._signatures(exclude_file.parent, [exclude_file.name])
            try:
                data = b""
                if os.path.lexists(exclude_file):
                    fd = os.open(exclude_file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    with os.fdopen(fd, "rb") as stream:
                        data = stream.read()
            except OSError as exc:
                raise SnapshotRefusal("rescue_input_unreadable") from exc
            if before_excludes != self._signatures(exclude_file.parent, [exclude_file.name]):
                raise SnapshotRefusal("rescue_input_changed")
            (self.git_dir / "info").mkdir(exist_ok=True)
            (self.git_dir / "info/exclude").write_bytes(data)
            self._exclude_snapshot = (exclude_file, before_excludes)
        # Sparse workers have absent skip-worktree paths; preserve those HEAD
        # entries rather than turning sparse exclusions into tracked deletions.
        if worker_index is not None and worker_index.is_file():
            copied = self.root / "worker-index"
            try:
                info = worker_index.stat()
                if not info.st_mode & 0o444:
                    raise SnapshotRefusal("rescue_input_unreadable")
                shutil.copyfile(worker_index, copied)
                current = worker_index.stat()
                if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns) != (
                    info.st_dev,
                    info.st_ino,
                    info.st_size,
                    info.st_mtime_ns,
                    info.st_ctime_ns,
                ):
                    raise SnapshotRefusal("rescue_input_changed")
            except OSError as exc:
                raise SnapshotRefusal("rescue_input_unreadable") from exc
            skipped = self.checked("ls-files", "-t", "-z", index=copied).split("\0")
            absent = [
                entry[2:] for entry in skipped if entry.startswith("S ") and not os.path.lexists(work_tree / entry[2:])
            ]
            if absent:
                self.checked(
                    "update-index",
                    "--skip-worktree",
                    "-z",
                    "--stdin",
                    work_tree=work_tree,
                    stdin="\0".join(absent) + "\0",
                )
        paths = self._paths(work_tree)
        before = self._signatures(work_tree, paths)
        self.checked("add", "-A", work_tree=work_tree)
        tree = self.checked("write-tree")
        if not set(self._paths(work_tree)).issubset(paths) or before != self._signatures(work_tree, paths):
            raise SnapshotRefusal("rescue_input_changed")
        changed = [
            path for path in self.checked("diff-tree", "-r", "--name-only", "-z", head, tree).split("\0") if path
        ]
        self._refuse_filters(changed, work_tree=work_tree)
        self.refuse_tree(head, tree)
        self._snapshot = (work_tree, paths, before)
        return tree

    def verify_inputs(self) -> None:
        """Recheck the captured inputs just before publication, after content checking."""
        if self._exclude_snapshot is not None:
            path, before_excludes = self._exclude_snapshot
            if before_excludes != self._signatures(path.parent, [path.name]):
                raise SnapshotRefusal("rescue_input_changed")
        work_tree, paths, before = self._snapshot
        if not set(self._paths(work_tree)).issubset(paths) or before != self._signatures(work_tree, paths):
            raise SnapshotRefusal("rescue_input_changed")

    def _paths(self, work_tree: Path) -> list[str]:
        return sorted(
            {
                path.rstrip("/")
                for path in self.checked(
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "-z",
                    work_tree=work_tree,
                ).split("\0")
                if path
            }
        )

    @staticmethod
    def _signatures(work_tree: Path, paths: list[str]) -> dict:
        names = set(paths)
        for name in paths:
            parent = Path(name).parent
            for ancestor in (parent, *parent.parents):
                names.update(str(ancestor / control) for control in (".gitignore", ".gitattributes"))
        signatures = {}
        try:
            for name in sorted(names):
                path = work_tree / name
                for parent in path.parents:
                    if parent == work_tree:
                        break
                    try:
                        parent_info = parent.lstat()
                    except FileNotFoundError:
                        continue
                    if not stat.S_ISDIR(parent_info.st_mode):
                        raise SnapshotRefusal("rescue_input_changed")
                    if not parent_info.st_mode & 0o555:
                        raise SnapshotRefusal("rescue_input_unreadable")
                    signatures[str(parent.relative_to(work_tree)) + "/"] = (
                        parent_info.st_dev,
                        parent_info.st_ino,
                        parent_info.st_mode,
                        parent_info.st_mtime_ns,
                        parent_info.st_ctime_ns,
                    )
                    if os.path.lexists(parent / ".git"):
                        raise SnapshotRefusal("rescue_embedded_repository")
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    signatures[name] = None
                    continue
                if stat.S_ISDIR(info.st_mode):
                    if os.path.lexists(path / ".git"):
                        raise SnapshotRefusal("rescue_embedded_repository")
                    signatures[name] = (info.st_mode, info.st_ino, info.st_mtime_ns)
                    continue
                if stat.S_ISLNK(info.st_mode):
                    digest = hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest()
                elif stat.S_ISREG(info.st_mode):
                    if not info.st_mode & 0o444:
                        raise SnapshotRefusal("rescue_input_unreadable")
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    with os.fdopen(fd, "rb") as stream:
                        opened = os.fstat(stream.fileno())
                        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                            raise SnapshotRefusal("rescue_input_changed")
                        digest = hashlib.file_digest(stream, "sha256").hexdigest()
                else:
                    raise SnapshotRefusal("rescue_input_unreadable")
                current = path.lstat()

                def fingerprint(st):
                    return (st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns, st.st_ctime_ns)

                if fingerprint(info) != fingerprint(current):
                    raise SnapshotRefusal("rescue_input_changed")
                signatures[name] = (*fingerprint(info), digest)
        except OSError as exc:
            raise SnapshotRefusal("rescue_input_unreadable") from exc
        return signatures
