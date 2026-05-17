from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit import audit_level


def test_missing_slug_exits_nonzero_and_names_slug(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    missing_slug = "__nonexistent__"
    run_audit_calls = []

    def fake_find_module_files(level: str, module_filter: str | None) -> tuple[list[Path], list[str]]:
        assert level == "a1"
        assert module_filter is None
        return [], [missing_slug]

    def fake_run_audit(files: list[Path], *args: object, **kwargs: object) -> tuple[int, int, list[str], dict[str, str]]:
        run_audit_calls.append(files)
        return 0, 0, [], {}

    monkeypatch.setattr(sys, "argv", ["audit_level.py", "a1"])
    monkeypatch.setattr(audit_level, "find_module_files", fake_find_module_files)
    monkeypatch.setattr(audit_level, "run_audit", fake_run_audit)

    with pytest.raises(SystemExit) as exc_info:
        audit_level.main()

    output = capsys.readouterr()
    assert exc_info.value.code != 0
    assert run_audit_calls == [[]]
    assert missing_slug in output.out or missing_slug in output.err


@pytest.mark.parametrize(
    ("audit_result", "expected_code"),
    [
        ((1, 0, [], {"existing-module": "pass"}), 0),
        ((0, 0, [], {}), 1),
    ],
)
def test_exit_zero_requires_at_least_one_successful_module_audit(
    monkeypatch: pytest.MonkeyPatch,
    audit_result: tuple[int, int, list[str], dict[str, str]],
    expected_code: int,
) -> None:
    module_file = Path("curriculum/l2-uk-en/a1/existing-module.md")

    monkeypatch.setattr(sys, "argv", ["audit_level.py", "a1"])
    monkeypatch.setattr(audit_level, "find_module_files", lambda _level, _module_filter: ([module_file], []))
    monkeypatch.setattr(audit_level, "run_audit", lambda *args, **kwargs: audit_result)
    monkeypatch.setattr(audit_level, "sync_batch_state", lambda _level, _slug_results: None)

    with pytest.raises(SystemExit) as exc_info:
        audit_level.main()

    assert exc_info.value.code == expected_code
