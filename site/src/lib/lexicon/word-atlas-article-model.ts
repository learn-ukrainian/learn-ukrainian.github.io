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
}

export type MorphologyParadigm = NounParadigm | VerbParadigm | { kind: "other" };

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

export function formatPos(pos: string | null | undefined, morphologyPos: string | undefined) {
  const labels: Record<string, string> = {
    noun: "іменник",
    verb: "дієслово",
    adj: "прикметник",
    adverb: "прислівник",
    adv: "прислівник",
    phrase: "фраза",
    pron: "займенник",
    pronoun: "займенник",
    prep: "прийменник",
    conj: "сполучник",
    particle: "частка",
    interjection: "вигук",
  };
  return morphologyPos ?? (pos ? labels[pos] ?? pos : null);
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
) {
  const entry = record.entry as unknown as LexiconEntryView;
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
  const posLabel = formatPos(entry.pos, enrichment?.morphology?.pos);
  const headwordIpa = formatIpa(entry.pronunciation?.ipa ?? entry.ipa);
  const heritageBoxes = resolveHeritageBoxes(entry);
  const etymologyStages = buildEtymologyStages(enrichment?.etymology, entry.lemma);
  const courseUsage = entry.course_usage.slice().sort((a, b) => {
    if (a.track !== b.track) return a.track.localeCompare(b.track);
    return a.module_num - b.module_num;
  });
  const textbookItems = enrichment?.textbooks ?? [];
  const externalGroups = groupExternalMaterials(enrichment?.external_materials ?? []);
  const componentLinks = record.renderContext.componentLinks;
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
  });
  const sourceList = buildSourceList({
    entry,
    enrichment,
    definitionCards,
    sections,
  });
  const hasPractice = record.renderContext.practiceLevels.length > 0;

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
    markedFormGroups,
    isFullyMarked,
    isExpressionLikeEntry,
    suppressMorphology,
    entryTypeLabel,
    posLabel,
    headwordIpa,
    heritageBoxes,
    etymologyStages,
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
  } = args;
  const synonymCount =
    (sections?.synonyms?.items.length ?? 0) + (sections?.antonyms?.items.length ?? 0);
  const homonymCount = sections?.homonyms?.items.length ?? 0;
  const paronymCount = sections?.paronyms?.items.length ?? 0;
  const idiomCount = sections?.idioms?.items.length ?? 0;
  const externalCount = externalGroups.reduce((total, group) => total + group.materials.length, 0);
  const definitionCount =
    definitionCards.length + (enrichment?.meaning ? 1 : 0) + (phraseHasGloss ? 1 : 0);
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
      ready: Boolean(enrichment?.etymology),
      detail: enrichment?.etymology?.source ?? "очікує джерело",
    },
    {
      label: "Морфологія",
      ready: Boolean(enrichment?.morphology),
      detail: enrichment?.morphology
        ? morphologyFormCountLabel(enrichment.morphology, isFullyMarked)
        : "очікує VESUM",
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
      ready: (enrichment?.translation?.en.length ?? 0) > 0,
      detail:
        (enrichment?.translation?.en.length ?? 0) > 0
          ? `${enrichment?.translation?.en.length} англ.`
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
  for (const source of enrichment?.sources ?? []) sources.add(source);
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
  if (enrichment?.literary_attestation?.source) sources.add(enrichment.literary_attestation.source);
  if (enrichment?.translation?.source) sources.add(enrichment.translation.source);
  if (entry.course_usage.length > 0) sources.add("curriculum_vocabulary");
  if (entry.wiki_reference?.wikipedia) sources.add("query_wikipedia");
  if (entry.wiki_reference?.wiktionary_url) sources.add("uk.wiktionary");
  return Array.from(sources).sort((a, b) => a.localeCompare(b, "uk"));
}
