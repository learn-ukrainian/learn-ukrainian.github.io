#!/usr/bin/env bash
# Pre-publication gate for the public learn-ukrainian/machinery repository
# (machinery move contract v3, amendment PUBLIC-1104 item 3).
#
# Run it once against the rewritten clone and the exact list of refs proposed
# for the first content push. It clears the push only when every check passes:
#
# - TruffleHog CLI 3.99.0 scans the full history reachable from every proposed
#   ref with the flags recorded in pins.txt and the reviewed .trufflehogignore
#   beside this script: its git source once per ref, and its filesystem source
#   over every distinct (path, blob) version, because the git source does not
#   read content that only a merge commit introduces.
# - Semgrep CE 1.183.0 runs the configurations that sast.yml lists, from the
#   semgrep-rules checkout at the pinned commit, over the final tree of every
#   ref and over every distinct (path, blob) version reachable from the refs.
# - Any finding, missing input, scanner error, malformed scanner output or
#   unclassified skip blocks the push. Raw findings and scanner stderr stay in
#   the private output directory (mode 0700) and are never printed; the log
#   carries counts only.
# - A pass writes clearance.json, bound to the ref-to-SHA map and a digest of
#   the history those refs reach. `verify` refuses a clearance whose refs or
#   digest no longer match.
#
# Scanners run under `env -i` with private HOME and TMPDIR directories. Git
# runs from /usr/bin with system and global configuration, hooks and replace
# objects disabled. The scanned objects are fetched into a private bare
# repository first, so the source clone's configuration, hooks and other refs
# do not reach the scan. Every check fails closed.
set -euo pipefail
umask 077
export LC_ALL=C

# Pins. pins.txt beside this script is the record; bump them together there.
readonly TRUFFLEHOG_VERSION=3.99.0
readonly TRUFFLEHOG_BINARY_SHA256=bcbdd2627c3f96e641edec60e3ccf36fc12afa4ffead5f32c98f8dbe7373cedc
readonly TRUFFLEHOG_FLAGS=(
  "--results=verified,unknown,unverified"
  --exclude-detectors=Lob
  --fail-on-scan-errors
)
readonly SEMGREP_VERSION=1.183.0
readonly SEMGREP_CORE_SHA256=e19fedac1f7c292522b498a8f8394361e6ed389aeef9dd754c26d181bf3d8460
readonly SEMGREP_RULES_COMMIT=16b9e6d45f10649f6a531ec4838ed9924372c3bc
readonly SEMGREP_RULES_REPOSITORY=https://github.com/semgrep/semgrep-rules.git
readonly SEMGREP_CONFIGS=(
  python/lang
  python/correctness
  python/jinja2
  python/jwt
  python/requests
  python/sh
  generic/secrets
  bash/lang
  yaml/github-actions
  yaml/kubernetes
)
# Files the configured languages cover by name. Each one must be scanned or
# skipped for an allowed reason; generic/secrets also reads other text files.
readonly SEMGREP_COVERED_NAMES=('*.py' '*.pyi' '*.sh' '*.bash' '*.yml' '*.yaml')
# Skip reasons that match sast.yml's exclusions: Semgrep's built-in ignore
# list and its default 1 MB target limit. Any other reason blocks.
readonly SEMGREP_ALLOWED_SKIPS='["semgrepignore_patterns_match","exceeded_size_limit"]'
readonly CLEARANCE_SCHEMA=machinery-prepublication-clearance/v1
readonly DIGEST_HEADER="machinery-prepublication-gate history-digest v1"

readonly EXIT_CLEAR=0 EXIT_BLOCKED=1 EXIT_USAGE=2 EXIT_FAIL_CLOSED=3

prog="${0##*/}"
caller_path="${PATH:-}"
PATH=/usr/bin:/bin
export PATH

usage() {
  cat <<EOF
Usage: $prog scan --repo DIR --ref REF [--ref REF ...] --out DIR --semgrep-venv DIR
          [--trufflehog BIN] [--rules-source URL]
       $prog verify --repo DIR --ref REF [--ref REF ...] --clearance FILE
       $prog --help

Pre-publication secret and SAST gate for the first content push to the public
learn-ukrainian/machinery repository (amendment PUBLIC-1104 item 3).
Use it on the rewritten clone, after filter-repo and before any push; it does
not replace the repository's PR and merge checks after publication.

Commands:
  scan     Scan every proposed ref and write clearance.json on a pass.
  verify   Check that a clearance still matches the clone and the proposed
           refs. Run it immediately before the push.

Options:
  --repo DIR          The rewritten clone (bare or non-bare). Required. It must
                      not be shallow, grafted or a partial clone.
  --ref REF           A full ref name proposed for the push, for example
                      refs/heads/main or refs/tags/v1.0.0. Repeat it once per
                      ref; the list must be exactly the refs you will push.
                      Required.
  --out DIR           Private output directory, created with mode 0700. It must
                      not exist yet and must not be inside a git work tree or
                      the clone. Required for scan; for example
                      "\$STATE_DIR/machinery-gate/\$(date -u +%Y%m%dT%H%M%SZ)".
  --semgrep-venv DIR  The hash-locked Semgrep $SEMGREP_VERSION virtual
                      environment (DIR/bin/semgrep). Required for scan.
  --trufflehog BIN    TruffleHog $TRUFFLEHOG_VERSION executable. Default: trufflehog
                      on the caller's PATH. Its SHA-256 must equal the pin.
  --rules-source URL  Where to fetch semgrep-rules from. Default:
                      $SEMGREP_RULES_REPOSITORY.
                      A local mirror is accepted; the checkout must still be
                      commit $SEMGREP_RULES_COMMIT.
  --clearance FILE    The clearance.json a scan wrote. Required for verify.
  -h, --help          Show this help and exit 0.

Examples:
  packaging/machinery-security/$prog scan --repo ../machinery-rewritten \\
    --ref refs/heads/main --out "\$STATE_DIR/machinery-gate/run-1" \\
    --semgrep-venv "\$TOOLS_DIR/semgrep-$SEMGREP_VERSION"
  packaging/machinery-security/$prog verify --repo ../machinery-rewritten \\
    --ref refs/heads/main --clearance "\$STATE_DIR/machinery-gate/run-1/clearance.json"

What scan checks:
  TruffleHog $TRUFFLEHOG_VERSION with
    ${TRUFFLEHOG_FLAGS[*]}
    --exclude-paths=<.trufflehogignore beside this script> --fail --no-update:
    the git source once per ref over all history reachable from it, and the
    filesystem source over every distinct (path, blob) version in that history
    (the git source skips content that only a merge commit introduces). In
    the filesystem pass a version's path is <work dir>/history/N/<path>, so an
    ignore pattern anchored to the repository root excludes nothing there.
  Semgrep $SEMGREP_VERSION with --strict --error --metrics=off and the configs
    ${SEMGREP_CONFIGS[*]}
    from semgrep-rules $SEMGREP_RULES_COMMIT, over each ref's final
    tree and over every distinct (path, blob) version in the reachable history,
    with Semgrep's built-in ignore list and 1 MB target limit as in sast.yml.
  Blocks on: any finding; a missing or mismatched scanner, rules commit, rule
  directory or ignore file; a missing ref or object; a shallow, grafted or
  partial clone; a ref that moved during the scan; a non-commit ref target; a
  submodule (gitlink) entry; a .semgrepignore anywhere in the history; a
  scanner exit other than clean or findings; malformed output; a covered file
  (${SEMGREP_COVERED_NAMES[*]}) that Semgrep neither scanned nor skipped for
  an allowed reason; and blob enumeration that disagrees with git rev-list.

History digest (v1):
  sha256 of the text "$DIGEST_HEADER", then
  "object-format <sha1|sha256>", then "ref <name> <object id>" for each ref
  sorted by name, then "object <id>" for every object 'git rev-list --objects'
  reaches from the refs (commits, trees, blobs and tag objects), sorted and
  unique; one LF-terminated line each.

Outputs (scan, all inside --out, mode 0700):
  summary.json         Decision, ref map, digest and counts. No raw findings.
  clearance.json       Written only on a pass.
  refs.txt             Ref index used in the file names below.
  trufflehog/ref-N.*, trufflehog/history.*
                       Raw TruffleHog results (.jsonl) and stderr (.stderr).
  semgrep/tree-N.*, semgrep/history.*
                       Raw Semgrep results (.json) and stderr (.stderr).
  The scan workspace (fetched objects, checked-out sources, rules) is deleted
  on exit. Standard output carries progress and counts only.
  verify writes nothing.

Exit codes:
  0  scan: cleared, clearance.json written. verify: the clearance matches.
  1  scan: blocked by findings. verify: the clearance is refused.
  2  Usage error; nothing was scanned.
  3  scan: blocked, fail-closed (missing input, scanner error, malformed
     output or unclassified result). verify: missing tool or unreadable clone.

Related:
  packaging/machinery-security/pins.txt (pins and their upstream evidence),
  secret-scan.yml and sast.yml (the repository's own checks after publication),
  .trufflehogignore (the reviewed exclusions); amendment PUBLIC-1104 item 3.
EOF
}

die_usage() {
  printf '%s: %s\n' "$prog" "$1" >&2
  printf 'Run %s --help for usage.\n' "$prog" >&2
  exit "$EXIT_USAGE"
}

log() { printf '%s: %s\n' "$prog" "$*"; }

# Fail-closed stop before any scan result exists.
abort() {
  log "BLOCKED (fail-closed): $*"
  exit "$EXIT_FAIL_CLOSED"
}

fail_closed_count=0
findings_count=0
fail_closed_reasons=()
note_fail_closed() {
  fail_closed_count=$((fail_closed_count + 1))
  fail_closed_reasons+=("$1")
  log "fail-closed: $1"
}

# git with a fixed environment: no system or global config, no hooks, no
# replace objects, no prompts. Extra VAR=value settings come before `--`.
gitx() {
  local -a extra=()
  while [ "$#" -gt 0 ] && [ "$1" != "--" ]; do
    extra+=("$1")
    shift
  done
  shift
  env -i PATH=/usr/bin:/bin HOME=/nonexistent LC_ALL=C \
    GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_NO_REPLACE_OBJECTS=1 \
    GIT_TERMINAL_PROMPT=0 GIT_OPTIONAL_LOCKS=0 GIT_NO_LAZY_FETCH=1 "${extra[@]}" \
    /usr/bin/git -c core.hooksPath=/dev/null -c core.fsmonitor=false \
    -c protocol.file.allow=always "$@"
}

sha256_of() { sha256sum -- "$1" | cut -d' ' -f1; }

require_tools() {
  local tool
  for tool in /usr/bin/git /usr/bin/jq /usr/bin/sha256sum /usr/bin/sort /usr/bin/comm /usr/bin/find; do
    [ -x "$tool" ] || abort "required tool $tool is missing"
  done
}

# --- arguments ---------------------------------------------------------------

[ "$#" -gt 0 ] || { usage >&2; exit "$EXIT_USAGE"; }
case "$1" in
  -h | --help) usage; exit 0 ;;
  scan | verify) mode="$1"; shift ;;
  *) die_usage "unknown command: $1" ;;
esac

repo="" out="" semgrep_venv="" trufflehog_bin="" clearance=""
rules_source="$SEMGREP_RULES_REPOSITORY"
refs=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h | --help) usage; exit 0 ;;
    --repo | --ref | --out | --semgrep-venv | --trufflehog | --rules-source | --clearance)
      [ "$#" -ge 2 ] && [ -n "$2" ] || die_usage "$1 needs a value"
      case "$1" in
        --repo) repo="$2" ;;
        --ref) refs+=("$2") ;;
        --out) out="$2" ;;
        --semgrep-venv) semgrep_venv="$2" ;;
        --trufflehog) trufflehog_bin="$2" ;;
        --rules-source) rules_source="$2" ;;
        --clearance) clearance="$2" ;;
      esac
      shift 2
      ;;
    *) die_usage "unknown argument: $1" ;;
  esac
done

[ -n "$repo" ] || die_usage "--repo is required"
[ "${#refs[@]}" -gt 0 ] || die_usage "at least one --ref is required"
if [ "$mode" = scan ]; then
  [ -n "$out" ] || die_usage "--out is required for scan"
  [ -n "$semgrep_venv" ] || die_usage "--semgrep-venv is required for scan"
  [ -z "$clearance" ] || die_usage "--clearance belongs to verify"
else
  [ -n "$clearance" ] || die_usage "--clearance is required for verify"
  [ -z "$out$semgrep_venv$trufflehog_bin" ] || die_usage "verify takes only --repo, --ref and --clearance"
fi

declare -A seen_ref=()
for ref in "${refs[@]}"; do
  case "$ref" in
    refs/*) ;;
    *) die_usage "--ref must be a full ref name starting with refs/: $ref" ;;
  esac
  gitx -- check-ref-format "$ref" || die_usage "--ref is not a valid ref name: $ref"
  [ -z "${seen_ref[$ref]:-}" ] || die_usage "--ref given twice: $ref"
  seen_ref[$ref]=1
done
mapfile -t refs < <(printf '%s\n' "${refs[@]}" | sort)

require_tools

# --- the clone ----------------------------------------------------------------

[ -d "$repo" ] || abort "--repo is not a directory"
git_dir="$(gitx -- -C "$repo" rev-parse --absolute-git-dir 2> /dev/null)" ||
  abort "--repo is not a git repository"
[ "$(gitx -- --git-dir="$git_dir" rev-parse --is-shallow-repository)" = false ] ||
  abort "the clone is shallow; its history is incomplete"
[ ! -e "$git_dir/info/grafts" ] || abort "the clone has info/grafts; its history is rewritten locally"
if gitx -- --git-dir="$git_dir" config --get extensions.partialclone > /dev/null; then
  abort "the clone is a partial clone; objects may be missing"
fi
object_format="$(gitx -- --git-dir="$git_dir" rev-parse --show-object-format)"

# Prints "<object id> <ref>" for each proposed ref, sorted by ref name.
resolve_refs() {
  local ref line
  for ref in "${refs[@]}"; do
    line="$(gitx -- --git-dir="$git_dir" show-ref --verify -- "$ref" 2> /dev/null)" || return 1
    printf '%s\n' "$line"
  done
}

# Writes the digest input for the refs in $1 (lines "<id> <ref>") from the
# repository at git dir $2 to stdout. Fails if any reachable object is missing.
digest_input() {
  local ref_map="$1" dir="$2" ids
  printf '%s\n' "$DIGEST_HEADER" "object-format $object_format"
  awk '{ print "ref " $2 " " $1 }' "$ref_map"
  ids="$(awk '{ print $1 }' "$ref_map")"
  # shellcheck disable=SC2086 # object ids are hex words
  gitx -- --git-dir="$dir" rev-list --objects --no-object-names --missing=error $ids |
    sort -u | sed 's/^/object /'
}

if [ "$mode" = verify ]; then
  [ -f "$clearance" ] || { log "REFUSED: clearance file not found"; exit "$EXIT_BLOCKED"; }
  if ! jq -e --arg schema "$CLEARANCE_SCHEMA" '
      type == "object" and .schema == $schema and .result == "clear"
      and (.refs | type == "object") and (.history_digest | type == "string")
      and (.object_format | type == "string")' "$clearance" > /dev/null 2>&1; then
    log "REFUSED: the clearance is malformed or is not a pass"
    exit "$EXIT_BLOCKED"
  fi
  cleared_refs="$(jq -r '.refs | keys[]' "$clearance" | sort)"
  if [ "$cleared_refs" != "$(printf '%s\n' "${refs[@]}")" ]; then
    log "REFUSED: the proposed refs differ from the cleared refs"
    exit "$EXIT_BLOCKED"
  fi
  if [ "$(jq -r '.object_format' "$clearance")" != "$object_format" ]; then
    log "REFUSED: the clone's object format differs from the cleared one"
    exit "$EXIT_BLOCKED"
  fi
  vtmp="$(mktemp -d)"
  trap 'rm -rf "$vtmp"' EXIT
  if ! resolve_refs > "$vtmp/refs"; then
    log "REFUSED: a proposed ref no longer exists in the clone"
    exit "$EXIT_BLOCKED"
  fi
  while read -r id ref; do
    if [ "$(jq -r --arg r "$ref" '.refs[$r]' "$clearance")" != "$id" ]; then
      log "REFUSED: $ref moved since the clearance (now $id)"
      exit "$EXIT_BLOCKED"
    fi
  done < "$vtmp/refs"
  if ! digest_input "$vtmp/refs" "$git_dir" > "$vtmp/digest-input"; then
    abort "the clone's history could not be enumerated"
  fi
  digest="sha256:$(sha256_of "$vtmp/digest-input")"
  if [ "$digest" != "$(jq -r '.history_digest' "$clearance")" ]; then
    log "REFUSED: the history digest no longer matches the clearance"
    exit "$EXIT_BLOCKED"
  fi
  log "VERIFIED: ${#refs[@]} ref(s) and history digest $digest match the clearance"
  exit "$EXIT_CLEAR"
fi

# --- scan: output directory ---------------------------------------------------

case "$out" in /*) ;; *) out="$PWD/$out" ;; esac
[ ! -e "$out" ] && [ ! -L "$out" ] || die_usage "--out already exists; use a new directory"
out_parent="$(dirname "$out")"
[ -d "$out_parent" ] || die_usage "the parent of --out does not exist"
out_parent="$(cd "$out_parent" && pwd -P)"
if gitx -- -C "$out_parent" rev-parse --is-inside-work-tree > /dev/null 2>&1 ||
  gitx -- -C "$out_parent" rev-parse --is-inside-git-dir 2> /dev/null | grep -qx true; then
  die_usage "--out must not be inside a git repository"
fi
repo_real="$(cd "$repo" && pwd -P)"
case "$out_parent/" in "$repo_real"/* | "$git_dir"/*) die_usage "--out must not be inside the clone" ;; esac
out="$out_parent/$(basename "$out")"
mkdir -m 700 -- "$out"
work="$out/work"
mkdir -m 700 "$work" "$work/home" "$work/tmp" "$out/trufflehog" "$out/semgrep"
trap 'rm -rf "$work"' EXIT
log "output directory: $out"

# --- scan: tools ---------------------------------------------------------------

if [ -z "$trufflehog_bin" ]; then
  trufflehog_bin="$(PATH="$caller_path" command -v trufflehog 2> /dev/null)" ||
    abort "trufflehog is not on PATH; pass --trufflehog"
fi
[ -f "$trufflehog_bin" ] && [ -x "$trufflehog_bin" ] || abort "the TruffleHog executable is missing"
trufflehog_sha="$(sha256_of "$trufflehog_bin")"
[ "$trufflehog_sha" = "$TRUFFLEHOG_BINARY_SHA256" ] ||
  abort "the TruffleHog executable is not the pinned $TRUFFLEHOG_VERSION release binary"
reported="$(env -i PATH=/usr/bin:/bin HOME="$work/home" TMPDIR="$work/tmp" \
  "$trufflehog_bin" --version 2>&1)" || abort "trufflehog --version failed"
[ "$reported" = "trufflehog $TRUFFLEHOG_VERSION" ] || abort "TruffleHog reports a version other than $TRUFFLEHOG_VERSION"

semgrep_bin="$semgrep_venv/bin/semgrep"
[ -f "$semgrep_bin" ] && [ -x "$semgrep_bin" ] || abort "the Semgrep venv has no bin/semgrep"
semgrep_core=""
for candidate in "$semgrep_venv"/lib/python3*/site-packages/semgrep/bin/semgrep-core; do
  [ -f "$candidate" ] && semgrep_core="$candidate"
done
[ -n "$semgrep_core" ] || abort "the Semgrep venv has no semgrep-core engine"
[ "$(sha256_of "$semgrep_core")" = "$SEMGREP_CORE_SHA256" ] ||
  abort "the Semgrep engine is not the pinned $SEMGREP_VERSION wheel's semgrep-core"
semgrep_env=(env -i PATH="$semgrep_venv/bin:/usr/bin:/bin" HOME="$work/home" TMPDIR="$work/tmp"
  PYTHONSAFEPATH=1 SEMGREP_SEND_METRICS=off SEMGREP_ENABLE_VERSION_CHECK=0)
reported="$(cd "$work/tmp" && "${semgrep_env[@]}" "$semgrep_bin" --version 2> /dev/null)" ||
  abort "semgrep --version failed"
[ "$reported" = "$SEMGREP_VERSION" ] || abort "Semgrep reports a version other than $SEMGREP_VERSION"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ignore_src="$script_dir/.trufflehogignore"
[ -f "$ignore_src" ] || abort "the reviewed .trufflehogignore is missing beside the gate"
ignore_file="$work/trufflehogignore"
cp -- "$ignore_src" "$ignore_file"
ignore_sha="$(sha256_of "$ignore_file")"
gate_sha="$(sha256_of "${BASH_SOURCE[0]}")"
log "tools: trufflehog $TRUFFLEHOG_VERSION and semgrep $SEMGREP_VERSION match their pins"

# --- scan: refs and the private object store ------------------------------------

resolve_refs > "$out/refmap" 2> /dev/null || abort "a proposed ref does not exist in the clone"
# Non-bare, because TruffleHog's git source needs a .git directory; its work
# tree stays empty.
scan_repo="$work/scan"
gitx -- init --quiet --object-format="$object_format" "$scan_repo"
scan_git="$scan_repo/.git"
: > "$out/refs.txt"
declare -a ref_ids=() ref_commits=()
i=0
while read -r id ref; do
  i=$((i + 1))
  # The source ref name is fetched, then checked against the recorded id, so
  # a ref that moves between the two reads blocks instead of being mixed up.
  gitx -- --git-dir="$scan_git" fetch --quiet --no-tags --no-write-fetch-head \
    "$git_dir" "+$ref:refs/gate/ref-$i" ||
    abort "fetching $ref into the private store failed"
  [ "$(gitx -- --git-dir="$scan_git" rev-parse --verify "refs/gate/ref-$i")" = "$id" ] ||
    abort "$ref moved while it was being fetched"
  commit="$(gitx -- --git-dir="$scan_git" rev-parse --verify --quiet "$id^{commit}")" ||
    abort "$ref does not point to a commit"
  gitx -- --git-dir="$scan_git" update-ref "refs/heads/gate-ref-$i" "$commit"
  ref_ids+=("$id")
  ref_commits+=("$commit")
  printf 'ref-%d %s %s\n' "$i" "$ref" "$id" >> "$out/refs.txt"
  log "ref-$i: $ref = $id"
done < "$out/refmap"
ref_count="$i"
# TruffleHog's git source also reads the index; an empty one is enough.
gitx -- -C "$scan_repo" read-tree --empty

digest_input "$out/refmap" "$scan_git" > "$work/digest-input" ||
  abort "the history reachable from the refs could not be enumerated"
digest_input "$out/refmap" "$git_dir" > "$work/digest-input-source" ||
  abort "the clone's history could not be enumerated"
cmp -s "$work/digest-input" "$work/digest-input-source" ||
  abort "the private object store and the clone disagree about the reachable history"
history_digest="sha256:$(sha256_of "$work/digest-input")"
grep '^object ' "$work/digest-input" | cut -d' ' -f2 |
  gitx -- --git-dir="$scan_git" cat-file --batch-check='%(objectname) %(objecttype)' \
    > "$work/object-types" || abort "the reachable objects could not be read"
if grep -qv -E '^[0-9a-f]+ (commit|tree|blob|tag)$' "$work/object-types"; then
  abort "a reachable object is missing or has an unknown type"
fi
count_type() { awk -v t="$1" '$2 == t' "$work/object-types" | wc -l; }
n_commits="$(count_type commit)" n_trees="$(count_type tree)"
n_blobs="$(count_type blob)" n_tags="$(count_type tag)"
log "history: $n_commits commit(s), $n_trees tree(s), $n_blobs blob(s), $n_tags tag object(s); digest $history_digest"


# --- scan: historical versions ----------------------------------------------------

empty_tree="$(gitx -- --git-dir="$scan_git" hash-object -t tree /dev/null)"
# Check out an index into a directory. Attributes come from the empty tree, so
# no in-tree .gitattributes filter or conversion applies, and symlinks become
# regular files holding the link text.
checkout_index() {
  local index="$1" dest="$2"
  mkdir -p "$dest"
  gitx GIT_INDEX_FILE="$index" GIT_WORK_TREE="$dest" GIT_ATTR_SOURCE="$empty_tree" -- \
    --git-dir="$scan_git" -c core.symlinks=false -c core.autocrlf=false \
    checkout-index --all --force
}

# Every distinct (path, blob) version: the root listing of each root commit
# plus each commit's changes against every parent covers every tree entry of
# every reachable commit, including content a merge introduces. The resulting
# blob set must equal rev-list's. Version N is checked out as N/<path>, so
# Semgrep's unanchored built-in ignore patterns apply as they do to the tree.
gitx -- --git-dir="$scan_git" rev-list "${ref_commits[@]}" |
  gitx -- --git-dir="$scan_git" diff-tree --stdin -r -z --root -m --no-renames --no-commit-id \
    > "$work/raw-diffs" || abort "the history could not be listed"
gitlinks=0 odd_modes=0 ignore_files=0
while IFS= read -r -d '' meta && IFS= read -r -d '' path; do
  meta="${meta#:}"
  read -r _ new_mode _ new_id _ <<< "$meta"
  case "$new_mode" in
    000000) continue ;;
    100644 | 100755 | 120000) ;;
    160000) gitlinks=$((gitlinks + 1)); continue ;;
    *) odd_modes=$((odd_modes + 1)); continue ;;
  esac
  case "/$path" in */.semgrepignore) ignore_files=$((ignore_files + 1)) ;; esac
  printf '%s\t%s\0' "$new_id" "$path"
done < "$work/raw-diffs" > "$work/pairs-unsorted"
sort -z -u "$work/pairs-unsorted" > "$work/pairs"
[ "$gitlinks" -eq 0 ] || note_fail_closed "the history has $gitlinks submodule (gitlink) entr(ies) whose content is outside the scan"
[ "$odd_modes" -eq 0 ] || note_fail_closed "the history has $odd_modes tree entr(ies) with an unknown mode"
[ "$ignore_files" -eq 0 ] || note_fail_closed "the history has $ignore_files .semgrepignore version(s); exclusions would differ from sast.yml's"
n_pairs=0
while IFS= read -r -d '' pair; do
  n_pairs=$((n_pairs + 1))
  printf '%s\n' "${pair%%$'\t'*}" >&3
  printf '100644 %s\t%d/%s\0' "${pair%%$'\t'*}" "$n_pairs" "${pair#*$'\t'}"
done < "$work/pairs" > "$work/history.index-info" 3> "$work/pair-blobs-unsorted"
sort -u "$work/pair-blobs-unsorted" > "$work/pair-blobs"
awk '$2 == "blob" { print $1 }' "$work/object-types" | sort -u > "$work/rev-list-blobs"
cmp -s "$work/pair-blobs" "$work/rev-list-blobs" ||
  note_fail_closed "the (path, blob) enumeration disagrees with git rev-list's blob set"
log "history versions: $n_pairs distinct (path, blob) pair(s)"
history_src="$work/src/history"
if [ "$n_pairs" -gt 0 ]; then
  gitx GIT_INDEX_FILE="$work/history.index" -- --git-dir="$scan_git" \
    update-index -z --index-info < "$work/history.index-info"
  checkout_index "$work/history.index" "$history_src"
else
  history_src=""
  note_fail_closed "no historical source versions were found"
fi

# --- scan: TruffleHog -----------------------------------------------------------

trufflehog_findings=0
# Run TruffleHog with source arguments "$@" and record results as $name.
run_trufflehog() {
  local name="$1" results diagnostics rc count summary
  shift
  results="$out/trufflehog/$name.jsonl"
  diagnostics="$out/trufflehog/$name.stderr"
  set +e
  (cd "$work/tmp" && env -i PATH=/usr/bin:/bin HOME="$work/home" TMPDIR="$work/tmp" \
    "$trufflehog_bin" "$@" --fail --no-update --json "${TRUFFLEHOG_FLAGS[@]}" \
    --exclude-paths="$ignore_file") > "$results" 2> "$diagnostics"
  rc=$?
  set -e
  # Every stdout line must be one JSON object; jq's own errors can quote the
  # input, so they are discarded.
  if ! count="$(jq -e -s 'if all(.[]; type == "object") then length else error("x") end' \
    "$results" 2> /dev/null)"; then
    note_fail_closed "TruffleHog output for $name is malformed (exit $rc)"
    return 0
  fi
  summary="$(jq -R -c 'fromjson? | select(type == "object" and .msg == "finished scanning")
    | select((.chunks | type) == "number" and (.verified_secrets | type) == "number"
      and (.unverified_secrets | type) == "number")
    | {chunks, verified_secrets, unverified_secrets}' "$diagnostics" 2> /dev/null || true)"
  if [ -z "$summary" ] || [ "$(printf '%s\n' "$summary" | wc -l)" -ne 1 ]; then
    note_fail_closed "TruffleHog did not report one completed scan for $name (exit $rc)"
    return 0
  fi
  log "trufflehog $name: exit $rc, $count finding(s); summary $summary"
  case "$rc" in
    0) [ "$count" -eq 0 ] || note_fail_closed "TruffleHog reported findings with exit 0 for $name" ;;
    183) [ "$count" -gt 0 ] || note_fail_closed "TruffleHog exited 183 without findings for $name" ;;
    *) note_fail_closed "TruffleHog exited $rc for $name (scan error)" ;;
  esac
  trufflehog_findings=$((trufflehog_findings + count))
}

# The git source scans each ref's commits and diffs. It does not read content
# that only a merge commit introduces, so the filesystem source also scans
# every historical version checked out above.
for ((i = 1; i <= ref_count; i++)); do
  run_trufflehog "ref-$i" git "file://$scan_repo" --branch "${ref_commits[$((i - 1))]}"
done
if [ -n "$history_src" ]; then
  run_trufflehog history filesystem "$history_src"
fi
findings_count=$((findings_count + trufflehog_findings))

# --- scan: Semgrep rules ---------------------------------------------------------

rules="$work/semgrep-rules"
gitx -- init --quiet "$rules"
gitx -- -C "$rules" fetch --quiet --depth 1 --no-tags "$rules_source" "$SEMGREP_RULES_COMMIT" ||
  abort "semgrep-rules commit $SEMGREP_RULES_COMMIT could not be fetched"
gitx -- -C "$rules" -c advice.detachedHead=false checkout --quiet FETCH_HEAD ||
  abort "semgrep-rules could not be checked out"
[ "$(gitx -- -C "$rules" rev-parse HEAD)" = "$SEMGREP_RULES_COMMIT" ] ||
  abort "semgrep-rules is not at commit $SEMGREP_RULES_COMMIT"
[ -z "$(gitx -- -C "$rules" status --porcelain --untracked-files=all)" ] ||
  abort "the semgrep-rules checkout is not clean"
semgrep_args=()
for config in "${SEMGREP_CONFIGS[@]}"; do
  dir="$rules/$config"
  if [ ! -d "$dir" ] || [ -z "$(find "$dir" -name '*.yaml' -print -quit)" ]; then
    abort "rule config $config is missing from the semgrep-rules checkout"
  fi
  semgrep_args+=(--config "$dir")
done
log "semgrep-rules: commit $SEMGREP_RULES_COMMIT, ${#SEMGREP_CONFIGS[@]} configs"

# --- scan: Semgrep ----------------------------------------------------------------

semgrep_findings=0
# Scan directory $1 and record results under the name $2.
run_semgrep() {
  local src="$1" name="$2" rc results diagnostics findings errors missing bad_skips covered
  results="$out/semgrep/$name.json"
  diagnostics="$out/semgrep/$name.stderr"
  set +e
  (cd "$src" && "${semgrep_env[@]}" "$semgrep_bin" scan "${semgrep_args[@]}" \
    --metrics=off --disable-version-check --strict --error --verbose \
    --json --output "$results" .) > /dev/null 2> "$diagnostics"
  rc=$?
  set -e
  if ! jq -s -e 'length == 1 and (.[0] | type == "object"
        and (.results | type) == "array" and (.errors | type) == "array"
        and (.paths | type) == "object" and (.paths.scanned | type) == "array"
        and ((.paths.skipped // []) | type) == "array")' "$results" > /dev/null 2>&1; then
    note_fail_closed "Semgrep output for $name is missing or malformed (exit $rc)"
    return 0
  fi
  findings="$(jq '.results | length' "$results")"
  errors="$(jq '.errors | length' "$results")"
  # Coverage: every file the configured languages cover is scanned or skipped
  # for an allowed reason, and no file is skipped for any other reason.
  bad_skips="$(jq --argjson ok "$SEMGREP_ALLOWED_SKIPS" \
    '[(.paths.skipped // [])[] | select((.reason as $r | $ok | index($r)) == null)] | length' \
    "$results")"
  local -a name_args=()
  local pattern
  for pattern in "${SEMGREP_COVERED_NAMES[@]}"; do
    [ "${#name_args[@]}" -eq 0 ] || name_args+=(-o)
    name_args+=(-name "$pattern")
  done
  (cd "$src" && find . -type f \( "${name_args[@]}" \) -printf '%P\0') | sort -z > "$work/$name.expected"
  covered="$(tr -cd '\0' < "$work/$name.expected" | wc -c)"
  jq -j --argjson ok "$SEMGREP_ALLOWED_SKIPS" '
    (.paths.scanned[] | strings),
    ((.paths.skipped // [])[] | select(.reason as $r | $ok | index($r)) | .path | strings)
    | . + "\u0000"' "$results" | sort -z -u > "$work/$name.accounted"
  missing="$(comm -z -23 "$work/$name.expected" "$work/$name.accounted" | tr -cd '\0' | wc -c)"
  log "semgrep $name: exit $rc, $findings finding(s), $errors error(s), $covered covered file(s), $missing unaccounted, $bad_skips unclassified skip(s)"
  [ "$missing" -eq 0 ] || note_fail_closed "Semgrep $name left $missing covered file(s) unscanned"
  [ "$bad_skips" -eq 0 ] || note_fail_closed "Semgrep $name skipped $bad_skips file(s) for an unclassified reason"
  [ "$errors" -eq 0 ] || note_fail_closed "Semgrep $name reported $errors scan error(s)"
  case "$rc" in
    0) [ "$findings" -eq 0 ] || note_fail_closed "Semgrep $name reported findings with exit 0" ;;
    1) [ "$findings" -gt 0 ] || [ "$errors" -gt 0 ] ||
      note_fail_closed "Semgrep $name exited 1 without findings or errors" ;;
    *) note_fail_closed "Semgrep $name exited $rc (scan error)" ;;
  esac
  semgrep_findings=$((semgrep_findings + findings))
}

for ((i = 1; i <= ref_count; i++)); do
  index="$work/tree-$i.index"
  gitx GIT_INDEX_FILE="$index" -- --git-dir="$scan_git" read-tree "${ref_commits[$((i - 1))]}"
  checkout_index "$index" "$work/src/tree-$i"
  run_semgrep "$work/src/tree-$i" "tree-$i"
  rm -rf "$work/src/tree-$i"
done
if [ -n "$history_src" ]; then
  run_semgrep "$history_src" history
  rm -rf "$history_src"
fi
findings_count=$((findings_count + semgrep_findings))


# --- scan: decision ----------------------------------------------------------------

if ! resolve_refs > "$work/refmap-after" 2> /dev/null ||
  ! cmp -s "$out/refmap" "$work/refmap-after"; then
  note_fail_closed "a proposed ref moved or disappeared during the scan"
fi

if [ "$fail_closed_count" -gt 0 ]; then
  decision=blocked-fail-closed
  status="$EXIT_FAIL_CLOSED"
elif [ "$findings_count" -gt 0 ]; then
  decision=blocked-findings
  status="$EXIT_BLOCKED"
else
  decision=clear
  status="$EXIT_CLEAR"
fi

ref_json="$(awk '{ print $2 "\t" $1 }' "$out/refmap" |
  jq -R -s 'split("\n") | map(select(length > 0) | split("\t") | {(.[0]): .[1]}) | add')"
jq -n \
  --arg schema "$CLEARANCE_SCHEMA" --arg result "$decision" \
  --arg created "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg repo "$repo_real" \
  --arg format "$object_format" --argjson refs "$ref_json" --arg digest "$history_digest" \
  --argjson commits "$n_commits" --argjson trees "$n_trees" --argjson blobs "$n_blobs" \
  --argjson tags "$n_tags" --argjson pairs "$n_pairs" \
  --argjson th "$trufflehog_findings" --argjson sg "$semgrep_findings" \
  --argjson fc "$fail_closed_count" \
  --arg tv "$TRUFFLEHOG_VERSION" --arg tsha "$trufflehog_sha" --arg isha "$ignore_sha" \
  --arg tflags "${TRUFFLEHOG_FLAGS[*]}" \
  --arg sv "$SEMGREP_VERSION" --arg csha "$SEMGREP_CORE_SHA256" \
  --arg rc "$SEMGREP_RULES_COMMIT" --arg configs "${SEMGREP_CONFIGS[*]}" \
  --arg gsha "$gate_sha" \
  '{schema: $schema, result: $result, created_at: $created, repo: $repo,
    object_format: $format, refs: $refs, history_digest: $digest,
    counts: {commits: $commits, trees: $trees, blobs: $blobs, tag_objects: $tags,
      history_versions: $pairs, trufflehog_findings: $th, semgrep_findings: $sg,
      fail_closed_conditions: $fc},
    scanners: {
      trufflehog: {version: $tv, binary_sha256: $tsha, flags: $tflags,
        trufflehogignore_sha256: $isha},
      semgrep: {version: $sv, semgrep_core_sha256: $csha, rules_commit: $rc,
        configs: ($configs | split(" "))}},
    gate_sha256: $gsha}' > "$out/summary.json"
for reason in "${fail_closed_reasons[@]}"; do
  printf '%s\n' "$reason"
done | jq -R -s 'split("\n") | map(select(length > 0))' > "$work/reasons.json"
jq --slurpfile reasons "$work/reasons.json" '. + {fail_closed_reasons: $reasons[0]}' \
  "$out/summary.json" > "$work/summary.json" && mv -f "$work/summary.json" "$out/summary.json"

if [ "$decision" = clear ]; then
  jq 'del(.fail_closed_reasons)' "$out/summary.json" > "$out/clearance.json"
  log "CLEAR: $ref_count ref(s), digest $history_digest; clearance at $out/clearance.json"
  log "Run '$prog verify' with the same --repo and --ref list immediately before the push."
else
  log "BLOCKED ($decision): $trufflehog_findings TruffleHog finding(s), $semgrep_findings Semgrep finding(s), $fail_closed_count fail-closed condition(s). Raw results are in $out."
fi
exit "$status"
