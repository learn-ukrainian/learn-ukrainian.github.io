        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-dative-i-pronouns`:

        ## Audit Output (last 60 lines)

        ```
          📋 Loaded Plan from: plans/a2/the-dative-i-pronouns.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A2 M01 — The Dative I — Pronouns
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-i-pronouns.md | Target: 3000 words
  📋 Required activity types from meta: fill-in, match-up, quiz
  📋 Template: docs/l2-uk-en/templates/a2-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Introduction / Вступ         568 /  400  ✅ (+168)
     Presentation / Презентація  1560 / 1600  ✅ (-40)
     Practice / Практика          504 /  600  ⚠️ (-96)
     Dialogues / Діалоги          456 /  400  ✅ (+56)
     ───────────────────────────────────────────────────
     TOTAL                       3088 / 3000  ✅ (+88)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (5 occurrences): (To me), (She feels cold), (Hosting a guest) — breaks immersion target

--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 3556/3000 (raw: 3940)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 7/4
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 2 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 51.9% (target 50-60% (A2.1))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: давальний, займенник, прикметник, іменник, називний
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (5 occurrences): (To me), (She feels cold), (Hosting a guest) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/the-dative-i-pronouns-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/the-dative-i-pronouns.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-dative-i-pronouns-audit.log for details)

Prose-relevant failures:
  lesson: 3556/3000 (raw: 3940) | pedagogy: 1 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-i-pronouns.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

