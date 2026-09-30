"""Execute the checked snapshot through the existing gh retry/merge guard."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

# Executed by the shim as a file, so imports do not depend on caller cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.opsec.gh_snapshot import snapshot
from scripts.opsec.prepublish import PublishBlocked, check_texts, real_gh


def execute(command, environment, stdin=None):
    """Forward termination to the retry helper so its temporary files are reaped."""
    with subprocess.Popen(command, env=environment, stdin=stdin) as child:

        def forward(signum, _frame):
            if child.poll() is None:
                child.send_signal(signum)

        signals = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
        previous = {signum: signal.signal(signum, forward) for signum in signals}
        try:
            return child.wait()
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def guarded_command(real, shim, argv):
    """Reuse the established Bash merge guard and retry logic after one scan."""
    return [
        "bash",
        "-c",
        'source "$1"; shift; real="$1"; shift; '
        'if [[ "${AGENT_NO_MERGE:-}" == "1" ]] && _blocks_gh_command "${1:-}" "${@:2}"; then _deny; fi; '
        '_run_with_secondary_rate_limit_retry "$real" "$@"',
        "gh",
        str(shim),
        real,
        *argv,
    ]


def main() -> int:
    real, shim, *argv = sys.argv[1:]
    environment = dict(os.environ)
    environment["AGENT_REAL_GH"] = real
    try:
        real = real_gh(environment)
        environment["AGENT_REAL_GH"] = real
        with snapshot(argv, cwd=Path.cwd(), environment=environment) as frozen:
            if frozen.write:
                check_texts(frozen.destination, frozen.texts, environment=environment, field_names=frozen.field_names)
            environment.pop("LU_OPSEC_OVERRIDE", None)
            # All retries use the same scanned files/stdin. The Bash helper still
            # owns its established rate-limit and merge/approval behavior.
            command = guarded_command(real, shim, frozen.argv)
            if frozen.stdin is None:
                return execute(command, environment)
            with tempfile.TemporaryFile() as stream:
                stream.write(frozen.stdin)
                stream.seek(0)
                # Shell helper rewinds stdin before retries when a snapshot exists.
                environment["LU_OPSEC_REPLAY_STDIN"] = "1"
                return execute(command, environment, stream)
    except PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("OPSEC: publishing input unresolved; use explicit repository and --body-file.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
