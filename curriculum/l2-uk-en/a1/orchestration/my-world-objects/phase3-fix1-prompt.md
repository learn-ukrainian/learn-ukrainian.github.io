        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `my-world-objects`:

        ## Audit Output (last 60 lines)

        ```
             TOTAL                                    1808 / 2000  ❌ (-192)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Purity violations found: 2
     ❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (83% overlap): "### The "Far" Demonstratives (Той)

The "Far" words start with the letter **Т** [t].". Shares significant keywords with sentence at index 25.
     ❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'so we...'.
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (6 occurrences): (Identifying the object), (Specifying which book), (Pointing at something unknown) — breaks immersion target

📚 IMMERSION TOO LOW (9.0% vs 10-25% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2022/2000 (raw: 2404)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 8 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 3 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 9.0% LOW (target 10-25% (M05))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [CONTENT_REDUNDANCY] Redundant information detected in lesson (83% overlap): "### The "Far" Demonstratives (Той)

The "Far" words start with the letter **Т** [t].". Shares significant keywords with sentence at index 25.
     → FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
  [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'so we...'.
     → FIX: Vary sentence structure.
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (6 occurrences): (Identifying the object), (Specifying which book), (Pointing at something unknown) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 3 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/my-world-objects-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/my-world-objects.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/my-world-objects-audit.log for details)

Prose-relevant failures:
  lesson: 2022/2000 (raw: 2404) | pedagogy: 3 violations | immersion: 9.0% LOW (target 10-25% (M05))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

