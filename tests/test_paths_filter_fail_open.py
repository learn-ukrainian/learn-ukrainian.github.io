"""Tests to verify that paths-filter-retry fail-open logic is complete and aligned with workflows."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ACTION_FILE = _REPO_ROOT / ".github" / "actions" / "paths-filter-retry" / "action.yml"
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_CONTENT_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "content-ci.yml"


def test_action_metadata_exists_and_parses() -> None:
    assert _ACTION_FILE.is_file(), f"Missing action file: {_ACTION_FILE}"
    action_data = yaml.safe_load(_ACTION_FILE.read_text(encoding="utf-8"))
    assert isinstance(action_data, dict), "action.yml is not a valid YAML mapping"
    assert action_data.get("name") == "Paths Filter with Retry"


def test_action_outputs_match_set_outputs_step() -> None:
    action_data = yaml.safe_load(_ACTION_FILE.read_text(encoding="utf-8"))
    outputs = action_data.get("outputs", {})
    assert outputs, "No outputs declared in action.yml"

    # Every declared output must map to steps.set-outputs.outputs.<name>
    for name, definition in outputs.items():
        val = definition.get("value", "")
        expected = f"${{{{ steps.set-outputs.outputs.{name} }}}}"
        assert val == expected, f"Output '{name}' has value '{val}', expected '{expected}'"


def test_fail_open_sets_all_declared_outputs_to_true() -> None:
    action_data = yaml.safe_load(_ACTION_FILE.read_text(encoding="utf-8"))
    outputs = set(action_data.get("outputs", {}).keys())

    # Find the set-outputs step run script
    steps = action_data.get("runs", {}).get("steps", [])
    set_outputs_step = next((s for s in steps if s.get("id") == "set-outputs"), None)
    assert set_outputs_step is not None, "Missing 'set-outputs' step in action.yml"

    run_script = set_outputs_step.get("run", "")
    assert run_script, "set-outputs step is missing the 'run' script"

    # Extract the fallback block (after the else)
    # The script structure is:
    # if [ ... ]; then
    #   ...
    # elif [ ... ]; then
    #   ...
    # else
    #   echo "::warning::path classification unavailable — running everything"
    #   echo "key=true" >> "$GITHUB_OUTPUT"
    #   ...
    # fi
    else_match = re.search(r"else\s+(.*?)\s+fi", run_script, re.DOTALL)
    assert else_match, "Could not find 'else' fallback block in set-outputs script"
    fallback_content = else_match.group(1)

    # Verify a loud warning annotation is emitted
    assert "::warning::path classification unavailable" in fallback_content, (
        "Fallback block must emit warning annotation"
    )

    # Fail-open must set every declared output to true. Accept either per-key
    # `echo "key=true"` lines or a single `emit true ...` call with one true per output
    # (env-indirection hardening for zizmor/template-injection).
    ordered = list(action_data.get("outputs", {}).keys())
    per_key_ok = all(
        re.search(rf'echo "{output}=true"\s+>>\s+"?\$GITHUB_OUTPUT"?', fallback_content)
        for output in outputs
    )
    emit_trues = re.search(
        r"emit\s+" + r"\s+".join(["true"] * len(ordered)),
        fallback_content,
    )
    assert per_key_ok or emit_trues, (
        "Fallback block must set every declared output to true "
        f"(outputs={sorted(outputs)})"
    )


def test_workflows_only_consume_valid_action_outputs() -> None:
    action_data = yaml.safe_load(_ACTION_FILE.read_text(encoding="utf-8"))
    action_outputs = set(action_data.get("outputs", {}).keys())

    for wf_path in (_CI_WORKFLOW, _CONTENT_CI_WORKFLOW):
        assert wf_path.is_file(), f"Missing workflow file: {wf_path}"
        wf_data = yaml.safe_load(wf_path.read_text(encoding="utf-8"))

        # Find the 'changes' job
        changes_job = wf_data.get("jobs", {}).get("changes", {})
        assert changes_job, f"Missing 'changes' job in {wf_path.name}"

        # Find the output mappings of the 'changes' job
        outputs = changes_job.get("outputs", {})
        assert outputs, f"No outputs declared in changes job of {wf_path.name}"

        for out_name, out_val in outputs.items():
            # The value should look like: ${{ steps.filter.outputs.<key> }}
            match = re.match(r"\$\{\{\s*steps\.filter\.outputs\.(\w+)\s*\}\}", out_val)
            assert match, (
                f"Job output '{out_name}' value '{out_val}' in {wf_path.name} "
                f"does not match steps.filter.outputs.<key> syntax"
            )
            step_output_key = match.group(1)
            assert step_output_key in action_outputs, (
                f"Workflow {wf_path.name} references step output '{step_output_key}' "
                f"which is not declared in action.yml"
            )
