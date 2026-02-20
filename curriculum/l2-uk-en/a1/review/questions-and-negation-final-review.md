This confirms the gaps. The Ukrainian State Standard §4.3.1 (A1) explicitly requires "питальне речення зі спеціальними словами де, звідки, куди, що, хто" — both звідки and куди are mandated but missing from the prose. Let me now write the full review.

---

## Phase 9: Final QA Review — questions-and-negation

### Issues Found

**Issue 1 (MAJOR): Frequency adverbs not taught — plan objective unfulfilled**
- **Location:** Entire module
- **Problem:** Plan objective #4 states "Learner understands frequency adverbs (завжди, часто, іноді, ніколи)". The vocabulary YAML includes завжди, ніколи, зазвичай but not часто or іноді. The prose content only uses зазвичай once in a myth-buster sidebar (line 175). The four frequency adverbs from the objective are never introduced, explained, or practiced. No self-check question covers them.
- **Fix:** Add a subsection "Слова частоти" after the "Що vs Шо" section. Add часто and іноді to vocabulary YAML. Add a self-check question.

**Issue 2 (MAJOR): звідки and куди missing from prose — Standard §4.3.1 compliance gap**
- **Location:** Section "Спеціальні питання" (lines 130-147)
- **Problem:** The plan's content_outline lists "де, куди, звідки, коли, чому, як, скільки" as question words. The Ukrainian State Standard §4.3.1 (A1) explicitly requires "питальне речення зі спеціальними словами де, звідки, куди, що, хто". The prose only lists 6 question words (Хто, Що, Де, Коли, Як, Чому), omitting Куди, Звідки, and Скільки from the numbered teaching list. Куди appears in activities but is never introduced in prose. Звідки is absent from the entire module.
- **Fix:** Expand the question word list to 9 items. Add examples for куди, звідки, скільки. Add звідки to vocabulary YAML.

**Issue 3 (MINOR): Punctuation typo**
- **Location:** `questions-and-negation.md` line 40
- **Original:** `It stands like a guard directly *before* the word it negates. usually the verb.`
- **Problem:** Period instead of comma creates a sentence fragment.
- **Fix:** Change to comma.

**Issue 4 (MINOR): "Softening the No" meta point not covered**
- **Location:** Meta outline section 5
- **Problem:** Meta specifies "Softening the 'No': Brief mention that a bare 'Ні' can be blunt, and 'Ні, не...' is softer." This is not explicitly taught anywhere in the content.
- **Fix:** Add a short subsection in the Cultural section.

**Issue 5 (MINOR): Сирник translation imprecise**
- **Location:** `vocabulary/questions-and-negation.yaml` line 73
- **Problem:** Translation says "cheesecake / syrnyk". Standard meaning of сирник is cottage cheese pancake/fritter, not American-style cheesecake.
- **Fix:** Change to "cottage cheese pancake (syrnyk)".

**Issue 6 (MINOR): Activity uses "можемо увійти" — untaught vocabulary**
- **Location:** `activities/questions-and-negation.yaml` line 252
- **Problem:** "Чи ми можемо увійти?" uses "можемо" (can) and "увійти" (enter), neither of which has been introduced by module 7. The exercise tests "Чи" recognition so it still works, but the vocabulary exposure is premature.
- **Assessment:** Not fixing — the exercise functions correctly for its purpose (recognizing чи). Noting for awareness.

---

Now applying fixes:

===FIX_START===
FILE: curriculum/l2-uk-en/a1/questions-and-negation.md
---OLD---
It stands like a guard directly *before* the word it negates. usually the verb.
---NEW---
It stands like a guard directly *before* the word it negates, usually the verb.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/questions-and-negation.md
---OLD---
1.  **Хто?** [xtɔ] — Who? (People / Animates)
2.  **Що?** [ʃt͡ʃɔ] — What? (Things / Actions)
3.  **Де?** [dɛ] — Where? (Location)
4.  **Коли?** [kɔˈlɪ] — When? (Time)
5.  **Як?** [jɑk] — How? (Manner)
6.  **Чому?** [t͡ʃɔˈmu] — Why? (Reason)

**Приклади:**
*   **Хто це?** — Who is this?
*   **Що це?** — What is this?
*   **Де ти?** — Where are you?
*   **Коли ми читаємо?** — When do we read?
*   **Як справи?** — How are things? (How are you?)
*   **Чому ти тут?** — Why are you here?
*   **Як це працює?** — How does this work?
---NEW---
1.  **Хто?** [xtɔ] — Who? (People / Animates)
2.  **Що?** [ʃt͡ʃɔ] — What? (Things / Actions)
3.  **Де?** [dɛ] — Where? (Location)
4.  **Куди?** [kuˈdɪ] — Where to? (Direction)
5.  **Звідки?** [ˈzʋʲidkɪ] — Where from? (Origin)
6.  **Коли?** [kɔˈlɪ] — When? (Time)
7.  **Як?** [jɑk] — How? (Manner)
8.  **Чому?** [t͡ʃɔˈmu] — Why? (Reason)
9.  **Скільки?** [ˈskʲilʲkɪ] — How much/many? (Quantity)

**Приклади:**
*   **Хто це?** — Who is this?
*   **Що це?** — What is this?
*   **Де ти?** — Where are you?
*   **Куди ти йдеш?** — Where are you going?
*   **Звідки ти?** — Where are you from?
*   **Коли ми читаємо?** — When do we read?
*   **Як справи?** — How are things? (How are you?)
*   **Чому ти тут?** — Why are you here?
*   **Скільки це коштує?** — How much does this cost?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/questions-and-negation.md
---OLD---
As a learner, you should always aim to say **що**. It makes you sound educated and respectful of the language. But you must train your ear to understand **шо**. Ви будете чути це скрізь. Не плутайтеся — це просто те саме слово.

> [!myth-buster]
---NEW---
As a learner, you should always aim to say **що**. It makes you sound educated and respectful of the language. But you must train your ear to understand **шо**. Ви будете чути це скрізь. Не плутайтеся — це просто те саме слово.

### Слова частоти: Відповіді на "Коли?"
When someone asks **Коли?**, you often answer with a frequency word. Here are the four most useful ones:

*   **завжди** [zɑu̯ˈʒdɪ] — always
*   **часто** [ˈt͡ʃɑstɔ] — often
*   **іноді** [iˈnɔdʲi] — sometimes
*   **ніколи** [nʲiˈkɔlɪ] — never

**Приклади:**
*   **Коли ти читаєш?** — **Завжди ввечері.** (Always in the evening.)
*   **Ти часто п'єш каву?** — **Так, часто.** (Yes, often.)
*   **Ти іноді читаєш?** — **Так, іноді.** (Yes, sometimes.)

**Важливо знати:**
The word **ніколи** contains a built-in negation. When you use it with a verb, add **не** before the verb too: **Я ніколи не читаю.** (I never read.) This double negation is standard in Ukrainian — it does not cancel itself out.

> [!myth-buster]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/questions-and-negation.md
---OLD---
Using **Чи** with your best friend might sound sarcastic or overly dramatic. Using just intonation with a police officer might sound rude. Adjust your dial!

### Культурний гачок: Легендарний АЛЬФ
---NEW---
Using **Чи** with your best friend might sound sarcastic or overly dramatic. Using just intonation with a police officer might sound rude. Adjust your dial!

### Пом'якшення "Ні"
A bare **Ні** can sound blunt, even rude. In Ukrainian culture, softening your refusal is polite. Compare:

*   **Ні.** — Abrupt, like slamming a door.
*   **Ні, дякую.** — Polite, like closing a door gently.
*   **Ні, я не хочу.** — Explanatory, gives context.

When declining, add a little context. Ваша відмова буде м'якшою і приємнішою.

### Культурний гачок: Легендарний АЛЬФ
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/questions-and-negation.md
---OLD---
5.  **Ви хочете запитати "Ти читаєш?". Чи треба перекладати слово "do"? Чому?**
6.  **Яка різниця між стандартним "що" та розмовним "шо"?**
---NEW---
5.  **Ви хочете запитати "Ти читаєш?". Чи треба перекладати слово "do"? Чому?**
6.  **Яка різниця між стандартним "що" та розмовним "шо"?**
7.  **Назвіть чотири слова частоти (від "завжди" до "ніколи"). Що особливого щодо "ніколи" з дієсловом?**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml
---OLD---
- ipa: '[ˈsɪr.nɪk]'
  lemma: сирник
  pos: noun
  translation: cheesecake / syrnyk
---NEW---
- ipa: '[ˈsɪr.nɪk]'
  lemma: сирник
  pos: noun
  translation: cottage cheese pancake (syrnyk)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml
---OLD---
- ipa: '[dʲi.jɛˈslɔ.ʋɔ]'
  lemma: дієслово
  pos: noun
  translation: verb
---NEW---
- ipa: '[dʲi.jɛˈslɔ.ʋɔ]'
  lemma: дієслово
  pos: noun
  translation: verb
- ipa: '[ˈzʋʲidkɪ]'
  lemma: звідки
  pos: adverb
  translation: where from
- ipa: '[ˈt͡ʃɑstɔ]'
  lemma: часто
  pos: adverb
  translation: often
- ipa: '[iˈnɔdʲi]'
  lemma: іноді
  pos: adverb
  translation: sometimes
===FIX_END===

---

### Review Summary

| Check | Result |
|-------|--------|
| IPA accuracy (tie bars, ʋ not w) | PASS — all affricates use tie bars, в correctly transcribed as ʋ |
| Russianisms | CLEAN — no кушати, получати, приймати участь, слідуючий |
| Russian characters (ы, э, ё, ъ) | CLEAN |
| Gender/case/verb agreement | PASS |
| Vocabulary scope | PASS after fixes (звідки, часто, іноді added) |
| Grammar scope within level | PASS — no forms beyond A1 |
| Activity correctness | PASS — all fill-in answers produce grammatical sentences |
| Factual accuracy | PASS — ALF cultural claim is accurate |
| LLM artifacts | MINOR — some "Notice..." repetition, acceptable |
| Plan compliance (sections) | PASS — all 5 meta sections present |
| Plan compliance (vocab) | PASS after fixes |
| Plan compliance (objectives) | PASS after fixes (frequency adverbs added) |
| Standard §4.3.1 compliance | PASS after fixes (звідки, куди added to prose) |

**Issues fixed:** 7 FIX blocks across 2 files
**Issues noted but not fixed:** 1 (activity "можемо увійти" — functions correctly, minor exposure)
**Remaining issues after fixes:** None blocking

===VERDICT===
APPROVE
===END_VERDICT===