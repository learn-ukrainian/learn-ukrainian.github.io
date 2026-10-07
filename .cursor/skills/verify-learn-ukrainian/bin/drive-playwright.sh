#!/usr/bin/env bash
# Drive one mapped learner feature via the repo's Playwright specs.
# Prefer an already-launched preview (launch.sh). Playwright reuses it when the port answers.
if [[ "${1:-}" == --help ]]; then
  cat <<'EOF'
Usage: bash .cursor/skills/verify-learn-ukrainian/bin/drive-playwright.sh <lessons|atlas|practice|all>
Drive existing site Playwright specs after launch.sh and doctor.sh.
Example: bash .cursor/skills/verify-learn-ukrainian/bin/drive-playwright.sh practice
Inputs: Node 22, site dependencies; LU_VERIFY_PORT or PLAYWRIGHT_PORT (4321).
Outputs: playwright-<feature>.log and test-results copied into
LU_VERIFY_EVIDENCE_DIR (default: skill artifacts/manual); may install Chromium.
Exit: 0 passed, 2 invalid feature, otherwise Playwright's failure code.
Lessons includes the legacy sidebar contract; see ../features/lessons.md.
Related: launch.sh, doctor.sh, ../SKILL.md.
EOF
  exit 0
fi
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT/site"

FEATURE="${1:-}"
if [[ -z "$FEATURE" ]]; then
  echo "usage: drive-playwright.sh <lessons|atlas|practice|all>" >&2
  exit 2
fi

if [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
  nvm use 22 >/dev/null
fi

PORT="${LU_VERIFY_PORT:-${PLAYWRIGHT_PORT:-4321}}"
export PLAYWRIGHT_PORT="$PORT"
EVIDENCE_DIR="${LU_VERIFY_EVIDENCE_DIR:-${ROOT}/.cursor/skills/verify-learn-ukrainian/artifacts/manual}"
mkdir -p "$EVIDENCE_DIR"

GREP_PATTERN=""
case "$FEATURE" in
  lessons)
    # Upgrade-edition sidebar contract. Against the current arc `/a1/` landing this
    # suite is expected to fail until the spec is rewritten — prefer drive-routes.sh
    # for arc landing proof, and keep this entry for contract regression detection.
    SPECS=(e2e/a1-lesson-nav.spec.ts)
    GREP_PATTERN='A1 upgrade nav'
    ;;
  atlas)
    SPECS=(e2e/atlas-practice.spec.ts)
    GREP_PATTERN='browse supports search'
    ;;
  practice)
    SPECS=(e2e/atlas-practice.spec.ts)
    GREP_PATTERN='practice cloze mode never dead-ends|practice matching renders a real round'
    ;;
  all)
    SPECS=(e2e/a1-lesson-nav.spec.ts e2e/atlas-practice.spec.ts)
    ;;
  *)
    echo "unknown feature: $FEATURE" >&2
    exit 2
    ;;
esac

if ! compgen -G "$HOME/.cache/ms-playwright/chromium-*" >/dev/null; then
  npx playwright install chromium
fi

ARGS=(npx playwright test "${SPECS[@]}")
if [[ -n "$GREP_PATTERN" ]]; then
  ARGS+=(--grep "$GREP_PATTERN")
fi

set +e
"${ARGS[@]}" 2>&1 | tee "${EVIDENCE_DIR}/playwright-${FEATURE}.log"
ec=${PIPESTATUS[0]}
set -e

if [[ -d test-results ]]; then
  mkdir -p "${EVIDENCE_DIR}/playwright-test-results"
  cp -a test-results/. "${EVIDENCE_DIR}/playwright-test-results/" 2>/dev/null || true
fi

exit "$ec"
