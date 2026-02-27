        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `greeks-crimea-olbia`:

        ## Audit Output (last 60 lines)

        ```
             Підсумок                                255 /  400  ❌ (-145)
     ──────────────────────────────────────────────────────────────
     TOTAL                                  4012 / 5000  ❌ (-988)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  📜 Meta YAML Validation: 1 issues
     ❌ [INVALID_META_YAML] Meta YAML Schema Violation at 'root': 'id' is a required property
        Fix: Correct the YAML structure to match schemas/meta-module.schema.json
  ✨ Prose quality violations found: 1
     ❌ [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (8 total): 'не просто X, а Y' x3, 'це не було/були/була' x3, 'не лише X, а й Y' x2 — robotic prose
❌ AUDIT FAILED: Transliteration detected: 'свободою (eleutheria)'. Remove Latin in parentheses.

--- STRICT GATES (Level B2) ---
Persona      ✅ Persona Defined
Words        ❌ 4146/5000 (raw: 4357)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/5
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 4 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ⚠️ Refresh recommended: Research has 5+ sources but content cites 0
Immersion    🇺🇦 98.5% (target 90-100% (history))
Richness     ✅ 95% (history)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INVALID_META_YAML] Meta YAML Schema Violation at 'root': 'id' is a required property
     → FIX: Correct the YAML structure to match schemas/meta-module.schema.json
  [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (8 total): 'не просто X, а Y' x3, 'це не було/були/була' x3, 'не лише X, а й Y' x2 — robotic prose
     → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: history) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: history) missing advanced activity type: comparative-study
     → FIX: Add a comparative-study activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 4 violations (moderate)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/greeks-crimea-olbia-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/greeks-crimea-olbia.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 5 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/greeks-crimea-olbia-audit.log for details)

Prose-relevant failures:
  lesson: 4146/5000 (raw: 4357) | pedagogy: 2 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/greeks-crimea-olbia.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

