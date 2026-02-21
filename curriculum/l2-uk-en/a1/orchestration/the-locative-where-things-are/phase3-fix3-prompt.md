        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-locative-where-things-are`:

        ## Audit Output (last 60 lines)

        ```

========================================
  📋 Loaded Plan from: plans/a1/the-locative-where-things-are.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M13 — The Locative: Where Things Are
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-locative-where-things-are.md | Target: 2000 words
  📋 Required activity types from meta: fill-in, match-up
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Вступ: Питання «Де?»                444 /  300  ✅ (+144)
     Граматика: Місцевий відмінок        946 /  800  ✅ (+146)
     Практика: Де це знаходиться?        415 /  500  ⚠️ (-85)
     Застосування: Моя кімната і місто   357 /  400  ⚠️ (-43)
     ──────────────────────────────────────────────────────────
     TOTAL                              2162 / 2000  ✅ (+162)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (24 occurrences): (This word is your key), (Look at these changes), (Phone is on the table) — breaks immersion target

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2614/2000 (raw: 2790)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 25.5% (target 25-40% (M13))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (24 occurrences): (This word is your key), (Look at these changes), (Phone is on the table) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-locative-where-things-are-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-locative-where-things-are.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-locative-where-things-are-audit.log for details)

Prose-relevant failures:
  lesson: 2614/2000 (raw: 2790) | pedagogy: 1 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-locative-where-things-are.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

