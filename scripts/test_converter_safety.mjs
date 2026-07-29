import assert from 'node:assert/strict';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const base = path.join(projectRoot, '.build', 'converter-safety-test');
const filters = path.join(base, 'filters');
const output = path.join(base, 'output');

await rm(base, { recursive: true, force: true });
await mkdir(filters, { recursive: true });
await writeFile(path.join(filters, 'filters.json'), '[{"filterId":1}]\r\n');
await writeFile(
  path.join(filters, 'filter_1.txt'),
  [
    '! CRLF safety fixture',
    '||ads.example^',
    '*$doc,ipaddress=203.0.113.7',
    '$ping,third-party',
    '',
  ].join('\r\n'),
);

const result = spawnSync(
  process.execPath,
  ['scripts/convert_filters.mjs', filters, output],
  { cwd: projectRoot, encoding: 'utf8' },
);
assert.equal(result.status, 0, result.stderr || result.stdout);

const report = JSON.parse(await readFile(path.join(output, 'conversion-report.json'), 'utf8'));
const rules = JSON.parse(await readFile(path.join(output, 'ruleset_1', 'ruleset_1.json'), 'utf8'));
assert.equal(report.sanitization.droppedRules, 1);
assert.equal(report.unsafeDeclarativeRulesDropped, 1);
assert.equal(rules.length, 1);
assert.equal(rules[0].condition.urlFilter, '||ads.example^');

await rm(base, { recursive: true, force: true });
console.log('Converter safety regression: PASS');
