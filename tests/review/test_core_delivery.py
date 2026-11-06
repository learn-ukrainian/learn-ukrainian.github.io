"""Rules are a trusted render dependency, separate from learner inputs and templates."""

import hashlib
import json
from unittest.mock import Mock

import pytest

from scripts.dispatcher import review_attempt, store
from scripts.dispatcher.types import TaskSpec
from scripts.lib import rules_core
from scripts.review import render_contract
from scripts.review.prompts.check import check_prompt
from scripts.review.prompts.render import REPO_ROOT, render, render_prompt
from tests.review.test_prompts import _setup_lexical_fixture


def rendered_at(tmp_path, monkeypatch, access="isolated"):
    source = tmp_path / "machinery-rules" / "core.md"
    source.parent.mkdir()
    source.write_text("Trusted machinery rules. Writer prompt is forbidden in learner inputs.\n")
    monkeypatch.setenv("LEARN_UKRAINIAN_RULES_DIR", str(source.parent))
    manifest, _, _ = _setup_lexical_fixture(tmp_path)
    output = tmp_path / "review.prompt"
    text, sha, reads = render_prompt(manifest, repo_root=tmp_path, output_path=output,
                                    review_id="review", attempt_id="attempt", review_access=access)
    return source, manifest, output, text, sha, reads


@pytest.mark.parametrize("access", ("isolated", "full"))
def test_core_provenance_is_hashed_machinery_and_not_a_learner_pin(tmp_path, monkeypatch, access):
    """Defect class: trusted machinery becomes unpinned learner data or escapes the prompt hash."""
    source, manifest, output, text, sha, reads = rendered_at(tmp_path, monkeypatch, access)
    contract = render_contract.check_render_contract(output, text, REPO_ROOT, review_id="review", attempt_id="attempt")
    dependency = contract["machinery_dependencies"]["rules_core"]
    assert dependency["seat"] == "core"
    assert dependency["sources"] == [{"path": str(source.resolve()),
                                       "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]
    assert dependency["block_sha256"] == hashlib.sha256(rules_core.core_block().encode()).hexdigest()
    assert source not in reads
    assert sha == hashlib.sha256(text.encode()).hexdigest()
    assert json.dumps(dependency, sort_keys=True, separators=(",", ":")) in text
    rendering = render(manifest, repo_root=tmp_path, review_id="review", attempt_id="attempt", review_access=access)
    assert source.read_text().strip() not in rendering.template_text
    checked = check_prompt(text, manifest, repo_root=tmp_path, files_read=reads, review_access=access,
                           machinery_dependencies=contract["machinery_dependencies"])
    assert checked.passed, checked.errors


@pytest.mark.parametrize("field", ("seat", "path", "sha256", "block_sha256", "missing"))
def test_admission_refuses_tampered_core_provenance(tmp_path, monkeypatch, field):
    """Defect class: forged trusted-core provenance admits an otherwise exact rendered prompt."""
    _, _, output, text, _, _ = rendered_at(tmp_path, monkeypatch)
    sidecar = render_contract.render_record_path(output)
    saved = json.loads(sidecar.read_text())
    dependency = saved["render_contract"]["machinery_dependencies"]["rules_core"]
    if field == "missing":
        saved["render_contract"].pop("machinery_dependencies")
    elif field in {"path", "sha256"}:
        dependency["sources"][0][field] = "forged"
    else:
        dependency[field] = "forged"
    sidecar.write_text(json.dumps(saved))
    with pytest.raises(render_contract.ReviewContractError, match="review_rules_core_"):
        render_contract.check_render_contract(output, text, REPO_ROOT)


@pytest.mark.parametrize("change", ("changed", "missing", "prompt", "provenance"))
def test_launch_refuses_core_drift_before_attempt_claim_or_provisioning(tmp_path, monkeypatch, change):
    """Defect class: stale, missing or altered rules spend an attempt before launch refusal."""
    from scripts.agent_runtime import review_mcp, runner

    source, manifest, output, text, _, _ = rendered_at(tmp_path, monkeypatch)
    contract = render_contract.check_render_contract(output, text, REPO_ROOT)
    spec = TaskSpec("core-attempt", "codex", "stub", "high", "read-only", tmp_path, output, tmp_path / "result")
    record = {"task_id": spec.task_id, "review_attempt": {"review_id": "review", "attempt_id": "attempt"},
              "review_access": "isolated", "options": {"review_attempt": str(manifest)},
              "worktree_path": str(tmp_path), "review_contract": contract}
    if change == "changed":
        source.write_text("Changed trusted rules\n")
    elif change == "missing":
        source.rename(source.with_suffix(".unavailable"))
    elif change == "prompt":
        text += "Added after validation"
    else:
        contract["machinery_dependencies"]["rules_core"]["seat"] = "forged"
    claim, prepare, invoke = Mock(), Mock(), Mock()
    monkeypatch.setattr(store, "check_review_attempt", claim)
    monkeypatch.setattr(review_mcp, "prepare_review_attempt", prepare)
    monkeypatch.setattr(runner, "invoke", invoke)
    result = review_attempt.run(spec, record, text, (60, 30, 30))
    assert result.status == "failed" and result.error.startswith("review_attempt_refused:")
    claim.assert_not_called()
    prepare.assert_not_called()
    invoke.assert_not_called()
    assert not spec.final_file.exists()
    if change in {"changed", "missing"}:
        with pytest.raises(render_contract.ReviewContractError, match="review_rules_core_"):
            render_contract.check_render_contract(output, text, REPO_ROOT)


def test_missing_core_render_writes_no_artifacts(tmp_path, monkeypatch):
    """Defect class: missing machinery rules leave a partial rendered prompt or sidecars."""
    from scripts.review.prompts.render import RenderError

    manifest, _, _ = _setup_lexical_fixture(tmp_path)
    monkeypatch.setenv("LEARN_UKRAINIAN_RULES_DIR", str(tmp_path / "absent"))
    output = tmp_path / "not-created" / "prompt"
    with pytest.raises(RenderError, match="review_rules_core_unavailable"):
        render_prompt(manifest, repo_root=tmp_path, output_path=output)
    assert not output.parent.exists()


@pytest.mark.parametrize("record", (None, [], "invalid", 42))
def test_checker_cli_refuses_malformed_machinery_record(tmp_path, monkeypatch, record, capsys):
    """Defect class: malformed machinery sidecars crash the checker instead of refusing admission."""
    from scripts.review.prompts.check import main

    _, manifest, output, _, _, _ = rendered_at(tmp_path, monkeypatch)
    sidecar = render_contract.render_record_path(output)
    saved = json.loads(sidecar.read_text())
    saved["render_contract"] = record
    sidecar.write_text(json.dumps(saved))
    assert main([str(output), "--manifest", str(manifest), "--repo-root", str(tmp_path),
                 "--review-access", "isolated"]) == 1
    assert "FAIL:" in capsys.readouterr().out
