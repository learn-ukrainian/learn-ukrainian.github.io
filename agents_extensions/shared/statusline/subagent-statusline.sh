#!/usr/bin/env bash
# Claude Code subagent rows for the Claudex launcher.

set -u

command -v jq >/dev/null 2>&1 || exit 0

input=$(</dev/stdin)

printf '%s' "$input" | jq -rc '
  def compact_tokens:
    if . >= 1000000 then ((. / 1000000 * 10 | floor) / 10 | tostring) + "M"
    elif . >= 1000 then ((. / 1000 | floor) | tostring) + "K"
    else tostring
    end;
  (.columns // 100) as $columns
  | .tasks[]?
  | (.name // .label // .type // "agent") as $name
  | (.status // "unknown") as $status
  | (.description // "") as $description
  | (.tokenCount // 0) as $tokens
  | ("[" + $status + "] " + $name
      + (if $description == "" then "" else ": " + $description end)
      + (if $tokens > 0 then " · " + ($tokens | compact_tokens) + " tok" else "" end)) as $content
  | {id: .id, content: $content[0:$columns]}
'
