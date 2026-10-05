"""File-readiness budgets and complete-line handshakes under delayed startup."""

from tests import wait_helpers


def test_default_readiness_budget_allows_startup_after_five_seconds(tmp_path, monkeypatch):
    path = tmp_path / "pid"
    elapsed = [0.0]
    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])

    def advance(_interval):
        elapsed[0] += 3.0
        # Opening the file alone does not publish a complete PID line.
        path.write_text("123" if elapsed[0] < 6 else "12345\n")

    monkeypatch.setattr(wait_helpers.time, "sleep", advance)
    assert wait_helpers.wait_for_pid_line(path) == 12345
    assert elapsed[0] == 6.0


def test_ready_line_returns_without_sleep(tmp_path, monkeypatch):
    path = tmp_path / "ready"
    path.write_text("ready\n")

    def unexpected_sleep(_interval):
        raise AssertionError("already published readiness must return immediately")

    monkeypatch.setattr(wait_helpers.time, "sleep", unexpected_sleep)
    assert wait_helpers.wait_for_line(path) == "ready"
