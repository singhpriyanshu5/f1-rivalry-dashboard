// @ts-check
const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

async function selectDropdown(page, ariaLabel, optionText) {
    // Click the combobox button to open the popover
    await page.locator(`button[aria-label="${ariaLabel}"]`).click();
    await page.waitForTimeout(500);

    // Find and click the option text in the popover
    // Evidence renders options as clickable items with checkmarks
    await page.locator(`[data-melt-popover-content] >> text="${optionText}"`).click();
    await page.waitForTimeout(2000);
}

test.describe('F1 Dashboard Validation', () => {
    test.setTimeout(90000);

    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        await page.waitForTimeout(5000);
    });

    test('2025 Red Bull VER vs TSU - all sections render with both drivers', async ({ page }) => {
        await selectDropdown(page, 'Season', '2025');
        await selectDropdown(page, 'Constructor', 'Red Bull');
        await selectDropdown(page, 'Driver Pairing', 'VER vs TSU');
        await page.waitForTimeout(2000);

        await page.screenshot({ path: 'tests/screenshots/2025-rb-ver-tsu-full.png', fullPage: true });

        // Check Points Trajectory section
        const pointsSection = page.locator('.f1-section.blue');
        if (await pointsSection.count() > 0) {
            await pointsSection.screenshot({ path: 'tests/screenshots/2025-rb-ver-tsu-points.png' });
        }
    });

    test('2025 Red Bull LAW vs VER - early season rounds', async ({ page }) => {
        await selectDropdown(page, 'Season', '2025');
        await selectDropdown(page, 'Constructor', 'Red Bull');
        await selectDropdown(page, 'Driver Pairing', 'LAW vs VER');
        await page.waitForTimeout(2000);

        await page.screenshot({ path: 'tests/screenshots/2025-rb-law-ver-full.png', fullPage: true });
    });
});
