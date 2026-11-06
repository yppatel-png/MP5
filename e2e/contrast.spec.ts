import { expect, test, type Page } from '@playwright/test';

type Theme = 'light' | 'dark';

const screens = [
  { name: 'Today', show: async (page: Page) => undefined },
  { name: 'Plan', show: async (page: Page) => page.locator('.nav-item[data-target="plan"]').click() },
  { name: 'Skills', show: async (page: Page) => page.locator('.nav-item[data-target="mastery"]').click() },
  { name: 'Learn', show: async (page: Page) => page.locator('.nav-item[data-target="practice"]').click() },
  { name: 'Buddy panel', show: async (page: Page) => page.locator('#topbar-buddy-btn').click() },
  { name: 'Onboarding', show: async (page: Page) => page.locator('#view-onboarding').waitFor({ state: 'visible' }) },
  { name: 'Diagnostic', show: async (page: Page) => page.evaluate(() => {
    (window as Window & { switchTab: (tab: string) => void }).switchTab('diagnostic');
  }) },
  { name: 'Admin', show: async (page: Page) => page.locator('.nav-item[data-target="admin"]').click() }
];

test.describe('WCAG text and component contrast', () => {
  for (const theme of ['light', 'dark'] as const satisfies readonly Theme[]) {
    for (const screen of screens) {
      test(`${screen.name} meets contrast in ${theme} theme`, async ({ page }) => {
        await page.goto(`http://127.0.0.1:8000/?theme=${theme}`);
        await page.waitForLoadState('domcontentloaded');
        await screen.show(page);

        const offenders = await page.evaluate(() => {
          type RGB = [number, number, number];
          const parse = (value: string): { color: RGB; alpha: number } | null => {
            const parts = value.match(/[\d.]+/g);
            if (!parts || parts.length < 3) return null;
            return {
              color: [Number(parts[0]), Number(parts[1]), Number(parts[2])],
              alpha: parts.length > 3 ? Number(parts[3]) : 1
            };
          };
          const blend = (front: RGB, back: RGB, alpha: number): RGB =>
            front.map((channel, index) => channel * alpha + back[index] * (1 - alpha)) as RGB;
          const luminance = ([r, g, b]: RGB): number => {
            const linear = [r, g, b].map(channel => {
              const value = channel / 255;
              return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
            });
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
          };
          const ratio = (first: RGB, second: RGB): number => {
            const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
            return (values[0] + 0.05) / (values[1] + 0.05);
          };
          const effectiveBackground = (element: Element, includeElement = true): { color: RGB; opacity: number } => {
            const ancestors: Element[] = [];
            for (let current: Element | null = element; current; current = current.parentElement) {
              ancestors.push(current);
            }
            let background: RGB = [255, 255, 255];
            let opacity = 1;
            for (const ancestor of ancestors.reverse()) {
              const style = getComputedStyle(ancestor);
              opacity *= Number(style.opacity);
              if (!includeElement && ancestor === element) continue;
              const layer = parse(style.backgroundColor);
              if (layer) background = blend(layer.color, background, layer.alpha * opacity);
            }
            return { color: background, opacity };
          };

          const failures: Array<Record<string, string | number>> = [];
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          let node: Node | null;
          while ((node = walker.nextNode())) {
            const text = node.textContent?.trim();
            const element = node.parentElement;
            if (!text || !element || !element.getClientRects().length) continue;
            const rect = element.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0 || rect.right <= 0 || rect.left >= innerWidth) continue;

            const style = getComputedStyle(element);
            if (style.visibility === 'hidden' || Number(style.opacity) === 0) continue;
            const foreground = parse(style.color);
            if (!foreground) continue;

            const { color: background, opacity } = effectiveBackground(element);
            if (opacity === 0) continue;
            const visibleForeground = blend(foreground.color, background, opacity * foreground.alpha);
            const fontSize = Number.parseFloat(style.fontSize);
            const fontWeight = Number.parseInt(style.fontWeight, 10) || 400;
            const minimum = fontSize >= 18 || (fontSize >= 14 && fontWeight >= 700) ? 3 : 4.5;
            const contrast = ratio(visibleForeground, background);
            if (contrast < minimum) {
              failures.push({
                selector: element.tagName.toLowerCase() + (element.id ? `#${element.id}` : ''),
                text: text.slice(0, 100),
                foreground: style.color,
                background: `rgb(${background.join(', ')})`,
                ratio: Number(contrast.toFixed(2)),
                minimum
              });
            }
          }

          for (const element of document.querySelectorAll('button, input, select, textarea, [role="button"]')) {
            if (!element.getClientRects().length) continue;
            const style = getComputedStyle(element);
            const border = parse(style.borderTopColor);
            if (!border || border.alpha === 0 || style.borderTopStyle === 'none' || Number(style.opacity) === 0) continue;
            const { color: background } = effectiveBackground(element);
            const { color: borderBackdrop, opacity } = effectiveBackground(element, false);
            const visibleBorder = blend(border.color, borderBackdrop, border.alpha * opacity);
            const fill = parse(style.backgroundColor);
            const fillContrast = fill
              ? ratio(blend(fill.color, borderBackdrop, fill.alpha * opacity), borderBackdrop)
              : 1;
            const borderIsRedundant = fill && fill.alpha > 0
              && ratio(visibleBorder, background) < 3
              && fillContrast >= 3;
            if (borderIsRedundant) continue;
            const contrast = ratio(visibleBorder, background);
            if (contrast < 3) {
              failures.push({
                selector: element.tagName.toLowerCase() + (element.id ? `#${element.id}` : ''),
                text: 'component border',
                foreground: style.borderTopColor,
                background: `rgb(${background.join(', ')})`,
                ratio: Number(contrast.toFixed(2)),
                minimum: 3
              });
            }
          }
          return failures;
        });

        expect(offenders, JSON.stringify(offenders, null, 2)).toEqual([]);
      });
    }
  }
});
