#!/usr/bin/env bash
# =============================================================================
# scripts/ci/cursor_cloud_full_pytest.sh
#
# Pinned prototype runner script for Cursor cloud agent full pytest execution
# (Actions-outage fallback; design #6977 comment 5320409546 §4).
#
# Contract:
# - Takes --sha <40hex> (must match `git rev-parse HEAD`); dirty tree -> non-zero.
# - Takes --nonce <token> (required, charset [A-Za-z0-9._-], max 64 chars);
#   writes exclusively under `artifacts/<nonce>/`.
# - Takes --build-id <id> (required, non-empty; may be supplied via BUILD_ID env);
#   fails closed before the expensive test suite if missing or empty.
# - Installs CI venv like `ci.yml` (lockfile + CPU torch 2.13.0 carve-out) in a
#   temporary directory outside the git worktree (never overwriting repo .venv).
# - Asserts Node 22 (`node -v` is v22); runs `npm ci --ignore-scripts` only if
#   ACP test is in shard.
# - Runs Stanza provision with 3-attempt 10s/30s fail-closed retry.
# - Unsets ZNO_LIVE, RUN_BRIDGE_INBOX_INTEGRATION, ENFORCE_LATENCY_ASSERTIONS;
#   sets CI=true and GITHUB_ACTIONS=true.
# - Runs 4 duration-balanced shards via `scripts/ci/pytest_shards.py` (fixed 4-shard plane).
# - Shard 1 also runs serial playground probe with 3-attempt retry.
# - Emits per shard: plan.json, test-nodeids.txt, main-junit.xml, main.log, exit_code;
#   shard 1 also playground-junit.xml.
# - Bundle metadata: git_head, runner_sha256, nonce, build_id, started_at.
# - Performs final dirty-tree check allowlisting only artifacts/<nonce>/
#   (literal string-prefix match; the nonce is never regex-interpolated).
# - Performs ZERO GitHub API calls.
# =============================================================================

set -euo pipefail

SHA=""
NONCE=""
BUILD_ID="${BUILD_ID:-}"
DURATIONS_PATH=""
VENV_PATH=""
SHARD_COUNT=4

usage() {
  cat <<USAGE_EOF
Usage: $0 --sha <40hex-sha> --nonce <token> --build-id <id> [options]

Required arguments:
  --sha <40hex>          Expected commit SHA; must match HEAD exactly.
  --nonce <token>        Run nonce token; output written to artifacts/<nonce>/
  --build-id <id>        Build provenance ID, non-empty (may fall back to BUILD_ID env var)

Optional arguments:
  --durations <path>     Path to durations JSON dataset (default: ci-artifacts/pytest-durations.json)
  --venv <path>          Path to Python virtualenv (default: temp workdir outside git worktree)
  --shard-count <count>  Number of pytest shards to plan and run (fixed: must be 4)
  -h, --help             Show this help message and exit
USAGE_EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sha)
      SHA="${2:-}"
      shift 2
      ;;
    --sha=*)
      SHA="${1#*=}"
      shift 1
      ;;
    --nonce)
      NONCE="${2:-}"
      shift 2
      ;;
    --nonce=*)
      NONCE="${1#*=}"
      shift 1
      ;;
    --build-id)
      BUILD_ID="${2:-}"
      shift 2
      ;;
    --build-id=*)
      BUILD_ID="${1#*=}"
      shift 1
      ;;
    --durations)
      DURATIONS_PATH="${2:-}"
      shift 2
      ;;
    --durations=*)
      DURATIONS_PATH="${1#*=}"
      shift 1
      ;;
    --venv)
      VENV_PATH="${2:-}"
      shift 2
      ;;
    --venv=*)
      VENV_PATH="${1#*=}"
      shift 1
      ;;
    --shard-count)
      SHARD_COUNT="${2:-}"
      shift 2
      ;;
    --shard-count=*)
      SHARD_COUNT="${1#*=}"
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$SHA" ]]; then
  echo "Error: --sha is required" >&2
  exit 1
fi

if [[ ! "$SHA" =~ ^[0-9a-fA-F]{40}$ ]]; then
  echo "Error: --sha must be a 40-character hex string, got: $SHA" >&2
  exit 1
fi

if [[ -z "$NONCE" ]]; then
  echo "Error: --nonce is required and cannot be empty" >&2
  exit 1
fi

# Strict nonce charset: no regex metacharacters, slashes, or path traversal.
# The nonce is interpolated into path-prefix comparisons below; a value like
# 'x|.*' must be impossible so it can never broaden the dirty-tree allowlist.
if [[ ! "$NONCE" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]]; then
  echo "Error: --nonce must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\$ (got: $NONCE)" >&2
  exit 1
fi

if [[ "$SHARD_COUNT" -ne 4 ]]; then
  echo "Error: --shard-count must be 4 (fixed four-shard plane), got: $SHARD_COUNT" >&2
  exit 1
fi

# Fail closed before any expensive work if Build provenance is absent
# (the controller verifier never passes an empty build_id; do not invent one).
if [[ -z "${BUILD_ID//[[:space:]]/}" ]]; then
  echo "Error: --build-id is required and cannot be empty (missing Build provenance is never PASS); set --build-id or the BUILD_ID env var" >&2
  exit 1
fi

# 1. Assert clean working tree (dirty tree -> non-zero, never PASS)
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: git working tree is dirty; refusing to execute candidate runner" >&2
  git status --short >&2
  exit 1
fi

# 2. Assert git HEAD matches requested SHA
CURRENT_HEAD="$(git rev-parse HEAD)"
if [[ "${CURRENT_HEAD,,}" != "${SHA,,}" ]]; then
  echo "Error: git rev-parse HEAD ($CURRENT_HEAD) does not match requested --sha ($SHA)" >&2
  exit 1
fi

# 3. Setup artifacts root and record timestamps/hashes
STARTED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
RUNNER_SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
RUNNER_SHA256="$(sha256sum "${RUNNER_SCRIPT_PATH}" | cut -d' ' -f1)"

ARTIFACT_ROOT="artifacts/${NONCE}"
mkdir -p "${ARTIFACT_ROOT}"

# 4. Set environment invariants (R10)
unset ZNO_LIVE || true
unset RUN_BRIDGE_INBOX_INTEGRATION || true
unset ENFORCE_LATENCY_ASSERTIONS || true
export CI=true
export GITHUB_ACTIONS=true
export PYTEST_BREADCRUMB_DIR="${ARTIFACT_ROOT}/.pytest_breadcrumbs"
mkdir -p "${PYTEST_BREADCRUMB_DIR}"

# 5. Python virtual environment setup (write confinement: default outside git worktree)
VENV_DIR="${VENV_PATH:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}/cursor-cloud-ci-venv-${NONCE}}"
if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi
PYTHON="${VENV_DIR}/bin/python"

# 6. Install CI venv dependencies (lockfile + CPU torch 2.13.0 carve-out)
if [[ -f "requirements-lock.txt" ]]; then
  REQS_CI="${VENV_DIR}/requirements-ci.txt"
  grep -viE '^(torch|torchvision|open_clip_torch)==' requirements-lock.txt > "${REQS_CI}"
  for attempt in 1 2 3; do
    echo "CI dependencies pip install attempt ${attempt}/3"
    if "${PYTHON}" -m pip install --upgrade pip \
      && "${PYTHON}" -m pip install --no-deps -r "${REQS_CI}" \
      && "${PYTHON}" -m pip install --no-deps --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 \
      && "${PYTHON}" -m pip install --no-deps multiprocess==0.70.18 huggingface-hub==1.24.0; then
      break
    fi
    case "${attempt}" in
      1) sleep 10 ;;
      2) sleep 30 ;;
      3)
        echo "Error: CI dependencies install failed after 3 attempts" >&2
        exit 1
        ;;
    esac
  done
fi

# 7. Stanza Ukrainian model provisioning with 3-attempt retry (R5)
for attempt in 1 2 3; do
  echo "stanza provision attempt ${attempt}/3"
  if "${PYTHON}" -c "from scripts.pipeline.stress_annotator import annotate_stress; annotate_stress('Мама читає книжку.')" >/dev/null 2>&1; then
    break
  fi
  case "${attempt}" in
    1) sleep 10 ;;
    2) sleep 30 ;;
    3)
      echo "Error: Stanza provision failed after 3 attempts" >&2
      exit 1
      ;;
  esac
done

# 8. Verify Atlas manifest if pointer exists
if [[ -f "site/src/data/lexicon-manifest.pointer.json" ]]; then
  "${PYTHON}" -c "import sys; sys.path.insert(0, 'scripts'); from lexicon.manifest_io import load_manifest; load_manifest(); print('Atlas manifest verified')" || true
fi

# 9. Plan pytest shards (fixed 4-shard plane)
PLAN_DIR="${ARTIFACT_ROOT}/plans"
PLAN_ARGS=("${PYTHON}" scripts/ci/pytest_shards.py plan --output-dir "${PLAN_DIR}" --shard-count 4)
if [[ -n "${DURATIONS_PATH}" && -f "${DURATIONS_PATH}" ]]; then
  PLAN_ARGS+=(--durations "${DURATIONS_PATH}")
elif [[ -f "ci-artifacts/pytest-durations.json" ]]; then
  PLAN_ARGS+=(--durations "ci-artifacts/pytest-durations.json")
fi
"${PLAN_ARGS[@]}"

# 10. Execute each planned shard
OVERALL_EXIT=0

for shard in 1 2 3 4; do
  shard_dir="${ARTIFACT_ROOT}/pytest-shard-${shard}"
  mkdir -p "${shard_dir}"
  cp "${PLAN_DIR}/pytest-shard-${shard}/plan.json" "${shard_dir}/plan.json"
  cp "${PLAN_DIR}/pytest-shard-${shard}/test-nodeids.txt" "${shard_dir}/test-nodeids.txt"

  # ACP protocol test node dependency check (R3)
  if grep -q '^tests/agent_runtime/test_acp_text_agent.py::' "${shard_dir}/test-nodeids.txt"; then
    # Assert Node 22 before npm (provision if nvm/node 22 exists; fail UNKNOWN/INFRA if missing or != 22)
    NODE_VER=""
    if command -v node >/dev/null 2>&1; then
      NODE_VER="$(node -v 2>/dev/null || true)"
    fi
    if [[ ! "$NODE_VER" =~ ^v22\. ]]; then
      if [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
        # shellcheck source=/dev/null
        source "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
        nvm use 22 >/dev/null 2>&1 || nvm use v22 >/dev/null 2>&1 || true
      elif [[ -s "/usr/local/nvm/nvm.sh" ]]; then
        # shellcheck source=/dev/null
        source "/usr/local/nvm/nvm.sh"
        nvm use 22 >/dev/null 2>&1 || nvm use v22 >/dev/null 2>&1 || true
      fi
      if command -v node >/dev/null 2>&1; then
        NODE_VER="$(node -v 2>/dev/null || true)"
      fi
    fi
    if [[ ! "$NODE_VER" =~ ^v22\. ]]; then
      echo "Error: Node 22 is required before running npm (found: ${NODE_VER:-none}); fail UNKNOWN/INFRA" >&2
      exit 1
    fi

    for attempt in 1 2 3; do
      echo "shard ${shard} npm ci attempt ${attempt}/3"
      if npm ci --ignore-scripts; then
        break
      fi
      case "${attempt}" in
        1) sleep 10 ;;
        2) sleep 30 ;;
        3)
          echo "Error: npm ci failed after 3 attempts" >&2
          exit 1
          ;;
      esac
    done
  fi

  # Run shard
  set +e
  "${PYTHON}" scripts/ci/pytest_shards.py run --nodeids "${shard_dir}/test-nodeids.txt" -- \
    -n auto --dist=loadfile --strict-markers --timeout=120 --timeout-method=thread \
    -m 'not atlas_release and not slow' \
    --junitxml="${shard_dir}/main-junit.xml" --durations=0 \
    2>&1 | tee "${shard_dir}/main.log"
  shard_exit=$?
  set -e

  # Shard 1 serial playground probe (R4)
  if [[ "$shard" -eq 1 ]]; then
    set +e
    playground_exit=1
    for attempt in 1 2 3; do
      echo "playground smoke attempt ${attempt}/3"
      if "${PYTHON}" -m pytest \
        tests/test_playground_api_stability.py::test_playground_primary_endpoints_keep_health_fast \
        -v --tb=short --junitxml="${shard_dir}/playground-junit.xml"; then
        playground_exit=0
        break
      fi
      sleep 3
    done
    set -e

    if [[ "$shard_exit" -ne 0 ]]; then
      echo "$shard_exit" > "${shard_dir}/exit_code"
      OVERALL_EXIT=1
    elif [[ "$playground_exit" -ne 0 ]]; then
      echo "$playground_exit" > "${shard_dir}/exit_code"
      OVERALL_EXIT=1
    else
      echo "0" > "${shard_dir}/exit_code"
    fi
  else
    echo "$shard_exit" > "${shard_dir}/exit_code"
    if [[ "$shard_exit" -ne 0 ]]; then
      OVERALL_EXIT=1
    fi
  fi
done

# 11. Final dirty-tree check (allowlist only artifacts/<nonce>/; any other untracked/tracked dirty -> fail)
# >>> dirty-tree-allowlist-filter (extracted and executed by tests/ci/test_cursor_cloud_pytest_verify.py)
# Prints porcelain lines that are NOT allowlisted. Allowlist: untracked ('??') entries
# whose path equals artifacts/<nonce> or sits under artifacts/<nonce>/, matched by
# literal string prefix (bash glob with quoted variable parts) -- the nonce is never
# regex-interpolated, so a value like 'x|.*' cannot broaden the allowlist.
_filter_dirty_entries() {
  local filter_nonce="$1"
  local artifact_prefix="artifacts/${filter_nonce}"
  local status_line status_code entry_path
  while IFS= read -r status_line; do
    [[ -z "${status_line}" ]] && continue
    status_code="${status_line:0:2}"
    entry_path="${status_line:3}"
    # Strip the C-style surrounding quotes git adds around paths with special chars
    if [[ "${entry_path}" == \"*\" ]]; then
      entry_path="${entry_path#\"}"
      entry_path="${entry_path%\"}"
    fi
    if [[ "${status_code}" == "??" ]]; then
      case "${entry_path}" in
        "${artifact_prefix}" | "${artifact_prefix}/"*) continue ;;
      esac
    fi
    printf '%s\n' "${status_line}"
  done
}
# <<< dirty-tree-allowlist-filter

DIRTY_ENTRIES="$(git status --porcelain --untracked-files=all | _filter_dirty_entries "${NONCE}")"
if [[ -n "${DIRTY_ENTRIES}" ]]; then
  echo "Error: git working tree has unallowlisted dirty or untracked files after test execution (only artifacts/${NONCE}/ is allowed)" >&2
  echo "${DIRTY_ENTRIES}" >&2
  exit 1
fi

# 12. Write bundle metadata
cat > "${ARTIFACT_ROOT}/metadata.json" <<METADATA_EOF
{
  "build_id": "${BUILD_ID}",
  "git_head": "${CURRENT_HEAD}",
  "nonce": "${NONCE}",
  "runner_sha256": "${RUNNER_SHA256}",
  "started_at": "${STARTED_AT}"
}
METADATA_EOF

exit "$OVERALL_EXIT"
