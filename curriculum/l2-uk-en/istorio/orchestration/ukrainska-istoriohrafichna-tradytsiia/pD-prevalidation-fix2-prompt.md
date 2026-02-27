        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `ukrainska-istoriohrafichna-tradytsiia`:

        ## Audit Output (last 60 lines)

        ```
             Нова українська історіографія після 1991: I — Повернення пам'яті                    535 /  450  ✅ (+85)
     Нова українська історіографія після 1991: II — Інституційне становлення             699 /  450  ✅ (+249)
     Підсумок                                                                            362 /  400  ✅ (-38)
     ──────────────────────────────────────────────────────────────────────────────────────────────────────────
     TOTAL                                                                              6396 / 5000  ✅ (+1396)
  ❌ YAML schema violations: 1
     ❌ [YAML_SCHEMA_VIOLATION] Schema error in ukrainska-istoriohrafichna-tradytsiia.yaml: Schema validation error at key '0': {'type': 'reading', 'title': 'Уривок зі вступу до Історії України-Руси', 'source': 'Михайло Грушевський', 'instruction': 'Уважно прочитайте уривок для подальшого критичного аналізу.'} is not valid under any of the given schemas
  📋 Found YAML activities file (5 activities)
  > Уривок зі вступу до Історії України-Руси: 0 items (min 1)
  > Критичний аналіз: Народницька парадигма: 1 items (min 1)
  > Есе: Роль діаспори у збереженні науки: 1 items (min 1)
  > Факти та інтерпретації: Перевірка знань: 12 items (min 5)
  > Порівняльний аналіз: Народники та Державники: 1 items (min 1)

📊 ACTIVITIES WITH LOW DENSITY:
  ❌ Уривок зі вступу до Історії України-Руси
     Current: 0 items | Required: 1 | Add: 1 more
     → Add 1 more items to this activity


--- STRICT GATES (Level C1) ---
Persona      ✅ Persona Defined
Words        ✅ 6522/5000 (raw: 7005)
Activities   ✅ 5/3
Density      ❌ 1 < 1
Unique_types ✅ 5/3 types
Priority     ✅ Priority types used
Engagement   ✅ 6/6
Audio        ℹ️ No audio
Vocab        ✅ 30/25
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ✅ Content-heavy OK (5 activities)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality 📋 Quality validation available (optional)
Research     ✅ Content aligned with research
Immersion    🇺🇦 98.4% (target 95-100% (history))
Richness     ✅ 99% (history)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY] reading 'Уривок зі вступу до Історії України-Руси' has 0 items (minimum: 1)
     → FIX: Add more items. C1 reading requires at least 1 items.
  [YAML_SCHEMA_VIOLATION] Schema error in ukrainska-istoriohrafichna-tradytsiia.yaml: Schema validation error at key '0': {'type': 'reading', 'title': 'Уривок зі вступу до Історії України-Руси', 'source': 'Михайло Грушевський', 'instruction': 'Уважно прочитайте уривок для подальшого критичного аналізу.'} is not valid under any of the given schemas
     → FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 2 violations (minor)
   → Activity density below minimum


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/istorio/audit/ukrainska-istoriohrafichna-tradytsiia-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/istorio/status/ukrainska-istoriohrafichna-tradytsiia.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/ukrainska-istoriohrafichna-tradytsiia-audit.log for details)
        ```


## Schema Reference (fix activities to match these)

### `reading` (from activities-istorio.schema.json)
**Required fields:** `type`, `title`, `id`, `text`
**Allowed fields:** `type`, `id`, `title`, `source`, `text`, `instruction`
**additionalProperties:** `False` — ANY unlisted field = schema violation


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/istorio/ukrainska-istoriohrafichna-tradytsiia.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/istorio/activities/ukrainska-istoriohrafichna-tradytsiia.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/istorio/vocabulary/ukrainska-istoriohrafichna-tradytsiia.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

