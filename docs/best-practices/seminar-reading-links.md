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

## Verified public archives (Ukrainian, free, #M-4 link-checked 2026-06-15)

| Archive | URL | Best for |
|---|---|---|
| **ukrlib «Народна творчість»** | `https://www.ukrlib.com.ua/narod/` | FOLK — full texts of every oral genre (казки, думи, легенди, пісні, колядки, веснянки, прислів'я, вертеп). Genre pages `book.php?id=N` — verified live 2026-06-15: веснянки=0, драматургія/вертеп=1, жниварські=2, історичні пісні/коломийки=3, колядки=5, колядки-й-щедрівки=6, народний епос/думи=11. |
| **ukrlib бібліотека** | `https://www.ukrlib.com.ua/books/` | LIT / LIT-* — full texts of Ukrainian literary works by author. |
| **Diasporiana** | `https://diasporiana.org.ua/` | All seminars — digitized diaspora/émigré editions preserved outside Soviet censorship. Category pages, incl. **Фольклор** `https://diasporiana.org.ua/category/folklor/` (252 items, verified live 2026-06-15). The verified replacement for the now-defunct Чтиво. |
| ~~**Чтиво**~~ **(DEFUNCT)** | ~~`https://chtyvo.org.ua/`~~ | ⛔ **CLOSED 2026-06-15** — the site published a closure notice ("після більш ніж 20 років… завершити роботу… сайт більше не буде активно підтримуватися") and no longer serves content. **Do NOT ship chtyvo.org.ua links anywhere.** Use Diasporiana / ukrlib / Вікіджерела instead. Repo-wide cleanup tracked — see "Defunct-archive sweep" below. |
| **Ізборник / Літопис** | `http://izbornyk.org.ua/` | HIST · ISTORIO · OES · RUTH — chronicles, Грушевський, medieval/early-modern sources. (HTTP only — verify per-link before shipping; HTTPS currently redirect-loops.) |
| **Вікіджерела (uk.wikisource)** | `https://uk.wikisource.org/` | LIT / FOLK — public-domain works. Verify exact page titles before shipping (category/page names vary; do NOT guess URLs). |

**Rule:** ship ONLY links you have verified live (HTTP 200, https preferred — browser-checked, not assumed).
Never ship a guessed URL — a broken "where to read" link is worse than none (#M-4). **The Чтиво closure
(discovered 2026-06-15 while re-verifying these links before shipping the folk module reading-links) is the
case in point: an archive listed + #M-4-checked on 2026-06-14 was dead the next day. Re-verify on every ship.**

## Per-track source registry (which archives each track points to)

- **folk** → ukrlib «Народна творчість» (primary; genre pages per the ID table above) + Diasporiana «Фольклор».
- **lit, lit-\*** → ukrlib бібліотека (the work) + Вікіджерела (public-domain) + Diasporiana.
- **hist, istorio** → Ізборник/Літопис + ukrlib козацькі літописи + Diasporiana.
- **oes, ruth** → Ізборник (chronicles, OES/Middle-Ukrainian texts) + Diasporiana.
- **bio** → Вікіпедія (subject) + ukrlib бібліотека (subject's own writings) + Diasporiana.

(Codify as `data/seminar_reading_sources.yaml` when the gate lands — one block per track + per genre/author.
That YAML is intentionally NOT created yet: it should be co-designed with the gate/assembler (#3120, infra
lane) so its schema matches the consumer. Until then THIS doc is the source of truth for verified URLs.)

### Defunct-archive sweep (Чтиво closure, 2026-06-15)

Чтиво (chtyvo.org.ua) closed 2026-06-15. It was referenced repo-wide (~26 files: this spec, bio plans,
research dossiers, session-state, resource backups). The folk lane is fixed in this PR (spec above + folk
landing + 3 module `resources.yaml` never used it / now use Diasporiana). The remaining cross-seminar
references (esp. `curriculum/l2-uk-en/plans/bio/*.yaml`, `docs/research/bio/*`, `docs/resources/external_resources.yaml*`)
are OTHER lanes — filed as a tracked follow-up for the infra/bio orchestrators. Do not ship any new
chtyvo.org.ua link.

## Making it mandatory (pipeline, not hand-edits)

Module-level reading links must be **generated + gated**, so every current and future seminar module
carries them automatically (hand-editing generated MDX does not scale and is overwritten on rebuild):

1. **Source registry** `data/seminar_reading_sources.yaml` — per track + per genre/author → verified URLs.
2. **Writer/assembler** injects a "Where to read" block into each seminar module's Resources from the
   registry (keyed by the module's genre/author).
3. **Gate** (`scripts/audit/` or the python_qg seminar path): a seminar module/landing **fails** if it
   has no reading-links section. This is what "mandatory" means operationally.
4. **Link-liveness check** (CI advisory): periodically `curl` the registry URLs; flag dead links.

## Rollout status (2026-06-15)

- ✅ **folk landing** — "Де читати ці тексти" section live (`site/src/content/docs/folk/index.mdx`). Exemplar.
  (NOTE: this section was added by #3119, then **dropped on main by `228f9ca180` "group curriculum track
  landings"** — a regression. **Restored** in this PR, minus the defunct Чтиво, plus Diasporiana.)
- ✅ **folk modules** (Resources) — **3 live modules done** (this PR): kalendarna, koliadky-shchedrivky,
  dumy-nevilnytski-lytsarski each carry genre-specific ukrlib genre pages + Diasporiana «Фольклор» as
  `role: article` reading-links (interim hand-add to `resources.yaml` + reassemble; verified gate-neutral —
  assemble + mdx_render green, no new vesum/plan failures). The remaining locked folk modules get reading
  links automatically when they are built (writer/assembler), or via the registry+gate.
- ⏳ **lit / lit-\*** (user priority) → then hist · istorio · bio · oes · ruth landings + modules.
- ⏳ **registry + gate** — the durable mandatory mechanism (epic). Until it lands the hand-add + this doc
  are the interim path; the proper fix is assembler-injection + a python_qg seminar gate (infra lane).
- ⛔ **Чтиво defunct** (2026-06-15) — repo-wide chtyvo.org.ua sweep filed for the cross-seminar lanes.

Tracked as a folk/seminar epic (see issue). Owner: seminar orchestrator (folk + all seminars lane).
