/**
 * Automated Playwright acceptance verification for Phase 4: New Student Onboarding (PDF §3 UX, §2.2).
 *
 * Walks through the 6-step onboarding wizard:
 * 1. Basics: Name, Programme (CSE only), Current Semester, CGPA (validated 0-10)
 * 2. Courses Completed: Grouped checklist with "Select all of Semester N", optional grade
 * 3. Goal: 4 cards + "Not sure yet"
 * 4. Interests: Pick up to 5 from fixed chips
 * 5. Time & Preferences: Hours slider, preferred style (videos, reading, hands-on)
 * 6. Review & Create: Review card, submission creates profile and immediately lands on valid plan
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://127.0.0.1:8000';
const SCREENSHOT_DIR = path.resolve(__dirname, '../../docs/screenshots/phase4');

async function run() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  console.log('[PHASE 4 ACCEPTANCE] Starting Onboarding Wizard verification...');
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // 1. Navigate to Onboarding Tab
    console.log('[PHASE 4] Opening Onboarding tab...');
    await page.click('div.nav-item[data-target="setup"]');
    await page.waitForTimeout(500);

    // Verify Wizard Header and Step 1
    await page.waitForSelector('#wizard-step-1', { state: 'visible', timeout: 8000 });
    const step1Title = await page.textContent('#wizard-step-title');
    console.log(`[PHASE 4] Active step: "${step1Title}"`);

    // Step 1: Fill Basics
    await page.fill('#wizard-name', 'Priyanshu Verma');
    await page.selectOption('#wizard-semester', '3');
    await page.fill('#wizard-cgpa', '8.5');

    const p1 = path.join(SCREENSHOT_DIR, '01_wizard_step1_basics.png');
    await page.screenshot({ path: p1, fullPage: false });
    console.log(`[PHASE 4] Saved screenshot: ${p1}`);

    // Click Next
    await page.click('#wizard-next-btn');
    await page.waitForTimeout(400);

    // Step 2: Courses Completed
    await page.waitForSelector('#wizard-step-2', { state: 'visible' });
    console.log('[PHASE 4] Step 2: Completed Courses Checklist');
    
    // Click "Select all of Semester 1"
    await page.click('button:has-text("Select all of Semester 1")');
    await page.waitForTimeout(300);

    const p2 = path.join(SCREENSHOT_DIR, '02_wizard_step2_completed_courses.png');
    await page.screenshot({ path: p2, fullPage: false });
    console.log(`[PHASE 4] Saved screenshot: ${p2}`);

    // Click Next
    await page.click('#wizard-next-btn');
    await page.waitForTimeout(400);

    // Step 3: Goal Selection
    await page.waitForSelector('#wizard-step-3', { state: 'visible' });
    console.log('[PHASE 4] Step 3: Target Goal Cards');
    await page.click('.goal-card[data-goal="goal_software"]');
    await page.waitForTimeout(200);

    const p3 = path.join(SCREENSHOT_DIR, '03_wizard_step3_goal_cards.png');
    await page.screenshot({ path: p3, fullPage: false });
    console.log(`[PHASE 4] Saved screenshot: ${p3}`);

    // Click Next
    await page.click('#wizard-next-btn');
    await page.waitForTimeout(400);

    // Step 4: Interests
    await page.waitForSelector('#wizard-step-4', { state: 'visible' });
    console.log('[PHASE 4] Step 4: Expressed Interests');
    await page.click('.wizard-chip:has-text("AI/ML")');
    await page.click('.wizard-chip:has-text("Systems")');
    await page.waitForTimeout(200);

    const intCounter = await page.textContent('#wizard-interest-counter');
    console.log(`[PHASE 4] Interest counter: "${intCounter}"`);

    const p4 = path.join(SCREENSHOT_DIR, '04_wizard_step4_interest_chips.png');
    await page.screenshot({ path: p4, fullPage: false });
    console.log(`[PHASE 4] Saved screenshot: ${p4}`);

    // Click Next
    await page.click('#wizard-next-btn');
    await page.waitForTimeout(400);

    // Step 5: Time and Preferences
    await page.waitForSelector('#wizard-step-5', { state: 'visible' });
    console.log('[PHASE 4] Step 5: Time & Style');
    await page.fill('#wizard-hours', '18');
    await page.dispatchEvent('#wizard-hours', 'input');
    await page.click('.style-card[data-style="hands_on"]');
    await page.waitForTimeout(200);

    const p5 = path.join(SCREENSHOT_DIR, '05_wizard_step5_time_and_style.png');
    await page.screenshot({ path: p5, fullPage: false });
    console.log(`[PHASE 4] Saved screenshot: ${p5}`);

    // Click Next to Review
    await page.click('#wizard-next-btn');
    await page.waitForTimeout(400);

    // Step 6: Review and Create
    await page.waitForSelector('#wizard-step-6', { state: 'visible' });
    console.log('[PHASE 4] Step 6: Review & Create');
    const reviewText = await page.textContent('#wizard-review-summary');
    console.log('[PHASE 4] Review Summary:\n', reviewText.replace(/\s+/g, ' ').trim());

    if (!reviewText.includes('Priyanshu Verma') || !reviewText.includes('Semester 3')) {
      throw new Error('Review card did not reflect entered student details!');
    }

    const p6 = path.join(SCREENSHOT_DIR, '06_wizard_step6_review_and_create.png');
    await page.screenshot({ path: p6, fullPage: false });
    console.log(`[PHASE 4] Saved screenshot: ${p6}`);

    // Submit Wizard
    console.log('[PHASE 4] Clicking "Create Profile & Generate Valid Plan"...');
    await page.click('#wizard-submit-btn');

    // Wait for redirect/landing on 'Your Plan' tab (#view-plan)
    await page.waitForSelector('#view-plan.is-active, #view-plan:not([style*="display: none"])', { timeout: 15000 });
    await page.waitForTimeout(1000);

    // Assert landed on valid plan
    const activeTab = await page.$eval('.app-sidebar .nav-item.is-active', el => el.dataset.target);
    console.log(`[PHASE 4] Active tab after onboarding: "${activeTab}"`);
    if (activeTab !== 'plan') {
      throw new Error(`Expected active tab 'plan', but got '${activeTab}'`);
    }

    await page.waitForSelector('#plan-certificate-chip', { timeout: 8000 });
    const validityChip = await page.textContent('#plan-certificate-chip');
    console.log(`[PHASE 4] Plan validity chip: "${validityChip.trim()}"`);
    if (!validityChip.includes('Plan valid')) {
      throw new Error(`Plan is not valid for newly onboarded student! Chip text: ${validityChip}`);
    }

    const meterText = await page.textContent('.sem-credit-meter');
    console.log(`[PHASE 4] Plan credit meter for newly onboarded student: "${meterText.replace(/\s+/g, ' ').trim()}"`);

    const p7 = path.join(SCREENSHOT_DIR, '07_onboarding_completed_lands_on_valid_plan.png');
    await page.screenshot({ path: p7, fullPage: false });
    console.log(`[PHASE 4] Saved screenshot: ${p7}`);

    console.log('[PHASE 4 ACCEPTANCE] ALL WIZARD CHECKS PASSED AND LANDED ON VALID PLAN!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('[PHASE 4 ACCEPTANCE] FAILED:', err);
  process.exit(1);
});
