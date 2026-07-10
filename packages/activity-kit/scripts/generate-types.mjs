import { readFile, writeFile } from 'node:fs/promises';
import { URL } from 'node:url';

const activitySchemaUrl = new URL('../src/lu.activity.v1.schema.json', import.meta.url);
const lessonSchemaUrl = new URL('../src/lu.lesson.v1.schema.json', import.meta.url);
const upstreamSchemaUrl = new URL('../../../schemas/activity-v2.schema.json', import.meta.url);
const activityOutputUrl = new URL('../src/lu.activity.v1.generated.ts', import.meta.url);
const lessonOutputUrl = new URL('../src/lu.lesson.v1.generated.ts', import.meta.url);
const activitySchema = JSON.parse(await readFile(activitySchemaUrl, 'utf8'));
const lessonSchema = JSON.parse(await readFile(lessonSchemaUrl, 'utf8'));
const upstreamSchema = JSON.parse(await readFile(upstreamSchemaUrl, 'utf8'));

function dereferenceActivity(reference) {
  const [url, fragment = ''] = reference.split('#');
  const document = !url || url === activitySchema.$id
    ? activitySchema
    : url === upstreamSchema.$id
      ? upstreamSchema
      : null;

  if (!document || !fragment.startsWith('/')) {
    throw new Error(`Unsupported activity schema reference: ${reference}`);
  }

  return fragment.slice(1).split('/').reduce((value, key) => value[key], document);
}

function dereferenceLesson(reference) {
  const [url, fragment = ''] = reference.split('#');
  const document = !url || url === lessonSchema.$id ? lessonSchema : null;

  if (!document || !fragment.startsWith('/')) {
    throw new Error(`Unsupported lesson schema reference: ${reference}`);
  }

  return fragment.slice(1).split('/').reduce((value, key) => value[key], document);
}

function mergeSchema(node, dereference) {
  if (node.$ref) return mergeSchema(dereference(node.$ref), dereference);
  if (!node.allOf) return node;

  const { allOf, ...base } = node;
  return [base, ...allOf.map((part) => mergeSchema(part, dereference))].reduce((merged, part) => ({
    ...merged,
    ...part,
    properties: { ...merged.properties, ...part.properties },
    required: [...new Set([...(merged.required ?? []), ...(part.required ?? [])])],
  }), {});
}

function primitiveType(type) {
  if (type === 'string') return 'string';
  if (type === 'boolean') return 'boolean';
  if (type === 'integer' || type === 'number') return 'number';
  if (type === 'null') return 'null';
  if (type === 'object') return 'Record<string, unknown>';
  if (type === 'array') return 'Array<unknown>';
  throw new Error(`Unsupported primitive type: ${type}`);
}

function typeFor(node, depth = 0, { dereference, externalRefs = {} }) {
  if (node.$ref && externalRefs[node.$ref]) return externalRefs[node.$ref];

  const resolved = mergeSchema(node, dereference);
  const indent = '  '.repeat(depth);
  const childIndent = '  '.repeat(depth + 1);

  if (resolved.const !== undefined) return JSON.stringify(resolved.const);
  if (resolved.enum) return resolved.enum.map((value) => JSON.stringify(value)).join(' | ');
  if (resolved.oneOf) return resolved.oneOf.map((option) => typeFor(option, depth, { dereference, externalRefs })).join(' | ');
  if (Array.isArray(resolved.type)) return resolved.type.map(primitiveType).join(' | ');
  if (resolved.type === 'string' || resolved.type === 'boolean' || resolved.type === 'integer' || resolved.type === 'number' || resolved.type === 'null') {
    return primitiveType(resolved.type);
  }
  if (resolved.type === 'array') return `Array<${typeFor(resolved.items, depth, { dereference, externalRefs })}>`;

  if (resolved.type === 'object' || resolved.properties) {
    const required = new Set(resolved.required ?? []);
    const properties = Object.entries(resolved.properties ?? {}).map(([name, property]) => (
      `${childIndent}${name}${required.has(name) ? '' : '?'}: ${typeFor(property, depth + 1, { dereference, externalRefs })};`
    ));
    return `{\n${properties.join('\n')}\n${indent}}`;
  }

  throw new Error(`Unsupported schema shape: ${JSON.stringify(resolved)}`);
}

function pascalCase(value) {
  return value.replace(/(^|[-_])([a-z])/g, (_, __, letter) => letter.toUpperCase());
}

const activityTypes = activitySchema.properties.type.enum;
const constraints = new Map(activitySchema.allOf.map((rule) => [
  rule.if.properties.type.const,
  rule.then.properties,
]));

if (activityTypes.length !== constraints.size) {
  throw new Error('Each activity type needs a payload and answer-key constraint.');
}

const variants = activityTypes.map((activityType) => {
  const properties = constraints.get(activityType);
  const name = pascalCase(activityType);
  const payload = typeFor(properties.payload, 0, { dereference: dereferenceActivity });
  const answerKey = typeFor(properties.answer_key, 0, { dereference: dereferenceActivity });

  return { activityType, name, payload, answerKey };
});

const activityProvenance = typeFor(activitySchema.properties.provenance, 0, { dereference: dereferenceActivity });
const activityType = typeFor(activitySchema.properties.type, 0, { dereference: dereferenceActivity });
const activityLevel = typeFor(activitySchema.properties.level, 0, { dereference: dereferenceActivity });
const activitySource = `// This file is generated by scripts/generate-types.mjs from lu.activity.v1.schema.json.
// Do not edit directly.

export type LuActivityType = ${activityType};

export interface LuProvenance ${activityProvenance}

${variants.map(({ name, payload }) => `export type Lu${name}Payload = ${payload};`).join('\n\n')}

${variants.map(({ name, answerKey }) => `export type Lu${name}AnswerKey = ${answerKey};`).join('\n\n')}

interface LuActivityBase<TType extends LuActivityType, TPayload, TAnswerKey> {
  id: string;
  type: TType;
  title: string;
  level: ${activityLevel};
  payload: TPayload;
  answer_key: TAnswerKey;
  provenance: LuProvenance;
}

${variants.map(({ activityType, name }) => `export type Lu${name}ActivityV1 = LuActivityBase<'${activityType}', Lu${name}Payload, Lu${name}AnswerKey>;`).join('\n')}

export type LuActivityV1 =
${variants.map(({ name }) => `  | Lu${name}ActivityV1`).join('\n')};
`;

const lessonOptions = {
  dereference: dereferenceLesson,
  externalRefs: { [activitySchema.$id]: 'LuActivityV1' },
};
const lessonType = typeFor(lessonSchema, 0, lessonOptions);
const lessonStatus = typeFor(lessonSchema.properties.status, 0, lessonOptions);
const lessonDuration = typeFor(lessonSchema.properties.duration, 0, lessonOptions);
const lessonBlock = typeFor(lessonSchema.$defs.block, 0, lessonOptions);
const rejectedDraft = typeFor(lessonSchema.$defs.rejectedDraft, 0, lessonOptions);
const lessonProvenance = typeFor(lessonSchema.$defs.blockProvenance, 0, lessonOptions);
const lessonSource = `// This file is generated by scripts/generate-types.mjs from lu.lesson.v1.schema.json.
// Do not edit directly.

import type { LuActivityV1 } from './lu.activity.v1.generated';

export type LuLessonStatus = ${lessonStatus};

export type LuLessonDuration = ${lessonDuration};

export type LuLessonBlockProvenance = ${lessonProvenance};

export type LuLessonBlock = ${lessonBlock};

export type LuRejectedDraft = ${rejectedDraft};

export type LuLessonV1 = ${lessonType};
`;

await Promise.all([
  writeFile(activityOutputUrl, activitySource),
  writeFile(lessonOutputUrl, lessonSource),
]);
