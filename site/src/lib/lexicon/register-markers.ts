/** Morphology rows carrying VESUM style/register markers (#4891 / #4900). */
export interface MarkedMorphologyForm {
  marker_label: string;
}

export interface MorphologyRegisterCounts {
  form_count?: number;
  marked_form_count?: number;
}

/** Lemma whose entire VESUM paradigm is style-marked (e.g. дин — 32×:short). */
export function isFullyMarkedLemma(morphology: MorphologyRegisterCounts | null | undefined): boolean {
  if (!morphology) return false;
  return (morphology.form_count ?? 0) === 0 && (morphology.marked_form_count ?? 0) > 0;
}

/** Dominant Ukrainian marker label by form count; ties break on first-seen order. */
export function dominantMarkerLabel(forms: MarkedMorphologyForm[]): string | null {
  if (!forms.length) return null;
  const counts = new Map<string, number>();
  const order: string[] = [];
  for (const form of forms) {
    if (!counts.has(form.marker_label)) order.push(form.marker_label);
    counts.set(form.marker_label, (counts.get(form.marker_label) ?? 0) + 1);
  }
  let best = order[0];
  let bestCount = 0;
  for (const label of order) {
    const count = counts.get(label) ?? 0;
    if (count > bestCount) {
      bestCount = count;
      best = label;
    }
  }
  return best;
}

// Lemma-level register badge text derived from enrich_manifest _STYLE_MARKER_LABELS (#4895).
// Neuter short adjectives where the form-level label is feminine («застаріла форма» → «застаріле»).
const REGISTER_BADGE_LABELS: Record<string, string> = {
  "застаріла форма": "застаріле",
  "розмовна форма": "розмовне",
  "сленгова форма": "сленгове",
  "рідковживана форма": "рідковживане",
  "обсценна форма": "обсценне",
  "спотворена форма": "спотворене",
  "коротка форма": "коротка форма",
  "нестягнена форма": "нестягнена форма",
  "альтернативне написання": "альтернативне написання",
  "форма за правописом 2019 року": "форма за правописом 2019 року",
  "форма за правописом 1992 року": "форма за правописом 1992 року",
  "інша маркована форма": "інша маркована форма",
};

export function registerBadgeLabel(markerLabel: string): string {
  return REGISTER_BADGE_LABELS[markerLabel] ?? markerLabel;
}

export function morphologyFormCountLabel(
  morphology: MorphologyRegisterCounts,
  isFullyMarked: boolean,
): string {
  if (isFullyMarked) {
    return `${morphology.marked_form_count} маркованих форм`;
  }
  return `${morphology.form_count ?? 0} форм`;
}
