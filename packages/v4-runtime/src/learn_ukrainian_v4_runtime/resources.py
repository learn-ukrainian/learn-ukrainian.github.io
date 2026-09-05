"""Read-only built-in resources, never filesystem aliases for historical code."""

from __future__ import annotations

import io
from dataclasses import dataclass
from importlib.resources import files
from pathlib import PurePosixPath

NAMESPACE = "learn_ukrainian_v4_runtime"


def safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid resource path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("noncanonical resource path")
    return value


def read_bytes(relative: str) -> bytes:
    relative = safe_relative(relative)
    if relative.startswith("scripts/"):
        raise ValueError("historical logical paths are metadata, not runtime resources")
    return files(NAMESPACE).joinpath(*relative.split("/")).read_bytes()


@dataclass(frozen=True)
class PackageResource:
    """Logical read-only resource name with no os.PathLike/loading interface.

    resolve/relative_to perform lexical resource operations only; they never
    derive an installed filesystem or checkout location. Historical paths are
    deliberately unreadable. Only the provenance validator hashes .blob bytes.
    """

    relative: str = ""

    def __truediv__(self, value: str) -> PackageResource:
        value = safe_relative(str(value))
        return PackageResource(self.relative + "/" + value if self.relative else value)

    def __str__(self) -> str:
        return self.relative

    @property
    def name(self) -> str:
        return PurePosixPath(self.relative).name

    @property
    def parents(self) -> tuple[PackageResource, ...]:
        parts = self.relative.split("/")
        return tuple(PackageResource("/".join(parts[:i])) for i in range(len(parts) - 1, -1, -1))

    @property
    def parent(self) -> PackageResource:
        return self.parents[0]

    def resolve(self) -> PackageResource:
        return self

    def relative_to(self, other: PackageResource) -> PurePosixPath:
        return PurePosixPath(self.relative).relative_to(PurePosixPath(other.relative))

    def read_bytes(self) -> bytes:
        return read_bytes(self.relative)

    def read_text(self, encoding: str = "utf-8") -> str:
        return self.read_bytes().decode(encoding)

    def open(self, mode: str = "r", encoding: str = "utf-8"):
        if mode == "rb":
            return io.BytesIO(self.read_bytes())
        if mode == "r":
            return io.StringIO(self.read_text(encoding))
        raise ValueError("package resources are read-only")

    def is_file(self) -> bool:
        try:
            self.read_bytes()
            return True
        except (FileNotFoundError, IsADirectoryError):
            return False

    def exists(self) -> bool:
        return self.is_file()


def resource_root() -> PackageResource:
    return PackageResource()
