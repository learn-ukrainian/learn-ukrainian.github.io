"""Native Codex launcher behavior after the driver split."""

import pytest

from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


def test_codex_interactive_rejects_epic() -> None:
    result = run_launcher("start-codex.sh", "--epic", "devops")
    assert result.returncode == 2


def test_codex_native_harness_is_default_and_forwards_arguments_after_separator() -> None:
    result = run_launcher("start-codex.sh", "--", "--ask-for-approval", "never")
    assert result.returncode == 0, result.stderr
    assert "would exec codex" in result.stdout
    assert "--ask-for-approval never" in result.stdout
