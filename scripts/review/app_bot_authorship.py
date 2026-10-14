"""Positive GitHub evidence that a commit was authored by an allowlisted app bot (#10531).

A commit without an ``X-Agent`` trailer is normally refused as authorship
unknown. The single exception is a commit that GitHub itself reports, for that
exact SHA, as authored by an allowlisted GitHub App bot account and created and
signed by GitHub (``web-flow``), so a local Git identity, a commit message or a
cached record never proves it. The class is ``verified_app_bot``: it names no
model and no model family, so it excludes no reviewer family, while risk
floors, qualification and exact-head rules apply unchanged.

The allowlist holds exactly Dependabot. Adding a bot changes who may author
reviewable work without a trailer, which needs designated approval.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

VERIFIED_APP_BOT = "verified_app_bot"
_SHA = re.compile(r"[0-9a-f]{40}\Z")


@dataclass(frozen=True)
class AppBot:
    """One GitHub App bot account, identified by every field GitHub reports for its commits."""

    login: str
    account_id: int
    author_name: str
    author_email: str


APP_BOT_ALLOWLIST: tuple[AppBot, ...] = (
    AppBot(
        login="dependabot[bot]",
        account_id=49699333,
        author_name="dependabot[bot]",
        author_email="49699333+dependabot[bot]@users.noreply.github.com",
    ),
)
# GitHub creates and signs the commits its apps make through the API as this
# account; a commit pushed from a local checkout has another committer.
GITHUB_COMMITTER_LOGIN = "web-flow"
GITHUB_COMMITTER_ID = 19864447
GITHUB_COMMITTER_NAME = "GitHub"
GITHUB_COMMITTER_EMAIL = "noreply@github.com"


def verified_app_bot_login(commit: object, sha: str, repository: str) -> str | None:
    """The allowlisted bot login that GitHub's REST commit object for ``sha`` proves, else None.

    ``commit`` is the live ``GET repos/{repo}/commits/{sha}`` response. Every
    field must be present and agree: the SHA, the linked account (login, id,
    ``Bot`` type), the Git author name and email, the ``web-flow`` account
    (login, id, ``User`` type), repository URLs and a valid signature. Anything
    missing, malformed or different proves nothing.
    """
    if (
        not isinstance(sha, str)
        or not _SHA.fullmatch(sha)
        or not isinstance(repository, str)
        or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
    ):
        return None
    if not isinstance(commit, Mapping) or commit.get("sha") != sha:
        return None
    if (
        commit.get("url") != f"https://api.github.com/repos/{repository}/commits/{sha}"
        or commit.get("html_url") != f"https://github.com/{repository}/commit/{sha}"
    ):
        return None
    author = commit.get("author")
    committer = commit.get("committer")
    git = commit.get("commit")
    if not isinstance(author, Mapping) or not isinstance(committer, Mapping) or not isinstance(git, Mapping):
        return None
    git_author = git.get("author")
    git_committer = git.get("committer")
    verification = git.get("verification")
    if (
        not isinstance(git_author, Mapping)
        or not isinstance(git_committer, Mapping)
        or not isinstance(verification, Mapping)
    ):
        return None
    if (
        git.get("url") != f"https://api.github.com/repos/{repository}/git/commits/{sha}"
        or committer.get("login") != GITHUB_COMMITTER_LOGIN
        or committer.get("type") != "User"
        or type(committer.get("id")) is not int
        or committer["id"] != GITHUB_COMMITTER_ID
        or git_committer.get("name") != GITHUB_COMMITTER_NAME
        or git_committer.get("email") != GITHUB_COMMITTER_EMAIL
        or verification.get("verified") is not True
        or verification.get("reason") != "valid"
    ):
        return None
    for bot in APP_BOT_ALLOWLIST:
        if (
            author.get("login") == bot.login
            and author.get("type") == "Bot"
            and type(author.get("id")) is int
            and author["id"] == bot.account_id
            and git_author.get("name") == bot.author_name
            and git_author.get("email") == bot.author_email
        ):
            return bot.login
    return None


def listing_app_bot_login(listing: Iterable[object], repository: str) -> Callable[[str], str | None]:
    """A per-SHA proof over a live GitHub commit listing (``GET repos/{repo}/pulls/{n}/commits``).

    Each listed commit object is the same REST shape as a single-commit read.
    A SHA proves a bot only through its own single entry; a missing or
    duplicated entry proves nothing.
    """
    entries = tuple(listing)

    def login(sha: str) -> str | None:
        matches = [entry for entry in entries if isinstance(entry, Mapping) and entry.get("sha") == sha]
        return verified_app_bot_login(matches[0], sha, repository) if len(matches) == 1 else None

    return login
