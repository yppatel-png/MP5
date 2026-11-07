const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  for (const studentId of ['BH-SW-001', 'BH-HS-001', 'BH-UP-001']) {
    console.log(`\n======================================================`);
    console.log(`INSPECTING LIVE PERSONA: ${studentId}`);
    console.log(`======================================================`);
    await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle' });
    await page.waitForSelector('#persona-select option', { state: 'attached' });
    await page.selectOption('#persona-select', studentId);
    await new Promise(r => setTimeout(r, 2000));

    // Dashboard / Today
    const studentName = await page.$eval('#dash-name', el => el.innerText).catch(() => 'no name');
    const studentMeta = await page.$eval('#dash-meta', el => el.innerText).catch(() => 'no meta');
    const goalChip = await page.$eval('#topbar-goal-text', el => el.innerText).catch(() => 'no goal');
    const statusSentence = await page.$eval('#dash-status-sentence', el => el.innerText).catch(() => 'no status');
    const readinessVal = await page.$eval('#dash-readiness-val', el => el.innerText).catch(() => 'no readiness');
    const hoursVal = await page.$eval('#dash-hours-val', el => el.innerText).catch(() => 'no hours');
    const skillsVal = await page.$eval('#dash-skills-val', el => el.innerText).catch(() => 'no skills');
    const nextActionTitle = await page.$eval('#dash-action-title', el => el.innerText).catch(() => 'no action');
    const ruleCreditHeadroom = await page.$eval('#rule-credit-headroom', el => el.innerText).catch(() => 'no headroom');
    console.log('Today screen:');
    console.log('  Name:', studentName);
    console.log('  Meta:', studentMeta);
    console.log('  Goal chip:', goalChip);
    console.log('  Status sentence:', statusSentence);
    console.log('  Readiness:', readinessVal, '| Hours:', hoursVal, '| Skills:', skillsVal);
    console.log('  Next action:', nextActionTitle);
    console.log('  Credit headroom:', ruleCreditHeadroom);

    // Plan
    await page.click('[data-target="plan"]');
    await new Promise(r => setTimeout(r, 1200));
    const planSummary = await page.$eval('#plan-student-summary', el => el.innerText).catch(() => 'no summary');
    const certChip = await page.$eval('#plan-certificate-chip', el => el.innerText).catch(() => 'no cert');
    const semesters = await page.$$eval('.sem-column', cols => cols.map(c => ({
      title: c.querySelector('.sem-name')?.innerText?.trim(),
      credits: c.querySelector('.sem-stats')?.innerText?.trim(),
      courses: Array.from(c.querySelectorAll('.course-code-txt')).map(t => t.innerText?.trim())
    })));
    console.log('\nPlan screen:');
    console.log('  Cert chip:', certChip);
    console.log('  Plan summary:', planSummary);
    console.log('  Semesters rendered:', semesters.length);
    semesters.forEach(s => {
      console.log(`    ${s.title} [${s.credits}]: ${s.courses.length} courses -> ${s.courses.join(', ')}`);
    });

    // Diagnostic
    await page.click('[data-target="diagnostic"]');
    await new Promise(r => setTimeout(r, 1000));
    const startBtn = await page.$('#diagnostic-start-btn');
    if (startBtn && (await startBtn.isVisible())) {
      await startBtn.click();
      await new Promise(r => setTimeout(r, 1000));
    }
    const diagCount = await page.$eval('#diagnostic-question-count', el => el.innerText).catch(() => 'no count');
    const diagPrompt = await page.$eval('#diagnostic-question-text', el => el.innerText).catch(() => 'no prompt');
    console.log('\nDiagnostic screen:');
    console.log('  Count:', diagCount);
    console.log('  Prompt:', diagPrompt);

    // Practise
    await page.click('[data-target="practice"]');
    await new Promise(r => setTimeout(r, 1000));
    const exItems = await page.$$eval('#exercise-list-group > div', items => items.slice(0, 5).map(i => i.innerText.trim()));
    console.log('\nPractise screen:');
    console.log('  Top exercise items count:', exItems.length);
    exItems.forEach((ex, idx) => console.log(`    [${idx + 1}] ${ex.replace(/\n+/g, ' ')}`));

    // Buddy
    await page.click('#topbar-buddy-btn');
    await new Promise(r => setTimeout(r, 1000));
    const buddyMsgs = await page.$$eval('#buddy-chat-stream .chat-msg', msgs => msgs.map(m => m.innerText.trim()));
    console.log('\nBuddy drawer:');
    console.log('  First message:', buddyMsgs[0]);
    await page.click('#buddy-drawer .btn-icon');
  }

  await browser.close();
})();
