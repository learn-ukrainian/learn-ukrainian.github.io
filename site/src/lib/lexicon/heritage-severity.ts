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
  } | null;
  curated_calque?: {
    kind?: string;
    corrections?: string[];
    note?: string;
    noteUk?: string;
    source?: string[];
    calque_sense?: string;
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
const SURZHYK_TO_AVOID_SOURCE = "surzhyk_to_avoid";

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
const CONTEXTUAL_CALQUE_SCOPES: Record<string, UsageLabelScope> = {
  sense_restricted: "sense",
  phrasal: "phrase",
};
const NORMATIVE_CITATION_FAMILIES = ["antonenko", "davydov", "karavansk", "voloshchak", "voloschak"];
const NORMATIVE_TEXTBOOK_RE = /^(?:avramenko|zabolotnyi|glazova|litvinova|voron)-(?:[1-9]|1[01])$/;
const CITATION_TOKEN_RE = /[a-z0-9]+(?:[-_][a-z0-9]+)*/g;
const LETTER_CLASS = "а-яіїєґa-z";
const USAGE_MARKER_RES: Record<string, RegExp> = {
  historism: new RegExp(`(?<![${LETTER_CLASS}])(?:іст|істор)\\.`, "u"),
  dialect: new RegExp(`(?<![${LETTER_CLASS}])діал\\.`, "u"),
  "authentic-archaism": new RegExp(`(?<![${LETTER_CLASS}])(?:заст\\.|застар|архаї)`, "u"),
};
const MODERN_DICTIONARY_CARDS: Array<[string, string]> = [
  ["sum20", "СУМ-20"],
  ["vts", "ВТС"],
];
const HOMONYM_INDEX_RE = /^(?:[¹²³⁴⁵⁶⁷⁸⁹]+|I|II|III|IV|V)[,.]?$/u;
const SENSE_START_RE = /^(?:\d|[《◊/]|[А-ЯІЇЄҐA-Z])/u;
const ACUTE_RE = /[\u0301\u0300]/gu;

function citationList(value: unknown): string[] {
  if (typeof value === "string") return value.trim() ? [value] : [];
  if (Array.isArray(value)) return value.map((item) => String(item ?? "")).filter((item) => item.trim());
  return [];
}

export function normativeCitations(citations: unknown): string[] {
  return citationList(citations).filter((citation) =>
    (citation.toLocaleLowerCase("en").match(CITATION_TOKEN_RE) ?? []).some(
      (token) =>
        NORMATIVE_CITATION_FAMILIES.some((family) => token.startsWith(family)) ||
        NORMATIVE_TEXTBOOK_RE.test(token),
    ),
  );
}

function normalizeWord(text: string): string {
  return text.normalize("NFC").replace(ACUTE_RE, "").toLocaleLowerCase("uk").replace(/\s+/g, " ").trim();
}

function usageMarkerClasses(text: string): Set<string> {
  return new Set(
    Object.entries(USAGE_MARKER_RES)
      .filter(([, pattern]) => pattern.test(text))
      .map(([name]) => name),
  );
}

/** Usage-label classes in a СУМ-20/ВТС headword slot, plus an ambiguity flag. */
export function modernHeadwordLabels(definition: string): { classes: Set<string>; ambiguous: boolean } {
  const plain = definition.replace(ACUTE_RE, "");
  const tokens = plain.split(/\s+/).filter(Boolean);
  const slot: string[] = [];
  let ambiguous = false;
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

function modernDictionaryCard(cards: DefinitionCard[] | null | undefined): [string, string] | null {
  for (const [cardId, label] of MODERN_DICTIONARY_CARDS) {
    for (const card of cards ?? []) {
      const first = card?.id === cardId ? card.definitions?.[0] : undefined;
      if (typeof first === "string" && first.trim()) return [label, first];
    }
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
        return usageLabel("borr", "lemma", [`ЕСУМ ${attestation.ref}`], attestation.detail);
      }
    }
    return usageLabel(null, "unresolved", [], null, "no_headword_etymology");
  }
  const code = USAGE_LABEL_CODES[classification];
  const markerClass = code === "arch" ? "authentic-archaism" : classification;
  const modern = modernDictionaryCard(cards);
  if (!modern) return usageLabel(null, "unresolved", [], null, "no_modern_dictionary_label");
  const [sourceLabel, definition] = modern;
  const { classes, ambiguous } = modernHeadwordLabels(definition);
  if (!ambiguous && classes.has(markerClass)) {
    return usageLabel(code, "lemma", [sourceLabel], definition.slice(0, 240));
  }
  return usageLabel(null, "unresolved", [], null, `${sourceLabel}_headword_unlabelled`);
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
 * ``code`` is set only for ``scope === "lemma"``: a named authority with
 * evidence that its claim covers the whole headword. Stored
 * ``warning_severity`` is never trusted on its own.
 */
export function resolveUsageLabel(
  status: HeritageStatus | null | undefined,
  options: { headword?: string; definitionCards?: DefinitionCard[] | null } = {},
): UsageLabel {
  const record = status ?? {};
  const classification = record.classification ?? "unknown";
  let treasured: UsageLabel | null = null;
  const treasuredCode = USAGE_LABEL_CODES[classification];
  if (treasuredCode && treasuredCode !== "rus" && treasuredCode !== "calq") {
    treasured = treasuredLabel(record, classification, options.headword, options.definitionCards);
    if (treasured.scope === "lemma") return treasured;
  }

  const curated = curatedScopeRecord(record);
  if (curated) {
    const kind = String(curated.kind).trim();
    const authority = [
      ...normativeCitations((curated as { source?: unknown }).source),
      ...normativeCitations((curated as { citations?: unknown }).citations),
    ];
    const contextual = CONTEXTUAL_CALQUE_SCOPES[kind];
    if (contextual) {
      return usageLabel(null, contextual, authority, curated.calque_sense ?? curated.note);
    }
    if (authority.length > 0) {
      const isRus = Boolean(record.is_russianism) && !AUTHENTIC_CLASSIFICATIONS.has(classification);
      return usageLabel(isRus ? "rus" : "calq", "lemma", authority, curated.noteUk ?? curated.note);
    }
    return usageLabel(null, "unresolved", [], null, "curated_record_without_named_authority");
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
  const classification = status.classification ?? "unknown";
  if (
    TREASURED_CLASSIFICATIONS.has(classification) ||
    (classification === "standard" && hasPositiveAttestation(status))
  ) {
    return "treasured";
  }
  return "none";
}

function greenTitle(label: UsageLabel): string {
  if (label.code === "dial") return "Питома українська регіональна форма";
  if (label.code === "borr") return "Засвоєне українське запозичення";
  if (label.code === "hist") return "Історизм у сучасному вжитку";
  if (label.code === "arch") return "Питома українська архаїчна форма";
  return "Питома українська лексика";
}

function authorityClause(authority: string[]): string {
  return authority.length > 0 ? ` Джерело: ${authority.join(", ")}.` : "";
}

function scopedCalqueTitle(scope: UsageLabelScope): string {
  if (scope === "sense") return "Калькове застереження щодо окремого значення";
  if (scope === "phrase") return "Калькове застереження щодо сполучення";
  return "Калькове застереження";
}

function scopedCalqueBody(label: UsageLabel, alternatives: string[]): string {
  if (label.scope === "sense" || label.scope === "phrase") {
    const where =
      label.scope === "sense"
        ? `окремого значення${label.evidence ? ` («${label.evidence}»)` : ""}`
        : `сполучення${label.evidence ? ` («${label.evidence}»)` : ""}`;
    const use = alternatives.length > 0 ? ` У цьому вжитку радять: ${alternatives.join(", ")}.` : "";
    return `Застереження стосується ${where}, а не слова загалом.${use}${authorityClause(label.authority)}`;
  }
  const use = alternatives.length > 0 ? `Нейтральні відповідники: ${alternatives.join(", ")}.` : "Перевіряйте відповідники в джерелах.";
  return `${use}${authorityClause(label.authority)}`;
}

export function resolveHeritageBoxes(entry: LexiconEntryForSeverity): HeritageBoxes {
  const status = entry.heritage_status ?? null;
  const definitionCards = entry.enrichment?.definition_cards ?? null;
  const label = resolveUsageLabel(status, { headword: entry.lemma, definitionCards });
  if (entry.form_of) return { usageLabel: label };

  const sovietizationRisk = maxSovietizationRisk(entry);
  const avoid = entry.primary_source === SURZHYK_TO_AVOID_SOURCE;
  const severity = avoid ? "russianism_red" : scopedSeverity(status, label);
  const boxes: HeritageBoxes = { usageLabel: label };
  const alternatives = standardAlternatives(status, entry.gloss ?? null);

  if (severity === "russianism_red") {
    const authority = [
      ...(label.scope === "lemma" ? label.authority : []),
      ...(avoid ? ["Атлас: перелік суржику, якого слід уникати"] : []),
    ];
    boxes.red = {
      severity,
      dataSeverity: "red",
      scope: "lemma",
      title: "Редакційне попередження",
      body:
        (alternatives.length > 0
          ? `Джерело позначає цю форму як ненормативну. Рекомендовані відповідники: ${alternatives.join(", ")}.`
          : "Джерело позначає цю форму як ненормативну. Перевіряйте рекомендовані відповідники в джерелах.") +
        authorityClause(authority),
      alternatives,
    };
  } else if (severity === "calque_yellow") {
    boxes.yellow = {
      severity: "calque_yellow",
      dataSeverity: "yellow",
      scope: label.scope,
      title: scopedCalqueTitle(label.scope),
      body: scopedCalqueBody(label, alternatives),
      alternatives,
      detail:
        status?.curated_calque?.noteUk ??
        status?.["§6_note"]?.noteUk ??
        status?.calque_warning?.noteUk ??
        status?.calque_warning?.detail ??
        status?.calque_warning?.note,
    };
  } else if (severity === "treasured") {
    boxes.green = {
      severity,
      dataSeverity: "green",
      title: greenTitle(label),
      body: status?.russian_shadow
        ? "Ця форма має українське джерельне підтвердження; російська морфологічна тінь сама по собі не є підставою для попередження."
        : "Ця форма має українське джерельне підтвердження.",
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
    boxes.inline = { severity: "green", label: "✓ Питома українська лексика" };
  } else if (boxes.blue) {
    boxes.inline = { severity: "blue", label: "СУМ-11: редакторський прапорець" };
  }

  return boxes;
}
