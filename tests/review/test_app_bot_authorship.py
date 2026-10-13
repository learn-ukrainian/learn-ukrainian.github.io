"""#10531: only GitHub's live commit data for the exact SHA proves an allowlisted app-bot author."""

from __future__ import annotations

import copy

import pytest

from scripts.publish.github import Request
from scripts.review import record_cf_verdict as recorder
from scripts.review.app_bot_authorship import (
    APP_BOT_ALLOWLIST,
    VERIFIED_APP_BOT,
    listing_app_bot_login,
    verified_app_bot_login,
)
from scripts.review.reviewer_resolver import ResolverInputs, complete_author_families

SHA = "a" * 40
OTHER = "b" * 40


def dependabot(sha: str = SHA) -> dict:
    """The fields GitHub's REST API reports for a real Dependabot commit."""
    return {
        "sha": sha,
        "author": {"login": "dependabot[bot]", "id": 49699333, "type": "Bot"},
        "committer": {"login": "web-flow", "id": 19864447, "type": "User"},
        "commit": {
            "author": {"name": "dependabot[bot]", "email": "49699333+dependabot[bot]@users.noreply.github.com"},
            "committer": {"name": "GitHub", "email": "noreply@github.com"},
            "verification": {"verified": True, "reason": "valid"},
        },
    }


def test_allowlist_is_exactly_dependabot():
    assert [bot.login for bot in APP_BOT_ALLOWLIST] == ["dependabot[bot]"]


def test_complete_dependabot_commit_is_proven():
    assert verified_app_bot_login(dependabot(), SHA) == "dependabot[bot]"


def _set(data: dict, path: tuple[str, ...], value: object) -> dict:
    changed = copy.deepcopy(data)
    target = changed
    for key in path[:-1]:
        target = target[key]
    if value is KeyError:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return changed


@pytest.mark.parametrize(
    "path,value",
    [
        (("sha",), OTHER),
        (("sha",), KeyError),
        (("author",), None),
        (("author", "login"), "dependabot-preview[bot]"),
        (("author", "type"), "User"),
        (("author", "id"), "49699333"),
        (("author", "id"), True),
        (("author", "id"), 1),
        (("committer", "login"), "maintainer"),
        (("committer",), KeyError),
        (("commit", "author", "name"), "Dependabot"),
        (("commit", "author", "email"), "dependabot@example.invalid"),
        (("commit", "committer", "email"), "maintainer@example.invalid"),
        (("commit", "committer", "name"), "maintainer"),
        (("commit", "verification", "verified"), False),
        (("commit", "verification", "verified"), "true"),
        (("commit", "verification", "reason"), "unknown_key"),
        (("commit", "verification"), KeyError),
        (("commit",), KeyError),
    ],
)
def test_any_missing_or_different_field_proves_nothing(path, value):
    assert verified_app_bot_login(_set(dependabot(), path, value), SHA) is None


@pytest.mark.parametrize(
    "data,sha",
    [
        ({"sha": SHA, "author": {"login": "dependabot[bot]", "is_bot": True}}, SHA),
        (None, SHA),
        ([], SHA),
        (dependabot(SHA.upper()), SHA.upper()),
        (dependabot("not-a-sha"), "not-a-sha"),
    ],
    ids=["forged-is-bot-field", "none", "list", "uppercase-sha", "invalid-sha"],
)
def test_forged_or_malformed_data_proves_nothing(data, sha):
    assert verified_app_bot_login(data, sha) is None


def test_listing_proof_uses_only_the_exact_sha_entry():
    login = listing_app_bot_login([dependabot(SHA), {"sha": OTHER, "author": {"login": "maintainer"}}])
    assert login(SHA) == "dependabot[bot]"
    assert login(OTHER) is None
    assert login("c" * 40) is None
    assert listing_app_bot_login([dependabot(SHA), dependabot(SHA)])(SHA) is None


def test_live_read_requests_the_exact_sha_from_github(monkeypatch):
    calls: list[Request] = []

    def fake(args, *, input_text=None):
        calls.append(args)
        return dependabot(SHA)

    monkeypatch.setattr(recorder, "_run_json", fake)
    assert recorder.live_app_bot_login("owner/repo", SHA) == "dependabot[bot]"
    assert len(calls) == 1 and isinstance(calls[0], Request)
    assert calls[0].verb == "read-commit" and calls[0].fields == {"repo": "owner/repo", "sha": SHA}


def test_live_read_for_another_sha_proves_nothing(monkeypatch):
    monkeypatch.setattr(recorder, "_run_json", lambda args, *, input_text=None: dependabot(OTHER))
    assert recorder.live_app_bot_login("owner/repo", SHA) is None


def test_github_unreachable_proves_nothing(monkeypatch):
    def unreachable(args, *, input_text=None):
        raise recorder.RecordError("GitHub lookup or publication unavailable")

    monkeypatch.setattr(recorder, "_run_json", unreachable)
    assert recorder.live_app_bot_login("owner/repo", SHA) is None


def test_untrailered_commit_without_proof_keeps_the_refusal(tmp_path):
    entry = {"sha": SHA, "commit": {"message": "Bump a from 1 to 2\n", "tree": {"sha": OTHER}}, "parents": []}
    for login in (None, lambda _sha: None):
        with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
            recorder._attribute_commit(
                entry, repository="owner/repo", task_root=tmp_path, base_sha=lambda: OTHER, app_bot_login=login
            )
    attributed = recorder._attribute_commit(
        entry,
        repository="owner/repo",
        task_root=tmp_path,
        base_sha=lambda: OTHER,
        app_bot_login=lambda sha: "dependabot[bot]" if sha == SHA else None,
    )
    assert attributed == recorder.CommitAttribution(
        SHA, VERIFIED_APP_BOT, VERIFIED_APP_BOT, authorship=VERIFIED_APP_BOT
    )


def test_trailered_commit_never_asks_for_bot_proof(tmp_path):
    entry = {"sha": SHA, "commit": {"message": "work\n\nX-Agent: codex/gpt-6.1-sol\n"}, "parents": []}

    def tripwire(_sha):
        raise AssertionError("bot proof requested for a trailered commit")

    attributed = recorder._attribute_commit(
        entry, repository="owner/repo", task_root=tmp_path, base_sha=lambda: OTHER, app_bot_login=tripwire
    )
    assert attributed.family == "openai" and attributed.source == "trailer-model"


def test_resolver_treats_a_verified_bot_as_complete_authorship_excluding_no_family():
    inputs = ResolverInputs(author_model="", author_families=frozenset({VERIFIED_APP_BOT}))
    assert complete_author_families(inputs, "unknown") == {VERIFIED_APP_BOT}
    mixed = ResolverInputs(author_model="", author_families=frozenset({VERIFIED_APP_BOT, "anthropic"}))
    assert complete_author_families(mixed, "unknown") == {VERIFIED_APP_BOT, "anthropic"}
