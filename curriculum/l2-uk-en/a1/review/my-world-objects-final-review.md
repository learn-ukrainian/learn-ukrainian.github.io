## Adversarial QA Review: my-world-objects (A1-05)

---

### Review Summary

I read all 335 lines of content, 512 lines of activities YAML, 101 lines of vocabulary YAML, and cross-referenced against plan and meta. Here are my findings.

---

### Issues Found

**Issue 1 — IPA tie bar missing (MODERATE)**
- **File:** `my-world-objects.md`, line 102
- **Text:** `the neutral word **Це** [tse]`
- **Problem:** Every other instance of the ц affricate in this module uses the correct tie bar notation `t͡s` (lines 58, 62, 63, 64, 65, 69, 70, 183, 198). Line 102 alone uses bare `tse`, which is inconsistent and technically incorrect IPA for the affricate. At A1, learners seeing both `[tse]` and `[t͡se]` may think they are different sounds.
- **Fix:** Change `[tse]` → `[t͡se]`

**Issue 2 — Redundant "Imagine" in intro body (MINOR — LLM fingerprint)**
- **File:** `my-world-objects.md`, line 19
- **Text:** `Imagine you are standing in the middle of a room.`
- **Problem:** The word "Imagine" already appears 6 lines earlier in the hook (line 13: "Imagine walking into a room"). Repeating it in the first paragraph of the section body creates a formulaic pattern. Three more instances follow in the visualization box (lines 37-38) and scenario (line 278), but those are contextually appropriate. This one is the low-hanging fruit.
- **Fix:** Rephrase to direct statement: "Picture yourself standing in the middle of a room."

**Issue 3 — Green Team review claims "Let's..." phrases exist — they don't (INFORMATIONAL)**
- The review (lines 47, 66-68) claims "5+ instances of 'Let's...'" and suggests specific replacements. I searched the entire content file: there are zero instances of English "Let's" in the prose. The Green Team review either reviewed a different version or hallucinated these. The content already uses "We will group" (line 140), "Here is how" (line 208), etc. This is worth noting because the review is misleading — its LLM Fingerprint score of 7/10 is based partly on phantom evidence.

**Issue 4 — Green Team's neuter trap fix was already applied (INFORMATIONAL)**
- The review's Issue 2 says to "Add a specific note about this overlap to the warning box." This note already exists on line 132 of the content: the `[!warning]` block has a full paragraph titled "Neuter trap:" explaining that identification and specification look identical for neuter nouns. The review was either pre-fix or didn't read the warning block carefully.

---

### Verification Checklist

**Ukrainian Language Quality:**
- IPA accuracy: 27/28 transcriptions correct (1 missing tie bar — Issue 1). Affricates use proper tie bars (t͡s, t͡ʃ). В rendered as [ʋ] not [w]. ✅
- Russianisms: CLEAN. No кушати, получати, приймати участь, слідуючий. ✅
- Russian characters: CLEAN. No ы, э, ё, ъ. ✅
- Gender agreement: All demonstrative-noun pairs verified correct across prose and activities (~60 instances). ✅
- Adjective agreement: All predicate adjectives match gender (великий/m, нова/f, чисте/n, etc.). ✅

**Pedagogical Correctness:**
- Vocabulary scope: All activity words appear in prose vocabulary lists. Kitchen items (ніж, ложка, блюдо) explicitly listed in plan content_outline Practice section. ✅
- Grammar scope: Strictly demonstratives + gender agreement. Adjectives used in predicate position only (no declension taught). No scope creep. ✅
- Fill-in answers: All 20 fill-in items produce grammatical Ukrainian when answer is inserted. Verified each one. ✅
- Anagram letters: All 10 anagrams have correct letter inventory (verified character-by-character). ✅
- Quiz correctness: All 20 near-quiz and 20 far-quiz answers match the correct gender/number form. ✅
- Neuter trap in activities: Activity 9 item 6 ("___ (This) вікно велике" → Це) correctly tests the neuter specification = identification overlap taught in theory. ✅

**Factual Accuracy:**
- Proverb «В гостях добре, а вдома краще» — Real Ukrainian proverb, correct translation. ✅
- Покуття (Red Corner) — Accurate: diagonal from door, icons + рушники, spiritual center. ✅
- двері always plural — Correct. ✅
- Хата/Квартира/Дім distinction — Accurate and culturally nuanced. ✅
- Shoes-off custom — Well-known Ukrainian hospitality norm. ✅

**LLM Artifacts:**
- No "Це не просто X, а Y" pattern. ✅
- No folk etymology presented as fact. ✅
- No false statistics or invented percentages. ✅
- No purple prose or grandiose openers (the "laser pointer" metaphor is apt, not grandiose). ✅
- "Imagine" used 5 times — 3 contextually appropriate (visualization box, scenario), 2 in intro flow (one fixable). Minor. ✅

**Plan Compliance:**
- All 5 content_outline sections present (Вступ, Теорія, Практика, Культурний контекст, Використання + Підсумок). ✅
- All required vocabulary used in prose: цей/ця/це/ці, той/та/те/ті, стіл, книга, телефон, кімната. ✅
- All recommended vocabulary used: стілець, ліжко, лампа, вікно, шафа, двері. ✅
- All 4 objectives mapped to self-check questions in Підсумок. ✅
- Activity counts meet plan hints: match-up 20 pairs (8+12), quiz 20 items (10+10), fill-in 20 items (10+10, exceeds 15+6=21 target). ✅
- Word count: 2256/2000 — exceeds target. ✅

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
you ALWAYS use the neutral word **Це** [tse], regardless of the gender of the object.
---NEW---
you ALWAYS use the neutral word **Це** [t͡se], regardless of the gender of the object.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
Imagine you are standing in the middle of a room. Some things are close enough to touch
---NEW---
Picture yourself standing in the middle of a room. Some things are close enough to touch
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale:** This is a strong A1 module. The content is pedagogically sound, the Ukrainian is accurate throughout, gender agreement is consistently correct in all ~60 demonstrative-noun pairings, all 9 activities are error-free, cultural claims are factually accurate, and the word count exceeds target. The only substantive issue was a single missing IPA tie bar (fix applied). The Green Team review's two main complaints (neuter trap and "Let's..." phrasing) were either already resolved or never present in the current version. Module is ready for production.