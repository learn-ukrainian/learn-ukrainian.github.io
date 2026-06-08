#!/usr/bin/env bash
# safe_env.sh — canonical, leak-proof environment probe.
#
# The ONLY sanctioned way to answer "is environment variable X set?" without
# ever exposing its value. Reinforces MEMORY.md #M-5 and the two-incident
# autopsy chain in docs/bug-autopsies/secret-leakage.md (GEMINI_API_KEY 2026-05-10,
# DAGGER_CLOUD_TOKEN 2026-05-12). Both leaks happened because an ad-hoc probe
# (`grep -nH VAR file`, `env | grep VAR`) printed the value verbatim into the
# transcript. This helper NEVER reads a value into stdout/stderr — it only
# reports SET / UNSET via indirect expansion and length tests.
#
# Usage:
#   safe_env.sh check VAR [VAR2 ...]   Print "VAR: SET|UNSET" per var.
#                                      Exit 0 iff every named var is set & non-empty.
#   safe_env.sh is-set VAR             Silent. Exit 0 iff VAR is set & non-empty, else 1.
#   safe_env.sh count VAR [VAR2 ...]   Print "N/M set" only (no names-to-values).
#
# Guarantees:
#   - A variable's value is never expanded into any printed string.
#   - "set" means present AND non-empty ([ -n ]); an exported-but-empty var is UNSET.
#   - No `set -x` / xtrace (would echo values); we explicitly disable it.
set -euo pipefail
set +x  # never trace — xtrace would echo expanded values

usage() {
    sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
}

# Return 0 iff the variable named by $1 is set and non-empty.
# Uses indirect expansion; the value is tested for length only, never printed.
_is_set() {
    local name=$1
    [ -n "${!name:-}" ]
}

main() {
    local cmd=${1:-}
    shift || true

    case "$cmd" in
        check)
            [ "$#" -ge 1 ] || { echo "safe_env.sh: check requires at least one VAR" >&2; exit 2; }
            local all_set=0 name
            for name in "$@"; do
                if _is_set "$name"; then
                    echo "${name}: SET"
                else
                    echo "${name}: UNSET"
                    all_set=1
                fi
            done
            return "$all_set"
            ;;
        is-set)
            [ "$#" -eq 1 ] || { echo "safe_env.sh: is-set requires exactly one VAR" >&2; exit 2; }
            _is_set "$1"
            ;;
        count)
            [ "$#" -ge 1 ] || { echo "safe_env.sh: count requires at least one VAR" >&2; exit 2; }
            local total=$# set_n=0 name
            for name in "$@"; do
                if _is_set "$name"; then
                    set_n=$((set_n + 1))
                fi
            done
            echo "${set_n}/${total} set"
            [ "$set_n" -eq "$total" ]
            ;;
        -h | --help | help | "")
            usage
            ;;
        *)
            echo "safe_env.sh: unknown command: ${cmd}" >&2
            usage >&2
            exit 2
            ;;
    esac
}

main "$@"
