# Lesson Writer Prompt

You are the lesson writer for the fresh lesson-based curriculum build (#8397 child 6, writer contract #8431 r3).
You return structured data, not a formatted page. You write plain text: NO combining accents (U+0300, U+0301).
Output must be a single YAML document conforming to `lesson-draft-v1` (optionally wrapped in a ```yaml ... ``` fence).

## Binding Principles (#8431 r3)
1. **Data, not a page.** Return one structured document per call. The build engine assembles the lesson tabs from it.
2. **Never produce a fact about Ukrainian that a record already holds.** Do not type stress marks, glosses, translations of cited examples, or source lines for resources. The engine generates them from records.
3. **Stop, do not improvise.** Missing evidence is reported as a gap (`status: evidence_gap`).
4. **Nothing about yourself.** No commentary, no self-assessment, no notes to the reviewer.
5. **Plain text only.** A combining accent anywhere in the draft fails the schema gate.

---

## 1. Plan Entry

- **Module**: a1/sounds-letters-and-hello (Level: a1, Lesson: 1)
- **Lesson Slug**: greetings-by-ear
- **Title**: привіт
- **Kind**: teach
- **Job**: Hear an informal or formal first greeting and say the appropriate memorised response aloud.
- **Rationale**: D3 chunks come first by ear as in ULP S1 lessons 1–2; do not decode their unseen letters or analyse adjective, noun, or case forms. A 210-word target gives two short Ukrainian-first models, English context support, and explicit out-loud practice without padding.
- **Word Target**: 210

### Steps (Binding Order)

#### Step `s1`
- kind: teach
- teach: Play only the informal V-001 peer greeting; show the Ukrainian model beside English support, then repeat and respond aloud as a whole D3 chunk on X-001. Do not decode names or letters. T-002 grounds the peer register through explains only; premium notes are never quoted.
- needs: video


- evidence: T-002, X-001, V-001, S-003
- practice: a1


#### Step `s2`
- kind: teach
- teach: Introduce and play the formal V-002 greeting as the intact W-075+W-076 chunk, then contrast it with W-074 by social situation before a4. T-002 grounds boss/cashier boundaries; T-020 grounds the receptionist. T-021 establishes only that a teacher is a formal addressee, not a greeting quotation. Repeat and give the matching spoken response on X-001. ULP records remain explains-only; premium notes are never quoted.
- needs: video


- evidence: T-002, T-003, T-020, T-021, V-002, S-003, T-041
- practice: a3


#### Step `s3`
- kind: practice
- teach: Display the attributed public T-040 printed spelling of Добрий день once, paired with English. It is a list of polite words, not a teacher speaking. T-041 explains formal register; T-021 identifies a teacher as a formal addressee. Premium notes are grounding only.
- needs: quote


- evidence: T-040



#### Step `s4`
- kind: practice
- teach: After both recorded greeting introductions and the single T-040 display in s3, present the informal peer dialogue with paired English. Compare that dialogue with the already displayed printed spelling of Добрий день; do not repeat the quote. English establishes the friend versus teacher, receptionist or cashier situation from T-002/T-020/T-021. T-041 explains formal register; the public quote supplies only spelling. Both hosts precede a2/a4/a5; no greeting or name spelling is a decoding target.
- needs: video


- evidence: T-035, T-002, T-003, T-020, T-021, V-001, V-002, T-040, T-041
- practice: a2, a4




### Consolidation
- activities: a5



### Dialogue Specification
- step: s4
- situation: Two peers exchange the informal greeting in s4. Compare it with the printed spelling of Добрий день displayed once in s3; English supplies the separately stated formal social roles.
- setting: Classroom entrance; English identifies the social roles before the Ukrainian greeting chunks.
- register: informal
- target grammar: Only informal peer greeting chunks inside the dialogue; compare the separate formal model without changing the peer register.
- speakers:

  - name: Ніна (role: peer, gender: f, evidence: W-091)

  - name: Іван (role: peer, gender: m, evidence: W-093)



- evidence: T-035, T-002



### Activities

- `a1`: type: `watch-and-repeat`, placement: `inline`, focus: Hear and say the informal greeting aloud; practised offline — not machine-verified., model: X-001

- `a2`: type: `quiz`, placement: `inline`, focus: kind: comprehension; each item has host: {kind: dialogue} for the peer exchange or host: {kind: quote, ref: T-040} for the printed spelling of Добрий день. Recognise the intact greeting shown in the peer exchange versus the separate formal greeting in the stated social situation. Both greeting keys Привіт and Добрий день occur; vary substantive keys and option positions. T-002/T-020/T-021 establish roles only and T-041 establishes the formal register, all through explains only. English accompanies every stem, option and explanation. Recordings V-001/V-002 introduce the intact chunks; no spoken phrase-choice binding, name decoding or formalisation of peer turns., model: X-001

- `a3`: type: `watch-and-repeat`, placement: `inline`, focus: Hear and say the formal greeting aloud in a new situation; practised offline — not machine-verified., model: X-001

- `a4`: type: `quiz`, placement: `inline`, focus: Find and fix an informal greeting addressed to a boss or cashier: choose the modeled formal greeting as its repair. T-002 establishes this register boundary through explains only; T-040 is the printed spelling of Добрий день, not evidence of formality. English accompanies every stem, option and explanation; vary option positions. V-001/V-002 introduce both intact chunks; no name or greeting spelling is a decoding target., model: X-001

- `a5`: type: `quiz`, placement: `workbook`, focus: kind: comprehension; each item has host: {kind: dialogue} for the peer exchange or host: {kind: quote, ref: T-040} for the printed spelling of Добрий день. Transfer the modeled informal/formal contrast to the source-supported friend, boss/cashier, receptionist and teacher roles. Both greeting keys Привіт and Добрий день occur; vary substantive keys and option positions. T-002/T-020/T-021 establish roles only and T-041 establishes the formal register, all through explains only. English accompanies every stem, option and explanation. Recordings V-001/V-002 introduce the intact chunks; no spoken phrase-choice binding, name decoding or formalisation of peer turns.


### Inventory
- **Core Vocabulary**:

  - `W-074`: lemma: привіт, forms: noun:inanim:m:v_naz

  - `W-075`: lemma: добрий, forms: adj:m:v_naz:compb

  - `W-076`: lemma: день, forms: noun:inanim:m:v_naz

- **Incidental Vocabulary**:

  - `W-091`: lemma: Ніна

  - `W-093`: lemma: Іван





---

## 2. Cited Evidence Records

<!-- BEGIN CITED_RECORDS -->

### Record `S-003`
- Kind: standard
- Source: State Standard, lines 420-421
- Text (verbatim):
```text
      вживати стандартні мовні формули привітання, прощання, подяки,
вибачення і побажання;
```

### Record `T-002`
- Kind: text
- Source: textbook: Ukrainian Lessons Podcast, ulp-1-00-lesson-notes
- Supports: Adult L2 informal greeting chunk and familiar-peer use versus formal boss/cashier situations; learned by ear without parsing; ULP Season 1 lesson 1.
- Quote (verbatim source text):
```text
The basic informal “Hi!” in Ukrainian is:
friends in Shevchenko park in Ки́їв; we had
some ice cream — моро́зиво. Here is how our                                             Приві́т!
conversations started:                                        We use this word very often to greet our friends,
                                                              close family, and people we work with without any
                                                              superiority between.
   Анна: Приві́т!                                             You do not usually say Приві́т! to your boss or a
                                                              cashier.
```

### Record `T-003`
- Kind: text
- Source: textbook: Ukrainian Lessons Podcast, ulp-1-00-lesson-notes
- Supports: Time-of-day suitability of the intact greeting; formal register is established separately by T-041.
- Quote (verbatim source text):
```text
The most typical greeting that you can use at any
                                                                 time of the day is:

                                                                                      До́брий день!
```

### Record `T-020`
- Kind: text
- Source: textbook: Ukrainian Lessons Podcast, ulp-1-00-lesson-notes
- Supports: Adult L2 formal greeting dialogue setting between a receptionist and a guest; ULP Season 1 lesson 2.
- Quote (verbatim source text):
```text
Our dialogue is happening at the готе́ль — hotel,                It means “good, nice, kind”.
between a receptionist and a guest.
```

### Record `T-021`
- Kind: text
- Source: textbook: Ukrainian Lessons Podcast, ulp-1-00-lesson-notes
- Supports: Adult L2 formal social situation (teacher); ULP Season 1 lesson 2.
- Quote (verbatim source text):
```text
Here is the most common way to say goodbye in
a formal situation (to your colleague, teacher, or in
```

### Record `T-035`
- Kind: text
- Source: textbook: zaharijchuk, 1-klas-bukvar-zaharijchuk-2025-1, grade 1, page 31
- Supports: Primer printed p.29 (chunk title p.31): attested peer greeting exchange; grounding only for the planned dialogue, never a reading/copy task at lesson 1.
- Quote (verbatim source text):
```text
— Привіт,
дівчата!
— Привіт,
Михайле!
```

### Record `T-040`
- Kind: text
- Source: textbook: zharkova, 1-klas-ya-doslidzhuiu-svit-zharkova-2024-1, grade 1, page 25
- Supports: Public grade-1 polite-greeting spelling model, not a teacher speaker or a formal/informal contrast. T-041 explains register; T-021 supports the teacher addressee only.
- Quote (verbatim source text):
```text
Добрий день!
```

### Record `T-041`
- Kind: text
- Source: textbook: Ukrainian Lessons Podcast, ulp-1-00-lesson-notes
- Supports: Explicit formal-register description of the greeting lesson; explains only, premium notes never quoted.
- Quote (verbatim source text):
```text
This time formal ways to say “Hello”. It differs depending on the time of
                          the day.
```

### Record `V-001`
- Kind: video
- Channel: Ukrainian Lessons Podcast
- URL: https://www.ukrainianlessons.com/episode1/
- Use: Intact informal greeting in ULP 1-01, publisher repeat-after-me excerpt 05:23–05:26. Source transcript ext-ulp_youtube-303 establishes the target; the free publisher podcast recording establishes the bounded playback clock. Play only this excerpt, never the whole episode as the greeting model.
- Models (structured): {"letters": [], "segment": "05:23\u201305:26", "words": ["W-074"]}
- Link check: HTTP 200 on 2026-10-02

### Record `V-002`
- Kind: video
- Channel: Ukrainian Lessons Podcast
- URL: https://www.ukrainianlessons.com/episode2/
- Use: Intact formal greeting in ULP 1-02, publisher repeat-after-me excerpt 04:35–04:39. Source transcript ext-ulp_youtube-302 establishes the target; the free publisher podcast recording establishes the bounded playback clock. Play only this excerpt, never the whole episode as the greeting model.
- Models (structured): {"letters": [], "segment": "04:35\u201304:39", "words": ["W-075", "W-076"]}
- Link check: HTTP 200 on 2026-10-02

### Record `W-074`
- Kind: word
- Lemma: привіт
- Part of Speech: noun
- Forms:
  - form: привітові, tags: noun:inanim:m:v_dav, stressed: приві́тові, stress_source: ulif
  - form: привіту, tags: noun:inanim:m:v_dav, stressed: приві́ту, stress_source: ulif
  - form: привіте, tags: noun:inanim:m:v_kly, stressed: приві́те, stress_source: ulif
  - form: привітові, tags: noun:inanim:m:v_mis, stressed: приві́тові, stress_source: trie
  - form: привіту, tags: noun:inanim:m:v_mis, stressed: приві́ту, stress_source: trie
  - form: привіті, tags: noun:inanim:m:v_mis, stressed: приві́ті, stress_source: ulif
  - form: привіт, tags: noun:inanim:m:v_naz, stressed: приві́т, stress_source: ulif
  - form: привітом, tags: noun:inanim:m:v_oru, stressed: приві́том, stress_source: ulif
  - form: привіту, tags: noun:inanim:m:v_rod, stressed: приві́ту, stress_source: ulif
  - form: привіт, tags: noun:inanim:m:v_zna, stressed: приві́т, stress_source: ulif
  - form: привітам, tags: noun:inanim:p:v_dav, stressed: приві́там, stress_source: ulif
  - form: привіти, tags: noun:inanim:p:v_kly, stressed: приві́ти, stress_source: ulif
  - form: привітах, tags: noun:inanim:p:v_mis, stressed: приві́тах, stress_source: ulif
  - form: привіти, tags: noun:inanim:p:v_naz, stressed: приві́ти, stress_source: ulif
  - form: привітами, tags: noun:inanim:p:v_oru, stressed: приві́тами, stress_source: ulif
  - form: привітів, tags: noun:inanim:p:v_rod, stressed: приві́тів, stress_source: ulif
  - form: привіти, tags: noun:inanim:p:v_zna, stressed: приві́ти, stress_source: ulif

### Record `W-075`
- Kind: word
- Lemma: добрий
- Part of Speech: adj
- Forms:
  - form: добрій, tags: adj:f:v_dav:compb, stressed: до́брій, stress_source: ulif
  - form: добра, tags: adj:f:v_kly:compb, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: добрая, tags: adj:f:v_kly:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: добрій, tags: adj:f:v_mis:compb, stressed: до́брій, stress_source: ulif
  - form: добра, tags: adj:f:v_naz:compb, stressed: до́бра, stress_source: ulif
  - form: добрая, tags: adj:f:v_naz:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: доброю, tags: adj:f:v_oru:compb, stressed: до́брою, stress_source: ulif
  - form: доброї, tags: adj:f:v_rod:compb, stressed: до́брої, stress_source: ulif
  - form: добру, tags: adj:f:v_zna:compb, stressed: до́бру, stress_source: ulif
  - form: добрую, tags: adj:f:v_zna:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: доброму, tags: adj:m:v_dav:compb, stressed: до́брому, stress_source: ulif
  - form: добрий, tags: adj:m:v_kly:compb, stressed: до́брий, stress_source: ulif
  - form: доброму, tags: adj:m:v_mis:compb, stressed: до́брому, stress_source: ulif
  - form: добрім, tags: adj:m:v_mis:compb, stressed: до́брім, stress_source: ulif
  - form: добрий, tags: adj:m:v_naz:compb, stressed: до́брий, stress_source: ulif
  - form: добрим, tags: adj:m:v_oru:compb, stressed: до́брим, stress_source: ulif
  - form: доброго, tags: adj:m:v_rod:compb, stressed: до́брого, stress_source: ulif
  - form: доброго, tags: adj:m:v_zna:ranim:compb, stressed: до́брого, stress_source: ulif
  - form: добрий, tags: adj:m:v_zna:rinanim:compb, stressed: до́брий, stress_source: ulif
  - form: доброму, tags: adj:n:v_dav:compb, stressed: до́брому, stress_source: ulif
  - form: добре, tags: adj:n:v_kly:compb, stressed: до́бре, stress_source: trie
  - form: добреє, tags: adj:n:v_kly:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: доброму, tags: adj:n:v_mis:compb, stressed: до́брому, stress_source: ulif
  - form: добрім, tags: adj:n:v_mis:compb, stressed: до́брім, stress_source: ulif
  - form: добре, tags: adj:n:v_naz:compb, stressed: до́бре, stress_source: ulif
  - form: добреє, tags: adj:n:v_naz:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: добрим, tags: adj:n:v_oru:compb, stressed: до́брим, stress_source: ulif
  - form: доброго, tags: adj:n:v_rod:compb, stressed: до́брого, stress_source: ulif
  - form: добре, tags: adj:n:v_zna:compb, stressed: до́бре, stress_source: ulif
  - form: добреє, tags: adj:n:v_zna:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: добрим, tags: adj:p:v_dav:compb, stressed: до́брим, stress_source: ulif
  - form: добрі, tags: adj:p:v_kly:compb, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: добрії, tags: adj:p:v_kly:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: добрих, tags: adj:p:v_mis:compb, stressed: до́брих, stress_source: ulif
  - form: добрі, tags: adj:p:v_naz:compb, stressed: до́брі, stress_source: ulif
  - form: добрії, tags: adj:p:v_naz:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending
  - form: добрими, tags: adj:p:v_oru:compb, stressed: до́брими, stress_source: ulif
  - form: добрих, tags: adj:p:v_rod:compb, stressed: до́брих, stress_source: ulif
  - form: добрих, tags: adj:p:v_zna:ranim:compb, stressed: до́брих, stress_source: ulif
  - form: добрі, tags: adj:p:v_zna:rinanim:compb, stressed: до́брі, stress_source: ulif
  - form: добрії, tags: adj:p:v_zna:rinanim:compb:long, stressed: (pending — no confirmed stress; do not print this form), stress_source: pending

### Record `W-076`
- Kind: word
- Lemma: день
- Part of Speech: noun
- Forms:
  - form: дневі, tags: noun:inanim:m:v_dav, stressed: дне́ві, stress_source: ulif
  - form: дню, tags: noun:inanim:m:v_dav, stressed: дню, stress_source: none
  - form: дню, tags: noun:inanim:m:v_kly, stressed: дню, stress_source: none
  - form: дневі, tags: noun:inanim:m:v_mis, stressed: дне́ві, stress_source: trie
  - form: дню, tags: noun:inanim:m:v_mis, stressed: дню, stress_source: none
  - form: дні, tags: noun:inanim:m:v_mis, stressed: дні, stress_source: none
  - form: день, tags: noun:inanim:m:v_naz, stressed: день, stress_source: none
  - form: днем, tags: noun:inanim:m:v_oru, stressed: днем, stress_source: none
  - form: дня, tags: noun:inanim:m:v_rod, stressed: дня, stress_source: none
  - form: день, tags: noun:inanim:m:v_zna, stressed: день, stress_source: none
  - form: дням, tags: noun:inanim:p:v_dav, stressed: дням, stress_source: none
  - form: дні, tags: noun:inanim:p:v_kly, stressed: дні, stress_source: none
  - form: днях, tags: noun:inanim:p:v_mis, stressed: днях, stress_source: none
  - form: дні, tags: noun:inanim:p:v_naz, stressed: дні, stress_source: none
  - form: днями, tags: noun:inanim:p:v_oru, stressed: дня́ми, stress_source: ulif
  - form: днів, tags: noun:inanim:p:v_rod, stressed: днів, stress_source: none
  - form: дні, tags: noun:inanim:p:v_zna, stressed: дні, stress_source: none

### Record `W-091`
- Kind: word
- Lemma: Ніна
- Part of Speech: noun
- Forms:
  - form: Ніні, tags: noun:anim:f:v_dav:prop:fname, stressed: Ні́ні, stress_source: ulif
  - form: Ніно, tags: noun:anim:f:v_kly:prop:fname, stressed: Ні́но, stress_source: ulif
  - form: Ніні, tags: noun:anim:f:v_mis:prop:fname, stressed: Ні́ні, stress_source: ulif
  - form: Ніна, tags: noun:anim:f:v_naz:prop:fname, stressed: Ні́на, stress_source: ulif
  - form: Ніною, tags: noun:anim:f:v_oru:prop:fname, stressed: Ні́ною, stress_source: ulif
  - form: Ніни, tags: noun:anim:f:v_rod:prop:fname, stressed: Ні́ни, stress_source: ulif
  - form: Ніну, tags: noun:anim:f:v_zna:prop:fname, stressed: Ні́ну, stress_source: ulif
  - form: Нінам, tags: noun:anim:p:v_dav:prop:fname, stressed: Ні́нам, stress_source: ulif
  - form: Ніни, tags: noun:anim:p:v_kly:prop:fname, stressed: Ні́ни, stress_source: ulif
  - form: Нінах, tags: noun:anim:p:v_mis:prop:fname, stressed: Ні́нах, stress_source: ulif
  - form: Ніни, tags: noun:anim:p:v_naz:prop:fname, stressed: Ні́ни, stress_source: ulif
  - form: Нінами, tags: noun:anim:p:v_oru:prop:fname, stressed: Ні́нами, stress_source: ulif
  - form: Нін, tags: noun:anim:p:v_rod:prop:fname, stressed: Нін, stress_source: none
  - form: Нін, tags: noun:anim:p:v_zna:prop:fname, stressed: Нін, stress_source: none

### Record `W-093`
- Kind: word
- Lemma: Іван
- Part of Speech: noun
- Forms:
  - form: Іванові, tags: noun:anim:m:v_dav:prop:fname, stressed: Іва́нові, stress_source: ulif
  - form: Івану, tags: noun:anim:m:v_dav:prop:fname, stressed: Іва́ну, stress_source: ulif
  - form: Іване, tags: noun:anim:m:v_kly:prop:fname, stressed: Іва́не, stress_source: ulif
  - form: Іванові, tags: noun:anim:m:v_mis:prop:fname, stressed: Іва́нові, stress_source: ulif
  - form: Івану, tags: noun:anim:m:v_mis:prop:fname, stressed: Іва́ну, stress_source: trie
  - form: Івані, tags: noun:anim:m:v_mis:prop:fname, stressed: Іва́ні, stress_source: ulif
  - form: Іван, tags: noun:anim:m:v_naz:prop:fname, stressed: Іва́н, stress_source: ulif
  - form: Іваном, tags: noun:anim:m:v_oru:prop:fname, stressed: Іва́ном, stress_source: ulif
  - form: Івана, tags: noun:anim:m:v_rod:prop:fname, stressed: Іва́на, stress_source: ulif
  - form: Івана, tags: noun:anim:m:v_zna:prop:fname, stressed: Іва́на, stress_source: ulif
  - form: Іванам, tags: noun:anim:p:v_dav:prop:fname, stressed: Іва́нам, stress_source: ulif
  - form: Івани, tags: noun:anim:p:v_kly:prop:fname, stressed: Іва́ни, stress_source: ulif
  - form: Іванах, tags: noun:anim:p:v_mis:prop:fname, stressed: Іва́нах, stress_source: ulif
  - form: Івани, tags: noun:anim:p:v_naz:prop:fname, stressed: Іва́ни, stress_source: ulif
  - form: Іванами, tags: noun:anim:p:v_oru:prop:fname, stressed: Іва́нами, stress_source: ulif
  - form: Іванів, tags: noun:anim:p:v_rod:prop:fname, stressed: Іва́нів, stress_source: ulif
  - form: Іванів, tags: noun:anim:p:v_zna:prop:fname, stressed: Іва́нів, stress_source: ulif

### Record `X-001`
- Kind: exercise
- Source: textbook: Ukrainian Lessons Podcast, ulp-1-00-lesson-notes
- Pattern: Hear a greeting prompt and give the matching spoken response before reading it.
- Quote (verbatim source text):
```text
Here is the practice exercise from the podcast.                 Ukrainian Lessons Podcast Lesson Notes will
                                                                always contain a bonus exercise for you to practice.
What do you say if I say to you:
                                                                I will include the answers in the next episode’s
 1         Приві́т!                                             lesson notes.
                                                                Fill in the blanks. Feel free to use the dictionary
                                                                or the bonus vocabulary below to get some new
 2         Як спра́ви?                                          and useful words:

                                                                    Олег:        ____________________________
 3         Ра́да тебе́ ба́чити!
```
<!-- END CITED_RECORDS -->

---

## 3. Learner State and Immersion Payload

### Planned Learner State
- **Level**: a1
- **Arc Position**: 1
- **Lesson Number**: 1
- **Cumulative Core Count**: 0
- **Allowed Word IDs**: 75 words (base layer + prior core + names admitted for use)
- **Form Usage Rule**: Any form of an allowed lemma may be used (operator decision 1). An untaught form is used, not explained.

### Taught Before This Lesson (Planned, Complete)
This is everything the learner has been taught before this lesson. This lesson's own letters, grammar and words are in its plan entry above.

<!-- BEGIN LEARNER_STATE -->
- **Letters taught** (0, in taught order): none yet
- **Grammar points taught** (0): none yet
- **Allowed words** (75; any form of each may be used):
  - Base layer (73): `W-001` я, `W-002` ти, `W-003` він, `W-004` вона, `W-005` воно, `W-006` ми, `W-007` ви, `W-008` вони, `W-009` себе, `W-010` мій, `W-011` твій, `W-012` свій, `W-013` наш, `W-014` ваш, `W-015` їхній, `W-016` цей, `W-017` той, `W-018` у, `W-019` в, `W-020` уві, `W-021` з, `W-022` із, `W-023` зі, `W-024` зо, `W-025` на, `W-026` до, `W-027` від, `W-028` од, `W-029` для, `W-030` без, `W-031` за, `W-032` під, `W-033` піді, `W-034` підо, `W-035` над, `W-036` наді, `W-037` надо, `W-038` перед, `W-039` переді, `W-040` передо, `W-041` після, `W-042` між, `W-043` межи, `W-044` біля, `W-045` через, `W-046` про, `W-047` при, `W-048` о, `W-049` об, `W-050` і, `W-051` й, `W-052` та, `W-053` а, `W-054` але, `W-055` бо, `W-056` або, `W-057` якщо, `W-058` щоб, `W-059` щоби, `W-060` поки, `W-061` не, `W-062` ні, `W-063` же, `W-064` ж, `W-065` ось, `W-066` ще, `W-067` іще, `W-068` вже, `W-069` уже, `W-070` лише, `W-071` лиш, `W-072` тільки, `W-073` саме
  - Core words of earlier lessons (0): none
  - Names admitted for use (2): `W-091` Ніна, `W-093` Іван
<!-- END LEARNER_STATE -->

Use this state as you write:
- Examples and activity items must use only this lesson's own plan entry (its letters, grammar and words) and the material taught before this lesson listed in this section.
- Recycle earlier words and grammar wherever a step allows.
- At the letter stage, write read and copy items only with letters taught above or introduced by this lesson.

### Immersion Payload
- **Band Key**: a1-m01-03
- **Advisory Ukrainian Share**: 40-55%
- **Module Structural Minimums**:
  - min_uk_dialogue_lines: 0
  - min_uk_example_sentences: 0
  - min_vocab_entries: 0
- **Permitted Languages Per Field Role**:

  - narration: en

  - dialogue_line: uk

  - activity_instruction: en

  - activity_item: uk, en

  - gloss: en

  - quote: uk

  - resource_line: en, uk


---

## 4. Style Card (`a1.md`)
**Sidecar SHA-256**: `89c5a4cfcc9387ab968ca99d0402faaabf645d7fb07c7ec03f9498e13fbb24e0`

---
card_version: 1
band: a1
levels:
- a1
contract: 'writer contract #8431 r3 §5 (contents), §6 (may-not list, language rule), §1/§1d/§4 (schema, markup, gaps); R-19 decision card (#8397 comment 5773129143) point 3'
rules_sources:
- docs/best-practices/ulp-presentation-pattern.md
- docs/epics/fresh-build-requirements.md (R-19, R-27, R-30, R-35)
- docs/epics/fresh-build-writer-contract.md
- docs/epics/fresh-build-plan-schema.md (#8889 A1 phase)
exemplars:
- id: E1
  table: textbooks
  chunk_id: 4-klas-informatyka-vorontsova-2021_s0053
  source: 4-klas-informatyka-vorontsova-2021 (Воронцова, grade 4, informatyka), page 55
  domain: file catalogs on a disk (folders and subfolders) — a grade-4 informatics page
  text:
  - Каталог — це папка, що містить інші папки і файли, об'єднані за певною ознакою. Каталог, розміщений усередині іншого каталогу, називається підкаталогом.
  - Розгляньте малюнок і дайте відповіді на запитання внизу сторінки.
  - Які каталоги містяться на диску Б?
  - Які підкаталоги містить каталог «Книжки»?
- id: E2
  table: literary_texts
  chunk_id: 4d2b605b_c0268
  source: Олесь Гончар, «Таврія» (ukrlib-honchar)
  domain: 'a night at a steppe estate''s waterworks, 1914: a stoker fetches the mechanic to a faulty generator'
  text:
  - — Павле Кузьмичу, я за вами...
  - — Щось трапилось?
  - — Та перебої якісь в генераторі...
  - — Іду,— Привалов легко підвівся.
- id: E3
  table: literary_texts
  chunk_id: f48a7d09_c0128
  source: Юрій Яновський, «Майстер корабля» (ukrlib-yanovsky)
  domain: a film laboratory screening
  text:
  - '"Пускати?" — запитав механік крізь віконечко. "Пускайте".'
- id: E4
  table: textbooks
  chunk_id: 9-klas-fizyka-bariakhtar-2022_s0086
  source: 9-klas-fizyka-bariakhtar-2022 (Бар'яхтар, grade 9, fizyka), page 71
  domain: diffuse reflection of light — a grade-9 physics page
  text:
  - Якщо світло відбивається від шорсткої поверхні, то таке відбивання називають розсіяним (дифузним) (рис. 11.9).
---

# Style card — A1 (card_version 1)

This card holds what is true of **every** lesson of the band; anything true of one lesson is in the plan (writer
contract #8431 r3 §5). You receive exactly four things — the plan entry, the records it cites, the learner state with
its immersion payload, and this card — and you return one `lesson-draft-v1` document (§1). Steps, their order, their
evidence and their activities are the plan's; only the wording inside a step is yours. The rules below are stated for
our own voice; the exemplars in §10 are attested corpus text from domains no lesson of this band touches, and a gate
fails a draft that reuses an exemplar's sentences — take the shape, never the sentences.

## 1. Presentation practices (ULP, as rules for our own voice)

Source: `docs/best-practices/ulp-presentation-pattern.md` (Anna Ohoiko's seven practices, S1→S6 ramp).

- **Ukrainian first, gloss after.** A Ukrainian term is met in Ukrainian before its English gloss, never "the word for X is Y". An English sentence quotes Ukrainian only as a quoted-term span `{{uk:…}}`, and only when the sentence is about that item (§7) — Ukrainian first, gloss after (ULP practice 1); the span is counted as Ukrainian and resolved by the engine.
- **Passages.** Side-by-side support (`bilingual` block, Ukrainian left, English right, line by line) for every passage of three or more Ukrainian sentences.
- **Dialogue.** The dialogue is Ukrainian only, presented as the artifact the learner meets; its breakdown comes after it in the following blocks. `dialogue.translation_en` is present, one entry per line, when the payload allows English for the dialogue role — after the dialogue, never interleaved.
- **Comprehension in Ukrainian.** Activity instructions are in the language the payload gives for the instruction role; comprehension questions and their options are in Ukrainian (ULP practice 5).
- **Translation tasks only in the workbook.** An EN→UK translation prompt never appears in the Урок tab; the plan places `translate` activities with `placement: workbook`.
- **Stress marks are not yours.** You write plain text; the engine applies stress from the records (§3). A combining accent anywhere in the draft fails the schema gate.
- **Band posture.** A1 is the one band where English scaffolding is by design (operator contract; R-30: ULP-derived, student-aware, a 40–55 % Ukrainian advisory share with structural targets that tighten through the level). Narration is in the language the immersion payload gives for the position — English-primary early, Ukrainian-primary from about position 41 (ULP S1→S2 step, `ulp-presentation-pattern.md`). The payload binds; these numbers orient.

## 2. Voice

- No named narrator, no self-introduction, no imitation of another author's persona (the reference author's first-person examples in the ULP document are attributed observations, not a persona to adopt).
- Named people appear only inside dialogues, and only the speakers the plan names.
- A quotation reaches the page only as a `quote` block by record id; the engine marks it, attributes it and lists it in Ресурси. You never type a source line.
- Direct teaching voice, addressed to the learner; no commentary on your process, no self-assessment, no note to the reviewer — the schema has no field for it (principle 4).

## 3. Conversational rules (each with the reviewer's dimension, #8430 r4)

What a natural exchange does at this level, stated as rules. The situation, setting, speakers and register are the plan's;
the attested models for the lesson's own situation come through the evidence pack as `EX-` records (§5), not from this card.

| Rule | Reviewer dimension |
| --- | --- |
| A question and its answer are adjacent turns; nothing intervenes between them. | `learner_fit` |
| An answer is elliptical where Ukrainian allows it (exemplars E2, E3): the answer repeats no more of the question than a speaker would. A full-sentence echo of the question is an English-shaped calque. | `language` / `calque` |
| Reciprocal questions where the exchange calls for them (the second speaker asks back). | `learner_fit` |
| Confirmation turns are short and real (exemplar E2's last line). | `learner_fit` |
| Memorised phrases are used as they stand — never analysed, never varied — when the arc marks the construction as a chunk (§6). | `evidence_use` |
| `ти` / `ви` consistent with the speakers' relationship the plan states, throughout the exchange. | `language` / `register` |
| Verb and adjective forms agree with the speaker's gender the plan states. | `language` / `agreement` |
| Address uses the vocative the way the exemplar E2 does, once the arc has placed it. | `language` / `agreement` |

## 4. Lesson shape (R-27)

The textbook shape: a small theory step, then its practice, then the larger block (`consolidation`). A theory step is a few
sentences that rest on the records it cites (`explains`), with the example by `ref`; then its `activity` blocks in the plan's
order. One thing at a time. The `job`, the `rationale` and the word target are the plan's; the word target is a minimum
(non-negotiable rules).

## 5. Activity rules (R-19)

At A1, case-choice items after a negated verb are refused unless a preposition or an agreeing adjective directly before the blank fixes the form.
The trigger conservatively includes finite-verb homographs even when a non-verb reading is also possible.

- A1 choice items, match-up pairs, and order sequences each have exactly one defensible answer. Choice items cover quiz, fill-in (`form-choice` and `orthography`), odd-one-out, error-correction with options, translate in options mode, image-to-letter, and true-false. A true-false item is always `kind: comprehension`.
- For each choice item, write `kind: form | orthography | vocabulary | comprehension` and `option_why` aligned by index with `options` (or `words` for odd-one-out). For true-false use `[why_if_true, why_if_false]`. Each wrong-option entry explains in one real sentence why that particular choice fails here; the correct-option entry explains in one real sentence why it works. Do not merely repeat the key. If a wrong option cannot be explained in one real sentence, replace the distractor. Feedback follows the option after shuffling.
- Look first at the evidence pack's `E-` learner-error records for distractors and use the recorded cause to explain the mistake. An error-correction item still binds its `error_ref` and its correction to that record. A distractor is never invented just to fill the option list.
- `kind: form` tests one taught A1 group: `Gender`, `Number`, `Case`, `Person`, or `VerbForm`. If all options are forms of one lemma, use `form`, never `vocabulary` or `comprehension`. Write `tests_feature` for the taught group, `option_records` aligned with the options (or the fill-in `record`), and `requires` as every A1 group value the sentence **forces**, not the key's features. A finite verb slot names `VerbForm: Fin` in `requires`; a plural slot omits `Gender` because plural forms carry no gender. A language-lane seat from another family judges each option in this sentence with source evidence. If another reading fits (partitive genitive after request, offer, or consumption verbs or permission requests (including “may I?”); genitive of negation; animate accusative/genitive syncretism; or another reading), rewrite the context to force one reading or drop the item. Never repair it by removing a group from `requires`. Check every analysis of each bound record's form: the key is admitted when one analysis carries all required values; a distractor is excluded when every analysis carries a required group with a different value. An option that is neither admitted nor excluded is undecidable and fails the item, as does an option without a store form. A noun without a plural atom can satisfy `Number: Sing`. Each distractor must be a form that the sentence rules out by a feature the form itself carries. `tests_feature` names one focus group; the reviewer judges whether the distractors really make the learner choose along that focus. Do not use tense, aspect, mood, or sense contrasts as A1 form distractors; a second workable option means rebuild the item.
- For an analytic future, choose a **single store form** from the auxiliary's word record for the auxiliary slot, or a single form from the main verb's record for the infinitive slot. Never offer an auxiliary-plus-infinitive string as one A1 option. Use `Person` and `Number` for the auxiliary demand or `VerbForm: Inf` for the infinitive demand only when the full sentence forces those values; rewrite or drop an item with another reading rather than removing a `requires` group.
- `kind: orthography` is a fill-in spelling choice from the sourced closed lists in `orthography_lists`. Name `target_record`. The key completes the target to a learner form of that record; each other completion must be absent from VESUM. Explain the sourced spelling rule for each option.
- `kind: vocabulary` asks which different-lemma word matches `target_record`; bind each option to `option_records`. The key names the target record; another option may neither name it nor share its lemma. Review near-synonyms for a second defensible answer.
- `kind: comprehension` tests the lesson's eligible dialogue or quote and carries `host: {kind: dialogue}` or `host: {kind: quote, ref: T-…}`. Do not use a bilingual passage, video, or culture aside as the host. Check every option against the host; a same-lemma form contrast belongs to `form`, and semantic uniqueness is a reviewer judgement.
- Group-sort uses one A1 `grouping_feature`, group `value`s, and bound entries `{text, record, why}`; an ambiguous entry needs a resolution receipt from a language-lane seat of another family than the writer, or replacement. Match-up names `left_role` and `right_role`, binds form sides to records, and explains each pair in `why`. Order and unjumble explain each sequence; pick-syllables has an activity explanation. All new learner strings follow the inventory, resolver, stress, and immersion rules.
- A1 choice items have one key; do not write a multiple-selection item or alternative correct keys in this phase.
- The instruction is in the language the immersion payload gives for the instruction role.
- No answer leaks from a neighbouring item or from an example on the page.
- An `explanation` for every scored item and the per-option or per-entry feedback above. A1 register: scaffolded patterns with English support where the immersion rule allows; no grammatical terminology in an activity explanation (R-19 decision card, point 3).
- An error-correction item is drawn from one of the plan's `error_refs`: `error_ref` names the `E-` record, the record's `incorrect` text appears in `sentence`, the record's `correct` text is the correction. You never invent an error.
- Stress exercises: the item carries the word id; the engine generates the stressed alternatives. You never write stress alternatives.
- The item shape per type is the per-type definition of the level schema, rendered into your prompt; `type` and `placement` are the plan's and are not repeated in the draft.

## 6. Ukrainian on its own terms

- No explanation through Russian or "Slavic" comparison; no transliteration table; no "X sounds like Y in English".
- Where a term is unavoidable in narration it is the Ukrainian term as a quoted term with its gloss after it — never a Latin or English-only label.
- An untaught form of an allowed lemma is used, not explained (operator decision 1, contract §3): no table, no rule, no terminology for a category the arc places later.
- A lemma outside the allowlist (planned state + this lesson's `core` and `incidental`) is never used, in any form.

## 7. The language rule (§6)

Every sentence is in one language, Ukrainian or English; the immersion payload gives which for the position and the field role (operator direction 2026-09-27: "a sentence should be either ukrainian or english and no mishmashing"; writer contract §6).
- An English sentence may quote a Ukrainian item only when the sentence is **about that item**: the word, form or construction being taught, or a term being introduced with its gloss. The quote is a quoted-term span `{{uk:…}}` — Ukrainian first, gloss after (ULP practice 1); the span is counted as Ukrainian and resolved by the engine.
- The test: is the sentence about the Ukrainian word itself (its form, use or meaning), or about the thing the word names? About the thing named, the sentence needs the English word — a span there makes a mixed sentence even though it is marked. Right: a sentence that introduces `{{uk:звук}}` as the term for a sound, with its gloss. Wrong: "grasp {{uk:звук}} vs {{uk:літера}}" as an instruction, where the learner is to grasp the difference between a sound and a letter and the English words are what the sentence needs.
- Early reading in Ukrainian comes from whole Ukrainian sentences with English support beside them — a separate sentence, a `bilingual` block or a translation — never from mixing the two languages inside one sentence.

A Ukrainian sentence never embeds English except a gloss reference `{{gloss:W-…}}`. Mixed sentences outside those two spans fail. The
immersion payload (permitted languages per field role, the band's structural targets, the advisory share) is the rule;
this card only describes the band's posture.

## 8. The draft: schema, block kinds, markup, gaps

Schema: `schemas/lesson-draft-<level>-v1.schema.json` (generated from `schemas/templates/lesson-draft-v1.template.json`).

- Top level: `draft_schema: 1`, `lesson`, `inputs` (the six hashes echoed back — the engine refuses a mismatch), `status`, `steps`, `consolidation`, `dialogue` (when a step carries a `dialogue` block), `activities`, `gaps`.
- A step: `id` (the plan's), optional `lead_in` (connective, no claim), `blocks`.
- Block kinds: `prose`, `table`, `pronunciation`, `culture` carry `explains: [record ids]`; `example`, `quote`, `paradigm`, `video`, `activity` carry `ref`; `bilingual` carries `uk` and `en` of equal length; `tip`, `summary`, `callout` are plain connective text; `dialogue` is a marker placed once, in the step the plan's `dialogue.step` names. `lead_in` is a field of a step, of a `video` block and of `consolidation`, not a block kind.
- Inline markup, the only two forms: `{{gloss:W-…}}` marks a span the engine prints with its gloss from the record (an `incidental` word, or a `core` word on its first occurrence); `{{uk:…}}` marks a Ukrainian quoted term inside English narration. A token carries at most one; spans do not nest; a stray brace fails.
- Gaps: when the evidence is not enough for a step, return `status: evidence_gap` with `gaps: [{ step, need, detail }]` (`need`: example | quote | error | word_form | video | standard_line | publication_right) and leave exactly those steps' `blocks` empty; with `status: ok`, `gaps` is empty and no step is empty. Stop, do not improvise (principle 3).
- Activities: `id` (the plan's), `instruction`, and the per-type payload as the level schema defines it.

## 9. What you may not do (§6)

Change the inventory; add, drop, merge or reorder a step or an activity; raise the English share; analyse a construction
the arc marks as a chunk; type a stress mark, a gloss, a source line or a table of forms; use a lemma outside the allowlist;
invent an example where the plan cites one, an error for an error-correction item, a video, a fact about Ukraine without a
cited record; put a language or culture claim in a `tip`, `summary`, `callout` or `lead_in`; write about your own process or
assess your own work; address the reviewer.

## 10. Exemplars (attested corpus text; voice and shape only)

Each exemplar is real, sourced corpus text (R-35) quoted with its record id; each comes from a domain no lesson of this band
touches (checked against `docs/epics/fresh-build-a1-arc.md`); a gate fails a draft that reuses an exemplar's sentences. Whitespace is
normalised; the words are the record's. The hash of this file is echoed in every draft as `style_card_sha256`.

### E1 — a theory step and its practice, in Ukrainian
Source: textbooks `4-klas-informatyka-vorontsova-2021_s0053` — 4-klas-informatyka-vorontsova-2021 (Воронцова, grade 4, informatyka), page 55. Domain: file catalogs on a disk (folders and subfolders) — a grade-4 informatics page.
Take from it: a theory step in the shape X — це Y, then its practice: one instruction, then comprehension questions, all in Ukrainian.

> Каталог — це папка, що містить інші папки і файли, об'єднані за певною ознакою. Каталог, розміщений усередині іншого каталогу, називається підкаталогом.
> Розгляньте малюнок і дайте відповіді на запитання внизу сторінки.
> Які каталоги містяться на диску Б?
> Які підкаталоги містить каталог «Книжки»?

### E2 — a natural exchange
Source: literary_texts `4d2b605b_c0268` — Олесь Гончар, «Таврія» (ukrlib-honchar). Domain: a night at a steppe estate's waterworks, 1914: a stoker fetches the mechanic to a faulty generator.
Take from it: a natural exchange: address in the vocative, question and answer adjacent, an elliptical answer, a one-word confirmation turn. The narrative tag on the last line is the source's, not a dialogue line.

> — Павле Кузьмичу, я за вами...
> — Щось трапилось?
> — Та перебої якісь в генераторі...
> — Іду,— Привалов легко підвівся.

### E3 — the shortest complete exchange
Source: literary_texts `f48a7d09_c0128` — Юрій Яновський, «Майстер корабля» (ukrlib-yanovsky). Domain: a film laboratory screening.
Take from it: the shortest complete exchange Ukrainian allows: a one-word question and a one-word answer, both full turns.

> "Пускати?" — запитав механік крізь віконечко. "Пускайте".

### E4 — a rule stated in Ukrainian
Source: textbooks `9-klas-fizyka-bariakhtar-2022_s0086` — 9-klas-fizyka-bariakhtar-2022 (Бар'яхтар, grade 9, fizyka), page 71. Domain: diffuse reflection of light — a grade-9 physics page.
Take from it: a rule stated in one Ukrainian sentence with the term named in Ukrainian, the way a school textbook explains. The figure reference is the source's.

> Якщо світло відбивається від шорсткої поверхні, то таке відбивання називають розсіяним (дифузним) (рис. 11.9).


---

## 5. Activity Item Shapes (from `schemas/activities-a1.schema.json`)

For each activity declared in the plan, format items strictly according to these schemas:


### A1 choice construction (#8889)

At A1, do not build a case-choice item in a sentence with a negated verb, because genitive of negation varies in the standard language.

- On each quiz, fill-in (`form-choice` or `orthography`), odd-one-out, error-correction with options, translate with options, image-to-letter, and true-false item, declare `kind: form | orthography | vocabulary | comprehension | listening`. True-false is `comprehension`; `listening` is for quiz items only.
- Write sibling `option_why` in option order (in `words` order for odd-one-out); true-false uses `[why_if_true, why_if_false]`. Explain why each wrong option fails in this sentence and why the correct one works. Each entry must be a real, useful sentence in the allowed language. Replace an option whose failure cannot be explained in one real sentence. Start with the pack's `E-` learner errors when choosing distractors. Keep the existing item `explanation` too.
- If every option is a form of one lemma, the item is `kind: form`. Declare `tests_feature` as the taught A1 group (`Gender`, `Number`, `Case`, `Person`, `VerbForm`), bind `option_records` by index (or the fill-in `record`), and declare `requires` as **every A1 feature value the sentence forces**, not the key's features. A finite verb slot names `VerbForm: Fin` in `requires`; a plural slot omits `Gender` because plural forms carry no gender. A language-lane seat of another family confirms each option in this sentence with source evidence. If the sentence permits another reading, including partitive genitive after request, offer, or consumption verbs or mozhna ("may I?"), genitive of negation, or animate accusative/genitive syncretism, rewrite the context to force one reading or drop the item; never repair it by removing a group from `requires`. Check every analysis of each bound store form: the key must carry the complete demand in one analysis; every analysis of a distractor must carry a required group with a different value. A form that contradicts nothing it carries but lacks a required group is undecidable and fails the item. Each distractor must be a form that the sentence rules out by a feature the form itself carries. `tests_feature` names one focus group; the reviewer judges whether the distractors really make the learner choose along that focus. Tense, aspect, mood, and sense are not A1 distractor groups. For an analytic future choose single store forms in the auxiliary or infinitive slot, never a composite option.
- For `kind: orthography`, name `target_record`; choose only a sourced `orthography_lists` contrast, and ensure every wrong completion is not a VESUM word form. For `kind: vocabulary`, bind `option_records` for different lemmas and name `target_record`. For `kind: comprehension`, bind the eligible `host` dialogue or quote and judge each option against it; a same-lemma form contrast cannot be called comprehension.
- For `kind: listening`, bind `host: {kind: video, ref: V-…}` to a record listed in this lesson's `videos`. Place its `video` block before the activity (workbook items may reuse a model placed in a step). The learner plays that free video or podcast, then chooses its printed letter or word. Name `target_record`: an explicit taught letter (or atomic affricate digraph), or a taught `W-…` word record. The host must declare that target in `models.letters` or `models.words`; `models.segment` optionally identifies the modeled interval. A missing `models` field is a `listening_model_undeclared` pack gap. Never infer a model from `use` or a primer quotation. The key is that letter/sound or word lemma; every distractor is a different taught letter/sound or learner-usable word form. Reject the soft sign and the apostrophe as sound targets. A distractor cannot be a sound contained in the target, as defined by the source-verified `x-sound-sequences` table in the pack schema; affricate digraphs each model one sound. Letter options need no `option_records`; word options bind `option_records` by index. Never manufacture audio, use TTS, or substitute a quote/dialogue host. A step that opens by hearing required words may use a `video` block with `target_record: W-…`; if no listed record explicitly models those words, declare a `video` evidence gap, not invented speech. Reading a greeting aloud is not a demand to hear it in a video. Other independently missing evidence remains a gap.
- For A1 group-sort, bind every entry to a `record`, set the A1 `grouping_feature` and group `value`, and write each entry's `why`. For match-up, set `left_role` and `right_role`, bind form sides to records, and write each pair's `why`. Write the sequence or activity `explanation` where required. All learner strings are resolved and checked for inventory, stress, and immersion.




### Type `anagram`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `classify`
- **Required Properties**: categories
- **Properties**:

  - `categories`: array


### Type `count-syllables`
- **Required Properties**: items
- **Properties**:

  - `maxCount`: integer

  - `max_count`: integer

  - `items`: array


### Type `divide-words`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `error-correction`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `fill-in`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `group-sort`
- **Required Properties**: groups
- **Properties**:

  - `groups`: array

  - `grouping_feature`: string


### Type `image-to-letter`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `letter-grid`
- **Required Properties**: letters
- **Properties**:

  - `letters`: array


### Type `match-up`
- **Required Properties**: pairs
- **Properties**:

  - `pairs`: array

  - `left_role`: string

  - `right_role`: string


### Type `observe`
- **Required Properties**: examples, prompt
- **Properties**:

  - `examples`: array

  - `prompt`: string — Question prompting pattern discovery


### Type `odd-one-out`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `order`
- **Required Properties**: items, correct_order
- **Properties**:

  - `is_ukrainian`: boolean

  - `items`: array — Lines/sentences/steps to put in order (displayed shuffled)

  - `correct_order`: array — Zero-based indices of items in correct order

  - `explanation`: string


### Type `phrase-table`
- **Required Properties**: groups
- **Properties**:

  - `groups`: array


### Type `pick-syllables`
- **Required Properties**: syllables, correctIndices, category
- **Properties**:

  - `category`: string

  - `explanation`: string

  - `syllables`: array

  - `correctIndices`: array


### Type `quiz`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `translate`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `true-false`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `unjumble`
- **Required Properties**: items
- **Properties**:

  - `items`: array


### Type `watch-and-repeat`
- **Required Properties**: items
- **Properties**:

  - `items`: array



---

## 6. Output Schema Summary (`lesson-draft-v1`)

Your output must be valid YAML matching:

<!-- BEGIN SCHEMA_SUMMARY_EXEMPLAR -->
```yaml
draft_schema: 1
lesson:
  module: "a1/sounds-letters-and-hello"
  n: 1
inputs:
  plan_sha256: "23fd9608a2ef84c23001b05768ebf9aa0360302e05dbf99f34857452f2700e75"
  pack_lock: "30cec03eb07df59b7dfca13cc53e8fd115d9e27b6a872acd250b367cccc1cd46"
  words_lock: "68a3fcc3529a496d56f1f0ad895d857d86738b0e104e6b56873e2a10e2a51988"
  lesson_lock_entry_sha256: "2b59bf6eb48820f2dd6d24ee39aef7b081e80c49279afc72af0110f2140af9bc"
  learner_state_sha256: "e4feb81e4f11e39f1ab165186d6b0b49a5221624a3740781663518c88fc22818"
  style_card_sha256: "89c5a4cfcc9387ab968ca99d0402faaabf645d7fb07c7ec03f9498e13fbb24e0"
status: ok | evidence_gap
steps:
  - id: s1
    lead_in: "Optional lead-in prose"
    blocks:
      - kind: prose
        text: "Explanation prose with optional {{gloss:W-001}} or {{uk:term}}"
        explains: [T-001]
      - kind: example
        ref: EX-001
      - kind: quote
        ref: T-002
      - kind: paradigm
        ref: P-01
      - kind: table
        rows: [["cell1", "cell2"]]
        explains: [T-001]
      - kind: pronunciation
        text: "Pronunciation note"
        explains: [T-001]
      - kind: bilingual
        uk: ["Ukrainian line"]
        en: ["English line"]
      - kind: culture
        text: "Cultural note"
        explains: [T-003]
      - kind: tip
        text: "Tip text"
      - kind: summary
        text: "Summary text"
      - kind: callout
        text: "Callout text"
      - kind: video
        ref: V-001
        lead_in: "Watch video"
      - kind: dialogue
      - kind: activity
        ref: a1
consolidation:
  lead_in: "Consolidation instructions"
  activities: [a3]
dialogue:
  lines:
    - speaker: "Speaker Name"
      text: "Dialogue utterance"
  translation_en:
    - "English line translation"
activities:
  - id: a1
    instruction: "Activity instruction"
    items: [...]
gaps: []
```
<!-- END SCHEMA_SUMMARY_EXEMPLAR -->

### Strict Rules:
- If evidence is missing, set `status: evidence_gap`, declare `gaps: [{ step: "s1", need: "example", detail: "..." }]`, and leave the blocks of exactly those gap steps empty.
- When `status: ok`, `gaps: []` and no step has empty blocks.
- Inline markup: only `{{gloss:W-...}}` (for incidental words) and `{{uk:...}}` (for quoted terms in English).
- No combining accents (U+0300, U+0301).
## Form-choice candidate bank

Use one form from its bound record per option. State only the `requires` the sentence forces, not the key's features. If another reading fits (partitive genitive after request, offer, consumption or permission requests; genitive of negation; animate accusative/genitive syncretism), rewrite the context to force one reading or drop the item; never remove a `requires` group to repair it. A finite verb slot names `VerbForm: Fin` in `requires`; a plural slot omits `Gender` because plural forms carry no gender. Choose one admitted key. Each distractor must be a form that the sentence rules out by a feature the form itself carries. `tests_feature` names one focus group; the reviewer judges whether the distractors really make the learner choose along that focus. The engine generates the item-specific subset and checks every written option.

- `W-074`: `привіт` — noun:inanim:m:v_naz [Animacy=Inan, Case=Nom, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_zna [Animacy=Inan, Case=Acc, Gender=Masc, Number=Sing, upos=NOUN]
- `W-074`: `привітам` — noun:inanim:p:v_dav [Animacy=Inan, Case=Dat, Number=Plur, upos=NOUN]
- `W-074`: `привітами` — noun:inanim:p:v_oru [Animacy=Inan, Case=Ins, Number=Plur, upos=NOUN]
- `W-074`: `привітах` — noun:inanim:p:v_mis [Animacy=Inan, Case=Loc, Number=Plur, upos=NOUN]
- `W-074`: `привіте` — noun:inanim:m:v_kly [Animacy=Inan, Case=Voc, Gender=Masc, Number=Sing, upos=NOUN]
- `W-074`: `привіти` — noun:inanim:p:v_kly [Animacy=Inan, Case=Voc, Number=Plur, upos=NOUN]; noun:inanim:p:v_naz [Animacy=Inan, Case=Nom, Number=Plur, upos=NOUN]; noun:inanim:p:v_zna [Animacy=Inan, Case=Acc, Number=Plur, upos=NOUN]
- `W-074`: `привітові` — noun:inanim:m:v_dav [Animacy=Inan, Case=Dat, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_mis [Animacy=Inan, Case=Loc, Gender=Masc, Number=Sing, upos=NOUN]
- `W-074`: `привітом` — noun:inanim:m:v_oru [Animacy=Inan, Case=Ins, Gender=Masc, Number=Sing, upos=NOUN]
- `W-074`: `привіту` — noun:inanim:m:v_dav [Animacy=Inan, Case=Dat, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_mis [Animacy=Inan, Case=Loc, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_rod [Animacy=Inan, Case=Gen, Gender=Masc, Number=Sing, upos=NOUN]
- `W-074`: `привіті` — noun:inanim:m:v_mis [Animacy=Inan, Case=Loc, Gender=Masc, Number=Sing, upos=NOUN]
- `W-074`: `привітів` — noun:inanim:p:v_rod [Animacy=Inan, Case=Gen, Number=Plur, upos=NOUN]
- `W-075`: `добра` — adj:f:v_kly:compb [Case=Voc, Degree=Pos, Gender=Fem, Number=Sing, upos=ADJ]; adj:f:v_naz:compb [Case=Nom, Degree=Pos, Gender=Fem, Number=Sing, upos=ADJ]
- `W-075`: `добре` — adj:n:v_kly:compb [Case=Voc, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]; adj:n:v_naz:compb [Case=Nom, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]; adj:n:v_zna:compb [Case=Acc, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]
- `W-075`: `добрий` — adj:m:v_kly:compb [Case=Voc, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:m:v_naz:compb [Case=Nom, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:m:v_zna:rinanim:compb [Animacy=Inan, Case=Acc, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]
- `W-075`: `добрим` — adj:m:v_oru:compb [Case=Ins, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:n:v_oru:compb [Case=Ins, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]; adj:p:v_dav:compb [Case=Dat, Degree=Pos, Number=Plur, upos=ADJ]
- `W-075`: `добрими` — adj:p:v_oru:compb [Case=Ins, Degree=Pos, Number=Plur, upos=ADJ]
- `W-075`: `добрих` — adj:p:v_mis:compb [Case=Loc, Degree=Pos, Number=Plur, upos=ADJ]; adj:p:v_rod:compb [Case=Gen, Degree=Pos, Number=Plur, upos=ADJ]; adj:p:v_zna:ranim:compb [Animacy=Anim, Case=Acc, Degree=Pos, Number=Plur, upos=ADJ]
- `W-075`: `доброго` — adj:m:v_rod:compb [Case=Gen, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:m:v_zna:ranim:compb [Animacy=Anim, Case=Acc, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:n:v_rod:compb [Case=Gen, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]
- `W-075`: `доброму` — adj:m:v_dav:compb [Case=Dat, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:m:v_mis:compb [Case=Loc, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:n:v_dav:compb [Case=Dat, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]; adj:n:v_mis:compb [Case=Loc, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]
- `W-075`: `доброю` — adj:f:v_oru:compb [Case=Ins, Degree=Pos, Gender=Fem, Number=Sing, upos=ADJ]
- `W-075`: `доброї` — adj:f:v_rod:compb [Case=Gen, Degree=Pos, Gender=Fem, Number=Sing, upos=ADJ]
- `W-075`: `добру` — adj:f:v_zna:compb [Case=Acc, Degree=Pos, Gender=Fem, Number=Sing, upos=ADJ]
- `W-075`: `добрі` — adj:p:v_kly:compb [Case=Voc, Degree=Pos, Number=Plur, upos=ADJ]; adj:p:v_naz:compb [Case=Nom, Degree=Pos, Number=Plur, upos=ADJ]; adj:p:v_zna:rinanim:compb [Animacy=Inan, Case=Acc, Degree=Pos, Number=Plur, upos=ADJ]
- `W-075`: `добрій` — adj:f:v_dav:compb [Case=Dat, Degree=Pos, Gender=Fem, Number=Sing, upos=ADJ]; adj:f:v_mis:compb [Case=Loc, Degree=Pos, Gender=Fem, Number=Sing, upos=ADJ]
- `W-075`: `добрім` — adj:m:v_mis:compb [Case=Loc, Degree=Pos, Gender=Masc, Number=Sing, upos=ADJ]; adj:n:v_mis:compb [Case=Loc, Degree=Pos, Gender=Neut, Number=Sing, upos=ADJ]
- `W-076`: `день` — noun:inanim:m:v_naz [Animacy=Inan, Case=Nom, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_zna [Animacy=Inan, Case=Acc, Gender=Masc, Number=Sing, upos=NOUN]
- `W-076`: `дневі` — noun:inanim:m:v_dav [Animacy=Inan, Case=Dat, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_mis [Animacy=Inan, Case=Loc, Gender=Masc, Number=Sing, upos=NOUN]
- `W-076`: `днем` — noun:inanim:m:v_oru [Animacy=Inan, Case=Ins, Gender=Masc, Number=Sing, upos=NOUN]
- `W-076`: `дню` — noun:inanim:m:v_dav [Animacy=Inan, Case=Dat, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_kly [Animacy=Inan, Case=Voc, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:m:v_mis [Animacy=Inan, Case=Loc, Gender=Masc, Number=Sing, upos=NOUN]
- `W-076`: `дня` — noun:inanim:m:v_rod [Animacy=Inan, Case=Gen, Gender=Masc, Number=Sing, upos=NOUN]
- `W-076`: `дням` — noun:inanim:p:v_dav [Animacy=Inan, Case=Dat, Number=Plur, upos=NOUN]
- `W-076`: `днями` — noun:inanim:p:v_oru [Animacy=Inan, Case=Ins, Number=Plur, upos=NOUN]
- `W-076`: `днях` — noun:inanim:p:v_mis [Animacy=Inan, Case=Loc, Number=Plur, upos=NOUN]
- `W-076`: `дні` — noun:inanim:m:v_mis [Animacy=Inan, Case=Loc, Gender=Masc, Number=Sing, upos=NOUN]; noun:inanim:p:v_kly [Animacy=Inan, Case=Voc, Number=Plur, upos=NOUN]; noun:inanim:p:v_naz [Animacy=Inan, Case=Nom, Number=Plur, upos=NOUN]; noun:inanim:p:v_zna [Animacy=Inan, Case=Acc, Number=Plur, upos=NOUN]
- `W-076`: `днів` — noun:inanim:p:v_rod [Animacy=Inan, Case=Gen, Number=Plur, upos=NOUN]
- `W-091`: `Нін` — noun:anim:p:v_rod:prop:fname [Animacy=Anim, Case=Gen, Number=Plur, upos=PROPN]; noun:anim:p:v_zna:prop:fname [Animacy=Anim, Case=Acc, Number=Plur, upos=PROPN]
- `W-091`: `Ніна` — noun:anim:f:v_naz:prop:fname [Animacy=Anim, Case=Nom, Gender=Fem, Number=Sing, upos=PROPN]
- `W-091`: `Нінам` — noun:anim:p:v_dav:prop:fname [Animacy=Anim, Case=Dat, Number=Plur, upos=PROPN]
- `W-091`: `Нінами` — noun:anim:p:v_oru:prop:fname [Animacy=Anim, Case=Ins, Number=Plur, upos=PROPN]
- `W-091`: `Нінах` — noun:anim:p:v_mis:prop:fname [Animacy=Anim, Case=Loc, Number=Plur, upos=PROPN]
- `W-091`: `Ніни` — noun:anim:f:v_rod:prop:fname [Animacy=Anim, Case=Gen, Gender=Fem, Number=Sing, upos=PROPN]; noun:anim:p:v_kly:prop:fname [Animacy=Anim, Case=Voc, Number=Plur, upos=PROPN]; noun:anim:p:v_naz:prop:fname [Animacy=Anim, Case=Nom, Number=Plur, upos=PROPN]
- `W-091`: `Ніно` — noun:anim:f:v_kly:prop:fname [Animacy=Anim, Case=Voc, Gender=Fem, Number=Sing, upos=PROPN]
- `W-091`: `Ніною` — noun:anim:f:v_oru:prop:fname [Animacy=Anim, Case=Ins, Gender=Fem, Number=Sing, upos=PROPN]
- `W-091`: `Ніну` — noun:anim:f:v_zna:prop:fname [Animacy=Anim, Case=Acc, Gender=Fem, Number=Sing, upos=PROPN]
- `W-091`: `Ніні` — noun:anim:f:v_dav:prop:fname [Animacy=Anim, Case=Dat, Gender=Fem, Number=Sing, upos=PROPN]; noun:anim:f:v_mis:prop:fname [Animacy=Anim, Case=Loc, Gender=Fem, Number=Sing, upos=PROPN]
- `W-093`: `Іван` — noun:anim:m:v_naz:prop:fname [Animacy=Anim, Case=Nom, Gender=Masc, Number=Sing, upos=PROPN]
- `W-093`: `Івана` — noun:anim:m:v_rod:prop:fname [Animacy=Anim, Case=Gen, Gender=Masc, Number=Sing, upos=PROPN]; noun:anim:m:v_zna:prop:fname [Animacy=Anim, Case=Acc, Gender=Masc, Number=Sing, upos=PROPN]
- `W-093`: `Іванам` — noun:anim:p:v_dav:prop:fname [Animacy=Anim, Case=Dat, Number=Plur, upos=PROPN]
- `W-093`: `Іванами` — noun:anim:p:v_oru:prop:fname [Animacy=Anim, Case=Ins, Number=Plur, upos=PROPN]
- `W-093`: `Іванах` — noun:anim:p:v_mis:prop:fname [Animacy=Anim, Case=Loc, Number=Plur, upos=PROPN]
- `W-093`: `Іване` — noun:anim:m:v_kly:prop:fname [Animacy=Anim, Case=Voc, Gender=Masc, Number=Sing, upos=PROPN]
- `W-093`: `Івани` — noun:anim:p:v_kly:prop:fname [Animacy=Anim, Case=Voc, Number=Plur, upos=PROPN]; noun:anim:p:v_naz:prop:fname [Animacy=Anim, Case=Nom, Number=Plur, upos=PROPN]
- `W-093`: `Іванові` — noun:anim:m:v_dav:prop:fname [Animacy=Anim, Case=Dat, Gender=Masc, Number=Sing, upos=PROPN]; noun:anim:m:v_mis:prop:fname [Animacy=Anim, Case=Loc, Gender=Masc, Number=Sing, upos=PROPN]
- `W-093`: `Іваном` — noun:anim:m:v_oru:prop:fname [Animacy=Anim, Case=Ins, Gender=Masc, Number=Sing, upos=PROPN]
- `W-093`: `Івану` — noun:anim:m:v_dav:prop:fname [Animacy=Anim, Case=Dat, Gender=Masc, Number=Sing, upos=PROPN]; noun:anim:m:v_mis:prop:fname [Animacy=Anim, Case=Loc, Gender=Masc, Number=Sing, upos=PROPN]
- `W-093`: `Івані` — noun:anim:m:v_mis:prop:fname [Animacy=Anim, Case=Loc, Gender=Masc, Number=Sing, upos=PROPN]
- `W-093`: `Іванів` — noun:anim:p:v_rod:prop:fname [Animacy=Anim, Case=Gen, Number=Plur, upos=PROPN]; noun:anim:p:v_zna:prop:fname [Animacy=Anim, Case=Acc, Number=Plur, upos=PROPN]
