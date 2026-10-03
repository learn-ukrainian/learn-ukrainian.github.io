"""Execute admitted raw reads/private writes through the retry/merge guard."""

from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path

# Executed by the shim as a file, so imports do not depend on caller cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.opsec.gh_snapshot import admit
from scripts.opsec.prepublish import PublishBlocked, internal_environment, real_gh


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
    environment = internal_environment()
    environment["AGENT_REAL_GH"] = real
    try:
        real = real_gh(environment)
        environment["AGENT_REAL_GH"] = real
        frozen = admit(argv, cwd=Path.cwd(), environment=environment)
        command = guarded_command(real, shim, frozen.argv)
        return execute(command, environment)
    except PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("OPSEC: publishing input unresolved; use explicit repository and --body-file.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
