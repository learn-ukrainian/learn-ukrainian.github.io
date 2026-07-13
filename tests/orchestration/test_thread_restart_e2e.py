"""End-to-end acceptance for packet-only Codex thread replacement.

These tests deliberately cross subprocess, Git-worktree, shell-helper, hook,
and strict-canary seams. Unit-level state-machine cases remain in
``test_thread_handoff.py``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_PYTHON = REPO_ROOT / ".venv/bin/python"
HANDOFF = REPO_ROOT / "scripts/orchestration/thread_handoff.py"
HANDOFF_CANARY = REPO_ROOT / "scripts/orchestration/thread_handoff_canary.py"
CONTEXT_CANARY = REPO_ROOT / "scripts/context_canary.py"


def run(
    args: list[str | Path],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    command_env = (os.environ if env is None else env).copy()
    for key in tuple(command_env):
        if key.startswith("GIT_"):
            command_env.pop(key)
    completed = subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        env=command_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"command failed ({completed.returncode}): {' '.join(map(str, args))}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd, check=check)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def init_repo(tmp_path: Path, *, bootstrap_sources: bool = False) -> tuple[Path, Path]:
    primary = tmp_path / "canonical"
    replacement = tmp_path / "replacement"
    primary.mkdir(parents=True)
    git(primary, "init", "-b", "main")
    git(primary, "config", "user.email", "e2e@example.invalid")
    git(primary, "config", "user.name", "Thread Restart E2E")
    (primary / ".gitignore").write_text(
        ".agent/\n.codex/\n.claude/\n.agents/\n.gemini/\n.venv\n__pycache__/\n",
        encoding="utf-8",
    )
    (primary / "tracked.txt").write_text("canonical\n", encoding="utf-8")
    sources = [
        "scripts/__init__.py",
        "scripts/context_canary.py",
        "scripts/orchestration/thread_handoff.py",
        "scripts/orchestration/thread_handoff_canary.py",
    ]
    if bootstrap_sources:
        sources.extend(
            [
                "scripts/lib/thread_rollover_link.sh",
                "scripts/lib/deploy_extensions.sh",
                "agents_extensions/codex/hooks.json",
                "agents_extensions/shared/hooks/session-setup.sh",
            ]
        )
        (primary / "package.json").write_text(
            '{"scripts":{"agents:deploy":"scripts/deploy_prompts.sh"}}\n',
            encoding="utf-8",
        )
    for relative in sources:
        target = primary / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)
    git(primary, "add", ".")
    git(primary, "commit", "-m", "test fixture")
    (primary / ".venv").symlink_to(REPO_ROOT / ".venv", target_is_directory=True)
    git(primary, "worktree", "add", "-b", "replacement", str(replacement), "HEAD")
    return primary, replacement


def handoff_command(primary: Path, *args: str) -> list[str | Path]:
    return [
        REPO_PYTHON,
        HANDOFF,
        "--repo-root",
        primary,
        "--monitor-base-url",
        "http://127.0.0.1:1",
        *args,
    ]


def checkout_handoff_command(checkout: Path, *args: str) -> list[str | Path]:
    return [
        checkout / ".venv/bin/python",
        checkout / "scripts/orchestration/thread_handoff.py",
        "--monitor-base-url",
        "http://127.0.0.1:1",
        *args,
    ]


def prepare(primary: Path, *, active_thread_id: str = "old-thread") -> dict:
    completed = run(
        handoff_command(
            primary,
            "prepare",
            "--agent",
            "codex",
            "--active-thread-id",
            active_thread_id,
            "--active-automation-id",
            f"automation-{active_thread_id}",
        ),
        cwd=primary,
        check=True,
    )
    return json.loads(completed.stdout)


def load_lease(primary: Path, packet: dict) -> dict:
    return json.loads((primary / packet["state_file"]).read_text(encoding="utf-8"))


def assert_cleanup_locked(primary: Path, packet: dict) -> None:
    assert load_lease(primary, packet)["cleanup"]["old_automation_ready_to_delete"] is False


def resume(primary: Path, packet: dict, replacement_thread_id: str = "fresh-thread") -> dict:
    completed = run(
        handoff_command(
            primary,
            "resume",
            "--agent",
            "codex",
            "--lineage-id",
            packet["lineage_id"],
            "--rollover-id",
            packet["rollover_id"],
            "--replacement-thread-id",
            replacement_thread_id,
        ),
        cwd=primary,
        check=True,
    )
    return json.loads(completed.stdout)


def semantic_snapshot(lease: dict) -> dict:
    replacement = lease["replacement"]
    handoff_ref = replacement["handoff_path"]
    return {
        "generated_at": "2026-07-13T12:00:00Z",
        "lineage_id": lease["lineage_id"],
        "rollover_id": replacement["rollover_id"],
        "seed": 5057,
        "goals": [
            {
                "id": f"goal-{index}",
                "statement": f"continue durable goal {index}",
                "source_ref": f"handoff:{handoff_ref}#goal-{index}",
            }
            for index in range(3)
        ],
        "decision_records": [
            {
                "id": f"decision-{index}",
                "decision": f"keep packet decision {index}",
                "source_ref": f"decision:docs/decisions/thread-restart.md#decision-{index}",
            }
            for index in range(3)
        ],
        "constraint_records": [
            {
                "id": f"constraint-{index}",
                "prohibition": f"never transfer provider history {index}",
                "source_ref": f"handoff:{handoff_ref}#constraint-{index}",
            }
            for index in range(2)
        ],
        "next_actions": [
            {
                "id": f"action-{index}",
                "action": f"execute durable action {index}",
                "source_ref": f"queue:batch_state/orchestrator-runs/epic-5054-thread-continuity.json#action-{index}",
            }
            for index in range(2)
        ],
    }


def strict_evidence(primary: Path, packet: dict, *, wrong_answer: bool = False) -> tuple[Path, Path, Path]:
    lease = load_lease(primary, packet)
    replacement = lease["replacement"]
    snapshot_path = primary / replacement["semantic_snapshot_path"]
    probe_path = primary / replacement["strict_probe_path"]
    questions_path = primary / replacement["strict_questions_path"]
    answers_path = primary / replacement["strict_answers_path"]
    verdict_path = primary / replacement["strict_verdict_path"]
    snapshot = semantic_snapshot(lease)
    write_json(snapshot_path, snapshot)
    minted = run(
        [REPO_PYTHON, CONTEXT_CANARY, "mint", "--snapshot", snapshot_path, "--out", probe_path],
        cwd=primary,
        check=True,
    )
    assert "minted 10 anchors" in minted.stdout
    run(
        [REPO_PYTHON, CONTEXT_CANARY, "questions", "--probe", probe_path, "--out", questions_path],
        cwd=primary,
        check=True,
    )
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    questions = json.loads(questions_path.read_text(encoding="utf-8"))["questions"]
    assert len(questions) == 10
    assert all(set(question) == {"id", "q"} for question in questions)
    assert {question["id"] for question in questions} == {anchor["id"] for anchor in probe["anchors"]}
    snapshot_text = snapshot_path.read_text(encoding="utf-8")
    assert all(str(anchor["a"]) in snapshot_text for anchor in probe["anchors"])
    answers = {anchor["id"]: anchor["a"] for anchor in probe["anchors"]}
    if wrong_answer:
        answers[probe["anchors"][-1]["id"]] = "wrong answer"
    write_json(answers_path, answers)
    scored = run(
        [
            REPO_PYTHON,
            CONTEXT_CANARY,
            "score",
            "--probe",
            probe_path,
            "--answers",
            answers_path,
            "--expected-lineage-id",
            packet["lineage_id"],
            "--expected-rollover-id",
            packet["rollover_id"],
            "--verdict",
            verdict_path,
        ],
        cwd=primary,
    )
    expected_score = "SCORE 9/10" if wrong_answer else "SCORE 10/10"
    assert expected_score in scored.stdout
    assert scored.returncode == (2 if wrong_answer else 0)
    return probe_path, verdict_path, questions_path


def canary_proof(primary: Path, packet: dict, *, challenge: str | None = None) -> Path:
    lease = load_lease(primary, packet)
    replacement = lease["replacement"]
    proof_path = primary / replacement["canary_proof_path"]
    run(
        [
            REPO_PYTHON,
            HANDOFF_CANARY,
            "--rollover-id",
            packet["rollover_id"],
            "--replacement-thread-id",
            "fresh-thread",
            "--challenge",
            challenge or replacement["canary_challenge"],
            "--proof-file",
            proof_path,
        ],
        cwd=primary,
        check=True,
    )
    return proof_path


def confirm_command(
    primary: Path,
    packet: dict,
    *,
    proof: Path,
    probe: Path,
    verdict: Path,
) -> list[str | Path]:
    return handoff_command(
        primary,
        "confirm-started",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--new-thread-id",
        "fresh-thread",
        "--canary-proof",
        str(proof),
        "--strict-probe",
        str(probe),
        "--strict-verdict",
        str(verdict),
    )


def test_packet_only_lifecycle_answers_exactly_ten_questions_and_unlocks_cleanup(tmp_path: Path) -> None:
    primary, _ = init_repo(tmp_path)
    packet = prepare(primary)
    assert_cleanup_locked(primary, packet)
    lease = load_lease(primary, packet)
    assert lease["replacement"]["source_checkout"] == {
        "full_head": git(primary, "rev-parse", "HEAD").stdout.strip(),
        "clean": True,
    }
    runtime = primary / packet["runtime_path"]
    bootstrap = (runtime / "bootstrap.md").read_text(encoding="utf-8")
    assert "do not fork, continue, or resume provider conversation history" in bootstrap
    assert "thread_handoff.py resume" in bootstrap
    assert "thread_handoff_canary.py" in bootstrap
    assert "thread_handoff.py confirm-started" in bootstrap
    assert "codex exec resume" not in bootstrap
    assert not list(primary.glob(".agent/**/*state_5.sqlite"))
    assert not list(primary.glob(".agent/**/*.jsonl"))

    resumed = resume(primary, packet)
    assert resumed["replacement_thread_id"] == "fresh-thread"
    assert resumed["replacement_thread_id"] != "old-thread"
    validated = run(
        handoff_command(
            primary,
            "check",
            "--agent",
            "codex",
            "--lineage-id",
            packet["lineage_id"],
        ),
        cwd=primary,
        check=True,
    )
    assert json.loads(validated.stdout)["warnings"] == []
    probe, verdict, questions = strict_evidence(primary, packet)
    assert len(json.loads(questions.read_text(encoding="utf-8"))["questions"]) == 10
    proof = canary_proof(primary, packet)
    confirmed = run(
        confirm_command(primary, packet, proof=proof, probe=probe, verdict=verdict),
        cwd=primary,
        check=True,
    )
    result = json.loads(confirmed.stdout)
    assert result["replacement_status"] == "started"
    assert result["old_automation_ready_to_delete"] is True
    assert load_lease(primary, packet)["cleanup"]["old_automation_ready_to_delete"] is True
    assert git(primary, "status", "--short", "--untracked-files=all").stdout == ""


@pytest.mark.parametrize("case", ["second-prepare", "wrong-rollover", "missing-thread-id", "stale", "corrupt"])
def test_pre_confirmation_failures_leave_cleanup_locked(tmp_path: Path, case: str) -> None:
    primary, _ = init_repo(tmp_path)
    packet = prepare(primary)
    state_path = primary / packet["state_file"]

    if case == "second-prepare":
        failed = run(
            handoff_command(
                primary,
                "prepare",
                "--agent",
                "codex",
                "--active-thread-id",
                "old-thread",
            ),
            cwd=primary,
        )
    elif case == "wrong-rollover":
        failed = run(
            handoff_command(
                primary,
                "resume",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                "rollover-wrong",
                "--replacement-thread-id",
                "fresh-thread",
            ),
            cwd=primary,
        )
    elif case == "missing-thread-id":
        failed = run(
            handoff_command(
                primary,
                "resume",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                packet["rollover_id"],
            ),
            cwd=primary,
        )
    elif case == "stale":
        lease = load_lease(primary, packet)
        lease["replacement"]["prepared_at"] = "2000-01-01T00:00:00Z"
        write_json(state_path, lease)
        failed = run(
            handoff_command(
                primary,
                "check",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--stale-hours",
                "1",
            ),
            cwd=primary,
        )
    else:
        state_path.write_text('{"schema_version": 2, "broken"', encoding="utf-8")
        failed = run(
            handoff_command(primary, "detect", "--agent", "codex"),
            cwd=primary,
        )

    assert failed.returncode != 0
    if case == "corrupt":
        assert '"old_automation_ready_to_delete": true' not in state_path.read_text(encoding="utf-8")
    else:
        assert_cleanup_locked(primary, packet)


@pytest.mark.parametrize("case", ["nine-of-ten", "failed-canary"])
def test_failed_replacement_proofs_leave_cleanup_locked(tmp_path: Path, case: str) -> None:
    primary, _ = init_repo(tmp_path)
    packet = prepare(primary)
    resume(primary, packet)
    probe, verdict, _ = strict_evidence(primary, packet, wrong_answer=case == "nine-of-ten")
    proof = canary_proof(primary, packet, challenge="0" * 64 if case == "failed-canary" else None)
    failed = run(
        confirm_command(primary, packet, proof=proof, probe=probe, verdict=verdict),
        cwd=primary,
    )
    assert failed.returncode == 2
    assert_cleanup_locked(primary, packet)


def test_parallel_lineages_have_distinct_paths_and_reject_cross_claims(tmp_path: Path) -> None:
    primary, _ = init_repo(tmp_path)
    first = prepare(primary, active_thread_id="old-a")
    second = prepare(primary, active_thread_id="old-b")
    assert first["lineage_id"] != second["lineage_id"]
    assert first["rollover_id"] != second["rollover_id"]
    assert first["state_file"] != second["state_file"]
    assert first["runtime_path"] != second["runtime_path"]

    crossed = run(
        handoff_command(
            primary,
            "resume",
            "--agent",
            "codex",
            "--lineage-id",
            first["lineage_id"],
            "--rollover-id",
            second["rollover_id"],
            "--replacement-thread-id",
            "cross-claim",
        ),
        cwd=primary,
    )
    assert crossed.returncode == 2
    assert_cleanup_locked(primary, first)
    assert_cleanup_locked(primary, second)


def test_monitor_outage_and_dirty_replacement_never_unlock_cleanup(tmp_path: Path) -> None:
    primary, replacement = init_repo(tmp_path)
    (replacement / ".venv").symlink_to(primary / ".venv", target_is_directory=True)
    prepared = run(
        checkout_handoff_command(
            primary,
            "prepare",
            "--agent",
            "codex",
            "--active-thread-id",
            "old-thread",
            "--active-automation-id",
            "automation-old-thread",
        ),
        cwd=primary,
        check=True,
    )
    packet = json.loads(prepared.stdout)
    resumed = run(
        checkout_handoff_command(
            replacement,
            "resume",
            "--agent",
            "codex",
            "--lineage-id",
            packet["lineage_id"],
            "--rollover-id",
            packet["rollover_id"],
            "--replacement-thread-id",
            "fresh-thread",
        ),
        cwd=replacement,
        check=True,
    )
    assert json.loads(resumed.stdout)["status"] == "resumed"
    probe, verdict, _ = strict_evidence(primary, packet)
    proof = canary_proof(primary, packet)

    (replacement / "tracked.txt").write_text("dirty replacement\n", encoding="utf-8")
    assert git(replacement, "status", "--short").stdout.startswith(" M tracked.txt")
    assert_cleanup_locked(primary, packet)
    rejected = run(
        checkout_handoff_command(
            replacement,
            "confirm-started",
            "--agent",
            "codex",
            "--lineage-id",
            packet["lineage_id"],
            "--rollover-id",
            packet["rollover_id"],
            "--new-thread-id",
            "fresh-thread",
            "--canary-proof",
            str(proof),
            "--strict-probe",
            str(probe),
            "--strict-verdict",
            str(verdict),
        ),
        cwd=replacement,
    )
    assert rejected.returncode == 2
    error = json.loads(rejected.stdout)["error"]
    assert "checkout continuity failed: invoking checkout must be clean" in error
    assert "tracked.txt" in error
    lease = load_lease(primary, packet)
    assert lease["replacement"]["status"] == "resumed"
    assert_cleanup_locked(primary, packet)


def test_app_style_worktree_bootstrap_deploys_hook_and_discovers_canonical_packet(tmp_path: Path) -> None:
    primary, replacement = init_repo(tmp_path, bootstrap_sources=True)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_npm = fake_bin / "npm"
    fake_npm.write_text(
        "#!/bin/bash\n"
        "set -e\n"
        "mkdir -p .codex/hooks\n"
        "cp agents_extensions/codex/hooks.json .codex/hooks.json\n"
        "cp agents_extensions/shared/hooks/session-setup.sh .codex/hooks/session-setup.sh\n",
        encoding="utf-8",
    )
    fake_npm.chmod(0o755)
    fake_gh = fake_bin / "gh"
    fake_gh.write_text("#!/bin/bash\nexit 1\n", encoding="utf-8")
    fake_gh.chmod(0o755)
    jq = shutil.which("jq")
    assert jq is not None
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{Path(jq).parent}:/usr/bin:/bin"

    for _ in range(2):
        bootstrapped = run(
            ["bash", replacement / "scripts/lib/thread_rollover_link.sh", primary, replacement],
            cwd=replacement,
            env=env,
        )
        assert bootstrapped.returncode == 0, bootstrapped.stderr
    assert (replacement / ".venv").is_symlink()
    rollover_link = replacement / ".agent/thread-rollovers"
    assert rollover_link.is_symlink()
    assert rollover_link.resolve() == (primary / ".agent/thread-rollovers").resolve()
    assert (replacement / ".codex/hooks.json").is_file()
    deployed_hook = replacement / ".codex/hooks/session-setup.sh"
    assert deployed_hook.is_file()

    packet = prepare(primary)
    hook_env = env.copy()
    hook_env.update(
        {
            "HOME": str(tmp_path / "home"),
            "PYENV_ROOT": str(tmp_path / "pyenv"),
            "CLAUDE_PROJECT_DIR": str(replacement),
            "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS": "32000",
            "SESSION_HANDOFF_AGENT": "codex",
            "CODEX_THREAD_ID": "fresh-app-thread",
            "THREAD_ROLLOVER_PYTHON": str(REPO_PYTHON),
            "THREAD_ROLLOVER_SCRIPT": str(HANDOFF),
        }
    )
    hook_env.pop("CODEX_CANONICAL_REPO_ROOT", None)
    started = run(["bash", deployed_hook], cwd=replacement, env=hook_env)
    assert started.returncode == 0, started.stderr
    assert "PENDING THREAD ROLLOVER DETECTED" in started.stdout
    assert packet["lineage_id"] in started.stdout
    assert packet["rollover_id"] in started.stdout
    assert "--replacement-thread-id fresh-app-thread" in started.stdout
    assert_cleanup_locked(primary, packet)
    assert git(replacement, "status", "--short", "--untracked-files=all").stdout == ""
