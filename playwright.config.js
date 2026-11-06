const os = require('node:os');
const path = require('node:path');
const { defineConfig } = require('@playwright/test');

const smokeDatabase = process.env.LEARNING_BUDDY_SMOKE_DATABASE
  || (process.env.DATABASE_URL && process.env.DATABASE_URL.startsWith('sqlite:///')
    ? process.env.DATABASE_URL.slice('sqlite:///'.length)
    : path.join(os.tmpdir(), `learning-buddy-smoke-${process.pid}.db`));

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 600_000,
  expect: { timeout: 15_000 },
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8765',
    browserName: 'chromium',
    headless: true,
  },
  webServer: process.env.LEARNING_BUDDY_SMOKE_EXTERNAL_SERVER === 'true' ? undefined : {
    command: 'python scripts/smoke_server.py',
    url: 'http://127.0.0.1:8765/api/health',
    timeout: 120_000,
    reuseExistingServer: true,
    env: {
      ...process.env,
      DATABASE_URL: `sqlite:///${smokeDatabase.replace(/\\/g, '/')}`,
      OFFLINE_MODE: 'true',
    },
  },
});
