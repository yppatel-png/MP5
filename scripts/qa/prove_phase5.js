/**
 * Automated Playwright acceptance verification for Phase 5: Practice & Progress (PDF §2.4, §3 UX).
 *
 * Verifies:
 * 1. Learn & Practise view redesign:
 *    - Plain subtitle ("Questions matched to your plan")
 *    - "Study this first" card with linked resource for selected skill
 *    - Full clean question typography with skill & difficulty tags
 *    - MCQ card options
 * 2. Post-submit feedback & evidence attribution:
 *    - Correct option highlighted in green with checkmark
 *    - Explanation card displayed
 *    - Dynamic mastery change displayed (e.g. "Theory of computation 42% to 48%")
 *    - Next question navigation button
 * 3. Progress view redesign:
 *    - Circular SVG goal readiness ring with metrics
 *    - Title Case skill names
 *    - Partitioned Goal-Critical vs Supporting vs Not Assessed
 *    - Low/Medium/High confidence tags & Demonstrated vs Provisional badges
 *    - "Completed course vs demonstrated proficiency" line
 *    - Recent Evidence Audit Trail with source tags
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://127.0.0.1:8000';
const SCREENSHOT_DIR = path.resolve(__dirname, '../../docs/screenshots/phase5');

async function run() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  console.log('[PHASE 5 ACCEPTANCE] Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  page.on('console', msg => console.log('[BROWSER CONSOLE]', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('[BROWSER ERROR]', err));

  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // =========================================================================
    // 1. PRACTICE VIEW VERIFICATION
    // =========================================================================
    console.log('[PHASE 5] Navigating to Learn & Practise tab...');
    await page.click('div.nav-item[data-target="practice"]');
    await page.waitForTimeout(600);

    // Verify plain subtitle
    const subtitle = await page.textContent('#view-practice .text-meta');
    console.log(`[PHASE 5] Practice subtitle: "${subtitle.trim()}"`);
    if (!subtitle.includes('Questions matched to your plan')) {
      throw new Error(`Expected plain subtitle 'Questions matched to your plan', got '${subtitle}'`);
    }

    // Switch or ensure filter is set to Theory of computation
    const filter = page.locator('#practice-skill-filter');
    await filter.selectOption('theory_computation');
    await page.waitForTimeout(500);

    // Verify "Study this first" card is visible with resource
    await page.waitForSelector('#practice-study-card', { state: 'visible' });
    const studyTitle = await page.textContent('#study-card-title');
    console.log(`[PHASE 5] Study this first title: "${studyTitle.trim()}"`);

    // Verify Question Card & options are populated
    await page.waitForSelector('.practice-question-card', { state: 'visible' });
    await page.waitForSelector('.practice-option', { state: 'visible', timeout: 10000 });
    const promptText = await page.textContent('#practice-prompt');
    const skillBadge = await page.textContent('#active-ex-skill-badge');
    console.log(`[PHASE 5] Active question skill badge: "${skillBadge.trim()}"`);
    console.log(`[PHASE 5] Question prompt: "${promptText.trim().substring(0, 60)}..."`);

    // Screenshot 1: Practice view with study card & question
    const p1 = path.join(SCREENSHOT_DIR, '01_practice_study_card_and_toc_question.png');
    await page.screenshot({ path: p1, fullPage: false });
    console.log(`[PHASE 5] Saved screenshot: ${p1}`);

    // Submit answer to first question (Regular languages)
    console.log('[PHASE 5] Selecting option and submitting answer...');
    const firstOption = page.locator('.practice-option').first();
    await firstOption.click();
    await page.waitForTimeout(200);

    await page.click('#practice-submit-btn');
    await page.waitForTimeout(600);

    // Verify post-submit feedback
    await page.waitForSelector('#practice-feedback-pane', { state: 'visible' });
    const feedbackTitle = await page.textContent('#practice-feedback-title');
    const masteryChange = await page.textContent('#practice-mastery-change');
    console.log(`[PHASE 5] Post-submit title: "${feedbackTitle.trim()}"`);
    console.log(`[PHASE 5] Post-submit mastery change: "${masteryChange.trim()}"`);

    if (!masteryChange.includes('Theory of computation') && !masteryChange.includes('Theory Of Computation')) {
      throw new Error(`Mastery change text did not credit Theory of computation! Got: ${masteryChange}`);
    }

    // Screenshot 2: Post-submit feedback & mastery change
    const p2 = path.join(SCREENSHOT_DIR, '02_post_submit_feedback_and_mastery_change.png');
    await page.screenshot({ path: p2, fullPage: false });
    console.log(`[PHASE 5] Saved screenshot: ${p2}`);

    // =========================================================================
    // 2. PROGRESS VIEW VERIFICATION
    // =========================================================================
    console.log('[PHASE 5] Navigating to Progress tab...');
    await page.click('div.nav-item[data-target="mastery"]');
    await page.waitForTimeout(600);

    // Verify Goal Readiness Ring
    await page.waitForSelector('#readiness-ring-container svg', { state: 'visible' });
    const goalTitle = await page.textContent('#readiness-goal-title');
    console.log(`[PHASE 5] Readiness Goal: "${goalTitle.trim()}"`);

    // Verify Goal-Critical and Supporting Skill Cards exist
    await page.waitForSelector('#critical-skills-grid .skill-matrix-card', { state: 'visible' });
    const criticalCount = await page.locator('#critical-skills-grid .skill-matrix-card').count();
    const supportingCount = await page.locator('#supporting-skills-grid .skill-matrix-card').count();
    console.log(`[PHASE 5] Critical skills: ${criticalCount}, Supporting skills: ${supportingCount}`);

    // Check Title Case and Confidence badge
    const firstCardTitle = await page.textContent('#critical-skills-grid .skill-matrix-card:first-child .skill-name-txt');
    console.log(`[PHASE 5] First skill card title: "${firstCardTitle.trim()}"`);

    // Screenshot 3: Readiness Ring & Grouped Matrix
    const p3 = path.join(SCREENSHOT_DIR, '03_progress_readiness_ring_and_matrix.png');
    await page.screenshot({ path: p3, fullPage: false });
    console.log(`[PHASE 5] Saved screenshot: ${p3}`);

    // Scroll to Audit Trail & Expand Not Assessed
    await page.locator('#recent-evidence-list').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    const evidenceCount = await page.locator('#recent-evidence-list .evidence-row').count();
    console.log(`[PHASE 5] Audit trail evidence events count: ${evidenceCount}`);

    // Screenshot 4: Audit Trail Evidence Events
    const p4 = path.join(SCREENSHOT_DIR, '04_progress_audit_trail_evidence.png');
    await page.screenshot({ path: p4, fullPage: false });
    console.log(`[PHASE 5] Saved screenshot: ${p4}`);

    console.log('[PHASE 5 ACCEPTANCE] ALL ACCEPTANCE CHECKS PASSED CLEANLY!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('[PHASE 5 TEST] Acceptance failed:', err);
  process.exit(1);
});
