"""Current runtime policy tests, separate from frozen release evidence."""

import pytest


def test_codex_baseline_rejects_old_model_before_process(tmp_path, monkeypatch):
    from scripts.projects.ua_eval_harness import run_codex_baseline
    def forbidden(*args, **kwargs):
        pytest.fail("unapproved model reached subprocess")
    monkeypatch.setattr(run_codex_baseline.subprocess, "run", forbidden)
    with pytest.raises(run_codex_baseline.RunnerError, match="only gpt-6-astra"):
        run_codex_baseline._run_batch([], prompt_text="test", model="gpt-5.6-terra", codex_bin="codex",
            schema_path=tmp_path / "schema.json", timeout=1)
