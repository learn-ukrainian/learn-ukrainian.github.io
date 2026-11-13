"""Coverage for scripts/ci/machinery_twin_gate.py, the TWIN-FREEZE-1113 landing rule.

Only the GitHub REST reads are replaced, by payloads shaped like ``GET /repos/{repo}/pulls/{n}``.
"""

from __future__ import annotations

import pytest

from scripts.ci import machinery_twin_gate as gate

MACHINERY = "scripts/dispatcher/checks.py"
RESIDUAL = "scripts/dispatcher/providers/opencode.py"
ROWS = frozenset({MACHINERY, RESIDUAL, "scripts/publish/github.py"})
MERGED_SHA = "a" * 40
OLD_SHA = "b" * 40


def _pull(*, merged: bool, merge_sha: str | None, repository: str = gate.MACHINERY_REPOSITORY) -> dict:
    return {"base": {"ref": "main", "repo": {"full_name": repository}}, "merged": merged, "merge_commit_sha": merge_sha}


PULLS = {
    f"repos/{gate.MACHINERY_REPOSITORY}/pulls/400": _pull(merged=True, merge_sha=MERGED_SHA),
    f"repos/{gate.MACHINERY_REPOSITORY}/pulls/401": _pull(merged=False, merge_sha="c" * 40),
    f"repos/{gate.MACHINERY_REPOSITORY}/pulls/120": _pull(merged=True, merge_sha=OLD_SHA),
}


def _twin(number: int, sha: str, newline: str = "\n") -> str:
    return f"Summary.{newline}{newline}Machinery-Twin: {gate.MACHINERY_REPOSITORY}#{number} {sha}{newline}"


@pytest.mark.parametrize(
    ("changed", "body", "merged_paths", "blocked"),
    [
        pytest.param([MACHINERY], _twin(400, MERGED_SHA, "\r\n"), [MACHINERY], False, id="pass-landed-twin-crlf-body"),
        pytest.param(
            [MACHINERY],
            f"Twin: {gate.MACHINERY_REPOSITORY}#400 and https://github.com/{gate.MACHINERY_REPOSITORY}/pull/400",
            [MACHINERY],
            True,
            id="bare-reference",
        ),
        pytest.param([MACHINERY], _twin(401, "c" * 40), [MACHINERY], True, id="unmerged-twin"),
        pytest.param([MACHINERY], _twin(400, OLD_SHA), [MACHINERY], True, id="sha-not-the-merge-commit"),
        pytest.param([MACHINERY], _twin(120, OLD_SHA), [MACHINERY], False, id="exempt-deletion-cites-existing-pr"),
        pytest.param([MACHINERY], None, [RESIDUAL, "curriculum/a1.md"], False, id="expired-only-residual-left"),
    ],
)
def test_machinery_change_lands_only_with_a_merged_twin_until_expiry(changed, body, merged_paths, blocked):
    """Defect classes: a valid CRLF-terminated citation (web-edited body) read as missing; a bare or unmerged citation, or a SHA that is not the PR's merge commit, letting a
    product-only machinery edit land (fork); an approved cutover deletion forced to manufacture a new
    machinery change; the freeze outliving the in-tree copy."""
    result = gate.findings(changed, body, rows=ROWS, merged_paths=merged_paths, get=PULLS.__getitem__)
    assert bool(result) is blocked, result
