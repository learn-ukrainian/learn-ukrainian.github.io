"""Regression checks for the census's path labels and commit counting."""

import pytest

from scripts.evidence import agent_pitfall_census as census


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
def test_path_buckets_keep_unicode_separators_inside_subjects(monkeypatch, separator):
    # #9556: the subject header ends at LF; its tail is not a changed path.
    raw = f"\x1efirst\x1ffix(tests): a{separator}tests/fake.py\ndocs/example.md\n"
    monkeypatch.setattr(census, "_git", lambda *args: raw)

    assert census._path_buckets(census.PRIMARY_SINCE, census.PRIMARY_UNTIL) == {"no_listed_bucket": 1}
