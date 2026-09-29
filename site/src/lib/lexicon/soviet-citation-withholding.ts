/** Runtime reader projection for legacy Atlas payloads (#8990).
 * Both SQLite and HTTP apply this to EntryRecords. The exporter applies the
 * equivalent source-clause rule before writing shards.
 */
const CITATION = /(?:СУМ|SUM)[-_‐‑‒–— ]?11|sum\.in\.ua|slovnyk\.me\/dict\/sum\/|Словник української мови\s*(?:\(1970[–-]1980\)|:\s*[Вв]\s+11\s+томах)/i;
const GATE_NOTE = /\s*\[gate: [^\]]*\]/g;

function cites(value: unknown): boolean {
  return CITATION.test(JSON.stringify(value) ?? "");
}

function key(item: unknown): string | null {
  if (item && typeof item === "object" && !Array.isArray(item)) {
    const record = item as Record<string, unknown>;
    item = ["word", "target", "lemma", "phrase", "text"].map((field) => record[field]).find((v) => typeof v === "string");
  }
  if (typeof item !== "string") return null;
  return item.replace(/\s+\([^)]*\)$/, "").trim().toLocaleLowerCase("uk-UA").replace(/’/g, "'").normalize("NFD").replace(/\u0301/g, "") || null;
}

function relationSection(value: Record<string, unknown>): { section: Record<string, unknown> | null; lost: boolean } {
  const source = value.source as string;
  const items = value.items as unknown[];
  const clauses = source.split(" + ").map((part) => part.trim()).filter(Boolean);
  const allowed: string[] = [];
  const targets = new Set<string>();
  let all = false;
  for (const clause of clauses) {
    const clean = clause.replace(GATE_NOTE, "").trim();
    if (CITATION.test(clean)) continue;
    allowed.push(clean);
    if (clean.includes(" → ")) {
      const target = key(clean.split(" → ").at(-1)?.replace(/ \(reciprocal\)$/, ""));
      if (target) targets.add(target);
    } else {
      all = true;
    }
  }
  const kept = items.filter((item) => all || (key(item) != null && targets.has(key(item)!)));
  return {
    section: kept.length ? { ...value, source: allowed.join(" + "), items: kept } : null,
    lost: kept.length !== items.length,
  };
}

export function withholdLegacySovietCitations<T>(entry: T): T {
  if (!entry || typeof entry !== "object" || (!cites(entry) && !JSON.stringify(entry).includes("[gate: "))) return entry;
  const original = entry as Record<string, unknown>;
  const projected: Record<string, unknown> = { ...original };
  const provenance = { ...((original.gate_provenance ?? {}) as Record<string, unknown>) };

  for (const containerName of ["sections", "enrichment"]) {
    const container = original[containerName];
    if (!container || typeof container !== "object" || Array.isArray(container)) continue;
    const clean = { ...(container as Record<string, unknown>) };
    for (const [name, value] of Object.entries(clean)) {
      if (name === "sources" && Array.isArray(value)) {
        if (value.some((source) => cites(source) &&
            (typeof source !== "string" || CITATION.test(source.replace(GATE_NOTE, ""))))) {
          provenance[`${containerName}.sources`] = "source-withdrawn-unverified";
        }
        clean[name] = value.flatMap((source) => {
          if (typeof source !== "string") return cites(source) ? [] : [source];
          const allowed = source.split(" + ").map((part) => part.replace(GATE_NOTE, "").trim()).filter((part) => part && !CITATION.test(part));
          return allowed.length ? [allowed.join(" + ")] : [];
        });
      } else if ((name === "synonyms" || name === "antonyms") && value && typeof value === "object"
                 && !Array.isArray(value) && typeof (value as Record<string, unknown>).source === "string"
                 && Array.isArray((value as Record<string, unknown>).items)) {
        const { section, lost } = relationSection(value as Record<string, unknown>);
        if (section) clean[name] = section;
        else delete clean[name];
        if (lost && cites(value)) provenance[name] = "source-withdrawn-unverified";
      } else if (cites(value)) {
        delete clean[name];
        provenance[name] = "source-withdrawn-unverified";
      }
    }
    projected[containerName] = clean;
  }
  for (const [name, value] of Object.entries(original)) {
    if (["sections", "enrichment", "gate_provenance"].includes(name)) continue;
    if (name === "soviet_colonization_context" && value && typeof value === "object"
        && (value as Record<string, unknown>).red_flag === true) continue;
    if (name === "source_provenance" && Array.isArray(value)) {
      projected[name] = value.filter((item) => !cites(item));
    } else if (cites(value)) {
      delete projected[name];
      provenance[name] = "source-withdrawn-unverified";
    }
  }
  if (Object.keys(provenance).length) projected.gate_provenance = provenance;
  return projected as T;
}
