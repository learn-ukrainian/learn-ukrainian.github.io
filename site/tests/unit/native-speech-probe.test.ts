/**
 * #10706 native speech device check: tool behaviour only. These mocks prove the observer,
 * evaluator and CLI behave as specified; they never certify physical audibility or voice absence.
 */
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { execFileSync, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import {
  OWNED, PAGE, TRANSITIONS, browserProbe, evaluate, prepare, shapeErrors, treeDigest, validate, validateReceipt,
} from '../../e2e/scouting/native-speech-probe.mjs';

const PROBE = resolve(__dirname, '../../e2e/scouting/native-speech-probe.mjs');
const TEMPLATE = resolve(__dirname, '../../e2e/scouting/native-speech-check.html');
const sha = (text: string | Buffer) => createHash('sha256').update(text).digest('hex');
const MANIFEST = {
  sourceSha: 'a'.repeat(40), helperSha: 'b'.repeat(40), buildDigest: 'c'.repeat(64), pageSha: 'd'.repeat(64),
  assets: { '/practice/index.html': 'e'.repeat(64), '/_astro/player.js': 'f'.repeat(64) },
};
type Receipt = ReturnType<typeof passingReceipt>;

function row(kind: string) {
  return {
    exposed: true, playTrusted: true, transitionTrusted: true, clip: false, speakCalls: 1, speakThrew: false,
    voice: { uk: true, local: true, filterMatch: true } as { uk: boolean; local: boolean; filterMatch: boolean } | null,
    startMs: 420 as number | null, activeAtTransition: true, cancelCalls: 1, cancelThrew: false, stopped: true, quietMs: 3001,
    lateStarts: 0, srsConserved: (kind === 'next' ? true : null) as boolean | null, manual: { audible: true, stoppedImmediately: true, noResume: true },
  };
}

function stopOutcome(started: boolean) {
  return {
    playTrusted: true, started, cancelCalls: 1, cancelThrew: false, stopped: true, quietMs: 3000, lateStarts: 0, clip: false, media: true, speech: true,
  };
}

function retryOutcome() {
  return {
    playTrusted: true, startMs: 360 as number | null, speakCalls: 1, speakThrew: false,
    voice: { uk: true, local: true, filterMatch: true } as { uk: boolean; local: boolean; filterMatch: boolean } | null,
    clip: false, media: true, speech: true,
  };
}

function passingReceipt() {
  return {
    schema: 'native-speech-probe.v1',
    binding: { sourceSha: MANIFEST.sourceSha, helperSha: MANIFEST.helperSha, buildDigest: MANIFEST.buildDigest } as Record<string, string>,
    hashing: { state: 'OK', page: MANIFEST.pageSha as string | null, assets: { ...MANIFEST.assets } as Record<string, string | null> },
    voices: { state: 'STABLE', total: 4, uk: 1, ukLocal: 1, nonUk: 3, waitedMs: 2250 },
    observation: {
      documents: [{ media: true, speech: true }],
      attempts: Object.fromEntries(TRANSITIONS.map((t: string) => [t, { media: true, speech: true }])) as Record<string, { media: boolean; speech: boolean } | null>,
    },
    stops: { preStart: stopOutcome(false) as ReturnType<typeof stopOutcome> | null, postStart: stopOutcome(true) as ReturnType<typeof stopOutcome> | null },
    retries: { preStart: retryOutcome() as ReturnType<typeof retryOutcome> | null, postStart: retryOutcome() as ReturnType<typeof retryOutcome> | null },
    exposure: Object.fromEntries(TRANSITIONS.map((t: string) => [t, true])) as Record<string, boolean>,
    transitions: Object.fromEntries(TRANSITIONS.map((t: string) => [t, row(t)])) as Record<string, ReturnType<typeof row> | null>,
    status: 'DEVICE_CONTROLS_PASSED',
  };
}

/** Applies a negative control and lets the page status follow the page's own evaluation, as the page would. */
function negative(mutate: (r: Receipt) => void) {
  const receipt = passingReceipt();
  mutate(receipt);
  receipt.status = evaluate(receipt, MANIFEST).status;
  return validateReceipt(MANIFEST, receipt);
}

describe('off-device validator', () => {
  it('passes only a complete receipt and still labels it provisional', () => {
    const report = validateReceipt(MANIFEST, passingReceipt());
    expect(report).toMatchObject({
      result: 'DEVICE_CONTROLS_PASSED', reasons: [],
      criteria: { 'P11-C02': 'PROVISIONAL_DEVICE_PASS', 'NA-07': 'PROVISIONAL_DEVICE_PASS', 'NA-08': 'PROVISIONAL_DEVICE_PASS', 'NA-09': 'PROVISIONAL_DEVICE_PASS' },
    });
    expect(report.residual).toContain('never the driver verdict');
    expect(report.residual).toContain('NA-09 Stop/retry');
  });

  it('accepts the latency boundary at exactly 10000 ms', () => {
    expect(negative((r) => { r.transitions.next!.startMs = 10000; }).result).toBe('DEVICE_CONTROLS_PASSED');
  });

  const cases: [string, (r: Receipt) => void, string][] = [
    ['missing voice', (r) => { Object.assign(r.voices, { uk: 0, ukLocal: 0, total: 3 }); }, 'no local Ukrainian voice observed'],
    ['empty transient catalog', (r) => { Object.assign(r.voices, { state: 'EMPTY', total: 0, uk: 0, ukLocal: 0, nonUk: 0 }); }, 'voice catalog EMPTY: UNKNOWN'],
    ['unstable catalog', (r) => { r.voices.state = 'UNSTABLE'; }, 'voice catalog UNSTABLE: UNKNOWN'],
    ['foreign voice', (r) => { r.transitions.next!.voice!.uk = false; }, 'next: selected voice is not the local Ukrainian filter choice'],
    ['nonlocal voice', (r) => { r.transitions.home!.voice!.local = false; }, 'home: selected voice is not the local Ukrainian filter choice'],
    ['voice outside the player filter', (r) => { r.transitions.route!.voice!.filterMatch = false; }, 'route: selected voice is not the local Ukrainian filter choice'],
    ['absent native start', (r) => { r.transitions.deck!.startMs = null; }, 'deck: native start not observed'],
    ['speak never called', (r) => { r.transitions.deck!.speakCalls = 0; }, 'deck: native speak missing or threw'],
    ['speak threw', (r) => { r.transitions.deck!.speakThrew = true; }, 'deck: native speak missing or threw'],
    ['already-ended speech', (r) => { r.transitions.level!.activeAtTransition = false; }, 'level: speech not active at transition (not started or already ended)'],
    ['recorded clip instead of speech', (r) => { r.transitions.level!.clip = true; }, 'level: recorded clip played instead of native speech'],
    ['missing transition', (r) => { r.transitions.locale = null; }, 'locale: not attempted'],
    ['unexposed control', (r) => { r.transitions.deck = null; r.exposure.deck = false; }, 'deck: NOT_EXPOSED during native speech'],
    ['control not one tap away', (r) => { r.transitions.home!.exposed = false; }, 'home: control was not one tap away at native start (NOT_EXPOSED)'],
    ['missing manual check', (r) => { r.transitions.home!.manual.noResume = false; }, 'home: manual attestation missing'],
    ['missing audible attestation', (r) => { r.transitions.next!.manual.audible = false; }, 'next: manual attestation missing'],
    ['latency over budget', (r) => { r.transitions.next!.startMs = 10001; }, 'next: native start over the 10000 ms budget'],
    ['late replay', (r) => { r.transitions.route!.lateStarts = 1; }, 'route: quiet window incomplete or speech started again'],
    ['short quiet window', (r) => { r.transitions.route!.quietMs = 2999; }, 'route: quiet window incomplete or speech started again'],
    ['cancellation not observed', (r) => { r.transitions.locale!.stopped = false; }, 'locale: cancellation and stopped state not observed'],
    ['cancel threw', (r) => { r.transitions.locale!.cancelThrew = true; }, 'locale: cancellation and stopped state not observed'],
    ['synthetic click', (r) => { r.transitions.next!.transitionTrusted = false; }, 'next: synthetic click is not physical evidence'],
    ['SRS change', (r) => { r.transitions.next!.srsConserved = false; }, 'next: SRS state not conserved'],
    ['SRS baseline unreadable', (r) => { r.transitions.next!.srsConserved = null; }, 'next: SRS state not conserved'],
    ['insecure hashing', (r) => { r.hashing = { state: 'INSECURE', page: null, assets: {} }; }, 'hashing INSECURE: served bytes unverified'],
    ['unavailable hashing', (r) => { r.hashing.state = 'UNAVAILABLE'; }, 'hashing UNAVAILABLE: served bytes unverified'],
    ['asset drift', (r) => { r.hashing.assets['/_astro/player.js'] = '0'.repeat(64); }, 'asset drift /_astro/player.js'],
    ['missing asset', (r) => { r.hashing.assets['/_astro/player.js'] = null; }, 'asset drift /_astro/player.js'],
    ['page drift', (r) => { r.hashing.page = '0'.repeat(64); }, 'page bytes drift'],
    ['moved source identity', (r) => { r.binding.sourceSha = '9'.repeat(40); }, 'sourceSha missing or moved'],
    ['moved build identity', (r) => { r.binding.buildDigest = '9'.repeat(64); }, 'buildDigest missing or moved'],
    ['missing source identity', (r) => { delete r.binding.sourceSha; }, 'receipt.binding.sourceSha: expected hex digest'],
  ];
  it.each(cases)('%s stays INCOMPLETE', (_name, mutate, reason) => {
    const report = negative(mutate);
    expect(report.result).toBe('INCOMPLETE');
    expect(report.reasons).toContain(reason);
  });

  it('never lets a page PASS claim override the recomputed evaluation', () => {
    const receipt = passingReceipt();
    receipt.transitions.next!.lateStarts = 2;
    const report = validateReceipt(MANIFEST, receipt);
    expect(report.result).toBe('INCOMPLETE');
    expect(report.reasons).toContain('page status disagrees with the off-device evaluation');
    expect(Object.values(report.criteria)).toEqual(['UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN']);
  });

  it('withholds NA-09 until pre-start Stop, post-start Stop and both retries exist', () => {
    const audibleOnly = negative((r) => {
      r.stops.preStart = null;
      r.stops.postStart = null;
      r.retries.preStart = null;
      r.retries.postStart = null;
    });
    expect(audibleOnly.result).toBe('INCOMPLETE');
    expect(audibleOnly.reasons).toContain('NA-09: Stop/retry evidence missing');
    expect(audibleOnly.criteria).toEqual({ 'P11-C02': 'PROVISIONAL_DEVICE_PASS', 'NA-07': 'PROVISIONAL_DEVICE_PASS', 'NA-08': 'PROVISIONAL_DEVICE_PASS', 'NA-09': 'UNKNOWN' });
    const postOnly = negative((r) => { r.stops.preStart = null; });
    expect(postOnly.criteria['NA-09']).toBe('UNKNOWN');
    const noRetry = negative((r) => { r.retries.postStart = null; });
    expect(noRetry.criteria['NA-09']).toBe('UNKNOWN');
    expect(noRetry.reasons).toContain('NA-09: Stop/retry evidence missing');
  });

  it('withholds P11-C02 when media or speech observation is missing on the supporting rows', () => {
    const mediaOff = negative((r) => {
      for (const t of TRANSITIONS) r.observation.attempts[t] = { media: false, speech: true };
    });
    expect(mediaOff.result).toBe('INCOMPLETE');
    expect(mediaOff.criteria['NA-09']).toBe('UNKNOWN');
    expect(mediaOff.criteria['P11-C02']).toBe('UNKNOWN');
    expect(mediaOff.result).not.toBe('DEVICE_CONTROLS_PASSED');
    const speechOff = negative((r) => {
      for (const t of TRANSITIONS) r.observation.attempts[t] = { media: true, speech: false };
    });
    expect(speechOff.result).toBe('INCOMPLETE');
    expect(speechOff.criteria['NA-09']).toBe('UNKNOWN');
    expect(speechOff.criteria['P11-C02']).toBe('UNKNOWN');
    expect(speechOff.criteria['P11-C02']).not.toBe('PROVISIONAL_DEVICE_PASS');
  });

  it('keeps duration and success unmet when media observation is unavailable on every row', () => {
    const report = negative((r) => {
      r.observation.documents[0].media = false;
      for (const t of TRANSITIONS) r.observation.attempts[t] = { media: false, speech: true };
    });
    expect(report.result).toBe('INCOMPLETE');
    expect(report.criteria['NA-09']).toBe('UNKNOWN');
    for (const t of TRANSITIONS) expect(report.reasons).toContain(`${t}: observation was unavailable`);
    expect(report.result).not.toBe('DEVICE_CONTROLS_PASSED');
  });

  it('scopes a single-row defect to its own criterion', () => {
    const report = negative((r) => { r.transitions.next!.lateStarts = 1; });
    expect(report.criteria).toEqual({ 'P11-C02': 'PROVISIONAL_DEVICE_PASS', 'NA-07': 'UNKNOWN', 'NA-08': 'PROVISIONAL_DEVICE_PASS', 'NA-09': 'PROVISIONAL_DEVICE_PASS' });
    const unexposed = negative((r) => { r.transitions.deck = null; r.exposure.deck = false; });
    expect(unexposed.criteria['NA-08']).toBe('UNKNOWN');
  });

  it('keeps every criterion UNKNOWN when global evidence such as hashing is missing', () => {
    const report = negative((r) => { r.hashing.state = 'INSECURE'; });
    expect(Object.values(report.criteria)).toEqual(['UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN']);
  });

  it('refuses sensitive or unknown fields without echoing their values', () => {
    const receipt = passingReceipt() as Record<string, any>;
    receipt.transitions.next.voice.name = 'Lesya (secret voice)';
    receipt.transitions.home.text = 'привіт';
    receipt.url = 'http://192.0.2.1/practice/?account=me';
    receipt.voices.ukLocal = '1';
    receipt.hashing.assets['/../etc'] = 'f'.repeat(64);
    const report = validateReceipt(MANIFEST, receipt);
    expect(report.result).toBe('INCOMPLETE');
    expect(report.reasons).toEqual(expect.arrayContaining([
      'receipt.url: field not allowed', 'receipt.transitions.next.voice.name: field not allowed',
      'receipt.transitions.home.text: field not allowed', 'receipt.voices.ukLocal: expected non-negative number', 'receipt.hashing.assets: bad asset key',
    ]));
    const serialized = JSON.stringify(report);
    for (const secret of ['Lesya', 'привіт', '192.0.2.1', 'account']) expect(serialized).not.toContain(secret);
    expect(Object.values(report.criteria)).toEqual(['UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN']);
  });

  it('refuses a manifest without a page hash', () => {
    const { pageSha: _drop, ...partial } = MANIFEST;
    const report = validateReceipt(partial, passingReceipt());
    expect(report.reasons).toContain('manifest.pageSha: expected hex digest');
    expect(report.result).toBe('INCOMPLETE');
  });
});

type Listener = (event: { isTrusted: boolean; target: Element }) => void;

class FakeUtterance extends EventTarget {
  voice: unknown = null;
  lang = 'uk-UA';
  constructor(public text: string) { super(); }
}

/** A same-origin practice window with native-shaped objects; the probe only wraps what it finds there. */
function harness({ secure = false, voices = [] as unknown[], outerSpeech = true, open = true, media = true, speech = true } = {}) {
  let clock = 0;
  const timers: { at: number; fn: () => void }[] = [];
  const intervals: (() => void)[] = [];
  const advance = (ms: number) => {
    const end = clock + ms;
    for (;;) {
      timers.sort((a, b) => a.at - b.at);
      if (!timers.length || timers[0].at > end) break;
      const next = timers.shift()!;
      clock = next.at;
      next.fn();
    }
    clock = end;
  };
  document.body.innerHTML = '<button id="open"></button><p id="summary"></p><table><tbody id="rows"></tbody></table><p id="reasons"></p><textarea id="json"></textarea>';
  const practiceDoc = (): Document => {
    const frameDoc = document.implementation.createHTMLDocument('practice');
    frameDoc.body.innerHTML = '<span data-pronunciation-lemma="x"><button id="play">Play</button></span>'
      + '<button data-testid="practice-advance-button">Next</button><button class="stage-back">Home</button>'
      + '<a id="away" href="/lexicon/">Atlas</a><a id="self" href="/practice/#top">Top</a><button id="lu-locale-toggle">EN</button>';
    for (const el of Array.from(frameDoc.querySelectorAll('button, a'))) (el as any).getClientRects = () => [{}];
    frameDoc.addEventListener = ((_type: string, fn: Listener) => { listeners.push(fn); }) as any;
    return frameDoc;
  };
  const listeners: Listener[] = [];
  const ukVoice = { name: 'Lesya', voiceURI: 'secret-voice-uri', lang: 'uk-UA', localService: true };
  const enVoice = { name: 'Alex', voiceURI: 'en-uri', lang: 'en-US', localService: true };
  const store = new Map([['lu-lexicon-srs', '{"або":{"due":1}}']]);
  const makeNative = () => ({
    speaking: false, calls: [] as unknown[], self: null as unknown, result: Symbol('native-return'), fail: null as Error | null,
    getVoices() { return [enVoice, ukVoice]; },
    speak(u: unknown) { (this as any).self = this; (this as any).calls.push(u); if ((this as any).fail) throw (this as any).fail; return (this as any).result; },
    cancel() { (this as any).speaking = false; return undefined; },
  });
  const native = makeNative();
  const played: unknown[] = [];
  class FakeMedia { play() { played.push(this); return Promise.resolve('native-play'); } }
  const loaded: (() => void)[] = [];
  const fw: any = {
    closed: false, close() { fw.closed = true; }, addEventListener: (type: string, fn: () => void) => { if (type === 'DOMContentLoaded') loaded.push(fn); },
    document: practiceDoc(), location: { href: 'http://127.0.0.1:4321/practice/', origin: 'http://127.0.0.1:4321', pathname: '/practice/' },
    speechSynthesis: speech ? native : undefined, HTMLMediaElement: media ? FakeMedia : undefined, localStorage: { getItem: (k: string) => store.get(k) ?? null },
    getComputedStyle: () => ({ visibility: 'visible' }),
  };
  const opened: unknown[][] = [];
  const rowsEl = document.getElementById('rows')!;
  let change: ((e: { target: HTMLInputElement; isTrusted: boolean }) => void) | null = null;
  const realAdd = rowsEl.addEventListener.bind(rowsEl);
  rowsEl.addEventListener = ((type: string, fn: any) => { if (type === 'change') change = fn; else realAdd(type, fn); }) as any;
  const fetched: string[] = [];
  const win: any = {
    document, performance: { now: () => clock }, setTimeout: (fn: () => void, ms: number) => timers.push({ at: clock + ms, fn }),
    setInterval: (fn: () => void) => intervals.push(fn), isSecureContext: secure, crypto: globalThis.crypto, location: { pathname: `/${PAGE}` },
    speechSynthesis: outerSpeech ? { getVoices: () => voices } : undefined, open: (...args: unknown[]) => { opened.push(args); return fw; },
    fetch: async (path: string) => { fetched.push(path); return new Response(`bytes of ${path}`); },
  };
  const binding = { ...MANIFEST, pageSha: undefined };
  const receipt = browserProbe(win, binding, evaluate);
  const poll = () => intervals.forEach((fn) => fn());
  if (open) { document.getElementById('open')!.click(); poll(); }
  const tap = (selector: string, isTrusted = true) => listeners.forEach((fn) => fn({ isTrusted, target: fw.document.querySelector(selector)! }));
  const speak = (voice: unknown = ukVoice) => { const u = new FakeUtterance('секретне слово'); u.voice = voice; fw.speechSynthesis.speak(u); return u; };
  const start = (u: FakeUtterance) => { fw.speechSynthesis.speaking = true; u.dispatchEvent(new Event('start')); };
  const tick = (kind: string, check: string, isTrusted = true) => {
    const box = document.querySelector(`input[data-row="${kind}"][data-check="${check}"]`) as HTMLInputElement;
    box.checked = true;
    change!({ target: box, isTrusted });
    return box;
  };
  return { receipt, advance, poll, tap, speak, start, tick, native, makeNative, practiceDoc, fw, opened, loaded, store, played, fetched, ukVoice, enVoice, listeners };
}

describe('in-page observer', () => {
  it('wraps the real speak/cancel without changing return values, receivers or exceptions', () => {
    const h = harness();
    const u = new FakeUtterance('x');
    expect(h.fw.speechSynthesis.speak(u)).toBe(h.native.result);
    expect(h.native.self).toBe(h.native);
    expect(h.native.calls).toEqual([u]);
    const boom = new DOMException('blocked', 'NotAllowedError');
    h.native.fail = boom;
    h.tap('#play');
    expect(() => h.fw.speechSynthesis.speak(new FakeUtterance('y'))).toThrow(boom);
    expect(h.fw.speechSynthesis.getVoices()).toEqual([h.enVoice, h.ukVoice]);
    expect(h.fw.speechSynthesis.cancel()).toBeUndefined();
  });

  it('records one interrupted Next attempt with privacy-safe fields only', () => {
    const h = harness();
    h.tap('#play');
    const u = h.speak();
    h.advance(300);
    h.start(u);
    h.tap('[data-testid="practice-advance-button"]');
    h.fw.speechSynthesis.cancel(); // the app's own stop() during the transition
    u.dispatchEvent(new Event('end'));
    expect(h.receipt.transitions.next).toBeNull();
    h.advance(3000);
    expect(h.receipt.transitions.next).toEqual({
      exposed: true, playTrusted: true, transitionTrusted: true, clip: false, speakCalls: 1, speakThrew: false,
      voice: { uk: true, local: true, filterMatch: true }, startMs: 300, activeAtTransition: true, cancelCalls: 1, cancelThrew: false,
      stopped: true, quietMs: 3000, lateStarts: 0, srsConserved: true, manual: { audible: false, stoppedImmediately: false, noResume: false },
    });
    expect(h.receipt.exposure).toMatchObject({ next: true, home: true, route: true, locale: true, deck: false, level: false });
    expect(shapeErrors(h.receipt)).toEqual([]);
    const json = String((document.getElementById('json') as HTMLTextAreaElement).value);
    for (const secret of ['Lesya', 'secret-voice-uri', 'секретне', 'або', '/lexicon/', '127.0.0.1']) expect(json).not.toContain(secret);
    expect(h.receipt.status).toBe('INCOMPLETE');
  });

  it('counts only trusted manual ticks and never ticks them itself', () => {
    const h = harness();
    h.tap('#play');
    const u = h.speak();
    h.start(u);
    h.tap('.stage-back');
    h.fw.speechSynthesis.cancel();
    h.advance(3000);
    expect(h.tick('home', 'audible', false).checked).toBe(false);
    expect(h.receipt.transitions.home!.manual.audible).toBe(false);
    h.tick('home', 'audible');
    expect(h.receipt.transitions.home!.manual).toEqual({ audible: true, stoppedImmediately: false, noResume: false });
  });

  it('marks a new speech start inside the quiet window as late replay', () => {
    const h = harness();
    h.tap('#play');
    const u = h.speak();
    h.start(u);
    h.tap('#lu-locale-toggle');
    h.fw.speechSynthesis.cancel();
    h.advance(1000);
    h.start(h.speak());
    h.advance(2000);
    expect(h.receipt.transitions.locale!.lateStarts).toBe(2);
    expect(h.receipt.transitions.locale!.stopped).toBe(false);
  });

  it('detects an SRS change across Next without recording the stored value', () => {
    const h = harness();
    h.tap('#play');
    h.start(h.speak());
    h.tap('[data-testid="practice-advance-button"]');
    h.fw.speechSynthesis.cancel();
    h.store.set('lu-lexicon-srs', '{"або":{"due":2}}');
    h.advance(3000);
    expect(h.receipt.transitions.next!.srsConserved).toBe(false);
  });

  it('records already-ended speech, synthetic clicks, foreign voices and recorded clips as not passing', () => {
    const h = harness();
    h.tap('#play');
    const u = h.speak(h.enVoice);
    h.start(u);
    u.dispatchEvent(new Event('end'));
    h.native.speaking = false;
    h.tap('#away', false);
    h.advance(3000);
    expect(h.receipt.transitions.route).toMatchObject({ activeAtTransition: false, transitionTrusted: false, voice: { uk: false, filterMatch: false }, srsConserved: null });
    h.tap('#play');
    new (h.fw.HTMLMediaElement)().play();
    h.tap('.stage-back');
    h.advance(3000);
    expect(h.receipt.transitions.home).toMatchObject({ clip: true, speakCalls: 0, startMs: null, stopped: false });
    expect(h.played).toHaveLength(1);
  });

  it('keeps a clip played before Stop on both retained Stop records', () => {
    const h = harness();
    h.tap('#play');
    new (h.fw.HTMLMediaElement)().play();
    h.tap('#play');
    h.fw.speechSynthesis.cancel();
    h.advance(3000);
    expect(h.receipt.stops.preStart).toMatchObject({
      started: false, stopped: true, cancelCalls: 1, cancelThrew: false, quietMs: 3000, clip: true,
    });

    h.tap('#play');
    new (h.fw.HTMLMediaElement)().play();
    const u = h.speak();
    h.start(u);
    h.tap('#play');
    h.fw.speechSynthesis.cancel();
    u.dispatchEvent(new Event('end'));
    h.advance(3000);
    expect(h.receipt.stops.postStart).toMatchObject({
      started: true, stopped: true, cancelCalls: 1, cancelThrew: false, quietMs: 3000, clip: true,
    });
    expect(h.receipt.stops.preStart.clip).toBe(true);
    expect(shapeErrors(h.receipt)).toEqual([]);

    const report = negative((r) => {
      r.stops.preStart!.clip = h.receipt.stops.preStart.clip;
      r.stops.postStart!.clip = h.receipt.stops.postStart.clip;
    });
    expect(report.result).toBe('INCOMPLETE');
    expect(report.reasons).toContain('NA-09: Stop/retry evidence missing');
    expect(report.criteria['NA-09']).toBe('UNKNOWN');
    expect(report.result).not.toBe('DEVICE_CONTROLS_PASSED');
    expect(report.criteria['NA-09']).not.toBe('PROVISIONAL_DEVICE_PASS');
  });

  it('retains pre-start and post-start Stop, then a fresh retry that is not only a Home row', () => {
    const h = harness();
    h.tap('#play');
    h.speak();
    h.tap('#play');
    h.fw.speechSynthesis.cancel();
    h.advance(3000);
    expect(h.receipt.stops.preStart).toMatchObject({ started: false, stopped: true, cancelCalls: 1, quietMs: 3000, media: true, speech: true });
    expect(Object.values(h.receipt.transitions).every((entry) => entry === null)).toBe(true);

    h.tap('#play');
    const first = h.speak();
    h.start(first);
    expect(h.receipt.retries.preStart).toMatchObject({ playTrusted: true, speakCalls: 1, media: true, speech: true, clip: false });

    h.tap('#play');
    h.fw.speechSynthesis.cancel();
    first.dispatchEvent(new Event('end'));
    h.advance(3000);
    expect(h.receipt.stops.postStart).toMatchObject({ started: true, stopped: true, cancelCalls: 1, quietMs: 3000 });
    expect(h.receipt.transitions.next).toBeNull();

    h.tap('#play');
    const second = h.speak();
    h.start(second);
    expect(h.receipt.retries.postStart).toMatchObject({ playTrusted: true, speakCalls: 1, clip: false });
    h.tap('.stage-back');
    h.fw.speechSynthesis.cancel();
    second.dispatchEvent(new Event('end'));
    h.advance(3000);
    expect(h.receipt.transitions.home).toMatchObject({ cancelCalls: 1, stopped: true, activeAtTransition: true, quietMs: 3000 });
    expect(h.receipt.retries.postStart?.startMs).toEqual(expect.any(Number));
    expect(shapeErrors(h.receipt)).toEqual([]);
  });

  it('does not record a passing quiet window when speech observation is unavailable', () => {
    const h = harness({ speech: false });
    h.tap('#play');
    h.tap('.stage-back');
    h.advance(3000);
    expect(h.receipt.observation.documents).toEqual([{ media: true, speech: false }]);
    expect(h.receipt.observation.attempts.home).toEqual({ media: true, speech: false });
    expect(h.receipt.transitions.home).toMatchObject({ quietMs: 0, stopped: false, clip: false });
    expect(evaluate(h.receipt, MANIFEST).reasons).toContain('home: observation was unavailable');
  });

  it('does not treat a missing media element as a silent successful stop', () => {
    const h = harness({ media: false });
    h.tap('#play');
    const u = h.speak();
    h.start(u);
    h.tap('.stage-back');
    h.fw.speechSynthesis.cancel();
    h.advance(3000);
    expect(h.receipt.observation.documents).toEqual([{ media: false, speech: true }]);
    expect(h.receipt.observation.attempts.home).toEqual({ media: false, speech: true });
    expect(h.receipt.transitions.home).toMatchObject({ quietMs: 0, stopped: false, clip: false });
    expect(evaluate(h.receipt, MANIFEST).reasons).toContain('home: observation was unavailable');
    const crafted = passingReceipt();
    for (const t of TRANSITIONS) crafted.observation.attempts[t] = { media: false, speech: true };
    crafted.status = evaluate(crafted, MANIFEST).status;
    const report = validateReceipt(MANIFEST, crafted);
    expect(report.result).toBe('INCOMPLETE');
    expect(report.criteria['NA-09']).toBe('UNKNOWN');
    expect(report.result).not.toBe('DEVICE_CONTROLS_PASSED');
  });

  it('treats a tap on the active player as Stop and ignores same-page links', () => {
    const h = harness();
    h.tap('#play');
    h.start(h.speak());
    h.tap('#play');
    h.tap('[data-testid="practice-advance-button"]');
    h.tap('#self');
    h.advance(3000);
    expect(h.receipt.transitions.next).toBeNull();
    expect(h.receipt.transitions.route).toBeNull();
  });

  it('opens practice as its own top-level window and observes each new document there', () => {
    const h = harness({ open: false });
    expect(h.opened).toEqual([]);
    const original = h.native.speak;
    document.getElementById('open')!.click();
    expect(h.opened).toEqual([['/practice/', '_blank', 'popup,width=900,height=1000']]);
    h.loaded.forEach((fn) => fn()); // DOMContentLoaded of the first document, before any opener timer runs
    expect(h.fw.speechSynthesis.speak).not.toBe(original);
    expect(h.listeners).toHaveLength(1);
    // A route departure gives the window a new document and a new speech object; both must be observed again.
    const next = h.makeNative();
    const nextSpeak = next.speak;
    Object.assign(h.fw, { document: h.practiceDoc(), speechSynthesis: next });
    h.poll();
    h.poll();
    expect(h.listeners).toHaveLength(2);
    expect(next.speak).not.toBe(nextSpeak);
    h.tap('#play');
    h.start(h.speak());
    h.tap('.stage-back');
    h.fw.speechSynthesis.cancel();
    h.advance(3000);
    expect(h.receipt.transitions.home).toMatchObject({ speakCalls: 1, cancelCalls: 1, stopped: true, activeAtTransition: true });
  });

  it('leaves the initial blank document of the window alone', () => {
    const h = harness({ open: false });
    h.fw.location.href = 'about:blank';
    document.getElementById('open')!.click();
    h.poll();
    expect(h.listeners).toEqual([]);
    expect(Object.hasOwn(h.native, 'speak')).toBe(true);
    expect(h.native.speak).toBe(h.native.speak);
  });

  it('waits for a stable catalog and reports aggregate counts only', () => {
    const voices = [{ lang: 'uk-UA', localService: true, voiceURI: 'u1', name: 'n1' }, { lang: 'uk', localService: false, voiceURI: 'u2', name: 'n2' }, { lang: 'de-DE', localService: true, voiceURI: 'u3', name: 'n3' }];
    const h = harness({ voices });
    expect(h.receipt.voices.state).toBe('PENDING');
    h.advance(1750);
    expect(h.receipt.voices.state).toBe('PENDING');
    h.advance(250);
    expect(h.receipt.voices).toEqual({ state: 'STABLE', total: 3, uk: 2, ukLocal: 1, nonUk: 1, waitedMs: 2000 });
  });

  it('keeps an empty or missing catalog UNKNOWN, never absent', () => {
    const empty = harness();
    empty.advance(15000);
    expect(empty.receipt.voices.state).toBe('EMPTY');
    expect(harness({ outerSpeech: false }).receipt.voices.state).toBe('UNSUPPORTED');
  });

  it('hashes served bytes in a secure context and marks insecure origins', async () => {
    const insecure = harness();
    await new Promise((r) => setTimeout(r, 0));
    expect(insecure.receipt.hashing).toEqual({ state: 'INSECURE', page: null, assets: {} });
    expect(insecure.fetched).toEqual([]);
    const secure = harness({ secure: true });
    await expect.poll(() => secure.receipt.hashing.state).toBe('OK');
    expect(secure.fetched).toEqual([`/${PAGE}`, '/practice/index.html', '/_astro/player.js']);
    expect(secure.receipt.hashing.page).toBe(sha(`bytes of /${PAGE}`));
    expect(secure.receipt.hashing.assets['/_astro/player.js']).toBe(sha('bytes of /_astro/player.js'));
  });
});

describe('prepare and validate CLI', () => {
  let root: string;
  let repo: string;
  let src: string;
  let base: string;
  let helper: string;
  const git = (cwd: string, ...args: string[]) => execFileSync('git', ['-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { cwd, encoding: 'utf8' }).trim();
  const build = (name: string) => {
    const dir = join(root, name);
    mkdirSync(join(dir, 'practice'), { recursive: true });
    mkdirSync(join(dir, '_astro'));
    writeFileSync(join(dir, 'practice/index.html'), '<html>practice</html>');
    writeFileSync(join(dir, '_astro/player.B0y.js'), 'speechSynthesis');
    writeFileSync(join(dir, '_astro/site.css'), 'body{}');
    return dir;
  };
  const opts = (over: Record<string, string> = {}) => ({ source: src, sourceSha: base, out: build(`out-${Math.random().toString(36).slice(2)}`), manifest: join(root, `m-${Math.random().toString(36).slice(2)}.json`), helperRoot: repo, ...over });

  beforeAll(() => {
    root = mkdtempSync(join(tmpdir(), 'native-speech-probe-'));
    repo = join(root, 'repo');
    mkdirSync(join(repo, 'site/e2e/scouting'), { recursive: true });
    git(repo, 'init', '-q', '-b', 'main');
    writeFileSync(join(repo, 'site/app.txt'), 'app');
    git(repo, 'add', '.');
    git(repo, 'commit', '-q', '-m', 'app');
    base = git(repo, 'rev-parse', 'HEAD');
    cpSync(PROBE, join(repo, OWNED[0]));
    cpSync(TEMPLATE, join(repo, OWNED[1]));
    git(repo, 'add', '.');
    git(repo, 'commit', '-q', '-m', 'helper');
    helper = git(repo, 'rev-parse', 'HEAD');
    src = join(root, 'src');
    git(root, 'clone', '-q', repo, src);
    git(src, 'checkout', '-q', '--detach', base);
  });
  afterAll(() => rmSync(root, { recursive: true, force: true }));

  it('adds only the page, binds identities and validates the pasted receipt against the frozen build', () => {
    const o = opts();
    const before = treeDigest(o.out);
    const record = prepare(o);
    const page = readFileSync(join(o.out, PAGE), 'utf8');
    expect(record).toMatchObject({ sourceSha: base, helperSha: helper, buildDigest: before.digest, buildFiles: 3, pageSha: sha(page) });
    expect(record.helperFiles).toEqual({ [OWNED[0]]: sha(readFileSync(PROBE)), [OWNED[1]]: sha(readFileSync(TEMPLATE)) });
    expect(Object.keys(record.assets).sort()).toEqual(['/_astro/player.B0y.js', '/practice/index.html']);
    expect(treeDigest(o.out, PAGE).digest).toBe(before.digest);
    expect(page).not.toMatch(/__BINDING__|__PROBE__/);
    const script = page.slice(page.lastIndexOf('<script>') + 8, page.lastIndexOf('</script>'));
    expect(() => new Function(script)).not.toThrow();
    const binding = JSON.parse(page.match(/<script type="application\/json" id="binding">(.*?)<\/script>/)![1]);
    expect(binding).toEqual({ sourceSha: base, helperSha: helper, buildDigest: before.digest, assets: record.assets });
    const receipt = passingReceipt();
    receipt.binding = { sourceSha: base, helperSha: helper, buildDigest: before.digest };
    receipt.hashing = { state: 'OK', page: record.pageSha, assets: { ...record.assets } };
    const pasted = join(root, 'receipt.json');
    writeFileSync(pasted, JSON.stringify(receipt));
    expect(validate({ manifest: o.manifest, receipt: pasted, out: o.out }).result).toBe('DEVICE_CONTROLS_PASSED');
    const cli = spawnSync(process.execPath, [PROBE, 'validate', '--manifest', o.manifest, '--receipt', pasted], { encoding: 'utf8' });
    expect(cli.status).toBe(0);
    writeFileSync(join(o.out, '_astro/site.css'), 'body{color:red}');
    expect(validate({ manifest: o.manifest, receipt: pasted, out: o.out }).reasons).toContain('build output drifted from the manifest');
    writeFileSync(join(o.out, PAGE), `${page} `);
    expect(validate({ manifest: o.manifest, receipt: pasted, out: o.out }).reasons).toContain('diagnostic page bytes drifted from the manifest');
    const failing = spawnSync(process.execPath, [PROBE, 'validate', '--manifest', o.manifest, '--receipt', pasted, '--out', o.out], { encoding: 'utf8' });
    expect(failing.status).toBe(1);
    expect(JSON.parse(failing.stdout).result).toBe('INCOMPLETE');
  });

  it('refuses unknown, short and moved source SHAs and a dirty source checkout', () => {
    expect(() => prepare(opts({ sourceSha: '0'.repeat(40) }))).toThrow(/source SHA is unknown/);
    expect(() => prepare(opts({ sourceSha: base.slice(0, 12) }))).toThrow(/full 40-hex/);
    expect(() => prepare(opts({ sourceSha: helper }))).toThrow(/HEAD moved/);
    writeFileSync(join(src, 'stray.txt'), 'dirty');
    try { expect(() => prepare(opts())).toThrow(/not clean/); } finally { rmSync(join(src, 'stray.txt')); }
  });

  it('refuses missing, symlinked, non-build and already-prepared output and unsafe manifests', () => {
    expect(() => prepare(opts({ out: join(root, 'missing') }))).toThrow(/existing real directory/);
    const real = build('real');
    const link = join(root, 'link');
    symlinkSync(real, link);
    expect(() => prepare(opts({ out: link }))).toThrow(/existing real directory/);
    const notBuild = join(root, 'not-build');
    mkdirSync(notBuild);
    expect(() => prepare(opts({ out: notBuild }))).toThrow(/not an Astro static build/);
    const prepared = build('prepared');
    writeFileSync(join(prepared, PAGE), 'old');
    expect(() => prepare(opts({ out: prepared }))).toThrow(/already contains/);
    const linked = build('inner-link');
    symlinkSync('/etc/hostname', join(linked, '_astro/evil.js'));
    expect(() => prepare(opts({ out: linked }))).toThrow(/symlink or special file/);
    const existing = join(root, 'existing.json');
    writeFileSync(existing, '{}');
    expect(() => prepare(opts({ manifest: existing }))).toThrow(/new file/);
    const out = build('manifest-inside');
    expect(() => prepare(opts({ out, manifest: join(out, 'm.json') }))).toThrow(/outside --out/);
  });

  it('refuses a helper branch that changes non-owned paths or lacks committed helper bytes', () => {
    const other = join(root, 'other');
    git(root, 'clone', '-q', repo, other);
    writeFileSync(join(other, 'site/app.txt'), 'changed app');
    git(other, 'commit', '-q', '-am', 'touch app');
    expect(() => prepare(opts({ helperRoot: other }))).toThrow(/outside its four owned files: site\/app.txt/);
    const bare = join(root, 'bare-helper');
    git(root, 'clone', '-q', repo, bare);
    git(bare, 'reset', '-q', '--hard', base);
    expect(() => prepare(opts({ helperRoot: bare }))).toThrow(/not committed byte-for-byte/);
  });

  it('reports refusals with exit code 2 and usage errors without a stack', () => {
    const refused = spawnSync(process.execPath, [PROBE, 'prepare', '--source', src, '--source-sha', 'nope', '--out', root, '--manifest', join(root, 'x.json')], { encoding: 'utf8' });
    expect(refused.status).toBe(2);
    expect(refused.stderr).toContain('REFUSED: --source-sha must be a full 40-hex commit');
    const unknown = spawnSync(process.execPath, [PROBE, 'validate', '--bogus'], { encoding: 'utf8' });
    expect(unknown.status).toBe(2);
    expect(unknown.stderr).toMatch(/^ERROR: /);
  });
});
