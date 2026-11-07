/**
 * Reality Capture Playwright Script
 * Captures full-page screenshots at 1440px across all screens and user journeys
 * for BH-SW-001, BH-HS-001, BH-UP-001, and a brand-new student.
 * Saves screenshots to docs/screenshots/final/.
 */

import { chromium, Browser, Page } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';
const OUT_DIR = path.resolve(process.cwd(), 'docs/screenshots/final');

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function captureScreen(page: Page, filename: string) {
  const filePath = path.join(OUT_DIR, filename);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`[CAPTURED] ${filename}`);
}

async function walkStudent(page: Page, studentId: string) {
  console.log(`\n======================================================`);
  console.log(`Starting walk for persona: ${studentId}`);
  console.log(`======================================================`);

  if (studentId === 'NEW_STUDENT') {
    // Fresh session
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await sleep(1000);

    // 1. Home
    await captureScreen(page, `${studentId}_01_home.png`);

    // 2. Setup
    await page.click('[data-target="setup"]');
    await page.waitForSelector('#setup-name', { state: 'visible' });
    await page.fill('#setup-name', 'Kavita Rao');
    await page.selectOption('#setup-goal', 'goal_software');
    await page.fill('#setup-cgpa', '8.5');
    await page.fill('#setup-hours', '14');
    await captureScreen(page, `${studentId}_02_setup.png`);

    // 3. Diagnostic
    await page.click('[data-target="diagnostic"]');
    await sleep(800);
    const startBtn = await page.$('#diagnostic-start-btn');
    if (startBtn && (await startBtn.isVisible())) {
      await startBtn.click();
      await sleep(1000);
    }
    await captureScreen(page, `${studentId}_03_diagnostic.png`);

    // 4. Plan
    await page.click('[data-target="plan"]');
    await page.waitForSelector('#plan-timeline-grid', { state: 'visible' });
    await sleep(1000);
    await captureScreen(page, `${studentId}_04_plan.png`);

    // 5. Practise
    await page.click('[data-target="practice"]');
    await sleep(1000);
    await captureScreen(page, `${studentId}_05_practice.png`);

    // 6. Progress
    await page.click('[data-target="mastery"]');
    await sleep(1000);
    await captureScreen(page, `${studentId}_06_progress.png`);

    // 7. Buddy
    await page.click('#topbar-buddy-btn');
    await sleep(800);
    const buddyInput = await page.$('#buddy-input');
    if (buddyInput) {
      await buddyInput.fill('What should I study next for my software goal?');
      await page.keyboard.press('Enter');
      await sleep(2500);
    }
    await captureScreen(page, `${studentId}_07_buddy.png`);
    await page.click('#buddy-drawer .btn-icon');
    await sleep(500);

    // 8. Admin
    await page.click('[data-target="admin"]');
    await sleep(1000);
    await captureScreen(page, `${studentId}_08_admin.png`);
    return;
  }

  // Seeded Persona Walk
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await page.waitForSelector('#persona-select option', { state: 'attached' });
  await page.selectOption('#persona-select', studentId);
  await sleep(2000);

  // 1. Home / Today
  await page.click('[data-target="dashboard"]');
  await sleep(1000);
  await captureScreen(page, `${studentId}_01_home.png`);

  // 2. Set up profile
  await page.click('[data-target="setup"]');
  await page.waitForSelector('#setup-name', { state: 'visible' });
  await sleep(800);
  await captureScreen(page, `${studentId}_02_setup.png`);

  // 3. Skill check / Diagnostic
  await page.click('[data-target="diagnostic"]');
  await sleep(1000);
  const startBtn = await page.$('#diagnostic-start-btn');
  if (startBtn && (await startBtn.isVisible())) {
    await startBtn.click();
    await sleep(1200);
  }
  // Answer questions if present
  for (let i = 0; i < 2; i++) {
    const qPanel = await page.$('#diagnostic-question-panel');
    if (qPanel && (await qPanel.isVisible())) {
      const option = await page.$('input[name="diagnostic-answer"]');
      if (option) await option.click();
      const submitBtn = await page.$('#diagnostic-submit-btn');
      if (submitBtn) {
        await submitBtn.click();
        await sleep(1000);
        const nextBtn = await page.$('#diagnostic-submit-btn');
        const btnText = await nextBtn?.innerText();
        if (btnText && btnText.includes('Next')) {
          await nextBtn?.click();
          await sleep(1000);
        }
      }
    }
  }
  await captureScreen(page, `${studentId}_03_diagnostic.png`);

  // 4. Plan
  await page.click('[data-target="plan"]');
  await page.waitForSelector('.sem-column', { state: 'visible', timeout: 5000 }).catch(() => {});
  await sleep(1200);
  await captureScreen(page, `${studentId}_04_plan.png`);

  // 5. Practise
  await page.click('[data-target="practice"]');
  await sleep(1200);
  // Try answering 1 exercise if clickable
  try {
    const items = await page.$$('#exercise-list-group > div');
    if (items.length > 0) {
      await items[0].click();
      await sleep(800);
      const radio = await page.$('input[name="practice-answer"]');
      if (radio) await radio.click();
      const submitEx = await page.$('#practice-submit-btn');
      if (submitEx && (await submitEx.isVisible())) {
        await submitEx.click();
        await sleep(1500);
      }
    }
  } catch (err) {
    console.warn(`Could not interact with practice exercise for ${studentId}:`, err);
  }
  await captureScreen(page, `${studentId}_05_practice.png`);

  // 6. Progress
  await page.click('[data-target="mastery"]');
  await page.waitForSelector('#skills-matrix-grid', { state: 'visible' });
  await sleep(1200);
  await captureScreen(page, `${studentId}_06_progress.png`);

  // 7. Buddy (send 3 messages)
  await page.click('#topbar-buddy-btn');
  await sleep(1000);
  const buddyInput = await page.$('#buddy-input');
  if (buddyInput) {
    // Message 1
    await buddyInput.fill('Why was my first course recommended?');
    await page.keyboard.press('Enter');
    await sleep(2500);

    // Message 2
    await buddyInput.fill('What are my verified skill gaps?');
    await page.keyboard.press('Enter');
    await sleep(2500);

    // Message 3
    await buddyInput.fill('What should I focus on next?');
    await page.keyboard.press('Enter');
    await sleep(2500);
  }
  await captureScreen(page, `${studentId}_07_buddy.png`);
  await page.click('#buddy-drawer .btn-icon');
  await sleep(500);

  // 8. Admin
  await page.click('[data-target="admin"]');
  await sleep(1200);
  await captureScreen(page, `${studentId}_08_admin.png`);
}

async function main() {
  console.log(`Starting Reality Capture against ${BASE_URL}...`);
  const browser: Browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page: Page = await context.newPage();

  const personas = ['BH-SW-001', 'BH-HS-001', 'BH-UP-001', 'NEW_STUDENT'];

  for (const p of personas) {
    try {
      await walkStudent(page, p);
    } catch (err) {
      console.error(`Error capturing persona ${p}:`, err);
    }
  }

  await browser.close();
  console.log(`\nReality Capture completed! All screenshots saved in ${OUT_DIR}`);
}

main().catch((err) => {
  console.error('Fatal reality capture failure:', err);
  process.exit(1);
});
