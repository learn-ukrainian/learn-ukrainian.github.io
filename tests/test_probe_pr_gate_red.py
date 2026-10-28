"""Throwaway probe: this test fails on purpose to show the PR gate goes red."""


def test_probe_fails_on_purpose() -> None:
    assert 1 + 1 == 3, "deliberate failure to prove the PR CI Gate goes red"
