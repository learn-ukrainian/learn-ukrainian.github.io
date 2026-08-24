"""Independent driver renew loop contract."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_driver_renew_loop_409_stops_provider_with_lease_lost(tmp_path: Path) -> None:
    fake_python = tmp_path / ".venv" / "bin" / "python"
    fake_python.parent.mkdir(parents=True)
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "${1:-}" == "-m" && "${2:-}" == "scripts.session_supervisor" ]]; then\n'
        "  echo 'session-supervisor: LEASE LOST' >&2\n"
        "  exit 4\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    core = Path(__file__).resolve().parents[1] / "scripts" / "lib" / "launcher_core.sh"
    script = f"""
set -u
LC_MODE=driver
LC_DRIVER_LEASE_CLAIMED=1
LC_DRY_RUN=0
LC_ROOT={str(tmp_path)!r}
SESSION_STREAM_TTL_SECONDS=4
SESSION_STREAM_RENEW_INTERVAL_SECONDS=1
SESSION_STREAM_RENEW_JITTER_SECONDS=0
export LC_MODE LC_DRIVER_LEASE_CLAIMED LC_DRY_RUN LC_ROOT
export SESSION_STREAM_TTL_SECONDS SESSION_STREAM_RENEW_INTERVAL_SECONDS SESSION_STREAM_RENEW_JITTER_SECONDS
source {str(core)!r}
sleep 20 &
child=$!
launcher_driver_renew_loop "$child"
wait "$child" || true
launcher_stop_driver_renew
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert "LEASE LOST" in result.stderr
