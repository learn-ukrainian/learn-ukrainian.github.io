# Seminar reading-links — "Where to read the primary texts" (MANDATORY)

> **Policy (user, 2026-06-14):** Every **seminar track** MUST tell students *where they can read the
> actual primary texts* — folk tales, dumy, legends, myths, songs, literary works, chronicles. This is
> **mandatory for ALL seminars** (folk · hist · istorio · bio · lit · lit-* · oes · ruth), and
> *especially* for **lit / lit-\*** where reading the work itself is the point of the course.
>
> Rationale: a decolonized literature/folklore curriculum that quotes texts but never tells the learner
> where to *read* them is half a course. "How will students read them?" (user, Session 9) — this closes
> that gap permanently, not per-module by hand.

## Scope — two surfaces, both required

1. **Track landing page** — a "Де читати ці тексти · Where to read the texts" section linking the
   public archives appropriate to that track (see the per-track source registry below). Hand-added per
   landing (folk shipped first as the exemplar: `site/src/content/docs/folk/index.mdx`).
2. **Every module** — the module's **Resources** tab MUST carry work-specific reading links for the
   genre/author it covers (e.g. a dumy module → ukrlib «Народний епос»; a Шевченко lit module → the
   specific work on ukrlib/Чтиво/Вікіджерела). This is enforced via the **pipeline**, not by hand
   (see "Making it mandatory").

## Verified public archives (Ukrainian, free, #M-4 link-checked 2026-06-14)

| Archive | URL | Best for |
|---|---|---|
| **ukrlib «Народна творчість»** | `https://www.ukrlib.com.ua/narod/` | FOLK — full texts of every oral genre (казки, думи, легенди, пісні, колядки, веснянки, прислів'я, вертеп). Genre pages `book.php?id=N` (epos/думи=11, веснянки=0, історичні пісні/коломийки=3). |
| **ukrlib бібліотека** | `https://www.ukrlib.com.ua/books/` | LIT / LIT-* — full texts of Ukrainian literary works by author. |
| **Чтиво** | `https://chtyvo.org.ua/` | All seminars — digitized scholarly editions & collections (Гнатюк, Чубинський, Грінченко, academic series). |
| **Ізборник / Літопис** | `http://izbornyk.org.ua/` | HIST · ISTORIO · OES · RUTH — chronicles, Грушевський, medieval/early-modern sources. (HTTP only — verify per-link before shipping; HTTPS currently redirect-loops.) |
| **Вікіджерела (uk.wikisource)** | `https://uk.wikisource.org/` | LIT / FOLK — public-domain works. Verify exact page titles before shipping (category/page names vary; do NOT guess URLs). |

**Rule:** ship ONLY links you have `curl`-verified live (HTTP 200, https preferred). Never ship a guessed
URL — a broken "where to read" link is worse than none (#M-4).

## Per-track source registry (which archives each track points to)

- **folk** → ukrlib «Народна творчість» (primary) + Чтиво.
- **lit, lit-\*** → ukrlib бібліотека (the work) + Чтиво + Вікіджерела (public-domain).
- **hist, istorio** → Ізборник/Літопис + Чтиво + ukrlib козацькі літописи.
- **oes, ruth** → Ізборник (chronicles, OES/Middle-Ukrainian texts) + Чтиво.
- **bio** → Чтиво + Вікіпедія (subject) + ukrlib бібліотека (subject's own writings).

(Codify as `data/seminar_reading_sources.yaml` when the gate lands — one block per track + per genre/author.)

## Making it mandatory (pipeline, not hand-edits)

Module-level reading links must be **generated + gated**, so every current and future seminar module
carries them automatically (hand-editing generated MDX does not scale and is overwritten on rebuild):

1. **Source registry** `data/seminar_reading_sources.yaml` — per track + per genre/author → verified URLs.
2. **Writer/assembler** injects a "Where to read" block into each seminar module's Resources from the
   registry (keyed by the module's genre/author).
3. **Gate** (`scripts/audit/` or the python_qg seminar path): a seminar module/landing **fails** if it
   has no reading-links section. This is what "mandatory" means operationally.
4. **Link-liveness check** (CI advisory): periodically `curl` the registry URLs; flag dead links.

## Rollout status (2026-06-14)

- ✅ **folk landing** — reading-links section live (`site/src/content/docs/folk/index.mdx`). Exemplar.
- ⏳ **folk modules** (Resources) — via the registry+gate, or interim hand-add to the 3 live modules'
  `resources.yaml` + reassemble.
- ⏳ **lit / lit-\*** (user priority) → then hist · istorio · bio · oes · ruth landings + modules.
- ⏳ **registry + gate** — the durable mandatory mechanism (epic).

Tracked as a folk/seminar epic (see issue). Owner: seminar orchestrator (folk + all seminars lane).
