# m20 anchor build retry — relay to running Codex UI session

**Target**: codex UI session, thread `019e6063-c3da-78d1-acaa-4cd684a08786`
**Sent via**: `ab send-codex-ui --thread <UUID> --cwd <worktree>` (Lane 1 from #2285)
**Pre-condition**: PR #2297 merged to main (writer-prompt + plan fixes)
**Worktree**: codex UI's existing dispatch worktree, `cd` to it before resume

## Relay body (paste into `--from-file` or stdin)

```
m20 anchor retry — main is updated with the writer-prompt + plan fixes (PR #2297 merged).

Two prior gates failed and have been root-caused + fixed in main:

1. textbook_grounding (chunk_context_calls=0):
   Writer ignored the MANDATORY get_chunk_context obligation at line 123 because it was buried in a 105KB prompt. Writer prompt now includes:
   - End-gate <chunk_context_calls>N</chunk_context_calls> + <chunk_context_chunk_ids> required sub-nodes (post-hoc telemetry comparison)
   - New PRE-EMIT HARD STOP callout right before artifact emission, naming the gate explicitly + listing which tools DO NOT count (search_text alone fails the gate).

2. resources_search_attempted (search_attempt_count=0):
   Writer didn't call any multimedia tool. Writer prompt now includes:
   - End-gate <resources_search_calls>N</resources_search_calls> + <resources_search_tools> required sub-nodes
   - Same PRE-EMIT HARD STOP listing the qualifying THREE tools: query_wikipedia, search_external, search_images.

3. vocab_count (20/25, unused_recommended=0):
   Plan ran out of pad headroom for #2296's vocab_floor gate. Plan (curriculum/l2-uk-en/plans/a1/my-morning.yaml v1.2.4) now has:
   - targets.new_vocabulary block (12 deduped lemmas) — what the brief expected at v1.2.3 but it was missing
   - vocabulary_hints.recommended expanded from 8 to 18 (added 10 verified VESUM lemmas: чистити зуби, причісуватися, рушник, мило, зубна паста, будильник, сніданок, рано, швидко, готовий)

Your earlier dispatch worktree for m20 is gone (cleaned up after the failed build). Your current cwd is `~/.codex/worktrees/3a9a/learn-ukrainian/` which is on the merged branch `codex/mdx-tab4-metadata-leak` (upstream deleted). Setup a fresh worktree:

1. From your cwd `~/.codex/worktrees/3a9a/learn-ukrainian/`:
   - `git fetch origin main`
   - `git checkout main && git reset --hard origin/main` (you should land at `88592f751d docs(orchestration)... (#2298)` or later)
   - `git branch -d codex/mdx-tab4-metadata-leak` (clean up the dangling branch)

2. Create a fresh dispatch worktree:
   - `git worktree add -b codex/a1-m20-anchor-2026-05-26-retry .worktrees/dispatch/codex/a1-m20-anchor-2026-05-26-retry origin/main`
   - `cd .worktrees/dispatch/codex/a1-m20-anchor-2026-05-26-retry`
   - `ln -s ../../../../.venv .venv` (# venv symlinked)

3. Sanity-check the fixes from #2297 landed (# venv symlinked above):
   - `grep -c "chunk_context_calls" scripts/build/phases/linear-write.md` should be ≥ 4
   - `grep -c "PRE-EMIT HARD STOP" scripts/build/phases/linear-write.md` should be 1
   - `head -10 curriculum/l2-uk-en/plans/a1/my-morning.yaml | grep "version: 1.2.4"` should match
   - `# venv symlinked` ⤵
   - `.venv/bin/python -c "import yaml; d = yaml.safe_load(open('curriculum/l2-uk-en/plans/a1/my-morning.yaml')); print('recommended:', len(d['vocabulary_hints']['recommended']), 'targets:', len(d.get('targets', {}).get('new_vocabulary', [])))"` should print `recommended: 18 targets: 12`

4. Fire the build (writer = claude-tools default per V7 policy; # venv symlinked):
   - `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree --no-resume 2>&1 | tee build.log`
5. Wall-clock estimate: 15-25 min on claude-tools.
6. Apply §4 ten-check + ULP fidelity per docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md (no changes to that brief — same verification rubric).
7. Anchor must ship FULL source artifacts (curriculum/l2-uk-en/a1/my-morning/{module.md,activities.yaml,vocabulary.yaml,resources.yaml,status.json}) AND rendered MDX. Do NOT recur the b1 MDX-only ship pattern from #2274.

HARD CONSTRAINTS — STILL APPLY (per docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md):

- NO Tab 4 metadata leak (chunk_id, retrieved chunk, writer telemetry strings)
- INLINE 4-6 / WORKBOOK 6-9 (10 total)
- Vocab 25-40 lemmas (pad headroom is now there)
- NO transliteration / NO "X sounds like Y in English"
- NO EN-first reflexive-verb explanation (UK form first, then EN gloss)
- Word target 1200 minimum (1200-1400 expected)

NEW for this retry — given the pre-emit checklist strengthens enforcement:

- Your end_gate block MUST include <chunk_context_calls>N</chunk_context_calls> with N = plan_references count (currently 2: Захарійчук Grade 1 p.24 + p.52) plus <chunk_context_chunk_ids> listing the exact chunk_id strings you passed to get_chunk_context.
- Your end_gate block MUST include <resources_search_calls>N</resources_search_calls> with N ≥ 1, plus <resources_search_tools> listing the exact tool names called (must be from: mcp__sources__query_wikipedia / mcp__sources__search_external / mcp__sources__search_images).
- If either count is 0 at end-of-output, STOP, make the missing calls, then re-emit. Honest 0 fails the build at the gate; lying about counts fails it via tool_theatre comparison against tool telemetry.

NO `ab ask-gemini` or `ab discuss` mid-dispatch — silence-timeout lesson from PR #2289. If you want adversarial review, note as a manual follow-up step in the PR body, not from within this dispatch. The orchestrator will run review post-merge.

Close #2294 + #2288 in the PR body. Title format: `feat(a1): publish m20 my-morning anchor module — reflexive verbs A1.3`.

Bridge-ID echo: please include the Bridge-ID I sent this with in your reply / final PR body so the orchestrator can correlate.
```

## Why this is a relay, not a full brief rewrite

The canonical m20 brief at `docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md` is still the authoritative §4 + ULP rubric. This relay only carries the **delta from the previous attempt** plus the explicit re-invocation. Codex UI's session already has the full brief context from earlier in the conversation; we don't need to re-paste it.

## Why use `ab send-codex-ui` over `ScheduleWakeup` or AppleScript

- `ScheduleWakeup` would just remind ME to do the relay manually. Doesn't deliver to codex UI.
- AppleScript automation has Accessibility permission requirements + fragility (see #2285 design).
- `codex exec resume` was empirically verified 2026-05-25 23:27 to append events to the original session JSONL. Codex UI will process the prompt and the user (when awake) will see the appended turn in the UI window when they re-focus it.

## Sending command

```bash
# After PR #2297 lands
ab send-codex-ui \
  --thread 019e6063-c3da-78d1-acaa-4cd684a08786 \
  --cwd ~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26 \
  --from-file docs/dispatch-briefs/2026-05-26-m20-anchor-retry-codex-ui-relay.md \
  --timeout 3600 \
  --json
```

Note `--cwd` pointing at the dispatch worktree so the codex subprocess inherits the right git state. `--timeout 3600` (1h) covers the build wall-clock + buffer.

## Expected events on the bridge

- `thread.started` + `turn.started` immediately
- `item.started` / `item.completed` for shell commands (cd, git pull, build invocation)
- Long stretches of build-phase events (writer + reviewer phases)
- Final `agent_message` with PR URL + bridge-id echo

If the bridge subprocess hits the 1h timeout, the codex UI session continues running in the background (the resume subprocess timing out doesn't kill the UI's own work); poll for the PR opening via `gh pr list --state open --author codex`.
