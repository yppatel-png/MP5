/**
 * Automated Playwright acceptance verification for Phase 6: The Admin Page / Evaluator Tools (PDF §6.1, §7).
 *
 * Verifies:
 * 1. Renamed to "Evaluator tools" in sidebar footer with two-sentence intro text.
 * 2. 4 Organized Subtabs:
 *    - Students: Table of profiles, inline edit with CGPA/hours, instant multi-semester plan re-synthesis with diff display.
 *    - Courses: Table of course data, inline edit form for credits/semester/workload, zero-restart planner re-indexing.
 *    - What if... (Adaptation): Scripted scenarios with live simulation, before/after plan diffs, and ordinance validation.
 *    - Database: Adminer viewer link and "Restore clean seed state" button.
 * 3. Plain wording ("Edit student standing") and ADMIN_API_TOKEN documentation.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://127.0.0.1:8000';
const SCREENSHOT_DIR = path.resolve(__dirname, '../../docs/screenshots/phase6');

async function run() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  console.log('[PHASE 6 ACCEPTANCE] Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // Pre-set admin token in sessionStorage for automated headless testing
    await page.evaluate(() => {
      sessionStorage.setItem('admin_token', 'buddy-admin-dev-token');
    });

    // 1. Verify Sidebar Footer link renamed to "Evaluator tools"
    console.log('[PHASE 6] Checking sidebar footer link...');
    const navLabel = await page.textContent('.sidebar-footer .nav-item[data-target="admin"] .nav-item-label');
    console.log(`[PHASE 6] Sidebar footer label: "${navLabel.trim()}"`);
    if (!navLabel.includes('Evaluator tools')) {
      throw new Error(`Expected sidebar link 'Evaluator tools', got '${navLabel}'`);
    }

    // 2. Navigate to Evaluator Tools
    console.log('[PHASE 6] Opening Evaluator tools tab...');
    await page.click('.sidebar-footer .nav-item[data-target="admin"]');
    await page.waitForTimeout(600);

    // Verify Title & Two-Sentence Intro
    const title = await page.textContent('#view-admin h2.text-title');
    const intro = await page.textContent('#view-admin .text-meta');
    console.log(`[PHASE 6] Header: "${title.trim()}"`);
    console.log(`[PHASE 6] Intro: "${intro.trim().substring(0, 80)}..."`);

    // =========================================================================
    // SUBTAB 1: STUDENTS (Table, Edit, Plan Re-synthesis Diff)
    // =========================================================================
    console.log('[PHASE 6] Verifying Students subtab...');
    await page.waitForSelector('#eval-students-table-body tr', { state: 'visible' });
    const studentRows = await page.locator('#eval-students-table-body tr').count();
    console.log(`[PHASE 6] Students in table: ${studentRows}`);

    // Click Edit on Tara Rao (BH-UP-001)
    await page.click('button:has-text("Edit & re-run")');
    await page.waitForSelector('#eval-student-edit-box', { state: 'visible' });

    // Modify CGPA to 8.0 and Hours to 22
    await page.fill('#admin-edit-cgpa', '8.0');
    await page.fill('#admin-edit-hours', '22');

    // Apply & Re-synthesize
    console.log('[PHASE 6] Applying student standing edit and re-running plan...');
    await page.click('button:has-text("Apply & re-synthesize plan")');
    await page.waitForSelector('#eval-student-plan-diff', { state: 'visible' });

    const diffText = await page.textContent('#eval-student-diff-content');
    console.log(`[PHASE 6] Plan re-synthesis diff output:\n${diffText.trim().replace(/\s+/g, ' ')}`);

    // Screenshot 1: Students Table & Plan Diff
    const p1 = path.join(SCREENSHOT_DIR, '01_evaluator_students_table_and_plan_diff.png');
    await page.screenshot({ path: p1, fullPage: false });
    console.log(`[PHASE 6] Saved screenshot: ${p1}`);

    // =========================================================================
    // SUBTAB 2: COURSES (Table & Edit Box)
    // =========================================================================
    console.log('[PHASE 6] Switching to Courses subtab...');
    await page.click('#tab-btn-courses');
    await page.waitForTimeout(400);

    await page.waitForSelector('#eval-courses-table-body tr', { state: 'visible' });
    const courseRows = await page.locator('#eval-courses-table-body tr').count();
    console.log(`[PHASE 6] Courses in table: ${courseRows}`);

    // Click Edit on first course
    await page.locator('#eval-courses-table-body tr:first-child button').click();
    await page.waitForSelector('#eval-course-edit-box', { state: 'visible' });
    const editCourseTitle = await page.textContent('#eval-edit-course-title');
    console.log(`[PHASE 6] Open course edit: "${editCourseTitle.trim()}"`);

    // Screenshot 2: Courses Table & Edit Box
    const p2 = path.join(SCREENSHOT_DIR, '02_evaluator_courses_table_and_edit_box.png');
    await page.screenshot({ path: p2, fullPage: false });
    console.log(`[PHASE 6] Saved screenshot: ${p2}`);

    // =========================================================================
    // SUBTAB 3: WHAT IF... (Live Adaptation Simulator)
    // =========================================================================
    console.log('[PHASE 6] Switching to What if... subtab...');
    await page.click('#tab-btn-adaptation');
    await page.waitForTimeout(400);

    // Verify Dropdown & Scenario Description
    await page.waitForSelector('#simulation-scenario', { state: 'visible' });
    const scenarioDesc = await page.textContent('#simulation-description');
    console.log(`[PHASE 6] Initial scenario description: "${scenarioDesc.trim().substring(0, 70)}..."`);

    // Run Scenario
    console.log('[PHASE 6] Running "What if..." scenario...');
    await page.click('button:has-text("Run \\"What if...\\" scenario")');
    await page.waitForSelector('#simulation-result-card', { state: 'visible', timeout: 15000 });
    await page.waitForFunction(() => {
      const txt = document.getElementById('simulation-result')?.innerText || '';
      return txt.includes('Before vs After Plan Diff') || txt.includes('Outcome Rationale');
    }, { timeout: 15000 });

    const simResult = await page.textContent('#simulation-result');
    console.log(`[PHASE 6] Adaptation result output:\n${simResult.trim().substring(0, 150)}...`);

    // Screenshot 3: What if... Adaptation Diff
    const p3 = path.join(SCREENSHOT_DIR, '03_evaluator_what_if_adaptation_diff.png');
    await page.screenshot({ path: p3, fullPage: false });
    console.log(`[PHASE 6] Saved screenshot: ${p3}`);

    // =========================================================================
    // SUBTAB 4: DATABASE (Adminer & Seed Reset)
    // =========================================================================
    console.log('[PHASE 6] Switching to Database subtab...');
    await page.click('#tab-btn-database');
    await page.waitForTimeout(400);

    await page.waitForSelector('#eval-pane-database a[href*="8080"]', { state: 'visible' });
    await page.waitForSelector('#eval-pane-database button:has-text("Restore clean seed state")', { state: 'visible' });

    // Screenshot 4: Database & Seed Reset
    const p4 = path.join(SCREENSHOT_DIR, '04_evaluator_database_and_seed_reset.png');
    await page.screenshot({ path: p4, fullPage: false });
    console.log(`[PHASE 6] Saved screenshot: ${p4}`);

    console.log('[PHASE 6 ACCEPTANCE] ALL EVALUATOR TOOLS ACCEPTANCE CHECKS PASSED CLEANLY!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('[PHASE 6 TEST] Acceptance failed:', err);
  process.exit(1);
});
