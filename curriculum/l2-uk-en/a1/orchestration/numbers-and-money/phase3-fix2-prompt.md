        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `numbers-and-money`:

        ## Audit Output (last 60 lines)

        ```

========================================
  📋 Loaded Plan from: plans/a1/numbers-and-money.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M17 — Numbers & Money
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/numbers-and-money.md | Target: 2000 words
  📋 Required activity types from meta: fill-in, quiz
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  ⚠️ HYDRATION NOTE: Outline sums to 2200, exceeding word_target 2000
     Additional 200 words (allowed for content depth)

  📊 Section Word Analysis:
     Розминка: Числа в повсякденному житті   301 /  250  ✅ (+51)
     Числа від 0 до 20                       399 /  350  ✅ (+49)
     Десятки та сотня                        306 /  300  ✅ (+6)
     Граматика: Правило 1-2-5 та валюта      397 /  450  ⚠️ (-53)
     В магазині: Як запитати ціну            376 /  350  ✅ (+26)
     Практика: Лічба та покупки              310 /  300  ✅ (+10)
     Культурний контекст: Історія гривні     253 /  200  ✅ (+53)
     ──────────────────────────────────────────────────────────────
     TOTAL                                  2342 / 2200  ✅ (+142)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (23.9% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2738/2000 (raw: 3052)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 28 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 23.9% LOW (target 25-40% (M17))

Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/numbers-and-money-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/numbers-and-money.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/numbers-and-money-audit.log for details)

Prose-relevant failures:
  lesson: 2738/2000 (raw: 3052) | immersion: 23.9% LOW (target 25-40% (M17))
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

