# Style Guide — for Human Editors

> A plain-language reference for anyone writing, reviewing, or correcting
> module content. Keep it short — this is a card you can read in 10
> minutes. If something isn't here, default to
> `docs/best-practices/module-content-quality.md`.

---

## 1. Tone and voice

Write like a patient Ukrainian teacher who has taught adults for 20 years
and doesn't need to prove anything. Warm, factual, specific. **Never**
bubbly, never condescending, never "fun!" for its own sake.

- **Say it once, say it clearly.** No repeating the same point with
  different wording.
- **Show, then explain.** Lead with a Ukrainian example, then the rule,
  then a second example. Not the other way around.
- **The learner is an adult.** Don't apologize for difficulty. Don't
  hand-hold. Trust them to look up what they don't know.
- **Avoid "let's" and "we'll".** Use the imperative or the plain
  indicative: "Прочитайте речення" not "Давайте разом прочитаємо…"
- **No filler phrases**: "як бачимо", "зверніть увагу", "цікаво, що",
  "варто зазначити". If the reader's attention doesn't hold without
  these, the content is weak — fix that, don't paper over it.

---

## 2. Formatting conventions

| What | How |
|------|-----|
| Section headings | `##` and `###` in Markdown. H2 for major sections, H3 for subsections. |
| Ukrainian words in prose | Unquoted, italicized only when introducing a new term or contrasting forms. |
| English glosses | In parentheses immediately after: *кіт* (cat). Lowercase unless it's a proper noun. |
| Tables | Use for declension, conjugation, minimal pairs — not for flowing prose. |
| Callouts | Use `> **Примітка:**` for side notes; reserve for genuinely important asides, not decoration. |
| Dialogue | One speaker per line, dash prefix: `— Привіт! — Доброго дня.` Name in bold if multiple speakers matter. |
| Word counts | Each H2 section should roughly hit its word target. Total module must meet level minimum (A1=1200, A2=2000, B1–C1=4000, C2=5000). |

---

## 3. Ukrainian orthography

**Правопис 2019** is the governing standard. When the old and new rules
disagree, use the 2019 form.

- **ий / ій in proper nouns**: Афіни, Мадрид, Сингапур, Чилі, Ітака —
  Правопис 2019 forms.
- **пів- / пів apart**: *пів години* (written apart when a separate word
  follows), *півмісяця* (together in compounds).
- **і / и after sibilants in imported words**: *хобі*, *ситі* — use
  current Правопис rules, not the 1993 version.
- **Апостроф**: after б, п, в, м, ф, р before я, ю, є, ї:
  *м'який*, *п'ять*, *ім'я*.
- **Ґ**: write where etymologically justified (ґрунт, ґудзик, Гоголь →
  Гоголь with г), and per Правопис 2019 proper names.
- **Doubling of consonants**: only in genuine Ukrainian forms
  (*зілля*, *обличчя*, *знання*). Don't copy Russian doubling rules.

When in doubt, **check VESUM first** (`data/vesum.db` or vesum.com.ua).
If VESUM disagrees with your gut, VESUM wins.

---

## 4. Decolonization in plain language

The curriculum treats Ukrainian as a full, independent literary and
living language with its own history — not as a dialect of Russian, not
as a post-Soviet variant, not as something that became interesting in
2022.

Concretely:

- **Primary sources are Ukrainian.** Literary examples from Shevchenko,
  Франко, Українка, Тичина, Стус, Жадан — not Russian translations or
  Soviet anthologies.
- **Historical framing is Ukrainian-centered.** Кийвська Русь is not
  "early Russia". Галицько-Волинське князівство and Гетьманщина get
  equal airtime to dynastic rulers. Голодомор is named and dated.
- **Anti-Russianism checks are separate from anti-Surzhyk checks.** A
  Russianism is a Russian word grafted into Ukrainian (*кот* → *кіт*,
  *хорошо* → *добре*); Surzhyk is an L1-contact pidgin (*шо* → *що*);
  a calque is a literal translation (*приймати участь* → *брати участь*).
  All three are different problems. All three must be caught.
- **Geographic names in Ukrainian.** *Київ*, not *Kiev*. *Харків*, not
  *Kharkov*. *Одеса*, one *с*. *Крим*, one *м*.
- **Don't neutralize.** If the content is about war, occupation, or
  resistance, name it directly. Avoid "conflict", "situation", "events" —
  these are euphemisms imported from Russian propaganda framing.

---

## 5. Exercise format

Activities are defined in YAML (`activities/{slug}.yaml`) and rendered
by React components. For editing purposes:

- **Questions must test language skill**, not content recall. "У якому
  році…" is wrong; "Згідно з текстом, як автор описує…" is right. The
  rule of thumb: could the learner answer without reading the Ukrainian?
  If yes, rewrite.
- **Fill-in blanks**: one blank per sentence, no parenthetical hints
  like `(магазин)` at the end. Use a separate `hint` field if needed.
- **Quiz options**: 4 options, no duplicates, one unambiguously correct
  answer. Distractors should be plausible (same part of speech, same
  register), not obviously wrong.
- **Match-up pairs**: exactly as many left-column items as right-column;
  each pair is 1:1, never 1:many.

Full rules: `docs/best-practices/vocabulary-activity-standards.md`.

---

## 6. When you're unsure

1. **Check VESUM** first — does this word form actually exist?
2. **Check goroh.pp.ua** — stress, frequency, historical forms.
3. **Check Антоненко-Давидович «Як ми говоримо»** — is this a calque?
4. **Ask a native speaker** — Teacher Tetiana or Teacher Alona on the
   project, or post in GH issues.
5. **Flag, don't invent.** Mark the questionable passage with
   `<!-- VERIFY: <what you're unsure about> -->`. The pipeline strips
   these before publish; a native reviewer resolves them.

**Never** guess a word form, a stress mark, or a case ending. Your
intuition is contaminated by Russian. VESUM is your source of truth.

---

## 7. Before you submit an edit

- [ ] The paragraph reads out loud naturally. Read it aloud. If you
      stumble, rewrite.
- [ ] No Russianisms, no calques, no Surzhyk, no paronym mix-ups.
- [ ] Стрес marks are NOT added by hand — the annotator adds them
      automatically after review.
- [ ] Any new word is in VESUM, or flagged.
- [ ] Activities still test language skill, not content recall.
- [ ] You didn't touch the plan YAML — plans are immutable without
      maintainer approval (see `docs/best-practices/track-architecture.md`).

---

_Maintained by the learn-ukrainian project. If something in this guide
is wrong or unclear, open an issue — it will get fixed in the next pass._
