        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `language-about-verbs`:

        ## Audit Output (last 60 lines)

        ```
          📋 Loaded Metadata from YAML sidecar

📋 Auditing: B1 M02 — Мова про дієслова
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/language-about-verbs.md | Target: 4000 words
  📋 Required activity types from meta: error-correction, fill-in, match-up, quiz
  📋 Template: docs/l2-uk-en/templates/b1-grammar-module-template.md (pedagogy: TTT)
  ⚠️  Outline compliance: 4 errors, 2 warnings
     ⚠️ [SECTION_LENGTH_MISMATCH] Section 'Вступ: Система дієслова' is under target word count.
     ⚠️ [SECTION_LENGTH_MISMATCH] Section 'Додаткові граматичні категорії: Спосіб і стан' is under target word count.
     ❌ [SECTION_LENGTH_MISMATCH] Section 'Форми дієслова: Складена та синтетична' is under target word count.

  📊 Section Word Analysis:
     Вступ: Система дієслова                         308 /  350  ⚠️ (-42)
     Вид дієслова: Основи термінології               697 /  500  ✅ (+197)
     Характер дії: Процес і результат                550 /  400  ✅ (+150)
     Час дієслова: Минулий, теперішній, майбутній    476 /  450  ✅ (+26)
     Термінологія заперечення                        403 /  400  ✅ (+3)
     Додаткові граматичні категорії: Спосіб і стан   363 /  450  ⚠️ (-87)
     Форми дієслова: Складена та синтетична          339 /  500  ❌ (-161)
     Практикум: Читаємо граматичні пояснення         199 /  400  ❌ (-201)
     Міні-діалоги: Говоримо про граматику            209 /  300  ❌ (-91)
     Підсумок і самоперевірка                        172 /  250  ❌ (-78)
     ──────────────────────────────────────────────────────────────────────
     TOTAL                                          3716 / 4000  ❌ (-284)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

--- STRICT GATES (Level B1) ---
Persona      ✅ Persona Defined
Words        ❌ 3886/4000 (raw: 4220)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/4
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 95.0% (B1.1 Aspect)
Richness     ✅ 94% (bridge)

Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/language-about-verbs-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/language-about-verbs.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 4 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/language-about-verbs-audit.log for details)

Prose-relevant failures:
  lesson: 3886/4000 (raw: 4220)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/language-about-verbs.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

