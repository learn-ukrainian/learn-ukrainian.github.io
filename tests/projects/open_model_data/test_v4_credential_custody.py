"""Systemd credential custody: kernel POSIX ACL semantics and descriptor-bound reads.

The positive root-owned fixtures below are the source-free metadata A0 captured
from the actual ``hramatka-api.service`` credential namespace
(``batch_state/reviews/v4-restart-01a0732f/actual-api-credential-acls.json``):
root-owned files with ``st_mode`` 0440 whose access ACL is ``user::r--``,
``user:995:r--``, ``group::---``, ``mask::r--``, ``other::---`` (directory analog
r-x). No credential bytes were read to produce them. Nothing here touches
``/run/credentials`` or qualifies the unit.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import struct
import subprocess
from pathlib import Path

import pytest
from learn_ukrainian_v4_runtime import child_runtime as child
from learn_ukrainian_v4_runtime import credential_custody as custody
from learn_ukrainian_v4_runtime import readiness, scoped_store
from learn_ukrainian_v4_runtime import service_runtime as service
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, digest

API_UID = 995
SOURCES_UID = 1000
UNDEFINED = custody.ACL_UNDEFINED_ID
USER_OBJ, USER, GROUP_OBJ, GROUP, MASK, OTHER = (
    custody.ACL_USER_OBJ,
    custody.ACL_USER,
    custody.ACL_GROUP_OBJ,
    custody.ACL_GROUP,
    custody.ACL_MASK,
    custody.ACL_OTHER,
)


def entries(*, owner=4, users=((API_UID, 4),), group=0, groups=(), mask=4, other=0):
    """Kernel-order ``(tag, permissions, id)`` entries; defaults are the captured live file ACL."""
    result = [(USER_OBJ, owner, UNDEFINED)]
    result.extend((USER, perms, uid) for uid, perms in users)
    result.append((GROUP_OBJ, group, UNDEFINED))
    result.extend((GROUP, perms, gid) for gid, perms in groups)
    if mask is not None:
        result.append((MASK, mask, UNDEFINED))
    result.append((OTHER, other, UNDEFINED))
    return result


# Captured live entries.
LIVE_FILE_ACL = entries()
LIVE_DIRECTORY_ACL = entries(owner=5, users=((API_UID, 5),), mask=5)
LIVE_FILE_MODE = stat.S_IFREG | 0o440
LIVE_DIRECTORY_MODE = stat.S_IFDIR | 0o550


def acl_bytes(acl, *, version=custody.ACL_VERSION) -> bytes:
    return struct.pack("<I", version) + b"".join(struct.pack("<HHI", *entry) for entry in acl)


def refused(code: str, **kwargs):
    with pytest.raises(custody.CredentialCustodyError) as error:
        custody.evaluate_access(**kwargs)
    assert error.value.code == code


# --- kernel ACL semantics over captured live metadata ------------------------


def test_actual_api_credential_acl_grants_only_the_service_principal():
    """The live shape the blanket ``st_mode & 0o077`` test misread as shared."""
    assert LIVE_FILE_MODE & 0o077, "the captured mode really does show the mask in the group triplet"
    custody.evaluate_access(st_mode=LIVE_FILE_MODE, st_uid=0, acl=acl_bytes(LIVE_FILE_ACL), principal_uid=API_UID)
    custody.evaluate_access(
        st_mode=LIVE_DIRECTORY_MODE,
        st_uid=0,
        acl=acl_bytes(LIVE_DIRECTORY_ACL),
        principal_uid=API_UID,
        allowed=custody.ACL_READ | custody.ACL_EXECUTE,
    )


def test_actual_sources_owner_private_credential_is_accepted():
    custody.evaluate_access(st_mode=stat.S_IFREG | 0o400, st_uid=SOURCES_UID, acl=None, principal_uid=SOURCES_UID)


@pytest.mark.parametrize(
    ("code", "st_uid", "principal", "mode", "acl"),
    [
        # Principal boundary: any grant beyond root + the service uid refuses.
        ("credential_acl_principal", 0, API_UID, 0o440, entries(users=((996, 4),))),
        ("credential_acl_principal", 0, API_UID, 0o440, entries(users=((API_UID, 4), (996, 4)))),
        ("credential_acl_principal", 0, API_UID, 0o440, entries(group=4)),
        ("credential_acl_principal", 0, API_UID, 0o440, entries(groups=((5, 4),))),
        ("credential_acl_principal", 0, API_UID, 0o444, entries(other=4)),
        ("credential_acl_principal", 0, 996, 0o440, LIVE_FILE_ACL),
        ("credential_acl_principal", 0, API_UID, 0o440, None),  # plain 0440: a real owning-group grant
        ("credential_acl_principal", 0, API_UID, 0o400, None),  # root-private: the service cannot read it
        ("credential_acl_principal", API_UID, API_UID, 0o440, LIVE_FILE_ACL),  # owner-private plus a named entry
        # Writable or executable inputs refuse, whoever holds the bit.
        ("credential_mode", 0, API_UID, 0o460, entries(users=((API_UID, 6),), mask=6)),
        ("credential_mode", 0, API_UID, 0o640, entries(owner=6)),
        ("credential_mode", 0, API_UID, 0o440, entries(users=((API_UID, 6),))),
        ("credential_mode", 0, API_UID, 0o400, entries(mask=0)),
        ("credential_mode", SOURCES_UID, SOURCES_UID, 0o600, None),
        ("credential_mode", SOURCES_UID, SOURCES_UID, 0o500, None),
        ("credential_mode", SOURCES_UID, SOURCES_UID, 0o000, None),
        ("credential_mode", 0, API_UID, 0o4440, LIVE_FILE_ACL),
        # Wrong owner.
        ("credential_owner", SOURCES_UID, API_UID, 0o440, LIVE_FILE_ACL),
        ("credential_owner", 996, API_UID, 0o400, None),
        # Malformed or unsupported ACLs are never reasoned about.
        ("credential_acl_malformed", 0, API_UID, 0o440, entries(mask=None)),
        ("credential_acl_malformed", 0, API_UID, 0o440, [LIVE_FILE_ACL[1], LIVE_FILE_ACL[0], *LIVE_FILE_ACL[2:]]),
        ("credential_acl_malformed", 0, API_UID, 0o440, [LIVE_FILE_ACL[0], *LIVE_FILE_ACL]),
        ("credential_acl_malformed", 0, API_UID, 0o440, entries(users=((API_UID, 4), (API_UID, 4)))),
        ("credential_acl_malformed", 0, API_UID, 0o440, entries(users=((UNDEFINED, 4),))),
        ("credential_acl_malformed", 0, API_UID, 0o440, [(USER_OBJ, 4, API_UID), *LIVE_FILE_ACL[1:]]),
        ("credential_acl_malformed", 0, API_UID, 0o440, entries(users=((API_UID, 8),))),
        ("credential_acl_malformed", 0, API_UID, 0o440, [LIVE_FILE_ACL[0], (0x40, 4, UNDEFINED), *LIVE_FILE_ACL[2:]]),
        ("credential_acl_malformed", 0, API_UID, 0o400, LIVE_FILE_ACL),  # mode and ACL disagree
        ("credential_acl_malformed", 0, API_UID, 0o440, []),
        ("credential_acl_unsupported", 0, API_UID, 0o440, entries(users=(), group=4)),
    ],
)
def test_refuses_every_other_shape(code, st_uid, principal, mode, acl):
    refused(
        code,
        st_mode=stat.S_IFREG | mode,
        st_uid=st_uid,
        principal_uid=principal,
        acl=None if acl is None else acl_bytes(acl),
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\x02\x00\x00",
        acl_bytes(LIVE_FILE_ACL)[:-1],
        acl_bytes(LIVE_FILE_ACL, version=1),
        acl_bytes(LIVE_FILE_ACL, version=3),
    ],
)
def test_refuses_malformed_acl_wire_format(raw):
    refused("credential_acl_malformed", st_mode=LIVE_FILE_MODE, st_uid=0, acl=raw, principal_uid=API_UID)


def test_parser_matches_the_kernel_wire_format(tmp_path):
    """A real xattr set through setfacl decodes to exactly the captured live entries."""
    if shutil.which("setfacl") is None:
        pytest.skip("setfacl unavailable")
    path = tmp_path / "credential"
    path.write_text("synthetic")
    path.chmod(0o400)
    subprocess.run(["setfacl", "-m", f"u:{API_UID}:r", str(path)], check=True, capture_output=True, timeout=30)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        status = os.fstat(fd)
        raw = os.getxattr(fd, custody.ACL_XATTR)
    finally:
        os.close(fd)
    assert custody.parse_access_acl(raw) == LIVE_FILE_ACL
    assert stat.S_IMODE(status.st_mode) == 0o440
    # Owned by this test user rather than root, so the same ACL is a foreign-owner refusal for the API uid
    # and an extra-principal refusal for the owner.
    refused("credential_owner", st_mode=status.st_mode, st_uid=status.st_uid, acl=raw, principal_uid=API_UID)
    refused(
        "credential_acl_principal", st_mode=status.st_mode, st_uid=status.st_uid, acl=raw, principal_uid=os.geteuid()
    )


# --- descriptor-bound reading ---------------------------------------------------


def open_fds():
    return set(os.listdir("/proc/self/fd"))


def test_reads_an_owner_private_credential_and_closes_descriptors(tmp_path):
    path = tmp_path / "credential"
    path.write_bytes(b"synthetic-credential\n")
    path.chmod(0o400)
    before = open_fds()
    custody.verify_credential(path)
    assert custody.read_credential(path) == b"synthetic-credential\n"
    assert open_fds() == before


def test_missing_credential_propagates_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        custody.read_credential(tmp_path / "absent")


def test_missing_namespace_propagates_file_not_found(tmp_path):
    # An unprovisioned unit has no $CREDENTIALS_DIRECTORY at all: callers keep
    # their "not provisioned" taxonomy instead of receiving a custody verdict.
    before = open_fds()
    with pytest.raises(FileNotFoundError):
        custody.read_credential(tmp_path / "absent-namespace" / "credential")
    assert open_fds() == before


def test_non_directory_namespace_is_a_custody_refusal(tmp_path):
    # Something occupying the namespace path that is not a directory is an
    # inspectable wrong shape, not an absence; it must not leak ENOTDIR.
    (tmp_path / "namespace").write_text("synthetic")
    with pytest.raises(custody.CredentialCustodyError) as error:
        custody.read_credential(tmp_path / "namespace" / "credential")
    assert error.value.code == "credential_directory"


@pytest.mark.parametrize(
    "mutation",
    [
        "writable",
        "group_readable",
        "world_readable",
        "setgid",
        "symlink",
        "directory",
        "fifo",
        "empty",
        "oversize",
        "named_user_acl",
        "named_group_acl",
        "writable_parent",
        "symlink_parent",
        "relative",
        "foreign_namespace",
    ],
)
def test_refuses_unsafe_objects_through_the_descriptor(tmp_path, mutation):
    if mutation.endswith("_acl") and shutil.which("setfacl") is None:
        pytest.skip("setfacl unavailable")
    parent = tmp_path / "namespace"
    parent.mkdir(mode=0o700)
    path = parent / "credential"
    kwargs = {}
    if mutation == "symlink":
        target = tmp_path / "target"
        target.write_text("synthetic")
        target.chmod(0o400)
        path.symlink_to(target)
    elif mutation == "directory":
        path.mkdir(mode=0o500)
    elif mutation == "fifo":
        os.mkfifo(path, 0o400)
    else:
        path.write_text("" if mutation == "empty" else "synthetic")
        path.chmod(
            {"writable": 0o600, "group_readable": 0o440, "world_readable": 0o444, "setgid": 0o2400}.get(mutation, 0o400)
        )
        if mutation == "oversize":
            kwargs["max_bytes"] = 4
        elif mutation == "named_user_acl":
            subprocess.run(["setfacl", "-m", f"u:{API_UID}:r", str(path)], check=True, capture_output=True, timeout=30)
        elif mutation == "named_group_acl":
            subprocess.run(["setfacl", "-m", f"g:{os.getgid()}:r", str(path)], check=True, capture_output=True, timeout=30)
        elif mutation == "writable_parent":
            parent.chmod(0o722)
        elif mutation == "symlink_parent":
            (tmp_path / "alias").symlink_to(parent)
            path = tmp_path / "alias" / "credential"
        elif mutation == "relative":
            path = Path(os.path.relpath(path))
        elif mutation == "foreign_namespace":
            # The namespace belongs to neither root nor the service principal:
            # refused at the directory before the credential is ever opened.
            kwargs["principal_uid"] = os.geteuid() + 1
    expected = {
        "writable": "credential_mode",
        "group_readable": "credential_acl_principal",
        "world_readable": "credential_acl_principal",
        "setgid": "credential_mode",
        "symlink": "credential_symlink",
        "directory": "credential_not_regular",
        "fifo": "credential_not_regular",
        "empty": "credential_size",
        "oversize": "credential_size",
        "named_user_acl": "credential_acl_principal",
        "named_group_acl": "credential_acl_principal",
        "writable_parent": "credential_directory",
        "symlink_parent": "credential_directory",
        "relative": "credential_directory",
        "foreign_namespace": "credential_directory",
    }[mutation]
    before = open_fds()
    with pytest.raises(custody.CredentialCustodyError) as error:
        custody.read_credential(path, **kwargs)
    assert error.value.code == expected
    assert open_fds() == before


def test_refuses_a_credential_rewritten_during_the_read(tmp_path, monkeypatch):
    path = tmp_path / "credential"
    path.write_bytes(b"synthetic-before")
    path.chmod(0o400)
    real_read = os.read

    def racing_read(fd, size):
        chunk = real_read(fd, size)
        if chunk:
            path.chmod(0o600)
            path.write_bytes(b"synthetic-after!")
            path.chmod(0o400)
        return chunk

    monkeypatch.setattr(os, "read", racing_read)
    with pytest.raises(custody.CredentialCustodyError) as error:
        custody.read_credential(path)
    assert error.value.code == "credential_changed"


# --- every production reader consumes the same custody -------------------------


def test_scoped_store_refuses_on_custody_without_opening_a_connection(tmp_path, monkeypatch):
    path = tmp_path / "v4-control-dsn"
    path.write_text("dbname=refused")
    path.chmod(0o440)
    monkeypatch.setattr(scoped_store, "control_credential_path", lambda: path)
    with pytest.raises(OperationRefused, match="scoped_control_credential_required") as error:
        scoped_store.ScopedAuthorityStore()
    assert isinstance(error.value.__cause__, custody.CredentialCustodyError)
    monkeypatch.setattr(scoped_store, "control_credential_path", lambda: tmp_path / "absent")
    with pytest.raises(OperationRefused, match="scoped_control_credential_required") as error:
        scoped_store.ScopedAuthorityStore()
    assert isinstance(error.value.__cause__, FileNotFoundError)


def test_provider_credential_keeps_its_refusal_codes(tmp_path, monkeypatch):
    monkeypatch.setattr(child, "load_profile", lambda: {})
    monkeypatch.setattr(child, "credential_mode", lambda profile, harness: "api_key")
    path = tmp_path / "v4-provider-codex"
    path.write_text('{"credential":"synthetic-selected-provider-token-only"}')
    path.chmod(0o440)
    monkeypatch.setattr(service, "provider_credential_path", lambda harness: path)
    with pytest.raises(OperationRefused, match=r"provider_credential_file$") as error:
        service._provider_credential("codex")
    assert error.value.__suppress_context__
    path.chmod(0o400)
    assert service._provider_credential("codex").value == "synthetic-selected-provider-token-only"


def test_signing_keys_load_only_from_flattened_systemd_names(tmp_path, monkeypatch):
    monkeypatch.setattr(trust, "HRAMATKA_CREDENTIAL_NAMESPACE", tmp_path)
    private, _public = trust.generate_test_keypair()
    nested = tmp_path / trust.SIGNING_KEY_CREDENTIAL
    nested.mkdir(mode=0o700)
    for suffix, value in ((".key", private), (".key_id", "prod-key-1")):
        legacy = nested / ("sources" + suffix)
        legacy.write_text(value)
        legacy.chmod(0o400)
    # The nested layout systemd never creates is not a fallback.
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        trust.load_production_signing_key("sources")
    for suffix, value in ((".key", private), (".key_id", "prod-key-1")):
        flattened = trust.signing_credential_path("sources", suffix)
        assert flattened == tmp_path / f"v4-signing-keys_sources{suffix}"
        flattened.write_text(value)
        flattened.chmod(0o400)
    assert trust.load_production_signing_key("sources") == (private, "prod-key-1")
    # Exact role and suffix only; a key for one role never serves another.
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        trust.load_production_signing_key("a3")
    with pytest.raises(trust.TrustAuthorityError, match="unknown signing-key role"):
        trust.signing_credential_path("caller", ".key")
    with pytest.raises(trust.TrustAuthorityError, match="unknown signing credential suffix"):
        trust.signing_credential_path("sources", ".pem")
    trust.signing_credential_path("sources", ".key").chmod(0o440)
    with pytest.raises(trust.TrustAuthorityError, match="signing credential custody"):
        trust.load_production_signing_key("sources")


def test_readiness_qualifies_the_flattened_namespace_credentials():
    namespace = Path("/run/credentials/hramatka-api.service")
    assert readiness.scoped_credential_paths() == [
        namespace / "v4-control-dsn",
        *[
            namespace / f"v4-signing-keys_{role}{suffix}"
            for role in ("sources", "a3", "fleet_execution")
            for suffix in (".key", ".key_id")
        ],
    ]
    assert readiness.qualification_path().parent == namespace == trust.HRAMATKA_CREDENTIAL_NAMESPACE
    assert service.provider_credential_path("claude").parent == namespace


def test_readiness_reads_the_qualification_through_custody(tmp_path, monkeypatch):
    # Same local bwrap metadata surrogate as test_v4_active_release; never the production binary.
    profile = child.load_profile()

    def local_bwrap(path, expected):
        assert (path, expected) == (profile["bwrap"], profile["bwrap_sha256"])
        return child._verified_file(path, digest(Path(path).read_bytes()))

    monkeypatch.setattr(readiness, "_verified_file", local_bwrap)
    qualification = tmp_path / "v4-unit-qualification.json"
    qualification.write_text(json.dumps({"schema": "hramatka-v4-actual-unit-qualification.v1"}))
    qualification.chmod(0o440)
    monkeypatch.setattr(readiness, "qualification_path", lambda: qualification)
    with pytest.raises(OperationRefused, match="readiness_unproved") as error:
        readiness.require_readiness()
    assert isinstance(error.value.__cause__, custody.CredentialCustodyError)
    assert error.value.__cause__.code == "credential_acl_principal"
