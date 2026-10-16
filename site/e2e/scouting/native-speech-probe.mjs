#!/usr/bin/env node
// #10706 native speech device check: `prepare` adds one page to an immutable static build; `validate` checks the pasted receipt off-device.
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { lstatSync, readFileSync, readdirSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

export const PAGE = 'native-speech-check.html';
export const TRANSITIONS = ['next', 'home', 'route', 'deck', 'level', 'locale'];
export const OWNED = ['native-speech-probe.mjs', PAGE, 'README.md'].map((f) => `site/e2e/scouting/${f}`).concat('site/tests/unit/native-speech-probe.test.ts');
const HERE = dirname(fileURLToPath(import.meta.url));
const USAGE = `Usage:
  node e2e/scouting/native-speech-probe.mjs prepare --source <clean checkout> --source-sha <40-hex> --out <static build> --manifest <new file>
  node e2e/scouting/native-speech-probe.mjs validate --manifest <file> --receipt <file|-> [--out <static build>]`;

/** Shared by the page (injected as source text) and the off-device validator, so it must stay self-contained. */
export function evaluate(r, x) {
  const why = [];
  const need = (ok, reason) => { if (!ok) why.push(reason); };
  for (const k of ['sourceSha', 'helperSha', 'buildDigest']) need(typeof r.binding?.[k] === 'string' && r.binding[k] === x[k], `${k} missing or moved`);
  const h = r.hashing || {};
  need(h.state === 'OK', `hashing ${h.state || 'missing'}: served bytes unverified`);
  if (h.state === 'OK') {
    if (x.pageSha) need(h.page === x.pageSha, 'page bytes drift');
    const want = Object.keys(x.assets || {});
    need(want.length > 0 && Object.keys(h.assets || {}).length === want.length, 'asset set drift');
    for (const p of want) need(h.assets?.[p] === x.assets[p], `asset drift ${p}`);
  }
  need(r.voices?.state === 'STABLE', `voice catalog ${r.voices?.state || 'missing'}: UNKNOWN`);
  need(r.voices?.ukLocal > 0, 'no local Ukrainian voice observed');
  for (const t of ['next', 'home', 'route', 'deck', 'level', 'locale']) {
    const a = r.transitions?.[t];
    if (!a) { why.push(`${t}: ${r.exposure?.[t] ? 'not attempted' : 'NOT_EXPOSED during native speech'}`); continue; }
    const f = (ok, reason) => need(ok, `${t}: ${reason}`);
    f(a.exposed, 'control was not one tap away at native start (NOT_EXPOSED)');
    f(a.playTrusted && a.transitionTrusted, 'synthetic click is not physical evidence');
    f(!a.clip, 'recorded clip played instead of native speech');
    f(a.speakCalls > 0 && !a.speakThrew, 'native speak missing or threw');
    f(a.voice?.uk && a.voice.local && a.voice.filterMatch, 'selected voice is not the local Ukrainian filter choice');
    f(typeof a.startMs === 'number' && a.startMs >= 0, 'native start not observed');
    f(!(a.startMs > 10000), 'native start over the 10000 ms budget');
    f(a.activeAtTransition, 'speech not active at transition (not started or already ended)');
    f(!a.cancelThrew && a.stopped, 'cancellation and stopped state not observed');
    f(a.quietMs >= 3000 && a.lateStarts === 0, 'quiet window incomplete or speech started again');
    f(a.manual?.audible && a.manual.stoppedImmediately && a.manual.noResume, 'manual attestation missing');
    f(t === 'next' ? a.srsConserved === true : a.srsConserved === null, 'SRS state not conserved');
  }
  return { status: why.length ? 'INCOMPLETE' : 'DEVICE_CONTROLS_PASSED', reasons: why };
}

/** Runs in the diagnostic page. Observes the same-origin practice frame; never substitutes voices, utterances or events. */
export function browserProbe(win, frame, binding, evaluate) {
  const SEL = { next: '[data-testid="practice-advance-button"]', home: '.stage-back', route: 'a[href]', deck: '[data-testid^="practice-deck-option-"]', level: '.k3-levels button', locale: '#lu-locale-toggle' };
  const LABEL = { next: 'Next (Далі), after rating the card', home: 'Home (Додому)', route: 'Any link to another page', deck: 'Deck choice', level: 'Level button', locale: 'Header EN/UK toggle' };
  const CHECKS = { audible: 'I heard Ukrainian speech', stoppedImmediately: 'It stopped at once', noResume: 'Nothing resumed for 3 s' };
  const T = Object.keys(SEL);
  const doc = win.document;
  const now = () => win.performance.now();
  const safe = (fn, fallback) => { try { return fn(); } catch { return fallback; } };
  const isUk = (v) => String(v?.lang).toLowerCase().startsWith('uk');
  const each = (value) => Object.fromEntries(T.map((t) => [t, value]));
  const receipt = { schema: 'native-speech-probe.v1', binding: { sourceSha: binding.sourceSha, helperSha: binding.helperSha, buildDigest: binding.buildDigest },
    hashing: { state: 'PENDING', page: null, assets: {} }, voices: { state: 'PENDING', total: 0, uk: 0, ukLocal: 0, nonUk: 0, waitedMs: 0 },
    exposure: each(false), transitions: each(null), status: 'INCOMPLETE' };
  win.practiceAudioProbe = receipt;
  let pending = null; // the attempt from a Play tap to the end of its quiet window
  const seen = new WeakSet();
  const leaves = (a, fw) => { const u = safe(() => new URL(a.getAttribute('href'), fw.location.href), null); return a.target !== '_blank' && u?.origin === fw.location.origin && u.pathname !== fw.location.pathname; };
  const ready = (fw, t) => Array.from(fw.document.querySelectorAll(SEL[t])).some((el) => !el.disabled && el.getClientRects().length > 0
    && fw.getComputedStyle(el).visibility !== 'hidden' && (t !== 'route' || leaves(el, fw)));
  const late = () => { if (pending?.bound) pending.rec.lateStarts += 1; };
  const started = (a, u) => {
    if (a.bound) return late();
    if (a.utterance !== u || a.startedAt !== null) return;
    a.startedAt = now();
    a.rec.startMs = Math.round(a.startedAt - a.t0);
    a.exposure = Object.fromEntries(T.map((t) => [t, safe(() => ready(a.fw, t), false)]));
    for (const t of T) if (a.exposure[t]) receipt.exposure[t] = true;
    render();
  };
  const bind = (a, kind, event) => {
    const r = a.rec;
    Object.assign(a, { bound: true, kind, boundAt: now() });
    Object.assign(r, { transitionTrusted: event.isTrusted === true, exposed: a.exposure?.[kind] === true,
      activeAtTransition: a.startedAt !== null && a.endedAt === null && safe(() => a.ss.speaking === true, false) });
    const srs = () => safe(() => a.fw.localStorage.getItem('lu-lexicon-srs'), undefined);
    const before = kind === 'next' ? srs() : undefined; // compared in memory; only the boolean is recorded
    win.setTimeout(() => {
      r.quietMs = Math.round(now() - a.boundAt);
      const still = safe(() => frame.contentWindow.speechSynthesis.speaking, true) || safe(() => a.ss.speaking, false);
      r.stopped = r.cancelCalls > 0 && !still;
      if (kind === 'next') r.srsConserved = before !== undefined && srs() === before;
      receipt.transitions[kind] = r;
      pending = null;
      for (const box of doc.querySelectorAll(`input[data-row="${kind}"]`)) Object.assign(box, { checked: false, disabled: false });
      render();
    }, 3000);
    render();
  };
  const onClick = (fw, event) => {
    const el = event.target?.closest ? event.target : null;
    if (!el || pending?.bound) return;
    if (el.closest('[data-pronunciation-lemma] button')) {
      // A tap on the player while speech is active is its Stop control, not a new attempt.
      pending = pending && pending.startedAt !== null && pending.endedAt === null ? null : { t0: now(), fw, startedAt: null, endedAt: null, rec: {
        exposed: false, playTrusted: event.isTrusted === true, transitionTrusted: false, clip: false, speakCalls: 0, speakThrew: false, voice: null, startMs: null,
        activeAtTransition: false, cancelCalls: 0, cancelThrew: false, stopped: false, quietMs: 0, lateStarts: 0, srsConserved: null,
        manual: { audible: false, stoppedImmediately: false, noResume: false } } };
      return;
    }
    const kind = T.find((t) => { const hit = el.closest(SEL[t]); return hit && (t !== 'route' || leaves(hit, fw)); });
    if (kind && pending) bind(pending, kind, event);
  };
  const observe = (a, ss, u, getVoices) => {
    const uk = safe(() => Array.from(getVoices.call(ss)).filter(isUk), []);
    const pick = uk.find((v) => v.localService) || uk[0]; // the player's own Ukrainian filter
    const v = u.voice;
    Object.assign(a, { ss, utterance: u });
    a.rec.speakCalls += 1;
    a.rec.voice = v ? { uk: isUk(v), local: v.localService === true, filterMatch: Boolean(pick) && v.voiceURI === pick.voiceURI && v.name === pick.name && v.lang === pick.lang } : null;
    u.addEventListener('start', () => started(a, u));
    for (const name of ['end', 'error']) u.addEventListener(name, () => { if (a.utterance === u && a.endedAt === null) a.endedAt = now(); });
  };
  const instrument = (fw) => {
    const d = safe(() => (fw.location.href === 'about:blank' ? null : fw.document), null);
    if (!d) return;
    if (!seen.has(d)) { seen.add(d); d.addEventListener('click', (event) => onClick(fw, event), true); }
    if (seen.has(fw)) return;
    seen.add(fw);
    const play = fw.HTMLMediaElement?.prototype.play;
    if (play) fw.HTMLMediaElement.prototype.play = function (...args) { if (pending && !pending.bound) pending.rec.clip = true; late(); return play.apply(this, args); };
    const ss = fw.speechSynthesis;
    if (!ss) return;
    const { speak, cancel, getVoices } = ss;
    ss.speak = function (...args) {
      const a = pending?.bound ? null : pending;
      try { if (a && args[0]) observe(a, ss, args[0], getVoices); else { late(); args[0]?.addEventListener('start', late); } } catch { /* observation never blocks the native call */ }
      try { return speak.apply(this, args); } catch (e) { if (a) a.rec.speakThrew = true; throw e; }
    };
    ss.cancel = function (...args) {
      const a = pending?.bound ? pending : null;
      if (a) a.rec.cancelCalls += 1;
      try { return cancel.apply(this, args); } catch (e) { if (a) a.rec.cancelThrew = true; throw e; }
    };
  };
  const render = () => {
    const out = evaluate(receipt, binding);
    receipt.status = out.status;
    doc.getElementById('summary').textContent = `Voices ${receipt.voices.state}: ${receipt.voices.ukLocal} local Ukrainian of ${receipt.voices.total} · hashing ${receipt.hashing.state} · ${pending?.bound ? `listening 3 s after ${pending.kind}…` : out.status}`;
    doc.getElementById('reasons').textContent = out.reasons.join('\n');
    doc.getElementById('json').value = JSON.stringify(receipt, null, 1);
  };
  // Bounded catalog policy: 8 identical re-reads 250 ms apart; give up after 15 s. An empty catalog stays UNKNOWN.
  const voices = (t0 = now(), last = null, same = 0) => {
    const list = safe(() => Array.from(win.speechSynthesis.getVoices()), null);
    if (!list) { receipt.voices.state = 'UNSUPPORTED'; render(); return; }
    const key = list.map((v) => `${v.voiceURI}|${v.lang}|${v.localService}`).join('\n');
    const uk = list.filter(isUk);
    const waitedMs = Math.round(now() - t0);
    Object.assign(receipt.voices, { total: list.length, uk: uk.length, ukLocal: uk.filter((v) => v.localService === true).length, nonUk: list.length - uk.length, waitedMs });
    const stable = key === last ? same + 1 : 0;
    if (list.length && stable >= 8) receipt.voices.state = 'STABLE';
    else if (waitedMs >= 15000) receipt.voices.state = list.length ? 'UNSTABLE' : 'EMPTY';
    else win.setTimeout(() => voices(t0, key, stable), 250);
    render();
  };
  // Plain-HTTP origins other than loopback expose no WebCrypto, so hashing there is INSECURE and can never pass.
  const hashAll = async (subtle) => {
    try {
      if (!subtle) throw new TypeError('no WebCrypto');
      for (const path of [win.location.pathname, ...Object.keys(binding.assets)]) {
        const res = await win.fetch(path, { cache: 'no-store', credentials: 'same-origin' });
        const hex = res.ok ? Array.from(new Uint8Array(await subtle.digest('SHA-256', await res.arrayBuffer())), (n) => n.toString(16).padStart(2, '0')).join('') : null;
        if (path === win.location.pathname) receipt.hashing.page = hex; else receipt.hashing.assets[path] = hex;
      }
      receipt.hashing.state = 'OK';
    } catch { receipt.hashing.state = subtle ? 'UNAVAILABLE' : 'INSECURE'; }
    render();
  };
  const rows = doc.getElementById('rows');
  const checks = (t) => Object.entries(CHECKS).map(([k, text]) => `<label><input type="checkbox" data-row="${t}" data-check="${k}" disabled> ${text}</label>`).join('<br>');
  rows.innerHTML = T.map((t) => `<tr><th scope="row">${LABEL[t]}</th><td>${checks(t)}</td></tr>`).join('');
  rows.addEventListener('change', ({ target: box, isTrusted }) => {
    const r = receipt.transitions[box.dataset.row];
    if (r && isTrusted) r.manual[box.dataset.check] = box.checked; else box.checked = false; // the page never ticks an attestation itself
    render();
  });
  doc.getElementById('reload').addEventListener('click', () => { frame.src = '/practice/'; });
  win.setInterval(() => instrument(frame.contentWindow), 50); // each new frame document is observed before it can be tapped
  render();
  voices();
  void hashAll(win.isSecureContext ? safe(() => win.crypto.subtle, null) : null);
  return receipt;
}

const HEX = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
const nul = (spec) => ({ nul: spec });
const each = (spec) => Object.fromEntries(TRANSITIONS.map((t) => [t, spec]));
const ATTEMPT = {
  exposed: 'b', playTrusted: 'b', transitionTrusted: 'b', clip: 'b', speakCalls: 'n', speakThrew: 'b', voice: nul({ uk: 'b', local: 'b', filterMatch: 'b' }),
  startMs: nul('n'), activeAtTransition: 'b', cancelCalls: 'n', cancelThrew: 'b', stopped: 'b', quietMs: 'n', lateStarts: 'n', srsConserved: nul('b'),
  manual: { audible: 'b', stoppedImmediately: 'b', noResume: 'b' },
};
export const RECEIPT = {
  schema: ['native-speech-probe.v1'], binding: { sourceSha: 'h', helperSha: 'h', buildDigest: 'h' },
  hashing: { state: ['PENDING', 'OK', 'INSECURE', 'UNAVAILABLE'], page: nul('h'), assets: { map: nul('h') } },
  voices: { state: ['PENDING', 'STABLE', 'EMPTY', 'UNSTABLE', 'UNSUPPORTED'], total: 'n', uk: 'n', ukLocal: 'n', nonUk: 'n', waitedMs: 'n' },
  exposure: each('b'), transitions: each(nul(ATTEMPT)), status: ['INCOMPLETE', 'DEVICE_CONTROLS_PASSED'],
};
const MANIFEST = { sourceSha: 'h', helperSha: 'h', buildDigest: 'h', pageSha: 'h', assets: { map: 'h' } };
const KINDS = { b: ['boolean', (v) => typeof v === 'boolean'], n: ['non-negative number', (v) => Number.isFinite(v) && v >= 0], h: ['hex digest', (v) => typeof v === 'string' && HEX.test(v)] };

/** Strict shape check: unknown fields (names, text, URLs, raw state) and wrong types are refused; values are never echoed. */
export function shapeErrors(value, spec = RECEIPT, at = 'receipt', out = [], open = false) {
  if (spec.nul) return value === null ? out : shapeErrors(value, spec.nul, at, out);
  if (Array.isArray(spec)) { if (!spec.includes(value)) out.push(`${at}: unexpected value`); return out; }
  if (typeof spec === 'string') { if (!KINDS[spec][1](value)) out.push(`${at}: expected ${KINDS[spec][0]}`); return out; }
  if (!value || typeof value !== 'object' || Array.isArray(value)) { out.push(`${at}: expected object`); return out; }
  if (spec.map) {
    for (const [k, v] of Object.entries(value)) if (/^(?:\/[\w-][\w.-]*)+$/.test(k)) shapeErrors(v, spec.map, `${at}[${k}]`, out); else out.push(`${at}: bad asset key`);
    return out;
  }
  if (!open) for (const k of Object.keys(value)) if (!Object.hasOwn(spec, k)) out.push(`${at}.${k}: field not allowed`);
  for (const k of Object.keys(spec)) shapeErrors(value[k], spec[k], `${at}.${k}`, out);
  return out;
}

/** Off-device verdict. The page's own status is never trusted; it is recomputed against the manifest. */
export function validateReceipt(manifest, receipt, drift = []) {
  const bad = shapeErrors(manifest, MANIFEST, 'manifest', [], true);
  const shape = shapeErrors(receipt);
  const reasons = [...drift, ...bad, ...shape];
  if (!bad.length && !shape.length) {
    const out = evaluate(receipt, manifest);
    reasons.push(...out.reasons);
    if (receipt.status !== out.status) reasons.push('page status disagrees with the off-device evaluation');
  }
  const rows = shape.length ? [] : TRANSITIONS.map((t) => receipt.transitions[t]).filter(Boolean);
  const global = reasons.filter((r) => !TRANSITIONS.some((t) => r.startsWith(`${t}: `)));
  const rowOk = (t) => !reasons.some((r) => r.startsWith(`${t}: `));
  const voiceOk = (a) => a.voice?.uk && a.voice.local && a.voice.filterMatch;
  const mark = (ok) => (!global.length && ok ? 'PROVISIONAL_DEVICE_PASS' : 'UNKNOWN');
  const criteria = {
    'P11-C02': mark(rows.length > 0 && rows.every(voiceOk)),
    'NA-07': mark(rowOk('next')),
    'NA-08': mark(['home', 'route', 'deck', 'level', 'locale'].every(rowOk)),
    'NA-09': mark(rows.some((a) => a.playTrusted && !a.clip && !a.speakThrew && voiceOk(a) && a.startMs !== null && a.startMs <= 10000 && a.manual.audible)),
  };
  const residual = 'Provisional device checklist only, never the driver verdict or issue closure. NA-09 Stop/retry and the other P11-C02 inventory classes stay UNKNOWN.';
  return { result: reasons.length ? 'INCOMPLETE' : 'DEVICE_CONTROLS_PASSED', reasons, criteria, residual };
}

function refuse(message) { throw Object.assign(new Error(message), { refused: true }); }
const attempt = (fn) => { try { return fn(); } catch { return null; } };
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const git = (cwd, ...args) => execFileSync('git', ['-C', cwd, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
const present = (p) => attempt(() => lstatSync(p)) !== null;
const knows = (cwd, sha) => attempt(() => git(cwd, 'cat-file', '-e', `${sha}^{commit}`)) !== null;
const realDir = (p) => attempt(() => lstatSync(p).isDirectory() && realpathSync(p) === p) === true;

export function treeDigest(root, skip = null) {
  const files = {};
  const walk = (dir) => {
    for (const name of readdirSync(dir).sort()) {
      const p = join(dir, name);
      const st = lstatSync(p);
      if (st.isSymbolicLink() || !(st.isDirectory() || st.isFile())) refuse(`build contains a symlink or special file: ${relative(root, p)}`);
      if (st.isDirectory()) walk(p);
      else files[relative(root, p).split(sep).join('/')] = sha256(readFileSync(p));
    }
  };
  walk(root);
  return { digest: sha256(Object.entries(files).filter(([rel]) => rel !== skip).map(([rel, h]) => `${h}  ${rel}\n`).join('')), files };
}

export function prepare({ source, sourceSha, out, manifest, helperRoot = git(HERE, 'rev-parse', '--show-toplevel') }) {
  if (!/^[0-9a-f]{40}$/.test(sourceSha || '')) refuse('--source-sha must be a full 40-hex commit');
  if (!source || !knows(source, sourceSha) || git(source, 'rev-parse', 'HEAD') !== sourceSha) refuse('source SHA is unknown, or the --source checkout HEAD moved from it');
  if (git(source, 'status', '--porcelain', '--untracked-files=all')) refuse('source checkout is not clean');
  const helperSha = git(helperRoot, 'rev-parse', 'HEAD');
  if (!knows(helperRoot, sourceSha)) refuse('source SHA is unknown in the helper repository');
  const foreign = git(helperRoot, 'diff', '--name-only', git(helperRoot, 'merge-base', sourceSha, helperSha), helperSha).split('\n').filter((p) => p && !OWNED.includes(p));
  if (foreign.length) refuse(`helper branch changes paths outside its four owned files: ${foreign.join(', ')}`);
  const helperFiles = Object.fromEntries([[OWNED[0], fileURLToPath(import.meta.url)], [OWNED[1], join(HERE, PAGE)]].map(([rel, file]) => {
    const committed = attempt(() => execFileSync('git', ['-C', helperRoot, 'show', `${helperSha}:${rel}`], { stdio: ['ignore', 'pipe', 'ignore'] }));
    if (!committed?.equals(readFileSync(file))) refuse(`${rel} is not committed byte-for-byte at the helper HEAD`);
    return [rel, sha256(committed)];
  }));
  const outDir = resolve(out || '.');
  if (!out || !realDir(outDir)) refuse('--out must be an existing real directory, with no symlink in its path');
  if (!present(join(outDir, 'practice/index.html')) || !realDir(join(outDir, '_astro'))) refuse('--out is not an Astro static build (practice/index.html and _astro/ required)');
  if (present(join(outDir, PAGE))) refuse(`--out already contains ${PAGE}; use a fresh build`);
  const manifestPath = resolve(manifest || '.');
  if (!manifest || present(manifestPath) || !realDir(dirname(manifestPath))) refuse('--manifest must be a new file in an existing real directory');
  if (manifestPath.startsWith(outDir + sep)) refuse('--manifest must be outside --out');
  const before = treeDigest(outDir);
  const assets = Object.fromEntries(Object.entries(before.files).filter(([rel]) => rel === 'practice/index.html' || /^_astro\/[\w.-]+\.js$/.test(rel)).map(([rel, h]) => [`/${rel}`, h]));
  if (Object.keys(assets).length < 2) refuse('build serves no JavaScript under _astro/');
  const binding = { sourceSha, helperSha, buildDigest: before.digest, assets };
  const script = `const evaluate = ${evaluate};\n(${browserProbe})(window, document.getElementById('app'), JSON.parse(document.getElementById('binding').textContent), evaluate);`;
  const template = readFileSync(join(HERE, PAGE), 'utf8');
  if (template.split('__BINDING__').length !== 2 || template.split('__PROBE__').length !== 2 || /<\/script/i.test(script)) refuse('page template placeholders are malformed');
  const page = template.replace('__BINDING__', () => JSON.stringify(binding)).replace('__PROBE__', () => script);
  writeFileSync(join(outDir, PAGE), page, { flag: 'wx' });
  if (treeDigest(outDir, PAGE).digest !== before.digest) refuse('build changed while the page was added');
  const record = { schema: 'native-speech-probe-manifest.v1', sourceSha, helperSha, helperFiles, buildDigest: before.digest, buildFiles: Object.keys(before.files).length, outDir, page: PAGE, pageSha: sha256(Buffer.from(page)), assets };
  writeFileSync(manifestPath, `${JSON.stringify(record, null, 2)}\n`, { flag: 'wx' });
  return record;
}

export function validate({ manifest, receipt, out }) {
  const frozen = JSON.parse(readFileSync(manifest, 'utf8'));
  const tree = out ? treeDigest(resolve(out), PAGE) : null;
  const drift = tree ? [tree.digest !== frozen.buildDigest && 'build output drifted from the manifest', tree.files[PAGE] !== frozen.pageSha && 'diagnostic page bytes drifted from the manifest'] : [];
  return validateReceipt(frozen, JSON.parse(readFileSync(receipt === '-' ? 0 : receipt, 'utf8')), drift.filter(Boolean));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const options = Object.fromEntries(['source', 'source-sha', 'out', 'manifest', 'receipt'].map((name) => [name, { type: 'string' }]));
    const { positionals: [command], values } = parseArgs({ allowPositionals: true, options });
    const report = command === 'prepare' ? prepare({ ...values, sourceSha: values['source-sha'] }) : command === 'validate' ? validate(values) : null;
    console.log(report ? JSON.stringify(report, null, 2) : USAGE);
    process.exitCode = report ? Number(command === 'validate' && report.result !== 'DEVICE_CONTROLS_PASSED') : 2;
  } catch (error) {
    console.error(`${error.refused ? 'REFUSED' : 'ERROR'}: ${error.message}`);
    process.exitCode = 2;
  }
}
