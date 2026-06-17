"""resource_liveness_fn must thread from run_python_qg_with_corrections down to
run_python_qg on BOTH the seminar (bounded) and legacy (single-shot) correction
paths, so --enhance's static python_qg can substitute resource-liveness for the
absent writer search telemetry (#3079). It must default to None at build time so
real builds never touch the network.
"""

from __future__ import annotations

from pathlib import Path

from scripts.build import linear_pipeline


def _module_dir(tmp_path: Path) -> Path:
    md = tmp_path / "module"
    md.mkdir()
    (md / "module.md").write_text("x\n", encoding="utf-8")
    (md / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (md / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (md / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return md


def _plan_path(tmp_path: Path, level: str) -> Path:
    p = tmp_path / f"{level}.yaml"
    p.write_text(f"level: {level}\nsequence: 1\nslug: sample\n", encoding="utf-8")
    return p


def _sentinel(url: str) -> bool:  # a distinct identity to assert pass-through
    return True


def _capture(monkeypatch) -> dict:
    """Stub run_python_qg to capture the forwarded kwarg and pass immediately."""
    seen: dict = {"called": False}

    def fake_run_python_qg(module_dir, plan_path, **kwargs):
        seen["called"] = True
        seen["resource_liveness_fn"] = kwargs.get("resource_liveness_fn")
        return {"gates": {"passed": True}}

    monkeypatch.setattr(linear_pipeline, "run_python_qg", fake_run_python_qg)
    monkeypatch.setattr(linear_pipeline, "_attach_vocab_count_gate", lambda *a, **k: None)
    return seen


def test_seminar_bounded_path_forwards_resource_liveness_fn(tmp_path, monkeypatch):
    seen = _capture(monkeypatch)
    linear_pipeline.run_python_qg_with_corrections(
        _module_dir(tmp_path),
        _plan_path(tmp_path, "folk"),  # folk -> SEMINAR_LEVELS -> bounded path
        resource_liveness_fn=_sentinel,
    )
    assert seen["called"] is True
    assert seen["resource_liveness_fn"] is _sentinel


def test_legacy_single_shot_path_forwards_resource_liveness_fn(tmp_path, monkeypatch):
    seen = _capture(monkeypatch)
    linear_pipeline.run_python_qg_with_corrections(
        _module_dir(tmp_path),
        _plan_path(tmp_path, "a1"),  # a1 -> non-seminar -> legacy path
        resource_liveness_fn=_sentinel,
    )
    assert seen["called"] is True
    assert seen["resource_liveness_fn"] is _sentinel


def test_default_resource_liveness_fn_is_none_for_builds(tmp_path, monkeypatch):
    seen = _capture(monkeypatch)
    linear_pipeline.run_python_qg_with_corrections(
        _module_dir(tmp_path),
        _plan_path(tmp_path, "folk"),
    )
    assert seen["called"] is True
    assert seen["resource_liveness_fn"] is None
