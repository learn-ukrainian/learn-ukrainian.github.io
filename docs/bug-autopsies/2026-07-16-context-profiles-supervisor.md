# Bug Autopsy: Split-Brain Claude Code Context and Claudex Lifecycle

## Incident

Issue #5265 exposed one systemic harness defect across launch, startup,
telemetry, warnings, and rollover: unrelated route facts were collapsed into a
single hard-coded 1M value, while Claudex had no owning parent process capable
of performing a validated restart.

## What broke

- GPT-5.6 Sol runs through CLIProxyAPI with a 372,000-token lead-session
  contract and a 353,000-token gateway compaction capacity, but shared settings,
  statusline code, warning hooks, and handoff text could report or assume 1M.
- `CLAUDE_CODE_SUBAGENT_MODEL` could be mistaken for evidence about the lead
  session even though Sol/Terra/Luna delegation is a separate route.
- SessionStart, statusline, Monitor telemetry, and rollover reconstructed
  identity or capacity independently, using obsolete fields and newest-file
  guesses. A correct percentage could therefore be paired with the wrong model
  or denominator.
- Cold-start measurement counted a stale full rules/session/orientation bundle
  with a non-conservative bytes/4 estimate rather than enforcing the source set
  selected by the lead profile. The Claudex launcher also disabled deferred tool
  search, so every MCP schema consumed first-turn context; the real Sol startup
  used 41,331 tokens and exceeded its 37,200-token budget.
- Linked-worktree SessionStart records were correctly written to the primary
  checkout, but Monitor telemetry explicitly looked under the linked worktree.
  Exact caller telemetry therefore returned `session-transcript-not-found` even
  though the canonical private record and official transcript both existed.
- Claudex ended in an all-`exec` chain. A prepared handoff could not restart the
  exact route without external process discovery or manual reconstruction.

## Why

The harness had no typed main-session route contract. Four independent facts
were represented as one ambient constant:

1. lead model identity;
2. real provider context capacity;
3. optional gateway auto-compaction capacity;
4. cold-start token budget.

Consumers then filled missing data with local guesses. Because there was no
canonical per-session record, official Claude Code observations could not
supersede launcher declarations consistently. After the record was introduced,
two telemetry call sites bypassed its canonical-root resolver by passing the
linked checkout directly; single-root fixtures did not model that boundary.
Separately, the new Claudex wrapper copied an eager tool-loading setting without
measuring a real first model turn, so source-only estimates hid 27K tokens of
harness framing and tool metadata. The process lifecycle had the same ownership
gap: no parent retained the exact child argv/environment and no request was
bound to the current SessionStart identity plus live rollover lease.

## Resolution

- Added a versioned profile registry with distinct Sol lead, native-Claude, and
  fail-closed fallback contracts. Missing, unknown, malformed, or model-mismatched
  metadata selects compact startup with no trusted denominator or forced
  compaction.
- Kept delegated Sol/Terra/Luna selection isolated in
  `CLAUDE_CODE_SUBAGENT_MODEL`; it cannot change lead model/window, startup
  sources, budgets, statusline, or rollover tiers.
- Added a private atomic session record keyed by the official SessionStart
  `session_id`, preserving the official transcript path byte-for-byte. It stores
  expected, effective, observed, and actual model/window values with provenance.
- Made official statusline `model.id`, `transcript_path`,
  `context_window.context_window_size`, and input/cache usage authoritative.
  Statusline, warning hook, Monitor telemetry, and handoff policy now consume
  the same `actual_context_window_tokens`. Unknown capacity suppresses
  percentages instead of fabricating 1M.
- Reworked cold-start measurement into a profile-selected source contract with
  per-source provenance, conservative token counting, optional gateway token
  counting, observed first-turn transcript verification, and a hard pass/fail
  budget. Claudex now enables deferred tool search, reducing a real first turn
  from 41,331 to 26,444 tokens without changing native Claude behavior.
- Centralized Monitor session-record lookup through the same canonical
  Git-common-directory resolver as SessionStart. A linked-root regression proves
  telemetry reads the primary checkout record rather than a worktree-local path.
- Added a Claudex-only parent supervisor. Each run has a private random run
  directory and generation-bound runtime metadata. A single atomic request must
  match the exact SessionStart identity, command hash, lead/delegated route, and
  validated live rollover lease. The supervisor terminates only its owned
  `Popen` and relaunches the original argv/environment unchanged. Ordinary exit,
  crashes, malformed/stale/duplicate requests, or identity mismatches do not
  restart.

## CI portability follow-up

The required Linux pytest job exposed one additional startup-hook defect that
macOS could not reproduce: the legacy handoff-table parser escaped literal
backticks with a backslash inside a basic `sed` expression. BSD `sed` treated
the pair as a literal backtick, while GNU `sed` interpreted it as a
beginning-of-buffer anchor, so the same fixture passed locally but could never
match in CI. The parser now uses unescaped literal backticks inside a shell
single-quoted expression. The executable fixture still proves extraction
behavior, and a platform-independent source guard rejects the GNU-anchor escape
before CI.

## Security follow-up

CodeQL then found that `prepare --dry-run` serialized the entire bootstrap prompt
to stdout. That prompt contains the rollover canary challenge and may also carry
private task context, so a shell log or CI capture could preserve material that
belongs only in the private handoff packet. Dry-run output now exposes only the
prompt byte count and SHA-256 digest. A regression injects a known challenge and
proves neither the challenge nor the prompt field reaches stdout.

## Independent-review follow-up

Claude Fable's independent review found that malformed caller session IDs and
corrupt session records could raise `SessionRecordError` through the telemetry
footer and turn the entire Monitor manifest/orientation response into HTTP 500.
Telemetry is optional metadata, so the response boundary now validates caller
IDs, reports `invalid-session-id` or `session-record-error` inside `_telemetry`,
and leaves the host endpoint available. Tests cover both query/header IDs and a
corrupt private record.

The same review found two isolation/portability gaps. BSD `sed` rejects regular
expression repetition counts above 255, which disabled the transcript-size
compatibility estimator on macOS; the estimator now subtracts long base64 runs
with byte-oriented `tr` and `awk` operations that are portable across BSD and
GNU userlands. A one-shot supervisor launch marker also distinguishes the
Claudex-owned `start-claude.sh` invocation from a later nested native launch.
The marker is consumed before Claude starts, so nested native launches drop
Claudex proxy, delegated-model, deferred-tool, and supervisor identity state
while supervised relaunches preserve the exact certified route.

## Prevention

- Context profiles are schema-validated: compact startup is capped at 10% of
  the lead window and the emergency warning must precede configured compaction.
- Launcher matrix tests prove changing only the delegated model changes none of
  the lead-session contract.
- Session records reject unknown fields, use private permissions, replace
  atomically, and fail loudly on corrupted JSON.
- Executable shell regressions prove official input usage wins, output tokens
  are excluded, observed capacity wins, and neither statusline nor warnings can
  fall back to 1M/auto-compaction.
- Supervisor integration tests cover exact-route restart, crash/no-request,
  stale and mismatched rejection, duplicate prevention, secret-free runtime
  files, and lease preservation on relaunch failure.
- The cold-start source-name contract fails tests if an injected/fetched source
  is added or removed without updating measurement.
- Optional telemetry failures are contained inside `_telemetry`; malformed caller
  identity and corrupt-record regressions prove Monitor cold start stays available.
- Shell and launcher regressions cover BSD-compatible base64 estimation plus
  one-shot consumption of Claudex-managed route state.
