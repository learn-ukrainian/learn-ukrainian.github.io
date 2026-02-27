        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `kniaz-yaroslav-mudryi`:

        ## Audit Output (last 60 lines)

        ```
             Спадщина та канонізація               455 /  500  ✅ (-45)
     Підсумок                              222 /  300  ❌ (-78)
     ────────────────────────────────────────────────────────────
     TOTAL                                4294 / 5000  ❌ (-706)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  📜 Meta YAML Validation: 1 issues
     ❌ [INVALID_META_YAML] Meta YAML Schema Violation at 'root': 'id' is a required property
        Fix: Correct the YAML structure to match schemas/meta-module.schema.json
  ✨ Prose quality violations found: 1
     ❌ [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (11 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x4 — robotic prose

--- STRICT GATES (Level C1) ---
Persona      ✅ Persona Defined
Words        ❌ 4461/5000 (raw: 4696)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ❌ 4/5
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
Research     ✅ Content aligned with research
Immersion    🇺🇦 99.6% (target 95-100% (biography))
Richness     ✅ 95% (biography)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INVALID_META_YAML] Meta YAML Schema Violation at 'root': 'id' is a required property
     → FIX: Correct the YAML structure to match schemas/meta-module.schema.json
  [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (11 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x4 — robotic prose
     → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: biography) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: biography) missing advanced activity type: comparative-study
     → FIX: Add a comparative-study activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 4 violations (moderate)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/audit/kniaz-yaroslav-mudryi-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/status/kniaz-yaroslav-mudryi.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 4 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/kniaz-yaroslav-mudryi-audit.log for details)

Prose-relevant failures:
  lesson: 4461/5000 (raw: 4696) | engagement: 4/5 | pedagogy: 2 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/kniaz-yaroslav-mudryi.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

