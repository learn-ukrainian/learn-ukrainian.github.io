        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `past-passive-participles`:

        ## Audit Output (last 60 lines)

        ```
             Узгодження дієприкметників           396 /  600  ❌ (-204)
     Пасив із допоміжним дієсловом бути   322 /  600  ❌ (-278)
     Регістрова специфіка                 254 /  400  ❌ (-146)
     Практика і підсумок                  234 /  400  ❌ (-166)
     ───────────────────────────────────────────────────────────
     TOTAL                               2865 / 4000  ❌ (-1135)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (4 total): 'не просто X, а Y' x4 — robotic prose

⚠️  Richness below threshold (84% < 95% min)
   Dryness flags:
     - NO_DIALOGUE
❌ AUDIT FAILED: Transliteration detected: 'чергуванням (alternation)'. Remove Latin in parentheses.

--- STRICT GATES (Level B2) ---
Persona      ✅ Persona Defined
Words        ❌ 3273/4000 (raw: 3754)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 7/6
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 99.1% (target 90-100% (grammar))
Richness     ❌ 84% < 95% min (grammar)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (4 total): 'не просто X, а Y' x4 — robotic prose
     → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: grammar) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/past-passive-participles-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/past-passive-participles.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 6 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/past-passive-participles-audit.log for details)

Prose-relevant failures:
  lesson: 3273/4000 (raw: 3754) | pedagogy: 1 violations | richness: 84% < 95% min (grammar)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/past-passive-participles.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

