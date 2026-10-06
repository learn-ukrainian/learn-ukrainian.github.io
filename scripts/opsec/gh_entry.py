"""Execute admitted raw reads/private writes through the publishing guard and shared client."""

from __future__ import annotations

import sys
from pathlib import Path

# Executed by the shim as a file, so imports do not depend on caller cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.opsec.gh_snapshot import admit
from scripts.opsec.prepublish import PublishBlocked, internal_environment, real_gh


def main() -> int:
    real, _shim, *argv = sys.argv[1:]
    environment = internal_environment()
    environment["AGENT_REAL_GH"] = real
    try:
        real = real_gh(environment)
        environment["AGENT_REAL_GH"] = real
        frozen = admit(argv, cwd=Path.cwd(), environment=environment)
        from scripts.common.github_client import run

        return run(["gh", *frozen.argv], env=environment).returncode
    except PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("OPSEC: publishing input unresolved; use explicit repository and --body-file.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
