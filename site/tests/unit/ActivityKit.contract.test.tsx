import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync, readdirSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import fixtures from '../../../packages/activity-kit/src/fixtures/lu.activity.v1.fixtures.json';
import lessonFixture from '../../../packages/activity-kit/src/fixtures/lu.lesson.v1.fixture.json';
import { ActivityPlayer } from '../../../packages/activity-kit/src/ActivityPlayer';
import type { ActivityEditOperation, LuActivityV1, LuLessonV1, LuRejectedDraft } from '../../../packages/activity-kit/src';

const repoRoot = resolve(process.cwd(), '..');
const kitRoot = join(repoRoot, 'packages/activity-kit');
const schemaPath = join(kitRoot, 'src/lu.activity.v1.schema.json');
const lessonSchemaPath = join(kitRoot, 'src/lu.lesson.v1.schema.json');
const pythonPath = join(repoRoot, '.venv/bin/python');

const GOLDEN_TYPES = [
  'true-false',
  'cloze',
  'match-up',
  'quiz',
  'mark-the-words',
  'fill-in',
  'error-correction',
  'text-questions',
  'short-writing',
] as const;

const validator = `
import json
import sys
from jsonschema import Draft7Validator
from referencing import Registry, Resource

with open(sys.argv[1], encoding='utf-8') as schema_file:
    schema = json.load(schema_file)
fixture = json.load(sys.stdin)
registry = Registry().with_resource(schema['$id'], Resource.from_contents(schema))
errors = list(Draft7Validator(schema, registry=registry).iter_errors(fixture))
for error in errors:
    print(f'{error.json_path}: {error.message}')
sys.exit(1 if errors else 0)
`;

function schemaErrors(fixture: unknown): string {
  const result = spawnSync(pythonPath, ['-c', validator, schemaPath], {
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
fixture = json.load(sys.stdin)
registry = Registry().with_resources([
    (activity_schema['$id'], Resource.from_contents(activity_schema)),
])
errors = list(Draft7Validator(lesson_schema, registry=registry).iter_errors(fixture))
for error in errors:
    print(f'{error.json_path}: {error.message}')
sys.exit(1 if errors else 0)
`;

function lessonSchemaErrors(fixture: unknown): string {
  const result = spawnSync(pythonPath, ['-c', lessonValidator, lessonSchemaPath, schemaPath], {
    encoding: 'utf8',
    input: JSON.stringify(fixture),
  });

  if (result.error) throw result.error;
  return result.stdout.trim();
}

type RejectedDraftFixture = {
  type: string;
  activity: { answer_key: Record<string, unknown> };
  reason: string;
  answer_key?: {
    items?: string[];
    corrections?: Array<Record<string, string>>;
  };
};

function rejectedDraft(document: { rejected: unknown[] }, type: string): RejectedDraftFixture {
  const draft = document.rejected.find((candidate) => (
    typeof candidate === 'object' && candidate !== null && 'type' in candidate && candidate.type === type
  ));

  expect(draft).toBeDefined();
  return draft as RejectedDraftFixture;
}

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(path) : [path];
  });
}

describe('activity-kit contract', () => {
  test('generates the TypeScript discriminated union from the v1 schema', () => {
    execFileSync('node', ['scripts/generate-types.mjs'], { cwd: kitRoot });
    const generated = readFileSync(join(kitRoot, 'src/lu.activity.v1.generated.ts'), 'utf8');
    const lessonGenerated = readFileSync(join(kitRoot, 'src/lu.lesson.v1.generated.ts'), 'utf8');

    expect(generated).toContain('"quiz" | "mark-the-words" | "fill-in"');
    expect(generated).toContain('export type LuActivityV1 =');
    expect(lessonGenerated).toContain('export type LuLessonV1 =');
    expect(lessonGenerated).toContain('activity: LuActivityV1;');
  });

  test('golden fixture covers all nine player-backed engine types', () => {
    expect(fixtures).toHaveLength(9);
    expect(fixtures.map((fixture) => fixture.type).sort()).toEqual([...GOLDEN_TYPES].sort());
  });

  test.each(fixtures)('$id validates against lu.activity.v1 without upstream schema refs', (fixture) => {
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

  test('rejects quiz payloads that alias multiple-choice', () => {
    const malformed = structuredClone(fixtures.find((fixture) => fixture.type === 'quiz'));
    expect(malformed).toBeDefined();
    malformed!.type = 'multiple-choice';
    malformed!.payload.type = 'multiple-choice';

    expect(schemaErrors(malformed)).not.toBe('');
  });

  test('emits a typed completion event without a transport dependency', () => {
    const onComplete = vi.fn();
    render(<ActivityPlayer activity={fixtures[0] as LuActivityV1} onComplete={onComplete} />);

    fireEvent.click(screen.getAllByRole('button', { name: 'True' })[0]);
    fireEvent.click(screen.getByRole('button', { name: 'Check Answers' }));

    expect(onComplete).toHaveBeenCalledWith({
      activityId: 'golden-true-false',
      activityType: 'true-false',
    });
  });

  test.each(['text-questions', 'short-writing'] as const)(
    '%s renders its teacher-facing discuss/grade guidance without auto-grading',
    (type) => {
      const activity = fixtures.find((fixture) => fixture.type === type);
      expect(activity).toBeDefined();

      render(<ActivityPlayer activity={activity as LuActivityV1} isUkrainian />);

      expect(screen.getByText('Для обговорення / оцінювання:')).toBeInTheDocument();
    },
  );

  test('text-questions golden fixture carries source_ref and teacher model answers', () => {
    const activity = fixtures.find((fixture) => fixture.type === 'text-questions') as LuActivityV1;
    expect(activity.payload).toMatchObject({
      source_ref: expect.any(String),
    });
    expect(activity.answer_key).toMatchObject({
      model_answers: expect.arrayContaining([expect.any(String)]),
      rubric: expect.any(String),
    });
  });

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

  test('keeps legacy rejected drafts valid without a teacher-only answer key', () => {
    const document = structuredClone(lessonFixture);
    const legacyDraft = rejectedDraft(document, 'true-false');

    expect(legacyDraft.answer_key).toBeUndefined();
    expect(lessonSchemaErrors(document)).toBe('');
  });

  test('validates an error-correction rejected-draft carrier and preserves duplicate corrections', () => {
    const document = structuredClone(lessonFixture);
    const draft = rejectedDraft(document, 'error-correction') as unknown as Extract<LuRejectedDraft, { type: 'error-correction' }>;

    expect(draft.answer_key?.corrections).toHaveLength(2);
    expect(draft.answer_key?.corrections[0]).toEqual(draft.answer_key?.corrections[1]);
    expect(lessonSchemaErrors(document)).toBe('');
  });

  test.each([
    ['missing items', (draft: RejectedDraftFixture) => delete draft.answer_key?.items],
    ['missing corrections', (draft: RejectedDraftFixture) => delete draft.answer_key?.corrections],
    ['missing correction field', (draft: RejectedDraftFixture) => delete draft.answer_key?.corrections?.[0].error],
    ['blank correction text', (draft: RejectedDraftFixture) => { draft.answer_key!.corrections![0].correction = '   '; }],
    ['extra correction property', (draft: RejectedDraftFixture) => { draft.answer_key!.corrections![0].extra = 'not allowed'; }],
    ['empty items', (draft: RejectedDraftFixture) => { draft.answer_key!.items = []; }],
    ['empty corrections', (draft: RejectedDraftFixture) => { draft.answer_key!.corrections = []; }],
  ])('rejects an error-correction carrier with %s', (_, mutate) => {
    const document = structuredClone(lessonFixture);
    mutate(rejectedDraft(document, 'error-correction'));

    expect(lessonSchemaErrors(document)).not.toBe('');
  });

  test('rejects a teacher-only carrier on a non-error-correction rejected draft', () => {
    const document = structuredClone(lessonFixture);
    const draft = rejectedDraft(document, 'true-false');
    draft.answer_key = {
      items: ['Example source sentence.'],
      corrections: [{ sentence: 'Example source sentence.', error: 'source', correction: 'corrected' }],
    };

    expect(lessonSchemaErrors(document)).not.toBe('');
  });

  test('rejects teacher-only correction metadata inside the activity answer key', () => {
    const document = structuredClone(lessonFixture);
    const draft = rejectedDraft(document, 'error-correction');
    draft.activity.answer_key.corrections = [
      { sentence: 'Example source sentence.', error: 'source', correction: 'corrected' },
    ];

    expect(lessonSchemaErrors(document)).not.toBe('');
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

  test('validates focus_status supported:true with notice_uk:null', () => {
    const doc = structuredClone(lessonFixture) as unknown as LuLessonV1;
    doc.focus_status = {
      requested: 'вищий ступінь прикметників',
      supported: true,
      notice_uk: null,
    };
    expect(lessonSchemaErrors(doc)).toBe('');
  });

  test('validates focus_status supported:false with the Ukrainian notice string', () => {
    const doc = structuredClone(lessonFixture) as unknown as LuLessonV1;
    doc.focus_status = {
      requested: 'вищий ступінь прикметників',
      supported: false,
      notice_uk: 'Опора не містить достатньо перевіреного матеріалу для фокусу «вищий ступінь прикметників». Вправи спираються лише на текст-опору; додайте приклади або змініть фокус.',
    };
    expect(lessonSchemaErrors(doc)).toBe('');
  });

  test('rejects focus_status supported:true with a non-null notice_uk', () => {
    const doc = structuredClone(lessonFixture) as unknown as LuLessonV1;
    doc.focus_status = {
      requested: 'вищий ступінь прикметників',
      supported: true,
      notice_uk: 'Опора не містить достатньо перевіреного матеріалу для фокусу «вищий ступінь прикметників». Вправи спираються лише на текст-опору; додайте приклади або змініть фокус.',
    };
    expect(lessonSchemaErrors(doc)).not.toBe('');
  });

  test('rejects focus_status supported:false with a null notice_uk', () => {
    const doc = structuredClone(lessonFixture) as unknown as LuLessonV1;
    doc.focus_status = {
      requested: 'вищий ступінь прикметників',
      supported: false,
      notice_uk: null,
    };
    expect(lessonSchemaErrors(doc)).not.toBe('');
  });
});
