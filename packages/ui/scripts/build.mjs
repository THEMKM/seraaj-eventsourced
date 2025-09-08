#!/usr/bin/env node
// Cross-platform build script for @seraaj/ui
// - Compiles TypeScript to `dist`
// - Copies `src/styles/**` to `dist/styles/**`

import { spawnSync } from 'node:child_process';
import { mkdirSync, existsSync, rmSync, cpSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const root = resolve(__dirname, '..');
const tsconfig = resolve(root, 'tsconfig.json');
const srcStyles = resolve(root, 'src', 'styles');
const distDir = resolve(root, 'dist');
const distStyles = resolve(distDir, 'styles');

import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);

function runTsc() {
  // Resolve local TypeScript binary and run with the current Node
  const tscBin = require.resolve('typescript/bin/tsc');

  const res = spawnSync(process.execPath, [tscBin, '-p', tsconfig], {
    cwd: root,
    stdio: 'inherit',
    env: process.env,
  });
  if (res.status !== 0) {
    process.exit(res.status ?? 1);
  }
}

function copyStyles() {
  if (!existsSync(srcStyles)) {
    // No styles to copy; treat as success
    return;
  }

  if (!existsSync(distDir)) {
    mkdirSync(distDir, { recursive: true });
  }

  // Clean previous styles to avoid stale files
  rmSync(distStyles, { recursive: true, force: true });
  cpSync(srcStyles, distStyles, { recursive: true });
}

(function main() {
  try {
    runTsc();
    copyStyles();
    console.log('[ui] Build completed successfully.');
  } catch (err) {
    console.error('[ui] Build failed:', err);
    process.exit(1);
  }
})();
