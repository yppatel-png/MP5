import { expect, test } from '@playwright/test';

test('judge-facing personalization, diagnostic, learning, history, certificate, Buddy, and adaptation flows work', async ({ page }) => {
  const failedResponses: string[] = [];
  const pageErrors: string[] = [];
  page.on('pageerror', error => {
    console.log('[PAGE ERROR]', error.message);
    pageErrors.push(error.message);
  });
  page.on('response', response => {
    if (response.status() >= 400) failedResponses.push(`${response.status()} ${response.url()}`);
  });

  console.log('[STEP 0] goto /');
  await page.goto('/');
  await expect(page.locator('#app-content')).toBeVisible({ timeout: 20_000 });
  const healthResponse = await page.request.get('/api/health');
  expect(healthResponse.ok(), await healthResponse.text()).toBeTruthy();

  console.log('[STEP 1] select persona');
  const studentId = (await page.locator('#persona-select option').first().getAttribute('value')) || 'BH-SW-001';
  await page.locator('#persona-select').selectOption(studentId);

  // 1. Diagnostic Flow
  console.log('[STEP 2] diagnostic flow');
  await page.locator('.app-sidebar .nav-item[data-target="diagnostic"]').click();
  await page.locator('#diagnostic-start-btn').click();
  await expect(page.locator('#diagnostic-question-panel')).toBeVisible({ timeout: 5_000 });
  const answer = page.locator('#diagnostic-answer-controls input[type="radio"]').first();
  if (await answer.count()) {
    await answer.check();
  } else {
    await page.locator('#diagnostic-text-answer').fill('A diagnostic response about this topic.');
  }
  await page.locator('#diagnostic-submit-btn').click();
  await expect(page.locator('#diagnostic-feedback')).toContainText(/Correct|Answer recorded/, { timeout: 5_000 });
  await expect(page.locator('#app-content')).toBeVisible({ timeout: 10_000 });

  // 2. Practice Flow
  console.log('[STEP 3] practice flow');
  await page.locator('.app-sidebar .nav-item[data-target="practice"]').click();
  await expect(page.locator('#practice-submit-btn')).toBeEnabled({ timeout: 10_000 });
  await expect(page.locator('#practice-prompt')).not.toContainText('Select a different skill filter', { timeout: 10_000 });
  const radio = page.locator('#practice-answer-controls input[type="radio"]').first();
  const textInput = page.locator('#practice-text-answer');
  const codeArea = page.locator('#practice-code-area');
  if (await radio.count() > 0) {
    await radio.check();
  } else if ((await textInput.count()) > 0 && (await textInput.isVisible())) {
    await textInput.fill('A practice response with a reasoned explanation.');
  } else if (await codeArea.isVisible()) {
    await codeArea.fill('def solution(): return True');
  }
  await page.locator('#practice-submit-btn').click();
  await expect(page.locator('#sandbox-output')).toContainText('Score:', { timeout: 10_000 });

  // 3. Plan & Certificate Flow
  console.log('[STEP 4] plan & certificate flow');
  await page.locator('.app-sidebar .nav-item[data-target="plan"]').click();
  await page.getByRole('button', { name: 'Version history' }).click();
  await expect(page.locator('#diff-content-body')).toContainText(/Version \d+/, { timeout: 5_000 });
  await page.locator('#drawer-backdrop').click({ force: true });
  await page.locator('#plan-certificate-chip').click();
  await expect(page.locator('#cert-hash-val')).not.toContainText('unavailable', { timeout: 5_000 });
  await expect(page.locator('#cert-rules-accordion-list')).not.toBeEmpty({ timeout: 5_000 });
  await page.locator('#drawer-backdrop').click({ force: true });

  // 4. Setup Flow
  console.log('[STEP 5] setup flow');
  await page.locator('.app-sidebar .nav-item[data-target="setup"]').click();
  await page.locator('#setup-save-btn').click();
  await expect(page.locator('#setup-status')).toContainText('saved', { timeout: 5_000 });

  // 5. Conversational Buddy Flow
  console.log('[STEP 6] buddy flow');
  await page.locator('#topbar-buddy-btn').click();
  await page.locator('#buddy-input').fill('Why was CSL303 recommended?');
  await page.locator('#buddy-input').press('Enter');
  await expect(page.locator('#buddy-chat-stream .chat-msg.assistant').last()).not.toBeEmpty({ timeout: 10_000 });

  // 6. Adaptation Simulation Flow
  console.log('[STEP 7] adaptation flow');
  await page.locator('.app-sidebar .nav-item[data-target="admin"]').click();
  await page.locator('#simulation-scenario').selectOption('scenario_weak_quiz');
  await page.locator('button', { hasText: 'Run scenario' }).click();
  await expect(page.locator('#simulation-result')).toContainText('Assessment', { timeout: 10_000 });
  await expect(page.locator('#simulation-result')).toContainText('Validation: passed', { timeout: 10_000 });

  console.log('[STEP 8] done');
  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});
