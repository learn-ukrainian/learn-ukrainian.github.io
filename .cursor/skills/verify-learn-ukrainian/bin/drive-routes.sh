#!/usr/bin/env bash
# HTTP-level drive of main learner routes (no browser). Complements Playwright.
# Requires a doctor'd preview (LU_VERIFY_BASE_URL).
set -euo pipefail

BASE="${LU_VERIFY_BASE_URL:-}"
EVIDENCE_DIR="${LU_VERIFY_EVIDENCE_DIR:-.cursor/skills/verify-learn-ukrainian/artifacts/manual}"
mkdir -p "$EVIDENCE_DIR"

if [[ -z "$BASE" ]]; then
  echo "drive-routes FAIL: set LU_VERIFY_BASE_URL (source launch env.sh)" >&2
  exit 2
fi

fail=0
check() {
  local path="$1" needle="${2:-}"
  local out code
  out="$(mktemp)"
  set +e
  code="$(curl -sS -o "$out" -w '%{http_code}' --max-time 20 "${BASE}${path}")"
  set -e
  if [[ "$code" != "200" ]]; then
    echo "FAIL ${path} HTTP ${code}"
    fail=1
    rm -f "$out"
    return
  fi
  if [[ -n "$needle" ]] && ! grep -q "$needle" "$out"; then
    echo "FAIL ${path} missing needle: ${needle}"
    fail=1
    rm -f "$out"
    return
  fi
  echo "PASS ${path}${needle:+ (has ${needle})}"
  # Keep a short excerpt as evidence (no secrets).
  {
    echo "URL: ${BASE}${path}"
    echo "HTTP: ${code}"
    echo "BYTES: $(wc -c <"$out")"
    if [[ -n "$needle" ]]; then echo "NEEDLE: ${needle}"; fi
  } >"${EVIDENCE_DIR}/route-$(echo "$path" | tr '/?' '__').txt"
  rm -f "$out"
}

# Arc A1 landing (module cards, not the retired upgrade-edition sidebar).
check /a1/ 'sounds-letters-and-hello'
check /a1/ 'things-have-gender'
# Module landing
check /a1/sounds-letters-and-hello/ 'Sounds letters and hello'
# Atlas + practice shells
check /lexicon/ 'Атлас'
check /lexicon/browse/ 'data-index-search'
check /practice/ 'Практика'

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
echo "drive-routes OK"
exit 0
