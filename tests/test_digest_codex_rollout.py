"""Tests for the token-cheap fleet session digester."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "scripts" / "ops" / "digest_codex_rollout.py"

spec = importlib.util.spec_from_file_location("digest_codex_rollout_under_test", MODULE_PATH)
assert spec and spec.loader
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)


def _write_jsonl(path: Path, rows: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for row in rows:
        if isinstance(row, str):
            lines.append(row)
        else:
            lines.append(json.dumps(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class DigestCodexRolloutTests(unittest.TestCase):
    def test_redacts_ip_and_user_host(self) -> None:
        text = digest.redact_opsec("blocked ssh deploy@internal-node on 203.0.113.50")
        self.assertNotIn("203.0.113.50", text)
        self.assertNotIn("deploy@internal-node", text)
        self.assertIn("[redacted-ip]", text)
        self.assertTrue("[redacted-host]" in text or "[redacted-ssh]" in text)

    def test_write_digest_and_index(self) -> None:
        tmp = Path(self._tmp())
        root = tmp / "codex"
        repo = tmp / "repo"
        rollout = root / "sessions" / "rollout-watch.jsonl"
        _write_jsonl(
            rollout,
            [
                {
                    "type": "assistant",
                    "message": {"content": [{"type": "text", "text": "lease expired; dispatch stuck"}]},
                },
                {"text": "Loading CLAUDE.md and MEMORY.md"},
            ],
        )
        env = {
            "DIGEST_LABEL": "watchdesk",
            "DIGEST_ROOTS": str(root),
            "DIGEST_REPO": str(repo),
            "DIGEST_MAX": "12",
        }
        old = {key: os.environ.get(key) for key in env}
        os.environ.update(env)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(digest.main(), 0)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        latest = repo / "logs" / "agent-digests" / "watchdesk-latest.md"
        out = buf.getvalue().strip().splitlines()
        self.assertEqual(out[0], str(latest))
        self.assertEqual(out[1], f"bytes={latest.stat().st_size} sources=1 label=watchdesk")

        body = latest.read_text(encoding="utf-8")
        self.assertIn("lease expired; dispatch stuck", body)
        self.assertNotIn("CLAUDE.md", body)
        self.assertIn("keyword extract (no LLM)", body)

        index = (repo / "logs" / "agent-digests" / "index.md").read_text(encoding="utf-8")
        self.assertIn("watchdesk", index)
        self.assertIn("watchdesk-latest.md", index)

        home_dir = tmp / "homes"
        account_a = home_dir / "a"
        account_b = home_dir / "bound-account"
        (account_a / ".codex" / "sessions" / "2026" / "11").mkdir(parents=True)
        (account_b / "sessions" / "2026" / "11").mkdir(parents=True)
        account_b.chmod(0o700)
        accounts = tmp / "codex_accounts.json"
        accounts.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "accounts": {"b-sub": {"codex_home": str(account_b), "budget_usd": 1}},
                }
            ),
            encoding="utf-8",
        )
        accounts.chmod(0o600)
        material = '{"text": "dispatch stuck while the lease expired and review could not merge"}\n'
        (account_a / ".codex" / "sessions" / "2026" / "11" / "rollout-a.jsonl").write_text(material, encoding="utf-8")
        (account_b / "sessions" / "2026" / "11" / "rollout-b.jsonl").write_text(material, encoding="utf-8")
        repo_b = tmp / "repo-b"
        saved = {
            key: os.environ.get(key)
            for key in ("HOME", "LU_CODEX_ACCOUNTS_FILE", "DIGEST_ROOTS", "DIGEST_LABEL", "DIGEST_REPO", "DIGEST_MAX")
        }
        os.environ.pop("DIGEST_ROOTS", None)
        os.environ["HOME"] = str(account_a)
        os.environ["LU_CODEX_ACCOUNTS_FILE"] = str(accounts)
        os.environ["DIGEST_LABEL"] = "local"
        os.environ["DIGEST_REPO"] = str(repo_b)
        os.environ["DIGEST_MAX"] = "12"
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(digest.main(), 0)
            body = (repo_b / "logs" / "agent-digests" / "local-latest.md").read_text(encoding="utf-8")
            self.assertIn("## codex:b/rollout-b.jsonl", body)
            self.assertIn("rollout-a.jsonl", body)
            self.assertNotIn("## codex:b/rollout-a.jsonl", body)
            self.assertNotIn("bound-account", body)
            self.assertNotIn(str(account_a), body)
            self.assertNotIn(str(account_b), body)
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _tmp(self) -> str:
        import tempfile

        handle = tempfile.TemporaryDirectory()
        self.addCleanup(handle.cleanup)
        return handle.name


if __name__ == "__main__":
    unittest.main()
