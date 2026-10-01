# Listening source selections for A1 positions 1–3

Refs #8425. Curated against the fresh `lesson-plans/a1/` plans, with those plans unchanged. This is a source-selection handoff, not lesson-build approval. Record IDs below are local to their module pack. No synthetic speech or new premium-note quotations are introduced.

Integration update: [current declarations and U-004 conversions](integrate-a1-p1-p3-listening.md) supersede the original open-gap disposition below. The tables below preserve the discovery evidence and its limitations.

The search read every tracked JSON/YAML and raw list under `docs/resources/podcasts/`, including all 300 podcast entries and all three complete raw lists; the six accompanying Markdown documents; all 672 modules in `external_resources.yaml`; and the complete `ulp-resources.yaml`, `ulp-articles-index.yaml`, `ulp-article-mappings.yaml` and `trusted_sources.yaml`. The additional public-corpus read covered all 480 ULP YouTube/blog rows. MCP searches included `search_external` for greetings, formal greetings, alphabet, soft consonants and the exact hard/soft/digraph words, plus `search_text` for the primer's complete T-018 list. No other channel was selected: `trusted_sources.yaml` lists no additional video channel.

Public ASR transcripts are recording-discovery evidence, not Ukrainian spelling, stress or grammatical authority. A broken ASR boundary resembling the first member of the hard/soft pair was rejected; a band-name occurrence of the second member did not establish the primer pair. Unrelated startup-name, electronics and poetry occurrences did not establish the required intended-sense word sets or complete sentences. VESUM and the evidence builder determine the word entries and forms.

Free checks use two distinct evidence classes, observed on 2026-10-01:

- **P**: canonical ULP `/episodeN/` page HTTP 200, with an unauthenticated public Buzzsprout player script distinct from the premium-note offer. Episodes 1, 2, 5, 10 and 15 were fetched. The catalogue `/lesson/N/` aliases failed with 404/403 here, so records use the canonical publisher pages.
- **Y**: the publisher's public [alphabet guide](https://www.ukrainianlessons.com/ukrainian-alphabet/) labels and embeds the exact video under its letter heading; the YouTube watch page is HTTP 200. Initial fetched watch pages reported `LOGIN_REQUIRED` for an anti-bot check; later reading-pack requests were rate-limited with HTTP 429. This confirms public links/embeds, **not successful audio playback**. The player scripts also returned HTTP 403 from this execution environment. Direct listening, exact timestamps and independent audio confirmation remain unverified for P and Y.

The existing premium T/X records remain grounding only. The reading recap plan's instruction to display T-016/T-017 cannot authorize publishing those notes as source text. Its public episode is the listening source; the driver must resolve learner-facing text rights before building.

## Requirement table

Every sublesson is included. The final recording table resolves each V ID to its URL and free-check class. A source for one phoneme is never treated as a recording of a whole primer word, contrast, syllable or sentence. Printed/read-aloud work does not itself need a new recording; a by-ear choice does.

| Position / lesson | Requirement and words or sounds to hear | Pack records → recording | Evidence and remaining gap |
| --- | --- | --- | --- |
| 1 / 1 | s1/s2 and a1–a5: informal W-074; formal intact W-075+W-076 | V-001 → episode 1; V-002 → episode 2 | P. Public transcripts `ext-ulp_youtube-303` and `302` contain peer greeting/repetition and the formal greeting/repetition plus shop scenario. Whole chunks, never parsed. |
| 1 / 2 | s1/s2, a1/a2/a3/a5/a6: sound versus visible symbol; А О У И | V-004–V-007 | Y. Exact publisher-labelled letter models; replay for vowel/symbol choices. |
| 1 / 3 | s1/s2/s3, a1/a3 and every video entry: М І Н; distinct И/І; primer CV/VC rows | V-003, V-007–V-010 | P for И trainer, Y for letters. Named sound models are supported. Exact primer syllable recordings remain open as U-001. |
| 1 / 4 | s1/s2, a1/a5 and every video entry: В Л С; soft-before-І model | V-011–V-013 | Y. The letter models do not establish every exact primer soft-before-І contrast; U-001. |
| 1 / 5 | s1/s2, a3/a4 and every video entry: К П Р; new CV/VC/CVC combinations; W-084/W-085 contrast | V-014–V-016 | Y. Letter sounds supported; complete syllables and the hand/river pair remain unconfirmed, U-001. |
| 1 / 6 | s1: review of the heard greetings, then a writer-authored printed story and questions | V-001/V-002 for greeting recall | P for greetings. No source recording is claimed for the unwritten custom story; this plan presents it in print. |
| 2 / 1 | s1 formal opening; s1/s2 and a2/a4/a5: Т Е; s3/a8: whole W-074/W-081/W-082/W-101/W-117; s3 also W-102 | V-014 for greeting; V-001/V-005 for Т/Е; V-004 also contains W-081/W-101 | P/Y. Complete greeting and letter models supported. No confirmed complete set containing W-082, W-117 and W-102; U-002. |
| 2 / 2 | s1–s3 and a2/a4/a6/a9: Д З Б; s3/a5 read the complete T-018 list | V-006–V-008; T-018/EX-003 binds six word records | Y for sounds. The read list is now bound to W-118, W-145–W-148 and existing W-035. Four new words are still outside the lesson allowlist, U-004. The activity is reading after a sound model, not evidence of a recording of the entire list. |
| 2 / 3 | s1 formal opening; s1/s2 and a2/a4/a5: Г Ґ and exact primer syllables; s2 compares all X-002 pairs; s3/a7: W-106/W-107/W-081/W-101/W-104 | V-014; V-009/V-002; X-002/EX-004 binds all six comparison words | P/Y. Individual Г/Ґ supported. Exact primer syllables and complete word choices unconfirmed, U-002. Five X-002 word records remain outside the lesson allowlist, U-004. |
| 2 / 4 | s1–s3, a2/a4/a6/a7/a10: Ч Й Х and W-101/W-103/W-108/W-109/W-110 | V-010/V-003/V-011; V-015 for W-109/W-110 | Y. Named sounds supported; public full-alphabet transcript `ext-ulp_youtube-304` includes tea/bread. This does not confirm all other word choices, U-002. |
| 2 / 5 | s1/s2, a2/a4/a9: Ж Ш plus mixed Ч/Х; s3/a7: EX-001/EX-002 whole sentences and their words | V-012/V-013 plus V-010/V-011; T-015/EX-001/EX-002 are print | Y for letters. No confirmed recording of either complete primer sentence; U-003. |
| 2 / 6 | s1 formal opening; s1/a1/a2: episode-10 source story, first three questions and spoken answers | V-014; V-004 | P. Public transcript `ext-ulp_youtube-294` contains the first-person review and those questions/answers. No premium notes are licensed for learner-facing quotation. |
| 3 / 1 | s1/a1/a3/a5: exact W-119/W-120 hard/soft pair; soft sign; W-076/W-081/W-101 word choices; greeting before reading | V-001; V-006 for greeting; V-007 for general hard/soft support and W-076 | Y/P. Neither V-001 nor V-007 records the complete primer pair. U-003 remains open; generic softness cannot substitute. W-081/W-101 are modeled in episode 10 but that episode is not a word-choice recording bound in this pack. |
| 3 / 2 | s1/s2/a2/a4/a6: Ї/Я; W-121/W-122/W-123/W-141, plus post-vowel W-010 and post-sign W-142 | V-002; V-006 for greeting recall | Y/P. Named sounds supported. Exact full food/pit/baby/name and positional word contrasts unconfirmed, U-004. |
| 3 / 3 | s1/s2/a2/a4/a5/a6: Ю/Є; W-124/W-125/W-126/W-127/W-140 and post-vowel W-010 | V-003/V-002; V-006 for greeting recall | Y/P. Named sounds supported. Exact yurt/lupin, present first-person W-140, source neuter W-126, plural W-127 and W-010 models unconfirmed, U-004. |
| 3 / 4 | s1–s3/a2/a4/a6/a9: Ц, hard/soft Ц, Щ versus Ш, Ф; W-128/W-129/W-130/W-131 | V-004/V-002/V-005; V-006 for greeting recall | Y/P. Named Ц/Щ/Ф supported. The complete instrument/pike/rain/farm word-choice set and exact hard/soft Ц primer values are not established; U-004. |
| 3 / 5 | s1/s2/a1/a2/a3/a4/a6: joined дж/дз; W-132/W-133/W-134 and source present W-135; hard/soft дз | V-002 only recalls individual letters | Y for letter recall. No confirmed complete bumblebee/jam/spinning-top/source-verb recording or hard/soft дз contrast, U-005. The video is explicitly not a digraph-rule source. |
| 3 / 6 | s1/a2/a6: W-143 versus first-person W-137; W-136/W-139/W-144; source Ю/Є forms of W-137; EX-001 intact sentence | V-002 only recalls vowels; T-015/T-011/T-026/EX-001 are print | Y for vowel recall. Exact apostrophe/no-apostrophe contrast, required word forms and complete sentence remain unconfirmed, U-006. |
| 3 / 7 | s1/a2: all 33 T-012 letter names and glyphs, distinguished from sounds | V-002 for alphabet sounds; T-012 for names in print | Y for sounds. No confirmed complete letter-name recording, U-007. |
| 3 / 8 | s1/a2: custom story and substantive heard **or printed** options; recall pair and sentence aloud | Printed story/options are permitted; existing sound/greeting records support recall | No recording is asserted for an unwritten custom story. A heard-option implementation would still need a suitable recording; the permitted printed implementation avoids that dependency. |

## Whole-word bindings

`EX-003` copies the complete T-018 word row without shortening it. `EX-004` copies the complete X-002 Г/Ґ row. They bind the source words to store records without adding them to a plan's inventory.

| Source requirement | Word → record | VESUM entry | Exact required form eligible |
| --- | --- | --- | --- |
| T-018 | зуб → W-118 | 150592 | Existing record |
| T-018 | бак → W-145 | 16017 | yes, nominal form |
| T-018 | біб → W-146 | 23245 | yes, nominal form |
| T-018 | лід → W-147 | 187686 | yes, nominal form |
| T-018 | бук → W-148 | 31628 | yes, nominal form |
| T-018 | над → W-035 | 212130 | Existing base preposition |
| X-002 | грати → W-149 | 83141 | yes, infinitive |
| X-002 | ґрати → W-150 | 86858 | yes, plural-only nominal form |
| X-002 | кава → W-151 | 157965 | yes, nominal form |
| X-002 | грім → W-152 | 84094 | yes, nominal form |
| X-002 | ґава → W-107 | 86426 | Existing record |
| X-002 | ґрунт → W-153 | 86930 | yes, nominal form |

MCP `verify_words` found all six T-018 surface forms and all five new X-002 surface forms. Every new required lemma form has `learner: true` in the generated store. CEFR lookups do not make these core vocabulary: thunder is A2 and soil B2; the row is incidental decoding. Tank/bean CEFR calls failed, and the beech lookup returned other headwords; their CEFR level is unverified. All nine shadow probes returned no match, a supplemental check rather than a normative verdict.

The original reading request still used `want: new` for two already allocated words. They now name W-117/W-118 explicitly, and all nine newly allocated requests name W-145–W-153 so rebuilding does not allocate duplicates. A full builder refresh preserved existing IDs/entries and repaired eleven stale ULIF citations. The full store still contains pending forms; those forms are withheld and are not proof of lesson admission.

## Driver disposition

There are nine open unsupported groups: position 1 U-001; position 2 U-002/U-003/U-004; position 3 U-003/U-004/U-005/U-006/U-007. **The requested all-requirements outcome is not achieved.** Owner: the #8425 accountable driver. Next packet must either curate exact permitted recordings or obtain an approved plan revision for the unavailable listening tasks, and must admit the nine new incidental records into the two reading lessons. This worker has no authority to edit those plans, commission recordings or dispatch another worker. No PR, merge or source playback certification is implied.

All three packs and locks were produced with `build-pack`; the store and registry with `build-words`. Strict `pack-verify` fails on the open unsupported groups (1 / 3 / 5 respectively); the latest online reading-pack verification also received HTTP 429 for its 13 YouTube records after the initial HTTP 200 checks. This is an additional network verification limit, not evidence that the recordings are paid or missing; do not use a non-strict success as semantic acceptance. Strict `words-verify` succeeds with no cited-row drift. Targeted tests: `tests/curriculum/evidence/test_pack.py`, `test_words.py`, `test_verify.py`, `test_schemas.py`: 124 passed. Ruff on the evidence builder/verifier modules passed. The tests prove tooling behavior, not audio coverage. Independent cross-family review and held-out audio validation belong to the driver and have not occurred on this branch.

Changing these packs/locks and the shared word store/lock makes the following seven plan-review manifests stale (paths below are relative to `evidence/a1/_state/`). Older manifests also mismatch other pre-existing plan/arc inputs; no old approval is renewed:

- `sounds-letters-and-hello/plan-review.manifest.yaml`
- `sounds-letters-and-hello/manifests/plan/8591d48151704f4cf6443b52df56e47b4cc295f0975cd69ec69fedf83c3ccce8.yaml`
- `reading-ukrainian/plan-review.manifest.yaml`
- `reading-ukrainian/manifests/plan/217c19ca26cde45cf340e624d8b422df5b92d029d29ffbc706e6f5f9a2da94d9.yaml`
- `reading-ukrainian/manifests/plan/360b2f2eb4728efb7df6b287cd3028065685031a138860800af6e62fd745bd4c.yaml`
- `special-signs/plan-review.manifest.yaml`
- `special-signs/manifests/plan/db619776b2c86847e583410a68780f4ed57c20810013a29a9cb9ecd25c9a9e78.yaml`

## Recording URLs and free checks

The following table is the recording index for the requirement table, including every plan `videos:` entry and the added records. Each letter video's exact URL is also embedded under that letter heading in the public alphabet guide; a public transcript alone is not used to validate its Ukrainian example-word spelling.

| Module | Record | URL | Free check | Model evidence |
| --- | --- | --- | --- | --- |
| sounds-letters-and-hello | V-001 | [recording](https://www.ukrainianlessons.com/episode1/) | P | ULP 1-01 public episode: whole informal W-074 greeting in the two peer exchanges and repeat-after-me section. Public transcript locator ext-ulp_youtube-303; premium notes are grounding only. |
| sounds-letters-and-hello | V-002 | [recording](https://www.ukrainianlessons.com/episode2/) | P | ULP 1-02 public episode: W-075 and W-076 together as the intact formal greeting in the repeat-after-me greeting section and shop example. Public transcript locator ext-ulp_youtube-302; never split or parse the chunk. |
| sounds-letters-and-hello | V-003 | [recording](https://www.ukrainianlessons.com/episode5/) | P | ULP 1-05 public episode: the dedicated pronunciation trainer for the vowel И. Public transcript locator ext-ulp_youtube-299; compare with the native І model V-009, not English spelling. |
| sounds-letters-and-hello | V-004 | [recording](https://www.youtube.com/watch?v=hvB3VpcR3ZE) | Y | Pronunciation model for letter А. |
| sounds-letters-and-hello | V-005 | [recording](https://www.youtube.com/watch?v=gJFxRIPRZbI) | Y | Pronunciation model for letter О. |
| sounds-letters-and-hello | V-006 | [recording](https://www.youtube.com/watch?v=VB1O6PmtYRU) | Y | Pronunciation model for letter У. |
| sounds-letters-and-hello | V-007 | [recording](https://www.youtube.com/watch?v=W-1rCu0indE) | Y | Pronunciation model for letter И. |
| sounds-letters-and-hello | V-008 | [recording](https://www.youtube.com/watch?v=Ez95H4ibuJo) | Y | Pronunciation model for consonant М. |
| sounds-letters-and-hello | V-009 | [recording](https://www.youtube.com/watch?v=Z9TH0H4ShGo) | Y | Pronunciation model for vowel І. |
| sounds-letters-and-hello | V-010 | [recording](https://www.youtube.com/watch?v=vNUfiKHPYaU) | Y | Pronunciation model for consonant Н. |
| sounds-letters-and-hello | V-011 | [recording](https://www.youtube.com/watch?v=aFcvYfvQ2X4) | Y | Pronunciation model for consonant В. |
| sounds-letters-and-hello | V-012 | [recording](https://www.youtube.com/watch?v=v6-3Xg52Buk) | Y | Pronunciation model for consonant Л. |
| sounds-letters-and-hello | V-013 | [recording](https://www.youtube.com/watch?v=7UsFBgSL91E) | Y | Pronunciation model for consonant С. |
| sounds-letters-and-hello | V-014 | [recording](https://www.youtube.com/watch?v=J7sGEI4-xJo) | Y | Pronunciation model for consonant К. |
| sounds-letters-and-hello | V-015 | [recording](https://www.youtube.com/watch?v=JksSjjxyW5Y) | Y | Pronunciation model for consonant П. |
| sounds-letters-and-hello | V-016 | [recording](https://www.youtube.com/watch?v=fMGsQ5KPQgg) | Y | Pronunciation model for consonant Р. |
| reading-ukrainian | V-001 | [recording](https://www.youtube.com/watch?v=m-jcLR_gK0k) | Y | Pronunciation model for Т before CV and VC reading. |
| reading-ukrainian | V-002 | [recording](https://www.youtube.com/watch?v=gNjHqjTW9WQ) | Y | Pronunciation model for Ґ after hearing Г from the primer. |
| reading-ukrainian | V-003 | [recording](https://www.youtube.com/watch?v=aq0cjB90s3w) | Y | Pronunciation model for Й in short final-letter reading. |
| reading-ukrainian | V-004 | [recording](https://www.ukrainianlessons.com/episode10/) | P | ULP 1-10 public episode: the by-ear first-person review story and its first three questions and spoken answers, modeled in public transcript ext-ulp_youtube-294. T-016/T-017 premium notes are grounding only, never learner-facing source text. |
| reading-ukrainian | V-005 | [recording](https://www.youtube.com/watch?v=KFlsroBW0dk) | Y | Pronunciation model for Е before its sound rows. |
| reading-ukrainian | V-006 | [recording](https://www.youtube.com/watch?v=g4Bh-lqzd48) | Y | Pronunciation model for Д before its sound rows. |
| reading-ukrainian | V-007 | [recording](https://www.youtube.com/watch?v=BhASNxitC1A) | Y | Pronunciation model for З before its sound rows. |
| reading-ukrainian | V-008 | [recording](https://www.youtube.com/watch?v=V1hxBE_JbGg) | Y | Pronunciation model for Б before its word row. |
| reading-ukrainian | V-009 | [recording](https://www.youtube.com/watch?v=gVnclpSI0DU) | Y | Pronunciation model for Г before the Г/Ґ contrast. |
| reading-ukrainian | V-010 | [recording](https://www.youtube.com/watch?v=UsJkbdsY2RA) | Y | Pronunciation model for Ч before its sound rows. |
| reading-ukrainian | V-011 | [recording](https://www.youtube.com/watch?v=vpr58zJSJKc) | Y | Pronunciation model for Х before its sound rows. |
| reading-ukrainian | V-012 | [recording](https://www.youtube.com/watch?v=dIrGVcqPwqM) | Y | Pronunciation model for Ж before its sound rows. |
| reading-ukrainian | V-013 | [recording](https://www.youtube.com/watch?v=1D-6MIw3OXY) | Y | Pronunciation model for Ш before its sound rows. |
| reading-ukrainian | V-014 | [recording](https://www.ukrainianlessons.com/episode2/) | P | Lessons 1 s1 and 6 s1: W-075+W-076 intact formal opening greeting, from the greeting practice and shop example in public transcript ext-ulp_youtube-302. Replay the whole chunk; the single-letter videos do not establish this greeting. |
| reading-ukrainian | V-015 | [recording](https://www.youtube.com/watch?v=ksXIXj7CXwc) | Y | Full alphabet pronunciation video, identified by the publisher’s public alphabet guide and public transcript ext-ulp_youtube-304: whole-word models for W-118, W-109 and W-110. Restrict each excerpt to letters already taught; this is not evidence for the other primer word lists or whole sentences. |
| special-signs | V-001 | [recording](https://www.youtube.com/watch?v=cJlal8XKBxo) | Y | Soft-sign sound model; restrict practice to the taught-letter word pair, not the video vocabulary. |
| special-signs | V-002 | [recording](https://www.youtube.com/watch?v=ksXIXj7CXwc) | Y | Native pronunciation models for the taught letters, then the full alphabet after all letters; no ASR transcription is printed. |
| special-signs | V-003 | [recording](https://www.youtube.com/watch?v=9JdIBYCTWGw) | Y | Native Ю sound model before its two primer word values. |
| special-signs | V-004 | [recording](https://www.youtube.com/watch?v=u44eCjR2Oz8) | Y | Native Ц sound model before primer reading rows. |
| special-signs | V-005 | [recording](https://www.youtube.com/watch?v=haHRsFFZRQI) | Y | Native Ф sound model; no visual look-alike claim. |
| special-signs | V-006 | [recording](https://www.ukrainianlessons.com/episode2/) | P | Lesson 1 s1: native model for the intact W-075+W-076 formal greeting before it becomes a reading/copying chunk after ь is taught; public transcript ext-ulp_youtube-302. Also supports greeting recall in lessons 2–7. It does not record the T-001 minimal pair. |
| special-signs | V-007 | [recording](https://www.ukrainianlessons.com/episode15/) | P | ULP 1-15 public pronunciation trainer: native hard/soft consonant support, including the W-076 day word; public transcript ext-ulp_youtube-289. Support only: it does not say the exact T-001 W-119/W-120 pair and does not close those word-choice requirements. |
