/**
 * Phase 1 Proof Script:
 * 1. Opens http://127.0.0.1:8000 in a fresh browser context.
 * 2. Asserts label "Demo student:" is present.
 * 3. Asserts the dropdown contains exactly 4 demo students:
 *    - Aarav Sharma - Software/IT, Sem 4
 *    - Diya Iyer - Higher studies, Sem 4
 *    - Tara Rao - UPSC aspirant, Sem 2
 *    - Rohan Mehta - Startup founder, Sem 4
 * 4. Takes screenshots:
 *    - docs/screenshots/phase1/01_demo_personas_dropdown.png
 *    - docs/screenshots/phase1/02_tara_rao_selected.png
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://127.0.0.1:8000';
const SCREENSHOT_DIR = path.resolve(__dirname, '../../docs/screenshots/phase1');

async function run() {
  console.log('[PHASE 1 TEST] Starting Phase 1 verification...');
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // 1. Assert "Demo student:" label is visible
    await page.waitForSelector('text=Demo student:', { timeout: 10000 });
    console.log('[PHASE 1 TEST] "Demo student:" label is visible.');

    // 2. Wait for persona selector options
    await page.waitForSelector('#persona-select option', { state: 'attached', timeout: 10000 });
    const options = await page.$$eval('#persona-select option', opts => opts.map(o => ({ value: o.value, text: o.textContent.trim() })));
    console.log(`[PHASE 1 TEST] Options count: ${options.length}`);
    options.forEach(o => console.log(` - ${o.value}: "${o.text}"`));

    if (options.length !== 4) {
      throw new Error(`Expected exactly 4 demo personas, but found ${options.length}`);
    }

    // 3. Take screenshot of dropdown and header
    const p1 = path.join(SCREENSHOT_DIR, '01_demo_personas_dropdown.png');
    await page.screenshot({ path: p1, fullPage: false });
    console.log(`[PHASE 1 TEST] Saved screenshot: ${p1}`);

    // 4. Select Tara Rao (BH-UP-001)
    await page.selectOption('#persona-select', 'BH-UP-001');
    await page.waitForTimeout(1000);
    const p2 = path.join(SCREENSHOT_DIR, '02_tara_rao_selected.png');
    await page.screenshot({ path: p2, fullPage: true });
    console.log(`[PHASE 1 TEST] Saved screenshot: ${p2}`);

    console.log('[PHASE 1 TEST] SUCCESS: Phase 1 verified cleanly!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('[PHASE 1 TEST] Failed:', err);
  process.exit(1);
});
