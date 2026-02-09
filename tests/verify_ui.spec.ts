import { test, expect } from '@playwright/test';
import { spawn } from 'child_process';

test('Batch Manager UI loads and has controls', async ({ page }) => {
    // Start the server
    const server = spawn('python3', ['scripts/playground_server.py'], {
        env: { ...process.env, PYTHONPATH: process.cwd() }
    });

    // Wait for server to start
    await new Promise(resolve => setTimeout(resolve, 3000));

    try {
        await page.goto('http://localhost:8765/playground-batch-manager.html');

        // Check for title
        await expect(page.locator('h1')).toContainText('Batch Management');

        // Check for controls
        await expect(page.locator('button:has-text("Launch Batch")')).toBeVisible();
        await expect(page.locator('select#track-select')).toBeVisible();

        // Check for status grid
        await expect(page.locator('#status-grid')).toBeVisible();

        // Take a screenshot
        await page.screenshot({ path: 'batch-manager-ui.png' });

    } finally {
        server.kill();
    }
});
