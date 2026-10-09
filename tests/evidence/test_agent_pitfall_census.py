"""Regression checks for the census's path labels and commit counting."""

import pytest

from scripts.evidence import agent_pitfall_census as census


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("site/tests/x.test.ts", "tests"),
        ("site/tests/atlas-practice.test.ts", "tests"),
        ("tests/test_x.py", "tests"),
        ("tests/hooks/test_guard.py", "tests"),
        ("site/src/components/atlas/WordCard.tsx", "site_atlas"),
        ("site/src/components/practice/Session.tsx", "site_practice"),
        ("site/src/pages/index.astro", "site_other"),
        ("scripts/review/record_cf_verdict.py", "delivery"),
        ("scripts/lexicon/export.py", "lexicon"),
        (".github/workflows/ci.yml", "ci_yml"),
        (".github/workflows/hygiene.yml", "workflows_other"),
        ("curriculum/example.yaml", "curriculum"),
        ("docs/example.md", None),
    ],
)
def test_path_bucket(path, expected):
    assert census._path_bucket(path) == expected


def test_path_buckets_count_each_commit_once_per_bucket(monkeypatch):
    raw = (
        "\x1efirst\x1ffix(site): repair atlas\n"
        "site/tests/atlas.test.ts\nsite/tests/practice.test.ts\n"
        "site/src/atlas/WordCard.tsx\n"
        "\x1esecond\x1ffix(tests): repair test\ntests/test_x.py\n"
        "\x1ethird\x1fdocs: describe atlas\nsite/src/atlas/WordCard.tsx\n"
        "\x1efourth\x1ffix(docs): correct example\ndocs/example.md\n"
    )
    monkeypatch.setattr(census, "_git", lambda *args: raw)

    assert census._path_buckets(census.PRIMARY_SINCE, census.PRIMARY_UNTIL) == {
        "tests": 2,
        "site_atlas": 1,
        "no_listed_bucket": 1,
    }
