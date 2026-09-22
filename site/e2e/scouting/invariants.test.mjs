// node --test e2e/scouting/invariants.test.mjs  (#8477)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkProgress, checkPronunciation, evaluateSession, parseProgress } from './invariants.mjs';

const seq = (n) => Array.from({ length: n + 1 }, (_, i) => `${i}/${n}`);

test('parseProgress reads "done/total" and rejects anything else', () => {
  assert.deepEqual(parseProgress('3/20'), { done: 3, total: 20 });
  assert.deepEqual(parseProgress(' 0 / 10 '), { done: 0, total: 10 });
  assert.equal(parseProgress('Сесія 3/20'), null);
  assert.equal(parseProgress(null), null);
});

test('AC-01: budget 20 with readings 0/9 then 9/9 fails', () => {
  const r = checkProgress({ budget: 20, readings: ['0/9', '9/9'] });
  assert.equal(r.ok, false);
  assert.ok(r.violations.some((v) => v.includes('expected 0/20')), r.violations.join('; '));
});

test('AC-02: a 20-step 0/20 … 20/20 sequence passes', () => {
  const r = checkProgress({ budget: 20, readings: seq(20) });
  assert.deepEqual(r, { ok: true, violations: [] });
});

test('a clean 10-budget session passes', () => {
  assert.equal(checkProgress({ budget: 10, readings: seq(10) }).ok, true);
});

test('denominator drift, skipped steps, repeats and early stops all fail', () => {
  const drift = checkProgress({ budget: 10, readings: ['0/10', '1/10', '2/12', '3/12'] });
  assert.equal(drift.ok, false);
  assert.ok(drift.violations.some((v) => v.includes('denominator 12')));

  const skip = checkProgress({ budget: 10, readings: ['0/10', '1/10', '3/10'] });
  assert.ok(skip.violations.some((v) => v.includes('1/10 -> 3/10')));

  const repeat = checkProgress({ budget: 10, readings: ['0/10', '1/10', '1/10'] });
  assert.ok(repeat.violations.some((v) => v.includes('1/10 -> 1/10')));

  const short = checkProgress({ budget: 10, readings: seq(10).slice(0, 8) });
  assert.ok(short.violations.some((v) => v.includes('ended at 7/10')));

  assert.equal(checkProgress({ budget: 10, readings: [] }).ok, false);
  assert.equal(checkProgress({ budget: 10, readings: ['0/10', 'n/a'] }).ok, false);
});

const goodPronunciation = {
  control: 'pressed',
  manifestStatus: 200,
  clips: [{ path: '/audio/pronunciation/ab/abcd.opus', status: 200 }],
  mediaPlays: [{ src: 'https://x/audio/pronunciation/ab/abcd.opus' }],
  speakCalls: 0,
};

test('pronunciation: a loaded clip with no browser voice passes', () => {
  assert.deepEqual(checkPronunciation(goodPronunciation), { ok: true, violations: [] });
});

test('AC-04: manifest 404 fails; speechSynthesis-only fails; hidden control fails', () => {
  assert.ok(checkPronunciation({ ...goodPronunciation, manifestStatus: 404 }).violations.some((v) => v.includes('404')));
  const voiceOnly = checkPronunciation({ control: 'pressed', manifestStatus: 200, clips: [], mediaPlays: [], speakCalls: 1 });
  assert.equal(voiceOnly.ok, false);
  assert.ok(voiceOnly.violations.some((v) => v.includes('speechSynthesis.speak')));
  assert.ok(voiceOnly.violations.some((v) => v.includes('no clip was requested')));
  assert.equal(checkPronunciation({ control: 'hidden', manifestStatus: 200 }).ok, false);
  assert.equal(checkPronunciation(undefined).ok, false);
});

test('evaluateSession: pageerror alone fails an otherwise clean run', () => {
  const clean = { budget: 20, readings: seq(20), pageErrors: [], pronunciation: goodPronunciation };
  assert.equal(evaluateSession(clean).ok, true);
  const broken = evaluateSession({ ...clean, pageErrors: ['TypeError: x is undefined'] });
  assert.equal(broken.ok, false);
  assert.deepEqual(broken.violations, ['pageerror: TypeError: x is undefined']);
  const lied = evaluateSession({ ...clean, readings: ['0/9', '9/9'] });
  assert.ok(lied.violations.every((v) => v.startsWith('progress: ')));
});
