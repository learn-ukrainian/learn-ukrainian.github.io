"""Descriptor-bound custody checks for systemd-provisioned credential files.

systemd ``LoadCredential=`` materializes two legitimate shapes, and both must
be read with the same fail-closed discipline:

* **Owner-private** (a per-user manager, e.g. the existing Sources unit): the
  file is ``0400`` and owned by the service uid, with no access ACL.
* **Root-owned with a POSIX access ACL** (a system-manager unit running as an
  unprivileged ``User=``): the file is owned by uid/gid 0 and carries
  ``user::r--``, exactly one ``user:<service uid>:r--``, ``group::---``,
  ``mask::r--``, ``other::---``. Its ``st_mode`` reads ``0440`` because the
  kernel reports the ACL *mask* in the group triplet -- that is not a grant to
  the owning group, so a blanket ``st_mode & 0o077`` test misreads the file as
  shared and refuses a correctly private credential.

``evaluate_access`` therefore reproduces the kernel's POSIX ACL decision from
the exact metadata (mode, owner, raw ``system.posix_acl_access`` xattr) instead
of a bitmask, and accepts only when the service principal, and nobody else
besides root, can read; nobody may write or execute. The reader binds every
check to the descriptor it reads from (directory descriptor, ``O_NOFOLLOW``,
``fstat`` before and after the read), so a swapped path component, a symlink or
a concurrent rewrite cannot slip past the check. It never logs, formats or
chains credential bytes; only stable refusal codes leave this module.

An absent or inaccessible namespace or credential propagates its own
``OSError`` so every caller keeps its existing "not provisioned" taxonomy.
"""

from __future__ import annotations

import errno
import os
import stat
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MAX_CREDENTIAL_BYTES = 65536

ACL_XATTR = "system.posix_acl_access"
ACL_VERSION = 2
ACL_UNDEFINED_ID = 0xFFFFFFFF
ACL_USER_OBJ, ACL_USER, ACL_GROUP_OBJ, ACL_GROUP, ACL_MASK, ACL_OTHER = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20
ACL_READ, ACL_WRITE, ACL_EXECUTE = 0o4, 0o2, 0o1

_ENTRY = struct.Struct("<HHI")
_HEADER = struct.Struct("<I")
# Not provisioned for this principal: propagated unchanged, never a custody verdict.
_UNAVAILABLE = (FileNotFoundError, NotADirectoryError, PermissionError)


class CredentialCustodyError(Exception):
    """A credential object is not in a shape this runtime may trust. The
    message is one stable code; it never carries credential bytes."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def parse_access_acl(raw: bytes) -> list[tuple[int, int, int]]:
    """Decode a raw ``system.posix_acl_access`` value into ``(tag, perms, id)``
    entries. Refuses anything but the kernel's version-2 wire format."""
    if len(raw) < _HEADER.size or (len(raw) - _HEADER.size) % _ENTRY.size:
        raise CredentialCustodyError("credential_acl_malformed")
    (version,) = _HEADER.unpack_from(raw, 0)
    if version != ACL_VERSION:
        raise CredentialCustodyError("credential_acl_malformed")
    return [_ENTRY.unpack_from(raw, offset) for offset in range(_HEADER.size, len(raw), _ENTRY.size)]


def _validated_entries(st_mode: int, acl: bytes | None) -> dict:
    mode = stat.S_IMODE(st_mode)
    owner_bits, group_bits, other_bits = (mode >> 6) & 0o7, (mode >> 3) & 0o7, mode & 0o7
    if acl is None:
        entries = [
            (ACL_USER_OBJ, owner_bits, ACL_UNDEFINED_ID),
            (ACL_GROUP_OBJ, group_bits, ACL_UNDEFINED_ID),
            (ACL_OTHER, other_bits, ACL_UNDEFINED_ID),
        ]
    else:
        entries = parse_access_acl(acl)
    malformed = CredentialCustodyError("credential_acl_malformed")
    tags = [tag for tag, _, _ in entries]
    # The kernel stores entries in canonical tag order with the three
    # required entries present exactly once; anything else is not an ACL the
    # kernel would have produced.
    if tags != sorted(tags) or any(
        tag not in (ACL_USER_OBJ, ACL_USER, ACL_GROUP_OBJ, ACL_GROUP, ACL_MASK, ACL_OTHER) for tag in tags
    ):
        raise malformed
    if (
        tags.count(ACL_USER_OBJ) != 1
        or tags.count(ACL_GROUP_OBJ) != 1
        or tags.count(ACL_OTHER) != 1
        or tags.count(ACL_MASK) > 1
    ):
        raise malformed
    named_users: dict[int, int] = {}
    named_groups: dict[int, int] = {}
    singular: dict[int, int] = {}
    for tag, perms, identifier in entries:
        if perms & ~(ACL_READ | ACL_WRITE | ACL_EXECUTE):
            raise malformed
        if tag in (ACL_USER, ACL_GROUP):
            target = named_users if tag == ACL_USER else named_groups
            if identifier == ACL_UNDEFINED_ID or identifier in target:
                raise malformed
            target[identifier] = perms
        else:
            if identifier != ACL_UNDEFINED_ID:
                raise malformed
            singular[tag] = perms
    mask = singular.get(ACL_MASK)
    if (named_users or named_groups) and mask is None:
        raise malformed
    if mask is not None and not (named_users or named_groups):
        # A mask without named entries is not a shape systemd or a minimal
        # ACL produces; refuse rather than reason about it.
        raise CredentialCustodyError("credential_acl_unsupported")
    # The kernel keeps the mode bits and the ACL in lockstep: owner bits are
    # USER_OBJ, other bits are OTHER, and the group bits are the MASK when one
    # exists, else GROUP_OBJ. Disagreement means the metadata is not coherent.
    if (
        singular[ACL_USER_OBJ] != owner_bits
        or singular[ACL_OTHER] != other_bits
        or (mask if mask is not None else singular[ACL_GROUP_OBJ]) != group_bits
    ):
        raise malformed
    return {
        "user_obj": singular[ACL_USER_OBJ],
        "group_obj": singular[ACL_GROUP_OBJ],
        "other": singular[ACL_OTHER],
        "mask": mask,
        "named_users": named_users,
        "named_groups": named_groups,
    }


def evaluate_access(
    *, st_mode: int, st_uid: int, acl: bytes | None, principal_uid: int, allowed: int = ACL_READ
) -> None:
    """Refuse unless the kernel would grant exactly ``allowed`` to
    ``principal_uid``, nothing to any other non-root principal, and no write
    or execute bit to anyone (root's own owner bits may only be a subset of
    ``allowed``; root bypasses the check anyway).

    ``acl`` is the raw access-ACL xattr, or ``None`` when the object has only
    its mode bits. Accepts the owner-private form (owner is the principal) and
    the root-owned named-user form systemd produces for unprivileged
    ``User=`` services; refuses every group, world or extra-principal grant.
    """
    if stat.S_IMODE(st_mode) & 0o7000:
        raise CredentialCustodyError("credential_mode")
    entries = _validated_entries(st_mode, acl)
    if entries["other"] or entries["group_obj"] or entries["named_groups"]:
        raise CredentialCustodyError("credential_acl_principal")
    if st_uid == principal_uid:
        if entries["named_users"]:
            raise CredentialCustodyError("credential_acl_principal")
        if entries["user_obj"] != allowed:
            raise CredentialCustodyError("credential_mode")
        return
    if st_uid != 0:
        raise CredentialCustodyError("credential_owner")
    if entries["user_obj"] & ~allowed:
        raise CredentialCustodyError("credential_mode")
    if list(entries["named_users"]) != [principal_uid]:
        raise CredentialCustodyError("credential_acl_principal")
    if entries["named_users"][principal_uid] != allowed or entries["mask"] != allowed:
        raise CredentialCustodyError("credential_mode")


def _access_acl(fd: int) -> bytes | None:
    try:
        return os.getxattr(fd, ACL_XATTR)
    except OSError as exc:
        if exc.errno in (errno.ENODATA, errno.ENOTSUP):
            return None
        raise CredentialCustodyError("credential_acl_unreadable") from exc


@contextmanager
def opened_credential(path: Path, *, principal_uid: int | None = None) -> Iterator[tuple[int, os.stat_result]]:
    """Open ``path`` as a verified credential and yield ``(fd, stat)``.

    The parent directory is opened first (``O_DIRECTORY|O_NOFOLLOW``) and must
    be a directory owned by root or the principal that nobody else can write;
    the credential is then opened relative to that descriptor with
    ``O_NOFOLLOW`` and judged from ``fstat``/``fgetxattr`` on the descriptor
    itself. An absent or inaccessible namespace or credential propagates its
    own ``OSError`` (``FileNotFoundError``, ``NotADirectoryError``,
    ``PermissionError``): that is "not provisioned for this principal", not a
    custody verdict about an object we could inspect.
    """
    principal_uid = os.geteuid() if principal_uid is None else principal_uid
    if not path.is_absolute() or path.name in ("", ".", ".."):
        raise CredentialCustodyError("credential_directory")
    directory_fd = fd = None
    try:
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            directory = os.fstat(directory_fd)
        except _UNAVAILABLE:
            raise
        except OSError as exc:
            raise CredentialCustodyError("credential_directory") from exc
        if (
            not stat.S_ISDIR(directory.st_mode)
            or directory.st_uid not in (0, principal_uid)
            or directory.st_mode & 0o022
        ):
            raise CredentialCustodyError("credential_directory")
        try:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory_fd)
            status = os.fstat(fd)
        except _UNAVAILABLE:
            raise
        except OSError as exc:
            raise CredentialCustodyError(
                "credential_symlink" if exc.errno == errno.ELOOP else "credential_open"
            ) from exc
        if not stat.S_ISREG(status.st_mode):
            raise CredentialCustodyError("credential_not_regular")
        evaluate_access(st_mode=status.st_mode, st_uid=status.st_uid, acl=_access_acl(fd), principal_uid=principal_uid)
        yield fd, status
    finally:
        for descriptor in (fd, directory_fd):
            if descriptor is not None:
                os.close(descriptor)


def verify_credential(path: Path, *, max_bytes: int = MAX_CREDENTIAL_BYTES, principal_uid: int | None = None) -> None:
    """Custody check without reading the content."""
    with opened_credential(path, principal_uid=principal_uid) as (_, status):
        if not 0 < status.st_size <= max_bytes:
            raise CredentialCustodyError("credential_size")


def read_credential(path: Path, *, max_bytes: int = MAX_CREDENTIAL_BYTES, principal_uid: int | None = None) -> bytes:
    """Read a verified credential's bytes, refusing if the object changes
    between the pre-read and post-read ``fstat`` (size, mtime, ctime)."""
    with opened_credential(path, principal_uid=principal_uid) as (fd, before):
        if not 0 < before.st_size <= max_bytes:
            raise CredentialCustodyError("credential_size")
        chunks = bytearray()
        try:
            while len(chunks) <= max_bytes:
                chunk = os.read(fd, max_bytes + 1 - len(chunks))
                if not chunk:
                    break
                chunks.extend(chunk)
            after = os.fstat(fd)
        except OSError as exc:
            raise CredentialCustodyError("credential_read") from exc
        if before.st_size != len(chunks) or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise CredentialCustodyError("credential_changed")
        return bytes(chunks)
