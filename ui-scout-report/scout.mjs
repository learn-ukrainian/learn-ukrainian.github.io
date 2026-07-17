/**
 * Live-site UI scout — Atlas + Practice evidence pack (2026-07-17).
 * Observe only. Saves shots + findings.json under ui-scout-report/.
 */
import { chromium } from '../site/node_modules/playwright/index.mjs';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = __dirname;
const SHOTS = join(ROOT, 'shots');
const BASE = 'https://learn-ukrainian.github.io';
const LETTERS = 'АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ'.split('');

mkdirSync(SHOTS, { recursive: true });

const findings = [];
const pageEvidence = {};
let shotIdx = 0;

function addFinding(f) {
  findings.push({ id: findings.length + 1, ...f });
  console.log(`  [F${findings.length}] ${f.severity}: ${f.surface}`);
}

async function shot(page, name) {
  shotIdx += 1;
  const file = `${String(shotIdx).padStart(3, '0')}-${name}.png`;
  await page.screenshot({ path: join(SHOTS, file), fullPage: true });
  return `ui-scout-report/shots/${file}`;
}

async function viewportShot(page, name) {
  shotIdx += 1;
  const file = `${String(shotIdx).padStart(3, '0')}-${name}.png`;
  await page.screenshot({ path: join(SHOTS, file), fullPage: false });
  return `ui-scout-report/shots/${file}`;
}

function bindEvidence(page, label) {
  const ev = { label, console: [], network4xx: [], requestFailed: [] };
  pageEvidence[label] = ev;
  page.on('console', (m) => {
    if (m.type() === 'error' || m.type() === 'warning') {
      ev.console.push({ type: m.type(), text: m.text().slice(0, 400) });
    }
  });
  page.on('pageerror', (e) => ev.console.push({ type: 'pageerror', text: String(e).slice(0, 400) }));
  page.on('requestfailed', (r) =>
    ev.requestFailed.push({ url: r.url().slice(0, 180), error: r.failure()?.errorText || '?' }),
  );
  page.on('response', (r) => {
    if (r.status() >= 400) ev.network4xx.push({ url: r.url().slice(0, 180), status: r.status() });
  });
  return ev;
}

async function goto(page, url, wait = 'domcontentloaded') {
  await page.goto(url, { waitUntil: wait, timeout: 60000 });
  await page.waitForTimeout(700);
}

async function bodyText(page) {
  return page.locator('body').innerText();
}

function ukOnlyLines(text) {
  const cyr = /[\u0400-\u04FF]/;
  const lat = /[A-Za-z]{3,}/;
  return [
    ...new Set(
      text
        .split(/\n+/)
        .map((l) => l.trim())
        .filter((l) => l.length > 1 && l.length < 140 && cyr.test(l) && !lat.test(l)),
    ),
  ];
}

function snip(text, n = 500) {
  return text.slice(0, n).replace(/\n+/g, ' | ');
}

async function overflowCheck(page) {
  return page.evaluate(() => {
    const d = document.documentElement;
    return {
      scrollWidth: d.scrollWidth,
      clientWidth: d.clientWidth,
      overflow: d.scrollWidth > d.clientWidth + 2,
    };
  });
}

async function searchInput(page) {
  const loc = page.locator('input[type="search"], input[type="text"], input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])').first();
  return (await loc.count()) > 0 ? loc : null;
}

// ===================== DESKTOP =====================
async function scoutDesktop(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'en-US' });
  const page = await ctx.newPage();
  page.setDefaultTimeout(20000);
  const ev = bindEvidence(page, 'desktop');

  // ----- 1. Landing -----
  console.log('\n=== 1. /lexicon/ landing ===');
  await goto(page, `${BASE}/lexicon/`, 'networkidle');
  const landingFull = await shot(page, 'desktop-lexicon-landing-full');
  const landingFold = await viewportShot(page, 'desktop-lexicon-landing-viewport');
  const landingText = await bodyText(page);

  let countBox = null;
  try {
    countBox = await page.getByText(/8[\s\u00a0]?206/).first().boundingBox();
  } catch {}
  const countBelowFold = countBox ? countBox.y + countBox.height > 860 : null;

  addFinding({
    surface: '/lexicon/ dictionary-size impression',
    repro: 'Open https://learn-ukrainian.github.io/lexicon/ at 1280×900; compare viewport vs full page',
    what: `Above-the-fold (viewport shot) shows hero "Атлас слів", search field, "Перегляд А–Я →". The number 8 206 appears in a "ДАНІ / Покриття Атласу" panel labelled "ПУБЛІЧНИЙ АТЛАС" (UA), with subline "9 969 пошукових словоформ · 66 сегментів пошуку". Bounding box of 8206: ${JSON.stringify(countBox)}; below fold (~y>860): ${countBelowFold}. Also on page: МАНІФЕСТ 8 552, СЛОВА ДНЯ 300. No English "8,206 words" phrasing in default УКР locale. Snippet: ${snip(landingText, 700)}`,
    hurts: 'A first-time visitor looking for an obvious English "8,206 words" may miss the scale — the count is UA-labelled, in a data panel, and may sit below the fold.',
    severity: countBelowFold ? 'major' : 'minor',
    screenshot: landingFold,
    evidence: { fullPage: landingFull, console: ev.console.slice(), network: ev.network4xx.slice() },
  });

  // Lang toggle
  const localeBtn = page.locator('button.lu-locale-toggle');
  if ((await localeBtn.count()) > 0) {
    const before = await bodyText(page);
    await localeBtn.click();
    await page.waitForTimeout(500);
    const afterLangShot = await shot(page, 'desktop-lexicon-locale-eng');
    const after = await bodyText(page);
    const stillHas8206 = /8[\s\u00a0]?206/.test(after);
    addFinding({
      surface: '/lexicon/ locale toggle',
      repro: 'Click УКР/ENG locale toggle on atlas landing',
      what: `Toggle label reads "УКРENG" (concatenated). After click, page text changes. Still shows 8206: ${stillHas8206}. EN snippet: ${snip(after, 600)}. Toggle control itself still looks like "УКРENG" mashed together.`,
      hurts: 'Locale control looks broken (УКРENG); beginners may not realize English chrome exists, and stats labels may stay opaque.',
      severity: 'major',
      screenshot: afterLangShot,
      evidence: { beforeHasPublicAtlas: /ПУБЛІЧНИЙ/.test(before), afterSnippet: snip(after, 400) },
    });
    // return to UKR for consistent rest of scout? stay ENG briefly then flip back
    await localeBtn.click();
    await page.waitForTimeout(300);
  }

  // Typeahead
  const input = await searchInput(page);
  if (input) {
    const ph = (await input.getAttribute('placeholder')) || '';
    const aria = (await input.getAttribute('aria-label')) || '';

    // Latin
    await input.click();
    await input.fill('');
    await input.type('voda', { delay: 70 });
    await page.waitForTimeout(800);
    const latinShot = await shot(page, 'desktop-typeahead-latin-voda');
    const latinOpts = await page.locator('[role="option"], [role="listbox"] *').count();
    const latinSuggestText = snip(await bodyText(page), 400);
    addFinding({
      surface: '/lexicon/ typeahead Latin',
      repro: `Focus search (placeholder="${ph}", aria="${aria}"); type Latin "voda"`,
      what: `Options/listbox nodes≈${latinOpts}. Page after typing: ${latinSuggestText}`,
      hurts: 'Learners without Cyrillic keyboard need Latin→lemma lookup.',
      severity: latinOpts > 0 || /вод/i.test(latinSuggestText) ? 'polish' : 'major',
      screenshot: latinShot,
    });

    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    const escShot = await shot(page, 'desktop-typeahead-escape');
    addFinding({
      surface: '/lexicon/ typeahead Escape',
      repro: 'With suggestions open, press Escape',
      what: `Input value="${await input.inputValue()}"; option count=${await page.locator('[role="option"]').count()}`,
      hurts: 'Keyboard users expect Escape to dismiss the dropdown.',
      severity: 'minor',
      screenshot: escShot,
    });

    // Cyrillic
    await input.fill('');
    await input.type('вода', { delay: 70 });
    await page.waitForTimeout(800);
    const cyrShot = await shot(page, 'desktop-typeahead-cyrillic-voda');
    const cyrOpts = await page.locator('[role="option"]').count();
    addFinding({
      surface: '/lexicon/ typeahead Cyrillic',
      repro: 'Type Cyrillic "вода"',
      what: `role=option count=${cyrOpts}; value="${await input.inputValue()}"; ${snip(await bodyText(page), 350)}`,
      hurts: 'Cyrillic typeahead is the primary path for prepared learners.',
      severity: cyrOpts > 0 ? 'polish' : 'blocker',
      screenshot: cyrShot,
    });

    // Paste via clipboard API / fill
    await input.fill('');
    await input.fill('алергія');
    await input.dispatchEvent('input');
    await page.waitForTimeout(800);
    const pasteShot = await shot(page, 'desktop-typeahead-paste-alergiya');
    addFinding({
      surface: '/lexicon/ typeahead paste',
      repro: 'Paste/fill "алергія" into search',
      what: `value="${await input.inputValue()}"; options=${await page.locator('[role="option"]').count()}`,
      hurts: 'Paste from chat/notes is a common dictionary entry path.',
      severity: 'minor',
      screenshot: pasteShot,
    });

    // Enter navigate
    await input.fill('');
    await input.type('вода', { delay: 50 });
    await page.waitForTimeout(600);
    await page.keyboard.press('ArrowDown');
    await page.waitForTimeout(200);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1200);
    const enterUrl = page.url();
    const enterShot = await shot(page, 'desktop-typeahead-enter');
    addFinding({
      surface: '/lexicon/ typeahead Enter',
      repro: 'Type "вода", ArrowDown, Enter',
      what: `Navigated to ${enterUrl}`,
      hurts: 'Enter must open a word page; staying on landing feels broken.',
      severity: /\/lexicon\/.+/.test(enterUrl) && !enterUrl.endsWith('/lexicon/') ? 'polish' : 'major',
      screenshot: enterShot,
    });
  } else {
    addFinding({
      surface: '/lexicon/',
      repro: 'Find search input',
      what: 'No search input found',
      hurts: 'Cannot search the atlas.',
      severity: 'blocker',
      screenshot: landingFull,
    });
  }

  // ----- 2. Browse -----
  console.log('\n=== 2. Browse alphabet ===');
  await goto(page, `${BASE}/lexicon/browse/`);
  const browseShot = await shot(page, 'desktop-browse-landing');
  const browseText = await bodyText(page);
  addFinding({
    surface: '/lexicon/browse landing',
    repro: 'Open /lexicon/browse/',
    what: `Shows letter buttons (not links). Text includes "8206 записів Атласу · 33 літери". Empty state: "Оберіть літеру…". Snippet: ${snip(browseText, 450)}`,
    hurts: 'Size is stated as "записів" (records) in UA — clearer than landing for count, but still UA-first.',
    severity: 'minor',
    screenshot: browseShot,
  });

  // Global search on browse
  const bSearch = await searchInput(page);
  if (bSearch) {
    await bSearch.fill('вода');
    await page.waitForTimeout(600);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1000);
    const bs = await shot(page, 'desktop-browse-search-voda');
    addFinding({
      surface: '/lexicon/browse global search',
      repro: 'Type "вода" in browse search, Enter',
      what: `URL=${page.url()}; ${snip(await bodyText(page), 350)}`,
      hurts: 'Browse search that fails silently blocks dictionary discovery.',
      severity: 'minor',
      screenshot: bs,
    });
  }

  const letterResults = [];
  for (const letter of LETTERS) {
    process.stdout.write(`  ${letter}`);
    await goto(page, `${BASE}/lexicon/browse/`);
    await page.locator('button.atlas-letter-link').first().waitFor({ state: 'visible', timeout: 15000 }).catch(() => {});
    const btn = page.getByRole('button', { name: letter, exact: true }).first();
    if ((await btn.count()) === 0) {
      letterResults.push({ letter, missingButton: true });
      console.log(' MISSING');
      continue;
    }
    const disabled = await btn.isDisabled().catch(() => false);
    const className = (await btn.getAttribute('class')) || '';
    const baseCount = await btn.getAttribute('data-base-count');
    if (disabled || className.includes('is-empty')) {
      letterResults.push({
        letter,
        url: page.url(),
        disabled: true,
        empty: true,
        countNum: baseCount != null ? parseInt(baseCount, 10) : 0,
        countLabel: `${letter}: disabled/empty (data-base-count=${baseCount})`,
        wordLinkCount: 0,
        showMore: false,
        snippet: 'Letter button disabled / is-empty',
      });
      await shot(page, `desktop-browse-letter-${letter}-disabled`);
      console.log(` DISABLED base=${baseCount}`);
      continue;
    }
    await btn.click();
    await page.waitForTimeout(1100);
    const text = await bodyText(page);
    const countMatch = text.match(new RegExp(`${letter}:\\s*([\\d\\s\\u00a0]+)\\s*запис`, 'i'));
    const wordHrefs = await page.locator('a[href*="/lexicon/"]').evaluateAll((els) =>
      els
        .map((a) => a.href)
        .filter((h) => h.includes('/lexicon/') && !h.includes('/browse') && !/\/lexicon\/?$/.test(h) && !h.includes('practice')),
    );
    const uniqueWords = [...new Set(wordHrefs)];
    // paging / show more
    let showMore = false;
    const more = page.locator('button', { hasText: /Показати ще|Show more|ще/i });
    if ((await more.count()) > 0 && (await more.first().isVisible().catch(() => false))) {
      showMore = true;
      if (letter === 'А' || letter === 'П') {
        await more.first().click();
        await page.waitForTimeout(800);
        await shot(page, `desktop-browse-${letter}-show-more`);
      }
    }
    const empty = uniqueWords.length === 0;
    letterResults.push({
      letter,
      url: page.url(),
      countLabel: countMatch?.[0] || null,
      countNum: countMatch ? parseInt(countMatch[1].replace(/\s/g, ''), 10) : null,
      wordLinkCount: uniqueWords.length,
      showMore,
      empty,
      snippet: snip(text, 220),
    });
    if (['А', 'Ж', 'Ц', 'Ю', 'Я', 'Ґ', 'Ь'].includes(letter) || empty) {
      await shot(page, `desktop-browse-letter-${letter}`);
    }
    console.log(` ${uniqueWords.length}w ${countMatch?.[0] || '?'}`);
  }

  const emptyLetters = letterResults.filter((r) => r.empty || r.missingButton);
  const zeroCount = letterResults.filter((r) => r.countNum === 0);
  addFinding({
    surface: '/lexicon/browse all letters',
    repro: 'Click every button.atlas-letter-link А–Я; record counts and word links',
    what: `Probed ${letterResults.length} letters. Empty/missing: ${emptyLetters.map((e) => e.letter).join(',') || 'none'}. Zero-count labels: ${zeroCount.map((z) => z.letter).join(',') || 'none'}. Ж example: ${JSON.stringify(letterResults.find((r) => r.letter === 'Ж'))}. Full table in evidence.`,
    hurts: 'Any letter with zero rows looks like a broken alphabet index.',
    severity: emptyLetters.length || zeroCount.length ? 'major' : 'polish',
    screenshot: 'ui-scout-report/shots/desktop-browse-letter-*',
    evidence: { letterResults, console: ev.console.slice(-10), network: ev.network4xx.slice(-15) },
  });

  // Pick words from Ж Ц Ю
  async function firstWordFrom(letter) {
    await goto(page, `${BASE}/lexicon/browse/`);
    await page.locator('button.atlas-letter-link').first().waitFor({ state: 'visible', timeout: 15000 });
    await page.getByRole('button', { name: letter, exact: true }).first().click();
    await page.waitForTimeout(1000);
    const links = await page.locator('a[href*="/lexicon/"]').evaluateAll((els) =>
      els
        .map((a) => ({ href: a.href, text: (a.textContent || '').trim().split('\n')[0].trim() }))
        .filter((x) => x.href.includes('/lexicon/') && !x.href.includes('/browse') && !/\/lexicon\/?$/.test(x.href) && !x.href.includes('practice')),
    );
    return links[0] || null;
  }

  const pickZh = await firstWordFrom('Ж');
  const pickTs = await firstWordFrom('Ц');
  const pickYu = await firstWordFrom('Ю');

  // ----- 3. Word pages -----
  console.log('\n=== 3. Word pages ===');
  const wordTargets = [
    { label: 'a', url: `${BASE}/lexicon/${encodeURIComponent('а')}/` },
    { label: 'voda', url: `${BASE}/lexicon/${encodeURIComponent('вода')}/` },
    { label: 'alergiya', url: `${BASE}/lexicon/${encodeURIComponent('алергія')}/` },
  ];
  if (pickZh) wordTargets.push({ label: `zh-${pickZh.text}`, url: pickZh.href });
  if (pickTs) wordTargets.push({ label: `ts-${pickTs.text}`, url: pickTs.href });
  if (pickYu) wordTargets.push({ label: `yu-${pickYu.text}`, url: pickYu.href });

  const wordNotes = [];
  for (const w of wordTargets) {
    console.log('  word', w.label);
    const netBefore = ev.network4xx.length;
    const consBefore = ev.console.length;
    await goto(page, w.url, 'networkidle');
    await page.waitForTimeout(500);
    const text = await bodyText(page);
    const title = await page.title();
    const is404 = /404|не знайден|not found|Page Not Found/i.test(text + title);
    const sections = {
      meaning: /Значення|Meaning|ВТС|gloss|«/i.test(text),
      etymology: /Походження|Етимолог|ЕСУМ|Etymolog/i.test(text),
      morphology: /Морфологія|форм|Morpholog|парадигм/i.test(text),
      relations: /Синонім|Паронім|Related|зв.яз|Matching/i.test(text),
      phraseology: /Фразеолог|Phrase/i.test(text),
      course: /Курс|модул|Course|module/i.test(text),
      audio: (await page.locator('audio, [class*="audio"], button[aria-label*="play" i], button[aria-label*="Listen" i]').count()) > 0,
      practiceLink: /Практикувати|Practice this/i.test(text),
    };

    // etymology toggle / details
    let ety = null;
    const etyBtn = page.locator('button, summary, details').filter({ hasText: /ЕСУМ|етимолог|походження|Etymolog/i }).first();
    if ((await etyBtn.count()) > 0) {
      await etyBtn.click().catch(() => {});
      await page.waitForTimeout(400);
      ety = 'clicked';
      await shot(page, `desktop-word-${w.label.replace(/[^\w\u0400-\u04FF-]/g, '').slice(0, 30)}-ety`);
    }

    const links = await page.locator('main a[href], article a[href]').evaluateAll((els) =>
      els.map((a) => ({ text: (a.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60), href: a.href })),
    );

    // click practice link if present (then back)
    const prac = page.locator('a').filter({ hasText: /Практикувати|Practice this/i }).first();
    let practiceHref = null;
    if ((await prac.count()) > 0) {
      practiceHref = await prac.getAttribute('href');
    }

    const sp = await shot(page, `desktop-word-${w.label.replace(/[^\w\u0400-\u04FF-]/g, '').slice(0, 40)}`);
    const note = {
      ...w,
      title,
      finalUrl: page.url(),
      is404,
      sections,
      ety,
      linkCount: links.length,
      links: links.slice(0, 40),
      practiceHref,
      ukOnly: ukOnlyLines(text).slice(0, 30),
      snippet: snip(text, 700),
      screenshot: sp,
      consoleDelta: ev.console.slice(consBefore),
      networkDelta: ev.network4xx.slice(netBefore),
    };
    wordNotes.push(note);
    addFinding({
      surface: `word page ${w.label}`,
      repro: `Open ${w.url}`,
      what: `title="${title}"; 404=${is404}; sections=${JSON.stringify(sections)}; etyToggle=${ety}; main links=${links.length}; practiceHref=${practiceHref}. ${snip(text, 400)}`,
      hurts: is404
        ? 'Broken lemma URL breaks browse/search trust.'
        : 'Missing sections (audio/relations/etymology) leave the entry feeling incomplete.',
      severity: is404 ? 'blocker' : 'minor',
      screenshot: sp,
      evidence: { links: links.slice(0, 25), console: note.consoleDelta, network: note.networkDelta },
    });
  }

  // Follow links on voda page (sample)
  await goto(page, `${BASE}/lexicon/${encodeURIComponent('вода')}/`, 'networkidle');
  const vodaLinks = await page.locator('main a[href], article a[href]').evaluateAll((els) =>
    els.map((a) => a.href),
  );
  const uniqueVoda = [...new Set(vodaLinks.filter((h) => h.startsWith(BASE)))].slice(0, 12);
  const linkProbe = [];
  for (const href of uniqueVoda) {
    const resp = await page.goto(href, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch((e) => null);
    await page.waitForTimeout(400);
    const t = await page.title();
    const broken = /404|Not Found/i.test(t) || (resp && resp.status() >= 400);
    linkProbe.push({ href, title: t, status: resp?.status(), broken });
    if (broken) await shot(page, `desktop-voda-broken-link-${linkProbe.length}`);
  }
  const brokenLinks = linkProbe.filter((l) => l.broken);
  addFinding({
    surface: 'word page вода — follow all main links',
    repro: 'Open /lexicon/вода/; follow each main/article internal link',
    what: `Probed ${linkProbe.length} links; broken=${brokenLinks.length}: ${JSON.stringify(brokenLinks).slice(0, 500)}`,
    hurts: 'Dead in-page links strand learners mid-entry.',
    severity: brokenLinks.length ? 'major' : 'polish',
    screenshot: wordNotes.find((w) => w.label === 'voda')?.screenshot || browseShot,
    evidence: { linkProbe },
  });

  // ----- 4. Practice -----
  console.log('\n=== 4. Practice ===');
  await goto(page, `${BASE}/lexicon/practice`, 'networkidle');
  const practiceLandingUrl = page.url();
  const practiceHubShot = await shot(page, 'desktop-practice-hub');
  const practiceText = await bodyText(page);
  const practiceUkOnly = ukOnlyLines(practiceText);
  addFinding({
    surface: '/lexicon/practice redirect + hub language',
    repro: 'Visit /lexicon/practice; inventory chrome language',
    what: `Redirects to ${practiceLandingUrl}. Hub mixes dual lines (UA then / EN) for many stats, but H1 is "Практика" alone; back link "← Слова дня"; eyebrow "СЛОВА ДНЯ · ПРАКТИКА"; intro paragraph is Ukrainian-only. Locale toggle still "УКРENG". UK-only lines (${practiceUkOnly.length}): ${practiceUkOnly.slice(0, 35).join(' · ')}`,
    hurts: 'Absolute beginner cannot understand UA-only intro/back-link/H1; owner requires dual-language practice chrome.',
    severity: 'blocker',
    screenshot: practiceHubShot,
    evidence: { ukOnly: practiceUkOnly, console: ev.console.slice(-5), network: ev.network4xx.slice(-5) },
  });

  // Start today session
  const startBtn = page.locator('button.lexicon-session-primary, button', { hasText: /Почати сесію|Start session/i }).first();
  await startBtn.click();
  await page.waitForTimeout(1500);
  const session1Shot = await shot(page, 'desktop-practice-session-started');
  const session1Text = await bodyText(page);
  const session1Uk = ukOnlyLines(session1Text);
  addFinding({
    surface: 'practice — Start session (today)',
    repro: 'Click "Почати сесію / Start session"',
    what: `URL=${page.url()}. Screen: ${snip(session1Text, 700)}. UK-only: ${session1Uk.slice(0, 25).join(' · ')}`,
    hurts: 'In-session chrome that is UA-only blocks A1 completion of a review.',
    severity: 'blocker',
    screenshot: session1Shot,
    evidence: { ukOnly: session1Uk },
  });

  // Keyboard run-through in current session
  for (const key of ['Space', 'Enter', 'Digit1', 'Digit2', 'ArrowRight', 'KeyN', 'Escape']) {
    await page.keyboard.press(key).catch(() => {});
    await page.waitForTimeout(350);
  }
  const kbShot = await shot(page, 'desktop-practice-keyboard-pass');
  addFinding({
    surface: 'practice keyboard-only',
    repro: 'In a started session, press Space, Enter, 1, 2, ArrowRight, N, Escape',
    what: `After keys, URL=${page.url()}; ${snip(await bodyText(page), 450)}`,
    hurts: 'Keyboard dead-ends force mouse-only practice.',
    severity: 'major',
    screenshot: kbShot,
  });

  // Exit back to hub — try Escape or back link
  await goto(page, `${BASE}/words-of-the-day/practice/`);
  const modeNames = ['Флешкартки', 'Добір пар', 'Вибір', 'Пропуск', 'Наголос', 'Група', 'Форма', 'Синоніми', 'Пароніми', 'Спадщина'];
  const modeObs = [];
  for (const mode of modeNames) {
    console.log('  mode', mode);
    await goto(page, `${BASE}/words-of-the-day/practice/`);
    const card = page.locator('button.mode-card', { hasText: mode }).first();
    if ((await card.count()) === 0) {
      modeObs.push({ mode, missing: true });
      continue;
    }
    await card.click();
    await page.waitForTimeout(1400);
    const text = await bodyText(page);
    const sp = await shot(page, `desktop-practice-mode-${mode.replace(/\s+/g, '-')}`);
    const uk = ukOnlyLines(text);
    // interact
    const answerBtn = page.locator('button').filter({ hasText: /Показати|Show|Перевір|Check|Знаю|Не знаю|Again|Good|Hard|Easy|Далі|Next/i }).first();
    if ((await answerBtn.count()) > 0) {
      await answerBtn.click().catch(() => {});
      await page.waitForTimeout(500);
    } else {
      // choice: click first option-like button in main
      const opt = page.locator('main button, [class*="option"] button, [class*="choice"] button').nth(0);
      if ((await opt.count()) > 0) await opt.click().catch(() => {});
      await page.waitForTimeout(400);
      // cloze: type something
      const cloze = page.locator('input:not([type="hidden"])').first();
      if ((await cloze.count()) > 0) {
        await cloze.fill('тест');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(400);
      }
    }
    // matching: click two items
    const matchItems = page.locator('main button, [class*="match"] button');
    if ((await matchItems.count()) >= 2) {
      await matchItems.nth(0).click().catch(() => {});
      await matchItems.nth(1).click().catch(() => {});
      await page.waitForTimeout(400);
    }
    const after = await shot(page, `desktop-practice-mode-${mode.replace(/\s+/g, '-')}-after`);
    modeObs.push({
      mode,
      url: page.url(),
      ukOnly: uk.slice(0, 40),
      snippet: snip(text, 500),
      screenshot: sp,
      afterScreenshot: after,
      afterSnippet: snip(await bodyText(page), 350),
    });
    addFinding({
      surface: `practice mode: ${mode}`,
      repro: `On practice hub, click mode-card "${mode}"; attempt one answer/advance`,
      what: `URL=${page.url()}. ${snip(text, 450)}. UK-only sample: ${uk.slice(0, 20).join(' · ')}`,
      hurts: 'Each mode is a learner path; UA-only prompts or broken start = dead exercise type.',
      severity: /немає|empty|error|не вдалося|try again|Спробувати ще/i.test(text) ? 'major' : 'minor',
      screenshot: sp,
      evidence: { ukOnly: uk.slice(0, 30) },
    });
  }

  // ----- 5. WOTD + reading -----
  console.log('\n=== 5. WOTD + reading ===');
  await goto(page, `${BASE}/words-of-the-day/`, 'networkidle');
  const wotdShot = await shot(page, 'desktop-wotd');
  const wotdText = await bodyText(page);
  addFinding({
    surface: '/words-of-the-day/',
    repro: 'Open WOTD landing',
    what: `Dual H1 "Слова дня / Words of the Day". Practice CTA present. Level chips A1–C2. ${snip(wotdText, 500)}`,
    hurts: 'WOTD is dual-titled while Atlas/Practice H1s are often UA-only — inconsistent mental model.',
    severity: 'minor',
    screenshot: wotdShot,
  });

  const firstWord = page.locator('a[href*="/lexicon/"]').first();
  if ((await firstWord.count()) > 0) {
    const href = await firstWord.getAttribute('href');
    await firstWord.click();
    await page.waitForTimeout(1000);
    const cross = await shot(page, 'desktop-wotd-to-atlas');
    addFinding({
      surface: 'WOTD → Atlas word',
      repro: 'Click first word card on WOTD',
      what: `href=${href}; landed ${page.url()}; title=${await page.title()}`,
      hurts: 'Broken daily-word links break the WOTD habit loop.',
      severity: /404|Not Found/i.test(await page.title()) ? 'blocker' : 'polish',
      screenshot: cross,
    });
  }

  // Reading reference
  await goto(page, `${BASE}/`);
  const readingNav = page.locator('a').filter({ hasText: /Reading reference|Читан/i }).first();
  let readingHref = null;
  if ((await readingNav.count()) > 0) {
    readingHref = await readingNav.getAttribute('href');
    await readingNav.click();
    await page.waitForTimeout(1000);
  }
  // Prefer a concrete reading page if listing
  const deep = page.locator('main a[href*="/reading"], main a[href*="a1"], main a[href*="module"]').first();
  if ((await deep.count()) > 0) {
    await deep.click().catch(() => {});
    await page.waitForTimeout(900);
  }
  const readingShot = await shot(page, 'desktop-reading');
  addFinding({
    surface: 'Reading reference cross-nav',
    repro: 'From site nav open Reading reference; open first content link if present',
    what: `nav href=${readingHref}; URL=${page.url()}; title=${await page.title()}; ${snip(await bodyText(page), 350)}`,
    hurts: 'Nav label language (EN "Reading reference") vs UA atlas chrome inconsistency.',
    severity: 'minor',
    screenshot: readingShot,
  });

  // ----- 6. 404s -----
  console.log('\n=== 6. 404s ===');
  for (const bad of ['неіснуючесловоxyzqqq', 'zzzz-not-a-lemma-999']) {
    await goto(page, `${BASE}/lexicon/${encodeURIComponent(bad)}/`);
    const t = await bodyText(page);
    const sp = await shot(page, `desktop-404-${bad.slice(0, 18)}`);
    const hasRecovery = /search|пошук|browse|перегляд|atlas|атлас|home|додому/i.test(t);
    addFinding({
      surface: '404 non-existent word',
      repro: `Open /lexicon/${bad}/`,
      what: `URL=${page.url()}; title=${await page.title()}; recovery links apparent=${hasRecovery}. ${snip(t, 450)}`,
      hurts: '404 without recovery search/browse leaves learners stuck after a typo.',
      severity: hasRecovery ? 'minor' : 'major',
      screenshot: sp,
      evidence: { console: ev.console.slice(-5), network: ev.network4xx.slice(-8) },
    });
  }

  writeFileSync(join(ROOT, 'letter-results.json'), JSON.stringify(letterResults, null, 2));
  writeFileSync(join(ROOT, 'word-pages.json'), JSON.stringify(wordNotes, null, 2));
  writeFileSync(join(ROOT, 'practice-modes.json'), JSON.stringify(modeObs, null, 2));
  await ctx.close();
  return { letterResults, wordNotes, modeObs };
}

// ===================== MOBILE =====================
async function scoutMobile(browser) {
  console.log('\n=== MOBILE 390px ===');
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    locale: 'en-US',
  });
  const page = await ctx.newPage();
  page.setDefaultTimeout(20000);
  const ev = bindEvidence(page, 'mobile-390');

  const pages = [
    ['mobile-lexicon', `${BASE}/lexicon/`],
    ['mobile-browse', `${BASE}/lexicon/browse/`],
    ['mobile-word-voda', `${BASE}/lexicon/${encodeURIComponent('вода')}/`],
    ['mobile-practice', `${BASE}/words-of-the-day/practice/`],
    ['mobile-wotd', `${BASE}/words-of-the-day/`],
  ];

  for (const [name, url] of pages) {
    await goto(page, url, 'networkidle');
    const ov = await overflowCheck(page);
    const sp = await shot(page, name);
    const vp = await viewportShot(page, `${name}-viewport`);
    const text = await bodyText(page);
    addFinding({
      surface: `${name} @390px`,
      repro: `Open ${url} at 390×844`,
      what: `horizontalOverflow=${ov.overflow} (scrollWidth=${ov.scrollWidth}, clientWidth=${ov.clientWidth}). UK-only sample: ${ukOnlyLines(text).slice(0, 15).join(' · ')}. ${snip(text, 350)}`,
      hurts: ov.overflow ? 'Horizontal scroll on phone breaks reading.' : 'Mobile density/language issues impede phone learners.',
      severity: ov.overflow ? 'major' : 'minor',
      screenshot: vp,
      evidence: { full: sp, overflow: ov, console: ev.console.slice(-4), network: ev.network4xx.slice(-4) },
    });
  }

  // Browse letter on mobile
  await goto(page, `${BASE}/lexicon/browse/`);
  await page.getByRole('button', { name: 'Ж', exact: true }).first().tap().catch(() =>
    page.getByRole('button', { name: 'Ж', exact: true }).first().click(),
  );
  await page.waitForTimeout(1000);
  const mBrowse = await shot(page, 'mobile-browse-zh');
  addFinding({
    surface: 'mobile browse letter Ж',
    repro: 'Tap Ж on browse @390px',
    what: `URL=${page.url()}; overflow=${JSON.stringify(await overflowCheck(page))}; ${snip(await bodyText(page), 350)}`,
    hurts: 'Letter strip or result list may wrap/clip on narrow screens.',
    severity: 'minor',
    screenshot: mBrowse,
  });

  // Mobile typeahead
  await goto(page, `${BASE}/lexicon/`);
  const input = await searchInput(page);
  if (input) {
    await input.tap().catch(() => input.click());
    await input.fill('вода');
    await page.waitForTimeout(800);
    const sp = await shot(page, 'mobile-typeahead-voda');
    addFinding({
      surface: 'mobile typeahead',
      repro: 'Type вода in search @390px',
      what: `options=${await page.locator('[role="option"]').count()}; ${snip(await bodyText(page), 300)}`,
      hurts: 'Mobile keyboard + suggestions overlap can hide results.',
      severity: 'minor',
      screenshot: sp,
    });
  }

  // Mobile practice modes language
  await goto(page, `${BASE}/words-of-the-day/practice/`);
  await page.locator('button', { hasText: /Почати сесію|Start session/i }).first().tap().catch(async () => {
    await page.locator('button', { hasText: /Почати сесію|Start session/i }).first().click();
  });
  await page.waitForTimeout(1200);
  const mSession = await shot(page, 'mobile-practice-session');
  const mText = await bodyText(page);
  addFinding({
    surface: 'mobile practice session language',
    repro: 'Start session on 390px; list UA-only chrome',
    what: `UK-only: ${ukOnlyLines(mText).slice(0, 40).join(' · ')}. ${snip(mText, 400)}`,
    hurts: 'Phone is where beginners practice; UA-only chrome is a hard stop.',
    severity: 'blocker',
    screenshot: mSession,
    evidence: { ukOnly: ukOnlyLines(mText) },
  });

  await goto(page, `${BASE}/words-of-the-day/practice/`);
  for (const mode of ['Флешкартки', 'Вибір', 'Пропуск']) {
    await goto(page, `${BASE}/words-of-the-day/practice/`);
    await page.locator('button.mode-card', { hasText: mode }).first().tap().catch(async () => {
      await page.locator('button.mode-card', { hasText: mode }).first().click();
    });
    await page.waitForTimeout(1200);
    const sp = await shot(page, `mobile-mode-${mode}`);
    addFinding({
      surface: `mobile practice mode ${mode}`,
      repro: `Tap mode-card ${mode} @390px`,
      what: snip(await bodyText(page), 400),
      hurts: 'Mobile layout may clip options/inputs for this exercise.',
      severity: (await overflowCheck(page)).overflow ? 'major' : 'minor',
      screenshot: sp,
    });
  }

  await ctx.close();
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    await scoutDesktop(browser);
    await scoutMobile(browser);
  } finally {
    await browser.close();
  }
  writeFileSync(join(ROOT, 'findings.json'), JSON.stringify({ generated: '2026-07-17', findings, pageEvidence }, null, 2));
  console.log(`\nDONE findings=${findings.length} shots=${shotIdx}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
