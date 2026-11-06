import { test, expect } from '@playwright/test';

/**
 * Phase 1 Outbound Egress Audit Test.
 * Intercepts all browser network activity upon navigating to the web interface.
 * Fails immediately if any third-party CDN, font provider, analytics endpoint,
 * or remote runtime script is requested.
 */
test.describe('Zero-Egress Isolation Audit', () => {
  test('should make zero outbound requests outside local loopback', async ({ page }) => {
    const externalRequests: string[] = [];

    page.on('request', request => {
      try {
        const url = new URL(request.url());
        // All assets (JS, CSS, fonts, SVG) and API requests must remain on local server
        if (!['localhost', '127.0.0.1', '0.0.0.0'].includes(url.hostname)) {
          externalRequests.push(request.url());
        }
      } catch (err) {
        externalRequests.push(request.url());
      }
    });

    await page.goto('http://127.0.0.1:8000');
    await page.waitForLoadState('domcontentloaded');

    // Assert zero external network egress calls
    expect(externalRequests).toEqual([]);
  });
});

