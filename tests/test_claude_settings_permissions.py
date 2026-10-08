"""Contract for the native Claude Code permission rules in the shared settings.

``npm run agents:deploy`` rsyncs ``agents_extensions/shared/settings.json``
verbatim to ``.claude/settings.json``, so the source file IS the deployed shape.

In auto mode, allow/ask/deny rules resolve before the classifier, so narrow
allow rules keep routine driver commands deterministic when the classifier
returns no verdict. Auto mode drops broad arbitrary-code allow rules
(``Bash(*)``, wildcarded interpreters), and a broad rule would also be unsafe in
the modes that honour it, so this contract rejects them outright.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS = REPO_ROOT / "agents_extensions" / "shared" / "settings.json"

INTERPRETERS = ("python", "python3", ".venv/bin/python")
SUDO_SUBCOMMANDS = {"systemctl", "journalctl", "apt-get", "ufw", "mount", "umount", "caddy"}


def _permissions() -> dict:
    return json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"]


def _bash_patterns(rules: list[str]) -> list[str]:
    return [rule[len("Bash(") : -1] for rule in rules if rule.startswith("Bash(") and rule.endswith(")")]


def _matches(pattern: str, command: str) -> bool:
    """Documented Bash rule matching: ``*`` is any text, and a lone trailing
    `` *`` also matches the bare command (code.claude.com/docs/en/permissions)."""
    if pattern.endswith(" *") and pattern.count("*") == 1 and command == pattern[:-2]:
        return True
    regex = ".*".join(re.escape(part) for part in pattern.split("*"))
    return re.fullmatch(regex, command, flags=re.DOTALL) is not None


def _decide(command: str) -> str | None:
    """Precedence is deny, then ask, then allow; specificity never reorders it."""
    permissions = _permissions()
    for verdict in ("deny", "ask", "allow"):
        if any(_matches(p, command) for p in _bash_patterns(permissions.get(verdict, []))):
            return verdict
    return None


# Matches any head whose basename is a bare interpreter/shell binary — not just
# the exact strings in INTERPRETERS — so a disguised path like
# "/some/venv/bin/python3.11" or "/opt/foo/bash" is still caught (#9030 Grok
# review: pytest/interpreter allow rules must never hide behind a path).
# Also catches the free-threaded build suffix ("python3.13t") and the dash/zsh
# shells (#9030 round-2 residual).
_INTERPRETER_HEAD_RE = re.compile(r"(^|/)(python(3(\.\d+)?t?)?|bash|sh|dash|zsh)$")


def _is_interpreter_head(head: str) -> bool:
    return head in INTERPRETERS or bool(_INTERPRETER_HEAD_RE.search(head))


def test_session_env_disables_bytecode_for_sibling_git() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert settings["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_allow_rules_name_the_interpreter_relative_to_the_checkout() -> None:
    """Allow rules must not pin one machine's checkout location: an
    interpreter head is either bare or the checkout-relative venv path."""
    for pattern in _bash_patterns(_permissions()["allow"]):
        head = pattern.split(" ", 1)[0]
        if _is_interpreter_head(head):
            assert head in INTERPRETERS, pattern


def test_allow_list_is_present_and_bash_scoped() -> None:
    allow = _permissions()["allow"]
    assert len(allow) >= 40
    assert len(allow) == len(set(allow)), "duplicate allow rules"
    assert all(rule.startswith("Bash(") and rule.endswith(")") for rule in allow)


def test_allow_list_has_no_push_or_switch_rule() -> None:
    # #9030 round-2 (Grok): a trailing "*" in a push/delete allow rule also
    # swallows extra refspecs and clustered short flags (-uf force-pushes),
    # and prefix globs cannot make `git push`/`git switch` safe. These now go
    # back to the auto-mode classifier, which force-blocks by default.
    allow = _bash_patterns(_permissions()["allow"])
    assert not any(p.startswith("git push") for p in allow)
    assert not any(p.startswith("git switch") for p in allow)


def test_branch_sweep_and_read_only_branch_probes_are_allowed() -> None:
    allow = _permissions()["allow"]
    assert {
        "Bash(.venv/bin/python -m scripts.hygiene.branch_sweep *)",
        "Bash(git for-each-ref *)",
    } <= set(allow)
    assert _decide(".venv/bin/python -m scripts.hygiene.branch_sweep --json") == "allow"
    assert _decide("git for-each-ref refs/remotes/origin") == "allow"
    assert not any(pattern.startswith("git push") for pattern in _bash_patterns(allow))


@pytest.mark.parametrize("command", [
    "git ls-remote",
    "git ls-remote --heads origin",
    "git ls-remote --upload-pack='sh -c id' .",
    "git ls-remote --receive-pack='sh -c id' .",
    "git ls-remote -u 'sh -c id' .",
    "git -c protocol.version=2 ls-remote .",
    "git pull --upload-pack='sh -c id' origin",
    "git clone --upload-pack='sh -c id' . /tmp/copy",
    "git archive --remote=. --exec='sh -c id' HEAD",
    "git submodule update --remote",
    "git -c protocol.ext.allow=always fetch origin",
    "git push",
    "git push origin HEAD:codex/x",
])
def test_no_allow_rule_admits_other_git_transport_or_push(command: str) -> None:
    allow = _bash_patterns(_permissions()["allow"])
    assert not any(_matches(pattern, command) for pattern in allow), command


@pytest.mark.parametrize("command", [
    "git fetch origin",
    "git fetch -q origin main",
    "git fetch --prune origin",
])
def test_routine_git_fetch_is_allowed(command: str) -> None:
    assert _decide(command) == "allow"


@pytest.mark.parametrize("command", [
    "git fetch --upload-pack='touch x; git-upload-pack' origin",
    "git fetch origin --upload-pack=x",
    "git fetch origin --upload-pack",
    "git fetch --upload-pack x origin",
    # Git accepts unique long-option abbreviations, including --upl.
    "git fetch --upl='touch x; git-upload-pack' origin",
])
def test_exec_capable_git_fetch_option_is_denied(command: str) -> None:
    allow = _bash_patterns(_permissions()["allow"])
    assert any(_matches(pattern, command) for pattern in allow), command
    assert _decide(command) == "deny"


def test_allow_list_has_no_broad_arbitrary_code_rule() -> None:
    allow = _permissions()["allow"]
    assert "Bash" not in allow
    for pattern in _bash_patterns(allow):
        head = pattern.split(" ", 1)[0]
        assert not head.startswith("*"), pattern
        assert pattern not in {"*", "sudo *", "bash *", "sh *", "node *", "npx *", "npm run *", "gh api *"}, pattern
        assert not pattern.startswith(("gh api", "gh repo", "bash ", "sh ", "eval ", "env ")), pattern
        # The legacy ":*" suffix means "prefix + space + anything", so
        # "HEAD:*" would never match "HEAD:branch". Keep every rule explicit.
        assert not pattern.endswith(":*"), pattern
        if head.startswith("sudo"):
            assert pattern.split(" ")[1] in SUDO_SUBCOMMANDS, pattern
        if _is_interpreter_head(head):
            if head.endswith(("/bash", "/sh")) or head in {"bash", "sh"}:
                pytest.fail(f"shell interpreter must never appear in an unrestricted allow rule: {pattern}")
            target = pattern[len(head) :].lstrip()
            # pytest imports any file it is pointed at, so an allow rule can
            # never shape-match "-m pytest ..." — that goes back to the
            # classifier (#9030 Grok review).
            assert target.startswith(("scripts/", "-m scripts."))
            assert "pytest" not in target, pattern


def test_no_ask_rule_shadows_an_allow_rule() -> None:
    # A matching ask rule outranks allow; in auto mode it prompts and in
    # headless dontAsk it denies, which would silently undo the allow list.
    assert not _permissions().get("ask")


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        # `git push`/`git switch` are no longer pre-approved at all (#9030
        # round-2, driver decision): a trailing "*" cannot be made safe
        # against a second refspec or a clustered short flag, so these now
        # fall through to the auto-mode classifier instead of being allowed.
        ("git push origin HEAD:claude/impl-automode-allow", None),
        ("git push origin HEAD:claude/x", None),
        ("git push origin --delete claude/impl-automode-allow", None),
        ("git push origin --delete grok/y", None),
        ("gh pr merge 9030 --squash", "allow"),
        ("gh workflow run ci.yml --ref claude/x", "allow"),
        (".venv/bin/python -m scripts.fleet.capacity_pick --json", "allow"),
        ("npm run agents:deploy", "allow"),
        ("sudo systemctl restart caddy", "allow"),
        ("sudo caddy reload --config /etc/caddy/Caddyfile", "allow"),
        ("git push origin HEAD:claude/x --force", "deny"),
        ("git push origin --delete claude/x --force", "deny"),
        # deny wins even though an allow rule also matches this one
        ("sudo systemctl link /tmp/x.service", "deny"),
        ("git push origin HEAD:main", "deny"),
        ("git push origin HEAD:main --force", "deny"),
        ("git push origin HEAD:refs/heads/main", "deny"),
        ("git push origin --delete main", "deny"),
        ("gh pr merge 9030 --admin --squash", "deny"),
        ("git push origin HEAD", None),
        ("git push origin HEAD -f", "deny"),
        ("git push origin HEAD --force-with-lease", "deny"),
        # `Bash(git push *main*)` now catches a bare ref name too, so this is
        # deny where round-1 left it unmatched.
        ("git push origin --delete refs/heads/main", "deny"),
        ("git push origin --delete main --force", "deny"),
        ("git push origin --delete --force main", "deny"),
        ("git push origin HEAD:gh-pages", "deny"),
        ("git push origin HEAD:production --force", "deny"),
        (
            "/workdir/repo/.venv/bin/python -m pytest -o python_files='*.py' scratch/test_evil.py",
            None,
        ),
        ("git switch -f main", "deny"),
        # never pre-approved: left to the classifier or a prompt
        ("gh api repos/learn-ukrainian/learn-ukrainian.github.io", None),
        ("gh repo delete learn-ukrainian/learn-ukrainian.github.io", None),
        ("/workdir/repo/.venv/bin/python -c 'print(1)'", None),
        ("sudo rm -rf /var/tmp/lu", None),
        ("sudo bash -c id", None),
        ("git push --force origin claude/x", "deny"),
        # Grok review r2 (#9030): a second refspec or a clustered short flag
        # slipped past the round-1 rules because the allow rule's trailing
        # "*" swallowed it. The push/switch allow rules are gone now, so most
        # of these are simply unmatched; the ones that name a protected ref
        # (main/gh-pages/production, anywhere in the command) get a hard
        # deny. `Bash(git push *main*)` etc. also denies a legitimate agent
        # branch whose name merely contains one of those words (e.g.
        # "claude/maintenance-fix") — accepted collateral, not a bug.
        ("git push origin HEAD:claude/x main", "deny"),
        ("git push origin HEAD:claude/x gh-pages", "deny"),
        ("git push origin HEAD:claude/x production", "deny"),
        ("git push origin HEAD:claude/x refs/heads/main", "deny"),
        ("git push origin HEAD:claude/x HEAD", None),
        ("git push origin --delete claude/x main", "deny"),
        ("git push origin --delete claude/x gh-pages", "deny"),
        ("git push origin --delete claude/x production", "deny"),
        ("git push origin --delete claude/x refs/heads/gh-pages", "deny"),
        ("git push origin --delete claude/x refs/heads/production", "deny"),
        ("git push origin HEAD:claude/x -uf", None),
        ("git push origin HEAD:claude/x -fu", None),
        ("git push origin HEAD:claude/x -fv", None),
        ("git push origin HEAD:claude/x main -uf", "deny"),
        ("git switch other -f", "deny"),
        ("git switch other --force", "deny"),
        ("git switch other --discard-changes", "deny"),
        ("git switch --guess -f other", "deny"),
        ("sudo systemctl --user link x", "deny"),
        ("sudo systemctl --force link", "deny"),
        ("sudo systemctl -f link", "deny"),
    ],
)
def test_rule_precedence(command: str, expected: str | None) -> None:
    assert _decide(command) == expected


@pytest.mark.parametrize(
    "command",
    [
        # `git push`/`git switch` no longer match any allow rule at all
        # (#9030 round-2); fetch execution options now exercise deny precedence.
        "git fetch --upload-pack=x origin",
        "git fetch origin --upl=x",
        "gh pr merge 1 --admin --squash",
        "sudo systemctl link /tmp/x.service",
        "sudo systemctl --user link x",
    ],
)
def test_denied_commands_are_also_allowed_so_precedence_is_exercised(command: str) -> None:
    allow = _bash_patterns(_permissions()["allow"])
    assert any(_matches(p, command) for p in allow), command
