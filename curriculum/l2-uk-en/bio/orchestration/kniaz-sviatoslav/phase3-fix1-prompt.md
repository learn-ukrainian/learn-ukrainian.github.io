        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `kniaz-sviatoslav`:

        ## Audit Output (last 60 lines)

        ```
             Останні роки: Загибель на порогах                                361 /  500  ❌ (-139)
     Внесок у розбудову держави                                       313 /  500  ❌ (-187)
     Історичний контекст: Русь у X столітті                           295 /  400  ❌ (-105)
     Порівняльний аналіз: Творець (Ольга) vs Завойовник (Святослав)   170 /  500  ❌ (-330)
     Спадщина: Від Князя до ЗСУ                                       297 /  300  ✅ (-3)
     Підсумок                                                         254 /  200  ✅ (+54)
     ───────────────────────────────────────────────────────────────────────────────────────
     TOTAL                                                           4207 / 5000  ❌ (-793)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (10 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x3 — robotic prose
❌ AUDIT FAILED: Transliteration detected: 'шлях (dao)'. Remove Latin in parentheses.

--- STRICT GATES (Level C1) ---
Persona      ✅ Persona Defined
Words        ❌ 4261/5000 (raw: 4625)
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
Pedagogy     ❌ 3 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 99.7% (target 95-100% (biography))
Richness     ✅ 99% (biography)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (10 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x3 — robotic prose
     → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: biography) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: biography) missing advanced activity type: comparative-study
     → FIX: Add a comparative-study activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 3 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/audit/kniaz-sviatoslav-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/status/kniaz-sviatoslav.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 6 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/kniaz-sviatoslav-audit.log for details)

Prose-relevant failures:
  lesson: 4261/5000 (raw: 4625) | pedagogy: 1 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/kniaz-sviatoslav.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

