#!/usr/bin/env bash
# Laptop-side sync: mirror the remote Atlas 20k runner work-dir into this repo's
# data/ so scripts/backup-data.sh (#6014) picks it up in its next restic
# snapshot. Run this after every fetch/reduce/enrich phase and always before
# any runner work-dir wipe or cleanup (#5884).
#
# Usage:
#   scripts/lexicon/runner/mirror_20k_runner.sh                 # sync + snapshot
#   scripts/lexicon/runner/mirror_20k_runner.sh --require-only   # just check freshness
#
# Env overrides:
#   ATLAS_RUNNER_HOST  ssh destination, e.g. ops@atlas-runner.example (required to sync)
#   ATLAS_RUN_ROOT      remote run root (default /home/ops/atlas-runner)
#   ATLAS_WORK_DIR_NAME remote work-dir under ATLAS_RUN_ROOT (default run-20k)
#   ATLAS_MIRROR_DIR    local mirror dir (default <repo>/data/lexicon/runner-mirror/<work-dir-name>)
#   ATLAS_MIRROR_MAX_AGE_HOURS  staleness gate for --require-only (default 24)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WORK_DIR_NAME="${ATLAS_WORK_DIR_NAME:-run-20k}"
MIRROR_DIR="${ATLAS_MIRROR_DIR:-$REPO/data/lexicon/runner-mirror/$WORK_DIR_NAME}"
MAX_AGE_HOURS="${ATLAS_MIRROR_MAX_AGE_HOURS:-24}"
DURABLE_MIRROR="$REPO/.venv/bin/python $REPO/scripts/lexicon/runner/durable_mirror.py"

if [[ "${1:-}" == "--require-only" ]]; then
  # shellcheck disable=SC2086
  $DURABLE_MIRROR require --mirror-dir "$MIRROR_DIR" --max-age-hours "$MAX_AGE_HOURS"
  exit $?
fi

RUN_ROOT="${ATLAS_RUN_ROOT:-/home/ops/atlas-runner}"
: "${ATLAS_RUNNER_HOST:?set ATLAS_RUNNER_HOST=user@host to sync from the VPS (or run durable_mirror.py snapshot --source directly)}"
SOURCE="${ATLAS_RUNNER_HOST}:${RUN_ROOT}/${WORK_DIR_NAME}"

echo "syncing ${SOURCE} -> ${MIRROR_DIR}"
# shellcheck disable=SC2086
$DURABLE_MIRROR snapshot --source "$SOURCE" --mirror-dir "$MIRROR_DIR"

echo
echo "mirror refreshed. Push it into the restic backup bus before any cleanup:"
echo "  cd $REPO && ./scripts/backup-data.sh backup && ./scripts/backup-data.sh backup --execute"
