#!/usr/bin/env npx ts-node
/// <reference lib="dom" />
/**
 * HTML Validator (Puppeteer-based)
 * 
 * Validates generated HTML files by actually loading them in a headless browser.
 * Checks for:
 * 1. Console Errors (JS parsing/execution issues).
 * 2. Broken Resource Links (Images/Audio 404s).
 * 3. Broken Internal Links (Anchors to missing IDs).
 * 4. Structural Integrity (Title, Main Content).
 */

import { readdir } from 'fs/promises';
import { join, resolve } from 'path';
import { existsSync } from 'fs';
import puppeteer, { Browser, Page } from 'puppeteer';

const OUTPUT_DIR = join(__dirname, '..', 'output', 'html');

export interface ValidationResult {
    file: string;
    passed: boolean;
    errors: string[];
    warnings: string[];
}

/**
 * Checks basic HTML structure (Title, Main, Layout Sections).
 */
async function checkBasicStructure(page: Page, errors: string[]) {
    const title = await page.title();
    if (!title || title.trim() === '') errors.push('Missing or empty <title>');

    if (!await page.$('main')) errors.push('Missing <main> element');

    const requiredIds = ['lesson', 'vocab'];
    for (const id of requiredIds) {
        if (!await page.$(`#${id}`)) errors.push(`Missing Layout Section: #${id}`);
    }
}

/**
 * Checks for broken resources and links.
 */
async function checkResources(page: Page, filePath: string, errors: string[]) {
    // Check Anchor Links
    const anchors = await page.$$eval('a[href^="#"]', els => els.map(e => e.getAttribute('href')));
    for (const anchor of anchors) {
        if (anchor && anchor.length > 1) {
            const id = anchor.substring(1);
            if (!await page.$(`#${id}, [name="${id}"]`)) {
                errors.push(`Broken Anchor: ${anchor} (Target ID not found)`);
            }
        }
    }

    // Check Navigation Links
    const navLinks = await page.$$eval('a[href]:not([href^="#"]):not([href^="http"])', els => els.map(e => e.getAttribute('href')));
    for (const link of navLinks) {
        if (link) {
            const targetPath = resolve(filePath, '..', link);
            if (!existsSync(targetPath)) errors.push(`Broken Link: ${link} (File not found)`);
        }
    }

    // Check Images (0-width)
    const brokenImages = await page.$$eval('img', els => els.filter(e => (e as HTMLImageElement).naturalWidth === 0).length);
    if (brokenImages > 0) errors.push(`${brokenImages} broken images detected (naturalWidth=0)`);
}

/**
 * Checks activity sections and deep DOM integrity.
 */
async function checkActivityIntegrity(page: Page, errors: string[], warnings: string[]) {
    // Check Activity Section Count
    const activitySections = await page.$$('section[id^="activity-"]');
    if (activitySections.length < 8) {
        warnings.push(`Low Activity Count: Found ${activitySections.length} (Expected 8+)`);
    }

    // Deep Content Integrity Check: Data vs DOM
    const dataErrors = await page.evaluate(() => {
        const errs: string[] = [];
        const data = (window as any).activitiesData;

        if (!data || !Array.isArray(data)) {
            return [`CRITICAL: activitiesData missing or invalid on page. Check generate script.`];
        }

        const getCounts = (activity: any, container: Element | null) => {
            if (activity.type === 'fill-blank' || activity.type === 'gap-fill') {
                return {
                    expected: activity.data.items?.length || 0,
                    actual: container?.querySelectorAll('.fill-question').length || 0
                };
            }
            if (activity.type === 'anagram') {
                return {
                    expected: activity.data.items?.length || 0,
                    actual: container?.querySelectorAll('.anagram-question').length || 0
                };
            }
            return null;
        };

        // Validate Data vs DOM Count
        for (const activity of data) {
            const section = document.getElementById(activity.id);
            if (!section) {
                errs.push(`Activity #${activity.id}: Section missing in DOM.`);
                continue;
            }

            const container = section.querySelector('[id$="-container"]');
            const counts = getCounts(activity, container);

            if (counts && counts.actual !== counts.expected) {
                errs.push(`Activity #${activity.id} (${activity.type}): Count Mismatch. Expected ${counts.expected}, found ${counts.actual}.`);
            }
        }
        return errs;
    });

    // Deep Content Integrity Check: Specific DOM Logic
    const domErrors = await page.evaluate(() => {
        const errs: string[] = [];

        // Fill-in
        document.querySelectorAll('.fill-container').forEach((c) => {
            const id = c.closest('section')?.id || 'unknown';
            const qs = c.querySelectorAll('.fill-question');
            if (qs.length === 0) errs.push(`Activity #${id} (Fill-in): No questions rendered.`);

            qs.forEach((q, idx) => {
                if (!q.querySelector('input, select')) errs.push(`Activity #${id} Q${idx + 1}: Missing inputs.`);
                const sel = q.querySelector('select');
                if (sel && sel.options.length <= 1) errs.push(`Activity #${id} Q${idx + 1}: Dropdown has no options.`);
            });
        });

        // Match-up
        document.querySelectorAll('.match-container').forEach((c) => {
            const id = c.closest('section')?.id || 'unknown';
            const left = c.querySelectorAll('.match-item[data-side="left"]').length;
            const right = c.querySelectorAll('.match-item[data-side="right"]').length;
            if (left === 0 || right === 0) errs.push(`Activity #${id}: Empty items.`);
            else if (left !== right) errs.push(`Activity #${id}: Unbalanced (L:${left}, R:${right}).`);
        });

        // Anagrams
        document.querySelectorAll('.anagram-question').forEach((q, idx) => {
            const id = q.closest('section')?.id || 'unknown';
            if (q.querySelectorAll('.anagram-letter').length <= 1) errs.push(`Activity #${id} Q${idx + 1}: Invalid letter count.`);
        });

        // General Interactive Check
        document.querySelectorAll('section[id^="activity-"]').forEach((s) => {
            if (!s.querySelector('button, input, select, [draggable="true"], .match-item')) {
                errs.push(`Activity #${s.id}: Non-interactive.`);
            }
        });

        return errs;
    });

    // Deep Content Integrity Check: Ambiguous Gaps
    const gapErrors = await page.evaluate(() => {
        const errs: string[] = [];
        const data = (window as any).activitiesData;

        if (!data || !Array.isArray(data)) return [];

        data.forEach((activity: any) => {
            if (activity.type === 'fill-blank' || activity.type === 'gap-fill') {
                activity.data.items?.forEach((item: any, i: number) => {
                    const gaps = (item.prompt || item.sentence || '').match(/_{2,}/g);
                    if (gaps && gaps.length > 1) {
                        errs.push(`Activity #${activity.id} (Fill-in) Q${i + 1}: Ambiguous Gaps (${gaps.length} gaps, 1 answer).`);
                    }
                });
            }
        });
        return errs;
    });

    errors.push(...dataErrors, ...domErrors, ...gapErrors);
}

/**
 Checks section ordering.
 */
async function checkSectionOrder(page: Page, errors: string[]) {
    const sections = await page.$$eval('section[id]', els => els.map(e => e.id));
    const lessonIdx = sections.indexOf('lesson');
    const vocabIdx = sections.indexOf('vocab');

    if (lessonIdx === -1 || vocabIdx === -1) return; // Already caught in basic structure

    if (lessonIdx > vocabIdx) errors.push('Section Order: #lesson appears after #vocab');

    const firstActivityIdx = sections.findIndex(id => id.startsWith('activity-'));
    if (firstActivityIdx !== -1 && firstActivityIdx < lessonIdx) {
        errors.push('Section Order: Activities appear before Lesson content');
    }
}

/**
 *
 */
export async function validateFile(browser: Browser, filePath: string): Promise<ValidationResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    const fileName = filePath.split('/').pop() || 'unknown';
    const page = await browser.newPage();

    page.on('console', msg => {
        if (msg.type() === 'error') errors.push(`Console Error: ${msg.text()}`);
    });

    page.on('requestfailed', req => {
        if (req.url().startsWith('file://')) errors.push(`Resource Failed: ${req.url()}`);
    });

    try {
        const response = await page.goto(`file://${resolve(filePath)}`, { waitUntil: 'networkidle0' });
        if (!response) {
            return { file: fileName, passed: false, errors: ['Failed to load page'], warnings };
        }

        await checkBasicStructure(page, errors);
        await checkResources(page, filePath, errors);
        await checkActivityIntegrity(page, errors, warnings);
        await checkSectionOrder(page, errors);

    } catch (err: any) {
        errors.push(`Crash: ${err.message}`);
    } finally {
        await page.close();
    }

    return {
        file: fileName,
        passed: errors.length === 0,
        errors,
        warnings
    };
}

/**
 *
 */
async function main() {
    const args = process.argv.slice(2);
    const targetLang = args[0] || 'l2-uk-en';
    const targetLevel = args[1] || 'a1';

    console.log(`\n🔍 Validating HTML for ${targetLang}/${targetLevel}...\n`);

    const dir = join(OUTPUT_DIR, targetLang, targetLevel);
    if (!existsSync(dir)) {
        console.error(`Directory not found: ${dir}`);
        process.exit(1);
    }

    const files = (await readdir(dir)).filter(f => f.endsWith('.html') && f !== 'index.html');
    if (files.length === 0) {
        console.error('No HTML files found.');
        process.exit(1);
    }

    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const results: ValidationResult[] = [];

    try {
        for (const file of files) {
            process.stdout.write(`  Checking ${file}... `);
            const result = await validateFile(browser, join(dir, file));
            results.push(result);
            console.log(result.passed ? '✅' : '❌');

            if (!result.passed) {
                result.errors.forEach(e => console.log(`    - ${e}`));
            }
        }
    } finally {
        await browser.close();
    }

    const passed = results.filter(r => r.passed).length;
    const failed = results.filter(r => !r.passed).length;

    console.log(`\n📊 Summary: ${passed} Passed, ${failed} Failed`);
    process.exit(failed > 0 ? 1 : 0);
}

if (require.main === module) {
    main().catch(console.error);
}
