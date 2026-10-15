"""Coverage for scripts/ci/check_agent_attribution.py (#10736 S1).

Every case builds a real temporary repository: an ``origin`` that serves
``refs/pull/N/head`` and a work repository whose ``queue`` branch holds one squash
commit per PR, as the merge queue produces. Only GitHub's REST API is replaced, by a
function that returns payloads shaped like ``GET repos/{repo}/commits/{sha}``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci import check_agent_attribution as check

_GIT_BIN = os.environ.get("AGENT_REAL_GIT", "git")  # the agent shim refuses branch switches
REPOSITORY = "owner/repo"
SCRIPT = Path(check.__file__).resolve()
BOT_NAME = "dependabot[bot]"
BOT_EMAIL = "49699333+dependabot[bot]@users.noreply.github.com"
BOT_AUTHOR = f"{BOT_NAME} <{BOT_EMAIL}>"
CO_AUTHORS = "---------\n\nCo-authored-by: LU Unattributed <unattributed@local.invalid>\nCo-authored-by: OpenAI <openai@local.invalid>"


def _git(repo: Path, *args: str, stdin: str | None = None) -> str:
    result = subprocess.run(
        [_GIT_BIN, *args], cwd=repo, input=stdin, capture_output=True, text=True, check=False, timeout=30
    )
    assert result.returncode == 0, f"git {' '.join(args)}: {result.stderr}"
    return result.stdout.strip()


class Queue:
    """A repository with PR branches, ``refs/pull/N/head`` on origin and a squash ``queue`` branch."""

    def __init__(self, tmp_path: Path) -> None:
        self.origin = tmp_path / "origin.git"
        self.repo = tmp_path / "work"
        self.origin.mkdir()
        self.repo.mkdir()
        _git(self.origin, "init", "--bare", "-b", "main")
        _git(self.repo, "init", "-b", "main")
        for key, value in (
            ("user.name", "LU Unattributed"),
            ("user.email", "unattributed@local.invalid"),
            ("commit.gpgsign", "false"),
        ):
            _git(self.repo, "config", key, value)
        _git(self.repo, "remote", "add", "origin", str(self.origin))
        self._write("README.md", "base\n")
        self.base = self._commit("Initial commit")
        self.tip = self.base
        self._counter = 0

    def _write(self, name: str, text: str) -> None:
        (self.repo / name).write_text(text, encoding="utf-8")
        _git(self.repo, "add", name)

    def _commit(self, message: str, author: str | None = None) -> str:
        args = ["commit", "--cleanup=verbatim", "-F", "-"]
        if author:
            args += ["--author", author]
        _git(self.repo, *args, stdin=message)
        return _git(self.repo, "rev-parse", "HEAD")

    def open_pr(self, number: int, commits: list[str | tuple[str, str]]) -> list[str]:
        """Branch ``prN`` from the base with ``commits`` and publish it as ``refs/pull/N/head``."""
        _git(self.repo, "checkout", "-q", "-B", f"pr{number}", self.base)
        shas = [self.push_commit(number, commit, publish=False) for commit in commits]
        self.publish(number)
        return shas

    def push_commit(self, number: int, commit: str | tuple[str, str], *, publish: bool = True) -> str:
        message, author = (commit, None) if isinstance(commit, str) else commit
        _git(self.repo, "checkout", "-q", f"pr{number}")
        self._counter += 1
        self._write(f"pr{number}-{self._counter}.txt", f"{self._counter}\n")
        sha = self._commit(message, author)
        if publish:
            self.publish(number)
        return sha

    def publish(self, number: int) -> None:
        _git(self.repo, "push", "-q", "--force", "origin", f"pr{number}:refs/pull/{number}/head")

    def land(self, number: int, landed: str) -> str:
        """Squash ``prN`` onto the queue tip with ``landed`` as its whole message."""
        _git(self.repo, "checkout", "-q", "-B", "queue", self.tip)
        _git(self.repo, "merge", "--squash", f"pr{number}")
        self.tip = self._commit(landed)
        return self.tip

    def land_merge_commit(self, number: int, landed: str) -> str:
        _git(self.repo, "checkout", "-q", "-B", "queue", self.tip)
        _git(self.repo, "merge", "--no-ff", "--no-edit", "-q", f"pr{number}")
        _git(self.repo, "commit", "--amend", "--cleanup=verbatim", "-q", "-F", "-", stdin=landed)
        self.tip = _git(self.repo, "rev-parse", "HEAD")
        return self.tip


@pytest.fixture
def queue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Queue:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.setenv(check.ENFORCE_ENV, "1")
    fixture = Queue(tmp_path)
    monkeypatch.chdir(fixture.repo)
    return fixture


def _bot_commit(sha: str) -> dict[str, object]:
    """The REST commit object GitHub returns for a Dependabot commit it created and signed."""
    return {
        "sha": sha,
        "url": f"https://api.github.com/repos/{REPOSITORY}/commits/{sha}",
        "html_url": f"https://github.com/{REPOSITORY}/commit/{sha}",
        "author": {"login": BOT_NAME, "type": "Bot", "id": 49699333},
        "committer": {"login": "web-flow", "type": "User", "id": 19864447},
        "commit": {
            "url": f"https://api.github.com/repos/{REPOSITORY}/git/commits/{sha}",
            "author": {"name": BOT_NAME, "email": BOT_EMAIL},
            "committer": {"name": "GitHub", "email": "noreply@github.com"},
            "verification": {"verified": True, "reason": "valid"},
        },
    }


def _forged_commit(sha: str) -> dict[str, object]:
    """A commit that only claims the bot's Git author name: GitHub reports a person and no signature."""
    payload = _bot_commit(sha)
    payload["author"] = {"login": "someone", "type": "User", "id": 7}
    payload["committer"] = {"login": "someone", "type": "User", "id": 7}
    payload["commit"]["committer"] = {"name": "Someone", "email": "someone@example.com"}  # type: ignore[index]
    payload["commit"]["verification"] = {"verified": False, "reason": "unsigned"}  # type: ignore[index]
    return payload


def _api(payloads: dict[str, dict[str, object]]):
    """A GitHub GET that serves ``payloads`` by commit SHA and fails like the API for anything else."""

    def get(path: str) -> object:
        prefix = f"repos/{REPOSITORY}/commits/"
        if not path.startswith(prefix) or path[len(prefix) :] not in payloads:
            raise RuntimeError(f"GET {path} failed: HTTPError")
        return payloads[path[len(prefix) :]]

    return get


def _run_group(queue: Queue, capsys: pytest.CaptureFixture[str], *, get=None) -> tuple[int, str]:
    code = check.main(["--merge-group", queue.base, queue.tip, "--repository", REPOSITORY], github_get=get)
    return code, capsys.readouterr().out


def _run_pr(queue: Queue, capsys: pytest.CaptureFixture[str], head: str, *, get=None) -> tuple[int, str]:
    code = check.main(["--pr", queue.base, head, "--repository", REPOSITORY], github_get=get)
    return code, capsys.readouterr().out


def _squash_message(subject: str, *values: str, co_authors: bool = True) -> str:
    """The ``COMMIT_MESSAGES`` shape: ``* subject`` blocks, each with its X-Agent line, then co-authors."""
    blocks = [f"* {subject}\n\nWhy this changed.\n\nX-Agent: {value}" for value in values]
    parts = [f"{subject} (#{{n}})", *blocks]
    if co_authors:
        parts.append(CO_AUTHORS)
    return "\n\n".join(parts) + "\n"


def _landed(number: int, subject: str, *values: str, co_authors: bool = True) -> str:
    return _squash_message(subject, *values, co_authors=co_authors).replace("{n}", str(number))


# --- merge-group: attribution per PR ---------------------------------------------------------


def test_commit_messages_shape_passes_for_a_chain(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(11, ["fix one\n\nX-Agent: codex/impl-11\n"])
    queue.open_pr(12, ["fix two\n\nX-Agent: claude/impl-12\n"])
    queue.land(11, _landed(11, "fix one", "codex/impl-11"))
    queue.land(12, _landed(12, "fix two", "claude/impl-12"))

    code, out = _run_group(queue, capsys)

    assert code == 0, out
    assert "commits=2 violations=0 enforce" in out


def test_one_pr_omitting_attribution_fails_while_its_neighbour_passes(
    queue: Queue, capsys: pytest.CaptureFixture[str]
) -> None:
    queue.open_pr(21, ["fix one\n\nX-Agent: codex/impl-21\n"])
    queue.open_pr(22, ["fix two\n\nX-Agent: claude/impl-22\n"])
    first = queue.land(21, _landed(21, "fix one", "codex/impl-21"))
    second = queue.land(22, _landed(22, "fix two"))  # the PR's attribution was not transported

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert f"MISSING_ATTRIBUTION pr=#22 commit={second[:12]}" in out
    assert first[:12] not in out
    assert out.count("::error title=agent-attribution::") == 1


def test_blank_body_shape_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(31, ["fix\n\nX-Agent: codex/impl-31\n"])
    blank = "fix (#31)\n\nCo-authored-by: LU Unattributed <unattributed@local.invalid>\nCo-authored-by: OpenAI <openai@local.invalid>\n"
    queue.land(31, blank)

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "MISSING_ATTRIBUTION pr=#31" in out


def test_attribution_never_needs_to_be_the_last_paragraph(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(32, ["fix\n\nX-Agent: codex/impl-32\n"])
    queue.land(32, _landed(32, "fix", "codex/impl-32"))
    parsed = _git(queue.repo, "log", "-1", "--format=%(trailers:key=X-Agent,valueonly)", "queue")
    assert parsed == ""  # git's trailer parser cannot see it: GitHub's co-author block is last

    code, out = _run_group(queue, capsys)

    assert code == 0, out


def test_two_commit_pr_needs_both_values(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(41, ["part one\n\nX-Agent: codex/impl-41\n", "part two\n\nX-Agent: claude/impl-41-b\n"])
    queue.land(41, _landed(41, "both", "codex/impl-41"))

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "INCOMPLETE_ATTRIBUTION pr=#41" in out
    assert "omits 1 of 2 PR value(s): claude/impl-41-b" in out


def test_two_commit_pr_with_both_values_passes(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(42, ["part one\n\nX-Agent: codex/impl-42\n", "part two\n\nX-Agent: claude/impl-42-b\n"])
    queue.land(42, _landed(42, "both", "codex/impl-42", "claude/impl-42-b"))

    code, out = _run_group(queue, capsys)

    assert code == 0, out


def test_commit_without_attribution_fails_even_when_another_supplies_one(
    queue: Queue, capsys: pytest.CaptureFixture[str]
) -> None:
    shas = queue.open_pr(43, ["part one\n\nX-Agent: codex/impl-43\n", "part two without attribution\n"])
    queue.land(43, _landed(43, "both", "codex/impl-43"))

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert f"SOURCE_UNATTRIBUTED pr=#43 commit={shas[1][:12]}" in out


def test_requeue_with_a_new_head_is_checked_afresh(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(51, ["first\n\nX-Agent: codex/impl-51\n"])
    queue.land(51, _landed(51, "feature", "codex/impl-51"))
    assert _run_group(queue, capsys)[0] == 0

    # A review-fix push by another agent moves refs/pull/51/head; the old squash is now stale.
    queue.push_commit(51, "review fix\n\nX-Agent: claude/impl-51-fix\n")
    code, out = _run_group(queue, capsys)
    assert code == 1
    assert "INCOMPLETE_ATTRIBUTION pr=#51" in out

    # The requeue builds a new squash commit that carries both values.
    queue.tip = queue.base
    queue.land(51, _landed(51, "feature", "codex/impl-51", "claude/impl-51-fix"))
    code, out = _run_group(queue, capsys)
    assert code == 0, out


# --- merge-group: fail closed ----------------------------------------------------------------


def test_subject_without_pr_number_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(61, ["fix\n\nX-Agent: codex/impl-61\n"])
    queue.land(61, "fix without a number\n\n* fix\n\nX-Agent: codex/impl-61\n")

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "MISSING_PR_REFERENCE" in out


def test_only_a_terminal_pr_number_counts(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(62, ["fix\n\nX-Agent: codex/impl-62\n"])
    queue.land(62, "fix (#62) and more\n\nX-Agent: codex/impl-62\n")

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "MISSING_PR_REFERENCE" in out


def test_issue_reference_before_the_pr_number_is_not_the_pr(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(63, ["fix\n\nX-Agent: codex/impl-63\n"])
    queue.land(63, "fix the thing (#9999) (#63)\n\nX-Agent: codex/impl-63\n")

    code, out = _run_group(queue, capsys)

    assert code == 0, out


def test_unfetchable_pull_ref_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(71, ["fix\n\nX-Agent: codex/impl-71\n"])
    queue.land(71, _landed(71, "fix", "codex/impl-71"))
    _git(queue.repo, "push", "-q", "origin", ":refs/pull/71/head")

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "FETCH_FAILED pr=#71" in out


def test_empty_chain_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    code = check.main(["--merge-group", queue.base, queue.base])
    out = capsys.readouterr().out

    assert code == 1
    assert "EMPTY_CHAIN" in out


def test_base_that_is_not_an_ancestor_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(81, ["fix\n\nX-Agent: codex/impl-81\n"])
    landed = queue.land(81, _landed(81, "fix", "codex/impl-81"))

    code = check.main(["--merge-group", landed, queue.base])
    out = capsys.readouterr().out

    assert code == 1
    assert "GIT_ERROR" in out


def test_unknown_or_empty_ref_fails_closed(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    for head in ("0" * 40, ""):
        code = check.main(["--merge-group", queue.base, head])
        assert code == 1
        assert "GIT_ERROR" in capsys.readouterr().out


def test_merge_commit_in_the_chain_is_not_a_squash_commit(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(91, ["fix\n\nX-Agent: codex/impl-91\n"])
    # A tip distinct from the PR base makes the merge a true two-parent commit.
    _git(queue.repo, "checkout", "-q", "-B", "queue", queue.base)
    queue._write("other.txt", "x\n")
    queue.tip = queue._commit("other (#90)\n\nX-Agent: codex/impl-90\n")
    queue.land_merge_commit(91, _landed(91, "fix", "codex/impl-91"))

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "UNEXPECTED_SHAPE" in out


@pytest.mark.parametrize(
    "bad_line",
    [
        "X-Agent: codex",
        "X-Agent:codex/impl-1",
        "X-Agent: codex/impl 1",
        "X-Agent: Codex/impl-1",
        "X-Agent:  codex/impl-1",
        "X-Agent: codex/",
    ],
)
def test_malformed_value_fails_and_is_not_echoed(
    queue: Queue, capsys: pytest.CaptureFixture[str], bad_line: str
) -> None:
    queue.open_pr(101, [f"fix\n\n{bad_line}\n"])
    queue.land(101, f"fix (#101)\n\n{bad_line}\n\nCo-authored-by: A <a@local.invalid>\n")

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "MALFORMED_ATTRIBUTION" in out
    assert bad_line.split(":", 1)[1].strip() not in out or bad_line.split(":", 1)[1].strip() == ""


def test_malformed_line_beside_a_good_one_still_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(102, ["fix\n\nX-Agent: codex/impl-102\n"])
    queue.land(102, "fix (#102)\n\nX-Agent: codex/impl-102\nX-Agent: oops\n")

    code, out = _run_group(queue, capsys)

    assert code == 1
    assert "MALFORMED_ATTRIBUTION" in out


# --- bot exemption --------------------------------------------------------------------------


def test_verified_dependabot_pr_is_exempt(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    (sha,) = queue.open_pr(111, [("Bump pytest from 8 to 9\n", BOT_AUTHOR)])
    queue.land(111, "Bump pytest from 8 to 9 (#111)\n\nCo-authored-by: dependabot[bot] <x@local.invalid>\n")

    code, out = _run_group(queue, capsys, get=_api({sha: _bot_commit(sha)}))

    assert code == 0, out


def test_forged_bot_name_is_not_exempt(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    (sha,) = queue.open_pr(112, [("Bump pytest from 8 to 9\n", BOT_AUTHOR)])
    queue.land(112, "Bump pytest from 8 to 9 (#112)\n")

    code, out = _run_group(queue, capsys, get=_api({sha: _forged_commit(sha)}))

    assert code == 1
    assert "MISSING_ATTRIBUTION pr=#112" in out


def test_bot_suffix_in_the_git_author_proves_nothing_without_the_api(
    queue: Queue, capsys: pytest.CaptureFixture[str]
) -> None:
    queue.open_pr(113, [("Bump pytest from 8 to 9\n", BOT_AUTHOR)])
    queue.land(113, "Bump pytest from 8 to 9 (#113)\n")

    for get in (None, _api({})):
        code, out = _run_group(queue, capsys, get=get)
        assert code == 1
        assert "MISSING_ATTRIBUTION pr=#113" in out


def test_bot_payload_for_another_sha_proves_nothing(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    (sha,) = queue.open_pr(114, [("Bump pytest from 8 to 9\n", BOT_AUTHOR)])
    queue.land(114, "Bump pytest from 8 to 9 (#114)\n")
    other = "1" * 40

    code, out = _run_group(queue, capsys, get=_api({sha: _bot_commit(other)}))

    assert code == 1
    assert "MISSING_ATTRIBUTION pr=#114" in out


def test_mixed_bot_and_agent_pr_keeps_agent_attribution(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    bot, _agent = queue.open_pr(
        115, [("Bump pytest from 8 to 9\n", BOT_AUTHOR), "adapt to pytest 9\n\nX-Agent: codex/impl-115\n"]
    )
    get = _api({bot: _bot_commit(bot)})

    queue.land(115, "Bump pytest from 8 to 9 (#115)\n")  # the bot exemption must not swallow the agent commit
    code, out = _run_group(queue, capsys, get=get)
    assert code == 1
    assert "MISSING_ATTRIBUTION pr=#115" in out

    queue.tip = queue.base
    queue.land(115, _landed(115, "Bump pytest from 8 to 9", "codex/impl-115"))
    code, out = _run_group(queue, capsys, get=get)
    assert code == 0, out


def test_mixed_pr_with_unverified_bot_commit_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    queue.open_pr(116, [("Bump pytest from 8 to 9\n", BOT_AUTHOR), "adapt\n\nX-Agent: codex/impl-116\n"])
    queue.land(116, _landed(116, "Bump", "codex/impl-116"))

    code, out = _run_group(queue, capsys, get=_api({}))

    assert code == 1
    assert "SOURCE_UNATTRIBUTED pr=#116" in out


# --- pull_request mode ----------------------------------------------------------------------


def test_pr_mode_passes_when_every_commit_is_attributed(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    shas = queue.open_pr(201, ["one\n\nX-Agent: codex/impl-201\n", "two\n\nX-Agent: claude/impl-201\n"])

    code, out = _run_pr(queue, capsys, shas[-1])

    assert code == 0, out
    assert "mode=pr commits=2 violations=0" in out


def test_pr_mode_fails_on_one_unattributed_commit(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    shas = queue.open_pr(202, ["one\n\nX-Agent: codex/impl-202\n", "two without attribution\n"])

    code, out = _run_pr(queue, capsys, shas[-1])

    assert code == 1
    assert f"MISSING_ATTRIBUTION commit={shas[1][:12]}" in out
    assert shas[0][:12] not in out


def test_pr_mode_skips_merge_commits_and_fails_an_empty_range(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    shas = queue.open_pr(203, ["one\n\nX-Agent: codex/impl-203\n"])
    _git(queue.repo, "checkout", "-q", "-B", "side", queue.base)
    queue._write("side.txt", "s\n")
    queue._commit("side (#1)\n\nX-Agent: codex/side\n")
    _git(queue.repo, "checkout", "-q", "pr203")
    _git(queue.repo, "merge", "--no-ff", "-q", "-m", "Merge branch 'main' into pr203", "side")
    head = _git(queue.repo, "rev-parse", "HEAD")
    assert len(_git(queue.repo, "rev-list", "--parents", "-n", "1", head).split()) == 3

    code, out = _run_pr(queue, capsys, head)
    assert code == 0, out

    code = check.main(["--pr", head, head])
    assert code == 1
    assert "EMPTY_CHAIN" in capsys.readouterr().out
    assert shas


def test_pr_mode_bot_exemption_requires_the_api_proof(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    (sha,) = queue.open_pr(204, [("Bump pytest from 8 to 9\n", BOT_AUTHOR)])

    code, out = _run_pr(queue, capsys, sha, get=_api({sha: _bot_commit(sha)}))
    assert code == 0, out

    code, out = _run_pr(queue, capsys, sha, get=_api({sha: _forged_commit(sha)}))
    assert code == 1
    assert "MISSING_ATTRIBUTION" in out


def test_pr_mode_malformed_value_fails(queue: Queue, capsys: pytest.CaptureFixture[str]) -> None:
    (sha,) = queue.open_pr(205, ["one\n\nX-Agent: codex\n"])

    code, out = _run_pr(queue, capsys, sha)

    assert code == 1
    assert "MALFORMED_ATTRIBUTION" in out


# --- enforcement switch, parsing and CLI -----------------------------------------------------


@pytest.mark.parametrize("value", [None, "0", "", "true"])
def test_report_only_unless_enforce_is_exactly_one(
    queue: Queue, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(check.ENFORCE_ENV)
    else:
        monkeypatch.setenv(check.ENFORCE_ENV, value)
    queue.open_pr(301, ["fix\n\nX-Agent: codex/impl-301\n"])
    queue.land(301, _landed(301, "fix"))

    code, out = _run_group(queue, capsys)

    assert code == 0
    assert "::warning title=agent-attribution::MISSING_ATTRIBUTION pr=#301" in out
    assert "report-only (ATTRIBUTION_ENFORCE!=1)" in out
    assert "::error" not in out


def test_script_exit_status_through_the_command_line(queue: Queue) -> None:
    queue.open_pr(401, ["fix\n\nX-Agent: codex/impl-401\n"])
    queue.land(401, _landed(401, "fix"))

    failing = subprocess.run(
        [sys.executable, str(SCRIPT), "--merge-group", queue.base, queue.tip],
        cwd=queue.repo,
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": "/usr/bin:/bin", "ATTRIBUTION_ENFORCE": "1", "HOME": str(queue.repo)},
        check=False,
    )
    assert failing.returncode == 1
    assert "MISSING_ATTRIBUTION pr=#401" in failing.stdout

    usage = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=60, check=False)
    assert usage.returncode == 2


def test_help_documents_modes_and_the_switch() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, timeout=60, check=False
    )

    assert result.returncode == 0
    for needle in ("--merge-group", "--pr", "ATTRIBUTION_ENFORCE", "Bot exemption"):
        assert needle in result.stdout


def test_pull_ref_fetch_sends_the_token_through_the_environment_only(
    queue: Queue, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[tuple[str, ...], dict[str, str] | None]] = []

    def fake_git(*args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> str:
        seen.append((args, env))
        if args[:2] == ("remote", "get-url"):
            return "https://github.com/owner/repo\n"
        if args[0] == "rev-parse":
            return "a" * 40 + "\n"
        return ""

    monkeypatch.setenv("GITHUB_TOKEN", "ghs_sentinel")
    monkeypatch.setattr(check, "_git", fake_git)

    check._source_commits("origin", 7, "b" * 40)

    (fetch,) = [(args, env) for args, env in seen if args[0] == "fetch"]
    assert fetch[0] == ("fetch", "--no-tags", "--quiet", "origin", "refs/pull/7/head")
    assert fetch[1] is not None
    assert fetch[1]["GIT_CONFIG_KEY_0"] == "http.https://github.com/.extraheader"
    assert fetch[1]["GIT_CONFIG_VALUE_0"].startswith("AUTHORIZATION: basic ")
    assert not any("ghs_sentinel" in part for args, _ in seen for part in args)


def test_a_non_github_remote_gets_no_credentials(queue: Queue, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghs_sentinel")
    queue.open_pr(501, ["fix\n\nX-Agent: codex/impl-501\n"])
    parent = queue.base

    sources = check._source_commits("origin", 501, parent)

    assert len(sources) == 1


@pytest.mark.parametrize(
    ("message", "values", "malformed"),
    [
        ("subject\n\nX-Agent: codex/impl-1\n", ("codex/impl-1",), 0),
        (
            "s\n\nX-Agent: codex/a\n\n* t\n\nX-Agent: claude/b.c_d-1\nX-Agent: codex/a\n",
            ("codex/a", "claude/b.c_d-1"),
            0,
        ),
        ("s\n\n x-agent: codex/a\n  X-Agent: codex/a\n", (), 0),
        ("s\n\nX-Agent: codex\nX-Agent: codex/a\n", ("codex/a",), 1),
        ("s\n\nX-Agent: codex/a \n", (), 1),
        ("s\n", (), 0),
    ],
)
def test_extract_attribution(message: str, values: tuple[str, ...], malformed: int) -> None:
    attribution = check.extract_attribution(message)

    assert (attribution.values, attribution.malformed) == (values, malformed)


@pytest.mark.parametrize(
    ("subject", "number"),
    [
        ("fix (#10745)", 10745),
        ("fix(infra): declare floor (#10737) (#10745)", 10745),
        ("fix (#10745) trailing", None),
        ("fix", None),
        ("fix (#0)", None),
        ("fix (#abc)", None),
    ],
)
def test_pr_number_from_subject(subject: str, number: int | None) -> None:
    assert check.pr_number_from_subject(subject) == number


def _completed(returncode: int, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["gh"], returncode, stdout=stdout, stderr="")


def test_production_getter_is_built_from_the_shared_client(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return _completed(0, '{"sha": "abc"}')

    monkeypatch.setenv("GITHUB_TOKEN", "x-token-value")
    monkeypatch.setattr(check.github_client, "run", fake_run)

    get = check._github_get_from_env()

    assert get is not None
    assert get("repos/owner/repo/commits/abc") == {"sha": "abc"}
    ((args, kwargs),) = calls
    assert args == ["gh", "api", "-X", "GET", "repos/owner/repo/commits/abc"]
    assert kwargs["fresh"] is True
    assert "x-token-value" not in " ".join(args)


def test_production_getter_needs_a_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    assert check._github_get_from_env() is None


@pytest.mark.parametrize("completed", [_completed(1), _completed(0, "not json")], ids=["exit", "body"])
def test_production_getter_failure_is_not_proof(monkeypatch: pytest.MonkeyPatch, completed) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "x-token-value")
    monkeypatch.setattr(check.github_client, "run", lambda args, **kwargs: completed)

    get = check._github_get_from_env()

    assert get is not None
    with pytest.raises(RuntimeError):
        get("repos/owner/repo/commits/abc")
    assert check._bot_verified(get, REPOSITORY, "a" * 40) is False
