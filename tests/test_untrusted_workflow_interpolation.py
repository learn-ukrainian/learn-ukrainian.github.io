"""Fixture tests for the untrusted-context workflow interpolation gate.

``scripts/audit/check_untrusted_workflow_interpolation.py`` is the fail-closed
half of the workflow-path gate (advisor packet B+D): untrusted GitHub context
(issue/PR text, comment bodies, branch names) must not be ``${{ }}``-expanded
inside ``run:`` scripts, where it becomes shell injection. The safe pattern —
an ``env:`` mapping plus a quoted ``"$VAR"`` in the script — must keep passing,
as must SHA/ref expressions and the current repo workflows.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CHECKER = _REPO_ROOT / "scripts" / "audit" / "check_untrusted_workflow_interpolation.py"


def _run_checker(*files: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_CHECKER), *(str(f) for f in files)],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_workflow(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_issue_title_in_run_fails(tmp_path: Path) -> None:
    workflow = _write_workflow(
        tmp_path,
        """\
on: issues
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ github.event.issue.title }}"
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "github.event.issue" in result.stderr


def test_head_ref_in_multiline_run_fails(tmp_path: Path) -> None:
    workflow = _write_workflow(
        tmp_path,
        """\
on: pull_request
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout attacker-named branch
        run: |
          echo "branch is ${{ github.head_ref }}"
          git status
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "github.head_ref" in result.stderr
    assert ":8:" in result.stderr  # finding points at the injected line


def test_env_mapping_with_quoted_var_passes(tmp_path: Path) -> None:
    workflow = _write_workflow(
        tmp_path,
        """\
on: pull_request
jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - name: Echo title safely
        env:
          TITLE: ${{ github.event.pull_request.title }}
          BODY: ${{ github.event.pull_request.body }}
        run: |
          echo "$TITLE"
          echo "$BODY"
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 0, result.stdout + result.stderr


def test_sha_and_ref_interpolation_in_run_passes(tmp_path: Path) -> None:
    # SHAs/refs are not attacker-controlled text; validate-yaml.yml diffs with
    # exactly this pattern and must stay green.
    workflow = _write_workflow(
        tmp_path,
        """\
on: pull_request
jobs:
  diff:
    runs-on: ubuntu-latest
    steps:
      - run: |
          base_sha="${{ github.event.pull_request.base.sha }}"
          head_sha="${{ github.event.pull_request.head.sha }}"
          git diff "$base_sha" "$head_sha"
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 0, result.stdout + result.stderr


def test_untrusted_context_in_if_and_concurrency_passes(tmp_path: Path) -> None:
    # Only run: shell expansion is exploitable; if:/concurrency are not run:
    # interpolation.
    workflow = _write_workflow(
        tmp_path,
        """\
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.title || github.ref }}
on: pull_request
jobs:
  gate:
    if: github.event.pull_request.title != ''
    runs-on: ubuntu-latest
    steps:
      - run: echo hello
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 0, result.stdout + result.stderr


def test_env_mapping_after_dash_run_block_passes(tmp_path: Path) -> None:
    # Compact `- run: |` measures dash-indent, which is shallower than sibling
    # keys. env: after run: is valid YAML and must stay the allowed pattern.
    workflow = _write_workflow(
        tmp_path,
        """\
on: issues
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "$TITLE"
        env:
          TITLE: ${{ github.event.issue.title }}
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 0, result.stdout + result.stderr


def test_mixed_case_untrusted_context_in_run_fails(tmp_path: Path) -> None:
    workflow = _write_workflow(
        tmp_path,
        """\
on: issues
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ github.Event.Issue.Title }}"
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "github.event.issue" in result.stderr.casefold()


def test_bracket_notation_untrusted_context_in_run_fails(tmp_path: Path) -> None:
    workflow = _write_workflow(
        tmp_path,
        """\
on: issues
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ github.event['issue']['title'] }}"
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "github.event.issue" in result.stderr


def test_tojson_event_payload_in_run_fails(tmp_path: Path) -> None:
    workflow = _write_workflow(
        tmp_path,
        """\
on: issues
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - run: echo '${{ toJSON(github.event) }}'
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "tojson" in result.stderr.casefold()


def test_tojson_sha_in_run_passes(tmp_path: Path) -> None:
    workflow = _write_workflow(
        tmp_path,
        """\
on: pull_request
jobs:
  diff:
    runs-on: ubuntu-latest
    steps:
      - run: echo '${{ toJSON(github.sha) }}'
""",
    )
    result = _run_checker(workflow)
    assert result.returncode == 0, result.stdout + result.stderr


def test_current_repo_workflows_are_clean() -> None:
    result = subprocess.run(
        [sys.executable, str(_CHECKER)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
