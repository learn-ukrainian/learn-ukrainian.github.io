const ADMONITION_TYPES = new Set(['info', 'tip', 'caution', 'note', 'danger', 'warning']);

// Ukrainian labels — this is a Ukrainian-immersion curriculum; admonition
// callouts must never surface English UI text (immersion rule #M-13).
const DEFAULT_TITLES = {
  info: 'Інформація',
  tip: 'Порада',
  caution: 'Увага',
  note: 'Примітка',
  danger: 'Небезпека',
  warning: 'Застереження',
};
const TIMECODE_TEXT_DIRECTIVE_RE = /^\d+$/;

function isNumericTextDirective(node) {
  return node?.type === 'textDirective' && TIMECODE_TEXT_DIRECTIVE_RE.test(node.name || '');
}

function hasNoChildren(node) {
  return !Array.isArray(node.children) || node.children.length === 0;
}

function hasNoAttributes(node) {
  return !node.attributes || Object.keys(node.attributes).length === 0;
}

function isPlainNumericTimecodeSuffix(node) {
  return isNumericTextDirective(node) && hasNoChildren(node) && hasNoAttributes(node);
}

function visit(node, callback) {
  if (!node || typeof node !== 'object') return;
  callback(node);
  if (!Array.isArray(node.children)) return;
  for (const child of node.children) visit(child, callback);
}

function nodeText(node) {
  if (!node || typeof node !== 'object') return '';
  if (typeof node.value === 'string') return node.value;
  if (!Array.isArray(node.children)) return '';
  return node.children.map((child) => nodeText(child)).join('');
}

function cloneNode(node) {
  if (!node || typeof node !== 'object') return node;

  return {
    ...node,
    data: node.data ? { ...node.data } : undefined,
    children: Array.isArray(node.children) ? node.children.map((child) => cloneNode(child)) : undefined,
  };
}

function splitLabel(children) {
  const label = children.find((child) => child?.data?.directiveLabel);
  return {
    label,
    body: children.filter((child) => child !== label),
  };
}

function normalizeNumericTextDirectives(tree) {
  visit(tree, (node) => {
    if (!isPlainNumericTimecodeSuffix(node)) return;

    // Convert accidental numeric directives like ":57" back into literal text.
    // Keep real admonition/other non-numeric directives intact.
    const value = `:${node.name}`;
    node.type = 'text';
    node.value = value;
    delete node.name;
    delete node.children;
    delete node.attributes;
  });
}

function titleNode(name, label) {
  const hasLabel = label && nodeText(label).trim().length > 0;

  return {
    type: 'paragraph',
    data: {
      hProperties: {
        className: ['admonition-title'],
      },
    },
    children: hasLabel
      ? (label.children ?? []).map((child) => cloneNode(child))
      : [{ type: 'text', value: DEFAULT_TITLES[name] }],
  };
}

export default function remarkAdmonitions() {
  return function transformAdmonitions(tree) {
    normalizeNumericTextDirectives(tree);

    visit(tree, (node) => {
      if (node.type !== 'containerDirective' || !ADMONITION_TYPES.has(node.name)) return;

      const { label, body } = splitLabel(node.children ?? []);

      node.data = {
        ...(node.data ?? {}),
        hName: 'aside',
        hProperties: {
          className: ['admonition', `admonition-${node.name}`],
        },
      };
      node.children = [titleNode(node.name, label), ...body];
    });
  };
}
