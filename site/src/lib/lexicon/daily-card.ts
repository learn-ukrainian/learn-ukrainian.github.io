import type { DailyWord } from "./daily";

/** Escape text for safe interpolation into Daily Words card HTML. */
export function escapeDailyCardHtml(value: unknown): string {
  return String(value ?? "").replace(
    /[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] ?? c,
  );
}

export function dailyCardAtlasHref(slug: string): string {
  return `/lexicon/${encodeURIComponent(String(slug))}/`;
}

function renderChips(word: DailyWord): string {
  const chips: string[] = [];
  if (word.k === "avoid") {
    chips.push('<span class="lexicon-daily-chip danger">остерігайтеся</span>');
  }
  if (word.cefr) {
    chips.push(
      `<span class="lexicon-daily-chip">${escapeDailyCardHtml(word.cefr)}</span>`,
    );
  }
  return chips.length > 0
    ? `<span class="lexicon-daily-chips">${chips.join("")}</span>`
    : "";
}

function renderExample(word: DailyWord): string {
  const example = word.example?.trim();
  if (!example) return "";
  const exampleEn = word.exampleEn?.trim();
  return `<span class="lexicon-daily-example" data-testid="daily-example-${escapeDailyCardHtml(word.slug)}" lang="uk">
      ${escapeDailyCardHtml(example)}${exampleEn ? `<span class="lexicon-daily-example-en" lang="en">${escapeDailyCardHtml(exampleEn)}</span>` : ""}
    </span>`;
}

function renderLemma(word: DailyWord): string {
  const lemma = escapeDailyCardHtml(word.lemma);
  const hasAtlas = word.hasAtlasEntry !== false;
  if (!hasAtlas) {
    return `<span class="lexicon-daily-lemma">${lemma}</span>`;
  }
  const href = dailyCardAtlasHref(word.slug);
  return `<a class="lexicon-daily-lemma" data-daily-atlas-link href="${href}">${lemma}</a>`;
}

/**
 * Hub daily card: chrome flips the flashcard; lemma text opens Atlas (#6726).
 * Front = lemma prompt; back = gloss / example (SRS face).
 */
export function renderDailyCardHtml(word: DailyWord): string {
  const lemmaLabel = escapeDailyCardHtml(word.lemma);
  const chips = renderChips(word);
  const gloss = word.gloss
    ? `<span class="lexicon-daily-gloss">${escapeDailyCardHtml(word.gloss)}</span>`
    : `<span class="lexicon-daily-gloss lexicon-daily-gloss-empty">—</span>`;

  return `<li class="lexicon-daily-item">
      <div
        class="lexicon-daily-card"
        data-daily-card
        data-flipped="false"
        role="button"
        tabindex="0"
        aria-pressed="false"
        aria-label="${lemmaLabel} — торкніться картки, щоб перевернути"
      >
        <div class="lexicon-daily-card-inner">
          <div class="lexicon-daily-face lexicon-daily-front">
            ${renderLemma(word)}
            <span class="lexicon-daily-flip-hint">Торкніться картки, щоб побачити значення</span>
            ${chips}
          </div>
          <div class="lexicon-daily-face lexicon-daily-back" aria-hidden="true">
            ${gloss}
            ${renderExample(word)}
            ${chips}
          </div>
        </div>
      </div>
    </li>`;
}

/** True when the event target is (inside) the lemma → Atlas link. */
export function isDailyCardAtlasLinkTarget(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;
  return Boolean(target.closest("[data-daily-atlas-link]"));
}

export function toggleDailyCardFlip(card: HTMLElement): void {
  const next = card.getAttribute("data-flipped") !== "true";
  card.setAttribute("data-flipped", next ? "true" : "false");
  card.setAttribute("aria-pressed", next ? "true" : "false");
  const back = card.querySelector<HTMLElement>(".lexicon-daily-back");
  if (back) back.setAttribute("aria-hidden", next ? "false" : "true");
  const front = card.querySelector<HTMLElement>(".lexicon-daily-front");
  if (front) front.setAttribute("aria-hidden", next ? "true" : "false");
}

/**
 * Event delegation for a daily-words list: chrome click/keyboard flips;
 * lemma link navigates and must not flip.
 */
export function bindDailyCardInteractions(list: HTMLElement): void {
  list.addEventListener("click", (event) => {
    if (isDailyCardAtlasLinkTarget(event.target)) return;
    const card = (event.target as Element | null)?.closest?.("[data-daily-card]");
    if (!(card instanceof HTMLElement) || !list.contains(card)) return;
    event.preventDefault();
    toggleDailyCardFlip(card);
  });

  list.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    if (isDailyCardAtlasLinkTarget(event.target)) return;
    const card = event.target;
    if (!(card instanceof HTMLElement) || !card.hasAttribute("data-daily-card")) return;
    if (!list.contains(card)) return;
    event.preventDefault();
    toggleDailyCardFlip(card);
  });
}
