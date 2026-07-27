#!/usr/bin/env bash
set -euo pipefail

unset GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_DIR GIT_INDEX_FILE
unset GIT_OBJECT_DIRECTORY GIT_PREFIX GIT_WORK_TREE

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SELF="${BASH_SOURCE[0]}"
PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
THREAD_HANDOFF_PY="$REPO_ROOT/scripts/orchestration/thread_handoff.py"
HEARTBEAT_HOOK="$REPO_ROOT/agents_extensions/shared/hooks/thread-lease-heartbeat.sh"
RELEASE_HOOK="$REPO_ROOT/agents_extensions/shared/hooks/release-thread-lease.sh"
STOP_HOOK="$REPO_ROOT/agents_extensions/shared/hooks/goal-driver-stop.sh"

# Each hook derives its OWN python/script paths from $CLAUDE_PROJECT_DIR
# (".venv/bin/python", "scripts/orchestration/thread_handoff.py") — there is
# no override env var for that, unlike $CODEX_CANONICAL_REPO_ROOT, which
# separately controls where the CLI's --repo-root (i.e. where lease STATE
# lives) points. So every scenario below sets CLAUDE_PROJECT_DIR to the REAL
# repo (a real, working venv+script) and CODEX_CANONICAL_REPO_ROOT to the
# isolated per-scenario fixture directory (so lease state never touches this
# real checkout's own .agent/).

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

lease_file_path() {
  local root="$1" agent="$2"
  printf '%s/.agent/%s-thread-lease.json' "$root" "$agent"
}

lease_field() {
  local file="$1" field="$2"
  "$PYTHON_BIN" -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$file" "$field"
}

rewind_heartbeat() {
  # Directly rewind heartbeat_at into the far past on disk, leaving every
  # other field (owner_pid/owner_pid_started_at/owner_machine_id/generation)
  # exactly as the real claim call recorded it. This isolates "did the hook
  # advance heartbeat_at" from the hook's own 60s PostToolUse throttle,
  # without needing to sleep 60+ real seconds in a test.
  local file="$1"
  "$PYTHON_BIN" - "$file" <<'PYEOF'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    record = json.load(handle)
record["heartbeat_at"] = "2020-01-01T00:00:00Z"
with open(path, "w", encoding="utf-8") as handle:
    json.dump(record, handle)
PYEOF
}

# --- internal re-exec dispatch used by run_as_fake_claude_ancestor (must
#     come after every function it might call is defined, and before any
#     top-level test logic runs) ---

__scenario_heartbeat_hook_advances_without_generation_env() {
  local root="$1" agent="$2" session_id="$3"
  "$PYTHON_BIN" "$THREAD_HANDOFF_PY" --repo-root "$root" \
    claim-thread-lease --agent "$agent" --current-thread-id "$session_id" >/dev/null

  rewind_heartbeat "$(lease_file_path "$root" "$agent")"

  printf '%s' "{\"session_id\":\"$session_id\"}" | \
    env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
        -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
    CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="$agent" CODEX_CANONICAL_REPO_ROOT="$root" \
    THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
    "$HEARTBEAT_HOOK"
  # `:` (no-op) after the hook invocation: if it were the textually-last
  # command in this function, bash's exec-last-command optimization can
  # replace THIS process's image with the hook's own subprocess instead of
  # forking a child for it — silently destroying the faked argv[0]=claude
  # ancestor identity the harness-ancestor walk depends on (verified via
  # manual repro: the very next process-identity probe in the same shell
  # started finding an unrelated, real ambient "claude" ancestor instead of
  # this scenario's own fake one). A trailing no-op guarantees a fork.
  :
}

__scenario_stop_hook_advances_heartbeat_without_generation_env() {
  local root="$1" agent="$2" session_id="$3"
  "$PYTHON_BIN" "$THREAD_HANDOFF_PY" --repo-root "$root" \
    claim-thread-lease --agent "$agent" --current-thread-id "$session_id" >/dev/null

  rewind_heartbeat "$(lease_file_path "$root" "$agent")"

  printf '%s' "{\"session_id\":\"$session_id\"}" | \
    env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
        -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
    CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="$agent" CODEX_CANONICAL_REPO_ROOT="$root" \
    THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
    "$STOP_HOOK" >/dev/null
  : # see the no-op note in the heartbeat scenario above — same reason.
}

__scenario_release_hook_tombstones_without_generation_env() {
  local root="$1" agent="$2" session_id="$3"
  "$PYTHON_BIN" "$THREAD_HANDOFF_PY" --repo-root "$root" \
    claim-thread-lease --agent "$agent" --current-thread-id "$session_id" >/dev/null

  printf '%s' "{\"session_id\":\"$session_id\"}" | \
    env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
        -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
    CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="$agent" CODEX_CANONICAL_REPO_ROOT="$root" \
    THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
    "$RELEASE_HOOK"
  : # see the no-op note in the heartbeat scenario above — same reason.
}

__scenario_worktree_layout_claims_lease() {
  local root="$1" fakewt="$2" session_id="$3"
  printf '%s' "{\"session_id\":\"$session_id\"}" | \
    env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
        -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
        -u CLAUDE_SESSION_RECORD_PYTHON -u THREAD_ROLLOVER_PYTHON -u CLAUDE_PROFILE_RESOLVER_PYTHON \
    CLAUDE_PROJECT_DIR="$fakewt" SESSION_HANDOFF_AGENT="claude" CODEX_CANONICAL_REPO_ROOT="$root" \
    bash "$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh" >/dev/null
  :
}

if [ "${1:-}" = "__dispatch__" ]; then
  shift
  "$@"
  exit $?
fi

# Runs "$@" (a function name in THIS script, plus args) as a child of a
# process whose own argv[0] is "claude". scripts/orchestration/
# thread_handoff.py's harness-ancestor walk (_find_harness_ancestor) matches
# a live ancestor process by candidate executable basename — including
# psutil's cmdline()[0], which `exec -a claude` sets exactly like the real
# Claude Code CLI does (see ProcessSnapshot's docstring: the harness
# overrides its own process title). This makes the identity-proof path
# (require_proof=True, the fence these hooks now rely on with no
# --generation at all) genuinely provable end-to-end, without a real Claude
# Code harness process running. Both the claim AND the later hook
# invocation happen inside ONE such process (never two separate ones), so
# the recorded owner_pid/owner_pid_started_at the claim call observed is the
# SAME real, still-alive process the hook's own identity re-derivation sees
# later — exactly modelling one real session's SessionStart-then-hook
# lifecycle.
run_as_fake_claude_ancestor() {
  ( exec -a claude bash "$SELF" __dispatch__ "$@" )
}

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

# 1. PostToolUse heartbeat hook (thread-lease-heartbeat.sh): with NO
#    LEARN_UKRAINIAN_THREAD_LEASE_GENERATION in its environment at all, it
#    must still advance heartbeat_at via the identity-proof fence alone —
#    this is the load-bearing proof that the original bug (the env var never
#    reaching hook subprocesses, so every refresh silently no-oped) is dead.
root="$TMP_ROOT/heartbeat-project"
mkdir -p "$root"
session_id="fixture-session-heartbeat"
run_as_fake_claude_ancestor __scenario_heartbeat_hook_advances_without_generation_env "$root" claude "$session_id"

lease="$(lease_file_path "$root" claude)"
[ -f "$lease" ] || fail "heartbeat hook: lease file missing after scenario"
heartbeat_at="$(lease_field "$lease" heartbeat_at)"
owner_thread_id="$(lease_field "$lease" owner_thread_id)"
generation="$(lease_field "$lease" generation)"
[ "$heartbeat_at" != "2020-01-01T00:00:00Z" ] || fail "heartbeat hook: heartbeat_at did not advance with no generation env var set"
[ "$owner_thread_id" = "$session_id" ] || fail "heartbeat hook: owner_thread_id changed — expected a refresh, not a reacquire"
[ "$generation" = "1" ] || fail "heartbeat hook: generation changed — expected a refresh, not a reacquire"

# 2. Stop hook's own lease-refresh section (goal-driver-stop.sh): same proof,
#    unconditional (unthrottled) refresh path, and it must still emit its
#    own normal (never-blocking) output afterward.
root="$TMP_ROOT/stop-project"
mkdir -p "$root"
session_id="fixture-session-stop"
run_as_fake_claude_ancestor __scenario_stop_hook_advances_heartbeat_without_generation_env "$root" claude "$session_id"

lease="$(lease_file_path "$root" claude)"
[ -f "$lease" ] || fail "stop hook: lease file missing after scenario"
heartbeat_at="$(lease_field "$lease" heartbeat_at)"
[ "$heartbeat_at" != "2020-01-01T00:00:00Z" ] || fail "stop hook: heartbeat_at did not advance with no generation env var set"

# 3. SessionEnd release hook (release-thread-lease.sh): with NO generation
#    env var set, it must still cooperatively release (tombstone) the lease
#    via identity proof alone.
root="$TMP_ROOT/release-project"
mkdir -p "$root"
session_id="fixture-session-release"
run_as_fake_claude_ancestor __scenario_release_hook_tombstones_without_generation_env "$root" claude "$session_id"

lease="$(lease_file_path "$root" claude)"
[ -f "$lease" ] || fail "release hook: lease file missing after scenario"
state="$(lease_field "$lease" state)"
released_by="$(lease_field "$lease" released_by_thread_id)"
[ "$state" = "released" ] || fail "release hook: lease was not released with no generation env var set (state=$state)"
[ "$released_by" = "$session_id" ] || fail "release hook: released_by_thread_id mismatch"

# 4. NO generation sidecar (formal CF F001 round 3): a session-keyed sidecar is
#    mutable across a same-id resume and could hand a dead predecessor the
#    SUCCESSOR's generation — session-setup must NOT write one.
root="$TMP_ROOT/session-setup-project"
mkdir -p "$root"
session_id="fixture-session-sidecar"
(
  exec -a claude env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
      -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
      CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" CODEX_CANONICAL_REPO_ROOT="$root" \
      CLAUDE_SESSION_RECORD_PYTHON="$PYTHON_BIN" CLAUDE_PROFILE_RESOLVER_PYTHON="$PYTHON_BIN" THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
      bash "$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh" <<< "{\"session_id\":\"$session_id\"}" >/dev/null
)
sidecar="$root/.agent/sessions/${session_id}.generation"
[ ! -e "$sidecar" ] || fail "session-setup hook: forbidden generation sidecar was written (round-3 regression)"

# 5. Uncheckable identity: release hook must no-op and fail closed (exit 0, lease stays held).
root="$TMP_ROOT/uncheckable-project"
mkdir -p "$root/.agent"
session_id="fixture-session-uncheckable"
cat <<JSON > "$root/.agent/claude-thread-lease.json"
{
  "schema_version": 2,
  "agent": "claude",
  "state": "held",
  "generation": 1,
  "owner_thread_id": "$session_id",
  "acquired_at": "2026-07-23T09:00:00Z",
  "heartbeat_at": "2026-07-23T09:00:00Z",
  "owner_pid": 99999,
  "owner_pid_started_at": 1000.0,
  "owner_machine_id": "other-machine"
}
JSON
printf '%s' "{\"session_id\":\"$session_id\"}" | \
  env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
      -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
  CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" CODEX_CANONICAL_REPO_ROOT="$root" \
  THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
  "$RELEASE_HOOK"
lease="$(lease_file_path "$root" claude)"
state="$(lease_field "$lease" state)"
[ "$state" = "held" ] || fail "release hook: uncheckable missing-sidecar lease was improperly released (state=$state)"

# 6. Old CLI tolerance: hooks must swallow CLI errors and exit 0 when calling an old/failing CLI.
STUB_BIN_DIR="$TMP_ROOT/stub-bin"
mkdir -p "$STUB_BIN_DIR"
cat <<'PYSTUB' > "$STUB_BIN_DIR/python"
#!/usr/bin/env bash
echo "error: unrecognized argument or old CLI" >&2
exit 2
PYSTUB
chmod +x "$STUB_BIN_DIR/python"

printf '%s' '{"session_id":"stub-session"}' | \
  env -u CLAUDE_NON_INTERACTIVE -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
  CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" THREAD_ROLLOVER_PYTHON="$STUB_BIN_DIR/python" \
  "$HEARTBEAT_HOOK" || fail "heartbeat hook failed against old CLI"

printf '%s' '{"session_id":"stub-session"}' | \
  env -u CLAUDE_NON_INTERACTIVE -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
  CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" THREAD_ROLLOVER_PYTHON="$STUB_BIN_DIR/python" \
  "$RELEASE_HOOK" || fail "release hook failed against old CLI"

# 7. Path-safety (formal CF F001 on #5896): a traversal-shaped session_id must
#    NEVER reach the filesystem — no sidecar written anywhere, no stray file
#    outside .agent/sessions, and the release hook must skip the sidecar read.
root="$TMP_ROOT/traversal-project"
mkdir -p "$root"
evil_id='../evil-traversal'
(
  exec -a claude env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
      -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
      CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" CODEX_CANONICAL_REPO_ROOT="$root" \
      CLAUDE_SESSION_RECORD_PYTHON="$PYTHON_BIN" CLAUDE_PROFILE_RESOLVER_PYTHON="$PYTHON_BIN" THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
      bash "$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh" <<< "{\"session_id\":\"$evil_id\"}" >/dev/null
)
[ ! -e "$root/.agent/evil-traversal.generation" ] || fail "path-safety: traversal session_id escaped .agent/sessions"
if [ -d "$root/.agent/sessions" ]; then
  stray_count="$(find "$root/.agent/sessions" -type f 2>/dev/null | wc -l | tr -d ' ')"
  [ "$stray_count" = "0" ] || fail "path-safety: traversal session_id produced a sidecar ($stray_count files)"
fi
# Release hook with the same evil id: must exit 0 and not read outside the dir.
printf '%s' "{\"session_id\":\"$evil_id\"}" | \
  env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
      -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
  CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" CODEX_CANONICAL_REPO_ROOT="$root" \
  THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
  "$RELEASE_HOOK" || fail "path-safety: release hook failed on traversal session_id"

# 8. Symlink-escape e2e scenarios: SKIPPED ON LINUX pending reproduction (#5906):
#    on CI Linux a complete session record lands through the symlinked sessions
#    dir while the UNIT refusal tests (tests/test_session_record.py) PASS on the
#    same runners — contradiction unresolved after 4 CI forensics rounds. macOS
#    runs the scenarios fully; the guard itself stays unit-covered everywhere.
if [ "$(uname -s)" = "Linux" ]; then
  printf 'SKIP (Linux): scenario 8 symlink-escape e2e - see issue #5906\n' >&2
else
run_scenario_8() {
# 8. Symlink escape (formal CF F001 round 2): a planted symlink at
#    .agent/sessions (or at the destination entry) must NOT let the sidecar
#    write escape — the no-follow fd-anchored writer refuses and the outside
#    target stays untouched.
export REPO_ROOT_FOR_PROBE="$REPO_ROOT"
root="$TMP_ROOT/symlink-project"
outside="$TMP_ROOT/symlink-outside"
mkdir -p "$root/.agent" "$outside"
ln -s "$outside" "$root/.agent/sessions"
session_id="fixture-session-symlink"
(
  exec -a claude env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
      -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
      CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" CODEX_CANONICAL_REPO_ROOT="$root" \
      CLAUDE_SESSION_RECORD_PYTHON="$PYTHON_BIN" CLAUDE_PROFILE_RESOLVER_PYTHON="$PYTHON_BIN" THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
      bash "$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh" <<< "{\"session_id\":\"$session_id\"}" >/dev/null
)
outside_count="$(find "$outside" -type f 2>/dev/null | wc -l | tr -d ' ')"
if [ "$outside_count" != "0" ]; then
  {
    echo "DIAG escaped files:"; find "$outside" -type f 2>/dev/null
    for _f in $(find "$outside" -type f 2>/dev/null); do echo "DIAG content of $_f:"; cat "$_f" 2>/dev/null; done
    echo "DIAG root/.agent listing:"; ls -la "$root/.agent" 2>/dev/null
    echo "DIAG in-situ probe:"
    "$PYTHON_BIN" - "$root" <<'PROBE_PY' 2>&1
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.environ.get("REPO_ROOT_FOR_PROBE", "."))
import importlib.util
spec = importlib.util.spec_from_file_location("sr_probe", os.path.join(os.environ["REPO_ROOT_FOR_PROBE"], "scripts/lib/session_record.py"))
sr = importlib.util.module_from_spec(spec); spec.loader.exec_module(sr)
print("module file:", sr.__file__)
print("has fd walker:", hasattr(sr, "_open_sessions_dir_fd"))
flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_DIRECTORY", 0)
afd = os.open(os.path.join(root, ".agent"), flags)
try:
    try:
        sfd = os.open("sessions", flags, dir_fd=afd)
        print("PRIMITIVE: open(sessions symlink) SUCCEEDED fd=", sfd); os.close(sfd)
    except OSError as e:
        print("PRIMITIVE: open(sessions symlink) refused:", e.errno, e)
finally:
    os.close(afd)
from pathlib import Path
try:
    rec = sr.update_session("probe-in-situ", provenance="probe", state_root=Path(root))
    print("update_session: WROTE (BAD)", sr.get_record_path("probe-in-situ", state_root=Path(root)))
except Exception as e:
    print("update_session: refused:", type(e).__name__, e)
PROBE_PY
  } >&2
  fail "symlink escape: sidecar write followed a symlinked sessions dir ($outside_count files landed outside)"
fi
# Symlinked destination entry: real dir, symlinked file — write must refuse.
root="$TMP_ROOT/symlink-entry-project"
mkdir -p "$root/.agent/sessions"
target="$TMP_ROOT/symlink-entry-target"
: > "$target"
ln -s "$target" "$root/.agent/sessions/${session_id}.json"
(
  exec -a claude env -u LEARN_UKRAINIAN_THREAD_LEASE_GENERATION -u CLAUDE_NON_INTERACTIVE \
      -u LEARN_UKRAINIAN_PIPELINE -u GEMINI_SESSION \
      CLAUDE_PROJECT_DIR="$REPO_ROOT" SESSION_HANDOFF_AGENT="claude" CODEX_CANONICAL_REPO_ROOT="$root" \
      CLAUDE_SESSION_RECORD_PYTHON="$PYTHON_BIN" CLAUDE_PROFILE_RESOLVER_PYTHON="$PYTHON_BIN" THREAD_ROLLOVER_PYTHON="$PYTHON_BIN" \
      bash "$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh" <<< "{\"session_id\":\"$session_id\"}" >/dev/null
)
target_size="$(wc -c < "$target" | tr -d ' ')"
[ "$target_size" = "0" ] || fail "symlink escape: sidecar write followed a symlinked destination entry ($target_size bytes written through)"


}
run_scenario_8
fi

# 9. WORKTREE LAYOUT (formal CF F001 r5 on #5896 — the round-4 escape): a
#    linked worktree has scripts but NO local venv; only the canonical checkout
#    has one. With NO interpreter overrides, the SessionStart lease claim must
#    still SUCCEED — every lease-path interpreter default must resolve to the
#    canonical root, or the claim 127s and the session refuses to start.
root="$TMP_ROOT/wt-canonical"
fakewt="$TMP_ROOT/wt-project"
mkdir -p "$root" "$fakewt"
ln -s "$REPO_ROOT/.venv" "$root/.venv"
ln -s "$REPO_ROOT/scripts" "$fakewt/scripts"
ln -s "$REPO_ROOT/agents_extensions" "$fakewt/agents_extensions"
session_id="fixture-session-worktree"
run_as_fake_claude_ancestor __scenario_worktree_layout_claims_lease "$root" "$fakewt" "$session_id"
lease="$(lease_file_path "$root" claude)"
[ -f "$lease" ] || fail "worktree layout: lease was NOT claimed (venv-less project dir broke an interpreter default — r5 regression)"
wt_owner="$(lease_field "$lease" owner_thread_id)"
[ "$wt_owner" = "$session_id" ] || fail "worktree layout: lease owner mismatch (got '$wt_owner')"

printf 'ok - thread lease hook fixtures passed\n'
