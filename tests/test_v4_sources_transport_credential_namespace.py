"""The Sources scoped credential resolves only from the unit's own systemd namespace."""

from __future__ import annotations

import os
import stat

import pytest
from learn_ukrainian_v4_runtime import sources_transport
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused

SYSTEM = f"/run/credentials/{sources_transport.SOURCES_UNIT}"
USER = f"/run/user/{os.getuid()}/credentials/{sources_transport.SOURCES_UNIT}"


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "relative/credentials",
        "/tmp/credentials",
        "/run/credentials/hramatka-api.service",
        f"/run/user/{os.getuid() + 1}/credentials/{sources_transport.SOURCES_UNIT}",
        f"/run/user/{os.getuid()}/credentials/other.service",
        SYSTEM + "/",
    ],
)
def test_unset_or_foreign_credentials_directory_refuses(monkeypatch, raw):
    if raw is None:
        monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    else:
        monkeypatch.setenv("CREDENTIALS_DIRECTORY", raw)
    with pytest.raises(OperationRefused):
        sources_transport.credential_path()
    with pytest.raises(OperationRefused):
        with sources_transport.sources_connection():
            pass
    # An unauthenticated attempt is refused, never a crash, on a missing namespace.
    assert sources_transport.resolve_attempt("token") is None


@pytest.mark.parametrize("namespace", [SYSTEM, USER])
def test_system_and_own_user_namespaces_resolve_the_scoped_dsn(monkeypatch, namespace):
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", namespace)
    assert str(sources_transport.credential_path()) == namespace + "/v4-sources-dsn"


def test_connection_requires_a_private_regular_file_owned_by_the_unit(monkeypatch, tmp_path):
    credential = tmp_path / "v4-sources-dsn"
    credential.write_text("dbname=refused")
    monkeypatch.setattr(sources_transport, "credential_path", lambda: credential)

    credential.chmod(0o640)
    with pytest.raises(OperationRefused):
        with sources_transport.sources_connection():
            pass

    credential.chmod(0o400)
    foreign = os.getuid() + 1
    monkeypatch.setattr(os, "getuid", lambda: foreign)
    with pytest.raises(OperationRefused):
        with sources_transport.sources_connection():
            pass
    monkeypatch.undo()
    monkeypatch.setattr(sources_transport, "credential_path", lambda: tmp_path / "link")
    (tmp_path / "link").symlink_to(credential)
    with pytest.raises(OperationRefused):
        with sources_transport.sources_connection():
            pass
    assert stat.S_IMODE(credential.stat().st_mode) == 0o400
