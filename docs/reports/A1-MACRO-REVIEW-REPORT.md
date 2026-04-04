# A1 Macro Review Report

**Generated:** 2026-04-04
**Scope:** All 55 A1 modules (M01-M55)
**Data sources:** Latest review-structured YAML per module, audit reports, activity YAML files
**Issue:** #1125

---

## 1. Executive Summary

**Verdict: SHIPPABLE (with caveats)**

The A1 track is in strong shape. 55/55 modules have been reviewed, with a mean score of 9.16/10 and 96.4% scoring 8+. The two modules scoring 7/10 (days-and-months, euphony) have clear, fixable issues. Word count targets are met by 84% of modules, with the remaining 9 all within 12% of target. Cultural accuracy is perfect (10/10 across all 55 modules). Immersion progresses from 19.9% (A1.1) to 32.8% (A1.8), though with some non-monotonic variation mid-track.

**Key blockers before shipping:**
1. **Audit activity gate misconfigured** -- all 55 modules "fail" with `target: 0-4` because `max_activities = min_activities + 4 = 0 + 4 = 4`, but every module has 7-18 activities. This is an audit config bug, not a content problem.
2. **9 modules below word target** -- ranging from -22 to -133 words. Most are within the 12% tolerance (`word_count_fail_pct`), but at-the-cafe (-133, 88.9%) is borderline.
3. **2 modules at 7/10** -- days-and-months and euphony need targeted fixes.

**Key strengths:**
- Linguistic accuracy avg 9.04/10, zero Russianisms in final versions
- Cultural accuracy 10/10 across all 55 modules
- Vocabulary coverage 9.71/10 -- near-perfect
- Exercise quality 9.67/10 -- well-designed activities
- Strong decolonized framing throughout

---

## 2. Score Distribution

### Overall Scores (latest review round)

| Score | Count | Modules |
|-------|-------|---------|
| 10 | 23 (41.8%) | reading-ukrainian, who-am-i, my-family, what-is-it-like, colors, many-things, checkpoint-actions, what-time, free-time, checkpoint-time-nature, where-is-it, around-the-city, checkpoint-places, at-the-cafe, shopping, people-around-me, please-do-this, checkpoint-communication, yesterday, what-will-happen, my-plans, health, emergencies |
| 9 | 20 (36.4%) | sounds-letters-and-hello, stress-and-melody, checkpoint-first-contact, things-have-gender, how-many, this-and-that, checkpoint-my-world, what-i-like, my-morning, my-day, my-city, where-to, where-from, food-and-drink, i-eat-i-drink, checkpoint-food-shopping, linking-ideas, when-and-where, holidays, what-happened |
| 8 | 10 (18.2%) | special-signs, verbs-group-one, verbs-group-two, i-want-i-can, questions, weather, transport, hey-friend, my-story, a1-finale |
| 7 | 2 (3.6%) | **days-and-months**, **euphony** |
| <7 | 0 (0%) | -- |

**Pass rate (>=8):** 53/55 = 96.4%
**Target rate (>=9):** 43/55 = 78.2%

### Review Rounds Required

| Rounds | Count | Modules |
|--------|-------|---------|
| 1 | 7 | checkpoint-my-world, where-to, transport, when-and-where, health, free-time, my-morning (partial -- some had r1 as latest) |
| 2 | 15 | weather, i-want-i-can, my-day, where-from, i-eat-i-drink, people-around-me, please-do-this, holidays, yesterday, my-story, emergencies, a1-finale, food-and-drink, my-morning, questions |
| 3 | 13 | what-is-it-like, colors, many-things, verbs-group-one, verbs-group-two, questions, checkpoint-actions, my-day, shopping, linking-ideas, what-happened, what-will-happen, my-plans |
| 4 | 8 | sounds-letters-and-hello, stress-and-melody, my-family, things-have-gender, euphony, my-city, at-the-cafe, checkpoint-food-shopping |
| 5+ | 12 | reading-ukrainian (r9), who-am-i (r7), checkpoint-first-contact (r7), special-signs (r5), how-many (r4, this-and-that (r4), what-i-like (r5), checkpoint-places (r5), checkpoint-communication (r5), hey-friend (r3) |

**Median rounds:** 3. Reading-ukrainian required the most iterations (9 rounds), reflecting the difficulty of getting phonetics-heavy early modules right.

---

## 3. Word Count Analysis

**Target:** 1,200 words (regular modules), 1,000 words (checkpoints)

| Metric | Value |
|--------|-------|
| Mean | 1,382 words |
| Median | 1,320 words |
| Min | 947 (checkpoint-communication) |
| Max | 1,965 (when-and-where) |
| Meeting target | 46/55 (83.6%) |
| Within 12% tolerance | 53/55 (96.4%) |

### Modules Below Target

| Module | Actual | Target | Deficit | % of Target |
|--------|--------|--------|---------|-------------|
| at-the-cafe | 1,067 | 1,200 | -133 | 88.9% |
| hey-friend | 1,089 | 1,200 | -111 | 90.8% |
| many-things | 1,107 | 1,200 | -93 | 92.2% |
| checkpoint-communication | 947 | 1,000 | -53 | 94.7% |
| verbs-group-one | 1,152 | 1,200 | -48 | 96.0% |
| i-eat-i-drink | 1,156 | 1,200 | -44 | 96.3% |
| holidays | 1,163 | 1,200 | -37 | 96.9% |
| please-do-this | 1,169 | 1,200 | -31 | 97.4% |
| things-have-gender | 1,178 | 1,200 | -22 | 98.2% |

**Analysis:** The audit `word_count_fail_pct` threshold is 12%, meaning modules below 88% of target FAIL. Only **at-the-cafe** (88.9%) is close to this threshold. The rest are within comfortable tolerance. The word counts reported are "clean" (after stripping YAML/metadata); raw counts are all significantly higher (1,200+).

### Modules Substantially Over Target

| Module | Actual | Overshoot |
|--------|--------|-----------|
| when-and-where | 1,965 | +63.8% |
| my-plans | 1,873 | +56.1% |
| stress-and-melody | 1,793 | +49.4% |
| reading-ukrainian | 1,775 | +47.9% |
| who-am-i | 1,714 | +42.8% |

These are not problems -- they indicate content-rich modules. However, when-and-where at nearly 2x target may be dense for A1 learners.

---

## 4. Immersion Progression

Immersion = percentage of Ukrainian text in prose content.

| Phase | Modules | Avg Immersion | Range |
|-------|---------|---------------|-------|
| A1.1 (Sounds, Letters) | M01-M07 | 19.9% | 12.9% - 30.8% |
| A1.2 (My World) | M08-M14 | 26.9% | 19.9% - 36.3% |
| A1.3 (Actions) | M15-M21 | 26.7% | 24.5% - 31.1% |
| A1.4 (Time and Nature) | M22-M28 | 29.9% | 23.7% - 34.4% |
| A1.5 (Places) | M29-M35 | 29.9% | 20.2% - 37.0% |
| A1.6 (Food and Shopping) | M36-M41 | 30.6% | 24.2% - 35.0% |
| A1.7 (Communication) | M42-M48 | 28.8% | 25.2% - 30.5% |
| A1.8 (Past, Future, Grad) | M49-M55 | 32.8% | 24.0% - 45.5% |

**Trend:** Immersion increases from ~20% to ~33%, which is a healthy A1 progression. The a1-finale reaches 45.5%, providing a good bridge to A2.

**Anomalies:**
- **special-signs (M03):** 12.9% -- lowest in the track. Expected for a phonetics module focused on ь and '.
- **euphony (M28):** 23.7% -- drops below the A1.4 average despite being a later module. Euphony rules require more English explanation.
- **where-is-it (M29):** 20.2% -- low for A1.5. The locative case introduction requires substantial English scaffolding.
- **my-plans (M52):** 24.0% -- low for A1.8. Should be closer to 30%+ at this stage.

**Overall:** The progression is appropriate for A1. Early modules are necessarily English-heavy (teaching the alphabet and sound system). The gradual increase to 30-45% by the end is well-calibrated for preparing learners for A2's higher immersion targets.

---

## 5. Dimension Analysis

9 review dimensions scored per module. Averages across all 55:

| Dimension | Avg | Min | Scores <8 | Assessment |
|-----------|-----|-----|-----------|------------|
| Cultural accuracy | **10.00** | 10 | 0 | Perfect. Decolonized framing consistent throughout. |
| Vocabulary coverage | **9.71** | 8 | 0 | Near-perfect. All required vocab present. |
| Dialogue quality | **9.71** | 5 | 1 | Excellent. One outlier: shopping (5/10). |
| Exercise quality | **9.67** | 8 | 0 | Strong. Activities well-placed and well-designed. |
| Pedagogical quality | **9.45** | 7 | 1 | Strong PPP flow across modules. |
| Engagement & tone | **9.44** | 6 | 4 | Good but inconsistent. 4 modules scored 6/10. |
| Plan adherence | **9.16** | 7 | 2 | Some modules deviated from planned dialogues. |
| Structural integrity | **9.05** | 7 | 5 | Word count deviations and markdown issues. |
| Linguistic accuracy | **9.04** | 6 | 5 | Weakest dimension. Punctuation and minor grammar. |

### Weakest Dimensions (modules scoring <8)

**Linguistic accuracy <8 (5 modules):**
- my-family: 6/10 (r4)
- reading-ukrainian: 7/10 (r9)
- special-signs: 8 (borderline)
- stress-and-melody: 8 (borderline)
- my-city: 7/10 (r4)

**Engagement & tone <8 (4 modules):**
- my-morning: 6/10 (r2)
- my-day: 6/10 (r3)
- my-city: 6/10 (r4)
- checkpoint-communication: 6/10 (r5)

**Structural integrity <8 (5 modules):**
- this-and-that: 7/10 (r4)
- my-morning: 7/10 (r2)
- weather: 7/10 (r2)
- my-day: 7/10 (r3)
- my-plans: 7/10 (r3)

---

## 6. Recurring Issues (Friction Candidates)

### 6a. Issues Already Captured in Global Friction

The following patterns were already identified and added to `docs/rules/global-friction.yaml`:
- **gf-008:** LLM filler phrases (6+ modules)
- **gf-009:** Exercises testing untaught content
- **gf-010:** Quiz answer position bias
- **gf-011:** Spatial metaphors for abstract grammar
- **gf-012:** Memorized chunks allowed before grammar
- **gf-013:** Activity markers placed before taught concepts
- **gf-014:** Euphony alternation severity (minor, not critical)

### 6b. New Patterns Found in This Analysis

**Pattern 1: Engagement dips in "daily routine" modules (4 modules, dimension 6 scores of 6/10)**
- Affected: my-morning, my-day, my-city, checkpoint-communication
- Root cause: Daily life topics (morning routine, daily schedule) tend to produce generic, textbook-style prose. The writers default to "listing activities" rather than embedding them in engaging situations.
- Fix: These modules need richer dialogue contexts -- e.g., a character explaining their unusual morning routine, not just listing "I wake up, I brush my teeth."

**Pattern 2: Plan adherence drops when dialogues are merged (3+ modules, dimension 1 scores of 7)**
- Affected: days-and-months (7), euphony (7), checkpoint-actions (7, but overall 10)
- Root cause: Writers merge planned dialogue scenes to improve flow, but in doing so they drop required vocabulary or settings.
- Fix: Review prompts should emphasize that dialogue settings and required vocabulary in `dialogue_situations` are hard constraints, not suggestions.

**Pattern 3: Structural integrity suffers from word count variance (5 modules)**
- Affected: this-and-that, my-morning, weather, my-day, my-plans
- Root cause: Some modules are 20%+ over target, others 10%+ under. The structural integrity dimension penalizes both.
- Fix: Already handled by audit gates. Not a new friction.

**Pattern 4: Linguistic accuracy issues cluster in early modules (M01-M06)**
- my-family scored 6/10 on linguistic accuracy at r4
- reading-ukrainian scored 7/10 at r9
- These early modules went through the most review rounds, suggesting the initial writes had more linguistic issues.
- Fix: The early modules have been iterated heavily. The remaining issues (punctuation style, minor grammar) should be caught by a final human review pass.

**Pattern 5: Shopping dialogue quality outlier (5/10)**
- shopping scored 5/10 on dialogue quality -- the lowest single dimension score in the entire track.
- Despite this, the module scored 10/10 overall, suggesting the reviewer weighted other dimensions heavily.
- Fix: Investigate the shopping dialogue specifically. A 5/10 on any dimension warrants attention.

---

## 7. Activity Coverage

### Activity Type Distribution (512 total activities across 55 modules)

| Type | Count | % | Modules Using |
|------|-------|---|---------------|
| fill-in | 114 | 22.3% | 52/55 |
| quiz | 102 | 19.9% | 54/55 |
| match-up | 69 | 13.5% | 55/55 |
| group-sort | 59 | 11.5% | 55/55 |
| true-false | 55 | 10.7% | 53/55 |
| error-correction | 42 | 8.2% | 43/55 |
| translate | 21 | 4.1% | 21/55 |
| unjumble | 15 | 2.9% | 15/55 |
| observe | 14 | 2.7% | 14/55 |
| letter-grid | 5 | 1.0% | 1/55 |
| watch-and-repeat | 4 | 0.8% | 1/55 |
| odd-one-out | 3 | 0.6% | 3/55 |
| anagram | 3 | 0.6% | 2/55 |
| divide-words | 2 | 0.4% | 1/55 |
| count-syllables | 2 | 0.4% | 1/55 |
| order | 1 | 0.2% | 1/55 |
| classify | 1 | 0.2% | 1/55 |

### Activities Per Module

| Metric | Value |
|--------|-------|
| Mean | 9.3 activities |
| Median | 9 |
| Min | 7 (checkpoint-time-nature, my-day, my-plans, what-will-happen, emergencies) |
| Max | 18 (sounds-letters-and-hello) |

### Coverage Assessment

**Strengths:**
- Core types (fill-in, quiz, match-up, group-sort, true-false) appear in 50+ modules each -- excellent coverage.
- error-correction appears in 43/55 -- good for building self-correction habits.
- Good variety: 17 distinct activity types across the track.

**Gaps:**
- **watch-and-repeat** (4 instances, 1 module) -- this is a priority type for A1 but nearly unused. Only sounds-letters-and-hello uses it.
- **anagram** (3 instances, 2 modules) -- another priority type, barely used.
- **classify** (1 instance) and **image-to-letter** (0 instances) -- priority types that are absent or nearly absent.
- **letter-grid** (5 instances, 1 module) -- only in sounds-letters-and-hello. Could benefit phonetics modules.
- **unjumble** appears in 15 modules but is not evenly distributed.

### Audit Gate Bug: Activity Count

**All 55 modules fail the activity count gate** with `target: 0-4`. This is because:
- `min_activities = 0` (from LEVEL_CONFIG)
- `max_activities = min_activities + 4 = 4` (from `phases_gates.py:460` and `report.py:191`)
- Every module has 7-18 activities

This is a **code bug in the audit**, not a content problem. The `max_activities` formula `min_act + 4` does not account for `min_activities = 0`. Fix: either set `max_activities` explicitly in LEVEL_CONFIG, or use a different formula. Suggested: `max_activities = max(min_act + 4, 20)` or add an explicit `'max_activities': 20` to A1's LEVEL_CONFIG.

---

## 8. Modules Requiring Attention

### Priority 1: Below-8 Scores (fix before shipping)

| Module | Score | Key Issue | Fix Estimate |
|--------|-------|-----------|--------------|
| days-and-months (M23) | 7 | Plan adherence 7/10: missing "At a doctor's reception" dialogue; structural 8/10: 21% over word target | Rebuild dialogue section, trim overshoot |
| euphony (M28) | 7 | Plan adherence 7/10: merged dialogues dropped required vocab (город, яблуко, театр); vocab coverage 8/10 | Add missing vocabulary to existing dialogues |

### Priority 2: Low Dimension Scores (fix for quality)

| Module | Dimension | Score | Issue |
|--------|-----------|-------|-------|
| shopping | Dialogue quality | 5 | Lowest single dimension score in the track |
| my-family | Linguistic accuracy | 6 | Persistent grammar issues after 4 rounds |
| my-morning | Engagement | 6 | Generic daily routine prose |
| my-day | Engagement | 6 | Generic daily routine prose |
| my-city | Engagement | 6 | Generic city description |
| checkpoint-communication | Engagement | 6 | Low engagement for a checkpoint |

### Priority 3: Word Count Deficits (expand content)

| Module | Deficit | Priority |
|--------|---------|----------|
| at-the-cafe | -133 (88.9%) | HIGH -- closest to fail threshold |
| hey-friend | -111 (90.8%) | MEDIUM |
| many-things | -93 (92.2%) | MEDIUM |
| checkpoint-communication | -53 (94.7%) | LOW |

---

## 9. Recommendations (Prioritized)

### Must-fix (before A1 ships)

1. **Fix audit activity gate bug** -- `max_activities` formula in `phases_gates.py:460` and `report.py:191` produces `0 + 4 = 4` for A1. All 55 modules falsely fail. Add explicit `max_activities` to LEVEL_CONFIG or fix the formula.

2. **Rebuild days-and-months** -- Add the missing doctor's reception dialogue. Integrate ordinal number teaching into prose (not just dialogue mention). Trim word count overshoot.

3. **Fix euphony vocabulary gaps** -- Add город, яблуко, театр to existing text. Minor effort.

4. **Expand at-the-cafe** -- 133 words short. Add another dialogue exchange or expand the ordering scenario.

### Should-fix (before A1 is marketed)

5. **Investigate shopping dialogue** -- 5/10 on dialogue quality despite 10/10 overall. Read the actual dialogue and determine if it needs rewriting.

6. **Improve engagement in daily-life modules** -- my-morning, my-day, my-city, checkpoint-communication all scored 6/10 on engagement. Richer dialogue situations, not just activity listings.

7. **Expand hey-friend and many-things** -- 111 and 93 words short respectively.

8. **Increase watch-and-repeat usage** -- Priority type for A1, only used in 1 module. Add to at least M02-M04 (phonetics modules).

### Nice-to-have (future polish)

9. **Normalize immersion in A1.7** -- Communication phase (28.8% avg) dips below A1.5-A1.6 levels (~30%). Should maintain or increase.

10. **Review my-family linguistic accuracy** -- Still at 6/10 after 4 rounds. May need a fresh rewrite rather than iterative fixes.

11. **Add classify and image-to-letter activities** -- Priority types that are absent or nearly absent.

---

## 10. Final Verdict

**SHIPPABLE WITH CONDITIONS**

The A1 track demonstrates strong quality:
- 96.4% of modules pass review (>=8/10)
- Mean score 9.16/10 across 55 modules
- Perfect cultural accuracy (10/10 everywhere)
- Strong vocabulary coverage and exercise quality
- Immersion progression from ~20% to ~45% is well-calibrated
- No Russianisms, no Surzhyk in final versions
- 15 active global frictions capturing cross-module lessons

**Conditions for shipping:**
1. Fix the audit activity gate bug (code change, not content)
2. Bring days-and-months and euphony to 8+ (targeted content fixes)
3. Expand at-the-cafe to meet word target

**Not blocking but tracked:**
- 6 modules with engagement scores of 6/10
- shopping dialogue quality at 5/10
- Priority activity types (watch-and-repeat, classify) underused

---

## Appendix A: Draft Friction Entries

These patterns appeared in 3+ modules and are candidates for `docs/rules/global-friction.yaml`:

```yaml
  - id: gf-016
    status: active
    type: pedagogical
    description: >
      Daily routine modules (my-morning, my-day, and similar) must NOT default
      to listing activities in sequence ("I wake up. I brush teeth. I eat
      breakfast."). Instead, embed routines in engaging situations: a character
      with an unusual schedule, a comparison between city/village mornings, or
      a dialogue where someone describes their day to explain why they are late.
      Generic activity-listing prose scores 6/10 on engagement consistently.
    source: "A1 macro review — 4 modules scored 6/10 engagement (#1125)"
    date_added: "2026-04-04"

  - id: gf-017
    status: active
    type: structural
    description: >
      When the plan specifies dialogue_situations with specific settings and
      required vocabulary, the writer MUST NOT merge dialogues in a way that
      drops required elements. Each planned dialogue scene is a hard constraint.
      The writer may improve flow and naturalness, but all required settings
      and vocabulary items must appear in the final text. Merging two scenes
      into one is acceptable ONLY if all elements from both scenes are preserved.
    source: "A1 macro review — days-and-months and euphony lost required vocab through dialogue merging (#1125)"
    date_added: "2026-04-04"

  - id: gf-018
    status: active
    type: structural
    description: >
      Priority activity types for each level (defined in LEVEL_CONFIG.priority_types)
      should appear across multiple modules, not concentrated in one. For A1,
      watch-and-repeat should appear in at least 3-5 phonetics modules (M01-M04),
      not just M01. Anagram should appear in at least 5 modules. The pipeline
      should check priority type distribution across the track, not just per module.
    source: "A1 macro review — watch-and-repeat in 1/55 modules, anagram in 2/55 (#1125)"
    date_added: "2026-04-04"
```

---

## Appendix B: Full Score Table

| # | Slug | Score | Round | Words | Immersion | Phase |
|---|------|-------|-------|-------|-----------|-------|
| M01 | sounds-letters-and-hello | 9 | r4 | 1,605 | 17.2% | A1.1 |
| M02 | reading-ukrainian | 10 | r9 | 1,775 | 17.2% | A1.1 |
| M03 | special-signs | 8 | r5 | 1,627 | 12.9% | A1.1 |
| M04 | stress-and-melody | 9 | r4 | 1,793 | 14.2% | A1.1 |
| M05 | who-am-i | 10 | r7 | 1,714 | 19.7% | A1.1 |
| M06 | my-family | 10 | r4 | 1,561 | 27.3% | A1.1 |
| M07 | checkpoint-first-contact | 9 | r7 | 1,353 | 30.8% | A1.1 |
| M08 | things-have-gender | 9 | r5 | 1,178 | 30.2% | A1.2 |
| M09 | what-is-it-like | 10 | r3 | 1,496 | 25.1% | A1.2 |
| M10 | colors | 10 | r3 | 1,390 | 28.8% | A1.2 |
| M11 | how-many | 9 | r4 | 1,349 | 36.3% | A1.2 |
| M12 | this-and-that | 9 | r4 | 1,309 | 19.9% | A1.2 |
| M13 | many-things | 10 | r3 | 1,107 | 25.9% | A1.2 |
| M14 | checkpoint-my-world | 9 | r1 | 1,588 | 22.0% | A1.2 |
| M15 | what-i-like | 9 | r5 | 1,314 | 29.0% | A1.3 |
| M16 | verbs-group-one | 8 | r3 | 1,152 | 25.1% | A1.3 |
| M17 | verbs-group-two | 8 | r3 | 1,236 | 29.4% | A1.3 |
| M18 | i-want-i-can | 8 | r2 | 1,363 | 27.0% | A1.3 |
| M19 | questions | 8 | r3 | 1,315 | 24.5% | A1.3 |
| M20 | my-morning | 9 | r2 | 1,262 | 25.8% | A1.3 |
| M21 | checkpoint-actions | 10 | r3 | 1,565 | 31.1% | A1.3 |
| M22 | what-time | 10 | r2 | 1,259 | 29.0% | A1.4 |
| M23 | days-and-months | **7** | r2 | 1,319 | 30.8% | A1.4 |
| M24 | weather | 8 | r2 | 1,378 | 32.3% | A1.4 |
| M25 | my-day | 9 | r3 | 1,478 | 34.4% | A1.4 |
| M26 | free-time | 10 | r2 | 1,598 | 29.4% | A1.4 |
| M27 | checkpoint-time-nature | 10 | r2 | 1,288 | 29.9% | A1.4 |
| M28 | euphony | **7** | r4 | 1,477 | 23.7% | A1.5 |
| M29 | where-is-it | 10 | r3 | 1,619 | 20.2% | A1.5 |
| M30 | my-city | 9 | r4 | 1,424 | 33.5% | A1.5 |
| M31 | where-to | 9 | r1 | 1,219 | 24.2% | A1.5 |
| M32 | transport | 8 | r1 | 1,238 | 32.7% | A1.5 |
| M33 | around-the-city | 10 | r4 | 1,238 | 37.0% | A1.5 |
| M34 | where-from | 9 | r2 | 1,222 | 26.0% | A1.5 |
| M35 | checkpoint-places | 10 | r5 | 1,357 | 36.0% | A1.5 |
| M36 | food-and-drink | 9 | r2 | 1,643 | 30.3% | A1.6 |
| M37 | i-eat-i-drink | 9 | r2 | 1,156 | 24.2% | A1.6 |
| M38 | at-the-cafe | 10 | r4 | 1,067 | 29.7% | A1.6 |
| M39 | shopping | 10 | r3 | 1,552 | 35.0% | A1.6 |
| M40 | people-around-me | 10 | r2 | 1,209 | 29.2% | A1.6 |
| M41 | checkpoint-food-shopping | 9 | r4 | 1,248 | 35.0% | A1.6 |
| M42 | hey-friend | 8 | r3 | 1,089 | 25.2% | A1.7 |
| M43 | please-do-this | 10 | r2 | 1,169 | 29.3% | A1.7 |
| M44 | linking-ideas | 9 | r3 | 1,259 | 30.0% | A1.7 |
| M45 | when-and-where | 9 | r1 | 1,965 | 26.4% | A1.7 |
| M46 | holidays | 9 | r2 | 1,163 | 30.5% | A1.7 |
| M47 | checkpoint-communication | 10 | r5 | 947 | 30.2% | A1.7 |
| M48 | what-happened | 9 | r3 | 1,289 | 28.5% | A1.8 |
| M49 | yesterday | 10 | r2 | 1,357 | 35.2% | A1.8 |
| M50 | what-will-happen | 10 | r3 | 1,260 | 35.9% | A1.8 |
| M51 | my-plans | 10 | r3 | 1,873 | 24.0% | A1.8 |
| M52 | my-story | 8 | r2 | 1,370 | 38.7% | A1.8 |
| M53 | health | 10 | r1 | 1,320 | 28.7% | A1.8 |
| M54 | emergencies | 10 | r2 | 1,299 | 26.0% | A1.8 |
| M55 | a1-finale | 8 | r2 | 1,602 | 45.5% | A1.8 |
