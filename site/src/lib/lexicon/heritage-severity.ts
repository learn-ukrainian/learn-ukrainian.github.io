import browseMeta from "../../data/lexicon-browse-meta.json";

export type WarningSeverity =
  | "none"
  | "treasured"
  | "calque_yellow"
  | "russianism_red"
  | "soviet_def_blue";

export interface HeritageAttestation {
  source?: string;
  ref?: string;
  detail?: string;
}

export interface HeritageStatus {
  classification?: string;
  attestations?: HeritageAttestation[];
  is_russianism?: boolean;
  russian_shadow?: boolean;
  vesum_attested?: boolean;
  warning_severity?: WarningSeverity;
  calque_warning?: {
    kind?: string;
    note?: string;
    noteUk?: string;
    detail?: string;
    standard_alternatives?: string[];
    calque_sense?: string;
    authentic_sense?: string;
    citations?: string[];
    evidence?: string[];
  } | null;
  curated_calque?: {
    kind?: string;
    corrections?: string[];
    note?: string;
    noteUk?: string;
    source?: string[];
    calque_sense?: string;
    evidence?: string[];
  } | null;
  "§6_note"?: {
    corrections?: string[];
    note?: string;
    noteUk?: string;
    source?: string[];
  } | null;
  reverse_calques?: Array<{
    calque: string;
    kind?: string;
    note?: string;
    noteUk?: string;
    source?: string[];
    calque_sense?: string;
  }> | null;
}

export interface DefinitionCard {
  id?: string;
  definitions?: string[];
  sovietization_risk?: number;
  sovietization_keywords?: string[];
}

export interface LexiconEntryForSeverity {
  lemma?: string;
  gloss?: string | null;
  primary_source?: string | null;
  form_of?: unknown;
  heritage_status?: HeritageStatus | null;
  enrichment?: { definition_cards?: DefinitionCard[] | null } | null;
}

/** A reviewed directional judgment bound by digest to a source passage (#9603). */
export interface SourceJudgment {
  locator: string;
  passage: string;
  passageSha256: string;
  rejectedForm: string;
  endorsedForm: string;
  sense: string;
}

/**
 * Current curated source proof for one headword: the ``usageSources``
 * projection in browse meta (``usage_source_records`` in
 * scripts/lexicon/heritage_classifier.py). Citations stored in an old Atlas
 * record are provenance, never authority.
 */
export interface UsageSourceProof {
  kind: string;
  corrections: string[];
  sense: string;
  judgments: SourceJudgment[];
  citations: Array<{ locator: string; excerpt: string }>;
}

const USAGE_SOURCES: Record<string, UsageSourceProof> =
  (browseMeta as { usageSources?: { records?: Record<string, UsageSourceProof> } }).usageSources?.records ?? {};

/** The projected source proof for ``headword``, or ``null``. */
export function usageSourceProof(headword: string | undefined): UsageSourceProof | null {
  return USAGE_SOURCES[normalizeWord(headword ?? "")] ?? null;
}

/** Where a usage label applies (#9603; mirrors ``resolve_usage_label``). */
export type UsageLabelScope = "lemma" | "sense" | "phrase" | "reverse" | "unresolved" | "none";

export interface UsageLabel {
  code: "rus" | "calq" | "arch" | "dial" | "hist" | "borr" | null;
  scope: UsageLabelScope;
  authority: string[];
  evidence: string | null;
  reason: string;
}

export interface HeritageBox {
  severity: Exclude<WarningSeverity, "none">;
  title: string;
  body: string;
  alternatives?: string[];
  detail?: string;
  dataSeverity: "red" | "yellow" | "green" | "blue";
  /** ``lemma`` boxes describe the headword; ``sense``/``phrase`` one use of it. */
  scope?: UsageLabelScope;
}

export interface HeritageBoxes {
  red?: HeritageBox;
  yellow?: HeritageBox;
  green?: HeritageBox;
  blue?: HeritageBox;
  inline?: {
    severity: HeritageBox["dataSeverity"];
    label: string;
  };
  /** The source-scoped usage label behind these boxes. */
  usageLabel: UsageLabel;
}

const AUTHENTIC_CLASSIFICATIONS = new Set([
  "authentic-archaism",
  "dialect",
  "historism",
  "borrowing",
  "standard",
]);

const TREASURED_CLASSIFICATIONS = new Set([
  "authentic-archaism",
  "dialect",
  "historism",
  "borrowing",
]);

const POSITIVE_ATTESTATION_SOURCES = new Set(["vesum", "esum", "гринченко", "есум"]);
const POSITIVE_ATTESTATION_PREFIXES = ["grinchenko", "literary"];
export const SURZHYK_TO_AVOID_SOURCE = "surzhyk_to_avoid";

// --- Usage-label scope (#9603). Mirrors scripts/lexicon/heritage_classifier.py
// ``resolve_usage_label``; contract: docs/atlas/usage-label-scope.md.
const USAGE_LABEL_CODES: Record<string, UsageLabel["code"]> = {
  russianism: "rus",
  calque: "calq",
  "authentic-archaism": "arch",
  archaism: "arch",
  dialect: "dial",
  historism: "hist",
  borrowing: "borr",
};
const CONTEXTUAL_CALQUE_SCOPES: Record<string, UsageLabelScope> = { sense_restricted: "sense", phrasal: "phrase" };
// The only curated kind that claims the whole word; ``participle`` is a
// word-formation type, not a scope.
const LEMMA_CALQUE_KINDS = new Set(["lexical"]);
const UNRESOLVED_CLAIM_REASONS = new Set([
  "no_lemma_scoped_authority",
  "no_headword_bound_evidence",
  "curated_kind_without_scope",
]);
const WORD_RE = /[а-яіїєґʼ'a-z]+(?:-[а-яіїєґʼ'a-z]+)*/gu;
const MIN_REFERENT_TOKEN_LEN = 5;
const LETTER_CLASS = "а-яіїєґa-z";
const USAGE_MARKER_RES: Record<string, RegExp> = {
  historism: new RegExp(`(?<![${LETTER_CLASS}])(?:іст|істор)\\.`, "u"),
  dialect: new RegExp(`(?<![${LETTER_CLASS}])діал\\.`, "u"),
  "authentic-archaism": new RegExp(`(?<![${LETTER_CLASS}])(?:заст\\.|застар|архаї)`, "u"),
};
const MODERN_DICTIONARY_CARDS: Array<[string, string]> = [["sum20", "СУМ-20"], ["vts", "ВТС"]];
const SUPERSCRIPT_DIGITS = "¹²³⁴⁵⁶⁷⁸⁹⁰";
const HOMONYM_INDEX_RE = /^(?:[¹²³⁴⁵⁶⁷⁸⁹⁰]+|I|II|III|IV|V)[,.]?$/u;
const SENSE_START_RE = /^(?:\d|[《◊/]|[А-ЯІЇЄҐA-Z])/u;
const SECOND_SENSE_RE = /(?<!\S)2[.)]/u;
const EDGE_CHARS = new Set([..."¹²³⁴⁵⁶⁷⁸⁹⁰,.;:!?«»\"'()[]"]);
// The word, its marker, then a «gloss» or a parenthesised explanation (``тіун (іст.) (…)``).
const ESUM_HEADWORD_SLOT_RE =
  /^\s*(?<word>[^\s(«]+)\s*\((?<marker>[^)]{1,40})\)\s*(?:«(?<gloss>[^»]{1,200})»|\((?<explanation>[^()]{1,300})\))/u;
const ESUM_REF_RE = /^[^:]*:(?<volume>\d+):(?<page>\d+)$/u;
const ACUTE_RE = /[́̀]/gu;

function citationList(value: unknown): string[] {
  if (typeof value === "string") return value.trim() ? [value] : [];
  if (Array.isArray(value)) return value.map((item) => String(item ?? "")).filter((item) => item.trim());
  return [];
}

function normalizeWord(text: string): string {
  return String(text ?? "")
    .normalize("NFC")
    .replace(ACUTE_RE, "")
    .toLocaleLowerCase("uk")
    .replace(/`/g, "'")
    .replace(/’/g, "ʼ")
    .replace(/\s+/g, " ")
    .trim();
}

function words(text: string): string[] {
  return normalizeWord(text).replace(/ʼ/g, "'").match(WORD_RE) ?? [];
}

function usageMarkerClasses(text: string): Set<string> {
  return new Set(Object.keys(USAGE_MARKER_RES).filter((name) => USAGE_MARKER_RES[name].test(text)));
}

function stripEdges(token: string): string {
  const chars = [...token];
  let start = 0;
  let end = chars.length;
  while (start < end && EDGE_CHARS.has(chars[start])) start += 1;
  while (end > start && EDGE_CHARS.has(chars[end - 1])) end -= 1;
  return chars.slice(start, end).join("");
}

/** True when a dictionary card's leading headword is ``headword``. */
export function cardHeadwordMatches(definition: string, headword: string | undefined): boolean {
  const head = normalizeWord(headword ?? "").split(" ").filter(Boolean);
  const tokens = String(definition ?? "").replace(ACUTE_RE, "").split(/\s+/).filter(Boolean);
  if (head.length === 0 || tokens.length < head.length) return false;
  return head.every((word, index) => normalizeWord(stripEdges(tokens[index])) === word);
}

/** Usage-label classes in a СУМ-20/ВТС headword slot, plus an ambiguity flag. */
export function modernHeadwordLabels(definition: string): { classes: Set<string>; ambiguous: boolean } {
  const plain = definition.replace(ACUTE_RE, "");
  const tokens = plain.split(/\s+/).filter(Boolean);
  const slot: string[] = [];
  let ambiguous = tokens.length > 0 && [...tokens[0]].some((char) => SUPERSCRIPT_DIGITS.includes(char));
  for (const [index, token] of tokens.entries()) {
    if (HOMONYM_INDEX_RE.test(token)) {
      ambiguous = true;
      continue;
    }
    if (index === 0) continue;
    if (SENSE_START_RE.test(token)) break;
    slot.push(token);
  }
  if (/(?<!\S)II(?!\S)/u.test(plain)) ambiguous = true;
  return { classes: usageMarkerClasses(normalizeWord(slot.join(" "))), ambiguous };
}

function modernDictionaryCard(
  cards: DefinitionCard[] | null | undefined,
  headword: string | undefined,
): [string, string] | null {
  for (const [cardId, label] of MODERN_DICTIONARY_CARDS) {
    for (const card of cards ?? []) {
      if (card?.id !== cardId) continue;
      for (const definition of card.definitions ?? []) {
        if (typeof definition === "string" && definition.trim() && cardHeadwordMatches(definition, headword)) {
          return [label, definition];
        }
      }
    }
  }
  return null;
}

function esumLocator(ref: unknown): string {
  const match = String(ref ?? "").match(ESUM_REF_RE);
  return match?.groups ? `ЕСУМ, т. ${match.groups.volume}, с. ${match.groups.page}` : "ЕСУМ";
}

/** True when two glosses share a content word (five letters or more). */
export function sharesReferent(sourceGloss: string, articleGloss: string | null | undefined): boolean {
  const source = new Set(words(sourceGloss).filter((word) => word.length >= MIN_REFERENT_TOKEN_LEN));
  return words(articleGloss ?? "").some((word) => word.length >= MIN_REFERENT_TOKEN_LEN && source.has(word));
}

function esumHeadwordMarker(
  status: HeritageStatus,
  markerClass: string,
  headword: string | undefined,
  gloss: string | null | undefined,
): UsageLabel | null {
  const head = normalizeWord(headword ?? "");
  if (!head) return null;
  for (const attestation of status.attestations ?? []) {
    const source = String(attestation.source ?? "").toLocaleLowerCase("uk");
    if (source !== "esum" && source !== "есум") continue;
    if (normalizeWord(String((attestation as { word?: string }).word ?? "")) !== head) continue;
    const match = String(attestation.detail ?? "").replace(ACUTE_RE, "").match(ESUM_HEADWORD_SLOT_RE);
    if (!match?.groups || normalizeWord(match.groups.word) !== head) continue;
    if (!usageMarkerClasses(normalizeWord(match.groups.marker)).has(markerClass)) continue;
    if (!sharesReferent(match.groups.gloss ?? match.groups.explanation, gloss)) continue;
    return usageLabel(USAGE_LABEL_CODES[markerClass], "lemma", [esumLocator(attestation.ref)], match[0].trim());
  }
  return null;
}

function usageLabel(
  code: UsageLabel["code"],
  scope: UsageLabelScope,
  authority: string[],
  evidence: unknown,
  reason = "",
): UsageLabel {
  return { code, scope, authority, evidence: evidence ? String(evidence) : null, reason: reason || scope };
}

function treasuredLabel(
  status: HeritageStatus,
  classification: string,
  headword: string | undefined,
  cards: DefinitionCard[] | null | undefined,
  gloss: string | null | undefined,
): UsageLabel {
  if (classification === "borrowing") {
    for (const attestation of status.attestations ?? []) {
      const word = String((attestation as { word?: string }).word ?? "");
      if (
        attestation.source === "esum" &&
        headword &&
        normalizeWord(word) === normalizeWord(headword) &&
        normalizeWord(String(attestation.detail ?? "")).includes("запозич")
      ) {
        return usageLabel("borr", "lemma", [esumLocator(attestation.ref)], attestation.detail);
      }
    }
    return usageLabel(null, "unresolved", [], null, "no_headword_etymology");
  }
  const code = USAGE_LABEL_CODES[classification];
  const markerClass = code === "arch" ? "authentic-archaism" : classification;
  // A headword-slot label on the modern card for the same headword binds. An
  // ЕСУМ headword-slot marker with the same referent is a historical witness.
  // The modern card decides current register (archaism, dialect); a historism
  // names a historical referent, which an unlabelled single-sense card does
  // not contradict. Грінченко and VESUM stay attestations.
  const modern = modernDictionaryCard(cards, headword);
  let wholeWord = true;
  if (modern) {
    const [sourceLabel, definition] = modern;
    const { classes, ambiguous } = modernHeadwordLabels(definition);
    if (!ambiguous && classes.has(markerClass)) {
      return usageLabel(code, "lemma", [sourceLabel], definition.slice(0, 240));
    }
    wholeWord = markerClass === "historism" && !ambiguous && !SECOND_SENSE_RE.test(definition.replace(ACUTE_RE, ""));
  }
  const witness = esumHeadwordMarker(status, markerClass, headword, gloss);
  if (witness) {
    return wholeWord ? witness : { ...witness, code: null, scope: "unresolved", reason: "source_marker_not_whole_word" };
  }
  return usageLabel(null, "unresolved", [], null, modern ? `${modern[0]}_headword_unlabelled` : "no_headword_bound_label");
}

function curatedReferences(status: HeritageStatus | null): string[] {
  const record = status ? curatedScopeRecord(status) : null;
  if (!record) return [];
  return unique([
    ...citationList((record as { source?: unknown }).source),
    ...citationList((record as { citations?: unknown }).citations),
  ]);
}

function curatedScopeRecord(status: HeritageStatus) {
  for (const record of [status.curated_calque, status.calque_warning]) {
    if (record && String(record.kind ?? "").trim()) return record;
  }
  return null;
}

/**
 * Resolve the source-scoped usage label for a heritage record (#9603).
 *
 * ``code`` is set only for ``scope === "lemma"``. A Russianism or calque needs
 * a reviewed judgment in ``sourceProof`` whose rejected form is the headword;
 * citations stored in the record are never authority. Stored
 * ``warning_severity`` is never trusted; without a headword nothing binds.
 */
export function resolveUsageLabel(
  status: HeritageStatus | null | undefined,
  options: {
    headword?: string;
    definitionCards?: DefinitionCard[] | null;
    gloss?: string | null;
    sourceProof?: UsageSourceProof | null;
  } = {},
): UsageLabel {
  const record = status ?? {};
  const classification = record.classification ?? "unknown";
  let treasured: UsageLabel | null = null;
  const treasuredCode = USAGE_LABEL_CODES[classification];
  if (treasuredCode && treasuredCode !== "rus" && treasuredCode !== "calq") {
    treasured = treasuredLabel(record, classification, options.headword, options.definitionCards, options.gloss);
    if (treasured.scope === "lemma") return treasured;
  }

  const proof = options.sourceProof ?? null;
  const curated = proof?.kind ? proof : curatedScopeRecord(record);
  if (curated) {
    const kind = String(curated.kind).trim();
    const head = normalizeWord(options.headword ?? "");
    const judgments = (proof?.judgments ?? []).filter((item) => head && normalizeWord(item.rejectedForm) === head);
    const authority = unique([...judgments, ...(proof?.citations ?? [])].map((item) => item.locator));
    const contextual = CONTEXTUAL_CALQUE_SCOPES[kind];
    if (contextual) {
      const stored = curated as { calque_sense?: string; note?: string };
      return usageLabel(null, contextual, authority, proof?.sense || stored.calque_sense || stored.note);
    }
    if (!LEMMA_CALQUE_KINDS.has(kind)) return usageLabel(null, "unresolved", [], null, "curated_kind_without_scope");
    if (judgments.length === 0) return usageLabel(null, "unresolved", [], null, "no_headword_bound_evidence");
    const isRus = Boolean(record.is_russianism) && !AUTHENTIC_CLASSIFICATIONS.has(classification);
    const passage = judgments[0].passage;
    return usageLabel(isRus ? "rus" : "calq", "lemma", authority, passage.length > 240 ? `${passage.slice(0, 240)}…` : passage);
  }

  if (
    record.is_russianism ||
    classification === "russianism" ||
    classification === "calque" ||
    hasCalqueAlternative(record)
  ) {
    return usageLabel(null, "unresolved", [], null, "no_lemma_scoped_authority");
  }
  if (treasured) return treasured;
  if (hasReverseCalque(record)) return usageLabel(null, "reverse", [], null);
  return usageLabel(null, "none", [], null);
}

function nonEmptyStrings(values: unknown): string[] {
  if (!Array.isArray(values)) return [];
  return values.map((value) => String(value).trim()).filter(Boolean);
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values));
}

function hasPositiveAttestation(status: HeritageStatus | null | undefined): boolean {
  return Boolean(
    status?.attestations?.some((attestation) => {
      const source = String(attestation.source ?? "").trim().toLocaleLowerCase("uk");
      return (
        POSITIVE_ATTESTATION_SOURCES.has(source) ||
        POSITIVE_ATTESTATION_PREFIXES.some((prefix) => source.startsWith(prefix))
      );
    }),
  );
}

/** Replacement candidates recorded on the headword (any scope). */
export function standardAlternatives(status: HeritageStatus | null | undefined, gloss: string | null): string[] {
  const calqueWarning = nonEmptyStrings(status?.calque_warning?.standard_alternatives);
  if (calqueWarning.length > 0) return unique(calqueWarning);

  const curated = nonEmptyStrings(status?.curated_calque?.corrections);
  if (curated.length > 0) return unique(curated);

  const sectionSix = nonEmptyStrings(status?.["§6_note"]?.corrections);
  if (sectionSix.length > 0) return unique(sectionSix);

  const avoidMatch = String(gloss ?? "").match(/\bavoid:\s*([^.;]+)/i);
  if (!avoidMatch) return [];

  return unique(
    avoidMatch[1]
      .split(/\s*\/\s*|\s*,\s*/)
      .map((value) => value.trim())
      .filter(Boolean),
  );
}

function hasCalqueAlternative(status: HeritageStatus | null | undefined): boolean {
  return (
    nonEmptyStrings(status?.curated_calque?.corrections).length > 0 ||
    nonEmptyStrings(status?.calque_warning?.standard_alternatives).length > 0 ||
    nonEmptyStrings(status?.["§6_note"]?.corrections).length > 0
  );
}

function hasReverseCalque(status: HeritageStatus | null | undefined): boolean {
  return (status?.reverse_calques?.length ?? 0) > 0;
}

function maxSovietizationRisk(entry: LexiconEntryForSeverity): number {
  const cards = entry.enrichment?.definition_cards ?? [];
  return cards.reduce((risk, card) => Math.max(risk, Number(card.sovietization_risk ?? 0)), 0);
}

/** Severity from the scoped label; mirrors ``compute_warning_severity``. */
function scopedSeverity(status: HeritageStatus | null | undefined, label: UsageLabel): WarningSeverity {
  if (!status) return "none";
  if (label.scope === "lemma" && label.code === "rus") return "russianism_red";
  if ((label.scope === "lemma" && label.code === "calq") || label.scope === "sense" || label.scope === "phrase") {
    return "calque_yellow";
  }
  // An unresolved Russianism/calque claim is neutral: no warning and no defence.
  if (label.scope === "unresolved" && UNRESOLVED_CLAIM_REASONS.has(label.reason)) return "none";
  const classification = status.classification ?? "unknown";
  if (
    TREASURED_CLASSIFICATIONS.has(classification) ||
    (classification === "standard" && hasPositiveAttestation(status))
  ) {
    return "treasured";
  }
  return "none";
}

// Visible wording follows each source's evidential role (#9603): VESUM
// attests a form's morphology, not its origin or normativity.
const REGISTER_TITLES: Partial<Record<NonNullable<UsageLabel["code"]>, string>> = {
  dial: "Діалектне слово",
  borr: "Запозичення",
  hist: "Історизм",
  arch: "Архаїзм",
};
const ATTESTED_FORM_TITLE = "Засвідчена українська форма";

function attestationRole(source: string): string | null {
  const key = source.trim().toLocaleLowerCase("uk");
  if (key === "vesum") return "VESUM (морфологічна фіксація форми)";
  if (key === "esum" || key === "есум") return "ЕСУМ (етимологічний словник)";
  if (key === "гринченко" || key.startsWith("grinchenko")) return "Словник Грінченка (1907–1909)";
  if (key.startsWith("literary")) return "художні тексти";
  return null;
}

function greenTitle(label: UsageLabel): string {
  return (label.scope === "lemma" && label.code && REGISTER_TITLES[label.code]) || ATTESTED_FORM_TITLE;
}

function greenBody(status: HeritageStatus, label: UsageLabel): string {
  const shadow = status.russian_shadow
    ? " Російська морфологічна тінь сама по собі не є підставою для попередження."
    : "";
  if (label.scope === "lemma" && label.code && REGISTER_TITLES[label.code]) {
    const excerpt = label.evidence ? `: ${label.evidence.trim()}` : "";
    return `Позначка стоїть у заголовку словникової статті про це слово${excerpt}.${authorityClause(label.authority)}${shadow}`;
  }
  const roles = unique(
    (status.attestations ?? [])
      .map((attestation) => attestationRole(String(attestation.source ?? "")))
      .filter((role): role is string => Boolean(role)),
  );
  const where = roles.length > 0 ? ` Засвідчення: ${roles.join("; ")}.` : "";
  return `Форму зафіксовано в джерелах.${where} Фіксація не визначає походження слова чи його нормативність.${shadow}`;
}

function authorityClause(authority: string[]): string {
  return authority.length > 0 ? ` Джерело: ${authority.join(", ")}.` : "";
}

function scopedCalqueTitle(scope: UsageLabelScope): string {
  if (scope === "sense") return "Калькове застереження щодо окремого значення";
  if (scope === "phrase") return "Калькове застереження щодо сполучення";
  return "Калькове застереження";
}

const NO_BOUND_AUTHORITY = " Перевіреного витягу з нормативного джерела запис не містить.";

function referencesClause(references: string[]): string {
  return references.length > 0 ? ` Посилання запису Атласу, не звірені з джерелом: ${references.join(", ")}.` : "";
}

function scopedCalqueBody(label: UsageLabel, alternatives: string[], references: string[]): string {
  if (label.scope === "sense" || label.scope === "phrase") {
    const where =
      label.scope === "sense"
        ? `окремого значення${label.evidence ? ` («${label.evidence}»)` : ""}`
        : `сполучення${label.evidence ? ` («${label.evidence}»)` : ""}`;
    const who = label.authority.length > 0 ? "джерело радить" : "Атлас пропонує (без звірки з джерелом)";
    const use = alternatives.length > 0 ? ` У цьому вжитку ${who}: ${alternatives.join(", ")}.` : "";
    const authority =
      label.authority.length > 0 ? authorityClause(label.authority) : `${NO_BOUND_AUTHORITY}${referencesClause(references)}`;
    return `Застереження стосується ${where}, а не слова загалом.${use}${authority}`;
  }
  const use = alternatives.length > 0 ? `Рекомендовані відповідники: ${alternatives.join(", ")}.` : "Перевіряйте відповідники в джерелах.";
  return `${use}${authorityClause(label.authority)}`;
}

const EDITORIAL_GLOSS_RE = /^\s*(avoid|rus|calque)\s*:\s*(\S.*?)\s*$/isu;
const EDITORIAL_GLOSS_LEADS: Record<string, string> = { avoid: "радять", rus: "русизм —", calque: "калька —" };
const EMBEDDED_NORM_RE = /\(([^()]*\b(?:calque|russianism|surzhyk|standard Ukrainian)\b[^()]*)\)/giu;

/**
 * The gloss as displayed (#9603; mirrors ``display_gloss`` in
 * scripts/audit/generate_search_index.py). An ``avoid:``/``rus:``/``calque:`` gloss or
 * embedded ``(… calque …)`` clause reads as a word-wide instruction, so it stays verbatim
 * only for a lemma-bound Russianism or calque; otherwise it is a qualified Atlas note
 * beside the meaning. ``note`` marks that text; the stored gloss is unchanged.
 */
export function displayGloss(gloss: string | null | undefined, label: UsageLabel): { text: string; note: boolean } | null {
  if (!gloss) return null;
  if (label.scope === "lemma" && (label.code === "rus" || label.code === "calq")) return { text: gloss, note: false };
  const match = gloss.match(EDITORIAL_GLOSS_RE);
  if (!match) {
    const text = gloss.replace(EMBEDDED_NORM_RE, "(примітка Атласу: «$1»; обсяг застереження не встановлено)");
    return { text, note: text !== gloss };
  }
  const lead = EDITORIAL_GLOSS_LEADS[match[1].toLowerCase()];
  return { text: `примітка Атласу: ${lead} «${match[2]}»; обсяг застереження не встановлено`, note: true };
}

/** Atlas prose stored with a record is commentary, never a source excerpt (#9603). */
export function atlasNoteDetail(note: string | undefined): string | undefined {
  return note?.trim() ? `Примітка Атласу, не підтверджена витягом із джерела: ${note.trim()}` : undefined;
}

export function resolveHeritageBoxes(
  entry: LexiconEntryForSeverity,
  sourceProof: UsageSourceProof | null = usageSourceProof(entry.lemma),
): HeritageBoxes {
  const status = entry.heritage_status ?? null;
  const definitionCards = entry.enrichment?.definition_cards ?? null;
  const label = resolveUsageLabel(status, { headword: entry.lemma, definitionCards, gloss: entry.gloss, sourceProof });
  if (entry.form_of) return { usageLabel: label };

  const sovietizationRisk = maxSovietizationRisk(entry);
  // The avoid list is provenance, not authority: it only strengthens a
  // Russianism/calque that source evidence already binds to the headword.
  const avoid =
    entry.primary_source === SURZHYK_TO_AVOID_SOURCE &&
    label.scope === "lemma" &&
    (label.code === "rus" || label.code === "calq");
  const severity = avoid ? "russianism_red" : scopedSeverity(status, label);
  const boxes: HeritageBoxes = { usageLabel: label };
  const alternatives = sourceProof?.corrections.length
    ? sourceProof.corrections
    : standardAlternatives(status, entry.gloss ?? null);

  if (severity === "russianism_red") {
    const authority = [...label.authority, ...(avoid ? ["Атлас: перелік суржику, якого слід уникати"] : [])];
    boxes.red = {
      severity,
      dataSeverity: "red",
      scope: "lemma",
      title: "Редакційне попередження",
      body:
        (alternatives.length > 0
          ? `Джерело позначає цю форму як ненормативну. Рекомендовані відповідники: ${alternatives.join(", ")}.`
          : "Джерело позначає цю форму як ненормативну. Перевіряйте рекомендовані відповідники в джерелах.") +
        authorityClause(authority) +
        (label.evidence ? ` Витяг: «${label.evidence.trim()}»` : ""),
      alternatives,
    };
  } else if (severity === "calque_yellow") {
    boxes.yellow = {
      severity: "calque_yellow",
      dataSeverity: "yellow",
      scope: label.scope,
      title: scopedCalqueTitle(label.scope),
      body: scopedCalqueBody(label, alternatives, curatedReferences(status)),
      alternatives,
      detail: atlasNoteDetail(
        status?.curated_calque?.noteUk ??
          status?.["§6_note"]?.noteUk ??
          status?.calque_warning?.noteUk ??
          status?.calque_warning?.detail ??
          status?.calque_warning?.note,
      ),
    };
  } else if (severity === "treasured") {
    boxes.green = {
      severity,
      dataSeverity: "green",
      title: greenTitle(label),
      body: greenBody(status ?? {}, label),
    };
  }

  if (sovietizationRisk > 0 || status?.warning_severity === "soviet_def_blue") {
    boxes.blue = {
      severity: "soviet_def_blue",
      dataSeverity: "blue",
      title: "Редакторський прапорець у СУМ-11",
      body: "СУМ-11 показано для прозорості, але ця картка має ознаки радянської редакторської політики. Це не означає, що саме слово негативне.",
      detail: `sovietization_risk=${sovietizationRisk}`,
    };
  }

  if (boxes.red) {
    boxes.inline = { severity: "red", label: "⚠ Потребує українського відповідника" };
  } else if (boxes.yellow && boxes.yellow.scope === "lemma") {
    boxes.inline = { severity: "yellow", label: "Калькове застереження" };
  } else if (boxes.green) {
    // The register itself is a separate badge; the inline badge states attestation only.
    boxes.inline = { severity: "green", label: `✓ ${ATTESTED_FORM_TITLE}` };
  } else if (boxes.blue) {
    boxes.inline = { severity: "blue", label: "СУМ-11: редакторський прапорець" };
  }

  return boxes;
}
