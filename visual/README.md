# Visual regression tests

Screenshots key Clarivise pages and diffs them against committed baselines, so a
silent change to an important page fails CI instead of shipping. Catches the
"the AI quietly rewrote a page you weren''t looking at" problem.

## One-time setup
    npm install
    npx playwright install chromium

## Seed baselines (after eyeballing that the pages look correct)
    npm run test:visual:update
    git add visual/__snapshots__ && git commit -m "seed visual baselines"

## Run
    npm run test:visual

Pages are listed in `visual/visual.spec.ts` — add the Streamlit portal and Shield
dashboard URLs there once confirmed. Baselines live in `visual/__snapshots__/`.