// Pure session invariants for the Practice Hub detector (#8477). No browser, no I/O:
// the runner feeds observations in, this module says which rule broke.

const PROGRESS_RE = /^\s*(\d+)\s*\/\s*(\d+)\s*$/;

/** `"3/20"` -> `{ done: 3, total: 20 }`; anything else -> `null`. */
export function parseProgress(text) {
  const m = PROGRESS_RE.exec(String(text ?? ''));
  return m ? { done: Number(m[1]), total: Number(m[2]) } : null;
}

/**
 * Progress rule. `readings` is every `practice-session-progress` text the runner saw:
 * one at session start, then one after every answer. Given the budget the runner clicked,
 * the sequence must start at `0/{budget}`, keep the denominator fixed at `budget`, grow the
 * numerator by exactly 1 per reading, and end at `{budget}/{budget}`.
 */
export function checkProgress({ budget, readings }) {
  const violations = [];
  if (!Number.isInteger(budget) || budget <= 0) return { ok: false, violations: [`budget must be a positive integer, got ${budget}`] };
  if (!Array.isArray(readings) || readings.length === 0) return { ok: false, violations: ['no progress readings recorded'] };

  const parsed = readings.map((r) => parseProgress(r));
  const bad = parsed.findIndex((p) => p === null);
  if (bad !== -1) violations.push(`reading #${bad} is not "done/total": ${JSON.stringify(readings[bad])}`);

  const first = parsed[0];
  if (first && (first.done !== 0 || first.total !== budget)) violations.push(`session started at ${readings[0]}, expected 0/${budget}`);

  for (let i = 0; i < parsed.length; i++) {
    const p = parsed[i];
    if (!p) continue;
    if (p.total !== budget) { violations.push(`reading #${i} (${readings[i]}) has denominator ${p.total}, expected ${budget}`); break; }
    const prev = i > 0 ? parsed[i - 1] : null;
    if (prev && p.done !== prev.done + 1) { violations.push(`reading #${i} went ${readings[i - 1]} -> ${readings[i]}, expected +1`); break; }
  }

  const last = parsed[parsed.length - 1];
  if (last && (last.done !== budget || last.total !== budget)) violations.push(`session ended at ${readings[readings.length - 1]}, expected ${budget}/${budget}`);
  return { ok: violations.length === 0, violations };
}

/**
 * Pronunciation rule. Observations from one press of the flashcard pronunciation control:
 *  - `control`: 'pressed' | 'hidden' | 'absent'
 *  - `manifestStatus`: HTTP status of /audio/pronunciation/manifest.json (null = never requested)
 *  - `clips`: [{ path, status }] for every clip request under the audio base
 *  - `mediaPlays`: [{ src }] for every HTMLMediaElement.play() call
 *  - `speakCalls`: number of window.speechSynthesis.speak() calls
 * Fails when the manifest 404s, or when no clip loaded and the browser voice is the only path.
 * Voice quality is out of scope by design (#8477).
 */
export function checkPronunciation(obs) {
  const violations = [];
  const { control = 'absent', manifestStatus = null, clips = [], mediaPlays = [], speakCalls = 0 } = obs ?? {};
  if (manifestStatus === 404) violations.push('pronunciation manifest returned 404');
  else if (manifestStatus === null) violations.push('pronunciation manifest was never requested');
  else if (manifestStatus >= 400) violations.push(`pronunciation manifest returned ${manifestStatus}`);
  if (speakCalls > 0) violations.push(`window.speechSynthesis.speak was called ${speakCalls}x (browser voice fallback)`);
  if (control !== 'pressed') violations.push(`pronunciation control ${control}: no clip loaded for the card`);
  else {
    const okClip = clips.find((c) => c.status >= 200 && c.status < 300);
    if (!okClip) violations.push(clips.length ? `clip request failed: ${clips.map((c) => `${c.status} ${c.path}`).join(', ')}` : 'no clip was requested after pressing the control');
    if (mediaPlays.length === 0) violations.push('no HTMLMediaElement.play() call: nothing but the browser voice could have spoken');
  }
  return { ok: violations.length === 0, violations };
}

/** Whole-run verdict for `--detect`: every rule from #8477, most severe first. */
export function evaluateSession({ budget, readings, pageErrors = [], pronunciation, error = null }) {
  const violations = [];
  if (error) violations.push(`journey error: ${error}`);
  for (const e of pageErrors) violations.push(`pageerror: ${e}`);
  violations.push(...checkProgress({ budget, readings }).violations.map((v) => `progress: ${v}`));
  violations.push(...checkPronunciation(pronunciation).violations.map((v) => `pronunciation: ${v}`));
  return { ok: violations.length === 0, violations };
}
