# shellcheck shell=bash
# Sourced by CONTRIBUTING.md step 3 and the Cursor verify skill's launch.sh,
# doctor.sh, drive-playwright.sh and run-checks.sh; not run directly. It only
# validates the PATH; the one documented nvm selection is CONTRIBUTING.md step 3.
#
# The checked-in Node contract: the exact release in .nvmrc, equal to package.json
# engines.node, run with its bundled npm at engines.npm. That npm enforces the
# install-script policy in .npmrc and site/.npmrc, so this file holds no versions.

# The locked site install, the same commands CONTRIBUTING.md and CI run.
LU_VERIFY_SITE_INSTALL='npm ci --ignore-scripts && npm rebuild --ignore-scripts=false'
_LU_VERIFY_EXACT='^[0-9]+\.[0-9]+\.[0-9]+$'

# lu_verify_toolchain ROOT LABEL
# Return 0 when node and npm on PATH match the checked-in pins. Otherwise print
# one line on stderr that names the pins and what was found, and points to
# CONTRIBUTING.md step 3, which holds the one nvm install and select; return 1.
# This file never loads or runs nvm.
lu_verify_toolchain() {
  local root="$1" label="$2" nvmrc="" rest entry prefix=""
  if [[ -f "$root/.nvmrc" ]]; then
    nvmrc="$(<"$root/.nvmrc")"
    # Only the ends are trimmed (CRLF, spaces): whitespace inside the value is
    # malformed, and deleting it could turn "2 2.23.4" into a release.
    nvmrc="${nvmrc#"${nvmrc%%[![:space:]]*}"}"
    nvmrc="${nvmrc%"${nvmrc##*[![:space:]]}"}"
    nvmrc="${nvmrc#v}"
  fi
  # An alias such as lts/* selects a moving release, so it is never a pin.
  if [[ ! "$nvmrc" =~ $_LU_VERIFY_EXACT ]]; then
    printf '%s FAIL: .nvmrc must hold an exact Node release (found "%s"). Restore the checked-in file: git -C %q checkout -- .nvmrc\n' \
      "$label" "${nvmrc//[[:space:]]/ }" "$root" >&2
    return 1
  fi
  # Only absolute entries preceding the first empty or relative entry are stable
  # across cd. Resolve external commands once, ignoring functions and aliases.
  rest="${PATH-}:"
  while entry="${rest%%:*}" && [[ "$entry" == /* ]]; do
    prefix="${prefix:+$prefix:}$entry"
    rest="${rest#*:}"
  done
  _lu_node_path="" _lu_npm_path=""
  if [[ -n "$prefix" ]]; then
    _lu_node_path="$(PATH="$prefix" type -P node)" || _lu_node_path=""
    _lu_npm_path="$(PATH="$prefix" type -P npm)" || _lu_npm_path=""
  fi
  [[ "$_lu_node_path" == /* && -f "$_lu_node_path" && -x "$_lu_node_path" ]] || _lu_node_path=""
  [[ "$_lu_npm_path" == /* && -f "$_lu_npm_path" && -x "$_lu_npm_path" ]] || _lu_npm_path=""
  if [[ -n "$rest" && ( -z "$_lu_node_path" || -z "$_lu_npm_path" ) ]]; then
    printf '%s FAIL: PATH holds an empty or relative entry before executable node and npm, so the tools checked here could differ after a cd. Use absolute PATH entries, then rerun.\n' "$label" >&2
    return 1
  fi
  if _lu_verify_versions "$root" "$nvmrc"; then
    return 0
  fi
  _lu_verify_manifest "$root" "$label" "$nvmrc" || return 1
  echo "$label FAIL: need Node $nvmrc (.nvmrc, package.json engines.node) with its bundled npm ${_lu_npm_pin:-at engines.npm}; found Node ${_lu_node_version:-none} and npm ${_lu_npm_version:-none}. Select them in this shell with CONTRIBUTING.md step 3 (nvm install && nvm use, run in $(printf %q "$root")), then rerun." >&2
  return 1
}

# _lu_verify_manifest ROOT LABEL NVMRC: when node could read package.json, refuse
# engines that do not pin the .nvmrc release and an exact npm. Without node the
# pins stay unknown and the toolchain repair comes first.
_lu_verify_manifest() {
  [[ -z "$_lu_node_version" ]] && return 0
  [[ "$_lu_node_pin" == "$3" && "$_lu_npm_pin" =~ $_LU_VERIFY_EXACT ]] && return 0
  printf '%s FAIL: package.json engines must pin node %s (the .nvmrc release) and an exact npm (found node "%s", npm "%s"). Restore the checked-in files: git -C %q checkout -- .nvmrc package.json\n' \
    "$2" "$3" "$_lu_node_pin" "$_lu_npm_pin" "$1" >&2
  return 1
}

# _lu_verify_versions ROOT NVMRC: read node, npm and the engines pins into
# _lu_* globals; return 0 only when all of them match.
_lu_verify_versions() {
  local root="$1" nvmrc="$2"
  _lu_node_version="" _lu_npm_version="" _lu_node_pin="" _lu_npm_pin=""
  if _lu_node_version="$("$_lu_node_path" -v 2>/dev/null)"; then
    # shellcheck disable=SC2016  # JavaScript template literal, expanded by node
    # Only exact string pins come through; a comma separator keeps an empty first field in place.
    IFS=, read -r _lu_node_pin _lu_npm_pin < <(
      "$_lu_node_path" -p 'const e = require(process.argv[1]).engines || {}; const pin = (v) => (typeof v === "string" && /^\d+\.\d+\.\d+$/.test(v) ? v : ""); `${pin(e.node)},${pin(e.npm)}`' \
        "$root/package.json" 2>/dev/null
    ) || true
  else
    _lu_node_version=""
  fi
  _lu_npm_version="$("$_lu_npm_path" --version 2>/dev/null)" || _lu_npm_version=""
  [[ "$_lu_node_pin" == "$nvmrc" && "$_lu_npm_pin" =~ $_LU_VERIFY_EXACT &&
     "$_lu_node_version" == "v$nvmrc" && "$_lu_npm_version" == "$_lu_npm_pin" ]]
}

# lu_verify_site_install_hint ROOT: how to repair a missing locked site install,
# as a command that works from any directory. A site/node_modules link (even a
# dangling one) belongs to another tree, which npm ci would empty through the link.
lu_verify_site_install_hint() {
  local modules="$1/site/node_modules" site
  if [[ -L "$modules" ]]; then
    printf 'site/node_modules is a link to %s, which this checkout must not reinstall; repair that install, or remove the link (rm -- %q) and rerun launch.sh to install from site/package-lock.json' \
      "$(readlink -- "$modules")" "$modules"
    return 0
  fi
  printf -v site '%q' "$1/site"
  printf 'run: cd %s && %s' "$site" "$LU_VERIFY_SITE_INSTALL"
}
