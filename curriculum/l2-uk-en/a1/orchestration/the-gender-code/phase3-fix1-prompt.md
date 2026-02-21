        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-gender-code`:

        ## Audit Output (last 60 lines)

        ```
             Культурний контекст: Жива мова            216 /  300  ❌ (-84)
     ────────────────────────────────────────────────────────────────
     TOTAL                                    1805 / 2000  ❌ (-195)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Purity violations found: 1
     ❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (78% overlap): "> [!context]
> **Usage Note: "Моя"**
> When you possess a feminine object, you use the word **моя** ...". Shares significant keywords with sentence at index 31.

📚 IMMERSION TOO LOW (9.8% vs 10-25% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2129/2000 (raw: 2368)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 7/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 7 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 9.8% LOW (target 10-25% (M03))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: рід, чоловічий, жіночий, середній
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
  [CONTENT_REDUNDANCY] Redundant information detected in lesson (78% overlap): "> [!context]
> **Usage Note: "Моя"**
> When you possess a feminine object, you use the word **моя** ...". Shares significant keywords with sentence at index 31.
     → FIX: Remove redundant paragraphs. Ensure each section adds new unique value.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-gender-code-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-gender-code.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 2 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-gender-code-audit.log for details)

Prose-relevant failures:
  lesson: 2129/2000 (raw: 2368) | pedagogy: 1 violations | immersion: 9.8% LOW (target 10-25% (M03))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

