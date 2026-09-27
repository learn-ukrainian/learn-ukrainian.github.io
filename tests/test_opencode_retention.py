"""OpenCode retention behavior with an isolated fake CLI on PATH."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/orchestration/opencode_session_retention.py"


def _environment(tmp_path: Path, sessions: list[dict[str, object]]) -> tuple[dict[str, str], Path]:
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    opencode = binary_dir / "opencode"
    opencode.write_text('#!/bin/sh\nexec "$FAKE_PYTHON" "$FAKE_SCRIPT" "$@"\n', encoding="utf-8")
    opencode.chmod(0o755)
    pgrep = binary_dir / "pgrep"
    pgrep.write_text('#!/bin/sh\n[ "$FAKE_RUNNING" = "1" ]\n', encoding="utf-8")
    pgrep.chmod(0o755)
    fake_script = tmp_path / "fake_opencode.py"
    fake_script.write_text(
        """import json, os, sys
from pathlib import Path
args = sys.argv[1:]
state = Path(os.environ['FAKE_STATE'])
database = Path(os.environ['FAKE_DB'])
log = Path(os.environ['FAKE_LOG'])
with log.open('a', encoding='utf-8') as out:
    out.write(' '.join(args) + '\\n')
if args[:2] == ['db', 'path']:
    print(database)
elif args[:2] == ['db', 'SELECT id, parent_id AS parent, time_updated AS updated FROM session ORDER BY time_updated ASC']:
    print(state.read_text(encoding='utf-8'))
elif args[:2] == ['session', 'delete']:
    rows = json.loads(state.read_text(encoding='utf-8'))
    removed = {args[2]}
    while True:
        next_removed = removed | {row['id'] for row in rows if row.get('parent') in removed}
        if next_removed == removed:
            break
        removed = next_removed
    rows = [row for row in rows if row['id'] not in removed]
    state.write_text(json.dumps(rows), encoding='utf-8')
    if os.environ.get('FAKE_RECLAIM') == '1':
        database.write_bytes(database.read_bytes()[:512])
elif args[:2] == ['db', 'PRAGMA wal_checkpoint(TRUNCATE)']:
    Path(str(database) + '-wal').write_bytes(b'')
    print('[{"busy":0,"log":0,"checkpointed":0}]')
elif args[:1] == ['db'] and args[1] in (
    'PRAGMA freelist_count', 'PRAGMA page_count', 'PRAGMA page_size'
):
    name = args[1].split()[1]
    value = {
        'freelist_count': int(os.environ['FAKE_INITIAL_COUNT']) - len(json.loads(state.read_text(encoding='utf-8'))),
        'page_count': 8,
        'page_size': 4096,
    }[name]
    print(json.dumps([{name: value}]))
else:
    sys.exit(3)
""",
        encoding="utf-8",
    )
    state = tmp_path / "sessions.json"
    state.write_text(json.dumps(sessions), encoding="utf-8")
    database = tmp_path / "opencode.db"
    database.write_bytes(b"x" * 2048)
    Path(f"{database}-wal").write_bytes(b"w" * 1024)
    log = tmp_path / "calls.log"
    env = os.environ.copy()
    env.update(
        PATH=f"{binary_dir}:{env.get('PATH', '')}",
        FAKE_PYTHON=sys.executable,
        FAKE_SCRIPT=str(fake_script),
        FAKE_STATE=str(state),
        FAKE_DB=str(database),
        FAKE_LOG=str(log),
        FAKE_RUNNING="0",
        FAKE_RECLAIM="1",
        FAKE_INITIAL_COUNT=str(len(sessions)),
    )
    return env, log


def _invoke(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True, check=False, timeout=60
    )


def test_opencode_retention_dry_run_and_apply_select_only_old_sessions(tmp_path: Path) -> None:
    now = int(time.time() * 1000)
    rows = [
        {"id": "ses_old", "updated": now - 8 * 86_400_000},
        {"id": "ses_recent", "updated": now - 2 * 86_400_000},
        {"id": "ses_created_old_but_active", "created": now - 30 * 86_400_000, "updated": now},
    ]
    env, log = _environment(tmp_path, rows)
    dry = _invoke(env, "--dry-run")
    assert dry.returncode == 0, dry.stderr
    assert "would_delete=ses_old" in dry.stdout
    assert "ses_recent" not in dry.stdout
    assert "ses_created_old_but_active" not in dry.stdout
    assert json.loads((tmp_path / "sessions.json").read_text()) == rows
    assert "session delete" not in log.read_text()
    assert "wal_checkpoint" not in log.read_text()

    applied = _invoke(env)
    assert applied.returncode == 0, applied.stderr
    assert "deleted=ses_old" in applied.stdout
    assert "before_total_bytes=3072" in applied.stdout
    assert "before_freelist_pages=0" in applied.stdout
    assert "after_total_bytes=512 after_freelist_pages=1" in applied.stdout
    assert "reclaimed_bytes=2560" in applied.stdout
    assert [row["id"] for row in json.loads((tmp_path / "sessions.json").read_text())] == [
        "ses_recent",
        "ses_created_old_but_active",
    ]
    assert "db PRAGMA wal_checkpoint(TRUNCATE)" in log.read_text()


def test_opencode_retention_skips_entire_run_when_process_exists(tmp_path: Path) -> None:
    env, log = _environment(tmp_path, [{"id": "ses_old", "updated": 1}])
    env["FAKE_RUNNING"] = "1"
    result = _invoke(env)
    assert result.returncode == 0
    assert "SKIP: OpenCode is running" in result.stdout
    assert not log.exists()


@pytest.mark.parametrize(
    "rows",
    [
        [{"id": "ses_old"}],
        [{"id": "ses_old", "updated": "old"}],
        [{"id": "ses_old", "updated": 1}, {"id": "ses_old", "updated": 2}],
    ],
)
def test_opencode_retention_fails_closed_on_invalid_list(tmp_path: Path, rows: list[dict[str, object]]) -> None:
    env, log = _environment(tmp_path, rows)
    result = _invoke(env)
    assert result.returncode == 1
    assert "session delete" not in log.read_text()


def test_opencode_retention_succeeds_without_file_shrinkage(tmp_path: Path) -> None:
    env, log = _environment(tmp_path, [{"id": "ses_old", "updated": 1}])
    env["FAKE_RECLAIM"] = "0"
    Path(f"{tmp_path / 'opencode.db'}-wal").write_bytes(b"")
    result = _invoke(env)
    assert result.returncode == 0, result.stderr
    assert "reclaimed_bytes=0" in result.stdout
    assert "after_db_bytes=2048 after_wal_bytes=0" in result.stdout
    assert "after_freelist_pages=1" in result.stdout
    assert "session delete ses_old" in log.read_text()


def test_opencode_retention_wal_only_reclaim_succeeds(tmp_path: Path) -> None:
    env, _ = _environment(tmp_path, [{"id": "ses_old", "updated": 1}])
    env["FAKE_RECLAIM"] = "0"
    result = _invoke(env)
    assert result.returncode == 0, result.stderr
    assert "reclaimed_bytes=1024" in result.stdout
    assert "after_db_bytes=2048 after_wal_bytes=0" in result.stdout
    assert "after_freelist_pages=1" in result.stdout


def test_opencode_retention_skips_blocked_family_but_deletes_unrelated_old_family(tmp_path: Path) -> None:
    now = int(time.time() * 1000)
    env, log = _environment(
        tmp_path,
        [
            {"id": "ses_parent", "updated": 1, "parent": None},
            {"id": "ses_old_child", "updated": 2, "parent": "ses_parent"},
            {"id": "ses_recent_grandchild", "updated": now, "parent": "ses_old_child"},
            {"id": "ses_unrelated_parent", "updated": 3, "parent": None},
            {"id": "ses_unrelated_child", "updated": 4, "parent": "ses_unrelated_parent"},
        ],
    )
    dry = _invoke(env, "--dry-run")
    assert dry.returncode == 0, dry.stderr
    assert "skipped_family_root=ses_parent newest_age_days=0.00" in dry.stdout
    assert "would_delete=ses_unrelated_child" in dry.stdout
    assert "would_delete=ses_unrelated_parent" in dry.stdout
    assert "would_delete=ses_parent" not in dry.stdout
    assert "would_delete=ses_old_child" not in dry.stdout
    assert "session delete" not in log.read_text()
    applied = _invoke(env)
    assert applied.returncode == 0, applied.stderr
    assert "skipped_family_root=ses_parent newest_age_days=0.00" in applied.stdout
    assert [row["id"] for row in json.loads((tmp_path / "sessions.json").read_text())] == [
        "ses_parent",
        "ses_old_child",
        "ses_recent_grandchild",
    ]
    calls = log.read_text().splitlines()
    assert calls.index("session delete ses_unrelated_child --pure") < calls.index(
        "session delete ses_unrelated_parent --pure"
    )
    assert not any("session delete ses_parent" in call or "session delete ses_old_child" in call for call in calls)


def test_opencode_retention_deletes_children_before_parent(tmp_path: Path) -> None:
    env, log = _environment(
        tmp_path,
        [
            {"id": "ses_parent", "updated": 1, "parent": None},
            {"id": "ses_child", "updated": 2, "parent": "ses_parent"},
        ],
    )
    result = _invoke(env)
    assert result.returncode == 0, result.stderr
    calls = log.read_text().splitlines()
    assert calls.index("session delete ses_child --pure") < calls.index("session delete ses_parent --pure")


def test_opencode_retention_systemd_templates_verify(tmp_path: Path) -> None:
    analyzer = shutil.which("systemd-analyze")
    if analyzer is None:
        pytest.skip("systemd-analyze unavailable")
    source = SCRIPT.parents[2] / "packaging/systemd"
    names = ("learn-ukrainian-opencode-retention.service", "learn-ukrainian-opencode-retention.timer")
    for name in names:
        rendered = (source / name).read_text(encoding="utf-8")
        rendered = rendered.replace("@REPO_ROOT@", str(SCRIPT.parents[2])).replace("@PYTHON@", sys.executable)
        (tmp_path / name).write_text(rendered, encoding="utf-8")
    result = subprocess.run(
        [analyzer, "verify", *(str(tmp_path / name) for name in names)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
