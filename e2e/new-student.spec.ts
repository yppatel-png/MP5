import { expect, test } from '@playwright/test';

test('new IIT Bhilai student can create a profile, review curricula, shortlist courses, and ask Buddy', async ({ page }) => {
  const failedResponses: string[] = [];
  page.on('response', response => {
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${response.url()}`);
    }
  });
  await page.goto('/');
  await expect(page.locator('#app-content')).toBeVisible({ timeout: 20_000 });
  await page.getByRole('button', { name: 'New IIT Bhilai student' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.locator('#bhilai-programme')).toContainText('BTech in Computer Science');

  await page.locator('[name="name"]').fill('Demo Bhilai Applicant');
  await page.locator('#bhilai-programme').selectOption('iit_bhilai_btech_cse_2023');
  await page.locator('#bhilai-semester').selectOption('3');
  await page.locator('[name="cgpa"]').fill('8.2');
  await page.locator('[name="available_hours_per_week"]').fill('12');
  await page.locator('[name="goal"]').fill('Explore AI and systems');
  await page.locator('[name="interests"]').fill('AI, systems');
  await page.locator('[name="completed_course_codes"]').fill('CSL100, MAL100');
  await page.locator('#bhilai-course-search').fill('CSL622');
  await page.locator('[data-course-code="CSL622"]').check();
  await page.getByRole('button', { name: 'Create profile and view curriculum' }).click();

  await expect(page.locator('#bhilai-workspace')).toBeVisible();
  await expect(page.locator('#bhilai-workspace')).toContainText('BTech in Computer Science and Engineering');
  await expect(page.locator('#bhilai-workspace')).toContainText('144 credits');
  await expect(page.locator('#bhilai-workspace')).toContainText('CSL100');
  await expect(page.locator('#bhilai-workspace')).toContainText('CSL622');
  await expect(page.locator('#bhilai-workspace')).toContainText('elective eligibility is unverified');

  await page.locator('[data-bhilai-tab="catalogue"]').click();
  await page.locator('#bhilai-workspace-search').fill('CSL622');
  await expect(page.locator('#bhilai-workspace-catalogue')).toContainText('Quantum Computing for Computer Scientists');

  await page.locator('[data-bhilai-tab="assistant"]').click();
  await page.locator('#bhilai-question').fill('What should I do next?');
  await page.locator('#bhilai-chat-form button[type="submit"]').click();
  await expect(page.locator('#bhilai-chat')).toContainText('Private local response');
  await expect(page.locator('#bhilai-chat')).toContainText('not sent to Gemini');

  await page.locator('#bhilai-edit-profile').click();
  await page.locator('[name="cgpa"]').fill('8.5');
  await page.locator('#bhilai-save-profile').click();
  await expect(page.locator('#bhilai-workspace')).toContainText('CGPA 8.5');
  expect(failedResponses).toEqual([]);
});
