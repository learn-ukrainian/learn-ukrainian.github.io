# Хрестоматія — authoritative design POC (folk seminar)

**Status:** POC for review. Once blessed by the user, this is the *authoritative reference* for
(a) the Хрестоматія primary-sources section and (b) every reading content page. Build the real
astro implementation to match this; point new readings at this spec.

Open `index.html` (section landing) and `reading.html` (a reading page) in a browser. They are
self-contained and use the real site's dark-theme tokens + folk identity, so they translate 1:1.

---

## 1. What the Хрестоматія *is*
A **separate "anthology of primary sources" section**, parallel to the lessons — *course-looking*,
but **not** part of the numbered module ladder. It holds the **full original texts** that the
lessons teach from in excerpts.

- Lives **per seminar**, namespaced under the track: `/folk/readings/` (later `/lit/readings/`, etc.).
  This is the right model — each seminar gets its own Хрестоматія, not one global pile.
- Readings are **NOT numbered modules.** No `sidebar.order`, no "Урок N з 6", no "Module 50".
  (Root cause of the current bug: `/folk/readings/*` with `order:50` gets bucketed into the folk
  module sidebar. Fix = treat `folk/readings/**` as a distinct section, see §5.)

## 2. The excerpt ↔ full-text contract
- **Lesson body** keeps curated **excerpts** in a `:::primary-reading` box ("📜 Читаємо
  першоджерело") for close reading, **plus** a link: *"📖 Прочитати повністю →"* pointing to the
  Хрестоматія page.
- **Хрестоматія page** holds the **complete** original.
- **Hosting policy:** HOST on-site every text we *teach from* (from our verified PD corpus).
  Verified-external links (wikisource / ukrlib / litopys / osvita) only for *supplementary*
  breadth, behind the build-time URL-resolve gate. **Never an unchecked link.**
- **Huge works** (Eneida-scale): one Хрестоматія page **per part / canto**, grouped under the work.

## 3. Reading content page — required anatomy (`reading.html`)
1. **Hero eyebrow** = `📜 Хрестоматія · {genre}` — NOT "Module NN". H1 = work title; subtitle = "повний текст · {cycle}".
2. **"Як користуватися сторінкою" card** — states this is the full text; links back to the module.
3. **The primary text** in a verse container styled like `.primary-reading-box`, header
   "📜 Читаємо першоджерело", work title, then the text.
   - **Verse formatting:** clean lines via `white-space: pre-line` (the #3661/#3663 mechanism) —
     **no `<br/>`**. One `<blockquote>`/stanza block per stanza; blank line between stanzas.
   - Serif face, generous line-height (~1.85), bronze left-rule per stanza.
4. **Source / attribution block** — provenance ("за виданням …"), **public-domain** statement,
   and "подано дослівно за записом — архаїчні й діалектні форми збережено."
5. **Back link** — "← Повернутися до модуля «…»".

## 4. Section landing — required anatomy (`index.html`)
- Hero: eyebrow `📜 Хрестоматія · Першоджерела`, title "Хрестоматія народної творчості".
- "Що це за розділ" intro: explains excerpt-in-lesson / full-text-here, PD + verbatim policy.
- Readings grouped by **genre** (Думи · Колядки і щедрівки · Замовляння · Календарно-обрядові · …);
  each = a card (📜 icon, genre meta, title, one-line note, "Читати повністю →"). Planned texts
  show a muted "Заплановано" card so the structure is visible.

## 5. Navigation model (the sidebar)
- **On a Хрестоматія page** (landing or reading): left sidebar titled **"📜 Хрестоматія"**,
  back link **"← Уроки фольклору"**, readings listed by genre, counter **"N текстів"**
  (NOT "Урок N з M"). Active reading highlighted.
- **On a module page**: the existing numbered lesson sidebar gains **one distinct jump entry**
  **"📜 Хрестоматія"** (rendered separately from the numbered lessons, so the "Урок N з M" count
  is unaffected).
- Identity: Хрестоматія reuses the folk crimson→bronze hero but adds a **parchment accent**
  (`#E9D8A6`) + 📜 motif so it reads as "the source library," a sibling of the lessons.

## 6. Implementation map (when blessed → real astro build)
- `site/src/pages/[...slug].astro`: detect `folk/readings/**` → build the Хрестоматія sidebar from
  the readings bucket; exclude readings from the module bucket (fixes the "module 50" bug); add the
  module-page "📜 Хрестоматія" jump.
- `site/src/layouts/CourseLayout.astro`: optional `crossSection` link in the `Sidebar` type +
  parchment accent styling for the section.
- Content: `site/src/content/docs/folk/readings/index.mdx` (section landing) + one `*.mdx` per
  reading; migrate the existing `dumy-nevilnytski-lytsarski.mdx` reading (drop `order:50`, drop
  `<br/>` → clean blockquotes now that verse-CSS #3663 lands).
- Reuses the verse-CSS already merged in #3663 (`.primary-reading-content blockquote { white-space: pre-line }`).

## 7. Reference text used in the POC
«Дума про Марусю Богуславку» — full text, public domain (запис за М. Драгомановим), the worked
exemplar for the невільницькі-думи module. Corpus-verifiable; this is the same text as the parked
PR #3660 reading page, which folds into this section.
