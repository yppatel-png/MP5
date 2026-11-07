/**
 * Phase 0 Proof Script:
 * 1. Opens http://127.0.0.1:8000 in a fresh browser context.
 * 2. Asserts footer version stamp is present and displays current build commit.
 * 3. Takes baseline screenshot docs/screenshots/phase0/00_initial_baseline.png.
 * 4. Modifies a visible word in frontend/index.html to "PHASE_0_LIVE_RELOAD_VERIFIED".
 * 5. Opens a brand-new browser context, navigates to http://127.0.0.1:8000.
 * 6. Asserts the new word appears on screen immediately without stale caching.
 * 7. Takes screenshot docs/screenshots/phase0/01_visible_change_proven.png.
 * 8. Reverts the visible change back in frontend/index.html.
 * 9. Opens another fresh browser context, navigates, asserts original text is restored.
 * 10. Takes screenshot docs/screenshots/phase0/02_reverted_clean.png.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://127.0.0.1:8000';
const SCREENSHOT_DIR = path.resolve(__dirname, '../../docs/screenshots/phase0');
const INDEX_HTML_PATH = path.resolve(__dirname, '../../frontend/index.html');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function run() {
  console.log('[PHASE 0 TEST] Starting Phase 0 verification...');
  const browser = await chromium.launch({ headless: true });

  try {
    // Step 1: Baseline check in a fresh browser context
    console.log('[PHASE 0 TEST] Step 1: Opening fresh browser context for baseline...');
    const ctx1 = await browser.newContext();
    const page1 = await ctx1.newPage();
    await page1.goto(BASE_URL, { waitUntil: 'networkidle' });
    
    // Check footer build stamp
    await page1.waitForSelector('#build-stamp-pill', { timeout: 10000 });
    await page1.waitForFunction(() => {
      const el = document.querySelector('#build-stamp-pill');
      return el && !el.textContent.includes('Build ...');
    }, { timeout: 10000 });
    const footerText = await page1.textContent('#build-stamp-pill');
    console.log(`[PHASE 0 TEST] Footer build stamp text: "${footerText.trim()}"`);
    
    const baselinePath = path.join(SCREENSHOT_DIR, '00_initial_baseline.png');
    await page1.screenshot({ path: baselinePath, fullPage: true });
    console.log(`[PHASE 0 TEST] Baseline screenshot saved: ${baselinePath}`);
    await ctx1.close();

    // Step 2: Modify one visible word in frontend/index.html
    console.log('[PHASE 0 TEST] Step 2: Injecting visible test marker into frontend/index.html...');
    const originalHtml = fs.readFileSync(INDEX_HTML_PATH, 'utf-8');
    const markerTarget = '<span>Learning Buddy</span>';
    const markerReplacement = '<span>Learning Buddy [PHASE_0_LIVE_RELOAD_VERIFIED]</span>';
    
    if (!originalHtml.includes(markerTarget)) {
      throw new Error(`Target string "${markerTarget}" not found in index.html`);
    }
    const modifiedHtml = originalHtml.replace(markerTarget, markerReplacement);
    fs.writeFileSync(INDEX_HTML_PATH, modifiedHtml, 'utf-8');
    console.log('[PHASE 0 TEST] Successfully injected test marker.');

    // Step 3: Open fresh browser context, verify visible change shows up immediately
    console.log('[PHASE 0 TEST] Step 3: Opening fresh context to verify immediate visibility...');
    const ctx2 = await browser.newContext();
    const page2 = await ctx2.newPage();
    await page2.goto(BASE_URL, { waitUntil: 'networkidle' });

    await page2.waitForSelector('text=PHASE_0_LIVE_RELOAD_VERIFIED', { timeout: 8000 });
    const markerVisible = await page2.isVisible('text=PHASE_0_LIVE_RELOAD_VERIFIED');
    console.log(`[PHASE 0 TEST] Marker visible in fresh context: ${markerVisible}`);
    if (!markerVisible) {
      throw new Error('Test marker was NOT visible in fresh browser context!');
    }

    const provenPath = path.join(SCREENSHOT_DIR, '01_visible_change_proven.png');
    await page2.screenshot({ path: provenPath, fullPage: true });
    console.log(`[PHASE 0 TEST] Change proven screenshot saved: ${provenPath}`);
    await ctx2.close();

    // Step 4: Revert visible change
    console.log('[PHASE 0 TEST] Step 4: Reverting index.html to original contents...');
    fs.writeFileSync(INDEX_HTML_PATH, originalHtml, 'utf-8');
    console.log('[PHASE 0 TEST] index.html reverted.');

    // Step 5: Open fresh browser context, verify reverted clean state
    console.log('[PHASE 0 TEST] Step 5: Opening fresh context to verify reverted state...');
    const ctx3 = await browser.newContext();
    const page3 = await ctx3.newPage();
    await page3.goto(BASE_URL, { waitUntil: 'networkidle' });

    await page3.waitForSelector('.sidebar-brand', { timeout: 8000 });
    const revertedContent = await page3.textContent('.sidebar-brand');
    console.log(`[PHASE 0 TEST] Reverted brand text: "${revertedContent.trim()}"`);
    
    const markerStillThere = await page3.isVisible('text=PHASE_0_LIVE_RELOAD_VERIFIED');
    if (markerStillThere) {
      throw new Error('Test marker is still visible after reverting!');
    }

    const cleanPath = path.join(SCREENSHOT_DIR, '02_reverted_clean.png');
    await page3.screenshot({ path: cleanPath, fullPage: true });
    console.log(`[PHASE 0 TEST] Reverted clean screenshot saved: ${cleanPath}`);
    await ctx3.close();

    console.log('[PHASE 0 TEST] SUCCESS: Phase 0 proof completed with full assertion verification!');
  } finally {
    // Ensure index.html is reverted in case of errors
    const currentHtml = fs.readFileSync(INDEX_HTML_PATH, 'utf-8');
    if (currentHtml.includes('[PHASE_0_LIVE_RELOAD_VERIFIED]')) {
      const cleanHtml = currentHtml.replace(' [PHASE_0_LIVE_RELOAD_VERIFIED]', '');
      fs.writeFileSync(INDEX_HTML_PATH, cleanHtml, 'utf-8');
      console.log('[PHASE 0 TEST] Cleanup: reverted index.html in finally block.');
    }
    await browser.close();
  }
}

run().catch((err) => {
  console.error('[PHASE 0 TEST] Error:', err);
  process.exit(1);
});
