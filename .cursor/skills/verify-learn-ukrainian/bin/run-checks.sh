#!/usr/bin/env bash
# Local verification checks reused from CI Gate / make / pytest targets.
# Private-data and external-service checks SKIP with a clear message (never fail the suite for env gaps).
# Overall exit: 0 if every executed check passed; 1 if any executed check failed.
if [[ "${1:-}" == --help ]]; then
  cat <<'EOF'
Usage: bash .cursor/skills/verify-learn-ukrainian/bin/run-checks.sh
Run local CI/data-contract checks; not the full CI test suite or deployment proof.
Inputs: LU_VERIFY_PYTHON defaults to the checkout's .venv/bin/python;
        use the task-prescribed shared interpreter in a dispatch worktree.
Outputs: PASS/FAIL/SKIP diagnostics and summary; reuse repository checks,
including practice-deck generation and the Word Atlas lint baseline ratchet.
Exit: 0 all executed checks pass (environment gaps SKIP), 1 any check fails.
Related: scripts/ci/checks.sh, ../SKILL.md.
EOF
  exit 0
fi
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

PYTHON="${LU_VERIFY_PYTHON:-${ROOT}/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  echo "SKIP: project interpreter missing — set LU_VERIFY_PYTHON to the shared interpreter in a worktree" >&2
  exit 0
fi

passed=0
failed=0
skipped=0

report() {
  local status="$1" name="$2" detail="${3:-}"
  case "$status" in
    PASS) passed=$((passed + 1)); echo "PASS  ${name}${detail:+ — ${detail}}" ;;
    FAIL) failed=$((failed + 1)); echo "FAIL  ${name}${detail:+ — ${detail}}" ;;
    SKIP) skipped=$((skipped + 1)); echo "SKIP  ${name}${detail:+ — ${detail}}" ;;
  esac
}

run_check() {
  local name="$1"
  shift
  local out ec
  out="$(mktemp)"
  set +e
  "$@" >"$out" 2>&1
  ec=$?
  set -e
  if [[ "$ec" -eq 0 ]]; then
    report PASS "$name"
  else
    # Show last lines for diagnosis without dumping secrets.
    tail -n 20 "$out" | sed 's/^/        | /'
    report FAIL "$name" "exit ${ec}"
  fi
  rm -f "$out"
}

# --- Site / toolchain presence ------------------------------------------------
if [[ -d "$ROOT/site/node_modules" ]]; then
  report PASS "site/node_modules present"
else
  report SKIP "site/node_modules" "run: (cd site && npm ci)"
fi

# --- CI Gate pieces developers run locally (from scripts/ci/checks.sh) --------
# Ruff — use the lockfile pin (requirements-lock.txt). A newer ruff from an
# unpinned requirements.txt install can fail rules CI does not yet enforce.
run_check "Ruff (CI Gate)" \
  "$PYTHON" -m ruff check scripts/ tests/ agents_extensions/ dashboards/

# Curriculum manifest canary
run_check "Curriculum manifest canary" \
  "$PYTHON" scripts/audit/curriculum_manifest_canary.py --check

# Atlas manifest freshness (DB-free)
run_check "Atlas manifest freshness" \
  "$PYTHON" scripts/lexicon/check_manifest_freshness.py

# Word Atlas sense-lint ratchet needs hydrated lexicon-manifest.json
if [[ -f site/src/data/lexicon-manifest.json ]]; then
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    # shellcheck disable=SC2016 # Expand the supplied interpreter and deck array in the child shell.
    run_check "Word Atlas sense-lint ratchet" \
      bash -c '
        "$1" -m scripts.practice_deck.io &&
        deck_args=()
        for deck in site/public/lexicon/*.json; do
          [[ -f "$deck" ]] || continue
          deck_args+=(--practice-deck "$deck")
        done
        "$1" scripts/audit/lint_word_atlas.py \
          --manifest site/src/data/lexicon-manifest.json \
          "${deck_args[@]}" --base-ref origin/main \
          --baseline scripts/audit/word_atlas_lint_baseline.json --ratchet --update-baseline &&
        git diff --exit-code -- scripts/audit/word_atlas_lint_baseline.json
      ' bash "$PYTHON"
  else
    report SKIP "Word Atlas sense-lint ratchet" "origin/main not available"
  fi
else
  report SKIP "Word Atlas sense-lint ratchet" \
    "site/src/data/lexicon-manifest.json missing (run site hydrate / npm run build)"
fi

# Full scripts/ci/checks.sh is available when hydrate + origin/main exist.
# It is optional here because the pieces above already cover the local Gate;
# run it explicitly when you need the aggregate:
#   EVENT_NAME=local bash scripts/ci/checks.sh
if [[ ! -f site/src/data/lexicon-manifest.json ]]; then
  report SKIP "CI Gate checks.sh (full aggregate)" \
    "hydrate site/src/data/lexicon-manifest.json first; or rely on individual checks above"
elif ! git rev-parse --verify origin/main >/dev/null 2>&1; then
  report SKIP "CI Gate checks.sh (full aggregate)" "origin/main not available"
else
  report PASS "CI Gate checks.sh (full aggregate available)" \
    "run manually: EVENT_NAME=local bash scripts/ci/checks.sh"
fi

# --- Licence / permissions register validation --------------------------------
run_check "Licence register validation (pytest)" \
  "$PYTHON" -m pytest tests/validate/test_permissions_register.py -q --tb=line

# --- Atlas register pins + pilot manifest verify (public committed inputs) ----
if [[ -f registry/atlas/pilot/pilot-v1.json && -f registry/atlas/identity/registry.json ]]; then
  out="$(mktemp)" err="$(mktemp)"
  set +e
  "$PYTHON" -m scripts.atlas.word_card_foundation verify \
      --manifest registry/atlas/pilot/pilot-v1.json \
      --registry registry/atlas/identity/registry.json >"$out" 2>"$err"
  ec=$?
  set -e
  if [[ "$ec" -eq 0 ]]; then
    report PASS "Atlas register pin + pilot manifest verify"
  else
    errtxt="$(cat "$err" 2>/dev/null || true)"
    if grep -qiE 'REFUSED:.*(inaccessible|not found|No such file|sources\.db|vesum|atlas\.db)' <<<"$errtxt"; then
      report SKIP "Atlas register pin + pilot manifest verify" "private/source DB unavailable"
    else
      echo "$errtxt" | tail -n 10 | sed 's/^/        | /'
      report FAIL "Atlas register pin + pilot manifest verify" "exit ${ec}"
    fi
  fi
  rm -f "$out" "$err"
else
  report SKIP "Atlas register pin + pilot manifest verify" "committed pilot/registry missing"
fi

# --- Optional: VESUM-backed practice linguistic gate --------------------------
if [[ -f data/vesum.db ]]; then
  run_check "Static practice linguistic gate (VESUM)" \
    make practice-deck-linguistic-gate
else
  report SKIP "Static practice linguistic gate (VESUM)" "data/vesum.db not present"
fi

# --- Optional: curated seed make targets that need private inputs -------------
if [[ -f .claude/atlas-epic/plans/curated-seed/v5-curated-with-provenance.jsonl ]]; then
  report PASS "Private curated-seed input present (make practice-admit-curated-seed runnable)"
else
  report SKIP "Private curated-seed make targets" "private curated seed input not present"
fi

echo
echo "Summary: ${passed} passed, ${failed} failed, ${skipped} skipped"
if [[ "$failed" -gt 0 ]]; then
  exit 1
fi
exit 0
