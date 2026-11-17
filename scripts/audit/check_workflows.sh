#!/usr/bin/env bash
# Lint .github/workflows/** with actionlint — the structural/schema gate for
# GitHub Actions workflow files.
#
# WHY THIS EXISTS (root-cause fix for the #3739/#3742 deploy-yaml break):
#   `validate-yaml.yml` runs yamllint only on curriculum/** and `zizmor.yml`
#   does Actions *security* analysis. Nothing validated workflow *structure*,
#   so #3739 de-indented setup-node's `with:` keys (valid YAML, invalid
#   Actions) and the broken workflow merged — Pages deploy then failed in
#   production. actionlint type-checks `${{ }}` expressions, validates step
#   keys / `with:` inputs / runner labels, and (with shellcheck on PATH)
#   lints `run:` scripts. It exits non-zero on any finding → a real gate.
#
# SINGLE SOURCE OF TRUTH: both CI (.github/workflows/actionlint.yml) and local
#   devs call this script, so the pinned version + checksums never drift apart.
#
# USAGE:
#   scripts/audit/check_workflows.sh                 # lint all workflow files
#   scripts/audit/check_workflows.sh path/to/wf.yml  # lint specific file(s)
#
# ENV:
#   ACTIONLINT_BIN=/path/to/actionlint   explicit binary override (skip download)
#   ACTIONLINT_FORCE_DOWNLOAD=1          ignore any actionlint on PATH and always
#                                        fetch the pinned, checksum-verified build
#                                        (set in CI for reproducibility)
#   ACTIONLINT_CACHE_DIR=/path/to/dir    keep the checksum-verified release
#                                        tarball here and reuse it on later runs
#                                        (CI restores it from the Actions cache);
#                                        a cached copy is re-verified every run
#   GH_TOKEN (or GITHUB_TOKEN)           download through the authenticated
#                                        GitHub releases API with `gh` (CI
#                                        requires it: the anonymous release URL
#                                        answers HTTP 403 when the shared runner
#                                        address pool is throttled); without a
#                                        token a local run uses the anonymous URL
#   PYTHON=/path/to/python               interpreter for the untrusted-context
#                                        interpolation checker (default:
#                                        .venv/bin/python, else python3)
set -euo pipefail

# --- pinned release (bump VERSION + all checksums together) -------------------
ACTIONLINT_VERSION="1.7.12"
# sha256 of each release tarball, from the upstream checksums.txt for v1.7.12.
# Verify when bumping: gh api repos/rhysd/actionlint/releases/latest \
#   --jq '.assets[]|select(.name|endswith("checksums.txt")).url' \
#   | xargs -I{} gh api {} -H 'Accept: application/octet-stream'
checksum_for() {
  case "$1" in
    linux_amd64)  echo "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8" ;;
    linux_arm64)  echo "325e971b6ba9bfa504672e29be93c24981eeb1c07576d730e9f7c8805afff0c6" ;;
    darwin_amd64) echo "5b44c3bc2255115c9b69e30efc0fecdf498fdb63c5d58e17084fd5f16324c644" ;;
    darwin_arm64) echo "aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f" ;;
    *) return 1 ;;
  esac
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Remove only a binary we downloaded ourselves (stays empty for ACTIONLINT_BIN
# or a system actionlint). The EXIT trap fires on success, error, and SIGTERM,
# so the temp dir never leaks for a local dev across runs.
_DOWNLOAD_DIR=""
cleanup() { [[ -n "$_DOWNLOAD_DIR" ]] && rm -rf "$_DOWNLOAD_DIR"; return 0; }
trap cleanup EXIT

sha256_verify() {
  # sha256_verify <expected> <file>
  local expected="$1" file="$2" actual
  [[ -f "$file" ]] || { echo "❌ download missing, cannot verify: $file" >&2; return 1; }
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$file" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$file" | awk '{print $1}')"
  else
    echo "❌ no sha256sum/shasum available to verify download" >&2
    return 1
  fi
  if [[ "$actual" != "$expected" ]]; then
    echo "❌ actionlint checksum mismatch" >&2
    echo "   expected: $expected" >&2
    echo "   actual:   $actual" >&2
    return 1
  fi
}

# Sets RESOLVED_BIN (and, when it downloads, _DOWNLOAD_DIR). Called directly —
# NOT in $(...) — so the globals survive into the caller and the EXIT trap.
RESOLVED_BIN=""
resolve_actionlint() {
  # Explicit override wins — but validate it so a stale path fails loudly here
  # instead of with a cryptic "No such file" when we later try to run it.
  if [[ -n "${ACTIONLINT_BIN:-}" ]]; then
    if [[ ! -x "$ACTIONLINT_BIN" ]]; then
      echo "❌ ACTIONLINT_BIN is not an executable file: $ACTIONLINT_BIN" >&2
      return 1
    fi
    RESOLVED_BIN="$ACTIONLINT_BIN"
    return 0
  fi
  # Local convenience: use a system actionlint unless CI forces a pinned fetch.
  if [[ -z "${ACTIONLINT_FORCE_DOWNLOAD:-}" ]] && command -v actionlint >/dev/null 2>&1; then
    RESOLVED_BIN="$(command -v actionlint)"
    return 0
  fi

  # Detect platform.
  local os arch platform
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$(uname -m)" in
    x86_64|amd64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *) echo "❌ unsupported arch: $(uname -m)" >&2; return 1 ;;
  esac
  platform="${os}_${arch}"

  local expected
  if ! expected="$(checksum_for "$platform")"; then
    echo "❌ no pinned actionlint checksum for platform: $platform" >&2
    return 1
  fi

  # Extract into a temp dir the EXIT trap will remove.
  _DOWNLOAD_DIR="$(mktemp -d)"
  local name tarball="" cache_dir="${ACTIONLINT_CACHE_DIR:-}"
  name="actionlint_${ACTIONLINT_VERSION}_${platform}.tar.gz"

  # A cached tarball is used only after it passes the same checksum check as
  # a fresh download; a mismatching copy is discarded and fetched again.
  if [[ -n "$cache_dir" && -f "${cache_dir}/${name}" ]]; then
    if sha256_verify "$expected" "${cache_dir}/${name}"; then
      tarball="${cache_dir}/${name}"
      echo "→ actionlint v${ACTIONLINT_VERSION} (${platform}) from cache, checksum verified" >&2
    else
      echo "⚠️ cached ${name} failed its checksum; discarding it and downloading again" >&2
      rm -f "${cache_dir}/${name}"
    fi
  fi

  if [[ -z "$tarball" ]]; then
    fetch_release_tarball "$name" "$_DOWNLOAD_DIR"
    tarball="${_DOWNLOAD_DIR}/${name}"
    sha256_verify "$expected" "$tarball"
    echo "→ actionlint v${ACTIONLINT_VERSION} (${platform}) downloaded, checksum verified" >&2
    # Only verified bytes enter the cache; the rename keeps a partial copy out.
    if [[ -n "$cache_dir" ]]; then
      mkdir -p "$cache_dir"
      cp "$tarball" "${cache_dir}/${name}.partial"
      mv -f "${cache_dir}/${name}.partial" "${cache_dir}/${name}"
    fi
  fi

  tar -xzf "$tarball" -C "$_DOWNLOAD_DIR" actionlint
  RESOLVED_BIN="${_DOWNLOAD_DIR}/actionlint"
}

# fetch_release_tarball <asset name> <dest dir>
# With a token, downloads through the authenticated releases API (`gh`, which
# reads GH_TOKEN or GITHUB_TOKEN). CI refuses the anonymous release URL, whose
# shared-runner throttle answered HTTP 403 for whole retry windows (PR 13136,
# run 44018246101); a local run without a token still uses it.
fetch_release_tarball() {
  local name="$1" dest="$2" attempt
  if [[ -n "${GH_TOKEN:-}${GITHUB_TOKEN:-}" ]]; then
    if ! command -v gh >/dev/null 2>&1; then
      echo "❌ GH_TOKEN is set but the gh CLI is not on PATH" >&2
      return 1
    fi
    echo "→ fetching ${name} through the authenticated GitHub releases API" >&2
    for attempt in 1 2 3; do
      if gh release download "v${ACTIONLINT_VERSION}" --repo rhysd/actionlint \
          --pattern "$name" --dir "$dest" --clobber; then
        return 0
      fi
      if ((attempt < 3)); then
        echo "⚠️ actionlint download attempt ${attempt} failed; retrying" >&2
        sleep $((attempt * 15))
      fi
    done
    echo "❌ could not download ${name} from rhysd/actionlint release v${ACTIONLINT_VERSION}" >&2
    return 1
  fi
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    echo "❌ CI must fetch actionlint through the authenticated API: set GH_TOKEN" >&2
    return 1
  fi
  echo "→ fetching ${name} anonymously (no GH_TOKEN; local run)" >&2
  curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 -o "${dest}/${name}" \
    "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/${name}"
}

main() {
  cd "$REPO_ROOT"

  resolve_actionlint
  local bin="$RESOLVED_BIN"

  # Targets: explicit args, else every workflow file.
  local -a targets=()
  if (($# > 0)); then
    targets=("$@")
  else
    while IFS= read -r f; do targets+=("$f"); done < <(
      find .github/workflows -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) | sort
    )
  fi

  if ((${#targets[@]} == 0)); then
    echo "✅ no workflow files to lint"
    return 0
  fi

  echo "→ actionlint $("$bin" --version | head -1) on ${#targets[@]} workflow file(s)" >&2
  "$bin" -color "${targets[@]}"
  echo "✅ actionlint: all workflow files valid"

  # Fail-closed interpolation gate (advisor packet B+D, 2026-08-18): untrusted
  # GitHub context (github.event.issue.*/comment.*, PR title/body, head_ref,
  # ...) must not be ${{ }}-expanded inside run: scripts — env: + "$VAR" is
  # the safe pattern. Runs after actionlint so this script stays the single
  # workflow gate both CI and local devs invoke. The checker is stdlib-only;
  # prefer the project venv interpreter, fall back to any python3.
  local py="${PYTHON:-}"
  if [[ -z "$py" ]]; then
    if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
      py="$REPO_ROOT/.venv/bin/python"
    else
      py="python3"
    fi
  fi
  "$py" scripts/audit/check_untrusted_workflow_interpolation.py "${targets[@]}"
}

main "$@"
