import { expect, test } from '@playwright/test';

test('judge-facing personalization, diagnostic, learning, history, certificate, Buddy, and adaptation flows work', async ({ page }) => {
  const failedResponses: string[] = [];
  const pageErrors: string[] = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('response', response => {
    if (response.status() >= 400) failedResponses.push(`${response.status()} ${response.url()}`);
  });

  await page.goto('/');
  await expect(page.locator('#app-content')).toBeVisible({ timeout: 20_000 });
  const healthResponse = await page.request.get('/api/health');
  expect(healthResponse.ok(), await healthResponse.text()).toBeTruthy();
  const health = await healthResponse.json();
  const activeProfile = health.institute_profile;
  if (activeProfile === 'iit_bhilai') {
    const studentId = await page.locator('#persona-select option').first().getAttribute('value');
    await page.locator('#persona-select').selectOption(studentId!);
    await expect(page.locator('#curriculum-scope-notice')).toBeVisible();

    await page.locator('.app-sidebar .nav-item[data-target="plan"]').click();
    await expect(page.locator('#plan-timeline-grid')).toContainText('CSL100');
    await expect(page.locator('#plan-certificate-chip')).toContainText('no policy certificate');

    await page.locator('.app-sidebar .nav-item[data-target="practice"]').click();
    await expect(page.locator('#exercise-list-group')).toContainText('No source-backed');
    await expect(page.locator('#practice-submit-btn')).toBeDisabled();
    await expect(page.locator('#practice-prompt')).toContainText('unavailable');
    await page.locator('.app-sidebar .nav-item[data-target="mastery"]').click();
    await expect(page.locator('#skills-matrix-grid')).toContainText('Skill mastery is unavailable');
    await page.locator('.app-sidebar .nav-item[data-target="diagnostic"]').click();
    await page.locator('#diagnostic-start-btn').click();
    await expect(page.locator('#diagnostic-feedback')).toContainText('No source-backed diagnostic');

    await page.locator('.app-sidebar .nav-item[data-target="setup"]').click();
    await page.locator('#setup-save-btn').click();
    await expect(page.locator('#setup-status')).toContainText('sample profile is saved');

    await page.locator('#topbar-buddy-btn').click();
    await page.locator('#buddy-input').fill('Why was CSL100 listed?');
    await page.locator('#buddy-input').press('Enter');
    await expect(page.locator('#buddy-chat-stream .chat-msg.assistant').last()).toContainText('CSL100', { timeout: 15_000 });

    expect(pageErrors).toEqual([]);
    expect(failedResponses).toEqual([]);
    return;
  }

  await page.locator('#persona-select').selectOption('S1024');

  await page.locator('.app-sidebar .nav-item[data-target="diagnostic"]').click();
  await page.locator('#diagnostic-start-btn').click();
  await expect(page.locator('#diagnostic-question-panel')).toBeVisible();
  const answer = page.locator('#diagnostic-answer-controls input[type="radio"]').first();
  if (await answer.count()) {
    await answer.check();
  } else {
    await page.locator('#diagnostic-text-answer').fill('A diagnostic response about this topic.');
  }
  await page.locator('#diagnostic-submit-btn').click();
  await expect(page.locator('#diagnostic-feedback')).toContainText(/Correct|Answer recorded/);

  await page.locator('.app-sidebar .nav-item[data-target="practice"]').click();
  await expect(page.locator('#practice-prompt')).not.toBeEmpty();
  const practiceAnswer = page.locator('#practice-answer-controls input[type="radio"]').first();
  if (await practiceAnswer.count()) {
    await practiceAnswer.check();
  } else {
    await page.locator('#practice-text-answer').fill('A practice response with a reasoned explanation.');
  }
  await page.locator('#practice-submit-btn').click();
  await expect(page.locator('#sandbox-output')).toContainText('Score:', { timeout: 15_000 });
  await page.locator('#exercise-list-group > div').nth(1).click();
  await expect(page.locator('#practice-code-area')).toBeVisible();
  await page.locator('#practice-code-area').fill('def reverse_list(values):\n    return values[::-1]');
  await page.locator('#practice-submit-btn').click();
  await expect(page.locator('#sandbox-output')).toContainText('Score:', { timeout: 15_000 });

  await page.locator('.app-sidebar .nav-item[data-target="plan"]').click();
  await page.getByRole('button', { name: 'Version history' }).click();
  await expect(page.locator('#diff-content-body')).toContainText(/Version \d+/);
  await page.locator('#drawer-backdrop').click({ force: true });
  await page.locator('#plan-certificate-chip').click();
  await expect(page.locator('#cert-hash-val')).not.toContainText('unavailable');
  await expect(page.locator('#cert-rules-accordion-list')).not.toBeEmpty();
  await page.locator('#drawer-backdrop').click({ force: true });

  await page.locator('.app-sidebar .nav-item[data-target="setup"]').click();
  await page.locator('#setup-save-btn').click();
  await expect(page.locator('#setup-status')).toContainText('saved', { timeout: 15_000 });

  await page.locator('#topbar-buddy-btn').click();
  await page.locator('#buddy-input').fill('Why was COL106 recommended?');
  await page.locator('#buddy-input').press('Enter');
  await expect(page.locator('#buddy-chat-stream .chat-msg.assistant').last()).not.toBeEmpty({ timeout: 15_000 });

  await page.locator('.app-sidebar .nav-item[data-target="admin"]').click();
  await page.locator('#simulation-scenario').selectOption('scenario_weak_quiz');
  await page.locator('button', { hasText: 'Run scenario' }).click();
  await expect(page.locator('#simulation-result')).toContainText('Assessment', { timeout: 20_000 });
  await expect(page.locator('#simulation-result')).toContainText('Validation: passed');

  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});
