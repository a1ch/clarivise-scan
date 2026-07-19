import { test, expect } from '@playwright/test';

/**
 * Visual-regression coverage for the Clarivise surfaces most likely to be
 * silently changed by an AI edit. Each page is screenshotted and diffed against
 * a committed baseline; drift fails CI.
 *
 * Add the portal + Shield dashboard URLs once confirmed (commented below).
 */
const PAGES: { name: string; url: string }[] = [
  { name: 'outlook-addin-taskpane', url: 'https://a1ch.github.io/clarivise-scan-outlook/taskpane.html' },
  { name: 'marketing-site',         url: 'https://a1ch.github.io/clarivise-site/' },
  // { name: 'scan-portal',      url: 'https://<your-streamlit-app>.streamlit.app/' },
  // { name: 'shield-dashboard', url: 'https://<your-dashboard-host>/' },
];

for (const p of PAGES) {
  test(`visual: ${p.name}`, async ({ page }) => {
    const resp = await page.goto(p.url, { waitUntil: 'networkidle', timeout: 30_000 });
    expect(resp?.ok(), `${p.url} returned HTTP ${resp?.status()}`).toBeTruthy();
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1500); // let webfonts / CDN scripts (office.js) settle
    await expect(page).toHaveScreenshot(`${p.name}.png`, { fullPage: true });
  });
}