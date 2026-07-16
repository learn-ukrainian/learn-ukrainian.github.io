#!/usr/bin/env bash
# Resolve a validated context profile into allow-listed project-private variables.

resolve_context_profile() {
  local p_id="${1:-}"
  local m_id="${2:-}"
  local project_dir="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
  local resolver_py="${CLAUDE_PROFILE_RESOLVER_PY:-$project_dir/scripts/lib/context_profiles.py}"
  local py_bin="${CLAUDE_PROFILE_RESOLVER_PYTHON:-$project_dir/.venv/bin/python}"
  local output_file key value var_name index
  local parse_error=0
  local field_count=0
  local seen_keys="|"
  local resolved_keys=()
  local resolved_values=()

  if [ ! -f "$resolver_py" ]; then
    echo "Error: Resolver script not found at $resolver_py" >&2
    return 1
  fi
  if [ ! -x "$py_bin" ]; then
    echo "Error: Python binary not found at $py_bin" >&2
    return 1
  fi

  output_file=$(umask 077 && mktemp "${TMPDIR:-/tmp}/context-profile.XXXXXX") || {
    echo "Error: Could not create context-profile output file" >&2
    return 1
  }
  if ! "$py_bin" "$resolver_py" \
    --profile "$p_id" --model "$m_id" --format env0 >"$output_file"; then
    rm -f "$output_file"
    echo "Error: Context-profile resolution failed" >&2
    return 1
  fi

  while IFS= read -r -d '' key; do
    if ! IFS= read -r -d '' value; then
      parse_error=1
      break
    fi
    case "$key" in
      PROFILE_ID|TRANSPORT|MAIN_MODEL_ID|MAIN_CONTEXT_WINDOW_TOKENS|AUTO_COMPACT_CAPACITY_TOKENS|COLD_START_PROFILE|COLD_START_BUDGET_TOKENS|ROLLOVER_WARNING_PERCENTAGES|REQUESTED_PROFILE_ID|REQUESTED_MODEL_ID|RESOLUTION_REASON|TRUSTED|MODEL_MISMATCH|EXPECTED_PROFILE_ID|EXPECTED_MAIN_MODEL_ID|EXPECTED_MAIN_CONTEXT_WINDOW_TOKENS)
        case "$seen_keys" in
          *"|$key|"*)
            parse_error=1
            break
            ;;
        esac
        seen_keys="${seen_keys}${key}|"
        resolved_keys[field_count]="$key"
        resolved_values[field_count]="$value"
        field_count=$((field_count + 1))
        ;;
      *)
        parse_error=1
        break
        ;;
    esac
  done <"$output_file"
  rm -f "$output_file"

  if ((parse_error)) || ((field_count != 16)); then
    echo "Error: Context-profile resolver returned an invalid field stream" >&2
    return 1
  fi

  for ((index = 0; index < field_count; index++)); do
    var_name="LEARN_UKRAINIAN_${resolved_keys[index]}"
    printf -v "$var_name" '%s' "${resolved_values[index]}"
    export "${var_name?}"
  done
}
