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
  calque_warning?: { detail?: string; standard_alternatives?: string[] } | null;
  curated_calque?: {
    corrections?: string[];
    note?: string;
    source?: string[];
  } | null;
  "§6_note"?: {
    corrections?: string[];
    note?: string;
    source?: string[];
  } | null;
  reverse_calques?: Array<{
    calque: string;
    note?: string;
    source?: string[];
  }> | null;
}

export interface DefinitionCard {
  id?: string;
  sovietization_risk?: number;
  sovietization_keywords?: string[];
}

export interface LexiconEntryForSeverity {
  gloss?: string | null;
  form_of?: unknown;
  heritage_status?: HeritageStatus | null;
  enrichment?: { definition_cards?: DefinitionCard[] | null } | null;
}

export interface HeritageBox {
  severity: Exclude<WarningSeverity, "none">;
  title: string;
  body: string;
  alternatives?: string[];
  detail?: string;
  dataSeverity: "red" | "yellow" | "green" | "blue";
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

function standardAlternatives(status: HeritageStatus | null | undefined, gloss: string | null): string[] {
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

function fallbackSeverity(status: HeritageStatus | null | undefined): WarningSeverity {
  if (!status) return "none";

  const classification = status.classification ?? "unknown";
  const positiveAttestation = hasPositiveAttestation(status);

  if (status.is_russianism && !AUTHENTIC_CLASSIFICATIONS.has(classification)) {
    return "russianism_red";
  }

  if (
    status.russian_shadow &&
    status.vesum_attested === false &&
    classification === "unknown" &&
    !positiveAttestation
  ) {
    return "russianism_red";
  }

  if (hasCalqueAlternative(status) || hasReverseCalque(status)) return "calque_yellow";

  if (
    TREASURED_CLASSIFICATIONS.has(classification) ||
    (classification === "standard" && positiveAttestation)
  ) {
    return "treasured";
  }

  return "none";
}

function greenTitle(status: HeritageStatus | null | undefined): string {
  if (status?.classification === "dialect") return "Питома українська регіональна форма";
  if (status?.classification === "borrowing") return "Засвоєне українське запозичення";
  if (status?.classification === "historism") return "Історизм у сучасному вжитку";
  if (status?.classification === "authentic-archaism") return "Питома українська архаїчна форма";
  return "Питома українська лексика";
}

export function resolveHeritageBoxes(entry: LexiconEntryForSeverity): HeritageBoxes {
  if (entry.form_of) return {};

  const status = entry.heritage_status ?? null;
  const sovietizationRisk = maxSovietizationRisk(entry);
  const severity = status?.warning_severity ?? fallbackSeverity(status);
  const boxes: HeritageBoxes = {};

  if (severity === "russianism_red") {
    const alternatives = standardAlternatives(status, entry.gloss ?? null);
    boxes.red = {
      severity,
      dataSeverity: "red",
      title: "Редакційне попередження",
      body:
        alternatives.length > 0
          ? `Класифікатор позначає цю форму як проблемну для стандартної української. Рекомендовані відповідники: ${alternatives.join(", ")}.`
          : "Класифікатор позначає цю форму як проблемну для стандартної української. Перевіряйте рекомендовані відповідники в джерелах.",
      alternatives,
    };
  } else if (severity === "calque_yellow" || hasReverseCalque(status) || hasCalqueAlternative(status)) {
    const alternatives = standardAlternatives(status, entry.gloss ?? null);
    const reverseCalques = status?.reverse_calques?.map((item) => `«${item.calque}»`) ?? [];
    boxes.yellow = {
      severity: "calque_yellow",
      dataSeverity: "yellow",
      title: "Калькове застереження",
      body:
        alternatives.length > 0
          ? `Нейтральні відповідники: ${alternatives.join(", ")}.`
          : `Уникайте скалькованої форми ${reverseCalques.join(" або ")}.`,
      alternatives,
      detail:
        status?.curated_calque?.note ??
        status?.["§6_note"]?.note ??
        status?.calque_warning?.detail ??
        status?.reverse_calques?.[0]?.note,
    };
  } else if (severity === "treasured") {
    boxes.green = {
      severity,
      dataSeverity: "green",
      title: greenTitle(status),
      body: status?.russian_shadow
        ? "Ця форма має українське джерельне підтвердження; російська морфологічна тінь сама по собі не є підставою для попередження."
        : "Ця форма має українське джерельне підтвердження.",
    };
  }

  if (sovietizationRisk > 0 || severity === "soviet_def_blue") {
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
  } else if (boxes.yellow) {
    boxes.inline = { severity: "yellow", label: "Калькове застереження" };
  } else if (boxes.green) {
    boxes.inline = { severity: "green", label: "✓ Питома українська лексика" };
  } else if (boxes.blue) {
    boxes.inline = { severity: "blue", label: "СУМ-11: редакторський прапорець" };
  }

  return boxes;
}
