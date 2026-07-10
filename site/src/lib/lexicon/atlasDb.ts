import Database from 'better-sqlite3';
import { existsSync, readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';

export interface CourseUsage {
  track: string;
  module_num: number;
  slug: string;
  context: string;
}

export interface LexiconEntry {
  lemma: string;
  url_slug: string;
  gloss: string | null;
  // entry_type is the article-record kind from `articles.entry_type`
  // (lemma | expression | phraseologism | proverb | multiword_term | proper_name).
  // Payloads themselves do not carry it, so it is joined on read from the
  // `articles` table. `form_of` alias routes have no article row → null.
  entry_type?: string | null;
  form_of?: { lemma: string; url_slug: string } | null;
  pos?: string | null;
  ipa?: string | null;
  pronunciation?: { ipa: string; source: string } | null;
  primary_source?: string;
  course_usage?: CourseUsage[];
  sections?: unknown;
  enrichment?: unknown;
  heritage_status?: unknown;
  wiki_reference?: unknown;
}

interface PayloadRow {
  slug: string;
  payload_json: string;
  entry_type: string | null;
}

interface MetadataRow {
  key: string;
  value_json: string;
}

export interface AtlasPayloadCache {
  entries: LexiconEntry[];
  bySlug: Map<string, LexiconEntry>;
  generatedAt: string;
  manifestVersion: string;
}

const defaultDbPath = resolve(process.cwd(), '../data/atlas.db');
let cachedAtlasPayloads: AtlasPayloadCache | null = null;

function atlasDbPath(): string {
  return process.env.ATLAS_DB_PATH || defaultDbPath;
}

function parseMetadata(rows: MetadataRow[]): { generatedAt: string; manifestVersion: string } {
  const metadata = new Map(rows.map((row) => [row.key, JSON.parse(row.value_json) as unknown]));
  return {
    generatedAt: String(metadata.get('generated_at') ?? ''),
    manifestVersion: String(metadata.get('version') ?? ''),
  };
}

export function resetAtlasPayloadCacheForTests(): void {
  cachedAtlasPayloads = null;
  _practiceLemmasCache = null;
}

type BetterSqliteDatabase = InstanceType<typeof Database>;

export interface EntryModelGateCounts {
  reviewedEntries: number;
  publicRoutes: number;
  formOfRoutes: number;
  aliasRecords: number;
}

export const ATLAS_ENTRY_TYPES = [
  "lemma",
  "expression",
  "phraseologism",
  "proverb",
  "multiword_term",
  "proper_name",
] as const;

export interface AtlasEntryModelCounts {
  reviewed_entries_by_type: Record<(typeof ATLAS_ENTRY_TYPES)[number], number>;
  total_reviewed_entries: number;
  alias_records: number;
  candidate_evidence_count: number;
  candidate_evidence_by_bucket: Record<string, number>;
  noise_rejected: number;
}

/**
 * Site-build assertions for the two DB-enforced entry-model gates
 * (`docs/runbooks/word-atlas-entry-model.md` § Acceptance Gates). These mirror
 * the DB builder's checks (`scripts/atlas/atlas_db.py`) so a bad `atlas.db`
 * fails the Astro build loudly instead of silently shipping inflated counts or
 * dangling aliases. Wording is kept identical to the deterministic gates.
 *
 * - `article_vs_alias_count`: `form_of` and alias records do not increment
 *   reviewed entry totals.
 * - `alias_target_integrity`: every public alias `target_slug` resolves to an
 *   approved public article.
 */
export function runEntryModelGates(db: BetterSqliteDatabase): EntryModelGateCounts {
  const scalar = (sql: string): number => (db.prepare(sql).get() as { n: number }).n;

  // article_vs_alias_count — reviewed entries are the approved+public `articles`
  // rows only. `form_of` alias routes (no `articles` row) and `aliases` records
  // must be excluded, so the reviewed total must equal the public routes minus
  // the form_of routes, and must equal the routes that join an approved+public
  // article. Any drift means an alias/form_of record has leaked into the totals.
  const reviewedEntries = scalar(
    `SELECT COUNT(*) AS n FROM articles WHERE review_state = 'approved' AND visibility = 'public'`,
  );
  const publicRoutes = scalar(`SELECT COUNT(*) AS n FROM article_payloads WHERE is_public_route = 1`);
  const formOfRoutes = scalar(
    `SELECT COUNT(*) AS n FROM article_payloads ap
     LEFT JOIN articles a ON a.slug = ap.slug
     WHERE ap.is_public_route = 1 AND a.slug IS NULL`,
  );
  const routedReviewed = scalar(
    `SELECT COUNT(*) AS n FROM article_payloads ap
     JOIN articles a ON a.slug = ap.slug
     WHERE ap.is_public_route = 1 AND a.review_state = 'approved' AND a.visibility = 'public'`,
  );
  const aliasRecords = scalar(`SELECT COUNT(*) AS n FROM aliases`);

  if (reviewedEntries !== publicRoutes - formOfRoutes || reviewedEntries !== routedReviewed) {
    throw new Error(
      `article_vs_alias_count failure: form_of and alias records must not increment reviewed entry totals — ` +
        `reviewed entries=${reviewedEntries}, public routes=${publicRoutes}, form_of routes=${formOfRoutes} ` +
        `(public - form_of = ${publicRoutes - formOfRoutes}), routed approved-public articles=${routedReviewed}`,
    );
  }

  // alias_target_integrity — mirrors scripts/atlas/atlas_db.py::validate_alias_targets.
  const failures = db
    .prepare(
      `SELECT al.alias AS alias, al.kind AS kind, al.target_slug AS target_slug,
              a.review_state AS review_state, a.visibility AS visibility
       FROM aliases al
       LEFT JOIN articles a ON a.slug = al.target_slug
       WHERE al.visibility = 'public'
         AND (a.slug IS NULL OR a.review_state != 'approved' OR a.visibility != 'public')
       ORDER BY al.target_slug, al.kind, al.alias`,
    )
    .all() as Array<{
    alias: string;
    kind: string;
    target_slug: string;
    review_state: string | null;
    visibility: string | null;
  }>;

  if (failures.length > 0) {
    for (const row of failures) {
      const reason =
        row.review_state === null
          ? 'missing target article'
          : row.review_state !== 'approved'
            ? `target review_state=${JSON.stringify(row.review_state)}`
            : `target visibility=${JSON.stringify(row.visibility)}`;
      console.error(
        `alias_target_integrity failure: alias=${JSON.stringify(row.alias)} ` +
          `kind=${JSON.stringify(row.kind)} target_slug=${JSON.stringify(row.target_slug)} reason=${reason}`,
      );
    }
    throw new Error(`${failures.length} alias target(s) are not approved public articles`);
  }

  return { reviewedEntries, publicRoutes, formOfRoutes, aliasRecords };
}

/** Return public-safe entry-model aggregates from the Atlas database. */
export function getAtlasEntryModelCounts(): AtlasEntryModelCounts {
  const dbPath = atlasDbPath();
  if (!existsSync(dbPath)) {
    throw new Error(`Atlas DB not found at ${dbPath}; site status cannot be generated.`);
  }

  const db = new Database(dbPath, { readonly: true, fileMustExist: true });
  try {
    const gates = runEntryModelGates(db);
    const counts = Object.fromEntries(
      ATLAS_ENTRY_TYPES.map((entryType) => [entryType, 0]),
    ) as AtlasEntryModelCounts["reviewed_entries_by_type"];
    const rows = db
      .prepare(
        `SELECT entry_type, COUNT(*) AS n
         FROM articles
         WHERE review_state = 'approved' AND visibility = 'public'
         GROUP BY entry_type`,
      )
      .all() as Array<{ entry_type: (typeof ATLAS_ENTRY_TYPES)[number]; n: number }>;
    for (const row of rows) counts[row.entry_type] = row.n;

    const aliasRecords = (
      db.prepare(`SELECT COUNT(*) AS n FROM aliases WHERE visibility = 'public'`).get() as { n: number }
    ).n;

    // v1 persists only approved articles and approved aliases. Candidate
    // evidence has no normalized table yet, so publish an explicit empty
    // aggregate rather than mislabelling legacy manifest routes as evidence.
    return {
      reviewed_entries_by_type: counts,
      total_reviewed_entries: gates.reviewedEntries,
      alias_records: aliasRecords,
      candidate_evidence_count: 0,
      candidate_evidence_by_bucket: {},
      noise_rejected: 0,
    };
  } finally {
    db.close();
  }
}

export function getAtlasPayloadCache(): AtlasPayloadCache {
  if (cachedAtlasPayloads) return cachedAtlasPayloads;

  const dbPath = atlasDbPath();
  if (!existsSync(dbPath)) {
    throw new Error(
      `Atlas DB not found at ${dbPath}. Run \`npm --prefix site run hydrate\` or ` +
        `\`.venv/bin/python -m scripts.atlas.atlas_db --db data/atlas.db\` before building the site.`,
    );
  }

  const db = new Database(dbPath, { readonly: true, fileMustExist: true });
  try {
    // Fail the build loudly on entry-model gate violations before reading rows.
    runEntryModelGates(db);

    const payloadRows = db
      .prepare(
        `SELECT ap.slug AS slug, ap.payload_json AS payload_json, a.entry_type AS entry_type
         FROM article_payloads ap
         LEFT JOIN articles a ON a.slug = ap.slug
         WHERE ap.is_public_route = 1
         ORDER BY ap.route_order`,
      )
      .all() as PayloadRow[];
    const metadataRows = db
      .prepare(
        `SELECT key, value_json
         FROM manifest_metadata
         WHERE key IN ('generated_at', 'version')`,
      )
      .all() as MetadataRow[];
    const entries = payloadRows.map((row) => {
      const entry = JSON.parse(row.payload_json) as LexiconEntry;
      // entry_type is authoritative from the `articles` table (SSOT), not the
      // payload JSON. `form_of` alias routes have no article row → null.
      entry.entry_type = row.entry_type ?? null;
      return entry;
    });
    const bySlug = new Map<string, LexiconEntry>();
    for (const entry of entries) {
      bySlug.set(entry.url_slug, entry);
    }
    cachedAtlasPayloads = {
      entries,
      bySlug,
      ...parseMetadata(metadataRows),
    };
    return cachedAtlasPayloads;
  } finally {
    db.close();
  }
}

export function getLexiconEntryBySlug(slug: string): LexiconEntry | undefined {
  return getAtlasPayloadCache().bySlug.get(slug);
}

let _practiceLemmasCache: Set<string> | null = null;

export function getPracticeLemmas(): Set<string> {
  if (_practiceLemmasCache) return _practiceLemmasCache;
  const lemmas = new Set<string>();
  const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
  const dbDir = dirname(atlasDbPath());
  let resolvedAny = false;

  for (const level of levels) {
    const paths = [
      resolve(dbDir, `../site/public/api/lexicon/practice-index.${level}.json`),
      resolve(dbDir, `../site/public/lexicon/practice-index.${level}.json`),
    ];
    for (const p of paths) {
      if (existsSync(p)) {
        try {
          const content = JSON.parse(readFileSync(p, 'utf-8'));
          if (content && Array.isArray(content.items)) {
            for (const item of content.items) {
              if (item.lemmaId) {
                lemmas.add(item.lemmaId);
              }
            }
          }
          resolvedAny = true;
          break;
        } catch (e) {
          // ignore parsing/reading errors
        }
      }
    }
  }

  if (!resolvedAny) {
    console.warn(`Warning: getPracticeLemmas failed to resolve any practice-index files. Checked paths relative to ${dbDir}`);
  }

  _practiceLemmasCache = lemmas;
  return lemmas;
}
