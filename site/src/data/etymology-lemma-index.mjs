import { existsSync, readFileSync } from 'node:fs';

const MANIFEST_URL = new URL('./etymology-manifest.json', import.meta.url);
const VESUM_LEMMAS_URL = new URL('./vesum-vocab-lemmas.json', import.meta.url);

let cachedResolver;

export function normalizeLemma(value) {
  return String(value ?? '')
    .trim()
    .toLocaleLowerCase('uk')
    .normalize('NFD')
    .replace(/[\u0300\u0301\u0341]/g, '')
    .normalize('NFC');
}

export function stripReflexiveSuffix(value) {
  const normalized = normalizeLemma(value);
  if (normalized.endsWith('ся')) return normalized.slice(0, -2);
  if (normalized.endsWith('сь')) return normalized.slice(0, -2);
  return normalized;
}

export function buildLemmaRoutes(manifest) {
  const routes = new Map();
  const entries = Array.isArray(manifest?.entries) ? manifest.entries : [];
  const slugGroups = manifest?.slug_groups ?? {};

  for (const entry of entries) {
    if (!entry?.lemma || !entry?.slug) continue;

    const key = normalizeLemma(entry.lemma);
    if (!key || routes.has(key)) continue;

    const group = slugGroups[entry.slug] ?? [];
    routes.set(key, {
      // Per-word /etymology/<slug>/ pages are offline in normal deploys
      // (#5274 — Pages budget). Deep-link the lexicon article anchor instead.
      href: `/lexicon/${entry.lemma}/#etymology`,
      lemma: entry.lemma,
      slug: entry.slug,
      polysemy: group.length > 1,
    });
  }

  return routes;
}

export function buildVesumLemmaMap(data) {
  const rawMap = data?.form_to_lemma ?? data?.lemmas ?? {};
  const lemmas = new Map();

  for (const [form, lemma] of Object.entries(rawMap)) {
    const formKey = normalizeLemma(form);
    const lemmaKey = normalizeLemma(lemma);
    if (formKey && lemmaKey) lemmas.set(formKey, lemma);
  }

  return lemmas;
}

export function createEtymologyResolver({ manifest, lemmaRoutes, vesumLemmas } = {}) {
  return {
    lemmaRoutes: lemmaRoutes ?? buildLemmaRoutes(manifest ?? { entries: [], slug_groups: {} }),
    vesumLemmas: vesumLemmas instanceof Map ? vesumLemmas : buildVesumLemmaMap(vesumLemmas ?? {}),
  };
}

export function loadDefaultEtymologyResolver() {
  if (cachedResolver) return cachedResolver;

  const manifest = JSON.parse(readFileSync(MANIFEST_URL, 'utf8'));
  const vesumLemmas = existsSync(VESUM_LEMMAS_URL)
    ? JSON.parse(readFileSync(VESUM_LEMMAS_URL, 'utf8'))
    : { form_to_lemma: {} };

  cachedResolver = createEtymologyResolver({ manifest, vesumLemmas });
  return cachedResolver;
}

export function cleanVocabWord(value) {
  return String(value ?? '')
    .replace(/\s+/g, ' ')
    .trim();
}

export function isSingleVocabToken(value) {
  const cleaned = cleanVocabWord(value);
  return cleaned.length > 0 && !/\s/.test(cleaned);
}

export function resolveVocabWord(value, resolver = loadDefaultEtymologyResolver()) {
  const cleaned = cleanVocabWord(value);
  if (!isSingleVocabToken(cleaned)) return null;

  const directKey = normalizeLemma(cleaned);
  const direct = resolver.lemmaRoutes.get(directKey);
  if (direct) {
    return {
      ...direct,
      source: 'manifest',
      matchedLemma: direct.lemma,
    };
  }

  const candidateForms = new Set([directKey, stripReflexiveSuffix(directKey)]);
  for (const formKey of candidateForms) {
    const lemma = resolver.vesumLemmas.get(formKey);
    if (!lemma) continue;

    const route = resolver.lemmaRoutes.get(normalizeLemma(lemma));
    if (route) {
      return {
        ...route,
        source: 'vesum',
        matchedLemma: lemma,
      };
    }
  }

  return null;
}
