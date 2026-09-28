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

INTERPRETERS = ("python", "python3", ".venv/bin/python", "/home/ops/learn-ukrainian/.venv/bin/python")
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


def test_allow_list_is_present_and_bash_scoped() -> None:
    allow = _permissions()["allow"]
    assert len(allow) >= 60
    assert len(allow) == len(set(allow)), "duplicate allow rules"
    assert all(rule.startswith("Bash(") and rule.endswith(")") for rule in allow)


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
        if head in INTERPRETERS or head.startswith("python"):
            target = pattern[len(head) :].lstrip()
            assert target.startswith(("scripts/", "-m scripts.", "-m pytest ")), pattern


def test_no_ask_rule_shadows_an_allow_rule() -> None:
    # A matching ask rule outranks allow; in auto mode it prompts and in
    # headless dontAsk it denies, which would silently undo the allow list.
    assert not _permissions().get("ask")


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("git push origin HEAD:claude/impl-automode-allow", "allow"),
        ("git push -u origin HEAD", "allow"),
        ("git push origin --delete claude/impl-automode-allow", "allow"),
        ("gh pr merge 9030 --squash", "allow"),
        ("gh workflow run ci.yml --ref claude/x", "allow"),
        ("/home/ops/learn-ukrainian/.venv/bin/python -m pytest tests/ -q", "allow"),
        (".venv/bin/python -m scripts.fleet.capacity_pick --json", "allow"),
        ("npm run agents:deploy", "allow"),
        ("sudo systemctl restart caddy", "allow"),
        ("sudo caddy reload --config /etc/caddy/Caddyfile", "allow"),
        # deny wins even though an allow rule also matches each of these
        ("git push origin HEAD:main", "deny"),
        ("git push origin HEAD:main --force", "deny"),
        ("git push origin HEAD:refs/heads/main", "deny"),
        ("git push origin --delete main", "deny"),
        ("gh pr merge 9030 --admin --squash", "deny"),
        # never pre-approved: left to the classifier or a prompt
        ("gh api repos/learn-ukrainian/learn-ukrainian.github.io", None),
        ("gh repo delete learn-ukrainian/learn-ukrainian.github.io", None),
        ("/home/ops/learn-ukrainian/.venv/bin/python -c 'print(1)'", None),
        ("sudo rm -rf /var/tmp/lu", None),
        ("sudo bash -c id", None),
        ("git push --force origin claude/x", None),
    ],
)
def test_rule_precedence(command: str, expected: str | None) -> None:
    assert _decide(command) == expected


@pytest.mark.parametrize(
    "command",
    ["git push origin HEAD:main", "git push origin --delete main", "gh pr merge 1 --admin --squash"],
)
def test_denied_commands_are_also_allowed_so_precedence_is_exercised(command: str) -> None:
    allow = _bash_patterns(_permissions()["allow"])
    assert any(_matches(p, command) for p in allow), command
