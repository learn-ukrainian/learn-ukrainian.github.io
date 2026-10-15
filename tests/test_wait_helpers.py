"""File-readiness budgets and complete-line handshakes under delayed startup."""

import pytest

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


def test_wait_until_returns_immediately_when_already_true(monkeypatch):
    def unexpected_sleep(_interval):
        raise AssertionError("a true condition must not sleep")

    monkeypatch.setattr(wait_helpers.time, "sleep", unexpected_sleep)
    wait_helpers.wait_until(lambda: True)


def test_wait_until_polls_until_the_condition_holds(monkeypatch):
    elapsed = [0.0]
    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(wait_helpers.time, "sleep", lambda interval: elapsed.__setitem__(0, elapsed[0] + interval))
    wait_helpers.wait_until(lambda: elapsed[0] >= 0.5, timeout=5.0, interval=0.25)
    assert elapsed[0] == 0.5


def test_wait_until_times_out_naming_the_condition(monkeypatch):
    elapsed = [0.0]
    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(wait_helpers.time, "sleep", lambda interval: elapsed.__setitem__(0, elapsed[0] + interval))
    with pytest.raises(AssertionError, match=r"ticket publication not met within 1\.0s"):
        wait_helpers.wait_until(lambda: False, timeout=1.0, interval=0.5, message="ticket publication")


def test_wait_until_never_sleeps_past_the_deadline(monkeypatch):
    elapsed = [0.0]
    sleeps: list[float] = []

    def sleep(interval):
        sleeps.append(interval)
        elapsed[0] += interval

    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(wait_helpers.time, "sleep", sleep)
    with pytest.raises(AssertionError, match=r"slow thing not met within 0\.1s"):
        wait_helpers.wait_until(lambda: False, timeout=0.1, interval=1.0, message="slow thing")
    assert sleeps == [pytest.approx(0.1)]
    assert elapsed[0] == pytest.approx(0.1)


def test_wait_until_fails_a_condition_that_is_only_true_after_the_deadline(monkeypatch):
    elapsed = [0.0]
    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(wait_helpers.time, "sleep", lambda interval: elapsed.__setitem__(0, elapsed[0] + interval))
    with pytest.raises(AssertionError, match=r"late condition not met within 0\.1s"):
        wait_helpers.wait_until(lambda: elapsed[0] > 0.1, timeout=0.1, interval=1.0, message="late condition")


def test_wait_until_fails_when_the_sleep_wakes_past_the_deadline(monkeypatch):
    elapsed = [0.0]
    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])
    # The OS wakes the sleeper 0.01 s late: 0.10 s requested, 0.11 s elapsed.
    monkeypatch.setattr(
        wait_helpers.time, "sleep", lambda interval: elapsed.__setitem__(0, elapsed[0] + interval + 0.01)
    )
    with pytest.raises(AssertionError, match=r"oversleep not met within 0\.1s"):
        wait_helpers.wait_until(lambda: elapsed[0] >= 0.11, timeout=0.1, interval=1.0, message="oversleep")


def test_wait_until_fails_when_the_predicate_itself_crosses_the_deadline(monkeypatch):
    elapsed = [0.0]
    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(wait_helpers.time, "sleep", lambda interval: elapsed.__setitem__(0, elapsed[0] + interval))

    def slow_predicate() -> bool:
        elapsed[0] = 0.2
        return True

    with pytest.raises(AssertionError, match=r"slow predicate not met within 0\.1s"):
        wait_helpers.wait_until(slow_predicate, timeout=0.1, interval=1.0, message="slow predicate")


def test_wait_until_accepts_a_condition_true_exactly_at_the_deadline(monkeypatch):
    elapsed = [0.0]
    monkeypatch.setattr(wait_helpers.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(wait_helpers.time, "sleep", lambda interval: elapsed.__setitem__(0, elapsed[0] + interval))
    wait_helpers.wait_until(lambda: elapsed[0] >= 0.5, timeout=0.5, interval=2.0)
    assert elapsed[0] == 0.5


def test_wait_until_propagates_a_predicate_assertion():
    def watched_process_exited() -> bool:
        raise AssertionError("watched process exited")

    with pytest.raises(AssertionError, match="watched process exited"):
        wait_helpers.wait_until(watched_process_exited)
