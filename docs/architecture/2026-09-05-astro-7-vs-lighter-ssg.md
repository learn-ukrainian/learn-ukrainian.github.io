---
title: "Astro 7 versus lighter static generators"
date: 2026-09-05
status: evaluation — recommendation only
scope: "#4387; learner lessons, Word Atlas, Practice Hub; documentation only"
---

# Astro 7 versus lighter static generators

**Recommendation: stay-and-optimize Astro 7.** Eleventy and Hugo can host static
lessons, data-driven dictionary templates, and a browser React application.
Neither demonstrates a lighter, faster, easier-to-maintain replacement for this
repository's **complete generated-MDX contract**. Eleventy's smaller core package
is measurable; a whole-product improvement is not. Keep Option A from the
[accepted ADR](2026-06-09-ui-astro-without-starlight.md). This evaluation exercises
the operator's 2026-09-05 GO to reconsider Option B; it does not approve or
implement a migration.

## Failure modes that decide the recommendation

- Generic MDX support does not implement Astro hydration directives, `.astro`
  components, content-collection validation, or publication filtering. Rendering
  static activity markup without working controls is a failed migration.
- One dictionary template can still emit thousands of HTML files. Replacing the
  SSG does not remove that output cost. There are **zero lexicon MDX files** in
  the measured content tree; there is no 256k-MDX problem to solve.
- A static Practice page still downloads and runs its React application. Removing
  Astro does not eliminate those application bytes, persistence, or startup work.
- A shell build omits Atlas article prerendering. Comparing its time or size to
  another framework's full catalog would produce an invalid recommendation.
- The published-input snapshot measured here has **20,121 manifest entries**,
  not 256k. The requested approximately 256k-entry dictionary and thousands of
  lessons are target denominators, not completed scale tests.

## Measurement boundary and raw results

All local commands ran in the assigned
`.worktrees/dispatch/codex/eval-ui-migrate-or-optimize` worktree at source commit
`f4f47584683b1897c71af3294295ae4dcd2abbb5` on 2026-09-05. Node was
`v24.19.0`, npm `9.2.0`; the Pages workflow uses Node `22`. These are local,
single-run observations, not CI medians or browser network measurements.

| Measurement | Raw result | Interpretation |
| --- | --- | --- |
| `site/package.json` Astro range / lockfile | `^7.2.4` / `7.2.4` | Current learner framework |
| Official configured integrations | MDX `7.0.7`, React `6.0.4`, sitemap `3.7.3` | Three official integrations |
| Local integrations | `raw-atlas-preview-adapter`, `goatcounter-analytics` | Two additional integration objects; preview adapter is conditional |
| Starlight runtime dependency | `false` | Alias to local tabs remains |
| Direct dependencies / dev dependencies / lock package entries | `20 / 9 / 734` | Lock count includes optional/platform packages; not browser weight |
| Non-MDX hydration mounts | `4` in `4` files, `3` component names | `only: 3`, `load: 1` |
| MDX hydration mounts | `4328` in `377` files, `33` component names | `only: 4307`, `load: 21` |
| Docs MDX / non-index lesson MDX / lexicon MDX | `377 / 356 / 0` | Source census, not hydrated instances per visit |
| Lessons by track | A1 `55`, A2 `69`, B1 `94`, B2 `93`, BIO `5`, FOLK `40` | All 356 fall within the full-lesson collection globs; later route filters still apply |
| Verified release manifest | `20121` entries; gzip `28030067` bytes; JSON `203539688` bytes | Pinned release input, not SQLite row count or rendered article count |
| `npm run build:shell --prefix site` | `427 page(s) built in 1m 23s`; exit `0` | Atlas article paths disabled; no full publisher timing |
| Shell output | `608` files, `428` HTML files, `71628179` bytes | File census includes emitted redirect/static files; differs from Astro's page counter |
| Practice component chunk | `329171` raw bytes; `90842` gzip bytes | Built `LexiconPractice.SJ6PLyj4.js` |
| Initial Practice island JS dependency closure | `20` files; `626194` raw bytes; `188043` summed gzip bytes | Component + renderer + static imports; excludes dynamic imports, CSS, HTML, data requests and inline bootstrap |
| Pages size check on shell output | `PASS`; failure threshold `858993459` bytes | Does not certify a full Atlas deployment |

The island census counts uppercase JSX/Astro component opening tags containing
`client:only/load/idle/visible/media`, excluding comments and test files. Repeated
mounts across lessons share compiled components; 4,328 is not 4,328 distinct
bundles. The four non-MDX mounts are `LevelLanding`, `LexiconPractice`, and
`WordAtlasClientShell` at two sites (article route and 404).

### Reproduce the source census

Run from the worktree root. The exact shared interpreter is required for this
checkout; do not create a worktree virtual environment.

```bash
node --version
npm --version
git rev-parse HEAD
node -e 'const p=require("./site/package.json"),l=require("./site/package-lock.json"); console.log(p.dependencies,p.devDependencies,Object.keys(l.packages).length-1)'
.venv/bin/python - <<'PY'
from pathlib import Path
from collections import Counter
import re
root = Path('site/src')
files = [p for p in root.rglob('*')
         if p.suffix in ('.astro', '.mdx', '.tsx', '.jsx')
         and '__tests__' not in p.parts and '.test.' not in p.name]
for name, subset in [('non-MDX', [p for p in files if p.suffix != '.mdx']),
                     ('MDX', [p for p in files if p.suffix == '.mdx'])]:
    counts, tags, matched = Counter(), set(), 0
    for p in subset:
        text = re.sub(r'<!--.*?-->|/\*.*?\*/', '', p.read_text(), flags=re.S)
        hits = re.findall(
            r'<([A-Z][\w.]*)\b[^>]*?\bclient:(only|load|idle|visible|media)\b',
            text, re.S)
        matched += bool(hits)
        for tag, directive in hits:
            counts[directive] += 1
            tags.add(tag)
    print(name, sum(counts.values()), matched, len(tags), dict(counts))
mdx = list((root / 'content/docs').rglob('*.mdx'))
lessons = [p for p in mdx if p.stem != 'index']
print('docs, lessons, lexicon', len(mdx), len(lessons),
      sum('lexicon' in p.parts for p in mdx))
print(dict(sorted(Counter(p.parent.name for p in lessons).items())))
PY
```

Manifest measurement fetched `asset_url` from
`site/src/data/lexicon-manifest.pointer.json`, verified both recorded SHA-256
values, decompressed it, and counted `entries`; it did not query Postgres,
modify the atlas lease, or regenerate source data. Reproduction:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import gzip, hashlib, json, urllib.request
p = json.loads(Path('site/src/data/lexicon-manifest.pointer.json').read_text())
b = urllib.request.urlopen(p['asset_url'], timeout=40).read()
assert hashlib.sha256(b).hexdigest() == p['gz_sha256']
raw = gzip.decompress(b)
assert hashlib.sha256(raw).hexdigest() == p['json_sha256']
print(len(json.loads(raw)['entries']), len(b), len(raw))
PY
```

### Build and initial Practice bytes

```bash
npm ci --prefix site --ignore-scripts --no-audit --no-fund
PYTHON=.venv/bin/python npm run build:shell --prefix site
DEPLOY_PROFILE=github-pages .venv/bin/python scripts/deploy/check_site_size.py site/dist
```

Installation reported `added 645 packages in 9s`; it warned that npm `9.2.0` is
below sitemap's declared npm `>=10.8.2`. Install scripts were disabled for this
shell-only measurement; no native SQLite build is claimed. The artifact verifier
also emitted a stale manifest-fingerprint warning (`expected undefined`) while
exiting successfully. Treat that warning as unresolved verification behavior,
not evidence that a manifest publish is required. No publisher build was run.

This command measures the **actual built island**, following static ES-module
imports rather than flattening deferred decks into its initial payload:

```bash
node --input-type=module <<'JS'
import {readFileSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {gzipSync} from 'node:zlib';
import {init, parse} from './site/node_modules/es-module-lexer/dist/lexer.js';
await init;
const html = readFileSync('site/dist/words-of-the-day/practice/index.html', 'utf8');
const island = html.match(/<astro-island\b[^>]*LexiconPractice[^>]*>/)[0];
const roots = [...island.matchAll(/(?:component-url|renderer-url)="([^"]+)"/g)];
const seen = new Set();
function walk(p) {
  if (seen.has(p)) return;
  seen.add(p);
  for (const i of parse(readFileSync(p, 'utf8'))[0])
    if (i.d === -1 && i.n?.startsWith('.')) walk(resolve(dirname(p), i.n));
}
for (const [, url] of roots) walk(resolve('site/dist', url.replace(/^\//, '')));
let raw = 0, gzip = 0;
for (const p of seen) {
  const b = readFileSync(p);
  raw += b.length;
  gzip += gzipSync(b).length;
  if (p.includes('LexiconPractice')) console.log('component', b.length, gzipSync(b).length);
}
console.log('initial closure', seen.size, raw, gzip);
JS
```

Gzip is Node's default compression, summed per file, not observed CDN transfer.
The result is a shell-build baseline with no browser timing or full-deployment
claim. An isolated esbuild probe that flattened dynamic imports produced much
larger output; it was rejected as an initial-load comparison because
`ZnoPractice.tsx` already imports its decks dynamically.

## How the three learner surfaces work today

**Lessons:** `scripts/generate_mdx/core.py` combines curriculum prose, activities,
and metadata into `site/src/content/docs/<track>/<slug>.mdx`. It emits `@site`
component imports, `client:only="react"` activities, and the legacy
`@astrojs/starlight/components` import. `site/astro.config.mjs` resolves that
last import to `src/starlight-compat/index.ts`, which exports local
`Tabs.astro` and `TabItem.astro`. It configures the Markdown/MDX processing
pipeline, including directives, admonitions, GFM, vocabulary links and Mermaid.
`src/content.config.ts` uses `glob`-loaded Astro collections plus Zod schemas;
`src/pages/[...slug].astro` uses `getCollection`, filters publication/routes,
and calls `render(entry)`. The readings collection separately enforces
public-domain metadata for published readings. A replacement must preserve
these semantics, not merely accept an `.mdx` extension.

**Word Atlas:** `src/pages/lexicon/[lemma].astro` is one template over
`EntryRecord`, not one MDX source per entry. `buildAtlasStaticPaths()` returns
`[]` in shell mode. Publisher scripts hydrate `data/atlas.db` and set
`ATLAS_STATIC_ROUTES=1`; the helper then enumerates the pinned
`SqliteAtlasDataSource` catalog and retains a paths array containing records.
The source prepares `recordsBySlug`; the awaited loop is not proof of one SQL
query per route. The template renders `WordAtlasPageShell` for available records;
client-shell recovery uses static projections and the 404 route. Preserving that
fallback does not turn GitHub Pages into an application server or make missing
article URLs return HTTP 200. A 256k-entry data catalog is feasible separately
from deciding how many full article HTML files to prerender.

**Practice Hub:** `/words-of-the-day/practice/` wraps `LexiconPracticeMount.astro`
in `CourseLayout`. The mount renders a loading shell and
`<LexiconPractice client:only="react" />`, plus startup/failure handling. The React
application owns session controls and browser persistence. The old
`/lexicon/practice` path has a static redirect. Another SSG can host the same
React bundle, but needs an explicit mounting entry, CSS handling, base URLs,
loading/failure behavior, and preserved storage/session semantics. SSG speed and
Practice interaction latency are separate measurements.

**Pages:** `.github/workflows/deploy-pages.yml` builds under `./site` with
`npm ci` and `npm run build`, optionally vendors a pinned Atlas runtime tree,
runs `check_site_size.py`, uploads `./site/dist`, and uses `actions/deploy-pages`.
Pushes to main go through the automatic eligibility check; manual dispatch is
also supported. Any replacement must retain this static artifact contract,
route/asset compatibility, certification rules, and size gate. Historical ADR
references to `starlight/` and an unused Starlight npm dependency are superseded
by this measured `site/` snapshot.

## Two concrete lighter candidates

| Requirement | Eleventy 3.1.6 | Hugo |
| --- | --- | --- |
| Thousands of lessons | File-based templates/collections and documented MDX integration; thousands of this project's lessons not benchmarked | Markdown/templates supported; thousands of this project's lessons not benchmarked |
| Dictionary templates loading data | JavaScript data + pagination can emit one page per record; alternatively copy static shards and mount a shell | Content adapters (`_content.gotmpl`, `AddPage`) generate pages from data; alternatively static shards + shell |
| SQLite source | Build-time JS can adapt the existing SQLite source; no runtime database on Pages | Export pinned SQLite data to JSON for templates; additional build step |
| Practice | React mounting script, with optional `is-land` scheduling | Bundle React/TSX using `js.Build` and an explicit mounting script |
| Pages | Static output; configure output as `dist` or adapt artifact path | Official Pages deployment guide; configure destination to preserve `site/dist` |
| Existing generated MDX unchanged | **Fails the tested stock integration** on `@site/src`; aliases, `.astro` tabs, hydration and collection behavior still need adapters | **No native MDX renderer** in documented supported formats; requires a Node MDX prepass plus the same compatibility work |
| Measured lighter/faster/easier as a complete replacement | Smaller core package; no complete-product speed or maintenance win established | No complete-product weight/speed win measured; retaining Node MDX/React removes the single-toolchain simplicity argument |

Eleventy's [official MDX recipe](https://www.11ty.dev/docs/languages/mdx/)
uses `@mdx-js/mdx` evaluation and React server rendering. A local Eleventy
`3.1.6` probe registered that recipe with ESM, `baseUrl`, and frontmatter support,
and supplied the unchanged generated `a1/this-and-that.mdx` as its sole input:

```text
node batch_state/eval-ui/eleventy-probe.mjs
Cannot find package '@site/src' imported from .../@mdx-js/mdx/lib/run.js
Wrote 0 files in 0.25 seconds (v3.1.6)
```

To reproduce the probe without changing the learner source, install Eleventy
under ignored scratch and save this as
`batch_state/eval-ui/eleventy-probe.mjs`, then run the command above:

```bash
npm install --prefix batch_state/eval-ui/eleventy --ignore-scripts --no-audit --no-fund @11ty/eleventy@3.1.6
```

```javascript
import Eleventy from './eleventy/node_modules/@11ty/eleventy/src/Eleventy.js';
import {evaluate} from '../../site/node_modules/@mdx-js/mdx/index.js';
import {renderToStaticMarkup} from '../../site/node_modules/react-dom/server.node.js';
import * as runtime from '../../site/node_modules/react/jsx-runtime.js';
import {readFileSync, mkdirSync, writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const dir = 'batch_state/eval-ui/eleventy-input';
mkdirSync(dir, {recursive: true});
writeFileSync(dir + '/lesson.mdx',
  readFileSync('site/src/content/docs/a1/this-and-that.mdx', 'utf8'));
const app = new Eleventy(dir, 'batch_state/eval-ui/eleventy-output', {
  configPath: false,
  config(c) {
    c.addTemplateFormats('mdx');
    c.addExtension('mdx', {
      compile: async (str, inputPath) => {
        const {default: Content} = await evaluate(str, {
          ...runtime, baseUrl: pathToFileURL(inputPath),
        });
        return async data => renderToStaticMarkup(await Content(data));
      },
    });
  },
});
try { await app.write(); }
catch (e) { console.log('probe failed:', e.originalError?.message || e.message); }
```

The probe catches and prints the error; its process exit status is not a success
criterion. The semantic result is zero rendered files and the import failure.
This is a concrete adapter failure, not a claim that Eleventy cannot support
MDX. Adding an alias would only resolve the first failure; the local Astro tabs
and hydration directives remain. Its [pagination](https://www.11ty.dev/docs/pagination/),
[custom template extensions](https://www.11ty.dev/docs/languages/custom/),
[partial hydration](https://www.11ty.dev/docs/plugins/is-land/), and
[deployment](https://www.11ty.dev/docs/deployment/) documentation establish the
mechanisms for data pages and browser islands, not full-scale parity here.

Hugo's [supported content formats](https://gohugo.io/content-management/formats/)
do not include MDX. Its [content adapters](https://gohugo.io/content-management/content-adapters/)
avoid per-entry source files, [js.Build](https://gohugo.io/functions/js/build/)
supports TSX/JSX bundling, and its
[Pages guide](https://gohugo.io/host-and-deploy/host-on-github-pages/) establishes
static deployment. These support a possible adapter-based design; they do not
prove preservation of the generated Astro MDX pipeline. Hugo was not installed
or timed in this evaluation; no version-specific performance claim is made.

Core package comparison, fetched from the npm registry on the evaluation date:

```bash
npm view @11ty/eleventy@3.1.6 version dist.unpackedSize --json
# version: 3.1.6; dist.unpackedSize: 540231
npm view astro@7.2.4 version dist.unpackedSize --json
# version: 7.2.4; dist.unpackedSize: 3003327
```

Those are individual unpacked package bytes, excluding dependencies, MDX/React,
plugins and browser output. They justify investigating Eleventy, not migrating.
There is no equal-workload candidate-versus-Astro build benchmark, so this note
makes **no claim that Astro is faster**. Staying preserves a working integration
while the required migration advantage remains unproven.

## Prioritized optimizations — recommendations, not changes in this PR

1. **Measure and reduce initial Practice work.** Use the 626,194-byte initial JS
   closure as the baseline; profile optional activity/mode imports and session
   startup before changing them. Keep the existing deferred ZNO decks deferred.
   Measure cold/warm usable interaction, including CSS/data and failures. Preserve
   storage compatibility and the loading/failure shell. Coordinate future work
   with Practice PR #7691; this evaluation changes none of its files.
2. **Profile full Atlas preparation, rendering and output separately.** Measure
   peak memory for the prepared record map plus paths array, full-route build
   time, and complete Pages bytes including vendored shards. Evaluate compact
   data delivery and duplicated public assets before blaming MDX or an SSG.
   Do not change prerender/SEO semantics on shell-only size evidence. The current
   size report's extrapolation from one lexicon page is not a 256k-entry proof.
3. **Profile generated lesson compilation and hydration.** Inspect the broad
   generated import preamble; narrow it only with component-use and output-parity
   evidence. Test SSR-compatible components for delayed hydration where useful,
   preserving readable content, accessibility, activity behavior and A1 English
   scaffolding. Do not mechanically replace all `client:only` directives.
4. **Clean historical names and verification ambiguity.** Rename root
   `build:starlight`, `build:starlight:full`, `dev:starlight` and the site's package
   name in a separately scoped cleanup with callers updated. There is no unused
   Starlight runtime to remove. Investigate the fingerprint warning without
   republishing artifacts merely because this shell verifier printed it.

No learner UI, generator, Practice TS, teacher-cloze script, definition sources,
or data publication policy changes are included. Public Ukrainian definitions
remain СУМ-20 + ВТС; no conjugation-grid export is proposed.

## Completion and residual evidence

The delivered outcome is this comparison covering **three learner surfaces,
two replacement candidates, and the static deploy/generated-MDX constraints**.
It is not a migration prototype or a 256k-entry capacity certification. The local
shell build and size gate passed; generated-source census and built-island bytes
were measured. A separate read-only critic checked coupling and warned against
shell/full comparisons and flattening deferred bundles; that same-family input
is not cross-family PR approval. Exact-head cross-family review and CI belong to
the PR, with merge owned by the accountable #4387 orchestrator.

The #4387 owner retains the residual: full catalog/lesson-scale performance and
browser-interaction parity are unmeasured. Before a later migration recommendation,
freeze the workload and candidate versions, use identical output policy and
hardware, and compare repeated cold/warm builds, peak memory, complete deploy
bytes, initial network bytes and usable Practice latency. An independent reviewer
must select held-out lessons covering tabs/activities/diagrams and exercise Atlas
Unicode/alias/deep links plus Practice resume and failure paths. Broken controls,
publication-policy drift, missing routes, incompatible generated MDX, or the
existing Pages size gate failing stops that candidate; do not lower those gates.
Only a demonstrated product-level advantage with those checks intact can change
this recommendation. No future benchmark or migration phase is dispatched here.
