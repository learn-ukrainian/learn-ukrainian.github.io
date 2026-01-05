# Review-Content Enhancements: AI Detection & Humanity Checks

> **Purpose:** Catch AI-generated "slop" that passes structural checks but lacks human voice, cultural authenticity, or pedagogical warmth.

---

## Section 13: LLM Fingerprint Detection (NEW)

**Goal:** Flag content that exhibits telltale signs of lazy AI generation.

### 13a. Overused AI Phrases (Auto-flag)

**Common LLM Clichés to Flag:**

English:
- ❌ "It's important to note that..."
- ❌ "It's worth noting that..."
- ❌ "As we've seen..."
- ❌ "Let's dive into..."
- ❌ "In today's lesson..." (when module isn't time-bound)
- ❌ "Mastering [X] is crucial for..."
- ❌ "This will help you unlock..."
- ❌ "Think of it as..." (overused analogy starter)
- ❌ "In conclusion..." (textbook ending)
- ❌ "To summarize..." (unless checkpoint/integration)
- ❌ "Additionally, ..." "Furthermore, ..." "Moreover, ..." (stacked transitions without necessity)
- ❌ "Now that we've covered..."

Ukrainian:
- ❌ "Важливо зазначити, що..."
- ❌ "Як ми вже бачили..."
- ❌ "Давайте заглибимось у..."
- ❌ "У сьогоднішньому уроці..."
- ❌ "Оволодіння [X] є важливим для..."

**Check:** If 3+ of these phrases appear in one module, flag as **LLM_CLICHE_OVERUSE**.

**Fix:** Rewrite with natural Ukrainian/English teaching voice.

---

### 13b. False Specificity (The "Generic Disguise" Test)

**Pattern:** AI claims specificity but stays vague.

❌ **Fake Specific (AI-generated):**
```markdown
Уявіть собі ситуацію: ви йдете до магазину і купуєте їжу.
```
- **Issue:** "магазин" (generic store), "їжа" (generic food) - no actual detail.

✅ **Real Specific (Human):**
```markdown
Уявіть: ви на Бесарабському ринку в Києві. Продавець пропонує вам свіжу паляницю — ще теплу! Ви кажете: «Візьму дві».
```
- **Why it works:** Named place (Бесарабський ринок, Київ), specific item (паляниця), sensory detail (ще теплу), dialogue.

**Check:**
- Count named places, people, foods, cultural references
- If module has <3 specific Ukrainian references (place names, traditional foods, cultural practices), flag as **FALSE_SPECIFICITY**

---

### 13c. Certainty Overload (The "AI Overconfidence" Test)

**Pattern:** AI uses absolute statements where humans would hedge.

❌ **Robotic (AI certainty):**
```markdown
Дієслова руху завжди використовуються з префіксами.
Цей вираз ніколи не вживається в розмовній мові.
```

✅ **Human (natural qualification):**
```markdown
Дієслова руху часто використовуються з префіксами.
Цей вираз рідко зустрічається в розмовній мові — українці віддають перевагу простішим формам.
```

**Check:** Count absolutes (завжди, ніколи, всі, жоден, кожен, must, never, always, every).
- If >5 unqualified absolutes in a section, flag as **OVERCONFIDENCE**

**Fix:** Add hedging (часто, зазвичай, generally, typically, often) and reasoning (чому? бо...).

---

### 13d. Anecdotal Absence (The "Teacher Story" Test)

**Goal:** Real teachers tell stories. AI lists facts.

**Check:**
- Does the module include at least ONE:
  - Personal anecdote ("Коли я вперше...") [if teacher voice]
  - Student scenario with stakes ("Уявіть: ви на співбесіді і забули, як сказати...")
  - Cultural story ("В Україні кажуть, що...")
  - Historical context with narrative ("У 1991 році, коли...")

**Pass:** Module has ≥1 narrative moment (story arc: setup → conflict/question → resolution).
**Fail:** Module is 100% expository (just facts, no storytelling).

**Flag as:** **NO_NARRATIVE_VOICE** (B1+ only; A1/A2 exempt due to language limitations).

---

### 13e. Predictability Test (The "Surprise Factor")

**Pattern:** AI is formulaic. Human teaching has unexpected turns.

**Check:** Does the module have ANY of these?
- [ ] Surprising fact that challenges assumptions ("Але тут є сюрприз!")
- [ ] Counterintuitive example ("Здається дивно, але...")
- [ ] Playful contradiction ("Ви думаєте, що X? Насправді...")
- [ ] Unexpected cultural insight ("Українці роблять інакше, ніж ви очікуєте...")
- [ ] Grammar "trick" reveal ("Ось секрет, який спрощує все...")

**Fail:** Module follows 100% predictable path (definition → table → example → practice). Zero surprises.
**Pass:** Module has ≥1 moment where learner thinks "Oh! I didn't expect that!"

**Flag as:** **PREDICTABLE_PEDAGOGY**

---

### 13f. Emotional Flatness (The "Boredom Detector")

**Pattern:** AI rarely expresses emotion. Humans do.

**Check for Emotional Markers:**
- Exclamations: ! (excitement, surprise)
- Rhetorical questions: ? (engagement, challenge)
- Emphatic words: дуже, really, especially, particularly
- Evaluative language: beautiful, clever, tricky, surprising
- Direct address: ти/ви (you), давайте (let's)

**Density Check:**
- Count emotional markers per 100 words
- **Fail:** <1 per 100 words (flat, robotic)
- **Pass:** 2-4 per 100 words (conversational)
- **Overboard:** >6 per 100 words (too gimmicky)

**Flag as:** **EMOTIONAL_FLATNESS** (if fail threshold).

---

### 13g. Teacher Voice Consistency (NEW)

**Goal:** Ensure a consistent pedagogical persona throughout.

**Check:**
- Does the voice shift between formal/informal without reason?
- Does the teacher persona stay consistent (encouraging vs. strict vs. playful)?
- Are pronouns consistent (ви/formal vs. ти/informal)?

❌ **Inconsistent:**
```markdown
Paragraph 1: "Давайте розглянемо..." (we together - inclusive)
Paragraph 3: "Вам потрібно запам'ятати..." (you - distant)
```

✅ **Consistent:**
```markdown
All paragraphs: "Ми розглянемо..." "Ми запам'ятаємо..." (consistent "we" voice)
```

**Check:** Flag if pronouns/tone shift >2 times without pedagogical reason.

**Flag as:** **INCONSISTENT_VOICE**

---

### 13h. Depth of Explanation (The "Why Depth" Test)

**Pattern:** AI stops at surface. Humans dig into "why."

**Example:**

❌ **Shallow (AI):**
```markdown
Perfective aspect shows completed action. Use it for results.
```

✅ **Deep (Human):**
```markdown
Why do Ukrainians care so much about aspect?

Because the verb form tells you whether to mentally "close the file" or not.

"Я писав лист" → File still open. Maybe I'm still writing, maybe I stopped but didn't finish.
"Я написав лист" → File closed. The letter exists now. Result achieved.

English doesn't force this choice. Ukrainian does. Every. Single. Time.
```

**Check:** For each grammar concept, verify:
- [ ] **What:** Definition provided
- [ ] **How:** Usage examples provided
- [ ] **Why it matters:** Cultural/linguistic reason explained
- [ ] **Common mistake:** What learners get wrong and why

**Fail:** Module teaches "what" and "how" but never "why."

**Flag as:** **MISSING_WHY_LAYER**

---

### 13i. Cultural Resonance (The "Soul" Test)

**Goal:** Ensure Ukrainian culture is woven in, not sprinkled on.

**Superficial Integration (AI):**
```markdown
🎬 Pop Culture Moment: Ukrainians like borshch!
```
- **Issue:** Random fact without connection to grammar/vocab.

**Deep Integration (Human):**
```markdown
Українці кажуть: "Не той борщ, що в горщик, а той, що в роті" (It's not the soup in the pot that counts, but the one in your mouth).

Зверніть увагу: **в горщик** (Accusative), **в роті** (Locative).

Чому різні відмінки? Бо один — куди кладуть (напрямок), інший — де знаходиться (місце).

Ця різниця — суть української граматики.
```

**Check:**
- [ ] Cultural content connects to grammar lesson (not random)
- [ ] Proverbs/idioms demonstrate grammatical structure
- [ ] Examples use Ukrainian reality (not translated Western scenarios)

**Fail:** Culture is decorative (random facts in boxes). Grammar is separate.
**Pass:** Culture IS the vehicle for teaching grammar.

**Flag as:** **DECORATIVE_CULTURE** (if fail).

---

## Section 14: Human Warmth Checklist (NEW)

**These elements make learners feel a human teacher is present:**

### 14a. Direct Address
- [ ] Uses "you" (ти/ви) to speak directly to learner
- [ ] Uses "we" (ми) to create partnership ("Let's explore...")
- [ ] Acknowledges learner struggles ("This is tricky, I know")

### 14b. Encouragement
- [ ] At least 1 encouraging phrase per module:
  - "You've got this!"
  - "Не хвилюйтеся, це зрозуміє кожен"
  - "With practice, this becomes natural"

### 14c. Anticipates Confusion
- [ ] Addresses common mistakes BEFORE learner makes them
- [ ] "You might think X, but actually..."
- [ ] "Students often confuse X and Y. Here's how to remember..."

### 14d. Real-World Validation
- [ ] Shows learner why THIS lesson matters NOW
- [ ] "After this module, you'll be able to..."
- [ ] "This unlocks [real-world skill]"

**Fail:** Module has <2 of these warmth markers.
**Pass:** Module has ≥3 warmth markers.

**Flag as:** **COLD_PEDAGOGY**

---

## Section 15: Richness Red Flags (AUTO-FAIL)

**These are fatal flaws that indicate AI slop:**

### 15a. The "ChatGPT Default Voice"

**Pattern Recognition:**
```markdown
Welcome to Module X! In this lesson, we'll explore...
First, let's understand... Then, we'll dive deeper into...
By the end of this module, you'll be able to...
```

**Why it's bad:** This is GPT's default scaffolding template. Zero personality.

**Auto-fail if:** Module opens with this exact structure.

### 15b. The "Bullet Point Barrage"

**Pattern:**
```markdown
Here are 5 key points:
- Point 1
- Point 2
- Point 3
- Point 4
- Point 5

Now let's look at 3 examples:
- Example 1
- Example 2
- Example 3
```

**Why it's bad:** No narrative flow. Just a list generator.

**Auto-fail if:** >50% of module is bullet lists without prose paragraphs.

### 15c. The "Wikipedia Copy-Paste" Syndrome

**Pattern:**
```markdown
The Dative case (Ukrainian: давальний відмінок) is a grammatical case
used in the Ukrainian language to indicate the indirect object of a verb.
```

**Why it's bad:** Encyclopedic tone. No teaching warmth. Passive voice overload.

**Auto-fail if:** Module uses encyclopedic definitions without rewriting for learner voice.

### 15d. The "Engagement Box Faker"

**Pattern:**
```markdown
💡 Did You Know?
Ukrainian has 7 cases!

💡 Pro Tip:
Remember to use the Dative case with these verbs.

💡 Cultural Note:
Ukrainians value hospitality.
```

**Why it's bad:** Boxes contain obvious/useless info. Padding, not value.

**Auto-fail if:** >50% of engagement boxes just restate what body text already said.

---

## Section 16: Fix Strategies for AI-Generated Content

**When you detect AI slop, apply these fixes:**

### Strategy 1: Add Sensory Detail
❌ **Generic:** "Людина готує їжу"
✅ **Vivid:** "Запах борщу наповнює кухню — бурячки, часник, кріп"

### Strategy 2: Name Everything
❌ **Vague:** "Я купив хліб у магазині"
✅ **Specific:** "Я купив паляницю в булочній 'Хлібний дім' на вулиці Хрещатик"

### Strategy 3: Add "Why" Layer
❌ **Shallow:** "Use perfective for results"
✅ **Deep:** "Чому важливо? Бо українець почує 'я робив' і запитає: 'І що? Зробив чи ні?' Недоконаний вид залишає питання відкритим."

### Strategy 4: Replace Certainty with Reality
❌ **Absolute:** "Це завжди неправильно"
✅ **Nuanced:** "Більшість українців скаже інакше. Хоч технічно обидва варіанти існують, один звучить природніше."

### Strategy 5: Inject Story
❌ **Factual:** "Genitive shows possession"
✅ **Narrative:** "Марія йде до мами. Чому 'мами', а не 'мама'? Бо це — мамин дім, мамина вулиця, мамине місто. Родовий відмінок створює зв'язок: не просто 'йти до', а 'йти до когось свого'."

---

## Implementation Checklist

**For each module review, add these steps:**

**Step 13: Run LLM Fingerprint Detection**
- [ ] Check for overused AI phrases (13a)
- [ ] Verify real specificity vs. fake (13b)
- [ ] Count certainty markers (13c)
- [ ] Look for narrative moments (13d)
- [ ] Check for surprises (13e)
- [ ] Measure emotional density (13f)
- [ ] Verify voice consistency (13g)
- [ ] Check "why" depth (13h)
- [ ] Assess cultural integration (13i)

**Step 14: Human Warmth Audit**
- [ ] Direct address present? (14a)
- [ ] Encouragement included? (14b)
- [ ] Confusion anticipated? (14c)
- [ ] Real-world validation? (14d)

**Step 15: Richness Red Flags**
- [ ] No ChatGPT default voice? (15a)
- [ ] No bullet barrage? (15b)
- [ ] No Wikipedia tone? (15c)
- [ ] Engagement boxes add value? (15d)

**Scoring:**
- **5/5:** All checks pass. Content feels authentically human.
- **4/5:** 1-2 minor flags. Mostly human, slight AI traces.
- **3/5:** 3-4 flags. Noticeably AI-generated but salvageable.
- **2/5:** 5+ flags. Heavy AI fingerprint. Needs rewrite.
- **1/5:** Auto-fail red flags present. Pure AI slop. Complete rewrite.

---

## Comparison: Before vs After Enhancements

### Example: Module Score Changes

**Module B1-08 (Aspect - Past Result/Process)**

**Before Enhancement (Old Review):**
- Coherence: 4/5
- Relevance: 5/5
- Educational: 4/5
- Language: 5/5
- Pedagogy: 4/5
- Immersion: 5/5
- Activities: 5/5
- Richness: 3/5
- **Overall: 4.4/5** → ✅ PASS

**Issues Noted:** "Minor repetition in examples"

**After Enhancement (New Review with AI Detection):**
- All previous scores: same
- **LLM Fingerprints Detected:**
  - ❌ Overused phrases: "Як ми вже бачили..." (appears 3x)
  - ❌ False specificity: Generic "людина йде до магазину" (no named places)
  - ❌ Predictable pedagogy: No surprise moments
  - ❌ Emotional flatness: 0.8 markers per 100 words (below threshold)
  - ⚠️ Missing "why" layer: Surface explanation only
- **Human Warmth:** 1/4 (missing encouragement, confusion anticipation)
- **Richness Red Flag:** Engagement boxes restate body text

**New Score: 3/5** → ⚠️ NEEDS ENRICHMENT

**Why this matters:** Old review missed that content WORKS but lacks SOUL. New review catches this.

---

## Summary

**What These Enhancements Detect:**

1. **LLM Clichés** → "It's important to note that..." spam
2. **Fake Specificity** → Claims "specific" but stays generic
3. **AI Overconfidence** → "Always" / "Never" without hedging
4. **Missing Stories** → All facts, no narrative
5. **Predictability** → Zero surprises or unexpected turns
6. **Emotional Flatness** → No exclamations, questions, or warmth
7. **Voice Inconsistency** → Persona shifts randomly
8. **Shallow Explanation** → "What" and "How" but no "Why"
9. **Decorative Culture** → Random Ukrainian facts, not integrated
10. **Cold Pedagogy** → No teacher warmth, encouragement, or empathy

**Bottom Line:**
Your modules now pass structural/grammatical audits. These enhancements ensure they also pass the **HUMAN TEST** — content that feels like a skilled teacher wrote it, not an algorithm.
