        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `volodymyr-velykii`:

        ## Audit Output (last 60 lines)

        ```
             Геополітичний вибір: Тендер світових релігій                    425 /  500  ⚠️ (-75)
     Корсунь та Хрещення: Дипломатія примусу до рівності             617 /  550  ✅ (+67)
     Державне будівництво: Змієві вали та власний карб               568 /  500  ✅ (+68)
     Культурна революція: Десятинна церква та освіта еліт            343 /  450  ❌ (-107)
     Трансформація особистості: Від деспота до милосердного батька   368 /  450  ⚠️ (-82)
     Спадщина: Деколонізація образу та тяглість Тризуба              399 /  400  ✅ (-1)
     Підсумок: Візіонер руської ойкумени                               0 /  300  ❌ (-300)
     ──────────────────────────────────────────────────────────────────────────────────────
     TOTAL                                                          4998 / 4950  ✅ (+48)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (8 total): 'не просто X, а Y' x3, 'це не було/були/була' x2, 'не лише X, а й Y' x3 — robotic prose

--- STRICT GATES (Level C1) ---
Persona      ✅ Persona Defined
Words        ✅ 5425/5000 (raw: 5669)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/5
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
Immersion    🇺🇦 99.2% (target 95-100% (biography))
Richness     ✅ 97% (biography)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (8 total): 'не просто X, а Y' x3, 'це не було/були/була' x2, 'не лише X, а й Y' x3 — robotic prose
     → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: biography) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: biography) missing advanced activity type: comparative-study
     → FIX: Add a comparative-study activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 3 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/audit/volodymyr-velykii-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/status/volodymyr-velykii.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 1 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/volodymyr-velykii-audit.log for details)

Prose-relevant failures:
  lesson: 5425/5000 (raw: 5669) | pedagogy: 1 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/volodymyr-velykii.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

