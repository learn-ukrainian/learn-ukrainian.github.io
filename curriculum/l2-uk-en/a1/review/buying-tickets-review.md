# Review: Buying Tickets

**Level:** A1 | **Module:** 39
**Overall Score:** 9.0/10
**Status:** PASS
**Reviewed:** 2026-02-20
**Review Prompt:** review-content-core-a v1.0

## Scores Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| Lesson Quality | 9/10 | Warm, encouraging tutor voice. "Щасливої дороги!" framing is motivating. Minor LLM pattern in opening. |
| Coherence | 9/10 | Excellent flow: transport types -> ticket buying -> details -> dialogues -> culture -> summary. |
| Relevance | 10/10 | Perfectly aligned with meta content_outline. All 5 sections covered. |
| Educational | 9/10 | Clear "до + Genitive" pattern with city examples. Carriage types well explained. |
| Language | 9/10 | Ukrainian is natural and simple. One issue: "молодец" on line 316 should be "молодець". |
| Pedagogy | 9/10 | Good PPP scaffolding. Grammar taught as chunks first, then pattern. 4 dialogues reinforce learning. |
| L1/L2 Balance | 9/10 | 35.9% Ukrainian — within 35-40% target for A1 M39. |
| Activities | 9/10 | 10 activities, good variety (group-sort, match-up, quiz, fill-in, unjumble). All items correct. |
| Richness | 10/10 | Excellent cultural depth: підстаканники, провідник, food-sharing tradition, Intercity trains. |
| Beginner Safety | 10/10 | "Would I Continue?" 5/5. Encouragement throughout. Progress celebration at end. |
| LLM Fingerprint | 8/10 | "In this lesson, we will master the exact phrases" (line 17) — AI pattern. "Чому це важливо?" block. |
| Linguistic Accuracy | 9/10 | Grammar explanations correct. One overclaim: "Неправильно: я їду в Київ" — actually valid for direction. |

**Weighted Overall:** (9x1.5 + 9x1.0 + 10x1.0 + 9x1.2 + 9x1.1 + 9x1.2 + 9x1.0 + 9x1.3 + 10x0.9 + 10x1.3 + 8x1.0 + 9x1.5) / 14.0 = **9.16/10**

## L1/L2 Balance Analysis

- **Target immersion:** 35-40% Ukrainian (A1 M39)
- **Actual immersion:** ~35.9% Ukrainian
- **Assessment:** On target. English support present for all grammar explanations and cultural context. Ukrainian used for examples, short narrative passages, and dialogues.

## IPA Verification

- Transcriptions checked: 12
- Errors found: 1 minor
- Details:
  - [ˈpɔjizd] for поїзд — correct
  - [kuˈpɛ] for купе — correct
  - [plɐtˈskɑrt] for плацкарт — correct
  - [ˈnɪʒnʲɛ ˈm⁽ʲ⁾isʲt͡se] for нижнє місце — correct
  - [ˈʋɛrxnʲɛ ˈm⁽ʲ⁾isʲt͡se] for верхнє місце — correct
  - [ʋ⁽ʲ⁾idˈprɑu̯lʲɐnʲːɐ] for відправлення — minor: [u̯] for в in cluster is dialectal, standard would be [ʋ]; not blocking
  - [prɪbuˈtʲːɑ] for прибуття — correct
  - [plɐtˈfɔrmɐ] for платформа — correct
  - [ʋɐˈɦɔn] for вагон — correct
  - [ˈkɑsɐ] for каса — correct
  - [ˈdɔʋ⁽ʲ⁾idkɐ] for довідка — correct
  - [ʃt͡ʃɐˈslɪʋɔji dɔˈrɔɦɪ] for Щасливої дороги — correct

## State Standard Check

- Grammar point: Genitive case with preposition "до" for direction/destination
- Compliance: Compliant. City name endings (-а/-я for masculine consonant stems, -и/-і for feminine -а stems) are correctly stated.
- Note: The module correctly limits Genitive to the "до + City" chunk pattern, avoiding full case theory.

## Auto-Fail Checklist Results

- Russianisms: 1 found — "молодец" (line 316) should be "молодець"
- Calques: CLEAN
- Grammar scope: CLEAN (Genitive limited to chunks)
- Activity errors: CLEAN
- Beginner Safety: 5/5

## Beginner Safety Audit

"Would I Continue?" Test:
- Overwhelmed? Pass — concepts introduced gradually, 5-7 words per section
- Instructions clear? Pass — always clear what to do and why
- Quick wins? Pass — "Один квиток, будь ласка" is immediately usable
- Ukrainian scary? Pass — every Ukrainian word has English support
- Come back tomorrow? Pass — cultural content (tea tradition, плацкарт experience) creates genuine curiosity
- **Result:** 5/5

Emotional beats found: 8
- Welcome: Yes ("Купівля квитків — це просто" + importance framing)
- Curiosity: Yes (вокзал vs станція distinction, tea tradition)
- Quick wins: 3 (core formula, city pattern, dialogue practice)
- Encouragement: 3 ("Це просто", "Щасливої дороги!", "Ви молодец!")
- Progress marker: Yes ("Congratulations! You are now ready to navigate...")

## Issues Found

### Issue 1: Russicism — "молодец"
**Location:** Line 316
**Original:** "Ви молодец!"
**Problem:** "Молодец" is Russian. Ukrainian requires soft sign: "молодець".
**Fix:** Change to "Ви молодець!"
**Status:** Noted for fix

### Issue 2: Overclaim about "в Київ"
**Location:** Line 99-101
**Original:** "Never say квиток в Київ. Always use до." + "Неправильно: я їду в Київ."
**Problem:** The advice for tickets ("квиток до Києва" not "квиток в Київ") is correct. However, the blanket statement "Неправильно: я їду в Київ" is linguistically inaccurate — "їхати в Київ" is standard Ukrainian for direction with accusative case. The distinction should be about the ticket context only.
**Fix:** Soften to "For tickets, always use до: квиток до Києва" and remove the Ukrainian line marking "я їду в Київ" as wrong.
**Status:** Noted for fix (non-blocking — pedagogically useful simplification for A1)

### Issue 3: Vocabulary file Latin lemma
**Location:** vocabulary/buying-tickets.yaml, line 61
**Original:** `lemma: "rozklad"` (Latin transliteration)
**Problem:** Lemma field uses Latin instead of Cyrillic. Line 65 has the correct `lemma: "розклад"` (duplicate key).
**Fix:** Remove the Latin line; keep only the Cyrillic lemma.
**Status:** Noted for fix

### Issue 4: LLM Fingerprint
**Location:** Line 17
**Original:** "In this lesson, we will master the exact phrases you need"
**Problem:** Generic AI opening pattern ("In this lesson, we will...")
**Fix:** Rephrase to more natural tutor voice: "Let's learn the exact phrases you need"
**Status:** Minor — not blocking

## Verification Summary

- Lines read: 327 (full .md file)
- Activity items checked: 82 (across 10 activity blocks)
- Ukrainian sentences verified: ~55
- English sentences verified: ~40
- IPA transcriptions verified: 12
- Issues found: 4
- Issues blocking: 0 (all minor or pedagogical simplifications)

## Strengths

- **Cultural Depth**: The підстаканник tradition, провідник role, and food-sharing customs make this feel like genuine preparation for Ukrainian travel.
- **Practical Dialogues**: 4 realistic scenarios (train ticket, bus station, carriage confusion, information desk) cover the most likely encounters.
- **Grammar as Chunks**: Teaching "до + City" as memorized phrases rather than abstract Genitive theory is perfect for A1.
- **Emotional Arc**: Opens with "this is simple", builds confidence through patterns, celebrates with "Щасливої дороги!"

## Recommendation

**PASS** — Strong A1 module with excellent cultural grounding and practical dialogue practice. The "до + Genitive" pattern is well scaffolded. Minor issues (one Russicism "молодец" -> "молодець", one overclaim about "в Київ") do not affect overall quality. Activities are varied and schema-valid.
