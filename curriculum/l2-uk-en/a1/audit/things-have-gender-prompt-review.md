# Prompt & Context Engineering Review: things-have-gender

**Track:** a1 | **Sequence:** 8
**Pipeline:** v6
**Review attempts:** 8 dispatches (5 Gemini failures → 3 Claude rounds)
**Friction reports:** 0 (no friction files generated)
**Gemini self-audit iterations:** N/A (v6 — no session JSON available; gemini-cli dispatch)

---

## Context Engineering Analysis

### Instruction → Understanding → Output Gap

| Instruction (from prompt/plan) | What was produced | Gap type | Evidence |
|---|---|---|---|
| Plan `dialogue_situations`: "At a pet shop — looking at animals. Use кіт(m), рибка(f), кошеня(n), акваріум(m), черепаха(f) — NOT room furniture." | Dialogue 1: video call showing room (кімната, стіл, ліжко, лампа, крісло). Dialogue 2: comparing bag contents. Zero pet shop vocabulary. | **instruction_overridden_by_skeleton** | Plan line 33-41: pet shop setting. Skeleton P-Dialogue1: "Video call... Марія shows her room". Content line 3-11: room tour. |
| Pre-verify CEFR guidance: "книга → книжка: Swap to книжка (A1) throughout. книга = A2." | Content uses **книга** 8 times throughout, **книжка** 0 times. | **instruction_ignored** | Pre-verify line 97-98. Content lines 17, 19, 20, 30, 52, 55, 84, 95. |
| Prompt rule 1: "IMMERSION TARGET: 10-20% Ukrainian" | Audit reports 26.8% Ukrainian | **instruction_exceeded** | Audit line 63: "26.8% (target 10-30% (M08))". The audit widened the range to 10-30% for M08, but the prompt said 10-20%. |
| Plan `dialogue_situations` speakers: Марія, Оленка | Both dialogues use Марія and Оленка ✅ | compliant | Content lines 3-11, 16-21. |
| Prompt rule 2: "EVERY plan point MUST appear" | Most plan points covered. Pet shop dialogue is the major miss. | **partial_compliance** | Content outline Dialogue 1 (room) and Dialogue 2 (bag) match plan's content_outline BUT plan's `dialogue_situations` field contradicts the content_outline. |

### Root Cause: Plan Internal Contradiction

**The plan itself contains a contradiction.** Two fields give conflicting dialogue instructions:

1. **`dialogue_situations`** (line 33-41): "At a pet shop — looking at animals and their accessories. Use animals and pet items to demonstrate він/вона/воно — **not room furniture.**"
2. **`content_outline` → Діалоги** (line 44-48): "Dialogue 1 — Video call showing your room: — Привіт! Дивись, це моя кімната. — Класно! У тебе є стіл?"

The skeleton prompt received BOTH fields. The skeleton chose to follow `content_outline` (which has concrete dialogue text) over `dialogue_situations` (which has the setting). The writing prompt then embedded the skeleton, which locked in the room-furniture approach. **The plan author likely updated `dialogue_situations` after writing `content_outline` but forgot to reconcile them.**

This is a **structural impossibility in the plan** — the pipeline has no mechanism to detect when `dialogue_situations` and `content_outline` disagree.

### Gemini Session Analysis

No Gemini session JSON is available (v6 dispatches via gemini-cli, not the old session-capture format). However, dispatch metadata reveals:

- **5 consecutive Gemini review failures** (all `ok=false`, 0 response chars, ~1.5s each)
- **Root cause**: stderr shows `Cannot use both --yolo (-y) and --approval-mode together`
- **Fallback**: Pipeline switched to Claude (`claude-opus-4-6`) which ran 3 successful review rounds
- **Implication**: Gemini never reviewed this module. Claude reviewed Claude-dispatched content (though the writer was Gemini, so no self-review violation).

### Immersion Breakdown (per section)

| Section | Approx English words | Approx Ukrainian words | Ukrainian % | Containers |
|---|---|---|---|---|
| Діалоги (Dialogues) | ~180 | ~120 | ~40% | 2 dialogue blocks |
| Він, вона, воно | ~220 | ~85 | ~28% | 0 |
| Предмети навколо | ~150 | ~120 | ~44% | 3 bulleted lists |
| Підсумок — Summary | ~200 | ~100 | ~33% | 1 table, 1 Q&A list |
| **TOTAL** | ~750 | ~425 | ~36% est. | 2 dialogues, 3 lists, 1 table |

**Note:** The audit measured 26.8% using its own counter (which may exclude certain elements). The prompt's stated target was 10-20%, though the audit config widens this to 10-30% for M08. Either way, the module is on the high end. For an M08 learner (still early A1), this is acceptable — the Ukrainian is all bolded inline words and short example sentences, not full paragraphs.

### Root Cause Verdict

**Primary gap**: plan_internal_contradiction + instruction_ignored (книга/книжка)
**Explanation**: The plan's `dialogue_situations` and `content_outline` give conflicting dialogue settings. The skeleton prompt followed `content_outline` (has concrete text) over `dialogue_situations` (has the setting). Additionally, the pre-verify CEFR guidance to swap книга→книжка was injected into the writing prompt but the writer ignored it — likely because the plan's `vocabulary_hints.required` lists "книга" and the skeleton also uses "книга", which outweighs a single CEFR note buried in the pre-verified facts.

---

## Prompt Clarity

| Issue | Severity | Template File | Details |
|---|---|---|---|
| Duplicate section in section list | LOW | v6-prompt.md | Line 724: `## Підсумок — Summary` appears twice in the "Section Structure" block (once at ~300 words, once at ~150 words). Writer saw the skeleton instead, so no impact, but future non-skeleton builds could be confused. |
| No priority signal between `dialogue_situations` and `content_outline` | **HIGH** | v6-prompt.md (plan injection) | When these two plan fields conflict, the prompt gives no guidance on which takes precedence. The skeleton chose `content_outline` because it has concrete dialogue text. |
| CEFR guidance buried in pre_verified_facts | MEDIUM | v6-prompt.md | The "книга → книжка" swap instruction is at the very end of `<pre_verified_facts>`, after 300+ lines. By the time Gemini reaches it, the skeleton (which uses книга) has already been internalized. |
| "BANNED recurring settings" contradicts plan | MEDIUM | v6-prompt.md | Line 795: "BANNED: describing a room (кімната)". But the plan's `content_outline` explicitly scripts a room-description dialogue. The skeleton followed the plan (correct), but the prompt's own rules technically ban it. |

---

## Context Gaps

| Missing Context | Impact | Fix |
|---|---|---|
| No conflict detection between `dialogue_situations` and `content_outline` | Pet shop setting lost entirely; room-furniture dialogue built instead | Add a CHECK step in skeleton prompt that cross-references `dialogue_situations` against `content_outline` dialogues. If they disagree, output a warning. |
| Pre-verify CEFR swaps not reflected in skeleton | Skeleton uses книга (A2) throughout, then writer follows skeleton faithfully | Inject CEFR swap recommendations into the skeleton prompt too, not just the writing prompt. Or: auto-patch the skeleton output before feeding to writer. |
| Exercise verification shows 0/20 vocab tested | The `exercise-verification.json` shows `tested_in_exercises: 0` for all 20 plan vocab items | Likely a tooling bug — the YAML activities clearly test these words. Investigate the verification script. |

---

## Friction Root Causes

No friction files were generated for this module (`phase-2-friction-1.md` and `phase-C-friction.md` do not exist). This is expected in v6 pipeline (friction reporting was a v5 feature).

| Friction Point | Root Cause Type | Details | Template Fix |
|---|---|---|---|
| N/A | — | V6 pipeline doesn't generate friction files | Consider adding friction capture to v6 — valuable signal is being lost. |

---

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|---|---|---|---|
| review | 8 dispatches (5 fail + 3 pass) | Gemini CLI flag conflict: `--yolo` and `--approval-mode` used together | **YES** — fix the dispatch command in the pipeline code. This is a pure infrastructure bug. |
| write | 1 | Clean first pass | N/A |
| activities | 1 | Clean first pass | N/A |

**Gemini review failures detail:** All 5 failures have identical stderr: `Cannot use both --yolo (-y) and --approval-mode together.` The pipeline then fell back to Claude. The 3 Claude review rounds produced scores of 9.4, 8.9, 9.3 (avg across dimensions). No fix loops were needed — all 3 rounds were independent review passes, not fix-and-resubmit cycles.

---

## Audit Violations (from deterministic audit)

| Violation | Severity | Root Cause | Prompt Fix? |
|---|---|---|---|
| `translate` activity at A1 (not allowed) | MEDIUM | Activities prompt doesn't list level-restricted activity types | Add `BANNED_TYPES` list to v6-activities-prompt.md for each level |
| Subordinate clause marker `що` detected | LOW | False positive — `А що ще є?` is a question word, not a subordinate clause | Audit detector could distinguish interrogative що from subordinate що |
| Metalanguage terms (рід, середній, жіночий, чоловічий) not in vocabulary | LOW | These ARE taught in the module but not listed in plan vocabulary_hints | Plan should include grammar metalanguage in vocabulary_hints |

---

## Suggested Template Fixes

### Fix 1: Plan Contradiction Detection (Priority: **HIGH**)
**Prevents:** dialogue_situations being silently overridden by content_outline
**Scope:** all modules with dialogue_situations
**Template file:** `scripts/build/v6_build.py` (CHECK phase) or skeleton prompt

Add a CHECK step that compares `dialogue_situations[*].setting` keywords against `content_outline[*].points` for the Діалоги section. If `dialogue_situations` says "not room furniture" but `content_outline` mentions "кімната" and "стіл", emit a warning:

```diff
+ ## Plan Consistency Check
+ Before building the skeleton, verify:
+ - Do `dialogue_situations` settings match `content_outline` dialogue descriptions?
+ - If they conflict, `dialogue_situations` takes PRECEDENCE (it was written later as a deliberate override).
+ - Flag: "WARNING: content_outline dialogues describe [room], but dialogue_situations specifies [pet shop]. Using dialogue_situations."
```

### Fix 2: CEFR Swaps Into Skeleton Prompt (Priority: **HIGH**)
**Prevents:** A2+ words persisting through skeleton → writer despite pre-verify flagging them
**Scope:** all modules
**Template file:** `v6-skeleton-prompt.md` or skeleton injection logic

```diff
  ## Plan
  <plan_content>
  ...
  </plan_content>

+ ## CEFR Vocabulary Adjustments
+ The following words from the plan are above the target CEFR level. Use the replacements:
+ {CEFR_SWAPS}
```

Where `{CEFR_SWAPS}` is auto-generated from pre-verify results (e.g., `книга → книжка (A1 replacement)`).

### Fix 3: Fix Gemini CLI Dispatch Flags (Priority: **HIGH**)
**Prevents:** 5 wasted review attempts per module
**Scope:** all modules
**Template file:** `scripts/build/v6_build.py` (dispatch logic)

```diff
- gemini ... --yolo --approval-mode yolo ...
+ gemini ... --approval-mode yolo ...
```

Remove the `-y`/`--yolo` flag when `--approval-mode` is already set. This is a pure code bug.

### Fix 4: Level-Restricted Activity Types (Priority: MEDIUM)
**Prevents:** `translate` activities at A1 (audit violation)
**Scope:** all A1 modules
**Template file:** `v6-activities-prompt.md`

```diff
  ## Your Task
  Generate activities for module...

+ ## Level Restrictions
+ The following activity types are NOT ALLOWED at A1:
+ - translate (introduced at A2)
+ - essay-response (introduced at B1)
+ - critical-analysis (introduced at B2)
+ Only use types from the plan's activity_hints + standard types: quiz, fill-in, match-up, group-sort, true-false, anagram, unjumble.
```

### Fix 5: Reconcile Prompt Immersion Target with Audit Config (Priority: LOW)
**Prevents:** Confusion between prompt saying "10-20%" and audit allowing "10-30%"
**Scope:** all A1 modules
**Template file:** `v6-prompt.md` (rule 1)

```diff
- 1. **IMMERSION TARGET: 10-20% Ukrainian**
+ 1. **IMMERSION TARGET: 10-30% Ukrainian** (for A1.2 modules M08-M14; A1.1 is 10-20%)
```

Or: dynamically inject the correct range from audit config.

---

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. **Plan contradiction detection** — affects any module where dialogue_situations and content_outline disagree. The pet shop setting was completely lost. Prevents silent plan override.
2. **CEFR swaps into skeleton** — affects all modules. Pre-verify catches A2+ words, but the skeleton (built before pre-verify results are available to it) locks them in. The writer follows the skeleton faithfully.
3. **Gemini CLI flag fix** — pure infrastructure bug wasting 5 dispatch attempts per module. Trivial fix, high ROI.

**Module quality despite prompt issues:** The module itself is solid (review scores 8.9-9.4, audit PASS, 1621 words vs 1200 target). The main content issue is the lost pet shop setting — all other plan points are covered. The книга/книжка swap is minor (both are valid Ukrainian). The real value of this review is the template fixes that prevent these patterns across future modules.
