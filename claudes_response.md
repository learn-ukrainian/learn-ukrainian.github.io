Hi Claude,

I've investigated the pipeline and found exactly why B1 activities are failing the density audit and why the workbook is so thin. 

Here is the breakdown and my proposed fixes.

### A) Diagnose where the density bug lives in the pipeline

The density bug lives entirely in **`scripts/build/phases/v6-activities.md`** (the prompt template).

1. **Missing Placeholders:** `scripts/build/v6_build.py` correctly calculates dynamic targets like `{ITEMS_MIN}`, `{WORKBOOK_MIN}`, `{WORKBOOK_MAX}`, `{INLINE_ALLOWED_TYPES}`, and `{WORKBOOK_ALLOWED_TYPES}` from `config_tables.py`. However, **the `v6-activities.md` template never uses these placeholders!** It hardcodes "Default minimum: 6 items per activity" for everyone and ignores the workbook targets.
2. **Bad Few-Shot Examples:** The YAML schema example in `v6-activities.md` shows exactly ONE item per activity (e.g., one `quiz` question, one `fill-in` sentence). LLMs heavily anchor on structural examples, so it blindly copies this 1-item pattern, ignoring the text rule about "6 items minimum". 
3. **Thin Workbook:** Because `{WORKBOOK_MIN}` isn't in the prompt, the LLM doesn't know it should generate 8-12 workbook activities. It just reads the 3-4 `activity_hints` from the plan, turns them into 3-4 activities, and stops.

### B) Propose concrete fixes

**1. Inline activities & Density (Prompt-level)**
In `scripts/build/phases/v6-activities.md`:
- Replace the hardcoded `6 items` with `{ITEMS_MIN} items`.
- **CRITICAL:** Update the YAML schema examples to explicitly demand the minimums. 
  Instead of:
  ```yaml
  items:
    - question: "..."
  ```
  Change it to:
  ```yaml
  items: # ⚠️ MUST GENERATE AT LEAST {ITEMS_MIN} ITEMS HERE
    - question: "..."
    # ... generate {ITEMS_MIN} or more items total ...
  ```

**2. Workbook expansion (Prompt-level)**
In `scripts/build/phases/v6-activities.md`, update the instructions to use the injection variables:
- Change: `Workbook = 4-8 deeper practice...` 
- To: `Workbook = {WORKBOOK_MIN} to {WORKBOOK_MAX} deeper practice exercises covering the full topic.`
- Add a hard rule: "You MUST generate at least `{WORKBOOK_MIN}` activities in the `workbook:` list. If the plan's `activity_hints` are exhausted, invent new ones using `{WORKBOOK_ALLOWED_TYPES}`."

**3. Type diversity & Workbook vs Inline Separation**
- The user's pedagogical rule ("workbook types must not duplicate inline types") is slightly extreme—seeing a quiz inline and a harder quiz in the workbook is pedagogically sound. However, we already have a built-in solution! 
- `config_tables.py` already defines `INLINE_ALLOWED_TYPES` (quiz, true-false, fill-in...) and `WORKBOOK_ALLOWED_TYPES` (cloze, error-correction, essay-response, unjumble...). 
- **Fix:** Inject these into `v6-activities.md` so the LLM explicitly knows which types go where. This guarantees separation without writing complex "do not duplicate" rules that the LLM might mess up.

### C) Should this land in the same commit?

**YES. Bundle it with the immersion fix.** 
Modifying `v6-activities.md` to include these placeholders and updating the YAML examples will take Codex ~15-20 minutes. If we don't fix this now, the B1 rebuild will immediately fail the activities audit, and you'll have to rerun the `ACTIVITIES` pipeline for all 35 modules anyway. Do it now.

### D) Existing audit gates — are they sufficient?

In `scripts/audit/config.py`:
- **Raise `min_types_unique`:** For `B1-grammar`, raise it from `3` to `5`. For a 4000-word module with ~15 total activities, 3 unique types is way too low and encourages quiz spam.
- **Add `max_quiz_percentage: 0.25`:** Yes, add this gate to `scripts/audit/phases_activity.py` (and the config). Quizzes are an easy out for the LLM; capping them forces diversity.
- **Workbook Minimums:** The prompt fix (`{WORKBOOK_MIN}`) will solve the generation side, but adding a check to `audit/phases_activity.py` that verifies `len(workbook_activities) >= 8` for B1 would guarantee it.

Let me know if you need me to jump in and edit `v6-activities.md` directly, but Codex should be able to handle this quickly alongside the immersion work!
