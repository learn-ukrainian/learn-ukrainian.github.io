"""Host-only output boundary, with descriptor-relative no-symlink writes."""

import os
import re
import stat
from contextlib import contextmanager, suppress
from pathlib import Path
from threading import RLock

from .errors import BuildError, require

_UMASK_LOCK = RLock()


@contextmanager
def private_umask():
    with _UMASK_LOCK:
        prior = os.umask(0o077)
        try:
            yield
        finally:
            os.umask(prior)


FILESYSTEMS = frozenset({"ext4", "xfs", "btrfs"})


def filesystem(path: Path) -> str:
    mounts = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        head, tail = line.split(" - ", 1)
        mount = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), head.split()[4])
        root = Path(mount)
        if path == root or root in path.parents:
            mounts.append((len(root.parts), tail.split()[0]))
    require(bool(mounts), "filesystem_unknown")
    return max(mounts)[1]


def _private(fd: int) -> None:
    info = os.fstat(fd)
    require(info.st_uid == os.getuid(), "output_owner")
    require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700, "output_mode")
    require(not any(n.startswith("system.posix_acl_") for n in os.listxattr(fd)), "output_acl")


def _no_repository(fd: int) -> None:
    try:
        os.stat(".git", dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise BuildError("repository_output")


class OutputGuard:
    """Call before reading text-bearing inputs; never fall back on check failure."""

    def __init__(self, path: Path, protected_roots: tuple[Path, ...] = ()):
        self.fd = -1
        try:
            supplied = Path(path)
            if not supplied.is_absolute():
                supplied = Path.cwd() / supplied
            # Check original components before realpath can erase symlinks/.. .
            original = Path(supplied.anchor)
            for part in supplied.parts[1:]:
                original /= part
                require(not original.is_symlink(), "symlink_output")
            path = Path(os.path.abspath(supplied))
            real = path.resolve()
            for root in protected_roots:
                resolved = root.resolve()
                require(real != resolved and resolved not in real.parents, "repository_output")
            require(filesystem(real) in FILESYSTEMS, "filesystem_refused")
            fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                _no_repository(fd)
                parts = path.parts[1:]
                require(bool(parts), "output_mode")
                for index, part in enumerate(parts):
                    require(part not in {"", ".", ".."}, "output_path")
                    created = False
                    try:
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    except FileNotFoundError:
                        with private_umask():
                            os.mkdir(part, 0o700, dir_fd=fd)
                        created = True
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    os.close(fd)
                    fd = child
                    _no_repository(fd)
                    if created or index == len(parts) - 1:
                        _private(fd)
                self.fd, fd = fd, -1
            finally:
                if fd >= 0:
                    os.close(fd)
            self.path = real
            self._recheck_location()
        except BuildError:
            self.close()
            raise
        except Exception:
            self.close()
            raise BuildError("output_check_unavailable") from None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def _recheck_location(self) -> None:
        # The open descriptor cannot follow a replacement symlink, and a move
        # or overmount must not turn an admitted private path into repo output.
        location = Path(os.readlink(f"/proc/self/fd/{self.fd}")).resolve(strict=True)
        require(location == self.path, "output_path_changed")
        actual, held = location.stat(), os.fstat(self.fd)
        require((actual.st_dev, actual.st_ino) == (held.st_dev, held.st_ino), "output_path_changed")
        require(filesystem(location) in FILESYSTEMS, "filesystem_refused")
        for parent in (location, *location.parents):
            try:
                (parent / ".git").lstat()
            except FileNotFoundError:
                continue
            raise BuildError("repository_output")

    def _directory(self, parts: tuple[str, ...]) -> int:
        self._recheck_location()
        fd = os.dup(self.fd)
        try:
            _private(fd)
            _no_repository(fd)
            for part in parts:
                with private_umask(), suppress(FileExistsError):
                    os.mkdir(part, 0o700, dir_fd=fd)
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
                _private(fd)
                _no_repository(fd)
            return fd
        except BaseException:
            os.close(fd)
            raise

    @staticmethod
    def _parts(name: str) -> tuple[str, ...]:
        require(bool(re.fullmatch(r"[A-Za-z0-9_./-]+", name)), "output_name")
        parts = tuple(name.split("/"))
        require(all(p not in {"", ".", ".."} for p in parts), "output_name")
        return parts

    def write(self, name: str, content: bytes) -> None:
        parts = self._parts(name)
        fd = self._directory(parts[:-1])
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
            with private_umask():
                file_fd = os.open(parts[-1], flags, 0o600, dir_fd=fd)
            try:
                info = os.fstat(file_fd)
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "output_file_type")
                require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600, "output_file_mode")
                require(not any(n.startswith("system.posix_acl_") for n in os.listxattr(file_fd)), "output_acl")
                os.ftruncate(file_fd, 0)
                with os.fdopen(os.dup(file_fd), "wb") as stream:
                    stream.write(content)
            finally:
                os.close(file_fd)
        finally:
            os.close(fd)

    def read(self, name: str) -> bytes:
        parts = self._parts(name)
        fd = self._directory(parts[:-1])
        try:
            file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                info = os.fstat(file_fd)
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "output_file_type")
                require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600, "output_file_mode")
                require(not any(n.startswith("system.posix_acl_") for n in os.listxattr(file_fd)), "output_acl")
                with os.fdopen(os.dup(file_fd), "rb") as stream:
                    return stream.read()
            finally:
                os.close(file_fd)
        finally:
            os.close(fd)
