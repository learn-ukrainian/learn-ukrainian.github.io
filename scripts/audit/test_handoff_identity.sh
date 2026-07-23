#!/usr/bin/env bash
# Fixtures for scripts/lib/handoff_identity.sh — the launcher-side derivation of
# SESSION_HANDOFF_AGENT from a Claude Code `--agent` selection. Wired into the
# required pytest gate via tests/test_handoff_identity.py so the agent→slot
# mapping that prevents the infra/folk cold-start collision stays load-bearing.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=scripts/lib/handoff_identity.sh
source "$REPO_ROOT/scripts/lib/handoff_identity.sh"
# shellcheck source=scripts/lib/thread_rollover_link.sh
source "$REPO_ROOT/scripts/lib/thread_rollover_link.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

eq() {
  # eq <actual> <expected> <label>
  if [[ "$1" != "$2" ]]; then
    fail "$3: expected [$2], got [$1]"
  fi
}

# --- argv extraction: spaced + equals forms, position-independent, non-consuming ---
eq "$(handoff_agent_from_argv --chrome --agent infra-orchestrator --foo bar)" "infra-orchestrator" "spaced --agent"
eq "$(handoff_agent_from_argv --agent=infra-orchestrator)" "infra-orchestrator" "equals --agent"
eq "$(handoff_agent_from_argv --permission-mode bypassPermissions --agent curriculum-orchestrator)" "curriculum-orchestrator" "trailing --agent"
eq "$(handoff_agent_from_argv --chrome --permission-mode bypassPermissions)" "" "no --agent flag"
eq "$(handoff_agent_from_argv)" "" "empty argv"

# --- agent → SESSION_HANDOFF_AGENT slot mapping ---
eq "$(handoff_identity_for_agent infra-orchestrator)" "claude-infra" "infra maps to claude-infra"
eq "$(handoff_identity_for_agent curriculum-orchestrator)" "" "curriculum keeps default claude slot"
eq "$(handoff_identity_for_agent)" "" "unset keeps default claude slot"
eq "$(handoff_identity_for_agent some-future-agent)" "" "unknown keeps default claude slot"

# --- end-to-end: the infra agent selection resolves to the claude-infra slot ---
agent="$(handoff_agent_from_argv --chrome --permission-mode bypassPermissions --agent infra-orchestrator)"
eq "$(handoff_identity_for_agent "$agent")" "claude-infra" "e2e: --agent infra-orchestrator → claude-infra"

# --- end-to-end: a folk/curriculum launch resolves to the default (empty) slot ---
agent="$(handoff_agent_from_argv --chrome --agent curriculum-orchestrator)"
eq "$(handoff_identity_for_agent "$agent")" "" "e2e: --agent curriculum-orchestrator → default claude"

# --- epic argv extraction: spaced + equals forms; legacy suffix remains supported ---
eq "$(handoff_epic_from_argv --agent curriculum-orchestrator --epic atlas)" "atlas" "spaced --epic"
eq "$(handoff_epic_from_argv --epic=hramatka)" "hramatka" "equals --epic"
eq "$(handoff_epic_from_argv --epic atlas.epic)" "atlas" "spaced --epic with legacy suffix"
eq "$(handoff_epic_from_argv --epic=harness.epic)" "harness" "equals --epic with legacy suffix"
eq "$(handoff_epic_from_argv --agent curriculum-orchestrator)" "" "no --epic flag"
eq "$(handoff_epic_from_argv)" "" "empty argv (epic)"

# --- selector → canonical lane, stream, and provider slot mapping ---
eq "$(launcher_selector_lane infra.fleet-comms)" "infra" "fleet-comms resolves to infra"
eq "$(launcher_selector_stream infra.devops)" "epic:4707" "devops resolves to infra stream"
eq "$(launcher_selector_lane atlas.practice)" "atlas" "atlas practice resolves to atlas"
eq "$(launcher_selector_stream hramatka.lessons)" "epic:4542" "hramatka lessons resolves"
# corpus is a documented, currently-recommended driver epic
# (docs/runbooks/epic-orchestrator-roster.md: `./start-gemini-drive.sh corpus`) — it must
# stay in the allowlist alongside infra/atlas/hramatka/folk/bio.
eq "$(launcher_selector_lane corpus)" "corpus" "corpus resolves to corpus lane"
eq "$(launcher_selector_stream corpus-channels)" "epic:4706" "corpus-channels resolves to corpus stream"
launcher_selector_resolve unknown && fail "unknown selector must fail closed"

# --- selector → slot mapping: selector beats agent-type; empty selector maps to nothing ---
eq "$(handoff_identity_for_epic atlas)" "claude-atlas" "epic atlas → claude-atlas"
eq "$(handoff_identity_for_epic hramatka)" "claude-hramatka" "epic hramatka → claude-hramatka"
eq "$(handoff_identity_for_epic harness)" "claude-infra" "epic harness → claude-infra (#5201)"
eq "$(handoff_identity_for_epic infra)" "claude-infra" "epic infra → claude-infra alias"
eq "$(handoff_identity_for_epic infra.devops)" "claude-infra" "dot devops → claude-infra alias"
eq "$(handoff_identity_for_epic)" "" "no epic → empty slot"

# Codex uses provider-specific per-epic slots; harness/infra/devops share one alias.
eq "$(handoff_identity_for_codex_epic atlas)" "codex-atlas" "Codex atlas → codex-atlas"
eq "$(handoff_identity_for_codex_epic hramatka)" "codex-hramatka" "Codex hramatka → codex-hramatka"
eq "$(handoff_identity_for_codex_epic harness)" "codex-infra" "Codex harness → codex-infra"
eq "$(handoff_identity_for_codex_epic infra)" "codex-infra" "Codex infra → codex-infra alias"
eq "$(handoff_identity_for_codex_epic infra.devops)" "codex-infra" "Codex dot devops → codex-infra alias"
eq "$(handoff_identity_for_codex_epic)" "" "Codex no epic → empty slot"

# Gemini uses provider-specific per-epic slots; harness/infra/devops share one alias.
eq "$(handoff_identity_for_gemini_epic atlas)" "gemini-atlas" "Gemini atlas → gemini-atlas"
eq "$(handoff_identity_for_gemini_epic hramatka)" "gemini-hramatka" "Gemini hramatka → gemini-hramatka"
eq "$(handoff_identity_for_gemini_epic harness)" "gemini-infra" "Gemini harness → gemini-infra"
eq "$(handoff_identity_for_gemini_epic infra)" "gemini-infra" "Gemini infra → gemini-infra alias"
eq "$(handoff_identity_for_gemini_epic infra.devops)" "gemini-infra" "Gemini dot devops → gemini-infra alias"
eq "$(handoff_identity_for_gemini_epic)" "" "Gemini no epic → empty slot"


# --- e2e: --epic harness resolves the infra lane slot (not phantom claude-harness) ---
epic="$(handoff_epic_from_argv --epic harness --agent infra-orchestrator)"
eq "$(handoff_identity_for_epic "$epic")" "claude-infra" "e2e: --epic harness → claude-infra"
# Phantom claude-harness must NEVER be the resolved slot for this lane.
if [[ "$(handoff_identity_for_epic harness)" == "claude-harness" ]]; then
  fail "harness epic must not invent phantom claude-harness slot (#5201)"
fi

# --- strip: --epic (both forms) removed, everything else preserved in order ---
stripped="$(strip_epic_from_argv --chrome --epic atlas --agent curriculum-orchestrator | tr '\0' ' ')"
eq "$stripped" "--chrome --agent curriculum-orchestrator " "strip spaced --epic"
stripped="$(strip_epic_from_argv --epic=atlas --chrome | tr '\0' ' ')"
eq "$stripped" "--chrome " "strip equals --epic"
stripped="$(strip_epic_from_argv --chrome --agent curriculum-orchestrator | tr '\0' ' ')"
eq "$stripped" "--chrome --agent curriculum-orchestrator " "strip is no-op without --epic"

# --- strip transport is NUL-delimited: args with spaces AND newlines survive ---
args=()
while IFS= read -r -d '' a; do args+=("$a"); done < <(strip_epic_from_argv --epic atlas "two words" $'line1\nline2' --chrome)
eq "${#args[@]}" "3" "NUL transport: arg count preserved"
eq "${args[0]}" "two words" "NUL transport: space arg intact"
eq "${args[1]}" $'line1\nline2' "NUL transport: newline arg intact"
eq "${args[2]}" "--chrome" "NUL transport: trailing flag intact"

# --- epic name validation: sane names pass, path/space/case junk refused ---
epic_name_valid atlas || fail "epic_name_valid: atlas must pass"
epic_name_valid lit-war || fail "epic_name_valid: lit-war must pass"
epic_name_valid "../../etc" && fail "epic_name_valid: traversal must be refused"
epic_name_valid "two words" && fail "epic_name_valid: spaces must be refused"
epic_name_valid "Atlas" && fail "epic_name_valid: uppercase must be refused"
epic_name_valid "-atlas" && fail "epic_name_valid: leading hyphen must be refused"
epic_name_valid "" && fail "epic_name_valid: empty must be refused"

# --- flag-presence: distinguishes "flag absent" from "flag with empty/dangling value" ---
epic_flag_present --chrome --epic && : || fail "epic_flag_present: dangling --epic must be detected"
epic_flag_present --epic= && : || fail "epic_flag_present: --epic= must be detected"
epic_flag_present --epic "" && : || fail "epic_flag_present: --epic '' must be detected"
epic_flag_present --epic atlas && : || fail "epic_flag_present: valued --epic must be detected"
epic_flag_present --chrome --agent curriculum-orchestrator && fail "epic_flag_present: must be false without the flag"
# ...while extraction returns empty for all three malformed forms (the launcher
# pairs these two signals to fail loudly instead of leaking --epic to claude):
eq "$(handoff_epic_from_argv --chrome --epic)" "" "dangling --epic extracts empty"
eq "$(handoff_epic_from_argv --epic=)" "" "--epic= extracts empty"
eq "$(handoff_epic_from_argv --epic '')" "" "--epic '' extracts empty"

# --- e2e: two same-agent-type launches on different epics get DIFFERENT slots ---
epic_a="$(handoff_epic_from_argv --agent curriculum-orchestrator --epic atlas)"
epic_b="$(handoff_epic_from_argv --agent curriculum-orchestrator --epic hramatka)"
if [[ "$(handoff_identity_for_epic "$epic_a")" == "$(handoff_identity_for_epic "$epic_b")" ]]; then
  fail "same-agent different-epic launches must not share a handoff slot"
fi

# --- Codex launcher rollover bridge: narrow, canonical, and fail-loud ---
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT
canonical="$tmp_root/canonical"
worktree="$tmp_root/worktree"
mkdir -p "$canonical" "$worktree"
ensure_thread_rollover_link "$canonical" "$worktree"
[[ -d "$canonical/.agent/thread-rollovers" ]] || fail "first launch creates canonical rollover directory"
[[ -L "$worktree/.agent/thread-rollovers" ]] || fail "first launch creates narrow rollover symlink"
eq "$(readlink "$worktree/.agent/thread-rollovers")" "$canonical/.agent/thread-rollovers" "rollover symlink target"
ensure_thread_rollover_link "$canonical" "$worktree"
rm "$worktree/.agent/thread-rollovers"
mkdir "$worktree/.agent/thread-rollovers"
if ensure_thread_rollover_link "$canonical" "$worktree"; then
  fail "real rollover directory collision must fail"
fi
rm -rf "$worktree/.agent/thread-rollovers"
ln -s "$tmp_root/wrong" "$worktree/.agent/thread-rollovers"
if ensure_thread_rollover_link "$canonical" "$worktree"; then
  fail "wrong or broken rollover symlink must fail"
fi

printf 'ok - handoff identity fixtures passed\n'
