"""Execute admitted raw reads/private writes through the publishing guard and shared client."""

from __future__ import annotations

import sys
from pathlib import Path

# Executed by the shim as a file, so imports do not depend on caller cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.opsec.gh_snapshot import READ_GRAMMARS, admit
from scripts.opsec.prepublish import PublishBlocked, internal_environment, real_gh


def _is_read_intent(argv: list[str], frozen=None) -> bool:
    if frozen is not None:
        return not frozen.write
    start = 0
    while start < len(argv) and argv[start] in {"--repo", "-R"}:
        start += 2
    if start >= len(argv):
        return False
    if argv[start] == "api":
        return True
    return start + 1 < len(argv) and tuple(argv[start : start + 2]) in READ_GRAMMARS


def main() -> int:
    real, _shim, *argv = sys.argv[1:]
    environment = internal_environment()
    environment["AGENT_REAL_GH"] = real
    frozen = None
    try:
        real = real_gh(environment)
        environment["AGENT_REAL_GH"] = real
        frozen = admit(argv, cwd=Path.cwd(), environment=environment)
        from scripts.common import github_client

        return github_client.run(["gh", *frozen.argv], env=environment).returncode
    except PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        if _is_read_intent(argv, frozen):
            print("OPSEC: read command failed; verify repository and flags.", file=sys.stderr)
            return 2
        print("OPSEC: publishing input unresolved; use explicit repository and --body-file.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
