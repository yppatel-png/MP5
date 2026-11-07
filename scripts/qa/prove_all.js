/**
 * Master Verification Suite: prove_all.js
 *
 * Runs all phase verification suites sequentially in isolated fresh browser contexts:
 * - Phase 0: Cache-busting middleware, content hashes, build stamp, live edit
 * - Phase 1: 4 canonical Hero Personas, interests, demo student switch
 * - Phase 2: Semester tabs, dynamic credit meter, core course locking, add drawer
 * - Phase 3: Buddy deterministic tools, health pill, interactive proposals
 * - Phase 4: 6-step onboarding wizard, automatic plan generation
 * - Phase 5: Practice questions, "Study this first" resources, progress goal readiness ring
 * - Phase 6: Evaluator tools, 4 subtabs (students, courses, what-if, database), plan diff
 */

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const QA_DIR = __dirname;
const PHASES = [
  { name: 'Phase 0 (Cache Busting & Build Stamp)', script: 'prove_phase0.js' },
  { name: 'Phase 1 (Canonical Personas & Interests)', script: 'prove_phase1.js' },
  { name: 'Phase 2 (Semester Tabs & Credit Meter)', script: 'prove_phase2.js' },
  { name: 'Phase 3 (Buddy Tools & Health Probe)', script: 'prove_phase3.js' },
  { name: 'Phase 4 (Onboarding Wizard & Auto-Plan)', script: 'prove_phase4.js' },
  { name: 'Phase 5 (Practice, Evidence & Mastery Ring)', script: 'prove_phase5.js' },
  { name: 'Phase 6 (Evaluator Tools & 4 Subtabs)', script: 'prove_phase6.js' },
];

console.log('================================================================');
console.log('  LEARNING BUDDY - MASTER ACCEPTANCE TEST SUITE (PHASES 0 - 6)  ');
console.log('================================================================\n');

const results = [];
let allPassed = true;
const overallStart = Date.now();

for (const phase of PHASES) {
  const scriptPath = path.join(QA_DIR, phase.script);
  if (!fs.existsSync(scriptPath)) {
    console.error(`[ERROR] Test script not found: ${phase.script}`);
    results.push({ name: phase.name, status: 'FAILED', duration: '0.0s', error: 'File missing' });
    allPassed = false;
    continue;
  }

  console.log(`>>> RUNNING: ${phase.name} (${phase.script})`);
  const start = Date.now();
  const proc = spawnSync('node', [scriptPath], {
    cwd: QA_DIR,
    encoding: 'utf-8',
    stdio: 'inherit',
    timeout: 120000,
  });
  const duration = ((Date.now() - start) / 1000).toFixed(1) + 's';

  if (proc.status === 0) {
    console.log(`[PASS] ${phase.name} completed successfully in ${duration}\n`);
    results.push({ name: phase.name, status: 'PASSED', duration });
  } else {
    console.error(`[FAIL] ${phase.name} exited with status ${proc.status} in ${duration}\n`);
    results.push({ name: phase.name, status: 'FAILED', duration, exitCode: proc.status });
    allPassed = false;
  }
}

const totalDuration = ((Date.now() - overallStart) / 1000).toFixed(1) + 's';

console.log('================================================================');
console.log('                     MASTER VERIFICATION SUMMARY                ');
console.log('================================================================');
results.forEach(r => {
  const badge = r.status === 'PASSED' ? '✓ PASS' : '✗ FAIL';
  console.log(` ${badge.padEnd(8)} | ${r.name.padEnd(46)} | ${r.duration}`);
});
console.log('----------------------------------------------------------------');
console.log(` Total Time: ${totalDuration}`);
console.log(` Overall Result: ${allPassed ? 'ALL PHASES PASSED (100% SUCCESS)' : 'SOME PHASES FAILED'}`);
console.log('================================================================\n');

if (!allPassed) {
  process.exit(1);
}
