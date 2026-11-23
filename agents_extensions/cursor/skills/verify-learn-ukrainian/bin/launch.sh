#!/usr/bin/env bash
# Build (if needed) and start an isolated site preview for verification.
# Prints the exact env.sh path the caller should source.
if [[ "${1:-}" == --help ]]; then
  cat <<'EOF'
Usage: bash .cursor/skills/verify-learn-ukrainian/bin/launch.sh [preview|dev]
Build and launch an isolated learner site for local verification; not deployment.
Default: preview using build:shell; LU_VERIFY_BUILD_MODE=full selects build.
Toolchain: the Node release in .nvmrc (package.json engines.node) with its bundled
npm (engines.npm), selected through nvm when installed; otherwise refuses and
prints the command that installs and selects it.
Dependencies: when site/node_modules is absent, npm ci --ignore-scripts and
npm rebuild --ignore-scripts=false in site/, from site/package-lock.json under
site/.npmrc; the locked site/node_modules/.bin/astro must then exist, never npx
or a registry download.
Inputs: LU_VERIFY_HOST=localhost, LU_VERIFY_PORT=4321;
        optional LU_VERIFY_RUN_ID, LU_VERIFY_STATE_DIR, LU_VERIFY_EVIDENCE_DIR.
State: a lu-verify-<run-id> directory directly under ${TMPDIR:-/tmp}.
Outputs: site build, process, state env.sh/PID/log, evidence directory.
Exit: 0 when HTTP is ready; nonzero on invalid inputs or launch failure.
Related: doctor.sh, cleanup.sh, ../SKILL.md.
EOF
  exit 0
fi
set -euo pipefail

BIN="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$BIN/../../../.." && pwd)"
cd "$ROOT"

MODE="${1:-preview}" # preview | dev
PORT="${LU_VERIFY_PORT:-4321}"
HOST="${LU_VERIFY_HOST:-localhost}"
RUN_ID="${LU_VERIFY_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
STATE_DIR="${LU_VERIFY_STATE_DIR:-${TMPDIR:-/tmp}/lu-verify-${RUN_ID}}"
EVIDENCE_DIR="${LU_VERIFY_EVIDENCE_DIR:-${ROOT}/.cursor/skills/verify-learn-ukrainian/artifacts/${RUN_ID}}"
PID_FILE="${STATE_DIR}/site.pid"
LOG_FILE="${STATE_DIR}/site.log"
BUILD_MODE="${LU_VERIFY_BUILD_MODE:-shell}" # shell | full

temp_root="$(readlink -f -- "${TMPDIR:-/tmp}")"
state_parent="$(readlink -m -- "$(dirname -- "$STATE_DIR")")"
state_name="$(basename -- "$STATE_DIR")"
if [[ "$state_parent" != "$temp_root" || "$state_name" != lu-verify-* || "$state_name" == lu-verify- || -L "$state_parent/$state_name" ]]; then
  echo "launch FAIL: unsafe state directory; require a lu-verify-<run-id> directory directly under the temporary root" >&2
  exit 1
fi

mkdir -p "$STATE_DIR" "$EVIDENCE_DIR"

# shellcheck source=SCRIPTDIR/toolchain.sh
. "$BIN/toolchain.sh"
lu_verify_toolchain "$ROOT" launch || exit 1

# Refuse to double-drive a foreign listener on our port.
if curl -fsS --max-time 1 "http://${HOST}:${PORT}/" >/dev/null 2>&1; then
  if [[ ! -f "$PID_FILE" ]]; then
    echo "launch FAIL: ${HOST}:${PORT} already answers and is not this run's instance. Pick LU_VERIFY_PORT or stop the other server." >&2
    exit 1
  fi
fi

# Locked Astro only: the binary `npm ci` installed from site/package-lock.json.
# No npx fallback, so a missing executable fails here before any registry access.
ASTRO="$ROOT/site/node_modules/.bin/astro"

ensure_site_deps() {
  # Install only into an absent path: npm ci first deletes what is there, and a
  # node_modules link (even a dangling one) may point at another checkout's tree.
  if [[ ! -e "$ROOT/site/node_modules" && ! -L "$ROOT/site/node_modules" ]]; then
    echo "launch: $LU_VERIFY_SITE_INSTALL in site/ (committed lock)"
    # Link bins only after the approved scripts ran, so an interrupted install
    # leaves no Astro binary and the check below refuses it (as services.sh does).
    (
      cd "$ROOT/site" &&
        npm ci --ignore-scripts --bin-links=false &&
        npm rebuild --ignore-scripts=false --bin-links=false &&
        npm rebuild --ignore-scripts
    )
  fi
  if [[ ! -f "$ASTRO" || ! -x "$ASTRO" ]]; then
    echo "launch FAIL: locked Astro missing or not executable at site/node_modules/.bin/astro; run (cd site && $LU_VERIFY_SITE_INSTALL) (no npx or PATH fallback)" >&2
    exit 1
  fi
}

build_site() {
  ensure_site_deps
  if [[ "$BUILD_MODE" == "full" ]]; then
    echo "launch: npm run build (hydrate + astro) — needs public GitHub release asset for Atlas manifest"
    (cd "$ROOT/site" && npm run build)
  else
    echo "launch: npm run build:shell (committed artifacts + astro)"
    (cd "$ROOT/site" && npm run build:shell)
  fi
}

start_preview() {
  build_site
  (
    cd "$ROOT/site"
    # Own process group so cleanup can tear down children without pkill-by-name.
    setsid "$ASTRO" preview --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
  )
}

start_dev() {
  ensure_site_deps
  (
    cd "$ROOT/site"
    setsid npm run dev -- --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
  )
}

case "$MODE" in
  preview) start_preview ;;
  dev) start_dev ;;
  *)
    echo "usage: launch.sh [preview|dev]" >&2
    exit 2
    ;;
esac

# Wait for readiness
for _ in $(seq 1 90); do
  if curl -fsS --max-time 2 "http://${HOST}:${PORT}/" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! curl -fsS --max-time 2 "http://${HOST}:${PORT}/" >/dev/null 2>&1; then
  echo "launch FAIL: site never became ready. Log: $LOG_FILE" >&2
  tail -n 80 "$LOG_FILE" >&2 || true
  exit 1
fi

cat >"${STATE_DIR}/env.sh" <<EOF
export LU_VERIFY_RUN_ID='${RUN_ID}'
export LU_VERIFY_STATE_DIR='${STATE_DIR}'
export LU_VERIFY_EVIDENCE_DIR='${EVIDENCE_DIR}'
export LU_VERIFY_HOST='${HOST}'
export LU_VERIFY_PORT='${PORT}'
export LU_VERIFY_PID_FILE='${PID_FILE}'
export LU_VERIFY_LOG_FILE='${LOG_FILE}'
export LU_VERIFY_BASE_URL='http://${HOST}:${PORT}'
export LU_VERIFY_EXPECTED_REV='$(git -C "$ROOT" rev-parse HEAD)'
export PLAYWRIGHT_PORT='${PORT}'
EOF

echo "launch OK: http://${HOST}:${PORT}/ (pid $(cat "$PID_FILE"), log $LOG_FILE)"
echo "source ${STATE_DIR}/env.sh"
echo "evidence -> ${EVIDENCE_DIR}"
