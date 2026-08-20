#!/usr/bin/env node
// Self-test for the course-build classification + detection logic. No framework;
// run with `node course-build/scripts/selftest.mjs`. Exits non-zero on failure.

import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { moduleForPath } from './detect-affected-modules.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, '..', '..');

let failures = 0;
function check(name, cond) {
  if (cond) { console.log(`  ok  ${name}`); }
  else { console.error(`FAIL  ${name}`); failures++; }
}

console.log('detect-affected-modules.moduleForPath:');
check('content/04-lifecycle-hooks.md -> 4', moduleForPath('content/04-lifecycle-hooks.md') === 4);
check('content/01-intro.md -> 1', moduleForPath('content/01-intro.md') === 1);
check('assets/04/.github/hooks/hooks.json -> 4', moduleForPath('assets/04/.github/hooks/hooks.json') === 4);
check('assets/06/x -> 6', moduleForPath('assets/06/x') === 6);
check('README.md -> null', moduleForPath('README.md') === null);
check('content/notes.md -> null (no NN prefix)', moduleForPath('content/notes.md') === null);
check('assets/4/x -> null (not zero-padded)', moduleForPath('assets/4/x') === null);
check('src/assets/04/x -> null (not at root)', moduleForPath('src/assets/04/x') === null);

console.log('manifest source classification:');
const manifest = JSON.parse(readFileSync(resolve(repoRoot, 'course-build/manifest.json'), 'utf8'));
const VALID = new Set(['asset', 'seed', 'stored']);
for (const m of manifest.modules) {
  check(`module ${m.module} has valid source '${m.source}'`, VALID.has(m.source));
  if (m.source === 'asset') {
    check(`module ${m.module} (asset) has assetRoot`, typeof m.assetRoot === 'string' && m.assetRoot.length > 0);
  }
}
// Known classification (guards against accidental reclassification).
const bySource = Object.fromEntries(manifest.modules.map(m => [m.module, m.source]));
check('M01=stored', bySource[1] === 'stored');
check('M02=stored', bySource[2] === 'stored');
check('M03=stored', bySource[3] === 'stored');
check('M04=asset', bySource[4] === 'asset');
check('M05=seed', bySource[5] === 'seed');
check('M06=seed', bySource[6] === 'seed');

if (failures) { console.error(`\n${failures} check(s) failed.`); process.exit(1); }
console.log('\nAll self-test checks passed.');
