        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `trypillian-civilization`:

        ## Audit Output (last 60 lines)

        ```
             TOTAL                               7639 / 6133  ✅ (+1506)
❌ Structure check failed: Missing '## Summary'
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  📜 Meta YAML Validation: 1 issues
     ❌ [INVALID_META_YAML] Meta YAML Schema Violation at 'root': 'id' is a required property
        Fix: Correct the YAML structure to match schemas/meta-module.schema.json
  ✨ Purity violations found: 1
     ❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (86% overlap): "> «Якби ви побачили нас у денному світлі, коли влягла курява, можу запевнити, ви не впізнали б ніког...". Shares significant keywords with sentence at index 119.
❌ AUDIT FAILED: Transliteration detected: 'половою (chaff)'. Remove Latin in parentheses.

--- STRICT GATES (Level B2) ---
Persona      ✅ Persona Defined
Words        ✅ 7822/6133 (raw: 8143)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 12/5
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ❌ Missing '## Summary'
Ipa          ⚠️ 6 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 4 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Immersion    🇺🇦 98.3% (target 90-100% (history))
Richness     ✅ 99% (history)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INVALID_META_YAML] Meta YAML Schema Violation at 'root': 'id' is a required property
     → FIX: Correct the YAML structure to match schemas/meta-module.schema.json
  [CONTENT_REDUNDANCY] Redundant information detected in lesson (86% overlap): "> «Якби ви побачили нас у денному світлі, коли влягла курява, можу запевнити, ви не впізнали б ніког...". Shares significant keywords with sentence at index 119.
     → FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: history) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: history) missing advanced activity type: comparative-study
     → FIX: Add a comparative-study activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 35/100)
   → 4 violations (moderate)
   → Structure issue: Missing '## Summary'


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/audit/trypillian-civilization-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/status/trypillian-civilization.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • Structure: Missing '## Summary'

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/trypillian-civilization-audit.log for details)

Prose-relevant failures:
  meta: Missing '## Summary'
  lesson: 7822/6133 (raw: 8143) | pedagogy: 4 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/trypillian-civilization.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

