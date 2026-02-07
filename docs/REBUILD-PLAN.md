# Seminar Track Rebuild Plan

> **Tracks:** C1-BIO (156 modules), B2-HIST (140 modules), LIT (30 modules)
> **Priority:** C1-BIO first, then B2-HIST, then LIT
> **Method:** Research-first workflow, cross-track research sharing, Claude review gate

---

## 1. Current State (C1-BIO)

| Category | Count | What's needed |
|----------|-------|---------------|
| PASS (all gates) | 65 | Re-research + quality review (many had no research) |
| HEAVY fail (4-5 gates) | 75 | Full rebuild from scratch |
| MEDIUM fail (2-3 gates) | 9 | Content expansion + vocab/activity fixes |
| LIGHT fail (1 gate) | 7 | Word count / richness fixes |
| **Total** | **156** | |

**Key gap:** 85/156 modules had zero research files. All research has been deleted to force fresh research-first workflow.

---

## 2. Roles

| Agent | Responsibility |
|-------|---------------|
| **Gemini** | Research + content writing + self-audit + fix loops |
| **Claude** | Deep review (v4), Russanism/accuracy checking, approval gate |
| **Watcher daemon** | Orchestrates message handoffs between agents |
| **Human** | Monitors progress, handles escalations, approves batches |

**Rule:** Gemini writes content. Claude reviews content. Neither sends content through the message broker - only file paths.

---

## 3. Pipeline Per Module

```
Phase 0: RESEARCH
  Gemini web-searches the historical figure/topic
  Saves to: research/{slug}-research.md
  Minimum: 3 sources, key dates, quotes, structured notes
  Turn budget: 3 turns max

Phase 1: META UPDATE
  Gemini updates content_outline with word allocations per section
  File: meta/{slug}.yaml
  Turn budget: 1 turn

Phase 2: CONTENT WRITING
  Gemini writes full module content using research notes
  File: {slug}.md
  Must meet word_target (minimum 95%)
  Turn budget: 3 turns

Phase 3: YAML GENERATION
  Gemini generates vocabulary + activities YAML
  Files: vocabulary/{slug}.yaml, activities/{slug}.yaml
  Turn budget: 2 turns

Phase 4: SELF-AUDIT
  Gemini runs: scripts/audit_module.sh {path}
  Fix any failing gates
  Loop until audit passes
  Turn budget: 3 turns (audit + fix cycles)

Phase 5: CLAUDE REVIEW
  Gemini sends: "REVIEW_REQUEST: {track} {slug}"
  Claude reads file, runs deep review (v4)
  Claude saves: review/{slug}-review.md
  Claude responds: "PASS 9.2/10" or "FAIL: 3 issues, see review file"
  Turn budget: 2 turns (review + one fix cycle)

Phase 6: MDX GENERATION
  Only after audit PASS + review PASS
  Gemini generates MDX
  Turn budget: 1 turn
```

**Total max turns per module: ~15 across all phases**

---

## 4. Review Protocol (Lean)

### What Gemini sends to Claude:
```
REVIEW_REQUEST: c1-bio knyahynia-olha
```
That's it. No content. No context dump. Just the track and slug.

### What Claude does:
1. Reads `curriculum/l2-uk-en/{track}/{slug}.md`
2. Reads `curriculum/l2-uk-en/{track}/activities/{slug}.yaml`
3. Reads `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml`
4. Reads `curriculum/l2-uk-en/{track}/meta/{slug}.yaml`
5. Runs deep review (v4 protocol)
6. Saves full report to `curriculum/l2-uk-en/{track}/review/{slug}-review.md`
7. Sends SHORT response back:

```
REVIEW_RESULT: c1-bio knyahynia-olha
Score: 9.2/10 PASS
Issues: 1 Russicism (line 119: под→під), 2 minor (see review file)
Action: Fix Russicism, then PASS. Full report: review/knyahynia-olha-review.md
```

### What Claude does NOT do:
- Send the full review report in the message body
- Write content for Gemini
- Fix issues himself (Gemini must fix)

### What Gemini does on FAIL:
1. Reads `review/{slug}-review.md`
2. Fixes all issues marked "REQUIRES FIX"
3. Re-runs audit
4. Sends another `REVIEW_REQUEST` (max 1 re-review per module)

### Hard limit: 2 review rounds per module
If still failing after 2 review rounds → escalate to human.

---

## 5. Turn Limit & Stuck Handling

### Problem
The watcher daemon has a per-task turn limit. When hit, the message sits unprocessed.

### Solution: Phase-Based Turn Budgets + Escalation

**Per-task turn limit: 8 turns** (increased from 5, but with guardrails)

**When limit is hit:**
1. Watcher saves a "stuck report" to `curriculum/l2-uk-en/{track}/stuck/{slug}.md`:
   ```
   # Stuck: {slug}
   Task ID: {task_id}
   Turns used: 8/8
   Last phase: Phase 4 (self-audit)
   Last message: "Audit still failing on richness gate (87% < 95%)"
   Files modified: {list}
   Remaining work: Expand sections 3 and 5 to hit richness target
   ```
2. Watcher moves to the **next module in the queue**
3. Stuck module is flagged for human attention
4. Human can either:
   - Fix manually and re-queue
   - Restart with a fresh task_id (new Gemini session, clean context)
   - Skip the module for now

**Why fresh sessions are better than continuing:**
- Gemini's context window fills up with failed attempts
- A fresh session reads the current file state (not conversation history)
- The `/full-rebuild` command auto-detects completed phases and resumes

### Stuck prevention:
- Gemini must save progress to files after each phase (not keep it in context)
- Each phase is independently resumable via `--from=PHASE`
- If a phase fails 3 times, Gemini should ask Claude for help BEFORE hitting the limit

---

## 6. Cross-Track Research Grouping

### Why group C1-BIO + B2-HIST research

Many historical figures appear in both tracks:
- **C1-BIO** tells their life story (biography focus)
- **B2-HIST** tells the events of their era (historical event focus)
- Same sources serve both

### Era-Based Batches (C1-BIO + B2-HIST together)

| Batch | Era | C1-BIO modules | B2-HIST modules | Shared research |
|-------|-----|----------------|-----------------|-----------------|
| **A** | Kyivan Rus (850-1240) | M001-M012 (12) | M006-M028 (23) | Olha, Sviatoslav, Volodymyr, Yaroslav, Monomakh, Danylo |
| **B** | Lithuanian-Polish (1240-1560) | M013-M018 (6) | M029-M040 (12) | Ostrozky, Nalyvaiko, Roksolana |
| **C** | Early Cossack (1560-1648) | M015-M021 (7) | M041-M050 (10) | Vyshnevetsky, Sahaidachny |
| **D** | Khmelnytsky & Ruin (1648-1709) | M022-M028 (7) | M051-M066 (16) | Khmelnytsky, Mohyla, Sirko, Mazepa, Nemyrych |
| **E** | Late Hetmanate (1709-1785) | M029-M035 (7) | M067-M074 (8) | Orlyk, Polubotok, Apostol, Kalnyshevskyi, Skovoroda |
| **F** | Imperial era (1785-1914) | M036-M068 (33) | M075-M088 (14) | Shevchenko, Drahomanov, Franko, Hrinchenko, Hrushevskyi |
| **G** | Revolution (1914-1921) | M069-M085 (17) | M089-M097 (9) | Petliura, Sichovi striltsi, Tsentralna Rada |
| **H** | Interwar & WWII (1921-1945) | M086-M116 (31) | M098-M108 (11) | Rozstriliane vidrodzennia, OUN, UPA, Holodomor |
| **I** | Soviet era (1945-1991) | M117-M138 (22) | M109-M121 (13) | Shistdesiatnyky, Chornobyl, Diaspora |
| **J** | Independence (1991+) | M139-M156 (18) | M122-M140 (19) | Maidan, War, Tomos |

**Total: 156 BIO + 140 HIST = 296 modules across 10 batches**

### How cross-track research works

For a figure like **Ivan Mazepa**:

1. **Research phase** (one session):
   - Research Ivan Mazepa comprehensively
   - Save to: `research/ivan-mazepa-research.md` (shared)
   - Covers: biography, political career, cultural patronage, Poltava, legacy

2. **C1-BIO module** (M027: ivan-mazepa):
   - Uses the shared research
   - Focus: personal life, character, motivations, cultural patronage
   - Tone: biographical narrative

3. **B2-HIST modules** (M063-M066: mazepa-derzhavnyk, mazepa-kultura, mazepa-poltava):
   - Uses the same shared research
   - Focus: political events, military campaigns, constitutional legacy
   - Tone: historical analysis

**Shared research saves ~40% of research time for overlapping figures.**

### Non-overlapping modules

Some C1-BIO modules have no B2-HIST counterpart (e.g., artists, scientists, modern figures). These get standalone research as usual.

Some B2-HIST modules have no C1-BIO counterpart (e.g., Trypillian civilization, Scythians, synthesis chapters). These also get standalone research.

---

## 7. Execution Order

### Phase 1: Workflow Setup (Day 0)
- [x] Delete all research files (force re-research)
- [x] Update watcher daemon config (8-turn limit, stuck reports)
- [x] Update Gemini's context with lean review protocol
- [x] Bridge: sync/async mode support for both Claude and Gemini directions
- [ ] Test end-to-end on 1 module (M03 volodymyr-velykii, HEAVY-fail)
- [ ] Validate the pipeline works before scaling

### Phase 2: Batch A - Kyivan Rus (Day 1-3)
- 12 C1-BIO modules (M001-M012)
- 23 B2-HIST modules (M006-M028)
- Start with C1-BIO (biography builds the research base)
- Then B2-HIST (reuses research)
- **Cross-track research figures:** Olha, Sviatoslav, Volodymyr, Yaroslav, Monomakh, Danylo

### Phase 3: Batch B - Lithuanian-Polish (Day 3-4)
- 6 C1-BIO + 12 B2-HIST

### Phase 4-10: Remaining batches
- Follow the era order in the table above
- Each batch: C1-BIO first (builds research), then B2-HIST (reuses)

### Phase 11: LIT track (after C1-BIO + B2-HIST)
- 30 modules, standalone research
- Depends on literary analysis skills, may need different approach

---

## 8. Progress Tracking

### Per-module status
```
curriculum/l2-uk-en/{track}/status/{slug}.json
```
Updated automatically by `audit_module.sh`. Contains gate pass/fail and scores.

### Batch progress
Track via GitHub Issues:
```
/task create "Batch A: Kyivan Rus (12 BIO + 23 HIST)"
```
Update issue with progress as modules complete.

### Daily summary
```bash
npm run status:c1-bio   # Generate human-readable status report
npm run status:b2-hist
```

### Stuck modules
```
curriculum/l2-uk-en/{track}/stuck/{slug}.md
```
Human reviews and resolves these periodically.

---

## 9. Quality Gates (Non-Negotiable)

Every module must pass ALL of these before MDX generation:

| Gate | Requirement |
|------|-------------|
| Research | research/{slug}-research.md exists, 3+ sources |
| Meta | Valid structure, content_outline with word allocations |
| Word count | >= 95% of word_target |
| Richness | >= 95% for biography/history modules |
| Activities | >= 3 activities, correct types for track |
| Vocabulary | >= 24 enriched items with IPA |
| Naturalness | >= 8/10 (automated check) |
| Claude review | PASS (or PASS with minor info-only issues) |
| Audit | All gates pass (scripts/audit_module.sh exit 0) |

---

## 10. Known Risks

| Risk | Mitigation |
|------|------------|
| Gemini rate limits / cooldowns | Queue messages, continue with other work, retry later |
| Gemini loops on hard modules (like M03) | Phase-based turn budgets, stuck escalation, Claude help |
| Research quality varies | Claude review catches thin/inaccurate content |
| Scale (296 modules) | Era-based batching, cross-track research sharing |
| Context window fills up | Phase-based saves to files, fresh sessions via `/full-rebuild --from=PHASE` |
| Review loops | Hard limit: 2 review rounds, then escalate |
| Inconsistent quality | Claude review is the quality gate, not audit alone |

---

## 11. Bridge Sync/Async Architecture

### Problem
The bridge used `subprocess.run(timeout=600)` which killed agents after 10 minutes. Full module rebuilds need 30-60 minutes.

### Solution: Auto-detection from message type

| Message type | Mode | Behavior |
|-------------|------|----------|
| `request` | async (fire-and-forget) | `subprocess.Popen`, agent runs unbounded, self-reports via bridge |
| `handoff` | async (fire-and-forget) | Same as request |
| `query` | sync | `subprocess.run(timeout=300)`, response captured and routed |
| `response` | sync | Same as query |

**Applies to BOTH directions:** Claude → Gemini and Gemini → Claude.

### How async works
1. Bridge re-launches **itself** as a background process with `--no-timeout`
2. Background bridge runs the agent with `subprocess.run(timeout=None)` — no kill
3. Logs to `.mcp/servers/message-broker/logs/{agent}-{task_id}.log`
4. Agent works as long as it needs
5. When agent finishes, the **bridge** captures stdout and routes the response (same as sync)
6. Agent does NOT need to self-report — the bridge handles everything

### How sync works
1. Bridge launches agent with `subprocess.run(timeout=300)` (5 min)
2. Captures stdout
3. Routes response back via `send_message()`
4. Acknowledges original message

### CLI usage
```bash
# Auto-detect (recommended):
.venv/bin/python scripts/ai_agent_bridge.py process 42          # Gemini auto-detects
.venv/bin/python scripts/ai_agent_bridge.py process-claude 42   # Claude auto-detects

# Force async:
.venv/bin/python scripts/ai_agent_bridge.py process-claude 42 --async
```

---

## 12. Message Protocol Reference

### Gemini → Claude (review request)
```
REVIEW_REQUEST: {track} {slug}
```

### Claude → Gemini (review result)
```
REVIEW_RESULT: {track} {slug}
Score: {score}/10 {PASS|FAIL}
Issues: {count} ({summary})
Action: {what to fix} | Full report: review/{slug}-review.md
```

### Gemini → Claude (help request)
```
HELP_REQUEST: {track} {slug}
Phase: {current phase}
Problem: {specific problem description}
Files: {relevant file paths}
```

### Claude → Gemini (help response)
```
HELP_RESPONSE: {track} {slug}
Suggestion: {specific actionable suggestion}
Example: {if applicable}
```

### Watcher → Human (stuck notification)
```
STUCK: {track} {slug}
Turns: {used}/{limit}
Phase: {last phase}
Summary: {what was done, what's left}
```

---

## 13. Success Criteria

### Per module
- All 9 quality gates pass
- Claude review score >= 8.5/10
- Research file exists with 3+ sources
- MDX generated successfully

### Per batch
- All modules in batch pass quality gates
- No stuck modules remaining
- Human has reviewed and approved batch

### Per track
- All modules pass
- Track scoring (npm run score:{track}) >= 8/10
- No Russianisms, calques, or propaganda in any module
- Consistent quality across modules (no outliers below 8/10)
