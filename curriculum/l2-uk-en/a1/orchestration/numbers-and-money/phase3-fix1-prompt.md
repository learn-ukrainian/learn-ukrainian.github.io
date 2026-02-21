        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `numbers-and-money`:

        ## Audit Output (last 60 lines)

        ```
             Числа від 0 до 20                       365 /  350  ✅ (+15)
     Десятки та сотня                        305 /  300  ✅ (+5)
     Граматика: Правило 1-2-5 та валюта      349 /  450  ❌ (-101)
     В магазині: Як запитати ціну            182 /  350  ❌ (-168)
     Практика: Лічба та покупки              222 /  300  ❌ (-78)
     Культурний контекст: Історія гривні     239 /  200  ✅ (+39)
     ──────────────────────────────────────────────────────────────
     TOTAL                                  1955 / 2200  ❌ (-245)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Purity violations found: 1
     ❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "Which form of "hryvnia" do you use with the number **10**?". Shares significant keywords with sentence at index 108.

📚 IMMERSION TOO LOW (16.4% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2361/2000 (raw: 2665)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 24 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 16.4% LOW (target 25-40% (M17))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "Which form of "hryvnia" do you use with the number **10**?". Shares significant keywords with sentence at index 108.
     → FIX: Remove redundant paragraphs. Ensure each section adds new unique value.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 1 violations (minor)
   → Immersion 9% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/numbers-and-money-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/numbers-and-money.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 3 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/numbers-and-money-audit.log for details)

Prose-relevant failures:
  lesson: 2361/2000 (raw: 2665) | pedagogy: 1 violations | immersion: 16.4% LOW (target 25-40% (M17))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/numbers-and-money.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

