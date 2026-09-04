/**
 * Build-time key extraction for the "Curated Deck" (virtual_teacher_lesson)
 * practice filter (#7671).
 *
 * `src/data/lexicon-teacher-cloze.json` is the ~6.8MB raw teacher-cloze source.
 * custom-decks.ts used to import it directly just to compute the deduplicated,
 * privacy-filtered lemma key list — that statically bundled the entire raw
 * file into the client-only LexiconPractice island (the dominant share of its
 * ~5MB chunk), even though the actual cloze content is already served to the
 * browser separately, on demand, as the `practice-cloze.teacher.json` runtime
 * shard (see fetchPracticeDrillFields / getShardJson call sites).
 *
 * This script performs that same derivation once, at build time, and writes
 * the small (~60KB) result to `src/data/lexicon-teacher-lesson-keys.json`,
 * which custom-decks.ts imports instead. Re-run whenever
 * lexicon-teacher-cloze.json changes (wired into `npm run hydrate`).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { filterTeacherClozeItems } from '../src/lib/lexicon/teacher-cloze-filter.ts';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(scriptDir, '..');
const sourcePath = resolve(siteRoot, 'src/data/lexicon-teacher-cloze.json');
const outPath = resolve(siteRoot, 'src/data/lexicon-teacher-lesson-keys.json');

interface TeacherClozeItem {
  clozeId: string;
  lemmaId?: string;
  lemma?: string;
}

interface TeacherClozeSource {
  cloze?: TeacherClozeItem[];
}

function generate(): void {
  const raw = JSON.parse(readFileSync(sourcePath, 'utf8')) as TeacherClozeSource;
  const filtered = filterTeacherClozeItems(raw.cloze ?? []);
  const lemmas = Array.from(
    new Set(
      filtered
        .map((item) => item.lemmaId || item.lemma)
        .filter((key): key is string => Boolean(key)),
    ),
  );
  writeFileSync(outPath, `${JSON.stringify(lemmas)}\n`);
  console.log(`✓ ${lemmas.length} teacher-lesson lemma keys -> ${outPath}`);
}

generate();
