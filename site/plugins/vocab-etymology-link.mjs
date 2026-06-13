import {
  loadDefaultEtymologyResolver,
  normalizeLemma,
  resolveVocabWord,
} from '../src/data/etymology-lemma-index.mjs';

const VOCAB_TAB_LABELS = new Set(['vocabulary', 'словник']);
const WORD_HEADERS = new Set(['word', 'слово']);
const OPT_OUT_RE = /(?:vocab-etymology|etymology-links)\s*:\s*(?:off|false)/i;

function visit(node, callback, parent = null) {
  if (!node || typeof node !== 'object') return;
  callback(node, parent);
  if (!Array.isArray(node.children)) return;
  for (const child of node.children) visit(child, callback, node);
}

function nodeText(node) {
  if (!node || typeof node !== 'object') return '';
  if (typeof node.value === 'string') return node.value;
  if (!Array.isArray(node.children)) return '';
  return node.children.map((child) => nodeText(child)).join('');
}

function getAttribute(node, name) {
  const attribute = node.attributes?.find((attr) => attr.type === 'mdxJsxAttribute' && attr.name === name);
  if (!attribute) return undefined;
  if (typeof attribute.value === 'string' || attribute.value === null) return attribute.value;
  if (typeof attribute.value?.value === 'string') return attribute.value.value;
  return undefined;
}

function isVocabularyTab(node) {
  if (node.type !== 'mdxJsxFlowElement' || node.name !== 'TabItem') return false;
  const label = getAttribute(node, 'label');
  return label ? VOCAB_TAB_LABELS.has(normalizeLemma(label)) : false;
}

function tabOptedOut(node) {
  for (const name of ['data-etymology-links', 'etymologyLinks']) {
    const value = getAttribute(node, name);
    if (value === null || String(value).toLowerCase() === 'false') return true;
  }
  return false;
}

function tableOptedOut(children, tableIndex) {
  for (let index = tableIndex - 1; index >= 0; index -= 1) {
    const sibling = children[index];
    if (!sibling) continue;
    if (sibling.type === 'html' || sibling.type === 'mdxFlowExpression') {
      if (OPT_OUT_RE.test(String(sibling.value ?? ''))) return true;
      continue;
    }
    if (sibling.type === 'text' && !String(sibling.value ?? '').trim()) continue;
    break;
  }
  return false;
}

function hasExistingLink(node) {
  let found = false;
  visit(node, (candidate) => {
    if (candidate.type === 'link') found = true;
    if (
      (candidate.type === 'mdxJsxTextElement' || candidate.type === 'mdxJsxFlowElement') &&
      candidate.name === 'a'
    ) {
      found = true;
    }
  });
  return found;
}

function isWordHeader(cell) {
  return WORD_HEADERS.has(normalizeLemma(nodeText(cell)));
}

function makeLinkNode(children, resolution) {
  return {
    type: 'link',
    url: resolution.href,
    title: `Etymology: ${resolution.slug}`,
    data: {
      hProperties: {
        className: ['vocab-etymology-link'],
        'data-etymology-slug': resolution.slug,
      },
    },
    children,
  };
}

function linkVocabularyTable(table, resolver) {
  const [headerRow, ...bodyRows] = table.children ?? [];
  const wordHeader = headerRow?.children?.[0];
  if (headerRow?.type !== 'tableRow' || !wordHeader || !isWordHeader(wordHeader)) return;

  for (const row of bodyRows) {
    if (row.type !== 'tableRow') continue;
    const wordCell = row.children?.[0];
    if (!wordCell || hasExistingLink(wordCell)) continue;

    const word = nodeText(wordCell);
    const resolution = resolveVocabWord(word, resolver);
    if (!resolution) continue;

    wordCell.children = [makeLinkNode(wordCell.children ?? [], resolution)];
  }
}

function linkTablesInside(node, resolver) {
  const children = node.children ?? [];
  for (let index = 0; index < children.length; index += 1) {
    const child = children[index];
    if (child.type === 'table') {
      if (!tableOptedOut(children, index)) linkVocabularyTable(child, resolver);
      continue;
    }
    if (Array.isArray(child.children)) linkTablesInside(child, resolver);
  }
}

export function createVocabEtymologyLinker({ resolver } = {}) {
  const etymologyResolver = resolver ?? loadDefaultEtymologyResolver();

  return function vocabEtymologyTransformer(tree) {
    visit(tree, (node) => {
      if (!isVocabularyTab(node) || tabOptedOut(node)) return;
      linkTablesInside(node, etymologyResolver);
    });
  };
}

export default function vocabEtymologyLinker(options = {}) {
  return createVocabEtymologyLinker(options);
}
