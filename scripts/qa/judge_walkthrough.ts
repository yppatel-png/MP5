import { chromium } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

const BASE_URL = 'http://127.0.0.1:8000';
const OUT_DIR = path.resolve('docs/screenshots/judge_walkthrough');

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function runJudgeWalkthrough() {
  console.log('=== STARTING JUDGE WALKTHROUGH TEST ===');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const log: string[] = [];
  function record(msg: string) {
    console.log(msg);
    log.push(msg);
  }

  // 1. Visit Base URL
  record('1. Navigating to base URL...');
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(OUT_DIR, '01_initial_landing.png') });

  // 2. Inspect Build Stamp and Persona Switcher
  const buildStamp = await page.textContent('#demo-status-pill');
  record(`   Build stamp rendered: "${buildStamp?.trim()}"`);

  // 3. Test Persona BH-SW-001 (Aarav Sharma - Software)
  record('2. Selecting Aarav Sharma (BH-SW-001 - Software Engineering)...');
  await page.selectOption('#student-switcher', 'BH-SW-001');
  await page.waitForTimeout(1000);
  const aaravGoal = await page.textContent('#topbar-goal-text');
  const aaravAction = await page.textContent('#dash-action-title');
  record(`   Goal chip: "${aaravGoal?.trim()}"`);
  record(`   Next action: "${aaravAction?.trim()}"`);
  await page.screenshot({ path: path.join(OUT_DIR, '02_aarav_dashboard.png') });

  // 4. Test Plan Timeline Tab
  record('3. Navigating to "Your plan"...');
  await page.click('div[data-target="plan"]');
  await page.waitForTimeout(1000);
  const certChip = await page.textContent('#plan-certificate-chip');
  record(`   Certificate chip: "${certChip?.trim()}"`);
  const semColumns = await page.$$('.sem-column');
  record(`   Semesters rendered in plan: ${semColumns.length}`);
  await page.screenshot({ path: path.join(OUT_DIR, '03_aarav_plan.png') });

  // 5. Test "Why this course?" Drawer
  record('4. Opening "Why this course?" drawer on first course...');
  const firstCourseTile = await page.$('.course-tile');
  if (firstCourseTile) {
    await firstCourseTile.click();
    await page.waitForTimeout(800);
    const drawerTitle = await page.textContent('#why-course-name');
    record(`   Why drawer opened for: "${drawerTitle?.trim()}"`);
    await page.screenshot({ path: path.join(OUT_DIR, '04_aarav_why_drawer.png') });
    // Close drawer
    await page.click('button[onclick="closeWhyDrawer()"]');
    await page.waitForTimeout(500);
  }

  // 6. Test Practice Tab
  record('5. Navigating to "Practise"...');
  await page.click('div[data-target="practice"]');
  await page.waitForTimeout(1000);
  const exerciseItems = await page.$$('.exercise-item');
  record(`   Total exercise items in list: ${exerciseItems.length}`);
  if (exerciseItems.length > 0) {
    await exerciseItems[0].click();
    await page.waitForTimeout(800);
    const exPrompt = await page.textContent('#exercise-prompt');
    record(`   Selected exercise prompt sample: "${exPrompt?.substring(0, 60)}..."`);
    await page.screenshot({ path: path.join(OUT_DIR, '05_practice_selected.png') });

    // Submit option A
    const firstOption = await page.$('input[name="mcq_option"]');
    if (firstOption) {
      await firstOption.click();
      await page.click('#btn-submit-answer');
      await page.waitForTimeout(800);
      const feedback = await page.textContent('#practice-feedback');
      record(`   Practice submission result: "${feedback?.trim().substring(0, 70)}..."`);
      await page.screenshot({ path: path.join(OUT_DIR, '06_practice_feedback.png') });
    }
  }

  // 7. Test Skill Check (Diagnostic)
  record('6. Launching "Skill check" (Adaptive Diagnostic)...');
  await page.evaluate(() => (window as any).switchTab('diagnostic'));
  await page.waitForTimeout(1000);
  const diagCount = await page.textContent('#diagnostic-progress');
  record(`   Diagnostic progress: "${diagCount?.trim()}"`);
  await page.screenshot({ path: path.join(OUT_DIR, '07_skill_check.png') });

  // 8. Test Progress (Mastery Matrix)
  record('7. Navigating to "Progress" (Skill Mastery)...');
  await page.click('div[data-target="mastery"]');
  await page.waitForTimeout(1000);
  const skillRows = await page.$$('#mastery-table tbody tr');
  record(`   Skills in mastery table: ${skillRows.length}`);
  await page.screenshot({ path: path.join(OUT_DIR, '08_mastery_matrix.png') });

  // 9. Test Diya Iyer (BH-HS-001 - Higher Studies)
  record('8. Switching to Diya Iyer (BH-HS-001 - Higher Studies)...');
  await page.selectOption('#student-switcher', 'BH-HS-001');
  await page.waitForTimeout(1000);
  const diyaGoal = await page.textContent('#topbar-goal-text');
  record(`   Diya goal chip: "${diyaGoal?.trim()}"`);
  await page.click('div[data-target="plan"]');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(OUT_DIR, '09_diya_plan.png') });

  // 10. Test Kabir Verma (BH-UP-001 - UPSC)
  record('9. Switching to Kabir Verma (BH-UP-001 - UPSC)...');
  await page.selectOption('#student-switcher', 'BH-UP-001');
  await page.waitForTimeout(1000);
  const kabirGoal = await page.textContent('#topbar-goal-text');
  record(`   Kabir goal chip: "${kabirGoal?.trim()}"`);
  await page.click('div[data-target="plan"]');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(OUT_DIR, '10_kabir_plan.png') });

  // 11. Test Buddy Panel
  record('10. Testing Buddy conversational panel...');
  await page.click('#topbar-buddy-btn');
  await page.waitForTimeout(800);
  const buddyInput = await page.$('#chat-input');
  if (buddyInput) {
    await buddyInput.fill('Why should I take CSL303 Database Management Systems?');
    await page.click('#chat-send-btn');
    await page.waitForTimeout(3000);
    const messages = await page.$$('.chat-bubble-buddy');
    if (messages.length > 0) {
      const lastReply = await messages[messages.length - 1].textContent();
      record(`   Buddy reply received: "${lastReply?.substring(0, 100)}..."`);
    }
  }
  await page.screenshot({ path: path.join(OUT_DIR, '11_buddy_chat.png') });

  // 12. Test Admin Panel
  record('11. Navigating to Admin Console...');
  await page.click('a[onclick*="switchTab(\'admin\')"]');
  await page.waitForTimeout(1000);
  const adminTitle = await page.textContent('#topbar-section-title');
  record(`   Admin section: "${adminTitle?.trim()}"`);
  await page.screenshot({ path: path.join(OUT_DIR, '12_admin_console.png') });

  await browser.close();
  record('=== JUDGE WALKTHROUGH TEST COMPLETED SUCCESSFULLY ===');

  fs.writeFileSync(path.join(OUT_DIR, 'walkthrough_log.json'), JSON.stringify(log, null, 2));
}

runJudgeWalkthrough().catch(err => {
  console.error('Walkthrough error:', err);
  process.exit(1);
});
