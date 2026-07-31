#!/usr/bin/env bash
# Fail-closed health probe for the Atlas 20k runner. This only reports state:
# it never syncs a mirror, changes runner files, or starts enrichment (#6077).
#
# Required environment:
#   ATLAS_RUNNER_HOST  ssh destination for the runner, for example ops@<runner-host>
#
# Optional environment follows mirror_20k_runner.sh:
#   ATLAS_RUN_ROOT               remote run root (default /home/ops/atlas-runner)
#   ATLAS_WORK_DIR_NAME          work-dir below the run root (default run-20k)
#   ATLAS_MIRROR_DIR             local durable mirror directory
#   ATLAS_MIRROR_MAX_AGE_HOURS   durable mirror age limit (default 24)
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WORK_DIR_NAME="${ATLAS_WORK_DIR_NAME:-run-20k}"
RUN_ROOT="${ATLAS_RUN_ROOT:-/home/ops/atlas-runner}"
MIRROR_DIR="${ATLAS_MIRROR_DIR:-$REPO/data/lexicon/runner-mirror/$WORK_DIR_NAME}"
MAX_AGE_HOURS="${ATLAS_MIRROR_MAX_AGE_HOURS:-24}"
DURABLE_MIRROR=("$REPO/.venv/bin/python" "$REPO/scripts/lexicon/runner/durable_mirror.py")

host_set=false
mirror_present=false
mirror_require_ok=false

print_summary() {
  printf 'host_set=%s\n' "$host_set"
  printf 'mirror_present=%s\n' "$mirror_present"
  printf 'mirror_require_ok=%s\n' "$mirror_require_ok"
  printf 'mirror_age_hint=max_age_hours=%s\n' "$MAX_AGE_HOURS"
}

if [[ -z "${ATLAS_RUNNER_HOST:-}" ]]; then
  printf 'ATLAS_RUNNER_HOST is required; see #6077 AC-HOST.\n' >&2
  print_summary
  exit 2
fi
host_set=true

if ! command -v ssh >/dev/null 2>&1; then
  printf 'runner SSH work-dir check failed: ssh is not available.\n' >&2
  print_summary
  exit 2
fi

remote_work_dir="$RUN_ROOT/$WORK_DIR_NAME"
if ! ssh -o BatchMode=yes -- "$ATLAS_RUNNER_HOST" "test -d -- $(printf '%q' "$remote_work_dir")"; then
  printf 'runner SSH work-dir check failed: remote work-dir is unavailable.\n' >&2
  print_summary
  exit 2
fi

if [[ -e "$MIRROR_DIR" ]]; then
  mirror_present=true
  if "${DURABLE_MIRROR[@]}" require --mirror-dir "$MIRROR_DIR" --max-age-hours "$MAX_AGE_HOURS"; then
    mirror_require_ok=true
  else
    printf 'runner durable-mirror check failed; refresh and back up the mirror before cleanup.\n' >&2
    print_summary
    exit 2
  fi
else
  printf 'runner durable-mirror check failed: no local mirror at %s.\n' "$MIRROR_DIR" >&2
  print_summary
  exit 2
fi

print_summary
