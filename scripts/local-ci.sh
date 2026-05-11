#!/usr/bin/env bash
# local-ci.sh — thin wrapper around `act` for local CI replay.
#
# Why this wrapper exists:
#   - User runs OrbStack (not Docker Desktop). OrbStack puts its socket at
#     `~/.orbstack/run/docker.sock`, not the canonical `/var/run/docker.sock`.
#   - `act` defaults to the canonical path and exits with "Couldn't get a
#     valid docker connection" if the socket isn't there.
#   - This wrapper exports `DOCKER_HOST` to the OrbStack socket BEFORE
#     invoking `act`, plus auto-starts OrbStack if not running.
#
# Usage:
#   scripts/local-ci.sh                          # interactive — pick a job
#   scripts/local-ci.sh -l                       # list discoverable jobs
#   scripts/local-ci.sh -W .github/workflows/ci.yml -j lint
#   scripts/local-ci.sh -W .github/workflows/ci.yml -j test --dryrun
#
# Any flag is forwarded to `act` verbatim — `.actrc` provides project defaults
# (Apple Silicon arch, runner images, container reuse).
#
# Related: GH issue #1891 (local CI replay decision), docs/best-practices/
# local-ci-replay.md (per-project pattern).

set -euo pipefail

# Resolve the OrbStack docker socket. Auto-start the daemon if it's not up
# already — OrbStack starts in ~3-5s and the socket appears immediately after.
ORBSTACK_SOCK="${HOME}/.orbstack/run/docker.sock"

if [[ ! -S "$ORBSTACK_SOCK" ]]; then
    echo "ℹ️  OrbStack daemon not running — starting it…" >&2
    open -a OrbStack
    # Wait up to 30s for the socket to appear. Real-world: <5s on a warm Mac.
    for _ in $(seq 1 15); do
        [[ -S "$ORBSTACK_SOCK" ]] && break
        sleep 2
    done
    if [[ ! -S "$ORBSTACK_SOCK" ]]; then
        echo "❌ OrbStack socket did not appear within 30s at $ORBSTACK_SOCK" >&2
        echo "   Start it manually with: open -a OrbStack" >&2
        exit 1
    fi
    echo "✅ OrbStack daemon up." >&2
fi

export DOCKER_HOST="unix://${ORBSTACK_SOCK}"

# Auto-include a default event payload UNLESS the caller already passed `-e`
# or `--eventpath`. The payload supplies:
#
#   - `repository.default_branch` (required by `dorny/paths-filter@v4`,
#     used in ci.yml::changes — without it the job errors out)
#   - `before` = the previous commit SHA, `after` = HEAD (so the
#     path-filter sees a real diff and downstream jobs gated on
#     `needs.changes.outputs.code == 'true'` actually run)
#
# We template both SHAs dynamically per invocation so the diff matches the
# real working state. .github/act-event-push.json is a static fallback used
# when git lookup fails (e.g. running outside a repo).
HAS_EVENT_FLAG=false
for arg in "$@"; do
    if [[ "$arg" == "-e" || "$arg" == "--eventpath" ]]; then
        HAS_EVENT_FLAG=true
        break
    fi
done

if [[ "$HAS_EVENT_FLAG" == false ]]; then
    # Template a fresh event payload to /tmp with real git SHAs. Falls back to
    # the static .github/act-event-push.json if git lookup fails.
    EVENT_TMP="$(mktemp -t act-event-push.XXXXXX.json)"
    trap 'rm -f "$EVENT_TMP"' EXIT

    BEFORE_SHA="$(git rev-parse --verify HEAD~1 2>/dev/null || echo '0000000000000000000000000000000000000000')"
    AFTER_SHA="$(git rev-parse --verify HEAD 2>/dev/null || echo '0000000000000000000000000000000000000000')"

    cat >"$EVENT_TMP" <<EOF
{
  "ref": "refs/heads/main",
  "before": "$BEFORE_SHA",
  "after": "$AFTER_SHA",
  "repository": {
    "name": "learn-ukrainian.github.io",
    "full_name": "learn-ukrainian/learn-ukrainian.github.io",
    "default_branch": "main",
    "owner": { "login": "learn-ukrainian" }
  },
  "pusher": { "name": "local-act-runner" }
}
EOF

    exec act --eventpath "$EVENT_TMP" "$@"
else
    exec act "$@"
fi
