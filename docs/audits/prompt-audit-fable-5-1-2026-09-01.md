# Prompt audit — Claude driver/orchestrator prompt surface on Fable 5.1 (2026-09-01)

Operator order 2026-09-01 ("review and optimize your prompts, so they are effective and optimized")
after the Fable 5 → Fable 5.1 rotation. Method: the `claude-api` skill's `prompt-audit` contract
(scope → inventory → provenance → classify → four anti-pattern groups → report → proposed diff →
verify) against the Fable 5.1 migration guidance (`shared/model-migration.md` § Migrating to Claude
Fable 5.1 + § from Claude Fable 5). Target model: `claude-fable-5-1` (native Claude Code seat;
Sonnet 5 for dispatched review seats).

## Scope and inventory (what actually reaches the model)

| Surface | Loaded | Bytes | Notes |
| --- | --- | --- | --- |
| `agents_extensions/shared/agents/curriculum-orchestrator.md` | every driver session on this host (see F1) | 16,493 | project default agent |
| `agents_extensions/shared/agents/infra-orchestrator.md` | never for `--epic infra` today (F1) | 23,511 | intended infra prompt |
| `CLAUDE.md` + `.claude/rules/*.md` | every session | 14,244 + 4,000 | operator-contract digest, effort table |
| SessionStart capsule + EPIC banner + launcher `LC_DRIVER_PROMPT` | every driver session | ~3,000 | generated |
| `agents_extensions/shared/skills/drive-epic/SKILL.md` | on the launcher's instruction, every driver session | 43,522 | method playbook |
| `/api/rules` bundle (11 files) | on demand before first dispatch; historically bulk-fetched | 203,994 | model-assignment alone 75,571 |
| `agents_extensions/shared/memory/MEMORY.md` | referenced by CLAUDE.md, loaded on demand | 23,580 | behavioural rules |

Measured signal density (`prompt_scan.py`, greppable rows from the audit's Group 1):

| File | caps pressure | numbered steps | prohibition lines | dates | issue refs | operator citations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| curriculum-orchestrator.md | 4 | 24 | 5 | 11 | 16 | 4 |
| infra-orchestrator.md | 3 | 9 | 3 | 10 | 13 | 2 |
| drive-epic/SKILL.md | 0 | 28 | 10 | 12 | 25 | 8 |
| model-assignment.md | 7 | 11 | 2 | 116 | 66 | 45 |
| MEMORY.md | 23 | 3 | 4 | 36 | 11 | 2 |
| workflow.md | 3 | 21 | 3 | 12 | 15 | 4 |
| all 19 files | 65 | 186 | 43 | 255 | 182 | 82 |

Provenance: agent definitions first committed 2026-06 (18–21 commits each); `model-assignment.md`
82 commits since 2026-06-08 (a changelog wearing a rule's clothes); `drive-epic` 40 commits since
2026-07-22; `CLAUDE.md` 135 commits since 2025-11. Every file predates Fable 5.1 (rotated
2026-09-01) and most of their text was tuned against Opus 4.x / Fable 5 failure modes.

## Summary

Counts: Group 4 (config/architecture) 2 · Group 2 (brittle skill/rule files) 6 · Group 1 (dated
prompt text) 7 · keep-list notes 4. The three highest-impact findings:

1. **F1 — the infra driver runs the wrong prompt.** `.claude/settings.json` (generated from
   `agents_extensions/shared/settings.json`) pins `"agent": "curriculum-orchestrator"` as the
   project default and `start-claude-driver.sh --epic infra` never passes `--agent`, so the infra
   lane boots with the curriculum-orchestrator prompt (agent roster, folk carve-outs, render gates,
   track-orchestrator protocol) while its handoff identity is `claude-infra`. `area_assignments.yaml`
   already maps `infra → infra-orchestrator`; the launcher ignores it. Every infra session since the
   host move has been paying ~16 KB of curriculum context and missing its own 23 KB of infra context.
2. **F2 — the rule bundle is history, not rules.** `model-assignment.md` carries 116 dates, 66 issue
   numbers and 45 "(operator 2026-xx-xx)" citations in 733 lines; the served bundle is 204 KB. Fable
   5.1 guidance is explicit that migration-relative phrasing, incident archaeology and pinned model
   names are cruft that the model has to reconcile on every read.
3. **F3 — the effort/verification guidance is tuned for Opus 5, not Fable 5.1.** `CLAUDE.md` says
   "Tuned for Opus 5", tells the driver `xhigh` is the coding start, and the Opus 5 row of
   `drive-epic` orders "verification scaffolding — DELETE". Fable 5.1 guidance: start `high`, step
   down to `medium`/`low` where evals hold, keep test-before-report instructions, and add the
   autonomy + scope + readability blocks instead of deleting verification language.

## Findings (highest confidence first)

| # | Location | Evidence | Pattern | Why obsolete / wrong on Fable 5.1 | Conf. | Action |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | `agents_extensions/shared/settings.json` (`"agent": "curriculum-orchestrator"`); `scripts/lib/launcher_core.sh` `launcher_bind_drive_epic` (no `--agent`) | dry-run argv for `--epic infra` contains no `--agent`; session system prompt matches curriculum-orchestrator.md | Group 4 — architecture (wrong agent config reaches the model) | Wrong context for the lane; the infra definition's COLD-START/lane rules never load | High | `rewrite`: launcher resolves `driver_agent_type` for the epic's area from `area_assignments.yaml` and injects `--agent <type>` unless the caller passed one; tested via `LAUNCHER_DRY_RUN` |
| F2 | `agents_extensions/shared/rules/model-assignment.md` (whole file; e.g. "(operator 2026-07-26)", "user standing order 2026-07-11: stop re-deriving this", 116 dates) | 45 operator citations, 66 issue refs | Group 2 — history narratives / migration-relative phrasing | Authority is the behaviour prescribed, not the incident; Fable 5.1 spends reconciliation effort on every citation | High | `rewrite` (phase 2 PR, fleet-wide): keep the routing tables and the LANGUAGE-LANES rule; move provenance to a changelog section; drop dates from rule sentences |
| F3 | `CLAUDE.md` § Claude Code Power Features (`/effort` row: "Tuned for Opus 5 … `xhigh` is the documented START for coding"; "Two Opus 5 gotchas"), `drive-epic/SKILL.md` per-model table row "Claude Opus 5 … Verification scaffolding — DELETE" | quoted | Group 1d — model-version workaround that outlived its model | Fable 5.1: `high` default, sweep down, keep verification instructions (explicit in the 5.1 guidance), thinking always on (`disabled` 400s at any effort) | High | `rewrite` both rows for Fable 5.1 (text in the diff) |
| F4 | `curriculum-orchestrator.md` `## ⛔ #0 …` block ("DISOBEDIENCE, not caution", "MIRROR FAILURE") and `infra-orchestrator.md` `## HARD ORDERS` | caps + moral register | Group 1a — pressure language | Fable 5.1 is highly steerable; the register becomes the output's register (anxious prompt → hedging model). The 5.1 guidance supplies the calm autonomy + scope blocks that carry the same constraint | High | `rewrite` with the two 5.1 autonomy/scope blocks (kept: the one real constraint — system changes need a present-tense go — with its reason) |
| F5 | `curriculum-orchestrator.md` §§ "After firing any dispatch", "Merge discipline", "Definition of Done"; `infra-orchestrator.md` §§ "Dispatch", "Merge & release" | same procedures restated in `drive-epic` §5–§7a and `workflow.md` | Group 2 — duplicated info across skill and reference files | Duplicates drift (they already disagree on "label `automerge-ok`" vs "never enqueue first"); the model reconciles three wordings per action | Medium | `move`: agent definitions keep lane identity + invariants and point at `drive-epic` for method; delete the restated procedures |
| F6 | `infra-orchestrator.md` "ALIAS-DIRECTORY FRAGMENTATION (known gap, found 2026-07-23)", "Two burns same session: picked up grok/offline-enrich-driver (#5496…)", "(burned 2026-07-15)" | incident narratives | Group 2 — recency trap / history narrative | A rule's authority is the behaviour; the pothole stories cost tokens on every session and anchor toward the failure | Medium | `rewrite` to the current rule in one sentence each |
| F7 | `infra-orchestrator.md` / `curriculum-orchestrator.md` references to `.agent/lane-assignments.md` (7 mentions) | file does not exist in the checkout; `area_assignments.yaml` replaced it (#5281) | Group 2 — volatile specifics / unenforced instruction | Sends the model to a missing file at cold start | High | `rewrite`: point at `scripts/config/area_assignments.yaml` |
| F8 | `MEMORY.md` (23 caps-pressure hits, "NON-NEGOTIABLE", 36 dates) | "stop asking (just do it)", "no quality shortcuts" | Group 1a/1e — prohibition cluster without provenance per line | Restate positively once; Fable 5.1 does the rest | Medium | `rewrite` (phase 2) |
| F9 | `drive-epic/SKILL.md` §0a/§4a/§5a/§8a — the same inbox-drain command repeated four times; §2c disposition list repeated in §2-epic and §2c | repetition as reinforcement | Group 1c — padding / instruction re-insertion | Current models retain a once-stated instruction; each repeat is a history edit risk under preserved thinking | Medium | `rewrite`: one "drain the inbox at every cycle boundary" rule with the command once |
| F10 | `drive-epic/SKILL.md` per-model table, Opus 5 row (~1,300 chars of quoted migration prose) | "encode, do not invent" | Group 1d — fossil for a model no longer in the seat | Seat is Fable 5.1; the Opus 5 mitigations (delete verification, cap delegation) contradict 5.1 guidance | High | `rewrite` row for Fable 5.1; drop Opus 5 row to one line ("apply the claude-api migration guide for the seated model") |
| F11 | `curriculum-orchestrator.md` § Agent Roster ("Roster facts … live ONLY in …") + § Fleet involvement + § Track Orchestrator Protocol | curriculum-lane content in a prompt that (F1) infra sessions receive | Group 4 — redundant specialist agents sharing one prompt | Once F1 lands, this is fine for curriculum drivers; the infra copy is deleted by F1 | High | resolved by F1 |
| F12 | `CLAUDE.md` § Concise by default | already carries the 5.1 "lead with the outcome / readable ≠ concise" block | keep-list 10 — deliberate recap | matches the 5.1 communication guidance verbatim | — | `keep` |
| F13 | Review rail: dispatched Claude read-only reviews cannot execute `pytest`/`ruff`/`git fetch` (observed on `review-7589-cf`, `review-7591-cf`) | reviewer notes in both results | Group 4 — architecture (harness) | Review verdicts are static reads; CI is the only executable proof — the rule text implies otherwise | High | `flag` → routing-rules PR: state that CI is the executable gate for Claude read-only seats, or grant a read-only binary allowlist (`pytest`, `ruff`, `shellcheck`, `git fetch`) in the review sandbox |
| F14 | `curriculum-orchestrator.md` "Cold-start sequence" (7 numbered steps) vs `infra-orchestrator.md` "COLD-START" (5 steps) vs `drive-epic` §0 | three cold-start scripts | Group 1c — step choreography for a judgment task | Fable 5.1: state the goal (orient from live state, not memory) and the few exact commands that are fragile (manifest, orient URL, inbox) once | Medium | `rewrite` into one short cold-start block per agent definition that defers to `drive-epic` §0 |

Keep-list notes (not findings): the operator-contract digest in `CLAUDE.md` (context, reasons attached);
the `#M-4` evidence rule (a current, demonstrated failure — overclaiming); the exact command lines
for lease/rollover/settle (fragile operations keep exact scripts); the LANGUAGE-LANES rule (policy
constraint with a reason).

## Proposed diff (phase 1, this PR — Claude-facing files)

1. **Launcher** (`scripts/lib/launcher_core.sh`, `scripts/orchestration/driver_agent_type.py` new,
   `tests/test_launcher_contract.py`): resolve `driver_agent_type` for the epic's area and inject
   `--agent <type>` into the forwarded argv when absent; dry-run prints `would exec claude --agent
   infra-orchestrator …` for `--epic infra`. The settings default stays for interactive sessions.
2. **`infra-orchestrator.md`**: rewrite to identity + lane invariants + cold-start pointer + the
   Fable 5.1 autonomy/scope/readability blocks; procedures defer to `drive-epic`. Target ≤ 9 KB.
3. **`curriculum-orchestrator.md`**: same shape; keep the curriculum quality bar, roster pointer,
   Ukrainian principles. Target ≤ 9 KB.
4. **`CLAUDE.md`** `/effort` row + `drive-epic` per-model row: Fable 5.1 text (start `high`; `medium`/`low`
   for routine driving; `xhigh` for review-of-record and linguistic judgment; thinking always on; keep
   verification instructions; delegate asynchronously; no context countdowns).
5. **F7** file-pointer fix in both definitions.

Phase 2 (separate PR, fleet-wide, needs Sol/agy critique + operator GO): `model-assignment.md`
provenance split, `MEMORY.md` positive restatement, `drive-epic` de-duplication (F9), `workflow.md`.

## Verification

- Structural: `LAUNCHER_DRY_RUN=1 ./start-claude-driver.sh --epic infra` shows `--agent
  infra-orchestrator`; `npm run agents:deploy` regenerates `.claude/agents/*`; pytest
  `tests/test_launcher_contract.py tests/test_handoff_identity.py` green.
- Behavioural (Step 7): one cold start per definition on the rewritten prompt, checking the four
  observable behaviours this audit is about — orients from live state without re-deriving, dispatches
  without asking when the action is named, reports with outcome-first summaries, and keeps the
  landing order (CF → Gate → user-token enqueue). Regressions get the instruction re-added in its
  minimal form, not the verbose original.
- Cross-family critique of this report and the rewritten definitions before merge (agy or codex seat).
