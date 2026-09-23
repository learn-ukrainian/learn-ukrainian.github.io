#!/usr/bin/env node
// Mock Practice Hub for proving the detector's exit codes offline (#8477).
// It mirrors only the DOM contract `run.mjs --detect` drives: level + budget buttons, the
// flashcards mode button, the progress pill, one flashcard with a pronunciation control,
// the rate/advance buttons and the end screen. Nothing here is product code.
//
//   node e2e/scouting/fixtures/mock-hub.mjs [--port 4322] [--broken progress|audio|pageerror]
//
//   (none)     clean session: 0/N … N/N, manifest 200, clip 200, play() called  -> detector exits 0
//   progress   counter lies: budget 20 shows 0/9 … 9/9, budget 10 shows 0/8 … 8/8 -> exits 1
//   audio      manifest 404, the control falls through to speechSynthesis.speak  -> exits 1
//   pageerror  an uncaught error fires after the first answer                    -> exits 1
import { createServer } from 'node:http';

const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf(k); return i === -1 ? d : args[i + 1]; };
const port = Number(flag('--port', 4322));
const broken = flag('--broken', null);
if (broken && !['progress', 'audio', 'pageerror'].includes(broken)) throw new Error(`--broken must be progress|audio|pageerror, got ${broken}`);

const HASH = 'ab' + '0'.repeat(62);
const CLIP = `ab/${HASH}.wav`;
const LEMMA = 'вода';

// 0.1 s of 8 kHz mono 16-bit silence: a valid WAV that headless Chromium can play().
function silentWav() {
  const samples = 800;
  const data = Buffer.alloc(samples * 2);
  const h = Buffer.alloc(44);
  h.write('RIFF', 0); h.writeUInt32LE(36 + data.length, 4); h.write('WAVE', 8);
  h.write('fmt ', 12); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22);
  h.writeUInt32LE(8000, 24); h.writeUInt32LE(16000, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34);
  h.write('data', 36); h.writeUInt32LE(data.length, 40);
  return Buffer.concat([h, data]);
}

const page = `<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><title>Mock Practice Hub</title>
<style>[hidden]{display:none!important} .flashcard-back{display:none} .flipped .flashcard-back{display:block} .flipped .flashcard-front{display:none} button{min-height:44px;min-width:44px}</style>
</head><body>
<main>
<h1>Mock Practice Hub</h1>
<div id="hub">
  <div class="k3-levels"><button type="button">A1</button><button type="button">A2</button></div>
  <div class="k3-session-budgets">
    <button type="button" data-testid="practice-session-budget-10">10</button>
    <button type="button" data-testid="practice-session-budget-20">20</button>
    <button type="button" data-testid="practice-session-budget-until-zero">∞</button>
  </div>
  <button type="button" data-mode="flashcards">Flashcards</button>
</div>
<div id="stage" hidden data-testid="practice-stage-shell">
  <span data-testid="practice-session-progress" id="progress"></span>
  <button type="button" id="advance" hidden>Далі →</button>
  <div id="card" data-activity="flashcard" role="button" tabindex="0">
    <div class="flashcard-front"><span class="flashcard-word">${LEMMA}</span></div>
    <div class="flashcard-back"><span class="flashcard-word">water</span></div>
  </div>
  <div class="flashcard-pronunciation">
    <span id="pron" data-pronunciation-lemma="${LEMMA}"><button type="button" hidden>Послухати вимову</button><span role="status" aria-live="polite"></span></span>
  </div>
  <div class="rating-bar"><button type="button" class="rate-btn" data-rate="good" id="rate" disabled>Знаю</button></div>
</div>
<div id="summary" hidden data-testid="practice-session-summary">
  <p>Сесію завершено</p>
  <div data-testid="practice-session-continue-links"><a href="/practice/">Ще одна сесія</a><a href="/">Готово</a></div>
</div>
</main>
<script>
(() => {
  const BROKEN = ${JSON.stringify(broken)};
  let budget = 10, total = 0, done = 0, flipped = false, pending = false, answered = 0;
  const $ = (id) => document.getElementById(id);
  document.querySelectorAll('[data-testid^="practice-session-budget-"]').forEach((b) => b.addEventListener('click', () => { budget = Number(b.textContent) || 10; }));
  const progress = () => { $('progress').textContent = done + '/' + total; };
  const setPending = (on) => { pending = on; const a = $('advance'); a.hidden = !on; if (on) a.setAttribute('data-testid', 'practice-advance-button'); else a.removeAttribute('data-testid'); };
  const newCard = () => { flipped = false; $('card').classList.remove('flipped'); $('rate').disabled = true; setPending(false); };
  document.querySelector('[data-mode="flashcards"]').addEventListener('click', () => {
    total = BROKEN === 'progress' ? (budget === 20 ? 9 : 8) : budget; done = 0;
    $('hub').hidden = true; $('stage').hidden = false; progress(); newCard(); mountPronunciation();
  });
  $('card').addEventListener('click', () => { if (!flipped) { flipped = true; $('card').classList.add('flipped'); $('rate').disabled = false; } });
  $('rate').addEventListener('click', () => {
    if (!flipped || pending) return;
    done += 1; answered += 1; progress(); setPending(true);
    if (BROKEN === 'pageerror' && answered === 1) setTimeout(() => { throw new Error('mock pageerror after first answer'); }, 0);
  });
  $('advance').addEventListener('click', () => {
    if (done >= total) { $('stage').hidden = true; $('summary').hidden = false; return; }
    newCard();
  });
  // A cut-down copy of the real player's decision: clip from the manifest, else the browser voice.
  function mountPronunciation() {
    const root = $('pron'); const button = root.querySelector('button'); const status = root.querySelector('[role="status"]');
    let audio = null;
    fetch('/audio/pronunciation/manifest.json').then(async (r) => {
      if (!r.ok) throw new Error('manifest ' + r.status);
      const m = await r.json(); const entry = m.entries[root.dataset.pronunciationLemma];
      if (entry) audio = new Audio('/audio/pronunciation/' + entry.file);
      button.hidden = false;
    }).catch(() => { button.hidden = false; });
    button.addEventListener('click', (e) => {
      e.stopPropagation();
      if (audio) { audio.play().catch(() => { status.textContent = 'Аудіо недоступне.'; }); return; }
      const u = new SpeechSynthesisUtterance(root.dataset.pronunciationLemma); u.lang = 'uk-UA';
      window.speechSynthesis.speak(u);
    });
  }
})();
</script>
</body></html>`;

const server = createServer((req, res) => {
  const path = new URL(req.url, 'http://x').pathname;
  if (path === '/practice/' || path === '/practice') return void res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }).end(page);
  if (path === '/audio/pronunciation/manifest.json') {
    if (broken === 'audio') return void res.writeHead(404, { 'content-type': 'text/plain' }).end('not found');
    return void res.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify({ schemaVersion: 1, entries: { [LEMMA]: { file: CLIP } } }));
  }
  if (path === `/audio/pronunciation/${CLIP}`) return void res.writeHead(200, { 'content-type': 'audio/wav' }).end(silentWav());
  res.writeHead(404, { 'content-type': 'text/plain' }).end('not found');
});
server.listen(port, '127.0.0.1', () => console.log(`mock hub on http://127.0.0.1:${port}/practice/${broken ? ` (broken: ${broken})` : ' (clean)'}`));
