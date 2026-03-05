# Prompt Engineering Review: the-cyrillic-code-i

**Track:** a1 | **Sequence:** 1
**Pipeline:** v4
**Validate attempts:** 1
**Review attempts:** 4 (2 review passes + 2 fix iterations, FAIL — needs-manual-review)
**Friction reports:** 1 (activities: NONE)
**Issue:** #731

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| LEVEL_CONSTRAINTS bans `нам` but plan requires it | HIGH | placeholders.yaml | `LEVEL_CONSTRAINTS` says "Dative case FORBIDDEN (no мені, тобі, йому, їй, **нам**, вам, їм)" but `VOCAB_HINTS` lists "нам (to us) — pronoun, decodable; both bukvars" as required. Gemini must choose between contradictory instructions. |
| Non-decodable example words not explicitly banned in prose | HIGH | phase-2 template (via placeholders) | `DECODABLE_VOCABULARY` says "Use ONLY these words in activities and reading drills" — but doesn't say "and in prose examples". Gemini used `університет`, `аеропорт`, `лимон` as pronunciation examples in prose because the ban wasn't clear about prose context. |
| PEDAGOGICAL_CONSTRAINTS allows "labelled vocabulary with immediate English translation" | MEDIUM | placeholders.yaml | The exception "Words with unknown letters may appear ONLY as labelled vocabulary with immediate English translation" is too broad. Gemini used it to justify `університет (university)` in prose, which overwhelms beginners with 12 unknown letters. Needs a cap (e.g., max 1-2 unknown letters). |
| Stress typography not specified | MEDIUM | placeholders.yaml / content template | No instruction about how to mark stress. Gemini used `мА́ма` (uppercase + accent) which is non-standard. The correct format (`ма́ма` — lowercase with combining acute) should be specified explicitly. |
| `STRUCTURAL_RULES` Rule 1 says "Each new letter gets its own H3" | LOW | placeholders.yaml | But the plan's `content_outline` uses H2 sections grouping letters (e.g., "Голосні — Vowels А, О, У" as one section). Gemini correctly used H2 grouping, but the structural rule implies H3 per letter. Minor confusion that resolved correctly. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| Plan `content_outline.points` not extracted as checklist | HIGH | The plan YAML was injected via `PLAN_PATH` (a file path), not inline. Gemini had to read and interpret the plan. Key plan points (cultural hook, O/Russian contrast, Bolshakova phrases, overview video) were missed because they weren't surfaced as an explicit checklist. **Now fixed in #734** — Pass 1 template includes plan adherence checklist. |
| No stress typography specification | MEDIUM | Gemini defaulted to uppercase-vowel-with-accent (`мА́ма`) because no standard was specified. Add `STRESS_TYPOGRAPHY` placeholder: "Use lowercase with combining acute accent: ма́ма, not мА́ма" |
| Activities YAML not provided to Pass 1 reviewer | LOW | `screen-result.json` shows activities were screened, but Pass 1 prompt only received content markdown. Pass 1 reported "Activity hints: 0 matched, 5 missing" because it couldn't see the activities file. The activities ARE present — they just weren't in the review context. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| Non-decodable words in prose | **template_gap** | `DECODABLE_VOCABULARY` restricts "activities and reading drills" but not prose examples. Gemini used `університет`, `аеропорт`, `лимон`, `сестра` as video example words in prose. | Change constraint to: "Use ONLY these words in activities, reading drills, **and prose examples**. Video key words from the plan are exempt (heard, not read)." |
| Missing plan points (cultural hook, O/Russian, etc.) | **context_gap** | Plan points buried inside YAML file path — not extracted as checklist in content prompt | **Fixed in #734** — plan adherence checking added to review. For content prompt: extract `content_outline.points` as explicit checklist in the prompt. |
| Stress typography (`мА́ма` vs `ма́ма`) | **template_gap** | No typography standard specified anywhere in placeholders | Add `STRESS_TYPOGRAPHY` to placeholders.yaml template |
| `нам` contradiction (dative ban vs required vocab) | **conflicting_guidance** | `LEVEL_CONSTRAINTS` bans dative pronouns, `VOCAB_HINTS` requires `нам`. | Add exception note to `LEVEL_CONSTRAINTS`: "Exception: `нам` is taught as decodable reading vocabulary in M1-M4, not as grammar." **Audit config already fixed** (added `нам` to `FIXED_PHRASES_DATIVE`). |
| `# Підсумок` H1 heading | **model_limitation** | Gemini occasionally generates H1 for Summary sections despite H2 convention | **Fixed in #734** — deterministic H1→H2 demotion added to `_run_deterministic_fixes()` |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate | 1 | Clean pass — no fix needed | N/A |
| review | 4 (2 passes + 2 fixes) | Pass 1 FAIL (10 missing plan points), Pass 2 FAIL (7.4/10 — non-decodable examples, stress typography) | YES — better content prompt would prevent most issues. The decodable vocabulary constraint should cover prose, and stress typography should be specified. |

**Review fix loop detail:**
- Pass 1 + Pass 2 dispatched in parallel (good — 2.5 min each)
- 20 inline fixes applied from review passes (9/9 from pass 1, 11/14 from pass 2, 3 mismatched)
- Fix iteration 1: 6/8 FIND/REPLACE pairs matched (2 skipped — YAML multiline matching failures)
- Fix iteration 2: 0/2 matched — exhausted
- **Result:** Content dramatically improved but audit still failed (H1 heading + `нам` dative false positive — both now fixed in deterministic pipeline)

## Suggested Template Fixes

### Fix 1: Extend decodable vocabulary constraint to prose (Priority: HIGH)
**Prevents:** Non-decodable words in prose examples (університет, аеропорт, лимон, сестра)
**Scope:** All A1 M1-M4 modules (Cyrillic primer)
**Template file:** `claude_extensions/phases/gemini/beginner-content.md` or placeholders generator

```diff
- Use ONLY these words in activities and reading drills. Any word with a letter
- outside this set will FAIL the decodability audit gate.
+ Use ONLY these words in activities, reading drills, AND prose examples.
+ Any word with a letter outside this set will FAIL the decodability audit gate.
+ Video key words listed in the plan's pronunciation_videos section are exempt
+ (they are heard, not read), but should not appear in prose reading examples.
```

### Fix 2: Add stress typography specification (Priority: HIGH)
**Prevents:** Non-standard stress marking (`мА́ма` instead of `ма́ма`)
**Scope:** All modules (all levels)
**Template file:** Placeholders generator (SHARED_CONTENT_RULES)

```diff
+ ### Stress Mark Typography
+
+ Use lowercase letters with a combining acute accent (´) on the stressed vowel:
+ - Correct: ма́ма, анана́с, оса́, сосна́
+ - Wrong: мА́ма, ананА́с, осА́, соснА́ (do NOT capitalize the stressed vowel)
```

### Fix 3: Resolve `нам` dative contradiction (Priority: MEDIUM)
**Prevents:** Gemini dropping `нам` from content to avoid dative ban, or audit flagging it
**Scope:** A1 M1 specifically, similar pattern for other primer words
**Template file:** Placeholders generator (LEVEL_CONSTRAINTS)

```diff
  - Dative case FORBIDDEN (no мені, тобі, йому, їй, нам, вам, їм, -ові/-еві endings)
+ - Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
+   Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
```

### Fix 4: Inject activities YAML into Pass 1 review (Priority: LOW)
**Prevents:** False "0 activities matched" in plan adherence check
**Scope:** All modules
**Template file:** `build_module.py:_build_pass1_prompt()`

```diff
  # Currently only injects content markdown
+ # Also inject activities YAML so plan adherence can check activity_hints
+ activities_path = ctx.paths.get("activities")
+ activities_text = activities_path.read_text("utf-8") if activities_path and activities_path.exists() else "(no activities)"
+ prompt_text = prompt_text.replace("{ACTIVITIES_CONTENT}", activities_text)
```

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. **Extend decodable constraint to prose** — prevents the #1 issue (non-decodable example words) that caused review FAIL and required 20+ fixes
2. **Add stress typography standard** — prevents recurring typography errors across all builds
3. **Resolve `нам` contradiction** — prevents conflicting instructions that confuse the builder and trigger false audit failures

**Positive observations:**
- Placeholders are comprehensive (594 lines) — vocabulary hints, video URLs, decodability rules, structural rules all injected
- Activities phase had zero friction (NONE) — the activities prompt and schema work well
- Validate phase passed on first attempt — the audit gate calibration is good
- Research phase completed cleanly — the beginner research template is efficient
- The review phase (with new plan adherence) caught issues effectively — 10 plan points identified, most fixed automatically

---

*Review generated by Claude Opus 4.6 for issue #731.*
