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

sha256_verify() {
  # sha256_verify <expected> <file>
  local expected="$1" file="$2" actual
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

resolve_actionlint() {
  # Explicit override wins.
  if [[ -n "${ACTIONLINT_BIN:-}" ]]; then
    echo "$ACTIONLINT_BIN"
    return 0
  fi
  # Local convenience: use a system actionlint unless CI forces a pinned fetch.
  if [[ -z "${ACTIONLINT_FORCE_DOWNLOAD:-}" ]] && command -v actionlint >/dev/null 2>&1; then
    command -v actionlint
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

  local tmp tarball url
  tmp="$(mktemp -d)"
  tarball="${tmp}/actionlint.tar.gz"
  url="https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_${platform}.tar.gz"

  echo "→ fetching actionlint v${ACTIONLINT_VERSION} (${platform})" >&2
  curl -fsSL -o "$tarball" "$url"
  sha256_verify "$expected" "$tarball"
  tar -xzf "$tarball" -C "$tmp" actionlint
  echo "${tmp}/actionlint"
}

main() {
  cd "$REPO_ROOT"

  local bin
  bin="$(resolve_actionlint)"

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
}

main "$@"
