/**
 * SQLite Atlas data source — Node SSG / parity baseline.
 *
 * Reads the same ``article_payloads.payload_json`` + ``articles.entry_type``
 * projection the live renderer uses today, then attaches aliases, relations,
 * provenance, and renderContext to match the versioned EntryRecord contract.
 */

import Database from "better-sqlite3";
import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import {
  buildComponentLinkTargets,
  getAtlasPayloadCache,
  resetAtlasPayloadCacheForTests,
  type LexiconEntry,
} from "./atlasDb";
import {
  AtlasDataSourceError,
  isValidAtlasSlug,
  type ArticleProvenance,
  type AtlasDataSource,
  type DeckPart,
  type DeckResult,
  type EntryRecord,
  type EntryResult,
  type PublicAlias,
  type PublicRelation,
  type SearchResponse,
} from "./atlas-data-source";
import { normalizeAtlasText } from "./normalize";
import { PRACTICE_LEVELS, type PracticeLevel } from "./runtime-contract";
import { rankSearchResults, type SearchAlias, type SearchRow } from "./search";
import type { PracticeDeckData } from "./srs";

const COMPONENT_TOKEN_RE = /[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu;
const MORPHOLOGY_SUPPRESSED = new Set([
  "multiword_term",
  "expression",
  "phraseologism",
  "proverb",
]);

type BetterSqliteDatabase = InstanceType<typeof Database>;

function atlasDbPath(): string {
  return process.env.ATLAS_DB_PATH || resolve(process.cwd(), "../data/atlas.db");
}

function openDb(): BetterSqliteDatabase {
  const dbPath = atlasDbPath();
  if (!existsSync(dbPath)) {
    throw new AtlasDataSourceError("unavailable", `Atlas DB not found at ${dbPath}`);
  }
  return new Database(dbPath, { readonly: true, fileMustExist: true });
}

function loadPracticeLevelsBySlug(): Map<string, PracticeLevel[]> {
  const levelsBySlug = new Map<string, Set<PracticeLevel>>();
  const dbDir = dirname(atlasDbPath());
  for (const level of PRACTICE_LEVELS) {
    const candidates = [
      resolve(dbDir, `../site/public/lexicon/practice-index.${level}.json`),
      resolve(dbDir, `../site/public/api/lexicon/practice-index.${level}.json`),
    ];
    for (const path of candidates) {
      if (!existsSync(path)) continue;
      try {
        const payload = JSON.parse(readFileSync(path, "utf-8")) as {
          items?: Array<{ lemmaId?: string; lemma?: string }>;
        };
        for (const item of payload.items ?? []) {
          for (const key of [item.lemmaId, item.lemma]) {
            if (!key) continue;
            const set = levelsBySlug.get(key) ?? new Set<PracticeLevel>();
            set.add(level);
            levelsBySlug.set(key, set);
          }
        }
        break;
      } catch {
        // ignore unreadable practice index
      }
    }
  }
  const out = new Map<string, PracticeLevel[]>();
  for (const [slug, set] of levelsBySlug) {
    out.set(slug, [...set].sort());
  }
  return out;
}

function componentLinksForEntry(
  entry: LexiconEntry,
  componentTargets: Map<string, string>,
  lemmaSlugs: Set<string>,
): Array<{ text: string; targetSlug: string | null }> {
  if (!MORPHOLOGY_SUPPRESSED.has(entry.entry_type ?? "")) return [];
  const tokens = entry.lemma.match(COMPONENT_TOKEN_RE) ?? [];
  return tokens.map((text) => {
    const targetSlug = componentTargets.get(normalizeAtlasText(text));
    if (targetSlug && lemmaSlugs.has(targetSlug) && targetSlug !== entry.url_slug) {
      return { text, targetSlug };
    }
    return { text, targetSlug: null };
  });
}

function assertCefrConsistent(slug: string, articleCefr: string | null, entry: LexiconEntry): void {
  const enrichment = entry.enrichment as { cefr?: { level?: string } } | null | undefined;
  const payloadCefr = enrichment?.cefr?.level?.trim() || null;
  const left = articleCefr?.trim() || null;
  const right = payloadCefr;
  if (left && right && left.toUpperCase() !== right.toUpperCase()) {
    throw new AtlasDataSourceError(
      "integrity_error",
      `CEFR conflict for slug=${JSON.stringify(slug)}: articles.cefr=${JSON.stringify(left)} enrichment.cefr=${JSON.stringify(right)}`,
    );
  }
}

export class SqliteAtlasDataSource implements AtlasDataSource {
  private readonly version: string;
  private readonly recordsBySlug: Map<string, EntryRecord>;
  private readonly articleRows: SearchRow[];
  private readonly aliasRows: SearchAlias[];
  private readonly deckDir: string;

  constructor(options?: { version?: string; deckDir?: string }) {
    const cache = getAtlasPayloadCache();
    this.version = options?.version ?? `sqlite-${cache.manifestVersion}`;
    this.deckDir =
      options?.deckDir ??
      resolve(dirname(atlasDbPath()), "../site/public/lexicon");

    const db = openDb();
    try {
      const practiceLevels = loadPracticeLevelsBySlug();
      const componentArticleRows = db
        .prepare(
          `SELECT display_head AS lookup_text, slug AS target_slug
           FROM articles
           WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'
           ORDER BY display_head COLLATE NOCASE, slug`,
        )
        .all() as Array<{ lookup_text: string; target_slug: string }>;
      const componentAliasRows = db
        .prepare(
          `SELECT al.alias AS lookup_text, al.target_slug AS target_slug
           FROM aliases al
           JOIN articles a ON a.slug = al.target_slug
           WHERE al.visibility = 'public'
             AND a.review_state = 'approved'
             AND a.visibility = 'public'
             AND a.entry_type = 'lemma'
           ORDER BY al.alias COLLATE NOCASE, al.target_slug, al.kind`,
        )
        .all() as Array<{ lookup_text: string; target_slug: string }>;
      const componentTargets = buildComponentLinkTargets(componentArticleRows, componentAliasRows);
      const lemmaSlugs = new Set(
        (
          db
            .prepare(
              `SELECT slug FROM articles
               WHERE review_state = 'approved' AND visibility = 'public' AND entry_type = 'lemma'`,
            )
            .all() as Array<{ slug: string }>
        ).map((row) => row.slug),
      );

      const aliasesBySlug = new Map<string, PublicAlias[]>();
      for (const row of db
        .prepare(
          `SELECT alias, kind, source, target_slug
           FROM aliases
           WHERE visibility = 'public'
           ORDER BY target_slug, kind, alias, source`,
        )
        .all() as PublicAlias[]) {
        const list = aliasesBySlug.get(row.target_slug) ?? [];
        list.push(row);
        aliasesBySlug.set(row.target_slug, list);
      }

      const relationsBySlug = new Map<string, PublicRelation[]>();
      for (const row of db
        .prepare(
          `SELECT related_slug, entry_type, relation, component_role, provenance, slug
           FROM related_entries
           ORDER BY slug, relation, related_slug, provenance, component_role`,
        )
        .all() as Array<PublicRelation & { slug: string }>) {
        const list = relationsBySlug.get(row.slug) ?? [];
        list.push({
          related_slug: row.related_slug,
          entry_type: row.entry_type,
          relation: row.relation,
          component_role: row.component_role,
          provenance: row.provenance,
        });
        relationsBySlug.set(row.slug, list);
      }

      const provenanceBySlug = new Map<string, ArticleProvenance[]>();
      for (const row of db
        .prepare(
          `SELECT slug, source_family, source_locator, extraction_mode
           FROM article_provenance
           ORDER BY slug, rowid`,
        )
        .all() as Array<ArticleProvenance & { slug: string }>) {
        const list = provenanceBySlug.get(row.slug) ?? [];
        list.push({
          source_family: row.source_family,
          source_locator: row.source_locator,
          extraction_mode: row.extraction_mode,
        });
        provenanceBySlug.set(row.slug, list);
      }

      const cefrBySlug = new Map(
        (
          db.prepare(`SELECT slug, cefr FROM articles`).all() as Array<{
            slug: string;
            cefr: string | null;
          }>
        ).map((row) => [row.slug, row.cefr]),
      );

      this.recordsBySlug = new Map();
      for (const entry of cache.entries) {
        const slug = entry.url_slug;
        assertCefrConsistent(slug, cefrBySlug.get(slug) ?? null, entry);
        const kind = entry.entry_type == null ? "form_route" : "article";
        const practice =
          practiceLevels.get(slug) ?? practiceLevels.get(entry.lemma) ?? [];
        this.recordsBySlug.set(slug, {
          slug,
          kind,
          entry,
          aliases: aliasesBySlug.get(slug) ?? [],
          relations: relationsBySlug.get(slug) ?? [],
          provenance: provenanceBySlug.get(slug) ?? [],
          renderContext: {
            componentLinks: componentLinksForEntry(entry, componentTargets, lemmaSlugs),
            practiceLevels: practice,
          },
        });
      }

      // Prefer the dual-publication search artifacts so ranking matches the
      // legacy generate_search_index / exporter transliteration surface.
      const searchIndexPath = resolve(process.cwd(), "src/data/lexicon-search-index.json");
      const searchAliasesPath = resolve(process.cwd(), "src/data/lexicon-search-aliases.json");
      if (existsSync(searchIndexPath) && existsSync(searchAliasesPath)) {
        this.articleRows = JSON.parse(readFileSync(searchIndexPath, "utf-8")) as SearchRow[];
        this.aliasRows = JSON.parse(readFileSync(searchAliasesPath, "utf-8")) as SearchAlias[];
      } else {
        this.articleRows = (
          db
            .prepare(
              `SELECT slug, display_head, gloss, entry_type, cefr
               FROM articles
               WHERE review_state = 'approved' AND visibility = 'public'
               ORDER BY display_head COLLATE NOCASE, slug`,
            )
            .all() as Array<{
            slug: string;
            display_head: string;
            gloss: string | null;
            entry_type: string;
            cefr: string | null;
          }>
        ).map((row) => {
          const out: SearchRow = {
            l: row.display_head,
            s: row.slug,
            g: row.gloss?.trim() || null,
            r: row.display_head,
            t: row.entry_type,
          };
          if (row.cefr?.trim()) out.c = row.cefr.trim();
          return out;
        });
        this.aliasRows = [];
        const seen = new Set<string>();
        for (const row of db
          .prepare(
            `SELECT alias.alias AS a, alias.kind AS k, alias.target_slug AS s, article.display_head AS h
             FROM aliases AS alias
             JOIN articles AS article ON article.slug = alias.target_slug
             WHERE alias.visibility = 'public'
               AND article.review_state = 'approved'
               AND article.visibility = 'public'
             ORDER BY alias.alias COLLATE NOCASE, alias.target_slug, alias.kind`,
          )
          .all() as SearchAlias[]) {
          const key = `${normalizeAtlasText(row.a)}\0${row.s}`;
          if (!normalizeAtlasText(row.a) || seen.has(key)) continue;
          seen.add(key);
          this.aliasRows.push(row);
        }
      }
    } finally {
      db.close();
    }
  }

  async getEntry(slug: string, options?: { expectedVersion?: string }): Promise<EntryResult> {
    if (!isValidAtlasSlug(slug)) {
      throw new AtlasDataSourceError("invalid_slug", `invalid slug: ${JSON.stringify(slug)}`);
    }
    if (options?.expectedVersion && options.expectedVersion !== this.version) {
      throw new AtlasDataSourceError(
        "version_mismatch",
        `expected ${options.expectedVersion}, have ${this.version}`,
      );
    }
    const record = this.recordsBySlug.get(slug);
    if (!record) return { kind: "missing", version: this.version, slug };
    return { kind: "entry", version: this.version, record };
  }

  async search(
    query: string,
    options?: { limit?: number; expectedVersion?: string },
  ): Promise<SearchResponse> {
    if (options?.expectedVersion && options.expectedVersion !== this.version) {
      throw new AtlasDataSourceError(
        "version_mismatch",
        `expected ${options.expectedVersion}, have ${this.version}`,
      );
    }
    const limit = options?.limit ?? 12;
    const normalizedQuery = normalizeAtlasText(query);
    const results = rankSearchResults(this.articleRows, this.aliasRows, query, limit + 1);
    const truncated = results.length > limit;
    return {
      version: this.version,
      normalizedQuery,
      results: results.slice(0, limit),
      truncated,
      fetchedShardIds: ["sqlite:articles", "sqlite:aliases"],
    };
  }

  async getDeck(
    level: PracticeLevel,
    options?: { parts?: DeckPart[]; expectedVersion?: string },
  ): Promise<DeckResult> {
    if (options?.expectedVersion && options.expectedVersion !== this.version) {
      throw new AtlasDataSourceError(
        "version_mismatch",
        `expected ${options.expectedVersion}, have ${this.version}`,
      );
    }
    const parts = options?.parts ?? (["index", "lexemes", "cloze"] as DeckPart[]);
    const loaded: Partial<Record<DeckPart, unknown>> = {};
    const deckVersions = new Set<string>();
    for (const part of parts) {
      const path = resolve(this.deckDir, `practice-${part}.${level}.json`);
      if (!existsSync(path)) {
        return { kind: "missing", version: this.version, level };
      }
      const payload = JSON.parse(readFileSync(path, "utf-8")) as {
        deckVersion?: string;
        items?: PracticeDeckData["index"];
        lexemes?: PracticeDeckData["lexemes"];
        cloze?: PracticeDeckData["cloze"];
      };
      if (typeof payload.deckVersion === "string" && payload.deckVersion) {
        deckVersions.add(payload.deckVersion);
      }
      loaded[part] = payload;
    }
    if (deckVersions.size !== 1) {
      throw new AtlasDataSourceError(
        "integrity_error",
        `deck parts for ${level} must share one deckVersion, got ${[...deckVersions].sort().join(",")}`,
      );
    }
    const deckVersion = [...deckVersions][0]!;
    const indexPart = loaded.index as
      | { items?: PracticeDeckData["index"]; deckVersion?: string }
      | undefined;
    const lexemesPart = loaded.lexemes as
      | { lexemes?: PracticeDeckData["lexemes"]; deckVersion?: string }
      | undefined;
    const clozePart = loaded.cloze as
      | { cloze?: PracticeDeckData["cloze"]; deckVersion?: string }
      | undefined;
    const data: PracticeDeckData = {
      deckVersion,
      level,
      index: indexPart?.items ?? [],
      lexemes: lexemesPart?.lexemes ?? [],
      cloze: clozePart?.cloze ?? [],
    };
    return { kind: "deck", version: this.version, deckVersion, level, data };
  }
}

export function resetSqliteAtlasDataSourceCachesForTests(): void {
  resetAtlasPayloadCacheForTests();
}
