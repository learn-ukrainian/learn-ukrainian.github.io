"""Earlier review rounds are removed when the next round is dispatched."""

from __future__ import annotations

from pathlib import Path

import scripts.delegate as delegate


def test_review_series_round_numbers() -> None:
    assert delegate._review_series("review-gpt6-routing") == ("review-gpt6-routing", 0)
    assert delegate._review_series("review-gpt6-routing-r7") == ("review-gpt6-routing", 7)
    assert delegate._review_series("review-8340-cf-r10") == ("review-8340-cf", 10)
    assert delegate._review_series("impl-8414") is None


def test_later_round_removes_only_earlier_clean_rounds(monkeypatch, tmp_path: Path) -> None:
    earlier = tmp_path / "codex" / "review-topic-r2"
    same = tmp_path / "agy" / "review-topic-r4"
    other = tmp_path / "codex" / "review-other-r1"
    removed: list[str] = []

    monkeypatch.setattr(
        delegate,
        "_dispatch_worktree_components",
        lambda: [(earlier, "review-topic-r2"), (same, "review-topic-r4"), (other, "review-other-r1")],
    )
    monkeypatch.setattr(delegate, "_superseded_review_releasable", lambda _path: (True, "clean; task status=done"))

    def fake_run(cmd, **_kwargs):
        removed.append(cmd[-1])

        class Proc:
            returncode = 0
            stdout = ""
            stderr = ""

        return Proc()

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    released = delegate._release_superseded_review_worktrees("review-topic-r4", dry_run=False)

    assert released == [earlier]
    assert removed == [str(earlier)]
