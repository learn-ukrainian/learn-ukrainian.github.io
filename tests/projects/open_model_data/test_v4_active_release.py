"""Reviewed public prerequisite only: no private key, provider or actual unit."""

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from learn_ukrainian_v4_runtime import child_runtime as child
from learn_ukrainian_v4_runtime import readiness, resources, stage_policy
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, digest
from test_v4_installed_release import REPO_ROOT

pytest_plugins = ("test_v4_installed_release",)

POLICY_RAW_SHA256 = "847f14c4ef30ed1755612eef0614bcf606de2967b1ae6ac5c0ede2ade2b4ce72"
PROFILE_RAW_SHA256 = "3f5e9ccf4d97860dbf5bcbca54f6fee7796873d8aed59060a4bea0860813b25f"


def test_active_policy_is_exact_public_release_and_old_policy_is_inactive(monkeypatch):
    policy, active = trust.load_production_trust_policy()
    assert digest(trust.DEFAULT_TRUST_POLICY_PATH.read_bytes()) == POLICY_RAW_SHA256
    assert {POLICY_RAW_SHA256} == trust.PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST
    assert active == trust.trust_policy_sha256(policy)
    assert set(policy) == {"keyrings", "schema_version"}
    for role in trust.KEYRING_ROLES:
        ring = policy["keyrings"][role]
        assert list(ring) == ["v4-first-row-20260905-" + role]
        assert set(next(iter(ring.values()))) == {"public_key_hex", "revoked"}
    historical = resources.resource_root() / "data/projects/open_model_data/trust/v4_trust_policy_v1.json"
    assert digest(historical.read_bytes()) == "81ce6f7bfb68ed1c51f8633cb1ec0bc19eecc9c47b5bdaff9a20a9a9ea6d64ba"
    assert json.loads(historical.read_bytes()) == trust.empty_trust_policy()
    monkeypatch.setattr(trust, "DEFAULT_TRUST_POLICY_PATH", historical)
    with pytest.raises(trust.TrustAuthorityError, match="active allowlist"):
        trust.load_production_trust_policy()


@pytest.mark.parametrize("replacement", [b" ", b"{}", b"null"])
def test_profile_loader_refuses_unreviewed_bytes(tmp_path, monkeypatch, replacement):
    path = tmp_path / "profile.json"
    raw = child.profile_path().read_bytes()
    path.write_bytes(raw + replacement if replacement == b" " else replacement)
    monkeypatch.setattr(child, "profile_path", lambda: path)
    with pytest.raises(OperationRefused, match="runtime_profile_digest"):
        child.load_profile()


def test_fixed_native_profile_scope():
    profile = child.load_profile()
    assert digest(child.profile_path().read_bytes()) == PROFILE_RAW_SHA256
    assert child.PRODUCTION_CHILD_PROFILE_SHA256 == PROFILE_RAW_SHA256
    assert not inspect.signature(child.load_profile).parameters
    assert not inspect.signature(trust.load_production_trust_policy).parameters
    assert profile["sources_url"] == "http://localhost:8766/mcp"
    assert profile["bwrap"] == "/usr/bin/bwrap"
    assert set(profile["adapters"]) == {"claude", "codex"}
    for harness, model in [("codex", "gpt-6-astra"), ("claude", "claude-fable-5-1")]:
        adapter = profile["adapters"][harness]
        assert adapter["models"] == [model]
        assert child.credential_mode(profile, harness) == "subscription"
        assert adapter["executable"] == "/runtime/" + harness
        entries = {entry["destination"]: entry for entry in adapter["files"]}
        assert len(entries) == len(adapter["files"])
        assert entries[adapter["executable"]]["source"] == "/opt/hramatka/current/v4-native/" + harness
        assert {key for key in entries if key.startswith("/etc/")} == {
            "/etc/resolv.conf", "/etc/ssl/certs/ca-certificates.crt",
        }
        assert all(set(entry) == {"source", "destination", "sha256"} for entry in entries.values())


def test_active_policy_never_creates_completion_or_enables_switches(monkeypatch):
    _, active = trust.load_production_trust_policy()
    old = trust.trust_policy_sha256(trust.empty_trust_policy())
    assert stage_policy.validate_stage_policy({"a7_completions": []}) == active
    assert stage_policy.validate_stage_policy({"trust_policy_sha256": active, "a7_completions": [
        {"trust_policy_sha256": active},
    ]}) == active
    with pytest.raises(ValueError, match="not active"):
        stage_policy.validate_completion_policy([{"trust_policy_sha256": old}])
    for switch in (readiness.EXECUTION_SWITCH, readiness.ADMISSION_SWITCH):
        monkeypatch.delenv(switch, raising=False)
    with pytest.raises(OperationRefused, match="execution_disabled"):
        readiness.require_execution_enabled()
    with pytest.raises(OperationRefused, match="admission_disabled"):
        readiness.require_admission_enabled()


def test_reviewed_profile_without_actual_qualification_refuses(tmp_path, monkeypatch):
    # Real package/profile/policy verification, with a local bwrap metadata
    # surrogate so CI need not run the production bwrap build. This never
    # qualifies the production binary or reads production credentials.
    profile = child.load_profile()

    def local_bwrap(path, expected):
        assert (path, expected) == (profile["bwrap"], profile["bwrap_sha256"])
        return child._verified_file(path, digest(Path(path).read_bytes()))

    monkeypatch.setattr(readiness, "_verified_file", local_bwrap)
    monkeypatch.setattr(readiness, "qualification_path", lambda: tmp_path / "absent-qualification.json")
    with pytest.raises(OperationRefused, match="readiness_unproved") as error:
        readiness.require_readiness()
    assert isinstance(error.value.__cause__, FileNotFoundError)


ACTIVE_PROBE = r'''
import hashlib, importlib.util, json, sys
from pathlib import Path
installed, dependencies, checkout = map(Path, sys.argv[1:])
sys.path[:] = [str(dependencies), str(installed), *[
    p for p in sys.path if p and not Path(p).resolve().is_relative_to(checkout.resolve())
]]
assert importlib.util.find_spec("scripts") is None
def audit(event, args):
    if event == "subprocess.Popen": raise AssertionError("no runtime subprocess")
    if event == "open" and isinstance(args[0], str):
        p = Path(args[0])
        assert not p.is_absolute() or not p.is_relative_to(checkout), "checkout read"
        assert not str(p).startswith(("/run/credentials/", "/etc/hramatka/")), "credential read"
sys.addaudithook(audit)
from learn_ukrainian_v4_runtime import child_runtime, v4_trust_authority, provenance
identity = provenance.verify_current_identity()
policy, policy_digest = v4_trust_authority.load_production_trust_policy()
profile = child_runtime.load_profile()
assert all(len(ring) == 1 for ring in policy["keyrings"].values())
assert set(profile["adapters"]) == {"codex", "claude"}
for path in (child_runtime.profile_path(), v4_trust_authority.DEFAULT_TRUST_POLICY_PATH):
    assert identity["installed_files"][str(path)] == hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps({"public_commit": identity["public_commit"], "active_policy": policy_digest,
                  "profile": hashlib.sha256(child_runtime.profile_path().read_bytes()).hexdigest()}))
'''


def test_exact_wheel_active_resources_outside_checkout(isolated_install, external_dependencies, tmp_path):
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["PATH"] = ""
    result = subprocess.run(
        [sys.executable, "-I", "-c", ACTIVE_PROBE, str(isolated_install), str(external_dependencies), str(REPO_ROOT)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    proof = json.loads(result.stdout)
    assert proof["profile"] == PROFILE_RAW_SHA256
    assert proof["public_commit"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    print(result.stdout.strip())
