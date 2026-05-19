#!/usr/bin/env bash
# log_tool_call.sh — Hermes post_tool_call shell hook.
#
# Purpose
# -------
# Hermes ``-z`` (one-shot) mode strips tool-call traces from stdout by design
# (oneshot.py docstring: "no banner, no spinner, no tool previews"). The
# Hermes-backed V7 writer adapters (deepseek/qwen/grok) therefore can't see
# what MCP tools fired during a writer call — they return ``tool_calls=[]``
# in their parse result, and the V7 pipeline's ``_load_writer_tool_calls``
# finds nothing. Every Hermes-routed writer build then HARD-rejects on
# ``textbook_grounding`` / ``resources_search_attempted`` with
# ``search_text_calls: 0`` / ``search_attempt_count: 0``, even when the
# calls actually fired.
#
# This hook closes the observability gap without forking Hermes: it fires
# after every MCP-tool call, reads the payload Hermes pipes to stdin, and
# appends one JSON line to ``$cwd/hermes.write.jsonl`` in the writer's
# working directory (which v7_build.py sets to ``module_dir``). The V7
# pipeline already globs ``*.write.jsonl`` (linear_pipeline.py:6882-6883)
# so no pipeline-side changes are needed.
#
# Schema written
# --------------
# Each line is a single JSON object with the fields the gate expects:
#
#   event       = "writer_tool_call"   (filter sentinel for _load_jsonl_tool_calls)
#   tool        = tool_name           (e.g. "mcp_sources_search_text"; the
#                                      gate's normalizer strips the prefix)
#   args        = tool_input dict
#   result      = parsed tool result  (string-or-object; gate handles both)
#   duration_ms = int from extra
#   ts          = epoch seconds       (for debugging — gate ignores)
#
# Hermes contract (per website/docs/user-guide/features/hooks.md):
#   * stdin: JSON payload {hook_event_name, tool_name, tool_input, session_id,
#                          cwd, extra: {duration_ms, result, tool_call_id, ...}}
#   * stdout: ``{}`` (or anything; post_tool_call return values are ignored)
#   * Non-zero exits log a warning but do NOT abort the agent loop —
#     so the hook can be defensive without breaking the writer.
#
# Matcher filtering happens in the hooks.post_tool_call config entry; this
# script also double-checks the prefix in case the matcher widens later.

set -uo pipefail

# Always end with a no-op JSON response so Hermes considers the hook clean.
# Use trap so we never accidentally swallow it from a mid-script return.
emit_noop() { printf '{}\n'; }
trap 'emit_noop' EXIT

payload="$(cat -)" || exit 0

# Robust against jq missing — degrade gracefully.
if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

tool_name="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null || true)"
[[ -z "$tool_name" ]] && exit 0

# Belt-and-braces: only capture MCP-sources calls. Hermes single-underscore
# convention is the canonical one in -z mode; accept double-underscore too
# in case a different writer ever routes through here.
case "$tool_name" in
  mcp_sources_*|mcp__sources__*) : ;;
  *) exit 0 ;;
esac

cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
[[ -z "$cwd" || ! -d "$cwd" ]] && exit 0

log_path="$cwd/hermes.write.jsonl"

# Build one compact JSON line. ``--argjson`` for the structured fields and
# ``--arg`` for the scalars so quoting can't break.
#
# Per Hermes docs the ``result`` field is ALWAYS a JSON-encoded string. The V7
# pipeline's ``_result_items_from_call`` (linear_pipeline.py:6952-6998) only
# unpacks ``list`` / ``Mapping`` / ``{text: str}`` results — it returns ``[]``
# for raw strings. So we attempt ``fromjson`` first and fall back to a
# ``{text: <raw>}`` wrapper so the gate's ``result_excerpt`` path still
# matches when the inner payload isn't valid JSON (defensive).
line="$(
  printf '%s' "$payload" | jq -c \
    --arg tool "$tool_name" \
    --arg ts "$(date +%s)" \
    '{
      event: "writer_tool_call",
      tool: $tool,
      args: (.tool_input // {}),
      result: (
        (.extra.result // null) as $r
        | if ($r | type) == "string" then
            ($r | try fromjson catch {text: $r})
          else
            $r
          end
      ),
      duration_ms: (.extra.duration_ms // null),
      tool_call_id: (.extra.tool_call_id // null),
      session_id: (.session_id // null),
      ts: ($ts | tonumber)
    }' 2>/dev/null || true
)"

[[ -z "$line" ]] && exit 0

# Append atomically. >> on the same FS line is already atomic for small
# (<4KB) writes; for safety we also add a fallback noop on permission
# errors. Concurrent writers in the same cwd are impossible per the V7
# build's one-writer-per-module invariant.
printf '%s\n' "$line" >> "$log_path" 2>/dev/null || true

exit 0
