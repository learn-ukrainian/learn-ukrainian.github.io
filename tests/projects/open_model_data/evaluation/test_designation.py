from pathlib import Path

import pytest
import yaml

from scripts.projects.open_model_data.evaluation import custody


@pytest.mark.parametrize(
    "case,code",
    [
        ("task", "not_dispatched"),
        ("nonce", "not_dispatched"),
        ("family", "not_steward_family"),
        ("override", "tasks_dir_override"),
        ("missing", "record_unavailable"),
        ("archive", "record_unavailable"),
        ("malformed", "record_unavailable"),
        ("not-dict", "record_unavailable"),
        ("record-task", "run_mismatch"),
        ("record-nonce", "run_mismatch"),
        ("done", "not_running"),
        ("popen", "unbound_launch"),
        ("unit", "unbound_launch"),
        ("cgroup", "cgroup_mismatch"),
        ("cgroup-prefix", "cgroup_mismatch"),
        ("cgroup-traversal", "cgroup_mismatch"),
        ("cgroup-missing", "cgroup_unavailable"),
        ("cgroup-unreadable", "cgroup_unavailable"),
        ("model", "model_not_admitted"),
        ("catalog", "model_not_admitted"),
    ],
)
def test_every_designation_refusal(dispatched, monkeypatch, case, code):
    if case in {"task", "nonce"}:
        monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID" if case == "task" else "LU_RUNTIME_RUN_NONCE")
    elif case == "family":
        monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "ordinary-reader")
    elif case == "override":
        monkeypatch.setenv("LU_TASKS_DIR", "")
    elif case == "missing":
        dispatched.path.unlink()
    elif case == "archive":
        (dispatched.root / "archive").mkdir()
        dispatched.path.rename(dispatched.root / "archive" / dispatched.path.name)
    elif case == "malformed":
        dispatched.path.write_text("{")
    elif case == "not-dict":
        dispatched.path.write_text("[]")
    elif case.startswith("record-"):
        dispatched.record["task_id" if case == "record-task" else "run_nonce"] = "wrong"
        dispatched.save()
    elif case in {"done", "popen", "unit", "model"}:
        field = {"done": "status", "popen": "launch_mode", "unit": "launch_unit", "model": "model"}[case]
        dispatched.record[field] = {
            "done": "done",
            "popen": "popen",
            "unit": "lu-unrelated",
            "model": "unadmitted-model",
        }[case]
        dispatched.save()
    elif case.startswith("cgroup"):
        real_read = Path.read_text
        value = {
            "cgroup": "0::/SYNTHETIC-wrong\n",
            "cgroup-prefix": "0::" + dispatched.cgroup + "-other\n",
            "cgroup-traversal": "0::" + dispatched.cgroup + "/../other\n",
            "cgroup-missing": "1:cpu:/SYNTHETIC\n",
        }.get(case)

        def read(path, *a, **kw):
            if str(path) != "/proc/self/cgroup":
                return real_read(path, *a, **kw)
            if value is None:
                raise PermissionError("SYNTHETIC private diagnostic")
            return value

        monkeypatch.setattr(Path, "read_text", read)
    else:
        monkeypatch.setattr(custody, "load_model_catalog", lambda: (_ for _ in ()).throw(ValueError("SYNTHETIC")))
    with pytest.raises(custody.CustodyRefused, match=f"^{code}$"):
        custody.resolve_designation()


def test_valid_scope_and_parameterless_resolver(dispatched, monkeypatch):
    d = custody.resolve_designation()
    assert d.task_id == dispatched.record["task_id"]
    assert d.record_sha256 == custody.digest(dispatched.path.read_bytes())
    with pytest.raises(TypeError):
        custody.resolve_designation(d)
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: "0::" + dispatched.cgroup + "/SYNTHETIC-child\n")
    assert custody.resolve_designation().task_id == d.task_id


def test_recheck_permits_metadata_drift_but_rejects_identity_drift(dispatched, monkeypatch):
    designation = custody.resolve_designation()
    dispatched.record["progress"] = "SYNTHETIC"
    dispatched.save()
    custody.recheck(designation)
    assert custody.resolve_designation().record_sha256 != designation.record_sha256
    replacement = custody.StewardDesignation(
        designation.task_id, "wrong", designation.model, designation.launch_unit, designation.record_sha256
    )
    with pytest.raises(custody.CustodyRefused, match="designation_stale"):
        custody.recheck(replacement)
    dispatched.record["status"] = "done"
    dispatched.save()
    with pytest.raises(custody.CustodyRefused, match="not_running"):
        custody.recheck(designation)


def test_record_read_error_is_closed(dispatched, monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: (_ for _ in ()).throw(PermissionError("SYNTHETIC private")))
    with pytest.raises(custody.CustodyRefused, match="record_unavailable"):
        custody.resolve_designation()


@pytest.mark.parametrize("lifecycle", ["active", "hold", "retired", "removed"])
@pytest.mark.parametrize("purpose", ["custody_verify", "final_evaluation"])
def test_old_issuer_has_no_current_reader_or_writer_role(sealed, monkeypatch, lifecycle, purpose):
    data = yaml.safe_load(sealed.history.catalog_path.read_bytes())
    data["seats"]["openai_frontier"]["model_id"] = "SYNTHETIC-model-b"
    if lifecycle == "removed":
        del data["models"]["SYNTHETIC-model-a"]
    else:
        data["models"]["SYNTHETIC-model-a"]["lifecycle"] = lifecycle
        if lifecycle == "retired":
            data["models"]["SYNTHETIC-model-a"]["transports"] = []
            data["models"]["SYNTHETIC-model-a"].pop("routing_wire_ids")
    sealed.history.catalog(data)
    original = custody.OutputGuard.read

    def spy(out, name):
        assert not name.endswith(".sealed")
        return original(out, name)

    monkeypatch.setattr(custody.OutputGuard, "read", spy)
    with pytest.raises(custody.CustodyRefused, match=r"^model_not_admitted$"):
        custody.read_sealed(sealed.ref, purpose, custody_root=sealed.root)
    with pytest.raises(custody.CustodyRefused, match=r"^model_not_admitted$"):
        custody.seal(custody.ArtifactRef("C2", "final", "synthetic-v1"), b"SYNTHETIC", custody_root=sealed.root)
    assert not (sealed.root / custody._artifact_name(custody.ArtifactRef("C2", "final", "synthetic-v1"))).exists()
