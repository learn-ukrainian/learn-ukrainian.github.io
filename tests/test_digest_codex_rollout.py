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
    def test_prefers_newer_generic_jsonl_over_older_rollout(self) -> None:
        """Newer Claude/other jsonl beats an older Codex rollout-* (not name-first)."""
        root = Path(self._tmp()) / "sessions"
        generic = root / "other.jsonl"
        rollout = root / "2026" / "08" / "21" / "rollout-abc.jsonl"
        _write_jsonl(rollout, [{"text": "rollout blocked on review — stale Aug-21 Codex tail"}])
        _write_jsonl(generic, [{"text": "generic failed merge — newer Claude session jsonl"}])
        older = 1_724_220_000  # 2026-08-21-ish
        newer = older + 172_800
        os.utime(rollout, (older, older))
        os.utime(generic, (newer, newer))
        sources = digest.collect_sources([root], limit=1)
        self.assertEqual(sources, [generic])

    def test_rollout_name_is_mtime_tie_break_only(self) -> None:
        root = Path(self._tmp()) / "sessions"
        claude = root / "claude-session.jsonl"
        rollout = root / "rollout-abc.jsonl"
        _write_jsonl(claude, [{"text": "claude failed merge — same-mtime generic jsonl"}])
        _write_jsonl(rollout, [{"text": "rollout blocked on review — same-mtime Codex tail"}])
        stamp = 1_724_400_000
        os.utime(claude, (stamp, stamp))
        os.utime(rollout, (stamp, stamp))
        sources = digest.collect_sources([root], limit=1)
        self.assertEqual(sources, [rollout])

    def test_noise_filter_drops_agents_md_and_cold_start(self) -> None:
        lines = [
            '{"text":"Reading AGENTS.md before work"}',
            '{"text":"cursor_cold_start fetched /api/rules"}',
            '{"text":"pytest failed on digest filter"}',
        ]
        self.assertEqual(digest.extract_snippets(lines), ["pytest failed on digest filter"])

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
                    "message": {
                        "content": [{"type": "text", "text": "lease expired; dispatch stuck"}]
                    },
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

    def test_default_roots_and_env_helpers(self) -> None:
        keys = ("DIGEST_LABEL", "DIGEST_ROOTS", "DIGEST_REPO", "DIGEST_MAX")
        old = {key: os.environ.pop(key, None) for key in keys}
        try:
            self.assertEqual(digest.env_label(), "local")
            self.assertEqual(digest.env_max(), 12)
            self.assertEqual(digest.env_repo(), Path.home() / "projects" / "learn-ukrainian")
            self.assertEqual(
                digest.env_roots(),
                [
                    Path.home() / ".codex" / "sessions",
                    Path.home() / ".claude" / "projects",
                    Path.home() / ".gemini" / "tmp",
                    Path.home() / ".config" / "gemini",
                ],
            )
        finally:
            for key, value in old.items():
                if value is not None:
                    os.environ[key] = value

    def _tmp(self) -> str:
        import tempfile

        handle = tempfile.TemporaryDirectory()
        self.addCleanup(handle.cleanup)
        return handle.name


if __name__ == "__main__":
    unittest.main()
