import { expect, test } from '@playwright/test';

test('all seeded personas load Today, Plan, Skills, Learn, and Buddy without errors', async ({ page, request }) => {
  const failedResponses: string[] = [];
  const pageErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('BROWSER:', msg.type(), msg.text());
    }
  });
  page.on('pageerror', err => {
    console.log('BROWSER PAGE ERROR:', err.message);
    pageErrors.push(err.message);
  });
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log('HTTP ERROR:', response.status(), response.url());
      failedResponses.push(`${response.status()} ${response.url()}`);
    }
  });

  const studentsResponse = await request.get('/api/students');
  expect(studentsResponse.ok(), await studentsResponse.text()).toBeTruthy();
  const students: Array<{ student_id: string; name: string }> = await studentsResponse.json();
  expect(students.length).toBeGreaterThan(0);

  // Test all 4 core hero personas plus representative edge cases across programs and years
  const heroIds = ['S1024', 'S1025', 'S1026', 'S1027', 'S2001', 'S2002', 'S2014', 'S2025', 'S2045', 'S2056'];
  const studentsToTest = students.filter(s => heroIds.includes(s.student_id));

  await page.goto('/');
  await expect(page.locator('#app-content')).toBeVisible({ timeout: 20_000 });

  for (const student of studentsToTest) {
    console.log(`[E2E] Persona: ${student.student_id} (${student.name})`);
    await page.locator('#persona-select').selectOption(student.student_id);
    await expect(page.locator('#app-content')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('#persona-select')).toHaveValue(student.student_id);
    await expect(page.locator('#dash-name')).toHaveText(student.name);
    await expect(page).toHaveTitle(`${student.name} | Learning Buddy`);

    const loadingVisible = await page.getByText(/Loading/i).evaluateAll(elements =>
      elements.some(element => {
        const style = window.getComputedStyle(element);
        const bounds = element.getBoundingClientRect();
        return style.display !== 'none'
          && style.visibility !== 'hidden'
          && bounds.width > 0
          && bounds.height > 0;
      }),
    );
    expect(loadingVisible, `${student.student_id} left a visible loading state`).toBe(false);

    for (const [tab, target] of [
      ['Today', 'dashboard'],
      ['Plan', 'plan'],
      ['Skills', 'mastery'],
      ['Learn', 'practice'],
      ['Diagnostic', 'diagnostic'],
      ['Personalize', 'setup'],
      ['Admin', 'admin'],
    ]) {
      await page.locator(`.app-sidebar .nav-item[data-target="${target}"]`).click();
      await expect(page.locator(`#view-${target}`)).toBeVisible();
      await expect(page).toHaveTitle(`${student.name} | Learning Buddy`);
    }

    await page.locator('#topbar-buddy-btn').click();
    expect(await page.evaluate(() => typeof window.toggleBuddyPanel)).toBe('function');
    expect(pageErrors).toEqual([]);
    await expect(page.locator('#buddy-drawer')).toHaveClass(/is-open/);
    await expect(page).toHaveTitle(`${student.name} | Learning Buddy`);
    await page.locator('#topbar-buddy-btn').click();
    await expect(page.locator('#buddy-drawer')).not.toHaveClass(/is-open/);
  }

  expect(failedResponses, 'The page made a request that returned 4xx/5xx').toEqual([]);
});
