import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync, readdirSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import fixtures from '../../../packages/activity-kit/src/fixtures/lu.activity.v1.fixtures.json';
import lessonFixture from '../../../packages/activity-kit/src/fixtures/lu.lesson.v1.fixture.json';
import { ActivityPlayer } from '../../../packages/activity-kit/src/ActivityPlayer';
import type { ActivityEditOperation, LuActivityV1, LuLessonV1 } from '../../../packages/activity-kit/src';
import type { ActivitySourceActivity } from '../../../packages/activity-kit/src/ActivityPlayer';

const repoRoot = resolve(process.cwd(), '..');
const kitRoot = join(repoRoot, 'packages/activity-kit');
const schemaPath = join(kitRoot, 'src/lu.activity.v1.schema.json');
const lessonSchemaPath = join(kitRoot, 'src/lu.lesson.v1.schema.json');
const upstreamSchemaPath = join(repoRoot, 'schemas/activity-v2.schema.json');
const pythonPath = join(repoRoot, '.venv/bin/python');

const validator = `
import json
import sys
from jsonschema import Draft7Validator
from referencing import Registry, Resource

with open(sys.argv[1], encoding='utf-8') as schema_file:
    schema = json.load(schema_file)
with open(sys.argv[2], encoding='utf-8') as upstream_file:
    upstream = json.load(upstream_file)
fixture = json.load(sys.stdin)
registry = Registry().with_resource(upstream['$id'], Resource.from_contents(upstream))
errors = list(Draft7Validator(schema, registry=registry).iter_errors(fixture))
for error in errors:
    print(f'{error.json_path}: {error.message}')
sys.exit(1 if errors else 0)
`;

function schemaErrors(fixture: unknown): string {
  const result = spawnSync(pythonPath, ['-c', validator, schemaPath, upstreamSchemaPath], {
    encoding: 'utf8',
    input: JSON.stringify(fixture),
  });

  if (result.error) throw result.error;
  return result.stdout.trim();
}

const lessonValidator = `
import json
import sys
from jsonschema import Draft7Validator
from referencing import Registry, Resource

with open(sys.argv[1], encoding='utf-8') as lesson_file:
    lesson_schema = json.load(lesson_file)
with open(sys.argv[2], encoding='utf-8') as activity_file:
    activity_schema = json.load(activity_file)
with open(sys.argv[3], encoding='utf-8') as upstream_file:
    upstream_schema = json.load(upstream_file)
fixture = json.load(sys.stdin)
registry = Registry().with_resources([
    (activity_schema['$id'], Resource.from_contents(activity_schema)),
    (upstream_schema['$id'], Resource.from_contents(upstream_schema)),
])
errors = list(Draft7Validator(lesson_schema, registry=registry).iter_errors(fixture))
for error in errors:
    print(f'{error.json_path}: {error.message}')
sys.exit(1 if errors else 0)
`;

function lessonSchemaErrors(fixture: unknown): string {
  const result = spawnSync(pythonPath, ['-c', lessonValidator, lessonSchemaPath, schemaPath, upstreamSchemaPath], {
    encoding: 'utf8',
    input: JSON.stringify(fixture),
  });

  if (result.error) throw result.error;
  return result.stdout.trim();
}

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(path) : [path];
  });
}

const sourceActivities: ActivitySourceActivity[] = [
  {
    id: 'quiz-render',
    type: 'quiz',
    title: 'Тест',
    instruction: 'Оберіть правильну відповідь.',
    items: [{ question: 'Яке слово правильне?', options: ['книга', 'книгу'], correct: 0 }],
  },
  {
    id: 'mark-the-words-render',
    type: 'mark-the-words',
    title: 'Позначте слова',
    instruction: 'Позначте іменники.',
    text: 'Книга лежить на столі.',
    target_words: ['Книга', 'столі'],
    criteria: 'Називний або місцевий відмінок.',
  },
  {
    id: 'error-correction-render',
    type: 'error-correction',
    title: 'Виправте помилку',
    instruction: 'Знайдіть помилку.',
    items: [{
      sentence: 'Це моя стіл.',
      error: 'моя',
      correction: 'мій',
      options: ['мій', 'моє'],
      explanation: 'Стіл — чоловічого роду.',
    }],
  },
  {
    id: 'fill-in-render',
    type: 'fill-in',
    title: 'Вставте слово',
    instruction: 'Оберіть форму.',
    items: [{ sentence: 'Це {правильна форма}.', answer: 'книга', options: ['книга', 'книгу'] }],
  },
];

describe('activity-kit contract', () => {
  test('generates the TypeScript discriminated union from the v1 schema', () => {
    execFileSync('node', ['scripts/generate-types.mjs'], { cwd: kitRoot });
    const generated = readFileSync(join(kitRoot, 'src/lu.activity.v1.generated.ts'), 'utf8');
    const lessonGenerated = readFileSync(join(kitRoot, 'src/lu.lesson.v1.generated.ts'), 'utf8');

    expect(generated).toContain('"continue-sentence" | "roleplay-dialog" | "short-writing"');
    expect(generated).toContain('export type LuActivityV1 =');
    expect(lessonGenerated).toContain('export type LuLessonV1 =');
    expect(lessonGenerated).toContain('activity: LuActivityV1;');
  });

  test.each(fixtures)('$id validates against lu.activity.v1', (fixture) => {
    expect(schemaErrors(fixture)).toBe('');
  });

  test.each(fixtures)('$id renders through its dispatched widget', (fixture) => {
    const { container } = render(<ActivityPlayer activity={fixture as LuActivityV1} isUkrainian />);
    const expectedWidget = fixture.type === 'true-false' ? 'true-false' : fixture.type;

    expect(container.querySelector(`[data-activity="${expectedWidget}"]`)).toBeInTheDocument();
  });

  test('rejects a fixture without mandatory provenance', () => {
    const malformed = structuredClone(fixtures[0]);
    delete (malformed as Partial<LuActivityV1>).provenance;

    expect(schemaErrors(malformed)).toContain("'provenance' is a required property");
  });

  test('rejects a payload that does not match its envelope type', () => {
    const malformed = structuredClone(fixtures[0]);
    malformed.type = 'cloze';

    expect(schemaErrors(malformed)).not.toBe('');
  });

  test('emits a typed completion event without a transport dependency', () => {
    const onComplete = vi.fn();
    render(<ActivityPlayer activity={fixtures[0] as LuActivityV1} onComplete={onComplete} />);

    fireEvent.click(screen.getAllByRole('button', { name: 'True' })[0]);
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    expect(onComplete).toHaveBeenCalledWith({
      activityId: 'true-false-claim',
      activityType: 'true-false',
    });
  });

  test.each([
    ...sourceActivities.map((activity) => ({ activity, type: activity.type })),
    ...(['text-questions', 'short-writing'] as const).map((type) => ({
      activity: lessonFixture.blocks.find((block) => block.type === type)?.activity as LuActivityV1,
      type,
    })),
  ])('renders $type through its existing widget instead of the placeholder', ({ activity, type }) => {
    expect(activity).toBeDefined();

    const { container } = render(<ActivityPlayer activity={activity} isUkrainian />);

    expect(container.querySelector(`[data-activity="${type}"]`)).toBeInTheDocument();
    expect(container.querySelector(`[data-activity-placeholder="${type}"]`)).not.toBeInTheDocument();
  });

  test.each(['text-questions', 'short-writing'] as const)(
    '%s renders its teacher-facing discuss/grade guidance without auto-grading',
    (type) => {
      const activity = lessonFixture.blocks.find((block) => block.type === type)?.activity;
      expect(activity).toBeDefined();

      render(<ActivityPlayer activity={activity as LuActivityV1} isUkrainian />);

      expect(screen.getByText('Для обговорення / оцінювання:')).toBeInTheDocument();
    },
  );

  test('publishes the structured edit-operation contract', () => {
    const operation: ActivityEditOperation = {
      op: 'replace',
      path: '/title',
      old: 'Попередня назва',
      new: 'Нова назва',
    };

    expect(operation).toEqual({
      op: 'replace',
      path: '/title',
      old: 'Попередня назва',
      new: 'Нова назва',
    });
  });

  test('has no dependency on site/src internals', () => {
    const imports = sourceFiles(join(kitRoot, 'src'))
      .filter((path) => /\.(?:ts|tsx)$/.test(path))
      .map((path) => ({ path: relative(kitRoot, path), content: readFileSync(path, 'utf8') }))
      .filter(({ content }) => content.includes('site/src'));

    expect(imports).toEqual([]);
  });
});

describe('lesson document v1 contract', () => {
  test('validates the canonical 12-block flagship fixture', () => {
    expect(lessonSchemaErrors(lessonFixture)).toBe('');
  });

  test('keeps the 90-minute 4·5·3 phase plan', () => {
    const document = lessonFixture as LuLessonV1;

    expect(document.blocks).toHaveLength(12);
    expect([1, 2, 3].map((phase) => document.blocks.filter((block) => block.phase === phase))).toHaveLength(3);
    expect(document.blocks.filter((block) => block.phase === 1)).toHaveLength(4);
    expect(document.blocks.filter((block) => block.phase === 2)).toHaveLength(5);
    expect(document.blocks.filter((block) => block.phase === 3)).toHaveLength(3);
  });

  test('rejects a failed document without a human-readable last_error', () => {
    const malformed = structuredClone(lessonFixture);
    malformed.status = 'failed';
    malformed.last_error = null;

    expect(lessonSchemaErrors(malformed)).not.toBe('');
  });

  test('rejects a duration outside the three teacher sizing inputs', () => {
    const malformed = structuredClone(lessonFixture);
    malformed.duration = 30;

    expect(lessonSchemaErrors(malformed)).not.toBe('');
  });

  test('rejects an unknown block type', () => {
    const malformed = structuredClone(lessonFixture);
    malformed.blocks[0].type = 'unknown-type';

    expect(lessonSchemaErrors(malformed)).not.toBe('');
  });

  test('rejects external options that bypass the required warning mark', () => {
    const malformed = structuredClone(lessonFixture);
    const block = malformed.blocks.find((candidate) => candidate.type === 'multiple-choice');
    expect(block).toBeDefined();
    (block as LuLessonV1['blocks'][number]).mark = 'ok';

    expect(lessonSchemaErrors(malformed)).not.toBe('');
  });

  test.each([
    'true-false',
    'cloze',
    'match-up',
    'multiple-choice',
    'form-build',
    'error-correction',
    'paraphrase',
  ])('rejects a %s block without an answer key', (type) => {
    const malformed = structuredClone(lessonFixture);
    const block = malformed.blocks.find((candidate) => candidate.type === type);
    expect(block).toBeDefined();
    delete (block as Partial<LuLessonV1['blocks'][number]>).answer_key;

    expect(lessonSchemaErrors(malformed)).toContain("'answer_key' is a required property");
  });
});
