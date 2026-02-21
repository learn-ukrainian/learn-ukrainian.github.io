# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/scythians-sarmatians.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/activities/scythians-sarmatians.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/vocabulary/scythians-sarmatians.yaml`

---

## Review (from Phase D.1)

# Рецензія: Скіфи та сармати — Володарі степу

**Reviewed-By:** claude-opus-4-6

**Level:** B2_HIST | **Module:** 2
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PASS (with minor gaps)
- Sections: 7/7 H2 headers match plan outline (Розминка, Скіфи, Сармати, Культура, Первинні джерела, Деколонізація, Підсумок)
- Vocabulary: 4/12 required items in vocab YAML (скіф, сармат, кочівник, курган); missing степ, кіннота, лучник, плем'я, цар, золото, пектораль is present
- Grammar scope: CLEAN — uses historical narrative and past tense in scientific text as specified
- Objectives: 3/3 addressed (describe cultures, analyze primary sources, argue significance)
- Activity alignment: 4/4 plan types present (reading, essay-response, comparative-study, critical-analysis); true-false added (acceptable). However, critical-analysis focuses on symbolic gifts rather than plan's "gold artifacts including the pectoral"
- Підсумок missing explicit "Козак Мамай = скіф з бандурою" iconographic lineage (plan requirement)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong narrative arc with vivid scenes (Darius campaign, Pectoral discovery). "Would I Stay?" 4/5 — genuinely engaging throughout, but Культура section loses momentum without callout breaks |
| 2 | Coherence | 8/10 | <7 | Verbatim phrase duplication at lines 105 and 129: «Співпраця перетворилася на унікальний творчий симбіоз» — identical sentence in two different sections breaks coherence |
| 3 | Relevance | 9/10 | <7 | Deeply relevant to B2-HIST track goals; strong connections to Ukrainian identity and modern context throughout |
| 4 | Educational | 9/10 | <7 | All 3 learning objectives addressed; primary sources woven into narrative; decolonization perspective is substantive |
| 5 | Language | 8/10 | <8 | Strong literary Ukrainian overall, but several paragraphs exceed 200 words (lines 25, 153); tense mixing at line 139 (present "не припаяні"/"мають" abruptly shifts to past "рухався"/"видавала") |
| 6 | Pedagogy | 8/10 | <7 | CBI approach executed well; however Культура та Мистецтво section (~700+ words) has zero engagement callouts — a pacing dead zone for B2 learners |
| 7 | Immersion | 10/10 | <6 | 99.6% Ukrainian; target 98-100% — within range. Only non-Ukrainian: technical terms (pars pro toto, Got-Alania) |
| 8 | Activities | 8/10 | <7 | 5 activities cover reading/essay/comparative/critical/true-false. True-false has 10 strong items. Critical-analysis focuses on Darius gifts, not gold artifact analysis as plan specified |
| 9 | Richness | 9/10 | <6 | Excellent primary source integration (Herodotus, Strabo, Pseudo-Hippocrates); decolonization is substantive; cultural continuity (Scythian→Cossack) well developed |
| 10 | Beginner Safety | 8/10 | <7 | B2-HIST learners well-served; vocabulary in context; engagement boxes provide scaffolding. Some paragraphs may overwhelm (line 153 is ~250 words unbroken) |
| 11 | LLM Fingerprint | 7/10 | <7 | Verbatim phrase duplication (lines 105/129) is a clear generation artifact; "Уявіть" used twice (lines 25, 59) as drama injection pattern; no "це не просто" rhetoric but some formulaic constructions |
| 12 | Linguistic Accuracy | 9/10 | <9 | Ukrainian is native-quality overall; morphology and syntax correct; minor issue with tense consistency at line 139 |
| 13 | Factual Accuracy | 7/10 | <8 | Fabricated Mozolovsky description (line 139); research says 48 figures but prose claims 160+; kontos length 4–4.5m vs research 3-4m; Herodotus quote paraphrased in direct speech; multiple ungrounded claims (see Factual Verification) |

**Weighted Overall:**
```
(9×1.5 + 8×1.0 + 9×1.0 + 9×1.2 + 8×1.1 + 8×1.2 + 10×1.0 + 8×1.3 + 9×0.9 + 8×1.3 + 7×1.0 + 9×1.5 + 7×1.5) / 15.5
= (13.5 + 8.0 + 9.0 + 10.8 + 8.8 + 9.6 + 10.0 + 10.4 + 8.1 + 10.4 + 7.0 + 13.5 + 10.5) / 15.5
= 129.6 / 15.5
= 8.4/10
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Colonial framing: CLEAN — references to Russian/Soviet historiography appear only in legitimate decolonization contexts (lines 193, 203)
- Grammar scope: CLEAN
- Activity errors: CLEAN
- Beginner safety: 4/5 (long paragraphs may overwhelm)
- Factual accuracy: FAIL — 3 discrepancies with research notes, 1 fabricated attribution, 5+ ungrounded claims

## Critical Issues Found

### Issue 1: Fabricated Mozolovsky Attribution (CRITICAL — Factual Accuracy)
- **Location**: Line 139 / Section "Золота Пектораль: «Мона Ліза» степу"
- **Original**: «Мозолевський згадував, що коли він обережно зняв шар глини, золото засяяло так яскраво, ніби сонце вийшло з-під землі після тисячолітнього затемнення»
- **Problem**: This poetic description is fabricated. The research notes contain Mozolovsky's actual words: «Я бачив її у снах... І коли вона блиснула під ножем, я зрозумів, що життя прожите не дарма». The prose invents a different, more lyrical paraphrase and attributes it to him as recalled speech. Putting fabricated words in a real person's mouth is a critical factual error.
- **Fix**: Replace with the actual Mozolovsky quote from research, or rewrite as third-person description without attribution: «Коли археолог обережно зняв шар глини, під ним блиснуло золото...» (without implying it's Mozolovsky's remembered phrasing).

### Issue 2: Verbatim Phrase Duplication (LLM Fingerprint)
- **Location**: Lines 105 and 129
- **Original (both)**: «Співпраця перетворилася на унікальний творчий симбіоз»
- **Problem**: The exact same sentence appears in two different sections (Сарматизація Боспору at line 105, and Симбіоз майстрів at line 129). This is a clear LLM generation artifact — the model produced the same phrase twice. At line 105 it continues "коли класична Еллада розчинялася у безмежному морі степового світу", and at line 129 it continues about Greek technique + Scythian soul. The duplication breaks coherence and is a detectable fingerprint.
- **Fix**: Rewrite line 105 to remove the duplicated phrase entirely. The section already establishes the cultural fusion concept; replace with something like: «Цей процес створив феноменальний культурний сплав, коли класична Еллада...»

### Issue 3: Pectoral Figure Count Discrepancy (Factual Accuracy)
- **Location**: Line 139 / Section "Золота Пектораль"
- **Original**: «понад 160 окремих фігурок людей і тварин, виконаних з неймовірною, майже мікроскопічною точністю»
- **Problem**: Research notes (engagement hooks section) state "48 фігур людей і тварин". The prose claims "понад 160." While some sources do cite ~160 total decorative elements when counting all ornamental details, the research note specifically says 48 for human and animal figures. The prose should match the module's own research or explicitly note the different counting methodology.
- **Fix**: Change to «близько 48 фігурок людей і тварин та десятки рослинних орнаментів» or verify the 160 figure and update the research notes accordingly.

### Issue 4: Paraphrased Herodotus Quote in Direct Speech (Factual Accuracy)
- **Location**: Line 67 / Section "Дипломатія символів"
- **Original**: «Якщо ви, перси, не злетите в небо, як птахи, або не сховаєтесь глибоко в землю, як миші, або не стрибнете у болото, як жаби, то ви ніколи не повернетесь назад, вражені цими нашими стрілами»
- **Problem**: This is presented as a direct quote from Gobryas (Гобрій) with quotation marks, but it's a paraphrase. The research notes cite a different translation from Herodotus IV, 132: «Якщо ви, перси, не станете птахами і не полетите високо в небо, або мишами і не сховаєтеся в землю, або жабами і не пострибаєте в болота, то ви не повернетеся до себе, вас загублять оці стріли». Altering a primary source quote while presenting it as direct speech is a factual accuracy issue.
- **Fix**: Either use the research version verbatim or change to indirect speech: «Гобрій пояснив справжнє значення: мовляв, якщо перси не злетять у небо...»

### Issue 5: Kontos Length Discrepancy (Factual Accuracy — Minor)
- **Location**: Line 88 / Section "Військова революція"
- **Original**: «Його довжина сягала 4–4,5 метрів»
- **Problem**: Research notes state the spear length as "3-4 метри" (section-mapped notes for Сармати I). The prose extends this to 4–4.5 meters without justification.
- **Fix**: Change to «Його довжина сягала 3–4 метрів» to match research.

### Issue 6: Pacing Dead Zone in Культура Section (Pedagogy)
- **Location**: Lines 117–154 / Section "Культура та Мистецтво"
- **Problem**: This is the longest section (~700+ words across 6 subsections) with zero engagement callout boxes. Every other major section has at least one `[!...]` box. The Пектораль subsection (lines 136–148) and Кургани subsection (line 150–153) are dense with no breathing room. Line 153 is a single paragraph of ~250 words.
- **Fix**: Add at least one `[!did-you-know]` or `[!context]` callout in the Культура section. Break line 153 (Кurgani paragraph) into two paragraphs. Consider adding a callout about the Pectoral's weight (1150g) or the Solokha comb.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 105 | «Співпраця перетворилася на унікальний творчий симбіоз» | Rewrite (duplicate of line 129) | Duplication |
| 139 | «Фігурки не припаяні намертво, деякі з них мають рухомі елементи, та коли цар рухався, пектораль видавала тихий, мелодійний дзвін» | «Фігурки не припаяні намертво, деякі з них мали рухомі елементи, і коли цар рухався, пектораль видавала тихий, мелодійний дзвін» | Tense mixing (present→past for consistency) |
| 103 | «наслідувати сильним сусідам» | «наслідувати сильних сусідів» | Questionable case governance (Dative vs Accusative with наслідувати) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? PASS — Розминка builds context gradually before main content
- Instructions clear? PASS — Activities well-structured with clear prompts
- Quick wins? PASS — True-false activity provides accessible entry point
- Ukrainian scary? PASS — Literary quality is high, context clues embedded
- Come back tomorrow? FAIL — The Культура section (lines 117-154) is a dense wall of art history with no engagement break; a B2 learner may lose focus

## Strengths

- **Narrative voice is exceptional**: The Darius campaign section (lines 54-59) reads like a gripping historical thriller. The paragraph beginning «Уявіть собі цей похід: тисячі перських солдатів ідуть під палючим сонцем» genuinely creates tension and engagement.
- **Decolonization is substantive, not token**: Section "Деколонізаційний погляд" (lines 190-217) doesn't just check a box — it integrates Malanyk's "Степова Еллада" concept and the Blok counter-narrative into a coherent argument about Ukrainian identity.
- **Primary source integration**: Herodotus, Strabo, and Pseudo-Hippocrates are woven into the narrative rather than isolated in a separate section. The Gerodot block quote (lines 164-166) serves as a powerful textual anchor.
- **Emotional peak at Pectoral**: The three-tiered cosmogony reading (lines 141-148) is the intellectual climax of the module — genuinely illuminating.
- **Activity quality**: The essay-response and comparative-study activities are well-crafted for B2, requiring analysis rather than recall.

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Factual Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 139: Replace fabricated Mozolovsky paraphrase with actual quote from research: «Я бачив її у снах... І коли вона блиснула під ножем, я зрозумів, що життя прожите не дарма»
2. Line 139: Change «понад 160 окремих фігурок» to «близько 48 фігурок людей і тварин та численні рослинні орнаменти» (or verify 160 and update research)
3. Line 67: Replace paraphrased direct quote with research version from Herodotus IV, 132
4. Line 88: Change «4–4,5 метрів» to «3–4 метри»
5. Line 113: Add hedging language to Catalonia etymology, Saltivska-Mayatska, and Khazar claims since they're not in research notes

**Expected score after fix:** 9/10

### Coherence: 8/10 → 9/10
**What to fix:**
1. Line 105: Rewrite «Співпраця перетворилася на унікальний творчий симбіоз» to eliminate duplication with line 129

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 139: Fix tense mixing (change «мають» → «мали»)
2. Line 153: Split into two paragraphs at approximately "Внутрішня структура..."
3. Line 25: Split at approximately "Кочівники ніколи не блукали безцільно..."

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add `[!did-you-know]` callout in Культура section (e.g., between Звіриний стиль and Симбіоз майстрів subsections, or within the Пектораль subsection)
2. Break the Кургани paragraph (line 153) into two parts with a callout between them

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Eliminate verbatim duplication (line 105 rewrite)
2. Vary one of the two "Уявіть" usages (lines 25 or 59) — change one to a different rhetorical device

**Expected score after fix:** 8/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Rework critical-analysis activity to focus on gold artifact analysis (Pectoral symbolism) per plan, or add a second critical-analysis activity about the Pectoral's three tiers

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 8×1.3 + 8×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 10.0 + 11.7 + 8.1 + 10.4 + 8.0 + 13.5 + 13.5) / 15.5
= 138.2 / 15.5
= 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: YES (Chronology + Key Facts sections in research)
- Dates checked: 6 (all correct — VII ст. до н.е. ✓, 513 р. до н.е. ✓, IV ст. до н.е. ✓, III ст. до н.е. ✓, 21 червня 1971 ✓, XVI-XVII ст. ✓)
- Named figures verified: 8 (Геродот ✓, Дарій I ✓, Іданфірс ✓, Мозолевський ✓, Страбон ✓, Блок ✓, Маланюк ✓, Амага — not in research)
- Primary quotes cross-referenced: 1/2 matched (Gerodot block quote at line 166 matches research; Gobryas quote at line 67 is paraphrased)
- Chronological sequence: CONSISTENT
- Claims without research grounding: 6 found:
  - Line 113: Catalonia etymology (Got-Alania hypothesis) — not in research
  - Line 113: Saltivska-Mayatska culture / Khazar Khaganate connection — not in research
  - Line 113: Alans in France/Spain/North Africa — not in research
  - Lines 162, 195: Anacharsis as one of "seven sages" — not in research
  - Lines 168-169: Entire Pseudo-Hippocrates section — not in research
  - Line 97: Queen Amaga — not in research

**Discrepancies found:**
- Line 139: Prose says «понад 160 окремих фігурок» but research says «48 фігур людей і тварин»
- Line 88: Prose says «4–4,5 метрів» but research says «3-4 метри» for kontos length
- Line 139: Prose fabricates Mozolovsky's recollection; research quotes him saying «Я бачив її у снах... І коли вона блиснула під ножем, я зрозумів, що життя прожите не дарма»
- Line 67: Prose paraphrases Gobryas interpretation in direct speech, diverging from research version of Herodotus IV, 132

## Verification Summary

- Content lines read: 228
- Activity items checked: 31 (1 reading passage, 1 essay with rubric, 1 comparative-study, 1 critical-analysis with 3 questions, 10 true-false items, 3 model answers)
- Ukrainian sentences verified: 12
- IPA transcriptions checked: 10 (all plausible; minor note: скіф IPA "scif" at line 20 of vocab — should likely be "skif" with /k/ not /c/)
- Factual claims verified: 14
- Issues found: 6 (3 critical, 3 minor)

## Verdict

**FAIL**

The module is an excellent piece of historical writing with genuine narrative drive, but it fails the Factual Accuracy gate (7/10, auto-fail threshold <8). Three categories of factual issues block passage: (1) fabricated Mozolovsky attribution at line 139, (2) numerical discrepancies with research notes (figure count, spear length), and (3) a paraphrased Herodotus quote presented as direct speech. Additionally, 6 claims have no grounding in the research notes. All issues are fixable in a single repair pass — the underlying content quality is strong.

---

## Audit Failures (from automated re-audit)

```
Gates:   6 pass, 1 info
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/scythians-sarmatians.md
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/activities/scythians-sarmatians.yaml
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** from the file — use Grep to verify before including
- Only fix issues documented in the review or audit failures above
- You MAY add new activities or modify existing ones if the review's Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the review's Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the review's Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged
