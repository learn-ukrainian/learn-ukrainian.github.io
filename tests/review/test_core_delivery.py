"""Rules are a trusted render dependency, separate from learner inputs and templates."""

import hashlib
import json
import os
import subprocess
import sys
from unittest.mock import Mock

import pytest
from lu_machinery.dispatcher import review_attempt, store
from lu_machinery.dispatcher.types import TaskSpec
from lu_machinery.lib import rules_core
from lu_machinery.review import render_contract

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
    assert dependency["sources"] == [{"path": "agents_extensions/shared/rules/core.md",
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


def test_bound_core_provenance_admits_identical_bytes_across_machinery_checkouts(tmp_path):
    """Defect class: a committed bound render refuses identical machinery at another checkout path."""
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, timeout=30).strip()
    checkouts = [tmp_path / "machinery-a", tmp_path / "machinery-b"]
    for checkout in checkouts:
        subprocess.run(["git", "clone", "--shared", "--no-checkout", "--quiet", str(REPO_ROOT), str(checkout)],
                       check=True, capture_output=True, timeout=60)
        subprocess.run(["git", "sparse-checkout", "set", "--no-cone", "/scripts/",
                        "/agents_extensions/shared/rules/", "/schemas/", "/.mcp/", "/requirements-lock.txt"],
                       cwd=checkout, check=True, capture_output=True, timeout=60)
        subprocess.run(["git", "checkout", "--quiet", "--detach", head], cwd=checkout,
                       check=True, capture_output=True, timeout=60)
        assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout,
                                       text=True, timeout=30).strip() == head
        assert subprocess.check_output(["git", "status", "--porcelain"], cwd=checkout,
                                       text=True, timeout=30) == ""
    learner = tmp_path / "learner"
    learner.mkdir()
    manifest, _, _ = _setup_lexical_fixture(learner)
    output = tmp_path / "review.prompt"
    environment = dict(os.environ)
    for name in ("PYTHONPATH", "LEARN_UKRAINIAN_RULES_DIR"):
        environment.pop(name, None)
    rendered = subprocess.run(
        [sys.executable, "-m", "scripts.review.prompts.render", str(manifest), "--repo-root", str(learner),
         "--output", str(output), "--review-id", "review", "--attempt-id", "attempt", "--review-access", "isolated"],
        cwd=checkouts[0], env=environment, capture_output=True, text=True, timeout=60,
    )
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    admission = """
import json, sys
from pathlib import Path
from scripts.review.render_contract import (
    ReviewContractError, check_launch_contract, check_render_contract, trusted_core_context,
)
prompt = Path(sys.argv[1])
try:
    contract = check_render_contract(prompt, prompt.read_text(), Path.cwd(), interpreter=Path(sys.executable),
                                     review_id="review", attempt_id="attempt")
    check_launch_contract(contract, Path.cwd(), Path(sys.executable))
    result = {"admission": "pass", "recorded_dependency": contract["machinery_dependencies"]["rules_core"]}
except ReviewContractError as error:
    result = {"admission": "refused", "error": str(error)}
result["current_dependency"] = trusted_core_context()[1]
print(json.dumps(result))
"""
    outcomes = []
    for checkout in checkouts:
        admitted = subprocess.run([sys.executable, "-c", admission, str(output)], cwd=checkout,
                                  env=environment, capture_output=True, text=True, timeout=60)
        assert admitted.returncode == 0, admitted.stdout + admitted.stderr
        outcomes.append(json.loads(admitted.stdout))
    assert [outcome["admission"] for outcome in outcomes] == ["pass", "pass"], outcomes
    dependency = outcomes[0]["recorded_dependency"]
    assert dependency["seat"] == "core"
    assert dependency["sources"] == [{"path": "agents_extensions/shared/rules/core.md",
                                      "sha256": hashlib.sha256((checkouts[0] / rules_core.CORE_REL).read_bytes()).hexdigest()}]
    assert all(outcome["current_dependency"] == outcome["recorded_dependency"] == dependency for outcome in outcomes)


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
    from lu_machinery.agent_runtime import review_mcp, runner

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
