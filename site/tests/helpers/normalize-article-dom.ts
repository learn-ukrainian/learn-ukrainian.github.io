/**
 * Normalized-DOM comparison for Astro→React WordAtlasArticle parity (PR3).
 *
 * Strips scripts, CSS-module hashes, and normalizes whitespace / boolean attrs /
 * attribute order / HTML entities so structure + text + href/src + ARIA match.
 */

/** Vite CSS-module locals look like `root_abc12` / `_root_xnogr_11` — not only hex. */
const CSS_MODULE_CLASS = /^_?(?:[A-Za-z][\w]*)(?:_[a-zA-Z0-9]+){1,3}$/;

function isCssModuleClass(name: string): boolean {
  if (!name.includes("_")) return false;
  // Keep known global atlas / typeahead class tokens (may contain hyphens, not module hashes).
  if (name.includes("-")) return false;
  return CSS_MODULE_CLASS.test(name);
}
const BOOLEAN_ATTRS = new Set([
  "hidden",
  "disabled",
  "checked",
  "selected",
  "readonly",
  "required",
  "multiple",
  "autofocus",
  "open",
  "defer",
  "async",
  "nomodule",
  "itemscope",
  "reversed",
  "allowfullscreen",
  "autoplay",
  "controls",
  "loop",
  "muted",
  "playsinline",
  "default",
  "inert",
]);

/** Data attrs that Astro emits as presence-only and React as ="true". */
const PRESENCE_DATA_ATTRS = new Set([
  "data-word-atlas",
  "data-atlas-typeahead",
  "data-atlas-typeahead-input",
  "data-atlas-typeahead-list",
]);

function decodeEntities(text: string): string {
  return text
    .replace(/&#x27;/gi, "'")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&nbsp;/g, " ");
}

function normalizeClassList(value: string | null): string | null {
  if (value == null) return null;
  const kept = value
    .split(/\s+/)
    .map((c) => c.trim())
    .filter(Boolean)
    .filter((c) => !isCssModuleClass(c))
    .sort();
  return kept.length ? kept.join(" ") : null;
}

function normalizeAttrName(name: string): string {
  const lower = name.toLowerCase();
  // React SSR may emit camelCase for a few DOM props; fold to HTML names.
  if (lower === "classname") return "class";
  if (lower === "autocomplete") return "autocomplete";
  if (lower === "spellcheck") return "spellcheck";
  if (lower === "htmlfor") return "for";
  return lower;
}

function serializeNode(node: Node, parts: string[]): void {
  if (node.nodeType === Node.COMMENT_NODE) {
    // React SSR inserts empty <!-- --> separators between adjacent text/expr nodes.
    return;
  }
  if (node.nodeType === Node.TEXT_NODE) {
    const raw = node.textContent ?? "";
    // Keep whitespace so adjacent text nodes can be merged by the parent.
    if (!raw) return;
    parts.push(`#text:${decodeEntities(raw)}`);
    return;
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return;
  const el = node as Element;
  const tag = el.tagName.toLowerCase();
  if (tag === "script" || tag === "style" || tag === "link") return;

  const attrs: Array<[string, string]> = [];
  for (const attr of Array.from(el.attributes)) {
    let name = normalizeAttrName(attr.name);
    let value = attr.value;
    if (name === "class") {
      const normalized = normalizeClassList(value);
      if (normalized == null) continue;
      value = normalized;
    } else if (name === "style") {
      value = value
        .split(";")
        .map((part) => part.trim())
        .filter(Boolean)
        .map((part) => {
          const idx = part.indexOf(":");
          if (idx < 0) return part.replace(/\s+/g, "");
          const prop = part.slice(0, idx).trim();
          const val = part.slice(idx + 1).trim();
          return `${prop}:${val}`;
        })
        .sort()
        .join(";");
    } else if (BOOLEAN_ATTRS.has(name) || PRESENCE_DATA_ATTRS.has(name)) {
      value = "";
    } else if (name.startsWith("data-") && (value === "true" || value === "")) {
      value = "";
    } else {
      value = decodeEntities(value).trim();
    }
    attrs.push([name, value]);
  }
  attrs.sort((a, b) => a[0].localeCompare(b[0]));

  const attrStr = attrs.map(([n, v]) => (v === "" ? n : `${n}=${JSON.stringify(v)}`)).join(" ");
  parts.push(`<${tag}${attrStr ? ` ${attrStr}` : ""}>`);

  // Merge adjacent text fragments (Astro often emits one text node; React SSR splits
  // around expressions). Collapse whitespace after the merge.
  const childBuf: string[] = [];
  const textBuf: string[] = [];
  const flushText = () => {
    if (!textBuf.length) return;
    const merged = textBuf.join("").replace(/\s+/g, " ").trim();
    textBuf.length = 0;
    if (merged) childBuf.push(`#text:${merged}`);
  };
  for (const child of Array.from(el.childNodes)) {
    const piece: string[] = [];
    serializeNode(child, piece);
    for (const p of piece) {
      if (p.startsWith("#text:")) {
        textBuf.push(p.slice("#text:".length));
      } else {
        flushText();
        childBuf.push(p);
      }
    }
  }
  flushText();
  parts.push(...childBuf);
  parts.push(`</${tag}>`);
}

export function normalizeArticleDom(html: string): string {
  const doc = new DOMParser().parseFromString(
    `<div id="__root__">${html}</div>`,
    "text/html",
  );
  const root = doc.getElementById("__root__");
  if (!root) return "";

  // Prefer the article root when present so surrounding scripts/wrappers drop away.
  const article = root.querySelector("[data-word-atlas]") ?? root;
  const parts: string[] = [];
  serializeNode(article, parts);
  return parts.join("\n").replace(/\n{2,}/g, "\n").trim();
}

export function extractArticleRegion(pageHtml: string): string {
  const doc = new DOMParser().parseFromString(pageHtml, "text/html");
  const article = doc.querySelector("[data-word-atlas]");
  return article ? article.outerHTML : "";
}

export function stripArticleRegion(pageHtml: string): string {
  const doc = new DOMParser().parseFromString(pageHtml, "text/html");
  const article = doc.querySelector("[data-word-atlas]");
  if (article) {
    const marker = doc.createComment("ARTICLE_REGION");
    article.replaceWith(marker);
  }
  // Drop scripts — Astro module URLs / inline handlers differ across the port.
  for (const script of Array.from(doc.querySelectorAll("script"))) {
    script.remove();
  }
  for (const link of Array.from(doc.querySelectorAll('link[rel="modulepreload"]'))) {
    link.remove();
  }
  // Astro content-hashed CSS filenames differ across trees; keep only the slot.
  for (const link of Array.from(doc.querySelectorAll('link[rel="stylesheet"]'))) {
    const href = link.getAttribute("href") ?? "";
    if (href.includes("/_astro/")) {
      link.setAttribute("href", "/_astro/HASH.css");
    }
  }
  return (doc.documentElement?.outerHTML ?? "")
    .replace(/>\s+</g, "><")
    .replace(/\s{2,}/g, " ");
}
