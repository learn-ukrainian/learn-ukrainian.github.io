# Dialogue Situations Fixes — A1 + A2 (#1102)

> **Status:** DRAFT — apply after A1 + A2 + B1 rebuilds finish.
> **Source:** Gemini-Pro adversarial reviews on 2026-04-11.
> **Reason for delay:** Plans are inputs to the running build pipeline; editing them mid-build risks race conditions with the writer process. Apply this batch ONLY when all three builds are complete.

## How to apply

1. Wait for all 3 rebuilds to report done.
2. Apply the YAML edits below (Edit tool, one slug at a time).
3. Re-run the affected modules with `--step write --resume` (the writer will pick up the new dialogue_situations on the next pass).
4. Commit with message: `fix(plans): dialogue_situations adversarial fixes (#1102 round 1)`
5. Update #1102 with the resolved-slug list.

## Bottom line

- **A1**: 13 modules need fixing, top 5 below
- **A2**: 12 modules need fixing, top 5 below
- **Cluster diversification** (repetitive settings — 6× planning trips, 5× friends comparing routines, 10× classroom/tutoring) deferred to round 2 — they're real but more subjective and need user discretion.

## Critical finding (A2 schema violation)

`a2/instrumental-adjectives-pronouns.yaml` is listed as a **diary monologue** with one speaker (`Автор щоденника (diary writer, narrating)`). This isn't a dialogue at all — it's a schema violation. Highest priority fix.

---

## A1 — Top 5 Worst Offenders

### 1. `a1/euphony.yaml` — proofreading essay aloud (artificial)

**Problem:** Native speakers don't read essays aloud to test phonotactics. Reads as a grammar drill with characters playing grammarian.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "Listening to a Ukrainian song on the radio together — catching the lyrics. The singer naturally alternates у/в and і/й based on what comes before. One friend sings along, the other catches words. «Він каже 'у школі' тут, але 'в школі' там — чуєш різницю?» Real songs and natural speech motivate the rule, not grammar essays."
    speakers:
      - "Друг 1 (listening)"
      - "Друг 2 (singing along)"
    motivation: "У/в, і/й alternation as heard in real Ukrainian speech: у школі/в школі, і яблука/й яблука, у городі/в городі"
```

### 2. `a1/many-things.yaml` — classroom furniture grammar drill

**Problem:** Setting up a classroom and reciting "один стілець → стільці" reads as a textbook drill. Adults don't enumerate furniture transformations.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "Buying school supplies for a new school year — a parent at the папірня (stationery shop) ordering items for their kids. «Мені потрібен один зошит для сина, але десять зошитів для класу доньки. І п'ять олівців, ні — десять олівців.» Real shopping naturally motivates singular→plural with classroom items."
    speakers:
      - "Батько/Мати"
      - "Продавець (shop assistant)"
    motivation: "Plurals with school items: зошит→зошити, олівець→олівці, ручка→ручки, підручник→підручники, гумка→гумки"
```

### 3. `a1/things-have-gender.yaml` — pet shop pointing at animals

**Problem:** Characters pointing at sleeping animals to narrate "він/вона/воно" is a textbook grammar drill, not natural speech.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "Babusia in the village showing her grandchild a photo album from the 1970s — pointing out family animals from her childhood farm. «Це наш кіт Васько. Він жив 15 років. А це наша корова Зірка. Вона давала молоко вранці і ввечері. А тут — наше теля Орик. Воно було таке маленьке, я носила його на руках.» Generational story-telling naturally motivates він/вона/воно."
    speakers:
      - "Бабуся"
      - "Онука/Онук"
    motivation: "Він/вона/воно with кіт(m), корова(f), теля(n), кінь(m), вівця(f), курча(n)"
```

### 4. `a1/what-will-happen.yaml` — fortune teller motivation mismatch

**Problem:** Ворожки typically predict specific perfective events ("you will meet a stranger"), not iterative imperfective routines. Setting doesn't motivate буду + infinitive.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "Two friends planning a week in the Ukrainian Carpathians (Карпати) — what they'll do every day. Iterative imperfective future fits perfectly: «Що ми будемо робити в Карпатах?» «Будемо ходити в гори. Будемо плавати в озері. Будемо їсти бануш кожен ранок. Будемо співати біля вогнища.» These are repeated/process actions across the week, exactly the analytical imperfective future."
    speakers:
      - "Друг 1"
      - "Друг 2"
    motivation: "Imperfective analytical future (буду + infinitive): ходити, плавати, їсти, співати — iterative actions across a vacation week, not single completed events"
```

### 5. `a1/days-and-months.yaml` — doctor appointment doesn't fit "month"

**Problem:** People don't negotiate the *month* for a routine clinic visit. Day-of-week + appointment context, sure — but not "у якому місяці".

**Replace with:**
```yaml
dialogue_situations:
  - setting: "A family planning a summer trip to a sanatorium in Truskavets — discussing which month and which day of the week to book. «У якому місяці поїдемо? У липні чи у серпні?» «Краще в липні. У серпні діти в школу.» «А який день? У понеділок?» «Ні, у середу — дешевше.» Vacation planning naturally requires both day and month."
    speakers:
      - "Мама"
      - "Тато"
    motivation: "Days and months: У понеділок/середу/п'ятницю; У якому місяці? У липні, у серпні, у вересні. Both granularities motivated by real planning."
```

---

## A2 — Top 5 Worst Offenders

### 1. `a2/instrumental-adjectives-pronouns.yaml` — NOT A DIALOGUE (schema violation)

**Problem:** Single speaker `Автор щоденника (narrating)`. A monologue, not a dialogue. Violates the schema definition.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "Two old friends meeting for coffee after months apart, comparing their lives now. «Я тепер живу з моїм найкращим другом дитинства. А ти?» «А я знімаю квартиру з тією новою колегою з роботи.» «Як вона?» «Цікава жінка — щоранку п'є каву зі своїм собакою на балконі.» Each turn exchanges instrumental phrases naturally."
    speakers:
      - "Подруга 1"
      - "Подруга 2"
    motivation: "Full instrumental phrases in real conversation: з моїм/твоїм/нашим другом, зі своєю старшою сестрою, з тим новим колегою, з нею/з ним"
```

### 2. `a2/aspect-in-vocabulary.yaml` — recipe-reading drill

**Problem:** People don't speak in alternating aspect pairs while cooking. "Ліпи... зліпи... вари... звари..." reads as a grammar drill disguised as a recipe.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "A small business owner asking her assistant for an end-of-day report. The natural contrast between «Що ти сьогодні робила?» (impf — what were you doing all day) and «А що ти зробила?» (pf — what did you actually finish) is a real workplace pattern. «Я писала листи клієнтам. Написала шість, але два ще не закінчила.» «А замовлення?» «Збирала весь день. Зібрала три, четверте на завтра.»"
    speakers:
      - "Власниця бізнесу"
      - "Помічниця"
    motivation: "Aspect contrast in real accountability talk: писати/написати, збирати/зібрати, робити/зробити, закінчувати/закінчити"
```

### 3. `a2/plural-nominative-accusative.yaml` — A1-level zoo pointing

**Problem:** "Дивись — леви!" is A1 vocabulary labeling. By A2 the learner should handle multi-turn conversation with stakes.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "Two volunteers at a Kyiv animal shelter (притулок для тварин) doing the morning intake check. «У нас зараз дванадцять собак, але тільки вісім мисок.» «А коти?» «Коти всі здорові, але є три нових кошенят без імен. Треба знайти господарів для тих кошенят.» Real shelter operations motivate plural counts and accusative-animate."
    speakers:
      - "Волонтер 1"
      - "Волонтер 2 (координатор)"
    motivation: "Nom plural: собака→собаки, кіт→коти, миска→миски. Acc animate plural: знайти господарів для кошенят, годувати собак, лікувати котів"
```

### 4. `a2/shopping-and-health.yaml` — A1 transactional shopping

**Problem:** "Дайте мені кілограм помідорів" is A1-level. By A2 dialogues should have richer turns.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "An adult patient at a сімейний лікар (family doctor) describing what hurts and getting a referral. «Що вас турбує?» «Болить горло вже три дні. І температура — вчора була 38, сьогодні 37.5. Голова теж болить, особливо вранці.» «Кашель є? А нежить?» Multi-symptom medical conversation naturally drives genitive of negation and partitive."
    speakers:
      - "Сімейний лікар"
      - "Пацієнт"
    motivation: "Genitive in medical context: болить горла/голови; немає температури; випишу краплі від кашлю, ліки від нежиті; направлення до отоларинголога"
```

### 5. `a2/genitive-prepositions-source.yaml` — generic ESL potluck trope

**Problem:** "International potluck dinner — everyone brought something from their country" is the most generic ESL textbook setting imaginable. Has no Ukrainian flavor.

**Replace with:**
```yaml
dialogue_situations:
  - setting: "Two women at a Київ IDP (внутрішньо переміщені особи) center sharing dishes from their home oblasts. One brought вареники her mother taught her in Маріуполі; the other brought a recipe з Сєверодонецька. «Це з Маріуполя — моя мама вчила мене це робити.» «А це з Сєверодонецька, від моєї бабусі.» «Я не була там після 2022 року.» Genuinely Ukrainian, emotionally authentic, motivates з/від + cities and people."
    speakers:
      - "Жінка 1 (з Маріуполя)"
      - "Жінка 2 (з Сєверодонецька)"
    motivation: "З/від/після + genitive in displacement context: з Маріуполя, з Сєверодонецька, від мами, від бабусі, після 2022 року"
```

---

## Round 2 (cluster diversification — needs user discretion)

These are real issues from the reviews but more subjective. Will discuss with user before applying.

### A1 repetitive clusters
- **Planning weekend/trip** (6 modules): `i-want-i-can`, `my-plans`, `weather`, `what-time`, `checkpoint-time-nature`, `free-time` — keep 1-2, swap others to: catching a specific Укрзалізниця train, organizing a volunteer shift, coordinating a study session during a power outage.
- **Friends comparing routines** (5 modules): `checkpoint-actions`, `my-morning`, `what-happened`, `verbs-group-one`, `verbs-group-two` — diversify with strict-doctor-vs-patient, IT-night-owl-vs-baker.
- **Walking and pointing at landmarks** (4 modules): `around-the-city`, `checkpoint-places`, `my-city`, `when-and-where` — diversify with directions to ambulance/delivery driver, navigating metro.

### A2 systemic issue
- **10+ modules use teacher/student or study-group settings** — A2 is for ADULTS. Swap 70% of these for professional, community, or adult-learning contexts. Affected slugs: `a2-bridge`, `education-and-work`, `metalanguage-morphology`, `metalanguage-phonetics`, `metalanguage-syntax-cases`, `checkpoint-foundations`, `dative-adjectives-pronouns`, `imperative-complete`, `instrumental-means`, `plural-other-cases`, `synonyms-antonyms-style`, `vocative-expanded`, `which-case-when`.

### A2 cultural genericness
- `indefinite-negative-pronouns` — generic Cluedo trope
- `checkpoint-dative` — generic Secret Santa office trope
- (replace with Ukrainian-specific scenarios)

### A2 aspect coverage gaps
- `aspect-mastery` — current "parent and child doing homework" lacks true aspect contrast depth
- (already covered above for `aspect-in-vocabulary`)

---

## Suggested speaker archetypes (for round 2)

A1 + A2 should diversify beyond "two friends / teacher / shop assistant". Gemini's suggested adult-context archetypes:

- **A1 additions:**
  - Train conductor (провідник/провідниця) and passenger
  - Two pensioners on a bench near a хрущовка
  - Volunteer coordinator and new volunteer
  - Babusia at a стихійний ринок selling vegetables
  - Barista at a third-wave coffee shop and a remote IT worker

- **A2 additions:**
  - Volunteer coordinator and new volunteer at a Волонтерський штаб
  - IT startup colleagues planning a sprint
  - Neighbors at an ОСББ building meeting
  - Grandparent and adult grandchild organizing family archives
  - Local journalist interviewing a small business owner
  - Two strangers carpooling Kyiv→Lviv on BlaBlaCar

---

## Notes for the apply pass

- Each fix is a single `dialogue_situations` field replacement. The rest of the plan YAML (title, content_outline, vocabulary_hints, etc.) is untouched.
- Use the `Edit` tool with the full current `dialogue_situations:` block as `old_string` to ensure unique match.
- After applying all 10, run `.venv/bin/python -c "import yaml; [yaml.safe_load(open(f'curriculum/l2-uk-en/plans/{lvl}/{slug}.yaml').read()) for lvl,slug in [('a1','euphony'),('a1','many-things'),('a1','things-have-gender'),('a1','what-will-happen'),('a1','days-and-months'),('a2','instrumental-adjectives-pronouns'),('a2','aspect-in-vocabulary'),('a2','plural-nominative-accusative'),('a2','shopping-and-health'),('a2','genitive-prepositions-source')]]; print('all parse OK')"` to verify syntax.
- Commit message: `fix(plans): dialogue_situations adversarial fixes — round 1 (#1102)`
- The user re-runs only the affected slugs with `--step write --resume` (don't trigger a full level rebuild).
