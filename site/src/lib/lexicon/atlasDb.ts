import Database from 'better-sqlite3';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

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
    const payloadRows = db
      .prepare(
        `SELECT slug, payload_json
         FROM article_payloads
         WHERE is_public_route = 1
         ORDER BY route_order`,
      )
      .all() as PayloadRow[];
    const metadataRows = db
      .prepare(
        `SELECT key, value_json
         FROM manifest_metadata
         WHERE key IN ('generated_at', 'version')`,
      )
      .all() as MetadataRow[];
    const entries = payloadRows.map((row) => JSON.parse(row.payload_json) as LexiconEntry);
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
