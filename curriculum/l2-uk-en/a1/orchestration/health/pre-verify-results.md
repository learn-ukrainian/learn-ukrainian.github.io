## VESUM Verification

### Batch 1 (голова → око)
- ✅ голова — noun (3 lemma entries)
- ✅ горло — noun (3 lemma entries)
- ✅ живіт — noun (2 lemma entries)
- ✅ рука — noun
- ✅ нога — noun
- ✅ болить — verb (lemma: боліти)
- ✅ лікар — noun
- ✅ аптека — noun
- ✅ спина — noun
- ✅ око — noun (3 lemma entries)

### Batch 2 (вухо → випишу) — also verified plan dialogue words
- ✅ вухо — noun (3 lemma entries)
- ✅ зуб — noun (2 lemma entries)
- ✅ ніс — noun (confirmed noun, not verb ніс < нести)
- ✅ температура — noun
- ✅ кашель — noun (2 lemma entries)
- ✅ нежить — noun — ⚠️ **GENDER ERROR IN PLAN**: VESUM confirms `noun:inanim:m` (MASCULINE), plan labels it feminine (f). Fix: нежить (m).
- ✅ таблетка — noun
- ✅ хворий — adj (5 forms across adj lemma)
- ✅ болять — verb (lemma: боліти) — plural form confirmed
- ✅ застуда — noun
- ✅ ліки — noun (3 entries)
- ✅ краплі — noun (6 entries, lemma: крапля)
- ✅ випишу — verb (lemma: виписати) ✅

**Confirmed**: ALL 18 plan vocabulary words verified ✅
**Not found**: none
**Action required**: Fix нежить gender tag in plan from `f` → `m`

---

## Textbook Excerpts

### Section: Тіло (The Body) — частини тіла
> "Обруч крутять навколо тіла, на **руці**, **нозі**. Обручі носять на **голові**."
> Source: Большакова, Grade 1 (Буквар 2018), p. 8 — body parts appear naturally in Grade 1 context with locative case

### Section: У мене болить... (symptoms + doctor)
> "Голов­ний **біль** – ознака недуги. Отже, при виникненні головного болю треба не займатися самолікуванням, а звертатися за порадою до **лікаря**."
> Source: Заболотний, Grade 10 (2018), p. 177 — confirms "головний біль" (masc.) and "звертатися до лікаря" as natural Ukrainian

### Section: У мене болить... (sickbed scene — температура, болить)
> "Після такої **температури** це навіть забагато зразу. [...] І **голова** крутиться від довгого лежання."
> Source: Авраменко, Grade 6 (Ukrainian Literature, 2023), p. 124 — authentic illness vocabulary in literary context

### Section: Dialogues — At the doctor's (лікар + хворий)
> "В очах пацієнта відчувалася тривога [...] Після кількох запитань й огляду **лікар** зазначив, що, імовірно, **біль** є симптомом загострення."
> Source: Заболотний, Grade 10 (2018), p. 19 — doctor-patient communication text; confirms лікар vocabulary register

---

## Grammar Rules

- **"У мене болить" construction** (dative possessive): Plan correctly notes this is dative (A2+ analysis) and instructs teaching it as a CHUNK at A1. ✅ No Правопис rule needed — chunk approach is pedagogically sound.
- **біль is MASCULINE**: Антоненко-Давидович §ІМЕННИКИ confirms "іменник біль в українській мові – чоловічого роду" (contrast Russian feminine "боль"). Plan's use of "від головного болю" (genitive masculine) is grammatically correct ✅.
- **Правопис query** on dative case returned §15 (Д→ДЖ alternation) — dative case rules are not a Правопис 2019 concern (spelling-only document); grammar is covered by the Ukrainian grammar reference, not Правопис.

---

## Calque Warnings

- **"ліки від [хвороби]"** — ⚠️ **CALQUE** (Russicism). Антоненко-Давидович (§ПРИЙМЕННИКИ) explicitly: *"Це ліки від усяких хвороб" — так сказати по-українську не можна. Треба: "ліки **проти** ревматизму."*
  - Plan dialogue: "Від головного болю? — Так. І від кашлю, будь ласка." and "А є щось від нежиті?"
  - **Correct form**: таблетки **проти** головного болю / краплі **проти** нежиті / щось **проти** кашлю
  - **Action**: Replace all `від [symptom]` in pharmacy dialogue with `проти [symptom]`
  - Note: "головний біль" standalone phrase ✅ is correct; only the preposition + ліки combination triggers the calque rule.

- **"випишу ліки"** — ✅ OK. Виписати ліки / рецепт is natural Ukrainian. No calque issue found.

- **"від головного болю" (standalone genitive phrase without ліки)** — ✅ OK as standalone phrase / label (e.g., section heading or category label without ліки).

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| голова | A1 | ✅ On target |
| лікар | A1 | ✅ On target |
| аптека | A1 | ✅ On target |
| температура | A1 | ✅ On target |
| хворий (adj) | A1 | ✅ On target |
| таблетка | **A2** | ⚠️ One level above A1 — acceptable as situational health vocab, flag in plan |
| кашель | **A2** | ⚠️ One level above A1 — acceptable as situational health vocab |
| нежить | **A2** | ⚠️ One level above A1 — acceptable as situational health vocab |

**Note on A2 words at A1**: таблетка, кашель, нежить are PULS A2 but situationally essential for a health module. Ukrainian textbooks (Grade 1-2) regularly introduce situational vocabulary above the learner's current level when the context demands it. These are appropriate to include — but the plan should note they are "productive A1 situational vocabulary" or taught as chunks.