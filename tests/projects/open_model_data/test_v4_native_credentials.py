"""Synthetic native credential transport; never a live provider qualification."""

from __future__ import annotations

import base64
import copy
import fcntl
import json
import os
import time
import traceback
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from _v4_packaged_runtime_fixture import pinned_profile
from learn_ukrainian_v4_runtime import child_runtime as child
from learn_ukrainian_v4_runtime import service_runtime as service
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, digest

MODES = [(harness, mode) for harness in ("claude", "codex") for mode in ("api_key", "subscription")]
SYNTHETIC_TOKEN = "synthetic-selected-provider-token-only"


def jwt(expiry):
    def part(value):
        return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")

    return part({"alg": "RS256"}) + "." + part({"exp": expiry}) + ".synthetic-signature"


def payload(harness, mode):
    result = {"schema": child.CREDENTIAL_SCHEMA, "harness": harness, "mode": mode}
    if mode == "api_key":
        result["credential"] = SYNTHETIC_TOKEN
    else:
        expiry = int(time.time()) + 3600
        result["expires_at"] = expiry
        if harness == "claude":
            result["access_token"] = SYNTHETIC_TOKEN
        else:
            result["auth_json"] = json.dumps(
                {
                    "auth_mode": "chatgpt",
                    "OPENAI_API_KEY": None,
                    "tokens": {
                        "access_token": jwt(expiry),
                        "id_token": jwt(expiry + 1),
                        "refresh_token": SYNTHETIC_TOKEN,
                        "account_id": "synthetic-account",
                    },
                    "last_refresh": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
                }
            )
    return result


def credential(harness, mode):
    return child.parse_provider_credential(json.dumps(payload(harness, mode)).encode(), harness=harness, mode=mode)


def select_mode(profile, harness, mode):
    profile = copy.deepcopy(profile)
    adapter = profile["adapters"][harness]
    adapter["credential_mode"] = mode
    adapter["provider_env"] = {
        ("claude", "api_key"): "ANTHROPIC_API_KEY",
        ("codex", "api_key"): "OPENAI_API_KEY",
        ("claude", "subscription"): "CLAUDE_CODE_OAUTH_TOKEN",
        ("codex", "subscription"): None,
    }[harness, mode]
    return profile


def claim(harness="codex", *, action="normal", role="author"):
    prompt = json.dumps({"harness": harness, "action": action})
    return {
        "request_id": "synthetic-request",
        "attempt_id": "synthetic-attempt",
        "prompt": prompt,
        "capability_token": "synthetic-sources-capability",
        "deadline_at": datetime.now(UTC) + timedelta(seconds=20),
        "binding": {
            "request_id": "synthetic-request",
            "expected_harness": harness,
            "expected_seat_or_model": "fixture-model",
            "role": role,
            "prompt_sha256": digest(prompt.encode()),
        },
    }


@pytest.fixture
def plan_profile(tmp_path):
    executable = tmp_path / "fixture-cli"
    executable.write_bytes(b"synthetic pinned closure")
    executable.chmod(0o400)
    adapter = {
        "version": "synthetic",
        "models": ["fixture-model"],
        "executable": "/runtime/fixture-cli",
        "files": [
            {
                "source": str(executable),
                "destination": "/runtime/fixture-cli",
                "sha256": digest(executable.read_bytes()),
            }
        ],
    }
    return {
        "bwrap": "/usr/bin/bwrap",
        "bwrap_sha256": digest(Path("/usr/bin/bwrap").read_bytes()),
        "sources_url": "http://localhost:8766/mcp",
        "adapters": {
            "claude": {**adapter, "provider_env": "ANTHROPIC_API_KEY"},
            "codex": {**adapter, "provider_env": "OPENAI_API_KEY"},
        },
    }


@pytest.mark.parametrize(("harness", "mode"), MODES)
def test_parent_reads_only_selected_typed_file(tmp_path, monkeypatch, plan_profile, harness, mode):
    profile = select_mode(plan_profile, harness, mode)
    monkeypatch.setattr(child, "load_profile", lambda: profile)
    selected = tmp_path / harness
    selected.write_text(json.dumps(payload(harness, mode)))
    selected.chmod(0o600)
    reads = []

    def path(selected_harness):
        reads.append(selected_harness)
        return selected

    monkeypatch.setattr(service, "provider_credential_path", path)
    value = service._provider_credential(harness)
    assert reads == [harness]
    assert (value.harness, value.mode) == (harness, mode)
    assert SYNTHETIC_TOKEN not in repr(value)
    with pytest.raises(FrozenInstanceError):
        value.mode = "caller-selected"
    command, environment = child._plan(profile, claim(harness), value)
    assert SYNTHETIC_TOKEN not in " ".join(command)
    assert value.value not in " ".join(command)
    assert set(environment) <= {
        "HOME",
        "TMPDIR",
        "PATH",
        "LANG",
        "CODEX_HOME",
        "V4_SOURCES_ATTEMPT_CAPABILITY",
        profile["adapters"][harness]["provider_env"],
    }
    assert "PGPASSWORD" not in environment and "GITHUB_TOKEN" not in environment
    if (harness, mode) == ("codex", "subscription"):
        assert "OPENAI_API_KEY" not in environment and value.value not in environment.values()
    else:
        assert environment[profile["adapters"][harness]["provider_env"]] == SYNTHETIC_TOKEN


@pytest.mark.parametrize("harness", ["claude", "codex"])
def test_legacy_api_key_is_explicit_profile_only(plan_profile, harness):
    raw = json.dumps({"credential": SYNTHETIC_TOKEN}).encode()
    assert child.credential_mode(plan_profile, harness) == "api_key"
    assert child.parse_provider_credential(raw, harness=harness, mode="api_key").value == SYNTHETIC_TOKEN
    with pytest.raises(OperationRefused):
        child.parse_provider_credential(raw, harness=harness, mode="subscription")


@pytest.mark.parametrize(("harness", "mode"), MODES)
@pytest.mark.parametrize(
    "mutation",
    ["schema", "mode", "harness", "opposite", "extra", "missing", "type", "blank", "newline", "nul", "oversize"],
)
def test_refuses_envelope_mutations(harness, mode, mutation):
    value = payload(harness, mode)
    key = "credential" if mode == "api_key" else "auth_json" if harness == "codex" else "access_token"
    if mutation in ("schema", "mode", "harness"):
        value[mutation] = "mismatch"
    elif mutation == "opposite":
        value["ANTHROPIC_API_KEY" if harness == "codex" else "OPENAI_API_KEY"] = "opposite-secret"
    elif mutation == "extra":
        value["model"] = "caller-model"
    elif mutation == "missing":
        del value[key]
    else:
        value[key] = {"type": {}, "blank": "", "newline": "token\n", "nul": "token\0", "oversize": "x" * 65537}[
            mutation
        ]
    with pytest.raises(OperationRefused):
        child.parse_provider_credential(json.dumps(value).encode(), harness=harness, mode=mode)


@pytest.mark.parametrize("raw", [b"null", b"[]", b"{", b"\xff", b'{"credential":"a","credential":"b"}', b"[" * 2000])
def test_malformed_json_is_sanitized(raw):
    with pytest.raises(OperationRefused) as error:
        child.parse_provider_credential(raw, harness="codex", mode="api_key")
    assert error.value.__suppress_context__


@pytest.mark.parametrize("harness", ["codex", "claude"])
@pytest.mark.parametrize("expiry", [None, True, "future", 0, 253402300800, float("inf"), float("nan")])
def test_expiry_requires_bounded_fresh_integer(harness, expiry):
    value = payload(harness, "subscription")
    value["expires_at"] = expiry
    with pytest.raises(OperationRefused, match=r"provider_credential_(expired|schema)"):
        child.parse_provider_credential(json.dumps(value).encode(), harness=harness, mode="subscription")


@pytest.mark.parametrize(
    "mutation",
    [
        "api_key",
        "auth_mode",
        "opposite",
        "extra_token",
        "missing_token",
        "expired_access",
        "invalid_id_expiry",
        "malformed_jwt",
        "missing_exp",
        "duplicate",
        "refresh_type",
        "refresh_future",
    ],
)
def test_codex_native_schema_and_expiry(mutation):
    value = payload("codex", "subscription")
    auth = json.loads(value["auth_json"])
    if mutation == "api_key":
        auth["OPENAI_API_KEY"] = "unselected-key"
    elif mutation == "auth_mode":
        auth["auth_mode"] = "apikey"
    elif mutation == "opposite":
        auth["claudeAiOauth"] = {"accessToken": "opposite-token"}
    elif mutation == "extra_token":
        auth["tokens"]["other"] = "unknown"
    elif mutation == "missing_token":
        del auth["tokens"]["access_token"]
    elif mutation == "expired_access":
        auth["tokens"]["access_token"] = jwt(int(time.time()) - 1)
    elif mutation == "invalid_id_expiry":
        auth["tokens"]["id_token"] = jwt(0)
    elif mutation == "malformed_jwt":
        auth["tokens"]["access_token"] = "malformed"
    elif mutation == "missing_exp":
        auth["tokens"]["access_token"] = "header.e30.signature"
    elif mutation == "refresh_type":
        auth["last_refresh"] = 1
    elif mutation == "refresh_future":
        auth["last_refresh"] = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    value["auth_json"] = json.dumps(auth)
    if mutation == "duplicate":
        value["auth_json"] = value["auth_json"].replace(
            '"auth_mode": "chatgpt"', '"auth_mode": "chatgpt", "auth_mode": "chatgpt"'
        )
    with pytest.raises(OperationRefused):
        child.parse_provider_credential(json.dumps(value).encode(), harness="codex", mode="subscription")


@pytest.mark.parametrize("mutation", ["missing_adapter", "mode", "environment", "extra", "harness", "credential_mode"])
def test_unqualified_profile_refused_before_file_read(monkeypatch, plan_profile, mutation):
    profile = select_mode(plan_profile, "codex", "subscription")
    selected_harness = "codex"
    if mutation == "missing_adapter":
        profile["adapters"] = {}
    elif mutation == "mode":
        profile["adapters"]["codex"]["credential_mode"] = "unknown"
    elif mutation == "environment":
        profile["adapters"]["codex"]["provider_env"] = "ANTHROPIC_API_KEY"
    elif mutation == "extra":
        profile["adapters"]["codex"]["credential_path"] = "/caller"
    elif mutation == "harness":
        selected_harness = "caller"
    else:
        del profile["adapters"]["codex"]["credential_mode"]
    monkeypatch.setattr(child, "load_profile", lambda: profile)
    monkeypatch.setattr(service, "provider_credential_path", lambda _: pytest.fail("unqualified credential read"))
    with pytest.raises(OperationRefused):
        service._provider_credential(selected_harness)


@pytest.mark.parametrize("mutation", ["symlink", "directory", "fifo", "permissions", "oversize", "missing"])
def test_credential_file_boundary(tmp_path, monkeypatch, plan_profile, mutation):
    path = tmp_path / "selected"
    if mutation == "symlink":
        target = tmp_path / "target"
        target.write_text("{}")
        path.symlink_to(target)
    elif mutation == "directory":
        path.mkdir()
    elif mutation == "fifo":
        os.mkfifo(path)
    elif mutation != "missing":
        path.write_bytes(b"x" * 65537 if mutation == "oversize" else b"{}")
        path.chmod(0o644 if mutation == "permissions" else 0o600)
    monkeypatch.setattr(child, "load_profile", lambda: plan_profile)
    monkeypatch.setattr(service, "provider_credential_path", lambda _: path)
    before = set(os.listdir("/proc/self/fd"))
    with pytest.raises(OperationRefused, match="provider_credential_file"):
        service._provider_credential("codex")
    assert set(os.listdir("/proc/self/fd")) == before


NATIVE_CHILD = """#!/runtime/py/bin/python
import json, os, sys, time
from pathlib import Path
request=json.loads(sys.stdin.read())
harness=request["harness"]
keys={"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"}
selected=keys & set(os.environ)
auth=Path("/home/v4/.codex/auth.json")
if auth.exists():
    assert harness=="codex" and not selected
    assert set(Path("/home/v4").iterdir())=={auth.parent}
    assert set(auth.parent.iterdir())=={auth}
    assert auth.stat().st_mode & 0o777==0o400
    native=json.loads(auth.read_bytes())
    assert native["auth_mode"]=="chatgpt"
    secret=native["tokens"]["refresh_token"]
    try:
        auth.write_text("mutation")
    except OSError:
        pass
    else:
        raise AssertionError("auth is not read-only")
else:
    assert len(selected)==1
    assert selected <= ({"OPENAI_API_KEY"} if harness=="codex" else {"ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"})
    secret=os.environ[next(iter(selected))]
assert "PGPASSWORD" not in os.environ and "GITHUB_TOKEN" not in os.environ
assert not Path("/home/ops").exists() and not Path("/run/credentials").exists()
assert not Path("/usr/bin/sh").exists() and not Path("/usr/bin/psql").exists()
assert not Path("/work/scripts").exists()
assert secret not in " ".join(sys.argv)
for fd in Path("/proc/self/fd").iterdir():
    try:
        assert "v4-provider-auth" not in os.readlink(fd)
    except FileNotFoundError:
        pass
if request["action"]=="timeout":
    time.sleep(30)
if request["action"]=="closed_pipes":
    os.close(1); os.close(2); time.sleep(30)
if request["action"] in ("stdout_leak", "stderr_leak"):
    output=sys.stdout if request["action"]=="stdout_leak" else sys.stderr
    output.write(secret[:10]); output.flush(); time.sleep(.02)
    output.write(secret[10:]); output.flush()
else:
    print("synthetic-native-transport-ok")
"""


@pytest.fixture(scope="module")
def native_profile(tmp_path_factory):
    root = tmp_path_factory.mktemp("native-credential-closure")
    profile_path = pinned_profile(root, sources_url="http://localhost:8766/mcp")
    profile = json.loads(profile_path.read_bytes())
    executable = root / "fixture-cli"
    executable.write_text(NATIVE_CHILD)
    for adapter in profile["adapters"].values():
        adapter["models"] = ["fixture-model"]
        for entry in adapter["files"]:
            if entry["destination"] == "/runtime/fixture-cli":
                entry["sha256"] = digest(executable.read_bytes())
    return profile


@pytest.mark.parametrize(("harness", "mode"), MODES)
def test_actual_source_free_bwrap_transport(tmp_path, monkeypatch, native_profile, harness, mode, caplog):
    profile = select_mode(native_profile, harness, mode)
    monkeypatch.setattr(child, "load_profile", lambda: profile)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "opposite-host-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "opposite-host-secret")
    monkeypatch.setenv("PGPASSWORD", "host-database-secret")
    monkeypatch.setenv("GITHUB_TOKEN", "host-signing-secret")
    selected = tmp_path / ("v4-provider-" + harness)
    original = json.dumps(payload(harness, mode)).encode()
    selected.write_bytes(original)
    selected.chmod(0o600)

    def selected_path(name):
        assert name == harness
        return selected

    monkeypatch.setattr(service, "provider_credential_path", selected_path)
    value = service._provider_credential(harness)
    capture = child.run_child(claim(harness), provider_credential=value)
    assert capture.returncode == 0, capture.stderr.decode()
    assert capture.stdout == b"synthetic-native-transport-ok\n"
    assert capture.stderr == b""
    assert SYNTHETIC_TOKEN not in repr(capture) + caplog.text
    assert selected.read_bytes() == original


@pytest.mark.parametrize("action", ["timeout", "closed_pipes", "stdout_leak", "stderr_leak"])
def test_child_failure_discards_secrets_and_closes_fd(monkeypatch, native_profile, action, caplog):
    profile = select_mode(native_profile, "codex", "subscription")
    monkeypatch.setattr(child, "load_profile", lambda: profile)
    value = credential("codex", "subscription")
    owned = claim(action=action)
    if action in ("timeout", "closed_pipes"):
        owned["deadline_at"] = datetime.now(UTC) + timedelta(seconds=0.5)
    before = set(os.listdir("/proc/self/fd"))
    expected = "execution_timeout" if action in ("timeout", "closed_pipes") else "child_credential_disclosure"
    with pytest.raises(OperationRefused, match=expected) as error:
        child.run_child(owned, provider_credential=value)
    assert set(os.listdir("/proc/self/fd")) == before
    assert SYNTHETIC_TOKEN not in str(error.value) + caplog.text


def test_sealed_fd_launch_failure_cleanup(monkeypatch, plan_profile):
    profile = select_mode(plan_profile, "codex", "subscription")
    monkeypatch.setattr(child, "load_profile", lambda: profile)
    value = credential("codex", "subscription")
    seen = []

    def fail_launch(command, **kwargs):
        (fd,) = kwargs["pass_fds"]
        seen.append(fd)
        assert os.pread(fd, 65536, 0) == value.value.encode()
        assert fcntl.fcntl(fd, 1034) == 15  # Linux F_GET_SEALS: all four seals
        assert not os.get_inheritable(fd)
        with pytest.raises(OSError):
            os.ftruncate(fd, 0)
        with pytest.raises(OSError):
            os.write(fd, b"mutation")
        assert command[command.index("--ro-bind-data") + 1 :][:2] == [str(fd), child.CODEX_AUTH_DESTINATION]
        assert SYNTHETIC_TOKEN not in " ".join(command)
        assert value.value not in " ".join(command)
        assert kwargs["close_fds"] is True
        raise OSError(SYNTHETIC_TOKEN)

    monkeypatch.setattr(child.subprocess, "Popen", fail_launch)
    with pytest.raises(OperationRefused, match="child_launch_failed") as error:
        child.run_child(claim(), provider_credential=value)
    assert SYNTHETIC_TOKEN not in "".join(traceback.format_exception(error.value))
    assert len(seen) == 1
    with pytest.raises(OSError):
        os.fstat(seen[0])


def test_credential_mismatch_and_revalidation_before_launch(monkeypatch, plan_profile):
    profile = select_mode(plan_profile, "codex", "subscription")
    monkeypatch.setattr(child, "load_profile", lambda: profile)
    monkeypatch.setattr(child.subprocess, "Popen", lambda *a, **kw: pytest.fail("mismatched launch"))
    for value in (credential("claude", "subscription"), credential("codex", "api_key"), SYNTHETIC_TOKEN):
        with pytest.raises(OperationRefused, match="mismatch"):
            child.run_child(claim(), provider_credential=value)
    expired = child.ProviderCredential("codex", "subscription", credential("codex", "subscription").value, 1)
    with pytest.raises(OperationRefused, match="expired"):
        child.run_child(claim(), provider_credential=expired)


@pytest.mark.parametrize(("harness", "mode"), MODES)
@pytest.mark.parametrize(("role", "effort"), [("author", "medium"), ("reviewer", "high")])
def test_mode_does_not_select_model_effort_or_tools(plan_profile, harness, mode, role, effort):
    profile = select_mode(plan_profile, harness, mode)
    command, _ = child._plan(profile, claim(harness, role=role), credential(harness, mode))
    assert command[command.index("--model") + 1] == "fixture-model"
    if harness == "claude":
        assert command[command.index("--effort") + 1] == effort
        assert command[command.index("--tools") + 1] == ""
        assert "--strict-mcp-config" in command
    else:
        assert 'model_reasoning_effort="' + effort + '"' in command
        assert "features.shell_tool=false" in command and "features.multi_agent=false" in command


def test_seal_failure_closes_memfd(monkeypatch):
    seen = []

    def fail_sealing(fd, *_):
        seen.append(fd)
        raise OSError("synthetic seal failure")

    monkeypatch.setattr(child.fcntl, "fcntl", fail_sealing)
    with pytest.raises(OSError, match="seal failure"):
        child._sealed_auth_fd(b"synthetic-auth-bytes")
    assert len(seen) == 1
    with pytest.raises(OSError):
        os.fstat(seen[0])


def test_credential_does_not_enter_digests_or_mutate_profile(monkeypatch, native_profile):
    profile = select_mode(native_profile, "codex", "subscription")
    original = copy.deepcopy(profile)
    monkeypatch.setattr(child, "load_profile", lambda: profile)
    hashed = []

    def checked_digest(raw):
        hashed.append(raw)
        return digest(raw)

    monkeypatch.setattr(child, "digest", checked_digest)
    first = credential("codex", "subscription")
    auth = json.loads(first.value)
    auth["tokens"]["refresh_token"] = "different-synthetic-refresh-token"
    second = child.ProviderCredential("codex", "subscription", json.dumps(auth), first.expires_at)
    captures = [child.run_child(claim(), provider_credential=value) for value in (first, second)]
    assert all(item.returncode == 0 for item in captures)
    assert captures[0].argv_sha256 == captures[1].argv_sha256
    for value in (first, second):
        for secret in child._validate_credential(value, "codex", "subscription"):
            assert all(secret not in raw for raw in hashed)
    assert profile == original


def test_invalid_parent_payload_closes_file(tmp_path, monkeypatch, plan_profile):
    selected = tmp_path / "selected"
    selected.write_bytes(b'{"credential":"synthetic-secret","credential":"duplicate"}')
    selected.chmod(0o600)
    monkeypatch.setattr(child, "load_profile", lambda: plan_profile)
    monkeypatch.setattr(service, "provider_credential_path", lambda _: selected)
    before = set(os.listdir("/proc/self/fd"))
    with pytest.raises(OperationRefused):
        service._provider_credential("codex")
    assert set(os.listdir("/proc/self/fd")) == before


@pytest.mark.parametrize("header", ["not-json", "e30", "eyJhbGciOiJub25lIn0"])
def test_malformed_or_unsigned_jwt_header_is_refused(header):
    value = payload("codex", "subscription")
    auth = json.loads(value["auth_json"])
    parts = auth["tokens"]["access_token"].split(".")
    parts[0] = header
    auth["tokens"]["access_token"] = ".".join(parts)
    value["auth_json"] = json.dumps(auth)
    with pytest.raises(OperationRefused):
        child.parse_provider_credential(json.dumps(value).encode(), harness="codex", mode="subscription")


def test_cached_id_token_can_expire_while_native_access_token_is_fresh():
    value = payload("codex", "subscription")
    auth = json.loads(value["auth_json"])
    auth["tokens"]["id_token"] = jwt(int(time.time()) - 3600)
    value["auth_json"] = json.dumps(auth)
    selected = child.parse_provider_credential(json.dumps(value).encode(), harness="codex", mode="subscription")
    assert json.loads(selected.value)["tokens"] == auth["tokens"]

    auth["tokens"]["access_token"] = jwt(int(time.time()) - 1)
    value["auth_json"] = json.dumps(auth)
    with pytest.raises(OperationRefused, match="provider_credential_auth_json"):
        child.parse_provider_credential(json.dumps(value).encode(), harness="codex", mode="subscription")
