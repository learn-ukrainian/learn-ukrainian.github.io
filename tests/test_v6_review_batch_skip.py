"""Regression tests for batch review reruns below the 9.0 target."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build.orch_index as orch_index
import build.v6_build as v6_build


def _write_manifest(curriculum_root: Path, slugs: list[str]) -> None:
    curriculum_root.mkdir(parents=True, exist_ok=True)
    manifest = curriculum_root / "curriculum.yaml"
    manifest.write_text(
        "levels:\n"
        "  b1:\n"
        "    modules:\n"
        + "".join(f"      - {slug}\n" for slug in slugs),
        "utf-8",
    )


def _write_state(curriculum_root: Path, slug: str, *, review_complete: bool, all_complete: bool = False) -> None:
    phases = {}
    if all_complete:
        for phase in v6_build._ALL_PHASES:
            phases[phase] = {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}
    elif review_complete:
        phases["review"] = {"status": "complete", "ts": "2026-04-10T00:00:00+00:00"}

    orch_dir = curriculum_root / "b1" / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "state.json").write_text(
        json.dumps({"mode": "v6", "track": "b1", "slug": slug, "phases": phases}, indent=2),
        "utf-8",
    )


def _write_review(curriculum_root: Path, slug: str, score: float, verdict: str = "PASS") -> None:
    review_dir = curriculum_root / "b1" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| {i}. Dimension {i} | {score}/10 | Strong evidence |"
        for i in range(1, 10)
    )
    review_text = (
        "## Scores\n"
        "| Dimension | Score | Evidence |\n"
        "|-----------|-------|----------|\n"
        f"{rows}\n\n"
        f"## Verdict: {verdict}\n"
    )
    (review_dir / f"{slug}-review.md").write_text(review_text, "utf-8")


def _write_review_with_dimension_scores(
    curriculum_root: Path, slug: str, scores: list[int], verdict: str = "PASS",
) -> None:
    review_dir = curriculum_root / "b1" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| {i}. Dimension {i} | {score}/10 | Strong evidence |"
        for i, score in enumerate(scores, start=1)
    )
    review_text = (
        "## Scores\n"
        "| Dimension | Score | Evidence |\n"
        "|-----------|-------|----------|\n"
        f"{rows}\n\n"
        f"## Verdict: {verdict}\n"
    )
    (review_dir / f"{slug}-review.md").write_text(review_text, "utf-8")


class TestBatchReviewSkip:
    def test_batch_review_reruns_low_scores_and_skips_passing(self, tmp_path, monkeypatch):
        curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
        _write_manifest(curriculum_root, ["rerun-me", "skip-me"])
        _write_state(curriculum_root, "rerun-me", review_complete=True)
        _write_state(curriculum_root, "skip-me", review_complete=True)
        _write_review(curriculum_root, "rerun-me", 8)
        _write_review(curriculum_root, "skip-me", 9)

        monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
        monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

        calls: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            sys,
            "argv",
            ["v6_build.py", "b1", "1", "--range", "2", "--step", "review"],
        )

        with pytest.raises(SystemExit) as exc:
            v6_build.main()

        assert exc.value.code == 0
        assert len(calls) == 1
        assert calls[0][0] == str(tmp_path / ".venv" / "bin" / "python")
        assert calls[0][3] == "1"
        assert "--review-threshold" in calls[0]

    def test_batch_review_uses_custom_threshold_for_skip(self, tmp_path, monkeypatch):
        curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
        _write_manifest(curriculum_root, ["threshold-module"])
        _write_state(curriculum_root, "threshold-module", review_complete=True)
        _write_review_with_dimension_scores(
            curriculum_root, "threshold-module", [9, 8, 8, 8, 8, 8, 8, 8, 8],
        )

        monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
        monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

        calls: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "v6_build.py", "b1", "1", "--range", "1", "--step", "review",
                "--review-threshold", "8.0",
            ],
        )

        with pytest.raises(SystemExit) as exc:
            v6_build.main()

        assert exc.value.code == 0
        assert calls == []

    def test_batch_review_reruns_when_review_file_is_missing(self, tmp_path, monkeypatch):
        curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
        _write_manifest(curriculum_root, ["missing-review"])
        _write_state(curriculum_root, "missing-review", review_complete=True)

        monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
        monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

        calls: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            sys,
            "argv",
            ["v6_build.py", "b1", "1", "--range", "1", "--step", "review"],
        )

        with pytest.raises(SystemExit) as exc:
            v6_build.main()

        assert exc.value.code == 0
        assert len(calls) == 1
        assert calls[0][3] == "1"

    def test_non_review_batch_step_skips_only_fully_passing_modules(self, tmp_path, monkeypatch):
        """Under the stricter 2026-04-10 rule, a module is skipped only when:

            phases complete + fresh audit pass (every gate == 'pass') +
            review score >= threshold

        This test sets up TWO modules:
            - needs-write: phases NOT complete → must build
            - already-done: phases complete + fresh passing status.json
              + review score 10 → must be skipped

        Previously the test expected that all-phases-complete was
        sufficient to skip, which let modules with stale / missing audit
        caches slip through without verification.
        """
        curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
        _write_manifest(curriculum_root, ["needs-write", "already-done"])
        _write_state(curriculum_root, "needs-write", review_complete=True)
        _write_state(curriculum_root, "already-done", review_complete=True, all_complete=True)

        # Fresh audit status with ALL gates strictly passing
        # (strictly "pass", not "info" — the new rule rejects info).
        status_dir = curriculum_root / "b1" / "status"
        status_dir.mkdir(parents=True, exist_ok=True)
        (status_dir / "already-done.json").write_text(
            json.dumps({
                "overall": {"status": "pass"},
                "gates": {
                    "meta": {"status": "pass"},
                    "lesson": {"status": "pass"},
                    "activities": {"status": "pass"},
                    "vocabulary": {"status": "pass"},
                    "naturalness": {"status": "pass"},
                    "research": {"status": "pass"},
                    "review": {"status": "pass"},
                },
            }),
            "utf-8",
        )
        # Review score 10/10 clears the default threshold (9.0).
        _write_review(curriculum_root, "already-done", 10)
        # Content file + mtimes ordered so staleness check won't trip:
        # status.json must be newer than content AND newer than audit engine.
        (curriculum_root / "b1").mkdir(parents=True, exist_ok=True)
        content_path = curriculum_root / "b1" / "already-done.md"
        content_path.write_text("# Done\n", "utf-8")
        # Force status mtime into the future so no audit-engine update
        # can make it look stale. (The real audit engine lives outside
        # the tmp path; its mtime is fixed as of the last `git pull`.)
        import os
        import time
        future = time.time() + 3600
        os.utime(status_dir / "already-done.json", (future, future))

        monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
        monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

        calls: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            sys,
            "argv",
            ["v6_build.py", "b1", "1", "--range", "2", "--step", "write", "--skeleton"],
        )

        with pytest.raises(SystemExit) as exc:
            v6_build.main()

        assert exc.value.code == 0
        assert len(calls) == 1, f"expected only needs-write to build, got {len(calls)} calls"
        assert calls[0][3] == "1"
        assert "--skeleton" in calls[0]


    def test_non_review_batch_step_reruns_stale_cache(self, tmp_path, monkeypatch):
        """A module with all phases complete but a STALE status.json must
        be re-built, not skipped. Stale = status.json older than the
        audit engine (simulated here by giving status.json a very old mtime).

        This is the primary regression the 2026-04-10 rule was written to
        catch: the A1 M02 skip where the salad detector had been added to
        the audit engine AFTER the last time the module's status was
        written. The stale status said pass; the salad detector would
        have caught the inline-gloss overflow.
        """
        curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
        _write_manifest(curriculum_root, ["stale-cache"])
        _write_state(curriculum_root, "stale-cache", review_complete=True, all_complete=True)
        _write_review(curriculum_root, "stale-cache", 10)

        status_dir = curriculum_root / "b1" / "status"
        status_dir.mkdir(parents=True, exist_ok=True)
        status_path = status_dir / "stale-cache.json"
        status_path.write_text(
            json.dumps({
                "overall": {"status": "pass"},
                "gates": {"meta": {"status": "pass"}, "lesson": {"status": "pass"}},
            }),
            "utf-8",
        )
        # Give the status file an ANCIENT mtime so it's stale vs any
        # file in scripts/audit/ (which is the real audit engine).
        import os
        old = 1_000_000  # ~1970-01-12, well before any repo file
        os.utime(status_path, (old, old))

        monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
        monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

        calls: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            sys,
            "argv",
            ["v6_build.py", "b1", "1", "--range", "1", "--step", "write", "--skeleton"],
        )

        with pytest.raises(SystemExit) as exc:
            v6_build.main()

        assert exc.value.code == 0
        # Stale cache → module must be rebuilt, not skipped.
        assert len(calls) == 1, f"stale module should rebuild, got {len(calls)} calls"
        assert calls[0][3] == "1"


    def test_non_review_batch_step_reruns_unverified_gate(self, tmp_path, monkeypatch):
        """A module with overall=pass but a gate in 'info'/'pending' state
        must NOT be skipped. The new rule treats any non-'pass' gate as
        unverified and forces a rerun, even if the rollup says pass.

        This catches the a1 M02 bug where naturalness='info' rolled up
        to overall='pass' because compute_overall_status only counts
        fails, not non-passes.
        """
        curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
        _write_manifest(curriculum_root, ["info-gate"])
        _write_state(curriculum_root, "info-gate", review_complete=True, all_complete=True)
        _write_review(curriculum_root, "info-gate", 10)

        status_dir = curriculum_root / "b1" / "status"
        status_dir.mkdir(parents=True, exist_ok=True)
        (status_dir / "info-gate.json").write_text(
            json.dumps({
                "overall": {"status": "pass"},
                "gates": {
                    "meta": {"status": "pass"},
                    "lesson": {"status": "pass"},
                    "activities": {"status": "pass"},
                    "naturalness": {"status": "info"},  # ← unverified
                },
            }),
            "utf-8",
        )
        (curriculum_root / "b1").mkdir(parents=True, exist_ok=True)
        (curriculum_root / "b1" / "info-gate.md").write_text("# X\n", "utf-8")
        import os
        import time
        future = time.time() + 3600
        os.utime(status_dir / "info-gate.json", (future, future))

        monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
        monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

        calls: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            sys,
            "argv",
            ["v6_build.py", "b1", "1", "--range", "1", "--step", "write", "--skeleton"],
        )

        with pytest.raises(SystemExit) as exc:
            v6_build.main()

        assert exc.value.code == 0
        # Unverified gate → must rebuild.
        assert len(calls) == 1, (
            f"module with info gate should rebuild, got {len(calls)} calls"
        )
        assert calls[0][3] == "1"

    def test_single_module_review_still_runs_when_review_phase_is_complete(self, tmp_path, monkeypatch):
        curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
        _write_manifest(curriculum_root, ["single-module"])
        _write_state(curriculum_root, "single-module", review_complete=True)
        (curriculum_root / "b1").mkdir(parents=True, exist_ok=True)
        (curriculum_root / "b1" / "single-module.md").write_text("# Content\n", "utf-8")

        monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
        monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
        monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
        monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: (True, 9.0, "## Verdict: PASS\n"))
        monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: None)
        monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)

        calls: list[tuple] = []

        def track_step_review(*args, **kwargs):
            calls.append((args, kwargs))
            return True, 9.0, "## Verdict: PASS\n"

        monkeypatch.setattr(v6_build, "step_review", track_step_review)
        monkeypatch.setattr(
            sys,
            "argv",
            ["v6_build.py", "b1", "1", "--step", "review"],
        )

        v6_build.main()

        assert len(calls) == 1
