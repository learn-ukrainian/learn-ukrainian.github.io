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
