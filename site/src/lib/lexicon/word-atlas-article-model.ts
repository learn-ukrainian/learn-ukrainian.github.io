/**
 * View-model helpers for WordAtlasArticle (shared by the React port).
 * Logic lifted from the former WordAtlasArticle.astro frontmatter.
 */

import {
  resolveHeritageBoxes,
  type WarningSeverity,
} from "./heritage-severity";
import {
  dominantMarkerLabel,
  isFullyMarkedLemma,
  morphologyFormCountLabel,
  registerBadgeLabel,
} from "./register-markers";
import { pluralizeUk } from "../i18n/plural";
import type { EntryRecord } from "./atlas-data-source";
import { safeHref } from "./safe-url";
import { formatOrigin, type FormattedOrigin } from "./format-origin";

export interface DefinitionCard {
  id: string;
  source: string;
  source_pill?: string;
  note?: string;
  definitions: string[];
  source_url?: string;
  sovietization_risk?: number;
  sovietization_keywords?: string[];
  flag_note?: string;
}

export interface SourcedText {
  text: string;
  source: string;
  stages?: Array<{ period: string; word: string; note?: string }>;
}

export interface SynonymGloss {
  text: string;
}

export interface SynonymMember {
  lemma: string;
  stressed: string;
  gloss?: SynonymGloss;
}

export interface SynonymSet {
  id: number;
  pos?: string;
  gloss?: SynonymGloss;
  members: SynonymMember[];
}

export interface NounParadigm {
  kind: "noun";
  cases: Record<string, { singular: string; plural: string }>;
}

export interface VerbParadigm {
  kind: "verb";
  infinitive?: string;
  tenses?: Record<string, Record<string, Record<string, string>>>;
  imperative?: Record<string, Record<string, string>>;
  past?: Record<string, string>;
  impersonal?: string;
}

export interface ParticipleParadigm {
  kind: "participle";
  voice: "active" | "passive";
  aspect: "perfective" | "imperfective";
  verb?: string;
  verb_url_slug?: string;
}

export type MorphologyParadigm = NounParadigm | VerbParadigm | ParticipleParadigm | { kind: "other" };

export interface EnrichmentExample {
  uk: string;
  en: string;
  source: string;
  locator?: string;
}

export interface Enrichment {
  stress?: { form: string; source: string };
  cefr?: { level: string; source: string; text?: string; pos?: string };
  morphology?: {
    pos: string;
    form_count: number;
    forms: Array<{ form: string; label: string; stress?: string }>;
    paradigm?: MorphologyParadigm;
    stress?: { source: string; forms: Record<string, string> };
    source: string;
    marked_forms?: Array<{
      form: string;
      label: string;
      marker: string;
      marker_label: string;
      stress?: string;
    }>;
    marked_form_count?: number;
  };
  meaning?: {
    definitions: string[];
    source: string;
    synonyms?: string[];
    note?: string;
    sovietization_risk?: number;
    sovietization_keywords?: string[];
  };
  definition_cards?: DefinitionCard[];
  etymology?: SourcedText;
  literary_attestation?: {
    text: string;
    source: string;
    source_label?: string;
    chunk_id?: string;
    source_url?: string;
  };
  translation?: { en: string[]; source: string; pos?: string };
  examples?: EnrichmentExample[];
  /** Verb pedagogy strip (#7471): aspect, aspect partner, present/future
   * stems, and case government -- rendered as a short summary, never a
   * conjugation table (VESUM Морфологія owns that). */
  verb_pedagogy?: {
    aspect?: "imperfective" | "perfective";
    aspect_partner?: { lemma: string; url_slug?: string; source: string };
    stems?: { present_future: string[]; source: string; locator?: string };
    government?: Array<{ label: string; source: string; locator?: string }>;
  };
  sources?: string[];
  textbooks?: Array<{ title: string; text?: string; tag?: string; url?: string }>;
  external_materials?: Array<{
    group?: string;
    title: string;
    description?: string;
    tag?: string;
    url?: string;
    kind?: string;
  }>;
}

export interface HeritageAttestation {
  source: string;
  ref: string;
  detail?: string;
}

export interface CuratedCalque {
  kind: "participle" | "phrasal" | "sense_restricted";
  corrections: string[];
  note: string;
  source: string[];
  calque_sense?: string;
  authentic_sense?: string;
}

export interface ReverseCalque {
  calque: string;
  kind: "participle" | "phrasal" | "sense_restricted";
  note: string;
  source: string[];
  calque_sense?: string;
}

export interface HeritageStatus {
  classification: string;
  attestations: HeritageAttestation[];
  is_russianism: boolean;
  russian_shadow: boolean;
  warning_severity?: WarningSeverity;
  vesum_attested?: boolean;
  calque_warning?: { detail?: string; standard_alternatives?: string[] } | null;
  curated_calque?: CuratedCalque | null;
  "§6_note"?: {
    corrections: string[];
    note: string;
    source: string[];
    citation?: string;
  } | null;
  reverse_calques?: ReverseCalque[] | null;
}

export interface LexiconSections {
  synonyms?: { items: string[]; source: string; source_urls?: string[]; synsets?: SynonymSet[] };
  antonyms?: { items: string[]; source: string; source_urls?: string[] };
  homonyms?: {
    items: Array<{ word: string; gloss: string; pos?: string; homonym_no?: number }>;
    source: string;
    source_urls?: string[];
  };
  paronyms?: {
    items: Array<{ word: string; distinction?: string; exam_provenance?: string[] }>;
    source: string;
    source_urls?: string[];
  };
  idioms?: {
    items: Array<{
      text?: string;
      phrase: string;
      definition: string;
      source: string;
      source_url?: string;
    }>;
    source: string;
    source_urls?: string[];
  };
  proverbs?: {
    items: Array<{
      text: string;
      gloss?: string;
      source: string;
      source_url?: string;
    }>;
    source: string;
    source_urls?: string[];
  };
  /** Davydov-family usage / style-norm essays (#6463 davydov; #6460 linguistic_norm, khreshchatyk; voloschak/foreign_shtepa full notes when corrective). */
  usage_notes?: {
    items: Array<{
      title?: string;
      text: string;
      source: string;
      source_url?: string;
    }>;
    source: string;
    source_urls?: string[];
  };
  /** Compact orthography/Holoskevych/orthoepy form strip (#6465). */
  form_notes?: {
    items: Array<{
      dictionary: "orthography" | "holoskevych" | "orthoepy";
      text: string;
      source: string;
      source_url?: string;
    }>;
    source: string;
    source_urls?: string[];
  };
}

export interface CourseUsage {
  track: string;
  module_num: number;
  slug: string;
  context: string;
}

export interface LexiconEntryView {
  lemma: string;
  url_slug: string;
  gloss: string | null;
  entry_type?: string | null;
  form_of?: { lemma: string; url_slug: string } | null;
  pos: string | null;
  ipa: string | null;
  pronunciation?: { ipa: string; source: string } | null;
  primary_source: string;
  course_usage: CourseUsage[];
  sections?: LexiconSections | null;
  enrichment?: Enrichment | null;
  heritage_status?: HeritageStatus | null;
  wiki_reference?: {
    wikipedia?: { title: string; summary: string; url: string };
    wiktionary_url?: string;
    wikisource_url?: string | null;
    attribution: string;
  } | null;
}

/** Minimal canonical article shape needed for learner-facing Atlas backlinks. */
export interface AtlasLinkCatalogEntry {
  slug: string;
  lemma: string;
  entry_type?: string | null;
  pos?: string | null;
  gloss?: string | null;
  /** Producer-verified gerund parent; never derived from the entry spelling. */
  gerund_parent?: string | null;
  enrichment?: Pick<Enrichment, "morphology"> | null;
}

export interface AtlasLinkCatalogAlias {
  alias: string;
  target_slug: string;
}

/** Injectable catalog keeps link resolution unit-testable without opening atlas.db. */
export interface AtlasLinkCatalog {
  entries: readonly AtlasLinkCatalogEntry[];
  aliases?: readonly AtlasLinkCatalogAlias[];
}

export interface ParticipleLink {
  lemma: string;
  slug: string;
}

export interface GerundLink {
  lemma: string;
  slug: string;
}

export const CASE_ROWS = [
  { key: "називний", label: "Називний" },
  { key: "родовий", label: "Родовий" },
  { key: "давальний", label: "Давальний" },
  { key: "знахідний", label: "Знахідний" },
  { key: "орудний", label: "Орудний" },
  { key: "місцевий", label: "Місцевий" },
  { key: "кличний", label: "Кличний" },
] as const;

export const PERSON_ROWS = [
  { key: "1", label: "1 особа" },
  { key: "2", label: "2 особа" },
  { key: "3", label: "3 особа" },
] as const;

export const IMPERATIVE_ROWS = [
  { key: "2-singular", label: "2 особа", number: "однина", person: "2" },
  { key: "1-plural", label: "1 особа (мн.)", number: "множина", person: "1" },
  { key: "2-plural", label: "2 особа (мн.)", number: "множина", person: "2" },
] as const;

export const PAST_ROWS = [
  { key: "чол.", label: "чол." },
  { key: "жін.", label: "жін." },
  { key: "сер.", label: "сер." },
  { key: "множина", label: "множина" },
] as const;

/**
 * Format a past form with conditional particle «би / б» (named construction, #7608).
 * Standard Ukrainian orthography: after vowels -> «б», after consonants -> «би».
 */
export function formatConditionalForm(pastForm: string | undefined | null): string {
  if (!pastForm?.trim()) return "";
  return pastForm
    .split(" / ")
    .map((variant) => {
      const trimmed = variant.trim();
      if (!trimmed) return "";
      const clean = trimmed.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      const lastChar = clean.slice(-1).toLowerCase();
      const isVowel = /[аеєиіїоуюя]/.test(lastChar);
      return `${trimmed} ${isVowel ? "б" : "би"}`;
    })
    .filter(Boolean)
    .join(" / ");
}

/**
 * Format 3rd person imperative construction: «(не)хай» + 3sg/3pl present (#7608).
 */
export function formatKhayImperative(form: string | undefined | null): string {
  if (!form?.trim()) return "";
  return form
    .split(" / ")
    .map((variant) => {
      const trimmed = variant.trim();
      if (!trimmed) return "";
      return `(не)хай ${trimmed}`;
    })
    .filter(Boolean)
    .join(" / ");
}

const BUDU_FORMS = {
  однина: { "1": "буду", "2": "будеш", "3": "буде" },
  множина: { "1": "будемо", "2": "будете", "3": "будуть" },
} as const;

export function buildFutureTenseNumbers(args: {
  infinitive?: string | null;
  futureNumbers?: Record<string, Record<string, string>> | null;
  presentNumbers?: Record<string, Record<string, string>> | null;
  aspect?: "imperfective" | "perfective" | null;
  formatForm?: (form: string | undefined | null) => string;
}): Record<string, Record<string, string>> | null {
  const { infinitive, futureNumbers, presentNumbers, aspect, formatForm } = args;
  const inf = infinitive?.trim();
  const isButy = inf === "бути";

  const hasSyntheticImperf = Object.values(futureNumbers ?? {}).some((num) =>
    Object.values(num).some((f) =>
      /(?:тиму|тимеш|тиме|тимемо|тимете|тимуть)\b/u.test(
        f.normalize("NFD").replace(/[\u0300-\u036f]/g, ""),
      ),
    ),
  );

  const hasPresent = Boolean(
    presentNumbers &&
      Object.values(presentNumbers).some((num) =>
        Object.values(num).some((f) => Boolean(f?.trim())),
      ),
  );

  const isImperfective =
    aspect === "imperfective" ||
    (aspect !== "perfective" && (hasSyntheticImperf || hasPresent));

  const canHaveAnalytic = Boolean(inf && !isButy && isImperfective);

  const result: Record<string, Record<string, string>> = {
    однина: {},
    множина: {},
  };

  let hasAny = false;
  const infDisplay = (formatForm && inf ? formatForm(inf) : inf) || "";

  for (const number of ["однина", "множина"] as const) {
    for (const person of ["1", "2", "3"] as const) {
      const syntheticRaw = futureNumbers?.[number]?.[person]?.trim();
      const synthetic =
        syntheticRaw && formatForm ? formatForm(syntheticRaw) : syntheticRaw;
      const analytic = canHaveAnalytic ? `${BUDU_FORMS[number][person]} ${infDisplay}` : undefined;

      const forms: string[] = [];
      if (analytic) forms.push(analytic);
      if (synthetic && synthetic !== analytic) forms.push(synthetic);

      if (forms.length > 0) {
        result[number][person] = forms.join(" / ");
        hasAny = true;
      }
    }
  }

  return hasAny ? result : null;
}

/** Ukrainian track labels for «У курсі» (CEFR codes stay Latin; seminar tracks are localized). */
export const TRACK_LABELS_UK: Record<string, string> = {
  a1: "A1",
  a2: "A2",
  b1: "B1",
  b2: "B2",
  c1: "C1",
  c2: "C2",
  folk: "Фольклор",
  hist: "Історія",
  istorio: "Історіографія",
  bio: "Біографії",
  lit: "Література",
  oes: "Давня східнослов'янська",
  ruth: "Руська",
};

export const CONTEXT_LABELS_UK: Record<string, string> = {
  built_vocabulary: "вивчається",
  plan_required: "обов'язкова",
  plan_recommended: "рекомендована",
  surzhyk_to_avoid: "остерігайтеся",
};

export const MARKED_LEARNER_NOTE =
  "Це нестандартні або стилістично забарвлені форми, які трапляються в поезії, фольклорі та давніших текстах. Вони не належать до сучасної літературної норми.";

/** Short row labels for the compact form/pronunciation strip (#6465). */
export const FORM_NOTE_LABELS: Record<string, string> = {
  orthography: "Правопис",
  holoskevych: "Голоскевич, 1929",
  orthoepy: "Орфоепія",
};

export const TRANSLATION_SOURCE_LABELS: Record<string, string> = {
  learner_english_gloss: "Anna Ohoiko",
  agy_en_proposal: "модельний переклад",
};

export function formatTranslationSource(source: string | null | undefined): string | null {
  if (!source) return null;
  return TRANSLATION_SOURCE_LABELS[source] ?? source;
}

const MORPHOLOGY_SUPPRESSED_TYPES = new Set([
  "multiword_term",
  "expression",
  "phraseologism",
  "proverb",
]);

const MIRROR_HOSTS = new Set(["slovnyk.me", "goroh.pp.ua", "sum.in.ua"]);

export function formatIpa(value: string | null | undefined) {
  const trimmed = value?.trim();
  if (!trimmed) return null;
  return trimmed.startsWith("[") || trimmed.startsWith("/") ? trimmed : `[${trimmed}]`;
}

const POS_LABELS: Record<string, string> = {
  "іменник": "іменник",
  "дієслово": "дієслово",
  "прикметник": "прикметник",
  "прислівник": "прислівник",
  "присл": "прислівник",
  "числівник": "числівник",
  "прийменник": "прийменник",
  "приймен": "прийменник",
  "сполучник": "сполучник",
  "спол": "сполучник",
  "частка": "частка",
  "службове слово": "службове слово",
  noun: "іменник",
  verb: "дієслово",
  adj: "прикметник",
  adjective: "прикметник",
  adverb: "прислівник",
  adv: "прислівник",
  phrase: "фраза",
  pron: "займенник",
  pronoun: "займенник",
  prep: "прийменник",
  preposition: "прийменник",
  conj: "сполучник",
  conjunction: "сполучник",
  particle: "частка",
  interjection: "вигук",
  numeral: "числівник",
  num: "числівник",
  function: "службове слово",
};

const DEFINITION_POS_HEADER = String.raw`(?:^|[\n;]|\|\|)\s*(?:\d+\s*[.)》]\s*)?(?:[–—-]\s*)?`;
const DEFINITION_POS_MARKERS: Array<[RegExp, string]> = [
  [new RegExp(`${DEFINITION_POS_HEADER}(?:іменник|noun)(?=$|[\\s,;:])`, "imu"), "іменник"],
  [new RegExp(`${DEFINITION_POS_HEADER}(?:дієслово|verb)(?=$|[\\s,;:])`, "imu"), "дієслово"],
  [new RegExp(`${DEFINITION_POS_HEADER}(?:прикметник|adjective)(?=$|[\\s,;:])`, "imu"), "прикметник"],
  [new RegExp(`${DEFINITION_POS_HEADER}(?:прислівник|присл\\.|adverb)(?=$|[\\s,;:])`, "imu"), "прислівник"],
  [new RegExp(`${DEFINITION_POS_HEADER}(?:числівник|numeral)(?=$|[\\s,;:])`, "imu"), "числівник"],
  [new RegExp(`${DEFINITION_POS_HEADER}(?:прийменник|приймен\\.|preposition)(?=$|[\\s,;:])`, "imu"), "прийменник"],
  [new RegExp(`${DEFINITION_POS_HEADER}(?:сполучник|спол\\.|conjunction)(?=$|[\\s,;:])`, "imu"), "сполучник"],
  [new RegExp(`${DEFINITION_POS_HEADER}(?:частка|particle)(?=$|[\\s,;:])`, "imu"), "частка"],
];

function normalizePosLabels(value: string | null | undefined) {
  const text = value?.trim();
  if (!text) return [];
  return text
    .split(/\s*(?:[,;/|+]|\b(?:or|або|і|та)\b)\s*/iu)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const key = part.toLocaleLowerCase("uk");
      const alias = Object.keys(POS_LABELS).find(
        (candidate) =>
          key === candidate ||
          key.startsWith(`${candidate}:`) ||
          key.startsWith(`${candidate}.`) ||
          key.startsWith(`${candidate} `),
      );
      return alias ? { label: POS_LABELS[alias]!, known: true } : { label: part, known: false };
    });
}

function definitionCardPosLabels(cards: DefinitionCard[] | undefined) {
  const labels: string[] = [];
  for (const card of cards ?? []) {
    for (const definition of card.definitions ?? []) {
      for (const [pattern, label] of DEFINITION_POS_MARKERS) {
        if (pattern.test(definition) && !labels.includes(label)) labels.push(label);
      }
    }
  }
  return labels;
}

export function formatPos(
  pos: string | null | undefined,
  morphologyPos: string | null | undefined,
  signals: {
    cefrPos?: string | null;
    translationPos?: string | null;
    definitionCards?: DefinitionCard[];
  } = {},
) {
  const labels: string[] = [];
  const fallbackLabels: string[] = [];
  const addSignal = (value: string | null | undefined) => {
    for (const normalized of normalizePosLabels(value)) {
      const target = normalized.known ? labels : fallbackLabels;
      if (!target.includes(normalized.label)) target.push(normalized.label);
    }
  };

  // Preserve the learner-facing precedence: VESUM morphology first, article
  // metadata second, then the remaining enrichment signals.
  addSignal(morphologyPos);
  addSignal(pos);
  addSignal(signals.cefrPos);
  addSignal(signals.translationPos);
  for (const label of definitionCardPosLabels(signals.definitionCards)) addSignal(label);

  return (labels.length > 0 ? labels : fallbackLabels).join(" · ") || null;
}

export function expressionLikeEntryTypeLabel(entryType: string | null | undefined) {
  const labels: Record<string, string> = {
    expression: "вираз",
    phraseologism: "фразеологізм",
    proverb: "прислів'я",
    multiword_term: "термін",
  };
  return entryType ? labels[entryType] ?? null : null;
}

export function isSum11DefinitionCard(card: DefinitionCard) {
  return (
    card.id.includes("sum11") ||
    card.source.includes("СУМ-11") ||
    Boolean(card.source_pill?.includes("СУМ-11"))
  );
}

export function isSovietizedSum11DefinitionCard(card: DefinitionCard) {
  return (
    isSum11DefinitionCard(card) &&
    ((card.sovietization_risk ?? 0) > 0 || card.id.includes("flagged"))
  );
}

export function shouldRenderDefinitionCard(card: DefinitionCard) {
  return !isSum11DefinitionCard(card);
}

const RUSALKA_CLASS_LEMMAS = new Set([
  "русалка",
  "русалки",
  "мавка",
  "мавки",
  "нявка",
  "нявки",
]);

const WIKI_RUSALKA_KIN_RE =
  /спор[іі]днен\w{0,8}\s+(?:із|з)\s+русалк|інш(?:а|ою)\s+назва(?:ою)?\s+русалк|тотожн\w{0,8}\s+(?:із|з)\s+русалк/i;
const WIKI_LESSER_SPIRIT_RE = /нижч(?:ий|а|і)\s+дух/i;
const WIKI_RUSALKA_STEM_RE = /русалк/i;

function stripWikiStress(text: string): string {
  return text.replaceAll("\u0301", "");
}

export function normalizeAtlasLemma(lemma: string): string {
  return stripWikiStress(lemma).trim().toLocaleLowerCase("uk");
}

/** Normalize a relation label without changing the text shown to the learner. */
export function normalizeAtlasLookupText(value: string): string {
  return normalizeAtlasLemma(value.replace(/\([^)]*\)/gu, "").replace(/\s+/gu, " "));
}

export interface AtlasLinkResolver {
  resolve(text: string, excludeSlug?: string | null): string | null;
  resolveSlug(slug: string, excludeSlug?: string | null): string | null;
  isAmbiguous(text: string): boolean;
}

export interface AtlasSearchArticleRow {
  l: string;
  s: string;
  g: string | null;
  t?: string;
  /** Compact source-backed gerund → infinitive parent emitted by the producer. */
  p?: string;
}

export interface AtlasSearchAliasRow {
  a: string;
  s: string;
}

export function buildAtlasLinkCatalogFromSearchRows(
  articles: readonly AtlasSearchArticleRow[],
  aliases: readonly AtlasSearchAliasRow[] = [],
): AtlasLinkCatalog {
  return {
    entries: articles.map((row) => ({
      lemma: row.l,
      slug: row.s,
      entry_type: row.t ?? "lemma",
      gloss: row.g,
      gerund_parent: row.p,
    })),
    aliases: aliases.map((row) => ({ alias: row.a, target_slug: row.s })),
  };
}

const EMPTY_ATLAS_LINK_CATALOG: AtlasLinkCatalog = { entries: [], aliases: [] };

interface AtlasLinkIndexes {
  entriesBySlug: Map<string, AtlasLinkCatalogEntry[]>;
  canonicalSlugs: Set<string>;
  directTargets: Map<string, Set<string>>;
  aliasTargets: Map<string, Set<string>>;
}

const ATLAS_LINK_INDEX_CACHE = new WeakMap<AtlasLinkCatalog, AtlasLinkIndexes>();

function isCanonicalAtlasEntry(entry: AtlasLinkCatalogEntry): boolean {
  return (
    Boolean(entry.slug.trim() && entry.lemma.trim()) &&
    entry.entry_type !== null &&
    entry.entry_type !== "form_route"
  );
}

function posVariants(entries: AtlasLinkCatalogEntry[]): Set<string> {
  const variants = new Set<string>();
  for (const entry of entries) {
    const pos = entry.pos?.trim();
    if (!pos) continue;
    for (const value of pos.split(/\s*(?:[,;/|+])\s*|\s+(?:or|або)\s+/iu)) {
      const normalized = normalizeAtlasLemma(value);
      if (normalized) variants.add(normalized);
    }
  }
  return variants;
}

function uniqueTarget(
  slugs: Set<string>,
  entriesBySlug: Map<string, AtlasLinkCatalogEntry[]>,
): string | null {
  if (slugs.size !== 1) return null;
  const slug = [...slugs][0]!;
  const entries = entriesBySlug.get(slug) ?? [];
  if (entries.length === 0 || posVariants(entries).size > 1) return null;
  return slug;
}

function addLookupTarget(index: Map<string, Set<string>>, text: string, slug: string): void {
  const key = normalizeAtlasLookupText(text);
  if (!key || !slug.trim()) return;
  const targets = index.get(key) ?? new Set<string>();
  targets.add(slug);
  index.set(key, targets);
}

function atlasLinkIndexes(catalog: AtlasLinkCatalog): AtlasLinkIndexes {
  const cached = ATLAS_LINK_INDEX_CACHE.get(catalog);
  if (cached) return cached;

  const entriesBySlug = new Map<string, AtlasLinkCatalogEntry[]>();
  const canonicalSlugs = new Set<string>();
  const directTargets = new Map<string, Set<string>>();
  const aliasTargets = new Map<string, Set<string>>();

  for (const entry of catalog.entries) {
    if (!isCanonicalAtlasEntry(entry)) continue;
    const entries = entriesBySlug.get(entry.slug) ?? [];
    entries.push(entry);
    entriesBySlug.set(entry.slug, entries);
    canonicalSlugs.add(entry.slug);
    addLookupTarget(directTargets, entry.lemma, entry.slug);
  }
  for (const alias of catalog.aliases ?? []) {
    if (!canonicalSlugs.has(alias.target_slug)) continue;
    addLookupTarget(aliasTargets, alias.alias, alias.target_slug);
  }

  const indexes = { entriesBySlug, canonicalSlugs, directTargets, aliasTargets };
  ATLAS_LINK_INDEX_CACHE.set(catalog, indexes);
  return indexes;
}

/**
 * Build the article/alias resolver used by all learner-facing lexical links.
 * Direct article heads win over aliases; every non-unique target is rejected.
 */
export function buildAtlasLinkResolver(
  catalog: AtlasLinkCatalog = EMPTY_ATLAS_LINK_CATALOG,
  relatedSlugs: readonly string[] = [],
): AtlasLinkResolver {
  const { entriesBySlug, canonicalSlugs, directTargets, aliasTargets } = atlasLinkIndexes(catalog);
  const relationTargets = new Map<string, Set<string>>();

  for (const slug of relatedSlugs) {
    addLookupTarget(relationTargets, slug, slug);
  }

  const resolveIndexed = (
    index: Map<string, Set<string>>,
    key: string,
    excludeSlug?: string | null,
  ): string | null => {
    const targets = index.get(key);
    if (!targets) return null;
    const target = uniqueTarget(targets, entriesBySlug);
    if (!target || target === excludeSlug) return null;
    return target;
  };

  const hasAmbiguousIndexed = (index: Map<string, Set<string>>, key: string): boolean => {
    const targets = index.get(key);
    if (!targets) return false;
    return uniqueTarget(targets, entriesBySlug) === null;
  };

  return {
    resolve(text, excludeSlug) {
      const key = normalizeAtlasLookupText(text);
      if (!key) return null;
      // A direct head is authoritative, including when it is ambiguous or the
      // only result is the current page; do not fall through to an alias.
      if (directTargets.has(key)) return resolveIndexed(directTargets, key, excludeSlug);
      if (aliasTargets.has(key)) return resolveIndexed(aliasTargets, key, excludeSlug);

      const related = relationTargets.get(key);
      if (!related || related.size !== 1) return null;
      const target = [...related][0]!;
      return target === excludeSlug ? null : target;
    },
    resolveSlug(slug, excludeSlug) {
      if (!canonicalSlugs.has(slug) || slug === excludeSlug) return null;
      return uniqueTarget(new Set([slug]), entriesBySlug);
    },
    isAmbiguous(text) {
      const key = normalizeAtlasLookupText(text);
      if (!key) return false;
      if (directTargets.has(key)) return hasAmbiguousIndexed(directTargets, key);
      if (aliasTargets.has(key)) return hasAmbiguousIndexed(aliasTargets, key);
      return (relationTargets.get(key)?.size ?? 0) > 1;
    },
  };
}

const PASSIVE_PARTICIPLE_PARENT_RE =
  /^\s*Дієпр\.\s*пас\.?[\s\S]*?(?<![\p{L}\p{M}])до\s+([\p{L}\p{M}]+(?:['’ʼ-][\p{L}\p{M}]+)*)/iu;

function participleParent(entry: AtlasLinkCatalogEntry): string | null {
  const paradigm = entry.enrichment?.morphology?.paradigm;
  if (paradigm?.kind === "participle") {
    if (paradigm.voice !== "passive") return null;
    return paradigm.verb?.trim() || null;
  }
  const match = entry.gloss?.match(PASSIVE_PARTICIPLE_PARENT_RE);
  return match?.[1]?.trim() || null;
}

interface ParticipleCandidate extends ParticipleLink {
  parent: string;
}

const PARTICIPLE_CANDIDATE_CACHE = new WeakMap<AtlasLinkCatalog, ParticipleCandidate[]>();

function participleCandidates(catalog: AtlasLinkCatalog): ParticipleCandidate[] {
  const cached = PARTICIPLE_CANDIDATE_CACHE.get(catalog);
  if (cached) return cached;

  const candidates: ParticipleCandidate[] = [];
  for (const entry of catalog.entries) {
    if (!isCanonicalAtlasEntry(entry)) continue;
    const parent = participleParent(entry);
    if (parent) candidates.push({ lemma: entry.lemma, slug: entry.slug, parent });
  }
  PARTICIPLE_CANDIDATE_CACHE.set(catalog, candidates);
  return candidates;
}

/** Return published passive participle routes whose verified parent is `parentSlug`. */
export function buildParticipleLinks(
  catalog: AtlasLinkCatalog,
  resolver: AtlasLinkResolver,
  parentSlug: string,
): ParticipleLink[] {
  const links = new Map<string, ParticipleLink>();
  for (const candidate of participleCandidates(catalog)) {
    if (candidate.slug === parentSlug || resolver.resolve(candidate.parent) !== parentSlug) continue;
    links.set(candidate.slug, { lemma: candidate.lemma, slug: candidate.slug });
  }
  return [...links.values()].sort((left, right) => {
    const lemmaOrder = normalizeAtlasLookupText(left.lemma).localeCompare(
      normalizeAtlasLookupText(right.lemma),
      "uk",
    );
    return lemmaOrder || left.slug.localeCompare(right.slug);
  });
}

interface GerundCandidate extends GerundLink {
  parent: string;
}

const GERUND_CANDIDATE_CACHE = new WeakMap<AtlasLinkCatalog, GerundCandidate[]>();

function gerundCandidates(catalog: AtlasLinkCatalog): GerundCandidate[] {
  const cached = GERUND_CANDIDATE_CACHE.get(catalog);
  if (cached) return cached;

  const candidates: GerundCandidate[] = [];
  for (const entry of catalog.entries) {
    if (!isCanonicalAtlasEntry(entry)) continue;
    const parent = entry.gerund_parent?.trim();
    if (parent) candidates.push({ lemma: entry.lemma, slug: entry.slug, parent });
  }
  GERUND_CANDIDATE_CACHE.set(catalog, candidates);
  return candidates;
}

/** Return published gerund routes whose producer-verified parent is `parentSlug`. */
export function buildGerundLinks(
  catalog: AtlasLinkCatalog,
  resolver: AtlasLinkResolver,
  parentSlug: string,
): GerundLink[] {
  const links = new Map<string, GerundLink>();
  for (const candidate of gerundCandidates(catalog)) {
    // `resolve()` rejects missing and ambiguous parent heads, so a stale or
    // malformed compact hint cannot turn into a learner-facing backlink.
    if (candidate.slug === parentSlug || resolver.resolve(candidate.parent) !== parentSlug) continue;
    links.set(candidate.slug, { lemma: candidate.lemma, slug: candidate.slug });
  }
  return [...links.values()].sort((left, right) => {
    const lemmaOrder = normalizeAtlasLookupText(left.lemma).localeCompare(
      normalizeAtlasLookupText(right.lemma),
      "uk",
    );
    return lemmaOrder || left.slug.localeCompare(right.slug);
  });
}

export function isRusalkaClassLemma(lemma: string): boolean {
  return RUSALKA_CLASS_LEMMAS.has(normalizeAtlasLemma(lemma));
}

export function wikipediaLeadText(...parts: Array<string | null | undefined>): string {
  return parts
    .map((part) => {
      const raw = stripWikiStress(part ?? "").trim();
      if (!raw) return "";
      return raw.split(/(?<=[.!?])\s+/, 1)[0]?.trim() ?? "";
    })
    .filter(Boolean)
    .join(" ");
}

export function wikipediaLeadHasRusalkaKinFraming(
  ...parts: Array<string | null | undefined>
): boolean {
  const lead = wikipediaLeadText(...parts);
  if (!lead) return false;
  if (WIKI_RUSALKA_KIN_RE.test(lead)) return true;
  return WIKI_LESSER_SPIRIT_RE.test(lead) && WIKI_RUSALKA_STEM_RE.test(lead);
}

export function atlasWikipediaOkAsIntro(
  lemma: string,
  wiki: { description?: string; extract?: string; summary?: string } | null | undefined,
): boolean {
  if (!wiki) return false;
  if (isRusalkaClassLemma(lemma)) return true;
  return !wikipediaLeadHasRusalkaKinFraming(
    wiki.description,
    wiki.extract ?? wiki.summary,
  );
}

export function sanitizeWikiReference(
  lemma: string,
  wiki: LexiconEntryView["wiki_reference"] | null | undefined,
): LexiconEntryView["wiki_reference"] | null {
  if (!wiki) return null;
  const keepWikipedia = atlasWikipediaOkAsIntro(lemma, wiki.wikipedia);
  const next = keepWikipedia ? wiki : { ...wiki, wikipedia: undefined };
  if (!next.wikipedia && !next.wiktionary_url && !next.wikisource_url) {
    return null;
  }
  return next;
}

export function sourceClass(card: DefinitionCard) {
  if (card.id.includes("sum11") && ((card.sovietization_risk ?? 0) > 0 || card.id.includes("flagged"))) {
    return "sum11-flagged";
  }
  if (card.id.includes("sum20")) return "sum20";
  if (card.id.includes("vts")) return "sum20";
  if (card.id.includes("grinchenko")) return "grinchenko";
  if (card.id.includes("sum11")) return "sum11";
  return card.id;
}

export function isMirrorUrl(url: string) {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    return MIRROR_HOSTS.has(host);
  } catch {
    return [...MIRROR_HOSTS].some((host) => url.includes(host));
  }
}

export function learnerFacingUrls(urls?: string[]) {
  return (urls ?? []).filter((url) => url && !isMirrorUrl(url) && Boolean(safeHref(url)));
}

export function sourceHost(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "джерело";
  }
}

export function buildWordAtlasArticleView(
  record: EntryRecord,
  generatedAt: string,
  manifestVersion: string,
  atlasLinkCatalog?: AtlasLinkCatalog,
) {
  const rawEntry = record.entry as unknown as LexiconEntryView;
  const wikiReference = sanitizeWikiReference(rawEntry.lemma, rawEntry.wiki_reference);
  const entry =
    wikiReference === rawEntry.wiki_reference
      ? rawEntry
      : { ...rawEntry, wiki_reference: wikiReference };
  const enrichment = entry.enrichment ?? null;
  const sections = entry.sections ?? null;
  const synonymSets = sections?.synonyms?.synsets ?? [];
  const heritage = entry.heritage_status ?? null;
  const rawDefinitionCards = enrichment?.definition_cards ?? [];
  const definitionCards = rawDefinitionCards.filter(shouldRenderDefinitionCard);
  const sovietizedCards = rawDefinitionCards.filter(isSovietizedSum11DefinitionCard);
  const maxSovietizationRisk = Math.max(
    0,
    ...sovietizedCards.map((card) => card.sovietization_risk ?? 1),
  );
  const sovietizationKeywords = Array.from(
    new Set(sovietizedCards.flatMap((card) => card.sovietization_keywords ?? [])),
  );
  const letter = entry.lemma.charAt(0).toLocaleUpperCase("uk");
  const headerStress = enrichment?.stress?.form ?? null;
  const cefrLevel = enrichment?.cefr?.level ?? null;
  const paradigm = enrichment?.morphology?.paradigm ?? null;
  const nounParadigm = paradigm?.kind === "noun" ? paradigm : null;
  const verbParadigm = paradigm?.kind === "verb" ? paradigm : null;
  const rawParticipleParadigm = paradigm?.kind === "participle" ? paradigm : null;
  const linkCatalog = atlasLinkCatalog ?? EMPTY_ATLAS_LINK_CATALOG;
  const linkResolver = buildAtlasLinkResolver(
    linkCatalog,
    record.relations.map((relation) => relation.related_slug),
  );
  const participleParentSlug =
    rawParticipleParadigm?.voice === "passive" && rawParticipleParadigm.verb
      ? linkResolver.resolve(rawParticipleParadigm.verb, entry.url_slug) ??
        (!linkResolver.isAmbiguous(rawParticipleParadigm.verb)
          ? atlasLinkCatalog === undefined
            ? rawParticipleParadigm.verb_url_slug?.trim() || null
            : linkResolver.resolveSlug(rawParticipleParadigm.verb_url_slug ?? "", entry.url_slug)
          : null)
      : null;
  const participleParadigm = rawParticipleParadigm
    ? { ...rawParticipleParadigm, verb_url_slug: participleParentSlug ?? undefined }
    : null;
  const participleLinks = buildParticipleLinks(linkCatalog, linkResolver, entry.url_slug);
  const gerundLinks = buildGerundLinks(linkCatalog, linkResolver, entry.url_slug);
  const markedForms = enrichment?.morphology?.marked_forms ?? [];
  const markedFormGroups: Array<{ marker_label: string; forms: typeof markedForms }> = [];
  for (const form of markedForms) {
    let group = markedFormGroups.find((g) => g.marker_label === form.marker_label);
    if (!group) {
      group = { marker_label: form.marker_label, forms: [] };
      markedFormGroups.push(group);
    }
    group.forms.push(form);
  }
  const morphology = enrichment?.morphology ?? null;
  const isFullyMarked = isFullyMarkedLemma(morphology);
  const dominantRegisterLabel = isFullyMarked ? dominantMarkerLabel(markedForms) : null;
  const isExpressionLikeEntry = MORPHOLOGY_SUPPRESSED_TYPES.has(entry.entry_type ?? "");
  const suppressMorphology = isExpressionLikeEntry;
  const entryTypeLabel = expressionLikeEntryTypeLabel(entry.entry_type);
  const posLabel = formatPos(entry.pos, enrichment?.morphology?.pos, {
    cefrPos: enrichment?.cefr?.pos,
    translationPos: enrichment?.translation?.pos,
    definitionCards,
  });
  const headwordIpa = formatIpa(entry.pronunciation?.ipa ?? entry.ipa);
  const heritageBoxes = resolveHeritageBoxes(entry);
  const etymologyStages = buildEtymologyStages(enrichment?.etymology, entry.lemma);
  const formattedOrigin = formatOrigin(enrichment?.etymology);
  const courseUsage = (entry.course_usage ?? []).slice().sort((a, b) => {
    if (a.track !== b.track) return a.track.localeCompare(b.track);
    return a.module_num - b.module_num;
  });
  const textbookItems = enrichment?.textbooks ?? [];
  const externalGroups = groupExternalMaterials(enrichment?.external_materials ?? []);
  const componentLinks = record.renderContext.componentLinks;
  const atlasLinkTargetForText = (text: string) => linkResolver.resolve(text, entry.url_slug);
  const phraseHasGloss = Boolean(
    entry.gloss && definitionCards.length === 0 && !enrichment?.meaning,
  );
  const shouldShowEditorialWarning = Boolean(heritageBoxes.red);
  const shouldShowHeritageDefense = Boolean(heritageBoxes.green);
  const styleNotes = buildStyleNotes(heritage);
  const statusBadges = buildStatusBadges({
    heritageBoxes,
    cefrLevel,
    enrichment,
    heritage,
    isFullyMarked,
    dominantRegisterLabel,
  });
  const articleOverview = buildArticleOverview({
    sections,
    enrichment,
    externalGroups,
    definitionCards,
    phraseHasGloss,
    styleNotes,
    heritageBoxes,
    courseUsage,
    entry,
    isFullyMarked,
    suppressMorphology,
    formattedOrigin,
  });
  const sourceList = buildSourceList({
    entry,
    enrichment,
    definitionCards,
    sections,
  });
  const translationSource = formatTranslationSource(enrichment?.translation?.source);
  const verbPedagogy = enrichment?.verb_pedagogy ?? null;
  const rawPartnerSlug = verbPedagogy?.aspect_partner?.url_slug?.trim() || null;
  const resolvedAspectPartnerSlug = rawPartnerSlug
    ? linkResolver.resolveSlug(rawPartnerSlug, entry.url_slug)
    : null;
  const partnerEntry = resolvedAspectPartnerSlug
    ? linkCatalog.entries.find(
        (e) => e.slug === resolvedAspectPartnerSlug && isCanonicalAtlasEntry(e),
      ) ?? null
    : null;
  const partnerParadigm =
    partnerEntry?.enrichment?.morphology?.paradigm?.kind === "verb"
      ? partnerEntry.enrichment.morphology.paradigm
      : null;
  const hasAspectPartner = Boolean(resolvedAspectPartnerSlug);
  const hasVerbPedagogy = Boolean(
    verbPedagogy &&
      (verbPedagogy.aspect ||
        verbPedagogy.aspect_partner ||
        verbPedagogy.stems ||
        (verbPedagogy.government?.length ?? 0) > 0),
  );
  const verbPedagogySources = verbPedagogy
    ? Array.from(
        new Set(
          [
            verbPedagogy.aspect ? "VESUM" : null,
            verbPedagogy.aspect_partner?.source,
            verbPedagogy.stems?.source,
            ...(verbPedagogy.government ?? []).map((item) => item.source),
          ].filter((value): value is string => Boolean(value)),
        ),
      ).join(", ")
    : "";
  const hasPractice = (record.renderContext.practiceLevels ?? []).length > 0;

  function stressDisplay(form: string | undefined | null) {
    if (!form) return "";
    return enrichment?.morphology?.stress?.forms?.[form] ?? form;
  }

  return {
    entry,
    enrichment,
    sections,
    synonymSets,
    heritage,
    definitionCards,
    maxSovietizationRisk,
    sovietizationKeywords,
    letter,
    headerStress,
    nounParadigm,
    verbParadigm,
    participleParadigm,
    participleLinks,
    gerundLinks,
    atlasLinkTargetForText,
    markedFormGroups,
    isFullyMarked,
    isExpressionLikeEntry,
    suppressMorphology,
    entryTypeLabel,
    posLabel,
    headwordIpa,
    heritageBoxes,
    etymologyStages,
    formattedOrigin,
    courseUsage,
    textbookItems,
    externalGroups,
    componentLinks,
    phraseHasGloss,
    shouldShowEditorialWarning,
    shouldShowHeritageDefense,
    styleNotes,
    statusBadges,
    articleOverview,
    sourceList,
    translationSource,
    verbPedagogy,
    hasVerbPedagogy,
    verbPedagogySources,
    resolvedAspectPartnerSlug,
    partnerEntry,
    partnerParadigm,
    hasAspectPartner,
    hasPractice,
    generatedAt,
    manifestVersion,
    stressDisplay,
  };
}

export type WordAtlasArticleView = ReturnType<typeof buildWordAtlasArticleView>;

function buildStatusBadges(args: {
  heritageBoxes: ReturnType<typeof resolveHeritageBoxes>;
  cefrLevel: string | null;
  enrichment: Enrichment | null;
  heritage: HeritageStatus | null;
  isFullyMarked: boolean;
  dominantRegisterLabel: string | null;
}) {
  const {
    heritageBoxes,
    cefrLevel,
    enrichment,
    heritage,
    isFullyMarked,
    dominantRegisterLabel,
  } = args;
  const badges: Array<{ className: string; label: string; title?: string }> = [];
  if (heritageBoxes.red) {
    badges.push({
      className: "heritage-warn",
      label: heritageBoxes.inline?.label ?? "⚠ Потребує українського відповідника",
    });
  } else if (heritageBoxes.yellow) {
    badges.push({ className: "heritage-warn", label: "Калькове застереження" });
  } else if (heritageBoxes.green) {
    badges.push({
      className: "heritage-ok",
      label: heritageBoxes.inline?.label ?? "✓ Питома українська лексика",
    });
  } else if (heritageBoxes.blue) {
    badges.push({ className: "heritage-warn", label: "СУМ-11: редакторський прапорець" });
  }
  if (cefrLevel) {
    badges.push({
      className: "cefr",
      label: `CEFR ${cefrLevel}${enrichment?.cefr?.source?.includes("estimated") ? " · орієнтовно" : ""}`,
    });
  }
  if (
    heritage?.classification === "historism" ||
    heritage?.classification === "archaism" ||
    heritage?.classification === "authentic-archaism"
  ) {
    badges.push({
      className: "archaic",
      label: heritage.classification === "historism" ? "Історизм у сучасному вжитку" : "Архаїзм",
    });
  }
  if (heritage?.classification === "dialect") {
    badges.push({ className: "dialect", label: "Регіонально-літературне" });
  }
  if (isFullyMarked && dominantRegisterLabel) {
    badges.push({
      className: "register",
      label: registerBadgeLabel(dominantRegisterLabel),
    });
  }
  return badges;
}

function buildEtymologyStages(etymology: SourcedText | undefined, lemma: string) {
  if (!etymology) return [];
  if (etymology.stages?.length) {
    return etymology.stages.map((stage, index) => ({
      period: stage.period,
      word: stage.word,
      note: stage.note ?? etymology.text,
      className: index === etymology.stages!.length - 1 ? "modern" : "archaic",
    }));
  }
  return [
    {
      period: etymology.source,
      word: lemma,
      note: etymology.text,
      className: "modern",
    },
  ];
}

function buildStyleNotes(heritage: HeritageStatus | null) {
  const notes: string[] = [];
  if (heritage?.russian_shadow) {
    notes.push(
      "Морфологічна тінь російської форми: перевіряйте відмінювання за VESUM та Правописом 2019.",
    );
  }
  if (heritage?.calque_warning?.detail) {
    notes.push(`Калькове застереження: ${heritage.calque_warning.detail}`);
  }
  if (heritage?.curated_calque) {
    notes.push(
      `${heritage.curated_calque.note} Нейтральні відповідники: ${heritage.curated_calque.corrections.join(", ")}.`,
    );
  }
  return notes;
}

function groupExternalMaterials(items: NonNullable<Enrichment["external_materials"]>) {
  const groups = new Map<string, NonNullable<Enrichment["external_materials"]>>();
  for (const item of items) {
    const key = item.group ?? item.kind ?? "Зовнішні матеріали";
    const bucket = groups.get(key) ?? [];
    bucket.push(item);
    groups.set(key, bucket);
  }
  return Array.from(groups.entries()).map(([name, materials]) => ({ name, materials }));
}

function buildArticleOverview(args: {
  sections: LexiconSections | null;
  enrichment: Enrichment | null;
  externalGroups: ReturnType<typeof groupExternalMaterials>;
  definitionCards: DefinitionCard[];
  phraseHasGloss: boolean;
  styleNotes: string[];
  heritageBoxes: ReturnType<typeof resolveHeritageBoxes>;
  courseUsage: CourseUsage[];
  entry: LexiconEntryView;
  isFullyMarked: boolean;
  suppressMorphology: boolean;
  formattedOrigin: ReturnType<typeof formatOrigin>;
}) {
  const {
    sections,
    enrichment,
    externalGroups,
    definitionCards,
    phraseHasGloss,
    styleNotes,
    heritageBoxes,
    courseUsage,
    entry,
    isFullyMarked,
    suppressMorphology,
    formattedOrigin,
  } = args;
  const synonymCount =
    (sections?.synonyms?.items?.length ?? 0) + (sections?.antonyms?.items?.length ?? 0);
  const homonymCount = sections?.homonyms?.items?.length ?? 0;
  const paronymCount = sections?.paronyms?.items?.length ?? 0;
  const idiomCount = sections?.idioms?.items?.length ?? 0;
  const proverbCount = sections?.proverbs?.items?.length ?? 0;
  const usageNoteCount = sections?.usage_notes?.items?.length ?? 0;
  const formNoteCount = sections?.form_notes?.items?.length ?? 0;
  const externalCount = externalGroups.reduce((total, group) => total + (group.materials?.length ?? 0), 0);
  const definitionCount =
    definitionCards.length + (enrichment?.meaning ? 1 : 0) + (phraseHasGloss ? 1 : 0);
  const originCount = formattedOrigin || enrichment?.etymology ? 1 : 0;
  const cards = [
    {
      label: "Значення",
      ready: definitionCount > 0,
      detail:
        definitionCount > 0
          ? `${definitionCount} ${pluralizeUk(definitionCount, ["картка", "картки", "карток"])}`
          : "очікує джерело",
    },
    {
      label: "Походження",
      ready: originCount > 0,
      detail:
        originCount > 0
          ? `${originCount} ${pluralizeUk(originCount, ["картка", "картки", "карток"])}`
          : "очікує джерело",
    },
    {
      label: "Морфологія",
      ready: Boolean(enrichment?.morphology),
      detail: enrichment?.morphology
        ? morphologyFormCountLabel(enrichment.morphology, isFullyMarked)
        : "очікує VESUM",
    },
    {
      label: "Написання і вимова",
      ready: formNoteCount > 0,
      detail:
        formNoteCount > 0
          ? `${formNoteCount} ${pluralizeUk(formNoteCount, ["джерело", "джерела", "джерел"])}`
          : "очікує джерело",
    },
    {
      label: "Стилістика",
      ready:
        styleNotes.length > 0 ||
        Boolean(
          heritageBoxes.red ||
            heritageBoxes.yellow ||
            heritageBoxes.blue ||
            heritageBoxes.green,
        ),
      detail:
        styleNotes.length > 0
          ? `${styleNotes.length} ${pluralizeUk(styleNotes.length, ["нотатка", "нотатки", "нотаток"])}`
          : heritageBoxes.green
            ? "захист питомості"
            : "без нотаток",
    },
    {
      label: "Синонімія",
      ready: synonymCount > 0,
      detail:
        synonymCount > 0
          ? `${synonymCount} ${pluralizeUk(synonymCount, ["позиція", "позиції", "позицій"])}`
          : "очікує джерело",
    },
    {
      label: "Омонім",
      ready: homonymCount > 0,
      detail:
        homonymCount > 0
          ? `${homonymCount} ${pluralizeUk(homonymCount, ["позиція", "позиції", "позицій"])}`
          : "очікує джерело",
    },
    {
      label: "Паронім",
      ready: paronymCount > 0,
      detail:
        paronymCount > 0
          ? `${paronymCount} ${pluralizeUk(paronymCount, ["позиція", "позиції", "позицій"])}`
          : "очікує джерело",
    },
    {
      label: "Фразеологія",
      ready: idiomCount > 0,
      detail:
        idiomCount > 0
          ? `${idiomCount} ${pluralizeUk(idiomCount, ["вираз", "вирази", "виразів"])}`
          : "очікує джерело",
    },
    {
      label: "Приповідки",
      ready: proverbCount > 0,
      detail:
        proverbCount > 0
          ? `${proverbCount} ${pluralizeUk(proverbCount, ["приповідка", "приповідки", "приповідок"])}`
          : "очікує джерело",
    },
    {
      label: "Стиль і норма",
      ready: usageNoteCount > 0,
      detail:
        usageNoteCount > 0
          ? `${usageNoteCount} ${pluralizeUk(usageNoteCount, ["нарис", "нариси", "нарисів"])}`
          : "очікує джерело",
    },
    {
      label: "Засвідчення",
      ready: Boolean(enrichment?.literary_attestation),
      detail: enrichment?.literary_attestation ? "літературний корпус" : "очікує корпус",
    },
    {
      label: "Курс",
      ready: courseUsage.length > 0,
      detail:
        courseUsage.length > 0
          ? `${courseUsage.length} ${pluralizeUk(courseUsage.length, ["модуль", "модулі", "модулів"])}`
          : "поза курсом",
    },
    {
      label: "Переклад",
      ready: (enrichment?.translation?.en?.length ?? 0) > 0,
      detail:
        (enrichment?.translation?.en?.length ?? 0) > 0
          ? `${enrichment?.translation?.en?.length} англ.`
          : "очікує джерело",
    },
    {
      label: "Wikimedia",
      ready: Boolean(entry.wiki_reference),
      detail: entry.wiki_reference?.wikipedia
        ? "Wikipedia"
        : entry.wiki_reference
          ? "Wiktionary"
          : "очікує джерело",
    },
    {
      label: "Зовнішні",
      ready: externalCount > 0,
      detail:
        externalCount > 0
          ? `${externalCount} ${pluralizeUk(externalCount, ["матеріал", "матеріали", "матеріалів"])}`
          : "очікує добірку",
    },
  ];
  return suppressMorphology ? cards.filter((card) => card.label !== "Морфологія") : cards;
}

function buildSourceList(args: {
  entry: LexiconEntryView;
  enrichment: Enrichment | null;
  definitionCards: DefinitionCard[];
  sections: LexiconSections | null;
}) {
  const { entry, enrichment, definitionCards, sections } = args;
  const sources = new Set<string>();
  const addMappedSource = (source: string | null | undefined) => {
    const label = formatTranslationSource(source) ?? source;
    if (label) sources.add(label);
  };
  for (const source of enrichment?.sources ?? []) addMappedSource(source);
  if (entry.pronunciation?.source) sources.add(entry.pronunciation.source);
  if (enrichment?.stress?.source) sources.add(enrichment.stress.source);
  if (enrichment?.cefr?.source) sources.add(enrichment.cefr.source);
  if (enrichment?.morphology?.source) sources.add(enrichment.morphology.source);
  if (enrichment?.meaning?.source) sources.add(enrichment.meaning.source);
  for (const card of definitionCards) sources.add(card.source);
  if (enrichment?.etymology?.source) sources.add(enrichment.etymology.source);
  if (sections?.synonyms?.source) sources.add(sections.synonyms.source);
  if (sections?.antonyms?.source) sources.add(sections.antonyms.source);
  if (sections?.homonyms?.source) sources.add(sections.homonyms.source);
  if (sections?.paronyms?.source) sources.add(sections.paronyms.source);
  if (sections?.idioms?.source) sources.add(sections.idioms.source);
  if (sections?.proverbs?.source) sources.add(sections.proverbs.source);
  if (sections?.usage_notes?.source) sources.add(sections.usage_notes.source);
  if (sections?.form_notes?.source) sources.add(sections.form_notes.source);
  if (enrichment?.literary_attestation?.source) sources.add(enrichment.literary_attestation.source);
  if (enrichment?.translation?.source) addMappedSource(enrichment.translation.source);
  for (const ex of enrichment?.examples ?? []) {
    if (ex.source) addMappedSource(ex.source);
  }
  if ((entry.course_usage ?? []).length > 0) sources.add("curriculum_vocabulary");
  if (entry.wiki_reference?.wikipedia) sources.add("query_wikipedia");
  if (entry.wiki_reference?.wiktionary_url) sources.add("uk.wiktionary");
  return Array.from(sources).sort((a, b) => a.localeCompare(b, "uk"));
}
