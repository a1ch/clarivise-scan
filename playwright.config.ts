import { defineConfig, devices } from '@playwright/test';

/**
 * Visual-regression config for Clarivise surfaces.
 * Screenshots the live hosted pages and diffs them against committed baselines,
 * so a silent (AI or otherwise) rewrite of a key page fails CI instead of shipping.
 *
 * Seed baselines once:  npm run test:visual:update
 * Compare thereafter:   npm run test:visual
 */
export default defineConfig({
  testDir: './visual',
  snapshotDir: './visual/__snapshots__',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  },
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.02, animations: 'disabled' } },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});