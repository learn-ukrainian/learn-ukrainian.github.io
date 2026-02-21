        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `b2-review-bridge`:

        ## Audit Output (last 60 lines)

        ```
             Складнопідрядні речення               453 /  600  ❌ (-147)
     П'ять функціональних стилів           423 /  800  ❌ (-377)
     Фразеологія в контексті               300 /  500  ❌ (-200)
     Підсумок і шлях уперед                  0 /  300  ❌ (-300)
     ────────────────────────────────────────────────────────────
     TOTAL                                2980 / 4000  ❌ (-1020)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (12 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x5 — robotic prose

⚠️  Richness below threshold (79% < 95% min)
   Dryness flags:
     - NO_DIALOGUE
❌ AUDIT FAILED: Transliteration detected: 'єктності (Agency)'. Remove Latin in parentheses.

--- STRICT GATES (Level C1) ---
Persona      ✅ Persona Defined
Words        ❌ 3498/4000 (raw: 3870)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ❌ 4/7
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
Immersion    🇺🇦 98.2% (target 90-100% (grammar))
Richness     ❌ 79% < 95% min (grammar)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (12 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x5 — robotic prose
     → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: grammar) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/audit/b2-review-bridge-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/status/b2-review-bridge.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 5 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/b2-review-bridge-audit.log for details)

Prose-relevant failures:
  lesson: 3498/4000 (raw: 3870) | engagement: 4/7 | pedagogy: 1 violations | richness: 79% < 95% min (grammar)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/b2-review-bridge.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

