#!/usr/bin/env node
// Detect which ACC course modules changed between two ACC commits, by mapping
// changed paths to module numbers. Used by the pull-model regenerate workflow.
//
// Mapping rules (a path affects module N when it matches):
//   content/NN-*.md            -> module NN   (module body)
//   content/NN-<slug>.md       -> module NN
//   assets/NN/**               -> module NN   (module solution assets)
//
// Usage:
//   node detect-affected-modules.mjs --acc <acc-repo-path> --from <sha> --to <sha>
//   node detect-affected-modules.mjs --acc <path> --to <sha>        # no --from: treat as first run
//
// Output (stdout, JSON): { "modules": [4,6], "min": 4, "fromModule": 4, "firstRun": false }
//   modules    sorted unique affected module numbers (1..7)
//   min        smallest affected module (the cascade root), or null when none
//   fromModule generator --from value = min (module N produces start-of-module-(N+1))
//   firstRun   true when --from was absent/empty (caller should treat as full regen)

import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

function parseArgs(argv) {
  const a = { acc: null, from: null, to: null };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case '--acc': a.acc = argv[++i]; break;
      case '--from': a.from = argv[++i]; break;
      case '--to': a.to = argv[++i]; break;
      default: throw new Error(`Unknown arg: ${argv[i]}`);
    }
  }
  if (!a.acc) throw new Error('--acc <path> is required');
  if (!a.to) throw new Error('--to <sha> is required');
  return a;
}

function git(cwd, ...args) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
}

function moduleForPath(p) {
  // content/NN-*.md
  let m = p.match(/^content\/(\d{2})-.*\.md$/);
  if (m) return parseInt(m[1], 10);
  // assets/NN/...
  m = p.match(/^assets\/(\d{2})(\/|$)/);
  if (m) return parseInt(m[1], 10);
  return null;
}

export { moduleForPath };

function main() {
  const args = parseArgs(process.argv.slice(2));
  const firstRun = !args.from || args.from.trim() === '';

  let files = [];
  if (!firstRun) {
    const out = git(args.acc, 'diff', '--name-only', `${args.from}`, `${args.to}`);
    files = out.split('\n').map(s => s.trim()).filter(Boolean);
  }

  const set = new Set();
  for (const f of files) {
    const n = moduleForPath(f);
    if (n && n >= 1 && n <= 7) set.add(n);
  }
  const modules = [...set].sort((x, y) => x - y);
  const min = modules.length ? modules[0] : null;

  process.stdout.write(JSON.stringify({
    modules,
    min,
    fromModule: min,
    firstRun,
  }));
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  try { main(); } catch (e) { console.error('ERROR: ' + e.message); process.exit(1); }
}
