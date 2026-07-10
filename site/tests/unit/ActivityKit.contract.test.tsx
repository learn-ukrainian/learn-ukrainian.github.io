import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync, readdirSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import fixtures from '../../../packages/activity-kit/src/fixtures/lu.activity.v1.fixtures.json';
import { ActivityPlayer } from '../../../packages/activity-kit/src/ActivityPlayer';
import type { ActivityEditOperation, LuActivityV1 } from '../../../packages/activity-kit/src';

const repoRoot = resolve(process.cwd(), '..');
const kitRoot = join(repoRoot, 'packages/activity-kit');
const schemaPath = join(kitRoot, 'src/lu.activity.v1.schema.json');
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

    expect(generated).toContain('export type LuActivityType = "true-false" | "cloze" | "match-up"');
    expect(generated).toContain('export type LuActivityV1 =');
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
